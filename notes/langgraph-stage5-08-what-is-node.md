# 阶段 5 第 8 节：node 节点是什么

## 本节定位

上一节我们第一次写了一个最小 `StateGraph`：

```text
START -> normalize_message -> build_reply -> END
```

这一节继续在这个最小图上学习，但重点从“图整体骨架”转到“节点本身”。

也就是回答这些问题：

```text
LangGraph 里的 node 到底是什么？
node 和普通 Python 函数有什么关系？
node 应该做多大？
node 应该返回什么？
node 里能不能调用 service、模型、外部 API？
node 失败时应该怎么想？
```

本节对第 7 节的最小图做了一个小改动：

```text
START
  -> normalize_message
  -> classify_message
  -> build_reply
  -> END
```

新增了：

```text
classify_message_node
```

它只做一件事：

```text
判断清洗后的消息是 blank 还是 ready。
```

这个改动很小，但教学价值很明确：

```text
一个 node 应该有清楚职责。
一个 node 读取 State。
一个 node 返回局部 State 更新。
多个 node 通过 State 连接起来。
```

## 本节学习目标

学完这一节，你应该能做到：

1. 用自己的话解释 LangGraph node 是什么。
2. 解释 node 和普通 Python 函数的关系。
3. 解释 node 的输入为什么通常是 State。
4. 解释 node 为什么只返回局部 State 更新。
5. 解释 node 名称为什么重要。
6. 解释 node 应该保持单一职责。
7. 判断一个功能应该拆成 node，还是留在普通函数 / service。
8. 解释 node 里什么时候可以调用 service。
9. 解释 node 里什么时候可以调用模型或外部 API。
10. 解释 node 里的副作用为什么要谨慎。
11. 解释 node 重执行和幂等性的关系。
12. 能读懂本节新增的 `classify_message_node`。
13. 能理解未来智能工单 Agent 会有哪些 node。

## 本节先不学什么

为了专注 node，本节暂时不学：

1. 不学 conditional edge。
2. 不学 graph.stream。
3. 不学 checkpoint 代码。
4. 不学 interrupt。
5. 不接真实模型。
6. 不接 RAG。
7. 不接 Java mock API。
8. 不接 FastAPI 新接口。
9. 不启动 Qdrant / Milvus / VMware。

这些后面会学。

本节只把 node 讲透。

## 一、基础知识铺垫

### 1. node 的直观理解

node 可以理解成：

```text
图里的一个处理步骤。
```

例如：

```text
normalize_message：清洗用户输入
classify_message：判断输入是否为空
build_reply：生成回复
```

如果把 Agent 看成一条业务流水线，node 就是流水线上的一个工位。

每个工位都应该有明确职责：

```text
这个工位负责什么？
它需要哪些输入？
它产出哪些结果？
它会不会调用外部系统？
它失败时怎么办？
```

### 2. node 本质上是 Python 函数

LangGraph 官方文档里说得很清楚：

```text
node 是 Python 函数，可以是同步函数，也可以是异步函数。
```

最常见的形状：

```python
def some_node(state: State) -> dict:
    return {"some_key": "some value"}
```

也就是说，node 不是一个神秘类。

它仍然是你熟悉的函数。

只是这个函数被注册到了图里：

```python
builder.add_node("some_node", some_node)
```

注册之后，它才成为 LangGraph 图中的节点。

### 3. node 的输入：State

node 通常接收当前 State。

例如：

```python
def normalize_message_node(state: MinimalGraphState) -> MinimalGraphState:
    user_message = state.get("user_message", "")
    ...
```

它不是从全局变量里读用户输入。

也不是自己去读 HTTP 请求。

它从 State 里拿：

```text
user_message
```

这符合 LangGraph 的思路：

```text
State 是图里所有节点共享的数据。
```

### 4. node 的输出：State 更新

node 通常返回 State 的局部更新。

例如：

```python
return {
    "normalized_message": user_message.strip(),
    "node_history": ["normalize_message"],
}
```

这不是完整 State。

它只是告诉 LangGraph：

```text
这个节点更新了 normalized_message。
这个节点给 node_history 追加了一条记录。
```

LangGraph 会再根据 reducer 把它合并进整体 State。

### 5. 为什么 node 不应该随便返回完整 State

如果 node 返回完整 State，会有几个问题：

```text
容易误覆盖别的字段。
看不出这个节点到底改了什么。
并行节点时更容易冲突。
测试也更难聚焦。
```

例如：

```python
def bad_node(state):
    state["normalized_message"] = state["user_message"].strip()
    return state
```

这段代码短期可能能跑。

但学习阶段更推荐：

```python
def good_node(state):
    return {"normalized_message": state["user_message"].strip()}
```

原因是：

```text
node 只声明自己的产出。
```

### 6. 什么是单一职责

单一职责的意思是：

```text
一个 node 最好只负责一类清晰的事情。
```

例如：

```text
normalize_message_node：清洗输入
classify_message_node：判断输入状态
build_reply_node：生成回复
```

不要把这三件事全部塞进一个 node：

```text
清洗 + 判断 + 生成回复 + 调模型 + 记录日志 + 调 API
```

这样的 node 会很难测试，也很难复用。

### 7. node 是不是越小越好

不是。

node 太大会混乱。

node 太小也会让图变碎。

例如把下面每一行都拆成 node 就没有意义：

```python
message = state.get("user_message", "")
message = message.strip()
message = message.lower()
```

这只是一个普通清洗逻辑。

它们可以放在同一个 `normalize_message_node` 里。

判断 node 粒度时，可以问：

```text
这一步是否有独立业务意义？
这一步是否影响下一步路由？
这一步是否需要单独测试？
这一步是否可能失败并需要单独处理？
这一步是否调用模型或外部服务？
这一步是否会产生副作用？
```

如果答案多次是“是”，它更适合成为 node。

### 8. node 里可以调用普通 service 吗

可以，而且这是推荐方向。

node 不应该把所有业务逻辑都写死在自己里面。

更好的模式：

```text
node 负责图的步骤边界。
service 负责具体业务实现。
```

例如未来智能工单 Agent：

```text
rag_answer_node
  -> 调用 RagAnswerService

create_ticket_node
  -> 调用 JavaTicketClient

extract_ticket_fields_node
  -> 调用结构化输出 service
```

这样图能看清流程，service 能保持可测试和可复用。

### 9. node 里可以调用模型吗

可以。

例如：

```text
classify_intent_node：调用模型做意图识别
extract_ticket_fields_node：调用模型做字段提取
summarize_tool_result_node：调用模型总结工具结果
```

但要注意：

```text
模型调用容易失败。
模型输出需要校验。
测试里不要真实调用模型。
重要业务边界不能只靠模型决定。
```

所以 node 可以调用模型，但模型结果要进入结构化 State，并由代码继续校验。

### 10. node 里可以调用外部 API 吗

可以。

例如：

```text
query_order_node：调用 Java mock 查询订单
create_ticket_node：调用 Java mock 创建工单
rag_retrieve_node：调用向量库检索
```

但外部 API 有风险：

```text
超时
网络失败
返回 404
返回 500
重复执行
数据不一致
```

所以调用外部 API 的 node 要特别注意：

```text
timeout
retry
错误写入 State
幂等性
日志
trace_id
```

### 11. node 里的副作用

副作用就是会改变外部世界的操作。

例如：

```text
创建工单
写数据库
发送邮件
扣库存
退款
```

LangGraph 官方文档提醒：如果图带 checkpointer，节点可能在恢复或重试时重新执行。

所以有副作用的 node 必须谨慎。

例如 `create_ticket_node`：

```text
不能因为恢复执行就重复创建两个工单。
```

后面我们会继续复用前面学过的幂等性思想。

### 12. node 和 edge 的区别

node 做事情。

edge 决定下一步。

例如：

```text
classify_message_node 做判断，写入 message_status。
edge 决定下一步走哪里。
```

本节还没学条件边，所以仍然是固定边。

但从设计上要分清：

```text
node 不应该承担所有路由职责。
路由职责后面会交给 conditional edge。
```

### 13. node 和 reducer 的关系

node 返回更新。

reducer 合并更新。

例如：

```python
return {"node_history": ["classify_message"]}
```

因为 `node_history` 使用：

```python
Annotated[list[str], add]
```

所以最终会追加到旧列表后面。

node 不应该自己手动拿旧 `node_history` 拼起来。

这件事交给 reducer。

### 14. node 和测试的关系

node 是普通函数，所以可以单独测试。

例如：

```python
update = classify_message_node({"normalized_message": "hello"})
assert update == {
    "message_status": "ready",
    "node_history": ["classify_message"],
}
```

这类测试很重要。

它不需要运行整个 graph。

它能精确验证：

```text
这个 node 读取了什么。
这个 node 返回了什么。
这个 node 有没有偷偷改别的字段。
```

## 二、本节主题系统讲解

### 1. 本节代码改了什么

本节主要修改：

```text
projects/ai-service/app/agents/minimal_graph.py
projects/ai-service/tests/test_langgraph_minimal_graph.py
```

文档和索引也会更新。

### 2. State 新增 message_status

代码：

```python
message_status: Literal["blank", "ready"]
```

它表示：

```text
清洗后的输入是否可用于生成正常回复。
```

取值只有两个：

```text
blank：清洗后为空
ready：清洗后有内容
```

为什么用 `Literal`？

因为这个字段最好只有固定值。

避免写成：

```text
empty
blank_message
ready_message
ok
```

固定取值能让后续判断更清楚。

### 3. 新增 classify_message_node

代码：

```python
def classify_message_node(state: MinimalGraphState) -> MinimalGraphState:
    normalized_message = state.get("normalized_message", "")
    message_status = "ready" if normalized_message else "blank"

    return {
        "message_status": message_status,
        "node_history": ["classify_message"],
    }
```

这个 node 的职责非常明确：

```text
读取 normalized_message。
判断它是 blank 还是 ready。
写入 message_status。
记录节点历史。
```

它不做：

```text
不清洗原始输入。
不生成回复。
不调用模型。
不决定流程结束。
不返回完整 State。
```

这就是单一职责。

### 4. build_reply_node 的职责变清楚

之前 `build_reply_node` 自己判断：

```python
if normalized_message:
    ...
```

现在它读取：

```python
message_status = state.get("message_status", "blank")
```

然后决定回复：

```python
reply = (
    f"你说的是：{normalized_message}"
    if message_status == "ready"
    else "你还没有输入内容。"
)
```

这让职责更清楚：

```text
classify_message_node 负责判断状态。
build_reply_node 负责根据状态生成回复。
```

### 5. 图结构更新

之前：

```text
START -> normalize_message -> build_reply -> END
```

现在：

```text
START -> normalize_message -> classify_message -> build_reply -> END
```

代码：

```python
builder.add_node("classify_message", classify_message_node)

builder.add_edge("normalize_message", "classify_message")
builder.add_edge("classify_message", "build_reply")
```

这说明：

```text
新增 node 后，不只是写函数，还要注册 node，并更新边。
```

### 6. node_history 的变化

运行结果从：

```text
["normalize_message", "build_reply"]
```

变成：

```text
["normalize_message", "classify_message", "build_reply"]
```

这说明：

```text
新 node 已经进入图执行链路。
```

### 7. 本节测试增加了什么

原来只测图最终结果。

本节新增了 node 级别测试：

```text
test_normalize_message_node_returns_only_its_state_update
test_classify_message_node_returns_status_update
test_build_reply_node_uses_message_status
```

这类测试的价值是：

```text
它不只看最终输出，还看每个 node 是否只做自己的事。
```

### 8. 为什么要测“只返回局部更新”

例如：

```python
update = normalize_message_node(
    {"user_message": "  hello  ", "reply": "old", "node_history": []}
)
```

期望：

```python
{
    "normalized_message": "hello",
    "node_history": ["normalize_message"],
}
```

注意结果里没有：

```text
reply
```

这说明 node 没有把不属于它的字段带回来。

这对后面大型 Agent 很重要。

### 9. node 名称为什么重要

注册 node 时：

```python
builder.add_node("classify_message", classify_message_node)
```

这里的字符串：

```text
classify_message
```

会用于：

```text
edge 引用
日志
调试
可视化
测试断言
错误排查
```

所以 node 名称不要随便写：

```text
node1
func2
do_stuff
process
```

应该表达业务动作：

```text
classify_intent
extract_ticket_fields
ask_user_confirmation
create_ticket
```

### 10. node 的粒度怎么判断

本节把 `classify_message` 拆出来，是因为它代表一个独立判断：

```text
输入是否为空。
```

在真实智能工单 Agent 中，下面这些通常适合成为 node：

```text
classify_intent
rag_answer
extract_ticket_fields
check_missing_fields
ask_user_confirmation
create_ticket
fallback
```

但下面这些不一定要成为 node：

```text
字符串 strip
日期格式化
字段名映射
简单 bool 判断
构造一个小 dict
```

本节的 `classify_message` 是教学拆分。

真实项目里是否单独拆，要看它是否有独立业务意义。

### 11. node 中不要塞太多 prompt

如果 node 调模型，不要把大量 prompt 字符串散落在 node 里。

更好的做法：

```text
node 负责取 State 和调用 service。
prompt_builder 负责构造 prompt。
structured_output_service 负责模型结构化输出。
```

这和前面阶段已有的 `prompt_builder`、`structured_output_service` 思路一致。

### 12. node 中的错误处理

node 错误大致分几类：

```text
用户可修复错误：缺少字段，需要追问用户。
外部系统错误：Java API 超时、500。
模型可恢复错误：结构化输出解析失败，可重试或让模型修正。
未知错误：应该暴露出来，方便开发排查。
```

不是所有错误都应该在 node 里吞掉。

如果 node 能处理，就写入 State 或进入 fallback。

如果 node 不能处理，应该让错误暴露，后面统一处理。

官方 Thinking in LangGraph 也强调，不同错误要用不同策略。

### 13. node 重执行和幂等性

LangGraph 带 checkpoint、interrupt、retry 后，某个 node 可能重新执行。

如果 node 只是：

```text
清洗字符串
分类
生成回复
```

问题不大。

如果 node 会：

```text
创建工单
写数据库
发送通知
```

就必须考虑幂等。

例如：

```text
create_ticket_node 重执行时不能重复创建两个工单。
```

这就是 node 设计必须考虑的工程问题。

## 三、当前代码逐段讲解

### 1. MinimalGraphState

当前 State：

```python
class MinimalGraphState(TypedDict, total=False):
    user_message: str
    normalized_message: str
    message_status: Literal["blank", "ready"]
    reply: str
    node_history: Annotated[list[str], add]
```

字段分工：

```text
输入：user_message
中间结果：normalized_message
状态判断：message_status
输出：reply
执行轨迹：node_history
```

这已经是一个很小的 Agent 状态模型。

### 2. normalize_message_node

职责：

```text
把用户原始输入标准化。
```

读取：

```text
user_message
```

写入：

```text
normalized_message
node_history
```

它不负责判断是否为空，也不负责生成回答。

### 3. classify_message_node

职责：

```text
判断 normalized_message 是否可用。
```

读取：

```text
normalized_message
```

写入：

```text
message_status
node_history
```

它不关心原始输入，也不生成最终回复。

### 4. build_reply_node

职责：

```text
根据 message_status 和 normalized_message 生成 reply。
```

读取：

```text
message_status
normalized_message
```

写入：

```text
reply
node_history
```

它不重新判断原始输入，也不负责路由。

### 5. build_minimal_graph

现在图结构是：

```python
builder.add_node("normalize_message", normalize_message_node)
builder.add_node("classify_message", classify_message_node)
builder.add_node("build_reply", build_reply_node)

builder.add_edge(START, "normalize_message")
builder.add_edge("normalize_message", "classify_message")
builder.add_edge("classify_message", "build_reply")
builder.add_edge("build_reply", END)
```

它表达：

```text
先清洗。
再分类。
再回复。
最后结束。
```

## 四、运行和验证

### 1. 运行 smoke 脚本

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run python scripts/langgraph_minimal_graph_smoke.py
```

输出包含：

```json
{
  "message_status": "ready",
  "node_history": [
    "normalize_message",
    "classify_message",
    "build_reply"
  ]
}
```

### 2. 运行本节测试

```powershell
uv run pytest tests/test_langgraph_minimal_graph.py
```

本节验证通过：

```text
6 passed
```

### 3. 为什么要跑全量测试

虽然本节只改了最小图，但当前工作区里第 7 节已经新增了 `langgraph` 依赖。

所以收尾时继续跑：

```powershell
uv run pytest
```

确保旧功能没受影响。

## 五、智能工单 Agent 里的 node 设计预览

后面智能工单 Agent 可能会有这些 node：

| node | 职责 | 可能调用 |
| --- | --- | --- |
| `add_user_message` | 把当前输入加入 messages | LangChain message 对象 |
| `classify_intent` | 判断用户意图 | LLM structured output |
| `rag_answer` | 知识库回答 | RAG service |
| `extract_ticket_fields` | 提取工单字段 | LLM structured output |
| `check_missing_fields` | 检查缺失字段 | 普通函数 / service |
| `ask_missing_fields` | 生成追问 | 普通模板或 LLM |
| `ask_user_confirmation` | 生成确认文案 | 普通模板 |
| `create_ticket` | 调 Java mock 创建工单 | JavaTicketClient |
| `fallback` | 兜底回复 | 普通模板或 LLM |

你会发现：

```text
不是每个 node 都调用模型。
不是每个 node 都调用外部 API。
不是每个 node 都很复杂。
```

node 的关键是：

```text
它是图里有意义的流程步骤。
```

## 六、本节练习与参考答案

### 练习 1：解释 node 是什么

参考答案：

```text
node 是 LangGraph 图里的一个处理步骤，本质上是 Python 函数。它读取当前 State，执行一个明确动作，并返回 State 的局部更新。
```

### 练习 2：判断下面哪些适合做 node

题目：

```text
1. 去掉字符串前后空格
2. 识别用户意图
3. 调用 Java API 创建工单
4. 把 priority 从 high 映射成 高
5. 检查工单字段是否缺失
```

参考答案：

```text
1. 通常不必单独做 node，可以放在清洗 node 内。
2. 适合做 node，因为影响后续路由，可能调用模型。
3. 适合做 node，因为是重要业务动作和外部 API 调用。
4. 通常不必单独做 node，可以放普通函数。
5. 适合做 node，因为结果会决定追问还是确认。
```

### 练习 3：为什么 node 返回局部更新

参考答案：

```text
因为 node 只负责声明自己产生的变化。返回局部更新可以避免误覆盖其他 State 字段，也方便 reducer 合并和测试定位。
```

### 练习 4：解释 classify_message_node

参考答案：

```text
它读取 normalized_message，如果有内容就返回 message_status=ready，否则返回 message_status=blank，同时追加 node_history。它不清洗输入，也不生成回复。
```

### 练习 5：为什么 build_reply_node 不再自己判断原始输入

参考答案：

```text
因为判断输入状态已经交给 classify_message_node。build_reply_node 只根据 message_status 和 normalized_message 生成 reply，这样职责更单一。
```

### 练习 6：node 里可以调用 service 吗

参考答案：

```text
可以。推荐模式是 node 负责流程步骤边界，service 负责具体业务实现。例如 create_ticket_node 可以调用 JavaTicketClient，rag_answer_node 可以调用 RagAnswerService。
```

### 练习 7：node 里有副作用时要注意什么

参考答案：

```text
要注意重试、恢复和重复执行。创建工单、写数据库、发送通知等副作用必须考虑幂等性，避免 node 重执行造成重复业务动作。
```

### 练习 8：node 名称为什么不能随便写

参考答案：

```text
node 名称会用于 edge 引用、日志、调试、可视化和测试。清楚的名称能表达业务动作，例如 classify_intent、create_ticket，比 node1、process 更容易维护。
```

### 练习 9：未来 create_ticket_node 应该做什么

参考答案：

```text
它应该读取 ticket_fields、confirmation_status、trace_id 等 State 字段，在确认状态合法且字段齐全时调用 JavaTicketClient 创建工单，然后返回 ticket_id、final_answer 或 error 等 State 更新。它不应该绕过确认直接执行。
```

### 练习 10：node 和 edge 的区别

参考答案：

```text
node 负责执行动作和更新 State；edge 负责决定执行顺序和下一步去哪。node 做事，edge 连接流程。
```

## 七、自测题与答案

### 自测 1：LangGraph node 本质上是什么？

答案：

```text
本质上是 Python 函数，可以是同步函数或异步函数。
```

### 自测 2：node 最常见的第一个参数是什么？

答案：

```text
当前 State。
```

### 自测 3：node 可以接收 config 或 runtime 吗？

答案：

```text
可以。官方文档说明 node 可以接收 state、config、runtime。config 可包含 thread_id 和 tracing 信息，runtime 可包含上下文、store、stream_writer 等运行时信息。
```

### 自测 4：node 返回完整 State 是推荐做法吗？

答案：

```text
通常不推荐。更推荐返回局部 State 更新，只返回这个 node 负责改变的字段。
```

### 自测 5：本节新增的 node 是什么？

答案：

```text
classify_message_node。
```

### 自测 6：classify_message_node 写入哪个字段？

答案：

```text
message_status。
```

### 自测 7：message_status 有哪些取值？

答案：

```text
blank 和 ready。
```

### 自测 8：为什么 node_history 能追加三个节点名？

答案：

```text
因为 node_history 使用 Annotated[list[str], add]，每个 node 返回自己的节点名后，reducer 会把列表追加起来。
```

### 自测 9：有副作用的 node 为什么要考虑幂等？

答案：

```text
因为在 checkpoint、interrupt、retry 或恢复场景中，node 可能重新执行。如果副作用不幂等，可能重复创建工单、重复写数据或重复发送通知。
```

### 自测 10：本节最核心的一句话是什么？

答案：

```text
node 是图里的单一职责处理步骤，它读取 State，执行明确动作，并返回局部 State 更新。
```

## 八、本节小结

本节把第 7 节的最小图扩展成：

```text
START
  -> normalize_message
  -> classify_message
  -> build_reply
  -> END
```

你要真正记住：

```text
node 是 Python 函数。
node 读取 State。
node 返回局部更新。
node 名称要表达业务动作。
node 要尽量单一职责。
node 可以调用 service、模型和外部 API，但副作用要谨慎。
node 失败要根据错误类型选择策略。
```

下一节会进入：

```text
阶段 5 第 9 节：edge 边是什么
```

那一节会专门讲：

```text
节点之间怎么连接。
固定边表示什么。
为什么边不是业务逻辑。
edge 和 conditional edge 有什么区别。
```

## 参考资料

- [LangGraph Graph API overview](https://docs.langchain.com/oss/python/langgraph/graph-api)
  - 用途：确认 node 是 Python 函数，接收 state/config/runtime，返回 State 更新，并通过 `add_node()` 注册到图里。

- [LangGraph Use the Graph API](https://docs.langchain.com/oss/python/langgraph/use-graph-api)
  - 用途：参考 node 如何返回 State 更新、更新如何通过 reducer 应用到 State，以及图执行后返回完整 State。

- [LangGraph Thinking in LangGraph](https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph)
  - 用途：理解如何把 Agent 流程拆成步骤，如何设计 State，如何实现 node，以及不同错误类型应该采用不同处理策略。
