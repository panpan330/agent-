from urllib.parse import parse_qs, urlencode, urlparse

import requests


def build_order_url(base_url: str, order_id: str) -> str:
    return f"{base_url.rstrip('/')}/orders/{order_id}"


def build_search_url(
    base_url: str,
    keyword: str,
    status: str,
    page: int,
) -> str:
    query = urlencode(
        {
            "keyword": keyword,
            "status": status,
            "page": page,
        }
    )

    return f"{base_url.rstrip('/')}/orders/search?{query}"


def build_auth_headers(token: str) -> dict[str, str]:
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }


def build_create_ticket_body(
    user_id: int,
    title: str,
    content: str,
    category: str,
) -> dict[str, object]:
    cleaned_title = title.strip()
    cleaned_content = content.strip()
    cleaned_category = category.strip()

    if not cleaned_title:
        raise ValueError("title is required")

    if not cleaned_content:
        raise ValueError("content is required")

    if not cleaned_category:
        raise ValueError("category is required")

    return {
        "user_id": user_id,
        "title": cleaned_title,
        "content": cleaned_content,
        "category": cleaned_category,
    }


def classify_status_code(status_code: int) -> str:
    if 200 <= status_code < 300:
        return "success"

    if 400 <= status_code < 500:
        return "client_error"

    if 500 <= status_code < 600:
        return "server_error"

    return "other"


def parse_query_params(url: str) -> dict[str, str]:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    result = {}
    for key, values in query.items():
        if values:
            result[key] = values[0]

    return result


def prepare_json_post(
    url: str,
    body: dict[str, object],
    token: str,
) -> dict[str, object]:
    request = requests.Request(
        "POST",
        url,
        json=body,
        headers=build_auth_headers(token),
    )
    prepared = request.prepare()

    prepared_body = prepared.body
    if isinstance(prepared_body, bytes):
        prepared_body = prepared_body.decode("utf-8")

    return {
        "method": prepared.method,
        "url": prepared.url,
        "headers": dict(prepared.headers),
        "body": prepared_body,
    }


def main() -> None:
    base_url = "https://api.example.com"

    order_url = build_order_url(base_url, "ORD-20260705-001")
    print("订单 URL:", order_url)

    search_url = build_search_url(base_url, keyword="python 课程", status="paid", page=1)
    print("搜索 URL:", search_url)
    print("query 参数:", parse_query_params(search_url))

    ticket_body = build_create_ticket_body(
        user_id=330,
        title="  订单退款问题  ",
        content="  用户想查询退款进度  ",
        category="refund",
    )
    print("工单 body:", ticket_body)

    prepared = prepare_json_post(
        f"{base_url}/tickets",
        ticket_body,
        token="test-token",
    )
    print("准备好的 POST 请求:", prepared)

    for status_code in [200, 201, 400, 401, 404, 500]:
        print(status_code, "=>", classify_status_code(status_code))


if __name__ == "__main__":
    main()
