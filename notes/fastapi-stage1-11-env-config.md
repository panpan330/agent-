# FastAPI 阶段 1 第 11 节：`.env` 配置读取

日期：2026-07-07

本节目标：学会把配置从代码里拆出去，用 `.env`、环境变量和 `pydantic-settings` 集中管理配置。

前面我们已经有：

```text
GET  /health
POST /chat
ChatRequest
ChatResponse
TestClient 测试
```

现在开始学习工程化里非常重要的一块：

```text
配置管理。
```

以后接大模型时一定会遇到：

```text
OPENAI_API_KEY
MODEL_NAME
REQUEST_TIMEOUT_SECONDS
LOG_LEVEL
```

这些不应该写死在代码里，也不应该把真实密钥提交到 GitHub。

## 1. 本节学什么

本节学习这些内容：

1. 什么是配置。
2. 为什么配置不能写死在代码里。
3. 环境变量是什么。
4. `.env` 是什么。
5. `.env.example` 是什么。
6. 为什么 `.env` 不提交 GitHub。
7. 为什么 `.env.example` 要提交 GitHub。
8. `pydantic-settings` 是什么。
9. `BaseSettings` 是什么。
10. `SettingsConfigDict` 是什么。
11. `get_settings()` 为什么要缓存。
12. FastAPI 应用如何使用配置。
13. 配置怎么测试。
14. API key 后面应该怎么管理。

先记住一句话：

```text
配置 = 不同环境可能不同，但代码逻辑不应该频繁修改的值。
```

再记住一句话：

```text
真实 .env 不提交，.env.example 提交。
```

## 2. 什么是配置

配置是程序运行时需要用到的一些外部参数。

例如：

```text
服务名称
服务版本
模型名称
日志级别
请求超时时间
API key
数据库地址
Redis 地址
向量库地址
```

这些值有一个共同特点：

```text
不同环境可能不一样。
```

比如：

```text
开发环境用 mock-chat-model。
测试环境用 test-model。
生产环境用正式模型。
```

如果这些值都写死在代码里，每换一个环境就要改代码。

这不是好的工程习惯。

## 3. 为什么配置不能写死在代码里

不推荐：

```python
OPENAI_API_KEY = "sk-xxxxx"
MODEL_NAME = "gpt-4.1"
```

原因：

```text
1. 密钥容易泄露到 GitHub。
2. 不同环境需要改代码。
3. 本地、测试、生产配置容易混乱。
4. 改配置需要重新改代码、提交代码。
5. 敏感信息和业务逻辑混在一起。
```

正确方向：

```text
代码只规定需要哪些配置。
具体配置值从环境变量或 .env 文件读取。
```

## 4. 环境变量是什么

环境变量是操作系统或运行环境提供给程序的键值对。

例如：

```text
APP_NAME=AI Service
MODEL_NAME=mock-chat-model
LOG_LEVEL=INFO
```

程序启动后可以读取这些值。

环境变量适合放：

```text
部署环境差异
密钥
服务地址
运行参数
```

## 5. `.env` 是什么

`.env` 是一个本地配置文件。

它通常长这样：

```env
APP_NAME="AI Service"
MODEL_NAME="mock-chat-model"
REQUEST_TIMEOUT_SECONDS=30
LOG_LEVEL="INFO"
OPENAI_API_KEY="your-real-key"
```

它的作用是：

```text
在本地开发时，用文件模拟环境变量。
```

这样你不用每次在命令行里手动设置一堆环境变量。

## 6. `.env.example` 是什么

`.env.example` 是示例配置文件。

本节新增：

```text
projects/ai-service/.env.example
```

内容：

```env
APP_NAME="AI Service"
APP_DESCRIPTION="Python AI service for Java + Python + AI learning project."
APP_VERSION="0.1.0"
MODEL_NAME="mock-chat-model"
REQUEST_TIMEOUT_SECONDS=30
LOG_LEVEL="INFO"
OPENAI_API_KEY=""
```

它的作用是告诉别人：

```text
这个项目需要哪些配置项。
每个配置大概长什么样。
```

但它不放真实密钥。

## 7. `.env` 和 `.env.example` 的区别

| 文件 | 是否提交 GitHub | 作用 |
| --- | --- | --- |
| `.env` | 不提交 | 本地真实配置，可能有密钥 |
| `.env.example` | 提交 | 示例配置，告诉别人需要哪些变量 |

当前根 `.gitignore` 已经有：

```gitignore
.env
.env.*
!.env.example
```

含义：

```text
忽略 .env。
忽略 .env.*。
但不要忽略 .env.example。
```

这正是我们想要的。

## 8. 本节新增依赖

新增正式依赖：

```text
pydantic-settings
```

执行命令：

```powershell
uv add pydantic-settings
```

uv 同时安装了：

```text
python-dotenv
```

`pydantic-settings` 负责把环境变量读进 Pydantic 模型。

`python-dotenv` 负责读取 `.env` 文件里的键值对。

## 9. 本节新增了哪些代码

新增：

```text
projects/ai-service/.env.example
projects/ai-service/app/core/__init__.py
projects/ai-service/app/core/config.py
projects/ai-service/tests/test_config.py
```

修改：

```text
projects/ai-service/app/main.py
projects/ai-service/pyproject.toml
projects/ai-service/uv.lock
```

## 10. 为什么新增 app/core/

新增目录：

```text
app/core/
```

它用来放应用核心基础设施。

例如：

```text
config.py       配置
logging.py      日志
exceptions.py   异常处理
security.py     安全相关
```

当前先放：

```text
config.py
```

后面日志、trace_id、异常处理也可能放进 `core/`。

## 11. config.py 完整代码

文件：

```text
projects/ai-service/app/core/config.py
```

代码：

```python
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    app_name: str = Field(default="AI Service")
    app_description: str = Field(
        default="Python AI service for Java + Python + AI learning project."
    )
    app_version: str = Field(default="0.1.0")
    model_name: str = Field(default="mock-chat-model")
    request_timeout_seconds: float = Field(default=30.0, gt=0)
    log_level: str = Field(default="INFO")
    openai_api_key: str | None = Field(default=None, repr=False)

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

下面逐段解释。

## 12. `BaseSettings` 是什么

代码：

```python
from pydantic_settings import BaseSettings
```

`BaseSettings` 是 `pydantic-settings` 里的基础配置类。

它和 Pydantic `BaseModel` 很像，但专门用于配置。

它会从这些来源读取值：

```text
初始化参数
环境变量
.env 文件
默认值
```

所以：

```python
class Settings(BaseSettings):
    app_name: str = "AI Service"
```

表示：

```text
定义一个配置项 app_name。
默认值是 AI Service。
如果环境变量 APP_NAME 存在，就可以覆盖默认值。
```

## 13. `Settings` 是什么

`Settings` 是我们项目自己的配置类。

当前配置项：

| 字段 | 环境变量 | 作用 |
| --- | --- | --- |
| `app_name` | `APP_NAME` | 应用名称 |
| `app_description` | `APP_DESCRIPTION` | 应用描述 |
| `app_version` | `APP_VERSION` | 应用版本 |
| `model_name` | `MODEL_NAME` | 模型名称 |
| `request_timeout_seconds` | `REQUEST_TIMEOUT_SECONDS` | 请求超时时间 |
| `log_level` | `LOG_LEVEL` | 日志级别 |
| `openai_api_key` | `OPENAI_API_KEY` | 未来模型 API key |

Pydantic Settings 会把字段名和环境变量对应起来。

例如：

```text
app_name <-> APP_NAME
model_name <-> MODEL_NAME
```

## 14. 为什么 openai_api_key 是可选

当前：

```python
openai_api_key: str | None = Field(default=None, repr=False)
```

它是可选的。

因为现在还没有接真实大模型。

如果现在强制要求 `OPENAI_API_KEY`，那么没有密钥就跑不了本地测试。

后面真正接模型时，可以在调用模型前检查：

```text
如果没有 API key，就返回明确错误。
```

`repr=False` 的作用是：

```text
打印 Settings 对象时，不显示这个字段值。
```

它不是绝对安全措施，但能减少日志里误打印密钥的风险。

## 15. `request_timeout_seconds` 为什么要 `gt=0`

代码：

```python
request_timeout_seconds: float = Field(default=30.0, gt=0)
```

`gt=0` 表示：

```text
必须大于 0。
```

为什么？

因为超时时间不能是：

```text
0
负数
```

如果有人配置：

```env
REQUEST_TIMEOUT_SECONDS=0
```

Pydantic 会校验失败。

## 16. `SettingsConfigDict` 是什么

代码：

```python
model_config = SettingsConfigDict(
    env_file=ENV_FILE,
    env_file_encoding="utf-8",
    extra="ignore",
)
```

它是 Pydantic Settings 的模型配置。

当前含义：

```text
env_file=ENV_FILE           从 projects/ai-service/.env 读取配置
env_file_encoding="utf-8"   用 UTF-8 读取
extra="ignore"              .env 里多余配置先忽略
```

为什么 `extra="ignore"`？

因为 `.env` 里以后可能有一些当前模型还没定义的变量。

初学阶段先允许忽略，减少无关错误。

## 17. 为什么 ENV_FILE 用绝对路径

代码：

```python
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"
```

`config.py` 在：

```text
app/core/config.py
```

`parents[2]` 指向：

```text
projects/ai-service
```

所以：

```text
ENV_FILE = projects/ai-service/.env
```

这样比简单写：

```python
env_file=".env"
```

更稳定。

因为程序从不同工作目录启动时，`.env` 相对路径可能不一样。

## 18. `get_settings()` 是什么

代码：

```python
@lru_cache
def get_settings() -> Settings:
    return Settings()
```

它是获取配置的统一入口。

以后应用里需要配置时，优先用：

```python
settings = get_settings()
```

不要到处写：

```python
Settings()
```

这样可以统一控制配置读取。

## 19. 为什么要 `@lru_cache`

`@lru_cache` 会缓存函数返回值。

第一次调用：

```python
get_settings()
```

会创建一个 `Settings` 对象。

后面再调用：

```python
get_settings()
```

会复用同一个对象。

好处：

```text
不用反复读取 .env。
应用内部配置保持一致。
测试时可以 cache_clear。
```

FastAPI 官方设置文档也推荐用缓存来避免重复读取配置。

## 20. main.py 如何使用配置

修改后：

```python
from app.core.config import get_settings
```

在 `create_app()` 里：

```python
settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
)
```

以前是写死：

```python
title="AI Service"
version="0.1.0"
```

现在是：

```text
从配置读取。
```

这样如果 `.env` 里写：

```env
APP_NAME="Local AI Service"
APP_VERSION="0.2.0"
```

应用标题和版本就可以变化，而不用改代码。

## 21. 配置读取优先级

初学阶段先这样理解：

```text
显式传入参数 > 环境变量 > .env 文件 > 默认值
```

例如：

```python
Settings(app_name="Manual")
```

优先用 `"Manual"`。

如果没有显式传入，但系统环境变量有：

```text
APP_NAME=FromEnv
```

就用环境变量。

如果环境变量没有，但 `.env` 有：

```env
APP_NAME="FromFile"
```

就用 `.env`。

如果都没有，就用默认值：

```text
AI Service
```

## 22. 本节测试文件

新增：

```text
projects/ai-service/tests/test_config.py
```

测试内容：

```text
默认配置。
环境变量覆盖。
.env 文件读取。
非法 timeout 拒绝。
get_settings 缓存。
```

## 23. 测试默认值

代码：

```python
settings = Settings(_env_file=None)
```

`_env_file=None` 表示：

```text
这个测试不读取 .env 文件。
```

这样可以稳定测试默认值。

断言：

```python
assert settings.app_name == "AI Service"
assert settings.model_name == "mock-chat-model"
assert settings.openai_api_key is None
```

## 24. 测试环境变量覆盖

代码：

```python
monkeypatch.setenv("APP_NAME", "Local AI Service")
monkeypatch.setenv("MODEL_NAME", "demo-model")
monkeypatch.setenv("REQUEST_TIMEOUT_SECONDS", "12.5")

settings = Settings(_env_file=None)
```

`monkeypatch` 是 pytest 提供的测试工具。

它可以临时设置环境变量。

测试结束后会自动恢复。

这比手动改系统环境变量安全。

## 25. 测试 .env 文件读取

测试里用 `tmp_path` 创建临时 `.env`：

```python
env_file = tmp_path / ".env"
env_file.write_text(...)

settings = Settings(_env_file=env_file)
```

这样不会影响真实项目里的 `.env`。

测试验证：

```text
Settings 能从指定 env 文件读取配置。
```

## 26. 测试非法 timeout

代码：

```python
with pytest.raises(ValidationError):
    Settings(request_timeout_seconds=0, _env_file=None)
```

因为配置里写了：

```python
gt=0
```

所以 0 不合法。

错误类型是：

```text
greater_than
```

## 27. 测试 get_settings 缓存

代码：

```python
get_settings.cache_clear()
monkeypatch.setenv("APP_NAME", "Cached AI Service")

first = get_settings()
second = get_settings()

assert first is second
```

`first is second` 表示：

```text
两次拿到的是同一个对象。
```

这证明缓存生效。

测试结束再：

```python
get_settings.cache_clear()
```

避免影响其他测试。

## 28. API key 应该怎么放

以后不要这样：

```python
api_key = "sk-xxxx"
```

应该放到本地 `.env`：

```env
OPENAI_API_KEY="sk-xxxx"
```

代码里读取：

```python
settings = get_settings()
api_key = settings.openai_api_key
```

并且 `.env` 不提交 GitHub。

只提交 `.env.example`：

```env
OPENAI_API_KEY=""
```

## 29. 常见错误

### 错误 1：把真实 .env 提交到 GitHub

这是严重错误。

`.env` 可能包含：

```text
API key
数据库密码
Redis 密码
模型服务地址
```

必须忽略。

### 错误 2：只提交 .env，不提交 .env.example

别人拉代码后不知道需要哪些配置。

应该提交 `.env.example`。

### 错误 3：配置散落在各个文件

不推荐：

```text
main.py 里一个配置
chat.py 里一个配置
service.py 里一个配置
```

推荐集中到：

```text
app/core/config.py
```

### 错误 4：在测试中依赖真实 .env

测试应该尽量稳定。

不要要求测试必须依赖你本机真实 `.env`。

可以用：

```python
Settings(_env_file=None)
Settings(_env_file=temp_env_file)
monkeypatch.setenv(...)
```

### 错误 5：以为 repr=False 就绝对安全

`repr=False` 只是避免直接打印模型时显示字段值。

它不能替代：

```text
不记录密钥日志。
不提交 .env。
不把密钥返回给前端。
```

## 30. 本节必须掌握的最小知识

这一节最少要掌握：

```text
配置不应该写死在代码里。
.env 保存本地真实配置，不提交 GitHub。
.env.example 保存示例配置，应该提交 GitHub。
pydantic-settings 用来读取环境变量和 .env。
BaseSettings 是配置模型基类。
Settings 是项目集中配置类。
get_settings() 是统一配置入口。
@lru_cache 让配置只读一次并复用。
API key 后面必须从配置读取，不能写死。
```

## 31. 本节练习

### 练习 1：解释配置

题目：

用自己的话解释：

```text
什么是配置？为什么配置不应该写死在代码里？
```

### 练习 2：区分 .env 和 .env.example

题目：

说明下面两个文件的区别：

```text
.env
.env.example
```

哪个应该提交 GitHub？哪个不应该？

### 练习 3：解释 Settings

题目：

解释下面代码的作用：

```python
class Settings(BaseSettings):
    app_name: str = Field(default="AI Service")
```

### 练习 4：解释 get_settings

题目：

解释下面代码：

```python
@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### 练习 5：判断配置是否安全

题目：

下面做法是否安全？为什么？

```python
OPENAI_API_KEY = "sk-real-key"
```

### 练习 6：写一个 .env 示例

题目：

写一个本地 `.env` 示例，包含：

```text
APP_NAME
MODEL_NAME
LOG_LEVEL
OPENAI_API_KEY
```

### 练习 7：解释测试里的 _env_file=None

题目：

为什么测试默认值时要写：

```python
Settings(_env_file=None)
```

## 32. 本节练习参考答案

### 练习 1 参考答案：解释配置

题目：

用自己的话解释：

```text
什么是配置？为什么配置不应该写死在代码里？
```

参考答案：

配置是程序运行时需要的外部参数，例如模型名称、日志级别、超时时间、API key。

配置不应该写死在代码里，因为不同环境可能不同，而且密钥写进代码容易泄露到 GitHub。

### 练习 2 参考答案：区分 .env 和 .env.example

题目：

说明下面两个文件的区别：

```text
.env
.env.example
```

哪个应该提交 GitHub？哪个不应该？

参考答案：

`.env` 是本地真实配置文件，可能包含密钥，不应该提交 GitHub。

`.env.example` 是示例配置文件，不包含真实密钥，应该提交 GitHub，让别人知道项目需要哪些配置。

### 练习 3 参考答案：解释 Settings

题目：

解释下面代码的作用：

```python
class Settings(BaseSettings):
    app_name: str = Field(default="AI Service")
```

参考答案：

这定义了一个配置类 `Settings`。

它继承 `BaseSettings`，表示它可以从环境变量和 `.env` 文件读取配置。

`app_name` 是一个配置项，默认值是 `"AI Service"`。

环境变量 `APP_NAME` 可以覆盖这个默认值。

### 练习 4 参考答案：解释 get_settings

题目：

解释下面代码：

```python
@lru_cache
def get_settings() -> Settings:
    return Settings()
```

参考答案：

`get_settings()` 是获取配置的统一入口。

`@lru_cache` 会缓存第一次创建的 `Settings` 对象，后面重复调用时直接复用，避免反复读取 `.env`。

### 练习 5 参考答案：判断配置是否安全

题目：

下面做法是否安全？为什么？

```python
OPENAI_API_KEY = "sk-real-key"
```

参考答案：

不安全。

真实 API key 写在代码里，容易被提交到 GitHub，也不方便区分本地、测试、生产环境。

应该放到 `.env` 或环境变量里，再通过 `Settings` 读取。

### 练习 6 参考答案：写一个 .env 示例

题目：

写一个本地 `.env` 示例，包含：

```text
APP_NAME
MODEL_NAME
LOG_LEVEL
OPENAI_API_KEY
```

参考答案：

```env
APP_NAME="Local AI Service"
MODEL_NAME="mock-chat-model"
LOG_LEVEL="DEBUG"
OPENAI_API_KEY="sk-your-real-key"
```

注意：

```text
这个 .env 不应该提交 GitHub。
```

### 练习 7 参考答案：解释测试里的 _env_file=None

题目：

为什么测试默认值时要写：

```python
Settings(_env_file=None)
```

参考答案：

这样可以明确告诉 Pydantic Settings 不读取 `.env` 文件。

测试默认值时，如果读取了本机 `.env`，测试结果可能受到本地配置影响，变得不稳定。

## 33. 自测问题

1. 什么是配置？
2. 为什么 API key 不能写死在代码里？
3. 环境变量是什么？
4. `.env` 是什么？
5. `.env.example` 是什么？
6. `.env` 应该提交 GitHub 吗？
7. `.env.example` 应该提交 GitHub 吗？
8. `pydantic-settings` 是干什么的？
9. `BaseSettings` 是什么？
10. `SettingsConfigDict(env_file=...)` 有什么作用？
11. `extra="ignore"` 有什么作用？
12. `get_settings()` 为什么要缓存？
13. `get_settings.cache_clear()` 在测试里有什么用？
14. 当前 `main.py` 从哪些配置读取应用信息？
15. 后面真实大模型 API key 应该从哪里读取？

## 34. 自测参考答案

### 自测 1 参考答案

题目：

什么是配置？

答案：

配置是程序运行时需要的外部参数，例如服务名、模型名、日志级别、超时时间、API key。

### 自测 2 参考答案

题目：

为什么 API key 不能写死在代码里？

答案：

因为代码可能提交到 GitHub，真实 API key 写在代码里会泄露，也不方便不同环境使用不同密钥。

### 自测 3 参考答案

题目：

环境变量是什么？

答案：

环境变量是操作系统或运行环境提供给程序的键值对，程序可以在运行时读取它们。

### 自测 4 参考答案

题目：

`.env` 是什么？

答案：

`.env` 是本地配置文件，用来在开发时保存环境变量形式的配置，可能包含真实密钥。

### 自测 5 参考答案

题目：

`.env.example` 是什么？

答案：

`.env.example` 是示例配置文件，用来告诉别人项目需要哪些配置项，不包含真实密钥。

### 自测 6 参考答案

题目：

`.env` 应该提交 GitHub 吗？

答案：

不应该。

`.env` 可能包含真实密钥和本地配置。

### 自测 7 参考答案

题目：

`.env.example` 应该提交 GitHub 吗？

答案：

应该。

它不包含真实密钥，能帮助别人知道项目需要哪些配置。

### 自测 8 参考答案

题目：

`pydantic-settings` 是干什么的？

答案：

它是 Pydantic 体系里用于配置管理的库，可以把环境变量和 `.env` 文件读取到 Pydantic 配置模型里。

### 自测 9 参考答案

题目：

`BaseSettings` 是什么？

答案：

`BaseSettings` 是 pydantic-settings 的配置模型基类。继承它的类可以从环境变量和 `.env` 读取配置。

### 自测 10 参考答案

题目：

`SettingsConfigDict(env_file=...)` 有什么作用？

答案：

它告诉 `Settings` 从哪个 `.env` 文件读取配置，以及使用什么编码、如何处理额外字段。

### 自测 11 参考答案

题目：

`extra="ignore"` 有什么作用？

答案：

它表示 `.env` 或输入中出现模型未定义的额外字段时，先忽略这些字段。

### 自测 12 参考答案

题目：

`get_settings()` 为什么要缓存？

答案：

为了避免反复读取 `.env`，并让应用内部复用同一个配置对象。

### 自测 13 参考答案

题目：

`get_settings.cache_clear()` 在测试里有什么用？

答案：

它可以清空缓存，让测试能重新读取新的环境变量或配置，避免上一个测试的配置影响下一个测试。

### 自测 14 参考答案

题目：

当前 `main.py` 从哪些配置读取应用信息？

答案：

当前 `main.py` 从：

```text
settings.app_name
settings.app_description
settings.app_version
```

读取 FastAPI 应用标题、描述和版本。

### 自测 15 参考答案

题目：

后面真实大模型 API key 应该从哪里读取？

答案：

应该从环境变量或 `.env` 读取，例如 `OPENAI_API_KEY`，再通过 `settings.openai_api_key` 使用。

## 35. 本节小结

这一节完成了配置管理的基础：

```text
.env.example
app/core/config.py
Settings
get_settings()
main.py 使用配置
配置测试
```

现在项目已经有了集中配置入口。

后面接大模型时，不会把 API key 写死在代码里，而是从配置读取。

下一节学习：

```text
logging 日志
```

会讲：

```text
为什么不能只用 print
日志级别是什么
如何用 LOG_LEVEL 控制日志
请求日志怎么打
模型调用日志后面怎么扩展
```

## 36. 参考资料

- [FastAPI：Settings and Environment Variables](https://fastapi.tiangolo.com/advanced/settings/)
- [Pydantic：Settings Management](https://pydantic.dev/docs/validation/latest/concepts/pydantic_settings/)
- [python-dotenv PyPI](https://pypi.org/project/python-dotenv/)
