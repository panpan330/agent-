def main() -> None:
    raw_question = "   HELLO, I want to learn AI!!!   "

    cleaned_question = raw_question.strip().lower()
    python_question = cleaned_question.replace("ai", "python")

    words = python_question.split(" ")
    keyword = "python"
    has_keyword = keyword in python_question

    prompt = f"""你是一个 Python 学习助手。
用户问题：{python_question}
问题单词列表：{words}
是否包含关键词 {keyword}：{has_keyword}

请根据用户问题，给出适合初学者的解释。"""

    print("原始问题:", repr(raw_question))
    print("清洗后问题:", cleaned_question)
    print("替换后问题:", python_question)
    print("单词列表:", words)
    print("是否包含关键词:", has_keyword)
    print("prompt:")
    print(prompt)


if __name__ == "__main__":
    main()
