import re


def extract_order_ids(text: str) -> list[str]:
    return re.findall(r"ORD-\d{8}-\d{3}", text)


def extract_phone_numbers(text: str) -> list[str]:
    return re.findall(r"1[3-9]\d{9}", text)


def extract_emails(text: str) -> list[str]:
    return re.findall(r"[\w.-]+@[\w.-]+\.\w+", text)


def clean_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def classify_question(question: str) -> str:
    if re.search(r"退款|退钱|退货", question):
        return "refund"

    if re.search(r"物流|快递|发货|配送", question):
        return "shipping"

    if re.search(r"发票|开票", question):
        return "invoice"

    return "other"


def parse_order_id(order_id: str) -> dict[str, str] | None:
    match = re.fullmatch(r"ORD-(\d{8})-(\d{3})", order_id)

    if match is None:
        return None

    return {
        "date": match.group(1),
        "sequence": match.group(2),
    }


def extract_trace_id(log_line: str) -> str | None:
    match = re.search(r"trace_id=([a-zA-Z0-9-]+)", log_line)

    if match is None:
        return None

    return match.group(1)


def mask_phone_number(text: str) -> str:
    return re.sub(r"(1[3-9]\d)\d{4}(\d{4})", r"\1****\2", text)


def main() -> None:
    print("=== 1. re.search：判断是否匹配 ===")
    question = "我想查询订单 ORD-20260705-001 的物流"
    match = re.search(r"ORD-\d{8}-\d{3}", question)
    print("是否找到订单号:", match is not None)
    if match is not None:
        print("找到的内容:", match.group())

    print("\n=== 2. re.findall：找出所有匹配 ===")
    text = "订单 ORD-20260705-001 和 ORD-20260705-002 都需要退款"
    print(extract_order_ids(text))

    print("\n=== 3. 常用符号：\\d、[]、{} ===")
    user_text = "手机号是 13812345678，备用手机号是 15987654321"
    print(extract_phone_numbers(user_text))

    print("\n=== 4. 提取邮箱 ===")
    email_text = "请联系 panpan@example.com 或 support.ai@test.cn"
    print(extract_emails(email_text))

    print("\n=== 5. re.sub：替换和清洗 ===")
    messy_text = "  Python    AI   学习   "
    print(clean_spaces(messy_text))
    print(mask_phone_number("用户手机号：13812345678"))

    print("\n=== 6. 分组 group ===")
    parsed = parse_order_id("ORD-20260705-001")
    print(parsed)

    print("\n=== 7. fullmatch：必须整体匹配 ===")
    print(re.fullmatch(r"\d{6}", "123456") is not None)
    print(re.fullmatch(r"\d{6}", "编号123456") is not None)

    print("\n=== 8. flags：忽略大小写 ===")
    print(re.search(r"python", "I am learning Python", flags=re.IGNORECASE) is not None)

    print("\n=== 9. 从日志中提取 trace_id ===")
    log_line = "2026-07-05 INFO trace_id=req-20260705-001 user_id=330 request done"
    print(extract_trace_id(log_line))

    print("\n=== 10. 简单规则分类 ===")
    questions = [
        "我的订单能退款吗？",
        "什么时候发货？",
        "可以开发票吗？",
        "怎么学习 Python？",
    ]

    for item in questions:
        print(item, "=>", classify_question(item))


if __name__ == "__main__":
    main()
