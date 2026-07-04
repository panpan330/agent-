def main() -> None:
    print("=== 1. 最基本的 if ===")
    age = 18
    if age >= 18:
        print("成年人")

    print("\n=== 2. if / else ===")
    question = "怎么学习 Python？"
    if question:
        print("用户问题:", question)
    else:
        print("问题不能为空")

    print("\n=== 3. if / elif / else ===")
    score = 82
    if score >= 90:
        print("优秀")
    elif score >= 60:
        print("及格")
    else:
        print("不及格")

    print("\n=== 4. 比较运算符 ===")
    temperature = 0.7
    print("temperature == 0.7:", temperature == 0.7)
    print("temperature != 1.0:", temperature != 1.0)
    print("temperature < 1.0:", temperature < 1.0)

    print("\n=== 5. and / or / not ===")
    is_logged_in = True
    has_permission = False

    if is_logged_in and has_permission:
        print("可以访问知识库")
    else:
        print("不能访问知识库")

    if is_logged_in or has_permission:
        print("至少满足一个条件")

    if not has_permission:
        print("没有权限")

    print("\n=== 6. 空字符串、空列表、None 的判断 ===")
    empty_question = ""
    chunks = []
    user = None

    if not empty_question:
        print("empty_question 是空字符串")

    if not chunks:
        print("chunks 是空列表")

    if user is None:
        print("user 是 None")

    print("\n=== 7. 字符串和列表里的判断 ===")
    user_question = "我想学习 Python 和 AI"
    finished_topics = ["变量", "字符串", "列表", "字典"]

    if "Python" in user_question:
        print("问题里提到了 Python")

    if "字典" in finished_topics:
        print("已经学过字典")

    print("\n=== 8. 字典字段判断 ===")
    request = {
        "user_id": "u001",
        "question": "怎么学习 LangChain？",
        "has_permission": True,
    }

    if request.get("question") and request.get("has_permission"):
        print("问题有效，并且用户有权限")

    print("\n=== 9. AI 应用里的拒答判断 ===")
    retrieval_score = 0.42
    if retrieval_score < 0.5:
        print("没有找到足够可靠的资料，应该拒答或提示用户补充信息")
    else:
        print("可以基于检索结果回答")


if __name__ == "__main__":
    main()
