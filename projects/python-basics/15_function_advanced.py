from collections.abc import Callable


def build_prompt(question: str, *, role: str = "Python 学习助手", max_lines: int = 3) -> str:
    return f"""角色：{role}
用户问题：{question}
要求：最多回答 {max_lines} 行。"""


def merge_keywords(*keywords: str) -> list[str]:
    result = []

    for keyword in keywords:
        cleaned_keyword = keyword.strip().lower()
        if cleaned_keyword and cleaned_keyword not in result:
            result.append(cleaned_keyword)

    return result


def build_ai_request(question: str, **metadata: object) -> dict[str, object]:
    return {
        "question": question,
        "metadata": metadata,
    }


def add_tag_wrong(tag: str, tags: list[str] = []) -> list[str]:
    tags.append(tag)
    return tags


def add_tag_safe(tag: str, tags: list[str] | None = None) -> list[str]:
    if tags is None:
        tags = []

    tags.append(tag)
    return tags


def clean_question(question: str) -> str:
    return question.strip()


def lower_question(question: str) -> str:
    return question.lower()


def apply_to_questions(
    questions: list[str],
    processor: Callable[[str], str],
) -> list[str]:
    result = []

    for question in questions:
        result.append(processor(question))

    return result


def make_keyword_checker(keyword: str) -> Callable[[str], bool]:
    def checker(text: str) -> bool:
        return keyword.lower() in text.lower()

    return checker


def print_before_and_after(func: Callable[[str], str]) -> Callable[[str], str]:
    def wrapper(question: str) -> str:
        print("准备调用函数，原始问题:", question)
        result = func(question)
        print("函数调用结束，处理结果:", result)
        return result

    return wrapper


@print_before_and_after
def clean_question_with_log(question: str) -> str:
    return question.strip()


def main() -> None:
    print("=== 1. 关键字专用参数 ===")
    prompt = build_prompt("什么是函数进阶？", role="AI 学习助手", max_lines=2)
    print(prompt)

    print("\n=== 2. *args：接收任意数量的位置参数 ===")
    keywords = merge_keywords(" Python ", "AI", "python", "FastAPI", "")
    print(keywords)

    print("\n=== 3. **kwargs：接收任意数量的关键字参数 ===")
    request = build_ai_request(
        "怎么学习函数进阶？",
        source="lesson-15",
        stream=False,
        user_id=330,
    )
    print(request)

    print("\n=== 4. 解包调用函数 ===")
    raw_keywords = ["Python", "LangChain", "RAG"]
    print(merge_keywords(*raw_keywords))

    metadata = {"source": "local-note", "topic": "function-advanced"}
    print(build_ai_request("什么是 **kwargs？", **metadata))

    print("\n=== 5. 默认参数的坑 ===")
    print(add_tag_wrong("python"))
    print(add_tag_wrong("ai"))
    print("第二次调用时，旧数据还在，这就是坑")

    print(add_tag_safe("python"))
    print(add_tag_safe("ai"))
    print("安全写法每次都会创建新的列表")

    print("\n=== 6. lambda：临时小函数 ===")
    documents = [
        {"id": "doc-1", "score": 0.72},
        {"id": "doc-2", "score": 0.95},
        {"id": "doc-3", "score": 0.81},
    ]
    sorted_documents = sorted(documents, key=lambda document: document["score"], reverse=True)
    print(sorted_documents)

    print("\n=== 7. 函数可以作为参数传给另一个函数 ===")
    questions = ["  Python 是什么？  ", "  函数怎么学？  "]
    print(apply_to_questions(questions, clean_question))
    print(apply_to_questions(questions, lower_question))

    print("\n=== 8. 函数可以返回函数 ===")
    contains_python = make_keyword_checker("Python")
    print(contains_python("我正在学习 Python"))
    print(contains_python("我正在学习 Java"))

    print("\n=== 9. 装饰器：在不改原函数代码的情况下增强函数 ===")
    clean_question_with_log("   什么是装饰器？   ")


if __name__ == "__main__":
    main()
