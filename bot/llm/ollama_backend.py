"""Локальный ИИ через Ollama (https://ollama.com) — самый простой способ
поднять настоящую модель локально: `ollama pull qwen2.5:0.5b-instruct`.

Обращение идёт к HTTP-API Ollama (/api/chat), поэтому тяжёлые зависимости не нужны.
"""
from __future__ import annotations

import json
import urllib.request

from .base import ChatMessage, LLMBackend


class OllamaBackend(LLMBackend):
    def __init__(self, base_url: str = "http://localhost:11434",
                 model: str = "qwen2.5:0.5b-instruct"):
        self._base_url = base_url.rstrip("/")
        self._model = model

    @property
    def name(self) -> str:
        return f"ollama/{self._model}"

    def _request(self, messages: list[ChatMessage], stream: bool):
        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": stream,
        }
        req = urllib.request.Request(
            f"{self._base_url}/api/chat",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        return urllib.request.urlopen(req, timeout=120)

    def generate(self, messages: list[ChatMessage]) -> str:
        with self._request(messages, stream=False) as resp:
            data = json.loads(resp.read())
        return data.get("message", {}).get("content", "").strip()

    def generate_stream(self, messages: list[ChatMessage]):
        """Настоящий стриминг: Ollama отдаёт JSON-lines с частями ответа."""
        with self._request(messages, stream=True) as resp:
            for line in resp:
                if not line.strip():
                    continue
                chunk = json.loads(line)
                piece = chunk.get("message", {}).get("content", "")
                if piece:
                    yield piece
