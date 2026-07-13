from collections.abc import Callable
from typing import Any

import httpx
import pytest

from app.core.config import Settings
from app.core.exceptions import AppException
from app.core.trace import TRACE_ID_HEADER, reset_trace_id, set_trace_id
from app.services.java_order_client import JavaOrderClient


def make_order_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "order_id": "A1001",
        "customer_id": "C9001",
        "order_status": "waiting_shipment",
        "payment_status": "paid",
        "logistics_message": "商家已接单，等待仓库发货。",
        "latest_event": "仓库正在准备出库。",
        "can_create_ticket": True,
    }
    payload.update(overrides)
    return payload


def make_client(handler: Callable[[httpx.Request], httpx.Response]) -> JavaOrderClient:
    return JavaOrderClient(
        base_url="http://java-mock.test",
        timeout_seconds=1.0,
        transport=httpx.MockTransport(handler),
    )


def test_java_order_client_get_order_returns_json_payload() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/orders/A1001"
        return httpx.Response(200, json=make_order_payload(), request=request)

    client = make_client(handler)

    result = client.get_order("A1001")

    assert result["order_id"] == "A1001"
    assert result["customer_id"] == "C9001"


def test_java_order_client_forwards_current_trace_id() -> None:
    received_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        received_headers["trace_id"] = request.headers[TRACE_ID_HEADER]
        return httpx.Response(200, json=make_order_payload(), request=request)

    client = make_client(handler)
    token = set_trace_id("trace-order-client-001")

    try:
        client.get_order("A1001")
    finally:
        reset_trace_id(token)

    assert received_headers["trace_id"] == "trace-order-client-001"


def test_java_order_client_maps_404_to_order_not_found() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            404,
            json={"code": "ORDER_NOT_FOUND"},
            request=request,
        )

    client = make_client(handler)

    with pytest.raises(AppException) as exc_info:
        client.get_order("A9999")

    exc = exc_info.value
    assert exc.code == "ORDER_NOT_FOUND"
    assert exc.message == "订单不存在，请确认订单号是否正确。"
    assert exc.status_code == 404


def test_java_order_client_maps_500_to_upstream_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            500,
            json={"code": "ORDER_SERVICE_ERROR"},
            request=request,
        )

    client = make_client(handler)

    with pytest.raises(AppException) as exc_info:
        client.get_order("A500")

    exc = exc_info.value
    assert exc.code == "TOOL_UPSTREAM_ERROR"
    assert exc.message == "订单查询服务暂时不可用，请稍后重试。"
    assert exc.status_code == 502


def test_java_order_client_maps_timeout_to_tool_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("read timed out", request=request)

    client = make_client(handler)

    with pytest.raises(AppException) as exc_info:
        client.get_order("A_TIMEOUT")

    exc = exc_info.value
    assert exc.code == "TOOL_TIMEOUT"
    assert exc.message == "订单查询工具调用超时，请稍后重试。"
    assert exc.status_code == 504


def test_java_order_client_maps_request_error_to_upstream_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    client = make_client(handler)

    with pytest.raises(AppException) as exc_info:
        client.get_order("A1001")

    exc = exc_info.value
    assert exc.code == "TOOL_UPSTREAM_ERROR"
    assert exc.message == "订单查询服务暂时不可用，请稍后重试。"
    assert exc.status_code == 502


def test_java_order_client_rejects_invalid_json_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"not-json", request=request)

    client = make_client(handler)

    with pytest.raises(AppException) as exc_info:
        client.get_order("A1001")

    exc = exc_info.value
    assert exc.code == "TOOL_RESULT_VALIDATION_FAILED"
    assert exc.message == "订单查询服务返回的 JSON 格式不正确。"
    assert exc.status_code == 502


def test_java_order_client_rejects_non_object_json_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=["not", "an", "object"], request=request)

    client = make_client(handler)

    with pytest.raises(AppException) as exc_info:
        client.get_order("A1001")

    exc = exc_info.value
    assert exc.code == "TOOL_RESULT_VALIDATION_FAILED"
    assert exc.message == "订单查询服务返回的数据结构不正确。"
    assert exc.status_code == 502


def test_java_order_client_from_settings_uses_java_mock_config() -> None:
    settings = Settings(
        java_mock_service_base_url=" http://localhost:9001/ ",
        java_mock_service_timeout_seconds=2.5,
        _env_file=None,
    )

    client = JavaOrderClient.from_settings(settings)

    assert client.base_url == "http://localhost:9001"
    assert client.timeout_seconds == 2.5
