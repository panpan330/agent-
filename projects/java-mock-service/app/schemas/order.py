from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class OrderStatus(StrEnum):
    WAITING_SHIPMENT = "waiting_shipment"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELED = "canceled"


class PaymentStatus(StrEnum):
    UNPAID = "unpaid"
    PAID = "paid"
    REFUNDED = "refunded"


class OrderResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: str = Field(description="Order id returned by the business service.")
    customer_id: str = Field(description="Mock customer id.")
    order_status: OrderStatus = Field(description="Current order status.")
    payment_status: PaymentStatus = Field(description="Current payment status.")
    logistics_message: str = Field(description="Short logistics message.")
    latest_event: str = Field(description="Latest order event.")
    can_create_ticket: bool = Field(
        description="Whether this order can create a customer service ticket.",
    )
