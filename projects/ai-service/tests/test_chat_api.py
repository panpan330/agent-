from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.trace import TRACE_ID_HEADER
from app.routers.chat import get_llm_chat_service


class FakeLLMChatService:
    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.messages: list[str] = []

    def generate_reply(self, user_message: str) -> str:
        self.messages.append(user_message)
        return self.reply


def test_chat_returns_llm_reply(app: FastAPI, client: TestClient) -> None:
    fake_service = FakeLLMChatService("FastAPI 是一个 Python Web 框架。")
    app.dependency_overrides[get_llm_chat_service] = lambda: fake_service

    response = client.post(
        "/chat",
        json={"message": "请解释 FastAPI 是什么"},
    )
    data = response.json()

    assert response.status_code == 200
    assert data == {"reply": "FastAPI 是一个 Python Web 框架。"}
    assert fake_service.messages == ["请解释 FastAPI 是什么"]


def test_chat_returns_config_error_when_llm_key_is_missing(
    client: TestClient,
) -> None:
    response = client.post(
        "/chat",
        headers={TRACE_ID_HEADER: "trace-no-key"},
        json={"message": "请解释 FastAPI 是什么"},
    )
    data = response.json()

    assert response.status_code == 500
    assert data == {
        "code": "LLM_API_KEY_MISSING",
        "message": "LLM API key 未配置，请先在本机 .env 中配置 LLM_API_KEY。",
        "trace_id": "trace-no-key",
    }


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
