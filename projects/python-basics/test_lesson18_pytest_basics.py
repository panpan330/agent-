from pathlib import Path
import json

import pytest

from lesson18_pytest_basics import (
    add,
    classify_question,
    clean_question,
    is_valid_order_id,
    load_tasks_from_json,
    parse_score,
    summarize_tasks,
)


def test_add() -> None:
    assert add(2, 3) == 5


def test_clean_question() -> None:
    assert clean_question("  Python    pytest   怎么学？  ") == "Python pytest 怎么学？"


@pytest.mark.parametrize(
    ("order_id", "expected"),
    [
        ("ORD-20260705-001", True),
        ("ORD-20260705-01", False),
        ("订单 ORD-20260705-001", False),
    ],
)
def test_is_valid_order_id(order_id: str, expected: bool) -> None:
    assert is_valid_order_id(order_id) is expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("0.82", 0.82),
        (1, 1.0),
        (0, 0.0),
    ],
)
def test_parse_score_success(value: object, expected: float) -> None:
    assert parse_score(value) == expected


@pytest.mark.parametrize("value", ["abc", -0.1, 1.2, None])
def test_parse_score_error(value: object) -> None:
    with pytest.raises(ValueError):
        parse_score(value)


def test_load_tasks_from_json(tmp_path: Path) -> None:
    tasks_file = tmp_path / "tasks.json"
    tasks_file.write_text(
        json.dumps(
            [
                {"name": "学习 pytest", "done": True},
                {"name": "学习 FastAPI", "done": False},
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    tasks = load_tasks_from_json(tasks_file)

    assert len(tasks) == 2
    assert tasks[0]["name"] == "学习 pytest"


def test_load_tasks_from_json_rejects_non_list(tmp_path: Path) -> None:
    tasks_file = tmp_path / "tasks.json"
    tasks_file.write_text(json.dumps({"name": "not list"}), encoding="utf-8")

    with pytest.raises(ValueError):
        load_tasks_from_json(tasks_file)


def test_summarize_tasks() -> None:
    tasks = [
        {"name": "学习 pytest", "done": True},
        {"name": "学习 FastAPI", "done": False},
        {"name": "学习 logging", "done": True},
    ]

    assert summarize_tasks(tasks) == {
        "done": 2,
        "todo": 1,
        "total": 3,
    }


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("我的订单怎么退款？", "refund"),
        ("快递什么时候发货？", "shipping"),
        ("帮我开发票", "invoice"),
        ("Python 怎么学？", "other"),
    ],
)
def test_classify_question(question: str, expected: str) -> None:
    assert classify_question(question) == expected
