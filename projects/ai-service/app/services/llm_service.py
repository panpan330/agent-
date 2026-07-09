import logging
from collections.abc import Sequence
from typing import Any

from openai import APITimeoutError, RateLimitError

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
        try:
            completion = self._get_client().chat.completions.create(
                model=self.settings.llm_model,
                messages=serialize_chat_messages(messages),
            )
        except AppException:
            raise
        except RateLimitError as exc:
            logger.warning(
                "llm_rate_limited provider=%s model=%s max_retries=%s",
                self.settings.llm_provider,
                self.settings.llm_model,
                self.settings.llm_max_retries,
            )
            raise AppException(
                code="LLM_RATE_LIMITED",
                message="模型服务请求过于频繁，请稍后重试。",
                status_code=429,
            ) from exc
        except APITimeoutError as exc:
            logger.warning(
                "llm_timeout provider=%s model=%s timeout_seconds=%s",
                self.settings.llm_provider,
                self.settings.llm_model,
                self.settings.request_timeout_seconds,
            )
            raise AppException(
                code="LLM_TIMEOUT",
                message="模型调用超时，请稍后重试。",
                status_code=504,
            ) from exc
        except Exception as exc:
            logger.exception(
                "llm_chat_failed provider=%s model=%s",
                self.settings.llm_provider,
                self.settings.llm_model,
            )
            raise AppException(
                code="LLM_CALL_FAILED",
                message="模型调用失败，请稍后重试。",
                status_code=502,
            ) from exc

        return extract_first_reply(completion)


def create_llm_chat_service(settings: Settings) -> LLMChatService:
    return LLMChatService(settings)
