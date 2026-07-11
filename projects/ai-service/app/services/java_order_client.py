from collections.abc import Mapping
from typing import Any

import httpx

from app.core.config import Settings
from app.core.exceptions import AppException


class JavaOrderClient:
    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.strip().rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    @classmethod
    def from_settings(cls, settings: Settings) -> "JavaOrderClient":
        return cls(
            base_url=settings.resolved_java_mock_service_base_url,
            timeout_seconds=settings.java_mock_service_timeout_seconds,
        )

    def get_order(self, order_id: str) -> Mapping[str, Any]:
        try:
            with httpx.Client(
                base_url=self.base_url,
                timeout=self.timeout_seconds,
                transport=self.transport,
            ) as client:
                response = client.get(f"/orders/{order_id}")
        except httpx.TimeoutException as exc:
            raise AppException(
                code="TOOL_TIMEOUT",
                message="订单查询工具调用超时，请稍后重试。",
                status_code=504,
            ) from exc
        except httpx.RequestError as exc:
            raise AppException(
                code="TOOL_UPSTREAM_ERROR",
                message="订单查询服务暂时不可用，请稍后重试。",
                status_code=502,
            ) from exc

        if response.status_code == 404:
            raise AppException(
                code="ORDER_NOT_FOUND",
                message="订单不存在，请确认订单号是否正确。",
                status_code=404,
            )

        if response.status_code >= 500:
            raise AppException(
                code="TOOL_UPSTREAM_ERROR",
                message="订单查询服务暂时不可用，请稍后重试。",
                status_code=502,
            )

        if response.status_code != 200:
            raise AppException(
                code="TOOL_UPSTREAM_ERROR",
                message="订单查询服务返回了无法处理的状态，请稍后重试。",
                status_code=502,
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise AppException(
                code="TOOL_RESULT_VALIDATION_FAILED",
                message="订单查询服务返回的 JSON 格式不正确。",
                status_code=502,
            ) from exc

        if not isinstance(data, dict):
            raise AppException(
                code="TOOL_RESULT_VALIDATION_FAILED",
                message="订单查询服务返回的数据结构不正确。",
                status_code=502,
            )

        return data
