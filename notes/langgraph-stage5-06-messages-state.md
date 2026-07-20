# 阶段 5 第 6 节：MessagesState：多轮对话消息怎么保存

## 本节定位

前两节我们连续学习了两个关键概念：

```text
第 4 节：State 是什么：Agent 为什么需要状态
第 5 节：Reducer 是什么：状态字段怎么合并
```

你已经知道：

```text
State 是 Agent 的结构化工作记忆。
reducer 决定 State 字段的新旧值怎么合并。
```

这一节专门讲 State 里最特殊、最容易混淆的字段：

```text
messages
```

为什么它特殊？

因为 `messages` 同时承担几件事：

```text
1. 它是模型理解多轮对话的上下文。
2. 它保存用户、AI、工具结果之间的交互轨迹。
3. 它通常需要追加，而不是覆盖。
4. 它可能包含 HumanMessage、AIMessage、SystemMessage、ToolMessage。
5. 它不只是普通 list，因为消息可能有 id、tool_calls、usage_metadata、response_metadata。
6. 它太长时会带来 token 成本和上下文窗口问题。
```

LangGraph 提供了两个重要工具来处理它：

```text
add_messages
MessagesState
```

本节目标不是让你死记 API，而是讲清楚：

```text
为什么多轮 Agent 需要 messages？
为什么 messages 不能只用 user_message 代替？
为什么 messages 不能简单覆盖？
为什么 operator.add 还不够？
为什么 LangGraph 要提供 add_messages / MessagesState？
```

## 本节学习目标

学完这一节，你应该能做到：

1. 解释 messages 是什么。
2. 解释 message 和普通字符串的区别。
3. 解释 `user_message` 和 `messages` 的区别。
4. 解释 `SystemMessage`、`HumanMessage`、`AIMessage`、`ToolMessage` 分别是什么。
5. 解释为什么多轮对话需要保存消息历史。
6. 解释为什么 `messages` 字段不能默认覆盖。
7. 解释 `operator.add` 追加 messages 的局限。
8. 解释 `add_messages` 解决什么问题。
9. 解释 `MessagesState` 是什么。
10. 解释 `MessagesState` 和自定义 `TicketAgentState` 怎么结合。
11. 解释 messages 和结构化 State 的分工。
12. 解释消息历史过长时会有什么问题。
13. 说明智能工单 Agent 里哪些信息应该放 messages，哪些应该放结构化字段。

## 本节先不学什么

为了把 messages 讲清楚，本节暂时不做这些事：

1. 不安装 `langgraph`。
2. 不修改 `projects/ai-service` 的运行时代码。
3. 不实现 `StateGraph` 最小图。
4. 不真实调用模型。
5. 不写 ToolMessage 的完整工具调用链路。
6. 不讲 checkpoint 代码实现。
7. 不讲消息裁剪和总结的完整工程实现。
8. 不启动 Qdrant 或 Milvus。

这些后面会逐步进入。

本节只解决一个核心问题：

```text
多轮 Agent 的消息历史应该怎么理解和保存？
```

## 一、基础知识铺垫

### 1. 先从单轮对话说起

单轮对话很简单。

例如：

```text
用户：订单 1001 发货了吗？
AI：订单 1001 还未发货。
```

如果只是这一轮，代码可能只需要一个字段：

```python
user_message = "订单 1001 发货了吗？"
```

然后把它交给模型或业务逻辑处理。

这种场景里，`user_message` 足够。

### 2. 多轮对话为什么不够

多轮对话就不一样了。

例如：

```text
第 1 轮
用户：订单 1001 一直没发货，帮我处理一下。
AI：我可以帮你创建工单，请确认是否创建。

第 2 轮
用户：确认。
AI：已为你创建工单 T-2026-0001。
```

第二轮用户只说了：

```text
确认
```

如果系统只看当前 `user_message`，它不知道：

```text
确认什么？
确认创建工单？
确认退款？
确认取消订单？
确认改地址？
```

所以多轮对话必须保存历史。

这份历史在 LLM 应用里通常就是：

```text
messages
```

### 3. messages 是什么

`messages` 是一组消息。

它按顺序记录对话里发生过的内容：

```text
system: 你是客服助手，创建工单前必须确认
human: 订单 1001 一直没发货，帮我处理一下
ai: 我可以帮你创建工单，请确认是否创建
human: 确认
ai: 已为你创建工单 T-2026-0001
```

在 LangChain 里，messages 不是随便的字符串列表。

它通常是 message 对象列表：

```python
[
    SystemMessage(content="你是客服助手，创建工单前必须确认"),
    HumanMessage(content="订单 1001 一直没发货，帮我处理一下"),
    AIMessage(content="我可以帮你创建工单，请确认是否创建"),
    HumanMessage(content="确认"),
]
```

也可以从 OpenAI 风格 dict 输入转换而来：

```python
[
    {"role": "system", "content": "你是客服助手"},
    {"role": "user", "content": "订单 1001 没发货"},
]
```

### 4. message 和普通字符串有什么区别

普通字符串只有内容：

```text
订单 1001 没发货
```

message 对象除了内容，还包含角色和元数据：

```text
role：谁说的，system/user/assistant/tool
content：说了什么
id：消息 ID
tool_calls：AI 请求调用哪些工具
usage_metadata：token 使用情况
response_metadata：模型供应商返回的元信息
```

这就是为什么 message 比普通字符串更适合模型对话。

模型不只是需要文字。

它还需要知道：

```text
这句话是系统指令，还是用户输入？
这句话是 AI 上次回答，还是工具结果？
这个 tool result 对应哪个 tool call？
```

### 5. role 为什么重要

同一句话，不同 role 的含义完全不同。

例如：

```text
创建工单前必须确认用户。
```

如果它是 system message：

```text
这是系统规则，模型应该遵守。
```

如果它是 human message：

```text
这是用户说的一句话，不一定是系统规则。
```

如果它是 assistant message：

```text
这是 AI 曾经说过的话。
```

如果它是 tool message：

```text
这是工具执行后的结果，不是用户或 AI 自然表达。
```

所以消息的 role 很关键。

### 6. SystemMessage 是什么

`SystemMessage` 表示系统指令。

它通常告诉模型：

```text
你是谁？
你要遵守什么规则？
回答风格是什么？
不能做什么？
遇到敏感操作怎么处理？
```

例如智能工单 Agent 可能有系统指令：

```text
你是客服助手。
回答必须使用中文。
创建工单前必须请求用户确认。
不能编造知识库里没有的信息。
```

SystemMessage 通常不会每一轮都由用户输入。

它是应用开发者给模型的行为约束。

### 7. HumanMessage 是什么

`HumanMessage` 表示用户输入。

例如：

```text
订单 1001 一直没发货，帮我处理一下。
```

或：

```text
确认。
```

HumanMessage 是模型最需要理解的当前任务来源。

但它不一定只包含纯文本。

官方文档里也说明，HumanMessage 可以包含文本、图片、音频、文件等多模态内容。

我们当前项目先只学文本。

### 8. AIMessage 是什么

`AIMessage` 表示模型输出。

它可能只是普通回答：

```text
我可以帮你创建工单，请确认是否创建。
```

也可能包含 tool calls。

例如模型说：

```text
我要调用 query_order 工具，参数是 order_id=1001。
```

在 LangChain message 对象里，这种工具调用不是一段普通文本，而是结构化的 `tool_calls`。

这对 Tool Calling 很重要。

### 9. ToolMessage 是什么

`ToolMessage` 表示工具执行结果。

比如模型请求调用：

```text
query_order(order_id="1001")
```

后端执行工具后，得到结果：

```json
{
  "order_id": "1001",
  "status": "not_shipped"
}
```

这个结果要作为 ToolMessage 放回 messages。

这样模型下一次调用时就能看到：

```text
工具已经查到了订单状态。
```

ToolMessage 必须和前面的 tool call 对上。

通常要通过 `tool_call_id` 关联。

### 10. messages 和 Tool Calling 的关系

Tool Calling 本质上不是模型直接调用工具。

更准确地说：

```text
模型在 AIMessage 里提出 tool call。
后端执行工具。
后端把工具结果作为 ToolMessage 放回 messages。
模型基于新的 messages 继续生成回答。
```

流程类似：

```text
HumanMessage: 用户问订单 1001
AIMessage: 请求 query_order 工具
ToolMessage: query_order 返回订单未发货
AIMessage: 根据工具结果总结中文回答
```

所以 messages 是工具调用链路的上下文载体。

### 11. user_message 和 messages 的区别

`user_message` 表示当前轮用户输入。

例如：

```text
确认
```

`messages` 表示完整对话历史。

例如：

```text
HumanMessage: 订单 1001 一直没发货
AIMessage: 我可以帮你创建工单，请确认
HumanMessage: 确认
```

两者关系：

```text
user_message 是当前轮。
messages 是多轮历史。
当前 user_message 通常会变成一条 HumanMessage 追加进 messages。
```

不要把这两个字段混为一谈。

### 12. messages 和结构化 State 的区别

上一节我们已经讲过，State 里不仅有 messages。

例如智能工单 Agent 的结构化 State 还可能有：

```text
intent
ticket_fields
missing_fields
confirmation_status
ticket_id
final_answer
error
trace_id
```

messages 更适合给模型理解上下文。

结构化字段更适合给代码做可靠判断。

例如用户说：

```text
确认
```

messages 可以帮助模型理解上下文。

但代码真正判断是否能创建工单，应该看：

```text
confirmation_status == "confirmed"
missing_fields == []
ticket_fields 不为空
```

### 13. 为什么不能只靠 messages

只靠 messages 会有几个问题。

第一个问题：代码难判断。

如果你要判断用户是否已确认，只能让模型读历史推断。

这不够稳定。

第二个问题：测试不稳定。

你很难写一个确定测试：

```text
messages 里有一堆自然语言，所以应该创建工单。
```

结构化 State 更好断言：

```python
assert state["confirmation_status"] == "confirmed"
```

第三个问题：安全边界弱。

创建工单、退款、取消订单这类动作不能只靠模型读 messages 决定。

第四个问题：上下文长度有限。

messages 太长会超出模型上下文窗口。

如果重要状态只在很早的 messages 里，后面裁剪历史时可能丢失。

所以：

```text
messages 是模型上下文。
结构化 State 是业务控制。
两者必须配合。
```

### 14. 为什么不能没有 messages

反过来，也不能只要结构化 State，不要 messages。

因为模型需要理解自然语言上下文。

例如：

```text
用户：我前面说的那个问题，帮我再写详细点。
```

如果没有 messages，模型不知道“前面说的那个问题”是什么。

再例如：

```text
用户：把语气放缓一点。
```

这也依赖前面的 AIMessage。

所以：

```text
结构化 State 不能完全替代 messages。
messages 也不能完全替代结构化 State。
```

### 15. messages 为什么需要 reducer

`messages` 是 State 里的字段。

节点会不断返回新的消息更新。

例如：

```python
return {"messages": [HumanMessage(content="订单 1001 没发货")]}
```

另一个节点：

```python
return {"messages": [AIMessage(content="我可以帮你创建工单，请确认")]}
```

如果没有 reducer，默认覆盖。

结果旧消息会丢。

所以 `messages` 必须有合并规则。

第 5 节我们学过：

```text
默认覆盖。
operator.add 可以追加列表。
add_messages 更适合 messages。
```

本节就继续讲这个区别。

## 二、本节主题系统讲解

### 1. 用 operator.add 保存 messages 的方式

上一节学过：

```python
from operator import add
from typing import Annotated
from typing_extensions import TypedDict

class State(TypedDict):
    messages: Annotated[list, add]
```

这表示：

```text
messages 字段用列表拼接方式合并。
```

旧 messages：

```python
[
    HumanMessage(content="订单 1001 没发货")
]
```

节点返回：

```python
[
    AIMessage(content="我可以帮你创建工单，请确认")
]
```

合并后：

```python
[
    HumanMessage(content="订单 1001 没发货"),
    AIMessage(content="我可以帮你创建工单，请确认"),
]
```

这比覆盖好。

但还不够。

### 2. operator.add 的局限

`operator.add` 对列表只是简单拼接。

它不知道什么是 message。

它不会看 message id。

它不会更新已有 message。

它也不会帮你把 dict 转成 LangChain Message 对象。

例如：

```python
old_messages = [
    AIMessage(content="草稿回答", id="msg_1")
]

new_messages = [
    AIMessage(content="修改后的回答", id="msg_1")
]
```

如果用 `operator.add`，结果是：

```python
[
    AIMessage(content="草稿回答", id="msg_1"),
    AIMessage(content="修改后的回答", id="msg_1"),
]
```

但有时你想要的是：

```python
[
    AIMessage(content="修改后的回答", id="msg_1")
]
```

也就是按 id 更新已有消息。

### 3. 为什么会需要更新已有消息

初学时你可能会问：

```text
消息历史不是一直追加吗？为什么还要更新已有消息？
```

有几个真实场景。

第一，human-in-the-loop。

人工可能要修改模型某条回答。

第二，纠正工具结果。

某个 ToolMessage 可能需要被人工或系统修正。

第三，流式输出或中间消息。

先生成一个临时消息，后面补全或替换。

第四，状态回放和调试。

你可能需要修正某条历史消息再继续执行。

这时简单追加会导致历史里出现两条同 id 消息。

### 4. add_messages 是什么

`add_messages` 是 LangGraph 预置的 messages reducer。

它主要做两件事：

```text
1. 对新消息做追加。
2. 如果新消息和旧消息有相同 id，则更新已有消息，而不是简单追加。
```

此外，官方文档还说明它会尝试把收到的消息反序列化成 LangChain Message 对象。

也就是说，下面两种输入都可以支持：

```python
{"messages": [HumanMessage(content="你好")]}
```

以及：

```python
{"messages": [{"type": "human", "content": "你好"}]}
```

使用 `add_messages` 后，读取消息时通常用对象属性：

```python
state["messages"][-1].content
```

### 5. add_messages 和 operator.add 的区别

| 维度 | operator.add | add_messages |
| --- | --- | --- |
| 本质 | 普通列表拼接 | 专门处理 LangChain messages 的 reducer |
| 新消息 | 追加 | 追加 |
| 同 id 消息 | 继续追加，可能重复 | 更新已有消息 |
| dict 输入 | 不会自动变 Message 对象 | 会尝试反序列化 |
| 适合场景 | 简单列表日志、节点历史 | messages 字段 |
| 对消息语义的理解 | 没有 | 有 |

所以：

```text
普通列表可以用 operator.add。
messages 字段更适合用 add_messages。
```

### 6. MessagesState 是什么

`MessagesState` 是 LangGraph 提供的预置 State。

它可以理解成：

```text
一个已经帮你定义好 messages 字段和 add_messages reducer 的 State。
```

官方文档里说明：

```text
MessagesState 有一个 messages key。
这个 key 是 AnyMessage 列表。
它使用 add_messages reducer。
```

也就是说，下面这种写法：

```python
from langchain.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing import Annotated
from typing_extensions import TypedDict

class GraphState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
```

可以简化成：

```python
from langgraph.graph import MessagesState

class State(MessagesState):
    pass
```

### 7. 为什么 MessagesState 常被继承

真实 Agent 通常不只有 messages。

智能工单 Agent 还需要：

```text
intent
ticket_fields
missing_fields
confirmation_status
ticket_id
error
trace_id
```

所以常见写法是继承 `MessagesState`，再加自己的字段：

```python
from typing import Literal
from langgraph.graph import MessagesState

class TicketAgentState(MessagesState):
    intent: Literal["rag_question", "create_ticket", "unknown"]
    ticket_fields: dict
    missing_fields: list[str]
    confirmation_status: Literal["none", "waiting", "confirmed", "rejected"]
    final_answer: str
```

学习阶段你可以理解成：

```text
MessagesState 解决 messages 字段。
TicketAgentState 增加业务字段。
```

### 8. MessagesState 和自定义 State 怎么选

如果你的图只需要保存消息历史，可以直接用：

```python
MessagesState
```

如果你的图还需要业务字段，可以：

```text
继承 MessagesState，然后添加字段。
```

如果你想完全自己控制，也可以显式写：

```python
messages: Annotated[list[AnyMessage], add_messages]
```

三种都可以。

对我们后面智能工单 Agent 来说，更适合：

```text
继承 MessagesState + 增加结构化业务字段
```

因为我们既需要多轮消息，又需要可靠业务控制。

### 9. messages 在节点里怎么使用

一个模型节点通常会读 messages：

```python
def call_model(state: State):
    response = model.invoke(state["messages"])
    return {"messages": [response]}
```

这段逻辑表达的是：

```text
把当前消息历史发给模型。
模型返回一条 AIMessage。
把这条 AIMessage 追加回 messages。
```

注意节点返回的是：

```python
{"messages": [response]}
```

不是：

```python
{"messages": state["messages"] + [response]}
```

因为合并这件事应该交给 reducer。

### 10. 用户输入怎么进入 messages

用户输入通常会作为 `HumanMessage` 进入 messages。

例如：

```python
return {"messages": [HumanMessage(content=state["user_message"])]}
```

或者调用图时直接传：

```python
graph.invoke({
    "messages": [{"role": "user", "content": "订单 1001 没发货"}]
})
```

使用 `add_messages` 时，dict 输入也可以被反序列化成 Message 对象。

### 11. 系统指令放哪里

SystemMessage 有两种常见处理方式。

第一种：每次模型调用前临时构造。

```python
messages = [
    SystemMessage(content="你是客服助手，创建工单前必须确认"),
    *state["messages"],
]
response = model.invoke(messages)
```

第二种：把 SystemMessage 也放进 state["messages"]。

这两种都能用。

学习阶段更推荐先理解第一种：

```text
系统规则是应用配置和模型调用策略。
对话历史主要保存用户、AI、工具之间发生过的交互。
```

真实项目里怎么做，要看是否需要 checkpoint 中保存完整模型上下文。

### 12. ToolMessage 为什么要保存

如果 Agent 使用工具，ToolMessage 很关键。

例如：

```text
用户：查一下订单 1001
AIMessage：请求调用 query_order
ToolMessage：query_order 返回未发货
AIMessage：订单 1001 还未发货
```

如果不保存 ToolMessage，模型下一次就不知道工具结果。

尤其是工具调用链路里：

```text
AIMessage 的 tool call id
ToolMessage 的 tool_call_id
```

必须对应。

这是模型理解工具结果的基础。

### 13. messages 和 final_answer 的区别

`final_answer` 是结构化 State 里的输出字段。

例如：

```text
已为你创建工单 T-2026-0001。
```

`messages` 里可能也有一条 AIMessage，内容同样是这句话。

这两个字段可以同时存在。

区别是：

```text
messages：给模型和对话历史使用。
final_answer：给 API 响应、测试断言、前端展示使用。
```

有些项目只从最后一条 AIMessage 取回答。

有些项目会额外保存 `final_answer`。

我们的学习项目里，保留 `final_answer` 有助于测试和理解。

### 14. messages 和 trace_id 的关系

`trace_id` 不应该混进 messages 内容里。

不要让 AIMessage 里写：

```text
[trace_id=abc] 已为你创建工单
```

trace_id 是系统追踪字段。

它应该放在结构化 State 或日志上下文里。

messages 主要给模型看。

如果把太多系统调试信息塞进 messages，会污染模型上下文。

### 15. messages 太长会怎样

messages 会被发给模型。

如果历史太长，会带来问题：

```text
token 成本增加
响应变慢
超出上下文窗口
模型被无关历史干扰
隐私风险增加
```

所以真实项目会做：

```text
裁剪历史
总结历史
只保留最近 N 轮
把长期事实放入结构化 State 或长期记忆
把工具原始大结果放 artifact，不全部塞 content
```

本节只讲基础。

后续生产化阶段会再补上下文管理和评测。

## 三、MessagesState 和智能工单 Agent 的关系

### 1. 智能工单 Agent 为什么需要 messages

智能工单 Agent 至少需要理解这些多轮表达：

```text
用户：订单 1001 没发货，帮我处理一下。
AI：可以创建工单，请确认。
用户：确认。
```

再例如：

```text
用户：退款多久到账？
AI：根据知识库，退款一般 3-5 个工作日到账。
用户：那如果超过 5 天呢？
```

第二轮的“超过 5 天”依赖上一轮问题。

没有 messages，模型不知道它在问退款到账。

### 2. 智能工单 Agent 为什么还需要结构化 State

但 messages 不够。

创建工单前，代码必须判断：

```text
ticket_fields 是否齐全
confirmation_status 是否 confirmed
用户是否有权限
是否已经创建过同一个工单
```

这些不能只靠模型读 messages 推断。

所以智能工单 Agent 会同时有：

```text
messages：对话上下文
ticket_fields：工单草稿
missing_fields：缺失字段
confirmation_status：确认状态
ticket_id：创建结果
error：错误信息
```

### 3. 一轮创建工单流程里的 messages

假设用户说：

```text
订单 1001 一直没发货，帮我处理一下。
```

messages 可能变成：

```text
HumanMessage: 订单 1001 一直没发货，帮我处理一下。
AIMessage: 我可以为你创建工单，请确认是否创建。
```

结构化 State 可能是：

```json
{
  "intent": "create_ticket",
  "ticket_fields": {
    "title": "订单未发货",
    "order_id": "1001",
    "priority": "normal"
  },
  "missing_fields": [],
  "confirmation_status": "waiting"
}
```

这两份信息一起工作。

### 4. 第二轮确认时的 messages

用户说：

```text
确认
```

messages 追加：

```text
HumanMessage: 确认
```

结构化 State 更新：

```json
{
  "confirmation_status": "confirmed"
}
```

然后流程才允许进入：

```text
create_ticket
```

### 5. 创建工单后的 messages

Java mock API 创建成功：

```json
{
  "ticket_id": "T-2026-0001"
}
```

最终 AIMessage：

```text
已为你创建工单 T-2026-0001。
```

结构化 State：

```json
{
  "ticket_id": "T-2026-0001",
  "final_answer": "已为你创建工单 T-2026-0001。"
}
```

messages 记录对话。

State 记录业务结果。

### 6. RAG 回答里的 messages

用户问：

```text
退款多久到账？
```

RAG 节点可能检索到：

```text
refund-return-policy.md
```

模型回答：

```text
根据退款退货规则，退款通常在 3-5 个工作日到账。
```

messages 保存：

```text
HumanMessage: 退款多久到账？
AIMessage: 根据退款退货规则，退款通常在 3-5 个工作日到账。
```

结构化 State 保存：

```json
{
  "intent": "rag_question",
  "rag_answer": "根据退款退货规则，退款通常在 3-5 个工作日到账。",
  "retrieved_sources": [
    {"source": "refund-return-policy.md"}
  ]
}
```

后续用户问：

```text
那超过 5 天呢？
```

模型靠 messages 理解上下文。

代码靠结构化 State 知道上轮是 RAG 问题和引用来源。

### 7. Tool Calling 里的 messages

后面智能工单 Agent 会继续用工具调用思想。

例如：

```text
HumanMessage: 查一下订单 1001
AIMessage: tool_calls=[query_order(order_id="1001")]
ToolMessage: {"status": "not_shipped"}
AIMessage: 订单 1001 还未发货
```

如果 ToolMessage 不放回 messages，模型无法基于工具结果继续回答。

所以 messages 是模型工具链的记录。

但工具返回的完整原始结果不一定都塞到 message content。

有些可以放：

```text
ToolMessage.artifact
结构化 State
日志
```

### 8. messages 和用户确认的边界

用户确认既要进入 messages，也要进入结构化 State。

进入 messages 是为了：

```text
模型知道用户说过“确认”。
对话历史完整。
```

进入结构化 State 是为了：

```text
代码能判断允许 create_ticket。
测试能断言 confirmation_status。
checkpoint 能恢复确认状态。
```

不要只做其中一个。

### 9. messages 不应该承载所有业务字段

不要把业务状态只写成自然语言塞进 AIMessage：

```text
当前工单字段：title=订单未发货，priority=normal，确认状态=waiting
```

这可以作为给用户的确认文案。

但真正的业务字段应该结构化保存：

```json
{
  "ticket_fields": {
    "title": "订单未发货",
    "priority": "normal"
  },
  "confirmation_status": "waiting"
}
```

### 10. messages 不应该塞太多系统内部信息

不要把这些都塞进 messages：

```text
trace_id
完整 HTTP 请求头
内部异常堆栈
数据库连接信息
完整 Java API 原始响应
API Key
```

这些会污染模型上下文，也可能带来安全风险。

messages 里的内容应该是模型确实需要理解和生成回答的信息。

## 四、学习版代码示例

### 1. 显式写 messages 字段

学习示例：

```python
from typing import Annotated
from typing_extensions import TypedDict
from langchain.messages import AnyMessage
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
```

意思是：

```text
State 里有 messages 字段。
messages 是 AnyMessage 列表。
这个字段用 add_messages 合并。
```

### 2. 使用 MessagesState

等价的简化写法：

```python
from langgraph.graph import MessagesState

class State(MessagesState):
    pass
```

这表示：

```text
State 已经带有 messages 字段和 add_messages reducer。
```

### 3. 继承 MessagesState 添加业务字段

智能工单 Agent 更可能这样：

```python
from typing import Literal
from langgraph.graph import MessagesState

class TicketAgentState(MessagesState):
    intent: Literal["rag_question", "create_ticket", "unknown"]
    ticket_fields: dict
    missing_fields: list[str]
    confirmation_status: Literal["none", "waiting", "confirmed", "rejected"]
    final_answer: str
```

意思是：

```text
messages 交给 MessagesState。
业务状态字段自己定义。
```

### 4. 模型节点返回 AIMessage

学习示例：

```python
def call_model(state: TicketAgentState):
    response = model.invoke(state["messages"])
    return {"messages": [response]}
```

注意：

```text
返回的是新增消息。
不是完整 messages。
add_messages 负责合并。
```

### 5. 用户输入追加 HumanMessage

学习示例：

```python
from langchain.messages import HumanMessage

def add_user_message(state: TicketAgentState):
    return {"messages": [HumanMessage(content=state["user_message"])]}
```

这表示：

```text
把当前轮 user_message 转成 HumanMessage，追加到 messages。
```

### 6. 读取最后一条消息

使用 `add_messages` 后，消息会被反序列化成 LangChain Message 对象。

读取内容通常这样：

```python
last_message = state["messages"][-1]
text = last_message.content
```

不要总是假设它是 dict：

```python
state["messages"][-1]["content"]
```

这在 Message 对象里不一定对。

### 7. dict 输入示例

学习示例：

```python
graph.invoke({
    "messages": [
        {"type": "human", "content": "订单 1001 没发货"}
    ]
})
```

使用 `add_messages` 时，LangGraph 会尝试把这类 dict 反序列化成 Message 对象。

### 8. ToolMessage 示例

学习示例：

```python
from langchain.messages import ToolMessage

tool_message = ToolMessage(
    content='{"status": "not_shipped"}',
    tool_call_id="call_123",
    name="query_order",
)
```

它表示：

```text
query_order 工具执行完成。
结果对应前面 id 为 call_123 的 tool call。
```

## 五、messages 设计常见错误

### 1. 只保存当前 user_message

错误：

```text
State 里只有 user_message，没有 messages。
```

问题：

```text
用户第二轮说“确认”时，系统不知道前文。
模型无法理解多轮上下文。
```

正确：

```text
user_message 保存当前轮。
messages 保存历史。
```

### 2. messages 使用默认覆盖

错误：

```python
class State(TypedDict):
    messages: list
```

问题：

```text
每次更新 messages 都覆盖旧历史。
```

正确：

```python
messages: Annotated[list[AnyMessage], add_messages]
```

或者：

```python
class State(MessagesState):
    ...
```

### 3. 用 operator.add 处理复杂消息

`operator.add` 可以简单追加。

但如果你需要：

```text
按 message id 更新
支持 dict 反序列化
处理人工修改历史消息
```

就应该用 `add_messages`。

### 4. 把结构化业务状态只写进 messages

错误：

```text
AIMessage: 当前确认状态是 confirmed，字段都齐了。
```

但 State 里没有：

```text
confirmation_status
ticket_fields
missing_fields
```

问题：

```text
代码没法可靠判断。
测试没法稳定断言。
```

### 5. 把所有工具原始结果都塞进 messages

有些工具结果很长。

例如 RAG 检索出多个 chunk。

如果全部塞进 ToolMessage content，会让模型上下文变长。

更好的做法可能是：

```text
content 放模型需要看的摘要或片段。
artifact 或结构化 State 放下游系统需要的元数据。
日志保存调试细节。
```

### 6. 忘记 tool_call_id

ToolMessage 要对应 AIMessage 里的 tool call。

如果没有正确的 `tool_call_id`，模型可能无法知道这个工具结果对应哪次调用。

### 7. messages 无限增长

错误：

```text
永远把所有历史都发给模型。
```

短期能跑。

长期会有：

```text
token 成本高
速度慢
上下文超限
无关历史干扰模型
```

后面要学习历史裁剪、总结和记忆策略。

### 8. 把敏感信息放进 messages

messages 会发给模型，也可能被追踪系统记录。

不要把 API Key、密码、完整身份证、完整 token 等敏感信息放进去。

真实项目要做脱敏和权限控制。

## 六、消息历史太长怎么办

### 1. 为什么会太长

多轮 Agent 会不断追加：

```text
用户消息
AI 回复
工具调用请求
工具执行结果
错误修复
人工确认
```

几十轮以后，messages 会很长。

### 2. 直接全量传给模型的问题

问题包括：

```text
token 成本增加
模型响应变慢
超过上下文窗口
模型被早期无关信息干扰
隐私数据暴露面扩大
```

### 3. 常见处理方式

常见方式有：

```text
只保留最近 N 轮
把早期历史总结成 summary
把长期事实放结构化 State
把业务记录放数据库
把知识放 RAG
工具大结果只传摘要
```

### 4. 哪些不能随便删

不能随便删的内容：

```text
当前未完成工单的用户确认
最新缺失字段追问
最近一次工具调用和 ToolMessage
当前问题相关的 RAG 引用
系统安全规则
```

如果删错，Agent 会失去上下文。

### 5. 结构化 State 可以减轻 messages 压力

例如工单字段不要只靠历史消息。

保存到：

```text
ticket_fields
confirmation_status
missing_fields
```

这样就算裁剪早期 messages，业务状态仍然保留。

这就是结构化 State 的价值。

## 七、本节和后续课程的关系

### 1. 第 7 节会写 StateGraph 最小图

下一节会开始真正写最小图。

到时你会看到：

```python
from langgraph.graph import StateGraph, MessagesState
```

本节就是为了让你理解：

```text
MessagesState 不是神秘类。
它主要帮你定义 messages 字段和 add_messages reducer。
```

### 2. 第 12 节会学 invoke 和 stream

graph 执行时，messages 会不断变化。

`stream` 可以观察中间状态更新。

那时你会看到每一步 messages 如何追加。

### 3. 第 14-20 节会接入智能工单节点

工单 Agent 会同时使用：

```text
messages
intent
ticket_fields
confirmation_status
ticket_id
final_answer
```

你需要知道哪些内容给模型看，哪些内容给代码判断。

### 4. 第 21-22 节会学 checkpoint 和 interrupt

当流程暂停等待用户确认时，messages 和结构化 State 都需要被保存。

否则用户下一轮回来时，流程无法继续。

## 八、本节练习与参考答案

### 练习 1：判断放 messages 还是结构化 State

判断下面内容更适合放 messages、结构化 State，还是两者都需要：

```text
1. 用户本轮说“确认”
2. confirmation_status = confirmed
3. 工单字段 title/order_id/priority
4. AI 给用户的确认文案
5. trace_id
6. ToolMessage 里的订单查询结果摘要
7. Java API 返回的完整内部调试信息
```

参考答案：

```text
1. 两者都需要。作为 HumanMessage 进入 messages，同时结构化确认结果进入 confirmation_status。
2. 结构化 State。
3. 结构化 State。
4. messages 里可以有 AIMessage，final_answer 或 confirmation_message 也可以结构化保存。
5. 结构化 State 或日志，不应该混进 messages 内容。
6. messages 需要模型看的摘要；完整结果可放结构化 State、artifact 或日志。
7. 不应该直接放 messages。可放日志或受控调试信息，并注意敏感信息。
```

### 练习 2：解释 HumanMessage 和 AIMessage

参考答案：

```text
HumanMessage 表示用户输入，AIMessage 表示模型输出。HumanMessage 是模型要理解的任务来源，AIMessage 是模型生成的回答或工具调用请求。
```

### 练习 3：为什么 ToolMessage 需要 tool_call_id

参考答案：

```text
ToolMessage 是对某次工具调用的结果回应。tool_call_id 用来和前面 AIMessage 里的 tool call 对应起来，让模型知道这个结果属于哪个工具请求。
```

### 练习 4：为什么 operator.add 不够处理 messages

参考答案：

```text
operator.add 只是列表拼接，不理解 message id，也不会更新已有消息或反序列化 dict 为 Message 对象。messages 需要更专门的 add_messages reducer。
```

### 练习 5：MessagesState 是什么

参考答案：

```text
MessagesState 是 LangGraph 预置 State，已经定义了 messages 字段，并使用 add_messages 作为 reducer。它适合需要消息历史的图，也可以被继承后添加业务字段。
```

### 练习 6：写一个继承 MessagesState 的学习版 State

参考答案：

```python
from typing import Literal
from langgraph.graph import MessagesState

class TicketAgentState(MessagesState):
    intent: Literal["rag_question", "create_ticket", "unknown"]
    ticket_fields: dict
    missing_fields: list[str]
    confirmation_status: Literal["none", "waiting", "confirmed", "rejected"]
    final_answer: str
```

### 练习 7：为什么 messages 不能替代 ticket_fields

参考答案：

```text
ticket_fields 是创建工单所需的结构化业务字段，代码需要可靠读取和校验。messages 是自然语言上下文，适合模型理解，不适合当作业务执行的唯一依据。
```

### 练习 8：messages 太长有什么问题

参考答案：

```text
会增加 token 成本、降低响应速度、可能超出上下文窗口，也可能让模型被无关历史干扰，还会扩大敏感信息暴露风险。
```

### 练习 9：如何减轻 messages 压力

参考答案：

```text
可以只保留最近 N 轮、总结早期历史、把长期事实放结构化 State、把业务记录放数据库、把知识放 RAG、工具大结果只传摘要。
```

### 练习 10：用户说“确认”时，系统应该怎么处理

参考答案：

```text
把“确认”作为 HumanMessage 追加进 messages，同时根据当前流程状态判断它是否表示工单确认。如果当前确实处于等待确认且字段齐全，再把 confirmation_status 更新为 confirmed，并允许进入创建工单节点。
```

## 九、自测题与答案

### 自测 1：messages 是什么？

答案：

```text
messages 是模型对话上下文，由一组带角色、内容和元数据的消息组成，用于表示 system、human、ai、tool 等交互历史。
```

### 自测 2：user_message 和 messages 的区别是什么？

答案：

```text
user_message 是当前轮用户输入；messages 是完整多轮对话历史。当前 user_message 通常会变成一条 HumanMessage 追加到 messages。
```

### 自测 3：SystemMessage 的作用是什么？

答案：

```text
SystemMessage 用来设置模型行为规则、角色、回答风格和安全边界，例如创建工单前必须确认。
```

### 自测 4：HumanMessage 的作用是什么？

答案：

```text
HumanMessage 表示用户输入和交互，是模型理解当前任务的重要来源。
```

### 自测 5：AIMessage 的作用是什么？

答案：

```text
AIMessage 表示模型输出，可以包含普通文本、tool_calls、usage_metadata、response_metadata 等。
```

### 自测 6：ToolMessage 的作用是什么？

答案：

```text
ToolMessage 表示工具调用结果，会通过 tool_call_id 对应前面的 tool call，让模型基于工具结果继续回答。
```

### 自测 7：为什么 messages 不能默认覆盖？

答案：

```text
因为 messages 保存多轮历史。默认覆盖会丢掉旧消息，导致模型失去上下文。
```

### 自测 8：add_messages 比 operator.add 强在哪里？

答案：

```text
add_messages 能追加新消息，也能根据消息 id 更新已有消息，并尝试把 dict 输入反序列化成 LangChain Message 对象；operator.add 只是简单列表拼接。
```

### 自测 9：MessagesState 里默认有什么？

答案：

```text
MessagesState 默认有 messages 字段，这个字段是 AnyMessage 列表，并使用 add_messages reducer。
```

### 自测 10：messages 能替代结构化 State 吗？

答案：

```text
不能。messages 适合模型理解上下文，结构化 State 适合代码做可靠流程控制、字段校验、用户确认、安全判断和测试断言。
```

### 自测 11：结构化 State 能完全替代 messages 吗？

答案：

```text
不能。模型仍然需要自然语言对话上下文，尤其是用户引用前文、要求改写、继续追问时。
```

### 自测 12：为什么不要把 trace_id 直接写进 AIMessage 给用户看？

答案：

```text
trace_id 是系统追踪字段，应该放结构化 State 或日志里。直接写进 messages 会污染模型上下文，也不适合展示给用户。
```

### 自测 13：本节最核心的一句话是什么？

答案：

```text
MessagesState 负责保存多轮对话消息历史，而结构化 State 负责保存业务流程需要可靠判断的数据；两者配合才是可控 Agent 的基础。
```

## 十、本节小结

这一节的核心不是背 `MessagesState` 这个类名。

你要真正掌握的是：

```text
messages 是模型理解多轮对话的上下文。
messages 不是普通字符串列表，而是带 role、content、metadata 的消息对象列表。
messages 不能默认覆盖。
operator.add 只能简单追加。
add_messages 更适合 messages，因为它能追加、按 id 更新，并做消息反序列化。
MessagesState 是 LangGraph 预置的 messages State。
真实 Agent 通常会继承 MessagesState，再添加业务字段。
messages 不能替代结构化 State。
结构化 State 也不能完全替代 messages。
```

对智能工单 Agent 来说：

```text
messages 负责多轮上下文。
ticket_fields 负责工单草稿。
missing_fields 负责缺失字段。
confirmation_status 负责确认状态。
ticket_id 负责创建结果。
final_answer 负责 API 返回。
trace_id 负责日志追踪。
```

下一节会进入：

```text
阶段 5 第 7 节：StateGraph 最小图
```

那一节会开始真正写一个最小 LangGraph 图。

## 参考资料

- [LangGraph Graph API overview](https://docs.langchain.com/oss/python/langgraph/graph-api)
  - 用途：确认 messages 在 graph state 中的用法、`add_messages` 的作用、`MessagesState` 的定义，以及 messages reducer 为什么不同于普通列表追加。

- [LangGraph Use the Graph API](https://docs.langchain.com/oss/python/langgraph/use-graph-api)
  - 用途：参考 Graph API 中 messages 字段、节点返回 state 更新、`add_messages` 和 `MessagesState` 的实际使用方式。

- [LangGraph Quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart)
  - 用途：观察最小 Agent 示例里如何使用 messages、模型节点、工具节点和条件边组织对话流程。

- [LangChain Messages](https://docs.langchain.com/oss/python/langchain/messages)
  - 用途：理解 `SystemMessage`、`HumanMessage`、`AIMessage`、`ToolMessage`、tool calls、message metadata 和消息内容结构。
