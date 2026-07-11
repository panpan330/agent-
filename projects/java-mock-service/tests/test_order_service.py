import pytest

from app.core.exceptions import MockServiceException
from app.schemas.order import OrderStatus, PaymentStatus
from app.services.order_service import get_order_by_id


def test_get_order_by_id_returns_order() -> None:
    order = get_order_by_id("A1001")

    assert order.order_id == "A1001"
    assert order.customer_id == "C9001"
    assert order.order_status == OrderStatus.WAITING_SHIPMENT
    assert order.payment_status == PaymentStatus.PAID
    assert order.logistics_message == "商家已接单，等待仓库发货。"
    assert order.latest_event == "仓库正在准备出库。"
    assert order.can_create_ticket is True


def test_get_order_by_id_raises_not_found() -> None:
    with pytest.raises(MockServiceException) as exc_info:
        get_order_by_id("A9999")

    exc = exc_info.value
    assert exc.code == "ORDER_NOT_FOUND"
    assert exc.message == "订单不存在，请确认订单号是否正确。"
    assert exc.status_code == 404
    assert exc.details == {"order_id": "A9999"}


def test_get_order_by_id_simulates_service_error() -> None:
    with pytest.raises(MockServiceException) as exc_info:
        get_order_by_id("A500")

    exc = exc_info.value
    assert exc.code == "ORDER_SERVICE_ERROR"
    assert exc.message == "订单服务内部错误，请稍后重试。"
    assert exc.status_code == 500
