from http import HTTPStatus
from urllib.parse import parse_qs, urlencode, urlparse
import json

import requests


def parse_url(url: str) -> dict[str, object]:
    parsed = urlparse(url)

    return {
        "scheme": parsed.scheme,
        "host": parsed.netloc,
        "path": parsed.path,
        "query": parse_qs(parsed.query),
    }


def build_url(base_url: str, path: str, query: dict[str, object] | None = None) -> str:
    base = base_url.rstrip("/")
    clean_path = path.lstrip("/")
    url = f"{base}/{clean_path}"

    if not query:
        return url

    return f"{url}?{urlencode(query)}"


def build_json_headers(token: str | None = None) -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    return headers


def explain_status_code(status_code: int) -> str:
    if 200 <= status_code < 300:
        return "success"

    if 400 <= status_code < 500:
        return "client_error"

    if 500 <= status_code < 600:
        return "server_error"

    return "other"


def get_status_phrase(status_code: int) -> str:
    try:
        return HTTPStatus(status_code).phrase
    except ValueError:
        return "Unknown"


def build_create_order_body(user_id: int, product_id: str, quantity: int) -> dict[str, object]:
    return {
        "user_id": user_id,
        "items": [
            {
                "product_id": product_id,
                "quantity": quantity,
            }
        ],
    }


def prepare_get_request(url: str, params: dict[str, object]) -> dict[str, object]:
    request = requests.Request("GET", url, params=params)
    prepared = request.prepare()

    return {
        "method": prepared.method,
        "url": prepared.url,
        "headers": dict(prepared.headers),
        "body": prepared.body,
    }


def prepare_post_request(
    url: str,
    json_body: dict[str, object],
    headers: dict[str, str],
) -> dict[str, object]:
    request = requests.Request("POST", url, json=json_body, headers=headers)
    prepared = request.prepare()

    body = prepared.body
    if isinstance(body, bytes):
        body = body.decode("utf-8")

    return {
        "method": prepared.method,
        "url": prepared.url,
        "headers": dict(prepared.headers),
        "body": body,
    }


def try_real_get_request() -> None:
    print("\n=== 9. 可选：真实 GET 请求 ===")

    try:
        response = requests.get(
            "https://httpbin.org/get",
            params={"topic": "http", "lesson": 20},
            timeout=5,
        )
    except requests.RequestException as error:
        print("网络请求失败，本节核心知识不受影响:", error)
        return

    print("状态码:", response.status_code)
    content_type = response.headers.get("Content-Type", "")
    print("响应类型:", content_type)

    if response.status_code != 200:
        print("服务端没有返回成功状态，本次真实请求只作为网络演示")
        return

    if "application/json" not in content_type:
        print("响应不是 JSON，不能直接 response.json()")
        return

    try:
        data = response.json()
    except ValueError as error:
        print("JSON 解析失败:", error)
        return

    print("响应 JSON 里的 args:", data.get("args"))


def main() -> None:
    print("=== 1. URL 结构 ===")
    url = "https://api.example.com/orders/123?detail=true&page=1"
    print(parse_url(url))

    print("\n=== 2. 构造带 query 参数的 URL ===")
    search_url = build_url(
        "https://api.example.com",
        "/orders",
        {"status": "paid", "page": 1},
    )
    print(search_url)

    print("\n=== 3. GET：查询数据 ===")
    get_request = prepare_get_request(
        "https://api.example.com/orders",
        {"status": "paid", "page": 1},
    )
    print(get_request)

    print("\n=== 4. POST：提交 JSON 数据 ===")
    body = build_create_order_body(user_id=330, product_id="book-python", quantity=2)
    headers = build_json_headers(token="test-token")
    post_request = prepare_post_request("https://api.example.com/orders", body, headers)
    print(post_request)
    print("POST body JSON:", json.loads(str(post_request["body"])))

    print("\n=== 5. Header ===")
    print(build_json_headers())
    print(build_json_headers(token="abc123"))

    print("\n=== 6. Request Body ===")
    print(body)

    print("\n=== 7. Status Code ===")
    for status_code in [200, 201, 400, 401, 403, 404, 500, 999]:
        print(status_code, get_status_phrase(status_code), explain_status_code(status_code))

    print("\n=== 8. JSON 响应长什么样 ===")
    response_json = {
        "order_id": "ORD-20260705-001",
        "status": "paid",
        "items": body["items"],
    }
    print(json.dumps(response_json, ensure_ascii=False, indent=2))

    try_real_get_request()


if __name__ == "__main__":
    main()
