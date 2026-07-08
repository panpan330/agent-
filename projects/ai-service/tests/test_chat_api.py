from fastapi.testclient import TestClient

from app.core.trace import TRACE_ID_HEADER


def test_chat_replies_with_mock_message(client: TestClient) -> None:
    response = client.post(
        "/chat",
        json={"message": "请解释 FastAPI 是什么"},
    )
    data = response.json()

    assert response.status_code == 200
    assert data == {"reply": "你刚才说的是：请解释 FastAPI 是什么"}


def test_chat_rejects_missing_message(client: TestClient) -> None:
    response = client.post("/chat", headers={TRACE_ID_HEADER: "trace-missing"}, json={})
    data = response.json()

    assert response.status_code == 422
    assert data["code"] == "VALIDATION_ERROR"
    assert data["message"] == "请求参数校验失败"
    assert data["trace_id"] == "trace-missing"
    assert data["details"][0]["loc"] == ["body", "message"]
    assert data["details"][0]["type"] == "missing"


def test_chat_rejects_empty_message(client: TestClient) -> None:
    response = client.post(
        "/chat",
        headers={TRACE_ID_HEADER: "trace-empty"},
        json={"message": ""},
    )
    data = response.json()

    assert response.status_code == 422
    assert data["code"] == "VALIDATION_ERROR"
    assert data["message"] == "请求参数校验失败"
    assert data["trace_id"] == "trace-empty"
    assert data["details"][0]["loc"] == ["body", "message"]
    assert data["details"][0]["type"] == "string_too_short"


def test_chat_rejects_non_string_message(client: TestClient) -> None:
    response = client.post(
        "/chat",
        headers={TRACE_ID_HEADER: "trace-type"},
        json={"message": 123},
    )
    data = response.json()

    assert response.status_code == 422
    assert data["code"] == "VALIDATION_ERROR"
    assert data["message"] == "请求参数校验失败"
    assert data["trace_id"] == "trace-type"
    assert data["details"][0]["loc"] == ["body", "message"]
    assert data["details"][0]["type"] == "string_type"


def test_chat_does_not_allow_get(client: TestClient) -> None:
    response = client.get("/chat", headers={TRACE_ID_HEADER: "trace-method"})
    data = response.json()

    assert response.status_code == 405
    assert data == {
        "code": "METHOD_NOT_ALLOWED",
        "message": "请求方法不允许",
        "trace_id": "trace-method",
    }
