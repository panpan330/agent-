# 阶段 2 第 17 节：测试模型调用：mock / fake LLM client

## 1. 这一节学什么

前面我们已经让项目具备了：

```text
真实 /chat 调用
多轮 history
timeout
retry
rate limit
错误映射
模型调用日志
/stream-chat 流式输出
/extract-ticket 结构化输出
```

这一节专门学习：

```text
模型调用怎么测试
```

你要学会：

```text
为什么自动化测试不能直接调用真实大模型
fake、mock、stub 是什么
为什么本项目优先用 fake client
fake OpenAI-compatible client 要模拟什么结构
怎么测试普通模型返回
怎么测试流式模型返回
怎么测试模型抛错
怎么测试请求参数是否传对
怎么测试日志不泄露敏感数据
FastAPI dependency_overrides 和 fake client 的区别
```

这一节非常重要。

因为 AI 应用不是“我手动调一次成功”就算工程化。

真正的工程化是：

```text
就算模型不在线，测试也能证明我们的业务代码是对的
```

## 2. 为什么不能在自动化测试里直接调用真实模型

真实模型调用有几个问题：

```text
会产生费用
依赖网络
依赖服务商状态
输出不完全稳定
速度慢
可能受 rate limit 影响
可能因为 key 过期失败
可能把测试数据发给外部服务
```

如果每次运行：

```powershell
uv run pytest -q
```

都真实调用模型，那么测试就会变得：

```text
慢
贵
不稳定
不适合频繁运行
```

所以自动化测试里通常不直接调真实模型。

真实模型调用可以留给：

```text
手动 smoke test
少量集成测试
上线前验收
专门的评测脚本
```

平时的单元测试和接口测试，应该使用 fake。

## 3. 先理解几个词

测试里经常出现这些词：

```text
dummy
stub
fake
mock
spy
```

初学时不用死记术语。

先按人话理解：

| 名称 | 人话理解 | 常见用途 |
| --- | --- | --- |
| dummy | 占位用的对象 | 传进去但不会真正用 |
| stub | 固定返回某个结果 | 让测试走成功或失败分支 |
| fake | 一个简化版可运行实现 | 模拟外部服务或数据库 |
| mock | 可以设置期待和断言调用行为的对象 | 检查某个函数是否被调用 |
| spy | 记录调用过程 | 检查参数、次数、顺序 |

本项目这节用的是：

```text
fake + spy
```

也就是：

```text
fake：模拟 OpenAI-compatible client
spy：记录每次 create(...) 的参数，方便测试断言
```

## 4. 为什么本项目优先用 fake client

Python 官方有 `unittest.mock`。

pytest 也有 `monkeypatch`。

这些都能替换真实依赖。

但本项目当前更适合手写 fake client。

原因是：

```text
OpenAI-compatible client 的结构比较固定
我们只需要模拟 chat.completions.create(...)
fake client 更直观，适合学习
fake client 可以复用到多个测试文件
fake client 可以同时模拟成功、流式、异常、usage
fake client 不需要理解太多 patch 细节
```

注意：

```text
不是 mock 不好
而是当前阶段 fake 更容易看懂和维护
```

以后项目复杂了，可以在某些地方使用 `unittest.mock` 或 `monkeypatch`。

## 5. 本节新增了什么

新增文件：

```text
projects/ai-service/tests/fakes.py
projects/ai-service/tests/test_fake_llm_client.py
```

修改文件：

```text
projects/ai-service/tests/test_llm_service.py
projects/ai-service/tests/test_structured_output_service.py
```

核心变化是：

```text
把原来分散在测试文件里的 FakeCompletions / FakeClient 抽出来
统一放到 tests/fakes.py
普通聊天测试和结构化输出测试共同复用
```

这就是测试代码的工程化整理。

## 6. 我们要模拟的真实结构

真实代码里调用模型是这样：

```python
client.chat.completions.create(
    model=...,
    messages=...,
)
```

流式调用是这样：

```python
client.chat.completions.create(
    model=...,
    messages=...,
    stream=True,
    stream_options={"include_usage": True},
)
```

结构化输出调用是这样：

```python
client.chat.completions.create(
    model=...,
    messages=...,
    response_format={"type": "json_object"},
)
```

所以 fake client 至少要模拟：

```text
client
client.chat
client.chat.completions
client.chat.completions.create(...)
```

这就是为什么 fake 不能只写一个普通函数。

它要长得像真实 SDK 对象。

## 7. `FakeOpenAICompatibleClient`

代码位置：

```text
projects/ai-service/tests/fakes.py
```

核心结构：

```python
class FakeOpenAICompatibleClient:
    def __init__(self, completions: FakeChatCompletions) -> None:
        self.completions = completions
        self.chat = SimpleNamespace(completions=completions)
```

这里用 `SimpleNamespace` 造出：

```text
client.chat.completions
```

也就是说：

```text
client.chat.completions.create(...)
```

会调用到我们自己的 fake completions。

这就是 fake 的关键：

```text
外形像真实对象
内部行为由测试控制
```

## 8. `FakeChatCompletions`

核心类：

```python
class FakeChatCompletions:
    def __init__(
        self,
        content: str | None = "模型回复",
        *,
        error: Exception | None = None,
        usage: object | None = None,
        stream_chunks: Iterable[object] | None = None,
    ) -> None:
        ...
```

它可以模拟四类情况：

| 参数 | 作用 |
| --- | --- |
| `content` | 普通模型回复内容 |
| `error` | 模拟模型调用抛异常 |
| `usage` | 模拟 token usage |
| `stream_chunks` | 模拟流式 chunk |

比如成功回复：

```python
completions = FakeChatCompletions(content="模型回复")
```

比如模型报错：

```python
completions = FakeChatCompletions(error=RuntimeError("provider failed"))
```

比如流式输出：

```python
completions = FakeChatCompletions(
    stream_chunks=[
        make_stream_chunk("你"),
        make_stream_chunk("好"),
    ]
)
```

## 9. fake 也要记录调用参数

`FakeChatCompletions` 里有：

```python
self.calls: list[dict[str, Any]] = []
```

每次调用：

```python
def create(self, **kwargs: Any) -> object:
    self.calls.append(kwargs)
    ...
```

这表示：

```text
模型调用参数会被保存下来
```

测试就可以检查：

```python
call = completions.calls[0]
assert call["model"] == "qwen-test"
assert call["messages"][0]["role"] == "system"
```

这件事很重要。

因为模型调用测试不只是测“返回了什么”。

还要测：

```text
我们有没有把正确参数发给模型
```

## 10. 为什么要断言调用参数

假设代码写错了：

```python
client.chat.completions.create(
    model="wrong-model",
    messages=[],
)
```

如果 fake 只返回固定结果，测试可能仍然通过。

但真实模型调用会出问题。

所以测试应该断言：

```text
model 是否正确
messages 是否正确
history 是否传入
stream=True 是否传入
stream_options 是否传入
response_format 是否传入
```

这是测试模型调用时的关键习惯。

## 11. 普通模型返回怎么测

测试示例：

```python
completions = FakeChatCompletions(content="  模型回复  ")
service = LLMChatService(
    Settings(llm_api_key="test-key", llm_model="qwen-test", _env_file=None),
    client=FakeOpenAICompatibleClient(completions),
)

reply = service.generate_reply("解释 FastAPI")
```

然后断言：

```python
assert reply == "模型回复"
assert completions.last_call["model"] == "qwen-test"
```

这里测试了两件事：

```text
模型回复会被 strip 去掉前后空格
调用模型时传了正确 model
```

## 12. 流式模型返回怎么测

流式输出不是一次返回完整字符串。

它是一块一块返回：

```python
stream_chunks=[
    make_stream_chunk("FastAPI"),
    make_stream_chunk(" 是"),
    make_stream_chunk(" Python Web 框架。"),
]
```

测试时：

```python
chunks = list(service.stream_reply("解释 FastAPI"))
```

断言：

```python
assert chunks == ["FastAPI", " 是", " Python Web 框架。"]
assert completions.last_call["stream"] is True
assert completions.last_call["stream_options"] == {"include_usage": True}
```

这说明：

```text
流式内容能被逐块提取
调用模型时确实开启了 stream
usage 选项也传对了
```

## 13. 结构化输出怎么测

结构化输出的 fake content 是一个 JSON 字符串：

```python
DEFAULT_TICKET_EXTRACTION_JSON = (
    '{"intent":"logistics","order_id":"A1001",'
    '"summary":"用户询问订单物流状态","urgency":"normal",'
    '"need_human_review":false}'
)
```

测试调用：

```python
completions = FakeChatCompletions(content=DEFAULT_TICKET_EXTRACTION_JSON)
service = StructuredOutputService(..., client=FakeOpenAICompatibleClient(completions))
```

断言：

```python
assert extraction.intent == TicketIntent.LOGISTICS
assert completions.last_call["response_format"] == {"type": "json_object"}
```

这里的重点是：

```text
不仅要测 JSON 能解析
还要测 JSON Mode 参数传对了
```

## 14. 错误怎么测

fake 可以直接抛异常：

```python
completions = FakeChatCompletions(error=RuntimeError("provider failed"))
```

业务代码应该把它映射成：

```text
LLM_CALL_FAILED
```

测试：

```python
with pytest.raises(AppException) as exc_info:
    service.generate_reply("解释 FastAPI")

assert exc_info.value.code == "LLM_CALL_FAILED"
assert exc_info.value.status_code == 502
```

这就是在测试：

```text
外部模型炸了，我们的服务不能直接把底层异常暴露给用户
```

## 15. OpenAI SDK 错误怎么测

真实 SDK 可能抛：

```text
APITimeoutError
RateLimitError
AuthenticationError
APIConnectionError
APIStatusError
```

这些错误对象通常需要带 request 或 response。

所以 `tests/fakes.py` 里提供了：

```python
def make_status_error(...)
```

它能构造类似真实 SDK 的状态码错误。

例如：

```python
make_status_error(AuthenticationError, 401)
```

这样就能测试：

```text
401 -> LLM_AUTHENTICATION_FAILED
429 -> LLM_RATE_LIMITED
404 -> LLM_RESOURCE_NOT_FOUND
```

这比随便抛 `Exception("bad")` 更接近真实情况。

## 16. token usage 怎么测

模型响应里可能带：

```text
usage.prompt_tokens
usage.completion_tokens
usage.total_tokens
```

fake 里有：

```python
make_usage(prompt_tokens=12, completion_tokens=7, total_tokens=19)
```

测试可以检查：

```text
extract_token_usage 能不能提取 usage
日志里有没有记录 token
流式最后一个 chunk 的 usage 能不能被识别
```

这能帮助我们以后做：

```text
成本统计
token 预算
调用监控
```

## 17. 日志怎么测

pytest 里有 `caplog`。

它可以捕获日志。

例如：

```python
caplog.set_level(logging.INFO, logger="app.services.llm_service")
...
messages = [record.getMessage() for record in caplog.records]
```

然后断言：

```python
assert any("llm_chat_succeeded" in message for message in messages)
assert all("test-key" not in message for message in messages)
assert all("解释 FastAPI" not in message for message in messages)
```

这说明：

```text
成功日志存在
日志不泄露 API key
日志不泄露完整用户输入
```

AI 项目里这个非常重要。

因为 prompt、用户消息、模型输出都可能含敏感信息。

## 18. FastAPI dependency_overrides 是什么

service 测试里，我们把 fake client 传给 service。

接口测试里，我们用 FastAPI 的：

```python
app.dependency_overrides
```

例如：

```python
app.dependency_overrides[get_llm_chat_service] = lambda: fake_service
```

意思是：

```text
测试时不要用真实 get_llm_chat_service
改用我提供的 fake_service
```

FastAPI 官方文档也推荐用这种方式覆盖依赖做测试。

它特别适合：

```text
不想真的调外部认证服务
不想真的调数据库
不想真的调模型 API
```

## 19. service fake 和 client fake 的区别

这两个容易混：

| 类型 | 用在哪里 | 模拟层级 |
| --- | --- | --- |
| fake service | API/router 测试 | 模拟整个业务服务 |
| fake client | service 测试 | 模拟外部 SDK client |

例如测试 `/chat` 接口时：

```text
router -> fake service
```

我们只关心：

```text
HTTP 状态码
请求体校验
响应 JSON
统一错误处理
```

测试 `LLMChatService` 时：

```text
service -> fake OpenAI client
```

我们关心：

```text
调用模型参数
模型响应解析
SDK 异常映射
日志
```

这就是分层测试。

## 20. 为什么不要所有测试都从 API 打到底

如果所有测试都从：

```text
HTTP -> router -> service -> real client -> real model
```

那测试会：

```text
慢
贵
不稳定
定位问题困难
```

分层测试更清楚：

```text
schema 测字段校验
service 测业务逻辑和模型调用
router 测 HTTP 行为
少量 smoke test 测真实外部服务
```

出了问题时，你更容易知道是哪层坏了。

## 21. 本项目现在的测试分层

当前项目大致是：

```text
test_chat_schema.py
-> 测 ChatRequest / ChatResponse / ChatMessage

test_structured_schema.py
-> 测 TicketExtraction / StructuredOutputResponse

test_llm_service.py
-> 测 LLMChatService + fake OpenAI-compatible client

test_structured_output_service.py
-> 测 StructuredOutputService + fake OpenAI-compatible client

test_chat_api.py
-> 测 /chat、/stream-chat、/extract-ticket + fake service

scripts/llm_compatible_smoke_test.py
-> 手动检查真实模型配置，可选真实调用
```

这就是一个比较健康的基础测试结构。

## 22. `tests/fakes.py` 为什么放在 tests 里

`tests/fakes.py` 只服务于测试。

它不应该放到：

```text
app/
```

原因是：

```text
app 是生产代码
tests 是测试代码
fake client 不是生产功能
```

这也是一个工程边界：

```text
测试辅助工具放 tests
业务运行代码放 app
```

## 23. fake client 不是越复杂越好

fake 的目标不是完整复刻 OpenAI SDK。

它只需要模拟当前项目用到的部分：

```text
普通 completion
stream completion
usage
错误
调用参数记录
```

如果 fake 写得和真实 SDK 一样复杂，维护成本会很高。

好的 fake 应该是：

```text
够用
简单
清晰
容易控制
容易断言
```

## 24. 什么时候用 monkeypatch

pytest 的 `monkeypatch` 可以临时替换：

```text
对象属性
字典项
环境变量
sys.path
```

例如你想测试环境变量：

```python
monkeypatch.setenv("LLM_API_KEY", "test-key")
```

或者替换某个函数：

```python
monkeypatch.setattr(module, "some_function", fake_function)
```

本项目现在很多地方通过构造函数传入 client：

```python
LLMChatService(settings, client=fake_client)
```

这种方式比 monkeypatch 更直接。

因为依赖是显式传进去的。

## 25. 什么时候用 unittest.mock

Python 官方的 `unittest.mock` 可以创建 Mock 对象，也可以用 `patch()` 临时替换模块里的对象。

它适合：

```text
想检查函数是否被调用
想检查调用次数
想快速替换某个对象
不想手写完整 fake 类
```

但 mock 也容易写得太“贴实现”。

如果测试只是在检查：

```text
某个内部函数被调用了 1 次
```

但不关心业务结果，测试可能会变脆。

所以初学阶段先记住：

```text
能用清晰 fake 表达业务行为时，优先用 fake
需要临时替换或断言调用细节时，再用 mock / monkeypatch
```

## 26. 一个好模型调用测试应该测什么

至少考虑：

```text
成功返回
空返回
坏响应结构
超时
限流
认证失败
权限失败
资源不存在
上游 5xx
网络连接失败
usage 提取
日志不泄露敏感信息
调用参数正确
```

结构化输出还要额外测：

```text
合法 JSON
非法 JSON
合法 JSON 但 schema 不匹配
response_format 是否正确
```

流式输出还要额外测：

```text
能逐块返回内容
忽略空 chunk
流开始前错误
流开始后错误
usage 出现在最后 chunk 时能识别
```

## 27. 这一节和后面 Agent 的关系

后面做 Agent 时，测试会更复杂。

因为 Agent 可能会：

```text
调用模型
决定工具
调用 Java API
查知识库
让用户确认
继续下一步
```

如果没有 fake，你很难稳定测试。

后面会出现更多 fake：

```text
fake LLM client
fake Java API client
fake vector store
fake tool result
fake user confirmation
```

所以这一节其实是在打基础。

你现在学的不是一个小技巧。

而是 AI 工程测试的基本方法。

## 28. 本节完成后你应该能解释什么

你应该能解释：

```text
为什么自动化测试不真实调用模型
fake 和 mock 的区别
为什么 fake client 要长得像真实 SDK
为什么要记录 completions.calls
为什么要断言 model/messages/stream/response_format
为什么 router 测试用 fake service
为什么 service 测试用 fake client
为什么日志也要测试
```

如果能讲清这些，你就不是只会“调 API”。

你开始理解：

```text
AI 调用也要像普通后端代码一样可测试
```

## 29. 本节练习

### 练习 1

题目：

为什么自动化测试里不应该默认真实调用大模型？

参考答案：

因为真实模型调用会产生费用、依赖网络和服务商状态、速度慢、输出不完全稳定，还可能受限流和 key 配置影响。

自动化测试应该快速、稳定、可重复，所以通常使用 fake client。

### 练习 2

题目：

fake client 要模拟 OpenAI-compatible client 的哪条调用链？

参考答案：

要模拟：

```text
client.chat.completions.create(...)
```

因为生产代码就是通过这条链路调用模型的。

### 练习 3

题目：

`FakeChatCompletions.calls` 有什么用？

参考答案：

它记录每次调用 `create(...)` 时传入的参数。

测试可以用它断言 `model`、`messages`、`stream`、`stream_options`、`response_format` 等参数是否传对。

### 练习 4

题目：

测试普通 `/chat` 调用时，为什么不仅要断言 `reply`，还要断言 `call["messages"]`？

参考答案：

因为 `reply` 只说明 fake 返回被处理了。

`call["messages"]` 才能证明我们把正确的 system/user/history 消息发给了模型。

### 练习 5

题目：

流式输出测试为什么要断言 `stream=True`？

参考答案：

因为如果没有传 `stream=True`，真实模型就不会按流式方式返回。

测试要确认服务代码真的开启了流式调用。

### 练习 6

题目：

结构化输出测试为什么要断言 `response_format={"type": "json_object"}`？

参考答案：

因为这是 JSON Mode 的关键参数。

如果漏传这个参数，模型更可能返回非 JSON 内容，结构化解析会变不稳定。

### 练习 7

题目：

router 测试为什么用 fake service，而不是 fake client？

参考答案：

router 测试关注 HTTP 层行为，例如请求体校验、响应格式、状态码和统一异常处理。

模型 client 是 service 层细节，所以 router 测试用 fake service 更清晰。

### 练习 8

题目：

service 测试为什么用 fake client，而不是 fake service？

参考答案：

service 测试要验证模型调用参数、模型响应解析、SDK 错误映射和日志。

这些都发生在 service 调用 client 的过程中，所以要用 fake client。

### 练习 9

题目：

为什么要测试日志里不包含 API key 和完整用户输入？

参考答案：

因为日志可能被长期保存、集中收集或多人查看。

API key 和完整用户输入可能包含敏感信息，不应该写入日志。

### 练习 10

题目：

fake client 是否需要完整复刻 OpenAI SDK 的所有功能？

参考答案：

不需要。

fake client 只需要模拟当前项目用到的行为，例如普通响应、流式响应、usage、错误和调用参数记录。

## 30. 本节自测

### 自测 1

题目：

本节新增的共享 fake 工具文件是什么？

参考答案：

`projects/ai-service/tests/fakes.py`。

### 自测 2

题目：

本节新增的 fake 工具测试文件是什么？

参考答案：

`projects/ai-service/tests/test_fake_llm_client.py`。

### 自测 3

题目：

`FakeOpenAICompatibleClient` 主要模拟什么？

参考答案：

模拟 OpenAI-compatible client 的 `.chat.completions.create(...)` 调用结构。

### 自测 4

题目：

`FakeChatCompletions(error=RuntimeError(...))` 用来测试什么？

参考答案：

用来模拟模型服务调用失败，测试业务代码是否能把底层异常映射成统一错误。

### 自测 5

题目：

`make_stream_chunk("你好")` 用来模拟什么？

参考答案：

用来模拟流式模型响应中的一个 chunk。

### 自测 6

题目：

FastAPI 的 `dependency_overrides` 适合测试哪一层？

参考答案：

适合测试 API/router 层，用 fake service 替换真实依赖。

### 自测 7

题目：

`caplog` 在本项目里主要用来测试什么？

参考答案：

用来捕获日志，检查成功/失败日志是否存在，以及日志是否没有泄露用户输入和 API key。

### 自测 8

题目：

测试模型调用参数时，至少应该关注哪些字段？

参考答案：

至少关注 `model`、`messages`，流式调用还要关注 `stream` 和 `stream_options`，结构化输出还要关注 `response_format`。

### 自测 9

题目：

真实模型调用完全不需要测吗？

参考答案：

不是。

真实模型调用可以通过手动 smoke test、少量集成测试或评测脚本来验证，但不应该作为普通自动化测试的默认方式。

### 自测 10

题目：

为什么 fake client 也要写测试？

参考答案：

因为 fake client 是多个测试依赖的测试工具。

如果 fake 本身行为错了，很多测试可能会误判，所以需要给共享 fake 工具写基本测试。

## 31. 本节小结

这一节完成了：

```text
理解为什么模型调用要用 fake 测试
理解 fake、mock、stub 的基础区别
新增共享 fake OpenAI-compatible client
测试普通 completion
测试 stream completion
测试模型错误
测试 OpenAI SDK 状态码错误构造
改造 LLMChatService 测试复用 fake 工具
改造 StructuredOutputService 测试复用 fake 工具
理解 router 测试和 service 测试的分层
```

最重要的一句话：

```text
AI 应用测试的重点不是让模型真的回答一次，而是验证我们的代码在各种模型返回和模型失败情况下都能正确处理。
```

下一节进入：

```text
阶段 2 第 18 节：阶段 2 项目整理
```

## 32. 参考资料

- [Python：unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [pytest：monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)
- [FastAPI：Testing Dependencies with Overrides](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
- [OpenAI：Create chat completion](https://developers.openai.com/api/reference/python/resources/chat/subresources/completions/methods/create/)
