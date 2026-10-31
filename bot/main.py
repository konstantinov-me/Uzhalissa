"""Точка входа: единое FastAPI-приложение с REST API (/api/v1/*) и веб-UI (/).

Запуск:
    uvicorn bot.main:app --reload
"""
from fastapi import FastAPI

from bot.api.routes import router as api_router
from bot.config.settings import get_settings
from bot.web.routes import router as web_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.api_title,
        description="Модульный чат-бот с локальным ИИ. REST API в /api/v1, веб-интерфейс в /",
        version="0.1.0",
    )
    app.include_router(api_router)   # JSON API для машинных клиентов
    app.include_router(web_router)   # HTML-интерфейс для людей
    return app


app = create_app()
