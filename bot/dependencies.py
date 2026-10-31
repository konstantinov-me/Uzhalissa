"""Composition root: единственное место, где собираются конкретные реализации.

api/routes.py и web/routes.py получают ChatService через Depends(get_service),
не зная, какая модель и какое хранилище стоят за ним.
"""
from __future__ import annotations

from functools import lru_cache

from bot.config.settings import Settings, get_settings
from bot.core.service import ChatService
from bot.llm.base import build_backend
from bot.storage.repository import ChatRepository


@lru_cache
def _build_service() -> ChatService:
    settings: Settings = get_settings()
    repo = ChatRepository(settings.db_path)

    if settings.llm_backend == "transformers":
        llm = build_backend("transformers",
                            model_name=settings.model_name,
                            max_new_tokens=settings.max_new_tokens)
    elif settings.llm_backend == "ollama":
        llm = build_backend("ollama",
                            base_url=settings.ollama_base_url,
                            model=settings.ollama_model)
    else:
        llm = build_backend("echo")

    return ChatService(repo=repo, llm=llm, settings=settings)


def get_service() -> ChatService:
    """Dependency provider для FastAPI."""
    return _build_service()
