import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Header

from app.core.config import Settings, get_settings
from app.schemas.tool_confirmation import (
    ConfirmToolConfirmationRequest,
    ToolConfirmationRequest,
    ToolConfirmationResponse,
)
from app.services.tool_confirmation_service import ToolConfirmationService
from app.schemas.tool import QueryOrderArgs, QueryOrderResponse
from app.tools.fake_order_tool import query_order as run_query_order_tool
from app.tools.tool_confirmation import get_tool_confirmation_store
from app.tools.idempotency import IDEMPOTENCY_KEY_HEADER, run_idempotent_tool
from app.tools.tool_registry import authorize_tool_call


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tools", tags=["tools"])


def get_tool_confirmation_service(
    settings: Settings = Depends(get_settings),
) -> ToolConfirmationService:
    return ToolConfirmationService(settings, get_tool_confirmation_store())


@router.post("/query-order", response_model=QueryOrderResponse)
def query_order(
    request: QueryOrderArgs,
    settings: Annotated[Settings, Depends(get_settings)],
    idempotency_key: Annotated[
        str | None,
        Header(alias=IDEMPOTENCY_KEY_HEADER),
    ] = None,
) -> QueryOrderResponse:
    authorize_tool_call("query_order")
    logger.info("fake_query_order_requested order_id=%s", request.order_id)
    result = run_idempotent_tool(
        "query_order",
        request,
        idempotency_key,
        lambda: run_query_order_tool(request, settings=settings),
    )
    return QueryOrderResponse(result=result)


@router.post("/confirmations", response_model=ToolConfirmationResponse)
def request_tool_confirmation(
    request: ToolConfirmationRequest,
    confirmation_service: ToolConfirmationService = Depends(
        get_tool_confirmation_service
    ),
) -> ToolConfirmationResponse:
    logger.info(
        "tool_confirmation_requested tool_name=%s actor_id=%s argument_count=%s",
        request.tool_name,
        request.actor_id,
        len(request.arguments),
    )
    return confirmation_service.request_confirmation(request)


@router.post(
    "/confirmations/{confirmation_id}/confirm",
    response_model=ToolConfirmationResponse,
)
def confirm_tool_confirmation(
    confirmation_id: str,
    request: ConfirmToolConfirmationRequest,
    confirmation_service: ToolConfirmationService = Depends(
        get_tool_confirmation_service
    ),
) -> ToolConfirmationResponse:
    logger.info(
        "tool_confirmation_confirmed confirmation_id=%s actor_id=%s",
        confirmation_id,
        request.actor_id,
    )
    return confirmation_service.confirm(confirmation_id, actor_id=request.actor_id)
