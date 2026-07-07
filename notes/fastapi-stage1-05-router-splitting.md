# FastAPI 阶段 1 第 5 节：router 路由拆分

日期：2026-07-07

本节目标：彻底理解 FastAPI 里为什么要拆 router，以及 `main.py` 和 `app/routers/*.py` 应该怎么配合。

上一节我们已经讲清楚了 `/health`：

```text
GET /health -> health_check() -> return dict -> JSON 响应
```

这一节继续往下问：

```text
为什么 health_check 不直接写在 main.py？
为什么要有 app/routers/health.py？
APIRouter 到底是什么？
include_router 到底做了什么？
tags 和 prefix 有什么用？
以后 chat.py、rag.py、tickets.py 应该怎么拆？
```

## 1. 本节学什么

本节学习这些内容：

1. router 是什么。
2. 路由拆分解决什么问题。
3. `APIRouter` 是什么。
4. 为什么说 `APIRouter` 像“小 FastAPI”。
5. `main.py` 应该负责什么。
6. `health.py` 应该负责什么。
7. `include_router()` 是什么。
8. `tags` 是什么。
9. `prefix` 是什么。
10. router 文件如何命名。
11. 一个接口应该放在哪个 router。
12. 以后 `/chat`、`/rag/query`、`/tickets/extract` 怎么组织。
13. 路由拆分常见错误。

先记住一句话：

```text
router = 一组相关接口的集合。
```

再记住一句话：

```text
main.py 负责组装应用，router 文件负责定义接口。
```

## 2. 什么是路由

在 Web API 里，路由可以先理解成：

```text
请求地址和处理函数之间的对应关系。
```

例如：

```text
GET /health -> health_check()
```

这就是一条路由。

再比如以后：

```text
POST /chat -> chat()
POST /rag/query -> query_rag()
POST /tickets/extract -> extract_ticket()
```

这些都是路由。

所以路由不是文件夹。

路由本质上是：

```text
HTTP 方法 + URL 路径 + Python 处理函数
```

## 3. 什么是 router

router 是路由集合。

比如：

```text
health router
  GET /health

chat router
  POST /chat
  POST /stream-chat

rag router
  POST /rag/query
  POST /rag/documents

tickets router
  POST /tickets/extract
  POST /tickets/create
```

一个 router 里通常放一组相关接口。

你可以这样理解：

```text
路由 = 一条接口映射。
router = 一组接口映射。
```

## 4. 为什么要拆 router

如果项目很小，可以直接写：

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/chat")
def chat():
    return {"reply": "hello"}
```

这在 demo 里没问题。

但真实项目会越来越多：

```text
/health
/chat
/stream-chat
/rag/query
/rag/documents
/tickets/extract
/tickets/create
/admin/config
/metrics
```

如果全部写在 `main.py`，很快会出现问题：

```text
main.py 越来越长。
不同业务接口混在一起。
找代码困难。
改代码容易误伤。
测试组织困难。
多人协作容易冲突。
```

拆 router 是为了：

```text
按业务模块组织接口。
让 main.py 保持清爽。
让每个文件职责清楚。
方便后续扩展和测试。
```

## 5. 当前项目已经怎么拆了

当前项目：

```text
projects/ai-service/
  app/
    main.py
    routers/
      __init__.py
      health.py
```

`main.py`：

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

`health.py`：

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

当前分工：

```text
main.py   创建应用，注册 router。
health.py 定义健康检查接口。
```

## 6. `APIRouter` 是什么

代码：

```python
from fastapi import APIRouter
```

`APIRouter` 是 FastAPI 提供的路由分组工具。

FastAPI 官方文档里说，`APIRouter` 可以用来把 path operations 分组，从而把应用结构拆到多个文件里。

初学阶段可以理解成：

```text
APIRouter = 一组接口的小容器。
```

或者：

```text
APIRouter = 小型的接口管理器。
```

它不是完整应用。

完整应用是：

```python
app = FastAPI()
```

router 是一部分接口：

```python
router = APIRouter()
```

## 7. 为什么说 APIRouter 像“小 FastAPI”

FastAPI 官方文档里提到，你可以把 `APIRouter` 想成一个“小 FastAPI”。

原因是它也能写：

```python
@router.get(...)
@router.post(...)
@router.put(...)
@router.delete(...)
```

这和：

```python
@app.get(...)
@app.post(...)
```

很像。

区别是：

```text
FastAPI app 是主应用。
APIRouter router 是接口分组。
```

router 不能单独作为最终服务入口。

它通常需要被：

```python
app.include_router(router)
```

注册到主应用里。

## 8. `main.py` 应该负责什么

`main.py` 是应用总入口。

它应该负责：

```text
创建 FastAPI 应用对象。
注册 router。
注册 CORS。
注册 middleware。
注册异常处理器。
读取基础配置。
初始化应用级能力。
```

它不应该负责：

```text
堆所有接口函数。
堆所有请求模型。
堆所有业务逻辑。
堆所有大模型调用代码。
堆所有数据库访问代码。
```

所以 `main.py` 更像：

```text
装配中心。
```

不是：

```text
所有业务代码的堆放处。
```

## 9. router 文件应该负责什么

以：

```text
app/routers/health.py
```

为例。

这个文件应该只负责健康检查相关接口。

比如现在：

```text
GET /health
```

将来如果有：

```text
GET /ready
```

也可以考虑放在 health 相关模块里。

但是不应该把聊天接口也放进去：

```text
POST /chat
```

因为聊天接口和健康检查不是一类职责。

router 文件应该遵循：

```text
一个文件负责一组相关接口。
```

## 10. `include_router()` 是什么

当前代码：

```python
app.include_router(health.router)
```

意思是：

```text
把 health.router 里面的所有路由加入主 FastAPI 应用。
```

如果 `health.router` 里面有：

```text
GET /health
GET /ready
```

那么：

```python
app.include_router(health.router)
```

会把这两个接口都注册到主应用里。

所以：

```text
router 文件定义接口。
include_router 把接口挂到主应用。
```

如果忘记 `include_router()`：

```text
router 文件里的接口不会生效。
访问对应路径会返回 404。
```

## 11. `tags` 是什么

当前代码：

```python
router = APIRouter(tags=["health"])
```

`tags` 用来给接口文档分组。

打开：

```text
http://127.0.0.1:8000/docs
```

你会看到 `/health` 被归到 `health` 分组。

所以：

```text
tags 主要影响自动文档显示。
```

它不是 URL 路径。

它不会把路径变成：

```text
/health/health
```

它只是在文档里分组展示。

## 12. `prefix` 是什么

`prefix` 是路径前缀。

例如：

```python
router = APIRouter(prefix="/api/v1", tags=["chat"])
```

如果下面写：

```python
@router.post("/chat")
def chat():
    ...
```

最终路径会是：

```text
POST /api/v1/chat
```

再比如：

```python
router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/query")
def query_rag():
    ...
```

最终路径是：

```text
POST /rag/query
```

所以：

```text
prefix = 给这个 router 里所有路径统一加前缀。
```

## 13. 当前 health 为什么没用 prefix

当前写法：

```python
router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    ...
```

最终路径：

```text
GET /health
```

也可以写成：

```python
router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check():
    ...
```

最终路径也可以是：

```text
GET /health
```

但当前项目选择第一种，是因为现在只有一个健康检查接口，写起来更直观。

后面像 RAG 这种一组路径更适合 prefix：

```python
router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/query")
def query():
    ...


@router.post("/documents")
def add_document():
    ...
```

这样最终路径是：

```text
POST /rag/query
POST /rag/documents
```

结构更清楚。

## 14. prefix 常见错误

错误写法：

```python
router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/rag/query")
def query():
    ...
```

最终路径会变成：

```text
POST /rag/rag/query
```

因为 prefix 已经加了一次 `/rag`。

正确写法：

```python
router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/query")
def query():
    ...
```

最终路径：

```text
POST /rag/query
```

记住：

```text
prefix 负责公共前缀。
装饰器里的 path 只写剩余部分。
```

## 15. 将来 chat router 应该怎么写

后面我们会增加：

```text
app/routers/chat.py
```

大概结构会是：

```python
from fastapi import APIRouter


router = APIRouter(tags=["chat"])


@router.post("/chat")
def chat():
    ...
```

然后在 `main.py` 里：

```python
from app.routers import chat, health


def create_app() -> FastAPI:
    app = FastAPI(...)
    app.include_router(health.router)
    app.include_router(chat.router)
    return app
```

这样：

```text
health.py 管 /health
chat.py 管 /chat
main.py 只负责注册它们
```

## 16. 将来 RAG router 应该怎么写

RAG 可能有多个接口：

```text
POST /rag/query
POST /rag/documents
GET  /rag/documents/{document_id}
```

更适合使用 prefix：

```python
from fastapi import APIRouter


router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/query")
def query_rag():
    ...


@router.post("/documents")
def add_document():
    ...
```

然后注册：

```python
app.include_router(rag.router)
```

这样路径清楚，文档分组也清楚。

## 17. 将来 tickets router 应该怎么写

智能工单相关接口可能有：

```text
POST /tickets/extract
POST /tickets/create
GET  /tickets/{ticket_id}
```

可以写：

```python
router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("/extract")
def extract_ticket():
    ...


@router.post("/create")
def create_ticket():
    ...
```

最终路径：

```text
POST /tickets/extract
POST /tickets/create
```

这样很容易看出这些接口属于工单模块。

## 18. router 文件命名规则

建议：

```text
health.py
chat.py
rag.py
tickets.py
admin.py
```

命名原则：

```text
按业务模块命名。
尽量短。
尽量明确。
不要叫 api1.py、test_router.py、misc.py。
```

不推荐：

```text
router1.py
all_api.py
common.py
aaa.py
```

因为这些名字不能说明职责。

## 19. 一个接口应该放在哪个 router

判断标准：

```text
这个接口服务于哪个业务模块？
```

例如：

```text
GET /health              -> health.py
POST /chat               -> chat.py
POST /stream-chat        -> chat.py
POST /rag/query          -> rag.py
POST /tickets/extract    -> tickets.py
```

如果一个接口很难判断放哪里，通常说明：

```text
接口命名还不清楚。
业务边界还没想清楚。
```

不要急着写代码，先把职责想清楚。

## 20. router 和 service 的区别

后面会出现：

```text
routers/
services/
```

它们不是一回事。

router 负责接口层：

```text
接收请求。
调用业务逻辑。
返回响应。
```

service 负责业务逻辑：

```text
调用大模型。
检索知识库。
处理规则。
调用 Java API。
组合结果。
```

例如以后：

```text
routers/chat.py       定义 POST /chat
services/chat.py      实际处理聊天逻辑
```

router 不应该塞太多业务逻辑。

初学阶段先记住：

```text
router 管 HTTP 接口。
service 管业务处理。
```

## 21. router 和 schema 的区别

后面也会出现：

```text
schemas/
```

schema 负责数据结构。

例如：

```python
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
```

router 使用 schema：

```python
@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    ...
```

所以：

```text
router 管接口地址和请求处理函数。
schema 管请求/响应数据长什么样。
```

下一阶段学 Pydantic 时会详细讲。

## 22. 当前项目为什么还没有 services 和 schemas

因为当前只有：

```text
GET /health
```

没有复杂请求体。

没有业务逻辑。

没有模型调用。

所以暂时不需要：

```text
schemas/
services/
```

不要为了显得专业就提前建很多空目录。

正确方式是：

```text
项目需要某个职责时，再创建对应目录。
```

后面做 `/chat` 时，我们会加 Pydantic 请求/响应模型。

那时再讨论是否创建 `schemas/`。

## 23. 和 Java Spring Boot 的类比

你可以这样类比：

| Java Spring Boot | FastAPI |
| --- | --- |
| Controller 类 | router 文件 |
| `@RestController` | `APIRouter()` |
| `@GetMapping` | `@router.get` |
| `@PostMapping` | `@router.post` |
| Controller 注册到 Spring 容器 | `app.include_router()` |
| Swagger tags | `tags=["..."]` |

但注意：

```text
FastAPI router 文件不是类。
它通常是一个 Python 模块，里面有 router 对象和函数。
```

不要强行套 Java 的类结构。

Python 项目更常见的是：

```text
模块 + 函数 + 对象
```

## 24. 路由拆分后的完整执行链路

当前项目链路：

```text
uvicorn app.main:app
        ↓
加载 app/main.py
        ↓
from app.routers import health
        ↓
加载 app/routers/health.py
        ↓
创建 health.router
        ↓
@router.get("/health") 注册路由到 health.router
        ↓
create_app()
        ↓
app.include_router(health.router)
        ↓
主应用拥有 GET /health
        ↓
客户端访问 GET /health
        ↓
执行 health_check()
```

这条链路很重要。

以后多一个 router，就是多一个：

```python
app.include_router(xxx.router)
```

## 25. 常见错误

### 错误 1：写了 router 文件，但忘了 include_router

现象：

```text
访问接口返回 404。
```

原因：

```text
接口只定义在 router 里，没有注册到主应用。
```

解决：

```python
app.include_router(chat.router)
```

### 错误 2：prefix 写重复

错误：

```python
router = APIRouter(prefix="/rag")


@router.post("/rag/query")
def query():
    ...
```

最终路径：

```text
/rag/rag/query
```

正确：

```python
router = APIRouter(prefix="/rag")


@router.post("/query")
def query():
    ...
```

### 错误 3：tags 当成路径

错误理解：

```text
tags=["health"] 会让路径自动加 /health
```

这是错的。

`tags` 只影响文档分组。

路径由：

```text
prefix + 装饰器里的 path
```

决定。

### 错误 4：router 里写太多业务逻辑

router 应该薄一点。

它主要做：

```text
接收请求。
调用 service。
返回响应。
```

大量业务逻辑以后应该拆到 service。

### 错误 5：router 文件命名太随意

不推荐：

```text
api.py
router.py
test.py
common.py
```

推荐按业务命名：

```text
health.py
chat.py
rag.py
tickets.py
```

## 26. 本节必须掌握的最小知识

这一节最少要掌握：

```text
路由 = HTTP 方法 + URL 路径 + 处理函数。
router = 一组相关路由。
APIRouter = FastAPI 的路由分组工具。
main.py = 应用装配中心。
router 文件 = 定义具体接口。
include_router = 把 router 注册到主应用。
tags = 自动文档分组。
prefix = 一组接口的统一路径前缀。
```

## 27. 本节练习

### 练习 1：解释 router

题目：

用自己的话解释：

```text
router 是什么？
它和一条路由有什么区别？
```

### 练习 2：解释 include_router

题目：

用自己的话解释：

```python
app.include_router(health.router)
```

这行代码做了什么？如果忘记写会怎样？

### 练习 3：解释 tags

题目：

用自己的话解释：

```python
router = APIRouter(tags=["health"])
```

`tags=["health"]` 的作用是什么？它会改变 URL 吗？

### 练习 4：解释 prefix

题目：

下面代码的最终路径是什么？

```python
router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/query")
def query_rag():
    ...
```

### 练习 5：找出 prefix 错误

题目：

下面代码有什么问题？

```python
router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("/tickets/create")
def create_ticket():
    ...
```

### 练习 6：判断接口应该放哪个文件

题目：

判断下面接口应该放在哪个 router 文件：

```text
GET /health
POST /chat
POST /stream-chat
POST /rag/query
POST /tickets/extract
```

### 练习 7：解释 main.py 和 router 文件分工

题目：

用自己的话解释：

```text
main.py 应该负责什么？
router 文件应该负责什么？
```

## 28. 本节练习参考答案

### 练习 1 参考答案：解释 router

题目：

用自己的话解释：

```text
router 是什么？
它和一条路由有什么区别？
```

参考答案：

一条路由是一个 HTTP 方法、URL 路径和处理函数的对应关系。

例如：

```text
GET /health -> health_check()
```

router 是一组相关路由的集合。

例如 health router 里可以放健康检查相关接口，chat router 里可以放聊天相关接口。

简单说：

```text
路由是一条映射。
router 是一组映射。
```

### 练习 2 参考答案：解释 include_router

题目：

用自己的话解释：

```python
app.include_router(health.router)
```

这行代码做了什么？如果忘记写会怎样？

参考答案：

这行代码把 `health.router` 里面定义的所有接口注册到主 FastAPI 应用里。

如果忘记写，`health.py` 里的接口虽然存在于 router 对象中，但主应用不知道它们。

结果通常是：

```text
访问 /health 返回 404 Not Found。
```

### 练习 3 参考答案：解释 tags

题目：

用自己的话解释：

```python
router = APIRouter(tags=["health"])
```

`tags=["health"]` 的作用是什么？它会改变 URL 吗？

参考答案：

`tags=["health"]` 用来在 `/docs` 自动文档里把接口归到 `health` 分组。

它不会改变 URL。

URL 由 `prefix` 和装饰器里的路径决定，不由 `tags` 决定。

### 练习 4 参考答案：解释 prefix

题目：

下面代码的最终路径是什么？

```python
router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/query")
def query_rag():
    ...
```

参考答案：

最终路径是：

```text
POST /rag/query
```

原因是：

```text
prefix 是 /rag
装饰器 path 是 /query
合起来是 /rag/query
```

### 练习 5 参考答案：找出 prefix 错误

题目：

下面代码有什么问题？

```python
router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("/tickets/create")
def create_ticket():
    ...
```

参考答案：

问题是路径前缀写重复了。

`prefix` 已经是：

```text
/tickets
```

装饰器里又写：

```text
/tickets/create
```

最终路径会变成：

```text
POST /tickets/tickets/create
```

更合理的写法是：

```python
router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("/create")
def create_ticket():
    ...
```

最终路径：

```text
POST /tickets/create
```

### 练习 6 参考答案：判断接口应该放哪个文件

题目：

判断下面接口应该放在哪个 router 文件：

```text
GET /health
POST /chat
POST /stream-chat
POST /rag/query
POST /tickets/extract
```

参考答案：

| 接口 | 建议文件 | 原因 |
| --- | --- | --- |
| `GET /health` | `app/routers/health.py` | 健康检查 |
| `POST /chat` | `app/routers/chat.py` | 聊天接口 |
| `POST /stream-chat` | `app/routers/chat.py` | 流式聊天也属于聊天模块 |
| `POST /rag/query` | `app/routers/rag.py` | 知识库问答 |
| `POST /tickets/extract` | `app/routers/tickets.py` | 工单字段提取 |

### 练习 7 参考答案：解释 main.py 和 router 文件分工

题目：

用自己的话解释：

```text
main.py 应该负责什么？
router 文件应该负责什么？
```

参考答案：

`main.py` 应该负责应用级装配，比如创建 `FastAPI` 应用对象、注册 router、注册 CORS、中间件和异常处理器。

router 文件应该负责具体接口定义，比如 `health.py` 负责 `/health`，`chat.py` 负责 `/chat`。

简单说：

```text
main.py 管组装。
router 文件管接口。
```

## 29. 自测问题

1. 路由是什么？
2. router 是什么？
3. 为什么真实项目不建议把所有接口都写进 `main.py`？
4. `APIRouter` 是什么？
5. 为什么说 `APIRouter` 像“小 FastAPI”？
6. `include_router()` 有什么作用？
7. `tags` 有什么作用？
8. `prefix` 有什么作用？
9. `tags` 会不会改变 URL？
10. `prefix="/rag"` 加 `@router.post("/query")` 的最终路径是什么？
11. `main.py` 和 `routers/health.py` 分别负责什么？
12. 后面 `/chat` 应该放在哪个文件？
13. 后面 `/rag/query` 适合用 prefix 吗？
14. router 和 service 有什么区别？
15. router 和 schema 有什么区别？

## 30. 自测参考答案

### 自测 1 参考答案

题目：

路由是什么？

答案：

路由是 HTTP 方法、URL 路径和处理函数之间的对应关系。

例如：

```text
GET /health -> health_check()
```

### 自测 2 参考答案

题目：

router 是什么？

答案：

router 是一组相关路由的集合，用来把同一类接口组织在一起。

例如 health router 放健康检查接口，chat router 放聊天接口。

### 自测 3 参考答案

题目：

为什么真实项目不建议把所有接口都写进 `main.py`？

答案：

因为项目变大后，`main.py` 会变得很长，不同业务接口混在一起，查找、修改、测试和多人协作都会变困难。

把接口拆到不同 router 文件，可以让职责更清楚。

### 自测 4 参考答案

题目：

`APIRouter` 是什么？

答案：

`APIRouter` 是 FastAPI 提供的路由分组工具，用来组织一组 path operations，然后通过 `include_router()` 注册到主应用。

### 自测 5 参考答案

题目：

为什么说 `APIRouter` 像“小 FastAPI”？

答案：

因为 `APIRouter` 也可以使用 `@router.get()`、`@router.post()` 等方式声明接口，写法和 `FastAPI` 应用对象上的 `@app.get()` 很像。

但它不是主应用，需要注册到主应用里。

### 自测 6 参考答案

题目：

`include_router()` 有什么作用？

答案：

`include_router()` 把某个 router 中定义的所有路由加入主 FastAPI 应用。

### 自测 7 参考答案

题目：

`tags` 有什么作用？

答案：

`tags` 用来在 OpenAPI 和 `/docs` 自动文档中给接口分组。

### 自测 8 参考答案

题目：

`prefix` 有什么作用？

答案：

`prefix` 给 router 里的所有接口统一添加路径前缀。

例如 `prefix="/rag"` 加 `@router.post("/query")`，最终路径是 `/rag/query`。

### 自测 9 参考答案

题目：

`tags` 会不会改变 URL？

答案：

不会。

`tags` 只影响文档分组，不影响 URL。

### 自测 10 参考答案

题目：

`prefix="/rag"` 加 `@router.post("/query")` 的最终路径是什么？

答案：

最终路径是：

```text
POST /rag/query
```

### 自测 11 参考答案

题目：

`main.py` 和 `routers/health.py` 分别负责什么？

答案：

`main.py` 负责创建 FastAPI 应用对象并注册 router。

`routers/health.py` 负责定义健康检查相关接口。

### 自测 12 参考答案

题目：

后面 `/chat` 应该放在哪个文件？

答案：

建议放在：

```text
app/routers/chat.py
```

因为它属于聊天模块。

### 自测 13 参考答案

题目：

后面 `/rag/query` 适合用 prefix 吗？

答案：

适合。

可以创建：

```python
router = APIRouter(prefix="/rag", tags=["rag"])
```

然后写：

```python
@router.post("/query")
```

最终路径就是：

```text
POST /rag/query
```

### 自测 14 参考答案

题目：

router 和 service 有什么区别？

答案：

router 负责 HTTP 接口层，比如接收请求、调用业务逻辑、返回响应。

service 负责业务逻辑，比如调用模型、检索知识库、调用 Java API、组合结果。

### 自测 15 参考答案

题目：

router 和 schema 有什么区别？

答案：

router 管接口路径和处理函数。

schema 管请求和响应数据结构，比如 Pydantic 的 `ChatRequest`、`ChatResponse`。

## 31. 本节小结

这一节最重要的是理解职责拆分：

```text
main.py 是应用入口和装配中心。
routers/ 是接口分组目录。
APIRouter 用来收纳一组相关接口。
include_router 把接口分组挂到主应用。
tags 管文档分组。
prefix 管统一路径前缀。
```

当前项目已经有：

```text
health.py -> GET /health
```

后续会逐步增加：

```text
chat.py    -> POST /chat、POST /stream-chat
rag.py     -> POST /rag/query
tickets.py -> POST /tickets/extract
```

下一节学习：

```text
POST、请求体和 JSON
```

下一节会讲：

```text
为什么 /chat 不能只用 GET
POST 请求和 GET 请求有什么区别
请求体 body 是什么
JSON 请求体是什么
FastAPI 怎么接收 JSON
```

## 32. 参考资料

- [FastAPI Bigger Applications - Multiple Files](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [FastAPI APIRouter Reference](https://fastapi.tiangolo.com/reference/apirouter/)
- [FastAPI Path Operation Configuration](https://fastapi.tiangolo.com/tutorial/path-operation-configuration/)
