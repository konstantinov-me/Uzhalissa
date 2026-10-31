"""Тесты REST API (/api/v1/*) — внешнего машинного интерфейса."""


def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["model"] == "echo-stub"


def test_chat_creates_new_dialog(client):
    r = client.post("/api/v1/chat", json={"message": "Привет!"})
    assert r.status_code == 200
    body = r.json()
    assert body["chat_id"]
    assert body["assistant_message"]["content"]
    assert body["user_message"]["role"] == "user"
    assert body["model"] == "echo-stub"


def test_chat_followup_keeps_context(client):
    first = client.post("/api/v1/chat", json={"message": "Первый вопрос?"}).json()
    second = client.post("/api/v1/chat",
                         json={"message": "Второй вопрос?",
                               "chat_id": first["chat_id"]}).json()
    assert second["chat_id"] == first["chat_id"]
    # история диалога должна содержать 4 сообщения
    hist = client.get(f"/api/v1/chats/{first['chat_id']}/messages").json()
    assert len(hist) == 4
    assert [m["role"] for m in hist] == ["user", "assistant", "user", "assistant"]


def test_list_and_delete_chats(client):
    chat_id = client.post("/api/v1/chat", json={"message": "данные"}).json()["chat_id"]
    chats = client.get("/api/v1/chats").json()
    assert any(c["id"] == chat_id for c in chats)

    assert client.delete(f"/api/v1/chats/{chat_id}").status_code == 204
    assert client.get(f"/api/v1/chats/{chat_id}/messages").status_code == 404
    assert client.delete(f"/api/v1/chats/{chat_id}").status_code == 404


def test_validation_empty_message(client):
    assert client.post("/api/v1/chat", json={"message": ""}).status_code == 422


def test_stream_sse_events(client):
    """SSE-стриминг: meta (chat_id) → delta (части) → done (id сообщения)."""
    with client.stream("POST", "/api/v1/chat/stream",
                       json={"message": "Стриминг привет"}) as r:
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/event-stream")
        events = []
        current = None
        for line in r.iter_lines():
            if line.startswith("event: "):
                current = line[7:]
            elif line.startswith("data: ") and current:
                events.append((current, line[6:]))
                current = None

    kinds = [e for e, _ in events]
    assert kinds[0] == "meta"
    assert "delta" in kinds
    assert kinds[-1] == "done"

    chat_id = events[0][1]  # первое событие — meta с id диалога
    # ответ сохранён в хранилище — проверка через обычный эндпоинт истории
    hist = client.get(f"/api/v1/chats/{chat_id}/messages").json()
    assert len(hist) == 2
    assert hist[1]["role"] == "assistant"
    assert hist[1]["content"]  # непустой ответ заглушки
