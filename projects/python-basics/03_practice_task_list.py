def main() -> None:
    tasks = ["学习变量", "学习字符串", "学习列表"]

    print("初始任务:", tasks)

    tasks.append("学习字典")
    tasks.append("学习函数")
    print("添加任务后:", tasks)

    tasks.remove("学习字符串")
    print("删除学习字符串后:", tasks)

    finished_task = tasks.pop(0)
    print("完成的任务:", finished_task)
    print("剩余任务:", tasks)

    print("任务数量:", len(tasks))
    print("是否包含学习列表:", "学习列表" in tasks)
    print("是否包含学习 FastAPI:", "学习 FastAPI" in tasks)

    print("前两个任务:", tasks[0:2])

    print("带编号的任务列表:")
    for index, task in enumerate(tasks, start=1):
        print(f"{index}. {task}")


if __name__ == "__main__":
    main()
