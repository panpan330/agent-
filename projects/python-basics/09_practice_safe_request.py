import requests


def safe_int(value: str, default: int = 0) -> int:
    try:
        return int(value)
    except ValueError:
        return default


def safe_get(data: dict, key: str, default: str = "") -> str:
    try:
        return data[key]
    except KeyError:
        return default


def validate_question(question: str) -> None:
    question = question.strip()
    if not question:
        raise ValueError("问题不能为空")
    if len(question) < 5:
        raise ValueError("问题太短")


def safe_fetch(url: str) -> dict:
    try:
        response = requests.get(url, timeout=5)
        return {
            "ok": True,
            "status_code": response.status_code,
            "error": None,
        }
    except requests.RequestException as error:
        return {
            "ok": False,
            "status_code": None,
            "error": str(error),
        }


def process_request(request: dict) -> dict:
    question = safe_get(request, "question", "").strip()
    age = safe_int(str(request.get("age", "0")))

    try:
        validate_question(question)
    except ValueError as error:
        return {
            "valid": False,
            "reason": str(error),
            "question": question,
            "age": age,
        }

    return {
        "valid": True,
        "reason": None,
        "question": question,
        "age": age,
    }


def main() -> None:
    requests_to_check = [
        {"question": " 我想学习 Python 异常处理 ", "age": "25"},
        {"question": "hi", "age": "abc"},
        {"age": "30"},
    ]

    for request in requests_to_check:
        print(process_request(request))

    print(safe_fetch("https://httpbin.org/get"))


if __name__ == "__main__":
    main()
