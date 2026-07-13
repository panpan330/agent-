from typing import Annotated

from fastapi import APIRouter, Header

from app.schemas.ticket import CreateTicketRequest, TicketResponse
from app.services.ticket_service import create_ticket


router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=TicketResponse, status_code=201)
def create_ticket_api(
    request: CreateTicketRequest,
    idempotency_key: Annotated[
        str | None,
        Header(alias="Idempotency-Key"),
    ] = None,
) -> TicketResponse:
    return create_ticket(request, idempotency_key=idempotency_key)
