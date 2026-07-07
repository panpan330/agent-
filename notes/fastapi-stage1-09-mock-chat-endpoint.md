# FastAPI 阶段 1 第 9 节：模拟 `/chat` 接口

日期：2026-07-07

本节目标：把前面学过的 router、POST、请求体、Pydantic 请求模型、Pydantic 响应模型串起来，完成第一个 `POST /chat` 接口。

这一节先不接大模型。

我们先做一个 mock 聊天接口：

```text
用户发来 message。
服务端返回：你刚才说的是：message。
```

请求：

```json
{
  "message": "请解释 FastAPI 是什么"
}
```

响应：

```json
{
  "reply": "你刚才说的是：请解释 FastAPI 是什么"
}
```

## 1. 本节学什么

本节学习这些内容：

1. 为什么先做 mock，不直接接大模型。
2. `/chat` 接口应该用什么 HTTP 方法。
3. `app/routers/chat.py` 怎么写。
4. `main.py` 怎么注册 `chat.router`。
5. `ChatRequest` 怎么接收请求体。
6. `ChatResponse` 怎么定义响应体。
7. `response_model=ChatResponse` 有什么作用。
8. 正常请求为什么返回 200。
9. 错误请求为什么返回 422。
10. GET 访问 `/chat` 为什么返回 405。
11. 怎么用 pytest 测试 POST 接口。
12. 怎么用 `/docs` 手动测试 POST 接口。

先记住一句话：

```text
模拟 /chat 接口 = 先把 API 输入输出链路跑通，不急着接真实 AI。
```

## 2. 为什么先做 mock

你可能会问：

```text
我们不是要学 AI 吗，为什么不直接接大模型？
```

原因是：

```text
API 基础没稳时，直接接大模型会把问题混在一起。
```

如果一上来就接大模型，出问题时你很难判断：

```text
是 POST 请求错了？
是 JSON body 错了？
是 Pydantic 校验错了？
是 router 没注册？
是 API key 错了？
是模型调用超时？
是网络问题？
是响应格式错了？
```

所以正确顺序是：

```text
先用 mock 响应跑通接口链路。
再接真实模型。
```

mock 不代表没用。

mock 的价值是：

```text
让我们在没有外部依赖的情况下，验证自己的服务接口设计是否正确。
```

## 3. 本节新增了哪些代码

新增文件：

```text
projects/ai-service/app/routers/chat.py
projects/ai-service/tests/test_chat_api.py
```

修改文件：

```text
projects/ai-service/app/main.py
```

新增接口：

```text
POST /chat
```

## 4. `chat.py` 完整代码

文件：

```text
projects/ai-service/app/routers/chat.py
```

代码：

```python
from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse


router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return ChatResponse(reply=f"你刚才说的是：{request.message}")
```

这一段代码把前面几节的知识全部串起来了。

## 5. `from fastapi import APIRouter`

代码：

```python
from fastapi import APIRouter
```

导入路由分组工具。

这一节我们创建的是：

```text
chat router
```

它专门放聊天相关接口。

## 6. 导入 ChatRequest 和 ChatResponse

代码：

```python
from app.schemas.chat import ChatRequest, ChatResponse
```

含义：

```text
ChatRequest 负责校验请求体。
ChatResponse 负责定义响应体。
```

对应上一节：

```python
class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    reply: str = Field(min_length=1)
```

## 7. 创建 chat router

代码：

```python
router = APIRouter(tags=["chat"])
```

创建一个聊天接口分组。

`tags=["chat"]` 的作用是：

```text
在 /docs 自动文档中，把 /chat 接口放到 chat 分组下。
```

它不改变 URL。

URL 仍然由：

```text
@router.post("/chat")
```

决定。

## 8. 定义 POST /chat

代码：

```python
@router.post("/chat", response_model=ChatResponse)
```

拆开：

```text
router          当前 chat router
post            HTTP POST 方法
"/chat"         URL 路径
response_model  响应模型
ChatResponse    这个接口返回的数据结构
```

这行代码表示：

```text
当客户端发 POST /chat 时，执行下面的 chat 函数。
```

## 9. 为什么 /chat 用 POST

`/chat` 要接收用户消息。

请求体：

```json
{
  "message": "请解释 FastAPI 是什么"
}
```

这是客户端提交给服务端的数据。

所以用：

```text
POST /chat
```

而不是：

```text
GET /chat
```

因为 GET 更适合查询，POST 更适合提交数据并触发处理。

## 10. `def chat(request: ChatRequest)`

代码：

```python
def chat(request: ChatRequest) -> ChatResponse:
```

这里最重要的是：

```python
request: ChatRequest
```

FastAPI 看到参数类型是 Pydantic 模型，就会：

```text
从请求 body 读取 JSON。
用 ChatRequest 校验。
校验成功后，把结果传给 request 参数。
```

所以客户端发：

```json
{
  "message": "你好"
}
```

函数里就可以用：

```python
request.message
```

拿到：

```text
你好
```

## 11. `-> ChatResponse`

代码：

```python
def chat(request: ChatRequest) -> ChatResponse:
```

`-> ChatResponse` 是返回类型提示。

它告诉读代码的人和编辑器：

```text
这个函数应该返回 ChatResponse。
```

真正让 FastAPI 明确响应模型的是：

```python
response_model=ChatResponse
```

现在两者都写，是为了让代码更清楚。

## 12. 返回 ChatResponse

代码：

```python
return ChatResponse(reply=f"你刚才说的是：{request.message}")
```

这里做了三件事：

```text
1. 读取 request.message。
2. 拼接一个 mock 回复。
3. 创建 ChatResponse 对象并返回。
```

如果用户发：

```json
{
  "message": "请解释 FastAPI 是什么"
}
```

服务端返回：

```json
{
  "reply": "你刚才说的是：请解释 FastAPI 是什么"
}
```

这不是 AI 回复。

它只是 mock 回复。

目的是测试接口链路。

## 13. main.py 怎么注册 chat router

修改后：

```python
from fastapi import FastAPI

from app.routers import chat, health


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Service",
        description="Python AI service for Java + Python + AI learning project.",
        version="0.1.0",
    )
    app.include_router(health.router)
    app.include_router(chat.router)
    return app


app = create_app()
```

关键新增：

```python
from app.routers import chat, health
```

和：

```python
app.include_router(chat.router)
```

如果忘了：

```python
app.include_router(chat.router)
```

那么 `chat.py` 文件虽然存在，但主应用不知道 `/chat`。

访问 `/chat` 会失败。

## 14. 当前完整执行链路

启动：

```powershell
uv run uvicorn app.main:app --reload
```

请求：

```text
POST /chat
```

完整链路：

```text
1. Uvicorn 加载 app.main:app。
2. app/main.py 执行 create_app()。
3. create_app 创建 FastAPI 应用。
4. include_router 注册 health.router。
5. include_router 注册 chat.router。
6. chat.router 里有 POST /chat。
7. 客户端发送 POST /chat 和 JSON body。
8. FastAPI 读取请求体。
9. FastAPI 用 ChatRequest 校验 JSON。
10. 校验成功后调用 chat(request)。
11. chat 函数创建 ChatResponse。
12. FastAPI 根据 response_model 处理响应。
13. 客户端收到 JSON。
```

## 15. 正常请求为什么返回 200

测试请求：

```json
{
  "message": "请解释 FastAPI 是什么"
}
```

符合 `ChatRequest`：

```text
message 存在。
message 是字符串。
message 不是空字符串。
```

所以 FastAPI 会执行 `chat()`。

函数正常返回 `ChatResponse`。

所以状态码是：

```text
200 OK
```

## 16. 缺少 message 为什么返回 422

请求：

```json
{}
```

不符合：

```python
class ChatRequest(BaseModel):
    message: str
```

因为 `message` 是必填字段。

FastAPI 会在调用 `chat()` 之前就发现错误。

所以：

```text
chat 函数不会执行。
FastAPI 直接返回 422。
```

## 17. 空 message 为什么返回 422

请求：

```json
{
  "message": ""
}
```

`message` 虽然存在，也确实是字符串。

但不满足：

```python
Field(min_length=1)
```

所以校验失败，返回：

```text
422
```

## 18. 数字 message 为什么返回 422

请求：

```json
{
  "message": 123
}
```

不符合：

```python
message: str
```

因为 `123` 是数字，不是字符串。

所以 FastAPI / Pydantic 校验失败，返回：

```text
422
```

## 19. GET /chat 为什么返回 405

我们定义的是：

```python
@router.post("/chat")
```

也就是说：

```text
/chat 只允许 POST。
```

如果你在浏览器地址栏打开：

```text
http://127.0.0.1:8000/chat
```

浏览器默认发：

```text
GET /chat
```

但服务端只有：

```text
POST /chat
```

所以返回：

```text
405 Method Not Allowed
```

这说明路径存在，但 HTTP 方法不允许。

## 20. 404 和 405 的区别

```text
404 Not Found
```

表示：

```text
这个路径找不到。
```

```text
405 Method Not Allowed
```

表示：

```text
路径可能存在，但你用了不允许的 HTTP 方法。
```

例如：

```text
POST /chat 存在。
GET /chat 不允许。
```

所以 GET `/chat` 返回 405 是合理的。

## 21. 本节新增测试

新增文件：

```text
projects/ai-service/tests/test_chat_api.py
```

测试包括：

```text
正常请求返回 mock reply。
缺少 message 返回 422。
空 message 返回 422。
非字符串 message 返回 422。
GET /chat 返回 405。
```

这些测试不是为了凑数量。

它们分别验证了：

```text
正常链路。
请求模型校验。
HTTP 方法限制。
```

## 22. 测试：正常请求

代码：

```python
def test_chat_replies_with_mock_message() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/chat",
        json={"message": "请解释 FastAPI 是什么"},
    )
    data = response.json()

    assert response.status_code == 200
    assert data == {"reply": "你刚才说的是：请解释 FastAPI 是什么"}
```

重点：

```python
client.post(...)
```

表示发送 POST。

```python
json={"message": "..."}
```

表示发送 JSON 请求体。

## 23. 测试：缺少 message

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

表示：

```text
错误发生在 body.message。
错误类型是 missing。
```

## 24. 测试：空 message

代码：

```python
response = client.post("/chat", json={"message": ""})
```

断言：

```python
assert data["detail"][0]["type"] == "string_too_short"
```

表示：

```text
字符串太短。
```

因为 `min_length=1`。

## 25. 测试：非字符串 message

代码：

```python
response = client.post("/chat", json={"message": 123})
```

断言：

```python
assert data["detail"][0]["type"] == "string_type"
```

表示：

```text
期望字符串，但收到的不是字符串。
```

## 26. 测试：GET /chat

代码：

```python
response = client.get("/chat")

assert response.status_code == 405
```

这个测试验证：

```text
/chat 是 POST 接口，不允许 GET。
```

## 27. 用 /docs 手动测试

启动服务：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run uvicorn app.main:app --reload
```

打开：

```text
http://127.0.0.1:8000/docs
```

找到：

```text
POST /chat
```

点击：

```text
Try it out
```

输入：

```json
{
  "message": "请解释 FastAPI 是什么"
}
```

点击执行。

你应该看到：

```json
{
  "reply": "你刚才说的是：请解释 FastAPI 是什么"
}
```

## 28. 用 curl 测试

PowerShell 里可以用：

```powershell
curl.exe -X POST "http://127.0.0.1:8000/chat" `
  -H "Content-Type: application/json" `
  -d "{\"message\":\"请解释 FastAPI 是什么\"}"
```

注意：

```text
Windows PowerShell 中建议写 curl.exe。
```

因为 `curl` 可能是 PowerShell 的别名。

## 29. 为什么现在还不接 AI

当前接口只是：

```python
return ChatResponse(reply=f"你刚才说的是：{request.message}")
```

它没有调用大模型。

这是刻意的。

原因：

```text
先把接口层跑通。
先把请求校验跑通。
先把响应模型跑通。
先把测试跑通。
```

后面接真实模型时，我们只需要把 mock 逻辑替换成模型调用。

接口边界可以保持不变：

```text
输入仍然是 ChatRequest。
输出仍然是 ChatResponse。
```

## 30. 当前 /chat 还缺什么

当前 `/chat` 已经能工作，但还不是完整 AI 聊天。

缺少：

```text
真实大模型调用。
API key 配置。
超时处理。
错误兜底。
日志。
trace_id。
流式输出。
上下文历史。
```

这些后面会逐步加。

现在只要求：

```text
掌握一个 POST JSON API 的完整基本写法。
```

## 31. 和 Java Controller 的类比

FastAPI：

```python
@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return ChatResponse(reply=f"你刚才说的是：{request.message}")
```

Java Spring Boot 类似：

```java
@PostMapping("/chat")
public ChatResponse chat(@RequestBody ChatRequest request) {
    return new ChatResponse("你刚才说的是：" + request.getMessage());
}
```

类比：

| Java Spring Boot | FastAPI |
| --- | --- |
| `@PostMapping("/chat")` | `@router.post("/chat")` |
| `@RequestBody ChatRequest` | `request: ChatRequest` |
| `ChatResponse` DTO | `ChatResponse` Pydantic 模型 |
| Controller 方法 | path operation function |

但 FastAPI 依靠 Pydantic 和类型提示完成很多校验与文档生成。

## 32. 常见错误

### 错误 1：写了 chat.py 但忘了 include_router

现象：

```text
POST /chat 返回 404。
```

原因：

```text
main.py 没有 app.include_router(chat.router)。
```

### 错误 2：用浏览器地址栏测试 /chat

浏览器地址栏发 GET。

但 `/chat` 是 POST。

所以可能返回：

```text
405
```

测试 POST 要用：

```text
/docs
curl
Postman
Apifox
pytest TestClient
```

### 错误 3：忘记 json=

测试里应该写：

```python
client.post("/chat", json={"message": "你好"})
```

不要写成：

```python
client.post("/chat", data={"message": "你好"})
```

`json=` 会按 JSON 请求体发送。

### 错误 4：不理解 422

422 不是服务崩了。

它通常表示：

```text
请求体能解析，但不符合 ChatRequest。
```

### 错误 5：以为 mock 接口没意义

mock 接口非常有意义。

它让我们先验证：

```text
请求体
校验
响应模型
路由注册
自动文档
测试
```

这些基础没问题，再接 AI。

## 33. 本节必须掌握的最小知识

这一节最少要掌握：

```text
/chat 是 POST 接口。
ChatRequest 接收请求体。
ChatResponse 定义响应体。
response_model=ChatResponse 声明响应模型。
chat.router 必须注册到 main.py。
正常请求返回 200。
请求体校验失败返回 422。
GET /chat 返回 405。
TestClient 可以用 client.post(..., json={...}) 测试 POST JSON。
```

## 34. 本节练习

### 练习 1：解释 /chat 为什么用 POST

题目：

用自己的话解释：

```text
为什么 /chat 使用 POST，而不是 GET？
```

### 练习 2：解释接口函数

题目：

解释下面代码：

```python
@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return ChatResponse(reply=f"你刚才说的是：{request.message}")
```

### 练习 3：判断状态码

题目：

根据当前 `/chat` 接口，判断下面请求会返回什么状态码：

A：

```json
{"message": "你好"}
```

B：

```json
{}
```

C：

```json
{"message": ""}
```

D：

```json
{"message": 123}
```

E：

```text
GET /chat
```

### 练习 4：解释 422

题目：

用自己的话解释：

```text
为什么缺少 message 时，/chat 返回 422，而不是进入 chat 函数？
```

### 练习 5：解释 405

题目：

用自己的话解释：

```text
为什么浏览器地址栏打开 /chat 可能返回 405？
```

### 练习 6：写 TestClient POST

题目：

写一段测试代码，用 TestClient 向 `/chat` 发送：

```json
{
  "message": "你好"
}
```

并断言返回：

```json
{
  "reply": "你刚才说的是：你好"
}
```

## 35. 本节练习参考答案

### 练习 1 参考答案：解释 /chat 为什么用 POST

题目：

用自己的话解释：

```text
为什么 /chat 使用 POST，而不是 GET？
```

参考答案：

因为 `/chat` 需要客户端提交用户消息。

用户消息应该放在 JSON 请求体里，而不是塞进 URL。

POST 适合提交数据并触发服务端处理，所以 `/chat` 使用 POST。

### 练习 2 参考答案：解释接口函数

题目：

解释下面代码：

```python
@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return ChatResponse(reply=f"你刚才说的是：{request.message}")
```

参考答案：

`@router.post("/chat")` 表示这个函数处理 `POST /chat`。

`response_model=ChatResponse` 表示响应应该符合 `ChatResponse`。

`request: ChatRequest` 表示请求体要用 `ChatRequest` 校验。

`-> ChatResponse` 表示函数应该返回 `ChatResponse`。

`return ChatResponse(...)` 返回一个 mock 回复。

### 练习 3 参考答案：判断状态码

题目：

根据当前 `/chat` 接口，判断下面请求会返回什么状态码：

A：

```json
{"message": "你好"}
```

B：

```json
{}
```

C：

```json
{"message": ""}
```

D：

```json
{"message": 123}
```

E：

```text
GET /chat
```

参考答案：

| 请求 | 状态码 | 原因 |
| --- | --- | --- |
| A | 200 | `message` 是非空字符串 |
| B | 422 | 缺少必填字段 `message` |
| C | 422 | `message` 是空字符串，不满足 `min_length=1` |
| D | 422 | `message` 不是字符串 |
| E | 405 | `/chat` 只定义了 POST，没有定义 GET |

### 练习 4 参考答案：解释 422

题目：

用自己的话解释：

```text
为什么缺少 message 时，/chat 返回 422，而不是进入 chat 函数？
```

参考答案：

因为 FastAPI 会在调用 `chat()` 之前先用 `ChatRequest` 校验请求体。

缺少 `message` 时，请求体不符合模型。

校验失败后，FastAPI 直接返回 422，不会继续执行 `chat()`。

### 练习 5 参考答案：解释 405

题目：

用自己的话解释：

```text
为什么浏览器地址栏打开 /chat 可能返回 405？
```

参考答案：

浏览器地址栏默认发送 GET 请求。

当前接口只定义了：

```text
POST /chat
```

没有定义：

```text
GET /chat
```

所以用 GET 访问 `/chat` 会返回 405 Method Not Allowed。

### 练习 6 参考答案：写 TestClient POST

题目：

写一段测试代码，用 TestClient 向 `/chat` 发送：

```json
{
  "message": "你好"
}
```

并断言返回：

```json
{
  "reply": "你刚才说的是：你好"
}
```

参考答案：

```python
def test_chat_replies_with_mock_message() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/chat",
        json={"message": "你好"},
    )

    assert response.status_code == 200
    assert response.json() == {"reply": "你刚才说的是：你好"}
```

## 36. 自测问题

1. mock `/chat` 接口有什么意义？
2. `/chat` 为什么使用 POST？
3. `ChatRequest` 在 `/chat` 里负责什么？
4. `ChatResponse` 在 `/chat` 里负责什么？
5. `response_model=ChatResponse` 有什么作用？
6. `request.message` 从哪里来？
7. 为什么缺少 `message` 返回 422？
8. 为什么空 `message` 返回 422？
9. 为什么数字 `message` 返回 422？
10. 为什么 GET `/chat` 返回 405？
11. `chat.py` 写好了，为什么还要修改 `main.py`？
12. `client.post("/chat", json={...})` 里的 `json=` 有什么作用？
13. 当前 `/chat` 是否已经调用真实大模型？
14. 后面接真实模型时，输入输出模型是否可以保持不变？

## 37. 自测参考答案

### 自测 1 参考答案

题目：

mock `/chat` 接口有什么意义？

答案：

mock `/chat` 可以在不依赖真实大模型的情况下，先验证 POST、JSON 请求体、Pydantic 校验、响应模型、路由注册和接口测试链路是否正确。

### 自测 2 参考答案

题目：

`/chat` 为什么使用 POST？

答案：

因为 `/chat` 需要客户端提交用户消息，请求数据应该放在 body 里。

POST 适合提交数据并触发服务端处理。

### 自测 3 参考答案

题目：

`ChatRequest` 在 `/chat` 里负责什么？

答案：

`ChatRequest` 负责接收和校验客户端发来的 JSON 请求体。

### 自测 4 参考答案

题目：

`ChatResponse` 在 `/chat` 里负责什么？

答案：

`ChatResponse` 负责定义服务端返回给客户端的响应结构。

### 自测 5 参考答案

题目：

`response_model=ChatResponse` 有什么作用？

答案：

它告诉 FastAPI 这个接口的响应应该符合 `ChatResponse`，并用于生成文档、序列化响应和过滤输出字段。

### 自测 6 参考答案

题目：

`request.message` 从哪里来？

答案：

它来自客户端发送的 JSON body。

FastAPI 先用 `ChatRequest` 校验请求体，校验成功后生成 `request` 对象，所以可以访问 `request.message`。

### 自测 7 参考答案

题目：

为什么缺少 `message` 返回 422？

答案：

因为 `message` 是 `ChatRequest` 的必填字段。

请求体缺少它时，校验失败，FastAPI 返回 422。

### 自测 8 参考答案

题目：

为什么空 `message` 返回 422？

答案：

因为 `message` 使用了 `Field(min_length=1)`，空字符串长度为 0，不满足要求。

### 自测 9 参考答案

题目：

为什么数字 `message` 返回 422？

答案：

因为 `message` 的类型是 `str`，数字不符合字符串类型要求。

### 自测 10 参考答案

题目：

为什么 GET `/chat` 返回 405？

答案：

因为当前只定义了 `POST /chat`，没有定义 `GET /chat`。

用不允许的 HTTP 方法访问已存在路径，会返回 405。

### 自测 11 参考答案

题目：

`chat.py` 写好了，为什么还要修改 `main.py`？

答案：

因为 router 文件只是定义接口分组。

必须在 `main.py` 里执行：

```python
app.include_router(chat.router)
```

主应用才会注册这些接口。

### 自测 12 参考答案

题目：

`client.post("/chat", json={...})` 里的 `json=` 有什么作用？

答案：

`json=` 会把 Python 字典作为 JSON 请求体发送，并设置合适的 JSON 请求内容类型。

### 自测 13 参考答案

题目：

当前 `/chat` 是否已经调用真实大模型？

答案：

没有。

当前只是 mock 回复：

```python
return ChatResponse(reply=f"你刚才说的是：{request.message}")
```

### 自测 14 参考答案

题目：

后面接真实模型时，输入输出模型是否可以保持不变？

答案：

可以先保持不变。

仍然用 `ChatRequest` 接收用户输入，用 `ChatResponse` 返回回复。

只需要把函数内部的 mock 回复替换成真实模型调用。

## 38. 本节小结

这一节完成了阶段 1 的第一个 POST 接口：

```text
POST /chat
```

它把前面几节串起来：

```text
router 路由拆分
POST 请求
JSON body
ChatRequest 请求模型
ChatResponse 响应模型
response_model
TestClient 接口测试
422 校验错误
405 方法错误
```

当前接口虽然还没有接大模型，但已经具备一个真实 API 的基本形态。

下一节学习：

```text
测试 FastAPI 接口
```

会系统整理：

```text
为什么要测试接口
TestClient 是什么
接口测试和 schema 测试区别
怎么测 200、422、405
怎么组织测试文件
```

## 39. 参考资料

- [FastAPI：Request Body](https://fastapi.tiangolo.com/tutorial/body/)
- [FastAPI：Response Model](https://fastapi.tiangolo.com/tutorial/response-model/)
- [FastAPI：Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [FastAPI：TestClient Reference](https://fastapi.tiangolo.com/reference/testclient/)
