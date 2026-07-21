from operator import add
from typing import Annotated, Any, Literal
from typing_extensions import TypedDict

from langgraph.graph import END, START, StateGraph


TicketIntent = Literal[
    "policy_question",
    "order_query",
    "ticket_request",
    "smalltalk",
    "unsupported",
    "unclear",
]
TicketAgentRoute = TicketIntent
TicketAgentStreamPart = dict[str, Any]

TICKET_AGENT_FIXED_EDGES: tuple[tuple[str, str], ...] = (
    (START, "normalize_user_input"),
    ("normalize_user_input", "classify_intent"),
    ("retrieve_policy", END),
    ("query_order", END),
    ("extract_ticket_fields", END),
    ("build_direct_answer", END),
    ("build_unsupported_answer", END),
    ("ask_clarifying_question", END),
)

TICKET_AGENT_INTENT_ROUTES: dict[TicketAgentRoute, str] = {
    "policy_question": "retrieve_policy",
    "order_query": "query_order",
    "ticket_request": "extract_ticket_fields",
    "smalltalk": "build_direct_answer",
    "unsupported": "build_unsupported_answer",
    "unclear": "ask_clarifying_question",
}


class TicketAgentIntentClassification(TypedDict):
    intent: TicketIntent
    reason: str


class TicketAgentState(TypedDict, total=False):
    """State shared by the ticket agent learning graph."""

    user_message: str
    normalized_message: str
    intent: TicketIntent
    intent_reason: str
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


def retrieve_policy_node(state: TicketAgentState) -> TicketAgentState:
    return {
        "final_answer": "已识别为政策/规则问题，后续课程会接入 RAG 知识库回答。",
        "node_history": ["retrieve_policy"],
    }


def query_order_node(state: TicketAgentState) -> TicketAgentState:
    return {
        "final_answer": "已识别为订单查询问题，后续课程会接入 query_order 工具。",
        "node_history": ["query_order"],
    }


def extract_ticket_fields_node(state: TicketAgentState) -> TicketAgentState:
    return {
        "final_answer": "已识别为工单创建诉求，后续课程会抽取工单字段并请求确认。",
        "node_history": ["extract_ticket_fields"],
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


def build_ticket_agent_graph():
    builder = StateGraph(TicketAgentState)

    builder.add_node("normalize_user_input", normalize_user_input_node)
    builder.add_node("classify_intent", classify_intent_node)
    builder.add_node("retrieve_policy", retrieve_policy_node)
    builder.add_node("query_order", query_order_node)
    builder.add_node("extract_ticket_fields", extract_ticket_fields_node)
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

    return builder.compile()


ticket_agent_graph = build_ticket_agent_graph()


def build_ticket_agent_input(user_message: str) -> TicketAgentState:
    return {
        "user_message": user_message,
        "node_history": [],
    }


def run_ticket_agent(user_message: str) -> TicketAgentState:
    return ticket_agent_graph.invoke(build_ticket_agent_input(user_message))


def stream_ticket_agent_updates(user_message: str) -> list[TicketAgentStreamPart]:
    return list(
        ticket_agent_graph.stream(
            build_ticket_agent_input(user_message),
            stream_mode="updates",
            version="v2",
        )
    )


def _contains_any(message: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword.casefold() in message for keyword in keywords)
