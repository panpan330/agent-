def main() -> None:
    name = "Panpan"
    age = 25
    height = 1.75
    is_learning_ai = True
    target_role = "AI 应用工程师"

    print("type(name):", type(name))
    print("type(age):", type(age))
    print("type(height):", type(height))
    print("type(is_learning_ai):", type(is_learning_ai))
    print("type(target_role):", type(target_role))

    introduction = (
        f"我叫 {name}，今年 {age} 岁，身高 {height}，"
        f"正在学习 AI：{is_learning_ai}，目标方向是 {target_role}。"
    )
    print(introduction)


if __name__ == "__main__":
    main()