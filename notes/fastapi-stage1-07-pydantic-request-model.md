# FastAPI 阶段 1 第 7 节：Pydantic 请求模型

日期：2026-07-07

本节目标：学会用 Pydantic 定义请求体结构，并理解 FastAPI 为什么能自动校验 JSON 请求体。

上一节我们学了：

```text
POST /chat
Content-Type: application/json
body: {"message": "..."}
```

现在继续往下问：

```text
FastAPI 怎么知道 body 里必须有 message？
FastAPI 怎么知道 message 必须是字符串？
如果 message 缺失、为空、类型不对，为什么应该报错？
为什么后面接口会返回 422？
```

答案是：

```text
Pydantic 请求模型。
```

## 1. 本节学什么

本节学习这些内容：

1. Pydantic 是什么。
2. 请求模型是什么。
3. `BaseModel` 是什么。
4. 字段 field 是什么。
5. 字段类型是什么。
6. 必填字段是什么。
7. 默认值和可选字段是什么。
8. `Field()` 是什么。
9. `min_length=1` 是什么。
10. `ValidationError` 是什么。
11. FastAPI 怎么把 Pydantic 模型用于请求体。
12. 为什么请求校验失败会变成 422。
13. `app/schemas/` 目录为什么出现。
14. 如何给请求模型写测试。

先记住一句话：

```text
Pydantic 请求模型 = 用 Python 类描述 JSON 请求体应该长什么样。
```

再记住一句话：

```text
FastAPI 看到函数参数是 Pydantic 模型时，会把它当作请求体来读取和校验。
```

## 2. Pydantic 是什么

Pydantic 是 Python 里的数据校验工具。

它可以帮我们做：

```text
检查字段是否存在。
检查字段类型是否正确。
检查字符串长度。
检查数字范围。
把输入数据转成 Python 对象。
生成 JSON Schema。
提供清晰的错误信息。
```

在 FastAPI 项目里，Pydantic 很重要。

因为 API 接收的是外部数据。

外部数据可能是：

```text
字段缺失。
字段类型错。
字符串为空。
结构不符合预期。
恶意构造。
前端传错。
Java 后端传错。
```

不能直接相信客户端传来的数据。

所以要先校验。

## 3. 为什么需要请求模型

假设我们后面要做：

```text
POST /chat
```

客户端应该发送：

```json
{
  "message": "请解释 FastAPI 是什么"
}
```

那我们必须告诉服务端：

```text
请求体必须是一个 JSON 对象。
里面必须有 message 字段。
message 必须是字符串。
message 不能是空字符串。
```

这就是请求模型要表达的规则。

如果没有请求模型，你可能会在接口里手动写：

```python
if "message" not in data:
    ...

if not isinstance(data["message"], str):
    ...

if len(data["message"]) < 1:
    ...
```

这样很麻烦，也容易漏。

Pydantic 可以把这些规则集中写成一个类。

## 4. 本节新增了哪些代码

本节新增：

```text
projects/ai-service/app/schemas/
  __init__.py
  chat.py

projects/ai-service/tests/
  test_chat_schema.py
```

新增请求模型：

```python
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        description="User message sent to the AI service.",
    )
```

先看懂这几件事：

```text
ChatRequest 是请求模型。
BaseModel 是 Pydantic 模型基类。
message 是字段。
str 表示字段类型必须是字符串。
Field(min_length=1) 表示字符串长度至少是 1。
description 会进入 JSON Schema / OpenAPI 文档。
```

## 5. 为什么放在 app/schemas/

新增目录：

```text
app/schemas/
```

它用来放请求和响应数据模型。

为什么不放进 `routers/chat.py`？

因为以后模型会越来越多：

```text
ChatRequest
ChatResponse
StreamChatRequest
RagQueryRequest
TicketExtractRequest
```

如果都混在 router 文件里，接口层会变乱。

所以按职责拆分：

```text
routers/  放接口
schemas/  放请求/响应数据结构
services/ 放业务逻辑
```

当前只创建了 `schemas/`，是因为现在开始学习请求模型了。

## 6. `BaseModel` 是什么

代码：

```python
from pydantic import BaseModel
```

`BaseModel` 是 Pydantic 的基础模型类。

你定义自己的模型时，要继承它：

```python
class ChatRequest(BaseModel):
    ...
```

继承 `BaseModel` 后，Pydantic 才知道：

```text
这是一个需要校验的数据模型。
```

它会根据类里的字段定义去校验输入数据。

## 7. `ChatRequest` 是什么

代码：

```python
class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
```

`ChatRequest` 表示聊天接口的请求体结构。

它描述的是：

```json
{
  "message": "请解释 FastAPI 是什么"
}
```

也就是说：

```text
ChatRequest 是服务端期待客户端发来的 JSON 结构。
```

## 8. 字段 field 是什么

在这个模型里：

```python
class ChatRequest(BaseModel):
    message: str
```

`message` 就是字段。

字段可以理解成：

```text
JSON 对象里的一个 key。
```

JSON：

```json
{
  "message": "你好"
}
```

Pydantic 模型：

```python
class ChatRequest(BaseModel):
    message: str
```

对应关系：

```text
JSON key message -> 模型字段 message
JSON value "你好" -> 字段值 request.message
```

## 9. 字段类型是什么

代码：

```python
message: str
```

这里的 `str` 是字段类型。

它表示：

```text
message 必须是字符串。
```

如果客户端发送：

```json
{
  "message": "你好"
}
```

这是合法的。

如果客户端发送：

```json
{
  "message": 123
}
```

这不是我们想要的聊天消息。

Pydantic 会把它判定为不符合模型。

## 10. 必填字段是什么

代码：

```python
class ChatRequest(BaseModel):
    message: str
```

这里 `message` 没有默认值。

在 Pydantic 里，没有默认值的字段通常是必填字段。

也就是说，客户端必须传：

```json
{
  "message": "你好"
}
```

如果传：

```json
{}
```

就会报错：

```text
message 字段缺失。
```

FastAPI 后面会把这种请求校验错误返回成 422。

## 11. 默认值和可选字段

假设写：

```python
class ChatRequest(BaseModel):
    message: str
    stream: bool = False
```

这里：

```text
message 没有默认值，所以必填。
stream 有默认值 False，所以可以不传。
```

客户端可以发送：

```json
{
  "message": "你好"
}
```

Pydantic 会得到：

```python
request.stream == False
```

如果你想允许字段为 `None`，可以写：

```python
class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
```

注意：

```text
类型写成 str | None 只是允许 None。
真正让字段不必填的是 = None 这个默认值。
```

这点很重要，后面会继续遇到。

## 12. `Field()` 是什么

当前代码：

```python
message: str = Field(
    min_length=1,
    description="User message sent to the AI service.",
)
```

`Field()` 用来给字段添加更多规则和说明。

这里添加了两个信息：

```text
min_length=1
description="User message sent to the AI service."
```

`min_length=1` 是校验规则。

`description` 是文档说明。

以后 `/docs` 里会看到这些 schema 信息。

## 13. 为什么 message 要 min_length=1

如果只写：

```python
message: str
```

那么下面这个也是字符串：

```json
{
  "message": ""
}
```

但空字符串没有实际聊天内容。

所以我们写：

```python
Field(min_length=1)
```

表示：

```text
message 至少要有 1 个字符。
```

这样空字符串会被拒绝。

注意：

```json
{
  "message": "   "
}
```

这种全是空格的字符串长度大于 1，目前会通过。

后面如果想禁止纯空格，需要更进一步的校验器。

现在先不加，避免一次讲太多。

## 14. 创建模型对象

可以直接在 Python 里创建：

```python
request = ChatRequest(message="请解释 FastAPI 是什么")
```

然后访问字段：

```python
request.message
```

得到：

```text
请解释 FastAPI 是什么
```

这说明 Pydantic 把输入数据变成了一个 Python 对象。

## 15. `model_dump()` 是什么

Pydantic 模型可以转回字典：

```python
request = ChatRequest(message="你好")
data = request.model_dump()
```

结果：

```python
{
    "message": "你好",
}
```

后面写接口、日志、测试时会经常用到 `model_dump()`。

初学阶段可以理解成：

```text
model_dump() = 把 Pydantic 模型转成 Python 字典。
```

## 16. `ValidationError` 是什么

如果输入数据不符合模型，Pydantic 会抛出：

```python
ValidationError
```

例如：

```python
ChatRequest()
```

没有传 `message`，就会报错。

再比如：

```python
ChatRequest(message="")
```

空字符串不满足 `min_length=1`，也会报错。

再比如：

```python
ChatRequest(message=123)
```

`message` 不是字符串，也会报错。

## 17. Pydantic 错误信息怎么看

Pydantic 的错误可以通过：

```python
exc.errors()
```

拿到结构化错误。

例如缺少字段时，错误里通常会包含：

```python
{
    "type": "missing",
    "loc": ("message",),
    "msg": "Field required",
    ...
}
```

重点看三个字段：

| 字段 | 含义 |
| --- | --- |
| `type` | 错误类型 |
| `loc` | 错误发生的位置 |
| `msg` | 错误说明 |

这和后面 FastAPI 返回的 422 错误格式有关系。

## 18. 为什么 FastAPI 会返回 422

这节还没有写 `/chat` 接口。

但后面一旦这样写：

```python
@router.post("/chat")
def chat(request: ChatRequest):
    ...
```

FastAPI 会知道：

```text
request 是 Pydantic 模型。
所以它应该从请求 body 里读取 JSON。
然后用 ChatRequest 校验。
```

如果客户端发：

```json
{}
```

或者：

```json
{
  "message": ""
}
```

校验失败。

FastAPI 会把这个请求判定为：

```text
请求内容语义不符合接口要求。
```

并返回：

```text
422 Unprocessable Content
```

初学阶段可以这样记：

```text
422 = 请求 JSON 格式能解析，但字段不符合 Pydantic 模型要求。
```

## 19. 400 和 422 的区别

简单理解：

```text
400 更偏请求本身格式有问题。
422 更偏请求能读懂，但内容不符合规则。
```

例如：

```text
JSON 写坏了，可能是 400。
JSON 能解析，但缺少 message，FastAPI 常返回 422。
```

你不需要现在死记所有 HTTP 细节。

先记住：

```text
FastAPI 请求体验证失败，经常看到 422。
```

## 20. 本节测试代码

新增测试：

```text
projects/ai-service/tests/test_chat_schema.py
```

测试内容：

```python
import pytest
from pydantic import ValidationError

from app.schemas.chat import ChatRequest
```

导入：

```text
pytest 用来断言会抛异常。
ValidationError 是 Pydantic 校验失败异常。
ChatRequest 是我们自己的请求模型。
```

## 21. 测试：正常 message

代码：

```python
def test_chat_request_accepts_message() -> None:
    request = ChatRequest(message="请解释 FastAPI 是什么")

    assert request.message == "请解释 FastAPI 是什么"
```

这个测试验证：

```text
只要 message 是非空字符串，模型能正常创建。
创建后可以通过 request.message 访问字段。
```

## 22. 测试：缺少 message

代码：

```python
def test_chat_request_rejects_missing_message() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ChatRequest()

    error = exc_info.value.errors()[0]
    assert error["loc"] == ("message",)
    assert error["type"] == "missing"
```

这个测试验证：

```text
message 是必填字段。
如果不传 message，Pydantic 会抛 ValidationError。
错误位置是 message。
错误类型是 missing。
```

## 23. 测试：空字符串

代码：

```python
def test_chat_request_rejects_empty_message() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ChatRequest(message="")

    error = exc_info.value.errors()[0]
    assert error["loc"] == ("message",)
    assert error["type"] == "string_too_short"
```

这个测试验证：

```text
message 不能是空字符串。
因为 Field(min_length=1) 要求长度至少是 1。
```

## 24. 测试：非字符串

代码：

```python
def test_chat_request_rejects_non_string_message() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ChatRequest(message=123)

    error = exc_info.value.errors()[0]
    assert error["loc"] == ("message",)
    assert error["type"] == "string_type"
```

这个测试验证：

```text
message 必须是字符串。
传数字会被拒绝。
```

## 25. 为什么现在只测模型，不测接口

因为这一节学的是：

```text
Pydantic 请求模型。
```

还没有实现：

```text
POST /chat
```

所以先测试模型本身。

下一步等 `/chat` 接口接入 `ChatRequest` 后，再测试接口行为：

```text
正常请求返回 200。
缺少 message 返回 422。
空 message 返回 422。
错误类型返回 422。
```

这样分层学习更清楚。

## 26. 请求模型和响应模型的区别

请求模型：

```text
客户端发给服务端的数据结构。
```

例如：

```python
class ChatRequest(BaseModel):
    message: str
```

响应模型：

```text
服务端返回给客户端的数据结构。
```

例如下一节可能会写：

```python
class ChatResponse(BaseModel):
    reply: str
```

当前这一节只学请求模型。

响应模型下一节再讲。

## 27. 和 Java DTO 的类比

你可以把 Pydantic 模型类比成 Java 里的 DTO。

Java 里可能写：

```java
public class ChatRequest {
    private String message;
}
```

再配合校验注解：

```java
@NotBlank
private String message;
```

FastAPI / Pydantic 里现在写：

```python
class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
```

类比关系：

| Java | Python / Pydantic |
| --- | --- |
| DTO 类 | `BaseModel` 子类 |
| 字段 | 模型字段 |
| `String` | `str` |
| `@NotBlank` | `Field(min_length=1)` 的一部分效果 |
| Bean Validation 错误 | `ValidationError` / FastAPI 422 |

注意：

```text
Field(min_length=1) 只禁止空字符串，不禁止纯空格。
```

Java 的 `@NotBlank` 通常会禁止纯空格。

如果 Python 里也要做到这一点，需要额外校验。

## 28. 常见错误

### 错误 1：忘记继承 BaseModel

错误：

```python
class ChatRequest:
    message: str
```

这只是普通 Python 类。

FastAPI 不会把它当作 Pydantic 请求模型。

正确：

```python
class ChatRequest(BaseModel):
    message: str
```

### 错误 2：以为类型提示会自动运行时校验

普通 Python 的类型提示：

```python
message: str
```

本身不一定会在运行时强制检查。

Pydantic 的作用是：

```text
读取这些类型提示，并在创建模型时执行校验。
```

### 错误 3：以为 `str | None` 就是不必填

不完整。

```python
conversation_id: str | None
```

表示允许值是字符串或 None，但如果没有默认值，它仍可能被视为必填。

更常见写法：

```python
conversation_id: str | None = None
```

### 错误 4：不知道空字符串也是字符串

```python
message: str
```

会允许：

```json
{
  "message": ""
}
```

如果你不想允许空字符串，需要加：

```python
Field(min_length=1)
```

### 错误 5：把请求模型和业务逻辑混在一起

请求模型只描述数据结构。

它不应该负责：

```text
调用大模型。
检索知识库。
调用 Java API。
写复杂业务流程。
```

这些应该放到 service 或其他业务层。

## 29. 本节必须掌握的最小知识

这一节最少要掌握：

```text
Pydantic 用来做数据模型和数据校验。
BaseModel 是 Pydantic 模型基类。
请求模型描述客户端 JSON body 应该长什么样。
message: str 表示 message 必须是字符串。
没有默认值的字段通常是必填。
Field(min_length=1) 表示字符串长度至少为 1。
ValidationError 表示模型校验失败。
FastAPI 使用 Pydantic 模型校验请求体。
请求体校验失败时，FastAPI 常返回 422。
schemas/ 用来放请求和响应模型。
```

## 30. 本节练习

### 练习 1：解释请求模型

题目：

用自己的话解释：

```text
什么是 Pydantic 请求模型？
```

### 练习 2：解释 BaseModel

题目：

用自己的话解释：

```python
class ChatRequest(BaseModel):
    ...
```

为什么要继承 `BaseModel`？

### 练习 3：解释字段规则

题目：

解释下面代码的含义：

```python
message: str = Field(min_length=1)
```

### 练习 4：判断请求是否有效

题目：

根据当前 `ChatRequest`，判断下面请求是否有效：

A：

```json
{
  "message": "你好"
}
```

B：

```json
{}
```

C：

```json
{
  "message": ""
}
```

D：

```json
{
  "message": 123
}
```

### 练习 5：解释 ValidationError

题目：

用自己的话解释：

```text
ValidationError 是什么？
```

### 练习 6：解释 422

题目：

用自己的话解释：

```text
为什么 FastAPI 里请求体校验失败经常返回 422？
```

### 练习 7：设计一个可选字段

题目：

给 `ChatRequest` 增加一个可选字段 `conversation_id`，类型是字符串或 `None`，默认值是 `None`。应该怎么写？

## 31. 本节练习参考答案

### 练习 1 参考答案：解释请求模型

题目：

用自己的话解释：

```text
什么是 Pydantic 请求模型？
```

参考答案：

Pydantic 请求模型是用 Python 类描述请求体 JSON 应该长什么样。

它规定字段名称、字段类型、是否必填、默认值和校验规则。

FastAPI 可以用它自动读取和校验请求体。

### 练习 2 参考答案：解释 BaseModel

题目：

用自己的话解释：

```python
class ChatRequest(BaseModel):
    ...
```

为什么要继承 `BaseModel`？

参考答案：

继承 `BaseModel` 表示 `ChatRequest` 是一个 Pydantic 模型。

Pydantic 会根据类里的类型提示和 `Field()` 规则校验输入数据。

如果不继承 `BaseModel`，它只是普通 Python 类，不能自动完成这些校验能力。

### 练习 3 参考答案：解释字段规则

题目：

解释下面代码的含义：

```python
message: str = Field(min_length=1)
```

参考答案：

这行代码定义了一个字段 `message`。

规则是：

```text
字段名是 message。
字段类型是 str，也就是字符串。
没有默认值，所以是必填字段。
min_length=1 表示字符串长度至少是 1，不能是空字符串。
```

### 练习 4 参考答案：判断请求是否有效

题目：

根据当前 `ChatRequest`，判断下面请求是否有效：

A：

```json
{
  "message": "你好"
}
```

B：

```json
{}
```

C：

```json
{
  "message": ""
}
```

D：

```json
{
  "message": 123
}
```

参考答案：

| 请求 | 是否有效 | 原因 |
| --- | --- | --- |
| A | 有效 | `message` 是非空字符串 |
| B | 无效 | 缺少必填字段 `message` |
| C | 无效 | `message` 是空字符串，不满足 `min_length=1` |
| D | 无效 | `message` 不是字符串 |

### 练习 5 参考答案：解释 ValidationError

题目：

用自己的话解释：

```text
ValidationError 是什么？
```

参考答案：

`ValidationError` 是 Pydantic 在数据不符合模型规则时抛出的异常。

它里面包含结构化错误信息，例如哪个字段错了、错误类型是什么、错误说明是什么。

### 练习 6 参考答案：解释 422

题目：

用自己的话解释：

```text
为什么 FastAPI 里请求体校验失败经常返回 422？
```

参考答案：

因为 FastAPI 能解析请求体 JSON，但 JSON 内容不符合 Pydantic 模型要求。

例如缺少必填字段、字段类型错误、字符串长度不满足规则。

这种情况 FastAPI 通常返回 422，表示请求内容语义不符合接口要求。

### 练习 7 参考答案：设计一个可选字段

题目：

给 `ChatRequest` 增加一个可选字段 `conversation_id`，类型是字符串或 `None`，默认值是 `None`。应该怎么写？

参考答案：

```python
class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: str | None = None
```

这里：

```text
str | None 表示值可以是字符串或 None。
= None 表示这个字段有默认值，所以可以不传。
```

## 32. 自测问题

1. Pydantic 是什么？
2. `BaseModel` 是什么？
3. 请求模型描述的是客户端发来的数据，还是服务端返回的数据？
4. `message: str` 表示什么？
5. 没有默认值的字段通常是不是必填？
6. `Field(min_length=1)` 有什么作用？
7. 空字符串 `""` 是不是字符串？
8. 当前 `ChatRequest` 会不会允许空字符串？
9. `ValidationError` 什么时候出现？
10. `errors()` 里的 `loc` 表示什么？
11. `errors()` 里的 `type` 表示什么？
12. FastAPI 怎么知道一个参数应该来自请求体？
13. 请求体校验失败为什么常见 422？
14. `schemas/` 目录应该放什么？
15. 请求模型和响应模型有什么区别？

## 33. 自测参考答案

### 自测 1 参考答案

题目：

Pydantic 是什么？

答案：

Pydantic 是 Python 的数据模型和数据校验工具，可以根据类型提示和字段规则校验输入数据，并生成结构化错误信息。

### 自测 2 参考答案

题目：

`BaseModel` 是什么？

答案：

`BaseModel` 是 Pydantic 的基础模型类。自定义模型继承它后，Pydantic 才能根据字段定义进行校验。

### 自测 3 参考答案

题目：

请求模型描述的是客户端发来的数据，还是服务端返回的数据？

答案：

请求模型描述客户端发给服务端的数据，也就是请求体 JSON 的结构。

### 自测 4 参考答案

题目：

`message: str` 表示什么？

答案：

它表示模型里有一个字段叫 `message`，这个字段的值应该是字符串。

### 自测 5 参考答案

题目：

没有默认值的字段通常是不是必填？

答案：

是。没有默认值的字段通常是必填字段，客户端必须提供。

### 自测 6 参考答案

题目：

`Field(min_length=1)` 有什么作用？

答案：

它给字符串字段加了最小长度约束，要求字段值长度至少是 1，因此空字符串会被拒绝。

### 自测 7 参考答案

题目：

空字符串 `""` 是不是字符串？

答案：

是。空字符串也是字符串，只是长度为 0。

### 自测 8 参考答案

题目：

当前 `ChatRequest` 会不会允许空字符串？

答案：

不会。

因为 `message` 字段使用了：

```python
Field(min_length=1)
```

### 自测 9 参考答案

题目：

`ValidationError` 什么时候出现？

答案：

当输入数据不符合 Pydantic 模型规则时会出现，例如缺少字段、类型错误、长度不满足要求。

### 自测 10 参考答案

题目：

`errors()` 里的 `loc` 表示什么？

答案：

`loc` 表示错误发生的位置。

例如 `("message",)` 表示错误发生在 `message` 字段。

### 自测 11 参考答案

题目：

`errors()` 里的 `type` 表示什么？

答案：

`type` 表示错误类型。

例如 `missing` 表示字段缺失，`string_too_short` 表示字符串太短。

### 自测 12 参考答案

题目：

FastAPI 怎么知道一个参数应该来自请求体？

答案：

如果路径操作函数的参数类型是 Pydantic 模型，FastAPI 会把它当作请求体模型，从 request body 里读取 JSON 并校验。

### 自测 13 参考答案

题目：

请求体校验失败为什么常见 422？

答案：

因为请求体 JSON 可以被读取，但内容不符合接口定义的 Pydantic 模型规则。

FastAPI 通常把这种请求校验失败返回为 422。

### 自测 14 参考答案

题目：

`schemas/` 目录应该放什么？

答案：

`schemas/` 目录放请求和响应数据模型，比如 `ChatRequest`、`ChatResponse`、`RagQueryRequest`。

### 自测 15 参考答案

题目：

请求模型和响应模型有什么区别？

答案：

请求模型描述客户端发给服务端的数据结构。

响应模型描述服务端返回给客户端的数据结构。

## 34. 本节小结

这一节完成了从“POST JSON body”到“请求模型”的过渡：

```text
POST /chat
        ↓
JSON body: {"message": "..."}
        ↓
ChatRequest(BaseModel)
        ↓
message: str
        ↓
Field(min_length=1)
        ↓
Pydantic 校验
```

当前我们还没有写 `/chat` 接口。

但已经先准备好了：

```text
app/schemas/chat.py
tests/test_chat_schema.py
```

下一节学习：

```text
Pydantic 响应模型
```

下一节会讲：

```text
服务端返回给客户端的数据结构怎么定义？
ChatResponse 是什么？
response_model 是什么？
为什么响应也要有模型？
```

## 35. 参考资料

- [FastAPI：Request Body](https://fastapi.tiangolo.com/tutorial/body/)
- [Pydantic：Models](https://pydantic.dev/docs/validation/latest/concepts/models/)
- [Pydantic：Fields](https://pydantic.dev/docs/validation/latest/concepts/fields/)
- [Pydantic：Error Handling](https://pydantic.dev/docs/validation/latest/errors/errors/)
