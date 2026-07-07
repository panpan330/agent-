from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        description="User message sent to the AI service.",
    )


class ChatResponse(BaseModel):
    reply: str = Field(
        min_length=1,
        description="Reply returned by the AI service.",
    )
