from typing import Annotated

from fastapi import APIRouter, Path

from app.schemas.order import OrderResponse
from app.services.order_service import get_order_by_id


router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: Annotated[
        str,
        Path(
            min_length=1,
            max_length=64,
            pattern=r"^[A-Za-z0-9_-]+$",
            description="Order id, for example A1001.",
        ),
    ],
) -> OrderResponse:
    return get_order_by_id(order_id)
