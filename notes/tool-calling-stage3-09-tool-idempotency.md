# 阶段 3 第 9 节：工具调用幂等性

## 本节目标

上一节我们解决的是：

```text
模型想调用工具，后端到底允不允许执行？
```

这一节解决的是：

```text
同一个工具调用如果被重复发送，后端会不会重复执行？
```

这在 AI Agent 里非常重要。
因为工具调用不是普通聊天文本，它可能真的改变业务系统。

比如：

```text
创建工单
申请退款
取消订单
发送短信
扣减库存
修改用户权限
```

如果这些动作被重复执行，就不是“多回复一句话”的问题，而是会产生真实业务事故。

本节学完你要能解释：

- 什么是幂等性。
- 为什么 AI 工具调用特别需要幂等性。
- 什么是 `Idempotency-Key`。
- 为什么同一个幂等键只能配同一组参数。
- 为什么后端要保存第一次执行结果。
- 为什么重复请求应该返回旧结果，而不是再执行一次。
- 当前项目里 `run_idempotent_tool(...)` 做了什么。
- 当前内存版幂等实现有什么局限。
- 生产环境应该如何升级成数据库或 Redis 版本。

## 一句话理解幂等性

先记一句话：

```text
同一个操作执行一次和执行多次，最终效果应该一样。
```

举例：

```text
把订单状态设置为已取消
```

如果执行一次，订单变成已取消。
如果重复执行十次，订单还是已取消。
这个动作比较容易做成幂等。

再看另一个动作：

```text
创建一个新工单
```

如果执行一次，创建 1 个工单。
如果重复执行十次，可能创建 10 个工单。
这个动作默认不是幂等的。

所以我们要给它加一层保护，让它变成：

```text
同一个创建请求重复发送，只创建 1 个工单。
后面的重复请求直接返回第一次创建出来的工单。
```

这就是工具调用幂等性的核心。

## 为什么 AI 工具调用容易重复

你可能会想：

```text
我就点一次按钮，为什么会重复请求？
```

真实系统里重复请求很常见。

常见来源有：

```text
用户重复点击按钮
浏览器刷新页面
前端超时后自动重试
网关超时后重试
后端任务队列重试
模型在多轮对话里再次生成相同工具调用
工具执行成功了，但响应在网络中丢了
服务端返回慢，客户端以为失败又发了一次
```

AI Agent 里还会多一种情况：

```text
模型不一定知道工具刚才到底有没有成功。
```

比如：

```text
1. 模型请求调用 create_ticket。
2. 后端真的创建了工单。
3. 但是网络超时，模型没有拿到结果。
4. 编排层重试。
5. 模型又请求调用 create_ticket。
```

如果没有幂等性，就可能创建两个工单。

## 幂等性不是“防止用户发请求”

幂等性不是说：

```text
不让用户重复请求。
```

真实系统里你很难完全阻止重复请求。

幂等性的思路是：

```text
允许重复请求进来，但后端保证重复请求不会重复产生副作用。
```

也就是：

```text
请求可以重复。
业务效果不能重复。
```

这是后端工程里非常重要的思想。

## 哪些工具需要幂等性

不是所有工具都同等需要幂等保护。

### read 工具

读工具只查询数据，不修改业务状态。

例子：

```text
query_order
search_faq
get_ticket_status
```

读工具一般天然更接近幂等。
你查一次订单和查十次订单，通常不会新增业务记录。

但它仍然可能需要缓存、限流和审计。
只是它的“重复执行风险”比写工具小。

### write 工具

写工具会修改业务系统。

例子：

```text
create_ticket
update_ticket
add_internal_note
send_sms
```

这类工具必须认真考虑幂等性。

尤其是：

```text
创建类操作
发送类操作
扣减类操作
状态变更类操作
```

### sensitive 工具

敏感工具会产生更高风险。

例子：

```text
refund_order
cancel_order
transfer_money
delete_user
modify_permission
```

这类工具不只需要幂等性，还需要：

```text
权限校验
用户确认
业务规则校验
风控
审计日志
人工审核
数据库事务
```

幂等性只是其中一层保护。

## 什么是 `Idempotency-Key`

`Idempotency-Key` 可以理解为：

```text
这一次业务操作的唯一编号。
```

客户端第一次请求时带上它：

```http
Idempotency-Key: query-order-api-key-001
```

后端看到这个 key 后，会记录：

```text
这个 key 已经执行过哪个工具？
当时的参数是什么？
第一次执行的结果是什么？
```

下次如果又收到同一个 key：

```text
如果工具和参数一样：返回第一次结果，不再执行工具。
如果工具或参数不一样：返回冲突错误。
```

这就是本节代码实现的核心。

## 为什么同一个 key 不能配不同参数

假设第一次请求：

```json
{
  "order_id": "A1001"
}
```

请求头：

```http
Idempotency-Key: same-key-001
```

后端记录：

```text
same-key-001 -> query_order(A1001)
```

如果第二次请求又用同一个 key，但参数变成：

```json
{
  "order_id": "A1002"
}
```

这时后端不能猜用户到底想干什么。

因为同一个幂等键应该代表同一次业务操作。
同一次业务操作不应该一会儿查 A1001，一会儿查 A1002。

所以后端应该拒绝：

```text
IDEMPOTENCY_KEY_CONFLICT
HTTP 409
```

这能防止客户端错误复用 key。

## 参数指纹是什么

参数指纹就是：

```text
把工具名和参数变成一个稳定的哈希值。
```

当前代码里用的是：

```python
build_arguments_fingerprint(tool_name, arguments)
```

它会把数据整理成稳定 JSON：

```json
{
  "tool_name": "query_order",
  "arguments": {
    "order_id": "A1001"
  }
}
```

然后用 SHA-256 算出一个字符串。

为什么要这么做？

因为直接比较原始 JSON 容易有问题。

比如这两个 JSON 含义一样：

```json
{"order_id": "A1001", "source": "test"}
```

```json
{"source": "test", "order_id": "A1001"}
```

字段顺序不同，但业务含义相同。

所以我们使用：

```python
sort_keys=True
```

让 JSON 字段顺序稳定。

## 本节新增代码

本节新增：

```text
projects/ai-service/app/tools/idempotency.py
projects/ai-service/tests/test_tool_idempotency.py
```

修改：

```text
projects/ai-service/app/routers/tools.py
projects/ai-service/tests/conftest.py
projects/ai-service/tests/test_tools_api.py
```

核心函数：

```text
validate_idempotency_key(...)
build_arguments_fingerprint(...)
run_idempotent_tool(...)
clear_idempotency_store()
get_idempotency_record_count()
```

## `validate_idempotency_key`

这个函数负责检查幂等键格式。

当前规则：

```text
允许为空。
如果为空，表示不启用幂等保护。
如果不为空，长度必须是 8 到 128。
只能包含字母、数字、点、下划线、冒号、短横线。
```

为什么要限制格式？

因为幂等键会进入后端存储和日志。
不能让它变成任意奇怪字符串。

不要把这些内容直接当幂等键：

```text
手机号
邮箱
身份证
用户完整输入
API key
```

幂等键应该是随机、唯一、无敏感信息的字符串。
实际项目里常用 UUID v4。

## `run_idempotent_tool`

这个函数是本节核心。

简化逻辑如下：

```python
def run_idempotent_tool(tool_name, arguments, idempotency_key, executor):
    key = validate_idempotency_key(idempotency_key)
    if key is None:
        return executor()

    fingerprint = build_arguments_fingerprint(tool_name, arguments)

    if key 已经存在:
        if fingerprint 不一样:
            抛出 IDEMPOTENCY_KEY_CONFLICT
        return 第一次执行结果

    result = executor()
    保存 key、fingerprint、result
    return result
```

你可以把它理解成：

```text
先查有没有旧记录。
有旧记录就复用。
没有旧记录才真的执行工具。
```

## 为什么要传 `executor`

当前调用方式是：

```python
result = run_idempotent_tool(
    "query_order",
    request,
    idempotency_key,
    lambda: run_query_order_tool(request),
)
```

这里的 `executor` 就是真正要执行的工具函数。

这样设计的好处是：

```text
幂等逻辑不用知道具体工具怎么执行。
query_order 可以用它。
create_ticket 以后也可以用它。
refund_order 如果开放，也可以用它。
```

这叫把通用能力抽出来。

不是每个工具里都自己写一遍：

```text
查 key
比参数
执行工具
存结果
返回旧结果
```

## `/tools/query-order` 如何接入

路由现在支持请求头：

```http
Idempotency-Key: query-order-api-key-001
```

接口流程变成：

```text
POST /tools/query-order
-> QueryOrderArgs 参数校验
-> authorize_tool_call("query_order")
-> run_idempotent_tool(...)
-> 真正执行 run_query_order_tool 或返回旧结果
-> QueryOrderResponse
```

也就是：

```text
参数合法
权限允许
幂等检查
执行工具
返回响应
```

这几个步骤顺序很重要。

当前实现是先做权限，再做幂等。
因为后端不应该为了一个不允许执行的工具去创建幂等记录。

## API 示例

第一次请求：

```http
POST /tools/query-order
Idempotency-Key: query-order-api-key-001
Content-Type: application/json
```

```json
{
  "order_id": "A1001"
}
```

后端执行真实工具，并保存结果。

第二次请求：

```http
POST /tools/query-order
Idempotency-Key: query-order-api-key-001
Content-Type: application/json
```

```json
{
  "order_id": "A1001"
}
```

后端不再执行工具，直接返回第一次结果。

如果第二次请求变成：

```json
{
  "order_id": "A1002"
}
```

后端返回：

```json
{
  "code": "IDEMPOTENCY_KEY_CONFLICT",
  "message": "同一个幂等键不能用于不同的工具调用参数。",
  "trace_id": "..."
}
```

状态码：

```text
409
```

## 为什么状态码用 409

409 可以理解成：

```text
请求本身格式没错，但和服务器当前已有状态冲突。
```

这里的冲突是：

```text
服务器已经记录 same-key-001 对应 A1001。
你现在又拿 same-key-001 请求 A1002。
```

所以它不是 422 参数格式错误。
参数格式是合法的，只是和已有幂等记录冲突。

## 当前测试覆盖

新增单元测试：

```text
projects/ai-service/tests/test_tool_idempotency.py
```

覆盖：

- 幂等键合法时能通过。
- 幂等键为空时表示不启用幂等。
- 幂等键格式不合法时返回 `IDEMPOTENCY_KEY_INVALID`。
- 同一组参数生成同一个 fingerprint。
- 不同参数生成不同 fingerprint。
- 没有 key 时每次都会执行工具。
- 同一个 key 和同一组参数只执行一次工具。
- 同一个 key 和不同参数返回 `IDEMPOTENCY_KEY_CONFLICT`。

扩展 API 测试：

```text
projects/ai-service/tests/test_tools_api.py
```

覆盖：

- 同一个 `Idempotency-Key` 重复请求时，工具函数只执行一次。
- 同一个 `Idempotency-Key` 配不同 body 时返回 409。
- 非法 `Idempotency-Key` 返回 422。

运行本节相关测试：

```powershell
uv run pytest tests/test_tool_idempotency.py tests/test_tools_api.py -q
```

运行全量测试：

```powershell
uv run pytest -q
```

## 当前实现的局限

本节是入门实现，目的是讲清楚原理。
它不是生产级完整方案。

当前局限：

```text
记录存在内存里，服务重启就丢失。
多进程部署时，每个进程都有自己的内存，不共享。
多台机器部署时，机器之间不共享。
没有过期时间 TTL。
没有保存失败响应。
没有 in-progress 状态。
没有数据库唯一索引。
没有和真实业务事务绑定。
```

这不是坏事。
学习时先用内存字典看懂流程。
等你理解了，再升级存储。

## 生产环境应该怎么做

真实项目里更常见的是：

```text
PostgreSQL / MySQL 表
Redis
业务数据库唯一索引
消息队列去重表
```

以数据库为例，可以设计一张表：

```text
tool_idempotency_records
```

字段可能包括：

```text
idempotency_key
tool_name
arguments_fingerprint
status
response_status_code
response_body
created_at
expires_at
```

关键点：

```text
idempotency_key 要有唯一索引。
第一次请求插入记录。
重复请求查询记录。
同 key 不同参数拒绝。
执行成功后保存响应。
过期数据定期清理。
```

如果是创建工单，还可以在业务表里加：

```text
idempotency_key
```

并设置唯一索引。

这样即使代码层发生重试，数据库也能兜底防止重复创建。

## 幂等性和缓存有什么区别

它们看起来都像：

```text
第二次请求返回旧结果。
```

但目的不同。

缓存的目标是：

```text
提高性能，减少重复计算。
```

幂等性的目标是：

```text
防止重复副作用，保证业务安全。
```

比如：

```text
搜索 FAQ 重复返回旧结果，可以叫缓存。
创建工单重复返回第一次工单，是幂等。
```

缓存可以为了性能失效。
幂等记录不能随便失效，否则可能重复创建业务数据。

## 幂等性和权限边界的关系

上一节的权限边界回答：

```text
能不能执行这个工具？
```

这一节的幂等性回答：

```text
如果能执行，重复请求会不会重复产生业务效果？
```

它们是两层不同保护：

```text
权限边界：防止不该执行的工具被执行。
幂等性：防止该执行的工具被重复执行。
```

对 `refund_order` 来说：

```text
权限边界决定当前是否允许退款。
幂等性保证同一次退款请求不会退两次。
```

两者都需要。

## 常见错误

### 错误 1：只靠前端防重复点击

前端按钮禁用是有用的，但不够。

因为重复请求可能来自：

```text
网络重试
服务端重试
模型重复工具调用
任务队列重放
```

所以后端必须做幂等。

### 错误 2：只用 `order_id` 当幂等键

`order_id` 不是一次操作的唯一编号。

同一个订单可能发生多个不同动作：

```text
查询订单
创建工单
申请退款
取消订单
```

如果都用 `order_id=A1001` 当 key，会互相冲突。

更好的做法是：

```text
每一次业务操作生成一个独立 Idempotency-Key。
```

### 错误 3：同一个 key 允许换参数

这会让后端无法判断到底哪次请求才是正确的。

正确做法：

```text
同 key 同参数：返回旧结果。
同 key 不同参数：返回冲突。
```

### 错误 4：只在 AI prompt 里提醒不要重复调用

prompt 可以提醒模型，但不能保证。

真正的幂等性必须在后端代码和存储层实现。

### 错误 5：没有保存第一次结果

如果第一次请求成功了，但响应丢了，第二次请求应该返回第一次结果。

如果后端只记录“执行过”，却不保存结果，客户端就拿不到稳定响应。

## 练习 1：判断是否需要幂等性

请判断下面工具是否需要重点做幂等保护：

```text
A. 很需要
B. 可以有，但不是最高优先级
```

题目：

1. `query_order`
2. `create_ticket`
3. `refund_order`
4. `search_faq`
5. `send_sms`
6. `cancel_order`
7. `get_ticket_status`

### 练习 1 参考答案

1. `query_order`：B。读操作，重复查询通常不改变业务状态。
2. `create_ticket`：A。重复执行会创建多个工单。
3. `refund_order`：A。重复执行可能造成重复退款，必须强保护。
4. `search_faq`：B。读知识库，主要考虑缓存和限流。
5. `send_sms`：A。重复执行会给用户发多条短信。
6. `cancel_order`：A。取消订单是业务状态变更，需要幂等。
7. `get_ticket_status`：B。读工单状态，重复查询风险较低。

## 练习 2：判断接口行为

假设第一次请求：

```text
Idempotency-Key: key-001
body: {"order_id":"A1001"}
```

请判断下面第二次请求会发生什么：

1. `key-001` + `{"order_id":"A1001"}`
2. `key-001` + `{"order_id":"A1002"}`
3. 没有 key + `{"order_id":"A1001"}`
4. `abc` + `{"order_id":"A1001"}`

### 练习 2 参考答案

1. 返回第一次结果，不再执行工具。
2. 返回 `IDEMPOTENCY_KEY_CONFLICT`，HTTP 409。
3. 不启用幂等保护，正常执行工具。
4. 返回 `IDEMPOTENCY_KEY_INVALID`，HTTP 422，因为 key 太短。

## 练习 3：解释参数指纹

问题：

```text
为什么要用参数指纹，而不是只记录 idempotency_key？
```

### 练习 3 参考答案

因为同一个 `idempotency_key` 只能代表同一次业务操作。
如果只记录 key，不记录参数，后端就无法发现客户端把同一个 key 错误地用于不同请求。

参数指纹可以判断：

```text
这次请求和第一次请求是不是同一个工具、同一组参数。
```

如果不是，就应该返回冲突，避免错误复用 key。

## 练习 4：设计 `create_ticket` 的幂等请求

假设以后有接口：

```text
POST /tools/create-ticket
```

请求体：

```json
{
  "order_id": "A1001",
  "title": "订单未发货",
  "description": "用户询问什么时候发货"
}
```

请设计一个合理的幂等策略。

### 练习 4 参考答案

可以这样设计：

```text
1. 前端或编排层为这一次创建工单生成 Idempotency-Key。
2. 后端校验用户是否确认创建工单。
3. 后端校验工具权限。
4. 后端计算 create_ticket + 请求体的参数指纹。
5. 如果 key 第一次出现，创建工单并保存工单结果。
6. 如果 key 重复出现且参数相同，返回第一次创建的工单。
7. 如果 key 重复出现但参数不同，返回 IDEMPOTENCY_KEY_CONFLICT。
8. 数据库里的工单表或幂等表给 idempotency_key 加唯一索引。
```

## 练习 5：为什么不能只靠模型记住

问题：

```text
如果 system prompt 里写了“不要重复创建工单”，为什么后端仍然要做幂等？
```

### 练习 5 参考答案

因为模型输出不是强一致的业务状态。
模型可能不知道第一次工具调用是否成功，也可能在重试、多轮对话、网络异常后再次生成同一个工具调用。

后端幂等性是程序级保护。
它不依赖模型是否记得，也不依赖用户是否只点一次。

## 自测题

### 1. 什么是幂等性？

参考答案：

```text
同一个操作执行一次和执行多次，最终产生的业务效果相同，就叫幂等性。
```

### 2. 为什么创建工单默认不是幂等的？

参考答案：

```text
因为每执行一次创建逻辑，都可能新增一条工单记录。重复执行会创建多个工单。
```

### 3. `Idempotency-Key` 的作用是什么？

参考答案：

```text
它用来标识一次唯一的业务操作。后端用它识别重复请求，并返回第一次执行结果，避免重复执行工具。
```

### 4. 同一个 key 携带不同参数时为什么要返回 409？

参考答案：

```text
因为同一个 key 已经被绑定到第一次请求的工具和参数。再次使用同一个 key 但参数不同，说明请求和服务器已有幂等记录冲突，所以返回 409。
```

### 5. 当前项目里没有 `Idempotency-Key` 会怎样？

参考答案：

```text
不会启用幂等保护，工具会按普通请求正常执行。
```

### 6. 当前内存版幂等实现为什么不能直接当生产方案？

参考答案：

```text
因为内存数据会在服务重启后丢失，多进程和多机器之间不共享，也没有 TTL、数据库唯一索引、in-progress 状态和事务保护。
```

### 7. 幂等性和缓存有什么区别？

参考答案：

```text
缓存主要为了性能，减少重复计算。幂等性主要为了业务安全，防止重复创建、重复退款、重复发送等副作用。
```

### 8. 权限边界和幂等性的区别是什么？

参考答案：

```text
权限边界判断工具能不能执行。幂等性保证允许执行的工具在重复请求时不会重复产生业务效果。
```

## 本节小结

这一节的核心是：

```text
AI 工具调用一定要考虑重复执行问题。
```

当前项目已经有了：

```text
Idempotency-Key 请求头
参数指纹
内存幂等记录
重复请求复用结果
同 key 不同参数冲突检测
API 和单元测试覆盖
```

你现在要记住这个完整链路：

```text
客户端生成 Idempotency-Key
-> 后端校验 key
-> 后端计算工具名和参数指纹
-> 第一次请求执行工具并保存结果
-> 重复请求返回旧结果
-> 同 key 不同参数返回 409
```

下一节继续学习：

```text
用 FastAPI 写一个最小 Java mock 业务服务。
```

也就是开始模拟真实的：

```text
Python AI 服务 -> Java 业务服务
```

这会让工具调用从 fake 内存数据逐步走向跨服务调用。

## 资料来源

- [RFC 9110：HTTP Semantics，9.2.2 Idempotent Methods](https://datatracker.ietf.org/doc/html/rfc9110#section-9.2.2)
- [Stripe：Idempotent requests](https://docs.stripe.com/api/idempotent_requests)
- [OpenAI：Function calling](https://developers.openai.com/api/docs/guides/function-calling)
