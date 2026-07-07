# FastAPI 阶段 1 第 10 节：测试 FastAPI 接口

日期：2026-07-07

本节目标：系统理解 FastAPI 接口测试，知道为什么要写测试、怎么写测试、每类测试到底在验证什么。

目前项目已经有：

```text
GET  /health
POST /chat
ChatRequest
ChatResponse
```

也已经有测试：

```text
tests/
  conftest.py
  test_health.py
  test_chat_schema.py
  test_chat_api.py
```

这一节把这些测试彻底讲清楚。

## 1. 本节学什么

本节学习这些内容：

1. 为什么后端接口必须写测试。
2. pytest 是什么。
3. FastAPI `TestClient` 是什么。
4. 为什么测试不需要手动启动 Uvicorn。
5. `conftest.py` 是什么。
6. pytest fixture 是什么。
7. `client` fixture 怎么复用。
8. schema 测试和 API 测试有什么区别。
9. 怎么测试 `GET /health`。
10. 怎么测试 `POST /chat`。
11. 怎么测试 200、422、405。
12. 怎么看 FastAPI 422 错误结构。
13. 测试文件应该怎么组织。
14. 后面测试会怎么扩展。

先记住一句话：

```text
测试不是为了证明代码现在能跑，而是为了防止以后改坏。
```

再记住一句话：

```text
schema 测试测数据模型，API 测试测 HTTP 接口行为。
```

## 2. 为什么后端接口必须写测试

后端接口一旦被前端、Java 服务或其他系统调用，就变成了对外承诺。

比如 `/chat` 承诺：

```text
客户端 POST /chat
发送 {"message": "..."}
服务端返回 {"reply": "..."}
```

如果以后你改代码时不小心把字段改了：

```json
{
  "answer": "..."
}
```

前端可能立刻坏掉。

测试的作用是：

```text
在你改代码时，自动检查这些承诺有没有被破坏。
```

所以测试不是额外负担。

测试是项目变大后还能放心修改的基础。

## 3. pytest 是什么

pytest 是 Python 里常用的测试框架。

它会自动寻找：

```text
test_*.py 文件
test_ 开头的函数
```

例如：

```python
def test_health_check() -> None:
    ...
```

运行命令：

```powershell
uv run pytest -q
```

含义：

```text
在当前项目环境里运行 pytest。
-q 表示输出更简洁。
```

当前结果：

```text
14 passed
```

说明 14 个测试全部通过。

## 4. TestClient 是什么

FastAPI 提供：

```python
from fastapi.testclient import TestClient
```

`TestClient` 用来测试 FastAPI 应用。

它可以像真实客户端一样发送：

```text
GET
POST
PUT
DELETE
```

例如：

```python
response = client.get("/health")
response = client.post("/chat", json={"message": "你好"})
```

但它不需要你手动启动：

```powershell
uv run uvicorn app.main:app --reload
```

## 5. 为什么测试不需要手动启动 Uvicorn

平时浏览器访问接口时，需要：

```text
浏览器 -> HTTP -> Uvicorn -> FastAPI
```

但测试时：

```text
TestClient -> FastAPI app
```

`TestClient` 直接和 FastAPI 应用通信。

它不需要真实打开网络端口。

好处：

```text
速度快。
稳定。
适合自动化。
不用手动开服务。
测试失败更容易定位。
```

所以接口测试可以直接运行：

```powershell
uv run pytest -q
```

## 6. conftest.py 是什么

文件：

```text
projects/ai-service/tests/conftest.py
```

当前代码：

```python
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.main import create_app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())
```

`conftest.py` 是 pytest 的特殊文件。

它可以放共享配置和共享 fixture。

pytest 会自动发现它。

测试文件里不需要手动 import `client` fixture。

只要测试函数参数写：

```python
def test_xxx(client: TestClient) -> None:
    ...
```

pytest 就会自动把 fixture 传进去。

## 7. 为什么 conftest.py 里要改 sys.path

当前代码：

```python
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
```

作用：

```text
把 projects/ai-service 加入 Python 导入路径。
```

这样测试才能导入：

```python
from app.main import create_app
```

当前项目还没有打包安装成正式 Python 包。

所以先用这种方式确保测试能找到 `app`。

后面项目结构更成熟时，可以进一步优化。

## 8. fixture 是什么

pytest fixture 可以理解成：

```text
测试前准备好的共享对象。
```

当前 fixture：

```python
@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())
```

它的作用是：

```text
给测试函数提供一个可用的 FastAPI 测试客户端。
```

测试函数这样用：

```python
def test_health_check(client: TestClient) -> None:
    response = client.get("/health")
```

pytest 看到参数名 `client`，会自动调用 fixture。

## 9. 为什么要把 client 做成 fixture

以前每个测试里都写：

```python
client = TestClient(create_app())
```

这样会重复。

现在集中到：

```python
@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())
```

好处：

```text
减少重复代码。
所有 API 测试用同一种客户端创建方式。
以后要改测试 app 初始化逻辑，只改 conftest.py。
测试函数更专注于请求和断言。
```

这是测试工程化的第一步。

## 10. 当前测试分成哪几类

当前有三类测试：

```text
健康检查 API 测试
聊天 schema 测试
聊天 API 测试
```

对应文件：

| 文件 | 类型 | 测什么 |
| --- | --- | --- |
| `test_health.py` | API 测试 | `GET /health` |
| `test_chat_schema.py` | schema 测试 | `ChatRequest`、`ChatResponse` |
| `test_chat_api.py` | API 测试 | `POST /chat` |

## 11. schema 测试是什么

schema 测试测试的是 Pydantic 模型本身。

例如：

```python
ChatRequest(message="你好")
ChatRequest()
ChatRequest(message="")
ChatRequest(message=123)
```

它不走 HTTP。

它直接测试：

```text
模型是否接受正确数据。
模型是否拒绝错误数据。
错误类型是否符合预期。
```

所以：

```text
schema 测试 = 测数据结构和校验规则。
```

## 12. API 测试是什么

API 测试测试的是 FastAPI 路由行为。

例如：

```python
response = client.post("/chat", json={"message": "你好"})
```

它会走：

```text
TestClient
        ↓
FastAPI 路由
        ↓
Pydantic 请求校验
        ↓
接口函数
        ↓
响应模型
        ↓
HTTP 响应
```

所以：

```text
API 测试 = 测接口整体行为。
```

## 13. schema 测试和 API 测试的区别

| 对比项 | schema 测试 | API 测试 |
| --- | --- | --- |
| 是否走 HTTP | 不走 | 走 TestClient 模拟 HTTP |
| 测试对象 | Pydantic 模型 | FastAPI 接口 |
| 典型断言 | `ValidationError` | 状态码、响应 JSON |
| 例子 | `ChatRequest(message="")` | `POST /chat` |

两个都需要。

schema 测试更小、更精确。

API 测试更接近真实调用。

## 14. 测试 GET /health

文件：

```text
tests/test_health.py
```

代码：

```python
from fastapi.testclient import TestClient


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "ok"
    assert data["service"] == "ai-service"
    assert isinstance(data["time"], str)
```

这个测试验证：

```text
/health 能返回 200。
status 是 ok。
service 是 ai-service。
time 是字符串。
```

## 15. 测试 POST /chat 正常请求

文件：

```text
tests/test_chat_api.py
```

代码：

```python
def test_chat_replies_with_mock_message(client: TestClient) -> None:
    response = client.post(
        "/chat",
        json={"message": "请解释 FastAPI 是什么"},
    )
    data = response.json()

    assert response.status_code == 200
    assert data == {"reply": "你刚才说的是：请解释 FastAPI 是什么"}
```

这里重点是：

```python
client.post(...)
```

表示发送 POST。

```python
json={...}
```

表示发送 JSON 请求体。

断言：

```python
assert response.status_code == 200
```

表示请求成功。

## 16. 测试 422：缺少 message

代码：

```python
response = client.post("/chat", json={})
```

这是发送空 JSON。

断言：

```python
assert response.status_code == 422
assert data["detail"][0]["loc"] == ["body", "message"]
assert data["detail"][0]["type"] == "missing"
```

这验证：

```text
message 是必填字段。
错误位置是 body.message。
错误类型是 missing。
```

## 17. 测试 422：空 message

代码：

```python
response = client.post("/chat", json={"message": ""})
```

断言：

```python
assert data["detail"][0]["type"] == "string_too_short"
```

这验证：

```text
Field(min_length=1) 生效。
空字符串会被拒绝。
```

## 18. 测试 422：非字符串 message

代码：

```python
response = client.post("/chat", json={"message": 123})
```

断言：

```python
assert data["detail"][0]["type"] == "string_type"
```

这验证：

```text
message 必须是字符串。
数字会被拒绝。
```

## 19. 测试 405：GET /chat

代码：

```python
response = client.get("/chat")

assert response.status_code == 405
```

`/chat` 只定义了：

```text
POST /chat
```

没有定义：

```text
GET /chat
```

所以 GET 访问 `/chat` 返回：

```text
405 Method Not Allowed
```

这不是 bug。

这是正确行为。

## 20. 200、422、405 分别说明什么

| 状态码 | 含义 | 当前例子 |
| --- | --- | --- |
| 200 | 请求成功 | 正确 `POST /chat` |
| 422 | 请求体校验失败 | 缺少 `message` |
| 405 | HTTP 方法不允许 | `GET /chat` |

要能分清：

```text
422 是数据不符合模型。
405 是方法不符合接口定义。
```

## 21. FastAPI 422 错误结构怎么看

错误响应大概是：

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "message"],
      "msg": "Field required"
    }
  ]
}
```

重点看：

| 字段 | 含义 |
| --- | --- |
| `detail` | 错误详情列表 |
| `type` | 错误类型 |
| `loc` | 错误位置 |
| `msg` | 错误说明 |

例如：

```text
loc = ["body", "message"]
```

表示：

```text
请求体里的 message 字段有问题。
```

## 22. 为什么断言错误类型

有些测试只写：

```python
assert response.status_code == 422
```

这样可以，但不够精确。

我们还断言：

```python
assert data["detail"][0]["type"] == "missing"
```

好处是：

```text
确认失败原因确实是 message 缺失。
而不是别的错误碰巧也返回 422。
```

测试越关键，断言越要具体。

## 23. tests/ 目录怎么组织

当前：

```text
tests/
  conftest.py
  test_health.py
  test_chat_schema.py
  test_chat_api.py
```

组织原则：

```text
conftest.py       放共享 fixture。
test_health.py    测健康检查接口。
test_chat_schema.py 测聊天数据模型。
test_chat_api.py  测聊天 API。
```

以后可能增加：

```text
test_config.py
test_errors.py
test_trace_id.py
test_stream_chat.py
```

文件名要表达测试对象。

## 24. 测试函数命名规则

pytest 会自动发现：

```text
test_ 开头的函数。
```

例如：

```python
def test_chat_replies_with_mock_message(...):
    ...
```

好的测试名应该说明：

```text
被测对象是什么。
场景是什么。
预期结果是什么。
```

例如：

```text
test_chat_rejects_missing_message
```

比：

```text
test_1
```

清楚得多。

## 25. 测试的 Arrange、Act、Assert

很多测试可以按三步看：

```text
Arrange 准备数据
Act     执行动作
Assert  断言结果
```

例如：

```python
def test_chat_replies_with_mock_message(client: TestClient) -> None:
    response = client.post(
        "/chat",
        json={"message": "请解释 FastAPI 是什么"},
    )
    data = response.json()

    assert response.status_code == 200
    assert data == {"reply": "你刚才说的是：请解释 FastAPI 是什么"}
```

这里：

```text
Arrange: 准备请求 JSON。
Act: client.post("/chat", json=...)。
Assert: 检查状态码和响应体。
```

## 26. 为什么测试里不用 print

测试不是靠肉眼看输出。

测试靠断言：

```python
assert response.status_code == 200
```

如果断言失败，pytest 会告诉你失败位置和实际值。

`print` 只能辅助调试。

真正判断对错要用 `assert`。

## 27. 常见错误

### 错误 1：忘记 test_ 前缀

错误：

```python
def chat_replies_with_mock_message():
    ...
```

pytest 不会把它当测试。

正确：

```python
def test_chat_replies_with_mock_message():
    ...
```

### 错误 2：把 schema 测试和 API 测试混淆

schema 测试：

```python
ChatRequest(message="")
```

API 测试：

```python
client.post("/chat", json={"message": ""})
```

前者测 Pydantic 模型。

后者测 FastAPI 接口。

### 错误 3：测试 POST 时忘记 json=

推荐：

```python
client.post("/chat", json={"message": "你好"})
```

不要误写成：

```python
client.post("/chat", data={"message": "你好"})
```

`json=` 更符合 JSON body 测试。

### 错误 4：只测成功，不测失败

只测：

```text
200
```

不够。

还要测：

```text
422
405
```

因为真实客户端经常传错数据。

### 错误 5：每个测试重复创建 client

可以工作，但重复。

更好的方式是使用 fixture：

```python
def test_xxx(client: TestClient) -> None:
    ...
```

## 28. 本节必须掌握的最小知识

这一节最少要掌握：

```text
pytest 用来运行测试。
TestClient 用来测试 FastAPI 应用。
TestClient 不需要手动启动 Uvicorn。
conftest.py 可以放共享 fixture。
fixture 可以给测试函数提供 client。
schema 测试测 Pydantic 模型。
API 测试测 FastAPI 路由行为。
200 表示请求成功。
422 表示请求体验证失败。
405 表示 HTTP 方法不允许。
```

## 29. 本节练习

### 练习 1：解释 TestClient

题目：

用自己的话解释：

```text
TestClient 是什么？为什么测试时不需要手动启动 Uvicorn？
```

### 练习 2：解释 conftest.py

题目：

用自己的话解释：

```text
conftest.py 在当前 tests/ 目录里有什么作用？
```

### 练习 3：解释 client fixture

题目：

解释下面代码：

```python
@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())
```

### 练习 4：区分 schema 测试和 API 测试

题目：

判断下面两个测试分别属于哪类测试：

```python
ChatRequest(message="")
```

```python
client.post("/chat", json={"message": ""})
```

### 练习 5：解释状态码

题目：

说明当前项目里这些状态码分别代表什么：

```text
200
422
405
```

### 练习 6：写一个 /health 测试

题目：

写一个测试，使用 `client` fixture 请求 `/health`，并断言状态码是 200。

### 练习 7：写一个 /chat 失败测试

题目：

写一个测试，向 `/chat` 发送空 JSON：

```json
{}
```

并断言返回 422。

## 30. 本节练习参考答案

### 练习 1 参考答案：解释 TestClient

题目：

用自己的话解释：

```text
TestClient 是什么？为什么测试时不需要手动启动 Uvicorn？
```

参考答案：

`TestClient` 是 FastAPI 提供的测试客户端。

它可以直接调用 FastAPI 应用，模拟 HTTP 请求并拿到响应。

它不需要真实启动 Uvicorn，也不需要打开网络端口，所以测试运行更快、更稳定。

### 练习 2 参考答案：解释 conftest.py

题目：

用自己的话解释：

```text
conftest.py 在当前 tests/ 目录里有什么作用？
```

参考答案：

当前 `conftest.py` 有两个作用：

```text
1. 把项目根目录加入 Python 导入路径，让测试能导入 app。
2. 定义共享 client fixture，让多个 API 测试复用 TestClient。
```

### 练习 3 参考答案：解释 client fixture

题目：

解释下面代码：

```python
@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())
```

参考答案：

这段代码定义了一个 pytest fixture，名字叫 `client`。

测试函数只要写参数：

```python
def test_xxx(client: TestClient) -> None:
    ...
```

pytest 就会自动调用这个 fixture，并传入一个 `TestClient` 对象。

### 练习 4 参考答案：区分 schema 测试和 API 测试

题目：

判断下面两个测试分别属于哪类测试：

```python
ChatRequest(message="")
```

```python
client.post("/chat", json={"message": ""})
```

参考答案：

```python
ChatRequest(message="")
```

属于 schema 测试。

它直接测试 Pydantic 模型。

```python
client.post("/chat", json={"message": ""})
```

属于 API 测试。

它通过 FastAPI 路由测试接口行为。

### 练习 5 参考答案：解释状态码

题目：

说明当前项目里这些状态码分别代表什么：

```text
200
422
405
```

参考答案：

```text
200：请求成功，例如正确 POST /chat。
422：请求体能解析，但不符合 Pydantic 模型，例如缺少 message。
405：路径存在，但 HTTP 方法不允许，例如 GET /chat。
```

### 练习 6 参考答案：写一个 /health 测试

题目：

写一个测试，使用 `client` fixture 请求 `/health`，并断言状态码是 200。

参考答案：

```python
from fastapi.testclient import TestClient


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
```

### 练习 7 参考答案：写一个 /chat 失败测试

题目：

写一个测试，向 `/chat` 发送空 JSON：

```json
{}
```

并断言返回 422。

参考答案：

```python
from fastapi.testclient import TestClient


def test_chat_rejects_missing_message(client: TestClient) -> None:
    response = client.post("/chat", json={})

    assert response.status_code == 422
```

## 31. 自测问题

1. pytest 是什么？
2. pytest 默认会发现什么样的测试函数？
3. TestClient 是什么？
4. TestClient 测试接口时是否需要启动 Uvicorn？
5. conftest.py 有什么作用？
6. fixture 是什么？
7. 当前 client fixture 返回什么？
8. schema 测试测什么？
9. API 测试测什么？
10. `client.post("/chat", json={...})` 里的 `json=` 有什么作用？
11. 200、422、405 分别是什么意思？
12. 422 错误里的 `loc` 表示什么？
13. 422 错误里的 `type` 表示什么？
14. 为什么不能只测成功请求？
15. 为什么测试函数名要写清楚？

## 32. 自测参考答案

### 自测 1 参考答案

题目：

pytest 是什么？

答案：

pytest 是 Python 常用测试框架，用来发现、运行测试函数，并报告测试结果。

### 自测 2 参考答案

题目：

pytest 默认会发现什么样的测试函数？

答案：

pytest 通常会发现 `test_` 开头的测试文件和 `test_` 开头的测试函数。

### 自测 3 参考答案

题目：

TestClient 是什么？

答案：

TestClient 是 FastAPI 的测试客户端，可以模拟 HTTP 请求来测试 FastAPI 应用。

### 自测 4 参考答案

题目：

TestClient 测试接口时是否需要启动 Uvicorn？

答案：

不需要。

TestClient 可以直接和 FastAPI 应用通信，不需要手动启动 Uvicorn 服务。

### 自测 5 参考答案

题目：

conftest.py 有什么作用？

答案：

`conftest.py` 可以放 pytest 共享配置和 fixture。

当前项目里，它提供 `client` fixture，并处理测试导入路径。

### 自测 6 参考答案

题目：

fixture 是什么？

答案：

fixture 是测试前准备好的共享对象或上下文，可以被多个测试函数复用。

### 自测 7 参考答案

题目：

当前 client fixture 返回什么？

答案：

返回：

```python
TestClient(create_app())
```

也就是一个绑定当前 FastAPI 应用的测试客户端。

### 自测 8 参考答案

题目：

schema 测试测什么？

答案：

schema 测试测 Pydantic 模型的数据结构和校验规则。

### 自测 9 参考答案

题目：

API 测试测什么？

答案：

API 测试测 FastAPI 接口整体行为，包括路由、请求校验、状态码和响应 JSON。

### 自测 10 参考答案

题目：

`client.post("/chat", json={...})` 里的 `json=` 有什么作用？

答案：

`json=` 会把 Python 字典作为 JSON 请求体发送给接口。

### 自测 11 参考答案

题目：

200、422、405 分别是什么意思？

答案：

```text
200 表示请求成功。
422 表示请求体验证失败。
405 表示 HTTP 方法不允许。
```

### 自测 12 参考答案

题目：

422 错误里的 `loc` 表示什么？

答案：

`loc` 表示错误发生的位置。

例如 `["body", "message"]` 表示请求体里的 `message` 字段有问题。

### 自测 13 参考答案

题目：

422 错误里的 `type` 表示什么？

答案：

`type` 表示错误类型。

例如 `missing` 表示字段缺失，`string_too_short` 表示字符串太短。

### 自测 14 参考答案

题目：

为什么不能只测成功请求？

答案：

因为真实客户端可能传错数据。

后端也必须正确处理错误请求，比如缺字段、类型错、方法不允许。

所以要同时测试成功和失败场景。

### 自测 15 参考答案

题目：

为什么测试函数名要写清楚？

答案：

清楚的测试名能直接说明测试场景和预期行为。

测试失败时，也更容易定位问题。

## 33. 本节小结

这一节把 FastAPI 接口测试系统化了：

```text
conftest.py 提供 client fixture。
TestClient 直接测试 FastAPI app。
schema 测试验证 Pydantic 模型。
API 测试验证 HTTP 行为。
200 测成功。
422 测请求校验失败。
405 测方法不允许。
```

当前测试结果：

```text
14 passed
```

下一节学习：

```text
.env 配置读取
```

下一节会讲：

```text
为什么配置不能写死在代码里
.env 是什么
.env.example 是什么
python-dotenv / pydantic-settings 是什么
API key 后面应该怎么管理
```

## 34. 参考资料

- [FastAPI：Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [FastAPI：TestClient Reference](https://fastapi.tiangolo.com/reference/testclient/)
- [pytest：Fixtures reference](https://docs.pytest.org/en/stable/reference/fixtures.html)
- [pytest：About fixtures](https://docs.pytest.org/en/stable/explanation/fixtures.html)
