# 阶段 2 第 7 节：第一次真实 `/chat` 调用

## 1. 这一节学什么

前面几节我们已经准备好了这些基础：

```text
LLM API 是什么
API key 和 .env 安全配置
token、上下文窗口和费用基础
OpenAI-compatible SDK client 怎么初始化
messages 是什么
prompt 怎么写清楚
```

这一节开始把这些东西真正接到 FastAPI 的 `/chat` 接口上。

本节要学：

```text
为什么要把 mock /chat 改成真实模型调用
真实 /chat 的请求流程是什么
router 层和 service 层分别负责什么
FastAPI Depends 是什么
依赖注入为什么适合测试
LLMChatService 怎么封装模型调用
怎么从 completion 里取出模型回复
没有 API key 时怎么返回统一错误
为什么测试不能真实调用模型
fake service / fake client 是什么
本地怎么手动调用真实 /chat
```

这一节是阶段 2 的重要转折点：

```text
之前 /chat 是后端自己拼一段假回复。
现在 /chat 开始调用真实大模型。
```

## 2. 从 mock 到真实调用

阶段 1 的 `/chat` 是 mock 接口。

意思是：

```text
它没有调用真实模型。
它只是把用户输入包装一下再返回。
```

原来的逻辑类似：

```python
return ChatResponse(reply=f"你刚才说的是：{request.message}")
```

这适合学习 HTTP、POST、请求体、响应体和测试。

但它不是 AI 服务。

真实 AI 服务至少需要：

```text
接收用户问题
构造 prompt
构造 messages
读取模型配置
初始化 SDK client
请求真实模型
解析模型响应
返回给前端
处理错误
记录日志
```

这一节就是把这条链路先跑通。

## 3. 当前真实 `/chat` 的整体流程

现在 `/chat` 的流程是：

```text
客户端
  |
  | POST /chat {"message": "..."}
  v
FastAPI router: app/routers/chat.py
  |
  | 调用 LLMChatService.generate_reply()
  v
LLM service: app/services/llm_service.py
  |
  | build_chat_prompt()
  | build_chat_messages()
  | create_openai_compatible_client()
  v
OpenAI-compatible SDK
  |
  | chat.completions.create(model=..., messages=...)
  v
阿里云百炼 / OpenAI-compatible 模型服务
  |
  | completion.choices[0].message.content
  v
ChatResponse(reply=...)
```

一句话：

```text
HTTP 层收到问题，service 层调用模型，最后把模型回复包装成 JSON 返回。
```

## 4. 为什么不把模型调用直接写在 router 里

初学时可能会想：

```text
既然 /chat 要调用模型，那直接在 chat.py 里写 SDK 调用不就行了吗？
```

小 demo 可以这样写。

但项目里不建议这样做。

原因是 router 层应该主要负责：

```text
接 HTTP 请求
校验请求体
调用业务逻辑
返回 HTTP 响应
```

模型调用属于业务逻辑和外部服务调用，更适合放到 service 层。

如果直接写在 router 里，会出现问题：

```text
router 文件越来越重
测试 /chat 时容易真实调用模型
模型错误处理和 HTTP 逻辑混在一起
以后多轮对话、RAG、streaming 不好扩展
```

所以本节新增：

```text
app/services/llm_service.py
```

让它专门负责模型调用。

## 5. router 层现在做什么

文件：

```text
projects/ai-service/app/routers/chat.py
```

核心代码：

```python
@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    llm_chat_service: LLMChatService = Depends(get_llm_chat_service),
) -> ChatResponse:
    logger.info("chat_requested message_length=%s", len(request.message))
    reply = llm_chat_service.generate_reply(request.message)
    return ChatResponse(reply=reply)
```

你先按顺序理解：

```text
@router.post("/chat")
```

表示这是一个 POST 接口。

```text
request: ChatRequest
```

表示请求体必须符合 `ChatRequest`。

```text
response_model=ChatResponse
```

表示响应体必须符合 `ChatResponse`。

```text
llm_chat_service: LLMChatService = Depends(...)
```

表示这个 service 不是你手动 new 出来的，而是交给 FastAPI 的依赖系统提供。

```text
llm_chat_service.generate_reply(request.message)
```

表示 router 把用户问题交给 service，自己不关心 SDK 细节。

## 6. FastAPI Depends 是什么

`Depends` 是 FastAPI 的依赖注入机制。

先用人话理解：

```text
这个函数运行前，需要先帮我准备一个东西。
```

比如：

```python
def chat(
    request: ChatRequest,
    llm_chat_service: LLMChatService = Depends(get_llm_chat_service),
) -> ChatResponse:
    ...
```

含义是：

```text
调用 chat 路由函数之前，
FastAPI 先调用 get_llm_chat_service，
把返回值传给 llm_chat_service 参数。
```

也就是：

```text
get_llm_chat_service() -> LLMChatService -> chat(..., llm_chat_service=这个对象)
```

## 7. 什么是依赖注入

依赖注入听起来很抽象。

拆开看：

```text
依赖：一个函数或类运行时需要用到的东西
注入：不是它自己创建，而是外部传进来
```

比如 `/chat` 需要一个 `LLMChatService`。

一种写法是自己创建：

```python
service = LLMChatService(settings)
```

另一种写法是外部注入：

```python
llm_chat_service: LLMChatService = Depends(get_llm_chat_service)
```

为什么后者好？

因为测试时可以替换：

```text
正式运行：注入真实 LLMChatService
测试运行：注入 FakeLLMChatService
```

这样测试不会真的调用模型。

## 8. get_llm_chat_service 做什么

文件：

```text
app/routers/chat.py
```

代码：

```python
def get_llm_chat_service(
    settings: Settings = Depends(get_settings),
) -> LLMChatService:
    return create_llm_chat_service(settings)
```

这段里又有一个依赖：

```text
settings: Settings = Depends(get_settings)
```

含义是：

```text
先读取项目配置 settings
再用 settings 创建 LLMChatService
```

最终链路是：

```text
get_settings()
  -> Settings
  -> create_llm_chat_service(settings)
  -> LLMChatService
  -> /chat 使用它
```

## 9. service 层现在做什么

文件：

```text
projects/ai-service/app/services/llm_service.py
```

它负责：

```text
构造清晰 prompt
构造 messages
检查 API key
创建 OpenAI-compatible client
调用 chat.completions.create
解析模型回复
把模型错误转换成 AppException
```

它不负责：

```text
读取 HTTP 请求体
设置 HTTP 状态码
返回 FastAPI response_model
处理 CORS
生成 trace_id
```

这就是分层。

## 10. build_chat_prompt 做什么

代码：

```python
def build_chat_prompt(user_message: str) -> str:
    return build_clear_user_prompt(
        PromptParts(
            task=user_message,
            constraints=DEFAULT_CHAT_CONSTRAINTS,
            output_format=DEFAULT_CHAT_OUTPUT_FORMAT,
            failure_policy=DEFAULT_CHAT_FAILURE_POLICY,
        )
    )
```

它把用户原始输入：

```text
请解释 FastAPI 是什么
```

整理成更清楚的 prompt：

```text
## 任务
请解释 FastAPI 是什么

## 要求
- 用中文回答
- 回答适合刚开始学习 AI 应用开发的人
- 解释概念时先讲人话，再补充术语
- 不要编造不确定的信息

## 输出格式
先直接回答用户问题，再在需要时补充关键要点。

## 无法完成时
如果不确定，请明确说不确定，并说明需要查官方文档。
```

这样做的目的：

```text
让模型更容易理解任务
让回答更适合当前学习阶段
降低胡乱编造的概率
```

## 11. build_chat_messages 做什么

代码：

```python
def build_chat_messages(user_message: str) -> list[ChatMessage]:
    return build_single_turn_messages(build_chat_prompt(user_message))
```

它做两步：

```text
1. 先把用户输入变成清晰 prompt
2. 再把 prompt 放进 user message
```

最终得到：

```text
system: 你是一个耐心的编程学习助手，回答要简洁清楚。
user:   带 ## 任务 / ## 要求 / ## 输出格式 的清晰 prompt
```

## 12. create_openai_compatible_client 做什么

文件：

```text
app/services/llm_client.py
```

它负责初始化 SDK client：

```python
OpenAI(
    api_key=...,
    base_url=...,
    timeout=...,
)
```

对 OpenAI 官方接口来说，通常只需要：

```text
api_key
```

对阿里云百炼 OpenAI 兼容接口来说，还需要：

```text
base_url
```

你的兼容模式地址类似：

```text
https://{WorkspaceId}.cn-beijing.maas.aliyuncs.com/compatible-mode/v1
```

注意：

```text
真实 WorkspaceId 和真实 API key 只放本机 .env，不写进笔记和 GitHub。
```

## 13. 真实调用的核心代码

`LLMChatService.generate_reply()` 里最核心的是：

```python
completion = self._get_client().chat.completions.create(
    model=self.settings.llm_model,
    messages=serialize_chat_messages(messages),
)
```

这就是 Chat Completions 风格接口的基本调用：

```text
model     使用哪个模型
messages 发送给模型的对话消息
```

OpenAI 官方 API reference 里，Chat Completions 的输入就是围绕 `model` 和 `messages` 这类参数组织。

阿里云百炼 OpenAI 兼容文档也给出了类似示例：

```python
client.chat.completions.create(
    model="qwen-plus",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "你是谁？"},
    ],
)
```

本项目只是把这些值从硬编码改成了：

```text
model    从 settings.llm_model 读取
messages 从 message_builder / prompt_builder 构造
api_key  从 .env 或环境变量读取
base_url 从 .env 或环境变量读取
```

## 14. completion 是什么

`completion` 可以理解成：

```text
模型服务返回的完整结果对象。
```

它不只包含文本。

通常还可能包含：

```text
id
model
choices
usage
finish_reason
```

最重要的回复文本一般在：

```python
completion.choices[0].message.content
```

拆开理解：

```text
choices       候选回答列表
choices[0]    第一个候选回答
message       这条候选回答的消息对象
content       模型真正回复的文本
```

为什么是列表？

因为有些模型接口支持一次生成多个候选回答。

我们当前只取第一个：

```text
choices[0]
```

## 15. extract_first_reply 做什么

代码：

```python
def extract_first_reply(completion: Any) -> str:
    try:
        reply = completion.choices[0].message.content
    except (AttributeError, IndexError, TypeError) as exc:
        raise AppException(
            code="LLM_BAD_RESPONSE",
            message="模型返回格式异常",
            status_code=502,
        ) from exc

    if not isinstance(reply, str) or not reply.strip():
        raise AppException(
            code="LLM_EMPTY_RESPONSE",
            message="模型返回了空内容",
            status_code=502,
        )
    return reply.strip()
```

它负责把模型返回对象变成普通字符串。

同时它做了两个保护：

```text
返回格式不对 -> LLM_BAD_RESPONSE
返回内容为空 -> LLM_EMPTY_RESPONSE
```

为什么要保护？

因为外部模型服务不是我们自己的代码。

外部服务可能：

```text
网络失败
限流
返回错误
返回空内容
返回结构变化
```

后端要有兜底。

## 16. 没有 API key 时怎么处理

现在如果本机没有配置：

```text
LLM_API_KEY
```

请求 `/chat` 会返回统一错误：

```json
{
  "code": "LLM_API_KEY_MISSING",
  "message": "LLM API key 未配置，请先在本机 .env 中配置 LLM_API_KEY。",
  "trace_id": "..."
}
```

状态码是：

```text
500
```

为什么不是 400？

因为用户请求本身没有错。

错的是服务端配置不完整。

所以这是服务端错误。

## 17. 模型调用失败时怎么处理

如果 SDK 调用时抛出异常，现在会转换成：

```json
{
  "code": "LLM_CALL_FAILED",
  "message": "模型调用失败，请稍后重试。",
  "trace_id": "..."
}
```

状态码是：

```text
502
```

为什么是 502？

因为后端服务还活着，但它调用上游模型服务失败了。

502 常用于表示：

```text
网关或服务调用上游失败。
```

当前只是基础处理。

后面第 11 节会专门讲：

```text
模型调用错误处理
```

到时候会把超时、认证失败、限流、模型不存在等情况拆得更细。

## 18. 为什么日志只记录 message_length

现在 router 日志是：

```python
logger.info("chat_requested message_length=%s", len(request.message))
```

它只记录用户输入长度，不记录完整内容。

原因是用户输入可能包含：

```text
API key
手机号
身份证号
订单号
公司内部资料
账号密码
```

日志通常会被保存很久，也可能被多人查看。

所以日志原则是：

```text
记录排查问题需要的信息。
不要记录敏感原文。
```

以后模型调用日志也会遵守这个原则。

## 19. 为什么测试不能真实调用模型

自动化测试必须满足：

```text
快
稳定
可重复
不依赖外部网络
不花真实费用
不需要真实密钥
```

如果测试真实调用模型，会出现问题：

```text
没有 key 时测试失败
网络波动时测试失败
模型回复变化导致断言不稳定
每次测试都可能产生费用
CI 上不能放真实 key
```

所以测试里不能真实调用 LLM。

本项目现在用 fake。

## 20. fake 是什么

fake 是测试里写的一个假对象。

它长得像真实对象，能被项目代码正常调用，但不会真的访问外部服务。

例如测试里的：

```python
class FakeLLMChatService:
    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.messages: list[str] = []

    def generate_reply(self, user_message: str) -> str:
        self.messages.append(user_message)
        return self.reply
```

它有真实 service 的同名方法：

```text
generate_reply
```

但它只是返回固定回复。

这样 `/chat` 测试可以验证：

```text
请求体能进来
router 会调用 service
响应体格式正确
用户输入传给了 service
```

但不会调用真实模型。

## 21. dependency_overrides 是什么

FastAPI 测试里可以这样替换依赖：

```python
app.dependency_overrides[get_llm_chat_service] = lambda: fake_service
```

意思是：

```text
正常情况下，get_llm_chat_service 会返回真实 LLMChatService。
测试时，请不要调用它，直接返回 fake_service。
```

这就是依赖注入的价值。

真实运行：

```text
get_llm_chat_service -> LLMChatService -> 真实 SDK -> 模型服务
```

测试运行：

```text
get_llm_chat_service -> FakeLLMChatService -> 固定假回复
```

## 22. fake service 和 fake client 的区别

本节用了两层 fake。

第一层：fake service。

用于测试 `/chat` 路由：

```text
我只想测 HTTP 接口，不想测 SDK 调用。
```

第二层：fake client。

用于测试 `LLMChatService`：

```text
我想测 service 是否正确调用 SDK 风格对象，但不想真的请求网络。
```

可以这样理解：

```text
测试 router -> fake service
测试 service -> fake client
```

这让每个测试只测自己该测的边界。

## 23. conftest.py 为什么也改了

文件：

```text
projects/ai-service/tests/conftest.py
```

现在测试创建 app 时使用：

```python
settings = Settings(_env_file=None)
test_app = create_app(settings)
test_app.dependency_overrides[get_settings] = lambda: settings
```

这很重要。

意思是：

```text
测试默认不读取本机真实 .env。
```

为什么？

因为你的本机 `.env` 可能有真实 API key。

测试不应该因为本机环境不同而表现不同。

也不应该误用真实 key。

所以测试使用：

```text
Settings(_env_file=None)
```

把 `.env` 文件排除掉。

## 24. create_app 为什么支持传 settings

现在应用入口支持：

```python
def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
```

正式运行时：

```python
app = create_app()
```

会读取真实配置。

测试运行时：

```python
app = create_app(Settings(_env_file=None))
```

可以传入测试专用配置。

这叫：

```text
让应用更容易测试。
```

## 25. 当前新增和修改的文件

本节主要新增：

```text
projects/ai-service/app/services/llm_service.py
projects/ai-service/tests/test_llm_service.py
notes/llm-api-stage2-07-real-chat-call.md
```

主要修改：

```text
projects/ai-service/app/routers/chat.py
projects/ai-service/app/main.py
projects/ai-service/scripts/llm_compatible_smoke_test.py
projects/ai-service/tests/conftest.py
projects/ai-service/tests/test_chat_api.py
projects/ai-service/tests/test_logging.py
projects/ai-service/tests/test_trace.py
```

## 26. 当前 `/chat` 请求体

请求：

```json
{
  "message": "请解释 FastAPI 是什么"
}
```

这部分没有变。

仍然由：

```text
ChatRequest
```

校验。

要求：

```text
message 必须是字符串
message 不能为空
```

## 27. 当前 `/chat` 响应体

成功响应：

```json
{
  "reply": "FastAPI 是一个用于构建 Python Web API 的框架..."
}
```

仍然由：

```text
ChatResponse
```

校验。

要求：

```text
reply 必须是非空字符串
```

## 28. 如何本地真实调用 `/chat`

第一步，确认本机 `.env` 存在：

```text
projects/ai-service/.env
```

如果还没有，就从示例复制：

```powershell
Copy-Item .env.example .env
```

第二步，在 `.env` 里配置真实值：

```text
LLM_PROVIDER="aliyun-compatible"
LLM_MODEL="你的模型名"
LLM_BASE_URL="你的 OpenAI-compatible base_url"
LLM_API_KEY="你的真实 key"
```

注意：

```text
真实 key 不要提交 GitHub。
真实 key 不要写进笔记。
真实 key 不要发到聊天里。
```

第三步，启动服务：

```powershell
uv run uvicorn app.main:app --reload
```

第四步，打开接口文档：

```text
http://127.0.0.1:8000/docs
```

找到：

```text
POST /chat
```

点击 `Try it out`，输入：

```json
{
  "message": "请用初学者能理解的方式解释 FastAPI 是什么"
}
```

然后执行。

## 29. 用 PowerShell 调用 `/chat`

服务启动后，也可以用 PowerShell：

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/chat" `
  -ContentType "application/json" `
  -Body '{"message":"请解释 FastAPI 是什么"}'
```

如果配置正确，会返回：

```text
reply
-----
模型生成的回答
```

如果没有配置 key，会返回：

```json
{
  "code": "LLM_API_KEY_MISSING",
  "message": "LLM API key 未配置，请先在本机 .env 中配置 LLM_API_KEY。",
  "trace_id": "..."
}
```

## 30. smoke test 脚本现在也复用 service

脚本：

```text
scripts/llm_compatible_smoke_test.py
```

现在真实调用时使用：

```python
print(LLMChatService(settings).generate_reply(args.prompt))
```

好处是：

```text
脚本和 /chat 复用同一套模型调用逻辑。
```

也就是说，以后改 prompt、messages、错误处理时，不需要在脚本和接口里改两遍。

## 31. 当前测试覆盖了什么

现在测试覆盖：

```text
/chat 可以返回 fake 模型回复
/chat 会把用户 message 传给 service
没有 LLM_API_KEY 时返回统一错误
请求体缺 message 时返回 VALIDATION_ERROR
message 为空时返回 VALIDATION_ERROR
message 类型不对时返回 VALIDATION_ERROR
GET /chat 返回 METHOD_NOT_ALLOWED
LLMChatService 会调用 OpenAI-compatible client 风格对象
LLMChatService 会构造清晰 prompt 和 messages
LLMChatService 会处理空模型回复
LLMChatService 会包装模型调用异常
日志和 trace_id 在 fake service 下仍能测试
```

这些测试不需要真实 API key。

也不会产生模型费用。

## 32. 为什么这节没有做 streaming

真实聊天接口有两种常见模式：

```text
非流式：等模型完整回答后一次性返回
流式：模型生成一点，前端收到一点
```

本节做的是非流式。

原因是：

```text
非流式更容易理解
更适合先打通配置、prompt、messages、response 解析
错误处理更简单
测试更直接
```

后面会单独学习：

```text
streaming 流式输出
FastAPI StreamingResponse
```

## 33. 为什么这节没有做重试

模型调用失败时，真实项目可能需要重试。

但重试不是随便加。

要考虑：

```text
哪些错误能重试
最多重试几次
每次等多久
会不会重复扣费
会不会让接口变慢
如何记录日志
```

本节先只做基础错误转换。

后面第 10 节会讲：

```text
重试 retry 和限流 rate limit 基础
```

## 34. 为什么这节没有统计真实 token

模型 API 返回结果里通常会包含：

```text
usage
```

里面可能有：

```text
prompt_tokens
completion_tokens
total_tokens
```

但不同兼容服务的字段可能略有差异。

本节先专注把 `/chat` 跑通。

后面会单独学习：

```text
模型调用日志：模型名、耗时、trace_id、token
```

到时候再读取 usage。

## 35. 常见错误 1：忘记配置 LLM_API_KEY

现象：

```text
POST /chat 返回 LLM_API_KEY_MISSING
```

原因：

```text
.env 里没有 LLM_API_KEY
或者 LLM_API_KEY 是空字符串
或者服务启动时没有读取到 .env
```

解决：

```text
确认 .env 在 projects/ai-service/.env
确认 LLM_API_KEY 有真实值
修改 .env 后重启 uvicorn
```

## 36. 常见错误 2：base_url 写错

现象可能是：

```text
模型调用失败
连接不上
404
认证失败
```

原因：

```text
LLM_BASE_URL 不完整
少了 /compatible-mode/v1
WorkspaceId 写错
地域不匹配
```

阿里云百炼北京地域的兼容地址形式是：

```text
https://{WorkspaceId}.cn-beijing.maas.aliyuncs.com/compatible-mode/v1
```

真实值以你控制台为准。

## 37. 常见错误 3：model 写错

现象可能是：

```text
模型不存在
服务不支持该模型
调用失败
```

原因：

```text
LLM_MODEL 和服务商支持的模型名不一致
模型没有开通
地域不支持
```

解决：

```text
去服务商官方模型列表确认当前可用模型名。
```

## 38. 常见错误 4：改了 .env 但没重启服务

`.env` 通常在应用启动时读取。

如果你服务已经启动，然后修改 `.env`：

```text
运行中的进程不一定会自动重新读取。
```

解决：

```text
停止 uvicorn
重新启动 uvicorn
```

## 39. 常见错误 5：把真实 key 写进代码

错误做法：

```python
api_key="sk-真实密钥"
```

正确做法：

```text
真实 key 放本机 .env 或系统环境变量
代码只读取 settings.llm_api_key
```

一旦真实 key 泄露：

```text
立即去服务商控制台撤销或重置。
```

## 40. 本节练习

### 练习 1

题目：

用自己的话解释：为什么 `/chat` 不应该直接在 router 里写 SDK 调用？

参考答案：

因为 router 主要负责 HTTP 请求和响应，SDK 调用属于业务逻辑和外部服务调用。

把 SDK 调用放在 service 层，可以让代码更清晰，也更容易测试、复用和扩展。

### 练习 2

题目：

`Depends(get_llm_chat_service)` 的作用是什么？

参考答案：

它告诉 FastAPI：调用路由函数前，先执行 `get_llm_chat_service`，把返回的 `LLMChatService` 对象传给路由参数。

### 练习 3

题目：

什么是依赖注入？

参考答案：

依赖注入就是一个函数或类需要用到的对象，不由它自己创建，而是由外部传进来。

这样正式运行时可以传真实对象，测试时可以传 fake 对象。

### 练习 4

题目：

当前真实模型调用的核心 SDK 方法是什么？

参考答案：

核心方法是：

```python
client.chat.completions.create(
    model=settings.llm_model,
    messages=messages,
)
```

### 练习 5

题目：

为什么测试不能真实调用模型？

参考答案：

因为真实调用依赖网络、API key、服务商状态和模型输出，还可能产生费用。

自动化测试应该快速、稳定、可重复，不依赖外部服务。

### 练习 6

题目：

fake service 和 fake client 的区别是什么？

参考答案：

fake service 用来测试 router，让 `/chat` 不真实调用 service。

fake client 用来测试 service，让 `LLMChatService` 不真实请求网络。

### 练习 7

题目：

`completion.choices[0].message.content` 表示什么？

参考答案：

它表示模型返回的第一个候选回答里的文本内容。

`choices` 是候选回答列表，`choices[0]` 是第一个候选，`message.content` 是具体回复文本。

### 练习 8

题目：

没有配置 `LLM_API_KEY` 时，为什么返回 500 而不是 400？

参考答案：

因为客户端请求格式没有错，问题是服务端缺少必要配置。

服务端配置错误属于服务端错误，所以使用 500。

### 练习 9

题目：

为什么日志只记录 `message_length`，不记录完整用户问题？

参考答案：

因为用户问题里可能包含敏感信息。

日志通常会长期保存，完整记录用户输入有泄露风险。

### 练习 10

题目：

按顺序写出当前 `/chat` 的调用链路。

参考答案：

```text
客户端 POST /chat
FastAPI router 接收 ChatRequest
router 通过 Depends 获得 LLMChatService
LLMChatService 构造 prompt
LLMChatService 构造 messages
LLMChatService 创建 OpenAI-compatible client
client.chat.completions.create 调用模型
extract_first_reply 解析模型回复
router 返回 ChatResponse
```

## 41. 本节自测

### 自测 1

题目：

当前 `/chat` 还是 mock 接口吗？

参考答案：

不是。

现在 `/chat` 会通过 `LLMChatService` 调用真实 OpenAI-compatible 模型服务。

但测试里会用 fake 替代真实服务。

### 自测 2

题目：

`LLMChatService` 属于哪一层？

参考答案：

属于 service 层。

它负责模型调用相关业务逻辑，不直接处理 HTTP 请求和响应。

### 自测 3

题目：

`build_chat_prompt` 的作用是什么？

参考答案：

它把用户原始输入整理成带任务、要求、输出格式和失败策略的清晰 prompt。

### 自测 4

题目：

`build_chat_messages` 的作用是什么？

参考答案：

它把清晰 prompt 包装成聊天模型需要的 messages，包含 system message 和 user message。

### 自测 5

题目：

`LLM_BAD_RESPONSE` 表示什么？

参考答案：

表示模型服务返回的数据结构不符合我们预期，导致无法从 `choices[0].message.content` 中取出回复。

### 自测 6

题目：

`LLM_EMPTY_RESPONSE` 表示什么？

参考答案：

表示模型返回了空字符串、全空格或非字符串内容。

### 自测 7

题目：

`LLM_CALL_FAILED` 表示什么？

参考答案：

表示请求模型服务时发生异常，比如网络失败、上游服务错误、认证失败或其他 SDK 异常。

### 自测 8

题目：

测试里为什么使用 `Settings(_env_file=None)`？

参考答案：

为了避免测试读取本机真实 `.env`，防止误用真实 API key，也让测试在不同机器上保持一致。

### 自测 9

题目：

修改 `.env` 后为什么通常要重启服务？

参考答案：

因为配置通常在应用启动时读取，运行中的进程不一定会自动重新加载 `.env`。

### 自测 10

题目：

下一节学习什么？

参考答案：

下一节学习多轮对话基础：历史消息怎么传。

## 42. 本节小结

这一节完成了：

```text
把 /chat 从 mock 回复改成真实模型调用
新增 LLMChatService
把 prompt_builder、message_builder、llm_client 串起来
使用 FastAPI Depends 注入 service
用 AppException 处理缺 key、空回复、坏响应和调用失败
测试中使用 fake service 和 fake client，避免真实调用模型
让 conftest.py 测试默认不读取本机 .env
让 smoke test 复用 LLMChatService
```

现在我们已经具备：

```text
一个能调用真实模型的 /chat 接口
一个可测试的 LLM service 层
一套不会误触发真实模型调用的测试方式
```

下一节进入：

```text
多轮对话基础：历史消息怎么传
```

## 43. 参考资料

- [OpenAI API Reference：Chat Completions](https://developers.openai.com/api/reference/resources/chat)
- [OpenAI 官方文档：Text generation](https://developers.openai.com/api/docs/guides/text)
- [OpenAI 官方文档：Prompt engineering](https://developers.openai.com/api/docs/guides/prompt-engineering)
- [阿里云百炼官方文档：通过 OpenAI SDK 调用千问模型](https://help.aliyun.com/zh/model-studio/compatibility-of-openai-with-dashscope)
- [FastAPI 官方文档：Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [FastAPI 官方文档：Testing Dependencies with Overrides](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
