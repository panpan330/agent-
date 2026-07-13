# 阶段 3 第 18 节：LangChain 是什么，为什么现在才引入

> 本节结论：LangChain 不是大模型，也不是业务系统，更不是一个能自动替你保证安全的万能 Agent。它是一套把模型、消息、Prompt、工具、结构化输出、Agent 循环等常见 AI 应用组件组织起来的开发框架。我们现在才引入它，是因为你已经手写过底层工具调用链路，能看懂它封装了什么，也能判断哪些业务边界不能交给框架。

## 生成笔记前的教学复核

本节必须满足这些教学要求：

```text
1. 先讲清楚什么是框架、抽象、编排，再讲 LangChain。
2. 讲清 LangChain 不是模型本身，也不是 Java/Python 后端的替代品。
3. 讲清 LangChain 到底帮我们封装了哪些重复工作。
4. 讲清 LangChain 不负责哪些关键事情，尤其是权限、安全、幂等和业务校验。
5. 把当前项目里已经手写的模块和 LangChain 概念一一对应。
6. 解释为什么我们前 17 节没有一开始就使用 LangChain。
7. 不在本节引入复杂 Agent、LangGraph、RAG、多工具循环或生产级部署。
8. 本节以理解为主，不强行写代码；代码示例只用于解释概念。
```

## 本节一句话定位

第 18 节是在你已经理解 Tool Calling 底层流程之后，开始认识 LangChain 这个框架：它能把我们前面手写的一部分模型调用、工具定义和调用编排封装起来，但不能替代后端自己的业务安全边界。

## 本节解决的真实问题

前面我们已经一步步手写过这些能力：

```text
OpenAI-compatible SDK 调用
messages 构建
prompt 构建
结构化输出
Pydantic 校验
tools 参数声明
tool_choice="auto"
模型返回 tool_calls
后端校验工具名和参数
后端执行 query_order
Python 调用 Java mock API
tool message 回传模型
第二轮模型总结
敏感操作用户确认
创建工单写操作
幂等性
trace_id 和日志
fake/mock 测试
```

这时你自然会问：

```text
既然 LangChain 很出名，为什么我们不一开始就用？
它是不是可以替我们把这些都做好？
用了 LangChain 以后，是不是以前写的代码都没用了？
以后真实项目里到底该用 SDK，还是用 LangChain？
LangChain 和 LangGraph 又是什么关系？
```

本节就是为了回答这些问题。

## 本节新增能力

学完后你应该能做到：

- 能用自己的话解释 LangChain 是什么；
- 能分清 LangChain、LangGraph、LangSmith 的基本定位；
- 能解释为什么我们现在才引入 LangChain；
- 能说清 LangChain 封装了哪些东西；
- 能说清 LangChain 不负责哪些业务边界；
- 能把当前项目里的手写代码对应到 LangChain 概念；
- 能判断一个场景适合直接用 SDK，还是适合引入 LangChain；
- 能避免“会调包但不知道底层发生什么”的学习误区。

## 和上一节的区别

第 17 节学的是：

```text
工具调用链路怎么用 fake/mock 分层测试。
```

第 18 节学的是：

```text
当你已经理解底层链路后，怎么认识 LangChain 这个更高层框架。
```

简单说：

```text
第 17 节：怎么验证我们手写的工具调用链路
第 18 节：怎么理解一个框架对这条链路做了哪些封装
```

## 基础知识铺垫

### 1. 什么是“库”

库，英文叫 library。

人话解释：库就是别人写好的一些函数、类或工具，你需要什么就调用什么。

例如：

```python
import httpx

response = httpx.get("http://127.0.0.1:8001/orders/A1001")
```

这里 `httpx` 就是一个库。你主动调用它，它帮你发送 HTTP 请求。

库的特点是：

```text
你控制主流程
你决定什么时候调用它
它解决一个相对明确的问题
```

当前项目里已经用过的库包括：

```text
fastapi
pydantic
httpx
openai
pytest
python-dotenv
```

### 2. 什么是“框架”

框架，英文叫 framework。

人话解释：框架不只是给你几个函数，而是给你一套组织程序的方式。你把自己的代码放到它规定的位置里，它按自己的流程帮你跑起来。

例如 FastAPI 就是框架：

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}
```

你没有自己写 HTTP 协议解析、路由匹配、请求体读取、响应序列化。你只是按 FastAPI 的方式定义接口，FastAPI 负责把请求分发到你的函数。

框架的特点是：

```text
它控制一部分主流程
它规定你怎么组织代码
它帮你处理大量通用流程
它会带来学习成本和约束
```

LangChain 也是框架。它不是只提供一个函数，而是提供一套组织 LLM 应用的方式。

### 3. 什么是“抽象”

抽象，英文叫 abstraction。

人话解释：抽象就是把很多不同东西背后的共同点提取出来，给它们一个统一的用法。

例如不同模型服务商的 SDK 可能长这样：

```text
OpenAI SDK 一种写法
Anthropic SDK 一种写法
Google Gemini SDK 一种写法
阿里云百炼兼容 OpenAI 又是一种配置方式
```

但它们背后都有共同点：

```text
输入 messages
选择 model
配置 temperature
可能支持 streaming
可能支持 tool calling
可能支持 structured output
返回模型消息
```

LangChain 会把这些共同点抽出来，形成更统一的模型接口，例如 ChatModel。

抽象的好处：

```text
减少重复代码
减少不同服务商之间的接入差异
让常见流程更容易组合
```

抽象的代价：

```text
你看到的不是底层完整细节
出问题时需要理解框架内部做了什么
某些服务商的特殊能力可能不容易完全表达
版本变化时需要跟着框架调整
```

所以抽象不是越多越好。合适的抽象能提高效率，过早的抽象会遮住底层原理。

### 4. 什么是“编排”

编排，英文常叫 orchestration。

人话解释：编排就是安排多个步骤按什么顺序执行、每一步的输入输出怎么传递、失败时怎么处理。

比如我们现在的 `/tool-chat` 其实就是一条编排链路：

```text
用户问题
-> 构造 messages
-> 模型决定是否调用工具
-> 校验工具名
-> 校验工具参数
-> 执行 query_order
-> 调用 Java mock API
-> 校验工具返回值
-> 构造 tool message
-> 第二次调用模型
-> 返回最终回答
```

这个流程不是单个函数能完整表达的，它是一串步骤。谁先谁后、谁能失败、失败怎么返回，这些都属于编排问题。

LangChain 很大一部分价值就是帮助你编排 LLM 应用里的常见步骤。

### 5. 什么是 AI 应用框架

普通后端框架主要处理：

```text
HTTP 请求
路由
请求体验证
响应返回
中间件
异常处理
```

AI 应用框架主要处理：

```text
模型调用
Prompt 组织
消息格式
工具定义
工具调用
结构化输出
上下文管理
多步骤链路
Agent 循环
观测和调试
```

FastAPI 和 LangChain 不是同一层东西。

在我们的项目里：

```text
FastAPI 负责 API 服务层
LangChain 后续会负责一部分 LLM 应用编排层
Java mock service 模拟真实业务系统
Pydantic 负责数据结构和校验
后端业务代码负责权限、安全、幂等和错误边界
```

### 6. 什么是 Agent

Agent 这个词很容易被讲玄。

先用最朴素的话解释：

```text
Agent 就是一个由模型参与决策的执行循环。
```

普通固定流程可能是：

```text
先查订单
再总结
最后返回
```

Agent 流程可能是：

```text
模型看用户问题
模型决定是否查订单
查完后模型再判断是否还需要别的工具
直到模型认为可以回答
```

也就是说，Agent 和普通工作流的区别在于：

```text
普通工作流：路径主要由程序员提前写死
Agent：某些步骤由模型根据上下文动态决定
```

官方文档里也把 agent 理解成“模型调用工具直到任务完成”的循环。我们不需要背这句话，但要理解它的意思：

```text
模型不是只生成文本
模型还能在循环中提出工具调用请求
后端或框架执行工具
工具结果再回到模型
模型决定继续调用还是最终回答
```

这和我们第 13 节手写的流程非常接近，只是我们当前项目为了安全和学习边界，只允许一轮、一个只读工具。

### 7. 什么是 workflow

workflow 是工作流。

人话解释：工作流就是比较确定的步骤安排。

例如：

```text
接收用户问题
-> 提取工单字段
-> 创建确认计划
-> 用户确认
-> 调用 Java 创建工单
-> 返回结果
```

这更像 workflow，因为关键步骤是我们后端决定的，不是模型想怎么走就怎么走。

这点很重要：

```text
不是所有 AI 应用都应该做成 Agent。
```

如果业务流程必须严格、安全、可审计，通常应该优先用 workflow。模型可以参与“理解自然语言”“提取字段”“生成总结”，但不应该完全接管业务流程。

### 8. LangChain、LangGraph、LangSmith 的关系

先不要被名字吓到，把它们当成同一生态里的三个角色。

```text
LangChain：更偏应用开发框架，提供模型、工具、结构化输出、Agent 等抽象。
LangGraph：更偏底层编排框架，适合复杂、长时间运行、有状态、需要恢复和人工介入的 Agent/工作流。
LangSmith：更偏观测、调试、评测平台，帮助你看清每一步模型调用和工具调用。
```

放到我们的学习路线里：

```text
现在：先学 LangChain，因为它离模型调用和工具调用最近。
后面：再学 LangGraph，因为复杂智能工单 Agent 需要更明确的状态和流程控制。
再后面：理解 LangSmith 或类似观测方案，因为生产项目需要 trace、debug 和 eval。
```

## 本节主题系统讲解

### 1. LangChain 到底是什么

LangChain 是一个面向 LLM 应用开发的框架。它提供了很多统一抽象和组件，帮助开发者把模型、Prompt、工具、结构化输出、Agent 循环等组合成应用。

更具体地说，它主要做这些事：

```text
统一不同模型的调用方式
统一消息和 Prompt 的组织方式
统一工具的定义方式
统一结构化输出的使用方式
提供链式组合能力
提供 Agent 循环能力
和 LangSmith/LangGraph 等生态工具衔接
```

但是 LangChain 不是：

```text
不是模型服务商
不是大模型本身
不是数据库
不是 Java 后端
不是权限系统
不是支付系统
不是工单系统
不是安全审计系统
不是自动保证正确的魔法
```

你可以把它理解成：

```text
LangChain 是 AI 应用层的“组织工具箱”。
```

它能帮你组织 AI 流程，但它不替你决定业务规则。

### 2. 为什么 LangChain 很容易被误解

因为很多教程会直接从类似这样的代码开始：

```python
from langchain.agents import create_agent

agent = create_agent(
    model="provider:model-name",
    tools=[some_tool],
    system_prompt="You are a helpful assistant.",
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "帮我查一下订单"}]
})
```

初学者看到后可能会以为：

```text
原来 Agent 就这么简单
只要 create_agent 就能做 AI 应用
工具传进去就行
业务安全框架会帮我处理
```

这就是危险的地方。

这段代码确实可以让你快速跑起来，但它没有自动替你回答这些问题：

```text
模型能看到哪些工具？
工具参数是否可信？
工具有没有权限等级？
写操作是否需要用户确认？
重复执行会不会产生重复工单？
工具失败时对用户返回什么？
Java 服务返回的字段是否可信？
日志里会不会泄露用户隐私或 API key？
测试是否会真实调用模型？
```

这些问题正是我们前 17 节学过的东西。

所以 LangChain 不是不能用，而是不能在没理解底层边界时盲目用。

### 3. 为什么我们现在才引入 LangChain

原因一：先理解模型调用本质。

如果一开始就用 LangChain，你可能只知道：

```text
agent.invoke(...)
```

但不知道底层其实发生了：

```text
构造 messages
选择 model
发送 HTTP 请求
解析模型响应
处理 timeout/rate limit
提取 token usage
记录 trace_id
```

我们在阶段 2 已经把这些基础补上了。

原因二：先理解 Tool Calling 本质。

如果一开始就用 LangChain 的 tool，你可能只知道：

```text
@tool
def query_order(...):
    ...
```

但不知道底层其实涉及：

```text
工具名
工具描述
参数 schema
模型返回 arguments
后端校验 arguments
后端执行函数
工具结果回传模型
模型再生成最终回答
```

我们在阶段 3 第 1-13 节已经手写过这条链路。

原因三：先理解安全边界。

LangChain 可以帮你组织工具，但它不会自动知道你的业务里：

```text
查订单是只读操作
创建工单是写操作
退款是高风险操作
修改地址需要确认
重复提交需要幂等
某些用户不能看某些订单
```

这些必须由你的后端业务规则来定义。

原因四：先理解可测试性。

如果直接引入框架后只做端到端测试，你很容易又回到：

```text
真实模型
真实网络
真实外部服务
测试慢且不稳定
```

第 17 节已经讲过，AI 工具调用链路也要分层测试。

原因五：先建立判断力。

框架最怕两种用法：

```text
完全不用，所有东西都重复手写
过度依赖，什么都交给框架
```

我们现在学 LangChain，是为了做到第三种：

```text
知道它适合封装哪一层，也知道哪些边界必须自己保留。
```

### 4. LangChain 和当前项目的对应关系

下面这张表非常重要。它能帮你把“我们已经写过的东西”和“LangChain 的概念”对应起来。

| 当前项目里手写过的东西 | LangChain 里的相近概念 | 说明 |
| --- | --- | --- |
| `LLMClientFactory` / OpenAI-compatible client | ChatModel / model integration | 统一模型调用入口 |
| `message_builder.py` | Messages / PromptTemplate / ChatPromptTemplate | 组织 system/user/assistant 消息 |
| `prompt_builder.py` | PromptTemplate | 组织可复用 prompt |
| `ToolDefinition` | Tool metadata | 描述工具名、描述、参数、风险等级 |
| `QueryOrderArgs` | tool args schema | 工具参数结构 |
| `QueryOrderResult` | tool result schema | 工具返回结构 |
| `query_order()` | Tool function | 真正被执行的工具函数 |
| `TOOL_REGISTRY` | tools list / tool registry | 模型可见工具和后端可执行工具的集合 |
| `authorize_tool_call()` | guardrails / middleware 的一部分 | 权限边界，但不能完全交给模型 |
| `ToolCallingChatService` | agent loop / runnable chain | 模型、工具、tool message 的编排 |
| `ToolConfirmationService` | human-in-the-loop 业务实现 | 写操作确认，不应简单交给模型 |
| `run_idempotent_tool()` | 自定义业务幂等层 | LangChain 不知道你的幂等规则 |
| `build_trace_headers()` | tracing context | 项目内部 trace，LangSmith 是另一类观测工具 |
| `tests/fakes.py` | fake model | 测试时替代真实模型 |
| `tests/tool_fakes.py` | fake tools / fake clients | 测试时替代真实工具依赖 |

你会发现一件事：

```text
LangChain 能覆盖一部分“模型和工具编排”的通用层，
但我们项目里的安全、权限、幂等、Java 业务接口、错误码、trace_id 仍然要自己设计。
```

这就是本节最关键的判断。

### 5. LangChain 帮我们封装什么

#### 5.1 模型调用封装

不用框架时，你可能要直接处理：

```text
不同 SDK 的初始化方式
不同服务商的参数名称
不同响应对象结构
普通响应和流式响应差异
tool_calls 的解析方式
结构化输出的调用方式
```

LangChain 会提供更统一的模型接口。

这不表示底层差异消失了，只表示你可以用更统一的方式组织常见调用。

#### 5.2 Prompt 和 messages 封装

我们当前自己写了 `message_builder.py` 和 `prompt_builder.py`，目的是把 prompt 和 messages 组织清楚。

LangChain 也提供类似能力：

```text
PromptTemplate
ChatPromptTemplate
MessagesPlaceholder
```

这些东西的核心价值不是“少写几行字符串”，而是让 prompt 变成可复用、可组合、可测试的对象。

#### 5.3 Tool 封装

我们现在定义一个工具，需要考虑：

```text
工具名
工具描述
参数类型
参数校验
工具函数
工具返回
模型可见描述
后端可执行白名单
```

LangChain 的 tool 抽象可以帮你把 Python 函数包装成模型可见的工具。

例如概念上可以理解成：

```python
from langchain.tools import tool

@tool
def query_order(order_id: str) -> str:
    """查询订单状态。"""
    return "订单已付款，等待发货。"
```

这里的关键不是装饰器本身，而是：

```text
函数名、类型提示、文档字符串会参与工具描述
模型根据工具描述判断是否调用
框架把函数包装成模型可理解的工具形式
```

但注意：

```text
工具能不能执行
谁能执行
是否需要确认
是否幂等
是否记录审计日志
```

这些仍然是业务系统要管的事。

#### 5.4 结构化输出封装

我们前面学过：

```text
JSON Mode
Structured Outputs
Pydantic 校验
```

LangChain 也提供结构化输出相关能力，可以让模型最终输出符合某个 schema。

但你必须记住：

```text
结构化输出不是业务正确性保证。
```

它只能帮助你拿到格式更稳定的数据，比如：

```text
summary 是字符串
priority 是枚举
order_id 可以为空
```

但它不能保证：

```text
这个 order_id 真的属于当前用户
这个 priority 业务上一定合理
这个工单应该被创建
这个字段没有被用户恶意诱导
```

### 6. LangChain 不帮我们解决什么

这一节必须讲清楚，因为这是从“会用”走向“真正懂”的关键。

#### 6.1 不替你做业务权限

LangChain 不知道你的公司规则：

```text
客服 A 能看哪些订单
用户 B 能不能查订单 C
创建工单是否需要登录
退款是否需要主管审批
```

权限必须由后端业务系统控制。

#### 6.2 不替你判断模型输出可信

模型返回的工具参数仍然是不可信输入。

即使用了 LangChain，后端仍然要做：

```text
工具名白名单
参数 Pydantic 校验
字段长度限制
枚举限制
业务权限校验
危险操作确认
```

#### 6.3 不替你保证幂等

LangChain 不知道：

```text
重复创建工单算不算错误
重复退款会不会造成事故
重复发送短信是否收费
```

幂等规则必须由业务层定义。

#### 6.4 不替你设计错误码

我们的项目里有：

```text
TOOL_TIMEOUT
TOOL_UPSTREAM_ERROR
TOOL_CALL_FAILED
TOOL_CONFIRMATION_REQUIRED
TICKET_UPSTREAM_REJECTED
```

这些错误码是为了让前端、日志、测试和业务排查都能看懂。

LangChain 可能会抛出框架异常或模型异常，但你仍然要把它们映射成项目自己的错误响应。

#### 6.5 不替你保证测试稳定

用了 LangChain 后，测试仍然要避免真实调用模型。

你仍然需要：

```text
fake model
fake tool
fake Java client
dependency override
MockTransport
```

框架不会自动让测试变稳定。测试稳定来自清楚的边界设计。

### 7. 直接用 SDK、使用 LangChain、使用 LangGraph 怎么选

#### 7.1 什么时候直接用 SDK 更合适

适合场景：

```text
功能很简单
只调用一个模型
没有复杂工具调用
只需要可控、透明的调用链路
团队刚开始学习底层原理
```

例如阶段 2 的 `/chat` 和 `/stream-chat`，直接用 OpenAI-compatible SDK 很合适。

原因：

```text
代码透明
依赖少
容易调试
容易理解 HTTP/API 本质
```

#### 7.2 什么时候 LangChain 更合适

适合场景：

```text
有多个模型提供商
有多个工具
需要把 prompt、model、tool、output parser 组合起来
想复用社区集成
希望更方便地构建 agent loop
希望后续接入 LangSmith / LangGraph 生态
```

例如我们后面要学习：

```text
LangChain ChatModel 基础
LangChain Tool 基础
LangChain 结构化输出
```

这时 LangChain 就适合逐步引入。

#### 7.3 什么时候 LangGraph 更合适

适合场景：

```text
流程很复杂
状态需要持久化
任务可能运行很久
中间需要人工介入
需要失败恢复
需要明确节点和边
需要把 Agent 行为控制得更细
```

例如后面真正做“智能工单 Agent”时，可能会有：

```text
接收用户问题
-> 判断意图
-> 查询订单
-> 判断是否需要创建工单
-> 如果是写操作，等待用户确认
-> 调用 Java 创建工单
-> 失败后进入人工处理
-> 记录状态
```

这种复杂流程更适合 LangGraph。

但现在还不是 LangGraph 的学习时机。我们先学 LangChain，是因为它离模型和工具调用基础更近。

### 8. LangChain 不是要替换掉所有手写代码

一个很常见的错误想法是：

```text
既然要学 LangChain，那是不是前面写的 ToolCallingChatService 都没用了？
```

不是。

前面写的代码至少有三个价值。

第一，它让你理解了底层流程。

以后看到 LangChain 的 agent 或 tool，你知道它内部大概在做什么。

第二，它沉淀了业务边界。

比如：

```text
工具注册表
权限等级
确认机制
幂等性
错误码
Java client
Pydantic schema
trace_id
测试 fake
```

这些东西就算用了 LangChain，也不应该随便丢掉。

第三，它可以作为迁移参照。

我们后续引入 LangChain 时，不会直接把项目推倒重来，而是逐步替换某些合适的层：

```text
先学习 ChatModel
再学习 Tool
再学习结构化输出
再判断哪些 service 编排可以用 LangChain 表达
最后再进入 LangGraph
```

这叫有边界地引入框架。

### 9. LangChain 里最值得先理解的几个核心词

#### 9.1 ChatModel

ChatModel 可以理解成聊天模型接口。

它对应我们已经学过的：

```text
model
messages
temperature
streaming
tool calling
structured output
```

我们下一节就会学习它。

#### 9.2 PromptTemplate / ChatPromptTemplate

PromptTemplate 是 prompt 模板。

它解决的问题是：

```text
不要到处拼接字符串
让 prompt 变量清楚
让 prompt 可以复用
```

#### 9.3 Tool

Tool 是模型可以请求调用的能力。

它通常包含：

```text
名称
描述
参数 schema
执行函数
返回值
```

这和我们前面手写的工具定义非常像。

#### 9.4 Runnable

Runnable 可以先粗略理解成：

```text
可以被 invoke 的组件。
```

一个模型可以是 runnable，一个 prompt 可以和模型组合成 runnable，一个链路也可以是 runnable。

现在不需要深入，只要先知道它是 LangChain 里用于组合流程的基础概念。

#### 9.5 Agent

Agent 是模型参与决策的循环。

它不是一个普通函数，而是一个“模型 + 工具 + 上下文 + 执行循环”的组合。

#### 9.6 Callback / tracing

AI 应用很难调试，因为中间有：

```text
prompt
模型输入
模型输出
工具参数
工具结果
第二轮模型输入
最终输出
```

tracing 的目标就是把这些中间过程记录下来，方便排查和评测。

我们项目现在自己做了日志和 `trace_id`。LangSmith 是 LangChain 生态里更完整的观测和评测平台。两者不是同一层，但目标相似：看清链路。

### 10. 一个手写流程和 LangChain 思路的对照

我们现在手写的 `/tool-chat` 思路大概是：

```text
1. 构造第一轮 messages
2. 把 tools 传给模型
3. 模型返回 tool_calls
4. 后端检查工具名和参数
5. 后端执行工具
6. 构造 tool message
7. 第二次调用模型
8. 返回最终回答
```

LangChain agent 的高层思路大概是：

```text
1. 你提供 model
2. 你提供 tools
3. 你提供 system prompt
4. 框架运行模型和工具调用循环
5. 返回最终结果和中间消息
```

它确实可以减少一部分编排代码。

但是我们仍然要在工具函数内部或工具外层保留：

```text
参数校验
权限判断
确认机制
幂等保护
Java API 调用错误映射
日志和 trace_id
测试 fake
```

这就是“框架封装通用流程，业务代码保留关键边界”。

## 最小心智模型

先把 LangChain 压缩成一张最小地图：

```text
模型能力
-> 用 ChatModel 表达

提示词和消息
-> 用 Prompt / Messages 表达

外部能力
-> 用 Tool 表达

多步骤调用
-> 用 Runnable / Chain / Agent loop 组织

复杂有状态流程
-> 后续用 LangGraph 更细地编排

调试、追踪、评测
-> 可接 LangSmith，也可以先保留项目自己的日志和 trace_id
```

再把它和我们的项目对应起来：

```text
LangChain 管通用 AI 编排
FastAPI 管 HTTP API
Pydantic 管数据结构校验
Java 服务管真实业务
Python 业务层管权限、确认、幂等、错误和日志
```

这一节最重要的心智模型是：

```text
LangChain 是封装层，不是业务边界。
```

## 不看代码复述版

如果不看任何代码，你应该能这样向别人解释本节：

```text
我们现在开始学 LangChain，是因为前面已经手写过模型调用和工具调用的底层链路。

LangChain 的价值是把 LLM 应用里的通用组件抽象出来，比如 ChatModel、Prompt、Tool、结构化输出和 Agent 循环。这样当项目里工具变多、模型调用链路变复杂时，可以少写一些重复编排代码。

但 LangChain 不是模型本身，也不是业务系统。它不会自动知道谁有权限查订单、哪些操作需要用户确认、重复创建工单是否危险、Java 服务报错应该映射成什么错误码。

所以我们的引入方式不是推翻以前代码，而是先理解它封装了什么，再逐步把合适的通用 AI 编排层交给 LangChain，同时保留后端自己的安全、权限、幂等、日志和测试边界。
```

## 学会的判断标准

学完本节后，如果你能做到下面几点，就说明第 18 节达标：

```text
1. 能说清 LangChain 是 LLM 应用开发框架，不是大模型。
2. 能说清 LangChain 主要封装模型、Prompt、Tool、结构化输出和 Agent loop。
3. 能说清权限、确认、幂等、业务校验和错误码不能交给 LangChain 自动保证。
4. 能把当前项目里的 ToolCallingChatService、ToolDefinition、QueryOrderArgs、query_order() 对应到 LangChain 概念。
5. 能判断简单模型调用适合 SDK，复杂工具组合适合 LangChain，复杂有状态流程后续适合 LangGraph。
6. 能解释为什么我们前 17 节先手写底层流程，而不是一开始就调 LangChain。
```

## 当前项目落地

本节不新增业务接口，也不引入 LangChain 依赖。

原因是：

```text
第 18 节目标是理解 LangChain 的位置，不是急着把项目改成 LangChain 写法。
```

本节产出是：

```text
新增一份 LangChain 概念笔记
更新学习进度
更新 README 和学习资源索引
```

下一节才开始真正进入：

```text
LangChain ChatModel 基础
```

也就是说，下一节我们才会考虑是否安装依赖、如何用 LangChain 表达一个最小模型调用。

## 本节代码讲解

本节没有新增生产代码。

这里特意不写生产代码，是为了避免你还没理解 LangChain 的定位，就先陷入 API 细节。

如果现在直接写代码，很容易变成：

```text
会复制 create_agent 示例
但不知道它封装了什么
也不知道哪些业务边界不能交给它
```

本节只保留一个概念示例：

```python
from langchain.agents import create_agent

agent = create_agent(
    model="provider:model-name",
    tools=[query_order],
    system_prompt="你是客服助手。",
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "帮我查订单 A1001"}]
})
```

这段代码想表达的是：

```text
model：模型能力
tools：模型可以请求的工具
system_prompt：行为边界提示
invoke：启动一次调用
```

但真实项目里还要补：

```text
工具权限
参数校验
错误映射
确认机制
幂等性
日志
测试
```

所以这段代码只能作为概念示例，不能直接当成我们的生产实现。

## 常见误区

### 误区 1：LangChain 等于 Agent

不对。

LangChain 包含 Agent 能力，但不只做 Agent。它还包含模型调用、Prompt、工具、结构化输出、组件组合等能力。

### 误区 2：用了 LangChain 就不用懂 OpenAI-compatible SDK

不对。

LangChain 底层仍然要调用模型服务。你越懂 SDK、messages、tool calling、streaming、错误处理，就越能调试 LangChain。

### 误区 3：LangChain 会自动保证工具安全

不对。

工具安全靠后端设计：

```text
白名单
权限
确认
幂等
审计
测试
```

Prompt 不能代替权限系统，框架也不能代替业务规则。

### 误区 4：所有 AI 应用都应该做成 Agent

不对。

很多场景更适合固定 workflow。

例如：

```text
提取字段 -> 用户确认 -> 创建工单
```

这类流程需要严格控制，不适合完全交给模型自由决定。

### 误区 5：框架越高级，代码越少，项目越好

不一定。

优秀项目追求的是：

```text
边界清楚
行为可控
错误可查
测试稳定
业务安全
后续可维护
```

如果一个框架让你看不懂链路、测不清边界、管不住权限，那就不是好的使用方式。

### 误区 6：用了 LangChain 以后以前的学习就过时了

不对。

前面学的内容是底层能力。LangChain 是在这些能力上做封装。你越懂底层，越能用好框架。

## 本节练习

### 练习 1：用自己的话解释 LangChain

题目：

不要使用“很强”“很方便”这类空话，用 3-5 句话解释 LangChain 是什么。

参考答案：

```text
LangChain 是一个用于开发 LLM 应用的框架。它把模型调用、Prompt、工具、结构化输出、Agent 循环等常见能力做成统一抽象，方便开发者组合复杂 AI 流程。它不是模型本身，也不是业务系统。它能减少通用编排代码，但不能替代权限、安全、幂等和业务校验。
```

### 练习 2：判断哪些事情 LangChain 不能替你做

题目：

下面哪些事情不能直接交给 LangChain 自动保证？

```text
A. 判断用户是否有权限查看订单
B. 把 Python 函数包装成模型可用工具
C. 防止重复创建工单
D. 把 prompt 和模型组合成调用链路
E. 判断退款操作是否需要主管审批
```

参考答案：

```text
A、C、E 不能直接交给 LangChain 自动保证。

B、D 是 LangChain 比较擅长辅助封装的事情。

权限、幂等、审批这类问题属于业务规则，必须由后端业务系统控制。
```

### 练习 3：把当前项目模块对应到 LangChain 概念

题目：

尝试把下面模块对应到 LangChain 概念：

```text
message_builder.py
ToolDefinition
query_order()
ToolCallingChatService
QueryOrderArgs
```

参考答案：

```text
message_builder.py -> Messages / ChatPromptTemplate
ToolDefinition -> Tool metadata
query_order() -> Tool function
ToolCallingChatService -> agent loop 或 runnable chain 的手写版本
QueryOrderArgs -> tool args schema
```

### 练习 4：为什么不一开始就用 LangChain

题目：

用 5 条理由解释为什么我们前面先手写底层流程，再引入 LangChain。

参考答案：

```text
1. 先理解模型调用的 messages、model、timeout、token、错误处理。
2. 先理解 Tool Calling 的工具名、参数 schema、tool_calls 和 tool message。
3. 先理解模型输出是不可信输入，必须后端校验。
4. 先设计权限、确认、幂等、日志和测试边界。
5. 有了底层理解后，才能判断 LangChain 封装了什么，以及哪些地方不能交给它。
```

### 练习 5：判断场景适合 SDK、LangChain 还是 LangGraph

题目：

给下面场景选择更合适的技术路线：

```text
1. 只做一个简单聊天接口。
2. 做一个有 5 个工具的客服助手，模型需要根据问题选择工具。
3. 做一个长时间运行的工单流程，中间可能需要人工确认、失败恢复和状态保存。
```

参考答案：

```text
1. 直接用 SDK 更合适，简单透明。
2. 可以考虑 LangChain，因为它能封装模型、工具和 agent loop。
3. 更适合 LangGraph，因为它更偏复杂、有状态、可恢复的流程编排。
```

## 自测问题

### 自测 1

问题：LangChain 是大模型吗？

答案：

```text
不是。LangChain 是 LLM 应用开发框架，它会调用模型，但它不是模型本身。
```

### 自测 2

问题：LangChain 和 FastAPI 是同一层框架吗？

答案：

```text
不是。FastAPI 主要负责 Web API 服务层，LangChain 主要负责 LLM 应用编排层。它们可以一起用。
```

### 自测 3

问题：为什么说模型返回的工具参数仍然不可信？

答案：

```text
因为参数是模型根据用户输入生成的，可能错误、缺字段、越权或被 prompt injection 影响。后端必须继续做 Pydantic 校验和业务权限校验。
```

### 自测 4

问题：LangChain 可以替代 Pydantic 吗？

答案：

```text
不能简单替代。LangChain 可以使用 schema 或 Pydantic 模型辅助结构化输出和工具参数定义，但项目边界上的数据校验仍然需要明确保留。
```

### 自测 5

问题：Agent 和 workflow 的核心区别是什么？

答案：

```text
workflow 的路径主要由程序员提前定义，Agent 的部分步骤由模型根据上下文动态决定，尤其是是否调用工具、调用哪个工具、是否继续循环。
```

### 自测 6

问题：为什么不是所有业务流程都适合 Agent？

答案：

```text
因为很多业务流程要求严格、安全、可审计。例如退款、创建工单、修改订单地址等操作不能完全交给模型自由决定，必须由后端控制流程和权限。
```

### 自测 7

问题：我们项目中的 `ToolCallingChatService` 和 LangChain agent loop 有什么关系？

答案：

```text
`ToolCallingChatService` 是我们手写的一轮工具调用编排：模型请求工具、后端执行工具、tool message 回传模型、模型总结。LangChain agent loop 可以封装类似流程，但我们仍然要保留业务安全边界。
```

### 自测 8

问题：LangGraph 和 LangChain 的基本区别是什么？

答案：

```text
LangChain 更偏模型、工具和 agent 应用框架；LangGraph 更偏复杂、有状态、可持久化、可恢复、可人工介入的底层编排框架。
```

### 自测 9

问题：使用 LangChain 后，测试还需要 fake/mock 吗？

答案：

```text
需要。自动化测试仍然应该避免真实调用模型和外部服务。可以继续使用 fake model、fake tool、MockTransport 和 dependency override。
```

### 自测 10

问题：本节为什么不直接安装 LangChain 写代码？

答案：

```text
因为本节目标是先理解 LangChain 的定位和边界。下一节学习 ChatModel 时再进入最小代码实践，这样不会在还没理解框架意义时陷入 API 细节。
```

## 本节真正学会了什么

学完本节，你真正要带走的不是某个 API，而是下面这套判断：

```text
LangChain 是 LLM 应用开发框架，不是模型本身。
LangChain 可以封装模型、Prompt、工具、结构化输出和 Agent 循环。
LangChain 不能替你保证权限、安全、幂等、业务校验和测试稳定。
我们前 17 节手写的内容不是浪费，而是理解框架的基础。
引入框架应该有边界，先替换通用编排层，不要丢掉业务安全层。
简单场景可以直接用 SDK，工具和组合复杂后可以考虑 LangChain，复杂有状态流程后续再看 LangGraph。
```

如果你能不看笔记讲清这几句话，就说明这一节真的学到了。

## 本节参考资料

- [LangChain overview](https://docs.langchain.com/oss/python/langchain/overview)
- [LangChain Agents](https://docs.langchain.com/oss/python/langchain/agents)
- [LangChain Tools](https://docs.langchain.com/oss/python/langchain/tools)
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)
- [LangGraph Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents)

## 下一节学什么

下一节进入阶段 3 第 19 节：

```text
LangChain ChatModel 基础
```

下一节会开始从概念进入代码，但仍然保持边界清楚：

```text
先用 LangChain 表达一次最小模型调用
对比它和我们手写 OpenAI-compatible SDK 调用的区别
不急着接 Agent
不急着接多工具
不推翻现有业务代码
```
