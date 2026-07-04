def split_question_and_tags(raw_question: str) -> tuple[str, tuple[str, ...]]:
    parts = raw_question.strip().split("#")
    question = parts[0].strip()

    tags = []
    for part in parts[1:]:
        tag = part.strip()
        if tag:
            tags.append(tag)

    return question, tuple(tags)


def main() -> None:
    print("=== 1. tuple：元组 ===")
    topic = ("Python 基础", 13, "元组和集合")
    print(topic)
    print(topic[0])
    print(topic[1])
    print(topic[2])

    print("\n=== 2. 只有一个元素的 tuple ===")
    wrong_single = ("Python")
    right_single = ("Python",)
    print("wrong_single:", wrong_single, type(wrong_single))
    print("right_single:", right_single, type(right_single))

    print("\n=== 3. tuple 不可修改 ===")
    try:
        topic[1] = 14  # type: ignore[index]
    except TypeError as error:
        print("修改 tuple 会报错:", error)

    print("\n=== 4. tuple 解包 ===")
    name, lesson_number, lesson_title = topic
    print(name)
    print(lesson_number)
    print(lesson_title)

    print("\n=== 5. 函数返回多个值，本质上就是返回 tuple ===")
    question, tags = split_question_and_tags("  怎么学习 Python 集合？ #Python #set #基础  ")
    print("question:", question)
    print("tags:", tags)

    print("\n=== 6. set：集合 ===")
    skills = {"Python", "Java", "Python", "AI"}
    print(skills)
    print("Python" in skills)
    print("Go" in skills)

    print("\n=== 7. 空 dict 和空 set 的区别 ===")
    empty_dict = {}
    empty_set = set()
    print("empty_dict:", empty_dict, type(empty_dict))
    print("empty_set:", empty_set, type(empty_set))

    print("\n=== 8. set 添加和删除元素 ===")
    topics = {"变量", "函数", "类"}
    topics.add("元组")
    topics.add("集合")
    topics.discard("不存在的内容")
    print(topics)

    print("\n=== 9. set 去重 ===")
    document_ids = ["doc-1", "doc-2", "doc-1", "doc-3", "doc-2"]
    unique_document_ids = set(document_ids)
    print("原始文档 ID:", document_ids)
    print("去重后文档 ID:", sorted(unique_document_ids))

    print("\n=== 10. set 集合运算 ===")
    known_topics = {"变量", "函数", "类", "JSON"}
    required_topics = {"函数", "类", "FastAPI", "JSON"}

    print("两个集合合并:", known_topics | required_topics)
    print("两个集合共有:", known_topics & required_topics)
    print("还没学的内容:", required_topics - known_topics)

    print("\n=== 11. 权限判断 ===")
    required_permissions = {"read:docs", "call:ai"}
    user_permissions = {"read:docs", "upload:docs"}
    missing_permissions = required_permissions - user_permissions

    if missing_permissions:
        print("权限不足，缺少:", missing_permissions)
    else:
        print("权限足够，可以回答")


if __name__ == "__main__":
    main()
