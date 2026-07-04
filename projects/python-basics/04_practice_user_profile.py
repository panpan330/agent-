def main() -> None:
    user = {
        "name": "Panpan",
        "age": 25,
        "skills": ["Java", "Python"],
    }

    print("原始用户:", user)

    print("姓名:", user["name"])
    print("年龄:", user["age"])
    print("技能:", user["skills"])

    user["age"] = 26
    user["target_role"] = "AI 应用工程师"
    user["skills"].append("FastAPI")

    print("更新后的用户:", user)

    email = user.get("email", "未填写邮箱")
    print("邮箱:", email)

    print("用户字段:")
    for key, value in user.items():
        print(f"{key}: {value}")

    ai_request = {
        "user_id": "u001",
        "question": "我应该怎么学习 Python 字典？",
        "metadata": {
            "source": "python-basics",
            "topic": "dict",
            "level": "beginner",
        },
    }

    print("AI 请求体:", ai_request)
    print("问题:", ai_request["question"])
    print("主题:", ai_request["metadata"]["topic"])


if __name__ == "__main__":
    main()
