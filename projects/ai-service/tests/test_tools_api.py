from fastapi.testclient import TestClient

from app.core.trace import TRACE_ID_HEADER


def test_query_order_api_returns_fake_order(client: TestClient) -> None:
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
            "source": "fake_order_tool",
        }
    }


def test_query_order_api_returns_not_found_for_missing_order(
    client: TestClient,
) -> None:
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
