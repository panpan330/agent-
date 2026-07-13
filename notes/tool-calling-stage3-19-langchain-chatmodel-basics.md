# 阶段 3 第 19 节：LangChain ChatModel 基础

> 本节结论：LangChain ChatModel 是对“聊天模型调用”的统一封装。它不是 Agent，也不会自动调用工具。它把不同模型服务的调用整理成相似的输入输出形式：输入是字符串或消息列表，输出是 `AIMessage`。本节我们新增 `/langchain-chat` 学习接口，用它和原来的 `/chat` 做对照，理解 LangChain 到底从模型调用层封装了什么。

## 生成笔记前的教学复核

本节必须满足这些教学要求：

```text
1. 先讲清 ChatModel 是什么，再讲 ChatOpenAI 是什么。
2. 讲清 ChatModel 和 LLM、Agent、Tool Calling 的区别。
3. 讲清 LangChain message 和我们项目 ChatMessage 的关系。
4. 讲清 invoke() 的输入、输出和边界。
5. 讲清为什么本节新增 /langchain-chat，而不是直接替换 /chat。
6. 讲清新增代码每一层解决什么学习问题。
7. 测试只讲关键意图，不逐行解释。
8. 不提前学习 LangChain Tool、Agent、Runnable 链式组合、streaming 和 LangGraph。
```

## 本节一句话定位

第 19 节是在理解 LangChain 框架定位之后，学习它最基础的模型调用抽象：ChatModel，并把它以一个独立接口接入当前 FastAPI 项目。

## 本节解决的真实问题

上一节我们已经知道：

```text
LangChain 是 LLM 应用开发框架
它可以封装模型、Prompt、Tool、结构化输出和 Agent 循环
但它不能替代业务权限、安全、幂等和校验边界
```

现在要解决的问题是：

```text
如果只看模型调用这一层，LangChain 到底怎么调用模型？
它和我们手写 OpenAI-compatible SDK 调用有什么区别？
项目里应该怎么引入它，才不会一上来就把现有代码推翻？
```

本节新增一个学习接口：

```text
POST /langchain-chat
```

它和已有接口的关系是：

```text
/chat            -> 直接使用 OpenAI-compatible SDK
/langchain-chat  -> 使用 LangChain ChatModel
/tool-chat       -> 仍然是我们手写的工具调用链路
```

这样你可以清楚比较两条模型调用路径，而不是把两种写法混在一起。

## 本节新增能力

学完后你应该能做到：

- 能解释 ChatModel 是什么；
- 能解释 `ChatOpenAI` 和 OpenAI-compatible SDK 的关系；
- 能说清 `SystemMessage`、`HumanMessage`、`AIMessage` 分别表示什么；
- 能说清 `invoke()` 是一次完整模型调用；
- 能解释为什么 ChatModel 返回的是 `AIMessage`，不是普通字符串；
- 能看懂当前项目如何把 `ChatRequest` 转成 LangChain messages；
- 能解释 `/chat` 和 `/langchain-chat` 的差异；
- 能判断 ChatModel 只是模型调用封装，不等于 Agent。

## 和上一节的区别

第 18 节学的是：

```text
LangChain 是什么，为什么现在才引入。
```

第 19 节学的是：

```text
LangChain 里最基础的模型调用组件 ChatModel 怎么落地。
```

简单说：

```text
第 18 节：认识框架的位置
第 19 节：学习框架里的第一个核心组件
```

## 基础知识铺垫

### 1. 什么是 model

model 就是模型。

在 AI 应用里，模型通常指：

```text
接收输入
生成输出
能处理自然语言、图片、音频或其他内容的 AI 服务
```

我们当前主要接触的是文本聊天模型，比如：

```text
qwen3.7-plus
gpt-4o
gpt-5-nano
deepseek-chat
```

模型本身不在我们项目里运行。我们的 Python 服务只是通过 API 去调用模型服务。

### 2. 什么是 LLM

LLM 是 Large Language Model，大语言模型。

早期很多 LLM 接口更像这样：

```text
输入：一大段 prompt 字符串
输出：一大段 completion 字符串
```

例如：

```text
Prompt:
请解释 FastAPI 是什么

Completion:
FastAPI 是一个 Python Web 框架...
```

这种模式更像“文本补全”。

### 3. 什么是 ChatModel

ChatModel 是聊天模型。

它不是只接收一段字符串，而是接收一组有角色的消息：

```text
system: 你是一个耐心的编程学习助手
user: 什么是 API？
assistant: API 是程序之间的接口
user: 那 FastAPI 呢？
```

模型会根据这一串消息生成新的 assistant 回复。

所以 ChatModel 的核心思想是：

```text
输入是 message 序列
输出也是 message
```

这比单纯字符串更适合多轮对话、系统指令、工具调用和上下文管理。

### 4. ChatModel 和 LLM 的区别

可以先用一句话区分：

```text
LLM 更像“文本补全模型”
ChatModel 更像“对话消息模型”
```

工程上你需要知道：

```text
传统 LLM 输入输出更偏字符串
ChatModel 输入输出更偏有角色的消息
```

当前主流大模型 API 大多是 chat model 风格。

我们前面学的 OpenAI-compatible Chat Completions，本质上也是 chat model 调用：

```python
client.chat.completions.create(
    model="qwen-test",
    messages=[
        {"role": "system", "content": "你是一个助手"},
        {"role": "user", "content": "解释 FastAPI"},
    ],
)
```

LangChain 的 ChatModel 是把这类调用再抽象一层。

### 5. 什么是 LangChain ChatModel

LangChain ChatModel 是 LangChain 对聊天模型的统一接口。

它想解决的问题是：

```text
不同模型服务商都有自己的 SDK、参数和响应结构
但聊天模型的核心行为很像
```

核心行为是：

```text
给模型一组消息
模型返回一条 AI 消息
```

LangChain 用相对统一的对象来表达这个过程。

例如：

```text
输入：
[
  SystemMessage("你是一个助手"),
  HumanMessage("解释 API")
]

输出：
AIMessage("API 是程序之间的接口...")
```

### 6. 什么是 ChatOpenAI

`ChatOpenAI` 是 LangChain 里连接 OpenAI Chat API 的实现类。

它来自：

```python
from langchain_openai import ChatOpenAI
```

名字里有 OpenAI，但它也可以用于很多 OpenAI-compatible 的 Chat Completions 接口。

官方文档也说明：某些模型提供商如果提供兼容 OpenAI Chat Completions API 的端点，可以用 `ChatOpenAI` 配合自定义 `base_url` 做基础聊天调用。

但要注意一个边界：

```text
ChatOpenAI 主要按官方 OpenAI API 规格处理响应。
第三方兼容服务的非标准字段，不一定会被保留或提取。
```

这对你使用千问兼容接口很重要：

```text
普通聊天内容通常可以用
但某些服务商特有字段，例如特殊 reasoning 字段，不能默认认为 LangChain 会完整保留
```

所以本节只做普通聊天调用，不学习 reasoning、tools 或 structured output 的服务商扩展能力。

### 7. 什么是 message object

我们项目原来使用的是自己的 `ChatMessage`：

```python
class ChatMessage(BaseModel):
    role: ChatMessageRole
    content: str
```

它是 API 边界上的数据模型，用来接收请求、校验请求、生成接口文档。

LangChain 也有自己的 message object：

```text
SystemMessage
HumanMessage
AIMessage
ToolMessage
```

这些是 LangChain 内部给 ChatModel 使用的消息对象。

两者不是同一个东西：

```text
项目 ChatMessage：我们的 API 请求/响应边界
LangChain Message：LangChain 调用模型时使用的内部对象
```

因此我们需要一个转换函数。

这不是多余代码，而是边界意识：

```text
外部接口用项目自己的 schema
内部模型调用再转成框架需要的对象
```

### 8. SystemMessage 是什么

`SystemMessage` 表示系统指令。

作用是告诉模型：

```text
你是谁
你应该按什么风格回答
你要遵守哪些总体规则
```

例如：

```text
你是一个耐心的编程学习助手，回答要简洁清楚。
```

它对应 OpenAI-compatible messages 里的：

```json
{"role": "system", "content": "..."}
```

### 9. HumanMessage 是什么

`HumanMessage` 表示用户输入。

它对应 OpenAI-compatible messages 里的：

```json
{"role": "user", "content": "..."}
```

在我们的项目里，本轮用户问题最终会变成 `HumanMessage`。

历史里的用户消息也会变成 `HumanMessage`。

### 10. AIMessage 是什么

`AIMessage` 表示模型输出。

它对应 OpenAI-compatible messages 里的：

```json
{"role": "assistant", "content": "..."}
```

但 LangChain 的 `AIMessage` 不只是普通字符串。它还可能包含：

```text
content
text
tool_calls
usage_metadata
response_metadata
id
```

这就是为什么 ChatModel 返回的是 `AIMessage`，不是直接返回字符串。

如果你只关心最终文本，可以从 `AIMessage.text` 或 `AIMessage.content` 里取。

但从工程角度看，保留 `AIMessage` 很有价值，因为后面学 Tool Calling 时，工具调用请求就可能在 `AIMessage.tool_calls` 里。

### 11. 什么是 invoke()

`invoke()` 是 LangChain 里很常见的调用方法。

对 ChatModel 来说：

```text
model.invoke(input)
```

表示：

```text
把 input 发给模型
等待模型完整生成
返回一条 AIMessage
```

它和我们之前直接调用 SDK 的关系可以这样理解：

```text
OpenAI-compatible SDK:
client.chat.completions.create(...)

LangChain ChatModel:
model.invoke(...)
```

`invoke()` 不是流式输出，不是工具循环，也不是 Agent。它就是一次普通调用。

### 12. ChatModel 和 Agent 的区别

这是本节必须分清的点。

ChatModel 做的是：

```text
输入消息 -> 输出 AIMessage
```

Agent 做的是：

```text
输入任务
-> 模型判断
-> 可能调用工具
-> 工具结果回到模型
-> 可能继续判断
-> 最终回答
```

所以：

```text
ChatModel 是 Agent 的底层组件之一
Agent 不是 ChatModel 本身
```

本节只学 ChatModel，不学 Agent。

## 本节主题系统讲解

### 1. 为什么先学 ChatModel

因为任何 LangChain 应用最后都离不开模型调用。

不管后面是：

```text
PromptTemplate
Tool
Agent
RAG
LangGraph
```

都要有一个最基础的问题：

```text
模型怎么被调用？
模型吃什么输入？
模型吐出什么输出？
```

ChatModel 就是回答这个问题的第一层抽象。

### 2. 原生 SDK 调用路径

我们已有的 `/chat` 走的是这条路径：

```text
POST /chat
-> ChatRequest
-> LLMChatService
-> build_chat_messages()
-> serialize_chat_messages()
-> OpenAI-compatible client
-> client.chat.completions.create(...)
-> completion.choices[0].message.content
-> ChatResponse
```

这里我们直接面对 OpenAI-compatible SDK 的结构：

```text
messages 是 dict 列表
返回值是 completion 对象
文本藏在 choices[0].message.content
```

优点：

```text
透明
依赖少
容易理解底层 API
```

缺点：

```text
以后切换模型集成、组合 prompt/tool/chain 时，需要自己写更多编排代码
```

### 3. LangChain ChatModel 调用路径

本节新增的 `/langchain-chat` 走的是这条路径：

```text
POST /langchain-chat
-> ChatRequest
-> LangChainChatModelService
-> build_langchain_chat_messages()
-> SystemMessage / HumanMessage / AIMessage
-> ChatOpenAI
-> model.invoke(...)
-> AIMessage
-> extract_langchain_reply()
-> ChatResponse
```

这里我们面对的是 LangChain 的结构：

```text
messages 是 LangChain message object
返回值是 AIMessage
文本可以从 text/content 取
```

优点：

```text
更接近 LangChain 后续的 Tool、Agent、Runnable 生态
消息对象保留更多元信息
后续组合能力更强
```

缺点：

```text
多了一层框架抽象
需要理解 LangChain message 和项目 schema 的转换
第三方兼容服务的非标准字段不一定完整保留
```

### 4. 为什么不直接替换 /chat

本节没有把 `/chat` 改成 LangChain 写法，而是新增 `/langchain-chat`。

原因有三个。

第一，学习上需要对比。

```text
/chat           让你看到原生 SDK 调用
/langchain-chat 让你看到 LangChain 封装调用
```

如果直接替换，你就很难看出框架到底帮你封装了什么。

第二，工程上要降低风险。

`/chat` 是已有功能，很多测试和后续服务依赖它。直接替换会扩大影响面。

第三，后续可以渐进迁移。

真实项目里引入框架，通常不应该一把推翻旧实现，而是：

```text
先并行接入
再验证行为
再决定是否替换
```

这是一种更稳的工程策略。

### 5. 为什么仍然保留项目自己的 ChatRequest

既然 LangChain 有 message object，为什么接口不直接接收 LangChain message？

因为 LangChain message 是框架内部对象，不适合作为我们的 HTTP API 边界。

API 边界应该考虑：

```text
请求校验
字段说明
OpenAPI 文档
错误响应
前端调用稳定性
版本兼容
```

这些都更适合用项目自己的 Pydantic schema 表达。

所以正确边界是：

```text
外部请求 -> ChatRequest
内部调用 -> LangChain messages
```

这也是后端工程里的常见模式：

```text
DTO / Request Model 不等于内部领域对象
```

### 6. 为什么仍然保留 AppException

LangChain 调用模型时可能抛出底层 OpenAI SDK 异常，也可能抛出其他框架异常。

但我们的 API 不能把这些内部异常原样丢给前端。

所以 service 层仍然要做统一错误映射：

```text
无 API key -> LLM_API_KEY_MISSING
模型返回空内容 -> LLM_EMPTY_RESPONSE
未知模型调用错误 -> LLM_CALL_FAILED
```

这说明一件事：

```text
LangChain 可以封装模型调用，但不能替代项目的错误响应规范。
```

### 7. 为什么测试不用真实 LangChain 模型调用

本节虽然引入 LangChain，但自动化测试仍然不能真实调用模型。

测试里用的是 fake model：

```text
FakeLangChainChatModel.invoke(messages)
```

它只做两件事：

```text
记录传入的 messages
返回一个假的 AIMessage
```

这样测试可以验证：

```text
项目消息是否正确转成 LangChain messages
service 是否调用了 invoke()
返回 AIMessage 后是否正确提取文本
接口是否仍然走统一错误格式
```

不会花钱，也不会依赖网络。

## 最小心智模型

本节最小链路是：

```text
ChatRequest
-> 项目自己的 ChatMessage
-> LangChain BaseMessage
-> ChatOpenAI.invoke()
-> AIMessage
-> reply 字符串
-> ChatResponse
```

最重要的边界是：

```text
项目 API 边界：Pydantic schema
LangChain 模型边界：SystemMessage / HumanMessage / AIMessage
模型调用边界：invoke()
接口输出边界：ChatResponse
```

一句话记忆：

```text
ChatModel 是“消息进、AIMessage 出”的模型调用封装。
```

## 当前项目如何落地

本节新增和修改了这些文件：

```text
projects/ai-service/pyproject.toml
projects/ai-service/uv.lock
projects/ai-service/app/services/langchain_chat_model_service.py
projects/ai-service/app/routers/chat.py
projects/ai-service/tests/test_langchain_chat_model_service.py
projects/ai-service/tests/test_chat_api.py
```

新增依赖：

```text
langchain-openai
```

它会带上：

```text
langchain-core
langsmith
tenacity
tiktoken
```

本节我们真正直接使用的是：

```text
langchain_openai.ChatOpenAI
langchain_core.messages.SystemMessage
langchain_core.messages.HumanMessage
langchain_core.messages.AIMessage
```

## 关键代码讲解

### 1. 创建 ChatOpenAI

文件：

```text
projects/ai-service/app/services/langchain_chat_model_service.py
```

核心函数：

```python
def create_langchain_chat_model(settings: Settings) -> ChatOpenAI:
    api_key = settings.resolved_llm_api_key
    if api_key is None:
        raise ValueError("LLM_API_KEY is not configured")

    model_kwargs = {
        "model": settings.llm_model,
        "api_key": api_key,
        "timeout": settings.request_timeout_seconds,
        "max_retries": settings.llm_max_retries,
    }

    base_url = settings.resolved_llm_base_url
    if base_url is not None:
        model_kwargs["base_url"] = base_url

    return ChatOpenAI(**model_kwargs)
```

它做的事很明确：

```text
从项目 Settings 里拿模型名、API key、base_url、timeout、retry
把这些配置交给 LangChain 的 ChatOpenAI
```

这说明：

```text
LangChain 不是绕过项目配置
而是复用项目配置
```

这点很重要。否则你会出现两套模型配置：

```text
/chat 用一套 key 和 base_url
/langchain-chat 用另一套 key 和 base_url
```

那会非常难排查。

### 2. 转换消息对象

核心函数：

```python
def convert_to_langchain_message(message: ChatMessage) -> BaseMessage:
    if message.role == ChatMessageRole.SYSTEM:
        return SystemMessage(content=message.content)
    if message.role == ChatMessageRole.USER:
        return HumanMessage(content=message.content)
    if message.role == ChatMessageRole.ASSISTANT:
        return AIMessage(content=message.content)
```

它解决的是：

```text
项目自己的 ChatMessage
如何变成 LangChain 能理解的 message object
```

对应关系是：

| 项目角色 | LangChain 类型 | 含义 |
| --- | --- | --- |
| `system` | `SystemMessage` | 系统指令 |
| `user` | `HumanMessage` | 用户输入 |
| `assistant` | `AIMessage` | 历史里的模型回复 |

注意：

```text
这不是为了“多写一层”
而是为了隔离 API schema 和框架内部对象
```

### 3. 构造 LangChain messages

核心函数：

```python
def build_langchain_chat_messages(user_message, *, history=None):
    return [
        convert_to_langchain_message(message)
        for message in build_chat_messages(user_message, history=history)
    ]
```

这里复用了旧的 `build_chat_messages()`。

好处是：

```text
旧 /chat 和新 /langchain-chat 使用同一套 prompt 构建逻辑
两条路径的差异只在“调用模型的方式”
不会因为 prompt 不同导致对比失真
```

### 4. 提取 AIMessage 文本

核心函数：

```python
def extract_langchain_reply(ai_message: Any) -> str:
    text = getattr(ai_message, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()

    content = getattr(ai_message, "content", None)
    if isinstance(content, str) and content.strip():
        return content.strip()

    raise AppException(...)
```

为什么不直接写：

```python
return ai_message.content
```

因为 LangChain 的 `AIMessage` 可能携带更复杂的内容结构。当前我们只支持普通文本回答，所以：

```text
优先读取 text
再兼容 content 字符串
空内容返回 LLM_EMPTY_RESPONSE
```

这是一种保守处理。

### 5. 调用 invoke()

核心逻辑：

```python
response = self._get_model().invoke(messages)
reply = extract_langchain_reply(response)
```

这里的 `invoke()` 就是本节最核心的 API。

它表示：

```text
把消息列表发给 ChatModel
等待模型完整返回
拿到 AIMessage
```

不要把它理解成 Agent，也不要理解成工具调用。它只是一次模型调用。

### 6. 新增 /langchain-chat

文件：

```text
projects/ai-service/app/routers/chat.py
```

新增接口：

```python
@router.post("/langchain-chat", response_model=ChatResponse)
def langchain_chat(...):
    reply = langchain_chat_model_service.generate_reply(
        request.message,
        history=request.history,
    )
    return ChatResponse(reply=reply)
```

这个接口复用了：

```text
ChatRequest
ChatResponse
history 校验
统一异常处理
trace_id 中间件
```

所以它不是另起炉灶，而是在现有 FastAPI 项目里加一条 LangChain 学习路径。

## 重要测试说明

本节新增的关键测试有三类。

第一类：消息转换测试。

它验证：

```text
ChatMessageRole.USER -> HumanMessage
ChatMessageRole.ASSISTANT -> AIMessage
当前用户问题也会变成 HumanMessage
```

这能防止 LangChain 调用时角色错乱。

第二类：service 测试。

它验证：

```text
LangChainChatModelService 会调用 model.invoke()
会把 history 传进去
会从 AIMessage 里提取文本
没有 API key 时返回 LLM_API_KEY_MISSING
模型异常会映射成统一 AppException
```

第三类：router 测试。

它验证：

```text
/langchain-chat 能返回 ChatResponse
能传递 history
缺少 message 时返回 VALIDATION_ERROR
GET 请求返回 METHOD_NOT_ALLOWED
```

测试不会真实调用模型。

## 常见误区

### 误区 1：ChatModel 等于 LangChain Agent

不对。

ChatModel 只是模型调用封装。

Agent 是模型、工具、状态和执行循环的组合。

### 误区 2：ChatOpenAI 只能调用 OpenAI 官方模型

不完全对。

如果第三方服务兼容 OpenAI Chat Completions API，`ChatOpenAI` 可以通过 `base_url` 做基础聊天调用。

但第三方非标准字段不一定被保留，所以不能把兼容性理解成“所有能力完全一样”。

### 误区 3：用了 ChatModel 就不需要项目自己的 schema

不对。

HTTP API 仍然应该使用项目自己的 Pydantic schema。LangChain message 是内部调用对象，不应该直接暴露成接口契约。

### 误区 4：AIMessage 就是字符串

不对。

`AIMessage` 可以包含文本、工具调用、metadata、token usage 等信息。

当前我们只取文本，是因为本节只学普通聊天。

### 误区 5：invoke() 会自动处理工具调用

不对。

普通 `invoke()` 只是调用模型。如果你想让模型可调用工具，需要后续学习 `bind_tools()` 或 Agent。

本节没有学这个。

### 误区 6：引入 LangChain 后就应该删掉旧 LLMChatService

不对。

现在保留两条路径是为了对比学习和降低风险。真实迁移要先验证行为、错误、日志和测试，再决定是否替换。

## 手动验证方式

如果你本机 `.env` 已经配置了：

```text
LLM_API_KEY
LLM_MODEL
LLM_BASE_URL
```

可以启动服务：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run uvicorn app.main:app --reload
```

然后请求：

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/langchain-chat" `
  -ContentType "application/json" `
  -Body '{"message":"用一句话解释 LangChain ChatModel 是什么"}'
```

注意：

```text
这个手动请求会真实调用模型，可能产生费用。
自动化测试不会真实调用模型。
```

## 练习与参考答案

### 练习 1：解释 ChatModel

题目：

用 3 句话解释 ChatModel 是什么。

参考答案：

```text
ChatModel 是聊天模型调用的抽象。它接收字符串或带角色的消息列表，返回一条 AIMessage。它只负责一次模型调用，不等于 Agent，也不会自动执行工具。
```

### 练习 2：区分三种 message

题目：

说明 `SystemMessage`、`HumanMessage`、`AIMessage` 分别对应什么。

参考答案：

```text
SystemMessage 对应系统指令，告诉模型行为规则。
HumanMessage 对应用户输入。
AIMessage 对应模型回复，也可能携带工具调用和 metadata。
```

### 练习 3：解释为什么要转换消息对象

题目：

为什么项目里的 `ChatMessage` 不能直接等同于 LangChain 的 `HumanMessage` / `AIMessage`？

参考答案：

```text
ChatMessage 是项目 API 边界的 Pydantic schema，用于请求校验和接口文档。LangChain message 是框架内部调用模型的对象。二者职责不同，所以需要转换函数把外部请求模型转换成内部框架对象。
```

### 练习 4：比较 /chat 和 /langchain-chat

题目：

说出 `/chat` 和 `/langchain-chat` 的核心区别。

参考答案：

```text
/chat 直接使用 OpenAI-compatible SDK，调用 client.chat.completions.create()。
/langchain-chat 使用 LangChain ChatModel，调用 model.invoke()。
两者复用相同的 ChatRequest、ChatResponse 和 prompt 构建逻辑，但模型调用层不同。
```

### 练习 5：判断说法对错

题目：

判断下面说法是否正确：

```text
1. ChatModel 是 Agent。
2. AIMessage 一定只是字符串。
3. invoke() 是一次完整的非流式模型调用。
4. ChatOpenAI 可以配置 base_url 调用兼容 OpenAI Chat Completions 的服务。
5. 用了 LangChain 后就不需要错误映射了。
```

参考答案：

```text
1. 错。ChatModel 是模型调用抽象，不是 Agent。
2. 错。AIMessage 还可能包含 tool_calls、metadata 等。
3. 对。
4. 对，但非标准字段不一定完整保留。
5. 错。项目仍然需要统一错误码和错误响应格式。
```

## 自测题与参考答案

### 自测 1

问题：ChatModel 的输入和输出分别是什么？

答案：

```text
输入通常是字符串或消息列表，输出是 AIMessage。
```

### 自测 2

问题：`HumanMessage("解释 FastAPI")` 对应 OpenAI-compatible messages 里的什么？

答案：

```text
对应 {"role": "user", "content": "解释 FastAPI"}。
```

### 自测 3

问题：为什么当前项目没有直接把 `/chat` 替换成 LangChain？

答案：

```text
为了对比学习、降低风险，并保留已有稳定接口。新增 /langchain-chat 可以让两种模型调用方式并行存在。
```

### 自测 4

问题：`invoke()` 和 streaming 有什么区别？

答案：

```text
invoke() 等模型生成完整结果后一次性返回 AIMessage；streaming 是边生成边返回多个 chunk。本节只学习 invoke()。
```

### 自测 5

问题：ChatOpenAI 使用 OpenAI-compatible base_url 时，需要注意什么？

答案：

```text
基础聊天调用通常可用，但第三方服务商的非标准响应字段不一定会被 LangChain 提取或保留，需要手动验证。
```

### 自测 6

问题：本节新增的 `/langchain-chat` 会自动调用工具吗？

答案：

```text
不会。它只做普通 ChatModel 调用。工具调用要等后续学习 LangChain Tool 或 Agent。
```

### 自测 7

问题：为什么测试里使用 fake model？

答案：

```text
为了避免自动化测试真实调用模型，保证测试稳定、快速、免费，并且能精确验证传入的 messages。
```

### 自测 8

问题：本节的核心新增 service 是什么？

答案：

```text
LangChainChatModelService。它负责构造 LangChain messages、调用 model.invoke()、提取 AIMessage 文本，并把异常映射成项目统一错误。
```

### 自测 9

问题：LangChain message 能不能直接作为 HTTP API 请求模型？

答案：

```text
不建议。HTTP API 边界应该使用项目自己的 Pydantic schema，LangChain message 应该作为内部调用对象。
```

### 自测 10

问题：学完本节后，下一步为什么适合学 LangChain Tool？

答案：

```text
因为我们已经知道了 ChatModel 如何调用模型。工具调用是在模型调用基础上，把工具 schema 绑定给模型，让模型能返回工具调用请求。
```

## 本节真正学会了什么

本节真正要学会的是：

```text
ChatModel 是 LangChain 对聊天模型调用的封装。
它输入 message，输出 AIMessage。
ChatOpenAI 可以复用项目里的 OpenAI-compatible 配置。
项目自己的 ChatMessage 和 LangChain message 职责不同，需要转换。
/langchain-chat 是学习和对比接口，不替换原有 /chat。
ChatModel 不等于 Agent，不会自动调用工具。
框架可以封装模型调用，但错误处理、日志、API 边界和测试隔离仍然要由项目自己负责。
```

如果你能向别人讲清下面这句话，就说明本节达标：

```text
以前我们直接用 SDK 调 client.chat.completions.create()，现在用 LangChain ChatModel 调 model.invoke()；前者更透明，后者更方便接入 LangChain 后续的 Tool、Agent 和 Runnable 生态，但业务边界仍然要自己管。
```

## 本节参考资料

- [LangChain ChatOpenAI integration](https://docs.langchain.com/oss/python/integrations/chat/openai)
- [LangChain chat model integrations](https://docs.langchain.com/oss/python/integrations/chat)
- [LangChain models](https://docs.langchain.com/oss/python/langchain/models)
- [LangChain messages](https://docs.langchain.com/oss/python/langchain/messages)

## 下一节学什么

下一节进入阶段 3 第 20 节：

```text
LangChain Tool 基础
```

下一节会把我们已经理解的 `query_order` 工具和 LangChain 的 Tool 抽象做对照：

```text
普通 Python 函数
-> LangChain Tool
-> 参数 schema
-> bind_tools()
-> 模型返回 tool_calls
```

但仍然会保持边界：

```text
不让模型直接绕过后端权限
不做多工具复杂 Agent
不跳过 Pydantic 校验
不取消我们已有的工具注册表和安全边界
```

