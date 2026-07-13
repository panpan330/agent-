from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any
from uuid import uuid4

from app.core.exceptions import AppException
from app.schemas.tool_confirmation import ToolConfirmationStatus
from app.tools.idempotency import build_arguments_fingerprint


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ToolConfirmationRecord:
    confirmation_id: str
    status: ToolConfirmationStatus
    actor_id: str
    tool_name: str
    arguments: dict[str, Any]
    arguments_fingerprint: str
    created_at: datetime
    expires_at: datetime


class ToolConfirmationStore:
    def __init__(self, clock: Callable[[], datetime] = utc_now) -> None:
        self._clock = clock
        self._lock = Lock()
        self._records: dict[str, ToolConfirmationRecord] = {}

    def create(
        self,
        *,
        actor_id: str,
        tool_name: str,
        arguments: Mapping[str, Any],
        ttl_seconds: int,
    ) -> ToolConfirmationRecord:
        created_at = self._clock()
        stored_arguments = deepcopy(dict(arguments))
        record = ToolConfirmationRecord(
            confirmation_id=uuid4().hex,
            status=ToolConfirmationStatus.PENDING,
            actor_id=actor_id,
            tool_name=tool_name,
            arguments=stored_arguments,
            arguments_fingerprint=build_arguments_fingerprint(
                tool_name,
                stored_arguments,
            ),
            created_at=created_at,
            expires_at=created_at + timedelta(seconds=ttl_seconds),
        )
        with self._lock:
            self._records[record.confirmation_id] = record
        return deepcopy(record)

    def confirm(
        self,
        confirmation_id: str,
        *,
        actor_id: str,
    ) -> ToolConfirmationRecord:
        with self._lock:
            record = self._records.get(confirmation_id)
            if record is None:
                raise AppException(
                    code="TOOL_CONFIRMATION_NOT_FOUND",
                    message="确认请求不存在或已失效。",
                    status_code=404,
                )

            if record.actor_id != actor_id:
                raise AppException(
                    code="TOOL_CONFIRMATION_FORBIDDEN",
                    message="当前操作者不能确认其他人的工具请求。",
                    status_code=403,
                )

            if self._clock() >= record.expires_at:
                raise AppException(
                    code="TOOL_CONFIRMATION_EXPIRED",
                    message="确认请求已过期，请重新发起操作。",
                    status_code=409,
                )

            if record.status == ToolConfirmationStatus.PENDING:
                record.status = ToolConfirmationStatus.CONFIRMED

            return deepcopy(record)

    def require_confirmed(
        self,
        confirmation_id: str,
        *,
        actor_id: str,
    ) -> ToolConfirmationRecord:
        with self._lock:
            record = self._records.get(confirmation_id)
            if record is None:
                raise AppException(
                    code="TOOL_CONFIRMATION_NOT_FOUND",
                    message="确认请求不存在或已失效。",
                    status_code=404,
                )

            if record.actor_id != actor_id:
                raise AppException(
                    code="TOOL_CONFIRMATION_FORBIDDEN",
                    message="当前操作者不能执行其他人的工具请求。",
                    status_code=403,
                )

            if self._clock() >= record.expires_at:
                raise AppException(
                    code="TOOL_CONFIRMATION_EXPIRED",
                    message="确认请求已过期，请重新发起操作。",
                    status_code=409,
                )

            if record.status != ToolConfirmationStatus.CONFIRMED:
                raise AppException(
                    code="TOOL_CONFIRMATION_REQUIRED",
                    message="该工具请求尚未获得用户确认。",
                    status_code=409,
                )

            return deepcopy(record)

    def clear(self) -> None:
        with self._lock:
            self._records.clear()

    def count(self) -> int:
        with self._lock:
            return len(self._records)


_TOOL_CONFIRMATION_STORE = ToolConfirmationStore()


def get_tool_confirmation_store() -> ToolConfirmationStore:
    return _TOOL_CONFIRMATION_STORE


def clear_tool_confirmation_store() -> None:
    _TOOL_CONFIRMATION_STORE.clear()
