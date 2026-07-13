# 阶段 3 第 22 节：阶段 3 项目整理

> 本节结论：阶段 3 已经完成一条“可控的 AI 工具调用链路”。你现在不只是知道 Tool Calling 这个名词，而是已经用 FastAPI、Pydantic、OpenAI-compatible SDK、LangChain、httpx 和 Java mock 服务搭出了一条从自然语言到业务服务的工程化链路。下一阶段可以在这个基础上继续学习 RAG 和更复杂的 Agent/Workflow。

## 生成笔记前的教学复核

本节不是新增功能课，而是阶段收束课。

这一节必须讲清：

```text
1. 阶段 3 从第 1 节到第 21 节到底学了什么。
2. Tool Calling 的完整链路是什么。
3. Python AI 服务和 Java 业务服务分别负责什么。
4. 模型、工具、后端、Pydantic、权限、确认、日志之间是什么关系。
5. /tool-decision、/tool-chat、/tickets、/langchain-* 这些接口分别解决什么问题。
6. LangChain 在当前项目里是封装层，不是安全边界。
7. 当前项目已经具备哪些能力，还没有具备哪些能力。
8. 为什么下一阶段适合进入 RAG，而不是立刻做复杂 Agent。
```

本节尽量少讲重复代码。

重点放在：

```text
知识地图
系统架构
调用链路
工程边界
复盘能力
阶段验收
下一阶段衔接
```

## 本节一句话定位

第 22 节是阶段 3 的总复盘：把 Tool Calling、Java mock API、确认机制、LangChain 封装和测试策略整理成一个完整的 AI 应用工程知识体系。

## 阶段 3 的核心目标

阶段 3 的目标不是“学会调用一个函数”。

真正目标是：

```text
让 Python AI 服务具备可控、可测、可解释的工具调用能力，并能通过 HTTP 调用 Java 业务服务。
```

这里面有几个关键词。

### 1. 可控

可控的意思是：

```text
模型不能想调用什么就调用什么。
模型不能想传什么参数就信什么参数。
模型不能想执行写操作就直接执行。
模型不能绕过后端权限边界直接操作业务系统。
```

所以我们加入了：

```text
工具注册表
工具启用状态
工具风险等级
只读/写入/敏感操作区分
Pydantic 参数校验
用户确认计划
幂等键
统一错误处理
```

### 2. 可测

可测的意思是：

```text
不真实调用模型，也能测试业务逻辑。
不真实启动 Java 服务，也能测试 Python HTTP client。
不真实创建工单，也能测试确认计划和幂等逻辑。
```

所以我们使用了：

```text
fake OpenAI-compatible client
fake LangChain ChatModel
fake tool
fake Java API
httpx.MockTransport
FastAPI dependency_overrides
service/client/router 分层测试
```

### 3. 可解释

可解释的意思是：

```text
你能说清楚一次请求为什么调用工具。
你能说清楚工具参数从哪里来。
你能说清楚工具结果为什么可信。
你能说清楚写操作为什么不能直接执行。
你能根据 trace_id 找到模型调用、工具调用、Java API 调用日志。
```

这对以后做企业级 AI 应用很关键。

AI 应用不是只要“模型回答看起来对”。

后端工程里更重要的是：

```text
出了问题能定位
重复请求不乱写
权限边界清楚
错误能被前端和日志稳定识别
测试能覆盖关键风险
```

## 阶段 3 学习清单总览

阶段 3 一共 22 节。

可以分成 6 组。

| 分组 | 小节 | 主题 | 解决的问题 |
| --- | --- | --- | --- |
| 基础概念 | 1-4 | Tool Calling、业务边界、JSON Schema、结构化输出区别 | 先知道工具调用是什么，不把它和普通聊天、结构化输出混在一起 |
| 本地工具能力 | 5-9 | fake tool、结果校验、错误处理、权限、幂等 | 先在 Python 内部把工具调用的后端边界做扎实 |
| Java 业务接入 | 10-11 | Java mock 服务、Python 调 Java API | 让 AI 服务通过 HTTP 调用业务服务，而不是直接操作业务数据 |
| 模型工具决策 | 12-13 | 模型决定是否调用工具、工具结果回传模型总结 | 让模型参与“选择工具”和“解释结果”，但执行权仍在后端 |
| 写操作安全 | 14-17 | 用户确认、创建工单、trace_id、分层测试 | 处理写操作、确认、日志和测试这些真实工程问题 |
| LangChain 映射 | 18-21 | LangChain 定位、ChatModel、Tool、结构化输出 | 把前面手写过的底层流程映射到 LangChain 抽象 |
| 阶段收束 | 22 | 阶段 3 项目整理 | 把全部知识串成系统地图 |

你现在应该能看出阶段 3 的安排逻辑。

我们没有一上来就学 LangChain Agent。

原因是：

```text
如果先不理解底层工具调用链路，直接用 Agent，很容易只会调库，不知道安全边界在哪里。
```

所以阶段 3 的顺序是：

```text
先理解 Tool Calling 本质
再手写后端工具边界
再接入 Java mock 业务服务
再让模型参与工具选择
再补写操作确认、日志、测试
最后引入 LangChain 做抽象映射
```

这个顺序是为了让你真正知道：

```text
LangChain 封装了什么
后端必须自己负责什么
以后什么时候该用框架
什么时候不能把责任交给框架
```

## 阶段 3 的一张总图

当前系统可以这样理解：

```text
用户自然语言
  |
  v
FastAPI 入口层
  |
  v
Pydantic 请求校验
  |
  v
AI 服务层
  |
  +--> 普通模型调用 /chat
  |
  +--> 结构化输出 /extract-ticket、/langchain-extract-ticket
  |
  +--> 工具决策 /tool-decision
  |
  +--> 完整只读工具调用 /tool-chat
  |
  +--> 创建工单计划 /tickets/plans
          |
          v
      确认计划
          |
          v
      已确认后执行
          |
          v
Java mock 业务服务
  |
  v
Pydantic 返回值校验
  |
  v
统一响应 / 统一错误 / 日志 trace_id
```

这张图里有一个非常重要的思想：

```text
模型只提供建议、判断、抽取和表达。
真正的执行权在后端。
```

## 当前项目有哪些服务

当前仓库里不止一个项目。

阶段 3 主要涉及两个项目。

| 项目 | 路径 | 作用 |
| --- | --- | --- |
| Python AI 服务 | `projects/ai-service` | 接收用户请求，调用模型，编排工具，调用 Java mock API |
| Java mock 服务 | `projects/java-mock-service` | 模拟未来 Java/Spring Boot 业务服务，提供订单和工单相关接口 |

现在的 `java-mock-service` 还是 FastAPI 写的 mock。

这不是说我们以后不用 Java。

它只是为了让你先学会：

```text
Python AI 服务如何通过 HTTP 调业务服务
跨服务 timeout 怎么处理
上游 404/500 怎么映射
Java 返回字段怎么白名单映射给 AI
trace_id 如何跨服务传递
测试里如何模拟 Java API
```

以后换成真正 Spring Boot 服务时，核心思想不变。

变化的只是：

```text
Java mock service -> Spring Boot business-service
内存数据 -> 数据库
教学 actor_id -> 登录态/JWT/session
内存确认计划 -> 数据库/Redis
```

## 当前接口地图

### 1. 基础 AI 接口

| 接口 | 作用 | 重点 |
| --- | --- | --- |
| `GET /health` | 健康检查 | 服务是否活着 |
| `POST /chat` | 原生 SDK 普通聊天 | OpenAI-compatible SDK、messages、prompt、错误处理 |
| `POST /langchain-chat` | LangChain ChatModel 聊天 | `ChatOpenAI`、`SystemMessage`、`HumanMessage`、`model.invoke()` |
| `POST /stream-chat` | 流式聊天 | SSE、chunk、`StreamingResponse` |

这组接口证明：

```text
ai-service 已经具备基础模型调用能力。
```

### 2. 结构化输出接口

| 接口 | 作用 | 重点 |
| --- | --- | --- |
| `POST /extract-ticket` | 原生 SDK + JSON Mode 抽取工单字段 | 手动解析模型 JSON，再用 Pydantic 校验 |
| `POST /langchain-extract-ticket` | LangChain 结构化输出抽取工单字段 | `with_structured_output(TicketExtraction, method="json_mode")` |

这组接口证明：

```text
模型输出不一定只给用户看，也可以被后端变成结构化数据继续处理。
```

但你必须记住：

```text
结构化输出不是工具调用。
```

结构化输出解决的是：

```text
把自然语言变成固定格式数据。
```

Tool Calling 解决的是：

```text
模型提出要调用哪个外部能力，以及传什么参数。
```

### 3. 只读工具接口

| 接口 | 作用 | 重点 |
| --- | --- | --- |
| `POST /tools/query-order` | 手动查询订单工具 | 后端工具函数、参数校验、权限、幂等、Java API 调用 |
| `POST /tool-decision` | 让模型决定是否需要工具 | 模型只返回工具调用意图，不执行工具 |
| `POST /tool-chat` | 完整只读工具调用 | 模型请求工具 -> 后端执行 -> tool message 回传 -> 模型总结 |
| `GET /tools/langchain` | 查看 LangChain Tool 元数据 | `StructuredTool` 的名字、描述、参数 schema |
| `POST /tools/langchain/query-order` | 手动调用 LangChain 包装后的工具 | LangChain Tool 包装不替代项目权限和校验 |

这组接口证明：

```text
AI 服务已经能把用户问题和业务查询能力连接起来。
```

典型链路是：

```text
用户问：“订单 A1001 到哪了？”
-> 模型判断需要 query_order
-> 后端校验工具名和参数
-> 后端调用 Java mock API
-> 后端校验工具结果
-> 后端把 tool message 交回模型
-> 模型用中文总结给用户
```

### 4. 写操作确认接口

| 接口 | 作用 | 重点 |
| --- | --- | --- |
| `POST /tools/confirmations` | 创建待确认计划 | 绑定工具名、参数、操作者、过期时间、参数指纹 |
| `POST /tools/confirmations/{confirmation_id}/confirm` | 确认已有计划 | 确认不等于执行，防止参数被替换 |
| `POST /tickets/plans` | 从自然语言提取工单字段并创建工单确认计划 | 自然语言 -> 结构化字段 -> 后端命令 -> pending plan |
| `POST /tickets/confirmations/{confirmation_id}/execute` | 执行已确认工单计划 | 真正调用 Java mock 创建工单，使用幂等键 |

这组接口证明：

```text
项目已经开始具备安全处理写操作的能力。
```

这里的关键思想是：

```text
写操作必须拆成“计划”和“执行”。
```

不能让模型直接从：

```text
用户说要投诉
```

跳到：

```text
立即创建工单
```

正确流程应该是：

```text
模型抽取字段
-> 后端构造明确的业务命令
-> 后端保存待确认计划
-> 用户明确确认
-> 后端读取原计划执行
-> Java 业务服务创建工单
```

## 四条最重要的调用链路

### 链路 1：原生结构化输出

```text
POST /extract-ticket
-> StructuredOutputService.extract_ticket()
-> build_ticket_extraction_messages()
-> OpenAI-compatible SDK
-> response_format={"type":"json_object"}
-> TicketExtraction.model_validate_json()
-> StructuredOutputResponse
```

这条链路让你理解：

```text
模型可以按 JSON 输出，但后端仍要用 Pydantic 校验。
```

### 链路 2：只读工具完整调用

```text
POST /tool-chat
-> ToolCallingChatService.chat()
-> 第一轮模型调用，传 tools 和 tool_choice="auto"
-> 模型返回 tool_calls
-> 后端校验工具名和 arguments
-> authorize_tool_call()
-> query_order()
-> JavaOrderClient.get_order()
-> validate_query_order_result()
-> 构造 tool message
-> 第二轮模型调用
-> 返回用户可读中文回答
```

这条链路让你理解：

```text
模型决定“想调用什么”，后端决定“能不能调用、怎么调用、结果是否可信”。
```

### 链路 3：创建工单写操作

```text
POST /tickets/plans
-> TicketWorkflowService.create_ticket_plan()
-> 模型抽取 TicketExtraction
-> 转换成 CreateTicketArgs
-> ToolConfirmationService.create_plan()
-> 返回 pending confirmation

POST /tools/confirmations/{confirmation_id}/confirm
-> 同一操作者确认计划
-> 状态从 pending 变为 confirmed

POST /tickets/confirmations/{confirmation_id}/execute
-> 消费已确认计划
-> JavaTicketClient.create_ticket()
-> Java mock POST /tickets
-> CreatedTicket Pydantic 校验
-> 返回 TicketExecutionResponse
```

这条链路让你理解：

```text
写操作不是模型说了算，而是后端用确认计划控制风险。
```

### 链路 4：LangChain 结构化输出

```text
POST /langchain-extract-ticket
-> LangChainStructuredOutputService.extract_ticket()
-> build_langchain_ticket_extraction_messages()
-> create_langchain_chat_model()
-> model.with_structured_output(TicketExtraction, method="json_mode")
-> structured_model.invoke(messages)
-> validate_langchain_ticket_extraction()
-> StructuredOutputResponse
```

这条链路让你理解：

```text
LangChain 能封装模型调用和结构化输出，但项目自己的校验和错误处理仍然要保留。
```

## 阶段 3 最重要的基础知识

### 1. Tool Calling 的本质

Tool Calling 不是模型执行函数。

它的本质是：

```text
模型输出一个结构化请求：
我要调用哪个工具
参数是什么
```

真正执行工具的是：

```text
你的后端代码
```

所以 Tool Calling 的真实工程结构是：

```text
LLM
-> tool call proposal
-> backend validation
-> backend execution
-> backend result validation
-> LLM summary or backend response
```

### 2. 工具不是 prompt 里的魔法

工具必须有后端定义。

至少包括：

```text
工具名
工具描述
参数 schema
返回结果 schema
权限等级
是否启用
是否需要确认
执行函数
错误处理
日志
测试
```

如果只在 prompt 里写：

```text
你可以查询订单
```

那不是可靠的工具系统。

可靠的工具系统必须由后端掌控。

### 3. JSON Schema 解决“怎么描述参数”

模型不是人类，它需要知道工具参数格式。

例如：

```json
{
  "type": "object",
  "properties": {
    "order_id": {
      "type": "string",
      "description": "订单号"
    }
  },
  "required": ["order_id"]
}
```

这个 schema 告诉模型：

```text
query_order 需要一个 order_id。
```

但 schema 只是在模型侧提高输出稳定性。

后端仍要用 Pydantic 校验。

### 4. Pydantic 是后端信任边界

阶段 3 里，Pydantic 出现了很多次。

它不是装饰品。

它代表后端的信任边界。

比如：

```text
用户请求体 -> Pydantic 校验
模型 tool arguments -> Pydantic 校验
Java API 返回值 -> Pydantic 校验
模型结构化输出 -> Pydantic 校验
工单创建命令 -> Pydantic 校验
```

你可以把 Pydantic 理解成：

```text
凡是不完全可信的数据，进入业务逻辑前都要过一道门。
```

### 5. Java 业务服务仍然是业务真相

Python AI 服务不是业务数据库。

模型也不是业务数据库。

订单、退款、物流、工单、权限这些真实业务能力，最终应该属于 Java 后端。

当前阶段用 mock 服务，是为了提前练习跨服务调用方式。

正确分工是：

```text
Java：业务规则、数据库、权限、事务、稳定 API
Python：模型调用、AI 编排、RAG、工具调用、结果整理
LLM：理解自然语言、选择工具、生成解释、辅助字段抽取
```

### 6. 写操作必须有人类确认

查询订单通常是只读操作。

创建工单、退款、审批、改地址、取消订单，这些是写操作或敏感操作。

写操作需要额外保护：

```text
确认计划
操作者绑定
参数绑定
参数指纹
过期时间
确认幂等
执行幂等
审计日志
```

不能只靠 prompt 说：

```text
如果不确定就不要执行
```

因为 prompt 不是权限系统。

### 7. 幂等性是业务系统的安全带

幂等性解决的是：

```text
同一个请求重复发多次，不应该重复产生业务效果。
```

在 AI 应用里，重复请求很常见：

```text
前端重试
网络超时后用户又点一次
模型调用重试
服务端重试
用户刷新页面
```

如果没有幂等性，创建工单可能重复创建多条。

所以阶段 3 引入了：

```text
Idempotency-Key
参数指纹
confirmation_id 作为创建工单幂等键
```

### 8. trace_id 是排查工具调用链路的线索

一次 AI 工具调用可能跨越：

```text
入口 HTTP 请求
模型调用
工具决策
工具执行
Python 调 Java
Java 返回响应
第二轮模型总结
```

如果没有 trace_id，出了问题很难定位。

有了 trace_id，可以把这些日志串起来。

这对真实生产环境很重要。

### 9. LangChain 是抽象层，不是业务边界

LangChain 在阶段 3 里做了三件事：

```text
ChatModel：统一模型调用接口
Tool：包装 Python callable 和参数 schema
Structured output：封装结构化输出
```

但 LangChain 不负责：

```text
你的业务权限
你的用户确认
你的幂等键
你的字段白名单
你的 Java API 业务规则
你的日志脱敏策略
你的测试边界
```

所以你以后用 LangChain，要记住一句话：

```text
LangChain 帮你编排 AI 组件，不替你承担业务安全责任。
```

## 当前项目分层复盘

`projects/ai-service` 现在大致分成这些层。

| 层 | 目录或文件 | 职责 |
| --- | --- | --- |
| app 入口 | `app/main.py` | 创建 FastAPI 应用，注册 router、middleware、exception handler |
| router | `app/routers/` | 接 HTTP 请求，调用 service，返回响应模型 |
| schema | `app/schemas/` | 定义请求、响应、工具参数、工具结果、确认计划等数据契约 |
| service | `app/services/` | 模型调用、工具编排、Java HTTP client、工单流程编排 |
| tools | `app/tools/` | 工具函数、工具注册表、幂等辅助、LangChain Tool 适配 |
| core | `app/core/` | 配置、日志、trace、异常、CORS、token 估算 |
| middleware | `app/middleware/` | 请求追踪 |
| tests | `tests/` | 自动化测试 |

这个分层有一个重要好处：

```text
router 不知道模型 SDK 细节
service 不直接关心 HTTP 响应格式
schema 专门描述数据契约
tools 专门描述可调用能力
core 专门提供基础设施
tests 可以替换依赖，做分层验证
```

以后项目变复杂时，这种分层会救你。

如果所有逻辑都写在一个路由函数里，后面会很难测试、很难维护、很难排查。

## 原生 SDK 和 LangChain 的关系

阶段 3 后半段我们引入了 LangChain。

你现在应该能这样区分：

| 方式 | 适合场景 | 优点 | 注意点 |
| --- | --- | --- | --- |
| 原生 OpenAI-compatible SDK | 需要完全掌控请求参数和响应结构 | 直观、透明、少一层封装 | 样板代码更多 |
| LangChain ChatModel | 希望统一模型调用接口 | 消息对象清晰，后续接 chain/agent 更自然 | 仍要处理业务错误和边界 |
| LangChain Tool | 希望把 Python 函数包装成可给模型使用的工具 | 工具名、描述、参数 schema 更标准 | 不替代项目工具注册表和权限 |
| LangChain structured output | 希望用 schema 约束模型输出 | 少写解析样板，更容易和 LangChain 生态衔接 | 仍要 Pydantic 兜底校验 |

所以不是“用了 LangChain，就不用原生 SDK”。

更准确的理解是：

```text
原生 SDK 帮你看清底层。
LangChain 帮你把常见 AI 编排模式封装起来。
```

阶段 3 先写底层，再引入 LangChain，是为了避免你只会框架，不懂框架下面发生了什么。

## 当前项目已经具备的能力

到第 22 节，当前项目已经具备这些能力。

### 1. AI 服务基础能力

```text
FastAPI 服务启动
健康检查
配置读取
统一异常
日志
trace_id
CORS
pytest 测试
```

### 2. 模型调用能力

```text
OpenAI-compatible SDK 调用
多轮 messages
prompt 构建
timeout
retry/rate limit 错误映射
流式输出
token usage 提取
fake LLM 测试
```

### 3. 结构化输出能力

```text
JSON Mode
Pydantic schema
TicketExtraction
原生 /extract-ticket
LangChain /langchain-extract-ticket
结构化输出错误映射
```

### 4. 工具调用能力

```text
工具参数 schema
工具结果 schema
工具注册表
权限等级
模型工具决策
工具执行
tool message 回传
模型二次总结
LangChain Tool 包装
```

### 5. Java 业务服务接入能力

```text
Java mock 订单服务
Java mock 工单服务
Python httpx client
base_url 配置
timeout 配置
上游错误映射
字段白名单映射
跨服务 trace_id
```

### 6. 写操作安全能力

```text
待确认计划
操作者绑定
参数绑定
参数指纹
TTL 过期
确认幂等
执行幂等
创建工单流程
```

### 7. 测试能力

```text
fake OpenAI-compatible client
fake LangChain ChatModel
fake LangChain Tool
fake tool
fake Java API
httpx.MockTransport
dependency_overrides
service/client/router 分层测试
```

这已经不是一个小 demo。

它是一个可继续演进的 AI 应用工程练习底座。

## 当前项目还没有解决什么

阶段 3 完成，不代表已经能做完整生产级 Agent。

当前还没有重点解决：

```text
真实用户登录和权限系统
真实 Spring Boot 业务服务
真实数据库
持久化确认计划
分布式幂等
队列和异步任务
复杂多工具循环
多工具并行调用
RAG 知识库检索
embedding 和向量数据库
LangGraph 状态机
完整 Agent 评测
生产级监控和告警
Docker Compose 一键启动
```

这些不是缺陷。

它们是后续阶段的学习内容。

你现在要明确边界：

```text
阶段 3 解决“工具调用和业务服务接入基础”。
阶段 4 适合开始解决“企业知识库 RAG”。
阶段 5 再把 LangGraph Agent 工作流做起来。
阶段 6 再补生产化、评测、部署和作品整理。
```

## 为什么下一阶段适合学 RAG

你可能会问：

```text
我们已经学了 Tool Calling，为什么不直接继续 Agent？
```

原因是，真实 AI 应用通常需要两类外部能力。

第一类是业务工具：

```text
查订单
查退款
查物流
创建工单
```

这部分阶段 3 已经打基础。

第二类是知识检索：

```text
查公司政策
查产品文档
查售后规则
查内部 FAQ
查历史案例
```

这就是 RAG。

如果没有 RAG，模型只能依靠自身训练知识和 prompt。

但企业应用里，大量答案来自企业自己的文档。

所以下一阶段学 RAG 很合理。

因为未来智能工单 Agent 需要同时具备：

```text
业务工具调用能力
+ 企业知识库检索能力
+ 用户确认和工作流能力
```

阶段 3 已经完成第一部分。

下一阶段补第二部分。

之后再进入 LangGraph，把它们编排成更完整的 Agent/Workflow。

## 你现在应该能讲清楚的 10 个问题

### 1. Tool Calling 是什么

标准回答：

```text
Tool Calling 是模型返回“想调用哪个工具、参数是什么”的结构化请求。模型本身不执行工具，真正执行工具的是后端。后端要校验工具名、参数、权限和结果，再决定是否把工具结果交回模型总结。
```

### 2. 为什么 AI 不能直接操作业务系统

标准回答：

```text
模型输出不可信，可能误判、幻觉、被 prompt injection 影响，也没有真实业务权限上下文。业务系统的数据库、权限、事务和审计必须由后端控制。AI 只能通过后端白名单工具间接调用业务能力。
```

### 3. 结构化输出和 Tool Calling 有什么区别

标准回答：

```text
结构化输出是让模型把自然语言整理成固定格式数据，例如 TicketExtraction。Tool Calling 是让模型提出调用外部工具的请求，例如 query_order(order_id)。前者偏数据抽取，后者偏外部能力调用。
```

### 4. Pydantic 在阶段 3 里的作用是什么

标准回答：

```text
Pydantic 是后端的数据契约和校验边界。用户输入、模型输出、工具参数、工具结果、Java API 返回值和工单命令都要经过 Pydantic 校验，避免不可信数据直接进入业务逻辑。
```

### 5. `/tool-decision` 和 `/tool-chat` 有什么区别

标准回答：

```text
/tool-decision 只观察模型是否想调用工具，返回直接回答或工具调用意图，不执行工具。/tool-chat 是完整只读工具链路，会校验并执行 query_order，再把 tool message 交回模型生成最终回答。
```

### 6. 为什么创建工单要先创建确认计划

标准回答：

```text
创建工单属于写操作，不能因为模型抽取出字段就直接执行。确认计划会绑定工具名、参数、操作者、过期时间和参数指纹，用户确认后后端再读取原计划执行，避免参数被替换和误操作。
```

### 7. 为什么工具调用需要幂等

标准回答：

```text
网络重试、用户重复点击、服务端重试都可能导致同一个操作被请求多次。幂等性保证同一请求不会重复产生业务效果，例如不会重复创建多张工单。
```

### 8. Java mock 服务在阶段 3 的作用是什么

标准回答：

```text
Java mock 服务模拟未来的 Java/Spring Boot 业务系统，让 Python AI 服务先练习通过 HTTP 调用订单和工单接口、处理 timeout/404/500、做字段白名单映射和跨服务 trace_id 传递。
```

### 9. LangChain 在当前项目里负责什么

标准回答：

```text
LangChain 在当前项目里负责封装模型调用、Tool 包装和结构化输出。它让 AI 编排更标准，但不负责业务权限、用户确认、幂等、Java API 业务规则和安全边界。
```

### 10. 阶段 3 完成后，为什么要进入 RAG

标准回答：

```text
阶段 3 解决了业务工具调用基础，但企业 AI 应用还需要从内部文档中检索知识。RAG 能让模型基于企业文档、FAQ、规则和历史案例回答问题，为后续智能工单 Agent 提供知识来源。
```

## 阶段 3 验收清单

你可以用下面这张表验收阶段 3。

| 能力 | 是否完成 | 说明 |
| --- | --- | --- |
| 能解释 Tool Calling | 已完成 | 知道模型只提出工具请求，后端负责执行 |
| 能定义工具参数 | 已完成 | `QueryOrderArgs`、JSON Schema、Pydantic 校验 |
| 能执行只读工具 | 已完成 | `query_order` 调 Java mock API |
| 能校验工具结果 | 已完成 | `QueryOrderResult`、字段白名单映射 |
| 能处理工具错误 | 已完成 | timeout、404、上游 500 映射成统一错误 |
| 能做工具权限控制 | 已完成 | `TOOL_REGISTRY`、`authorize_tool_call()` |
| 能处理工具幂等 | 已完成 | `Idempotency-Key`、参数指纹 |
| 能调用 Java mock 服务 | 已完成 | `JavaOrderClient`、`JavaTicketClient` |
| 能让模型决定是否调用工具 | 已完成 | `/tool-decision` |
| 能完成工具执行和模型总结 | 已完成 | `/tool-chat` |
| 能处理写操作确认 | 已完成 | confirmation plan、confirm、execute |
| 能创建工单 | 已完成 | `/tickets/plans` + `/tickets/confirmations/{id}/execute` |
| 能串联 trace_id | 已完成 | 出站 `X-Trace-Id`、关键日志 |
| 能做分层测试 | 已完成 | fake client、MockTransport、dependency_overrides |
| 能理解 LangChain 定位 | 已完成 | 先手写底层，再映射 LangChain |
| 能使用 LangChain ChatModel | 已完成 | `/langchain-chat` |
| 能使用 LangChain Tool | 已完成 | `/tools/langchain`、`StructuredTool` |
| 能使用 LangChain 结构化输出 | 已完成 | `/langchain-extract-ticket` |

## 阶段 3 复盘练习

### 练习 1：画出 `/tool-chat` 的调用链路

题目：

```text
用文字画出用户请求 /tool-chat 后，系统从模型决策到最终中文回答的完整链路。
```

参考答案：

```text
用户发送问题
-> FastAPI /tool-chat
-> ChatRequest 校验
-> ToolCallingChatService
-> 第一轮模型调用，传入 tools 和 tool_choice="auto"
-> 模型返回 tool_calls
-> 后端解析工具名和参数
-> 校验工具是否存在、启用、只读、不需要确认
-> QueryOrderArgs 校验 order_id
-> 执行 query_order
-> JavaOrderClient 调 Java mock /orders/{order_id}
-> 字段白名单映射
-> QueryOrderResult 校验
-> 构造 assistant tool-call message 和 tool message
-> 第二轮模型调用
-> 模型生成最终中文回答
-> ChatResponse 返回给用户
```

### 练习 2：说明 `/extract-ticket` 和 `/langchain-extract-ticket` 的区别

题目：

```text
这两个接口都抽取工单字段，为什么还要同时保留？
```

参考答案：

```text
/extract-ticket 使用原生 OpenAI-compatible SDK、JSON Mode 和手动 Pydantic 解析，能让我们看清结构化输出底层流程。

/langchain-extract-ticket 使用 LangChain ChatModel 的 with_structured_output(TicketExtraction, method="json_mode")，能让我们学习 LangChain 对结构化输出的封装。

同时保留是为了教学对比：一个看底层，一个看框架封装。它们都不能替代后端自己的 Pydantic 校验、异常映射和安全边界。
```

### 练习 3：判断哪些操作需要用户确认

题目：

```text
下面哪些工具应该需要用户确认？

1. 查询订单状态
2. 查询物流信息
3. 创建售后工单
4. 发起退款
5. 修改收货地址
6. 查询公开帮助文档
```

参考答案：

```text
通常需要确认：
3. 创建售后工单
4. 发起退款
5. 修改收货地址

通常不需要确认，但仍要权限控制和参数校验：
1. 查询订单状态
2. 查询物流信息
6. 查询公开帮助文档

判断标准是：是否产生业务写入、是否可能造成资金/履约/客户权益变化、是否涉及敏感数据或不可逆后果。
```

### 练习 4：解释为什么 Java 返回值也要 Pydantic 校验

题目：

```text
Java mock 服务是我们自己写的，为什么 Python 还要校验它返回的数据？
```

参考答案：

```text
跨服务调用的数据都应该当作外部输入处理。即使服务是自己团队写的，也可能因为版本变更、字段缺失、类型变化、错误响应格式变化或上游 bug 导致数据不符合预期。

Python AI 服务要把 Java 返回值映射成给模型看的工具结果，所以必须先用字段白名单和 Pydantic 校验，避免把不稳定或敏感字段交给模型。
```

### 练习 5：设计一个新工具 `query_refund`

题目：

```text
如果下一步要新增 query_refund(order_id)，你觉得至少要补哪些内容？
```

参考答案：

```text
至少需要：

1. 定义 QueryRefundArgs，校验 order_id。
2. 定义 QueryRefundResult，描述退款状态、退款金额、退款原因等安全字段。
3. 在工具注册表中新增 query_refund，标记为 read。
4. 实现 JavaRefundClient 或对应 HTTP client。
5. 做 Java API 返回字段白名单映射。
6. 校验工具结果。
7. 处理 timeout、404、上游错误。
8. 给模型可见工具列表增加该工具。
9. 为 service/client/router 写测试。
10. 确认日志不记录敏感字段。
```

## 自测题

### 自测 1：模型能不能直接创建工单？

参考答案：

```text
不能。模型可以辅助抽取工单字段，也可以提出创建工单的意图，但真正创建工单必须由后端在用户确认后执行，并经过参数绑定、权限控制、幂等保护和 Java 业务服务调用。
```

### 自测 2：Tool Calling 里最容易被误解的一点是什么？

参考答案：

```text
最容易误解的是以为模型真的调用了函数。实际上模型只返回工具调用请求，函数调用发生在后端代码里。后端必须校验工具名、参数、权限和结果。
```

### 自测 3：为什么不能只靠 prompt 做安全控制？

参考答案：

```text
prompt 只是给模型的指令，不是强制权限系统。模型可能误解、幻觉、被诱导或输出不符合预期内容。安全控制必须放在后端，包括白名单、权限等级、确认机制、Pydantic 校验和幂等保护。
```

### 自测 4：LangChain Tool 和项目里的 `ToolDefinition` 是不是一回事？

参考答案：

```text
不是。LangChain Tool 更偏模型侧工具描述和 callable 封装，项目里的 ToolDefinition 更偏业务侧工具注册、权限等级、启用状态和是否需要确认。当前项目可以把两者结合，但不能用 LangChain Tool 替代项目自己的权限边界。
```

### 自测 5：为什么 `/tool-decision` 不执行工具？

参考答案：

```text
/tool-decision 是教学和调试接口，用来单独观察模型是否想调用工具以及返回了什么参数。它不执行工具，是为了把“模型决策”和“后端执行”拆开学习。真正完整执行链路由 /tool-chat 负责。
```

### 自测 6：什么情况下工具结果不应该交给模型总结？

参考答案：

```text
如果工具执行失败，例如订单不存在、Java 服务超时、上游 500、返回值校验失败或权限不允许，就不应该伪造成功结果交给模型总结。后端应该直接返回统一错误，让调用方知道真实失败原因。
```

### 自测 7：阶段 3 和阶段 4 的关系是什么？

参考答案：

```text
阶段 3 解决业务工具调用基础，让 AI 服务能安全调用订单、工单等业务能力。阶段 4 将学习 RAG，让 AI 服务能从企业文档中检索知识。未来完整 Agent 需要同时具备工具调用能力和知识检索能力。
```

## 本节总结

阶段 3 结束后，你要记住这条主线：

```text
用户自然语言
-> 模型理解和决策
-> 后端校验工具名和参数
-> 后端执行受控工具
-> Java 业务服务提供真实数据或执行写操作
-> 后端校验结果
-> 模型负责解释和总结
-> 日志、trace_id、幂等、确认机制保证工程可控
```

这就是 AI 应用工程和普通聊天 demo 的区别。

普通聊天 demo 只关心：

```text
模型回复了什么
```

AI 应用工程还要关心：

```text
谁发起的请求
模型为什么调用工具
工具有没有权限
参数是否合法
业务服务是否成功
结果是否可信
写操作是否确认
重复请求是否会重复执行
日志能不能查到
测试能不能覆盖
```

如果你能把这些讲清楚，阶段 3 就不是“学过了”，而是真的开始入门 AI 应用工程了。

## 下一阶段预告

下一阶段建议进入：

```text
阶段 4：企业知识库 RAG 基础
```

它会解决新的问题：

```text
模型不知道公司内部文档怎么办？
如何把 Markdown、PDF、docx 等文档变成可检索知识？
什么是 chunk？
什么是 embedding？
什么是向量数据库？
如何检索 top_k 文档片段？
如何让回答带引用来源？
如何测试 RAG 回答质量？
```

阶段 3 已经学会“调用业务工具”。

阶段 4 会开始学习“检索企业知识”。

这两部分合起来，才是后面智能工单 Agent 的基础。

