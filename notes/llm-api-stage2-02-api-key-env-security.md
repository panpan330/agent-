# 阶段 2 第 2 节：API key 和 `.env` 安全配置

## 1. 这一节学什么

上一节我们知道了：

```text
LLM API 是程序调用大语言模型服务的接口。
```

这一节学习调用真实模型前必须先弄明白的安全基础：

```text
API key 是什么
为什么 API key 不能泄露
什么是环境变量
什么是 .env
什么是 .env.example
为什么 .env 不能上传 GitHub
Windows 本机应该怎么放 key
项目里怎么读取 OPENAI_API_KEY
怎么判断 key 是否配置了
如果 key 泄露了怎么办
```

这一节仍然不需要把真实 API key 发给任何人，也不要发给我。

我们只把项目改成：

```text
能读取 OPENAI_API_KEY
能判断 OPENAI_API_KEY 是否真的配置
能测试空 key 不算配置成功
```

## 2. API key 是什么

API key 可以先理解成：

```text
调用 API 的密码。
```

更准确一点：

```text
API key 是服务商发给你的身份凭证。
```

程序调用 OpenAI API 时，服务端需要知道：

```text
你是谁
你有没有权限调用
这次调用算到哪个账号或项目上
是否超过了额度或限制
费用应该记到哪里
```

所以 API key 不是普通配置项。

它属于：

```text
secret
密钥
敏感信息
```

## 3. API key 和账号密码有什么相似点

你可以把 API key 想成一个“程序专用密码”。

普通账号密码通常是：

```text
人登录网页或 App 使用
```

API key 通常是：

```text
程序调用接口时使用
```

二者共同点是：

```text
都能代表身份
泄露后都可能被别人滥用
都不应该公开
都应该在泄露后立即作废或更换
```

区别是：

```text
账号密码给人用
API key 给程序用
```

## 4. 为什么 API key 泄露很危险

如果别人拿到了你的 API key，可能会：

```text
用你的账号调用模型
消耗你的额度
产生费用
冒充你的项目发请求
导致你的服务异常
```

如果 key 被上传到公开 GitHub 仓库，风险更高。

因为公开仓库会被很多自动化工具扫描。

也就是说：

```text
不是只有人看到才危险。
机器扫描到也危险。
```

所以真实 key 不能出现在：

```text
代码文件
测试文件
README
学习笔记
GitHub commit
前端代码
浏览器页面
截图
聊天记录
日志文件
```

## 5. 官方文档怎么要求

OpenAI 官方 API Reference 的 Authentication 部分说明：

```text
API key 是 secret。
不要分享给别人。
不要暴露在浏览器或 App 这类客户端代码里。
应该在服务端通过环境变量或密钥管理服务读取。
```

OpenAI Developer quickstart 说明，创建 API key 后，可以把它导出为环境变量，OpenAI SDK 会自动读取系统环境里的 `OPENAI_API_KEY`。

OpenAI Python API library 文档也说明，推荐用 `python-dotenv` 把 `OPENAI_API_KEY` 放在 `.env` 文件里，避免把 key 存进源代码管理。

OpenAI Production best practices 也强调，不要把 API key 暴露在代码或公开仓库里，应该通过环境变量或 secret management service 提供给应用。

我们当前项目就是按这个原则做：

```text
真实 key 只放本机 .env
.env 不提交 GitHub
.env.example 只放示例空值
代码只读取 OPENAI_API_KEY
日志和响应都不输出 key
```

## 6. 什么是环境变量

环境变量可以理解成：

```text
操作系统或运行环境提供给程序的一组配置。
```

比如你的程序运行时，可以从环境变量里读：

```text
APP_NAME
LOG_LEVEL
OPENAI_API_KEY
```

环境变量的好处是：

```text
代码不用写死配置
同一份代码可以在不同环境使用不同配置
敏感信息可以和代码分开
部署时可以由服务器提供密钥
```

一个常见原则是：

```text
代码负责逻辑。
环境变量负责环境差异和敏感配置。
```

## 7. 什么是 `.env`

`.env` 是一个普通文本文件。

它通常放在项目根目录，用来保存本地开发配置。

格式一般是：

```env
APP_NAME="AI Service"
LOG_LEVEL="INFO"
OPENAI_API_KEY="your_api_key_here"
```

注意：

```text
.env 不是 Python 专属。
.env 是很多后端项目都会用的本地配置文件约定。
```

我们的 FastAPI 项目通过 Pydantic Settings 读取 `.env`。

项目路径是：

```text
projects/ai-service/.env
```

## 8. 什么是 `.env.example`

`.env.example` 是示例配置文件。

它的作用是告诉别人：

```text
这个项目需要哪些配置项
每个配置项大概长什么样
怎么复制出自己的 .env
```

`.env.example` 可以上传 GitHub。

但它不能包含真实密钥。

所以我们的 `.env.example` 里是：

```env
OPENAI_API_KEY=""
```

这表示：

```text
项目需要这个配置项。
但真实值你要自己在本机 .env 里填。
```

## 9. `.env` 和 `.env.example` 的区别

| 文件 | 作用 | 能不能上传 GitHub | 是否包含真实 key |
| --- | --- | --- | --- |
| `.env` | 本机真实配置 | 不能 | 可以包含真实 key |
| `.env.example` | 示例配置模板 | 可以 | 不能包含真实 key |

一句话记忆：

```text
.env 是我的本机秘密。
.env.example 是给别人看的模板。
```

## 10. 为什么 `.env` 不能上传 GitHub

因为 `.env` 可能包含：

```text
API key
数据库密码
Redis 密码
第三方服务 token
云服务密钥
管理员账号
内部地址
```

只要这些被上传到公开仓库，就可能被滥用。

即使你后来删除文件，也不代表完全安全。

因为 Git 有历史记录。

别人可能从旧 commit 里找到已经删除的 key。

所以最好从一开始就避免提交。

## 11. `.gitignore` 是什么

`.gitignore` 是 Git 的忽略规则文件。

它告诉 Git：

```text
哪些文件不要加入版本控制。
```

当前仓库根目录已经有：

```gitignore
.env
.env.*
!.env.example
```

意思是：

```text
忽略 .env
忽略 .env.xxx
但是不要忽略 .env.example
```

这样就能做到：

```text
真实配置不上传。
示例配置可以上传。
```

## 12. 为什么不能让前端保存 API key

前端代码运行在用户浏览器里。

浏览器里的内容用户都能看到。

如果你把 API key 放进前端，例如：

```text
HTML
JavaScript
Vue
React
浏览器 localStorage
浏览器控制台
```

那么用户就可能拿到 key。

所以正确结构应该是：

```text
浏览器前端 -> 我们自己的 FastAPI 后端 -> OpenAI API
```

而不是：

```text
浏览器前端 -> OpenAI API
```

FastAPI 后端负责隐藏 key。

## 13. 为什么 Java 后端也不应该直接把 key 暴露给前端

未来你的项目可能有 Java 后端。

Java 后端可以调用 Python AI 服务。

结构可能是：

```text
前端 -> Java 后端 -> Python FastAPI AI 服务 -> OpenAI API
```

也可能是：

```text
前端 -> Python FastAPI AI 服务 -> OpenAI API
```

不管哪种结构，原则都一样：

```text
真实 API key 只在服务端。
不要给浏览器。
不要给用户。
不要写进前端包。
```

## 14. Windows 本机怎么放 API key

你现在主要在 Windows 学习。

有两种常见方式。

### 方式 1：项目 `.env`

这是当前阶段最适合你的方式。

在项目目录：

```text
D:\wendang\java+python+ai\projects\ai-service
```

复制示例文件：

```powershell
Copy-Item .env.example .env
```

然后只在本机 `.env` 里填写：

```env
OPENAI_API_KEY="your_api_key_here"
```

优点：

```text
只影响当前项目
容易理解
容易删除
配合 .gitignore 不会上传
```

缺点：

```text
每个项目都要单独配置
```

### 方式 2：Windows 用户环境变量

PowerShell 可以设置用户环境变量：

```powershell
setx OPENAI_API_KEY "your_api_key_here"
```

注意：

```text
setx 设置后，通常要重新打开终端才生效。
```

优点：

```text
所有项目都能读取同一个环境变量
```

缺点：

```text
不如项目 .env 直观
多个项目共用同一个 key，不方便隔离
```

当前学习阶段建议：

```text
先用项目 .env。
后面学部署时，再学服务器环境变量和 secret 管理。
```

## 15. 现在不要做什么

现阶段不要：

```text
把真实 key 发给我
把真实 key 截图发出来
把真实 key 写进 notes
把真实 key 写进 README
把真实 key 写进测试
把真实 key 上传 GitHub
把真实 key 放到前端
```

学习时可以用占位符：

```text
your_api_key_here
sk-test-for-local-config
```

但不要使用真实 key。

## 16. 项目里现在怎么读取 key

当前项目的配置入口是：

```text
projects/ai-service/app/core/config.py
```

核心类是：

```python
class Settings(BaseSettings):
    ...
    openai_api_key: str | None = Field(default=None, repr=False)
```

这行表示：

```text
配置项名称：openai_api_key
环境变量名称：OPENAI_API_KEY
类型：字符串或 None
默认值：None
repr=False：打印 Settings 对象时不要显示这个字段
```

`repr=False` 不是绝对安全措施。

但它能降低你调试时不小心把 key 打印出来的概率。

真正的安全措施仍然是：

```text
不要主动 print key
不要写日志
不要返回给接口调用方
不要提交 .env
```

## 17. 为什么要加 `has_openai_api_key`

`.env.example` 里有：

```env
OPENAI_API_KEY=""
```

这个值不是 `None`。

它是一个空字符串。

如果后面代码只判断：

```python
if settings.openai_api_key:
    ...
```

大多数时候也能工作。

但我们想把这个判断集中起来，避免后面到处重复写。

所以现在增加了：

```python
@property
def has_openai_api_key(self) -> bool:
    return bool(self.openai_api_key and self.openai_api_key.strip())
```

它的意思是：

```text
如果 openai_api_key 是 None -> False
如果 openai_api_key 是 "" -> False
如果 openai_api_key 是 "   " -> False
如果 openai_api_key 是 "sk-..." -> True
```

注意：

```text
它只判断“有没有非空值”。
它不验证这个 key 是不是真的有效。
```

验证 key 是否有效，需要真正调用 API。

那是后面学习的内容。

## 18. 为什么测试里可以写 `sk-test-for-local-config`

测试里出现了：

```text
sk-test-for-local-config
```

这是假的测试值。

它不是有效 API key。

测试目的只是验证：

```text
Settings 能不能从环境变量读取字符串
has_openai_api_key 能不能把非空字符串判断为 True
```

测试里不能写真实 key。

真实 key 永远不应该进入测试代码。

## 19. 本节代码改动

### 改动 1：配置类增加 key 检查属性

文件：

```text
projects/ai-service/app/core/config.py
```

新增：

```python
@property
def has_openai_api_key(self) -> bool:
    return bool(self.openai_api_key and self.openai_api_key.strip())
```

### 改动 2：配置测试补充 key 场景

文件：

```text
projects/ai-service/tests/test_config.py
```

新增测试覆盖：

```text
默认没有 OPENAI_API_KEY
环境变量里有非空 OPENAI_API_KEY
.env 文件里 OPENAI_API_KEY="" 视为没有配置
OPENAI_API_KEY="   " 视为没有配置
```

### 改动 3：项目 README 补充安全说明

文件：

```text
projects/ai-service/README.md
```

补充说明：

```text
OPENAI_API_KEY 属于敏感信息
真实值只放本机 .env 或系统环境变量
不要写进代码、README、测试、截图或聊天记录
```

## 20. 以后真实调用时会怎么用

后面实现真实 `/chat` 时，会类似这样：

```python
settings = get_settings()

if not settings.has_openai_api_key:
    raise AppException(
        code="OPENAI_API_KEY_MISSING",
        message="OpenAI API key is not configured.",
        status_code=500,
    )
```

意思是：

```text
调用模型前先检查 key。
如果没有 key，就返回明确错误。
不要等 SDK 报一个难懂的错误。
```

这就是工程化思维：

```text
提前检查
错误可解释
问题可定位
不要泄露密钥
```

## 21. 如何检查 `.env` 没有被 Git 跟踪

在仓库根目录可以运行：

```powershell
git status --short
```

如果 `.env` 被正确忽略，一般不会看到：

```text
?? projects/ai-service/.env
```

如果你看到 `.env` 出现在 git status 里，就要停止提交，先检查 `.gitignore`。

也可以检查忽略规则：

```powershell
git check-ignore -v projects/ai-service/.env
```

如果输出了 `.gitignore` 里的规则，说明它被忽略了。

## 22. 如果 API key 已经泄露怎么办

如果真实 API key 被发到聊天记录、截图、GitHub、日志或公开文件里，不要抱侥幸心理。

按这个顺序处理：

```text
1. 立刻去 OpenAI dashboard 删除或 revoke 这个 key
2. 创建一个新的 key
3. 更新本机 .env 或服务器环境变量
4. 检查 GitHub、日志、截图、文档里是否还有残留
5. 如果已经进了 Git 历史记录，把这个 key 当作永久泄露处理
6. 后续只使用新 key
```

重点：

```text
泄露过的 key 不要继续使用。
```

## 23. API key 安全规则清单

你以后写任何 AI 项目，都可以先套这个清单：

```text
真实 key 只在服务端
真实 key 不进代码
真实 key 不进 GitHub
真实 key 不进前端
真实 key 不进日志
真实 key 不进截图
真实 key 不进聊天记录
.env 本机保存
.env.example 只放空值或示例值
.gitignore 忽略 .env
测试只用假 key
泄露后立即作废并换新
```

## 24. 本节练习

### 练习 1

题目：

用自己的话解释 API key 是什么。

参考答案：

API key 是调用 API 时使用的身份凭证，可以理解成程序专用密码。

它告诉 API 服务商是谁在调用、有没有权限、调用量算到哪个账号或项目上。

### 练习 2

题目：

为什么不能把 API key 上传到 GitHub？

参考答案：

因为 API key 泄露后，别人可能用它调用模型、消耗额度、产生费用，甚至影响项目安全。

GitHub 公开仓库还可能被自动扫描，所以真实 key 绝不能提交。

### 练习 3

题目：

`.env` 和 `.env.example` 有什么区别？

参考答案：

`.env` 是本机真实配置文件，可以保存真实 API key，不能上传 GitHub。

`.env.example` 是示例模板，用来告诉别人项目需要哪些配置项，可以上传 GitHub，但不能包含真实 key。

### 练习 4

题目：

为什么前端不能直接保存 OpenAI API key？

参考答案：

因为前端代码运行在用户浏览器里，用户可以查看代码、网络请求和本地存储。

如果 key 放在前端，就可能被用户或工具拿到。

正确做法是由服务端保存 key，前端只调用自己的后端接口。

### 练习 5

题目：

`OPENAI_API_KEY=""` 为什么不算配置成功？

参考答案：

因为它只是空字符串，没有真实密钥内容。

程序如果拿空字符串去调用 API，仍然无法通过认证。

所以项目用 `has_openai_api_key` 把空字符串和空格都判断为未配置。

### 练习 6

题目：

如果真实 API key 已经被上传到 GitHub，第一件事应该做什么？

参考答案：

第一件事是立刻去 OpenAI dashboard 删除或 revoke 这个 key。

然后创建新 key，更新本机或服务器配置，并检查仓库和日志里是否还有残留。

## 25. 本节自测

### 自测 1

题目：

API key 属于普通配置还是敏感信息？

参考答案：

属于敏感信息，也可以叫 secret。

它不能公开，不能上传 GitHub，不能写入前端。

### 自测 2

题目：

环境变量的作用是什么？

参考答案：

环境变量是运行环境提供给程序的配置。

它可以让代码和配置分离，让不同环境使用不同配置，也适合保存敏感配置的入口。

### 自测 3

题目：

`.gitignore` 里的 `.env` 表示什么？

参考答案：

表示让 Git 忽略 `.env` 文件，不把本机真实配置加入版本控制。

### 自测 4

题目：

`.gitignore` 里的 `!.env.example` 表示什么？

参考答案：

表示不要忽略 `.env.example`。

也就是说，真实 `.env` 不提交，但示例 `.env.example` 可以提交。

### 自测 5

题目：

`repr=False` 能不能保证 API key 绝对安全？

参考答案：

不能。

它只能减少打印 `Settings` 对象时显示 key 的风险。

真正的安全还需要不打印、不写日志、不返回接口、不提交 `.env`。

### 自测 6

题目：

`has_openai_api_key` 检查的是什么？

参考答案：

它检查 `openai_api_key` 是否存在非空内容。

`None`、空字符串、全空格都返回 `False`。

### 自测 7

题目：

`has_openai_api_key` 能不能验证 key 一定有效？

参考答案：

不能。

它只能判断是否配置了非空值。

key 是否有效，需要真实调用 API 后才能确认。

### 自测 8

题目：

当前学习阶段推荐把真实 key 放在哪里？

参考答案：

推荐放在当前项目的本机 `.env` 文件里：

```text
projects/ai-service/.env
```

这个文件应该被 `.gitignore` 忽略。

### 自测 9

题目：

测试代码里能不能写真实 API key？

参考答案：

不能。

测试只能使用假的占位值，例如 `sk-test-for-local-config`。

### 自测 10

题目：

为什么自己的 FastAPI 后端要负责保存 key？

参考答案：

因为后端运行在服务端，用户不能直接看到代码和环境变量。

后端可以隐藏 key，并统一处理请求校验、日志、trace_id、异常、权限和业务逻辑。

## 26. 本节小结

这一节完成了真实模型调用前最重要的安全基础：

```text
理解 API key 是程序调用 API 的身份凭证
理解 API key 泄露的风险
理解环境变量、.env、.env.example
理解为什么 .env 不能上传 GitHub
理解为什么前端不能保存 key
理解当前项目怎么读取 OPENAI_API_KEY
新增 has_openai_api_key 判断
补充配置测试，确保空 key 不算配置成功
```

下一节学习：

```text
token、上下文窗口、费用基础
```

下一节会重点讲：

```text
什么是 token
为什么模型不是按字数理解文本
什么是上下文窗口
输入和输出为什么都会影响费用
为什么要限制用户输入长度
为什么日志里后面要记录 token 使用量
```

## 27. 参考资料

- [OpenAI 官方文档：Developer quickstart](https://platform.openai.com/docs/quickstart)
- [OpenAI API Reference：Authentication](https://developers.openai.com/api/reference/overview#authentication)
- [OpenAI Python API library](https://developers.openai.com/api/reference/python)
- [OpenAI 官方文档：Production best practices](https://platform.openai.com/docs/guides/production-best-practices)
