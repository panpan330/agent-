from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings


def test_settings_use_default_values() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_name == "AI Service"
    assert settings.app_version == "0.1.0"
    assert settings.model_name == "mock-chat-model"
    assert settings.request_timeout_seconds == 30.0
    assert settings.log_level == "INFO"
    assert settings.openai_api_key is None


def test_settings_read_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_NAME", "Local AI Service")
    monkeypatch.setenv("MODEL_NAME", "demo-model")
    monkeypatch.setenv("REQUEST_TIMEOUT_SECONDS", "12.5")

    settings = Settings(_env_file=None)

    assert settings.app_name == "Local AI Service"
    assert settings.model_name == "demo-model"
    assert settings.request_timeout_seconds == 12.5


def test_settings_read_env_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                'APP_NAME="File AI Service"',
                'APP_VERSION="9.9.9"',
                'LOG_LEVEL="DEBUG"',
            ]
        ),
        encoding="utf-8",
    )

    settings = Settings(_env_file=env_file)

    assert settings.app_name == "File AI Service"
    assert settings.app_version == "9.9.9"
    assert settings.log_level == "DEBUG"


def test_settings_reject_invalid_timeout() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(request_timeout_seconds=0, _env_file=None)

    error = exc_info.value.errors()[0]
    assert error["loc"] == ("request_timeout_seconds",)
    assert error["type"] == "greater_than"


def test_get_settings_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("APP_NAME", "Cached AI Service")

    first = get_settings()
    second = get_settings()

    assert first is second
    assert first.app_name == "Cached AI Service"

    get_settings.cache_clear()
