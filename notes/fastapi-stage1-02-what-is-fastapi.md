# FastAPI 阶段 1 第 2 节：FastAPI 是什么

日期：2026-07-06

本节目标：把 FastAPI 这个框架本身讲清楚。

上一节我们已经知道：

```text
客户端通过 HTTP 请求访问服务端。
服务端根据 URL 路径和 HTTP 方法找到对应处理逻辑。
处理逻辑返回响应。
接口通常返回 JSON。
```

这一节继续往下问：

```text
既然 Python 已经能写函数，为什么还要 FastAPI？
FastAPI 到底帮我们做了哪些事？
Uvicorn、FastAPI、Pydantic 分别是什么角色？
为什么写一个装饰器，就能把 URL 绑定到 Python 函数？
为什么 /docs 会自动出现？
```

## 1. 本节学什么

本节学习这些内容：

1. FastAPI 是什么。
2. 为什么普通 Python 函数不能直接当 Web API。
3. FastAPI 在一次请求里负责什么。
4. Uvicorn、FastAPI、Pydantic 的分工。
5. `FastAPI()` 创建了什么。
6. `@app.get()` / `@router.get()` 做了什么。
7. 路径操作 path operation 是什么。
8. FastAPI 为什么能自动生成 `/docs`。
9. FastAPI 为什么适合做 AI 服务。
10. FastAPI 和 Java Spring Boot 的类比。

先记住一句话：

```text
FastAPI 是一个用 Python 写 Web API 服务的框架。
```

更具体一点：

```text
FastAPI 帮我们把 HTTP 请求变成 Python 函数调用，
再把 Python 函数的返回值变成 HTTP JSON 响应。
```

## 2. 先用一句话理解 FastAPI

FastAPI 官方文档把它定义为一个用于构建 API 的现代 Python Web 框架，核心特点是基于标准 Python 类型提示。

初学阶段可以这样理解：

```text
FastAPI = 用 Python 写后端接口的工具箱。
```

它解决的是这类问题：

```text
外部程序发来了 HTTP 请求，
Python 代码怎么接住？
怎么知道该执行哪个函数？
怎么读取 URL 参数、查询参数、请求体？
怎么校验 JSON 数据？
怎么返回 JSON？
怎么生成接口文档？
怎么让测试工具调用接口？
```

这些事情如果全部自己写，会很麻烦。

FastAPI 的价值就是：

```text
把写 Web API 时大量重复、容易出错的工作封装好，
让我们把精力放在业务逻辑和 AI 能力上。
```

## 3. 为什么不能只用普通 Python 函数

普通 Python 函数是这样的：

```python
def health_check() -> dict[str, str]:
    return {"status": "ok"}
```

这个函数本身可以运行。

但外部浏览器不知道它存在。

浏览器只能发 HTTP 请求：

```text
GET /health
```

问题来了：

```text
浏览器发来的 GET /health，怎么找到 health_check 函数？
```

普通 Python 函数没有这个能力。

它只会被 Python 代码内部调用：

```python
result = health_check()
```

Web API 需要让外部程序通过 HTTP 调用函数。

所以中间需要一个框架帮我们做映射：

```text
HTTP 请求 GET /health
        ↓
FastAPI 路由匹配
        ↓
Python 函数 health_check()
        ↓
返回 Python 字典
        ↓
FastAPI 转成 JSON 响应
```

这就是 FastAPI 的核心作用。

## 4. 框架是什么

框架不是某个单独函数。

框架是一套已经写好的基础结构和规则。

你可以把框架理解成：

```text
别人帮你搭好的房子骨架。
你按照它的规则，把自己的房间、线路、家具放进去。
```

在 Web 服务里，框架通常负责：

- 接收请求。
- 匹配路由。
- 解析参数。
- 校验数据。
- 执行业务函数。
- 处理返回值。
- 生成响应。
- 处理异常。
- 支持中间件。
- 支持测试。
- 生成接口文档。

你写的代码只需要关注：

```text
这个接口要做什么业务。
```

比如：

```python
@router.get("/health")
def health_check() -> dict[str, object]:
    return {"status": "ok"}
```

你没有自己写 HTTP 报文解析，也没有自己拼响应头。

这些都是框架帮你做了。

## 5. FastAPI 在一次请求中做了什么

以当前 `/health` 为例。

客户端请求：

```text
GET /health
```

FastAPI 做的事情可以拆成：

```text
1. 接到 Uvicorn 转交过来的请求。
2. 看请求方法是 GET。
3. 看请求路径是 /health。
4. 在已经注册好的路由表里查找。
5. 找到 health_check 函数。
6. 调用 health_check 函数。
7. 拿到函数返回的 Python 字典。
8. 把字典转换成 JSON 响应。
9. 把响应交回给 Uvicorn。
10. Uvicorn 把响应发回客户端。
```

你可以先把 FastAPI 想成一个调度员：

```text
请求来了，它负责判断该交给哪个 Python 函数处理。
```

## 6. Uvicorn、FastAPI、Pydantic 分别是什么

这三个名字很容易混。

先看大图：

```text
浏览器 / 前端 / Java 服务
        ↓ HTTP 请求
Uvicorn
        ↓ ASGI 调用
FastAPI
        ↓ 路由、参数、校验、响应
你的 Python 函数
        ↓
FastAPI
        ↓
Uvicorn
        ↓ HTTP 响应
客户端
```

### 6.1 Uvicorn 是什么

Uvicorn 是服务器程序。

更具体地说，它是 ASGI server。

初学时可以理解成：

```text
Uvicorn = 真正负责监听端口、接收 HTTP 连接、把请求交给 FastAPI 的程序。
```

你运行：

```powershell
uv run uvicorn app.main:app --reload
```

其实是在启动 Uvicorn。

Uvicorn 会监听：

```text
127.0.0.1:8000
```

然后等待别人访问。

### 6.2 FastAPI 是什么

FastAPI 是 Web API 框架。

它负责：

```text
路由匹配
请求参数读取
请求体解析
数据校验
执行接口函数
响应转换
接口文档生成
```

你写：

```python
app = FastAPI()
```

就是创建了一个 FastAPI 应用对象。

### 6.3 Pydantic 是什么

Pydantic 是数据校验和数据模型工具。

后面写 `/chat` 时会用到：

```python
class ChatRequest(BaseModel):
    message: str
```

它的作用是：

```text
规定请求 JSON 应该长什么样，
并自动检查客户端传来的数据是否符合要求。
```

例如你要求：

```text
message 必须是字符串
```

客户端却传：

```json
{
  "message": 123
}
```

FastAPI 会借助 Pydantic 发现问题，并返回错误响应。

### 6.4 三者分工总结

| 名称 | 角色 | 你可以先理解成 |
| --- | --- | --- |
| Uvicorn | ASGI 服务器 | 门卫和网络入口 |
| FastAPI | Web API 框架 | 调度员和接口管理器 |
| Pydantic | 数据模型和校验 | 表格规则检查员 |

再简单一点：

```text
Uvicorn 负责跑起来。
FastAPI 负责接接口。
Pydantic 负责验数据。
```

## 7. ASGI 是什么

ASGI 是 Python Web 应用和服务器之间的一套标准接口。

你不需要一开始就深入 ASGI 协议。

现在只要知道：

```text
FastAPI 是 ASGI Web 框架。
Uvicorn 是 ASGI 服务器。
二者能配合，是因为它们遵守同一套接口规范。
```

类比 Java：

```text
Java 里不同组件之间也会遵守接口规范。
Python Web 里，ASGI 就是服务器和应用之间的接口标准之一。
```

所以：

```text
Uvicorn app.main:app
```

意思不是 Uvicorn 随便运行一个 Python 文件。

而是：

```text
Uvicorn 导入 app.main 这个模块里的 app 对象，
并把它当作 ASGI 应用来运行。
```

## 8. `FastAPI()` 创建了什么

看当前代码：

```python
from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Service",
        description="Python AI service for Java + Python + AI learning project.",
        version="0.1.0",
    )
    return app
```

这里的：

```python
app = FastAPI(...)
```

创建的是一个 FastAPI 应用对象。

它里面会保存很多信息：

- 应用标题。
- 应用描述。
- 应用版本。
- 已注册的路由。
- 中间件。
- 异常处理器。
- OpenAPI 文档配置。

你可以把 `app` 理解成：

```text
整个 API 服务的总入口对象。
```

后面 Uvicorn 要运行的也是它：

```text
app.main:app
```

冒号前面的 `app.main` 是模块。

冒号后面的 `app` 是 FastAPI 应用对象。

## 9. 为什么当前项目用了 `create_app()`

很多教程直接写：

```python
app = FastAPI()
```

我们当前项目写成：

```python
def create_app() -> FastAPI:
    app = FastAPI(...)
    app.include_router(health.router)
    return app


app = create_app()
```

这是为了让项目更适合后续扩展和测试。

### 9.1 直接写 `app = FastAPI()`

优点：

```text
简单，适合最小 demo。
```

缺点：

```text
后面配置、中间件、路由、异常处理多了以后，main.py 容易混乱。
```

### 9.2 使用 `create_app()`

优点：

```text
创建应用的过程集中在一个函数里。
测试时可以重新创建一个干净的 app。
以后加配置、日志、中间件、异常处理更清楚。
```

这也是我们从一开始就稍微工程化一点的原因。

## 10. `@router.get("/health")` 是什么

当前代码：

```python
@router.get("/health")
def health_check() -> dict[str, object]:
    return {
        "status": "ok",
        "service": "ai-service",
        "time": datetime.now(timezone.utc).isoformat(),
    }
```

这里的：

```python
@router.get("/health")
```

是一个装饰器。

初学阶段你可以这样理解：

```text
它告诉 FastAPI：
如果有人用 GET 方法访问 /health，
就执行下面这个 health_check 函数。
```

所以装饰器做了绑定：

```text
GET /health  ->  health_check()
```

没有这个装饰器，`health_check` 就只是一个普通 Python 函数。

有了这个装饰器，它就变成了一个能被 HTTP 请求触发的接口函数。

## 11. 什么是 path operation

FastAPI 官方文档里经常出现 path operation 这个说法。

拆开看：

```text
path      = 路径，比如 /health
operation = HTTP 方法，比如 GET、POST、PUT、DELETE
```

所以：

```text
GET /health
```

就是一个 path operation。

对应代码：

```python
@router.get("/health")
def health_check():
    ...
```

其中：

```text
path      = /health
operation = get
function  = health_check
```

中文可以叫：

```text
路径操作
```

但你不需要死记这个翻译。

知道它表示：

```text
某个 HTTP 方法 + 某个 URL 路径 + 某个处理函数
```

就够了。

## 12. 为什么 `/docs` 会自动出现

你启动服务后访问：

```text
http://127.0.0.1:8000/docs
```

会看到接口文档。

这是 FastAPI 自动生成的。

它能自动生成文档，是因为 FastAPI 知道：

- 你注册了哪些路径。
- 每个路径支持哪些 HTTP 方法。
- 请求参数是什么。
- 请求体模型是什么。
- 响应模型是什么。
- 状态码可能有哪些。
- 接口标题、描述、标签是什么。

这些信息会生成 OpenAPI schema。

你还可以访问：

```text
http://127.0.0.1:8000/openapi.json
```

这里能看到原始 JSON 格式的接口描述。

`/docs` 页面就是基于这些描述渲染出来的交互式文档。

## 13. OpenAPI 是什么

OpenAPI 是描述 API 的标准。

初学阶段可以这样理解：

```text
OpenAPI = 用机器能看懂的格式，描述你的接口有哪些、参数是什么、返回什么。
```

例如它会描述：

```text
/health 这个路径支持 GET。
它会返回 200 响应。
响应内容是 JSON。
```

这有什么用？

```text
1. 自动生成 /docs 页面。
2. 前端可以看接口怎么调用。
3. 测试人员可以直接调接口。
4. 将来可以生成客户端 SDK。
5. 团队协作时接口更清楚。
```

所以 FastAPI 不只是帮你写接口。

它还帮你把接口说明书自动生成出来。

## 14. FastAPI 为什么依赖 Python 类型提示

你之前学过类型提示：

```python
def add(a: int, b: int) -> int:
    return a + b
```

在普通 Python 里，类型提示主要帮助：

```text
人读代码
编辑器提示
静态检查工具分析
```

在 FastAPI 里，类型提示还能参与接口行为。

例如：

```python
def read_item(item_id: int):
    ...
```

FastAPI 可以知道：

```text
item_id 应该是整数。
```

再比如后面：

```python
class ChatRequest(BaseModel):
    message: str
```

FastAPI 可以知道：

```text
请求体里应该有 message。
message 应该是字符串。
```

这就是 FastAPI 和 Pydantic 配合的关键。

## 15. FastAPI 主要帮我们省了哪些事

如果不用 FastAPI，你可能要自己写：

```text
1. 监听端口。
2. 解析 HTTP 请求。
3. 判断 URL 路径。
4. 判断 GET/POST。
5. 读取请求头。
6. 读取请求体。
7. 解析 JSON。
8. 校验字段是否存在。
9. 校验字段类型是否正确。
10. 执行业务函数。
11. 把返回值转成 JSON。
12. 设置响应状态码。
13. 处理异常。
14. 生成接口文档。
15. 写接口测试工具。
```

FastAPI 帮我们处理了大量通用工作。

你真正要写的是：

```text
路径是什么
请求数据长什么样
业务逻辑是什么
返回数据长什么样
```

## 16. FastAPI 不是万能的

也要知道 FastAPI 不负责什么。

FastAPI 不负责：

- 替你设计业务逻辑。
- 替你写数据库表。
- 替你决定接口该怎么命名。
- 替你选择大模型。
- 替你写 prompt。
- 替你做 RAG 检索。
- 替你保证系统不会出错。
- 替你部署服务器。

FastAPI 是 API 服务框架。

它负责的是：

```text
把你的 Python 能力稳定地以 HTTP API 的形式暴露出去。
```

后面的 AI 能力，比如：

```text
LLM 调用
RAG 检索
Tool Calling
LangGraph 工作流
```

都会被包在 FastAPI 接口后面。

## 17. 为什么 FastAPI 适合做 AI 服务

我们学习路线是：

```text
Java 后端 + Python AI 服务 + LangChain/LangGraph + RAG + Tool Calling
```

为什么 Python AI 服务层适合用 FastAPI？

### 17.1 AI 生态主要在 Python

很多 AI 工具优先支持 Python：

- LangChain
- LangGraph
- Transformers
- sentence-transformers
- 向量库 SDK
- 各类模型 API SDK
- 数据处理工具

如果 AI 服务用 Python 写，接这些工具更自然。

### 17.2 Java 后端可以通过 HTTP 调 Python

Java 后端不需要直接运行 Python 代码。

它可以这样调用：

```text
Java 业务系统
        ↓ HTTP
Python FastAPI AI 服务
        ↓
LLM / RAG / Agent
```

这是一种很常见的服务拆分方式。

### 17.3 FastAPI 适合包装 AI 能力

比如：

```text
POST /chat
POST /stream-chat
POST /rag/query
POST /tickets/extract
```

这些接口背后可以调用：

```text
大模型
embedding 模型
向量数据库
LangChain
LangGraph
Java 业务 API
```

对外仍然是稳定的 HTTP API。

## 18. 和 Java Spring Boot 的类比

你有 Java 基础，可以这样对比：

| Java Spring Boot | Python FastAPI |
| --- | --- |
| `@SpringBootApplication` | `app = FastAPI()` |
| `@RestController` | router / path operation function |
| `@GetMapping("/health")` | `@router.get("/health")` |
| `@PostMapping("/chat")` | `@router.post("/chat")` |
| DTO | Pydantic `BaseModel` |
| Bean Validation | Pydantic 校验 |
| Controller 方法 | Python 接口函数 |
| SpringDoc / Swagger | FastAPI 自动 `/docs` |
| 内嵌 Tomcat / Jetty | Uvicorn |

但不要把它们完全等同。

重要差异：

```text
1. Java 是静态强类型语言，Python 是动态语言。
2. FastAPI 很依赖 Python 类型提示和 Pydantic。
3. Spring 的依赖注入体系和 FastAPI 的 Depends 不是一回事。
4. FastAPI 的 async/await 更常见，后面会专门学。
5. Python 项目结构和 Java Maven/Gradle 项目结构不同。
```

所以我们用 Java 经验帮助理解，但不会跳过 FastAPI 基础。

## 19. 当前项目代码对照

当前入口：

```text
projects/ai-service/app/main.py
```

核心代码：

```python
from fastapi import FastAPI

from app.routers import health


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Service",
        description="Python AI service for Java + Python + AI learning project.",
        version="0.1.0",
    )
    app.include_router(health.router)
    return app


app = create_app()
```

逐块理解：

```python
from fastapi import FastAPI
```

导入 FastAPI 类。

```python
from app.routers import health
```

导入健康检查路由模块。

```python
def create_app() -> FastAPI:
```

定义一个函数，用来创建 FastAPI 应用对象。

```python
app = FastAPI(...)
```

创建应用对象，并设置标题、描述、版本。

```python
app.include_router(health.router)
```

把健康检查这一组路由注册进总应用。

```python
return app
```

返回创建好的应用对象。

```python
app = create_app()
```

真正创建应用对象，供 Uvicorn 加载。

## 20. 当前 `/health` 代码对照

文件：

```text
projects/ai-service/app/routers/health.py
```

核心代码：

```python
from datetime import datetime, timezone

from fastapi import APIRouter


router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, object]:
    return {
        "status": "ok",
        "service": "ai-service",
        "time": datetime.now(timezone.utc).isoformat(),
    }
```

逐块理解：

```python
from fastapi import APIRouter
```

导入路由工具。

```python
router = APIRouter(tags=["health"])
```

创建一个路由分组。

这个分组专门放健康检查相关接口。

```python
@router.get("/health")
```

注册一个 GET 接口，路径是 `/health`。

```python
def health_check() -> dict[str, object]:
```

定义处理函数。

```python
return {...}
```

返回 Python 字典，FastAPI 会转换成 JSON 响应。

## 21. FastAPI 的执行链路

把当前项目串起来：

```text
uvicorn app.main:app
        ↓
导入 app/main.py
        ↓
拿到 app = create_app()
        ↓
create_app 里创建 FastAPI 对象
        ↓
include_router 注册 health.router
        ↓
health.router 里有 GET /health
        ↓
客户端访问 GET /health
        ↓
FastAPI 执行 health_check()
        ↓
返回 JSON
```

这一条链路必须慢慢看懂。

以后所有接口都是在这条链路上扩展。

比如 `/chat`：

```text
include_router(chat.router)
        ↓
chat.router 里有 POST /chat
        ↓
客户端提交 JSON
        ↓
FastAPI + Pydantic 校验
        ↓
执行 chat 函数
        ↓
返回 JSON
```

## 22. FastAPI 项目里常见对象

你后面会经常看到这些对象。

| 对象 | 作用 |
| --- | --- |
| `FastAPI` | 创建整个应用 |
| `APIRouter` | 拆分接口模块 |
| `BaseModel` | 定义请求和响应数据结构 |
| `Request` | 表示一次请求 |
| `Response` | 表示一次响应 |
| `HTTPException` | 主动返回 HTTP 错误 |
| `Depends` | 声明依赖 |
| Middleware | 中间件，处理请求前后逻辑 |
| TestClient | 测试接口 |

现阶段先重点掌握：

```text
FastAPI
APIRouter
BaseModel
TestClient
```

其他对象后面逐步学。

## 23. 常见误区

### 误区 1：FastAPI 就是服务器

不准确。

FastAPI 是 Web API 框架。

Uvicorn 才是当前负责运行和监听端口的服务器程序。

### 误区 2：有了 FastAPI 就不用理解 HTTP

不对。

FastAPI 帮你简化 HTTP 处理，但你仍然要懂：

```text
GET
POST
状态码
请求体
响应体
headers
JSON
```

不懂 HTTP，就很难设计好接口。

### 误区 3：`@router.get` 是普通注释

不对。

`@router.get("/health")` 是 Python 装饰器。

它不是注释。

它会让 FastAPI 记录：

```text
GET /health 由 health_check 处理。
```

### 误区 4：`/docs` 是自己写的接口

不是。

`/docs` 是 FastAPI 根据 OpenAPI schema 自动提供的交互式文档页面。

### 误区 5：FastAPI 会自动帮你写业务逻辑

不会。

FastAPI 帮你处理接口层。

真正的业务逻辑仍然要你写。

例如：

```text
用户问什么
调用哪个模型
是否检索知识库
是否调用 Java API
错误怎么兜底
```

这些都不是 FastAPI 自动决定的。

## 24. 本节练习

### 练习 1：说清楚三者分工

用自己的话解释：

```text
Uvicorn、FastAPI、Pydantic 分别负责什么？
```

### 练习 2：解释 `app = FastAPI()`

用自己的话解释：

```python
app = FastAPI()
```

这行代码创建了什么？

### 练习 3：解释装饰器绑定

用自己的话解释：

```python
@router.get("/health")
def health_check():
    ...
```

为什么访问 `GET /health` 会执行 `health_check`？

### 练习 4：打开自动文档

启动服务后访问：

```text
http://127.0.0.1:8000/docs
```

观察里面有没有 `GET /health`。

### 练习 5：打开 OpenAPI JSON

启动服务后访问：

```text
http://127.0.0.1:8000/openapi.json
```

在返回内容里找：

```text
/health
```

### 练习 6：和 Java 类比

把下面 FastAPI 写法类比到 Spring Boot：

```python
@router.get("/health")
def health_check():
    ...
```

它大概对应 Spring Boot 里的什么？

## 25. 本节练习参考答案

### 练习 1 参考答案

```text
Uvicorn：负责启动服务、监听端口、接收 HTTP 请求。
FastAPI：负责路由匹配、参数处理、调用接口函数、返回响应、生成文档。
Pydantic：负责定义数据模型和校验请求/响应数据。
```

更短的说法：

```text
Uvicorn 负责跑起来。
FastAPI 负责接接口。
Pydantic 负责验数据。
```

### 练习 2 参考答案

```python
app = FastAPI()
```

这行代码创建了一个 FastAPI 应用对象。

这个对象是整个 API 服务的总入口。

后面注册路由、中间件、异常处理、OpenAPI 文档信息，都会挂到这个应用对象上。

### 练习 3 参考答案

```python
@router.get("/health")
def health_check():
    ...
```

`@router.get("/health")` 会告诉 FastAPI：

```text
当收到 GET /health 请求时，调用下面的 health_check 函数。
```

所以访问 `GET /health` 会执行 `health_check`。

### 练习 4 参考答案

打开 `/docs` 后，应该能看到 `GET /health`。

如果看不到，先确认：

```text
1. 服务是否启动。
2. 当前端口是否是 8000。
3. app.include_router(health.router) 是否存在。
4. health.py 里是否写了 @router.get("/health")。
```

### 练习 5 参考答案

打开 `/openapi.json` 后，应该能在 JSON 里看到类似：

```json
{
  "paths": {
    "/health": {
      "get": {
        ...
      }
    }
  }
}
```

这说明 FastAPI 已经把 `/health` 接口记录进 OpenAPI schema。

### 练习 6 参考答案

大概对应 Spring Boot 里的：

```java
@GetMapping("/health")
public Map<String, Object> healthCheck() {
    ...
}
```

如果放在 Controller 里，整体概念类似：

```text
Spring Controller 方法  <->  FastAPI path operation function
@GetMapping             <->  @router.get
```

## 26. 自测问题

1. FastAPI 是什么？
2. 为什么普通 Python 函数不能直接被浏览器通过 URL 调用？
3. Uvicorn 是什么？
4. Pydantic 是什么？
5. `FastAPI()` 创建了什么？
6. `app.main:app` 里的两个 `app` 各是什么意思？
7. `@router.get("/health")` 是注释吗？
8. path operation 由哪三部分组成？
9. `/docs` 为什么会自动出现？
10. `/openapi.json` 是什么？
11. FastAPI 为什么适合做 Python AI 服务层？
12. FastAPI 会不会替你写 AI 业务逻辑？

## 27. 自测参考答案

1. FastAPI 是一个用 Python 构建 Web API 服务的框架，基于 Python 类型提示，常用于写 HTTP 接口。

2. 普通 Python 函数只能在 Python 代码内部被调用。浏览器发的是 HTTP 请求，需要框架把 URL 和 HTTP 方法映射到函数。

3. Uvicorn 是 ASGI 服务器，负责启动服务、监听端口、接收 HTTP 请求，并把请求交给 FastAPI 应用。

4. Pydantic 是数据模型和数据校验工具，FastAPI 用它来校验请求体、生成 schema、辅助生成接口文档。

5. `FastAPI()` 创建了一个 FastAPI 应用对象，它是整个 API 服务的总入口。

6. `app.main:app` 里，左边的 `app.main` 是 Python 模块路径，右边的 `app` 是模块里的 FastAPI 应用对象。

7. 不是。`@router.get("/health")` 是 Python 装饰器，用来把 `GET /health` 绑定到下面的函数。

8. path operation 可以理解为路径、HTTP 方法、处理函数三部分。例如 `/health`、`GET`、`health_check`。

9. 因为 FastAPI 会根据已注册的路由、参数、请求体和响应信息生成 OpenAPI schema，再用它提供交互式文档页面。

10. `/openapi.json` 是 FastAPI 自动生成的 API 描述 JSON，里面记录了接口路径、方法、参数、响应等信息。

11. 因为 AI 生态大量工具在 Python 里，FastAPI 又能把 Python 能力包装成 HTTP API，方便 Java 后端、前端或其他服务调用。

12. 不会。FastAPI 只负责接口层，真正的模型调用、RAG 检索、业务判断、异常兜底都要我们自己写。

## 28. 本节小结

这一节最重要的是分清角色：

```text
Uvicorn：负责把服务跑起来，监听端口。
FastAPI：负责 Web API 框架能力，把请求分发到函数。
Pydantic：负责数据结构和数据校验。
OpenAPI：负责描述接口，让文档和工具能读懂 API。
```

再记住当前项目链路：

```text
uvicorn app.main:app
        ↓
加载 FastAPI 应用对象
        ↓
FastAPI 注册 router
        ↓
router 绑定 GET /health
        ↓
客户端访问 /health
        ↓
执行 health_check
        ↓
返回 JSON
```

下一节学习：

```text
创建 projects/ai-service 项目骨架
```

虽然项目代码已经提前搭好，但我们会从零解释：

```text
为什么要有 app/
为什么要有 routers/
为什么要有 tests/
pyproject.toml 是什么
uv.lock 是什么
为什么不能把所有东西都放 main.py
```

## 29. 参考资料

- [FastAPI 官方首页](https://fastapi.tiangolo.com/)
- [FastAPI First Steps](https://fastapi.tiangolo.com/tutorial/first-steps/)
- [FastAPI Request Body](https://fastapi.tiangolo.com/tutorial/body/)
- [FastAPI Run a Server Manually](https://fastapi.tiangolo.com/deployment/manually/)
