# 阶段 5 第 21 节：checkpoint 和 thread_id：中断、恢复、继续对话

## 本节定位

第 20 节我们完成了：

```text
字段完整
-> 请求用户确认
-> 如果 ticket_confirmation_approved=True
-> 调用 Java mock 创建工单
```

但第 20 节有一个明显的学习阶段限制：

```text
ticket_confirmation_approved=True 是我们直接放进同一次 State 里的。
```

真实对话不是这样。

真实对话通常是两轮：

```text
第 1 轮：
用户：我要投诉订单 1001，物流一直不动
Agent：我已整理好待确认工单，请确认是否创建

第 2 轮：
用户：确认创建
Agent：找到上一轮待确认工单，继续创建，返回工单号
```

第 21 节要解决的问题就是：

```text
Agent 如何记住上一轮的 State，并在下一轮继续执行。
```

这就要学：

```text
checkpoint
thread_id
```

本节先用内存版 checkpointer 学机制，不接数据库持久化，也不直接使用 `interrupt()`。真正的 `interrupt()` 会放到下一节。

## 本节学习目标

学完本节，你应该能讲清楚：

1. 什么是 checkpoint。
2. 什么是 thread_id。
3. checkpoint 和普通变量有什么区别。
4. thread_id 为什么不是用户输入内容。
5. 为什么多轮 Agent 必须保存 State。
6. 为什么 `MemorySaver` 只适合学习和测试。
7. `graph.invoke(input, config=...)` 里的 config 是什么。
8. 为什么同一个 thread_id 能找回上一轮状态。
9. 为什么不同 thread_id 的状态必须隔离。
10. `graph.get_state(config)` 能做什么。
11. `graph.update_state(config, values, as_node=...)` 能做什么。
12. 为什么确认后恢复时使用 `as_node="request_ticket_confirmation"`。
13. 为什么恢复执行时可以调用 `graph.invoke(None, config=...)`。
14. checkpoint 和 interrupt 的关系。
15. 本节和下一节 human-in-the-loop 的衔接。

## 本节先不学什么

本节暂时不学：

1. 不直接使用 `interrupt()`。
2. 不使用 `Command(resume=...)`。
3. 不接 PostgreSQL checkpointer。
4. 不接 SQLite checkpointer。
5. 不做生产级会话表。
6. 不做前端会话管理。
7. 不做登录态和用户鉴权。
8. 不把 checkpoint 存进 Redis 或数据库。
9. 不处理多个并发确认。
10. 不做长时间过期清理。

本节只解决一个基础问题：

```text
用 thread_id 找回同一条 Agent 线程的 State，并从待确认节点后继续执行。
```

## 一、基础知识铺垫

### 1. 为什么 Agent 需要记住上一轮

普通函数调用是一次性的。

例如：

```python
result = run_ticket_agent("我要投诉订单 1001，物流一直不动")
```

这次运行结束后，如果没有额外保存，程序不会天然记得：

1. 刚才识别出的意图是什么。
2. 刚才提取出的订单号是什么。
3. 刚才生成的待确认工单是什么。
4. 刚才流程停在哪里。
5. 用户下一句“确认创建”到底是在确认哪一件事。

但对话式 Agent 必须记住这些信息。

否则第二轮用户说：

```text
确认创建
```

Agent 只看这一句话，会很难知道：

```text
确认创建什么？
哪个订单？
什么问题？
要调用哪个工具？
之前有没有请求过确认？
```

所以多轮 Agent 的基础能力是：

```text
保存上一轮 State。
```

### 2. 什么是 State

在我们当前项目里，State 是：

```python
TicketAgentState
```

它保存了当前 Agent 流程中的关键信息，比如：

```text
user_message
normalized_message
intent
ticket_fields
pending_ticket_confirmation
ticket_confirmation_approved
created_ticket
final_answer
node_history
```

可以把 State 理解成：

```text
Agent 当前这条流程的工作台。
```

节点不是靠全局变量互相传信息，而是读写 State。

### 3. 什么是 checkpoint

checkpoint 可以理解为：

```text
某一条 Agent 线程在某个时间点的 State 快照。
```

比如第 1 轮用户发起工单后，流程停在确认节点，State 里有：

```text
pending_ticket_confirmation = {...}
final_answer = 请确认是否创建...
node_history = [...]
```

如果图启用了 checkpointer，LangGraph 会把这些状态保存成 checkpoint。

下次同一个 thread_id 再来时，就能找回这些状态。

所以 checkpoint 的作用是：

```text
让图执行结果不只存在于这一次函数调用里。
```

### 4. checkpoint 和普通变量的区别

普通变量通常只存在于当前函数或当前对象里。

例如：

```python
state = {"pending_ticket_confirmation": "..."}
```

如果函数结束后你没有保存它，它就没法被下一次请求可靠找回。

checkpoint 是 LangGraph 提供的状态保存机制。

它知道：

1. 这条线程的 State 是什么。
2. 每一步节点写入了什么。
3. 下一步可以从哪里继续。
4. 这份 State 属于哪个 thread_id。

所以 checkpoint 更像：

```text
LangGraph 运行时维护的线程状态记录。
```

### 5. checkpoint 保存的不只是聊天记录

很多人第一次学 Agent 记忆时，会以为：

```text
记忆 = 保存聊天记录
```

这只说对了一小部分。

聊天记录当然重要，但 LangGraph 的 checkpoint 保存的是图的 State，不只是几条 message。

在我们的工单 Agent 里，真正需要保存的是：

```text
pending_ticket_confirmation
ticket_fields
ticket_need_source
ticket_confirmation_required
node_history
final_answer
```

这些东西里，只有 `final_answer` 比较像聊天内容。

其他字段都是业务流程状态。

如果只保存聊天文本，第二轮用户说“确认创建”时，系统仍然要重新从文字里猜：

```text
之前的订单号是什么？
之前提取的问题类型是什么？
之前的确认 ID 是什么？
之前是不是已经生成过待确认工单？
```

这会让流程变得不稳定。

checkpoint 的价值在于：

```text
保存结构化状态，而不是只保存自然语言。
```

这点对 Agent 工程化非常重要。

LLM 可以读聊天记录，但业务系统更需要结构化 State。

### 6. checkpoint 解决的是短期流程记忆

checkpoint 不是万能数据库。

它主要解决的是：

```text
同一条 thread 内，图流程如何继续。
```

比如：

```text
第 1 轮生成待确认工单
第 2 轮确认创建
第 3 轮查看创建结果
```

这些都属于同一条短期流程。

checkpoint 很适合保存：

1. 这一轮图执行到了哪里。
2. 当前 State 是什么。
3. 下一步可以从哪里继续。
4. 这条 thread 的中间结果是什么。

但它不适合直接当成：

1. 用户长期资料库。
2. 企业知识库。
3. 工单正式数据库。
4. 订单正式数据库。
5. 审计日志系统。

所以你要建立一个边界意识：

```text
checkpoint 保存 Agent 流程状态。
业务数据库保存正式业务数据。
```

### 7. 什么是 thread_id

thread_id 是：

```text
一条对话线程或一条 Agent 流程的唯一标识。
```

它不是用户说的话。

它也不是工单号。

它是用来告诉 checkpointer：

```text
我要读写哪一条线程的 State。
```

官方文档也强调，传入：

```python
{"configurable": {"thread_id": "thread-1"}}
```

就是告诉 LangGraph 当前运行属于哪条线程。

同一个 thread_id：

```text
复用同一条线程状态。
```

不同 thread_id：

```text
互相隔离，互不影响。
```

### 8. thread_id 和用户 ID 的区别

初学者很容易把 thread_id 和 user_id 混在一起。

它们不是一回事。

`user_id` 表示：

```text
哪个用户。
```

`thread_id` 表示：

```text
这个用户的哪一次对话或哪一条流程。
```

一个用户可能同时有多个 thread：

```text
thread-001：咨询退款
thread-002：投诉物流
thread-003：账号安全问题
```

所以生产系统里通常是：

```text
user_id 负责身份
thread_id 负责对话线程
```

### 9. thread_id 应该怎么设计

thread_id 不能随便设计。

它必须满足几个要求：

1. 稳定：同一条对话后续请求必须继续使用同一个 thread_id。
2. 唯一：不同对话不能撞到同一个 thread_id。
3. 可控：不能让用户随便猜到别人的 thread_id。
4. 长度合理：生产数据库字段通常会有限制。
5. 可追踪：日志里能用它定位一条 Agent 流程。

学习阶段可以写：

```text
ticket-thread-001
```

生产环境更常见的是：

```text
UUID
数据库会话 ID
会话表主键
前端创建的 conversation_id
服务端生成的 opaque id
```

所谓 opaque id，就是：

```text
外部只能拿来使用，不能从 ID 本身推断业务含义。
```

例如，不建议直接用：

```text
user_001_order_1001_ticket
```

因为这种 ID 暴露了用户、订单和业务含义，也容易被猜测。

更好的做法是：

```text
thread_id 只负责定位线程。
用户身份、权限、订单归属由后端鉴权单独判断。
```

### 10. 什么是 MemorySaver

本节使用：

```python
MemorySaver()
```

它是 LangGraph 的内存 checkpointer。

内存 checkpointer 的特点：

1. 使用简单。
2. 不需要数据库。
3. 适合学习。
4. 适合单元测试。
5. 进程重启后状态会丢失。
6. 不适合生产环境长期保存。

你可以把它理解为：

```text
先把 checkpoint 存在当前 Python 进程内存里。
```

后面真正工程化时，可以换成数据库版 checkpointer。

### 11. MemorySaver 的真实限制

`MemorySaver` 很适合本节学习，因为它让我们不用安装数据库就能体验 checkpoint。

但它有几个现实限制：

1. Python 进程重启，checkpoint 丢失。
2. 多个服务实例之间不能共享状态。
3. 不适合跨机器部署。
4. 不适合保存大量长期对话。
5. 不适合做正式审计。
6. 不能代替数据库备份。

举个例子：

```text
你在本地启动 FastAPI
用户发起工单，生成待确认状态
你关闭服务再启动
用户回复确认创建
```

如果只用 `MemorySaver`，第二轮就找不到上一轮状态。

所以你要知道：

```text
MemorySaver 是学习用和测试用。
生产要换持久化 checkpointer。
```

这不是因为 `MemorySaver` 不好，而是因为它的定位就是内存保存。

### 12. checkpoint 和 store 的区别

LangGraph 文档里会区分：

```text
checkpointer
store
```

它们都和记忆有关，但用途不同。

checkpointer 保存的是：

```text
某条 thread 的图状态。
```

例如：

```text
当前待确认工单是什么
流程执行到哪里
node_history 是什么
```

store 保存的是：

```text
跨 thread 的长期应用数据。
```

例如：

```text
用户偏好
用户常用地址
长期事实
共享知识
```

本节只学 checkpointer。

store 不是本节重点。

### 13. 短期记忆和长期记忆怎么区分

可以用一个简单判断：

```text
这份数据是不是为了继续当前流程？
```

如果是，通常属于 checkpoint。

例如：

```text
当前待确认工单
当前节点路径
当前用户已经补充了哪些字段
当前图下一步要去哪
```

再问：

```text
这份数据是不是跨很多对话都要长期使用？
```

如果是，通常属于 store 或业务数据库。

例如：

```text
用户偏好
用户会员等级
用户历史订单
正式工单记录
企业知识库文档
```

这能避免一个常见错误：

```text
把所有数据都塞进 checkpoint。
```

checkpoint 不是垃圾桶。

它应该保存能帮助当前图继续执行的必要状态。

### 14. 为什么 checkpoint 是 human-in-the-loop 的基础

human-in-the-loop 的意思是：

```text
流程中某一步需要等人输入。
```

比如创建工单前要等用户确认：

```text
Agent：请确认是否创建
用户：确认创建
```

这中间可能隔了几秒、几分钟，甚至更久。

如果没有 checkpoint，Agent 可能忘记：

```text
之前要确认的工单是什么。
```

所以要实现真正的 human-in-the-loop，必须先有 checkpoint。

下一节学 `interrupt()` 时，你会看到：

```text
interrupt 负责暂停。
checkpoint 负责保存暂停时的 State。
thread_id 负责找到要恢复的那条线程。
```

### 15. 为什么本节不直接学 interrupt

第 19 节我们已经做了确认节点。

第 20 节我们已经做了创建节点。

本节先学 checkpoint 和 thread_id，是因为：

```text
如果你不知道 State 怎么保存、怎么找回，直接学 interrupt 会很容易只会照抄。
```

所以本节先做一个“手动恢复版”：

```text
第 1 轮：保存待确认 State
第 2 轮：手动把 ticket_confirmation_approved 写进同一条 thread
继续执行 create_ticket
```

下一节再把手动恢复升级为：

```text
interrupt 暂停
Command(resume=...) 恢复
```

这个顺序更适合真正理解。

## 二、本节主题系统讲解

### 1. 第 20 节的问题

第 20 节可以这样创建工单：

```python
graph.invoke({
    "user_message": "我要投诉订单 1001，物流一直不动",
    "ticket_confirmation_approved": True,
})
```

这能证明：

```text
确认后可以进入 create_ticket。
```

但它不符合真实对话。

真实对话不会在用户第一句话里就带着：

```text
ticket_confirmation_approved=True
```

真实情况是第一轮生成确认，第二轮用户才确认。

所以第 21 节要把流程改成：

```text
第 1 轮保存状态
第 2 轮从保存状态继续
```

### 2. 本节新增的 checkpointed graph

第 20 节的普通图：

```python
ticket_agent_graph = build_ticket_agent_graph()
```

没有 checkpointer。

本节新增：

```python
def build_checkpointed_ticket_agent_graph(ticket_creator=None):
    return build_ticket_agent_graph(
        ticket_creator=ticket_creator,
        checkpointer=MemorySaver(),
    )
```

它的意思是：

```text
构建一个带内存 checkpoint 的智能工单图。
```

普通图适合单轮调用。

checkpointed graph 适合学习多轮状态保存和恢复。

### 3. 本节新增的 thread config

LangGraph 不是把 thread_id 放进 State 里，而是放进 config：

```python
{"configurable": {"thread_id": "ticket-thread-001"}}
```

本节新增：

```python
build_ticket_agent_thread_config(thread_id)
```

它负责：

1. 去掉 thread_id 前后空格。
2. 禁止空 thread_id。
3. 返回 LangGraph 需要的 config 格式。

为什么要单独写函数？

因为 config 格式以后会到处用：

```text
invoke
get_state
update_state
stream
```

统一封装后不容易写错。

### 4. 第 1 轮：在线程中运行 Agent

本节新增：

```python
run_ticket_agent_in_thread(graph, user_message, thread_id=..., actor_id=...)
```

它做的事情是：

```text
构建初始 State
带上 actor_id
带上 thread_id config
调用 graph.invoke
让 checkpointer 保存执行后的 State
```

第 1 轮用户输入：

```text
我要投诉订单 1001，物流一直不动
```

运行后 State 里会有：

```text
pending_ticket_confirmation
ticket_confirmation_required = True
final_answer = 请确认是否创建...
```

同时 checkpointer 会把这份 State 保存到：

```text
thread_id = ticket-thread-001
```

### 5. 如何读取线程状态

本节新增：

```python
get_ticket_agent_thread_state(graph, thread_id=...)
```

内部使用：

```python
graph.get_state(config)
```

它可以让我们检查：

```text
这条 thread 当前保存了什么 State。
```

测试中我们会断言：

```text
saved_state["pending_ticket_confirmation"] 存在
saved_state["node_history"] 停在 request_ticket_confirmation
```

这证明 checkpoint 真的保存了待确认工单。

### 6. StateSnapshot 里有什么

`graph.get_state(config)` 返回的不是一个普通字典，而是一个 StateSnapshot。

本节代码为了让你更容易使用，封装成：

```python
return dict(snapshot.values)
```

但你要知道，snapshot 本身通常不只包含 values。

你可以重点理解两个概念：

```text
values
next
```

`values` 表示：

```text
当前 thread 保存下来的 State 字段。
```

例如：

```text
pending_ticket_confirmation
ticket_fields
final_answer
node_history
```

`next` 表示：

```text
当前 checkpoint 后面可能要继续执行的节点。
```

在我们的手动恢复实验里，第 1 轮正常结束后，`next` 通常是空的，因为流程已经到 END。

但当我们使用：

```python
graph.update_state(..., as_node="request_ticket_confirmation")
```

把确认状态写到 `request_ticket_confirmation` 节点之后，LangGraph 会重新推导这个节点后面的条件边。

这时下一步就可能变成：

```text
create_ticket
```

所以你可以把 snapshot 理解成：

```text
当前保存了什么，以及接下来能从哪里继续。
```

这比只保存一个普通 dict 更强。

### 7. 第 2 轮：确认后恢复执行

本节新增：

```python
approve_ticket_confirmation_and_resume(graph, thread_id=..., actor_id=...)
```

它做了几件事：

```text
1. 用 thread_id 找回当前 State
2. 检查是否存在 pending_ticket_confirmation
3. 写入 ticket_confirmation_approved=True
4. 告诉 LangGraph 这次更新发生在 request_ticket_confirmation 节点之后
5. 调用 graph.invoke(None, config=...)
6. 让图继续执行 create_ticket
```

这里最容易不懂的是：

```python
as_node="request_ticket_confirmation"
```

它的含义是：

```text
这次 update_state 相当于 request_ticket_confirmation 节点之后的新状态。
```

因为图里有这条条件边：

```text
request_ticket_confirmation
-> route_by_ticket_confirmation
-> create_ticket 或 END
```

当我们在这个节点后写入：

```text
ticket_confirmation_approved=True
```

LangGraph 就知道下一步可以沿着确认后的条件边继续。

### 8. as_node 为什么不是随便填

`as_node` 不是一个普通备注。

它会影响 LangGraph 怎么理解这次状态更新发生在图的哪个位置。

如果我们写：

```python
as_node="request_ticket_confirmation"
```

意思是：

```text
用户确认这件事，发生在 request_ticket_confirmation 节点之后。
```

这和业务流程一致：

```text
request_ticket_confirmation
-> 用户看到确认信息
-> 用户确认
-> create_ticket
```

如果你乱写成：

```python
as_node="extract_ticket_fields"
```

那就等于告诉 LangGraph：

```text
这次更新发生在字段提取节点之后。
```

这会让图重新从字段完整分支进入确认节点，而不是直接进入创建节点。

如果你乱写成不存在的节点名，就会直接出错。

所以 `as_node` 的本质是：

```text
告诉 LangGraph 从图的哪个位置继续推导下一步。
```

本节写 `request_ticket_confirmation`，不是为了通过测试，而是因为它符合业务语义。

### 9. 为什么恢复时调用 invoke(None)

第一次运行需要输入：

```python
{"user_message": "..."}
```

但恢复时，我们不是要重新从 START 开始跑。

我们要做的是：

```text
从已经保存的 checkpoint 的下一步继续。
```

所以本节使用：

```python
graph.invoke(None, config=config)
```

意思是：

```text
没有新的普通输入，继续执行当前 thread 的下一步。
```

如果你重新传入：

```python
{"user_message": "确认创建"}
```

那图会从 START 开始，把“确认创建”当作新的用户问题重新分类。

这不是本节想要的恢复方式。

### 10. 为什么不把“确认创建”当普通 user_message 重新跑

有些系统会选择把第二轮用户输入：

```text
确认创建
```

重新送进意图识别，让模型判断这是确认。

这不是完全不行，但它会带来额外复杂度：

1. 需要识别“确认创建”是不是确认上一张工单。
2. 需要查找上一张待确认工单。
3. 需要防止用户没有待确认工单却说确认。
4. 需要处理“确认，但订单号改成 1002”这种编辑场景。
5. 需要处理多张待确认工单的匹配问题。

本节先不做这套自然语言确认解析。

本节的学习重点是：

```text
只要应用层已经判断用户确认，如何恢复 LangGraph 流程。
```

也就是说，本节把两个问题拆开：

```text
用户自然语言是不是确认
```

和：

```text
确认后图怎么继续执行
```

本节只学第二个。

第 22 节学 `interrupt()` 后，再继续把用户输入和恢复机制结合起来。

### 11. 为什么不同 thread_id 要隔离

假设有两个线程：

```text
ticket-thread-001
ticket-thread-002
```

第一个线程有待确认工单。

第二个线程从未发起过工单。

如果你用第二个 thread_id 读取 State，应该得到空状态。

这说明：

```text
thread_id 是状态隔离边界。
```

如果不同用户或不同会话混用 thread_id，就可能出现严重问题：

```text
用户 A 确认了用户 B 的工单
```

所以生产系统必须严肃管理 thread_id。

### 12. thread_id 隔离背后的安全问题

thread_id 隔离不是单纯的技术洁癖。

它直接关系到业务安全。

如果一个系统允许用户随意指定 thread_id，并且不校验这个 thread 是否属于当前用户，就可能出现：

```text
用户 A 拿到了用户 B 的 thread_id
用户 A 发送“确认创建”
系统用用户 B 的待确认工单创建了正式工单
```

这就是越权。

所以生产系统里要做两层校验：

```text
thread_id 能找到状态
当前用户有权访问这个 thread_id
```

本节为了学习，没有实现完整鉴权。

但你要记住：

```text
thread_id 不是安全凭证。
```

它只是状态指针。

真正的安全要靠登录态、actor_id、权限校验和后端鉴权。

### 13. 本节恢复后的完整路径

第 1 轮路径：

```text
normalize_user_input
-> classify_intent
-> decide_ticket_need
-> extract_ticket_fields
-> request_ticket_confirmation
```

保存到 checkpoint。

第 2 轮确认后恢复，只继续：

```text
create_ticket
```

最终完整 `node_history` 是：

```text
normalize_user_input
-> classify_intent
-> decide_ticket_need
-> extract_ticket_fields
-> request_ticket_confirmation
-> create_ticket
```

注意，第 2 轮没有重新跑：

```text
normalize_user_input
classify_intent
extract_ticket_fields
```

这正是 checkpoint 恢复的价值。

### 14. 本节手动恢复的完整心智模型

你可以把本节恢复过程想成三层：

第一层，业务层：

```text
用户确认了上一轮的待确认工单。
```

第二层，State 层：

```text
把 ticket_confirmation_approved=True 写入同一个 thread 的 State。
```

第三层，图执行层：

```text
从 request_ticket_confirmation 后面的条件边继续，进入 create_ticket。
```

这三层不要混。

如果只理解业务层，你会不知道代码怎么恢复。

如果只理解 State 层，你会不知道为什么要写 `as_node`。

如果只理解图执行层，你会不知道为什么必须先校验 pending_ticket_confirmation。

真正掌握这节，应该能把三层串起来：

```text
用户确认
-> 更新同一 thread 的 State
-> 让图从正确节点后继续执行
-> 创建工单
```

### 15. 本节和下一节的关系

本节是手动恢复：

```text
update_state
-> invoke(None)
```

下一节会学习更正式的 human-in-the-loop：

```text
interrupt()
-> Command(resume=...)
```

你可以这样理解：

```text
第 21 节：先学会保存和找回状态。
第 22 节：再学会让图自己暂停并等待人类输入。
```

## 三、本节代码改动讲解

### 1. build_ticket_agent_graph 增加 checkpointer 参数

原来：

```python
def build_ticket_agent_graph(ticket_creator=None):
```

现在：

```python
def build_ticket_agent_graph(ticket_creator=None, *, checkpointer=None):
```

最后编译时：

```python
return builder.compile(checkpointer=checkpointer)
```

这样同一个图构建函数既能创建普通图，也能创建带 checkpoint 的图。

### 2. build_checkpointed_ticket_agent_graph

新增：

```python
def build_checkpointed_ticket_agent_graph(ticket_creator=None):
    return build_ticket_agent_graph(
        ticket_creator=ticket_creator,
        checkpointer=MemorySaver(),
    )
```

这是学习用的快捷函数。

它创建一个：

```text
内存 checkpoint 图。
```

### 3. build_ticket_agent_thread_config

新增：

```python
def build_ticket_agent_thread_config(thread_id: str) -> dict[str, Any]:
```

它返回：

```python
{"configurable": {"thread_id": "ticket-thread-001"}}
```

这个结构是 LangGraph 读取 checkpoint 所需的 config。

### 4. run_ticket_agent_in_thread

新增：

```python
def run_ticket_agent_in_thread(graph, user_message, *, thread_id, actor_id=None):
```

它和普通 `run_ticket_agent` 的区别是：

```text
普通 run_ticket_agent 不保存线程状态。
run_ticket_agent_in_thread 会用 thread_id 保存线程状态。
```

### 5. get_ticket_agent_thread_state

新增：

```python
def get_ticket_agent_thread_state(graph, *, thread_id):
```

它通过：

```python
graph.get_state(config)
```

读取当前 thread 的 State。

这对测试、调试和理解 checkpoint 很有用。

### 6. approve_ticket_confirmation_and_resume

新增：

```python
def approve_ticket_confirmation_and_resume(graph, *, thread_id, actor_id=None):
```

这是本节最核心的恢复函数。

它会：

1. 读取 thread 状态。
2. 确认存在待确认工单。
3. 写入 `ticket_confirmation_approved=True`。
4. 指定 `as_node="request_ticket_confirmation"`。
5. 调用 `graph.invoke(None, config=config)` 继续执行。

如果当前 thread 没有待确认工单，会抛出：

```text
TICKET_CONFIRMATION_NOT_FOUND
```

这比直接创建失败更清楚。

### 7. 本节常见错误和排查

学习 checkpoint / thread_id 时，常见错误不是 Python 语法错误，而是流程语义错误。

#### 错误 1：忘记传 config

错误写法：

```python
graph.invoke(build_ticket_agent_input(user_message))
```

如果图有 checkpointer，但你不传：

```python
{"configurable": {"thread_id": "..."}}
```

LangGraph 就不知道这次运行属于哪条线程。

正确做法：

```python
graph.invoke(
    build_ticket_agent_input(user_message),
    config=build_ticket_agent_thread_config(thread_id),
)
```

#### 错误 2：第二轮用了新的 thread_id

第 1 轮：

```text
thread_id = ticket-thread-001
```

第 2 轮：

```text
thread_id = ticket-thread-002
```

这样第二轮当然找不到上一轮的待确认工单。

这不是 LangGraph 坏了，而是你换了一条线程。

#### 错误 3：把 thread_id 放进 State

错误理解：

```text
thread_id 是 State 的一个字段。
```

本节的做法不是这样。

thread_id 放在 config 里：

```python
{"configurable": {"thread_id": "..."}}
```

State 保存业务字段，config 告诉运行时这次执行属于哪条线程。

#### 错误 4：恢复时重新从 START 跑

错误做法：

```python
graph.invoke({"user_message": "确认创建"}, config=config)
```

这会让图从 START 重新处理“确认创建”这句话。

本节想要的是从保存的 checkpoint 继续：

```python
graph.invoke(None, config=config)
```

#### 错误 5：as_node 写错

如果 `as_node` 写错，LangGraph 会从错误的位置继续推导下一步。

本节必须写：

```python
as_node="request_ticket_confirmation"
```

因为用户确认发生在确认节点之后。

#### 错误 6：以为 MemorySaver 能长期保存

`MemorySaver` 只存在内存里。

进程重启后，状态会丢。

所以如果你在本地重启服务后发现 thread 状态没了，这不是中文乱码，也不是测试坏了，而是内存 checkpointer 的正常限制。

## 四、本节测试讲解

本节新增测试主要验证：

1. `thread_id` config 构建正确，空 thread_id 会报错。
2. checkpointed graph 能保存待确认工单。
3. `get_state` 能读出保存后的 State。
4. 同一个 thread_id 可以恢复执行。
5. 恢复后只继续执行 `create_ticket`。
6. 不同 thread_id 的状态互相隔离。
7. 没有待确认工单时不能恢复创建。

测试仍然使用：

```text
FakeTicketCreator
```

因为本节重点不是测试真实 Java 服务，而是测试：

```text
checkpoint + thread_id + 状态恢复。
```

## 五、本节完成后的流程

### 第 1 轮

```text
thread_id = ticket-thread-001

用户：我要投诉订单 1001，物流一直不动

START
-> normalize_user_input
-> classify_intent
-> decide_ticket_need
-> extract_ticket_fields
-> request_ticket_confirmation
-> END

checkpoint 保存 pending_ticket_confirmation
```

### 第 2 轮

```text
thread_id = ticket-thread-001

用户：确认创建

应用层调用 approve_ticket_confirmation_and_resume
-> update_state(ticket_confirmation_approved=True, as_node="request_ticket_confirmation")
-> graph.invoke(None)
-> create_ticket
-> END
```

最终：

```text
created_ticket = {...}
final_answer = 工单已创建，工单号：T1001...
```

## 六、你要真正记住的核心句子

1. checkpoint 是某条 thread 的 State 快照。
2. thread_id 是找到某条 State 线程的指针。
3. State 保存业务流程信息，thread_id 不应该混进用户自然语言里。
4. 同一个 thread_id 能继续同一条流程。
5. 不同 thread_id 必须互相隔离。
6. MemorySaver 只适合学习和测试，进程重启会丢。
7. `get_state` 用来查看当前 thread 保存了什么。
8. `update_state` 可以向已有 thread 写入新的状态。
9. `as_node` 会影响 LangGraph 从哪条边继续推导下一步。
10. `invoke(None)` 可以从 checkpoint 的下一步继续执行。
11. checkpoint 是 interrupt 和 human-in-the-loop 的基础。
12. 本节是手动恢复，下一节会学习正式 interrupt 恢复。

## 七、本节练习

### 练习 1：解释概念

请用自己的话解释：

```text
checkpoint
thread_id
```

### 练习 2：判断状态

第 1 轮用户说：

```text
我要投诉订单 1001，物流一直不动
```

如果使用 checkpointed graph 和 thread_id，运行结束后 State 里应该保存什么关键字段？

### 练习 3：判断隔离

`ticket-thread-001` 已经有待确认工单。

现在用 `ticket-thread-002` 去读取 State，应该得到什么？为什么？

### 练习 4：解释恢复

为什么本节恢复创建时调用：

```python
graph.invoke(None, config=config)
```

而不是重新传入：

```python
{"user_message": "确认创建"}
```

### 练习 5：解释 as_node

为什么 `approve_ticket_confirmation_and_resume` 里要使用：

```python
as_node="request_ticket_confirmation"
```

## 八、练习参考答案

### 练习 1 参考答案

checkpoint 是某条 Agent 线程在某个时刻保存下来的 State 快照。

thread_id 是这条线程的标识，用来告诉 LangGraph 要读写哪一条线程的 checkpoint。

### 练习 2 参考答案

关键字段包括：

```text
pending_ticket_confirmation
ticket_confirmation_required = True
ticket_confirmation_message
ticket_fields
node_history
final_answer
```

这些信息能让下一轮用户确认时继续创建工单。

### 练习 3 参考答案

应该得到空状态。

因为不同 thread_id 代表不同线程，checkpoint 不能混用。

如果 thread 状态不隔离，可能出现用户确认了别人待确认工单的严重问题。

### 练习 4 参考答案

因为重新传入 `{"user_message": "确认创建"}` 会让图从 START 开始，把“确认创建”当成一个新的用户问题重新分类。

本节想要的是从上一轮 checkpoint 的下一步继续执行，所以使用：

```python
graph.invoke(None, config=config)
```

### 练习 5 参考答案

因为第 1 轮流程停在 `request_ticket_confirmation` 节点之后。

确认后写入：

```text
ticket_confirmation_approved=True
```

应该让 LangGraph 从 `request_ticket_confirmation` 后面的条件边继续判断。

所以需要：

```python
as_node="request_ticket_confirmation"
```

## 九、本节自测题

### 自测 1

为什么 checkpoint 是多轮 Agent 的基础？

### 自测 2

为什么 MemorySaver 不适合生产环境长期保存对话？

### 自测 3

thread_id 和 user_id 有什么区别？

### 自测 4

如果没有待确认工单，为什么不能直接执行 `approve_ticket_confirmation_and_resume`？

### 自测 5

本节和下一节 `interrupt()` 的关系是什么？

## 十、自测题参考答案

### 自测 1 参考答案

因为多轮 Agent 需要记住上一轮的 State。

没有 checkpoint，第二轮用户说“确认创建”时，Agent 不知道上一轮待确认工单是什么，也不知道流程应该从哪里继续。

### 自测 2 参考答案

因为 MemorySaver 把 checkpoint 存在当前 Python 进程内存里。

进程重启后状态会丢失，不能满足生产环境的长期可靠保存。

### 自测 3 参考答案

user_id 表示哪个用户。

thread_id 表示这个用户的哪一条对话或哪一条 Agent 流程。

一个用户可以有多个 thread。

### 自测 4 参考答案

因为确认必须对应一份已经生成的待确认工单。

如果没有 `pending_ticket_confirmation`，系统不知道用户确认的是哪件事，直接创建工单是不安全的。

### 自测 5 参考答案

本节学习 checkpoint 和 thread_id，解决状态如何保存和找回。

下一节学习 `interrupt()`，解决图如何在节点中正式暂停，并用 `Command(resume=...)` 恢复。

checkpoint 是 interrupt 能恢复的基础。

## 十一、本节小结

本节完成了智能工单 Agent 的多轮状态基础：

```text
第 1 轮生成待确认工单
-> checkpoint 保存 State
-> 第 2 轮用同一个 thread_id 找回 State
-> 写入用户确认
-> 从确认节点后继续创建工单
```

本节之后，你应该已经能理解：

```text
为什么真实 Agent 不能只靠一次函数调用。
```

它必须能保存状态、找回状态、继续状态。

下一节要学：

```text
interrupt / human-in-the-loop
```

也就是让 LangGraph 自己在确认节点暂停，等待用户输入，再恢复执行。

## 十二、参考资料

1. LangGraph 官方文档：Persistence
   https://docs.langchain.com/oss/python/langgraph/persistence

2. LangGraph 官方文档：Interrupts
   https://docs.langchain.com/oss/python/langgraph/interrupts
