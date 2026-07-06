# FastAPI 阶段 1 第 3 节：创建 ai-service 项目骨架

日期：2026-07-06

本节目标：看懂 `projects/ai-service` 这个 FastAPI 项目的基础目录结构。

这一节不是单纯背目录名，而是要弄明白：

```text
每个文件为什么存在？
它负责什么？
以后代码变多时应该放在哪里？
哪些东西应该提交到 GitHub？
哪些东西不应该提交？
```

项目骨架是后续所有功能的地基。

如果一开始结构乱，后面加 `/chat`、`.env`、日志、trace_id、RAG、LangChain 时会越来越难维护。

## 1. 本节学什么

本节学习这些内容：

1. 为什么要单独创建 `projects/ai-service`。
2. `projects/ai-service` 当前目录结构。
3. `.python-version` 是什么。
4. `pyproject.toml` 是什么。
5. `uv.lock` 是什么。
6. `.venv` 是什么，为什么不提交 GitHub。
7. `README.md` 是什么。
8. `app/` 是什么。
9. `app/main.py` 是什么。
10. `routers/` 是什么。
11. `tests/` 是什么。
12. `__init__.py` 是什么。
13. 为什么不要把所有代码都写进 `main.py`。
14. 一个 FastAPI 项目后续会怎么长大。

先记住一句话：

```text
项目骨架 = 代码、配置、依赖、测试、文档的摆放规则。
```

## 2. 为什么要单独创建 ai-service

之前我们有：

```text
projects/python-basics
```

它的作用是：

```text
学习 Python 基础语法和小练习。
```

现在我们有：

```text
projects/ai-service
```

它的作用是：

```text
开发一个真正可以长期扩展的 Python AI 服务。
```

这两个项目不能混在一起。

原因很简单：

```text
python-basics 是练语法。
ai-service 是做服务。
```

语法练习文件通常是：

```text
01_variables_types.py
02_strings.py
03_lists.py
```

这些文件适合逐个运行、逐个观察。

FastAPI 服务项目则是：

```text
启动一个 Web 服务
接收 HTTP 请求
按接口组织代码
有统一依赖
有测试
有文档
以后还要接大模型和 RAG
```

所以必须单独成项目。

## 3. 当前 ai-service 目录结构

当前项目结构是：

```text
projects/ai-service/
  .python-version
  pyproject.toml
  uv.lock
  README.md
  app/
    __init__.py
    main.py
    routers/
      __init__.py
      health.py
  tests/
    conftest.py
    test_health.py
```

先不要怕文件多。

你可以先按 4 类理解：

```text
项目配置：.python-version、pyproject.toml、uv.lock
项目说明：README.md
服务代码：app/
测试代码：tests/
```

也就是：

```text
ai-service/
  配置文件
  说明文档
  真正服务代码
  自动化测试
```

## 4. `.python-version` 是什么

文件：

```text
projects/ai-service/.python-version
```

它记录这个项目希望使用的 Python 版本。

比如里面可能是：

```text
3.12
```

它的作用是告诉 uv：

```text
这个项目默认用哪个 Python 版本。
```

你可以理解成：

```text
.python-version = 项目的 Python 版本提示牌。
```

为什么需要它？

因为不同项目可能使用不同 Python 版本：

```text
项目 A 用 Python 3.10
项目 B 用 Python 3.12
项目 C 用 Python 3.13
```

没有版本约束时，很容易出现：

```text
你这里能跑，换台电脑跑不了。
```

`.python-version` 能帮助 uv 选择合适的解释器。

## 5. `pyproject.toml` 是什么

文件：

```text
projects/ai-service/pyproject.toml
```

这是现代 Python 项目的核心配置文件。

当前内容大概是：

```toml
[project]
name = "ai-service"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.139.0",
    "uvicorn>=0.50.0",
]

[dependency-groups]
dev = [
    "httpx2>=2.5.0",
    "pytest>=9.1.1",
]
```

不要急着全背。

先按区域理解。

### 5.1 `[project]`

这一段是项目基本信息。

```toml
[project]
name = "ai-service"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.12"
```

含义：

| 字段 | 含义 |
| --- | --- |
| `name` | 项目名 |
| `version` | 项目版本 |
| `description` | 项目描述 |
| `readme` | 项目说明文档 |
| `requires-python` | 要求的 Python 版本 |

这里的：

```toml
requires-python = ">=3.12"
```

意思是：

```text
这个项目需要 Python 3.12 或更高版本。
```

### 5.2 `dependencies`

这一段是正式运行依赖：

```toml
dependencies = [
    "fastapi>=0.139.0",
    "uvicorn>=0.50.0",
]
```

它表示：

```text
项目正常运行必须安装 FastAPI 和 Uvicorn。
```

为什么 FastAPI 和 Uvicorn 是正式依赖？

因为没有它们，服务就跑不起来。

### 5.3 `[dependency-groups]`

这一段是依赖分组：

```toml
[dependency-groups]
dev = [
    "httpx2>=2.5.0",
    "pytest>=9.1.1",
]
```

这里的 `dev` 表示开发依赖。

开发依赖通常是：

```text
开发、测试、检查代码时需要，
但服务正式运行时不一定需要。
```

当前：

```text
pytest  用来运行测试。
httpx2  当前 FastAPI TestClient 需要的 HTTP 测试客户端相关依赖。
```

## 6. 正式依赖和开发依赖有什么区别

你可以这样理解：

```text
正式依赖 = 服务运行必须要有。
开发依赖 = 开发和测试时才需要。
```

举例：

| 依赖 | 类型 | 原因 |
| --- | --- | --- |
| `fastapi` | 正式依赖 | 服务代码直接依赖它 |
| `uvicorn` | 正式依赖 | 需要它启动服务 |
| `pytest` | 开发依赖 | 只在跑测试时用 |
| `httpx2` | 开发依赖 | 当前测试客户端需要 |

类比 Java：

```text
正式依赖类似 implementation。
开发/测试依赖类似 testImplementation。
```

这个类比不是完全等价，但有助于理解。

## 7. `uv.lock` 是什么

文件：

```text
projects/ai-service/uv.lock
```

它是 uv 生成的锁文件。

锁文件的作用是：

```text
记录当前项目解析出来的精确依赖版本。
```

`pyproject.toml` 里写的是范围：

```toml
fastapi>=0.139.0
```

这表示：

```text
FastAPI 版本大于等于 0.139.0 都可以。
```

但真正安装时，uv 会解析出一个具体版本，比如：

```text
fastapi 0.139.0
starlette 1.3.1
pydantic 2.13.4
```

这些精确结果会写进 `uv.lock`。

你可以这样理解：

```text
pyproject.toml = 我想要哪些依赖，允许什么版本范围。
uv.lock = 这次实际锁定了哪些精确版本。
```

为什么要提交 `uv.lock`？

因为这样别人拉代码后，可以安装和你一致的依赖版本。

这能减少：

```text
我电脑能跑，你电脑不能跑。
```

这类问题。

## 8. `uv sync` 和 `uv run` 的区别

常用命令：

```powershell
uv sync
uv run pytest -q
uv run uvicorn app.main:app --reload
```

### 8.1 `uv sync`

`uv sync` 的作用是：

```text
根据 pyproject.toml 和 uv.lock，把项目虚拟环境同步好。
```

也就是安装项目需要的依赖。

### 8.2 `uv run`

`uv run` 的作用是：

```text
在这个项目的虚拟环境里运行命令。
```

比如：

```powershell
uv run pytest -q
```

意思是：

```text
用当前项目环境里的 pytest 运行测试。
```

再比如：

```powershell
uv run uvicorn app.main:app --reload
```

意思是：

```text
用当前项目环境里的 uvicorn 启动 FastAPI 服务。
```

## 9. `.venv` 是什么

目录：

```text
projects/ai-service/.venv/
```

它是项目虚拟环境。

虚拟环境里放的是：

```text
Python 解释器
已安装依赖包
命令行工具
```

为什么需要虚拟环境？

因为不同项目依赖可能不同。

例如：

```text
项目 A 需要 fastapi 0.100
项目 B 需要 fastapi 0.139
```

如果都装到系统 Python 里，很容易互相影响。

虚拟环境能隔离每个项目的依赖。

### 9.1 为什么 `.venv` 不提交 GitHub

`.venv` 里文件很多，而且和你电脑环境有关。

它不应该提交 GitHub。

正确做法是：

```text
提交 pyproject.toml 和 uv.lock。
别人拉代码后运行 uv sync，重新生成自己的 .venv。
```

所以：

```text
pyproject.toml 要提交。
uv.lock 要提交。
.venv 不提交。
```

## 10. `README.md` 是什么

文件：

```text
projects/ai-service/README.md
```

README 是项目说明书。

它应该告诉别人：

```text
这个项目是什么。
怎么安装依赖。
怎么启动。
怎么测试。
有哪些接口。
```

当前 README 里有：

```powershell
uv sync
uv run uvicorn app.main:app --reload
uv run pytest -q
```

这很重要。

因为以后你把项目给别人看，对方不应该靠猜。

一个项目必须能让别人快速知道：

```text
我怎么把它跑起来？
```

## 11. `app/` 是什么

目录：

```text
projects/ai-service/app/
```

它放真正的服务代码。

当前里面有：

```text
app/
  __init__.py
  main.py
  routers/
```

你可以把 `app/` 理解成：

```text
FastAPI 应用源码目录。
```

以后会继续增加：

```text
app/
  core/        配置、日志、异常处理
  schemas/     Pydantic 请求/响应模型
  services/    业务逻辑和 AI 调用
  routers/     接口路由
```

现阶段先保持简单。

## 12. `app/main.py` 是什么

文件：

```text
projects/ai-service/app/main.py
```

它是 FastAPI 应用入口。

当前核心代码：

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

`main.py` 主要负责：

```text
创建 FastAPI 应用对象。
注册 router。
以后注册中间件、异常处理、CORS、启动事件等。
```

它不应该负责：

```text
写所有业务逻辑。
写所有接口函数。
写所有模型调用。
写所有数据库逻辑。
```

`main.py` 应该是总入口，不是垃圾桶。

## 13. `routers/` 是什么

目录：

```text
projects/ai-service/app/routers/
```

它放接口分组。

当前：

```text
routers/
  __init__.py
  health.py
```

`health.py` 放健康检查接口：

```python
@router.get("/health")
def health_check() -> dict[str, object]:
    ...
```

后面会增加：

```text
routers/
  health.py
  chat.py
  rag.py
  tickets.py
```

每个文件负责一类接口：

| 文件 | 职责 |
| --- | --- |
| `health.py` | 健康检查 |
| `chat.py` | 聊天接口 |
| `rag.py` | 知识库问答 |
| `tickets.py` | 工单相关接口 |

这样比所有接口都塞进 `main.py` 清楚很多。

## 14. `tests/` 是什么

目录：

```text
projects/ai-service/tests/
```

它放自动化测试。

当前：

```text
tests/
  conftest.py
  test_health.py
```

`test_health.py` 测试 `/health` 接口：

```python
def test_health_check() -> None:
    client = TestClient(create_app())

    response = client.get("/health")
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "ok"
    assert data["service"] == "ai-service"
    assert isinstance(data["time"], str)
```

测试的意义是：

```text
以后你改代码时，可以快速确认旧功能有没有坏。
```

不要把测试当作额外负担。

对后端项目来说，测试是防止越改越乱的重要工具。

## 15. `conftest.py` 是什么

文件：

```text
projects/ai-service/tests/conftest.py
```

当前它主要做一件事：

```text
让测试能找到 app 这个包。
```

当前内容：

```python
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
```

意思是：

```text
把 projects/ai-service 加入 Python 导入路径。
```

这样测试里才能写：

```python
from app.main import create_app
```

后面我们会逐步优化项目结构，现在先知道它的作用即可。

## 16. `__init__.py` 是什么

当前有：

```text
app/__init__.py
app/routers/__init__.py
```

它们目前内容可能是空的。

那为什么还要有？

因为 `__init__.py` 可以告诉 Python：

```text
这个目录可以被当作一个包来导入。
```

例如：

```python
from app.routers import health
```

这里的 `app` 和 `routers` 都是包路径的一部分。

现代 Python 在某些场景下没有 `__init__.py` 也能工作，但初学阶段建议保留。

原因是：

```text
更明确。
更传统。
更容易理解导入路径。
更少遇到奇怪的工具兼容问题。
```

## 17. 为什么不要把所有代码都放 main.py

小 demo 可以这样：

```text
main.py
  所有接口
  所有模型
  所有配置
  所有业务逻辑
```

但真实项目不建议。

因为代码会很快变成：

```text
main.py 1000 行
找一个接口要翻半天
改一个功能影响一大片
测试也不好写
新人看不懂
```

正确方向是按职责拆分：

```text
main.py       应用入口
routers/      接口层
schemas/      请求/响应模型
services/     业务逻辑
core/         配置、日志、异常处理
tests/        测试
```

这就是工程化。

工程化不是写得复杂。

工程化是：

```text
让项目变大以后仍然能看懂、能修改、能测试。
```

## 18. 当前结构和后续结构对比

当前结构：

```text
app/
  main.py
  routers/
    health.py
tests/
  test_health.py
```

后续可能变成：

```text
app/
  main.py
  core/
    config.py
    logging.py
    exceptions.py
  routers/
    health.py
    chat.py
    rag.py
  schemas/
    chat.py
    rag.py
  services/
    chat_service.py
    rag_service.py
    llm_client.py
  middleware/
    trace.py
tests/
  test_health.py
  test_chat.py
  test_config.py
  test_errors.py
```

不要现在就全建出来。

原因是：

```text
现在功能还少，提前建太多空目录反而增加理解负担。
```

我们采用渐进方式：

```text
需要什么，再加什么。
每加一个目录，都讲清楚为什么加。
```

## 19. 哪些文件应该提交 GitHub

应该提交：

```text
.python-version
pyproject.toml
uv.lock
README.md
app/
tests/
```

原因：

```text
它们是项目源码、配置、依赖描述、锁定版本、测试和说明。
```

不应该提交：

```text
.venv/
__pycache__/
.pytest_cache/
*.log
```

原因：

```text
它们是本地生成物、缓存、日志，和你电脑环境有关。
```

当前仓库已经通过 `.gitignore` 忽略这些文件。

## 20. 从 0 创建项目时的命令

这次项目已经创建好了。

但你要知道从 0 怎么来。

大致流程是：

```powershell
cd D:\wendang\java+python+ai
uv init projects\ai-service --app --name ai-service
cd projects\ai-service
uv add fastapi uvicorn
uv add --dev pytest httpx2
```

然后创建：

```text
app/
tests/
```

再把默认的单文件 demo 改成当前这种工程结构。

注意：

```text
命令不是重点，理解每一步为什么做才是重点。
```

## 21. 当前项目怎么运行

进入项目：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
```

同步依赖：

```powershell
uv sync
```

启动服务：

```powershell
uv run uvicorn app.main:app --reload
```

访问：

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
```

运行测试：

```powershell
uv run pytest -q
```

## 22. 本节必须掌握的最小知识

这一节最少要掌握：

```text
pyproject.toml：项目配置和依赖声明。
uv.lock：锁定精确依赖版本。
.python-version：项目默认 Python 版本。
.venv：本地虚拟环境，不提交。
README.md：项目说明书。
app/：服务源码。
app/main.py：FastAPI 应用入口。
routers/：接口分组。
tests/：自动化测试。
__init__.py：让目录更明确地作为 Python 包。
```

## 23. 本节练习

### 练习 1：识别文件职责

题目：

把下面文件和它们的职责对应起来：

```text
pyproject.toml
uv.lock
.python-version
README.md
app/main.py
app/routers/health.py
tests/test_health.py
```

### 练习 2：判断是否应该提交 GitHub

题目：

判断下面这些内容是否应该提交 GitHub，并说明原因：

```text
pyproject.toml
uv.lock
.venv/
__pycache__/
app/main.py
tests/test_health.py
uvicorn-8000.out.log
```

### 练习 3：解释 pyproject.toml 和 uv.lock 的区别

题目：

用自己的话解释：

```text
pyproject.toml 和 uv.lock 有什么区别？
```

### 练习 4：解释为什么要有 routers

题目：

用自己的话解释：

```text
为什么不要把所有接口都写在 app/main.py？
为什么要拆到 app/routers/？
```

### 练习 5：解释 __init__.py

题目：

用自己的话解释：

```text
__init__.py 有什么作用？
为什么 app/ 和 app/routers/ 里都有它？
```

### 练习 6：画出当前项目结构

题目：

不看笔记，自己写出当前 `projects/ai-service` 的主要目录结构。

至少写出：

```text
pyproject.toml
uv.lock
app/main.py
app/routers/health.py
tests/test_health.py
```

## 24. 本节练习参考答案

### 练习 1 参考答案：识别文件职责

题目：

把下面文件和它们的职责对应起来：

```text
pyproject.toml
uv.lock
.python-version
README.md
app/main.py
app/routers/health.py
tests/test_health.py
```

参考答案：

| 文件 | 职责 |
| --- | --- |
| `pyproject.toml` | 记录项目元数据、Python 版本要求、依赖声明 |
| `uv.lock` | 锁定依赖解析后的精确版本 |
| `.python-version` | 指定项目默认 Python 版本 |
| `README.md` | 说明项目是什么、怎么运行、怎么测试 |
| `app/main.py` | FastAPI 应用入口，创建 app 并注册路由 |
| `app/routers/health.py` | 健康检查接口 |
| `tests/test_health.py` | `/health` 接口测试 |

### 练习 2 参考答案：判断是否应该提交 GitHub

题目：

判断下面这些内容是否应该提交 GitHub，并说明原因：

```text
pyproject.toml
uv.lock
.venv/
__pycache__/
app/main.py
tests/test_health.py
uvicorn-8000.out.log
```

参考答案：

| 内容 | 是否提交 | 原因 |
| --- | --- | --- |
| `pyproject.toml` | 是 | 项目配置和依赖声明 |
| `uv.lock` | 是 | 锁定依赖版本，保证环境可复现 |
| `.venv/` | 否 | 本地虚拟环境，文件多且和机器有关 |
| `__pycache__/` | 否 | Python 运行缓存 |
| `app/main.py` | 是 | 服务源码 |
| `tests/test_health.py` | 是 | 自动化测试源码 |
| `uvicorn-8000.out.log` | 否 | 本地运行日志 |

### 练习 3 参考答案：解释 pyproject.toml 和 uv.lock 的区别

题目：

用自己的话解释：

```text
pyproject.toml 和 uv.lock 有什么区别？
```

参考答案：

`pyproject.toml` 是项目配置文件，里面写项目名称、版本、Python 要求和依赖范围。

`uv.lock` 是锁文件，里面记录 uv 实际解析出来的精确依赖版本。

简单说：

```text
pyproject.toml = 你声明想要什么。
uv.lock = uv 实际锁定了什么。
```

### 练习 4 参考答案：解释为什么要有 routers

题目：

用自己的话解释：

```text
为什么不要把所有接口都写在 app/main.py？
为什么要拆到 app/routers/？
```

参考答案：

如果所有接口都写在 `app/main.py`，项目小的时候还能看，项目大了以后会变得很乱。

例如以后会有：

```text
/health
/chat
/stream-chat
/rag/query
/tickets/extract
```

如果全放在一个文件里，查找、修改、测试都会变难。

拆到 `app/routers/` 后，可以按功能分组：

```text
health.py  放健康检查
chat.py    放聊天接口
rag.py     放知识库接口
```

这样职责更清楚。

### 练习 5 参考答案：解释 __init__.py

题目：

用自己的话解释：

```text
__init__.py 有什么作用？
为什么 app/ 和 app/routers/ 里都有它？
```

参考答案：

`__init__.py` 可以让 Python 更明确地把目录当作包来导入。

有了它，可以更清楚地使用包路径：

```python
from app.routers import health
```

`app/` 是一个包，`app/routers/` 也是它下面的子包。

所以这两个目录里都有 `__init__.py`。

### 练习 6 参考答案：画出当前项目结构

题目：

不看笔记，自己写出当前 `projects/ai-service` 的主要目录结构。

至少写出：

```text
pyproject.toml
uv.lock
app/main.py
app/routers/health.py
tests/test_health.py
```

参考答案：

```text
projects/ai-service/
  .python-version
  pyproject.toml
  uv.lock
  README.md
  app/
    __init__.py
    main.py
    routers/
      __init__.py
      health.py
  tests/
    conftest.py
    test_health.py
```

## 25. 自测问题

1. 为什么要把 `ai-service` 和 `python-basics` 分开？
2. `pyproject.toml` 是什么？
3. `uv.lock` 是什么？
4. `.python-version` 是什么？
5. `.venv` 是什么，为什么不提交 GitHub？
6. `README.md` 应该写什么？
7. `app/` 目录放什么？
8. `app/main.py` 负责什么？
9. `routers/` 目录放什么？
10. `tests/` 目录放什么？
11. `conftest.py` 当前有什么作用？
12. `__init__.py` 是什么？
13. 为什么不要把所有代码都放进 `main.py`？

## 26. 自测参考答案

### 自测 1 参考答案

题目：

为什么要把 `ai-service` 和 `python-basics` 分开？

答案：

因为 `python-basics` 是语法练习项目，`ai-service` 是真正的 FastAPI 服务项目。

二者职责不同。分开后，练习代码不会污染服务代码，服务项目也更容易扩展、测试和展示。

### 自测 2 参考答案

题目：

`pyproject.toml` 是什么？

答案：

`pyproject.toml` 是现代 Python 项目的核心配置文件，用来记录项目元数据、Python 版本要求、正式依赖、开发依赖等信息。

### 自测 3 参考答案

题目：

`uv.lock` 是什么？

答案：

`uv.lock` 是 uv 生成的锁文件，用来记录项目依赖解析后的精确版本，保证不同机器安装出尽量一致的依赖环境。

### 自测 4 参考答案

题目：

`.python-version` 是什么？

答案：

`.python-version` 记录项目默认使用的 Python 版本，帮助 uv 选择合适的 Python 解释器。

### 自测 5 参考答案

题目：

`.venv` 是什么，为什么不提交 GitHub？

答案：

`.venv` 是项目虚拟环境，里面包含 Python 解释器和安装好的依赖包。

它和本机环境有关，文件也很多，所以不提交 GitHub。应该提交 `pyproject.toml` 和 `uv.lock`，让别人运行 `uv sync` 生成自己的 `.venv`。

### 自测 6 参考答案

题目：

`README.md` 应该写什么？

答案：

`README.md` 应该说明项目是什么、如何安装依赖、如何启动服务、如何运行测试、当前有哪些接口。

### 自测 7 参考答案

题目：

`app/` 目录放什么？

答案：

`app/` 放 FastAPI 服务源码，比如应用入口、router、配置、服务逻辑、数据模型等。

### 自测 8 参考答案

题目：

`app/main.py` 负责什么？

答案：

`app/main.py` 是 FastAPI 应用入口，负责创建 `FastAPI` 应用对象、注册路由，后面还会注册中间件、异常处理、CORS 等。

### 自测 9 参考答案

题目：

`routers/` 目录放什么？

答案：

`routers/` 放接口分组文件，比如 `health.py`、`chat.py`、`rag.py`。每个文件负责一类接口。

### 自测 10 参考答案

题目：

`tests/` 目录放什么？

答案：

`tests/` 放自动化测试代码，用来验证接口和业务逻辑是否正常。

### 自测 11 参考答案

题目：

`conftest.py` 当前有什么作用？

答案：

当前 `conftest.py` 把 `projects/ai-service` 加入 Python 导入路径，让测试代码可以导入 `app.main`。

### 自测 12 参考答案

题目：

`__init__.py` 是什么？

答案：

`__init__.py` 可以让目录更明确地作为 Python 包使用，方便写类似 `from app.routers import health` 的导入语句。

### 自测 13 参考答案

题目：

为什么不要把所有代码都放进 `main.py`？

答案：

因为项目变大后，所有接口、配置、业务逻辑都堆在 `main.py` 会难以阅读、难以修改、难以测试。

按职责拆分到 `routers/`、`schemas/`、`services/`、`core/` 等目录后，结构更清楚，也更适合长期维护。

## 27. 本节小结

这一节你要建立一个基本认识：

```text
FastAPI 项目不是随便放几个 Python 文件。
它需要有配置、依赖、入口、路由、测试和说明文档。
```

当前项目骨架：

```text
pyproject.toml  管项目配置和依赖
uv.lock         锁定依赖版本
.python-version 管 Python 版本
README.md       告诉别人怎么运行
app/            放服务源码
routers/        放接口分组
tests/          放测试
```

下一节学习：

```text
FastAPI 最小服务 /health
```

下一节会逐行讲：

```text
FastAPI()
create_app()
include_router()
APIRouter()
@router.get("/health")
health_check()
return dict
JSON 响应
```

## 28. 参考资料

- [uv 官方文档：Working on projects](https://docs.astral.sh/uv/guides/projects/)
- [uv 官方文档：Locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/)
- [uv 官方文档：Python versions](https://docs.astral.sh/uv/concepts/python-versions/)
- [FastAPI First Steps](https://fastapi.tiangolo.com/tutorial/first-steps/)
