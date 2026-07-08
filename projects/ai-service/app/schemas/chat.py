from enum import StrEnum

from pydantic import BaseModel, Field


class ChatMessageRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    role: ChatMessageRole = Field(
        description="Message role used by chat completion models.",
    )
    content: str = Field(
        min_length=1,
        max_length=4000,
        description="Message text content.",
    )

    def to_openai_dict(self) -> dict[str, str]:
        return {
            "role": self.role.value,
            "content": self.content,
        }


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
