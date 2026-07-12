import json
import logging
from collections.abc import Iterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core.config import Settings, get_settings
from app.core.exceptions import AppException
from app.core.trace import get_trace_id
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.structured import StructuredOutputRequest, StructuredOutputResponse
from app.schemas.tool_decision import ToolDecisionResponse
from app.services.llm_service import LLMChatService, create_llm_chat_service
from app.services.structured_output_service import (
    StructuredOutputService,
    create_structured_output_service,
)
from app.services.tool_decision_service import (
    ToolDecisionService,
    create_tool_decision_service,
)
from app.services.tool_calling_chat_service import (
    ToolCallingChatService,
    create_tool_calling_chat_service,
)


logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])
SSE_MEDIA_TYPE = "text/event-stream"


def get_llm_chat_service(
    settings: Settings = Depends(get_settings),
) -> LLMChatService:
    return create_llm_chat_service(settings)


def get_structured_output_service(
    settings: Settings = Depends(get_settings),
) -> StructuredOutputService:
    return create_structured_output_service(settings)


def get_tool_decision_service(
    settings: Settings = Depends(get_settings),
) -> ToolDecisionService:
    return create_tool_decision_service(settings)


def get_tool_calling_chat_service(
    settings: Settings = Depends(get_settings),
) -> ToolCallingChatService:
    return create_tool_calling_chat_service(settings)


def format_sse_event(event: str, data: dict[str, object]) -> str:
    json_data = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"event: {event}\ndata: {json_data}\n\n"


def build_stream_events(
    chunks: Iterator[str],
    *,
    trace_id: str,
) -> Iterator[str]:
    try:
        for chunk in chunks:
            yield format_sse_event("message", {"content": chunk})
    except AppException as exc:
        logger.warning(
            "stream_chat_app_exception code=%s",
            exc.code,
        )
        yield format_sse_event(
            "error",
            {
                "code": exc.code,
                "message": exc.message,
                "trace_id": trace_id,
            },
        )
        return
    except Exception:
        logger.exception("stream_chat_unhandled_exception")
        yield format_sse_event(
            "error",
            {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "服务器内部错误",
                "trace_id": trace_id,
            },
        )
        return

    yield format_sse_event("done", {"trace_id": trace_id})


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    llm_chat_service: LLMChatService = Depends(get_llm_chat_service),
) -> ChatResponse:
    logger.info(
        "chat_requested message_length=%s history_size=%s",
        len(request.message),
        len(request.history),
    )
    reply = llm_chat_service.generate_reply(
        request.message,
        history=request.history,
    )
    return ChatResponse(reply=reply)


@router.post("/stream-chat")
def stream_chat(
    request: ChatRequest,
    llm_chat_service: LLMChatService = Depends(get_llm_chat_service),
) -> StreamingResponse:
    logger.info(
        "stream_chat_requested message_length=%s history_size=%s",
        len(request.message),
        len(request.history),
    )
    chunks = llm_chat_service.stream_reply(
        request.message,
        history=request.history,
    )
    return StreamingResponse(
        build_stream_events(chunks, trace_id=get_trace_id()),
        media_type=SSE_MEDIA_TYPE,
    )


@router.post("/extract-ticket", response_model=StructuredOutputResponse)
def extract_ticket(
    request: StructuredOutputRequest,
    structured_output_service: StructuredOutputService = Depends(
        get_structured_output_service
    ),
) -> StructuredOutputResponse:
    logger.info(
        "extract_ticket_requested message_length=%s",
        len(request.message),
    )
    extraction = structured_output_service.extract_ticket(request.message)
    return StructuredOutputResponse(extraction=extraction)


@router.post("/tool-decision", response_model=ToolDecisionResponse)
def tool_decision(
    request: ChatRequest,
    tool_decision_service: ToolDecisionService = Depends(get_tool_decision_service),
) -> ToolDecisionResponse:
    logger.info(
        "tool_decision_requested message_length=%s history_size=%s",
        len(request.message),
        len(request.history),
    )
    return tool_decision_service.decide(
        request.message,
        history=request.history,
    )


@router.post("/tool-chat", response_model=ChatResponse)
def tool_chat(
    request: ChatRequest,
    tool_calling_chat_service: ToolCallingChatService = Depends(
        get_tool_calling_chat_service
    ),
) -> ChatResponse:
    logger.info(
        "tool_chat_requested message_length=%s history_size=%s",
        len(request.message),
        len(request.history),
    )
    reply = tool_calling_chat_service.generate_reply(
        request.message,
        history=request.history,
    )
    return ChatResponse(reply=reply)
