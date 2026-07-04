def main() -> None:
    request = {
        "user_id": "u001",
        "question": "  我想学习 Python 条件判断  ",
        "has_permission": True,
        "finished_topics": ["变量", "字符串", "列表", "字典"],
    }

    raw_question = request.get("question", "")
    question = raw_question.strip()
    has_permission = request.get("has_permission", False)
    finished_topics = request.get("finished_topics", [])

    if not question:
        print("问题不能为空")
    elif len(question) < 5:
        print("问题太短，请补充更多信息")
    elif not has_permission:
        print("用户没有权限提问")
    else:
        print("问题检查通过")
        print("清洗后的问题:", question)

        if "Python" in question:
            print("问题和 Python 有关")

        if "条件判断" in question:
            print("问题和条件判断有关")

        if "字典" in finished_topics and "列表" in finished_topics:
            print("已经具备学习条件判断的前置基础")
        else:
            print("建议先复习列表和字典")

    retrieval_score = 0.68
    if retrieval_score >= 0.8:
        print("检索结果很可靠，可以直接回答")
    elif retrieval_score >= 0.5:
        print("检索结果一般，回答时要谨慎并提示来源")
    else:
        print("检索结果不可靠，应该拒答或让用户补充信息")


if __name__ == "__main__":
    main()
