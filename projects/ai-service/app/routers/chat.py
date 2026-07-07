import logging

from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse


logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    logger.info("mock_chat_requested message_length=%s", len(request.message))
    return ChatResponse(reply=f"你刚才说的是：{request.message}")
