"""Абстракция LLM-бэкенда.

Любой локальный ИИ подключается реализацией интерфейса LLMBackend:
 - EchoBackend   — заглушка для тестов и разработки без GPU;
 - TransformersBackend — локальная модель через HuggingFace transformers;
 - OllamaBackend — локальный сервер Ollama (проще всего в деплое).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ChatMessage:
    """Сообщение в формате, понятному модели (role/content)."""
    role: str   # system | user | assistant
    content: str


class LLMBackend(ABC):
    """Интерфейс генератора ответов."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Идентификатор модели/бэкенда для логов и API."""

    @abstractmethod
    def generate(self, messages: list[ChatMessage]) -> str:
        """Принимает историю диалога, возвращает текст ответа ассистента."""


def build_backend(backend: str, **kwargs) -> LLMBackend:
    """Фабрика бэкендов по имени из конфигурации."""
    if backend == "echo":
        from .echo import EchoBackend
        return EchoBackend()
    if backend == "transformers":
        from .transformers_backend import TransformersBackend
        return TransformersBackend(**kwargs)
    if backend == "ollama":
        from .ollama_backend import OllamaBackend
        return OllamaBackend(**kwargs)
    raise ValueError(f"Неизвестный LLM-бэкенд: {backend!r}")
