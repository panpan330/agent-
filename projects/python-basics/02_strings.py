def main() -> None:
    print("=== 1. 字符串是什么 ===")
    message = "Hello, Python"
    print(message)
    print(type(message))

    print("\n=== 2. 单引号、双引号、三引号 ===")
    single_quote = 'I am learning Python'
    double_quote = "I am learning AI"
    multi_line = """你是一个 AI 学习助手。
请用简单、清楚的方式解释 Python 字符串。
每次都给出例子。"""

    print(single_quote)
    print(double_quote)
    print(multi_line)

    print("\n=== 3. 字符串拼接 ===")
    first_name = "Pan"
    last_name = "Pan"
    full_name = first_name + last_name
    print(full_name)

    print("\n=== 4. f-string ===")
    name = "Panpan"
    age = 25
    target = "AI 应用工程师"
    introduction = f"我叫 {name}，今年 {age} 岁，目标是成为 {target}。"
    print(introduction)

    print("\n=== 5. 常用字符串方法 ===")
    raw_question = "   HELLO, I want to learn AI!!!   "
    print("原始问题:", repr(raw_question))

    cleaned_question = raw_question.strip()
    print("strip 后:", repr(cleaned_question))
    print("lower 后:", cleaned_question.lower())
    print("upper 后:", cleaned_question.upper())
    print("replace 后:", cleaned_question.replace("AI", "Python"))

    words = cleaned_question.split(" ")
    print("split 后:", words)

    joined = "-".join(words)
    print("join 后:", joined)

    print("\n=== 6. 索引和切片 ===")
    language = "Python"
    print("language[0]:", language[0])
    print("language[1]:", language[1])
    print("language[-1]:", language[-1])
    print("language[0:2]:", language[0:2])
    print("language[2:]:", language[2:])

    print("\n=== 7. 判断是否包含 ===")
    user_question = "How can I learn Python and AI?"
    print("Python" in user_question)
    print("Java" in user_question)

    print("\n=== 8. prompt 字符串 ===")
    role = "Python 基础老师"
    topic = "字符串"
    prompt = f"""你是一个{role}。
请用零基础能听懂的方式讲解：{topic}。
要求：
1. 先解释概念
2. 再给代码例子
3. 最后给练习题"""

    print(prompt)


if __name__ == "__main__":
    main()
