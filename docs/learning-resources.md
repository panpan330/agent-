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

## 当前阶段推荐资料组合

阶段 1：FastAPI 服务基础已完成。复盘时优先看：

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
