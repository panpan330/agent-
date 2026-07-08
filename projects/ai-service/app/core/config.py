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
    max_output_tokens: int = Field(default=1024, gt=0)
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
