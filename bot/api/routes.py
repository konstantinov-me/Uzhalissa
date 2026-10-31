"""REST API модуль (FastAPI router).

Тонкая надстройка над ChatService; вся логика — в core.
Документация автоматически доступна на /docs (OpenAPI/Swagger).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from bot.core.models import Chat, ChatRequest, ChatResponse, HealthResponse, Message
from bot.core.service import ChatService
from bot.dependencies import get_service

router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.get("/health", response_model=HealthResponse)
def health(svc: ChatService = Depends(get_service)):
    return HealthResponse(status="ok", model=svc.model_name, backend="fastapi")


@router.post("/chat", response_model=ChatResponse, summary="Задать вопрос боту")
def chat(req: ChatRequest, svc: ChatService = Depends(get_service)):
    """Если chat_id не передан — создаётся новый диалог, его id вернётся в ответе."""
    try:
        return svc.ask(message=req.message, chat_id=req.chat_id)
    except Exception as e:  # ошибки бэкенда модели → 502
        raise HTTPException(status_code=502, detail=f"Ошибка генерации: {e}")


@router.get("/chats", response_model=list[Chat], summary="Список диалогов")
def list_chats(svc: ChatService = Depends(get_service)):
    return svc.list_chats()


@router.get("/chats/{chat_id}/messages", response_model=list[Message],
            summary="История диалога")
def chat_messages(chat_id: str, svc: ChatService = Depends(get_service)):
    messages = svc.get_messages(chat_id)
    if not messages and svc.get_chat(chat_id) is None:
        raise HTTPException(status_code=404, detail="Диалог не найден")
    return messages


@router.delete("/chats/{chat_id}", status_code=204, summary="Удалить диалог")
def delete_chat(chat_id: str, svc: ChatService = Depends(get_service)):
    if not svc.delete_chat(chat_id):
        raise HTTPException(status_code=404, detail="Диалог не найден")
