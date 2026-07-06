# FastAPI 阶段 1 第 4 节：最小服务 `/health`

日期：2026-07-06

本节目标：把当前项目里已经存在的 `/health` 健康检查接口彻底讲明白。

这一节会围绕两个文件：

```text
projects/ai-service/app/main.py
projects/ai-service/app/routers/health.py
```

你学完以后，要能完整解释：

```text
为什么访问 http://127.0.0.1:8000/health
会执行 health_check 函数，
并返回 JSON。
```

## 1. 本节学什么

本节学习这些内容：

1. `/health` 接口是什么。
2. 为什么服务需要健康检查接口。
3. `app/main.py` 在项目里负责什么。
4. `create_app()` 是什么。
5. `FastAPI()` 是什么。
6. `app = create_app()` 是什么。
7. `include_router()` 是什么。
8. `APIRouter()` 是什么。
9. `@router.get("/health")` 是什么。
10. `health_check()` 是什么。
11. `return dict` 为什么会变成 JSON。
12. `datetime.now(timezone.utc).isoformat()` 是什么。
13. `/health` 的完整执行链路。
14. `/health` 测试在测什么。

先记住一句话：

```text
/health 是服务健康检查接口，用来告诉调用方：这个服务当前还能正常响应。
```

## 2. 什么是健康检查接口

健康检查接口通常叫：

```text
/health
/healthz
/ping
/status
```

它的作用是：

```text
让外部系统快速判断服务是否活着。
```

比如：

```text
浏览器访问 /health
运维监控访问 /health
Docker / Kubernetes 访问 /health
Java 后端访问 /health
测试程序访问 /health
```

如果返回正常：

```json
{
  "status": "ok"
}
```

就说明服务至少能接收请求并返回响应。

## 3. 健康检查不等于业务一定正常

注意：

```text
/health 正常，只能说明服务基本活着。
不代表所有业务都一定正常。
```

比如：

```text
FastAPI 服务活着，但数据库挂了。
FastAPI 服务活着，但大模型 API key 错了。
FastAPI 服务活着，但向量库连接失败。
```

这些都可能发生。

所以健康检查也分层：

```text
浅层健康检查：服务能返回响应。
深层健康检查：数据库、缓存、模型服务、向量库都能连接。
```

当前我们的 `/health` 是浅层健康检查。

先做浅层检查是合理的，因为现在项目刚开始。

## 4. 当前 `/health` 返回什么

当前接口返回：

```json
{
  "status": "ok",
  "service": "ai-service",
  "time": "2026-07-06T08:00:00+00:00"
}
```

字段含义：

| 字段 | 含义 |
| --- | --- |
| `status` | 服务状态，`ok` 表示正常 |
| `service` | 服务名称 |
| `time` | 服务端当前 UTC 时间 |

为什么要有 `service`？

因为以后可能有多个服务：

```text
java-api
ai-service
rag-service
worker-service
```

返回服务名有助于确认你访问的是哪个服务。

为什么要有 `time`？

因为它能说明：

```text
响应是当前服务新生成的，不是你误看了旧内容。
```

## 5. 先看 `app/main.py`

文件：

```text
projects/ai-service/app/main.py
```

当前代码：

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

这个文件是 FastAPI 应用入口。

简单说：

```text
main.py 负责创建 FastAPI 应用，并把各个接口模块注册进去。
```

## 6. `from fastapi import FastAPI`

代码：

```python
from fastapi import FastAPI
```

意思是：

```text
从 fastapi 这个包里导入 FastAPI 类。
```

`FastAPI` 是用来创建应用对象的类。

你可以先理解成：

```text
FastAPI 类 = 用来创建整个 Web API 应用的模板。
```

后面：

```python
app = FastAPI(...)
```

就是根据这个类创建一个具体应用对象。

## 7. `from app.routers import health`

代码：

```python
from app.routers import health
```

意思是：

```text
从 app/routers/ 这个包里导入 health.py 这个模块。
```

对应文件：

```text
app/routers/health.py
```

为什么要导入它？

因为 `health.py` 里有：

```python
router = APIRouter(tags=["health"])
```

以及：

```python
@router.get("/health")
def health_check():
    ...
```

`main.py` 需要拿到这个 router，然后注册到主应用里。

## 8. `create_app()` 是什么

代码：

```python
def create_app() -> FastAPI:
```

它定义了一个函数，名字叫 `create_app`。

返回值类型提示是：

```python
-> FastAPI
```

意思是：

```text
这个函数会返回一个 FastAPI 应用对象。
```

为什么要专门写一个 `create_app()`？

因为创建应用通常不止一行。

以后这里会越来越多：

```text
创建 FastAPI 对象
注册 router
注册 CORS
注册 middleware
注册异常处理器
读取配置
初始化日志
```

把这些都放进 `create_app()`，结构更清楚。

## 9. `app = FastAPI(...)` 是什么

代码：

```python
app = FastAPI(
    title="AI Service",
    description="Python AI service for Java + Python + AI learning project.",
    version="0.1.0",
)
```

它创建了一个 FastAPI 应用对象。

这个对象是整个服务的总入口。

参数含义：

| 参数 | 含义 |
| --- | --- |
| `title` | 接口文档里的服务标题 |
| `description` | 接口文档里的服务描述 |
| `version` | 接口文档里的服务版本 |

这些信息会出现在：

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/openapi.json
```

所以它们不只是装饰文字。

它们也是接口文档的一部分。

## 10. `app.include_router(health.router)` 是什么

代码：

```python
app.include_router(health.router)
```

意思是：

```text
把 health 模块里的 router 注册到主 FastAPI 应用里。
```

如果没有这一行，会发生什么？

`health.py` 里虽然定义了：

```python
@router.get("/health")
def health_check():
    ...
```

但主应用并不知道它。

结果就是：

```text
访问 /health 可能得到 404 Not Found。
```

所以：

```text
定义 router 只是创建接口分组。
include_router 才是把这个分组挂到主应用上。
```

## 11. `return app` 是什么

代码：

```python
return app
```

意思是：

```text
把创建好、注册好 router 的 FastAPI 应用对象返回出去。
```

这个返回值会被下面这行拿到：

```python
app = create_app()
```

## 12. `app = create_app()` 是什么

代码：

```python
app = create_app()
```

它真正执行 `create_app()`。

执行结果是：

```text
得到一个 FastAPI 应用对象，并把它赋值给模块级变量 app。
```

为什么变量名必须叫 `app` 吗？

不是必须。

但启动命令里写的是：

```powershell
uv run uvicorn app.main:app --reload
```

这里的：

```text
app.main:app
```

右边的 `app` 指的就是 `app/main.py` 里的这个变量。

如果你把变量改成：

```python
api = create_app()
```

那启动命令也要改成：

```powershell
uv run uvicorn app.main:api --reload
```

所以当前保持 `app` 是最常见写法。

## 13. 再看 `health.py`

文件：

```text
projects/ai-service/app/routers/health.py
```

当前代码：

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

这个文件专门负责健康检查接口。

## 14. `from datetime import datetime, timezone`

代码：

```python
from datetime import datetime, timezone
```

意思是从 Python 标准库 `datetime` 里导入：

```text
datetime  用来获取时间
timezone  用来指定时区
```

当前用在：

```python
datetime.now(timezone.utc).isoformat()
```

也就是生成当前 UTC 时间字符串。

## 15. 为什么用 UTC 时间

当前代码：

```python
datetime.now(timezone.utc)
```

这里用的是 UTC 时间。

UTC 可以理解成全球统一的标准时间。

为什么服务端常用 UTC？

因为线上系统可能部署在不同地区：

```text
中国服务器
美国服务器
欧洲服务器
```

如果都用本地时间，排查日志会很混乱。

使用 UTC 能减少时区混乱。

初学阶段记住：

```text
服务端时间优先用 UTC，展示给用户时再转换成本地时间。
```

## 16. `from fastapi import APIRouter`

代码：

```python
from fastapi import APIRouter
```

导入 `APIRouter`。

`APIRouter` 用来创建接口分组。

你可以理解成：

```text
APIRouter = 一组相关接口的收纳盒。
```

当前：

```text
health router 只放健康检查接口。
```

以后：

```text
chat router 放聊天接口。
rag router 放知识库接口。
ticket router 放工单接口。
```

## 17. `router = APIRouter(tags=["health"])`

代码：

```python
router = APIRouter(tags=["health"])
```

它创建了一个 router 对象。

`tags=["health"]` 的作用是：

```text
在 /docs 接口文档里，把这个接口归到 health 分组。
```

如果你打开：

```text
http://127.0.0.1:8000/docs
```

会看到 `/health` 被放在 `health` 标签下面。

所以 `tags` 不是必须的业务逻辑，但它能让接口文档更清楚。

## 18. `@router.get("/health")`

代码：

```python
@router.get("/health")
```

这是路径操作装饰器。

先拆开：

```text
router  当前接口分组
get     HTTP GET 方法
/health URL 路径
```

整体意思是：

```text
如果有人向 /health 发 GET 请求，
就执行下面这个函数。
```

也就是绑定：

```text
GET /health -> health_check()
```

这不是注释。

它是 Python 装饰器，会在程序加载时把函数注册到 router 里。

## 19. `health_check()` 是什么

代码：

```python
def health_check() -> dict[str, object]:
```

这是一个普通 Python 函数。

名字叫：

```text
health_check
```

返回值类型提示：

```python
dict[str, object]
```

意思是：

```text
返回一个字典。
字典的 key 是字符串。
字典的 value 可以是不同类型的对象。
```

为什么 value 用 `object`？

因为返回值里有：

```python
"status": "ok"       # 字符串
"service": "ai-service"  # 字符串
"time": "..."        # 字符串
```

当前都是字符串，但以后健康检查可能返回：

```python
"dependencies": {"database": "ok"}
"uptime_seconds": 123
```

`object` 更宽泛。

## 20. `return {...}` 为什么会变成 JSON

代码：

```python
return {
    "status": "ok",
    "service": "ai-service",
    "time": datetime.now(timezone.utc).isoformat(),
}
```

这个函数返回的是 Python 字典。

但浏览器收到的是 JSON。

中间发生了转换：

```text
Python dict
        ↓
FastAPI 转成 JSON-compatible data
        ↓
JSONResponse
        ↓
HTTP 响应
        ↓
浏览器显示 JSON
```

所以你要记住：

```text
你在代码里 return dict。
客户端收到的是 JSON。
```

FastAPI 默认适合写 API，就是因为它很自然地处理 JSON 响应。

## 21. `datetime.now(timezone.utc).isoformat()`

代码：

```python
datetime.now(timezone.utc).isoformat()
```

拆开看：

```python
datetime.now(timezone.utc)
```

获取当前 UTC 时间。

```python
.isoformat()
```

把时间对象转换成 ISO 8601 格式字符串。

结果类似：

```text
2026-07-06T08:00:00.123456+00:00
```

这个格式适合接口返回。

原因是：

```text
它比 “2026年7月6日 下午4点” 这种文字更标准。
程序更容易解析。
跨语言更容易处理。
```

## 22. `/health` 完整执行链路

现在把所有东西串起来。

启动命令：

```powershell
uv run uvicorn app.main:app --reload
```

完整链路：

```text
1. Uvicorn 启动。
2. Uvicorn 根据 app.main:app 导入 app/main.py。
3. Python 执行 app/main.py。
4. 执行 app = create_app()。
5. create_app 里创建 FastAPI 应用对象。
6. create_app 里执行 app.include_router(health.router)。
7. health.router 里已经注册了 GET /health。
8. FastAPI 应用现在知道有一个 GET /health 接口。
9. 浏览器访问 http://127.0.0.1:8000/health。
10. Uvicorn 接收 HTTP 请求。
11. Uvicorn 把请求交给 FastAPI。
12. FastAPI 发现请求是 GET /health。
13. FastAPI 找到 health_check 函数。
14. FastAPI 调用 health_check。
15. health_check 返回 Python 字典。
16. FastAPI 把字典转换成 JSON 响应。
17. Uvicorn 把 HTTP 响应返回浏览器。
18. 浏览器显示 JSON。
```

这就是最小 FastAPI 服务的完整流程。

## 23. `/health` 为什么用 GET

`/health` 是查询服务状态。

它不会创建数据。

不会修改数据。

不会删除数据。

所以用：

```text
GET /health
```

这符合 HTTP 语义：

```text
GET 通常用于获取数据。
```

后面的 `/chat` 会用 POST。

因为聊天接口需要提交用户消息：

```json
{
  "message": "你好"
}
```

## 24. `/health` 测试在测什么

测试文件：

```text
projects/ai-service/tests/test_health.py
```

当前代码：

```python
from fastapi.testclient import TestClient

from app.main import create_app


def test_health_check() -> None:
    client = TestClient(create_app())

    response = client.get("/health")
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "ok"
    assert data["service"] == "ai-service"
    assert isinstance(data["time"], str)
```

逐行理解：

```python
client = TestClient(create_app())
```

创建一个测试客户端。

它可以不手动启动 Uvicorn，也能测试 FastAPI 应用。

```python
response = client.get("/health")
```

模拟发送：

```text
GET /health
```

```python
data = response.json()
```

把 JSON 响应解析成 Python 数据。

```python
assert response.status_code == 200
```

确认状态码是 200。

```python
assert data["status"] == "ok"
```

确认状态是 ok。

```python
assert data["service"] == "ai-service"
```

确认服务名正确。

```python
assert isinstance(data["time"], str)
```

确认 time 字段是字符串。

## 25. 为什么测试里不用真的启动服务

平时浏览器访问需要启动：

```powershell
uv run uvicorn app.main:app --reload
```

但测试里用的是：

```python
TestClient(create_app())
```

它可以直接在测试进程里调用 FastAPI 应用。

好处是：

```text
测试更快。
不需要手动开服务。
更适合自动化运行。
```

以后每加一个接口，都要配对应测试。

## 26. 如何运行本节代码

进入项目：

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

访问健康检查：

```text
http://127.0.0.1:8000/health
```

访问接口文档：

```text
http://127.0.0.1:8000/docs
```

访问 OpenAPI JSON：

```text
http://127.0.0.1:8000/openapi.json
```

## 27. 常见错误

### 错误 1：访问 `/health` 返回 404

常见原因：

```text
1. 没有写 @router.get("/health")。
2. 写了 router，但 main.py 里忘了 include_router。
3. 启动的不是当前项目。
4. 路径写错，比如访问了 /heath。
```

排查顺序：

```text
先看 health.py 有没有 router。
再看 main.py 有没有 include_router。
再看启动目录和启动命令。
```

### 错误 2：启动时报找不到 app

如果命令是：

```powershell
uv run uvicorn app.main:app --reload
```

你必须在：

```text
projects/ai-service
```

目录里运行。

如果你在仓库根目录运行，可能找不到 `app` 包。

### 错误 3：以为 `@router.get` 是注释

它不是注释。

它是装饰器。

它会把下面的函数注册为接口处理函数。

### 错误 4：以为返回的是 Python 字典

函数里返回的是 Python 字典。

客户端收到的是 JSON。

中间是 FastAPI 做了转换。

### 错误 5：以为 `/health` 能代表所有业务正常

当前 `/health` 只是浅层健康检查。

它只能证明服务能响应。

不能证明数据库、大模型、向量库都正常。

## 28. 本节必须掌握的最小知识

这一节最少要掌握：

```text
create_app() 用来创建 FastAPI 应用。
FastAPI() 创建应用对象。
app = create_app() 让 Uvicorn 能加载到应用对象。
APIRouter() 创建接口分组。
@router.get("/health") 把 GET /health 绑定到 health_check。
include_router() 把 router 注册到主应用。
health_check() 返回 Python 字典。
FastAPI 把 Python 字典转换成 JSON 响应。
/health 是浅层健康检查接口。
```

## 29. 本节练习

### 练习 1：解释启动命令

题目：

解释下面命令里 `app.main:app` 的含义：

```powershell
uv run uvicorn app.main:app --reload
```

### 练习 2：解释 `create_app()`

题目：

用自己的话解释：

```python
def create_app() -> FastAPI:
    ...
```

这个函数为什么存在？

### 练习 3：解释 `include_router`

题目：

用自己的话解释：

```python
app.include_router(health.router)
```

这行代码做了什么？如果删掉会怎么样？

### 练习 4：解释 `APIRouter`

题目：

用自己的话解释：

```python
router = APIRouter(tags=["health"])
```

这里创建了什么？`tags=["health"]` 有什么用？

### 练习 5：解释装饰器绑定

题目：

用自己的话解释：

```python
@router.get("/health")
def health_check() -> dict[str, object]:
    ...
```

为什么访问 `GET /health` 会执行 `health_check()`？

### 练习 6：解释 JSON 返回

题目：

为什么 `health_check()` 里返回的是 Python 字典，但浏览器看到的是 JSON？

### 练习 7：解释时间字段

题目：

解释下面代码做了什么：

```python
datetime.now(timezone.utc).isoformat()
```

### 练习 8：解释测试代码

题目：

下面测试主要检查了 `/health` 的哪些内容？

```python
assert response.status_code == 200
assert data["status"] == "ok"
assert data["service"] == "ai-service"
assert isinstance(data["time"], str)
```

## 30. 本节练习参考答案

### 练习 1 参考答案：解释启动命令

题目：

解释下面命令里 `app.main:app` 的含义：

```powershell
uv run uvicorn app.main:app --reload
```

参考答案：

`app.main:app` 分成两部分：

```text
app.main  表示 app/main.py 这个 Python 模块。
app       表示这个模块里的 FastAPI 应用对象变量。
```

Uvicorn 会导入 `app.main`，然后找到里面叫 `app` 的对象，把它作为 ASGI 应用运行。

### 练习 2 参考答案：解释 `create_app()`

题目：

用自己的话解释：

```python
def create_app() -> FastAPI:
    ...
```

这个函数为什么存在？

参考答案：

`create_app()` 用来集中创建 FastAPI 应用。

它现在负责：

```text
创建 FastAPI 对象。
注册 health router。
返回创建好的 app。
```

以后还可以继续加入：

```text
CORS
中间件
异常处理
日志
配置
```

所以它让应用创建流程更清楚，也方便测试。

### 练习 3 参考答案：解释 `include_router`

题目：

用自己的话解释：

```python
app.include_router(health.router)
```

这行代码做了什么？如果删掉会怎么样？

参考答案：

这行代码把 `health.router` 里定义的接口注册到主 FastAPI 应用里。

如果删掉，`health.py` 里虽然写了 `/health`，但主应用不知道这个接口。

结果可能是：

```text
访问 /health 返回 404 Not Found。
```

### 练习 4 参考答案：解释 `APIRouter`

题目：

用自己的话解释：

```python
router = APIRouter(tags=["health"])
```

这里创建了什么？`tags=["health"]` 有什么用？

参考答案：

这行代码创建了一个 `APIRouter` 对象。

它是接口分组，用来收纳健康检查相关接口。

`tags=["health"]` 用来在 `/docs` 自动文档里把这些接口归到 `health` 分组。

### 练习 5 参考答案：解释装饰器绑定

题目：

用自己的话解释：

```python
@router.get("/health")
def health_check() -> dict[str, object]:
    ...
```

为什么访问 `GET /health` 会执行 `health_check()`？

参考答案：

`@router.get("/health")` 是路径操作装饰器。

它会告诉 FastAPI：

```text
当收到 GET /health 请求时，调用下面的 health_check 函数。
```

所以访问 `GET /health` 会执行 `health_check()`。

### 练习 6 参考答案：解释 JSON 返回

题目：

为什么 `health_check()` 里返回的是 Python 字典，但浏览器看到的是 JSON？

参考答案：

因为 FastAPI 会把接口函数返回的 Python 字典转换成 JSON-compatible 数据，再放进 JSON 响应里返回给客户端。

所以：

```text
代码里 return dict。
客户端收到 JSON。
```

### 练习 7 参考答案：解释时间字段

题目：

解释下面代码做了什么：

```python
datetime.now(timezone.utc).isoformat()
```

参考答案：

```python
datetime.now(timezone.utc)
```

获取当前 UTC 时间。

```python
.isoformat()
```

把时间对象转换成标准字符串。

最终结果类似：

```text
2026-07-06T08:00:00.123456+00:00
```

### 练习 8 参考答案：解释测试代码

题目：

下面测试主要检查了 `/health` 的哪些内容？

```python
assert response.status_code == 200
assert data["status"] == "ok"
assert data["service"] == "ai-service"
assert isinstance(data["time"], str)
```

参考答案：

它检查了四件事：

```text
状态码是 200，说明请求成功。
status 字段是 ok，说明服务声明自己正常。
service 字段是 ai-service，说明服务名正确。
time 字段是字符串，说明返回了时间信息。
```

## 31. 自测问题

1. `/health` 接口的作用是什么？
2. 当前 `/health` 是浅层健康检查还是深层健康检查？
3. `app/main.py` 负责什么？
4. `create_app()` 返回什么？
5. `FastAPI(title=..., description=..., version=...)` 里的这些信息会出现在哪里？
6. `app = create_app()` 为什么重要？
7. `APIRouter()` 的作用是什么？
8. `include_router()` 的作用是什么？
9. `@router.get("/health")` 是注释吗？
10. `health_check()` 返回的 Python 字典为什么会变成 JSON？
11. 为什么服务端时间建议用 UTC？
12. `TestClient(create_app())` 有什么用？
13. 如果访问 `/health` 返回 404，优先检查哪些地方？

## 32. 自测参考答案

### 自测 1 参考答案

题目：

`/health` 接口的作用是什么？

答案：

`/health` 是健康检查接口，用来让浏览器、监控系统、测试程序或其他服务快速判断当前服务是否还能正常响应。

### 自测 2 参考答案

题目：

当前 `/health` 是浅层健康检查还是深层健康检查？

答案：

当前 `/health` 是浅层健康检查。

它只说明 FastAPI 服务能接收请求并返回响应，不代表数据库、大模型、向量库等依赖都正常。

### 自测 3 参考答案

题目：

`app/main.py` 负责什么？

答案：

`app/main.py` 是应用入口，负责创建 FastAPI 应用对象，并把 router 注册到主应用里。

以后它还会负责注册中间件、异常处理、CORS、日志等应用级能力。

### 自测 4 参考答案

题目：

`create_app()` 返回什么？

答案：

`create_app()` 返回一个创建好并注册好 router 的 FastAPI 应用对象。

### 自测 5 参考答案

题目：

`FastAPI(title=..., description=..., version=...)` 里的这些信息会出现在哪里？

答案：

这些信息会出现在 FastAPI 自动生成的接口文档和 OpenAPI schema 里，例如：

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/openapi.json
```

### 自测 6 参考答案

题目：

`app = create_app()` 为什么重要？

答案：

这行代码真正创建了 FastAPI 应用对象，并把它赋值给模块级变量 `app`。

启动命令 `uvicorn app.main:app` 需要找到这个变量。

### 自测 7 参考答案

题目：

`APIRouter()` 的作用是什么？

答案：

`APIRouter()` 用来创建接口分组，把相关接口放在一起，方便拆分文件和组织项目结构。

### 自测 8 参考答案

题目：

`include_router()` 的作用是什么？

答案：

`include_router()` 用来把某个 router 里的接口注册到主 FastAPI 应用里。

### 自测 9 参考答案

题目：

`@router.get("/health")` 是注释吗？

答案：

不是。

它是 Python 装饰器，会把下面的函数注册为 `GET /health` 的处理函数。

### 自测 10 参考答案

题目：

`health_check()` 返回的 Python 字典为什么会变成 JSON？

答案：

FastAPI 默认会把接口函数返回的 Python 数据转换成 JSON 响应。

所以 Python 代码里返回字典，客户端收到的是 JSON。

### 自测 11 参考答案

题目：

为什么服务端时间建议用 UTC？

答案：

UTC 是统一标准时间。

服务可能部署在不同地区，用 UTC 可以减少时区混乱，方便日志排查和跨系统对齐。

### 自测 12 参考答案

题目：

`TestClient(create_app())` 有什么用？

答案：

它创建一个测试客户端，可以在 pytest 里直接调用 FastAPI 应用，不需要手动启动 Uvicorn 服务。

### 自测 13 参考答案

题目：

如果访问 `/health` 返回 404，优先检查哪些地方？

答案：

优先检查：

```text
health.py 里是否有 @router.get("/health")。
main.py 里是否有 app.include_router(health.router)。
启动命令是否在 projects/ai-service 目录运行。
访问路径是否拼写正确。
```

## 33. 本节小结

这一节的核心不是记住每一行代码，而是看懂完整链路：

```text
启动 Uvicorn
        ↓
加载 app.main:app
        ↓
执行 create_app()
        ↓
创建 FastAPI 应用
        ↓
include_router 注册 health router
        ↓
@router.get("/health") 绑定函数
        ↓
GET /health 触发 health_check()
        ↓
return dict
        ↓
FastAPI 转成 JSON 响应
```

这是所有 FastAPI 接口的基本模型。

后面 `/chat`、`/stream-chat`、`/rag/query` 都是在这个模型上继续扩展。

下一节学习：

```text
router 路由拆分
```

下一节会专门讲：

```text
为什么要有 app/routers/
一个 router 里面应该写什么
main.py 和 router 文件如何配合
prefix、tags、include_router 是什么
```

## 34. 参考资料

- [FastAPI First Steps](https://fastapi.tiangolo.com/tutorial/first-steps/)
- [FastAPI Bigger Applications - Multiple Files](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [FastAPI Custom Response](https://fastapi.tiangolo.com/advanced/custom-response/)
- [FastAPI APIRouter Reference](https://fastapi.tiangolo.com/reference/apirouter/)
