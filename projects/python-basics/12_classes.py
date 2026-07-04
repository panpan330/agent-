class LearningTask:
    def __init__(self, name: str, done: bool = False) -> None:
        self.name = name
        self.done = done

    def mark_done(self) -> None:
        self.done = True

    def is_done(self) -> bool:
        return self.done

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "done": self.done,
        }

    def __repr__(self) -> str:
        return f"LearningTask(name={self.name!r}, done={self.done!r})"


class ChatMessage:
    def __init__(self, role: str, content: str) -> None:
        self.role = role
        self.content = content

    def to_dict(self) -> dict[str, str]:
        return {
            "role": self.role,
            "content": self.content,
        }

    def __repr__(self) -> str:
        return f"ChatMessage(role={self.role!r}, content={self.content!r})"


def main() -> None:
    print("=== 1. 创建对象 ===")
    task = LearningTask("学习 class")
    print(task)
    print(task.name)
    print(task.done)

    print("\n=== 2. 调用方法 ===")
    print("完成了吗:", task.is_done())
    task.mark_done()
    print("完成了吗:", task.is_done())

    print("\n=== 3. 对象转字典 ===")
    print(task.to_dict())

    print("\n=== 4. 多个对象放进列表 ===")
    tasks = [
        LearningTask("学习变量", done=True),
        LearningTask("学习函数", done=True),
        LearningTask("学习 class"),
    ]

    for item in tasks:
        print(item.to_dict())

    print("\n=== 5. 类和字典的区别 ===")
    task_dict = {"name": "学习字典形式任务", "done": False}
    task_object = LearningTask("学习对象形式任务")
    print(task_dict["name"])
    print(task_object.name)

    print("\n=== 6. AI 消息对象 ===")
    messages = [
        ChatMessage("system", "你是一个 Python 老师"),
        ChatMessage("user", "请解释 class"),
    ]

    message_dicts = []
    for message in messages:
        message_dicts.append(message.to_dict())

    print(message_dicts)


if __name__ == "__main__":
    main()
