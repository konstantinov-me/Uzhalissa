"""Веб-модуль: минимальный HTML-интерфейс чата поверх того же ChatService.

Рендеринг — Jinja2-шаблоны; состояние диалога хранится в cookie chat_id,
поэтому история сохраняется между визитами без JS-фреймворков.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from bot.core.service import ChatService
from bot.dependencies import get_service

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(tags=["web"], include_in_schema=False)


@router.get("/", response_class=HTMLResponse)
def index(request: Request, svc: ChatService = Depends(get_service)):
    chat_id = request.cookies.get("chat_id")
    messages = svc.get_messages(chat_id) if chat_id else []
    return templates.TemplateResponse(
        "chat.html",
        {"request": request, "messages": messages,
         "model_name": svc.model_name, "chat_id": chat_id},
    )


@router.post("/send", response_class=HTMLResponse)
def send(message: str = Form(...), svc: ChatService = Depends(get_service)):
    from fastapi.responses import RedirectResponse

    response = svc.ask(message=message)
    # редирект с установкой cookie — паттерн Post/Redirect/Get
    redirect = RedirectResponse(url="/", status_code=303)
    redirect.set_cookie("chat_id", response.chat_id, max_age=60 * 60 * 24 * 30)
    return redirect
