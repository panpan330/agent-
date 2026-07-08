# 阶段 2 第 1 节：什么是 LLM API

## 1. 这一节学什么

阶段 2 开始进入：

```text
LLM API 基础调用
```

LLM 是：

```text
Large Language Model
大语言模型
```

API 是：

```text
Application Programming Interface
应用程序编程接口
```

所以 `LLM API` 可以先理解成：

```text
程序通过 HTTP 请求调用大语言模型的接口。
```

阶段 1 我们已经搭好了 FastAPI 服务基础：

```text
前端或客户端 -> FastAPI /chat -> mock 回复
```

阶段 2 要逐步变成：

```text
前端或客户端 -> FastAPI /chat -> 调用真实大模型 API -> 返回模型回复
```

这一节先不急着写真实调用代码。

先把这些问题讲清楚：

```text
什么是大模型
什么是 LLM API
LLM API 和网页 ChatGPT 有什么区别
LLM API 和本地模型有什么区别
一次 LLM API 请求大概发生什么
为什么需要 API key
为什么阶段 2 先从 OpenAI API 学
为什么当前推荐先理解 Responses API
```

## 2. 什么是大语言模型

大语言模型可以先理解成：

```text
一种根据输入文本，生成输出文本的 AI 模型。
```

你给它输入：

```text
请用一句话解释 FastAPI 是什么
```

它输出：

```text
FastAPI 是一个用于快速构建 Python Web API 的框架。
```

这就是最常见的文本生成能力。

但大模型不只会聊天。

它还可以做：

```text
总结
翻译
分类
改写
问答
代码生成
结构化信息提取
JSON 输出
工具调用规划
```

阶段 2 先从最基础的文本调用开始。

## 3. LLM 不是数据库

这一点很重要。

数据库更像：

```text
你查什么，它从确定的数据里找什么。
```

例如：

```sql
select * from users where id = 1;
```

结果来自数据库里真实存储的数据。

LLM 更像：

```text
根据输入、模型训练中学到的语言规律、上下文和指令生成一个回答。
```

它不是简单查表。

所以大模型可能：

```text
答得很自然
能总结和推理
也可能编造不存在的信息
也可能没有你公司内部数据
也可能因为提示词不清楚而答偏
```

后面学 RAG，就是为了解决“模型不知道你私有资料”的问题。

## 4. 什么是 API

API 你在阶段 1 已经接触过。

简单说：

```text
API 是程序之间约定好的调用方式。
```

比如我们现在的 FastAPI 项目有：

```text
POST /chat
```

客户端按约定传：

```json
{
  "message": "你好"
}
```

服务端按约定返回：

```json
{
  "reply": "你刚才说的是：你好"
}
```

这就是 API。

LLM API 也是类似。

只不过服务端不是我们自己的 `/chat` 逻辑，而是大模型服务。

## 5. 什么是 LLM API

LLM API 可以理解成：

```text
由模型服务商提供的 HTTP 接口，你的程序把 prompt/messages 发过去，服务商返回模型生成结果。
```

一次最简化的调用流程：

```text
你的 Python 程序
-> 发送 HTTP 请求
-> OpenAI API 服务
-> 选择某个模型
-> 模型生成结果
-> API 返回 JSON 响应
-> 你的 Python 程序解析结果
```

这和阶段 1 的 FastAPI 非常有关。

阶段 1 是你写服务端。

阶段 2 是你的服务端再去调用另一个服务端。

也就是：

```text
客户端 -> 你的 FastAPI 服务 -> OpenAI API 服务 -> 模型
```

## 6. LLM API 和网页 ChatGPT 的区别

网页 ChatGPT 是给人直接使用的产品。

你打开网页：

```text
https://chatgpt.com
```

然后在输入框里提问。

这种方式适合：

```text
人直接聊天
写作
学习
临时问答
手动操作
```

LLM API 是给程序调用的接口。

你的程序通过代码发请求。

这种方式适合：

```text
把 AI 接进业务系统
做客服机器人
做知识库问答
做工单 Agent
批量处理文本
集成到 Java 或 Python 后端
```

一句话区别：

```text
ChatGPT 网页是人用的。
LLM API 是程序用的。
```

## 7. LLM API 和本地模型的区别

本地模型是：

```text
模型文件和推理程序运行在你自己的电脑或服务器上。
```

例如以后你可能听到：

```text
Ollama
LM Studio
vLLM
llama.cpp
```

本地模型的特点：

```text
数据不一定要发给外部 API
可以离线或内网部署
需要自己准备机器资源
性能、显存、并发都要自己处理
模型能力取决于你部署的模型
```

LLM API 的特点：

```text
不需要自己部署模型
通过 HTTP 调用
按量计费
需要 API key
依赖网络和服务商
模型升级和能力由服务商提供
```

我们当前阶段先学 LLM API。

原因是：

```text
更容易开始
更接近真实 AI 应用工程
更适合先学 prompt、消息、流式输出、结构化输出、错误处理
```

本地模型后面可以单独作为扩展学习。

## 8. LLM API 请求里通常有什么

不同服务商、不同 API 细节不完全一样。

但概念上通常有这些：

```text
API key
model
input 或 messages
instructions 或 system prompt
temperature 等生成参数
timeout
stream 是否流式
```

先不用全记住。

阶段 2 会一项一项讲。

## 9. model 是什么

`model` 表示你要调用哪个模型。

可以先理解成：

```text
你选择哪一个大脑来回答问题。
```

不同模型可能有不同特点：

```text
能力不同
速度不同
成本不同
上下文长度不同
适合任务不同
```

例如有的模型适合复杂推理，有的模型适合低成本快速回复。

阶段 2 第一次真实调用时，我们会基于当前官方文档再决定用哪个模型。

这里先不要死记某个模型名。

因为模型会更新。

## 10. input 是什么

`input` 是你发给模型的内容。

最简单形式就是一段字符串：

```text
请用一句话解释 FastAPI 是什么
```

模型根据 input 生成 output。

在聊天类任务里，input 可能会更复杂。

比如：

```text
用户这一轮说了什么
之前几轮对话是什么
系统希望模型遵守什么规则
```

## 11. instructions 是什么

OpenAI 当前文本生成文档里，Responses API 支持 `instructions` 参数。

你可以先把它理解成：

```text
给模型的高层行为要求。
```

例如：

```text
你是一个耐心的 Python 教师，回答要适合零基础学习者。
```

用户输入是：

```text
解释一下列表推导式
```

模型回答时就会参考这个身份和要求。

阶段 2 后面会专门讲 prompt 和 instructions。

## 12. messages 是什么

很多聊天模型 API 会用 `messages` 表达对话。

一个 message 通常有：

```text
role
content
```

常见 role：

```text
system
user
assistant
```

大致意思：

```text
system     系统级要求
user       用户说的话
assistant  模型之前回复的话
```

虽然 OpenAI 当前推荐的 Responses API 可以直接使用 `input` 和 `instructions`，但理解 message roles 仍然很重要。

因为很多资料、框架、LangChain、历史 API、其他模型服务都会用 messages 的概念。

## 13. output 是什么

`output` 是模型返回的结果。

最常见是文本：

```text
FastAPI 是一个用于构建高性能 Python API 的 Web 框架。
```

也可以是结构化结果：

```json
{
  "intent": "explain_concept",
  "topic": "FastAPI"
}
```

阶段 2 后面会讲：

```text
普通文本输出
流式输出
结构化输出
```

## 14. API key 是什么

API key 可以理解成：

```text
调用 API 的身份凭证。
```

它告诉服务商：

```text
是谁在调用
有没有权限
调用量算到哪个账号或项目上
```

API key 很敏感。

不能：

```text
写死在代码里
上传到 GitHub
发到聊天记录里
写进截图里
```

阶段 1 已经提前准备了：

```text
OPENAI_API_KEY
```

后面真实调用时，会从 `.env` 读取。

## 15. 为什么先不急着填 API key

这一节不需要你立刻填真实 API key。

原因是：

```text
先理解 LLM API 是什么
下一节专门讲 API key 和安全配置
再决定怎么在本机配置
```

API key 属于敏感信息。

必须单独讲清楚。

## 16. 为什么阶段 2 使用 OpenAI API 作为主线

原因有三个：

```text
官方文档完整
SDK 成熟
后面能自然衔接 streaming、structured output、tool calling、Agents、RAG
```

这不代表以后只能用 OpenAI。

真正学会的是：

```text
LLM API 调用的通用工程思路。
```

以后换其他模型服务，也会遇到类似问题：

```text
key 怎么放
模型怎么选
请求怎么组装
错误怎么处理
超时怎么处理
流式怎么返回
结果怎么结构化
日志怎么记录
成本怎么控制
```

## 17. 当前官方文档里的重要方向

OpenAI 官方快速开始文档说明，OpenAI API 可以通过简单接口访问模型，用于文本生成、自然语言处理、计算机视觉等，并要求先创建 API key 再运行第一次 API 调用。

OpenAI 文本生成文档说明，可以用大语言模型根据 prompt 生成文本，并且当前直接模型请求推荐使用 Responses API。

这对我们阶段 2 很重要。

所以阶段 2 主线会是：

```text
OpenAI Python SDK
Responses API
FastAPI /chat 集成
```

旧的 Chat Completions API 也会解释概念，但不作为主线优先实现。

## 18. Responses API 是什么

你现在先把 Responses API 理解成：

```text
OpenAI 当前用于直接向模型发请求并获得响应的 API。
```

它可以用于：

```text
文本生成
结构化输出
工具调用
多模态输入
流式输出
```

阶段 2 不会一口气讲完全部能力。

我们会按顺序来：

```text
普通文本调用
错误和超时
日志
streaming
结构化输出
```

## 19. 一次 LLM API 调用的大流程

以 `/chat` 为例，后面会变成：

```text
1. 用户请求 POST /chat
2. FastAPI 用 ChatRequest 校验请求
3. 读取 OPENAI_API_KEY
4. 创建 OpenAI client
5. 组装 model、instructions、input
6. 调用 OpenAI Responses API
7. 得到模型输出
8. 转换成 ChatResponse
9. 返回给用户
10. 日志记录模型名、耗时、trace_id
```

这就是阶段 2 的主线。

## 20. 为什么还需要我们自己的 FastAPI 服务

你可能会问：

```text
既然可以直接调 OpenAI API，为什么还要我们自己的 FastAPI？
```

原因是业务系统不能直接把一切交给前端。

我们的 FastAPI 服务负责：

```text
隐藏 API key
统一请求和响应格式
做参数校验
做日志和 trace_id
做异常处理
做超时和重试
接入 Java 业务系统
接入 RAG 检索
接入权限控制
接入 Agent 流程
```

前端或 Java 服务只需要调用我们自己的稳定接口：

```text
POST /chat
```

不用直接接触大模型服务商的复杂细节。

## 21. LLM API 为什么需要工程化

调用一次模型很简单。

做一个稳定的 AI 服务不简单。

因为真实环境会遇到：

```text
API key 配错
网络超时
服务端限流
模型返回慢
模型输出格式不稳定
用户输入太长
token 成本过高
多轮对话上下文太长
流式输出中断
错误日志查不到
测试不能依赖真实模型
```

阶段 2 就是开始解决这些问题。

## 22. 阶段 2 的 18 项学习清单

阶段 2 我们按 18 项学：

```text
1. 什么是 LLM API
2. API key 和 .env 安全配置
3. token、上下文窗口、费用基础
4. OpenAI SDK 基础调用方式
5. messages 是什么：system / user / assistant
6. prompt 基础：怎么写清楚任务
7. 第一次真实 /chat 调用
8. 多轮对话基础：历史消息怎么传
9. 超时 timeout
10. 重试 retry 和限流 rate limit 基础
11. 模型调用错误处理
12. 模型调用日志：模型名、耗时、trace_id、token
13. streaming 流式输出是什么
14. FastAPI StreamingResponse 实现 /stream-chat
15. 结构化输出是什么
16. Pydantic 约束结构化输出
17. 测试模型调用：mock/fake LLM client
18. 阶段 2 项目整理
```

这样学完后，你不是只会“调通 API”。

你会理解：

```text
怎么把大模型 API 放进一个后端服务里。
```

## 23. 本节练习

### 练习 1

题目：

用自己的话解释什么是 LLM API。

参考答案：

LLM API 是程序调用大语言模型的接口。

程序通过 HTTP 请求把输入内容、模型名和参数发给模型服务，模型服务生成结果后返回 JSON 响应。

### 练习 2

题目：

网页 ChatGPT 和 LLM API 的区别是什么？

参考答案：

网页 ChatGPT 是给人直接使用的产品，人通过网页输入问题并查看回答。

LLM API 是给程序调用的接口，用来把大模型能力接入业务系统、后端服务、批处理脚本或应用程序。

### 练习 3

题目：

LLM API 和本地模型有什么区别？

参考答案：

LLM API 不需要自己部署模型，通过网络调用服务商接口，通常按量计费，需要 API key。

本地模型运行在自己的电脑或服务器上，需要自己准备模型文件、推理程序和硬件资源。

### 练习 4

题目：

为什么不能把 API key 写死在代码里？

参考答案：

API key 是调用 API 的身份凭证。

如果写死在代码里，可能被上传到 GitHub 或被别人看到，导致账号被滥用和费用损失。

所以应该放在 `.env` 或环境变量里。

### 练习 5

题目：

为什么我们不让前端直接调用 OpenAI API？

参考答案：

因为前端代码会暴露给用户。

如果前端直接调用 OpenAI API，就可能泄露 API key。

而且后端还需要统一请求格式、日志、trace_id、异常处理、权限控制和业务逻辑。

### 练习 6

题目：

阶段 2 为什么要先学概念，再写真实调用代码？

参考答案：

因为真实模型调用涉及 API key、模型选择、请求格式、费用、错误处理和安全问题。

先理解概念，可以避免只是复制代码，不知道每个参数和流程的意义。

## 24. 本节自测

### 自测 1

题目：

LLM 的全称是什么？

参考答案：

LLM 的全称是：

```text
Large Language Model
```

中文是大语言模型。

### 自测 2

题目：

API 的全称是什么？

参考答案：

API 的全称是：

```text
Application Programming Interface
```

中文是应用程序编程接口。

### 自测 3

题目：

LLM API 的调用对象是谁？

参考答案：

调用对象是大语言模型服务。

程序把输入、模型名和参数发给模型服务，模型服务返回生成结果。

### 自测 4

题目：

`model` 参数表示什么？

参考答案：

`model` 表示要调用哪个大模型。

不同模型的能力、速度、成本和适用任务可能不同。

### 自测 5

题目：

`input` 或 `messages` 表示什么？

参考答案：

它们表示发给模型的输入内容。

`input` 可以是一段文本，`messages` 通常表示带角色的对话历史。

### 自测 6

题目：

API key 的作用是什么？

参考答案：

API key 是身份凭证，用来证明调用者有权限访问 API，并把调用量关联到对应账号或项目。

### 自测 7

题目：

为什么 LLM 不是数据库？

参考答案：

数据库是从确定的数据里查询结果。

LLM 是根据输入、上下文和模型能力生成回答，可能总结、推理，也可能编造或答错。

### 自测 8

题目：

阶段 2 主线会优先学习 OpenAI 的哪个 API 方向？

参考答案：

阶段 2 会优先学习 OpenAI SDK 和 Responses API 方向。

### 自测 9

题目：

为什么我们自己的 FastAPI 服务仍然重要？

参考答案：

它负责隐藏 API key、统一请求和响应、参数校验、日志、trace_id、异常处理、权限控制、业务集成和后续 RAG/Agent 扩展。

### 自测 10

题目：

阶段 2 学完后的目标是什么？

参考答案：

目标是能把当前 mock `/chat` 逐步替换成真实大模型调用，并具备 API key 安全、超时、错误处理、日志、流式输出、结构化输出和可测试性基础。

## 25. 本节小结

这一节完成了阶段 2 的概念开场：

```text
理解大语言模型
理解 LLM API
区分网页 ChatGPT、LLM API、本地模型
理解 model、input、instructions、messages、output
理解 API key 的基本意义
理解为什么要通过自己的 FastAPI 服务调用模型
明确阶段 2 的 18 项学习清单
```

下一节学习：

```text
API key 和 .env 安全配置
```

下一节会重点讲：

```text
OpenAI API key 是什么
怎么创建和保存
为什么不能上传
怎么在 Windows 本机配置
怎么让项目从 .env 读取
怎么确认没有泄露 key
```

## 26. 参考资料

- [OpenAI 官方文档：Developer quickstart](https://platform.openai.com/docs/quickstart)
- [OpenAI 官方文档：Text generation](https://platform.openai.com/docs/guides/text)
- [OpenAI 官方文档：Models](https://platform.openai.com/docs/models)
- [OpenAI API Reference：Create a model response](https://platform.openai.com/docs/api-reference/responses/create)
