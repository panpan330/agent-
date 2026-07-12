# 阶段 3 第 13 节：工具调用结果再交给模型总结

## 本节目标

第 12 节已经让模型能决定是否请求工具，但当时链路停在这里：

```text
用户问题
-> 模型返回 query_order + arguments
-> 后端校验工具名和参数
-> 返回“模型想调用工具”的意图
```

这还不是完整的工具调用。用户真正需要的不是一段 `tool_calls` JSON，而是基于真实订单数据的自然语言回答。

本节完成一条边界清晰的完整链路：

```text
用户：帮我查订单 A1001 的物流
-> 第一轮模型：请求 query_order(order_id="A1001")
-> 后端：再次校验并执行 query_order
-> Java mock 服务：返回订单数据
-> AI 服务：过滤字段、Pydantic 校验工具结果
-> AI 服务：把 assistant tool-call message 和 tool message 交回模型
-> 第二轮模型：根据真实结果生成中文回答
-> 用户：收到自然语言回复
```

本节新增接口：

```text
POST /tool-chat
```

它与第 12 节的 `/tool-decision` 不冲突：

| 接口 | 用途 | 是否执行工具 |
| --- | --- | --- |
| `/tool-decision` | 学习、观察模型是否想调用工具 | 否 |
| `/tool-chat` | 完整处理用户问题并返回最终回答 | 是，只支持 `query_order` |

## 先记住一句话

```text
工具结果不是用户消息，也不是模型自己说的话；它是后端生成的 tool message。
```

为什么要这样区分？

因为“谁说了什么”决定模型如何理解上下文：

- `user`：用户的需求，例如“查订单 A1001”。
- `assistant`：模型第一轮的工具请求，里面有 `tool_calls`。
- `tool`：后端实际执行工具得到的结果。
- `assistant`：模型第二轮基于工具结果给出的最终回答。

如果把工具结果伪装成用户消息，例如：

```text
user: 订单 A1001 已付款……
```

模型无法明确知道这是真实业务系统的结果，也无法知道它对应哪一次工具请求。真实业务流程的来源边界就被破坏了。

## 本节学习地图

### 从哪里接上来

已有能力：

```text
ToolDecisionService
-> tools + tool_choice="auto"
-> tool_calls 解析
-> authorize_tool_call()
-> QueryOrderArgs Pydantic 校验

query_order
-> JavaOrderClient
-> java-mock-service GET /orders/{order_id}
-> 字段映射
-> QueryOrderResult Pydantic 校验
```

本节负责把这两段能力串起来。

### 解决什么问题

模型自己不知道当前订单的真实状态；Java 业务服务也不会生成面向用户的解释。AI 服务把两者连接起来：

```text
模型负责判断与表达
后端负责授权、执行、校验、记录和兜底
Java 业务服务负责真实业务数据
```

### 学完后应该能解释什么

你应该能清楚解释：

1. 为什么第一轮 assistant message 也必须放进第二轮 `messages`。
2. `tool_call_id` 为什么像一次调用的“关联编号”。
3. 为什么 `tool` 的 `content` 是 JSON 字符串，而不是直接塞 Python `dict`。
4. 为什么 Java 返回的数据要先字段映射和 Pydantic 校验，再交给模型。
5. 为什么订单不存在、超时或上游 500 时，不应该让第二轮模型假装总结成功结果。

### 本节明确不学什么

本节仅支持：

```text
一个只读工具
一次工具执行
一次工具结果回传
一次模型总结
```

暂时不做：

- 多工具并行调用；
- 工具调用循环；
- 创建工单、退款等写操作；
- 用户确认；
- 流式工具调用；
- LangChain 或 LangGraph 封装。

这些限制不是功能缺陷，而是有意识的学习边界。先把最小完整闭环讲透，再增加复杂度。

## 官方协议流程

阿里云百炼的 OpenAI-compatible Function Calling 文档描述的核心顺序是：

```text
1. 发送 messages 和 tools
2. 接收模型 tool_calls
3. 应用执行工具
4. 把第一轮 assistant message 加回 messages
5. 添加携带 tool_call_id 的 tool message
6. 再次调用模型获得自然语言回答
```

文档特别强调两点：

- tool message 的 `content` 要是字符串；
- `tool_call_id` 用于让工具结果关联到模型发起的那次工具请求。

资料：

- [阿里云百炼：Function Calling](https://help.aliyun.com/zh/model-studio/qwen-function-calling)
- [阿里云百炼：OpenAI Chat 接口兼容](https://help.aliyun.com/zh/model-studio/compatibility-of-openai-with-dashscope)
- [OpenAI Function Calling Guide](https://developers.openai.com/api/docs/guides/function-calling)

把消息列表简化后，可以画成：

```text
第一轮请求：
system
user

第一轮响应：
assistant (tool_calls=[{id="call_001", name="query_order", ...}])

后端执行后，第二轮请求：
system
user
assistant (tool_calls=[{id="call_001", name="query_order", ...}])
tool (tool_call_id="call_001", content="{...真实订单结果...}")

第二轮响应：
assistant (content="订单 A1001 已付款，等待仓库发货。")
```

`call_001` 就像一次 RPC 调用的关联 ID：模型提出请求时创建，后端回传结果时必须带回同一个值。

## 为什么要先放 assistant tool-call message

初学时很容易只想到下面这一步：

```python
messages.append({
    "role": "tool",
    "tool_call_id": "call_001",
    "content": "{...}",
})
```

但这还不完整。模型需要先在历史里看见：

```text
assistant 曾经请求了 id=call_001 的 query_order
```

随后才能理解：

```text
tool 返回的是对 id=call_001 的执行结果
```

所以顺序不能颠倒：

```text
assistant tool-call message
-> tool result message
```

这不是普通 prompt 拼接，而是 Chat Completions 工具调用协议的一部分。

## 为什么 tool result 要 JSON 序列化

Python 中已校验的订单对象是：

```python
QueryOrderResult(...)
```

它不能直接作为 HTTP/SDK message 的 `content` 传给模型。我们先做：

```python
result.model_dump(mode="json")
json.dumps(..., ensure_ascii=False)
```

两个动作分别解决不同问题：

| 动作 | 作用 |
| --- | --- |
| `model_dump(mode="json")` | 把 Pydantic 对象变成 JSON 兼容数据；枚举也变成字符串值 |
| `json.dumps(...)` | 把 Python `dict` 变成协议要求的字符串 content |

`ensure_ascii=False` 让中文在消息字符串里保持可读，而 `separators=(",", ":")` 去掉无意义空格，避免额外 token。

注意：JSON 序列化不等于安全。真正的安全发生在前面：

```text
Java 原始响应
-> 字段白名单 map_java_order_to_query_order_payload()
-> QueryOrderResult.model_validate(...)
-> 才能 JSON 序列化给模型
```

因此 Java 返回的 `customer_id` 不会被传给模型。

## 本节新增和修改的代码

### 1. `ToolCallingChatService`：完整流程编排者

文件：

```text
projects/ai-service/app/services/tool_calling_chat_service.py
```

这个 service 的职责是：

```text
构造第一轮消息
-> 调用模型并解析工具意图
-> 校验 call_id
-> 执行后端允许的工具
-> 构造 assistant/tool 协议消息
-> 调用第二轮模型
-> 返回最终 reply
```

它不负责：

```text
维护订单数据
绕过 Java 直接查数据库
决定退款或创建工单权限
无限循环执行模型请求的工具
```

这就是 service 层的职责边界：它负责“编排”，不拥有业务数据和权限规则本身。

### 2. `build_tool_chat_messages`

```python
def build_tool_chat_messages(...)
```

它构造第一轮的 `system + history + user` 消息。

新 system prompt 同时说明两件事：

1. 没有真实订单数据时，模型可以请求 `query_order`。
2. 收到 tool message 后，模型必须基于工具结果自然回答，不能编造，也不应继续请求工具。

这和第 12 节的“工具决策器”prompt 不同。第 12 节只观察决策；本节的模型还要承担最终表达工作。

### 3. `require_tool_call_id`

```python
def require_tool_call_id(tool_call: ToolCallCandidate) -> str:
```

第 12 节里 `call_id` 是可选字段，因为教学接口只展示模型意图；但本节需要创建 tool message，必须有可关联的 ID。

因此完整链路在真正执行工具前检查：

```text
没有 call_id
-> TOOL_CALL_ID_MISSING
-> HTTP 502
-> 不执行工具
```

为什么先检查再执行？即使 `query_order` 是只读的，也应先确保整个协议能完成。以后若工具是写操作，先执行、后发现无法回传结果会更危险。

### 4. `build_assistant_tool_call_message`

```python
def build_assistant_tool_call_message(...) -> dict[str, Any]:
```

它把已经通过后端校验的工具请求重新组织为第二轮 messages 中的 assistant message：

```json
{
  "role": "assistant",
  "content": null,
  "tool_calls": [
    {
      "id": "call_query_order_001",
      "type": "function",
      "function": {
        "name": "query_order",
        "arguments": "{\"order_id\":\"A1001\"}"
      }
    }
  ]
}
```

这里的参数再次变成 JSON 字符串，是因为 Chat Completions 工具调用协议中的 `function.arguments` 使用字符串形式。

### 5. `build_tool_result_message`

```python
def build_tool_result_message(...) -> dict[str, str]:
```

它产生真正的 tool message：

```json
{
  "role": "tool",
  "tool_call_id": "call_query_order_001",
  "content": "{\"order_id\":\"A1001\",...}"
}
```

不要把 `tool_call_id` 写成工具名。它不是 `query_order`，而是某一次具体调用的 ID。一个模型可能在未来同一轮请求两次 `query_order`；只有 ID 才能精确配对。

### 6. `_execute_tool_call`

核心逻辑是：

```python
definition = authorize_tool_call(tool_call.name)
arguments = QueryOrderArgs.model_validate(tool_call.arguments)
return query_order(arguments, settings=self.settings)
```

为什么已经在第 12 节校验过，这里还要再授权和校验？

因为“模型输出解析”和“真正执行工具”是两道独立关口。执行点永远不应该假设上游一定安全。真实项目里，即使对象来自同一个服务内部，也要在风险边界重做最关键的检查。

这里直接调用 Python 工具函数，而不是调用 `/tools/query-order` HTTP 接口。原因是：

```text
router 是 HTTP 边界
tool function 是业务执行单元
```

服务内部已经在同一个进程里，不需要为了复用逻辑再走一次 HTTP。`query_order()` 仍然会通过 `JavaOrderClient` 调用真正的业务服务边界：`java-mock-service`。

`query_order` 是只读工具，因此当前没有把 HTTP 接口的 `Idempotency-Key` 包装带进来；未来写操作必须重新设计幂等与确认流程。

### 7. 第二轮仍然传 `tools`

当前代码第二轮继续传入同一份安全工具定义，并使用 `tool_choice="auto"`，与百炼完整 Function Calling 示例的“追加 messages 后再次调用”流程保持一致。

但本节明确只支持一次工具执行。如果第二轮模型仍返回 `tool_calls`，`extract_tool_summary_reply()` 会返回：

```text
TOOL_SUMMARY_UNEXPECTED_TOOL_CALL
HTTP 502
```

这避免模型悄悄进入无限循环或继续执行未教学的多工具流程。未来专门学习多轮/多工具编排时，才会把这里演进为受限循环、最大轮数、每轮审计和部分失败处理。

### 8. 新路由 `/tool-chat`

文件：

```text
projects/ai-service/app/routers/chat.py
```

新增 router 很薄：

```python
@router.post("/tool-chat", response_model=ChatResponse)
def tool_chat(...):
    reply = tool_calling_chat_service.generate_reply(...)
    return ChatResponse(reply=reply)
```

它只做 HTTP 层工作：请求体校验、依赖注入、长度日志和响应模型。完整流程都在 service 层，所以 service 测试不用启动 FastAPI。

## 最终调用链路

```text
POST /tool-chat
-> ChatRequest 校验 message/history
-> ToolCallingChatService.generate_reply()
-> 第一轮模型调用（tools + tool_choice="auto"）
-> extract_tool_decision()
-> authorize_tool_call() + QueryOrderArgs 校验 + call_id 校验
-> fake_order_tool.query_order()
-> JavaOrderClient.get_order()
-> GET java-mock-service /orders/{order_id}
-> map_java_order_to_query_order_payload()
-> QueryOrderResult 校验
-> assistant tool-call message
-> tool message(tool_call_id + JSON result)
-> 第二轮模型调用
-> extract_tool_summary_reply()
-> ChatResponse(reply)
```

其中唯一可以产生真实订单事实的位置是：

```text
java-mock-service / 未来的 Java Business Service
```

模型的职责是请求和表达，不是编造或确认业务事实。

## 错误处理与排查

| 现象 | 错误码/结果 | 优先排查位置 |
| --- | --- | --- |
| 本机没有模型 key | `LLM_API_KEY_MISSING`，500 | 本机 `.env`，不要把 key 发到聊天或写入代码 |
| 第一轮参数不是合法 JSON | `TOOL_ARGUMENTS_INVALID_JSON`，502 | 模型返回的 `function.arguments` |
| 参数不符合订单号规则 | `TOOL_ARGUMENTS_VALIDATION_FAILED`，502 | `QueryOrderArgs` 与模型调用日志 |
| 工具请求没有 ID | `TOOL_CALL_ID_MISSING`，502 | 模型 provider 的 tool call 响应结构 |
| 订单不存在 | `ORDER_NOT_FOUND`，404 | Java 业务服务与订单号 |
| Java 服务连接/上游异常 | `TOOL_TIMEOUT` / `TOOL_UPSTREAM_ERROR` | `JAVA_MOCK_SERVICE_BASE_URL`、服务是否启动、超时配置 |
| 第二轮模型又要调用工具 | `TOOL_SUMMARY_UNEXPECTED_TOOL_CALL`，502 | system prompt；当前阶段不支持工具循环 |
| 第二轮没有文本 | `LLM_EMPTY_RESPONSE`，502 | provider 响应和当前模型兼容性 |

一个重要原则：

```text
工具执行失败，就直接返回统一错误；不要把“错误信息”伪装成工具成功结果，让模型编造安慰性回答。
```

例如订单 A9999 不存在时，应返回 404，而不是让模型说“订单正在查询中”。

## Qwen / OpenAI-compatible 需要手动验证的点

自动化测试验证的是我们自己的协议拼装、校验和错误分支，不能证明每个模型都完全兼容。

当前已参考百炼的 OpenAI-compatible Function Calling 文档；仍应在本机手动验证：

1. 当前 `.env` 中的实际模型是否支持 Function Calling。
2. 第一轮是否返回 `tool_calls[0].id`。
3. 第二轮是否接受 `assistant tool_calls + tool message` 的完整 messages。
4. 当前模型在第二轮是否会按 prompt 直接总结，而不是继续请求工具。
5. 如果实际模型要求额外参数（例如某些模型的 thinking 配置），应以该模型在百炼官方文档中的要求为准。

这不是代码缺陷，而是 OpenAI-compatible 的含义：请求形状尽量兼容，但不同供应商、模型版本和推理模式可能有额外限制。

## 如何手动运行和验证

先启动 Java mock 服务：

```powershell
cd D:\wendang\java+python+ai\projects\java-mock-service
uv run uvicorn app.main:app --reload --port 8001
```

再启动 AI 服务：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run uvicorn app.main:app --reload --port 8000
```

访问：

```text
http://127.0.0.1:8000/docs
```

调用 `POST /tool-chat`：

```json
{
  "message": "帮我查订单 A1001 的物流"
}
```

预期：模型先请求 `query_order`，后端查询 Java mock 服务，最终接口返回类似：

```json
{
  "reply": "订单 A1001 已付款，商家已接单，仓库正在准备出库。"
}
```

还可以试：

| 请求 | 预期 |
| --- | --- |
| `FastAPI 是什么？` | 不执行工具，模型直接回答 |
| `帮我查订单` | 不执行工具，提醒提供订单号 |
| `帮我查订单 A9999` | Java 返回 `ORDER_NOT_FOUND`，AI 服务返回 404 |
| `帮我查订单 A500` | Java mock 模拟 500，AI 服务返回 `TOOL_UPSTREAM_ERROR`，502 |

真实调用模型可能产生费用。自动化测试不使用本机真实 key，也不访问真实模型或真实 Java 服务。

## 重要测试说明

新增：

```text
projects/ai-service/tests/test_tool_calling_chat_service.py
```

它重点验证：

| 测试场景 | 防止的问题 |
| --- | --- |
| 正常工具调用后第二轮总结 | 工具结果没有正确回传模型，或执行了错误参数 |
| assistant/tool 两条消息的 ID 一致 | 工具结果关联到错误的调用 |
| tool content 是 JSON 且不含 `customer_id` | 内部字段泄露给模型 |
| 普通问题直接回答 | 不必要的 Java 服务调用 |
| 缺少 `call_id` 不执行工具 | 协议无法闭环仍访问业务服务 |
| 订单不存在时不调用第二轮模型 | 用模型掩盖真实业务错误 |
| 第二轮再次要求工具时拒绝 | 当前阶段意外进入无限工具循环 |
| 缺少 API key、第二轮模型异常 | 外部依赖错误映射不一致 |

`test_chat_api.py` 还覆盖 `/tool-chat` 的 HTTP 响应、`history` 传递、配置错误、422 参数校验和 405 方法错误。它通过 FastAPI dependency override 放入 fake service，不调用真实模型。

## 练习 1：补全第二轮消息顺序

题目：把下面顺序补完整。

```text
system
user
__________
__________
-> 第二轮模型调用
```

### 练习 1 参考答案

```text
system
user
assistant（第一轮返回的 tool_calls）
tool（后端执行结果，带 tool_call_id）
-> 第二轮模型调用
```

## 练习 2：判断 ID 是否正确

第一轮模型返回：

```json
{
  "id": "call_001",
  "function": {"name": "query_order", "arguments": "{\"order_id\":\"A1001\"}"}
}
```

下面哪个 tool message 正确？

1.

```json
{"role":"tool","tool_call_id":"query_order","content":"{...}"}
```

2.

```json
{"role":"tool","tool_call_id":"call_001","content":"{...}"}
```

### 练习 2 参考答案

第 2 个正确。`tool_call_id` 必须是具体调用的 ID `call_001`，不能写工具名 `query_order`。

## 练习 3：判断失败后的行为

题目：Java 服务返回“订单不存在”时，下面哪个正确？

1. 把 `{"error":"not found"}` 当作 tool result 给模型，让模型自由回答。
2. 后端返回 `ORDER_NOT_FOUND` 404，不进行第二轮总结。
3. 模型猜测用户可能输错了订单号，并说“订单正在发货”。

### 练习 3 参考答案

第 2 个正确。订单是否存在是业务事实，错误应该由后端按统一错误码返回，不能让模型猜测或掩盖失败。

## 练习 4：解释两次校验

题目：为什么本节在第 12 节已经解析过工具参数后，执行前还会调用 `authorize_tool_call()` 和 `QueryOrderArgs.model_validate()`？

### 练习 4 参考答案

因为解析模型输出和真正执行业务工具是不同风险边界。执行点必须独立确认工具仍允许执行、参数仍满足规则，不能只相信前一步对象已经处理过。

## 自测题

### 1. Tool Calling 的第二轮中，为什么需要 assistant tool-call message？

参考答案：

它保留模型第一轮“我请求了哪个工具、调用 ID 是什么”的上下文。后面的 tool message 才能用 `tool_call_id` 明确关联到这次请求。

### 2. `tool_call_id` 和工具名有什么区别？

参考答案：

工具名表示“调用哪种能力”，例如 `query_order`；`tool_call_id` 表示“这一次具体调用”，例如 `call_001`。同一种工具可以被调用多次，所以不能用工具名代替调用 ID。

### 3. 为什么 tool message 的 content 不直接传 Python dict？

参考答案：

当前 OpenAI-compatible Chat Completions 工具消息要求 content 使用字符串。后端先把已校验对象转成 JSON 兼容 dict，再 `json.dumps` 成字符串。

### 4. 本节模型能直接调用 Java 服务吗？

参考答案：

不能。模型只返回 `tool_calls`；Python 后端的 `ToolCallingChatService` 调用 `query_order`，再由 `JavaOrderClient` 通过 HTTP 调 Java mock 服务。

### 5. 为什么不直接调用 `/tools/query-order` HTTP 接口？

参考答案：

`/tools/query-order` 是给 HTTP 客户端使用的 router。AI 服务内部已经在同一个 Python 进程中，可以直接复用工具函数；真正的跨服务 HTTP 边界仍然是 Python 到 Java 服务的调用。

### 6. 缺少 `call_id` 时为什么不执行工具？

参考答案：

没有 ID 就无法构造与第一轮请求正确配对的 tool message。先拒绝可以保证协议完整，未来面对写操作时也避免出现“业务已执行但无法正确收尾”的风险。

### 7. 第二轮模型再次返回 tool_calls 时，本节怎么处理？

参考答案：

返回 `TOOL_SUMMARY_UNEXPECTED_TOOL_CALL`，不再执行工具。因为多轮工具循环的最大轮数、部分失败、审计和成本控制还没有在本节设计。

### 8. `QueryOrderResult` 校验在第二轮模型调用前的意义是什么？

参考答案：

它确保传给模型的字段、枚举和类型符合后端契约，并配合字段映射防止 Java 内部字段（例如 `customer_id`）泄露给模型。

## 本节小结

本节完成了一个最小但完整的 Tool Calling 闭环：

```text
模型提出请求
-> 后端校验和执行
-> Java 业务服务提供事实
-> 后端构造 tool message
-> 模型把事实表达成自然语言
```

现在你应该能向别人说明：

```text
为什么工具调用通常需要两次模型调用
assistant tool-call message 与 tool message 的区别
tool_call_id 的关联作用
为什么工具结果要先过滤、校验、JSON 序列化
为什么失败时后端必须直接兜底
为什么当前只支持一个工具、一次执行
```

## 下一节衔接

下一节是阶段 3 第 14 节：

```text
用户确认机制：敏感操作不能直接执行
```

这一节会从当前只读 `query_order` 继续扩展到写操作的安全边界：模型即使请求 `create_ticket`，后端也必须先展示待执行信息，等待用户明确确认后才允许真正写入业务系统。
