from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings


def test_settings_use_default_values() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_name == "AI Service"
    assert settings.app_version == "0.1.0"
    assert settings.model_name == "mock-chat-model"
    assert settings.llm_provider == "openai-compatible"
    assert settings.llm_model == "qwen3.7-plus"
    assert settings.llm_base_url is None
    assert settings.llm_api_key is None
    assert settings.resolved_llm_api_key is None
    assert settings.has_llm_api_key is False
    assert settings.resolved_llm_base_url is None
    assert settings.request_timeout_seconds == 30.0
    assert settings.llm_max_retries == 2
    assert settings.max_output_tokens == 1024
    assert settings.java_mock_service_base_url == "http://127.0.0.1:8001"
    assert settings.resolved_java_mock_service_base_url == "http://127.0.0.1:8001"
    assert settings.java_mock_service_timeout_seconds == 5.0
    assert settings.tool_confirmation_ttl_seconds == 300
    assert settings.log_level == "INFO"
    assert settings.cors_allowed_origins == "http://localhost:5173,http://127.0.0.1:5173"
    assert settings.cors_allowed_origin_list == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    assert settings.openai_api_key is None
    assert settings.has_openai_api_key is False


def test_settings_read_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_NAME", "Local AI Service")
    monkeypatch.setenv("MODEL_NAME", "demo-model")
    monkeypatch.setenv("LLM_PROVIDER", "aliyun-compatible")
    monkeypatch.setenv("LLM_MODEL", "qwen3.7-plus")
    monkeypatch.setenv(
        "LLM_BASE_URL",
        " https://example.cn-beijing.maas.aliyuncs.com/compatible-mode/v1 ",
    )
    monkeypatch.setenv("LLM_API_KEY", "llm-test-key")
    monkeypatch.setenv("REQUEST_TIMEOUT_SECONDS", "12.5")
    monkeypatch.setenv("LLM_MAX_RETRIES", "3")
    monkeypatch.setenv("MAX_OUTPUT_TOKENS", "256")
    monkeypatch.setenv("JAVA_MOCK_SERVICE_BASE_URL", " http://localhost:9001/ ")
    monkeypatch.setenv("JAVA_MOCK_SERVICE_TIMEOUT_SECONDS", "2.5")
    monkeypatch.setenv("TOOL_CONFIRMATION_TTL_SECONDS", "120")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000")

    settings = Settings(_env_file=None)

    assert settings.app_name == "Local AI Service"
    assert settings.model_name == "demo-model"
    assert settings.llm_provider == "aliyun-compatible"
    assert settings.llm_model == "qwen3.7-plus"
    assert (
        settings.resolved_llm_base_url
        == "https://example.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
    )
    assert settings.resolved_llm_api_key == "llm-test-key"
    assert settings.has_llm_api_key is True
    assert settings.request_timeout_seconds == 12.5
    assert settings.llm_max_retries == 3
    assert settings.max_output_tokens == 256
    assert settings.resolved_java_mock_service_base_url == "http://localhost:9001"
    assert settings.java_mock_service_timeout_seconds == 2.5
    assert settings.tool_confirmation_ttl_seconds == 120
    assert settings.cors_allowed_origin_list == ["http://localhost:3000"]


def test_settings_detect_openai_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-for-local-config")

    settings = Settings(_env_file=None)

    assert settings.openai_api_key == "sk-test-for-local-config"
    assert settings.has_openai_api_key is True
    assert settings.resolved_llm_api_key == "sk-test-for-local-config"
    assert settings.has_llm_api_key is True


def test_settings_prefer_llm_api_key_over_legacy_openai_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_API_KEY", "llm-test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "legacy-openai-test-key")

    settings = Settings(_env_file=None)

    assert settings.resolved_llm_api_key == "llm-test-key"


def test_settings_fall_back_to_legacy_openai_api_key_when_llm_key_is_blank(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_API_KEY", "   ")
    monkeypatch.setenv("OPENAI_API_KEY", "legacy-openai-test-key")

    settings = Settings(_env_file=None)

    assert settings.resolved_llm_api_key == "legacy-openai-test-key"


def test_settings_treat_blank_openai_api_key_as_missing() -> None:
    settings = Settings(openai_api_key="   ", _env_file=None)

    assert settings.has_openai_api_key is False
    assert settings.has_llm_api_key is False


def test_settings_treat_blank_llm_api_key_as_missing() -> None:
    settings = Settings(llm_api_key="   ", _env_file=None)

    assert settings.resolved_llm_api_key is None
    assert settings.has_llm_api_key is False


def test_settings_read_env_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                'APP_NAME="File AI Service"',
                'APP_VERSION="9.9.9"',
                'LOG_LEVEL="DEBUG"',
                'LLM_PROVIDER="aliyun-compatible"',
                'LLM_MODEL="qwen3.7-plus"',
                'LLM_BASE_URL="https://example.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"',
                'LLM_API_KEY=""',
                "LLM_MAX_RETRIES=4",
                "MAX_OUTPUT_TOKENS=512",
                'JAVA_MOCK_SERVICE_BASE_URL="http://localhost:9001/"',
                "JAVA_MOCK_SERVICE_TIMEOUT_SECONDS=3",
                "TOOL_CONFIRMATION_TTL_SECONDS=240",
                'CORS_ALLOWED_ORIGINS="http://localhost:5173, http://localhost:3000"',
                'OPENAI_API_KEY=""',
            ]
        ),
        encoding="utf-8",
    )

    settings = Settings(_env_file=env_file)

    assert settings.app_name == "File AI Service"
    assert settings.app_version == "9.9.9"
    assert settings.log_level == "DEBUG"
    assert settings.llm_provider == "aliyun-compatible"
    assert settings.llm_model == "qwen3.7-plus"
    assert (
        settings.resolved_llm_base_url
        == "https://example.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
    )
    assert settings.has_llm_api_key is False
    assert settings.llm_max_retries == 4
    assert settings.max_output_tokens == 512
    assert settings.resolved_java_mock_service_base_url == "http://localhost:9001"
    assert settings.java_mock_service_timeout_seconds == 3.0
    assert settings.tool_confirmation_ttl_seconds == 240
    assert settings.cors_allowed_origin_list == [
        "http://localhost:5173",
        "http://localhost:3000",
    ]
    assert settings.has_openai_api_key is False


def test_settings_ignore_blank_cors_origins() -> None:
    settings = Settings(
        cors_allowed_origins=" http://localhost:5173, , http://127.0.0.1:5173 ",
        _env_file=None,
    )

    assert settings.cors_allowed_origin_list == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


def test_settings_reject_invalid_timeout() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(request_timeout_seconds=0, _env_file=None)

    error = exc_info.value.errors()[0]
    assert error["loc"] == ("request_timeout_seconds",)
    assert error["type"] == "greater_than"


def test_settings_reject_invalid_max_output_tokens() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(max_output_tokens=0, _env_file=None)

    error = exc_info.value.errors()[0]
    assert error["loc"] == ("max_output_tokens",)
    assert error["type"] == "greater_than"


def test_settings_reject_invalid_java_mock_service_timeout() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(java_mock_service_timeout_seconds=0, _env_file=None)

    error = exc_info.value.errors()[0]
    assert error["loc"] == ("java_mock_service_timeout_seconds",)
    assert error["type"] == "greater_than"


def test_settings_reject_tool_confirmation_ttl_outside_allowed_range() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(tool_confirmation_ttl_seconds=29, _env_file=None)

    error = exc_info.value.errors()[0]
    assert error["loc"] == ("tool_confirmation_ttl_seconds",)
    assert error["type"] == "greater_than_equal"


def test_settings_reject_negative_llm_max_retries() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(llm_max_retries=-1, _env_file=None)

    error = exc_info.value.errors()[0]
    assert error["loc"] == ("llm_max_retries",)
    assert error["type"] == "greater_than_equal"


def test_settings_reject_too_many_llm_max_retries() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(llm_max_retries=6, _env_file=None)

    error = exc_info.value.errors()[0]
    assert error["loc"] == ("llm_max_retries",)
    assert error["type"] == "less_than_equal"


def test_get_settings_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("APP_NAME", "Cached AI Service")

    first = get_settings()
    second = get_settings()

    assert first is second
    assert first.app_name == "Cached AI Service"

    get_settings.cache_clear()
