# 阶段 2 第 12 节：模型调用日志：模型名、耗时、trace_id、token

## 1. 这一节学什么

前面我们已经让 `/chat` 具备了真实模型调用、history、多轮对话、timeout、retry、rate limit 和错误映射。

这一节开始补一个真正工程里非常关键的能力：

```text
模型调用日志
```

你要学会：

```text
为什么模型调用必须打日志
日志和错误响应有什么区别
一次模型调用成功时应该记录什么
一次模型调用失败时应该记录什么
为什么要记录模型名
为什么要记录耗时 elapsed_ms
为什么要记录 trace_id
为什么要记录 token usage
为什么不能记录完整 prompt、history、API key
怎么从模型响应里提取 prompt_tokens、completion_tokens、total_tokens
怎么用 pytest 的 caplog 测试日志
```

这一节不是为了“让控制台多打印几行”，而是为了以后你能排查真实线上问题。

## 2. 先用人话理解日志

日志就是程序运行时留下的记录。

比如一个用户调用 `/chat`，页面只看到：

```json
{
  "reply": "模型生成的回答"
}
```

但后端开发者需要知道：

```text
这次请求有没有真正调用模型？
调用的是哪个服务商？
调用的是哪个模型？
花了多久？
消耗了多少 token？
失败时是什么错误码？
这个错误和哪一次 HTTP 请求对应？
```

这些信息不能都返回给前端。

所以我们写入日志。

## 3. 日志和接口响应不是一回事

接口响应是给用户或前端看的。

日志是给开发者、运维、排查问题的人看的。

例如模型超时时，前端应该看到：

```json
{
  "code": "LLM_TIMEOUT",
  "message": "模型调用超时，请稍后重试。",
  "trace_id": "..."
}
```

日志里可以看到更适合排查的信息：

```text
llm_chat_failed code=LLM_TIMEOUT provider=aliyun-compatible model=qwen3.7-plus status_code=504 elapsed_ms=3001.25
```

前端不需要知道服务商内部细节。

开发者需要知道。

## 4. 模型调用日志最少应该记录什么

当前阶段，我们先记录这些字段：

```text
provider
model
elapsed_ms
prompt_tokens
completion_tokens
total_tokens
code
status_code
trace_id
```

它们分别表示：

| 字段 | 含义 |
| --- | --- |
| `provider` | 当前模型服务商标识，例如 `aliyun-compatible` |
| `model` | 当前调用的模型名，例如 `qwen3.7-plus` |
| `elapsed_ms` | 本次模型调用花了多少毫秒 |
| `prompt_tokens` | 输入给模型的 token 数 |
| `completion_tokens` | 模型生成回复的 token 数 |
| `total_tokens` | 输入 token + 输出 token |
| `code` | 项目内部错误码，例如 `LLM_TIMEOUT` |
| `status_code` | 对外返回的 HTTP 状态码 |
| `trace_id` | 一次 HTTP 请求的追踪 ID |

成功日志更关注：

```text
调用哪个模型
用了多久
消耗多少 token
```

失败日志更关注：

```text
失败类型
调用哪个模型
用了多久
对外返回什么状态码
```

## 5. 为什么要记录 provider

因为以后你可能不只用一个模型服务。

例如：

```text
aliyun-compatible
openai
local-ollama
azure-openai
```

如果日志只写：

```text
model=qwen3.7-plus
```

你不一定知道这次请求走的是哪套服务商配置。

记录 `provider` 后，排查就更清楚：

```text
provider=aliyun-compatible model=qwen3.7-plus
```

## 6. 为什么要记录 model

因为不同模型的表现、速度、价格、上下文长度可能不同。

同一个 `/chat` 接口，未来可能会切换模型：

```text
qwen-plus
qwen-max
gpt-4.1
gpt-5-mini
```

如果某天用户反馈“今天回答明显变慢了”，你可以看日志：

```text
昨天 model=qwen-plus elapsed_ms=800
今天 model=qwen-max elapsed_ms=2600
```

这就能判断是不是模型切换导致的。

## 7. 为什么要记录 elapsed_ms

`elapsed_ms` 是耗时，单位是毫秒。

它回答的问题是：

```text
模型调用到底慢不慢？
```

例如：

```text
elapsed_ms=240.50
elapsed_ms=1200.13
elapsed_ms=8500.77
```

这些数字比“感觉有点慢”可靠。

有了耗时，你才能做：

```text
发现慢请求
判断 timeout 是否合理
比较不同模型速度
发现服务商异常波动
后续做监控和告警
```

## 8. 为什么用 perf_counter

Python 里可以用 `time.perf_counter()` 统计一段代码运行了多久。

本节代码里是这样做的：

```python
start_time = perf_counter()

# 调用模型

elapsed_ms = (perf_counter() - start_time) * 1000
```

为什么不用当前时间相减？

因为当前时间可能受系统时间调整影响。

`perf_counter()` 更适合统计耗时。

你可以记住：

```text
看现在几点：datetime
统计代码跑了多久：perf_counter
```

## 9. 为什么要记录 trace_id

`trace_id` 是一次请求的追踪编号。

假设前端拿到错误响应：

```json
{
  "code": "LLM_TIMEOUT",
  "message": "模型调用超时，请稍后重试。",
  "trace_id": "abc123"
}
```

开发者可以拿 `abc123` 去日志里查：

```text
trace_id=abc123 chat_requested message_length=12
trace_id=abc123 llm_chat_failed code=LLM_TIMEOUT provider=... model=... elapsed_ms=...
```

这样你就能把：

```text
用户看到的错误
后端请求日志
模型调用日志
异常处理日志
```

串成同一次请求。

这就是请求追踪。

## 10. 本项目的 trace_id 是怎么进入日志的

本项目前面已经有：

```text
app/core/trace.py
app/middleware/tracing.py
app/core/logging.py
```

大致流程是：

```text
请求进入 FastAPI
-> tracing middleware 生成或读取 X-Trace-Id
-> 把 trace_id 放进 ContextVar
-> logging record factory 读取当前 trace_id
-> 每条日志格式里自动带 trace_id=...
-> 响应头返回 X-Trace-Id
```

所以本节的 `llm_service.py` 不需要每条日志都手动写 `trace_id`。

只要使用项目统一日志配置，日志格式会自动带：

```text
trace_id=...
```

这叫统一注入。

## 11. 为什么要记录 token

模型服务通常按 token 计费。

token 越多，通常：

```text
成本越高
响应越慢
上下文越容易超限
```

所以模型调用成功后，我们要记录：

```text
prompt_tokens
completion_tokens
total_tokens
```

这三个值常见含义是：

| 字段 | 含义 |
| --- | --- |
| `prompt_tokens` | 输入给模型的内容消耗多少 token |
| `completion_tokens` | 模型生成的回复消耗多少 token |
| `total_tokens` | 本次请求总 token 数 |

OpenAI API Reference 和阿里云百炼 OpenAI 兼容文档都把 `usage` 作为返回里的 token 用量信息。

## 12. 本地估算 token 和真实 usage 的区别

前面第 3 节我们写过：

```text
app/core/token_usage.py
```

那是本地粗略估算。

它适合用来提前提醒：

```text
这段输入大概很长
可能会超过上下文
可能会比较贵
```

但真实计费和真实 token 用量，要看模型 API 返回的：

```text
completion.usage
```

所以你要区分：

```text
本地估算：调用前的粗略判断
真实 usage：调用后的真实结果
```

## 13. usage 长什么样

不同 SDK 返回的对象表现略有差异。

常见对象形式：

```python
completion.usage.prompt_tokens
completion.usage.completion_tokens
completion.usage.total_tokens
```

也可能在测试里模拟成字典：

```python
{
    "prompt_tokens": 12,
    "completion_tokens": 7,
    "total_tokens": 19,
}
```

所以本节代码写了一个小函数：

```python
extract_token_usage(completion)
```

它负责从模型响应里提取 token 信息。

## 14. 为什么要允许 usage 为空

不是所有场景都一定有完整 usage。

例如：

```text
某些兼容服务没有返回 usage
流式输出时 usage 可能在最后一个 chunk
测试 fake response 没有模拟 usage
异常发生时根本没有拿到 completion
```

所以本节代码不是强行要求每次都有 token。

而是允许：

```text
prompt_tokens=None
completion_tokens=None
total_tokens=None
```

这表示：

```text
这次没有拿到对应字段
```

不是程序崩了。

## 15. 为什么不能记录完整 prompt

模型 prompt 里可能包含：

```text
用户真实问题
用户隐私
业务数据
订单信息
手机号
内部知识库片段
系统提示词
```

如果直接写进日志，就可能造成敏感信息泄露。

所以本项目当前只记录：

```text
message_length
provider
model
elapsed_ms
token usage
错误码
```

不记录：

```text
完整用户输入
完整 history
完整 prompt
完整模型回复
API key
Authorization header
```

这点非常重要。

会写日志，不代表什么都能写日志。

## 16. 为什么不能记录 API key

API key 是调用模型的钥匙。

如果写进日志，等于把钥匙复制到另一个地方。

日志可能被：

```text
上传到服务器
发给别人排查
接入日志平台
长期保存
被多人查看
```

所以 key 绝对不能进日志。

本节测试也会检查日志里不能出现：

```text
test-key
```

真实项目里还应该定期做敏感信息扫描。

## 17. 本节新增的 LLMTokenUsage

本节在 `llm_service.py` 里新增：

```python
@dataclass(frozen=True)
class LLMTokenUsage:
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
```

`dataclass` 是 Python 标准库提供的工具。

它适合表达这种简单数据对象：

```text
只有字段
没有复杂行为
需要方便比较
需要清晰类型
```

`frozen=True` 表示对象创建后不应该再修改。

也就是：

```text
这是一份结果，不是一块到处被改的临时数据
```

## 18. 为什么字段类型是 int | None

因为 token 数如果存在，应该是整数。

例如：

```text
prompt_tokens=12
completion_tokens=7
total_tokens=19
```

但如果服务商没有返回，应该允许为空：

```text
prompt_tokens=None
completion_tokens=None
total_tokens=None
```

所以类型写成：

```python
int | None
```

意思是：

```text
要么是 int
要么是 None
```

## 19. 为什么要过滤 bool

Python 里有个容易忽略的点：

```python
isinstance(True, int)
```

结果是：

```text
True
```

因为 `bool` 是 `int` 的子类。

但 token 数不应该是：

```text
True
False
```

所以本节代码里专门过滤：

```python
if isinstance(value, bool):
    return None
```

这是一个小细节，但能避免脏数据混进日志。

## 20. 成功日志怎么写

本节新增：

```python
def _log_success(self, elapsed_ms: float, usage: LLMTokenUsage) -> None:
    logger.info(
        (
            "llm_chat_succeeded provider=%s model=%s elapsed_ms=%.2f "
            "prompt_tokens=%s completion_tokens=%s total_tokens=%s"
        ),
        self.settings.llm_provider,
        self.settings.llm_model,
        elapsed_ms,
        usage.prompt_tokens,
        usage.completion_tokens,
        usage.total_tokens,
    )
```

成功时日志类似：

```text
llm_chat_succeeded provider=aliyun-compatible model=qwen3.7-plus elapsed_ms=842.31 prompt_tokens=30 completion_tokens=81 total_tokens=111
```

这里用 `%s` 占位，不用 f-string。

这是 logging 的常见写法。

好处是日志库可以更好地处理格式化和参数。

## 21. 失败日志怎么写

本节新增：

```python
def _log_failure(
    self,
    app_exception: AppException,
    elapsed_ms: float,
    *,
    exc_info: bool = False,
) -> None:
    logger.warning(
        "llm_chat_failed code=%s provider=%s model=%s status_code=%s elapsed_ms=%.2f",
        app_exception.code,
        self.settings.llm_provider,
        self.settings.llm_model,
        app_exception.status_code,
        elapsed_ms,
        exc_info=exc_info,
    )
```

失败时日志类似：

```text
llm_chat_failed code=LLM_TIMEOUT provider=aliyun-compatible model=qwen3.7-plus status_code=504 elapsed_ms=3002.18
```

## 22. 为什么失败日志用 warning

日志级别可以简单理解为：

| 级别 | 含义 |
| --- | --- |
| `DEBUG` | 调试细节 |
| `INFO` | 正常业务事件 |
| `WARNING` | 需要关注，但服务未必崩 |
| `ERROR` | 明确错误 |
| `CRITICAL` | 严重故障 |

模型调用失败值得关注。

但一次模型失败不一定意味着整个服务崩溃。

所以本节先用：

```text
WARNING
```

以后如果要接监控，可以按错误码和数量做告警。

## 23. exc_info 是什么

`exc_info=True` 会把异常堆栈也写进日志。

这对开发排查很有用。

本节规则是：

```text
未知异常 -> exc_info=True
已经整理好的 AppException -> exc_info=False
```

原因是：

```text
未知异常需要堆栈帮助排查
AppException 已经是项目内主动抛出的业务错误，通常不需要每次都打印完整堆栈
```

## 24. generate_reply 现在的调用流程

本节改完后，`generate_reply` 的核心流程变成：

```text
检查 API key
构建 messages
记录开始时间
调用模型
提取回复
提取 token usage
记录成功日志
返回 reply
```

失败时：

```text
检查 API key
构建 messages
记录开始时间
调用模型失败
映射成 AppException
记录失败日志
抛给统一异常处理器
```

这就是典型工程写法：

```text
业务逻辑
错误映射
日志记录
统一响应
```

## 25. 为什么没有把 token 放进接口响应

现在 `/chat` 的响应仍然是：

```json
{
  "reply": "模型生成的回答"
}
```

没有返回：

```json
{
  "prompt_tokens": 12,
  "completion_tokens": 7
}
```

原因是当前阶段先把 token 作为服务端观测信息。

以后如果做：

```text
用户用量统计
计费系统
控制台展示
成本报表
```

再设计专门的响应字段或数据库表。

不要为了调试方便，随便把内部信息暴露给前端。

## 26. 为什么要测试日志

如果只看控制台，容易漏。

自动化测试可以明确检查：

```text
成功时有 llm_chat_succeeded
失败时有 llm_chat_failed
日志包含 provider
日志包含 model
日志包含 elapsed_ms
日志包含 token usage
日志不包含完整用户输入
日志不包含 API key
```

这就把“日志规范”变成了可验证的工程规则。

## 27. pytest 的 caplog 是什么

`caplog` 是 pytest 提供的日志捕获工具。

它可以在测试里拿到当前代码打出的日志。

例如：

```python
def test_xxx(caplog):
    caplog.set_level(logging.INFO, logger="app.services.llm_service")

    # 执行业务代码

    messages = [record.getMessage() for record in caplog.records]
```

然后你就可以断言：

```python
assert "llm_chat_succeeded" in messages[0]
```

这和测试函数返回值一样，是在测试程序行为。

## 28. 本节新增测试覆盖了什么

本节在 `tests/test_llm_service.py` 增加了：

```text
extract_token_usage 可以从对象 usage 提取 token
extract_token_usage 可以从 dict usage 提取 token
extract_token_usage 遇到缺失或非法 token 值时返回 None
模型调用成功时会记录 provider、model、elapsed_ms、token usage
模型调用失败时会记录 code、provider、model、status_code、elapsed_ms
日志不记录完整用户输入
日志不记录 API key
```

这就是工程化测试的价值：

```text
不仅测返回值
还测可观测性和安全边界
```

## 29. 当前成功日志示例

如果你本地配置了真实 `.env`，调用 `/chat` 成功后，日志大概像这样：

```text
2026-07-09 10:00:00 INFO [app.services.llm_service] trace_id=... llm_chat_succeeded provider=aliyun-compatible model=qwen3.7-plus elapsed_ms=842.31 prompt_tokens=30 completion_tokens=81 total_tokens=111
```

字段很多，但结构清楚。

你可以从左到右读：

```text
什么时候
什么级别
哪个 logger
哪次请求
发生了什么事件
调用哪个服务商
调用哪个模型
用了多久
用了多少 token
```

## 30. 当前失败日志示例

如果模型调用失败，日志大概像这样：

```text
2026-07-09 10:00:02 WARNING [app.services.llm_service] trace_id=... llm_chat_failed code=LLM_CALL_FAILED provider=aliyun-compatible model=qwen3.7-plus status_code=502 elapsed_ms=126.75
```

如果是未知异常，还会带堆栈信息。

堆栈能帮助你定位是哪一行代码出错。

## 31. 为什么日志事件名用 llm_chat_succeeded

本节日志里有两个事件名：

```text
llm_chat_succeeded
llm_chat_failed
```

事件名的作用是方便检索。

以后你可以在日志系统里搜索：

```text
llm_chat_succeeded
```

看成功调用。

搜索：

```text
llm_chat_failed
```

看失败调用。

如果只写：

```text
success
failed
```

就太泛了。

## 32. 为什么不记录模型回复全文

模型回复也可能包含敏感内容。

例如用户问：

```text
帮我总结这份合同里的付款账号
```

模型回复里可能会出现付款账号。

如果完整记录模型回复，也可能泄露数据。

所以当前阶段不记录完整 reply。

需要排查质量问题时，后面可以设计：

```text
脱敏采样
用户授权
测试环境复现
专门的审计存储
```

不能直接把所有回复扔进普通日志。

## 33. 为什么不记录完整 history

history 是多轮对话上下文。

它可能比本轮用户输入更敏感。

例如：

```text
第一轮：我的订单号是 ...
第二轮：我的手机号是 ...
第三轮：那这个怎么退款？
```

如果记录完整 history，就把前几轮敏感数据全写进日志。

所以当前只记录元信息，不记录原文。

## 34. 以后还会怎么升级日志

这一节是基础版。

后续真实项目可能继续升级：

```text
request_id / user_id
tenant_id
route
模型输入输出 token 成本换算
错误分组统计
慢请求阈值
日志 JSON 格式
接入 OpenTelemetry
接入 Prometheus / Grafana
接入云日志平台
```

但现在不要一下子堆太多。

先把基础字段写对、测住、安全边界守住。

## 35. 你现在应该能解释什么

学完这一节，你应该能向别人解释：

```text
为什么模型调用不是调通就结束
为什么日志是 AI 服务工程化的一部分
为什么成功和失败日志字段不一样
为什么 trace_id 可以把多条日志串起来
为什么 token usage 是成本和性能分析的基础
为什么敏感信息不能写日志
为什么用 caplog 测试日志
```

如果你能把这些讲清楚，就不是只会复制代码。

你是真的理解了模型调用日志。

## 36. 本节代码变更

本节主要修改：

```text
projects/ai-service/app/services/llm_service.py
projects/ai-service/tests/test_llm_service.py
```

新增能力：

```text
LLMTokenUsage
extract_token_usage
成功日志 _log_success
失败日志 _log_failure
模型调用耗时 elapsed_ms
success/failure log tests
token usage extraction tests
```

## 37. 本节练习

### 练习 1

题目：

请用自己的话解释：模型调用日志和接口响应有什么区别？

参考答案：

接口响应是给前端或用户看的，要简洁、安全、稳定。

模型调用日志是给开发者排查问题看的，可以记录 provider、model、elapsed_ms、token usage、错误码等内部排查信息。

### 练习 2

题目：

为什么模型调用成功时要记录 `elapsed_ms`？

参考答案：

因为 `elapsed_ms` 可以告诉我们模型调用实际花了多久。

它能帮助判断接口慢不慢、timeout 是否合理、不同模型速度是否有差异、服务商是否有异常波动。

### 练习 3

题目：

为什么本项目不在日志里记录完整用户输入？

参考答案：

因为用户输入可能包含隐私、业务数据、订单号、手机号、内部资料等敏感信息。

如果写进日志，日志被复制、上传或多人查看时就可能泄露数据。

### 练习 4

题目：

`prompt_tokens`、`completion_tokens`、`total_tokens` 分别表示什么？

参考答案：

`prompt_tokens` 表示输入给模型的 token 数。

`completion_tokens` 表示模型生成回复的 token 数。

`total_tokens` 表示本次请求总 token 数，通常是输入 token 和输出 token 的总和。

### 练习 5

题目：

为什么 `extract_token_usage` 要允许 token 字段是 `None`？

参考答案：

因为不是所有场景都会返回完整 usage。

例如兼容服务没有返回 usage、流式输出 usage 出现在最后、测试 fake response 没有模拟 usage、或者调用失败没有拿到 completion。

用 `None` 可以表示没有拿到该字段，而不是让程序直接失败。

### 练习 6

题目：

为什么 `bool` 类型不应该被当成 token 数？

参考答案：

虽然 Python 里 `bool` 是 `int` 的子类，但 token 数应该是明确的整数数量。

`True` 和 `False` 不能表达真实 token 数，所以应该过滤掉。

### 练习 7

题目：

为什么本节用 `perf_counter()` 统计耗时？

参考答案：

`perf_counter()` 适合测量一段代码运行了多久，不容易受系统时间调整影响。

统计模型调用耗时应该用它，而不是用当前日期时间做业务时间差。

### 练习 8

题目：

为什么 `llm_service.py` 里没有手动把 `trace_id` 写进每条日志？

参考答案：

因为项目已经在 `app/core/logging.py` 里安装了 log record factory。

每条日志创建时都会自动从 `ContextVar` 里读取当前请求的 `trace_id`，日志格式也已经包含 `trace_id=%(trace_id)s`。

### 练习 9

题目：

`caplog` 在本节测试里有什么作用？

参考答案：

`caplog` 用来捕获测试期间产生的日志。

测试可以从 `caplog.records` 里读取日志内容，并断言成功日志、失败日志、字段和敏感信息过滤是否符合预期。

### 练习 10

题目：

为什么失败日志记录 `code` 和 `status_code`，但不直接把原始 SDK 异常返回给前端？

参考答案：

`code` 是项目稳定的错误码，`status_code` 是对外 HTTP 状态。

原始 SDK 异常属于后端实现细节，可能包含不适合暴露的信息，也会让前端依赖第三方 SDK 细节。

所以前端看项目错误码，开发者看日志和后端异常信息。

## 38. 本节自测

### 自测 1

题目：

模型调用成功日志的事件名是什么？

参考答案：

```text
llm_chat_succeeded
```

### 自测 2

题目：

模型调用失败日志的事件名是什么？

参考答案：

```text
llm_chat_failed
```

### 自测 3

题目：

当前成功日志会记录完整 prompt 吗？

参考答案：

不会。

当前只记录 provider、model、elapsed_ms 和 token usage 等元信息，不记录完整 prompt。

### 自测 4

题目：

当前失败日志会记录 API key 吗？

参考答案：

不会。

API key 是敏感凭证，不能进入日志。

### 自测 5

题目：

当前项目真实 token 用量应该优先看哪里？

参考答案：

优先看模型 API 响应里的 `completion.usage`。

本地 token 估算只能做调用前的粗略判断。

### 自测 6

题目：

`total_tokens` 通常等于什么？

参考答案：

通常等于：

```text
prompt_tokens + completion_tokens
```

### 自测 7

题目：

为什么 `trace_id` 对排查问题很重要？

参考答案：

因为它能把同一次请求产生的多条日志和前端错误响应串起来。

用户只要提供 `trace_id`，开发者就可以定位到对应请求的完整日志链路。

### 自测 8

题目：

`elapsed_ms=2500` 大约表示模型调用花了多久？

参考答案：

大约 2500 毫秒，也就是 2.5 秒。

### 自测 9

题目：

未知异常为什么通常要 `exc_info=True`？

参考答案：

因为未知异常需要完整堆栈帮助开发者定位是哪一行代码出错。

### 自测 10

题目：

下一节学习什么？

参考答案：

下一节学习 streaming 流式输出是什么，为后面实现 `/stream-chat` 做准备。

## 39. 本节小结

这一节完成了：

```text
理解模型调用日志的作用
理解日志和接口响应的区别
理解成功日志和失败日志应该记录什么
理解 provider、model、elapsed_ms、trace_id、token usage 的价值
理解哪些敏感信息不能进入日志
新增 LLMTokenUsage
新增 extract_token_usage
新增模型调用成功日志
新增模型调用失败日志
补充 token usage 提取测试
补充成功/失败日志测试
```

现在 `/chat` 已经具备：

```text
真实模型调用
多轮 history
timeout 处理
SDK retry 配置
限流错误处理
常见 SDK 错误映射
模型调用成功/失败日志
token usage 记录
trace_id 串联日志
fake 测试隔离
```

下一节进入：

```text
streaming 流式输出是什么
```

## 40. 参考资料

- [OpenAI API Reference：Chat Completions](https://developers.openai.com/api/reference/python/resources/chat/subresources/completions/methods/create/)
- [OpenAI API Reference：Completions usage](https://developers.openai.com/api/reference/resources/completions/methods/create/)
- [阿里云百炼：OpenAI Chat接口兼容](https://help.aliyun.com/zh/model-studio/compatibility-of-openai-with-dashscope)
- [Python logging 文档](https://docs.python.org/3/library/logging.html)
- [Python time.perf_counter 文档](https://docs.python.org/3/library/time.html#time.perf_counter)
