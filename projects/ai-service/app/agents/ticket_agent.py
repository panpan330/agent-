import hashlib
import json
import logging
import re
from operator import add
from time import perf_counter
from typing import Annotated, Any, Literal, Protocol
from typing_extensions import TypedDict

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.trace import get_trace_id
from app.rag.documents import RetrievedChunk
from app.rag.generator import RagAnswer, build_grounded_rag_answer, build_no_context_rag_answer
from app.schemas.ticket import (
    CreateTicketArgs,
    CreatedTicket,
    TicketCategory,
    TicketPriority,
)
from app.services.java_ticket_client import JavaTicketClient
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


logger = logging.getLogger(__name__)


TicketIntent = Literal[
    "policy_question",
    "order_query",
    "ticket_request",
    "smalltalk",
    "unsupported",
    "unclear",
]
TicketAgentRoute = TicketIntent
TicketNeedRoute = Literal["create_ticket", "finish"]
TicketFieldCompletionRoute = Literal["ask_missing_fields", "request_confirmation"]
TicketConfirmationRoute = Literal["execute_create_ticket", "finish"]
TicketNeedSource = Literal[
    "explicit_user_request",
    "rag_no_context",
    "rag_answered",
    "not_applicable",
]
TicketIssueType = Literal["refund", "logistics", "complaint", "policy_gap", "unknown"]
TicketUrgencyLevel = Literal["low", "normal", "high"]
TicketFieldExtractionSource = Literal["rule_based"]
TicketConfirmationStatus = Literal["pending"]
TicketCreationStatus = Literal["created", "blocked", "failed"]
TicketAgentStreamPart = dict[str, Any]

TICKET_AGENT_FIXED_EDGES: tuple[tuple[str, str], ...] = (
    (START, "normalize_user_input"),
    ("normalize_user_input", "classify_intent"),
    ("retrieve_policy", "decide_ticket_need"),
    ("query_order", END),
    ("ask_missing_ticket_fields", END),
    ("create_ticket", END),
    ("build_direct_answer", END),
    ("build_unsupported_answer", END),
    ("ask_clarifying_question", END),
)

TICKET_AGENT_INTENT_ROUTES: dict[TicketAgentRoute, str] = {
    "policy_question": "retrieve_policy",
    "order_query": "query_order",
    "ticket_request": "decide_ticket_need",
    "smalltalk": "build_direct_answer",
    "unsupported": "build_unsupported_answer",
    "unclear": "ask_clarifying_question",
}

TICKET_AGENT_TICKET_NEED_ROUTES: dict[TicketNeedRoute, str] = {
    "create_ticket": "extract_ticket_fields",
    "finish": END,
}

TICKET_AGENT_FIELD_COMPLETION_ROUTES: dict[TicketFieldCompletionRoute, str] = {
    "ask_missing_fields": "ask_missing_ticket_fields",
    "request_confirmation": "request_ticket_confirmation",
}

TICKET_AGENT_CONFIRMATION_ROUTES: dict[TicketConfirmationRoute, str] = {
    "execute_create_ticket": "create_ticket",
    "finish": END,
}


class TicketAgentIntentClassification(TypedDict):
    intent: TicketIntent
    reason: str


class TicketNeedDecision(TypedDict):
    needs_ticket: bool
    reason: str
    source: TicketNeedSource


class TicketFields(TypedDict):
    issue_type: TicketIssueType
    order_id: str | None
    description: str
    user_request: str
    urgency: TicketUrgencyLevel
    need_human_review: bool


class PendingTicketConfirmation(TypedDict):
    confirmation_id: str
    status: TicketConfirmationStatus
    title: str
    summary: str
    ticket_fields: TicketFields
    message: str


class PolicyRagService(Protocol):
    def answer_policy_question(self, query: str) -> RagAnswer:
        """Return a grounded policy answer or a no-context fallback."""


class TicketCreator(Protocol):
    def create_ticket(
        self,
        arguments: CreateTicketArgs,
        *,
        idempotency_key: str,
    ) -> CreatedTicket:
        """Create a ticket through the backend business service."""


class TicketAgentState(TypedDict, total=False):
    """State shared by the ticket agent learning graph."""

    user_message: str
    agent_trace_id: str
    normalized_message: str
    intent: TicketIntent
    intent_reason: str
    rag_query: str
    rag_answer_status: str
    rag_citations: list[dict[str, Any]]
    rag_no_context_reason: str | None
    rag_suggestions: list[str]
    needs_ticket: bool
    ticket_need_reason: str
    ticket_need_source: TicketNeedSource
    ticket_fields: TicketFields
    missing_ticket_fields: list[str]
    ticket_fields_complete: bool
    ticket_field_extraction_source: TicketFieldExtractionSource
    missing_ticket_field_question: str
    missing_ticket_field_question_fields: list[str]
    ticket_confirmation_required: bool
    ticket_confirmation_approved: bool
    ticket_confirmation_message: str
    pending_ticket_confirmation: PendingTicketConfirmation
    ticket_actor_id: str
    ticket_creation_args: dict[str, Any]
    ticket_creation_status: TicketCreationStatus
    ticket_creation_error_code: str | None
    ticket_creation_error_message: str | None
    created_ticket: dict[str, Any]
    agent_error_code: str | None
    agent_error_message: str | None
    agent_error_node: str | None
    fallback_used: bool
    final_answer: str
    node_history: Annotated[list[str], add]


POLICY_KEYWORDS = (
    "规则",
    "政策",
    "faq",
    "退款规则",
    "退货规则",
    "售后政策",
    "账号安全",
    "怎么退款",
    "怎么退货",
    "多久可以退款",
    "多久可以退货",
)
ORDER_KEYWORDS = (
    "订单",
    "物流",
    "快递",
    "发货",
    "到哪",
    "到哪了",
    "支付",
    "付款",
    "签收",
)
TICKET_KEYWORDS = (
    "投诉",
    "工单",
    "售后处理",
    "人工处理",
    "人工客服",
    "创建工单",
    "商品坏了",
    "商品破损",
    "不发货",
    "一直不动",
    "帮我处理",
)
SMALLTALK_KEYWORDS = (
    "你好",
    "您好",
    "hello",
    "hi",
    "你是谁",
    "你能做什么",
)
UNSUPPORTED_KEYWORDS = (
    "直接退款",
    "退款到账",
    "立刻退款",
    "取消订单",
    "黑客",
    "攻击脚本",
    "写小说",
    "股票",
    "天气",
)
UNCLEAR_MESSAGES = (
    "有问题",
    "帮我看看",
    "这个怎么办",
    "处理一下",
)
ORDER_ID_PATTERN = re.compile(
    r"(?:订单号?|order(?:_id)?)\s*[:：#-]?\s*([A-Za-z0-9_-]{3,64})",
    re.IGNORECASE,
)
FALLBACK_ORDER_ID_PATTERN = re.compile(r"\b([A-Za-z]\d{3,}|\d{4,})\b")
REFUND_ISSUE_KEYWORDS = ("退款", "退货", "售后")
LOGISTICS_ISSUE_KEYWORDS = ("物流", "快递", "发货", "未发货", "不发货", "一直不动", "到哪")
COMPLAINT_ISSUE_KEYWORDS = (
    "投诉",
    "人工处理",
    "人工客服",
    "帮我处理",
    "商品坏了",
    "商品破损",
    "破损",
)
HIGH_URGENCY_KEYWORDS = (
    "投诉",
    "破损",
    "坏了",
    "一直不动",
    "一周",
    "加急",
    "立刻",
    "马上",
)
ORDER_REQUIRED_ISSUE_TYPES: tuple[TicketIssueType, ...] = (
    "refund",
    "logistics",
    "complaint",
)
MISSING_TICKET_FIELD_QUESTIONS: dict[str, str] = {
    "order_id": "请补充相关订单号（例如 1001 或 A1001），这样我才能继续为你整理工单。",
    "issue_type": "请说明这是退款、物流、投诉，还是其他需要人工处理的问题。",
    "description": "请补充问题的具体描述，例如发生了什么、影响是什么。",
    "user_request": "请说明你希望客服帮你处理什么，例如投诉处理、退款处理或人工解释。",
}
TICKET_ISSUE_TYPE_LABELS: dict[TicketIssueType, str] = {
    "refund": "退款/退货",
    "logistics": "物流/发货",
    "complaint": "投诉/异常处理",
    "policy_gap": "知识库缺口",
    "unknown": "未确定",
}
TICKET_URGENCY_LABELS: dict[TicketUrgencyLevel, str] = {
    "low": "低",
    "normal": "普通",
    "high": "高",
}
TICKET_ISSUE_TYPE_TO_CATEGORY: dict[TicketIssueType, TicketCategory] = {
    "refund": TicketCategory.REFUND,
    "logistics": TicketCategory.LOGISTICS,
    "complaint": TicketCategory.COMPLAINT,
    "policy_gap": TicketCategory.POLICY_GAP,
}
TICKET_URGENCY_TO_PRIORITY: dict[TicketUrgencyLevel, TicketPriority] = {
    "low": TicketPriority.LOW,
    "normal": TicketPriority.NORMAL,
    "high": TicketPriority.HIGH,
}
DEFAULT_TICKET_ACTOR_ID = "demo_user_001"
TICKET_CONFIRMATION_NOT_FOUND_MESSAGE = "当前会话没有待确认工单，请先发起工单流程。"
TICKET_CONFIRMATION_INTERRUPT_NOT_FOUND_MESSAGE = "当前执行结果里没有待处理的工单确认中断。"
TICKET_CONFIRMATION_REJECTED_MESSAGE = "已取消创建工单；如需创建，请重新发起工单流程。"
TICKET_CONFIRMATION_INTERRUPT_KIND = "ticket_confirmation"
TICKET_AGENT_FALLBACK_ERROR_CODE = "TICKET_AGENT_UNEXPECTED_ERROR"
TICKET_AGENT_FALLBACK_MESSAGE = "智能工单流程暂时遇到异常，请稍后重试或联系人工客服。"
TICKET_CREATION_UNEXPECTED_ERROR_CODE = "TICKET_CREATION_UNEXPECTED_ERROR"
TICKET_CREATION_UNEXPECTED_ERROR_MESSAGE = "创建工单时遇到异常，请稍后重试或联系人工客服。"
TICKET_THREAD_ID_INVALID_ERROR_CODE = "TICKET_THREAD_ID_INVALID"
TICKET_AGENT_LOG_VALUE_EMPTY = "-"


class FakePolicyRagService:
    def answer_policy_question(self, query: str) -> RagAnswer:
        normalized_query = query.strip()
        lowered_query = normalized_query.casefold()

        if not normalized_query:
            return build_no_context_rag_answer()

        if "退款" in lowered_query:
            return build_grounded_rag_answer(
                "根据知识库，退款申请通常需要先核对订单状态和售后条件，"
                "用户可以按退款退货规则提交申请。",
                [
                    _make_fake_retrieved_chunk(
                        chunk_id="refund_return_policy_chunk_0001",
                        content="退款申请通常需要先核对订单状态、售后条件和商品状态。",
                        source="refund-return-policy.md",
                        title="退款退货规则",
                        section="退款申请",
                    )
                ],
            )

        if "退货" in lowered_query:
            return build_grounded_rag_answer(
                "根据知识库，退货通常需要商品符合售后规则，并按页面或客服指引提交退货申请。",
                [
                    _make_fake_retrieved_chunk(
                        chunk_id="refund_return_policy_chunk_0002",
                        content="退货通常需要商品符合售后规则，并按指引提交退货申请。",
                        source="refund-return-policy.md",
                        title="退款退货规则",
                        section="退货申请",
                    )
                ],
            )

        if "账号安全" in lowered_query:
            return build_grounded_rag_answer(
                "根据知识库，账号安全相关操作通常需要进行身份验证，"
                "客服不能在聊天中索要完整敏感身份信息。",
                [
                    _make_fake_retrieved_chunk(
                        chunk_id="account_security_faq_chunk_0001",
                        content="账号安全相关操作通常需要身份验证，客服不能索要完整敏感身份信息。",
                        source="account-security-faq.md",
                        title="账号安全常见问题",
                        section="身份验证",
                    )
                ],
            )

        return build_no_context_rag_answer()


def normalize_user_input_node(state: TicketAgentState) -> TicketAgentState:
    user_message = state.get("user_message", "")

    return {
        "normalized_message": user_message.strip(),
        "node_history": ["normalize_user_input"],
    }


def classify_ticket_intent(message: str) -> TicketAgentIntentClassification:
    normalized_message = message.strip()
    lowered_message = normalized_message.casefold()

    if not normalized_message:
        return {
            "intent": "unclear",
            "reason": "用户输入为空，需要先追问用户要处理的问题。",
        }

    if _contains_any(lowered_message, UNSUPPORTED_KEYWORDS):
        return {
            "intent": "unsupported",
            "reason": "用户请求超出当前客服 Agent v1 的安全业务范围。",
        }

    if _contains_any(lowered_message, SMALLTALK_KEYWORDS):
        return {
            "intent": "smalltalk",
            "reason": "用户在进行问候或询问助手能力，不需要查询业务系统。",
        }

    if _contains_any(lowered_message, TICKET_KEYWORDS):
        return {
            "intent": "ticket_request",
            "reason": "用户表达了投诉、售后处理或创建工单诉求。",
        }

    if _contains_any(lowered_message, ORDER_KEYWORDS):
        return {
            "intent": "order_query",
            "reason": "用户在询问订单、物流、支付或发货状态。",
        }

    if _contains_any(lowered_message, POLICY_KEYWORDS):
        return {
            "intent": "policy_question",
            "reason": "用户在询问规则、政策或 FAQ 类知识库问题。",
        }

    if normalized_message in UNCLEAR_MESSAGES:
        return {
            "intent": "unclear",
            "reason": "用户描述过于笼统，需要追问具体问题和必要信息。",
        }

    return {
        "intent": "unclear",
        "reason": "当前规则分类器无法稳定判断意图，需要追问用户补充信息。",
    }


def classify_intent_node(state: TicketAgentState) -> TicketAgentState:
    classification = classify_ticket_intent(state.get("normalized_message", ""))

    return {
        "intent": classification["intent"],
        "intent_reason": classification["reason"],
        "node_history": ["classify_intent"],
    }


def route_by_intent(state: TicketAgentState) -> TicketAgentRoute:
    intent = state.get("intent")
    if intent in TICKET_AGENT_INTENT_ROUTES:
        return intent
    return "unclear"


def decide_ticket_need(state: TicketAgentState) -> TicketNeedDecision:
    intent = state.get("intent")
    rag_answer_status = state.get("rag_answer_status")

    if intent == "ticket_request":
        return {
            "needs_ticket": True,
            "reason": "用户明确表达了投诉、售后处理或创建工单诉求，需要进入工单流程。",
            "source": "explicit_user_request",
        }

    if intent == "policy_question" and rag_answer_status == "no_context":
        return {
            "needs_ticket": True,
            "reason": "知识库没有找到足够资料，需要进入工单流程记录问题或交给人工处理。",
            "source": "rag_no_context",
        }

    if intent == "policy_question" and rag_answer_status == "answered":
        return {
            "needs_ticket": False,
            "reason": "知识库已给出可引用回答，当前不需要创建工单。",
            "source": "rag_answered",
        }

    return {
        "needs_ticket": False,
        "reason": "当前路线暂不需要创建工单。",
        "source": "not_applicable",
    }


def decide_ticket_need_node(state: TicketAgentState) -> TicketAgentState:
    decision = decide_ticket_need(state)

    return {
        "needs_ticket": decision["needs_ticket"],
        "ticket_need_reason": decision["reason"],
        "ticket_need_source": decision["source"],
        "node_history": ["decide_ticket_need"],
    }


def route_by_ticket_need(state: TicketAgentState) -> TicketNeedRoute:
    if state.get("needs_ticket") is True:
        return "create_ticket"
    return "finish"


def extract_ticket_fields(state: TicketAgentState) -> TicketFields:
    normalized_message = state.get("normalized_message", "").strip()
    lowered_message = normalized_message.casefold()
    ticket_need_source = state.get("ticket_need_source")
    rag_answer_status = state.get("rag_answer_status")
    issue_type = _infer_ticket_issue_type(
        lowered_message,
        ticket_need_source=ticket_need_source,
        rag_answer_status=rag_answer_status,
    )
    urgency = _infer_ticket_urgency(lowered_message, issue_type=issue_type)

    return {
        "issue_type": issue_type,
        "order_id": _extract_order_id(normalized_message),
        "description": _build_ticket_description(
            normalized_message,
            ticket_need_source=ticket_need_source,
        ),
        "user_request": _infer_ticket_user_request(
            lowered_message,
            issue_type=issue_type,
            ticket_need_source=ticket_need_source,
        ),
        "urgency": urgency,
        "need_human_review": (
            ticket_need_source in {"explicit_user_request", "rag_no_context"}
            or urgency == "high"
        ),
    }


def find_missing_ticket_fields(fields: TicketFields) -> list[str]:
    missing_fields: list[str] = []

    if fields["issue_type"] == "unknown":
        missing_fields.append("issue_type")
    if not fields["description"].strip():
        missing_fields.append("description")
    if not fields["user_request"].strip():
        missing_fields.append("user_request")
    if (
        fields["issue_type"] in ORDER_REQUIRED_ISSUE_TYPES
        and fields["order_id"] is None
    ):
        missing_fields.append("order_id")

    return missing_fields


def route_by_ticket_fields_complete(state: TicketAgentState) -> TicketFieldCompletionRoute:
    if state.get("ticket_fields_complete") is True:
        return "request_confirmation"
    return "ask_missing_fields"


def route_by_ticket_confirmation(state: TicketAgentState) -> TicketConfirmationRoute:
    if state.get("ticket_confirmation_approved") is True:
        return "execute_create_ticket"
    return "finish"


def build_missing_ticket_fields_question(missing_fields: list[str]) -> str:
    if not missing_fields:
        return "工单字段已经完整，后续课程会学习如何请求用户确认。"

    field_questions = [
        MISSING_TICKET_FIELD_QUESTIONS.get(field, f"请补充 {field}。")
        for field in missing_fields
    ]

    if len(field_questions) == 1:
        return field_questions[0]

    return "为了继续创建工单，请补充以下信息：" + "；".join(field_questions)


def build_ticket_confirmation_id(fields: TicketFields) -> str:
    confirmation_payload = json.dumps(fields, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(confirmation_payload.encode("utf-8")).hexdigest()[:16]


def build_ticket_confirmation_message(fields: TicketFields) -> str:
    issue_type_label = TICKET_ISSUE_TYPE_LABELS[fields["issue_type"]]
    urgency_label = TICKET_URGENCY_LABELS[fields["urgency"]]
    order_id = fields["order_id"] or "无"
    human_review = "是" if fields["need_human_review"] else "否"

    return (
        "我已整理好一份待确认工单，请确认是否按以下信息创建：\n"
        f"问题类型：{issue_type_label}\n"
        f"订单号：{order_id}\n"
        f"问题描述：{fields['description']}\n"
        f"用户诉求：{fields['user_request']}\n"
        f"紧急程度：{urgency_label}\n"
        f"是否需要人工复核：{human_review}\n"
        "如果信息正确，请回复“确认创建”；如果不正确，请说明需要修改的内容。"
    )


def build_pending_ticket_confirmation(fields: TicketFields) -> PendingTicketConfirmation:
    issue_type_label = TICKET_ISSUE_TYPE_LABELS[fields["issue_type"]]
    order_id = fields["order_id"] or "无订单号"
    summary = f"{issue_type_label}，{order_id}，{fields['user_request']}"

    return {
        "confirmation_id": build_ticket_confirmation_id(fields),
        "status": "pending",
        "title": f"待确认工单：{issue_type_label}",
        "summary": summary,
        "ticket_fields": fields,
        "message": build_ticket_confirmation_message(fields),
    }


def build_ticket_confirmation_interrupt_payload(
    pending_confirmation: PendingTicketConfirmation,
) -> dict[str, Any]:
    return {
        "kind": TICKET_CONFIRMATION_INTERRUPT_KIND,
        "confirmation_id": pending_confirmation["confirmation_id"],
        "message": pending_confirmation["message"],
        "pending_ticket_confirmation": pending_confirmation,
    }


def is_ticket_confirmation_resume_approved(resume_value: Any) -> bool:
    if isinstance(resume_value, bool):
        return resume_value
    if isinstance(resume_value, dict):
        return resume_value.get("approved") is True
    return False


def get_ticket_confirmation_resume_actor_id(resume_value: Any) -> str | None:
    if not isinstance(resume_value, dict):
        return None

    actor_id = resume_value.get("actor_id")
    if not isinstance(actor_id, str):
        return None

    normalized_actor_id = actor_id.strip()
    return normalized_actor_id or None


def build_create_ticket_args_from_fields(
    fields: TicketFields,
    *,
    actor_id: str,
) -> CreateTicketArgs:
    category = TICKET_ISSUE_TYPE_TO_CATEGORY.get(fields["issue_type"])
    if category is None:
        raise AppException(
            code="TICKET_FIELDS_INCOMPLETE",
            message="工单字段还不完整，暂时不能创建工单。",
            status_code=422,
        )

    return CreateTicketArgs(
        requester_id=actor_id,
        title=_build_ticket_creation_title(fields),
        description=fields["description"],
        category=category,
        priority=TICKET_URGENCY_TO_PRIORITY[fields["urgency"]],
        related_order_id=fields["order_id"],
    )


def build_ticket_agent_fallback_state(
    *,
    node_name: str,
    code: str = TICKET_AGENT_FALLBACK_ERROR_CODE,
    message: str = TICKET_AGENT_FALLBACK_MESSAGE,
) -> TicketAgentState:
    return {
        "agent_error_code": code,
        "agent_error_message": message,
        "agent_error_node": node_name,
        "fallback_used": True,
        "final_answer": message,
        "node_history": [node_name],
    }


def build_ticket_creation_failure_state(
    *,
    code: str,
    message: str,
) -> TicketAgentState:
    update = build_ticket_agent_fallback_state(
        node_name="create_ticket",
        code=code,
        message=message,
    )
    update.update(
        {
            "ticket_creation_status": "failed",
            "ticket_creation_error_code": code,
            "ticket_creation_error_message": message,
        }
    )
    return update


def build_ticket_agent_observation_metadata(
    state: dict[str, Any],
    *,
    operation: str,
    thread_id: str | None = None,
    elapsed_ms: float | None = None,
) -> dict[str, Any]:
    node_history = list(state.get("node_history", []))
    metadata: dict[str, Any] = {
        "operation": operation,
        "trace_id": state.get("agent_trace_id") or get_trace_id(),
        "thread_id": _safe_log_value(thread_id),
        "intent": _safe_log_value(state.get("intent")),
        "node_count": len(node_history),
        "last_node": _safe_log_value(node_history[-1] if node_history else None),
        "interrupted": bool(state.get("__interrupt__")),
        "fallback_used": state.get("fallback_used") is True,
        "agent_error_code": _safe_log_value(state.get("agent_error_code")),
        "ticket_creation_status": _safe_log_value(
            state.get("ticket_creation_status")
        ),
    }
    if elapsed_ms is not None:
        metadata["elapsed_ms"] = round(elapsed_ms, 2)
    return metadata


def log_ticket_agent_run_started(
    *,
    operation: str,
    user_message: str | None = None,
    thread_id: str | None = None,
    actor_id: str | None = None,
) -> None:
    logger.info(
        (
            "ticket_agent_started operation=%s thread_id=%s actor_id=%s "
            "message_length=%s"
        ),
        operation,
        _safe_log_value(thread_id),
        _safe_log_value(actor_id),
        len(user_message or ""),
    )


def log_ticket_agent_run_finished(
    state: dict[str, Any],
    *,
    operation: str,
    elapsed_ms: float,
    thread_id: str | None = None,
) -> None:
    metadata = build_ticket_agent_observation_metadata(
        state,
        operation=operation,
        thread_id=thread_id,
        elapsed_ms=elapsed_ms,
    )
    logger.info(
        (
            "ticket_agent_finished operation=%s thread_id=%s elapsed_ms=%.2f "
            "intent=%s node_count=%s last_node=%s interrupted=%s "
            "fallback_used=%s agent_error_code=%s ticket_creation_status=%s"
        ),
        metadata["operation"],
        metadata["thread_id"],
        metadata["elapsed_ms"],
        metadata["intent"],
        metadata["node_count"],
        metadata["last_node"],
        metadata["interrupted"],
        metadata["fallback_used"],
        metadata["agent_error_code"],
        metadata["ticket_creation_status"],
    )


def log_ticket_agent_run_failed(
    exc: Exception,
    *,
    operation: str,
    elapsed_ms: float,
    thread_id: str | None = None,
) -> None:
    error_code = exc.code if isinstance(exc, AppException) else TICKET_AGENT_FALLBACK_ERROR_CODE
    logger.warning(
        (
            "ticket_agent_failed operation=%s thread_id=%s elapsed_ms=%.2f "
            "code=%s error_type=%s"
        ),
        operation,
        _safe_log_value(thread_id),
        elapsed_ms,
        error_code,
        type(exc).__name__,
    )


def retrieve_policy_node(
    state: TicketAgentState,
    service: PolicyRagService | None = None,
) -> TicketAgentState:
    rag_query = state.get("normalized_message", "").strip()
    rag_service = service or create_policy_rag_service()
    rag_answer = rag_service.answer_policy_question(rag_query)

    return {
        "rag_query": rag_query,
        "rag_answer_status": rag_answer.status.value,
        "rag_citations": [citation.model_dump() for citation in rag_answer.citations],
        "rag_no_context_reason": (
            rag_answer.no_context_reason.value
            if rag_answer.no_context_reason is not None
            else None
        ),
        "rag_suggestions": list(rag_answer.suggestions),
        "final_answer": rag_answer.answer,
        "node_history": ["retrieve_policy"],
    }


def query_order_node(state: TicketAgentState) -> TicketAgentState:
    return {
        "final_answer": "已识别为订单查询问题，后续课程会接入 query_order 工具。",
        "node_history": ["query_order"],
    }


def extract_ticket_fields_node(state: TicketAgentState) -> TicketAgentState:
    fields = extract_ticket_fields(state)
    missing_fields = find_missing_ticket_fields(fields)

    return {
        "ticket_fields": fields,
        "missing_ticket_fields": missing_fields,
        "ticket_fields_complete": not missing_fields,
        "ticket_field_extraction_source": "rule_based",
        "final_answer": _build_ticket_fields_extraction_answer(missing_fields),
        "node_history": ["extract_ticket_fields"],
    }


def ask_missing_ticket_fields_node(state: TicketAgentState) -> TicketAgentState:
    missing_fields = list(state.get("missing_ticket_fields", []))
    question = build_missing_ticket_fields_question(missing_fields)

    return {
        "missing_ticket_field_question": question,
        "missing_ticket_field_question_fields": missing_fields,
        "final_answer": question,
        "node_history": ["ask_missing_ticket_fields"],
    }


def request_ticket_confirmation_node(state: TicketAgentState) -> TicketAgentState:
    fields = state.get("ticket_fields")
    if fields is None:
        message = "当前还没有可确认的工单字段，请先补充问题信息。"
        return {
            "ticket_confirmation_required": False,
            "ticket_confirmation_message": message,
            "final_answer": message,
            "node_history": ["request_ticket_confirmation"],
        }

    pending_confirmation = build_pending_ticket_confirmation(fields)

    return {
        "ticket_confirmation_required": True,
        "ticket_confirmation_message": pending_confirmation["message"],
        "pending_ticket_confirmation": pending_confirmation,
        "final_answer": pending_confirmation["message"],
        "node_history": ["request_ticket_confirmation"],
    }


def request_ticket_confirmation_interrupt_node(
    state: TicketAgentState,
) -> TicketAgentState:
    fields = state.get("ticket_fields")
    if fields is None:
        message = "当前还没有可确认的工单字段，请先补充问题信息。"
        return {
            "ticket_confirmation_required": False,
            "ticket_confirmation_message": message,
            "final_answer": message,
            "node_history": ["request_ticket_confirmation"],
        }

    pending_confirmation = build_pending_ticket_confirmation(fields)
    resume_value = interrupt(
        build_ticket_confirmation_interrupt_payload(pending_confirmation)
    )
    approved = is_ticket_confirmation_resume_approved(resume_value)

    update: TicketAgentState = {
        "ticket_confirmation_required": True,
        "ticket_confirmation_approved": approved,
        "ticket_confirmation_message": pending_confirmation["message"],
        "pending_ticket_confirmation": pending_confirmation,
        "final_answer": (
            "用户已确认创建工单，正在继续执行。"
            if approved
            else TICKET_CONFIRMATION_REJECTED_MESSAGE
        ),
        "node_history": ["request_ticket_confirmation"],
    }
    actor_id = get_ticket_confirmation_resume_actor_id(resume_value)
    if actor_id is not None:
        update["ticket_actor_id"] = actor_id
    return update


def create_ticket_node(
    state: TicketAgentState,
    creator: TicketCreator | None = None,
) -> TicketAgentState:
    if state.get("ticket_confirmation_approved") is not True:
        message = "创建工单前需要先得到用户确认。"
        logger.info(
            "ticket_agent_create_ticket_blocked code=%s",
            "TICKET_CONFIRMATION_REQUIRED",
        )
        return {
            "ticket_creation_status": "blocked",
            "ticket_creation_error_code": "TICKET_CONFIRMATION_REQUIRED",
            "ticket_creation_error_message": message,
            "final_answer": message,
            "node_history": ["create_ticket"],
        }

    fields = _get_confirmed_ticket_fields(state)
    if fields is None:
        message = "没有找到可创建工单的确认字段，请重新整理工单信息。"
        logger.warning("ticket_agent_create_ticket_failed code=%s", "TICKET_FIELDS_NOT_FOUND")
        return build_ticket_creation_failure_state(
            code="TICKET_FIELDS_NOT_FOUND",
            message=message,
        )

    actor_id = state.get("ticket_actor_id") or DEFAULT_TICKET_ACTOR_ID
    idempotency_key = _get_ticket_creation_idempotency_key(state, fields)

    try:
        arguments = build_create_ticket_args_from_fields(fields, actor_id=actor_id)
        logger.info(
            (
                "ticket_agent_create_ticket_started category=%s priority=%s "
                "related_order_id=%s idempotency_key=%s"
            ),
            arguments.category,
            arguments.priority,
            _safe_log_value(arguments.related_order_id),
            idempotency_key,
        )
        ticket_creator = creator or create_ticket_creator()
        ticket = ticket_creator.create_ticket(
            arguments,
            idempotency_key=idempotency_key,
        )
    except AppException as exc:
        logger.warning(
            "ticket_agent_create_ticket_failed code=%s error_type=%s",
            exc.code,
            type(exc).__name__,
        )
        return build_ticket_creation_failure_state(
            code=exc.code,
            message=exc.message,
        )
    except Exception as exc:
        logger.warning(
            "ticket_agent_create_ticket_failed code=%s error_type=%s",
            TICKET_CREATION_UNEXPECTED_ERROR_CODE,
            type(exc).__name__,
        )
        return build_ticket_creation_failure_state(
            code=TICKET_CREATION_UNEXPECTED_ERROR_CODE,
            message=TICKET_CREATION_UNEXPECTED_ERROR_MESSAGE,
        )

    logger.info(
        (
            "ticket_agent_create_ticket_finished status=created ticket_id=%s "
            "category=%s priority=%s"
        ),
        ticket.ticket_id,
        ticket.category,
        ticket.priority,
    )
    return {
        "ticket_creation_args": arguments.model_dump(mode="json"),
        "ticket_creation_status": "created",
        "ticket_creation_error_code": None,
        "ticket_creation_error_message": None,
        "created_ticket": ticket.model_dump(mode="json"),
        "final_answer": (
            f"工单已创建，工单号：{ticket.ticket_id}。客服会根据工单继续处理。"
        ),
        "node_history": ["create_ticket"],
    }


def build_direct_answer_node(state: TicketAgentState) -> TicketAgentState:
    return {
        "final_answer": "你好，我是智能客服工单助手，可以帮你查询规则、订单和创建客服工单。",
        "node_history": ["build_direct_answer"],
    }


def build_unsupported_answer_node(state: TicketAgentState) -> TicketAgentState:
    return {
        "final_answer": "这个请求超出当前智能客服工单助手 v1 的处理范围。",
        "node_history": ["build_unsupported_answer"],
    }


def ask_clarifying_question_node(state: TicketAgentState) -> TicketAgentState:
    return {
        "final_answer": "我还不能确定你要处理的问题，请补充订单号、问题类型或具体诉求。",
        "node_history": ["ask_clarifying_question"],
    }


def build_ticket_agent_graph(
    ticket_creator: TicketCreator | None = None,
    *,
    policy_rag_service: PolicyRagService | None = None,
    checkpointer: Any | None = None,
    interrupt_confirmation: bool = False,
):
    builder = StateGraph(TicketAgentState)

    builder.add_node("normalize_user_input", normalize_user_input_node)
    builder.add_node("classify_intent", classify_intent_node)
    builder.add_node(
        "retrieve_policy",
        lambda state: retrieve_policy_node(state, service=policy_rag_service),
    )
    builder.add_node("decide_ticket_need", decide_ticket_need_node)
    builder.add_node("query_order", query_order_node)
    builder.add_node("extract_ticket_fields", extract_ticket_fields_node)
    builder.add_node("ask_missing_ticket_fields", ask_missing_ticket_fields_node)
    builder.add_node(
        "request_ticket_confirmation",
        (
            request_ticket_confirmation_interrupt_node
            if interrupt_confirmation
            else request_ticket_confirmation_node
        ),
    )
    builder.add_node(
        "create_ticket",
        lambda state: create_ticket_node(state, creator=ticket_creator),
    )
    builder.add_node("build_direct_answer", build_direct_answer_node)
    builder.add_node("build_unsupported_answer", build_unsupported_answer_node)
    builder.add_node("ask_clarifying_question", ask_clarifying_question_node)

    for start_node, end_node in TICKET_AGENT_FIXED_EDGES:
        builder.add_edge(start_node, end_node)

    builder.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        TICKET_AGENT_INTENT_ROUTES,
    )
    builder.add_conditional_edges(
        "decide_ticket_need",
        route_by_ticket_need,
        TICKET_AGENT_TICKET_NEED_ROUTES,
    )
    builder.add_conditional_edges(
        "extract_ticket_fields",
        route_by_ticket_fields_complete,
        TICKET_AGENT_FIELD_COMPLETION_ROUTES,
    )
    builder.add_conditional_edges(
        "request_ticket_confirmation",
        route_by_ticket_confirmation,
        TICKET_AGENT_CONFIRMATION_ROUTES,
    )

    return builder.compile(checkpointer=checkpointer)


ticket_agent_graph = build_ticket_agent_graph()


def build_checkpointed_ticket_agent_graph(
    ticket_creator: TicketCreator | None = None,
    *,
    policy_rag_service: PolicyRagService | None = None,
):
    return build_ticket_agent_graph(
        ticket_creator=ticket_creator,
        policy_rag_service=policy_rag_service,
        checkpointer=MemorySaver(),
    )


def build_interrupting_ticket_agent_graph(
    ticket_creator: TicketCreator | None = None,
    *,
    policy_rag_service: PolicyRagService | None = None,
):
    return build_ticket_agent_graph(
        ticket_creator=ticket_creator,
        policy_rag_service=policy_rag_service,
        checkpointer=MemorySaver(),
        interrupt_confirmation=True,
    )


def build_ticket_agent_input(user_message: str) -> TicketAgentState:
    return {
        "user_message": user_message,
        "agent_trace_id": get_trace_id(),
        "node_history": [],
    }


def build_ticket_agent_thread_config(thread_id: str) -> dict[str, Any]:
    normalized_thread_id = thread_id.strip()
    if not normalized_thread_id:
        raise ValueError("thread_id 不能为空。")

    return {"configurable": {"thread_id": normalized_thread_id}}


def run_ticket_agent(user_message: str) -> TicketAgentState:
    start_time = perf_counter()
    log_ticket_agent_run_started(
        operation="invoke",
        user_message=user_message,
    )
    try:
        result = ticket_agent_graph.invoke(build_ticket_agent_input(user_message))
    except Exception as exc:
        log_ticket_agent_run_failed(
            exc,
            operation="invoke",
            elapsed_ms=_elapsed_ms_since(start_time),
        )
        raise
    log_ticket_agent_run_finished(
        result,
        operation="invoke",
        elapsed_ms=_elapsed_ms_since(start_time),
    )
    return result


def run_ticket_agent_safely(
    user_message: str,
    *,
    graph: Any | None = None,
) -> TicketAgentState:
    selected_graph = graph or ticket_agent_graph
    start_time = perf_counter()
    log_ticket_agent_run_started(
        operation="invoke_safe",
        user_message=user_message,
    )
    try:
        result = selected_graph.invoke(build_ticket_agent_input(user_message))
    except AppException as exc:
        elapsed_ms = _elapsed_ms_since(start_time)
        log_ticket_agent_run_failed(
            exc,
            operation="invoke_safe",
            elapsed_ms=elapsed_ms,
        )
        fallback = build_ticket_agent_fallback_state(
            node_name="ticket_agent_graph",
            code=exc.code,
            message=exc.message,
        )
        log_ticket_agent_run_finished(
            fallback,
            operation="invoke_safe",
            elapsed_ms=elapsed_ms,
        )
        return fallback
    except Exception as exc:
        elapsed_ms = _elapsed_ms_since(start_time)
        log_ticket_agent_run_failed(
            exc,
            operation="invoke_safe",
            elapsed_ms=elapsed_ms,
        )
        fallback = build_ticket_agent_fallback_state(
            node_name="ticket_agent_graph",
        )
        log_ticket_agent_run_finished(
            fallback,
            operation="invoke_safe",
            elapsed_ms=elapsed_ms,
        )
        return fallback
    log_ticket_agent_run_finished(
        result,
        operation="invoke_safe",
        elapsed_ms=_elapsed_ms_since(start_time),
    )
    return result


def run_ticket_agent_in_thread(
    graph: Any,
    user_message: str,
    *,
    thread_id: str,
    actor_id: str | None = None,
) -> TicketAgentState:
    initial_state = build_ticket_agent_input(user_message)
    if actor_id is not None:
        initial_state["ticket_actor_id"] = actor_id

    start_time = perf_counter()
    log_ticket_agent_run_started(
        operation="invoke_thread",
        user_message=user_message,
        thread_id=thread_id,
        actor_id=actor_id,
    )
    try:
        result = graph.invoke(
            initial_state,
            config=build_ticket_agent_thread_config(thread_id),
        )
    except Exception as exc:
        log_ticket_agent_run_failed(
            exc,
            operation="invoke_thread",
            elapsed_ms=_elapsed_ms_since(start_time),
            thread_id=thread_id,
        )
        raise
    log_ticket_agent_run_finished(
        result,
        operation="invoke_thread",
        elapsed_ms=_elapsed_ms_since(start_time),
        thread_id=thread_id,
    )
    return result


def get_ticket_agent_thread_state(graph: Any, *, thread_id: str) -> TicketAgentState:
    snapshot = graph.get_state(build_ticket_agent_thread_config(thread_id))
    return dict(snapshot.values)


def approve_ticket_confirmation_and_resume(
    graph: Any,
    *,
    thread_id: str,
    actor_id: str | None = None,
) -> TicketAgentState:
    config = build_ticket_agent_thread_config(thread_id)
    current_state = graph.get_state(config).values
    if current_state.get("pending_ticket_confirmation") is None:
        raise AppException(
            code="TICKET_CONFIRMATION_NOT_FOUND",
            message=TICKET_CONFIRMATION_NOT_FOUND_MESSAGE,
            status_code=409,
        )

    approved_update: TicketAgentState = {"ticket_confirmation_approved": True}
    if actor_id is not None:
        approved_update["ticket_actor_id"] = actor_id

    graph.update_state(
        config,
        approved_update,
        as_node="request_ticket_confirmation",
    )
    return graph.invoke(None, config=config)


def get_ticket_confirmation_interrupt_payload(result: dict[str, Any]) -> dict[str, Any]:
    interrupts = result.get("__interrupt__")
    if not interrupts:
        raise AppException(
            code="TICKET_CONFIRMATION_INTERRUPT_NOT_FOUND",
            message=TICKET_CONFIRMATION_INTERRUPT_NOT_FOUND_MESSAGE,
            status_code=409,
        )

    interrupt_value = interrupts[0].value
    if (
        not isinstance(interrupt_value, dict)
        or interrupt_value.get("kind") != TICKET_CONFIRMATION_INTERRUPT_KIND
    ):
        raise AppException(
            code="TICKET_CONFIRMATION_INTERRUPT_NOT_FOUND",
            message=TICKET_CONFIRMATION_INTERRUPT_NOT_FOUND_MESSAGE,
            status_code=409,
        )

    return interrupt_value


def resume_ticket_confirmation_interrupt(
    graph: Any,
    *,
    thread_id: str,
    approved: bool,
    actor_id: str | None = None,
) -> TicketAgentState:
    resume_payload: dict[str, Any] = {"approved": approved}
    if actor_id is not None:
        resume_payload["actor_id"] = actor_id

    start_time = perf_counter()
    log_ticket_agent_run_started(
        operation="resume_interrupt",
        thread_id=thread_id,
        actor_id=actor_id,
    )
    try:
        result = graph.invoke(
            Command(resume=resume_payload),
            config=build_ticket_agent_thread_config(thread_id),
        )
    except Exception as exc:
        log_ticket_agent_run_failed(
            exc,
            operation="resume_interrupt",
            elapsed_ms=_elapsed_ms_since(start_time),
            thread_id=thread_id,
        )
        raise
    log_ticket_agent_run_finished(
        result,
        operation="resume_interrupt",
        elapsed_ms=_elapsed_ms_since(start_time),
        thread_id=thread_id,
    )
    return result


def resume_ticket_confirmation_interrupt_safely(
    graph: Any,
    *,
    thread_id: str,
    approved: bool,
    actor_id: str | None = None,
) -> TicketAgentState:
    try:
        return resume_ticket_confirmation_interrupt(
            graph,
            thread_id=thread_id,
            approved=approved,
            actor_id=actor_id,
        )
    except AppException as exc:
        return build_ticket_agent_fallback_state(
            node_name="resume_ticket_confirmation_interrupt",
            code=exc.code,
            message=exc.message,
        )
    except ValueError as exc:
        return build_ticket_agent_fallback_state(
            node_name="resume_ticket_confirmation_interrupt",
            code=TICKET_THREAD_ID_INVALID_ERROR_CODE,
            message=str(exc),
        )
    except Exception:
        return build_ticket_agent_fallback_state(
            node_name="resume_ticket_confirmation_interrupt",
        )


def stream_ticket_agent_updates(user_message: str) -> list[TicketAgentStreamPart]:
    return list(
        ticket_agent_graph.stream(
            build_ticket_agent_input(user_message),
            stream_mode="updates",
            version="v2",
        )
    )


def create_policy_rag_service() -> PolicyRagService:
    return FakePolicyRagService()


def create_ticket_creator() -> TicketCreator:
    return JavaTicketClient.from_settings(get_settings())


def _make_fake_retrieved_chunk(
    *,
    chunk_id: str,
    content: str,
    source: str,
    title: str,
    section: str,
) -> RetrievedChunk:
    return RetrievedChunk(
        point_id=f"fake-{chunk_id}",
        chunk_id=chunk_id,
        content=content,
        metadata={
            "source": source,
            "title": title,
            "section": section,
            "doc_type": "policy",
            "permission_group": "customer_service",
        },
        score=0.91,
    )


def _elapsed_ms_since(start_time: float) -> float:
    return (perf_counter() - start_time) * 1000


def _safe_log_value(value: object | None) -> str:
    if value is None:
        return TICKET_AGENT_LOG_VALUE_EMPTY
    text = str(value).strip()
    return text or TICKET_AGENT_LOG_VALUE_EMPTY


def _contains_any(message: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword.casefold() in message for keyword in keywords)


def _extract_order_id(message: str) -> str | None:
    match = ORDER_ID_PATTERN.search(message)
    if match is not None:
        return match.group(1).strip()

    fallback_match = FALLBACK_ORDER_ID_PATTERN.search(message)
    if fallback_match is not None:
        return fallback_match.group(1).strip()

    return None


def _infer_ticket_issue_type(
    lowered_message: str,
    *,
    ticket_need_source: TicketNeedSource | None,
    rag_answer_status: str | None,
) -> TicketIssueType:
    if _contains_any(lowered_message, COMPLAINT_ISSUE_KEYWORDS):
        return "complaint"
    if _contains_any(lowered_message, LOGISTICS_ISSUE_KEYWORDS):
        return "logistics"
    if _contains_any(lowered_message, REFUND_ISSUE_KEYWORDS):
        return "refund"
    if ticket_need_source == "rag_no_context" or rag_answer_status == "no_context":
        return "policy_gap"
    return "unknown"


def _infer_ticket_user_request(
    lowered_message: str,
    *,
    issue_type: TicketIssueType,
    ticket_need_source: TicketNeedSource | None,
) -> str:
    if "投诉" in lowered_message:
        return "投诉处理"
    if "创建工单" in lowered_message or "工单" in lowered_message:
        return "创建工单"
    if "人工" in lowered_message or "处理" in lowered_message:
        return "人工处理"
    if issue_type == "policy_gap" or ticket_need_source == "rag_no_context":
        return "补充或人工解释知识库未覆盖问题"
    if issue_type == "refund":
        return "售后退款处理"
    if issue_type == "logistics":
        return "物流问题处理"
    if issue_type == "complaint":
        return "投诉处理"
    return ""


def _infer_ticket_urgency(
    lowered_message: str,
    *,
    issue_type: TicketIssueType,
) -> TicketUrgencyLevel:
    if _contains_any(lowered_message, HIGH_URGENCY_KEYWORDS):
        return "high"
    if issue_type == "policy_gap":
        return "normal"
    return "normal"


def _build_ticket_description(
    normalized_message: str,
    *,
    ticket_need_source: TicketNeedSource | None,
) -> str:
    if ticket_need_source == "rag_no_context":
        return f"用户问题：{normalized_message}；知识库未找到足够资料。"
    return normalized_message


def _build_ticket_fields_extraction_answer(missing_fields: list[str]) -> str:
    if missing_fields:
        return (
            "已进入工单流程，并抽取了部分工单字段；仍缺少："
            f"{'、'.join(missing_fields)}。后续课程会学习如何追问缺失字段。"
        )
    return "已进入工单流程，并抽取了初步工单字段；后续课程会学习如何请求用户确认。"


def _build_ticket_creation_title(fields: TicketFields) -> str:
    issue_type_label = TICKET_ISSUE_TYPE_LABELS[fields["issue_type"]]
    order_part = f"订单 {fields['order_id']}" if fields["order_id"] else "无订单号"
    title = f"{issue_type_label}：{order_part}，{fields['user_request']}"
    return title[:200]


def _get_confirmed_ticket_fields(state: TicketAgentState) -> TicketFields | None:
    pending_confirmation = state.get("pending_ticket_confirmation")
    if pending_confirmation is not None:
        return pending_confirmation["ticket_fields"]
    return state.get("ticket_fields")


def _get_ticket_creation_idempotency_key(
    state: TicketAgentState,
    fields: TicketFields,
) -> str:
    pending_confirmation = state.get("pending_ticket_confirmation")
    if pending_confirmation is not None:
        return pending_confirmation["confirmation_id"]
    return build_ticket_confirmation_id(fields)
