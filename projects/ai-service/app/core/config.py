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
    request_timeout_seconds: float = Field(default=30.0, gt=0)
    log_level: str = Field(default="INFO")
    openai_api_key: str | None = Field(default=None, repr=False)

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
