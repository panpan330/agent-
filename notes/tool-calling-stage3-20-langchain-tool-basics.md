# 阶段 3 第 20 节：LangChain Tool 基础

> 本节结论：LangChain Tool 是把一个后端能力包装成“模型和框架能理解的工具对象”。它包含工具名、描述、参数 schema 和执行函数。包装成 LangChain Tool 不代表模型可以绕过后端直接操作业务系统；真正能不能执行、参数怎么校验、是否需要确认、错误怎么处理，仍然由我们的后端边界控制。

## 生成笔记前的教学复核

本节必须满足这些教学要求：

```text
1. 先讲清 Tool 是什么，再讲 LangChain Tool。
2. 讲清普通 Python 函数、项目 ToolDefinition、LangChain StructuredTool 的区别。
3. 讲清 @tool、StructuredTool、args_schema、description、name 分别解决什么问题。
4. 讲清为什么复用 QueryOrderArgs 作为 LangChain Tool 的 args_schema。
5. 讲清本节只学习“包装工具”和“手动调用工具”，不让模型自动调用工具。
6. 讲清 LangChain Tool 不替代权限、确认、幂等、Pydantic 校验和错误映射。
7. 新增代码要讲清楚每层职责，但不重复讲 query_order 旧逻辑。
8. 测试只讲关键风险，不逐行展开。
```

## 本节一句话定位

第 20 节是在第 19 节 ChatModel 基础上，学习如何把已有的后端工具函数包装成 LangChain Tool，为后续让 ChatModel 看到工具定义、返回工具调用请求做准备。

## 本节解决的真实问题

前面我们已经有一个后端工具：

```text
query_order
```

它当前已经具备：

```text
工具参数模型 QueryOrderArgs
工具返回模型 QueryOrderResult
后端工具注册表 TOOL_REGISTRY
工具权限守卫 authorize_tool_call()
Java mock API 调用
Pydantic 返回值校验
错误映射
测试 fake
```

但 LangChain 并不知道这些东西。

如果以后要让 LangChain 的模型或 Agent 使用这个工具，LangChain 需要看到一种它认识的对象：

```text
LangChain Tool
```

所以本节要解决的问题是：

```text
如何在不推翻现有 query_order 工具链路的前提下，
把它包装成 LangChain 能理解的 Tool。
```

本节新增两个学习接口：

```text
GET  /tools/langchain
POST /tools/langchain/query-order
```

它们只用于学习和验证：

```text
GET  /tools/langchain             -> 查看 LangChain Tool 元数据
POST /tools/langchain/query-order -> 手动调用包装后的 query_order Tool
```

本节不做：

```text
不让模型自动选择工具
不做 Agent 循环
不做多工具并行
不开放写操作 Tool 给模型
不取消现有工具注册表和权限守卫
```

## 本节新增能力

学完后你应该能做到：

- 能解释 LangChain Tool 是什么；
- 能说清普通函数、`ToolDefinition`、`StructuredTool` 的区别；
- 能解释 `name`、`description`、`args_schema` 为什么重要；
- 能知道 `@tool` 和 `StructuredTool.from_function()` 的基本区别；
- 能看懂为什么本项目复用 `QueryOrderArgs` 做工具参数 schema；
- 能解释为什么包装成 Tool 不等于让模型直接执行业务操作；
- 能手动调用一个 LangChain Tool；
- 能解释本节和下一节 `bind_tools()` 的关系。

## 和上一节的区别

第 19 节学的是：

```text
ChatModel 怎么调用模型：messages -> model.invoke() -> AIMessage
```

第 20 节学的是：

```text
怎么把后端能力包装成模型可识别的工具对象。
```

简单说：

```text
第 19 节：模型怎么说话
第 20 节：工具怎么被描述给模型
```

## 基础知识铺垫

### 1. 什么是工具

工具就是模型本身不会做、但外部系统可以做的能力。

例如模型可以读懂一句话：

```text
帮我查一下订单 A1001
```

但模型自己不能真的查业务数据库。

真正能查订单的是：

```text
后端函数
Java 业务服务
数据库查询
第三方 API
内部系统接口
```

所以工具的本质是：

```text
把外部能力接到 AI 应用里。
```

### 2. 为什么模型需要工具

模型只靠自身参数，通常只能回答训练时学到的通用知识。

但真实业务问题经常需要实时数据：

```text
订单当前状态
工单是否已创建
用户权限
库存数量
物流轨迹
付款状态
```

这些信息不在模型脑子里，必须查业务系统。

这就是工具调用的价值：

```text
模型负责理解用户意图
后端工具负责访问真实系统
```

### 3. 工具不是让模型直接操作系统

这点必须反复强调。

正确链路是：

```text
模型提出工具调用请求
后端校验工具名和参数
后端检查权限和风险
后端执行工具
后端把结果交回模型或直接返回
```

错误理解是：

```text
模型想调什么就调什么
模型给什么参数就信什么
模型决定是否退款、创建工单、修改订单
```

我们项目一直坚持：

```text
模型只能提出请求
后端才有执行权
```

### 4. 什么是 LangChain Tool

LangChain Tool 是 LangChain 对外部能力的抽象。

一个 LangChain Tool 通常包含：

```text
name：工具名
description：工具描述
args_schema：参数 schema
callable：真正执行的函数
```

换句话说，LangChain Tool 既是：

```text
给模型看的工具说明书
```

也是：

```text
给框架执行的函数包装器
```

这就是它和普通函数最大的区别。

### 5. 普通 Python 函数和 LangChain Tool 的区别

普通 Python 函数像这样：

```python
def query_order(order_id: str) -> dict:
    ...
```

它对 Python 程序员来说很清楚，但对模型来说不够清楚。

模型还需要知道：

```text
这个函数叫什么名字
它什么时候应该被用
参数是什么结构
每个参数是什么意思
哪些参数必填
返回大概是什么
```

LangChain Tool 就是把这些信息包装起来。

### 6. 什么是工具名 name

工具名是模型或框架识别工具的标识。

例如：

```text
query_order
```

官方文档建议工具名使用类似 `snake_case` 的形式，避免空格和特殊字符，因为不同模型提供商可能对工具名有兼容要求。

我们项目里的工具名也一直使用：

```text
query_order
create_ticket
refund_order
```

这说明我们前面设计的命名方式和 LangChain 生态是兼容的。

### 7. 什么是 description

description 是给模型看的工具说明。

它要回答：

```text
这个工具能做什么？
什么时候应该用？
有什么限制？
```

例如：

```text
查询订单状态和物流摘要，只读取订单信息，不修改业务数据。
```

这句话里有两个关键信息：

```text
能做：查询订单状态和物流摘要
不能做：不修改业务数据
```

好的工具描述应该简短、准确、边界清楚。

坏的工具描述会导致模型误用工具，例如：

```text
处理订单问题
```

这太模糊，模型不知道它是查订单、改订单、退款，还是创建工单。

### 8. 什么是 args_schema

`args_schema` 是工具参数结构。

它告诉模型和框架：

```text
这个工具需要哪些参数
参数类型是什么
参数是否必填
参数有没有描述
参数有没有格式限制
```

本项目的订单查询参数是：

```python
class QueryOrderArgs(BaseModel):
    order_id: str
```

并且有约束：

```text
非空
最长 64
只能包含字母、数字、下划线、短横线
自动去掉前后空格
不允许多余字段
```

这比只写一个普通 `order_id: str` 更安全。

### 9. 为什么 args_schema 用 Pydantic

Pydantic 的优势是：

```text
既能生成 JSON Schema
又能做运行时校验
还能作为项目内部类型
```

我们已经在前面反复使用 Pydantic：

```text
请求模型
响应模型
结构化输出
工具参数
工具返回结果
工单创建参数
```

现在 LangChain Tool 也可以复用 Pydantic 模型作为 `args_schema`。

这意味着：

```text
项目已有的参数边界不会因为引入 LangChain 而丢失。
```

### 10. 什么是 @tool

`@tool` 是 LangChain 提供的装饰器。

最简单写法类似：

```python
from langchain.tools import tool

@tool
def search_database(query: str) -> str:
    """Search database by query."""
    ...
```

它会把一个普通 Python 函数包装成 LangChain Tool。

默认情况下：

```text
函数名 -> tool name
函数 docstring -> tool description
类型提示 -> 参数 schema
```

这很方便，但也有一个风险：

```text
如果函数名、docstring、类型提示写得不严谨，工具描述也会不严谨。
```

### 11. 什么是 StructuredTool

`StructuredTool` 是 LangChain 里更明确的结构化工具对象。

它适合这种场景：

```text
你已经有明确的 Pydantic 参数模型
你想显式指定 name、description、args_schema
你想把已有业务函数包装成工具
```

本节我们使用：

```python
StructuredTool.from_function(...)
```

原因是我们已经有：

```text
TOOL_REGISTRY 里的 name 和 description
QueryOrderArgs 作为 args_schema
已有 query_order() 业务函数
```

所以用 `StructuredTool.from_function()` 更符合当前项目结构。

## 本节主题系统讲解

### 1. LangChain Tool 在工具调用链路里的位置

完整工具调用链路可以拆成几层：

```text
工具描述层：告诉模型有哪些工具、参数是什么
模型决策层：模型判断是否请求工具
后端校验层：校验工具名、参数、权限、风险
工具执行层：调用 Java API 或业务函数
结果回传层：把工具结果交给模型总结或直接返回
```

LangChain Tool 主要覆盖：

```text
工具描述层
一部分工具执行包装层
```

它不应该覆盖：

```text
业务权限
写操作确认
幂等规则
统一错误码
审计日志
用户身份判断
```

### 2. 我们已有 ToolDefinition 和 LangChain Tool 的关系

当前项目已有：

```python
ToolDefinition(
    name="query_order",
    description="查询订单状态和物流摘要，只读取订单信息，不修改业务数据。",
    access_level=ToolAccessLevel.READ,
    requires_confirmation=False,
    enabled=True,
    argument_schema=get_query_order_args_json_schema(),
)
```

这个 `ToolDefinition` 是我们项目自己的工具定义。

它包含 LangChain Tool 没有直接负责的业务信息：

```text
access_level
requires_confirmation
enabled
```

LangChain Tool 更关心：

```text
name
description
args_schema
callable
```

所以二者不是谁替代谁，而是分工不同：

```text
ToolDefinition：项目业务边界
LangChain Tool：框架可识别的工具包装
```

### 3. 为什么不直接把 create_ticket 也包装成 LangChain Tool

因为 `create_ticket` 是写操作。

它会：

```text
创建客服工单
写入业务系统
产生业务效果
```

我们前面已经学过：

```text
写操作必须先确认
确认计划必须绑定操作者和参数
执行要幂等
```

如果现在直接把 `create_ticket` 包成 LangChain Tool，让模型可以自动请求执行，就会破坏学习边界。

所以本节只包装：

```text
query_order
```

因为它是只读工具。

### 4. 为什么本节还不 bind_tools()

`bind_tools()` 是把 Tool 绑定到 ChatModel，让模型在调用时可以返回工具调用请求。

这会进入下一层知识：

```text
ChatModel + Tools
模型返回 tool_calls
后端解析 tool_calls
后端执行工具
把 ToolMessage 回传模型
```

这些内容我们以前手写过，但还没有用 LangChain 表达。

本节只学：

```text
怎么创建 Tool 对象
怎么看 Tool 元数据
怎么手动 invoke Tool
```

下一节或后续才适合进入：

```text
bind_tools()
```

这样学习层次更清楚。

### 5. 为什么新增 /tools/langchain

`GET /tools/langchain` 用来观察 LangChain Tool 的元数据。

它让你看到：

```text
Tool name 是什么
Tool description 是什么
Tool args_schema 是什么
```

这和前面直接看代码不同。

通过接口看元数据，你更容易理解：

```text
模型能看到的工具说明大概长什么样
```

### 6. 为什么新增 /tools/langchain/query-order

`POST /tools/langchain/query-order` 用来手动调用包装后的 LangChain Tool。

这个接口不是生产必需接口，而是学习验证接口。

它验证：

```text
QueryOrderArgs 请求进来
-> FastAPI/Pydantic 校验
-> StructuredTool.invoke()
-> 内部调用已有 query_order
-> 返回 QueryOrderResponse
```

这样你能看懂：

```text
LangChain Tool 可以像普通对象一样被手动调用
不一定非要等 Agent 调用
```

## 最小心智模型

本节最小链路是：

```text
已有 query_order(arguments)
-> 包装成 StructuredTool
-> Tool 暴露 name / description / args_schema
-> 手动 tool.invoke({"order_id": "A1001"})
-> 内部仍然走 authorize_tool_call + QueryOrderArgs + query_order
-> 返回 QueryOrderResult
```

一句话记忆：

```text
LangChain Tool 是“带说明书和参数 schema 的函数包装器”。
```

## 当前项目如何落地

本节新增和修改了这些文件：

```text
projects/ai-service/app/tools/langchain_tools.py
projects/ai-service/app/schemas/tool.py
projects/ai-service/app/routers/tools.py
projects/ai-service/tests/test_langchain_tools.py
projects/ai-service/tests/test_tools_api.py
notes/tool-calling-stage3-20-langchain-tool-basics.md
README.md
docs/learning-progress.md
docs/learning-resources.md
projects/ai-service/README.md
```

新增能力：

```text
创建 query_order 的 LangChain StructuredTool
查看 LangChain Tool 元数据
手动调用 LangChain Tool
用测试 fake 隔离真实 Java 服务
```

## 关键代码讲解

### 1. create_query_order_langchain_tool()

文件：

```text
projects/ai-service/app/tools/langchain_tools.py
```

核心逻辑：

```python
def create_query_order_langchain_tool(...):
    definition = get_tool_definition("query_order")

    def _query_order(order_id: str) -> dict[str, Any]:
        authorize_tool_call("query_order")
        arguments = QueryOrderArgs(order_id=order_id)
        result = query_order(arguments, client=client, settings=settings)
        return result.model_dump(mode="json")

    return StructuredTool.from_function(
        _query_order,
        name=definition.name,
        description=definition.description,
        args_schema=QueryOrderArgs,
    )
```

它有几个关键点。

第一，工具名和描述来自项目自己的 `ToolDefinition`：

```text
name=definition.name
description=definition.description
```

这避免出现两套工具描述。

第二，执行前仍然调用：

```text
authorize_tool_call("query_order")
```

这说明 LangChain Tool 没有绕过后端权限守卫。

第三，参数仍然进入：

```text
QueryOrderArgs(order_id=order_id)
```

这说明 LangChain 的参数 schema 和项目 Pydantic 校验保持一致。

第四，最终仍然调用已有：

```text
query_order(...)
```

这说明本节不是重写工具业务逻辑，而是包装已有工具。

### 2. get_langchain_tool_metadata()

核心逻辑：

```python
def get_langchain_tool_metadata(tool):
    return {
        "name": tool.name,
        "description": tool.description,
        "args_schema": tool.args,
    }
```

它的作用是把 LangChain Tool 中对学习最重要的字段提取出来。

我们不把整个 `StructuredTool` 对象直接返回给 API，因为它不是 JSON 响应模型。

### 3. list_model_callable_langchain_tools()

当前只返回：

```text
query_order
```

原因是：

```text
本节只开放只读工具
create_ticket 是写操作，不能在本节暴露给模型
refund_order 是敏感操作，当前禁用
```

这符合我们之前学过的工具权限边界。

### 4. LangChainToolInfo

文件：

```text
projects/ai-service/app/schemas/tool.py
```

新增：

```python
class LangChainToolInfo(BaseModel):
    name: str
    description: str
    args_schema: dict[str, Any]
```

它是接口响应模型。

它解决的是：

```text
把 LangChain Tool 元数据以稳定 JSON 格式返回给学习接口
```

### 5. GET /tools/langchain

文件：

```text
projects/ai-service/app/routers/tools.py
```

接口作用：

```text
列出当前模型可见的 LangChain Tool 元数据
```

返回示例大概是：

```json
{
  "tools": [
    {
      "name": "query_order",
      "description": "查询订单状态和物流摘要，只读取订单信息，不修改业务数据。",
      "args_schema": {
        "order_id": {
          "description": "Order id to query, for example A1001.",
          "title": "Order Id",
          "type": "string"
        }
      }
    }
  ]
}
```

这里你能看到 Tool 的三个核心信息：

```text
name
description
args_schema
```

### 6. POST /tools/langchain/query-order

接口作用：

```text
手动调用包装后的 query_order LangChain Tool
```

它的输入仍然是：

```text
QueryOrderArgs
```

它的输出仍然是：

```text
QueryOrderResponse
```

这很重要：

```text
引入 LangChain Tool 之后，API 边界没有变
```

变的是内部执行路径：

```text
原来：router -> query_order()
现在：router -> StructuredTool.invoke() -> query_order()
```

## 重要测试说明

本节新增的测试主要验证四件事。

第一，Tool 元数据正确：

```text
tool.name == "query_order"
tool.description 来自 ToolDefinition
tool.args_schema is QueryOrderArgs
```

第二，Tool 调用仍然复用旧逻辑：

```text
tool.invoke({"order_id": " A1002 "})
```

会去掉空格，调用 fake client，并返回经过 Pydantic 校验的结果。

第三，接口不访问真实 Java 服务：

```text
测试用 dependency_overrides 注入 fake LangChain Tool
```

这延续第 17 节学过的测试隔离原则。

第四，参数校验仍然生效：

```text
order_id = "A 1001"
```

会被 `QueryOrderArgs` 拒绝，返回统一 `VALIDATION_ERROR`。

## 常见误区

### 误区 1：LangChain Tool 等于模型已经会调用工具

不对。

创建 Tool 只是准备工具对象。

模型要看到工具，还需要后续：

```text
bind_tools()
```

或者 Agent。

### 误区 2：Tool 的 description 随便写也行

不对。

description 会影响模型什么时候使用工具。描述越模糊，模型越容易误用。

### 误区 3：args_schema 只是给文档看的

不对。

args_schema 不只是文档，它也参与输入结构约束。用 Pydantic 模型作为 args_schema，可以复用项目里的参数校验。

### 误区 4：包装成 LangChain Tool 后就不需要 ToolDefinition

不对。

`ToolDefinition` 负责项目业务边界，比如风险等级、是否启用、是否需要确认。

LangChain Tool 负责框架包装。

### 误区 5：只读工具和写操作工具可以一样处理

不对。

只读工具可以更早开放给模型尝试。

写操作必须先有确认、操作者绑定、参数绑定、幂等和审计。

### 误区 6：Tool.invoke() 和 model.invoke() 是一回事

不对。

`model.invoke()` 是调用模型。

`tool.invoke()` 是调用工具函数。

它们都是 LangChain 生态里常见的调用方式，但调用对象完全不同。

## 手动验证方式

启动 AI 服务：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run uvicorn app.main:app --reload
```

查看 LangChain Tool 元数据：

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri "http://127.0.0.1:8000/tools/langchain"
```

手动调用 LangChain query_order Tool：

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/tools/langchain/query-order" `
  -ContentType "application/json" `
  -Body '{"order_id":"A1001"}'
```

注意：

```text
第二个请求会通过 Python AI 服务调用 Java mock 服务。
如果本机没有启动 java-mock-service，会返回上游连接错误。
```

启动 Java mock 服务：

```powershell
cd D:\wendang\java+python+ai\projects\java-mock-service
uv run uvicorn app.main:app --reload --port 8001
```

## 练习与参考答案

### 练习 1：解释 LangChain Tool

题目：

用 3 句话解释 LangChain Tool 是什么。

参考答案：

```text
LangChain Tool 是对外部能力的包装。它包含工具名、描述、参数 schema 和执行函数，让模型和框架知道这个工具能做什么、需要什么参数、如何调用。它只是框架层包装，不替代后端权限、校验、确认和幂等。
```

### 练习 2：区分三种东西

题目：

说明普通函数、`ToolDefinition`、`StructuredTool` 的区别。

参考答案：

```text
普通函数负责真正执行业务逻辑。
ToolDefinition 是项目自己的工具定义，包含风险等级、是否启用、是否需要确认等业务边界。
StructuredTool 是 LangChain 的工具对象，包含 name、description、args_schema 和 callable，方便模型/框架识别和调用。
```

### 练习 3：为什么复用 QueryOrderArgs

题目：

为什么本节把 `QueryOrderArgs` 作为 LangChain Tool 的 `args_schema`？

参考答案：

```text
因为 QueryOrderArgs 已经定义了 order_id 的类型、长度、格式、去空格规则和禁止多余字段。复用它可以避免出现两套参数定义，也能保证 LangChain Tool 和项目原有工具调用使用同一套校验边界。
```

### 练习 4：判断哪些工具能暴露

题目：

下面哪些工具适合在当前阶段包装成模型可见的 LangChain Tool？

```text
A. query_order，只读查询订单
B. create_ticket，创建客服工单
C. refund_order，发起退款
```

参考答案：

```text
当前阶段只适合 A。

query_order 是只读工具，风险较低。
create_ticket 是写操作，必须先有用户确认和幂等控制。
refund_order 是敏感操作，当前禁用，不应暴露给模型。
```

### 练习 5：解释为什么本节不学 bind_tools

题目：

为什么本节只创建 Tool，不学习 `bind_tools()`？

参考答案：

```text
因为 bind_tools 会进入模型自动请求工具调用的阶段，涉及 AIMessage.tool_calls、后端执行工具、ToolMessage 回传模型等流程。本节目标是先理解 Tool 对象本身，包括 name、description、args_schema 和 invoke，下一节再学习如何把工具绑定给模型。
```

## 自测题与参考答案

### 自测 1

问题：LangChain Tool 至少包含哪些核心信息？

答案：

```text
name、description、args_schema 和执行函数。
```

### 自测 2

问题：`@tool` 默认会从哪里获取工具描述？

答案：

```text
默认从函数 docstring 获取工具描述。
```

### 自测 3

问题：为什么工具名建议使用 `snake_case`？

答案：

```text
因为不同模型提供商可能对工具名中的空格或特殊字符兼容性不好，snake_case 更稳定。
```

### 自测 4

问题：`StructuredTool.from_function()` 适合什么场景？

答案：

```text
适合已有明确函数、工具名、描述和 Pydantic args_schema，希望显式包装成 LangChain Tool 的场景。
```

### 自测 5

问题：本节新增的 `/tools/langchain/query-order` 是让模型自动调用工具吗？

答案：

```text
不是。它是学习用的手动调用接口，用来验证 StructuredTool.invoke() 的行为。
```

### 自测 6

问题：LangChain Tool 会自动处理业务权限吗？

答案：

```text
不会。业务权限仍然要由后端自己的 authorize_tool_call、确认机制、幂等机制等控制。
```

### 自测 7

问题：Tool 的 description 为什么重要？

答案：

```text
因为模型会根据 description 判断什么时候使用工具。描述不清会导致模型误用或不用工具。
```

### 自测 8

问题：`ToolDefinition` 能不能被 `StructuredTool` 完全替代？

答案：

```text
不能。ToolDefinition 里有 access_level、requires_confirmation、enabled 等项目业务边界，而 StructuredTool 主要是 LangChain 框架层工具包装。
```

### 自测 9

问题：本节为什么只包装 `query_order`？

答案：

```text
因为 query_order 是只读工具，风险较低。写操作和敏感操作需要更多安全边界，不适合当前阶段直接暴露。
```

### 自测 10

问题：下一节学习 `bind_tools()` 前，必须先理解什么？

答案：

```text
必须先理解 Tool 对象本身，包括工具名、描述、参数 schema、执行函数，以及后端安全边界不能丢。
```

## 本节真正学会了什么

本节真正要学会的是：

```text
LangChain Tool 是带 name、description、args_schema 和 callable 的函数包装器。
普通 Python 函数只负责执行，Tool 还要负责向模型描述自己。
项目 ToolDefinition 负责业务边界，StructuredTool 负责框架包装。
QueryOrderArgs 可以直接复用为 LangChain Tool 的 args_schema。
包装成 Tool 不等于允许模型自动执行工具。
后端权限、确认、幂等、Pydantic 校验和错误映射仍然必须保留。
```

如果你能说清下面这句话，就说明本节达标：

```text
我们不是把 query_order 重写成 LangChain 版本，而是把已有 query_order 用 StructuredTool 包起来，让 LangChain 能识别它，同时继续保留项目自己的工具注册表和安全边界。
```

## 本节参考资料

- [LangChain Tools](https://docs.langchain.com/oss/python/langchain/tools)
- [LangChain StructuredTool reference](https://reference.langchain.com/python/langchain-core/tools/structured/StructuredTool)
- [LangChain Models - Tool calling](https://docs.langchain.com/oss/python/langchain/models#tool-calling)

## 下一节学什么

下一节进入阶段 3 第 21 节：

```text
LangChain 结构化输出
```

`bind_tools()` 会放到后续工具调用封装里再学。下一节先按阶段表学习结构化输出，是为了把 LangChain 的“模型输出变成稳定结构”这条线补齐，再继续把工具调用链路往 LangChain 抽象上迁移。
