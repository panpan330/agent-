# Java Mock Service

这个项目用 FastAPI 临时模拟 Java 业务后端。

它现在还不是真正的 Spring Boot 服务。当前阶段先用你已经熟悉的 FastAPI 快速搭一个“业务服务 API”，让后续 `ai-service` 学习跨服务调用时有一个稳定目标。

真实目标关系是：

```text
Python AI Service
-> Java Business Service
-> 订单、工单、权限等业务系统
```

当前学习阶段先模拟成：

```text
Python AI Service
-> Java Mock Service
-> 内存订单数据 / 内存工单数据
```

## 当前接口

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| `GET` | `/health` | 健康检查 |
| `GET` | `/orders/{order_id}` | 查询订单 |
| `POST` | `/tickets` | 创建工单，支持 `Idempotency-Key` |

## 运行

首次进入项目时同步依赖：

```powershell
uv sync
```

启动服务：

```powershell
uv run uvicorn app.main:app --reload --port 8001
```

启动后访问：

```text
http://127.0.0.1:8001/health
http://127.0.0.1:8001/orders/A1001
http://127.0.0.1:8001/tickets
http://127.0.0.1:8001/docs
```

这里使用 `8001` 端口，是为了和 `ai-service` 常用的 `8000` 端口区分开。

## 订单接口示例

请求：

```http
GET /orders/A1001
```

响应：

```json
{
  "order_id": "A1001",
  "customer_id": "C9001",
  "order_status": "waiting_shipment",
  "payment_status": "paid",
  "logistics_message": "商家已接单，等待仓库发货。",
  "latest_event": "仓库正在准备出库。",
  "can_create_ticket": true
}
```

订单不存在：

```http
GET /orders/A9999
```

响应：

```json
{
  "code": "ORDER_NOT_FOUND",
  "message": "订单不存在，请确认订单号是否正确。",
  "details": {
    "order_id": "A9999"
  }
}
```

模拟服务内部错误：

```http
GET /orders/A500
```

响应：

```json
{
  "code": "ORDER_SERVICE_ERROR",
  "message": "订单服务内部错误，请稍后重试。"
}
```

## 工单接口示例

请求：

```http
POST /tickets
Idempotency-Key: ticket-create-key-001
```

```json
{
  "requester_id": "demo_user_001",
  "title": "订单 A1001 未发货",
  "description": "用户反馈订单迟迟未发货。",
  "category": "complaint",
  "priority": "high",
  "related_order_id": "A1001"
}
```

响应：

```json
{
  "ticket_id": "T1001",
  "requester_id": "demo_user_001",
  "title": "订单 A1001 未发货",
  "description": "用户反馈订单迟迟未发货。",
  "category": "complaint",
  "priority": "high",
  "related_order_id": "A1001",
  "created_at": "2026-07-12T10:00:00Z"
}
```

同一个 `Idempotency-Key` 配同一份参数会返回同一张工单；如果同一个幂等键换了参数，会返回 `TICKET_IDEMPOTENCY_KEY_CONFLICT`。这模拟真实业务服务对写操作的防重复保护。

## 项目结构

```text
app/
  core/
    exception_handlers.py  统一错误响应
    exceptions.py          mock 服务异常
  routers/
    health.py              /health
    orders.py              /orders/{order_id}
    tickets.py             /tickets
  schemas/
    error.py               错误响应模型
    health.py              健康检查响应模型
    order.py               订单响应模型和枚举
    ticket.py              工单创建请求和响应模型
  services/
    order_service.py       mock 订单业务逻辑和内存数据
    ticket_service.py      mock 工单创建、内存数据和幂等保护
  main.py                  FastAPI 应用入口
tests/
  conftest.py              pytest 共享夹具
  test_health_api.py       健康检查接口测试
  test_order_service.py    订单 service 测试
  test_orders_api.py       订单接口测试
  test_tickets_api.py      工单创建和幂等测试
```

## 测试

```powershell
uv run pytest -q
```

编译检查：

```powershell
uv run python -m compileall -q -x ".venv|__pycache__" .
```

## 当前学习重点

这个项目重点不是 FastAPI 本身，而是让你理解业务服务边界：

```text
AI 服务不直接读数据库。
AI 服务通过 HTTP 调用业务服务。
业务服务负责订单、权限、工单等真实业务规则。
AI 服务负责模型调用、工具编排和结果总结。
```

当前 `ai-service` 已经通过 HTTP 调用这个 mock 服务查询订单，并能在用户确认后调用 `POST /tickets` 创建工单。后续会继续补工具调用日志、trace_id 串联和更接近真实 Java 服务的业务边界。
