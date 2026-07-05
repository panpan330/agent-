# FastAPI 阶段 1：项目结构和最小服务

日期：2026-07-05

对应代码：

```text
projects/ai-service/
```

## 1. 本节学什么

从这一节开始，我们从 Python 基础进入 Python AI 服务工程。

本节先做三件事：

1. 创建 `projects/ai-service` 项目。
2. 安装 FastAPI 和 Uvicorn。
3. 实现第一个接口 `/health`。

目标不是马上接大模型，而是先把服务骨架搭稳。

## 2. Web 服务是什么

Web 服务可以先理解成：

```text
一个长期运行的程序，等待别人通过 HTTP 请求来调用它。
```

例如：

```text
GET /health
```

服务收到请求后，执行对应 Python 函数，再返回 JSON 响应。

## 3. FastAPI 是什么

FastAPI 是一个 Python Web API 框架。

它帮我们做这些事：

- 把 URL 映射到 Python 函数。
- 接收 JSON 请求。
- 返回 JSON 响应。
- 自动校验请求数据。
- 自动生成接口文档。
- 支持异步接口。

后面 AI 服务的 `/chat`、`/stream-chat`、`/rag/query` 都会用 FastAPI 写。

## 4. Uvicorn 是什么

FastAPI 只负责定义应用和接口。

真正把服务跑起来，需要一个 ASGI 服务器。

本项目使用：

```text
uvicorn
```

运行命令：

```powershell
uv run uvicorn app.main:app --reload
```

其中：

- `app.main` 表示 `app/main.py` 这个模块。
- `app` 表示模块里的 FastAPI 应用对象。
- `--reload` 表示代码变化后自动重启，适合开发阶段。

## 5. 为什么单独创建 ai-service

之前的 `projects/python-basics` 是语法学习项目。

现在的 `projects/ai-service` 是 AI 服务项目。

分开是为了让职责清楚：

```text
python-basics = 学基础
ai-service = 做真实服务
```

真实项目里不要把练习脚本和服务代码混在一起。

## 6. 当前目录结构

```text
projects/ai-service/
  app/
    __init__.py
    main.py
    routers/
      __init__.py
      health.py
  tests/
    test_health.py
  pyproject.toml
  README.md
  uv.lock
```

现在结构还很小，但已经不是单文件项目。

## 7. app/main.py

```python
from fastapi import FastAPI

from app.routers import health


def create_app() -> FastAPI:
    app = FastAPI(...)
    app.include_router(health.router)
    return app


app = create_app()
```

这里有两个重点：

- `create_app()` 用来创建 FastAPI 应用。
- `app = create_app()` 是 Uvicorn 要加载的对象。

## 8. router 是什么

router 是路由模块。

简单理解：

```text
router = 一组相关接口
```

当前：

```text
app/routers/health.py
```

专门放健康检查接口。

后面会加：

```text
app/routers/chat.py
```

专门放聊天接口。

这样就不会把所有接口都堆在 `main.py`。

## 9. /health 接口

```python
@router.get("/health")
def health_check() -> dict[str, object]:
    return {
        "status": "ok",
        "service": "ai-service",
        "time": datetime.now(timezone.utc).isoformat(),
    }
```

含义：

```text
当客户端 GET /health 时，执行 health_check 函数。
```

函数返回字典，FastAPI 会自动转成 JSON。

## 10. Swagger UI

FastAPI 会自动生成接口文档。

启动服务后访问：

```text
http://127.0.0.1:8000/docs
```

你会看到 Swagger UI，可以直接在浏览器里测试接口。

## 11. TestClient

测试文件：

```text
tests/test_health.py
```

使用：

```python
from fastapi.testclient import TestClient
```

测试：

```python
def test_health_check() -> None:
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
```

它不用真的启动一个外部服务，也可以测试 API。

## 12. 本节命令

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

访问接口：

```text
http://127.0.0.1:8000/health
```

访问文档：

```text
http://127.0.0.1:8000/docs
```

## 13. 常见错误

### 错误 1：运行目录不对

如果在仓库根目录直接运行：

```powershell
uv run uvicorn app.main:app --reload
```

可能找不到 `app`。

当前应该在：

```text
projects/ai-service
```

里运行。

### 错误 2：把所有接口都写在 main.py

小 demo 可以。

真实项目不建议。

我们从一开始就拆 `routers/`，是为了养成工程习惯。

### 错误 3：不知道 app.main:app 是什么

```text
app.main:app
```

左边 `app.main` 是模块路径。

右边 `app` 是模块里的 FastAPI 对象。

## 14. 本节练习

1. 运行测试：

   ```powershell
   uv run pytest -q
   ```

2. 启动服务：

   ```powershell
   uv run uvicorn app.main:app --reload
   ```

3. 打开：

   ```text
   http://127.0.0.1:8000/health
   ```

4. 打开：

   ```text
   http://127.0.0.1:8000/docs
   ```

5. 试着解释：

   ```text
   为什么访问 /health 会执行 health_check 函数？
   ```

## 15. 本节练习参考答案

1. 运行测试的参考结果：

   ```text
   1 passed
   ```

   只要看到 `passed`，就说明 `/health` 接口测试通过。

2. 启动服务后，终端里应该能看到类似含义的信息：

   ```text
   Uvicorn running on http://127.0.0.1:8000
   ```

   这表示 FastAPI 服务已经由 Uvicorn 跑起来了。

3. 打开 `/health` 后，应该看到类似 JSON：

   ```json
   {
     "status": "ok",
     "service": "ai-service",
     "time": "2026-07-05T09:00:00+00:00"
   }
   ```

   `time` 每次访问都会不同，这是正常的。

4. 打开 `/docs` 后，应该看到 FastAPI 自动生成的接口文档页面，里面有 `GET /health`。

5. 访问 `/health` 会执行 `health_check` 函数，是因为代码里写了：

   ```python
   @router.get("/health")
   def health_check() -> dict[str, object]:
       ...
   ```

   `@router.get("/health")` 把 HTTP 的 `GET /health` 请求绑定到了下面的 `health_check` 函数。

## 16. 自测问题

1. FastAPI 是什么？
2. Uvicorn 是什么？
3. `app.main:app` 表示什么？
4. `/health` 接口有什么用？
5. 为什么要拆 `routers/`？
6. FastAPI 为什么能返回 JSON？
7. `/docs` 是什么？
8. TestClient 有什么用？

## 17. 自测参考答案

1. FastAPI 是什么？

   FastAPI 是 Python Web API 框架，用来写 HTTP API 服务。

2. Uvicorn 是什么？

   Uvicorn 是 ASGI 服务器，用来运行 FastAPI 应用。

3. `app.main:app` 表示什么？

   `app.main` 表示 `app/main.py` 模块，后面的 `app` 表示这个模块里的 FastAPI 应用对象。

4. `/health` 接口有什么用？

   它用来检查服务是否正常运行。

5. 为什么要拆 `routers/`？

   为了把不同接口按模块组织，避免所有接口都堆在 `main.py`。

6. FastAPI 为什么能返回 JSON？

   因为 FastAPI 会把 Python 字典自动转换成 JSON 响应。

7. `/docs` 是什么？

   `/docs` 是 FastAPI 自动生成的 Swagger UI 接口文档页面。

8. TestClient 有什么用？

   TestClient 可以在 pytest 里测试 FastAPI 接口，不需要手动启动外部服务。
