# 阶段 2 第 9 节：timeout 超时

## 1. 这一节学什么

上一节我们让 `/chat` 支持了多轮对话：

```text
message + history
```

现在 `/chat` 已经能调用真实模型，也能带历史消息。

但还有一个非常现实的问题：

```text
如果模型服务很慢怎么办？
如果网络卡住怎么办？
如果请求一直不返回怎么办？
```

这一节学习：

```text
timeout 是什么
为什么调用外部 API 必须设置 timeout
OpenAI SDK 里的 timeout 怎么配置
当前项目的 REQUEST_TIMEOUT_SECONDS 怎么用
APITimeoutError 是什么
为什么超时要单独处理
为什么超时适合映射成 504
为什么测试不能真的等几十秒
怎么用 fake client 模拟 timeout
```

## 2. timeout 是什么

`timeout` 翻译成中文就是：

```text
超时时间
```

更工程化一点：

```text
一个操作最多允许等待多久。
```

比如：

```text
请求模型最多等 30 秒。
30 秒内返回，就继续处理。
超过 30 秒还没返回，就认为这次请求失败。
```

所以 timeout 不是让请求更快。

它是：

```text
防止请求无限等待的保护边界。
```

## 3. 为什么不能无限等

如果后端调用模型时不设置 timeout，可能出现：

```text
请求一直卡着
用户页面一直转圈
后端 worker 被占住
并发能力下降
队列越积越多
日志不好排查
前端和网关先超时
用户重复点击导致更多请求
```

AI 服务通常要调用外部模型服务。

外部服务可能因为这些原因变慢：

```text
网络不稳定
DNS 或代理问题
服务商负载高
模型请求太复杂
history 太长
输出太长
服务商短暂故障
```

所以调用外部 API 必须有 timeout。

## 4. timeout 和错误处理的关系

timeout 本身不是业务成功。

它是一种失败。

但它不是普通代码 bug。

更准确地说：

```text
我们的服务调用上游模型服务时，上游没有在规定时间内返回。
```

所以它应该被转换成清晰错误。

本项目现在返回：

```json
{
  "code": "LLM_TIMEOUT",
  "message": "模型调用超时，请稍后重试。",
  "trace_id": "..."
}
```

HTTP 状态码：

```text
504
```

## 5. 为什么是 504

`504 Gateway Timeout` 通常表示：

```text
服务器作为网关或代理调用上游服务时，上游没有及时响应。
```

我们的 `ai-service` 调模型服务时，角色很像：

```text
客户端 -> ai-service -> 模型服务
```

如果模型服务超时：

```text
ai-service 本身还活着
客户端请求格式也没错
问题出在等待上游模型服务返回
```

所以用 504 比 500 更准确。

## 6. OpenAI SDK 怎么配置 timeout

OpenAI Python SDK 官方文档说明：

```python
client = OpenAI(
    timeout=20.0,
)
```

也可以按请求覆盖：

```python
client.with_options(timeout=5.0).chat.completions.create(...)
```

官方文档还说明：

```text
超时时会抛 APITimeoutError。
```

当前项目在 client 初始化时已经配置了 timeout：

```python
client_kwargs: dict[str, object] = {
    "api_key": api_key,
    "timeout": settings.request_timeout_seconds,
}
```

也就是：

```text
REQUEST_TIMEOUT_SECONDS -> settings.request_timeout_seconds -> OpenAI(timeout=...)
```

## 7. 当前项目的 timeout 配置

`.env.example` 里有：

```text
REQUEST_TIMEOUT_SECONDS=30
```

配置类里有：

```python
request_timeout_seconds: float = Field(default=30.0, gt=0)
```

含义：

```text
默认等 30 秒。
必须大于 0。
```

为什么要 `gt=0`？

因为：

```text
timeout=0 没意义。
负数 timeout 也没意义。
```

Pydantic 会提前阻止这种错误配置。

## 8. timeout 设置太长的问题

比如设置：

```text
REQUEST_TIMEOUT_SECONDS=600
```

也就是等 10 分钟。

问题：

```text
用户体验很差
后端连接长期占用
请求堆积风险更高
前端或网关可能早就超时
问题暴露得太慢
```

对普通聊天接口来说，10 分钟通常太长。

## 9. timeout 设置太短的问题

比如设置：

```text
REQUEST_TIMEOUT_SECONDS=1
```

问题：

```text
稍微复杂一点的问题就可能超时
模型刚准备好回答就被切断
用户经常看到失败
服务稳定性看起来很差
```

所以 timeout 不是越短越好。

## 10. 初学阶段怎么选 timeout

当前项目默认：

```text
30 秒
```

这是一个学习阶段比较合理的值。

原因：

```text
不会无限等
普通问答通常够用
排错时不会等太久
后续还可以按接口类型调整
```

以后生产环境可以按场景拆分：

```text
普通 chat：20-30 秒
复杂 RAG：30-60 秒
后台批处理：更长，但不走同步 HTTP
流式输出：连接策略会不同
```

这些不是死规则，要结合实际服务和用户体验。

## 11. APITimeoutError 是什么

OpenAI Python SDK 超时时会抛：

```python
APITimeoutError
```

它是 OpenAI SDK 的异常类型。

它表示：

```text
请求超过了允许等待的时间。
```

当前项目新增：

```python
from openai import APITimeoutError
```

然后在 service 里单独捕获。

## 12. 为什么要单独捕获 timeout

之前代码里有通用异常处理：

```python
except Exception as exc:
    ...
    raise AppException(
        code="LLM_CALL_FAILED",
        message="模型调用失败，请稍后重试。",
        status_code=502,
    ) from exc
```

如果不单独捕获 timeout，超时也会变成：

```text
LLM_CALL_FAILED
```

这样问题不够清楚。

用户和开发者看不出：

```text
是超时
还是模型报错
还是网络连接失败
还是代码解析失败
```

所以本节把 timeout 单独映射成：

```text
LLM_TIMEOUT
```

## 13. 当前新增的 timeout 处理代码

文件：

```text
projects/ai-service/app/services/llm_service.py
```

新增：

```python
except APITimeoutError as exc:
    logger.warning(
        "llm_timeout provider=%s model=%s timeout_seconds=%s",
        self.settings.llm_provider,
        self.settings.llm_model,
        self.settings.request_timeout_seconds,
    )
    raise AppException(
        code="LLM_TIMEOUT",
        message="模型调用超时，请稍后重试。",
        status_code=504,
    ) from exc
```

这段代码做了三件事：

```text
捕获 OpenAI SDK 的超时异常
记录一条 warning 日志
转换成项目统一异常 AppException
```

## 14. 为什么用 logger.warning

超时不是普通成功日志。

但它也不一定是我们代码崩了。

它可能是：

```text
网络慢
模型服务慢
请求太复杂
上游临时拥堵
```

所以使用：

```python
logger.warning(...)
```

含义是：

```text
这件事需要注意，但不一定是程序崩溃。
```

而普通未知异常仍然使用：

```python
logger.exception(...)
```

因为那类异常需要完整堆栈辅助排查。

## 15. timeout 日志里记录什么

当前记录：

```text
provider
model
timeout_seconds
```

例如：

```text
llm_timeout provider=aliyun-compatible model=qwen3.7-plus timeout_seconds=30.0
```

这些信息有助于排查：

```text
哪个服务商超时
哪个模型超时
当时配置的 timeout 是多少
```

但没有记录：

```text
用户完整问题
history 原文
API key
```

因为这些可能包含敏感信息。

## 16. 异常处理顺序为什么重要

代码顺序是：

```python
except AppException:
    raise
except APITimeoutError as exc:
    ...
except Exception as exc:
    ...
```

顺序不能随便写。

如果写成：

```python
except Exception:
    ...
except APITimeoutError:
    ...
```

那么 `APITimeoutError` 会先被 `Exception` 捕获。

后面的 timeout 分支永远走不到。

所以更具体的异常要放在更通用的异常前面。

## 17. APITimeoutError 和重试

OpenAI Python SDK 文档还说明：

```text
部分错误默认会自动重试，timeout 默认也可能重试。
```

这意味着：

```text
你设置 timeout=30 秒，不一定代表整体只等 30 秒。
```

因为如果 SDK 默认重试，实际等待时间可能更长。

本节先只学：

```text
怎么设置 timeout
怎么处理 APITimeoutError
```

下一节会专门学：

```text
retry 重试和 rate limit 限流基础
```

## 18. 连接超时和读取超时

初学阶段可以先知道两个概念：

```text
连接超时：连不上对方服务器
读取超时：连上了，但对方迟迟不返回数据
```

OpenAI SDK 的 `timeout` 可以传简单数字：

```python
timeout=30.0
```

也可以使用更细粒度的 `httpx.Timeout`：

```python
timeout=httpx.Timeout(60.0, read=5.0, write=10.0, connect=2.0)
```

当前项目先用简单数字。

原因：

```text
初学阶段先把整体超时学清楚。
细粒度超时后面需要时再拆。
```

## 19. 为什么测试不能真的等超时

错误测试方式：

```text
设置 timeout=30 秒
真的等 30 秒
看它会不会超时
```

这不适合自动化测试。

因为：

```text
测试会非常慢
容易受网络影响
需要真实模型服务
可能产生费用
CI 上不稳定
```

正确做法：

```text
用 fake client 直接抛 APITimeoutError。
```

这样测试的是：

```text
我们的代码是否正确处理 timeout 异常。
```

而不是测试真实网络环境。

## 20. timeout 单元测试

文件：

```text
projects/ai-service/tests/test_llm_service.py
```

新增测试：

```python
def test_llm_chat_service_maps_timeout_errors() -> None:
    timeout_error = APITimeoutError(
        request=httpx.Request("POST", "https://example.com/chat/completions")
    )
    service = LLMChatService(
        Settings(
            llm_api_key="test-key",
            request_timeout_seconds=3,
            _env_file=None,
        ),
        client=FakeClient(FakeCompletions(error=timeout_error)),
    )

    with pytest.raises(AppException) as exc_info:
        service.generate_reply("解释 FastAPI")

    assert exc_info.value.code == "LLM_TIMEOUT"
    assert exc_info.value.status_code == 504
```

这个测试没有真实请求网络。

它只是让 fake client 模拟：

```text
SDK 抛出了 APITimeoutError。
```

然后检查项目是否转换成：

```text
LLM_TIMEOUT / 504
```

## 21. 为什么 APITimeoutError 需要 request

OpenAI SDK 的 `APITimeoutError` 构造需要：

```python
request=httpx.Request(...)
```

因为 SDK 异常通常会携带请求上下文。

测试里只需要构造一个假的 request：

```python
httpx.Request("POST", "https://example.com/chat/completions")
```

它不会真的发请求。

它只是一个请求对象。

## 22. 接口级 timeout 测试

除了 service 单元测试，还补了 `/chat` 接口测试。

测试思路：

```text
fake service 直接抛 AppException(code="LLM_TIMEOUT")
然后看 /chat 返回是否是统一错误响应
```

这样可以验证：

```text
AppException -> exception handler -> JSON response
```

接口返回应该是：

```json
{
  "code": "LLM_TIMEOUT",
  "message": "模型调用超时，请稍后重试。",
  "trace_id": "trace-timeout"
}
```

HTTP 状态码：

```text
504
```

## 23. 当前错误码对比

现在和 LLM 调用相关的错误包括：

| 错误码 | HTTP 状态码 | 含义 |
| --- | --- | --- |
| `LLM_API_KEY_MISSING` | 500 | 服务端没有配置模型 API key |
| `LLM_TIMEOUT` | 504 | 调用模型超时 |
| `LLM_BAD_RESPONSE` | 502 | 模型返回结构异常 |
| `LLM_EMPTY_RESPONSE` | 502 | 模型返回空内容 |
| `LLM_CALL_FAILED` | 502 | 其他模型调用失败 |

这样比全部返回：

```text
模型调用失败
```

更容易排查。

## 24. timeout 和 trace_id

即使模型超时，响应里也会有：

```text
trace_id
```

例如：

```json
{
  "code": "LLM_TIMEOUT",
  "message": "模型调用超时，请稍后重试。",
  "trace_id": "trace-timeout"
}
```

这很重要。

用户或前端看到错误后，可以把 `trace_id` 给后端排查。

后端日志里也会有同一个 `trace_id`。

## 25. timeout 和用户体验

用户不应该看到：

```text
APITimeoutError: Request timed out...
```

这类内部错误。

用户应该看到：

```text
模型调用超时，请稍后重试。
```

原因：

```text
内部错误不适合直接暴露给用户
异常堆栈可能包含敏感信息
统一错误文案更可控
前端也更容易处理
```

## 26. timeout 和前端

前端收到 504 后，可以做：

```text
提示用户稍后重试
允许重新发送
不要无限 loading
记录 trace_id
必要时提示换短一点的问题
```

前端不应该做：

```text
自动疯狂重试
隐藏错误
一直转圈
```

重试要有节制。

下一节会讲 retry。

## 27. timeout 和 history

上一节加入了 `history`。

history 太长可能导致：

```text
输入 token 多
模型处理慢
更容易超时
成本更高
```

所以 timeout 和 history 有关系。

当前我们已经限制：

```text
history 最多 20 条
```

以后还会学：

```text
token 预算
历史摘要
只保留最近 N 轮
```

这些都能降低超时风险。

## 28. timeout 和 max_output_tokens

项目里还有：

```text
MAX_OUTPUT_TOKENS
```

输出越长，模型生成时间可能越长。

如果允许模型生成特别长的回答：

```text
耗时更久
费用更高
更可能超时
```

当前阶段还没有真正把 `MAX_OUTPUT_TOKENS` 传给模型调用。

后面会结合模型参数一起处理。

## 29. timeout 和 streaming

以后学流式输出时，timeout 会更复杂。

非流式：

```text
等完整回答返回
```

流式：

```text
模型生成一点，服务端返回一点
```

流式场景要考虑：

```text
连接建立超时
首 token 超时
中间长时间无数据
客户端断开
```

本节先处理非流式 `/chat`。

## 30. 当前调用链中的 timeout 位置

当前链路：

```text
/chat router
  -> LLMChatService.generate_reply()
  -> client.chat.completions.create(...)
```

timeout 发生在：

```text
client.chat.completions.create(...)
```

如果超过 SDK 设置的 timeout，就抛：

```text
APITimeoutError
```

然后被转换成：

```text
AppException(code="LLM_TIMEOUT", status_code=504)
```

最后由统一异常处理器转换成 JSON。

## 31. 手动测试 timeout 的方式

学习阶段不建议为了测试 timeout 去调用真实模型硬等。

如果你想观察配置，可以先看：

```powershell
uv run python scripts\llm_compatible_smoke_test.py
```

这条命令默认不会调用模型，只会显示：

```text
provider
model
base_url_configured
```

如果你真的要调模型：

```powershell
uv run python scripts\llm_compatible_smoke_test.py --call
```

注意：

```text
--call 会请求真实模型，可能产生费用。
```

## 32. 常见错误 1：没有 timeout

错误：

```python
client = OpenAI(api_key=api_key)
```

如果完全依赖默认超时，可能不符合你的服务体验要求。

当前项目更明确：

```python
OpenAI(
    api_key=api_key,
    timeout=settings.request_timeout_seconds,
)
```

这样 timeout 可配置、可测试、可解释。

## 33. 常见错误 2：把 timeout 当成 retry

timeout 和 retry 不是一回事。

timeout：

```text
最多等多久。
```

retry：

```text
失败后要不要再试一次。
```

它们经常一起出现，但概念不同。

本节学 timeout。

下一节学 retry。

## 34. 常见错误 3：捕获 Exception 后才捕获 timeout

错误：

```python
try:
    ...
except Exception:
    ...
except APITimeoutError:
    ...
```

这会导致 `APITimeoutError` 永远进不到自己的分支。

正确：

```python
try:
    ...
except APITimeoutError:
    ...
except Exception:
    ...
```

具体异常放前面，通用异常放后面。

## 35. 常见错误 4：把 timeout 堆栈直接返回给用户

错误：

```json
{
  "error": "openai.APITimeoutError: Request timed out..."
}
```

正确：

```json
{
  "code": "LLM_TIMEOUT",
  "message": "模型调用超时，请稍后重试。",
  "trace_id": "..."
}
```

内部错误写日志。

对外返回统一错误结构。

## 36. 常见错误 5：为了测试真的等待 30 秒

错误：

```text
测试时真的等模型请求超时。
```

正确：

```text
fake client 直接抛 APITimeoutError。
```

测试应该快、稳、不依赖外部服务。

## 37. 本节练习

### 练习 1

题目：

用自己的话解释 timeout 是什么。

参考答案：

timeout 是一个操作最多允许等待的时间。

超过这个时间还没有完成，就认为这次操作失败，避免程序无限等待。

### 练习 2

题目：

为什么调用外部模型 API 必须设置 timeout？

参考答案：

因为外部 API 可能因为网络、服务商负载、请求复杂度等原因迟迟不返回。

如果没有 timeout，后端请求可能一直卡住，占用资源，导致用户体验和系统稳定性变差。

### 练习 3

题目：

当前项目用哪个配置项控制模型调用超时时间？

参考答案：

使用：

```text
REQUEST_TIMEOUT_SECONDS
```

对应代码里的：

```python
settings.request_timeout_seconds
```

### 练习 4

题目：

OpenAI Python SDK 超时时会抛什么异常？

参考答案：

会抛：

```python
APITimeoutError
```

### 练习 5

题目：

当前项目把模型调用超时映射成什么错误码和 HTTP 状态码？

参考答案：

错误码：

```text
LLM_TIMEOUT
```

HTTP 状态码：

```text
504
```

### 练习 6

题目：

为什么 timeout 适合返回 504？

参考答案：

因为 `/chat` 调用模型服务时，`ai-service` 相当于调用上游服务。

如果上游模型服务没有及时响应，使用 504 Gateway Timeout 比 500 更准确。

### 练习 7

题目：

为什么测试 timeout 时不应该真的等 30 秒？

参考答案：

因为这样测试会很慢、不稳定、依赖真实网络和模型服务，还可能产生费用。

应该用 fake client 直接抛 `APITimeoutError`。

### 练习 8

题目：

下面异常捕获顺序有什么问题？

```python
try:
    call_model()
except Exception:
    handle_general_error()
except APITimeoutError:
    handle_timeout()
```

参考答案：

`APITimeoutError` 继承自 `Exception`，会先被 `except Exception` 捕获。

所以 timeout 分支不会执行。

应该把 `except APITimeoutError` 放在 `except Exception` 前面。

### 练习 9

题目：

timeout 和 retry 的区别是什么？

参考答案：

timeout 规定一次操作最多等多久。

retry 规定失败后要不要再试一次。

它们相关，但不是同一个概念。

### 练习 10

题目：

timeout 日志为什么不记录完整用户输入？

参考答案：

因为用户输入和 history 可能包含敏感信息。

日志只记录 provider、model、timeout_seconds 这类排查必需信息，避免泄露隐私和密钥。

## 38. 本节自测

### 自测 1

题目：

timeout 是让模型更快吗？

参考答案：

不是。

timeout 是限制最多等待多久，防止无限等待。

### 自测 2

题目：

当前默认 timeout 是多少秒？

参考答案：

当前默认：

```text
30 秒
```

### 自测 3

题目：

`request_timeout_seconds` 允许是 0 吗？

参考答案：

不允许。

配置里使用了 `gt=0`，必须大于 0。

### 自测 4

题目：

timeout 后用户会看到 SDK 原始异常吗？

参考答案：

不会。

用户会看到统一错误：

```text
LLM_TIMEOUT
```

以及友好的错误消息。

### 自测 5

题目：

`LLM_TIMEOUT` 和 `LLM_CALL_FAILED` 有什么区别？

参考答案：

`LLM_TIMEOUT` 明确表示模型调用超时。

`LLM_CALL_FAILED` 表示其他模型调用失败。

### 自测 6

题目：

为什么 timeout 日志使用 warning？

参考答案：

因为超时需要关注，但不一定代表程序代码崩溃。

它可能是网络或上游服务慢。

### 自测 7

题目：

OpenAI SDK 默认可能会对 timeout 重试吗？

参考答案：

会。

官方文档说明超时请求默认可能被重试。

下一节会专门学 retry。

### 自测 8

题目：

连接超时和读取超时有什么大概区别？

参考答案：

连接超时是连不上对方服务器。

读取超时是连接已经建立，但对方迟迟不返回数据。

### 自测 9

题目：

本节新增了哪些测试？

参考答案：

新增了：

```text
LLMChatService 把 APITimeoutError 映射为 LLM_TIMEOUT
/chat 在 service 抛 LLM_TIMEOUT 时返回 504 统一错误响应
```

### 自测 10

题目：

下一节学习什么？

参考答案：

下一节学习 retry 重试和 rate limit 限流基础。

## 39. 本节小结

这一节完成了：

```text
理解 timeout 是最多等待时间
理解调用外部模型 API 必须设置 timeout
理解 REQUEST_TIMEOUT_SECONDS 的作用
理解 OpenAI SDK 的 APITimeoutError
把 APITimeoutError 映射为 LLM_TIMEOUT
使用 504 表示模型调用超时
补充 service 单元测试
补充 /chat 接口级 timeout 测试
```

现在 `/chat` 已经具备：

```text
真实模型调用
多轮 history
API key 缺失错误
模型超时错误
统一错误响应
fake 测试隔离
```

下一节进入：

```text
retry 重试和 rate limit 限流基础
```

## 40. 参考资料

- [OpenAI Python API library：Timeouts](https://developers.openai.com/api/reference/python#timeouts)
- [OpenAI Error codes：APITimeoutError](https://developers.openai.com/api/docs/guides/error-codes)
- [HTTP MDN：504 Gateway Timeout](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/504)
- [HTTPX Timeouts](https://www.python-httpx.org/advanced/timeouts/)
