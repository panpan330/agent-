# 阶段 3 第 15 节：创建工单流程：提取字段、确认、调用 Java API

> 本节结论：模型可以帮助我们从用户自然语言里整理工单字段，但真正创建工单必须由后端完成。后端要把“模型提取结果”转换成自己的业务命令，要求用户确认固定计划，再调用 Java 业务服务，并且用幂等保护避免重复创建。

## 生成笔记前的教学复核

本节必须满足以下学习要求：

```text
1. 讲清楚“工单创建”为什么是写操作，不是普通问答。
2. 讲清楚自然语言、模型提取结果、后端业务命令、Java API 请求之间的区别。
3. 讲清楚第 14 节确认计划在本节如何被真正消费。
4. 讲清楚为什么执行前还要再次校验工具权限、操作者、确认状态和参数契约。
5. 讲清楚 Python AI 服务为什么通过 HTTP 调 Java mock 服务，而不是自己写业务数据。
6. 讲清楚幂等键为什么使用 confirmation_id，以及它能防止什么问题。
7. 对新增 schema、service、client、router、Java mock 代码按调用链详细解释。
8. 测试部分只讲关键风险：未确认不能执行、重复执行不重复创建、Java 返回不可信要校验。
9. 不提前讲 LangChain、LangGraph、RAG、真实登录系统、数据库持久化和多级审批。
10. 结尾要有练习、参考答案、自测题和答案，保证以后可以复盘。
```

## 本节目标

第 14 节只做了“用户确认机制”：

```text
创建确认计划
-> 用户确认
-> 状态变成 confirmed
-> 不执行真实工具
```

本节向前走一步：用已经确认的计划真正创建工单。

完整链路是：

```text
用户说：订单 A1001 一直没发货，请帮我处理
-> Python AI 服务让模型提取工单字段
-> 后端把模型字段转换成 CreateTicketArgs
-> 后端创建 create_ticket 的确认计划
-> 用户确认这个计划
-> 后端读取已确认计划
-> 后端再次校验参数、权限和幂等
-> Python 通过 HTTP 调用 Java mock 服务 POST /tickets
-> Java mock 创建工单并返回 ticket_id
-> Python 校验 Java 返回值
-> 返回给用户
```

学完本节，你要能解释：

- 为什么“模型建议创建工单”不等于“后端可以直接创建工单”；
- 为什么后端要把模型输出转换成自己的业务命令；
- 为什么确认计划只保存参数还不够，执行时仍要再次校验；
- 为什么写操作必须考虑幂等；
- 为什么 Python AI 层不直接操作数据库；
- `schema -> service -> client -> router -> mock business service` 每层分别负责什么。

## 本节不学什么

为了边界清晰，本节不学习：

- 不学习真实 Spring Boot，只用 FastAPI 模拟 Java 业务服务；
- 不学习 JWT、登录、RBAC，`actor_id` 仍是教学占位；
- 不学习数据库、Redis、消息队列；
- 不学习 LangChain Tool 封装；
- 不学习 LangGraph 多节点流程；
- 不学习 RAG；
- 不学习多级审批、撤销确认、工单状态流转。

这些后续会逐步补。

## 基础知识铺垫

### 1. 什么是工单

人话解释：工单就是把用户的问题变成一条可以被客服、运营、仓库或技术人员跟进的记录。

例如用户说：

```text
订单 A1001 已付款一周仍未发货，请帮我处理。
```

系统里可能创建一条工单：

```text
工单号：T1001
提交人：demo_user_001
标题：订单 A1001 一直未发货
分类：complaint
优先级：high
关联订单：A1001
描述：订单 A1001 已付款一周仍未发货，请帮我处理。
```

工程术语：工单是业务系统里的一个 domain record，也就是业务记录。创建工单是 write operation，因为它会改变系统状态。

没有工单系统会怎么样：

- 用户问题只能停留在聊天记录里；
- 后续人员无法分配、追踪、统计；
- 没有状态、责任人、处理结果；
- 无法审计用户什么时候提交过问题。

当前项目里，工单字段主要由 `CreateTicketArgs` 和 Java mock 的 `CreateTicketRequest` 表达。

### 2. 什么是写操作

读操作只查看已有信息，例如：

```text
查询订单 A1001
查询退款状态
查询用户权限
```

写操作会改变系统，例如：

```text
创建工单
申请退款
修改收货地址
关闭订单
发送短信
```

写操作的风险更高，因为它有副作用。副作用就是系统外部或内部真的发生了变化。

本节的副作用是：

```text
Java mock 服务内存里新增一条 ticket 记录
```

真实项目中可能是：

```text
数据库新增工单
消息队列发出通知
客服系统收到待处理任务
用户收到短信或站内信
```

所以写操作必须有：

- 参数校验；
- 权限校验；
- 用户确认；
- 幂等；
- 日志和审计；
- 错误兜底。

### 3. 自然语言、模型提取结果和业务命令不是一回事

用户自然语言：

```text
订单 A1001 已付款一周仍未发货，请帮我处理。
```

模型提取结果 `TicketExtraction`：

```json
{
  "intent": "complaint",
  "order_id": "A1001",
  "summary": "订单 A1001 一直未发货",
  "urgency": "high",
  "need_human_review": true
}
```

后端业务命令 `CreateTicketArgs`：

```json
{
  "requester_id": "demo_user_001",
  "title": "订单 A1001 一直未发货",
  "description": "订单 A1001 已付款一周仍未发货，请帮我处理。",
  "category": "complaint",
  "priority": "high",
  "related_order_id": "A1001"
}
```

三者的区别：

| 层次 | 来源 | 作用 | 是否可信 |
| --- | --- | --- | --- |
| 自然语言 | 用户输入 | 描述问题 | 需要清洗和理解 |
| 模型提取结果 | LLM | 帮助结构化 | 不完全可信 |
| 后端业务命令 | Python 后端 | 真正调用业务系统的契约 | 必须由后端校验后生成 |

关键点：模型不能直接决定最终业务参数。模型只提供候选字段，后端负责转换、校验和约束。

### 4. 什么是后端拥有的业务命令

业务命令可以理解为“后端准备执行的一次业务动作”。

本节的业务命令是 `CreateTicketArgs`。它表示：

```text
请为 requester_id 创建一张工单，字段如下。
```

为什么不直接把 `TicketExtraction` 发给 Java？

因为 `TicketExtraction` 是模型视角：

```text
intent
summary
urgency
need_human_review
```

而 Java 业务服务需要业务视角：

```text
requester_id
title
description
category
priority
related_order_id
```

中间必须有一层转换。当前项目由 `build_create_ticket_args()` 负责。

### 5. 什么是确认计划的消费

第 14 节创建的确认计划像一张待审批单：

```text
confirmation_id = abc...
actor_id = demo_user_001
tool_name = create_ticket
arguments = {...}
status = confirmed
expires_at = ...
```

本节执行时不是让客户端重新提交参数，而是：

```text
客户端只提交 confirmation_id 和 actor_id
后端从 store 里读取原计划
后端用原计划参数执行
```

这样可以防止：

```text
用户确认的是 A1001
执行时客户端偷偷换成 A1002
```

这叫参数绑定。用户确认的是后端保存的那一份固定参数，不是确认了一个任意写操作权限。

### 6. 什么是幂等

人话解释：同一个写请求因为网络重试发了两次，结果应该像只发了一次。

本节为什么需要幂等？

用户点击执行后，网络可能超时。前端不知道后端到底有没有创建成功，于是重试一次。如果没有幂等保护，就可能创建两张一模一样的工单。

本节使用：

```text
confirmation_id 作为幂等键
```

原因是：

- 一个确认计划对应一次固定的创建工单动作；
- 同一个 `confirmation_id` 重试，应该拿到同一个结果；
- 不同确认计划，即使参数相似，也应该独立处理。

AI 服务内部用 `run_idempotent_tool()` 防重复执行。Java mock 服务也接收 `Idempotency-Key`，在业务服务侧再次防重复创建。

### 7. 为什么 Python AI 服务要调用 Java 业务服务

当前项目的长期目标是：

```text
Python AI 服务：负责模型调用、工具编排、结构化输出、RAG、Agent 流程
Java 业务服务：负责订单、工单、权限、用户、财务等核心业务
```

所以 Python AI 服务不应该直接写业务数据库。

真实公司里常见原因：

- Java 业务服务已经有完整业务规则；
- 数据库表结构不应该暴露给 AI 服务；
- 权限、审计、事务通常在业务服务里；
- AI 服务直接写库容易绕过风控和校验；
- 业务系统以后变更时，只需要保持 API 契约稳定。

本节用 FastAPI 写 `java-mock-service`，只是为了先模拟未来 Java 服务。

### 8. 什么是 HTTP adapter

`JavaTicketClient` 是 HTTP adapter。

人话解释：它把 Python 内部对象变成 HTTP 请求，把 Java HTTP 响应变回 Python 内部对象。

它做的事情：

```text
CreateTicketArgs
-> POST /tickets JSON
-> Idempotency-Key header
-> HTTP status code 判断
-> response.json()
-> CreatedTicket.model_validate(...)
```

为什么单独写 client，而不是在 service 里直接 `httpx.post()`？

因为这样职责清楚：

- workflow service 关心业务流程；
- JavaTicketClient 关心 HTTP 细节；
- 测试时可以用 `httpx.MockTransport` 模拟 Java 服务；
- 后续替换真实 Java 地址时影响小。

## 本节新增和修改的代码讲解

### 1. `projects/ai-service/app/schemas/ticket.py`

这个文件定义 Python AI 服务里的工单相关数据契约。

#### `TicketCategory`

```python
class TicketCategory(StrEnum):
    REFUND = "refund"
    ORDER_QUERY = "order_query"
    LOGISTICS = "logistics"
    COMPLAINT = "complaint"
```

它表示工单分类。用枚举的好处是避免随便传字符串。

例如不允许：

```text
"logistic"
"shipping_problem"
"complain"
```

只能用后端明确允许的值。

#### `TicketPriority`

```python
class TicketPriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
```

它表示优先级。模型提取出来的是 `TicketUrgency`，后端会把它映射为这里的 `TicketPriority`。

#### `CreateTicketArgs`

这是本节最重要的 schema。

它不是用户直接输入，也不是模型原始输出，而是后端准备交给业务服务的命令。

字段含义：

| 字段 | 含义 |
| --- | --- |
| `requester_id` | 谁提交工单，当前来自 `actor_id` |
| `title` | 工单标题，来自模型摘要 |
| `description` | 工单描述，保留用户原始问题 |
| `category` | 工单分类，由模型意图映射 |
| `priority` | 工单优先级，由模型紧急程度映射 |
| `related_order_id` | 关联订单号，可为空 |

为什么 `model_config = ConfigDict(extra="forbid")`？

因为创建工单是写操作，不应该默默接受未知字段。客户端或模型多传：

```json
{"is_admin": true}
```

应该直接拒绝，而不是忽略或误用。

#### `CreatedTicket`

这是 Java 业务服务返回后，Python AI 服务认可的结果契约。

注意：即使 Java 服务是自己系统，也不能完全不校验返回值。跨服务边界上的数据都应该当成不可信输入重新校验。

如果 Java 返回：

```json
{"id": "T1001"}
```

但 Python 期待：

```json
{"ticket_id": "T1001"}
```

就说明接口契约不一致，应该报错而不是继续假装成功。

#### `TicketPlanRequest`

它是创建确认计划的入口请求：

```python
actor_id: str
message: str
```

这里的 `message` 是用户自然语言问题，不是最终工单参数。

#### `TicketPlanResponse`

它返回两部分：

```text
extraction：模型提取结果
confirmation：后端创建的确认计划
```

这样用户可以看到模型理解了什么，也能看到最终将要确认的业务参数。

#### `ExecuteTicketConfirmationRequest`

它只有：

```python
actor_id: str
```

为什么没有 `arguments`？

因为执行时必须使用确认计划里保存的参数。如果执行接口允许重新传参数，就破坏了第 14 节的参数绑定。

#### `TicketExecutionResponse`

它返回：

```text
confirmation_id
ticket
```

这样用户和日志都能把“哪次确认”与“创建出的哪张工单”关联起来。

#### `get_create_ticket_args_json_schema()`

这个函数把 `CreateTicketArgs` 转成 JSON Schema，交给工具注册表。

意义是：模型和后端都知道 `create_ticket` 工具需要哪些参数。但注意，本节真正执行时仍以后端保存和 Pydantic 校验为准。

### 2. `projects/ai-service/app/services/ticket_workflow_service.py`

这个文件负责“创建工单工作流”。

它不是 HTTP 层，也不是 Java HTTP client，而是把多步业务流程串起来。

#### `TicketExtractor`

这是一个 `Protocol`，意思是：只要某个对象有这个方法，就可以当作工单字段提取器。

```python
def extract_ticket(self, user_message: str) -> TicketExtraction
```

为什么用 Protocol？

因为测试时可以传 fake extractor，不需要真实调用模型。

#### `TicketCreator`

它也是 `Protocol`：

```python
def create_ticket(arguments: CreateTicketArgs, *, idempotency_key: str) -> CreatedTicket
```

真实运行时用 `JavaTicketClient`。测试时用 fake creator。

这叫依赖抽象。好处是业务流程测试不依赖真实网络和真实模型。

#### `_INTENT_TO_CATEGORY`

它把模型意图映射成业务分类：

```text
TicketIntent.COMPLAINT -> TicketCategory.COMPLAINT
TicketIntent.LOGISTICS -> TicketCategory.LOGISTICS
```

为什么需要映射？

因为模型输出结构和业务服务契约不是同一个东西。中间转换层让后端保留控制权。

如果模型输出 `unknown`，本节不会猜：

```python
TICKET_INTENT_UNSUPPORTED
```

这很重要。写操作宁可拒绝，也不要乱猜。

#### `_URGENCY_TO_PRIORITY`

它把模型紧急程度映射成工单优先级。

这也是业务规则。以后可以改成：

```text
退款投诉 high
普通咨询 normal
物流问题根据订单状态判断
```

当前先做最小但完整的映射。

#### `build_create_ticket_args()`

这是从模型提取结果到业务命令的关键函数。

输入：

```text
extraction：模型提取字段
actor_id：当前操作者
original_message：用户原始问题
```

输出：

```text
CreateTicketArgs
```

执行步骤：

```text
1. 根据 extraction.intent 找到业务 category
2. unknown intent 直接拒绝
3. requester_id 使用 actor_id
4. title 使用 extraction.summary
5. description 保留 original_message
6. priority 根据 extraction.urgency 映射
7. related_order_id 使用 extraction.order_id
8. 交给 Pydantic 再校验一次
```

为什么 description 使用原始问题，而不是模型 summary？

因为 summary 可能丢信息。工单描述应该尽量保留用户原话，方便人工处理和审计。

#### `TicketWorkflowService.plan_ticket()`

它负责创建待确认工单计划。

调用链：

```text
TicketPlanRequest
-> extractor.extract_ticket(request.message)
-> build_create_ticket_args(...)
-> ToolConfirmationService.request_confirmation(...)
-> TicketPlanResponse
```

这里不会调用 Java 服务。它只是准备一份固定计划，让用户确认。

关键点：

```python
tool_name="create_ticket"
arguments=arguments.model_dump(mode="json")
```

这表示确认计划绑定的是后端已经校验过的 `CreateTicketArgs`，不是模型原始 JSON。

#### `TicketWorkflowService.execute_confirmed_ticket()`

这是本节真正执行写操作的核心。

输入：

```text
confirmation_id
ExecuteTicketConfirmationRequest(actor_id)
```

内部流程：

```text
1. confirmation_service.require_confirmed(...)
2. 检查 record.tool_name 必须是 create_ticket
3. 用 CreateTicketArgs.model_validate(record.arguments) 再校验参数
4. authorize_tool_call("create_ticket", user_confirmed=True)
5. run_idempotent_tool(...)
6. ticket_creator.create_ticket(...)
7. 返回 TicketExecutionResponse
```

为什么已经 confirmed 还要 `authorize_tool_call()`？

因为确认和执行之间可能发生变化：

- 工具被禁用；
- 用户权限变化；
- 参数规则变化；
- 后端策略变化。

这就是 TOCTOU 问题：检查时和使用时不是同一时刻。执行前必须再检查。

为什么要重新 `CreateTicketArgs.model_validate(record.arguments)`？

因为确认记录可能来自内存、数据库、缓存或旧版本系统。执行前再校验可以防止坏数据进入 Java 服务。

为什么 `run_idempotent_tool()` 的 key 用 `confirmation_id`？

因为确认计划就是这次固定写操作的唯一业务凭据。相同确认重复执行，应返回同一结果，不应创建第二张工单。

### 3. `projects/ai-service/app/services/java_ticket_client.py`

这个文件负责 Python 调 Java mock 服务。

#### `JavaTicketClient.__init__()`

核心参数：

```text
base_url：Java mock 服务地址
timeout_seconds：超时时间
transport：测试时注入 MockTransport
```

`base_url.strip().rstrip("/")` 是为了避免地址结尾多一个 `/` 导致拼路径混乱。

#### `from_settings()`

它从配置里读取：

```text
JAVA_MOCK_SERVICE_BASE_URL
JAVA_MOCK_SERVICE_TIMEOUT_SECONDS
```

这样环境不同只改配置，不改代码。

#### `create_ticket()`

输入：

```text
arguments: CreateTicketArgs
idempotency_key: str
```

执行：

```text
POST /tickets
json = arguments.model_dump(mode="json")
headers = {"Idempotency-Key": idempotency_key}
```

错误处理：

| 情况 | 后端错误 |
| --- | --- |
| 超时 | `TOOL_TIMEOUT` |
| 网络连接失败 | `TOOL_UPSTREAM_ERROR` |
| Java 5xx | `TOOL_UPSTREAM_ERROR` |
| Java 非 201 | `TICKET_UPSTREAM_REJECTED` |
| Java 返回非 JSON | `TOOL_RESULT_VALIDATION_FAILED` |
| Java JSON 不符合 `CreatedTicket` | `TOOL_RESULT_VALIDATION_FAILED` |

为什么 400 也映射成 502？

因为 Python AI 服务已经校验过参数。如果 Java 仍拒绝，说明两个服务之间的接口契约不一致。对调用方来说，这是上游业务服务异常，而不是让用户自己修请求。

### 4. `projects/ai-service/app/routers/tickets.py`

这个文件暴露 HTTP API。

#### `POST /tickets/plans`

作用：根据用户自然语言创建一份待确认计划。

它调用：

```text
workflow_service.plan_ticket(request)
```

返回：

```text
模型提取结果 + 确认计划
```

#### `POST /tickets/confirmations/{confirmation_id}/execute`

作用：执行已确认的创建工单计划。

注意它不负责确认。确认仍然走第 14 节接口：

```text
POST /tools/confirmations/{confirmation_id}/confirm
```

本节把流程拆成三步：

```text
1. POST /tickets/plans
2. POST /tools/confirmations/{id}/confirm
3. POST /tickets/confirmations/{id}/execute
```

为什么不合成一步？

因为真实系统里创建计划、用户确认和执行通常是三个独立动作。拆开后更容易审计、重试、排查和扩展。

### 5. `projects/ai-service/app/main.py`

本节把 `tickets.router` 注册到 FastAPI 应用：

```python
app.include_router(tickets.router)
```

如果忘了注册，文件写好了也无法通过 HTTP 访问。

### 6. `projects/ai-service/app/tools/tool_registry.py`

本节让 `create_ticket` 的工具定义带上真实参数 schema：

```python
argument_schema=get_create_ticket_args_json_schema()
```

这让后端工具注册表知道：

```text
create_ticket 是 write 工具
需要用户确认
参数结构由 CreateTicketArgs 定义
```

同时保留：

```text
authorize_tool_call("create_ticket", user_confirmed=True)
```

执行前仍要走工具权限边界。

### 7. `projects/java-mock-service/app/schemas/ticket.py`

这是模拟 Java 业务服务里的工单请求和响应契约。

`CreateTicketRequest` 与 Python 的 `CreateTicketArgs` 基本对齐。真实项目中，Java 服务会有自己的 DTO。

`TicketResponse` 多了：

```text
ticket_id
created_at
```

这两个字段由业务服务生成，不应该由 AI 服务提供。

### 8. `projects/java-mock-service/app/services/ticket_service.py`

这个文件模拟 Java 业务服务创建工单。

核心内存结构：

```python
_TICKET_STORE
_TICKET_IDEMPOTENCY_STORE
_TICKET_LOCK
```

#### `_normalize_idempotency_key()`

它校验 `Idempotency-Key` 格式。

如果格式错误，返回：

```text
TICKET_IDEMPOTENCY_KEY_INVALID
```

#### `_build_arguments_fingerprint()`

它把请求参数转成稳定 JSON，再计算 SHA-256。

作用：判断同一个幂等键是否被拿去执行了不同参数。

#### `create_ticket()`

流程：

```text
1. 规范化幂等键
2. 计算参数指纹
3. 加锁
4. 如果幂等键已存在：
   - 参数相同：返回旧 ticket
   - 参数不同：409 冲突
5. 如果不存在：生成新 ticket_id
6. 写入内存 store
7. 保存幂等记录
8. 返回 ticket
```

为什么 Java mock 也做幂等？

因为真实生产环境里，调用链每一层都可能重试。只在 AI 服务做幂等不够，业务服务侧也应该保护自己的写操作。

### 9. `projects/java-mock-service/app/routers/tickets.py`

这个文件提供：

```text
POST /tickets
```

它接收：

```text
CreateTicketRequest
Idempotency-Key header
```

返回：

```text
TicketResponse
```

### 10. `projects/java-mock-service/app/main.py`

本节把 `tickets.router` 注册进 Java mock 应用。

这样 Python AI 服务才能调用：

```text
http://127.0.0.1:8001/tickets
```

## 完整调用链路

### 第一段：创建计划

```text
POST /tickets/plans
-> TicketPlanRequest 校验 actor_id/message
-> TicketWorkflowService.plan_ticket()
-> extractor.extract_ticket(message)
-> TicketExtraction
-> build_create_ticket_args()
-> CreateTicketArgs
-> ToolConfirmationService.request_confirmation()
-> ToolConfirmationStore.create()
-> pending ToolConfirmationResponse
-> TicketPlanResponse
```

本阶段没有创建工单。

### 第二段：用户确认

```text
POST /tools/confirmations/{confirmation_id}/confirm
-> ConfirmToolConfirmationRequest 校验 actor_id
-> ToolConfirmationService.confirm()
-> ToolConfirmationStore.confirm()
-> 检查 ID、actor、TTL
-> pending -> confirmed
```

本阶段仍然没有创建工单。

### 第三段：执行工单创建

```text
POST /tickets/confirmations/{confirmation_id}/execute
-> ExecuteTicketConfirmationRequest 校验 actor_id
-> TicketWorkflowService.execute_confirmed_ticket()
-> ToolConfirmationService.require_confirmed()
-> 检查 tool_name == create_ticket
-> CreateTicketArgs.model_validate(record.arguments)
-> authorize_tool_call("create_ticket", user_confirmed=True)
-> run_idempotent_tool(..., idempotency_key=confirmation_id)
-> JavaTicketClient.create_ticket()
-> POST Java mock /tickets
-> Java mock create_ticket()
-> TicketResponse
-> CreatedTicket.model_validate(...)
-> TicketExecutionResponse
```

## 手动验证方式

先启动 Java mock 服务：

```powershell
cd D:\wendang\java+python+ai\projects\java-mock-service
uv run uvicorn app.main:app --reload --port 8001
```

再启动 AI 服务：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run uvicorn app.main:app --reload --port 8000
```

第一步：创建工单计划。

```http
POST http://127.0.0.1:8000/tickets/plans
```

```json
{
  "actor_id": "demo_user_001",
  "message": "订单 A1001 已付款一周仍未发货，请帮我处理。"
}
```

第二步：复制响应里的 `confirmation_id`，确认计划。

```http
POST http://127.0.0.1:8000/tools/confirmations/{confirmation_id}/confirm
```

```json
{
  "actor_id": "demo_user_001"
}
```

第三步：执行创建工单。

```http
POST http://127.0.0.1:8000/tickets/confirmations/{confirmation_id}/execute
```

```json
{
  "actor_id": "demo_user_001"
}
```

预期返回：

```json
{
  "confirmation_id": "...",
  "ticket": {
    "ticket_id": "T1001",
    "requester_id": "demo_user_001",
    "title": "...",
    "description": "...",
    "category": "complaint",
    "priority": "high",
    "related_order_id": "A1001",
    "created_at": "..."
  }
}
```

注意：真实模型调用需要 `.env` 中的 LLM 配置可用。自动化测试不会真实调用模型，而是使用 fake extractor 和 fake creator。

## 重要测试说明

### 1. `test_ticket_workflow_service.py`

重点验证业务流程：

- 模型提取结果会被转换成固定确认计划；
- `unknown` intent 不会被猜测成某类工单；
- 未确认计划不能执行；
- 确认后可以执行；
- 同一个确认重复执行不会重复创建；
- 操作者不一致会拒绝；
- 确认记录里的参数坏了会被重新校验拦住。

这些测试保护的是业务安全边界。

### 2. `test_java_ticket_client.py`

重点验证 Python 调 Java 的 HTTP adapter：

- 发送的是 `POST /tickets`；
- 会带 `Idempotency-Key`；
- 会把响应校验成 `CreatedTicket`；
- Java 5xx、400、非 JSON 都不会被当成成功。

这些测试保护的是跨服务边界。

### 3. `projects/java-mock-service/tests/test_tickets_api.py`

重点验证业务服务侧：

- 能创建工单；
- 同一个幂等键重复请求返回同一张工单；
- 同一个幂等键换参数会 409。

这些测试保护的是写操作幂等。

## 常见错误和排查方法

| 现象 | 优先排查 | 说明 |
| --- | --- | --- |
| 执行返回 `TOOL_CONFIRMATION_REQUIRED` | 是否先调用了确认接口 | 创建计划不等于确认 |
| 返回 `TOOL_CONFIRMATION_FORBIDDEN` | `actor_id` 是否与创建计划的人一致 | A 创建的计划 B 不能执行 |
| 返回 `TOOL_CONFIRMATION_EXPIRED` | TTL 是否过期 | 过期后必须重新创建计划 |
| 返回 `TOOL_CONFIRMATION_TOOL_MISMATCH` | confirmation 是否属于 `create_ticket` | 不能拿别的工具确认单创建工单 |
| 返回 `TICKET_ARGUMENTS_VALIDATION_FAILED` | 确认记录里的参数是否符合 `CreateTicketArgs` | 执行前会重新校验 |
| 返回 `TOOL_TIMEOUT` | Java mock 服务是否卡住或网络超时 | HTTP 调用超时 |
| 返回 `TOOL_UPSTREAM_ERROR` | Java mock 是否启动、端口是否正确 | 上游服务不可用 |
| 返回 `TOOL_RESULT_VALIDATION_FAILED` | Java 返回 JSON 是否符合 `CreatedTicket` | 跨服务契约不一致 |
| 重复创建两张工单 | 幂等键是否稳定传递 | 应使用 `confirmation_id` |

## 真实项目中的注意点

1. `actor_id` 不能由客户端随便传，必须来自登录态、JWT、session 或网关认证。
2. 确认计划不能只存在内存，生产应放数据库或 Redis，并带 TTL、状态、审计字段。
3. 执行确认计划时最好有“已消费”状态，避免长时间重复执行。
4. Java 业务服务要自己做权限校验，不能完全相信 Python AI 服务。
5. 写操作必须记录 trace_id、actor_id、confirmation_id、ticket_id、参数指纹和耗时。
6. 工单参数里可能有隐私信息，日志不能直接打印完整 description。
7. 模型提取结果必须允许失败和拒绝，不要为了自动化强行猜字段。
8. 如果 Java API 契约变更，Python 的 `CreatedTicket` 校验会第一时间暴露问题。
9. 幂等不是锁住所有重复请求，而是让同一个业务意图重复请求返回一致结果。
10. 后续接 LangGraph 时，这一节会变成“工单 Agent”中的一个节点链路。

## 练习

### 练习 1：为什么执行接口不接收 `arguments`

如果执行接口设计成：

```json
{
  "actor_id": "demo_user_001",
  "arguments": {
    "related_order_id": "A1002"
  }
}
```

会有什么风险？

#### 参考答案

用户确认的可能是 A1001 的计划，但执行时客户端可以换成 A1002。这样确认机制失去意义。正确设计是执行接口只接收 `confirmation_id` 和可信操作者身份，参数从后端保存的确认计划读取。

### 练习 2：为什么 `TicketExtraction` 不能直接发给 Java

#### 参考答案

`TicketExtraction` 是模型提取结果，字段是模型理解视角；Java 业务服务需要的是明确业务命令，例如 `requester_id`、`title`、`category`、`priority`。中间必须由后端转换和校验，防止模型输出直接控制业务系统。

### 练习 3：为什么创建工单要幂等

#### 参考答案

网络超时、浏览器重试、前端重复点击都可能让同一个创建请求发多次。如果没有幂等，会创建重复工单。本节用 `confirmation_id` 作为幂等键，让同一个确认计划重复执行时返回同一张工单。

### 练习 4：为什么 Java mock 也要校验幂等键

#### 参考答案

幂等不能只依赖调用方。业务服务自己才是写入的最后防线。即使 Python AI 服务出 bug 或重试，Java 服务也应该保证同一个幂等键不会创建多个不同结果。

### 练习 5：如果模型提取 intent 为 `unknown`，为什么不创建工单

#### 参考答案

写操作不能靠猜。`unknown` 说明模型不能确定业务分类，此时应该让用户补充信息或转人工，而不是随便归到 complaint、logistics 等分类。错误分类会影响处理流程和责任归属。

## 自测题

1. 本节为什么要分成 `plans -> confirm -> execute` 三步？

   参考答案：三步分别对应生成固定计划、用户确认计划、执行已确认计划。拆开后可以参数绑定、审计、重试、过期控制和执行前再次授权。

2. `CreateTicketArgs` 和 `CreatedTicket` 分别代表什么？

   参考答案：`CreateTicketArgs` 是 Python 后端准备发给业务服务的创建命令；`CreatedTicket` 是业务服务创建成功后返回并经 Python 校验的结果。

3. `JavaTicketClient` 为什么要单独成类？

   参考答案：它隔离 HTTP 细节，让 workflow service 专注业务流程；测试时可以用 `MockTransport` 替代真实网络；以后替换真实 Java 服务地址更容易。

4. 为什么确认后执行前还要 `authorize_tool_call()`？

   参考答案：确认和执行不是同一时刻，工具开关、权限和策略可能变化。执行前重新授权可以防止旧确认绕过当前规则。

5. 为什么 `CreatedTicket.model_validate()` 很重要？

   参考答案：跨服务返回值不应该直接信任。校验可以发现 Java API 契约变化、字段缺失、类型错误，防止系统把错误结果当成功。

6. `confirmation_id` 在本节承担了哪两个作用？

   参考答案：一是定位已确认计划；二是作为创建工单写操作的幂等键。

7. 当前实现最大的不生产化限制是什么？

   参考答案：确认计划和 Java mock 工单都存内存，没有真实认证、数据库、审计和分布式一致性。服务重启会丢数据，不能直接上生产。

8. 如果重复执行同一个已确认计划，为什么不会重复创建工单？

   参考答案：AI 服务的 `run_idempotent_tool()` 使用同一个 `confirmation_id` 返回缓存结果，Java mock 服务也用 `Idempotency-Key` 保存并复用同一张工单。

## 本节总结

本节把 Tool Calling 从“只读查询”推进到“受控写操作”。核心不是让模型更自由，而是让后端更可控：

```text
模型负责提取候选字段
后端负责生成业务命令
用户负责确认固定计划
后端负责再次校验和执行
Java 业务服务负责真正写入
幂等机制负责防止重复副作用
```

你要记住一句话：AI 可以建议做什么，但业务系统必须由后端按规则执行什么。

## 下一节衔接

第 16 节建议学习“工具调用日志和 trace_id 串联”。

本节虽然能创建工单，但排查能力还不够。真实项目里必须能追踪：

```text
用户问题
-> 模型提取结果
-> confirmation_id
-> 执行请求
-> Java API 调用
-> ticket_id
-> 错误码和耗时
```

下一节会把这些关键节点串到日志和 trace_id 里，让工具调用链路真正可排查。
