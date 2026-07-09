# 阶段 2 第 14 节：FastAPI `StreamingResponse` 实现 `/stream-chat`

## 1. 这一节学什么

上一节我们学的是 streaming 概念。

这一节开始真正写代码，实现：

```text
POST /stream-chat
```

你要学会：

```text
怎么让 OpenAI-compatible SDK 开启 stream=True
怎么从流式 chunk 里提取 delta.content
怎么用 Python Iterator/yield 表达一段一段的输出
怎么用 FastAPI StreamingResponse 返回流式响应
怎么把文本块包装成 SSE event
为什么 /stream-chat 不使用 response_model
流开始前错误和流开始后错误怎么处理
怎么用 fake client 测试流式模型调用
怎么用 TestClient 测试 SSE 响应文本
```

本节不是只加一个接口。

更重要的是让你理解：

```text
模型端怎么流
后端怎么流
接口协议怎么设计
测试怎么隔离真实模型
```

## 2. 本节最终调用链路

本节新增的链路是：

```text
POST /stream-chat
-> app/routers/chat.py
-> LLMChatService.stream_reply()
-> client.chat.completions.create(..., stream=True)
-> 遍历模型返回的 chunk
-> 提取 chunk.choices[0].delta.content
-> StreamingResponse 逐块返回 SSE
```

和普通 `/chat` 对比：

```text
/chat        -> generate_reply() -> str -> JSON
/stream-chat -> stream_reply()   -> Iterator[str] -> text/event-stream
```

## 3. 为什么新增 `/stream-chat`

普通 `/chat` 返回完整 JSON：

```json
{
  "reply": "完整回答"
}
```

它适合：

```text
短回答
后端内部调用
需要一次性拿完整结果
接口逻辑简单
```

`/stream-chat` 返回一串事件：

```text
event: message
data: {"content":"FastAPI"}

event: message
data: {"content":" 是"}

event: done
data: {"trace_id":"..."}
```

它适合：

```text
聊天界面
长回答
边生成边展示
降低用户体感等待
```

所以这两个接口都保留。

它们解决的是不同场景。

## 4. 本节新增了哪些代码

主要改了两个文件：

```text
projects/ai-service/app/services/llm_service.py
projects/ai-service/app/routers/chat.py
```

测试改了：

```text
projects/ai-service/tests/test_llm_service.py
projects/ai-service/tests/test_chat_api.py
```

笔记就是当前文件：

```text
notes/llm-api-stage2-14-stream-chat-endpoint.md
```

## 5. service 层新增了什么

`llm_service.py` 新增了：

```text
extract_stream_delta_content(chunk)
has_token_usage(usage)
LLMChatService.stream_reply(...)
LLMChatService._iter_stream_reply_chunks(...)
流式成功日志
流式失败日志
```

service 层只关心：

```text
怎么调用模型
怎么读取模型 chunk
怎么把模型 chunk 变成文本片段
怎么记录模型调用日志
```

它不关心：

```text
SSE 格式
HTTP Content-Type
前端怎么接收
```

这就是分层。

## 6. router 层新增了什么

`chat.py` 新增了：

```text
format_sse_event(...)
build_stream_events(...)
POST /stream-chat
```

router 层关心：

```text
HTTP 请求体
HTTP 响应类型
SSE 事件格式
流开始后的 error event
```

它不直接解析模型返回的原始 chunk。

因为模型 chunk 是 service 层的职责。

## 7. 为什么 `stream_reply` 返回 Iterator[str]

普通方法：

```python
def generate_reply(...) -> str:
    ...
```

返回的是完整字符串。

流式方法：

```python
def stream_reply(...) -> Iterator[str]:
    ...
```

返回的是一个可以被遍历的对象。

你可以这样理解：

```text
str：一次性给你完整答案
Iterator[str]：你每次问它要下一小段
```

`StreamingResponse` 正好可以消费这种迭代器。

## 8. 为什么不能把 `stream_reply` 写成直接返回 list

如果写成：

```python
chunks = []
for chunk in stream:
    chunks.append(content)
return chunks
```

那就已经把模型输出全部攒完了。

前端还是要等完整结果。

真正的流式应该是：

```python
for chunk in stream:
    yield content
```

一边收到，一边返回。

## 9. `stream=True` 放在哪里

本节在模型调用时加了：

```python
stream = self._get_client().chat.completions.create(
    model=self.settings.llm_model,
    messages=serialize_chat_messages(messages),
    stream=True,
    stream_options={"include_usage": True},
)
```

重点是：

```text
stream=True
```

它告诉 OpenAI-compatible 接口：

```text
不要等完整回答生成完
生成一点就返回一点
```

`stream_options={"include_usage": True}` 的作用是：

```text
尽量让最后一个 chunk 带上 token usage
```

阿里云百炼文档明确说明，OpenAI 兼容流式输出默认不返回 usage，需要设置这个参数才会在最后数据块包含 token 消耗信息。

## 10. `message.content` 和 `delta.content`

非流式时，我们取完整回复：

```python
completion.choices[0].message.content
```

流式时，我们取增量内容：

```python
chunk.choices[0].delta.content
```

所以本节新增：

```python
extract_stream_delta_content(chunk)
```

它只做一件事：

```text
从一个流式 chunk 里提取这次新增的文本
```

## 11. 为什么提取函数要兼容对象和 dict

真实 SDK 返回的通常是对象：

```python
chunk.choices[0].delta.content
```

但测试里有时更方便模拟成字典：

```python
{
    "choices": [
        {
            "delta": {
                "content": "FastAPI"
            }
        }
    ]
}
```

所以 `extract_stream_delta_content` 同时支持对象和 dict。

这样测试更灵活。

## 12. 为什么空 chunk 要跳过

流式 chunk 不一定每次都有文本。

有些 chunk 可能只有：

```text
角色信息
结束原因
usage 信息
空内容
```

所以如果：

```python
content is None
content == ""
```

当前项目会跳过，不返回给前端。

这样前端只收到真正要显示的文本片段。

## 13. usage 怎么处理

流式 usage 通常不是每个 chunk 都有。

本节做法是：

```text
遍历每个 chunk
如果这个 chunk 有 usage，就保存下来
最后成功日志里记录 usage
```

也就是：

```python
chunk_usage = extract_token_usage(chunk)
if has_token_usage(chunk_usage):
    usage = chunk_usage
```

这也是为什么上一节先实现了：

```text
LLMTokenUsage
extract_token_usage
```

第 12 节给第 14 节铺了路。

## 14. SSE 格式怎么设计

本节选择了简单 SSE 格式：

```text
event: message
data: {"content":"文本片段"}

event: done
data: {"trace_id":"..."}
```

如果中途失败：

```text
event: error
data: {"code":"LLM_CALL_FAILED","message":"模型调用失败，请稍后重试。","trace_id":"..."}
```

当前有三个事件：

| event | 作用 |
| --- | --- |
| `message` | 一小段模型输出 |
| `done` | 正常结束 |
| `error` | 流开始后发生错误 |

这个协议简单、可测试、前端也容易处理。

## 15. `format_sse_event` 做什么

代码：

```python
def format_sse_event(event: str, data: dict[str, object]) -> str:
    json_data = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"event: {event}\ndata: {json_data}\n\n"
```

它把 Python 数据：

```python
event = "message"
data = {"content": "FastAPI"}
```

变成 SSE 文本：

```text
event: message
data: {"content":"FastAPI"}

```

最后的空行很重要。

SSE 用空行表示一个事件结束。

## 16. 为什么 data 里放 JSON

SSE 的 `data:` 本质是文本。

我们可以直接写：

```text
data: FastAPI
```

但用 JSON 更清楚：

```text
data: {"content":"FastAPI"}
```

以后要扩展字段也方便：

```json
{
  "content": "FastAPI",
  "index": 1
}
```

错误事件也可以复用：

```json
{
  "code": "LLM_CALL_FAILED",
  "message": "模型调用失败，请稍后重试。",
  "trace_id": "..."
}
```

## 17. 为什么 `/stream-chat` 不写 `response_model`

普通接口：

```python
@router.post("/chat", response_model=ChatResponse)
```

因为它返回完整 JSON。

流式接口：

```python
@router.post("/stream-chat")
def stream_chat(...) -> StreamingResponse:
    ...
```

因为它返回的是 `text/event-stream`。

这不是一个完整 JSON 响应。

所以不应该用 `response_model=ChatResponse`。

## 18. `StreamingResponse` 怎么用

本节代码：

```python
return StreamingResponse(
    build_stream_events(chunks, trace_id=get_trace_id()),
    media_type="text/event-stream",
)
```

含义是：

```text
build_stream_events(...) 负责一块一块 yield SSE 文本
StreamingResponse 负责把这些文本一块一块写进 HTTP 响应
media_type 告诉客户端这是 SSE 事件流
```

## 19. 为什么要捕获 trace_id

流式响应有个特殊点：

```text
路由函数返回 StreamingResponse 后，真正的 body 可能稍后才开始迭代
```

所以本节在创建流时把当前 `trace_id` 传给：

```python
build_stream_events(chunks, trace_id=get_trace_id())
```

这样即使后面发生流式错误，也能在 error event 里带上这次请求的 trace_id。

## 20. 流开始前错误怎么处理

例如没有 API key：

```text
LLM_API_KEY_MISSING
```

本节让 `stream_reply()` 在返回迭代器之前先检查：

```python
if not self.settings.has_llm_api_key:
    raise AppException(...)
```

因为这时还没有开始返回流。

FastAPI 统一异常处理器还能正常返回：

```json
{
  "code": "LLM_API_KEY_MISSING",
  "message": "...",
  "trace_id": "..."
}
```

## 21. 流开始后错误怎么处理

如果已经返回了第一段：

```text
event: message
data: {"content":"先返回一段"}
```

这时模型突然断了。

已经不能再改成完整 JSON 错误响应。

所以本节会返回：

```text
event: error
data: {"code":"LLM_CALL_FAILED","message":"模型调用失败，请稍后重试。","trace_id":"..."}
```

前端看到 `error` event 后，就可以停止追加文本，并显示错误状态。

## 22. 为什么流开始后状态码还是 200

因为 HTTP 响应头已经发出去了。

状态码也已经确定了。

所以流中途失败时，不能把状态码改成 502。

这就是流式接口和普通接口非常重要的区别。

普通接口：

```text
失败 -> HTTP 502 + JSON error
```

流式接口：

```text
已经开始 -> HTTP 200 + error event
```

这不是偷懒，是 HTTP 机制决定的。

## 23. 为什么自动化测试不真实调用模型

测试里仍然使用 fake client。

原因是：

```text
真实模型会产生费用
真实网络不稳定
真实服务商可能限流
真实模型输出不确定
测试应该快速、稳定、可重复
```

所以本节测试模拟：

```text
正常 chunk
空 chunk
usage chunk
创建 stream 时失败
stream 迭代中途失败
```

这样能覆盖核心逻辑，不需要真实请求模型。

## 24. service 层测试覆盖什么

`test_llm_service.py` 新增覆盖：

```text
extract_stream_delta_content 可以从对象 chunk 提取内容
extract_stream_delta_content 可以从 dict chunk 提取内容
空内容或缺失内容会被忽略
stream_reply 会传 stream=True
stream_reply 会传 stream_options={"include_usage": True}
stream_reply 会把 delta.content 逐块产出
stream_reply 会传递 history
stream_reply 会记录流式成功日志
stream_reply 会在缺少 API key 时提前失败
stream 创建失败会映射成 AppException
stream 迭代中途失败会映射成 AppException
```

这说明我们测的不只是“接口能返回”，还测了模型调用参数和异常分支。

## 25. router 层测试覆盖什么

`test_chat_api.py` 新增覆盖：

```text
/stream-chat 返回 text/event-stream
/stream-chat 返回 message 和 done 事件
/stream-chat 会把 history 传给 service
流开始前 AppException 返回统一 JSON 错误
流开始后 AppException 返回 SSE error 事件
/stream-chat 请求参数校验失败返回 422
GET /stream-chat 返回 405
```

这说明接口协议被测试锁住了。

以后改格式时，测试会提醒你。

## 26. 当前 `/stream-chat` 请求示例

请求体和 `/chat` 一样：

```json
{
  "message": "请解释 FastAPI 是什么"
}
```

多轮对话也一样：

```json
{
  "message": "那 FastAPI 呢？",
  "history": [
    {"role": "user", "content": "什么是 API？"},
    {"role": "assistant", "content": "API 是程序之间的接口。"}
  ]
}
```

区别在响应。

## 27. 当前 `/stream-chat` 响应示例

成功时：

```text
event: message
data: {"content":"FastAPI"}

event: message
data: {"content":" 是一个 Python Web 框架。"}

event: done
data: {"trace_id":"..."}

```

中途失败时：

```text
event: message
data: {"content":"先返回一段"}

event: error
data: {"code":"LLM_CALL_FAILED","message":"模型调用失败，请稍后重试。","trace_id":"..."}

```

## 28. 当前实现还有哪些边界

本节先做基础版本。

还没有做：

```text
前端页面
用户主动取消生成
客户端断开检测
更复杂的事件类型
流式 tool calling
流式 reasoning 内容
生产级监控指标
流式输出限速
```

这些以后再逐步补。

现在最重要的是：

```text
能跑通基本流式链路
能测住核心行为
知道错误边界
知道为什么这样分层
```

## 29. 和上一节的关系

第 13 节讲概念：

```text
streaming 是什么
chunk 是什么
SSE 是什么
StreamingResponse 是什么
```

第 14 节落代码：

```text
stream=True
delta.content
Iterator[str]
SSE event
/stream-chat
测试
```

这是正确的学习顺序。

先知道“为什么”，再写“怎么做”。

## 30. 你现在应该能解释什么

学完这一节，你应该能解释：

```text
/chat 和 /stream-chat 的区别
为什么 stream_reply 返回 Iterator[str]
为什么流式接口不使用 response_model
为什么 stream=True 只是模型端流式
为什么还需要 StreamingResponse
为什么 delta.content 不是完整回复
为什么流开始后错误不能变成 HTTP 502 JSON
为什么测试要用 fake stream
```

能讲清楚这些，说明你不是只会复制 `StreamingResponse`。

## 31. 本节练习

### 练习 1

题目：

请说明 `/chat` 和 `/stream-chat` 的核心区别。

参考答案：

`/chat` 等模型完整生成后返回一个完整 JSON。

`/stream-chat` 开启模型流式输出，把模型生成的一小段内容包装成 SSE event，逐块返回给客户端。

### 练习 2

题目：

为什么 `stream_reply()` 返回 `Iterator[str]`，而不是 `str`？

参考答案：

因为流式输出不是一次性得到完整字符串，而是每次得到一小段文本。

`Iterator[str]` 表示可以被逐步遍历，每次拿到一个字符串 chunk。

### 练习 3

题目：

`stream=True` 解决的是哪一段流式？

参考答案：

`stream=True` 解决的是模型服务到后端这一段流式。

如果要让前端也看到流式效果，后端还要用 `StreamingResponse` 把 chunk 继续逐块返回。

### 练习 4

题目：

为什么流式接口不能直接用 `response_model=ChatResponse`？

参考答案：

因为流式接口返回的是 `text/event-stream`，不是一个完整 JSON。

`ChatResponse` 适合普通 `/chat` 的完整 JSON 响应，不适合 SSE 流。

### 练习 5

题目：

本节为什么要写 `format_sse_event()`？

参考答案：

因为模型返回的是文本 chunk，前端需要一个清晰的事件协议。

`format_sse_event()` 把事件名和数据转换成 SSE 文本格式，例如 `event: message` 和 `data: {...}`。

### 练习 6

题目：

流开始前缺少 API key 时，应该返回什么？

参考答案：

应该由统一异常处理器返回普通 JSON 错误：

```json
{
  "code": "LLM_API_KEY_MISSING",
  "message": "...",
  "trace_id": "..."
}
```

因为此时流还没开始。

### 练习 7

题目：

流开始后模型中途失败，为什么不能再返回 HTTP 502 JSON？

参考答案：

因为响应头和部分响应体已经发给客户端，HTTP 状态码已经确定，不能再改成新的 JSON 响应。

所以只能在流里发送 `error` event，或者关闭连接并记录日志。

### 练习 8

题目：

为什么流式测试要用 fake client？

参考答案：

因为真实模型调用会产生费用、依赖网络、输出不稳定，还可能被限流。

fake client 可以稳定模拟 chunk、usage 和中途异常，让测试快速可重复。

### 练习 9

题目：

`stream_options={"include_usage": True}` 的作用是什么？

参考答案：

它让 OpenAI-compatible 流式输出尽量在最后一个 chunk 返回 token usage。

这样后端可以在流式成功日志里记录 `prompt_tokens`、`completion_tokens` 和 `total_tokens`。

### 练习 10

题目：

本节的 SSE 协议有哪三种 event？

参考答案：

```text
message
done
error
```

`message` 表示文本片段，`done` 表示正常结束，`error` 表示流开始后发生错误。

## 32. 本节自测

### 自测 1

题目：

当前 `/stream-chat` 的 HTTP 方法是什么？

参考答案：

```text
POST
```

### 自测 2

题目：

当前 `/stream-chat` 的 media type 是什么？

参考答案：

```text
text/event-stream
```

### 自测 3

题目：

模型端流式输出通过哪个参数开启？

参考答案：

```python
stream=True
```

### 自测 4

题目：

流式 chunk 的文本增量从哪个字段提取？

参考答案：

常见是：

```python
chunk.choices[0].delta.content
```

### 自测 5

题目：

当前项目的 `message` SSE event 里包含哪个字段？

参考答案：

```json
{
  "content": "文本片段"
}
```

### 自测 6

题目：

当前项目的 `done` SSE event 里包含哪个字段？

参考答案：

```json
{
  "trace_id": "..."
}
```

### 自测 7

题目：

流开始后的 `AppException` 会被转换成什么？

参考答案：

会被转换成 SSE `error` event。

### 自测 8

题目：

`/stream-chat` 是否允许客户端在 `history` 里传 `system` 消息？

参考答案：

不允许。

它复用 `ChatRequest`，所以和 `/chat` 一样会拒绝 history 里的 `system` 消息。

### 自测 9

题目：

当前自动化测试会真实调用模型吗？

参考答案：

不会。

测试使用 fake service 和 fake client 模拟模型行为。

### 自测 10

题目：

下一节学习什么？

参考答案：

下一节学习结构化输出是什么。

## 33. 本节小结

这一节完成了：

```text
新增 /stream-chat
新增 SSE 格式化工具
新增 StreamingResponse 流式返回
新增 LLMChatService.stream_reply()
新增 extract_stream_delta_content()
开启 OpenAI-compatible stream=True
开启 stream_options include_usage
新增流式成功/失败日志
补充 service 层流式测试
补充接口层 /stream-chat 测试
```

现在项目同时具备：

```text
普通完整聊天接口 /chat
流式聊天接口 /stream-chat
统一请求模型 ChatRequest
多轮 history
模型错误映射
trace_id
模型调用日志
fake 测试隔离
```

下一节进入：

```text
结构化输出是什么
```

## 34. 参考资料

- [OpenAI：Streaming API responses](https://developers.openai.com/api/docs/guides/streaming-responses)
- [OpenAI API Reference：Create chat completion](https://developers.openai.com/api/reference/python/resources/chat/subresources/completions/methods/create/)
- [OpenAI：Migrate to the Responses API](https://developers.openai.com/api/docs/guides/migrate-to-responses)
- [阿里云百炼：流式输出](https://help.aliyun.com/zh/model-studio/stream)
- [阿里云百炼：OpenAI兼容-Chat](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions)
- [FastAPI：StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/)
- [MDN：Using server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)
