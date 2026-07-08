# 阶段 1 第 16 节：阶段 1 项目整理

## 1. 这一节学什么

这一节不是新增一个孤立知识点。

这一节的目标是：

```text
把阶段 1 FastAPI 服务基础整体收尾。
```

你要确认自己不是只跟着写了一堆文件，而是真的理解：

```text
这个项目为什么这样分目录
每个模块负责什么
一次请求进入服务后会经过哪些步骤
接口成功时怎么返回
接口失败时怎么返回
日志和 trace_id 怎么帮助排查问题
配置为什么不能写死
测试为什么能证明功能没有坏
```

阶段 1 完成后，你应该能看懂并讲清楚一个最小 Python AI 服务的基础结构。

## 2. 阶段 1 已完成什么

阶段 1 完成了 16 节：

```text
1. Web 服务、HTTP 和 API 是什么
2. FastAPI 是什么
3. 创建 ai-service 项目骨架
4. FastAPI 最小服务 /health
5. router 路由拆分
6. POST、请求体和 JSON
7. Pydantic 请求模型
8. Pydantic 响应模型
9. 模拟 /chat 接口
10. 测试 FastAPI 接口
11. .env 配置读取
12. logging 日志
13. trace_id 请求追踪
14. 统一异常处理
15. CORS 基础
16. 阶段 1 项目整理
```

这些不是随便排列的。

它们的顺序是从外到内、从简单到工程化：

```text
先理解 HTTP/API
再搭 FastAPI 服务
再写接口
再定义请求和响应模型
再写测试
再加配置、日志、trace_id、异常处理、CORS
最后整理成一个可继续扩展的项目
```

## 3. 阶段 1 的项目位置

项目目录：

```text
projects/ai-service
```

它是后续 Python AI 服务的基础。

当前它还没有接真实大模型。

现在的 `/chat` 是 mock 接口。

这是有意安排的。

原因是：

```text
接大模型之前，先把 Web 服务基础打牢。
```

否则后面一边学大模型 API，一边补 HTTP、FastAPI、Pydantic、配置、日志、异常处理，会很乱。

## 4. 当前项目结构

当前核心结构：

```text
projects/ai-service/
  app/
    core/
      config.py
      cors.py
      exception_handlers.py
      exceptions.py
      logging.py
      trace.py
    middleware/
      tracing.py
    routers/
      chat.py
      health.py
    schemas/
      chat.py
      error.py
    main.py
  tests/
    conftest.py
    test_chat_api.py
    test_chat_schema.py
    test_config.py
    test_cors.py
    test_exception_handlers.py
    test_health.py
    test_logging.py
    test_trace.py
  .env.example
  pyproject.toml
  uv.lock
  README.md
```

你不需要死记。

你要理解每一类目录的职责。

## 5. app/main.py 负责什么

`app/main.py` 是 FastAPI 应用入口。

它负责：

```text
读取配置
配置日志
创建 FastAPI app
注册异常处理器
注册 trace middleware
注册 CORS middleware
注册 router
暴露 app 对象给 uvicorn
```

你可以把它理解成：

```text
应用组装中心。
```

它不应该堆太多业务逻辑。

业务逻辑应该放到 router、service 或其他模块里。

## 6. app/core 负责什么

`app/core` 放项目核心基础能力。

当前包括：

```text
config.py              配置读取
cors.py                CORS 配置
exception_handlers.py  统一异常处理
exceptions.py          项目自定义异常
logging.py             日志配置
trace.py               trace_id 上下文
```

这些都不是某个接口独有的功能。

它们属于整个应用都要用的基础设施。

## 7. app/routers 负责什么

`app/routers` 放路由。

当前包括：

```text
health.py
chat.py
```

路由负责：

```text
定义 URL 路径
定义 HTTP 方法
接收请求模型
返回响应模型
调用后续业务逻辑
```

现在业务很简单，所以 `/chat` 直接返回 mock 响应。

后面接真实大模型时，会把模型调用逻辑逐步拆到 service 层。

## 8. app/schemas 负责什么

`app/schemas` 放 Pydantic 模型。

当前包括：

```text
chat.py
error.py
```

其中：

```text
ChatRequest   /chat 请求体
ChatResponse  /chat 响应体
ErrorResponse 统一错误响应体
```

Pydantic 模型的作用是：

```text
定义数据结构
校验输入
约束输出
生成接口文档
让代码更清楚
```

## 9. app/middleware 负责什么

`app/middleware` 放中间件。

当前有：

```text
tracing.py
```

它负责给每次请求加上：

```text
trace_id
X-Trace-Id 响应头
请求开始日志
请求结束日志
请求耗时
```

middleware 适合处理：

```text
所有请求都要经过的通用逻辑。
```

## 10. tests 负责什么

`tests` 放自动化测试。

当前测试覆盖：

```text
/health
/chat
ChatRequest
ChatResponse
配置读取
日志
trace_id
统一异常处理
CORS
```

自动化测试的意义是：

```text
你改代码后，可以快速确认已有功能没有被改坏。
```

这对后面接大模型尤其重要。

因为 AI 功能本身会更复杂，如果没有测试，改一点东西就容易把前面基础能力弄坏。

## 11. 当前接口

当前有两个正式接口：

```text
GET /health
POST /chat
```

`GET /health` 用于健康检查。

它表示：

```text
服务还活着，可以响应请求。
```

`POST /chat` 是模拟聊天接口。

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

## 12. 当前配置

`.env.example` 当前包含：

```text
APP_NAME
APP_DESCRIPTION
APP_VERSION
MODEL_NAME
REQUEST_TIMEOUT_SECONDS
LOG_LEVEL
CORS_ALLOWED_ORIGINS
OPENAI_API_KEY
```

你要理解：

```text
.env.example 可以提交到 GitHub
.env 是本机真实配置，不提交
```

真正的密钥，比如：

```text
OPENAI_API_KEY
```

以后只能放在 `.env` 或环境变量里。

不能写死到代码里。

## 13. 当前日志能力

当前项目使用 Python 标准库：

```text
logging
```

日志级别来自：

```text
LOG_LEVEL
```

日志格式会带：

```text
时间
级别
logger 名称
trace_id
日志消息
```

例如：

```text
INFO [app.routers.chat] trace_id=abc mock_chat_requested message_length=4
```

这说明：

```text
哪个模块写的日志
属于哪次请求
发生了什么事件
```

## 14. 当前 trace_id 能力

当前每次请求都会有：

```text
trace_id
```

响应头会返回：

```text
X-Trace-Id
```

如果客户端传入：

```text
X-Trace-Id: client-trace-001
```

服务端会复用它。

如果客户端没传，服务端会生成新的。

trace_id 的作用是：

```text
把同一次请求产生的多行日志串起来。
```

## 15. 当前统一异常处理能力

当前错误响应统一为：

```json
{
  "code": "VALIDATION_ERROR",
  "message": "请求参数校验失败",
  "trace_id": "..."
}
```

如果有细节，还会有：

```json
{
  "details": []
}
```

当前已处理：

```text
404 NOT_FOUND
405 METHOD_NOT_ALLOWED
422 VALIDATION_ERROR
业务异常 AppException
未知异常 INTERNAL_SERVER_ERROR
```

这样前端或 Java 服务可以稳定读取：

```text
code
message
trace_id
details
```

## 16. 当前 CORS 能力

当前使用：

```text
CORSMiddleware
```

允许来源来自：

```text
CORS_ALLOWED_ORIGINS
```

默认允许：

```text
http://localhost:5173
http://127.0.0.1:5173
```

这能支持前后端分离开发。

例如前端 Vite 服务在 5173，后端 FastAPI 在 8000。

## 17. 一次成功请求会经历什么

以：

```text
POST /chat
```

为例。

流程大致是：

```text
1. 浏览器或客户端发起请求
2. CORS middleware 判断 Origin 是否允许
3. trace middleware 设置 trace_id
4. FastAPI 匹配 /chat 路由
5. Pydantic 校验请求体 ChatRequest
6. /chat 记录业务日志
7. /chat 返回 ChatResponse
8. trace middleware 写入 X-Trace-Id
9. 客户端收到 JSON 响应
```

这个流程你要能讲出来。

不要求一开始讲得特别专业，但要能说明每一步大概做什么。

## 18. 一次失败请求会经历什么

比如请求：

```text
POST /chat
```

但请求体是：

```json
{}
```

流程大致是：

```text
1. 请求进入服务
2. trace middleware 设置 trace_id
3. FastAPI 找到 /chat
4. Pydantic 发现 message 缺失
5. 抛 RequestValidationError
6. 统一异常处理器捕获
7. 返回统一 ErrorResponse
8. 响应头带 X-Trace-Id
```

响应类似：

```json
{
  "code": "VALIDATION_ERROR",
  "message": "请求参数校验失败",
  "trace_id": "...",
  "details": [
    {
      "type": "missing",
      "loc": ["body", "message"]
    }
  ]
}
```

## 19. 当前测试数量

当前测试通过数量是：

```text
41 passed
```

测试不是为了好看。

测试证明这些能力仍然正常：

```text
接口能调用
模型能校验
配置能读取
日志能记录
trace_id 能生成和传递
错误格式稳定
CORS 行为符合预期
```

## 20. 你应该能讲出来的知识点

阶段 1 结束后，你应该能解释：

```text
HTTP 请求和响应是什么
GET 和 POST 的基本区别
JSON 请求体是什么
FastAPI 的 app 是什么
router 为什么要拆分
Pydantic 请求模型和响应模型有什么用
TestClient 怎么测试接口
.env 和 .env.example 的区别
logging 比 print 强在哪里
trace_id 为什么重要
middleware 是什么
统一异常处理为什么必要
CORS 为什么只在浏览器里常见
```

如果这些现在还不能完整讲出来，没关系。

后面每次用到时还会重复。

学习不是一次记住所有，而是：

```text
第一次建立概念
第二次能看懂
第三次能改代码
第四次能讲给别人听
```

## 21. 你现在还没有学什么

阶段 1 没有接真实大模型。

这些还没学：

```text
真实 LLM API 调用
API key 的实际使用
system prompt / user prompt
streaming 流式输出
结构化输出
tool calling
LangChain
LangGraph
RAG
向量数据库
Docker 部署
```

这不是缺失。

这是阶段安排。

先把 FastAPI 服务基础完成，再进入大模型 API。

## 22. 阶段 1 和下一阶段的关系

下一阶段要学 LLM API。

也就是把现在的 mock：

```python
return ChatResponse(reply=f"你刚才说的是：{request.message}")
```

逐步换成：

```text
调用真实大模型
处理超时
处理错误
记录模型名
记录耗时
保护 API key
支持 streaming
返回结构化结果
```

如果没有阶段 1 的基础，下一阶段会很乱。

现在这些基础已经准备好了。

## 23. 阶段 1 综合练习

### 练习 1

题目：

说出 `projects/ai-service/app/main.py` 的主要职责。

参考答案：

`main.py` 是 FastAPI 应用入口，负责读取配置、配置日志、创建 FastAPI app、注册异常处理器、注册 middleware、注册 router，并暴露 `app` 给 Uvicorn 启动。

### 练习 2

题目：

说出 `app/core` 目录当前放了哪些基础能力。

参考答案：

当前 `app/core` 放了配置读取、CORS 配置、统一异常处理、项目自定义异常、日志配置和 trace_id 上下文。

对应文件包括：

```text
config.py
cors.py
exception_handlers.py
exceptions.py
logging.py
trace.py
```

### 练习 3

题目：

为什么 `/chat` 请求体要用 `ChatRequest`，响应体要用 `ChatResponse`？

参考答案：

因为 Pydantic 模型可以定义数据结构、校验输入、约束输出，并帮助 FastAPI 生成接口文档。

`ChatRequest` 让请求必须包含合法的 `message`。

`ChatResponse` 让响应必须包含合法的 `reply`。

### 练习 4

题目：

为什么真实 `.env` 不应该提交到 GitHub？

参考答案：

因为真实 `.env` 可能包含 API key、数据库密码、内部地址等敏感信息。

提交到 GitHub 会导致密钥泄露。

所以只能提交 `.env.example`，真实 `.env` 留在本机或服务器环境里。

### 练习 5

题目：

为什么日志里不要直接记录完整用户输入？

参考答案：

因为用户输入可能包含隐私、账号、手机号、公司数据或其他敏感内容。

日志可能被长期保存和多人查看，所以当前只记录消息长度，不记录完整输入。

### 练习 6

题目：

`trace_id` 有什么用？

参考答案：

`trace_id` 是一次请求的唯一编号。

它可以把同一次请求产生的多行日志串起来。

排查问题时，可以用响应里的 `trace_id` 去日志中查同一次请求的完整过程。

### 练习 7

题目：

统一错误响应为什么要有 `code`？

参考答案：

`code` 是给程序判断用的稳定错误码。

`message` 是给人看的文案，可能会调整。

前端或 Java 服务应该优先根据 `code` 判断错误类型。

### 练习 8

题目：

CORS 解决什么问题？

参考答案：

CORS 解决浏览器页面跨源读取接口响应的问题。

后端通过 CORS 响应头告诉浏览器哪些 origin 可以访问接口。

CORS 不是后端权限系统。

### 练习 9

题目：

为什么要写自动化测试？

参考答案：

自动化测试可以在改代码后快速确认已有功能没有被破坏。

当前测试覆盖接口、模型、配置、日志、trace_id、异常处理和 CORS，为后续接大模型提供基础保障。

### 练习 10

题目：

阶段 1 结束后，下一阶段为什么适合学习 LLM API？

参考答案：

因为当前已经具备 FastAPI 服务基础：接口、模型、配置、日志、trace_id、异常处理、CORS 和测试。

下一阶段可以专注学习真实大模型调用，而不是同时补 Web 服务基础。

## 24. 阶段 1 自测

### 自测 1

题目：

`GET /health` 的作用是什么？

参考答案：

用于健康检查，确认服务可以正常响应请求。

### 自测 2

题目：

`POST /chat` 当前是真实大模型接口吗？

参考答案：

不是。

当前 `/chat` 是 mock 接口，只返回模拟回复。

真实大模型调用会在下一阶段学习。

### 自测 3

题目：

router 拆分的好处是什么？

参考答案：

router 拆分可以让不同接口模块分开管理，避免所有路由都堆在 `main.py` 中。

项目变大后更清晰、更容易维护。

### 自测 4

题目：

`TestClient` 的作用是什么？

参考答案：

`TestClient` 可以在测试里模拟 HTTP 请求，用 pytest 测试 FastAPI 接口，不需要真的手动启动服务器。

### 自测 5

题目：

`LOG_LEVEL` 有什么作用？

参考答案：

`LOG_LEVEL` 用来控制日志输出级别，例如 `DEBUG`、`INFO`、`WARNING`、`ERROR`。

### 自测 6

题目：

错误响应里的 `trace_id` 有什么用？

参考答案：

调用方可以把错误响应里的 `trace_id` 提供给后端，后端用它查找对应请求的日志。

### 自测 7

题目：

`RequestValidationError` 通常什么时候出现？

参考答案：

当请求参数不符合 FastAPI/Pydantic 模型要求时出现。

例如 `/chat` 缺少 `message` 字段。

### 自测 8

题目：

`CORS_ALLOWED_ORIGINS` 当前用来配置什么？

参考答案：

它用来配置允许跨源访问后端接口的前端来源列表。

多个来源用逗号分隔。

### 自测 9

题目：

为什么阶段 1 不急着接真实大模型？

参考答案：

因为接真实大模型之前，要先掌握 Web API 服务基础。

这样后面学习 LLM API 时，能把注意力放在模型调用、prompt、超时、错误处理和 streaming 上。

### 自测 10

题目：

阶段 1 项目整理完成后，当前项目最重要的价值是什么？

参考答案：

它提供了一个可以继续扩展的 Python AI 服务基础骨架。

后续可以在这个基础上接真实大模型、streaming、结构化输出、LangChain、RAG 和 Agent。

## 25. 阶段 1 小结

阶段 1 已经完成：

```text
FastAPI 服务基础
请求/响应模型
mock 聊天接口
配置读取
日志
trace_id
统一异常处理
CORS
自动化测试
项目文档
```

下一阶段进入：

```text
LLM API 基础调用
```

下一阶段会开始学习：

```text
什么是大模型 API
API key 怎么安全使用
system prompt / user prompt
普通调用
streaming 流式输出
超时和错误处理
结构化输出
```

## 26. 参考资料

阶段 1 的主要参考资料已经分散记录在每节笔记末尾。

当前总复盘建议优先回看：

```text
notes/fastapi-stage1-01-web-http-api.md
notes/fastapi-stage1-04-health-endpoint.md
notes/fastapi-stage1-07-pydantic-request-model.md
notes/fastapi-stage1-10-testing-fastapi-apis.md
notes/fastapi-stage1-11-env-config.md
notes/fastapi-stage1-12-logging.md
notes/fastapi-stage1-13-trace-id.md
notes/fastapi-stage1-14-exception-handling.md
notes/fastapi-stage1-15-cors.md
```
