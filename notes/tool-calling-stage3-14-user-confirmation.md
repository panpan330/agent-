# 阶段 3 第 14 节：用户确认机制——敏感操作不能直接执行

> 本节结论：模型提出“创建工单”不等于用户同意创建，更不等于后端可以立即写入业务系统。确认必须是一份由后端保存、绑定操作者、工具、参数和过期时间的待执行计划。

## 本节目标

第 13 节完成的是只读 `query_order`：模型请求后，后端校验并查询 Java 服务，结果可以直接总结给用户。只读查询不会改变订单、余额或工单状态。

本节面对的是未来的写操作：

```text
create_ticket
refund_order
修改订单地址
发送消息
```

本节新增两个接口，但**不会真正执行写工具**：

```text
POST /tools/confirmations
POST /tools/confirmations/{confirmation_id}/confirm
```

它们完成：

```text
用户/模型提出一个写操作计划
-> 后端保存精确的工具、参数和操作者
-> 后端展示待确认内容
-> 同一操作者确认
-> 状态变为 confirmed
-> 本节到此停止，不执行 Java 写操作
```

第 15 节才会使用 `confirmed` 计划创建真实工单。

## 学习地图

### 从哪里接上来

第 8 节已在注册表中标记：

```text
query_order   read      不需要确认
create_ticket write     需要确认
refund_order  sensitive 禁用且需要确认
```

第 9 节又说明写操作需要幂等性，避免重试重复产生业务效果。

第 13 节完成了“模型请求只读工具 -> 后端执行 -> 模型总结”。本节在真正执行写工具之前插入一道门：确认计划。

### 本节解决的问题

```text
模型说“应该创建工单”
≠ 用户已经同意
≠ 当前登录用户有权限
≠ 参数仍然是用户看到的那一份
≠ 工具现在仍允许执行
```

### 学完后能解释什么

- human-in-the-loop 是什么，为什么不是一个普通确认弹窗；
- 为什么确认必须绑定操作者、工具名、参数、过期时间；
- 为什么确认请求不允许再次提交 arguments；
- 参数指纹、确认 ID、确认幂等分别解决什么问题；
- 为什么确认成功也不等于已经执行；
- 当前 `actor_id` 为什么只是教学占位，生产环境必须来自认证身份。

### 本节不学什么

- 不创建真实工单；
- 不实现 Java 写接口；
- 不实现 JWT、登录和 RBAC；
- 不实现数据库/Redis 持久化确认计划；
- 不实现退款或多级审批。

## 基础知识铺垫

### 1. 读操作、写操作与敏感操作

**人话**：查订单像看账单；创建工单像提交表单；退款像转走钱。风险逐级上升。

**工程术语**：read / write / sensitive action。写操作会改变业务状态，敏感操作还可能造成资金、隐私或合规后果。

**没有分类会怎样**：后端可能把“查订单”和“退款”用同一条自动执行规则处理，模型的一次误判就会造成不可逆影响。

**当前项目**：`ToolAccessLevel`、`ToolDefinition.requires_confirmation`、`enabled` 共同描述工具边界；`create_ticket` 是 write，`refund_order` 是 sensitive 且 disabled。

### 2. 什么是 human-in-the-loop

**人话**：AI 可以准备好一份“准备创建工单”的草稿，但最后按下确认键的人必须是用户或有权限的人工。

**工程术语**：human-in-the-loop（人在环路中）、approval gate（审批门）或 policy enforcement point（策略执行点）。

**它解决什么问题**：模型可能误解、幻觉或被 prompt injection 诱导。高影响动作需要人确认最终意图。

**真实开发**：退款、转账、发布公告、删除资源、发送对外邮件、修改权限都常见确认/审批。

OWASP 将过度自主、过大权限和过多工具能力视为 Excessive Agency 风险，并建议对高风险动作保留人工批准与最小权限。 [OWASP LLM06:2025 Excessive Agency](https://genai.owasp.org/download/43299/?tmstv=1731900559)

### 3. 确认不是一句“好的”

下面对话不可靠：

```text
模型：要为 A1001 创建工单吗？
用户：好的
```

“好的”可能是在回答上一个问题，也可能没有说明确认的是哪个订单、哪个标题、哪个操作者。可靠确认需要后端保存的计划：

```text
confirmation_id
actor_id
tool_name
arguments
arguments_fingerprint
created_at / expires_at
status
```

这叫 confirmation plan（确认计划）。当前项目把它保存在 `ToolConfirmationStore`。

### 4. 确认 ID 与关联 ID

第 13 节的 `tool_call_id` 用来关联“模型请求”和“工具结果”。本节的 `confirmation_id` 用来关联“待确认计划”和“用户确认”。两者都属于 correlation ID（关联 ID），但服务对象不同。

```text
tool_call_id：模型工具协议内部配对
confirmation_id：用户审批流程中的计划配对
```

没有确认 ID，确认接口就只能重新接收工具名和参数，极易被替换。

### 5. 参数绑定与参数指纹

**人话**：用户确认的是“为 A1001 创建标题为 X 的工单”，不是“同意系统以后随便创建一个工单”。

**工程术语**：parameter binding（参数绑定）、fingerprint/hash（指纹/哈希）。

本项目复用第 9 节 `build_arguments_fingerprint()`：它将工具名和规范 JSON 参数排序后计算 SHA-256。指纹能帮助日志、审计和测试判断“确认前后的计划是否是同一份”。

更关键的是：确认接口根本不接收新 `arguments`；它只按 ID 从后端存储读取原参数。因此指纹不是唯一安全措施，后端保存的原计划才是事实来源。

### 6. 操作者绑定不等于真正认证

本节请求里有 `actor_id="demo_user_001"`，确认时必须相同。

这演示了 actor binding（操作者绑定）：A 创建的计划，B 不能确认。

但当前 `actor_id` 由客户端 JSON 传入，**不能当成真实身份认证**。生产环境必须从 JWT、session、网关认证或服务端身份上下文中取得用户 ID；客户端自己说“我是管理员”不可信。

### 7. 为什么确认计划必须过期

用户上午确认的“给 A1001 建工单”可能下午已经不适用：订单状态变了、权限变了、参数变了。短期 TTL（time to live）让旧意图失效。

本项目配置：

```text
TOOL_CONFIRMATION_TTL_SECONDS=300
```

即五分钟。过期确认返回 `TOOL_CONFIRMATION_EXPIRED` 409，必须重新创建计划。

### 8. 确认本身也要幂等

网络重试可能让用户点两次确认。对同一计划、同一操作者，第二次确认不应报错或创建第二份计划；状态保持 `confirmed` 即可。

这与第 9 节“写工具的幂等”有关但不相同：本节确认动作幂等，未来真正创建工单的写动作也必须独立幂等。

### 9. 计划确认与工具执行必须分离

本节确认成功的 message 是：

```text
确认已记录；当前阶段仍不会执行工具。
```

这是刻意设计。确认只证明用户批准了某份计划；执行时仍要再次检查：工具是否启用、用户是否仍有权限、计划是否已确认且未被消费、业务前置条件是否成立。

### 10. 内存存储只是教学实现

`ToolConfirmationStore` 使用进程内 `dict + Lock`。它便于理解状态机和写单元测试，但生产环境有明显限制：

```text
服务重启会丢数据
多实例之间不共享
没有持久审计
没有分布式锁/事务
```

真实系统通常用数据库或 Redis，加 TTL、唯一约束、审计表、身份认证和消费状态。

## 最小例子：确认什么才算可靠

不可靠：

```text
前端：POST /execute {"tool_name":"refund_order","confirmed":true}
```

问题：用户到底确认了哪个订单、金额、操作者？请求是否被篡改？

本节可靠流程：

```text
1. 创建计划：A 为 create_ticket + 参数 P 创建 confirmation_id=C
2. 后端保存 A、create_ticket、P、fingerprint、expires_at
3. A 使用 C 确认；确认请求不带新参数
4. 后端检查 A、C、未过期，状态改 confirmed
5. 第 15 节才会从 C 读取原计划并执行
```

## 本节新增/修改代码详细讲解

### `schemas/tool_confirmation.py`：把确认请求变成数据契约

`ToolConfirmationRequest` 的输入是：

```python
actor_id: str
tool_name: str
arguments: dict[str, Any]
```

它使用 `extra="forbid"` 拒绝多余字段，`actor_id`/`tool_name` 用正则限制格式，`arguments` 不允许空。现在还没有 `CreateTicketArgs`，所以 arguments 保持通用 dict；第 15 节会为具体工单字段建立更严格 schema。

`ConfirmToolConfirmationRequest` 只有 `actor_id`，故意没有 `tool_name` 和 `arguments`。这正是防止确认时替换计划的关键。

`ToolConfirmationResponse` 返回后端保存的精确计划、状态、指纹和过期时间，让前端能清楚展示“你将确认什么”。

### `tools/tool_confirmation.py`：最小确认状态机

`ToolConfirmationRecord` 是内部记录，含 pending/confirmed 状态。

`ToolConfirmationStore.create()`：

1. 用 `uuid4().hex` 生成不透明 `confirmation_id`；
2. 深拷贝 arguments，避免调用方后来修改同一个 dict；
3. 用第 9 节 helper 计算工具名 + 参数的 SHA-256 指纹；
4. 记录 UTC 创建时间和 TTL 过期时间；
5. 在 `Lock` 保护下写入内存 dict。

`ToolConfirmationStore.confirm()`：

1. 按 ID 查找计划；不存在返回 404；
2. 比较 `actor_id`，不同返回 403；
3. 检查当前时间，过期返回 409；
4. pending 改为 confirmed；已 confirmed 则原样返回，保证确认幂等。

### `services/tool_confirmation_service.py`：业务规则编排

`request_confirmation()` 先调用 `require_enabled_tool_definition()`：未知或禁用工具一律 `TOOL_NOT_ALLOWED`。随后检查 `requires_confirmation`；只读 `query_order` 不应进入确认流程，返回 `TOOL_CONFIRMATION_NOT_REQUIRED`。

`confirm()` 不接收新参数，只委托 store 从已保存计划中确认。`_to_response()` 根据状态生成“待确认但未执行”或“已确认但仍未执行”的提示。

### `tool_registry.py`：分离“工具启用”与“是否已经确认”

新增 `require_enabled_tool_definition()`，只负责检查工具存在且 enabled。原有 `authorize_tool_call()` 复用它，再额外判断 `requires_confirmation` 和 `user_confirmed`。

这样确认服务可以安全地询问“这个工具是否允许被计划”，而真正执行点仍由 `authorize_tool_call()` 把关。

### `routers/tools.py`：HTTP 边界保持薄

新增：

```text
POST /tools/confirmations
POST /tools/confirmations/{confirmation_id}/confirm
```

router 只负责 Pydantic 请求校验、依赖注入和不含敏感参数内容的日志；计划创建、操作者检查、过期判断都在 service/store。

### `Settings`：确认 TTL 也是配置

`tool_confirmation_ttl_seconds` 默认 300，范围 30-3600。有效期是安全/体验取舍：太长增加陈旧确认风险，太短让用户频繁重来。生产环境通常按动作风险分级配置。

## 完整调用链路

```text
POST /tools/confirmations
-> ToolConfirmationRequest 校验
-> ToolConfirmationService.request_confirmation()
-> require_enabled_tool_definition()
-> requires_confirmation 检查
-> ToolConfirmationStore.create()
-> confirmation_id + 参数指纹 + expires_at
-> pending ToolConfirmationResponse

POST /tools/confirmations/{id}/confirm
-> ConfirmToolConfirmationRequest（只有 actor_id）
-> ToolConfirmationService.confirm()
-> ToolConfirmationStore.confirm()
-> ID、操作者、TTL、状态检查
-> confirmed ToolConfirmationResponse
-> 本节停止，不执行工具
```

## 常见错误和排查

| 现象 | 优先排查 | 预期结果 |
| --- | --- | --- |
| 给 `query_order` 创建确认计划 | 工具是否 requires confirmation | `TOOL_CONFIRMATION_NOT_REQUIRED` 409 |
| 确认 ID 不存在 | 前端是否使用了旧 ID、服务是否重启 | `TOOL_CONFIRMATION_NOT_FOUND` 404 |
| 他人确认 | actor 是否与创建计划一致 | `TOOL_CONFIRMATION_FORBIDDEN` 403 |
| 过期后确认 | `expires_at`、TTL 配置、系统时间 | `TOOL_CONFIRMATION_EXPIRED` 409 |
| 确认请求带新 arguments | schema `extra="forbid"` | FastAPI 422 |
| 以为 confirmed 已创建工单 | 查看本节边界与 Java 服务记录 | 本节不会调用 Java 写接口 |

## 真实项目注意点

- `actor_id` 必须来自认证上下文，不信任客户端字段；
- 确认页面必须展示完整但脱敏后的工具/参数/diff；
- 执行前必须再次权限校验，确认不应永久授权；
- 确认计划需要持久化、审计、TTL 和消费状态；
- 写操作执行还要使用独立幂等键；
- trace_id 应串起“模型建议 -> 计划 -> 用户确认 -> 未来执行”；
- 高风险动作可要求二次验证、双人审批或强认证；
- 模型输出始终是不可信输入，不能让模型自己声称“用户已确认”。

OWASP 也建议对高风险操作实施人工批准、最小权限和输入/输出审查。 [OWASP Prompt Injection mitigations](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)

## 如何手动验证

启动 AI 服务：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run uvicorn app.main:app --reload --port 8000
```

创建计划：

```json
POST /tools/confirmations
{
  "actor_id": "demo_user_001",
  "tool_name": "create_ticket",
  "arguments": {"title": "订单 A1001 未发货", "order_id": "A1001"}
}
```

复制响应中的 `confirmation_id`，再确认：

```json
POST /tools/confirmations/{confirmation_id}/confirm
{"actor_id": "demo_user_001"}
```

确认 `status` 从 `pending` 变为 `confirmed`，并确认 Java mock 服务没有新增任何写入动作——这正是本节验证点。

## 重要测试说明

- `test_tool_confirmation_schema.py`：防止空参数、非法身份和确认时偷偷加入新 arguments。
- `test_tool_confirmation_service.py`：验证工具/操作者/参数绑定、TTL、确认幂等、禁用工具和只读工具边界。
- `test_tools_api.py`：验证 HTTP 状态码、trace_id、两步 API 协议以及客户端篡改参数时的 422。
- `test_tool_registry.py`：验证“工具启用检查”和“执行前确认检查”仍是两道不同关口。

自动化测试不调用模型、不访问 Java 服务，因为本节确认计划本身不应产生外部业务动作。

## 练习

### 练习 1：判断确认对象

用户确认“为 A1001 创建标题为‘未发货’的工单”后，确认请求应再携带哪些内容？

#### 参考答案

只携带 confirmation ID（在路径中）和可信操作者身份。工具名与参数应从后端保存的计划读取，不能由确认请求重新提交。

### 练习 2：确认与执行

`status="confirmed"` 是否说明工单已经创建？

#### 参考答案

不是。它只说明用户批准了固定计划。本节没有写 Java API；第 15 节执行时仍需重新校验权限、确认状态和业务前置条件。

### 练习 3：过期原因

为什么确认计划要有 TTL？

#### 参考答案

避免旧意图在订单、权限或参数已经变化后仍被执行。过期后应重新展示最新计划并再次确认。

### 练习 4：actor_id 的局限

当前 JSON 里的 `actor_id` 能当真实身份认证吗？

#### 参考答案

不能。它只用于教学演示绑定关系；生产环境必须从 JWT、session 或网关认证的可信上下文获取用户身份。

### 练习 5：确认幂等

用户网络重试导致确认接口被调用两次，应怎样处理？

#### 参考答案

同一操作者对同一未过期计划重复确认，应返回同一 confirmed 计划，而不是报错或创建第二份计划；真正写操作仍需自己的幂等保护。

## 自测题

1. 为什么模型说“用户已确认”不可信？

   参考答案：模型输出是不可信输入，可能误解、幻觉或被注入攻击影响；确认必须由后端记录的用户操作和可信身份决定。

2. 参数指纹解决什么问题？

   参考答案：它为固定工具名和参数生成稳定摘要，用于审计、比较和测试；但真正防篡改依赖后端保存原计划且确认接口不接收新参数。

3. 为什么本节对 `query_order` 返回“无需确认”？

   参考答案：它是 enabled 的只读工具，不改变业务状态。对它强制确认只会增加无意义交互；风险等级决定流程。

4. 为什么 disabled 的 `refund_order` 不能创建确认计划？

   参考答案：确认不是绕过开关的后门。工具未启用时，无论是否有人确认，后端都应拒绝。

5. 确认计划和第 9 节幂等键有什么关系？

   参考答案：两者都绑定参数，但确认计划记录用户批准的意图；幂等键防止真正写操作重复产生业务效果。未来执行时两者都需要。

## 基础知识扩展讲解：把“确认”理解成后端状态机

前面的基础知识给出了结论。这里再把最容易在工作和面试中混淆的概念拆开。不要把“确认”理解成一个前端按钮；它本质是后端维护的有限状态机（finite-state machine）。

### 扩展 1：意图、授权、认证、确认、执行是五件不同的事

下面五句话看起来接近，工程上却必须分开：

| 阶段 | 人话 | 工程含义 | 当前项目位置 |
| --- | --- | --- | --- |
| 意图 | 模型建议“创建工单” | model intent / tool request | 第 12、13 节的 `tool_calls` |
| 认证 | “你是谁？” | authentication | 当前项目尚未实现，`actor_id` 只是占位 |
| 授权 | “你有没有资格做？” | authorization | `enabled`、风险等级、未来订单权限 |
| 确认 | “你是否同意这份具体计划？” | explicit confirmation | `ToolConfirmationStore.confirm()` |
| 执行 | “现在真正写入业务系统” | execution / side effect | 第 15 节才实现 |

一个常见错误是把它们压缩成：

```text
模型有意图 -> 立即执行
```

这会跳过四道不同的安全门。另一个错误是认为“用户确认了”就等于“用户有权限”；确认不能代替权限校验。

### 扩展 2：状态机为什么比 `confirmed: true` 更可靠

如果请求体只有：

```json
{"confirmed": true}
```

后端不知道它确认的是哪一份操作，也不知道这个确认是否已经过期、是否来自正确操作者、是否已经被消费。

本节的最小状态机是：

```text
不存在
  -> pending（创建确认计划）
  -> confirmed（同一操作者确认）

pending --过期--> 拒绝确认
pending --他人确认--> 拒绝确认
confirmed --重复确认--> 仍为 confirmed
```

第 15 节会再增加“已执行/已消费”的状态。为什么现在不加？因为本节还没有写工具执行；提前设计一堆未使用状态，会掩盖当前最重要的 pending -> confirmed 关系。

### 扩展 3：TOCTOU——为什么确认后执行前还要再检查

TOCTOU 是 time of check to time of use（检查时刻与使用时刻不一致）问题。

例子：

```text
10:00 用户创建确认计划，create_ticket 工具启用。
10:02 管理员禁用 create_ticket，或用户权限被收回。
10:03 用户点击确认。
10:04 系统准备执行。
```

即使 10:03 确认成功，10:04 的真正执行点也必须再次检查工具启用状态、用户权限和业务前置条件。确认计划记录的是“用户当时同意了什么”，不是永久通行证。

这解释了为什么本节的 confirmed 状态不直接调用工具，也解释了第 15 节为什么不能只看 `status == confirmed`。

### 扩展 4：参数指纹不是加密授权令牌

`arguments_fingerprint` 是 SHA-256 摘要，适合回答：

```text
确认前后的 tool_name + arguments 是否完全相同？
```

它适合日志、审计、测试和冲突判断。但它不是：

```text
用户身份凭证
权限凭证
可直接执行的签名令牌
```

当前防止参数替换的主机制是：确认接口的 schema 根本不允许 `arguments`，后端只从内存计划读取原始参数。指纹是可观察、可比较的补强，而不是唯一防线。

### 扩展 5：为什么要深拷贝 arguments

Python 的 `dict` 是可变对象。假设 store 直接保存了调用方传入的同一个 dict：

```python
arguments = {"order_id": "A1001"}
store.create(arguments=arguments)
arguments["order_id"] = "A1002"
```

如果没有 `deepcopy`，已展示给用户确认的计划可能在内存中被悄悄改成 A1002。`ToolConfirmationStore.create()` 深拷贝参数，确保记录是当时的快照（snapshot）。

这也是 Python 基础知识在安全场景中的新用法：可变对象的引用共享不仅会造成普通 bug，也会造成确认对象漂移。

### 扩展 6：确认幂等与执行幂等不能混为一谈

重复确认：

```text
同一 actor 对同一 confirmation_id 点击两次
-> 都返回 confirmed
-> 不新增计划
```

这是确认幂等。

重复执行：

```text
同一 confirmed 计划被网络重试两次
-> 不能创建两张工单
```

这是写操作幂等。第 9 节的 `Idempotency-Key` 将在第 15 节重新进入流程。二者都与“重复”有关，但保护的业务动作不同。

### 扩展 7：为什么 UI 弹窗不是安全边界

前端可以显示“确定创建吗？”弹窗，但攻击者、脚本或旧版本客户端可以绕过前端，直接请求后端 API。真正的安全规则必须在后端：

```text
后端只接受存在、未过期、属于当前 actor 的 confirmation_id。
```

这与第 8 节“prompt 不是安全边界”是同一个思想：前端提示和模型提示用于改善体验；后端校验才是强制规则。

### 扩展 8：确认页面应该展示什么

真正的确认 UI 不能只显示“是否继续？”。至少应展示：

```text
动作：创建工单
对象：订单 A1001
关键参数：标题、描述、优先级
影响：将向业务系统写入一条新记录
有效期：五分钟
操作者：当前登录用户
```

高风险动作还应展示 diff、金额、收款人、权限变化等。用户确认的是可读、具体、可预期的业务影响。

### 扩展 9：锁与并发

`ToolConfirmationStore` 用 `Lock` 保护内存 dict。人话说：两条线程不能在同一瞬间把同一份 pending 计划都当成“还没确认”去修改。

但这只适用于单 Python 进程。生产多实例部署时，每台机器都有自己的 dict 和 Lock，彼此不知道对方发生了什么。因此要用数据库事务、Redis 原子操作或分布式锁，并设计“确认/消费”唯一约束。

### 扩展 10：审计为什么重要

确认流程适合记录：

```text
confirmation_id
trace_id
actor_id
tool_name
arguments_fingerprint
created_at
confirmed_at
executed_at
execution_result
```

这样发生争议时能回答：谁在何时批准了什么、后来是否执行、执行结果如何。注意审计不等于把全部敏感参数明文写日志；应该按数据分类脱敏或分级存储。

## 最小转账例子：先看清流程，再回到工单

假设工具是：

```text
transfer_money(to="merchant_001", amount=100)
```

错误设计：

```text
模型：建议转 100 元
-> 后端立刻转账
```

稍好但仍错误：

```text
前端弹窗“确认吗？”
-> POST /transfer {"confirmed": true}
```

本节模型：

```text
POST /confirmations
  保存 to=merchant_001、amount=100、actor=U1、TTL
  返回 C123

POST /confirmations/C123/confirm
  只带 U1
  后端读取原计划并确认

未来 POST /execute
  读取 C123
  再次权限检查 + 写操作幂等
  才真正转账
```

把 `transfer_money` 换成 `create_ticket`，就是本项目。转账例子能帮助你看出：确认机制并不依赖 LLM；LLM 只是可能触发这条流程的上游建议者。

## 关键函数逐段深入

### `ToolConfirmationRequest`：入口不是“任意 JSON”

它用 `ConfigDict(extra="forbid")`。这表示客户端多传 `confirmed`、`is_admin` 等字段时不会被静默忽略或误用，而会得到 422。

`actor_id` 与 `tool_name` 先 `strip()`，再正则校验。先 trim 的意义和第 12 节订单号一致：允许用户在前后多打空格，但不允许中间混入非法字符。

`arguments` 只做“非空 JSON 对象”校验，因为具体 `CreateTicketArgs` 还没到第 15 节。这里必须明确边界：通用确认计划不等于具体业务参数校验已经完成。

### `ToolConfirmationStore.create()`：从输入变成不可漂移计划

输入：actor、工具名、参数、TTL。输出：完整 `ToolConfirmationRecord`。

关键步骤是：生成 UUID、深拷贝参数、计算指纹、写入 created/expires、加锁存储。返回值也 `deepcopy`，避免 service/response 层意外修改内部记录。

### `ToolConfirmationStore.confirm()`：四个必须按顺序看的分支

```text
1. 找不到 ID -> 404：不能确认不存在的计划
2. actor 不同 -> 403：不能代替别人确认
3. 时间已到 -> 409：旧意图无效
4. pending -> confirmed；已 confirmed 直接返回：确认幂等
```

分支顺序也有意义：先找记录，再比较身份，再判断有效期，最后改状态。每个分支都把业务规则变成可测试的后端事实，而不是依赖 UI 或模型解释。

### `ToolConfirmationService.request_confirmation()`：确认前也要看工具开关

它先调用 `require_enabled_tool_definition()`。这与直接执行时的 `authorize_tool_call()` 不同：此时我们还没确认，只是在决定能不能创建一份计划。

```text
未知/disabled -> TOOL_NOT_ALLOWED
enabled 但不需确认 -> TOOL_CONFIRMATION_NOT_REQUIRED
enabled 且 requires_confirmation -> 创建 pending 计划
```

这防止确认接口成为绕过 `enabled=False` 的后门。

### `ToolConfirmationService.confirm()`：为什么没有工具执行代码

它只调用 store.confirm 并转成 response。少做不是遗漏，而是本节设计：确认和执行分离。第 15 节会明确引入“消费已确认计划”的执行函数；到那时仍要再次授权和做写操作幂等。

### router：为什么确认接口仍需要 service dependency

`get_tool_confirmation_service()` 把当前 Settings 与全局 store 组合。router 负责 HTTP/Pydantic/日志，service 负责规则，store 负责状态。这样 service 单测可以注入假时钟和独立 store，不需要启动 FastAPI。

## 与第 8、9、13 节如何组合

```text
第 8 节：什么工具允许、什么工具需要确认
第 9 节：真正写操作重复执行怎么办
第 13 节：只读工具如何回传真实结果给模型
第 14 节：写操作在执行前如何固定计划并得到用户批准
第 15 节：具体创建工单字段 + 已确认计划 + Java 写 API + 幂等
```

这五节不是彼此独立的技巧，而是一条逐步收紧的安全链。

## 额外排查决策树

```text
确认失败
├─ 404 -> confirmation_id 是否来自当前服务进程？服务是否重启？
├─ 403 -> actor_id 是否一致？生产环境身份是否可信？
├─ 409 expired -> TTL 是否过短？客户端是否停留太久？
├─ 409 not required -> 是否误把 read 工具放进确认流程？
├─ 403 not allowed -> 工具是否 disabled 或名称错误？
└─ 422 -> 是否在确认请求中偷偷传了 arguments/tool_name，或 schema 字段不合法？
```

## 补充练习

### 练习 6：识别 TOCTOU

用户在上午确认创建工单，下午管理员禁用了该工具。第 15 节真正执行前应该做什么？

#### 参考答案

再次检查工具是否 enabled、用户是否仍有权限、计划是否 confirmed 且未过期/未消费。确认不能替代执行时授权。

### 练习 7：为什么不能只保存 fingerprint

如果后端只保存参数指纹、不保存原始参数，为什么第 15 节难以执行？

#### 参考答案

哈希只能比较“是否相同”，不能还原标题、描述和订单号。执行时需要后端保存的原始、已验证参数；指纹只是辅助审计和比较。

### 练习 8：生产身份来源

为什么生产环境不能让浏览器传 `actor_id="admin"`？

#### 参考答案

任何客户端字段都可伪造。服务端应从已经验证的 JWT、session、网关 header 或内部身份系统获得当前主体，再把它绑定到计划。

## 扩展自测题

6. `confirmation_id` 是不是权限凭证？

   参考答案：不是。它用于定位计划，确认时仍需匹配可信 actor；执行时还需再次授权。生产中还应避免 ID 可预测和日志泄露。

7. 为什么 pending 计划返回完整 arguments，确认请求却不允许传 arguments？

   参考答案：前者用于让用户看清将要发生什么；后者防止确认时篡改计划。展示与提交是不同的安全需求。

8. 为什么过期返回 409 而不是 404？

   参考答案：计划曾经存在，但当前状态与操作要求冲突：它已不再可确认。404 更适合从未存在或无法找到的 ID。

9. 为什么 store 使用 UTC 时间？

   参考答案：服务器可能跨时区部署；UTC 避免本地时区和夏令时造成过期判断混乱。展示给用户时再转换为本地时区。

10. 本节的最大安全缺口是什么？

   参考答案：没有真实认证和持久化；`actor_id` 可被客户端伪造，内存记录重启即丢失。因此它是教学确认机制，不是可直接上线的审批系统。

## 从一次用户操作到确认状态的逐帧演练

下面用当前接口真实允许的 `create_ticket` 计划走一遍。注意：此处只创建计划，不创建工单。

### 第 1 帧：客户端提出“请展示确认计划”

```http
POST /tools/confirmations
```

```json
{
  "actor_id": "demo_user_001",
  "tool_name": "create_ticket",
  "arguments": {
    "title": "订单 A1001 未发货",
    "description": "用户反馈订单迟迟未发货。",
    "order_id": "A1001"
  }
}
```

这里不要误解：这不是“执行创建工单”的请求，而是“请后端创建一份待确认计划”的请求。

### 第 2 帧：FastAPI 与 Pydantic 守住入口

FastAPI 把 JSON 交给 `ToolConfirmationRequest`。它会检查：

```text
actor_id 非空且格式合法
tool_name 非空且格式合法
arguments 是非空对象
没有多余字段
```

如果用户传：

```json
{"actor_id":"demo_user_001","tool_name":"create_ticket","arguments":{},"confirmed":true}
```

它不会“宽容地忽略” `confirmed`；会返回 422。对安全入口来说，拒绝不认识的字段往往比静默忽略更容易发现客户端/攻击者行为异常。

### 第 3 帧：service 确认这确实是可计划的工具

`ToolConfirmationService.request_confirmation()` 调用：

```python
definition = require_enabled_tool_definition(request.tool_name)
```

此时的判断不是“用户已经确认了吗”，而是更早的问题：

```text
这个工具存在吗？
当前启用吗？
它真的属于需要确认的工具吗？
```

因此：

```text
create_ticket -> 可以创建 pending 计划
query_order -> 409，无需确认
refund_order -> 403，当前禁用
delete_database -> 403，不在后端工具表
```

### 第 4 帧：store 将用户看到的计划冻结

假设当前时间为 `10:00:00 UTC`，TTL 为 300 秒。store 会保存近似：

```text
confirmation_id = c7...（随机 32 位 hex）
status = pending
actor_id = demo_user_001
tool_name = create_ticket
arguments = {title, description, order_id}
arguments_fingerprint = sha256(...)
created_at = 10:00:00 UTC
expires_at = 10:05:00 UTC
```

这里有两个“冻结”：

1. 参数通过 `deepcopy` 冻结为独立快照；
2. 指纹记录这个快照的可比较摘要。

后端返回同样的可读信息，前端才能向用户展示：“你即将确认的就是这一份计划。”

### 第 5 帧：用户确认时不重传业务参数

正确请求：

```http
POST /tools/confirmations/{confirmation_id}/confirm
```

```json
{"actor_id":"demo_user_001"}
```

为什么没有 title/order_id？因为这些数据不是“用户第二次输入的事实”，而是“用户第一次看到并准备确认的计划内容”。确认接口从 store 读取它们。

如果前端因 bug 传了：

```json
{"actor_id":"demo_user_001","arguments":{"order_id":"A1002"}}
```

Pydantic 的 `extra="forbid"` 返回 422；不会发生“确认 A1001，实际保存 A1002”的静默替换。

### 第 6 帧：确认的三个安全判断

`ToolConfirmationStore.confirm()` 依次检查：

```text
确认 ID 是否存在？
当前 actor 是否与计划 actor 相同？
现在是否早于 expires_at？
```

只有都成立，才做：

```text
pending -> confirmed
```

这里可以用 Java 类比：它有点像业务表中的一条待审批记录，状态更新必须带条件，例如：

```sql
UPDATE confirmation
SET status = 'CONFIRMED'
WHERE id = ? AND actor_id = ? AND status = 'PENDING' AND expires_at > now()
```

本项目用内存 dict 演示相同的业务条件；生产环境应依靠数据库原子条件更新或 Redis Lua/事务保证并发正确性。

### 第 7 帧：confirmed 不产生副作用

响应中的：

```json
{"status":"confirmed"}
```

只代表批准记录已存在。当前 Java mock 服务没有收到 POST 请求，工单也没有创建。这是本节最重要的边界验证。

## HTTP 状态码为什么这样设计

| 状态 | 当前含义 | 为什么不是别的状态 |
| --- | --- | --- |
| 422 | 请求结构不合法，例如确认时多传 arguments | 客户端入口参数校验失败 |
| 403 | 工具禁用、未知，或 actor 不同 | 后端拒绝该主体/该工具的权限边界 |
| 404 | confirmation_id 不存在 | 要确认的资源找不到 |
| 409 | 无需确认、计划过期 | 请求格式正确，但当前资源状态不允许这个动作 |
| 200 | pending 创建成功或 confirmed 成功 | 当前阶段没有真正执行业务写入 |

不要机械背状态码。判断方法是：请求格式对不对、资源存不存在、调用方有没有资格、资源当前状态是否允许操作，这四类问题分别对应不同处理层。

## 八个特别容易犯的工程错误

### 错误 1：把确认放在 prompt 里

```text
system: 只有用户确认后才能退款
```

模型仍可能被误导或误判“用户确认了”。prompt 只能帮助模型对话，不能替代后端存储和权限检查。

### 错误 2：确认接口接受完整工具参数

这是本节专门避免的参数替换漏洞。确认接口只接收 confirmation ID 和可信身份。

### 错误 3：confirmed 后不再检查权限

确认发生时和执行发生时可能相隔数秒或数天。执行前必须再次授权，防 TOCTOU。

### 错误 4：用客户端时间判断过期

客户端时钟可错误或被伪造；过期判断必须用服务端 UTC 时间。

### 错误 5：把确认记录只存在浏览器 localStorage

用户可修改、多个客户端不同步、服务端无法审计。确认事实必须由服务端保存。

### 错误 6：把 parameters fingerprint 当成密码

哈希可以比较，不能证明请求者是谁，也不能单独授权执行。

### 错误 7：重复确认后创建多个副作用

本节的确认已经幂等；第 15 节写 API 还要独立幂等，不能因为“用户只点了一次”就放弃保护。

### 错误 8：为了方便让模型直接设置 status=confirmed

模型输出不可信。状态只能由后端接收真实用户确认、验证身份和计划后变更。

## 面试表达与工作迁移

可以这样描述本节，不要只说“我加了一个确认接口”：

```text
我把高风险工具从模型自动执行链路中拆出，设计了服务端确认计划。
计划绑定操作者、工具名、参数快照、参数指纹和短期 TTL；确认接口只接收确认 ID 与操作者，
避免确认时参数被替换。确认状态与真正工具执行分离，未来执行前仍会重新授权并使用写操作幂等键。
当前内存实现用于教学，生产会替换为带认证、持久化、审计和原子消费的数据库或 Redis 方案。
```

如果面试官追问“为什么确认后还要再次授权”，就用 TOCTOU、权限变化和计划过期解释；如果追问“为什么不让前端传 confirmed”，就用服务端事实、参数绑定和客户端可伪造解释。

## 本节结束前自检

请不用看代码尝试回答：

1. 为什么确认不是一个布尔字段？
2. 为什么 confirmation_id 与 tool_call_id 不能混用？
3. 为什么确认请求不能重传工具参数？
4. 为什么 pending/confirmed 不是最终执行状态？
5. 为什么 actor_id 在当前项目还不够安全？
6. 为什么确认幂等与创建工单幂等要分别实现？
7. 如果服务重启，当前内存计划会怎样？生产怎么办？
8. 你能在代码中指出 schema、store、service、router 分别在哪里吗？

如果不能顺畅回答，优先复习“基础知识铺垫”“逐帧演练”和“关键函数逐段深入”，不要急着进入第 15 节。

## 本节总结

本节建立的核心模型是：

```text
模型提出建议
-> 后端生成固定确认计划
-> 用户确认该计划
-> 后端以后才有资格尝试执行
```

确认不是一句自然语言“好的”，不是模型字段 `confirmed=true`，也不是直接执行。它是一段可审计、可过期、绑定操作者和参数的后端状态。

## 下一节衔接

第 15 节“创建工单流程：提取字段、确认、调用 Java API”会新增具体 `CreateTicketArgs`、Java mock 写接口，并且只消费本节已经 confirmed 的计划。届时会再次校验权限和确认状态，再加写操作幂等保护。
