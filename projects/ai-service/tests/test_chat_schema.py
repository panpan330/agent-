import pytest
from pydantic import ValidationError

from app.schemas.chat import ChatRequest, ChatResponse


def test_chat_request_accepts_message() -> None:
    request = ChatRequest(message="请解释 FastAPI 是什么")

    assert request.message == "请解释 FastAPI 是什么"


def test_chat_request_rejects_missing_message() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ChatRequest()

    error = exc_info.value.errors()[0]
    assert error["loc"] == ("message",)
    assert error["type"] == "missing"


def test_chat_request_rejects_empty_message() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ChatRequest(message="")

    error = exc_info.value.errors()[0]
    assert error["loc"] == ("message",)
    assert error["type"] == "string_too_short"


def test_chat_request_rejects_non_string_message() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ChatRequest(message=123)

    error = exc_info.value.errors()[0]
    assert error["loc"] == ("message",)
    assert error["type"] == "string_type"


def test_chat_response_accepts_reply() -> None:
    response = ChatResponse(reply="你刚才说的是：请解释 FastAPI 是什么")

    assert response.reply == "你刚才说的是：请解释 FastAPI 是什么"


def test_chat_response_rejects_missing_reply() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ChatResponse()

    error = exc_info.value.errors()[0]
    assert error["loc"] == ("reply",)
    assert error["type"] == "missing"


def test_chat_response_rejects_empty_reply() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ChatResponse(reply="")

    error = exc_info.value.errors()[0]
    assert error["loc"] == ("reply",)
    assert error["type"] == "string_too_short"


def test_chat_response_rejects_non_string_reply() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ChatResponse(reply=123)

    error = exc_info.value.errors()[0]
    assert error["loc"] == ("reply",)
    assert error["type"] == "string_type"
