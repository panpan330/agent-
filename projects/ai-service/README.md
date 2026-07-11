# AI Service

Python AI 服务项目。阶段 1：FastAPI 服务基础已完成；阶段 2：LLM API 基础调用已完成；阶段 3：LangChain + Java 工具调用基础已开始。

当前 `/chat` 已经从 mock 回复改成 OpenAI-compatible 真实模型调用。没有配置本机 `LLM_API_KEY` 时，接口会返回统一配置错误。

当前 `/stream-chat` 已经支持 OpenAI-compatible 流式输出，并通过 SSE 逐块返回模型生成内容。

当前 `/extract-ticket` 已经支持 OpenAI-compatible JSON Mode，并用 Pydantic 校验模型返回的结构化工单字段。

当前阶段 3 第 1-11 节已完成 Tool Calling 概念、业务系统安全边界、工具参数和 JSON Schema、结构化输出与 Tool Calling 的边界、fake tool 模拟订单查询、工具调用结果 Pydantic 校验、工具调用错误处理、工具调用权限边界、工具调用幂等性、`projects/java-mock-service` 最小业务服务，以及 Python AI 服务调用 Java mock API。后续会让模型决定是否调用工具，并继续补工具调用日志和 trace_id 串联。

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
- `/tools/query-order` 订单查询工具接口，当前调用 Java mock API
- Pydantic 结构化输出模型和 JSON Schema 生成
- 模型返回 JSON 的 Pydantic 校验
- `QueryOrderArgs` 工具参数模型
- `QueryOrderResult` fake 工具返回模型
- `query_order` 订单查询工具函数
- `JavaOrderClient` Java mock 订单服务 HTTP 客户端
- `map_java_order_to_query_order_payload` Java 订单响应到 AI 工具结果的字段映射函数
- `JAVA_MOCK_SERVICE_BASE_URL` 和 `JAVA_MOCK_SERVICE_TIMEOUT_SECONDS` 跨服务调用配置
- `validate_query_order_result` 工具结果校验函数
- `TOOL_RESULT_VALIDATION_FAILED` 工具结果校验失败错误
- `map_query_order_error` 工具底层异常映射函数
- `TOOL_TIMEOUT`、`TOOL_UPSTREAM_ERROR`、`TOOL_CALL_FAILED` 工具调用错误
- `ToolDefinition` 工具定义模型
- `ToolAccessLevel` 工具风险等级
- `TOOL_REGISTRY` 后端工具注册表
- `authorize_tool_call` 工具权限守卫函数
- `TOOL_NOT_ALLOWED`、`TOOL_CONFIRMATION_REQUIRED` 工具权限错误
- `Idempotency-Key` 工具调用幂等请求头
- `run_idempotent_tool` 工具幂等执行包装函数
- `build_arguments_fingerprint` 工具名和参数指纹生成函数
- `IDEMPOTENCY_KEY_CONFLICT`、`IDEMPOTENCY_KEY_INVALID` 工具幂等错误
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
    tools.py               工具调用学习接口
  schemas/
    chat.py                聊天请求/响应模型
    error.py               统一错误响应模型
    structured.py          结构化输出请求/响应和工单字段模型
    tool.py                工具参数和工具结果模型
  services/
    llm_client.py          OpenAI-compatible SDK client 初始化
    llm_service.py         LLM 聊天调用服务
    message_builder.py     聊天 messages 构建工具
    prompt_builder.py      prompt 分段构建工具
    structured_output_service.py 结构化输出调用服务
    java_order_client.py   Java mock 订单服务 HTTP 客户端
  tools/
    fake_order_tool.py     订单查询工具，当前调用 Java mock API
    idempotency.py         工具调用幂等性辅助函数
    tool_registry.py       工具注册表和权限守卫
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
  test_fake_order_tool.py  订单查询工具映射和校验测试
  test_java_order_client.py Java mock HTTP 客户端测试
  test_fake_llm_client.py  fake LLM client 工具测试
  test_health.py           /health 测试
  test_llm_client.py       LLM client 初始化测试
  test_llm_service.py      LLM 聊天服务测试
  test_logging.py          日志测试
  test_message_builder.py  聊天 messages 构建测试
  test_prompt_builder.py   prompt 分段构建测试
  test_structured_output_service.py 结构化输出服务测试
  test_structured_schema.py 结构化输出模型测试
  test_tool_idempotency.py 工具调用幂等性测试
  test_tool_registry.py    工具注册表和权限守卫测试
  test_tool_schema.py      工具参数和工具结果模型测试
  test_tools_api.py        /tools/query-order 接口测试
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

当前测试使用 FastAPI 的 `TestClient`，覆盖 `/health`、`/chat`、`/stream-chat`、`/extract-ticket`、`/tools/query-order`、`ChatRequest`、`ChatResponse`、`ChatMessage`、`TicketExtraction`、`QueryOrderArgs`、`QueryOrderResult`、`ToolDefinition`、`ToolAccessLevel`、多轮 `history`、配置读取、日志、`trace_id`、统一异常处理、CORS、token 粗略估算、LLM client 初始化、LLM service、结构化输出 service、JavaOrderClient、Java mock API 字段映射、工具结果 Pydantic 校验、工具调用 timeout/上游错误映射、工具注册表和权限守卫、工具调用幂等性、fake OpenAI-compatible client、OpenAI-compatible SDK 错误映射、模型调用日志、流式调用日志、结构化输出日志、模型响应 token usage 提取、messages 构建和 prompt 构建。

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
| `JAVA_MOCK_SERVICE_BASE_URL` | Java mock 订单服务基础地址，默认 `http://127.0.0.1:8001` |
| `JAVA_MOCK_SERVICE_TIMEOUT_SECONDS` | 调用 Java mock 订单服务的超时时间，默认 `5` 秒 |
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

## 订单查询工具 `/tools/query-order`

`/tools/query-order` 当前通过 `app/tools/fake_order_tool.py` 执行订单查询工具。文件名还保留 `fake_order_tool.py`，但内部已经不再查询本地内存 fake 数据，而是通过 `app/services/java_order_client.py` 调用 `java-mock-service`：

调用链路：

```text
POST /tools/query-order
-> app/routers/tools.py
-> QueryOrderArgs 校验 order_id
-> authorize_tool_call("query_order")
-> run_idempotent_tool(..., Idempotency-Key)
-> fake_order_tool.query_order()
-> JavaOrderClient.get_order(order_id)
-> GET /orders/{order_id}
-> map_java_order_to_query_order_payload()
-> validate_query_order_result()
-> QueryOrderResult
```

当前默认调用地址来自配置：

```text
JAVA_MOCK_SERVICE_BASE_URL=http://127.0.0.1:8001
JAVA_MOCK_SERVICE_TIMEOUT_SECONDS=5
```

请求示例：

```json
{
  "order_id": "A1001"
}
```

成功响应示例：

```json
{
  "result": {
    "order_id": "A1001",
    "order_status": "waiting_shipment",
    "payment_status": "paid",
    "logistics_message": "商家已接单，等待仓库发货。",
    "latest_event": "仓库正在准备出库。",
    "can_create_ticket": true,
    "source": "java_mock_service"
  }
}
```

响应里不会暴露 Java mock 返回的 `customer_id`。这是工具层字段映射的一部分：只把当前 AI 工具需要的、安全的、稳定的字段返回给模型和调用方。

如果订单号格式合法但 Java mock 服务里不存在，会返回：

```json
{
  "code": "ORDER_NOT_FOUND",
  "message": "订单不存在，请确认订单号是否正确。",
  "trace_id": "..."
}
```

当前 Java mock 服务还提供一个教学用订单号，用来模拟上游服务失败：

| 订单号 | 模拟场景 | 错误码 | HTTP 状态码 |
| --- | --- | --- | --- |
| `A500` | 上游订单服务内部错误 | `TOOL_UPSTREAM_ERROR` | 502 |

如果 `java-mock-service` 没有启动、连接失败或调用超时，`ai-service` 会把底层 HTTP 客户端异常映射成项目统一错误。超时响应示例：

```json
{
  "code": "TOOL_TIMEOUT",
  "message": "订单查询工具调用超时，请稍后重试。",
  "trace_id": "..."
}
```

`A500` 响应示例：

```json
{
  "code": "TOOL_UPSTREAM_ERROR",
  "message": "订单查询服务暂时不可用，请稍后重试。",
  "trace_id": "..."
}
```

当前工具注册表：

| 工具名 | 权限等级 | 是否启用 | 是否需要确认 |
| --- | --- | --- | --- |
| `query_order` | `read` | 是 | 否 |
| `create_ticket` | `write` | 是 | 是 |
| `refund_order` | `sensitive` | 否 | 是 |

如果模型请求未知工具或禁用工具，后端会返回：

```json
{
  "code": "TOOL_NOT_ALLOWED",
  "message": "工具不在允许列表中，后端已拒绝执行。",
  "trace_id": "..."
}
```

如果工具需要用户确认但当前没有确认，后端会返回：

```json
{
  "code": "TOOL_CONFIRMATION_REQUIRED",
  "message": "该工具需要用户确认后才能执行。",
  "trace_id": "..."
}
```

## 工具调用幂等性

`/tools/query-order` 当前支持可选请求头：

```http
Idempotency-Key: query-order-api-key-001
```

如果不传 `Idempotency-Key`，接口按普通请求执行。

如果传入合法 `Idempotency-Key`：

```text
第一次请求：执行工具并保存工具名、参数指纹和结果。
重复请求且参数相同：返回第一次结果，不再执行工具。
重复请求但参数不同：返回 IDEMPOTENCY_KEY_CONFLICT。
```

当前实现入口：

```text
app/tools/idempotency.py
```

当前是学习用内存版实现，服务重启后记录会丢失。生产环境应升级为数据库或 Redis，并配合唯一索引、TTL、事务和审计日志。

同一个幂等键配不同参数时，后端会返回：

```json
{
  "code": "IDEMPOTENCY_KEY_CONFLICT",
  "message": "同一个幂等键不能用于不同的工具调用参数。",
  "trace_id": "..."
}
```

幂等键格式不合法时，后端会返回：

```json
{
  "code": "IDEMPOTENCY_KEY_INVALID",
  "message": "幂等键格式不正确，请使用 8 到 128 位的字母、数字、点、下划线、冒号或短横线。",
  "trace_id": "..."
}
```

如果 Java mock API 返回的数据不符合 `QueryOrderResult`，会返回：

```json
{
  "code": "TOOL_RESULT_VALIDATION_FAILED",
  "message": "工具返回结果校验失败，请稍后重试。",
  "trace_id": "...",
  "details": []
}
```

当前订单查询工具已经把内部 fake 数据替换成 Java mock API。后续会继续让模型决定是否调用这个工具，并把工具结果交回模型做自然语言总结。

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
| POST | `/tools/query-order` | 订单查询工具接口，通过 Java mock API 查询订单 |

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
| `ToolAccessLevel` | `app/schemas/tool.py` | 工具风险等级枚举，当前包括 `read`、`write`、`sensitive` |
| `ToolDefinition` | `app/schemas/tool.py` | 后端工具定义模型，包含工具名、描述、风险等级、是否启用和是否需要确认 |
| `QueryOrderArgs` | `app/schemas/tool.py` | `query_order` 工具参数模型，要求 `order_id` 非空且格式合法 |
| `OrderStatus` | `app/schemas/tool.py` | 订单状态枚举，如 `waiting_shipment`、`shipped`、`delivered` |
| `PaymentStatus` | `app/schemas/tool.py` | 支付状态枚举，如 `unpaid`、`paid`、`refunded` |
| `QueryOrderResult` | `app/schemas/tool.py` | 订单查询工具结果，包含订单状态、支付状态、物流说明和是否可创建工单 |
| `QueryOrderResponse` | `app/schemas/tool.py` | 订单查询接口响应体，包裹 `QueryOrderResult` |
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

## 阶段 3 学习方向

下一步继续学习 LangChain + Java 工具调用基础，为智能工单 Agent 调用 Java 业务服务做准备。

当前阶段 3 的核心目标：

- 理解 Tool Calling 不是模型直接执行代码，而是模型返回工具名和参数，由后端决定是否执行。
- 理解 AI 不能绕过 Java 后端直接操作业务系统，模型输出必须当成不可信输入处理。
- 理解工具参数如何用 JSON Schema 描述，并用 Pydantic 在后端校验模型返回的 arguments。
- 理解结构化输出和 Tool Calling 的区别：前者把自然语言整理成固定格式数据，后者让模型提出调用外部工具的请求。
- 用 fake tool 先模拟订单查询，避免一开始就引入复杂业务服务。
- 理解工具返回结果、Java API 响应和第三方接口返回也要先用 Pydantic 校验。
- 理解工具调用失败时要把 timeout、404、上游 500 映射成统一、安全、可测试的项目错误。
- 理解工具调用必须经过后端白名单、启用状态、风险等级和用户确认守卫，不能由模型自行决定权限。
- 理解重复工具调用要通过 `Idempotency-Key` 和参数指纹避免重复产生业务效果。
- 已用 FastAPI 写一个 Java mock 业务服务，模拟后续 Spring Boot 接口。
- 当前已经让 Python AI 服务调用 Java mock API，并处理超时、404、500、权限和幂等。
- 下一步让模型决定是否调用订单查询工具。
- 后续再引入 LangChain 的 Tool 抽象，把已经理解的底层流程封装起来。
