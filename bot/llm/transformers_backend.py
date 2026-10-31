"""Локальный ИИ через HuggingFace transformers (CPU-friendly маленькие модели).

Модель загружается лениво при первом запросе, чтобы старт сервиса был быстрым.
Рекомендуемые компактные модели: Qwen/Qwen2.5-0.5B-Instruct, TinyLlama/TinyLlama-1.1B-Chat-v1.0
"""
from __future__ import annotations

import torch

from .base import ChatMessage, LLMBackend


class TransformersBackend(LLMBackend):
    def __init__(self, model_name: str, max_new_tokens: int = 256):
        self._model_name = model_name
        self._max_new_tokens = max_new_tokens
        self._tokenizer = None
        self._model = None

    @property
    def name(self) -> str:
        return self._model_name

    def _load(self):
        if self._model is None:
            from transformers import AutoModelForCausalLM, AutoTokenizer

            self._tokenizer = AutoTokenizer.from_pretrained(self._model_name)
            self._model = AutoModelForCausalLM.from_pretrained(
                self._model_name,
                torch_dtype=torch.float32,  # CPU; для GPU замените на float16/bnb-квантование
                device_map="auto",
            )

    def generate(self, messages: list[ChatMessage]) -> str:
        self._load()
        conversation = [{"role": m.role, "content": m.content} for m in messages]

        # chat-токенизация, если модель её поддерживает
        if self._tokenizer.chat_template is not None:
            prompt = self._tokenizer.apply_chat_template(
                conversation, tokenize=False, add_generation_prompt=True
            )
            inputs = self._tokenizer(prompt, return_tensors="pt").to(self._model.device)
        else:
            plain = "\n".join(f"{m.role}: {m.content}" for m in messages)
            inputs = self._tokenizer(plain, return_tensors="pt").to(self._model.device)

        with torch.no_grad():
            output_ids = self._model.generate(
                **inputs,
                max_new_tokens=self._max_new_tokens,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=self._tokenizer.eos_token_id,
            )
        new_tokens = output_ids[0][inputs["input_ids"].shape[1]:]
        text = self._tokenizer.decode(new_tokens, skip_special_tokens=True)
        return text.strip()
