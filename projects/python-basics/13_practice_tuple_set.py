def normalize_keyword(keyword: str) -> str:
    return keyword.strip().lower()


def extract_keywords(raw_keywords: list[str]) -> set[str]:
    keywords = set()

    for raw_keyword in raw_keywords:
        keyword = normalize_keyword(raw_keyword)
        if keyword:
            keywords.add(keyword)

    return keywords


def build_learning_record(
    student_name: str,
    lesson: tuple[int, str],
    keywords: set[str],
) -> dict[str, object]:
    lesson_number, lesson_title = lesson

    return {
        "student_name": student_name,
        "lesson_number": lesson_number,
        "lesson_title": lesson_title,
        "keywords": sorted(keywords),
    }


def compare_document_ids(old_ids: set[str], new_ids: set[str]) -> dict[str, set[str]]:
    return {
        "all_ids": old_ids | new_ids,
        "same_ids": old_ids & new_ids,
        "only_new_ids": new_ids - old_ids,
    }


def check_permissions(
    required_permissions: set[str],
    user_permissions: set[str],
) -> tuple[bool, set[str]]:
    missing_permissions = required_permissions - user_permissions
    can_access = len(missing_permissions) == 0

    return can_access, missing_permissions


def main() -> None:
    raw_keywords = [" Python ", "python", "AI", "ai", "集合", ""]
    keywords = extract_keywords(raw_keywords)
    print("去重后的关键词:", sorted(keywords))

    lesson = (13, "元组和集合")
    record = build_learning_record("Panpan", lesson, keywords)
    print("学习记录:", record)

    old_ids = {"doc-1", "doc-2", "doc-3"}
    new_ids = {"doc-2", "doc-3", "doc-4"}
    document_result = compare_document_ids(old_ids, new_ids)
    print("全部文档:", sorted(document_result["all_ids"]))
    print("重复文档:", sorted(document_result["same_ids"]))
    print("新增文档:", sorted(document_result["only_new_ids"]))

    required_permissions = {"read:docs", "call:ai"}
    user_permissions = {"read:docs", "upload:docs"}
    can_access, missing_permissions = check_permissions(required_permissions, user_permissions)
    print("是否可以访问:", can_access)
    print("缺少权限:", sorted(missing_permissions))


if __name__ == "__main__":
    main()
