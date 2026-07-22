"""Configuração sem dependências externas."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = (PROJECT_ROOT / "data").resolve()
KNOWLEDGE_ROOT = (PROJECT_ROOT / "knowledge").resolve()
PROMPTS_DIR = (PROJECT_ROOT / "prompts").resolve()
STATIC_DIR = (PROJECT_ROOT / "static").resolve()


def _load_env_file() -> None:
    path = PROJECT_ROOT / ".env"
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))


_load_env_file()


def ensure_within(path: str | Path, allowed_root: str | Path) -> Path:
    resolved = Path(path).expanduser().resolve()
    root = Path(allowed_root).expanduser().resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"Caminho fora da pasta permitida: {resolved}")
    return resolved


def project_path(value: str, allowed_root: Path) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return ensure_within(candidate, allowed_root)


def safe_read_text(path: str | Path, allowed_root: str | Path) -> str:
    safe_path = ensure_within(path, allowed_root)
    if not safe_path.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {safe_path.name}")
    return safe_path.read_text(encoding="utf-8")


def _positive_int(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
        return value if value > 0 else default
    except ValueError:
        return default


def _local_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("OLLAMA_BASE_URL deve apontar para um servidor HTTP local.")
    return value.rstrip("/")


OLLAMA_BASE_URL = _local_url(os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2").strip() or "llama3.2"
OLLAMA_TIMEOUT_SECONDS = _positive_int("OLLAMA_TIMEOUT_SECONDS", 90)
DATABASE_PATH = project_path(os.getenv("DATABASE_PATH", "data/betcoach.db"), DATA_DIR)
KNOWLEDGE_DIR = project_path(os.getenv("KNOWLEDGE_DIR", "knowledge"), KNOWLEDGE_ROOT)
MAX_HISTORY_MESSAGES = _positive_int("MAX_HISTORY_MESSAGES", 12)
KNOWLEDGE_TOP_K = _positive_int("KNOWLEDGE_TOP_K", 4)
SYSTEM_PROMPT_PATH = ensure_within(PROMPTS_DIR / "system_prompt.txt", PROMPTS_DIR)

