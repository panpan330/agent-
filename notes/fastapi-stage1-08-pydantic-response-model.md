# FastAPI 阶段 1 第 8 节：Pydantic 响应模型

日期：2026-07-07

本节目标：学会用 Pydantic 定义服务端返回给客户端的数据结构。

上一节我们学了请求模型：

```python
class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
```

它描述的是：

```text
客户端发给服务端的数据结构。
```

这一节学习响应模型：

```python
class ChatResponse(BaseModel):
    reply: str = Field(min_length=1)
```

它描述的是：

```text
服务端返回给客户端的数据结构。
```

## 1. 本节学什么

本节学习这些内容：

1. 响应模型是什么。
2. 为什么响应也要定义模型。
3. `ChatResponse` 怎么写。
4. `reply` 字段是什么意思。
5. 请求模型和响应模型的区别。
6. `response_model` 是什么。
7. FastAPI 如何用响应模型生成文档。
8. FastAPI 如何用响应模型过滤多余字段。
9. 响应字段类型错了会怎样。
10. 为什么不能随便返回内部对象。
11. 如何给响应模型写测试。
12. 响应模型和 AI 服务有什么关系。

先记住一句话：

```text
请求模型管客户端发什么，响应模型管服务端回什么。
```

再记住一句话：

```text
响应模型是 API 对外承诺的返回结构。
```

## 2. 为什么响应也要有模型

你可能会问：

```text
服务端返回一个 dict 不就行了吗？
为什么还要 ChatResponse？
```

比如：

```python
return {"reply": "你好"}
```

确实可以返回。

但真实项目里，响应模型能解决这些问题：

```text
1. 明确告诉前端/Java 后端：接口会返回哪些字段。
2. 防止返回字段乱变。
3. 防止把内部字段、敏感字段暴露出去。
4. 让 /docs 自动文档更准确。
5. 让测试更明确。
6. 让代码可读性更好。
```

所以响应模型不是为了写得复杂。

它是为了：

```text
让接口输出稳定、清晰、可维护。
```

## 3. 本节新增了哪些代码

修改文件：

```text
projects/ai-service/app/schemas/chat.py
```

新增：

```python
class ChatResponse(BaseModel):
    reply: str = Field(
        min_length=1,
        description="Reply returned by the AI service.",
    )
```

修改测试：

```text
projects/ai-service/tests/test_chat_schema.py
```

新增了 `ChatResponse` 相关测试。

## 4. `ChatResponse` 是什么

代码：

```python
class ChatResponse(BaseModel):
    reply: str = Field(
        min_length=1,
        description="Reply returned by the AI service.",
    )
```

`ChatResponse` 是聊天接口的响应模型。

它描述的是后面 `/chat` 可能返回：

```json
{
  "reply": "你刚才说的是：请解释 FastAPI 是什么"
}
```

也就是说：

```text
ChatResponse 是服务端返回给客户端的 JSON 结构。
```

## 5. `reply` 字段是什么

`reply` 是响应字段。

它表示：

```text
AI 服务返回给用户的回复内容。
```

当前规则：

```python
reply: str = Field(min_length=1)
```

含义：

```text
reply 必须是字符串。
reply 不能是空字符串。
```

为什么不能是空字符串？

因为聊天接口如果返回：

```json
{
  "reply": ""
}
```

客户端虽然收到了响应，但没有任何有效内容。

这通常不是我们想要的结果。

## 6. 请求模型和响应模型的区别

请求模型：

```python
class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
```

它管：

```text
客户端 -> 服务端
```

响应模型：

```python
class ChatResponse(BaseModel):
    reply: str = Field(min_length=1)
```

它管：

```text
服务端 -> 客户端
```

对比：

| 模型 | 方向 | 谁提供数据 | 谁接收数据 |
| --- | --- | --- | --- |
| `ChatRequest` | 客户端到服务端 | 客户端 | FastAPI 服务 |
| `ChatResponse` | 服务端到客户端 | FastAPI 服务 | 客户端 |

简单记：

```text
Request 是进来的。
Response 是出去的。
```

## 7. 为什么字段名不都叫 message

请求里是：

```json
{
  "message": "你好"
}
```

响应里是：

```json
{
  "reply": "你刚才说的是：你好"
}
```

为什么不都叫 `message`？

因为含义不同。

```text
message = 用户发来的消息。
reply = 服务端返回的回复。
```

字段名应该表达业务含义。

如果都叫 `message`，前端或 Java 调用方容易分不清：

```text
这是用户消息，还是 AI 回复？
```

## 8. `response_model` 是什么

等后面写 `/chat` 接口时，会用到：

```python
@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    return {"reply": f"你刚才说的是：{request.message}"}
```

这里的：

```python
response_model=ChatResponse
```

告诉 FastAPI：

```text
这个接口的响应应该符合 ChatResponse 结构。
```

FastAPI 会用它做几件事：

```text
1. 生成 OpenAPI 文档。
2. 在 /docs 中展示响应结构。
3. 序列化响应数据。
4. 过滤掉响应中不应该暴露的多余字段。
5. 帮助检查响应结构是否符合预期。
```

## 9. response_model 和返回类型注解的区别

有时你会看到：

```python
def chat(request: ChatRequest) -> ChatResponse:
    ...
```

也会看到：

```python
@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    ...
```

初学阶段先优先理解：

```text
response_model 是 FastAPI 路由层明确声明响应模型的方式。
```

以后我们可以同时写：

```python
@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    ...
```

但现在先不要纠结太多。

核心是：

```text
FastAPI 需要知道响应结构是什么。
ChatResponse 就是响应结构。
```

## 10. 响应模型会进入 /docs

如果接口写：

```python
@router.post("/chat", response_model=ChatResponse)
```

FastAPI 会在：

```text
http://127.0.0.1:8000/docs
```

里展示响应模型。

调用方能看到：

```json
{
  "reply": "string"
}
```

这很重要。

因为前端或 Java 后端调用接口时，不应该靠猜返回结构。

自动文档能告诉他们：

```text
这个接口返回 reply 字段。
reply 是字符串。
```

## 11. 响应模型会过滤多余字段

FastAPI 官方文档强调，`response_model` 会用于输出数据的转换和过滤。

例如接口内部返回：

```python
return {
    "reply": "你好",
    "internal_prompt": "hidden system prompt",
    "api_key": "secret",
}
```

如果声明：

```python
response_model=ChatResponse
```

而 `ChatResponse` 只有：

```python
reply: str
```

那么响应给客户端时，只应该暴露：

```json
{
  "reply": "你好"
}
```

这对 AI 服务很重要。

因为内部可能有：

```text
system prompt
模型参数
trace 信息
内部错误细节
token 成本
密钥
```

这些不一定都应该返回给客户端。

响应模型可以帮助控制边界。

## 12. 响应模型不是安全万能药

虽然响应模型能过滤字段，但不要把安全全部寄托在它身上。

你仍然应该：

```text
不要把密钥放进返回对象。
不要随便返回内部异常。
不要把完整 prompt 暴露给用户。
不要返回不该给前端的数据。
```

响应模型是接口边界的一层保护。

但良好的业务代码也必须自己控制返回内容。

## 13. 响应字段类型错了会怎样

`ChatResponse` 要求：

```python
reply: str
```

如果你创建：

```python
ChatResponse(reply=123)
```

当前 Pydantic 会认为这不符合 `str` 类型要求，并抛出 `ValidationError`。

如果以后接口声明了：

```python
response_model=ChatResponse
```

但你返回的数据无法符合这个模型，FastAPI 可能会在响应处理阶段报错。

所以响应模型也能帮我们发现：

```text
服务端返回的数据结构不对。
```

## 14. 为什么响应错误更严重

请求错了，通常是客户端传错。

响应错了，通常是服务端代码写错。

例如：

```text
客户端少传 message -> 请求错误。
服务端返回 reply=123 -> 服务端错误。
```

所以响应模型校验失败时，通常应该被开发者尽快修复。

这也是为什么给响应模型写测试有价值。

## 15. 本节测试代码

文件：

```text
projects/ai-service/tests/test_chat_schema.py
```

现在导入：

```python
from app.schemas.chat import ChatRequest, ChatResponse
```

响应模型测试包括：

```text
正常 reply 可以创建。
缺少 reply 会失败。
空 reply 会失败。
非字符串 reply 会失败。
```

## 16. 测试：正常 reply

代码：

```python
def test_chat_response_accepts_reply() -> None:
    response = ChatResponse(reply="你刚才说的是：请解释 FastAPI 是什么")

    assert response.reply == "你刚才说的是：请解释 FastAPI 是什么"
```

这个测试验证：

```text
reply 是非空字符串时，ChatResponse 可以正常创建。
```

## 17. 测试：缺少 reply

代码：

```python
def test_chat_response_rejects_missing_reply() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ChatResponse()

    error = exc_info.value.errors()[0]
    assert error["loc"] == ("reply",)
    assert error["type"] == "missing"
```

这个测试验证：

```text
reply 是必填字段。
不传 reply 会抛 ValidationError。
```

## 18. 测试：空 reply

代码：

```python
def test_chat_response_rejects_empty_reply() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ChatResponse(reply="")

    error = exc_info.value.errors()[0]
    assert error["loc"] == ("reply",)
    assert error["type"] == "string_too_short"
```

这个测试验证：

```text
reply 不能是空字符串。
因为 Field(min_length=1) 要求至少 1 个字符。
```

## 19. 测试：非字符串 reply

代码：

```python
def test_chat_response_rejects_non_string_reply() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ChatResponse(reply=123)

    error = exc_info.value.errors()[0]
    assert error["loc"] == ("reply",)
    assert error["type"] == "string_type"
```

这个测试验证：

```text
reply 必须是字符串。
传数字会被拒绝。
```

## 20. model_dump 对响应模型也有用

可以这样：

```python
response = ChatResponse(reply="你好")
data = response.model_dump()
```

得到：

```python
{
    "reply": "你好",
}
```

后面如果接口函数返回 `ChatResponse` 对象，FastAPI 可以把它序列化成 JSON。

## 21. AI 服务为什么更需要响应模型

AI 输出有一个特点：

```text
不稳定。
```

如果我们随便把模型输出原样返回，可能出现：

```text
字段名变了。
多了不该返回的字段。
少了前端需要的字段。
类型变了。
格式不稳定。
```

响应模型可以帮助我们把对外接口稳定下来。

例如无论内部模型怎么处理，对外都承诺：

```json
{
  "reply": "string"
}
```

以后做结构化输出时，这一点会更重要。

## 22. 响应模型和结构化输出

后面我们会学习：

```text
structured output
```

也就是让大模型输出固定结构。

例如工单提取：

```json
{
  "title": "无法登录",
  "priority": "high",
  "category": "account"
}
```

这类能力离不开模型定义。

所以现在学 `ChatResponse`，不是只为了一个简单 reply。

它是在为后面的：

```text
RAG 答案结构
工单字段结构
工具调用结果结构
```

打基础。

## 23. 和 Java DTO 的类比

Java 里可能有：

```java
public class ChatResponse {
    private String reply;
}
```

FastAPI / Pydantic 里是：

```python
class ChatResponse(BaseModel):
    reply: str = Field(min_length=1)
```

类比：

| Java | Python / Pydantic |
| --- | --- |
| Response DTO | 响应模型 |
| `String reply` | `reply: str` |
| Bean Validation | `Field()` 约束 |
| Swagger 响应文档 | FastAPI `/docs` |

差别是：

```text
Python 本身是动态语言。
Pydantic 会在运行时根据类型提示做校验和序列化。
```

## 24. 请求模型和响应模型是否可以共用

有些场景可以共用。

但很多场景不建议共用。

例如用户创建账号：

请求可能包含：

```json
{
  "username": "panpan",
  "password": "123456"
}
```

响应绝对不应该返回：

```json
{
  "username": "panpan",
  "password": "123456"
}
```

所以请求模型和响应模型经常要分开。

当前聊天接口也是分开的：

```text
ChatRequest  有 message。
ChatResponse 有 reply。
```

这样语义更清楚。

## 25. 常见错误

### 错误 1：响应结构随便返回

不推荐：

```python
return {"a": "hello"}
```

前端或 Java 后端不知道 `a` 是什么意思。

推荐：

```python
return {"reply": "hello"}
```

并定义：

```python
class ChatResponse(BaseModel):
    reply: str
```

### 错误 2：把内部字段返回给客户端

危险：

```python
return {
    "reply": "hello",
    "system_prompt": "...",
    "api_key": "...",
}
```

接口返回前要明确：

```text
哪些字段可以给客户端？
哪些字段只能内部使用？
```

### 错误 3：请求模型和响应模型混用

不推荐为了省事到处复用同一个模型。

请求和响应的方向不同，职责不同。

字段也经常不同。

### 错误 4：以为响应模型只影响文档

不止。

FastAPI 的 `response_model` 还会参与输出数据转换和过滤。

### 错误 5：响应模型不写测试

响应模型也可能出错。

比如忘了必填字段、类型写错、空字符串没限制。

所以核心响应模型也应该测试。

## 26. 本节必须掌握的最小知识

这一节最少要掌握：

```text
响应模型描述服务端返回给客户端的数据结构。
ChatResponse 是聊天接口的响应模型。
reply 是服务端返回的回复字段。
response_model 用来告诉 FastAPI 响应应该符合哪个模型。
响应模型会进入 /docs 文档。
响应模型可以过滤多余字段。
响应模型能帮助稳定接口输出。
请求模型和响应模型通常要分开。
```

## 27. 本节练习

### 练习 1：解释响应模型

题目：

用自己的话解释：

```text
什么是 Pydantic 响应模型？
```

### 练习 2：区分请求模型和响应模型

题目：

说明下面两个模型分别负责什么：

```python
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
```

### 练习 3：解释 reply 字段

题目：

解释下面代码的含义：

```python
reply: str = Field(min_length=1)
```

### 练习 4：判断响应是否有效

题目：

根据当前 `ChatResponse`，判断下面响应是否有效：

A：

```json
{
  "reply": "你好"
}
```

B：

```json
{}
```

C：

```json
{
  "reply": ""
}
```

D：

```json
{
  "reply": 123
}
```

### 练习 5：解释 response_model

题目：

用自己的话解释：

```python
@router.post("/chat", response_model=ChatResponse)
```

里的 `response_model=ChatResponse` 有什么作用？

### 练习 6：解释字段过滤

题目：

如果接口内部返回：

```python
{
    "reply": "你好",
    "internal_prompt": "hidden",
}
```

但声明了：

```python
response_model=ChatResponse
```

为什么客户端不应该看到 `internal_prompt`？

### 练习 7：设计一个响应模型

题目：

设计一个 `HealthResponse` 响应模型，包含：

```text
status: str
service: str
time: str
```

## 28. 本节练习参考答案

### 练习 1 参考答案：解释响应模型

题目：

用自己的话解释：

```text
什么是 Pydantic 响应模型？
```

参考答案：

Pydantic 响应模型是用 Python 类描述服务端返回给客户端的数据结构。

它规定响应里有哪些字段、字段类型是什么、是否允许为空，以及文档里如何展示。

### 练习 2 参考答案：区分请求模型和响应模型

题目：

说明下面两个模型分别负责什么：

```python
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
```

参考答案：

`ChatRequest` 负责客户端发给服务端的数据。

`message` 是用户输入。

`ChatResponse` 负责服务端返回给客户端的数据。

`reply` 是服务端生成的回复。

### 练习 3 参考答案：解释 reply 字段

题目：

解释下面代码的含义：

```python
reply: str = Field(min_length=1)
```

参考答案：

这表示响应模型里有一个字段叫 `reply`。

规则是：

```text
reply 必须是字符串。
reply 是必填字段。
reply 长度至少是 1，不能是空字符串。
```

### 练习 4 参考答案：判断响应是否有效

题目：

根据当前 `ChatResponse`，判断下面响应是否有效：

A：

```json
{
  "reply": "你好"
}
```

B：

```json
{}
```

C：

```json
{
  "reply": ""
}
```

D：

```json
{
  "reply": 123
}
```

参考答案：

| 响应 | 是否有效 | 原因 |
| --- | --- | --- |
| A | 有效 | `reply` 是非空字符串 |
| B | 无效 | 缺少必填字段 `reply` |
| C | 无效 | `reply` 是空字符串，不满足 `min_length=1` |
| D | 无效 | `reply` 不是字符串 |

### 练习 5 参考答案：解释 response_model

题目：

用自己的话解释：

```python
@router.post("/chat", response_model=ChatResponse)
```

里的 `response_model=ChatResponse` 有什么作用？

参考答案：

它告诉 FastAPI：

```text
这个接口返回的数据应该符合 ChatResponse 结构。
```

FastAPI 会用它生成接口文档、序列化响应、过滤多余字段，并帮助检查响应结构。

### 练习 6 参考答案：解释字段过滤

题目：

如果接口内部返回：

```python
{
    "reply": "你好",
    "internal_prompt": "hidden",
}
```

但声明了：

```python
response_model=ChatResponse
```

为什么客户端不应该看到 `internal_prompt`？

参考答案：

因为 `ChatResponse` 只声明了 `reply` 字段。

`internal_prompt` 不属于对外响应模型。

FastAPI 使用 `response_model` 时，会按响应模型控制输出结构，多余字段不应该暴露给客户端。

这可以避免泄露内部实现细节。

### 练习 7 参考答案：设计一个响应模型

题目：

设计一个 `HealthResponse` 响应模型，包含：

```text
status: str
service: str
time: str
```

参考答案：

```python
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    time: str
```

如果想加字段说明，也可以写：

```python
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(description="Service status.")
    service: str = Field(description="Service name.")
    time: str = Field(description="Current server time in ISO format.")
```

## 29. 自测问题

1. 响应模型描述的是哪一方向的数据？
2. `ChatResponse` 当前有哪些字段？
3. `reply: str` 表示什么？
4. `Field(min_length=1)` 对 `reply` 有什么作用？
5. 请求模型和响应模型有什么区别？
6. 为什么请求模型和响应模型经常不共用？
7. `response_model` 有什么作用？
8. 响应模型会不会影响 `/docs`？
9. 响应模型为什么能帮助过滤多余字段？
10. 为什么不能随便返回内部字段？
11. AI 服务为什么更需要稳定响应结构？
12. 响应模型校验失败通常说明客户端错了还是服务端错了？
13. `model_dump()` 对响应模型有什么用？
14. 第 9 节模拟 `/chat` 会怎样使用 `ChatRequest` 和 `ChatResponse`？

## 30. 自测参考答案

### 自测 1 参考答案

题目：

响应模型描述的是哪一方向的数据？

答案：

响应模型描述服务端返回给客户端的数据结构。

### 自测 2 参考答案

题目：

`ChatResponse` 当前有哪些字段？

答案：

当前只有一个字段：

```text
reply
```

它表示服务端返回的聊天回复。

### 自测 3 参考答案

题目：

`reply: str` 表示什么？

答案：

它表示 `reply` 字段应该是字符串。

### 自测 4 参考答案

题目：

`Field(min_length=1)` 对 `reply` 有什么作用？

答案：

它要求 `reply` 字符串长度至少是 1，因此空字符串会被拒绝。

### 自测 5 参考答案

题目：

请求模型和响应模型有什么区别？

答案：

请求模型描述客户端发给服务端的数据结构。

响应模型描述服务端返回给客户端的数据结构。

### 自测 6 参考答案

题目：

为什么请求模型和响应模型经常不共用？

答案：

因为请求和响应方向不同，字段含义和安全边界也不同。

例如请求可能包含密码、内部参数，响应不应该返回这些字段。

### 自测 7 参考答案

题目：

`response_model` 有什么作用？

答案：

`response_model` 告诉 FastAPI 接口响应应该符合哪个模型。

FastAPI 会用它生成文档、序列化响应、过滤输出字段，并检查响应结构。

### 自测 8 参考答案

题目：

响应模型会不会影响 `/docs`？

答案：

会。

FastAPI 会把响应模型写进 OpenAPI schema，并在 `/docs` 中展示响应结构。

### 自测 9 参考答案

题目：

响应模型为什么能帮助过滤多余字段？

答案：

因为 `response_model` 声明了对外允许返回的字段。

FastAPI 生成响应时会按模型结构处理输出，不属于模型的字段不应该暴露给客户端。

### 自测 10 参考答案

题目：

为什么不能随便返回内部字段？

答案：

内部字段可能包含 system prompt、密钥、调试信息、模型参数、内部 trace 等。

这些信息不一定适合暴露给前端或外部调用方。

### 自测 11 参考答案

题目：

AI 服务为什么更需要稳定响应结构？

答案：

AI 内部输出可能不稳定。

响应模型可以让外部 API 保持稳定，比如始终返回 `reply` 字段，而不是让前端猜返回格式。

### 自测 12 参考答案

题目：

响应模型校验失败通常说明客户端错了还是服务端错了？

答案：

通常说明服务端代码错了。

因为响应数据是服务端生成的，如果不符合响应模型，说明服务端返回结构不符合自己的接口承诺。

### 自测 13 参考答案

题目：

`model_dump()` 对响应模型有什么用？

答案：

`model_dump()` 可以把 Pydantic 响应模型对象转换成 Python 字典。

例如：

```python
ChatResponse(reply="你好").model_dump()
```

得到：

```python
{"reply": "你好"}
```

### 自测 14 参考答案

题目：

第 9 节模拟 `/chat` 会怎样使用 `ChatRequest` 和 `ChatResponse`？

答案：

会用 `ChatRequest` 接收和校验客户端请求体。

会用 `ChatResponse` 定义接口返回结构。

大概形式是：

```python
@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return ChatResponse(reply=f"你刚才说的是：{request.message}")
```

## 31. 本节小结

这一节完成了响应模型：

```text
ChatRequest  管输入。
ChatResponse 管输出。
```

当前代码：

```python
class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    reply: str = Field(min_length=1)
```

后面 `/chat` 接口会把它们串起来：

```text
客户端 JSON body
        ↓
ChatRequest 校验
        ↓
接口函数处理
        ↓
ChatResponse 返回
        ↓
FastAPI 输出 JSON
```

下一节学习：

```text
模拟 /chat 接口
```

下一节会真正新增：

```text
app/routers/chat.py
POST /chat
response_model=ChatResponse
chat router 测试
```

## 32. 参考资料

- [FastAPI：Response Model - Return Type](https://fastapi.tiangolo.com/tutorial/response-model/)
- [FastAPI：Custom Response](https://fastapi.tiangolo.com/advanced/custom-response/)
- [FastAPI：Return a Response Directly](https://fastapi.tiangolo.com/advanced/response-directly/)
- [Pydantic：Models](https://pydantic.dev/docs/validation/latest/concepts/models/)
- [Pydantic：Fields](https://pydantic.dev/docs/validation/latest/concepts/fields/)
