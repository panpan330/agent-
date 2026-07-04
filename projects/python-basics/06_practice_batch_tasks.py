def main() -> None:
    tasks = [
        {"name": "学习变量", "done": True, "important": False},
        {"name": "学习字符串", "done": True, "important": False},
        {"name": "学习列表", "done": True, "important": False},
        {"name": "学习字典", "done": True, "important": False},
        {"name": "学习条件判断", "done": True, "important": False},
        {"name": "学习循环", "done": False, "important": False},
        {"name": "学习函数", "done": False, "important": True},
        {"name": "学习异常处理", "done": False, "important": False},
    ]

    unfinished_count = 0

    print("全部任务:")
    for index, task in enumerate(tasks, start=1):
        print(f"{index}. {task['name']} done={task['done']} important={task['important']}")

    print("\n未完成任务:")
    for task in tasks:
        if task["done"]:
            continue

        unfinished_count += 1
        print("-", task["name"])

        if task["important"]:
            print("遇到重要任务，先停下来重点学习:", task["name"])
            break

    print("\n已统计到的未完成任务数量:", unfinished_count)

    print("\n模拟批量评测:")
    test_cases = [
        {"question": "列表是什么？", "answer": "列表是保存多个值的容器", "keyword": "多个值"},
        {"question": "字典是什么？", "answer": "字典保存键值对", "keyword": "键值对"},
        {"question": "循环是什么？", "answer": "循环可以重复处理数据", "keyword": "重复"},
    ]

    passed_count = 0
    for case in test_cases:
        if case["keyword"] in case["answer"]:
            passed_count += 1
            print("通过:", case["question"])
        else:
            print("失败:", case["question"])

    print("通过数量:", passed_count)
    print("总数量:", len(test_cases))


if __name__ == "__main__":
    main()
