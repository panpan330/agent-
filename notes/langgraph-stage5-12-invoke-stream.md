# 阶段 5 第 12 节：graph.invoke / graph.stream：普通执行和流式执行

## 本节定位

前面我们已经把 LangGraph 的结构学到一个关键节点：

```text
State
Reducer
MessagesState
StateGraph
node
edge
conditional edge
START
END
```

这些是在讲：

```text
图是什么。
图由什么组成。
图从哪里开始。
图在哪里结束。
```

但是一个图光定义出来还不够。

你最终一定要运行它。

本节学习两个最常用的运行方式：

```text
graph.invoke()
graph.stream()
```

可以先用一句话理解：

```text
invoke：一次性运行完整张图，最后给你最终 State。
stream：边运行边把中间过程吐出来，让你看到每一步发生了什么。
```

如果用做饭来类比：

```text
invoke：你只看到最后端上来的菜。
stream：你能看到洗菜、切菜、下锅、调味、出锅每一步。
```

真实 Agent 开发里，不能只看最终答案。

因为 Agent 很容易出现这些问题：

```text
意图识别错了
走错分支了
工具没调用
工具调用了两次
State 字段被覆盖了
某个节点没有写入预期字段
模型给了最终回答但图还在继续跑
```

如果只用 `invoke()`，你只能看到最后结果。

如果用 `stream()`，你可以看到每个节点的中间更新。

所以本节不是简单学两个 API。

本节是在学：

```text
如何观察 LangGraph 的执行过程。
```

这会直接影响你以后调试智能工单 Agent 的能力。

## 本节学习目标

学完本节，你应该能解释清楚：

1. `graph.invoke()` 是什么。
2. `graph.stream()` 是什么。
3. `invoke` 和 `stream` 的核心区别。
4. `invoke` 为什么返回最终 State。
5. `stream` 为什么适合观察中间步骤。
6. `stream_mode="updates"` 是什么。
7. `stream_mode="values"` 是什么。
8. `updates` 和 `values` 的区别。
9. 为什么本节使用 `version="v2"`。
10. 当前最小图正常输入的 stream 输出是什么路线。
11. 当前最小图 `/stop` 的 stream 输出为什么没有回复节点。
12. 智能工单 Agent 调试时为什么必须关注中间过程。

## 本节先不学什么

本节暂时不学：

1. `astream()` 异步流。
2. LLM token 级流式输出。
3. `messages` stream mode。
4. `custom` stream mode。
5. `debug` / `tasks` / `checkpoints` stream mode。
6. event streaming 的完整 typed projection。
7. checkpoint 恢复后的流式执行。
8. FastAPI SSE 流式接口。

这些后面都会用到。

但现在如果一次全讲，会把主线搞散。

本节先把最基础、最常用的两种观察方式讲透：

```text
updates：看节点更新了什么。
values：看每一步之后完整 State 变成什么。
```

## 一、基础知识铺垫

### 1. 运行图之前先明确：图不是函数，但可以像函数一样调用

普通 Python 函数是这样运行的：

```python
result = handle_message("hello")
```

你传入参数，函数内部执行，最后返回结果。

LangGraph 图也可以这样理解：

```python
result = graph.invoke({"user_message": "hello"})
```

但是图和普通函数有一个重要区别：

```text
普通函数内部执行顺序通常藏在函数代码里。
LangGraph 的执行顺序由 node + edge + conditional edge 共同决定。
```

也就是说，图运行时不是简单从上到下执行代码。

它会根据你定义的图结构走：

```text
START -> node -> edge -> node -> conditional edge -> node or END
```

所以运行图时，我们不仅关心最终结果，还关心：

```text
到底走了哪些节点？
每个节点写了哪些 State 字段？
分支是怎么选的？
在哪一步结束？
```

这就是本节要学 `stream()` 的原因。

### 2. 什么是输入 State

调用图时，你传进去的不是普通字符串，而是一个字典。

本项目里：

```python
{
    "user_message": "hello",
    "node_history": [],
}
```

这就是初始 State。

它不是完整最终 State。

它只是给图一个起点。

后面的节点会逐步补充字段：

```text
normalize_message 写入 normalized_message
classify_message 写入 message_status
build_ready_reply 写入 reply
```

最终 State 可能变成：

```python
{
    "user_message": "hello",
    "normalized_message": "hello",
    "message_status": "ready",
    "reply": "你说的是：hello",
    "node_history": [
        "normalize_message",
        "classify_message",
        "build_ready_reply",
    ],
}
```

这就是：

```text
初始 State -> 多个节点更新 -> 最终 State
```

### 3. invoke 的直观理解

`invoke()` 可以理解成：

```text
把输入交给图，让图完整跑完，然后一次性拿最终结果。
```

本项目代码：

```python
def run_minimal_graph(user_message: str) -> MinimalGraphState:
    return minimal_graph.invoke(build_minimal_graph_input(user_message))
```

它做两件事：

第一，构造初始 State：

```python
build_minimal_graph_input(user_message)
```

第二，调用图：

```python
minimal_graph.invoke(...)
```

最终返回的是：

```text
完整执行结束后的最终 State。
```

### 4. stream 的直观理解

`stream()` 可以理解成：

```text
图一边执行，一边把过程分批返回。
```

普通 `invoke()` 像：

```text
等整张图跑完再告诉我结果。
```

`stream()` 像：

```text
每跑完一步就告诉我这一步发生了什么。
```

当前最小图正常输入：

```text
START
  -> normalize_message
  -> classify_message
  -> build_ready_reply
  -> END
```

如果用 `stream_mode="updates"`，你会看到：

```text
normalize_message 更新了 normalized_message 和 node_history
classify_message 更新了 message_status 和 node_history
build_ready_reply 更新了 reply 和 node_history
```

这比最终结果更适合调试。

### 5. 为什么 Agent 开发不能只看最终结果

假设用户问：

```text
我的订单 1001 到哪了？
```

最终回答可能是：

```text
订单 1001 正在运输中。
```

看起来正确。

但你还要知道：

```text
它有没有真的调用订单工具？
有没有误走 RAG？
有没有先调用了错误工具再兜底？
有没有重复调用工具？
有没有把订单结果写进 State？
```

这些问题最终答案不一定能看出来。

所以调试 Agent 时要看中间过程：

```text
识别意图节点输出什么？
路由函数走哪条边？
工具节点返回什么？
总结节点拿到了什么上下文？
```

`stream()` 就是观察这些过程的基础工具之一。

### 6. stream_mode 是什么

`stream()` 可以输出不同类型的数据。

你用 `stream_mode` 告诉 LangGraph：

```text
我想看哪种流式信息。
```

本节只学两个：

```text
updates
values
```

官方文档里说明：

```text
updates：每一步节点写入的 State 更新。
values：每一步之后完整 State 的快照。
```

简单说：

```text
updates 看增量。
values 看全量。
```

### 7. updates 是什么

`updates` 表示：

```text
节点本次返回了哪些 State 更新。
```

比如 `normalize_message_node` 返回：

```python
{
    "normalized_message": "hello",
    "node_history": ["normalize_message"],
}
```

那么 `stream_mode="updates"` 会给你类似：

```python
{
    "type": "updates",
    "ns": (),
    "data": {
        "normalize_message": {
            "normalized_message": "hello",
            "node_history": ["normalize_message"],
        }
    },
}
```

重点是：

```text
它不是完整 State。
它只是这个节点本次写了什么。
```

如果你想知道“哪个节点写了 reply”，看 `updates` 很清楚。

### 8. values 是什么

`values` 表示：

```text
每一步执行后，当前完整 State 是什么。
```

正常输入 `"hello"` 的最后一个 `values` chunk 里会包含：

```python
{
    "user_message": "  hello  ",
    "normalized_message": "hello",
    "message_status": "ready",
    "reply": "你说的是：hello",
    "node_history": [
        "normalize_message",
        "classify_message",
        "build_ready_reply",
    ],
}
```

它更像：

```text
状态快照。
```

如果你想知道“执行到这一步时 State 累积成什么样”，看 `values` 更适合。

### 9. updates 和 values 的区别

用一句话区分：

```text
updates：这个节点刚刚写了什么。
values：这一步之后 State 总共有什么。
```

对比表：

| 对比点 | updates | values |
| --- | --- | --- |
| 关注点 | 节点增量更新 | 累积后的完整 State |
| 是否包含全部字段 | 通常不包含 | 通常包含当前完整字段 |
| 适合观察 | 哪个节点写了什么 | State 如何一步步累积 |
| 调试用途 | 定位节点输出问题 | 定位状态合并和最终状态问题 |
| 本节函数 | `stream_minimal_graph_updates()` | `stream_minimal_graph_values()` |

### 10. version="v2" 是什么

本节代码使用：

```python
version="v2"
```

原因是官方文档现在推荐 v2 输出格式。

v2 的每个 chunk 结构更统一：

```python
{
    "type": "...",
    "ns": (...),
    "data": ...,
}
```

比如：

```python
{
    "type": "updates",
    "ns": (),
    "data": {
        "normalize_message": {...}
    },
}
```

这样你不用根据不同 stream mode 猜返回结构。

学习阶段用 v2 更清楚：

```text
type 告诉你这是哪种流。
ns 告诉你命名空间，本节没有子图，所以是空元组。
data 是真正的数据。
```

注意：

如果把 Python 对象用 JSON 打印出来，空元组 `()` 会显示成空数组 `[]`。

这是 JSON 表示差异，不是乱码，也不是逻辑错误。

### 11. stream 和真正的“模型打字流”不是一回事

很多人一听流式，就想到：

```text
大模型一个字一个字输出。
```

那是 token streaming。

本节的 `graph.stream()` 不等于只做 token streaming。

它更基础：

```text
它能流式观察图运行过程。
```

可以看：

```text
State 更新
节点执行
LLM 消息
自定义进度
检查点
调试事件
```

本节只看 State 更新和 State 快照。

以后接大模型时，才会再讲 token 级流式输出。

### 12. stream 不是为了替代 invoke

不要理解成：

```text
stream 比 invoke 高级，所以以后都不用 invoke。
```

不是这样。

它们用途不同。

`invoke()` 适合：

```text
接口内部只需要最终结果
测试最终 State
命令行 smoke 快速验证
同步业务流程
```

`stream()` 适合：

```text
调试中间过程
前端展示执行进度
观察节点输出
检查 Agent 是否走错分支
做流式响应
```

真实项目里两者都会用。

### 13. 为什么本节先封装输入构造函数

本节新增：

```python
def build_minimal_graph_input(user_message: str) -> MinimalGraphState:
    return {
        "user_message": user_message,
        "node_history": [],
    }
```

原因是：

```text
invoke 和 stream 都需要同样的初始 State。
```

如果每个函数都手写：

```python
{
    "user_message": user_message,
    "node_history": [],
}
```

以后容易不一致。

比如有一天你在 `invoke` 里加了：

```python
"trace_id": "..."
```

但忘了在 `stream` 里加。

那两种运行方式的初始 State 就不一致。

所以把初始 State 单独封装，能保证：

```text
同一个输入构造逻辑，同时服务 invoke 和 stream。
```

### 14. stream 为什么返回 list

LangGraph 的 `graph.stream()` 本身返回的是迭代器。

迭代器的意思是：

```text
你可以一条一条消费输出。
```

本节封装成：

```python
return list(minimal_graph.stream(...))
```

是为了教学和测试方便。

测试里需要一次性比较完整结果：

```python
assert chunks == [...]
```

真实接口里不一定要转成 list。

比如 FastAPI SSE 流式接口里，通常会：

```text
边收到 chunk
边发给前端
```

那时就不会先 `list()` 收集完。

本节先用 list，是为了把概念讲清楚。

## 二、本节主题系统讲解

### 1. 本节代码改了什么

本节在第 11 节基础上新增了四个教学点：

```python
MinimalGraphStreamPart = dict[str, Any]
build_minimal_graph_input()
stream_minimal_graph_updates()
stream_minimal_graph_values()
```

并调整了：

```python
run_minimal_graph()
```

现在它不再自己手写初始 State，而是复用：

```python
build_minimal_graph_input(user_message)
```

这样这几个运行入口关系变成：

```text
build_minimal_graph_input
  -> run_minimal_graph
  -> stream_minimal_graph_updates
  -> stream_minimal_graph_values
```

它们不是新的业务节点。

它们是：

```text
运行和观察图的辅助函数。
```

### 2. build_minimal_graph_input 的作用

代码：

```python
def build_minimal_graph_input(user_message: str) -> MinimalGraphState:
    return {
        "user_message": user_message,
        "node_history": [],
    }
```

它负责构造初始 State。

当前最小图至少需要：

```text
user_message：用户输入
node_history：节点执行历史，初始为空列表
```

为什么 `node_history` 初始是空列表？

因为后续节点会通过 reducer 追加：

```text
normalize_message
classify_message
build_ready_reply
```

如果初始没有这个字段，某些情况下也可能能运行。

但学习阶段显式初始化更清楚：

```text
一开始没有任何节点执行过。
```

### 3. run_minimal_graph 的作用

代码：

```python
def run_minimal_graph(user_message: str) -> MinimalGraphState:
    return minimal_graph.invoke(build_minimal_graph_input(user_message))
```

这就是 invoke 版本。

它只返回最终 State。

比如：

```python
run_minimal_graph("  hello  ")
```

最终结果包含：

```python
{
    "user_message": "  hello  ",
    "normalized_message": "hello",
    "message_status": "ready",
    "reply": "你说的是：hello",
    "node_history": [
        "normalize_message",
        "classify_message",
        "build_ready_reply",
    ],
}
```

你看不到中间每一步怎么返回。

你只看到最终累积结果。

### 4. stream_minimal_graph_updates 的作用

代码：

```python
def stream_minimal_graph_updates(user_message: str) -> list[MinimalGraphStreamPart]:
    return list(
        minimal_graph.stream(
            build_minimal_graph_input(user_message),
            stream_mode="updates",
            version="v2",
        )
    )
```

它做的是：

```text
以 updates 模式流式运行最小图。
```

正常输入 `"  hello  "` 的输出是三段：

第一段：

```python
{
    "type": "updates",
    "ns": (),
    "data": {
        "normalize_message": {
            "normalized_message": "hello",
            "node_history": ["normalize_message"],
        }
    },
}
```

第二段：

```python
{
    "type": "updates",
    "ns": (),
    "data": {
        "classify_message": {
            "message_status": "ready",
            "node_history": ["classify_message"],
        }
    },
}
```

第三段：

```python
{
    "type": "updates",
    "ns": (),
    "data": {
        "build_ready_reply": {
            "reply": "你说的是：hello",
            "node_history": ["build_ready_reply"],
        }
    },
}
```

这三段正好对应三个业务节点。

所以 `updates` 很适合观察：

```text
每个节点返回了什么。
```

### 5. stream_minimal_graph_values 的作用

代码：

```python
def stream_minimal_graph_values(user_message: str) -> list[MinimalGraphStreamPart]:
    return list(
        minimal_graph.stream(
            build_minimal_graph_input(user_message),
            stream_mode="values",
            version="v2",
        )
    )
```

它做的是：

```text
以 values 模式流式运行最小图。
```

`values` 会给你每一步之后的完整 State。

比如最后一个 chunk 的 `data` 是：

```python
{
    "user_message": "  hello  ",
    "normalized_message": "hello",
    "message_status": "ready",
    "reply": "你说的是：hello",
    "node_history": [
        "normalize_message",
        "classify_message",
        "build_ready_reply",
    ],
}
```

这和 `invoke()` 的结果很像。

区别是：

```text
values 不只给最终状态。
它会在每一步后都给你状态快照。
```

### 6. 为什么本节测试 updates

测试：

```python
def test_stream_minimal_graph_updates_returns_node_updates() -> None:
    chunks = stream_minimal_graph_updates("  hello  ")
    assert chunks == [...]
```

这个测试证明：

```text
正常输入会依次经过 normalize_message、classify_message、build_ready_reply。
```

并且每个节点输出了预期字段：

```text
normalize_message -> normalized_message
classify_message -> message_status
build_ready_reply -> reply
```

这比只测最终结果更细。

如果将来某个节点没写字段，或者写错字段，这个测试会更早暴露问题。

### 7. 为什么本节测试 /stop 的 stream

测试：

```python
def test_stream_minimal_graph_updates_shows_stop_route_without_reply_node() -> None:
    chunks = stream_minimal_graph_updates("  /stop  ")
    assert chunks == [...]
```

它证明：

```text
/stop 只经过 normalize_message 和 classify_message。
```

没有：

```text
build_ready_reply
build_blank_reply
```

这比单纯检查最终结果更直观。

因为你能看到：

```text
图真的在 classify_message 后结束了。
```

### 8. 为什么本节测试 values

测试：

```python
def test_stream_minimal_graph_values_returns_accumulated_state() -> None:
    chunks = stream_minimal_graph_values("  hello  ")
    assert chunks[-1] == {...}
```

这个测试只检查最后一个 values chunk。

原因是：

```text
本节重点不是把每一步 values 全部背下来。
重点是理解 values 是累积 State。
```

最后一个 values chunk 应该和最终 State 对齐：

```text
包含 user_message
包含 normalized_message
包含 message_status
包含 reply
包含累积后的 node_history
```

这说明 `values` 看的是全量快照。

### 9. smoke 脚本为什么同时打印 invoke_result 和 stream_updates

本节修改了：

```python
scripts/langgraph_minimal_graph_smoke.py
```

现在输出结构：

```python
{
    "invoke_result": ...,
    "stream_updates": ...,
}
```

这样你在命令行运行：

```powershell
uv run python scripts/langgraph_minimal_graph_smoke.py
```

可以同时看到：

```text
最终结果是什么
每一步更新是什么
```

这比只打印最终 State 更适合学习 LangGraph。

### 10. JSON 里的 ns 为什么是 []

Python 里 `version="v2"` 的 stream chunk 里：

```python
"ns": ()
```

这是空元组。

但 `json.dumps()` 打印时，元组会被转成 JSON 数组：

```json
"ns": []
```

所以 smoke 输出里看到：

```json
"ns": []
```

不要误判成乱码或错误。

它只是：

```text
Python tuple -> JSON array
```

本节没有子图，所以命名空间为空。

## 三、当前代码逐段讲解

### 1. MinimalGraphStreamPart

```python
MinimalGraphStreamPart = dict[str, Any]
```

这是给 stream chunk 起一个简单类型别名。

为什么用 `Any`？

因为不同 stream mode 的 `data` 结构不同。

`updates` 的 `data` 是：

```python
{
    "node_name": {
        "field": "value"
    }
}
```

`values` 的 `data` 是：

```python
{
    "user_message": "...",
    "normalized_message": "...",
    ...
}
```

如果后面加 `messages` 或 `custom`，结构还会不同。

学习阶段先用：

```python
dict[str, Any]
```

保持简单。

### 2. build_minimal_graph_input

```python
def build_minimal_graph_input(user_message: str) -> MinimalGraphState:
    return {
        "user_message": user_message,
        "node_history": [],
    }
```

这段代码对学习很有帮助。

它让你明确：

```text
图不是直接吃一个字符串。
图吃的是初始 State。
```

以后智能工单 Agent 的输入可能变成：

```python
{
    "messages": [...],
    "user_message": "...",
    "trace_id": "...",
    "user_id": "...",
}
```

到时候也应该有一个统一的输入构造入口。

### 3. run_minimal_graph

```python
def run_minimal_graph(user_message: str) -> MinimalGraphState:
    return minimal_graph.invoke(build_minimal_graph_input(user_message))
```

这段代码就是普通执行。

重点是：

```text
invoke 会让图从 START 跑到 END。
```

如果中间遇到条件分支，就按条件分支走。

最后返回最终 State。

### 4. stream_minimal_graph_updates

```python
def stream_minimal_graph_updates(user_message: str) -> list[MinimalGraphStreamPart]:
    return list(
        minimal_graph.stream(
            build_minimal_graph_input(user_message),
            stream_mode="updates",
            version="v2",
        )
    )
```

逐行解释：

```python
minimal_graph.stream(...)
```

表示流式运行图。

```python
build_minimal_graph_input(user_message)
```

表示传入初始 State。

```python
stream_mode="updates"
```

表示只看节点更新。

```python
version="v2"
```

表示使用统一 chunk 格式。

```python
list(...)
```

表示把迭代器一次性收集成列表，方便测试和打印。

### 5. stream_minimal_graph_values

```python
def stream_minimal_graph_values(user_message: str) -> list[MinimalGraphStreamPart]:
    return list(
        minimal_graph.stream(
            build_minimal_graph_input(user_message),
            stream_mode="values",
            version="v2",
        )
    )
```

它和 updates 版本只有一个关键区别：

```python
stream_mode="values"
```

所以你可以这样记：

```text
同样是 stream。
不同 stream_mode 决定你看到什么。
```

### 6. 测试文件里的三种层次

本节测试现在有三种层次：

第一，测纯节点函数：

```text
normalize_message_node
classify_message_node
build_ready_reply_node
build_blank_reply_node
```

第二，测完整图最终结果：

```text
run_minimal_graph
```

第三，测完整图中间过程：

```text
stream_minimal_graph_updates
stream_minimal_graph_values
```

这是一种很好的 Agent 测试结构。

以后真实智能工单 Agent 也会这样测：

```text
单个节点逻辑
完整图最终结果
关键路线的 stream 过程
```

## 四、三条路线的 invoke 和 stream 对比

### 1. 正常输入

输入：

```python
"  hello  "
```

`invoke` 最终结果：

```python
{
    "user_message": "  hello  ",
    "normalized_message": "hello",
    "message_status": "ready",
    "reply": "你说的是：hello",
    "node_history": [
        "normalize_message",
        "classify_message",
        "build_ready_reply",
    ],
}
```

`updates` 过程：

```text
normalize_message 更新 normalized_message
classify_message 更新 message_status
build_ready_reply 更新 reply
```

适合观察：

```text
正常分支每个节点是否都执行了。
```

### 2. 空输入

输入：

```python
"   "
```

`invoke` 最终结果：

```python
{
    "normalized_message": "",
    "message_status": "blank",
    "reply": "你还没有输入内容。",
    "node_history": [
        "normalize_message",
        "classify_message",
        "build_blank_reply",
    ],
}
```

`updates` 过程：

```text
normalize_message 更新 normalized_message = ""
classify_message 更新 message_status = "blank"
build_blank_reply 更新 reply = "你还没有输入内容。"
```

适合观察：

```text
空输入是否正确走 blank 分支。
```

### 3. 停止输入

输入：

```python
"  /stop  "
```

`invoke` 最终结果：

```python
{
    "user_message": "  /stop  ",
    "normalized_message": "/stop",
    "message_status": "stop",
    "node_history": [
        "normalize_message",
        "classify_message",
    ],
}
```

没有：

```python
"reply"
```

`updates` 过程：

```text
normalize_message 更新 normalized_message = "/stop"
classify_message 更新 message_status = "stop"
```

然后直接进入：

```text
END
```

适合观察：

```text
/stop 是否真的没有进入回复节点。
```

## 五、智能工单 Agent 里的 invoke / stream

### 1. invoke 适合什么场景

智能工单 Agent 里，`invoke` 适合：

```text
后台服务只需要最终响应
单元测试验证最终 State
命令行 smoke 验证主流程
同步 API 返回最终答案
```

比如 FastAPI 接口：

```python
result = ticket_agent_graph.invoke(input_state)
return {"answer": result["final_answer"]}
```

这种场景只关心最终回答。

### 2. stream 适合什么场景

智能工单 Agent 里，`stream` 适合：

```text
前端显示执行进度
调试图路线
观察工具调用过程
定位 State 字段问题
观察多轮 Agent 是否进入循环
把节点状态实时展示给开发者
```

比如前端可以显示：

```text
正在理解问题...
正在查询订单...
正在生成回复...
```

这些都可以从 stream 事件里组织出来。

### 3. 只看最终答案可能漏掉什么问题

假设最终答案是：

```text
已为你创建工单。
```

你还需要确认：

```text
是否经过用户确认？
是否真的调用 Java 创建工单服务？
是否重复创建了两次？
是否记录了工单号？
是否写入了 trace_id？
```

这些都要看中间过程。

`stream` 能帮助你观察：

```text
request_confirmation 节点是否执行
create_ticket 节点是否执行
build_final_answer 节点是否执行
```

### 4. 未来智能工单 Agent 可能的 updates 输出

以后真实图可能有：

```text
normalize_user_input
classify_intent
retrieve_policy
query_order
extract_ticket_fields
request_confirmation
create_ticket
build_final_answer
```

`updates` 可能像：

```python
{
    "type": "updates",
    "data": {
        "classify_intent": {
            "intent": "query_order"
        }
    },
}
```

或者：

```python
{
    "type": "updates",
    "data": {
        "query_order": {
            "order": {...}
        }
    },
}
```

这样你能一步步看 Agent 到底在做什么。

### 5. stream 和日志不是一回事

stream 和 logging 都能帮助观察系统，但它们不同。

logging：

```text
主要给开发者和服务端排查问题。
```

stream：

```text
可以把运行过程返回给调用方或前端。
```

真实项目里两者都会用。

比如：

```text
stream 给前端展示“正在查询订单”
logging 记录 trace_id、耗时、错误堆栈
```

### 6. stream 和 trace 也不是一回事

trace 更偏向完整链路追踪。

比如：

```text
请求从 FastAPI 进入
调用 LangGraph
调用 LLM
调用 Java 服务
返回响应
```

stream 更偏向运行时输出。

比如：

```text
节点 A 更新了什么
节点 B 更新了什么
当前 State 是什么
```

后面学 LangGraph 可观测性时会把这些串起来。

本节先记住：

```text
stream 是观察图执行过程的直接方式。
```

## 六、常见错误

### 1. 以为 invoke 会返回每一步过程

错误理解：

```text
invoke 可以告诉我每个节点做了什么。
```

正确理解：

```text
invoke 返回最终 State。
```

如果要看过程，用：

```python
graph.stream(...)
```

### 2. 以为 stream 返回最终 State

错误理解：

```text
stream 返回的就是一个最终结果字典。
```

正确理解：

```text
stream 返回的是迭代器。
你要遍历它，才能拿到一段段 chunk。
```

### 3. 混淆 updates 和 values

错误理解：

```text
updates 和 values 差不多。
```

正确理解：

```text
updates 是节点增量更新。
values 是累积 State 快照。
```

### 4. 看见 ns 是 [] 就以为乱码

smoke 脚本 JSON 输出里：

```json
"ns": []
```

这是正常的。

Python 里原本是：

```python
"ns": ()
```

JSON 没有 tuple，所以打印成数组。

这不是中文乱码，也不是数据错误。

### 5. 测试 stream 时只看 chunk 数量

只测：

```python
assert len(chunks) == 3
```

不够。

因为数量正确，节点也可能错。

更好的测试是：

```text
检查每个 chunk 的 type
检查 data 里的节点名
检查节点更新字段
检查关键分支没有进入错误节点
```

### 6. 把 stream 当成生产日志

stream 不是日志系统。

它是运行输出机制。

生产环境仍然需要：

```text
logging
trace_id
错误堆栈
耗时统计
监控告警
```

stream 可以辅助前端展示和调试，但不能完全替代日志和 tracing。

### 7. 在真实接口里盲目 list(stream)

本节用：

```python
list(graph.stream(...))
```

是为了测试方便。

真实流式接口里，如果你先 `list()`，就会等整个图跑完才返回。

那就失去了流式意义。

真实 SSE 或 WebSocket 通常应该：

```text
边遍历 stream
边发给前端
```

### 8. 忘记 stream 也是一次图运行

`stream()` 不是“查看已经运行过的 invoke 过程”。

它本身会运行图。

也就是说：

```python
run_minimal_graph("hello")
stream_minimal_graph_updates("hello")
```

这是两次运行。

如果节点里有真实副作用，比如创建工单，两次运行可能创建两次。

所以真实项目里要非常注意副作用和幂等性。

本节最小图没有外部副作用，所以安全。

## 七、本节练习与参考答案

### 练习 1：用自己的话解释 invoke

参考答案：

`invoke` 是普通执行方式。它把初始 State 交给图，让图从 `START` 跑到 `END`，最后一次性返回最终 State。

### 练习 2：用自己的话解释 stream

参考答案：

`stream` 是流式执行方式。它会一边运行图，一边把中间过程以 chunk 的形式返回，让我们能观察每一步节点更新或 State 快照。

### 练习 3：updates 和 values 的区别是什么？

参考答案：

`updates` 看节点本次写入的增量更新，`values` 看每一步执行后的完整 State 快照。

### 练习 4：为什么本节要有 build_minimal_graph_input？

参考答案：

因为 `invoke` 和 `stream` 都需要同样的初始 State。把输入构造统一封装，可以避免不同运行方式的初始字段不一致。

### 练习 5：正常输入 `"  hello  "` 的 updates 会有几个 chunk？

参考答案：

有 3 个，分别对应：

```text
normalize_message
classify_message
build_ready_reply
```

### 练习 6：`/stop` 的 updates 为什么只有两个 chunk？

参考答案：

因为 `/stop` 经过 `normalize_message` 和 `classify_message` 后，条件边直接进入 `END`，不会进入任何回复节点。

### 练习 7：smoke 输出里 `ns: []` 是不是错误？

参考答案：

不是。Python 里 `ns` 是空元组 `()`，用 JSON 打印时会变成空数组 `[]`。本节没有子图，所以命名空间为空。

### 练习 8：真实 FastAPI 流式接口里为什么不应该先 list(stream)？

参考答案：

因为 `list(stream)` 会先把整个流收集完，等图全部跑完后才返回，失去了边执行边返回的流式效果。真实接口应该边遍历边发送。

### 练习 9：stream 会不会重新运行图？

参考答案：

会。`stream()` 本身就是一次图运行，不是查看之前 `invoke()` 的历史。因此真实有副作用的节点必须注意幂等性。

### 练习 10：智能工单 Agent 调试时为什么需要 stream？

参考答案：

因为只看最终答案看不出中间是否走错分支、是否调用工具、是否重复调用、是否写错 State。stream 可以观察每个节点的更新和执行路线，更适合调试复杂 Agent。

## 八、自测题与答案

### 自测 1：`invoke()` 返回什么？

答案：

返回图执行结束后的最终 State。

### 自测 2：`stream()` 返回什么？

答案：

返回一个可迭代的流式输出，每次迭代得到一个 chunk。

### 自测 3：`stream_mode="updates"` 看什么？

答案：

看每个节点本次返回的 State 增量更新。

### 自测 4：`stream_mode="values"` 看什么？

答案：

看每一步执行后累积形成的完整 State 快照。

### 自测 5：本节为什么使用 `version="v2"`？

答案：

因为 v2 输出格式统一，每个 chunk 都有 `type`、`ns`、`data`，学习和测试更清晰。

### 自测 6：正常输入的 updates 最后一个节点是谁？

答案：

`build_ready_reply`。

### 自测 7：空输入的 updates 最后一个节点是谁？

答案：

`build_blank_reply`。

### 自测 8：`/stop` 的 updates 最后一个节点是谁？

答案：

`classify_message`。之后直接进入 `END`。

### 自测 9：`stream()` 是否等于 LLM token 流？

答案：

不等于。`graph.stream()` 是图执行流，可以输出 State 更新、State 快照、消息、custom 数据等。LLM token 流只是其中一种更具体的流式场景。

### 自测 10：本节最核心的一句话是什么？

答案：

`invoke` 看最终结果，`stream` 看执行过程。

## 九、本节小结

本节完成了 LangGraph 基础执行方式的学习。

你现在应该能清楚区分：

```text
invoke：从 START 跑到 END，一次性返回最终 State。
stream：边运行边返回 chunk，用来观察中间过程。
updates：节点本次写了什么。
values：每一步后 State 累积成什么。
```

当前最小图有三条路线：

```text
正常输入：
normalize_message -> classify_message -> build_ready_reply

空输入：
normalize_message -> classify_message -> build_blank_reply

/stop：
normalize_message -> classify_message -> END
```

`invoke` 能告诉你最终 State。

`stream updates` 能告诉你每个节点写了什么。

`stream values` 能告诉你每一步后 State 长什么样。

这节对后面很重要。

因为智能工单 Agent 会越来越复杂。

如果你不会观察中间过程，后面遇到问题时只能猜：

```text
是不是意图错了？
是不是工具没调用？
是不是路由错了？
是不是 State 被覆盖了？
```

学会 `stream` 后，你可以用证据排查。

下一节进入：

```text
阶段 5 第 13 节：智能工单 Agent 总流程设计
```

也就是开始把前面 12 节 LangGraph 基础，真正接到智能工单 Agent v1 的业务流程上。

## 参考资料

- [LangGraph Streaming](https://docs.langchain.com/oss/python/langgraph/streaming)
  - 用途：确认 `graph.stream()`、`stream_mode`、`updates`、`values`、`version="v2"`、v2 chunk 结构，以及流式输出的官方解释。
- [LangGraph Graph API overview](https://docs.langchain.com/oss/python/langgraph/graph-api)
  - 用途：确认 State 更新、`stream_mode="updates"` 与完整 State 快照的区别，以及 Graph API 运行和状态更新基础。
- [LangGraph Use the graph API](https://docs.langchain.com/oss/python/langgraph/use-graph-api)
  - 用途：参考 `StateGraph`、State、节点、编译、调用和图执行示例，为 `invoke` / `stream` 的学习提供上下文。
