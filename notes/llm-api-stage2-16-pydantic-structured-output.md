# 阶段 2 第 16 节：Pydantic 约束结构化输出

## 1. 这一节学什么

上一节我们学了结构化输出的概念：

```text
自然语言适合给人看
结构化输出适合给程序处理
JSON 只是格式
JSON Schema 是契约
Pydantic 可以做校验
模型输出不能直接信
```

这一节进入代码。

我们要实现一个练习接口：

```text
POST /extract-ticket
```

它的作用是：

```text
输入用户一句话
调用 OpenAI-compatible 模型
要求模型返回 JSON
用 Pydantic 校验模型返回的 JSON
返回稳定的结构化字段
```

这节的核心不是“让模型说得像 JSON”。

而是：

```text
模型输出 -> 解析 -> Pydantic 校验 -> 校验通过才给业务使用
```

## 2. 先看最终效果

用户请求：

```json
{
  "message": "订单 A1001 我想退款，东西有质量问题。"
}
```

服务端希望返回：

```json
{
  "extraction": {
    "intent": "refund",
    "order_id": "A1001",
    "summary": "用户因商品质量问题申请退款",
    "urgency": "normal",
    "need_human_review": false
  }
}
```

这几个字段的意思是：

| 字段 | 含义 |
| --- | --- |
| `intent` | 用户意图 |
| `order_id` | 用户提到的订单号，没有就用 `null` |
| `summary` | 一句话摘要 |
| `urgency` | 紧急程度 |
| `need_human_review` | 是否需要人工审核 |

这就是智能工单 Agent 的雏形。

现在它只是提取字段。

以后会继续接：

```text
查订单
判断权限
让用户确认
调用 Java API 创建工单
记录完整调用链路
```

## 3. 为什么先做工单字段抽取

因为你的长期项目里有：

```text
智能工单 Agent
```

工单 Agent 不是直接和用户聊天就结束。

它需要把用户自然语言变成后端可以处理的数据。

例如用户说：

```text
我昨天买的耳机左边没声音了，订单 A1001，想退款。
```

后端真正需要的是：

```json
{
  "intent": "refund",
  "order_id": "A1001",
  "summary": "耳机左边无声，用户申请退款",
  "urgency": "normal",
  "need_human_review": false
}
```

这就是信息抽取。

它是后面 Tool Calling、Agent、RAG 工单流程的基础。

## 4. 本节新增了哪些文件

这一节主要新增和修改：

```text
projects/ai-service/app/schemas/structured.py
projects/ai-service/app/services/structured_output_service.py
projects/ai-service/app/routers/chat.py
projects/ai-service/tests/test_structured_schema.py
projects/ai-service/tests/test_structured_output_service.py
projects/ai-service/tests/test_chat_api.py
```

分别负责：

| 文件 | 作用 |
| --- | --- |
| `schemas/structured.py` | 定义结构化输出的 Pydantic 模型 |
| `services/structured_output_service.py` | 调用模型、解析 JSON、校验输出 |
| `routers/chat.py` | 暴露 `/extract-ticket` 接口 |
| `test_structured_schema.py` | 测试 Pydantic 模型 |
| `test_structured_output_service.py` | 测试结构化输出服务 |
| `test_chat_api.py` | 测试 FastAPI 接口 |

## 5. 第一层：定义枚举

代码位置：

```text
projects/ai-service/app/schemas/structured.py
```

我们先定义用户意图：

```python
class TicketIntent(StrEnum):
    REFUND = "refund"
    ORDER_QUERY = "order_query"
    LOGISTICS = "logistics"
    COMPLAINT = "complaint"
    UNKNOWN = "unknown"
```

`StrEnum` 的意思是：

```text
它是枚举
它的值同时也是字符串
```

为什么要用枚举？

因为如果不限制，模型可能返回很多写法：

```text
退款
refund
return
apply_refund
用户想退钱
```

这些人能看懂。

程序不好稳定判断。

用枚举以后，程序只接受：

```text
refund
order_query
logistics
complaint
unknown
```

如果模型返回：

```json
{
  "intent": "cancel"
}
```

Pydantic 会校验失败。

这就是结构化输出的价值。

## 6. 第二层：定义请求模型

请求模型是用户传进来的数据：

```python
class StructuredOutputRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=4000,
        description="User message to extract a ticket from.",
    )
```

这表示：

```text
请求体必须有 message
message 必须是字符串
message 不能为空
message 最长 4000 字符
```

如果用户传：

```json
{}
```

会被 FastAPI + Pydantic 拦住，返回 `422`。

如果用户传：

```json
{
  "message": ""
}
```

也会被拦住。

注意：

```text
请求模型校验的是用户输入
结构化输出模型校验的是模型输出
```

两者都是 Pydantic，但位置不同。

## 7. 第三层：定义模型输出结构

核心模型是：

```python
class TicketExtraction(BaseModel):
    intent: TicketIntent
    order_id: str | None = Field(default=None, min_length=1, max_length=64)
    summary: str = Field(min_length=1, max_length=200)
    urgency: TicketUrgency = Field(default=TicketUrgency.NORMAL)
    need_human_review: bool = Field(default=False)
```

这就是我们要求模型输出的结构。

字段解释：

| 字段 | Python 类型 | JSON 示例 |
| --- | --- | --- |
| `intent` | `TicketIntent` | `"refund"` |
| `order_id` | `str \| None` | `"A1001"` 或 `null` |
| `summary` | `str` | `"用户申请退款"` |
| `urgency` | `TicketUrgency` | `"normal"` |
| `need_human_review` | `bool` | `true` 或 `false` |

这里最重要的是类型。

如果模型返回：

```json
{
  "need_human_review": "是"
}
```

这就不如：

```json
{
  "need_human_review": true
}
```

后者是标准布尔值，程序更容易处理。

## 8. `str | None` 是什么意思

这一行：

```python
order_id: str | None
```

表示：

```text
order_id 可以是字符串
也可以是 None
```

对应 JSON 里就是：

```text
字符串 或 null
```

为什么订单号可以为空？

因为用户可能没有说订单号：

```text
我想退款。
```

这时结构化输出应该是：

```json
{
  "order_id": null
}
```

而不是：

```json
{
  "order_id": ""
}
```

`null` 表示没有值。

空字符串表示有一个字符串，只是内容为空。

语义不一样。

## 9. 为什么要处理空字符串订单号

模型有时可能返回：

```json
{
  "order_id": ""
}
```

或者：

```json
{
  "order_id": "   "
}
```

为了让语义更干净，我们写了一个 Pydantic validator：

```python
@field_validator("order_id", mode="before")
@classmethod
def empty_order_id_to_none(cls, value: object) -> object:
    if isinstance(value, str):
        stripped_value = value.strip()
        return stripped_value or None
    return value
```

它做两件事：

```text
去掉订单号前后的空格
如果去掉空格后是空，就变成 None
```

例如：

```text
"  A1001  " -> "A1001"
"   " -> None
```

这是一个很小的细节，但很工程化。

因为后端系统更喜欢明确的空值，而不是一堆空字符串。

## 10. `Field()` 的作用

`Field()` 可以给字段加规则和说明。

例如：

```python
summary: str = Field(
    min_length=1,
    max_length=200,
    description="Short summary of the user issue.",
)
```

这表示：

```text
summary 必须是字符串
至少 1 个字符
最多 200 个字符
这个字段的说明是 Short summary of the user issue
```

`description` 不只是给人看的。

后面生成 JSON Schema 时，它也会进入 schema。

模型调用前，我们可以把 schema 放进 prompt，帮助模型理解字段含义。

## 11. 从 Pydantic 生成 JSON Schema

本节代码里有：

```python
def get_ticket_extraction_json_schema() -> dict[str, Any]:
    return TicketExtraction.model_json_schema()
```

`model_json_schema()` 是 Pydantic 提供的方法。

它会把 Pydantic 模型转成 JSON Schema。

也就是说：

```text
Pydantic 模型是 Python 里的结构定义
JSON Schema 是 JSON 世界里的结构定义
```

两者可以互相配合。

在结构化输出里，常见做法是：

```text
调用模型前：把 JSON Schema 给模型看
模型返回后：用 Pydantic 再验一遍
```

## 12. 为什么不是只靠 prompt

你可以在 prompt 里写：

```text
请只返回 JSON，字段必须有 intent、order_id、summary。
```

但模型仍然可能返回：

```text
好的，下面是 JSON：
{"intent": "refund"}
```

或者：

```json
{
  "intent": "退款",
  "order": "A1001"
}
```

这些都不可靠。

所以我们的策略是：

```text
prompt 负责引导
JSON mode 负责提高 JSON 合法性
Pydantic 负责最后验收
```

这三层合在一起，才更接近工程化结构化输出。

## 13. 本节为什么使用 JSON Mode

本项目当前用的是 OpenAI-compatible 调用方式。

阿里云百炼兼容接口的结构化输出文档里，JSON Mode 用法是：

```python
response_format={"type": "json_object"}
```

并且提示词里需要出现 JSON 关键词。

所以本节服务调用里写了：

```python
completion = self._get_client().chat.completions.create(
    model=self.settings.llm_model,
    messages=messages,
    response_format={"type": "json_object"},
)
```

注意：

```text
JSON Mode 主要帮助模型返回合法 JSON
它不等于后端校验
```

所以后面仍然要执行：

```python
TicketExtraction.model_validate_json(raw_reply)
```

## 14. OpenAI Structured Outputs 和本节代码的关系

OpenAI 官方 Structured Outputs 能力更进一步。

它的目标是让模型输出符合 JSON Schema。

官方 Python SDK 里也有把 Pydantic 模型作为结构化输出格式的用法。

但我们当前要兼容你的模型服务地址。

所以本节采用更通用的方案：

```text
OpenAI-compatible Chat Completions
+ JSON Mode
+ Pydantic 后端校验
```

这样更适合当前项目。

以后如果切到完整支持 Structured Outputs 的模型和接口，可以再升级调用方式。

## 15. messages 是怎么构建的

代码里有：

```python
def build_ticket_extraction_messages(user_message: str) -> list[dict[str, str]]:
    ...
```

它返回两条消息：

```text
system：告诉模型它是客服工单字段抽取器，只能返回 JSON
user：给出 JSON Schema 和真实用户消息
```

system prompt 里明确了：

```text
只能返回合法 JSON
不要 Markdown
不要解释文字
字段必须包含哪些
枚举值只能是什么
没有订单号用 null
什么时候需要人工审核
```

user message 里包含：

```text
JSON Schema
用户原始消息
```

这样模型既知道任务，也知道结构要求。

## 16. 为什么不要记录完整用户消息和模型原文

本节日志只记录：

```text
provider
model
elapsed_ms
intent
urgency
need_human_review
token usage
错误码
```

不记录：

```text
完整用户消息
完整模型输出
API key
完整 prompt
```

原因是用户消息里可能有：

```text
手机号
订单号
姓名
地址
投诉内容
```

日志是排查问题用的，不应该随便写入敏感内容。

这和前面模型调用日志一节是一致的。

## 17. 解析模型输出

模型返回后，先取第一条回复：

```python
raw_reply = extract_first_reply(completion)
```

然后进入：

```python
result = parse_ticket_extraction_json(raw_reply)
```

核心解析代码是：

```python
return TicketExtraction.model_validate_json(raw_json)
```

`model_validate_json()` 做两件事：

```text
先把 JSON 字符串解析成数据
再按 TicketExtraction 规则校验
```

如果 JSON 不合法，失败。

如果 JSON 合法但字段不对，也失败。

例如：

```json
{
  "intent": "cancel",
  "summary": "用户想取消订单"
}
```

这虽然是合法 JSON。

但 `intent` 不在允许枚举里，所以校验失败。

## 18. 校验失败怎么处理

本节定义了结构化输出校验失败错误：

```text
STRUCTURED_OUTPUT_VALIDATION_FAILED
```

对应 HTTP 状态码：

```text
502
```

为什么是 502？

因为这个错误不是用户请求格式错。

用户的请求可能没问题。

失败发生在：

```text
服务端调用外部模型
外部模型返回了不符合要求的内容
```

所以更像上游服务返回异常结果。

如果模型返回空内容，会返回：

```text
STRUCTURED_OUTPUT_EMPTY
```

## 19. 服务类做了什么

代码里新增了：

```python
class StructuredOutputService:
    ...
```

它负责：

```text
检查是否配置了 LLM_API_KEY
构建结构化输出 messages
调用 OpenAI-compatible 模型
启用 JSON Mode
提取模型第一条回复
用 Pydantic 校验 JSON
记录成功或失败日志
把模型 SDK 错误映射成 AppException
```

你可以把它理解成：

```text
结构化输出的业务服务层
```

router 不直接写模型调用细节。

router 只负责接 HTTP 请求和返回 HTTP 响应。

这就是前面学过的分层思想。

## 20. `/extract-ticket` 接口

代码位置：

```text
projects/ai-service/app/routers/chat.py
```

新增路由：

```python
@router.post("/extract-ticket", response_model=StructuredOutputResponse)
def extract_ticket(...):
    ...
```

调用链路是：

```text
POST /extract-ticket
-> app/routers/chat.py
-> StructuredOutputService.extract_ticket()
-> build_ticket_extraction_messages()
-> client.chat.completions.create(..., response_format={"type": "json_object"})
-> parse_ticket_extraction_json()
-> TicketExtraction.model_validate_json()
-> StructuredOutputResponse
```

这里 `response_model=StructuredOutputResponse` 很重要。

它表示：

```text
FastAPI 返回给客户端之前，也会按响应模型整理输出
```

也就是说：

```text
请求进来有模型校验
模型输出有 Pydantic 校验
响应出去也有 response_model 约束
```

## 21. 测试为什么不用真实模型

本节测试没有真实调用模型。

原因是：

```text
真实模型会花钱
真实模型有网络波动
真实模型输出不完全可控
自动化测试需要稳定
```

所以我们用 fake client 和 fake service。

测试重点不是模型聪不聪明。

测试重点是我们的代码逻辑是否稳定：

```text
是否传了 response_format
是否会解析合法 JSON
是否拒绝非法 JSON
是否拒绝枚举错误
是否在缺少 API key 时不调用模型
是否不会把用户消息和 key 写进日志
接口是否返回正确结构
```

## 22. Schema 测试测了什么

`test_structured_schema.py` 主要验证：

```text
StructuredOutputRequest 接受正常 message
空 message 会失败
TicketExtraction 接受合法枚举值
空白 order_id 会变成 None
非法 intent 会失败
缺少 summary 会失败
StructuredOutputResponse 能包住 extraction
model_json_schema() 里有预期字段
```

这类测试看起来简单。

但它能保护数据契约。

以后如果你改字段名、改必填项、改枚举值，测试会提醒你。

## 23. Service 测试测了什么

`test_structured_output_service.py` 主要验证：

```text
messages 里包含 JSON 和 JSON Schema
合法 JSON 能解析成 TicketExtraction
非法 JSON 会返回 STRUCTURED_OUTPUT_VALIDATION_FAILED
schema 不匹配也会失败
空内容会返回 STRUCTURED_OUTPUT_EMPTY
服务调用模型时带 response_format={"type":"json_object"}
缺少 API key 时不会调用模型
模型异常会映射成统一错误
成功日志不包含原始用户消息和 key
```

这说明我们的结构化输出不是只写了接口。

而是有可验证的工程行为。

## 24. API 测试测了什么

`test_chat_api.py` 增加了 `/extract-ticket` 的测试：

```text
正常请求返回结构化响应
缺少 API key 返回统一错误
缺少 message 返回校验错误
GET /extract-ticket 返回 405
```

这里通过 FastAPI 的：

```python
app.dependency_overrides
```

把真实服务替换成 fake service。

这样测试接口时不会真实调用模型。

这是 FastAPI 测试里很常见的隔离方法。

## 25. 自己怎么手动试

进入项目目录：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
```

启动服务：

```powershell
uv run uvicorn app.main:app --reload
```

打开接口文档：

```text
http://127.0.0.1:8000/docs
```

找到：

```text
POST /extract-ticket
```

请求示例：

```json
{
  "message": "订单 A1001 一直没有发货，我要投诉。"
}
```

注意：

```text
如果本机 .env 没有 LLM_API_KEY，会返回 LLM_API_KEY_MISSING
```

这是正常的。

因为真实接口需要模型 API key。

## 26. 本节容易混的点

### 1. JSON Mode 不等于 Pydantic 校验

JSON Mode 主要让模型更容易返回合法 JSON。

Pydantic 校验是后端确认数据能不能用。

两者不是一回事。

### 2. JSON 合法不等于业务可用

这个是合法 JSON：

```json
{
  "intent": "我想退款"
}
```

但它不符合我们的业务契约。

因为 `intent` 必须是：

```text
refund
order_query
logistics
complaint
unknown
```

### 3. Pydantic 不是模型能力

Pydantic 不会让模型变聪明。

它只是帮后端判断：

```text
模型返回的数据能不能进业务流程
```

### 4. 结构化输出不能跳过人工确认

即使模型提取到：

```json
{
  "intent": "refund",
  "order_id": "A1001"
}
```

也不能直接退款。

退款前仍然要：

```text
查订单
校验用户身份
检查退款规则
让用户或客服确认
```

## 27. 本节完成后你应该会什么

你应该能解释：

```text
为什么要定义 TicketExtraction
为什么 intent 和 urgency 用枚举
为什么 order_id 可以是 null
为什么要用 model_json_schema()
为什么模型返回 JSON 后还要 model_validate_json()
为什么 JSON Mode 不是最终保障
为什么测试里不用真实模型
```

你也应该能看懂这条链路：

```text
用户消息
-> LLM JSON 输出
-> Pydantic 校验
-> 后端稳定结构
```

## 28. 本节练习

### 练习 1

题目：

为什么 `intent` 字段要用枚举，而不是普通字符串？

参考答案：

普通字符串太自由，模型可能返回很多不同写法，例如 `退款`、`return_money`、`apply_refund`。

枚举可以把允许值限制在固定范围内，例如 `refund`、`order_query`、`logistics`、`complaint`、`unknown`，这样程序判断更稳定。

### 练习 2

题目：

`order_id: str | None` 表示什么意思？

参考答案：

表示 `order_id` 可以是字符串，也可以没有值。

在 JSON 中对应字符串或 `null`。如果用户没有提供订单号，应该返回 `null`，而不是乱编一个订单号。

### 练习 3

题目：

为什么本节要把空字符串订单号转成 `None`？

参考答案：

因为空字符串和没有值不是一回事。

订单号为空白时，语义上更接近“没有订单号”，所以统一转成 `None`，方便后续业务判断。

### 练习 4

题目：

`TicketExtraction.model_json_schema()` 的作用是什么？

参考答案：

它会把 Pydantic 模型转换成 JSON Schema 字典。

这个 schema 可以描述模型输出应该有哪些字段、字段类型是什么、哪些字段必填、枚举值有哪些。

### 练习 5

题目：

`TicketExtraction.model_validate_json(raw_json)` 做了哪两件事？

参考答案：

第一，解析 JSON 字符串。

第二，按 `TicketExtraction` 的字段、类型、枚举和长度约束进行校验。

### 练习 6

题目：

为什么用了 `response_format={"type": "json_object"}` 后仍然要 Pydantic 校验？

参考答案：

因为 JSON Mode 主要保证输出是合法 JSON，不一定保证字段名、字段类型、必填字段和枚举值都符合业务要求。

Pydantic 是后端最后的验收。

### 练习 7

题目：

为什么结构化输出失败返回 502，而不是 422？

参考答案：

422 通常表示用户请求参数校验失败。

结构化输出失败通常发生在服务端调用外部模型后，模型返回了不符合要求的结果，所以更像上游服务异常，返回 502 更合适。

### 练习 8

题目：

本节为什么不在测试中真实调用模型？

参考答案：

真实模型调用会产生费用、依赖网络、输出不完全稳定。

自动化测试应该稳定、快速、可重复，所以使用 fake client 和 fake service。

### 练习 9

题目：

为什么日志里不记录完整用户消息？

参考答案：

用户消息可能包含姓名、手机号、订单号、地址、投诉内容等敏感信息。

日志只应该记录排查问题需要的元信息，例如模型名、耗时、错误码、token 用量，不应该记录完整敏感内容。

### 练习 10

题目：

如果模型返回下面 JSON，Pydantic 会通过吗？

```json
{
  "intent": "cancel",
  "order_id": "A1001",
  "summary": "用户想取消订单",
  "urgency": "normal",
  "need_human_review": false
}
```

参考答案：

不会通过。

因为 `intent` 只能是 `refund`、`order_query`、`logistics`、`complaint`、`unknown`，`cancel` 不在枚举范围内。

## 29. 本节自测

### 自测 1

题目：

结构化输出的最终目标是让人看着舒服，还是让程序稳定处理？

参考答案：

让程序稳定处理。

### 自测 2

题目：

本节新增的接口路径是什么？

参考答案：

`POST /extract-ticket`。

### 自测 3

题目：

`TicketIntent` 和 `TicketUrgency` 为什么用 `StrEnum`？

参考答案：

因为它们既是枚举，又能以字符串值出现在 JSON 响应中，适合限制固定取值。

### 自测 4

题目：

如果用户没提供订单号，`order_id` 应该是什么？

参考答案：

应该是 `null`，对应 Python 里的 `None`。

### 自测 5

题目：

JSON Mode 的参数在本节代码里是什么？

参考答案：

`response_format={"type": "json_object"}`。

### 自测 6

题目：

Pydantic 的 `model_json_schema()` 用在调用模型前还是调用模型后？

参考答案：

主要用在调用模型前，用来生成 schema，帮助模型理解输出结构。

### 自测 7

题目：

Pydantic 的 `model_validate_json()` 用在调用模型前还是调用模型后？

参考答案：

用在调用模型后，用来解析和校验模型返回的 JSON。

### 自测 8

题目：

测试里为什么使用 fake client？

参考答案：

为了避免真实网络调用和费用，并让测试结果稳定可重复。

### 自测 9

题目：

结构化输出能不能代替订单权限校验？

参考答案：

不能。结构化输出只负责提取字段，权限和业务规则必须由后端系统校验。

### 自测 10

题目：

如果模型返回合法 JSON，但缺少 `summary`，能不能通过本节校验？

参考答案：

不能。`summary` 是必填字段，缺少它会触发 Pydantic 校验失败。

## 30. 本节小结

这一节完成了：

```text
定义结构化输出 Pydantic 模型
定义意图和紧急程度枚举
处理 order_id 空值语义
从 Pydantic 模型生成 JSON Schema
使用 OpenAI-compatible JSON Mode
解析模型返回 JSON
使用 Pydantic 校验模型输出
新增 /extract-ticket 接口
新增 schema、service、API 三层测试
```

最重要的一句话：

```text
模型返回的 JSON 不是最终结果，Pydantic 校验通过后的对象才是后端可以继续处理的数据。
```

下一节进入：

```text
测试模型调用：mock/fake LLM client
```

虽然我们已经用了一些 fake client，但下一节会专门把“如何测试模型调用”讲透。

## 31. 参考资料

- [OpenAI：Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [Pydantic：JSON](https://docs.pydantic.dev/latest/concepts/json/)
- [Pydantic：JSON Schema](https://docs.pydantic.dev/latest/concepts/json_schema/)
- [阿里云百炼：结构化输出](https://help.aliyun.com/zh/model-studio/qwen-structured-output)
- [FastAPI：Response Model](https://fastapi.tiangolo.com/tutorial/response-model/)
