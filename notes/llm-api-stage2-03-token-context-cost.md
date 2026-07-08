# 阶段 2 第 3 节：token、上下文窗口、费用基础

## 1. 这一节学什么

这一节学习大模型 API 里非常核心的三个概念：

```text
token
上下文窗口
费用
```

它们决定了：

```text
一次请求能发多长
模型最多能回复多长
为什么长对话会越来越贵
为什么 RAG 不能把所有文档都塞给模型
为什么后面要记录 input_tokens、output_tokens、total_tokens
为什么要限制用户输入长度和 max_output_tokens
```

这一节不要求你背价格。

价格会变。

我们要掌握的是：

```text
计费逻辑
长度限制逻辑
工程控制思路
```

## 2. 先用一个生活例子理解 token

你平时读一句话，是按字读、按词读、按语义读。

例如：

```text
我正在学习 FastAPI
```

人可能会理解成：

```text
我 / 正在 / 学习 / FastAPI
```

模型不直接按“中文一个字”或“英文一个单词”工作。

模型会先把文本切成更小的片段。

这些片段就叫：

```text
token
```

可以先粗略理解成：

```text
token 是模型处理文本时使用的基本小块。
```

## 3. token 不是字，也不是单词

这是最容易误解的点。

token 不是：

```text
一个中文汉字
一个英文单词
一个标点
一个字符串
```

token 是 tokenizer 切出来的片段。

英文里，一个常见短词可能是一个 token。

一个长词可能被拆成多个 token。

OpenAI 官方 Key concepts 文档举过类似例子：

```text
tokenization
```

可能会被拆成类似：

```text
token
ization
```

也就是说：

```text
token 的切分方式由模型使用的 tokenizer 决定。
```

## 4. 为什么模型不直接按字处理

如果模型按每个字符处理，会有问题：

```text
英文单词会被拆得太碎
中文、英文、数字、代码混在一起时不好统一处理
常见词和常见片段不能复用
输入序列会变长
计算成本会上升
```

tokenizer 的作用是：

```text
把文本切成模型更容易处理的片段。
```

常见片段可以作为一个 token。

不常见或很长的内容会被拆成多个 token。

## 5. 一个粗略估算规则

OpenAI 官方 Key concepts 文档给了一个英文粗略估算：

```text
1 token 约等于 4 个英文字符，约等于 0.75 个英文单词。
```

注意三个关键词：

```text
粗略
英文
估算
```

这不是精确规则。

中文、代码、JSON、标点、空格、emoji 都可能让实际 token 数不同。

所以你现在只需要先记住：

```text
token 数和文本长度相关，但不等于字数。
```

## 6. 怎么精确知道 token 数

有三种方式：

```text
1. 使用官方 tokenizer 工具预估
2. 使用 tokenizer 库在本地计算
3. 看 API 响应里的 usage 字段
```

当前阶段最重要的是第 3 个：

```text
真实调用以后，看 API 返回的 usage。
```

因为真实请求里不仅有用户输入。

还可能有：

```text
system/developer instructions
历史消息
RAG 检索出来的文档片段
工具定义
结构化输出 schema
模型内部 reasoning tokens
```

这些都可能影响 token 使用量。

## 7. 输入 token 是什么

输入 token 指你发给模型的内容占用的 token。

包括：

```text
用户问题
系统指令
开发者指令
历史对话
RAG 文档片段
工具定义
格式要求
```

例如：

```text
你是一个耐心的 Python 教师。
请解释什么是列表。
```

这两句话都属于输入内容。

它们都会占用输入 token。

## 8. 输出 token 是什么

输出 token 指模型生成的内容占用的 token。

例如模型回复：

```text
列表是 Python 中用于保存一组有序数据的容器。
```

这段回答就会消耗输出 token。

输出越长，输出 token 越多。

所以如果你让模型：

```text
写一篇 3000 字长文
```

费用、延迟和失败风险都会上升。

## 9. 总 token 是什么

总 token 通常可以理解成：

```text
输入 token + 输出 token
```

很多 API 响应会提供类似：

```json
{
  "usage": {
    "input_tokens": 75,
    "output_tokens": 1186,
    "total_tokens": 1261
  }
}
```

不同 API 或 SDK 字段名可能不完全相同。

但核心意思都是：

```text
这次请求到底用了多少 token。
```

## 10. prompt tokens 和 completion tokens

你还会在一些资料里看到：

```text
prompt_tokens
completion_tokens
```

可以先这样理解：

```text
prompt_tokens      输入部分使用的 token
completion_tokens  模型生成部分使用的 token
```

在 Responses API 的新文档里，更常见的是：

```text
input_tokens
output_tokens
total_tokens
```

你不用纠结命名。

重点是理解：

```text
输入会计入 token。
输出也会计入 token。
```

## 11. cached input tokens 是什么

官方 pricing 页面里会看到：

```text
input
cached input
output
```

`cached input` 可以先理解成：

```text
模型服务对重复的输入前缀做了缓存后，部分输入 token 可能按缓存输入价格计算。
```

这在后面生产优化里有用。

比如很多请求都包含同一段系统提示词、工具定义、规则说明。

如果这些内容能被缓存，成本和延迟可能下降。

当前阶段你只需要知道：

```text
普通输入 token 和 cached input token 在计费上可能不同。
```

不要现在就深挖缓存策略。

后面做成本优化时再学。

## 12. reasoning tokens 是什么

一些推理模型会有：

```text
reasoning tokens
```

可以先理解成：

```text
模型内部思考过程占用的 token。
```

这些 token 通常不会完整展示给用户。

但官方 reasoning 文档说明，reasoning tokens 仍然会占用上下文空间，也会按输出 token 相关规则计费。

这意味着：

```text
即使你看到的最终答案不长，模型内部推理也可能消耗 token。
```

当前你先知道这个概念即可。

后面真正选择推理模型时，会再讲：

```text
reasoning effort
推理强度
速度
成本
质量
```

## 13. 什么是上下文窗口

上下文窗口可以理解成：

```text
模型一次请求最多能“看见”和“生成”的 token 总空间。
```

它不是记忆力。

它更像一次考试时给模型的一张纸：

```text
这张纸能放输入，也要预留输出空间。
纸的容量有限。
```

输入太多，就没有足够空间给输出。

如果输入和输出合起来超过模型限制，请求可能失败，或者被截断。

## 14. 上下文窗口包含什么

对文本生成模型来说，上下文窗口通常要容纳：

```text
输入 token
输出 token
某些模型的 reasoning tokens
```

也就是：

```text
用户问题
系统提示词
历史对话
检索文档
工具描述
模型回复
模型内部推理空间
```

这就是为什么不能无限塞内容。

## 15. 一个简单的上下文预算例子

假设某个模型上下文窗口是：

```text
10000 tokens
```

你这次请求输入已经用了：

```text
8500 tokens
```

如果你还希望模型最多输出：

```text
2000 tokens
```

总共就是：

```text
8500 + 2000 = 10500 tokens
```

这就超过了 10000。

所以你需要做选择：

```text
减少输入
减少输出上限
换更大上下文的模型
对历史消息做摘要
减少 RAG 文档数量
```

## 16. 为什么多轮对话不能一直塞所有历史

多轮对话看起来像 ChatGPT 一直记得你说过什么。

但从 API 工程角度看，很多时候我们需要把历史消息重新传给模型。

假设每一轮对话都加入：

```text
用户问题
模型回答
```

轮数越多，历史越长。

如果永远把所有历史都塞进去，会出现：

```text
越来越慢
越来越贵
超过上下文窗口
模型注意力被无关历史分散
```

所以后面学多轮对话时，要学：

```text
保留最近几轮
摘要旧历史
只保留关键事实
按任务选择相关历史
```

## 17. 为什么 RAG 不能塞全部文档

RAG 是企业知识库问答的核心能力。

它大概流程是：

```text
用户提问
检索相关文档片段
把文档片段和问题一起发给模型
模型基于资料回答
```

问题是：

```text
公司文档可能非常多。
```

不能把所有文档都发给模型。

原因：

```text
超过上下文窗口
成本太高
延迟太高
无关资料会干扰模型
```

所以 RAG 后面要学：

```text
chunk 切分
top_k 检索
score_threshold
rerank
引用来源
```

这些都是为了控制上下文。

## 18. 什么是 max_output_tokens

`max_output_tokens` 是一个常见参数。

它表示：

```text
限制模型最多生成多少输出 token。
```

它的作用是：

```text
控制成本
控制响应长度
控制延迟
避免模型无限写下去
给上下文窗口预留边界
```

比如你只需要一句话分类结果，就没必要允许模型输出 4000 tokens。

可以限制得很小。

## 19. max_output_tokens 不是“保证输出这么多”

这一点也很重要。

`max_output_tokens=1000` 的意思不是：

```text
模型一定输出 1000 tokens。
```

它的意思是：

```text
模型最多输出 1000 tokens。
```

模型可以提前结束。

例如它只输出 80 tokens 就完成任务。

## 20. 为什么输出限制太小也会出问题

如果 `max_output_tokens` 设置太小，模型可能还没回答完就被截断。

推理模型还可能先消耗 reasoning tokens，导致没有足够空间输出可见答案。

官方 reasoning 文档说明，如果生成 token 达到上下文窗口限制或 `max_output_tokens`，响应可能变成 incomplete。

所以设置输出上限时要结合任务：

```text
分类：可以很小
一句话解释：较小
普通问答：中等
长文总结：更大
复杂推理：要给推理和输出留空间
```

## 21. 什么是费用

大模型 API 的费用通常和 token 数有关。

可以先理解成：

```text
用得越多，花得越多。
```

更具体：

```text
输入 token 要计费
输出 token 要计费
不同模型单价不同
cached input 可能有不同价格
使用某些工具还可能有额外费用
```

官方 Pricing 页面会列出不同模型的价格。

价格会随时间变化。

所以不要在学习笔记里死记某个价格。

## 22. 费用计算公式

概念上可以这样算：

```text
输入费用 = 输入 token 数 / 计价单位 * 输入单价
输出费用 = 输出 token 数 / 计价单位 * 输出单价
总费用 = 输入费用 + 输出费用 + 可能的工具费用
```

如果价格按每 1M tokens 展示，就可以理解成：

```text
输入费用 = input_tokens / 1_000_000 * input_price_per_1m
输出费用 = output_tokens / 1_000_000 * output_price_per_1m
```

当前你不用手算真实价格。

你要理解：

```text
input_tokens 和 output_tokens 都会影响成本。
```

## 23. 为什么输出通常更贵

很多模型的 pricing 页面会把：

```text
input
output
cached input
```

分开列。

输出 token 往往比输入 token 更贵。

原因可以粗略理解成：

```text
模型生成输出需要一步一步预测下一个 token。
生成越长，计算越多。
```

所以工程上经常要控制：

```text
不要让模型废话太多
不要无意义要求长篇大论
用明确格式约束输出
必要时设置 max_output_tokens
```

## 24. token 和速度的关系

token 数也影响速度。

一般来说：

```text
输入越长，模型读入和处理越慢。
输出越长，生成越慢。
推理越复杂，可能越慢。
```

所以成本优化和性能优化经常是同一件事：

```text
减少无用输入
减少无用输出
选择合适模型
缓存可复用内容
```

## 25. token 和日志有什么关系

后面真实调用模型时，我们不应该只记录：

```text
请求成功了
请求失败了
```

还应该记录：

```text
model
input_tokens
output_tokens
total_tokens
latency_ms
trace_id
```

这样你才能回答：

```text
为什么这个接口突然变贵了
为什么这个用户请求很慢
哪个模型消耗最多
哪类问题最耗 token
RAG 检索出来的内容是不是太长
```

这就是工程化。

## 26. token 和用户输入长度限制

我们的 `/chat` 接口后面不能无限接收用户输入。

原因：

```text
太长会增加成本
太长会增加延迟
太长可能超过上下文窗口
太长可能挤占输出空间
太长也可能是恶意请求
```

后面会逐步做：

```text
请求模型限制长度
业务层限制长度
token 预算检查
错误提示
日志记录
```

## 27. 当前项目新增了什么

这一节给 `projects/ai-service` 加了两个小基础。

### 新增配置：MAX_OUTPUT_TOKENS

文件：

```text
projects/ai-service/.env.example
projects/ai-service/app/core/config.py
```

新增：

```env
MAX_OUTPUT_TOKENS=1024
```

配置类里新增：

```python
max_output_tokens: int = Field(default=1024, gt=0)
```

意思是：

```text
后面调用真实模型时，默认最多让模型输出 1024 tokens。
这个值必须大于 0。
```

### 新增本地粗略估算工具

文件：

```text
projects/ai-service/app/core/token_usage.py
```

提供：

```python
estimate_text_tokens_roughly(text)
build_token_budget(text, max_output_tokens)
```

注意：

```text
它不是精确 tokenizer。
它不是计费依据。
它只是学习和预算保护用的粗略估算。
```

真实 token 数以后以 API 返回的 `usage` 为准。

## 28. 为什么不现在接精确 tokenizer

你可能会问：

```text
为什么不直接安装 tokenizer 库，精确计算 token？
```

原因是当前阶段重点不是追求工具完整，而是先建立概念。

而且真实工程里，最终仍然要看：

```text
API 返回 usage
```

本地 tokenizer 适合：

```text
请求前预估
大文本切分
RAG chunk 控制
成本预估
```

这些后面会系统学习。

当前先用粗略估算帮助你理解预算。

## 29. 一个最小预算例子

假设：

```text
用户输入粗略估算 300 tokens
MAX_OUTPUT_TOKENS=1024
```

那么这次请求至少要预留：

```text
300 + 1024 = 1324 tokens
```

这不是最终费用。

它只是告诉你：

```text
这次请求大概要给输入和输出留多少 token 空间。
```

真实输出可能只用了 200 tokens。

那真实 total_tokens 会更小。

## 30. 当前先不要深入什么

这一节先不要深入：

```text
不同模型的精确价格
复杂 prompt caching 策略
不同 tokenizer 的底层算法
长上下文注意力机制
embedding token 计算
音频 token 和图片 token
```

后面需要时再学。

当前阶段先会解释：

```text
token 是什么
上下文窗口是什么
费用为什么和 token 有关
为什么要控制输入和输出长度
为什么要记录 usage
```

## 31. 本节练习

### 练习 1

题目：

用自己的话解释 token 是什么。

参考答案：

token 是模型处理文本时使用的基本片段。

它不是简单等于一个字或一个单词，而是 tokenizer 按模型规则切出来的文本小块。

### 练习 2

题目：

为什么“token 不是字数”这个理解很重要？

参考答案：

因为 API 的长度限制和费用通常按 token 计算。

如果误以为 token 等于字数，就可能错误估算输入长度、输出长度、上下文空间和费用。

### 练习 3

题目：

输入 token 包括哪些内容？

参考答案：

输入 token 包括用户问题、系统指令、开发者指令、历史对话、RAG 文档片段、工具定义和格式要求等发给模型的内容。

### 练习 4

题目：

输出 token 是什么？

参考答案：

输出 token 是模型生成回复时消耗的 token。

模型回复越长，输出 token 通常越多。

### 练习 5

题目：

上下文窗口是什么？

参考答案：

上下文窗口是模型一次请求最多能处理的 token 空间。

它通常要容纳输入 token、输出 token，有些模型还要容纳 reasoning tokens。

### 练习 6

题目：

为什么多轮对话不能一直把所有历史都传给模型？

参考答案：

因为历史越多，输入 token 越多，请求会越来越慢、越来越贵，还可能超过上下文窗口，并且无关历史会干扰回答。

### 练习 7

题目：

`max_output_tokens=1024` 是否表示模型一定输出 1024 tokens？

参考答案：

不是。

它表示模型最多输出 1024 tokens，模型可以在更少 token 时完成回复。

### 练习 8

题目：

费用为什么和 token 有关？

参考答案：

因为模型 API 通常按 token 使用量计费。

输入 token 和输出 token 都可能计费，不同模型、不同 token 类型的单价可能不同。

### 练习 9

题目：

后面日志里为什么要记录 `input_tokens`、`output_tokens` 和 `total_tokens`？

参考答案：

为了排查成本、性能和异常。

记录 token 使用量后，可以知道哪些请求最贵、哪些输入太长、哪些模型消耗最多、RAG 检索内容是否过多。

### 练习 10

题目：

当前项目里的 `estimate_text_tokens_roughly` 能不能作为真实计费依据？

参考答案：

不能。

它只是本地粗略估算工具，用于学习和预算保护。

真实 token 数应该以模型 API 响应里的 `usage` 为准。

## 32. 本节自测

### 自测 1

题目：

token 是模型处理文本的什么？

参考答案：

token 是模型处理文本时使用的基本文本片段。

### 自测 2

题目：

1 token 是否一定等于 1 个英文单词？

参考答案：

不是。

常见短词可能是一个 token，长词可能拆成多个 token。

### 自测 3

题目：

OpenAI 官方文档给的英文粗略估算是什么？

参考答案：

粗略来说，1 token 约等于 4 个英文字符，约等于 0.75 个英文单词。

### 自测 4

题目：

`input_tokens` 表示什么？

参考答案：

表示输入给模型的内容消耗的 token 数。

### 自测 5

题目：

`output_tokens` 表示什么？

参考答案：

表示模型生成输出时消耗的 token 数。

### 自测 6

题目：

`total_tokens` 通常怎么理解？

参考答案：

通常可以理解成输入 token 和输出 token 的总和。

### 自测 7

题目：

上下文窗口只限制输入吗？

参考答案：

不是。

对文本生成模型来说，输入和生成输出合起来都要受模型上下文长度限制。

### 自测 8

题目：

为什么 RAG 要做 top_k 检索？

参考答案：

因为不能把所有文档都塞进上下文窗口。

top_k 用来只选择最相关的若干文档片段，控制 token 数、成本和回答质量。

### 自测 9

题目：

`MAX_OUTPUT_TOKENS` 的作用是什么？

参考答案：

它用来限制模型最多生成多少输出 token，从而控制成本、长度、延迟和上下文预算。

### 自测 10

题目：

真实费用应该看本地估算，还是看 API 返回的 usage？

参考答案：

应该看 API 返回的 usage。

本地估算只能做请求前的粗略预算。

## 33. 本节小结

这一节学完后，你应该能解释：

```text
token 是模型处理文本的小块
token 不等于字数或单词数
输入和输出都会消耗 token
上下文窗口限制一次请求能容纳的总 token 空间
长对话和 RAG 都必须控制上下文
费用和 token 数、模型单价、工具使用有关
max_output_tokens 用来限制输出长度
日志里要记录 token 使用量
本地估算不等于真实计费
```

下一节学习：

```text
OpenAI SDK 基础调用方式
```

下一节会开始准备真实调用代码，但仍然会先讲清楚：

```text
SDK 是什么
为什么用 SDK
SDK 和 HTTP 请求是什么关系
如何安装 openai Python SDK
如何写最小 Responses API 调用
如何不泄露 API key
```

## 34. 参考资料

- [OpenAI 官方文档：Key concepts - Tokens](https://developers.openai.com/api/docs/concepts#tokens)
- [OpenAI 官方文档：Pricing](https://developers.openai.com/api/docs/pricing)
- [OpenAI 官方文档：Models](https://developers.openai.com/api/docs/models)
- [OpenAI API Reference：Create a model response](https://developers.openai.com/api/reference/resources/responses/methods/create/)
- [OpenAI 官方文档：Production best practices](https://platform.openai.com/docs/guides/production-best-practices)
- [OpenAI 官方文档：Reasoning models](https://developers.openai.com/api/docs/guides/reasoning)
