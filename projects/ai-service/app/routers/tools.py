import logging

from fastapi import APIRouter

from app.schemas.tool import QueryOrderArgs, QueryOrderResponse
from app.tools.fake_order_tool import query_order as run_query_order_tool


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tools", tags=["tools"])


@router.post("/query-order", response_model=QueryOrderResponse)
def query_order(request: QueryOrderArgs) -> QueryOrderResponse:
    logger.info("fake_query_order_requested order_id=%s", request.order_id)
    result = run_query_order_tool(request)
    return QueryOrderResponse(result=result)
