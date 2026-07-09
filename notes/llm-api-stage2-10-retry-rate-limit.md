# 阶段 2 第 10 节：retry 重试和 rate limit 限流基础

## 1. 这一节学什么

上一节我们学了：

```text
timeout 超时
APITimeoutError
LLM_TIMEOUT
504 Gateway Timeout
```

这一节继续学习真实模型调用里的两个高频问题：

```text
retry 重试
rate limit 限流
```

这一节要学：

```text
retry 是什么
为什么不能无限重试
哪些错误适合重试
哪些错误不应该重试
exponential backoff 指数退避是什么
rate limit 是什么
429 是什么意思
OpenAI SDK 默认重试行为是什么
项目里怎么显式配置 max_retries
RateLimitError 怎么映射成统一错误
怎么用 fake 测试限流，不真实撞服务商限流
```

## 2. retry 是什么

`retry` 就是：

```text
一次操作失败后，再试一次或多次。
```

比如调用模型：

```text
第 1 次：网络短暂抖动，失败
等一下
第 2 次：网络恢复，成功
```

这就是 retry 的价值。

它可以提高系统对临时错误的容忍度。

## 3. retry 不是万能修复

很多初学者会以为：

```text
失败了就多试几次。
```

这不对。

有些错误重试有意义。

有些错误重试没意义。

有些错误重试反而会更糟。

例如：

```text
API key 错了，重试 100 次也不会成功。
请求参数写错了，重试也不会成功。
余额没了，重试也不会成功。
请求太频繁被限流，立刻疯狂重试只会更糟。
```

所以 retry 要有策略。

## 4. 哪些错误适合重试

通常适合重试的是临时性错误。

例如：

```text
网络短暂中断
连接失败
请求超时
服务商临时 5xx
服务商短暂繁忙
409 冲突
408 请求超时
429 限流，但要等待后再重试
```

这些错误的共同特点是：

```text
过一小会儿再试，可能会成功。
```

## 5. 哪些错误不应该重试

通常不适合重试的是确定性错误。

例如：

```text
401 API key 无效
403 没有权限
404 模型或资源不存在
400 请求参数错误
422 请求格式正确但内容无法处理
本地代码 bug
请求体校验失败
```

这些错误的共同特点是：

```text
不改配置、不改代码、不改请求内容，再试也不会成功。
```

## 6. 为什么不能无限重试

无限重试会带来严重问题：

```text
请求越来越多
服务商压力更大
自己服务线程被占住
用户等待更久
可能重复扣费
可能重复执行副作用操作
日志变得混乱
限流更严重
```

所以 retry 必须有上限。

例如：

```text
最多重试 2 次
最多重试 3 次
超过就返回错误
```

## 7. exponential backoff 是什么

`exponential backoff` 叫：

```text
指数退避
```

它的核心思想是：

```text
失败后不要立刻连续重试，而是越往后等得越久。
```

例如：

```text
第 1 次失败：等 0.5 秒
第 2 次失败：等 1 秒
第 3 次失败：等 2 秒
第 4 次失败：等 4 秒
```

这样做的原因是：

```text
如果服务商正在拥堵，立刻疯狂重试只会让拥堵更严重。
```

## 8. rate limit 是什么

`rate limit` 是：

```text
限流。
```

更直白地说：

```text
服务商限制你在一段时间内最多能发多少请求或 token。
```

比如：

```text
每分钟最多 60 个请求
每分钟最多 100000 个 token
每天最多多少额度
```

如果你超过限制，服务商会拒绝请求。

## 9. 429 是什么

HTTP 状态码：

```text
429 Too Many Requests
```

意思是：

```text
请求太多了。
```

在模型 API 里，429 常见原因包括：

```text
请求频率太高
token 使用太多
并发太高
账号或项目额度不足
套餐限制较低
```

OpenAI Python SDK 会把 429 映射成：

```python
RateLimitError
```

## 10. rate limit 和余额不足的关系

要注意：

```text
429 不一定只是“请求太快”。
```

它也可能表示：

```text
额度用完
账单限制
项目预算限制
套餐限制
```

所以用户看到 429 时，后端可以先返回：

```text
模型服务请求过于频繁，请稍后重试。
```

但开发者排查时还要看：

```text
服务商控制台
余额
项目限额
用量统计
具体错误 body
```

## 11. OpenAI SDK 默认重试行为

OpenAI Python SDK 官方文档说明：

```text
某些错误默认会自动重试 2 次。
```

默认会重试的情况包括：

```text
连接错误
408 Request Timeout
409 Conflict
429 Rate Limit
>=500 Internal errors
```

并且使用短的指数退避。

所以你要知道：

```text
就算项目代码里没有自己写 for 循环，SDK 也可能已经帮你重试了。
```

## 12. 为什么还要显式配置 max_retries

如果完全依赖 SDK 默认值，初学者看代码时会不知道：

```text
到底有没有重试？
重试几次？
这个行为在哪里控制？
```

所以本节新增配置：

```text
LLM_MAX_RETRIES=2
```

代码里显式传给 SDK：

```python
OpenAI(
    api_key=api_key,
    max_retries=settings.llm_max_retries,
    timeout=settings.request_timeout_seconds,
)
```

这样项目行为更清楚。

## 13. 当前项目为什么默认 2 次

OpenAI SDK 默认就是 2 次。

本项目先保持：

```text
LLM_MAX_RETRIES=2
```

原因是：

```text
不改变 SDK 默认策略
但把默认策略显式写进配置
方便你学习和后续调整
```

如果想关闭 SDK 重试，可以设置：

```text
LLM_MAX_RETRIES=0
```

如果想多重试几次，可以调大。

但本项目限制最大 5 次。

## 14. 为什么限制最大 5 次

配置里写的是：

```python
llm_max_retries: int = Field(default=2, ge=0, le=5)
```

含义：

```text
最少 0 次
最多 5 次
默认 2 次
```

为什么限制？

```text
防止误配置成 100、999 这种危险值。
```

学习项目里，先把边界守住。

生产项目可以按实际情况重新设计。

## 15. 当前 .env.example 新增了什么

文件：

```text
projects/ai-service/.env.example
```

新增：

```text
LLM_MAX_RETRIES=2
```

这表示：

```text
模型调用交给 SDK 最多重试 2 次。
```

注意：

```text
这不是我们自己写循环。
这是传给 OpenAI SDK 的重试配置。
```

## 16. llm_client.py 新增了什么

文件：

```text
app/services/llm_client.py
```

现在 client 初始化参数里有：

```python
client_kwargs: dict[str, object] = {
    "api_key": api_key,
    "max_retries": settings.llm_max_retries,
    "timeout": settings.request_timeout_seconds,
}
```

也就是说：

```text
API key 负责认证
max_retries 负责 SDK 自动重试次数
timeout 负责单次等待边界
```

## 17. timeout 和 retry 的关系

timeout 和 retry 经常一起出现，但不是一回事。

timeout：

```text
一次请求最多等多久。
```

retry：

```text
失败后最多再试几次。
```

例如：

```text
timeout=30 秒
max_retries=2
```

可能意味着：

```text
第一次请求最多等 30 秒
失败后可能再试
最终整体耗时可能超过 30 秒
```

所以这两个配置要一起理解。

## 18. 本节为什么不手写 retry 循环

我们可以自己写：

```python
for attempt in range(3):
    try:
        call_model()
    except SomeError:
        sleep(...)
```

但本节没有这样做。

原因：

```text
OpenAI SDK 已经内置基础重试
我们还没学异步、任务队列和幂等
手写重试容易重复调用、重复扣费、重复副作用
当前阶段先显式配置 SDK 重试
```

后面复杂场景再考虑自己封装重试策略。

## 19. 幂等是什么

重试前要理解一个词：

```text
幂等
```

简单说：

```text
同一个操作执行一次和执行多次，结果一样。
```

比如查询订单：

```text
查一次和查三次，一般不会改变数据。
```

但创建工单：

```text
执行一次创建一个工单。
执行三次可能创建三个工单。
```

所以涉及写操作、扣费、创建资源时，重试要更小心。

当前 `/chat` 是生成回答，虽然不写数据库，但可能产生模型费用。

所以也不能无限重试。

## 20. RateLimitError 怎么处理

OpenAI SDK 收到 429 时会抛：

```python
RateLimitError
```

本项目新增：

```python
from openai import RateLimitError
```

然后单独捕获：

```python
except RateLimitError as exc:
    logger.warning(
        "llm_rate_limited provider=%s model=%s max_retries=%s",
        self.settings.llm_provider,
        self.settings.llm_model,
        self.settings.llm_max_retries,
    )
    raise AppException(
        code="LLM_RATE_LIMITED",
        message="模型服务请求过于频繁，请稍后重试。",
        status_code=429,
    ) from exc
```

这让限流错误不会被混成普通：

```text
LLM_CALL_FAILED
```

## 21. 为什么 RateLimitError 放在 Exception 前面

异常捕获顺序很重要。

正确：

```python
except RateLimitError:
    ...
except APITimeoutError:
    ...
except Exception:
    ...
```

如果先写：

```python
except Exception:
    ...
```

那么 `RateLimitError` 会被通用异常吞掉。

后面的专门分支就没机会执行。

## 22. 当前 LLM 错误码

当前与模型调用相关的错误码：

| 错误码 | HTTP 状态码 | 含义 |
| --- | --- | --- |
| `LLM_API_KEY_MISSING` | 500 | 服务端没有配置模型 API key |
| `LLM_TIMEOUT` | 504 | 模型调用超时 |
| `LLM_RATE_LIMITED` | 429 | 模型服务限流或请求过于频繁 |
| `LLM_BAD_RESPONSE` | 502 | 模型返回结构异常 |
| `LLM_EMPTY_RESPONSE` | 502 | 模型返回空内容 |
| `LLM_CALL_FAILED` | 502 | 其他模型调用失败 |

这样排查问题会更清楚。

## 23. 为什么返回 429

如果模型服务返回的是：

```text
429 Too Many Requests
```

我们的 `/chat` 也返回：

```text
429
```

这是合理的。

因为对客户端来说：

```text
现在请求太频繁或额度受限，应该稍后再试。
```

前端可以根据 429 做更友好的提示。

## 24. 为什么不暴露服务商原始错误

服务商原始错误可能包含：

```text
内部字段
请求信息
项目标识
调试信息
不适合用户看的英文错误
```

所以对外统一：

```json
{
  "code": "LLM_RATE_LIMITED",
  "message": "模型服务请求过于频繁，请稍后重试。",
  "trace_id": "..."
}
```

内部日志记录必要信息。

## 25. rate limit 日志记录什么

当前日志记录：

```text
provider
model
max_retries
```

例如：

```text
llm_rate_limited provider=aliyun-compatible model=qwen3.7-plus max_retries=2
```

不记录：

```text
用户完整输入
history 原文
API key
```

原因还是：

```text
日志不能泄露敏感信息。
```

## 26. 测试为什么不用真实限流

错误测试方式：

```text
疯狂调用模型接口，直到服务商返回 429。
```

这非常不好。

问题：

```text
浪费费用
污染真实账号限额
测试很慢
测试不稳定
可能影响后续真实学习调用
```

正确方式：

```text
用 fake client 直接抛 RateLimitError。
```

我们测试的是：

```text
自己的代码是否正确处理 RateLimitError。
```

不是测试服务商会不会真的限流。

## 27. RateLimitError 单元测试

测试里构造假的 429 response：

```python
request = httpx.Request("POST", "https://example.com/chat/completions")
response = httpx.Response(
    status_code=429,
    request=request,
    json={"error": {"message": "Too many requests"}},
)
rate_limit_error = RateLimitError(
    "Too many requests",
    response=response,
    body={"error": {"message": "Too many requests"}},
)
```

它不会真的发请求。

它只是构造了一个 SDK 异常对象。

然后 fake client 抛出这个异常。

测试断言：

```text
LLM_RATE_LIMITED
429
```

## 28. /chat 接口级限流测试

接口测试用 fake service：

```python
class FakeRateLimitedLLMChatService:
    def generate_reply(...):
        raise AppException(
            code="LLM_RATE_LIMITED",
            message="模型服务请求过于频繁，请稍后重试。",
            status_code=429,
        )
```

然后请求 `/chat`。

期望响应：

```json
{
  "code": "LLM_RATE_LIMITED",
  "message": "模型服务请求过于频繁，请稍后重试。",
  "trace_id": "trace-rate-limit"
}
```

这验证了：

```text
AppException -> 统一异常处理器 -> JSON 响应
```

## 29. 配置测试

本节新增配置测试：

```text
默认 llm_max_retries 是 2
环境变量 LLM_MAX_RETRIES 可以读取
.env 文件里的 LLM_MAX_RETRIES 可以读取
负数会被拒绝
大于 5 会被拒绝
```

这说明配置不是只写了字段。

它有自动化测试保护。

## 30. client 测试

`test_llm_client.py` 现在会检查：

```python
{
    "api_key": "llm-test-key",
    "base_url": "...",
    "max_retries": 3,
    "timeout": 12.5,
}
```

也就是说：

```text
settings.llm_max_retries 真的传给了 OpenAI client。
```

## 31. smoke test 现在输出什么

脚本：

```text
scripts/llm_compatible_smoke_test.py
```

现在默认输出里多了：

```text
max_retries=2
```

它仍然默认不调用模型。

只是帮助你检查本机配置。

## 32. 真实项目怎么处理 rate limit

真实项目里，429 后可能要做：

```text
提示用户稍后再试
降低请求频率
限制每个用户的调用次数
做队列排队
缓存重复问题
减少 prompt 和 history token
升级服务商额度
根据 Retry-After 头等待
```

当前项目还没做这些。

这一节只先完成：

```text
能识别限流
能返回统一错误
能通过测试验证
```

## 33. rate limit 和限流保护的区别

服务商 rate limit：

```text
服务商限制你调用它的频率。
```

自己系统限流：

```text
你自己的后端限制用户调用你的服务频率。
```

两者都需要。

例如：

```text
用户 -> 你的 ai-service -> 模型服务商
```

你的服务可以先限制用户请求，避免打爆模型服务商。

后面工程化阶段会学自己的限流。

## 34. 常见错误 1：无限重试

错误：

```text
失败就一直重试，直到成功。
```

问题：

```text
可能拖垮系统
可能重复扣费
可能让限流更严重
```

正确：

```text
设置最大重试次数。
```

## 35. 常见错误 2：所有错误都重试

错误：

```text
401、403、404、400 都重试。
```

问题：

```text
这些错误通常不是临时问题。
```

正确：

```text
只对可能临时恢复的错误重试。
```

## 36. 常见错误 3：一被限流就立刻重试

错误：

```text
收到 429 后马上连发更多请求。
```

问题：

```text
会让限流更严重。
```

正确：

```text
等待一段时间，或者按 Retry-After / 指数退避策略重试。
```

## 37. 常见错误 4：不知道 SDK 已经默认重试

错误理解：

```text
我没有写 retry，所以一定没有重试。
```

实际：

```text
OpenAI Python SDK 默认会对部分错误重试 2 次。
```

所以本节把 `LLM_MAX_RETRIES=2` 写进配置，避免隐形行为。

## 38. 常见错误 5：为了测试真的撞限流

错误：

```text
写脚本疯狂调用真实模型，等它 429。
```

正确：

```text
用 fake client 抛 RateLimitError。
```

自动化测试必须快、稳、不依赖外部服务。

## 39. 本节练习

### 练习 1

题目：

用自己的话解释 retry 是什么。

参考答案：

retry 是一次操作失败后，再尝试执行一次或多次，用来应对临时性错误。

### 练习 2

题目：

为什么不能无限重试？

参考答案：

因为无限重试会占用资源、增加费用、让限流更严重，还可能导致重复执行有副作用的操作。

### 练习 3

题目：

哪些错误通常适合重试？

参考答案：

网络短暂失败、连接错误、请求超时、服务商临时 5xx、408、409、429 等临时性错误通常适合有限重试。

### 练习 4

题目：

哪些错误通常不适合重试？

参考答案：

API key 错误、权限不足、模型不存在、请求参数错误、本地校验失败等确定性错误通常不适合重试。

### 练习 5

题目：

rate limit 是什么？

参考答案：

rate limit 是服务商限制你在一段时间内最多能发送多少请求或 token。

超过限制时，服务商可能返回 429。

### 练习 6

题目：

429 状态码是什么意思？

参考答案：

429 表示 Too Many Requests，请求太多了。

在模型服务中通常表示请求频率、token 用量、并发或额度达到限制。

### 练习 7

题目：

OpenAI Python SDK 默认会重试哪些错误？

参考答案：

官方文档说明，连接错误、408、409、429 和 5xx 默认会自动重试，默认重试 2 次。

### 练习 8

题目：

当前项目新增了哪个配置控制 SDK 重试次数？

参考答案：

新增：

```text
LLM_MAX_RETRIES
```

默认值是 2。

### 练习 9

题目：

当前项目把 `RateLimitError` 映射成什么错误码？

参考答案：

映射成：

```text
LLM_RATE_LIMITED
```

HTTP 状态码是：

```text
429
```

### 练习 10

题目：

为什么测试限流时不能真的疯狂调用模型接口？

参考答案：

因为这样会浪费费用、污染真实限额、测试不稳定，还可能影响后续真实调用。

应该用 fake client 直接模拟 `RateLimitError`。

## 40. 本节自测

### 自测 1

题目：

retry 和 timeout 是同一个概念吗？

参考答案：

不是。

timeout 是一次请求最多等多久。

retry 是失败后再试几次。

### 自测 2

题目：

当前 `LLM_MAX_RETRIES` 默认是多少？

参考答案：

默认是：

```text
2
```

### 自测 3

题目：

当前项目允许 `LLM_MAX_RETRIES=-1` 吗？

参考答案：

不允许。

配置要求大于等于 0。

### 自测 4

题目：

当前项目允许 `LLM_MAX_RETRIES=100` 吗？

参考答案：

不允许。

当前限制最大为 5。

### 自测 5

题目：

`RateLimitError` 应该放在 `except Exception` 前面还是后面？

参考答案：

前面。

否则会先被 `Exception` 捕获，专门的限流处理分支不会执行。

### 自测 6

题目：

为什么本节不手写 retry 循环？

参考答案：

因为 OpenAI SDK 已经有基础重试能力，当前阶段先显式配置 SDK 重试。

手写重试还要处理幂等、费用、副作用、退避策略等复杂问题。

### 自测 7

题目：

指数退避是什么意思？

参考答案：

失败后不立刻连续重试，而是每次等待更久，比如 0.5 秒、1 秒、2 秒、4 秒。

### 自测 8

题目：

服务商 rate limit 和自己系统限流是同一件事吗？

参考答案：

不是。

服务商 rate limit 是服务商限制你调用它。

自己系统限流是你的后端限制用户调用你的服务。

### 自测 9

题目：

`LLM_RATE_LIMITED` 对用户意味着什么？

参考答案：

表示模型服务当前请求过于频繁或额度受限，用户应该稍后重试。

### 自测 10

题目：

下一节学习什么？

参考答案：

下一节学习模型调用错误处理，把更多 SDK 错误类型映射成更清晰的统一错误。

## 41. 本节小结

这一节完成了：

```text
理解 retry 是失败后的有限再试
理解不能无限重试
理解哪些错误适合重试，哪些不适合
理解 exponential backoff 指数退避
理解 rate limit 和 429
理解 OpenAI SDK 默认重试 2 次
新增 LLM_MAX_RETRIES 配置
把 max_retries 显式传给 OpenAI client
把 RateLimitError 映射成 LLM_RATE_LIMITED
补充配置测试、client 测试、service 测试和 /chat 接口测试
```

现在 `/chat` 已经具备：

```text
真实模型调用
多轮 history
timeout 处理
SDK 重试次数配置
限流错误处理
统一错误响应
fake 测试隔离
```

下一节进入：

```text
模型调用错误处理
```

会继续把认证失败、权限失败、请求错误、连接错误、服务商 5xx 等错误拆开处理。

## 42. 参考资料

- [OpenAI Python API library：Retries](https://developers.openai.com/api/reference/python#retries)
- [OpenAI Python API library：Handling errors](https://developers.openai.com/api/reference/python#handling-errors)
- [OpenAI Error codes](https://developers.openai.com/api/docs/guides/error-codes)
- [OpenAI Rate limits guide](https://platform.openai.com/docs/guides/rate-limits)
- [MDN：429 Too Many Requests](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/429)
