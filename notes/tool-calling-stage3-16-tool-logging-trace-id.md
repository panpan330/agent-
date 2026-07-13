# 阶段 3 第 16 节：工具调用日志和 trace_id 串联

> 本节结论：工具调用链路只“能跑”还不够，必须“能排查”。`trace_id` 用来把一次请求中的 HTTP 入口、模型调用、工具执行、确认计划、Java API 调用和最终结果串起来；日志用来记录关键节点、结果、错误码和耗时，但不能泄露完整用户隐私和敏感业务内容。

## 生成笔记前的教学复核

本节笔记必须满足这些要求：

```text
1. 先讲清楚为什么第 15 节之后必须补日志和 trace_id，而不是继续堆业务功能。
2. 讲清楚日志、trace_id、调用链路、可观测性、排查节点这些基础概念。
3. 用真实排查场景解释：没有日志时会卡在哪里，有日志后怎么定位。
4. 在进入代码前，系统讲透“工具调用链路应该记录哪些节点、哪些字段、哪些不能记录”。
5. 代码讲解只讲关键改动：出站 trace header、Java client 日志、工具执行日志、工单执行日志。
6. 测试只讲关键验证：trace_id 能传给 Java client，关键工具节点有日志，不打印完整描述。
7. 不提前学习 ELK、OpenTelemetry、分布式链路追踪平台、日志采集架构。
8. 结尾必须让学习者能不看代码说清：本节真正学会的是“让工具链路可排查”。
```

## 本节一句话定位

第 16 节不是新增一个更聪明的 AI 能力，而是把第 13、14、15 节做出来的工具调用链路变成“出问题时能查得清楚”的工程链路。

## 本节解决的真实问题

第 15 节结束后，我们已经能做：

```text
用户描述问题
-> 模型提取工单字段
-> 创建确认计划
-> 用户确认
-> Python 调 Java mock 创建工单
-> 返回 ticket_id
```

但是如果用户说“我点了确认，为什么没有创建工单？”，没有足够日志时你会很难判断：

```text
是请求没有到 Python 服务？
是模型提取失败？
是确认计划没创建？
是确认计划过期？
是 actor_id 不一致？
是执行接口没调？
是 Java mock 服务没启动？
是 Java 返回 500？
是 Java 返回格式变了？
是重复点击被幂等复用了？
```

这些问题不是靠“代码看起来对”解决的，而是靠运行时日志和同一个 `trace_id` 把每一段串起来。

本节新增能力：

```text
你以后看到一个 trace_id，就能沿着日志追踪这次请求经历了哪些关键步骤。
```

## 和上一节的区别

第 15 节学的是：

```text
怎么把已确认计划真正执行成一张工单。
```

第 16 节学的是：

```text
怎么知道这条执行链路到底走到了哪里、哪里失败、失败时应该查什么。
```

简单说：

```text
第 15 节：把事情做成
第 16 节：把事情查清
```

## 基础知识铺垫

### 1. 什么是日志

人话解释：日志就是程序运行时留下的“过程记录”。

比如你去医院挂号，系统可能记录：

```text
用户提交挂号请求
校验身份证成功
扣费成功
生成挂号单成功
```

程序日志也是类似作用。它记录系统关键节点发生了什么。

工程术语：日志是 application runtime events，也就是应用运行时事件。

日志常见用途：

- 排查错误；
- 分析慢请求；
- 审计关键操作；
- 统计调用量；
- 判断上下游服务是否稳定；
- 复盘线上事故。

当前项目里，日志由 Python 标准库 `logging` 实现，格式在 `app/core/logging.py` 中配置。

### 2. 什么是 trace_id

人话解释：`trace_id` 就是一次请求的“追踪编号”。

如果一个用户请求经历了很多步骤：

```text
FastAPI 收到请求
-> 调模型
-> 执行工具
-> 调 Java mock
-> 返回结果
```

这些步骤都会产生日志。没有 `trace_id` 时，你只能看到一堆混在一起的日志，很难判断哪些属于同一次请求。

有 `trace_id` 后，每条相关日志都带同一个编号：

```text
trace_id=abc123 request_started
trace_id=abc123 structured_ticket_extraction_succeeded
trace_id=abc123 ticket_plan_created
trace_id=abc123 java_ticket_create_finished
trace_id=abc123 request_finished
```

工程术语：`trace_id` 是 correlation id，也就是关联 ID。它用于关联同一次业务链路中的多个日志事件。

### 3. 日志和 trace_id 的关系

日志回答：

```text
发生了什么？
```

trace_id 回答：

```text
这些事情是不是同一次请求里的？
```

两者组合才有排查价值。

没有日志：

```text
不知道发生了什么。
```

有日志但没有 trace_id：

```text
知道发生了很多事，但不知道哪些属于同一个用户请求。
```

有日志也有 trace_id：

```text
能沿着同一条请求链路从入口查到出口。
```

### 4. 什么是调用链路

调用链路就是一次请求经过的步骤。

以创建工单为例：

```text
POST /tickets/plans
-> 模型提取字段
-> 后端生成 CreateTicketArgs
-> 创建 confirmation

POST /tools/confirmations/{id}/confirm
-> 标记 confirmed

POST /tickets/confirmations/{id}/execute
-> 读取确认计划
-> 校验参数
-> 调 Java mock
-> 返回 ticket_id
```

每个箭头都是可能失败的点。日志应该覆盖这些关键节点。

### 5. 什么是可观测性

人话解释：系统不是黑盒，出问题时你能从外部记录看出里面发生了什么。

工程术语：observability，可观测性。它通常包括：

```text
logs：日志
metrics：指标
traces：链路追踪
```

本节只学习最基础的 logs + trace_id。

暂时不学：

- Prometheus metrics；
- OpenTelemetry；
- Jaeger；
- Grafana；
- ELK；
- 云厂商日志平台。

先把基本日志打对，比一开始引入复杂平台更重要。

### 6. 日志级别

常见日志级别：

| 级别 | 含义 | 当前项目例子 |
| --- | --- | --- |
| DEBUG | 很细的调试信息 | 暂时少用 |
| INFO | 正常关键节点 | 请求开始、工具执行成功 |
| WARNING | 业务可预期失败 | 上游超时、确认过期、参数校验失败 |
| ERROR | 严重错误 | 未处理异常 |

本节主要用：

```text
INFO：记录成功路径关键节点
WARNING：记录可预期失败
```

为什么不全用 ERROR？

因为很多失败是业务预期内的，比如订单不存在、确认过期、Java 返回 400。它们需要排查，但不是程序崩溃。

### 7. 什么是结构化日志

普通日志：

```text
创建工单成功了。
```

结构化倾向的日志：

```text
ticket_created_from_confirmation confirmation_id=abc actor_id=demo_user_001 ticket_id=T1001 elapsed_ms=12.3
```

后者更容易搜索：

```text
confirmation_id=abc
ticket_id=T1001
code=TOOL_TIMEOUT
```

当前项目还不是 JSON 日志，但已经使用 `key=value` 风格，为以后接日志平台做准备。

### 8. 日志里应该记录什么

工具调用链路里建议记录：

- `trace_id`：自动带；
- 请求方法和路径；
- 工具名；
- `tool_call_id`；
- `confirmation_id`；
- `actor_id`；
- 订单号；
- 工单号；
- HTTP 状态码；
- 项目错误码；
- 耗时；
- 上游服务是否成功。

这些字段能帮助排查。

### 9. 日志里不应该记录什么

不要随便记录：

- API key；
- 用户完整问题；
- 工单完整描述；
- 身份证、手机号、地址；
- 支付信息；
- 模型完整 prompt；
- 模型完整回答；
- 密码、token、cookie。

为什么？

日志通常会被更多人看到，也可能被长期保存。日志泄露就是数据泄露。

本节创建工单时只记录：

```text
category
priority
related_order_id
ticket_id
confirmation_id
```

不记录完整 `description`。

### 10. 什么是出站 trace 传播

用户请求进入 Python AI 服务时有一个 `X-Trace-Id`：

```text
X-Trace-Id: trace-001
```

如果 Python 再调用 Java mock 服务，也应该把这个 header 传过去：

```text
Python AI Service -> Java Mock Service
Header: X-Trace-Id: trace-001
```

这叫 trace propagation，追踪 ID 传播。

意义是：未来 Java 服务也打日志时，可以用同一个 `trace_id` 查到两边日志。

## 本节主题系统讲解

### 1. 为什么工具调用比普通接口更需要日志

普通接口可能只有：

```text
请求 -> 查数据库 -> 返回
```

工具调用链路更复杂：

```text
用户自然语言
-> 模型判断
-> 工具参数
-> 后端校验
-> 权限判断
-> 幂等判断
-> Java API
-> 工具结果
-> 模型总结
-> 用户回答
```

这里面既有模型不确定性，也有业务系统调用，还有后端安全边界。任何一段失败，用户看到的可能只是“请求失败”。

所以我们不能只记录入口和出口，还要记录关键中间节点。

### 2. 工具调用链路应该怎么分层记录

本节按四层记录：

```text
HTTP 入口层：request_started / request_finished
模型层：模型调用成功、失败、token、耗时
工具层：工具开始、成功、失败、工具名、参数摘要
跨服务层：Java API 请求开始、结束、状态码、耗时
```

当前项目之前已经有：

```text
HTTP 入口层日志
模型层日志
```

本节补的是：

```text
工具层日志
跨服务层 trace_id 传播和日志
```

### 3. 第 13、14、15 节分别该看哪些日志

第 13 节 `/tool-chat`：

```text
模型是否请求 query_order？
工具参数是否校验通过？
query_order 是否执行？
Java 订单服务是否返回 200？
第二轮模型总结是否成功？
```

第 14 节确认机制：

```text
是否创建 confirmation？
是否同一个 actor 确认？
是否过期？
确认是否成功？
```

第 15 节创建工单：

```text
模型字段提取是否成功？
CreateTicketArgs 是否构建成功？
确认计划是否存在并 confirmed？
执行前权限是否仍通过？
Java 工单服务是否返回 201？
是否返回 ticket_id？
```

第 16 节要把这些节点变得更容易查。

### 4. 一条真实排查路径应该长什么样

假设用户反馈：

```text
我确认了，但工单没创建。
```

你应该先拿到这次请求的 `trace_id`，然后查日志：

```text
trace_id=trace-001 ticket_execution_requested confirmation_id=...
trace_id=trace-001 ticket_confirmation_loaded confirmation_id=... tool_name=create_ticket
trace_id=trace-001 ticket_tool_execution_started confirmation_id=... category=complaint
trace_id=trace-001 java_ticket_create_started method=POST path=/tickets
trace_id=trace-001 java_ticket_create_finished status_code=201
trace_id=trace-001 java_ticket_create_validated ticket_id=T1001
trace_id=trace-001 ticket_created_from_confirmation ticket_id=T1001
```

这说明创建成功了。如果用户没看到，可能是前端展示问题。

如果日志是：

```text
trace_id=trace-001 ticket_execution_failed code=TOOL_CONFIRMATION_REQUIRED
```

说明根本没确认。

如果是：

```text
trace_id=trace-001 java_ticket_create_failed code=TOOL_TIMEOUT
```

说明卡在 Java mock 调用。

这就是日志的价值：把猜测变成证据。

### 5. 为什么不记录完整用户消息

很多初学者会想：

```text
我把所有参数都打出来，排查不是更方便吗？
```

短期看方便，长期看危险。

用户消息可能包含：

- 手机号；
- 地址；
- 订单隐私；
- 投诉细节；
- 账号信息；
- 甚至误贴的密钥。

日志通常会：

- 被平台收集；
- 被多人查看；
- 保留较长时间；
- 出现在错误报告里。

所以真实项目里日志要做取舍：

```text
能定位问题，但不泄露敏感内容。
```

本节只记录字段摘要，不记录完整描述。

### 6. 为什么 trace_id 不等于用户 ID

`trace_id` 标识一次请求或一条调用链。

`user_id` / `actor_id` 标识谁发起操作。

它们不能混用：

```text
trace_id：这次请求是哪一次？
actor_id：这次操作是谁做的？
confirmation_id：确认的是哪份计划？
ticket_id：创建出了哪张工单？
```

一次用户操作可能有多个请求，所以可能有多个 `trace_id`。一个 `actor_id` 会出现在很多 trace 里。

### 7. 为什么 trace_id 要继续传给 Java

如果 Python AI 服务调用 Java 服务时不传 `X-Trace-Id`，将来两边日志会断开：

```text
Python 日志：trace_id=abc 调用了 Java
Java 日志：不知道这是 abc 这次调用
```

传过去后：

```text
Python 日志：trace_id=abc java_ticket_create_started
Java 日志：trace_id=abc POST /tickets
```

这样可以跨服务排查。

当前 Java mock 还没完整实现自己的 trace 日志，但 Python 出站请求已经带上 header，为后续真实 Java 服务接入打基础。

### 8. 本节为什么不引入 OpenTelemetry

OpenTelemetry 是更专业的链路追踪标准，真实生产常用。

但现在直接学它会有几个问题：

- 概念更多：span、trace、exporter、collector；
- 部署更复杂；
- 会分散 Tool Calling 主线；
- 你还没先建立手写日志和 trace_id 的基础心智模型。

所以本节先学最基础的手工 trace_id 和关键日志。等你能看懂这条链，再学 OpenTelemetry 会更稳。

## 最小心智模型

记住这 5 行：

```text
trace_id 负责把同一次请求串起来
日志负责记录关键节点发生了什么
工具链路要记录开始、成功、失败和耗时
跨服务调用要把 X-Trace-Id 传下去
日志要能排查问题，但不能泄露敏感内容
```

## 当前项目如何落地

本节落地点：

```text
app/core/trace.py
  增加 build_trace_headers()

app/services/java_order_client.py
  查询订单时带 X-Trace-Id，并记录 Java 请求开始/结束/失败

app/services/java_ticket_client.py
  创建工单时带 X-Trace-Id，并记录 Java 请求开始/结束/校验成功/失败

app/services/tool_calling_chat_service.py
  记录 query_order 工具执行开始/成功/失败

app/services/ticket_workflow_service.py
  记录工单计划字段构建、确认计划加载、执行开始、执行成功/失败
```

注意：本节没有改变接口返回，也没有改变业务规则。

## 关键代码讲解

### 1. `build_trace_headers()`

它的职责是把当前请求上下文里的 trace_id 变成 HTTP 出站 header：

```text
当前有真实 trace_id -> {"X-Trace-Id": trace_id}
当前没有请求上下文 -> {}
```

为什么没有上下文时不返回 `X-Trace-Id: -`？

因为 `-` 只是本地日志里的占位符，不是真实追踪 ID。把它传给 Java 没有意义，还可能污染日志。

### 2. `JavaOrderClient`

订单查询现在会：

```text
记录 java_order_request_started
GET /orders/{order_id} 时携带 X-Trace-Id
记录 java_order_request_finished
超时或连接失败时记录 java_order_request_failed
```

这让 `/tool-chat` 里执行 `query_order` 时，可以看出是否真的调到了 Java mock。

### 3. `JavaTicketClient`

创建工单现在会：

```text
记录 java_ticket_create_started
POST /tickets 时携带 X-Trace-Id 和 Idempotency-Key
记录 java_ticket_create_finished
校验返回成功后记录 java_ticket_create_validated
失败时记录 java_ticket_create_failed
```

它不记录完整工单描述，只记录分类、优先级、关联订单和最终工单号。

### 4. `ToolCallingChatService`

只读工具执行现在会记录：

```text
tool_execution_started
tool_execution_succeeded
tool_execution_failed
```

关键字段：

```text
tool_name
tool_call_id
order_id
source
code
status_code
elapsed_ms
```

这能帮助你判断：模型是否请求了工具，后端是否执行了工具，工具失败还是模型总结失败。

### 5. `TicketWorkflowService`

工单执行现在会记录：

```text
ticket_plan_arguments_built
ticket_confirmation_loaded
ticket_tool_execution_started
ticket_created_from_confirmation
ticket_execution_failed
```

这些日志对应第 15 节的关键链路。以后看到错误码，就能知道失败在哪个阶段。

## 常见误区和排查

| 现象 | 可能原因 | 怎么查 |
| --- | --- | --- |
| 响应里没有 `X-Trace-Id` | middleware 没注册 | 查 `app/main.py` 是否注册 trace middleware |
| Python 日志有 trace_id，Java 没有 | 没传 header 或 Java 没记录 | 查 Java client 是否带 `X-Trace-Id` |
| 工具失败但不知道哪个工具 | 没记录 tool_name | 查 `tool_execution_*` 日志 |
| 确认后没创建工单 | 可能没执行、未确认、过期或 Java 失败 | 查 `ticket_execution_*` 和 `java_ticket_*` |
| 日志里出现完整用户问题 | 过度记录敏感字段 | 改成记录长度、分类、ID、状态 |
| 只有失败日志，没有成功节点 | 成功路径不可观测 | 补关键 INFO 日志 |
| 日志太多看不懂 | 节点太碎或字段无意义 | 只保留排查需要的关键节点 |

## 手动验证方式

启动服务后，带一个自定义 trace_id：

```http
POST /tickets/plans
X-Trace-Id: lesson16-trace-001
```

然后观察日志里是否出现：

```text
trace_id=lesson16-trace-001 request_started
trace_id=lesson16-trace-001 ticket_plan_requested
trace_id=lesson16-trace-001 structured_ticket_extraction_succeeded
trace_id=lesson16-trace-001 ticket_plan_arguments_built
trace_id=lesson16-trace-001 ticket_plan_created
trace_id=lesson16-trace-001 request_finished
```

执行创建工单时继续带同一个或新的 trace_id，观察：

```text
ticket_execution_requested
ticket_confirmation_loaded
ticket_tool_execution_started
java_ticket_create_started
java_ticket_create_finished
java_ticket_create_validated
ticket_created_from_confirmation
```

## 重要测试说明

本节测试重点不是“每条日志逐字相等”，而是验证关键风险：

1. `build_trace_headers()` 没有真实 trace_id 时不会传 `-`；
2. `JavaOrderClient` 会把当前 `trace_id` 传给 Java mock 请求；
3. `JavaTicketClient` 会把当前 `trace_id` 传给 Java mock 请求；
4. `/tool-chat` 的只读工具执行会留下开始和成功日志；
5. 工单执行日志包含关键节点和 `ticket_id`，但不打印完整用户描述。

这些测试对应本节目标：链路可关联、节点可排查、日志不过度泄露。

## 练习

### 练习 1：判断该不该记录

下面字段哪些适合记录到日志？

```text
trace_id
actor_id
ticket_id
用户完整投诉内容
API key
confirmation_id
Java HTTP status_code
elapsed_ms
```

#### 参考答案

适合记录：`trace_id`、`actor_id`、`ticket_id`、`confirmation_id`、Java HTTP `status_code`、`elapsed_ms`。

不适合直接记录：用户完整投诉内容、API key。前者可能包含隐私，后者是敏感凭据。

### 练习 2：根据日志判断失败位置

看到日志：

```text
ticket_confirmation_loaded confirmation_id=abc tool_name=create_ticket
ticket_tool_execution_started confirmation_id=abc category=complaint
java_ticket_create_failed code=TOOL_TIMEOUT
ticket_execution_failed code=TOOL_TIMEOUT
```

失败在哪里？

#### 参考答案

确认计划已经读取成功，执行也开始了，失败发生在调用 Java 工单服务阶段，具体是超时。

### 练习 3：为什么不能只看 HTTP 状态码

如果接口返回 502，为什么还要看项目错误码和日志？

#### 参考答案

502 只说明上游或外部调用出问题，但不能区分是 Java 超时、Java 返回格式错误、模型调用失败还是接口契约不一致。项目错误码如 `TOOL_TIMEOUT`、`TOOL_RESULT_VALIDATION_FAILED` 能定位具体失败类型，日志能定位失败节点。

### 练习 4：trace_id 和 confirmation_id 有什么区别

#### 参考答案

`trace_id` 用来关联一次请求或调用链日志；`confirmation_id` 用来定位一份用户确认计划。一次确认计划可能经历多次 HTTP 请求，所以它们不能混用。

### 练习 5：为什么日志要记录耗时

#### 参考答案

耗时能帮助判断慢在哪里。比如模型调用慢、Java API 慢、还是整个请求慢。如果只记录成功失败，不记录耗时，就很难做性能排查。

## 自测题

1. 本节真正解决的工程问题是什么？

   参考答案：让工具调用链路可观察、可关联、可排查。不是新增业务功能，而是能定位模型、工具、确认计划、Java API 哪一段出了问题。

2. `trace_id` 的核心作用是什么？

   参考答案：把同一次请求或调用链中的多条日志关联起来。

3. 为什么 Java client 要传 `X-Trace-Id`？

   参考答案：为了把 Python AI 服务和 Java 业务服务的日志串成同一条链路，方便跨服务排查。

4. 为什么日志不能记录完整工单描述？

   参考答案：工单描述可能包含用户隐私或敏感业务信息，日志会长期保存并被多人查看，直接记录有泄露风险。

5. 工具执行失败时至少应该记录哪些字段？

   参考答案：`tool_name`、关联 ID（如 `tool_call_id` 或 `confirmation_id`）、错误码、HTTP 状态码、耗时，必要时记录订单号或工单号等非敏感业务 ID。

6. 为什么有日志还需要错误码？

   参考答案：日志用于排查过程，错误码用于稳定分类失败类型。错误码比自然语言消息更适合测试、统计和自动化处理。

7. 本节为什么不直接学 OpenTelemetry？

   参考答案：当前阶段先建立日志和 trace_id 的基础心智模型。OpenTelemetry 更强但概念和部署复杂，后续在有基础后再学更合适。

## 本节你真正学会了什么

以前你已经能让 AI 服务调用工具、确认写操作、调用 Java mock 创建工单。

现在你进一步学会：

```text
如何让这条链路出问题时能查清楚。
```

你应该能不看代码讲出：

```text
一次工具调用不能只看最终成功失败。
后端要在入口、模型、工具、确认、Java API、最终结果这些关键节点留下日志。
这些日志必须带同一个 trace_id，跨服务时还要把 X-Trace-Id 传给下游。
日志要记录能排查问题的 ID、状态、错误码和耗时，但不能记录 API key、完整用户隐私和大段 prompt。
```

如果让你自己再做一遍，先抓住这条主线：

```text
确定关键节点
-> 给每个节点设计安全字段
-> 让同一次请求共享 trace_id
-> 出站请求传递 X-Trace-Id
-> 用测试验证 trace 能传、日志有关键节点、敏感内容不被打印
```

## 下一节衔接

第 17 节建议学习“工具调用测试：fake Java API / fake tool”。

前面我们已经写了不少 fake client 和 mock transport，但还没有系统讲测试策略。下一节会把这些整理成一套方法：什么时候 fake 模型、什么时候 fake Java API、什么时候测 service、什么时候测 router，以及为什么自动化测试不能真实调用模型。
