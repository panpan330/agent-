from typing import Any


def greet(name: str) -> str:
    return f"你好，{name}"


def add(a: int, b: int) -> int:
    return a + b


def get_first_topic(topics: list[str]) -> str | None:
    if not topics:
        return None
    return topics[0]


def build_user(name: str, age: int, skills: list[str]) -> dict[str, object]:
    return {
        "name": name,
        "age": age,
        "skills": skills,
    }


def build_ai_request(question: str, metadata: dict[str, str] | None = None) -> dict[str, object]:
    if metadata is None:
        metadata = {}

    return {
        "question": question,
        "metadata": metadata,
        "stream": False,
    }


def print_anything(value: Any) -> None:
    print("value:", value)
    print("type:", type(value))


def main() -> None:
    print("=== 1. 变量类型提示 ===")
    name: str = "Panpan"
    age: int = 25
    height: float = 1.75
    is_learning_ai: bool = True

    print(name, age, height, is_learning_ai)

    print("\n=== 2. 函数参数和返回值类型提示 ===")
    print(greet(name))
    print(add(3, 5))

    print("\n=== 3. list[str] ===")
    topics: list[str] = ["变量", "字符串", "列表"]
    print(get_first_topic(topics))
    print(get_first_topic([]))

    print("\n=== 4. dict[str, object] ===")
    user = build_user("Panpan", 25, ["Java", "Python"])
    print(user)

    print("\n=== 5. str | None 和 dict[str, str] | None ===")
    request = build_ai_request(
        question="怎么学习 Python 类型提示？",
        metadata={"source": "python-basics", "topic": "type hints"},
    )
    print(request)

    print("\n=== 6. Any 表示任意类型 ===")
    print_anything("hello")
    print_anything(123)
    print_anything({"name": "Panpan"})

    print("\n=== 7. 类型提示不会自动校验 ===")
    wrong_result = add("3", "5")  # type: ignore[arg-type]
    print("wrong_result:", wrong_result)


if __name__ == "__main__":
    main()
