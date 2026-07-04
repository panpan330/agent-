import datetime
import json

import requests

import question_utils
from question_utils import build_prompt, clean_question
from question_utils import contains_keyword as has_keyword


def main() -> None:
    print("=== 1. 导入标准库 ===")
    now = datetime.datetime.now()
    print("当前时间:", now)

    data = {
        "name": "Panpan",
        "topic": "import",
    }
    json_text = json.dumps(data, ensure_ascii=False)
    print("字典转 JSON 字符串:", json_text)

    print("\n=== 2. 导入第三方库 ===")
    try:
        response = requests.get("https://httpbin.org/get", timeout=5)
        print("HTTP 状态码:", response.status_code)
    except requests.RequestException as error:
        print("请求失败，但 requests 已成功导入:", error)

    print("\n=== 3. 导入自己写的模块 ===")
    raw_question = "   我想学习 Python 模块导入   "

    cleaned_1 = question_utils.clean_question(raw_question)
    print("通过模块名调用:", cleaned_1)

    cleaned_2 = clean_question(raw_question)
    print("直接导入函数调用:", cleaned_2)

    print("是否包含 Python:", has_keyword(cleaned_2, "Python"))

    prompt = build_prompt(cleaned_2, role="Python 基础老师")
    print("prompt:")
    print(prompt)


if __name__ == "__main__":
    main()
