import re


ORDER_ID_PATTERN = r"ORD-\d{8}-\d{3}"


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_order_ids(text: str) -> tuple[str, ...]:
    order_ids = re.findall(ORDER_ID_PATTERN, text)
    return tuple(dict.fromkeys(order_ids))


def classify_question(question: str) -> str:
    if re.search(r"退款|退钱|退货", question):
        return "refund"

    if re.search(r"物流|快递|发货|配送", question):
        return "shipping"

    if re.search(r"发票|开票", question):
        return "invoice"

    if re.search(r"学习|Python|Java|AI|函数|测试|异步", question, flags=re.IGNORECASE):
        return "learning"

    return "other"


def extract_keywords(question: str) -> tuple[str, ...]:
    known_keywords = ["python", "java", "ai", "pytest", "fastapi", "rag", "async"]
    lower_question = question.lower()
    keywords = []

    for keyword in known_keywords:
        if keyword in lower_question:
            keywords.append(keyword)

    return tuple(keywords)
