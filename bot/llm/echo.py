"""Заглушка LLM: отвечает эхом + простой реакцией. Позволяет запускать
весь стек (API, веб, хранилище) без установки моделей."""
from .base import ChatMessage, LLMBackend

_GREETINGS = {"привет", "здравствуй", "hi", "hello", "добрый день"}


class EchoBackend(LLMBackend):
    @property
    def name(self) -> str:
        return "echo-stub"

    def generate(self, messages: list[ChatMessage]) -> str:
        last = messages[-1].content.strip() if messages else ""
        low = last.lower()
        if any(low.startswith(g) for g in _GREETINGS):
            return f"Привет! (заглушка) Вы написали: «{last}»"
        if low.endswith("?"):
            return f"Хороший вопрос. (заглушка) Короткий ответ на «{last[:-1]}»: возможно."
        return f"(заглушка, без реальной модели) Получено сообщение: «{last}»"
