from typing import Any, Callable


def parse_positive_int(value: object) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError("value must be an integer") from error

    if number <= 0:
        raise ValueError("value must be positive")

    return number


def get_required_field(data: dict[str, object], key: str) -> object:
    if key not in data:
        raise KeyError(f"missing required field: {key}")

    return data[key]


def calculate_average(numbers: list[float]) -> float:
    if not numbers:
        raise ValueError("numbers must not be empty")

    return sum(numbers) / len(numbers)


def normalize_user(user: dict[str, object]) -> dict[str, object]:
    name = get_required_field(user, "name")
    age = get_required_field(user, "age")

    if not isinstance(name, str) or not name.strip():
        raise ValueError("name must be a non-empty string")

    parsed_age = parse_positive_int(age)

    return {
        "name": name.strip(),
        "age": parsed_age,
    }


def safe_run(case_name: str, func: Callable[[], object]) -> dict[str, object]:
    try:
        result = func()
    except Exception as error:
        return {
            "case_name": case_name,
            "ok": False,
            "error_type": type(error).__name__,
            "error_message": str(error),
        }

    return {
        "case_name": case_name,
        "ok": True,
        "result": result,
    }


def main() -> None:
    cases = [
        ("正常用户", lambda: normalize_user({"name": " Panpan ", "age": "25"})),
        ("缺少 name", lambda: normalize_user({"age": 25})),
        ("age 不是数字", lambda: normalize_user({"name": "Panpan", "age": "abc"})),
        ("空列表平均值", lambda: calculate_average([])),
        ("正常平均值", lambda: calculate_average([0.8, 0.9, 1.0])),
    ]

    for case_name, func in cases:
        print(safe_run(case_name, func))


if __name__ == "__main__":
    main()
