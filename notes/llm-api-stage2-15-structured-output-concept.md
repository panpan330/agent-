# 阶段 2 第 15 节：结构化输出是什么

## 1. 这一节学什么

前面我们已经学了：

```text
普通 /chat
多轮 history
timeout
retry
rate limit
错误处理
模型调用日志
/stream-chat 流式输出
```

这一节开始学习另一个非常重要的能力：

```text
结构化输出
```

你要学会：

```text
自然语言输出是什么
结构化输出是什么
为什么业务系统不能只依赖一段自然语言
JSON 和结构化输出是什么关系
JSON Mode 是什么
Structured Outputs 是什么
JSON Schema 是什么
Pydantic 在结构化输出里做什么
为什么模型返回 JSON 后还要校验
结构化输出适合哪些业务场景
结构化输出有哪些坑
```

本节先讲概念。

下一节才用 Pydantic 写代码约束结构化输出。

## 2. 先用人话理解结构化输出

普通聊天回答像这样：

```text
用户想退款，订单号是 12345，原因是质量问题。
```

这段话人能看懂。

但程序不好稳定处理。

结构化输出希望模型返回：

```json
{
  "intent": "refund",
  "order_id": "12345",
  "reason": "质量问题"
}
```

这份数据程序可以直接读：

```text
intent 是 refund
order_id 是 12345
reason 是 质量问题
```

这就是结构化输出的核心：

```text
让模型输出机器更容易理解和处理的数据结构
```

## 3. 自然语言输出适合什么

自然语言适合给人看。

例如：

```text
FastAPI 是一个用 Python 编写的 Web 框架，适合快速构建 API。
```

这种回答适合：

```text
解释概念
聊天
总结
写文章
生成客服回复
给用户展示
```

自然语言的优点是：

```text
灵活
容易读
表达丰富
像人说话
```

但它不适合直接驱动业务流程。

## 4. 自然语言输出的问题

如果你要让程序根据模型输出继续做事，自然语言就麻烦了。

例如模型返回：

```text
这个用户应该是想退款，订单号看起来是 12345。
```

程序要怎么判断？

```text
意图字段在哪里？
订单号字段在哪里？
退款原因有没有？
置信度是多少？
是否需要人工确认？
```

如果让程序再去从这段话里用正则提取，就会很脆弱。

模型下次可能换一种说法：

```text
用户提出了退货退款请求，涉及订单 12345。
```

人看起来差不多。

程序可能就解析失败。

## 5. 结构化输出适合什么

结构化输出适合给程序处理。

例如：

```json
{
  "intent": "refund",
  "order_id": "12345",
  "need_human_review": false
}
```

程序可以稳定做判断：

```python
if result["intent"] == "refund":
    ...
```

结构化输出适合：

```text
意图识别
信息抽取
工单字段提取
表单自动填写
客服问题分类
文档元数据抽取
RAG 引用来源整理
工具调用前参数准备
评测结果打分
```

一句话：

```text
只要后端要继续处理模型结果，就应该优先考虑结构化输出
```

## 6. 结构化输出不是只要 JSON

很多初学者会以为：

```text
模型返回 JSON = 结构化输出
```

这个理解只对了一半。

JSON 是一种数据格式。

结构化输出更强调：

```text
字段稳定
类型稳定
枚举值稳定
必填字段稳定
后端可以校验
业务可以依赖
```

例如这个是 JSON：

```json
{
  "text": "用户想退款，订单号是 12345"
}
```

但它对业务帮助不大。

更好的结构化输出是：

```json
{
  "intent": "refund",
  "order_id": "12345",
  "reason": null,
  "confidence": 0.86
}
```

所以你要记住：

```text
JSON 是格式
结构化输出是稳定可用的数据契约
```

## 7. 什么是数据契约

数据契约就是双方约定好数据长什么样。

例如后端和前端约定：

```json
{
  "reply": "字符串"
}
```

前端就知道一定从 `reply` 里拿聊天回复。

结构化输出也是一种契约。

例如我们约定模型必须返回：

```json
{
  "intent": "refund | order_query | unknown",
  "order_id": "字符串或 null",
  "reason": "字符串或 null"
}
```

那后端就可以按这个结构写业务代码。

## 8. 没有契约会怎样

如果没有契约，模型可能今天返回：

```json
{
  "intent": "refund",
  "order_id": "12345"
}
```

明天返回：

```json
{
  "用户意图": "退款",
  "订单": 12345
}
```

后天返回：

```text
用户想退款，订单号 12345。
```

人都看得懂。

程序会崩。

所以结构化输出的目标不是让人看得懂，而是让程序稳定处理。

## 9. JSON 是什么

JSON 是一种轻量数据交换格式。

它常见的数据类型包括：

```text
object 对象
array 数组
string 字符串
number 数字
boolean 布尔值
null 空值
```

例如：

```json
{
  "intent": "refund",
  "order_id": "12345",
  "need_human_review": false,
  "confidence": 0.86,
  "tags": ["refund", "quality"],
  "extra": null
}
```

Python 里可以用：

```python
import json

data = json.loads(json_string)
```

把 JSON 字符串变成 Python 字典。

## 10. 只让模型“请返回 JSON”够不够

不够。

你可以在 prompt 里写：

```text
请用 JSON 返回。
```

模型通常会尽量照做。

但仍然可能出现：

```text
返回 Markdown 代码块
JSON 前后加解释文字
漏字段
字段名换了
类型错了
枚举值乱写
多返回不需要的字段
返回的 JSON 不合法
```

例如：

```text
当然可以，下面是 JSON：
```json
{"intent": "refund"}
```
```

这对人没问题。

但程序直接 `json.loads()` 可能失败。

## 11. JSON Mode 是什么

JSON Mode 通常表示：

```text
让模型输出合法 JSON
```

阿里云百炼 OpenAI 兼容文档里，结构化输出 JSON Mode 使用：

```python
response_format={"type": "json_object"}
```

同时提示词中需要包含 JSON 关键词。

这样可以让模型更倾向于返回标准 JSON 字符串。

但要注意：

```text
JSON Mode 主要保证输出是 JSON
不一定保证字段完全符合你的业务 schema
```

## 12. Structured Outputs 是什么

OpenAI 官方文档里，Structured Outputs 是比 JSON Mode 更强的一类能力。

它的目标是：

```text
让模型输出符合你提供的 JSON Schema
```

也就是说，它不只关心：

```text
是不是 JSON
```

还关心：

```text
有没有 required 字段
字段类型对不对
枚举值是否允许
结构是否符合 schema
```

OpenAI 文档明确区分：

```text
JSON Mode：保证有效 JSON
Structured Outputs：保证遵守 schema
```

能用 Structured Outputs 时，优先用它。

## 13. JSON Mode 和 Structured Outputs 的区别

可以这样理解：

| 能力 | 主要保证 | 例子 |
| --- | --- | --- |
| 普通 prompt | 尽量按你说的格式返回 | “请返回 JSON” |
| JSON Mode | 输出是合法 JSON | `{"type": "json_object"}` |
| Structured Outputs | 输出符合 JSON Schema | 字段、类型、必填、枚举都受约束 |

举例。

JSON Mode 可能返回：

```json
{
  "意图": "用户想退款"
}
```

这是合法 JSON。

但如果你的业务要求是：

```json
{
  "intent": "refund",
  "order_id": "12345"
}
```

那前面的结果仍然不合格。

Structured Outputs 的目标就是减少这类问题。

## 14. JSON Schema 是什么

JSON Schema 是用来描述 JSON 长什么样的规则。

例如你希望模型返回：

```json
{
  "intent": "refund",
  "order_id": "12345",
  "confidence": 0.86
}
```

对应 schema 大概可以写成：

```json
{
  "type": "object",
  "properties": {
    "intent": {
      "type": "string",
      "enum": ["refund", "order_query", "unknown"]
    },
    "order_id": {
      "type": ["string", "null"]
    },
    "confidence": {
      "type": "number"
    }
  },
  "required": ["intent", "order_id", "confidence"]
}
```

这个 schema 在说：

```text
整体必须是对象
intent 必须是字符串
intent 只能是三个值之一
order_id 可以是字符串或 null
confidence 必须是数字
三个字段都必须出现
```

## 15. schema 像什么

你可以把 schema 理解成：

```text
模型输出的说明书
模型输出的合同
模型输出的验收标准
```

没有 schema：

```text
你随便返回点能看懂的
```

有 schema：

```text
你必须按这个结构返回
字段名、类型、可选值都要符合要求
```

这就是工程化。

## 16. Pydantic 在这里做什么

Pydantic 是 Python 里常用的数据校验工具。

在 FastAPI 阶段 1，我们已经用过：

```python
class ChatRequest(BaseModel):
    message: str
```

它可以校验用户请求。

在结构化输出里，Pydantic 可以校验模型输出。

例如：

```python
class IntentResult(BaseModel):
    intent: str
    order_id: str | None
    confidence: float
```

模型返回 JSON 后，我们可以用 Pydantic 检查：

```text
字段有没有
类型对不对
数字是不是数字
null 是否允许
```

如果不符合，就不让它进入业务流程。

## 17. Pydantic 和 JSON Schema 的关系

Pydantic 模型可以生成 JSON Schema。

官方文档里的方法是：

```python
MyModel.model_json_schema()
```

这会返回一个可以 JSON 序列化的 schema 字典。

所以 Pydantic 可以做两件事：

```text
调用模型前：把 Pydantic 模型转成 JSON Schema，告诉模型输出什么结构
调用模型后：把模型返回结果解析成 Pydantic 对象，校验它是否真的符合结构
```

这就是下一节要学的重点。

## 18. 为什么模型返回 JSON 后还要校验

因为模型不是数据库。

即使你要求它返回 JSON，它也可能：

```text
漏字段
多字段
字段类型错
枚举值错
字符串里塞了多余解释
数字写成字符串
null 写成空字符串
```

如果不校验，错误数据可能继续流入：

```text
数据库
Java 业务接口
工单系统
退款系统
统计报表
```

后果就比“回答不好”严重。

所以结构化输出一定要有后端校验。

## 19. 结构化输出的基本流程

典型流程是：

```text
1. 定义业务字段
2. 定义 Pydantic 模型
3. 生成 JSON Schema 或写 response_format
4. 调用模型
5. 拿到模型输出 JSON 字符串
6. json.loads 解析
7. Pydantic 校验
8. 校验通过后进入业务逻辑
9. 校验失败则重试、修复、降级或返回错误
```

现在先记住一句话：

```text
模型输出不能直接信，必须先解析和校验
```

## 20. 结构化输出适合智能工单 Agent

你后面的项目会做智能工单 Agent。

用户可能说：

```text
我买的耳机左边没声音了，订单号 A12345，想申请退款。
```

自然语言回复可以是：

```text
我理解您想申请退款，我会帮您处理。
```

但系统真正需要的是：

```json
{
  "intent": "refund",
  "order_id": "A12345",
  "product": "耳机",
  "problem": "左边没声音",
  "requested_action": "refund",
  "need_human_review": false
}
```

这样后端才能：

```text
查订单
判断权限
创建工单
调用 Java API
进入人工审核
```

## 21. 结构化输出适合 RAG 引用来源

企业知识库 RAG 里，模型可能要回答问题并给引用。

自然语言回答：

```text
根据员工手册，年假需要提前三天申请。
```

结构化输出可以是：

```json
{
  "answer": "年假需要提前三天申请。",
  "citations": [
    {
      "document_id": "hr-handbook",
      "title": "员工手册",
      "page": 12
    }
  ],
  "has_enough_evidence": true
}
```

后端可以用这个结构：

```text
展示答案
展示引用来源
判断是否证据不足
做评测
做审计
```

## 22. 结构化输出适合分类

例如用户问：

```text
我的订单怎么还没发货？
```

模型结构化输出：

```json
{
  "category": "logistics",
  "priority": "normal",
  "need_order_lookup": true
}
```

系统就可以决定：

```text
走物流查询流程
调用订单 API
不用交给退款流程
```

## 23. 结构化输出适合信息抽取

输入：

```text
我叫张三，手机号 13800000000，想预约周五下午的安装服务。
```

输出：

```json
{
  "name": "张三",
  "phone": "13800000000",
  "service_type": "installation",
  "preferred_time": "周五下午"
}
```

这类任务就是信息抽取。

结构化输出非常适合。

## 24. 结构化输出和 tool calling 的区别

这两个概念容易混。

结构化输出是：

```text
模型直接返回一个结构化结果给你
```

tool calling 是：

```text
模型决定要调用哪个工具，并给出工具参数
```

OpenAI 文档里也区分了这两类用途：

```text
想让模型连接外部工具、函数、数据时，用 function/tool calling
想让模型回答用户时按固定结构输出，用 structured response_format 或 text.format
```

举例：

结构化输出：

```json
{
  "intent": "refund",
  "order_id": "12345"
}
```

tool calling：

```json
{
  "tool_name": "create_refund_ticket",
  "arguments": {
    "order_id": "12345",
    "reason": "质量问题"
  }
}
```

后面学 Agent 和工具调用时，会继续展开。

## 25. 结构化输出和流式输出的关系

流式输出适合逐步展示自然语言。

结构化输出通常更适合等完整结果出来后解析。

原因是 JSON 在没生成完之前通常是不完整的。

例如流式过程可能先收到：

```text
{"intent":
```

这不是合法 JSON。

等完整输出结束后才是：

```json
{
  "intent": "refund"
}
```

所以当前阶段你可以先记住：

```text
展示给用户的长文本：适合 streaming
给后端处理的结构化数据：通常先等完整结果，再解析校验
```

## 26. 结构化输出的常见坑

常见问题有：

```text
模型返回 Markdown 代码块
字段名不稳定
缺少必填字段
多返回解释文字
数字和字符串混用
枚举值乱写
null 和空字符串混用
日期格式不统一
数组长度不可控
嵌套结构太复杂
中文字段名和英文字段名混用
```

解决思路是：

```text
使用 JSON Mode 或 Structured Outputs
定义清晰 schema
使用 Pydantic 校验
校验失败时重试或修复
业务关键动作前人工确认
```

## 27. 字段名为什么建议用英文

不是中文字段名不能用。

但后端工程里通常更建议：

```json
{
  "intent": "refund",
  "order_id": "12345"
}
```

而不是：

```json
{
  "用户意图": "退款",
  "订单号": "12345"
}
```

原因是：

```text
代码变量通常用英文
跨语言系统更统一
Java/Python/数据库字段更好映射
减少编码和命名混乱
更接近 API 规范
```

给用户看的文案可以是中文。

给程序用的字段名建议稳定英文。

## 28. 枚举值为什么重要

如果不限制枚举，模型可能返回：

```text
退款
refund
return_money
apply_refund
用户想退货退款
```

这些人都能懂。

程序不好判断。

如果约定枚举：

```text
refund
order_query
complaint
unknown
```

程序就可以稳定写：

```python
if intent == "refund":
    ...
```

结构化输出里，枚举是非常重要的工程习惯。

## 29. null 和空字符串要分清楚

例如没有订单号。

建议输出：

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

`null` 表示：

```text
没有这个值
```

空字符串表示：

```text
有一个字符串，只是内容为空
```

两者语义不同。

业务代码里要分清。

## 30. 置信度是不是必须要有

不一定。

有些分类任务可以加：

```json
{
  "intent": "refund",
  "confidence": 0.86
}
```

置信度可以辅助：

```text
低置信度转人工
低置信度继续追问
低置信度不自动调用敏感操作
```

但模型给出的 confidence 不等于真实概率。

它只是一个参考信号。

不要把它当成绝对准确的数学概率。

## 31. 结构化输出不能替代业务校验

模型输出：

```json
{
  "intent": "refund",
  "order_id": "12345"
}
```

不代表真的可以退款。

后端还要检查：

```text
订单是否存在
订单是否属于当前用户
是否超过退款时间
商品是否支持退款
是否需要人工审核
```

结构化输出只是把用户意图整理成数据。

它不能替代业务规则。

## 32. 结构化输出不能替代权限控制

模型可能判断：

```json
{
  "action": "refund",
  "order_id": "12345"
}
```

但真正执行退款前，Java 后端必须检查：

```text
当前用户是谁
有没有权限操作这个订单
是否允许退款
是否需要二次确认
```

AI 不能绕过权限系统。

这点以后做 Agent 时非常重要。

## 33. 结构化输出不能替代人工确认

对敏感操作，例如：

```text
退款
删除数据
修改合同
转账
取消订单
创建正式工单
```

即使模型提取出了结构化参数，也应该加入确认步骤：

```text
请用户确认
请客服确认
请管理员确认
```

结构化输出让系统更容易处理，不代表系统可以盲目执行。

## 34. 结构化输出的错误处理

结构化输出失败时，常见处理方式：

```text
重新提示模型按 schema 输出
调用更便宜模型修复 JSON
返回让用户补充信息
走人工审核
记录日志方便排查
降级成普通自然语言回复
```

不要只写：

```text
except Exception:
    pass
```

结构化输出一旦失败，后端必须知道，并且要有明确降级策略。

## 35. 下一节会怎么做

下一节我们会进入：

```text
阶段 2 第 16 节：Pydantic 约束结构化输出
```

预计会做：

```text
定义结构化输出 Pydantic 模型
生成或理解 JSON Schema
让模型返回 JSON
解析 JSON 字符串
用 Pydantic 校验模型输出
写 fake LLM 测试
处理模型返回非法 JSON
处理字段缺失和类型错误
```

也就是从概念进入代码。

## 36. 你现在应该能解释什么

学完这一节，你应该能解释：

```text
为什么自然语言输出适合给人看
为什么结构化输出适合给程序处理
JSON 和结构化输出不是一回事
JSON Mode 和 Structured Outputs 的区别
JSON Schema 是输出契约
Pydantic 可以校验模型输出
模型返回 JSON 后仍然要校验
结构化输出不能替代业务规则、权限控制和人工确认
```

能讲清这些，就说明你不是只会写 prompt。

你开始理解 AI 应用工程了。

## 37. 本节产出

本节主要产出：

```text
notes/llm-api-stage2-15-structured-output-concept.md
```

本节不改业务代码。

原因是：

```text
第 15 节先学概念
第 16 节再用 Pydantic 写代码约束结构化输出
```

## 38. 本节练习

### 练习 1

题目：

请用自己的话解释：自然语言输出和结构化输出有什么区别？

参考答案：

自然语言输出主要给人看，表达灵活，例如一段解释、一段客服回复。

结构化输出主要给程序处理，字段、类型和含义更稳定，例如 JSON 对象里的 `intent`、`order_id`、`confidence`。

### 练习 2

题目：

为什么“返回 JSON”不一定等于“可靠的结构化输出”？

参考答案：

因为 JSON 只说明格式合法，不一定说明字段符合业务要求。

模型可能返回合法 JSON，但字段名不对、缺少必填字段、类型错误、枚举值乱写，所以仍然需要 schema 和后端校验。

### 练习 3

题目：

JSON Mode 和 Structured Outputs 的区别是什么？

参考答案：

JSON Mode 主要保证模型输出是合法 JSON。

Structured Outputs 进一步要求模型输出符合给定 JSON Schema，包括字段、类型、必填和枚举等约束。

### 练习 4

题目：

JSON Schema 的作用是什么？

参考答案：

JSON Schema 用来描述 JSON 数据应该长什么样。

它可以约束整体类型、字段名、字段类型、必填字段、枚举值、数组结构等，是结构化输出的数据契约。

### 练习 5

题目：

Pydantic 在结构化输出里有什么作用？

参考答案：

Pydantic 可以定义结构化输出模型，也可以在模型返回 JSON 后校验字段和类型。

它还可以从 Pydantic 模型生成 JSON Schema，给模型调用时使用。

### 练习 6

题目：

为什么模型返回 JSON 后还要做后端校验？

参考答案：

因为模型可能漏字段、类型错误、枚举值错误或返回不符合业务要求的数据。

后端校验可以阻止错误数据进入数据库、Java API、工单系统等业务流程。

### 练习 7

题目：

结构化输出适合智能工单 Agent 的哪些地方？

参考答案：

适合提取用户意图、订单号、问题描述、期望动作、是否需要人工审核等字段。

这些字段可以用于查询订单、创建工单、进入人工审核或调用 Java 业务接口。

### 练习 8

题目：

为什么结构化输出不能替代权限控制？

参考答案：

结构化输出只是在整理用户意图和参数。

真正执行退款、改订单、创建工单等操作前，后端仍然必须检查当前用户身份、订单归属、业务规则和操作权限。

### 练习 9

题目：

为什么结构化输出的字段名建议用英文？

参考答案：

英文更适合代码变量、API 字段、数据库字段和跨语言系统映射。

中文可以用于展示给用户，但给程序处理的数据字段建议稳定使用英文。

### 练习 10

题目：

结构化输出和 tool calling 是一回事吗？

参考答案：

不是。

结构化输出是让模型按固定结构回答。

tool calling 是让模型决定调用哪个工具，并生成工具参数。它们都可能用 schema，但用途不同。

## 39. 本节自测

### 自测 1

题目：

结构化输出主要是给人看还是给程序处理？

参考答案：

主要给程序处理。

### 自测 2

题目：

JSON Mode 主要保证什么？

参考答案：

主要保证模型输出是合法 JSON。

### 自测 3

题目：

Structured Outputs 主要保证什么？

参考答案：

主要保证模型输出符合指定 JSON Schema。

### 自测 4

题目：

JSON Schema 能约束哪些内容？

参考答案：

可以约束字段名、字段类型、必填字段、枚举值、对象结构、数组结构等。

### 自测 5

题目：

Pydantic 的 `model_json_schema()` 可以做什么？

参考答案：

可以从 Pydantic 模型生成 JSON Schema 字典。

### 自测 6

题目：

模型输出 `{"order_id": ""}` 和 `{"order_id": null}` 语义一样吗？

参考答案：

不一样。

`null` 表示没有值，空字符串表示有一个字符串但内容为空。

### 自测 7

题目：

结构化输出能不能直接替代业务规则校验？

参考答案：

不能。

业务规则仍然要由后端系统校验。

### 自测 8

题目：

结构化输出是否天然适合流式逐块解析？

参考答案：

通常不适合。

因为 JSON 在生成完整之前往往不是合法 JSON，通常要等完整输出后再解析和校验。

### 自测 9

题目：

如果模型返回合法 JSON，但枚举值不在允许范围内，能不能直接进入业务流程？

参考答案：

不能。

需要校验失败并进行重试、修复、降级或人工处理。

### 自测 10

题目：

下一节学习什么？

参考答案：

下一节学习 Pydantic 约束结构化输出。

## 40. 本节小结

这一节完成了：

```text
理解自然语言输出和结构化输出
理解 JSON 不等于可靠结构化输出
理解 JSON Mode
理解 Structured Outputs
理解 JSON Schema
理解 Pydantic 在结构化输出中的作用
理解结构化输出适合分类、抽取、RAG 引用和工单 Agent
理解结构化输出不能替代业务校验、权限控制和人工确认
```

现在你已经知道为什么 AI 应用不能只返回一段话。

下一节进入：

```text
Pydantic 约束结构化输出
```

## 41. 参考资料

- [OpenAI：Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [OpenAI：Migrate to the Responses API](https://developers.openai.com/api/docs/guides/migrate-to-responses)
- [阿里云百炼：结构化输出](https://help.aliyun.com/zh/model-studio/qwen-structured-output)
- [Pydantic：JSON Schema](https://docs.pydantic.dev/latest/concepts/json_schema/)
- [JSON Schema：Creating your first schema](https://json-schema.org/learn/getting-started-step-by-step)
