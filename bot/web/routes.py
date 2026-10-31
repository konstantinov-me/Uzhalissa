"""Веб-модуль: минимальный HTML-интерфейс чата поверх того же ChatService.

Рендеринг — Jinja2-шаблоны; состояние диалога хранится в cookie chat_id,
поэтому история сохраняется между визитами без JS-фреймворков.
Дополнительно есть AJAX-страница /chat со стримингом ответов через SSE.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from bot.core.models import ChatRequest
from bot.core.service import ChatService
from bot.dependencies import get_service

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(tags=["web"], include_in_schema=False)


@router.get("/", response_class=HTMLResponse)
def index(request: Request, svc: ChatService = Depends(get_service)):
    """Классическая серверная страница (POST + PRG) — работает даже без JS."""
    chat_id = request.cookies.get("chat_id")
    messages = svc.get_messages(chat_id) if chat_id else []
    return templates.TemplateResponse(
        request, "chat.html",
        {"messages": messages, "model_name": svc.model_name, "chat_id": chat_id},
    )


@router.post("/send", response_class=HTMLResponse)
async def send(message: str = Form(...), svc: ChatService = Depends(get_service)):
    response = await svc.ask(message=message)
    # редирект с установкой cookie — паттерн Post/Redirect/Get
    redirect = RedirectResponse(url="/", status_code=303)
    redirect.set_cookie("chat_id", response.chat_id, max_age=60 * 60 * 24 * 30)
    return redirect


@router.get("/chat", response_class=HTMLResponse)
def chat_page(request: Request, svc: ChatService = Depends(get_service)):
    """Страница с асинхронным UI: отправка через fetch + стриминг SSE."""
    return templates.TemplateResponse(
        request, "chat_stream.html", {"model_name": svc.model_name},
    )


@router.post("/chat/send")
async def chat_send(req: ChatRequest, svc: ChatService = Depends(get_service)):
    """JSON-эндпоинт для страницы /chat (тот же ChatService, что и у REST API)."""
    try:
        return await svc.ask(message=req.message, chat_id=req.chat_id)
    except Exception as e:  # ошибки бэкенда модели → 502
        raise HTTPException(status_code=502, detail=f"Ошибка генерации: {e}")
