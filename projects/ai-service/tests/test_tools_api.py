import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import AppException
from app.core.trace import TRACE_ID_HEADER
from app.schemas.tool import (
    OrderStatus,
    PaymentStatus,
    QueryOrderArgs,
    QueryOrderResult,
)
from app.tools.idempotency import IDEMPOTENCY_KEY_HEADER


def make_query_order_result(order_id: str = "A1001") -> QueryOrderResult:
    return QueryOrderResult(
        order_id=order_id,
        order_status=OrderStatus.WAITING_SHIPMENT,
        payment_status=PaymentStatus.PAID,
        logistics_message="商家已接单，等待仓库发货。",
        latest_event="仓库正在准备出库。",
        can_create_ticket=True,
        source="java_mock_service",
    )


def patch_query_order_tool(
    monkeypatch: pytest.MonkeyPatch,
    *,
    call_count_ref: dict[str, int] | None = None,
) -> None:
    from app.routers import tools as tools_router

    def fake_query_order_tool(
        arguments: QueryOrderArgs,
        **kwargs: object,
    ) -> QueryOrderResult:
        if call_count_ref is not None:
            call_count_ref["count"] += 1

        if arguments.order_id == "A9999":
            raise AppException(
                code="ORDER_NOT_FOUND",
                message="订单不存在，请确认订单号是否正确。",
                status_code=404,
            )
        if arguments.order_id == "A_TIMEOUT":
            raise AppException(
                code="TOOL_TIMEOUT",
                message="订单查询工具调用超时，请稍后重试。",
                status_code=504,
            )
        if arguments.order_id == "A500":
            raise AppException(
                code="TOOL_UPSTREAM_ERROR",
                message="订单查询服务暂时不可用，请稍后重试。",
                status_code=502,
            )

        return make_query_order_result(arguments.order_id)

    monkeypatch.setattr(
        tools_router,
        "run_query_order_tool",
        fake_query_order_tool,
    )


def test_query_order_api_returns_java_mock_order(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_query_order_tool(monkeypatch)

    response = client.post(
        "/tools/query-order",
        headers={TRACE_ID_HEADER: "trace-query-order"},
        json={"order_id": "A1001"},
    )
    data = response.json()

    assert response.status_code == 200
    assert response.headers[TRACE_ID_HEADER] == "trace-query-order"
    assert data == {
        "result": {
            "order_id": "A1001",
            "order_status": "waiting_shipment",
            "payment_status": "paid",
            "logistics_message": "商家已接单，等待仓库发货。",
            "latest_event": "仓库正在准备出库。",
            "can_create_ticket": True,
            "source": "java_mock_service",
        }
    }


def test_query_order_api_reuses_result_for_same_idempotency_key(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call_count_ref = {"count": 0}
    patch_query_order_tool(monkeypatch, call_count_ref=call_count_ref)

    first_response = client.post(
        "/tools/query-order",
        headers={
            TRACE_ID_HEADER: "trace-query-order-idem-first",
            IDEMPOTENCY_KEY_HEADER: "query-order-api-key-001",
        },
        json={"order_id": "A1001"},
    )
    second_response = client.post(
        "/tools/query-order",
        headers={
            TRACE_ID_HEADER: "trace-query-order-idem-second",
            IDEMPOTENCY_KEY_HEADER: "query-order-api-key-001",
        },
        json={"order_id": "A1001"},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json() == second_response.json()
    assert call_count_ref["count"] == 1


def test_query_order_api_rejects_same_idempotency_key_with_different_body(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_query_order_tool(monkeypatch)

    first_response = client.post(
        "/tools/query-order",
        headers={
            TRACE_ID_HEADER: "trace-query-order-idem-conflict-first",
            IDEMPOTENCY_KEY_HEADER: "query-order-api-key-002",
        },
        json={"order_id": "A1001"},
    )
    second_response = client.post(
        "/tools/query-order",
        headers={
            TRACE_ID_HEADER: "trace-query-order-idem-conflict-second",
            IDEMPOTENCY_KEY_HEADER: "query-order-api-key-002",
        },
        json={"order_id": "A1002"},
    )
    data = second_response.json()

    assert first_response.status_code == 200
    assert second_response.status_code == 409
    assert data == {
        "code": "IDEMPOTENCY_KEY_CONFLICT",
        "message": "同一个幂等键不能用于不同的工具调用参数。",
        "trace_id": "trace-query-order-idem-conflict-second",
    }


def test_query_order_api_rejects_invalid_idempotency_key(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_query_order_tool(monkeypatch)

    response = client.post(
        "/tools/query-order",
        headers={
            TRACE_ID_HEADER: "trace-query-order-idem-invalid",
            IDEMPOTENCY_KEY_HEADER: "abc",
        },
        json={"order_id": "A1001"},
    )
    data = response.json()

    assert response.status_code == 422
    assert data["code"] == "IDEMPOTENCY_KEY_INVALID"
    assert data["trace_id"] == "trace-query-order-idem-invalid"


def test_query_order_api_returns_not_found_for_missing_order(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_query_order_tool(monkeypatch)

    response = client.post(
        "/tools/query-order",
        headers={TRACE_ID_HEADER: "trace-order-missing"},
        json={"order_id": "A9999"},
    )
    data = response.json()

    assert response.status_code == 404
    assert data == {
        "code": "ORDER_NOT_FOUND",
        "message": "订单不存在，请确认订单号是否正确。",
        "trace_id": "trace-order-missing",
    }


def test_query_order_api_returns_timeout_error(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_query_order_tool(monkeypatch)

    response = client.post(
        "/tools/query-order",
        headers={TRACE_ID_HEADER: "trace-order-timeout"},
        json={"order_id": "A_TIMEOUT"},
    )
    data = response.json()

    assert response.status_code == 504
    assert data == {
        "code": "TOOL_TIMEOUT",
        "message": "订单查询工具调用超时，请稍后重试。",
        "trace_id": "trace-order-timeout",
    }


def test_query_order_api_returns_upstream_error(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_query_order_tool(monkeypatch)

    response = client.post(
        "/tools/query-order",
        headers={TRACE_ID_HEADER: "trace-order-upstream"},
        json={"order_id": "A500"},
    )
    data = response.json()

    assert response.status_code == 502
    assert data == {
        "code": "TOOL_UPSTREAM_ERROR",
        "message": "订单查询服务暂时不可用，请稍后重试。",
        "trace_id": "trace-order-upstream",
    }


def test_query_order_api_rejects_missing_order_id(client: TestClient) -> None:
    response = client.post(
        "/tools/query-order",
        headers={TRACE_ID_HEADER: "trace-order-id-missing"},
        json={},
    )
    data = response.json()

    assert response.status_code == 422
    assert data["code"] == "VALIDATION_ERROR"
    assert data["message"] == "请求参数校验失败"
    assert data["trace_id"] == "trace-order-id-missing"
    assert data["details"][0]["loc"] == ["body", "order_id"]
    assert data["details"][0]["type"] == "missing"


def test_query_order_api_rejects_invalid_order_id(client: TestClient) -> None:
    response = client.post(
        "/tools/query-order",
        headers={TRACE_ID_HEADER: "trace-order-id-invalid"},
        json={"order_id": "A 1001"},
    )
    data = response.json()

    assert response.status_code == 422
    assert data["code"] == "VALIDATION_ERROR"
    assert data["trace_id"] == "trace-order-id-invalid"
    assert data["details"][0]["loc"] == ["body", "order_id"]
    assert data["details"][0]["type"] == "string_pattern_mismatch"


def test_query_order_api_rejects_extra_request_fields(client: TestClient) -> None:
    response = client.post(
        "/tools/query-order",
        headers={TRACE_ID_HEADER: "trace-order-extra"},
        json={"order_id": "A1001", "admin": True},
    )
    data = response.json()

    assert response.status_code == 422
    assert data["code"] == "VALIDATION_ERROR"
    assert data["trace_id"] == "trace-order-extra"
    assert data["details"][0]["loc"] == ["body", "admin"]
    assert data["details"][0]["type"] == "extra_forbidden"


def test_query_order_api_does_not_allow_get(client: TestClient) -> None:
    response = client.get(
        "/tools/query-order",
        headers={TRACE_ID_HEADER: "trace-query-order-method"},
    )
    data = response.json()

    assert response.status_code == 405
    assert data == {
        "code": "METHOD_NOT_ALLOWED",
        "message": "请求方法不允许",
        "trace_id": "trace-query-order-method",
    }
