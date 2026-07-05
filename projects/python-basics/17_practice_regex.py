import re


def extract_order_ids(text: str) -> list[str]:
    return re.findall(r"ORD-\d{8}-\d{3}", text)


def is_valid_order_id(order_id: str) -> bool:
    return re.fullmatch(r"ORD-\d{8}-\d{3}", order_id) is not None


def extract_phone_numbers(text: str) -> list[str]:
    return re.findall(r"1[3-9]\d{9}", text)


def extract_emails(text: str) -> list[str]:
    return re.findall(r"[\w.-]+@[\w.-]+\.\w+", text)


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def mask_phone_numbers(text: str) -> str:
    return re.sub(r"(1[3-9]\d)\d{4}(\d{4})", r"\1****\2", text)


def extract_log_fields(log_line: str) -> dict[str, str]:
    trace_match = re.search(r"trace_id=([a-zA-Z0-9-]+)", log_line)
    user_match = re.search(r"user_id=(\d+)", log_line)

    return {
        "trace_id": trace_match.group(1) if trace_match else "",
        "user_id": user_match.group(1) if user_match else "",
    }


def classify_question(question: str) -> str:
    rules = {
        "refund": r"退款|退钱|退货",
        "shipping": r"物流|快递|发货|配送",
        "invoice": r"发票|开票",
    }

    for category, pattern in rules.items():
        if re.search(pattern, question):
            return category

    return "other"


def main() -> None:
    text = """
    用户 13812345678 反馈订单 ORD-20260705-001 需要退款。
    另一个订单 ORD-20260705-002 咨询物流。
    邮箱 panpan@example.com，备用邮箱 support.ai@test.cn。
    """

    print("订单号:", extract_order_ids(text))
    print("订单号是否合法:", is_valid_order_id("ORD-20260705-001"))
    print("订单号是否合法:", is_valid_order_id("订单 ORD-20260705-001"))
    print("手机号:", extract_phone_numbers(text))
    print("邮箱:", extract_emails(text))
    print("清洗空格:", normalize_spaces("  Python    正则    表达式  "))
    print("脱敏文本:", mask_phone_numbers("手机号 13812345678，备用 15987654321"))

    log_line = "2026-07-05 INFO trace_id=req-20260705-001 user_id=330 status=200"
    print("日志字段:", extract_log_fields(log_line))

    questions = [
        "我的订单怎么退款？",
        "快递什么时候到？",
        "帮我开发票",
        "Python 怎么学？",
    ]

    for question in questions:
        print(question, "=>", classify_question(question))


if __name__ == "__main__":
    main()
