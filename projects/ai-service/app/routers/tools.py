import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Header

from app.core.config import Settings, get_settings
from app.schemas.tool import QueryOrderArgs, QueryOrderResponse
from app.tools.fake_order_tool import query_order as run_query_order_tool
from app.tools.idempotency import IDEMPOTENCY_KEY_HEADER, run_idempotent_tool
from app.tools.tool_registry import authorize_tool_call


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tools", tags=["tools"])


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
