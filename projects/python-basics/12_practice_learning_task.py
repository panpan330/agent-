class LearningTask:
    def __init__(self, name: str, topic: str, done: bool = False) -> None:
        self.name = name
        self.topic = topic
        self.done = done

    def mark_done(self) -> None:
        self.done = True

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "topic": self.topic,
            "done": self.done,
        }

    def __repr__(self) -> str:
        return f"LearningTask(name={self.name!r}, topic={self.topic!r}, done={self.done!r})"


def count_done_tasks(tasks: list[LearningTask]) -> int:
    count = 0
    for task in tasks:
        if task.done:
            count += 1
    return count


def tasks_to_dicts(tasks: list[LearningTask]) -> list[dict[str, object]]:
    result = []
    for task in tasks:
        result.append(task.to_dict())
    return result


def main() -> None:
    tasks = [
        LearningTask("学习变量", "Python 基础", done=True),
        LearningTask("学习函数", "Python 基础", done=True),
        LearningTask("学习 class", "Python 基础"),
    ]

    print("原始任务:")
    print(tasks)

    tasks[2].mark_done()

    print("完成数量:", count_done_tasks(tasks))
    print("字典列表:")
    print(tasks_to_dicts(tasks))


if __name__ == "__main__":
    main()
