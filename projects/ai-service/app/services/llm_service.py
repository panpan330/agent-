import logging
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from time import perf_counter
from typing import Any

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    UnprocessableEntityError,
)

from app.core.config import Settings
from app.core.exceptions import AppException
from app.schemas.chat import ChatMessage
from app.services.llm_client import create_openai_compatible_client
from app.services.message_builder import (
    build_multi_turn_messages,
    serialize_chat_messages,
)
from app.services.prompt_builder import PromptParts, build_clear_user_prompt


logger = logging.getLogger(__name__)

DEFAULT_CHAT_CONSTRAINTS = (
    "用中文回答",
    "回答适合刚开始学习 AI 应用开发的人",
    "解释概念时先讲人话，再补充术语",
    "不要编造不确定的信息",
)
DEFAULT_CHAT_OUTPUT_FORMAT = "先直接回答用户问题，再在需要时补充关键要点。"
DEFAULT_CHAT_FAILURE_POLICY = "如果不确定，请明确说不确定，并说明需要查官方文档。"


@dataclass(frozen=True)
class LLMTokenUsage:
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


def build_chat_prompt(user_message: str) -> str:
    return build_clear_user_prompt(
        PromptParts(
            task=user_message,
            constraints=DEFAULT_CHAT_CONSTRAINTS,
            output_format=DEFAULT_CHAT_OUTPUT_FORMAT,
            failure_policy=DEFAULT_CHAT_FAILURE_POLICY,
        )
    )


def build_chat_messages(
    user_message: str,
    *,
    history: Sequence[ChatMessage] | None = None,
) -> list[ChatMessage]:
    return build_multi_turn_messages(
        build_chat_prompt(user_message),
        history=history,
    )


def extract_first_reply(completion: Any) -> str:
    try:
        reply = completion.choices[0].message.content
    except (AttributeError, IndexError, TypeError) as exc:
        raise AppException(
            code="LLM_BAD_RESPONSE",
            message="模型返回格式异常",
            status_code=502,
        ) from exc

    if not isinstance(reply, str) or not reply.strip():
        raise AppException(
            code="LLM_EMPTY_RESPONSE",
            message="模型返回了空内容",
            status_code=502,
        )
    return reply.strip()


def _get_usage_value(usage: Any, field_name: str) -> int | None:
    if isinstance(usage, dict):
        value = usage.get(field_name)
    else:
        value = getattr(usage, field_name, None)

    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None


def extract_token_usage(completion: Any) -> LLMTokenUsage:
    usage = getattr(completion, "usage", None)
    if usage is None:
        return LLMTokenUsage()

    return LLMTokenUsage(
        prompt_tokens=_get_usage_value(usage, "prompt_tokens"),
        completion_tokens=_get_usage_value(usage, "completion_tokens"),
        total_tokens=_get_usage_value(usage, "total_tokens"),
    )


def _get_first_choice(response_part: Any) -> Any | None:
    if isinstance(response_part, dict):
        choices = response_part.get("choices")
    else:
        choices = getattr(response_part, "choices", None)

    try:
        return choices[0]
    except (IndexError, TypeError):
        return None


def extract_stream_delta_content(chunk: Any) -> str | None:
    choice = _get_first_choice(chunk)
    if choice is None:
        return None

    if isinstance(choice, dict):
        delta = choice.get("delta")
    else:
        delta = getattr(choice, "delta", None)

    if isinstance(delta, dict):
        content = delta.get("content")
    else:
        content = getattr(delta, "content", None)

    if not isinstance(content, str) or content == "":
        return None
    return content


def has_token_usage(usage: LLMTokenUsage) -> bool:
    return any(
        value is not None
        for value in (
            usage.prompt_tokens,
            usage.completion_tokens,
            usage.total_tokens,
        )
    )


def map_openai_error_to_app_exception(exc: Exception) -> AppException:
    if isinstance(exc, RateLimitError):
        return AppException(
            code="LLM_RATE_LIMITED",
            message="模型服务请求过于频繁，请稍后重试。",
            status_code=429,
        )
    if isinstance(exc, APITimeoutError):
        return AppException(
            code="LLM_TIMEOUT",
            message="模型调用超时，请稍后重试。",
            status_code=504,
        )
    if isinstance(exc, AuthenticationError):
        return AppException(
            code="LLM_AUTHENTICATION_FAILED",
            message="模型服务认证失败，请检查服务端 API key 配置。",
            status_code=502,
        )
    if isinstance(exc, PermissionDeniedError):
        return AppException(
            code="LLM_PERMISSION_DENIED",
            message="模型服务拒绝访问，请检查服务端模型权限配置。",
            status_code=502,
        )
    if isinstance(exc, NotFoundError):
        return AppException(
            code="LLM_RESOURCE_NOT_FOUND",
            message="模型服务资源不存在，请检查模型名或接口地址配置。",
            status_code=502,
        )
    if isinstance(exc, (BadRequestError, UnprocessableEntityError)):
        return AppException(
            code="LLM_BAD_REQUEST",
            message="模型请求参数错误，请联系开发者检查模型调用配置。",
            status_code=502,
        )
    if isinstance(exc, InternalServerError):
        return AppException(
            code="LLM_PROVIDER_ERROR",
            message="模型服务暂时异常，请稍后重试。",
            status_code=502,
        )
    if isinstance(exc, APIConnectionError):
        return AppException(
            code="LLM_CONNECTION_ERROR",
            message="无法连接模型服务，请稍后重试。",
            status_code=502,
        )
    if isinstance(exc, APIStatusError):
        return AppException(
            code="LLM_PROVIDER_STATUS_ERROR",
            message="模型服务返回异常状态，请稍后重试。",
            status_code=502,
        )
    return AppException(
        code="LLM_CALL_FAILED",
        message="模型调用失败，请稍后重试。",
        status_code=502,
    )


class LLMChatService:
    def __init__(self, settings: Settings, client: Any | None = None) -> None:
        self.settings = settings
        self._client = client

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client

        try:
            self._client = create_openai_compatible_client(self.settings)
        except ValueError as exc:
            raise AppException(
                code="LLM_API_KEY_MISSING",
                message="LLM API key 未配置，请先在本机 .env 中配置 LLM_API_KEY。",
                status_code=500,
            ) from exc
        return self._client

    def _log_success(self, elapsed_ms: float, usage: LLMTokenUsage) -> None:
        logger.info(
            (
                "llm_chat_succeeded provider=%s model=%s elapsed_ms=%.2f "
                "prompt_tokens=%s completion_tokens=%s total_tokens=%s"
            ),
            self.settings.llm_provider,
            self.settings.llm_model,
            elapsed_ms,
            usage.prompt_tokens,
            usage.completion_tokens,
            usage.total_tokens,
        )

    def _log_failure(
        self,
        app_exception: AppException,
        elapsed_ms: float,
        *,
        exc_info: bool = False,
    ) -> None:
        logger.warning(
            "llm_chat_failed code=%s provider=%s model=%s status_code=%s elapsed_ms=%.2f",
            app_exception.code,
            self.settings.llm_provider,
            self.settings.llm_model,
            app_exception.status_code,
            elapsed_ms,
            exc_info=exc_info,
        )

    def _log_stream_success(
        self,
        elapsed_ms: float,
        usage: LLMTokenUsage,
        *,
        chunk_count: int,
        content_chunk_count: int,
    ) -> None:
        logger.info(
            (
                "llm_stream_chat_succeeded provider=%s model=%s elapsed_ms=%.2f "
                "chunks=%s content_chunks=%s prompt_tokens=%s "
                "completion_tokens=%s total_tokens=%s"
            ),
            self.settings.llm_provider,
            self.settings.llm_model,
            elapsed_ms,
            chunk_count,
            content_chunk_count,
            usage.prompt_tokens,
            usage.completion_tokens,
            usage.total_tokens,
        )

    def _log_stream_failure(
        self,
        app_exception: AppException,
        elapsed_ms: float,
        *,
        chunk_count: int,
        content_chunk_count: int,
        exc_info: bool = False,
    ) -> None:
        logger.warning(
            (
                "llm_stream_chat_failed code=%s provider=%s model=%s "
                "status_code=%s elapsed_ms=%.2f chunks=%s content_chunks=%s"
            ),
            app_exception.code,
            self.settings.llm_provider,
            self.settings.llm_model,
            app_exception.status_code,
            elapsed_ms,
            chunk_count,
            content_chunk_count,
            exc_info=exc_info,
        )

    def generate_reply(
        self,
        user_message: str,
        *,
        history: Sequence[ChatMessage] | None = None,
    ) -> str:
        if not self.settings.has_llm_api_key:
            raise AppException(
                code="LLM_API_KEY_MISSING",
                message="LLM API key 未配置，请先在本机 .env 中配置 LLM_API_KEY。",
                status_code=500,
            )

        messages = build_chat_messages(user_message, history=history)
        start_time = perf_counter()
        try:
            completion = self._get_client().chat.completions.create(
                model=self.settings.llm_model,
                messages=serialize_chat_messages(messages),
            )
            reply = extract_first_reply(completion)
        except AppException as exc:
            self._log_failure(exc, (perf_counter() - start_time) * 1000)
            raise
        except Exception as exc:
            app_exception = map_openai_error_to_app_exception(exc)
            self._log_failure(
                app_exception,
                (perf_counter() - start_time) * 1000,
                exc_info=True,
            )
            raise app_exception from exc

        self._log_success(
            (perf_counter() - start_time) * 1000,
            extract_token_usage(completion),
        )
        return reply

    def _iter_stream_reply_chunks(
        self,
        stream: Iterator[Any],
        start_time: float,
    ) -> Iterator[str]:
        usage = LLMTokenUsage()
        chunk_count = 0
        content_chunk_count = 0

        try:
            for chunk in stream:
                chunk_count += 1

                chunk_usage = extract_token_usage(chunk)
                if has_token_usage(chunk_usage):
                    usage = chunk_usage

                content = extract_stream_delta_content(chunk)
                if content is None:
                    continue

                content_chunk_count += 1
                yield content
        except AppException as exc:
            self._log_stream_failure(
                exc,
                (perf_counter() - start_time) * 1000,
                chunk_count=chunk_count,
                content_chunk_count=content_chunk_count,
            )
            raise
        except Exception as exc:
            app_exception = map_openai_error_to_app_exception(exc)
            self._log_stream_failure(
                app_exception,
                (perf_counter() - start_time) * 1000,
                chunk_count=chunk_count,
                content_chunk_count=content_chunk_count,
                exc_info=True,
            )
            raise app_exception from exc

        self._log_stream_success(
            (perf_counter() - start_time) * 1000,
            usage,
            chunk_count=chunk_count,
            content_chunk_count=content_chunk_count,
        )

    def stream_reply(
        self,
        user_message: str,
        *,
        history: Sequence[ChatMessage] | None = None,
    ) -> Iterator[str]:
        if not self.settings.has_llm_api_key:
            raise AppException(
                code="LLM_API_KEY_MISSING",
                message="LLM API key 未配置，请先在本机 .env 中配置 LLM_API_KEY。",
                status_code=500,
            )

        messages = build_chat_messages(user_message, history=history)
        start_time = perf_counter()
        try:
            stream = self._get_client().chat.completions.create(
                model=self.settings.llm_model,
                messages=serialize_chat_messages(messages),
                stream=True,
                stream_options={"include_usage": True},
            )
        except AppException as exc:
            self._log_stream_failure(
                exc,
                (perf_counter() - start_time) * 1000,
                chunk_count=0,
                content_chunk_count=0,
            )
            raise
        except Exception as exc:
            app_exception = map_openai_error_to_app_exception(exc)
            self._log_stream_failure(
                app_exception,
                (perf_counter() - start_time) * 1000,
                chunk_count=0,
                content_chunk_count=0,
                exc_info=True,
            )
            raise app_exception from exc

        return self._iter_stream_reply_chunks(iter(stream), start_time)


def create_llm_chat_service(settings: Settings) -> LLMChatService:
    return LLMChatService(settings)
