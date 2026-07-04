from copy import deepcopy


def get_document_score(document: dict[str, object]) -> float:
    score = document.get("score", 0.0)

    if isinstance(score, int | float):
        return float(score)

    return 0.0


def select_top_documents(
    documents: list[dict[str, object]],
    min_score: float,
    top_k: int,
) -> list[dict[str, object]]:
    valid_documents = [
        document
        for document in documents
        if get_document_score(document) >= min_score
    ]

    sorted_documents = sorted(valid_documents, key=get_document_score, reverse=True)
    return sorted_documents[:top_k]


def main() -> None:
    print("=== 1. 切片：从列表里取一段 ===")
    topics = ["变量", "字符串", "列表", "字典", "函数", "类", "集合"]
    print("前三个:", topics[:3])
    print("第 2 到第 4 个:", topics[1:4])
    print("最后两个:", topics[-2:])
    print("复制列表:", topics[:])

    print("\n=== 2. enumerate：循环时同时拿到序号和值 ===")
    for index, topic in enumerate(topics, start=1):
        print(f"第 {index} 节：{topic}")

    print("\n=== 3. zip：把两组数据配对 ===")
    questions = ["什么是 list？", "什么是 dict？", "什么是 set？"]
    answers = ["有顺序的可变数据", "key-value 数据", "不重复的数据集合"]

    for question, answer in zip(questions, answers):
        print({"question": question, "answer": answer})

    print("\n=== 4. sorted + key：按指定字段排序 ===")
    documents = [
        {"id": "doc-1", "title": "Python 变量", "score": 0.68},
        {"id": "doc-2", "title": "Python 函数", "score": 0.92},
        {"id": "doc-3", "title": "Python 集合", "score": 0.81},
        {"id": "doc-4", "title": "Java 基础", "score": 0.42},
    ]

    top_documents = select_top_documents(documents, min_score=0.7, top_k=2)
    print(top_documents)

    print("\n=== 5. 推导式：用更短的写法生成新容器 ===")
    raw_topics = ["  Python  ", "", " Java", "AI ", "python"]
    cleaned_topics = [topic.strip().lower() for topic in raw_topics if topic.strip()]
    topic_lengths = {topic: len(topic) for topic in cleaned_topics}
    unique_topics = {topic for topic in cleaned_topics}

    print("清洗后的列表:", cleaned_topics)
    print("主题长度字典:", topic_lengths)
    print("去重后的集合:", unique_topics)

    print("\n=== 6. any / all：判断一组条件 ===")
    scores = [0.91, 0.82, 0.65]
    print("是否有一个分数 >= 0.9:", any(score >= 0.9 for score in scores))
    print("是否全部分数 >= 0.6:", all(score >= 0.6 for score in scores))

    print("\n=== 7. 可变对象和不可变对象 ===")
    a = 10
    b = a
    a = a + 1
    print("数字不可变:", a, b)

    skills_a = ["Python", "Java"]
    skills_b = skills_a
    skills_a.append("AI")
    print("列表可变:", skills_a, skills_b)

    skills_c = skills_a.copy()
    skills_c.append("FastAPI")
    print("复制后的列表:", skills_a, skills_c)

    print("\n=== 8. 浅拷贝和深拷贝 ===")
    learning_plan = {
        "title": "Python 基础",
        "tasks": [
            {"name": "学习列表", "done": True},
            {"name": "学习字典", "done": False},
        ],
    }

    shallow_plan = learning_plan.copy()
    shallow_plan["tasks"][1]["done"] = True  # type: ignore[index]
    print("浅拷贝会影响内部嵌套对象:")
    print("learning_plan:", learning_plan)
    print("shallow_plan:", shallow_plan)

    safe_plan = deepcopy(learning_plan)
    safe_plan["tasks"][0]["done"] = False  # type: ignore[index]
    print("深拷贝不会影响原对象:")
    print("learning_plan:", learning_plan)
    print("safe_plan:", safe_plan)


if __name__ == "__main__":
    main()
