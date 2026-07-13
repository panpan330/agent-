# 阶段 3 第 21 节：LangChain 结构化输出

> 本节结论：LangChain 结构化输出是让 ChatModel 按指定 schema 返回稳定数据的一种封装。我们使用 `with_structured_output(TicketExtraction)` 把“工单字段抽取”从手写 JSON Mode + 手动解析，改成 LangChain 模型封装 + Pydantic 返回对象。本节仍然只做字段提取，不创建工单、不执行工具、不进入 Agent。

## 生成笔记前的教学复核

本节必须满足这些教学要求：

```text
1. 先复习结构化输出是什么，再讲 LangChain 结构化输出。
2. 讲清 JSON Mode、JSON Schema、Pydantic、with_structured_output 的关系。
3. 讲清本节用的是 ChatModel.with_structured_output()，不是 Agent response_format。
4. 讲清为什么本节新增 /langchain-extract-ticket，而不是替换 /extract-ticket。
5. 讲清结构化输出适合提取字段，但不等于执行业务动作。
6. 讲清为什么当前项目选择 method="json_mode"，以及它和 json_schema 的取舍。
7. 新增代码要讲清服务层、消息构造、校验和路由边界。
8. 测试只讲关键意图，不逐行展开。
```

## 本节一句话定位

第 21 节是在 LangChain ChatModel 和 Tool 基础之后，学习如何用 LangChain 的 `with_structured_output()` 让模型直接返回经过 Pydantic 校验的结构化数据。

## 本节解决的真实问题

阶段 2 我们已经写过一个结构化输出接口：

```text
POST /extract-ticket
```

它的底层流程是：

```text
构造 system/user prompt
-> 调 OpenAI-compatible SDK
-> response_format={"type":"json_object"}
-> 提取 choices[0].message.content
-> 手动 model_validate_json()
-> 返回 TicketExtraction
```

现在我们已经引入 LangChain，于是要回答：

```text
LangChain 能不能帮我们少写一些结构化输出解析代码？
它和我们已有的 JSON Mode + Pydantic 有什么区别？
它返回的到底是字符串、dict，还是 Pydantic 对象？
用了它以后，后端业务边界还需不需要保留？
```

本节新增一个并行学习接口：

```text
POST /langchain-extract-ticket
```

对比关系是：

```text
/extract-ticket
-> 原生 OpenAI-compatible JSON Mode + 手动 Pydantic 解析

/langchain-extract-ticket
-> LangChain with_structured_output() + Pydantic schema
```

## 本节新增能力

学完后你应该能做到：

- 能解释 LangChain 结构化输出是什么；
- 能说清 `with_structured_output()` 的作用；
- 能区分 JSON Mode、JSON Schema、Pydantic schema；
- 能解释为什么 `TicketExtraction` 可以直接作为结构化输出 schema；
- 能看懂 `/extract-ticket` 和 `/langchain-extract-ticket` 的区别；
- 能解释 `method="json_mode"` 和 `method="json_schema"` 的基本取舍；
- 能说明结构化输出不能直接替代业务校验和用户确认；
- 能用 fake model 测试 LangChain 结构化输出。

## 和上一节的区别

第 20 节学的是：

```text
怎么把后端函数包装成 LangChain Tool。
```

第 21 节学的是：

```text
怎么让 ChatModel 输出符合 schema 的结构化数据。
```

简单说：

```text
第 20 节：外部能力怎么描述给模型
第 21 节：模型结果怎么变成稳定数据
```

## 基础知识铺垫

### 1. 什么是结构化输出

结构化输出就是让模型不要只返回自然语言，而是返回程序更容易处理的数据结构。

普通自然语言回答可能是：

```text
用户想投诉订单 A1001 没有发货，情况比较紧急，建议人工介入。
```

结构化输出希望拿到：

```json
{
  "intent": "complaint",
  "order_id": "A1001",
  "summary": "用户投诉订单没有发货",
  "urgency": "high",
  "need_human_review": true
}
```

对后端来说，第二种更有价值。

因为程序可以直接判断：

```text
intent 是什么
order_id 有没有
urgency 是不是 high
是否需要人工审核
```

### 2. 为什么 AI 应用需要结构化输出

真实 AI 应用不是只把模型回答展示给用户。

很多时候后端需要拿模型结果继续处理：

```text
分类
抽取字段
判断风险
路由到不同流程
生成待确认计划
写入数据库
调用业务系统
```

如果模型只返回一段自然语言，程序很难稳定解析。

结构化输出就是为了解决：

```text
模型输出不稳定，程序不好继续处理
```

### 3. JSON Mode 是什么

JSON Mode 是服务商提供的一种模型输出约束方式。

它通常表示：

```text
模型必须返回合法 JSON
```

但 JSON Mode 不一定保证：

```text
字段一定完整
枚举值一定合法
类型一定正确
没有多余字段
```

所以我们阶段 2 才会继续用 Pydantic 校验。

### 4. JSON Schema 是什么

JSON Schema 是描述 JSON 结构的标准格式。

它可以描述：

```text
字段名
字段类型
哪些字段必填
字符串长度
枚举值
对象结构
数组结构
是否允许多余字段
```

例如 `TicketExtraction` 可以生成 JSON Schema。

模型看到 schema 后，更容易按指定结构输出。

### 5. Pydantic 在结构化输出里的作用

Pydantic 至少有三个作用。

第一，定义结构：

```python
class TicketExtraction(BaseModel):
    intent: TicketIntent
    order_id: str | None
    summary: str
    urgency: TicketUrgency
    need_human_review: bool
```

第二，生成 schema：

```python
TicketExtraction.model_json_schema()
```

第三，运行时校验：

```python
TicketExtraction.model_validate(...)
```

所以它是结构化输出里非常关键的后端边界。

### 6. 什么是 LangChain with_structured_output()

`with_structured_output()` 是 ChatModel 上的方法。

它的作用是：

```text
基于一个 schema 创建一个“结构化输出版本”的模型调用对象。
```

例如：

```python
structured_model = model.with_structured_output(TicketExtraction)
result = structured_model.invoke(messages)
```

如果使用 Pydantic schema，理想情况下 `result` 就是：

```text
TicketExtraction 实例
```

这比手动解析 JSON 字符串更接近我们想要的后端对象。

### 7. with_structured_output() 和 Agent response_format 的区别

LangChain 有两个层次的结构化输出。

第一种是模型层：

```text
ChatModel.with_structured_output(...)
```

它用于直接调用模型，不涉及 Agent。

第二种是 Agent 层：

```text
create_agent(..., response_format=...)
```

它用于 Agent 最终状态里的结构化响应。

本节只学第一种。

原因是：

```text
我们还没有把当前项目改成 LangChain Agent
现在只需要理解 ChatModel 层的结构化输出
```

### 8. method="json_schema"、"function_calling"、"json_mode" 是什么

LangChain 的 `with_structured_output()` 支持不同方法。

常见有：

```text
json_schema
function_calling
json_mode
```

大致理解：

```text
json_schema：使用服务商原生结构化输出能力，约束通常更强
function_calling：用工具调用形式让模型输出符合 schema 的参数
json_mode：要求模型输出 JSON，schema 需要通过 prompt 说明
```

官方文档也说明，Pydantic 模型提供最丰富的字段校验能力；但具体 method 支持情况要看模型和服务商。

### 9. 为什么本项目本节使用 method="json_mode"

我们当前用的是 OpenAI-compatible 模型接口，而且阶段 2 已经验证过 JSON Mode 思路。

所以本节选择：

```python
with_structured_output(TicketExtraction, method="json_mode")
```

这样和已有 `/extract-ticket` 的兼容路径更接近。

但要注意：

```text
json_mode 通常只保证 JSON 格式，不一定原生强制 schema
所以 prompt 里仍然要写清 schema
Pydantic 校验仍然必须保留
```

如果以后确认模型服务商稳定支持 JSON Schema，再考虑：

```python
method="json_schema"
```

它可能更强，但兼容模型不一定都支持。

### 10. 结构化输出不是业务事实

模型提取出：

```json
{
  "order_id": "A1001",
  "intent": "refund"
}
```

这只表示：

```text
模型认为用户提到了订单 A1001，并且意图可能是退款
```

它不表示：

```text
订单 A1001 一定存在
订单 A1001 一定属于当前用户
用户一定有权退款
系统应该立刻退款
```

结构化输出只是“理解用户话语”的结果。

真正业务事实仍然要查后端系统。

真正业务动作仍然要权限、确认、幂等和审计。

## 本节主题系统讲解

### 1. 旧结构化输出链路

已有 `/extract-ticket` 的链路是：

```text
用户消息
-> build_ticket_extraction_messages()
-> OpenAI-compatible SDK
-> response_format={"type":"json_object"}
-> 模型返回 JSON 字符串
-> parse_ticket_extraction_json()
-> TicketExtraction
-> StructuredOutputResponse
```

它的特点是：

```text
底层非常透明
自己控制 prompt
自己解析 JSON
自己处理 Pydantic 错误
```

好处是容易理解。

缺点是代码相对手动。

### 2. 新 LangChain 结构化输出链路

新增 `/langchain-extract-ticket` 的链路是：

```text
用户消息
-> build_langchain_ticket_extraction_messages()
-> ChatOpenAI
-> with_structured_output(TicketExtraction, method="json_mode")
-> structured_model.invoke(messages)
-> TicketExtraction
-> StructuredOutputResponse
```

这里的核心变化是：

```text
把“模型输出按 TicketExtraction 解析”交给 LangChain 结构化输出封装
```

但 API 边界没有变：

```text
请求仍然是 StructuredOutputRequest
响应仍然是 StructuredOutputResponse
```

### 3. 为什么不直接替换 /extract-ticket

原因和前几节一样。

第一，学习上需要对比。

```text
/extract-ticket
-> 看懂原生 JSON Mode + Pydantic

/langchain-extract-ticket
-> 看懂 LangChain with_structured_output()
```

第二，工程上要降低风险。

直接替换已有接口会扩大影响面。

第三，兼容模型要实际验证。

`with_structured_output()` 在不同服务商和 method 下行为可能不完全一样。

先并行更稳。

### 4. 为什么 prompt 里仍然带 JSON Schema

虽然我们调用了：

```python
with_structured_output(TicketExtraction, method="json_mode")
```

但 `json_mode` 的特点是：

```text
更偏保证 JSON 格式
schema 约束还需要 prompt 说明
```

所以我们仍然在 HumanMessage 里放：

```text
JSON Schema: ...
用户消息: ...
```

这不是重复，而是为了兼容当前模型调用方式。

### 5. 为什么返回后还要 validate

理想情况下，LangChain 已经返回 `TicketExtraction`。

但工程代码最好兼容：

```text
返回 Pydantic 对象
返回 dict
返回异常
```

所以本节写了：

```python
validate_langchain_ticket_extraction(raw_result)
```

它的作用是：

```text
如果已经是 TicketExtraction，直接返回
如果是 dict，再用 TicketExtraction.model_validate()
如果不符合 schema，转成项目统一 AppException
```

这体现了一个原则：

```text
框架返回值也要守项目边界
```

### 6. 为什么结构化输出适合工单字段提取

工单字段提取的目标是：

```text
从自然语言中抽取 intent、order_id、summary、urgency、need_human_review
```

这非常适合结构化输出。

因为它不是直接执行业务动作，而是生成一个中间数据对象。

后续可以基于这个对象：

```text
判断是否支持该意图
判断是否需要人工审核
创建确认计划
调用 Java 创建工单
```

但这些后续动作不能由结构化输出直接完成。

### 7. 为什么测试仍然 fake model

本节测试没有真实调用模型。

而是 fake：

```text
base model.with_structured_output(...)
structured_model.invoke(...)
```

这样测试能验证：

```text
with_structured_output 是否使用 TicketExtraction
method 是否是 json_mode
messages 是否包含 JSON Schema
返回对象是否被校验
异常是否映射成项目错误
```

不会依赖网络、模型余额、服务商状态。

## 最小心智模型

本节最小链路是：

```text
ChatModel
-> with_structured_output(TicketExtraction)
-> structured_model.invoke(messages)
-> TicketExtraction
-> 后端继续校验和业务判断
```

一句话记忆：

```text
with_structured_output() 是把“模型自然语言输出”收窄成“符合 schema 的数据对象”。
```

## 当前项目如何落地

本节新增和修改了这些文件：

```text
projects/ai-service/app/services/langchain_structured_output_service.py
projects/ai-service/app/routers/chat.py
projects/ai-service/tests/test_langchain_structured_output_service.py
projects/ai-service/tests/test_chat_api.py
notes/tool-calling-stage3-21-langchain-structured-output.md
README.md
docs/learning-progress.md
docs/learning-resources.md
projects/ai-service/README.md
```

新增接口：

```text
POST /langchain-extract-ticket
```

新增服务：

```text
LangChainStructuredOutputService
```

它负责：

```text
构造 LangChain messages
调用 model.with_structured_output(TicketExtraction, method="json_mode")
调用 structured_model.invoke(messages)
校验返回值
记录日志
映射错误
```

## 关键代码讲解

### 1. build_langchain_ticket_extraction_messages()

它构造的是 LangChain message object：

```python
[
    SystemMessage(content=TICKET_EXTRACTION_SYSTEM_PROMPT),
    HumanMessage(content="请把下面的用户消息抽取成结构化工单字段...")
]
```

和旧版不同：

```text
旧版是 dict：{"role": "system", "content": "..."}
新版是 LangChain message：SystemMessage(...)
```

但语义一样。

### 2. _get_structured_model()

核心代码：

```python
self._structured_model = self._get_model().with_structured_output(
    TicketExtraction,
    method="json_mode",
)
```

它表示：

```text
基于当前 ChatModel 创建一个按 TicketExtraction 输出的结构化模型调用对象。
```

这里的 `TicketExtraction` 不是普通注释，而是结构化输出 schema。

### 3. extract_ticket()

核心流程：

```python
messages = build_langchain_ticket_extraction_messages(user_message)
raw_result = self._get_structured_model().invoke(messages)
result = validate_langchain_ticket_extraction(raw_result)
```

这和旧版对比很清楚：

```text
旧版：模型返回 JSON 字符串，然后我们手动 parse
新版：LangChain structured model 返回结构化对象或 dict，然后我们做最终校验
```

### 4. validate_langchain_ticket_extraction()

它处理两种情况：

```text
已经是 TicketExtraction -> 直接返回
是 dict 或其他对象 -> 尝试 TicketExtraction.model_validate()
```

如果失败，统一转成：

```text
STRUCTURED_OUTPUT_VALIDATION_FAILED
```

这保证接口错误格式和旧版结构化输出保持一致。

### 5. /langchain-extract-ticket

路由很薄：

```python
extraction = langchain_structured_output_service.extract_ticket(request.message)
return StructuredOutputResponse(extraction=extraction)
```

这说明：

```text
路由只负责 HTTP
LangChain 结构化输出逻辑放在 service 层
```

## 重要测试说明

本节测试重点有四类。

第一，消息构造测试：

```text
确认 SystemMessage / HumanMessage 正确生成
确认 HumanMessage 中包含 JSON Schema
```

第二，结构化模型调用测试：

```text
确认调用 with_structured_output(TicketExtraction, method="json_mode")
确认 structured_model.invoke(messages) 被调用
```

第三，返回值校验测试：

```text
TicketExtraction 可以直接返回
dict 可以被 Pydantic 校验
无效 dict 会映射成 STRUCTURED_OUTPUT_VALIDATION_FAILED
```

第四，路由测试：

```text
/langchain-extract-ticket 成功返回结构化结果
无 API key 返回统一错误
缺少 message 返回 VALIDATION_ERROR
GET 请求返回 METHOD_NOT_ALLOWED
```

自动化测试不会真实调用模型。

## 常见误区

### 误区 1：结构化输出等于一定正确

不对。

结构化输出只能提高格式稳定性，不保证业务事实正确。

### 误区 2：Pydantic 校验通过就可以直接创建工单

不对。

Pydantic 校验只说明字段格式合规，不说明业务动作应该执行。

创建工单仍然需要：

```text
业务意图支持
确认计划
操作者绑定
幂等
Java API 调用
```

### 误区 3：with_structured_output() 一定使用服务商原生 JSON Schema

不一定。

具体取决于 method 和模型提供商支持情况。

本节显式使用：

```text
method="json_mode"
```

### 误区 4：用了 LangChain 就不用写 prompt

不对。

尤其在 `json_mode` 下，仍然需要告诉模型应该抽取哪些字段、字段含义是什么、枚举值有哪些。

### 误区 5：LangChain 结构化输出只能用于 Agent

不对。

本节就是直接在 ChatModel 上使用：

```text
model.with_structured_output(...)
```

没有 Agent。

### 误区 6：新接口应该立刻替换旧接口

不对。

并行保留更适合学习和验证。确认行为一致、兼容性稳定后，才考虑迁移。

## 手动验证方式

如果本机 `.env` 已经配置模型：

```text
LLM_API_KEY
LLM_MODEL
LLM_BASE_URL
```

启动服务：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run uvicorn app.main:app --reload
```

调用：

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/langchain-extract-ticket" `
  -ContentType "application/json" `
  -Body '{"message":"订单 A1001 一直不发货，我要投诉"}'
```

注意：

```text
这个手动请求会真实调用模型，可能产生费用。
自动化测试不会真实调用模型。
```

如果兼容模型不支持当前 LangChain structured output 方法，可能需要改 method 或回到原生 SDK 路径验证。

## 练习与参考答案

### 练习 1：解释 LangChain 结构化输出

题目：

用 3 句话解释 LangChain 结构化输出是什么。

参考答案：

```text
LangChain 结构化输出是让模型按照指定 schema 返回稳定数据的封装。使用 Pydantic schema 时，它可以返回经过校验的 Pydantic 对象。它适合分类、字段抽取和信息整理，但不等于执行业务动作。
```

### 练习 2：比较两个接口

题目：

比较 `/extract-ticket` 和 `/langchain-extract-ticket` 的区别。

参考答案：

```text
/extract-ticket 使用原生 OpenAI-compatible SDK，要求模型返回 JSON 字符串，然后项目手动用 Pydantic 解析。
/langchain-extract-ticket 使用 LangChain ChatModel.with_structured_output(TicketExtraction)，让 LangChain 帮助完成结构化输出封装。
两者都使用 TicketExtraction 作为最终结构，业务边界都不能跳过。
```

### 练习 3：解释 method 取舍

题目：

为什么本节使用 `method="json_mode"`？

参考答案：

```text
因为当前项目之前已经基于 OpenAI-compatible JSON Mode 做过结构化输出，json_mode 和现有兼容路径更接近。json_schema 可能更强，但依赖模型服务商原生支持，兼容模型需要实际验证。
```

### 练习 4：判断结构化输出能不能直接创建工单

题目：

模型输出：

```json
{
  "intent": "complaint",
  "order_id": "A1001",
  "summary": "用户投诉未发货",
  "urgency": "high",
  "need_human_review": true
}
```

后端能不能直接创建工单？

参考答案：

```text
不能直接创建。这个结构化结果只是字段抽取结果。后端仍然要根据业务规则创建确认计划、绑定操作者和参数，用户确认后再调用 Java API 创建工单。
```

### 练习 5：解释为什么还要 validate

题目：

既然用了 `with_structured_output(TicketExtraction)`，为什么还写 `validate_langchain_ticket_extraction()`？

参考答案：

```text
因为工程代码要兼容框架返回 Pydantic 对象、dict 或异常等情况。最终进入项目接口响应前，仍然要用项目自己的 Pydantic 边界确认结果是合法的 TicketExtraction，并把错误映射成统一 AppException。
```

## 自测题与参考答案

### 自测 1

问题：`with_structured_output()` 是 ChatModel 的方法还是 Agent 的方法？

答案：

```text
是 ChatModel 的方法。本节没有使用 Agent。
```

### 自测 2

问题：Pydantic 在本节里起什么作用？

答案：

```text
定义结构化输出 schema，生成 JSON Schema，并在返回结果进入项目边界时做运行时校验。
```

### 自测 3

问题：JSON Mode 和 JSON Schema 的区别是什么？

答案：

```text
JSON Mode 更偏保证输出是合法 JSON；JSON Schema 更偏按字段结构、类型和约束输出。具体支持取决于模型服务商。
```

### 自测 4

问题：结构化输出结果里的 `order_id` 一定存在于业务系统吗？

答案：

```text
不一定。它只是模型从用户文本里抽取出的字段，必须再查业务系统确认。
```

### 自测 5

问题：为什么 `/langchain-extract-ticket` 不替换 `/extract-ticket`？

答案：

```text
为了学习对比、降低风险，并验证 LangChain 在当前兼容模型上的行为稳定性。
```

### 自测 6

问题：本节是否会调用工具？

答案：

```text
不会。本节只做结构化输出，不执行工具，也不进入 Agent。
```

### 自测 7

问题：结构化输出适合什么场景？

答案：

```text
适合分类、字段抽取、信息整理、风险标签、生成中间数据对象等场景。
```

### 自测 8

问题：如果模型返回结构不符合 TicketExtraction，接口应该返回什么类型错误？

答案：

```text
应该映射成 STRUCTURED_OUTPUT_VALIDATION_FAILED。
```

### 自测 9

问题：为什么测试里要 fake `with_structured_output()`？

答案：

```text
为了避免真实调用模型，同时验证 service 是否正确使用 TicketExtraction schema 和 json_mode 方法。
```

### 自测 10

问题：学完本节后，LangChain 在当前项目里已经覆盖了哪些基础抽象？

答案：

```text
ChatModel、Tool、Structured Output 三个基础抽象。
```

## 本节真正学会了什么

本节真正要学会的是：

```text
LangChain 结构化输出可以把模型输出收窄成 schema 数据。
with_structured_output(TicketExtraction) 是 ChatModel 层能力，不是 Agent。
Pydantic schema 仍然是结构化输出的核心边界。
json_mode 兼容性更接近我们已有实现，但 schema 约束不如原生 json_schema 强。
结构化输出适合提取字段，不等于执行业务操作。
后端确认、权限、幂等、业务事实校验仍然必须保留。
```

如果你能说清下面这句话，就说明本节达标：

```text
以前我们让模型返回 JSON 字符串再手动解析，现在用 LangChain with_structured_output() 让模型调用直接返回 TicketExtraction；但这个对象仍然只是字段抽取结果，不能绕过后端业务流程。
```

## 本节参考资料

- [LangChain Models - Structured output](https://docs.langchain.com/oss/python/langchain/models#structured-output)
- [LangChain Structured output](https://docs.langchain.com/oss/python/langchain/structured-output)
- [LangChain ChatOpenAI integration](https://docs.langchain.com/oss/python/integrations/chat/openai)

## 下一节学什么

下一节进入阶段 3 第 22 节：

```text
阶段 3 项目整理
```

阶段整理会复盘：

```text
原生 SDK 调用
Tool Calling 底层链路
Java mock 服务
确认机制
幂等
日志 trace_id
测试 fake/mock
LangChain ChatModel
LangChain Tool
LangChain 结构化输出
```

重点不是加很多新代码，而是把阶段 3 的知识体系串起来，确认你能讲清楚每一层的边界。

