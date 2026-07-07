from fastapi.testclient import TestClient


def test_chat_replies_with_mock_message(client: TestClient) -> None:
    response = client.post(
        "/chat",
        json={"message": "请解释 FastAPI 是什么"},
    )
    data = response.json()

    assert response.status_code == 200
    assert data == {"reply": "你刚才说的是：请解释 FastAPI 是什么"}


def test_chat_rejects_missing_message(client: TestClient) -> None:
    response = client.post("/chat", json={})
    data = response.json()

    assert response.status_code == 422
    assert data["detail"][0]["loc"] == ["body", "message"]
    assert data["detail"][0]["type"] == "missing"


def test_chat_rejects_empty_message(client: TestClient) -> None:
    response = client.post("/chat", json={"message": ""})
    data = response.json()

    assert response.status_code == 422
    assert data["detail"][0]["loc"] == ["body", "message"]
    assert data["detail"][0]["type"] == "string_too_short"


def test_chat_rejects_non_string_message(client: TestClient) -> None:
    response = client.post("/chat", json={"message": 123})
    data = response.json()

    assert response.status_code == 422
    assert data["detail"][0]["loc"] == ["body", "message"]
    assert data["detail"][0]["type"] == "string_type"


def test_chat_does_not_allow_get(client: TestClient) -> None:
    response = client.get("/chat")

    assert response.status_code == 405
