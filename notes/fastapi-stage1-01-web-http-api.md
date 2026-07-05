# FastAPI 阶段 1 第 1 节：Web 服务、HTTP 和 API 是什么

日期：2026-07-05

本节目标：先不急着写复杂代码，而是把 FastAPI 背后的基础概念讲清楚。

你要先明白：

```text
为什么浏览器能访问后端服务？
为什么一个 URL 能对应一个 Python 函数？
为什么接口会返回 JSON？
为什么后面 AI 服务也要先写成 HTTP API？
```

这些问题弄明白以后，后面学 FastAPI、Pydantic、日志、trace_id、异常处理、RAG 接口都会轻松很多。

## 1. 本节学什么

本节学习 9 个基础概念：

1. 客户端
2. 服务端
3. Web 服务
4. HTTP
5. 请求 Request
6. 响应 Response
7. URL
8. HTTP 方法
9. 状态码、JSON、API

先记住一句话：

```text
Web 服务 = 一个长期运行、等待别人通过 HTTP 来调用的程序。
```

FastAPI 就是帮我们写这种 Web 服务的 Python 框架。

## 2. 先从生活里的例子理解

你可以把一次 HTTP 调用理解成去窗口办业务。

```text
你                 -> 客户端
业务窗口           -> 服务端
你递交的材料       -> 请求 Request
窗口给你的办理结果 -> 响应 Response
窗口编号           -> URL 路径
办理方式           -> HTTP 方法
办理是否成功       -> 状态码
返回的表格内容     -> JSON 数据
```

比如你访问：

```text
http://127.0.0.1:8000/health
```

可以理解成：

```text
我这个客户端，去 127.0.0.1:8000 这个服务端，访问 /health 这个窗口，问服务是否健康。
```

服务端回答：

```json
{
  "status": "ok",
  "service": "ai-service",
  "time": "2026-07-05T09:00:00+00:00"
}
```

这就是一次最小的 API 调用。

## 3. 客户端是什么

客户端就是发起请求的一方。

常见客户端有：

- 浏览器
- 前端网页
- 手机 App
- Java 后端服务
- Python 脚本
- Postman、curl、Apifox 这类接口测试工具
- pytest 里的 `TestClient`

在我们当前项目里，你打开浏览器访问：

```text
http://127.0.0.1:8000/health
```

浏览器就是客户端。

如果后面 Java 后端调用 Python AI 服务：

```text
Java 服务 -> Python FastAPI 服务
```

那 Java 服务就是客户端，Python FastAPI 服务就是服务端。

## 4. 服务端是什么

服务端就是接收请求、处理请求、返回响应的一方。

当前项目里，FastAPI 应用就是服务端程序。

它运行后，会一直等待请求：

```text
uv run uvicorn app.main:app --reload
```

启动以后，它不是运行一下就结束，而是一直等待：

```text
有没有人访问 /health？
有没有人访问 /chat？
有没有人访问 /docs？
```

这和你之前写的普通 Python 脚本不一样。

普通脚本通常是：

```text
运行 -> 执行代码 -> 打印结果 -> 结束
```

Web 服务是：

```text
启动 -> 一直运行 -> 等请求 -> 处理请求 -> 返回响应 -> 继续等请求
```

## 5. Web 服务是什么

Web 服务不是网页本身。

更准确地说：

```text
Web 服务是通过网络提供功能的程序。
```

例如：

- 用户登录服务
- 商品查询服务
- 文件上传服务
- 支付服务
- AI 聊天服务
- RAG 知识库问答服务
- 智能工单创建服务

我们现在做的 `projects/ai-service`，就是未来的 Python AI Web 服务。

它将来会提供这些接口：

```text
GET  /health
POST /chat
POST /stream-chat
POST /rag/query
POST /tickets/extract
```

这些接口不是给人直接“看”的，而是给前端、Java 后端或其他程序“调用”的。

## 6. HTTP 是什么

HTTP 是客户端和服务端之间约定好的通信规则。

你可以先把它理解成：

```text
HTTP = 客户端和服务端说话时共同遵守的格式。
```

如果没有统一规则，客户端和服务端就无法理解对方。

HTTP 规定了很多东西，例如：

- 请求应该长什么样
- 响应应该长什么样
- 怎么表示要读取数据
- 怎么表示要提交数据
- 怎么表示成功
- 怎么表示失败
- 数据类型怎么告诉对方

所以我们写接口时，不是在随便发字符串，而是在遵守 HTTP 规则。

## 7. 请求 Request 是什么

请求是客户端发给服务端的一段信息。

一个 HTTP 请求通常包含：

```text
请求方法 method
请求路径 path
请求头 headers
请求体 body
```

例如：

```text
GET /health HTTP/1.1
Host: 127.0.0.1:8000
```

这个请求的意思是：

```text
我要用 GET 方法访问 /health。
```

后面做 `/chat` 时，请求会更复杂：

```http
POST /chat HTTP/1.1
Content-Type: application/json

{
  "message": "请解释 FastAPI 是什么"
}
```

这里就有请求体 body。

## 8. 响应 Response 是什么

响应是服务端处理完请求后，返回给客户端的信息。

一个 HTTP 响应通常包含：

```text
状态码 status code
响应头 headers
响应体 body
```

例如 `/health` 的响应可以理解成：

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "ok",
  "service": "ai-service"
}
```

其中：

```text
200 OK                  表示成功
Content-Type            表示返回内容的类型
application/json        表示返回的是 JSON
后面的花括号内容         是响应体
```

## 9. URL 是什么

URL 是资源地址。

例如：

```text
http://127.0.0.1:8000/health
```

可以拆成：

```text
http              协议
127.0.0.1         主机地址
8000              端口
/health           路径
```

### 9.1 http

`http` 表示使用 HTTP 协议通信。

以后线上项目常见的是：

```text
https
```

`https` 可以先理解成更安全的 HTTP。

### 9.2 127.0.0.1

`127.0.0.1` 表示本机。

也就是说：

```text
访问 127.0.0.1 = 访问你自己电脑上的服务
```

常见写法还有：

```text
localhost
```

它通常也指向本机。

### 9.3 8000

`8000` 是端口。

你可以把端口理解成一栋楼里的不同房间号。

同一台电脑上可以跑多个服务：

```text
127.0.0.1:8000  FastAPI 服务
127.0.0.1:8080  Java 服务
127.0.0.1:5432  PostgreSQL 数据库
127.0.0.1:6379  Redis
```

端口的作用是区分不同程序。

### 9.4 /health

`/health` 是路径。

路径表示你要访问服务里的哪个功能。

例如：

```text
/health       健康检查
/chat         聊天
/docs         接口文档
/rag/query    知识库问答
```

FastAPI 会根据路径找到对应的 Python 函数。

## 10. HTTP 方法是什么

HTTP 方法表示这次请求想做什么。

最常用的是：

| 方法 | 常见含义 | 例子 |
| --- | --- | --- |
| GET | 获取数据 | 查询服务健康状态 |
| POST | 提交数据 | 发送聊天问题 |
| PUT | 整体更新数据 | 替换一条记录 |
| PATCH | 局部更新数据 | 修改用户昵称 |
| DELETE | 删除数据 | 删除一条任务 |

现阶段你先重点掌握：

```text
GET  = 我要拿数据
POST = 我要提交数据，让服务端处理
```

所以 `/health` 用 GET：

```text
GET /health
```

因为它只是查询服务状态。

后面的 `/chat` 用 POST：

```text
POST /chat
```

因为聊天时要提交一段用户输入：

```json
{
  "message": "请解释 FastAPI"
}
```

## 11. 状态码是什么

状态码是服务端告诉客户端“这次请求结果如何”的数字。

常见状态码：

| 状态码 | 含义 | 初学理解 |
| --- | --- | --- |
| 200 | OK | 成功 |
| 201 | Created | 创建成功 |
| 400 | Bad Request | 请求格式不对 |
| 401 | Unauthorized | 没登录或认证失败 |
| 403 | Forbidden | 没权限 |
| 404 | Not Found | 路径不存在 |
| 422 | Unprocessable Content | 请求数据校验失败 |
| 500 | Internal Server Error | 服务端内部错误 |

后面用 FastAPI 时，你会经常看到：

```text
200 成功
404 路径写错
422 请求体格式不符合 Pydantic 模型
500 代码内部报错
```

这些不是乱码，而是服务端和客户端之间的标准信号。

## 12. JSON 是什么

JSON 是一种数据格式。

它长得很像 Python 字典，但它不是 Python 字典。

JSON 示例：

```json
{
  "name": "panpan",
  "age": 18,
  "skills": ["Java", "Python", "AI"],
  "active": true
}
```

Python 字典示例：

```python
{
    "name": "panpan",
    "age": 18,
    "skills": ["Java", "Python", "AI"],
    "active": True,
}
```

注意区别：

| 内容 | JSON | Python |
| --- | --- | --- |
| 布尔真 | `true` | `True` |
| 布尔假 | `false` | `False` |
| 空值 | `null` | `None` |
| 字符串 | 双引号 | 单引号、双引号都可以 |

FastAPI 很常用 JSON，因为前端、Java、Python、Go、Node.js 都能理解 JSON。

## 13. API 是什么

API 是 Application Programming Interface，应用程序编程接口。

初学时不用背英文，先这样理解：

```text
API = 程序给其他程序调用的功能入口。
```

比如你写了：

```text
GET /health
```

这就是一个 API。

它的作用是：

```text
让其他程序知道 ai-service 是否还活着。
```

再比如后面写：

```text
POST /chat
```

这也是一个 API。

它的作用是：

```text
让其他程序把用户问题发给 Python AI 服务，并拿到 AI 回复。
```

## 14. API 和普通函数有什么关系

普通函数只能在代码内部调用。

例如：

```python
def add(a: int, b: int) -> int:
    return a + b
```

你只能在 Python 代码里这样调用：

```python
result = add(1, 2)
```

API 是把函数暴露给外部程序调用。

例如 FastAPI 里：

```python
@router.get("/health")
def health_check() -> dict[str, object]:
    return {"status": "ok"}
```

这表示：

```text
当外部访问 GET /health 时，执行 health_check 函数。
```

所以可以这样理解：

```text
API = 通过 HTTP 暴露出来的函数入口。
```

这个理解不是完整定义，但非常适合入门阶段。

## 15. 用当前项目理解一次完整流程

当前代码大概是这样：

```python
@router.get("/health")
def health_check() -> dict[str, object]:
    return {
        "status": "ok",
        "service": "ai-service",
        "time": datetime.now(timezone.utc).isoformat(),
    }
```

当你访问：

```text
http://127.0.0.1:8000/health
```

完整流程是：

```text
1. 浏览器作为客户端发出 HTTP 请求
2. 请求方法是 GET
3. 请求路径是 /health
4. Uvicorn 接收到这个请求
5. Uvicorn 把请求交给 FastAPI
6. FastAPI 查找哪个函数绑定了 GET /health
7. 找到 health_check 函数
8. 执行 health_check 函数
9. 函数返回 Python 字典
10. FastAPI 把 Python 字典转成 JSON
11. 服务端返回 HTTP 响应
12. 浏览器显示 JSON 结果
```

这一整套，就是 FastAPI 服务最核心的工作方式。

## 16. 和 Java 后端的类比

你有 Java 基础，可以这样对比：

| Java / Spring Boot | Python / FastAPI |
| --- | --- |
| `@RestController` | `FastAPI()` + router |
| `@GetMapping("/health")` | `@router.get("/health")` |
| `@PostMapping("/chat")` | `@router.post("/chat")` |
| DTO 请求对象 | Pydantic 请求模型 |
| DTO 响应对象 | Pydantic 响应模型 |
| Controller 方法 | Python 接口函数 |
| Spring Boot 内嵌服务器 | Uvicorn |

但是注意：

```text
不要因为 Java 里见过 Controller，就跳过 FastAPI 基础。
```

框架不一样，很多细节也不一样：

- Python 类型提示和 Java 强类型不一样。
- Pydantic 的校验方式和 Java Bean Validation 不完全一样。
- FastAPI 的依赖注入和 Spring 的 DI 不是一回事。
- Python 异步模型和 Java 线程模型也不一样。

所以我们会重新学。

## 17. 本节必须掌握的最小知识

这一节你不需要记住所有专业词。

先记住这些：

```text
客户端：发请求的一方
服务端：接请求、处理请求、返回结果的一方
HTTP：客户端和服务端通信的规则
请求：客户端发给服务端的信息
响应：服务端返回给客户端的信息
URL：要访问的地址
GET：通常用于获取数据
POST：通常用于提交数据
状态码：表示请求成功还是失败
JSON：接口常用的数据格式
API：程序暴露给其他程序调用的功能入口
```

## 18. 本节运行观察

进入项目：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
```

启动服务：

```powershell
uv run uvicorn app.main:app --reload
```

打开：

```text
http://127.0.0.1:8000/health
```

你应该看到类似：

```json
{
  "status": "ok",
  "service": "ai-service",
  "time": "2026-07-05T09:00:00+00:00"
}
```

再打开：

```text
http://127.0.0.1:8000/docs
```

这是 FastAPI 自动生成的 API 文档。

## 19. 常见误区

### 误区 1：以为 API 就是网页

API 不是普通网页。

网页主要给人看。

API 主要给程序调用。

`/docs` 是网页，因为它是文档页面。

`/health` 是 API，因为它返回结构化 JSON 数据。

### 误区 2：以为 URL 只是一串地址

URL 不是随便写的。

它包含协议、主机、端口、路径。

后端开发必须能拆开看 URL。

### 误区 3：以为 GET 和 POST 只是名字不同

GET 通常用于拿数据。

POST 通常用于提交数据。

后面做 `/chat` 时，用户消息要放在请求体里，所以更适合 POST。

### 误区 4：以为返回字典就是返回 Python 对象

FastAPI 接口返回给客户端的不是 Python 字典本身。

流程是：

```text
Python 字典 -> FastAPI 转换 -> JSON -> HTTP 响应 -> 客户端
```

客户端拿到的是 JSON。

### 误区 5：看见 422 就慌

FastAPI 里 422 很常见。

它通常表示：

```text
你的请求数据格式和 Pydantic 模型要求的不一致。
```

后面学 Pydantic 时会重点讲。

## 20. 本节练习

### 练习 1：拆 URL

把下面这个 URL 拆成协议、主机、端口、路径：

```text
http://127.0.0.1:8000/health
```

### 练习 2：判断客户端和服务端

下面这个调用里，谁是客户端，谁是服务端？

```text
浏览器 -> http://127.0.0.1:8000/health
```

### 练习 3：判断 GET 还是 POST

下面这些场景应该用 GET 还是 POST？

1. 查询服务是否健康。
2. 提交用户聊天内容。
3. 查询某个订单详情。
4. 创建一个新工单。

### 练习 4：解释状态码

用自己的话解释：

```text
200
404
422
500
```

### 练习 5：解释 `/health`

用自己的话解释：

```text
为什么访问 /health 会执行 health_check 函数？
```

## 21. 本节练习参考答案

### 练习 1 参考答案

```text
协议：http
主机：127.0.0.1
端口：8000
路径：/health
```

### 练习 2 参考答案

```text
客户端：浏览器
服务端：运行在 127.0.0.1:8000 的 FastAPI 服务
```

### 练习 3 参考答案

1. 查询服务是否健康：GET
2. 提交用户聊天内容：POST
3. 查询某个订单详情：GET
4. 创建一个新工单：POST

这里不是绝对死记硬背，而是看语义：

```text
获取数据，优先 GET。
提交数据、创建东西、触发处理，优先 POST。
```

### 练习 4 参考答案

```text
200：请求成功。
404：路径不存在，服务端找不到这个接口。
422：请求数据格式不对，FastAPI/Pydantic 校验失败。
500：服务端代码内部出错。
```

### 练习 5 参考答案

因为代码里写了：

```python
@router.get("/health")
def health_check() -> dict[str, object]:
    ...
```

`@router.get("/health")` 把 `GET /health` 这个 HTTP 请求绑定到了 `health_check` 函数。

所以当客户端访问 `/health` 时，FastAPI 会找到并执行这个函数。

## 22. 自测问题

1. 什么是客户端？
2. 什么是服务端？
3. Web 服务和普通 Python 脚本有什么区别？
4. HTTP 是什么？
5. 一个 HTTP 请求通常包含哪些部分？
6. 一个 HTTP 响应通常包含哪些部分？
7. URL 里的端口有什么用？
8. GET 和 POST 最常见的区别是什么？
9. 状态码 200、404、422、500 分别是什么意思？
10. JSON 和 Python 字典完全一样吗？
11. API 是什么？
12. 为什么说 `/health` 是一个 API？

## 23. 自测参考答案

1. 客户端是发起请求的一方，比如浏览器、前端、Java 服务、测试工具。

2. 服务端是接收请求、处理请求、返回响应的一方，比如当前 FastAPI 服务。

3. 普通 Python 脚本通常运行一次就结束；Web 服务会长期运行，等待请求，处理请求，再继续等待。

4. HTTP 是客户端和服务端通信时共同遵守的规则。

5. 一个 HTTP 请求通常包含请求方法、请求路径、请求头、请求体。

6. 一个 HTTP 响应通常包含状态码、响应头、响应体。

7. 端口用来区分同一台机器上的不同服务程序。

8. GET 通常用于获取数据；POST 通常用于提交数据或触发服务端处理。

9. `200` 表示成功；`404` 表示路径不存在；`422` 表示请求数据校验失败；`500` 表示服务端内部错误。

10. 不完全一样。JSON 是跨语言数据格式，Python 字典是 Python 自己的数据类型。例如 JSON 用 `true`，Python 用 `True`。

11. API 是程序暴露给其他程序调用的功能入口。

12. 因为 `/health` 可以被客户端通过 HTTP 调用，并返回结构化 JSON 数据，用来检查服务状态。

## 24. 本节小结

这一节不是为了写很多代码，而是为了建立后端服务的基本脑图。

你现在应该能说清楚：

```text
客户端通过 HTTP 请求访问 URL。
服务端根据方法和路径找到对应函数。
函数处理后返回数据。
FastAPI 把 Python 数据转成 JSON。
客户端收到 HTTP 响应和状态码。
```

下一节再学：

```text
FastAPI 是什么，以及它到底帮我们省了哪些事。
```

## 25. 参考资料

- [MDN：HTTP messages](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Messages)
- [MDN：HTTP request methods](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods)
- [MDN：HTTP response status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status)
- [FastAPI 官方 Tutorial](https://fastapi.tiangolo.com/tutorial/)
