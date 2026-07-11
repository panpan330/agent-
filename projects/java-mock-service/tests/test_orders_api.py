from fastapi.testclient import TestClient


def test_get_order_api_returns_order(client: TestClient) -> None:
    response = client.get("/orders/A1001")
    data = response.json()

    assert response.status_code == 200
    assert data == {
        "order_id": "A1001",
        "customer_id": "C9001",
        "order_status": "waiting_shipment",
        "payment_status": "paid",
        "logistics_message": "商家已接单，等待仓库发货。",
        "latest_event": "仓库正在准备出库。",
        "can_create_ticket": True,
    }


def test_get_order_api_returns_not_found(client: TestClient) -> None:
    response = client.get("/orders/A9999")
    data = response.json()

    assert response.status_code == 404
    assert data == {
        "code": "ORDER_NOT_FOUND",
        "message": "订单不存在，请确认订单号是否正确。",
        "details": {"order_id": "A9999"},
    }


def test_get_order_api_returns_service_error(client: TestClient) -> None:
    response = client.get("/orders/A500")
    data = response.json()

    assert response.status_code == 500
    assert data == {
        "code": "ORDER_SERVICE_ERROR",
        "message": "订单服务内部错误，请稍后重试。",
    }


def test_get_order_api_rejects_invalid_order_id(client: TestClient) -> None:
    response = client.get("/orders/A%201001")
    data = response.json()

    assert response.status_code == 422
    assert data["code"] == "VALIDATION_ERROR"
    assert data["message"] == "请求参数校验失败。"
    assert data["details"][0]["loc"] == ["path", "order_id"]
    assert data["details"][0]["type"] == "string_pattern_mismatch"
