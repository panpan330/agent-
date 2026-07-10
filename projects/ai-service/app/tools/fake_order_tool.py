from collections.abc import Mapping
from typing import Any

from pydantic import ValidationError

from app.core.exceptions import AppException
from app.schemas.tool import (
    OrderStatus,
    PaymentStatus,
    QueryOrderArgs,
    QueryOrderResult,
)


_FAKE_ORDER_STORE: dict[str, dict[str, object]] = {
    "A1001": {
        "order_id": "A1001",
        "order_status": OrderStatus.WAITING_SHIPMENT.value,
        "payment_status": PaymentStatus.PAID.value,
        "logistics_message": "商家已接单，等待仓库发货。",
        "latest_event": "仓库正在准备出库。",
        "can_create_ticket": True,
    },
    "A1002": {
        "order_id": "A1002",
        "order_status": OrderStatus.SHIPPED.value,
        "payment_status": PaymentStatus.PAID.value,
        "logistics_message": "包裹已发出，正在运输途中。",
        "latest_event": "快递已从分拨中心发出。",
        "can_create_ticket": False,
    },
    "A1003": {
        "order_id": "A1003",
        "order_status": OrderStatus.DELIVERED.value,
        "payment_status": PaymentStatus.PAID.value,
        "logistics_message": "订单已签收。",
        "latest_event": "用户已签收包裹。",
        "can_create_ticket": False,
    },
}


def validate_query_order_result(raw_result: Mapping[str, Any]) -> QueryOrderResult:
    try:
        return QueryOrderResult.model_validate(raw_result)
    except ValidationError as exc:
        raise AppException(
            code="TOOL_RESULT_VALIDATION_FAILED",
            message="工具返回结果校验失败，请稍后重试。",
            status_code=502,
            details=exc.errors(include_url=False, include_input=False),
        ) from exc


def query_order(arguments: QueryOrderArgs) -> QueryOrderResult:
    raw_result = _FAKE_ORDER_STORE.get(arguments.order_id)
    if raw_result is None:
        raise AppException(
            code="ORDER_NOT_FOUND",
            message="订单不存在，请确认订单号是否正确。",
            status_code=404,
        )

    return validate_query_order_result(raw_result)
