import requests


def parse_age(age_text: str) -> int:
    try:
        return int(age_text)
    except ValueError:
        print(f"年龄格式不正确: {age_text}")
        return 0


def get_user_name(user: dict) -> str:
    try:
        return user["name"]
    except KeyError:
        return "未知用户"


def get_first_item(items: list) -> str | None:
    try:
        return items[0]
    except IndexError:
        print("列表为空，无法取第一个元素")
        return None


def fetch_status(url: str) -> int | None:
    try:
        response = requests.get(url, timeout=5)
        return response.status_code
    except requests.RequestException as error:
        print("请求失败:", error)
        return None


def validate_question(question: str) -> None:
    if not question.strip():
        raise ValueError("问题不能为空")

    if len(question.strip()) < 5:
        raise ValueError("问题太短")


def main() -> None:
    print("=== 1. 捕获 ValueError ===")
    print(parse_age("25"))
    print(parse_age("abc"))

    print("\n=== 2. 捕获 KeyError ===")
    user = {"age": 25}
    print(get_user_name(user))

    print("\n=== 3. 捕获 IndexError ===")
    print(get_first_item([]))
    print(get_first_item(["Python", "FastAPI"]))

    print("\n=== 4. 捕获网络请求异常 ===")
    print(fetch_status("https://httpbin.org/get"))

    print("\n=== 5. try / except / else / finally ===")
    number_text = "100"
    try:
        number = int(number_text)
    except ValueError:
        print("转换失败")
    else:
        print("转换成功:", number)
    finally:
        print("无论成功失败，finally 都会执行")

    print("\n=== 6. 主动 raise 异常 ===")
    questions = ["", "hi", "我想学习 Python 异常处理"]
    for question in questions:
        try:
            validate_question(question)
            print("问题有效:", question)
        except ValueError as error:
            print("问题无效:", error)


if __name__ == "__main__":
    main()
