import asyncio
from pathlib import Path

import pytest

from learning_task_assistant.async_service import build_user_context
from learning_task_assistant.models import LearningTask
from learning_task_assistant.rules import (
    classify_question,
    extract_keywords,
    extract_order_ids,
    normalize_text,
)
from learning_task_assistant.service import LearningTaskAssistant
from learning_task_assistant.storage import load_tasks, save_tasks


def test_learning_task_validation() -> None:
    with pytest.raises(ValueError):
        LearningTask(task_id="", title="学习 pytest", topic="Python")

    with pytest.raises(ValueError):
        LearningTask(task_id="py-001", title="  ", topic="Python")


def test_learning_task_to_dict_and_from_dict() -> None:
    task = LearningTask(
        task_id="py-001",
        title=" 学习 pytest ",
        topic=" Python ",
        done=True,
        created_at="2026-07-05T00:00:00+00:00",
    )

    data = task.to_dict()
    loaded_task = LearningTask.from_dict(data)

    assert data == {
        "task_id": "py-001",
        "title": "学习 pytest",
        "topic": "Python",
        "done": True,
        "created_at": "2026-07-05T00:00:00+00:00",
    }
    assert loaded_task == task


def test_rules() -> None:
    question = "  订单 ORD-20260705-001 和 ORD-20260705-001 怎么退款？我要学习 pytest  "

    assert normalize_text(question) == "订单 ORD-20260705-001 和 ORD-20260705-001 怎么退款？我要学习 pytest"
    assert extract_order_ids(question) == ("ORD-20260705-001",)
    assert classify_question(question) == "refund"
    assert extract_keywords(question) == ("pytest",)


def test_storage_round_trip(tmp_path: Path) -> None:
    storage_path = tmp_path / "tasks.json"
    tasks = [
        LearningTask("py-001", "学习 pytest", "Python", done=True),
        LearningTask("py-002", "学习 FastAPI", "Python", done=False),
    ]

    save_tasks(storage_path, tasks)
    loaded_tasks = load_tasks(storage_path)

    assert [task.to_dict() for task in loaded_tasks] == [task.to_dict() for task in tasks]


def test_assistant_add_mark_analyze_and_summary(tmp_path: Path) -> None:
    assistant = LearningTaskAssistant(tmp_path / "tasks.json")
    assistant.add_task("py-001", "学习 pytest", "Python")
    assistant.add_task("ai-001", "学习 RAG", "AI")
    assistant.mark_done("py-001")

    analysis = assistant.analyze_question("订单 ORD-20260705-001 怎么退款？")
    summary = assistant.summarize_tasks()

    assert analysis.to_dict() == {
        "question": "订单 ORD-20260705-001 怎么退款？",
        "category": "refund",
        "order_ids": ["ORD-20260705-001"],
        "keywords": [],
    }
    assert summary == {
        "total": 2,
        "status": {"done": 1, "todo": 1},
        "topics": {"Python": 1, "AI": 1},
    }


def test_assistant_duplicate_and_missing_task(tmp_path: Path) -> None:
    assistant = LearningTaskAssistant(tmp_path / "tasks.json")
    assistant.add_task("py-001", "学习 pytest", "Python")

    with pytest.raises(ValueError):
        assistant.add_task("py-001", "重复任务", "Python")

    with pytest.raises(KeyError):
        assistant.mark_done("missing")


def test_assistant_save_and_reload(tmp_path: Path) -> None:
    storage_path = tmp_path / "tasks.json"
    assistant = LearningTaskAssistant(storage_path)
    assistant.add_task("py-001", "学习 pytest", "Python")
    assistant.save()

    reloaded_assistant = LearningTaskAssistant(storage_path)

    assert reloaded_assistant.find_task("py-001") is not None


def test_build_user_context() -> None:
    context = asyncio.run(build_user_context(330))

    assert context == {
        "user": {
            "user_id": 330,
            "name": "Panpan",
        },
        "permissions": ["call:ai", "read:tasks", "write:tasks"],
    }
