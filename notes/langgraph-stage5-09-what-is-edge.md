# 阶段 5 第 9 节：edge 边是什么

## 本节定位

前两节我们已经真正写了 LangGraph 最小图。

第 7 节重点是：

```text
StateGraph 最小图
```

第 8 节重点是：

```text
node 节点是什么
```

这一节继续往下讲：

```text
edge 边是什么
```

如果说 node 是“做事情的步骤”，那么 edge 就是：

```text
步骤之间的连接关系。
```

当前最小图是：

```text
START
  -> normalize_message
  -> classify_message
  -> build_reply
  -> END
```

这几条箭头就是 edge。

本节不会提前讲条件分支。

本节只讲最基础的固定边：

```text
add_edge(A, B)
```

意思是：

```text
A 执行完后，固定进入 B。
```

理解固定边非常重要。

因为后面智能工单 Agent 里有很多流程并不是每一步都需要模型判断，也不是每一步都需要条件分支。

很多地方就是明确顺序：

```text
提取字段 -> 检查缺失字段
用户确认 -> 创建工单
创建成功 -> 生成最终回复
```

这些都可以先用固定 edge 表达。

## 本节学习目标

学完这一节，你应该能做到：

1. 解释 edge 是什么。
2. 解释 node 和 edge 的区别。
3. 解释 `add_edge(A, B)` 的含义。
4. 解释为什么 `START -> node` 是入口边。
5. 解释为什么 `node -> END` 是结束边。
6. 解释固定 edge 适合表达什么样的流程。
7. 解释 edge 不应该承载复杂业务逻辑。
8. 解释 edge 写错可能出现什么问题。
9. 解释多个普通 edge 从同一个 node 出发时会发生什么。
10. 解释固定 edge 和下一节 conditional edge 的区别。
11. 能读懂本节新增的 `MINIMAL_GRAPH_EDGES`。
12. 能把智能工单 Agent 里的部分顺序流程设计成固定 edge。

## 本节先不学什么

为了把固定 edge 讲清楚，本节暂时不学：

1. 不学 `add_conditional_edges()` 的完整用法。
2. 不学 `Command` 动态跳转。
3. 不学 `Send` 并行分发。
4. 不学 checkpoint。
5. 不学 interrupt。
6. 不调用真实模型。
7. 不调用 RAG。
8. 不调用 Java mock API。
9. 不接 FastAPI 新接口。
10. 不启动 Qdrant / Milvus / VMware。

下一节会专门学：

```text
conditional edge 条件分支
```

本节只把固定边学扎实。

## 一、基础知识铺垫

### 1. 先回顾 node

上一节我们说：

```text
node 是图里的单一职责处理步骤。
```

例如：

```text
normalize_message：清洗用户输入
classify_message：判断输入状态
build_reply：生成回复
```

每个 node 只负责做一件明确的事。

但光有 node 不够。

如果只有三个 node：

```text
normalize_message
classify_message
build_reply
```

LangGraph 不知道：

```text
谁先执行？
谁后执行？
执行完 normalize_message 应该去哪？
什么时候结束？
```

这就需要 edge。

### 2. edge 的直观理解

edge 可以理解成：

```text
从一个节点到另一个节点的路。
```

例如：

```text
normalize_message -> classify_message
```

意思是：

```text
normalize_message 执行完，下一步执行 classify_message。
```

再例如：

```text
build_reply -> END
```

意思是：

```text
build_reply 执行完，流程结束。
```

### 3. node 和 edge 的区别

一句话：

```text
node 做事情，edge 连接事情。
```

| 概念 | 负责什么 | 例子 |
| --- | --- | --- |
| node | 执行动作，更新 State | 清洗输入、提取字段、调用 Java API |
| edge | 决定执行顺序 | A 后面执行 B |

不要把这两个职责混在一起。

如果把所有流程控制都写进 node，图会变得不清楚。

如果把业务逻辑塞进 edge，也会让流程难维护。

### 4. 固定边是什么

固定边就是：

```text
无论 State 是什么，都固定从 A 到 B。
```

代码：

```python
builder.add_edge("node_a", "node_b")
```

含义：

```text
node_a 执行完后，node_b 一定执行。
```

本节最小图里的这些都是固定边：

```text
START -> normalize_message
normalize_message -> classify_message
classify_message -> build_reply
build_reply -> END
```

### 5. 什么场景适合固定边

固定边适合流程顺序确定的场景。

例如：

```text
清洗输入 -> 判断输入状态
字段提取 -> 检查缺失字段
创建工单 -> 生成最终回复
写日志 -> 返回结果
```

这些流程不需要动态选择。

只要前一步做完，后一步就一定要做。

这就是固定边的用途。

### 6. 什么场景不适合固定边

如果下一步取决于 State，就不适合只用固定边。

例如：

```text
intent = rag_question -> rag_answer
intent = create_ticket -> extract_ticket_fields
intent = unknown -> fallback
```

这里下一步不是固定的。

需要条件分支。

下一节会学：

```text
conditional edge
```

### 7. START 是什么

`START` 是 LangGraph 的虚拟入口节点。

它不是你写的业务 node。

它表示：

```text
图从哪里开始。
```

代码：

```python
builder.add_edge(START, "normalize_message")
```

意思是：

```text
图开始执行时，先进入 normalize_message。
```

官方文档也说明，可以从虚拟 `START` 节点连到第一个要执行的节点。

### 8. END 是什么

`END` 是 LangGraph 的终止节点。

它也不是你写的业务 node。

它表示：

```text
图执行到这里停止。
```

代码：

```python
builder.add_edge("build_reply", END)
```

意思是：

```text
build_reply 执行完后，没有后续动作，图结束。
```

### 9. set_entry_point 和 add_edge(START, node)

有些旧例子或其他资料里，你可能看到：

```python
builder.set_entry_point("node_a")
```

它表示设置入口节点。

现代写法更推荐：

```python
builder.add_edge(START, "node_a")
```

这样入口也用 edge 表达，整个图更统一。

同理：

```python
builder.set_finish_point("node_a")
```

可以理解为：

```python
builder.add_edge("node_a", END)
```

本项目采用：

```text
START / END + add_edge
```

### 10. edge 写错会怎样

edge 写错会导致流程错误。

例如：

```text
START -> build_reply
```

如果跳过 `normalize_message` 和 `classify_message`，`build_reply` 可能拿不到需要的 State。

再例如：

```text
normalize_message -> END
```

流程会过早结束，不会生成 reply。

再例如漏掉：

```text
build_reply -> END
```

图可能无法正确结束，编译时也可能检查出结构问题。

### 11. edge 不应该承载复杂业务逻辑

固定 edge 不应该写业务判断。

例如不要试图把这些逻辑塞进固定 edge：

```text
如果用户要创建工单，就去 create_ticket。
如果用户问知识库，就去 rag_answer。
```

固定 edge 只表达：

```text
A 后面固定是 B。
```

如果有条件，就留给 conditional edge。

### 12. 一个 node 有多条普通 edge 会怎样

官方文档提醒：

```text
一个 node 可以有多个 outgoing edges。
如果一个 node 有多条普通边，目标节点会在下一轮 super-step 并行执行。
```

例如：

```text
node_a -> node_b
node_a -> node_c
```

这不是“二选一”。

它表示：

```text
node_b 和 node_c 都会执行。
```

所以不要用多条普通 edge 表达分支选择。

要表达二选一，应该用：

```text
conditional edge
```

### 13. 不要混用普通 edge 和动态路由

官方文档还提醒：

```text
同一个 node 最好选择一种路由机制。
```

也就是说：

```text
要么用普通 edge 表达固定路线。
要么用 conditional edge / Command 表达动态路线。
```

不要在同一个 node 后面既有普通 edge，又有动态 goto。

否则两条路径都可能执行，流程会变难理解。

### 14. edge 和业务流程图的关系

业务流程图里你画的箭头，落到 LangGraph 里通常就是 edge。

例如智能工单流程图：

```text
提取字段 -> 检查缺失字段
```

落到代码：

```python
builder.add_edge("extract_ticket_fields", "check_missing_fields")
```

但是业务流程图里的“条件箭头”：

```text
字段齐全 -> 用户确认
字段缺失 -> 追问用户
```

落到代码就不是普通 edge，而是 conditional edge。

## 二、本节主题系统讲解

### 1. 本节代码改了什么

本节没有改变最小图的运行结果。

但把 edge 显式整理出来：

```python
MINIMAL_GRAPH_EDGES: tuple[tuple[str, str], ...] = (
    (START, "normalize_message"),
    ("normalize_message", "classify_message"),
    ("classify_message", "build_reply"),
    ("build_reply", END),
)
```

然后在构建图时遍历：

```python
for start_node, end_node in MINIMAL_GRAPH_EDGES:
    builder.add_edge(start_node, end_node)
```

这个改动的目的不是炫技巧。

它的教学意义是：

```text
把边从一串 add_edge 调用里抽出来，让你直接看到这张图的固定执行路线。
```

### 2. MINIMAL_GRAPH_EDGES 怎么读

这一组 tuple 可以从上到下读：

```text
START -> normalize_message
normalize_message -> classify_message
classify_message -> build_reply
build_reply -> END
```

它就是当前最小图的流程定义。

### 3. 为什么用 tuple

这里用：

```python
tuple[tuple[str, str], ...]
```

表示：

```text
这是一组固定边。
每条边是一个二元组。
二元组第一个元素是起点，第二个元素是终点。
```

例如：

```python
("classify_message", "build_reply")
```

意思是：

```text
classify_message 执行完后，进入 build_reply。
```

### 4. 为什么不把 edge 放到 node 里

不要在 node 里写：

```python
def classify_message_node(state):
    ...
    next_node = "build_reply"
```

本节是固定流程。

固定流程应该写在 graph 结构里。

node 负责：

```text
读取 State，做动作，返回更新。
```

edge 负责：

```text
连接 node。
```

这样职责清楚。

### 5. build_minimal_graph 现在做什么

当前构建逻辑：

```python
def build_minimal_graph():
    builder = StateGraph(MinimalGraphState)

    builder.add_node("normalize_message", normalize_message_node)
    builder.add_node("classify_message", classify_message_node)
    builder.add_node("build_reply", build_reply_node)

    for start_node, end_node in MINIMAL_GRAPH_EDGES:
        builder.add_edge(start_node, end_node)

    return builder.compile()
```

它分成三部分：

```text
1. 创建 StateGraph。
2. 注册 node。
3. 注册 edge。
4. compile。
```

这就是最小图构建的基本结构。

### 6. 为什么新增 edge 测试

测试：

```python
def test_minimal_graph_edges_define_fixed_execution_order() -> None:
    assert MINIMAL_GRAPH_EDGES == (
        (START, "normalize_message"),
        ("normalize_message", "classify_message"),
        ("classify_message", "build_reply"),
        ("build_reply", END),
    )
```

这个测试不是为了测 LangGraph 源码。

它是在测：

```text
我们这个学习图的固定流程有没有被改乱。
```

如果以后有人把边改成：

```text
START -> build_reply
```

测试会提醒流程变了。

### 7. edge 和 node_history 的区别

`MINIMAL_GRAPH_EDGES` 是图的静态结构。

它表示：

```text
图被设计成什么样。
```

`node_history` 是运行结果。

它表示：

```text
这次执行实际走过哪些 node。
```

当前固定图里，两者会对应。

但以后有条件分支时：

```text
图里可能有很多边。
一次运行只会走其中一部分边。
```

所以要区分：

```text
edge 定义的是可能路线。
node_history 记录的是实际路线。
```

### 8. edge 和 State 的关系

固定 edge 不看 State。

无论 State 是：

```text
message_status = ready
```

还是：

```text
message_status = blank
```

当前图都会走：

```text
classify_message -> build_reply
```

这就是固定 edge。

下一节 conditional edge 会根据 State 选择下一步。

例如：

```text
message_status = ready -> build_reply
message_status = blank -> ask_for_input
```

### 9. 当前图为什么仍然用固定 edge

本节明明有：

```text
message_status = blank / ready
```

为什么没有马上做条件分支？

因为本节目标是固定 edge。

无论输入是否为空，当前都进入 `build_reply`，由 `build_reply_node` 根据 `message_status` 生成不同回复。

下一节我们再把分支逻辑迁移到 conditional edge，学习：

```text
根据 State 选择不同节点。
```

### 10. edge 的命名问题

edge 本身通常没有名字。

它由起点和终点表达：

```text
("normalize_message", "classify_message")
```

所以 node 名称要清楚。

因为 edge 的可读性依赖 node 名称。

如果 node 都叫：

```text
node1 -> node2 -> node3
```

edge 也看不懂。

如果 node 叫：

```text
normalize_message -> classify_message -> build_reply
```

流程就很清楚。

## 三、当前代码逐段讲解

### 1. MINIMAL_GRAPH_EDGES

代码：

```python
MINIMAL_GRAPH_EDGES: tuple[tuple[str, str], ...] = (
    (START, "normalize_message"),
    ("normalize_message", "classify_message"),
    ("classify_message", "build_reply"),
    ("build_reply", END),
)
```

逐条解释：

```text
START -> normalize_message：
  图启动后先清洗输入。

normalize_message -> classify_message：
  清洗完后判断消息状态。

classify_message -> build_reply：
  判断完后生成回复。

build_reply -> END：
  回复生成后结束。
```

### 2. for 循环注册 edge

代码：

```python
for start_node, end_node in MINIMAL_GRAPH_EDGES:
    builder.add_edge(start_node, end_node)
```

这和手写四行效果一样：

```python
builder.add_edge(START, "normalize_message")
builder.add_edge("normalize_message", "classify_message")
builder.add_edge("classify_message", "build_reply")
builder.add_edge("build_reply", END)
```

为什么现在用循环？

因为本节要突出：

```text
edge 是一组流程连接关系。
```

### 3. 测试固定边

新增测试：

```python
test_minimal_graph_edges_define_fixed_execution_order
```

它直接断言 `MINIMAL_GRAPH_EDGES` 的内容。

这可以帮助你把图结构当作可测试对象。

后面流程复杂时，这类测试可以防止误改主流程。

### 4. 原有执行测试仍然保留

除了 edge 测试，本节还保留了：

```text
正常输入测试
空白输入测试
独立编译图测试
node 单元测试
```

这说明我们同时验证：

```text
静态结构是对的。
运行结果是对的。
每个 node 自身也是对的。
```

## 四、智能工单 Agent 里的固定 edge

### 1. 哪些地方适合固定 edge

智能工单 Agent 里有些步骤顺序非常明确。

例如：

```text
extract_ticket_fields -> check_missing_fields
```

字段提取后，肯定要检查是否缺字段。

再例如：

```text
create_ticket -> build_ticket_created_answer
```

创建工单成功后，通常要生成最终答复。

这些适合固定 edge。

### 2. 哪些地方不适合固定 edge

这些地方不适合固定 edge：

```text
classify_intent 后走 RAG 还是工单？
check_missing_fields 后追问还是确认？
等待用户确认后创建还是取消？
Java API 失败后重试还是 fallback？
```

这些要看 State。

应该用 conditional edge 或更高级的控制方式。

### 3. 初版智能工单固定边示例

未来可能有：

```text
START -> add_user_message
add_user_message -> classify_intent
extract_ticket_fields -> check_missing_fields
create_ticket -> build_final_answer
build_final_answer -> END
```

这些都是固定顺序。

### 4. 初版智能工单条件边示例

未来可能有：

```text
classify_intent -> route_by_intent
  rag_question -> rag_answer
  create_ticket -> extract_ticket_fields
  unknown -> fallback

check_missing_fields -> route_by_missing_fields
  missing -> ask_missing_fields
  complete -> ask_user_confirmation
```

这些是下一节内容。

### 5. 固定 edge 让主干流程稳定

一个复杂 Agent 不应该所有步骤都动态跳来跳去。

稳定的主干流程应该用固定 edge 表达。

动态分支只放在真正需要选择的地方。

这样图更容易解释、测试和维护。

## 五、edge 常见错误

### 1. 忘记入口边

错误：

```text
没有 START -> first_node
```

问题：

```text
图不知道从哪里开始。
```

正确：

```python
builder.add_edge(START, "normalize_message")
```

### 2. 忘记结束边

错误：

```text
最后一个 node 没有连到 END。
```

问题：

```text
图可能无法正确终止。
```

正确：

```python
builder.add_edge("build_reply", END)
```

### 3. 边顺序写错

错误：

```text
START -> build_reply -> normalize_message
```

问题：

```text
build_reply 执行时还没有 normalized_message。
```

### 4. 用多条普通 edge 表达二选一

错误：

```python
builder.add_edge("classify_intent", "rag_answer")
builder.add_edge("classify_intent", "extract_ticket_fields")
```

如果这是普通 edge，两个节点都可能执行。

如果你想表达二选一，应该用 conditional edge。

### 5. 同一个 node 混用普通 edge 和动态路由

如果一个 node 后面既有：

```text
普通 edge
```

又返回：

```text
Command(goto=...)
```

或者有 conditional edge，就容易让多条路径同时执行。

原则：

```text
同一个 node 后面尽量选择一种路由机制。
```

### 6. 把业务判断藏在 edge 注册里

固定 edge 注册不要写复杂业务判断。

不要把 graph 构建写成：

```python
if user_is_vip:
    builder.add_edge(...)
```

图结构通常应该在启动时确定。

运行时分支应该通过 State 和 conditional edge 解决。

## 六、本节练习与参考答案

### 练习 1：解释 edge 是什么

参考答案：

```text
edge 是图中节点之间的连接关系，表示一个节点执行完后下一步应该去哪里。
```

### 练习 2：node 和 edge 的区别

参考答案：

```text
node 负责执行动作和更新 State，edge 负责连接节点和决定执行顺序。node 做事，edge 指路。
```

### 练习 3：解释 `add_edge("a", "b")`

参考答案：

```text
它表示 a 节点执行完后，固定进入 b 节点。
```

### 练习 4：解释 `add_edge(START, "normalize_message")`

参考答案：

```text
它表示图启动后，第一个执行的业务节点是 normalize_message。
```

### 练习 5：解释 `add_edge("build_reply", END)`

参考答案：

```text
它表示 build_reply 执行完后图结束，不再执行其他节点。
```

### 练习 6：当前最小图有几条 edge

参考答案：

```text
4 条：
START -> normalize_message
normalize_message -> classify_message
classify_message -> build_reply
build_reply -> END
```

### 练习 7：为什么不能用两条普通 edge 表达二选一

参考答案：

```text
因为普通 edge 不是选择关系。如果一个 node 有多条普通 outgoing edge，多个目标节点可能都会在下一轮执行。二选一应该用 conditional edge。
```

### 练习 8：智能工单里哪些适合固定 edge

参考答案：

```text
extract_ticket_fields -> check_missing_fields
create_ticket -> build_final_answer
build_final_answer -> END
```

这些步骤顺序比较确定。

### 练习 9：智能工单里哪些不适合固定 edge

参考答案：

```text
classify_intent 后选择 rag_answer、extract_ticket_fields 或 fallback。
check_missing_fields 后选择 ask_missing_fields 或 ask_user_confirmation。
用户确认后选择 create_ticket 或 done。
```

这些都需要根据 State 分支。

### 练习 10：为什么本节没有直接学 conditional edge

参考答案：

```text
因为固定 edge 是图连接的基础。先理解 A 固定到 B，再学根据 State 动态选择 B 或 C，学习顺序更清楚。
```

## 七、自测题与答案

### 自测 1：edge 的核心作用是什么？

答案：

```text
连接节点，决定节点之间的执行顺序和图什么时候结束。
```

### 自测 2：固定 edge 看 State 吗？

答案：

```text
不看。固定 edge 表示无论当前 State 如何，都从 A 进入 B。
```

### 自测 3：`START` 是你写的业务节点吗？

答案：

```text
不是。START 是 LangGraph 的虚拟入口节点。
```

### 自测 4：`END` 是你写的业务节点吗？

答案：

```text
不是。END 是 LangGraph 的终止节点。
```

### 自测 5：`set_entry_point("x")` 和 `add_edge(START, "x")` 有什么关系？

答案：

```text
都可以表达入口节点。当前项目采用 add_edge(START, "x") 这种更统一的写法。
```

### 自测 6：一个 node 有两条普通 outgoing edge 是二选一吗？

答案：

```text
不是。多个目标节点可能都会执行。二选一需要 conditional edge。
```

### 自测 7：本节新增的常量是什么？

答案：

```text
MINIMAL_GRAPH_EDGES。
```

### 自测 8：MINIMAL_GRAPH_EDGES 表达什么？

答案：

```text
表达当前最小图的固定边列表，也就是固定执行路线。
```

### 自测 9：edge 和 node_history 有什么区别？

答案：

```text
edge 是图的静态结构，表示可能路线；node_history 是一次运行的实际执行轨迹。
```

### 自测 10：本节最核心的一句话是什么？

答案：

```text
edge 是节点之间的连接关系，固定 edge 用来表达 A 执行完后一定进入 B 的确定顺序。
```

## 八、本节小结

本节把第 8 节的最小图继续整理为显式固定边：

```text
MINIMAL_GRAPH_EDGES = (
    START -> normalize_message,
    normalize_message -> classify_message,
    classify_message -> build_reply,
    build_reply -> END,
)
```

你需要真正记住：

```text
node 做事，edge 指路。
固定 edge 不看 State。
START 表示图入口。
END 表示图出口。
add_edge(A, B) 表示 A 执行完固定进入 B。
多条普通 outgoing edge 不是二选一。
需要二选一时用 conditional edge。
同一个 node 后面不要混乱地同时使用普通 edge 和动态路由。
```

下一节会进入：

```text
阶段 5 第 10 节：conditional edge 条件分支
```

那一节会把当前图继续推进：

```text
message_status = ready -> build_reply
message_status = blank -> ask_for_input
```

也就是让图真正根据 State 选择下一步。

## 参考资料

- [LangGraph Graph API overview](https://docs.langchain.com/oss/python/langgraph/graph-api)
  - 用途：确认 edge 的类型、普通边、条件边、入口边、`START`、`END`、多条 outgoing edge 和路由机制选择原则。

- [LangGraph Use the Graph API](https://docs.langchain.com/oss/python/langgraph/use-graph-api)
  - 用途：参考 `add_edge(START, node)`、`add_edge(node, END)`、顺序节点和图编译执行的实际写法。
