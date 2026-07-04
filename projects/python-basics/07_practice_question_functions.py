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


def check_score(score: float, threshold: float = 0.5) -> dict:
    if score < threshold:
        return {
            "can_answer": False,
            "reason": "检索分数太低",
        }

    return {
        "can_answer": True,
        "reason": "检索分数可用",
    }


def process_user_question(raw_question: str, score: float) -> dict:
    question = clean_question(raw_question)

    if not is_valid_question(question):
        return {
            "valid": False,
            "reason": "问题不能为空或太短",
            "question": question,
        }

    score_result = check_score(score)
    if not score_result["can_answer"]:
        return {
            "valid": False,
            "reason": score_result["reason"],
            "question": question,
        }

    return {
        "valid": True,
        "reason": None,
        "question": question,
        "contains_python": contains_keyword(question, "Python"),
        "prompt": build_prompt(question),
    }


def main() -> None:
    result = process_user_question("   我想学习 Python 函数   ", 0.82)
    print(result)

    short_result = process_user_question(" hi ", 0.82)
    print(short_result)

    low_score_result = process_user_question("我想学习 Python 函数", 0.32)
    print(low_score_result)


if __name__ == "__main__":
    main()
