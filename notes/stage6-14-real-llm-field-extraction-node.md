# 阶段 6 第 14 节：真实 LLM 字段提取节点

本节目标：把智能工单 Agent 里的“工单字段提取”从固定规则升级为支持真实 LLM 提取，同时保留默认规则模式和 fake 测试模式。

这节不是为了追求“模型更聪明”这么简单，而是学习一个生产化 AI 工程里很重要的能力：

> 让模型负责理解自然语言，让后端代码负责校验边界、控制流程、保证业务安全。

## 一、本节在主线里的位置

上一节我们完成了阶段 6 第 13 节：真实 LLM 意图识别节点。

第 13 节解决的问题是：

```text
用户消息
-> classify_intent
-> 模型或规则判断 intent
-> 后端根据 intent 选择下一条路
```

本节继续往前推进，解决另一个更贴近业务的问题：

```text
用户消息
-> Agent 判断需要创建工单
-> extract_ticket_fields
-> 模型或规则提取 issue_type、order_id、description、user_request、urgency、need_human_review
-> 后端判断字段是否完整
-> 完整则请求用户确认，不完整则追问缺失字段
```

你可以把第 13 节和第 14 节的区别记成一句话：

- 意图识别回答：这句话应该走哪条业务路？
- 字段提取回答：如果要创建工单，需要从这句话里拿到哪些结构化业务字段？

## 二、本节学习目标

学完本节，你要能解释清楚以下问题：

1. 为什么“字段提取”和“意图识别”不是一回事。
2. 为什么字段提取很适合交给 LLM 做，但不能完全相信 LLM。
3. 为什么工单字段必须有固定 schema。
4. 为什么 `order_id` 不能让模型猜。
5. 为什么 `should_create_ticket` 这种流程控制字段不应该放进字段提取模型。
6. 为什么模型输出 JSON 后，还要用 Pydantic 再校验一遍。
7. 为什么测试里不能真实调用模型，而要用 fake client。
8. 为什么默认 Agent 仍然走规则提取，真实 LLM 通过注入方式启用。
9. 手动 smoke 脚本和自动化测试的区别是什么。
10. 怎么把一个真实模型节点接入 LangGraph，但不破坏现有稳定链路。

## 三、本节暂时不学什么

为了边界清晰，本节不提前学习下面这些内容：

- 不接入真实创建工单 API 的复杂确认策略。
- 不让模型决定是否创建工单。
- 不做多轮补槽，也就是用户补充订单号后继续合并字段。
- 不做 prompt 版本管理。
- 不做模型输出失败后的多策略降级。
- 不做 LLM-as-judge 来评估字段提取质量。
- 不改 Java mock service。
- 不在自动化测试中真实调用模型。

这些内容后面会分开学。本节只完成一个最小但完整的真实 LLM 字段提取节点。

这里的“最小”不是内容少，而是工程边界小：

```text
只改字段提取这一件事
只让模型返回字段
只在注入时启用真实模型
只用 fake 测试保证行为
```

## 四、基础知识铺垫

### 1. 什么是字段提取

字段提取，就是把一段自然语言转换成结构化数据。

用户可能这样说：

```text
商品破损，订单 A2001，帮我投诉处理
```

人一眼能看出来里面有几类信息：

```json
{
  "issue_type": "complaint",
  "order_id": "A2001",
  "description": "商品破损，订单 A2001，帮我投诉处理",
  "user_request": "投诉处理",
  "urgency": "high",
  "need_human_review": true
}
```

这就是字段提取。

注意：字段提取不是生成一段漂亮回答，而是把非结构化语言变成后端能处理的数据。

在真实业务系统里，字段提取经常出现于：

- 客服工单自动填单。
- 发票信息提取。
- 合同条款提取。
- 简历信息提取。
- 报销单信息提取。
- 医疗问诊信息预填。
- 订单售后问题分类。

### 2. 字段提取为什么适合 LLM

固定规则适合处理非常稳定、格式很明确的输入。

例如：

```text
订单号：A2001
```

用正则就能提取。

但是用户真实表达通常不稳定：

```text
我那个 A2001 的快递坏了，包装也破了，想让客服帮我处理一下
```

这里有几个难点：

- 订单号不一定写成“订单号：A2001”。
- 用户没说“投诉”，但语义上接近投诉或异常处理。
- 用户说“快递坏了”，可能是物流问题，也可能是商品破损。
- 用户说“帮我处理一下”，需要概括成 `user_request`。
- 紧急程度要结合上下文判断。

LLM 擅长理解这类不规整表达。

所以字段提取是 LLM 的典型强项。

### 3. 字段提取为什么不能完全交给 LLM

LLM 擅长理解语言，但它不是业务系统。

它可能出现这些问题：

- 把不存在的订单号猜出来。
- 把不允许的字段值写成 `"after_sale"`。
- 输出自然语言解释，而不是 JSON。
- 缺少必填字段。
- 多输出业务不允许的字段。
- 把“是否创建工单”也一起决定了。
- 因为 prompt 被用户干扰而改变输出格式。

所以生产系统不能只写一句：

```text
你帮我提取工单字段
```

而要有三层约束：

```text
第一层：prompt 说明任务和规则
第二层：JSON Schema 告诉模型字段结构
第三层：Pydantic 在后端二次校验模型输出
```

本节代码做的就是这三层。

### 4. 意图识别和字段提取的区别

意图识别的输出很小，通常是一个分类：

```json
{
  "intent": "ticket_request",
  "reason": "用户要求人工处理投诉"
}
```

字段提取的输出更贴近业务对象：

```json
{
  "issue_type": "complaint",
  "order_id": "A2001",
  "description": "商品破损，用户希望客服处理订单 A2001。",
  "user_request": "人工处理商品破损投诉",
  "urgency": "high",
  "need_human_review": true
}
```

两者的职责完全不同：

| 对比点 | 意图识别 | 字段提取 |
| --- | --- | --- |
| 主要问题 | 这句话属于哪类请求 | 这句话里有哪些业务字段 |
| 输出粒度 | 粗 | 细 |
| 对流程的影响 | 决定路由方向 | 决定后续是否能创建工单 |
| 典型字段 | intent、reason | issue_type、order_id、description 等 |
| 失败后果 | 走错节点 | 创建工单信息错误或缺失 |

一个用户问题可能先经过意图识别，再经过字段提取：

```text
我要投诉订单 A2001，商品破损
```

第一步：

```json
{"intent": "ticket_request"}
```

第二步：

```json
{
  "issue_type": "complaint",
  "order_id": "A2001",
  "description": "用户投诉订单 A2001 商品破损",
  "user_request": "投诉处理",
  "urgency": "high",
  "need_human_review": true
}
```

### 5. route intent 和 issue_type 不是一个概念

这是本节最容易混的地方。

`intent` 是 Agent 路由用的：

```text
policy_question
order_query
ticket_request
smalltalk
unsupported
unclear
```

`issue_type` 是工单业务分类：

```text
refund
logistics
complaint
policy_gap
unknown
```

例如：

```text
退款规则是什么？
```

它的 `intent` 是：

```text
policy_question
```

因为用户在问规则，不是在要求创建工单。

而如果知识库没有答案，系统决定要记录一个人工工单，那么它的 `issue_type` 可能是：

```text
policy_gap
```

再比如：

```text
我要投诉订单 A2001，物流一直不动
```

它的 `intent` 是：

```text
ticket_request
```

因为用户要进入工单流程。

它的 `issue_type` 可能是：

```text
complaint
```

因为工单业务上这是投诉或异常处理。

所以不能把 `intent` 和 `issue_type` 合并成一个字段。

### 6. 当前工单字段分别表示什么

当前项目里的工单字段是：

```text
issue_type
order_id
description
user_request
urgency
need_human_review
```

逐个理解：

`issue_type`

表示工单业务类型。它不是随便写字符串，只能从固定集合里选：

```text
refund / logistics / complaint / policy_gap / unknown
```

`order_id`

表示相关订单号。如果用户没提供，必须是 `null`。

这个字段最重要的一条规则是：

```text
不能编造订单号。
```

原因很简单：订单号是业务系统定位订单的关键字段，编造订单号会导致后端查询错误、工单关联错误，甚至影响别人的订单。

`description`

表示问题描述。它要尽量保留事实。

例如用户说：

```text
订单 A2001 商品破损，包装盒也裂了
```

description 可以是：

```text
订单 A2001 商品破损，包装盒也裂了。
```

`user_request`

表示用户希望客服做什么。

例如：

```text
帮我投诉处理
```

可以提取成：

```text
投诉处理
```

description 和 user_request 的区别：

```text
description = 发生了什么
user_request = 用户想让客服做什么
```

`urgency`

表示紧急程度：

```text
low / normal / high
```

商品破损、长期未处理、明确催促、明显投诉，一般会倾向 `high`。

`need_human_review`

表示是否需要人工复核。

投诉、知识库缺口、高紧急度、不确定问题，一般需要人工复核。

### 7. 为什么 order_id 可以是 null

很多初学者会觉得：“创建工单不是一定要订单号吗？”

不一定。

要看工单类型。

当前项目里的规则是：

```text
refund / logistics / complaint 通常需要 order_id
policy_gap 可以没有 order_id
unknown 要继续追问
```

例如：

```text
会员等级政策是什么？知识库没查到
```

这类问题如果进入工单，是为了让人工补充知识库或解释政策，不一定和某个订单有关。

所以：

```json
{
  "issue_type": "policy_gap",
  "order_id": null
}
```

是合理的。

但是：

```text
商品破损，帮我处理
```

如果没有订单号，系统应该追问：

```text
请补充相关订单号。
```

这就是为什么“字段提取”和“缺字段判断”要分开。

模型负责提取：

```json
{"order_id": null}
```

代码负责判断：

```text
complaint 类型缺 order_id，所以不能直接进入确认，要追问。
```

### 8. 为什么不让模型输出 should_create_ticket

这节字段模型里没有 `should_create_ticket`。

这是故意的。

因为“是否创建工单”属于流程控制，不属于字段提取。

流程控制应该由 Agent 图和后端代码决定：

```text
intent
-> retrieve_policy
-> decide_ticket_need
-> extract_ticket_fields
-> route_by_ticket_fields_complete
```

如果让模型同时输出：

```json
{
  "should_create_ticket": true
}
```

风险会变大：

- 用户可能通过 prompt injection 要求模型直接创建工单。
- 模型可能绕过 RAG 的 no_context 判断。
- 模型可能把普通咨询误判成创建工单。
- 代码里的路由边界变模糊。

本项目采用的原则是：

```text
模型可以给建议和结构化字段；
真正的业务路由、权限、写操作确认由后端代码控制。
```

这就是 AI 工程里很重要的安全边界。

### 9. JSON mode、JSON Schema、Pydantic 是三件事

这三个概念容易混。

`JSON mode`

表示告诉模型：

```text
请返回 JSON 对象。
```

在代码里是：

```python
response_format={"type": "json_object"}
```

它主要约束“输出必须像 JSON”。

`JSON Schema`

表示告诉模型 JSON 应该长什么样：

```json
{
  "properties": {
    "issue_type": {"enum": ["refund", "logistics", "complaint", "policy_gap", "unknown"]},
    "order_id": {"type": ["string", "null"]}
  }
}
```

本节把 Pydantic 模型生成的 schema 放进 user message，帮助兼容模型理解字段结构。

`Pydantic`

表示后端代码真正拿模型输出做校验：

```python
LLMTicketFields.model_validate_json(raw_json)
```

它是最后一道确定性防线。

本节实现的是：

```text
JSON mode + prompt 内嵌 JSON Schema + Pydantic 二次校验
```

注意：这不等于假设所有 OpenAI-compatible 模型都支持 OpenAI strict Structured Outputs。

OpenAI 官方 Structured Outputs 是更强的 schema 约束能力；兼容模型是否完整支持，要看具体提供商文档和实际验证。所以本项目现在采用更稳妥的兼容写法：让模型按 JSON 返回，再由 Pydantic 严格验收。

### 10. 为什么需要 fake 和 real 双模式

真实模型调用有几个特点：

- 会消耗 API quota。
- 会受网络影响。
- 会受模型版本影响。
- 输出可能有轻微波动。
- 调用速度比本地函数慢。

自动化测试需要稳定、快速、可重复。

所以测试不能真实调用模型。

本节采用：

```text
测试：FakeOpenAICompatibleClient
手动验证：ticket_agent_llm_field_smoke.py
线上或真实模式：create_llm_ticket_field_extractor()
默认主图：仍然走 rule_based
```

这就是工程里常说的依赖注入思想。

### 11. 什么是依赖注入

依赖注入不是玄学。

它只是把“函数内部自己创建依赖”改成“外部传进来依赖”。

不容易测试的写法：

```python
def extract_ticket_fields_node(state):
    client = OpenAI(...)
    return client.chat.completions.create(...)
```

这样测试很难控制模型返回什么。

更容易测试的写法：

```python
def extract_ticket_fields_node(state, *, extractor=None):
    if extractor is None:
        fields = extract_ticket_fields(state)
    else:
        fields = extractor.extract_fields(state)
```

测试时传 fake extractor。

真实 smoke 时传 LLM extractor。

默认运行时不传，继续使用规则。

这样一个节点可以支持三种模式：

```text
rule_based
fake
llm
```

### 12. 模型输出为什么仍然是不可信输入

模型输出虽然来自“我们自己的模型调用”，但在后端系统里仍然要当作外部输入处理。

原因：

- 用户消息会影响模型输出。
- 模型可能没有严格遵守 prompt。
- 兼容模型实现可能和 OpenAI 官方能力不同。
- 网络、服务端异常、返回格式变化都可能发生。

所以模型输出进入业务流程之前必须被验证。

本节的关键语句是：

```python
result = LLMTicketFields.model_validate_json(raw_json)
```

这句话的含义不是“把 JSON 转成对象”这么简单，而是：

```text
只有通过 schema 和字段约束的数据，才能继续进入工单流程。
```

## 五、本节主题系统讲解

### 1. 原来的字段提取链路

原来只有规则提取：

```text
extract_ticket_fields_node
-> extract_ticket_fields(state)
-> 正则提取 order_id
-> 关键词判断 issue_type
-> 规则判断 urgency
-> find_missing_ticket_fields(fields)
-> 写回 state
```

规则提取的优点：

- 快。
- 稳定。
- 可测试。
- 不花钱。

规则提取的缺点：

- 对自然语言变化不敏感。
- 关键词覆盖有限。
- 很难理解复杂表达。
- 每增加一种说法，都要补关键词或正则。

### 2. 本节升级后的链路

现在字段提取节点支持两种方式：

```text
extract_ticket_fields_node(state, extractor=None)
```

如果没有传 `extractor`：

```text
走原来的 rule_based 规则提取
```

如果传入 `LLMTicketFieldExtractor`：

```text
走真实 LLM 字段提取
```

完整链路：

```text
用户消息
-> normalize_user_input
-> classify_intent
-> decide_ticket_need
-> extract_ticket_fields
   -> build_ticket_field_extraction_messages
   -> LLM 返回 JSON
   -> parse_ticket_field_extraction_json
   -> Pydantic 校验
-> find_missing_ticket_fields
-> route_by_ticket_fields_complete
-> request_ticket_confirmation 或 ask_missing_ticket_fields
```

重点：

```text
模型没有决定下一步路由。
```

模型只是返回：

```text
issue_type / order_id / description / user_request / urgency / need_human_review
```

后端代码再判断：

```text
字段完整吗？
该追问还是确认？
```

### 3. 为什么字段提取节点需要 Agent 上下文

字段提取不能只看用户原话，有些时候要结合前面节点的状态。

例如：

```text
用户问：会员等级政策是什么？
RAG 结果：no_context
decide_ticket_need：needs_ticket = true
ticket_need_source = rag_no_context
```

这时字段提取应该倾向：

```json
{
  "issue_type": "policy_gap",
  "order_id": null,
  "description": "用户问题：会员等级政策是什么？知识库未找到足够资料。",
  "user_request": "补充或人工解释知识库未覆盖问题",
  "urgency": "normal",
  "need_human_review": true
}
```

如果模型只看用户原话，它可能不知道这是 RAG 没答上的问题。

所以本节的 prompt 会带上 Agent 上下文：

```json
{
  "intent": "policy_question",
  "ticket_need_source": "rag_no_context",
  "rag_answer_status": "no_context",
  "rag_no_context_reason": "..."
}
```

这让模型知道：

```text
这不是普通政策咨询，而是知识库没覆盖后进入工单流程。
```

### 4. 为什么字段缺失判断仍然放在代码里

模型可以提取字段，但不应该拥有最终业务规则。

例如模型返回：

```json
{
  "issue_type": "complaint",
  "order_id": null
}
```

这不是模型调用失败。

它可能准确表达了“用户没提供订单号”。

此时业务代码要判断：

```text
complaint 类型需要 order_id
所以缺少 order_id
所以要追问用户
```

如果把这个判断交给模型，就会出现不可控问题。

所以本节仍然复用原来的：

```python
find_missing_ticket_fields(fields)
```

它是确定性的业务规则。

### 5. 为什么默认 graph 不能直接改成真实 LLM

很多初学者会想：

```text
既然 LLM 更强，那默认就用 LLM 吧。
```

在学习项目和生产系统里，这都不是好选择。

原因：

- 你本地不一定配置了 API key。
- 自动化测试不能依赖真实网络。
- eval 跑一遍会变慢、变贵。
- 真实模型输出有不稳定性。
- 当前规则链路是已有稳定基线，不能随便破坏。

所以本节采用：

```python
ticket_agent_graph = build_ticket_agent_graph()
```

默认仍然规则提取。

真实 LLM 通过手动脚本启用：

```python
graph = build_ticket_agent_graph(
    field_extractor=create_llm_ticket_field_extractor(),
)
```

这才是更稳的工程升级方式。

### 6. 为什么日志不能记录用户原文和 API key

字段提取会处理用户问题，里面可能包含：

- 订单号。
- 手机号。
- 地址。
- 投诉内容。
- 售后描述。

生产日志不能随便记录这些内容。

本节 LLM 字段提取成功日志只记录：

```text
provider
model
elapsed_ms
issue_type
has_order_id
urgency
need_human_review
prompt_tokens
completion_tokens
total_tokens
```

它没有记录：

```text
用户原文
API key
完整 prompt
完整模型输出
```

这就是生产化日志的基本边界：

```text
足够排查问题，但不泄露敏感信息。
```

## 六、本节代码改动讲解

### 1. 扩展字段提取来源

文件：

```text
projects/ai-service/app/agents/ticket_agent.py
```

原来只有：

```python
TicketFieldExtractionSource = Literal["rule_based"]
```

现在改成：

```python
TicketFieldExtractionSource = Literal["rule_based", "llm"]
```

含义：

- `rule_based`：字段来自规则提取。
- `llm`：字段来自真实模型或 fake LLM extractor。

这个字段写进 Agent state：

```python
ticket_field_extraction_source: TicketFieldExtractionSource
```

它的作用是让我们知道本次字段从哪里来。

这对调试、评测、日志和后续对比规则/模型效果都很重要。

### 2. 新增 `LLMTicketFields`

本节新增：

```python
class LLMTicketFields(BaseModel):
    issue_type: TicketIssueType
    order_id: str | None
    description: str
    user_request: str
    urgency: TicketUrgencyLevel
    need_human_review: bool
```

它是模型输出的后端验收标准。

几个关键点：

`issue_type: TicketIssueType`

表示只能是：

```text
refund / logistics / complaint / policy_gap / unknown
```

如果模型输出：

```json
{"issue_type": "after_sale"}
```

Pydantic 会拒绝。

`order_id: str | None`

表示订单号可以是字符串，也可以是 `null`。

这点很重要，因为用户可能没有提供订单号。

`description: str`

用 `min_length=1` 避免空描述。

`user_request: str`

用 `min_length=1` 避免模型返回空诉求。

`urgency: TicketUrgencyLevel`

只能是：

```text
low / normal / high
```

`need_human_review: bool`

必须是布尔值。

### 3. 为什么要写 field_validator

本节新增：

```python
@field_validator("order_id", mode="before")
def normalize_order_id(...)
```

作用：

```text
把 "  A2001  " 变成 "A2001"
把 "" 变成 None
```

这不是“美化数据”，而是让后续业务判断更稳定。

例如：

```python
if fields["order_id"] is None:
    missing_fields.append("order_id")
```

如果模型返回空字符串 `""`，业务判断可能出现不一致。

所以进入业务流程前要归一化：

```text
空订单号统一变成 None
```

另一个 validator：

```python
@field_validator("description", "user_request", mode="before")
```

作用：

```text
去掉 description 和 user_request 两边多余空白
```

这样后续判断：

```python
if not fields["description"].strip():
```

会更稳定。

### 4. 新增字段提取 prompt

本节新增：

```python
TICKET_FIELD_EXTRACTION_SYSTEM_PROMPT = (...)
```

这个 prompt 明确告诉模型：

- 你是字段提取器。
- 你不是聊天助手。
- 你不决定是否创建工单。
- 你只能返回 JSON。
- `issue_type` 只能从允许集合里选。
- `order_id` 不能编造。
- `urgency` 只能是 `low/normal/high`。
- 不要输出流程控制字段。

这里最重要的一句是：

```text
你的任务不是聊天，也不是决定是否创建工单，而是从用户消息和 Agent 上下文中提取工单字段。
```

它把模型的职责限定住。

### 5. 新增 `get_ticket_field_extraction_json_schema`

代码：

```python
def get_ticket_field_extraction_json_schema() -> dict[str, Any]:
    return LLMTicketFields.model_json_schema()
```

它把 Pydantic 模型变成 JSON Schema。

这个 schema 的作用有两个：

1. 放进 prompt，让模型知道应该返回哪些字段。
2. 帮我们保持 prompt 和后端校验模型来自同一份定义。

这比手写 schema 更不容易出错。

如果以后字段变化，比如新增：

```text
customer_contact
```

只要先改 Pydantic 模型，再生成 schema，就能减少模型提示和后端校验不一致的问题。

### 6. 新增 `build_ticket_field_extraction_messages`

代码职责：

```text
构造发给 LLM 的 messages
```

它会拼出：

```text
system message：字段提取规则
user message：JSON Schema + Agent 上下文 + 用户消息
```

大致结构：

```text
请把下面的 Agent 上下文和用户消息提取成工单字段 JSON。
JSON Schema:
...

Agent 上下文:
...

用户消息:
...
```

为什么不只传用户消息？

因为 `policy_gap` 这类问题需要结合 RAG 状态。

为什么要带 schema？

因为兼容模型不一定支持严格 Structured Outputs，但模型通常能读懂 schema，并按 schema 输出更稳定的 JSON。

### 7. 新增 `parse_ticket_field_extraction_json`

代码职责：

```text
把模型返回的 JSON 字符串，校验成 TicketFields
```

它处理两类失败：

第一类：空响应。

```python
code="TICKET_FIELD_LLM_EMPTY_RESPONSE"
```

第二类：JSON 或字段校验失败。

```python
code="TICKET_FIELD_LLM_VALIDATION_FAILED"
```

这两个错误码很重要。

因为它们区分了不同问题：

- 空响应：模型没有给可处理内容。
- 校验失败：模型给了内容，但不符合我们的业务 schema。

后续第 18 节学习“模型输出失败处理”时，会继续扩展这些错误的兜底策略。

### 8. 新增 `TicketFieldExtractor` Protocol

本节新增：

```python
class TicketFieldExtractor(Protocol):
    extraction_source: TicketFieldExtractionSource

    def extract_fields(self, state: TicketAgentState) -> TicketFields:
        ...
```

它定义了字段提取器必须长什么样。

只要一个对象有：

```text
extraction_source
extract_fields(state)
```

它就能被 `extract_ticket_fields_node` 使用。

这让三种实现可以共存：

```text
RuleBasedTicketFieldExtractor
LLMTicketFieldExtractor
测试里的 StaticFieldExtractor
```

Protocol 的好处是：

```text
节点不关心你具体是什么类，只关心你能不能提取字段。
```

### 9. 新增 `LLMTicketFieldExtractor`

这是本节真实模型字段提取的核心类。

它做几件事：

1. 检查 API key。
2. 构造 messages。
3. 调用 OpenAI-compatible chat completions。
4. 要求返回 JSON object。
5. 读取模型第一段回复。
6. 用 Pydantic 校验。
7. 记录安全日志。
8. 把底层模型异常映射成项目统一异常。

核心调用：

```python
completion = self._get_client().chat.completions.create(
    model=self.settings.llm_model,
    messages=messages,
    response_format={"type": "json_object"},
)
```

这里仍然用当前项目已经学过的 OpenAI-compatible SDK 风格。

也就是说，只要你的模型服务兼容这个接口，并支持对应参数，就可以复用这条链路。

### 10. 修改 `extract_ticket_fields_node`

原来：

```python
def extract_ticket_fields_node(state):
    fields = extract_ticket_fields(state)
```

现在：

```python
def extract_ticket_fields_node(state, *, extractor=None):
    if extractor is None:
        fields = extract_ticket_fields(state)
        extraction_source = "rule_based"
    else:
        fields = extractor.extract_fields(state)
        extraction_source = extractor.extraction_source
```

含义：

- 不传 extractor：保持老逻辑。
- 传 extractor：使用外部注入的字段提取器。

然后仍然执行：

```python
missing_fields = find_missing_ticket_fields(fields)
```

这说明模型只替代了“提取字段”这一步，没有替代“业务规则判断”这一步。

### 11. 修改 `build_ticket_agent_graph`

现在 graph builder 支持：

```python
build_ticket_agent_graph(field_extractor=...)
```

并且在添加节点时：

```python
builder.add_node(
    "extract_ticket_fields",
    lambda state: extract_ticket_fields_node(state, extractor=field_extractor),
)
```

这就是 LangGraph 中常见的依赖注入方式：

```text
图结构不变
节点名字不变
边不变
只是节点内部使用的依赖可以替换
```

它让我们既能保持主流程稳定，又能替换节点能力。

### 12. 新增手动 smoke 脚本

文件：

```text
projects/ai-service/scripts/ticket_agent_llm_field_smoke.py
```

它做的事：

```python
graph = build_ticket_agent_graph(
    field_extractor=create_llm_ticket_field_extractor(),
)
```

也就是只把字段提取换成真实 LLM。

默认消息：

```text
商品破损，订单 A2001，帮我投诉处理
```

运行方式：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run python scripts\ticket_agent_llm_field_smoke.py
```

也可以传自己的消息：

```powershell
uv run python scripts\ticket_agent_llm_field_smoke.py "订单 A3001 一直没发货，帮我处理"
```

这个脚本会输出：

```json
{
  "ok": true,
  "message": "...",
  "intent": "ticket_request",
  "ticket_fields": {
    "issue_type": "...",
    "order_id": "...",
    "description": "...",
    "user_request": "...",
    "urgency": "...",
    "need_human_review": true
  },
  "missing_ticket_fields": [],
  "ticket_fields_complete": true,
  "ticket_field_extraction_source": "llm",
  "node_history": [...]
}
```

注意：这是手动 smoke，会真实调用模型。

自动化测试不会调用它。

## 七、本节测试讲解

本节新增：

```text
projects/ai-service/tests/test_ticket_agent_llm_fields.py
```

测试重点不是“模型聪不聪明”，而是“我们的工程边界是否稳定”。

### 1. prompt 构造测试

测试：

```text
test_build_ticket_field_extraction_messages_include_schema_context_and_message
```

验证：

- system message 说明自己是字段提取器。
- prompt 禁止输出 `should_create_ticket`。
- user message 包含 JSON Schema。
- user message 包含 Agent 上下文。
- user message 包含用户原文。

这个测试防止后面改 prompt 时把关键结构删掉。

### 2. JSON 解析和校验测试

测试：

```text
test_parse_ticket_field_extraction_json_returns_validated_fields
```

验证：

- 合法 JSON 可以被解析。
- `order_id` 两边空格会被去掉。
- `description` 和 `user_request` 会被去掉多余空白。

测试：

```text
test_parse_ticket_field_extraction_json_rejects_invalid_issue_type
```

验证：

- 模型输出非法业务枚举时，后端拒绝。

测试：

```text
test_parse_ticket_field_extraction_json_rejects_empty_response
```

验证：

- 模型空响应不会进入业务流程。

### 3. fake client 测试真实调用边界

测试：

```text
test_llm_ticket_field_extractor_calls_openai_compatible_client
```

验证：

- 调用了 fake OpenAI-compatible client。
- 传入了正确 model。
- 使用了 `response_format={"type": "json_object"}`。
- prompt 包含用户消息。
- 日志记录 provider、model、issue_type、token。
- 日志没有泄露 API key。

这类测试很重要，因为它验证的是“我们怎样调用模型”，不是模型实际质量。

### 4. 注入 extractor 的节点测试

测试：

```text
test_extract_ticket_fields_node_can_use_injected_extractor
```

验证：

- 节点能使用外部传入的 extractor。
- 字段写回 state。
- 缺字段判断仍然运行。
- `ticket_field_extraction_source` 是 `llm`。

### 5. 整图测试

测试：

```text
test_build_ticket_agent_graph_can_extract_fields_with_injected_extractor
```

验证完整路径：

```text
normalize_user_input
-> classify_intent
-> decide_ticket_need
-> extract_ticket_fields
-> request_ticket_confirmation
```

这说明字段提取换成 injected extractor 后，LangGraph 主路径仍然正常。

## 八、手动验证方式

### 1. 自动化测试

在 `projects/ai-service` 下运行：

```powershell
uv run pytest -q tests/test_ticket_agent_llm_fields.py tests/test_ticket_agent_llm_intent.py tests/test_ticket_agent_intent.py tests/test_agent_field_evaluation.py
```

本节执行结果：

```text
119 passed
```

这组测试不会真实调用模型。

### 2. 编译 smoke 脚本

```powershell
uv run python -m py_compile scripts\ticket_agent_llm_intent_smoke.py scripts\ticket_agent_llm_field_smoke.py
```

本节已通过。

### 3. 真实模型 smoke

如果你已经在 `.env` 配置了兼容模型：

```text
LLM_API_KEY=...
LLM_BASE_URL=...
LLM_MODEL=...
LLM_PROVIDER=...
```

可以运行：

```powershell
uv run python scripts\ticket_agent_llm_field_smoke.py
```

如果想自己换一句话：

```powershell
uv run python scripts\ticket_agent_llm_field_smoke.py "订单 A3001 物流一周没动，帮我投诉"
```

这会真实调用模型，所以不要把它放进自动化测试。

## 九、本节容易误解的点

### 误解 1：有了 LLM，就不需要规则了

不对。

LLM 负责理解自然语言，规则负责业务边界。

本节仍然保留：

```text
find_missing_ticket_fields
route_by_ticket_fields_complete
request_ticket_confirmation
```

这说明：

```text
模型是节点能力的一部分，不是整个业务流程的主人。
```

### 误解 2：模型返回 JSON 就一定安全

不对。

JSON 只是格式，不代表业务合法。

下面这个是 JSON，但业务不合法：

```json
{
  "issue_type": "after_sale",
  "order_id": "我猜是 1001",
  "description": "",
  "user_request": "",
  "urgency": "super_high",
  "need_human_review": "yes"
}
```

所以必须用 Pydantic 校验。

### 误解 3：字段提取模型应该决定下一步怎么走

不对。

下一步路由属于后端工作流。

模型最多返回字段。

真正决定：

```text
追问缺字段
请求用户确认
创建工单
结束流程
```

的是 LangGraph 的节点和边。

### 误解 4：真实 smoke 通过就代表系统质量没问题

不对。

smoke 只说明一条样例能跑通。

质量要靠：

- 固定 eval dataset。
- 字段准确率。
- bad case 分析。
- 回归评测。
- 真实线上日志。

后续会继续把真实模型节点纳入评测体系。

## 十、你应该掌握的表达方式

如果别人问你“你这个 Agent 是怎么用模型提取工单字段的”，你可以这样回答：

> 我们没有让模型直接控制工单流程，而是把模型封装成一个字段提取器。它根据用户消息和前面 Agent 节点的上下文返回固定 JSON 字段，比如 issue_type、order_id、description、user_request、urgency 和 need_human_review。后端用 Pydantic 对模型输出做二次校验，校验通过后才进入缺字段判断和用户确认节点。默认图仍然使用规则提取，真实 LLM 通过依赖注入启用，测试里用 fake client 保证稳定性。

如果别人追问“为什么不直接让模型创建工单”，你可以回答：

> 因为创建工单是写操作，必须由后端控制权限、字段完整性和用户确认。模型可以提取字段，但不能越过后端业务规则。我们把自然语言理解交给模型，把流程控制、校验、确认和真实 API 调用留给代码。

## 十一、本节代码地图

核心文件：

```text
projects/ai-service/app/agents/ticket_agent.py
```

新增或修改的关键对象：

```text
LLMTicketFields
TicketFieldExtractor
TICKET_FIELD_EXTRACTION_SYSTEM_PROMPT
get_ticket_field_extraction_json_schema()
build_ticket_field_extraction_messages()
parse_ticket_field_extraction_json()
RuleBasedTicketFieldExtractor
LLMTicketFieldExtractor
create_llm_ticket_field_extractor()
extract_ticket_fields_node(..., extractor=...)
build_ticket_agent_graph(field_extractor=...)
```

新增测试：

```text
projects/ai-service/tests/test_ticket_agent_llm_fields.py
```

新增手动 smoke：

```text
projects/ai-service/scripts/ticket_agent_llm_field_smoke.py
```

顺手修正：

```text
projects/ai-service/scripts/ticket_agent_llm_intent_smoke.py
```

原因：补上 `PROJECT_ROOT` 到 `sys.path`，避免从 `projects/ai-service` 里运行脚本时找不到 `app` 包。

## 十二、本节练习

### 练习 1：判断字段提取结果

题目：

用户说：

```text
订单 A3001 一周没发货，帮我处理一下
```

请你写出合理的字段提取结果。

参考答案：

```json
{
  "issue_type": "logistics",
  "order_id": "A3001",
  "description": "订单 A3001 一周没发货，用户希望客服处理。",
  "user_request": "物流问题处理",
  "urgency": "high",
  "need_human_review": true
}
```

解释：

- 一周没发货属于物流或发货问题。
- 用户明确给出订单号 `A3001`。
- “一周没发货”时间较长，可以认为紧急度偏高。
- 需要客服处理，所以 `need_human_review` 为 true。

### 练习 2：判断缺失字段

题目：

模型返回：

```json
{
  "issue_type": "complaint",
  "order_id": null,
  "description": "商品破损，用户希望处理。",
  "user_request": "人工处理投诉",
  "urgency": "high",
  "need_human_review": true
}
```

后端应该直接请求用户确认吗？

参考答案：

不应该。

原因：

`complaint` 属于当前项目里需要订单号的工单类型，而 `order_id` 是 `null`。

后端应该通过：

```python
find_missing_ticket_fields(fields)
```

得到：

```python
["order_id"]
```

然后进入：

```text
ask_missing_ticket_fields
```

而不是直接进入确认。

### 练习 3：判断模型输出是否合法

题目：

模型返回：

```json
{
  "issue_type": "after_sale",
  "order_id": "A3001",
  "description": "用户要售后。",
  "user_request": "售后处理",
  "urgency": "normal",
  "need_human_review": true
}
```

这个输出能通过 `LLMTicketFields` 吗？

参考答案：

不能。

原因：

`issue_type` 只能是：

```text
refund / logistics / complaint / policy_gap / unknown
```

`after_sale` 不在允许集合里。

Pydantic 会抛出 `ValidationError`，项目会把它转换为：

```text
TICKET_FIELD_LLM_VALIDATION_FAILED
```

### 练习 4：解释为什么不让模型输出 should_create_ticket

题目：

为什么本节字段提取模型不允许输出：

```json
{"should_create_ticket": true}
```

参考答案：

因为 `should_create_ticket` 是流程控制，不是字段提取。

当前 Agent 的创建工单决策由：

```text
classify_intent
retrieve_policy
decide_ticket_need
```

这些节点共同决定。

字段提取节点只负责提取工单字段。

如果让模型决定是否创建工单，会扩大模型权限，增加 prompt injection、误创建工单和绕过后端规则的风险。

### 练习 5：运行 fake 测试

题目：

在 `projects/ai-service` 下运行：

```powershell
uv run pytest -q tests/test_ticket_agent_llm_fields.py
```

它会真实调用模型吗？

参考答案：

不会。

原因：

测试里使用的是：

```text
FakeOpenAICompatibleClient
FakeChatCompletions
StaticFieldExtractor
```

它们都是测试替身，不会访问真实网络，也不会消耗 API key。

## 十三、自测题

### 自测 1：字段提取和意图识别最大的区别是什么？

参考答案：

意图识别决定用户请求属于哪类路由，例如 `ticket_request` 或 `policy_question`。

字段提取是在已经进入工单流程后，把用户消息转换成工单业务字段，例如 `issue_type`、`order_id`、`description`。

### 自测 2：为什么 `order_id` 不能由模型猜？

参考答案：

订单号是业务系统定位订单的关键字段。模型如果猜订单号，可能导致查询错误订单、关联错误工单，甚至影响别人的订单数据。因此用户没提供订单号时必须返回 `null`，由后端追问用户。

### 自测 3：为什么模型输出 JSON 后还要 Pydantic 校验？

参考答案：

JSON 只保证格式，不保证业务合法。模型可能输出非法枚举、缺少字段、字段类型错误或空字符串。Pydantic 可以用确定性规则验证字段类型、长度、枚举范围和空值处理，防止非法模型输出进入业务流程。

### 自测 4：本节为什么默认 graph 仍然使用 rule_based？

参考答案：

默认 graph 要稳定、可测试、不依赖 API key、不消耗费用，也不能让已有 eval 因真实模型波动而不稳定。真实 LLM 字段提取通过 `field_extractor` 注入启用，适合手动 smoke 或后续可控的真实模式。

### 自测 5：`ticket_field_extraction_source` 有什么用？

参考答案：

它记录字段提取来源，比如 `rule_based` 或 `llm`。这样调试、日志、评测和对比规则/模型效果时，可以知道本次字段来自哪种提取方式。

### 自测 6：如果模型返回 `issue_type=complaint` 但 `order_id=null`，下一步应该是什么？

参考答案：

下一步应该进入缺字段追问，而不是请求用户确认。因为当前项目规定 `complaint` 类型需要订单号，`find_missing_ticket_fields(fields)` 会返回 `["order_id"]`。

### 自测 7：fake client 测试主要验证什么？

参考答案：

它主要验证我们的代码是否正确调用 OpenAI-compatible client、是否传入 model/messages/response_format、是否能解析和校验模型输出、是否记录安全日志、是否不泄露 API key。它不验证真实模型质量。

### 自测 8：为什么字段提取 prompt 要包含 Agent 上下文？

参考答案：

因为有些字段不能只靠用户原文判断。例如 RAG 没有检索到答案后进入工单流程时，字段提取要知道 `ticket_need_source=rag_no_context` 和 `rag_answer_status=no_context`，才能更合理地提取 `issue_type=policy_gap`。

## 十四、本节小结

本节完成了一个生产化 AI Agent 里非常关键的升级：

```text
规则字段提取
-> 支持真实 LLM 字段提取
-> 保留默认规则模式
-> fake 测试保障稳定性
-> Pydantic 校验模型输出
-> 后端继续控制缺字段判断和路由
```

你现在应该形成一个清晰认识：

```text
模型不是业务系统。
模型是自然语言理解能力。
后端代码才是业务边界、流程控制和安全确认的执行者。
```

这一点会贯穿后面所有真实模型节点、工具调用、写操作确认、checkpoint 持久化、可观测性和生产稳定性课程。

## 十五、参考资料

- [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)：理解结构化输出、JSON Schema 约束和 JSON mode 的边界。
- [OpenAI Text Generation](https://developers.openai.com/api/docs/guides/text)：理解模型文本生成、messages 和输出格式。
- [OpenAI Chat Completions Create Reference](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create)：查询 chat completions、messages、response_format 等参数。
- [Pydantic Models](https://pydantic.dev/docs/validation/latest/concepts/models/)：理解 `BaseModel`、`model_validate_json()`、`model_json_schema()`。
- [Pydantic Validators](https://pydantic.dev/docs/validation/latest/concepts/validators/)：理解 `field_validator` 如何在字段进入业务前做归一化和校验。
- [Pydantic JSON Schema](https://pydantic.dev/docs/validation/latest/concepts/json_schema/)：理解如何从 Pydantic 模型生成 JSON Schema。
