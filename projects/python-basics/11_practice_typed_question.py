def clean_question(question: str) -> str:
    return question.strip()


def is_valid_question(question: str) -> bool:
    return len(question) >= 5


def build_metadata(source: str, topic: str) -> dict[str, str]:
    return {
        "source": source,
        "topic": topic,
    }


def build_prompt(question: str, role: str = "Python 学习助手") -> str:
    return f"""你是一个{role}。
用户问题：{question}
请用零基础能理解的方式回答。"""


def process_question(raw_question: str, metadata: dict[str, str] | None = None) -> dict[str, object]:
    question = clean_question(raw_question)

    if metadata is None:
        metadata = {}

    if not is_valid_question(question):
        return {
            "valid": False,
            "question": question,
            "reason": "问题不能为空或太短",
            "metadata": metadata,
            "prompt": None,
        }

    return {
        "valid": True,
        "question": question,
        "reason": None,
        "metadata": metadata,
        "prompt": build_prompt(question),
    }


def main() -> None:
    metadata = build_metadata(source="python-basics", topic="type hints")

    result = process_question("  我想学习 Python 类型提示  ", metadata)
    print(result)

    invalid_result = process_question(" hi ")
    print(invalid_result)


if __name__ == "__main__":
    main()
