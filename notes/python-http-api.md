# Python HTTP/API 基础

日期：2026-07-05

对应代码：

```text
projects/python-basics/lesson20_http_api.py
projects/python-basics/lesson20_practice_http_api.py
projects/python-basics/test_lesson20_practice_http_api.py
```

## 1. HTTP 是什么

HTTP 是一种通信协议。

可以先理解成：

```text
HTTP = 客户端和服务端之间约定好的请求/响应规则
```

浏览器访问网站、前端调用后端、Python 调 AI 服务，很多时候都是通过 HTTP。

一次 HTTP 通信通常分两部分：

- Request：请求。
- Response：响应。

## 2. API 是什么

API 是应用程序之间互相调用的接口。

在 Web 项目里，我们经常说的 API 通常指 HTTP API。

例如：

```text
GET /orders/123
POST /tickets
```

可以先理解成：

```text
HTTP API = 通过 HTTP 暴露出来的函数入口
```

后面 FastAPI 做的事情，就是让我们用 Python 函数写 HTTP API。

## 3. URL 是什么

URL 是资源地址。

例子：

```text
https://api.example.com/orders/123?detail=true&page=1
```

可以拆成：

- `https`：协议。
- `api.example.com`：域名或主机。
- `/orders/123`：路径。
- `?detail=true&page=1`：query 参数。

Python 里可以用 `urlparse()` 拆 URL：

```python
from urllib.parse import urlparse, parse_qs

parsed = urlparse(url)
query = parse_qs(parsed.query)
```

## 4. Path 参数

Path 参数是 URL 路径的一部分。

```text
/orders/123
```

这里 `123` 可以表示订单 ID。

后面 FastAPI 会这样写：

```python
@app.get("/orders/{order_id}")
def get_order(order_id: str):
    ...
```

`order_id` 就来自路径。

## 5. Query 参数

Query 参数在 `?` 后面。

```text
/orders?status=paid&page=1
```

这里：

- `status=paid`
- `page=1`

适合用来表达筛选、分页、搜索条件。

用 Python 构造 query 参数：

```python
from urllib.parse import urlencode

query = urlencode({"status": "paid", "page": 1})
```

## 6. GET 是什么

`GET` 通常用来查询数据。

例如：

```text
GET /orders/ORD-20260705-001
GET /orders?status=paid&page=1
```

特点：

- 通常不提交复杂 body。
- 参数常放在 path 或 query 里。
- 语义上是读取数据。

## 7. POST 是什么

`POST` 通常用来提交数据或创建数据。

例如：

```text
POST /tickets
```

请求 body：

```json
{
  "user_id": 330,
  "title": "订单退款问题",
  "content": "用户想查询退款进度",
  "category": "refund"
}
```

语义上是把一份数据提交给服务端处理。

## 8. Request Body

Request Body 是请求体。

GET 请求通常没有 body。

POST、PUT、PATCH 经常有 body。

最常见的 body 是 JSON：

```json
{
  "question": "怎么学习 FastAPI？",
  "stream": false
}
```

后面 FastAPI 会用 Pydantic 定义 body 结构。

## 9. Headers 是什么

Headers 是请求或响应的附加信息。

常见请求 header：

- `Accept`：希望服务端返回什么类型。
- `Content-Type`：请求体是什么类型。
- `Authorization`：认证信息。
- `User-Agent`：客户端信息。

JSON 请求常见 header：

```python
{
    "Accept": "application/json",
    "Content-Type": "application/json",
}
```

带 token：

```python
{
    "Authorization": "Bearer abc123"
}
```

## 10. Status Code 是什么

Status Code 是响应状态码。

它告诉客户端请求处理结果。

常见状态码：

| 状态码 | 含义 |
| --- | --- |
| `200` | 成功 |
| `201` | 创建成功 |
| `400` | 请求参数错误 |
| `401` | 没有认证 |
| `403` | 没有权限 |
| `404` | 找不到资源 |
| `500` | 服务端错误 |

可以先按范围记：

- `2xx`：成功。
- `4xx`：客户端请求有问题。
- `5xx`：服务端有问题。

## 11. JSON 请求和 JSON 响应

JSON 是 HTTP API 里最常见的数据格式。

请求 JSON：

```json
{
  "question": "什么是 HTTP？"
}
```

响应 JSON：

```json
{
  "answer": "HTTP 是一种请求响应协议。"
}
```

Python 字典和 JSON 很像，但不是同一个东西。

Python 字典：

```python
{"stream": False}
```

JSON：

```json
{"stream": false}
```

注意 JSON 里的布尔值是小写 `true`、`false`。

## 12. requests 是什么

`requests` 是 Python 常用 HTTP 客户端库。

当前项目已经安装：

```toml
dependencies = [
    "requests>=2.34.2",
]
```

GET 请求：

```python
import requests

response = requests.get("https://httpbin.org/get", params={"topic": "http"})
```

POST JSON：

```python
response = requests.post(
    "https://api.example.com/tickets",
    json={"title": "订单退款问题"},
    headers={"Content-Type": "application/json"},
)
```

## 13. 构造请求但不发送

学习阶段可以用 `requests.Request` 构造请求，但不真正发送。

```python
request = requests.Request("GET", url, params={"page": 1})
prepared = request.prepare()
print(prepared.method)
print(prepared.url)
```

这样不依赖网络，也能看清楚 HTTP 请求长什么样。

## 14. 超时 timeout

真实请求一定要设置 timeout。

```python
requests.get(url, timeout=5)
```

不设置 timeout，网络卡住时程序可能等很久。

后面做 AI 服务，模型请求、Java API 请求、向量库请求都要考虑超时。

## 15. RequestException

网络请求可能失败。

应该捕获 `requests.RequestException`：

```python
try:
    response = requests.get(url, timeout=5)
except requests.RequestException as error:
    print("请求失败:", error)
```

不要默认网络一定可用。

## 16. API 调用的基本流程

可以按这个顺序理解一次 API 调用：

1. 确定 URL。
2. 确定 HTTP 方法，比如 GET 或 POST。
3. 准备 path/query/body/header。
4. 发送请求。
5. 拿到响应状态码。
6. 判断状态码是否成功。
7. 解析 JSON 响应。
8. 处理错误情况。

## 17. FastAPI 和 HTTP 的关系

FastAPI 就是用 Python 写 HTTP API 的框架。

后面你会看到：

```python
@app.get("/health")
def health():
    return {"status": "ok"}
```

这表示：

```text
当客户端 GET /health 时，执行 health 函数，把返回值转成 JSON 响应。
```

所以现在学 HTTP，是为了后面看懂 FastAPI。

## 18. 常见错误

### 错误 1：把 path 参数和 query 参数混淆

Path：

```text
/orders/123
```

Query：

```text
/orders?status=paid
```

### 错误 2：GET 里放复杂 body

查询用 GET。

提交复杂 JSON 通常用 POST。

### 错误 3：忘记 Content-Type

提交 JSON 时，通常需要：

```text
Content-Type: application/json
```

### 错误 4：不看状态码直接解析结果

不要默认响应一定成功。

先看：

```python
response.status_code
```

再决定怎么处理。

### 错误 5：不设置 timeout

真实网络请求要设置 timeout。

## 19. 本节练习

创建文件：

```text
projects/python-basics/lesson20_practice_http_api.py
projects/python-basics/test_lesson20_practice_http_api.py
```

要求：

1. 写函数 `build_order_url(base_url, order_id)`
   - 构造 `/orders/{order_id}`。
2. 写函数 `build_search_url(base_url, keyword, status, page)`
   - 构造带 query 参数的搜索 URL。
3. 写函数 `build_auth_headers(token)`
   - 返回 JSON header 和 Authorization。
4. 写函数 `build_create_ticket_body(...)`
   - 清洗 title/content/category。
   - 必填字段为空时抛 `ValueError`。
5. 写函数 `classify_status_code(status_code)`
   - 返回 `success`、`client_error`、`server_error`、`other`。
6. 写函数 `parse_query_params(url)`
   - 从 URL 中解析 query 参数。
7. 写函数 `prepare_json_post(url, body, token)`
   - 构造 POST JSON 请求，但不发送。
8. 写 pytest 测试验证这些函数。

## 20. 练习参考答案

```python
def build_order_url(base_url: str, order_id: str) -> str:
    return f"{base_url.rstrip('/')}/orders/{order_id}"
```

```python
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
```

```python
def classify_status_code(status_code: int) -> str:
    if 200 <= status_code < 300:
        return "success"

    if 400 <= status_code < 500:
        return "client_error"

    if 500 <= status_code < 600:
        return "server_error"

    return "other"
```

测试示例：

```python
def test_build_order_url() -> None:
    assert (
        build_order_url("https://api.example.com/", "ORD-20260705-001")
        == "https://api.example.com/orders/ORD-20260705-001"
    )
```

```python
def test_prepare_json_post() -> None:
    prepared = prepare_json_post("https://api.example.com/tickets", body, token="abc123")

    assert prepared["method"] == "POST"
    assert prepared["headers"]["Authorization"] == "Bearer abc123"
```

运行：

```powershell
uv run pytest test_lesson20_practice_http_api.py -q
```

## 21. 自测问题

1. HTTP 是什么？
2. API 是什么？
3. URL 主要由哪几部分组成？
4. Path 参数和 query 参数有什么区别？
5. GET 通常用来做什么？
6. POST 通常用来做什么？
7. Request Body 是什么？
8. Header 里的 `Content-Type` 表示什么？
9. `2xx`、`4xx`、`5xx` 状态码大致分别表示什么？
10. 为什么真实 HTTP 请求要设置 timeout？

## 22. 自测参考答案

1. HTTP 是什么？

   HTTP 是客户端和服务端之间约定好的请求/响应通信规则。

2. API 是什么？

   API 是程序之间互相调用的接口；HTTP API 就是通过 HTTP 暴露出来的接口。

3. URL 主要由哪几部分组成？

   主要包括协议、主机、路径和 query 参数。

4. Path 参数和 query 参数有什么区别？

   Path 参数是路径的一部分，比如 `/orders/123`；query 参数在 `?` 后面，比如 `/orders?status=paid`。

5. GET 通常用来做什么？

   GET 通常用来查询或读取数据。

6. POST 通常用来做什么？

   POST 通常用来提交数据、创建数据或触发服务端处理。

7. Request Body 是什么？

   Request Body 是请求体，常用于 POST 请求提交 JSON 数据。

8. Header 里的 `Content-Type` 表示什么？

   它表示请求体的数据格式，比如 `application/json` 表示请求体是 JSON。

9. `2xx`、`4xx`、`5xx` 状态码大致分别表示什么？

   `2xx` 表示成功；`4xx` 表示客户端请求有问题；`5xx` 表示服务端有问题。

10. 为什么真实 HTTP 请求要设置 timeout？

    因为网络可能卡住，不设置 timeout 可能导致程序长时间等待，影响服务稳定性。

## 23. 推荐资料

- MDN：HTTP 概述
  https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Guides/Overview

- MDN：HTTP 请求方法
  https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Methods

- MDN：HTTP 状态码
  https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Reference/Status

- requests 官方文档
  https://requests.readthedocs.io/
