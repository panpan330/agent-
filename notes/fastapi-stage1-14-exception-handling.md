# 阶段 1 第 14 节：统一异常处理

## 1. 这一节学什么

这一节学习 FastAPI 服务里的统一异常处理。

先记住一句话：

```text
统一异常处理，就是让接口出错时也返回稳定、可预测的 JSON 格式。
```

正常接口返回要稳定。

错误接口返回也要稳定。

后端服务不能今天错误长这样：

```json
{"detail": "Not Found"}
```

明天错误长这样：

```json
{"error": "bad request"}
```

后天错误又长这样：

```json
{"message": "server error", "status": 500}
```

如果错误格式乱，前端、Java 服务、测试、日志排查都会很痛苦。

本节目标是把错误响应统一成类似：

```json
{
  "code": "VALIDATION_ERROR",
  "message": "请求参数校验失败",
  "trace_id": "..."
}
```

如果有参数校验细节，再加：

```json
{
  "details": []
}
```

## 2. 什么是异常

异常就是程序运行时出现了不正常情况。

Python 里最简单的例子：

```python
number = int("abc")
```

这会报错。

因为 `"abc"` 不能转成整数。

这种错误在 Python 里叫异常。

常见异常包括：

```text
ValueError
TypeError
KeyError
RuntimeError
```

在 Web 服务里，异常可能来自：

```text
请求路径不存在
请求方法不允许
请求参数不符合模型
业务规则不允许
数据库不可用
调用大模型失败
代码里有 bug
```

## 3. API 服务为什么要关心异常

API 服务不是写给人用眼睛看的函数。

API 服务通常被这些调用：

```text
浏览器前端
Java 后端
测试脚本
移动端
其他微服务
```

调用方需要知道：

```text
请求成功了吗
如果失败，失败类型是什么
用户能不能修正
后端要不要排查
对应 trace_id 是什么
```

所以错误响应必须稳定。

## 4. FastAPI 默认错误响应

如果访问不存在的接口，例如：

```text
GET /missing
```

FastAPI 默认大概返回：

```json
{
  "detail": "Not Found"
}
```

如果请求体缺字段，例如：

```json
{}
```

访问：

```text
POST /chat
```

FastAPI 默认大概返回：

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "message"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

这些默认响应不是不能用。

但对于我们自己的项目，后面要接 Java、RAG、Agent、前端和日志排查。

所以更适合统一成项目自己的错误格式。

## 5. 本节统一后的错误格式

本项目统一错误响应模型是：

```json
{
  "code": "错误码",
  "message": "给人看的错误说明",
  "trace_id": "本次请求编号",
  "details": []
}
```

其中：

```text
code       给程序判断用，稳定，不随便改
message    给人看，可以是中文
trace_id   给排查问题用，能去日志里查
details    可选，放更具体的错误细节
```

## 6. 为什么需要 code

`message` 是给人看的。

比如：

```text
请求参数校验失败
资源不存在
服务器内部错误
```

但程序不应该靠中文句子判断错误。

程序更适合看：

```text
VALIDATION_ERROR
NOT_FOUND
INTERNAL_SERVER_ERROR
CHAT_DISABLED
```

因为 `code` 更稳定。

前端或 Java 服务可以这样判断：

```text
如果 code == VALIDATION_ERROR，就提示用户检查输入
如果 code == INTERNAL_SERVER_ERROR，就提示稍后重试并记录 trace_id
```

## 7. 为什么错误响应里要带 trace_id

上一节我们学了：

```text
trace_id 是一次请求的唯一编号。
```

错误发生时，`trace_id` 更重要。

比如用户说：

```text
我刚才点提交报错了。
```

如果错误响应里没有 trace_id，后端只能靠时间和用户信息慢慢找。

如果错误响应里有：

```json
{
  "trace_id": "trace-abc"
}
```

后端可以直接去日志里搜：

```text
trace_id=trace-abc
```

这就是工程化排查问题的基础能力。

## 8. 本节新增和修改的文件

新增：

```text
app/schemas/error.py
app/core/exceptions.py
app/core/exception_handlers.py
tests/test_exception_handlers.py
notes/fastapi-stage1-14-exception-handling.md
```

修改：

```text
app/main.py
app/middleware/tracing.py
tests/conftest.py
tests/test_chat_api.py
```

## 9. ErrorResponse 模型

文件：

```text
projects/ai-service/app/schemas/error.py
```

代码：

```python
from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    code: str = Field(description="Stable error code for programmatic handling.")
    message: str = Field(description="Human-readable error message.")
    trace_id: str = Field(description="Request trace id for troubleshooting.")
    details: list[dict[str, Any]] | None = Field(
        default=None,
        description="Optional structured error details.",
    )
```

这个模型定义了统一错误响应长什么样。

## 10. 为什么 ErrorResponse 放在 schemas

之前我们已经有：

```text
app/schemas/chat.py
```

里面放：

```text
ChatRequest
ChatResponse
```

这些都是 API 输入输出模型。

`ErrorResponse` 也是 API 输出模型。

所以放在：

```text
app/schemas/error.py
```

这样结构清楚。

## 11. details 为什么是可选的

有些错误不需要 details。

例如 404：

```json
{
  "code": "NOT_FOUND",
  "message": "资源不存在",
  "trace_id": "..."
}
```

但参数校验错误需要更多细节。

例如：

```json
{
  "code": "VALIDATION_ERROR",
  "message": "请求参数校验失败",
  "trace_id": "...",
  "details": [
    {
      "type": "missing",
      "loc": ["body", "message"]
    }
  ]
}
```

所以 `details` 是：

```python
list[dict[str, Any]] | None
```

意思是：

```text
可以是错误详情列表，也可以没有。
```

## 12. AppException 业务异常

文件：

```text
projects/ai-service/app/core/exceptions.py
```

代码：

```python
class AppException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)
```

`AppException` 表示项目自己的业务异常。

比如以后可以这样用：

```python
raise AppException(
    code="CHAT_DISABLED",
    message="聊天功能暂时不可用",
    status_code=409,
)
```

## 13. 为什么要自定义 AppException

FastAPI 有 `HTTPException`。

但业务异常最好有自己的类型。

原因是：

```text
业务异常有固定 code
业务异常有中文 message
业务异常可以带 details
业务异常可以统一记录日志
业务异常和框架异常分开
```

例如：

```text
CHAT_DISABLED
USER_QUOTA_EXCEEDED
MODEL_TIMEOUT
KNOWLEDGE_BASE_NOT_FOUND
```

这些都是业务含义，不只是 HTTP 含义。

## 14. HTTPException 是什么

`HTTPException` 是 Web 框架里的异常。

它表示：

```text
请求不能按正常方式完成，并且应该返回某个 HTTP 状态码。
```

例如：

```text
404 Not Found
405 Method Not Allowed
401 Unauthorized
403 Forbidden
```

FastAPI 官方文档强调，`HTTPException` 是你可以在代码里 raise 的异常，用来告诉客户端发生了某种 HTTP 层面的错误。

## 15. 为什么处理 StarletteHTTPException

本节代码里处理的是：

```python
from starlette.exceptions import HTTPException as StarletteHTTPException
```

不是只处理：

```python
from fastapi import HTTPException
```

原因是 FastAPI 基于 Starlette。

有些内部错误，比如 404、405，来自 Starlette。

如果只注册 FastAPI 的 `HTTPException`，可能接不住所有 HTTP 异常。

所以统一异常处理器注册：

```python
@app.exception_handler(StarletteHTTPException)
```

这样更稳。

## 16. RequestValidationError 是什么

当请求参数不符合 Pydantic 模型时，FastAPI 会抛：

```python
RequestValidationError
```

例如 `/chat` 要求：

```json
{
  "message": "非空字符串"
}
```

但用户传：

```json
{}
```

或者：

```json
{"message": ""}
```

FastAPI 会在进入你的业务函数之前就发现参数不对。

这时抛出的就是请求校验异常。

## 17. exception handler 是什么

exception handler 翻译成异常处理器。

它的作用是：

```text
当某类异常发生时，统一把它转换成 HTTP 响应。
```

FastAPI 写法：

```python
@app.exception_handler(SomeException)
async def some_exception_handler(request: Request, exc: SomeException):
    ...
```

意思是：

```text
如果请求处理中抛了 SomeException，就交给这个函数处理。
```

## 18. register_exception_handlers()

文件：

```text
projects/ai-service/app/core/exception_handlers.py
```

核心入口：

```python
def register_exception_handlers(app: FastAPI) -> None:
    ...
```

我们没有把一堆 handler 都写在 `main.py` 里。

原因是：

```text
main.py 应该负责创建 app 和组装模块
异常处理细节放到 core/exception_handlers.py
```

这样 `main.py` 更干净。

## 19. build_error_response()

统一构造错误响应的函数：

```python
def build_error_response(
    status_code: int,
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
    headers: dict[str, str] | None = None,
    trace_id: str | None = None,
) -> JSONResponse:
    trace_id = trace_id or get_trace_id()
    body = ErrorResponse(
        code=code,
        message=message,
        trace_id=trace_id,
        details=details,
    ).model_dump(exclude_none=True)
    response_headers = dict(headers or {})
    response_headers[TRACE_ID_HEADER] = trace_id
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(body),
        headers=response_headers,
    )
```

这个函数做几件事：

```text
组装 ErrorResponse
去掉值为 None 的 details
把内容转成 JSON 可序列化格式
把 X-Trace-Id 放到响应头
返回 JSONResponse
```

## 20. 为什么使用 exclude_none=True

```python
model_dump(exclude_none=True)
```

意思是：

```text
字段值是 None 时，不输出这个字段。
```

如果没有 details，我们希望响应是：

```json
{
  "code": "NOT_FOUND",
  "message": "资源不存在",
  "trace_id": "..."
}
```

而不是：

```json
{
  "code": "NOT_FOUND",
  "message": "资源不存在",
  "trace_id": "...",
  "details": null
}
```

这让响应更干净。

## 21. 为什么使用 jsonable_encoder

```python
jsonable_encoder(body)
```

FastAPI 的 `jsonable_encoder` 可以把一些 Python 对象转换成 JSON 能处理的格式。

比如：

```text
datetime
UUID
Pydantic 模型
错误详情里的特殊对象
```

虽然我们现在大部分内容已经是普通 dict，但用 `jsonable_encoder` 更稳。

## 22. 为什么 build_error_response 也设置响应头

上一节 trace middleware 已经会设置：

```text
X-Trace-Id
```

但本节发现一个真实细节：

```text
未知异常可能会被更外层的错误处理中间件处理。
```

这种情况下，trace middleware 不一定有机会给最终响应补 header。

所以 `build_error_response()` 自己也设置：

```python
response_headers[TRACE_ID_HEADER] = trace_id
```

这样错误响应也能稳定带上 `X-Trace-Id`。

## 23. get_request_trace_id()

```python
def get_request_trace_id(request: Request) -> str:
    return getattr(request.state, "trace_id", None) or get_trace_id()
```

它的作用是：

```text
优先从 request.state 里拿 trace_id
如果没有，再从 ContextVar 里拿
```

为什么需要 `request.state`？

因为未知异常的处理可能发生在 `ContextVar` 被清理之后。

所以我们在 trace middleware 里增加了：

```python
request.state.trace_id = trace_id
```

这样异常处理器仍然能拿到本次请求的 trace_id。

## 24. 处理 AppException

```python
@app.exception_handler(AppException)
async def app_exception_handler(
    request: Request,
    exc: AppException,
) -> JSONResponse:
    trace_id = get_request_trace_id(request)
    token = set_trace_id(trace_id)
    try:
        logger.warning(
            "app_exception code=%s method=%s path=%s",
            exc.code,
            request.method,
            request.url.path,
        )
        return build_error_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            details=exc.details,
            trace_id=trace_id,
        )
    finally:
        reset_trace_id(token)
```

业务异常返回：

```text
自定义 status_code
自定义 code
自定义 message
可选 details
trace_id
```

日志级别用 `warning`。

因为业务异常通常不是代码 bug。

比如用户额度不足、资源不存在、状态不允许，都属于可预期错误。

## 25. 处理 HTTPException

```python
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(...)
```

本节给常见 HTTP 错误映射了 code：

```python
def get_http_error_code(status_code: int) -> str:
    if status_code == 404:
        return "NOT_FOUND"
    if status_code == 405:
        return "METHOD_NOT_ALLOWED"
    return "HTTP_ERROR"
```

同时给 404、405 设置中文 message：

```python
def get_http_error_message(exc: StarletteHTTPException) -> str:
    if exc.status_code == 404:
        return "资源不存在"
    if exc.status_code == 405:
        return "请求方法不允许"
    if isinstance(exc.detail, str):
        return exc.detail
    return "请求处理失败"
```

这样：

```text
GET /missing
```

返回：

```json
{
  "code": "NOT_FOUND",
  "message": "资源不存在",
  "trace_id": "..."
}
```

## 26. 处理 RequestValidationError

```python
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(...)
```

它返回：

```json
{
  "code": "VALIDATION_ERROR",
  "message": "请求参数校验失败",
  "trace_id": "...",
  "details": [...]
}
```

`details` 来自：

```python
exc.errors()
```

里面会有：

```text
loc   错误位置
type  错误类型
msg   错误说明
```

例如缺少 `message`：

```json
{
  "loc": ["body", "message"],
  "type": "missing"
}
```

## 27. 处理未知异常

```python
@app.exception_handler(Exception)
async def unhandled_exception_handler(...)
```

未知异常指的是：

```text
没有被 AppException、HTTPException、RequestValidationError 处理的异常。
```

例如：

```python
raise RuntimeError("database is unavailable")
```

对外返回：

```json
{
  "code": "INTERNAL_SERVER_ERROR",
  "message": "服务器内部错误",
  "trace_id": "..."
}
```

注意：

```text
不要把真实异常信息直接返回给用户。
```

比如不要返回：

```text
database is unavailable
```

更不要返回数据库地址、密钥、堆栈路径。

真实错误细节应该记录在服务端日志里。

## 28. logger.exception()

未知异常里使用：

```python
logger.exception(...)
```

它会记录错误日志，并自动带上异常堆栈。

这适合未知异常。

因为未知异常通常需要开发者排查代码或环境问题。

## 29. 为什么异常处理器里还要 set_trace_id

异常处理器里有类似代码：

```python
trace_id = get_request_trace_id(request)
token = set_trace_id(trace_id)
try:
    logger.exception(...)
    return build_error_response(...)
finally:
    reset_trace_id(token)
```

这是为了保证：

```text
异常处理器自己写的日志也带正确 trace_id。
```

尤其是未知异常，可能发生在 trace middleware 清理上下文之后。

所以异常处理器会临时把 trace_id 放回日志上下文。

## 30. main.py 如何接入

文件：

```text
projects/ai-service/app/main.py
```

新增：

```python
from app.core.exception_handlers import register_exception_handlers
```

创建 app 后注册：

```python
register_exception_handlers(app)
register_trace_middleware(app)
```

当前 `create_app()` 负责：

```text
读取配置
配置日志
创建 FastAPI 应用
注册异常处理器
注册 trace middleware
注册路由
```

## 31. trace middleware 的小改动

文件：

```text
projects/ai-service/app/middleware/tracing.py
```

本节新增：

```python
request.state.trace_id = trace_id
```

`request.state` 是 FastAPI/Starlette 给当前请求存临时数据的地方。

它只属于当前请求。

我们把 trace_id 存进去，是为了：

```text
即使 ContextVar 被清理，异常处理器仍然能从 request 里找到 trace_id。
```

## 32. 测试夹具的小调整

文件：

```text
projects/ai-service/tests/conftest.py
```

现在拆成：

```python
@pytest.fixture
def app() -> FastAPI:
    return create_app()


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)
```

为什么要暴露 `app`？

因为异常测试里需要临时加测试路由：

```python
@app.get("/test/business-error")
def business_error() -> None:
    raise AppException(...)
```

这样可以测试异常处理器，但不需要把测试接口写进正式代码。

## 33. 测试 404

```python
def test_not_found_response_is_unified(client: TestClient) -> None:
    response = client.get("/missing", headers={TRACE_ID_HEADER: "trace-not-found"})
```

断言：

```python
assert response.status_code == 404
assert response.headers[TRACE_ID_HEADER] == "trace-not-found"
assert response.json() == {
    "code": "NOT_FOUND",
    "message": "资源不存在",
    "trace_id": "trace-not-found",
}
```

这证明不存在的路径也走统一错误格式。

## 34. 测试 422

```python
response = client.post("/chat", headers={TRACE_ID_HEADER: "trace-validation"}, json={})
```

`/chat` 需要 `message`。

传空对象 `{}` 会触发请求校验错误。

断言：

```text
status_code == 422
code == VALIDATION_ERROR
message == 请求参数校验失败
trace_id == trace-validation
details[0].loc == ["body", "message"]
```

这证明 Pydantic 校验错误也统一了。

## 35. 测试业务异常

测试里临时挂一个路由：

```python
@app.get("/test/business-error")
def business_error() -> None:
    raise AppException(
        code="CHAT_DISABLED",
        message="聊天功能暂时不可用",
        status_code=409,
    )
```

断言返回：

```json
{
  "code": "CHAT_DISABLED",
  "message": "聊天功能暂时不可用",
  "trace_id": "trace-business"
}
```

这证明项目自己的业务异常可以被统一处理。

## 36. 测试未知异常

测试里临时挂一个路由：

```python
@app.get("/test/unhandled-error")
def unhandled_error() -> None:
    raise RuntimeError("database is unavailable")
```

测试客户端要这样创建：

```python
client = TestClient(app, raise_server_exceptions=False)
```

为什么？

因为测试环境默认会把服务端异常重新抛给测试代码。

但我们这里要测试的是：

```text
真实 HTTP 客户端会收到什么响应。
```

所以设置：

```text
raise_server_exceptions=False
```

让测试客户端不要直接抛异常，而是读取 500 响应。

## 37. 未知异常测试断言了什么

断言响应：

```python
assert response.status_code == 500
assert response.headers[TRACE_ID_HEADER] == "trace-unhandled"
assert response.json() == {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "服务器内部错误",
    "trace_id": "trace-unhandled",
}
```

还断言日志：

```python
assert "unhandled_exception method=GET path=/test/unhandled-error" in caplog.text
```

并断言日志记录里的 trace_id：

```python
assert any(
    record.name == "app.core.exception_handlers"
    and record.trace_id == "trace-unhandled"
    for record in caplog.records
)
```

这证明：

```text
未知异常响应带 trace_id
未知异常日志也带 trace_id
```

## 38. 当前错误响应示例

### 404

```json
{
  "code": "NOT_FOUND",
  "message": "资源不存在",
  "trace_id": "trace-not-found"
}
```

### 405

```json
{
  "code": "METHOD_NOT_ALLOWED",
  "message": "请求方法不允许",
  "trace_id": "trace-method"
}
```

### 422

```json
{
  "code": "VALIDATION_ERROR",
  "message": "请求参数校验失败",
  "trace_id": "trace-validation",
  "details": [
    {
      "type": "missing",
      "loc": ["body", "message"]
    }
  ]
}
```

### 业务异常

```json
{
  "code": "CHAT_DISABLED",
  "message": "聊天功能暂时不可用",
  "trace_id": "trace-business"
}
```

### 未知异常

```json
{
  "code": "INTERNAL_SERVER_ERROR",
  "message": "服务器内部错误",
  "trace_id": "trace-unhandled"
}
```

## 39. 当前实现还可以怎么扩展

后面可以继续扩展：

```text
错误码集中管理
不同业务模块定义自己的异常
错误响应加入 timestamp
错误响应加入 path
生产环境隐藏 details
开发环境保留更多调试信息
对外错误 message 国际化
接入告警系统
```

但当前阶段先不加太多。

因为现在最重要的是学会：

```text
统一响应模型
异常处理器
trace_id 贯穿错误响应和错误日志
测试错误路径
```

## 40. 本节练习

### 练习 1

题目：

用自己的话解释什么是统一异常处理。

参考答案：

统一异常处理就是把不同类型的错误集中转换成固定格式的 HTTP 响应。

这样调用方不管遇到 404、422、业务异常还是 500，都能按同一套字段读取错误信息。

### 练习 2

题目：

为什么错误响应里要有 `code`，不能只靠 `message`？

参考答案：

因为 `message` 是给人看的，可能改文案、换语言。

`code` 是给程序判断用的，应该稳定。

调用方可以根据 `code` 判断下一步怎么处理。

### 练习 3

题目：

`RequestValidationError` 通常什么时候出现？

参考答案：

当请求参数不符合 FastAPI/Pydantic 定义的请求模型时出现。

例如 `/chat` 需要 `message` 字段，但请求体传 `{}`，就会触发 `RequestValidationError`。

### 练习 4

题目：

为什么未知异常不要把真实异常信息直接返回给用户？

参考答案：

因为真实异常信息可能包含代码路径、数据库信息、内部服务信息或其他敏感内容。

未知异常应该对外返回通用提示，比如“服务器内部错误”，真实细节写入服务端日志。

### 练习 5

题目：

下面这段代码有什么作用？

```python
request.state.trace_id = trace_id
```

参考答案：

它把当前请求的 trace_id 存到 request 对象里。

这样即使 `ContextVar` 被清理，异常处理器仍然可以从 `request.state` 找到本次请求的 trace_id。

### 练习 6

题目：

为什么测试未知异常时要使用：

```python
TestClient(app, raise_server_exceptions=False)
```

参考答案：

因为测试客户端默认会把服务端异常重新抛给测试代码。

但我们要测试真实 HTTP 响应，所以要让客户端不要抛异常，而是返回 500 响应。

## 41. 本节自测

### 自测 1

题目：

本项目统一错误响应包含哪些核心字段？

参考答案：

核心字段是：

```text
code
message
trace_id
```

可选字段是：

```text
details
```

### 自测 2

题目：

`AppException` 是什么？

参考答案：

`AppException` 是项目自定义业务异常，用来表达业务规则失败，并携带 `code`、`message`、`status_code` 和可选 `details`。

### 自测 3

题目：

404 当前会返回什么 code？

参考答案：

404 当前返回：

```text
NOT_FOUND
```

### 自测 4

题目：

405 当前会返回什么 code？

参考答案：

405 当前返回：

```text
METHOD_NOT_ALLOWED
```

### 自测 5

题目：

422 当前会返回什么 code？

参考答案：

422 当前返回：

```text
VALIDATION_ERROR
```

### 自测 6

题目：

未知异常当前会返回什么 code？

参考答案：

未知异常当前返回：

```text
INTERNAL_SERVER_ERROR
```

### 自测 7

题目：

为什么异常处理器里要记录日志？

参考答案：

因为错误响应给调用方看，日志给开发者排查问题。

特别是未知异常，对外只返回通用提示，但服务端日志要记录堆栈和 trace_id。

### 自测 8

题目：

`logger.exception()` 通常应该在哪里使用？

参考答案：

通常在处理未知异常或 `except` 代码块里使用，因为它会记录错误日志并自动带上异常堆栈。

### 自测 9

题目：

为什么处理 HTTP 异常时注册的是 `StarletteHTTPException`？

参考答案：

因为 FastAPI 基于 Starlette，很多框架内部 HTTP 异常来自 Starlette。

注册 `StarletteHTTPException` 能覆盖 404、405 等框架内部异常。

### 自测 10

题目：

本节和上一节 `trace_id` 是怎么连接起来的？

参考答案：

本节的错误响应和错误日志都会带上 trace_id。

这样请求失败时，调用方可以拿响应里的 `trace_id` 去服务端日志中查同一次请求的错误详情。

## 42. 本节小结

这一节完成了统一异常处理基础：

```text
定义 ErrorResponse
定义 AppException
统一处理 AppException
统一处理 HTTPException
统一处理 RequestValidationError
统一处理未知 Exception
错误响应带 trace_id
错误响应头带 X-Trace-Id
错误日志带 trace_id
测试 404、422、业务异常、未知异常
```

当前项目错误响应已经从 FastAPI 默认格式，变成了项目自己的稳定格式。

下一节学习：

```text
CORS 基础
```

会讲：

```text
浏览器为什么会有跨域限制
什么是 origin
为什么前端访问后端会遇到 CORS
FastAPI 怎么配置 CORSMiddleware
```

## 43. 参考资料

- [FastAPI 官方文档：Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [FastAPI 官方文档：HTTPException](https://fastapi.tiangolo.com/reference/exceptions/)
- [Starlette 官方文档：Exceptions](https://starlette.dev/exceptions/)
- [Python 官方文档：Errors and Exceptions](https://docs.python.org/3/tutorial/errors.html)
