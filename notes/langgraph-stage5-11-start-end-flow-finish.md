# 阶段 5 第 11 节：START / END 和流程结束

## 本节定位

前面几节我们已经学了 LangGraph 的几个核心概念：

```text
State：图运行时共享的状态
Reducer：多个状态更新怎么合并
MessagesState：多轮消息怎么保存
StateGraph：用 State 组织一张图
node：图里的处理步骤
edge：节点之间的固定连接
conditional edge：根据 State 动态选择下一步
```

本节学习两个特殊边界：

```text
START
END
```

它们不是普通业务节点。

它们更像一张图的边界标记：

```text
START 表示图从哪里进入。
END 表示图在哪里停止。
```

如果你把 LangGraph 想成一条业务流程，那么：

```text
START 是流程入口。
END 是流程出口。
```

如果你把 LangGraph 想成一次 Agent 执行，那么：

```text
START 表示本次执行开始。
END 表示本次执行结束，并把最终 State 返回给调用方。
```

第 9 节我们已经见过：

```python
builder.add_edge(START, "normalize_message")
builder.add_edge("build_ready_reply", END)
```

第 10 节我们又见过 conditional edge：

```python
builder.add_conditional_edges(...)
```

本节要把这两类知识接起来：

```text
固定流程怎么从 START 开始？
固定流程怎么走到 END？
条件分支能不能直接走到 END？
一个图为什么必须有清楚的入口和出口？
```

本节代码新增了一个教学路线：

```text
用户输入 /stop
  -> normalize_message
  -> classify_message
  -> END
```

也就是说：

```text
/stop 不再进入任何回复节点。
它在分类后直接结束图。
```

这个例子很小，但非常重要。

因为真实智能工单 Agent 里，经常会出现：

```text
某些情况下继续执行
某些情况下直接结束
某些情况下等待用户补充
某些情况下进入人工确认
```

能不能清楚控制“继续还是结束”，是 Agent 工作流能否稳定的基础。

## 本节学习目标

学完本节，你应该能解释清楚：

1. `START` 是什么。
2. `END` 是什么。
3. 为什么 `START` / `END` 不是普通业务节点。
4. `add_edge(START, "node")` 表达什么。
5. `add_edge("node", END)` 表达什么。
6. 为什么 `set_entry_point("node")` 和 `add_edge(START, "node")` 含义相近。
7. 为什么 `set_finish_point("node")` 和 `add_edge("node", END)` 含义相近。
8. 条件边里如何直接结束流程。
9. 为什么流程要有清楚的终点。
10. 如果忘记入口或忘记结束，可能出现什么问题。
11. `/stop` 路线为什么不进入回复节点。
12. 智能工单 Agent 里哪些情况应该结束，哪些情况不能结束。

## 本节先不学什么

本节暂时不学：

1. `graph.invoke()` 的完整执行模型。
2. `graph.stream()` 的流式中间过程。
3. checkpoint 和恢复。
4. interrupt 人工确认。
5. 多轮 thread_id。
6. Agent 循环。
7. LangSmith tracing。

这些都和“图怎么运行”有关，但本节只盯住一个基础问题：

```text
图从哪里开始，在哪里结束。
```

下一节再专门学习：

```text
invoke / stream
```

也就是图怎么被真正调用，以及怎么观察中间步骤。

## 一、基础知识铺垫

### 1. 为什么一张图需要入口和出口

任何流程都要有入口和出口。

比如一个客服流程：

```text
用户发起咨询
  -> 客服理解问题
  -> 查询规则或订单
  -> 给出回复
  -> 本轮结束
```

这里：

```text
用户发起咨询
```

就是入口。

```text
本轮结束
```

就是出口。

如果没有入口，系统不知道从哪一步开始。

如果没有出口，系统不知道什么时候停止。

程序也一样。

一个普通函数有入口：

```python
def handle_message(message):
```

它也有出口：

```python
return result
```

LangGraph 是图，不是单个函数。

所以它需要用图的方式表达入口和出口：

```text
START
END
```

### 2. START 的直观理解

`START` 可以理解成：

```text
图的虚拟开始点。
```

它不是你写的业务函数。

你不会写：

```python
def START(...):
    ...
```

你也不会把它注册成普通节点：

```python
builder.add_node(START, ...)
```

它是 LangGraph 提供的特殊标记。

你用它告诉 LangGraph：

```text
本次图执行时，第一步应该进入哪个节点。
```

本节最小图里：

```python
builder.add_edge(START, "normalize_message")
```

意思是：

```text
图开始后，第一个真正执行的业务节点是 normalize_message。
```

### 3. END 的直观理解

`END` 可以理解成：

```text
图的虚拟终点。
```

它也不是你写的业务函数。

你不会写：

```python
def END(...):
    ...
```

它只是告诉 LangGraph：

```text
走到这里，本次图执行结束。
```

本节最小图里：

```python
builder.add_edge("build_ready_reply", END)
builder.add_edge("build_blank_reply", END)
```

意思是：

```text
正常回复节点执行完，图结束。
空回复节点执行完，图也结束。
```

### 4. START / END 为什么不是普通业务节点

普通业务节点有几个特点：

1. 有节点名。
2. 对应一个 Python 函数。
3. 读取 State。
4. 返回 State 更新。
5. 可以出现在业务执行历史里。

比如：

```python
builder.add_node("classify_message", classify_message_node)
```

`classify_message` 是业务节点。

它对应：

```python
def classify_message_node(...)
```

它会写入：

```python
{"message_status": "..."}
```

但 `START` / `END` 不一样。

`START` 不处理业务。

`END` 也不处理业务。

它们只是边界。

可以这样理解：

```text
START / END 是流程控制标记。
node 是业务处理步骤。
```

### 5. 入口边是什么

入口边就是从 `START` 指向第一个业务节点的边。

本节代码：

```python
(START, "normalize_message")
```

它表达：

```text
图启动后，从 normalize_message 开始。
```

为什么第一个节点是 `normalize_message`？

因为任何输入都应该先清洗：

```text
"  hello  " -> "hello"
"   " -> ""
"  /stop  " -> "/stop"
```

如果不先清洗，后面的分类会更混乱。

比如用户输入：

```text
"  /stop  "
```

如果不先 `strip()`，分类节点看到的是带空格的字符串，它就可能识别不出 `/stop`。

所以入口不是随便选的。

入口节点应该是：

```text
所有路线共同需要的第一步。
```

### 6. 结束边是什么

结束边就是从某个业务节点指向 `END` 的边。

本节代码里有：

```python
("build_ready_reply", END)
("build_blank_reply", END)
```

它们表达：

```text
回复已经生成，本轮图执行可以结束。
```

为什么不是 `classify_message -> END`？

因为普通正常输入和空输入都还需要回复：

```text
ready -> build_ready_reply -> END
blank -> build_blank_reply -> END
```

但是 `/stop` 不需要回复节点。

它可以：

```text
stop -> END
```

这就是本节新增的知识点。

### 7. 直接结束是什么意思

直接结束不是程序崩溃。

也不是没有返回值。

直接结束的意思是：

```text
图不再进入下一个业务节点。
LangGraph 把当前已经积累好的 State 作为最终结果返回。
```

本节 `/stop` 路线：

```text
START
  -> normalize_message
  -> classify_message
  -> END
```

最终 State 里有：

```python
{
    "user_message": "  /stop  ",
    "normalized_message": "/stop",
    "message_status": "stop",
    "node_history": ["normalize_message", "classify_message"],
}
```

但没有：

```python
"reply"
```

为什么没有？

因为没有进入：

```text
build_ready_reply
build_blank_reply
```

没有回复节点执行，就没有节点写入 `reply`。

### 8. 流程结束和业务成功不是同一件事

很多初学者会把“结束”理解成“成功”。

这不准确。

在工作流里：

```text
结束只表示本次流程停止。
```

结束可能有很多原因：

```text
成功完成
用户取消
输入无效
权限不足
工具失败后兜底
流程需要等待用户下次输入
```

比如智能工单 Agent：

```text
工单创建成功 -> END
用户取消创建 -> END
用户问题不属于客服范围 -> END
订单查询失败并返回兜底说明 -> END
缺少字段并向用户追问 -> 本轮也可能 END，等待下一轮用户输入
```

所以你要区分：

```text
业务成功状态
流程结束状态
```

流程结束不一定代表业务成功。

它只表示本轮图不再继续执行。

### 9. 为什么循环流程更需要 END

有些 LangGraph 不是直线，而是循环。

比如工具调用 Agent：

```text
call_model
  -> 如果模型要求调用工具，进入 tools
  -> tools 执行完再回到 call_model
  -> 如果模型不再要求工具，进入 END
```

这类流程如果没有 `END`，就可能一直循环。

所以 END 不只是“好看”。

它是循环流程的安全出口。

一个成熟 Agent 必须能回答：

```text
什么情况下继续？
什么情况下停止？
```

如果回答不了，就容易出现：

```text
一直调用模型
一直调用工具
一直追问用户
一直重试失败请求
```

这些都是生产环境里要避免的。

### 10. set_entry_point / set_finish_point 和 START / END

官方文档里还有两个方法：

```python
builder.set_entry_point("node")
builder.set_finish_point("node")
```

它们的含义接近：

```python
builder.add_edge(START, "node")
builder.add_edge("node", END)
```

本项目采用：

```python
add_edge(START, ...)
add_edge(..., END)
```

原因是：

```text
入口和出口都以 edge 的形式写出来，学习时更直观。
```

当你看到：

```python
(START, "normalize_message")
```

你能直接把它读成：

```text
图从 normalize_message 进入。
```

当你看到：

```python
("build_ready_reply", END)
```

你能直接把它读成：

```text
build_ready_reply 之后图结束。
```

这比把入口和出口藏在不同方法里更适合现在的学习阶段。

### 11. 条件分支里也可以结束

第 10 节我们学过 path map：

```python
{
    "ready": "build_ready_reply",
    "blank": "build_blank_reply",
}
```

第 11 节新增了：

```python
"stop": END
```

完整映射变成：

```python
{
    "ready": "build_ready_reply",
    "blank": "build_blank_reply",
    "stop": END,
}
```

这说明：

```text
条件边不一定要进入普通节点。
条件边也可以直接进入 END。
```

这很常见。

比如：

```text
用户取消操作 -> END
安全校验失败 -> END
模型判断不需要工具 -> END
用户输入 /stop -> END
```

### 12. END 后面还能不能继续？

在同一次图执行里，走到 `END` 后就结束。

这意味着：

```text
不会再执行后续业务节点。
```

但是这不等于整个应用永远结束。

用户下一次请求时，应用仍然可以再次调用图。

比如：

```text
第一次 invoke：用户输入 /stop -> 图结束
第二次 invoke：用户输入 hello -> 图重新从 START 开始
```

这点很重要。

`END` 结束的是：

```text
本次图执行
```

不是结束：

```text
整个程序
整个服务
所有会话
```

以后学 checkpoint 和 thread_id 时，还会进一步区分：

```text
一次执行结束
一个会话继续
一个线程恢复
```

本节先记住：

```text
END 是本次图运行的出口。
```

## 二、本节主题系统讲解

### 1. 本节代码改了什么

本节在第 10 节基础上加入了第三种消息状态：

```text
stop
```

第 10 节状态：

```python
MessageRoute = Literal["ready", "blank"]
```

第 11 节改成：

```python
MessageStatus = Literal["blank", "ready", "stop"]
MessageRoute = Literal["ready", "blank", "stop"]
```

也就是说，现在最小图有三种分类结果：

```text
ready：用户输入正常
blank：用户输入为空
stop：用户输入 /stop
```

三种结果对应三条路线：

```text
ready -> build_ready_reply -> END
blank -> build_blank_reply -> END
stop -> END
```

### 2. 为什么新增 MessageStatus

本节新增：

```python
MessageStatus = Literal["blank", "ready", "stop"]
```

它表示：

```text
消息被分类后的业务状态。
```

第 10 节里我们只有 `MessageRoute`。

第 11 节把 `MessageStatus` 单独提出来，是为了让你区分：

```text
message_status：State 里的业务状态
MessageRoute：路由函数返回的路线结果
```

在本节这个小例子里，它们刚好都用：

```text
ready / blank / stop
```

但概念上不是一回事。

真实 Agent 里可能是：

```text
State 里的业务状态：order_found / order_missing / tool_timeout
路由结果：answer_order / ask_order_id / fallback
```

它们可以相同，也可以不同。

### 3. classify_message_node 现在做什么

代码：

```python
def classify_message_node(state: MinimalGraphState) -> MinimalGraphState:
    normalized_message = state.get("normalized_message", "")
    if normalized_message == "/stop":
        message_status: MessageStatus = "stop"
    elif normalized_message:
        message_status = "ready"
    else:
        message_status = "blank"

    return {
        "message_status": message_status,
        "node_history": ["classify_message"],
    }
```

这段代码按顺序判断：

第一种：

```text
如果 normalized_message 是 /stop
```

分类为：

```text
stop
```

第二种：

```text
如果 normalized_message 不是空字符串
```

分类为：

```text
ready
```

第三种：

```text
否则
```

分类为：

```text
blank
```

为什么 `/stop` 要放在 `elif normalized_message` 前面？

因为：

```text
/stop 也是一个非空字符串。
```

如果先判断：

```python
elif normalized_message:
```

那么 `/stop` 会被当成普通 ready 输入。

这说明分支判断顺序很重要。

### 4. route_by_message_status 现在做什么

代码：

```python
def route_by_message_status(state: MinimalGraphState) -> MessageRoute:
    message_status = state.get("message_status")
    if message_status == "ready":
        return "ready"
    if message_status == "stop":
        return "stop"
    return "blank"
```

这段代码读取：

```text
message_status
```

然后返回路线：

```text
ready
stop
blank
```

注意最后：

```python
return "blank"
```

这是兜底路线。

如果 State 里没有 `message_status`，或者出现未知状态，它会走：

```text
blank
```

为什么这样设计？

因为对于这个最小图来说，不确定时不应该假装用户输入正常。

更保守的做法是提示用户输入为空。

真实项目里也会有这种原则：

```text
状态不确定时，走更安全的路线。
```

比如：

```text
用户确认状态不明确 -> 不创建工单
订单号不明确 -> 不调用订单查询
权限不明确 -> 不返回敏感信息
```

### 5. conditional routes 现在怎么读

代码：

```python
MINIMAL_GRAPH_CONDITIONAL_ROUTES: dict[MessageRoute, str] = {
    "ready": "build_ready_reply",
    "blank": "build_blank_reply",
    "stop": END,
}
```

逐行读：

```text
ready -> build_ready_reply
blank -> build_blank_reply
stop -> END
```

前两条进入普通业务节点。

第三条直接进入 `END`。

这就是本节最关键的新增点：

```text
条件边的目标可以是业务节点，也可以是 END。
```

### 6. 固定边现在表达什么

代码：

```python
MINIMAL_GRAPH_EDGES: tuple[tuple[str, str], ...] = (
    (START, "normalize_message"),
    ("normalize_message", "classify_message"),
    ("build_ready_reply", END),
    ("build_blank_reply", END),
)
```

这四条边分成两类。

第一类是入口和主干：

```text
START -> normalize_message
normalize_message -> classify_message
```

第二类是回复分支的出口：

```text
build_ready_reply -> END
build_blank_reply -> END
```

注意这里没有：

```text
classify_message -> END
```

为什么？

因为 `classify_message` 后面的路线是动态的。

它不是固定总是结束。

它可能：

```text
ready -> build_ready_reply
blank -> build_blank_reply
stop -> END
```

所以 `classify_message` 后面用的是：

```python
add_conditional_edges()
```

不是普通：

```python
add_edge()
```

### 7. `/stop` 路线的完整执行过程

输入：

```python
"  /stop  "
```

第一步，图从 `START` 进入：

```text
normalize_message
```

第二步，清洗字符串：

```text
"  /stop  " -> "/stop"
```

第三步，进入：

```text
classify_message
```

第四步，分类：

```text
message_status = "stop"
```

第五步，条件路由：

```text
route_by_message_status -> "stop"
```

第六步，path map：

```text
"stop" -> END
```

第七步，图结束。

最终执行过的业务节点只有：

```python
[
    "normalize_message",
    "classify_message",
]
```

不会执行：

```text
build_ready_reply
build_blank_reply
```

### 8. 为什么 `/stop` 不写 reply

本节测试里有：

```python
assert "reply" not in result
```

这不是遗漏。

这是为了证明：

```text
图确实在 classify_message 后结束了。
```

如果 `/stop` 还生成了 `reply`，说明它进入了回复节点。

本节要展示的是：

```text
有些路线可以不进入后续节点，直接结束。
```

所以没有 `reply` 是有意设计。

真实产品里，你可能会想返回：

```text
已停止本轮处理
```

那也可以。

但那就需要新增一个节点：

```text
build_stop_reply -> END
```

本节没有这么做，是为了让 `stop -> END` 更明显。

### 9. 三条路线对比

正常输入：

```text
START
  -> normalize_message
  -> classify_message
  -> build_ready_reply
  -> END
```

空输入：

```text
START
  -> normalize_message
  -> classify_message
  -> build_blank_reply
  -> END
```

停止输入：

```text
START
  -> normalize_message
  -> classify_message
  -> END
```

你可以看到：

```text
三条路线的入口相同。
三条路线的中间分支不同。
三条路线最终都会结束。
```

这就是图流程设计里非常常见的形态。

### 10. 为什么测试要检查 node_history

`node_history` 是我们为了学习加的观察字段。

它可以帮助你看到：

```text
到底哪些业务节点执行了。
```

本节 `/stop` 测试：

```python
assert result["node_history"] == [
    "normalize_message",
    "classify_message",
]
```

这说明：

```text
/stop 没有进入回复节点。
```

如果写错了条件边，测试可能会变成：

```python
[
    "normalize_message",
    "classify_message",
    "build_ready_reply",
]
```

那就说明 `/stop` 被错误地当成普通输入了。

所以对流程类代码来说，测试不仅要看最终字段，还要看关键路线。

### 11. START / END 和测试的关系

测试里检查：

```python
assert MINIMAL_GRAPH_EDGES == (
    (START, "normalize_message"),
    ("normalize_message", "classify_message"),
    ("build_ready_reply", END),
    ("build_blank_reply", END),
)
```

这个测试不是为了测试 LangGraph 官方库。

它测试的是：

```text
我们的教学图是否仍然保持预期结构。
```

如果以后有人把入口改成：

```text
START -> classify_message
```

测试会失败。

因为这会跳过清洗节点。

如果有人删掉：

```text
build_blank_reply -> END
```

测试也会失败。

因为空输入回复后没有明确结束。

### 12. 为什么本节不改 run_minimal_graph

`run_minimal_graph()` 仍然是：

```python
def run_minimal_graph(user_message: str) -> MinimalGraphState:
    return minimal_graph.invoke(
        {
            "user_message": user_message,
            "node_history": [],
        }
    )
```

它没有直接关心：

```text
START
END
ready
blank
stop
```

它只负责：

```text
把初始输入交给图。
```

至于图从哪里开始，在哪里结束，由图结构决定。

这就是 LangGraph 的一个重要思想：

```text
调用方提供初始 State。
图结构决定执行路线。
```

下一节讲 `invoke` 时会继续展开。

## 三、当前代码逐段讲解

### 1. 类型定义

```python
MessageStatus = Literal["blank", "ready", "stop"]
MessageRoute = Literal["ready", "blank", "stop"]
```

这两行分别表达：

```text
消息状态有哪些
路由结果有哪些
```

现在它们内容相同，但职责不同。

`MessageStatus` 是 State 字段的类型。

`MessageRoute` 是路由函数返回值的类型。

如果你要给别人讲，可以这样说：

```text
MessageStatus 说明图已经判断出用户输入是什么状态。
MessageRoute 说明下一步该走哪条路线。
```

### 2. State 字段

```python
class MinimalGraphState(TypedDict, total=False):
    user_message: str
    normalized_message: str
    message_status: MessageStatus
    reply: str
    node_history: Annotated[list[str], add]
```

本节重点看：

```python
message_status: MessageStatus
```

它现在可以是：

```text
blank
ready
stop
```

因为 `total=False`，`reply` 不是每条路线都必须存在。

这正好支持 `/stop`：

```text
/stop 路线不生成 reply
```

如果这里是严格要求所有字段必填的结构，就需要考虑 `/stop` 是否也必须写入一个 `reply`。

### 3. 分类节点

```python
if normalized_message == "/stop":
    message_status: MessageStatus = "stop"
elif normalized_message:
    message_status = "ready"
else:
    message_status = "blank"
```

这段代码体现一个很基础但很重要的规则：

```text
更具体的条件要放前面。
更宽泛的条件放后面。
```

`/stop` 是具体条件。

`normalized_message` 非空是宽泛条件。

所以先判断 `/stop`。

### 4. 路由函数

```python
message_status = state.get("message_status")
if message_status == "ready":
    return "ready"
if message_status == "stop":
    return "stop"
return "blank"
```

这段代码没有更新 State。

它只返回路线。

这就是 routing function 和 node function 的区别。

你可以把它读成：

```text
ready 继续生成正常回复。
stop 直接结束。
其他情况走空输入提醒。
```

### 5. 条件路由表

```python
MINIMAL_GRAPH_CONDITIONAL_ROUTES: dict[MessageRoute, str] = {
    "ready": "build_ready_reply",
    "blank": "build_blank_reply",
    "stop": END,
}
```

这张表是本节核心。

它把三种路由结果连接到三个目标：

```text
ready -> 普通节点
blank -> 普通节点
stop -> END
```

这说明 `END` 可以作为条件边的目标。

### 6. 图注册

```python
builder.add_conditional_edges(
    "classify_message",
    route_by_message_status,
    MINIMAL_GRAPH_CONDITIONAL_ROUTES,
)
```

完整含义：

```text
classify_message 执行完以后，
调用 route_by_message_status，
再根据 MINIMAL_GRAPH_CONDITIONAL_ROUTES 找到下一个目标。
```

如果目标是普通节点，就继续执行该节点。

如果目标是 `END`，就结束图。

### 7. 新增测试

本节新增的关键测试有三类。

第一类，检查路由表：

```python
"stop": END
```

第二类，检查路由函数：

```python
route_by_message_status({"message_status": "stop"}) == "stop"
```

第三类，检查完整执行：

```python
result = run_minimal_graph("  /stop  ")
assert "reply" not in result
assert result["node_history"] == [
    "normalize_message",
    "classify_message",
]
```

这三类测试分别覆盖：

```text
图结构
路由逻辑
运行效果
```

以后你写 Agent 流程测试时，也可以按这个思路拆。

## 四、智能工单 Agent 里的 START / END

### 1. 智能工单 Agent 的入口通常是什么

智能工单 Agent 的入口一般不是“查订单”。

也不是“创建工单”。

它通常先做通用准备：

```text
读取用户输入
清洗输入
加载会话历史
初始化 trace_id
识别用户意图
```

所以入口可能是：

```text
START -> normalize_user_input
```

或者：

```text
START -> load_context
```

或者：

```text
START -> classify_intent
```

具体选哪个，取决于项目结构。

原则是：

```text
入口节点应该是所有路线都需要的第一步。
```

### 2. 哪些情况应该进入 END

智能工单 Agent 里，以下情况通常可以进入 `END`：

```text
已经生成最终回答
已经创建工单并返回工单号
用户取消创建工单
用户输入无效且已给出提示
不支持的问题已经说明边界
工具失败且已经兜底
追问用户补充信息后等待下一轮输入
```

注意最后一个：

```text
追问用户补充信息后等待下一轮输入
```

它也可能是本轮 `END`。

因为本轮已经做完了：

```text
向用户要缺失字段
```

下一轮等用户回复后，再从 `START` 开始新的图执行，或者借助 checkpoint 恢复上下文。

### 3. 哪些情况不能太早 END

以下情况不应该太早进入 `END`：

```text
刚识别出要查订单，但还没查
刚查到订单，但还没总结给用户
刚抽取出工单字段，但还没检查缺失字段
刚发现要创建工单，但还没让用户确认
用户已确认创建，但还没调用 Java 服务
工具返回原始结果，但还没转成用户能懂的话
```

如果太早 `END`，用户会看到不完整结果。

比如：

```text
用户：我要投诉订单 1001
系统只做到：intent = create_ticket
然后 END
```

这就没有完成业务。

### 4. END 和用户确认

创建工单这种写操作，不能没有确认。

流程可能是：

```text
extract_ticket_fields
  -> check_missing_fields
  -> request_user_confirmation
  -> END
```

为什么确认后可能先 `END`？

因为系统已经把确认问题发给用户：

```text
请确认是否创建以下工单...
```

这时本轮等待用户回复。

下一轮用户说：

```text
确认
```

再进入：

```text
create_ticket
```

所以 `END` 不是“这个业务永远结束”。

它可能表示：

```text
本轮已经完成，等待用户下一轮输入。
```

### 5. END 和工具调用

工具调用流程常见结构：

```text
call_model
  -> 如果有 tool_calls，进入 tools
  -> tools 执行后回到 call_model
  -> 如果没有 tool_calls，进入 END
```

这里 `END` 的含义是：

```text
模型已经给出最终回答，不需要继续调用工具。
```

如果模型还要调用工具，就不能结束。

所以 END 经常和条件边搭配：

```text
should_continue
  -> tools
  -> END
```

这也是下一阶段真实 Agent 图里会反复出现的结构。

### 6. END 和错误处理

错误处理也需要考虑是否结束。

比如：

```text
订单服务超时
```

你可能有几种选择：

第一，重试：

```text
retry_query_order
```

第二，降级：

```text
fallback_answer
```

第三，结束：

```text
END
```

通常更合理的是：

```text
工具失败 -> fallback_answer -> END
```

而不是：

```text
工具失败 -> END
```

因为直接结束会让用户没有解释。

本节 `/stop -> END` 是教学例子。

真实用户场景里，是否直接 END 要根据产品体验决定。

## 五、常见错误

### 1. 把 START 当成普通节点

错误理解：

```text
START 是一个会执行的业务节点。
```

正确理解：

```text
START 是虚拟入口。
```

它只是告诉图：

```text
从哪里开始。
```

### 2. 把 END 当成普通节点

错误理解：

```text
END 会执行一个函数。
```

正确理解：

```text
END 是虚拟终点。
```

走到 END 后，本次图执行结束。

### 3. 忘记入口

如果没有入口，图不知道第一步执行哪个节点。

错误结构：

```text
normalize_message -> classify_message
build_ready_reply -> END
```

但没有：

```text
START -> normalize_message
```

这会导致图结构不完整。

### 4. 忘记结束

如果某条路线没有结束，也没有后续节点，流程就不清楚。

比如：

```text
ready -> build_ready_reply
```

但没有：

```text
build_ready_reply -> END
```

这会让图缺少明确出口。

### 5. 太早 END

错误：

```text
classify_intent -> END
```

如果只是识别了意图，还没有回答用户，这就结束太早。

正确做法应该是：

```text
classify_intent
  -> query_order / retrieve_policy / create_ticket
  -> build_final_answer
  -> END
```

### 6. 太晚 END

错误：

```text
已经生成最终回答
  -> 继续调用模型
  -> 继续查工具
  -> 继续循环
```

这会浪费资源，也可能引入错误。

正确做法：

```text
已经完成本轮输出 -> END
```

### 7. 不区分“本轮结束”和“会话结束”

`END` 结束的是本次图执行。

它不一定表示会话结束。

比如：

```text
系统追问：请提供订单号
本轮 END
用户下一轮提供订单号
新一轮继续
```

所以不要把 `END` 理解成：

```text
用户再也不能继续聊了。
```

### 8. 条件分支返回了 END 但忘记测试

只要条件分支可能结束，就应该测试这个分支。

本节测试 `/stop` 的原因就是：

```text
证明 stop 路线确实直接结束。
```

没有测试的话，你很难发现 `/stop` 被错误地路由到了正常回复节点。

## 六、本节练习与参考答案

### 练习 1：用自己的话解释 START

参考答案：

`START` 是 LangGraph 的虚拟入口点。它不是业务节点，也不对应业务函数。`add_edge(START, "normalize_message")` 表示图启动后第一个执行的业务节点是 `normalize_message`。

### 练习 2：用自己的话解释 END

参考答案：

`END` 是 LangGraph 的虚拟终点。它不是业务节点。图走到 `END` 后，本次执行结束，LangGraph 会把当前最终 State 返回给调用方。

### 练习 3：`START -> normalize_message` 为什么合理？

参考答案：

因为所有输入都应该先清洗。比如 `"  /stop  "` 要先变成 `"/stop"`，后面的分类节点才能正确识别停止命令。

### 练习 4：本节有哪几条路线会进入 END？

参考答案：

有三条：

```text
ready -> build_ready_reply -> END
blank -> build_blank_reply -> END
stop -> END
```

### 练习 5：`/stop` 为什么没有 `reply`？

参考答案：

因为 `/stop` 路线在 `classify_message` 后通过条件边直接进入 `END`，没有进入任何回复节点，所以没有节点写入 `reply`。

### 练习 6：`END` 是不是表示整个程序关闭？

参考答案：

不是。`END` 只表示本次图执行结束。应用服务仍然运行，用户下一次请求仍然可以再次调用图。

### 练习 7：智能工单 Agent 里举三个适合 END 的场景

参考答案：

可以是：

1. 已经生成最终回答。
2. 已经创建工单并返回工单号。
3. 已经追问用户缺失字段，等待用户下一轮补充。

### 练习 8：智能工单 Agent 里举两个不应该太早 END 的场景

参考答案：

可以是：

1. 刚识别出用户要查订单，但还没有调用订单查询工具。
2. 刚抽取出工单字段，但还没有检查字段是否完整，也没有让用户确认。

### 练习 9：`set_entry_point("x")` 和 `add_edge(START, "x")` 有什么关系？

参考答案：

它们都可以表达图的入口节点。当前项目采用 `add_edge(START, "x")`，因为入口作为边写出来更直观。

### 练习 10：为什么条件分支可以直接返回 END？

参考答案：

因为某些状态下流程不需要再进入业务节点。例如用户取消、输入停止命令、模型已经给出最终回答、权限校验失败等，这些情况下条件路由可以直接进入 `END` 结束本轮执行。

## 七、自测题与答案

### 自测 1：`START` 会执行 Python 函数吗？

答案：

不会。`START` 是虚拟入口，不是业务节点。

### 自测 2：`END` 会执行 Python 函数吗？

答案：

不会。`END` 是虚拟终点，不是业务节点。

### 自测 3：本节新增的消息状态是什么？

答案：

新增了 `stop`。

### 自测 4：`message_status == "stop"` 时，路由函数返回什么？

答案：

返回 `"stop"`。

### 自测 5：`"stop"` 在 path map 里对应什么？

答案：

对应 `END`。

### 自测 6：`/stop` 路线执行哪些业务节点？

答案：

执行：

```text
normalize_message
classify_message
```

然后进入 `END`。

### 自测 7：为什么 `/stop` 不进入 `build_ready_reply`？

答案：

因为 `classify_message_node` 会把 `"/stop"` 分类为 `stop`，路由函数返回 `stop`，path map 把 `stop` 映射到 `END`。

### 自测 8：图走到 END 后返回什么？

答案：

返回当前最终 State。

### 自测 9：END 是否等于业务成功？

答案：

不等于。END 只表示本次图执行结束。业务可能成功、取消、失败兜底或等待用户下一轮输入。

### 自测 10：本节最核心的一句话是什么？

答案：

`START` 定义图从哪里进入，`END` 定义本次图执行在哪里停止。

## 八、本节小结

本节把 LangGraph 的入口和出口讲清楚了。

你现在应该知道：

```text
START 是虚拟入口。
END 是虚拟终点。
START / END 都不是普通业务节点。
```

本节最小图现在有三条路线：

```text
正常输入：
START -> normalize_message -> classify_message -> build_ready_reply -> END

空输入：
START -> normalize_message -> classify_message -> build_blank_reply -> END

停止输入：
START -> normalize_message -> classify_message -> END
```

本节新增的关键知识是：

```text
条件边也可以直接进入 END。
```

这为后面智能工单 Agent 做准备。

以后我们会反复判断：

```text
继续执行？
进入某个业务节点？
直接结束？
等待用户下一轮输入？
```

这些问题都离不开 `START` / `END`。

下一节进入：

```text
阶段 5 第 12 节：graph.invoke / graph.stream：普通执行和流式执行
```

也就是：

```text
图怎么被调用？
invoke 一次性返回什么？
stream 怎么看到中间节点更新？
为什么调试 Agent 时 stream 很重要？
```

## 参考资料

- [LangGraph Graph API overview](https://docs.langchain.com/oss/python/langgraph/graph-api)
  - 用途：确认 edge 类型、入口边、条件边、`START` 虚拟入口、`END` 终止、`set_entry_point` / `set_finish_point` 与 `add_edge(START, ...)` / `add_edge(..., END)` 的关系。
- [LangGraph Use the graph API](https://docs.langchain.com/oss/python/langgraph/use-graph-api)
  - 用途：参考 LangGraph 如何定义 State、注册节点、设置入口、编译图、调用图，以及后续学习 invoke / stream 的官方示例。
