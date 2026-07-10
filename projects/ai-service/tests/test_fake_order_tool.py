import pytest

from app.core.exceptions import AppException
from app.schemas.tool import OrderStatus, QueryOrderArgs
from app.tools.fake_order_tool import query_order, validate_query_order_result


def test_query_order_returns_fake_order_result() -> None:
    result = query_order(QueryOrderArgs(order_id="A1001"))

    assert result.order_id == "A1001"
    assert result.order_status == OrderStatus.WAITING_SHIPMENT
    assert result.logistics_message == "商家已接单，等待仓库发货。"
    assert result.can_create_ticket is True
    assert result.source == "fake_order_tool"


def test_query_order_returns_copy_of_fake_data() -> None:
    first_result = query_order(QueryOrderArgs(order_id="A1002"))
    second_result = query_order(QueryOrderArgs(order_id="A1002"))

    assert first_result == second_result
    assert first_result is not second_result


def test_query_order_raises_app_exception_when_order_is_missing() -> None:
    with pytest.raises(AppException) as exc_info:
        query_order(QueryOrderArgs(order_id="A9999"))

    exc = exc_info.value
    assert exc.code == "ORDER_NOT_FOUND"
    assert exc.message == "订单不存在，请确认订单号是否正确。"
    assert exc.status_code == 404


def test_validate_query_order_result_accepts_raw_tool_result() -> None:
    result = validate_query_order_result(
        {
            "order_id": "A1001",
            "order_status": "waiting_shipment",
            "payment_status": "paid",
            "logistics_message": "商家已接单，等待仓库发货。",
            "latest_event": "仓库正在准备出库。",
            "can_create_ticket": True,
        }
    )

    assert result.order_id == "A1001"
    assert result.order_status == OrderStatus.WAITING_SHIPMENT
    assert result.source == "fake_order_tool"


def test_validate_query_order_result_raises_when_status_is_invalid() -> None:
    with pytest.raises(AppException) as exc_info:
        validate_query_order_result(
            {
                "order_id": "A1001",
                "order_status": "unknown_status",
                "payment_status": "paid",
                "logistics_message": "商家已接单，等待仓库发货。",
                "latest_event": "仓库正在准备出库。",
                "can_create_ticket": True,
            }
        )

    exc = exc_info.value
    assert exc.code == "TOOL_RESULT_VALIDATION_FAILED"
    assert exc.status_code == 502
    assert exc.details is not None
    assert exc.details[0]["loc"] == ("order_status",)
    assert exc.details[0]["type"] == "enum"
    assert "input" not in exc.details[0]


def test_validate_query_order_result_raises_when_required_field_is_missing() -> None:
    with pytest.raises(AppException) as exc_info:
        validate_query_order_result(
            {
                "order_id": "A1001",
                "order_status": "waiting_shipment",
                "payment_status": "paid",
                "latest_event": "仓库正在准备出库。",
                "can_create_ticket": True,
            }
        )

    exc = exc_info.value
    assert exc.code == "TOOL_RESULT_VALIDATION_FAILED"
    assert exc.details is not None
    assert exc.details[0]["loc"] == ("logistics_message",)
    assert exc.details[0]["type"] == "missing"
