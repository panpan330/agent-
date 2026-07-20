# 阶段 5 第 7 节：StateGraph 最小图

## 本节定位

前面 6 节一直在打基础：

```text
第 1 节：LangGraph 是什么，为什么现在才学
第 2 节：LangGraph / LangChain / 普通函数流程的区别
第 3 节：Agent 流程和状态机基础
第 4 节：State 是什么
第 5 节：Reducer 是什么
第 6 节：MessagesState 是什么
```

这一节开始第一次真正写 LangGraph 代码。

但我们不会一上来就做智能工单 Agent。

本节只做一个最小图：

```text
输入 user_message
-> normalize_message 节点去掉前后空格
-> build_reply 节点生成回复
-> END
```

这个图没有真实模型，没有 RAG，没有 Java API，没有工具调用。

原因是：

```text
第一个 LangGraph 图的目标不是炫功能，而是看清楚 StateGraph 的骨架。
```

你要先真正理解：

```text
State 是怎么定义的？
node 是怎么写的？
edge 是怎么连接的？
START / END 是什么？
compile() 为什么需要？
invoke() 执行后返回什么？
node 为什么只返回 State 的局部更新？
```

这些搞懂后，后面第 8-12 节再分别拆 node、edge、conditional edge、START/END、invoke/stream。

## 本节学习目标

学完这一节，你应该能做到：

1. 解释 `StateGraph` 是什么。
2. 解释为什么定义图前要先定义 State。
3. 解释 node 为什么是普通 Python 函数。
4. 解释 node 为什么读取 State 并返回局部 State 更新。
5. 解释 `START` 和 `END` 的作用。
6. 解释 `add_node()` 是把函数注册成图节点。
7. 解释 `add_edge()` 是连接节点执行顺序。
8. 解释 `compile()` 是把图定义编译成可执行图。
9. 解释 `invoke()` 是执行图并返回最终 State。
10. 解释最小图和普通函数顺序调用的区别。
11. 能运行本节 smoke 脚本，看到 StateGraph 的最终输出。
12. 能理解本节最小图以后如何扩展成智能工单 Agent。

## 本节先不学什么

为了保证第一段代码清楚，本节暂时不学这些：

1. 不调用真实大模型。
2. 不使用 `MessagesState`。
3. 不写 conditional edge。
4. 不写 graph.stream。
5. 不写 checkpoint。
6. 不写 interrupt。
7. 不调用 RAG。
8. 不调用 Java mock API。
9. 不接 FastAPI 接口。
10. 不启动 Qdrant / Milvus / VMware。

这些后面会学。

本节只实现：

```text
StateGraph 最小可运行图。
```

## 一、基础知识铺垫

### 1. 什么是图

程序里的图不是图片。

图是一种结构：

```text
节点 + 边
```

节点表示一个步骤。

边表示步骤之间的连接关系。

例如：

```text
START
  -> normalize_message
  -> build_reply
  -> END
```

这里有两个业务节点：

```text
normalize_message
build_reply
```

它们之间有三条边：

```text
START -> normalize_message
normalize_message -> build_reply
build_reply -> END
```

这就是一个最小的顺序图。

### 2. 什么是 StateGraph

`StateGraph` 可以先理解成：

```text
围绕一个共享 State 执行的图。
```

它和普通流程图不一样。

普通流程图只是画出来给人看。

`StateGraph` 是可以运行的。

它会：

```text
保存当前 State
执行 node
应用 node 返回的 State 更新
根据 edge 找到下一步
一直执行到 END
```

所以 `StateGraph` 的核心不是“图长什么样”，而是：

```text
图执行过程中 State 如何一步步变化。
```

### 3. 为什么要先定义 State

LangGraph 官方文档里，定义图的第一步就是定义 State。

原因是：

```text
所有节点和边都围绕 State 工作。
```

节点要读取 State：

```text
normalize_message 读取 user_message。
build_reply 读取 normalized_message。
```

节点要返回 State 更新：

```text
normalize_message 返回 normalized_message。
build_reply 返回 reply。
```

边以后也可能根据 State 判断下一步：

```text
如果 intent 是 rag_question，走 RAG。
如果 intent 是 create_ticket，走工单流程。
```

所以 State 是图的内部数据合同。

### 4. 什么是 node

node 是图里的执行步骤。

在 LangGraph 里，node 本质上就是一个普通 Python 函数。

它通常长这样：

```python
def some_node(state: State) -> dict:
    ...
    return {"some_key": "new value"}
```

它做三件事：

```text
读取当前 State。
执行一个明确动作。
返回 State 的局部更新。
```

本节有两个 node：

```text
normalize_message_node
build_reply_node
```

### 5. node 为什么返回局部更新

节点不要返回完整 State。

例如 `normalize_message_node` 只负责：

```text
把 user_message.strip() 得到 normalized_message。
```

所以它只返回：

```python
{
    "normalized_message": "...",
    "node_history": ["normalize_message"],
}
```

它不需要返回：

```text
user_message
reply
所有其他字段
```

这样做的好处是：

```text
节点职责清楚。
不会误覆盖其他字段。
LangGraph 可以用 reducer 合并局部更新。
stream 时更容易观察每一步更新。
```

### 6. 什么是 edge

edge 是节点之间的连线。

固定 edge 表示：

```text
A 执行完后，一定执行 B。
```

例如：

```text
normalize_message -> build_reply
```

意思是：

```text
先清洗输入，再生成回复。
```

本节还不学条件边。

条件边会在第 10 节专门学。

### 7. START 和 END 是什么

`START` 是图执行入口。

它不是你写的业务函数。

它表示：

```text
图从这里开始。
```

`END` 是图执行出口。

它表示：

```text
图到这里结束。
```

本节的流程是：

```text
START
  -> normalize_message
  -> build_reply
  -> END
```

### 8. compile 是什么

你用 `StateGraph` 定义的是图结构。

但它还不能直接执行。

需要：

```python
graph = builder.compile()
```

`compile()` 会把图定义变成可执行图。

官方文档也说明，compile 会做一些结构检查，例如有没有孤立节点，也会在这里绑定一些运行时能力，例如 checkpointer。

本节暂时不传 checkpointer。

### 9. invoke 是什么

`invoke()` 表示执行图。

例如：

```python
result = graph.invoke({"user_message": "  你好  ", "node_history": []})
```

执行过程是：

```text
初始 State:
  user_message = "  你好  "
  node_history = []

normalize_message 节点:
  写入 normalized_message = "你好"
  追加 node_history = ["normalize_message"]

build_reply 节点:
  写入 reply = "你说的是：你好"
  追加 node_history = ["build_reply"]

最终 State:
  user_message = "  你好  "
  normalized_message = "你好"
  reply = "你说的是：你好"
  node_history = ["normalize_message", "build_reply"]
```

### 10. 最小图和普通函数有什么区别

普通函数也能写：

```python
def handle(message: str) -> str:
    normalized = message.strip()
    return f"你说的是：{normalized}"
```

这当然可以。

本节的最小图并不是为了证明 LangGraph 比普通函数更适合这个小任务。

这个小任务用普通函数更简单。

本节用图的目的是学习骨架：

```text
State
node
edge
START
END
compile
invoke
```

等流程变成：

```text
意图识别
RAG
字段提取
缺失字段追问
用户确认
Java API 创建工单
错误兜底
暂停恢复
```

LangGraph 的价值才真正体现出来。

## 二、本节主题系统讲解

### 1. 本节新增了什么

本节新增和修改：

```text
projects/ai-service/pyproject.toml
projects/ai-service/uv.lock
projects/ai-service/app/agents/__init__.py
projects/ai-service/app/agents/minimal_graph.py
projects/ai-service/scripts/langgraph_minimal_graph_smoke.py
projects/ai-service/tests/test_langgraph_minimal_graph.py
```

其中最核心的是：

```text
app/agents/minimal_graph.py
```

### 2. 为什么要加 langgraph 依赖

之前项目里已经有：

```text
langchain-openai
```

但没有直接安装：

```text
langgraph
```

本节要真正使用：

```python
from langgraph.graph import END, START, StateGraph
```

所以必须把 `langgraph` 加入 `pyproject.toml`。

这次通过：

```powershell
uv add langgraph
```

加入了：

```text
langgraph>=1.2.9
```

并更新了 `uv.lock`。

### 3. app/agents 目录的意义

新增：

```text
app/agents/
```

这个目录以后会放：

```text
LangGraph 练习图
智能工单 Agent 图
Agent state
Agent nodes
```

本节先放最小图：

```text
minimal_graph.py
```

它不是最终业务 Agent。

它是学习用的最小可运行例子。

### 4. MinimalGraphState

代码：

```python
class MinimalGraphState(TypedDict, total=False):
    """State shared by the minimal LangGraph learning example."""

    user_message: str
    normalized_message: str
    reply: str
    node_history: Annotated[list[str], add]
```

逐个字段解释：

```text
user_message：输入，用户原始消息。
normalized_message：中间结果，去掉前后空格后的消息。
reply：输出，最终回复。
node_history：节点执行轨迹。
```

`node_history` 使用：

```python
Annotated[list[str], add]
```

表示：

```text
这个字段更新时不是覆盖，而是列表追加。
```

这正好复习第 5 节 reducer。

### 5. normalize_message_node

代码：

```python
def normalize_message_node(state: MinimalGraphState) -> MinimalGraphState:
    user_message = state.get("user_message", "")

    return {
        "normalized_message": user_message.strip(),
        "node_history": ["normalize_message"],
    }
```

这个节点做一件事：

```text
读取 user_message，去掉前后空格，写入 normalized_message。
```

它还追加节点历史：

```text
normalize_message
```

注意它没有直接修改 `state`：

```python
state["normalized_message"] = ...
```

而是返回局部更新。

这是 LangGraph 节点的常见写法。

### 6. build_reply_node

代码：

```python
def build_reply_node(state: MinimalGraphState) -> MinimalGraphState:
    normalized_message = state.get("normalized_message", "")
    reply = (
        f"你说的是：{normalized_message}"
        if normalized_message
        else "你还没有输入内容。"
    )

    return {
        "reply": reply,
        "node_history": ["build_reply"],
    }
```

这个节点读取：

```text
normalized_message
```

然后生成：

```text
reply
```

如果输入为空，返回：

```text
你还没有输入内容。
```

它也追加节点历史：

```text
build_reply
```

### 7. build_minimal_graph

代码：

```python
def build_minimal_graph():
    builder = StateGraph(MinimalGraphState)

    builder.add_node("normalize_message", normalize_message_node)
    builder.add_node("build_reply", build_reply_node)

    builder.add_edge(START, "normalize_message")
    builder.add_edge("normalize_message", "build_reply")
    builder.add_edge("build_reply", END)

    return builder.compile()
```

这段是本节核心。

分成 5 步看。

第一步：

```python
builder = StateGraph(MinimalGraphState)
```

创建一个围绕 `MinimalGraphState` 运行的图构建器。

第二步：

```python
builder.add_node("normalize_message", normalize_message_node)
builder.add_node("build_reply", build_reply_node)
```

把两个 Python 函数注册成图节点。

第三步：

```python
builder.add_edge(START, "normalize_message")
```

告诉图：

```text
从 START 进入 normalize_message。
```

第四步：

```python
builder.add_edge("normalize_message", "build_reply")
builder.add_edge("build_reply", END)
```

告诉图：

```text
normalize_message 执行完去 build_reply。
build_reply 执行完去 END。
```

第五步：

```python
return builder.compile()
```

把图编译成可执行对象。

### 8. minimal_graph 和 run_minimal_graph

代码：

```python
minimal_graph = build_minimal_graph()
```

这会在模块加载时构建一个可复用图。

代码：

```python
def run_minimal_graph(user_message: str) -> MinimalGraphState:
    return minimal_graph.invoke(
        {
            "user_message": user_message,
            "node_history": [],
        }
    )
```

这提供了一个更简单的调用入口。

你不用每次手写：

```python
minimal_graph.invoke(...)
```

而是：

```python
run_minimal_graph("你好")
```

### 9. 为什么初始 State 里传 node_history=[]

因为 `node_history` 使用 `operator.add` 做列表追加。

初始传：

```python
"node_history": []
```

可以让后续节点追加：

```text
["normalize_message"]
["build_reply"]
```

最终得到：

```text
["normalize_message", "build_reply"]
```

这让你能直观看到节点执行顺序。

### 10. smoke 脚本

新增：

```text
scripts/langgraph_minimal_graph_smoke.py
```

运行：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run python scripts/langgraph_minimal_graph_smoke.py
```

输出类似：

```json
{
  "user_message": "  你好，LangGraph  ",
  "normalized_message": "你好，LangGraph",
  "reply": "你说的是：你好，LangGraph",
  "node_history": [
    "normalize_message",
    "build_reply"
  ]
}
```

这说明：

```text
图执行成功。
两个节点按顺序执行。
State 被逐步更新。
node_history reducer 追加成功。
```

### 11. 为什么脚本里要处理 sys.path

脚本里有：

```python
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
```

原因是：

```text
直接运行 scripts/xxx.py 时，Python 默认会把 scripts 目录当作导入起点。
```

如果不把项目根目录加进 `sys.path`，会报：

```text
ModuleNotFoundError: No module named 'app'
```

之前你运行 RAG smoke 脚本时也遇到过类似问题。

这个写法和项目已有脚本保持一致。

### 12. 测试文件

新增：

```text
tests/test_langgraph_minimal_graph.py
```

测试了三件事：

```text
正常输入能返回更新后的 State。
空白输入能走 fallback 回复。
build_minimal_graph 可以编译出独立图。
```

测试不调用模型，不需要网络，不需要虚拟机。

### 13. 本节最小图的完整执行过程

输入：

```python
{
    "user_message": "  你好，LangGraph  ",
    "node_history": [],
}
```

进入 `normalize_message_node`：

```python
{
    "normalized_message": "你好，LangGraph",
    "node_history": ["normalize_message"],
}
```

通过 reducer 合并：

```python
{
    "user_message": "  你好，LangGraph  ",
    "normalized_message": "你好，LangGraph",
    "node_history": ["normalize_message"],
}
```

进入 `build_reply_node`：

```python
{
    "reply": "你说的是：你好，LangGraph",
    "node_history": ["build_reply"],
}
```

再次合并：

```python
{
    "user_message": "  你好，LangGraph  ",
    "normalized_message": "你好，LangGraph",
    "reply": "你说的是：你好，LangGraph",
    "node_history": ["normalize_message", "build_reply"],
}
```

到 `END`，返回最终 State。

### 14. 这个图为什么有学习价值

虽然它很简单，但已经包含 LangGraph 的核心骨架：

```text
State schema
node 函数
node 返回局部更新
reducer
START
END
add_node
add_edge
compile
invoke
测试
smoke 脚本
```

后面智能工单 Agent 只是把这些东西放大：

```text
normalize_message -> classify_intent
build_reply -> rag_answer / extract_ticket_fields / create_ticket
固定 edge -> conditional edge
简单 State -> TicketAgentState
普通 invoke -> checkpoint + thread_id + interrupt
```

## 三、本节代码和智能工单 Agent 的关系

### 1. 现在的最小图

```text
START
  -> normalize_message
  -> build_reply
  -> END
```

### 2. 后面的智能工单图

未来可能变成：

```text
START
  -> add_user_message
  -> classify_intent
  -> route_intent
     -> rag_answer
     -> extract_ticket_fields
        -> check_missing_fields
           -> ask_missing_fields
           -> ask_user_confirmation
              -> create_ticket
  -> END
```

### 3. 本节学到的东西会怎么复用

| 本节概念 | 后面智能工单 Agent 中的对应 |
| --- | --- |
| `MinimalGraphState` | `TicketAgentState` |
| `normalize_message_node` | `classify_intent_node`、`rag_answer_node` 等 |
| `build_reply_node` | `ask_confirmation_node`、`final_answer_node` |
| `node_history` reducer | messages、event_log、retrieved_sources 等 reducer |
| `START -> node` | 智能工单入口 |
| `node -> END` | 流程结束 |
| `invoke()` | 单次执行图 |

### 4. 为什么本节不接 FastAPI

本节只学 LangGraph 最小执行。

如果现在接 FastAPI，会同时出现：

```text
router
schema
request
response
dependency
graph invoke
error handling
```

学习重点会变散。

后面等图结构稳定，再接 HTTP 接口。

## 四、本节运行方式

### 1. 运行 smoke 脚本

在 PowerShell 里：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run python scripts/langgraph_minimal_graph_smoke.py
```

你应该看到 JSON 输出。

如果中文看起来乱码，先不要急着改文件。

优先怀疑 PowerShell 输出编码问题。

可以先执行：

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
```

再重新运行。

### 2. 运行本节测试

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run pytest tests/test_langgraph_minimal_graph.py
```

本节已经验证通过：

```text
3 passed
```

### 3. 运行全量测试

本节后面收尾时也会运行全量测试：

```powershell
uv run pytest
```

因为这次引入了新依赖和新包目录，需要确认没有影响旧功能。

## 五、本节练习与参考答案

### 练习 1：解释最小图的执行顺序

题目：

```text
本节最小图从哪里开始？经过哪些节点？在哪里结束？
```

参考答案：

```text
从 START 开始，进入 normalize_message 节点，再进入 build_reply 节点，最后到 END 结束。
```

### 练习 2：解释 MinimalGraphState 字段

题目：

```text
user_message、normalized_message、reply、node_history 分别表示什么？
```

参考答案：

```text
user_message 表示用户原始输入。
normalized_message 表示去掉前后空格后的消息。
reply 表示最终回复。
node_history 表示节点执行轨迹。
```

### 练习 3：node 为什么返回局部更新

参考答案：

```text
因为每个节点只负责更新自己产生的字段。返回局部更新能避免误覆盖其他 State 字段，也让 reducer 可以按字段规则合并更新。
```

### 练习 4：为什么 node_history 使用 reducer

参考答案：

```text
node_history 是节点执行历史，需要保留旧值并追加新节点名，所以用 Annotated[list[str], add] 指定列表追加 reducer。
```

### 练习 5：解释 compile 的作用

参考答案：

```text
compile() 把 StateGraph 构建器定义的图结构变成可执行图，并做基本结构检查。只有 compile 后才能 invoke 或 stream。
```

### 练习 6：解释 invoke 的输入和输出

参考答案：

```text
invoke 的输入是初始 State。图执行所有节点后，返回最终 State。最终 State 包含输入字段、节点生成的字段，以及 reducer 合并后的字段。
```

### 练习 7：空白输入为什么返回“你还没有输入内容。”

参考答案：

```text
normalize_message_node 会对 user_message 执行 strip。如果输入全是空格，normalized_message 变成空字符串。build_reply_node 检查它为空，就返回兜底回复“你还没有输入内容。”。
```

### 练习 8：为什么本节不用真实模型

参考答案：

```text
本节目标是理解 StateGraph 骨架。真实模型会带来 API key、网络、费用、错误处理和测试不稳定等额外复杂度，不适合第一个最小图。
```

### 练习 9：把本节图扩展一个节点

题目：

```text
如果要在 build_reply 前增加 detect_empty 节点，大概应该加哪几步？
```

参考答案：

```text
需要新增 detect_empty_node 函数，用 builder.add_node 注册它，然后把边从 normalize_message -> build_reply 改成 normalize_message -> detect_empty -> build_reply。后续如果要根据是否为空走不同路径，就需要 conditional edge。
```

### 练习 10：最小图和智能工单图的关系

参考答案：

```text
最小图展示了 StateGraph 的基本结构。智能工单图会使用同样的 State、node、edge、compile、invoke 思想，只是节点更多，State 更复杂，并且会加入条件边、messages、checkpoint、interrupt 和外部服务调用。
```

## 六、自测题与答案

### 自测 1：StateGraph 是什么？

答案：

```text
StateGraph 是围绕共享 State 执行的图。它用 node 表示处理步骤，用 edge 表示步骤之间的流转，并在执行过程中不断更新 State。
```

### 自测 2：START 是业务节点吗？

答案：

```text
不是。START 是图的入口标记，不是我们自己写的业务函数。
```

### 自测 3：END 是什么？

答案：

```text
END 是图的结束标记。图执行到 END 后停止，并返回最终 State。
```

### 自测 4：add_node 做什么？

答案：

```text
add_node 把一个 Python 函数注册为图中的节点，并给它一个节点名。
```

### 自测 5：add_edge 做什么？

答案：

```text
add_edge 连接两个节点，表示前一个节点执行完后进入后一个节点。
```

### 自测 6：node 函数的输入通常是什么？

答案：

```text
node 函数通常接收当前 State。
```

### 自测 7：node 函数的输出通常是什么？

答案：

```text
node 函数通常返回 State 的局部更新，例如 {"reply": "..."}。
```

### 自测 8：为什么 `node_history` 最终有两个节点名？

答案：

```text
因为 normalize_message_node 和 build_reply_node 都返回了 node_history 更新，并且 node_history 使用 operator.add reducer 追加列表。
```

### 自测 9：为什么脚本要把项目根目录加入 sys.path？

答案：

```text
直接运行 scripts/xxx.py 时，Python 的导入起点是 scripts 目录。把项目根目录加入 sys.path 后，脚本才能导入 app 包。
```

### 自测 10：本节最核心的一句话是什么？

答案：

```text
StateGraph 最小图就是先定义 State，再注册 node，用 edge 连接 START、节点和 END，compile 后通过 invoke 执行并得到最终 State。
```

## 七、本节小结

本节完成了阶段 5 第一个真正的 LangGraph 代码。

你现在已经见过：

```text
StateGraph
State schema
node
edge
START
END
compile
invoke
reducer 在图里的实际效果
```

本节最小图虽然简单，但很关键。

它证明了：

```text
LangGraph 不是只停留在概念里。
它可以把多个普通 Python 函数组织成一个围绕 State 执行的图。
```

下一节会继续深入：

```text
阶段 5 第 8 节：node 节点是什么
```

那一节会专门讲：

```text
一个 node 应该多大？
node 里应该放什么？
node 里不应该放什么？
node 如何调用普通 service？
node 如何处理错误？
```

## 参考资料

- [LangGraph Graph API overview](https://docs.langchain.com/oss/python/langgraph/graph-api)
  - 用途：确认 `StateGraph`、State、node、edge、`START`、`END`、`compile()` 的官方定义和执行模型。

- [LangGraph Quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart)
  - 用途：参考最小图如何定义 State、添加节点、添加边、编译并调用。

- [LangGraph Use the Graph API](https://docs.langchain.com/oss/python/langgraph/use-graph-api)
  - 用途：参考节点返回 State 更新、图执行、stream/update 等 Graph API 用法。
