# 阶段 3 第 12 节：让模型决定是否调用工具

## 本节目标

前面我们已经有了：

```text
query_order 工具
-> 参数 QueryOrderArgs
-> 权限白名单 authorize_tool_call()
-> 幂等保护 Idempotency-Key
-> Python 调用 Java mock API
-> QueryOrderResult 结果校验
```

但是到上一节为止，工具还是我们手动调用的：

```text
POST /tools/query-order
```

真实 AI Agent 不是这样工作的。真实流程应该更接近：

```text
用户说：帮我查一下订单 A1001
-> 模型判断：这个问题需要查订单
-> 模型返回：我想调用 query_order，参数是 {"order_id":"A1001"}
-> 后端校验工具名和参数
-> 后端再决定是否真正执行工具
```

本节只完成中间最关键的一步：

```text
让模型决定是否需要调用工具。
```

注意，本节还不执行工具。执行工具以及把工具结果交回模型总结，放到下一节。

## 先记住一句话

```text
Tool Calling 不是模型直接执行代码，而是模型返回一个“工具调用请求”。
```

这个请求通常包含：

```json
{
  "name": "query_order",
  "arguments": {
    "order_id": "A1001"
  }
}
```

真正执行不执行，永远由后端决定。

这句话很重要。模型不能越过后端权限系统直接操作业务系统。模型只能提出意图，后端负责校验、授权、执行、记录日志、处理错误。

## 官方流程怎么描述 Tool Calling

OpenAI Function Calling 文档把流程拆成几步：

```text
1. 应用把 messages 和 tools 发给模型。
2. 模型判断是否需要调用工具。
3. 如果需要，模型返回 tool call。
4. 应用执行对应的工具函数。
5. 应用把工具结果再发给模型，让模型生成最终回答。
```

阿里云百炼 Qwen Function Calling 文档也是类似思路：

```text
定义工具
创建 messages
调用模型
根据模型返回执行工具函数
再让模型总结工具输出
```

本节只做到第 1、2、3 步：

```text
把工具定义给模型
让模型选择是否调用
解析模型返回的 tool_calls
```

第 4、5 步下一节做。

## 本节新增的接口

新增：

```text
POST /tool-decision
```

它的作用是教学用的：查看模型是否会请求工具。

请求体复用之前的 `ChatRequest`：

```json
{
  "message": "帮我查一下订单 A1001"
}
```

如果模型认为需要调用工具，响应类似：

```json
{
  "decision": "call_tool",
  "reply": null,
  "tool_call": {
    "name": "query_order",
    "arguments": {
      "order_id": "A1001"
    },
    "call_id": "call_001"
  }
}
```

如果模型认为不需要调用工具，响应类似：

```json
{
  "decision": "answer_directly",
  "reply": "请提供订单号后我再帮你查询。",
  "tool_call": null
}
```

这两个结果一定要分清：

| 结果 | 含义 | 当前是否执行工具 |
| --- | --- | --- |
| `answer_directly` | 模型认为不用工具，直接回答 | 不执行 |
| `call_tool` | 模型请求调用某个工具 | 本节仍然不执行，只展示意图 |

## 为什么本节不直接执行工具

因为你现在要学清楚 Tool Calling 的底层链路。

如果一上来就把所有步骤写到一个接口里，你会很容易混在一起：

```text
模型选择工具
后端校验工具名
后端校验参数
后端执行工具
工具结果再给模型
模型最终回答
```

这些是不同职责。

本节先只学：

```text
模型选择工具 + 后端解析和校验这个选择
```

下一节再学：

```text
后端执行工具 + 工具结果再交给模型总结
```

这样你能真正理解每一层的作用，而不是只会复制一段 Agent 代码。

## 本节新增和修改的关键文件

新增：

```text
projects/ai-service/app/schemas/tool_decision.py
projects/ai-service/app/services/tool_decision_service.py
projects/ai-service/tests/test_tool_decision_schema.py
projects/ai-service/tests/test_tool_decision_service.py
```

修改：

```text
projects/ai-service/app/tools/tool_registry.py
projects/ai-service/app/routers/chat.py
projects/ai-service/tests/fakes.py
projects/ai-service/tests/test_tool_registry.py
projects/ai-service/tests/test_chat_api.py
```

下面按业务代码详细讲。

## `ToolDecisionType`：为什么要定义决策枚举

文件：

```text
projects/ai-service/app/schemas/tool_decision.py
```

新增：

```python
class ToolDecisionType(StrEnum):
    ANSWER_DIRECTLY = "answer_directly"
    CALL_TOOL = "call_tool"
```

这表示模型决策只有两类：

```text
answer_directly  直接回答
call_tool        请求调用工具
```

为什么不直接用 `bool`，比如 `should_call_tool: true`？

因为枚举更清楚。以后如果增加更多决策类型，例如：

```text
ask_user_confirmation
need_more_information
reject_request
```

枚举会比一个布尔值更容易扩展。

布尔值只能表达：

```text
是 / 否
```

枚举可以表达：

```text
具体是哪一种状态
```

## `ToolCallCandidate`：模型请求调用的工具候选

新增：

```python
class ToolCallCandidate(BaseModel):
    name: str
    arguments: dict[str, Any]
    call_id: str | None = None
```

它表示模型返回的一个工具调用请求。

字段含义：

| 字段 | 含义 |
| --- | --- |
| `name` | 模型请求的工具名，例如 `query_order` |
| `arguments` | 模型给出的工具参数，例如 `{"order_id":"A1001"}` |
| `call_id` | 模型服务商返回的工具调用编号，不一定有 |

这里对 `name` 做了格式限制：

```python
pattern=r"^[a-z][a-z0-9_]*$"
```

意思是工具名必须类似：

```text
query_order
create_ticket
refund_order
```

不允许：

```text
QueryOrder
query-order
../delete
```

这不是主要安全防线，但它是第一层格式约束。真正的权限防线仍然是后端注册表和 `authorize_tool_call()`。

## `ToolDecisionResponse`：为什么响应里同时有 `reply` 和 `tool_call`

新增：

```python
class ToolDecisionResponse(BaseModel):
    decision: ToolDecisionType
    reply: str | None = None
    tool_call: ToolCallCandidate | None = None
```

设计规则是：

```text
decision = answer_directly 时，必须有 reply，不能有 tool_call
decision = call_tool 时，必须有 tool_call，不能有 reply
```

所以又加了：

```python
@model_validator(mode="after")
def validate_decision_shape(self) -> "ToolDecisionResponse":
    ...
```

这个校验器的作用是保证响应结构不自相矛盾。

错误例子：

```json
{
  "decision": "answer_directly",
  "reply": null,
  "tool_call": null
}
```

这不合理。说了直接回答，却没有回答。

另一个错误例子：

```json
{
  "decision": "call_tool",
  "reply": "我帮你查到了",
  "tool_call": {
    "name": "query_order",
    "arguments": {
      "order_id": "A1001"
    }
  }
}
```

这也不合理。本节还没执行工具，模型不能假装已经查到了结果。

## 工具注册表新增了“模型可见工具”

文件：

```text
projects/ai-service/app/tools/tool_registry.py
```

之前我们已经有：

```python
TOOL_REGISTRY
authorize_tool_call()
```

本节新增：

```python
def list_model_callable_tool_definitions() -> list[ToolDefinition]:
    return [
        definition
        for definition in list_tool_definitions()
        if definition.enabled
        and definition.access_level == ToolAccessLevel.READ
        and not definition.requires_confirmation
    ]
```

它的作用是筛选“可以暴露给模型选择的工具”。

当前注册表里有三个工具：

| 工具 | 风险等级 | 是否启用 | 是否需要用户确认 |
| --- | --- | --- | --- |
| `query_order` | `read` | 是 | 否 |
| `create_ticket` | `write` | 是 | 是 |
| `refund_order` | `sensitive` | 否 | 是 |

本节只暴露：

```text
query_order
```

原因：

```text
它是只读工具
它已经启用
它不需要用户确认
```

为什么不把 `create_ticket` 也给模型？

因为 `create_ticket` 是写操作。写操作代表会改变业务系统状态，例如创建工单、修改记录、发起流程。它必须有用户确认机制。本节还没学用户确认，所以不暴露给模型。

为什么不把 `refund_order` 给模型？

因为退款属于敏感操作，而且当前还是禁用状态。模型不能看到、不能请求、更不能执行。

这里体现了一个关键安全原则：

```text
模型能看到的工具越少越好。
```

只给当前任务真正需要的工具，不要把后端所有能力都暴露给模型。

## OpenAI Chat Completions 的工具定义形状

本节新增：

```python
def build_openai_chat_tool_definition(
    definition: ToolDefinition,
) -> dict[str, object]:
    return {
        "type": "function",
        "function": {
            "name": definition.name,
            "description": definition.description,
            "parameters": definition.argument_schema,
            "strict": True,
        },
    }
```

这会把我们自己的 `ToolDefinition` 转成模型 API 认识的工具格式。

大致结果是：

```json
{
  "type": "function",
  "function": {
    "name": "query_order",
    "description": "查询订单状态和物流摘要...",
    "parameters": {
      "type": "object",
      "properties": {
        "order_id": {
          "type": "string"
        }
      },
      "required": ["order_id"],
      "additionalProperties": false
    },
    "strict": true
  }
}
```

逐个字段解释：

| 字段 | 含义 |
| --- | --- |
| `type: "function"` | 告诉模型这是函数工具 |
| `function.name` | 工具名，模型返回 tool call 时会使用它 |
| `function.description` | 告诉模型什么时候应该用这个工具 |
| `function.parameters` | 工具参数 JSON Schema |
| `strict: true` | 要求模型尽量严格遵守 schema |

注意：`description` 会影响模型是否选择工具。

如果 description 写得含糊，例如：

```text
查询信息
```

模型就不容易知道什么时候调用。

更好的写法是明确边界：

```text
查询订单状态和物流摘要，只读取订单信息，不修改业务数据。
```

这样模型更容易知道：

```text
订单状态/物流问题 -> 可以调用 query_order
退款/创建工单/修改数据 -> 不能用 query_order 代替
```

## `ToolDecisionService` 的职责

文件：

```text
projects/ai-service/app/services/tool_decision_service.py
```

这个 service 的职责是：

```text
构造工具决策 prompt
把可见工具列表传给模型
读取模型响应
判断模型是否返回 tool_calls
校验工具名
解析 arguments
用 Pydantic 校验参数
返回 ToolDecisionResponse
```

它不负责：

```text
执行 query_order
调用 Java mock API
把工具结果总结成自然语言
处理用户确认
```

这些都属于后续步骤。

## 工具决策 prompt 做了什么

新增：

```python
TOOL_DECISION_SYSTEM_PROMPT = (...)
```

核心要求是：

```text
你是工具调用决策器
需要真实订单状态且有订单号时，优先请求 query_order
没有订单号时，不要调用工具
普通学习问题和闲聊，不要调用工具
不要编造订单号
不要请求未提供的工具
不要请求写入或敏感操作
```

为什么 prompt 里还要强调这些？

因为工具选择本身是模型推理行为。你要给模型明确任务边界。

但你也要记住：

```text
prompt 不是安全边界。
```

就算 prompt 写了“不要请求退款工具”，模型仍然可能返回：

```json
{
  "name": "refund_order",
  "arguments": {
    "order_id": "A1001"
  }
}
```

所以后端仍然必须用 `authorize_tool_call()` 拦住。

prompt 负责引导模型，后端代码负责安全。

## `build_tool_decision_messages`

新增：

```python
def build_tool_decision_messages(
    user_message: str,
    *,
    history: Sequence[ChatMessage] | None = None,
) -> list[dict[str, str]]:
    messages = build_multi_turn_messages(
        build_tool_decision_prompt(user_message),
        history=history,
        system_message=TOOL_DECISION_SYSTEM_PROMPT,
    )
    return serialize_chat_messages(messages)
```

这段代码复用了之前学过的多轮消息构造能力。

最终发给模型的结构是：

```text
system: 你是工具调用决策器...
history: 可选的历史 user/assistant 消息
user: 请判断下面这条用户消息是否需要调用后端工具...
```

为什么要支持 `history`？

因为用户可能这样说：

```text
用户：订单 A1001 有问题
助手：你想查询订单状态吗？
用户：对，查一下
```

最后一句“对，查一下”本身没有订单号，但结合历史就知道订单号是 `A1001`。

不过当前阶段你要注意：历史上下文会让模型更聪明，也会让风险更复杂。后面做正式 Agent 时，还要继续处理上下文长度、敏感信息和用户确认。

## 真正调用模型时多了两个参数

核心代码：

```python
completion = self._get_client().chat.completions.create(
    model=self.settings.llm_model,
    messages=messages,
    tools=list_model_callable_openai_tools(),
    tool_choice="auto",
)
```

和普通 `/chat` 对比，本节多了：

```python
tools=...
tool_choice="auto"
```

### `tools`

`tools` 是你交给模型的工具清单。

可以理解成告诉模型：

```text
你如果需要外部能力，只能从这些工具里选。
```

当前传进去的工具只有：

```text
query_order
```

### `tool_choice="auto"`

`tool_choice="auto"` 的意思是：

```text
由模型自己判断是否调用工具。
```

如果需要，模型会返回 `tool_calls`。

如果不需要，模型会返回普通 `content`。

所以我们后端必须同时处理两种情况：

```text
有 tool_calls -> 解析工具调用请求
没有 tool_calls -> 当作直接回答
```

## 模型返回 `tool_calls` 时是什么样

真实 SDK 对象大概可以理解成：

```text
completion
  choices[0]
    message
      content = None
      tool_calls = [
        {
          id: "call_xxx",
          type: "function",
          function: {
            name: "query_order",
            arguments: "{\"order_id\":\"A1001\"}"
          }
        }
      ]
```

注意这里最容易踩坑的点：

```text
function.arguments 通常是 JSON 字符串，不是 Python dict。
```

也就是它看起来像：

```python
'{"order_id":"A1001"}'
```

而不是：

```python
{"order_id": "A1001"}
```

所以本节必须先：

```python
json.loads(raw_arguments)
```

再交给 Pydantic。

## `extract_tool_decision` 的完整逻辑

核心函数：

```python
def extract_tool_decision(completion: Any) -> ToolDecisionResponse:
    message = extract_first_message(completion)
    tool_calls = extract_message_tool_calls(message)
    if not tool_calls:
        return ToolDecisionResponse(
            decision=ToolDecisionType.ANSWER_DIRECTLY,
            reply=extract_direct_reply(message),
        )
    ...
```

第一步，取出模型返回的 assistant message。

第二步，看有没有 `tool_calls`。

如果没有：

```text
说明模型选择直接回答。
```

于是读取：

```python
message.content
```

并返回：

```python
ToolDecisionResponse(
    decision=ToolDecisionType.ANSWER_DIRECTLY,
    reply=...
)
```

如果有 `tool_calls`：

```text
说明模型请求工具。
```

当前阶段只支持一个工具调用：

```python
if len(tool_calls) > 1:
    raise AppException(
        code="TOOL_DECISION_TOO_MANY_CALLS",
        ...
    )
```

为什么一次只支持一个？

因为你现在还在学习底层流程。多个工具调用会引入：

```text
并行调用
调用顺序
部分失败
多个工具结果如何合并
token 成本
日志追踪
```

这些后面可以学。当前先把一个工具调用吃透。

## 后端再次校验工具名

模型返回：

```python
tool_name = "query_order"
```

后端不会直接相信它，而是调用：

```python
definition = authorize_tool_call(tool_name.strip())
```

这一步会处理：

| 场景 | 错误 |
| --- | --- |
| 未知工具 | `TOOL_NOT_ALLOWED` |
| 禁用工具 | `TOOL_NOT_ALLOWED` |
| 写操作但没有用户确认 | `TOOL_CONFIRMATION_REQUIRED` |

这就是“模型只能提出请求，后端决定能不能执行”。

就算模型请求：

```text
delete_database
```

后端也会拒绝。

就算模型请求：

```text
create_ticket
```

当前也会因为需要用户确认而拒绝。

## 为什么参数还要 Pydantic 校验

模型可能返回：

```json
{
  "order_id": "A1001"
}
```

也可能返回：

```json
{
  "order_id": "A 1001"
}
```

第二个不符合我们之前定义的 `QueryOrderArgs`，因为订单号不允许中间有空格。

所以本节新增：

```python
def validate_tool_arguments(
    definition: ToolDefinition,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    if definition.name != "query_order":
        ...

    try:
        return QueryOrderArgs.model_validate(arguments).model_dump()
    except ValidationError as exc:
        raise AppException(
            code="TOOL_ARGUMENTS_VALIDATION_FAILED",
            ...
        ) from exc
```

这一步很重要：

```text
模型返回的 arguments 也是外部输入，必须校验。
```

不要以为传了 JSON Schema，模型就 100% 永远正确。

真实项目里依然要后端校验：

```text
字段是否存在
类型是否正确
格式是否正确
有没有额外字段
是否符合业务规则
```

JSON Schema 是告诉模型怎么填，Pydantic 是后端真正验收。

## 为什么 `arguments` 非法时返回 502

如果用户传入非法请求体，例如：

```json
{}
```

那是客户端请求错误，FastAPI 返回 422。

但如果模型服务返回了非法工具参数，例如：

```text
function.arguments = "{not-json"
```

这不是用户直接传错了请求体，而是我们依赖的模型服务返回了不符合预期的内容。

所以本节把它映射成：

```text
TOOL_ARGUMENTS_INVALID_JSON
HTTP 502
```

或者：

```text
TOOL_ARGUMENTS_VALIDATION_FAILED
HTTP 502
```

从 `ai-service` 视角看，这是上游模型响应不可用。

## 新增的 `/tool-decision` 路由

文件：

```text
projects/ai-service/app/routers/chat.py
```

新增依赖：

```python
def get_tool_decision_service(
    settings: Settings = Depends(get_settings),
) -> ToolDecisionService:
    return create_tool_decision_service(settings)
```

新增接口：

```python
@router.post("/tool-decision", response_model=ToolDecisionResponse)
def tool_decision(
    request: ChatRequest,
    tool_decision_service: ToolDecisionService = Depends(get_tool_decision_service),
) -> ToolDecisionResponse:
    logger.info(
        "tool_decision_requested message_length=%s history_size=%s",
        len(request.message),
        len(request.history),
    )
    return tool_decision_service.decide(
        request.message,
        history=request.history,
    )
```

这个接口做的事情很少：

```text
接收请求
记录消息长度和历史条数
调用 service.decide()
返回 ToolDecisionResponse
```

为什么 router 这么薄？

因为 router 主要负责 HTTP 层：

```text
路径
请求模型
响应模型
依赖注入
基础日志
```

真正业务逻辑放在 service 里：

```text
模型调用
工具定义
模型响应解析
参数校验
错误映射
```

这样更容易测试，也更容易维护。

## 测试 fake client 为什么也要改

文件：

```text
projects/ai-service/tests/fakes.py
```

以前 fake client 只会模拟：

```text
message.content
```

本节需要模拟：

```text
message.tool_calls
```

所以新增：

```python
def make_tool_call(
    name: str,
    arguments: dict[str, Any] | str,
    *,
    call_id: str = "call_001",
) -> object:
    ...
```

测试里可以这样构造一个模型工具调用：

```python
make_tool_call("query_order", {"order_id": "A1001"})
```

它会把参数转成模型常见的 JSON 字符串：

```python
'{"order_id":"A1001"}'
```

这样 service 测试就能覆盖真实场景：

```text
模型返回 tool_calls
arguments 是 JSON 字符串
后端 json.loads
后端 Pydantic 校验
后端返回 ToolDecisionResponse
```

自动化测试不需要真的请求 Qwen 或 OpenAI。

## 本节测试重点

本节新增和修改的测试主要覆盖：

| 测试文件 | 关注点 |
| --- | --- |
| `test_tool_decision_schema.py` | 决策响应模型是否合法 |
| `test_tool_decision_service.py` | 解析模型返回、校验工具名、校验参数、调用模型参数 |
| `test_tool_registry.py` | 只有安全只读工具暴露给模型 |
| `test_chat_api.py` | `/tool-decision` 接口请求响应是否正确 |

重点测试场景：

```text
模型直接回答
模型请求 query_order
模型请求未知工具
模型请求需要用户确认的写工具
模型返回非法 JSON arguments
模型返回不符合 QueryOrderArgs 的 arguments
模型一次返回多个 tool_calls
没有 API key 时不调用模型
```

## 当前可以怎么手动试

先启动 `ai-service`：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run uvicorn app.main:app --reload --port 8000
```

访问：

```text
http://127.0.0.1:8000/docs
```

调用：

```text
POST /tool-decision
```

请求体 1：

```json
{
  "message": "帮我查一下订单 A1001"
}
```

如果模型支持当前工具调用格式，预期会返回：

```json
{
  "decision": "call_tool",
  "reply": null,
  "tool_call": {
    "name": "query_order",
    "arguments": {
      "order_id": "A1001"
    },
    "call_id": "..."
  }
}
```

请求体 2：

```json
{
  "message": "FastAPI 是什么？"
}
```

预期更可能返回：

```json
{
  "decision": "answer_directly",
  "reply": "FastAPI 是一个 Python Web 框架...",
  "tool_call": null
}
```

请求体 3：

```json
{
  "message": "帮我查一下订单"
}
```

因为没有订单号，模型应该直接回答：

```json
{
  "decision": "answer_directly",
  "reply": "请提供订单号后我再帮你查询。",
  "tool_call": null
}
```

## 现在的完整链路到哪一步

本节后，链路变成：

```text
POST /tool-decision
-> ChatRequest 校验 message/history
-> ToolDecisionService.decide()
-> build_tool_decision_messages()
-> list_model_callable_openai_tools()
-> client.chat.completions.create(..., tools=..., tool_choice="auto")
-> extract_tool_decision()
-> authorize_tool_call(tool_name)
-> parse_tool_call_arguments()
-> QueryOrderArgs.model_validate(arguments)
-> ToolDecisionResponse
```

注意现在还没有：

```text
query_order 工具执行
Java mock API 调用
工具结果返回模型总结
最终客服回答
```

这些下一节继续。

## 本节容易混淆的点

### 1. `tools` 不是执行工具

`tools` 只是告诉模型：

```text
你可以请求这些工具。
```

它不会自动执行 Python 函数，也不会自动访问 Java 服务。

### 2. `tool_choice="auto"` 不是自动执行

`auto` 的意思是：

```text
模型自动决定是否返回 tool call。
```

不是：

```text
SDK 自动帮你调用工具。
```

### 3. `tool_calls` 是模型输出，不是可信业务事实

模型返回：

```json
{
  "name": "query_order",
  "arguments": {
    "order_id": "A1001"
  }
}
```

这只表示模型想查这个订单。

它不代表订单存在，也不代表用户有权限，也不代表参数一定合法。

### 4. JSON Schema 不能替代 Pydantic

JSON Schema 给模型看。

Pydantic 给后端验收。

两者要配合用，不要只靠其中一个。

### 5. 模型可见工具和后端注册工具不是一回事

后端注册表里可以有很多工具。

模型当前能看到的工具应该更少。

当前策略是：

```text
enabled=True
access_level=READ
requires_confirmation=False
```

所以只有 `query_order` 暴露给模型。

## 练习 1：判断是否应该调用工具

判断下面用户消息应该返回 `answer_directly` 还是 `call_tool`。

题目：

1. `帮我查一下订单 A1001 到哪了`
2. `FastAPI 是什么？`
3. `帮我查一下订单`
4. `订单 A1002 能创建工单吗？`
5. `给订单 A1001 直接退款`

### 练习 1 参考答案

1. `call_tool`。用户要查订单状态，并且提供了订单号。
2. `answer_directly`。这是知识解释问题，不需要业务系统数据。
3. `answer_directly`。缺少订单号，不能猜参数。
4. `call_tool`。需要先查订单信息，订单号明确。
5. 当前阶段应拒绝或直接说明不能直接退款，不能调用退款工具。退款属于敏感操作，当前不暴露给模型。

## 练习 2：判断工具是否应该暴露给模型

根据当前规则判断是否暴露：

```text
enabled=True
access_level=READ
requires_confirmation=False
```

题目：

| 工具 | enabled | access_level | requires_confirmation |
| --- | --- | --- | --- |
| `query_order` | true | read | false |
| `create_ticket` | true | write | true |
| `refund_order` | false | sensitive | true |
| `list_public_faq` | true | read | false |

### 练习 2 参考答案

应该暴露：

```text
query_order
list_public_faq
```

不应该暴露：

```text
create_ticket
refund_order
```

原因：

```text
create_ticket 是写操作并且需要用户确认。
refund_order 是敏感操作，而且当前禁用。
```

## 练习 3：分析 arguments 是否合法

`QueryOrderArgs` 要求：

```text
order_id 必须存在
order_id 是字符串
order_id 非空
order_id 只能包含字母、数字、下划线、短横线
```

判断下面参数是否合法：

1. `{"order_id":"A1001"}`
2. `{"order_id":"  A1001  "}`
3. `{"order_id":"A 1001"}`
4. `{"orderId":"A1001"}`
5. `{"order_id":"A1001","admin":true}`

### 练习 3 参考答案

1. 合法。
2. 合法，Pydantic validator 会去掉前后空格，最终变成 `A1001`。
3. 不合法，中间有空格，不符合正则。
4. 不合法，字段名不是 `order_id`。
5. 不合法，额外字段 `admin` 会被 `extra="forbid"` 拒绝。

## 练习 4：解释 502 和 422 的区别

问题：

```text
为什么用户请求体缺少 message 返回 422，而模型返回非法 arguments 返回 502？
```

### 练习 4 参考答案

用户请求体缺少 `message` 是客户端请求参数错误，属于 FastAPI/Pydantic 对入口请求的校验失败，所以返回 422。

模型返回非法 `arguments` 是上游模型服务返回了不符合预期的内容。对 `ai-service` 来说，这是依赖服务响应异常，所以更适合返回 502。

## 练习 5：补全流程

请补全本节 `/tool-decision` 的链路：

```text
POST /tool-decision
-> ChatRequest
-> ________
-> client.chat.completions.create(..., tools=..., tool_choice="auto")
-> ________
-> authorize_tool_call(tool_name)
-> parse_tool_call_arguments(raw_arguments)
-> ________
-> ToolDecisionResponse
```

### 练习 5 参考答案

```text
POST /tool-decision
-> ChatRequest
-> ToolDecisionService.decide()
-> client.chat.completions.create(..., tools=..., tool_choice="auto")
-> extract_tool_decision()
-> authorize_tool_call(tool_name)
-> parse_tool_call_arguments(raw_arguments)
-> QueryOrderArgs.model_validate(arguments)
-> ToolDecisionResponse
```

## 自测题

### 1. Tool Calling 是模型直接执行后端函数吗？

参考答案：

```text
不是。Tool Calling 是模型返回工具调用请求，包括工具名和参数。真正执行工具的是后端应用代码。
```

### 2. `tools` 参数的作用是什么？

参考答案：

```text
`tools` 把当前允许模型请求的工具定义传给模型，包括工具名、描述和参数 JSON Schema。它只是给模型选择工具用，不会自动执行工具。
```

### 3. `tool_choice="auto"` 表示什么？

参考答案：

```text
表示由模型自己判断是否需要调用工具。如果需要，模型返回 tool_calls；如果不需要，模型返回普通文本内容。
```

### 4. 为什么本节只把 `query_order` 暴露给模型？

参考答案：

```text
因为当前只允许模型看到启用的、只读的、不需要用户确认的工具。query_order 满足这些条件；create_ticket 是写操作且需要确认；refund_order 是敏感操作且禁用。
```

### 5. 为什么模型返回的 `arguments` 还要 `json.loads`？

参考答案：

```text
因为 Chat Completions 工具调用里的 function.arguments 通常是 JSON 字符串，不是 Python dict。后端要先把字符串解析成 dict，才能继续用 Pydantic 校验。
```

### 6. 为什么已经给了 JSON Schema，还要用 Pydantic 校验？

参考答案：

```text
JSON Schema 是给模型看的，用来引导模型生成参数；Pydantic 是后端验收用的，用来保证模型返回的参数真正符合服务端要求。模型输出仍然不能直接信任。
```

### 7. 模型请求 `create_ticket` 时为什么当前会被拒绝？

参考答案：

```text
因为 create_ticket 是写操作，并且 ToolDefinition 标记 requires_confirmation=True。当前没有用户确认流程，所以 authorize_tool_call() 会返回 TOOL_CONFIRMATION_REQUIRED。
```

### 8. 本节和下一节的区别是什么？

参考答案：

```text
本节只让模型决定是否调用工具，并解析、校验 tool call。下一节会真正执行工具，把工具结果再交给模型，让模型生成最终自然语言回答。
```

## 本节小结

本节完成了从“手动调用工具”到“模型提出工具调用意图”的关键一步。

现在你应该能解释：

```text
tools 参数是什么
tool_choice="auto" 是什么
tool_calls 是什么
function.arguments 为什么要 json.loads
为什么工具名要经过 authorize_tool_call()
为什么 arguments 要经过 QueryOrderArgs.model_validate()
为什么模型可见工具要少于后端注册工具
为什么本节只做决策，不执行工具
```

当前链路已经具备 Agent 的雏形：

```text
用户问题
-> 模型判断是否需要工具
-> 后端校验工具名和参数
-> 返回工具调用意图
```

下一节继续补上：

```text
后端执行 query_order
-> 调用 Java mock API
-> 把工具结果作为 tool message 交回模型
-> 模型生成最终回答
```

## 资料来源

- [OpenAI Function Calling Guide](https://developers.openai.com/api/docs/guides/function-calling)
- [OpenAI Tools Guide](https://developers.openai.com/api/docs/guides/tools)
- [阿里云百炼：Qwen Function Calling](https://help.aliyun.com/zh/model-studio/qwen-function-calling)
