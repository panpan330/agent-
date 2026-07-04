def main() -> None:
    print("=== 1. 列表是什么 ===")
    tasks = ["学习变量", "学习字符串", "学习列表"]
    print(tasks)
    print(type(tasks))

    print("\n=== 2. 访问列表元素 ===")
    print("第 1 个任务:", tasks[0])
    print("第 2 个任务:", tasks[1])
    print("最后一个任务:", tasks[-1])

    print("\n=== 3. 修改列表元素 ===")
    tasks[0] = "复习变量和类型"
    print(tasks)

    print("\n=== 4. 添加元素 append ===")
    tasks.append("学习字典")
    print(tasks)

    print("\n=== 5. 删除元素 remove / pop ===")
    tasks.remove("学习字符串")
    print("remove 后:", tasks)

    last_task = tasks.pop()
    print("pop 取出的任务:", last_task)
    print("pop 后:", tasks)

    print("\n=== 6. 列表长度 len ===")
    print("任务数量:", len(tasks))

    print("\n=== 7. 遍历列表 for ===")
    for task in tasks:
        print("待办:", task)

    print("\n=== 8. 带编号遍历 enumerate ===")
    for index, task in enumerate(tasks, start=1):
        print(f"{index}. {task}")

    print("\n=== 9. 判断元素是否存在 in ===")
    print("学习列表" in tasks)
    print("学习 FastAPI" in tasks)

    print("\n=== 10. 切片 ===")
    ai_steps = ["Python 基础", "FastAPI", "LangChain", "RAG", "LangGraph"]
    print("全部:", ai_steps)
    print("前两个:", ai_steps[0:2])
    print("从第 3 个到最后:", ai_steps[2:])
    print("最后两个:", ai_steps[-2:])

    print("\n=== 11. 列表里可以放不同类型，但不建议乱放 ===")
    mixed = ["Panpan", 25, True, None]
    print(mixed)

    print("\n=== 12. AI 应用里的列表例子 ===")
    messages = [
        "system: 你是一个 Python 老师",
        "user: 请解释列表",
        "assistant: 列表是按顺序保存多个值的容器",
    ]

    for message in messages:
        print(message)


if __name__ == "__main__":
    main()
