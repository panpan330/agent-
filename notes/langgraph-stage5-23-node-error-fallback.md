# 阶段 5 第 23 节：节点错误处理、fallback 和流程兜底

## 本节定位

前面几节我们已经把智能工单 Agent 的主链路搭出来了：

```text
用户输入
-> 意图识别
-> RAG 回答或进入工单流程
-> 判断是否需要创建工单
-> 抽取工单字段
-> 缺失字段追问
-> 用户确认
-> checkpoint/thread_id 保存会话
-> interrupt 暂停等待人工确认
-> 用户确认后恢复
-> 调用 Java mock 创建工单
```

这条链路在“所有步骤都正常”时已经能跑。

但真实项目不能只考虑正常路径。

真实项目一定会遇到：

```text
外部服务超时
Java 服务返回 500
Java 服务返回的数据不符合约定
节点拿不到该有的 State 字段
用户传了空的 thread_id
恢复 interrupt 时线程状态不对
某个节点代码出现了意外 RuntimeError
```

如果这些问题没有处理好，Agent 会出现三种糟糕结果：

```text
1. 程序直接崩掉，用户看见 500 或堆栈。
2. 用户不知道到底发生了什么，只觉得助手没反应。
3. 系统继续往下走，执行了不该执行的业务动作。
```

所以第 23 节要补上：

```text
节点错误处理
fallback
流程兜底
```

本节的核心目标不是让 Agent “永远不出错”。

这不现实。

本节的核心目标是：

```text
出错时，不乱继续、不泄露内部错误、能给用户明确反馈、能把错误写进 State。
```

## 本节学习目标

学完本节，你应该能讲清楚：

1. 什么是错误处理。
2. 什么是 fallback。
3. 什么是流程兜底。
4. 业务失败和程序异常有什么区别。
5. 为什么 Agent 节点出错不能直接把异常抛给用户。
6. 为什么不是所有异常都应该吞掉。
7. `AppException` 在本项目里的作用。
8. `final_answer` 和内部错误信息的边界。
9. 为什么 State 里要记录 `agent_error_code`、`agent_error_message`、`agent_error_node`。
10. 为什么创建工单失败要返回 `ticket_creation_status="failed"`。
11. 为什么“没有用户确认”是 blocked，不是 failed。
12. 为什么未知异常要返回通用兜底语。
13. 节点级兜底和图级兜底有什么区别。
14. interrupt 恢复失败时为什么也要兜底。
15. 为什么本节不直接引入复杂 retry。
16. LangGraph 官方错误处理思路是什么。
17. 怎么用测试验证失败路径。

## 本节先不学什么

本节暂时不做：

1. 不接真实 FastAPI Agent 接口。
2. 不引入 LangSmith tracing。
3. 不做生产级日志。
4. 不做复杂 retry policy。
5. 不做 LangGraph `error_handler` 实战。
6. 不做 PostgreSQL checkpoint。
7. 不做失败后自动补偿。
8. 不做工单创建幂等持久化。
9. 不做告警通知。
10. 不真实调用 Java 服务。

这些内容不是不重要。

只是当前学习顺序应该先掌握：

```text
一个节点失败时，State 应该怎么表达失败。
一个图执行失败时，调用方应该怎么得到安全结果。
```

有了这个基础，再学 retry、日志、trace、监控和补偿才不会乱。

## 一、基础知识铺垫

### 1. 什么是错误

在编程里，“错误”是一个大词。

它可以指很多情况：

```text
用户输入不合法
业务规则不允许
外部服务不可用
第三方接口返回异常
网络超时
程序代码写错
数据格式不符合约定
```

这些都叫错误，但处理方式不一样。

例如：

```text
用户没有提供订单号
```

这不是系统坏了。

它应该追问用户补充订单号。

再比如：

```text
Java 工单服务超时
```

这不是用户能修的。

它应该告诉用户稍后重试，并在日志里记录服务调用失败。

再比如：

```text
代码里访问了不存在的字段，触发 KeyError
```

这可能是程序 bug。

它不应该把堆栈展示给用户，而应该返回安全兜底语，并让开发者通过日志和测试排查。

所以第一条基础认知是：

```text
错误处理不是简单 try/except。
错误处理首先是错误分类。
```

### 2. 什么是异常

异常是程序运行过程中抛出的错误对象。

Python 里常见的异常有：

```text
ValueError
KeyError
TypeError
RuntimeError
TimeoutError
```

本项目还定义了自己的异常：

```python
AppException
```

`AppException` 用来表达项目内部已经识别过的业务错误或服务错误。

它包含：

```text
code
message
status_code
details
```

例如：

```text
code = TOOL_UPSTREAM_ERROR
message = 工单业务服务暂时不可用，请稍后重试。
status_code = 502
```

这类异常和普通 `RuntimeError` 不一样。

`AppException` 通常表示：

```text
系统知道发生了什么，也知道应该给用户什么提示。
```

普通 `RuntimeError` 通常表示：

```text
系统没有专门识别这个错误，不能随便把原始内容告诉用户。
```

### 3. 业务失败和程序异常的区别

业务失败是业务规则导致流程不能继续。

例如：

```text
没有用户确认，不能创建工单。
工单字段不完整，不能创建工单。
thread_id 为空，不能恢复线程。
```

程序异常是代码或运行环境出了问题。

例如：

```text
对象没有这个属性
访问字典缺少 key
外部依赖抛了未预期异常
序列化失败
```

二者处理方式不同。

业务失败通常可以明确告诉用户：

```text
请补充订单号。
创建工单前需要先得到用户确认。
当前会话没有待确认工单，请先发起工单流程。
```

程序异常通常不能直接告诉用户内部细节。

例如不能把下面这种内容放进用户回答：

```text
RuntimeError: database password leaked in stack
```

因为这可能泄露内部实现、路径、变量名、密钥、数据库信息。

所以本节新增了通用兜底语：

```text
智能工单流程暂时遇到异常，请稍后重试或联系人工客服。
```

### 4. 什么是 fallback

fallback 可以理解成：

```text
主方案失败后的备用方案。
```

例如：

```text
主方案：调用 Java 服务创建工单
失败后 fallback：告诉用户服务暂时不可用，请稍后重试
```

再比如：

```text
主方案：RAG 找到资料并回答
失败后 fallback：没有找到足够资料，进入工单流程
```

fallback 不是“掩盖错误”。

fallback 的目标是：

```text
在当前步骤不能正常完成时，仍然给出一个安全、清晰、可解释的结果。
```

一个好的 fallback 至少要满足四点：

```text
1. 用户能理解现在发生了什么。
2. 系统不会继续执行危险动作。
3. 内部错误不会直接暴露给用户。
4. State 里保留足够信息，方便后续日志和测试。
```

### 5. 什么是流程兜底

流程兜底比 fallback 更偏整体。

fallback 常常针对一个节点或一个调用。

流程兜底关注整条 Agent 流程：

```text
无论哪个节点出现可预期失败，流程都应该稳定结束。
无论图级执行出现未预期异常，调用方也应该拿到安全结果。
```

在本项目里，流程兜底体现在：

```text
create_ticket_node 出错时返回 failed State
run_ticket_agent_safely 捕获图级异常
resume_ticket_confirmation_interrupt_safely 捕获恢复失败
```

也就是说，兜底不只在一个地方。

真实项目通常会有多层兜底：

```text
节点内部兜底
Service 层兜底
API 层兜底
全局异常处理器兜底
日志和监控兜底
```

本节先做前两层：

```text
节点内部兜底
Agent 调用入口兜底
```

### 6. Agent 为什么特别需要错误处理

普通接口通常是一条简单链路：

```text
请求
-> service
-> 数据库
-> 响应
```

Agent 往往是多节点流程：

```text
用户输入
-> 意图识别
-> RAG
-> 工具调用
-> 字段抽取
-> 人工确认
-> Java 服务
-> 最终回答
```

节点越多，失败点越多。

而且 Agent 还有一个特点：

```text
它会根据 State 和条件边决定下一步。
```

如果错误没有写进 State，后续节点可能不知道前面失败了。

如果错误写得不清楚，条件边可能走错。

所以 Agent 的错误处理不是只打印日志。

它还要影响：

```text
State
final_answer
条件边
是否继续执行
是否需要人工介入
```

### 7. 节点错误处理的基本原则

本节采用这些原则：

```text
1. 业务规则失败，返回明确业务状态。
2. 已知服务错误，保留 AppException 的 code 和 message。
3. 未知异常，返回通用兜底语。
4. 不把原始异常堆栈放进 final_answer。
5. 出错节点要写入 node_history。
6. 出错时不要继续执行危险副作用。
7. 测试必须覆盖失败路径。
```

你要特别记住第 4 点：

```text
final_answer 是给用户看的，不是给开发者看的。
```

开发者需要的调试信息应该进入日志、trace 或监控。

用户需要的是清晰、安全、可行动的提示。

### 8. 哪些错误应该在节点内处理

适合在节点内处理的错误：

```text
节点自己调用的外部服务失败
节点自己构建参数失败
节点自己知道怎么给用户兜底
节点失败后不应该继续往下执行
```

例如 `create_ticket_node`。

它负责：

```text
把 ticket_fields 转成 CreateTicketArgs
调用 TicketCreator
拿到 CreatedTicket
```

所以创建失败时，它最清楚应该写什么字段：

```text
ticket_creation_status
ticket_creation_error_code
ticket_creation_error_message
final_answer
```

这类错误适合在节点内处理。

### 9. 哪些错误应该让外层处理

有些错误节点自己不一定知道怎么处理。

例如：

```text
图对象本身执行失败
线程恢复入口参数错误
checkpoint 存储异常
未来 API 层鉴权失败
```

这类错误可以在调用入口处理。

所以本节新增了：

```python
run_ticket_agent_safely(...)
resume_ticket_confirmation_interrupt_safely(...)
```

它们的职责是：

```text
调用图
如果图抛出异常，把异常转成安全 fallback State
```

这属于图级兜底。

### 10. 什么是用户安全的错误信息

用户安全的错误信息是：

```text
用户能理解
不泄露内部实现
不暴露密钥、路径、数据库、堆栈
不让用户误以为操作已经成功
```

例如安全：

```text
创建工单时遇到异常，请稍后重试或联系人工客服。
```

不安全：

```text
RuntimeError: database password leaked in stack
```

不安全的原因是：

```text
它暴露了内部异常类型
它可能包含敏感字段
它让用户看到开发者才应该看的信息
```

### 11. final_answer 和 error_message 的区别

本项目里有两个层次：

```text
final_answer
error_message
```

`final_answer` 是本轮 Agent 给用户看的最终回答。

`ticket_creation_error_message` 是创建工单节点记录的错误说明。

`agent_error_message` 是 Agent 层统一记录的错误说明。

这三者可以相同，也可以不同。

学习阶段为了清晰，本节让它们在失败时使用同一份用户安全消息。

以后生产项目可能会进一步拆开：

```text
final_answer: 用户友好提示
agent_error_message: 内部可控错误摘要
logs: 原始异常、堆栈、trace_id、上下文
```

你现在先记住：

```text
用户回答里不要放原始异常。
```

### 12. 什么是错误码

错误码是给系统看的稳定标识。

例如：

```text
TICKET_CONFIRMATION_REQUIRED
TOOL_UPSTREAM_ERROR
TICKET_CREATION_UNEXPECTED_ERROR
TICKET_AGENT_UNEXPECTED_ERROR
```

错误码的价值是：

```text
比自然语言稳定
方便测试
方便前端分支处理
方便日志统计
方便排查问题
```

错误消息可以改得更友好。

错误码应该尽量稳定。

例如：

```text
message 可以从“请稍后重试”改成“系统繁忙，请稍后再试”
code 最好仍然是 TOOL_UPSTREAM_ERROR
```

### 13. 什么是 blocked

本项目里创建工单节点有一种状态：

```text
ticket_creation_status = blocked
```

它不是 failed。

`blocked` 表示：

```text
流程被业务规则挡住了，还没有真正尝试创建。
```

例如：

```text
用户还没有确认，不能创建工单。
```

这不是创建失败。

因为系统根本不应该调用创建接口。

所以它返回：

```text
ticket_creation_status = blocked
ticket_creation_error_code = TICKET_CONFIRMATION_REQUIRED
```

而不是：

```text
ticket_creation_status = failed
```

这个区别很重要。

### 14. 什么是 failed

`failed` 表示：

```text
流程已经走到这个动作，但动作没有完成。
```

例如：

```text
用户已经确认
开始创建工单
Java 服务超时
```

这就是 failed。

再比如：

```text
用户已经确认
准备创建工单
但是 State 里没有找到工单字段
```

这也是 failed。

因为流程已经来到创建节点，但无法完成创建。

### 15. 为什么未知异常不能直接抛出

如果未知异常直接抛出，可能带来这些问题：

```text
API 返回 500
用户不知道该怎么办
测试无法稳定断言业务结果
前端无法展示业务状态
后续节点或调用方没有结构化 State
```

所以本节给未知异常一个统一出口：

```text
TICKET_CREATION_UNEXPECTED_ERROR
创建工单时遇到异常，请稍后重试或联系人工客服。
```

这不是说异常不重要。

而是说：

```text
用户侧要稳定，开发侧要排查。
```

开发侧的排查会在下一节日志和 trace_id 里继续加强。

### 16. 为什么不能吞掉所有异常

有些人学到 `try/except Exception` 后，会写成：

```python
try:
    do_something()
except Exception:
    pass
```

这很危险。

因为它会让系统看起来没事，但实际已经失败。

本节不是这么做。

本节的处理方式是：

```text
捕获异常
转成明确 State
写入错误码
写入错误节点
写入 fallback_used=True
给出 final_answer
```

也就是说：

```text
异常被处理了，但错误没有被隐藏。
```

这是好 fallback 和坏吞错的区别。

### 17. LangGraph 官方错误处理思路

LangGraph 官方资料里有一个很重要的观点：

```text
Errors are part of the flow.
```

意思是：

```text
错误不是流程之外的东西，错误也应该被纳入流程设计。
```

官方也把错误分成几类：

```text
临时错误：网络问题、限流，适合 retry。
LLM 可恢复错误：工具失败、解析失败，可以把错误写进 State，再让模型调整。
用户可修复错误：缺信息、不明确，可以 interrupt 让用户补充。
重试后仍失败：可以走 recovery branch。
未知错误：应该暴露给开发者排查。
```

本节没有立刻做 retry policy 和 `error_handler`。

原因是我们现在的项目还在学习主线。

当前更重要的是：

```text
先让你知道错误应该怎么分类。
先让 State 能表达失败。
先让用户侧有稳定 fallback。
```

等这些基础扎实后，再引入 LangGraph 的节点 retry、timeout、error handler，理解会更清楚。

## 二、本节主题系统讲解

### 1. 本节之前的问题

第 22 节之后，创建工单节点已经能处理 `AppException`：

```python
except AppException as exc:
    return {
        "ticket_creation_status": "failed",
        "ticket_creation_error_code": exc.code,
        "ticket_creation_error_message": exc.message,
        "final_answer": exc.message,
        "node_history": ["create_ticket"],
    }
```

这能处理 Java client 主动转换过的错误。

例如：

```text
TOOL_TIMEOUT
TOOL_UPSTREAM_ERROR
TOOL_RESULT_VALIDATION_FAILED
```

但它有几个不足：

```text
1. AppException 以外的异常会直接冒泡。
2. 没有统一 Agent 层错误字段。
3. 图级执行失败时没有安全包装。
4. interrupt 恢复失败时没有安全包装。
5. 失败路径没有统一 fallback_used 标记。
```

第 23 节就是补这些缺口。

### 2. 本节新增的状态字段

本节给 `TicketAgentState` 增加了四个 Agent 级错误字段：

```text
agent_error_code
agent_error_message
agent_error_node
fallback_used
```

它们分别表示：

```text
agent_error_code     Agent 级错误码
agent_error_message  Agent 级错误消息
agent_error_node     哪个节点或哪个入口触发兜底
fallback_used        本次是否使用了 fallback
```

为什么还要有 Agent 级错误字段？

因为 `ticket_creation_error_code` 只适合创建工单节点。

未来还有：

```text
RAG 节点错误
模型节点错误
订单查询节点错误
人工确认恢复错误
```

如果每个节点只写自己的错误字段，调用方要读很多地方。

Agent 级字段可以提供统一视角：

```text
这次 Agent 是否出现兜底？
兜底发生在哪里？
兜底错误码是什么？
用户最终看到什么？
```

### 3. 本节新增的通用 fallback 函数

本节新增：

```python
build_ticket_agent_fallback_state(...)
```

它返回：

```python
{
    "agent_error_code": code,
    "agent_error_message": message,
    "agent_error_node": node_name,
    "fallback_used": True,
    "final_answer": message,
    "node_history": [node_name],
}
```

这个函数的意义是：

```text
把通用兜底格式集中起来。
```

如果不封装，后面每个节点都可能手写一遍：

```text
agent_error_code
agent_error_message
agent_error_node
fallback_used
final_answer
node_history
```

字段越多，越容易漏。

封装后，只要调用：

```python
build_ticket_agent_fallback_state(
    node_name="ticket_agent_graph",
    code="...",
    message="...",
)
```

就能得到统一结构。

### 4. 本节新增的创建失败状态函数

本节新增：

```python
build_ticket_creation_failure_state(...)
```

它在通用 fallback 基础上，再加创建工单专用字段：

```text
ticket_creation_status = failed
ticket_creation_error_code
ticket_creation_error_message
```

也就是说，它返回的是两层信息：

```text
Agent 级错误信息
创建工单节点专用错误信息
```

这样做的好处是：

```text
通用调用方看 agent_error_code
创建工单业务看 ticket_creation_error_code
用户看 final_answer
```

不同角色看不同层次。

### 5. create_ticket_node 的错误处理升级

本节对 `create_ticket_node` 做了三类处理。

第一类：没有用户确认。

```text
ticket_confirmation_approved is not True
```

返回：

```text
ticket_creation_status = blocked
ticket_creation_error_code = TICKET_CONFIRMATION_REQUIRED
```

这不是 failed，因为根本没有尝试创建。

第二类：已知业务或服务错误。

```python
except AppException as exc:
```

返回：

```text
ticket_creation_status = failed
ticket_creation_error_code = exc.code
ticket_creation_error_message = exc.message
final_answer = exc.message
fallback_used = True
```

第三类：未知异常。

```python
except Exception:
```

返回：

```text
ticket_creation_status = failed
ticket_creation_error_code = TICKET_CREATION_UNEXPECTED_ERROR
ticket_creation_error_message = 创建工单时遇到异常，请稍后重试或联系人工客服。
final_answer = 创建工单时遇到异常，请稍后重试或联系人工客服。
fallback_used = True
```

注意：

```text
未知异常的原始内容不会进入 final_answer。
```

### 6. run_ticket_agent_safely 是什么

本节新增：

```python
run_ticket_agent_safely(user_message, graph=None)
```

它和 `run_ticket_agent(user_message)` 的区别是：

```text
run_ticket_agent:
    图执行失败就直接抛异常

run_ticket_agent_safely:
    图执行失败会返回 fallback State
```

这很适合作为未来 API 层调用 Agent 的入口。

因为 API 层通常希望拿到一个稳定结构，而不是在每个路由里重复写 try/except。

本节还给它加了可选 `graph` 参数，是为了测试。

测试里可以传入一个故意报错的假 graph，验证兜底逻辑。

### 7. resume_ticket_confirmation_interrupt_safely 是什么

第 22 节有：

```python
resume_ticket_confirmation_interrupt(...)
```

它负责用：

```python
Command(resume=...)
```

恢复 interrupt。

但恢复时也可能失败：

```text
thread_id 为空
checkpoint 状态异常
图对象执行失败
```

所以本节新增：

```python
resume_ticket_confirmation_interrupt_safely(...)
```

它会把恢复失败转成 fallback State。

其中 `thread_id` 为空是明确参数错误，所以返回：

```text
TICKET_THREAD_ID_INVALID
thread_id 不能为空。
```

其他未知异常返回：

```text
TICKET_AGENT_UNEXPECTED_ERROR
智能工单流程暂时遇到异常，请稍后重试或联系人工客服。
```

### 8. 本节为什么不让错误继续进入 create_ticket

如果前面节点出错，但条件边还继续进入 `create_ticket`，可能出现危险结果。

例如：

```text
ticket_fields 不完整
ticket_confirmation_approved 被错误设置为 True
create_ticket 继续调用 Java 服务
```

所以本项目已经有多道边界：

```text
字段不完整 -> ask_missing_ticket_fields
没有确认 -> create_ticket_node blocked
确认拒绝 -> END
创建失败 -> failed State
```

本节新增的 fallback 继续强化这个原则：

```text
出错时优先稳定结束，不继续执行危险动作。
```

### 9. 本节的错误状态分层

可以把本节状态分三层理解。

第一层：用户回答。

```text
final_answer
```

第二层：Agent 通用错误。

```text
agent_error_code
agent_error_message
agent_error_node
fallback_used
```

第三层：具体业务节点错误。

```text
ticket_creation_status
ticket_creation_error_code
ticket_creation_error_message
```

为什么要分层？

因为不同调用方关心的东西不一样。

用户只关心：

```text
我现在应该怎么办？
```

前端可能关心：

```text
要不要展示重试按钮？
要不要展示联系人工客服？
```

后端和测试关心：

```text
哪个节点失败？
错误码是什么？
流程是否用了 fallback？
```

### 10. 本节和第 21、22 节的关系

第 21 节解决：

```text
状态怎么保存
线程怎么找回
确认后怎么继续
```

第 22 节解决：

```text
怎么用 interrupt 正式暂停等待人工确认
```

第 23 节解决：

```text
恢复后继续创建时，如果失败怎么办
恢复 interrupt 本身失败怎么办
图执行本身失败怎么办
```

它们是一条连续链路：

```text
checkpoint/thread_id
-> interrupt
-> resume
-> create_ticket
-> error fallback
```

所以第 23 节不是额外内容。

它是让第 21、22 节具备真实项目稳定性的必要补充。

### 11. 本节为什么不直接上 retry

retry 很重要。

例如：

```text
网络短暂抖动
服务临时 429
数据库连接短暂失败
```

这些可以重试。

但本节暂时不实现复杂 retry，原因有三点：

```text
1. 当前 create_ticket 是写操作，重试必须配合幂等。
2. 你需要先学会错误分类和 fallback，再学 retry。
3. 下一节要学日志和 trace，retry 没有日志很难排查。
```

尤其是写操作。

创建工单不是普通查询。

如果没有幂等键和结果持久化，盲目重试可能导致重复创建。

所以本节只做：

```text
失败后稳定返回 failed State。
```

retry 后面再系统学。

### 12. 本节为什么不直接用 LangGraph error_handler

LangGraph 新版本支持节点级 `error_handler`。

它可以在节点重试耗尽后进入恢复分支。

但本节没有直接使用。

原因是：

```text
当前项目的 create_ticket_node 已经有清晰业务字段。
我们需要先让你看懂普通 try/except 如何映射到 State。
直接上 error_handler 会把 LangGraph API 和业务错误分类混在一起。
```

等你理解：

```text
错误分类
fallback State
final_answer 边界
节点级兜底
图级兜底
```

再学 `RetryPolicy`、`timeout`、`error_handler` 会更稳。

## 三、本节代码改动讲解

### 1. TicketAgentState 新增错误字段

新增：

```python
agent_error_code: str | None
agent_error_message: str | None
agent_error_node: str | None
fallback_used: bool
```

这几个字段不是替代原来的业务字段。

它们是 Agent 通用错误层。

例如创建工单失败时，State 里会同时有：

```text
agent_error_code = TOOL_UPSTREAM_ERROR
agent_error_node = create_ticket
fallback_used = True
ticket_creation_status = failed
ticket_creation_error_code = TOOL_UPSTREAM_ERROR
```

这说明：

```text
Agent 层知道用了 fallback。
创建工单节点知道自己失败了。
```

### 2. 新增通用错误常量

新增：

```python
TICKET_AGENT_FALLBACK_ERROR_CODE = "TICKET_AGENT_UNEXPECTED_ERROR"
TICKET_AGENT_FALLBACK_MESSAGE = "智能工单流程暂时遇到异常，请稍后重试或联系人工客服。"
TICKET_CREATION_UNEXPECTED_ERROR_CODE = "TICKET_CREATION_UNEXPECTED_ERROR"
TICKET_CREATION_UNEXPECTED_ERROR_MESSAGE = "创建工单时遇到异常，请稍后重试或联系人工客服。"
TICKET_THREAD_ID_INVALID_ERROR_CODE = "TICKET_THREAD_ID_INVALID"
```

这些常量的作用是：

```text
统一错误码
统一用户提示
避免字符串散落在代码和测试里
```

尤其是测试。

测试不应该到处复制同一段错误码字符串。

### 3. build_ticket_agent_fallback_state

新增函数：

```python
def build_ticket_agent_fallback_state(
    *,
    node_name: str,
    code: str = TICKET_AGENT_FALLBACK_ERROR_CODE,
    message: str = TICKET_AGENT_FALLBACK_MESSAGE,
) -> TicketAgentState:
```

它构建通用 fallback State。

这里使用关键字参数，是为了调用时更清楚：

```python
build_ticket_agent_fallback_state(
    node_name="ticket_agent_graph",
    code="DEMO_ERROR",
    message="流程暂时不可用。",
)
```

比下面这种更不容易看错：

```python
build_ticket_agent_fallback_state("ticket_agent_graph", "DEMO_ERROR", "流程暂时不可用。")
```

### 4. build_ticket_creation_failure_state

新增函数：

```python
def build_ticket_creation_failure_state(
    *,
    code: str,
    message: str,
) -> TicketAgentState:
```

它先调用通用 fallback：

```python
update = build_ticket_agent_fallback_state(
    node_name="create_ticket",
    code=code,
    message=message,
)
```

再追加创建工单字段：

```python
ticket_creation_status = failed
ticket_creation_error_code = code
ticket_creation_error_message = message
```

这样做避免了两份错误状态格式不一致。

### 5. create_ticket_node 捕获 AppException

原来就有：

```python
except AppException as exc:
```

本节把返回逻辑改成：

```python
return build_ticket_creation_failure_state(
    code=exc.code,
    message=exc.message,
)
```

这不是行为大改。

它是结构升级。

之前只写创建工单字段。

现在同时写：

```text
创建工单字段
Agent 通用错误字段
fallback_used
```

### 6. create_ticket_node 捕获未知异常

新增：

```python
except Exception:
    return build_ticket_creation_failure_state(
        code=TICKET_CREATION_UNEXPECTED_ERROR_CODE,
        message=TICKET_CREATION_UNEXPECTED_ERROR_MESSAGE,
    )
```

这解决了普通 `RuntimeError` 直接冒泡的问题。

注意这里没有写：

```python
message=str(exc)
```

这是刻意的。

因为 `str(exc)` 可能包含内部敏感信息。

本节统一用用户安全提示。

### 7. run_ticket_agent_safely

新增：

```python
def run_ticket_agent_safely(
    user_message: str,
    *,
    graph: Any | None = None,
) -> TicketAgentState:
```

它的逻辑是：

```text
选择 graph
构建初始 State
调用 graph.invoke
如果正常，返回正常结果
如果 AppException，转成对应 fallback
如果未知 Exception，转成通用 fallback
```

它适合作为以后 API 层调用 Agent 的入口。

### 8. resume_ticket_confirmation_interrupt_safely

新增：

```python
def resume_ticket_confirmation_interrupt_safely(...)
```

它包装第 22 节的恢复函数。

重点处理三类错误：

```text
AppException -> 保留业务错误码和消息
ValueError -> TICKET_THREAD_ID_INVALID
未知 Exception -> TICKET_AGENT_UNEXPECTED_ERROR
```

为什么 `ValueError` 单独处理？

因为当前 `build_ticket_agent_thread_config` 会对空 thread_id 抛：

```text
thread_id 不能为空。
```

这是明确参数错误，不应该归成未知异常。

## 四、本节测试讲解

本节测试重点不是“正常路径”。

正常路径前面已经测得很多。

本节重点测失败路径。

### 1. 测通用 fallback State

测试：

```python
test_build_ticket_agent_fallback_state_returns_user_safe_state
```

验证：

```text
agent_error_code
agent_error_message
agent_error_node
fallback_used
final_answer
node_history
```

都写对。

这个测试保证最基础的兜底格式不会被改坏。

### 2. 测 AppException 创建失败

测试：

```python
test_create_ticket_node_writes_failure_state_when_creator_fails
```

模拟：

```text
FakeTicketCreator 抛 AppException(TOOL_UPSTREAM_ERROR)
```

验证：

```text
ticket_creation_status = failed
ticket_creation_error_code = TOOL_UPSTREAM_ERROR
fallback_used = True
agent_error_node = create_ticket
```

这表示已知外部服务错误被正确转换成 State。

### 3. 测未知 RuntimeError 创建失败

测试：

```python
test_create_ticket_node_returns_safe_fallback_when_creator_crashes
```

模拟：

```text
FakeTicketCreator 抛 RuntimeError("database password leaked in stack")
```

验证：

```text
ticket_creation_error_code = TICKET_CREATION_UNEXPECTED_ERROR
final_answer = 用户安全兜底语
final_answer 不包含 database password
```

这个测试非常关键。

它验证：

```text
内部异常不会直接暴露给用户。
```

### 4. 测安全恢复函数

测试：

```python
test_resume_ticket_confirmation_interrupt_safely_handles_invalid_thread_id
```

模拟：

```text
thread_id = "   "
```

验证：

```text
agent_error_code = TICKET_THREAD_ID_INVALID
final_answer = thread_id 不能为空。
```

这说明明确参数错误被稳定处理。

### 5. 测恢复时未知异常

测试：

```python
test_resume_ticket_confirmation_interrupt_safely_handles_unexpected_error
```

模拟：

```text
BrokenTicketAgentGraph 抛 RuntimeError
```

验证：

```text
agent_error_code = TICKET_AGENT_UNEXPECTED_ERROR
fallback_used = True
```

这说明 checkpoint 或图执行异常不会直接炸穿调用方。

### 6. 测 run_ticket_agent_safely 正常路径

测试：

```python
test_run_ticket_agent_safely_returns_normal_result_when_graph_succeeds
```

输入：

```text
你好
```

验证：

```text
仍然返回 smalltalk 正常结果
没有 fallback_used
```

这说明 safe 包装不会影响正常路径。

### 7. 测 run_ticket_agent_safely 失败路径

两个测试：

```python
test_run_ticket_agent_safely_converts_app_exception_to_fallback_state
test_run_ticket_agent_safely_converts_unexpected_error_to_fallback_state
```

分别验证：

```text
AppException 会保留 code/message
RuntimeError 会转成通用安全兜底
```

这就是图级兜底的核心。

## 五、本节完成后的流程

### 1. 正常创建流程

```text
用户发起投诉
-> 抽取字段
-> interrupt 等确认
-> 用户确认
-> create_ticket
-> Java mock 返回成功
-> ticket_creation_status=created
-> final_answer=工单已创建...
```

### 2. Java 服务已知失败

```text
用户确认
-> create_ticket
-> Java client 抛 AppException(TOOL_UPSTREAM_ERROR)
-> create_ticket_node 返回 failed State
-> final_answer=工单业务服务暂时不可用，请稍后重试。
```

### 3. 创建节点未知异常

```text
用户确认
-> create_ticket
-> creator 抛 RuntimeError
-> create_ticket_node 捕获未知异常
-> 返回 TICKET_CREATION_UNEXPECTED_ERROR
-> final_answer=创建工单时遇到异常，请稍后重试或联系人工客服。
```

### 4. 图级未知异常

```text
run_ticket_agent_safely
-> graph.invoke 抛 RuntimeError
-> 返回 TICKET_AGENT_UNEXPECTED_ERROR
-> final_answer=智能工单流程暂时遇到异常，请稍后重试或联系人工客服。
```

### 5. interrupt 恢复参数错误

```text
resume_ticket_confirmation_interrupt_safely
-> thread_id 为空
-> build_ticket_agent_thread_config 抛 ValueError
-> 返回 TICKET_THREAD_ID_INVALID
-> final_answer=thread_id 不能为空。
```

## 六、你要真正记住的核心句子

1. 错误处理首先是错误分类，不是简单写 try/except。
2. 业务失败、外部服务失败、程序异常要分开处理。
3. fallback 是主路径失败后的安全备用结果。
4. 流程兜底是让 Agent 出错时稳定结束，不乱继续。
5. `final_answer` 是给用户看的，不能放原始异常堆栈。
6. `AppException` 是项目已经识别过的错误，可以保留它的 code 和 message。
7. 未知异常要返回通用安全提示。
8. 创建工单前没有用户确认是 blocked，不是 failed。
9. 已经尝试创建但没有成功才是 failed。
10. State 里要记录错误码、错误节点和 fallback 标记，方便测试和后续排查。
11. 节点级兜底处理节点自己能理解的失败。
12. 图级兜底处理整个 graph.invoke 或 resume 入口的异常。
13. retry 不是万能药，写操作重试必须考虑幂等。
14. 错误不能被偷偷吞掉，要转成明确 State。
15. 失败路径也必须写测试。

## 七、本节练习

### 练习 1：解释概念

请解释什么是 fallback。

参考答案：

fallback 是主方案失败后的备用方案。它不是假装没有错误，而是在当前步骤不能正常完成时，给出安全、清晰、可解释的结果。例如创建工单服务不可用时，不继续创建，也不暴露堆栈，而是返回“服务暂时不可用，请稍后重试”。

### 练习 2：区分 blocked 和 failed

为什么“没有用户确认，不能创建工单”应该是 `blocked`，而不是 `failed`？

参考答案：

因为系统还没有真正尝试创建工单。它只是被业务规则挡住了。`blocked` 表示当前动作不能开始，`failed` 表示动作已经开始或已经走到该节点但没有完成。

### 练习 3：判断错误信息是否安全

下面哪个更适合作为 `final_answer`？

```text
A. RuntimeError: database password leaked in stack
B. 创建工单时遇到异常，请稍后重试或联系人工客服。
```

参考答案：

选 B。`final_answer` 是给用户看的，不能泄露内部异常类型、堆栈、数据库、路径、变量名或敏感信息。A 只能进入开发者日志，不能直接返回给用户。

### 练习 4：解释 AppException

为什么 `AppException` 可以保留它的 `code` 和 `message`？

参考答案：

因为 `AppException` 是项目内部已经识别过、包装过的错误。它的 `message` 通常已经是用户可理解的安全提示，`code` 也是稳定的业务错误码。普通未知异常则没有经过这个安全包装，不能直接暴露。

### 练习 5：解释 State 分层

为什么创建工单失败时，既要写 `agent_error_code`，又要写 `ticket_creation_error_code`？

参考答案：

`agent_error_code` 是 Agent 通用错误层，方便调用方统一判断这次流程是否用了 fallback、错误发生在哪个节点。`ticket_creation_error_code` 是创建工单节点的业务专用错误层，方便工单创建逻辑、测试和后续前端针对创建失败做处理。

### 练习 6：解释 safe 包装

`run_ticket_agent_safely` 和 `run_ticket_agent` 的区别是什么？

参考答案：

`run_ticket_agent` 直接调用图，图执行失败时异常会往外抛。`run_ticket_agent_safely` 会捕获 `AppException` 和未知异常，把它们转换成结构化 fallback State，保证调用方能拿到稳定结果。

### 练习 7：判断 retry 是否适合

创建工单失败后，为什么本节没有马上加自动 retry？

参考答案：

因为创建工单是写操作。写操作重试必须考虑幂等，否则可能重复创建工单。本节先学习错误分类和 fallback，后续结合幂等、日志、trace 后再学习 retry 更稳。

### 练习 8：判断异常是否被吞掉

本节捕获 `Exception` 后返回 fallback State，这算不算“吞掉异常”？

参考答案：

不算坏的吞错。坏的吞错是 `except Exception: pass`，系统没有任何记录。本节捕获异常后写入错误码、错误节点、`fallback_used=True` 和 `final_answer`，错误被转换成了可观察的 State。后续再配合日志和 trace，开发者就能排查。

## 八、本节自测题

### 自测 1

Agent 节点错误处理为什么不能只靠 FastAPI 全局异常处理器？

参考答案：

因为 LangGraph 节点错误会影响 State、条件边和后续流程。FastAPI 全局异常处理器只能在接口最外层返回 HTTP 错误，它不知道哪个节点失败、是否应该继续、State 里应该写什么。节点级错误需要在 Agent 流程内部表达。

### 自测 2

为什么 `final_answer` 不能放 `str(exc)`？

参考答案：

因为 `str(exc)` 可能包含内部实现细节、路径、密钥、数据库信息或堆栈片段。`final_answer` 是给用户看的，必须使用用户安全提示。原始异常应该进入日志或监控，不应该直接暴露。

### 自测 3

如果 Java 服务返回 500，本项目应该把它归成哪类错误？

参考答案：

它属于外部业务服务或上游服务错误。`JavaTicketClient` 会把它转换成 `AppException(code="TOOL_UPSTREAM_ERROR")`，`create_ticket_node` 再把它转成 `ticket_creation_status="failed"` 的 State。

### 自测 4

为什么 `fallback_used=True` 有价值？

参考答案：

它让调用方、测试和后续日志能快速判断本次流程是否走了兜底路径。没有这个字段时，只能通过错误码或 final_answer 猜测。明确字段更稳定，也更适合后续统计。

### 自测 5

`resume_ticket_confirmation_interrupt_safely` 为什么要单独处理 `ValueError`？

参考答案：

因为空 `thread_id` 是明确的参数错误，不是未知系统异常。单独处理后可以返回稳定错误码 `TICKET_THREAD_ID_INVALID` 和明确消息 `thread_id 不能为空。`，而不是泛化成系统异常。

### 自测 6

LangGraph 官方为什么说错误是流程的一部分？

参考答案：

因为 Agent 流程不是简单直线执行。不同错误要触发不同策略：临时错误可能 retry，工具错误可能写入 State 后让模型调整，缺信息可能 interrupt 等用户补充，未知错误可能上报开发者。错误会影响流程下一步，所以它本身就是流程设计的一部分。

### 自测 7

什么时候适合节点级兜底，什么时候适合图级兜底？

参考答案：

节点级兜底适合节点自己能理解和表达的错误，例如创建工单失败。图级兜底适合整个 `graph.invoke` 或 resume 入口失败，例如图对象异常、checkpoint 异常、调用入口参数错误。节点级更细，图级更外层。

### 自测 8

如果测试只测正常路径，不测失败路径，会有什么问题？

参考答案：

正常路径通过只能说明“顺利时能跑”。真实项目里最容易出问题的是外部服务失败、异常输入和恢复失败。如果不测失败路径，可能出现异常泄露、错误状态缺字段、流程继续执行危险动作等问题。

## 九、本节常见误区

### 误区 1：加了 try/except 就是错误处理

不对。

错误处理不是语法动作，而是设计动作。

要先判断：

```text
这是什么错误？
谁能修？
要不要继续流程？
要不要给用户看？
要写什么 State？
要不要报警？
```

### 误区 2：所有错误都应该返回同一句话

不对。

用户没确认，应该说需要确认。

服务超时，应该说服务暂时不可用。

未知异常，才用通用兜底语。

错误分类越清楚，用户体验和排查效率越好。

### 误区 3：用户看不见异常就等于安全

不对。

如果异常被 `pass` 掉，用户可能看不见，但系统也不知道发生过什么。

安全的做法是：

```text
用户看到安全提示
State 记录错误码
日志记录原始异常
测试覆盖失败路径
```

### 误区 4：retry 可以解决大部分错误

不对。

retry 只适合临时错误。

例如网络抖动、限流、短暂不可用。

但下面这些不能靠 retry：

```text
参数错误
权限错误
字段缺失
用户没有确认
代码 bug
数据契约不一致
```

写操作 retry 还必须考虑幂等。

### 误区 5：fallback 就是降级回答一句话

不完整。

fallback 不只是文案。

它还应该包括：

```text
错误码
错误节点
业务状态
是否使用兜底
是否继续流程
```

在 Agent 项目里，fallback 应该进入 State，而不只是返回一句文本。

## 十、本节小结

本节把智能工单 Agent 从“正常能跑”推进到“失败时能稳定收尾”。

新增能力包括：

```text
通用 Agent fallback State
创建工单失败 State
创建节点未知异常兜底
图级安全运行入口
interrupt 恢复安全入口
失败路径测试
```

现在你应该能讲清楚：

```text
业务失败和程序异常不同
blocked 和 failed 不同
AppException 和未知异常不同
节点级兜底和图级兜底不同
final_answer 和内部错误不同
```

这是 Agent 工程化非常关键的一步。

下一节会继续补：

```text
LangGraph 日志、trace_id 和可观测性
```

也就是把这节的错误状态和项目已有的 trace_id、日志体系串起来，让失败不仅能返回给用户，也能被开发者追踪和排查。

## 十一、参考资料

1. LangGraph 官方文档：Thinking in LangGraph
   https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph

2. LangGraph 官方文档：Fault tolerance
   https://docs.langchain.com/oss/python/langgraph/fault-tolerance

3. LangGraph 官方文档：Use the graph API
   https://docs.langchain.com/oss/python/langgraph/use-graph-api

4. LangGraph 官方文档：Persistence
   https://docs.langchain.com/oss/python/langgraph/persistence

5. 本仓库：阶段 1 第 14 节统一异常处理
   `notes/fastapi-stage1-14-exception-handling.md`

6. 本仓库：阶段 3 第 7 节工具调用错误处理
   `notes/tool-calling-stage3-07-tool-error-handling.md`

7. 本仓库：阶段 4 第 21 节 RAG 错误处理
   `notes/rag-stage4-21-error-handling.md`
