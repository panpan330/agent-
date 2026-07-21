# 阶段 5 第 19 节：用户确认节点

## 本节定位

前面几节我们已经把智能工单 Agent 的前半段主线接起来了：

```text
用户问题
-> 意图识别
-> 如果是规则问题，先走 RAG
-> 判断是否需要创建工单
-> 提取工单字段
-> 如果字段缺失，就追问用户
```

第 18 节解决的是：

```text
字段不完整时，Agent 应该问用户补什么。
```

本节解决的是另一个同样关键的问题：

```text
字段已经完整时，Agent 也不能马上创建工单，而是要先让用户确认。
```

也就是说，本节要把原来的流程：

```text
extract_ticket_fields
-> END
```

改成：

```text
extract_ticket_fields
-> request_ticket_confirmation
-> END
```

注意，本节仍然不真正调用 Java 服务创建工单。真正创建工单会放到下一节。

## 本节学习目标

学完本节，你应该能讲清楚：

1. 什么是用户确认节点。
2. 为什么字段完整也不能直接创建工单。
3. 用户确认和缺失字段追问有什么区别。
4. 为什么确认内容既要给用户看，也要写进 State。
5. 为什么要保存 `pending_ticket_confirmation`。
6. 为什么确认状态先用 `pending`。
7. 为什么要给待确认工单生成 `confirmation_id`。
8. 为什么本节不直接使用 LangGraph `interrupt()`。
9. 用户确认节点和后面 checkpoint / thread_id / interrupt 的关系。
10. 完整工单链路现在变成了什么样。
11. 如何测试“字段完整进入确认，字段不完整进入追问”。

## 本节先不学什么

本节不提前做这些：

1. 不调用 Java mock 服务创建真实工单。
2. 不保存工单到数据库。
3. 不实现用户回复“确认创建”后的继续执行。
4. 不实现用户修改字段后的合并逻辑。
5. 不接 LangGraph checkpoint。
6. 不接 `thread_id`。
7. 不用 `interrupt()` 暂停图。
8. 不调用真实大模型生成确认话术。
9. 不做前端确认按钮。

这些都不是不重要，而是要按顺序学。

本节先把“确认节点”作为普通节点接进图里，让你先理解业务边界和 State 设计。等后面学 checkpoint、thread_id、interrupt 时，再把这个确认节点升级成真正可以暂停、恢复、继续执行的 human-in-the-loop 流程。

## 一、基础知识铺垫

### 1. 什么是用户确认

用户确认就是：

```text
系统准备执行一个有业务影响的动作前，先把准备执行的内容展示给用户，让用户明确同意后再执行。
```

在我们的智能客服工单 Agent 里，创建工单不是一句闲聊，也不是简单回答问题。创建工单通常意味着：

1. 系统会把用户问题写入业务系统。
2. 后台客服可能会收到任务。
3. 工单可能进入排队、分派、处理流程。
4. 用户的订单号、诉求、投诉内容会被保存。
5. 后续可能触发人工处理、售后审核、补偿流程。

所以它属于“有副作用的动作”。

副作用的意思是：

```text
这个动作执行后，外部世界发生了变化。
```

例如：

```text
查询订单
```

通常只是读数据，不会改变订单状态，所以它是只读操作。

但是：

```text
创建工单
```

会新增一条工单记录，所以它是写操作。

只读操作可以更自动一点。
写操作必须更谨慎。

### 2. 为什么字段完整也不能直接创建

很多初学者容易觉得：

```text
字段都齐了，为什么不直接创建？
```

原因是：字段完整只代表“系统认为信息够了”，不代表“用户同意按这些信息执行”。

这两件事不是一回事。

字段完整解决的是信息问题：

```text
有没有问题类型？
有没有订单号？
有没有问题描述？
有没有用户诉求？
```

用户确认解决的是授权问题：

```text
用户是否同意系统按照这份内容创建工单？
```

举个例子：

```text
用户：我要投诉订单 1001，物流一直不动。
```

Agent 可以抽取出：

```text
issue_type = complaint
order_id = 1001
description = 我要投诉订单 1001，物流一直不动
user_request = 投诉处理
urgency = high
need_human_review = True
```

这些字段看起来完整。

但仍然存在风险：

1. 用户可能只是表达不满，不是真的要创建工单。
2. Agent 对“投诉处理”的理解可能太强。
3. 订单号可能识别错。
4. 紧急程度可能判断偏高。
5. 用户可能想修改描述。
6. 用户可能只想问物流，不想留下投诉记录。

所以正确流程是：

```text
字段完整
-> 生成待确认工单
-> 用户确认
-> 再创建工单
```

### 3. 用户确认和缺失字段追问的区别

第 18 节的“追问”和本节的“确认”很像，都是问用户一句话。

但它们的目的完全不同。

缺失字段追问解决的是：

```text
信息不够，流程不能继续。
```

比如：

```text
请补充相关订单号。
```

用户确认解决的是：

```text
信息够了，但执行前需要用户明确同意。
```

比如：

```text
我已整理好一份待确认工单，请确认是否按以下信息创建。
```

可以这样区分：

| 对比点 | 缺失字段追问 | 用户确认 |
| --- | --- | --- |
| 发生时机 | 字段不完整 | 字段完整 |
| 核心问题 | 缺信息 | 缺授权 |
| 用户要做什么 | 补充信息 | 同意、拒绝或修改 |
| 下一步 | 重新补齐字段 | 创建工单或取消/修改 |
| 本节是否执行写操作 | 不执行 | 也不执行 |

这点非常重要。

以后你做 Agent，不要把“信息完整”和“可以执行”混成一件事。

### 4. 什么是 human-in-the-loop

human-in-the-loop 可以理解为：

```text
让人参与到自动化流程中的关键决策点。
```

不是所有节点都需要人参与。只有这些情况通常需要：

1. 会写数据库。
2. 会调用真实业务 API。
3. 会修改订单、退款、发货、账号等状态。
4. 会产生费用。
5. 会影响用户权益。
6. 大模型判断可能不稳定。
7. 需要人审阅、批准或修改。

本节的用户确认节点就是 human-in-the-loop 的前置版本。

为什么叫前置版本？

因为我们本节只是：

```text
生成确认信息
-> 返回给用户
-> 图执行结束
```

还没有做到：

```text
图暂停
-> 等用户确认
-> 用同一个 thread_id 恢复
-> 继续创建工单
```

真正的暂停和恢复要靠后面要学的 checkpoint、thread_id 和 interrupt。

### 5. 为什么本节不直接用 interrupt

LangGraph 的 `interrupt()` 可以在节点内部暂停执行，等待外部输入。官方文档里也把它用于审批、人工审阅、编辑状态等 human-in-the-loop 场景。

但本节不直接用它，原因是你现在还没有系统学完三件事：

1. checkpoint：图暂停时，状态保存在哪里。
2. thread_id：下一次用户回复时，怎么找到上一次暂停的流程。
3. resume：拿到用户回复后，怎么继续执行原来的节点或后续节点。

如果现在直接上 `interrupt()`，你会看到代码能跑，但很可能不知道为什么要配置 checkpointer，也不知道为什么同一个用户会话要绑定同一个 `thread_id`。

所以本节采用更容易理解的方式：

```text
先把确认做成普通节点。
```

这个节点不暂停图，只返回：

```text
ticket_confirmation_required = True
pending_ticket_confirmation = {...}
final_answer = 确认话术
```

这样你先掌握“确认节点应该产出什么”，再学习“怎么暂停和恢复”。

### 6. 为什么确认信息不能只写在 final_answer 里

`final_answer` 是给用户看的自然语言。

它适合展示：

```text
我已整理好一份待确认工单，请确认是否按以下信息创建...
```

但是后端系统不能只依赖 `final_answer`。

原因是自然语言不适合做后续业务判断。

例如：

```text
问题类型：投诉/异常处理
订单号：1001
紧急程度：高
```

人能看懂，但后端更需要结构化数据：

```python
{
    "issue_type": "complaint",
    "order_id": "1001",
    "urgency": "high",
}
```

结构化数据的好处是：

1. 可以校验。
2. 可以测试。
3. 可以传给 Java API。
4. 可以持久化。
5. 可以生成确认 ID。
6. 可以被前端渲染成表单或确认卡片。
7. 可以在用户修改时精确更新某个字段。

所以本节新增了：

```text
pending_ticket_confirmation
```

它表示：

```text
现在有一份等待用户确认的工单草稿。
```

### 7. 为什么要有 confirmation_id

`confirmation_id` 是待确认工单的标识。

它不是最终工单号。

最终工单号应该由真正的工单系统创建，比如下一节要调用的 Java mock 服务。

`confirmation_id` 解决的是另一个问题：

```text
用户确认的是哪一份工单草稿？
```

如果没有确认 ID，可能出现这些问题：

1. 用户同时发起多个工单请求，系统不知道确认哪一个。
2. 用户修改字段后，旧确认信息和新确认信息混在一起。
3. 后端无法判断确认请求是否对应当前字段版本。
4. 测试中很难稳定断言同一份草稿。

本节用字段内容生成稳定哈希：

```text
ticket_fields
-> JSON 字符串
-> SHA256
-> 取前 16 位作为 confirmation_id
```

这表示：

```text
同样的字段，会生成同样的确认 ID。
字段变了，确认 ID 也会变。
```

这不是生产系统唯一方案，但非常适合学习。

生产系统也可以用：

1. 数据库自增 ID。
2. UUID。
3. 雪花 ID。
4. Redis 中的临时确认 ID。
5. 业务系统返回的 draft ID。

### 8. 为什么确认状态是 pending

`pending` 的意思是：

```text
等待用户处理。
```

本节先只引入一个状态：

```text
pending
```

后面可以扩展为：

```text
pending
approved
rejected
edited
expired
created
failed
```

不要一开始就把状态设计得过大。

现在我们只需要表达：

```text
工单字段完整，但还没得到用户确认。
```

所以 `pending` 足够。

### 9. 为什么要把确认做成独立节点

你可能会问：

```text
为什么不直接在 extract_ticket_fields_node 里生成确认话术？
```

因为两个节点的职责不同。

`extract_ticket_fields_node` 的职责是：

```text
从当前 State 中抽取工单字段，并判断字段是否完整。
```

`request_ticket_confirmation_node` 的职责是：

```text
把完整字段整理成待确认工单，并生成确认话术。
```

拆开以后有几个好处：

1. 每个节点只做一件事。
2. 字段抽取可以独立测试。
3. 确认话术可以独立测试。
4. stream 输出更清楚。
5. 后面可以把确认节点替换成 `interrupt()`。
6. 后面可以在确认节点前后加日志、trace_id、超时、风控。
7. 图路径更能表达业务流程。

LangGraph 的思路就是把流程拆成可观察、可测试、可恢复的节点。

## 二、本节主题系统讲解

### 1. 本节前后的完整流程变化

第 18 节之后，工单流程有两个分支：

```text
字段缺失
-> ask_missing_ticket_fields
-> END
```

```text
字段完整
-> END
```

这个设计还不够真实。

因为字段完整后直接 END，会让用户以为：

```text
系统已经完成处理了。
```

但实际上下一步应该是：

```text
请用户确认这份工单草稿。
```

所以本节把字段完整分支改成：

```text
字段完整
-> request_ticket_confirmation
-> END
```

现在两条分支分别是：

```text
字段缺失
-> 追问缺失字段
-> 等用户补充
```

```text
字段完整
-> 展示待确认工单
-> 等用户确认
```

这才更像真实客服系统。

### 2. 本节新增的 State 字段

本节新增了三个和确认有关的 State 字段：

```python
ticket_confirmation_required: bool
ticket_confirmation_message: str
pending_ticket_confirmation: PendingTicketConfirmation
```

它们的含义分别是：

```text
ticket_confirmation_required
```

表示当前是否需要用户确认。

```text
ticket_confirmation_message
```

表示给用户看的确认话术。

```text
pending_ticket_confirmation
```

表示机器可处理的待确认工单草稿。

注意这三个字段不是重复，而是面向不同用途。

`ticket_confirmation_required` 适合前端判断：

```text
要不要显示确认按钮？
```

`ticket_confirmation_message` 适合聊天窗口展示：

```text
给用户看什么文字？
```

`pending_ticket_confirmation` 适合后端继续处理：

```text
用户确认后，拿哪份字段去创建工单？
```

### 3. 本节新增的 PendingTicketConfirmation

本节新增了一个 TypedDict：

```python
class PendingTicketConfirmation(TypedDict):
    confirmation_id: str
    status: TicketConfirmationStatus
    title: str
    summary: str
    ticket_fields: TicketFields
    message: str
```

逐个解释：

```text
confirmation_id
```

待确认草稿 ID。它用来区分“用户确认的是哪一份草稿”。

```text
status
```

当前确认状态。本节只有 `pending`，代表等待用户确认。

```text
title
```

给前端、日志或调试界面看的简短标题。

```text
summary
```

一句话摘要，方便列表展示。

```text
ticket_fields
```

真正用于创建工单的结构化字段。

```text
message
```

给用户看的确认话术。

这里最关键的是：

```text
message 是展示层内容。
ticket_fields 是业务层内容。
```

不要把展示文本当成业务数据源。

### 4. 字段完整路由为什么从 finish 改成 request_confirmation

第 18 节里有：

```python
TicketFieldCompletionRoute = Literal["ask_missing_fields", "finish"]
```

含义是：

```text
字段缺失 -> ask_missing_fields
否则 -> finish
```

本节改成：

```python
TicketFieldCompletionRoute = Literal["ask_missing_fields", "request_confirmation"]
```

含义变成：

```text
字段缺失 -> ask_missing_fields
字段完整 -> request_confirmation
```

这个改变不只是改名字。

它代表业务流程升级了：

```text
字段完整不是终点，而是进入确认。
```

### 5. 为什么 route_by_ticket_fields_complete 默认走追问

本节路由函数变成：

```python
def route_by_ticket_fields_complete(state: TicketAgentState) -> TicketFieldCompletionRoute:
    if state.get("ticket_fields_complete") is True:
        return "request_confirmation"
    return "ask_missing_fields"
```

注意这里不是：

```python
if state.get("ticket_fields_complete") is False:
    return "ask_missing_fields"
return "request_confirmation"
```

区别在默认值。

现在只有在明确为 `True` 时，才进入确认。

如果字段完整状态不存在、为 `None`、或者前面节点异常没写入，都会走追问分支。

这体现了一个安全原则：

```text
不确定时，不要进入更靠近写操作的分支。
```

确认节点虽然还没有真正创建工单，但它比追问更靠近“创建工单”。所以默认应该更保守。

### 6. 确认话术应该包含什么

确认话术至少要包含：

1. 明确告诉用户这是一份待确认工单。
2. 问题类型。
3. 订单号。
4. 问题描述。
5. 用户诉求。
6. 紧急程度。
7. 是否需要人工复核。
8. 用户下一步应该怎么回复。

本节生成的话术类似：

```text
我已整理好一份待确认工单，请确认是否按以下信息创建：
问题类型：投诉/异常处理
订单号：1001
问题描述：我要投诉订单 1001，物流一直不动
用户诉求：投诉处理
紧急程度：高
是否需要人工复核：是
如果信息正确，请回复“确认创建”；如果不正确，请说明需要修改的内容。
```

这段话的设计重点不是好看，而是清晰。

用户看到后应该能立刻判断：

```text
这是不是我要提交的问题？
有没有字段识别错？
我下一步该回复什么？
```

### 7. 为什么要做中文标签映射

内部字段是英文枚举：

```text
complaint
logistics
refund
policy_gap
high
normal
low
```

这些适合代码，但不适合直接展示给用户。

用户应该看到：

```text
投诉/异常处理
物流/发货
退款/退货
知识库缺口
高
普通
低
```

所以本节增加了：

```python
TICKET_ISSUE_TYPE_LABELS
TICKET_URGENCY_LABELS
```

这就是展示层映射。

内部字段保持稳定，展示文本可以根据语言、产品风格、前端需求调整。

### 8. 本节完整路径示例

用户输入：

```text
我要投诉订单 1001，物流一直不动
```

现在路径是：

```text
normalize_user_input
-> classify_intent
-> decide_ticket_need
-> extract_ticket_fields
-> request_ticket_confirmation
```

对应含义：

```text
清理输入
-> 判断是工单诉求
-> 判断需要创建工单
-> 提取完整字段
-> 生成待确认工单
```

最终不会说：

```text
工单已创建。
```

而是说：

```text
请确认是否按以下信息创建。
```

这就是本节最核心的行为变化。

### 9. 缺字段路径是否受影响

用户输入：

```text
商品破损，帮我处理
```

Agent 可以知道：

```text
issue_type = complaint
description = 商品破损，帮我处理
user_request = 人工处理
urgency = high
```

但缺：

```text
order_id
```

所以路径仍然是：

```text
normalize_user_input
-> classify_intent
-> decide_ticket_need
-> extract_ticket_fields
-> ask_missing_ticket_fields
```

不会进入：

```text
request_ticket_confirmation
```

因为还没到确认的时候。

如果缺信息时就让用户确认，会导致用户确认一份不完整的工单，后面创建时仍然失败。

### 10. RAG no_context 为什么也会进入确认

用户输入：

```text
会员等级政策是什么？
```

如果知识库没有查到足够信息，前面第 16 节已经规定：

```text
RAG no_context
-> 需要创建工单
```

第 17 节会把它整理成：

```text
issue_type = policy_gap
order_id = None
description = 用户问题：会员等级政策是什么？；知识库未找到足够资料。
user_request = 补充或人工解释知识库未覆盖问题
urgency = normal
need_human_review = True
```

这个场景不要求订单号，因为它不是退款、物流、投诉类订单问题。

所以字段完整。

本节之后，它也会进入：

```text
request_ticket_confirmation
```

这说明确认节点不仅服务“投诉工单”，也服务“知识库缺口转人工”。

### 11. 本节和下一节的关系

本节结束时，系统只做到：

```text
生成待确认工单。
```

下一节会继续：

```text
用户确认后
-> 调用 Java mock 服务
-> 创建工单
-> 拿到工单 ID
-> 返回创建结果
```

所以本节是写操作之前的最后一道边界。

如果没有这一节，下一节直接接 Java 创建工单，就会缺一个非常重要的安全步骤。

## 三、本节代码改动讲解

### 1. 新增确认相关类型

新增：

```python
TicketConfirmationStatus = Literal["pending"]
```

它表示确认状态。

目前只有 `pending`，因为本节只生成待确认工单，不处理确认结果。

新增：

```python
class PendingTicketConfirmation(TypedDict):
    confirmation_id: str
    status: TicketConfirmationStatus
    title: str
    summary: str
    ticket_fields: TicketFields
    message: str
```

它表示一份“等待用户确认的工单草稿”。

### 2. State 新增确认字段

新增：

```python
ticket_confirmation_required: bool
ticket_confirmation_message: str
pending_ticket_confirmation: PendingTicketConfirmation
```

这让后续节点、测试、前端都可以从 State 里读到确认信息。

### 3. 字段完整路由改变

原来：

```text
字段完整 -> finish
```

现在：

```text
字段完整 -> request_confirmation
```

对应常量：

```python
TICKET_AGENT_FIELD_COMPLETION_ROUTES = {
    "ask_missing_fields": "ask_missing_ticket_fields",
    "request_confirmation": "request_ticket_confirmation",
}
```

这说明图结构现在明确知道：

```text
字段完整后要去确认节点。
```

### 4. 新增确认 ID 生成函数

新增：

```python
def build_ticket_confirmation_id(fields: TicketFields) -> str:
    confirmation_payload = json.dumps(fields, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(confirmation_payload.encode("utf-8")).hexdigest()[:16]
```

关键点：

1. `json.dumps` 把字段变成字符串。
2. `sort_keys=True` 保证字段顺序稳定。
3. `ensure_ascii=False` 让中文按 UTF-8 内容参与计算。
4. `sha256` 生成稳定哈希。
5. 取前 16 位，让 ID 足够短，便于学习和测试。

### 5. 新增确认话术函数

新增：

```python
def build_ticket_confirmation_message(fields: TicketFields) -> str:
```

它负责把结构化字段转成人能看懂的确认文本。

注意它没有修改 State，也不做外部调用，只做一件事：

```text
格式化确认话术。
```

这种函数很容易测试。

### 6. 新增待确认工单构建函数

新增：

```python
def build_pending_ticket_confirmation(fields: TicketFields) -> PendingTicketConfirmation:
```

它负责把字段包装成一份完整的待确认对象。

它包含：

```text
confirmation_id
status
title
summary
ticket_fields
message
```

以后用户确认时，后端就可以拿这份对象继续创建工单。

### 7. 新增 request_ticket_confirmation_node

新增节点：

```python
def request_ticket_confirmation_node(state: TicketAgentState) -> TicketAgentState:
```

它做三件事：

1. 从 State 读取 `ticket_fields`。
2. 构建 `pending_ticket_confirmation`。
3. 把确认信息写回 State 和 `final_answer`。

正常返回：

```python
{
    "ticket_confirmation_required": True,
    "ticket_confirmation_message": pending_confirmation["message"],
    "pending_ticket_confirmation": pending_confirmation,
    "final_answer": pending_confirmation["message"],
    "node_history": ["request_ticket_confirmation"],
}
```

这里的 `final_answer` 仍然是当前对用户输出的最后一句话。

### 8. 图里注册确认节点

新增：

```python
builder.add_node("request_ticket_confirmation", request_ticket_confirmation_node)
```

并把它接到结束：

```python
("request_ticket_confirmation", END)
```

所以本节不是无限等待用户，而是先把确认请求返回出去。

后续学 checkpoint / interrupt 时，再让图真正停在这里并等待恢复。

## 四、本节测试讲解

本节重点测试这些行为：

1. 字段完整时，路由返回 `request_confirmation`。
2. 字段不完整时，路由返回 `ask_missing_fields`。
3. 确认话术包含关键字段。
4. 同一份字段生成稳定的确认 ID。
5. 确认节点会写入 `pending_ticket_confirmation`。
6. 完整工单路径会经过 `request_ticket_confirmation`。
7. 缺订单号路径仍然经过 `ask_missing_ticket_fields`。
8. stream 输出里能看到确认节点更新。

测试里没有真实调用 Java，也没有真实调用大模型。

这是刻意设计的。

因为本节要验证的是：

```text
图结构和确认节点行为。
```

不是验证外部服务。

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
   -> request_confirmation -> request_ticket_confirmation -> END
```

本节真正新增的是最后一段：

```text
extract_ticket_fields
-> request_ticket_confirmation
-> END
```

## 六、你需要真正理解的核心句子

1. 字段完整不等于用户授权。
2. 写操作之前必须有确认边界。
3. 用户确认节点不是创建工单节点。
4. 确认话术给人看，待确认对象给机器用。
5. `final_answer` 不能替代结构化 State。
6. `pending` 表示当前等待用户确认。
7. `confirmation_id` 表示用户确认的是哪一版草稿。
8. 不确定字段是否完整时，应走追问，而不是走确认。
9. 本节是后续 Java 创建工单节点的前置安全步骤。
10. 后续 checkpoint / interrupt 会让确认流程真正具备暂停和恢复能力。

## 七、本节练习

### 练习 1：判断流程

用户输入：

```text
我要投诉订单 1001，物流一直不动
```

请写出本节之后的完整节点路径。

### 练习 2：判断分支

用户输入：

```text
商品破损，帮我处理
```

这条请求为什么不应该进入 `request_ticket_confirmation`？

### 练习 3：解释字段

请解释下面三个字段分别给谁用：

```text
ticket_confirmation_required
ticket_confirmation_message
pending_ticket_confirmation
```

### 练习 4：解释 confirmation_id

为什么待确认工单需要 `confirmation_id`？它和真正的工单号有什么区别？

### 练习 5：设计确认话术

如果字段是：

```text
issue_type = refund
order_id = A1001
description = 用户申请退款，商品还未发货
user_request = 售后退款处理
urgency = normal
need_human_review = true
```

请你写一段适合给用户看的确认话术。

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

因为用户明确表达投诉诉求，并提供了订单号，字段完整，所以进入确认节点。

### 练习 2 参考答案

因为这句话虽然能判断出大概是投诉或异常处理，也能生成描述和诉求，但没有订单号。

对于 `complaint` 类型，本项目规定订单号是必填字段。

所以它应该进入：

```text
ask_missing_ticket_fields
```

而不是进入：

```text
request_ticket_confirmation
```

确认一份缺少订单号的工单没有意义，后面创建时也可能失败。

### 练习 3 参考答案

`ticket_confirmation_required` 给前端或调用方判断是否需要展示确认交互。

`ticket_confirmation_message` 给用户看，是聊天窗口里的确认文本。

`pending_ticket_confirmation` 给后端继续处理，是结构化的待确认工单草稿。

### 练习 4 参考答案

`confirmation_id` 用来标识一份待确认草稿，解决“用户确认的是哪一份内容”的问题。

它不是最终工单号。

最终工单号应该由真正的工单系统在创建成功后返回。

可以理解为：

```text
confirmation_id = 创建前的草稿确认编号
ticket_id = 创建后的正式工单编号
```

### 练习 5 参考答案

可以这样写：

```text
我已整理好一份待确认工单，请确认是否按以下信息创建：
问题类型：退款/退货
订单号：A1001
问题描述：用户申请退款，商品还未发货
用户诉求：售后退款处理
紧急程度：普通
是否需要人工复核：是
如果信息正确，请回复“确认创建”；如果不正确，请说明需要修改的内容。
```

## 九、本节自测题

### 自测 1

为什么不能把“字段完整”直接等同于“可以创建工单”？

### 自测 2

`pending_ticket_confirmation` 里为什么还要保存 `ticket_fields`，而不是只保存确认话术？

### 自测 3

本节为什么没有直接使用 LangGraph `interrupt()`？

### 自测 4

`request_ticket_confirmation_node` 是读操作节点还是写操作节点？为什么？

### 自测 5

如果 `ticket_fields_complete` 不存在，路由为什么默认走 `ask_missing_fields`？

## 十、自测题参考答案

### 自测 1 参考答案

字段完整只说明信息足够，不说明用户同意执行。

创建工单是写操作，会影响业务系统，所以执行前需要用户确认。

### 自测 2 参考答案

确认话术是自然语言，适合展示给用户，但不适合后端继续处理。

`ticket_fields` 是结构化数据，能校验、测试、传给 Java API、保存和修改。

### 自测 3 参考答案

因为 `interrupt()` 需要配合 checkpoint、thread_id 和 resume 才能真正实现暂停和恢复。

本节还没系统学习这些内容，所以先把确认做成普通节点，先掌握确认节点应该产出什么。

### 自测 4 参考答案

它是当前 Agent State 内部的写入节点，但不是外部业务写操作节点。

它会写入：

```text
ticket_confirmation_required
ticket_confirmation_message
pending_ticket_confirmation
final_answer
```

但它不会调用 Java 服务，不会创建真实工单，不会修改数据库。

### 自测 5 参考答案

因为不确定字段是否完整时，不能进入更靠近写操作的确认分支。

默认走追问更保守，也更安全。

## 十一、本节小结

本节完成了智能工单 Agent 的一个重要安全边界：

```text
字段完整
-> 不直接创建
-> 先请求用户确认
```

现在完整工单请求会生成：

```text
pending_ticket_confirmation
ticket_confirmation_message
final_answer
```

这说明 Agent 已经能把“工单草稿”展示给用户确认。

下一节就可以在这个基础上学习：

```text
确认之后，如何调用 Java mock 服务创建工单。
```

## 十二、参考资料

1. LangGraph 官方文档：Thinking in LangGraph
   https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph

2. LangGraph 官方文档：Interrupts
   https://docs.langchain.com/oss/python/langgraph/interrupts

3. LangGraph 官方文档：Persistence
   https://docs.langchain.com/oss/python/langgraph/persistence
