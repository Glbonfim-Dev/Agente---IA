"""Cliente Ollama usando apenas a biblioteca padrão."""

from __future__ import annotations

import json
import socket
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class LocalLLMError(RuntimeError):
    pass


class OllamaUnavailableError(LocalLLMError):
    pass


class ModelNotInstalledError(LocalLLMError):
    pass


class LocalLLMClient:
    def __init__(self, base_url: str, model: str, timeout: int = 90) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def _request(self, path: str, payload: dict | None = None) -> dict:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            f"{self.base_url}{path}",
            data=data,
            headers={"Content-Type": "application/json"} if data else {},
            method="POST" if data else "GET",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code == 404:
                raise ModelNotInstalledError(f"O modelo {self.model} não está instalado.") from exc
            raise OllamaUnavailableError("O Ollama retornou um erro HTTP.") from exc
        except (URLError, TimeoutError, socket.timeout) as exc:
            raise OllamaUnavailableError("Não foi possível conectar ao Ollama local.") from exc
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise LocalLLMError("O Ollama retornou uma resposta inválida.") from exc

    def _models(self) -> list[str]:
        data = self._request("/api/tags")
        models = data.get("models", []) if isinstance(data, dict) else []
        return [
            str(item.get("name") or item.get("model"))
            for item in models
            if isinstance(item, dict) and (item.get("name") or item.get("model"))
        ]

    def check_connection(self) -> bool:
        try:
            self._models()
            return True
        except LocalLLMError:
            return False

    def check_model(self) -> bool:
        try:
            models = self._models()
        except LocalLLMError:
            return False
        expected = self.model if ":" in self.model else f"{self.model}:latest"
        return self.model in models or expected in models

    def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: list[dict],
        formatted_context: str,
    ) -> str:
        models = self._models()
        expected = self.model if ":" in self.model else f"{self.model}:latest"
        if self.model not in models and expected not in models:
            raise ModelNotInstalledError(f"O modelo {self.model} não está instalado.")
        history = [
            {"role": item["role"], "content": item["content"]}
            for item in conversation_history
            if item.get("role") in {"user", "assistant"} and item.get("content")
        ]
        data = self._request(
            "/api/chat",
            {
                "model": self.model,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "system", "content": formatted_context},
                    *history,
                    {"role": "user", "content": user_message},
                ],
                "options": {"temperature": 0.2},
            },
        )
        content = data.get("message", {}).get("content", "") if isinstance(data, dict) else ""
        if not isinstance(content, str) or not content.strip():
            raise LocalLLMError("O modelo retornou uma resposta vazia.")
        return content.strip()

