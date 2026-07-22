"""Histórico local da conversa em SQLite."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

from config import DATABASE_PATH, DATA_DIR, ensure_within


def _connect() -> sqlite3.Connection:
    path = ensure_within(DATABASE_PATH, DATA_DIR)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL
            )
            """
        )


def save_message(role: str, content: str) -> None:
    if role not in {"user", "assistant"} or not content.strip():
        raise ValueError("Mensagem inválida.")
    with _connect() as connection:
        connection.execute(
            "INSERT INTO messages (created_at, role, content) VALUES (?, ?, ?)",
            (datetime.now(timezone.utc).isoformat(), role, content.strip()),
        )


def list_messages(limit: int = 30) -> list[dict[str, Any]]:
    with _connect() as connection:
        rows = connection.execute(
            "SELECT * FROM (SELECT * FROM messages ORDER BY id DESC LIMIT ?) ORDER BY id",
            (max(1, limit),),
        ).fetchall()
    return [dict(row) for row in rows]


def clear_messages() -> int:
    with _connect() as connection:
        cursor = connection.execute("DELETE FROM messages")
        return cursor.rowcount

