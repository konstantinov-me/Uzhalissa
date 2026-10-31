"""Доменные модели чат-бота (pydantic).

Используются всеми модулями как единый контракт данных:
core, llm, storage, api, web зависят от этого модуля, но не друг от друга.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


def _uuid() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    """Одно сообщение в диалоге."""
    id: str = Field(default_factory=_uuid)
    chat_id: str
    role: Role
    content: str
    created_at: datetime = Field(default_factory=_now)


class Chat(BaseModel):
    """Диалог (сессия) пользователя с ботом."""
    id: str = Field(default_factory=_uuid)
    title: str = "Новый диалог"
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class ChatRequest(BaseModel):
    """Входной контракт API: задать вопрос в диалоге."""
    chat_id: Optional[str] = None          # если нет — создаётся новый диалог
    message: str = Field(min_length=1, max_length=8000)
    stream: bool = False                   # зарезервировано для SSE-ответа


class ChatResponse(BaseModel):
    """Выходной контракт API: ответ бота."""
    chat_id: str
    user_message: Message
    assistant_message: Message
    model: str                             # имя модели, сгенерировавшей ответ


class HealthResponse(BaseModel):
    status: str
    model: str
    backend: str
