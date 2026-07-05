from collections.abc import Callable


def merge_tags(*tags: str) -> list[str]:
    result = []

    for tag in tags:
        cleaned_tag = tag.strip().lower()
        if cleaned_tag and cleaned_tag not in result:
            result.append(cleaned_tag)

    return result


def build_chat_request(
    question: str,
    *,
    stream: bool = False,
    **metadata: object,
) -> dict[str, object]:
    return {
        "question": question,
        "stream": stream,
        "metadata": metadata,
    }


def append_history_safe(message: str, history: list[str] | None = None) -> list[str]:
    if history is None:
        history = []

    history.append(message)
    return history


def apply_processor(items: list[str], processor: Callable[[str], str]) -> list[str]:
    result = []

    for item in items:
        result.append(processor(item))

    return result


def clean_text(text: str) -> str:
    return text.strip()


def make_min_score_filter(min_score: float) -> Callable[[dict[str, object]], bool]:
    def checker(document: dict[str, object]) -> bool:
        score = document.get("score", 0.0)
        if not isinstance(score, int | float):
            return False
        return float(score) >= min_score

    return checker


def log_call(func: Callable[[str], str]) -> Callable[[str], str]:
    def wrapper(text: str) -> str:
        print("调用前:", text)
        result = func(text)
        print("调用后:", result)
        return result

    return wrapper


@log_call
def clean_text_with_log(text: str) -> str:
    return text.strip()


def main() -> None:
    tags = merge_tags(" Python ", "AI", "python", " FastAPI ", "")
    print("标签:", tags)

    request = build_chat_request(
        "怎么学习函数进阶？",
        stream=True,
        source="lesson-15",
        user_id=330,
    )
    print("请求:", request)

    print("历史 1:", append_history_safe("你好"))
    print("历史 2:", append_history_safe("继续学习"))

    raw_questions = ["  什么是 *args？  ", "  什么是 **kwargs？  "]
    cleaned_questions = apply_processor(raw_questions, clean_text)
    print("清洗后的问题:", cleaned_questions)

    documents = [
        {"id": "doc-1", "score": 0.91},
        {"id": "doc-2", "score": 0.45},
        {"id": "doc-3", "score": 0.78},
    ]
    high_score_filter = make_min_score_filter(0.7)
    high_score_documents = [document for document in documents if high_score_filter(document)]
    print("高分文档:", high_score_documents)

    clean_text_with_log("   装饰器会在函数前后加逻辑   ")


if __name__ == "__main__":
    main()
