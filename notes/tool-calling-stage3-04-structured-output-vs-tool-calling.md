# 阶段 3 第 4 节：结构化输出 vs Tool Calling

## 本节目标

阶段 2 我们已经学过结构化输出，并做过 `/extract-ticket`：

```text
用户一句自然语言
-> 模型抽取工单字段
-> 后端用 Pydantic 校验
-> 返回稳定 JSON
```

阶段 3 我们正在学习 Tool Calling：

```text
用户一句自然语言
-> 模型判断是否需要工具
-> 模型返回工具名和参数
-> 后端校验参数
-> 后端决定是否执行工具
-> 工具结果再返回给模型或接口
```

这两件事都可能出现 JSON、JSON Schema、Pydantic，所以初学时很容易混在一起。

本节要解决一个问题：

```text
什么时候用结构化输出？
什么时候用 Tool Calling？
什么时候两者一起用？
```

学完以后，你要能说清楚：

- 结构化输出解决什么问题。
- Tool Calling 解决什么问题。
- 为什么它们都可能用 JSON Schema。
- 为什么 `/extract-ticket` 不是 Tool Calling。
- 为什么查订单、创建工单、申请退款这类动作更适合 Tool Calling。
- 为什么模型返回结构化 JSON 也不能代表后端已经安全。

## 一句话区分

先记住最核心的一句话：

```text
结构化输出 = 让模型按固定格式回答。
Tool Calling = 让模型提出调用哪个工具、带什么参数。
```

再换成更接地气的说法：

```text
结构化输出问的是：这句话里有哪些字段？
Tool Calling 问的是：下一步应该调用哪个工具？
```

比如用户说：

```text
订单 A1001 三天没发货了，我要投诉。
```

结构化输出更关心：

```json
{
  "intent": "complaint",
  "order_id": "A1001",
  "summary": "用户投诉订单 A1001 三天未发货",
  "urgency": "high",
  "need_human_review": true
}
```

Tool Calling 更关心：

```json
{
  "tool_name": "query_order",
  "arguments": {
    "order_id": "A1001"
  }
}
```

注意：Tool Calling 这里不是“模型已经查了订单”，而是“模型建议调用 `query_order`”。真正查订单必须由后端代码执行。

## 先把“输出”和“动作”分开

很多人学 AI Agent 会混淆一个点：

```text
模型返回了一段 JSON，不等于模型执行了动作。
```

结构化输出也是 JSON。

Tool Calling 的参数也是 JSON。

但它们背后的目的不一样。

### 结构化输出的重点是“结果形状”

结构化输出希望模型最终给我们一个稳定的数据结构。

比如：

```json
{
  "intent": "refund",
  "order_id": "A1001",
  "summary": "用户想申请退款",
  "urgency": "normal",
  "need_human_review": true
}
```

这里的重点是：

```text
模型把自然语言整理成程序能处理的数据。
```

它没有查数据库。

它没有创建工单。

它没有退款。

它只是把用户输入转换成一个结构。

### Tool Calling 的重点是“动作意图”

Tool Calling 希望模型判断：

```text
要不要调用工具？
调用哪个工具？
参数是什么？
```

比如：

```json
{
  "tool_name": "query_order",
  "arguments": {
    "order_id": "A1001"
  }
}
```

这里的重点是：

```text
模型想要从外部系统拿数据，或者让外部系统执行某个动作。
```

但模型本身仍然不能直接执行。

后端要做这些事情：

```text
1. 检查工具名是不是允许调用。
2. 检查参数是不是符合 schema。
3. 检查当前用户有没有权限。
4. 判断是不是敏感操作。
5. 需要时让用户确认。
6. 调用 Java 业务服务或其他系统。
7. 记录日志和 trace_id。
8. 把工具结果交回给模型或直接返回给前端。
```

## 官方资料怎么区分

OpenAI 官方文档把两个方向分得很清楚：

- Structured Outputs：让模型响应符合你定义的 JSON Schema。
- Function Calling / Tool Calling：让模型连接外部系统、访问训练数据之外的信息，或使用应用提供的动作能力。

OpenAI 的 Structured Outputs 文档也明确建议：

```text
如果你要连接模型到工具、函数、数据等系统，用 function calling。
如果你只是想约束模型回复给用户的格式，用 structured response_format。
```

阿里云百炼的模型能力文档也把 Function Calling 和 Structured output 分成两个能力：

- Function calling：让模型使用外部工具，例如查天气、查数据库、预订会议。
- Structured output：强制有效 JSON 输出，适合从文本里抽取姓名、地址等结构化数据。

这说明：它们经常一起出现，但不是同一个东西。

## 对比表

| 对比点 | 结构化输出 | Tool Calling |
| --- | --- | --- |
| 核心目的 | 让模型按固定结构回答 | 让模型提出要调用的工具和参数 |
| 关注点 | 输出数据长什么样 | 下一步该做什么动作 |
| 常见问题 | 从文本中抽取字段、分类、总结成 JSON | 查订单、查库存、创建工单、调用 Java API |
| 模型输出 | 最终业务数据 | 工具名 + arguments |
| 是否访问外部系统 | 通常不访问 | 通常要访问 |
| 是否产生业务动作 | 不应该直接产生动作 | 可能触发动作，但必须由后端决定 |
| schema 的作用 | 约束模型最终输出结构 | 约束工具参数结构 |
| 后端校验 | 仍然必须校验 | 更必须校验 |
| 风险重点 | 模型返回字段错误、类型错误、漏字段 | 越权调用、参数注入、误操作、重复执行 |
| 当前项目例子 | `/extract-ticket` | 后续 `query_order`、`create_ticket` |

## 为什么它们都用 JSON Schema

你可能会问：

```text
既然二者不同，为什么都用 JSON Schema？
```

因为 JSON Schema 只是在描述“数据长什么样”。

它可以描述结构化输出：

```json
{
  "type": "object",
  "properties": {
    "intent": {
      "type": "string",
      "enum": ["refund", "order_query", "logistics", "complaint", "unknown"]
    },
    "order_id": {
      "type": ["string", "null"]
    }
  },
  "required": ["intent", "order_id"]
}
```

它也可以描述工具参数：

```json
{
  "type": "object",
  "properties": {
    "order_id": {
      "type": "string",
      "description": "订单编号，例如 A1001"
    }
  },
  "required": ["order_id"],
  "additionalProperties": false
}
```

JSON Schema 本身不关心你是“抽字段”还是“调用工具”。

它只关心：

```text
这个 JSON 对象应该有哪些字段？
字段是什么类型？
哪些字段必填？
哪些值是允许的？
是否允许多余字段？
```

真正决定它属于结构化输出还是 Tool Calling 的，是业务目的。

## Pydantic 在两者里的角色

Pydantic 也不是结构化输出专属的。

Pydantic 的核心作用是：

```text
把外部数据校验成 Python 程序可信的数据对象。
```

在结构化输出里：

```text
模型返回 JSON
-> TicketExtraction.model_validate_json(...)
-> 得到 TicketExtraction 对象
```

在 Tool Calling 里：

```text
模型返回 tool arguments
-> QueryOrderArgs.model_validate(...)
-> 得到 QueryOrderArgs 对象
-> 后端再决定是否调用 query_order
```

所以你要记住：

```text
Pydantic 不是让模型变安全。
Pydantic 是让后端发现模型输出是否符合我们的规则。
```

如果不符合，就拒绝、重试、降级或交给人工处理。

## `/extract-ticket` 为什么不是 Tool Calling

我们当前项目里有一个接口：

```text
POST /extract-ticket
```

调用链路是：

```text
POST /extract-ticket
-> StructuredOutputService.extract_ticket()
-> build_ticket_extraction_messages()
-> client.chat.completions.create(..., response_format={"type":"json_object"})
-> TicketExtraction.model_validate_json()
```

它做的事情是：

```text
把用户的一句话抽取成工单字段。
```

比如用户输入：

```text
订单 A1001 一直没有发货，我要投诉。
```

模型输出：

```json
{
  "intent": "complaint",
  "order_id": "A1001",
  "summary": "用户投诉订单 A1001 未发货",
  "urgency": "high",
  "need_human_review": true
}
```

后端校验通过后返回给前端。

这里没有出现：

```text
模型选择 query_order 工具
模型选择 create_ticket 工具
后端执行工具
工具结果回传
```

所以它是结构化输出，不是 Tool Calling。

## 查订单为什么是 Tool Calling

如果用户问：

```text
帮我查一下订单 A1001 到哪了。
```

只做结构化输出，最多得到：

```json
{
  "intent": "logistics",
  "order_id": "A1001",
  "summary": "用户询问订单 A1001 物流状态",
  "urgency": "normal",
  "need_human_review": false
}
```

但这个结果不能告诉用户订单现在到底在哪。

因为模型不知道实时订单状态。

订单状态在业务系统里，可能在 Java 后端、数据库、第三方物流接口里。

所以这时需要 Tool Calling：

```json
{
  "tool_name": "query_order",
  "arguments": {
    "order_id": "A1001"
  }
}
```

后端收到后，再执行：

```text
调用 Java 订单服务
-> 查询订单 A1001
-> 得到真实状态
-> 返回给模型总结，或直接返回给用户
```

这才是工具调用要解决的问题：

```text
模型自身不知道实时数据，所以让后端去查。
```

## 创建工单为什么通常要两者结合

用户说：

```text
订单 A1001 三天没发货了，我要投诉。
```

如果你直接让模型调用 `create_ticket`，风险很高。

因为创建工单是业务动作：

```text
系统里会多一条记录。
可能通知客服。
可能影响售后流程。
可能产生重复工单。
```

更稳的流程是：

```text
第一步：结构化输出，抽取工单字段。
第二步：后端展示给用户确认。
第三步：用户确认后，模型或后端决定调用 create_ticket。
第四步：后端校验参数、权限、幂等性。
第五步：后端调用 Java 工单服务。
第六步：把创建结果返回给用户。
```

用流程表示：

```text
用户输入
-> 结构化输出：抽取 intent/order_id/summary/urgency
-> 用户确认
-> Tool Calling：create_ticket(arguments)
-> 后端执行 Java API
-> 返回工单号
-> 模型总结给用户
```

这里两者都用到了：

- 结构化输出负责把自然语言变成稳定字段。
- Tool Calling 负责把确认后的动作交给后端系统执行。

## 什么时候用结构化输出

遇到下面这些场景，优先想到结构化输出：

- 从用户输入里抽取字段。
- 判断用户意图。
- 把一段文本分类。
- 把长文本总结成固定格式。
- 从简历里抽取姓名、技能、工作年限。
- 从客服对话里抽取问题类型和紧急程度。
- 从用户问题里抽取订单号、手机号、产品名。
- 让模型输出固定 API 响应结构。

判断标准：

```text
如果你只需要模型把文字整理成程序能读的数据，通常用结构化输出。
```

当前项目例子：

```text
/extract-ticket
```

它只抽取工单字段，不查外部业务系统。

## 什么时候用 Tool Calling

遇到下面这些场景，优先想到 Tool Calling：

- 需要查询实时订单状态。
- 需要查询用户权限。
- 需要查询库存。
- 需要创建工单。
- 需要取消订单。
- 需要申请退款。
- 需要调用 Java 后端 API。
- 需要读数据库。
- 需要访问外部系统。
- 需要把模型不知道的新数据拿回来。

判断标准：

```text
如果模型必须借助外部系统才能完成任务，通常用 Tool Calling。
```

后续项目例子：

```text
query_order(order_id)
create_ticket(order_id, summary, urgency)
```

## 什么时候两者一起用

很多真实业务流程会同时用两者。

比如智能工单 Agent：

```text
用户：订单 A1001 三天没发货了，我要投诉。
```

可以设计成：

```text
1. 结构化输出：
   抽取 intent=complaint、order_id=A1001、summary、urgency。

2. Tool Calling：
   调用 query_order(order_id="A1001") 查询真实订单状态。

3. 业务规则判断：
   如果订单确实异常，生成工单草稿。

4. 用户确认：
   “我将为订单 A1001 创建投诉工单，紧急程度 high，是否确认？”

5. Tool Calling：
   用户确认后调用 create_ticket(...)。

6. 模型总结：
   “已创建工单 T9001，客服会继续处理。”
```

这个流程比“模型一上来就创建工单”更可靠。

## 一个重要边界：结构化输出不能偷偷变成动作

假设模型结构化输出返回：

```json
{
  "intent": "refund",
  "order_id": "A1001",
  "summary": "用户要求退款",
  "urgency": "high",
  "need_human_review": false
}
```

后端不能因为 `need_human_review=false` 就自动退款。

原因很简单：

```text
这个字段是模型生成的。
模型不能决定是否绕过审核。
```

正确做法是：

```text
模型可以给建议。
后端必须按业务规则重新判断。
```

比如：

```text
是否超过退款期限？
当前用户是否是订单本人？
订单是否已发货？
商品是否支持退款？
是否需要人工审核？
是否已经创建过退款单？
```

这些必须由后端和业务系统判断。

## 另一个重要边界：Tool Calling 不等于自动执行

模型返回：

```json
{
  "tool_name": "refund_order",
  "arguments": {
    "order_id": "A1001",
    "reason": "用户要求退款"
  }
}
```

这只是模型提出：

```text
我认为应该调用 refund_order。
```

后端可以拒绝：

```text
当前用户不是订单本人。
订单已签收超过 7 天。
退款工具是敏感工具，需要用户二次确认。
缺少幂等键。
参数不符合 schema。
工具不在允许列表里。
```

真正执行权永远在后端。

## 常见误区

### 误区 1：只要模型返回 JSON，就是结构化输出

不准确。

Tool Calling 的 arguments 也是 JSON。

要看目的：

```text
最终回答固定格式 -> 结构化输出
请求调用工具 -> Tool Calling
```

### 误区 2：结构化输出可以直接驱动业务动作

不可以。

结构化输出只是抽取结果或建议。

它可以作为业务流程的输入，但不能替代权限、确认和业务规则。

### 误区 3：Tool Calling 是模型在执行函数

不是。

模型通常只是返回工具调用请求。

函数在你的后端执行。

### 误区 4：用了 JSON Schema 就不用校验

不对。

schema 能帮助模型更稳定地输出，也能帮助后端定义规则。

但后端必须继续用 Pydantic 或其他方式校验。

### 误区 5：所有任务都要用 Tool Calling

没必要。

如果只是分类、抽字段、总结成 JSON，用结构化输出更简单。

Tool Calling 会引入更多复杂性：

```text
工具列表
参数校验
权限判断
执行错误
超时重试
幂等
审计日志
用户确认
```

## 本项目里的分工

当前项目已经有：

```text
/extract-ticket
```

它属于结构化输出。

它负责：

```text
从用户输入中抽取工单字段。
```

后续阶段 3 会逐步加入：

```text
query_order
create_ticket
```

它们属于 Tool Calling。

它们负责：

```text
和外部业务系统交互。
```

项目里推荐的整体流程是：

```text
用户自然语言
-> 结构化输出抽字段
-> 后端校验
-> 必要时用户确认
-> Tool Calling 查询或创建
-> 后端调用 Java 服务
-> 工具结果返回
-> 模型总结
```

这条线就是智能工单 Agent 的基础。

## 和 LangChain 的关系

这节还没有正式引入 LangChain，但要提前知道：

```text
LangChain 不是创造了结构化输出和 Tool Calling。
LangChain 是把这些能力封装得更容易用。
```

底层概念仍然是：

```text
结构化输出：模型按 schema 返回固定结构。
Tool Calling：模型返回工具名和参数，后端执行工具。
```

以后学 LangChain 的 `with_structured_output()`、`bind_tools()`、`Tool`、Agent 时，不要只记 API。

你要能看出它们背后的底层动作。

## 练习 1：判断该用什么

请判断下面场景更适合：

```text
A. 结构化输出
B. Tool Calling
C. 两者结合
```

题目：

1. 用户说“订单 A1001 还没发货，我想投诉”，系统只需要提取订单号、意图和摘要。
2. 用户问“订单 A1001 现在物流到哪了”，系统需要查实时物流。
3. 用户说“帮我创建一个投诉工单”，系统要先抽字段，再让用户确认，最后创建工单。
4. 把一篇文章总结成 `{title, summary, tags}`。
5. 判断用户是否符合退款条件，需要查询订单状态、支付状态和售后规则。

### 练习 1 参考答案

1. A，结构化输出。只需要抽取字段，不访问外部系统。
2. B，Tool Calling。实时物流必须查外部业务系统。
3. C，两者结合。先结构化输出抽字段，再确认，最后工具调用创建工单。
4. A，结构化输出。固定格式总结，不需要外部动作。
5. C，两者结合。可以先抽取退款意图和订单号，再调用工具查询订单和规则。

## 练习 2：写出两种输出

用户输入：

```text
订单 A1001 已经三天没更新物流了，帮我看一下。
```

请分别写出：

1. 结构化输出可能返回什么。
2. Tool Calling 可能返回什么。

### 练习 2 参考答案

结构化输出示例：

```json
{
  "intent": "logistics",
  "order_id": "A1001",
  "summary": "用户询问订单 A1001 三天未更新物流的问题",
  "urgency": "normal",
  "need_human_review": false
}
```

Tool Calling 示例：

```json
{
  "tool_name": "query_order",
  "arguments": {
    "order_id": "A1001"
  }
}
```

如果后面有单独的物流工具，也可以是：

```json
{
  "tool_name": "query_logistics",
  "arguments": {
    "order_id": "A1001"
  }
}
```

## 练习 3：设计一个安全流程

用户输入：

```text
订单 A1001 没发货，直接给我退款。
```

请设计一个安全流程。

要求：

- 不能让模型直接退款。
- 要用到结构化输出。
- 要用到 Tool Calling。
- 要有人类确认或用户确认。

### 练习 3 参考答案

一种安全流程：

```text
1. 结构化输出抽取：
   intent=refund
   order_id=A1001
   summary=用户要求订单未发货退款
   urgency=normal
   need_human_review=true

2. 后端校验结构化输出：
   intent 必须在允许枚举里。
   order_id 格式必须合法。

3. Tool Calling 查询订单：
   query_order(order_id="A1001")

4. 后端调用 Java 订单服务：
   查询订单是否存在、是否属于当前用户、是否已发货、是否可退款。

5. 后端业务规则判断：
   如果不符合退款条件，拒绝并说明原因。
   如果符合退款条件，生成退款确认提示。

6. 用户确认：
   “订单 A1001 可申请退款，是否确认提交退款申请？”

7. 用户确认后，再调用退款申请工具：
   create_refund_request(order_id="A1001", reason="订单未发货")

8. 后端执行时检查权限、幂等和审计日志。

9. 返回退款申请单号。
```

注意：即使模型说 `need_human_review=false`，后端也不能盲信。退款属于敏感业务动作，必须按后端规则处理。

## 自测题

### 1. 结构化输出和 Tool Calling 最大区别是什么？

参考答案：

```text
结构化输出是让模型按固定格式返回数据。
Tool Calling 是让模型提出要调用哪个工具以及参数是什么。
```

### 2. 为什么它们都可能用 JSON Schema？

参考答案：

```text
因为 JSON Schema 只是描述 JSON 数据结构的规则。结构化输出用它约束最终回答结构，Tool Calling 用它约束工具参数结构。
```

### 3. `/extract-ticket` 为什么不是 Tool Calling？

参考答案：

```text
因为 `/extract-ticket` 只是从用户输入中抽取工单字段，然后用 Pydantic 校验并返回结果。它没有让模型选择工具，也没有由后端执行工具。
```

### 4. 查订单为什么适合 Tool Calling？

参考答案：

```text
因为订单状态是实时业务数据，模型训练知识里没有当前订单状态，必须由后端调用订单系统或 Java API 查询。
```

### 5. 模型返回了 `create_ticket` 的工具调用，后端是否必须执行？

参考答案：

```text
不是。模型只是提出工具调用请求，后端必须校验工具名、参数、权限、业务规则、用户确认和幂等性，然后才能决定是否执行。
```

### 6. 结构化输出能不能直接创建工单？

参考答案：

```text
不能。结构化输出可以生成工单草稿或抽取字段，但真正创建工单是业务动作，应该由后端在校验、确认和权限检查后通过工具或业务服务执行。
```

### 7. 如果只需要把文本总结成固定 JSON，要不要用 Tool Calling？

参考答案：

```text
通常不用。只需要固定格式输出时，用结构化输出更简单。Tool Calling 适合需要外部数据或外部动作的场景。
```

## 本节小结

这节只要记住三句话：

```text
结构化输出：把自然语言变成固定格式的数据。
Tool Calling：让模型提出调用工具的请求。
后端：永远负责校验、权限、确认、执行和审计。
```

对智能工单 Agent 来说：

```text
/extract-ticket 是结构化输出。
query_order / create_ticket 是 Tool Calling。
真实业务流程通常会把两者组合起来。
```

下一节开始，我们会进入更接近代码的部分：

```text
用 fake tool 模拟查订单。
```

也就是先不接真实 Java 服务，先在 Python 里写一个假的 `query_order` 工具，把工具调用的后端执行流程跑通。

## 资料来源

- [OpenAI：Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [OpenAI：Function calling](https://developers.openai.com/api/docs/guides/function-calling)
- [OpenAI：Using tools](https://developers.openai.com/api/docs/guides/tools)
- [阿里云百炼：Function Calling](https://help.aliyun.com/zh/model-studio/qwen-function-calling)
- [阿里云 Model Studio：Text generation models](https://help.aliyun.com/en/model-studio/text-generation-model/)
- [阿里云百炼：结构化输出](https://help.aliyun.com/zh/model-studio/qwen-structured-output)
- [Pydantic：JSON Schema](https://pydantic.dev/docs/validation/latest/concepts/json_schema/)
