import json
from pathlib import Path

from learning_task_assistant.models import LearningTask


def load_tasks(path: Path) -> list[LearningTask]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("tasks json must be a list")

    tasks = []
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("each task must be an object")
        tasks.append(LearningTask.from_dict(item))

    return tasks


def save_tasks(path: Path, tasks: list[LearningTask]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            [task.to_dict() for task in tasks],
            file,
            ensure_ascii=False,
            indent=2,
        )
