# 阶段 4 第 18 节：把检索结果交给模型回答

## 本节状态

已完成。

前面第 15 到 17 节，我们已经完成了检索侧的最小链路：

```text
用户问题
-> query embedding
-> payload filter 限定范围
-> top_k 取候选
-> score_threshold 过滤低相关结果
-> RetrievedChunk
```

第 18 节开始进入 RAG 的 generate 阶段：

```text
RetrievedChunk
-> 整理成模型可读上下文
-> 放进 messages / prompt
-> 调用模型
-> 生成基于知识库资料的中文回答
```

这一步很关键。因为 RAG 不是“搜到资料就结束”，也不是“把资料随便塞给模型”。真正要学的是：

```text
如何把检索结果变成受约束、可解释、尽量不编造的模型输入。
```

## 本节学习目标

学完本节，你要能讲清楚：

1. RAG 里的 generate 阶段是什么。
2. 为什么检索结果不能原样乱塞给模型。
3. 为什么上下文要有编号、来源、标题、章节、分数和正文。
4. 为什么 prompt 里要明确“只能根据资料回答”。
5. 为什么没有检索结果时不能调用模型硬答。
6. 为什么本节还不做引用来源输出。
7. 为什么测试里继续使用 fake LLM，不真实调用模型。
8. 本项目新增的 `RagAnswerService` 负责什么，不负责什么。

## 本节暂时不学什么

本节只做“检索结果交给模型生成回答”的最小安全链路。

暂时不做：

- 不做 HTTP API 接口，先把内部能力学清楚。
- 不把真实 Qdrant 检索和真实模型调用串成完整接口。
- 不做引用来源格式，第 19 节单独讲。
- 不系统讲无检索结果兜底策略，第 20 节单独讲。
- 不做 prompt injection 防护，第 28 节会系统讲 RAG 安全。
- 不做真实 embedding 阈值调优，第 24、25 节会讲。
- 不做 LangChain RAG chain 封装，当前先用原生 OpenAI-compatible SDK 跑清楚底层逻辑。

## 一、基础知识铺垫

### 1. RAG 为什么分 retrieve 和 generate

RAG 可以拆成两个核心动作：

```text
retrieve：找资料
generate：根据资料生成回答
```

前面几节主要在学 retrieve。

retrieve 负责：

- 把用户问题转成 query vector。
- 去向量数据库找相似 chunk。
- 用 payload filter 限定业务范围和权限。
- 用 top_k 控制最多返回几个候选。
- 用 score_threshold 过滤低相关结果。

generate 负责：

- 把 retrieved chunks 整理成模型可读上下文。
- 把用户问题和上下文一起放进 prompt/messages。
- 要求模型只根据资料回答。
- 从模型响应中取出最终自然语言答案。

两者不要混在一起理解。

检索做得好，不代表回答一定好。

回答 prompt 写得好，也不能弥补检索资料完全错误。

所以真实 RAG 问题通常要分别排查：

```text
是没检索到对的资料？
还是检索到了，但 prompt 没约束好模型？
```

还可以换一个更工程化的说法：

```text
retrieve 决定“答案的证据从哪里来”。
generate 决定“如何把证据组织成用户能读懂的回答”。
```

这两个阶段的失败方式不同。

如果 retrieve 失败，模型拿到的是错误资料或没有资料。再好的 prompt 也很难生成正确答案。

如果 generate 失败，检索资料可能是对的，但模型没有严格使用资料，或者回答格式混乱，或者把调试字段当成了业务事实。

所以从这一节开始，你要建立一个非常重要的 RAG 排查习惯：

```text
先看检索结果是否正确，再看生成回答是否忠实于检索结果。
```

不要一看到回答不对，就只改 prompt。

也不要一看到回答不对，就只调 embedding。

RAG 是一条链路，问题可能出现在链路的不同位置。

### 2. generate 阶段不是“让模型随便总结”

很多人刚学 RAG 时，会把 generate 理解成：

```text
把资料给模型，让模型总结一下。
```

这个理解太粗。

在企业知识库 RAG 里，generate 至少包含 5 件事：

1. **选择要给模型的资料**
   不是所有检索结果都一定放进去。前面已经通过 `score_threshold` 过滤了低相关结果，后面还可能通过 rerank、去重、截断进一步控制。

2. **组织资料格式**
   模型需要知道哪里是资料正文，哪里是来源信息，哪里是系统调试字段。

3. **声明回答边界**
   告诉模型只能根据资料回答，不能把自己的常识或猜测混进去。

4. **规定资料不足时的行为**
   资料不足时要承认不足，而不是继续编。

5. **提取最终回答**
   模型返回的是 API 响应对象，后端要提取其中的文本，并处理空响应、异常响应和调用失败。

所以 generate 阶段不是“让模型自由发挥”，而是：

```text
后端把可用证据包装成上下文，并让模型在明确边界内组织语言。
```

这个思路会贯穿后面的引用来源、无资料处理、RAG 安全和评测。

### 3. 什么是 grounded answer

这一节你要认识一个很重要的概念：`grounded answer`。

可以先翻译成：

```text
有资料支撑的回答
```

普通聊天回答可能来自模型训练时学到的通用知识。

RAG 回答应该来自当前检索到的知识库资料。

两者区别很大：

| 类型 | 答案依据 | 风险 |
| --- | --- | --- |
| 普通聊天回答 | 模型训练知识 + 当前 prompt | 可能和企业最新规则不一致 |
| RAG grounded answer | 当前检索资料 | 更容易追溯和更新 |

举个例子。

用户问：

```text
订单多久发货？
```

模型凭常识可能回答：

```text
一般 1 到 3 天发货。
```

但你的企业知识库资料写的是：

```text
订单付款后通常会在 24 小时内发货。
```

RAG 的回答应该跟着企业资料走：

```text
订单通常会在付款后 24 小时内发货。
```

这就是 grounded answer 的意义：

```text
答案要落在当前资料上，而不是落在模型自己的记忆上。
```

以后你跟别人讲 RAG 时，要能说出这句话：

```text
RAG 不是让模型更会背知识，而是让模型围绕当前检索到的证据回答。
```

### 4. 什么是上下文工程

本节其实开始接触一个重要能力：上下文工程。

上下文工程可以先理解成：

```text
把模型需要的信息，以清楚、稳定、有边界的形式放进上下文窗口。
```

在 RAG 里，上下文工程至少要考虑：

- 放哪些 chunk。
- chunk 按什么顺序放。
- 每个 chunk 是否有编号。
- 是否保留来源和章节。
- 正文和 metadata 是否分清楚。
- 资料之间是否有明显分隔。
- 是否告诉模型哪些字段不能当成业务事实。
- 没有资料时是否完全不让模型硬答。

如果上下文组织得不好，模型可能会：

- 把多个资料混在一起。
- 忽略真正相关的资料。
- 把 `score` 当成用户能理解的业务信息。
- 把 `chunk_id` 写进回答。
- 把检索资料里的说明和用户问题混淆。
- 在资料不足时继续补全答案。

所以本节的重点不是字符串拼接，而是：

```text
为模型建立一个清楚的资料阅读环境。
```

### 5. 什么是 context stuffing

RAG 入门阶段常见做法叫 `context stuffing`。

意思是：

```text
把检索到的若干 chunk 直接塞进 prompt，让模型基于这些上下文回答。
```

本节做的就是一个最小版 context stuffing。

它的优点：

- 简单。
- 直观。
- 容易测试。
- 适合刚开始理解 RAG。

它的局限：

- 上下文窗口有限，chunk 太多会放不下。
- 检索结果有噪声时，模型可能受干扰。
- 多个 chunk 内容冲突时，模型可能不知道信谁。
- 不能自动保证引用来源准确。
- 长文档、多跳问题、复杂推理时不够强。

所以你要知道：

```text
context stuffing 是 RAG 入门的第一种生成方式，不是 RAG 的最终形态。
```

后面随着系统变复杂，可能会加入：

- rerank。
- 去重。
- 上下文压缩。
- map-reduce 总结。
- 分步检索。
- 多轮检索。
- citation 校验。

但现在先把最基础的一步走稳。

### 6. 为什么不能把 chunk 原样乱塞给模型

一个 `RetrievedChunk` 里有：

```text
content
metadata
score
chunk_id
point_id
```

如果我们只是简单拼：

```text
资料1：xxx
资料2：xxx
资料3：xxx
问题：yyy
```

模型可能不清楚：

- 哪些是用户问题。
- 哪些是检索资料。
- 哪些字段是调试信息。
- 哪些内容能作为业务事实。
- 分数、chunk_id 是否应该写进回答。
- 资料不足时该不该拒答。

所以必须把上下文组织得清楚。

本节使用的上下文格式类似：

```text
[资料 1]
source: order-shipping-policy.md
title: 订单发货规则
section: 正常发货时效
chunk_id: order_shipping_policy_chunk_0001
score: 0.9100
content:
订单付款后通常会在 24 小时内发货。
```

这样模型更容易区分：

- `content` 是可以用来回答的资料正文。
- `source/title/section` 是资料背景。
- `chunk_id/score` 是检索调试信息，不是业务事实。

这背后有一个基本原则：

```text
给模型的上下文越结构清楚，模型越容易按你的边界工作。
```

当然，这不代表格式清楚就万无一失，但它比随便拼接要可靠得多。

### 7. 为什么要保留 metadata

你可能会想：

```text
不是只要 content 就能回答吗？
```

短期看，似乎可以。

但真实 RAG 里 metadata 很重要：

1. `source`：后续引用来源要用。
2. `title`：帮助模型理解资料来自哪类文档。
3. `section`：帮助模型理解资料位于哪个章节。
4. `chunk_id`：方便开发者排查是哪一段资料被用到。
5. `score`：方便调试相关性，但不应该当成业务事实。

本节还不要求模型输出引用来源，但我们在上下文中保留 metadata，是为了后面第 19 节自然衔接。

### 8. 模型为什么必须被约束

大模型默认是一个语言生成器。

如果你只给它：

```text
请回答用户问题。
```

它可能会根据自己的训练知识回答，而不是严格根据你的企业知识库。

这不符合 RAG 的目标。

RAG 的目标不是：

```text
让模型凭记忆回答。
```

而是：

```text
让模型根据当前检索出来的企业资料回答。
```

所以 prompt 里必须有规则：

```text
只能使用检索资料中的信息回答。
如果检索资料不足以回答，直接说明资料不足，不要编造。
不要把资料编号、score 或 chunk_id 当成业务事实。
```

这不是绝对安全防线，但它是生成阶段最基本的约束。

还要注意一点：

```text
约束模型，不等于信任模型。
```

prompt 规则是必要的，但后端仍然要做工程边界：

- 没有 chunks 时不调用模型。
- 权限过滤放在检索阶段，而不是只靠 prompt。
- 低相关资料通过 `score_threshold` 先过滤。
- 后续引用来源要有结构化校验。
- 后续 RAG 安全要处理资料里的恶意指令。

所以模型约束只是其中一层，不是全部安全机制。

### 9. 没有检索结果为什么不能硬答

如果 `chunks=[]`，说明检索阶段没有给出可用资料。

这时有两种做法：

错误做法：

```text
仍然调用模型，让模型自己想办法回答。
```

正确做法：

```text
不要调用模型硬答，返回“当前知识库没有找到足够相关的资料”。
```

原因很简单：

```text
RAG 答案必须有资料支撑。
没有资料，就没有根据知识库回答的基础。
```

本节先做一个最小兜底：

```text
当前知识库没有找到足够相关的资料，无法根据知识库回答这个问题。
```

第 20 节会系统讲无检索结果时还能怎么处理，比如扩大检索范围、提示用户补充问题、转人工、记录待补充知识等。

### 10. generate 阶段和“问答质量”的关系

这一节加入 generate 后，你会开始看到 RAG 质量不只由检索决定。

同样一批检索结果，不同的 generate 写法会产生不同效果。

比如检索资料是：

```text
订单付款后通常会在 24 小时内发货。
促销高峰期可能延迟。
```

如果 prompt 没有限制，模型可能回答：

```text
订单一般 1 到 3 天发货，如果延迟可以催促商家。
```

这个回答可能有一部分常识是模型补的。

如果 prompt 明确要求只根据资料回答，模型更应该回答：

```text
订单付款后通常会在 24 小时内发货；如果处于促销高峰期，可能会有延迟。
```

所以 generate 阶段会影响：

- 答案是否忠实资料。
- 答案是否清楚。
- 答案是否承认资料不足。
- 答案是否混入模型常识。
- 答案是否暴露调试字段。

这也是为什么本节要单独学，而不是一句“调用模型”带过。

### 11. 本节为什么还不做引用来源

你可能会问：

```text
既然上下文里已经有 source，为什么不直接让模型回答时带出处？
```

因为引用来源不是一句 prompt 就能可靠完成的。

引用来源要考虑：

- 回答里的每个关键结论来自哪段资料。
- 模型是否引用了真正用到的资料。
- 多个 chunk 合并回答时怎么列出处。
- 来源格式怎么设计。
- 前端如何展示。
- 如果模型引用不存在的编号怎么办。

这些会在第 19 节单独讲。

本节只先做到：

```text
模型基于检索资料生成回答。
```

不要把“生成回答”和“引用来源”混成一个模糊任务。

### 12. 本节为什么还不接完整 HTTP API

你可能也会问：

```text
既然已经能根据 chunks 生成回答了，为什么不直接做一个 /rag-chat 接口？
```

原因是本节目标是理解 generate 阶段。

如果现在直接做完整接口，会同时引入：

- 请求模型设计。
- 依赖注入。
- retriever 和 generator 的编排。
- Qdrant 运行环境。
- LLM API key。
- 错误响应。
- 空结果处理。
- 引用来源返回格式。

这些内容会把本节主题冲散。

现在先把内部能力拆清楚：

```text
retriever 负责找资料。
generator 负责根据资料生成回答。
```

后面再把它们编排成完整接口，会更稳。

### 13. 为什么测试里不用真实模型

第 18 节新增了模型调用，但测试仍然不能真实调用模型。

原因：

1. 真实模型调用需要 API key。
2. 真实模型调用会产生费用。
3. 网络和模型服务状态会让测试不稳定。
4. 模型输出不完全可控，断言会不稳定。
5. 单元测试关注的是“参数是否正确传递”和“边界是否正确处理”。

所以测试里继续使用：

```text
FakeOpenAICompatibleClient
FakeChatCompletions
```

这样我们能验证：

- 是否调用了模型。
- 传给模型的 messages 是否包含问题和资料。
- 没有 chunks 时是否没有调用模型。
- 模型报错时是否映射成统一 `AppException`。
- 日志是否不泄露完整用户问题。

## 二、本节主题系统讲解

### 1. 本节在 RAG 主线里的位置

先把阶段 4 到目前为止的链路完整摆出来：

```text
知识文档
-> loader 读取和清洗
-> splitter 切成 chunk
-> metadata 标准化
-> embedding 生成向量
-> vector_store 写入 Qdrant
-> retriever 查询 Qdrant
-> generator 组织上下文并调用模型
-> answer 返回给用户
```

本节只覆盖最后两步中的第一版：

```text
RetrievedChunk -> generator -> answer
```

也就是说，本节不是重新设计检索，也不是做最终完整产品接口，而是把 RAG 从“能找资料”推进到“能用资料回答”。

从职责角度看：

| 模块 | 负责的问题 |
| --- | --- |
| `retriever.py` | 用户问题应该找回哪些 chunk |
| `generator.py` | 已找回的 chunk 应该怎样交给模型回答 |
| 后续 pipeline/router | 如何把检索和生成编排成完整用户接口 |

这三个层次分开后，代码更容易测试，也更容易讲清楚。

### 2. 本节生成链路的完整流程

`RagAnswerService.generate_answer()` 的流程可以画成：

```text
输入 query + chunks
-> query 去空白校验
-> chunks 为空：直接返回无资料兜底
-> chunks 非空：检查 LLM API key
-> build_rag_messages()
-> client.chat.completions.create(...)
-> extract_first_reply()
-> 记录日志
-> 返回 answer
```

这条流程里面有两个关键分支：

第一个分支：

```text
chunks 为空
```

处理方式：

```text
不调用模型，直接返回固定兜底。
```

第二个分支：

```text
chunks 非空
```

处理方式：

```text
构造上下文，调用模型，生成回答。
```

这两个分支非常重要。

因为它们体现了一个 RAG 系统的基本态度：

```text
有证据才回答，没有证据就承认资料不足。
```

### 3. 本节新增 `app/rag/generator.py`

新增文件：

```text
projects/ai-service/app/rag/generator.py
```

它的职责是：

```text
把 RetrievedChunk 转成模型上下文，并调用模型生成回答。
```

它不负责：

- 文档加载。
- chunk 切分。
- embedding。
- Qdrant 查询。
- payload filter。
- score_threshold。
- 引用来源输出。
- HTTP API 路由。

这就是边界清晰。

到目前为止，RAG 内部模块大致变成：

```text
loaders.py      读文档
splitters.py    切 chunk
embeddings.py   生成向量
vector_store.py 写入和查询 Qdrant
filters.py      构造 payload filter
retriever.py    编排 query embedding + 检索参数
generator.py    把检索结果交给模型生成回答
```

### 4. generate 阶段的输入和输出

本节生成阶段的输入不是“原始文档”，也不是“用户上传的文件”，而是已经经过检索筛选后的：

```text
Sequence[RetrievedChunk]
```

每个 `RetrievedChunk` 都已经带有：

- `content`
- `metadata`
- `score`
- `chunk_id`
- `point_id`

生成阶段输出也不是复杂对象，而是：

```text
str
```

也就是用户能读的自然语言回答。

为什么现在只返回字符串？

因为第 18 节只学习：

```text
怎么根据资料生成回答。
```

第 19 节会开始引入更复杂的输出结构，比如：

```text
answer + citations
```

所以本节输出保持简单。

### 5. `format_retrieved_chunk_for_context()` 做什么

它把一个 `RetrievedChunk` 转成一段模型可读的上下文。

输入是：

```python
RetrievedChunk(
    point_id="point-1",
    chunk_id="order_shipping_policy_chunk_0001",
    content="订单付款后通常会在 24 小时内发货。",
    metadata={
        "source": "order-shipping-policy.md",
        "title": "订单发货规则",
        "section": "正常发货时效",
    },
    score=0.91,
)
```

输出类似：

```text
[资料 1]
source: order-shipping-policy.md
title: 订单发货规则
section: 正常发货时效
chunk_id: order_shipping_policy_chunk_0001
score: 0.9100
content:
订单付款后通常会在 24 小时内发货。
```

这里有几个学习点：

1. `content` 是模型回答的主要依据。
2. `source/title/section` 是资料背景。
3. `chunk_id/score` 主要用于调试和后续引用链路。
4. 资料编号 `[资料 1]` 让多段资料更容易区分。

这里还要理解一个细节：

```text
格式化 chunk，不是为了人看着整齐，而是为了模型更容易识别资料结构。
```

模型虽然能读自然语言，但它不会天然知道你的对象结构。

你要把对象结构明确展开成文本。

### 6. `build_rag_context()` 做什么

它把多个 chunk 拼成一个上下文块。

比如：

```text
[资料 1]
...

[资料 2]
...
```

为什么要统一构造上下文？

因为如果每个调用点都自己拼字符串，后面很容易出现：

- 有的地方没有 source。
- 有的地方没有 score。
- 有的地方编号格式不同。
- 有的地方把 metadata 和 content 混在一起。

统一函数可以保证生成阶段上下文格式稳定。

这里还有一个隐含好处：

```text
上下文格式稳定，后续引用来源、评测和调试才有基础。
```

如果今天资料格式是 `资料1：...`，明天变成 `source=... content=...`，后天又变成 JSON 字符串，模型行为和测试都会变得不稳定。

### 7. `build_rag_user_prompt()` 做什么

它把用户问题和检索资料组织成一个完整 user prompt。

结构是：

```text
请根据下面的检索资料回答用户问题。

回答规则：
1. 只能使用检索资料中的信息回答。
2. 如果检索资料不足以回答，直接说明资料不足，不要编造。
3. 不要把资料编号、score 或 chunk_id 当成业务事实。
4. 当前阶段先生成自然语言回答，引用来源会在后续小节单独学习。

用户问题：
...

检索资料：
...
```

这里的重点不是“文字写得好看”，而是把边界告诉模型：

```text
你要回答什么。
你能依据什么回答。
你不能做什么。
资料不足时怎么办。
```

本节 prompt 里有一句很关键：

```text
不要把资料编号、score 或 chunk_id 当成业务事实。
```

为什么要写这句？

因为上下文里确实包含这些字段。

如果不提醒模型，模型可能回答：

```text
根据 chunk_id order_shipping_policy_chunk_0001，订单会在 24 小时内发货。
```

这对用户来说很奇怪。

更好的回答是：

```text
订单通常会在付款后 24 小时内发货。
```

所以 prompt 不只是告诉模型“回答什么”，还要告诉模型“哪些东西不要暴露给用户”。

### 8. `build_rag_messages()` 做什么

它构造 OpenAI-compatible Chat Completions 常见的 messages：

```python
[
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."},
]
```

system message 负责设定身份和硬约束：

```text
你是企业知识库 RAG 问答助手。
只能根据后端提供的检索资料回答。
资料不足时不能编造。
```

user message 负责提供当前任务：

```text
用户问题 + 检索资料 + 回答规则
```

这比把所有内容都塞到一个普通字符串里更清楚。

从阶段 2 学过的 messages 角度看：

```text
system：长期规则和角色
user：当前任务、问题和资料
assistant：模型回答
```

本节没有把检索资料放进 system message。

原因是检索资料是当前问题的动态上下文，不是助手永久规则。

所以它更适合放在 user message 里，和当前问题绑定。

### 9. `RagAnswerService` 做什么

`RagAnswerService` 是本节的生成服务。

它的核心方法：

```python
generate_answer(query, chunks=[...])
```

执行流程：

```text
检查 query 是否为空
如果 chunks 为空，直接返回无资料回答，不调用模型
检查 LLM API key
构造 RAG messages
调用 OpenAI-compatible chat.completions.create
提取模型 reply
记录成功日志
返回 reply
```

如果模型调用失败，会映射成项目统一异常。

这沿用了前面阶段学过的模型错误处理边界。

### 10. `RagAnswerService` 为什么不直接接收 retriever

你可能会想：

```text
RagAnswerService 为什么不自己调用 retrieve_top_k？
```

因为本节要保持两个阶段的边界：

```text
retriever：找资料。
generator：用资料回答。
```

如果 `RagAnswerService` 里直接调用 Qdrant 检索，就会变成：

```text
既负责检索，又负责生成。
```

这样短期看方便，长期会难测试、难替换、难调试。

比如你想单独测试 prompt 是否正确，就必须准备 embedding 模型和 Qdrant。

现在分开后，测试生成器只需要构造几个 `RetrievedChunk`。

这就是模块拆分的价值。

### 11. 为什么无 chunks 时不检查 API key

当前实现里：

```text
如果 chunks 为空，直接返回 RAG_NO_CONTEXT_REPLY。
```

这一步不需要模型。

所以即使本机没有配置 API key，也可以返回无资料兜底。

这个设计有实际意义：

```text
没有资料时不需要花模型成本，也不应该让模型自由发挥。
```

### 12. 生成阶段日志为什么不能记录完整问题

本节记录日志时会记录：

- provider
- model
- elapsed_ms
- chunk_count
- token usage
- error code

但不记录：

- 完整用户问题。
- 完整检索资料。
- API key。
- 完整模型回答。

原因是 RAG 问答里可能有敏感业务信息。

日志要服务排查，但不能变成敏感数据泄露点。

### 13. 本节测试到底在保护什么

本节测试不是为了证明“模型回答一定正确”。

因为 fake LLM 不理解资料，也不会真正推理。

本节测试保护的是工程边界：

- chunk 格式化后包含必要 metadata 和正文。
- prompt 包含用户问题、检索资料和回答规则。
- messages 分成 system 和 user。
- 有 chunks 时会调用模型。
- 无 chunks 时不会调用模型。
- 没有 API key 时会报项目统一错误。
- 模型异常会映射成 `AppException`。
- 日志不记录完整用户问题。

这些测试能保证：

```text
生成链路的结构是对的。
```

至于真实回答质量，要等真实 embedding、真实检索数据、真实模型和评测集一起验证。

### 14. 第 18 节和后续小节的系统关系

第 18 节之后，RAG 主线会继续这样推进：

| 小节 | 解决的问题 |
| --- | --- |
| 第 18 节 | 能根据检索资料生成回答 |
| 第 19 节 | 回答必须带出处 |
| 第 20 节 | 没有检索结果时怎么处理 |
| 第 21 节 | embedding、向量库、模型调用异常怎么处理 |
| 第 22 节 | RAG 怎么做 fake 测试 |
| 第 28 节 | 文档权限、Prompt Injection、敏感信息怎么防 |

所以第 18 节不是终点。

它是一个连接点：

```text
前面：检索链路
当前：生成回答
后面：出处、兜底、异常、测试、安全
```

你要把它理解成 RAG 问答链路真正开始成型的一节。

## 三、从一次完整流程理解第 18 节

假设用户问：

```text
订单多久发货？
```

前面检索阶段返回：

```text
RetrievedChunk(
  content="订单付款后通常会在 24 小时内发货。",
  source="order-shipping-policy.md",
  section="正常发货时效",
  score=0.91
)
```

第 18 节会把它变成：

```text
system:
你是企业知识库 RAG 问答助手，只能根据资料回答...

user:
请根据下面的检索资料回答用户问题。

回答规则：
...

用户问题：
订单多久发货？

检索资料：
[资料 1]
source: order-shipping-policy.md
title: 订单发货规则
section: 正常发货时效
chunk_id: order_shipping_policy_chunk_0001
score: 0.9100
content:
订单付款后通常会在 24 小时内发货。
```

然后模型生成：

```text
订单通常会在付款后 24 小时内发货。
```

这就是最小 RAG 生成链路。

## 四、常见误区

### 误区 1：RAG 就是把资料复制给模型

不对。

RAG 需要：

- 检索正确资料。
- 控制资料范围。
- 过滤低相关内容。
- 组织上下文。
- 约束模型只能根据资料回答。
- 处理资料不足。

复制资料只是其中很小的一部分。

### 误区 2：prompt 里写“不要编造”就绝对安全

不对。

prompt 约束是必要的，但不是绝对安全。

如果检索资料错了、权限错了、资料里有恶意指令，模型仍可能出问题。

后面还会学 RAG 安全和 prompt injection。

### 误区 3：没有资料时让模型自己回答也可以

不建议。

那就变成普通聊天，不是基于知识库回答。

在企业系统里，用户通常以为答案来自企业知识库。如果没有资料还让模型凭常识回答，容易产生错误信任。

### 误区 4：score 和 chunk_id 应该写进最终回答

当前不应该。

`score` 和 `chunk_id` 主要是系统调试信息。

用户通常需要的是自然语言答案和可读来源。

引用来源会在第 19 节用更合适的方式处理。

### 误区 5：现在已经完成完整 RAG 了

还没有。

现在只是完成了：

```text
检索结果 -> 模型回答
```

后面还要补：

- 引用来源。
- 无结果处理。
- 错误处理。
- RAG 测试策略。
- 文档更新和删除。
- 真实 embedding。
- 检索质量调优。
- 安全和性能。

## 五、本节代码改动说明

### 1. 新增 `app/rag/generator.py`

核心内容：

- `RAG_SYSTEM_PROMPT`
- `RAG_NO_CONTEXT_REPLY`
- `format_retrieved_chunk_for_context()`
- `build_rag_context()`
- `build_rag_user_prompt()`
- `build_rag_messages()`
- `RagAnswerService`
- `create_rag_answer_service()`

学习重点是职责边界：

```text
generator.py 不负责找资料。
generator.py 只负责使用已找回的资料生成回答。
```

### 2. 新增 `tests/test_rag_generator.py`

测试覆盖：

- 单个 chunk 如何格式化成上下文。
- 多个 chunk 如何编号。
- prompt 是否包含问题、资料和回答规则。
- messages 是否包含 system 和 user。
- 有 chunks 时是否调用模型。
- 无 chunks 时是否不调用模型。
- 没有 API key 时是否报统一错误。
- 模型错误是否映射成 `AppException`。
- 日志是否不记录完整用户问题。

测试继续使用 fake LLM。

## 六、本节练习

### 练习 1：解释 retrieve 和 generate 的区别

题目：

请解释 RAG 中 retrieve 和 generate 分别做什么。

参考答案：

retrieve 负责根据用户问题从知识库中找相关资料，比如 query embedding、向量检索、payload filter、top_k、score_threshold。generate 负责把找回的资料整理成上下文，放进 prompt/messages，调用模型生成基于资料的自然语言回答。

### 练习 2：判断哪些信息适合放进上下文

题目：

下面哪些信息适合放进模型上下文？

```text
A. chunk 正文 content
B. source
C. section
D. API key
E. score
F. chunk_id
```

参考答案：

A、B、C、E、F 可以放进上下文，但作用不同。

`content` 是回答依据；`source`、`section` 帮助理解来源；`score` 和 `chunk_id` 主要用于调试和后续引用链路，不应当被模型当成业务事实。API key 绝对不能放进上下文。

### 练习 3：为什么空 chunks 不调用模型

题目：

为什么 `chunks=[]` 时不应该继续调用模型？

参考答案：

因为 RAG 的回答应该基于知识库资料。没有检索资料时，模型没有可靠依据。如果继续调用模型，模型可能凭训练知识或猜测回答，导致答案看起来合理但没有企业知识库支撑。

### 练习 4：设计一条 prompt 规则

题目：

请写一条适合放进 RAG prompt 的规则，用来减少模型编造。

参考答案：

可以写：

```text
只能使用检索资料中的信息回答；如果检索资料不足以回答，直接说明资料不足，不要编造。
```

### 练习 5：说明为什么本节不做引用来源

题目：

为什么本节已经有 `source`，但还不要求模型输出引用来源？

参考答案：

因为引用来源需要单独设计格式和校验方式。模型可能引用错误资料编号，或者把没有用到的资料列为来源。第 18 节先学习“根据资料生成回答”，第 19 节再专门学习“回答必须带出处”。

## 七、自测问题

### 自测 1

问题：

`generator.py` 负责检索 Qdrant 吗？

答案：

不负责。检索由 `retriever.py` 和 `vector_store.py` 负责，`generator.py` 只负责把已检索出的 `RetrievedChunk` 交给模型生成回答。

### 自测 2

问题：

为什么上下文里要区分 `content` 和 metadata？

答案：

`content` 是回答依据，metadata 是资料背景、调试和后续引用来源所需的信息。混在一起会让模型和开发者都更难判断哪些是业务事实。

### 自测 3

问题：

本节生成回答时真实调用模型了吗？

答案：

代码支持真实 OpenAI-compatible 模型调用，但自动化测试不真实调用模型。测试使用 fake client 验证参数和边界。

### 自测 4

问题：

没有检索结果时，本节返回什么？

答案：

返回固定兜底：`当前知识库没有找到足够相关的资料，无法根据知识库回答这个问题。`

### 自测 5

问题：

为什么日志不记录完整用户问题和完整检索资料？

答案：

因为用户问题和检索资料可能包含敏感业务信息。日志只记录 provider、model、耗时、chunk_count、token usage 和错误码等定位信息。

### 自测 6

问题：

第 18 节和第 19 节的边界是什么？

答案：

第 18 节学习如何把检索结果交给模型生成回答。第 19 节学习如何让回答带出处，以及如何设计引用来源格式。

## 八、你应该能口述出的版本

你可以这样向别人解释本节：

```text
第 18 节开始进入 RAG 的 generate 阶段。前面我们已经能检索出 RetrievedChunk，现在要把这些 chunk 变成模型能理解的上下文，再调用模型生成回答。

这一步不是简单把 chunk 原样粘给模型，而是要把每段资料格式化，包括 source、title、section、chunk_id、score 和 content。content 是回答依据，metadata 主要用于背景、调试和后续引用来源。

然后我们构造 system + user messages。system message 规定模型是企业知识库 RAG 问答助手，只能根据资料回答；user prompt 里放用户问题、检索资料和回答规则。如果没有检索资料，就不调用模型，而是直接返回知识库没有足够相关资料，避免模型硬编。

代码上新增 generator.py，里面的 RagAnswerService 只负责生成阶段，不负责检索 Qdrant。测试继续用 fake LLM，验证 messages、模型调用、无资料兜底、错误映射和日志边界。
```

## 九、本节产出

新增：

- `projects/ai-service/app/rag/generator.py`
- `projects/ai-service/tests/test_rag_generator.py`
- `notes/rag-stage4-18-retrieved-context-to-model-answer.md`

修改：

- `README.md`
- `docs/learning-progress.md`
- `docs/learning-resources.md`
- `projects/ai-service/README.md`
- `projects/ai-service/app/rag/README.md`

## 十、参考资料

- [阶段 4 第 15 节：基础 top_k 检索](rag-stage4-15-basic-top-k-retrieval.md)
- [阶段 4 第 16 节：payload filter](rag-stage4-16-payload-filter.md)
- [阶段 4 第 17 节：score_threshold](rag-stage4-17-score-threshold.md)
- [阶段 2 第 5 节：messages 是什么](llm-api-stage2-05-messages-roles.md)
- [阶段 2 第 6 节：prompt 基础](llm-api-stage2-06-prompt-basics.md)
- [阶段 2 第 17 节：测试模型调用](llm-api-stage2-17-testing-model-calls.md)
