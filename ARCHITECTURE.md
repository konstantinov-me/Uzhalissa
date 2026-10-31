# Uzhalissa — модульный чат-бот с локальным ИИ

Лёгкий чат-бот на **Python**: FastAPI + SQLite + подключаемый локальный LLM-бэкенд
(заглушка / HuggingFace transformers / Ollama). Два внешних интерфейса из одного ядра:
**REST API** (JSON, Swagger) и **веб-интерфейс** (HTML, Jinja2).

## Архитектура

```
bot/
├── main.py               # точка входа: сборка FastAPI-приложения
├── dependencies.py       # composition root: выбор реализаций по конфигурации
├── config/settings.py    # настройки из ENV (.env)
├── core/                 # ЯДРО (не знает про HTTP и про конкретную модель)
│   ├── models.py         #   доменные модели: Chat, Message, контракты запросов
│   └── service.py        #   ChatService: бизнес-логика диалога
├── llm/                  # СЛОЙ ИИ (интерфейс LLMBackend)
│   ├── base.py           #   абстракция + фабрика бэкендов
│   ├── echo.py           #   заглушка для разработки без GPU
│   ├── transformers_backend.py  # локальная модель через HF transformers
│   └── ollama_backend.py        # локальный сервер Ollama
├── storage/repository.py # ХРАНИЛИЩЕ: SQLite, ChatRepository
├── api/routes.py         # REST API (/api/v1/*)
└── web/                  # ВЕБ-ИНТЕРФЕЙС (/, /send) + templates/chat.html
```

Принципы:
- **Одно ядро, две оболочки.** `api` и `web` — тонкие роутеры, оба вызывают только `ChatService`.
- **Плагинность ИИ.** Модель подключается через абстрактный `LLMBackend`; чтобы добавить
  новый бэкенд (например, llama.cpp), реализуйте один метод `generate()` и зарегистрируйте в фабрике.
- **Направление зависимостей** — только внутрь: `api/web → core → (llm, storage)`; ядро ничего
  не знает о внешних слоях. Конкретные реализации склеиваются в `dependencies.py`.

## Быстрый старт

```bash
pip install -r requirements.txt
uvicorn bot.main:app --reload
```

- Веб-чат: http://127.0.0.1:8000/
- Swagger API: http://127.0.0.1:8000/docs

По умолчанию работает заглушка `echo` (реальная модель не нужна).

## Подключение локального ИИ

Вариант 1 — **Ollama** (рекомендуется, simplest):
```bash
ollama pull qwen2.5:0.5b-instruct
echo "llm_backend=ollama" > .env
```

Вариант 2 — **transformers** (модель скачивается при первом запросе):
```bash
echo "llm_backend=transformers" > .env   # pip install transformers torch
```

## Внешний REST API

| Метод | Путь | Назначение |
|---|---|---|
| GET | `/api/v1/health` | статус и имя активной модели |
| POST | `/api/v1/chat` | задать вопрос (`{message, chat_id?}`); без `chat_id` создаётся новый диалог |
| GET | `/api/v1/chats` | список диалогов |
| GET | `/api/v1/chats/{id}/messages` | история диалога |
| DELETE | `/api/v1/chats/{id}` | удалить диалог |

Пример:
```bash
curl -s localhost:8000/api/v1/chat -H 'Content-Type: application/json' \
     -d '{"message": "Привет! Как дела?"}'
```

## Веб- интерфейс

Классическая серверная страница: форма POST на `/send`, состояние диалога хранится
в cookie `chat_id` (паттерн Post/Redirect/Get), история рендерится Jinja2-шаблоном
без JS-фреймворков.

## Конфигурация (ENV / .env)

| Переменная | По умолчанию | Описание |
|---|---|---|
| `llm_backend` | `echo` | `echo` \| `transformers` \| `ollama` |
| `model_name` | `Qwen/Qwen2.5-0.5B-Instruct` | модель для transformers |
| `ollama_base_url` / `ollama_model` | `http://localhost:11434` / `qwen2.5:0.5b-instruct` | для Ollama |
| `max_new_tokens` | `256` | лимит генерации |
| `db_path` | `data/chats.db` | файл SQLite |
| `system_prompt` | см. settings.py | системный промпт ассистента |
