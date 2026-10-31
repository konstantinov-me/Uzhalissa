"""Общие фикстуры: изолированное приложение с временной БД."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Свежий App с SQLite в tmp_path и echo-бэкендом (без внешних зависимостей)."""
    monkeypatch.setenv("db_path", str(tmp_path / "test.db"))
    monkeypatch.setenv("llm_backend", "echo")

    # сбрасываем кэш настроек и singleton сервиса, чтобы подхватить tmp-БД
    from bot.config.settings import get_settings
    from bot.dependencies import _build_service

    get_settings.cache_clear()
    _build_service.cache_clear()

    from bot.main import create_app

    with TestClient(create_app()) as c:
        yield c

    get_settings.cache_clear()
    _build_service.cache_clear()
