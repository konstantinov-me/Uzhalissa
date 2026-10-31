"""REST API модуль (FastAPI router).

Тонкая надстройка над ChatService; вся логика — в core.
Документация автоматически доступна на /docs (OpenAPI/Swagger).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from bot.core.models import Chat, ChatRequest, ChatResponse, HealthResponse, Message
from bot.core.service import ChatService
from bot.dependencies import get_service

router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.get("/health", response_model=HealthResponse)
async def health(svc: ChatService = Depends(get_service)):
    return HealthResponse(status="ok", model=svc.model_name, backend="fastapi")


@router.post("/chat", response_model=ChatResponse, summary="Задать вопрос боту")
async def chat(req: ChatRequest, svc: ChatService = Depends(get_service)):
    """Если chat_id не передан — создаётся новый диалог, его id вернётся в ответе."""
    try:
        return await svc.ask(message=req.message, chat_id=req.chat_id)
    except Exception as e:  # ошибки бэкенда модели → 502
        raise HTTPException(status_code=502, detail=f"Ошибка генерации: {e}")


@router.post("/chat/stream", summary="Задать вопрос боту (стриминг SSE)")
async def chat_stream(req: ChatRequest, svc: ChatService = Depends(get_service)):
    """Server-Sent Events: события `meta` (chat_id), `delta` (части ответа),
    `done` (id сохранённого сообщения). Подходит для посимвольного вывода в UI."""
    return StreamingResponse(
        svc.ask_stream(message=req.message, chat_id=req.chat_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/chats", response_model=list[Chat], summary="Список диалогов")
async def list_chats(svc: ChatService = Depends(get_service)):
    return svc.list_chats()


@router.get("/chats/{chat_id}/messages", response_model=list[Message],
            summary="История диалога")
async def chat_messages(chat_id: str, svc: ChatService = Depends(get_service)):
    messages = svc.get_messages(chat_id)
    if not messages and svc.get_chat(chat_id) is None:
        raise HTTPException(status_code=404, detail="Диалог не найден")
    return messages


@router.delete("/chats/{chat_id}", status_code=204, summary="Удалить диалог")
async def delete_chat(chat_id: str, svc: ChatService = Depends(get_service)):
    if not svc.delete_chat(chat_id):
        raise HTTPException(status_code=404, detail="Диалог не найден")
