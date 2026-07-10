from collections.abc import Iterable
from types import SimpleNamespace
from typing import Any

import httpx
from openai import APIStatusError


def make_usage(
    *,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    total_tokens: int | None = None,
) -> object:
    return SimpleNamespace(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )


def make_chat_completion(
    content: str | None,
    *,
    usage: object | None = None,
) -> object:
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content),
            )
        ],
        usage=usage,
    )


def make_stream_chunk(
    content: str | None = None,
    usage: object | None = None,
) -> object:
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                delta=SimpleNamespace(content=content),
            )
        ],
        usage=usage,
    )


class FakeChatCompletions:
    def __init__(
        self,
        content: str | None = "模型回复",
        *,
        error: Exception | None = None,
        usage: object | None = None,
        stream_chunks: Iterable[object] | None = None,
    ) -> None:
        self.content = content
        self.error = error
        self.usage = usage
        self.stream_chunks = stream_chunks
        self.calls: list[dict[str, Any]] = []

    @property
    def last_call(self) -> dict[str, Any]:
        if not self.calls:
            raise AssertionError("FakeChatCompletions was not called")
        return self.calls[-1]

    def create(self, **kwargs: Any) -> object:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        if kwargs.get("stream") is True:
            return iter(self.stream_chunks or [])
        return make_chat_completion(self.content, usage=self.usage)


class FakeOpenAICompatibleClient:
    def __init__(self, completions: FakeChatCompletions) -> None:
        self.completions = completions
        self.chat = SimpleNamespace(completions=completions)


def make_status_error(
    error_class: type[APIStatusError],
    status_code: int,
    *,
    message: str = "provider error",
) -> APIStatusError:
    request = httpx.Request("POST", "https://example.com/chat/completions")
    response = httpx.Response(
        status_code=status_code,
        request=request,
        json={"error": {"message": message}},
    )
    return error_class(
        message,
        response=response,
        body={"error": {"message": message}},
    )
