# 阶段 5 第 1 节：LangGraph 是什么，为什么现在才学

## 本节定位

这一节正式进入阶段 5：LangGraph 智能工单 Agent。

阶段 5 不是换一个方向重新学，而是把前面四个阶段的能力串起来：

```text
FastAPI AI 服务
+ LLM API
+ Tool Calling
+ Java mock 业务服务
+ 用户确认机制
+ RAG 知识库
+ LangGraph 流程编排
= 智能工单 Agent v1
```

这一节先不急着写复杂代码，也不安装新依赖。

原因是 LangGraph 不是一个“背 API 就能会”的库。它背后的核心思想是：

```text
把 AI 应用里的多步骤流程，变成有状态、可分支、可中断、可恢复、可测试的图。
```

如果这个思想不懂，后面看到 `StateGraph`、`node`、`edge`、`conditional edge`、`checkpoint`、`interrupt` 就会变成死记硬背。

## 本节学习目标

学完这一节，你应该能做到：

1. 用自己的话解释 LangGraph 是什么。
2. 解释为什么 LangGraph 适合长流程、有状态、可人工介入的 Agent。
3. 解释 LangGraph 和 LangChain 的分工。
4. 解释为什么普通函数流程写到一定程度会变乱。
5. 解释为什么阶段 5 要在 Tool Calling 和 RAG 之后才学 LangGraph。
6. 解释智能工单 Agent 为什么适合用 LangGraph。
7. 初步认识 state、node、edge、conditional edge、START、END、checkpoint、thread_id、interrupt、human-in-the-loop。
8. 知道阶段 5 的 26 节将如何从概念走到项目。

## 本节先不学什么

为了把第一节基础打稳，本节暂时不做这些事：

1. 不安装 `langgraph`。
2. 不修改 `projects/ai-service` 运行时代码。
3. 不接入真实模型。
4. 不接入真实 RAG 检索。
5. 不接入 Java mock API。
6. 不讲 reducer 的代码细节。
7. 不讲 checkpoint 的具体存储实现。
8. 不讲 LangSmith tracing。

这些后面都会学。第一节先把“为什么要用 LangGraph”讲清楚。

## 一、基础知识铺垫

### 1. 先回顾：我们现在已经有什么

你现在不是从零开始学 LangGraph。

前面已经有这些能力：

```text
阶段 1：FastAPI 服务基础
阶段 2：LLM API 调用、messages、prompt、streaming、结构化输出
阶段 3：Tool Calling、Java mock API、用户确认、创建工单
阶段 4：RAG 知识库、Qdrant/Milvus、检索问答、安全、性能、评测
```

这些能力都能单独跑。

例如：

```text
用户问知识 -> RAG 可以回答
用户查订单 -> Tool Calling 可以调 Java mock API
用户要创建工单 -> 用户确认机制可以保护敏感操作
```

问题是：真实业务不会总是只走一条简单路径。

用户可能这样说：

```text
我的订单三天没发货，客服说要帮我建工单，你帮我处理一下。
```

这个请求里可能同时包含：

1. 识别用户意图。
2. 判断是不是订单问题。
3. 可能需要查知识库的发货规则。
4. 可能需要查订单状态。
5. 判断是否需要创建工单。
6. 提取工单字段。
7. 缺字段时追问用户。
8. 创建前让用户确认。
9. 确认后调用 Java API。
10. 返回工单号。
11. 记录 trace_id 和日志。
12. 如果中途用户离开，下次还能继续。

这已经不是一个简单 `/chat` 接口能优雅处理的事情。

### 2. 普通函数流程是什么

普通函数流程就是你自己写一段代码，把所有步骤按顺序调一遍。

伪代码可能像这样：

```python
def handle_user_message(message):
    intent = classify_intent(message)
    if intent == "knowledge_question":
        answer = rag_answer(message)
        return answer

    if intent == "create_ticket":
        fields = extract_ticket_fields(message)
        if missing_fields(fields):
            return ask_missing_fields(fields)
        confirmation = create_confirmation(fields)
        return confirmation

    if intent == "query_order":
        order = query_order(message)
        return summarize_order(order)
```

一开始这看起来很清楚。

但业务稍微复杂，就会出现：

1. `if/else` 越来越多。
2. 中间状态散落在局部变量里。
3. 用户第二次回复时，不知道上次流程停在哪里。
4. 节点失败后，不知道如何恢复。
5. 测试某个分支很麻烦。
6. 日志里看不清走过哪些步骤。
7. 人工确认、等待用户输入、中断恢复很难写得干净。

普通函数不是不能做，而是复杂到一定程度后会变成一团流程代码。

### 3. 什么是流程

流程就是一件事情从开始到结束，中间经过的一系列步骤。

比如创建工单流程：

```text
收到用户问题
-> 判断意图
-> 提取工单字段
-> 检查缺失字段
-> 追问用户
-> 用户补充
-> 再次检查
-> 创建确认计划
-> 用户确认
-> 调用 Java API 创建工单
-> 返回工单号
```

流程有几个特点：

1. 有开始。
2. 有结束。
3. 中间有多个步骤。
4. 每一步会读取已有信息。
5. 每一步可能写入新信息。
6. 某些步骤会决定下一步走哪条路。
7. 某些步骤可能暂停等待用户。
8. 某些步骤可能失败。

LangGraph 就是用“图”的方式描述这种流程。

### 4. 什么是图

图不是图片。

在编程和计算机科学里，图通常指：

```text
节点 + 边
```

节点表示一个个点。

边表示点和点之间的连接。

例如：

```text
START -> classify_intent -> rag_answer -> END
```

这里：

```text
START 是入口
classify_intent 是节点
rag_answer 是节点
END 是出口
箭头是边
```

如果流程有分支，就可能是：

```text
classify_intent
  -> rag_answer
  -> extract_ticket_fields
  -> query_order
```

图的好处是：

```text
每一步是什么、下一步去哪、哪里分支、哪里结束，都能被明确表达出来。
```

### 5. 什么是状态

状态就是流程运行到某一刻时，系统已经知道的全部重要信息。

例如智能工单 Agent 的状态里可能有：

```text
用户原始问题
当前意图
RAG 检索结果
RAG 回答
是否需要工单
工单字段
缺失字段
确认 ID
Java API 返回的工单号
错误信息
对话消息历史
trace_id
```

普通函数里，这些信息可能只是一些变量。

LangGraph 里，状态会被明确建模成一个结构：

```text
AgentState
```

每个节点都可以读取状态，并返回要更新的字段。

这就是 LangGraph 的核心之一：

```text
流程不是靠一堆局部变量隐式传递，而是围绕一个明确的 state 流动。
```

### 6. 什么是有状态

“有状态”表示系统记得之前发生过什么。

普通的一次性函数调用是：

```text
输入 -> 处理 -> 输出
```

处理完就结束。

有状态流程是：

```text
第一次输入 -> 保存状态 -> 暂停
第二次输入 -> 读取上次状态 -> 继续处理
```

智能工单很需要有状态。

比如用户第一次说：

```text
我要投诉订单一直没发货。
```

系统追问：

```text
请提供订单号。
```

用户第二次说：

```text
订单号是 1001。
```

系统必须知道：

```text
用户现在不是开启新聊天，而是在补充上一次创建工单流程缺失的 order_id。
```

这就需要状态。

### 7. 什么是 Agent

Agent 这个词容易被讲玄。

在我们当前项目里，可以先这样理解：

```text
Agent 是一个能根据当前任务和状态，决定下一步要做什么的 AI 工作流。
```

它不只是“模型回答一句话”。

它可能会：

1. 看用户问题。
2. 判断任务类型。
3. 查知识库。
4. 调工具。
5. 等用户确认。
6. 继续执行。
7. 输出最终结果。

官方 LangChain 文档里也把 agent 描述成“模型循环调用工具直到任务完成”的模式。我们阶段 5 不会一开始就做完全自由的 Agent，而是先做“可控流程型 Agent”。

也就是说：

```text
不是让模型想干什么就干什么，而是后端设计好节点和边，让模型只在受控位置做判断。
```

这点很重要。

### 8. 什么是可控 Agent

可控 Agent 的意思是：

```text
AI 可以参与判断和生成，但不能绕过后端流程边界。
```

比如创建工单：

模型可以帮忙提取字段：

```text
title
description
category
priority
related_order_id
```

但模型不能直接创建工单。

必须经过：

```text
后端字段校验
-> 用户确认
-> 幂等保护
-> Java API 调用
-> 日志记录
```

这和阶段 3 的原则一致：

```text
AI 不能直接操作业务系统。
```

LangGraph 不是让 AI 变得更“放飞”，而是让复杂 AI 流程更可控。

### 9. 为什么现在才学 LangGraph

如果一开始就学 LangGraph，你会遇到一个问题：

```text
图里每个节点要做什么，你还没有能力填进去。
```

LangGraph 是流程编排工具。

但流程里的节点需要已有能力支撑：

```text
意图识别节点 -> 需要 LLM API 和结构化输出基础
RAG 回答节点 -> 需要阶段 4 RAG 基础
订单查询节点 -> 需要阶段 3 Tool Calling 和 Java mock API
创建工单节点 -> 需要用户确认机制和 Java ticket API
错误处理节点 -> 需要前面统一异常和日志基础
测试图流程 -> 需要 fake LLM / fake tool / fake RAG 基础
```

所以现在学 LangGraph 正合适。

你已经有了节点需要调用的能力，现在要学的是：

```text
怎么把这些能力编排成一个可靠流程。
```

## 二、本节主题系统讲解

### 1. LangGraph 是什么

LangGraph 是 LangChain 生态里的低层编排框架和运行时。

你可以先这样记：

```text
LangGraph = 用图来编排有状态 Agent 流程的工具
```

更工程化一点说：

```text
LangGraph 负责把多个节点组织成一个可执行流程，并围绕 state 进行状态传递、分支控制、持久化、流式输出和人工介入。
```

它特别适合：

1. 多步骤任务。
2. 有分支的任务。
3. 需要保存中间状态的任务。
4. 可能运行较久的任务。
5. 需要暂停等待人的任务。
6. 需要失败后恢复的任务。
7. 需要观察每一步执行情况的任务。

这正好符合智能工单 Agent。

### 2. LangGraph 不是什么

为了避免误解，也要知道 LangGraph 不是什么。

LangGraph 不是：

```text
一个新的大模型
```

它不负责训练模型。

LangGraph 不是：

```text
一个向量数据库
```

它不替代 Qdrant 或 Milvus。

LangGraph 不是：

```text
一个 Java 业务系统
```

它不替代 Spring Boot、订单系统、工单系统。

LangGraph 不是：

```text
一个让 AI 自动乱点工具的魔法框架
```

它的价值恰恰是让流程边界更清楚。

LangGraph 也不是必须替代你之前写的代码。

更准确地说：

```text
LangGraph 会调用你已经写好的 service、RAG 模块、tool、Java client，把它们组织成流程。
```

### 3. LangChain 和 LangGraph 的区别

这是阶段 5 必须先搞清楚的点。

LangChain 更偏：

```text
模型、prompt、messages、tools、structured output、agent harness、retriever 等组件封装。
```

LangGraph 更偏：

```text
把多个步骤组织成有状态、可恢复、可分支、可人工介入的执行图。
```

简单对比：

| 对比点 | LangChain | LangGraph |
| --- | --- | --- |
| 主要定位 | LLM 应用组件和 agent harness | 低层流程编排和运行时 |
| 关注点 | model、prompt、tool、structured output、retriever | state、node、edge、branch、checkpoint、interrupt |
| 适合场景 | 单步或常见 agent loop | 长流程、多分支、有状态业务流程 |
| 是否必须一起用 | 可以单独用 | 可以单独用，也常和 LangChain 组件一起用 |
| 在当前项目里的角色 | 调模型、结构化输出、工具封装 | 编排智能工单 Agent 流程 |

一句话：

```text
LangChain 解决“每个 AI 组件怎么调用”。
LangGraph 解决“多个步骤怎么可靠地跑完整个流程”。
```

### 4. 为什么普通 service 不够

你可能会问：

```text
我自己写 Python service 函数，不也能编排流程吗？
```

可以。

小流程完全可以自己写。

但智能工单 Agent 会逐步遇到这些需求：

1. 多轮对话中继续上次流程。
2. 创建工单前暂停等待用户确认。
3. 根据模型分类结果走不同分支。
4. RAG 回答失败时走工单流程。
5. 工单字段缺失时追问用户。
6. 用户补充字段后回到字段检查。
7. Java API 调用失败时走 fallback。
8. 需要记录每个节点输入输出。
9. 测试每一条分支。
10. 未来支持流式展示节点进度。

自己写当然能写，但会变成大量手写流程控制。

LangGraph 给你的不是“少写几行代码”，而是一个更适合表达这些问题的结构。

### 5. LangGraph 的几个核心词

这一节先认识，不要求立刻写熟。

#### State

状态。

保存流程运行中的关键信息。

例如：

```text
user_message
intent
rag_answer
ticket_fields
missing_fields
confirmation_id
ticket_id
errors
messages
trace_id
```

#### StateGraph

基于 state 定义的图。

可以理解成：

```text
这个 Agent 流程的蓝图。
```

#### Node

节点。

流程中的一个处理步骤。

例如：

```text
classify_intent
answer_with_rag
extract_ticket_fields
ask_missing_fields
create_confirmation
create_ticket
```

#### Edge

边。

表示节点之间的流转关系。

例如：

```text
START -> classify_intent
classify_intent -> answer_with_rag
answer_with_rag -> END
```

#### Conditional Edge

条件边。

根据 state 决定下一步走哪里。

例如：

```text
如果 intent == "knowledge_question" -> answer_with_rag
如果 intent == "create_ticket" -> extract_ticket_fields
如果 intent == "query_order" -> query_order
```

#### START / END

图的开始和结束。

`START` 表示流程入口。

`END` 表示流程结束。

#### Checkpoint

检查点。

保存流程状态，让流程可以恢复。

例如用户确认前暂停：

```text
流程停在 waiting_for_confirmation
保存当前 state
用户确认后从这个 state 继续
```

#### thread_id

线程 ID，也可以理解成一次对话/任务的 ID。

它用于区分不同用户或不同会话的状态。

例如：

```text
thread_id = "user-1001-ticket-flow"
```

同一个 `thread_id` 可以继续同一个流程。

#### interrupt

中断。

让流程在某个节点暂停，等待外部输入。

创建工单前的用户确认就非常适合 interrupt。

#### human-in-the-loop

人在环路中。

意思是：

```text
流程不是全自动跑到底，而是在关键位置让人查看、确认、修改或拒绝。
```

智能工单 Agent 里，创建工单前必须 human-in-the-loop。

### 6. LangGraph 最小流程长什么样

本节不写项目代码，但你可以先看一个极简形状。

```python
from langgraph.graph import StateGraph, START, END


def classify_intent(state):
    return {"intent": "knowledge_question"}


def answer_with_rag(state):
    return {"answer": "这里是基于知识库的回答"}


graph_builder = StateGraph(dict)
graph_builder.add_node("classify_intent", classify_intent)
graph_builder.add_node("answer_with_rag", answer_with_rag)

graph_builder.add_edge(START, "classify_intent")
graph_builder.add_edge("classify_intent", "answer_with_rag")
graph_builder.add_edge("answer_with_rag", END)

graph = graph_builder.compile()
result = graph.invoke({"user_message": "退货运费谁承担？"})
```

这段代码先不用背。

只看结构：

```text
定义 state 类型
定义节点函数
把节点加入图
用边连接节点
compile 成可执行 graph
invoke 执行 graph
```

后面第 7 节才会真正写最小图。

### 7. 智能工单 Agent 为什么适合 LangGraph

智能工单不是普通聊天。

它天然有流程：

```text
用户问题
-> 意图识别
-> 查知识库
-> 判断能否直接回答
-> 工单字段提取
-> 缺失字段追问
-> 用户确认
-> 调 Java API 创建工单
-> 返回工单号
```

它天然有状态：

```text
intent
rag_result
ticket_fields
missing_fields
confirmation_id
ticket_id
```

它天然有分支：

```text
能直接回答 -> 回答后结束
不能回答但需要工单 -> 进入工单流程
字段缺失 -> 追问
字段完整 -> 等确认
用户拒绝 -> 结束
用户确认 -> 创建工单
```

它天然有人类介入：

```text
创建工单前必须确认
```

它天然需要恢复：

```text
用户补充字段或确认时，要回到上次流程继续
```

这些特点正是 LangGraph 的适用场景。

### 8. 阶段 5 的整体路线

阶段 5 固定按 26 节走。

可以分成四段。

第一段：基础认知。

```text
1. LangGraph 是什么
2. LangGraph 和 LangChain / 普通函数流程的区别
3. Agent 流程和状态机基础
```

第二段：LangGraph 基础结构。

```text
4. State
5. Reducer
6. MessagesState
7. StateGraph 最小图
8. node
9. edge
10. conditional edge
11. START / END
12. graph.invoke / graph.stream
```

第三段：智能工单业务流程。

```text
13. 总流程设计
14. 意图识别节点
15. RAG 知识库回答节点
16. 判断是否需要创建工单
17. 工单字段提取节点
18. 缺失字段追问节点
19. 用户确认节点
20. 调用 Java mock 创建工单节点
21. checkpoint 和 thread_id
22. interrupt / human-in-the-loop
```

第四段：工程补强和收尾。

```text
23. 节点错误处理、fallback 和流程兜底
24. LangGraph 日志、trace_id 和可观测性
25. LangGraph 测试
26. 阶段 5 项目整理和面试表达
```

### 9. 阶段 5 和阶段 6 的边界

阶段 5 目标是：

```text
把智能工单 Agent v1 做扎实。
```

阶段 5 不急着做：

```text
LangSmith tracing 深入
Agent 评测体系
Docker Compose
前端工作台
真实 Spring Boot 业务服务替换
线上监控
多 Agent 协作
长期记忆
```

这些放阶段 6 或后续增强。

为什么要分开？

因为如果阶段 5 一开始就塞太多生产化内容，你会看不清主线。

当前最重要的是：

```text
先把 Agent 流程跑通、讲透、测住。
```

## 三、对当前项目的意义

### 1. 以前的能力是零件

当前项目已经有很多零件：

```text
LLMChatService
LangChainChatModelService
ToolDecisionService
ToolCallingChatService
TicketWorkflowService
RAG retriever / generator
JavaOrderClient
JavaTicketClient
ToolConfirmationService
```

这些都是能力模块。

但 Agent 项目需要的是：

```text
把能力模块组织成一条完整业务流程。
```

LangGraph 接下来会成为这一层：

```text
app/agent 或 app/graphs
```

它不会替代已有模块，而是调用已有模块。

### 2. 智能工单 Agent 的第一版能力

阶段 5 做完后，理想的智能工单 Agent v1 应该能处理：

```text
用户问知识库能回答的问题
用户描述售后问题但资料不足
用户要求创建工单
用户字段说不全
用户补充字段
用户确认创建
Java mock API 返回工单号
流程日志可追踪
流程分支可测试
```

这比单纯 `/chat` 更接近真实 AI 应用。

### 3. 为什么对你的学习很关键

你前面已经学了不少“点”：

```text
FastAPI
Pydantic
LLM API
Tool Calling
RAG
Milvus/Qdrant
评测
```

阶段 5 开始训练的是“线”和“面”：

```text
一个真实业务问题来了，AI 系统应该怎么分步骤处理？
每一步由谁负责？
哪些步骤由模型参与？
哪些步骤必须由后端控制？
哪些状态要保存？
哪些分支要测试？
哪里要人工确认？
失败时怎么兜底？
```

这就是 AI 应用工程能力。

## 四、常见误区

### 误区 1：LangGraph 是 LangChain 的替代品

不准确。

LangChain 和 LangGraph 分工不同。

LangChain 更像组件库和 agent harness。

LangGraph 更像流程编排运行时。

当前项目后面会同时用它们：

```text
LangChain 调模型、结构化输出、工具封装
LangGraph 编排节点、状态、分支、中断恢复
```

### 误区 2：用了 LangGraph 就等于有了智能 Agent

不对。

LangGraph 只是编排工具。

真正的 Agent 质量来自：

1. 流程设计。
2. 状态设计。
3. 节点职责。
4. 模型 prompt。
5. 工具边界。
6. RAG 质量。
7. 用户确认。
8. 错误兜底。
9. 测试覆盖。

框架不能替你做业务设计。

### 误区 3：Agent 越自动越好

不对。

企业应用里，很多动作不能全自动。

比如：

```text
创建工单
退款
修改订单
审批
发送通知
```

这些动作必须有权限、确认、日志和幂等。

可控比炫技更重要。

### 误区 4：状态就是聊天记录

不完整。

聊天记录只是状态的一部分。

智能工单状态还包括：

```text
意图
RAG 结果
工单字段
缺失字段
确认状态
工具结果
错误信息
trace_id
```

后面第 4 节会重点讲 state。

### 误区 5：现在就应该接真实 RAG 和 Java 服务

不急。

阶段 5 前几节是基础结构。

先用 fake 节点理解图怎么跑，再接真实模块更稳。

否则你会同时被 LangGraph、RAG、Java API、模型调用、环境问题干扰。

## 五、本节最小示例：不用代码也能理解图

把智能工单最小流程画成文字：

```text
START
  |
  v
classify_intent
  |
  v
route_by_intent
  |----------------------|
  v                      v
answer_with_rag       extract_ticket_fields
  |                      |
  v                      v
END                  check_missing_fields
                         |
             |-----------|------------|
             v                        v
      ask_missing_fields        create_confirmation
             |                        |
             v                        v
           END              wait_for_user_confirm
                                      |
                                      v
                                create_ticket
                                      |
                                      v
                                     END
```

这里你先理解：

1. 每个名字都是一个节点。
2. 箭头是边。
3. `route_by_intent` 是条件分支。
4. 有些路径直接结束。
5. 有些路径需要追问。
6. 有些路径需要确认。
7. 确认后才能创建工单。

这就是 LangGraph 适合表达的东西。

## 六、本节练习与参考答案

### 练习 1：用一句话解释 LangGraph

题目：请用一句话解释 LangGraph 是什么。

参考答案：

LangGraph 是一个用图来编排有状态 Agent 流程的框架，它把复杂 AI 应用拆成 state、node、edge 和条件分支，并支持长流程、恢复、流式输出和人工介入。

### 练习 2：解释为什么现在才学 LangGraph

题目：为什么不在阶段 1 或阶段 2 就学 LangGraph？

参考答案：

因为 LangGraph 是流程编排工具，流程里的节点需要已有能力支撑。阶段 1-4 已经学了 FastAPI、LLM API、Tool Calling、Java mock API、用户确认和 RAG。现在这些能力都具备了，才适合学习如何把它们编排成智能工单 Agent。

### 练习 3：区分 LangChain 和 LangGraph

题目：LangChain 和 LangGraph 的主要区别是什么？

参考答案：

LangChain 更偏模型、prompt、messages、tools、structured output、retriever 和 agent harness 等组件封装；LangGraph 更偏把多个步骤组织成有状态、可分支、可恢复、可人工介入的执行图。

### 练习 4：解释 state

题目：在智能工单 Agent 里，state 可能保存哪些信息？

参考答案：

可能保存用户原始问题、对话消息、意图、RAG 检索结果、RAG 回答、是否需要创建工单、工单字段、缺失字段、确认 ID、Java API 返回的工单号、错误信息和 trace_id。

### 练习 5：解释 node

题目：什么是 node？请举 3 个智能工单 Agent 里的 node。

参考答案：

node 是流程中的一个处理步骤。智能工单 Agent 里的 node 可以是 `classify_intent`、`answer_with_rag`、`extract_ticket_fields`、`create_ticket`。

### 练习 6：解释 conditional edge

题目：为什么智能工单 Agent 需要 conditional edge？

参考答案：

因为用户问题可能走不同路径。知识类问题可以走 RAG 回答并结束；创建工单类问题需要提取字段、确认和调用 Java API；字段缺失时需要追问。下一步取决于 state，所以需要条件分支。

### 练习 7：解释 human-in-the-loop

题目：为什么创建工单前需要 human-in-the-loop？

参考答案：

创建工单是业务写操作，不能让模型直接执行。必须让用户或操作人确认字段和动作，再由后端执行 Java API 调用，这样才能保证安全、审计和责任边界。

### 练习 8：判断 LangGraph 是否替代 RAG

题目：LangGraph 会替代阶段 4 的 RAG 模块吗？

参考答案：

不会。LangGraph 不负责向量检索或知识库回答，它会把 RAG 模块作为一个节点或服务调用，编排到智能工单流程里。

### 练习 9：判断 LangGraph 是否替代 Java 后端

题目：LangGraph 会替代 Java mock 业务服务吗？

参考答案：

不会。Java 后端仍负责业务数据和写操作。LangGraph 只是在 Python AI 服务里编排流程，真正查询订单或创建工单仍然通过受控的 Java API。

### 练习 10：画出一个最小智能工单图

题目：写出一个最小智能工单流程图，用文字箭头即可。

参考答案：

```text
START
-> classify_intent
-> extract_ticket_fields
-> create_confirmation
-> wait_for_user_confirm
-> create_ticket
-> END
```

## 七、自测题与答案

### 自测 1

问题：LangGraph 的核心价值是什么？

答案：把复杂 AI 流程拆成有状态的图，让流程具备清晰节点、分支、状态传递、中断恢复、流式观察和人工介入能力。

### 自测 2

问题：为什么普通函数流程在智能工单 Agent 里会逐渐变乱？

答案：因为智能工单包含多分支、多轮对话、字段追问、用户确认、工具调用、失败兜底和状态恢复。全部写在普通函数里会导致 `if/else` 复杂、状态分散、恢复困难和测试困难。

### 自测 3

问题：Agent 是不是等于完全自动？

答案：不是。企业 Agent 应该是可控的，模型可以参与判断和生成，但敏感动作必须由后端权限、确认、幂等和日志控制。

### 自测 4

问题：state 和 messages 是一回事吗？

答案：不是。messages 是对话消息历史，state 是整个流程的状态，除了 messages 还可能包含意图、RAG 结果、工单字段、确认 ID、错误信息和 trace_id。

### 自测 5

问题：node 的职责应该大还是小？

答案：应该尽量单一。一个节点最好负责一个明确步骤，例如意图识别、RAG 回答、字段提取、用户确认或创建工单。

### 自测 6

问题：edge 的作用是什么？

答案：edge 用来连接节点，表示流程从一个节点执行完后应该进入哪个节点。

### 自测 7

问题：conditional edge 和普通 edge 有什么区别？

答案：普通 edge 是固定流转，conditional edge 会根据 state 中的信息决定下一步走哪个节点。

### 自测 8

问题：checkpoint 解决什么问题？

答案：checkpoint 保存流程状态，让长流程可以在失败、暂停或等待用户输入后继续执行。

### 自测 9

问题：thread_id 的直观作用是什么？

答案：thread_id 用来标识一次对话或任务，让系统知道后续输入应该接着哪一个流程状态继续。

### 自测 10

问题：阶段 5 为什么不一开始就做 LangSmith tracing、Docker Compose、前端工作台？

答案：因为阶段 5 主线是先把智能工单 Agent v1 的流程跑通、讲透、测住。LangSmith tracing、Docker Compose、前端工作台属于更生产化的增强，放到阶段 6 更清晰。

### 自测 11

问题：LangGraph 会如何使用阶段 3 的 Tool Calling 能力？

答案：LangGraph 可以把工具调用或 Java API 调用封装成节点，例如查询订单节点、创建工单节点，让它们在受控流程中执行。

### 自测 12

问题：LangGraph 会如何使用阶段 4 的 RAG 能力？

答案：LangGraph 可以把 RAG 检索回答封装成节点，当用户问题适合知识库回答时，先调用 RAG 节点返回带出处的回答；如果不能解决，再进入工单流程。

## 八、本节小结

这一节最重要的结论是：

```text
LangGraph 不是新的模型，也不是新的向量库，而是用图来编排有状态 Agent 流程的工具。
```

阶段 5 之所以现在开始，是因为你已经有了足够的“节点能力”：

```text
LLM 调用
结构化输出
Tool Calling
Java mock API
用户确认
RAG 知识库
测试 fake
日志和 trace_id
```

接下来要学的是：

```text
如何把这些能力组织成一个可控、可恢复、可测试的智能工单 Agent。
```

下一节会继续讲：

```text
阶段 5 第 2 节：LangGraph 和 LangChain / 普通函数流程的区别
```

那一节会更系统地比较：

```text
普通函数编排
LangChain chain / agent harness
LangGraph state graph
```

## 参考资料

- [LangGraph 官方 Overview](https://docs.langchain.com/oss/python/langgraph/overview)
- [LangGraph Quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart)
- [LangGraph Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents)
- [LangChain Overview](https://docs.langchain.com/oss/python/langchain/overview)
- [LangChain Agents](https://docs.langchain.com/oss/python/langchain/agents)
