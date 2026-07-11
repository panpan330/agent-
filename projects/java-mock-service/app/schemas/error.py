from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(description="Stable error code for callers.")
    message: str = Field(description="Safe error message for callers.")
    details: Any | None = Field(default=None, description="Optional error details.")
