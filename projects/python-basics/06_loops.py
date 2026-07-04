def main() -> None:
    print("=== 1. for 遍历列表 ===")
    tasks = ["学习变量", "学习字符串", "学习列表"]
    for task in tasks:
        print("任务:", task)

    print("\n=== 2. enumerate 带编号遍历 ===")
    for index, task in enumerate(tasks, start=1):
        print(f"{index}. {task}")

    print("\n=== 3. for 遍历字符串 ===")
    word = "Python"
    for char in word:
        print(char)

    print("\n=== 4. for 遍历字典 ===")
    user = {
        "name": "Panpan",
        "age": 25,
        "target_role": "AI 应用工程师",
    }
    for key, value in user.items():
        print(f"{key}: {value}")

    print("\n=== 5. range 生成数字序列 ===")
    for number in range(5):
        print(number)

    print("\n=== 6. range 设置开始、结束、步长 ===")
    for number in range(1, 10, 2):
        print(number)

    print("\n=== 7. continue 跳过本次循环 ===")
    topics = ["变量", "字符串", "列表", "字典", "条件判断"]
    finished_topics = ["变量", "字符串"]

    for topic in topics:
        if topic in finished_topics:
            continue
        print("还没学:", topic)

    print("\n=== 8. break 提前结束循环 ===")
    scores = [0.91, 0.82, 0.48, 0.76]
    for score in scores:
        if score < 0.5:
            print("发现低分结果，停止处理:", score)
            break
        print("处理检索结果:", score)

    print("\n=== 9. while 循环 ===")
    retry_count = 0
    max_retries = 3

    while retry_count < max_retries:
        print("第", retry_count + 1, "次尝试")
        retry_count += 1

    print("\n=== 10. 嵌套循环 ===")
    users = ["u001", "u002"]
    permissions = ["read", "write"]

    for user_id in users:
        for permission in permissions:
            print(f"user={user_id}, permission={permission}")

    print("\n=== 11. AI 应用里的批量评测例子 ===")
    test_cases = [
        {"question": "Python 列表是什么？", "expected_keyword": "多个值"},
        {"question": "字典是什么？", "expected_keyword": "键值对"},
        {"question": "条件判断有什么用？", "expected_keyword": "不同分支"},
    ]

    for case in test_cases:
        print(f"评测问题: {case['question']}")
        print(f"期望关键词: {case['expected_keyword']}")


if __name__ == "__main__":
    main()
