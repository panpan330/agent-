import json
import re
from pathlib import Path


def normalize_tags(raw_tags: list[str]) -> list[str]:
    result = []

    for raw_tag in raw_tags:
        tag = raw_tag.strip().lower()
        if tag and tag not in result:
            result.append(tag)

    return result


def require_order_id(text: str) -> str:
    match = re.search(r"ORD-\d{8}-\d{3}", text)

    if match is None:
        raise ValueError("order id is required")

    return match.group()


def build_report(user_name: str, tags: list[str], order_id: str) -> dict[str, object]:
    if not user_name.strip():
        raise ValueError("user_name is required")

    return {
        "user_name": user_name.strip(),
        "tags": normalize_tags(tags),
        "order_id": order_id,
    }


def save_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)


def load_report(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("report json must be an object")

    return data
