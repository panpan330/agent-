import pytest

from app.core.exceptions import AppException
from app.schemas.tool import ToolAccessLevel, ToolDefinition
from app.tools.tool_registry import (
    authorize_tool_call,
    get_tool_definition,
    list_tool_definitions,
)


def test_get_tool_definition_returns_query_order_definition() -> None:
    definition = get_tool_definition("query_order")

    assert definition is not None
    assert definition.name == "query_order"
    assert definition.access_level == ToolAccessLevel.READ
    assert definition.requires_confirmation is False
    assert definition.enabled is True
    assert set(definition.argument_schema["properties"]) == {"order_id"}


def test_list_tool_definitions_contains_backend_owned_tools() -> None:
    definitions = list_tool_definitions()
    names = {definition.name for definition in definitions}

    assert names == {"query_order", "create_ticket", "refund_order"}
    assert all(isinstance(definition, ToolDefinition) for definition in definitions)


def test_authorize_tool_call_allows_read_tool_without_confirmation() -> None:
    definition = authorize_tool_call("query_order")

    assert definition.name == "query_order"
    assert definition.access_level == ToolAccessLevel.READ


def test_authorize_tool_call_rejects_unknown_tool() -> None:
    with pytest.raises(AppException) as exc_info:
        authorize_tool_call("delete_database")

    exc = exc_info.value
    assert exc.code == "TOOL_NOT_ALLOWED"
    assert exc.message == "工具不在允许列表中，后端已拒绝执行。"
    assert exc.status_code == 403


def test_authorize_tool_call_requires_confirmation_for_write_tool() -> None:
    with pytest.raises(AppException) as exc_info:
        authorize_tool_call("create_ticket")

    exc = exc_info.value
    assert exc.code == "TOOL_CONFIRMATION_REQUIRED"
    assert exc.message == "该工具需要用户确认后才能执行。"
    assert exc.status_code == 409


def test_authorize_tool_call_allows_write_tool_after_confirmation() -> None:
    definition = authorize_tool_call("create_ticket", user_confirmed=True)

    assert definition.name == "create_ticket"
    assert definition.access_level == ToolAccessLevel.WRITE
    assert definition.requires_confirmation is True


def test_authorize_tool_call_rejects_disabled_sensitive_tool_even_when_confirmed() -> None:
    with pytest.raises(AppException) as exc_info:
        authorize_tool_call("refund_order", user_confirmed=True)

    exc = exc_info.value
    assert exc.code == "TOOL_NOT_ALLOWED"
    assert exc.status_code == 403
