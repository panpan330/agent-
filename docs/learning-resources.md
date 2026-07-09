# 学习资料清单

维护原则：

- 官方文档优先，用来确认概念、API 和最佳实践。
- GitHub 学习笔记和教程作为辅助，用来补中文解释和练习。
- 视频只作为理解辅助，不用视频替代动手编码。
- 每个资料都要服务当前学习阶段，不为了收藏资料而收藏。
- 学完一个资料，要沉淀到 `notes/`，并用代码验证。

## 1. Python 基础

### 主资料

- [Python 官方教程](https://docs.python.org/3/tutorial/index.html)
  - 用途：确认 Python 语法和语言特性。
  - 使用方式：遇到变量、列表、字典、函数、异常、模块等概念时查官方解释。

- [Datawhale：聪明办法学 Python 第二版](https://github.com/datawhalechina/learn-python-the-smart-way-v2)
  - 用途：中文系统入门资料，偏计算机科学和 AI 学习方向。
  - 使用方式：作为 Python 基础阶段的主要中文参考。

### 辅助资料

- [jackfrued/Python-100-Days](https://github.com/jackfrued/python-100-days)
  - 用途：中文内容完整，覆盖 Python 基础、Web、数据、项目实践。
  - 使用方式：不按 100 天完整照学，只按当前知识点查对应章节。

- [shibing624/python-tutorial](https://github.com/shibing624/python-tutorial)
  - 用途：偏实用教程，包含 Python 基础、高级特性、Web、爬虫等。
  - 使用方式：作为补充例子和复习材料。

### 视频辅助

- [小甲鱼：零基础入门学习 Python](https://www.bilibili.com/video/BV1xs411Q799/)
  - 用途：适合零基础听概念。
  - 使用方式：只看当前知识点对应视频，不刷全集。

## 2. Python 项目环境与 uv

### 主资料

- [uv 官方文档](https://docs.astral.sh/uv/)
  - 用途：确认 uv 的项目管理、依赖管理、虚拟环境、lock 文件用法。

- [uv 项目指南](https://docs.astral.sh/uv/guides/projects/)
  - 用途：学习 `uv init`、`uv add`、`uv run`、`uv sync`。

### 已完成练习

- `projects/python-basics`
- `notes/python-project-environment.md`

## 3. HTTP / JSON / requests

### 主资料

- [MDN：HTTP messages](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Messages)
  - 用途：理解 HTTP 请求和响应的基本结构。

- [MDN：HTTP request methods](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods)
  - 用途：理解 GET、POST、PUT、PATCH、DELETE 等方法的语义。

- [MDN：POST request method](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/POST)
  - 用途：理解 POST 用于向服务端发送数据，以及请求体类型由 `Content-Type` 指明。

- [MDN：Content-Type header](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Type)
  - 用途：理解 `Content-Type: application/json` 表示请求体或响应体的媒体类型。

- [MDN：HTTP response status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status)
  - 用途：理解 200、404、422、500 等状态码。

- [Requests 官方 Quickstart](https://requests.readthedocs.io/en/latest/user/quickstart/)
  - 用途：学习 GET、POST、headers、JSON、timeout 等基础用法。

- [Requests 中文快速上手](https://docs.python-requests.org/projects/cn/zh-cn/latest/user/quickstart.html)
  - 用途：中文辅助理解。

### 辅助练习

- [4GeeksAcademy: Python API Requests Tutorial and Exercises](https://github.com/4GeeksAcademy/python-http-requests-api-tutorial-exercises)
  - 用途：练习 HTTP 请求和 API 调用。

## 4. FastAPI

### 主资料

- [FastAPI 官方 Tutorial](https://fastapi.tiangolo.com/tutorial/)
  - 用途：学习路由、请求参数、响应模型、依赖注入、自动文档。

- [FastAPI Request Body](https://fastapi.tiangolo.com/tutorial/body/)
  - 用途：学习 FastAPI 如何读取 JSON 请求体，并在下一节配合 Pydantic 校验数据。

- [FastAPI Response Model](https://fastapi.tiangolo.com/tutorial/response-model/)
  - 用途：学习 `response_model`、响应文档、响应校验、输出过滤和响应模型边界。

- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
  - 用途：学习 `TestClient`，用 pytest 测试 GET、POST、JSON body 和响应状态码。

- [FastAPI TestClient Reference](https://fastapi.tiangolo.com/reference/testclient/)
  - 用途：查 `TestClient` 的请求方法和行为。

- [FastAPI Settings and Environment Variables](https://fastapi.tiangolo.com/advanced/settings/)
  - 用途：学习 FastAPI 项目中如何集中读取环境变量和 `.env` 配置。

- [FastAPI Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)
  - 用途：学习如何在请求进入路由前、响应返回客户端前统一处理逻辑，例如 trace_id 和请求耗时。

- [FastAPI Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)
  - 用途：学习 `HTTPException`、自定义异常处理器、覆盖默认校验错误响应。

- [FastAPI CORS Middleware](https://fastapi.tiangolo.com/tutorial/cors/)
  - 用途：学习 `CORSMiddleware`、`allow_origins`、`allow_methods`、`allow_headers` 等基础配置。

- [FastAPI HTTPException Reference](https://fastapi.tiangolo.com/reference/exceptions/)
  - 用途：理解 `HTTPException` 的定位，它适合表达客户端请求相关错误，不适合直接暴露服务端内部错误。

- [FastAPI First Steps](https://fastapi.tiangolo.com/tutorial/first-steps/)
  - 用途：理解 `FastAPI()`、path operation、装饰器、`/docs` 和 OpenAPI。

- [FastAPI Bigger Applications - Multiple Files](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
  - 用途：学习 `APIRouter`、多文件路由拆分、`include_router`、`prefix` 和 `tags`。

- [FastAPI APIRouter Reference](https://fastapi.tiangolo.com/reference/apirouter/)
  - 用途：查 `APIRouter`、`prefix`、`tags`、`dependencies` 等参数含义。

- [FastAPI Run a Server Manually](https://fastapi.tiangolo.com/deployment/manually/)
  - 用途：理解 FastAPI、ASGI、Uvicorn 和 `main:app` 的关系。

- [FastAPI GitHub 仓库](https://github.com/fastapi/fastapi)
  - 用途：确认框架定位和官方示例。

### 中文辅助

- [FastAPI-Learning-Example](https://github.com/oinsd/FastAPI-Learning-Example)
  - 用途：中文视频配套示例。

- [fastapi-best-practices-zh-cn](https://github.com/hellowac/fastapi-best-practices-zh-cn)
  - 用途：进阶阶段看项目结构、异步、最佳实践。
  - 注意：不要一开始就看，等基础接口会写后再看。

## 5. Pydantic

### 主资料

- [Pydantic 官方 Get Started](https://pydantic.dev/docs/validation/latest/get-started/)
  - 用途：理解数据校验的作用。

- [Pydantic Models 文档](https://pydantic.dev/docs/validation/latest/concepts/models/)
  - 用途：学习 `BaseModel`、字段类型、嵌套模型、校验错误。

- [Pydantic Fields 文档](https://pydantic.dev/docs/validation/latest/concepts/fields/)
  - 用途：学习 `Field()`、默认值、字段约束和字段说明。

- [Pydantic Error Handling 文档](https://pydantic.dev/docs/validation/latest/errors/errors/)
  - 用途：学习 `ValidationError` 和结构化错误信息。

### 配置相关资料

- [Pydantic Settings Management](https://pydantic.dev/docs/validation/latest/concepts/pydantic_settings/)
  - 用途：学习 `BaseSettings`、`SettingsConfigDict`、环境变量和 `.env` 文件读取。

- [python-dotenv PyPI](https://pypi.org/project/python-dotenv/)
  - 用途：了解 `.env` 文件读取能力来自哪里，知道它通常作为配置读取的底层依赖。

## 6. pytest

### 主资料

- [pytest fixtures reference](https://docs.pytest.org/en/stable/reference/fixtures.html)
  - 用途：理解 `conftest.py`、fixture 共享和测试复用。

- [pytest about fixtures](https://docs.pytest.org/en/stable/explanation/fixtures.html)
  - 用途：从概念上理解 fixture 是测试上下文和准备数据。

## 7. logging 日志

### 主资料

- [Python 官方文档：logging](https://docs.python.org/3/library/logging.html)
  - 用途：理解 `getLogger()`、logger、handler、formatter、日志层级和日志传播。

- [Python 官方文档：Logging HOWTO](https://docs.python.org/3/howto/logging.html)
  - 用途：入门理解日志是什么、什么时候用 `print`、什么时候用 `logging`、各日志级别的含义。

- [Uvicorn Settings - Logging](https://uvicorn.dev/settings/)
  - 用途：理解 Uvicorn 的 `--log-level` 和 `--log-config`。

- [Uvicorn Logging](https://uvicorn.dev/concepts/logging/)
  - 用途：理解 Uvicorn 如何使用 Python logging，以及后续如何自定义更完整的日志配置。

## 8. trace_id 请求追踪

### 主资料

- [FastAPI Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)
  - 用途：理解 middleware 如何在请求前后执行，适合做 trace_id、耗时统计和通用请求日志。

- [Python 官方文档：contextvars](https://docs.python.org/3/library/contextvars.html)
  - 用途：理解 `ContextVar`，用于保存当前请求自己的 trace_id，避免并发请求串号。

- [Python 官方文档：Logging Cookbook](https://docs.python.org/3/howto/logging-cookbook.html)
  - 用途：理解如何给日志补充上下文信息，例如 trace_id。

- [Python 官方文档：uuid](https://docs.python.org/3/library/uuid.html)
  - 用途：理解 `uuid4()` 如何生成随机唯一编号。

## 9. 统一异常处理

### 主资料

- [FastAPI Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)
  - 用途：理解 FastAPI 如何处理 `HTTPException`、自定义异常和 `RequestValidationError`。

- [FastAPI HTTPException Reference](https://fastapi.tiangolo.com/reference/exceptions/)
  - 用途：确认 `HTTPException` 的参数和适用场景。

- [Starlette Exceptions](https://starlette.dev/exceptions/)
  - 用途：理解 FastAPI 底层 Starlette 的异常处理机制，以及为什么要处理 Starlette 的 HTTPException。

- [Python 官方文档：Errors and Exceptions](https://docs.python.org/3/tutorial/errors.html)
  - 用途：复习 Python 异常基础，理解异常是运行时错误以及如何处理。

## 10. CORS 基础

### 主资料

- [FastAPI CORS Middleware](https://fastapi.tiangolo.com/tutorial/cors/)
  - 用途：理解 FastAPI 中如何使用 `CORSMiddleware` 允许指定前端来源访问后端接口。

- [MDN：Cross-Origin Resource Sharing](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS)
  - 用途：理解 CORS 的浏览器机制、请求头、响应头和预检请求。

- [MDN：Same-origin policy](https://developer.mozilla.org/en-US/docs/Web/Security/Same-origin_policy)
  - 用途：理解什么是同源，为什么协议、域名、端口任一不同都算不同源。

## 11. LangChain

### 主资料

- [LangChain 官方 Overview](https://docs.langchain.com/oss/python/langchain/overview)
  - 用途：理解 LangChain 在模型、prompt、tool、agent harness 中的位置。

- [LangChain Python Reference](https://reference.langchain.com/python/langchain)
  - 用途：查 API 细节。

## 12. LangGraph

### 主资料

- [LangGraph 官方 Overview](https://docs.langchain.com/oss/python/langgraph/overview)
  - 用途：理解有状态、长流程、可恢复 agent 编排。

- [LangGraph Quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart)
  - 用途：做第一个最小图流程。

- [LangChain Academy: Introduction to LangGraph](https://academy.langchain.com/courses/intro-to-langgraph)
  - 用途：系统课程辅助理解。

## 13. RAG / 向量库

### 主资料

- [Qdrant 官方文档](https://qdrant.tech/documentation/)
  - 用途：理解向量库、collection、point、filter、search。

- [Qdrant Local Quickstart](https://qdrant.tech/documentation/quickstart/)
  - 用途：后续本地跑 Qdrant 时使用。

### 辅助理解

- [RAGFlow GitHub](https://github.com/infiniflow/ragflow)
  - 用途：观察成熟 RAG 系统的功能边界。
  - 注意：不作为初学主线，先自己实现基础 RAG。

- [RAGFlow 文档](https://ragflow.io/docs/)
  - 用途：参考 RAG 产品化能力，如数据集、解析、引用、问答流程。

## 14. LLM API 基础调用

### 主资料

- [OpenAI Developer quickstart](https://platform.openai.com/docs/quickstart)
  - 用途：理解 OpenAI API 的基本入口、API key、SDK 安装和第一次 API 调用。

- [OpenAI API Reference：Authentication](https://developers.openai.com/api/reference/overview#authentication)
  - 用途：确认 API key 是敏感凭证，应该在服务端通过环境变量或密钥管理服务读取，不要暴露在客户端代码里。

- [OpenAI Python API library](https://developers.openai.com/api/reference/python)
  - 用途：确认 Python SDK 如何读取 `OPENAI_API_KEY`，以及为什么推荐用 `.env` 避免把 key 存进源码。

- [OpenAI SDKs and CLI](https://developers.openai.com/api/docs/libraries)
  - 用途：理解 OpenAI SDK 的安装、环境变量读取和基础使用方式。

- [OpenAI Production best practices](https://platform.openai.com/docs/guides/production-best-practices)
  - 用途：理解生产环境中 API key 不应写进代码或公开仓库，应该通过环境变量或 secret management service 提供给应用。

- [OpenAI Key concepts：Tokens](https://developers.openai.com/api/docs/concepts#tokens)
  - 用途：理解 token 是模型处理文本的基本片段，以及 token、上下文长度和 tokenizer 工具的关系。

- [OpenAI Pricing](https://developers.openai.com/api/docs/pricing)
  - 用途：确认不同模型的 input、cached input、output token 当前价格。价格会变化，需要使用时再查。

- [OpenAI Reasoning models](https://developers.openai.com/api/docs/guides/reasoning)
  - 用途：理解 reasoning tokens、上下文空间、`max_output_tokens` 和成本控制之间的关系。

- [OpenAI Text generation](https://platform.openai.com/docs/guides/text)
  - 用途：理解如何用大语言模型根据 prompt 生成文本，以及为什么阶段 2 优先使用 Responses API。

- [OpenAI Prompt engineering](https://developers.openai.com/api/docs/guides/prompt-engineering)
  - 用途：理解不同消息角色的优先级、developer/user/assistant 的职责，以及为什么 prompt 要在代码里可版本化和可测试。

- [OpenAI Migrate to the Responses API](https://developers.openai.com/api/docs/guides/migrate-to-responses)
  - 用途：理解 Chat Completions 的 `messages` 和 Responses API 的 typed Items 之间的关系，以及多轮对话状态管理方式。

- [OpenAI Models](https://platform.openai.com/docs/models)
  - 用途：了解模型会随时间更新，模型选择要以官方文档为准，不死记某个固定名字。

- [OpenAI Responses API Reference](https://platform.openai.com/docs/api-reference/responses/create)
  - 用途：后续实现真实模型调用时查请求参数、响应结构和流式事件。

- [OpenAI Streaming API responses](https://developers.openai.com/api/docs/guides/streaming-responses)
  - 用途：理解 Chat Completions 和 Completions 通过 `stream=True` 返回流式数据，以及为什么要逐块读取响应。

- [OpenAI Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
  - 用途：理解 Structured Outputs、JSON Schema、JSON Mode 的区别，以及为什么 schema adherence 比只返回 JSON 更稳定。

- [OpenAI API Reference：Chat Completions](https://developers.openai.com/api/reference/resources/chat)
  - 用途：确认 Chat Completions 风格接口的 `model`、`messages` 和响应结构。

- [OpenAI API Reference：Chat Completions create](https://developers.openai.com/api/reference/python/resources/chat/subresources/completions/methods/create/)
  - 用途：确认 `client.chat.completions.create(...)` 的返回结构，以及 `usage` 里的 token 用量信息。

- [OpenAI Conversation state](https://developers.openai.com/api/docs/guides/conversation-state)
  - 用途：理解多轮对话中如何管理上下文状态，以及为什么要主动保存或传递对话状态。

- [OpenAI Python API library：Timeouts](https://developers.openai.com/api/reference/python#timeouts)
  - 用途：确认 OpenAI Python SDK 的 `timeout` 配置方式、默认超时和 `APITimeoutError`。

- [OpenAI Error codes](https://developers.openai.com/api/docs/guides/error-codes)
  - 用途：理解 OpenAI Python SDK 常见异常类型，例如 `APITimeoutError`、`APIConnectionError`、`RateLimitError`。

- [OpenAI Rate limits guide](https://platform.openai.com/docs/guides/rate-limits)
  - 用途：理解模型服务的请求频率、token 用量、限流和 429 错误。

- [FastAPI：StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/)
  - 用途：理解 FastAPI 如何通过生成器或迭代器逐块返回响应内容。

- [FastAPI：Stream Data](https://fastapi.tiangolo.com/advanced/stream-data/)
  - 用途：理解 FastAPI 在流式返回时会原样发送每个 chunk，不会自动转换为 JSON。

- [MDN：Using server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)
  - 用途：理解 SSE 事件流格式、`text/event-stream` 和浏览器如何接收服务端持续推送。

- [MDN：EventSource](https://developer.mozilla.org/en-US/docs/Web/API/EventSource)
  - 用途：理解浏览器 `EventSource` 如何打开 SSE 连接并接收服务端事件。

- [MDN：429 Too Many Requests](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/429)
  - 用途：理解 HTTP 429 的通用语义。

- [Python logging 官方文档](https://docs.python.org/3/library/logging.html)
  - 用途：理解 logger、日志级别、`exc_info` 和日志格式化。

- [Python time.perf_counter 官方文档](https://docs.python.org/3/library/time.html#time.perf_counter)
  - 用途：理解为什么统计调用耗时要用适合测量时间间隔的计时器。

- [阿里云百炼：OpenAI Chat接口兼容](https://help.aliyun.com/zh/model-studio/compatibility-of-openai-with-dashscope)
  - 用途：学习如何用 OpenAI SDK 调用千问兼容接口，重点理解 API Key、BASE_URL 和模型名称三项配置。

- [阿里云百炼：流式输出](https://help.aliyun.com/zh/model-studio/stream)
  - 用途：理解百炼模型流式输出、`stream=True`、`stream_options={"include_usage": true}` 和流式计费说明。

- [阿里云百炼：结构化输出](https://help.aliyun.com/zh/model-studio/qwen-structured-output)
  - 用途：理解千问 OpenAI 兼容接口的 JSON Mode、`response_format={"type": "json_object"}` 和提示词 JSON 关键词要求。

- [阿里云百炼：文本生成模型API参考](https://help.aliyun.com/zh/model-studio/qwen-api-reference/)
  - 用途：理解百炼提供的 OpenAI 兼容 Chat Completions、OpenAI 兼容 Responses、Anthropic 兼容 Messages 和 DashScope 原生接口之间的区别。

- [Pydantic：JSON Schema](https://docs.pydantic.dev/latest/concepts/json_schema/)
  - 用途：理解 Pydantic 如何从 `BaseModel` 生成 JSON Schema，以及为什么下一节可以用 Pydantic 约束模型输出。

- [JSON Schema：Creating your first schema](https://json-schema.org/learn/getting-started-step-by-step)
  - 用途：理解 JSON Schema 如何描述对象、字段、类型、必填项和枚举值。

## 当前阶段推荐资料组合

阶段 2：LLM API 基础调用。当前优先看：

1. 本仓库 `notes/llm-api-stage2-01-what-is-llm-api.md`
2. 本仓库 `notes/llm-api-stage2-02-api-key-env-security.md`
3. 本仓库 `notes/llm-api-stage2-03-token-context-cost.md`
4. 本仓库 `notes/llm-api-stage2-04-openai-compatible-sdk.md`
5. 本仓库 `notes/llm-api-stage2-05-messages-roles.md`
6. 本仓库 `notes/llm-api-stage2-06-prompt-basics.md`
7. 本仓库 `notes/llm-api-stage2-07-real-chat-call.md`
8. 本仓库 `notes/llm-api-stage2-08-multi-turn-history.md`
9. 本仓库 `notes/llm-api-stage2-09-timeout.md`
10. 本仓库 `notes/llm-api-stage2-10-retry-rate-limit.md`
11. 本仓库 `notes/llm-api-stage2-11-model-error-handling.md`
12. 本仓库 `notes/llm-api-stage2-12-llm-call-logging.md`
13. 本仓库 `notes/llm-api-stage2-13-streaming-concept.md`
14. 本仓库 `notes/llm-api-stage2-14-stream-chat-endpoint.md`
15. 本仓库 `notes/llm-api-stage2-15-structured-output-concept.md`
16. OpenAI Developer quickstart，理解 API key、SDK 和第一次 API 调用
17. OpenAI API Reference：Authentication，理解 API key 认证和密钥安全
18. OpenAI Python API library，理解 Python SDK、`.env`、timeouts、retries、错误层级和 `APIStatusError`
19. OpenAI SDKs and CLI，理解 SDK 安装和基础使用
20. OpenAI API Reference：Chat Completions，确认 `model`、`messages` 和 `choices[0].message.content`
21. OpenAI API Reference：Chat Completions create，确认 `usage.prompt_tokens`、`usage.completion_tokens` 和 `usage.total_tokens`
22. OpenAI Streaming API responses，理解 `stream=True` 和逐块读取响应
23. OpenAI Structured model outputs，理解 Structured Outputs、JSON Mode 和 JSON Schema
24. OpenAI Conversation state，理解多轮对话状态管理
25. OpenAI Error codes，理解 SDK 错误类型和错误处理
26. OpenAI Rate limits guide，理解请求频率、token 限额和 429
27. FastAPI StreamingResponse，理解服务端如何逐块返回数据
28. FastAPI Stream Data，理解 FastAPI 不会自动把 chunk 转换成 JSON
29. MDN Using server-sent events，理解 SSE 和 `text/event-stream`
30. MDN EventSource，理解浏览器 SSE 接收方式
31. Python logging 官方文档，理解日志级别、日志格式和 `exc_info`
32. Python time.perf_counter 官方文档，理解模型调用耗时统计
33. MDN 429 Too Many Requests，理解 HTTP 429 通用语义
34. 阿里云百炼：OpenAI Chat接口兼容，理解千问兼容接口的 `api_key`、`base_url`、`model`、`messages` 和 `usage`
35. 阿里云百炼：流式输出，理解 `stream=True`、`stream_options={"include_usage": true}` 和流式计费
36. 阿里云百炼：结构化输出，理解 JSON Mode 和 `response_format={"type": "json_object"}`
37. 阿里云百炼：文本生成模型API参考，理解兼容 Chat Completions 和 Responses 的区别
38. Pydantic JSON Schema，理解 `BaseModel.model_json_schema()`
39. JSON Schema Creating your first schema，理解对象、字段、类型和必填项
40. OpenAI Production best practices，理解生产环境 key 安全和 token 成本估算
41. OpenAI Key concepts：Tokens，理解 token 和上下文窗口
42. OpenAI Pricing，确认当前模型价格
43. OpenAI Reasoning models，理解 reasoning tokens 和 `max_output_tokens`
44. OpenAI Text generation，理解大模型文本生成和 Responses API
45. OpenAI Prompt engineering，理解消息角色、prompt 版本化和测试
46. OpenAI Migrate to the Responses API，理解 `messages` 和 typed Items 的映射
47. OpenAI Models，理解模型选择要看当前官方文档
48. OpenAI Responses API Reference，后续写真实调用时查参数和响应
49. 本仓库 `notes/fastapi-stage1-16-project-summary.md`，复习当前 FastAPI 服务基础
50. 本仓库 `notes/fastapi-stage1-11-env-config.md`，复习 `.env` 配置读取
51. 本仓库 `notes/fastapi-stage1-12-logging.md`，复习日志
52. 本仓库 `notes/fastapi-stage1-13-trace-id.md`，复习请求追踪
53. 本仓库 `notes/fastapi-stage1-14-exception-handling.md`，复习统一异常处理

阶段 1：FastAPI 服务基础已完成。复盘时可看：

1. 本仓库 `notes/fastapi-stage1-01-web-http-api.md`
2. 本仓库 `notes/fastapi-stage1-02-what-is-fastapi.md`
3. 本仓库 `notes/fastapi-stage1-03-ai-service-project-skeleton.md`
4. 本仓库 `notes/fastapi-stage1-04-health-endpoint.md`
5. 本仓库 `notes/fastapi-stage1-05-router-splitting.md`
6. 本仓库 `notes/fastapi-stage1-06-post-body-json.md`
7. 本仓库 `notes/fastapi-stage1-07-pydantic-request-model.md`
8. 本仓库 `notes/fastapi-stage1-08-pydantic-response-model.md`
9. 本仓库 `notes/fastapi-stage1-09-mock-chat-endpoint.md`
10. 本仓库 `notes/fastapi-stage1-10-testing-fastapi-apis.md`
11. 本仓库 `notes/fastapi-stage1-11-env-config.md`
12. 本仓库 `notes/fastapi-stage1-12-logging.md`
13. 本仓库 `notes/fastapi-stage1-13-trace-id.md`
14. 本仓库 `notes/fastapi-stage1-14-exception-handling.md`
15. 本仓库 `notes/fastapi-stage1-15-cors.md`
16. 本仓库 `notes/fastapi-stage1-16-project-summary.md`
17. 本仓库 `notes/fastapi-stage1-project-structure.md`
18. MDN HTTP messages，理解请求和响应
19. MDN HTTP request methods，理解 GET、POST 等方法
20. MDN POST request method，理解 POST 和请求体
21. MDN Content-Type header，理解 `application/json`
22. MDN HTTP response status codes，理解状态码
23. MDN Same-origin policy，理解同源策略和 origin
24. MDN CORS，理解跨源资源共享和预检请求
25. FastAPI First Steps，理解 `FastAPI()`、path operation 和自动文档
26. FastAPI Bigger Applications，理解 router 路由拆分
27. FastAPI Request Body，理解请求体和 Pydantic 的关系
28. FastAPI Response Model，理解响应模型和 `response_model`
29. FastAPI Testing，理解 `TestClient` 如何测试接口
30. FastAPI Settings and Environment Variables，理解环境变量和配置读取
31. FastAPI Middleware，理解请求前后统一处理逻辑
32. FastAPI Handling Errors，理解异常处理器和 `RequestValidationError`
33. FastAPI CORS Middleware，理解 `CORSMiddleware`
34. FastAPI HTTPException Reference，理解 `HTTPException`
35. Starlette Exceptions，理解 FastAPI 底层异常处理机制
36. Python Logging HOWTO，理解日志级别和 `getLogger(__name__)`
37. Python logging 文档，理解 logger、handler、formatter、LogRecord
38. Python contextvars，理解当前请求上下文
39. Python uuid，理解 `uuid4()` 生成唯一编号
40. Python Errors and Exceptions，复习 Python 异常基础
41. Uvicorn Settings - Logging，理解 `--log-level`
42. pytest fixtures reference，理解 `conftest.py` 和 fixture
43. Pydantic Models，理解 `BaseModel`
44. Pydantic Fields，理解 `Field()` 和字段约束
45. Pydantic Settings Management，理解 `BaseSettings` 和 `.env`
46. python-dotenv PyPI，理解 `.env` 文件读取依赖
47. FastAPI 官方 Tutorial，只看当前需要的路由、请求、响应、自动文档
48. uv 官方项目指南，重点复习 `uv sync`、`uv add`、`uv run`
49. HTTP/API 基础笔记 `notes/python-http-api.md`

暂时不要深入：

- FastAPI 复杂最佳实践
- LangChain
- LangGraph
- RAGFlow
- Qdrant

这些后面到对应阶段再看。阶段 1 复盘重点是：能写、能启动、能测试一个基础 API 服务，并能解释项目里每个基础模块的作用。
