import pytest
from langgraph.graph import END, START

from app.agents.ticket_agent import (
    TICKET_AGENT_FIXED_EDGES,
    TICKET_AGENT_INTENT_ROUTES,
    ask_clarifying_question_node,
    build_ticket_agent_input,
    classify_intent_node,
    classify_ticket_intent,
    normalize_user_input_node,
    route_by_intent,
    run_ticket_agent,
    stream_ticket_agent_updates,
)


def test_ticket_agent_fixed_edges_define_entry_and_finish_points() -> None:
    assert TICKET_AGENT_FIXED_EDGES == (
        (START, "normalize_user_input"),
        ("normalize_user_input", "classify_intent"),
        ("retrieve_policy", END),
        ("query_order", END),
        ("extract_ticket_fields", END),
        ("build_direct_answer", END),
        ("build_unsupported_answer", END),
        ("ask_clarifying_question", END),
    )


def test_ticket_agent_intent_routes_map_intent_to_next_node() -> None:
    assert TICKET_AGENT_INTENT_ROUTES == {
        "policy_question": "retrieve_policy",
        "order_query": "query_order",
        "ticket_request": "extract_ticket_fields",
        "smalltalk": "build_direct_answer",
        "unsupported": "build_unsupported_answer",
        "unclear": "ask_clarifying_question",
    }


@pytest.mark.parametrize(
    ("message", "expected_intent"),
    [
        ("退款规则是什么？", "policy_question"),
        ("我的订单 1001 到哪了？", "order_query"),
        ("我要投诉订单 1001，物流一直不动", "ticket_request"),
        ("你好，你能做什么？", "smalltalk"),
        ("帮我直接退款到账", "unsupported"),
        ("有问题", "unclear"),
        ("   ", "unclear"),
    ],
)
def test_classify_ticket_intent_returns_expected_intent(
    message: str,
    expected_intent: str,
) -> None:
    classification = classify_ticket_intent(message)

    assert classification["intent"] == expected_intent
    assert classification["reason"]


def test_normalize_user_input_node_returns_clean_message() -> None:
    update = normalize_user_input_node({"user_message": "  退款规则是什么？  "})

    assert update == {
        "normalized_message": "退款规则是什么？",
        "node_history": ["normalize_user_input"],
    }


def test_classify_intent_node_writes_intent_to_state() -> None:
    update = classify_intent_node({"normalized_message": "我的订单 1001 到哪了？"})

    assert update["intent"] == "order_query"
    assert update["intent_reason"]
    assert update["node_history"] == ["classify_intent"]


def test_route_by_intent_returns_matching_route() -> None:
    assert route_by_intent({"intent": "ticket_request"}) == "ticket_request"


def test_route_by_intent_defaults_to_unclear() -> None:
    assert route_by_intent({}) == "unclear"


@pytest.mark.parametrize(
    ("message", "expected_intent", "expected_last_node"),
    [
        ("退款规则是什么？", "policy_question", "retrieve_policy"),
        ("我的订单 1001 到哪了？", "order_query", "query_order"),
        ("我要投诉订单 1001", "ticket_request", "extract_ticket_fields"),
        ("你好", "smalltalk", "build_direct_answer"),
        ("帮我直接退款到账", "unsupported", "build_unsupported_answer"),
        ("这个怎么办", "unclear", "ask_clarifying_question"),
    ],
)
def test_run_ticket_agent_routes_to_expected_placeholder_node(
    message: str,
    expected_intent: str,
    expected_last_node: str,
) -> None:
    result = run_ticket_agent(message)

    assert result["intent"] == expected_intent
    assert result["final_answer"]
    assert result["node_history"] == [
        "normalize_user_input",
        "classify_intent",
        expected_last_node,
    ]


def test_stream_ticket_agent_updates_exposes_intent_route() -> None:
    chunks = stream_ticket_agent_updates("我的订单 1001 到哪了？")

    assert chunks[0]["data"] == {
        "normalize_user_input": {
            "normalized_message": "我的订单 1001 到哪了？",
            "node_history": ["normalize_user_input"],
        }
    }
    assert chunks[1]["data"]["classify_intent"]["intent"] == "order_query"
    assert chunks[2]["data"] == {
        "query_order": {
            "final_answer": "已识别为订单查询问题，后续课程会接入 query_order 工具。",
            "node_history": ["query_order"],
        }
    }


def test_build_ticket_agent_input_returns_initial_state() -> None:
    assert build_ticket_agent_input("hello") == {
        "user_message": "hello",
        "node_history": [],
    }


def test_ask_clarifying_question_node_returns_final_answer() -> None:
    update = ask_clarifying_question_node({})

    assert update == {
        "final_answer": "我还不能确定你要处理的问题，请补充订单号、问题类型或具体诉求。",
        "node_history": ["ask_clarifying_question"],
    }
