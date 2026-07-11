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
-> 内存订单数据
```

## 当前接口

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| `GET` | `/health` | 健康检查 |
| `GET` | `/orders/{order_id}` | 查询订单 |

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

## 项目结构

```text
app/
  core/
    exception_handlers.py  统一错误响应
    exceptions.py          mock 服务异常
  routers/
    health.py              /health
    orders.py              /orders/{order_id}
  schemas/
    error.py               错误响应模型
    health.py              健康检查响应模型
    order.py               订单响应模型和枚举
  services/
    order_service.py       mock 订单业务逻辑和内存数据
  main.py                  FastAPI 应用入口
tests/
  conftest.py              pytest 共享夹具
  test_health_api.py       健康检查接口测试
  test_order_service.py    订单 service 测试
  test_orders_api.py       订单接口测试
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

下一节会让 `ai-service` 调用这个 mock 服务，把当前内部 fake 数据逐步替换成跨服务 HTTP 调用。
