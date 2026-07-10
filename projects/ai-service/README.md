# AI Service

Python AI 服务项目。阶段 1：FastAPI 服务基础已完成；阶段 2：LLM API 基础调用已完成。

当前 `/chat` 已经从 mock 回复改成 OpenAI-compatible 真实模型调用。没有配置本机 `LLM_API_KEY` 时，接口会返回统一配置错误。

当前 `/stream-chat` 已经支持 OpenAI-compatible 流式输出，并通过 SSE 逐块返回模型生成内容。

当前 `/extract-ticket` 已经支持 OpenAI-compatible JSON Mode，并用 Pydantic 校验模型返回的结构化工单字段。

## 当前能力

- FastAPI 应用创建和启动
- `/health` 健康检查接口
- `/chat` mock 聊天接口
- router 路由拆分
- Pydantic 请求模型和响应模型
- `.env` 配置读取
- OpenAI SDK 依赖
- OpenAI-compatible LLM client 初始化
- `system` / `user` / `assistant` 消息结构
- prompt 分段构建工具
- `/chat` 真实模型调用
- `/chat` 可选多轮对话 `history`
- `/stream-chat` 流式聊天接口
- SSE `message` / `done` / `error` 事件格式
- `/extract-ticket` 工单字段结构化抽取接口
- Pydantic 结构化输出模型和 JSON Schema 生成
- 模型返回 JSON 的 Pydantic 校验
- 共享 fake OpenAI-compatible client 测试工具
- 模型调用 timeout 统一错误处理
- SDK retry 次数配置和 rate limit 统一错误处理
- OpenAI-compatible SDK 常见错误映射
- 模型调用成功/失败日志和流式调用日志
- 模型响应 `usage` token 用量提取
- fake LLM service/client 测试隔离
- logging 基础日志
- `trace_id` 请求追踪
- 统一异常处理
- CORS 基础配置
- token 粗略估算和输出 token 上限配置
- pytest 自动化测试

## 项目结构

```text
app/
  core/
    config.py              配置读取
    cors.py                CORS 配置
    exception_handlers.py  统一异常处理器
    exceptions.py          项目业务异常
    logging.py             日志配置
    token_usage.py         token 粗略估算和预算辅助
    trace.py               trace_id 上下文
  middleware/
    tracing.py             请求追踪 middleware
  routers/
    chat.py                /chat 路由
    health.py              /health 路由
  schemas/
    chat.py                聊天请求/响应模型
    error.py               统一错误响应模型
    structured.py          结构化输出请求/响应和工单字段模型
  services/
    llm_client.py          OpenAI-compatible SDK client 初始化
    llm_service.py         LLM 聊天调用服务
    message_builder.py     聊天 messages 构建工具
    prompt_builder.py      prompt 分段构建工具
    structured_output_service.py 结构化输出调用服务
  main.py                  FastAPI 应用入口
scripts/
  llm_compatible_smoke_test.py 手动检查或调用兼容模型
tests/
  conftest.py              pytest 共享夹具
  fakes.py                 OpenAI-compatible fake client 测试工具
  test_chat_api.py         /chat 接口测试
  test_chat_schema.py      聊天模型测试
  test_config.py           配置测试
  test_cors.py             CORS 测试
  test_exception_handlers.py 统一异常处理测试
  test_fake_llm_client.py  fake LLM client 工具测试
  test_health.py           /health 测试
  test_llm_client.py       LLM client 初始化测试
  test_llm_service.py      LLM 聊天服务测试
  test_logging.py          日志测试
  test_message_builder.py  聊天 messages 构建测试
  test_prompt_builder.py   prompt 分段构建测试
  test_structured_output_service.py 结构化输出服务测试
  test_structured_schema.py 结构化输出模型测试
  test_token_usage.py      token 粗略估算测试
  test_trace.py            trace_id 测试
```

## 运行

首次进入项目时，先同步依赖：

```powershell
uv sync
```

如果需要本地配置，先复制示例配置文件：

```powershell
Copy-Item .env.example .env
```

再启动服务：

```powershell
uv run uvicorn app.main:app --reload
```

启动后访问：

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
```

## 测试

```powershell
uv run pytest -q
```

当前测试使用 FastAPI 的 `TestClient`，覆盖 `/health`、`/chat`、`/stream-chat`、`/extract-ticket`、`ChatRequest`、`ChatResponse`、`ChatMessage`、`TicketExtraction`、多轮 `history`、配置读取、日志、`trace_id`、统一异常处理、CORS、token 粗略估算、LLM client 初始化、LLM service、结构化输出 service、fake OpenAI-compatible client、OpenAI-compatible SDK 错误映射、模型调用日志、流式调用日志、结构化输出日志、模型响应 token usage 提取、messages 构建和 prompt 构建。

也可以运行 Python 编译检查：

```powershell
uv run python -m compileall -q -x ".venv|__pycache__" .
```

## 配置

本项目使用 `app/core/config.py` 集中读取配置。

`.env.example` 是可以提交到 GitHub 的示例配置，真实 `.env` 只放在本机，不提交。

| 配置项 | 说明 |
| --- | --- |
| `APP_NAME` | FastAPI 应用名称 |
| `APP_DESCRIPTION` | FastAPI 应用描述 |
| `APP_VERSION` | FastAPI 应用版本 |
| `MODEL_NAME` | 当前使用的模型名称，现阶段先是 mock 名称 |
| `LLM_PROVIDER` | LLM 服务商标识，例如 `aliyun-compatible` |
| `LLM_MODEL` | 真实模型名，例如 `qwen3.7-plus` |
| `LLM_BASE_URL` | OpenAI-compatible 接口地址，真实值只放本机 `.env` |
| `LLM_API_KEY` | LLM API key，真实值只放本机 `.env` 或系统环境变量 |
| `REQUEST_TIMEOUT_SECONDS` | 后续调用模型或外部接口时使用的超时时间 |
| `LLM_MAX_RETRIES` | OpenAI-compatible SDK 自动重试次数，默认 `2`，当前允许 `0-5` |
| `MAX_OUTPUT_TOKENS` | 后续限制模型最多生成多少输出 token |
| `LOG_LEVEL` | 日志级别 |
| `CORS_ALLOWED_ORIGINS` | 允许跨源访问后端的前端来源，多个值用逗号分隔 |
| `OPENAI_API_KEY` | 旧版兼容字段，后续优先使用 `LLM_API_KEY` |

`LLM_API_KEY` 和 `OPENAI_API_KEY` 都属于敏感信息。真实值只应该放在本机 `.env` 或系统环境变量里，不要写进代码、README、测试用例、截图或聊天记录里。

项目里可以通过 `settings.has_llm_api_key` 判断是否已经配置了非空 key。`LLM_API_KEY=""` 或全是空格时，都视为未配置。

`app/core/token_usage.py` 提供的是本地粗略估算工具，用来学习和做预算保护，不等于真实计费结果。真实 token 数以后要以模型 API 响应里的 `usage` 为准。

## OpenAI-compatible SDK 检查

当前项目使用官方 `openai` Python SDK 初始化 OpenAI-compatible client。

配置入口：

```text
app/services/llm_client.py
```

手动检查配置：

```powershell
uv run python scripts/llm_compatible_smoke_test.py
```

这条命令默认不会调用模型，只检查本机 `.env` 是否已经配置 `LLM_API_KEY`。

脚本真实调用时会先用 `app/services/prompt_builder.py` 把用户输入整理成包含任务、要求、输出格式和失败策略的清晰 prompt。

确认要真实调用模型时，再显式加：

```powershell
uv run python scripts/llm_compatible_smoke_test.py --call
```

注意：`--call` 会请求真实模型，可能产生费用。真实 key 不要发给任何人，只放本机 `.env`。

## 真实 `/chat`

`/chat` 当前通过 `app/services/llm_service.py` 调用 OpenAI-compatible 模型，并支持可选 `history` 做多轮对话。

调用链路：

```text
POST /chat
-> app/routers/chat.py
-> LLMChatService.generate_reply()
-> prompt_builder.py
-> message_builder.py
-> llm_client.py
-> client.chat.completions.create(...)
```

请求示例：

```json
{
  "message": "请解释 FastAPI 是什么"
}
```

多轮请求示例：

```json
{
  "message": "那 FastAPI 呢？",
  "history": [
    {"role": "user", "content": "什么是 API？"},
    {"role": "assistant", "content": "API 是程序之间约定好的调用方式。"}
  ]
}
```

`history` 只允许 `user` 和 `assistant`，不允许客户端传 `system`。当前最多允许 20 条历史消息。

成功响应示例：

```json
{
  "reply": "模型生成的回答"
}
```

如果没有配置本机 `LLM_API_KEY`，会返回：

```json
{
  "code": "LLM_API_KEY_MISSING",
  "message": "LLM API key 未配置，请先在本机 .env 中配置 LLM_API_KEY。",
  "trace_id": "..."
}
```

如果模型调用超过 `REQUEST_TIMEOUT_SECONDS`，会返回：

```json
{
  "code": "LLM_TIMEOUT",
  "message": "模型调用超时，请稍后重试。",
  "trace_id": "..."
}
```

如果模型服务返回限流，或请求过于频繁，会返回：

```json
{
  "code": "LLM_RATE_LIMITED",
  "message": "模型服务请求过于频繁，请稍后重试。",
  "trace_id": "..."
}
```

自动化测试不会真实调用模型。测试通过 FastAPI `dependency_overrides` 注入 fake service，通过 fake client 测试 `LLMChatService`。

当前模型调用错误会先映射成项目统一错误码，再由统一异常处理器返回 JSON：

| 错误码 | HTTP 状态码 | 含义 |
| --- | --- | --- |
| `LLM_API_KEY_MISSING` | 500 | 本机没有配置模型 API key |
| `LLM_TIMEOUT` | 504 | 模型调用超时 |
| `LLM_RATE_LIMITED` | 429 | 模型服务限流或请求过于频繁 |
| `LLM_AUTHENTICATION_FAILED` | 502 | 模型服务认证失败 |
| `LLM_PERMISSION_DENIED` | 502 | 模型服务拒绝访问 |
| `LLM_RESOURCE_NOT_FOUND` | 502 | 模型、接口或资源不存在 |
| `LLM_BAD_REQUEST` | 502 | 发给模型服务的请求参数错误 |
| `LLM_PROVIDER_ERROR` | 502 | 模型服务内部错误 |
| `LLM_CONNECTION_ERROR` | 502 | 无法连接模型服务 |
| `LLM_PROVIDER_STATUS_ERROR` | 502 | 模型服务返回其他异常状态 |
| `LLM_BAD_RESPONSE` | 502 | 模型返回格式异常 |
| `LLM_EMPTY_RESPONSE` | 502 | 模型返回空内容 |
| `LLM_CALL_FAILED` | 502 | 其他模型调用失败 |
| `STRUCTURED_OUTPUT_EMPTY` | 502 | 模型没有返回可解析的结构化内容 |
| `STRUCTURED_OUTPUT_VALIDATION_FAILED` | 502 | 模型返回的结构化内容不符合 Pydantic 模型 |

## 流式 `/stream-chat`

`/stream-chat` 当前通过 `app/services/llm_service.py` 调用 OpenAI-compatible 模型，并开启：

```python
stream=True
stream_options={"include_usage": True}
```

调用链路：

```text
POST /stream-chat
-> app/routers/chat.py
-> LLMChatService.stream_reply()
-> prompt_builder.py
-> message_builder.py
-> llm_client.py
-> client.chat.completions.create(..., stream=True)
-> StreamingResponse
```

请求体和 `/chat` 相同：

```json
{
  "message": "请解释 FastAPI 是什么"
}
```

响应类型是：

```text
text/event-stream
```

成功时会逐块返回 SSE：

```text
event: message
data: {"content":"FastAPI"}

event: message
data: {"content":" 是 Python Web 框架。"}

event: done
data: {"trace_id":"..."}
```

流开始前发生的错误，例如缺少 `LLM_API_KEY`，仍然返回统一 JSON 错误。

流开始后发生的错误，会返回 SSE `error` 事件：

```text
event: error
data: {"code":"LLM_CALL_FAILED","message":"模型调用失败，请稍后重试。","trace_id":"..."}
```

## 结构化 `/extract-ticket`

`/extract-ticket` 当前通过 `app/services/structured_output_service.py` 调用 OpenAI-compatible 模型，并开启 JSON Mode：

```python
response_format={"type": "json_object"}
```

调用链路：

```text
POST /extract-ticket
-> app/routers/chat.py
-> StructuredOutputService.extract_ticket()
-> build_ticket_extraction_messages()
-> llm_client.py
-> client.chat.completions.create(..., response_format={"type":"json_object"})
-> TicketExtraction.model_validate_json()
```

请求示例：

```json
{
  "message": "订单 A1001 一直没有发货，我要投诉。"
}
```

成功响应示例：

```json
{
  "extraction": {
    "intent": "complaint",
    "order_id": "A1001",
    "summary": "用户投诉订单未发货",
    "urgency": "high",
    "need_human_review": true
  }
}
```

当前支持的 `intent`：

```text
refund
order_query
logistics
complaint
unknown
```

当前支持的 `urgency`：

```text
low
normal
high
```

如果模型返回的 JSON 不符合 `TicketExtraction`，会返回：

```json
{
  "code": "STRUCTURED_OUTPUT_VALIDATION_FAILED",
  "message": "模型结构化输出校验失败，请稍后重试。",
  "trace_id": "...",
  "details": []
}
```

自动化测试不会真实调用模型。接口测试通过 `dependency_overrides` 注入 fake service，服务测试通过 fake client 验证 JSON Mode 参数、Pydantic 解析和错误处理。

## 模型调用测试工具

测试代码里的共享 fake 工具放在：

```text
tests/fakes.py
```

当前提供：

| 工具 | 作用 |
| --- | --- |
| `FakeOpenAICompatibleClient` | 模拟 `client.chat.completions.create(...)` 结构 |
| `FakeChatCompletions` | 模拟普通响应、流式响应、错误和调用参数记录 |
| `make_stream_chunk()` | 构造流式响应 chunk |
| `make_usage()` | 构造 token usage |
| `make_status_error()` | 构造 OpenAI SDK 风格的状态码错误 |

service 测试通过 fake client 验证模型调用参数，例如 `model`、`messages`、`stream`、`stream_options` 和 `response_format`。

router/API 测试通过 FastAPI `dependency_overrides` 注入 fake service，避免测试接口时真实调用模型。

## 阶段 2 验收

- [x] `/chat` 能调用 OpenAI-compatible 模型
- [x] `/chat` 支持多轮 `history`
- [x] `/stream-chat` 支持 SSE 流式输出
- [x] `/extract-ticket` 支持 JSON Mode 和 Pydantic 结构化校验
- [x] API key 只从本机 `.env` 或环境变量读取
- [x] timeout、rate limit、认证失败、连接失败等模型错误会映射成统一错误码
- [x] 模型调用日志记录 provider、model、耗时、token 和错误码
- [x] 日志不记录完整用户输入、完整 prompt、完整模型回复或 API key
- [x] 自动化测试使用 fake service / fake client，不真实调用模型
- [x] `uv run pytest -q` 全量通过

## CORS

本项目使用 FastAPI 的 `CORSMiddleware` 处理浏览器跨源访问。

配置入口：

```text
app/core/cors.py
```

允许来源从配置读取：

```text
CORS_ALLOWED_ORIGINS
```

默认允许：

```text
http://localhost:5173
http://127.0.0.1:5173
```

如果前端开发服务器端口不同，需要修改 `.env` 里的 `CORS_ALLOWED_ORIGINS`。

## 日志

本项目使用 Python 标准库 `logging`。

日志配置入口：

```text
app/core/logging.py
```

应用启动时会读取配置：

```text
LOG_LEVEL
```

当前 `/chat` 接口会记录一条业务日志：

```text
chat_requested message_length=...
```

模型调用成功时会记录：

```text
llm_chat_succeeded provider=... model=... elapsed_ms=... prompt_tokens=... completion_tokens=... total_tokens=...
```

模型调用失败时会记录：

```text
llm_chat_failed code=... provider=... model=... status_code=... elapsed_ms=...
```

流式模型调用成功时会记录：

```text
llm_stream_chat_succeeded provider=... model=... elapsed_ms=... chunks=... content_chunks=... prompt_tokens=... completion_tokens=... total_tokens=...
```

流式模型调用失败时会记录：

```text
llm_stream_chat_failed code=... provider=... model=... status_code=... elapsed_ms=... chunks=... content_chunks=...
```

日志格式会自动带上当前请求的 `trace_id`：

```text
trace_id=...
```

注意：日志只记录消息长度、模型名、服务商、耗时、token 用量和错误码等元信息，不记录完整用户输入、完整 `history`、完整 prompt、完整模型回复或 API key，避免把敏感内容写入日志。

## 请求追踪

本项目使用 `trace_id` 追踪一次 HTTP 请求。

相关文件：

```text
app/core/trace.py
app/middleware/tracing.py
```

每个请求都会经过 trace middleware：

```text
请求进入 -> 设置 trace_id -> 执行路由 -> 响应头返回 X-Trace-Id -> 清理 trace_id
```

如果客户端传入：

```text
X-Trace-Id
```

服务端会复用它。

如果客户端没有传，服务端会生成新的 `trace_id`。

## 统一异常处理

本项目使用统一错误响应格式：

```json
{
  "code": "VALIDATION_ERROR",
  "message": "请求参数校验失败",
  "trace_id": "..."
}
```

如果错误有结构化细节，会额外返回：

```json
{
  "details": []
}
```

相关文件：

```text
app/schemas/error.py
app/core/exceptions.py
app/core/exception_handlers.py
```

当前已统一处理：

| 类型 | code |
| --- | --- |
| 404 | `NOT_FOUND` |
| 405 | `METHOD_NOT_ALLOWED` |
| 参数校验错误 | `VALIDATION_ERROR` |
| 业务异常 | 自定义业务错误码 |
| 未知异常 | `INTERNAL_SERVER_ERROR` |

## 当前接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/health` | 服务健康检查 |
| POST | `/chat` | 聊天接口，调用 OpenAI-compatible 模型 |
| POST | `/stream-chat` | 流式聊天接口，调用 OpenAI-compatible 模型并返回 SSE |
| POST | `/extract-ticket` | 结构化工单字段抽取接口，调用 OpenAI-compatible 模型并用 Pydantic 校验 |

## 当前模型

| 模型 | 路径 | 说明 |
| --- | --- | --- |
| `ChatRequest` | `app/schemas/chat.py` | 聊天请求体，要求 `message` 是非空字符串，可选 `history` 做多轮上下文 |
| `ChatResponse` | `app/schemas/chat.py` | 聊天响应体，要求 `reply` 是非空字符串 |
| `ChatMessageRole` | `app/schemas/chat.py` | 聊天消息角色，只允许 `system`、`user`、`assistant` |
| `ChatMessage` | `app/schemas/chat.py` | 聊天消息模型，包含 `role` 和 `content` |
| `StructuredOutputRequest` | `app/schemas/structured.py` | 结构化输出请求体，要求 `message` 是非空字符串 |
| `TicketExtraction` | `app/schemas/structured.py` | 工单字段抽取结果，包含 `intent`、`order_id`、`summary`、`urgency`、`need_human_review` |
| `StructuredOutputResponse` | `app/schemas/structured.py` | 结构化输出响应体，包裹 `TicketExtraction` |
| `ErrorResponse` | `app/schemas/error.py` | 统一错误响应体，包含 `code`、`message`、`trace_id` 和可选 `details` |

## 阶段 1 验收

- [x] 服务可以启动
- [x] `/health` 可以访问
- [x] `/chat` 可以接收 JSON 请求体
- [x] 请求和响应使用 Pydantic 模型
- [x] 配置从 `.env` 或环境变量读取
- [x] 日志可以通过 `LOG_LEVEL` 控制
- [x] 每个请求都有 `X-Trace-Id`
- [x] 错误响应格式统一
- [x] CORS 允许配置的前端来源
- [x] 自动化测试通过

## 下一阶段

下一步进入 LangChain + Java 工具调用基础，为智能工单 Agent 调用 Java 业务服务做准备。
