# 阶段 5 第 22 节：interrupt / human-in-the-loop

## 本节定位

第 21 节我们学会了：

```text
checkpoint 保存 State
thread_id 找回同一条线程
update_state 手动写入确认结果
invoke(None) 从 checkpoint 后继续执行
```

这已经能实现“确认后继续创建工单”。

但第 21 节仍然是手动恢复：

```text
应用层自己判断用户确认
-> update_state(ticket_confirmation_approved=True)
-> as_node="request_ticket_confirmation"
-> invoke(None)
```

第 22 节要升级成 LangGraph 更标准的 human-in-the-loop 方式：

```text
节点内部调用 interrupt()
-> 图暂停
-> 返回中断 payload 给调用方
-> 用户确认
-> Command(resume=...) 恢复
-> 节点继续返回 State
-> 后续条件边进入 create_ticket
```

本节会把第 19 节的用户确认节点、第 20 节的创建工单节点、第 21 节的 checkpoint/thread_id 串起来。

## 本节学习目标

学完本节，你应该能讲清楚：

1. 什么是 `interrupt()`。
2. 什么是 human-in-the-loop。
3. `interrupt()` 和 checkpoint 的关系。
4. `interrupt()` 和 thread_id 的关系。
5. `Command(resume=...)` 是什么。
6. 第一次运行为什么会返回 `__interrupt__`。
7. interrupt payload 应该放什么。
8. 为什么 payload 必须能被应用层理解。
9. 用户确认后怎么恢复。
10. 节点为什么会在 resume 时重新执行。
11. 为什么 interrupt 前不能放不可重复的副作用。
12. 为什么创建工单不能放在 interrupt 前面。
13. 本节和第 21 节手动恢复有什么区别。
14. 为什么测试仍然用 fake creator，不真实调用 Java 服务。
15. 本项目如何把确认节点升级成真正暂停点。

## 本节先不学什么

本节暂时不做：

1. 不接真实前端确认按钮。
2. 不接真实用户登录态。
3. 不接 PostgreSQL checkpointer。
4. 不处理多个并行 interrupt。
5. 不做超时过期。
6. 不做复杂审批流。
7. 不做“用户修改字段后继续”的编辑流程。
8. 不真实调用 Java 服务。
9. 不把 LangGraph Server / Studio 引进项目。
10. 不做生产级权限系统。

本节只解决：

```text
如何让 LangGraph 在用户确认节点暂停，并在用户确认后恢复创建工单。
```

## 一、基础知识铺垫

### 1. 什么是 human-in-the-loop

human-in-the-loop 可以翻译成：

```text
人在流程中参与决策。
```

Agent 不是所有事情都应该自己做。

特别是这些动作：

```text
创建工单
取消订单
发起退款
修改用户资料
发送通知
调用真实业务写接口
```

它们都会影响业务系统。

这类动作执行前，通常应该让人参与确认。

在我们的项目里，人参与的点是：

```text
创建工单前，让用户确认待确认工单。
```

这就是 human-in-the-loop。

### 2. 为什么不能让 Agent 自己直接创建

即使 Agent 已经抽出了字段：

```text
issue_type = complaint
order_id = 1001
description = 我要投诉订单 1001，物流一直不动
user_request = 投诉处理
urgency = high
```

它仍然不能直接创建工单。

原因是：

```text
字段完整不等于用户授权。
```

这句话在第 19 节已经讲过，本节继续强化。

创建工单是写操作。

写操作一旦执行，外部系统会发生变化：

1. Java mock 服务会新增工单。
2. 工单会有正式工单号。
3. 后续可能触发客服处理。
4. 用户记录会发生变化。
5. 系统日志会记录这个动作。

所以必须让用户明确确认。

### 3. 什么是 interrupt()

`interrupt()` 是 LangGraph 提供的动态暂停机制。

你可以把它理解成：

```text
节点运行到这里，先停下来，把一个问题或 payload 交给外部调用方，等待外部输入后再继续。
```

在我们的工单流程里，确认节点会做：

```text
生成待确认工单
-> interrupt(待确认工单 payload)
-> 等用户确认
-> resume 后得到用户确认结果
-> 写入 ticket_confirmation_approved
```

它不是普通的 `input()`。

它也不是简单的 `return`。

它是 LangGraph 运行时能识别的暂停点。

### 4. interrupt() 为什么需要 checkpoint

`interrupt()` 会让图暂停。

暂停以后，图必须知道：

```text
暂停时 State 是什么？
暂停在哪个节点？
恢复时应该回到哪里？
```

这些都要靠 checkpoint。

如果没有 checkpointer，LangGraph 没地方保存暂停位置。

所以 `interrupt()` 的基础条件是：

```text
图必须带 checkpointer。
```

本节使用：

```python
MemorySaver()
```

它适合学习和测试。

生产环境要换成持久化 checkpointer。

### 5. interrupt() 为什么需要 thread_id

checkpoint 可以保存很多条线程的状态。

那 LangGraph 怎么知道要恢复哪一条？

靠：

```text
thread_id
```

第一次运行：

```python
config = {"configurable": {"thread_id": "ticket-interrupt-001"}}
graph.invoke(input_state, config=config)
```

恢复时必须用同一个：

```python
graph.invoke(Command(resume=...), config=config)
```

如果换了 thread_id，LangGraph 会以为这是另一条线程。

这和第 21 节完全一致。

### 6. interrupt() 和普通 return 的区别

普通节点返回：

```python
return {"final_answer": "请确认..."}
```

表示：

```text
这个节点已经结束，图可以继续走后续边。
```

`interrupt()` 不一样。

它表示：

```text
这个节点还没真正结束，先暂停，等外部输入。
```

第一次运行到 `interrupt()` 时，节点不会返回正常 State 更新。

图会返回类似：

```text
__interrupt__ = [Interrupt(value=..., id=...)]
```

resume 之后，`interrupt()` 才会拿到外部传回来的值，节点继续执行并返回 State。

### 7. 什么是 interrupt payload

调用：

```python
interrupt(payload)
```

里面的 `payload` 就是给外部调用方看的中断信息。

在本节里，payload 包含：

```text
kind
confirmation_id
message
pending_ticket_confirmation
```

其中：

```text
kind = ticket_confirmation
```

表示这是一个工单确认中断。

```text
confirmation_id
```

表示这份待确认工单草稿的 ID。

```text
message
```

表示给用户展示的确认话术。

```text
pending_ticket_confirmation
```

表示结构化待确认工单。

### 8. payload 为什么不能只是一句话

可以只写：

```python
interrupt("请确认是否创建工单")
```

但这对真实系统不够。

因为外部应用层需要知道：

1. 这是什么类型的中断。
2. 要展示什么信息。
3. 用户确认的是哪份工单。
4. 前端要不要显示确认按钮。
5. 后端要用哪个 confirmation_id。

所以本节使用结构化 payload。

这体现了一个工程原则：

```text
给人看的话术和给程序用的数据要分开。
```

### 9. 什么是 Command(resume=...)

当图暂停后，要用：

```python
Command(resume=...)
```

恢复。

例如：

```python
graph.invoke(
    Command(resume={"approved": True, "actor_id": "demo_user_001"}),
    config=config,
)
```

这个 `resume` 里的值，会成为节点里 `interrupt()` 的返回值。

也就是说：

```python
resume_value = interrupt(payload)
```

第一次运行到这里会暂停。

第二次恢复时：

```text
resume_value = {"approved": True, "actor_id": "demo_user_001"}
```

节点就能继续执行。

### 10. 节点为什么会重新执行

LangGraph 的 `interrupt()` 有一个非常重要的行为：

```text
resume 时，会从触发 interrupt 的节点开头重新运行。
```

不是从 `interrupt()` 这一行的下一行直接继续。

这意味着：

```text
interrupt 前面的代码会再运行一次。
```

本节确认节点在 interrupt 前做的是：

```text
根据 ticket_fields 构建 pending_confirmation
构建 interrupt payload
```

这些都是纯计算，没有副作用。

所以重跑是安全的。

### 11. 为什么 interrupt 前不能放副作用

副作用是会改变外部世界的操作。

例如：

```text
调用 Java 创建工单
写数据库
发短信
发送邮件
扣款
写正式日志流水
```

如果这些操作放在 `interrupt()` 前面，就会发生风险：

```text
第一次运行执行了一次
resume 时节点重跑又执行一次
```

所以规则是：

```text
interrupt 前只能放可重复的纯计算，不能放不可重复的写操作。
```

本节创建工单在 `create_ticket_node`，位于 interrupt 恢复之后。

这是正确边界。

### 12. interrupt 和第 21 节手动恢复的区别

第 21 节：

```text
run -> request confirmation -> END
应用层 update_state
invoke(None)
```

第 22 节：

```text
run -> request confirmation -> interrupt 暂停
Command(resume=...)
图从中断节点恢复
```

第 21 节是手动告诉 LangGraph：

```text
我把确认结果写到 request_ticket_confirmation 后面了。
```

第 22 节是 LangGraph 自己知道：

```text
request_ticket_confirmation 节点在 interrupt 处暂停了。
```

所以第 22 节更接近正式 human-in-the-loop。

### 13. interrupt 的完整生命周期

你可以把一次 `interrupt()` 理解成下面这个生命周期：

```text
1. 图开始执行
2. 前面的节点正常更新 State
3. 执行到某个节点
4. 这个节点调用 interrupt(payload)
5. LangGraph 保存当前线程的执行位置和 State
6. 本次 invoke 提前返回 __interrupt__
7. 应用层把 payload 展示给用户
8. 用户点击确认或拒绝
9. 应用层再次调用 graph.invoke(Command(resume=...), config=同一个 thread_id)
10. LangGraph 找回原来的暂停点
11. 暂停节点重新执行到 interrupt 这一行
12. 这一次 interrupt 返回 resume 值
13. 节点继续执行后面的逻辑并 return State 更新
14. 图继续沿着条件边往下走
```

这里最关键的是第 5、9、10、11 步。

没有第 5 步，系统不知道暂停在哪。

没有第 9 步的同一个 `thread_id`，系统找不回原来的线程。

没有第 11 步的“重新执行到 interrupt”，你就很容易误以为它像普通函数一样从下一行继续。

所以你要形成一个准确理解：

```text
interrupt 不是把 Python 函数挂起在内存里。
interrupt 是把图的暂停信息保存到 checkpointer，后续再通过 thread_id 和 Command(resume=...) 让图恢复。
```

这个理解很重要。

因为真实服务里，一次确认可能跨越很长时间：

```text
用户发起请求
服务返回确认卡片
用户过了 10 秒、1 分钟甚至更久才点击确认
后端再恢复图
```

这中间 Python 进程不应该依赖“某个函数一直卡在内存里”。  
正式系统依赖的是可保存、可恢复的执行状态。

### 14. interrupt 和一次 HTTP 请求的关系

很多初学者会把 `interrupt()` 想成：

```text
后端一直等着用户点按钮
```

这不准确。

在 Web 服务里，更合理的理解是：

```text
第一次 HTTP 请求：
用户：我要投诉订单 1001
后端：运行 LangGraph，遇到 interrupt，返回确认信息给前端

第二次 HTTP 请求：
用户：确认创建
后端：用同一个 thread_id 和 Command(resume=...) 恢复 LangGraph
```

也就是说：

```text
interrupt 跨越的是多次请求，不是一次请求里一直阻塞等待。
```

这也是为什么本节一定要理解 `thread_id`。

如果没有 `thread_id`，第二次请求到来时，后端不知道用户确认的是哪一次对话、哪一个暂停点、哪一份待创建工单。

所以真实接口通常会长成这样：

```text
POST /agent/ticket
body: { "message": "我要投诉订单 1001" }
return: {
  "status": "needs_confirmation",
  "thread_id": "ticket-thread-001",
  "payload": {...}
}

POST /agent/ticket/confirm
body: {
  "thread_id": "ticket-thread-001",
  "approved": true
}
return: {
  "status": "created",
  "ticket": {...}
}
```

本节没有真正写 FastAPI 路由，是为了先把 LangGraph 的核心机制学清楚。

但你要知道：  
后面一旦接接口，这节的函数就是接口背后的业务核心。

### 15. 用户确认值为什么不能完全信任

`Command(resume=...)` 的值来自应用层。

而应用层的数据，最终来自用户操作。

所以你不能认为：

```python
Command(resume={"approved": True})
```

就天然安全。

真实业务里要继续考虑：

```text
这个 thread_id 是不是当前用户自己的？
这份 confirmation_id 是否还有效？
用户是否有权限创建这种工单？
待创建字段是否仍然完整？
订单号是否仍然存在？
这个确认是否已经被使用过？
```

本节现在只做学习版确认：

```text
approved=True 才继续创建
approved=False 或无法识别就不创建
```

这是第一层安全边界。

以后如果升级到真实系统，还要增加：

```text
用户身份校验
thread_id 归属校验
confirmation_id 校验
确认过期时间
幂等键
创建结果持久化
审计日志
```

你现在先记住一句话：

```text
interrupt 解决的是“暂停等待人输入”，不是解决所有安全问题。
```

### 16. interrupt 和幂等性的关系

幂等性是后端开发里的重要概念。

通俗说：

```text
同一个操作重复请求多次，结果不应该造成重复业务影响。
```

例如创建工单：

```text
用户点了一次确认
网络卡了一下
前端重试
后端收到两次确认
```

如果后端没有幂等设计，可能创建两个工单。

`interrupt()` 本身不能保证幂等。

它只负责暂停和恢复。

真正的幂等通常要靠：

```text
confirmation_id
idempotency_key
数据库唯一约束
创建结果记录
重复请求返回同一个结果
```

本节在 payload 里放 `confirmation_id`，就是为了让你建立这个意识：

```text
用户确认的不是一句话，而是一份具体的待执行操作。
```

以后真实创建工单时，可以用类似字段来判断：

```text
这次确认是不是已经消费过？
这次创建是不是已经成功过？
```

### 17. interrupt 更像工作流暂停点，不是普通函数输入

普通函数输入是：

```python
answer = input("确认吗？")
```

这适合命令行学习，不适合真实后端服务。

后端服务里的 Agent 更像工作流：

```text
节点 A：理解意图
节点 B：抽字段
节点 C：等待确认
节点 D：创建工单
节点 E：总结结果
```

`interrupt()` 的价值在于：

```text
它让节点 C 成为一个正式的、可保存的暂停点。
```

这个暂停点可以跨请求、跨时间、跨进程恢复。

所以你可以把它理解成：

```text
LangGraph 工作流里的“等待人工决策”节点。
```

这个理解比“它让代码停一下”更准确。

## 二、本节主题系统讲解

### 1. 本节前的流程

第 21 节确认后恢复流程是：

```text
第 1 轮：
request_ticket_confirmation
-> END

第 2 轮：
update_state(ticket_confirmation_approved=True, as_node="request_ticket_confirmation")
-> invoke(None)
-> create_ticket
```

这能用，但需要应用层手动指定 `as_node`。

第 22 节改成：

```text
第 1 轮：
request_ticket_confirmation
-> interrupt

第 2 轮：
Command(resume={"approved": True})
-> request_ticket_confirmation 节点恢复
-> create_ticket
```

### 2. 本节为什么保留普通确认节点

项目里现在有两个确认节点：

```text
request_ticket_confirmation_node
request_ticket_confirmation_interrupt_node
```

普通节点用于前面课程和单轮流程。

interrupt 节点用于第 22 节学习正式暂停。

为什么不直接替换？

因为如果直接替换，之前的 `run_ticket_agent()` 测试都会变成返回 `__interrupt__`。

为了学习阶段更清楚，本节采用：

```text
普通图保持普通确认
interrupt 图使用 interrupt 确认
```

这让两个版本可以并存对比。

### 3. 本节新增 interrupt 图

新增：

```python
build_interrupting_ticket_agent_graph(ticket_creator=None)
```

它等价于：

```text
带 MemorySaver
确认节点使用 request_ticket_confirmation_interrupt_node
```

也就是说：

```text
build_checkpointed_ticket_agent_graph
```

是第 21 节手动恢复图。

```text
build_interrupting_ticket_agent_graph
```

是第 22 节 interrupt 恢复图。

### 4. interrupt 版确认节点做什么

`request_ticket_confirmation_interrupt_node` 做这些事：

```text
1. 从 State 读取 ticket_fields
2. 构建 pending_confirmation
3. 构建 interrupt payload
4. 调用 interrupt(payload)
5. 等待 Command(resume=...)
6. 解析 resume_value
7. 写入 ticket_confirmation_approved
8. 返回 State 更新
```

第一次运行时，执行到第 4 步就暂停。

恢复后，继续完成第 5 到第 8 步。

### 5. 第一次运行返回什么

第一次运行：

```python
result = run_ticket_agent_in_thread(
    graph,
    "我要投诉订单 1001，物流一直不动",
    thread_id="ticket-interrupt-001",
)
```

返回结果里会有：

```text
__interrupt__
```

本节用：

```python
get_ticket_confirmation_interrupt_payload(result)
```

把中断 payload 取出来。

payload 里有：

```text
kind = ticket_confirmation
message = 请确认是否按以下信息创建...
pending_ticket_confirmation = {...}
```

这就是应用层应该展示给用户的内容。

### 6. 暂停时 State 里有什么

注意一个容易误解的点：

```text
第一次 interrupt 时，节点还没有 return。
```

所以 `request_ticket_confirmation_interrupt_node` 返回的 State 更新还没写进去。

checkpoint 保存的是触发 interrupt 前已有的 State。

这时 State 里通常已经有：

```text
ticket_fields
ticket_fields_complete
node_history 到 extract_ticket_fields
```

但不一定已经有：

```text
pending_ticket_confirmation
ticket_confirmation_approved
```

因为这些是 interrupt 节点恢复后才 return 的内容。

待确认工单第一次给调用方，是通过：

```text
interrupt payload
```

不是通过节点 return。

### 7. 为什么 payload 和 State 都会出现确认信息

第一次暂停时：

```text
payload 给应用层展示。
```

恢复后：

```text
pending_ticket_confirmation 写回 State。
```

这不是重复，而是两个阶段：

```text
暂停阶段：外部需要知道问用户什么。
恢复阶段：图需要把确认结果和待确认对象写进 State。
```

### 8. resume=True 后发生什么

恢复时：

```python
resume_ticket_confirmation_interrupt(
    graph,
    thread_id="ticket-interrupt-001",
    approved=True,
    actor_id="demo_user_001",
)
```

内部使用：

```python
Command(resume={"approved": True, "actor_id": "demo_user_001"})
```

恢复后，`interrupt()` 返回：

```python
{"approved": True, "actor_id": "demo_user_001"}
```

确认节点写入：

```text
ticket_confirmation_approved = True
pending_ticket_confirmation = {...}
```

然后条件边判断：

```text
approved=True
-> create_ticket
```

最后创建工单。

### 9. resume=False 后发生什么

如果用户拒绝：

```python
Command(resume={"approved": False})
```

确认节点写入：

```text
ticket_confirmation_approved = False
final_answer = 已取消创建工单...
```

条件边判断：

```text
approved 不为 True
-> END
```

不会进入 `create_ticket`。

这说明 human-in-the-loop 不只是批准，也要能拒绝。

### 10. 为什么恢复函数要封装

本节新增：

```python
resume_ticket_confirmation_interrupt(...)
```

它把底层：

```python
graph.invoke(Command(resume=...), config=...)
```

封装起来。

好处是：

1. 应用层不用到处手写 Command。
2. thread_id config 格式统一。
3. approved / actor_id 契约统一。
4. 测试更容易读。
5. 后续接 FastAPI 时可以复用。

### 11. 为什么不能在 interrupt 节点里创建工单

创建工单必须在 `create_ticket_node`。

不能写成：

```python
resume_value = interrupt(payload)
if resume_value:
    java_client.create_ticket(...)
```

虽然看起来也能跑，但不推荐在确认节点里混入创建动作。

原因是：

1. 确认节点职责会变复杂。
2. 创建节点的错误处理无法复用。
3. 幂等逻辑分散。
4. 图结构看不出创建动作。
5. 测试不够清晰。

本项目继续保持：

```text
确认节点只负责确认
创建节点只负责创建
```

### 12. interrupt 的三个安全原则

本节你必须记住三个原则：

```text
1. interrupt 前不做不可重复副作用。
2. interrupt payload 必须是调用方能理解的结构化数据。
3. resume 后仍要走后端校验和条件边，不直接相信用户输入。
```

第三点也很重要。

用户说确认，不代表我们跳过：

```text
ticket_fields
CreateTicketArgs
JavaTicketClient
幂等键
错误处理
```

确认只是授权信号。

业务执行仍要走完整后端契约。

### 13. 本节的状态变化表

为了把流程真正看懂，可以把本节看成状态机。

第一次运行到 `interrupt()` 之前：

```text
ticket_fields                 已抽取
ticket_confirmation_required  尚未写入，或者仍是旧值
ticket_confirmation_approved  尚未确认
pending_ticket_confirmation   准备放进 payload
ticket_creation_status        尚未创建
```

第一次运行返回后：

```text
result["__interrupt__"]       有值
payload.kind                  ticket_confirmation
payload.pending_ticket_confirmation  待用户确认的工单信息
checkpoint                    保存了线程暂停信息
```

用户确认后恢复：

```text
Command(resume={"approved": True})
-> interrupt() 返回 {"approved": True}
-> 节点写入 ticket_confirmation_approved=True
-> 条件边进入 create_ticket
-> 创建工单
```

用户拒绝后恢复：

```text
Command(resume={"approved": False})
-> interrupt() 返回 {"approved": False}
-> 节点写入 ticket_confirmation_approved=False
-> 条件边不进入 create_ticket
-> 流程结束
```

你以后排查这类流程时，要会看三个位置：

```text
1. 本次 invoke 的返回值
2. checkpoint 里的 State
3. 下一条边会走向哪个节点
```

只看其中一个，很容易误判。

### 14. 为什么第一次返回的是 __interrupt__，不是 final_answer

普通节点最终会返回 State 更新。

但是 `interrupt()` 的设计目标不是生成最终答案，而是告诉外部：

```text
我现在需要人工输入。
```

所以第一次运行遇到 interrupt 后，返回值不是我们平常那种完整业务结果，而是：

```text
__interrupt__: [
  Interrupt(value=payload, id=...)
]
```

这里的 `value` 才是业务层真正关心的 payload。

这就是为什么本节写了：

```python
get_ticket_confirmation_interrupt_payload(result)
```

它把 LangGraph 的底层返回格式转换成我们项目更容易使用的结构。

这个封装很重要。

因为应用层最好不要到处写：

```text
result["__interrupt__"][0].value
```

一旦 LangGraph 返回结构变化，或者未来支持多个中断点，散落在各处的访问逻辑都会变得难维护。

### 15. 为什么 resume_value 要允许 bool 和 dict

本节的解析函数支持两种输入：

```python
True
False
{"approved": True}
{"approved": False, "actor_id": "user-001"}
```

为什么不只支持 `True/False`？

因为真实业务里，确认通常不止一个布尔值。

后续可能需要携带：

```text
actor_id        谁确认的
confirmed_at    什么时候确认的
comment         用户补充说明
version         确认的是第几版待执行内容
source          来自网页、钉钉、企业微信还是后台
```

如果现在只支持布尔值，后面扩展会很别扭。

所以学习版虽然只真正使用 `approved` 和 `actor_id`，但结构已经朝真实业务靠近：

```text
简单场景可以传 bool
工程场景建议传 dict
```

这就是从 demo 走向项目代码的思路。

### 16. 为什么拒绝确认也要返回明确 final_answer

用户拒绝后，不能什么都不说。

如果流程静默结束，调用方会不知道：

```text
是用户拒绝了？
是系统异常了？
是条件边没走对？
是创建接口失败了？
```

所以本节设置了：

```python
TICKET_CONFIRMATION_REJECTED_MESSAGE
```

当 `approved=False` 时，最终回答是：

```text
已取消创建工单；如需创建，请重新发起工单流程。
```

这属于流程兜底的一部分。

即使用户没有创建工单，Agent 也要给出明确结果。

这和下一节要学的错误处理、fallback 会连起来：

```text
正常拒绝要有明确结束语
异常失败也要有明确兜底语
```

### 17. 本节为什么没有把 interrupt 接到真实 FastAPI 路由

本节故意没有直接做接口。

原因是你现在要先把核心机制学明白：

```text
图怎么暂停
payload 怎么返回
thread_id 怎么找回线程
Command(resume=...) 怎么恢复
条件边怎么决定是否创建
```

如果这一节同时加入 FastAPI 路由、请求模型、响应模型、前端按钮、用户身份，就会把重点打散。

学习顺序应该是：

```text
先学 LangGraph 内部机制
再学 API 怎么包装它
最后学前端怎么展示和确认
```

这也是为什么本节主要改 Agent 层，而不是 API 层。

你以后看到类似系统，可以自己拆开：

```text
Agent 层：负责工作流
Service/API 层：负责请求响应、鉴权、thread_id 传递
前端层：负责展示 payload 和收集用户确认
```

三层不要混在一起，项目会更清楚。

## 三、本节代码改动讲解

### 1. 新增 LangGraph 类型导入

新增：

```python
from langgraph.types import Command, interrupt
```

`interrupt` 用来暂停。

`Command` 用来恢复。

### 2. 新增 interrupt 常量

新增：

```python
TICKET_CONFIRMATION_INTERRUPT_KIND = "ticket_confirmation"
TICKET_CONFIRMATION_REJECTED_MESSAGE = "已取消创建工单；如需创建，请重新发起工单流程。"
```

`kind` 是为了让应用层知道这是什么中断。

拒绝消息是为了让 `approved=False` 时给用户明确反馈。

### 3. build_ticket_confirmation_interrupt_payload

这个函数负责构建 payload：

```python
{
    "kind": "ticket_confirmation",
    "confirmation_id": "...",
    "message": "...",
    "pending_ticket_confirmation": {...},
}
```

它不调用模型，不调用 Java，不写数据库。

只是结构化数据构建。

### 4. is_ticket_confirmation_resume_approved

这个函数解析 resume 值。

支持：

```text
True
False
{"approved": True}
{"approved": False}
```

其他值默认当作不批准。

这体现了安全默认值：

```text
不明确批准，就不创建工单。
```

### 5. request_ticket_confirmation_interrupt_node

这是本节核心节点。

它先构建待确认工单，再调用：

```python
resume_value = interrupt(payload)
```

恢复后再写入：

```text
ticket_confirmation_required
ticket_confirmation_approved
ticket_confirmation_message
pending_ticket_confirmation
final_answer
node_history
```

如果 approved 为 True，后续条件边会进 `create_ticket`。

如果 approved 为 False，后续条件边结束。

### 6. build_ticket_agent_graph 新增 interrupt_confirmation 参数

新增：

```python
interrupt_confirmation: bool = False
```

默认是 False，保持普通图不变。

当它为 True 时，确认节点使用：

```text
request_ticket_confirmation_interrupt_node
```

### 7. build_interrupting_ticket_agent_graph

新增：

```python
build_interrupting_ticket_agent_graph(ticket_creator=None)
```

它会：

```text
使用 MemorySaver
启用 interrupt_confirmation=True
```

这是第 22 节专用的学习图。

### 8. get_ticket_confirmation_interrupt_payload

这个函数从执行结果里取出：

```text
__interrupt__[0].value
```

并校验：

```text
kind == ticket_confirmation
```

如果没有中断，或者中断类型不对，就抛出业务错误。

### 9. resume_ticket_confirmation_interrupt

这个函数封装：

```python
graph.invoke(Command(resume=...), config=...)
```

它是应用层恢复确认的入口。

以后接 FastAPI 时，可以把用户点击“确认创建”映射到这个函数。

## 四、本节测试讲解

本节新增测试覆盖：

1. interrupt payload 结构正确。
2. resume 值解析正确。
3. interrupt 节点不能脱离 LangGraph 运行时直接调用。
4. interrupt 图第一次运行会暂停。
5. 暂停结果里有 `__interrupt__`。
6. payload 里有待确认工单。
7. checkpoint 的 next 停在确认节点。
8. approved=True 后恢复并创建工单。
9. approved=False 后取消，不创建工单。
10. 没有 interrupt 结果时不能提取 payload。

最重要的测试是：

```text
第一次运行：暂停
第二次恢复：创建
```

这才是 human-in-the-loop 的核心。

## 五、本节完成后的流程

### 第 1 轮

```text
用户：我要投诉订单 1001，物流一直不动

normalize_user_input
-> classify_intent
-> decide_ticket_need
-> extract_ticket_fields
-> request_ticket_confirmation
   -> interrupt(payload)

返回 __interrupt__
```

### 第 2 轮：用户确认

```text
用户：确认创建

Command(resume={"approved": True})
-> request_ticket_confirmation 节点恢复
-> ticket_confirmation_approved=True
-> create_ticket
-> 返回工单号
```

### 第 2 轮：用户拒绝

```text
用户：取消

Command(resume={"approved": False})
-> request_ticket_confirmation 节点恢复
-> ticket_confirmation_approved=False
-> END
-> 不创建工单
```

## 六、你要真正记住的核心句子

1. `interrupt()` 是节点内的动态暂停点。
2. `interrupt()` 必须配合 checkpointer 和 thread_id。
3. 第一次运行到 interrupt 会返回 `__interrupt__`。
4. `Command(resume=...)` 的值会成为 `interrupt()` 的返回值。
5. resume 时，触发 interrupt 的节点会从开头重新执行。
6. interrupt 前不能放不可重复的副作用。
7. 创建工单必须放在用户确认恢复之后。
8. interrupt payload 要结构化，不能只靠一句自然语言。
9. 不明确 approved=True，就不能创建工单。
10. 第 21 节是手动恢复，第 22 节是 LangGraph 正式暂停恢复。

## 七、本节练习

### 练习 1：解释概念

请解释：

```text
interrupt()
Command(resume=...)
```

### 练习 2：判断流程

第一次运行到 `request_ticket_confirmation_interrupt_node` 时，节点会正常 return 吗？

为什么？

### 练习 3：判断副作用

下面这段逻辑为什么危险？

```python
java_client.create_ticket(...)
approved = interrupt(payload)
```

### 练习 4：判断恢复结果

如果 resume 值是：

```python
{"approved": False}
```

后续会不会进入 `create_ticket`？

### 练习 5：解释 payload

为什么本节 interrupt payload 要包含 `kind` 和 `confirmation_id`？

### 练习 6：解释 HTTP 边界

为什么不能把 `interrupt()` 理解成“后端一直阻塞等待用户点确认”？

## 八、练习参考答案

### 练习 1 参考答案

`interrupt()` 是 LangGraph 节点里的暂停点，用来把 payload 返回给外部调用方，并等待外部输入。

`Command(resume=...)` 是恢复暂停图执行的方式，`resume` 里的值会成为 `interrupt()` 的返回值。

### 练习 2 参考答案

第一次运行不会正常 return。

因为节点执行到 `interrupt(payload)` 时会暂停，LangGraph 返回 `__interrupt__`，等待下一次用 `Command(resume=...)` 恢复。

节点恢复后才会继续执行并 return State 更新。

### 练习 3 参考答案

危险在于 resume 时，触发 interrupt 的节点会从开头重新执行。

如果 `java_client.create_ticket(...)` 放在 interrupt 前，可能第一次运行执行一次，恢复时又执行一次，导致重复创建工单。

写操作必须放在 interrupt 之后，并且最好放在单独的 `create_ticket_node`。

### 练习 4 参考答案

不会。

`{"approved": False}` 会被解析成：

```text
ticket_confirmation_approved = False
```

条件边只有在明确为 True 时才进入 `create_ticket`。

所以流程会结束，不创建工单。

### 练习 5 参考答案

`kind` 用来告诉应用层这是哪类中断，比如工单确认。

`confirmation_id` 用来标识用户确认的是哪一份待确认工单。

如果没有这些结构化字段，应用层只能靠自然语言猜测，很不稳定。

### 练习 6 参考答案

因为真实 Web 服务通常不是一次请求一直卡住等用户确认。

更合理的流程是：

```text
第一次请求运行图，遇到 interrupt，返回确认 payload。
第二次请求带 thread_id 和 approved 结果，再用 Command(resume=...) 恢复。
```

所以 `interrupt()` 不是让后端线程一直阻塞，而是把流程暂停点保存下来，等后续请求恢复。

这也是为什么 checkpointer 和 thread_id 是 interrupt 的基础条件。

## 九、本节自测题

### 自测 1

为什么 `interrupt()` 必须配合 checkpointer？

### 自测 2

为什么恢复时必须使用同一个 thread_id？

### 自测 3

为什么 interrupt 前只能做纯计算？

### 自测 4

本节为什么仍然使用 `FakeTicketCreator`？

### 自测 5

第 21 节手动恢复和第 22 节 interrupt 恢复最大的区别是什么？

### 自测 6

为什么说 `interrupt()` 只解决“等待人工输入”，不等于解决了权限、安全和幂等？

## 十、自测题参考答案

### 自测 1 参考答案

因为 `interrupt()` 会让图暂停。

暂停后必须保存当前 State、暂停节点和恢复位置。

这些信息都要靠 checkpointer 保存。

### 自测 2 参考答案

thread_id 是 checkpoint 的状态指针。

恢复时如果换了 thread_id，LangGraph 会找另一条线程，无法恢复原来的中断。

### 自测 3 参考答案

因为 resume 时触发 interrupt 的节点会从开头重新执行。

如果 interrupt 前有创建工单、写数据库、发通知这类副作用，就可能重复执行。

### 自测 4 参考答案

因为本节重点是 LangGraph interrupt 和恢复机制，不是测试真实 Java HTTP 服务。

`FakeTicketCreator` 能让测试稳定、快速、可重复，同时验证恢复后确实进入了创建节点。

### 自测 5 参考答案

第 21 节是应用层手动 `update_state` 并指定 `as_node`。

第 22 节是节点内部 `interrupt()` 正式暂停，应用层用 `Command(resume=...)` 恢复。

第 22 节更接近正式 human-in-the-loop。

### 自测 6 参考答案

因为 `interrupt()` 的职责很窄。

它只负责：

```text
暂停图
把 payload 返回给调用方
等待 Command(resume=...) 恢复
```

它不会自动判断：

```text
这个用户有没有权限
这个 thread_id 是不是属于当前用户
这个 confirmation_id 是否过期
这次确认是否已经消费过
重复恢复会不会重复创建工单
```

这些仍然需要应用层、数据库、业务服务和幂等设计共同保证。

## 十一、本节常见误区

### 误区 1：interrupt 就是 return

不是。

return 表示节点结束。

interrupt 表示节点暂停，等待外部输入后再继续。

### 误区 2：resume 后从 interrupt 下一行继续

不准确。

resume 时节点会从开头重新执行，直到再次到达 interrupt，然后把 resume 值返回给这一行。

所以 interrupt 前的代码必须可重复。

### 误区 3：有了 interrupt 就不用校验

错。

interrupt 只是拿到用户输入。

后端仍然要校验字段、确认状态、创建参数、幂等键和权限。

### 误区 4：payload 随便放字符串就行

学习 demo 可以。

业务系统不够。

真实项目里 payload 应该结构化，方便前端展示和后端恢复。

### 误区 5：任何图都能 interrupt

不行。

没有 checkpointer 和 thread_id，图无法可靠保存暂停位置并恢复。

## 十二、本节小结

本节把智能工单 Agent 的确认流程升级成了正式 human-in-the-loop：

```text
生成待确认工单
-> interrupt(payload)
-> 用户确认
-> Command(resume=...)
-> 恢复确认节点
-> create_ticket
```

现在你已经学会：

```text
checkpoint 保存状态
thread_id 找回线程
interrupt 暂停节点
Command(resume=...) 恢复节点
```

这四个能力合在一起，才是 LangGraph 多轮 Agent 和人工确认流程的核心基础。

下一节会学：

```text
节点错误处理、fallback 和流程兜底
```

也就是当中断恢复、工具调用或节点执行出现异常时，Agent 应该怎么稳定收尾。

## 十三、参考资料

1. LangGraph 官方文档：Interrupts
   https://docs.langchain.com/oss/python/langgraph/interrupts

2. LangGraph 官方文档：Persistence
   https://docs.langchain.com/oss/python/langgraph/persistence
