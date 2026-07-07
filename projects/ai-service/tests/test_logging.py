import logging

import pytest
from fastapi.testclient import TestClient

from app.core.logging import configure_logging, get_log_level


def test_get_log_level_accepts_known_level() -> None:
    assert get_log_level("INFO") == logging.INFO


def test_get_log_level_is_case_insensitive() -> None:
    assert get_log_level("debug") == logging.DEBUG


def test_get_log_level_rejects_unknown_level() -> None:
    with pytest.raises(ValueError) as exc_info:
        get_log_level("LOUD")

    assert "Unsupported log level" in str(exc_info.value)


def test_configure_logging_sets_app_logger_level() -> None:
    configure_logging("ERROR")

    assert logging.getLogger("app").level == logging.ERROR


def test_chat_writes_business_log(client: TestClient, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="app.routers.chat")

    response = client.post("/chat", json={"message": "测试日志"})

    assert response.status_code == 200
    assert "mock_chat_requested message_length=4" in caplog.text
