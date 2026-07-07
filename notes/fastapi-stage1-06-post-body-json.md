# FastAPI 阶段 1 第 6 节：POST、请求体和 JSON

日期：2026-07-07

本节目标：学会 HTTP 里 POST、请求体 body、JSON 请求体、`Content-Type: application/json` 是什么。

前面我们已经写过：

```text
GET /health
```

它只是查询服务状态，不需要客户端提交复杂数据。

但是后面要做聊天接口：

```text
POST /chat
```

客户端必须把用户输入发给服务端：

```json
{
  "message": "请解释 FastAPI 是什么"
}
```

这就需要理解：

```text
POST
请求体 body
JSON
Content-Type
```

这一节暂时不讲 Pydantic。Pydantic 是下一节。

## 1. 本节学什么

本节学习这些内容：

1. GET 和 POST 的区别。
2. 为什么 `/health` 用 GET。
3. 为什么 `/chat` 要用 POST。
4. 请求体 body 是什么。
5. JSON 请求体是什么。
6. `Content-Type` 是什么。
7. `application/json` 是什么。
8. URL、查询参数、请求体的区别。
9. 浏览器直接打开 URL 和发送 POST 请求有什么区别。
10. 为什么不能把聊天内容都塞进 URL。
11. FastAPI 后面会怎么接收 JSON。
12. POST 常见错误。

先记住一句话：

```text
GET 常用于获取数据，POST 常用于向服务端提交数据。
```

再记住一句话：

```text
请求体 body 是客户端随请求一起发给服务端的主体数据。
```

## 2. 回顾 GET /health

当前项目有：

```text
GET /health
```

访问：

```text
http://127.0.0.1:8000/health
```

服务端返回：

```json
{
  "status": "ok",
  "service": "ai-service",
  "time": "2026-07-07T08:00:00+00:00"
}
```

这个接口的特点：

```text
客户端不需要提交复杂数据。
客户端只是问：服务是否正常？
服务端返回状态。
```

所以它适合 GET。

## 3. 为什么聊天接口不适合 GET

聊天接口需要客户端提交用户输入。

例如：

```text
请用初学者能听懂的话解释 FastAPI、Uvicorn、Pydantic 的关系
```

如果用 GET，可能会写成：

```text
GET /chat?message=请用初学者能听懂的话解释 FastAPI...
```

这样有几个问题：

```text
1. URL 会变得很长。
2. 中文、空格、特殊符号需要编码。
3. URL 容易被浏览器历史、日志、代理记录。
4. 复杂结构不好表达。
5. 聊天消息更像提交数据，不是简单查询资源。
```

所以聊天接口更适合：

```text
POST /chat
```

把用户消息放到请求体里：

```json
{
  "message": "请解释 FastAPI 是什么"
}
```

## 4. GET 和 POST 的基本区别

先看最简单版本：

| 方法 | 常见用途 | 数据通常放哪里 |
| --- | --- | --- |
| GET | 获取数据 | URL 路径或查询参数 |
| POST | 提交数据 | 请求体 body |

例子：

```text
GET /health
GET /orders/1001
GET /rag/documents?keyword=fastapi
```

这些更像：

```text
我要获取某些信息。
```

再看 POST：

```text
POST /chat
POST /tickets/create
POST /rag/documents
```

这些更像：

```text
我要提交一份数据，让服务端处理。
```

## 5. GET 一定不能有 body 吗

初学阶段先按这个规则使用：

```text
GET 不放请求体。
POST 放请求体。
```

严格说，HTTP 规范和不同实现里有很多细节，但实际工程中：

```text
不要设计依赖 GET body 的接口。
```

因为很多客户端、网关、代理、工具对 GET body 支持并不一致。

所以我们现在按最常见、最稳妥的方式学：

```text
查询用 GET。
提交用 POST。
```

## 6. 请求体 body 是什么

一个 HTTP 请求大概有这些部分：

```text
请求行
请求头 headers
空行
请求体 body
```

例如：

```http
POST /chat HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/json

{
  "message": "请解释 FastAPI 是什么"
}
```

下面这部分就是请求体：

```json
{
  "message": "请解释 FastAPI 是什么"
}
```

它是客户端提交给服务端的主体数据。

## 7. headers 是什么

headers 是请求头。

请求头用来传递请求的附加信息。

比如：

```http
Content-Type: application/json
Authorization: Bearer xxxxx
User-Agent: Mozilla/5.0
```

当前这节重点看：

```http
Content-Type: application/json
```

它告诉服务端：

```text
这次请求体里的数据是 JSON。
```

## 8. Content-Type 是什么

`Content-Type` 是 HTTP header。

它用来说明：

```text
请求体或响应体里的内容是什么类型。
```

常见值：

| Content-Type | 含义 |
| --- | --- |
| `application/json` | JSON 数据 |
| `application/x-www-form-urlencoded` | 普通表单 |
| `multipart/form-data` | 文件上传表单 |
| `text/plain` | 普通文本 |
| `text/html` | HTML 页面 |

我们现在重点学：

```text
application/json
```

因为后面的 AI 服务接口主要传 JSON。

## 9. application/json 是什么

`application/json` 是 JSON 的媒体类型。

也可以先理解成：

```text
告诉服务端：body 里面是 JSON 格式。
```

例如：

```http
Content-Type: application/json

{
  "message": "你好"
}
```

如果你不告诉服务端 Content-Type，服务端可能不知道该怎么解析 body。

所以发送 JSON 请求时，通常要带：

```http
Content-Type: application/json
```

## 10. JSON 是什么

JSON 是一种跨语言数据格式。

示例：

```json
{
  "message": "请解释 FastAPI",
  "temperature": 0.7,
  "stream": false,
  "tags": ["fastapi", "python"]
}
```

它适合 API，因为很多语言都能处理：

```text
Python
Java
JavaScript
Go
Rust
```

Java 后端调用 Python AI 服务时，也很适合用 JSON。

## 11. JSON 和 Python 字典的区别

JSON 长得很像 Python 字典，但不是一回事。

JSON：

```json
{
  "message": "你好",
  "stream": false,
  "metadata": null
}
```

Python 字典：

```python
{
    "message": "你好",
    "stream": False,
    "metadata": None,
}
```

区别：

| 含义 | JSON | Python |
| --- | --- | --- |
| 真 | `true` | `True` |
| 假 | `false` | `False` |
| 空 | `null` | `None` |
| 字符串 | 必须双引号 | 单引号、双引号都可以 |

所以：

```text
接口传输的是 JSON。
Python 程序内部处理的是 Python 对象。
```

中间需要解析和转换。

FastAPI 会帮我们做很多转换。

## 12. URL、查询参数、请求体的区别

看这个 URL：

```text
http://127.0.0.1:8000/search?keyword=fastapi&page=1
```

拆开：

```text
路径 path：/search
查询参数 query：keyword=fastapi&page=1
```

查询参数适合简单筛选：

```text
keyword=fastapi
page=1
size=20
```

请求体适合复杂数据：

```json
{
  "message": "请解释 FastAPI 是什么",
  "history": [
    {"role": "user", "content": "什么是 HTTP？"},
    {"role": "assistant", "content": "HTTP 是..."}
  ],
  "stream": false
}
```

简单理解：

| 位置 | 适合放什么 |
| --- | --- |
| path | 资源路径，比如 `/orders/1001` |
| query | 简单过滤条件，比如 `?page=1` |
| body | 复杂提交数据，比如 JSON 对象 |

## 13. 为什么不能把长文本放 URL

聊天消息可能很长：

```text
请你基于我前面学过的 FastAPI、HTTP、router 路由拆分知识，帮我总结如何设计一个 /chat 接口……
```

如果放 URL：

```text
/chat?message=请你基于我前面学过的...
```

问题很多：

```text
URL 太长。
中文和特殊符号需要编码。
可读性差。
容易出现在浏览器历史记录。
容易出现在服务器访问日志。
复杂结构不好表达。
```

所以聊天内容放请求体更合适。

## 14. 浏览器打开 URL 默认是什么请求

当你在浏览器地址栏输入：

```text
http://127.0.0.1:8000/health
```

浏览器默认发的是：

```text
GET 请求
```

所以浏览器地址栏很适合测试：

```text
GET /health
GET /docs
GET /openapi.json
```

但它不适合直接测试：

```text
POST /chat
```

因为 POST 需要请求体。

你需要用：

```text
/docs 页面
curl
Postman
Apifox
pytest TestClient
前端代码
```

来发送 POST 请求。

## 15. 一个 POST /chat 请求长什么样

后面我们会实现：

```text
POST /chat
```

请求大概是：

```http
POST /chat HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/json

{
  "message": "请解释 FastAPI 是什么"
}
```

拆开：

```text
POST                  HTTP 方法
/chat                 路径
Content-Type          请求头
application/json      说明 body 是 JSON
{...}                 请求体
message               用户消息字段
```

## 16. 一个 POST /chat 响应长什么样

后面模拟接口可能返回：

```json
{
  "reply": "你刚才说的是：请解释 FastAPI 是什么"
}
```

完整一点：

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "reply": "你刚才说的是：请解释 FastAPI 是什么"
}
```

这里响应也有：

```text
状态码
响应头
响应体
```

## 17. FastAPI 后面怎么接收 JSON

下一节会详细讲 Pydantic。

这里先看一个预告：

```python
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
```

然后接口可能写：

```python
@router.post("/chat")
def chat(request: ChatRequest):
    return {"reply": f"你刚才说的是：{request.message}"}
```

FastAPI 会做这些事：

```text
读取请求体。
把 JSON 转成 Python 数据。
根据 ChatRequest 校验字段。
把校验后的对象传给 chat 函数。
```

但这些是第 7 节内容。

本节先知道：

```text
POST 请求可以带 JSON body。
FastAPI 能接收 JSON body。
Pydantic 用来定义和校验 body 的结构。
```

## 18. curl 发送 POST 示例

如果用 curl，POST 请求大概这样：

```powershell
curl.exe -X POST "http://127.0.0.1:8000/chat" `
  -H "Content-Type: application/json" `
  -d "{\"message\":\"请解释 FastAPI 是什么\"}"
```

注意：

```text
Windows PowerShell 里建议用 curl.exe，避免 curl 被别名到 Invoke-WebRequest。
```

当前项目还没有 `/chat`，所以现在运行这个命令会失败或返回 404。

这是正常的。

我们这里只是先看 POST 请求长什么样。

## 19. FastAPI /docs 发送 POST

等 `/chat` 写好后，可以打开：

```text
http://127.0.0.1:8000/docs
```

找到：

```text
POST /chat
```

然后点：

```text
Try it out
```

输入 JSON：

```json
{
  "message": "请解释 FastAPI 是什么"
}
```

再执行。

这比浏览器地址栏更适合测试 POST。

## 20. pytest 里发送 POST

测试里可以这样：

```python
response = client.post(
    "/chat",
    json={"message": "请解释 FastAPI 是什么"},
)
```

这里的：

```python
json={...}
```

会帮你把 Python 字典作为 JSON 请求体发送。

并且通常会自动设置：

```http
Content-Type: application/json
```

后面写 `/chat` 测试时会用到。

## 21. POST 和“创建资源”的关系

很多教程会说：

```text
POST 用于创建资源。
```

这是常见用法，但不是唯一用法。

POST 更宽泛地说是：

```text
把数据提交给服务端，让服务端处理。
```

例如：

```text
POST /tickets/create  创建工单
POST /chat            提交用户消息，生成回复
POST /rag/query       提交问题，执行检索问答
```

`/chat` 不一定创建数据库资源，但它确实需要提交数据并触发处理，所以用 POST 合理。

## 22. GET 和 POST 的安全性误区

不要以为：

```text
POST 比 GET 天然安全。
```

不准确。

如果用的是普通 HTTP：

```text
GET 和 POST 都可能被中间人看到。
```

真正保护传输内容的是：

```text
HTTPS
```

但是 POST 把数据放 body，不会直接出现在 URL 中。

这可以减少：

```text
浏览器历史记录暴露。
URL 日志暴露。
复制链接时把敏感数据带出去。
```

所以：

```text
POST 不是加密。
HTTPS 才负责传输加密。
```

## 23. 常见错误

### 错误 1：用浏览器地址栏测试 POST

浏览器地址栏默认发 GET。

如果你直接打开：

```text
http://127.0.0.1:8000/chat
```

它不是在发：

```text
POST /chat
```

而是在发：

```text
GET /chat
```

如果服务只定义了 POST `/chat`，浏览器地址栏可能返回：

```text
405 Method Not Allowed
```

### 错误 2：忘记 Content-Type

如果你发送 JSON，但没告诉服务端：

```http
Content-Type: application/json
```

服务端可能不知道如何解析请求体。

测试工具里要注意设置。

### 错误 3：JSON 写成 Python 字典格式

错误 JSON：

```json
{
  "message": "你好",
  "stream": False
}
```

这里的 `False` 是 Python 写法，不是 JSON。

正确 JSON：

```json
{
  "message": "你好",
  "stream": false
}
```

### 错误 4：JSON 字符串用单引号

错误：

```json
{
  'message': '你好'
}
```

正确：

```json
{
  "message": "你好"
}
```

JSON 字符串必须用双引号。

### 错误 5：把复杂数据塞进 query

不推荐：

```text
/chat?message=很长很长的一段问题&history=...
```

推荐：

```text
POST /chat
```

body：

```json
{
  "message": "很长很长的一段问题",
  "history": []
}
```

## 24. 本节必须掌握的最小知识

这一节最少要掌握：

```text
GET 常用于获取数据。
POST 常用于提交数据。
请求体 body 是请求里的主体数据。
JSON 是 API 常用的数据格式。
Content-Type 告诉服务端 body 是什么类型。
application/json 表示 body 是 JSON。
浏览器地址栏默认发 GET，不适合测试 POST body。
聊天内容应该放 POST body，不应该塞进 URL。
Pydantic 下一节用来定义和校验 JSON body 结构。
```

## 25. 本节练习

### 练习 1：判断 GET 还是 POST

题目：

下面场景更适合 GET 还是 POST？

```text
1. 查询服务健康状态。
2. 提交用户聊天消息。
3. 查询某个订单详情。
4. 创建一个新工单。
5. 提交一个 RAG 问题进行知识库问答。
```

### 练习 2：识别请求体

题目：

下面请求中，哪一部分是请求体？

```http
POST /chat HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/json

{
  "message": "请解释 FastAPI 是什么"
}
```

### 练习 3：解释 Content-Type

题目：

用自己的话解释：

```http
Content-Type: application/json
```

是什么意思？

### 练习 4：判断 JSON 是否正确

题目：

下面哪个是正确 JSON？为什么？

A：

```json
{
  "message": "你好",
  "stream": false
}
```

B：

```text
{
  'message': '你好',
  'stream': False
}
```

### 练习 5：解释为什么 `/chat` 用 POST

题目：

用自己的话解释：

```text
为什么 /chat 不适合用 GET，而更适合用 POST？
```

### 练习 6：解释浏览器地址栏的问题

题目：

为什么直接在浏览器地址栏打开：

```text
http://127.0.0.1:8000/chat
```

不能等价于发送：

```text
POST /chat
```

### 练习 7：设计 `/chat` 请求 JSON

题目：

设计一个最简单的 `/chat` JSON 请求体，只包含用户消息字段。

## 26. 本节练习参考答案

### 练习 1 参考答案：判断 GET 还是 POST

题目：

下面场景更适合 GET 还是 POST？

```text
1. 查询服务健康状态。
2. 提交用户聊天消息。
3. 查询某个订单详情。
4. 创建一个新工单。
5. 提交一个 RAG 问题进行知识库问答。
```

参考答案：

```text
1. 查询服务健康状态：GET
2. 提交用户聊天消息：POST
3. 查询某个订单详情：GET
4. 创建一个新工单：POST
5. 提交一个 RAG 问题进行知识库问答：POST
```

核心判断：

```text
获取已有信息，通常 GET。
提交数据让服务端处理，通常 POST。
```

### 练习 2 参考答案：识别请求体

题目：

下面请求中，哪一部分是请求体？

```http
POST /chat HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/json

{
  "message": "请解释 FastAPI 是什么"
}
```

参考答案：

请求体是空行后面的 JSON：

```json
{
  "message": "请解释 FastAPI 是什么"
}
```

前面的：

```http
POST /chat HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/json
```

属于请求行和请求头。

### 练习 3 参考答案：解释 Content-Type

题目：

用自己的话解释：

```http
Content-Type: application/json
```

是什么意思？

参考答案：

它表示这次请求体里的内容类型是 JSON。

服务端看到这个请求头，就知道应该按 JSON 格式解析 body。

### 练习 4 参考答案：判断 JSON 是否正确

题目：

下面哪个是正确 JSON？为什么？

A：

```json
{
  "message": "你好",
  "stream": false
}
```

B：

```text
{
  'message': '你好',
  'stream': False
}
```

参考答案：

A 是正确 JSON。

原因：

```text
JSON 字符串使用双引号。
JSON 布尔值使用 false。
```

B 不是正确 JSON。

原因：

```text
单引号不是标准 JSON 字符串写法。
False 是 Python 写法，JSON 里应该写 false。
```

### 练习 5 参考答案：解释为什么 `/chat` 用 POST

题目：

用自己的话解释：

```text
为什么 /chat 不适合用 GET，而更适合用 POST？
```

参考答案：

`/chat` 需要客户端提交用户消息，消息可能很长，也可能包含复杂结构，比如历史对话、是否流式输出、模型参数等。

这些数据不适合放在 URL 里，更适合放在请求体 body 里。

POST 常用于向服务端提交数据并触发处理，所以 `/chat` 更适合用 POST。

### 练习 6 参考答案：解释浏览器地址栏的问题

题目：

为什么直接在浏览器地址栏打开：

```text
http://127.0.0.1:8000/chat
```

不能等价于发送：

```text
POST /chat
```

参考答案：

浏览器地址栏默认发送 GET 请求。

所以直接打开这个 URL 发的是：

```text
GET /chat
```

不是：

```text
POST /chat
```

POST 请求通常需要请求体 body，应该用 `/docs`、curl、Postman、Apifox、pytest 或前端代码发送。

### 练习 7 参考答案：设计 `/chat` 请求 JSON

题目：

设计一个最简单的 `/chat` JSON 请求体，只包含用户消息字段。

参考答案：

```json
{
  "message": "请解释 FastAPI 是什么"
}
```

其中：

```text
message 是字段名。
字段值是用户输入的文本。
```

## 27. 自测问题

1. GET 通常用来做什么？
2. POST 通常用来做什么？
3. 请求体 body 是什么？
4. headers 是什么？
5. `Content-Type` 的作用是什么？
6. `application/json` 表示什么？
7. JSON 和 Python 字典完全一样吗？
8. JSON 里的布尔值和 Python 里的布尔值有什么区别？
9. URL 查询参数适合放什么？
10. 请求体适合放什么？
11. 为什么聊天内容不适合放在 URL 里？
12. 浏览器地址栏默认发送什么请求？
13. 测试 POST 请求可以用哪些工具？
14. FastAPI 后面会用什么来定义和校验 JSON body？

## 28. 自测参考答案

### 自测 1 参考答案

题目：

GET 通常用来做什么？

答案：

GET 通常用来获取数据，例如查询服务状态、查询订单详情、获取文档列表。

### 自测 2 参考答案

题目：

POST 通常用来做什么？

答案：

POST 通常用来向服务端提交数据，让服务端创建资源或执行处理逻辑。

### 自测 3 参考答案

题目：

请求体 body 是什么？

答案：

请求体是 HTTP 请求中承载主体数据的部分，通常放在请求头后面的空行之后。

POST 请求常把 JSON 数据放在 body 里。

### 自测 4 参考答案

题目：

headers 是什么？

答案：

headers 是请求头或响应头，用来传递附加信息，例如内容类型、认证信息、客户端信息等。

### 自测 5 参考答案

题目：

`Content-Type` 的作用是什么？

答案：

`Content-Type` 用来说明请求体或响应体的内容类型。

例如 `Content-Type: application/json` 表示 body 是 JSON。

### 自测 6 参考答案

题目：

`application/json` 表示什么？

答案：

`application/json` 表示内容是 JSON 格式。

发送 JSON 请求体时，通常要设置这个 Content-Type。

### 自测 7 参考答案

题目：

JSON 和 Python 字典完全一样吗？

答案：

不完全一样。

JSON 是跨语言数据格式，Python 字典是 Python 内部数据类型。

它们语法相似，但布尔值、空值、字符串引号规则不同。

### 自测 8 参考答案

题目：

JSON 里的布尔值和 Python 里的布尔值有什么区别？

答案：

JSON 使用：

```json
true
false
```

Python 使用：

```python
True
False
```

大小写不同。

### 自测 9 参考答案

题目：

URL 查询参数适合放什么？

答案：

查询参数适合放简单筛选条件，例如：

```text
page=1
size=20
keyword=fastapi
```

### 自测 10 参考答案

题目：

请求体适合放什么？

答案：

请求体适合放复杂提交数据，例如聊天消息、表单内容、嵌套 JSON、历史对话、创建工单字段等。

### 自测 11 参考答案

题目：

为什么聊天内容不适合放在 URL 里？

答案：

因为聊天内容可能很长，包含中文、空格、特殊符号和复杂结构。

放在 URL 里可读性差，也更容易出现在浏览器历史和服务器访问日志里。

### 自测 12 参考答案

题目：

浏览器地址栏默认发送什么请求？

答案：

浏览器地址栏默认发送 GET 请求。

### 自测 13 参考答案

题目：

测试 POST 请求可以用哪些工具？

答案：

可以用：

```text
FastAPI /docs
curl
Postman
Apifox
pytest TestClient
前端代码
```

### 自测 14 参考答案

题目：

FastAPI 后面会用什么来定义和校验 JSON body？

答案：

会用 Pydantic 的 `BaseModel` 定义请求模型，例如：

```python
class ChatRequest(BaseModel):
    message: str
```

## 29. 本节小结

这一节最重要的是建立这个模型：

```text
POST /chat
        ↓
headers: Content-Type: application/json
        ↓
body: {"message": "..."}
        ↓
FastAPI 读取 JSON body
        ↓
下一节用 Pydantic 定义和校验结构
```

现在先不要急着写 Pydantic。

先确保你能说清楚：

```text
为什么 /health 用 GET。
为什么 /chat 用 POST。
请求体 body 是什么。
JSON 请求体长什么样。
Content-Type: application/json 是什么。
```

下一节学习：

```text
Pydantic 请求模型
```

也就是正式回答：

```text
FastAPI 怎么知道 /chat 的请求体里必须有 message？
message 为什么必须是字符串？
传错了为什么会返回 422？
```

## 30. 参考资料

- [MDN：POST request method](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/POST)
- [MDN：Content-Type header](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Type)
- [MDN：HTTP headers](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers)
- [FastAPI：Request Body](https://fastapi.tiangolo.com/tutorial/body/)
