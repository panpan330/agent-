import logging

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm_service import LLMChatService, create_llm_chat_service


logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


def get_llm_chat_service(
    settings: Settings = Depends(get_settings),
) -> LLMChatService:
    return create_llm_chat_service(settings)


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    llm_chat_service: LLMChatService = Depends(get_llm_chat_service),
) -> ChatResponse:
    logger.info("chat_requested message_length=%s", len(request.message))
    reply = llm_chat_service.generate_reply(request.message)
    return ChatResponse(reply=reply)
