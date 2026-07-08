# AI Service

Python AI 服务项目。阶段 1：FastAPI 服务基础已完成。

当前项目还没有接真实大模型，`/chat` 是 mock 接口。这个阶段的重点是先把 AI 服务的 Web API 工程基础搭稳。

## 当前能力

- FastAPI 应用创建和启动
- `/health` 健康检查接口
- `/chat` mock 聊天接口
- router 路由拆分
- Pydantic 请求模型和响应模型
- `.env` 配置读取
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
  main.py                  FastAPI 应用入口
tests/
  conftest.py              pytest 共享夹具
  test_chat_api.py         /chat 接口测试
  test_chat_schema.py      聊天模型测试
  test_config.py           配置测试
  test_cors.py             CORS 测试
  test_exception_handlers.py 统一异常处理测试
  test_health.py           /health 测试
  test_logging.py          日志测试
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

当前测试使用 FastAPI 的 `TestClient`，覆盖 `/health`、`/chat`、`ChatRequest`、`ChatResponse`、配置读取、日志、`trace_id`、统一异常处理、CORS 和 token 粗略估算。

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
| `REQUEST_TIMEOUT_SECONDS` | 后续调用模型或外部接口时使用的超时时间 |
| `MAX_OUTPUT_TOKENS` | 后续限制模型最多生成多少输出 token |
| `LOG_LEVEL` | 日志级别 |
| `CORS_ALLOWED_ORIGINS` | 允许跨源访问后端的前端来源，多个值用逗号分隔 |
| `OPENAI_API_KEY` | 后续接真实大模型时使用，不能写死在代码里 |

`OPENAI_API_KEY` 属于敏感信息。真实值只应该放在本机 `.env` 或系统环境变量里，不要写进代码、README、测试用例、截图或聊天记录里。

项目里可以通过 `settings.has_openai_api_key` 判断是否已经配置了非空 key。`OPENAI_API_KEY=""` 或全是空格时，都视为未配置。

`app/core/token_usage.py` 提供的是本地粗略估算工具，用来学习和做预算保护，不等于真实计费结果。真实 token 数以后要以模型 API 响应里的 `usage` 为准。

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
mock_chat_requested message_length=...
```

日志格式会自动带上当前请求的 `trace_id`：

```text
trace_id=...
```

注意：日志只记录消息长度，不记录完整用户输入，避免把敏感内容写入日志。

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
| POST | `/chat` | 模拟聊天接口，返回 mock 回复 |

## 当前模型

| 模型 | 路径 | 说明 |
| --- | --- | --- |
| `ChatRequest` | `app/schemas/chat.py` | 聊天请求体，要求 `message` 是非空字符串 |
| `ChatResponse` | `app/schemas/chat.py` | 聊天响应体，要求 `reply` 是非空字符串 |
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

下一阶段进入 LLM API 基础调用，把当前 mock `/chat` 逐步替换成真实大模型调用。
