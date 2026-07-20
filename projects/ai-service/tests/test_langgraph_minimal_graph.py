from app.agents.minimal_graph import (
    MINIMAL_GRAPH_CONDITIONAL_ROUTES,
    MINIMAL_GRAPH_EDGES,
    build_blank_reply_node,
    build_minimal_graph,
    build_ready_reply_node,
    classify_message_node,
    normalize_message_node,
    route_by_message_status,
    run_minimal_graph,
)
from langgraph.graph import END, START


def test_minimal_graph_edges_define_fixed_parts_of_execution_order() -> None:
    assert MINIMAL_GRAPH_EDGES == (
        (START, "normalize_message"),
        ("normalize_message", "classify_message"),
        ("build_ready_reply", END),
        ("build_blank_reply", END),
    )


def test_minimal_graph_conditional_routes_map_status_to_reply_node() -> None:
    assert MINIMAL_GRAPH_CONDITIONAL_ROUTES == {
        "ready": "build_ready_reply",
        "blank": "build_blank_reply",
    }


def test_route_by_message_status_returns_ready_route() -> None:
    route = route_by_message_status({"message_status": "ready"})

    assert route == "ready"


def test_route_by_message_status_defaults_to_blank_route() -> None:
    route = route_by_message_status({})

    assert route == "blank"


def test_run_minimal_graph_returns_updated_state() -> None:
    result = run_minimal_graph("  你好，LangGraph  ")

    assert result["user_message"] == "  你好，LangGraph  "
    assert result["normalized_message"] == "你好，LangGraph"
    assert result["message_status"] == "ready"
    assert result["reply"] == "你说的是：你好，LangGraph"
    assert result["node_history"] == [
        "normalize_message",
        "classify_message",
        "build_ready_reply",
    ]


def test_run_minimal_graph_handles_blank_message() -> None:
    result = run_minimal_graph("   ")

    assert result["normalized_message"] == ""
    assert result["message_status"] == "blank"
    assert result["reply"] == "你还没有输入内容。"
    assert result["node_history"] == [
        "normalize_message",
        "classify_message",
        "build_blank_reply",
    ]


def test_build_minimal_graph_can_compile_independent_graph() -> None:
    graph = build_minimal_graph()

    result = graph.invoke({"user_message": "  test  ", "node_history": []})

    assert result["normalized_message"] == "test"
    assert result["message_status"] == "ready"
    assert result["reply"] == "你说的是：test"


def test_normalize_message_node_returns_only_its_state_update() -> None:
    update = normalize_message_node(
        {"user_message": "  hello  ", "reply": "old", "node_history": []}
    )

    assert update == {
        "normalized_message": "hello",
        "node_history": ["normalize_message"],
    }


def test_classify_message_node_returns_status_update() -> None:
    update = classify_message_node({"normalized_message": "hello"})

    assert update == {
        "message_status": "ready",
        "node_history": ["classify_message"],
    }


def test_build_ready_reply_node_returns_normal_reply() -> None:
    update = build_ready_reply_node({"normalized_message": "hello"})

    assert update == {
        "reply": "你说的是：hello",
        "node_history": ["build_ready_reply"],
    }


def test_build_blank_reply_node_returns_blank_reply() -> None:
    update = build_blank_reply_node({})

    assert update == {
        "reply": "你还没有输入内容。",
        "node_history": ["build_blank_reply"],
    }
