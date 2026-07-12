# 阶段 3 第 13 节：工具调用结果再交给模型总结

> 本节定位：这是一次“完整但受控”的两轮 Tool Calling。目标不是学会复制 Agent 代码，而是理解：模型为什么需要工具结果、后端为什么要把结果按协议放回消息上下文、以及业务事实为什么始终由后端掌控。

## 本节目标

第 12 节已经完成了第一轮能力：模型可以根据 `tools` 和 `tool_choice="auto"`，决定是否请求：

```text
query_order({"order_id": "A1001"})
```

但用户不关心模型“想调用什么”。用户真正要的是：

```text
订单 A1001 当前是什么状态？物流到哪了？
```

因此，本节完成下面的闭环：

```text
用户问题
-> 第一轮模型提出工具请求
-> 后端校验、授权并执行工具
-> Java 业务服务返回真实订单事实
-> AI 服务过滤并校验结果
-> 后端按工具协议把结果作为 tool message 放回上下文
-> 第二轮模型把事实组织成自然语言回答
```

本节完成后，你应该能：

1. 解释为什么 Tool Calling 往往不是一次模型调用，而是至少两次。
2. 说清 `system`、`user`、`assistant`、`tool` 四种消息角色在本节分别代表什么。
3. 解释 `tool_call_id` 为什么像一次调用的“回执编号”或“关联 ID”。
4. 说清为什么工具结果必须先过滤、校验、JSON 序列化，才能交给模型。
5. 看懂 `ToolCallingChatService` 如何把模型、Python 工具和 Java mock 服务串起来。
6. 在工具失败、模型结果异常或模型第二轮继续要工具时，知道应该在哪一层排查。

## 学习地图

### 从上一节接到哪里

第 12 节的终点：

```text
POST /tool-decision
-> ToolDecisionService.decide()
-> 第一轮模型调用
-> tool_calls 解析
-> 工具名白名单校验
-> QueryOrderArgs 参数校验
-> ToolDecisionResponse
```

它只回答：

```text
模型是否想调用工具？想调用哪个？参数是什么？
```

本节新增的终点：

```text
POST /tool-chat
-> ToolCallingChatService.generate_reply()
-> 第一轮模型决定
-> 真正执行 query_order
-> 将工具结果回传模型
-> 第二轮模型输出最终 reply
```

### 本节的核心问题

模型第一轮已经说：

```text
“请帮我查 query_order，订单号 A1001。”
```

后端也真的查到了结果。现在问题是：

```text
怎样让模型知道“这份结果正是它刚才请求的那次查询结果”，并且让它只根据真实结果回答？
```

答案不是再拼一句普通 prompt，而是遵守 Tool Calling 的消息协议：

```text
assistant tool-call message
-> tool result message
-> 第二轮模型调用
```

### 本节明确不学什么

为了把底层流程学透，本节只支持：

```text
一个只读工具：query_order
一次工具执行
一次工具结果回传
一次自然语言总结
```

暂时不做：

- 多个工具并行调用；
- 工具循环和最大轮数控制；
- 创建工单、退款等写操作；
- 用户确认；
- 流式工具调用；
- LangChain / LangGraph 封装。

这些不是“不重要”，而是后续需要单独设计权限、确认、幂等、审计、部分失败和成本控制，不能在本节顺手塞进来。

## 和第 12 节的关系：新旧知识对比

| 维度 | 第 12 节 | 第 13 节 |
| --- | --- | --- |
| 核心问题 | 模型要不要工具 | 工具结果怎样变成最终回答 |
| 模型调用次数 | 一次 | 一次或两次 |
| 业务工具 | 不执行 | 执行安全的 `query_order` |
| Java 服务 | 不访问 | 通过 Python 工具访问 |
| 返回给客户端 | 决策对象 | `ChatResponse.reply` |
| 新协议消息 | 无 | assistant tool-call message、tool message |
| 主要风险 | 模型请求错误工具/参数 | 结果错配、数据泄露、失败被模型掩盖、工具循环 |

第 12 节的安全原则没有失效，反而在本节更重要：

```text
模型可以提出请求
不等于模型可以执行请求
更不等于模型可以确认业务事实
```

## 基础知识铺垫

下面先不看项目代码。先把理解本节必须用到的基础概念建立起来。

### 基础 1：什么是“多步骤应用流程”

**人话解释**：普通聊天像你问一句、对方答一句。工具调用像你问问题后，对方先说“我得去查一下”，查完再回来回答你。

**工程术语**：这是一种 application-orchestrated workflow（由应用后端编排的多步骤流程）。模型调用只是流程中的一个节点，不是整个应用。

**它为什么出现**：大模型没有你的订单数据库、Java 业务规则和当前物流状态。它只会根据训练内容生成文本，不能凭空获得今天某一笔订单的真实信息。

**它解决什么问题**：让模型负责理解用户意图和组织语言，让外部系统负责提供实时、可信的事实。

**没有它会怎样**：模型可能生成看起来合理但不真实的回答，例如把没有发货的订单说成“已在运输中”。这就是业务场景中的幻觉风险。

**真实开发常见位置**：

```text
客服查订单
银行查余额
航班查询
库存查询
企业知识库检索
创建工单前的字段提取与确认
```

**当前项目例子**：`ToolCallingChatService.generate_reply()` 就是本节的编排者。它先调用模型、再调用 `query_order`、再调用模型。

### 基础 2：为什么一次 Tool Calling 常常需要两次模型调用

**人话解释**：第一次模型调用像“前台接待员”判断要不要查系统；第二次像“拿到查询单后，把结果翻译成用户听得懂的话”。

**工程术语**：first model turn（工具选择轮）与 follow-up model turn（工具结果总结轮）。

**小例子**：

```text
用户：北京天气如何？
第一轮模型：我要调用 get_weather("北京")
后端工具：返回 {"weather": "晴", "temperature": 26}
第二轮模型：北京今天晴，26℃。
```

第一轮没有天气事实，所以不能负责最终事实回答；工具返回的 JSON 又比较机械，所以需要第二轮组织自然语言。

**当前项目例子**：

```text
第一轮：模型请求 query_order(A1001)
工具：Java mock 返回 waiting_shipment、paid、物流摘要
第二轮：模型生成“已付款，等待仓库发货”等自然语言
```

**常见误区**：把 `tool_calls` 当成最终答复。它只是“模型想做什么”的结构化请求，不是订单查询结果。

### 基础 3：`messages` 不是普通字符串列表，而是对话协议

**人话解释**：同一句话由不同的人说，意义可能完全不同。“订单已发货”如果是用户说的，只是用户声称；如果是业务系统说的，才是系统查到的事实。

**工程术语**：Chat Completions messages 是带 role 的 conversation context（对话上下文协议）。role 描述一条信息的来源和在流程中的语义。

本节会出现四种 role：

| role | 谁产生 | 本节含义 |
| --- | --- | --- |
| `system` | 后端 | 给模型设定任务边界和行为规则 |
| `user` | 用户 | 真实需求，例如“查订单 A1001” |
| `assistant` | 模型 | 第一轮工具请求或第二轮自然语言回答 |
| `tool` | 后端工具执行器 | 对某次工具请求返回的已校验结果 |

**没有 role 会怎样**：如果把工具结果伪装成用户说的话，模型不再能区分“用户提供的信息”和“后端查到的事实”。在多轮、审计和安全场景中，这会让系统边界变得模糊。

**当前项目例子**：`build_tool_summary_messages()` 构造的是：

```text
system
user
assistant（含 tool_calls）
tool（含 tool_call_id 和真实结果）
```

### 基础 4：Tool Call 是“请求”，不是函数真的被模型执行

**人话解释**：模型像客服说“请后台帮我查订单”，它自己没有进入订单系统，也没有执行 Python 函数。

**工程术语**：tool call / function call request（工具调用请求）是模型的结构化输出；tool execution（工具执行）由应用服务器负责。

第一轮模型结果可能近似：

```json
{
  "id": "call_001",
  "type": "function",
  "function": {
    "name": "query_order",
    "arguments": "{\"order_id\":\"A1001\"}"
  }
}
```

注意：这段内容不是订单事实，也不是 Python 函数调用记录；它只是模型提出的建议。

**为什么需要后端接管**：后端才能决定：

```text
这个工具是否存在？
是否启用？
当前用户是否有权限？
参数是否符合格式？
是否需要确认？
怎么处理超时和失败？
```

**当前项目例子**：第一轮请求必须经过 `authorize_tool_call()` 与 `QueryOrderArgs.model_validate()`，然后才会进入 `query_order()`。

### 基础 5：`tool_call_id` 是什么，为什么必须存在

**人话解释**：把它理解成医院的取号单号或快递单号。你不能只说“这是一次挂号结果”，而要说“这是 A017 号挂号单的结果”。

**工程术语**：correlation ID（关联 ID）或 request-response correlation（请求与响应配对）。

模型可能未来一次提出两个请求：

```text
call_001 -> query_order(A1001)
call_002 -> query_order(A1002)
```

如果后端只返回：

```text
tool: 订单 A1002 已发货
```

模型不知道它对应哪个请求。正确结构必须是：

```json
{
  "role": "tool",
  "tool_call_id": "call_002",
  "content": "{...A1002 的结果...}"
}
```

**没有它会怎样**：工具结果错配。对只读订单查询也会答错订单；对未来转账、退款、创建工单等写操作，错配可能造成严重业务事故。

**当前项目例子**：`require_tool_call_id()` 在真正执行工具之前检查 ID；缺失就抛出 `TOOL_CALL_ID_MISSING`，不访问 Java 服务。

### 基础 6：Python 对象、`dict` 与 JSON 字符串的区别

本节会同时出现三个非常容易混淆的东西：

```python
# Python Pydantic 对象
result = QueryOrderResult(...)

# Python dict
payload = result.model_dump(mode="json")

# JSON 字符串
content = json.dumps(payload, ensure_ascii=False)
```

**人话解释**：

- Pydantic 对象像有规则的订单表单；
- `dict` 像 Python 程序内部使用的普通字典；
- JSON 字符串像可以通过 HTTP、日志或模型 API 传递的文字格式。

**工程术语**：serialization（序列化）是把内存中的对象转换成可传输格式；deserialization（反序列化）是把可传输格式转回程序对象。

**为什么出现**：工具消息协议要求 `content` 是字符串，而模型第一轮的 `function.arguments` 通常也是 JSON 字符串。服务端不能直接把 Python 对象塞给 API。

**没有它会怎样**：

- 传入 Python `dict` 时，SDK 或 provider 可能报参数格式错误；
- 直接序列化未校验的 Java 原始响应，可能传出内部字段；
- 不了解 JSON 字符串与 dict 的区别，会在 `json.loads()` 或 `json.dumps()` 处反复出错。

**当前项目例子**：

```python
result.model_dump(mode="json")
json.dumps(..., ensure_ascii=False, separators=(",", ":"))
```

前者让枚举如 `OrderStatus.WAITING_SHIPMENT` 变成 JSON 值 `"waiting_shipment"`；后者把 dict 变成 tool message 的字符串内容。

### 基础 7：数据契约、DTO、字段白名单与 Pydantic 校验

**人话解释**：Java 业务服务知道的内容，不等于 AI 模型应该知道的内容。后端要先挑出“允许给 AI 的字段”，并确认这些字段的格式正确。

**工程术语**：

- data contract（数据契约）：不同模块约定数据应有什么字段和类型；
- DTO（Data Transfer Object）：为某个调用场景专门准备的数据结构；
- allowlist（白名单）：只允许明确列出的字段流出。

Java mock 的原始结果中有：

```json
{
  "order_id": "A1001",
  "customer_id": "C9001",
  "order_status": "waiting_shipment"
}
```

AI 工具层映射后只保留：

```json
{
  "order_id": "A1001",
  "order_status": "waiting_shipment",
  "payment_status": "paid",
  "logistics_message": "...",
  "latest_event": "...",
  "can_create_ticket": true,
  "source": "java_mock_service"
}
```

**没有它会怎样**：模型上下文可能出现客户 ID、内部备注、手机号、价格成本等本不该暴露的数据；上游字段改名或返回非法状态时，错误也会静悄悄地传到模型。

**当前项目例子**：

```text
map_java_order_to_query_order_payload()
-> validate_query_order_result()
-> QueryOrderResult
-> build_tool_result_message()
```

这是第 6、11 节知识在“结果回传模型”这个新场景中的组合应用。

### 基础 8：什么是信任边界

**人话解释**：跨过一扇门的数据都要检查。模型输出从模型服务进来，Java 响应从另一个服务进来，用户请求从浏览器进来；它们都不是你当前函数自己凭空创造的可信数据。

**工程术语**：trust boundary（信任边界）与 untrusted input（不可信输入）。

本节有三个关键边界：

```text
用户 -> FastAPI：ChatRequest 校验
模型 -> AI 服务：工具名、arguments、call_id、第二轮 content 校验
Java 服务 -> AI 服务：HTTP 状态、JSON 结构、QueryOrderResult 校验
```

**没有它会怎样**：

- 模型可请求 `delete_database`；
- 模型可传入非法订单号；
- Java 服务返回错误 JSON 时，模型可能根据半截数据胡编；
- 上游新增敏感字段时，可能直接泄露。

**当前项目例子**：`ToolCallingChatService._execute_tool_call()` 在执行点再次调用 `authorize_tool_call()` 和 `QueryOrderArgs.model_validate()`。这不是多余，而是对“真正执行”这一风险点的第二道门。

### 基础 9：同步跨服务调用、延迟与失败传播

**人话解释**：用户等待 `/tool-chat` 的回复时，AI 服务在等待模型、等待 Java 服务、再等待模型。任何一个慢下来，用户都会觉得整个接口慢。

**工程术语**：synchronous request chain（同步请求链）、latency（延迟）、failure propagation（失败传播）。

本节的成功路径至少包含：

```text
模型调用 1 耗时
+ Java HTTP 调用耗时
+ 模型调用 2 耗时
= 用户感知的主要等待时间
```

**没有超时与错误映射会怎样**：Java 服务卡住时，AI 服务可能一直等；用户只看到 500，无法判断是模型、工具还是业务服务出错。

**当前项目例子**：

```text
JavaOrderClient
-> httpx.TimeoutException -> TOOL_TIMEOUT (504)
-> httpx.RequestError / 5xx -> TOOL_UPSTREAM_ERROR (502)
-> 404 -> ORDER_NOT_FOUND (404)
```

本节不新建这些错误码，但让它们首次进入“模型决定工具后”的完整链路。

### 基础 10：状态、历史消息与“一次请求内的上下文”

**人话解释**：HTTP 本身不会记住上次对话。模型也不会天然记住“它刚才请求了什么工具”。要让它记住，应用必须把需要的消息再次放进本次请求。

**工程术语**：stateless HTTP（无状态 HTTP）、conversation history（对话历史）、request-local context（一次请求局部上下文）。

当前 `ChatRequest.history` 允许客户端传入之前的 user/assistant 对话。与此同时，`build_tool_summary_messages()` 在当前这一次 `/tool-chat` 请求内，额外补上：

```text
第一轮 assistant 工具请求
工具执行结果
```

二者不同：

| 内容 | 来源 | 作用 |
| --- | --- | --- |
| `history` | 客户端传入的历史对话 | 理解“对，查一下”中的上下文 |
| assistant/tool 消息 | 当前后端流程生成 | 完成当前工具请求与结果的协议闭环 |

**常见误区**：把 tool message 直接放入客户端的 `history`。当前 `ChatMessage` 只允许 user/assistant，工具协议消息应该由可信后端生成。

### 基础 11：为什么当前拒绝第二轮继续调用工具

**人话解释**：模型第二轮如果又说“再查一下别的”，我们当前不会自动顺着做。先把“一次查询、一次回答”学完整，比写一个看似聪明但失控的循环更重要。

**工程术语**：tool-calling loop（工具调用循环）、termination condition（终止条件）、maximum iterations（最大轮数）。

完整 Agent 可能是：

```text
模型 -> 工具 -> 模型 -> 工具 -> 模型 -> ...
```

它必须考虑：

```text
最大轮数
总 token 成本
总超时
重复调用
部分成功
审计记录
用户确认
```

**当前项目例子**：`extract_tool_summary_reply()` 发现第二轮仍然有 `tool_calls` 时，返回 `TOOL_SUMMARY_UNEXPECTED_TOOL_CALL`，而不是继续执行。

这不是说“模型第二轮永远不能调用工具”，而是明确告诉你：当前产品能力和教学边界只到一轮。

## 先用最小例子理解协议，再看订单项目

暂时忘记 FastAPI、Pydantic 和 Java。假设只有天气工具：

```text
工具名：get_weather
入参：{"city": "北京"}
```

用户发来：

```text
北京天气怎么样？
```

第一轮 messages：

```json
[
  {"role": "system", "content": "需要实时天气时可以调用工具。"},
  {"role": "user", "content": "北京天气怎么样？"}
]
```

第一轮模型不应该猜天气，而应请求：

```json
{
  "role": "assistant",
  "content": null,
  "tool_calls": [
    {
      "id": "call_weather_001",
      "type": "function",
      "function": {
        "name": "get_weather",
        "arguments": "{\"city\":\"北京\"}"
      }
    }
  ]
}
```

后端真的调用天气服务，得到：

```json
{"city":"北京","weather":"晴","temperature":26}
```

第二轮 messages 必须追加两条：

```json
{
  "role": "assistant",
  "content": null,
  "tool_calls": ["保留第一轮的完整工具请求"]
}
```

```json
{
  "role": "tool",
  "tool_call_id": "call_weather_001",
  "content": "{\"city\":\"北京\",\"weather\":\"晴\",\"temperature\":26}"
}
```

第二轮模型才可以回答：

```text
北京今天晴，气温约 26℃。
```

把 `get_weather` 换成 `query_order`，把天气服务换成 Java mock 服务，就是当前项目的本节实现。

## 为什么现在要学这一节

前面已经分别学过：

```text
模型 API 调用
messages 与 history
Pydantic
HTTPX 跨服务调用
工具参数与结果校验
工具权限边界
幂等性
模型决定是否调用工具
```

本节第一次把这些知识真正组合成用户可用流程：

```text
LLM 决策
+ 后端安全守卫
+ Java 业务事实
+ 数据契约
+ 第二轮自然语言生成
= 最小完整工具调用产品能力
```

后续的用户确认、创建工单、LangChain Tool、LangGraph 工作流都建立在这个闭环上。如果这里没理解清楚，后面只会变成“会调框架但不知道框架替你做了什么”。

## 本节修改的文件与职责

| 文件 | 为什么需要它 | 本节作用 |
| --- | --- | --- |
| `app/services/tool_calling_chat_service.py` | 第 12 节只有决策，缺少完整编排者 | 负责两轮模型调用、执行工具、构造协议消息和返回最终文本 |
| `app/routers/chat.py` | 需要对外提供完整能力 | 新增 `POST /tool-chat` 与依赖注入 |
| `tests/test_tool_calling_chat_service.py` | 完整流程有多步且不能真实调用模型 | 用 fake client 验证消息顺序、错误边界和第二轮调用 |
| `tests/test_chat_api.py` | 新接口仍要遵守 HTTP 契约 | 验证 200、history、422、405 和配置错误 |
| `README.md`、进度、资源、笔记 | 学习成果必须可定位和复习 | 记录接口、边界、资料和进度 |

本节**没有修改** `java-mock-service`。原因是它已经正确承担业务服务角色：提供订单事实、返回 404/500。第 13 节要学的是 AI 服务如何安全地消费这些事实并交回模型，不是重新设计订单服务。

## 业务代码详细讲解

### 一、为什么新增 `ToolCallingChatService`

文件：

```text
projects/ai-service/app/services/tool_calling_chat_service.py
```

如果把两轮模型调用、Java 调用、JSON 构造都塞进 router，会产生三个问题：

```text
HTTP 路由和业务流程混在一起
难以脱离 FastAPI 单独测试
后面加确认、日志、循环时会迅速失控
```

因此 router 只负责 HTTP，service 负责业务编排。这和 Java 里的 `Controller -> Service -> Client/Repository` 分层思想相似；但 Python 中没有强制框架替你分层，必须靠项目结构自觉保持边界。

### 二、`build_tool_chat_prompt` 与 `build_tool_chat_messages`

简化后的职责：

```python
def build_tool_chat_messages(user_message, *, history=None) -> list[dict[str, str]]:
    messages = build_multi_turn_messages(
        build_tool_chat_prompt(user_message),
        history=history,
        system_message=TOOL_CHAT_SYSTEM_PROMPT,
    )
    return serialize_chat_messages(messages)
```

**输入**：

- `user_message`：本轮用户问题；
- `history`：可选的旧 user/assistant 消息。

**输出**：第一轮模型可直接接收的 `list[dict[str, str]]`。

**内部步骤**：

1. `build_tool_chat_prompt()` 说明什么时候可调用 `query_order`、什么时候直接回答；
2. `build_multi_turn_messages()` 按 `system -> history -> user` 组织顺序；
3. `serialize_chat_messages()` 将 Pydantic `ChatMessage` 转成 SDK 需要的 dict。

**为什么不用第 12 节的 `TOOL_DECISION_SYSTEM_PROMPT`**：第 12 节的模型身份是“工具决策器”，任务止于输出工具意图。本节需要模型在收到工具结果后继续生成面向用户的回答，因此使用新的 `TOOL_CHAT_SYSTEM_PROMPT`。

**常见错误**：

```text
把 system 放在 history 后面：规则优先级和上下文语义会变差。
让客户端传 system/tool role：不可信客户端可能伪造规则或工具结果。
忘记传 history：用户说“对，查一下”时模型可能找不到订单号。
```

### 三、`require_tool_call_id`：先确认能闭环，再执行

核心逻辑：

```python
def require_tool_call_id(tool_call: ToolCallCandidate) -> str:
    if isinstance(tool_call.call_id, str) and tool_call.call_id.strip():
        return tool_call.call_id
    raise AppException(code="TOOL_CALL_ID_MISSING", status_code=502, ...)
```

**输入**：第 12 节已经解析、校验过的 `ToolCallCandidate`。

**返回**：非空 `call_id` 字符串。

**为什么是 502**：缺少 ID 不是用户 HTTP 请求体写错，而是上游模型返回的工具调用结构无法满足协议。因此从 AI 服务视角是上游响应异常。

**为什么在执行工具前检查**：当前 `query_order` 是只读，即使晚一点检查也不会写坏数据；但正确流程应该从现在就建立。未来写工具若先执行、后发现无法构造正确 tool message，就可能出现“业务动作已经发生、对话却无法可靠收尾”的事故。

### 四、`build_assistant_tool_call_message`：保留第一轮请求

输入是经过后端校验后的：

```python
ToolCallCandidate(
    name="query_order",
    arguments={"order_id": "A1001"},
    call_id="call_query_order_001",
)
```

它输出第二轮上下文中的 assistant message：

```python
{
    "role": "assistant",
    "content": None,
    "tool_calls": [
        {
            "id": call_id,
            "type": "function",
            "function": {
                "name": tool_call.name,
                "arguments": json.dumps(tool_call.arguments),
            },
        }
    ],
}
```

**关键设计**：我们没有把模型原始对象不加处理地再次传下去，而是使用已经通过白名单和 Pydantic 校验的名字、参数、ID 构造协议消息。这样第二轮消息仍遵守协议，同时不把未知字段或非法参数继续扩散。

**为什么 `content` 是 `None`**：第一轮模型的重点是工具请求，不一定有普通文本内容。`tool_calls` 才是这条 assistant message 的业务语义。

### 五、`build_tool_result_message`：后端把事实放回上下文

核心结构：

```python
{
    "role": "tool",
    "tool_call_id": require_tool_call_id(tool_call),
    "content": json.dumps(result.model_dump(mode="json"), ensure_ascii=False),
}
```

**输入**：

- 第一次工具请求 `ToolCallCandidate`；
- 已校验的 `QueryOrderResult`。

**返回**：符合工具协议的 `dict[str, str]`。

**为什么 result 一定要是 `QueryOrderResult`**：因为它已经经过 `map_java_order_to_query_order_payload()` 的字段白名单以及 `validate_query_order_result()` 的类型/枚举校验。这里不接受 Java 原始 dict，避免 `customer_id` 等字段绕过工具层。

### 六、`build_tool_summary_messages`：不要破坏原来的消息顺序

它把三段内容合并：

```text
initial_messages
+ assistant tool-call message
+ tool result message
```

**为什么是追加而不是重建一个“更简单”的 prompt**：模型需要同时看见原始用户问题、第一轮请求和对应结果。随意重写成一句“订单结果如下，请总结”会丢失工具调用关系，也让后续多工具场景无法正确扩展。

### 七、`ToolCallingChatService.__init__`：依赖注入为什么重要

构造函数接收：

```python
settings: Settings
client: Any | None = None
query_order_executor: OrderQueryExecutor | None = None
```

**人话解释**：生产环境不传后两个参数，service 自己创建真实模型 client 和真实工具；测试环境传入 fake client/fake executor，避免花钱、避免依赖网络和 Java 服务。

**工程术语**：dependency injection（依赖注入）与 test double（测试替身）。

**为什么需要它**：如果 service 内部把 `OpenAI(...)` 和 HTTP 调用写死，测试就会真实访问外部服务，速度慢、成本高、结果不稳定。

### 八、`_get_client` 与 `_call_model`：模型依赖统一处理

`_get_client()` 的职责是延迟创建 OpenAI-compatible client，并把没有 API key 的 `ValueError` 转成项目统一错误：

```text
LLM_API_KEY_MISSING
HTTP 500
```

`_call_model(messages)` 的职责是统一调用：

```python
client.chat.completions.create(
    model=self.settings.llm_model,
    messages=list(messages),
    tools=list_model_callable_openai_tools(),
    tool_choice="auto",
)
```

**输入**：当前轮完整消息列表。

**输出**：provider 的 completion 对象。

**关键分支**：任何 OpenAI SDK/provider 异常都会进入 `map_openai_error_to_app_exception()`，变为项目已定义的 `LLM_TIMEOUT`、`LLM_RATE_LIMITED`、`LLM_CALL_FAILED` 等错误。

**为什么第二轮仍传 `tools` 和 `auto`**：百炼的完整 Function Calling 流程是追加 assistant/tool 消息后再次调用模型。当前 system prompt 要求它得到结果后直接回答；如果实际第二轮仍请求工具，当前能力不会继续执行，而是显式拒绝。这保留协议兼容性，同时守住本节“一次工具”的边界。

### 九、`_execute_tool_call`：真正执行前的第二道安全门

简化逻辑：

```python
definition = authorize_tool_call(tool_call.name)
arguments = QueryOrderArgs.model_validate(tool_call.arguments)
return query_order(arguments, settings=self.settings)
```

**为什么第 12 节已经校验过，这里还要再校验**：因为“解析模型输出”和“执行外部业务动作”是两个不同风险点。真正执行工具的位置必须独立守卫，不能只信任调用者已经做过什么。

**为什么直接调用 `query_order()`，而不是请求 `/tools/query-order`**：

```text
/tools/query-order 是 HTTP router，面向外部客户端。
query_order() 是同一 Python 进程里的可复用业务工具函数。
```

服务内部再绕一圈 HTTP 只会增加开销和故障点。真正跨服务的边界仍是：

```text
Python AI 服务 -> JavaOrderClient -> Java mock 服务
```

**和幂等性的关系**：当前工具是只读查询，重复执行不会产生新业务效果。未来 `create_ticket`、`refund_order` 等写操作不能简单照搬这里，必须带确认与幂等保护。

### 十、`extract_tool_summary_reply`：为本节设置终止条件

第二轮后，代码先检查是否仍有 `tool_calls`：

```python
if extract_message_tool_calls(message):
    raise AppException(code="TOOL_SUMMARY_UNEXPECTED_TOOL_CALL", ...)
```

没有新的工具请求，才使用 `extract_direct_reply()` 读取非空 `message.content`。

**为什么不能忽略第二轮 tool_calls**：如果忽略，接口可能把空 `content` 当回答返回；如果自动继续执行，则未经设计地进入工具循环。

### 十一、`generate_reply`：把完整分支串起来

这是本节最核心的函数。可以按下面伪代码理解：

```python
def generate_reply(user_message, history=None):
    检查 API key
    构造第一轮 messages
    第一轮调用模型
    解析 ToolDecisionResponse

    如果模型直接回答：
        记录一次模型调用成功
        返回 reply

    检查 tool_call 和 call_id
    后端再次授权、校验并执行 query_order
    构造 assistant tool-call + tool result messages
    第二轮调用模型
    确认第二轮不再要工具
    返回最终 reply
```

关键分支表：

| 分支 | 为什么这样做 |
| --- | --- |
| 第一轮直接回答 | 普通学习问题或缺订单号时不浪费 Java/模型第二轮调用 |
| 缺少 `tool_call` | 模型结构与声明的决策不一致，按上游异常处理 |
| 缺少 `call_id` | 无法可靠回传结果，不执行工具 |
| 工具异常 | 保留 `ORDER_NOT_FOUND`、`TOOL_TIMEOUT` 等事实性错误，不进行总结 |
| 第二轮又要工具 | 本节能力边界，拒绝继续执行 |
| 第二轮文本正常 | 返回 `ChatResponse.reply` |

### 十二、router：`POST /tool-chat` 为什么要保持薄

文件：

```text
projects/ai-service/app/routers/chat.py
```

核心代码：

```python
@router.post("/tool-chat", response_model=ChatResponse)
def tool_chat(request: ChatRequest, tool_calling_chat_service=Depends(...)):
    reply = tool_calling_chat_service.generate_reply(
        request.message,
        history=request.history,
    )
    return ChatResponse(reply=reply)
```

**输入**：`ChatRequest`。它负责保证 `message` 非空，`history` 只含允许角色。

**输出**：`ChatResponse`，只向客户端暴露最终 `reply`。

**router 还做了什么**：记录消息长度和 history 数量，不记录完整用户内容，避免日志泄露。

**router 不做什么**：不解析 tool_calls、不查 Java、不手拼 JSON、不处理 provider 异常。这些是 service 的职责。

## 本节如何复用前面模块

本节不是凭空新增一套系统，而是把已学模块接起来：

```text
ToolDecisionService
  解析模型工具意图
      ↓
tool_registry
  工具白名单和权限边界
      ↓
QueryOrderArgs
  工具参数契约
      ↓
fake_order_tool.query_order
  工具函数与字段映射
      ↓
JavaOrderClient
  HTTP 调用 Java mock 服务
      ↓
QueryOrderResult
  工具结果契约
      ↓
ToolCallingChatService
  构造 tool message 并第二次调用模型
```

注意 `fake_order_tool.py` 的文件名保留了历史教学痕迹，但内部已经不查本地内存数据，而是调用 Java mock API。不要只看文件名判断职责，要顺着调用链看实际行为。

## 完整调用链路

```text
POST /tool-chat
-> FastAPI 把 JSON 请求体校验为 ChatRequest
-> chat.tool_chat()
-> ToolCallingChatService.generate_reply()
-> build_tool_chat_messages()
-> 第一轮 client.chat.completions.create(... tools=..., tool_choice="auto")
-> extract_tool_decision()
-> authorize_tool_call() + QueryOrderArgs 校验 + call_id 校验
-> fake_order_tool.query_order()
-> JavaOrderClient.get_order()
-> GET java-mock-service /orders/{order_id}
-> Java 原始 JSON
-> map_java_order_to_query_order_payload()
-> QueryOrderResult Pydantic 校验
-> build_assistant_tool_call_message()
-> build_tool_result_message()
-> 第二轮 client.chat.completions.create(...)
-> extract_tool_summary_reply()
-> ChatResponse(reply)
-> HTTP JSON 响应
```

数据流中的事实来源要牢记：

```text
订单状态事实：Java 业务服务
工具可否执行：Python 后端注册表/权限规则
用户可读表述：模型第二轮生成
```

## 常见错误、错误路径与排查方式

### 1. 用户只说“帮我查订单”，没有订单号

预期：第一轮模型直接回复“请提供订单号”，不调用 Java 服务。

排查：

```text
检查第一轮 fake/真实 completion 是否真的没有 tool_calls
检查 TOOL_CHAT_SYSTEM_PROMPT 是否明确“不猜订单号”
检查 history 中是否已经提供了订单号
```

### 2. 模型请求未知工具

例如：

```text
delete_database
```

预期：`authorize_tool_call()` 抛出 `TOOL_NOT_ALLOWED`，HTTP 403。

排查：检查 `TOOL_REGISTRY`、模型可见工具列表和 tool call 原始 name。不要只靠 prompt 说“不要调用危险工具”。

### 3. `arguments` 不是合法 JSON 或格式不对

例子：

```text
{not-json
{"order_id":"A 1001"}
```

预期：

```text
TOOL_ARGUMENTS_INVALID_JSON 或 TOOL_ARGUMENTS_VALIDATION_FAILED
HTTP 502
```

排查：先区分 JSON 解析失败还是 Pydantic 规则失败；再看订单号是否有中间空格、错误字段名或额外字段。

### 4. 模型请求有工具但没有 `call_id`

预期：`TOOL_CALL_ID_MISSING`，并且工具不执行。

排查：查看 provider/model 是否支持当前 Function Calling 结构；确认 SDK 对象中 `tool_calls[0].id` 是否存在。不要通过自己随便生成 ID 来“修复”，因为那会破坏与模型原始请求的关联。

### 5. Java 服务没有启动、超时或返回 500

预期：

| 场景 | 错误 |
| --- | --- |
| 请求超时 | `TOOL_TIMEOUT`，504 |
| 连接失败或 Java 5xx | `TOOL_UPSTREAM_ERROR`，502 |
| 订单不存在 | `ORDER_NOT_FOUND`，404 |

排查顺序：

```text
确认 java-mock-service 是否在 8001 启动
确认 JAVA_MOCK_SERVICE_BASE_URL
直接访问 GET /orders/A1001
查看 AI 服务日志和 Java 服务日志
检查 JAVA_MOCK_SERVICE_TIMEOUT_SECONDS
```

### 6. 工具结果校验失败

预期：`TOOL_RESULT_VALIDATION_FAILED`，502。

常见原因：Java 服务字段缺失、枚举值变更、字符串过长或字段类型错误。

排查：从 `JavaOrderClient.get_order()` 看到原始响应，再检查 `map_java_order_to_query_order_payload()` 与 `QueryOrderResult` 的契约是否同步。生产环境不要为了“先跑起来”跳过校验。

### 7. 第二轮模型没有文本，或者又想调用工具

预期：

```text
空文本 -> LLM_EMPTY_RESPONSE
再次 tool_calls -> TOOL_SUMMARY_UNEXPECTED_TOOL_CALL
```

排查：

```text
确认第二轮 messages 是否保留 assistant tool-call message
确认 tool_call_id 是否正确配对
确认 tool content 是字符串 JSON
查看当前模型/推理模式对 Function Calling 的官方兼容要求
检查 system prompt 是否要求“收到结果后直接回答”
```

## 真实项目中的注意点

### 日志与 trace_id

当前已有请求级 `trace_id`，但以后完整工具链日志应能关联：

```text
trace_id
第一轮模型调用耗时
工具名、call_id、参数摘要
Java 调用耗时与结果码
第二轮模型调用耗时
最终错误码或回答摘要
```

不能记录完整 API key、完整敏感订单数据或不必要的用户隐私。第 16 节会专门把 tool 日志和 trace 串联起来。

### 成本与延迟

本节工具路径有两次模型调用，所以通常比普通 `/chat` 更慢、更贵。真实项目会关注：

```text
第一轮 token
第二轮 token
工具描述 token
history 长度
Java 请求耗时
总响应时间
```

不是每个问题都要工具；模型直接回答分支既是体验优化，也是成本控制。

### 权限和用户身份

当前示例只验证工具自身是否可调用，没有实现“当前用户能否查询 A1001”。真实订单系统至少需要：

```text
用户身份认证
订单归属或角色权限
服务间认证
审计日志
敏感字段脱敏
```

工具白名单不能替代数据权限。

### 超时、重试与幂等

当前查询是只读动作，重复调用通常只增加成本和延迟。未来写操作要同时考虑：

```text
用户确认
幂等键
重试策略
事务或最终一致性
重复执行审计
```

“模型说再试一次”不是自动重试策略；重试必须由后端根据异常类型、次数和业务风险控制。

### 工具循环与安全

生产 Agent 不能无限：

```text
模型 -> 工具 -> 模型 -> 工具 -> ...
```

至少应设计最大轮数、总预算、总超时、允许工具集合、写操作确认、失败终止和审计。当前的 `TOOL_SUMMARY_UNEXPECTED_TOOL_CALL` 是一个教学上的安全护栏。

## Qwen / OpenAI-compatible 手动验证点

自动化测试证明的是：我们自己的消息拼装、校验、错误映射和调用顺序正确；它不能替代真实 provider 兼容性验证。

请在有本机 `.env` 配置、且确认可产生调用费用后，手动验证：

1. 当前 `LLM_MODEL` 是否支持 Function Calling。
2. 第一轮是否返回 `tool_calls[0].id`。
3. 当前模型是否接受 assistant tool-call message 与 tool message 的连续上下文。
4. `tool` message 的 JSON 字符串是否被模型正确理解。
5. 第二轮能否直接总结，而不是返回新的工具请求。
6. 当前模型或思考模式是否要求额外兼容参数。

百炼 Function Calling 官方文档说明了“追加 assistant message、追加含 `tool_call_id` 的 tool message、再调用模型”的流程；具体模型能力和额外参数仍要以当前百炼模型文档与实际调用结果为准。

资料：

- [阿里云百炼：Function Calling](https://help.aliyun.com/zh/model-studio/qwen-function-calling)
- [阿里云百炼：OpenAI Chat 接口兼容](https://help.aliyun.com/zh/model-studio/compatibility-of-openai-with-dashscope)
- [OpenAI Function Calling Guide](https://developers.openai.com/api/docs/guides/function-calling)

## 如何手动运行和验证

先启动 Java mock 服务：

```powershell
cd D:\wendang\java+python+ai\projects\java-mock-service
uv run uvicorn app.main:app --reload --port 8001
```

在另一个终端启动 AI 服务：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run uvicorn app.main:app --reload --port 8000
```

打开：

```text
http://127.0.0.1:8000/docs
```

测试请求：

```json
{
  "message": "帮我查订单 A1001 的物流"
}
```

请求：

```text
POST /tool-chat
```

如果本机模型支持当前工具协议，预期最终响应类似：

```json
{
  "reply": "订单 A1001 已付款，商家已接单，仓库正在准备出库。"
}
```

再依次测试：

| 输入 | 预期 | 验证什么 |
| --- | --- | --- |
| `FastAPI 是什么？` | 直接回答 | 不需要工具时不访问 Java 服务 |
| `帮我查订单` | 提醒提供订单号 | 不猜参数 |
| `帮我查订单 A9999` | `ORDER_NOT_FOUND`，404 | 业务事实错误不被模型掩盖 |
| `帮我查订单 A500` | `TOOL_UPSTREAM_ERROR`，502 | Java 5xx 统一映射 |

真实模型调用可能产生费用。自动化测试不会调用真实模型或真实 Java 服务。

## 重要测试说明

### `test_tool_calling_chat_service.py`

这个文件使用 sequential fake completions，模拟“第一次返回 tool_call、第二次返回文本”的真实顺序。

| 测试类别 | 验证内容 | 防止的问题 |
| --- | --- | --- |
| 消息协议测试 | assistant tool-call 与 tool result 的 ID 一致 | 结果关联到错误请求 |
| 完整成功链路 | 执行 `query_order` 后确实第二次调用模型 | 工具结果没有回传模型 |
| 字段泄露测试 | tool content 不含 `customer_id` | 内部业务字段泄露给模型 |
| 直接回答测试 | 普通问题只调用模型一次 | 无意义工具/Java 调用与额外成本 |
| 缺失 ID 测试 | 不执行工具 | 协议无法闭环仍访问业务系统 |
| 工具错误测试 | 订单不存在时不进入第二轮模型 | 模型掩盖真实业务错误 |
| 第二轮 tool call 测试 | 明确拒绝 | 当前阶段失控进入循环 |
| provider 错误测试 | 映射为统一错误码 | SDK 异常泄露或接口格式不一致 |

### `test_chat_api.py`

它验证 `/tool-chat` 的 HTTP 层：

```text
200 成功响应
history 是否传给 service
没有 API key 时的统一错误
缺少 message 的 422
GET 请求的 405
```

这里通过 FastAPI `dependency_overrides` 注入 fake service。这样 router 测试只关注 HTTP 契约，不会因为模型费用、网络或 Java 服务状态变得不稳定。

### 已有工具和 Java 测试为什么仍重要

`test_fake_order_tool.py`、`test_java_order_client.py`、`test_tools_api.py` 虽不是本节新文件，但它们证明本节依赖的工具层基础正确：字段映射、Pydantic 校验、404/500/timeout 映射、幂等 HTTP 接口行为。完整链路的可靠性依赖每一层都守住自己的契约。

## 练习

### 练习 1：画出最小消息列表

用户说“帮我查订单 A1001”。第一轮模型请求 `query_order`，ID 是 `call_001`。请按顺序写出第二轮模型调用前必须具备的四类消息 role。

#### 练习 1 参考答案

```text
system
user
assistant（携带 id=call_001 的 tool_calls）
tool（携带 tool_call_id=call_001 的结果）
```

### 练习 2：判断哪种结果回传正确

第一轮请求为：

```text
id=call_002
name=query_order
```

下面哪个正确？

1.

```json
{"role":"tool","tool_call_id":"query_order","content":"{...}"}
```

2.

```json
{"role":"tool","tool_call_id":"call_002","content":"{...}"}
```

#### 练习 2 参考答案

第 2 个。`query_order` 是工具种类，`call_002` 才是这一次具体调用的关联 ID。

### 练习 3：判断错误应该由谁处理

场景：Java 服务返回订单不存在。

1. 让第二轮模型自由组织一段安慰性回答。
2. 后端返回 `ORDER_NOT_FOUND` 404，不进行第二轮模型总结。
3. 让模型猜测订单可能已经发货。

#### 练习 3 参考答案

第 2 个。订单是否存在是业务事实；Java/后端返回的错误必须保留，不能交给模型猜测或掩盖。

### 练习 4：解释两次参数校验

为什么第 12 节已经校验 `arguments` 后，本节执行前还要 `QueryOrderArgs.model_validate(tool_call.arguments)`？

#### 练习 4 参考答案

因为解析模型输出与真正执行外部业务工具是两个风险边界。执行点应该独立验证最关键的名称、权限和参数，不能只相信调用链上游已经做过检查。

### 练习 5：设计第二轮异常边界

如果第二轮模型仍然返回 `tool_calls`，当前系统应该：

1. 无限循环继续调用；
2. 假装这是一条正常文本；
3. 返回明确错误并停止；
4. 自动调用所有后端工具。

#### 练习 5 参考答案

第 3 个。本节只支持一次工具执行；正确行为是 `TOOL_SUMMARY_UNEXPECTED_TOOL_CALL`。未来实现工具循环时也必须有最大轮数、超时、预算和权限设计。

## 自测题

### 1. 为什么本节通常需要两次模型调用？

参考答案：第一轮模型没有实时业务事实，只能决定是否需要工具；工具执行后，第二轮模型才能基于经过后端校验的真实结果组织自然语言回答。

### 2. `tool` role 的消息是谁产生的？

参考答案：由后端工具执行器产生，不是用户传入，也不是模型自己编造。它承载的是外部工具执行后得到并经过后端处理的结果。

### 3. `tool_call_id` 为什么不能用工具名代替？

参考答案：同一个工具可以被多次调用，工具名不能精确区分某一次调用；`tool_call_id` 能把结果与第一轮中对应的请求配对。

### 4. 为什么 `tool` 的 `content` 要 JSON 序列化成字符串？

参考答案：当前 OpenAI-compatible Chat Completions 工具消息使用字符串 content。Pydantic 对象先转 JSON 兼容 dict，再序列化为字符串，才能符合 API 协议。

### 5. 模型返回 `query_order` 就说明订单存在吗？

参考答案：不说明。它只表示模型希望查询这个订单。订单是否存在只能由 Java 业务服务返回，后端再将 404 或查询结果映射给客户端。

### 6. 为什么 Java 的 `customer_id` 不会交给模型？

参考答案：工具层使用字段白名单 `map_java_order_to_query_order_payload()`，只选择当前 AI 场景确实需要的字段；随后再由 `QueryOrderResult` 校验。

### 7. 为什么 router 不直接调用 JavaOrderClient？

参考答案：router 应只处理 HTTP 请求、依赖注入和响应；两轮模型调用、权限、工具执行、消息协议属于业务编排，放在 service 更清晰、更可测试。

### 8. `history` 与本节追加的 assistant/tool message 有什么不同？

参考答案：history 是客户端提供的历史 user/assistant 对话，用来理解上下文；assistant/tool message 是当前后端流程为完成一次工具协议闭环而生成的可信消息。

### 9. 为什么工具错误后不调用第二轮模型？

参考答案：订单不存在、超时、上游 500 都是后端已知的事实性错误。直接返回统一错误更可靠，避免模型弱化、改写或编造失败结果。

### 10. 当前第二轮继续请求工具时为什么返回 502？

参考答案：从 AI 服务看，这是上游模型响应超出了当前“一次工具调用”能力边界，无法安全按预期处理；当前将其视为模型响应不可用，而不是用户请求格式错误。

## 面试或工作中的表达练习

可以这样概括本节：

```text
我实现了一个两阶段的只读 Tool Calling 链路。
第一轮由模型选择 query_order，Python 后端对工具名、参数和调用 ID 做校验后，
通过 HTTP 调用 Java 业务服务获取订单事实；工具层使用字段白名单和 Pydantic 约束结果，
再将 assistant 工具请求与带 tool_call_id 的 tool result 回传给第二轮模型生成最终答复。
订单不存在、超时和上游异常由后端统一返回，不让模型编造业务结果；
当前还通过终止条件限制为一次工具执行，避免未经设计的循环。
```

不要死背这段话。你需要能继续解释：为什么两次模型调用、为什么要 ID、为什么要白名单、为什么错误不交给模型处理。

## 本节总结

本节真正学到的不是“新增了 `/tool-chat`”，而是一个可迁移的知识模型：

```text
模型负责理解与表达
后端负责协议、校验、授权、执行和兜底
业务系统负责真实事实
```

完整工具调用的最小协议是：

```text
用户问题
-> assistant 的工具请求（带 call_id）
-> 后端真实执行
-> tool 的执行结果（带同一个 tool_call_id）
-> assistant 的最终回答
```

如果你能解释这个协议、数据流和错误边界，即使以后换成 LangChain、LangGraph、不同的模型 provider、天气工具、数据库工具或企业知识库工具，核心理解仍然成立。

## 本节结束前自检

请确认自己能回答：

- 我能否不看代码画出两轮 Tool Calling 的消息顺序？
- 我能否解释 `assistant tool-call message` 和 `tool message` 的来源差异？
- 我能否说清 `tool_call_id` 为什么像关联 ID？
- 我能否在当前项目定位：工具参数校验、Java 调用、字段过滤、结果校验和第二轮总结分别在哪里？
- 我能否判断订单不存在、Java 超时、第二轮又要工具时应该在哪一层排查？
- 我能否说明为什么模型不能直接操作 Java 业务系统？

如果任何一项回答不顺畅，不要急着进入下一节。先重新看“基础知识铺垫”和“最小天气例子”，再沿调用链阅读代码。

## 下一节衔接

下一节是阶段 3 第 14 节：

```text
用户确认机制：敏感操作不能直接执行
```

本节的 `query_order` 是只读工具，所以后端可以在校验后执行。下一节会处理写操作：即使模型请求 `create_ticket`，后端也只能先生成“待执行计划”，等用户明确确认后才允许真正写入业务系统。
