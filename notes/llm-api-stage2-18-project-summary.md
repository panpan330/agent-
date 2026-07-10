# 阶段 2 第 18 节：阶段 2 项目整理

## 1. 这一节学什么

这一节是阶段 2 收尾。

它不继续堆新功能，而是做四件事：

```text
复盘阶段 2 已经学过什么
补齐模型参数基础
补齐 OpenAI-compatible 兼容差异
确认 ai-service 是否达到阶段 2 验收标准
```

阶段 2 的核心目标是：

```text
让 Python FastAPI 服务能够稳定、安全、可测试地调用 LLM API
```

你现在已经不是只会写一行 SDK 调用。

你已经有了一个基础 AI 服务调用底座。

## 2. 阶段 2 的边界

阶段 2 学的是：

```text
LLM API 基础调用
```

它不负责一次性学完：

```text
RAG
embedding
向量数据库
LangChain
LangGraph
Tool Calling
Agent 状态机
Java 业务工具调用
Docker 部署
生产级鉴权
复杂 eval
```

这些后面会专门学。

阶段 2 只解决一个基础问题：

```text
后端怎么可靠地调用大模型 API
```

所以本阶段重点是：

```text
配置
调用
messages
prompt
token
timeout
retry
rate limit
错误处理
日志
streaming
结构化输出
测试
```

## 3. 阶段 2 学习清单

阶段 2 一共 18 节：

| 节 | 主题 | 你应该掌握什么 |
| --- | --- | --- |
| 1 | 什么是 LLM API | 后端通过 API 调模型 |
| 2 | API key 和 `.env` 安全配置 | key 不进代码和 GitHub |
| 3 | token、上下文窗口、费用 | 输入输出都会消耗 token |
| 4 | OpenAI-compatible SDK | 用 OpenAI SDK 调兼容接口 |
| 5 | messages | system/user/assistant 的职责 |
| 6 | prompt 基础 | 任务、要求、格式、失败策略 |
| 7 | 真实 `/chat` | 从 mock 变成真实模型调用 |
| 8 | 多轮 history | 把历史消息传给模型 |
| 9 | timeout | 超时返回统一错误 |
| 10 | retry / rate limit | 理解重试和限流 |
| 11 | 模型错误处理 | SDK 错误映射成业务错误 |
| 12 | 模型调用日志 | 模型名、耗时、token、错误码 |
| 13 | streaming 概念 | 理解流式返回 |
| 14 | `/stream-chat` | 用 SSE 逐块返回 |
| 15 | 结构化输出概念 | JSON、JSON Schema、Pydantic |
| 16 | Pydantic 约束结构化输出 | `/extract-ticket` |
| 17 | mock / fake LLM client | 不真实调模型也能测试 |
| 18 | 阶段 2 项目整理 | 收尾验收和复盘 |

这些合起来就是 AI 服务调用层的基础。

## 4. 当前 ai-service 有哪些接口

项目位置：

```text
projects/ai-service
```

当前接口：

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| `GET` | `/health` | 健康检查 |
| `POST` | `/chat` | 普通聊天，返回完整回复 |
| `POST` | `/stream-chat` | 流式聊天，通过 SSE 逐块返回 |
| `POST` | `/extract-ticket` | 工单字段结构化抽取 |

这说明项目已经从普通 Web API 进入了 AI 服务 API。

## 5. 三条核心调用链路

普通聊天：

```text
POST /chat
-> app/routers/chat.py
-> LLMChatService.generate_reply()
-> build_chat_messages()
-> build_chat_prompt()
-> create_openai_compatible_client()
-> client.chat.completions.create(...)
-> extract_first_reply()
-> ChatResponse
```

流式聊天：

```text
POST /stream-chat
-> app/routers/chat.py
-> LLMChatService.stream_reply()
-> client.chat.completions.create(..., stream=True)
-> extract_stream_delta_content()
-> format_sse_event()
-> StreamingResponse
```

结构化输出：

```text
POST /extract-ticket
-> app/routers/chat.py
-> StructuredOutputService.extract_ticket()
-> build_ticket_extraction_messages()
-> client.chat.completions.create(..., response_format={"type":"json_object"})
-> parse_ticket_extraction_json()
-> TicketExtraction.model_validate_json()
-> StructuredOutputResponse
```

你要能把这三条链路讲出来。

这比只会复制 SDK 示例更重要。

## 6. 当前项目分层

项目现在大致分成：

| 层 | 文件或目录 | 作用 |
| --- | --- | --- |
| app 入口 | `app/main.py` | 创建 FastAPI 应用 |
| router | `app/routers/` | 接 HTTP 请求，返回 HTTP 响应 |
| schema | `app/schemas/` | 请求和响应数据契约 |
| service | `app/services/` | 业务逻辑和模型调用 |
| core | `app/core/` | 配置、日志、异常、trace、CORS |
| middleware | `app/middleware/` | 请求追踪 |
| tests | `tests/` | 自动化测试 |
| scripts | `scripts/` | 手动检查脚本 |

分层的好处是：

```text
router 不关心 SDK 细节
service 不关心 HTTP 响应格式
schema 专门负责数据契约
core 专门负责通用基础设施
tests 可以分层测试
```

这就是后端工程能力。

## 7. 补充知识 1：模型参数是什么

调用模型时，除了：

```text
model
messages
```

还可以传很多参数。

这些参数会影响：

```text
输出长度
输出随机性
输出格式
是否流式返回
是否调用工具
```

常见参数包括：

```text
temperature
top_p
max_completion_tokens / max_tokens / max_output_tokens
stream
stream_options
response_format
stop
tools
tool_choice
```

阶段 2 只需要掌握基础参数。

工具调用参数后面再学。

## 8. `temperature`

`temperature` 控制输出随机性。

先用人话理解：

```text
temperature 越低，回答越稳定、越保守
temperature 越高，回答越发散、越有变化
```

常见经验：

| 场景 | 建议 |
| --- | --- |
| 分类、抽取、结构化输出 | 低一点 |
| 代码生成、严谨问答 | 低到中等 |
| 头脑风暴、文案创意 | 可以高一点 |

例如：

```text
temperature=0.2
```

更适合：

```text
工单字段抽取
意图识别
格式固定的回答
```

但要记住：

```text
低 temperature 不等于绝对正确
```

结构化输出仍然要 Pydantic 校验。

## 9. `top_p`

`top_p` 也是控制随机性的参数。

它和 `temperature` 都会影响模型怎么选择下一个 token。

OpenAI 文档建议通常调整 `temperature` 或 `top_p` 其中一个，不要两个一起乱调。

初学阶段可以先记住：

```text
先用 temperature
不要同时改 temperature 和 top_p
除非你明确知道自己在调什么
```

当前项目没有暴露这两个参数。

这是合理的。

因为当前重点是调用链路稳定，而不是微调模型风格。

## 10. 输出 token 上限

不同 API 对输出上限参数命名可能不同：

```text
max_tokens
max_completion_tokens
max_output_tokens
```

OpenAI Chat Completions 文档里有：

```text
max_completion_tokens
```

它表示 completion 最多生成多少 token。

本项目配置里已经有：

```text
MAX_OUTPUT_TOKENS
```

但目前还没有真正传给模型。

后续可以补：

```python
client.chat.completions.create(
    model=...,
    messages=...,
    max_completion_tokens=settings.max_output_tokens,
)
```

不过要先确认当前服务商兼容接口支持哪个参数名。

## 11. `stream`

`stream=True` 表示：

```text
不要等完整回答生成完再返回
而是边生成边返回
```

本项目在 `/stream-chat` 里已经使用：

```python
stream=True
stream_options={"include_usage": True}
```

流式输出的好处是：

```text
用户更快看到内容
长回答体验更好
```

复杂点是：

```text
每个 chunk 可能没有内容
usage 可能在最后出现
流开始后不能再改 HTTP 状态码
错误需要用 SSE error 事件表达
```

## 12. `response_format`

`response_format` 用来约束输出格式。

本项目使用：

```python
response_format={"type": "json_object"}
```

这表示 JSON Mode。

OpenAI 文档里还有更强的 JSON Schema 结构化输出：

```python
response_format={
    "type": "json_schema",
    "json_schema": {...}
}
```

但你当前项目使用 OpenAI-compatible 服务。

所以更兼容的做法是：

```text
JSON Mode + Pydantic 后端校验
```

JSON Mode 让模型更容易返回合法 JSON。

Pydantic 负责后端最终验收。

## 13. `stop`

`stop` 用来指定停止生成的标记。

例如：

```python
stop=["\n\n用户:"]
```

当模型生成到这个片段时停止。

初学阶段不建议乱用。

原因是：

```text
stop 配错会截断正常回答
不同模型支持情况可能不同
结构化 JSON 被截断会解析失败
```

当前项目不使用 `stop` 是合理的。

## 14. 参数不要一开始全开放

有些人一开始就想把所有参数都放进 `.env`：

```text
LLM_TEMPERATURE
LLM_TOP_P
LLM_MAX_TOKENS
LLM_STOP
LLM_REASONING_EFFORT
LLM_VERBOSITY
```

这不一定是好事。

参数越多：

```text
配置越复杂
测试组合越多
排查问题越难
```

更好的策略是：

```text
先固定简单参数
只开放必须配置的 key、base_url、model、timeout、retry
等业务需要明确后，再增加 temperature、输出上限等参数
```

这叫工程上的克制。

## 15. 补充知识 2：OpenAI-compatible 不等于完全一样

`OpenAI-compatible` 的意思是：

```text
接口形态和 OpenAI 类似
可以使用 OpenAI SDK
可以配置 base_url
可以调用类似 /chat/completions 的接口
```

但它不等于 100% 一样。

可能不同的地方包括：

```text
模型名称不同
base_url 不同
支持的参数不同
支持的 response_format 不同
错误码细节不同
usage 返回位置不同
stream_options 支持情况不同
工具调用格式细节不同
结构化输出能力不同
```

所以以后看到兼容接口，要这样理解：

```text
调用方式大体兼容，细节以当前服务商文档为准
```

## 16. 当前项目怎么处理兼容差异

当前项目通过几种方式隔离兼容差异：

```text
Settings 里配置 llm_provider
Settings 里配置 llm_model
Settings 里配置 llm_base_url
Settings 里配置 llm_api_key
llm_client.py 统一创建 SDK client
llm_service.py 统一解析返回和映射错误
structured_output_service.py 单独处理 JSON Mode
tests/fakes.py 固定当前项目依赖的 SDK 结构
```

也就是说，兼容差异没有散落在所有 router 里。

主要集中在：

```text
app/services/llm_client.py
app/services/llm_service.py
app/services/structured_output_service.py
```

这叫隔离外部依赖。

## 17. 当前项目为什么还不用 LangChain

你后面会学 LangChain。

但现在不急着用。

原因是：

```text
先学底层 API，知道模型调用本质是什么
再学框架，才能理解框架帮你封装了什么
```

如果一开始就用 LangChain，很容易变成：

```text
会调用链，但不知道底层 HTTP/API/messages/token/error 怎么回事
```

现在你先学了底层，再学 LangChain 会更稳。

## 18. 当前项目为什么还不用 Tool Calling

Tool Calling 要解决的是：

```text
模型决定调用哪个工具
模型生成工具参数
后端执行工具
把工具结果再给模型
模型生成最终回答
```

这比阶段 2 复杂。

阶段 2 先解决：

```text
怎么稳定调用模型
怎么处理模型返回
怎么测试模型调用
```

等这些稳了，再学 Tool Calling。

## 19. 当前项目为什么还不用 RAG

RAG 需要另外一套能力：

```text
文档解析
chunk 切分
embedding
向量数据库
检索
rerank
引用来源
无答案处理
权限过滤
```

这不是 LLM API 基础调用本身。

所以阶段 2 不学 RAG 是合理的。

## 20. 当前配置能力

当前配置入口：

```text
app/core/config.py
```

重要配置包括：

```text
LLM_PROVIDER
LLM_MODEL
LLM_BASE_URL
LLM_API_KEY
OPENAI_API_KEY
REQUEST_TIMEOUT_SECONDS
LLM_MAX_RETRIES
MAX_OUTPUT_TOKENS
LOG_LEVEL
CORS_ALLOWED_ORIGINS
```

你应该知道：

```text
.env.example 可以提交
.env 不提交
真实 key 只放本机 .env 或系统环境变量
```

这是安全底线。

## 21. 当前错误处理能力

当前模型调用错误会统一转成：

| 错误码 | 含义 |
| --- | --- |
| `LLM_API_KEY_MISSING` | 没有配置 key |
| `LLM_TIMEOUT` | 模型调用超时 |
| `LLM_RATE_LIMITED` | 模型服务限流 |
| `LLM_AUTHENTICATION_FAILED` | 认证失败 |
| `LLM_PERMISSION_DENIED` | 权限不足 |
| `LLM_RESOURCE_NOT_FOUND` | 模型或资源不存在 |
| `LLM_BAD_REQUEST` | 请求参数错误 |
| `LLM_PROVIDER_ERROR` | 模型服务内部错误 |
| `LLM_CONNECTION_ERROR` | 网络连接失败 |
| `LLM_BAD_RESPONSE` | 返回结构异常 |
| `LLM_EMPTY_RESPONSE` | 返回空内容 |
| `STRUCTURED_OUTPUT_VALIDATION_FAILED` | 结构化输出校验失败 |

这些错误会通过统一异常处理返回稳定 JSON。

不会直接把底层 SDK 异常暴露给用户。

## 22. 当前日志能力

当前日志记录：

```text
请求进入
模型名
服务商
耗时
token usage
错误码
trace_id
流式 chunks 数量
结构化输出 intent/urgency 等元信息
```

当前日志不记录：

```text
完整用户输入
完整 history
完整 prompt
完整模型回复
API key
```

这是重要安全习惯。

## 23. 当前测试能力

当前测试覆盖：

```text
健康检查
chat API
stream-chat API
extract-ticket API
Pydantic 请求/响应模型
配置读取
CORS
trace_id
统一异常处理
日志
message builder
prompt builder
token usage
LLM client 初始化
LLM service
structured output service
fake OpenAI-compatible client
OpenAI SDK 错误映射
```

测试证明：

```text
模型不在线时，业务代码仍然可以被验证
```

## 24. 当前手动检查能力

当前脚本：

```text
scripts/llm_compatible_smoke_test.py
```

默认运行：

```powershell
uv run python scripts\llm_compatible_smoke_test.py
```

只检查配置，不真实调用模型。

真实调用要显式加：

```powershell
uv run python scripts\llm_compatible_smoke_test.py --call
```

这样设计是对的。

因为真实调用可能产生费用。

## 25. 阶段 2 验收清单

阶段 2 完成后，你应该能做到：

```text
知道什么是 LLM API
知道 API key 为什么不能进 GitHub
知道 token、上下文窗口和费用的基本关系
能解释 system/user/assistant
能解释 prompt 为什么要结构化
能启动 FastAPI 服务
能调用 /chat
能传 history 做多轮对话
能解释 timeout、retry、rate limit
能解释模型错误映射
能看懂模型调用日志
能解释 streaming 和 SSE
能调用 /stream-chat
能解释结构化输出、JSON Mode、JSON Schema、Pydantic
能调用 /extract-ticket
能解释为什么测试不用真实模型
能看懂 fake LLM client
能跑完整 pytest
```

如果你能讲清这些，阶段 2 就够扎实。

## 26. 当前阶段暂时没做什么

暂时没做：

```text
把 MAX_OUTPUT_TOKENS 真实传给模型
把 temperature 做成配置
把 response_format 升级成 JSON Schema 模式
引入 Tool Calling
引入 LangChain
引入 LangGraph
引入 RAG
做 eval 数据集
做 Docker Compose 部署
做前端页面
接 Java 业务服务
```

这些不是遗漏。

它们是后续阶段内容。

## 27. 如果还要补一个小代码点

如果阶段 2 后面还要补一个小代码点，我建议优先补：

```text
把 MAX_OUTPUT_TOKENS 传给模型调用
```

原因是它和：

```text
输出长度
token 成本
超时风险
```

都有关系。

但要先确认当前服务商兼容接口支持的参数名。

所以本节先作为知识点记录，不急着动代码。

## 28. 下一阶段建议学什么

下一阶段建议进入：

```text
LangChain + Java 工具调用基础
```

因为你的长期目标包括：

```text
智能工单 Agent
企业知识库 RAG
Java 后端 + Python AI 服务协作
```

阶段 2 已经解决模型调用。

下一阶段要解决：

```text
AI 服务怎么调用外部工具
AI 怎么和 Java 业务系统连接
怎么把模型输出变成业务动作
```

这会自然引出：

```text
Tool Calling
LangChain
Java mock 业务 API
```

## 29. 阶段 2 怎么复习

建议按这个顺序复习：

```text
1. 先看 ai-service README，理解项目现在能做什么
2. 再看第 7 节，确认 /chat 真实调用链路
3. 再看第 11、12 节，确认错误和日志
4. 再看第 14 节，确认 /stream-chat
5. 再看第 16 节，确认 /extract-ticket
6. 再看第 17 节，确认 fake 测试
7. 最后看本节，串起来
```

复习时不要只读。

要配合运行：

```powershell
uv run pytest -q
uv run python scripts\llm_compatible_smoke_test.py
```

## 30. 本节练习

### 练习 1

题目：

阶段 2 的核心目标是什么？

参考答案：

阶段 2 的核心目标是让 Python FastAPI 服务能够稳定、安全、可测试地调用 LLM API，包括配置、调用、messages、prompt、错误、日志、流式、结构化输出和测试。

### 练习 2

题目：

为什么 `OpenAI-compatible` 不等于完全一样？

参考答案：

因为兼容通常表示接口形态和 SDK 调用方式大体类似，但模型名称、支持参数、结构化输出能力、错误码、流式 usage、工具调用细节等仍可能因服务商不同而不同。

### 练习 3

题目：

`temperature` 大致控制什么？

参考答案：

它控制输出随机性。值越低，输出通常越稳定、保守；值越高，输出通常越发散、有变化。

### 练习 4

题目：

为什么不建议初学阶段同时调整 `temperature` 和 `top_p`？

参考答案：

因为它们都影响采样随机性，同时调整会让输出变化原因更难判断。通常调整其中一个即可。

### 练习 5

题目：

`response_format={"type":"json_object"}` 的作用是什么？

参考答案：

它启用 JSON Mode，让模型更倾向于返回合法 JSON。但它不保证业务字段完全符合 schema，所以后端仍然需要 Pydantic 校验。

### 练习 6

题目：

为什么当前项目把兼容接口差异集中在 service/client 层，而不是写在 router 里？

参考答案：

因为 router 应该只处理 HTTP 请求和响应。模型服务商差异属于外部依赖细节，集中在 client/service 层更容易维护、测试和替换。

### 练习 7

题目：

当前项目的三条核心 AI 调用链路是什么？

参考答案：

`/chat` 普通完整回复链路，`/stream-chat` 流式 SSE 链路，`/extract-ticket` 结构化输出链路。

### 练习 8

题目：

为什么阶段 2 暂时不学 RAG？

参考答案：

RAG 需要文档解析、chunk、embedding、向量数据库、检索、引用和权限过滤等额外能力。阶段 2 的重点是 LLM API 基础调用，RAG 应该放到后续阶段。

### 练习 9

题目：

为什么测试模型调用时要用 fake LLM client？

参考答案：

因为真实模型调用会产生费用、依赖网络、输出不稳定。fake client 能让测试快速、稳定、可重复，并且能验证调用参数和错误处理。

### 练习 10

题目：

如果要在阶段 2 后补一个小代码点，优先补什么？

参考答案：

可以优先把 `MAX_OUTPUT_TOKENS` 真实传给模型调用，用来限制输出长度和控制成本。但要先确认当前服务商兼容接口支持的参数名。

## 31. 本节自测

### 自测 1

题目：

阶段 2 完成后，当前项目有哪几个 HTTP 接口？

参考答案：

`GET /health`、`POST /chat`、`POST /stream-chat`、`POST /extract-ticket`。

### 自测 2

题目：

普通聊天接口最终返回哪个响应模型？

参考答案：

`ChatResponse`。

### 自测 3

题目：

结构化工单抽取最终使用哪个 Pydantic 模型校验模型输出？

参考答案：

`TicketExtraction`。

### 自测 4

题目：

流式输出使用 FastAPI 的哪个响应类？

参考答案：

`StreamingResponse`。

### 自测 5

题目：

当前项目里创建 OpenAI-compatible SDK client 的文件是什么？

参考答案：

`app/services/llm_client.py`。

### 自测 6

题目：

当前项目里 fake OpenAI-compatible client 放在哪里？

参考答案：

`tests/fakes.py`。

### 自测 7

题目：

真实 `.env` 文件是否应该提交到 GitHub？

参考答案：

不应该。真实 `.env` 只放本机，GitHub 只提交 `.env.example`。

### 自测 8

题目：

模型返回 JSON 后是否可以直接写入业务系统？

参考答案：

不可以。应该先经过 Pydantic 校验，再经过业务规则和权限校验。

### 自测 9

题目：

阶段 2 后下一阶段建议学什么？

参考答案：

建议进入 LangChain + Java 工具调用基础，为智能工单 Agent 和 Java 业务系统集成做准备。

### 自测 10

题目：

阶段 2 学完后，最重要的能力是什么？

参考答案：

能把 LLM API 调用做成一个稳定、安全、可测试的后端服务能力，而不是只会手动调一次模型。

## 32. 本节小结

阶段 2 已经完成：

```text
LLM API 概念
API key 安全
token 和成本
OpenAI-compatible SDK
messages
prompt
真实 /chat
多轮 history
timeout
retry 和 rate limit
错误处理
模型调用日志
streaming
/stream-chat
结构化输出
Pydantic 校验
/extract-ticket
fake LLM client 测试
阶段 2 整体复盘
```

最重要的一句话：

```text
LLM API 调用不是一行 SDK 代码，而是一整套配置、安全、消息、prompt、错误、日志、输出解析和测试体系。
```

## 33. 参考资料

- [OpenAI：Create chat completion](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create/)
- [阿里云百炼：OpenAI 兼容 Chat](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions)
- [阿里云百炼：结构化输出](https://help.aliyun.com/en/model-studio/qwen-structured-output)
- [阿里云百炼：文本生成模型 API 参考](https://help.aliyun.com/zh/model-studio/qwen-api-reference/)
