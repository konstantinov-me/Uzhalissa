"""Хранилище диалогов: SQLite (стандартная библиотека) за простым интерфейсом.

Модуль не знает про LLM и API — только про доменные модели из core.models.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:  # Python 3.12+: собственный адаптер вместо устаревшего default
    sqlite3.register_adapter(datetime, lambda dt: dt.isoformat())
except AttributeError:
    pass

from bot.core.models import Chat, Message, Role

_SCHEMA = """
CREATE TABLE IF NOT EXISTS chats (
    id         TEXT PRIMARY KEY,
    title      TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
    id         TEXT PRIMARY KEY,
    chat_id    TEXT NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    role       TEXT NOT NULL,
    content    TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id, created_at);
"""


class ChatRepository:
    def __init__(self, db_path: str):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._db_path = db_path
        with self._conn() as c:
            c.executescript(_SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    # --- Чаты ---
    def create_chat(self, title: str = "Новый диалог") -> Chat:
        chat = Chat(title=title)
        with self._conn() as c:
            c.execute(
                "INSERT INTO chats VALUES (:id, :title, :created_at, :updated_at)",
                {**chat.model_dump(mode="python")},
            )
        return chat

    def get_chat(self, chat_id: str) -> Optional[Chat]:
        with self._conn() as c:
            row = c.execute("SELECT * FROM chats WHERE id = ?", (chat_id,)).fetchone()
        return Chat(**dict(row)) if row else None

    def list_chats(self, limit: int = 50) -> list[Chat]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM chats ORDER BY updated_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [Chat(**dict(r)) for r in rows]

    def delete_chat(self, chat_id: str) -> bool:
        with self._conn() as c:
            cur = c.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
            return cur.rowcount > 0

    # --- Сообщения ---
    def add_message(self, chat_id: str, role: Role, content: str) -> Message:
        msg = Message(chat_id=chat_id, role=role, content=content)
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as c:
            c.execute(
                "INSERT INTO messages VALUES (:id, :chat_id, :role, :content, :created_at)",
                {"id": msg.id, "chat_id": chat_id, "role": role.value,
                 "content": content, "created_at": msg.created_at.isoformat()},
            )
            c.execute("UPDATE chats SET updated_at = ? WHERE id = ?", (now, chat_id))
        return msg

    def get_history(self, chat_id: str, limit: int = 100) -> list[Message]:
        """Последние `limit` сообщений в хронологическом порядке."""
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM (SELECT * FROM messages WHERE chat_id = ? "
                "ORDER BY created_at DESC LIMIT ?) ORDER BY created_at ASC",
                (chat_id, limit),
            ).fetchall()
        return [Message(**dict(r)) for r in rows]
