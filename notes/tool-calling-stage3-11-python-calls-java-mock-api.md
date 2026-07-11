# 阶段 3 第 11 节：Python AI 服务调用 Java mock API

## 本节目标

上一节我们创建了一个独立的 `java-mock-service`：

```text
GET /health
GET /orders/{order_id}
```

它现在模拟的是未来真正的 Java 业务服务。

这一节我们要把 `ai-service` 里的订单查询工具，从“自己查本地 fake 数据”改成“通过 HTTP 调用 Java mock API”。

改造前：

```text
POST /tools/query-order
-> fake_order_tool.py
-> Python 内存里的假订单数据
```

改造后：

```text
POST /tools/query-order
-> fake_order_tool.py
-> JavaOrderClient
-> HTTP GET http://127.0.0.1:8001/orders/{order_id}
-> java-mock-service
-> 订单 JSON
-> 映射成 QueryOrderResult
```

本节学完后，你要能解释：

- 什么是跨服务 HTTP 调用。
- 什么是调用方和被调用方。
- `base_url` 是什么。
- 为什么要单独写 `JavaOrderClient`。
- 为什么 router 里不直接写 `httpx.get(...)`。
- `httpx.Client` 是什么。
- `timeout` 为什么必须配置。
- Java mock 返回 404、500、非法 JSON 时，Python AI 服务应该怎么处理。
- 为什么上游服务返回 500，AI 服务对外更适合返回 502。
- 为什么 Java mock 返回的字段不能原样全部暴露给 AI 工具结果。
- 什么是 DTO 映射，为什么它是服务边界的一部分。
- 为什么 Java API 的返回结果还要再用 Pydantic 校验。
- 为什么测试里使用 `httpx.MockTransport`，而不是每次都启动 8001 服务。

## 先记住一句话

```text
AI 服务不应该拥有订单数据，它应该调用业务服务获得订单数据。
```

这句话非常重要。

在真实项目中，订单、退款、工单、权限这些数据通常属于 Java 后端或业务系统。Python AI 服务更适合负责：

```text
理解用户问题
决定是否需要调用工具
准备工具参数
调用业务 API
把业务结果组织成回答
记录调用日志和 trace_id
处理模型调用与工具调用错误
```

Java 业务服务更适合负责：

```text
订单是否存在
当前用户有没有权限看订单
订单状态怎么计算
能不能创建工单
能不能退款
业务规则和数据一致性
```

所以这一节的关键不是“学会调一个接口”这么简单，而是开始建立真实后端工程里的服务边界。

## 什么是跨服务调用

先把概念拆开。

服务可以理解为：

```text
一个独立运行的后端程序，对外提供 API。
```

现在我们有两个服务：

```text
ai-service
java-mock-service
```

它们是两个独立项目，也可以是两个独立进程：

```text
ai-service:         http://127.0.0.1:8000
java-mock-service:  http://127.0.0.1:8001
```

当 `ai-service` 需要订单数据时，它不再自己查本地字典，而是发 HTTP 请求：

```http
GET http://127.0.0.1:8001/orders/A1001
```

这就叫跨服务 HTTP 调用。

## 调用方和被调用方

这一节里：

| 角色 | 服务 | 作用 |
| --- | --- | --- |
| 调用方 | `ai-service` | 主动发 HTTP 请求，查询订单 |
| 被调用方 | `java-mock-service` | 接收请求，返回订单数据 |

用一句话说：

```text
ai-service 调用 java-mock-service。
```

真实项目以后会变成：

```text
Python AI Service 调用 Java Spring Boot Business Service。
```

当前用 FastAPI 写 `java-mock-service`，只是为了降低学习负担，先把“跨服务调用链路”学清楚。

## 什么是 `base_url`

`base_url` 就是一个服务的基础地址。

例如 Java mock 服务运行在：

```text
http://127.0.0.1:8001
```

那么：

```text
base_url = "http://127.0.0.1:8001"
```

具体订单接口是：

```text
/orders/A1001
```

把它们合起来就是：

```text
http://127.0.0.1:8001/orders/A1001
```

代码里我们会这样写：

```python
with httpx.Client(base_url=self.base_url) as client:
    response = client.get(f"/orders/{order_id}")
```

这里 `client.get("/orders/A1001")` 会自动拼到 `base_url` 后面。

## 本节新增配置

文件：

```text
projects/ai-service/.env.example
```

新增：

```env
JAVA_MOCK_SERVICE_BASE_URL="http://127.0.0.1:8001"
JAVA_MOCK_SERVICE_TIMEOUT_SECONDS=5
```

为什么要放进配置，而不是直接写死在代码里？

因为不同环境地址可能不同：

```text
本地开发: http://127.0.0.1:8001
Docker Compose: http://java-mock-service:8001
测试环境: http://test-business-service:8080
生产环境: https://business-api.example.com
```

如果写死在代码里，每换一个环境都要改代码。

如果放在 `.env` 或环境变量里，只需要改配置。

## `Settings` 里新增了什么

文件：

```text
projects/ai-service/app/core/config.py
```

新增配置字段：

```python
java_mock_service_base_url: str = Field(default="http://127.0.0.1:8001")
java_mock_service_timeout_seconds: float = Field(default=5.0, gt=0)
```

这两个字段分别表示：

| 字段 | 含义 |
| --- | --- |
| `java_mock_service_base_url` | Java mock 服务基础地址 |
| `java_mock_service_timeout_seconds` | 调用 Java mock 服务最多等几秒 |

还新增了一个属性：

```python
@property
def resolved_java_mock_service_base_url(self) -> str:
    return self.java_mock_service_base_url.strip().rstrip("/")
```

它做两件事：

```text
strip()      去掉前后空格
rstrip("/") 去掉末尾多余的斜杠
```

这样用户即使配置成：

```text
" http://127.0.0.1:8001/ "
```

代码里最终也会变成：

```text
http://127.0.0.1:8001
```

这是很常见的配置清洗动作。

## 为什么要引入 `httpx`

Python 里有很多 HTTP 客户端库。

你之前在 Python 基础阶段见过 `requests`。在 FastAPI、异步服务、测试友好场景里，`httpx` 很常见。

本项目当前依赖写在：

```text
projects/ai-service/pyproject.toml
```

依赖项里有：

```toml
"httpx2>=2.5.0"
```

这个包在当前环境里提供的导入名是：

```python
import httpx
```

所以代码里使用：

```python
import httpx
```

本节重点不是背库 API，而是理解 HTTP 客户端承担的职责：

```text
发请求
等响应
设置超时
解析响应状态码
读取 JSON
处理网络错误
```

## 为什么要写 `JavaOrderClient`

文件：

```text
projects/ai-service/app/services/java_order_client.py
```

核心类：

```python
class JavaOrderClient:
    def get_order(self, order_id: str) -> Mapping[str, Any]:
        ...
```

它的职责是：

```text
知道 Java mock 服务地址。
知道超时时间。
负责发 HTTP 请求。
负责把 HTTP/network 错误映射成 AppException。
负责把响应 JSON 读出来。
```

它不负责：

```text
决定模型要不要调用工具。
决定工具是否有权限执行。
决定最终返回给用户什么字段。
生成自然语言回答。
```

这些职责属于其他层。

## 为什么 router 里不直接写 `httpx.get(...)`

你可能会想：

```python
@router.post("/query-order")
def query_order(...):
    response = httpx.get("http://127.0.0.1:8001/orders/A1001")
```

这样看起来更短。

但真实项目里不推荐这么做。

原因是 router 的职责应该是：

```text
接收 HTTP 请求
触发参数校验
调用业务函数
返回响应模型
```

如果 router 里直接写 HTTP 调用，它会混进很多不属于 router 的细节：

```text
上游服务地址
超时时间
网络异常
状态码映射
JSON 解析
测试 mock
字段转换
```

这样后果是：

```text
router 越来越胖
测试越来越难写
以后换真实 Java 服务时影响面更大
多个地方调用订单服务时容易重复代码
```

所以我们把“怎么调用 Java 订单 API”放进：

```text
JavaOrderClient
```

router 只负责把请求交给工具函数。

## `JavaOrderClient.get_order` 的执行流程

核心流程可以拆成 7 步：

```text
1. 创建 httpx.Client
2. GET /orders/{order_id}
3. 如果网络超时，抛 TOOL_TIMEOUT
4. 如果连接失败，抛 TOOL_UPSTREAM_ERROR
5. 如果状态码是 404，抛 ORDER_NOT_FOUND
6. 如果状态码是 500 或更高，抛 TOOL_UPSTREAM_ERROR
7. 如果成功，解析 JSON 并返回 dict
```

对应代码大致是：

```python
with httpx.Client(
    base_url=self.base_url,
    timeout=self.timeout_seconds,
) as client:
    response = client.get(f"/orders/{order_id}")
```

注意这里用了 `with`。

`with httpx.Client(...) as client` 表示：

```text
进入 with 时创建 HTTP client。
离开 with 时自动关闭 client 占用的资源。
```

这和文件读写里的：

```python
with open("a.txt") as f:
    ...
```

是同一类思想。

## 为什么必须配置 timeout

调用外部服务时，不配置 timeout 是危险的。

假设 `java-mock-service` 卡住了，或者网络有问题：

```text
ai-service 等待 java-mock-service 响应。
请求线程一直占着。
用户一直等。
并发请求越来越多。
最后 ai-service 自己也被拖慢。
```

所以我们配置：

```text
JAVA_MOCK_SERVICE_TIMEOUT_SECONDS=5
```

意思是：

```text
最多等 5 秒。
超过 5 秒就认为工具调用超时。
```

当前映射成：

```text
TOOL_TIMEOUT
HTTP 504
```

为什么是 504？

因为从 `ai-service` 视角看，它是在等待上游服务响应时超时了。

## HTTP 状态码映射

Java mock 服务返回的状态码，不能简单原样透传给外部调用方。

当前映射规则：

| Java mock 返回 | Java mock 含义 | ai-service 对外返回 | ai-service 含义 |
| --- | --- | --- | --- |
| 200 | 订单查询成功 | 200 | 工具调用成功 |
| 404 | 订单不存在 | 404 `ORDER_NOT_FOUND` | 业务资源不存在 |
| 500 | Java mock 内部错误 | 502 `TOOL_UPSTREAM_ERROR` | AI 服务依赖的上游失败 |
| timeout | 调用超时 | 504 `TOOL_TIMEOUT` | 上游响应超时 |
| 非法 JSON | 上游响应格式坏了 | 502 `TOOL_RESULT_VALIDATION_FAILED` | 上游返回不可信 |

重点是 500 到 502 的变化。

从 `java-mock-service` 自己的视角看：

```text
我自己内部出错了，所以我返回 500。
```

从 `ai-service` 的视角看：

```text
不是我自己的核心逻辑崩了，是我依赖的上游服务失败了。
```

所以 `ai-service` 对外更适合返回：

```text
502 Bad Gateway
```

这就是“不同服务视角”导致的状态码差异。

## 网络错误和业务错误要分开

调用 Java mock API 时，至少会遇到两类错误。

第一类是网络或协议层错误：

```text
连接不上
读取超时
DNS 失败
返回内容不是 JSON
```

第二类是业务错误：

```text
订单不存在
没有权限
当前订单不允许创建工单
```

它们不能混在一起。

例如订单不存在不是网络坏了，它是业务资源不存在：

```text
ORDER_NOT_FOUND
404
```

Java mock 服务 500 不是订单不存在，它是上游服务失败：

```text
TOOL_UPSTREAM_ERROR
502
```

这类清晰区分，会让前端、日志、监控和排查都更容易。

## 为什么还叫 `fake_order_tool.py`

这一节没有立刻把文件改名。

当前文件仍然叫：

```text
projects/ai-service/app/tools/fake_order_tool.py
```

但它的内部实现已经从“查本地 fake 数据”改成“调用 Java mock 服务”。

为什么暂时不改名？

因为我们现在正在连续学习阶段中，前几节所有入口、测试和文档都围绕它展开。直接改名会带来大量重命名噪音，反而干扰本节核心知识点。

后面阶段整理时，可以把它改成更准确的名字，例如：

```text
order_tool.py
query_order_tool.py
```

本节先保持改动聚焦：

```text
先换实现，再整理命名。
```

## 什么是 DTO 映射

Java mock 返回的订单 JSON 是：

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

但是 AI 工具对外返回的是：

```json
{
  "order_id": "A1001",
  "order_status": "waiting_shipment",
  "payment_status": "paid",
  "logistics_message": "商家已接单，等待仓库发货。",
  "latest_event": "仓库正在准备出库。",
  "can_create_ticket": true,
  "source": "java_mock_service"
}
```

注意：`customer_id` 被去掉了。

这一步叫映射。

更正式一点，可以理解成 DTO 映射：

```text
上游服务返回的数据结构
-> AI 工具内部需要的数据结构
-> 对外安全暴露的数据结构
```

DTO 可以理解成 Data Transfer Object，也就是“用来传输数据的对象或结构”。

本节对应函数：

```python
def map_java_order_to_query_order_payload(raw_order: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "order_id": raw_order.get("order_id"),
        "order_status": raw_order.get("order_status"),
        "payment_status": raw_order.get("payment_status"),
        "logistics_message": raw_order.get("logistics_message"),
        "latest_event": raw_order.get("latest_event"),
        "can_create_ticket": raw_order.get("can_create_ticket"),
        "source": "java_mock_service",
    }
```

## 为什么不能把 Java 返回原样给模型

因为 Java 服务返回的字段不一定都适合进入 AI 上下文。

例如：

```text
customer_id
internal_note
user_phone
address
refund_risk_score
admin_flag
```

这些字段可能是：

```text
内部字段
敏感字段
权限字段
模型不需要知道的字段
容易造成误解的字段
```

所以工具层要做一层明确过滤：

```text
只把模型需要的、安全的、稳定的字段暴露出去。
```

这也是 AI 应用安全的一部分。

模型不能因为“上游服务返回了什么”就“看到什么”。

## 为什么 Java 返回结果还要 Pydantic 校验

你可能会问：

```text
Java mock 服务已经有 OrderResponse 了，为什么 Python 这边还要 QueryOrderResult 校验？
```

原因是：

```text
跨服务边界的数据永远要当成外部输入。
```

即使对方是我们自己写的服务，也可能出现：

```text
服务升级后字段改名
枚举值变化
字段缺失
字段类型变化
某次异常返回了错误结构
网关返回了 HTML 错误页
```

所以 Python AI 服务拿到数据后，仍然要用：

```python
QueryOrderResult.model_validate(raw_result)
```

校验成自己认可的数据结构。

这一步不是多余的。

它保护的是：

```text
AI 服务内部逻辑的稳定性
模型上下文的安全性
对外 API 响应的一致性
测试的可预测性
```

## 当前工具调用链路

现在 `/tools/query-order` 的完整链路是：

```text
POST /tools/query-order
-> app/routers/tools.py
-> QueryOrderArgs 校验 order_id
-> authorize_tool_call("query_order")
-> run_idempotent_tool(..., Idempotency-Key)
-> fake_order_tool.query_order(...)
-> JavaOrderClient.get_order(order_id)
-> GET /orders/{order_id}
-> map_java_order_to_query_order_payload(...)
-> validate_query_order_result(...)
-> QueryOrderResponse
```

这里已经串起了前几节学过的内容：

| 前面学的知识 | 本节如何使用 |
| --- | --- |
| Pydantic 请求模型 | `QueryOrderArgs` 校验 `order_id` |
| Pydantic 响应模型 | `QueryOrderResult` 校验工具结果 |
| 统一异常处理 | `AppException` 统一返回错误 JSON |
| 工具错误映射 | timeout、404、500 都映射成稳定错误码 |
| 工具权限边界 | `authorize_tool_call("query_order")` |
| 幂等性 | `Idempotency-Key` 重复请求复用结果 |
| mock service | `java-mock-service` 模拟 Java 业务服务 |

这就是为什么前面几节看起来都很小，但它们现在能组合成真实链路。

## 本节新增和修改的关键文件

新增：

```text
projects/ai-service/app/services/java_order_client.py
projects/ai-service/tests/test_java_order_client.py
```

修改：

```text
projects/ai-service/.env.example
projects/ai-service/pyproject.toml
projects/ai-service/app/core/config.py
projects/ai-service/app/tools/fake_order_tool.py
projects/ai-service/app/routers/tools.py
projects/ai-service/tests/test_config.py
projects/ai-service/tests/test_fake_order_tool.py
projects/ai-service/tests/test_tools_api.py
```

同时为了保证被调用方也能稳定返回正常中文和统一错误，修正了：

```text
projects/java-mock-service/app/core/exception_handlers.py
projects/java-mock-service/app/services/order_service.py
projects/java-mock-service/tests/test_order_service.py
projects/java-mock-service/tests/test_orders_api.py
projects/java-mock-service/README.md
```

## 为什么测试不用真的启动 8001

真实启动方式是：

```powershell
cd D:\wendang\java+python+ai\projects\java-mock-service
uv run uvicorn app.main:app --reload --port 8001
```

然后 `ai-service` 可以真的调用：

```text
http://127.0.0.1:8001/orders/A1001
```

但自动化测试不应该依赖一个正在运行的外部进程。

否则测试会变得不稳定：

```text
8001 没启动，测试失败。
8001 被别的程序占用，测试失败。
网络慢一点，测试失败。
Java mock 数据变了，ai-service 测试失败。
```

所以 `JavaOrderClient` 的单元测试使用：

```python
httpx.MockTransport
```

它可以在不发真实网络请求的情况下，模拟 HTTP 响应。

例如：

```python
def handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json=make_order_payload(), request=request)

client = JavaOrderClient(
    base_url="http://java-mock.test",
    timeout_seconds=1.0,
    transport=httpx.MockTransport(handler),
)
```

这样测试的是：

```text
JavaOrderClient 遇到 200、404、500、timeout、非法 JSON 时是否处理正确。
```

而不是测试真实网络。

## router 测试为什么 monkeypatch 工具函数

`tests/test_tools_api.py` 里没有真的调用 Java mock 服务。

它临时替换了 router 里的：

```text
run_query_order_tool
```

这叫 monkeypatch。

原因是 API 测试关注的是：

```text
/tools/query-order 是否接收请求
参数校验是否生效
trace_id 是否返回
幂等性是否生效
AppException 是否被统一异常处理
响应模型是否正确
```

而不是重复测试 JavaOrderClient。

分开测试的好处是：

```text
JavaOrderClient 测 HTTP 调用。
fake_order_tool 测字段映射和结果校验。
tools API 测路由、幂等、统一错误。
java-mock-service 测被调用方 API。
```

每类测试各管一层，问题更容易定位。

## 当前可以手动联调

开两个终端。

终端 1，启动 Java mock 服务：

```powershell
cd D:\wendang\java+python+ai\projects\java-mock-service
uv run uvicorn app.main:app --reload --port 8001
```

终端 2，启动 ai-service：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run uvicorn app.main:app --reload --port 8000
```

然后访问：

```text
http://127.0.0.1:8000/docs
```

调用：

```text
POST /tools/query-order
```

请求体：

```json
{
  "order_id": "A1001"
}
```

成功响应应该类似：

```json
{
  "result": {
    "order_id": "A1001",
    "order_status": "waiting_shipment",
    "payment_status": "paid",
    "logistics_message": "商家已接单，等待仓库发货。",
    "latest_event": "仓库正在准备出库。",
    "can_create_ticket": true,
    "source": "java_mock_service"
  }
}
```

注意：响应里没有 `customer_id`。

这是故意的。

## 手动测试几个订单号

| 订单号 | 预期结果 |
| --- | --- |
| `A1001` | 成功，待发货 |
| `A1002` | 成功，已发货 |
| `A1003` | 成功，已签收 |
| `A9999` | 404，`ORDER_NOT_FOUND` |
| `A500` | Java mock 返回 500，ai-service 映射成 502 `TOOL_UPSTREAM_ERROR` |

如果 Java mock 服务没启动，`ai-service` 调用会失败，通常会返回：

```text
TOOL_UPSTREAM_ERROR
```

这表示：

```text
ai-service 连接不上它依赖的订单服务。
```

## 本节容易混淆的点

### 1. `java-mock-service` 不是最终目标

当前它只是临时模拟。

最终我们会逐步走向：

```text
Spring Boot Java Service
```

但先学清楚跨服务调用链路，再换技术栈，会稳很多。

### 2. `ai-service` 不应该信任 Java 返回的一切

就算 Java 服务是自己写的，也要把跨服务返回当成外部输入。

所以本节保留：

```text
字段映射
Pydantic 校验
错误映射
```

### 3. 502 不等于 ai-service 自己崩了

在当前语义里：

```text
502 表示 ai-service 依赖的上游服务失败。
```

如果 ai-service 自己有未处理异常，才更接近：

```text
500 INTERNAL_SERVER_ERROR
```

### 4. timeout 不是可有可无

所有外部调用都应该有 timeout。

模型调用、Java API 调用、数据库调用、向量库调用，都一样。

没有 timeout 的外部调用，迟早会拖慢服务。

### 5. `MockTransport` 不是业务 mock

`MockTransport` 是测试层 mock HTTP 传输。

它不是 Java mock 服务。

区别：

| 名称 | 位置 | 作用 |
| --- | --- | --- |
| `java-mock-service` | 独立服务 | 模拟未来 Java 业务服务 |
| `httpx.MockTransport` | 测试代码 | 模拟 HTTP 响应，不走真实网络 |

## 练习 1：判断职责边界

请判断下面职责应该放在哪一层：

```text
A. ai-service
B. java-mock-service / Java Business Service
```

题目：

1. 根据用户问题决定是否需要查询订单。
2. 查询订单是否存在。
3. 判断订单状态是 `waiting_shipment` 还是 `delivered`。
4. 调用 `/orders/{order_id}`。
5. 把 `customer_id` 从工具结果里过滤掉。
6. 检查当前用户是否有权限查看订单。
7. 把订单结果总结成自然语言。

### 练习 1 参考答案

1. A。是否调用工具属于 AI 编排职责。
2. B。订单是否存在属于业务服务职责。
3. B。订单状态是业务事实，应该由业务服务提供。
4. A。调用业务 API 是 AI 服务的工具执行职责。
5. A。AI 服务决定暴露给模型和前端的安全字段。
6. B。权限校验通常属于业务后端核心职责。
7. A。自然语言总结属于 AI 服务职责。

## 练习 2：判断错误映射

请判断下面情况在 `ai-service` 对外应该返回什么错误码和 HTTP 状态码。

题目：

1. Java mock 返回 404。
2. Java mock 返回 500。
3. 调用 Java mock 超时。
4. Java mock 返回 200，但响应体不是 JSON。
5. Java mock 返回 200，但缺少 `logistics_message`。

### 练习 2 参考答案

1. `ORDER_NOT_FOUND`，HTTP 404。业务资源不存在。
2. `TOOL_UPSTREAM_ERROR`，HTTP 502。依赖的上游服务失败。
3. `TOOL_TIMEOUT`，HTTP 504。等待上游服务超时。
4. `TOOL_RESULT_VALIDATION_FAILED`，HTTP 502。上游响应格式不可信。
5. `TOOL_RESULT_VALIDATION_FAILED`，HTTP 502。上游数据结构不符合 AI 服务需要的工具结果模型。

## 练习 3：解释 `base_url`

问题：

```text
如果 base_url 是 http://127.0.0.1:8001，代码执行 client.get("/orders/A1001")，最终请求地址是什么？
```

### 练习 3 参考答案

最终请求地址是：

```text
http://127.0.0.1:8001/orders/A1001
```

`base_url` 提供服务基础地址，`/orders/A1001` 是具体接口路径。

## 练习 4：为什么要过滤 `customer_id`

问题：

```text
Java mock 服务返回了 customer_id，为什么 QueryOrderResult 里不返回它？
```

### 练习 4 参考答案

因为上游服务返回的字段不一定都适合暴露给 AI 工具结果。`customer_id` 对当前订单状态回答不是必需字段，也可能属于内部业务标识。工具层应该只暴露模型需要的、安全的、稳定的字段，避免把内部字段或敏感字段放进模型上下文。

## 练习 5：为什么测试不依赖真实 8001

问题：

```text
为什么 JavaOrderClient 的单元测试使用 httpx.MockTransport，而不是要求你先启动 java-mock-service？
```

### 练习 5 参考答案

因为单元测试应该稳定、快速、可重复。依赖真实 8001 服务会让测试受端口、进程、网络和外部服务状态影响。`MockTransport` 可以直接模拟 HTTP 响应，让测试专注验证 `JavaOrderClient` 对 200、404、500、timeout、非法 JSON 等情况的处理逻辑。

## 自测题

### 1. 什么是跨服务 HTTP 调用？

参考答案：

```text
一个服务通过 HTTP 请求调用另一个服务提供的 API，获取数据或触发业务动作，这就叫跨服务 HTTP 调用。
```

### 2. 本节里谁是调用方，谁是被调用方？

参考答案：

```text
ai-service 是调用方，java-mock-service 是被调用方。
```

### 3. 为什么要单独写 `JavaOrderClient`？

参考答案：

```text
因为调用 Java 订单 API 的地址、超时、网络异常、状态码映射和 JSON 解析都属于外部服务客户端职责。把它们放进 JavaOrderClient，可以让 router 和工具函数更清晰，也让测试更容易。
```

### 4. 为什么调用 Java mock 服务要设置 timeout？

参考答案：

```text
因为外部服务可能卡住、网络可能异常。如果没有 timeout，ai-service 会一直等待，占用请求处理资源，最终拖慢甚至拖垮自己。
```

### 5. Java mock 返回 500 时，为什么 ai-service 对外返回 502？

参考答案：

```text
从 Java mock 的视角看，是它自己内部错误，所以它返回 500。从 ai-service 的视角看，是依赖的上游服务失败，不是 ai-service 自己的内部逻辑崩溃，所以对外更适合映射成 502。
```

### 6. 为什么 Java API 返回结果还要用 Pydantic 校验？

参考答案：

```text
因为跨服务返回的数据属于外部输入。即使服务是自己写的，也可能因为升级、异常、网关、字段变化导致返回结构不符合预期。Pydantic 校验可以保护 AI 服务内部逻辑和对外响应结构稳定。
```

### 7. DTO 映射解决什么问题？

参考答案：

```text
DTO 映射把上游服务返回的数据结构转换成当前服务认可的数据结构，同时可以过滤不该暴露的字段、补充 source 等字段，并隔离上游字段变化对当前服务的影响。
```

### 8. `httpx.MockTransport` 的作用是什么？

参考答案：

```text
它在测试中模拟 HTTP 传输层响应，让 JavaOrderClient 测试不需要真的发网络请求，也不需要真的启动 java-mock-service。
```

## 本节小结

这一节完成了一个关键转变：

```text
本地 fake 数据
-> 跨服务 HTTP 调用
```

现在 `ai-service` 的 `/tools/query-order` 已经开始具备真实项目形态：

```text
工具参数校验
工具权限守卫
幂等性保护
HTTP 调用 Java mock 服务
上游错误映射
字段映射
Pydantic 工具结果校验
统一错误响应
自动化测试
```

你现在要记住的主线是：

```text
模型只提出工具调用意图。
后端决定能不能执行。
AI 服务通过受控客户端调用业务服务。
业务服务提供真实业务数据。
AI 服务只暴露安全、稳定、必要的工具结果。
```

下一节继续学习：

```text
让模型决定是否调用工具。
```

也就是从现在的“我们手动调用 `/tools/query-order`”进一步走向：

```text
用户问订单问题
-> 模型判断需要 query_order
-> 后端校验并执行工具
-> 工具结果再进入模型总结
```

## 资料来源

- [HTTPX Quickstart](https://www.python-httpx.org/quickstart/)
- [HTTPX Timeouts](https://www.python-httpx.org/advanced/timeouts/)
- [HTTPX Exceptions](https://www.python-httpx.org/exceptions/)
- [HTTPX Transports and MockTransport](https://www.python-httpx.org/advanced/transports/)
- [FastAPI Path Parameters](https://fastapi.tiangolo.com/tutorial/path-params/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [FastAPI Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)
