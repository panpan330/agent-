import json
import logging
import traceback
from pathlib import Path
from typing import Any, Callable


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def divide_total(total: int, count: int) -> float:
    return total / count


def get_user_name(user: dict[str, object]) -> str:
    value = user["name"]

    if not isinstance(value, str):
        raise TypeError("name must be a string")

    return value


def parse_score(raw_score: str) -> float:
    score = float(raw_score)

    if score < 0 or score > 1:
        raise ValueError("score must be between 0 and 1")

    return score


def load_json_file(path: Path) -> object:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize_question(question: str) -> str:
    logging.debug("原始问题: %r", question)

    cleaned = question.strip()
    logging.debug("去掉左右空格后: %r", cleaned)

    normalized = " ".join(cleaned.split())
    logging.debug("压缩中间空格后: %r", normalized)

    return normalized


def build_prompt(question: str, role: str) -> str:
    logging.debug("build_prompt question=%r role=%r", question, role)
    return f"角色：{role}\n问题：{question}"


def run_case(title: str, func: Callable[[], Any]) -> None:
    print(f"\n=== {title} ===")

    try:
        result = func()
    except Exception as error:
        print("错误类型:", type(error).__name__)
        print("错误信息:", error)
        print("traceback:")
        print(traceback.format_exc())
    else:
        print("执行成功:", result)


def main() -> None:
    setup_logging()

    print("=== 1. 正常运行的代码 ===")
    print(divide_total(10, 2))
    print(get_user_name({"name": "Panpan"}))
    print(parse_score("0.82"))

    print("\n=== 2. 用 logging 观察中间过程 ===")
    question = normalize_question("   Python     traceback   怎么看？   ")
    print(build_prompt(question, role="Python 调试助手"))

    print("\n=== 3. 安全演示常见报错 ===")
    run_case("ZeroDivisionError：除数不能为 0", lambda: divide_total(10, 0))
    run_case("KeyError：字典 key 不存在", lambda: get_user_name({"age": 25}))
    run_case("ValueError：字符串不能转成合法分数", lambda: parse_score("abc"))
    run_case("ValueError：分数超出范围", lambda: parse_score("1.2"))
    run_case("FileNotFoundError：文件不存在", lambda: load_json_file(Path("data") / "missing.json"))

    print("\n=== 4. 调试时的基本顺序 ===")
    print("1. 先看最后一行错误类型和错误信息")
    print("2. 再从下往上找自己写的文件和行号")
    print("3. 回到那一行，检查变量值和数据类型")
    print("4. 用 print/logging/断点缩小问题范围")
    print("5. 修复后重新运行脚本或测试")


if __name__ == "__main__":
    main()
