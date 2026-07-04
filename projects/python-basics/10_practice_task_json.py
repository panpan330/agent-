import json
from pathlib import Path


BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
TASK_FILE = DATA_DIR / "practice_tasks.json"
REPORT_FILE = DATA_DIR / "practice_report.json"


def create_default_tasks() -> list[dict]:
    return [
        {"name": "学习变量", "done": True},
        {"name": "学习字符串", "done": True},
        {"name": "学习列表", "done": True},
        {"name": "学习文件读写", "done": False},
    ]


def save_json(path: Path, data: list[dict] | dict) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def load_json(path: Path) -> list[dict]:
    if not path.exists():
        default_tasks = create_default_tasks()
        save_json(path, default_tasks)
        return default_tasks

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def add_task(tasks: list[dict], name: str) -> None:
    for task in tasks:
        if task["name"] == name:
            return

    tasks.append({"name": name, "done": False})


def build_report(tasks: list[dict]) -> dict:
    done_count = 0
    undone_tasks = []

    for task in tasks:
        if task["done"]:
            done_count += 1
        else:
            undone_tasks.append(task["name"])

    return {
        "total_count": len(tasks),
        "done_count": done_count,
        "undone_count": len(undone_tasks),
        "undone_tasks": undone_tasks,
    }


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)

    tasks = load_json(TASK_FILE)
    add_task(tasks, "学习 JSON 文件")
    save_json(TASK_FILE, tasks)

    report = build_report(tasks)
    save_json(REPORT_FILE, report)

    print("任务:", tasks)
    print("报告:", report)


if __name__ == "__main__":
    main()
