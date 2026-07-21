import pytest
from langgraph.graph import END, START

from app.agents.ticket_agent import (
    FakePolicyRagService,
    TICKET_AGENT_CONFIRMATION_ROUTES,
    TICKET_AGENT_FIELD_COMPLETION_ROUTES,
    TICKET_AGENT_FIXED_EDGES,
    TICKET_AGENT_INTENT_ROUTES,
    TICKET_AGENT_TICKET_NEED_ROUTES,
    ask_missing_ticket_fields_node,
    ask_clarifying_question_node,
    build_create_ticket_args_from_fields,
    build_ticket_agent_graph,
    build_pending_ticket_confirmation,
    build_missing_ticket_fields_question,
    build_ticket_confirmation_message,
    build_ticket_agent_input,
    classify_intent_node,
    classify_ticket_intent,
    decide_ticket_need,
    decide_ticket_need_node,
    extract_ticket_fields,
    extract_ticket_fields_node,
    find_missing_ticket_fields,
    normalize_user_input_node,
    create_ticket_node,
    retrieve_policy_node,
    request_ticket_confirmation_node,
    route_by_ticket_confirmation,
    route_by_ticket_fields_complete,
    route_by_intent,
    route_by_ticket_need,
    run_ticket_agent,
    stream_ticket_agent_updates,
)
from app.core.exceptions import AppException
from app.rag.generator import RAG_NO_CONTEXT_REPLY
from tests.tool_fakes import FakeTicketCreator


def make_complete_ticket_fields() -> dict[str, object]:
    return {
        "issue_type": "complaint",
        "order_id": "1001",
        "description": "我要投诉订单 1001，物流一直不动",
        "user_request": "投诉处理",
        "urgency": "high",
        "need_human_review": True,
    }


def test_ticket_agent_fixed_edges_define_entry_and_finish_points() -> None:
    assert TICKET_AGENT_FIXED_EDGES == (
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


def test_ticket_agent_intent_routes_map_intent_to_next_node() -> None:
    assert TICKET_AGENT_INTENT_ROUTES == {
        "policy_question": "retrieve_policy",
        "order_query": "query_order",
        "ticket_request": "decide_ticket_need",
        "smalltalk": "build_direct_answer",
        "unsupported": "build_unsupported_answer",
        "unclear": "ask_clarifying_question",
    }


def test_ticket_agent_ticket_need_routes_map_decision_to_next_node() -> None:
    assert TICKET_AGENT_TICKET_NEED_ROUTES == {
        "create_ticket": "extract_ticket_fields",
        "finish": END,
    }


def test_ticket_agent_field_completion_routes_map_decision_to_next_node() -> None:
    assert TICKET_AGENT_FIELD_COMPLETION_ROUTES == {
        "ask_missing_fields": "ask_missing_ticket_fields",
        "request_confirmation": "request_ticket_confirmation",
    }


def test_ticket_agent_confirmation_routes_map_decision_to_next_node() -> None:
    assert TICKET_AGENT_CONFIRMATION_ROUTES == {
        "execute_create_ticket": "create_ticket",
        "finish": END,
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


def test_decide_ticket_need_returns_true_for_explicit_ticket_request() -> None:
    decision = decide_ticket_need(
        {
            "intent": "ticket_request",
            "normalized_message": "我要投诉订单 1001",
        }
    )

    assert decision == {
        "needs_ticket": True,
        "reason": "用户明确表达了投诉、售后处理或创建工单诉求，需要进入工单流程。",
        "source": "explicit_user_request",
    }


def test_decide_ticket_need_returns_false_when_rag_answered() -> None:
    decision = decide_ticket_need(
        {
            "intent": "policy_question",
            "rag_answer_status": "answered",
        }
    )

    assert decision == {
        "needs_ticket": False,
        "reason": "知识库已给出可引用回答，当前不需要创建工单。",
        "source": "rag_answered",
    }


def test_decide_ticket_need_returns_true_when_rag_has_no_context() -> None:
    decision = decide_ticket_need(
        {
            "intent": "policy_question",
            "rag_answer_status": "no_context",
        }
    )

    assert decision == {
        "needs_ticket": True,
        "reason": "知识库没有找到足够资料，需要进入工单流程记录问题或交给人工处理。",
        "source": "rag_no_context",
    }


def test_decide_ticket_need_node_writes_decision_to_state() -> None:
    update = decide_ticket_need_node(
        {
            "intent": "ticket_request",
            "normalized_message": "我要创建工单",
        }
    )

    assert update == {
        "needs_ticket": True,
        "ticket_need_reason": "用户明确表达了投诉、售后处理或创建工单诉求，需要进入工单流程。",
        "ticket_need_source": "explicit_user_request",
        "node_history": ["decide_ticket_need"],
    }


def test_route_by_ticket_need_returns_create_ticket_when_needed() -> None:
    assert route_by_ticket_need({"needs_ticket": True}) == "create_ticket"


def test_route_by_ticket_need_returns_finish_by_default() -> None:
    assert route_by_ticket_need({}) == "finish"


def test_route_by_ticket_fields_complete_asks_when_fields_incomplete() -> None:
    assert (
        route_by_ticket_fields_complete({"ticket_fields_complete": False})
        == "ask_missing_fields"
    )


def test_route_by_ticket_fields_complete_requests_confirmation_when_complete() -> None:
    assert (
        route_by_ticket_fields_complete({"ticket_fields_complete": True})
        == "request_confirmation"
    )


def test_route_by_ticket_fields_complete_asks_by_default() -> None:
    assert route_by_ticket_fields_complete({}) == "ask_missing_fields"


def test_route_by_ticket_confirmation_executes_only_when_approved() -> None:
    assert (
        route_by_ticket_confirmation({"ticket_confirmation_approved": True})
        == "execute_create_ticket"
    )


def test_route_by_ticket_confirmation_finishes_by_default() -> None:
    assert route_by_ticket_confirmation({}) == "finish"


def test_build_missing_ticket_fields_question_returns_single_field_question() -> None:
    assert build_missing_ticket_fields_question(["order_id"]) == (
        "请补充相关订单号（例如 1001 或 A1001），这样我才能继续为你整理工单。"
    )


def test_build_missing_ticket_fields_question_returns_multi_field_question() -> None:
    question = build_missing_ticket_fields_question(["issue_type", "order_id"])

    assert question.startswith("为了继续创建工单，请补充以下信息：")
    assert "请说明这是退款、物流、投诉，还是其他需要人工处理的问题。" in question
    assert "请补充相关订单号" in question


def test_build_missing_ticket_fields_question_handles_complete_fields() -> None:
    assert build_missing_ticket_fields_question([]) == (
        "工单字段已经完整，后续课程会学习如何请求用户确认。"
    )


def test_extract_ticket_fields_from_explicit_complaint_with_order_id() -> None:
    fields = extract_ticket_fields(
        {
            "normalized_message": "我要投诉订单 1001，物流一直不动",
            "ticket_need_source": "explicit_user_request",
        }
    )

    assert fields == {
        "issue_type": "complaint",
        "order_id": "1001",
        "description": "我要投诉订单 1001，物流一直不动",
        "user_request": "投诉处理",
        "urgency": "high",
        "need_human_review": True,
    }


def test_extract_ticket_fields_marks_order_id_missing_for_order_related_issue() -> None:
    fields = extract_ticket_fields(
        {
            "normalized_message": "商品破损，帮我处理",
            "ticket_need_source": "explicit_user_request",
        }
    )

    assert fields["issue_type"] == "complaint"
    assert fields["order_id"] is None
    assert find_missing_ticket_fields(fields) == ["order_id"]


def test_extract_ticket_fields_builds_policy_gap_ticket_from_rag_no_context() -> None:
    fields = extract_ticket_fields(
        {
            "normalized_message": "会员等级政策是什么？",
            "ticket_need_source": "rag_no_context",
            "rag_answer_status": "no_context",
        }
    )

    assert fields == {
        "issue_type": "policy_gap",
        "order_id": None,
        "description": "用户问题：会员等级政策是什么？；知识库未找到足够资料。",
        "user_request": "补充或人工解释知识库未覆盖问题",
        "urgency": "normal",
        "need_human_review": True,
    }
    assert find_missing_ticket_fields(fields) == []


def test_extract_ticket_fields_node_writes_complete_fields_to_state() -> None:
    update = extract_ticket_fields_node(
        {
            "normalized_message": "我要投诉订单 1001，物流一直不动",
            "ticket_need_source": "explicit_user_request",
        }
    )

    assert update["ticket_fields"] == {
        "issue_type": "complaint",
        "order_id": "1001",
        "description": "我要投诉订单 1001，物流一直不动",
        "user_request": "投诉处理",
        "urgency": "high",
        "need_human_review": True,
    }
    assert update["missing_ticket_fields"] == []
    assert update["ticket_fields_complete"] is True
    assert update["ticket_field_extraction_source"] == "rule_based"
    assert update["node_history"] == ["extract_ticket_fields"]


def test_extract_ticket_fields_node_writes_missing_fields_to_state() -> None:
    update = extract_ticket_fields_node(
        {
            "normalized_message": "商品破损，帮我处理",
            "ticket_need_source": "explicit_user_request",
        }
    )

    assert update["ticket_fields"]["issue_type"] == "complaint"
    assert update["ticket_fields"]["order_id"] is None
    assert update["missing_ticket_fields"] == ["order_id"]
    assert update["ticket_fields_complete"] is False
    assert "order_id" in update["final_answer"]


def test_ask_missing_ticket_fields_node_writes_question_to_state() -> None:
    update = ask_missing_ticket_fields_node({"missing_ticket_fields": ["order_id"]})

    assert update == {
        "missing_ticket_field_question": (
            "请补充相关订单号（例如 1001 或 A1001），这样我才能继续为你整理工单。"
        ),
        "missing_ticket_field_question_fields": ["order_id"],
        "final_answer": "请补充相关订单号（例如 1001 或 A1001），这样我才能继续为你整理工单。",
        "node_history": ["ask_missing_ticket_fields"],
    }


def test_build_ticket_confirmation_message_includes_key_fields() -> None:
    fields = {
        "issue_type": "complaint",
        "order_id": "1001",
        "description": "我要投诉订单 1001，物流一直不动",
        "user_request": "投诉处理",
        "urgency": "high",
        "need_human_review": True,
    }

    message = build_ticket_confirmation_message(fields)

    assert "请确认是否按以下信息创建" in message
    assert "问题类型：投诉/异常处理" in message
    assert "订单号：1001" in message
    assert "问题描述：我要投诉订单 1001，物流一直不动" in message
    assert "用户诉求：投诉处理" in message
    assert "紧急程度：高" in message
    assert "确认创建" in message


def test_build_pending_ticket_confirmation_is_stable_for_same_fields() -> None:
    fields = {
        "issue_type": "complaint",
        "order_id": "1001",
        "description": "我要投诉订单 1001，物流一直不动",
        "user_request": "投诉处理",
        "urgency": "high",
        "need_human_review": True,
    }

    first = build_pending_ticket_confirmation(fields)
    second = build_pending_ticket_confirmation(fields)

    assert first["confirmation_id"] == second["confirmation_id"]
    assert first["status"] == "pending"
    assert first["title"] == "待确认工单：投诉/异常处理"
    assert first["ticket_fields"] == fields
    assert first["message"]


def test_request_ticket_confirmation_node_writes_pending_confirmation_to_state() -> None:
    fields = make_complete_ticket_fields()

    update = request_ticket_confirmation_node({"ticket_fields": fields})

    assert update["ticket_confirmation_required"] is True
    assert update["pending_ticket_confirmation"]["status"] == "pending"
    assert update["pending_ticket_confirmation"]["ticket_fields"] == fields
    assert update["ticket_confirmation_message"] == update["final_answer"]
    assert update["node_history"] == ["request_ticket_confirmation"]


def test_build_create_ticket_args_from_fields_maps_agent_fields_to_java_contract() -> None:
    arguments = build_create_ticket_args_from_fields(
        make_complete_ticket_fields(),
        actor_id="demo_user_001",
    )

    assert arguments.requester_id == "demo_user_001"
    assert arguments.title == "投诉/异常处理：订单 1001，投诉处理"
    assert arguments.description == "我要投诉订单 1001，物流一直不动"
    assert arguments.category == "complaint"
    assert arguments.priority == "high"
    assert arguments.related_order_id == "1001"


def test_build_create_ticket_args_from_policy_gap_fields_maps_contract() -> None:
    arguments = build_create_ticket_args_from_fields(
        {
            "issue_type": "policy_gap",
            "order_id": None,
            "description": "用户问题：会员等级政策是什么？；知识库未找到足够资料。",
            "user_request": "补充或人工解释知识库未覆盖问题",
            "urgency": "normal",
            "need_human_review": True,
        },
        actor_id="demo_user_001",
    )

    assert arguments.category == "policy_gap"
    assert arguments.priority == "normal"
    assert arguments.related_order_id is None


def test_create_ticket_node_blocks_without_user_confirmation() -> None:
    creator = FakeTicketCreator()
    update = create_ticket_node(
        {"ticket_fields": make_complete_ticket_fields()},
        creator=creator,
    )

    assert update["ticket_creation_status"] == "blocked"
    assert update["ticket_creation_error_code"] == "TICKET_CONFIRMATION_REQUIRED"
    assert update["final_answer"] == "创建工单前需要先得到用户确认。"
    assert update["node_history"] == ["create_ticket"]
    assert creator.calls == []


def test_create_ticket_node_calls_creator_after_confirmation() -> None:
    fields = make_complete_ticket_fields()
    pending_confirmation = build_pending_ticket_confirmation(fields)
    creator = FakeTicketCreator()

    update = create_ticket_node(
        {
            "ticket_actor_id": "demo_user_001",
            "ticket_confirmation_approved": True,
            "pending_ticket_confirmation": pending_confirmation,
        },
        creator=creator,
    )

    assert update["ticket_creation_status"] == "created"
    assert update["ticket_creation_args"]["requester_id"] == "demo_user_001"
    assert update["ticket_creation_args"]["category"] == "complaint"
    assert update["created_ticket"]["ticket_id"] == "T1001"
    assert "工单已创建，工单号：T1001" in update["final_answer"]
    assert update["node_history"] == ["create_ticket"]
    assert len(creator.calls) == 1
    assert creator.idempotency_keys == [pending_confirmation["confirmation_id"]]


def test_create_ticket_node_writes_failure_state_when_creator_fails() -> None:
    creator = FakeTicketCreator(
        error=AppException(
            code="TOOL_UPSTREAM_ERROR",
            message="工单业务服务暂时不可用，请稍后重试。",
            status_code=502,
        )
    )

    update = create_ticket_node(
        {
            "ticket_confirmation_approved": True,
            "ticket_fields": make_complete_ticket_fields(),
        },
        creator=creator,
    )

    assert update["ticket_creation_status"] == "failed"
    assert update["ticket_creation_error_code"] == "TOOL_UPSTREAM_ERROR"
    assert update["final_answer"] == "工单业务服务暂时不可用，请稍后重试。"
    assert update["node_history"] == ["create_ticket"]


def test_retrieve_policy_node_returns_grounded_rag_answer() -> None:
    update = retrieve_policy_node({"normalized_message": "退款规则是什么？"})

    assert update["rag_query"] == "退款规则是什么？"
    assert update["rag_answer_status"] == "answered"
    assert update["final_answer"] == (
        "根据知识库，退款申请通常需要先核对订单状态和售后条件，"
        "用户可以按退款退货规则提交申请。"
    )
    assert update["rag_citations"][0]["source"] == "refund-return-policy.md"
    assert update["rag_citations"][0]["chunk_id"] == "refund_return_policy_chunk_0001"
    assert update["rag_no_context_reason"] is None
    assert update["rag_suggestions"] == []
    assert update["node_history"] == ["retrieve_policy"]


def test_retrieve_policy_node_returns_no_context_fallback() -> None:
    update = retrieve_policy_node(
        {"normalized_message": "会员等级政策是什么？"},
        service=FakePolicyRagService(),
    )

    assert update["rag_query"] == "会员等级政策是什么？"
    assert update["rag_answer_status"] == "no_context"
    assert update["final_answer"] == RAG_NO_CONTEXT_REPLY
    assert update["rag_citations"] == []
    assert update["rag_no_context_reason"] == "no_retrieved_chunks"
    assert update["rag_suggestions"]
    assert update["node_history"] == ["retrieve_policy"]


def test_run_ticket_agent_policy_question_uses_rag_answer_node() -> None:
    result = run_ticket_agent("退款规则是什么？")

    assert result["intent"] == "policy_question"
    assert result["rag_answer_status"] == "answered"
    assert result["needs_ticket"] is False
    assert result["ticket_need_source"] == "rag_answered"
    assert result["rag_citations"][0]["chunk_id"] == "refund_return_policy_chunk_0001"
    assert result["node_history"] == [
        "normalize_user_input",
        "classify_intent",
        "retrieve_policy",
        "decide_ticket_need",
    ]


def test_run_ticket_agent_policy_no_context_enters_ticket_flow() -> None:
    result = run_ticket_agent("会员等级政策是什么？")

    assert result["intent"] == "policy_question"
    assert result["rag_answer_status"] == "no_context"
    assert result["needs_ticket"] is True
    assert result["ticket_need_source"] == "rag_no_context"
    assert result["ticket_fields"] == {
        "issue_type": "policy_gap",
        "order_id": None,
        "description": "用户问题：会员等级政策是什么？；知识库未找到足够资料。",
        "user_request": "补充或人工解释知识库未覆盖问题",
        "urgency": "normal",
        "need_human_review": True,
    }
    assert result["ticket_fields_complete"] is True
    assert result["ticket_confirmation_required"] is True
    assert result["pending_ticket_confirmation"]["status"] == "pending"
    assert (
        result["pending_ticket_confirmation"]["ticket_fields"]
        == result["ticket_fields"]
    )
    assert "请确认是否按以下信息创建" in result["final_answer"]
    assert result["node_history"] == [
        "normalize_user_input",
        "classify_intent",
        "retrieve_policy",
        "decide_ticket_need",
        "extract_ticket_fields",
        "request_ticket_confirmation",
    ]


def test_run_ticket_agent_missing_order_id_asks_follow_up_question() -> None:
    result = run_ticket_agent("商品破损，帮我处理")

    assert result["intent"] == "ticket_request"
    assert result["needs_ticket"] is True
    assert result["ticket_fields"]["issue_type"] == "complaint"
    assert result["ticket_fields"]["order_id"] is None
    assert result["missing_ticket_fields"] == ["order_id"]
    assert result["ticket_fields_complete"] is False
    assert result["missing_ticket_field_question_fields"] == ["order_id"]
    assert result["final_answer"] == (
        "请补充相关订单号（例如 1001 或 A1001），这样我才能继续为你整理工单。"
    )
    assert result["node_history"] == [
        "normalize_user_input",
        "classify_intent",
        "decide_ticket_need",
        "extract_ticket_fields",
        "ask_missing_ticket_fields",
    ]


def test_run_ticket_agent_complete_ticket_fields_requests_confirmation() -> None:
    result = run_ticket_agent("我要投诉订单 1001，物流一直不动")

    assert result["intent"] == "ticket_request"
    assert result["needs_ticket"] is True
    assert result["ticket_fields_complete"] is True
    assert result["ticket_confirmation_required"] is True
    assert result["pending_ticket_confirmation"]["status"] == "pending"
    assert (
        result["pending_ticket_confirmation"]["ticket_fields"]
        == result["ticket_fields"]
    )
    assert "问题类型：投诉/异常处理" in result["final_answer"]
    assert "确认创建" in result["final_answer"]
    assert result["node_history"] == [
        "normalize_user_input",
        "classify_intent",
        "decide_ticket_need",
        "extract_ticket_fields",
        "request_ticket_confirmation",
    ]


def test_graph_executes_ticket_creation_when_confirmation_is_approved() -> None:
    creator = FakeTicketCreator()
    graph = build_ticket_agent_graph(ticket_creator=creator)

    result = graph.invoke(
        {
            "user_message": "我要投诉订单 1001，物流一直不动",
            "ticket_actor_id": "demo_user_001",
            "ticket_confirmation_approved": True,
            "node_history": [],
        }
    )

    assert result["ticket_confirmation_required"] is True
    assert result["ticket_creation_status"] == "created"
    assert result["created_ticket"]["ticket_id"] == "T1001"
    assert result["node_history"] == [
        "normalize_user_input",
        "classify_intent",
        "decide_ticket_need",
        "extract_ticket_fields",
        "request_ticket_confirmation",
        "create_ticket",
    ]
    assert len(creator.calls) == 1


@pytest.mark.parametrize(
    ("message", "expected_intent", "expected_node_history"),
    [
        (
            "退款规则是什么？",
            "policy_question",
            [
                "normalize_user_input",
                "classify_intent",
                "retrieve_policy",
                "decide_ticket_need",
            ],
        ),
        (
            "我的订单 1001 到哪了？",
            "order_query",
            ["normalize_user_input", "classify_intent", "query_order"],
        ),
        (
            "我要投诉订单 1001",
            "ticket_request",
            [
                "normalize_user_input",
                "classify_intent",
                "decide_ticket_need",
                "extract_ticket_fields",
                "request_ticket_confirmation",
            ],
        ),
        (
            "你好",
            "smalltalk",
            ["normalize_user_input", "classify_intent", "build_direct_answer"],
        ),
        (
            "帮我直接退款到账",
            "unsupported",
            ["normalize_user_input", "classify_intent", "build_unsupported_answer"],
        ),
        (
            "这个怎么办",
            "unclear",
            ["normalize_user_input", "classify_intent", "ask_clarifying_question"],
        ),
    ],
)
def test_run_ticket_agent_routes_to_expected_business_path(
    message: str,
    expected_intent: str,
    expected_node_history: list[str],
) -> None:
    result = run_ticket_agent(message)

    assert result["intent"] == expected_intent
    assert result["final_answer"]
    assert result["node_history"] == expected_node_history


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


def test_stream_ticket_agent_updates_exposes_rag_answer_update() -> None:
    chunks = stream_ticket_agent_updates("账号安全怎么验证？")

    policy_update = chunks[2]["data"]["retrieve_policy"]
    assert policy_update["rag_answer_status"] == "answered"
    assert policy_update["rag_citations"][0]["source"] == "account-security-faq.md"
    assert policy_update["node_history"] == ["retrieve_policy"]


def test_stream_ticket_agent_updates_exposes_ticket_need_decision() -> None:
    chunks = stream_ticket_agent_updates("退款规则是什么？")

    decision_update = chunks[3]["data"]["decide_ticket_need"]
    assert decision_update == {
        "needs_ticket": False,
        "ticket_need_reason": "知识库已给出可引用回答，当前不需要创建工单。",
        "ticket_need_source": "rag_answered",
        "node_history": ["decide_ticket_need"],
    }


def test_stream_ticket_agent_updates_exposes_ticket_field_extraction() -> None:
    chunks = stream_ticket_agent_updates("我要投诉订单 1001，物流一直不动")

    extraction_update = chunks[3]["data"]["extract_ticket_fields"]
    assert extraction_update["ticket_fields"]["issue_type"] == "complaint"
    assert extraction_update["ticket_fields"]["order_id"] == "1001"
    assert extraction_update["missing_ticket_fields"] == []
    assert extraction_update["ticket_fields_complete"] is True
    assert extraction_update["node_history"] == ["extract_ticket_fields"]


def test_stream_ticket_agent_updates_exposes_ticket_confirmation_request() -> None:
    chunks = stream_ticket_agent_updates("我要投诉订单 1001，物流一直不动")

    confirmation_update = chunks[4]["data"]["request_ticket_confirmation"]
    assert confirmation_update["ticket_confirmation_required"] is True
    assert (
        confirmation_update["pending_ticket_confirmation"]["status"]
        == "pending"
    )
    assert "问题类型：投诉/异常处理" in confirmation_update["final_answer"]
    assert confirmation_update["node_history"] == ["request_ticket_confirmation"]


def test_stream_ticket_agent_updates_exposes_missing_field_question() -> None:
    chunks = stream_ticket_agent_updates("商品破损，帮我处理")

    question_update = chunks[4]["data"]["ask_missing_ticket_fields"]
    assert question_update == {
        "missing_ticket_field_question": (
            "请补充相关订单号（例如 1001 或 A1001），这样我才能继续为你整理工单。"
        ),
        "missing_ticket_field_question_fields": ["order_id"],
        "final_answer": "请补充相关订单号（例如 1001 或 A1001），这样我才能继续为你整理工单。",
        "node_history": ["ask_missing_ticket_fields"],
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
