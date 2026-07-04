def say_hello() -> None:
    print("Hello, Python")


def greet(name: str) -> None:
    print(f"你好，{name}")


def add(a: int, b: int) -> int:
    return a + b


def clean_question(question: str) -> str:
    return question.strip().lower()


def is_valid_question(question: str) -> bool:
    return len(question) >= 5


def build_prompt(question: str, topic: str = "Python") -> str:
    return f"""你是一个{topic}学习助手。
用户问题：{question}
请用零基础能听懂的方式回答。"""


def check_retrieval_score(score: float, threshold: float = 0.5) -> str:
    if score < threshold:
        return "检索结果不可靠，应该拒答或让用户补充信息"
    return "检索结果可用，可以谨慎回答"


def process_question(raw_question: str, topic: str = "Python") -> dict:
    question = clean_question(raw_question)
    valid = is_valid_question(question)

    if not valid:
        return {
            "valid": False,
            "reason": "问题太短",
            "question": question,
            "prompt": None,
        }

    prompt = build_prompt(question=question, topic=topic)
    return {
        "valid": True,
        "reason": None,
        "question": question,
        "prompt": prompt,
    }


def main() -> None:
    print("=== 1. 最简单的函数 ===")
    say_hello()

    print("\n=== 2. 带参数的函数 ===")
    greet("Panpan")

    print("\n=== 3. 有返回值的函数 ===")
    result = add(3, 5)
    print("3 + 5 =", result)

    print("\n=== 4. 清洗问题 ===")
    raw_question = "   HOW to learn Python functions?   "
    cleaned_question = clean_question(raw_question)
    print("原始问题:", repr(raw_question))
    print("清洗后:", cleaned_question)

    print("\n=== 5. 默认参数和关键字参数 ===")
    prompt = build_prompt(question=cleaned_question, topic="Python 函数")
    print(prompt)

    print("\n=== 6. 检查检索分数 ===")
    print(check_retrieval_score(0.42))
    print(check_retrieval_score(0.82, threshold=0.7))

    print("\n=== 7. 函数调用函数 ===")
    processed = process_question("  我想学习 Python 函数  ", topic="Python 函数")
    print(processed)

    short_processed = process_question(" hi ")
    print(short_processed)


if __name__ == "__main__":
    main()
