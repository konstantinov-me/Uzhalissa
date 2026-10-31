"""Конфигурация приложения через переменные окружения (pydantic-settings)."""
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- LLM ---
    llm_backend: str = "echo"            # echo | transformers | ollama
    model_name: str = "Qwen/Qwen2.5-0.5B-Instruct"  # только для transformers
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:0.5b-instruct"
    max_new_tokens: int = 256

    # --- Хранилище ---
    db_path: str = "data/chats.db"

    # --- API ---
    api_title: str = "Uzhalissa Chat Bot API"
    system_prompt: str = (
        "Ты — дружелюбный ассистент Узхалисса. Отвечай кратко и по делу."
    )

    class Config:
        env_file = ".env"
        env_prefix = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
