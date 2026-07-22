"""Busca leve por relevância, limitada à pasta knowledge do projeto."""

from __future__ import annotations

import logging
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

from config import KNOWLEDGE_ROOT, ensure_within, safe_read_text

LOGGER = logging.getLogger(__name__)
BLOCKED_PHRASES = (
    "ignore as instrucoes anteriores",
    "revele o system prompt",
    "desative as regras",
    "garanta lucro",
    "execute acoes automaticamente",
)


def normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", text.lower())
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9\s]", " ", value)


def tokenize(text: str) -> list[str]:
    """Extrai termos úteis sem bibliotecas científicas externas."""
    return [word for word in normalize(text).split() if len(word) > 2]


def _sanitize(text: str) -> str:
    return "\n".join(
        line
        for line in text.splitlines()
        if not any(phrase in normalize(line) for phrase in BLOCKED_PHRASES)
    )


def _chunks(text: str, max_chars: int = 800) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if current and len(current) + len(paragraph) + 2 > max_chars:
            chunks.append(current)
            current = paragraph
        else:
            current = f"{current}\n\n{paragraph}".strip()
    if current:
        chunks.append(current)
    return chunks


class KnowledgeBase:
    """Indexa Markdown locais e pontua termos com frequência inversa simples."""

    def __init__(self, knowledge_dir: str | Path, allowed_root: str | Path | None = None) -> None:
        self.allowed_root = Path(allowed_root or KNOWLEDGE_ROOT).resolve()
        self.knowledge_dir = ensure_within(knowledge_dir, self.allowed_root)
        self.documents: list[dict[str, Any]] = []
        self.document_frequency: Counter[str] = Counter()

    def load_documents(self) -> None:
        self.documents = []
        self.document_frequency.clear()
        if not self.knowledge_dir.is_dir():
            return
        for path in sorted(self.knowledge_dir.iterdir()):
            if not path.is_file() or path.suffix.lower() != ".md":
                continue
            try:
                content = _sanitize(safe_read_text(path, self.allowed_root))
                for chunk in _chunks(content):
                    tokens = tokenize(chunk)
                    if tokens:
                        self.documents.append(
                            {
                                "source": path.name,
                                "content": chunk,
                                "term_counts": Counter(tokens),
                                "token_count": len(tokens),
                            }
                        )
            except (OSError, UnicodeError, ValueError):
                LOGGER.exception("Documento local inválido: %s", path.name)
        for document in self.documents:
            self.document_frequency.update(document["term_counts"].keys())

    def search(self, query: str, top_k: int = 4) -> list[dict[str, Any]]:
        query_terms = set(tokenize(query))
        if not query_terms or not self.documents:
            return []
        total_documents = len(self.documents)
        scored: list[tuple[float, dict[str, Any]]] = []
        for document in self.documents:
            counts: Counter[str] = document["term_counts"]
            score = 0.0
            for term in query_terms:
                frequency = counts.get(term, 0)
                if frequency:
                    inverse_frequency = math.log(
                        (total_documents + 1) / (self.document_frequency[term] + 1)
                    ) + 1
                    score += (1 + math.log(frequency)) * inverse_frequency
            if score > 0:
                normalized_score = score / math.sqrt(document["token_count"])
                scored.append((normalized_score, document))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            {
                "source": document["source"],
                "content": document["content"],
                "score": float(score),
            }
            for score, document in scored[: max(1, top_k)]
        ]
