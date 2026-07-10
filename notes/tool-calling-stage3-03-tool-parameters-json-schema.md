# 阶段 3 第 3 节：工具参数和 JSON Schema

## 本节目标

前两节我们已经建立了两个核心概念：

```text
Tool Calling = 模型提出工具调用意图，后端决定是否执行。
模型输出 = 不可信输入，后端必须校验。
```

这一节开始讲工具调用里最关键的细节：

```text
工具参数怎么描述？
模型怎么知道该传哪些参数？
后端怎么知道参数是否合法？
```

答案就是：用 JSON Schema 描述参数结构。

本节先不写项目业务代码，但你要把下面这些概念学清楚：

- 什么是工具参数。
- 为什么模型需要参数说明。
- JSON Schema 是什么。
- `type` 是什么。
- `properties` 是什么。
- `required` 是什么。
- `enum` 是什么。
- `additionalProperties` 是什么。
- JSON Schema 和 Pydantic 是什么关系。
- 为什么 schema 不能替代后端校验。

## 先从一个工具开始

假设我们后面要做一个查订单工具：

```text
query_order(order_id)
```

它的意思是：

```text
根据订单号查询订单详情。
```

如果用户说：

```text
帮我查一下订单 A1001。
```

模型应该能判断：

```text
需要调用 query_order 工具。
参数 order_id 应该是 A1001。
```

但模型怎么知道这个工具需要 `order_id`？

因为我们要提前把工具说明给模型：

```json
{
  "type": "function",
  "name": "query_order",
  "description": "查询订单详情，适合用户询问订单状态、支付状态或发货状态时使用。",
  "parameters": {
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
}
```

这段里真正描述参数的是：

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

这部分就是 JSON Schema。

## 什么是工具参数

工具参数就是调用工具时必须传给工具的数据。

比如：

```text
query_order(order_id="A1001")
```

这里的参数是：

```json
{
  "order_id": "A1001"
}
```

再比如创建工单：

```text
create_ticket(order_id, category, summary, urgency)
```

参数可能是：

```json
{
  "order_id": "A1001",
  "category": "shipping_delay",
  "summary": "用户反馈订单三天未发货",
  "urgency": "normal"
}
```

你可以把工具参数理解成：

```text
模型从自然语言里整理出来的一包结构化数据。
```

但是这一包数据不能随便长。

它必须符合后端定义好的规则。

## 为什么模型需要参数说明

模型不是你代码里的函数调用者。

普通 Python 代码调用函数时，开发者能看到函数签名：

```python
def query_order(order_id: str) -> dict:
    ...
```

开发者看到这个签名，就知道要传 `order_id`。

但模型看不到你的 Python 函数签名，也看不到 Java 方法签名。

所以我们要用工具定义告诉模型：

```text
这个工具叫什么。
什么时候应该用它。
它需要哪些参数。
每个参数是什么类型。
哪些参数必须有。
哪些参数只能从固定选项里选。
```

这就是工具参数 schema 的作用。

## 什么是 JSON Schema

JSON Schema 可以先这样理解：

```text
JSON Schema 是 JSON 数据的说明书和约束规则。
```

JSON 是数据：

```json
{
  "order_id": "A1001",
  "category": "shipping_delay"
}
```

JSON Schema 是描述这份 JSON 应该长什么样：

```json
{
  "type": "object",
  "properties": {
    "order_id": {
      "type": "string"
    },
    "category": {
      "type": "string"
    }
  },
  "required": ["order_id", "category"]
}
```

二者关系是：

```text
JSON = 实际数据
JSON Schema = 校验 JSON 数据的规则
```

就像：

```text
表单填写内容 = JSON
表单填写规则 = JSON Schema
```

## `type`：规定数据类型

`type` 用来规定一个值应该是什么类型。

常见类型：

| JSON Schema 类型 | 含义 | JSON 例子 |
| --- | --- | --- |
| `object` | 对象，类似 Python 字典 | `{"order_id": "A1001"}` |
| `string` | 字符串 | `"A1001"` |
| `integer` | 整数 | `3` |
| `number` | 数字，整数或小数 | `19.8` |
| `boolean` | 布尔值 | `true` / `false` |
| `array` | 数组，类似 Python 列表 | `["A1001", "A1002"]` |
| `null` | 空值 | `null` |

比如：

```json
{
  "type": "string"
}
```

表示这个值必须是字符串。

如果我们写：

```json
{
  "order_id": "A1001"
}
```

符合 `order_id` 是 string。

如果模型传：

```json
{
  "order_id": 1001
}
```

这就不符合，因为 `1001` 是数字，不是字符串。

注意：

```text
"1001" 是字符串。
1001 是数字。
```

JSON 里有没有引号很重要。

## `object`：一组字段

工具参数通常是一个对象。

比如：

```json
{
  "order_id": "A1001",
  "category": "shipping_delay"
}
```

它对应的 schema 顶层一般写：

```json
{
  "type": "object"
}
```

意思是：

```text
工具参数整体必须是一个对象。
```

为什么工具参数要用对象？

因为对象可以表达多个字段：

```text
order_id
category
summary
urgency
```

如果只传一个字符串：

```json
"A1001"
```

模型和后端都不容易扩展。

所以工具参数一般都设计成对象：

```json
{
  "order_id": "A1001"
}
```

## `properties`：规定对象里有哪些字段

`properties` 用来描述对象里的字段。

例如：

```json
{
  "type": "object",
  "properties": {
    "order_id": {
      "type": "string",
      "description": "订单编号，例如 A1001"
    },
    "include_items": {
      "type": "boolean",
      "description": "是否返回订单商品明细"
    }
  }
}
```

这表示对象里可以有两个字段：

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `order_id` | string | 订单编号 |
| `include_items` | boolean | 是否返回商品明细 |

对应数据：

```json
{
  "order_id": "A1001",
  "include_items": true
}
```

要注意：

```text
properties 只是声明字段规则，不代表字段一定必填。
```

字段是否必填，要看 `required`。

## `required`：规定哪些字段必填

`required` 是一个数组，用来列出必填字段名。

例如：

```json
{
  "type": "object",
  "properties": {
    "order_id": {
      "type": "string"
    },
    "include_items": {
      "type": "boolean"
    }
  },
  "required": ["order_id"]
}
```

这表示：

- `order_id` 必填。
- `include_items` 可以不传。

合法：

```json
{
  "order_id": "A1001"
}
```

也合法：

```json
{
  "order_id": "A1001",
  "include_items": true
}
```

不合法：

```json
{
  "include_items": true
}
```

因为缺少 `order_id`。

常见误区：

```json
{
  "properties": {
    "order_id": {
      "type": "string"
    }
  }
}
```

这并不代表 `order_id` 必填。

如果要必填，必须写：

```json
{
  "required": ["order_id"]
}
```

## `enum`：固定选项

`enum` 用来限制字段只能是固定几个值之一。

比如工单优先级：

```json
{
  "type": "string",
  "enum": ["low", "normal", "high"]
}
```

合法：

```json
{
  "urgency": "normal"
}
```

不合法：

```json
{
  "urgency": "urgent"
}
```

因为 `"urgent"` 不在 `["low", "normal", "high"]` 里面。

为什么 `enum` 很重要？

因为模型可能会用自然语言生成各种说法：

```text
紧急
非常急
urgent
important
high_priority
```

但后端需要稳定枚举：

```text
low
normal
high
```

所以 schema 要把选项规定清楚。

## `additionalProperties`：是否允许多余字段

默认情况下，JSON Schema 的对象可能允许额外字段。

例如 schema 只定义：

```json
{
  "type": "object",
  "properties": {
    "order_id": {
      "type": "string"
    }
  },
  "required": ["order_id"]
}
```

模型传：

```json
{
  "order_id": "A1001",
  "admin": true
}
```

如果没有禁止额外字段，这个 `admin` 字段可能不会因为 `properties` 自动失败。

在工具调用里，我们通常更希望严格一点：

```json
{
  "additionalProperties": false
}
```

完整写法：

```json
{
  "type": "object",
  "properties": {
    "order_id": {
      "type": "string"
    }
  },
  "required": ["order_id"],
  "additionalProperties": false
}
```

这样模型多传：

```json
{
  "order_id": "A1001",
  "admin": true
}
```

就应该被拒绝。

这很适合工具调用，因为工具参数要可控。

## `description`：给模型看的解释

`description` 不是校验规则，但非常重要。

它主要给模型看，让模型知道这个字段是什么意思。

比如：

```json
{
  "order_id": {
    "type": "string",
    "description": "订单编号，例如 A1001。不要填写用户手机号或商品编号。"
  }
}
```

这句话会帮助模型更准确地从用户输入里提取参数。

如果只写：

```json
{
  "order_id": {
    "type": "string"
  }
}
```

模型也能猜，但不如描述清楚稳定。

好的 `description` 应该说明：

- 这个字段是什么。
- 什么时候填写。
- 示例值是什么。
- 不应该填什么。
- 和相似字段有什么区别。

例如：

```json
{
  "category": {
    "type": "string",
    "enum": ["shipping_delay", "refund", "complaint"],
    "description": "工单类型。shipping_delay 表示催发货或物流延迟；refund 表示退款问题；complaint 表示用户明确投诉。"
  }
}
```

## 第一个完整工具：查询订单

现在我们把 `query_order` 工具完整写出来：

```json
{
  "type": "function",
  "name": "query_order",
  "description": "查询订单详情，适合用户询问订单状态、支付状态、发货状态或物流进度时使用。",
  "parameters": {
    "type": "object",
    "properties": {
      "order_id": {
        "type": "string",
        "description": "订单编号，例如 A1001。不要填写手机号、用户名或商品编号。"
      }
    },
    "required": ["order_id"],
    "additionalProperties": false
  }
}
```

用户输入：

```text
帮我查一下订单 A1001。
```

模型理想输出：

```json
{
  "tool_name": "query_order",
  "arguments": {
    "order_id": "A1001"
  }
}
```

这个工具的参数规则是：

- 参数整体必须是对象。
- 只能有 `order_id`。
- `order_id` 必须是字符串。
- `order_id` 必填。
- 不允许额外字段。

## 第二个完整工具：创建工单草稿

再看一个稍复杂的工具：

```text
create_ticket_draft(order_id, category, summary, urgency)
```

我们先叫“创建工单草稿”，而不是“创建正式工单”，是因为正式创建会涉及用户确认。

schema：

```json
{
  "type": "function",
  "name": "create_ticket_draft",
  "description": "根据用户问题创建工单草稿，不会直接提交正式工单。适合用户表达售后、投诉、催发货或退款问题时使用。",
  "parameters": {
    "type": "object",
    "properties": {
      "order_id": {
        "type": "string",
        "description": "订单编号，例如 A1001。如果用户没有提供订单号，先不要编造。"
      },
      "category": {
        "type": "string",
        "enum": ["shipping_delay", "refund", "complaint", "other"],
        "description": "工单类型。shipping_delay 表示物流或发货延迟；refund 表示退款；complaint 表示明确投诉；other 表示其他问题。"
      },
      "summary": {
        "type": "string",
        "description": "用一句话概括用户问题，不要包含 API key、身份证号、完整手机号等敏感信息。"
      },
      "urgency": {
        "type": "string",
        "enum": ["low", "normal", "high"],
        "description": "紧急程度。普通问题用 normal；明确投诉、长时间未处理或强烈不满可用 high。"
      }
    },
    "required": ["order_id", "category", "summary", "urgency"],
    "additionalProperties": false
  }
}
```

用户输入：

```text
订单 A1001 三天没发货了，我要投诉。
```

模型理想参数：

```json
{
  "order_id": "A1001",
  "category": "complaint",
  "summary": "用户反馈订单 A1001 三天未发货并明确投诉。",
  "urgency": "high"
}
```

这里 `category` 和 `urgency` 都用了 `enum`，目的是让模型输出稳定字段，而不是随便写中文、英文或其他格式。

## 数组参数：`array` 和 `items`

有些工具需要传多个值。

例如批量查订单：

```text
query_orders(order_ids)
```

参数：

```json
{
  "order_ids": ["A1001", "A1002"]
}
```

schema 可以写：

```json
{
  "type": "object",
  "properties": {
    "order_ids": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "订单编号列表，例如 [\"A1001\", \"A1002\"]。"
    }
  },
  "required": ["order_ids"],
  "additionalProperties": false
}
```

这里：

- `type: "array"` 表示这是数组。
- `items` 表示数组里每一项应该是什么类型。

合法：

```json
{
  "order_ids": ["A1001", "A1002"]
}
```

不合法：

```json
{
  "order_ids": ["A1001", 1002]
}
```

因为第二项是数字，不是字符串。

## 嵌套对象

有些参数里面还包含对象。

比如创建通知：

```json
{
  "receiver": {
    "user_id": "U1001",
    "channel": "sms"
  },
  "message": "你的工单已经创建"
}
```

schema：

```json
{
  "type": "object",
  "properties": {
    "receiver": {
      "type": "object",
      "properties": {
        "user_id": {
          "type": "string"
        },
        "channel": {
          "type": "string",
          "enum": ["sms", "email", "site_message"]
        }
      },
      "required": ["user_id", "channel"],
      "additionalProperties": false
    },
    "message": {
      "type": "string"
    }
  },
  "required": ["receiver", "message"],
  "additionalProperties": false
}
```

这叫嵌套对象。

阶段 3 前期我们先少用复杂嵌套，先把简单对象掌握牢。

## schema 是给谁看的

schema 同时给三类对象看：

### 1. 给模型看

模型根据 schema 判断：

- 这个工具要什么参数。
- 参数是什么类型。
- 哪些字段必须有。
- 哪些值可以选。

### 2. 给开发者看

开发者看 schema 就知道：

- 工具契约是什么。
- 后端要校验什么。
- 测试要覆盖哪些合法和非法参数。

### 3. 给程序看

程序可以用 schema 做自动校验，或者从 Pydantic 模型生成 schema。

但在我们的项目里，真正落地时会更偏向：

```text
Pydantic 模型负责后端校验。
Pydantic 生成 JSON Schema 给模型看。
```

## JSON Schema 和 Pydantic 的关系

你可以这样理解：

```text
JSON Schema 是通用规则格式。
Pydantic 是 Python 里的数据校验工具。
```

两者关系：

```text
Pydantic BaseModel
-> 可以生成 JSON Schema
-> JSON Schema 可以给模型当工具参数说明
```

例如 Pydantic 模型：

```python
from pydantic import BaseModel, Field


class QueryOrderArgs(BaseModel):
    order_id: str = Field(description="订单编号，例如 A1001")
```

可以生成类似这样的 schema：

```json
{
  "properties": {
    "order_id": {
      "description": "订单编号，例如 A1001",
      "title": "Order Id",
      "type": "string"
    }
  },
  "required": ["order_id"],
  "title": "QueryOrderArgs",
  "type": "object"
}
```

注意：

```text
Pydantic 生成的 schema 可能会带 title 等额外字段。
这通常没问题，但我们要理解核心字段仍然是 type/properties/required。
```

后面写代码时，我们会让 Pydantic 同时做两件事：

1. 生成工具参数 schema，给模型看。
2. 校验模型返回的 arguments，保护后端。

## 为什么 schema 不能替代后端校验

这是本节最重要的工程结论。

你不能以为：

```text
我已经把 JSON Schema 发给模型了，所以模型一定会按 schema 返回。
```

不可以。

原因：

- 模型可能输出缺字段。
- 模型可能输出错类型。
- 模型可能输出额外字段。
- 模型可能选错 enum。
- 不同模型或兼容接口对 schema 的遵循程度可能不同。
- 即使模型输出格式正确，也不代表业务上允许执行。

所以正确流程是：

```text
把 JSON Schema 发给模型
-> 模型返回 tool arguments
-> Python 用 Pydantic 校验 arguments
-> 校验通过后，再检查权限、确认、幂等
-> 再调用 Java API
```

schema 是说明书。

Pydantic 校验是门卫。

Java 业务规则是最终裁判。

## 工具参数设计原则

### 1. 参数越少越好

不要一开始设计很大的工具。

差的设计：

```text
handle_order_problem(order_id, user_id, phone, address, payment_info, action, reason, note, priority, internal_tag)
```

问题是：

- 参数太多。
- 容易泄露敏感信息。
- 模型容易填错。
- 后端难校验。
- 工具职责不清楚。

更好的设计：

```text
query_order(order_id)
create_ticket_draft(order_id, category, summary, urgency)
```

一个工具只做一件事。

### 2. 参数名要稳定

不要今天叫 `order_id`，明天叫 `orderNo`，后天叫 `order_number`。

统一用一种命名方式。

我们后面 Python 项目里优先用：

```text
snake_case
```

例如：

```text
order_id
ticket_id
user_id
need_human_review
```

### 3. 字段描述要具体

差的描述：

```json
{
  "description": "订单"
}
```

好的描述：

```json
{
  "description": "订单编号，例如 A1001。不要填写手机号、用户名或商品编号。"
}
```

### 4. 能用 enum 就用 enum

如果后端只接受固定值，就不要让模型自由发挥。

例如：

```json
{
  "category": {
    "type": "string",
    "enum": ["shipping_delay", "refund", "complaint", "other"]
  }
}
```

比让模型随便写：

```text
催发货
物流问题
延迟发货
快递慢
```

更稳定。

### 5. 敏感字段不要放进工具参数

不要让模型生成这些参数：

```text
api_key
password
access_token
id_card
full_phone
payment_account
database_url
```

如果业务必须用某些敏感信息，也应该由后端自己从安全位置读取，而不是让模型传。

### 6. 写操作参数要更严格

查询工具可以稍微简单。

写操作工具必须更严格。

例如创建工单至少要考虑：

- `order_id`。
- `category`。
- `summary`。
- `urgency`。
- 用户确认状态。
- 幂等键。

但注意：确认状态和幂等键通常不应该由模型随便生成，而应该由后端控制。

## 常见错误

### 错误 1：忘记写 `required`

错误 schema：

```json
{
  "type": "object",
  "properties": {
    "order_id": {
      "type": "string"
    }
  }
}
```

这没有要求 `order_id` 必填。

应该写：

```json
{
  "required": ["order_id"]
}
```

### 错误 2：不限制 enum

错误 schema：

```json
{
  "urgency": {
    "type": "string"
  }
}
```

模型可能返回：

```text
urgent
very_high
特别急
紧急
```

更好的 schema：

```json
{
  "urgency": {
    "type": "string",
    "enum": ["low", "normal", "high"]
  }
}
```

### 错误 3：允许模型传多余字段

模型可能多传：

```json
{
  "order_id": "A1001",
  "force": true,
  "admin": true
}
```

工具参数里通常不应该接受这种字段。

可以用：

```json
{
  "additionalProperties": false
}
```

后端 Pydantic 也要配置为禁止或忽略额外字段，具体策略后面写代码时再定。

### 错误 4：把业务权限交给 schema

schema 能判断类型和结构。

schema 不能判断：

```text
订单 A1001 是否属于当前用户。
这个用户是否能创建投诉工单。
这个订单是否已经关闭。
```

这些必须由 Java 业务服务判断。

### 错误 5：字段描述太模糊

模糊描述：

```json
{
  "summary": {
    "type": "string",
    "description": "描述"
  }
}
```

更好的描述：

```json
{
  "summary": {
    "type": "string",
    "description": "用一句话概括用户问题，避免包含身份证号、完整手机号、API key 等敏感信息。"
  }
}
```

## 以后在项目里怎么用

后面真正写代码时，我们会这样走：

```text
定义 Pydantic 参数模型
-> 生成 JSON Schema
-> 注册工具定义
-> 模型返回 tool call
-> 用同一个 Pydantic 模型校验 arguments
-> 调用 fake tool 或 Java mock API
```

例如：

```python
class QueryOrderArgs(BaseModel):
    order_id: str = Field(description="订单编号，例如 A1001")
```

以后它会同时服务两个方向：

```text
给模型看：QueryOrderArgs.model_json_schema()
给后端校验：QueryOrderArgs.model_validate(arguments)
```

这样可以避免写两套规则。

## 本节练习

### 练习 1：判断字段类型

请判断下面字段应该用什么 JSON Schema 类型：

1. `order_id = "A1001"`
2. `need_human_review = true`
3. `retry_count = 3`
4. `score = 0.87`
5. `order_ids = ["A1001", "A1002"]`

参考答案：

1. `string`
2. `boolean`
3. `integer`
4. `number`
5. `array`，并且 `items.type` 应该是 `string`

### 练习 2：补全查询订单 schema

请补全这个 schema，让 `order_id` 必填，并且不允许多余字段。

题目：

```json
{
  "type": "object",
  "properties": {
    "order_id": {
      "type": "string",
      "description": "订单编号，例如 A1001"
    }
  }
}
```

参考答案：

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

### 练习 3：给工单紧急程度加 enum

题目：`urgency` 只能是 `low`、`normal`、`high`，请写出字段 schema。

参考答案：

```json
{
  "type": "string",
  "enum": ["low", "normal", "high"],
  "description": "工单紧急程度。普通问题用 normal，明确投诉或长时间未处理用 high。"
}
```

### 练习 4：判断哪些参数应该拒绝

schema：

```json
{
  "type": "object",
  "properties": {
    "order_id": {
      "type": "string"
    },
    "urgency": {
      "type": "string",
      "enum": ["low", "normal", "high"]
    }
  },
  "required": ["order_id", "urgency"],
  "additionalProperties": false
}
```

判断下面哪些合法：

1. `{"order_id": "A1001", "urgency": "normal"}`
2. `{"order_id": 1001, "urgency": "normal"}`
3. `{"order_id": "A1001", "urgency": "urgent"}`
4. `{"order_id": "A1001"}`
5. `{"order_id": "A1001", "urgency": "high", "admin": true}`

参考答案：

1. 合法。
2. 不合法，`order_id` 应该是字符串。
3. 不合法，`urgent` 不在 enum 里。
4. 不合法，缺少必填字段 `urgency`。
5. 不合法，`additionalProperties: false` 不允许 `admin`。

## 自测问题

### 1. JSON 和 JSON Schema 有什么区别？

答案：

JSON 是实际数据；JSON Schema 是描述和约束 JSON 数据结构的规则。

### 2. `properties` 和 `required` 有什么区别？

答案：

`properties` 描述对象里有哪些字段以及字段类型；`required` 规定哪些字段必须出现。只写在 `properties` 里不代表必填。

### 3. `enum` 适合用在什么场景？

答案：

适合后端只接受固定选项的字段，例如工单类型、紧急程度、状态、渠道等。它能限制模型输出固定值，减少自由发挥。

### 4. 为什么建议工具参数里写 `additionalProperties: false`？

答案：

因为工具调用参数要可控，不希望模型多传未知字段，例如 `admin`、`force` 这类危险或无意义字段。拒绝多余字段能让后端更安全、更容易测试。

### 5. JSON Schema 能不能替代 Pydantic 校验？

答案：

不能。JSON Schema 可以给模型说明参数结构，也可以做某些格式校验，但模型输出仍然是不可信输入。后端仍然要用 Pydantic 校验 arguments，再做权限、确认、幂等和业务规则判断。

### 6. Pydantic 和 JSON Schema 的关系是什么？

答案：

Pydantic 是 Python 的数据校验工具；JSON Schema 是通用的数据结构描述格式。Pydantic 模型可以生成 JSON Schema，给模型作为工具参数说明，同时 Pydantic 模型也可以校验模型返回的参数。

## 本节小结

本节最重要的是掌握这条链路：

```text
工具参数需要规则
-> JSON Schema 描述规则
-> 模型根据 schema 生成 arguments
-> 后端用 Pydantic 校验 arguments
-> 校验通过后才可能调用业务工具
```

你现在要能看懂并写出这种基础 schema：

```json
{
  "type": "object",
  "properties": {
    "order_id": {
      "type": "string",
      "description": "订单编号，例如 A1001"
    },
    "urgency": {
      "type": "string",
      "enum": ["low", "normal", "high"]
    }
  },
  "required": ["order_id", "urgency"],
  "additionalProperties": false
}
```

下一节我们会把这一节和第 2 阶段的结构化输出放在一起比较：

```text
结构化输出 vs Tool Calling
```

你会看到两者都可能用 JSON Schema / Pydantic，但目的不一样。

## 参考资料

- [OpenAI Function Calling Guide](https://developers.openai.com/api/docs/guides/function-calling)
- [JSON Schema：Creating your first schema](https://json-schema.org/learn/getting-started-step-by-step)
- [JSON Schema：Object](https://json-schema.org/understanding-json-schema/reference/object)
- [JSON Schema：Enumerated values](https://json-schema.org/understanding-json-schema/reference/enum)
- [Pydantic：JSON Schema](https://pydantic.dev/docs/validation/latest/concepts/json_schema/)
