"""Servidor web leve do BetCoach, implementado com a biblioteca padrão."""

from __future__ import annotations

import json
import logging
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from config import (
    KNOWLEDGE_DIR,
    KNOWLEDGE_TOP_K,
    MAX_HISTORY_MESSAGES,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT_SECONDS,
    PROMPTS_DIR,
    STATIC_DIR,
    SYSTEM_PROMPT_PATH,
    ensure_within,
    safe_read_text,
)
from context_builder import build_context, format_context
from database import clear_messages, initialize_database, list_messages, save_message
from fallback import fallback_response
from knowledge_base import KnowledgeBase
from local_llm import LocalLLMClient, LocalLLMError
from risk_detection import detect_risk_signals, normalize

LOGGER = logging.getLogger(__name__)
KNOWLEDGE = KnowledgeBase(KNOWLEDGE_DIR)
KNOWLEDGE.load_documents()


def model_status() -> tuple[bool, bool]:
    client = LocalLLMClient(OLLAMA_BASE_URL, OLLAMA_MODEL, timeout=2)
    connected = client.check_connection()
    return connected, client.check_model() if connected else False


def answer(question: str) -> dict[str, Any]:
    history = list_messages(MAX_HISTORY_MESSAGES)
    results = KNOWLEDGE.search(question, KNOWLEDGE_TOP_K)
    risks = detect_risk_signals(question, [], 0.0)
    connected, available = model_status()
    guaranteed = any(
        phrase in normalize(question)
        for phrase in ("aposta certa", "aposta garantida", "sem risco")
    )
    used_model = False
    if connected and available and not risks and not guaranteed:
        try:
            response = LocalLLMClient(
                OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT_SECONDS
            ).generate_response(
                safe_read_text(SYSTEM_PROMPT_PATH, PROMPTS_DIR),
                question,
                history,
                format_context(build_context(risks, results)),
            )
            used_model = True
        except LocalLLMError:
            LOGGER.warning("Ollama indisponível; usando modo básico")
            response = fallback_response(question, results, risks)
    else:
        response = fallback_response(question, results, risks, model_available=available)
    save_message("user", question)
    save_message("assistant", response)
    return {
        "answer": response,
        "sources": sorted({item["source"] for item in results}),
        "mode": "ollama" if used_model else "basic",
    }


class ChatHandler(BaseHTTPRequestHandler):
    server_version = "BetCoach/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        LOGGER.info("%s - %s", self.client_address[0], fmt % args)

    def _json(self, data: Any, status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _static(self, filename: str, content_type: str) -> None:
        try:
            path = ensure_within(STATIC_DIR / filename, STATIC_DIR)
            body = path.read_bytes()
        except (OSError, ValueError):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path == "/":
            self._static("index.html", "text/html; charset=utf-8")
        elif path == "/styles.css":
            self._static("styles.css", "text/css; charset=utf-8")
        elif path == "/app.js":
            self._static("app.js", "text/javascript; charset=utf-8")
        elif path == "/api/history":
            self._json(list_messages(MAX_HISTORY_MESSAGES))
        elif path == "/api/status":
            connected, available = model_status()
            self._json({"connected": connected, "available": available, "model": OLLAMA_MODEL})
        elif path == "/health":
            self._json({"status": "ok"})
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        length = min(int(self.headers.get("Content-Length", "0")), 16_384)
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
        except (UnicodeError, json.JSONDecodeError):
            self._json({"error": "Requisição inválida."}, 400)
            return
        if self.path == "/api/chat":
            question = str(payload.get("message", "")).strip()[:2000]
            if not question:
                self._json({"error": "Digite uma pergunta."}, 400)
                return
            try:
                self._json(answer(question))
            except Exception:
                LOGGER.exception("Falha ao responder")
                self._json({"error": "Não foi possível responder agora."}, 500)
        elif self.path == "/api/clear":
            clear_messages()
            self._json({"cleared": True})
        else:
            self.send_error(HTTPStatus.NOT_FOUND)


def serve() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    initialize_database()
    server = ThreadingHTTPServer(("127.0.0.1", 8501), ChatHandler)
    print("[BetCoach AI] Em execução: http://localhost:8501")
    print("Pressione Ctrl+C para encerrar.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    serve()
