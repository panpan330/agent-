from app.core.exceptions import MockServiceException
from app.schemas.order import OrderResponse, OrderStatus, PaymentStatus


_ORDER_STORE: dict[str, dict[str, object]] = {
    "A1001": {
        "order_id": "A1001",
        "customer_id": "C9001",
        "order_status": OrderStatus.WAITING_SHIPMENT.value,
        "payment_status": PaymentStatus.PAID.value,
        "logistics_message": "商家已接单，等待仓库发货。",
        "latest_event": "仓库正在准备出库。",
        "can_create_ticket": True,
    },
    "A1002": {
        "order_id": "A1002",
        "customer_id": "C9002",
        "order_status": OrderStatus.SHIPPED.value,
        "payment_status": PaymentStatus.PAID.value,
        "logistics_message": "包裹已发出，正在运输途中。",
        "latest_event": "快递已从分拨中心发出。",
        "can_create_ticket": False,
    },
    "A1003": {
        "order_id": "A1003",
        "customer_id": "C9003",
        "order_status": OrderStatus.DELIVERED.value,
        "payment_status": PaymentStatus.PAID.value,
        "logistics_message": "订单已签收。",
        "latest_event": "用户已签收包裹。",
        "can_create_ticket": False,
    },
}


def get_order_by_id(order_id: str) -> OrderResponse:
    if order_id == "A500":
        raise MockServiceException(
            code="ORDER_SERVICE_ERROR",
            message="订单服务内部错误，请稍后重试。",
            status_code=500,
        )

    raw_order = _ORDER_STORE.get(order_id)
    if raw_order is None:
        raise MockServiceException(
            code="ORDER_NOT_FOUND",
            message="订单不存在，请确认订单号是否正确。",
            status_code=404,
            details={"order_id": order_id},
        )

    return OrderResponse.model_validate(raw_order)
