from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class TicketCategory(StrEnum):
    REFUND = "refund"
    ORDER_QUERY = "order_query"
    LOGISTICS = "logistics"
    COMPLAINT = "complaint"


class TicketPriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class CreateTicketRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requester_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=1000)
    category: TicketCategory
    priority: TicketPriority = TicketPriority.NORMAL
    related_order_id: str | None = Field(default=None, max_length=64)


class TicketResponse(CreateTicketRequest):
    ticket_id: str = Field(pattern=r"^T\d{4}$")
    created_at: datetime
