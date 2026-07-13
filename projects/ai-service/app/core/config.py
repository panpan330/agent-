from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    app_name: str = Field(default="AI Service")
    app_description: str = Field(
        default="Python AI service for Java + Python + AI learning project."
    )
    app_version: str = Field(default="0.1.0")
    model_name: str = Field(default="mock-chat-model")
    llm_provider: str = Field(default="openai-compatible")
    llm_model: str = Field(default="qwen3.7-plus")
    llm_base_url: str | None = Field(default=None)
    llm_api_key: str | None = Field(default=None, repr=False)
    request_timeout_seconds: float = Field(default=30.0, gt=0)
    llm_max_retries: int = Field(default=2, ge=0, le=5)
    max_output_tokens: int = Field(default=1024, gt=0)
    java_mock_service_base_url: str = Field(default="http://127.0.0.1:8001")
    java_mock_service_timeout_seconds: float = Field(default=5.0, gt=0)
    tool_confirmation_ttl_seconds: int = Field(default=300, ge=30, le=3600)
    log_level: str = Field(default="INFO")
    cors_allowed_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173"
    )
    openai_api_key: str | None = Field(default=None, repr=False)

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_allowed_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]

    @property
    def has_openai_api_key(self) -> bool:
        return bool(self.openai_api_key and self.openai_api_key.strip())

    @property
    def resolved_llm_api_key(self) -> str | None:
        for api_key in (self.llm_api_key, self.openai_api_key):
            if api_key and api_key.strip():
                return api_key.strip()
        return None

    @property
    def has_llm_api_key(self) -> bool:
        return self.resolved_llm_api_key is not None

    @property
    def resolved_llm_base_url(self) -> str | None:
        if not self.llm_base_url or not self.llm_base_url.strip():
            return None
        return self.llm_base_url.strip()

    @property
    def resolved_java_mock_service_base_url(self) -> str:
        return self.java_mock_service_base_url.strip().rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()
