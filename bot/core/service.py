"""Ядро бизнес-логики (service layer).

Связывает хранилище и LLM-бэкенд; ничего не знает про HTTP —
и FastAPI-модуль, и веб-модуль вызывают только ChatService.
"""
from __future__ import annotations

from bot.config.settings import Settings
from bot.core.models import Chat, ChatResponse, Message, Role
from bot.llm.base import ChatMessage, LLMBackend
from bot.storage.repository import ChatRepository

# Сколько последних сообщений отправлять модели как контекст
CONTEXT_WINDOW = 20


class ChatService:
    def __init__(self, repo: ChatRepository, llm: LLMBackend, settings: Settings):
        self._repo = repo
        self._llm = llm
        self._settings = settings

    @property
    def model_name(self) -> str:
        return self._llm.name

    def ensure_chat(self, chat_id: str | None, title_from: str | None = None) -> Chat:
        """Вернуть существующий чат или создать новый."""
        if chat_id:
            chat = self._repo.get_chat(chat_id)
            if chat:
                return chat
        title = (title_from or "Новый диалог").strip()[:60] or "Новый диалог"
        return self._repo.create_chat(title=title)

    def ask(self, message: str, chat_id: str | None = None) -> ChatResponse:
        """Главный сценарий: сохранить вопрос → собрать контекст → сгенерировать ответ."""
        chat = self.ensure_chat(chat_id, title_from=message)

        user_msg = self._repo.add_message(chat.id, Role.USER, message)

        history = self._repo.get_history(chat.id, limit=CONTEXT_WINDOW)
        prompt_messages = [ChatMessage(Role.SYSTEM.value, self._settings.system_prompt)]
        prompt_messages += [ChatMessage(m.role.value, m.content) for m in history]

        answer = self._llm.generate(prompt_messages)
        assistant_msg = self._repo.add_message(chat.id, Role.ASSISTANT, answer)

        return ChatResponse(
            chat_id=chat.id,
            user_message=user_msg,
            assistant_message=assistant_msg,
            model=self._llm.name,
        )

    # --- тонкие прокси для UI/API ---
    def get_chat(self, chat_id: str) -> Chat | None:
        return self._repo.get_chat(chat_id)

    def list_chats(self) -> list[Chat]:
        return self._repo.list_chats()

    def get_messages(self, chat_id: str) -> list[Message]:
        return self._repo.get_history(chat_id, limit=500)

    def delete_chat(self, chat_id: str) -> bool:
        return self._repo.delete_chat(chat_id)
