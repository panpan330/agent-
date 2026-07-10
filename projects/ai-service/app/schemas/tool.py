from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OrderStatus(StrEnum):
    WAITING_SHIPMENT = "waiting_shipment"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELED = "canceled"


class PaymentStatus(StrEnum):
    UNPAID = "unpaid"
    PAID = "paid"
    REFUNDED = "refunded"


class QueryOrderArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
        description="Order id to query, for example A1001.",
    )

    @field_validator("order_id", mode="before")
    @classmethod
    def strip_order_id(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class QueryOrderResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: str = Field(description="Order id returned by the business system.")
    order_status: OrderStatus = Field(description="Current order fulfillment status.")
    payment_status: PaymentStatus = Field(description="Current payment status.")
    logistics_message: str = Field(
        min_length=1,
        max_length=200,
        description="Short logistics or order status message.",
    )
    latest_event: str = Field(
        min_length=1,
        max_length=200,
        description="Latest simulated business event for this order.",
    )
    can_create_ticket: bool = Field(
        description="Whether this order is suitable for creating a support ticket.",
    )
    source: str = Field(
        default="fake_order_tool",
        description="Where this result comes from.",
    )


class QueryOrderResponse(BaseModel):
    result: QueryOrderResult = Field(description="Validated fake query order result.")


def get_query_order_args_json_schema() -> dict[str, Any]:
    return QueryOrderArgs.model_json_schema()


def get_query_order_result_json_schema() -> dict[str, Any]:
    return QueryOrderResult.model_json_schema()
