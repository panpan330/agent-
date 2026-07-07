# 阶段 1 第 12 节：logging 日志

## 1. 这一节学什么

这一节学习 FastAPI 服务里的日志。

你要先记住一句话：

```text
日志是程序运行时留下的记录。
```

后端服务不是只在你眼前运行一次的小脚本。

后端服务通常是：

```text
一直开着
一直接收请求
可能被很多用户访问
可能在半夜报错
可能部署在服务器上
```

所以你不能只靠“我看一下代码”来判断发生了什么。

你需要日志告诉你：

```text
服务有没有启动
接口有没有被调用
请求用了哪个模型
这次请求花了多久
有没有报错
错误发生在哪里
```

现在我们还没有接真实大模型，所以本节先做最基础的事情：

```text
用 Python 标准库 logging
从 .env 的 LOG_LEVEL 控制日志级别
在 /chat 接口里打一条业务日志
写测试确认日志真的产生了
```

## 2. 为什么不能只用 print

你刚开始写 Python 时，经常会这样：

```python
print("程序运行到这里了")
print(user_message)
```

这在学习小脚本时可以。

但是后端服务里不能长期依赖 `print`。

原因不是 `print` 完全不能用，而是它太简单了：

```text
print 没有日志级别
print 不方便统一控制输出格式
print 不方便区分不同模块
print 不方便在生产环境里按级别过滤
print 不适合以后接入文件、日志系统、云平台
```

比如你希望：

```text
开发时看到 DEBUG 细节
上线时只看 INFO、WARNING、ERROR
出问题时重点查 ERROR
```

如果全是 `print`，你只能手动删代码或加很多 `if`。

如果用 `logging`，可以通过配置控制。

## 3. 什么是 logging

`logging` 是 Python 标准库里的日志模块。

标准库的意思是：

```text
不用 pip install
Python 自带
可以直接 import
```

最小例子：

```python
import logging

logger = logging.getLogger(__name__)

logger.info("服务启动成功")
logger.error("调用模型失败")
```

这里有三个核心概念：

```text
logger   谁在写日志
level    这条日志有多重要
handler  日志输出到哪里
```

本节先重点理解前两个。

## 4. logger 是什么

`logger` 可以理解成：

```text
某个模块专用的日志记录器
```

比如在 `app/routers/chat.py` 里：

```python
logger = logging.getLogger(__name__)
```

这里的 `__name__` 在当前文件里通常是：

```text
app.routers.chat
```

也就是说，这条日志会带上“它来自哪个模块”。

这很重要。

项目大了以后，如果日志只显示：

```text
调用失败
```

你不知道是哪里失败。

如果日志显示：

```text
ERROR [app.routers.chat] 调用失败
```

你就知道问题来自聊天接口模块。

## 5. 为什么推荐 `logging.getLogger(__name__)`

你以后会经常看到这句：

```python
logger = logging.getLogger(__name__)
```

这是 Python 官方推荐的常见写法。

它的好处是：

```text
每个模块都有自己的 logger 名字
logger 名字跟 Python 包路径一致
日志来源清楚
后续可以单独控制某个模块的日志级别
```

比如：

```text
app.main
app.core.config
app.routers.chat
app.services.llm
```

这些以后都可以成为不同的 logger 名称。

## 6. 日志级别是什么

日志级别表示：

```text
这条日志有多重要
```

常见级别从低到高：

```text
DEBUG
INFO
WARNING
ERROR
CRITICAL
```

越往下越严重。

## 7. DEBUG

`DEBUG` 用来记录非常细的调试信息。

比如：

```python
logger.debug("准备调用模型，model_name=%s", model_name)
```

适合开发阶段排查问题。

上线后一般不会默认打开太多 DEBUG。

因为 DEBUG 可能非常多，容易把重要日志淹没。

## 8. INFO

`INFO` 用来记录正常运行过程中的关键信息。

比如：

```python
logger.info("mock_chat_requested message_length=%s", len(request.message))
```

这表示：

```text
/chat 接口被正常调用了一次
用户消息长度是多少
```

它不是错误。

它是“正常发生，但值得记录”的事件。

## 9. WARNING

`WARNING` 表示出现了不太正常的情况，但程序还能继续运行。

例如：

```text
请求缺少可选参数，已经使用默认值
模型响应比较慢，但还没有超时
配置使用了默认值，需要注意
```

它比 `INFO` 严重，但还不是失败。

## 10. ERROR

`ERROR` 表示某个功能失败了。

比如：

```text
调用大模型失败
数据库连接失败
解析用户请求失败
```

后面接真实 AI 接口时，模型调用失败应该记录 `ERROR`。

## 11. CRITICAL

`CRITICAL` 表示非常严重，程序可能无法继续运行。

例如：

```text
核心配置缺失
服务启动失败
数据库完全不可用
```

日常业务代码里不一定经常用到。

## 12. 日志级别的过滤规则

假设配置：

```text
LOG_LEVEL=INFO
```

那么会输出：

```text
INFO
WARNING
ERROR
CRITICAL
```

不会输出：

```text
DEBUG
```

再比如配置：

```text
LOG_LEVEL=ERROR
```

那么只会输出：

```text
ERROR
CRITICAL
```

不会输出：

```text
DEBUG
INFO
WARNING
```

这就是“日志级别是过滤门槛”。

## 13. 为什么日志级别要放进 .env

上一节我们已经做了配置读取：

```text
.env
.env.example
app/core/config.py
Settings
get_settings()
```

日志级别属于配置。

它不应该写死在代码里。

原因是：

```text
开发环境可能想用 DEBUG
测试环境可能想用 INFO
生产环境可能想用 WARNING 或 INFO
临时排查问题时可能想改成 DEBUG
```

所以我们放在 `.env.example` 里：

```env
LOG_LEVEL="INFO"
```

本机真实配置放在 `.env` 里：

```env
LOG_LEVEL="DEBUG"
```

这样不需要改代码，就能改变日志输出级别。

## 14. 本节新增的日志配置模块

新增文件：

```text
projects/ai-service/app/core/logging.py
```

核心代码：

```python
import logging
import sys


APP_LOGGER_NAMES = (
    "app",
    "uvicorn",
    "uvicorn.error",
    "uvicorn.access",
)
LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_log_level(log_level: str) -> int:
    level = logging.getLevelName(log_level.upper())
    if not isinstance(level, int):
        raise ValueError(f"Unsupported log level: {log_level}")
    return level


def configure_logging(log_level: str) -> None:
    level = get_log_level(log_level)
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        stream=sys.stdout,
    )

    for logger_name in APP_LOGGER_NAMES:
        logging.getLogger(logger_name).setLevel(level)
```

我们一段一段拆。

## 15. `import logging`

```python
import logging
```

导入 Python 标准库日志模块。

后面这些都来自它：

```text
logging.getLogger()
logging.basicConfig()
logging.INFO
logging.ERROR
```

## 16. `import sys`

```python
import sys
```

这里用它是为了指定日志输出到：

```python
stream=sys.stdout
```

`stdout` 是标准输出。

你可以简单理解成：

```text
日志显示在终端里
```

## 17. `APP_LOGGER_NAMES`

```python
APP_LOGGER_NAMES = (
    "app",
    "uvicorn",
    "uvicorn.error",
    "uvicorn.access",
)
```

这里列出我们想控制日志级别的 logger。

`app` 是我们自己的应用包名。

例如：

```text
app.main
app.routers.chat
app.core.config
```

都属于 `app` 下面。

`uvicorn` 是运行 FastAPI 的 ASGI 服务器。

当你运行：

```powershell
uv run uvicorn app.main:app --reload
```

真正负责监听端口和接收 HTTP 请求的是 Uvicorn。

所以我们也把 Uvicorn 的常见 logger 放进来：

```text
uvicorn
uvicorn.error
uvicorn.access
```

## 18. `LOG_FORMAT`

```python
LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
```

这是日志格式。

含义是：

```text
%(asctime)s     时间
%(levelname)s   日志级别
%(name)s        logger 名称
%(message)s     日志内容
```

输出大概像这样：

```text
2026-07-07 18:20:00 INFO [app.routers.chat] mock_chat_requested message_length=4
```

看到这行，你能知道：

```text
什么时候发生
严重级别是什么
来自哪个模块
具体事件是什么
```

## 19. `DATE_FORMAT`

```python
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
```

这是时间格式。

例如：

```text
2026-07-07 18:20:00
```

它比默认格式更容易读。

## 20. `get_log_level()`

```python
def get_log_level(log_level: str) -> int:
    level = logging.getLevelName(log_level.upper())
    if not isinstance(level, int):
        raise ValueError(f"Unsupported log level: {log_level}")
    return level
```

这个函数做一件事：

```text
把字符串日志级别转成 logging 模块内部使用的数字
```

比如：

```text
"INFO"  -> 20
"ERROR" -> 40
```

为什么要转？

因为 `.env` 里读出来的是字符串：

```env
LOG_LEVEL="INFO"
```

但 `logging.basicConfig(level=...)` 接收的是日志级别值。

`log_level.upper()` 的作用是：

```text
让 info、Info、INFO 都可以被识别
```

如果传入：

```text
LOUD
```

它不是合法日志级别，就抛出：

```python
ValueError
```

这比悄悄忽略错误更好。

因为配置写错时，我们应该尽早知道。

## 21. `configure_logging()`

```python
def configure_logging(log_level: str) -> None:
    level = get_log_level(log_level)
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        stream=sys.stdout,
    )
```

这个函数负责真正配置日志。

`logging.basicConfig(...)` 是最基础的日志配置入口。

这里配置了：

```text
level    输出哪些级别的日志
format   日志长什么样
datefmt  时间长什么样
stream   输出到哪里
```

本阶段先用 `basicConfig`。

后面生产化阶段，如果需要更复杂的日志，我们再学：

```text
dictConfig
JSON 日志
日志文件
trace_id 注入日志
日志采集系统
```

## 22. 为什么还要设置多个 logger 的 level

```python
for logger_name in APP_LOGGER_NAMES:
    logging.getLogger(logger_name).setLevel(level)
```

这段代码把我们的应用 logger 和 Uvicorn logger 都设置到同一个级别。

简单理解：

```text
LOG_LEVEL=DEBUG 时，让 app 和 uvicorn 都尽量输出 DEBUG
LOG_LEVEL=INFO 时，让 app 和 uvicorn 都按 INFO 输出
```

注意：

```text
Uvicorn 自己也有日志配置
```

比如命令行参数：

```powershell
uv run uvicorn app.main:app --reload --log-level debug
```

本节我们先控制应用内部日志。

后面如果做完整部署，会进一步统一 Uvicorn 和应用日志。

## 23. 在 main.py 里接入日志配置

文件：

```text
projects/ai-service/app/main.py
```

现在的核心逻辑：

```python
from fastapi import FastAPI

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.routers import chat, health


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
    )
    app.include_router(health.router)
    app.include_router(chat.router)
    return app
```

流程是：

```text
读取配置
根据配置设置日志
创建 FastAPI 应用
挂载路由
返回 app
```

这就是上一节 `.env 配置读取` 和本节 `logging 日志` 的连接点。

## 24. 在 /chat 里写业务日志

文件：

```text
projects/ai-service/app/routers/chat.py
```

现在核心代码：

```python
import logging

from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse


logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    logger.info("mock_chat_requested message_length=%s", len(request.message))
    return ChatResponse(reply=f"你刚才说的是：{request.message}")
```

重点是这行：

```python
logger.info("mock_chat_requested message_length=%s", len(request.message))
```

这表示：

```text
有一次 mock chat 请求发生了
用户消息长度是多少
```

## 25. 为什么不直接记录完整 message

你可能会想：

```python
logger.info("user_message=%s", request.message)
```

现在我们没有这样做。

原因是：

```text
用户输入可能包含隐私
用户输入可能包含账号、手机号、地址、公司数据
日志通常会被长期保存
很多人或系统可能能看到日志
```

所以本节先养成一个习惯：

```text
默认不要把完整用户输入写进日志
```

如果确实要记录，也要经过明确设计，例如：

```text
脱敏
截断
加权限
只在开发环境打开
```

AI 服务尤其要注意这一点。

因为用户给 AI 的内容可能很敏感。

## 26. 为什么日志内容用英文事件名

我们写的是：

```text
mock_chat_requested
```

而不是：

```text
模拟聊天接口被请求
```

原因是日志通常会被系统检索、统计、过滤。

英文事件名更适合机器处理：

```text
mock_chat_requested
llm_call_started
llm_call_failed
ticket_created
rag_retrieval_empty
```

但笔记和注释可以用中文解释。

## 27. 为什么使用 `%s`，不直接 f-string

我们写的是：

```python
logger.info("mock_chat_requested message_length=%s", len(request.message))
```

不是：

```python
logger.info(f"mock_chat_requested message_length={len(request.message)}")
```

两种写法都能运行。

但日志里更推荐第一种。

原因是：

```text
logging 会在真正需要输出这条日志时再格式化参数
这是 Python logging 的常见写法
以后接入日志系统时也更规范
```

你先记住这个习惯：

```python
logger.info("xxx=%s", value)
logger.error("failed reason=%s", reason)
```

## 28. 本节新增测试

新增文件：

```text
projects/ai-service/tests/test_logging.py
```

测试目标：

```text
确认日志级别可以正确解析
确认非法日志级别会报错
确认 configure_logging 会设置 app logger
确认 /chat 请求会写业务日志
```

## 29. 测试日志级别

```python
def test_get_log_level_accepts_known_level() -> None:
    assert get_log_level("INFO") == logging.INFO
```

这个测试说明：

```text
"INFO" 能转换成 logging.INFO
```

## 30. 测试大小写不敏感

```python
def test_get_log_level_is_case_insensitive() -> None:
    assert get_log_level("debug") == logging.DEBUG
```

这个测试说明：

```text
LOG_LEVEL="debug"
LOG_LEVEL="DEBUG"
```

都能识别。

## 31. 测试非法日志级别

```python
def test_get_log_level_rejects_unknown_level() -> None:
    with pytest.raises(ValueError) as exc_info:
        get_log_level("LOUD")

    assert "Unsupported log level" in str(exc_info.value)
```

这个测试说明：

```text
如果配置写错，程序不要假装没事
```

因为配置错误越早暴露越好。

## 32. 测试配置函数

```python
def test_configure_logging_sets_app_logger_level() -> None:
    configure_logging("ERROR")

    assert logging.getLogger("app").level == logging.ERROR
```

这个测试确认：

```text
configure_logging("ERROR")
```

真的会把 `app` logger 设置成 `ERROR`。

## 33. 测试 /chat 写日志

```python
def test_chat_writes_business_log(client: TestClient, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="app.routers.chat")

    response = client.post("/chat", json={"message": "测试日志"})

    assert response.status_code == 200
    assert "mock_chat_requested message_length=4" in caplog.text
```

这里出现一个新工具：

```text
caplog
```

`caplog` 是 pytest 提供的日志捕获工具。

它可以在测试里捕获日志内容。

这句：

```python
caplog.set_level(logging.INFO, logger="app.routers.chat")
```

表示：

```text
捕获 app.routers.chat 这个 logger 的 INFO 级别日志
```

然后请求 `/chat`：

```python
response = client.post("/chat", json={"message": "测试日志"})
```

最后断言日志里出现：

```text
mock_chat_requested message_length=4
```

为什么长度是 4？

因为：

```text
测
试
日
志
```

一共 4 个中文字符。

## 34. 当前你应该怎么运行

进入项目目录：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
```

运行测试：

```powershell
uv run pytest -q
```

启动服务：

```powershell
uv run uvicorn app.main:app --reload
```

如果你想本地临时看 DEBUG 日志，可以创建 `.env`：

```powershell
Copy-Item .env.example .env
```

然后修改：

```env
LOG_LEVEL="DEBUG"
```

再重启服务。

## 35. 当前项目里日志还缺什么

本节只是日志基础。

真实 AI 服务还需要：

```text
每个请求一个 trace_id
记录请求耗时
记录模型名
记录模型调用耗时
记录错误堆栈
记录统一错误响应
避免记录敏感信息
必要时输出 JSON 日志
```

这些不会一次性全塞进本节。

因为你现在要先理解：

```text
logging 是什么
logger 是什么
level 是什么
怎么配置
怎么测试
```

下一节会学：

```text
trace_id 请求追踪
```

到时候每次请求都会有一个唯一编号。

例如：

```text
trace_id=abc123
```

这样多行日志可以串成同一次请求。

## 36. 本节练习

### 练习 1

题目：

在 `.env` 里把：

```env
LOG_LEVEL="INFO"
```

改成：

```env
LOG_LEVEL="DEBUG"
```

然后重启服务。

说出这代表什么意思。

参考答案：

这表示应用日志级别改成 `DEBUG`。

理论上 `DEBUG`、`INFO`、`WARNING`、`ERROR`、`CRITICAL` 都可以输出。

因为 `DEBUG` 是最低的常用日志级别，门槛最低。

### 练习 2

题目：

在 `/chat` 接口里，为什么我们记录：

```python
len(request.message)
```

而不是直接记录：

```python
request.message
```

参考答案：

因为用户输入可能包含隐私或敏感数据。

日志通常会被保存和检索，不能随便把完整用户内容写进去。

记录长度可以证明请求发生过，也能提供一点排查信息，同时降低泄露风险。

### 练习 3

题目：

下面这行日志代码是什么意思？

```python
logger.info("mock_chat_requested message_length=%s", len(request.message))
```

参考答案：

它表示用当前模块的 logger 写一条 `INFO` 级别日志。

日志事件名是 `mock_chat_requested`。

`message_length=%s` 里的 `%s` 会被 `len(request.message)` 替换。

例如用户输入 `"测试日志"`，长度是 4，日志内容就是：

```text
mock_chat_requested message_length=4
```

### 练习 4

题目：

如果 `LOG_LEVEL="ERROR"`，下面哪些日志会输出？

```text
DEBUG
INFO
WARNING
ERROR
CRITICAL
```

参考答案：

会输出：

```text
ERROR
CRITICAL
```

不会输出：

```text
DEBUG
INFO
WARNING
```

因为日志级别是过滤门槛，`ERROR` 只允许错误及更严重的日志通过。

### 练习 5

题目：

为什么 `logger = logging.getLogger(__name__)` 比直接 `print()` 更适合后端项目？

参考答案：

因为 logger 会带模块名称，可以按级别控制，可以统一格式，也可以接入后续的日志收集系统。

`print()` 只能简单输出文本，不适合长期运行的后端服务。

## 37. 本节自测

### 自测 1

题目：

日志是什么？

参考答案：

日志是程序运行时留下的记录，用来帮助开发者了解服务运行状态、接口调用情况和错误原因。

### 自测 2

题目：

`print` 和 `logging` 的核心区别是什么？

参考答案：

`print` 只是简单输出文本。

`logging` 可以设置级别、格式、logger 名称和输出目标，更适合后端服务和生产环境。

### 自测 3

题目：

常见日志级别从低到高是什么？

参考答案：

从低到高是：

```text
DEBUG
INFO
WARNING
ERROR
CRITICAL
```

### 自测 4

题目：

`INFO` 通常用来记录什么？

参考答案：

`INFO` 通常用来记录程序正常运行过程中的关键事件，比如接口被调用、任务完成、服务启动成功。

### 自测 5

题目：

`ERROR` 通常用来记录什么？

参考答案：

`ERROR` 通常用来记录某个功能失败，例如模型调用失败、数据库查询失败或接口处理失败。

### 自测 6

题目：

`logging.getLogger(__name__)` 里的 `__name__` 有什么作用？

参考答案：

`__name__` 会让 logger 名称跟当前模块路径一致，比如 `app.routers.chat`。

这样日志里能看出记录来自哪个模块。

### 自测 7

题目：

`.env` 里的 `LOG_LEVEL` 有什么作用？

参考答案：

`LOG_LEVEL` 用来控制应用输出哪些级别的日志。

例如 `INFO` 会输出 `INFO` 及更严重级别，`ERROR` 只输出 `ERROR` 和 `CRITICAL`。

### 自测 8

题目：

为什么日志级别不应该写死在代码里？

参考答案：

因为不同环境需要不同日志级别。

开发环境可能需要 `DEBUG`，生产环境可能只需要 `INFO` 或 `WARNING`。

放在 `.env` 里可以不用改代码就调整。

### 自测 9

题目：

`caplog` 是什么？

参考答案：

`caplog` 是 pytest 的日志捕获工具。

它可以在测试里捕获 logger 输出的日志，并让我们断言日志内容是否出现。

### 自测 10

题目：

为什么不要随便把完整用户输入写进日志？

参考答案：

因为用户输入可能包含隐私、账号、手机号、公司数据或其他敏感信息。

日志可能长期保存，也可能被多人查看，所以要避免泄露。

## 38. 本节小结

这一节完成了日志基础：

```text
理解 print 和 logging 的区别
理解 logger
理解日志级别
用 LOG_LEVEL 控制日志级别
新增 app/core/logging.py
在 create_app() 里配置日志
在 /chat 里记录业务日志
用 pytest caplog 测试日志
```

当前项目已经具备最基础的应用日志能力。

下一节学习：

```text
trace_id 请求追踪
```

## 39. 参考资料

- [Python 官方文档：logging](https://docs.python.org/3/library/logging.html)
- [Python 官方文档：Logging HOWTO](https://docs.python.org/3/howto/logging.html)
- [Uvicorn 官方文档：Settings - Logging](https://uvicorn.dev/settings/)
- [Uvicorn 官方文档：Logging](https://uvicorn.dev/concepts/logging/)
