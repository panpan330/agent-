def clean_question(question: str) -> str:
    return question.strip()


def is_valid_question(question: str) -> bool:
    return len(question) >= 5


def contains_keyword(question: str, keyword: str) -> bool:
    return keyword.lower() in question.lower()


def build_prompt(question: str, role: str = "Python 学习助手") -> str:
    return f"""你是一个{role}。
用户问题：{question}
请按“概念、例子、练习”的结构回答。"""


if __name__ == "__main__":
    demo_question = "  我想学习 Python import  "
    cleaned = clean_question(demo_question)
    print("清洗后:", cleaned)
    print("是否有效:", is_valid_question(cleaned))
    print("是否包含 Python:", contains_keyword(cleaned, "Python"))
    print(build_prompt(cleaned))
