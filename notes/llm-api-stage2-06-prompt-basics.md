# 阶段 2 第 6 节：prompt 基础：怎么写清楚任务

## 1. 这一节学什么

上一节我们学了：

```text
messages 是一组带 role 的消息
system / user / assistant 分别承担不同职责
```

这一节继续往下走：

```text
每条消息里的 content 到底应该怎么写？
```

这就是 prompt 基础。

这一节要学：

```text
prompt 是什么
prompt 和 messages 的关系
一个好 prompt 应该包含哪些部分
什么是模糊 prompt
怎么把模糊任务改成清晰任务
怎么写上下文
怎么写约束
怎么写输出格式
怎么写不知道时的处理规则
哪些事情不能只靠 prompt
项目里怎么用 prompt_builder.py 构建清晰 prompt
```

## 2. prompt 是什么

`prompt` 可以先理解成：

```text
你给模型看的任务说明。
```

但这句话还不够完整。

更工程化一点：

```text
prompt 是模型本次生成回答时看到的全部指令、上下文和输入。
```

在简单场景里，prompt 可能就是一句话：

```text
请解释 FastAPI 是什么。
```

在真实项目里，prompt 往往包括：

```text
系统规则
用户问题
历史对话
业务上下文
检索到的资料
输出格式要求
失败时怎么处理
```

所以 prompt 不是“玄学咒语”。

它是：

```text
给模型的结构化任务说明。
```

## 3. prompt 和 messages 的关系

上一节我们学过 messages：

```json
[
  {"role": "system", "content": "你是一个耐心的编程老师。"},
  {"role": "user", "content": "请解释 FastAPI 是什么。"}
]
```

这里每个 `content` 都是 prompt 的一部分。

可以这样理解：

```text
messages 是容器。
prompt 是容器里的任务内容。
```

在 Chat Completions 风格接口里：

```text
system content + user content + assistant history = 本次模型看到的 prompt 上下文
```

在 Responses API 里，OpenAI 官方文档推荐把高层要求放到 `instructions`，把用户输入放到 `input`。

概念上仍然是：

```text
告诉模型规则
提供用户输入
让模型按要求生成
```

## 4. prompt 不是越长越好

很多初学者会以为：

```text
prompt 越长越专业。
```

这不对。

好的 prompt 应该是：

```text
清楚
具体
必要
可执行
不互相矛盾
```

太长的 prompt 会带来问题：

```text
占 token
成本更高
响应更慢
模型抓不住重点
规则之间可能冲突
后续维护困难
```

所以目标不是写长，而是写清楚。

## 5. 一个好 prompt 的 5 个部分

初学阶段可以先记住 5 个部分：

```text
任务
上下文
约束
输出格式
无法完成时怎么办
```

也就是：

```text
让模型知道要做什么
让模型知道基于什么做
让模型知道不能怎么做
让模型知道回答长什么样
让模型知道不确定时怎么处理
```

## 6. 任务：告诉模型要做什么

任务要具体。

模糊写法：

```text
帮我看看这个。
```

问题是：

```text
看什么？
看语法？
看逻辑？
看安全？
看性能？
要不要修改？
要不要解释？
```

清楚写法：

```text
请检查下面这段 Python 代码是否存在语法错误，并用初学者能理解的方式解释错误原因。
```

这就明确了：

```text
对象：Python 代码
任务：检查语法错误
输出：解释错误原因
受众：初学者
```

## 7. 上下文：告诉模型背景

上下文是：

```text
帮助模型理解任务背景的信息。
```

例如：

```text
用户刚学完 Python 函数，还不熟悉类型提示。
```

这句话会影响模型回答方式。

没有上下文时，模型可能回答得很抽象。

有上下文时，模型更容易贴合当前学习阶段。

上下文可以包括：

```text
用户水平
业务背景
当前项目状态
前置知识
相关资料
错误信息
代码片段
```

## 8. 约束：告诉模型必须遵守什么

约束是：

```text
回答时必须遵守的限制。
```

例如：

```text
用中文回答
不要假设用户懂 FastAPI
不要给出真实价格，价格需要查官方文档
不要输出超过 5 个要点
不要编造资料中没有的信息
```

约束可以让回答更稳定。

但要注意：

```text
约束不要互相矛盾。
```

错误例子：

```text
请详细解释，每个回答不超过 20 个字。
```

这两个要求可能冲突。

## 9. 输出格式：告诉模型怎么回答

输出格式是：

```text
回答应该长成什么样。
```

例如：

```text
先用一句话解释，再给 3 个要点。
```

或者：

```text
按下面格式输出：
问题：
原因：
修复方式：
示例代码：
```

输出格式越明确，后端越容易处理。

后面学结构化输出时，会进一步要求模型输出 JSON 或符合 Pydantic schema 的结构。

## 10. 无法完成时怎么办

这是很多初学者会忽略的一点。

模型有时不知道答案。

如果你不告诉它“不知道时怎么办”，它可能会：

```text
猜
编
说得很像真的
```

所以可以写：

```text
如果资料中没有答案，请回答“根据现有资料无法确定”，不要编造。
```

或者：

```text
如果不确定，请明确说不确定，并说明需要查哪些资料。
```

后面做 RAG 时，这一点非常重要。

## 11. 模糊 prompt 示例

模糊 prompt：

```text
优化一下这段代码。
```

它的问题：

```text
不知道优化什么
不知道目标是可读性、性能还是安全
不知道是否允许改接口
不知道是否需要解释
不知道输出完整代码还是只给建议
```

更清楚的 prompt：

```text
请检查下面这段 Python 代码的可读性问题。
要求：
- 不改变函数输入输出
- 优先指出变量命名、重复逻辑和异常处理问题
- 每个问题给出原因和修改建议
输出格式：
1. 问题
2. 原因
3. 建议
```

## 12. 模糊 prompt 为什么容易答偏

模型不是读心术。

如果你不说清目标，它会自己猜。

猜测方向可能和你真正想要的不一致。

比如你写：

```text
写好一点。
```

模型可能理解成：

```text
语言更优美
内容更长
结构更清楚
更适合商务场景
更像营销文案
```

所以你要把“好”具体化。

例如：

```text
改得更适合初学者阅读。
每段不超过 3 行。
保留原意，不增加新观点。
```

## 13. prompt 和代码的边界

prompt 很有用，但不能代替代码。

这些事情可以放 prompt：

```text
回答风格
解释深度
输出格式
遇到不确定资料时怎么说
按什么角色回答
```

这些事情不能只靠 prompt：

```text
权限校验
API key 安全
金额计算
数据库写入权限
用户身份判断
敏感操作确认
JSON 格式强校验
日志和审计
```

一句话：

```text
prompt 负责指导模型。
代码负责保证系统边界。
```

## 14. 为什么 prompt 要放进代码

OpenAI prompt engineering 文档建议把生产 prompt 放在应用代码里，而不是只放在外部临时对象里。

原因是代码里的 prompt 可以：

```text
代码审查
版本管理
测试
跟随部署
回滚
和业务逻辑放在一起维护
```

这和我们当前做法一致。

我们新增：

```text
app/services/prompt_builder.py
```

把 prompt 构建逻辑放进项目代码。

这样 prompt 不是散落在脚本里的字符串。

## 15. 当前项目新增了什么

本节新增：

```text
projects/ai-service/app/services/prompt_builder.py
projects/ai-service/tests/test_prompt_builder.py
```

并让：

```text
scripts/llm_compatible_smoke_test.py
```

复用 prompt builder。

这样以后真实调用模型时，用户 prompt 是结构化构建出来的。

## 16. PromptParts

项目新增：

```python
@dataclass(frozen=True)
class PromptParts:
    task: str
    context: str | None = None
    constraints: Sequence[str] = ()
    output_format: str | None = None
    failure_policy: str | None = None
```

它表示一个清晰 prompt 的组成部分。

字段含义：

```text
task            任务
context         上下文
constraints     约束
output_format   输出格式
failure_policy  无法完成时怎么办
```

## 17. build_clear_user_prompt

项目新增：

```python
def build_clear_user_prompt(parts: PromptParts) -> str:
    ...
```

它会把 `PromptParts` 转成带分段标题的 prompt。

例如：

```python
build_clear_user_prompt(
    PromptParts(
        task="解释 token 是什么",
        context="用户刚学完 LLM API 基础。",
        constraints=["用中文回答", "适合零基础学习者"],
        output_format="先给一句话解释，再给 3 个要点。",
        failure_policy="如果不确定，请明确说不确定。",
    )
)
```

会得到：

```text
## 任务
解释 token 是什么

## 上下文
用户刚学完 LLM API 基础。

## 要求
- 用中文回答
- 适合零基础学习者

## 输出格式
先给一句话解释，再给 3 个要点。

## 无法完成时
如果不确定，请明确说不确定。
```

这种格式比随手写一段话更清楚。

## 18. 为什么用分段标题

分段标题的作用是：

```text
让模型更容易区分任务、背景、要求和输出格式。
```

人读起来也更清楚。

后续维护时也更容易改：

```text
改任务
改约束
改输出格式
改失败策略
```

## 19. 为什么 task 不能为空

如果 task 为空：

```text
模型不知道要做什么。
```

所以 `build_clear_user_prompt` 会检查：

```python
if not stripped:
    raise ValueError("task must not be blank")
```

这是一个小的工程化保护。

让错误尽早发生，而不是把空任务发给模型。

## 20. 为什么清理空约束

有时候约束列表可能来自代码拼接：

```python
["用中文回答", "", "   "]
```

空约束没有意义。

所以项目会把空约束过滤掉，只保留有效内容。

## 21. smoke test 现在怎么使用 prompt builder

上一节的 smoke test 原来直接把用户输入塞进 messages。

现在改成：

```python
user_prompt = build_clear_user_prompt(
    PromptParts(
        task=args.prompt,
        constraints=[
            "用中文回答",
            "回答适合刚开始学习 AI 应用开发的人",
            "不要编造不确定的信息",
        ],
        output_format="先用一句话回答，再给 3 个要点。",
        failure_policy="如果不确定，请明确说不确定，并说明需要查官方文档。",
    )
)
messages = serialize_chat_messages(build_single_turn_messages(user_prompt))
```

这样真实调用时，模型看到的是更清楚的任务说明。

## 22. prompt builder 和 message builder 的关系

两个模块分工不同。

```text
prompt_builder.py   负责生成 user content
message_builder.py  负责把 system/user/history 组装成 messages
```

也就是：

```text
prompt_builder 负责写清楚“说什么”
message_builder 负责放到“哪个 role 里”
```

这种分工以后会很有用。

## 23. 一个从模糊到清晰的例子

模糊输入：

```text
讲一下 Python 列表
```

清晰 prompt：

```text
## 任务
解释 Python 列表是什么

## 上下文
用户刚学完变量和字符串，还不熟悉容器类型。

## 要求
- 用中文回答
- 从零基础角度解释
- 给 2 个简单代码例子
- 不要讲列表推导式

## 输出格式
先给一句话定义，再解释用途，最后给代码例子。

## 无法完成时
如果需要前置知识，请先说明前置知识。
```

这比一句“讲一下 Python 列表”稳定得多。

## 24. prompt 里的输出格式不等于强校验

如果你写：

```text
请输出 JSON
```

模型大概率会尽量输出 JSON。

但这不等于一定合法。

它可能输出：

```text
解释文字 + JSON
缺少字段
字段类型不对
多一个逗号
```

所以真正需要强格式时，后面要学：

```text
结构化输出
Pydantic 校验
错误重试
```

当前 prompt 只是第一层约束。

## 25. prompt 里的“不知道就说不知道”也不是绝对保证

写：

```text
不知道就说不知道
```

很重要。

但不能保证模型永远不编造。

后面 RAG 系统还要加：

```text
检索结果为空时不调用模型或明确拒答
回答必须引用来源
输出后做引用检查
日志记录检索结果
必要时人工审核
```

所以还是那句话：

```text
prompt 指导模型，代码守住边界。
```

## 26. prompt 版本管理

prompt 会变。

你可能会不断调整：

```text
回答风格
拒答策略
输出格式
业务规则
```

如果 prompt 写在代码里，就能通过 Git 看到：

```text
谁改了
改了什么
什么时候改的
测试是否通过
能不能回滚
```

这也是为什么本节把 prompt builder 放进项目代码。

## 27. prompt 测试

本节新增：

```text
tests/test_prompt_builder.py
```

测试内容包括：

```text
只有任务时怎么输出
完整任务、上下文、约束、格式、失败策略怎么输出
首尾空格会被清理
空约束会被忽略
空任务会报错
```

这些测试不会调用真实模型。

测试的是：

```text
我们自己的 prompt 构建逻辑是否稳定。
```

## 28. 为什么 prompt 也要测试

很多人认为 prompt 是文字，不需要测试。

这是不对的。

prompt 一旦进入项目，就属于业务逻辑的一部分。

如果有人改坏 prompt：

```text
删掉“不确定就说不确定”
删掉“必须引用来源”
改坏输出格式
把中文回答改成英文回答
```

模型行为就会变化。

所以 prompt 也要测试。

## 29. 常见 prompt 错误

### 错误 1：目标不清

```text
帮我处理一下。
```

应该改成：

```text
请把下面这段文本总结成 3 个要点。
```

### 错误 2：没有上下文

```text
解释一下这个。
```

应该补充：

```text
用户是 Python 初学者，刚学完函数，还没有学过类。
```

### 错误 3：没有输出格式

```text
分析一下日志。
```

应该改成：

```text
按“错误现象 / 可能原因 / 排查步骤 / 修复建议”输出。
```

### 错误 4：把安全交给模型自觉

```text
不要做危险操作。
```

这不够。

代码层也要限制：

```text
权限
白名单
确认流程
审计日志
```

### 错误 5：要求互相冲突

```text
详细解释，但每个回答不超过 20 个字。
```

要改成可执行的要求：

```text
先用一句话概括，再用 3 个短要点解释。
```

## 30. 本节练习

### 练习 1

题目：

用自己的话解释 prompt 是什么。

参考答案：

prompt 是模型本次生成回答时看到的任务说明、上下文、约束和输入内容。

它不只是用户的一句话，而是模型用来理解任务并生成回答的完整信息。

### 练习 2

题目：

prompt 和 messages 的关系是什么？

参考答案：

messages 是带角色的消息列表，prompt 是这些消息里真正给模型看的任务内容。

system、user、assistant 的 content 共同组成模型本次看到的上下文。

### 练习 3

题目：

一个好 prompt 通常包含哪 5 个部分？

参考答案：

通常包含：

```text
任务
上下文
约束
输出格式
无法完成时怎么办
```

### 练习 4

题目：

把“帮我看看这段代码”改成更清楚的 prompt。

参考答案：

可以改成：

```text
请检查下面这段 Python 代码是否存在语法错误和明显逻辑问题。
要求：
- 不改变函数输入输出
- 用初学者能理解的方式解释
- 每个问题给出原因和修改建议
输出格式：
1. 问题
2. 原因
3. 修改建议
```

### 练习 5

题目：

为什么 prompt 不能代替权限校验？

参考答案：

因为 prompt 只是给模型的行为指导，不能保证模型百分百遵守，也不能真正阻止系统执行危险操作。

权限校验必须由代码、数据库、后端逻辑和审计机制完成。

### 练习 6

题目：

为什么要给模型写“无法完成时怎么办”？

参考答案：

因为模型不确定时可能会猜测或编造。

明确写出无法完成时的处理方式，可以降低编造风险，比如要求它说明“不确定”或“根据现有资料无法确定”。

### 练习 7

题目：

`PromptParts.task` 为什么不能为空？

参考答案：

因为 task 是模型要完成的核心任务。

如果 task 为空，模型不知道要做什么，所以项目会提前抛出错误。

### 练习 8

题目：

为什么项目要把 prompt builder 写进代码，而不是每次在脚本里手写字符串？

参考答案：

因为代码里的 prompt builder 可以复用、测试、代码审查、版本管理和回滚。

这样 prompt 变成可维护的工程资产，而不是散落的临时字符串。

### 练习 9

题目：

写“请输出 JSON”是否一定能得到合法 JSON？

参考答案：

不一定。

prompt 只能指导模型，不能保证格式绝对正确。

需要强格式时，还要结合结构化输出、Pydantic 校验和错误处理。

### 练习 10

题目：

把“讲一下 RAG”改成适合当前学习阶段的清晰 prompt。

参考答案：

可以改成：

```text
## 任务
解释 RAG 是什么

## 上下文
用户已经学过 Python 基础、FastAPI 基础和 LLM API 基础，但还没有学过向量数据库。

## 要求
- 用中文回答
- 适合初学者
- 不深入公式
- 用一个企业知识库问答的例子解释

## 输出格式
先给一句话定义，再用 4 个步骤解释流程，最后列出后续要学的知识点。

## 无法完成时
如果涉及暂未学习的概念，请先用一句话解释，不要展开太深。
```

## 31. 本节自测

### 自测 1

题目：

prompt 是不是越长越好？

参考答案：

不是。

prompt 应该清楚、具体、必要、可执行，不是越长越好。

### 自测 2

题目：

“帮我优化一下”为什么不好？

参考答案：

因为它没有说明优化目标、对象、限制和输出方式。

模型不知道你想优化可读性、性能、安全还是结构。

### 自测 3

题目：

上下文的作用是什么？

参考答案：

上下文帮助模型理解任务背景，例如用户水平、业务场景、项目状态、相关资料或错误信息。

### 自测 4

题目：

输出格式的作用是什么？

参考答案：

输出格式告诉模型回答应该长成什么样，方便用户阅读，也方便后端处理。

### 自测 5

题目：

prompt 能不能保证模型永远不编造？

参考答案：

不能。

prompt 可以降低风险，但还需要 RAG 检索、引用校验、结构化输出、代码校验和必要的人工审核。

### 自测 6

题目：

`build_clear_user_prompt` 会把 prompt 分成哪些标题？

参考答案：

可能包含：

```text
## 任务
## 上下文
## 要求
## 输出格式
## 无法完成时
```

### 自测 7

题目：

`prompt_builder.py` 和 `message_builder.py` 的区别是什么？

参考答案：

`prompt_builder.py` 负责生成清晰的用户 prompt 内容。

`message_builder.py` 负责把 system、user、history 组装成 messages。

### 自测 8

题目：

为什么 prompt 也需要测试？

参考答案：

因为 prompt 会影响模型行为，属于业务逻辑的一部分。

测试可以防止输出格式、拒答策略、约束等被误改。

### 自测 9

题目：

OpenAI 文档建议新 prompt 工程把 prompt 放在哪里？

参考答案：

OpenAI prompt engineering 文档建议把生产 prompt 放在应用代码中，便于代码审查、测试和部署管理。

### 自测 10

题目：

下一节学习什么？

参考答案：

下一节学习第一次真实 `/chat` 调用，把当前 mock `/chat` 逐步接入真实模型调用。

## 32. 本节小结

这一节完成了：

```text
理解 prompt 是模型本次看到的任务说明
理解 prompt 和 messages 的关系
掌握任务、上下文、约束、输出格式、失败策略 5 个组成部分
理解模糊 prompt 为什么容易答偏
理解 prompt 不能代替代码边界
新增 prompt_builder.py
新增 prompt builder 测试
让 smoke test 使用结构化 prompt
```

现在我们已经具备：

```text
SDK client
messages 构建工具
prompt 构建工具
```

下一节进入：

```text
第一次真实 /chat 调用
```

这会开始把 mock `/chat` 替换为真实模型调用，但仍然会按步骤做：

```text
先封装 LLM service
再处理缺 key
再处理模型响应
再补测试
再考虑错误处理
```

## 33. 参考资料

- [OpenAI 官方文档：Prompt engineering](https://developers.openai.com/api/docs/guides/prompt-engineering)
- [OpenAI 官方文档：Text generation](https://developers.openai.com/api/docs/guides/text)
- [OpenAI 官方文档：Migrate to the Responses API](https://developers.openai.com/api/docs/guides/migrate-to-responses)
