# 阶段 6 第 15 节：Pydantic 校验模型输出

本节目标：把“模型返回了 JSON”这件事继续往下讲透，真正理解为什么 AI 项目里必须用 Pydantic 对模型输出做后端验收。

第 13 节我们做了真实 LLM 意图识别节点。

第 14 节我们做了真实 LLM 字段提取节点。

这两节都有一个共同点：

```text
模型返回 JSON
-> 后端解析 JSON
-> 后端把结果写入 Agent state
-> 后续节点继续执行
```

但这里有一个很关键的问题：

```text
JSON 格式正确，不等于业务数据正确。
```

所以第 15 节单独学习 Pydantic 校验模型输出。

## 一、本节在主线里的位置

当前阶段 6 的节奏是：

```text
第 12 节：evaluator 类型
第 13 节：真实 LLM 意图识别节点
第 14 节：真实 LLM 字段提取节点
第 15 节：Pydantic 校验模型输出
```

你可以把这几节连起来理解：

```text
第 13 节：模型能不能参与 Agent 节点
第 14 节：模型能不能提取业务字段
第 15 节：模型输出能不能被后端安全接收
```

本节不是重新学 Pydantic 基础语法，而是把 Pydantic 放到 AI 工程场景里理解：

> 模型输出就是外部输入，必须先验收，再进入业务流程。

## 二、本节学习目标

学完本节，你要能讲清楚：

1. 为什么模型输出属于“不可信输入”。
2. 为什么 JSON 解析成功不代表业务校验成功。
3. Pydantic 的模型、字段、约束、validator 分别负责什么。
4. `Literal` 为什么适合约束意图和业务枚举。
5. `Field(min_length=...)`、`Field(max_length=...)`、`Field(pattern=...)` 在模型输出里解决什么问题。
6. `ConfigDict(extra="forbid")` 为什么能防止模型偷偷多输出字段。
7. `field_validator(mode="before")` 为什么适合做空白清理和空值归一化。
8. `StrictBool` 为什么能防止模型把 `"true"` 当成布尔值混进业务。
9. 为什么校验失败要变成项目统一异常，而不是让底层 `ValidationError` 直接抛出去。
10. 自动化测试应该怎样覆盖“模型乱输出”的情况。

## 三、本节暂时不学什么

本节只围绕 Pydantic 校验模型输出，不提前展开这些内容：

- 不做 prompt 版本管理。
- 不做模型失败后的自动重试和降级。
- 不做多模型输出对比。
- 不做 LLM-as-judge 校验。
- 不把真实模型调用加入全量 eval。
- 不改写 Agent 主流程。
- 不改变默认规则模式。

本节代码改动很小：

```text
把现有两个 LLM 输出模型变得更严格
增加一组坏输出测试
写清楚这些校验规则为什么存在
```

## 四、基础知识铺垫

### 1. 什么叫“不可信输入”

在后端开发里，只要数据不是你代码内部自己稳定生成的，都应该先当成不可信输入。

常见不可信输入包括：

- 用户请求 body。
- URL query 参数。
- 表单输入。
- 第三方接口响应。
- 消息队列里的消息。
- 文件内容。
- 数据库里历史脏数据。
- 大模型返回的文本。

为什么模型输出也算不可信？

因为模型输出不是确定性代码生成的。

模型输出会受这些因素影响：

- 用户输入。
- prompt。
- 模型版本。
- 温度参数。
- 提供商兼容程度。
- 网络返回内容。
- 模型对 schema 的理解。
- prompt injection。

所以即使模型是你自己调用的，它的输出也不能直接进入业务系统。

### 2. JSON 解析和业务校验不是一回事

这句话非常重要：

```text
JSON 解析只回答“这个字符串是不是 JSON”。
业务校验回答“这个 JSON 能不能被业务接受”。
```

例如下面这个能被解析成 JSON：

```json
{
  "intent": "refund",
  "reason": "用户要退款"
}
```

但在当前 Agent 里它不合法。

因为 `intent` 只能是：

```text
policy_question
order_query
ticket_request
smalltalk
unsupported
unclear
```

`refund` 是工单业务类型，不是 Agent 路由意图。

再看这个：

```json
{
  "issue_type": "complaint",
  "order_id": "我猜是 A2001",
  "description": "",
  "user_request": "处理一下",
  "urgency": "super_high",
  "need_human_review": "true",
  "should_create_ticket": true
}
```

它也是 JSON。

但它有很多业务问题：

- `order_id` 不是纯订单号。
- `description` 为空。
- `urgency` 不在允许枚举里。
- `need_human_review` 是字符串，不是布尔值。
- `should_create_ticket` 是多余流程控制字段。

所以：

```text
JSON 能 parse，只是第一关。
Pydantic 能 validate，才是业务入口。
```

### 3. Pydantic 在 AI 项目里到底负责什么

Pydantic 不是“把字典变成对象”这么简单。

在 AI 项目里，它承担的是模型输出验收工作：

```text
模型原始文本
-> JSON 字符串
-> Pydantic 模型校验
-> 业务可接受的 Python 数据
```

它主要负责：

- 字段是否存在。
- 字段类型是否正确。
- 字段值是否在允许范围内。
- 字符串是否为空。
- 字符串长度是否合理。
- 字符串格式是否符合规则。
- 是否出现了多余字段。
- 某些字段是否需要归一化。

本节不是为了“用上 Pydantic”，而是为了建立一个工程原则：

```text
任何 LLM 输出进入业务系统前，都必须有可解释、可测试、可复现的校验层。
```

### 4. BaseModel 是输出结构的边界

在当前项目里，意图识别模型是：

```python
class LLMTicketIntentClassification(BaseModel):
    intent: TicketIntent
    reason: str
```

字段提取模型是：

```python
class LLMTicketFields(BaseModel):
    issue_type: TicketIssueType
    order_id: str | None
    description: str
    user_request: str
    urgency: TicketUrgencyLevel
    need_human_review: StrictBool
```

它们不是普通类。

它们是模型输出的合同。

意思是：

```text
模型只有按这个结构输出，后端才接收。
```

### 5. Literal 为什么适合约束模型输出

`Literal` 表示字段只能取固定值。

例如：

```python
TicketIntent = Literal[
    "policy_question",
    "order_query",
    "ticket_request",
    "smalltalk",
    "unsupported",
    "unclear",
]
```

这非常适合 AI 输出里的分类字段。

因为模型很容易输出相似但不合法的词：

```text
refund
after_sale
manual_service
complain
customer_support
```

这些词人能看懂，但后端路由不能接受。

后端路由需要稳定字段：

```text
ticket_request
```

所以 `Literal` 的价值是：

```text
把“意思差不多”变成“必须完全匹配业务枚举”。
```

### 6. Field 负责字段级约束

`Field()` 可以给字段增加约束。

例如：

```python
reason: str = Field(min_length=1, max_length=500)
```

含义：

```text
reason 不能是空字符串
reason 最多 500 个字符
```

字段提取里的订单号：

```python
order_id: str | None = Field(
    default=None,
    min_length=1,
    max_length=64,
    pattern=r"^[A-Za-z0-9_-]+$",
)
```

含义：

- 可以是字符串。
- 也可以是 `None`。
- 如果是字符串，最少 1 个字符。
- 最多 64 个字符。
- 只能包含英文字母、数字、下划线、短横线。

这样模型输出：

```json
{"order_id": "A2001"}
```

可以通过。

但模型输出：

```json
{"order_id": "我猜是 A2001"}
```

不能通过。

### 7. ConfigDict(extra="forbid") 解决什么问题

Pydantic 默认对多余字段可能比较宽容。

但是 LLM 输出场景里，宽容不一定是好事。

例如模型返回：

```json
{
  "intent": "ticket_request",
  "reason": "用户要投诉",
  "confidence": 0.92
}
```

`confidence` 看起来没有危害，但它不是我们定义的输出合同。

再比如字段提取返回：

```json
{
  "issue_type": "complaint",
  "order_id": "A2001",
  "description": "商品破损",
  "user_request": "投诉处理",
  "urgency": "high",
  "need_human_review": true,
  "should_create_ticket": true
}
```

`should_create_ticket` 就很危险了。

它试图让模型参与流程控制。

所以本节给两个 LLM 输出模型都加了：

```python
model_config = ConfigDict(extra="forbid")
```

含义：

```text
模型多输出一个字段也不接受。
```

这是一个很重要的生产化习惯：

```text
LLM 输出 schema 要尽量窄，不要宽。
```

### 8. field_validator 的作用

`field_validator` 用来处理字段进入模型前后的自定义逻辑。

本节用的是：

```python
@field_validator("order_id", mode="before")
```

`mode="before"` 的意思是：

```text
在 Pydantic 做类型和约束校验之前，先处理这个值。
```

为什么要 before？

因为模型可能返回：

```json
{"order_id": "  A2001  "}
```

我们希望先把它变成：

```text
A2001
```

然后再进入 `pattern` 校验。

如果不先 strip，它可能因为空格不符合正则而失败。

再比如模型返回：

```json
{"order_id": "未提供"}
```

业务上这不是订单号，而是“没有订单号”。

所以我们把它归一成：

```python
None
```

这就是 validator 的价值：

```text
在严格校验之前，先做少量可解释的数据清理。
```

### 9. 归一化和放宽校验不是一回事

这里有一个边界要注意。

归一化不是纵容模型乱输出。

合理归一化：

```text
"  A2001  " -> "A2001"
"null" -> None
"未提供" -> None
```

不合理放宽：

```text
"我猜是 A2001" -> "A2001"
```

为什么不应该把“我猜是 A2001”自动变成 `A2001`？

因为这里面有“猜”的语义。

订单号不能猜。

所以本节的规则是：

```text
空白和明确无值表达可以归一化。
带解释、猜测、自然语言的订单号不能通过。
```

### 10. StrictBool 为什么有必要

JSON 里真正的布尔值是：

```json
true
false
```

但模型可能输出：

```json
"true"
```

这是字符串，不是布尔值。

在一些场景里，Pydantic 可能会做类型转换，把 `"true"` 理解成 `True`。

但在模型输出验收里，我们更希望它严格：

```text
你说字段是 bool，就必须给 JSON bool。
```

所以本节把：

```python
need_human_review: bool
```

改成：

```python
need_human_review: StrictBool
```

这样模型输出：

```json
{"need_human_review": "true"}
```

会被拒绝。

### 11. 校验失败为什么要变成 AppException

Pydantic 原始错误是：

```python
ValidationError
```

它适合开发者看，但不适合直接暴露给业务调用方。

当前项目统一转换成：

```python
AppException(
    code="TICKET_FIELD_LLM_VALIDATION_FAILED",
    message="模型工单字段提取结果校验失败，请稍后重试。",
    status_code=502,
    details=...
)
```

这样做有几个好处：

- 错误码稳定。
- HTTP 状态码稳定。
- 用户看到的 message 可控。
- details 可以给内部排查使用。
- 后续 fallback 可以按错误码分支处理。

所以异常转换也是模型输出安全的一部分。

### 12. 为什么这里用 502

模型输出校验失败，本质上不是用户请求 JSON 格式错。

用户可能只是正常提问。

失败发生在：

```text
后端调用上游模型
-> 上游模型返回了不符合合同的数据
```

所以当前项目用：

```text
502
```

表达上游模型结果不可用。

这比直接返回 500 更清晰。

后续如果做更细粒度错误处理，也可以区分：

- 模型空响应。
- 模型 JSON 格式错误。
- 模型 schema 校验失败。
- 模型服务超时。
- 模型服务限流。

## 五、本节主题系统讲解

### 1. 当前模型输出进入业务的完整路径

以字段提取为例：

```text
LLMTicketFieldExtractor.extract_fields(state)
-> build_ticket_field_extraction_messages(state)
-> client.chat.completions.create(...)
-> extract_first_reply(completion)
-> parse_ticket_field_extraction_json(raw_reply)
-> LLMTicketFields.model_validate_json(raw_reply)
-> 返回 TicketFields
-> find_missing_ticket_fields(fields)
-> 写入 Agent state
```

真正的关口在：

```python
LLMTicketFields.model_validate_json(raw_json)
```

这一步没通过，后面的业务流程就不会继续执行。

### 2. 本节给意图识别输出加了什么

意图识别模型：

```python
class LLMTicketIntentClassification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: TicketIntent
    reason: str = Field(min_length=1, max_length=500)
```

它现在能拦住：

```json
{
  "intent": "ticket_request",
  "reason": "用户要求人工处理。",
  "confidence": 0.91
}
```

为什么要拦住 `confidence`？

因为当前业务合同没定义它。

如果后续真的需要 confidence，就应该明确新增字段、补测试、更新笔记，而不是让模型随便多输出。

这叫：

```text
schema 显式演进
```

而不是：

```text
模型想给什么就收什么
```

### 3. 本节给字段提取输出加了什么

字段提取模型：

```python
class LLMTicketFields(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issue_type: TicketIssueType
    order_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
    )
    description: str = Field(min_length=1, max_length=1000)
    user_request: str = Field(min_length=1, max_length=200)
    urgency: TicketUrgencyLevel
    need_human_review: StrictBool
```

它现在能拦住：

```json
{
  "should_create_ticket": true
}
```

能拦住：

```json
{
  "order_id": "我猜是 A2001"
}
```

能拦住：

```json
{
  "need_human_review": "true"
}
```

能拦住：

```json
{
  "description": "   "
}
```

这就是本节的核心价值：

```text
把模型可能犯的错，用确定性测试和确定性校验提前挡住。
```

### 4. 为什么多余字段要被拒绝

多余字段有两类。

第一类是看似无害的字段：

```json
{
  "confidence": 0.9
}
```

第二类是危险字段：

```json
{
  "should_create_ticket": true,
  "route": "create_ticket",
  "execute_now": true
}
```

如果 Pydantic 忽略多余字段，第一类字段看起来没问题。

但问题是：

```text
你也同时忽略了第二类字段曾经出现过。
```

在学习阶段和生产化早期，更好的做法是：

```text
只要模型多输出字段，就认为它没有遵守合同。
```

这样可以逼着 prompt、schema 和模型调用保持清晰。

### 5. 为什么订单号要有 pattern

订单号是和业务系统关联的关键字段。

它不能是自然语言解释。

允许：

```text
A2001
1001
ORDER_1001
ORDER-1001
```

不允许：

```text
我猜是 A2001
订单应该是 A2001
没有提供
不知道
```

当前 pattern 是：

```python
r"^[A-Za-z0-9_-]+$"
```

意思是：

```text
从开头到结尾，只能由字母、数字、下划线、短横线组成。
```

这不是为了追求完美订单号规则，而是为了防止明显自然语言混进订单号字段。

如果以后 Java 业务系统规定订单号必须是：

```text
ORD-2026-000001
```

那就应该把 pattern 改成更贴近真实业务的形式，并补对应测试。

### 6. 为什么空值表达要归一化

模型可能用不同方式表达“没有订单号”：

```text
null
"null"
"None"
"未提供"
"未知"
""
"   "
```

业务代码不应该到处判断这些变体。

业务代码应该只判断：

```python
fields["order_id"] is None
```

所以本节把这些空值表达统一成 `None`。

这叫归一化。

归一化的好处：

- 后续业务判断更简单。
- 测试更稳定。
- state 里的数据更干净。
- 日志和评测更容易分析。

### 7. 为什么 description 和 user_request 要 strip

模型可能返回：

```json
{
  "description": "  商品破损  ",
  "user_request": "  投诉处理  "
}
```

前后空格对业务没有意义。

所以进入模型前先 strip。

如果 strip 后为空：

```json
{
  "description": "   "
}
```

就应该失败。

这就是：

```text
先归一化，再校验。
```

### 8. 当前错误码怎么分层

意图识别：

```text
TICKET_INTENT_LLM_EMPTY_RESPONSE
TICKET_INTENT_LLM_VALIDATION_FAILED
```

字段提取：

```text
TICKET_FIELD_LLM_EMPTY_RESPONSE
TICKET_FIELD_LLM_VALIDATION_FAILED
```

这个分层很有用。

如果日志里出现：

```text
TICKET_INTENT_LLM_VALIDATION_FAILED
```

说明模型在意图识别节点输出不合格。

如果出现：

```text
TICKET_FIELD_LLM_VALIDATION_FAILED
```

说明模型在字段提取节点输出不合格。

错误码定位到节点，后续排查会快很多。

### 9. 测试应该怎么覆盖模型坏输出

AI 项目里的模型输出测试，不是拿真实模型问几句就完事。

要主动构造坏输出。

本节新增测试文件：

```text
projects/ai-service/tests/test_ticket_agent_llm_output_validation.py
```

它主动构造：

- 多余字段。
- 空 reason。
- 多余流程字段。
- 非法订单号。
- 空值订单号。
- 字符串布尔值。
- 空 description。

这类测试的价值是：

```text
即使真实模型今天刚好没犯错，我们也要证明代码能挡住它将来可能犯的错。
```

### 10. 为什么这节没有大改 Agent 流程

因为 Pydantic 校验是边界层，不是流程层。

流程层已经在前几节搭好了：

```text
normalize
classify
retrieve
decide
extract
confirm
create
```

本节只加强：

```text
LLM 输出 -> 业务字段
```

这条边界。

工程上要避免把所有事情混在一节里：

```text
本节只收紧模型输出合同。
后续再学失败处理、双模式、prompt 版本管理。
```

## 六、本节代码讲解

### 1. 引入 ConfigDict 和 StrictBool

代码：

```python
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    ValidationError,
    field_validator,
)
```

新增两个东西：

```text
ConfigDict
StrictBool
```

`ConfigDict` 用来配置模型行为。

本节用它拒绝多余字段：

```python
model_config = ConfigDict(extra="forbid")
```

`StrictBool` 用来要求字段必须是真正布尔值。

本节用它约束：

```python
need_human_review: StrictBool
```

### 2. 意图识别输出拒绝多余字段

代码：

```python
class LLMTicketIntentClassification(BaseModel):
    model_config = ConfigDict(extra="forbid")
```

现在模型输出：

```json
{
  "intent": "ticket_request",
  "reason": "用户要求人工处理。",
  "confidence": 0.91
}
```

会失败。

失败后会被包装成：

```text
TICKET_INTENT_LLM_VALIDATION_FAILED
```

### 3. 字段提取输出拒绝多余字段

代码：

```python
class LLMTicketFields(BaseModel):
    model_config = ConfigDict(extra="forbid")
```

现在模型输出：

```json
{
  "should_create_ticket": true
}
```

会失败。

这正好呼应第 14 节讲过的边界：

```text
模型不决定流程。
```

### 4. 订单号格式校验

代码：

```python
order_id: str | None = Field(
    default=None,
    min_length=1,
    max_length=64,
    pattern=r"^[A-Za-z0-9_-]+$",
)
```

这让订单号字段保持干净。

合法例子：

```text
A2001
1001
ORDER_1001
ORDER-1001
```

非法例子：

```text
我猜是 A2001
订单号可能是 A2001
A2001，请帮我看一下
```

注意：这不是完整订单业务规则，只是第一层基础格式门槛。

### 5. 订单号空值归一化

代码：

```python
if normalized.casefold() in {"", "null", "none", "n/a", "na"}:
    return None
if normalized in {"无", "没有", "未提供", "未知"}:
    return None
```

作用：

```text
把模型输出的“没有订单号”表达统一成 None
```

这样后续：

```python
find_missing_ticket_fields(fields)
```

不用理解 `"未提供"`、`"未知"`、`"null"` 这些变体，只需要判断 `None`。

### 6. 严格布尔值

代码：

```python
need_human_review: StrictBool = Field(...)
```

允许：

```json
true
false
```

不允许：

```json
"true"
"false"
"yes"
1
0
```

为什么要严格？

因为模型输出要尽量接近业务合同，而不是靠后端不断猜测模型想表达什么。

### 7. 新增测试文件

文件：

```text
projects/ai-service/tests/test_ticket_agent_llm_output_validation.py
```

这个测试文件不测真实模型质量。

它测试：

```text
如果模型乱输出，我们能不能挡住。
```

这是 AI 工程里非常重要的一类测试。

### 8. schema 也会反映约束

因为 Pydantic 模型加了：

```python
model_config = ConfigDict(extra="forbid")
```

生成的 JSON Schema 里会出现类似：

```json
{
  "additionalProperties": false
}
```

这有两个价值：

1. prompt 里给模型看的 schema 更严格。
2. 后端实际校验也更严格。

这减少了“提示词里说一套，后端验收另一套”的风险。

## 七、本节测试讲解

### 1. schema 拒绝多余字段测试

测试：

```text
test_intent_output_json_schema_forbids_extra_properties
test_field_output_json_schema_forbids_extra_properties_and_limits_order_id
```

它验证：

```text
additionalProperties = false
```

以及订单号 schema 里有 pattern。

这不是测 Pydantic 官方能力，而是测我们自己的输出合同确实变严了。

### 2. 意图识别多余字段测试

测试输入：

```json
{
  "intent": "ticket_request",
  "reason": "用户要求人工处理。",
  "confidence": 0.91
}
```

预期：

```text
TICKET_INTENT_LLM_VALIDATION_FAILED
```

说明多余字段被挡住。

### 3. 空 reason 测试

测试输入：

```json
{
  "intent": "ticket_request",
  "reason": "   "
}
```

流程：

```text
field_validator 先 strip
-> reason 变成 ""
-> Field(min_length=1) 拒绝
```

这说明：

```text
空白字符串不能伪装成有效原因。
```

### 4. should_create_ticket 测试

测试输入：

```json
{
  "issue_type": "complaint",
  "order_id": "A2001",
  "description": "商品破损",
  "user_request": "投诉处理",
  "urgency": "high",
  "need_human_review": true,
  "should_create_ticket": true
}
```

预期失败。

这验证了第 14 节的原则：

```text
字段提取模型不能决定是否创建工单。
```

### 5. 非法订单号测试

测试输入：

```json
{
  "order_id": "我猜是 A2001"
}
```

预期失败。

因为它不符合：

```text
^[A-Za-z0-9_-]+$
```

这能挡住模型把解释性文本塞进订单号字段。

### 6. 空值订单号归一化测试

测试输入包括：

```text
""
"  "
"null"
"None"
"未提供"
"未知"
```

预期：

```python
fields["order_id"] is None
```

这说明我们不是机械地拒绝所有非标准表达，而是区分：

```text
明确无值表达 -> 归一成 None
自然语言猜测 -> 拒绝
```

### 7. 字符串布尔值测试

测试输入：

```json
{
  "need_human_review": "true"
}
```

预期失败。

这说明：

```text
JSON bool 必须是 true/false，不是字符串。
```

### 8. 空 description 测试

测试输入：

```json
{
  "description": "   "
}
```

预期失败。

因为 strip 后为空，不满足 `min_length=1`。

## 八、本节运行结果

本节先运行了相关测试：

```powershell
uv run pytest -q tests/test_ticket_agent_llm_output_validation.py tests/test_ticket_agent_llm_fields.py tests/test_ticket_agent_llm_intent.py
```

结果：

```text
30 passed
```

这说明：

- 第 15 节新增校验测试通过。
- 第 13 节真实 LLM 意图识别 fake 测试仍然通过。
- 第 14 节真实 LLM 字段提取 fake 测试仍然通过。

## 九、本节和第 14 节的关系

第 14 节重点是：

```text
把字段提取接入真实 LLM
```

第 15 节重点是：

```text
把真实 LLM 输出验收变严格
```

可以这样理解：

```text
第 14 节：模型可以参与工作
第 15 节：模型必须遵守合同
```

如果只做第 14 节，不做第 15 节，系统就会有风险：

```text
模型能进来，但边界不够硬。
```

第 15 节把这个边界补上了。

## 十、常见误区

### 误区 1：prompt 写清楚就不用校验

不对。

prompt 是软约束。

Pydantic 是硬验收。

模型可能不遵守 prompt，但只要 Pydantic 不通过，业务流程就不能继续。

### 误区 2：多余字段忽略掉就行

学习阶段和生产化早期，不建议这样做。

因为多余字段可能暴露模型越界倾向。

如果它多输出了：

```text
should_create_ticket
```

你不应该悄悄忽略，而应该让测试和日志告诉你：

```text
模型没有遵守输出合同。
```

### 误区 3：校验越严格越好

也不完全对。

校验要服务业务。

太松会放进脏数据。

太严会拒绝合理输入。

本节做的是基础且必要的严格：

- 拒绝多余字段。
- 拒绝非法枚举。
- 拒绝空关键字段。
- 拒绝订单号自然语言。
- 拒绝字符串布尔值。

这些都是模型输出进入业务系统前合理的门槛。

### 误区 4：Pydantic 校验通过就一定业务正确

也不对。

Pydantic 只能证明：

```text
结构、类型、格式基本符合合同。
```

它不能证明：

```text
模型语义判断一定正确。
```

例如模型把物流问题误提成投诉，只要 `complaint` 是合法枚举，Pydantic 可能会通过。

这种质量问题要靠：

- eval dataset。
- bad case 分析。
- 人工 review。
- 真实线上反馈。

所以 Pydantic 是必要条件，不是充分条件。

## 十一、你应该掌握的表达方式

如果别人问你“为什么模型已经返回 JSON 了还要 Pydantic”，你可以这样回答：

> JSON 只说明格式能解析，不代表业务字段合法。模型可能输出非法枚举、多余字段、空字符串、错误类型，甚至输出 should_create_ticket 这种流程控制字段。我们用 Pydantic 把模型输出当成不可信输入做验收，只有通过类型、枚举、长度、格式和额外字段检查的数据，才允许进入 Agent state 和后续业务流程。

如果别人问你“extra='forbid' 有什么价值”，你可以回答：

> 它能拒绝模型多输出的字段。这样模型不能偷偷塞入 confidence、route、should_create_ticket 等合同外字段。输出 schema 会更窄，测试也能更早发现模型没有遵守约定。

如果别人问你“Pydantic 校验通过是不是就代表模型判断一定对”，你可以回答：

> 不是。Pydantic 只保证结构和基础约束正确，不保证语义判断一定正确。语义质量还要靠 eval、bad case 分析和真实反馈。Pydantic 负责守住业务入口，eval 负责衡量模型效果。

## 十二、本节代码地图

核心代码：

```text
projects/ai-service/app/agents/ticket_agent.py
```

本节重点对象：

```text
LLMTicketIntentClassification
LLMTicketFields
parse_ticket_intent_classification_json()
parse_ticket_field_extraction_json()
get_ticket_intent_classification_json_schema()
get_ticket_field_extraction_json_schema()
```

新增测试：

```text
projects/ai-service/tests/test_ticket_agent_llm_output_validation.py
```

相关旧测试：

```text
projects/ai-service/tests/test_ticket_agent_llm_intent.py
projects/ai-service/tests/test_ticket_agent_llm_fields.py
```

## 十三、本节练习

### 练习 1：判断 JSON 是否能通过校验

题目：

下面这个意图识别输出能通过吗？

```json
{
  "intent": "ticket_request",
  "reason": "用户要求人工处理。",
  "confidence": 0.88
}
```

参考答案：

不能通过。

原因：

`LLMTicketIntentClassification` 使用了：

```python
model_config = ConfigDict(extra="forbid")
```

`confidence` 是多余字段，不在模型定义里，所以会被拒绝。

### 练习 2：判断订单号是否合法

题目：

下面这个字段提取输出里的 `order_id` 能通过吗？

```json
{
  "order_id": "我猜是 A2001"
}
```

参考答案：

不能通过。

原因：

订单号字段要求符合：

```text
^[A-Za-z0-9_-]+$
```

`"我猜是 A2001"` 包含中文、空格和自然语言解释，不是纯订单号。

### 练习 3：判断空值归一化

题目：

模型返回：

```json
{
  "order_id": "未提供"
}
```

后端应该把它当成字符串 `"未提供"` 还是 `None`？

参考答案：

应该归一化成 `None`。

原因：

`"未提供"` 表示用户没有给订单号，不是订单号本身。后续业务只需要判断：

```python
fields["order_id"] is None
```

### 练习 4：判断布尔值是否合法

题目：

下面这个字段能通过吗？

```json
{
  "need_human_review": "true"
}
```

参考答案：

不能通过。

原因：

当前使用的是：

```python
StrictBool
```

所以只能接受 JSON 里的真正布尔值：

```json
true
```

不能接受字符串：

```json
"true"
```

### 练习 5：解释 Pydantic 和 eval 的区别

题目：

Pydantic 校验和 Agent eval 分别解决什么问题？

参考答案：

Pydantic 校验解决的是：

```text
模型输出结构、类型、格式、枚举、字段边界是否符合业务合同。
```

Agent eval 解决的是：

```text
模型和 Agent 整体行为质量是否符合预期，例如意图是否判断对、字段语义是否提取对、路由是否走对。
```

Pydantic 是入口验收，eval 是质量评估。

## 十四、自测题

### 自测 1：为什么模型输出要当成不可信输入？

参考答案：

因为模型输出受用户输入、prompt、模型版本、提供商兼容程度和随机性影响，不是确定性业务代码生成的数据。它可能格式错、字段错、枚举错、多输出字段或受 prompt injection 干扰，所以必须先校验。

### 自测 2：JSON 解析成功说明什么？不说明什么？

参考答案：

JSON 解析成功只说明字符串符合 JSON 格式。

它不说明字段类型正确、枚举合法、业务含义正确、没有多余字段，也不说明可以进入业务流程。

### 自测 3：`ConfigDict(extra="forbid")` 的作用是什么？

参考答案：

它让 Pydantic 拒绝模型定义之外的多余字段。这样模型不能多输出 `confidence`、`should_create_ticket`、`route` 等合同外字段。

### 自测 4：为什么 `order_id` 要加 pattern？

参考答案：

因为订单号是业务系统关联订单的关键字段，不能包含自然语言解释或猜测。pattern 能保证订单号只包含允许字符，防止 `"我猜是 A2001"` 这类内容进入业务字段。

### 自测 5：`field_validator(mode="before")` 在本节有什么作用？

参考答案：

它在 Pydantic 做类型和字段约束前先处理值。本节用它去掉字符串两边空白，把 `"null"`、`"未提供"`、`"未知"` 这类无订单号表达归一化成 `None`。

### 自测 6：`StrictBool` 比普通 `bool` 严格在哪里？

参考答案：

`StrictBool` 要求输入必须是真正布尔值，不能把字符串 `"true"`、`"false"` 或数字 `1/0` 宽松转换成布尔值。

### 自测 7：Pydantic 校验通过是否代表模型语义一定正确？

参考答案：

不代表。Pydantic 只能保证结构和基础约束符合合同，不能保证模型语义判断一定正确。语义质量要靠 eval dataset、bad case 分析和真实反馈继续评估。

### 自测 8：模型输出校验失败后为什么不能继续创建工单？

参考答案：

因为字段可能缺失、类型错误、枚举非法或包含多余流程字段。继续创建工单会把不可靠数据写入业务系统，造成错误关联、错误分类或越权流程。所以校验失败必须阻断后续业务流程。

## 十五、本节小结

本节把第 13、14 节的真实 LLM 节点继续向生产化推进了一步。

我们完成了：

```text
LLM 输出模型 extra="forbid"
订单号格式校验
订单号空值归一化
严格布尔值校验
空 reason / description 校验
模型坏输出测试
```

你应该记住这条主线：

```text
模型负责生成候选结构化输出。
Pydantic 负责验收输出合同。
业务代码负责流程控制和写操作安全。
eval 负责评估整体质量。
```

这四者不能混在一起。

## 十六、参考资料

- [Pydantic Models](https://pydantic.dev/docs/validation/latest/concepts/models/)：理解模型校验、`BaseModel` 和 `model_validate_json()`。
- [Pydantic Configuration](https://pydantic.dev/docs/validation/latest/concepts/config/)：理解 `ConfigDict` 以及模型行为配置。
- [Pydantic Fields](https://pydantic.dev/docs/validation/latest/concepts/fields/)：理解 `Field()`、长度、默认值、pattern 等字段约束。
- [Pydantic Validators](https://pydantic.dev/docs/validation/latest/concepts/validators/)：理解 `field_validator` 和 `mode="before"`。
- [Pydantic JSON](https://pydantic.dev/docs/validation/latest/concepts/json/)：理解 `model_validate_json()` 对 JSON 输入的校验。
- [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)：理解结构化输出和 JSON Schema 的边界。
