# 阶段 3 第 5 节：用 fake tool 模拟查订单

## 本节目标

前面几节我们已经学了：

```text
Tool Calling = 模型提出工具调用意图，后端决定是否执行。
工具参数 = 模型传给工具的 arguments。
JSON Schema = 用来描述参数结构。
Pydantic = 后端用来校验外部输入。
```

这一节开始进入代码。

但我们还不直接接 Java 服务，也不直接引入 LangChain。

我们先做一个最小的 fake tool：

```text
query_order(order_id)
```

它模拟“查询订单”的业务能力。

本节完成后，你要能解释：

- 什么是 fake tool。
- 为什么先写 fake tool，而不是一上来接 Java 服务。
- 工具函数本质上就是普通后端函数。
- 工具输入参数为什么要先校验。
- `QueryOrderArgs` 是什么。
- `QueryOrderResult` 是什么。
- fake 订单数据为什么先放在内存字典里。
- `/tools/query-order` 接口只是学习用入口，不等于模型已经会自动调用工具。
- 当前离真正 Tool Calling 还差哪几步。

## 这一节新增了哪些文件

本节新增和修改的核心文件：

```text
projects/ai-service/app/schemas/tool.py
projects/ai-service/app/tools/__init__.py
projects/ai-service/app/tools/fake_order_tool.py
projects/ai-service/app/routers/tools.py
projects/ai-service/app/main.py
projects/ai-service/tests/test_tool_schema.py
projects/ai-service/tests/test_fake_order_tool.py
projects/ai-service/tests/test_tools_api.py
```

对应功能：

| 文件 | 作用 |
| --- | --- |
| `app/schemas/tool.py` | 定义工具参数和工具返回结果的 Pydantic 模型 |
| `app/tools/fake_order_tool.py` | 定义假的订单查询工具函数 |
| `app/routers/tools.py` | 提供学习用接口 `/tools/query-order` |
| `app/main.py` | 把 tools router 注册到 FastAPI 应用 |
| `tests/test_tool_schema.py` | 测试工具参数和结果模型 |
| `tests/test_fake_order_tool.py` | 测试 fake tool 函数 |
| `tests/test_tools_api.py` | 测试 `/tools/query-order` 接口 |

## 什么是 fake tool

fake tool 可以先理解成：

```text
假的工具函数。
```

更准确一点：

```text
fake tool 是一个本地模拟实现，用来代替还没接入的真实外部系统。
```

在真实项目里，查订单可能要调用：

```text
Java Spring Boot 订单服务
数据库
物流接口
支付系统
权限系统
```

但我们现在还在学 Tool Calling 基础。

如果一上来就接 Java 服务，你会同时面对很多问题：

```text
Python 怎么调 Java API？
Java 服务怎么启动？
接口路径怎么设计？
鉴权怎么做？
超时怎么处理？
404 怎么处理？
500 怎么处理？
网络失败怎么办？
测试怎么写？
```

这些都重要，但现在一起上会干扰你理解 Tool Calling 的主线。

所以先写 fake tool：

```text
不用网络。
不用数据库。
不用 Java 服务。
只用一个 Python 函数和一份假数据。
```

先把工具调用的基本形状学明白。

## fake tool 和真实工具的关系

fake tool 不是玩具代码。

它是一个“替身”。

今天它内部从字典里查：

```text
_FAKE_ORDER_STORE["A1001"]
```

以后可以换成：

```text
调用 Java 订单服务 GET /orders/A1001
```

只要输入输出模型尽量稳定，上层流程就不需要大改。

今天：

```text
query_order(QueryOrderArgs(order_id="A1001"))
-> 从内存字典里拿订单
-> 返回 QueryOrderResult
```

以后：

```text
query_order(QueryOrderArgs(order_id="A1001"))
-> 调用 Java API
-> 把 Java 返回结果转换成 QueryOrderResult
-> 返回 QueryOrderResult
```

对上层来说，它仍然叫：

```text
query_order
```

参数仍然是：

```text
order_id
```

返回仍然是：

```text
QueryOrderResult
```

这就是先定义边界的好处。

## 工具函数本质上是什么

不要把 Tool Calling 想得太玄。

站在后端代码角度，一个工具函数本质上就是：

```text
一个有明确输入、明确输出、明确错误的函数。
```

比如：

```python
def query_order(arguments: QueryOrderArgs) -> QueryOrderResult:
    ...
```

这和普通业务代码没有本质区别。

区别只在于：

```text
未来这个函数可能会被模型“建议调用”。
```

但函数仍然由后端执行。

模型不会跳进 Python 进程里自己执行代码。

真实流程应该是：

```text
模型返回：我想调用 query_order，参数是 {"order_id": "A1001"}
后端校验参数
后端执行 query_order
后端拿到结果
后端再决定怎么返回
```

## 当前实现的调用链路

这一节为了方便你手动测试，新增了一个接口：

```text
POST /tools/query-order
```

当前调用链路是：

```text
HTTP 请求
-> FastAPI 读取 JSON
-> QueryOrderArgs 校验 order_id
-> app/routers/tools.py
-> app/tools/fake_order_tool.py
-> query_order(...)
-> 从 _FAKE_ORDER_STORE 查询
-> QueryOrderResponse 返回结果
```

用图表示：

```text
POST /tools/query-order
        |
        v
QueryOrderArgs(order_id="A1001")
        |
        v
query_order(arguments)
        |
        v
_FAKE_ORDER_STORE
        |
        v
QueryOrderResult
        |
        v
QueryOrderResponse
```

注意：这一节还没有让模型自动决定调用工具。

现在是我们手动调接口来验证工具函数。

## 第一步：定义工具参数 `QueryOrderArgs`

文件：

```text
projects/ai-service/app/schemas/tool.py
```

核心模型：

```python
class QueryOrderArgs(BaseModel):
    order_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
        description="Order id to query, for example A1001.",
    )
```

这表示：

```text
query_order 工具必须接收一个 order_id。
order_id 必须是字符串。
order_id 最短 1 个字符。
order_id 最长 64 个字符。
order_id 只能包含字母、数字、下划线和短横线。
```

为什么要这样做？

因为模型未来传过来的 arguments 不能直接信。

比如模型可能返回：

```json
{
  "order_id": ""
}
```

也可能返回：

```json
{
  "order_id": "A 1001"
}
```

还可能返回：

```json
{
  "order_id": null
}
```

后端必须先挡住这些不合法参数。

## 为什么要 strip

代码里还有一个校验器：

```python
@field_validator("order_id", mode="before")
@classmethod
def strip_order_id(cls, value: object) -> object:
    if isinstance(value, str):
        return value.strip()
    return value
```

它的作用是去掉首尾空格。

比如：

```text
"  A1001  "
```

会变成：

```text
"A1001"
```

但中间有空格的：

```text
"A 1001"
```

仍然会被拒绝。

这是一个常见后端处理方式：

```text
对用户容易误输的首尾空格做兼容。
对结构上明显不合法的内容直接拒绝。
```

## 第二步：定义工具返回结果 `QueryOrderResult`

文件仍然是：

```text
projects/ai-service/app/schemas/tool.py
```

核心模型：

```python
class QueryOrderResult(BaseModel):
    order_id: str
    order_status: OrderStatus
    payment_status: PaymentStatus
    logistics_message: str
    latest_event: str
    can_create_ticket: bool
    source: str = "fake_order_tool"
```

这表示查订单工具返回：

| 字段 | 含义 |
| --- | --- |
| `order_id` | 订单号 |
| `order_status` | 当前订单状态 |
| `payment_status` | 当前支付状态 |
| `logistics_message` | 给用户看的物流或订单说明 |
| `latest_event` | 最近一次模拟业务事件 |
| `can_create_ticket` | 是否适合创建客服工单 |
| `source` | 数据来自哪里 |

这里有两个枚举：

```python
class OrderStatus(StrEnum):
    WAITING_SHIPMENT = "waiting_shipment"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELED = "canceled"
```

```python
class PaymentStatus(StrEnum):
    UNPAID = "unpaid"
    PAID = "paid"
    REFUNDED = "refunded"
```

枚举的作用是：

```text
限制状态只能从固定值里选。
```

比如 `order_status` 不能随便写成：

```text
"maybe_shipping"
"不知道"
"快了"
```

它必须是我们认可的固定值。

这对后续业务判断非常重要。

## 第三步：定义 fake 数据

文件：

```text
projects/ai-service/app/tools/fake_order_tool.py
```

里面有一个内存字典：

```python
_FAKE_ORDER_STORE: dict[str, QueryOrderResult] = {
    "A1001": QueryOrderResult(...),
    "A1002": QueryOrderResult(...),
    "A1003": QueryOrderResult(...),
}
```

你可以把它想成一个很小的假数据库。

现在它有 3 条假订单：

| 订单号 | 状态 | 说明 |
| --- | --- | --- |
| `A1001` | `waiting_shipment` | 商家已接单，等待仓库发货 |
| `A1002` | `shipped` | 包裹已发出，正在运输途中 |
| `A1003` | `delivered` | 订单已签收 |

真实项目里，这个字典以后会被替换成：

```text
Java 订单服务
```

但现在我们只关心工具调用的输入、输出和错误边界。

## 第四步：实现 `query_order`

文件：

```text
projects/ai-service/app/tools/fake_order_tool.py
```

核心函数：

```python
def query_order(arguments: QueryOrderArgs) -> QueryOrderResult:
    result = _FAKE_ORDER_STORE.get(arguments.order_id)
    if result is None:
        raise AppException(
            code="ORDER_NOT_FOUND",
            message="订单不存在，请确认订单号是否正确。",
            status_code=404,
        )

    return result.model_copy(deep=True)
```

这个函数做了三件事：

```text
1. 从 arguments 里拿到 order_id。
2. 去 fake 数据里查订单。
3. 查到就返回结果，查不到就抛出统一业务异常。
```

如果查：

```text
A1001
```

会返回订单结果。

如果查：

```text
A9999
```

会抛出：

```text
ORDER_NOT_FOUND
```

HTTP 状态码是：

```text
404
```

## 为什么返回 `model_copy(deep=True)`

代码里没有直接返回原始对象，而是：

```python
return result.model_copy(deep=True)
```

这是什么意思？

```text
返回一份拷贝。
```

为什么要拷贝？

因为 `_FAKE_ORDER_STORE` 是共享假数据。

如果直接把里面的对象返回出去，别的代码不小心修改它，就可能污染假数据源。

返回拷贝可以减少这种副作用。

这是一个小细节，但是真实项目里很重要：

```text
共享数据源不要随便暴露可变对象。
```

## 第五步：提供学习用接口

文件：

```text
projects/ai-service/app/routers/tools.py
```

核心代码：

```python
@router.post("/query-order", response_model=QueryOrderResponse)
def query_order(request: QueryOrderArgs) -> QueryOrderResponse:
    logger.info("fake_query_order_requested order_id=%s", request.order_id)
    result = run_query_order_tool(request)
    return QueryOrderResponse(result=result)
```

接口完整路径是：

```text
POST /tools/query-order
```

请求体：

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

查不到订单时：

```json
{
  "code": "ORDER_NOT_FOUND",
  "message": "订单不存在，请确认订单号是否正确。",
  "trace_id": "..."
}
```

参数不合法时：

```json
{
  "code": "VALIDATION_ERROR",
  "message": "请求参数校验失败",
  "trace_id": "...",
  "details": []
}
```

## 为什么要提供 `/tools/query-order`

这个接口主要是为了学习和验证。

你可以直接在 FastAPI docs 里测试：

```text
http://127.0.0.1:8000/docs
```

也可以用 PowerShell 测试：

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/tools/query-order" `
  -ContentType "application/json" `
  -Body '{"order_id":"A1001"}'
```

但要记住：

```text
这个接口不是 Tool Calling 的最终形态。
```

真正 Tool Calling 的入口不是用户手动访问 `/tools/query-order`。

真正流程会是：

```text
用户输入自然语言
-> 模型判断需要 query_order
-> 模型返回 tool call
-> 后端校验 arguments
-> 后端执行 query_order
-> 后端把结果交回给模型或返回给用户
```

这一节只是先把后端工具本身准备好。

## 当前还不是完整 Tool Calling

现在我们已经有：

```text
query_order 工具函数
工具参数模型
工具结果模型
工具接口
自动化测试
```

但还没有：

```text
模型自动决定是否调用 query_order
模型生成 tool call
后端解析模型 tool call
工具结果再交给模型总结
Java mock API
LangChain Tool 封装
```

所以当前阶段应该这样理解：

```text
我们先做好“后端可执行的工具”。
下一步再让模型学会“什么时候请求调用工具”。
```

## 这和上一节的关系

上一节讲了：

```text
结构化输出 = 固定格式返回数据。
Tool Calling = 模型提出工具调用请求。
```

这一节的 `query_order` 属于 Tool Calling 里“后端真正执行的工具”。

但当前我们是手动调用它。

未来模型可能返回：

```json
{
  "tool_name": "query_order",
  "arguments": {
    "order_id": "A1001"
  }
}
```

后端要做：

```text
QueryOrderArgs.model_validate({"order_id": "A1001"})
-> query_order(args)
-> QueryOrderResult
```

这就是今天代码的价值。

## 这和 Java 后端的关系

你原本是 Java 后端方向。

所以要把这节放到真实架构里看：

```text
Python AI 服务
-> 工具函数 query_order
-> Java 订单服务
-> 数据库
```

现在 fake tool 省略了 Java 和数据库：

```text
Python AI 服务
-> 工具函数 query_order
-> 内存 fake 数据
```

未来替换时，理想情况是：

```text
工具函数名不变。
工具参数模型不变。
工具返回模型尽量不变。
只把内部实现从 fake 数据换成 httpx 调 Java API。
```

这就是工程里的“边界稳定”。

## 为什么工具结果也要模型

这节已经定义了：

```text
QueryOrderResult
```

它也是 Pydantic 模型。

严格来说，这已经在做“工具结果模型化”。

但下一节会专门讲：

```text
工具调用结果也要 Pydantic 校验。
```

为什么要单独讲？

因为未来接 Java API 时，Java 返回的数据也是外部输入。

比如 Java 可能返回：

```json
{
  "status": "UNKNOWN_STATUS",
  "paid": "yes"
}
```

这对 Python AI 服务来说也不可信。

所以不只是模型输出要校验。

工具结果、Java API 返回、数据库外部输入，都要校验。

## 怎么运行

进入项目：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
```

启动服务：

```powershell
uv run uvicorn app.main:app --reload
```

打开文档：

```text
http://127.0.0.1:8000/docs
```

找到：

```text
POST /tools/query-order
```

请求：

```json
{
  "order_id": "A1001"
}
```

你也可以直接用 PowerShell：

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/tools/query-order" `
  -ContentType "application/json" `
  -Body '{"order_id":"A1001"}'
```

## 本节测试

本节新增测试：

```text
tests/test_tool_schema.py
tests/test_fake_order_tool.py
tests/test_tools_api.py
```

你可以只跑这几组：

```powershell
uv run pytest tests/test_tool_schema.py tests/test_fake_order_tool.py tests/test_tools_api.py -q
```

也可以跑全量：

```powershell
uv run pytest -q
```

测试覆盖了：

- `order_id` 首尾空格会被去掉。
- 空 `order_id` 会被拒绝。
- 中间带空格的 `order_id` 会被拒绝。
- 工具结果只能使用允许的订单状态。
- `query_order(A1001)` 可以返回 fake 数据。
- `query_order(A9999)` 会返回统一 404 错误。
- `/tools/query-order` 成功响应正确。
- `/tools/query-order` 参数错误会返回统一校验错误。
- `/tools/query-order` 不允许 GET。

## 练习 1：新增一条假订单

请你在 `_FAKE_ORDER_STORE` 里新增一条订单：

```text
A1004
```

要求：

```text
order_status = canceled
payment_status = refunded
logistics_message = 订单已取消并退款。
latest_event = 退款已原路退回。
can_create_ticket = false
```

然后新增一个测试：

```text
查询 A1004 时，返回 canceled 和 refunded。
```

### 练习 1 参考答案

可以在 `_FAKE_ORDER_STORE` 增加：

```python
"A1004": QueryOrderResult(
    order_id="A1004",
    order_status=OrderStatus.CANCELED,
    payment_status=PaymentStatus.REFUNDED,
    logistics_message="订单已取消并退款。",
    latest_event="退款已原路退回。",
    can_create_ticket=False,
),
```

测试可以写：

```python
def test_query_order_returns_canceled_order() -> None:
    result = query_order(QueryOrderArgs(order_id="A1004"))

    assert result.order_status == OrderStatus.CANCELED
    assert result.payment_status == PaymentStatus.REFUNDED
```

## 练习 2：为什么不能让模型直接传字符串给工具

问题：

```text
为什么不要直接写 query_order("A1001")，而是写 query_order(QueryOrderArgs(order_id="A1001"))？
```

### 练习 2 参考答案

因为真实 Tool Calling 里，模型返回的是外部输入：

```json
{
  "order_id": "A1001"
}
```

后端不能直接信。

用 `QueryOrderArgs` 可以统一做：

```text
字段是否存在
类型是否正确
长度是否合法
格式是否合法
首尾空格处理
```

校验通过后，再把可信参数交给工具函数。

## 练习 3：fake tool 和接口有什么区别

问题：

```text
query_order 函数和 /tools/query-order 接口有什么区别？
```

### 练习 3 参考答案

`query_order` 是后端内部工具函数。

`/tools/query-order` 是为了学习和手动测试而暴露的 HTTP 接口。

真实 Tool Calling 流程里，模型不会自己访问 `/tools/query-order`。

更常见的是：

```text
后端收到模型 tool call
-> 后端校验 arguments
-> 后端直接调用 query_order 函数
```

## 练习 4：解释一次成功调用

请解释下面请求发生了什么：

```http
POST /tools/query-order
```

```json
{
  "order_id": "A1001"
}
```

### 练习 4 参考答案

流程是：

```text
1. FastAPI 收到请求。
2. 请求体进入 QueryOrderArgs。
3. QueryOrderArgs 去掉首尾空格，并校验 order_id。
4. 校验通过后进入 tools router。
5. router 调用 fake_order_tool.query_order(...)。
6. query_order 从 _FAKE_ORDER_STORE 找到 A1001。
7. 返回 QueryOrderResult 的拷贝。
8. router 包装成 QueryOrderResponse。
9. FastAPI 返回 JSON。
```

## 练习 5：解释一次失败调用

请解释下面请求发生了什么：

```json
{
  "order_id": "A9999"
}
```

### 练习 5 参考答案

流程是：

```text
1. QueryOrderArgs 校验通过，因为 A9999 格式合法。
2. router 调用 query_order。
3. query_order 在 _FAKE_ORDER_STORE 找不到 A9999。
4. query_order 抛出 AppException。
5. 统一异常处理器把 AppException 转成 JSON。
6. 接口返回 404 和 ORDER_NOT_FOUND。
```

注意：

```text
A9999 格式合法，但业务上不存在。
```

所以它不是 422 参数校验错误，而是 404 业务资源不存在。

## 自测题

### 1. fake tool 是什么？

参考答案：

```text
fake tool 是本地模拟的工具实现，用来代替暂时还没接入的真实外部系统，比如 Java 订单服务。
```

### 2. 为什么这一节先不用真实 Java 服务？

参考答案：

```text
因为当前学习重点是工具输入、输出、错误和测试边界。如果一开始接 Java 服务，会同时引入网络、接口、鉴权、超时、404、500 等问题，干扰主线。
```

### 3. `QueryOrderArgs` 的作用是什么？

参考答案：

```text
它定义 query_order 工具需要的参数结构，并负责校验 order_id 是否存在、是否是字符串、长度和格式是否合法。
```

### 4. `QueryOrderResult` 的作用是什么？

参考答案：

```text
它定义查询订单工具返回的数据结构，让工具结果有稳定字段和固定状态枚举。
```

### 5. 查不到订单为什么返回 404，而不是 422？

参考答案：

```text
因为 order_id 的格式是合法的，只是业务数据里没有这个订单。422 表示请求参数结构或类型不合法，404 表示资源不存在。
```

### 6. 当前 `/tools/query-order` 是完整 Tool Calling 吗？

参考答案：

```text
不是。它只是学习用接口，用来手动验证后端工具函数。完整 Tool Calling 还需要模型决定是否调用工具、返回工具名和参数、后端解析 tool call、执行工具并把结果交回模型。
```

### 7. 为什么 `query_order` 返回结果时要拷贝？

参考答案：

```text
因为 fake 数据存放在共享字典里，返回拷贝可以避免调用方不小心修改共享假数据。
```

## 本节小结

这一节你要记住：

```text
fake tool 是真实工具的替身。
工具函数本质是普通后端函数。
工具输入必须校验。
工具输出要有稳定结构。
当前只是手动验证工具，还没有让模型自动调用工具。
```

当前我们已经完成：

```text
query_order(order_id)
```

下一节继续补齐：

```text
工具调用结果也要 Pydantic 校验。
```

也就是专门讲：为什么不只模型输出要校验，Java API 或工具返回的数据也要校验。
