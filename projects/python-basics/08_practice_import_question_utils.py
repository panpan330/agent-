from question_utils import build_prompt, clean_question, contains_keyword, is_valid_question


def main() -> None:
    raw_question = "   我想学习 Python import   "
    question = clean_question(raw_question)

    if not is_valid_question(question):
        print("问题无效")
        return

    result = {
        "question": question,
        "contains_python": contains_keyword(question, "Python"),
        "contains_import": contains_keyword(question, "import"),
        "prompt": build_prompt(question, role="Python 模块导入老师"),
    }

    print(result)


if __name__ == "__main__":
    main()
