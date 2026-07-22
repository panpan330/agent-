# 阶段 5 第 24 节：LangGraph 日志、trace_id 和可观测性

## 本节定位

第 23 节我们完成了：

```text
节点错误处理
fallback
流程兜底
```

也就是说，Agent 出错时已经不会轻易把内部异常直接暴露给用户。

但只做到这一步还不够。

因为用户看到的是：

```text
智能工单流程暂时遇到异常，请稍后重试或联系人工客服。
```

这个回答对用户是安全的。

但开发者还需要知道：

```text
是哪一次请求出错？
trace_id 是什么？
thread_id 是什么？
哪个节点最后执行？
是否触发了 interrupt？
是否用了 fallback？
创建工单是否成功？
失败错误码是什么？
耗时大概是多少？
有没有把用户原始输入写进日志？
```

这就是第 24 节要解决的问题：

```text
让智能工单 Agent 的执行过程可观察、可追踪、可排查。
```

本节不会马上引入 LangSmith。

本节先基于项目已有的：

```text
logging
trace_id
node_history
State
pytest caplog
```

做一套本地可验证的 Agent 可观测性基础。

后续如果接 LangSmith、OpenTelemetry、日志平台或监控平台，这一节的思想仍然适用。

## 本节学习目标

学完本节，你应该能讲清楚：

1. 什么是可观测性。
2. logging、trace_id、node_history 分别解决什么问题。
3. 为什么 Agent 比普通接口更需要可观测性。
4. 为什么日志不能只写“开始了”和“结束了”。
5. 为什么不能记录原始用户问题。
6. trace_id 是怎么从请求进入日志的。
7. 为什么要把当前 trace_id 写入 Agent State。
8. 为什么要记录 operation、thread_id、intent、last_node、fallback_used。
9. 如何记录 Agent 开始、结束、失败。
10. 如何记录创建工单节点的开始、成功、失败。
11. 为什么未知异常日志里也不直接写原始异常消息。
12. 如何用 `caplog` 测试日志。
13. LangGraph stream、debug stream、LangSmith tracing 和本地 logging 的区别。
14. 当前项目距离生产级可观测性还缺什么。

## 本节先不学什么

本节暂时不做：

1. 不接 LangSmith API key。
2. 不打开 LangSmith tracing。
3. 不接 OpenTelemetry。
4. 不接 ELK、Loki、Datadog、Grafana。
5. 不做分布式链路追踪。
6. 不做日志采样。
7. 不做成本统计看板。
8. 不做慢节点性能分析平台。
9. 不记录完整 prompt。
10. 不记录完整用户输入。

原因很简单：

```text
你现在要先学会“应该观察什么”和“什么不能乱记”。
```

如果基础没学清楚，直接上平台，只会看到一堆日志和 trace，却不知道哪些信息真正有用。

## 一、基础知识铺垫

### 1. 什么是可观测性

可观测性可以理解成：

```text
系统运行后，开发者能不能从外部信息判断系统内部发生了什么。
```

比如用户说：

```text
我刚才点了确认，但没有创建工单。
```

如果系统有良好的可观测性，你应该能查到：

```text
这次请求的 trace_id
对应的 thread_id
Agent 执行了哪些节点
是否触发了 interrupt
resume 的 approved 是 True 还是 False
create_ticket 有没有执行
Java 服务有没有返回错误
最终是否走了 fallback
耗时主要发生在哪里
```

如果没有可观测性，开发者只能猜：

```text
是不是用户没确认？
是不是 thread_id 错了？
是不是 Java 服务挂了？
是不是 Agent 条件边没走对？
是不是创建成功但前端没展示？
```

猜测不是工程能力。

可观测性就是把猜测变成证据。

### 2. logging 是什么

logging 是程序主动写出的运行记录。

例如：

```text
ticket_agent_started operation=invoke_safe message_length=2
ticket_agent_finished operation=invoke_safe last_node=build_direct_answer fallback_used=False
ticket_agent_create_ticket_failed code=TOOL_UPSTREAM_ERROR error_type=AppException
```

日志的作用是：

```text
告诉开发者某个时间点发生了什么。
```

它适合记录：

```text
请求开始
请求结束
关键节点开始
关键节点成功
关键节点失败
错误码
耗时
状态变化摘要
```

日志不适合记录：

```text
完整用户隐私
完整 prompt
完整 API key
完整身份信息
完整堆栈暴露给所有人
大段检索内容
```

所以日志不是“想记什么就记什么”。

日志是经过选择的工程事实。

### 3. trace_id 是什么

`trace_id` 可以理解成：

```text
一次请求或一次调用链路的追踪编号。
```

一个请求进入系统时，系统生成或复用一个 trace_id。

之后这个请求产生的日志都带着同一个 trace_id。

这样你就能从一堆日志里筛出：

```text
这一次请求相关的所有日志。
```

本项目在阶段 1 第 13 节已经实现过：

```text
X-Trace-Id 请求头
ContextVar 保存当前 trace_id
LogRecordFactory 给日志自动补 trace_id
build_trace_headers 传给下游 Java 服务
```

也就是说，trace_id 不是第 24 节才出现。

第 24 节是把它接入 Agent 层。

### 4. node_history 是什么

`node_history` 是 Agent State 里记录的节点执行路径。

例如：

```text
[
  "normalize_user_input",
  "classify_intent",
  "decide_ticket_need",
  "extract_ticket_fields",
  "request_ticket_confirmation",
  "create_ticket"
]
```

它回答的问题是：

```text
Agent 走了哪些节点？
```

它和日志不一样。

日志是外部观察记录。

`node_history` 是流程 State 的一部分。

二者可以互补：

```text
node_history 告诉你路线。
日志告诉你什么时候开始、什么时候结束、耗时多少、是否失败。
```

### 5. trace_id、thread_id、node_history 的区别

这三个东西很容易混。

它们分别解决不同问题。

`trace_id` 解决：

```text
这一次请求的日志怎么串起来？
```

`thread_id` 解决：

```text
LangGraph checkpoint 里怎么找回同一条会话线程？
```

`node_history` 解决：

```text
这次 Agent 执行走过哪些节点？
```

举例：

```text
trace_id = trace-001
thread_id = ticket-thread-001
node_history = normalize -> classify -> extract -> interrupt
```

含义是：

```text
这一次请求编号是 trace-001。
它操作的是 ticket-thread-001 这条会话线程。
这次图执行到 request_ticket_confirmation 后触发 interrupt。
```

三者不能互相替代。

### 6. 为什么 Agent 比普通接口更需要可观测性

普通接口可能只有一两个步骤：

```text
接收请求
查数据库
返回响应
```

Agent 有多个节点、条件边、外部工具和中断恢复：

```text
意图识别
RAG
字段抽取
缺失字段追问
用户确认
interrupt
checkpoint
Java 服务调用
fallback
```

如果没有可观测性，排查会非常困难。

例如同样是“没创建工单”，可能有很多原因：

```text
意图识别成了 smalltalk
字段缺少 order_id
用户拒绝确认
thread_id 不对
interrupt 没恢复
Java 服务失败
create_ticket 节点未知异常
```

所以 Agent 的日志不能只写：

```text
agent started
agent finished
```

它必须能帮助你定位：

```text
路由
节点
状态
错误
耗时
是否中断
是否兜底
```

### 7. 什么信息应该写进 Agent 日志

本节选择记录这些字段：

```text
operation
thread_id
actor_id
message_length
elapsed_ms
intent
node_count
last_node
interrupted
fallback_used
agent_error_code
ticket_creation_status
ticket_id
category
priority
error_type
```

这些字段的特点是：

```text
能帮助排查问题
又不会直接泄露用户完整输入
```

例如 `message_length` 能告诉你输入是不是空、是不是异常长。

但它不会把用户的原始投诉内容写入日志。

### 8. 什么信息不应该写进 Agent 日志

本节刻意不记录：

```text
原始 user_message
完整工单 description
完整 prompt
完整 RAG chunk 内容
API key
用户完整身份信息
原始未知异常 message
```

原因是：

```text
日志通常会被更多系统读取、存储、搜索、转发。
```

一旦敏感信息进入日志，后续很难彻底清理。

所以本节测试里明确断言：

```text
我要投诉订单 1001，物流一直不动
```

不会出现在 Agent 日志中。

这不是形式主义。

这是工程安全边界。

### 9. 为什么未知异常日志里也不直接写 str(exc)

第 23 节我们已经说过，未知异常不能进 `final_answer`。

第 24 节再补一层：

```text
未知异常也不要随便把 str(exc) 写进业务日志。
```

例如测试里故意抛：

```text
RuntimeError("database password leaked in stack")
```

如果日志里直接写：

```text
error=database password leaked in stack
```

也不安全。

本节日志只写：

```text
error_type=RuntimeError
code=TICKET_CREATION_UNEXPECTED_ERROR
```

这能说明出错类型和错误码，又不会把异常消息原文写出来。

真实生产里，是否记录完整堆栈要看日志权限、脱敏策略、合规要求和环境隔离。

当前学习项目先采用保守策略：

```text
业务日志不写未知异常原文。
```

### 10. elapsed_ms 是什么

`elapsed_ms` 是耗时，单位是毫秒。

它回答的问题是：

```text
这次 Agent 调用花了多久？
```

例如：

```text
elapsed_ms=12.35
```

有了耗时，你可以发现：

```text
某次请求很慢
某个节点很慢
外部服务调用变慢
恢复 interrupt 很慢
```

本节用：

```python
perf_counter()
```

计算耗时。

`perf_counter()` 适合测量短时间间隔，比直接用系统时间更适合做耗时统计。

### 11. operation 是什么

本节日志里有 `operation`。

例如：

```text
invoke
invoke_safe
invoke_thread
resume_interrupt
```

它表示当前执行入口。

为什么要记录它？

因为同一个 Agent 图可能有不同调用方式：

```text
普通单轮调用
安全包装调用
带 thread_id 的调用
interrupt 恢复调用
```

如果日志里不记录 operation，你看到：

```text
ticket_agent_finished
```

但不知道它是第一次运行，还是恢复运行。

### 12. interrupted 字段有什么用

`interrupted=True` 表示：

```text
本次图执行返回了 __interrupt__。
```

这对第 22 节之后非常重要。

因为 Agent 不是每次都会给最终答案。

有时它会：

```text
暂停等待用户确认
```

这不是失败。

日志里需要能区分：

```text
正常结束
中断等待
失败兜底
```

所以本节的 observation metadata 里有：

```text
interrupted
fallback_used
ticket_creation_status
```

它们合在一起能更清楚地表达执行结果。

### 13. 本地 logging 和 LangSmith tracing 的区别

本地 logging 是我们自己写日志。

它适合：

```text
快速排查
记录业务关键字段
跟现有 FastAPI 日志系统融合
用 pytest caplog 测试
```

LangSmith tracing 更像专门的 LLM/Agent 可观测平台。

官方文档里说，trace 是应用从输入到输出的一系列步骤，每个步骤可以表示成一个 run。LangSmith 可以用来可视化这些执行步骤。

LangSmith 更适合：

```text
可视化复杂 Agent 执行
查看每一步输入输出
分析模型调用
评估应用表现
监控生产表现
调试 LangGraph 节点和状态变化
```

本节暂时不接 LangSmith，是为了先把本地可观测字段设计好。

以后接 LangSmith 时，这些字段也可以变成 trace metadata。

### 14. LangGraph stream 和日志的区别

第 12 节我们学过：

```text
graph.invoke
graph.stream
```

LangGraph 官方 streaming 文档里提到，stream 可以用 `updates`、`values`、`messages`、`custom`、`checkpoints`、`tasks`、`debug` 等模式观察图执行。

stream 更适合：

```text
实时看到节点更新
给前端展示进度
调试每一步 State 变化
观察 checkpoint 和 task 事件
```

logging 更适合：

```text
长期保存
线上排查
按 trace_id 搜索
统计错误码
统计耗时
和 API 日志、Java 服务日志串联
```

二者不是谁替代谁。

更准确的理解是：

```text
stream 是执行过程的实时输出。
logging 是系统运行的持久记录。
```

### 15. 可观测性不是越多越好

初学时容易以为：

```text
记录越多越好。
```

这不对。

日志太少，排查困难。

日志太多，也会带来问题：

```text
存储成本变高
搜索变慢
噪声太多
敏感信息风险变高
开发者找不到重点
```

所以可观测性不是“全部记录”。

可观测性是：

```text
记录能解释系统行为的关键事实。
```

本节选择的关键事实是：

```text
谁调用
怎么调用
走到哪里
是否中断
是否兜底
是否创建成功
失败错误码
耗时
trace_id
```

## 二、本节主题系统讲解

### 1. 本节之前已有的基础

项目已有：

```python
app/core/trace.py
app/core/logging.py
```

`trace.py` 提供：

```text
generate_trace_id
get_or_create_trace_id
get_trace_id
set_trace_id
reset_trace_id
build_trace_headers
```

`logging.py` 提供：

```text
install_trace_id_log_record_factory
configure_logging
```

其中关键机制是：

```text
LogRecordFactory 会给每条日志补 trace_id。
```

所以 Agent 层不需要自己在每条日志 message 里拼 `trace_id`。

只要当前上下文里设置了 trace_id，日志记录就能通过 `record.trace_id` 拿到它。

### 2. 本节为什么仍然把 trace_id 写进 State

既然日志已经有 trace_id，为什么还要加：

```python
agent_trace_id: str
```

原因是：

```text
日志是外部记录。
State 是 Agent 本轮执行结果的一部分。
```

把 trace_id 写进 State 有几个好处：

```text
1. 测试可以直接断言 Agent 输入捕获了当前 trace_id。
2. 后续 API 响应可以选择返回 trace_id 给前端。
3. 后续 LangSmith metadata 可以复用。
4. 出错时 fallback State 也能和请求 trace 关联。
```

但是要注意：

```text
trace_id 不是业务状态。
```

它不决定流程走向。

它只是排查和关联日志用的技术上下文。

### 3. 本节新增 observation metadata

本节新增：

```python
build_ticket_agent_observation_metadata(...)
```

它把完整 State 摘要成一组适合日志和监控的字段：

```text
operation
trace_id
thread_id
intent
node_count
last_node
interrupted
fallback_used
agent_error_code
ticket_creation_status
elapsed_ms
```

为什么不直接把完整 State 打进日志？

因为 State 里可能有：

```text
user_message
ticket_fields.description
pending_ticket_confirmation.message
rag_citations
created_ticket
```

这些有些可能很长，有些可能敏感。

所以本节先做摘要。

摘要的原则是：

```text
能定位问题，但不暴露完整内容。
```

### 4. 本节新增 Agent 开始日志

本节新增：

```python
log_ticket_agent_run_started(...)
```

日志类似：

```text
ticket_agent_started operation=invoke_safe thread_id=- actor_id=- message_length=2
```

它记录：

```text
operation
thread_id
actor_id
message_length
```

注意这里是：

```text
message_length
```

不是：

```text
user_message
```

这就是安全边界。

开发者能知道用户输入长度，但看不到原始内容。

### 5. 本节新增 Agent 结束日志

本节新增：

```python
log_ticket_agent_run_finished(...)
```

日志类似：

```text
ticket_agent_finished operation=invoke_safe thread_id=- elapsed_ms=3.12 intent=smalltalk node_count=3 last_node=build_direct_answer interrupted=False fallback_used=False agent_error_code=- ticket_creation_status=-
```

这条日志回答几个问题：

```text
这次调用是什么入口？
耗时多少？
识别成什么意图？
执行了几个节点？
最后一个节点是什么？
是否中断？
是否走 fallback？
错误码是什么？
工单创建状态是什么？
```

它比单纯写：

```text
agent finished
```

有用得多。

### 6. 本节新增 Agent 失败日志

本节新增：

```python
log_ticket_agent_run_failed(...)
```

日志类似：

```text
ticket_agent_failed operation=invoke_safe thread_id=- elapsed_ms=1.23 code=TICKET_AGENT_UNEXPECTED_ERROR error_type=RuntimeError
```

它记录：

```text
错误码
异常类型
耗时
operation
thread_id
```

它不记录：

```text
原始异常 message
原始用户 message
```

这就是本节的安全取舍。

### 7. run_ticket_agent 的日志

`run_ticket_agent` 现在会：

```text
记录开始日志
调用 graph.invoke
成功后记录结束日志
失败后记录失败日志并继续抛异常
```

为什么失败后继续抛异常？

因为 `run_ticket_agent` 是普通入口。

它不负责兜底。

兜底入口是：

```python
run_ticket_agent_safely
```

这体现了清晰分工：

```text
run_ticket_agent: 原始执行入口
run_ticket_agent_safely: 安全兜底执行入口
```

### 8. run_ticket_agent_safely 的日志

`run_ticket_agent_safely` 现在会：

```text
记录开始日志
调用 graph.invoke
成功后记录结束日志
AppException 失败时记录失败日志，返回 fallback State，再记录结束日志
未知异常失败时记录失败日志，返回通用 fallback State，再记录结束日志
```

它的价值是：

```text
API 层以后可以调用 safe 入口，并拿到稳定 State。
日志里也能看到这次是成功、失败还是 fallback。
```

### 9. run_ticket_agent_in_thread 的日志

`run_ticket_agent_in_thread` 是第 21 节之后的线程执行入口。

它现在会记录：

```text
operation=invoke_thread
thread_id
actor_id
message_length
interrupted
elapsed_ms
```

这个入口常用于：

```text
带 checkpoint 的图
带 thread_id 的会话
第 22 节 interrupt 暂停
```

所以它必须记录 thread_id。

否则你看到一次 interrupt，却不知道它属于哪条线程。

### 10. resume_ticket_confirmation_interrupt 的日志

`resume_ticket_confirmation_interrupt` 是第 22 节恢复 interrupt 的入口。

它现在会记录：

```text
operation=resume_interrupt
thread_id
actor_id
elapsed_ms
last_node
ticket_creation_status
fallback_used
```

这很重要。

因为工单创建往往发生在 resume 之后。

排查“用户确认后没创建工单”时，你要重点看：

```text
resume_interrupt 是否执行
resume_interrupt 对应的 thread_id 是否正确
last_node 是否是 create_ticket
ticket_creation_status 是否是 created
fallback_used 是否是 True
```

### 11. create_ticket_node 的日志

创建工单是本 Agent 当前最关键的写操作。

所以本节给它加了节点级日志。

未确认时：

```text
ticket_agent_create_ticket_blocked code=TICKET_CONFIRMATION_REQUIRED
```

开始创建时：

```text
ticket_agent_create_ticket_started category=complaint priority=high related_order_id=1001 idempotency_key=...
```

创建成功时：

```text
ticket_agent_create_ticket_finished status=created ticket_id=T1001 category=complaint priority=high
```

创建失败时：

```text
ticket_agent_create_ticket_failed code=TOOL_UPSTREAM_ERROR error_type=AppException
```

未知异常时：

```text
ticket_agent_create_ticket_failed code=TICKET_CREATION_UNEXPECTED_ERROR error_type=RuntimeError
```

注意：

```text
没有记录完整 description。
没有记录原始 user_message。
```

### 12. 为什么日志里有 idempotency_key

创建工单是写操作。

写操作排查时经常要知道：

```text
这次创建请求是不是同一个业务动作？
重复请求是否用了同一个幂等键？
```

本项目的 `idempotency_key` 来自确认内容的 hash。

它不是用户原始描述。

记录它可以帮助排查：

```text
同一次确认是否重复创建
同一次重试是否使用同一个 key
Java 服务是否按幂等键处理
```

真实项目里是否记录完整幂等键，要看安全要求。

学习项目先记录完整值，方便理解。

### 13. 为什么要测试日志

很多人写日志只靠肉眼看。

这不够。

关键日志应该测试。

本节新增测试验证：

```text
Agent safe 入口会写 started 和 finished 日志
日志记录带有 trace_id
日志不会包含原始用户消息
创建工单成功会写 started 和 finished
创建工单未知异常会写失败日志
未知异常日志不包含原始异常 message
observation metadata 摘要字段正确
```

这说明：

```text
日志也是可测试的工程行为。
```

### 14. caplog 是什么

`caplog` 是 pytest 提供的日志捕获工具。

它可以捕获测试期间产生的日志。

例如：

```python
caplog.set_level(logging.INFO, logger="app.agents.ticket_agent")
```

意思是：

```text
捕获 app.agents.ticket_agent 这个 logger 的 INFO 及以上日志。
```

然后可以断言：

```python
assert "ticket_agent_started operation=invoke_safe" in caplog.text
```

也可以检查每条日志记录：

```python
record.trace_id
record.name
record.getMessage()
```

本节用 `caplog` 测试 trace_id，就是为了确认日志记录真的带上了当前请求的 trace_id。

### 15. 为什么要安装 LogRecordFactory

项目里的日志记录要有 `trace_id` 字段，需要：

```python
install_trace_id_log_record_factory()
```

它的作用是：

```text
创建 LogRecord 时自动补 trace_id。
```

FastAPI 应用启动时会配置 logging。

但单元测试里直接调用 Agent 函数时，不一定经过完整应用启动流程。

所以测试里主动调用：

```python
install_trace_id_log_record_factory()
```

这样 `caplog.records` 里的每条记录都可以读取：

```python
record.trace_id
```

### 16. 本节和下一节的关系

第 24 节做的是：

```text
本地日志和 trace_id 基础
```

下一节第 25 节会做：

```text
LangGraph 测试：fake LLM / fake RAG / fake Java client
```

为什么顺序是这样？

因为测试复杂 Agent 时，你需要知道：

```text
成功路径是否走对
失败路径是否走对
日志是否能辅助排查
fake 依赖是否真的隔离外部系统
```

第 24 节的可观测性会让第 25 节的测试体系更完整。

## 三、本节代码改动讲解

### 1. 新增 logging 和 perf_counter

新增：

```python
import logging
from time import perf_counter
```

`logging` 用来写业务日志。

`perf_counter` 用来统计耗时。

同时新增：

```python
logger = logging.getLogger(__name__)
```

在当前文件里，`__name__` 是：

```text
app.agents.ticket_agent
```

所以测试里可以针对这个 logger 捕获日志。

### 2. TicketAgentState 新增 agent_trace_id

新增：

```python
agent_trace_id: str
```

`build_ticket_agent_input` 现在返回：

```python
{
    "user_message": user_message,
    "agent_trace_id": get_trace_id(),
    "node_history": [],
}
```

这表示：

```text
Agent 开始执行时，把当前请求上下文里的 trace_id 写入 State。
```

### 3. build_ticket_agent_observation_metadata

新增：

```python
build_ticket_agent_observation_metadata(...)
```

它不是业务逻辑。

它是把 State 转换成日志摘要。

例如输入：

```python
{
    "agent_trace_id": "trace-agent-001",
    "intent": "ticket_request",
    "node_history": ["normalize_user_input", "create_ticket"],
    "fallback_used": True,
    "agent_error_code": "TOOL_UPSTREAM_ERROR",
    "ticket_creation_status": "failed",
}
```

输出摘要：

```python
{
    "operation": "invoke_safe",
    "trace_id": "trace-agent-001",
    "thread_id": "ticket-thread-001",
    "intent": "ticket_request",
    "node_count": 2,
    "last_node": "create_ticket",
    "interrupted": False,
    "fallback_used": True,
    "agent_error_code": "TOOL_UPSTREAM_ERROR",
    "ticket_creation_status": "failed",
    "elapsed_ms": 12.35,
}
```

这个函数让日志字段有统一来源。

### 4. _safe_log_value

新增：

```python
def _safe_log_value(value: object | None) -> str:
```

它把 `None`、空字符串转换成：

```text
-
```

为什么需要？

因为日志里出现：

```text
thread_id=None
```

不如：

```text
thread_id=-
```

统一。

`-` 表示：

```text
当前没有这个值。
```

### 5. _elapsed_ms_since

新增：

```python
def _elapsed_ms_since(start_time: float) -> float:
    return (perf_counter() - start_time) * 1000
```

它把耗时计算集中起来。

调用方式：

```python
start_time = perf_counter()
...
elapsed_ms = _elapsed_ms_since(start_time)
```

这样不用每个地方重复写：

```python
(perf_counter() - start_time) * 1000
```

### 6. log_ticket_agent_run_started

新增：

```python
log_ticket_agent_run_started(...)
```

它只记录：

```text
operation
thread_id
actor_id
message_length
```

它不记录：

```text
user_message
```

这体现了本节的安全设计。

### 7. log_ticket_agent_run_finished

新增：

```python
log_ticket_agent_run_finished(...)
```

它会调用：

```python
build_ticket_agent_observation_metadata(...)
```

然后记录执行摘要。

它不会把完整 State 直接打进日志。

这是非常重要的边界。

### 8. log_ticket_agent_run_failed

新增：

```python
log_ticket_agent_run_failed(...)
```

它记录：

```text
operation
thread_id
elapsed_ms
code
error_type
```

对 `AppException`：

```text
code = exc.code
```

对未知异常：

```text
code = TICKET_AGENT_UNEXPECTED_ERROR
```

它不写：

```text
str(exc)
```

### 9. run_ticket_agent 接入日志

现在 `run_ticket_agent` 的结构是：

```text
start_time = perf_counter()
log started
try graph.invoke
except log failed and raise
log finished
return result
```

它仍然是普通入口。

失败时不返回 fallback。

### 10. run_ticket_agent_safely 接入日志

现在 `run_ticket_agent_safely` 的结构是：

```text
start_time = perf_counter()
log started
try graph.invoke
except AppException -> log failed -> fallback -> log finished -> return
except Exception -> log failed -> fallback -> log finished -> return
success -> log finished -> return
```

这就是 API 层未来更适合使用的入口。

### 11. run_ticket_agent_in_thread 接入日志

这个函数现在记录：

```text
operation=invoke_thread
thread_id
actor_id
message_length
```

如果图返回 `__interrupt__`，结束日志里的：

```text
interrupted=True
```

会帮助你知道：

```text
这不是失败，是流程暂停。
```

### 12. resume_ticket_confirmation_interrupt 接入日志

这个函数现在记录：

```text
operation=resume_interrupt
thread_id
actor_id
elapsed_ms
ticket_creation_status
```

如果恢复后创建成功：

```text
ticket_creation_status=created
```

如果恢复后被拒绝：

```text
ticket_creation_status=-
last_node=request_ticket_confirmation
```

如果恢复失败：

```text
ticket_agent_failed operation=resume_interrupt ...
```

### 13. create_ticket_node 接入日志

创建工单节点现在记录四类事件：

```text
blocked
started
finished
failed
```

这基本覆盖了写操作排查所需信息。

尤其是：

```text
started
finished
failed
```

能帮助判断：

```text
到底有没有尝试调用创建服务？
有没有成功返回？
失败是 AppException 还是未知异常？
```

## 四、本节测试讲解

### 1. 测 observation metadata

测试：

```python
test_build_ticket_agent_observation_metadata_summarizes_state
```

验证：

```text
operation
trace_id
thread_id
intent
node_count
last_node
interrupted
fallback_used
agent_error_code
ticket_creation_status
elapsed_ms
```

这个测试保证 State 摘要逻辑稳定。

### 2. 测 build_ticket_agent_input 保存 trace_id

测试：

```python
test_build_ticket_agent_input_returns_initial_state
```

现在会先设置：

```python
set_trace_id("trace-agent-input-001")
```

再断言：

```python
"agent_trace_id": "trace-agent-input-001"
```

这说明 Agent 输入可以拿到当前请求 trace_id。

### 3. 测 safe 入口日志和 trace_id

测试：

```python
test_run_ticket_agent_safely_returns_normal_result_when_graph_succeeds
```

验证：

```text
started 日志存在
finished 日志存在
last_node=build_direct_answer
日志 record.trace_id 等于 trace-agent-safe-001
日志不包含原始用户消息“你好”
```

这说明日志既能追踪，又没有记录原始输入。

### 4. 测 safe 入口未知异常日志

测试：

```python
test_run_ticket_agent_safely_converts_unexpected_error_to_fallback_state
```

模拟：

```text
RuntimeError("internal stack trace")
```

验证：

```text
final_answer 不包含 internal stack trace
caplog.text 也不包含 internal stack trace
日志里只有 error_type=RuntimeError
```

这说明用户回答和业务日志都没有直接暴露未知异常原文。

### 5. 测创建工单成功日志

测试：

```python
test_create_ticket_node_calls_creator_after_confirmation
```

验证：

```text
ticket_agent_create_ticket_started
ticket_agent_create_ticket_finished
不包含原始投诉描述
```

这是副作用节点的关键日志测试。

### 6. 测创建工单未知异常日志

测试：

```python
test_create_ticket_node_returns_safe_fallback_when_creator_crashes
```

模拟：

```text
RuntimeError("database password leaked in stack")
```

验证：

```text
ticket_agent_create_ticket_failed code=TICKET_CREATION_UNEXPECTED_ERROR
error_type=RuntimeError
日志不包含 database password
```

这条测试非常重要。

它证明我们没有把敏感异常消息写进业务日志。

## 五、本节完成后的排查方式

### 场景 1：用户说“我问了你好，助手正常回答”

你可以看到：

```text
ticket_agent_started operation=invoke_safe ... message_length=2
ticket_agent_finished operation=invoke_safe ... intent=smalltalk last_node=build_direct_answer fallback_used=False
```

说明：

```text
走了 safe 入口
识别为 smalltalk
没有 fallback
正常结束
```

### 场景 2：用户发起投诉，系统要求确认

你可能看到：

```text
ticket_agent_started operation=invoke_thread thread_id=ticket-thread-001 ...
ticket_agent_finished operation=invoke_thread ... interrupted=True fallback_used=False
```

说明：

```text
图不是失败，而是 interrupt 暂停等待确认。
```

### 场景 3：用户确认后创建成功

你可能看到：

```text
ticket_agent_started operation=resume_interrupt thread_id=ticket-thread-001 ...
ticket_agent_create_ticket_started category=complaint priority=high related_order_id=1001 ...
ticket_agent_create_ticket_finished status=created ticket_id=T1001 ...
ticket_agent_finished operation=resume_interrupt ... last_node=create_ticket ticket_creation_status=created
```

说明：

```text
resume 成功
创建节点执行
Java 工单创建成功
最终状态 created
```

### 场景 4：用户确认后创建失败

你可能看到：

```text
ticket_agent_create_ticket_failed code=TOOL_UPSTREAM_ERROR error_type=AppException
ticket_agent_finished operation=resume_interrupt ... fallback_used=True agent_error_code=TOOL_UPSTREAM_ERROR ticket_creation_status=failed
```

说明：

```text
恢复成功
创建节点执行
Java 或工具层失败
Agent 返回 fallback State
```

### 场景 5：图执行未知异常

你可能看到：

```text
ticket_agent_failed operation=invoke_safe code=TICKET_AGENT_UNEXPECTED_ERROR error_type=RuntimeError
ticket_agent_finished operation=invoke_safe ... fallback_used=True agent_error_code=TICKET_AGENT_UNEXPECTED_ERROR
```

说明：

```text
safe 入口兜住了未知异常
用户不会看到内部异常
开发者可以按 trace_id 继续排查
```

## 六、你要真正记住的核心句子

1. 可观测性是把猜测变成证据。
2. logging 记录运行事实，trace_id 串联同一次请求，node_history 记录 Agent 节点路径。
3. trace_id、thread_id、node_history 不能互相替代。
4. Agent 比普通接口更需要可观测性，因为它有多节点、条件边、工具调用、中断和恢复。
5. 日志不是越多越好，关键是记录能解释系统行为的事实。
6. 不要把原始用户输入、完整 prompt、API key、敏感身份信息写进业务日志。
7. 未知异常不要直接把 `str(exc)` 写进用户回答，也不要随便写进业务日志。
8. `message_length` 比原始 `user_message` 更安全。
9. `operation` 能区分普通调用、安全调用、线程调用和 interrupt 恢复。
10. `interrupted=True` 表示流程暂停，不等于失败。
11. `fallback_used=True` 表示本次使用了兜底路径。
12. 创建工单是关键写操作，必须记录 started、finished、failed。
13. 日志也应该写测试。
14. 本地 logging 和 LangSmith tracing 是互补关系。
15. 先设计好可观测字段，再接平台，学习会更扎实。

## 七、本节练习

### 练习 1：解释概念

请解释什么是可观测性。

参考答案：

可观测性是指系统运行后，开发者能不能通过日志、trace、指标、状态等外部信息判断系统内部发生了什么。对 Agent 来说，可观测性要能帮助我们知道执行了哪些节点、是否中断、是否兜底、哪个错误码、耗时多少，以及这次日志属于哪一个 trace_id。

### 练习 2：区分三个 ID 和路径

请说明 `trace_id`、`thread_id`、`node_history` 的区别。

参考答案：

`trace_id` 用来串联一次请求相关的日志。`thread_id` 用来让 LangGraph checkpoint 找回同一条会话线程。`node_history` 用来记录 Agent 本轮执行走过哪些节点。它们解决的问题不同，不能互相替代。

### 练习 3：判断日志是否安全

下面哪种日志更安全？

```text
A. ticket_agent_started user_message=我要投诉订单 1001，物流一直不动
B. ticket_agent_started message_length=18
```

参考答案：

B 更安全。A 直接记录了用户原始输入，可能包含隐私和业务敏感信息。B 只记录长度，能帮助判断输入是否为空或异常长，但不会暴露原文。

### 练习 4：解释 operation

为什么日志里要记录 `operation=invoke_safe` 或 `operation=resume_interrupt`？

参考答案：

因为同一个 Agent 图可能通过不同入口执行。`invoke_safe` 表示安全兜底入口，`resume_interrupt` 表示恢复第 22 节的人工确认中断。记录 operation 后，排查时能知道这条日志属于普通调用、线程调用，还是 interrupt 恢复调用。

### 练习 5：解释 interrupted

`interrupted=True` 是不是表示失败？

参考答案：

不是。`interrupted=True` 表示 LangGraph 本次执行返回了 `__interrupt__`，流程暂停等待外部输入。它是 human-in-the-loop 的正常状态，不等于失败。失败通常要看 `fallback_used`、`agent_error_code`、`ticket_creation_status` 等字段。

### 练习 6：解释为什么不打完整 State

为什么不能直接把完整 Agent State 打进日志？

参考答案：

因为 State 里可能包含原始用户输入、工单描述、待确认消息、RAG 引用内容、创建结果等敏感或过长内容。直接打完整 State 会增加隐私风险、日志噪声和存储成本。本节使用 observation metadata 摘要关键字段，是更安全、更可控的做法。

### 练习 7：解释 caplog

`caplog` 在本节测试中起什么作用？

参考答案：

`caplog` 用来捕获测试期间产生的日志。我们可以用它断言 Agent 是否写了 started、finished、failed 日志，日志里是否带 trace_id，以及日志里是否没有原始用户输入或未知异常原文。

### 练习 8：解释 LangSmith 和本地 logging

LangSmith tracing 和本地 logging 有什么区别？

参考答案：

本地 logging 是项目自己写出的运行记录，适合和现有 FastAPI 日志、trace_id、测试体系结合。LangSmith tracing 是专门面向 LLM/Agent 的可观测平台，能可视化 trace、run、节点执行、模型调用和性能表现。二者互补，本节先学本地 logging，后续可以把这些字段接入 LangSmith metadata。

## 八、本节自测题

### 自测 1

为什么 Agent 的日志不能只写“开始”和“结束”？

参考答案：

因为 Agent 有多节点、条件边、工具调用、interrupt 和 fallback。只写开始和结束，无法判断走了哪个节点、是否中断、是否创建工单、哪个错误码、是否使用兜底。Agent 日志必须包含能解释流程行为的关键字段。

### 自测 2

为什么本节把 trace_id 写入 `agent_trace_id`，但又说 trace_id 不是业务状态？

参考答案：

`agent_trace_id` 是为了排查和关联日志，属于技术上下文，不决定业务流程走向。它放进 State 是为了让结果和测试能关联当前请求，但不能用于判断是否创建工单、是否进入 RAG、是否中断等业务决策。

### 自测 3

如果用户确认后没有创建工单，你应该优先看哪些日志字段？

参考答案：

优先看 `operation=resume_interrupt`、`thread_id`、`last_node`、`ticket_creation_status`、`fallback_used`、`agent_error_code`。还要看是否出现 `ticket_agent_create_ticket_started` 和 `ticket_agent_create_ticket_failed`。这些字段能判断是否恢复了正确线程、是否走到创建节点、创建是否失败。

### 自测 4

为什么未知异常日志里只记录 `error_type=RuntimeError`，不记录异常原文？

参考答案：

因为未知异常原文可能包含内部实现、路径、密钥、数据库信息或其他敏感内容。记录 `error_type` 和错误码已经足够表达错误分类。原始异常是否记录到更高权限日志或监控系统，要看生产环境的脱敏和权限策略。

### 自测 5

`fallback_used=True` 和 `interrupted=True` 有什么区别？

参考答案：

`fallback_used=True` 表示本次走了兜底路径，通常和错误或失败有关。`interrupted=True` 表示本次 LangGraph 执行暂停等待外部输入，是 human-in-the-loop 的正常机制。一个表示兜底，一个表示中断等待。

### 自测 6

为什么创建工单节点要单独写 started、finished、failed 日志？

参考答案：

因为创建工单是关键写操作。单独记录 started 可以证明系统尝试创建，finished 可以证明创建成功并拿到 ticket_id，failed 可以说明创建失败的错误码和异常类型。写操作必须比普通判断节点更容易追踪。

### 自测 7

为什么本节测试要断言日志不包含原始用户输入？

参考答案：

因为“不记录敏感信息”不是口头约定，而是应该被测试保护的行为。测试能防止以后有人把 `user_message` 直接拼进日志，造成隐私和安全风险。

### 自测 8

本节距离生产级可观测性还缺什么？

参考答案：

还缺结构化 JSON 日志、统一日志平台、LangSmith 或 OpenTelemetry tracing、指标统计、慢节点分析、日志采样、敏感信息脱敏、告警、跨服务 trace 串联、成本统计和生产级权限控制。本节只是本地可观测性的基础。

## 九、本节常见误区

### 误区 1：有日志就等于有可观测性

不对。

日志只是可观测性的一部分。

如果日志里没有 trace_id、节点、错误码、耗时、状态字段，排查时仍然很难用。

### 误区 2：日志越多越好

不对。

日志太多会增加存储成本、搜索难度和敏感信息风险。

关键是记录有解释力的字段。

### 误区 3：trace_id 和 thread_id 是一个东西

不对。

trace_id 串联一次请求日志。

thread_id 找回 LangGraph checkpoint 线程。

一次 thread_id 可能跨多次请求，每次请求有不同 trace_id。

### 误区 4：node_history 可以替代日志

不对。

node_history 只记录节点路径。

它不记录耗时、不记录开始结束时间、不记录错误类型、不记录外部服务调用细节。

### 误区 5：线上出错时直接看用户反馈就够了

不对。

用户反馈通常只描述现象。

开发者需要 trace_id、日志、State 摘要、错误码和节点路径来定位原因。

## 十、本节小结

本节给智能工单 Agent 补上了本地可观测性基础。

新增能力：

```text
Agent State 保存 agent_trace_id
Agent 运行开始日志
Agent 运行结束日志
Agent 运行失败日志
observation metadata 摘要
创建工单节点 started / finished / failed 日志
日志 trace_id 测试
日志安全测试
```

现在你应该能讲清楚：

```text
logging、trace_id、thread_id、node_history 分别解决什么问题
为什么 Agent 需要比普通接口更细的可观测性
为什么不能记录原始用户输入
如何用 caplog 测试日志
本地 logging 和 LangSmith tracing 的关系
```

下一节进入：

```text
阶段 5 第 25 节：LangGraph 测试：fake LLM / fake RAG / fake Java client
```

也就是把我们当前 Agent 的 fake 依赖、节点测试、图测试、失败路径测试整理成一套更系统的测试方法。

## 十一、参考资料

1. LangGraph 官方文档：LangSmith Observability  
   https://docs.langchain.com/oss/python/langgraph/observability

2. LangGraph 官方文档：Streaming  
   https://docs.langchain.com/oss/python/langgraph/streaming

3. LangSmith 官方文档：Trace LangGraph applications  
   https://docs.langchain.com/langsmith/trace-with-langgraph

4. LangSmith 官方文档：Observability concepts  
   https://docs.langchain.com/langsmith/observability-concepts

5. Python 官方文档：logging  
   https://docs.python.org/3/library/logging.html

6. Python 官方文档：time.perf_counter  
   https://docs.python.org/3/library/time.html#time.perf_counter

7. 本仓库：阶段 1 第 12 节 logging 日志  
   `notes/fastapi-stage1-12-logging.md`

8. 本仓库：阶段 1 第 13 节 trace_id 请求追踪  
   `notes/fastapi-stage1-13-trace-id.md`

9. 本仓库：阶段 5 第 23 节节点错误处理、fallback 和流程兜底  
   `notes/langgraph-stage5-23-node-error-fallback.md`
