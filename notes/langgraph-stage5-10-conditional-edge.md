# 阶段 5 第 10 节：conditional edge 条件分支

## 本节定位

上一节我们学习了 edge。

上一节的核心结论是：

```text
node 负责做事。
edge 负责决定做完之后去哪里。
```

但是上一节的 edge 是固定的。

也就是说：

```text
START
  -> normalize_message
  -> classify_message
  -> build_reply
  -> END
```

无论用户输入什么，图都会沿着同一条路线往下走。

这在简单流程里没问题。

但是 Agent 不可能永远只有一条路线。

智能工单 Agent 至少会遇到这些情况：

```text
用户问退款规则
  -> 查知识库
  -> 总结回答

用户问订单物流
  -> 调用订单查询工具
  -> 总结回答

用户要创建投诉工单
  -> 抽取工单字段
  -> 检查缺失字段
  -> 必要时追问
  -> 创建工单

用户输入为空
  -> 直接提示重新输入
```

这些都不是固定顺序。

它们需要根据当前状态决定下一步。

所以本节学习：

```text
conditional edge 条件边
```

本节不会接真实大模型，也不会接真实工具。

本节只做一个最小但完整的分支示例：

```text
用户输入为空
  -> 走 build_blank_reply

用户输入正常
  -> 走 build_ready_reply
```

这个例子很小，但它是后面智能工单 Agent 分流的基础。

以后这些流程：

```text
是否需要查订单
是否需要查知识库
是否需要创建工单
是否需要用户确认
是否需要继续追问
```

本质上都要靠类似的分支能力。

## 本节学习目标

学完本节，你应该能解释清楚：

1. 什么是 conditional edge。
2. conditional edge 和普通 edge 的区别。
3. 为什么 Agent 需要条件分支。
4. routing function 路由函数是什么。
5. routing function 为什么要读取 State。
6. `add_conditional_edges()` 的三个核心参数分别是什么。
7. path map 路由映射是什么。
8. 为什么条件判断不应该写在普通 edge 里。
9. 为什么多个普通 outgoing edge 不是二选一。
10. 为什么本节把 `build_reply` 拆成两个节点。
11. 正常输入和空输入在图里分别走哪条路线。
12. 智能工单 Agent 里哪些场景会用 conditional edge。

## 本节先不学什么

本节暂时不学：

1. 多工具并行。
2. `Send` 动态分发。
3. `Command` 同时更新 State 和跳转。
4. checkpoint 持久化。
5. interrupt 人工确认。
6. 真实大模型工具调用循环。
7. LangSmith tracing。

原因很简单：

conditional edge 是 LangGraph 分支控制的基础。

如果这一层没学透，后面的工具调用、人工确认、循环追问都会变成“看得懂代码，但说不清流程为什么这样走”。

所以本节先把条件分支讲扎实。

## 一、基础知识铺垫

### 1. 先从生活里的流程分支理解

很多流程不是一条直线。

比如你去办理业务：

```text
开始
  -> 取号
  -> 工作人员检查材料
```

接下来有两种可能：

```text
材料齐全
  -> 进入办理窗口

材料不齐
  -> 回去补材料
```

这里的“材料齐全吗”就是一个判断条件。

判断结果不同，下一步就不同。

这就是条件分支。

程序里也一样。

普通 Python 代码会这样写：

```python
if material_ready:
    process()
else:
    ask_for_more_material()
```

LangGraph 里的 conditional edge，本质也是类似思想。

只是它不是普通函数里的 `if/else`。

它是在“图的边”上表达：

```text
某个节点执行完以后，根据 State 选择下一条边。
```

### 2. 为什么普通 edge 不够用

普通 edge 只能表达固定路线。

比如：

```python
builder.add_edge("classify_message", "build_reply")
```

意思是：

```text
classify_message 执行完以后，总是进入 build_reply。
```

这个“总是”很关键。

普通 edge 不看 State。

它不会关心：

```text
用户输入是不是空
意图是不是查订单
字段是不是完整
工具是不是失败
用户是不是确认了
```

它只表达固定连接。

所以如果你想表达：

```text
如果 message_status == ready，走正常回复。
如果 message_status == blank，走空内容提醒。
```

普通 edge 就不够了。

### 3. conditional edge 是什么

conditional edge 可以翻译成：

```text
条件边
```

它的意思是：

```text
某个节点执行完以后，不是固定进入某一个节点，
而是调用一个路由函数，
由路由函数根据当前 State 返回路线，
然后 LangGraph 根据返回结果选择下一个节点。
```

可以拆成三个动作：

```text
第一步：某个节点刚执行完
第二步：LangGraph 调用路由函数
第三步：根据路由函数的返回值，进入对应节点
```

本节例子里是：

```text
classify_message 执行完
  -> 调用 route_by_message_status
  -> 如果返回 ready，进入 build_ready_reply
  -> 如果返回 blank，进入 build_blank_reply
```

### 4. conditional edge 和普通 edge 的区别

普通 edge：

```text
A -> B
```

含义：

```text
A 执行完固定进入 B。
```

conditional edge：

```text
A -> routing_function -> B 或 C
```

含义：

```text
A 执行完以后，先调用路由函数。
路由函数看 State。
State 不同，返回值不同。
返回值不同，下一步节点不同。
```

对比表：

| 对比点 | 普通 edge | conditional edge |
| --- | --- | --- |
| 是否看 State | 不看 | 看 |
| 是否分支 | 不分支 | 可以分支 |
| 适合什么 | 固定流程 | 动态流程 |
| 核心 API | `add_edge()` | `add_conditional_edges()` |
| 是否需要路由函数 | 不需要 | 需要 |
| 智能工单用途 | 稳定主干流程 | 意图分流、工具分流、追问分流 |

### 5. 为什么 Agent 必须有条件分支

Agent 和普通问答接口最大的区别之一，就是 Agent 会根据情况决定下一步。

普通问答接口可能是：

```text
用户问题
  -> 调模型
  -> 返回答案
```

Agent 更像：

```text
用户问题
  -> 判断问题类型
  -> 决定是否调用工具
  -> 决定调用哪个工具
  -> 决定工具结果是否够用
  -> 决定是否继续问用户
  -> 决定最终如何回答
```

这些“决定”就是分支点。

如果没有条件分支，你只能写成：

```text
每一步都执行
```

这会出问题。

比如：

```text
用户只是问退款规则
  -> 不应该查订单
  -> 不应该创建工单
  -> 不应该要求用户确认创建
```

再比如：

```text
用户输入为空
  -> 不应该继续调用大模型
  -> 不应该查知识库
  -> 不应该查订单
```

所以 Agent 必须能根据状态选择路线。

conditional edge 就是 LangGraph 里表达这件事的基础方式。

### 6. State 在条件分支里的作用

State 是图运行时共享的状态。

前面我们已经学过：

```text
State 保存图运行过程中积累的信息。
```

在本节代码里，State 里有：

```python
message_status: Literal["blank", "ready"]
```

它表示用户输入状态：

```text
blank：用户输入为空
ready：用户输入正常
```

条件边要靠它做决定。

如果没有 State，路由函数就没有判断依据。

路由函数不会凭空知道用户输入是不是空。

所以分支路线通常是：

```text
前面的 node 写入 State
后面的 routing function 读取 State
conditional edge 根据 routing function 的返回值选择下一步
```

本节就是：

```text
normalize_message_node
  -> 写入 normalized_message

classify_message_node
  -> 读取 normalized_message
  -> 写入 message_status

route_by_message_status
  -> 读取 message_status
  -> 返回 ready 或 blank
```

### 7. routing function 是什么

routing function 可以翻译成：

```text
路由函数
```

它不是普通业务节点。

它的任务不是生成回复，也不是查数据库，也不是调用工具。

它只负责回答一个问题：

```text
下一步走哪里？
```

本节代码里：

```python
def route_by_message_status(state: MinimalGraphState) -> MessageRoute:
    return "ready" if state.get("message_status") == "ready" else "blank"
```

这段代码可以翻译成：

```text
如果 State 里的 message_status 是 ready，
路由结果就是 ready。

否则，
路由结果就是 blank。
```

注意：

它返回的不是用户最终答案。

它返回的是路线标识。

### 8. 路由函数和节点函数有什么区别

节点函数 node function：

```text
负责做事，并返回 State 更新。
```

比如：

```python
def classify_message_node(state):
    return {"message_status": "ready"}
```

路由函数 routing function：

```text
负责选路，并返回路线结果。
```

比如：

```python
def route_by_message_status(state):
    return "ready"
```

区别很重要：

| 对比点 | node function | routing function |
| --- | --- | --- |
| 是否是图里的节点 | 是 | 不是业务节点 |
| 主要职责 | 做事 | 选路 |
| 常见返回值 | State 更新字典 | 路线名、节点名、END 等 |
| 是否应该写复杂业务副作用 | 可以谨慎写 | 不应该 |
| 是否进入 `node_history` | 通常进入 | 本节不进入 |

为什么本节不把 routing function 写进 `node_history`？

因为 `node_history` 是用来观察真正执行过的业务节点。

路由函数只是边上的判断逻辑。

它不是一个独立执行业务动作的节点。

### 9. path map 是什么

LangGraph 的 `add_conditional_edges()` 可以接收一个映射。

本节代码：

```python
MINIMAL_GRAPH_CONDITIONAL_ROUTES: dict[MessageRoute, str] = {
    "ready": "build_ready_reply",
    "blank": "build_blank_reply",
}
```

它的意思是：

```text
如果路由函数返回 ready，就去 build_ready_reply。
如果路由函数返回 blank，就去 build_blank_reply。
```

这个映射可以叫：

```text
path map
路由映射
分支映射
```

它把“路由函数返回的语义结果”和“真实节点名”分开。

这样有两个好处：

第一，路由函数更像业务判断：

```python
return "ready"
```

第二，图结构里再说明 ready 对应哪个节点：

```python
"ready": "build_ready_reply"
```

这比让路由函数直接返回节点名更适合教学。

因为你能清楚看到两层关系：

```text
判断结果：ready / blank
真实节点：build_ready_reply / build_blank_reply
```

### 10. 为什么本节不用路由函数直接返回节点名

官方文档允许路由函数直接返回节点名。

比如：

```python
def route(state):
    return "build_ready_reply"
```

然后：

```python
builder.add_conditional_edges("classify_message", route)
```

这种写法可以运行。

但本节没有这么写。

本节采用：

```python
def route_by_message_status(state):
    return "ready"

builder.add_conditional_edges(
    "classify_message",
    route_by_message_status,
    {"ready": "build_ready_reply", "blank": "build_blank_reply"},
)
```

原因是：

```text
学习阶段要把“业务判断结果”和“图节点名”拆开。
```

真实项目里也是这样更容易维护。

比如智能工单 Agent 以后可能有：

```python
{
    "answer_from_knowledge_base": "retrieve_policy",
    "query_order": "query_order_tool",
    "create_ticket": "extract_ticket_fields",
    "need_clarification": "ask_clarifying_question",
}
```

左边是意图或路线。

右边是真正节点。

这比直接到处写节点名更清晰。

### 11. 为什么不应该用多个普通 edge 表达二选一

这一点上一节讲过，本节再补一层。

错误写法：

```python
builder.add_edge("classify_message", "build_ready_reply")
builder.add_edge("classify_message", "build_blank_reply")
```

你可能会以为这代表：

```text
二选一
```

但普通 edge 不是二选一。

普通 edge 表达的是：

```text
都可以继续走
```

在 LangGraph 的图执行模型里，一个节点有多个普通 outgoing edge，多个目标节点会在下一轮一起执行。

所以这不是分支选择。

如果你想表达：

```text
条件满足走 A，否则走 B
```

就应该用 conditional edge。

### 12. 为什么不要把条件判断全部塞进一个 node

不用 conditional edge，也可以这样写：

```python
def build_reply_node(state):
    if state["message_status"] == "ready":
        return {"reply": "..."}
    return {"reply": "你还没有输入内容。"}
```

这确实能运行。

第 9 节之前我们的代码就是这种思路。

但问题是：

```text
图结构看不出分支。
```

如果流程很小，问题不大。

但是智能工单 Agent 会越来越复杂。

如果所有分支都塞进一个 node，最后会变成：

```python
def giant_agent_node(state):
    if 要查订单:
        ...
    elif 要查知识库:
        ...
    elif 要创建工单:
        ...
    elif 要追问:
        ...
    elif 要人工确认:
        ...
```

这就退化成一个巨大的函数。

LangGraph 的价值之一，就是让流程结构显式化。

条件边可以把流程表达成：

```text
classify_intent
  -> query_order
  -> retrieve_policy
  -> extract_ticket_fields
  -> ask_clarifying_question
  -> request_user_confirmation
```

也就是：

```text
判断逻辑清楚。
节点职责清楚。
路线关系清楚。
测试也更容易写。
```

### 13. conditional edge 应该保持轻量

路由函数应该尽量轻。

它最好只做：

```text
读取 State
做简单判断
返回路线名
```

不适合在路由函数里做：

```text
调用大模型
访问数据库
发 HTTP 请求
写文件
创建工单
修改外部状态
```

原因是：

1. 路由函数主要是控制流程，不是执行业务。
2. 有副作用的操作应该放在明确的 node 里。
3. 路由函数越复杂，图越难推理。
4. 测试路由时会变得很麻烦。

更好的设计是：

```text
node 负责产生判断依据
routing function 负责根据判断依据选路
```

比如：

```text
classify_intent_node
  -> 写入 intent

route_by_intent
  -> 读取 intent
  -> 返回 query_order / answer_policy / create_ticket
```

### 14. conditional edge 和 if/else 的关系

conditional edge 很像 `if/else`，但它不是普通 `if/else` 的简单替代品。

普通 `if/else` 发生在一个函数内部：

```python
if condition:
    do_a()
else:
    do_b()
```

conditional edge 发生在图结构上：

```text
node_a
  -> 条件判断
  -> node_b 或 node_c
```

区别在于：

```text
普通 if/else 隐藏在代码内部。
conditional edge 让分支成为图的一部分。
```

这会带来几个好处：

1. 更容易画出流程图。
2. 更容易单独测试每个节点。
3. 更容易扩展新分支。
4. 更适合做 tracing 和调试。
5. 更适合 long-running agent。

### 15. conditional edge 和智能工单 Agent 的关系

智能工单 Agent 里，conditional edge 会反复出现。

例如：

```text
用户输入
  -> 识别意图
  -> 根据意图分支
```

可能路线：

```text
退款规则问题
  -> RAG 检索知识库

订单状态问题
  -> 调用订单查询工具

投诉/售后问题
  -> 抽取工单字段

闲聊或无关问题
  -> 直接回答或拒答
```

再比如工单创建流程：

```text
抽取字段
  -> 检查字段是否完整
```

可能路线：

```text
字段完整
  -> 请求用户确认

字段缺失
  -> 追问缺失字段
```

再比如工具执行结果：

```text
调用订单查询工具
  -> 检查结果
```

可能路线：

```text
查询成功
  -> 总结订单状态

订单不存在
  -> 提示用户核对订单号

工具失败
  -> 兜底说明并建议稍后重试
```

这些都离不开 conditional edge。

### 16. 本节的最小图为什么仍然有价值

本节例子只有两个分支：

```text
ready
blank
```

你可能会觉得太简单。

但它的价值在于：

```text
它把 LangGraph 条件分支的完整结构走通了。
```

完整结构包括：

1. 前置节点写入状态。
2. 路由函数读取状态。
3. `add_conditional_edges()` 注册条件边。
4. 路由映射把返回值对应到节点。
5. 不同分支进入不同节点。
6. 两个分支最后都进入 `END`。
7. 测试验证两条路线都能走通。

这比一上来写复杂业务更适合学习。

因为你先把骨架看懂，后面换成智能工单业务时只是把：

```text
ready / blank
```

换成：

```text
query_order / retrieve_policy / create_ticket / ask_clarification
```

思想是一样的。

## 二、本节主题系统讲解

### 1. 本节代码改了什么

本节把第 9 节的固定路线：

```text
START
  -> normalize_message
  -> classify_message
  -> build_reply
  -> END
```

改成了带条件分支的路线：

```text
START
  -> normalize_message
  -> classify_message
      -> ready -> build_ready_reply -> END
      -> blank -> build_blank_reply -> END
```

变化点有四个：

1. 新增 `MessageRoute` 类型。
2. 新增 `MINIMAL_GRAPH_CONDITIONAL_ROUTES`。
3. 新增 `route_by_message_status()` 路由函数。
4. 把一个 `build_reply` 节点拆成两个回复节点。

这样做不是为了让代码更长。

而是为了让图的分支更清楚。

### 2. MessageRoute 是什么

代码：

```python
MessageRoute = Literal["ready", "blank"]
```

它表示路由函数只能返回两种路线：

```text
ready
blank
```

这不是必须的。

不用 `Literal` 也可以写。

但学习阶段加上它有三个好处：

第一，返回值范围更清楚。

你一眼能看出：

```text
这个路由函数不会返回 query_order，也不会返回 create_ticket。
它只会返回 ready 或 blank。
```

第二，编辑器更容易提示。

如果你以后写错：

```python
return "readey"
```

这种拼写错误更容易被发现。

第三，它让路由设计更像接口契约。

也就是说：

```text
路由函数承诺只返回这些路线。
path map 也应该覆盖这些路线。
```

### 3. MINIMAL_GRAPH_EDGES 现在表达什么

代码：

```python
MINIMAL_GRAPH_EDGES: tuple[tuple[str, str], ...] = (
    (START, "normalize_message"),
    ("normalize_message", "classify_message"),
    ("build_ready_reply", END),
    ("build_blank_reply", END),
)
```

第 9 节时，它表达完整固定路线。

第 10 节以后，它表达的是：

```text
图中仍然固定的部分。
```

固定部分有：

```text
START -> normalize_message
normalize_message -> classify_message
build_ready_reply -> END
build_blank_reply -> END
```

注意，中间少了：

```text
classify_message -> build_reply
```

因为这里已经不再固定。

`classify_message` 后面应该根据 `message_status` 分支。

所以它不能再写成普通 edge。

### 4. MINIMAL_GRAPH_CONDITIONAL_ROUTES 是什么

代码：

```python
MINIMAL_GRAPH_CONDITIONAL_ROUTES: dict[MessageRoute, str] = {
    "ready": "build_ready_reply",
    "blank": "build_blank_reply",
}
```

它表达：

```text
路由结果 ready 对应 build_ready_reply 节点。
路由结果 blank 对应 build_blank_reply 节点。
```

这就是 path map。

它不是业务数据。

它是图结构配置。

如果以后新增一种状态：

```text
too_long
```

那么你可能需要新增：

```python
MessageRoute = Literal["ready", "blank", "too_long"]
```

并新增映射：

```python
"too_long": "build_too_long_reply"
```

然后新增对应节点。

这就是 conditional edge 的可扩展性。

### 5. classify_message_node 的职责

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

这个节点负责：

```text
判断消息状态。
```

它不负责决定下一个节点。

它只把判断结果写入 State：

```text
message_status = ready 或 blank
```

这种设计很重要。

因为它把事情拆开了：

```text
classify_message_node：产出判断依据
route_by_message_status：使用判断依据选路
```

如果你把这两件事混在一起，短期看代码少，长期会难维护。

### 6. route_by_message_status 的职责

代码：

```python
def route_by_message_status(state: MinimalGraphState) -> MessageRoute:
    return "ready" if state.get("message_status") == "ready" else "blank"
```

它只做一件事：

```text
根据 message_status 返回路线名。
```

如果状态是：

```python
{"message_status": "ready"}
```

它返回：

```text
ready
```

如果状态是：

```python
{"message_status": "blank"}
```

它返回：

```text
blank
```

如果 State 里暂时没有 `message_status`，它也会返回：

```text
blank
```

这是一个保守兜底。

因为输入状态不完整时，比起继续生成正常回复，提示用户没有输入更安全。

### 7. build_ready_reply_node 的职责

代码：

```python
def build_ready_reply_node(state: MinimalGraphState) -> MinimalGraphState:
    normalized_message = state.get("normalized_message", "")

    return {
        "reply": f"你说的是：{normalized_message}",
        "node_history": ["build_ready_reply"],
    }
```

这个节点只处理正常输入。

它默认自己收到的是：

```text
ready 分支
```

所以它不再需要写：

```python
if message_status == "ready":
```

原因是：

```text
分支判断已经交给 conditional edge。
进入这个节点，就意味着图已经选择了 ready 路线。
```

这就是条件边带来的好处：

```text
节点内部少一点分支判断。
节点职责更单一。
```

### 8. build_blank_reply_node 的职责

代码：

```python
def build_blank_reply_node(state: MinimalGraphState) -> MinimalGraphState:
    return {
        "reply": "你还没有输入内容。",
        "node_history": ["build_blank_reply"],
    }
```

这个节点只处理空输入。

它不关心正常输入怎么回复。

因为正常输入不会进入它。

它的职责很明确：

```text
告诉用户输入为空。
```

以后智能工单 Agent 里也会有类似节点：

```text
ask_missing_order_id_node
ask_missing_ticket_reason_node
ask_user_confirmation_node
```

这些节点只服务于某一条分支。

### 9. build_minimal_graph 现在怎么注册图

代码：

```python
def build_minimal_graph():
    builder = StateGraph(MinimalGraphState)

    builder.add_node("normalize_message", normalize_message_node)
    builder.add_node("classify_message", classify_message_node)
    builder.add_node("build_ready_reply", build_ready_reply_node)
    builder.add_node("build_blank_reply", build_blank_reply_node)

    for start_node, end_node in MINIMAL_GRAPH_EDGES:
        builder.add_edge(start_node, end_node)

    builder.add_conditional_edges(
        "classify_message",
        route_by_message_status,
        MINIMAL_GRAPH_CONDITIONAL_ROUTES,
    )

    return builder.compile()
```

可以按三步读：

第一步，注册节点：

```text
normalize_message
classify_message
build_ready_reply
build_blank_reply
```

第二步，注册固定边：

```text
START -> normalize_message
normalize_message -> classify_message
build_ready_reply -> END
build_blank_reply -> END
```

第三步，注册条件边：

```text
classify_message
  -> route_by_message_status
  -> ready / blank
  -> 对应节点
```

这样整个图就完整了。

### 10. add_conditional_edges 的三个参数

本节代码：

```python
builder.add_conditional_edges(
    "classify_message",
    route_by_message_status,
    MINIMAL_GRAPH_CONDITIONAL_ROUTES,
)
```

第一个参数：

```text
"classify_message"
```

意思是：

```text
从哪个节点执行完以后开始做条件路由。
```

第二个参数：

```text
route_by_message_status
```

意思是：

```text
用哪个函数判断下一步路线。
```

第三个参数：

```text
MINIMAL_GRAPH_CONDITIONAL_ROUTES
```

意思是：

```text
路由函数返回值和真实节点之间如何对应。
```

合起来读：

```text
classify_message 节点执行完以后，
调用 route_by_message_status，
如果它返回 ready，就去 build_ready_reply，
如果它返回 blank，就去 build_blank_reply。
```

### 11. 图运行时的完整过程

当输入是：

```python
"  你好，LangGraph  "
```

执行过程：

```text
START
  -> normalize_message
      写入 normalized_message = "你好，LangGraph"

  -> classify_message
      写入 message_status = "ready"

  -> route_by_message_status
      读取 message_status
      返回 ready

  -> build_ready_reply
      写入 reply = "你说的是：你好，LangGraph"

  -> END
```

最终 `node_history`：

```python
[
    "normalize_message",
    "classify_message",
    "build_ready_reply",
]
```

当输入是：

```python
"   "
```

执行过程：

```text
START
  -> normalize_message
      写入 normalized_message = ""

  -> classify_message
      写入 message_status = "blank"

  -> route_by_message_status
      读取 message_status
      返回 blank

  -> build_blank_reply
      写入 reply = "你还没有输入内容。"

  -> END
```

最终 `node_history`：

```python
[
    "normalize_message",
    "classify_message",
    "build_blank_reply",
]
```

这就是条件边的效果：

```text
同一个图，不同输入，走不同路线。
```

### 12. 为什么测试要覆盖两条分支

条件分支最怕只测一条路。

如果只测正常输入：

```python
run_minimal_graph("hello")
```

你只能证明：

```text
ready 分支能走通。
```

但你不能证明：

```text
blank 分支能走通。
```

所以本节测试必须覆盖：

```text
正常输入
空输入
路由函数返回 ready
路由函数默认 blank
path map 是否正确
两个回复节点是否职责单一
```

以后写真实 Agent 时也是一样。

只要有分支，就要尽量覆盖每条重要路线。

比如：

```text
查订单成功
订单不存在
工具超时
字段完整
字段缺失
用户确认
用户拒绝
```

这些都是要测试的路线。

## 三、当前代码逐段讲解

### 1. 路由类型

```python
MessageRoute = Literal["ready", "blank"]
```

这行代码的学习价值在于：

```text
把允许出现的路线结果限制住。
```

它不是业务功能本身。

它是为了让代码更像有清晰契约的流程系统。

如果以后有人问你：

```text
这个条件边可能走哪些路线？
```

你可以直接回答：

```text
看 MessageRoute，目前只有 ready 和 blank。
```

### 2. 固定边

```python
MINIMAL_GRAPH_EDGES: tuple[tuple[str, str], ...] = (
    (START, "normalize_message"),
    ("normalize_message", "classify_message"),
    ("build_ready_reply", END),
    ("build_blank_reply", END),
)
```

这里没有写：

```python
("classify_message", "build_ready_reply")
```

也没有写：

```python
("classify_message", "build_blank_reply")
```

因为 `classify_message` 后面不是固定关系。

它后面是条件关系。

所以 `classify_message` 的后续路线要交给：

```python
add_conditional_edges()
```

### 3. 条件路由映射

```python
MINIMAL_GRAPH_CONDITIONAL_ROUTES: dict[MessageRoute, str] = {
    "ready": "build_ready_reply",
    "blank": "build_blank_reply",
}
```

这段代码的重点不是字典语法。

字典你前面 Python 基础已经学过。

这里的重点是：

```text
字典被用来表达路线映射。
```

左边：

```text
ready / blank
```

是路由函数返回的结果。

右边：

```text
build_ready_reply / build_blank_reply
```

是真实节点名。

### 4. 路由函数

```python
def route_by_message_status(state: MinimalGraphState) -> MessageRoute:
    return "ready" if state.get("message_status") == "ready" else "blank"
```

这段代码不要只看成三元表达式。

它在图里的含义是：

```text
根据当前 State 里的 message_status，
决定 classify_message 后面走哪条边。
```

它不返回：

```python
{"reply": "..."}
```

它也不返回：

```python
{"message_status": "..."}
```

因为它不是 node。

它返回：

```text
路线名
```

### 5. 两个回复节点

正常输入节点：

```python
def build_ready_reply_node(state: MinimalGraphState) -> MinimalGraphState:
    normalized_message = state.get("normalized_message", "")

    return {
        "reply": f"你说的是：{normalized_message}",
        "node_history": ["build_ready_reply"],
    }
```

空输入节点：

```python
def build_blank_reply_node(state: MinimalGraphState) -> MinimalGraphState:
    return {
        "reply": "你还没有输入内容。",
        "node_history": ["build_blank_reply"],
    }
```

重点不是这两个回复内容有多复杂。

重点是：

```text
两个分支进入两个不同节点。
```

这能让你从 `node_history` 里直接观察路线。

### 6. 条件边注册

```python
builder.add_conditional_edges(
    "classify_message",
    route_by_message_status,
    MINIMAL_GRAPH_CONDITIONAL_ROUTES,
)
```

这就是本节最核心的代码。

可以翻译为：

```text
classify_message 节点执行完以后，
调用 route_by_message_status 看当前 State。
根据返回的路线名，
在 MINIMAL_GRAPH_CONDITIONAL_ROUTES 里找到真实下一节点。
```

如果返回：

```text
ready
```

进入：

```text
build_ready_reply
```

如果返回：

```text
blank
```

进入：

```text
build_blank_reply
```

### 7. 为什么两个回复节点都连到 END

代码里有：

```python
("build_ready_reply", END),
("build_blank_reply", END),
```

因为无论走哪条回复分支，回复生成后这张最小图都应该结束。

所以两条分支最后都回到：

```text
END
```

可以画成：

```text
                      -> build_ready_reply -> END
classify_message ----|
                      -> build_blank_reply -> END
```

这也是工作流里很常见的结构：

```text
先分叉，再在某个位置结束或汇合。
```

本节没有把两个分支汇合到同一个后续节点。

以后真实 Agent 可能会这样：

```text
query_order -> build_final_answer
retrieve_policy -> build_final_answer
create_ticket -> build_final_answer
```

这叫“分支之后汇合”。

后面会学。

## 四、智能工单 Agent 里的 conditional edge

### 1. 第一类：根据用户意图分流

智能工单 Agent 最常见的条件边之一：

```text
classify_intent
  -> route_by_intent
```

可能路线：

```text
query_order
answer_policy
create_ticket
smalltalk
unsupported
```

示意：

```text
用户问：“我的订单 1001 到哪了？”
  -> intent = query_order
  -> 走 query_order_tool

用户问：“退款规则是什么？”
  -> intent = answer_policy
  -> 走 retrieve_policy

用户说：“我要投诉商家”
  -> intent = create_ticket
  -> 走 extract_ticket_fields
```

这种分支不能用普通 edge。

因为普通 edge 会让多个分支都执行。

### 2. 第二类：根据字段是否完整分流

创建工单通常需要字段。

比如：

```text
订单号
问题类型
问题描述
联系方式
```

抽取字段后，需要判断：

```text
字段完整吗？
```

可能路线：

```text
完整
  -> 请求用户确认

不完整
  -> 追问缺失字段
```

这也是 conditional edge。

示意：

```text
extract_ticket_fields
  -> check_missing_fields
  -> route_by_missing_fields
      -> ask_missing_fields
      -> request_confirmation
```

### 3. 第三类：根据工具结果分流

订单查询工具可能返回不同结果：

```text
成功
订单不存在
工具超时
权限不足
参数错误
```

不同结果要走不同路线：

```text
成功
  -> 总结订单状态

订单不存在
  -> 提示用户核对订单号

工具超时
  -> 兜底说明并建议稍后重试
```

这也是条件分支。

### 4. 第四类：根据用户确认结果分流

写操作不能随便执行。

比如创建工单前，要让用户确认：

```text
是否确认创建工单？
```

用户可能回答：

```text
确认
取消
修改信息
```

对应路线：

```text
确认
  -> create_ticket

取消
  -> cancel_ticket_creation

修改信息
  -> ask_for_correction
```

这里也需要 conditional edge。

### 5. 第五类：根据是否需要继续循环分流

很多 Agent 不是只走一轮。

比如工具调用 Agent：

```text
LLM 生成消息
  -> 如果有 tool_calls，执行工具
  -> 工具结果回给 LLM
  -> LLM 再决定是否继续调用工具
  -> 没有 tool_calls，结束
```

这类流程通常需要一个“是否继续”的路由函数。

官方 quickstart 里也有类似思想：

```text
如果最后一条模型消息带有 tool_calls，就去工具节点。
否则结束。
```

这就是 Agent 循环的基础。

## 五、常见错误

### 1. 把普通 edge 当成条件分支

错误写法：

```python
builder.add_edge("classify_message", "build_ready_reply")
builder.add_edge("classify_message", "build_blank_reply")
```

问题：

```text
这不是二选一。
两个目标节点都可能执行。
```

正确做法：

```python
builder.add_conditional_edges(
    "classify_message",
    route_by_message_status,
    {
        "ready": "build_ready_reply",
        "blank": "build_blank_reply",
    },
)
```

### 2. 路由函数返回值和 path map 对不上

错误写法：

```python
def route(state):
    return "empty"

path_map = {
    "blank": "build_blank_reply",
}
```

问题：

```text
路由函数返回 empty，但 path map 里没有 empty。
```

结果可能是运行时报错，或者图无法找到正确下一步。

正确做法：

```text
路由函数可能返回什么，path map 就要覆盖什么。
```

### 3. 路由函数里写太多业务逻辑

不推荐：

```python
def route(state):
    result = requests.get(...)
    if result.ok:
        return "success"
    return "failed"
```

问题：

```text
路由函数变成了业务执行节点。
```

更推荐：

```text
query_order_node 负责请求外部服务并写入 State。
route_by_order_result 负责读取 State 并选择路线。
```

### 4. 忘记给分支终止或后续路线

错误：

```text
classify_message
  -> build_ready_reply
```

但：

```text
build_ready_reply 没有连到 END，也没有连到后续节点。
```

这样图可能无法按预期结束。

本节两个分支都显式连到：

```text
END
```

### 5. 一个节点后面混用普通 edge 和 conditional edge

不推荐：

```python
builder.add_edge("classify_message", "some_node")

builder.add_conditional_edges(
    "classify_message",
    route_by_message_status,
    {...},
)
```

问题：

```text
classify_message 后面既有固定路线，又有动态路线。
这会让流程很难推理。
```

更清晰的规则：

```text
一个节点后面要么用普通 edge。
要么用 conditional edge。
不要混着写。
```

### 6. 把路线名起得太抽象

不推荐：

```python
return "a"
return "b"
```

更推荐：

```python
return "ready"
return "blank"
```

原因：

```text
路线名本身应该表达业务含义。
```

以后你看日志或测试失败时，`ready` / `blank` 比 `a` / `b` 好理解得多。

## 六、本节练习与参考答案

### 练习 1：用自己的话解释 conditional edge

参考答案：

conditional edge 是条件边。它表示某个节点执行完以后，不是固定进入某个下一个节点，而是先调用路由函数，由路由函数根据当前 State 返回路线，再进入对应的下一个节点。

### 练习 2：普通 edge 和 conditional edge 最大区别是什么？

参考答案：

普通 edge 是固定路线，不看 State。conditional edge 是动态路线，会通过路由函数读取 State，再决定下一步走哪里。

### 练习 3：本节为什么不能继续使用 `classify_message -> build_reply`？

参考答案：

因为 `classify_message` 后面已经不是固定路线。正常输入应该走 `build_ready_reply`，空输入应该走 `build_blank_reply`。所以这里需要 conditional edge，而不是普通 edge。

### 练习 4：`route_by_message_status` 是 node 吗？

参考答案：

不是。它是路由函数，不是业务节点。它不返回 State 更新，而是返回路线名，例如 `ready` 或 `blank`。

### 练习 5：本节的 path map 是什么？

参考答案：

本节的 path map 是：

```python
{
    "ready": "build_ready_reply",
    "blank": "build_blank_reply",
}
```

它表示路由函数返回 `ready` 时进入 `build_ready_reply`，返回 `blank` 时进入 `build_blank_reply`。

### 练习 6：为什么 `build_ready_reply_node` 里不再判断 `message_status`？

参考答案：

因为是否进入 `build_ready_reply_node` 已经由 conditional edge 决定。进入这个节点就说明当前路线是 `ready`，所以节点内部不需要再次写同样的分支判断。

### 练习 7：用户输入 `"   "` 时，图会经过哪些业务节点？

参考答案：

会经过：

```text
normalize_message
classify_message
build_blank_reply
```

因为空格会被 `strip()` 清理成空字符串，然后 `message_status` 变成 `blank`，路由函数返回 `blank`。

### 练习 8：用户输入 `"hello"` 时，图会经过哪些业务节点？

参考答案：

会经过：

```text
normalize_message
classify_message
build_ready_reply
```

因为 `normalized_message` 是 `"hello"`，`message_status` 是 `ready`，路由函数返回 `ready`。

### 练习 9：为什么不建议在路由函数里调用外部 API？

参考答案：

因为路由函数的职责是选路，不是执行业务副作用。调用外部 API 应该放在明确的 node 里，然后把结果写入 State，再由路由函数根据 State 选择下一步。

### 练习 10：智能工单 Agent 里举三个适合 conditional edge 的场景

参考答案：

可以是：

1. 根据用户意图选择查订单、查知识库、创建工单或直接回答。
2. 根据工单字段是否完整选择追问用户或请求确认。
3. 根据工具调用结果选择总结回答、提示订单不存在或进入失败兜底。

## 七、自测题与答案

### 自测 1：conditional edge 的核心作用是什么？

答案：

根据当前 State 动态选择下一步节点。

### 自测 2：`add_conditional_edges()` 至少需要哪两个核心信息？

答案：

需要知道从哪个节点出发，以及用哪个路由函数决定下一步。通常还会提供 path map，让路由结果映射到真实节点。

### 自测 3：路由函数应该返回 State 更新字典吗？

答案：

不应该。路由函数返回的是路线结果，例如路线名、节点名或 `END`。返回 State 更新是 node function 的职责。

### 自测 4：本节路由函数读取了 State 的哪个字段？

答案：

读取了 `message_status`。

### 自测 5：本节 `message_status == "ready"` 时会进入哪个节点？

答案：

进入 `build_ready_reply`。

### 自测 6：本节 `message_status` 缺失时默认走哪条路线？

答案：

默认走 `blank` 路线，进入 `build_blank_reply`。

### 自测 7：为什么多个普通 outgoing edge 不是条件分支？

答案：

因为普通 outgoing edge 不表达二选一。一个节点有多个普通 outgoing edge 时，多个目标节点可能在下一轮一起执行。

### 自测 8：为什么条件分支要写测试覆盖两条路线？

答案：

因为只测一条路线不能证明另一条路线能正常运行。条件分支的错误经常藏在未覆盖的分支里。

### 自测 9：智能工单里 `classify_intent` 后面适合用什么边？

答案：

适合用 conditional edge。因为不同意图要走不同路线，比如查订单、查知识库、创建工单或直接回答。

### 自测 10：本节最核心的一句话是什么？

答案：

conditional edge 让 LangGraph 可以根据 State 动态选择下一步节点。

## 八、本节小结

本节完成了从固定流程到条件分支的第一步。

第 9 节我们学的是：

```text
edge 连接节点，表达执行路线。
```

第 10 节我们进一步学到：

```text
conditional edge 不是固定连接，而是根据 State 动态选路。
```

本节最小图现在是：

```text
START
  -> normalize_message
  -> classify_message
      -> ready -> build_ready_reply -> END
      -> blank -> build_blank_reply -> END
```

你现在应该能解释：

1. 普通 edge 用 `add_edge()`。
2. 条件 edge 用 `add_conditional_edges()`。
3. 普通 edge 适合固定路线。
4. conditional edge 适合动态路线。
5. 路由函数读取 State，返回路线结果。
6. path map 把路线结果映射到真实节点。
7. 条件分支让复杂 Agent 流程更加清楚。
8. 智能工单 Agent 后面会大量使用 conditional edge。

下一节进入：

```text
阶段 5 第 11 节：START / END / invoke / stream 图运行入口和执行方式
```

也就是：

```text
图到底怎么启动？
invoke 是一次性运行什么？
stream 为什么能看到中间过程？
START 和 END 在运行时到底起什么作用？
```

## 参考资料

- [LangGraph Graph API overview](https://docs.langchain.com/oss/python/langgraph/graph-api)
  - 用途：确认普通 edge、conditional edge、entry point、conditional entry point、多个 outgoing edge、不要混用静态路由和动态路由等核心概念。
- [LangGraph Quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart)
  - 用途：参考 `should_continue` 这类路由函数如何根据模型消息决定进入工具节点或结束。
- [LangGraph Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents)
  - 用途：参考工作流、路由、条件边、Agent 动态路线和工具调用循环的典型结构。
