from datetime import datetime, timezone

import httpx
import pytest

from app.core.exceptions import AppException
from app.core.trace import TRACE_ID_HEADER, reset_trace_id, set_trace_id
from app.schemas.ticket import CreateTicketArgs
from app.services.java_ticket_client import JavaTicketClient


def make_arguments() -> CreateTicketArgs:
    return CreateTicketArgs(
        requester_id="demo_user_001",
        title="订单 A1001 一直未发货",
        description="订单 A1001 已付款一周仍未发货，请帮我处理。",
        category="complaint",
        priority="high",
        related_order_id="A1001",
    )


def test_java_ticket_client_sends_validated_arguments_and_validates_response() -> None:
    received_request: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        received_request["method"] = request.method
        received_request["path"] = request.url.path
        received_request["body"] = request.content.decode("utf-8")
        received_request["idempotency_key"] = request.headers["Idempotency-Key"]
        received_request["trace_id"] = request.headers[TRACE_ID_HEADER]
        return httpx.Response(
            201,
            json={
                **make_arguments().model_dump(mode="json"),
                "ticket_id": "T1001",
                "created_at": datetime(2026, 7, 12, tzinfo=timezone.utc).isoformat(),
            },
        )

    client = JavaTicketClient(
        base_url="http://java-mock.test",
        timeout_seconds=1,
        transport=httpx.MockTransport(handler),
    )
    token = set_trace_id("trace-ticket-client-001")

    try:
        result = client.create_ticket(
            make_arguments(),
            idempotency_key="confirmation-idempotency-001",
        )
    finally:
        reset_trace_id(token)

    assert received_request["method"] == "POST"
    assert received_request["path"] == "/tickets"
    assert "demo_user_001" in str(received_request["body"])
    assert received_request["idempotency_key"] == "confirmation-idempotency-001"
    assert received_request["trace_id"] == "trace-ticket-client-001"
    assert result.ticket_id == "T1001"
    assert result.created_at == datetime(2026, 7, 12, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    ("response", "code"),
    [
        (httpx.Response(500), "TOOL_UPSTREAM_ERROR"),
        (httpx.Response(400), "TICKET_UPSTREAM_REJECTED"),
        (httpx.Response(201, content=b"not-json"), "TOOL_RESULT_VALIDATION_FAILED"),
    ],
)
def test_java_ticket_client_maps_untrusted_upstream_failures(
    response: httpx.Response,
    code: str,
) -> None:
    client = JavaTicketClient(
        base_url="http://java-mock.test",
        timeout_seconds=1,
        transport=httpx.MockTransport(lambda request: response),
    )

    with pytest.raises(AppException) as exc_info:
        client.create_ticket(
            make_arguments(),
            idempotency_key="confirmation-idempotency-002",
        )

    assert exc_info.value.code == code
