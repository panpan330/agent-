import json
import re
from pathlib import Path


def add(a: int, b: int) -> int:
    return a + b


def clean_question(question: str) -> str:
    return " ".join(question.strip().split())


def is_valid_order_id(order_id: str) -> bool:
    return re.fullmatch(r"ORD-\d{8}-\d{3}", order_id) is not None


def parse_score(value: object) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError("score must be a number") from error

    if score < 0 or score > 1:
        raise ValueError("score must be between 0 and 1")

    return score


def load_tasks_from_json(path: Path) -> list[dict[str, object]]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("tasks json must be a list")

    tasks = []
    for item in data:
        if isinstance(item, dict):
            tasks.append(item)

    return tasks


def summarize_tasks(tasks: list[dict[str, object]]) -> dict[str, int]:
    done_count = 0
    todo_count = 0

    for task in tasks:
        if task.get("done", False):
            done_count += 1
        else:
            todo_count += 1

    return {
        "done": done_count,
        "todo": todo_count,
        "total": done_count + todo_count,
    }


def classify_question(question: str) -> str:
    if re.search(r"退款|退钱|退货", question):
        return "refund"

    if re.search(r"物流|快递|发货|配送", question):
        return "shipping"

    if re.search(r"发票|开票", question):
        return "invoice"

    return "other"


def main() -> None:
    print("add:", add(2, 3))
    print("clean_question:", clean_question("  Python    pytest   怎么学？  "))
    print("is_valid_order_id:", is_valid_order_id("ORD-20260705-001"))
    print("parse_score:", parse_score("0.82"))
    print("classify_question:", classify_question("我的订单怎么退款？"))


if __name__ == "__main__":
    main()
