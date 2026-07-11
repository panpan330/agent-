from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = Field(description="Service health status.")
    service: str = Field(description="Service name.")
