def main() -> None:
    print("=== 1. 字典是什么 ===")
    user = {
        "name": "Panpan",
        "age": 25,
        "target_role": "AI 应用工程师",
    }
    print(user)
    print(type(user))

    print("\n=== 2. 读取字段 ===")
    print("name:", user["name"])
    print("age:", user["age"])

    print("\n=== 3. 修改字段 ===")
    user["age"] = 26
    print(user)

    print("\n=== 4. 添加字段 ===")
    user["city"] = "Shanghai"
    user["is_learning_ai"] = True
    print(user)

    print("\n=== 5. 删除字段 ===")
    removed_city = user.pop("city")
    print("removed_city:", removed_city)
    print(user)

    print("\n=== 6. get 安全读取 ===")
    print("email:", user.get("email"))
    print("email with default:", user.get("email", "未填写邮箱"))

    print("\n=== 7. keys / values / items ===")
    print("keys:", list(user.keys()))
    print("values:", list(user.values()))
    print("items:", list(user.items()))

    print("\n=== 8. 遍历字典 ===")
    for key, value in user.items():
        print(f"{key}: {value}")

    print("\n=== 9. 字典里放列表 ===")
    user["skills"] = ["Java", "Python", "FastAPI"]
    print(user)
    print("第一个技能:", user["skills"][0])

    print("\n=== 10. 嵌套字典 ===")
    profile = {
        "user": {
            "name": "Panpan",
            "age": 25,
        },
        "learning": {
            "current_topic": "dict",
            "finished_topics": ["variables", "strings", "lists"],
        },
    }
    print(profile)
    print("用户名:", profile["user"]["name"])
    print("当前主题:", profile["learning"]["current_topic"])

    print("\n=== 11. AI 应用里的字典例子 ===")
    chat_request = {
        "model": "gpt-example",
        "messages": [
            {"role": "system", "content": "你是一个 Python 老师"},
            {"role": "user", "content": "请解释字典"},
        ],
        "temperature": 0.7,
        "stream": False,
    }
    print(chat_request)
    print("第一条消息角色:", chat_request["messages"][0]["role"])
    print("第二条消息内容:", chat_request["messages"][1]["content"])


if __name__ == "__main__":
    main()
