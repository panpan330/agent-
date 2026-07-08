# 阶段 2 第 4 节：OpenAI-compatible SDK 基础调用方式

## 1. 这一节学什么

这一节开始进入真实模型调用前的代码准备。

我们这次不只讲 OpenAI 官方接口，而是讲：

```text
OpenAI-compatible SDK 调用方式
```

原因是你准备用的是：

```text
阿里云百炼 / 千问 / OpenAI 兼容接口
```

你的接口属于这一类：

```text
OpenAI-compatible API
```

意思是：

```text
服务商不是 OpenAI，但它尽量按照 OpenAI API 的调用格式提供接口。
```

这一节要学：

```text
SDK 是什么
SDK 和 HTTP API 的关系
OpenAI-compatible 是什么
为什么 compatible 接口也可以用 openai Python SDK
base_url 是什么
model 是什么
为什么要改成 LLM_API_KEY / LLM_BASE_URL / LLM_MODEL
怎么安装 openai Python SDK
怎么创建 SDK client
怎么写一个不默认花钱的 smoke test 脚本
为什么这节先用 Chat Completions，不直接用 Responses API
```

## 2. 再强调一次：真实 key 不能发给别人

你之前已经把一个真实 API key 发到了聊天里。

从安全角度看：

```text
这个 key 应该当作已经泄露。
```

正确处理方式是：

```text
去控制台作废旧 key
重新生成新 key
新 key 只放本机 .env
不要发给我
不要写进笔记
不要写进 README
不要上传 GitHub
```

本节代码和文档都不会保存你的真实 key。

## 3. SDK 是什么

SDK 的全称是：

```text
Software Development Kit
软件开发工具包
```

你可以先把 SDK 理解成：

```text
服务商或官方给程序员准备的一套代码工具。
```

不用 SDK 时，你可能要自己写：

```text
HTTP 请求地址
请求头 Authorization
JSON 请求体
超时
错误处理
响应 JSON 解析
```

用 SDK 后，很多重复细节会被封装。

你写的是：

```python
client.chat.completions.create(...)
```

SDK 在底层帮你发 HTTP 请求。

## 4. SDK 和 HTTP API 的关系

这点很重要。

SDK 不是魔法。

SDK 本质上还是在调用 HTTP API。

可以理解成：

```text
你的 Python 代码
-> OpenAI Python SDK
-> HTTP 请求
-> 模型服务商 API
-> HTTP 响应
-> SDK 转成 Python 对象
-> 你的 Python 代码读取结果
```

所以你要知道两层：

```text
表层：怎么用 SDK 写代码
底层：SDK 实际是在帮你发 HTTP 请求
```

后面出错时，这个理解很关键。

比如：

```text
401 可能是 key 错
404 可能是模型名或路径不对
429 可能是限流
500 可能是服务商内部错误
timeout 可能是网络或模型响应太慢
```

这些都不是 Python 语法问题，而是 API 调用问题。

## 5. 什么是 OpenAI-compatible API

OpenAI-compatible API 可以理解成：

```text
第三方模型服务商提供了一个尽量兼容 OpenAI 调用格式的接口。
```

你原来可能写：

```python
from openai import OpenAI

client = OpenAI(api_key="OpenAI key")
```

如果换成兼容接口，通常改成：

```python
client = OpenAI(
    api_key="第三方服务商 key",
    base_url="第三方服务商 OpenAI-compatible 地址",
)
```

也就是说，核心改动通常是：

```text
api_key
base_url
model
```

阿里云百炼官方文档也说明，千问模型支持 OpenAI 兼容接口，迁移时主要调整 API Key、BASE_URL 和模型名称。

## 6. base_url 是什么

`base_url` 是：

```text
API 的基础地址。
```

OpenAI 官方默认基础地址大致是：

```text
https://api.openai.com/v1
```

阿里云百炼兼容模式会是类似：

```text
https://your-workspace-id.cn-beijing.maas.aliyuncs.com/compatible-mode/v1
```

为什么要有 `base_url`？

因为 SDK 默认会请求 OpenAI 官方地址。

如果你要让同一个 SDK 请求阿里云百炼，就要告诉 SDK：

```text
不要去默认 OpenAI 地址。
去我配置的这个兼容接口地址。
```

这就是 `base_url` 的作用。

## 7. model 是什么

`model` 表示你要调用哪个模型。

你提供的是：

```text
qwen3.7-plus
```

它不是密钥。

它是模型名。

调用时会出现在：

```python
completion = client.chat.completions.create(
    model="qwen3.7-plus",
    messages=[...],
)
```

如果模型名写错，可能会出现：

```text
模型不存在
权限不足
404
400
```

具体错误要看服务商返回。

## 8. 为什么不用 `OPENAI_API_KEY`

之前我们准备了：

```text
OPENAI_API_KEY
```

这个名字适合直接调用 OpenAI 官方 API。

但你现在使用的是阿里云百炼兼容接口。

如果仍然叫 `OPENAI_API_KEY`，容易误会：

```text
这是 OpenAI 的 key。
```

所以现在项目改成更通用的：

```text
LLM_PROVIDER
LLM_MODEL
LLM_BASE_URL
LLM_API_KEY
```

这样以后你换服务商，只要改 `.env`：

```text
OpenAI
阿里云百炼
DeepSeek
Kimi
智谱
OpenRouter
本地兼容接口
```

代码不用大改。

## 9. 当前 `.env.example`

示例配置是：

```env
LLM_PROVIDER="aliyun-compatible"
LLM_MODEL="qwen3.7-plus"
LLM_BASE_URL="https://your-workspace-id.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
LLM_API_KEY=""
```

注意：

```text
.env.example 可以上传 GitHub。
.env.example 不能放真实 key。
.env.example 里的 base_url 也使用了占位符。
```

你的真实配置应该放在：

```text
D:\wendang\java+python+ai\projects\ai-service\.env
```

不要放进：

```text
.env.example
README
notes
代码
测试
聊天记录
```

## 10. 当前项目配置类怎么读

文件：

```text
projects/ai-service/app/core/config.py
```

新增字段：

```python
llm_provider: str = Field(default="openai-compatible")
llm_model: str = Field(default="qwen3.7-plus")
llm_base_url: str | None = Field(default=None)
llm_api_key: str | None = Field(default=None, repr=False)
```

含义：

```text
llm_provider  当前服务商标识
llm_model     当前模型名
llm_base_url  OpenAI-compatible 接口地址
llm_api_key   API key，敏感信息
```

`repr=False` 表示：

```text
打印 Settings 对象时，尽量不要把这个字段显示出来。
```

但它不是绝对安全。

你仍然不能主动打印 key、写日志或提交 `.env`。

## 11. 为什么有 `resolved_llm_api_key`

项目新增了：

```python
@property
def resolved_llm_api_key(self) -> str | None:
    api_key = self.llm_api_key or self.openai_api_key
    if not api_key or not api_key.strip():
        return None
    return api_key.strip()
```

这段的意思是：

```text
优先读 LLM_API_KEY
如果没有，再兜底读旧的 OPENAI_API_KEY
空字符串和全空格都当成没有配置
读取到后去掉首尾空格
```

为什么保留旧字段？

因为前面阶段已经讲过 `OPENAI_API_KEY`。

直接删除会让旧学习内容和测试突然不连贯。

所以现在是平滑过渡：

```text
新代码优先 LLM_API_KEY
旧字段暂时保留兼容
```

## 12. 为什么有 `resolved_llm_base_url`

项目新增了：

```python
@property
def resolved_llm_base_url(self) -> str | None:
    if not self.llm_base_url or not self.llm_base_url.strip():
        return None
    return self.llm_base_url.strip()
```

作用：

```text
空字符串 -> None
全空格 -> None
首尾有空格 -> 去掉空格
```

这能避免 `.env` 里不小心多打一个空格导致接口地址错误。

## 13. 安装 openai Python SDK

本节执行了：

```powershell
uv add openai
```

它会修改：

```text
projects/ai-service/pyproject.toml
projects/ai-service/uv.lock
```

现在依赖里有：

```toml
openai>=2.44.0
```

这表示：

```text
项目可以 import openai
可以创建 OpenAI client
可以调用兼容 OpenAI 的接口
```

## 14. SDK client 初始化

文件：

```text
projects/ai-service/app/services/llm_client.py
```

核心代码：

```python
from openai import OpenAI

from app.core.config import Settings


def create_openai_compatible_client(settings: Settings) -> OpenAI:
    api_key = settings.resolved_llm_api_key
    if api_key is None:
        raise ValueError("LLM_API_KEY is not configured")

    client_kwargs: dict[str, object] = {
        "api_key": api_key,
        "timeout": settings.request_timeout_seconds,
    }

    base_url = settings.resolved_llm_base_url
    if base_url is not None:
        client_kwargs["base_url"] = base_url

    return OpenAI(**client_kwargs)
```

逐行理解：

```text
from openai import OpenAI
```

导入 SDK 提供的客户端类。

```text
api_key = settings.resolved_llm_api_key
```

从配置里取 key。

```text
if api_key is None:
    raise ValueError(...)
```

如果没有 key，提前报明确错误。

```text
timeout
```

设置请求超时时间。

```text
base_url
```

如果配置了兼容接口地址，就传给 SDK。

## 15. 为什么提前检查 key

如果不提前检查 key，SDK 可能在真正请求时才报错。

错误可能比较绕。

现在我们提前判断：

```text
没有 LLM_API_KEY -> 直接告诉你缺少配置
```

这叫：

```text
fail fast
快速失败
```

对后端工程很重要。

## 16. 为什么不在 FastAPI `/chat` 里直接写 SDK 初始化

可以写，但不推荐。

如果把所有代码都塞进 `/chat` 路由：

```text
读取配置
创建 SDK client
组装 messages
调用模型
解析响应
处理错误
记录日志
返回响应
```

路由会越来越乱。

所以我们先把 SDK 初始化放到：

```text
app/services/llm_client.py
```

以后再继续拆：

```text
llm_client.py        创建 client
llm_service.py       调用模型
chat.py              FastAPI 路由
```

这就是后端分层。

## 17. 为什么本节先写 smoke test 脚本

smoke test 可以理解成：

```text
冒烟测试，最小可用性检查。
```

它不是完整自动化测试。

它的作用是：

```text
确认配置能读到
确认 SDK client 能创建
确认需要时能手动发一次最小请求
```

文件：

```text
projects/ai-service/scripts/llm_compatible_smoke_test.py
```

默认运行：

```powershell
uv run python scripts/llm_compatible_smoke_test.py
```

只检查配置，不调用模型。

真实调用：

```powershell
uv run python scripts/llm_compatible_smoke_test.py --call
```

只有你明确加 `--call`，才会请求模型。

这样可以避免：

```text
误调用
误花钱
没有准备好 key 就报复杂错误
```

## 18. smoke test 脚本做了什么

脚本逻辑是：

```text
1. 读取 Settings
2. 检查有没有 LLM_API_KEY
3. 打印 provider、model、base_url 是否配置
4. 如果没有 --call，直接结束
5. 如果有 --call，创建 SDK client
6. 调用 client.chat.completions.create(...)
7. 打印模型回复
```

它不会打印 API key。

这是刻意设计的。

## 19. 为什么本节先用 Chat Completions

前面我们说过：

```text
OpenAI 官方新项目推荐 Responses API。
```

OpenAI 文本生成文档也说明，直接模型请求推荐使用 Responses API。

但是你当前使用的是：

```text
阿里云百炼 OpenAI-compatible 接口
```

阿里云百炼官方文本生成模型 API 参考里，把 OpenAI 兼容 Chat Completions 标为与 OpenAI 客户端库直接兼容，迁移现有应用或接入第三方工具成本最低。

所以本节先用：

```python
client.chat.completions.create(...)
```

原因是：

```text
兼容接口资料更多
第三方 OpenAI-compatible 更常见
下一节正好要学 messages
先跑通基础调用更稳
```

后面我们仍然会讲：

```text
Responses API
结构化输出
streaming
```

但兼容接口学习阶段，先以 Chat Completions 打基础。

## 20. Chat Completions 最小结构

最小结构大概是：

```python
completion = client.chat.completions.create(
    model=settings.llm_model,
    messages=[
        {"role": "system", "content": "你是一个耐心的编程学习助手。"},
        {"role": "user", "content": "请用一句话解释 FastAPI 是什么。"},
    ],
)
```

这里有两个核心参数：

```text
model
messages
```

`model`：

```text
你要调用哪个模型
```

`messages`：

```text
这次对话内容
```

下一节会详细讲：

```text
system
user
assistant
```

## 21. 为什么 smoke test 里没有写 max_tokens

现在先不写。

原因是：

```text
不同兼容接口对参数支持细节可能不同
本节重点是 SDK 和最小调用链路
先减少变量
```

后面接入真实 `/chat` 时，会再考虑：

```text
max_tokens
max_completion_tokens
max_output_tokens
不同服务商参数差异
```

当前项目配置里已经有：

```text
MAX_OUTPUT_TOKENS
```

但这节先不强行塞进兼容调用里。

## 22. 自动化测试怎么做

本节新增测试：

```text
tests/test_llm_client.py
```

测试不会真实调用模型。

它使用一个假的类：

```python
class FakeOpenAI:
    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs
```

然后用 `monkeypatch` 把真实 `OpenAI` 替换掉。

这样测试能验证：

```text
api_key 是否传对
base_url 是否传对
timeout 是否传对
缺 key 是否报错
```

但不会产生网络请求和费用。

这就是：

```text
测试外部服务时，不直接依赖真实外部服务。
```

## 23. 为什么不自动真实调用

自动化测试不能依赖真实模型。

原因：

```text
需要真实 key
会产生费用
网络可能不稳定
模型响应可能变化
CI 环境不一定有密钥
失败原因可能不是代码错误
```

所以真实调用放在：

```text
手动 smoke test
```

自动测试只测：

```text
配置
初始化
参数组装
错误分支
```

## 24. 本节代码改动

### 改动 1：安装 SDK

文件：

```text
projects/ai-service/pyproject.toml
projects/ai-service/uv.lock
```

新增依赖：

```text
openai
```

### 改动 2：通用 LLM 配置

文件：

```text
projects/ai-service/.env.example
projects/ai-service/app/core/config.py
tests/test_config.py
```

新增：

```text
LLM_PROVIDER
LLM_MODEL
LLM_BASE_URL
LLM_API_KEY
```

### 改动 3：SDK client 初始化

文件：

```text
projects/ai-service/app/services/llm_client.py
tests/test_llm_client.py
```

作用：

```text
根据 Settings 创建 OpenAI-compatible client。
```

### 改动 4：手动 smoke test 脚本

文件：

```text
projects/ai-service/scripts/llm_compatible_smoke_test.py
```

作用：

```text
默认只检查配置。
加 --call 才真实调用模型。
```

## 25. 你本机下一步怎么配

在你的本机 `.env`：

```text
D:\wendang\java+python+ai\projects\ai-service\.env
```

填写：

```env
LLM_PROVIDER="aliyun-compatible"
LLM_MODEL="qwen3.7-plus"
LLM_BASE_URL="你自己的兼容接口 base_url"
LLM_API_KEY=""
```

注意：

```text
你要把重新生成的新 key 填到 LLM_API_KEY 的双引号中间。
真实值只写在本机 .env。
这个文件不上传 GitHub。
不要把真实值发给我。
```

## 26. 手动检查命令

进入项目：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
```

检查配置：

```powershell
uv run python scripts/llm_compatible_smoke_test.py
```

如果没有 key，会提示：

```text
LLM_API_KEY is missing. Put your real key in local .env first.
```

如果配置好了，会看到类似：

```text
provider=aliyun-compatible
model=qwen3.7-plus
base_url_configured=True
SDK configuration looks ready. No API call was made.
```

## 27. 手动真实调用命令

只有你确认要真实调用模型时，再运行：

```powershell
uv run python scripts/llm_compatible_smoke_test.py --call
```

也可以改 prompt：

```powershell
uv run python scripts/llm_compatible_smoke_test.py --call --prompt "请用一句话解释 token 是什么"
```

注意：

```text
这会产生真实 API 请求。
可能产生费用。
```

## 28. 常见错误

### 错误 1：缺少 API key

现象：

```text
LLM_API_KEY is missing
```

原因：

```text
.env 没有写 LLM_API_KEY
或者写成了空字符串
```

### 错误 2：key 错误

可能现象：

```text
401
Unauthorized
Invalid API key
```

处理：

```text
确认 key 是否作废
确认 key 是否属于当前地域或业务空间
确认没有复制多余空格
```

### 错误 3：base_url 错误

可能现象：

```text
404
连接失败
域名无法访问
```

处理：

```text
检查 LLM_BASE_URL
确认地域
确认 workspace id
确认末尾包含 compatible-mode/v1
```

### 错误 4：model 错误

可能现象：

```text
model not found
model unavailable
权限不足
```

处理：

```text
检查 LLM_MODEL
确认账号是否有模型权限
确认模型名是否和控制台一致
```

## 29. 本节练习

### 练习 1

题目：

用自己的话解释 SDK 是什么。

参考答案：

SDK 是软件开发工具包，是服务商或官方提供给程序员使用的一组代码工具。

它可以封装 HTTP 请求、认证、响应解析、错误处理等重复细节，让我们用更简单的代码调用 API。

### 练习 2

题目：

SDK 和 HTTP API 是什么关系？

参考答案：

SDK 底层仍然是在调用 HTTP API。

它只是把手写 HTTP 请求、请求头、JSON 请求体和响应解析封装成更方便的 Python 方法。

### 练习 3

题目：

OpenAI-compatible API 是什么？

参考答案：

OpenAI-compatible API 是第三方模型服务商提供的兼容 OpenAI 调用格式的接口。

它不是 OpenAI 官方 API，但可以让我们用类似 OpenAI SDK 的方式调用第三方模型。

### 练习 4

题目：

调用兼容接口时，通常需要改哪三个核心配置？

参考答案：

通常需要改：

```text
api_key
base_url
model
```

### 练习 5

题目：

`base_url` 的作用是什么？

参考答案：

`base_url` 用来告诉 SDK 请求哪个 API 服务地址。

如果不配置，SDK 默认会请求 OpenAI 官方地址；配置后可以请求阿里云百炼、DeepSeek、OpenRouter 等兼容接口。

### 练习 6

题目：

为什么我们把配置改成 `LLM_API_KEY`，而不是继续只用 `OPENAI_API_KEY`？

参考答案：

因为当前项目可能调用不同服务商的模型，不一定只调用 OpenAI。

`LLM_API_KEY` 更通用，适合 OpenAI-compatible、阿里云、DeepSeek、Kimi 等不同服务商。

### 练习 7

题目：

为什么自动化测试不能直接调用真实模型？

参考答案：

因为真实模型调用需要 API key，会产生费用，网络可能不稳定，模型响应也可能变化。

自动化测试应该尽量稳定、可重复、不依赖外部服务。

### 练习 8

题目：

`scripts/llm_compatible_smoke_test.py` 默认会不会调用模型？

参考答案：

不会。

默认只检查配置。

只有加 `--call` 才会真实调用模型。

### 练习 9

题目：

为什么本节先用 `client.chat.completions.create(...)`？

参考答案：

因为阿里云百炼的 OpenAI-compatible Chat Completions 与 OpenAI 客户端库直接兼容，迁移成本低，并且下一节正好要学习 messages。

虽然 OpenAI 官方新项目推荐 Responses API，但第三方兼容接口阶段先用 Chat Completions 更稳。

### 练习 10

题目：

真实 API key 应该放在哪里？

参考答案：

真实 API key 应该只放本机 `.env` 或系统环境变量里。

不能放进代码、README、笔记、测试、截图、聊天记录或 GitHub。

## 30. 本节自测

### 自测 1

题目：

SDK 的全称是什么？

参考答案：

SDK 的全称是 Software Development Kit，中文是软件开发工具包。

### 自测 2

题目：

OpenAI-compatible 是否表示服务商一定是 OpenAI？

参考答案：

不是。

它表示接口格式兼容 OpenAI，但服务商可以是阿里云、DeepSeek、OpenRouter 或其他平台。

### 自测 3

题目：

`LLM_BASE_URL` 是不是密钥？

参考答案：

不是。

它是 API 基础地址。

但它可能包含业务空间信息，公开仓库里仍然建议使用占位符。

### 自测 4

题目：

`LLM_API_KEY=""` 算不算配置成功？

参考答案：

不算。

空字符串没有真实密钥内容。

### 自测 5

题目：

`resolved_llm_api_key` 优先读取哪个字段？

参考答案：

优先读取 `LLM_API_KEY`。

如果没有，再兜底读取旧字段 `OPENAI_API_KEY`。

### 自测 6

题目：

`create_openai_compatible_client` 主要做什么？

参考答案：

它根据 Settings 读取 API key、base_url 和 timeout，然后创建 OpenAI SDK client。

### 自测 7

题目：

为什么 `llm_client.py` 不直接写在 `routers/chat.py` 里？

参考答案：

为了分层清晰。

路由负责 HTTP 接口，service 负责外部服务调用准备，配置由 config 负责。

### 自测 8

题目：

运行 smoke test 时，哪个参数会真实调用模型？

参考答案：

`--call`。

不加 `--call` 时只检查配置。

### 自测 9

题目：

当前自动化测试用什么方式避免真实网络请求？

参考答案：

使用 `FakeOpenAI` 和 `monkeypatch` 替换真实 SDK client，只验证参数，不发网络请求。

### 自测 10

题目：

本节之后下一节学什么？

参考答案：

下一节学习 messages 是什么，重点理解 `system`、`user`、`assistant` 三种角色。

## 31. 本节小结

这一节完成了：

```text
理解 SDK
理解 SDK 和 HTTP API 的关系
理解 OpenAI-compatible API
理解 base_url、model、api_key
安装 openai Python SDK
新增 LLM_* 通用配置
新增 OpenAI-compatible client 初始化
新增不默认调用模型的 smoke test 脚本
补充自动化测试
明确本节先用 Chat Completions 的原因
```

现在项目还没有把真实模型接入 `/chat`。

这是刻意的。

学习顺序是：

```text
先会配置
再会 SDK
再会 messages
再接真实 /chat
```

下一节学习：

```text
messages 是什么：system / user / assistant
```

## 32. 参考资料

- [OpenAI 官方文档：Python API library](https://developers.openai.com/api/reference/python)
- [OpenAI 官方文档：SDKs and CLI](https://developers.openai.com/api/docs/libraries)
- [OpenAI 官方文档：Text generation](https://developers.openai.com/api/docs/guides/text)
- [阿里云百炼官方文档：OpenAI Chat接口兼容](https://help.aliyun.com/zh/model-studio/compatibility-of-openai-with-dashscope)
- [阿里云百炼官方文档：文本生成模型API参考](https://help.aliyun.com/zh/model-studio/qwen-api-reference/)
