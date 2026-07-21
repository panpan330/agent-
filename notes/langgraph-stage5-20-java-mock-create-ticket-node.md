# 阶段 5 第 20 节：调用 Java mock 创建工单节点

## 本节定位

第 19 节我们完成了：

```text
字段完整
-> 生成待确认工单
-> 请求用户确认
```

这一步非常关键，因为它把“信息已经够了”和“用户已经同意执行”分开了。

本节继续往后走：

```text
用户已经确认
-> Python Agent 调用 Java mock 工单服务
-> Java mock 创建工单
-> Python Agent 把创建结果写回 State
-> 返回工单号
```

本节是阶段 5 里第一次把 LangGraph Agent 接到“真正会产生业务结果”的写操作节点。

注意，本节仍然不做真正的多轮恢复。我们先用一个明确的 State 字段模拟“用户已经确认”：

```text
ticket_confirmation_approved = True
```

等后面学 checkpoint、thread_id、interrupt 时，再把“用户确认后继续执行”做成真正的可暂停、可恢复流程。

## 本节学习目标

学完本节，你应该能讲清楚：

1. 什么是写操作节点。
2. 为什么创建工单必须放在用户确认之后。
3. Python Agent 为什么要调用 Java 后端服务。
4. Java mock 服务在项目里扮演什么角色。
5. 什么是接口契约。
6. 为什么 Agent 字段不能直接当作 HTTP 请求发出去。
7. `TicketFields` 和 `CreateTicketArgs` 有什么区别。
8. 为什么要用 Pydantic 模型做参数校验。
9. 为什么创建工单需要幂等键。
10. `confirmation_id` 为什么可以作为本节的幂等键。
11. 为什么普通对话默认仍然停在确认节点。
12. 为什么测试里必须用 fake client，不能真实调用 Java 服务。
13. 为什么本节要把 `policy_gap` 同步进 Java mock 契约。

## 本节先不学什么

本节暂时不学：

1. 不实现真实多轮对话恢复。
2. 不接 LangGraph checkpoint。
3. 不接 `thread_id`。
4. 不使用 `interrupt()`。
5. 不做前端确认按钮。
6. 不做数据库持久化。
7. 不做复杂重试策略。
8. 不展开完整分布式事务。
9. 不做生产级鉴权。
10. 不把 Java mock 服务换成真正 Java Spring Boot。

本节只解决一个核心问题：

```text
在用户已经确认的前提下，Agent 如何把待确认工单变成一次受控的后端创建工单调用。
```

## 一、基础知识铺垫

### 1. 什么是跨服务调用

我们的项目不是只有一个 Python 文件。

它的整体方向是：

```text
Java 后端 + Python AI 服务 + RAG + Agent
```

所以迟早会出现这种情况：

```text
Python AI 服务负责理解用户问题
Java 后端服务负责执行业务动作
```

这时 Python 就要调用 Java。

在真实公司里，这种调用通常通过 HTTP API 完成。

例如：

```text
Python AI 服务
-> POST http://java-service/tickets
-> Java 工单服务
-> 创建工单
-> 返回 ticket_id
```

这就是跨服务调用。

跨服务调用不是“直接调一个函数”。

它涉及：

1. URL。
2. HTTP 方法。
3. 请求 JSON。
4. 请求头。
5. 超时时间。
6. 返回状态码。
7. 返回 JSON。
8. 错误处理。
9. 参数契约。
10. 响应契约。

所以跨服务调用一定要谨慎设计。

### 2. 什么是 Java mock 服务

我们现在项目里的 `java-mock-service` 不是严格意义上的 Java 程序，它是用 Python FastAPI 模拟出来的 Java 后端服务。

为什么这样做？

因为学习阶段最重要的是先理解系统边界：

```text
Python AI 服务
-> 调用一个“后端业务服务”
-> 后端业务服务返回业务结果
```

至于这个 mock 服务内部现在是不是 Java 写的，不影响你先学会：

1. AI 服务怎么调用后端。
2. 后端接口契约怎么设计。
3. 创建工单这种写操作怎么保护。
4. 测试里怎么替换外部服务。

后面你学 Java Spring Boot 时，可以把这个 mock 服务替换成真正 Java 服务。

现在它先充当：

```text
Java 业务服务的替身。
```

### 3. 什么是写操作

写操作就是会改变系统状态的操作。

例如：

```text
创建工单
取消订单
发起退款
修改地址
冻结账号
发送邮件
```

这些动作执行后，系统里会多一条数据，或者某个状态会发生改变。

与它相对的是读操作：

```text
查询订单
查询规则
读取知识库
查看物流
```

读操作一般不会改变业务数据。

本节的创建工单属于写操作。

写操作必须更谨慎，原因是：

1. 执行后可能不能随便撤销。
2. 可能影响用户权益。
3. 可能触发人工客服工作流。
4. 可能产生通知、记录、审核任务。
5. 可能被重复执行。

所以本节延续第 19 节的原则：

```text
没有用户确认，不创建工单。
```

### 4. 什么是接口契约

接口契约就是两个服务之间约定好的数据格式。

比如 Java mock 创建工单接口要求：

```text
requester_id
title
description
category
priority
related_order_id
```

这就是请求契约。

Java mock 创建成功后返回：

```text
ticket_id
requester_id
title
description
category
priority
related_order_id
created_at
```

这就是响应契约。

契约的意义是：

```text
Python 服务知道该发什么。
Java 服务知道会收到什么。
Python 服务知道该接收什么。
```

如果没有契约，就会变成：

```text
Python 随便发
Java 随便猜
出错以后很难排查
```

所以本节没有把字典随手传给 Java，而是继续使用：

```python
CreateTicketArgs
CreatedTicket
```

这两个 Pydantic 模型来表达契约。

### 5. Agent 内部字段和后端接口字段为什么不同

第 17 节提取出来的是 Agent 内部字段：

```text
TicketFields
```

它长这样：

```text
issue_type
order_id
description
user_request
urgency
need_human_review
```

Java mock 接口需要的是：

```text
CreateTicketArgs
```

它长这样：

```text
requester_id
title
description
category
priority
related_order_id
```

它们不一样。

原因是它们服务的对象不同。

`TicketFields` 服务 Agent 流程：

1. 判断缺什么字段。
2. 生成追问。
3. 生成确认信息。
4. 表达 Agent 对用户问题的理解。

`CreateTicketArgs` 服务后端业务接口：

1. 创建正式工单。
2. 满足 Java 服务的 API 契约。
3. 让后端能持久化和处理。

所以中间必须有一层转换：

```text
TicketFields
-> build_create_ticket_args_from_fields
-> CreateTicketArgs
```

这层转换非常重要。

它是 Agent 世界和业务系统世界之间的边界。

### 6. 为什么不能直接把大模型/Agent 的字段发给 Java

大模型和规则抽取出来的内容，本质上是“推断结果”。

它可能不完整，也可能不符合后端契约。

例如 Agent 字段里有：

```text
issue_type = complaint
urgency = high
order_id = 1001
```

但 Java 接口要的是：

```text
category = complaint
priority = high
related_order_id = 1001
```

字段名不同。

如果直接发过去，Java 可能报错：

```text
字段不存在
缺少必填字段
枚举值不匹配
```

更严重的是，如果随手兼容各种字段名，接口会越来越乱。

所以正确做法是：

```text
Agent 输出
-> 后端再次映射和校验
-> 只有合法参数才发给 Java
```

### 7. 什么是 Pydantic 校验

Pydantic 可以理解为：

```text
Python 里的数据契约和数据校验工具。
```

本项目的 `CreateTicketArgs` 会校验：

1. `requester_id` 不能为空。
2. `requester_id` 只能是字母、数字、下划线、短横线。
3. `title` 不能为空，最长 200。
4. `description` 不能为空，最长 1000。
5. `category` 必须是允许的枚举。
6. `priority` 必须是允许的枚举。
7. `related_order_id` 最长 64。
8. 不能出现额外字段。

这意味着：

```text
创建工单前，Python 侧先把参数校验一遍。
```

这样可以避免把明显错误的数据发给 Java。

### 8. 什么是幂等

幂等是后端开发里非常重要的概念。

简单理解：

```text
同一个请求重复执行多次，结果应该和执行一次一样。
```

创建工单为什么要幂等？

因为网络请求可能失败、超时、重试。

例如：

```text
Python 发起创建工单
Java 已经创建成功
但是网络断了，Python 没收到响应
Python 以为失败，又重试一次
```

如果没有幂等，就会创建两张工单。

这很糟糕。

所以创建工单时要带：

```text
Idempotency-Key
```

同一个幂等键加同一份参数，Java mock 会返回同一张工单。

同一个幂等键加不同参数，Java mock 会拒绝。

这能防止重复创建。

### 9. 为什么本节用 confirmation_id 做幂等键

第 19 节已经有：

```text
confirmation_id
```

它代表：

```text
用户确认的是哪一份工单草稿。
```

本节创建工单时，可以用它作为幂等键：

```text
idempotency_key = pending_ticket_confirmation.confirmation_id
```

这很合理。

因为：

1. 同一份待确认草稿对应同一个确认 ID。
2. 用户确认同一份草稿时，不应该重复创建多张工单。
3. 字段变化后，确认 ID 会变化。
4. 幂等键和确认内容绑定，逻辑清楚。

### 10. 什么是 actor_id

创建工单时，后端必须知道：

```text
是谁请求创建这张工单。
```

这个人或系统身份就是：

```text
actor_id
```

在真实系统里，`actor_id` 应该来自登录态、JWT、Session、网关鉴权或内部服务身份。

本节为了学习，先使用：

```text
ticket_actor_id
```

如果 State 里没有，就使用学习用默认值：

```text
demo_user_001
```

你要记住：

```text
生产环境不能随便相信用户自己传 actor_id。
```

这部分后面做鉴权时再深入。

### 11. 为什么测试不能真实调用 Java 服务

自动化测试应该稳定、快速、可重复。

如果测试每次都真实调用 Java mock 服务，会有几个问题：

1. Java mock 服务没启动，测试就失败。
2. 端口被占用，测试就失败。
3. 网络慢，测试就变慢。
4. 数据状态没清理，测试会互相影响。
5. 测试失败时很难判断是代码问题还是服务问题。

所以本节测试使用：

```text
FakeTicketCreator
```

它模拟 Java 创建工单接口。

这样测试要验证的是：

```text
Agent 是否会在确认后调用创建器。
Agent 是否传了正确参数。
Agent 是否使用 confirmation_id 做幂等键。
Agent 是否把创建结果写回 State。
```

至于真实 HTTP 调用，前面 `JavaTicketClient` 已经有专门测试。

这就是测试分层。

## 二、本节主题系统讲解

### 1. 本节前后的流程变化

第 19 节之后，字段完整时流程是：

```text
extract_ticket_fields
-> request_ticket_confirmation
-> END
```

本节之后，流程变成：

```text
extract_ticket_fields
-> request_ticket_confirmation
-> 如果用户未确认：END
-> 如果用户已确认：create_ticket
-> END
```

也就是说，`request_ticket_confirmation` 后面不再是固定边，而是条件边。

条件是：

```text
ticket_confirmation_approved 是否为 True
```

### 2. 为什么普通 run_ticket_agent 仍然不会创建工单

普通调用：

```python
run_ticket_agent("我要投诉订单 1001，物流一直不动")
```

只会走到：

```text
request_ticket_confirmation
```

因为初始 State 没有：

```text
ticket_confirmation_approved = True
```

所以确认节点后的路由会返回：

```text
finish
```

这保证普通对话不会自动创建工单。

这就是本节的安全边界：

```text
必须显式确认，才能执行写操作。
```

### 3. 确认后的流程怎么模拟

本节还没有 checkpoint 和 interrupt，所以我们用 State 模拟用户已确认：

```python
{
    "user_message": "我要投诉订单 1001，物流一直不动",
    "ticket_actor_id": "demo_user_001",
    "ticket_confirmation_approved": True,
    "node_history": [],
}
```

图执行时会经历：

```text
normalize_user_input
-> classify_intent
-> decide_ticket_need
-> extract_ticket_fields
-> request_ticket_confirmation
-> create_ticket
```

这不是最终生产形态。

最终生产形态会是：

```text
第一次运行：停在确认
用户回复确认
第二次运行：用同一个 thread_id 恢复
继续执行 create_ticket
```

但在没学 checkpoint 之前，本节这样设计更容易理解。

### 4. 本节新增的确认后路由

新增类型：

```python
TicketConfirmationRoute = Literal["execute_create_ticket", "finish"]
```

意思是确认节点后只有两条路：

```text
execute_create_ticket
finish
```

新增路由表：

```python
TICKET_AGENT_CONFIRMATION_ROUTES = {
    "execute_create_ticket": "create_ticket",
    "finish": END,
}
```

新增路由函数：

```python
def route_by_ticket_confirmation(state):
    if state.get("ticket_confirmation_approved") is True:
        return "execute_create_ticket"
    return "finish"
```

这段逻辑非常关键。

它表达了：

```text
只有明确 True 才执行创建。
其他所有情况都结束。
```

注意，默认不是创建。

### 5. 为什么创建工单节点要和确认节点拆开

你可能会问：

```text
既然确认之后就创建，为什么不把创建逻辑放进 request_ticket_confirmation_node？
```

因为职责不同。

确认节点负责：

```text
生成待确认内容。
```

创建节点负责：

```text
执行后端写操作。
```

拆开的好处：

1. 未确认时可以只停在确认节点。
2. 确认节点可以未来升级为 `interrupt()`。
3. 创建节点可以单独测试。
4. 创建失败可以单独处理。
5. 日志、trace、重试、幂等都可以围绕创建节点展开。
6. 图结构更清楚。

这就是 LangGraph 的价值：

```text
把复杂业务流程拆成清晰节点和边。
```

### 6. 本节新增的创建参数转换

新增函数：

```python
build_create_ticket_args_from_fields(fields, actor_id=...)
```

它做的是：

```text
TicketFields
-> CreateTicketArgs
```

映射关系是：

| Agent 字段 | Java 创建参数 |
| --- | --- |
| `issue_type` | `category` |
| `urgency` | `priority` |
| `order_id` | `related_order_id` |
| `description` | `description` |
| `user_request` | 参与生成 `title` |
| `actor_id` | `requester_id` |

这一步很重要。

因为 Agent 内部字段不应该直接穿透到后端业务接口。

### 7. 为什么本节同步增加 policy_gap 类别

第 17 节开始，我们让 RAG 无资料场景进入工单流程：

```text
RAG no_context
-> issue_type = policy_gap
```

但原来的创建工单接口只有：

```text
refund
order_query
logistics
complaint
```

这就出现了契约不一致：

```text
Agent 能产生 policy_gap
Java 创建接口却不认识 policy_gap
```

本节修正了这个问题，把 `policy_gap` 加进：

```text
ai-service 的 TicketCategory
java-mock-service 的 TicketCategory
```

这说明一个真实工程经验：

```text
当 Agent 流程新增业务类型时，下游业务服务契约也可能需要同步演进。
```

否则流程会在创建工单时失败。

### 8. create_ticket_node 做了什么

创建节点逻辑可以拆成几步：

```text
1. 检查是否已经用户确认
2. 读取待确认字段
3. 读取 actor_id
4. 生成幂等键
5. 转换成 CreateTicketArgs
6. 调用 TicketCreator.create_ticket
7. 把创建结果写回 State
8. 把工单号放进 final_answer
```

成功时写入：

```text
ticket_creation_args
ticket_creation_status = created
created_ticket
final_answer
node_history
```

失败时写入：

```text
ticket_creation_status = failed
ticket_creation_error_code
ticket_creation_error_message
final_answer
node_history
```

未确认时写入：

```text
ticket_creation_status = blocked
ticket_creation_error_code = TICKET_CONFIRMATION_REQUIRED
```

### 9. 为什么创建结果也要写回 State

Java mock 返回：

```text
ticket_id
created_at
category
priority
...
```

这些信息不能只写进 `final_answer`。

因为后续可能还要：

1. 在前端展示工单卡片。
2. 写日志。
3. 给用户发送通知。
4. 进入后续节点。
5. 做测试断言。
6. 保存到对话历史。

所以本节写入：

```text
created_ticket
```

而 `final_answer` 只是给用户看的总结。

### 10. 为什么 build_ticket_agent_graph 支持注入 ticket_creator

新增：

```python
def build_ticket_agent_graph(ticket_creator: TicketCreator | None = None):
```

这让测试可以传入：

```text
FakeTicketCreator
```

生产默认使用：

```text
JavaTicketClient.from_settings(...)
```

这个设计叫依赖注入。

它的好处是：

```text
生产用真实依赖，测试用 fake 依赖。
```

这样测试既不会真实调用 Java 服务，也能验证完整 LangGraph 路径。

## 三、本节代码改动讲解

### 1. 工单类别契约增加 policy_gap

两个地方都增加：

```python
POLICY_GAP = "policy_gap"
```

分别是：

```text
ai-service/app/schemas/ticket.py
java-mock-service/app/schemas/ticket.py
```

这是为了让 RAG 无资料转人工场景可以创建正式工单。

### 2. 新增 TicketCreator 协议

新增：

```python
class TicketCreator(Protocol):
    def create_ticket(
        self,
        arguments: CreateTicketArgs,
        *,
        idempotency_key: str,
    ) -> CreatedTicket:
        ...
```

它表示：

```text
只要一个对象有 create_ticket 方法，就可以被 Agent 创建节点使用。
```

真实环境里是：

```text
JavaTicketClient
```

测试里是：

```text
FakeTicketCreator
```

### 3. 新增创建状态字段

State 新增：

```python
ticket_actor_id
ticket_creation_args
ticket_creation_status
ticket_creation_error_code
ticket_creation_error_message
created_ticket
```

这些字段让创建节点的结果变得可观察。

不只是返回一句：

```text
工单已创建
```

而是能在 State 里看到：

```text
用什么参数创建
创建是否成功
失败原因是什么
创建出的工单是什么
```

### 4. 新增确认后条件边

第 19 节的固定边：

```text
request_ticket_confirmation -> END
```

本节改成条件边：

```text
request_ticket_confirmation
-> route_by_ticket_confirmation
   -> execute_create_ticket -> create_ticket
   -> finish -> END
```

这就是本节图结构的核心。

### 5. 新增 build_create_ticket_args_from_fields

这个函数是本节非常重要的边界函数。

它把：

```text
Agent 内部字段
```

变成：

```text
Java 服务创建工单参数
```

如果 `issue_type` 是 `unknown`，它不会瞎猜类别，而是抛出业务异常。

这体现了一个原则：

```text
不能确定业务类型时，不要执行写操作。
```

### 6. 新增 create_ticket_node

这个节点是本节新增的执行节点。

它有三类结果：

```text
blocked：没有用户确认，阻止创建。
created：创建成功。
failed：创建失败。
```

本节只是做基础失败处理，更系统的错误处理会放到第 23 节。

### 7. create_ticket_node 为什么捕获 AppException

`JavaTicketClient` 可能抛出：

```text
TOOL_TIMEOUT
TOOL_UPSTREAM_ERROR
TICKET_UPSTREAM_REJECTED
TOOL_RESULT_VALIDATION_FAILED
```

这些都是业务可理解的错误。

本节让节点把它们写回 State：

```text
ticket_creation_status = failed
ticket_creation_error_code = ...
ticket_creation_error_message = ...
```

这样用户能收到友好的错误信息，测试也能断言失败状态。

更完整的 fallback、重试、日志会在后面继续学。

## 四、本节测试讲解

本节新增测试覆盖：

1. 确认后路由表。
2. 未确认默认结束。
3. 已确认进入创建节点。
4. `TicketFields` 到 `CreateTicketArgs` 的映射。
5. `policy_gap` 可以映射成 Java 工单类别。
6. 未确认时创建节点被阻止。
7. 已确认时创建节点调用 fake creator。
8. 创建节点使用 `confirmation_id` 作为幂等键。
9. 创建失败时写入失败状态。
10. 完整 LangGraph 路径能走到 `create_ticket`。
11. Java mock 服务接受 `policy_gap` 工单。

这里最重要的不是测试数量，而是测试分层：

```text
JavaTicketClient 测 HTTP 调用
java-mock-service 测服务契约
ticket_agent 测图流程和节点行为
```

每一层测自己的职责。

## 五、本节完成后的流程图

```text
START
-> normalize_user_input
-> classify_intent
   -> policy_question -> retrieve_policy -> decide_ticket_need
   -> order_query -> query_order -> END
   -> ticket_request -> decide_ticket_need
   -> smalltalk -> build_direct_answer -> END
   -> unsupported -> build_unsupported_answer -> END
   -> unclear -> ask_clarifying_question -> END

decide_ticket_need
   -> finish -> END
   -> create_ticket -> extract_ticket_fields

extract_ticket_fields
   -> ask_missing_fields -> ask_missing_ticket_fields -> END
   -> request_confirmation -> request_ticket_confirmation

request_ticket_confirmation
   -> finish -> END
   -> execute_create_ticket -> create_ticket -> END
```

本节新增的是最后一段：

```text
request_ticket_confirmation
-> create_ticket
```

但它必须满足：

```text
ticket_confirmation_approved = True
```

## 六、本节你要真正记住的核心句子

1. 创建工单是写操作，不是普通回答。
2. 写操作必须在用户确认之后执行。
3. `TicketFields` 是 Agent 内部字段，`CreateTicketArgs` 是后端接口契约。
4. Agent 字段不能直接发给 Java，必须经过映射和校验。
5. Pydantic 模型是服务间契约的一部分。
6. `confirmation_id` 可以作为创建工单的幂等键。
7. 没有明确 `ticket_confirmation_approved=True`，图不会进入创建节点。
8. 测试里用 fake client，不真实调用外部服务。
9. 下游接口契约必须跟 Agent 新增的业务类型保持一致。
10. 本节只是模拟确认后执行，真正多轮恢复要等 checkpoint 和 interrupt。

## 七、本节练习

### 练习 1：判断节点路径

用户输入：

```text
我要投诉订单 1001，物流一直不动
```

普通 `run_ticket_agent` 没有传入 `ticket_confirmation_approved=True`。

请写出最终节点路径。

### 练习 2：判断确认后路径

如果初始 State 包含：

```text
ticket_confirmation_approved = True
```

同样输入：

```text
我要投诉订单 1001，物流一直不动
```

请写出最终节点路径。

### 练习 3：字段映射

请把下面的 Agent 字段映射成 Java 创建工单字段：

```text
issue_type = logistics
order_id = A1001
description = 订单 A1001 一直未发货
user_request = 物流问题处理
urgency = high
actor_id = demo_user_001
```

### 练习 4：解释幂等

为什么创建工单接口需要 `Idempotency-Key`？

### 练习 5：解释 fake client

为什么本节测试不能直接启动 Java mock 服务，然后真的发 HTTP 请求？

## 八、练习参考答案

### 练习 1 参考答案

路径是：

```text
normalize_user_input
-> classify_intent
-> decide_ticket_need
-> extract_ticket_fields
-> request_ticket_confirmation
```

因为没有明确确认，所以确认节点后走 `finish`，不会进入 `create_ticket`。

### 练习 2 参考答案

路径是：

```text
normalize_user_input
-> classify_intent
-> decide_ticket_need
-> extract_ticket_fields
-> request_ticket_confirmation
-> create_ticket
```

因为 State 里明确有：

```text
ticket_confirmation_approved = True
```

所以确认节点后的条件边会进入创建工单节点。

### 练习 3 参考答案

可以映射成：

```text
requester_id = demo_user_001
title = 物流/发货：订单 A1001，物流问题处理
description = 订单 A1001 一直未发货
category = logistics
priority = high
related_order_id = A1001
```

注意：

```text
issue_type -> category
urgency -> priority
order_id -> related_order_id
actor_id -> requester_id
```

### 练习 4 参考答案

因为创建工单是写操作，网络超时或重试时可能重复执行。

`Idempotency-Key` 可以让同一份创建请求重复提交时只创建一张工单。

如果同一个幂等键配了不同参数，服务应该拒绝，避免混乱。

### 练习 5 参考答案

因为自动化测试要稳定、快速、可重复。

真实 HTTP 服务可能没启动、端口冲突、响应变慢、数据没清理。

本节测试的重点是 Agent 是否正确调用创建器，而不是测试 HTTP 网络。

所以用 `FakeTicketCreator` 更合适。

## 九、本节自测题

### 自测 1

`request_ticket_confirmation_node` 和 `create_ticket_node` 的职责分别是什么？

### 自测 2

为什么 `route_by_ticket_confirmation` 只有在 `ticket_confirmation_approved is True` 时才创建？

### 自测 3

`TicketFields` 和 `CreateTicketArgs` 最大的区别是什么？

### 自测 4

为什么本节要给 `java-mock-service` 也增加 `policy_gap`？

### 自测 5

创建成功后，为什么要把 `created_ticket` 写回 State？

## 十、自测题参考答案

### 自测 1 参考答案

`request_ticket_confirmation_node` 负责生成待确认工单和确认话术。

`create_ticket_node` 负责在用户已经确认后调用后端创建工单。

一个是确认准备，一个是执行写操作。

### 自测 2 参考答案

因为创建工单是写操作。

只有明确的 `True` 才代表用户已经确认。

如果字段不存在、为 `False`、为 `None`，都不能执行创建。

### 自测 3 参考答案

`TicketFields` 是 Agent 内部理解用户问题的字段。

`CreateTicketArgs` 是 Java 工单服务要求的接口契约。

二者必须通过明确映射函数转换，不能混用。

### 自测 4 参考答案

因为 Agent 现在会把 RAG 无资料场景标记为：

```text
issue_type = policy_gap
```

如果 Java mock 服务不支持 `policy_gap`，这个场景走到创建工单时就会契约不匹配。

所以要同步扩展下游服务契约。

### 自测 5 参考答案

因为后续流程可能要展示工单号、记录日志、继续处理、做测试断言或保存状态。

`final_answer` 只是给用户看的自然语言，不适合作为后续业务数据源。

## 十一、本节小结

本节完成了智能工单 Agent 的第一个真实写操作节点：

```text
create_ticket
```

现在流程具备了这条能力：

```text
字段完整
-> 请求确认
-> 明确确认
-> 调用 Java mock 创建工单
-> 返回工单号
```

同时，本节仍然保持安全边界：

```text
普通对话不会自动创建工单。
```

这节之后，智能工单 Agent v1 的主业务链路已经越来越完整。

下一节要学的是：

```text
checkpoint 和 thread_id：中断、恢复、继续对话
```

也就是把现在这种“用 State 模拟已确认”的方式，逐步升级成真正可恢复的多轮 Agent 流程。

## 十二、参考资料

1. Pydantic 官方文档：Models
   https://docs.pydantic.dev/latest/concepts/models/

2. HTTPX 官方文档：QuickStart
   https://www.python-httpx.org/quickstart/

3. FastAPI 官方文档：Request Body
   https://fastapi.tiangolo.com/tutorial/body/

4. LangGraph 官方文档：Persistence
   https://docs.langchain.com/oss/python/langgraph/persistence
