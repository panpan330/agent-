# AI Service

Python AI 服务项目。当前处于阶段 1：FastAPI 服务基础。

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

当前测试使用 FastAPI 的 `TestClient`，覆盖 `/health`、`/chat`、`ChatRequest`、`ChatResponse` 和配置读取。

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
| `LOG_LEVEL` | 日志级别，下一节会使用 |
| `OPENAI_API_KEY` | 后续接真实大模型时使用，不能写死在代码里 |

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

注意：日志只记录消息长度，不记录完整用户输入，避免把敏感内容写入日志。

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
