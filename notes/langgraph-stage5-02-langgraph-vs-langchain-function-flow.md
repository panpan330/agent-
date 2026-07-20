# 阶段 5 第 2 节：LangGraph 和 LangChain / 普通函数流程的区别

## 本节定位

上一节我们先回答了一个问题：

```text
LangGraph 是什么，为什么现在才学？
```

这一节继续把边界讲清楚：

```text
普通函数流程、LangChain、LangGraph 到底分别该负责什么？
```

这不是一个小问题。

因为后面做智能工单 Agent 时，我们会同时碰到这些代码：

```text
普通 Python 函数 / service
LangChain ChatModel / Tool / structured output
LangGraph StateGraph / node / edge / checkpoint / interrupt
FastAPI router
Java mock 业务 API
RAG 检索服务
```

如果分工不清楚，很容易出现两种错误：

1. 明明一个普通函数就能解决的问题，硬塞进 LangGraph，代码变复杂。
2. 明明是多步骤、有状态、需要恢复和人工确认的流程，却只用普通函数硬写，后面越来越乱。

所以这一节不急着写代码。

本节的真正目标是建立判断标准：

```text
什么时候用普通函数？
什么时候用 LangChain？
什么时候用 LangGraph？
```

## 本节学习目标

学完这一节，你应该能做到：

1. 解释普通函数流程是什么。
2. 解释普通 service 编排为什么适合确定性业务逻辑。
3. 解释 LangChain 主要解决什么问题。
4. 解释 LangGraph 主要解决什么问题。
5. 解释 LangChain 和 LangGraph 不是互相替代关系。
6. 解释 workflow 和 agent 的区别。
7. 解释为什么智能工单 Agent 不能只靠一串普通函数。
8. 解释为什么智能工单 Agent 也不应该把所有业务代码都塞进 LangGraph。
9. 能画出本项目后续的三层分工：业务函数层、LLM 能力层、流程编排层。
10. 面试或跟别人讲项目时，能说明你为什么这样选型。

## 本节先不学什么

为了把概念打牢，本节暂时不做这些事：

1. 不安装新的依赖。
2. 不新增运行时代码。
3. 不调用真实模型。
4. 不启动 Qdrant 或 Milvus。
5. 不修改 Java mock 服务。
6. 不写 LangGraph 最小图。
7. 不讲 reducer 细节。
8. 不讲 checkpoint 存储实现。

这些后面会按顺序学。

本节只做一件事：

```text
把普通函数、LangChain、LangGraph 的边界讲透。
```

## 一、基础知识铺垫

### 1. 什么是“流程”

写程序时，我们经常不是只做一个动作，而是做一连串动作。

例如一个客服问题：

```text
用户说：我的订单 1001 一直没发货，帮我查一下。
```

程序可能要做这些事情：

```text
1. 接收用户输入
2. 判断用户想查订单
3. 提取订单号 1001
4. 调用订单查询接口
5. 判断接口是否成功
6. 把查询结果整理成中文
7. 返回给用户
```

这一串动作就叫流程。

流程不一定复杂。一个简单流程可以直接写成一个函数。

但是当流程里开始出现这些东西时，复杂度会明显上升：

```text
分支：不同情况走不同路线
循环：模型可能需要多次调用工具
状态：上一步结果要给下一步用
暂停：需要等用户确认
恢复：用户确认后从中间继续
错误：某一步失败后要兜底
审计：要知道每一步发生了什么
测试：每个分支都要能测
```

LangGraph 之所以重要，是因为 AI 应用很容易同时出现这些问题。

### 2. 什么是普通函数流程

普通函数流程，就是用普通代码把步骤串起来。

伪代码大概是这样：

```python
def handle_user_message(message: str) -> str:
    intent = classify_intent(message)

    if intent == "query_order":
        order_id = extract_order_id(message)
        order = query_order(order_id)
        return summarize_order(order)

    if intent == "rag_question":
        docs = retrieve_docs(message)
        return answer_with_docs(message, docs)

    return "我暂时不能处理这个问题。"
```

这类写法的优点很明显：

1. 直观。
2. 好读。
3. 好调试。
4. 好测试。
5. 不依赖复杂框架。
6. 适合业务边界明确的小流程。

普通函数流程不是落后的写法。

在真实项目里，很多核心业务都应该保持普通函数或普通 service 的形式。

例如我们项目里的这些能力，就很适合作为普通 service：

```text
JavaOrderClient：调用 Java mock 订单接口
JavaTicketClient：调用 Java mock 工单接口
RagAnswerService：根据检索结果生成回答
TicketWorkflowService：字段提取、确认、创建工单的业务服务
Pydantic schema：校验请求和响应
工具注册表：校验工具名和参数
```

原因是这些模块做的是明确动作：

```text
输入是什么
输出是什么
失败时怎么处理
都可以说清楚
```

### 3. 普通函数流程什么时候开始吃力

普通函数流程适合小而明确的流程。

但当流程变成下面这样时，普通函数会开始变得吃力：

```text
用户先描述问题
系统判断能否直接 RAG 回答
如果不能直接回答，再判断是否要建工单
如果要建工单，提取字段
如果字段缺失，追问用户
用户补充后继续提取
如果字段齐了，让用户确认
用户确认后调用 Java API
如果 Java API 失败，要返回可解释错误
如果用户中途又问知识库问题，要能切换回答
整个过程要保存状态，下次继续
```

这时候用一个大函数硬写，通常会出现几个问题。

第一个问题：函数越来越长。

```text
一个 handle_message 函数里有十几个 if/else。
```

第二个问题：状态到处传。

```text
message、intent、order_id、ticket_fields、missing_fields、rag_docs、confirm_status
每个函数都要传一堆参数。
```

第三个问题：中断恢复难。

```text
流程走到“等待用户确认”时，函数已经返回了。
用户下一次回复“确认”时，程序怎么知道上次停在哪一步？
```

第四个问题：测试分支很麻烦。

```text
要测 RAG 分支、工单分支、字段缺失分支、用户拒绝分支、Java API 失败分支。
大函数会让这些测试互相牵连。
```

第五个问题：可观测性差。

```text
线上出问题时，只知道最终失败了，不清楚失败在意图识别、RAG、字段提取、确认，还是 Java API。
```

这些问题不是 Python 独有，也不是 FastAPI 独有。

这是“多步骤 Agent 流程”的天然复杂度。

### 4. 什么是 LangChain

LangChain 是一个 LLM 应用开发框架。

你可以先把它理解成：

```text
LangChain 主要帮我们更方便地使用模型、消息、工具、结构化输出、agent harness 等 LLM 组件。
```

在前面的阶段里，我们已经见过 LangChain 的一些作用：

```text
ChatModel：统一不同模型供应商的调用方式
Tool：把 Python 函数包装成模型能理解的工具
structured output：让模型输出符合 Pydantic schema 的结构
messages：用统一格式表达 system/user/assistant/tool 消息
retriever：把检索能力接入 LLM 应用
agent：提供一个模型调用工具的循环框架
```

LangChain 不是数据库。

LangChain 不是 Web 框架。

LangChain 也不是专门用来管理复杂业务流程的状态机。

它更像是 LLM 应用里的“组件层”：

```text
我需要调用模型 -> LangChain 有 ChatModel
我需要绑定工具 -> LangChain 有 Tool
我需要结构化输出 -> LangChain 有 schema 支持
我需要一个常见 agent loop -> LangChain 有 create_agent
```

官方文档中也把 LangChain agents 描述为一种高度可配置的 harness。这里的 harness 可以理解成“围绕模型循环的一套外壳”：它把模型、prompt、工具、中间件、上下文等组织起来，让模型可以反复调用工具直到任务完成。

### 5. 什么是 harness

这个词初学时容易抽象。

在这里可以先这样理解：

```text
harness = 让模型能稳定运行起来的一套外部支撑结构
```

模型本身只会根据输入生成输出。

但是一个 Agent 不是只调用模型一次。

Agent 可能要：

```text
1. 给模型系统提示词
2. 告诉模型有哪些工具
3. 接收模型的 tool call
4. 执行工具
5. 把工具结果放回消息
6. 再次调用模型
7. 直到模型给出最终回答
```

这一圈支撑结构就可以叫 harness。

简单说：

```text
模型是发动机。
harness 是让发动机能在应用里工作的外壳、线路、控制结构。
```

LangChain 的 `create_agent` 就是这种 harness 的代表。

### 6. 什么是 LangGraph

LangGraph 是面向长流程、有状态 Agent 的编排框架和运行时。

你可以先抓住这几个关键词：

```text
低层
编排
有状态
长流程
可恢复
可人工介入
可观察
```

LangGraph 不主要帮你写 prompt。

LangGraph 不主要帮你封装某个模型供应商。

LangGraph 不主要帮你写普通业务函数。

它更关心的是：

```text
整个 Agent 流程有几个步骤？
每一步叫什么？
每一步读写哪些状态？
下一步怎么决定？
流程什么时候结束？
流程能不能暂停？
暂停后能不能恢复？
每一步的状态变化能不能追踪？
```

如果 LangChain 更像 LLM 组件层，那么 LangGraph 更像流程编排层。

### 7. 什么是图式编排

LangGraph 里的 graph，就是图。

图不是图片。

在程序里，图可以理解为：

```text
节点 + 边
```

节点是一个个动作。

边是动作之间的连接关系。

例如：

```text
START
  -> classify_intent
  -> route_by_intent
  -> rag_answer
  -> END
```

再复杂一点：

```text
START
  -> classify_intent
  -> route
     -> rag_answer -> END
     -> extract_ticket_fields -> check_missing_fields
        -> ask_missing_fields -> END
        -> ask_user_confirmation -> END
```

这里的节点可能是：

```text
classify_intent：判断用户意图
rag_answer：调用 RAG 服务回答
extract_ticket_fields：提取工单字段
ask_missing_fields：追问缺失字段
ask_user_confirmation：请求用户确认
create_ticket：调用 Java API 创建工单
```

边表示：

```text
这一步结束后应该去哪一步
```

条件边表示：

```text
根据当前状态决定下一步去哪
```

### 8. 什么是 state

state 就是流程运行过程中的状态。

普通函数里也有状态，只是常常藏在局部变量里：

```python
intent = "create_ticket"
ticket_fields = {"title": "订单没发货"}
missing_fields = ["priority"]
```

LangGraph 会要求我们把这些状态显式设计出来。

例如智能工单 Agent 可能需要这些状态：

```text
messages：用户和 AI 的对话消息
intent：当前识别出的用户意图
rag_answer：知识库回答
retrieved_docs：检索到的文档
ticket_fields：已提取出的工单字段
missing_fields：还缺哪些字段
needs_confirmation：是否需要用户确认
confirmation_status：用户是否确认
ticket_id：创建成功后的工单 ID
error：流程中的错误信息
trace_id：请求追踪 ID
```

显式设计 state 的好处是：

```text
流程每一步读什么、写什么会更清楚。
暂停和恢复有基础。
测试可以直接构造 state。
日志和调试能看到状态变化。
```

### 9. 什么是 workflow

workflow 是工作流。

它通常指：

```text
步骤顺序比较确定的流程。
```

例如：

```text
提交订单
-> 扣库存
-> 生成支付单
-> 等待支付
-> 支付成功后发货
```

或者：

```text
文档加载
-> 文本清洗
-> chunk 切分
-> embedding
-> 写入向量库
```

workflow 的特点是：

```text
流程大体固定
分支规则由代码决定
每一步的职责比较明确
```

RAG 入库流程就很像 workflow。

### 10. 什么是 agent

agent 比 workflow 更动态。

在 LLM 应用里，agent 常常指：

```text
模型可以根据任务状态，决定下一步做什么、是否调用工具、调用哪个工具。
```

例如用户问：

```text
帮我看看订单 1001 是不是发货了，如果没发货就创建一个工单。
```

Agent 可能需要自己决定：

```text
先查订单
如果订单已发货，就直接回答
如果订单没发货，再准备创建工单
如果缺少工单标题，就追问
如果信息齐了，就让用户确认
确认后再调用创建工单工具
```

这里不是简单的固定顺序。

模型和代码会共同决定下一步。

所以 agent 的难点不只是“会调用工具”，而是：

```text
模型决定 + 代码边界 + 状态保存 + 安全确认 + 错误兜底
```

### 11. 确定性流程和非确定性流程

理解 LangGraph 前，一定要区分这两个词。

确定性流程：

```text
同样的输入，在同样条件下，代码大概率走同样路线。
```

例如：

```python
if order_status == "shipped":
    return "已发货"
else:
    return "未发货"
```

非确定性流程：

```text
流程中有模型判断、自然语言理解、工具选择，结果可能受 prompt、上下文、模型版本影响。
```

例如：

```text
用户说“这个单子不对劲”
模型要判断这是查订单、退款、投诉，还是创建工单。
```

AI 应用通常是两者混合：

```text
模型负责理解自然语言和生成内容。
代码负责校验、权限、安全边界和确定性动作。
```

这也是我们后面要坚持的原则：

```text
让模型做它擅长的理解和表达。
让代码做它必须负责的规则和执行。
让 LangGraph 管理多步骤流程和状态。
```

## 二、本节主题系统讲解

### 1. 三层心智模型

这一节最重要的结论是下面这张分工图：

```text
┌──────────────────────────────────────────────┐
│ LangGraph：流程编排层                         │
│ 负责状态、节点、边、分支、暂停、恢复、可观察     │
└──────────────────────────────────────────────┘
                    ↓ 调用
┌──────────────────────────────────────────────┐
│ LangChain：LLM 能力层                         │
│ 负责模型、消息、工具、结构化输出、agent harness │
└──────────────────────────────────────────────┘
                    ↓ 调用
┌──────────────────────────────────────────────┐
│ 普通函数 / service：业务能力层                 │
│ 负责查订单、查知识库、创建工单、校验、错误处理   │
└──────────────────────────────────────────────┘
```

用更简单的话说：

```text
普通函数 / service：把一件具体事情做好。
LangChain：把模型能力接进来。
LangGraph：把多件事情按状态和分支组织起来。
```

### 2. 普通函数负责什么

普通函数应该负责具体、稳定、可测试的动作。

例如：

```python
def normalize_order_id(raw_order_id: str) -> str:
    return raw_order_id.strip().upper()
```

这个函数不需要 LangChain。

也不需要 LangGraph。

因为它只是一个明确转换：

```text
输入原始订单号
输出标准订单号
```

再比如：

```python
def is_sensitive_action(action: str) -> bool:
    return action in {"create_ticket", "cancel_order", "refund"}
```

这也是普通函数应该做的事。

原因是安全规则必须由代码确定，不能交给模型随意决定。

我们项目里后续也会坚持这个原则：

```text
校验、权限、确认、白名单、字段转换、错误兜底，优先用普通函数 / service。
```

### 3. LangChain 负责什么

LangChain 适合处理和 LLM 交互相关的能力。

例如：

```text
把用户消息变成 ChatModel 输入
把 Python 函数包装成工具
让模型输出 Pydantic 结构
管理 system/user/assistant/tool messages
让模型在工具调用循环中工作
```

举一个非常小的例子：

```python
from langchain.agents import create_agent

agent = create_agent(
    model="openai:gpt-5.5",
    tools=[query_order],
    system_prompt="你是客服助手，回答要简洁准确。",
)
```

这段代码表达的是：

```text
我想创建一个能调用 query_order 工具的模型助手。
```

它关注的是：

```text
模型是谁
工具有哪些
系统提示词是什么
模型如何和工具循环交互
```

但是它不直接回答：

```text
等待用户确认后怎么恢复？
多轮工单状态放哪里？
不同节点怎么拆？
线上如何看每一步状态变化？
```

这些就是 LangGraph 更擅长的范围。

### 4. LangGraph 负责什么

LangGraph 适合处理多步骤、有状态、带分支的 Agent 流程。

例如我们后面要做的智能工单 Agent：

```text
用户问题
-> 意图识别
-> 如果是知识问题，走 RAG 回答
-> 如果是工单问题，提取工单字段
-> 如果字段缺失，追问用户
-> 如果字段齐了，让用户确认
-> 用户确认后，调用 Java mock 创建工单
-> 返回结果
```

用图式思维看，它大概是：

```text
START
  -> classify_intent
  -> route_intent
     -> rag_answer
     -> extract_ticket_fields
        -> check_missing_fields
           -> ask_missing_fields
           -> ask_confirmation
              -> create_ticket
  -> END
```

这里每个节点都可以调用普通函数或 LangChain 组件。

例如：

```text
classify_intent 节点：可能调用 LangChain structured output
rag_answer 节点：调用已有 RagAnswerService
extract_ticket_fields 节点：可能调用模型结构化输出
ask_confirmation 节点：生成确认提示，但不执行写操作
create_ticket 节点：调用 JavaTicketClient
```

LangGraph 的价值不是替代这些 service。

LangGraph 的价值是把它们组织成可控流程。

### 5. LangChain 和 LangGraph 不是二选一

很多初学者容易问：

```text
学了 LangGraph，是不是就不用 LangChain 了？
```

不是。

更准确的理解是：

```text
LangChain 可以在 LangGraph 的节点里使用。
LangGraph 也可以完全不依赖 LangChain。
但在多数 LLM 应用里，两者经常配合使用。
```

例如：

```text
LangGraph 负责：
  现在应该执行 classify_intent 还是 rag_answer？
  当前 state 里有哪些字段？
  下一步去哪？
  是否暂停等用户确认？

LangChain 负责：
  classify_intent 节点里怎么调用模型？
  extract_ticket_fields 节点里怎么做结构化输出？
  工具怎么绑定给模型？
  messages 怎么组织？
```

这个分工非常重要。

如果你说：

```text
我用 LangGraph 管流程，用 LangChain 管模型调用和工具抽象，用普通 service 管业务动作。
```

这就是比较成熟的表达。

### 6. 三者对比表

| 维度 | 普通函数 / service | LangChain | LangGraph |
| --- | --- | --- | --- |
| 核心定位 | 明确业务动作 | LLM 能力组件 | 有状态流程编排 |
| 主要解决 | 输入输出明确的逻辑 | 模型、消息、工具、结构化输出 | 多步骤、分支、暂停、恢复 |
| 是否必须有大模型 | 不需要 | 通常需要 | 不一定，但常用于 Agent |
| 是否适合复杂状态 | 一般 | 一般 | 适合 |
| 是否适合人工确认 | 可做，但容易散 | 不是重点 | 适合 |
| 是否适合中断恢复 | 需要自己写很多 | 不是重点 | 适合 |
| 是否适合单个小功能 | 很适合 | 看是否涉及 LLM | 通常没必要 |
| 测试方式 | 单元测试最简单 | fake model / fake tool | fake node / fake state / fake graph |
| 在本项目中的角色 | 业务基础能力 | 模型能力接入 | 智能工单主流程 |

### 7. 什么时候只用普通函数

如果一个功能满足下面条件，普通函数或普通 service 通常就够了：

```text
步骤少
输入输出明确
没有多轮状态
不需要暂停恢复
不需要模型自己决定下一步
失败处理简单
```

例如：

```text
校验订单号格式
把 Java API 响应映射成 Pydantic 响应模型
判断某个操作是否敏感
从 payload 里取白名单字段
计算检索结果是否低于 score_threshold
```

这些都不要硬塞到 LangGraph 里。

如果把这些小函数都写成图节点，反而会让系统变难懂。

### 8. 什么时候用 LangChain

如果功能的核心是“和大模型交互”，LangChain 就有价值。

例如：

```text
调用 ChatModel
统一 OpenAI-compatible 模型接口
绑定 tools
解析结构化输出
组织 messages
管理一个简单工具调用循环
把 retriever 接到问答链路中
```

举例：

```text
“请把用户输入提取成 TicketDraft”
```

这件事适合用 LangChain structured output。

因为它不是纯规则能稳定完成的事，模型理解自然语言更合适。

但是提取出来以后，字段是否合法、是否缺失、能不能创建工单，仍然要用代码判断。

### 9. 什么时候用 LangGraph

如果功能满足下面任意几个条件，就可以考虑 LangGraph：

```text
流程有多个节点
每个节点职责不同
需要根据状态选择下一步
需要多轮对话
需要等待用户补充字段
需要等待用户确认
需要恢复上次流程
需要记录每一步状态变化
需要把 RAG、工具调用、业务 API 串起来
```

智能工单 Agent 正好符合这些条件。

它不是“一次模型调用返回一个答案”。

它更像一个可中断的业务办理流程：

```text
理解问题
查知识库
判断是否需要工单
收集字段
确认
执行
反馈结果
```

这就是 LangGraph 适合接手的地方。

### 10. 为什么不能把所有代码都交给 LangGraph

LangGraph 很强，但不是越多越好。

一个常见错误是：

```text
既然 LangGraph 管流程，那我把所有函数都改成节点。
```

这会带来几个坏处：

1. 小逻辑变重。
2. 节点数量爆炸。
3. 测试变复杂。
4. 业务规则被流程框架淹没。
5. 新人看不出真正的业务重点。

正确做法是：

```text
节点保持粗粒度。
节点内部调用普通 service。
service 内部再调用更小的函数。
```

例如：

```text
create_ticket 节点
  -> 调用 TicketWorkflowService
     -> 校验字段
     -> 构造 Java 请求
     -> 调用 JavaTicketClient
     -> 映射响应
```

这样 LangGraph 图看起来是业务流程。

普通 service 里保留具体业务实现。

### 11. 为什么不能只用 LangChain agent

另一种常见问题是：

```text
LangChain 已经有 create_agent 了，为什么还要 LangGraph？
```

如果任务很简单，`create_agent` 可能够用。

例如：

```text
用户问一个问题
模型决定是否调用一个查询工具
工具结果返回模型
模型回答
```

这类流程不复杂。

但是智能工单流程有业务安全边界：

```text
创建工单前必须确认
敏感操作不能让模型直接执行
缺字段时要暂停追问
用户下一轮补充后要接着上次状态继续
要能清楚记录每一步
```

这些东西如果全塞进一个 agent harness，后面会不好控制。

LangGraph 的优势是把流程显式拆出来：

```text
哪一步让模型判断
哪一步由代码判断
哪一步暂停
哪一步执行工具
哪一步结束
```

这比把所有行为都放进一个大 prompt 里可靠。

### 12. workflow 和 agent 的区别

官方文档对 workflow 和 agent 的区分可以这样理解：

```text
workflow：路线主要由代码预先写好。
agent：模型可以动态决定过程和工具使用。
```

本项目的智能工单 Agent 是两者混合。

它不是完全自由的 agent。

因为业务系统不能让模型随便调用。

它也不是完全固定的 workflow。

因为用户自然语言很多变，模型需要参与意图识别、字段提取和回答生成。

所以我们的设计会更接近：

```text
受控 Agent
```

也就是：

```text
模型可以参与理解和生成。
代码控制边界和执行。
LangGraph 控制流程和状态。
```

这比“让模型自己想怎么做就怎么做”更适合企业业务系统。

### 13. 当前项目里的具体分工

后面做智能工单 Agent 时，可以先用这个分工表指导代码设计。

| 能力 | 放在哪里 | 原因 |
| --- | --- | --- |
| FastAPI 接口入口 | router | HTTP 边界清楚 |
| 请求和响应校验 | Pydantic schema | 数据结构要稳定 |
| 调用真实/兼容模型 | LangChain ChatModel 或已有 client | 模型接入层 |
| 意图识别 | LangGraph 节点里调用 LangChain structured output | 既是流程节点，又涉及模型理解 |
| RAG 回答 | LangGraph 节点调用 RagAnswerService | RAG 逻辑已有 service，图只负责调度 |
| 工单字段提取 | LangGraph 节点里调用模型结构化输出 | 自然语言抽取适合模型 |
| 缺失字段判断 | 普通函数 / service | 规则明确 |
| 用户确认状态 | LangGraph state | 需要跨轮保存 |
| 创建工单 | LangGraph 节点调用 JavaTicketClient | 执行动作必须显式放在节点里 |
| trace_id 串联 | FastAPI + service + graph state | 后续可观察性需要 |
| 测试 | fake model / fake RAG / fake Java client | 不在测试里真实调用外部服务 |

### 14. 用一个例子看三种写法

假设需求是：

```text
用户说“订单 1001 没发货，帮我处理一下”
```

#### 写法一：普通函数流程

```python
def handle_message(message: str) -> str:
    intent = classify_intent(message)

    if intent == "query_order":
        order_id = extract_order_id(message)
        order = query_order(order_id)
        return summarize_order(order)

    if intent == "create_ticket":
        ticket = extract_ticket_fields(message)
        if ticket.missing_fields:
            return ask_missing_fields(ticket.missing_fields)
        return ask_confirmation(ticket)

    return fallback_answer()
```

这种写法能跑。

如果需求很小，它没问题。

但如果用户下一轮说“确认”，这个函数要知道：

```text
上次提取出的工单字段是什么？
上次停在确认节点吗？
这个确认对应哪个用户、哪个会话？
确认后该调用哪个 Java API？
```

这些状态管理会把普通函数写复杂。

#### 写法二：LangChain agent

```python
agent = create_agent(
    model=model,
    tools=[query_order, create_ticket],
    system_prompt="你是客服助手。创建工单前必须确认用户意愿。",
)
```

这种写法能快速搭一个能用工具的助手。

但业务上仍然要小心：

```text
模型会不会在没确认时调用 create_ticket？
确认状态保存在哪里？
用户中断后怎么恢复？
如何强制 create_ticket 只能在确认节点之后执行？
```

如果流程安全要求高，只靠 prompt 不够。

#### 写法三：LangGraph 编排

```text
START
  -> classify_intent
  -> route_intent
     -> query_order
     -> extract_ticket_fields
        -> check_missing_fields
           -> ask_missing_fields
           -> ask_confirmation
              -> create_ticket
  -> END
```

这种写法把流程边界显式写出来。

你可以清楚说明：

```text
create_ticket 只能从 ask_confirmation 之后进入。
缺字段会进入 ask_missing_fields。
RAG 问题不会进入 create_ticket。
每一步都读写统一 state。
暂停和恢复可以围绕 state/checkpoint 设计。
```

这就是阶段 5 要学的方向。

### 15. 为什么这一节重要

这一节看起来没有写代码，但它直接影响后面的代码质量。

如果这个边界不清楚，后面可能会写出这样的代码：

```text
一个巨大 graph，里面每个小函数都是节点。
一个巨大 LangChain agent，所有业务规则都靠 prompt 约束。
一个巨大 FastAPI service，所有状态都靠 if/else 和临时变量传递。
```

这三种都不理想。

我们后面的方向是：

```text
普通 service 保持清晰。
LangChain 负责模型能力。
LangGraph 负责流程编排。
FastAPI 负责 HTTP 入口。
Java mock service 负责模拟真实业务系统。
```

### 16. 对你以后工作有什么帮助

你以后如果面试或做项目，别人可能会问：

```text
为什么要用 LangGraph？
LangChain 不够吗？
普通 Python 写流程不行吗？
```

你不能只回答：

```text
因为 LangGraph 很火。
```

更好的回答是：

```text
普通函数适合明确的业务动作；LangChain 适合模型、工具、结构化输出等 LLM 能力；LangGraph 适合有状态、多步骤、可分支、可中断恢复的 Agent 编排。我的智能工单场景需要 RAG、字段提取、用户确认、Java API 调用和跨轮状态，所以用 LangGraph 做流程层，同时保留普通 service 做确定性业务逻辑。
```

这类回答能体现你不是只会调库，而是知道架构边界。

## 三、对当前项目的设计结论

### 1. 本节不改运行时代码

本节没有新增 `projects/ai-service` 的运行时代码。

原因是：

```text
这节的产出是架构判断，不是功能接口。
```

如果现在急着写 LangGraph 代码，你可能会看到 `StateGraph`、`add_node`、`add_edge`，但并不知道为什么这样拆。

后面第 3-12 节会逐步进入代码。

### 2. 现有 service 不会被废弃

阶段 5 不是推翻前面阶段。

前面写过的很多能力都会继续复用：

```text
RAG 检索问答
Tool Calling 思路
Java mock API client
工单字段 schema
用户确认机制
trace_id
fake 测试
```

LangGraph 只是把它们串成更清晰的流程。

### 3. 后续代码大致会怎么组织

后面可能会逐步出现类似结构：

```text
projects/ai-service/app/agents/
  ticket_agent_state.py
  ticket_agent_graph.py
  ticket_agent_nodes.py

projects/ai-service/app/services/
  继续保留 RAG、Java client、工单业务 service

projects/ai-service/app/api/
  继续保留 FastAPI router
```

这只是方向，不是本节必须落地的代码。

真实落地时仍然要看当前项目结构，避免乱加抽象。

### 4. 本阶段的核心架构原则

后面阶段 5 可以先记住这四句话：

```text
能用普通函数讲清楚的，不急着做成 graph。
涉及模型能力的，用 LangChain 或现有 LLM client。
涉及多步骤状态和分支的，用 LangGraph。
涉及真实业务执行的，必须由代码校验和控制。
```

这四句话会贯穿智能工单 Agent。

## 四、本节练习与参考答案

### 练习 1：判断下面功能应该放在哪里

请判断下面功能更适合放在普通函数、LangChain，还是 LangGraph：

```text
1. 校验订单号是否为空
2. 让模型把用户描述提取成工单字段
3. 在“知识库回答”和“创建工单”之间选择下一步
4. 调用 Java mock API 创建工单
5. 多轮保存用户已经补充过的字段
```

参考答案：

```text
1. 普通函数 / Pydantic 校验
2. LangChain structured output 或现有 LLM client
3. LangGraph 条件边 / 路由节点
4. 普通 Java client，由 LangGraph 节点显式调用
5. LangGraph state / checkpoint
```

### 练习 2：为什么普通函数不适合承载整个智能工单流程

请用自己的话回答。

参考答案：

```text
因为智能工单流程不是一次性动作。它有意图识别、RAG 回答、字段提取、缺失字段追问、用户确认、Java API 调用、错误兜底和跨轮状态。普通函数可以写小流程，但如果把所有状态和分支都放进一个函数，代码会变长、状态难保存、中断恢复困难、测试分支复杂。
```

### 练习 3：为什么也不能把所有业务逻辑都塞进 LangGraph

参考答案：

```text
LangGraph 适合做流程编排，不适合替代所有业务函数。订单号校验、字段白名单、权限判断、Java 响应映射等逻辑输入输出明确，用普通函数或 service 更清楚、更容易测试。如果每个小函数都变成图节点，图会变得臃肿，反而看不清业务主线。
```

### 练习 4：用三层模型解释本项目

请补全下面内容：

```text
普通函数 / service 负责：
LangChain 负责：
LangGraph 负责：
```

参考答案：

```text
普通函数 / service 负责：查订单、创建工单、字段校验、权限边界、RAG 检索服务调用、错误处理。
LangChain 负责：模型调用、messages、tools、结构化输出、简单 agent harness。
LangGraph 负责：智能工单 Agent 的整体流程、state、node、edge、条件分支、暂停恢复、人工确认。
```

### 练习 5：判断 workflow 和 agent

请判断下面哪个更像 workflow，哪个更像 agent：

```text
A. 文档加载 -> 清洗 -> chunk -> embedding -> 写入向量库
B. 用户说一句自然语言，系统判断要查知识库、查订单还是创建工单，并根据后续对话继续推进
```

参考答案：

```text
A 更像 workflow，因为步骤顺序比较固定。
B 更像 agent，因为它需要理解自然语言，根据状态和上下文动态决定下一步。
```

### 练习 6：说出 LangChain 和 LangGraph 的关系

参考答案：

```text
LangChain 和 LangGraph 不是二选一。LangChain 更偏模型、工具、结构化输出和 agent harness；LangGraph 更偏有状态流程编排。LangChain 组件可以放在 LangGraph 节点里使用，LangGraph 也可以不依赖 LangChain 单独使用。
```

### 练习 7：为什么创建工单不能只靠 prompt 约束

参考答案：

```text
因为创建工单属于写操作或敏感业务动作。prompt 只能影响模型行为，不能作为可靠安全边界。是否允许创建、字段是否齐全、用户是否确认、权限是否满足，都必须由代码校验。LangGraph 可以把“确认后才能进入 create_ticket 节点”的流程显式化。
```

### 练习 8：给智能工单 Agent 设计几个节点

请列出至少 5 个你认为后面会用到的节点。

参考答案：

```text
classify_intent：识别用户意图
rag_answer：知识库问答
extract_ticket_fields：提取工单字段
check_missing_fields：检查缺失字段
ask_user_confirmation：请求用户确认
create_ticket：调用 Java mock API 创建工单
fallback：兜底回答
```

### 练习 9：一句话说清楚本节核心

参考答案：

```text
普通函数做好确定性业务动作，LangChain 接入模型和工具能力，LangGraph 负责把多步骤、有状态、可分支、可暂停恢复的 Agent 流程组织起来。
```

## 五、自测题与答案

### 自测 1：普通函数是不是落后的写法？

答案：

```text
不是。普通函数适合输入输出明确、规则稳定、容易测试的业务逻辑。真实项目里大量核心逻辑都应该保留普通函数或 service。
```

### 自测 2：LangChain 的核心定位是什么？

答案：

```text
LangChain 的核心定位是 LLM 应用组件层，常用于模型调用、消息组织、工具绑定、结构化输出、retriever、agent harness 等。
```

### 自测 3：LangGraph 的核心定位是什么？

答案：

```text
LangGraph 的核心定位是有状态 Agent / workflow 的流程编排运行时，适合多步骤、分支、暂停、恢复、人工介入和可观察的流程。
```

### 自测 4：LangGraph 是否一定依赖 LangChain？

答案：

```text
不一定。LangGraph 可以独立使用。但在 LLM 应用里，LangGraph 节点经常会调用 LangChain 的模型、工具和结构化输出能力。
```

### 自测 5：为什么智能工单 Agent 适合 LangGraph？

答案：

```text
因为它有意图识别、RAG 回答、字段提取、缺失字段追问、用户确认、Java API 调用、错误兜底和跨轮状态，属于多步骤、有状态、可分支、可能暂停恢复的 Agent 流程。
```

### 自测 6：什么是 node？

答案：

```text
node 是图里的一个步骤或动作，例如意图识别、RAG 回答、字段提取、创建工单。
```

### 自测 7：什么是 edge？

答案：

```text
edge 是节点之间的连接关系，表示一个节点执行完后下一步去哪。
```

### 自测 8：什么是 conditional edge？

答案：

```text
conditional edge 是条件边。它根据当前 state 判断下一步走哪个节点，例如根据 intent 走 RAG 回答还是工单流程。
```

### 自测 9：为什么敏感业务动作不能交给模型直接决定？

答案：

```text
因为模型输出不是可靠安全边界。创建工单、取消订单、退款等动作必须由代码做权限、字段、确认和幂等校验，模型只能辅助理解和表达。
```

### 自测 10：workflow 和 agent 的区别是什么？

答案：

```text
workflow 的路径通常由代码预先定义，步骤顺序比较确定；agent 更动态，模型可能根据任务状态决定过程和工具使用。
```

### 自测 11：为什么阶段 5 不应该推翻前面阶段的 service？

答案：

```text
因为 LangGraph 是编排层，不是替代业务能力层。前面阶段的 RAG、Java client、字段校验、用户确认等 service 仍然有价值，后面应该被 LangGraph 节点调用和组织。
```

### 自测 12：你如何向别人解释本项目的技术选型？

答案：

```text
本项目用 FastAPI 作为 AI 服务入口，用 LangChain 或已有 LLM client 接入模型、工具和结构化输出，用普通 service 封装 RAG、Java mock API 和确定性业务规则，用 LangGraph 编排智能工单 Agent 的多步骤状态流程，包括意图识别、知识库回答、字段提取、用户确认和创建工单。
```

## 六、本节小结

这一节没有写运行时代码，但它是阶段 5 的关键基础。

你需要真正记住的不是某个 API，而是这个判断标准：

```text
普通函数 / service：负责明确、稳定、可测试的业务动作。
LangChain：负责模型、消息、工具、结构化输出、agent harness 等 LLM 能力。
LangGraph：负责多步骤、有状态、可分支、可暂停恢复的 Agent / workflow 编排。
```

后面我们做智能工单 Agent 时，不会把所有东西都塞进 LangGraph。

我们会让每一层做它最擅长的事：

```text
FastAPI 接收请求。
LangGraph 管流程。
LangChain 管模型能力。
普通 service 管业务动作。
Java mock service 模拟真实业务系统。
RAG service 提供知识库回答。
Pydantic 和测试保护边界。
```

这就是阶段 5 后续代码设计的基础。

## 参考资料

- [LangGraph 官方 Overview](https://docs.langchain.com/oss/python/langgraph/overview)
  - 用途：确认 LangGraph 的定位，它是面向长流程、有状态 Agent 的低层编排框架和运行时。

- [LangGraph Quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart)
  - 用途：了解 Graph API、Functional API、state、node、edge、conditional edge 的基础写法。

- [LangGraph Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents)
  - 用途：理解 workflow 和 agent 的区别，以及常见流程编排模式。

- [LangChain 官方 Overview](https://docs.langchain.com/oss/python/langchain/overview)
  - 用途：确认 LangChain 在模型、工具、agent harness 和更高层 LLM 应用框架中的定位。

- [LangChain Agents](https://docs.langchain.com/oss/python/langchain/agents)
  - 用途：理解 agent loop、harness、tools、structured output 和 thread_id/checkpointer 等概念。
