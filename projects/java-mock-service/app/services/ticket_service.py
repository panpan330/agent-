from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re
from threading import Lock

from app.core.exceptions import MockServiceException
from app.schemas.ticket import CreateTicketRequest, TicketResponse


_TICKET_STORE: dict[str, TicketResponse] = {}
_TICKET_IDEMPOTENCY_STORE: dict[str, "TicketIdempotencyRecord"] = {}
_TICKET_LOCK = Lock()
_IDEMPOTENCY_KEY_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")


@dataclass(frozen=True)
class TicketIdempotencyRecord:
    arguments_fingerprint: str
    ticket: TicketResponse


def _build_arguments_fingerprint(request: CreateTicketRequest) -> str:
    canonical_json = json.dumps(
        request.model_dump(mode="json"),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def _normalize_idempotency_key(idempotency_key: str | None) -> str | None:
    if idempotency_key is None or not idempotency_key.strip():
        return None

    normalized_key = idempotency_key.strip()
    if not _IDEMPOTENCY_KEY_PATTERN.fullmatch(normalized_key):
        raise MockServiceException(
            code="TICKET_IDEMPOTENCY_KEY_INVALID",
            message="幂等键格式不正确。",
            status_code=422,
        )
    return normalized_key


def create_ticket(
    request: CreateTicketRequest,
    *,
    idempotency_key: str | None = None,
) -> TicketResponse:
    normalized_key = _normalize_idempotency_key(idempotency_key)
    arguments_fingerprint = _build_arguments_fingerprint(request)

    with _TICKET_LOCK:
        if normalized_key is not None:
            existing_record = _TICKET_IDEMPOTENCY_STORE.get(normalized_key)
            if existing_record is not None:
                if existing_record.arguments_fingerprint != arguments_fingerprint:
                    raise MockServiceException(
                        code="TICKET_IDEMPOTENCY_KEY_CONFLICT",
                        message="同一个幂等键不能用于不同的创建工单参数。",
                        status_code=409,
                    )
                return deepcopy(existing_record.ticket)

        ticket_id = f"T{len(_TICKET_STORE) + 1001}"
        ticket = TicketResponse(
            ticket_id=ticket_id,
            created_at=datetime.now(timezone.utc),
            **request.model_dump(),
        )
        _TICKET_STORE[ticket_id] = ticket
        if normalized_key is not None:
            _TICKET_IDEMPOTENCY_STORE[normalized_key] = TicketIdempotencyRecord(
                arguments_fingerprint=arguments_fingerprint,
                ticket=deepcopy(ticket),
            )
        return deepcopy(ticket)


def clear_ticket_store() -> None:
    with _TICKET_LOCK:
        _TICKET_STORE.clear()
        _TICKET_IDEMPOTENCY_STORE.clear()
