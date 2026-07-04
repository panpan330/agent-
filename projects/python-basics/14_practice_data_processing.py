from copy import deepcopy


def clean_topics(raw_topics: list[str]) -> list[str]:
    return [topic.strip().lower() for topic in raw_topics if topic.strip()]


def number_topics(topics: list[str]) -> list[str]:
    result = []

    for index, topic in enumerate(topics, start=1):
        result.append(f"{index}. {topic}")

    return result


def pair_questions_and_answers(
    questions: list[str],
    answers: list[str],
) -> list[dict[str, str]]:
    pairs = []

    for question, answer in zip(questions, answers):
        pairs.append(
            {
                "question": question,
                "answer": answer,
            }
        )

    return pairs


def get_score(document: dict[str, object]) -> float:
    score = document.get("score", 0.0)

    if isinstance(score, int | float):
        return float(score)

    return 0.0


def filter_and_sort_documents(
    documents: list[dict[str, object]],
    min_score: float,
    top_k: int,
) -> list[dict[str, object]]:
    valid_documents = [
        document
        for document in documents
        if get_score(document) >= min_score
    ]

    sorted_documents = sorted(valid_documents, key=get_score, reverse=True)
    return sorted_documents[:top_k]


def collect_sources(documents: list[dict[str, object]]) -> set[str]:
    sources = set()

    for document in documents:
        source = document.get("source")
        if isinstance(source, str) and source:
            sources.add(source)

    return sources


def update_task_safely(plan: dict[str, object], task_index: int, done: bool) -> dict[str, object]:
    new_plan = deepcopy(plan)
    tasks = new_plan.get("tasks", [])

    if isinstance(tasks, list) and 0 <= task_index < len(tasks):
        task = tasks[task_index]
        if isinstance(task, dict):
            task["done"] = done

    return new_plan


def main() -> None:
    raw_topics = ["  Python  ", "", "Java", " AI ", "python"]
    topics = clean_topics(raw_topics)
    print("清洗后的主题:", topics)
    print("编号后的主题:", number_topics(topics))

    questions = ["什么是列表？", "什么是字典？", "什么是集合？"]
    answers = ["保存一组数据", "保存 key-value", "保存不重复数据"]
    print("问答配对:", pair_questions_and_answers(questions, answers))

    documents = [
        {"id": "doc-1", "source": "python.md", "score": 0.91},
        {"id": "doc-2", "source": "java.md", "score": 0.43},
        {"id": "doc-3", "source": "python.md", "score": 0.82},
        {"id": "doc-4", "source": "ai.md", "score": 0.76},
    ]
    top_documents = filter_and_sort_documents(documents, min_score=0.7, top_k=2)
    print("top 文档:", top_documents)
    print("来源集合:", sorted(collect_sources(top_documents)))

    plan = {
        "title": "Python 基础",
        "tasks": [
            {"name": "学习数据处理", "done": False},
            {"name": "学习 pytest", "done": False},
        ],
    }
    new_plan = update_task_safely(plan, task_index=0, done=True)
    print("原计划:", plan)
    print("新计划:", new_plan)


if __name__ == "__main__":
    main()
