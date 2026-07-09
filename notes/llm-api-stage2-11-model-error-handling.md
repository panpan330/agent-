# 阶段 2 第 11 节：模型调用错误处理

## 1. 这一节学什么

前面几节我们已经处理了几个具体问题：

```text
没有 API key -> LLM_API_KEY_MISSING
模型超时 -> LLM_TIMEOUT
模型限流 -> LLM_RATE_LIMITED
模型返回空内容 -> LLM_EMPTY_RESPONSE
模型返回结构异常 -> LLM_BAD_RESPONSE
其他模型调用失败 -> LLM_CALL_FAILED
```

这一节把模型调用错误处理系统化。

你要学会：

```text
OpenAI SDK 常见异常类型有哪些
APIConnectionError 和 APIStatusError 的区别
400 / 401 / 403 / 404 / 422 / 429 / 5xx 分别表示什么
为什么不能把 SDK 原始异常直接返回给前端
为什么要映射成项目自己的错误码
为什么多数上游模型错误对外用 502
怎么集中维护错误映射函数
怎么用 fake error 测试错误分支
```

## 2. 为什么模型错误处理很重要

真实 AI 服务不是只要能调通模型就结束。

模型调用可能失败：

```text
网络连不上
API key 错
没有模型权限
模型名写错
请求参数不合法
请求太频繁
模型服务超时
模型服务内部错误
模型返回格式不符合预期
```

如果这些都只返回：

```text
模型调用失败
```

你排查时会很痛苦。

用户也不知道是：

```text
稍后重试
联系管理员
减少请求频率
还是服务端配置错了
```

所以要做清晰错误映射。

## 3. 三层错误结构

当前项目里有三层错误：

```text
OpenAI SDK 原始异常
    -> 项目 AppException
        -> HTTP JSON 错误响应
```

例如：

```text
openai.AuthenticationError
    -> AppException(code="LLM_AUTHENTICATION_FAILED", status_code=502)
        -> {"code": "LLM_AUTHENTICATION_FAILED", "message": "...", "trace_id": "..."}
```

这三层不要混在一起。

## 4. 为什么不能直接返回 SDK 原始异常

错误做法：

```json
{
  "error": "openai.AuthenticationError: Error code: 401..."
}
```

问题：

```text
暴露内部 SDK 细节
可能包含服务商原始错误信息
可能包含请求 ID、组织信息、模型名等内部信息
用户看不懂
前端不好统一处理
不同服务商错误格式不同
```

正确做法：

```json
{
  "code": "LLM_AUTHENTICATION_FAILED",
  "message": "模型服务认证失败，请检查服务端 API key 配置。",
  "trace_id": "..."
}
```

内部细节写日志。

对外响应保持统一。

## 5. OpenAI SDK 的错误大类

OpenAI Python SDK 官方文档说明：

```text
无法连接 API 时，会抛 APIConnectionError 的子类。
API 返回非成功状态码时，会抛 APIStatusError 的子类。
所有错误都继承自 APIError。
```

你可以先记住两大类：

```text
连接类错误：请求没能正常连到 API
状态码错误：API 返回了 4xx 或 5xx
```

## 6. APIConnectionError 是什么

`APIConnectionError` 表示：

```text
客户端没能正常连接到模型 API。
```

可能原因：

```text
网络断开
DNS 问题
代理问题
TLS/证书问题
服务商地址不可达
连接被中断
```

当前项目映射成：

```text
LLM_CONNECTION_ERROR
```

HTTP 状态码：

```text
502
```

因为这是后端调用上游模型服务失败。

## 7. APITimeoutError 是特殊连接错误

`APITimeoutError` 是 `APIConnectionError` 的子类。

它表示：

```text
请求超过了 timeout 设置的等待时间。
```

虽然它属于连接类错误，但我们已经在上一节单独处理：

```text
LLM_TIMEOUT
504
```

为什么单独处理？

因为超时对用户和开发者都很重要。

它不是普通连接失败。

## 8. APIStatusError 是什么

`APIStatusError` 表示：

```text
模型 API 返回了非 2xx 状态码。
```

例如：

```text
400
401
403
404
422
429
500
```

SDK 会按状态码抛出更具体的子类。

## 9. 常见状态码和 SDK 错误类型

OpenAI SDK 文档列出的对应关系包括：

| HTTP 状态码 | SDK 错误类型 |
| --- | --- |
| 400 | `BadRequestError` |
| 401 | `AuthenticationError` |
| 403 | `PermissionDeniedError` |
| 404 | `NotFoundError` |
| 422 | `UnprocessableEntityError` |
| 429 | `RateLimitError` |
| >=500 | `InternalServerError` |
| N/A | `APIConnectionError` |

这一节就是把这些 SDK 错误类型映射到项目错误码。

## 10. 为什么项目不直接复用 HTTP 状态码

模型服务返回 401，并不代表访问我们 `/chat` 的用户没登录。

它通常代表：

```text
我们的后端调用模型服务时认证失败。
```

所以不能直接把上游 401 原样返回给前端。

否则前端可能误以为：

```text
当前用户登录失效。
```

实际上可能是：

```text
服务端 .env 里的 LLM_API_KEY 错了。
```

所以项目要定义自己的错误码。

## 11. 为什么多数上游错误用 502

当前链路是：

```text
浏览器或客户端
    -> ai-service
        -> 模型服务商
```

当模型服务商出错时，`ai-service` 像一个调用上游服务的网关。

所以多数上游模型错误对客户端返回：

```text
502 Bad Gateway
```

这表示：

```text
你的请求到了 ai-service，但 ai-service 调上游模型服务失败。
```

例外：

```text
限流 -> 429
超时 -> 504
```

## 12. 当前项目新增的映射函数

文件：

```text
projects/ai-service/app/services/llm_service.py
```

新增：

```python
def map_openai_error_to_app_exception(exc: Exception) -> AppException:
    ...
```

它负责：

```text
OpenAI SDK 异常 -> AppException
```

这样 `generate_reply()` 不用堆一大串业务映射。

## 13. 为什么要集中映射

如果直接在 `generate_reply()` 里写很多：

```python
except AuthenticationError:
    ...
except PermissionDeniedError:
    ...
except NotFoundError:
    ...
```

函数会越来越长。

后面新增：

```text
embedding 错误
streaming 错误
tool calling 错误
结构化输出错误
```

会更乱。

集中成映射函数的好处：

```text
错误码统一管理
测试更容易写
后续扩展更清晰
generate_reply 保持主流程清楚
```

## 14. 当前映射表

当前项目映射：

| SDK 错误 | 项目错误码 | HTTP 状态码 |
| --- | --- | --- |
| `RateLimitError` | `LLM_RATE_LIMITED` | 429 |
| `APITimeoutError` | `LLM_TIMEOUT` | 504 |
| `AuthenticationError` | `LLM_AUTHENTICATION_FAILED` | 502 |
| `PermissionDeniedError` | `LLM_PERMISSION_DENIED` | 502 |
| `NotFoundError` | `LLM_RESOURCE_NOT_FOUND` | 502 |
| `BadRequestError` | `LLM_BAD_REQUEST` | 502 |
| `UnprocessableEntityError` | `LLM_BAD_REQUEST` | 502 |
| `InternalServerError` | `LLM_PROVIDER_ERROR` | 502 |
| `APIConnectionError` | `LLM_CONNECTION_ERROR` | 502 |
| 其他 `APIStatusError` | `LLM_PROVIDER_STATUS_ERROR` | 502 |
| 其他未知异常 | `LLM_CALL_FAILED` | 502 |

## 15. 为什么 RateLimitError 放在前面

`RateLimitError` 也是 `APIStatusError` 的子类。

如果先判断：

```python
isinstance(exc, APIStatusError)
```

那 429 会被通用状态错误吃掉。

所以更具体的类型要先判断：

```python
RateLimitError
APITimeoutError
AuthenticationError
...
APIStatusError
Exception
```

顺序很重要。

## 16. 为什么 APITimeoutError 要放在 APIConnectionError 前面

`APITimeoutError` 是 `APIConnectionError` 的子类。

如果先判断：

```python
isinstance(exc, APIConnectionError)
```

timeout 会被映射成：

```text
LLM_CONNECTION_ERROR
```

而不是：

```text
LLM_TIMEOUT
```

所以 timeout 要放在连接错误前面。

## 17. AuthenticationError 怎么处理

`AuthenticationError` 通常对应 401。

可能原因：

```text
API key 错了
API key 被撤销
API key 格式不对
环境变量读错了
用了不属于当前服务商的 key
```

当前项目映射：

```text
LLM_AUTHENTICATION_FAILED
502
```

用户文案：

```text
模型服务认证失败，请检查服务端 API key 配置。
```

注意：

```text
不要把真实 key 打到日志或响应里。
```

## 18. PermissionDeniedError 怎么处理

`PermissionDeniedError` 通常对应 403。

可能原因：

```text
账号没有模型权限
模型没有开通
项目没有权限
组织或工作空间不对
资源访问被拒绝
```

当前项目映射：

```text
LLM_PERMISSION_DENIED
502
```

用户文案：

```text
模型服务拒绝访问，请检查服务端模型权限配置。
```

## 19. NotFoundError 怎么处理

`NotFoundError` 通常对应 404。

可能原因：

```text
模型名写错
base_url 写错
接口路径不对
资源 ID 不存在
工作空间或地域不匹配
```

当前项目映射：

```text
LLM_RESOURCE_NOT_FOUND
502
```

用户文案：

```text
模型服务资源不存在，请检查模型名或接口地址配置。
```

## 20. BadRequestError 怎么处理

`BadRequestError` 通常对应 400。

可能原因：

```text
messages 格式不对
参数名写错
模型不支持某个参数
传了非法字段
输入超出服务商限制
```

当前项目映射：

```text
LLM_BAD_REQUEST
502
```

为什么不是 400？

因为用户调用 `/chat` 的请求体可能是合法的。

真正错误在：

```text
ai-service 发给模型服务商的请求参数。
```

这是后端集成问题，不应该误导前端用户。

## 21. UnprocessableEntityError 怎么处理

`UnprocessableEntityError` 通常对应 422。

它表示：

```text
请求格式可能能解析，但内容无法处理。
```

当前项目也映射成：

```text
LLM_BAD_REQUEST
502
```

因为它仍然属于：

```text
后端调用上游模型时的请求内容问题。
```

## 22. InternalServerError 怎么处理

`InternalServerError` 对应上游 5xx。

可能原因：

```text
模型服务商临时异常
服务商内部错误
服务商服务拥堵
兼容接口临时故障
```

当前项目映射：

```text
LLM_PROVIDER_ERROR
502
```

用户文案：

```text
模型服务暂时异常，请稍后重试。
```

## 23. APIConnectionError 怎么处理

`APIConnectionError` 表示连接失败。

当前项目映射：

```text
LLM_CONNECTION_ERROR
502
```

用户文案：

```text
无法连接模型服务，请稍后重试。
```

排查方向：

```text
网络
代理
DNS
base_url
服务商可用性
```

## 24. APIStatusError 兜底

如果出现一个没有专门处理的 `APIStatusError`，项目映射成：

```text
LLM_PROVIDER_STATUS_ERROR
502
```

这是兜底。

以后如果发现某类错误很常见，再单独拆出更明确的错误码。

## 25. 未知异常兜底

如果不是 OpenAI SDK 异常，也不是项目自己的 `AppException`，就映射成：

```text
LLM_CALL_FAILED
502
```

例如：

```text
Fake client 抛 RuntimeError
SDK 返回对象异常
第三方库抛未知错误
```

兜底的意义是：

```text
不要让内部异常直接裸奔到前端。
```

## 26. generate_reply 现在更清楚

现在 `generate_reply()` 的异常处理变成：

```python
except AppException:
    raise
except Exception as exc:
    app_exception = map_openai_error_to_app_exception(exc)
    logger.warning(...)
    raise app_exception from exc
```

它的主流程更干净：

```text
构造 messages
调用模型
解析回复
```

错误映射交给独立函数。

## 27. 为什么 AppException 要直接 raise

`AppException` 是项目内部已经整理好的业务异常。

例如：

```text
LLM_EMPTY_RESPONSE
LLM_BAD_RESPONSE
```

如果再次进入 OpenAI 错误映射，会很奇怪。

所以：

```python
except AppException:
    raise
```

表示：

```text
项目异常已经是最终形态，不要再包装。
```

## 28. 日志怎么记录

当前日志记录：

```text
llm_chat_failed code=... provider=... model=... status_code=...
```

并带上异常堆栈：

```python
exc_info=True
```

这样开发者可以排查。

但日志里不记录：

```text
API key
用户完整问题
history 原文
```

这继续遵守敏感信息保护原则。

## 29. 测试策略

这一节新增了两类测试：

```text
映射函数测试
service 调用测试
```

映射函数测试负责：

```text
传入 SDK 错误
检查输出 AppException 的 code 和 status_code
```

service 调用测试负责：

```text
fake client 抛 SDK 错误
检查 generate_reply 是否抛出正确 AppException
```

## 30. 为什么不真实制造这些错误

错误做法：

```text
故意写错真实 API key
故意写错真实模型名
故意疯狂请求撞限流
故意断网
```

这些都不适合作为自动化测试。

原因：

```text
慢
不稳定
依赖外部网络
可能产生费用
可能污染真实账号状态
```

正确做法：

```text
构造 SDK 异常对象
让 fake client 抛出它
```

## 31. 如何构造状态码错误

测试里用：

```python
def make_status_error(
    error_class: type[APIStatusError],
    status_code: int,
) -> APIStatusError:
    request = httpx.Request("POST", "https://example.com/chat/completions")
    response = httpx.Response(
        status_code=status_code,
        request=request,
        json={"error": {"message": "provider error"}},
    )
    return error_class(
        "provider error",
        response=response,
        body={"error": {"message": "provider error"}},
    )
```

这不会发送真实请求。

只是构造一个带状态码的假响应对象。

## 32. 为什么测试映射函数

映射函数是纯逻辑。

它适合单独测试。

例如：

```python
app_exception = map_openai_error_to_app_exception(error)

assert app_exception.code == expected_code
assert app_exception.status_code == expected_status_code
```

这样可以快速覆盖很多错误类型。

## 33. 为什么还要测试 service

只测试映射函数还不够。

还要确认：

```text
generate_reply 真正调用模型时，
如果 SDK 抛错，
会经过映射函数，
最终抛出 AppException。
```

所以测试里让 fake client 抛：

```text
AuthenticationError
```

然后断言：

```text
LLM_AUTHENTICATION_FAILED
```

## 34. 当前错误码对前端有什么价值

前端可以根据 `code` 做处理。

例如：

```text
LLM_RATE_LIMITED -> 提示稍后再试
LLM_TIMEOUT -> 提示请求超时，可重试
LLM_AUTHENTICATION_FAILED -> 提示服务暂不可用，并提醒管理员
LLM_PERMISSION_DENIED -> 提示服务暂不可用
LLM_RESOURCE_NOT_FOUND -> 提示服务配置异常
```

前端不需要知道：

```text
OpenAI SDK 的具体类名。
```

## 35. 当前错误码对后端有什么价值

后端排查时可以通过：

```text
trace_id
code
provider
model
status_code
```

快速判断问题方向。

例如：

```text
LLM_RESOURCE_NOT_FOUND -> 先查模型名和 base_url
LLM_AUTHENTICATION_FAILED -> 先查 API key
LLM_PERMISSION_DENIED -> 先查模型权限或工作空间
LLM_CONNECTION_ERROR -> 先查网络和代理
LLM_PROVIDER_ERROR -> 先查服务商状态
```

## 36. 和统一异常处理的关系

`LLMChatService` 只负责抛：

```python
AppException(...)
```

最终 JSON 响应仍然由：

```text
app/core/exception_handlers.py
```

统一生成。

所以格式仍然是：

```json
{
  "code": "...",
  "message": "...",
  "trace_id": "..."
}
```

这就是阶段 1 的统一异常处理在阶段 2 的复用。

## 37. 常见错误 1：把上游 401 原样返回

错误：

```text
模型服务返回 401，/chat 也返回 401。
```

问题：

```text
前端可能误以为用户登录失效。
```

更合适：

```text
返回 LLM_AUTHENTICATION_FAILED，HTTP 502。
```

表示：

```text
后端调用上游模型服务认证失败。
```

## 38. 常见错误 2：所有异常都返回 500

错误：

```text
无论限流、超时、认证失败、网络失败，都返回 INTERNAL_SERVER_ERROR。
```

问题：

```text
排查困难
前端无法区分
日志统计没有意义
用户体验差
```

更合适：

```text
给常见错误设计稳定 code。
```

## 39. 常见错误 3：错误码太依赖服务商

错误：

```text
直接把 openai.AuthenticationError 作为 code 返回给前端。
```

问题：

```text
以后换服务商，前端错误码会变。
```

更合适：

```text
项目定义自己的稳定错误码，比如 LLM_AUTHENTICATION_FAILED。
```

## 40. 常见错误 4：日志打印用户原文

错误：

```text
模型调用失败时把完整 prompt 和 history 写进日志。
```

问题：

```text
可能泄露隐私、密钥、内部资料。
```

更合适：

```text
日志记录 provider、model、code、trace_id、status_code。
必要时另做脱敏后的调试日志。
```

## 41. 常见错误 5：没有兜底

错误：

```text
只处理几个已知异常，没有兜底。
```

问题：

```text
未知异常可能直接冒泡成内部错误。
```

更合适：

```text
最后统一映射成 LLM_CALL_FAILED。
```

## 42. 本节练习

### 练习 1

题目：

模型调用错误处理为什么要分三层？

参考答案：

因为 SDK 原始异常适合开发者排查，不适合直接返回给前端。

项目先把 SDK 异常映射成自己的 `AppException`，再由统一异常处理器转换成稳定 JSON 响应。

### 练习 2

题目：

`APIConnectionError` 和 `APIStatusError` 的区别是什么？

参考答案：

`APIConnectionError` 表示连接 API 失败，例如网络、DNS、代理、超时等问题。

`APIStatusError` 表示 API 返回了非成功 HTTP 状态码，例如 400、401、403、429、500。

### 练习 3

题目：

为什么模型服务返回 401 时，不应该直接让 `/chat` 返回 401？

参考答案：

因为这个 401 通常是后端调用模型服务时认证失败，不是当前用户访问 `/chat` 未登录。

直接返回 401 会误导前端和用户。

### 练习 4

题目：

当前项目把 `AuthenticationError` 映射成什么？

参考答案：

映射成：

```text
LLM_AUTHENTICATION_FAILED
HTTP 502
```

### 练习 5

题目：

当前项目把 `NotFoundError` 映射成什么？

参考答案：

映射成：

```text
LLM_RESOURCE_NOT_FOUND
HTTP 502
```

常见排查方向是模型名、base_url、接口路径或资源 ID。

### 练习 6

题目：

为什么 `RateLimitError` 要在 `APIStatusError` 前面判断？

参考答案：

因为 `RateLimitError` 是 `APIStatusError` 的子类。

如果先判断 `APIStatusError`，429 限流错误会被通用状态错误分支处理，无法映射成 `LLM_RATE_LIMITED`。

### 练习 7

题目：

为什么多数上游模型错误返回 502？

参考答案：

因为客户端请求到达了 `ai-service`，但 `ai-service` 调用上游模型服务失败。

这类场景更像网关调用上游失败，所以使用 502。

### 练习 8

题目：

为什么不能把完整 prompt 和 history 写进错误日志？

参考答案：

因为 prompt 和 history 可能包含用户隐私、内部资料、账号信息或密钥。

日志应该只记录排查必要信息，并避免敏感内容。

### 练习 9

题目：

为什么要单独测试 `map_openai_error_to_app_exception`？

参考答案：

因为它是错误映射的核心纯逻辑。

单独测试可以快速覆盖多种 SDK 错误，确保每种错误都映射到正确的项目错误码和状态码。

### 练习 10

题目：

如果出现没有专门处理的 SDK 状态码错误，当前项目会映射成什么？

参考答案：

会映射成：

```text
LLM_PROVIDER_STATUS_ERROR
HTTP 502
```

## 43. 本节自测

### 自测 1

题目：

所有 OpenAI SDK 错误都继承自哪个大类？

参考答案：

官方文档说明所有错误都继承自：

```text
openai.APIError
```

### 自测 2

题目：

400 对应哪个 SDK 错误类型？

参考答案：

```text
BadRequestError
```

### 自测 3

题目：

403 对应哪个 SDK 错误类型？

参考答案：

```text
PermissionDeniedError
```

### 自测 4

题目：

429 对应哪个 SDK 错误类型？

参考答案：

```text
RateLimitError
```

### 自测 5

题目：

上游 5xx 对应哪个 SDK 错误类型？

参考答案：

```text
InternalServerError
```

### 自测 6

题目：

当前项目把连接失败映射成什么？

参考答案：

```text
LLM_CONNECTION_ERROR
HTTP 502
```

### 自测 7

题目：

当前项目把模型服务内部错误映射成什么？

参考答案：

```text
LLM_PROVIDER_ERROR
HTTP 502
```

### 自测 8

题目：

`AppException` 为什么要直接 `raise`？

参考答案：

因为 `AppException` 已经是项目整理好的统一业务异常，不需要再次映射。

### 自测 9

题目：

前端应该依赖 OpenAI SDK 类名还是项目错误码？

参考答案：

应该依赖项目错误码，例如 `LLM_TIMEOUT`、`LLM_RATE_LIMITED`、`LLM_AUTHENTICATION_FAILED`。

SDK 类名属于后端内部实现细节。

### 自测 10

题目：

下一节学习什么？

参考答案：

下一节学习模型调用日志：模型名、耗时、trace_id、token。

## 44. 本节小结

这一节完成了：

```text
理解 OpenAI SDK 错误层级
理解 APIConnectionError 和 APIStatusError
理解 400/401/403/404/422/429/5xx 对应错误类型
新增 map_openai_error_to_app_exception
把常见 SDK 错误映射成项目稳定错误码
保留 LLM_TIMEOUT 和 LLM_RATE_LIMITED 的特殊处理语义
补充映射函数测试
补充 service 错误处理测试
```

现在 `/chat` 的错误处理已经更像真实工程：

```text
配置缺失
超时
限流
认证失败
权限不足
资源不存在
请求参数错误
连接失败
服务商异常
未知失败
```

下一节进入：

```text
模型调用日志：模型名、耗时、trace_id、token
```

## 45. 参考资料

- [OpenAI Python API library：Handling errors](https://developers.openai.com/api/reference/python#handling-errors)
- [OpenAI Error codes](https://developers.openai.com/api/docs/guides/error-codes)
- [MDN：502 Bad Gateway](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/502)
- [MDN：504 Gateway Timeout](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/504)
