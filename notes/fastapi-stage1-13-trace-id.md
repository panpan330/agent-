# 阶段 1 第 13 节：trace_id 请求追踪

## 1. 这一节学什么

这一节学习 `trace_id` 请求追踪。

先记住一句话：

```text
trace_id 是一次请求的唯一编号。
```

它的作用是：

```text
把同一次请求产生的多行日志串起来。
```

上一节我们已经学了 `logging`。

现在 `/chat` 会写日志：

```text
mock_chat_requested message_length=4
```

但真实服务里，一次请求不会只产生一行日志。

以后一次 AI 请求可能会经历：

```text
收到 HTTP 请求
校验请求参数
调用大模型
调用向量库
调用 Java 接口
生成响应
返回给用户
```

每一步都可能写日志。

如果同时有很多用户访问，日志会交错在一起。

例如：

```text
request_started path=/chat
request_started path=/chat
mock_chat_requested message_length=4
mock_chat_requested message_length=9
request_finished status_code=200
request_finished status_code=200
```

你很难看出哪一行属于哪一次请求。

如果加上 `trace_id`，就清楚了：

```text
trace_id=a111 request_started path=/chat
trace_id=b222 request_started path=/chat
trace_id=a111 mock_chat_requested message_length=4
trace_id=b222 mock_chat_requested message_length=9
trace_id=a111 request_finished status_code=200
trace_id=b222 request_finished status_code=200
```

这就是请求追踪。

## 2. 为什么 AI 服务更需要 trace_id

普通接口可能只是：

```text
查数据库
返回结果
```

AI 服务通常更复杂。

一次用户提问可能会变成：

```text
HTTP 请求
解析用户问题
调用 embedding 模型
查询向量库
重排结果
拼 prompt
调用大模型
解析模型输出
必要时调用工具
返回最终答案
```

如果其中一步慢了、错了、结果不对，你要能追踪整条链路。

所以后面做 RAG 和 Agent 时，`trace_id` 是非常基础的工程能力。

## 3. 什么是请求追踪

请求追踪可以理解成：

```text
给每一次请求贴一个标签，然后让这次请求后续产生的日志都带着这个标签。
```

这个标签就是 `trace_id`。

最简单版本就是：

```text
请求进来 -> 生成 trace_id
处理请求 -> 日志带 trace_id
响应返回 -> 响应头也带 trace_id
```

本节做的是这个最小版本。

## 4. 什么是响应头里的 X-Trace-Id

HTTP 响应除了 body，还有 headers。

例如响应 body 可能是：

```json
{"status": "ok"}
```

响应 headers 里可以有：

```text
X-Trace-Id: 4f9f3d6f3b0b43a3a9404bfa39923f18
```

这样客户端拿到错误时，可以把这个编号告诉后端：

```text
我刚才那次请求的 X-Trace-Id 是 4f9f...
```

后端就能用这个编号查日志。

## 5. 为什么 header 叫 X-Trace-Id

本节使用：

```text
X-Trace-Id
```

这是一个自定义 HTTP 头。

意思是：

```text
这次请求或响应对应的追踪编号。
```

真实生产系统里也可能用：

```text
X-Request-Id
X-Correlation-Id
traceparent
```

`traceparent` 属于更标准化的分布式追踪协议方向。

我们现在先从最容易理解的 `X-Trace-Id` 开始。

## 6. 这一节新增了哪些文件

本节新增：

```text
app/core/trace.py
app/middleware/__init__.py
app/middleware/tracing.py
tests/test_trace.py
notes/fastapi-stage1-13-trace-id.md
```

并修改：

```text
app/core/logging.py
app/main.py
```

## 7. `app/core/trace.py` 的作用

文件：

```text
projects/ai-service/app/core/trace.py
```

这个文件只负责 trace_id 的底层工具。

代码结构：

```python
from contextvars import ContextVar, Token
from uuid import uuid4


TRACE_ID_HEADER = "X-Trace-Id"
DEFAULT_TRACE_ID = "-"

_trace_id: ContextVar[str] = ContextVar("trace_id", default=DEFAULT_TRACE_ID)
```

这里先看三个东西：

```text
TRACE_ID_HEADER
DEFAULT_TRACE_ID
_trace_id
```

## 8. `TRACE_ID_HEADER`

```python
TRACE_ID_HEADER = "X-Trace-Id"
```

这个常量表示我们统一使用的 HTTP header 名称。

为什么要定义常量？

因为如果到处手写：

```python
"X-Trace-Id"
```

以后容易写错：

```text
X-Trace-ID
X-Trace-id
X-Request-Id
```

统一成常量后，代码里都引用它：

```python
response.headers[TRACE_ID_HEADER] = trace_id
```

这样更稳定。

## 9. `DEFAULT_TRACE_ID`

```python
DEFAULT_TRACE_ID = "-"
```

这个表示当前没有请求上下文时的默认 trace_id。

比如程序启动时，或者某个后台代码不在 HTTP 请求里运行时，日志里可以显示：

```text
trace_id=-
```

这表示：

```text
当前日志不属于某一次 HTTP 请求。
```

## 10. 为什么需要 ContextVar

```python
_trace_id: ContextVar[str] = ContextVar("trace_id", default=DEFAULT_TRACE_ID)
```

`ContextVar` 是 Python 标准库 `contextvars` 提供的上下文变量。

你可以先把它理解成：

```text
它像一个变量，但它的值跟当前执行上下文绑定。
```

为什么不用普通全局变量？

假设使用普通全局变量：

```python
current_trace_id = "a111"
```

如果两个请求同时进来：

```text
请求 A 设置 current_trace_id = a111
请求 B 设置 current_trace_id = b222
请求 A 继续写日志
```

请求 A 的日志可能会读到 B 的 trace_id。

这就是串号。

后端服务经常并发处理请求，所以不能用普通全局变量保存“当前请求编号”。

`ContextVar` 更适合这种场景。

## 11. `generate_trace_id()`

```python
def generate_trace_id() -> str:
    return uuid4().hex
```

`uuid4()` 会生成一个随机 UUID。

`.hex` 会把它变成 32 位十六进制字符串。

例如：

```text
4f9f3d6f3b0b43a3a9404bfa39923f18
```

这个字符串适合放进日志和响应头。

## 12. 为什么不用自增数字

你可能会想：

```text
第 1 次请求 trace_id=1
第 2 次请求 trace_id=2
```

这在单机小程序里看起来可以。

但后端服务可能：

```text
重启
多进程
多台机器
多个服务
```

自增数字很容易重复。

`uuid4()` 更适合作为简单唯一 ID。

## 13. `get_or_create_trace_id()`

```python
def get_or_create_trace_id(incoming_trace_id: str | None) -> str:
    if incoming_trace_id and incoming_trace_id.strip():
        return incoming_trace_id.strip()
    return generate_trace_id()
```

这个函数做的是：

```text
如果请求头里已经带了 trace_id，就复用它
如果没有，就新生成一个
```

为什么要复用请求头里的 trace_id？

因为一个完整系统可能不只有 Python 服务。

以后可能是：

```text
前端 -> Java 服务 -> Python AI 服务
```

如果 Java 服务已经生成了 trace_id，Python 服务应该继续使用同一个。

这样跨服务日志才能串起来。

## 14. `set_trace_id()`

```python
def set_trace_id(trace_id: str) -> Token[str]:
    return _trace_id.set(trace_id)
```

这行表示：

```text
把当前请求上下文里的 trace_id 设置成指定值。
```

它返回一个 `Token`。

你先把 `Token` 理解成：

```text
恢复现场用的凭证。
```

设置之前是什么值，`Token` 里会记住。

## 15. `reset_trace_id()`

```python
def reset_trace_id(token: Token[str]) -> None:
    _trace_id.reset(token)
```

请求结束后，要用 `Token` 恢复原来的值。

这很重要。

否则当前请求的 trace_id 可能影响后续代码。

我们在 middleware 里会用：

```python
token = set_trace_id(trace_id)

try:
    ...
finally:
    reset_trace_id(token)
```

`finally` 的意思是：

```text
无论请求成功还是失败，最后都要清理上下文。
```

## 16. 什么是 middleware

middleware 翻译成“中间件”。

在 FastAPI 里，你可以先理解成：

```text
所有请求进入接口函数之前，都会先经过 middleware。
所有响应返回客户端之前，也会经过 middleware。
```

请求流程：

```text
客户端请求
-> middleware 请求前逻辑
-> 路由函数，例如 /chat
-> middleware 响应后逻辑
-> 客户端收到响应
```

所以 trace_id 非常适合放在 middleware 里做。

因为它不是某一个接口独有的逻辑。

它应该对所有接口生效。

## 17. `app/middleware/tracing.py`

新增文件：

```text
projects/ai-service/app/middleware/tracing.py
```

核心结构：

```python
def register_trace_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def trace_request(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        ...
```

这表示：

```text
给 FastAPI app 注册一个 HTTP middleware。
```

`request` 是当前 HTTP 请求。

`call_next` 是一个函数。

它的作用是：

```text
把请求继续交给后面的路由处理。
```

如果不调用 `call_next(request)`，请求就不会进入 `/health` 或 `/chat`。

## 18. middleware 里读取请求头

```python
trace_id = get_or_create_trace_id(request.headers.get(TRACE_ID_HEADER))
```

这行做了两件事：

```text
从请求头读取 X-Trace-Id
如果没有，就生成一个新的 trace_id
```

例如客户端带了：

```text
X-Trace-Id: client-trace-001
```

那服务端就复用：

```text
client-trace-001
```

如果客户端没带，就生成类似：

```text
4f9f3d6f3b0b43a3a9404bfa39923f18
```

## 19. middleware 里设置上下文

```python
token = set_trace_id(trace_id)
```

这行把当前请求的 trace_id 放进 `ContextVar`。

从这一行之后，同一次请求里的日志就可以读到这个 trace_id。

比如 `/chat` 里没有手动传 trace_id：

```python
logger.info("mock_chat_requested message_length=%s", len(request.message))
```

但日志记录仍然能带上 trace_id。

因为 logging 会从当前上下文里读取。

## 20. middleware 里记录请求开始

```python
logger.info(
    "request_started method=%s path=%s",
    request.method,
    request.url.path,
)
```

这表示：

```text
请求开始了
请求方法是什么
请求路径是什么
```

例如：

```text
request_started method=POST path=/chat
```

## 21. middleware 里计算耗时

```python
start_time = time.perf_counter()
```

`perf_counter()` 适合用来计算耗时。

请求结束后：

```python
elapsed_ms = (time.perf_counter() - start_time) * 1000
```

这里乘以 1000，是把秒变成毫秒。

例如：

```text
0.012 秒 = 12 毫秒
```

## 22. middleware 里继续处理请求

```python
response = await call_next(request)
```

这行非常关键。

它表示：

```text
继续执行后面的路由函数。
```

如果是：

```text
GET /health
```

就会进入 `/health` 对应函数。

如果是：

```text
POST /chat
```

就会进入 `/chat` 对应函数。

## 23. middleware 里设置响应头

```python
response.headers[TRACE_ID_HEADER] = trace_id
```

这行表示：

```text
把 trace_id 放到响应头 X-Trace-Id 里。
```

客户端拿到响应后，就能看到本次请求的编号。

## 24. middleware 里记录请求结束

```python
logger.info(
    "request_finished method=%s path=%s status_code=%s elapsed_ms=%.2f",
    request.method,
    request.url.path,
    response.status_code,
    elapsed_ms,
)
```

这行会记录：

```text
请求方法
请求路径
响应状态码
请求耗时
```

例如：

```text
request_finished method=POST path=/chat status_code=200 elapsed_ms=3.52
```

## 25. middleware 里记录异常

```python
except Exception:
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    logger.exception(
        "request_failed method=%s path=%s elapsed_ms=%.2f",
        request.method,
        request.url.path,
        elapsed_ms,
    )
    raise
```

`logger.exception()` 会记录错误日志，并带上异常堆栈。

这里我们捕获异常后又 `raise`。

意思是：

```text
我记录这个错误，但不在这里吞掉错误。
```

统一异常响应会放到下一节学习。

本节只负责追踪和记录。

## 26. 为什么用 finally 清理

```python
finally:
    reset_trace_id(token)
```

`finally` 的特点是：

```text
无论 try 里成功还是失败，都会执行。
```

所以它适合清理资源、恢复上下文。

请求结束后，当前 trace_id 应该恢复成之前的值。

否则后续代码可能读到已经结束的请求编号。

## 27. 在 main.py 注册 middleware

文件：

```text
projects/ai-service/app/main.py
```

新增：

```python
from app.middleware.tracing import register_trace_middleware
```

并在创建 app 后注册：

```python
register_trace_middleware(app)
```

当前 `create_app()` 的顺序是：

```text
读取配置
配置日志
创建 FastAPI app
注册 trace middleware
注册 health router
注册 chat router
返回 app
```

## 28. 日志怎么自动带 trace_id

上一节日志格式是：

```text
%(asctime)s %(levelname)s [%(name)s] %(message)s
```

本节改成：

```text
%(asctime)s %(levelname)s [%(name)s] trace_id=%(trace_id)s %(message)s
```

多了：

```text
trace_id=%(trace_id)s
```

这表示每条日志都要从日志记录里取 `trace_id` 字段。

## 29. 什么是 LogRecord

Python logging 每写一条日志，内部都会创建一个 `LogRecord`。

你可以把它理解成：

```text
一条日志在 Python 内部的数据对象。
```

它里面有：

```text
日志级别
logger 名称
日志消息
时间
文件名
行号
```

本节给它额外补上：

```text
trace_id
```

## 30. `install_trace_id_log_record_factory()`

文件：

```text
projects/ai-service/app/core/logging.py
```

新增核心逻辑：

```python
def install_trace_id_log_record_factory() -> None:
    global _TRACE_ID_LOG_RECORD_FACTORY_INSTALLED

    if _TRACE_ID_LOG_RECORD_FACTORY_INSTALLED:
        return

    previous_factory = logging.getLogRecordFactory()

    def record_factory(*args: object, **kwargs: object) -> logging.LogRecord:
        record = previous_factory(*args, **kwargs)
        if not hasattr(record, "trace_id"):
            record.trace_id = get_trace_id()
        return record

    logging.setLogRecordFactory(record_factory)
    _TRACE_ID_LOG_RECORD_FACTORY_INSTALLED = True
```

这段代码的目标是：

```text
以后每创建一条日志记录，就自动把当前 trace_id 放进去。
```

这样业务代码不用写：

```python
logger.info("xxx trace_id=%s", trace_id)
```

业务代码只写业务事件：

```python
logger.info("mock_chat_requested message_length=%s", len(request.message))
```

日志系统自动补 trace_id。

## 31. 为什么不用每行日志都手动传 trace_id

手动写会变成：

```python
logger.info("trace_id=%s event=a", trace_id)
logger.info("trace_id=%s event=b", trace_id)
logger.info("trace_id=%s event=c", trace_id)
```

问题是：

```text
重复
容易漏
容易写错
业务代码被日志细节污染
```

更好的方式是：

```text
trace_id 属于横切能力，由日志配置自动注入。
```

“横切能力”意思是：

```text
不是某个业务独有，而是很多业务都需要。
```

日志、trace_id、异常处理、权限校验都属于这类常见能力。

## 32. 本节测试覆盖了什么

新增文件：

```text
projects/ai-service/tests/test_trace.py
```

测试包含：

```text
生成 trace_id
复用请求头里的 trace_id
空请求头时生成新 trace_id
ContextVar 可以 set/reset
/health 响应头有 X-Trace-Id
客户端传 X-Trace-Id 时响应会复用
两次请求会有不同 trace_id
/chat 的多条日志共享同一个 trace_id
```

## 33. 测试生成 trace_id

```python
def test_generate_trace_id_returns_hex_string() -> None:
    trace_id = generate_trace_id()

    assert re.fullmatch(r"[0-9a-f]{32}", trace_id)
```

这个测试说明：

```text
generate_trace_id() 会生成 32 位小写十六进制字符串。
```

## 34. 测试复用请求头

```python
def test_get_or_create_trace_id_reuses_incoming_header() -> None:
    assert get_or_create_trace_id("client-trace-001") == "client-trace-001"
```

这个测试说明：

```text
如果客户端已经传了 trace_id，服务端会复用它。
```

## 35. 测试空请求头时生成新值

```python
def test_get_or_create_trace_id_ignores_blank_header() -> None:
    trace_id = get_or_create_trace_id("   ")

    assert re.fullmatch(r"[0-9a-f]{32}", trace_id)
```

空字符串或全是空格没有意义。

所以这种情况要生成新的 trace_id。

## 36. 测试 ContextVar set/reset

```python
def test_trace_id_context_can_be_set_and_reset() -> None:
    token = set_trace_id("lesson-13")

    try:
        assert get_trace_id() == "lesson-13"
    finally:
        reset_trace_id(token)

    assert get_trace_id() == DEFAULT_TRACE_ID
```

这个测试非常重要。

它证明：

```text
设置后能读到
重置后恢复默认值
```

## 37. 测试响应头有 trace_id

```python
def test_health_response_has_trace_id_header(client: TestClient) -> None:
    response = client.get("/health")
    trace_id = response.headers[TRACE_ID_HEADER]

    assert response.status_code == 200
    assert re.fullmatch(r"[0-9a-f]{32}", trace_id)
```

这个测试说明：

```text
即使是 /health 这种简单接口，也会经过 trace middleware。
```

所以响应里会有：

```text
X-Trace-Id
```

## 38. 测试响应复用客户端 trace_id

```python
def test_trace_id_header_reuses_incoming_value(client: TestClient) -> None:
    response = client.get("/health", headers={TRACE_ID_HEADER: "client-trace-001"})

    assert response.status_code == 200
    assert response.headers[TRACE_ID_HEADER] == "client-trace-001"
```

这个测试模拟：

```text
上游服务已经传入 trace_id。
```

Python AI 服务不重新生成，而是继续使用它。

## 39. 测试两次请求 trace_id 不同

```python
def test_trace_id_header_is_different_for_different_requests(client: TestClient) -> None:
    first = client.get("/health")
    second = client.get("/health")

    assert first.headers[TRACE_ID_HEADER] != second.headers[TRACE_ID_HEADER]
```

这个测试说明：

```text
没有传请求头时，每次请求都会生成自己的 trace_id。
```

## 40. 测试 /chat 日志共享同一个 trace_id

```python
def test_chat_logs_share_request_trace_id(
    client: TestClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    trace_id = "client-trace-lesson-13"
    caplog.set_level(logging.INFO)

    response = client.post(
        "/chat",
        headers={TRACE_ID_HEADER: trace_id},
        json={"message": "追踪日志"},
    )
```

这个测试里，客户端主动传：

```text
X-Trace-Id: client-trace-lesson-13
```

然后我们检查日志：

```python
trace_ids = [
    record.trace_id
    for record in caplog.records
    if record.name in {"app.middleware.tracing", "app.routers.chat"}
]
```

最后断言：

```python
assert all(value == trace_id for value in trace_ids)
```

这表示：

```text
middleware 的日志和 /chat 的日志都属于同一次请求。
```

## 41. 现在一次 /chat 请求会发生什么

当你请求：

```text
POST /chat
```

大致流程是：

```text
1. 请求进入 trace middleware
2. middleware 读取或生成 trace_id
3. middleware 把 trace_id 放入 ContextVar
4. middleware 记录 request_started
5. 请求进入 /chat 路由
6. /chat 记录 mock_chat_requested
7. /chat 返回 ChatResponse
8. middleware 把 X-Trace-Id 放入响应头
9. middleware 记录 request_finished
10. middleware 清理 trace_id 上下文
```

## 42. 当前日志会长什么样

启动服务后，请求 `/chat`，日志大致会像这样：

```text
2026-07-07 19:20:00 INFO [app.middleware.tracing] trace_id=abc request_started method=POST path=/chat
2026-07-07 19:20:00 INFO [app.routers.chat] trace_id=abc mock_chat_requested message_length=4
2026-07-07 19:20:00 INFO [app.middleware.tracing] trace_id=abc request_finished method=POST path=/chat status_code=200 elapsed_ms=2.31
```

三行日志虽然来自不同位置，但 `trace_id` 相同。

这就能串起来。

## 43. 当前实现还不是完整分布式追踪

本节的 `trace_id` 是基础工程能力。

它还不是完整的分布式追踪系统。

完整系统可能会涉及：

```text
OpenTelemetry
traceparent
span_id
parent_span_id
Jaeger
Tempo
Zipkin
链路采样
跨服务调用传播
```

现在先不用学这些。

当前阶段要学会的是：

```text
一次请求一个编号
日志里带编号
响应头返回编号
测试能验证编号存在
```

## 44. 本节练习

### 练习 1

题目：

用自己的话解释：

```text
trace_id 是什么？
```

参考答案：

`trace_id` 是一次请求的唯一编号。

它用来把同一次请求产生的多行日志串起来，方便排查问题。

### 练习 2

题目：

为什么不能用普通全局变量保存当前请求的 trace_id？

参考答案：

因为后端服务可能同时处理多个请求。

如果用普通全局变量，请求 A 和请求 B 可能互相覆盖 trace_id，导致日志串号。

所以我们使用 `ContextVar` 保存当前执行上下文里的 trace_id。

### 练习 3

题目：

下面这段代码是什么意思？

```python
response.headers[TRACE_ID_HEADER] = trace_id
```

参考答案：

它把当前请求的 trace_id 写入 HTTP 响应头。

因为 `TRACE_ID_HEADER` 的值是 `"X-Trace-Id"`，所以响应头里会出现：

```text
X-Trace-Id: 当前请求编号
```

### 练习 4

题目：

为什么 middleware 适合做 trace_id？

参考答案：

因为 trace_id 不是某一个接口独有的逻辑，而是所有请求都需要的通用逻辑。

middleware 会在路由函数前后执行，所以可以统一处理所有接口的 trace_id。

### 练习 5

题目：

为什么请求结束后要执行：

```python
reset_trace_id(token)
```

参考答案：

因为请求结束后要清理当前上下文，避免当前请求的 trace_id 影响后续代码或其他请求。

使用 `finally` 可以保证成功和失败都会清理。

### 练习 6

题目：

如果客户端请求头已经带了：

```text
X-Trace-Id: client-001
```

服务端应该重新生成还是复用？

参考答案：

当前实现会复用 `client-001`。

这样如果上游服务已经生成了 trace_id，下游 Python AI 服务可以继续使用同一个编号，方便跨服务追踪。

## 45. 本节自测

### 自测 1

题目：

`trace_id` 的核心作用是什么？

参考答案：

把同一次请求产生的多行日志串起来，方便定位问题。

### 自测 2

题目：

本项目使用哪个响应头返回 trace_id？

参考答案：

使用：

```text
X-Trace-Id
```

### 自测 3

题目：

`uuid4().hex` 会生成什么？

参考答案：

会生成一个随机 UUID，并转换成 32 位十六进制字符串。

### 自测 4

题目：

`ContextVar` 在本节里解决什么问题？

参考答案：

它用来保存当前请求上下文里的 trace_id，避免并发请求之间互相覆盖。

### 自测 5

题目：

`call_next(request)` 在 middleware 里有什么作用？

参考答案：

它把请求继续交给后面的路由函数处理，并返回路由生成的响应。

### 自测 6

题目：

为什么 middleware 里要记录 `request_started` 和 `request_finished`？

参考答案：

这样可以知道请求什么时候开始、什么时候结束、路径是什么、状态码是什么、耗时多久。

### 自测 7

题目：

`logger.exception()` 和 `logger.error()` 有什么常见区别？

参考答案：

`logger.exception()` 通常在 `except` 代码块里使用，它会记录错误日志并自动带上异常堆栈。

`logger.error()` 只记录错误级别日志，不一定带异常堆栈。

### 自测 8

题目：

为什么日志格式里要加：

```text
trace_id=%(trace_id)s
```

参考答案：

这样每条日志都会显示当前请求的 trace_id，排查问题时可以按 trace_id 搜索同一次请求的所有日志。

### 自测 9

题目：

本节测试如何证明 `/chat` 的多行日志属于同一次请求？

参考答案：

测试向 `/chat` 发送请求时带上固定的 `X-Trace-Id`，然后用 `caplog` 捕获日志，断言 middleware 和 `/chat` 产生的日志记录里 `record.trace_id` 都等于这个固定值。

### 自测 10

题目：

本节实现是不是完整的 OpenTelemetry 分布式追踪？

参考答案：

不是。

本节只是基础请求追踪：生成或复用 trace_id、写入响应头、注入日志。

完整分布式追踪还会涉及 `span_id`、`traceparent`、OpenTelemetry、Jaeger、Tempo 等工具。

## 46. 本节小结

这一节完成了请求追踪基础：

```text
理解 trace_id 的作用
理解 middleware
理解 ContextVar
生成 trace_id
复用客户端传入的 X-Trace-Id
响应头返回 X-Trace-Id
日志自动带 trace_id
测试 trace_id 行为
```

当前项目已经能把一次请求的多行日志串起来。

下一节学习：

```text
统一异常处理
```

到时候会把错误响应也变得稳定，并让错误响应里带上 trace_id。

## 47. 参考资料

- [FastAPI 官方文档：Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)
- [Python 官方文档：contextvars](https://docs.python.org/3/library/contextvars.html)
- [Python 官方文档：logging](https://docs.python.org/3/library/logging.html)
- [Python 官方文档：Logging Cookbook](https://docs.python.org/3/howto/logging-cookbook.html)
- [Python 官方文档：uuid](https://docs.python.org/3/library/uuid.html)
