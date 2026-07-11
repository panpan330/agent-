# 阶段 3 第 10 节：用 FastAPI 写一个最小 Java mock 业务服务

## 本节目标

前面我们已经有了：

```text
Python AI 服务
-> /tools/query-order
-> fake_order_tool.py
-> Python 内存里的 _FAKE_ORDER_STORE
```

这适合学习工具调用的基本流程。

但真实项目里，订单数据通常不应该放在 Python AI 服务里。
你的主线是：

```text
Java 后端负责真实业务系统。
Python AI 服务负责 AI 调用、工具编排和结果总结。
```

所以后续架构应该逐步变成：

```text
Python AI Service
-> HTTP 调用
-> Java Business Service
-> 订单、工单、权限、数据库
```

本节先不直接写 Spring Boot。
我们先用 FastAPI 写一个很小的 `java-mock-service`，模拟 Java 业务服务。

学完本节你要能解释：

- 什么是 mock service。
- 为什么现在先模拟 Java 服务。
- 为什么 AI 服务不应该直接读业务数据库。
- `ai-service` 和 `java-mock-service` 应该是什么关系。
- 什么是路径参数 `/orders/{order_id}`。
- 为什么 mock 服务也要有响应模型。
- 为什么 mock 服务也要有统一错误响应。
- 为什么业务服务应该返回稳定错误码。
- 怎么启动、测试这个 mock 服务。
- 后续 Python AI 服务如何调用它。

## 什么是 mock service

`mock` 可以理解成：

```text
假的、模拟的、临时代替真实系统的东西。
```

`mock service` 就是：

```text
用一个简单服务模拟真实服务的接口和响应。
```

比如真实 Java 服务以后可能是：

```text
Spring Boot
-> Controller
-> Service
-> Repository
-> MySQL
```

但现在我们先用：

```text
FastAPI
-> router
-> service
-> 内存 dict
```

来模拟它。

为什么这样做？

因为当前学习重点不是 Spring Boot 本身，而是：

```text
AI 服务怎么通过 HTTP 调用业务服务。
业务服务应该返回什么格式。
AI 服务应该怎么处理成功、404、500。
```

先把跨服务调用链学明白，再换成真正 Java 服务。

## 为什么不直接上 Spring Boot

你有 Java 基础，但这一阶段重点是 Tool Calling 和 AI 服务编排。

如果现在同时引入：

```text
Spring Boot
Controller
Service
Maven/Gradle
配置文件
端口
序列化
异常处理
跨服务 HTTP
AI 工具调用
```

学习负担会一下变重。

所以本节先用你已经熟悉的 FastAPI 快速搭一个 mock。
等调用流程跑通，再把 mock 替换成 Spring Boot。

你要记住：

```text
现在用 FastAPI 是为了模拟 Java 服务边界，不是说真实项目要用 Python 写业务后端。
```

## 为什么 AI 服务不能直接查订单数据库

很多初学者会想：

```text
Python AI 服务直接连数据库查订单，不是更简单吗？
```

短期看简单，长期会出大问题。

原因：

```text
业务规则绕过 Java 后端。
权限校验可能被绕过。
订单字段含义容易理解错。
数据库表结构变化会影响 AI 服务。
AI 服务会和业务数据库强耦合。
审计、限流、风控不统一。
```

正确边界应该是：

```text
业务服务负责业务事实和业务规则。
AI 服务负责调用业务服务，并把结果转成用户能理解的回答。
```

比如查订单：

```text
AI 服务不应该自己拼 SQL。
AI 服务应该调用 Java 的订单查询 API。
```

以后创建工单也是：

```text
AI 服务不应该自己写工单表。
AI 服务应该调用 Java 的工单创建 API。
```

## 本节新增项目

新增目录：

```text
projects/java-mock-service
```

它是一个独立服务，不属于 `ai-service`。

当前结构：

```text
projects/java-mock-service/
  app/
    core/
      exception_handlers.py
      exceptions.py
    routers/
      health.py
      orders.py
    schemas/
      error.py
      health.py
      order.py
    services/
      order_service.py
    main.py
  tests/
    conftest.py
    test_health_api.py
    test_order_service.py
    test_orders_api.py
  pyproject.toml
  README.md
  uv.lock
```

这和 `ai-service` 的分层思想类似：

| 层 | 作用 |
| --- | --- |
| `routers` | 接收 HTTP 请求 |
| `schemas` | 定义请求/响应结构 |
| `services` | 写业务逻辑 |
| `core` | 放通用异常处理 |
| `tests` | 自动化测试 |

## 当前接口

本节只做两个接口：

```text
GET /health
GET /orders/{order_id}
```

### `/health`

健康检查接口。

请求：

```http
GET /health
```

响应：

```json
{
  "status": "ok",
  "service": "java-mock-service"
}
```

这个接口的作用是：

```text
确认服务是否启动。
确认服务是否能被访问。
后续被 Docker、网关、监控系统检查。
```

### `/orders/{order_id}`

订单查询接口。

请求：

```http
GET /orders/A1001
```

这里的 `A1001` 就是路径参数。

在 FastAPI 代码里：

```python
@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: str) -> OrderResponse:
    return get_order_by_id(order_id)
```

路径里的：

```text
{order_id}
```

会被 FastAPI 取出来，传给函数参数：

```text
order_id
```

这就是路径参数。

## 为什么用 GET

查订单是读取数据。

所以接口设计成：

```text
GET /orders/{order_id}
```

而不是：

```text
POST /orders/query
```

这里先记一个简单规则：

```text
读取资源，优先 GET。
创建资源，通常 POST。
整体替换资源，通常 PUT。
局部修改资源，通常 PATCH。
删除资源，通常 DELETE。
```

后续创建工单会更适合：

```text
POST /tickets
```

## `OrderResponse`

文件：

```text
projects/java-mock-service/app/schemas/order.py
```

核心模型：

```python
class OrderResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: str
    customer_id: str
    order_status: OrderStatus
    payment_status: PaymentStatus
    logistics_message: str
    latest_event: str
    can_create_ticket: bool
```

这个模型代表：

```text
订单服务对外承诺的订单响应结构。
```

为什么 mock 服务也要写模型？

因为后续 `ai-service` 会依赖这个接口。
如果 mock 服务随便返回字段，下一节调用它时就很难稳定测试。

接口之间一定要有契约。

这里的契约就是：

```text
字段名
字段类型
枚举值
是否允许多余字段
错误响应格式
```

## 订单状态枚举

当前订单状态：

```python
class OrderStatus(StrEnum):
    WAITING_SHIPMENT = "waiting_shipment"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELED = "canceled"
```

支付状态：

```python
class PaymentStatus(StrEnum):
    UNPAID = "unpaid"
    PAID = "paid"
    REFUNDED = "refunded"
```

为什么要用枚举？

因为状态字段不能随便写。

不应该一会儿返回：

```text
waiting_shipment
```

一会儿返回：

```text
待发货
WAITING
wait_ship
```

稳定枚举能减少跨服务理解错误。

## mock 订单数据

文件：

```text
projects/java-mock-service/app/services/order_service.py
```

当前用内存字典模拟数据库：

```python
_ORDER_STORE = {
    "A1001": {...},
    "A1002": {...},
    "A1003": {...},
}
```

这不是生产做法。
它只是为了模拟：

```text
Java 服务查数据库后返回订单。
```

以后真正 Java 服务里，这部分会变成：

```text
Repository 查询数据库
Service 处理业务规则
Controller 返回 JSON
```

## 成功、404、500

本节 mock 服务故意设计了三类结果。

### 成功

```text
GET /orders/A1001
```

返回 200 和订单 JSON。

### 订单不存在

```text
GET /orders/A9999
```

返回：

```json
{
  "code": "ORDER_NOT_FOUND",
  "message": "订单不存在，请确认订单号是否正确。",
  "details": {
    "order_id": "A9999"
  }
}
```

状态码：

```text
404
```

这表示：

```text
请求格式没问题，但业务资源不存在。
```

### 模拟服务内部错误

```text
GET /orders/A500
```

返回：

```json
{
  "code": "ORDER_SERVICE_ERROR",
  "message": "订单服务内部错误，请稍后重试。"
}
```

状态码：

```text
500
```

这里的 `A500` 是一个测试用特殊订单号。
它用来模拟：

```text
Java 业务服务内部出错。
```

下一节 `ai-service` 调用它时，会学习：

```text
Java mock 返回 500
-> Python AI 服务应该映射成 TOOL_UPSTREAM_ERROR
-> 对外返回 502
```

## 为什么 mock 服务返回 500，AI 服务对外可能返回 502

从 mock 服务自己的角度：

```text
它内部出错了，所以它返回 500。
```

从 `ai-service` 的角度：

```text
ai-service 没有自己崩溃，是它依赖的上游业务服务出错。
```

所以 `ai-service` 对它自己的调用方更适合返回：

```text
502 Bad Gateway
```

这就是服务视角不同导致的状态码差异。

当前先记住：

```text
业务服务自身出错：业务服务返回 500。
AI 服务调用业务服务失败：AI 服务可以对外映射成 502。
```

## 统一错误响应

本节 mock 服务也加了统一错误格式：

```json
{
  "code": "...",
  "message": "...",
  "details": {}
}
```

对应文件：

```text
app/core/exceptions.py
app/core/exception_handlers.py
app/schemas/error.py
```

这样做的原因：

```text
调用方不用猜错误结构。
测试可以稳定断言错误码。
后续 ai-service 可以按 code 做错误映射。
前端也可以按 code 做提示。
```

如果没有统一错误格式，可能一会儿是：

```json
{"detail": "not found"}
```

一会儿是：

```json
{"error": "ORDER_NOT_FOUND"}
```

一会儿又是：

```text
Java stacktrace
```

这会让调用方很难处理。

## `create_app`

文件：

```text
app/main.py
```

代码：

```python
def create_app() -> FastAPI:
    app = FastAPI(...)
    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(orders.router)
    return app
```

为什么写 `create_app()`？

因为测试里可以这样创建独立应用：

```python
test_app = create_app()
```

这样测试不用依赖全局状态。

同时入口还保留：

```python
app = create_app()
```

这样 Uvicorn 可以启动：

```powershell
uv run uvicorn app.main:app --reload --port 8001
```

## 为什么用 8001 端口

之前 `ai-service` 通常用：

```text
8000
```

如果两个服务都用 8000，就会端口冲突。

所以本节建议：

```text
ai-service: 8000
java-mock-service: 8001
```

后续跨服务调用会变成：

```text
ai-service -> http://127.0.0.1:8001/orders/A1001
```

## 运行方式

进入项目：

```powershell
cd D:\wendang\java+python+ai\projects\java-mock-service
```

同步依赖：

```powershell
uv sync
```

启动：

```powershell
uv run uvicorn app.main:app --reload --port 8001
```

访问：

```text
http://127.0.0.1:8001/health
http://127.0.0.1:8001/orders/A1001
http://127.0.0.1:8001/orders/A9999
http://127.0.0.1:8001/orders/A500
http://127.0.0.1:8001/docs
```

## 本节测试

测试文件：

```text
tests/test_health_api.py
tests/test_order_service.py
tests/test_orders_api.py
```

运行：

```powershell
uv run pytest -q
```

当前覆盖：

- `/health` 返回 200。
- `/orders/A1001` 返回订单数据。
- `/orders/A9999` 返回 `ORDER_NOT_FOUND` 和 404。
- `/orders/A500` 返回 `ORDER_SERVICE_ERROR` 和 500。
- 非法订单号返回 `VALIDATION_ERROR` 和 422。
- `get_order_by_id(...)` service 函数能被单独测试。

为什么 service 函数也要单独测试？

因为业务逻辑不应该只能通过 HTTP 测。
HTTP 测试验证接口。
service 测试验证业务判断。

两类测试配合，问题更容易定位。

## 当前它和 `ai-service` 还没有连起来

本节只是创建 mock 服务。
当前 `ai-service` 还在调用：

```text
fake_order_tool.py
```

下一节才会改成：

```text
ai-service
-> httpx 调用 java-mock-service
-> GET /orders/{order_id}
```

也就是说，本节先准备被调用方。
下一节再写调用方。

## 练习 1：判断服务边界

请判断下面职责应该放在哪个服务里：

```text
A. Python AI Service
B. Java Business Service
```

题目：

1. 调用大模型总结订单状态。
2. 查询订单是否存在。
3. 校验当前用户是否有权查看订单。
4. 生成工具调用参数。
5. 创建工单。
6. 把订单结果组织成自然语言回答。
7. 保存订单表。

### 练习 1 参考答案

1. A。模型总结属于 AI 服务职责。
2. B。订单是否存在属于业务服务职责。
3. B。权限校验属于业务后端核心职责。
4. A。工具参数生成属于 AI 编排职责。
5. B。创建工单是业务写入动作。
6. A。自然语言回答由 AI 服务生成。
7. B。订单表属于业务系统数据。

## 练习 2：判断状态码

请判断下面场景应该返回什么状态码：

1. `/health` 正常。
2. `/orders/A1001` 找到订单。
3. `/orders/A9999` 订单不存在。
4. `/orders/A500` 模拟服务内部错误。
5. `/orders/A 1001` 订单号格式不合法。

### 练习 2 参考答案

1. 200。健康检查成功。
2. 200。订单查询成功。
3. 404。请求格式合法，但业务资源不存在。
4. 500。mock 业务服务自身内部错误。
5. 422。路径参数格式不符合校验规则。

## 练习 3：解释路径参数

问题：

```text
`/orders/{order_id}` 里的 `{order_id}` 是什么？
```

### 练习 3 参考答案

`{order_id}` 是路径参数。
它表示 URL 里的这一段是变量。

例如：

```text
/orders/A1001
```

FastAPI 会把 `A1001` 取出来，传给函数参数：

```python
def get_order(order_id: str):
```

所以函数里能拿到：

```text
order_id = "A1001"
```

## 练习 4：为什么要写 `OrderResponse`

问题：

```text
既然只是 mock 服务，为什么还要写 Pydantic 响应模型？
```

### 练习 4 参考答案

因为 mock 服务也是接口契约的一部分。
后续 `ai-service` 会依赖它返回的字段。

`OrderResponse` 可以保证：

```text
字段名稳定。
字段类型稳定。
状态值受枚举约束。
多余字段被禁止。
自动生成 OpenAPI 文档。
测试可以稳定断言响应结构。
```

## 练习 5：设计下一个接口

假设下一步要模拟创建工单接口，请设计路径和方法。

要求：

```text
创建一个新资源。
资源名叫 ticket。
```

### 练习 5 参考答案

可以设计成：

```text
POST /tickets
```

因为创建新资源通常使用 `POST`。

请求体可以是：

```json
{
  "order_id": "A1001",
  "title": "订单未发货",
  "description": "用户询问什么时候发货"
}
```

响应可以是：

```json
{
  "ticket_id": "T1001",
  "order_id": "A1001",
  "status": "created"
}
```

后续这个接口还需要：

```text
用户确认
权限校验
幂等键
字段校验
错误响应
```

## 自测题

### 1. 什么是 mock service？

参考答案：

```text
mock service 是用一个简单服务临时代替真实服务，用来模拟真实接口的请求、响应和错误场景。
```

### 2. 为什么本节用 FastAPI 模拟 Java 服务？

参考答案：

```text
因为当前重点是学习 AI 服务如何调用业务服务。先用熟悉的 FastAPI 快速模拟接口，可以降低学习负担。后续再把 mock 替换成真正 Spring Boot。
```

### 3. `ai-service` 和 `java-mock-service` 的关系是什么？

参考答案：

```text
ai-service 是调用方，负责 AI 编排和工具调用。java-mock-service 是被调用方，模拟 Java 业务服务，负责返回订单业务数据。
```

### 4. 为什么 AI 服务不应该直接查订单数据库？

参考答案：

```text
因为这样会绕过业务后端的权限、规则、审计和数据边界，导致 AI 服务和数据库强耦合。AI 服务应该通过业务 API 获取数据。
```

### 5. `/orders/A9999` 为什么返回 404？

参考答案：

```text
因为请求格式合法，但订单资源不存在。它不是参数格式错误，也不是服务崩溃。
```

### 6. `/orders/A500` 为什么返回 500？

参考答案：

```text
因为这是 mock 服务用来模拟业务服务自身内部错误的特殊订单号。从该服务视角看，它内部处理失败，所以返回 500。
```

### 7. 为什么下一节 `ai-service` 调用到这个 500 时可能对外返回 502？

参考答案：

```text
因为从 ai-service 的视角看，是它依赖的上游业务服务失败，不是 ai-service 自己内部逻辑崩溃。所以对 ai-service 的调用方可以映射成 502。
```

### 8. 为什么要把 mock 服务做成独立项目？

参考答案：

```text
因为真实架构里 AI 服务和业务服务是两个不同服务。独立项目能帮助我们学习端口、进程、HTTP 调用和服务边界。
```

## 本节小结

这一节完成了一个最小业务服务：

```text
projects/java-mock-service
```

它现在能提供：

```text
GET /health
GET /orders/{order_id}
```

并能模拟：

```text
订单存在 -> 200
订单不存在 -> 404 ORDER_NOT_FOUND
服务错误 -> 500 ORDER_SERVICE_ERROR
参数错误 -> 422 VALIDATION_ERROR
```

这节最重要的不是代码量，而是服务边界：

```text
AI 服务不直接拥有业务数据。
业务数据由业务服务提供。
AI 服务通过 HTTP 工具调用业务服务。
```

下一节继续学习：

```text
Python AI 服务调用 Java mock API。
```

到时候我们会把现在 `fake_order_tool.py` 里的内存查询，逐步替换成对：

```text
http://127.0.0.1:8001/orders/{order_id}
```

的 HTTP 调用。

## 资料来源

- [FastAPI：Path Parameters](https://fastapi.tiangolo.com/tutorial/path-params/)
- [FastAPI：Bigger Applications - Multiple Files](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [FastAPI：Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [FastAPI：Testing](https://fastapi.tiangolo.com/tutorial/testing/)
