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

### HTTPX 跨服务调用

- [HTTPX Quickstart](https://www.python-httpx.org/quickstart/)
  - 用途：学习 `httpx.Client`、GET 请求、读取 JSON 响应和基础请求写法。
- [HTTPX Timeouts](https://www.python-httpx.org/advanced/timeouts/)
  - 用途：理解跨服务 HTTP 调用为什么必须配置 timeout，以及 timeout 不是可选细节。
- [HTTPX Exceptions](https://www.python-httpx.org/exceptions/)
  - 用途：理解 `TimeoutException`、`RequestError` 等异常层级，方便把底层错误映射成项目统一错误码。
- [HTTPX Transports and MockTransport](https://www.python-httpx.org/advanced/transports/)
  - 用途：学习测试时如何模拟 HTTP 响应，避免单元测试依赖真实外部服务。

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

- [LangChain Models](https://docs.langchain.com/oss/python/langchain/models)
  - 用途：理解 ChatModel 的 `invoke()`、`stream()`、`batch()` 等基础调用方式。

- [LangChain Messages](https://docs.langchain.com/oss/python/langchain/messages)
  - 用途：理解 `SystemMessage`、`HumanMessage`、`AIMessage` 和 `ToolMessage` 的角色。

- [LangChain ChatOpenAI integration](https://docs.langchain.com/oss/python/integrations/chat/openai)
  - 用途：理解 `langchain-openai`、`ChatOpenAI`、`base_url`、`api_key` 和 OpenAI-compatible 调用边界。

- [LangChain Agents](https://docs.langchain.com/oss/python/langchain/agents)
  - 用途：理解 agent loop、model、tools、system prompt、structured output 和 harness 的关系。

- [LangChain Tools](https://docs.langchain.com/oss/python/langchain/tools)
  - 用途：理解 LangChain 如何把 Python callable 包装成模型可请求的工具。

- [LangChain Structured output](https://docs.langchain.com/oss/python/langchain/structured-output)
  - 用途：理解 LangChain 结构化输出的 provider strategy、tool strategy、Pydantic schema 和错误处理。

- [LangChain Python Reference](https://reference.langchain.com/python/langchain)
  - 用途：查 API 细节。

## 12. LangGraph

### 主资料

- [LangGraph 官方 Overview](https://docs.langchain.com/oss/python/langgraph/overview)
  - 用途：理解有状态、长流程、可恢复 agent 编排。

- [LangGraph Quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart)
  - 用途：做第一个最小图流程。

- [LangGraph Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents)
  - 用途：理解固定工作流和动态 Agent 的区别。

- [LangChain Academy: Introduction to LangGraph](https://academy.langchain.com/courses/intro-to-langgraph)
  - 用途：系统课程辅助理解。

## 13. RAG / 向量库

### 主资料

- [LangChain Retrieval](https://docs.langchain.com/oss/python/langchain/retrieval)
  - 用途：理解 RAG 的检索、文档索引、retriever 和把检索结果交给模型回答的整体方向。

- [OpenAI Embeddings Guide](https://developers.openai.com/api/docs/guides/embeddings)
  - 用途：理解 embedding 是什么，文本为什么可以变成向量，以及 embedding 在搜索、聚类、推荐和 RAG 里的作用。

- [Qdrant 官方文档](https://qdrant.tech/documentation/)
  - 用途：理解向量库、collection、point、filter、search。

- [Qdrant Local Quickstart](https://qdrant.tech/documentation/quickstart/)
  - 用途：后续本地跑 Qdrant 时使用。

- [Qdrant Points](https://qdrant.tech/documentation/manage-data/points/)
  - 用途：理解 Qdrant 的 point 是 vector + payload 的记录，是后续文档 chunk 入库的基础。

- [Qdrant Filtering](https://qdrant.tech/documentation/search/filtering/)
  - 用途：理解 payload filter，后续做文档类型、来源、权限过滤时会用到。

- [Milvus 官方文档](https://milvus.io/docs)
  - 用途：阶段 4 后半段理解 Milvus 的向量数据库定位、安装、collection、index 和搜索能力。

- [Milvus Docker Compose 安装](https://milvus.io/docs/install_standalone-docker-compose.md)
  - 用途：后续本地启动 Milvus Standalone 时使用。

- [Milvus Basic Vector Search](https://milvus.io/docs/single-vector-search.md)
  - 用途：理解 Milvus 基础 ANN 向量搜索流程。

- [Milvus Index Explained](https://milvus.io/docs/index-explained.md)
  - 用途：理解向量索引的作用、成本和召回率取舍。

- [LangChain Milvus integration](https://docs.langchain.com/oss/python/integrations/vectorstores/milvus)
  - 用途：理解 LangChain 如何接入 Milvus vector store。

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

## 15. Tool Calling / 工具调用

### 主资料

- [OpenAI Function Calling Guide](https://developers.openai.com/api/docs/guides/function-calling)
  - 用途：理解模型如何根据工具定义返回工具调用，以及工具调用为什么需要开发者在后端执行。

- [OpenAI Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
  - 用途：和 Function Calling 对比，理解什么时候只是约束模型输出格式，什么时候需要连接工具、函数或外部数据。

- [OpenAI Tools Guide](https://platform.openai.com/docs/guides/tools)
  - 用途：理解 OpenAI API 中 tools 的整体定位，后续区分函数工具、内置工具和 agent 工作流。

- [OpenAI Responses API Reference](https://platform.openai.com/docs/api-reference/responses/create)
  - 用途：后续实现真实工具调用时查 `tools`、工具调用输出和响应结构。

- [OpenAI Safety Best Practices](https://developers.openai.com/api/docs/guides/safety-best-practices)
  - 用途：理解上线 AI 应用时为什么需要对抗测试、人类审核和安全边界。

- [OpenAI API Key Safety](https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety)
  - 用途：复习 API key 为什么不能放到客户端、仓库或模型上下文里。

- [RFC 9110：HTTP Semantics，Idempotent Methods](https://datatracker.ietf.org/doc/html/rfc9110#section-9.2.2)
  - 用途：理解“同一个请求执行一次和多次，服务端预期效果相同”这个幂等性基础定义。

- [Stripe：Idempotent requests](https://docs.stripe.com/api/idempotent_requests)
  - 用途：学习真实 API 如何用 idempotency key 防止连接错误和重试导致重复创建或重复更新。

- [阿里云百炼：Function Calling](https://help.aliyun.com/zh/model-studio/qwen-function-calling)
  - 用途：理解千问兼容模型里的工具调用流程、工具定义和多轮调用方式。

- [阿里云百炼：结构化输出](https://help.aliyun.com/zh/model-studio/qwen-structured-output)
  - 用途：理解千问兼容模型里的 JSON 输出能力，并和 Function Calling 的外部工具调用能力区分开。

- [JSON Schema：Creating your first schema](https://json-schema.org/learn/getting-started-step-by-step)
  - 用途：理解工具参数为什么要用 schema 描述，以及 `type`、`properties`、`required` 的含义。

- [JSON Schema：Object](https://json-schema.org/understanding-json-schema/reference/object)
  - 用途：理解 `properties`、`required` 和 `additionalProperties` 如何约束对象字段。

- [JSON Schema：Enumerated values](https://json-schema.org/understanding-json-schema/reference/enum)
  - 用途：理解 `enum` 如何限制字段只能取固定值。

- [Pydantic：JSON Schema](https://pydantic.dev/docs/validation/latest/concepts/json_schema/)
  - 用途：理解 Pydantic 如何从 `BaseModel` 生成 JSON Schema，后续用于工具参数说明。

- [OWASP Top 10 for Large Language Model Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
  - 用途：理解 LLM 应用里的 Prompt Injection、Insecure Output Handling、Excessive Agency 等风险分类。

- [OWASP LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
  - 用途：理解用户输入、外部文档或网页内容如何诱导模型偏离原始规则。

- [OWASP LLM Top 10 2025 Risks and Mitigations](https://genai.owasp.org/llm-top-10/)
  - 用途：理解生成式 AI 应用的 2025 风险框架，后续设计工具权限和人工确认时参考。

### 本仓库笔记

- [阶段 3 第 1 节：Tool Calling 是什么](../notes/tool-calling-stage3-01-what-is-tool-calling.md)
  - 用途：用智能工单 Agent 场景理解 Tool Calling 的边界、流程、安全要求和 Java 集成关系。

- [阶段 3 第 2 节：为什么 AI 不能直接操作业务系统](../notes/tool-calling-stage3-02-why-ai-cannot-operate-business-system-directly.md)
  - 用途：理解模型输出为什么是“不可信输入”，以及权限、确认、幂等、审计为什么必须由后端控制。

- [阶段 3 第 3 节：工具参数和 JSON Schema](../notes/tool-calling-stage3-03-tool-parameters-json-schema.md)
  - 用途：理解工具参数 schema 的基本写法，以及 `type`、`properties`、`required`、`enum`、`additionalProperties` 的含义。

- [阶段 3 第 4 节：结构化输出 vs Tool Calling](../notes/tool-calling-stage3-04-structured-output-vs-tool-calling.md)
  - 用途：区分“按固定格式返回数据”和“请求调用外部工具”，理解二者在智能工单 Agent 中如何组合使用。

- [阶段 3 第 5 节：用 fake tool 模拟查订单](../notes/tool-calling-stage3-05-fake-query-order-tool.md)
  - 用途：用本地 Python 函数模拟未来 Java 订单服务，理解工具输入、工具输出、fake 数据和统一错误响应。

- [阶段 3 第 6 节：工具调用结果也要 Pydantic 校验](../notes/tool-calling-stage3-06-tool-result-pydantic-validation.md)
  - 用途：理解工具返回结果、Java API 响应和第三方接口返回都属于外部输入，进入业务逻辑前也要校验成 Pydantic 对象。

- [阶段 3 第 7 节：工具调用错误处理：超时、404、500](../notes/tool-calling-stage3-07-tool-error-handling.md)
  - 用途：理解工具调用失败时如何把底层 timeout、404、上游 500 转换成统一、安全、可测试的 API 错误。

- [阶段 3 第 8 节：工具调用权限边界](../notes/tool-calling-stage3-08-tool-permission-boundary.md)
  - 用途：理解模型只能请求工具，后端必须通过工具注册表、启用状态、用户确认和风险等级决定是否执行。

- [阶段 3 第 9 节：工具调用幂等性](../notes/tool-calling-stage3-09-tool-idempotency.md)
  - 用途：理解 `Idempotency-Key`、参数指纹、重复请求复用结果和同 key 不同参数冲突。

- [阶段 3 第 10 节：用 FastAPI 写一个最小 Java mock 业务服务](../notes/tool-calling-stage3-10-java-mock-service.md)
  - 用途：理解 mock service、业务服务边界、`/orders/{order_id}` 路径参数、统一错误响应和跨服务调用准备。

- [阶段 3 第 11 节：Python AI 服务调用 Java mock API](../notes/tool-calling-stage3-11-python-calls-java-mock-api.md)
  - 用途：理解跨服务 HTTP 调用、`JavaOrderClient`、`base_url`、timeout、上游错误映射、DTO 字段映射、Pydantic 二次校验和 `httpx.MockTransport` 测试。
- [阶段 3 第 12 节：让模型决定是否调用工具](../notes/tool-calling-stage3-12-model-decides-tool-call.md)
  - 用途：理解 `tools`、`tool_choice="auto"`、`tool_calls`、模型工具选择、后端工具白名单、工具参数 JSON 解析和 Pydantic 二次校验。

- [阶段 3 第 13 节：工具调用结果再交给模型总结](../notes/tool-calling-stage3-13-tool-result-model-summary.md)
  - 用途：理解 assistant tool-call message、`tool_call_id`、tool message、工具结果 JSON 序列化、第二轮模型总结，以及为什么工具执行失败时不能让模型假装成功。

- [阶段 3 第 14 节：用户确认机制：敏感操作不能直接执行](../notes/tool-calling-stage3-14-user-confirmation.md)
  - 用途：理解 human-in-the-loop、确认计划、操作者和参数绑定、参数指纹、确认过期、确认幂等，以及为什么确认不等于执行。

- [阶段 3 第 15 节：创建工单流程：提取字段、确认、调用 Java API](../notes/tool-calling-stage3-15-ticket-creation-workflow.md)
  - 用途：理解自然语言如何变成后端业务命令、确认计划如何被消费、Python AI 服务如何调用 Java 业务服务、写操作为什么要幂等，以及跨服务返回值为什么仍要 Pydantic 校验。

- [阶段 3 第 16 节：工具调用日志和 trace_id 串联](../notes/tool-calling-stage3-16-tool-logging-trace-id.md)
  - 用途：理解工具调用链路为什么必须可排查、`trace_id` 如何关联入口日志和跨服务调用、出站 `X-Trace-Id` 如何传递、工具执行日志应该记录什么以及哪些敏感内容不能进日志。

- [阶段 3 第 17 节：工具调用测试：fake Java API / fake tool](../notes/tool-calling-stage3-17-tool-testing-fakes.md)
  - 用途：理解 fake、mock、stub、dependency override、`httpx.MockTransport` 的区别，掌握模型 fake、工具 fake、HTTP client 测试和 FastAPI router 测试的分层方式。

- [阶段 3 第 18 节：LangChain 是什么，为什么现在才引入](../notes/tool-calling-stage3-18-what-is-langchain.md)
  - 用途：理解 LangChain 的框架定位、它封装了什么、不负责什么，以及它和当前项目手写工具调用链路、LangGraph、LangSmith 的关系。

- [阶段 3 第 19 节：LangChain ChatModel 基础](../notes/tool-calling-stage3-19-langchain-chatmodel-basics.md)
  - 用途：理解 ChatModel、`ChatOpenAI`、`SystemMessage`、`HumanMessage`、`AIMessage`、`invoke()`，以及 `/chat` 原生 SDK 调用和 `/langchain-chat` LangChain 调用的区别。

- [阶段 3 第 20 节：LangChain Tool 基础](../notes/tool-calling-stage3-20-langchain-tool-basics.md)
  - 用途：理解 LangChain Tool、`StructuredTool`、`args_schema`、工具名和描述，以及 LangChain Tool 与项目 `ToolDefinition`、权限边界和 Pydantic 校验的关系。

- [阶段 3 第 21 节：LangChain 结构化输出](../notes/tool-calling-stage3-21-langchain-structured-output.md)
  - 用途：理解 `with_structured_output()`、Pydantic schema、`json_mode`/`json_schema` 的取舍，以及 LangChain 结构化输出和原生 JSON Mode + Pydantic 的区别。

- [阶段 3 第 22 节：阶段 3 项目整理](../notes/tool-calling-stage3-22-project-summary.md)
  - 用途：复盘 Tool Calling、Java mock API、用户确认、trace_id、分层测试和 LangChain 封装，建立阶段 3 的完整项目地图，并衔接下一阶段 RAG。

- [阶段 4 第 1 节：RAG 是什么，为什么大模型需要知识库](../notes/rag-stage4-01-what-is-rag.md)
  - 用途：理解 RAG 的核心价值、普通聊天/prompt/微调/Tool Calling/RAG 的区别，以及阶段 4 的完整学习地图。

- [阶段 4 第 2 节：RAG 完整流程](../notes/rag-stage4-02-rag-pipeline.md)
  - 用途：理解文档入库流水线和用户问答流水线，明确 load、clean、split、embed、store、retrieve、generate、cite sources 每一步的职责。

## 阶段 4 推荐资料组合

阶段 4：企业知识库 RAG 基础 + 向量数据库入门。当前优先看：

1. 本仓库 `notes/rag-stage4-01-what-is-rag.md`
2. 本仓库 `notes/rag-stage4-02-rag-pipeline.md`
3. LangChain Retrieval，理解 RAG 的整体流程
4. OpenAI Embeddings Guide，理解文本如何变成向量
5. Qdrant 官方文档，理解 collection、point、vector、payload、search
6. Qdrant Points，理解 chunk 入库时为什么要同时保存 vector 和 payload
7. Qdrant Filtering，理解后续权限过滤和 metadata 过滤
8. Milvus 官方文档，后半段用于向量数据库对比
9. Milvus Basic Vector Search，后半段理解 ANN 搜索
10. Milvus Index Explained，后半段理解索引和召回率取舍
11. RAGFlow GitHub / 文档，只做产品化功能观察，不作为初学实现主线

## 阶段 3 复盘资料组合

阶段 3：LangChain + Java 工具调用基础。复盘时优先看：

1. 本仓库 `notes/tool-calling-stage3-01-what-is-tool-calling.md`
2. 本仓库 `notes/tool-calling-stage3-02-why-ai-cannot-operate-business-system-directly.md`
3. 本仓库 `notes/tool-calling-stage3-03-tool-parameters-json-schema.md`
4. 本仓库 `notes/tool-calling-stage3-04-structured-output-vs-tool-calling.md`
5. 本仓库 `notes/tool-calling-stage3-05-fake-query-order-tool.md`
6. 本仓库 `notes/tool-calling-stage3-06-tool-result-pydantic-validation.md`
7. 本仓库 `notes/tool-calling-stage3-07-tool-error-handling.md`
8. 本仓库 `notes/tool-calling-stage3-08-tool-permission-boundary.md`
9. 本仓库 `notes/tool-calling-stage3-09-tool-idempotency.md`
10. 本仓库 `notes/tool-calling-stage3-10-java-mock-service.md`
11. 本仓库 `notes/tool-calling-stage3-11-python-calls-java-mock-api.md`
12. 本仓库 `notes/tool-calling-stage3-12-model-decides-tool-call.md`
13. 本仓库 `notes/tool-calling-stage3-13-tool-result-model-summary.md`
14. 本仓库 `notes/tool-calling-stage3-14-user-confirmation.md`
15. 本仓库 `notes/tool-calling-stage3-15-ticket-creation-workflow.md`
16. 本仓库 `notes/tool-calling-stage3-16-tool-logging-trace-id.md`
17. 本仓库 `notes/tool-calling-stage3-17-tool-testing-fakes.md`
18. 本仓库 `notes/tool-calling-stage3-18-what-is-langchain.md`
19. 本仓库 `notes/tool-calling-stage3-19-langchain-chatmodel-basics.md`
20. 本仓库 `notes/tool-calling-stage3-20-langchain-tool-basics.md`
21. 本仓库 `notes/tool-calling-stage3-21-langchain-structured-output.md`
22. 本仓库 `notes/tool-calling-stage3-22-project-summary.md`
23. LangChain overview，理解 LangChain 的整体定位
24. LangChain Models，理解 ChatModel 的 `invoke()`、`stream()` 和 `batch()`
25. LangChain Messages，理解 `SystemMessage`、`HumanMessage`、`AIMessage`
26. LangChain ChatOpenAI integration，理解 `langchain-openai` 和 OpenAI-compatible `base_url`
27. LangChain Tools，理解工具定义、参数 schema 和模型工具调用
28. LangChain Structured output，理解 provider strategy、tool strategy 和 Pydantic schema
29. LangChain Agents，理解 model + tools + harness 的 agent loop
30. LangGraph overview，理解 LangGraph 与 LangChain 的分工
31. LangGraph Workflows and agents，理解 workflow 与 agent 的区别
32. HTTPX Quickstart，理解 Python HTTP 客户端的 GET、JSON 和响应读取
33. HTTPX Timeouts，理解跨服务调用为什么必须配置 timeout
34. HTTPX Exceptions，理解 timeout、连接失败等异常层级
35. HTTPX Transports and MockTransport，理解如何在测试里模拟 HTTP 响应
36. OpenAI Function Calling Guide，理解工具定义、工具调用和后端执行的边界
37. RFC 9110 Idempotent Methods，理解幂等性的基础定义
38. Stripe Idempotent requests，理解 idempotency key 的真实 API 实践
39. FastAPI Path Parameters，理解 `/orders/{order_id}` 这类路径参数
40. FastAPI Bigger Applications，理解 `APIRouter` 和多文件项目结构
41. FastAPI Handling Errors，理解接口错误应该统一抛出和统一响应
42. FastAPI Testing，理解如何用 `TestClient` 测试 API
43. OpenAI Structured model outputs，理解结构化输出和 Tool Calling 的边界
44. OpenAI Tools Guide，理解 tools 在模型调用里的定位
45. OpenAI Safety Best Practices，理解对抗测试和人类审核
46. OWASP Top 10 for LLM Applications，理解 Prompt Injection、Insecure Output Handling、Excessive Agency
47. OWASP LLM06:2025 Excessive Agency，理解过多工具、过大权限和过高自主性带来的风险
48. OWASP LLM01:2025 Prompt Injection，理解为什么不能只靠 prompt 做安全控制
49. OpenAI Responses API Reference，后续查真实工具调用参数和响应结构
50. 阿里云百炼：Function Calling，理解千问兼容模型里的工具调用流程
51. 阿里云百炼：结构化输出，理解千问兼容模型里的 JSON 输出能力
52. JSON Schema Creating your first schema，理解工具参数 schema 的基础
53. JSON Schema Object，理解 `properties`、`required`、`additionalProperties`
54. JSON Schema Enumerated values，理解 `enum`
55. Pydantic JSON Schema，理解 `BaseModel.model_json_schema()`
56. Pydantic Models，理解 `model_validate` 和 `ValidationError`
57. Pydantic Configuration，理解 `ConfigDict(extra="forbid")`
58. MDN HTTP response status codes，理解 404、502、504 的语义
59. 本仓库 `notes/llm-api-stage2-15-structured-output-concept.md`，复习结构化输出
60. 本仓库 `notes/llm-api-stage2-16-pydantic-structured-output.md`，复习 Pydantic 校验
61. 本仓库 `notes/fastapi-stage1-13-trace-id.md`，复习请求追踪
62. 本仓库 `notes/fastapi-stage1-14-exception-handling.md`，复习统一异常处理

阶段 2：LLM API 基础调用已完成。复盘时可看：

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
16. 本仓库 `notes/llm-api-stage2-16-pydantic-structured-output.md`
17. 本仓库 `notes/llm-api-stage2-17-testing-model-calls.md`
18. 本仓库 `notes/llm-api-stage2-18-project-summary.md`
19. OpenAI Developer quickstart，理解 API key、SDK 和第一次 API 调用
20. OpenAI API Reference：Authentication，理解 API key 认证和密钥安全
21. OpenAI Python API library，理解 Python SDK、`.env`、timeouts、retries、错误层级和 `APIStatusError`
22. OpenAI SDKs and CLI，理解 SDK 安装和基础使用
23. OpenAI API Reference：Chat Completions，确认 `model`、`messages` 和 `choices[0].message.content`
24. OpenAI API Reference：Chat Completions create，确认 `usage.prompt_tokens`、`usage.completion_tokens`、`usage.total_tokens`、`temperature`、`top_p`、`max_completion_tokens` 和 `response_format`
25. OpenAI Streaming API responses，理解 `stream=True` 和逐块读取响应
26. OpenAI Structured model outputs，理解 Structured Outputs、JSON Mode 和 JSON Schema
27. OpenAI Conversation state，理解多轮对话状态管理
28. OpenAI Error codes，理解 SDK 错误类型和错误处理
29. OpenAI Rate limits guide，理解请求频率、token 限额和 429
30. FastAPI StreamingResponse，理解服务端如何逐块返回数据
31. FastAPI Stream Data，理解 FastAPI 不会自动把 chunk 转换成 JSON
32. FastAPI Testing Dependencies with Overrides，理解测试时替换外部依赖
33. pytest monkeypatch，理解临时替换对象、环境变量和路径
34. Python unittest.mock，理解 mock、patch 和调用断言
35. MDN Using server-sent events，理解 SSE 和 `text/event-stream`
36. MDN EventSource，理解浏览器 SSE 接收方式
37. Python logging 官方文档，理解日志级别、日志格式和 `exc_info`
38. Python time.perf_counter 官方文档，理解模型调用耗时统计
39. MDN 429 Too Many Requests，理解 HTTP 429 通用语义
40. 阿里云百炼：OpenAI Chat接口兼容，理解千问兼容接口的 `api_key`、`base_url`、`model`、`messages` 和 `usage`
41. 阿里云百炼：流式输出，理解 `stream=True`、`stream_options={"include_usage": true}` 和流式计费
42. 阿里云百炼：结构化输出，理解 JSON Mode 和 `response_format={"type": "json_object"}`
43. 阿里云百炼：文本生成模型API参考，理解兼容 Chat Completions、Responses、Anthropic Messages 和 DashScope 的区别
44. Pydantic JSON Schema，理解 `BaseModel.model_json_schema()`
45. Pydantic JSON，理解 `BaseModel.model_validate_json()`
46. JSON Schema Creating your first schema，理解对象、字段、类型和必填项
47. OpenAI Production best practices，理解生产环境 key 安全和 token 成本估算
48. OpenAI Key concepts：Tokens，理解 token 和上下文窗口
49. OpenAI Pricing，确认当前模型价格
50. OpenAI Reasoning models，理解 reasoning tokens 和 `max_output_tokens`
51. OpenAI Text generation，理解大模型文本生成和 Responses API
52. OpenAI Prompt engineering，理解消息角色、prompt 版本化和测试
53. OpenAI Migrate to the Responses API，理解 `messages` 和 typed Items 的映射
54. OpenAI Models，理解模型选择要看当前官方文档
55. OpenAI Responses API Reference，后续写真实调用时查参数和响应
56. 本仓库 `notes/fastapi-stage1-16-project-summary.md`，复习当前 FastAPI 服务基础
57. 本仓库 `notes/fastapi-stage1-11-env-config.md`，复习 `.env` 配置读取
58. 本仓库 `notes/fastapi-stage1-12-logging.md`，复习日志
59. 本仓库 `notes/fastapi-stage1-13-trace-id.md`，复习请求追踪
60. 本仓库 `notes/fastapi-stage1-14-exception-handling.md`，复习统一异常处理

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
