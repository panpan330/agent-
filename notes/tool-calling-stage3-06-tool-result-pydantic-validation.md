# 阶段 3 第 6 节：工具调用结果也要 Pydantic 校验

## 本节目标

前几节我们一直在强调：

```text
模型输出不能直接信。
工具参数要校验。
```

这一节再补一个同样重要的点：

```text
工具返回结果也不能直接信。
```

原因很简单：

后面 `query_order` 不会一直查本地假数据，它会变成：

```text
Python AI 服务
-> query_order 工具函数
-> Java 订单服务
-> 数据库或第三方系统
```

Java 服务返回的数据，对 Python AI 服务来说也是外部输入。

所以它也必须校验。

学完本节，你要能说清楚：

- 为什么工具结果也不可信。
- 什么是工具参数校验。
- 什么是工具结果校验。
- `QueryOrderArgs` 和 `QueryOrderResult` 分别负责什么。
- `QueryOrderResult.model_validate(...)` 是什么。
- 为什么要用 `ConfigDict(extra="forbid")`。
- 为什么工具结果坏了应该返回 502，而不是 422。
- 为什么不要把原始坏数据直接塞进错误详情里。
- 以后接 Java API 时，这套校验怎么复用。

## 先回顾第 5 节

第 5 节我们做了一个 fake tool：

```text
query_order(order_id)
```

它提供一个学习用接口：

```text
POST /tools/query-order
```

成功请求：

```json
{
  "order_id": "A1001"
}
```

成功响应：

```json
{
  "result": {
    "order_id": "A1001",
    "order_status": "waiting_shipment",
    "payment_status": "paid",
    "logistics_message": "商家已接单，等待仓库发货。",
    "latest_event": "仓库正在准备出库。",
    "can_create_ticket": true,
    "source": "fake_order_tool"
  }
}
```

第 5 节重点是：

```text
先有一个后端可执行的工具。
```

第 6 节重点是：

```text
工具执行完以后，返回结果也要变成可信对象。
```

## 什么叫“工具结果”

工具结果就是工具函数执行后返回的数据。

比如：

```text
query_order(QueryOrderArgs(order_id="A1001"))
```

返回：

```text
QueryOrderResult(...)
```

从业务角度看，它是：

```text
订单查询结果。
```

从 Agent 流程看，它是：

```text
模型请求调用工具后，后端拿到的工具执行结果。
```

以后这个结果可能会继续交给模型总结：

```text
工具结果 -> 模型总结 -> 回复用户
```

所以工具结果如果不稳定，后面的模型总结、业务判断和前端展示都会受影响。

## 为什么工具结果也不可信

很多初学者会有一个误区：

```text
模型输出不可信，这我知道。
但工具是我自己写的，所以工具结果应该可信吧？
```

要分情况。

如果工具内部只使用固定本地数据，风险小一些。

但真实项目里的工具往往会调用外部系统：

```text
Java 后端 API
数据库
Redis
第三方物流接口
支付系统
权限系统
搜索服务
向量数据库
```

这些系统返回的数据，都可能出现问题：

- 字段缺失。
- 字段类型变了。
- 字段名改了。
- 状态值超出枚举。
- 多返回了内部字段。
- 返回了错误格式。
- 返回了空对象。
- 返回了 HTML 错误页。
- 返回了第三方系统的异常结构。

所以从 Python AI 服务的角度看：

```text
凡是从当前模块边界外进来的数据，都先当成不可信输入。
```

这包括：

```text
用户请求
模型输出
工具参数
工具返回结果
Java API 返回
第三方接口返回
```

## 输入模型和输出模型

这一节要分清两个模型：

```text
QueryOrderArgs
QueryOrderResult
```

### `QueryOrderArgs`

它是工具输入模型。

负责校验：

```text
调用 query_order 时，参数是否合规。
```

比如：

```json
{
  "order_id": "A1001"
}
```

它回答的问题是：

```text
这个工具能不能拿这些参数去执行？
```

### `QueryOrderResult`

它是工具输出模型。

负责校验：

```text
query_order 查回来的结果是否合规。
```

比如：

```json
{
  "order_id": "A1001",
  "order_status": "waiting_shipment",
  "payment_status": "paid",
  "logistics_message": "商家已接单，等待仓库发货。",
  "latest_event": "仓库正在准备出库。",
  "can_create_ticket": true
}
```

它回答的问题是：

```text
这个工具返回的数据，能不能被后续业务逻辑安全使用？
```

## 参数校验和结果校验的区别

| 对比点 | 工具参数校验 | 工具结果校验 |
| --- | --- | --- |
| 校验对象 | 模型或接口传来的 arguments | 工具执行后拿到的数据 |
| 当前模型 | `QueryOrderArgs` | `QueryOrderResult` |
| 数据方向 | 进入工具前 | 离开工具后 |
| 常见错误 | 缺少 `order_id`、类型错误、格式错误 | 缺字段、状态值未知、类型错误、多余内部字段 |
| 错误性质 | 请求方给错参数 | 上游工具或业务系统返回异常 |
| 常见 HTTP 状态 | 422 或业务拒绝 | 502 更合适 |

简单记：

```text
进工具前，校验参数。
出工具后，校验结果。
```

## 本节代码改了什么

第 5 节里，fake 数据一开始就是 `QueryOrderResult` 对象。

这虽然安全，但不够贴近真实 Java API。

真实 Java API 返回的通常是 JSON，也就是 Python 里会先变成普通 `dict`。

所以本节把 fake 数据改成原始 `dict`：

```python
_FAKE_ORDER_STORE: dict[str, dict[str, object]] = {
    "A1001": {
        "order_id": "A1001",
        "order_status": "waiting_shipment",
        "payment_status": "paid",
        "logistics_message": "商家已接单，等待仓库发货。",
        "latest_event": "仓库正在准备出库。",
        "can_create_ticket": True,
    }
}
```

然后新增一个函数：

```python
def validate_query_order_result(raw_result: Mapping[str, Any]) -> QueryOrderResult:
    try:
        return QueryOrderResult.model_validate(raw_result)
    except ValidationError as exc:
        raise AppException(
            code="TOOL_RESULT_VALIDATION_FAILED",
            message="工具返回结果校验失败，请稍后重试。",
            status_code=502,
            details=exc.errors(include_url=False, include_input=False),
        ) from exc
```

现在 `query_order` 的流程是：

```text
拿到原始 dict
-> validate_query_order_result(...)
-> QueryOrderResult
```

## `model_validate` 是什么

`model_validate` 是 Pydantic v2 常用的模型校验入口。

它可以把外部数据校验成 Pydantic 对象。

比如：

```python
result = QueryOrderResult.model_validate(raw_result)
```

意思是：

```text
请按照 QueryOrderResult 的规则校验 raw_result。
如果成功，返回 QueryOrderResult 对象。
如果失败，抛出 ValidationError。
```

校验成功后，后续代码拿到的不是随便一个 `dict`，而是：

```text
字段明确
类型明确
枚举明确
结构明确
```

的对象。

## 什么情况会校验失败

### 1. 状态值不在枚举里

错误数据：

```json
{
  "order_id": "A1001",
  "order_status": "unknown_status",
  "payment_status": "paid",
  "logistics_message": "商家已接单，等待仓库发货。",
  "latest_event": "仓库正在准备出库。",
  "can_create_ticket": true
}
```

失败原因：

```text
order_status 只能是 waiting_shipment、shipped、delivered、canceled。
unknown_status 不在允许范围内。
```

### 2. 缺少必填字段

错误数据：

```json
{
  "order_id": "A1001",
  "order_status": "waiting_shipment",
  "payment_status": "paid",
  "latest_event": "仓库正在准备出库。",
  "can_create_ticket": true
}
```

失败原因：

```text
缺少 logistics_message。
```

### 3. 多了不该暴露的字段

错误数据：

```json
{
  "order_id": "A1001",
  "order_status": "waiting_shipment",
  "payment_status": "paid",
  "logistics_message": "商家已接单，等待仓库发货。",
  "latest_event": "仓库正在准备出库。",
  "can_create_ticket": true,
  "internal_note": "仓库内部备注"
}
```

失败原因：

```text
internal_note 不在 QueryOrderResult 定义里。
```

这就是 `extra="forbid"` 的作用。

## 为什么要禁止多余字段

本节给 `QueryOrderArgs` 和 `QueryOrderResult` 都加了：

```python
model_config = ConfigDict(extra="forbid")
```

这表示：

```text
如果传进来的数据包含模型没有定义的字段，直接报错。
```

比如参数里多了：

```json
{
  "order_id": "A1001",
  "admin": true
}
```

会被拒绝。

工具结果里多了：

```json
{
  "internal_note": "不要给用户看"
}
```

也会被拒绝。

为什么这么严格？

因为 AI 服务很容易把工具结果继续交给模型总结。

如果上游多返回了内部字段，而我们没有拦住，模型可能把内部信息说给用户听。

所以工具结果模型要清楚声明：

```text
我只接受这些字段。
其他字段一律拒绝。
```

## 为什么工具结果错误用 502

这一节新增错误码：

```text
TOOL_RESULT_VALIDATION_FAILED
```

对应状态码：

```text
502
```

你可能会问：

```text
为什么不是 422？
```

因为 422 通常表示：

```text
客户端请求参数不对。
```

比如用户请求：

```json
{
  "order_id": "A 1001"
}
```

这是请求体格式错误，所以是 422。

但工具结果坏了，通常不是用户请求直接造成的。

比如 Java 订单服务返回：

```json
{
  "order_status": "UNKNOWN"
}
```

这是上游服务返回了 Python AI 服务无法接受的数据。

对当前服务来说，更像是：

```text
上游依赖返回异常。
```

所以用 502 更合理。

简单记：

```text
请求进来错了：422。
上游工具结果错了：502。
业务资源不存在：404。
```

## 为什么错误详情不带原始 input

代码里用了：

```python
exc.errors(include_url=False, include_input=False)
```

意思是：

```text
返回错误类型、位置、说明，但不要把原始输入值带进 details。
```

为什么？

因为工具结果可能来自业务系统。

里面可能有：

```text
手机号
地址
内部备注
支付信息
物流单号
用户隐私
系统内部字段
```

如果直接把原始 input 放进错误响应，可能会泄漏敏感信息。

所以当前策略是：

```text
告诉调用方哪里错了，但不回显原始坏数据。
```

## 当前 `query_order` 的完整流程

现在 `query_order` 函数是：

```text
QueryOrderArgs
-> 查 _FAKE_ORDER_STORE
-> 得到 raw_result
-> validate_query_order_result(raw_result)
-> QueryOrderResult
```

完整链路：

```text
POST /tools/query-order
        |
        v
QueryOrderArgs 校验请求参数
        |
        v
query_order(arguments)
        |
        v
_FAKE_ORDER_STORE 返回原始 dict
        |
        v
validate_query_order_result
        |
        v
QueryOrderResult
        |
        v
QueryOrderResponse
```

这就是：

```text
输入要校验。
输出也要校验。
```

## `response_model` 不能替代工具结果校验

FastAPI 的接口可以写：

```python
@router.post("/query-order", response_model=QueryOrderResponse)
```

这会约束 HTTP 响应结构。

但不要把它当成工具结果校验的唯一防线。

原因是：

```text
工具结果可能不只用于 HTTP 响应。
```

它还可能用于：

```text
业务规则判断
是否创建工单
是否需要人工审核
是否让模型总结
日志记录
后续工具调用
```

所以更好的习惯是：

```text
工具函数返回前，就先保证结果是 QueryOrderResult。
```

不要等到接口返回时才发现数据坏了。

## 以后接 Java API 怎么用

现在 fake tool 是：

```python
raw_result = _FAKE_ORDER_STORE.get(arguments.order_id)
return validate_query_order_result(raw_result)
```

以后接 Java API 可能会变成：

```python
response = httpx.get(f"{JAVA_BASE_URL}/orders/{arguments.order_id}")
raw_result = response.json()
return validate_query_order_result(raw_result)
```

你看，关键校验函数不用变：

```text
validate_query_order_result
```

这就是提前建好边界的价值。

fake 数据也好，Java API 也好，只要进来的是原始数据，都走同一个校验入口。

## 本节新增和修改的代码

核心文件：

```text
projects/ai-service/app/schemas/tool.py
projects/ai-service/app/tools/fake_order_tool.py
projects/ai-service/tests/test_tool_schema.py
projects/ai-service/tests/test_fake_order_tool.py
projects/ai-service/tests/test_tools_api.py
```

主要变化：

- `QueryOrderArgs` 增加 `extra="forbid"`。
- `QueryOrderResult` 增加 `extra="forbid"`。
- 新增 `get_query_order_result_json_schema()`。
- fake 订单数据从 `QueryOrderResult` 对象改成原始 `dict`。
- 新增 `validate_query_order_result(...)`。
- `query_order(...)` 返回前显式校验工具结果。
- 新增工具结果校验失败测试。
- 新增接口拒绝多余请求字段测试。

## 本节测试

只跑本节相关测试：

```powershell
uv run pytest tests/test_tool_schema.py tests/test_fake_order_tool.py tests/test_tools_api.py -q
```

全量测试：

```powershell
uv run pytest -q
```

本节新增测试覆盖：

- `QueryOrderArgs` 拒绝多余字段。
- `QueryOrderResult` 拒绝未知订单状态。
- `QueryOrderResult` 拒绝多余字段。
- `get_query_order_result_json_schema()` 包含结果字段。
- `validate_query_order_result(...)` 可以把原始 dict 转成 Pydantic 对象。
- 工具结果状态异常时返回 `TOOL_RESULT_VALIDATION_FAILED`。
- 工具结果缺字段时返回 `TOOL_RESULT_VALIDATION_FAILED`。
- 错误详情不回显原始 input。

## 练习 1：判断错误类型

请判断下面错误应该属于哪类：

```text
A. 请求参数错误，返回 422
B. 业务资源不存在，返回 404
C. 工具结果校验失败，返回 502
```

题目：

1. 用户请求体是 `{}`，没有 `order_id`。
2. 用户请求体是 `{"order_id": "A 1001"}`。
3. 用户请求体是 `{"order_id": "A9999"}`，但 fake 数据没有这个订单。
4. Java API 返回 `{"order_status": "UNKNOWN"}`。
5. Java API 返回结果缺少 `logistics_message`。

### 练习 1 参考答案

1. A。缺少请求参数，属于客户端请求体校验错误，返回 422。
2. A。`order_id` 格式不合法，返回 422。
3. B。参数格式合法，但业务资源不存在，返回 404。
4. C。上游工具结果状态值不符合 `QueryOrderResult`，返回 502。
5. C。上游工具结果缺少必填字段，返回 502。

## 练习 2：解释输入模型和输出模型

问题：

```text
QueryOrderArgs 和 QueryOrderResult 有什么区别？
```

### 练习 2 参考答案

`QueryOrderArgs` 是工具输入模型，负责校验调用工具前传入的参数，例如 `order_id` 是否存在、格式是否合法。

`QueryOrderResult` 是工具输出模型，负责校验工具执行后返回的数据，例如订单状态、支付状态、物流说明是否符合我们系统约定。

一句话：

```text
QueryOrderArgs 管进工具前的数据。
QueryOrderResult 管出工具后的数据。
```

## 练习 3：为什么要禁止多余字段

问题：

```text
为什么 QueryOrderResult 要设置 extra="forbid"？
```

### 练习 3 参考答案

因为工具结果后续可能会交给模型总结，或者用于业务判断。

如果上游返回了未定义字段，例如 `internal_note`、`user_phone`、`debug_info`，而我们没有拦截，就可能发生：

```text
敏感信息泄漏
模型引用内部字段
业务逻辑误用未知字段
接口响应结构不稳定
```

所以结果模型应该明确声明允许哪些字段，其他字段直接拒绝。

## 练习 4：写一个坏结果测试

请写一个测试：当工具结果多了 `internal_note` 字段时，`validate_query_order_result` 应该抛出 `TOOL_RESULT_VALIDATION_FAILED`。

### 练习 4 参考答案

示例：

```python
def test_validate_query_order_result_raises_when_result_has_extra_field() -> None:
    with pytest.raises(AppException) as exc_info:
        validate_query_order_result(
            {
                "order_id": "A1001",
                "order_status": "waiting_shipment",
                "payment_status": "paid",
                "logistics_message": "商家已接单，等待仓库发货。",
                "latest_event": "仓库正在准备出库。",
                "can_create_ticket": True,
                "internal_note": "不要暴露给用户",
            }
        )

    exc = exc_info.value
    assert exc.code == "TOOL_RESULT_VALIDATION_FAILED"
    assert exc.details[0]["loc"] == ("internal_note",)
    assert exc.details[0]["type"] == "extra_forbidden"
```

## 练习 5：以后接 Java API 时放在哪里校验

问题：

```text
以后 query_order 内部改成调用 Java API，应该在什么时候调用 validate_query_order_result？
```

### 练习 5 参考答案

应该在拿到 Java API 原始响应以后立刻校验。

流程：

```text
调用 Java API
-> response.json() 得到 raw_result
-> validate_query_order_result(raw_result)
-> 成功后返回 QueryOrderResult
```

不要把 Java 原始 dict 直接传给模型、前端或业务逻辑。

## 自测题

### 1. 为什么工具结果也要校验？

参考答案：

```text
因为工具结果可能来自 Java API、数据库或第三方系统，对当前 Python AI 服务来说也是外部输入。字段、类型、状态值和多余字段都可能不符合预期。
```

### 2. `model_validate` 的作用是什么？

参考答案：

```text
它按照 Pydantic 模型规则校验外部数据。成功时返回模型对象，失败时抛出 ValidationError。
```

### 3. `extra="forbid"` 的作用是什么？

参考答案：

```text
禁止未定义字段。如果传入数据里有模型没有声明的字段，Pydantic 会抛出 extra_forbidden 错误。
```

### 4. 工具结果坏了为什么更适合返回 502？

参考答案：

```text
因为这通常表示上游工具或业务系统返回了当前服务无法接受的数据，不是客户端请求体本身格式错误。422 更适合表示客户端请求参数错误。
```

### 5. 为什么错误详情里不要带原始 input？

参考答案：

```text
因为工具结果可能包含手机号、地址、内部备注等敏感信息。错误详情应该说明哪里错了，但不要回显原始业务数据。
```

### 6. `response_model` 能不能替代工具函数内部的结果校验？

参考答案：

```text
不能完全替代。response_model 主要约束 HTTP 响应，但工具结果还可能用于业务规则、模型总结、日志和后续工具调用。所以工具函数返回前就应该校验成稳定的结果模型。
```

## 本节小结

这节的核心是三句话：

```text
工具参数要校验。
工具结果也要校验。
外部数据进入核心逻辑前，必须先变成 Pydantic 对象。
```

当前 `query_order` 的边界更清楚了：

```text
QueryOrderArgs -> query_order -> raw tool result -> QueryOrderResult
```

这会直接服务后面的 Java 集成：

```text
fake dict 可以换成 Java API 响应。
validate_query_order_result 不需要换。
```

下一节会继续讲：

```text
工具调用错误处理：超时、404、500。
```

也就是当工具本身调用失败、上游服务报错或网络超时时，AI 服务应该怎么统一处理。

## 资料来源

- [Pydantic：Models](https://pydantic.dev/docs/validation/dev/concepts/models/)
- [Pydantic：Configuration](https://pydantic.dev/docs/validation/dev/api/pydantic/config/)
- [FastAPI：Request Body](https://fastapi.tiangolo.com/tutorial/body/)
