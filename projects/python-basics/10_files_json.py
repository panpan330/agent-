import json
from pathlib import Path


BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
TEXT_FILE = DATA_DIR / "notes.txt"
JSON_FILE = DATA_DIR / "tasks.json"
REPORT_FILE = DATA_DIR / "task_report.json"


def write_text_demo() -> None:
    TEXT_FILE.write_text("今天学习 Python 文件读写。\n", encoding="utf-8")


def append_text_demo() -> None:
    with TEXT_FILE.open("a", encoding="utf-8") as file:
        file.write("追加一行：JSON 也很重要。\n")


def read_text_demo() -> str:
    return TEXT_FILE.read_text(encoding="utf-8")


def read_tasks() -> list[dict]:
    with JSON_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_tasks(tasks: list[dict]) -> None:
    with JSON_FILE.open("w", encoding="utf-8") as file:
        json.dump(tasks, file, ensure_ascii=False, indent=2)


def build_report(tasks: list[dict]) -> dict:
    total_count = len(tasks)
    done_count = 0

    for task in tasks:
        if task["done"]:
            done_count += 1

    return {
        "total_count": total_count,
        "done_count": done_count,
        "undone_count": total_count - done_count,
    }


def write_report(report: dict) -> None:
    with REPORT_FILE.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)


def add_task_if_missing(tasks: list[dict], task_name: str) -> None:
    for task in tasks:
        if task["name"] == task_name:
            return

    tasks.append({"name": task_name, "done": False})


def main() -> None:
    print("=== 1. 写入文本文件 ===")
    write_text_demo()
    append_text_demo()
    print(read_text_demo())

    print("=== 2. 读取 JSON 文件 ===")
    tasks = read_tasks()
    print(tasks)

    print("=== 3. 新增任务并写回 JSON ===")
    add_task_if_missing(tasks, "学习 JSON 文件")
    write_tasks(tasks)
    print(read_tasks())

    print("=== 4. 生成报告 ===")
    report = build_report(tasks)
    write_report(report)
    print(report)


if __name__ == "__main__":
    main()
