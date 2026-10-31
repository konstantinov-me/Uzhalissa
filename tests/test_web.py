"""Тесты веб-интерфейса (HTML-оболочка поверх того же ChatService)."""


def test_index_renders(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Uzhalissa" in r.text
    assert 'action="/send"' in r.text


def test_send_prg_flow_with_cookie(client):
    """POST /send → 303 на /, cookie chat_id, история видна при следующем GET."""
    r = client.post("/send", data={"message": "Привет, веб!"}, follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/"
    assert "chat_id" in r.cookies

    page = client.get("/").text
    assert "Привет, веб!" in page          # реплики пользователя сохраняются
    assert "echo-stub" in page             # имя модели в шапке


def test_stream_page_served(client):
    r = client.get("/chat")
    assert r.status_code == 200
    assert "/api/v1/chat/stream" in r.text  # страница использует SSE-эндпоинт


def test_web_json_endpoint(client):
    r = client.post("/chat/send", json={"message": "апи через веб"})
    assert r.status_code == 200
    body = r.json()
    assert body["assistant_message"]["content"]
