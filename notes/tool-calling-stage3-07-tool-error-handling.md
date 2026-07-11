# 阶段 3 第 7 节：工具调用错误处理：超时、404、500

## 本节目标

前面我们已经完成了：

```text
query_order
-> 工具参数 QueryOrderArgs 校验
-> fake 订单数据查询
-> 工具结果 QueryOrderResult 校验
```

这一节继续补齐一个非常关键的能力：

```text
工具调用失败时，后端应该怎么处理？
```

真实项目里，工具不是永远成功的。

以后 `query_order` 可能会调用 Java 订单服务：

```text
Python AI 服务 -> Java 订单服务 -> 数据库 / 第三方物流系统
```

这个链路里可能出现：

- 订单不存在。
- Java 服务返回 500。
- Java 服务超时。
- 网络连接失败。
- 返回数据格式不符合约定。
- 出现未知异常。

本节要学会：

- 区分请求参数错误、业务资源不存在、上游服务错误、工具超时。
- 为什么底层异常不能直接暴露给用户。
- 为什么要把底层异常转换成统一 `AppException`。
- 为什么上游 500 对当前 AI 服务来说更适合映射成 502。
- 为什么 timeout 更适合映射成 504。
- 为什么 404 不能被兜底错误吞掉。
- 怎么测试工具错误处理。

## 本节新增和修改了什么

核心代码文件：

```text
projects/ai-service/app/tools/fake_order_tool.py
projects/ai-service/tests/test_fake_order_tool.py
projects/ai-service/tests/test_tools_api.py
```

主要新增：

| 内容 | 作用 |
| --- | --- |
| `FakeOrderServiceTimeoutError` | 模拟上游订单服务超时 |
| `FakeOrderServiceError` | 模拟上游订单服务 500 类错误 |
| `fetch_fake_order_raw_result(...)` | 模拟从上游订单服务获取原始结果 |
| `map_query_order_error(...)` | 把底层异常映射成项目统一 `AppException` |
| `A_TIMEOUT` | 测试用订单号，模拟 timeout |
| `A500` | 测试用订单号，模拟上游 500 |
| `TOOL_TIMEOUT` | 对外统一的工具超时错误码 |
| `TOOL_UPSTREAM_ERROR` | 对外统一的上游工具服务错误码 |
| `TOOL_CALL_FAILED` | 对外统一的未知工具调用失败错误码 |

## 为什么要专门学错误处理

Tool Calling 不是只要能调用工具就行。

真正工程化的工具调用必须回答：

```text
工具失败了怎么办？
```

如果没有错误处理，用户可能看到：

```text
Python traceback
Java 500 原始错误
数据库异常
第三方接口错误页
NoneType has no attribute ...
```

这有几个问题：

- 用户看不懂。
- 可能泄漏内部实现。
- 可能泄漏业务数据。
- 前端不好统一处理。
- 日志、trace_id、监控难以串起来。
- 模型可能把内部错误内容总结给用户。

所以我们要做一层转换：

```text
底层异常 -> 项目统一错误 -> 安全的 API 响应
```

## 底层异常和项目统一异常

这一节有两类异常：

```text
底层异常
项目统一异常
```

### 底层异常

底层异常是某个具体实现产生的异常。

比如：

```python
class FakeOrderServiceTimeoutError(TimeoutError):
    """Simulates a timeout from an upstream order service."""
```

```python
class FakeOrderServiceError(RuntimeError):
    """Simulates a 500-style error from an upstream order service."""
```

它们模拟以后真实 Java API 可能出现的问题：

```text
请求超时
服务内部错误
```

底层异常适合在内部代码里表达真实原因。

但不适合直接返回给用户。

### 项目统一异常

项目统一异常是我们自己设计的：

```text
AppException
```

它包含：

```text
code
message
status_code
details
```

比如：

```python
AppException(
    code="TOOL_TIMEOUT",
    message="订单查询工具调用超时，请稍后重试。",
    status_code=504,
)
```

它适合被统一异常处理器转换成 API 响应。

## 当前错误分类

这一节之后，`query_order` 相关错误可以这样看：

| 场景 | 示例 | 错误码 | HTTP 状态码 | 含义 |
| --- | --- | --- | --- | --- |
| 请求参数缺失 | `{}` | `VALIDATION_ERROR` | 422 | 客户端请求体不合法 |
| 请求参数格式错误 | `{"order_id":"A 1001"}` | `VALIDATION_ERROR` | 422 | `order_id` 格式不符合规则 |
| 订单不存在 | `{"order_id":"A9999"}` | `ORDER_NOT_FOUND` | 404 | 参数合法，但业务资源不存在 |
| 工具超时 | `{"order_id":"A_TIMEOUT"}` | `TOOL_TIMEOUT` | 504 | 上游订单服务没有及时响应 |
| 上游 500 | `{"order_id":"A500"}` | `TOOL_UPSTREAM_ERROR` | 502 | 上游订单服务内部错误 |
| 工具结果格式坏了 | 状态值未知、缺字段 | `TOOL_RESULT_VALIDATION_FAILED` | 502 | 上游返回数据不符合约定 |
| 未知工具异常 | 未分类异常 | `TOOL_CALL_FAILED` | 502 | 工具调用出现未知失败 |

## 为什么 422、404、502、504 要分清楚

### 422：请求参数错误

422 表示：

```text
请求体本身不符合接口要求。
```

比如：

```json
{}
```

缺少 `order_id`。

或者：

```json
{
  "order_id": "A 1001"
}
```

中间有空格，不符合 `QueryOrderArgs` 的规则。

这类错误是：

```text
请求进工具之前就失败了。
```

### 404：业务资源不存在

404 表示：

```text
请求格式正确，但要查的业务资源不存在。
```

比如：

```json
{
  "order_id": "A9999"
}
```

`A9999` 的格式合法。

但 fake 数据里没有这个订单。

所以这是：

```text
业务资源不存在。
```

不是参数格式错误。

### 502：上游服务或工具结果异常

502 在这里表示：

```text
当前 Python AI 服务作为调用方，依赖的上游工具或业务服务返回了不可用结果。
```

比如 Java 订单服务内部 500。

从 Java 服务角度看，它是 500。

但从 Python AI 服务对外看，更准确是：

```text
我的上游依赖坏了。
```

所以对用户返回：

```text
TOOL_UPSTREAM_ERROR
```

状态码用：

```text
502
```

### 504：上游超时

504 表示：

```text
当前服务等待上游服务响应，但上游没有及时返回。
```

比如：

```json
{
  "order_id": "A_TIMEOUT"
}
```

在 fake tool 里它会触发：

```text
FakeOrderServiceTimeoutError
```

然后映射成：

```text
TOOL_TIMEOUT
```

状态码：

```text
504
```

## 这一节的核心代码

### 1. 模拟底层订单服务

文件：

```text
projects/ai-service/app/tools/fake_order_tool.py
```

新增：

```python
def fetch_fake_order_raw_result(order_id: str) -> dict[str, object] | None:
    if order_id == "A_TIMEOUT":
        raise FakeOrderServiceTimeoutError("fake order service timed out")
    if order_id == "A500":
        raise FakeOrderServiceError("fake order service returned 500")
    return _FAKE_ORDER_STORE.get(order_id)
```

它模拟真实 Java API：

- `A1001`：正常返回订单。
- `A9999`：找不到订单，返回 `None`。
- `A_TIMEOUT`：模拟超时。
- `A500`：模拟上游服务 500。

### 2. 映射底层异常

新增：

```python
def map_query_order_error(exc: Exception) -> AppException:
    if isinstance(exc, FakeOrderServiceTimeoutError):
        return AppException(
            code="TOOL_TIMEOUT",
            message="订单查询工具调用超时，请稍后重试。",
            status_code=504,
        )
    if isinstance(exc, FakeOrderServiceError):
        return AppException(
            code="TOOL_UPSTREAM_ERROR",
            message="订单查询服务暂时不可用，请稍后重试。",
            status_code=502,
        )
    return AppException(
        code="TOOL_CALL_FAILED",
        message="工具调用失败，请稍后重试。",
        status_code=502,
    )
```

这就是错误处理的关键：

```text
底层具体异常
-> 对外统一错误码
-> 安全提示语
-> 合适 HTTP 状态码
```

### 3. `query_order` 只向外抛统一异常

现在 `query_order` 是：

```python
def query_order(arguments: QueryOrderArgs) -> QueryOrderResult:
    try:
        raw_result = fetch_fake_order_raw_result(arguments.order_id)
        if raw_result is None:
            raise AppException(
                code="ORDER_NOT_FOUND",
                message="订单不存在，请确认订单号是否正确。",
                status_code=404,
            )

        return validate_query_order_result(raw_result)
    except AppException:
        raise
    except Exception as exc:
        raise map_query_order_error(exc) from exc
```

这里有一个细节：

```python
except AppException:
    raise
```

它的意思是：

```text
如果已经是项目统一异常，就原样抛出去。
```

比如：

```text
ORDER_NOT_FOUND
TOOL_RESULT_VALIDATION_FAILED
```

这些已经是我们设计好的错误，不应该再被兜底转换成：

```text
TOOL_CALL_FAILED
```

所以要先放行 `AppException`。

再处理未知异常：

```python
except Exception as exc:
    raise map_query_order_error(exc) from exc
```

## 为什么不能直接暴露底层异常

如果直接把底层异常返回给用户，可能是：

```text
fake order service returned 500
java.net.SocketTimeoutException
org.springframework.dao.QueryTimeoutException
database connection refused
NoneType object has no attribute ...
```

这些内容不适合给用户。

原因：

- 用户看不懂。
- 暴露技术栈。
- 可能暴露内部服务名。
- 可能暴露数据库、表名、字段名。
- 可能被攻击者利用。

所以对外返回：

```json
{
  "code": "TOOL_UPSTREAM_ERROR",
  "message": "订单查询服务暂时不可用，请稍后重试。",
  "trace_id": "..."
}
```

内部日志再通过 `trace_id` 去查具体原因。

## 为什么底层 500 不直接返回 500

以后 Java 服务可能返回 500。

你可能会问：

```text
Java 返回 500，Python AI 服务为什么不也返回 500？
```

因为对用户来说，请求到的是：

```text
Python AI 服务
```

Python AI 服务本身没有崩溃。

它是调用上游订单服务失败。

所以更准确的是：

```text
上游依赖错误。
```

在 HTTP 语义里，这类情况更接近：

```text
502 Bad Gateway
```

如果是等待上游服务超时，更接近：

```text
504 Gateway Timeout
```

这个区分对排查问题很有用：

```text
500：当前服务自己内部出错。
502：当前服务依赖的上游服务出错。
504：当前服务等上游服务超时。
```

## 当前接口效果

### 正常查询

请求：

```json
{
  "order_id": "A1001"
}
```

响应：

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

### 订单不存在

请求：

```json
{
  "order_id": "A9999"
}
```

响应：

```json
{
  "code": "ORDER_NOT_FOUND",
  "message": "订单不存在，请确认订单号是否正确。",
  "trace_id": "..."
}
```

状态码：

```text
404
```

### 工具超时

请求：

```json
{
  "order_id": "A_TIMEOUT"
}
```

响应：

```json
{
  "code": "TOOL_TIMEOUT",
  "message": "订单查询工具调用超时，请稍后重试。",
  "trace_id": "..."
}
```

状态码：

```text
504
```

### 上游 500

请求：

```json
{
  "order_id": "A500"
}
```

响应：

```json
{
  "code": "TOOL_UPSTREAM_ERROR",
  "message": "订单查询服务暂时不可用，请稍后重试。",
  "trace_id": "..."
}
```

状态码：

```text
502
```

## 这一节的测试

新增和扩展的测试在：

```text
projects/ai-service/tests/test_fake_order_tool.py
projects/ai-service/tests/test_tools_api.py
```

只跑相关测试：

```powershell
uv run pytest tests/test_fake_order_tool.py tests/test_tools_api.py -q
```

覆盖点：

- `A_TIMEOUT` 会触发 `FakeOrderServiceTimeoutError`。
- `A500` 会触发 `FakeOrderServiceError`。
- `query_order(A_TIMEOUT)` 会映射成 `TOOL_TIMEOUT` 和 504。
- `query_order(A500)` 会映射成 `TOOL_UPSTREAM_ERROR` 和 502。
- 未知异常会映射成 `TOOL_CALL_FAILED` 和 502。
- `ORDER_NOT_FOUND` 仍然保持 404，不会被兜底转换。
- `/tools/query-order` 会返回统一 JSON 错误响应。

## 练习 1：判断错误码

请判断下面场景应该返回什么错误码和 HTTP 状态码。

题目：

1. 请求体是 `{}`。
2. 请求体是 `{"order_id":"A 1001"}`。
3. 请求体是 `{"order_id":"A9999"}`。
4. 请求体是 `{"order_id":"A_TIMEOUT"}`。
5. 请求体是 `{"order_id":"A500"}`。
6. 工具返回结果缺少 `logistics_message`。

### 练习 1 参考答案

1. `VALIDATION_ERROR`，422。缺少请求参数。
2. `VALIDATION_ERROR`，422。`order_id` 格式不合法。
3. `ORDER_NOT_FOUND`，404。订单资源不存在。
4. `TOOL_TIMEOUT`，504。订单查询工具超时。
5. `TOOL_UPSTREAM_ERROR`，502。上游订单服务错误。
6. `TOOL_RESULT_VALIDATION_FAILED`，502。工具结果结构不符合约定。

## 练习 2：为什么 404 不能被兜底吞掉

问题：

```text
为什么 query_order 里要先 except AppException: raise？
```

### 练习 2 参考答案

因为有些错误已经是我们设计好的业务错误。

比如：

```text
ORDER_NOT_FOUND
TOOL_RESULT_VALIDATION_FAILED
```

如果不先放行 `AppException`，它们可能会被后面的通用 `except Exception` 捕获，然后错误地转换成：

```text
TOOL_CALL_FAILED
```

这样会丢失真实语义。

所以顺序必须是：

```text
先放行业务异常。
再兜底未知异常。
```

## 练习 3：为什么不直接返回底层异常

问题：

```text
为什么不能把 FakeOrderServiceError("fake order service returned 500") 直接返回给用户？
```

### 练习 3 参考答案

因为底层异常属于内部实现细节。

真实系统里，它可能包含：

```text
Java 类名
数据库错误
内部服务名
第三方接口细节
敏感业务字段
```

这些不适合暴露给用户。

对外应该返回安全、稳定、可被前端识别的错误：

```text
TOOL_UPSTREAM_ERROR
订单查询服务暂时不可用，请稍后重试。
```

内部排查靠日志和 `trace_id`。

## 练习 4：设计一个退款工具错误映射

假设以后有工具：

```text
create_refund_request
```

请设计三个错误码：

1. 退款服务超时。
2. 退款服务内部错误。
3. 未知退款工具失败。

### 练习 4 参考答案

可以设计为：

| 场景 | 错误码 | HTTP 状态码 | message |
| --- | --- | --- | --- |
| 退款服务超时 | `REFUND_TOOL_TIMEOUT` | 504 | 退款申请工具调用超时，请稍后重试。 |
| 退款服务内部错误 | `REFUND_TOOL_UPSTREAM_ERROR` | 502 | 退款申请服务暂时不可用，请稍后重试。 |
| 未知退款工具失败 | `REFUND_TOOL_CALL_FAILED` | 502 | 退款申请工具调用失败，请稍后重试。 |

真实项目里也可以统一成：

```text
TOOL_TIMEOUT
TOOL_UPSTREAM_ERROR
TOOL_CALL_FAILED
```

然后通过日志字段记录具体工具名。

## 练习 5：解释一次 `A_TIMEOUT`

请求：

```json
{
  "order_id": "A_TIMEOUT"
}
```

请解释完整流程。

### 练习 5 参考答案

流程：

```text
1. FastAPI 收到请求。
2. QueryOrderArgs 校验 order_id，通过。
3. router 调用 query_order。
4. query_order 调用 fetch_fake_order_raw_result("A_TIMEOUT")。
5. fetch_fake_order_raw_result 抛出 FakeOrderServiceTimeoutError。
6. query_order 捕获底层异常。
7. map_query_order_error 把它转换成 AppException(code="TOOL_TIMEOUT", status_code=504)。
8. 统一异常处理器把 AppException 转成 JSON。
9. API 返回 504 和 TOOL_TIMEOUT。
```

## 自测题

### 1. 工具调用错误处理的核心目的是什么？

参考答案：

```text
把底层异常转换成统一、稳定、安全的项目错误，方便前端处理、日志排查和用户理解。
```

### 2. 订单不存在为什么是 404？

参考答案：

```text
因为请求参数格式合法，但业务资源不存在。它不是请求体结构错误，也不是工具服务崩溃。
```

### 3. 上游 Java 服务 500 为什么对 Python AI 服务来说可以映射成 502？

参考答案：

```text
因为 Python AI 服务本身没有崩溃，是它依赖的上游业务服务返回了错误。对当前服务的调用方来说，这是上游依赖失败。
```

### 4. timeout 为什么用 504？

参考答案：

```text
因为当前服务等待上游工具或业务服务响应，但没有在规定时间内拿到结果。
```

### 5. 为什么底层异常 message 不适合直接返回给用户？

参考答案：

```text
底层异常可能包含技术栈、内部服务名、数据库错误、业务字段或敏感信息。对外应该返回安全、稳定的错误码和提示语。
```

### 6. `TOOL_CALL_FAILED` 的作用是什么？

参考答案：

```text
它是未知工具调用失败的兜底错误，避免未分类异常直接变成未处理异常或泄漏底层信息。
```

## 本节小结

这节的核心是：

```text
工具调用不能只处理成功路径。
失败路径也必须设计清楚。
```

当前我们已经把 `query_order` 的主要错误分清楚：

```text
参数错 -> 422 VALIDATION_ERROR
订单不存在 -> 404 ORDER_NOT_FOUND
上游 500 -> 502 TOOL_UPSTREAM_ERROR
上游超时 -> 504 TOOL_TIMEOUT
结果坏了 -> 502 TOOL_RESULT_VALIDATION_FAILED
未知异常 -> 502 TOOL_CALL_FAILED
```

这会直接服务后面的 Java mock API：

```text
现在是 fake exception。
以后是真实 httpx timeout、HTTP 404、HTTP 500。
但映射成 AppException 的思想不变。
```

下一节继续学：

```text
工具调用权限边界。
```

也就是哪些工具可以被模型请求，哪些操作必须用户确认，哪些业务动作不能让模型直接触发。

## 资料来源

- [MDN：HTTP response status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status)
- [MDN：404 Not Found](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/404)
- [MDN：504 Gateway Timeout](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/504)
- [FastAPI：Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [Python：Built-in Exceptions](https://docs.python.org/3/library/exceptions.html)
