"""Тесты ядра и LLM-бэкендов (без HTTP)."""
import pytest

from bot.config.settings import Settings
from bot.core.models import Role
from bot.core.service import ChatService
from bot.llm.base import ChatMessage, build_backend
from bot.storage.repository import ChatRepository


class ScriptedBackend:
    """Детерминированный бэкенд для тестов сервиса."""
    name = "scripted"

    def __init__(self, chunks):
        self._chunks = list(chunks)
        self.seen_messages: list[list[ChatMessage]] = []

    def generate(self, messages):
        self.seen_messages.append(list(messages))
        return "".join(self._chunks)

    def generate_stream(self, messages):
        self.seen_messages.append(list(messages))
        yield from self._chunks


@pytest.fixture()
def service(tmp_path):
    llm = ScriptedBackend(["При", "вет", "!"])
    repo = ChatRepository(str(tmp_path / "db.sqlite"))
    settings = Settings(llm_backend="echo", db_path=str(tmp_path / "db.sqlite"))
    return ChatService(repo=repo, llm=llm, settings=settings), llm, repo


def test_ask_saves_both_sends_and_builds_prompt(service):
    import asyncio

    svc, llm, repo = service
    resp = asyncio.run(svc.ask("Привет!"))
    assert resp.assistant_message.content == "Привет!"
    # промпт = system + история (user-сообщение уже сохранено)
    prompt = llm.seen_messages[0]
    assert prompt[0].role == Role.SYSTEM.value
    assert prompt[-1].content == "Привет!"
    assert len(repo.get_history(resp.chat_id)) == 2


def test_unknown_backend_raises():
    with pytest.raises(ValueError):
        build_backend("no-such-backend")


def test_factory_returns_implementations():
    from bot.llm.echo import EchoBackend
    from bot.llm.ollama_backend import OllamaBackend
    from bot.llm.transformers_backend import TransformersBackend

    assert isinstance(build_backend("echo"), EchoBackend)
    assert isinstance(build_backend("ollama"), OllamaBackend)
    # transformers конструируется без загрузки модели (ленивая загрузка)
    assert isinstance(build_backend("transformers", model_name="x/y"),
                      TransformersBackend)


def test_default_stream_falls_back_to_generate():
    from bot.llm.echo import EchoBackend

    backend = EchoBackend()
    pieces = list(backend.generate_stream(
        [ChatMessage(Role.USER.value, "привет")]
    ))
    assert len(pieces) == 1
    assert "привет" in pieces[0]
