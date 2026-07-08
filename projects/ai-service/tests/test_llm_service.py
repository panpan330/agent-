from types import SimpleNamespace

import pytest

from app.core.config import Settings
from app.core.exceptions import AppException
from app.services.llm_service import LLMChatService, build_chat_messages


class FakeCompletions:
    def __init__(
        self,
        content: str | None = "模型回复",
        error: Exception | None = None,
    ) -> None:
        self.content = content
        self.error = error
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=self.content),
                )
            ]
        )


class FakeClient:
    def __init__(self, completions: FakeCompletions) -> None:
        self.completions = completions
        self.chat = SimpleNamespace(completions=completions)


def test_build_chat_messages_wraps_user_message_in_clear_prompt() -> None:
    messages = build_chat_messages("解释 API 是什么")

    assert messages[0].role == "system"
    assert messages[1].role == "user"
    assert "## 任务\n解释 API 是什么" in messages[1].content
    assert "## 要求" in messages[1].content
    assert "## 输出格式" in messages[1].content
    assert "## 无法完成时" in messages[1].content


def test_llm_chat_service_calls_openai_compatible_client() -> None:
    completions = FakeCompletions(content="  模型回复  ")
    service = LLMChatService(
        Settings(llm_api_key="test-key", llm_model="qwen-test", _env_file=None),
        client=FakeClient(completions),
    )

    reply = service.generate_reply("解释 FastAPI")

    assert reply == "模型回复"
    assert len(completions.calls) == 1
    call = completions.calls[0]
    assert call["model"] == "qwen-test"
    assert call["messages"][0]["role"] == "system"
    assert call["messages"][1]["role"] == "user"
    assert "## 任务\n解释 FastAPI" in call["messages"][1]["content"]


def test_llm_chat_service_requires_api_key() -> None:
    completions = FakeCompletions(content="不会被调用")
    service = LLMChatService(
        Settings(llm_api_key="", openai_api_key="", _env_file=None),
        client=FakeClient(completions),
    )

    with pytest.raises(AppException) as exc_info:
        service.generate_reply("解释 FastAPI")

    assert exc_info.value.code == "LLM_API_KEY_MISSING"
    assert exc_info.value.status_code == 500
    assert completions.calls == []


def test_llm_chat_service_rejects_empty_model_reply() -> None:
    service = LLMChatService(
        Settings(llm_api_key="test-key", _env_file=None),
        client=FakeClient(FakeCompletions(content="   ")),
    )

    with pytest.raises(AppException) as exc_info:
        service.generate_reply("解释 FastAPI")

    assert exc_info.value.code == "LLM_EMPTY_RESPONSE"
    assert exc_info.value.status_code == 502


def test_llm_chat_service_wraps_provider_errors() -> None:
    service = LLMChatService(
        Settings(llm_api_key="test-key", _env_file=None),
        client=FakeClient(FakeCompletions(error=RuntimeError("provider failed"))),
    )

    with pytest.raises(AppException) as exc_info:
        service.generate_reply("解释 FastAPI")

    assert exc_info.value.code == "LLM_CALL_FAILED"
    assert exc_info.value.status_code == 502
