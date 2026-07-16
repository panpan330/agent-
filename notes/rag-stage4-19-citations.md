# 阶段 4 第 19 节：引用来源：回答必须带出处

## 本节状态

已完成。

第 18 节我们已经完成了 RAG 的第一版生成链路：

```text
RetrievedChunk
-> 整理成模型可读上下文
-> 调用模型
-> 生成基于资料的中文回答
```

第 19 节继续往前走一步：

```text
回答 answer
+ 引用来源 citations
```

本节的核心不是“让回答看起来更专业”，而是：

```text
让 RAG 回答能追溯到后端实际检索到的知识来源。
```

企业知识库 RAG 不能只回答一句话。它还要让使用者知道：

- 这个答案依据哪份文档。
- 来自哪个章节。
- 对应哪个 chunk。
- 检索分数是多少。
- 后端到底给模型看过哪些资料。

如果回答没有出处，用户很难判断是否可信，开发者也很难排查回答为什么错。

## 本节学习目标

学完本节，你要能讲清楚：

1. 什么是 citation / 引用来源。
2. 为什么企业 RAG 回答必须带出处。
3. citation、metadata、chunk、answer 之间是什么关系。
4. 为什么引用来源不能完全交给模型自己生成。
5. 为什么本节让后端根据 retrieved chunks 生成 citations。
6. 为什么 `answer` 和 `citations` 要分开建模。
7. 本节的 citation 是 chunk 级出处，不是逐句事实校验。
8. `RagCitation` 和 `RagAnswer` 在当前项目里的职责。
9. 为什么没有检索结果时 citations 应该是空列表。
10. 第 19 节和后续 RAG API、无结果处理、安全评测之间的关系。

## 本节暂时不学什么

本节只做最小但完整的“结构化引用来源”能力。

暂时不做：

- 不做 `/rag-chat` HTTP API，后面会把 retriever 和 generator 编排起来。
- 不做前端引用展示。
- 不做逐句引用，也不验证回答中的每一句话分别来自哪个 chunk。
- 不要求模型输出严格的 `[1] [2]` 行内引用。
- 不做 citation 可信度评分算法。
- 不做文档权限安全强化，第 28 节会系统讲 RAG 安全。
- 不做真实模型调用，测试仍然使用 fake LLM client。

## 一、基础知识铺垫

### 1. 什么是 citation

`citation` 可以先理解成：

```text
答案的来源说明。
```

在论文、书籍、法律文件里，citation 通常表示：

```text
这句话或这个观点来自哪本书、哪篇文章、哪条法规、哪一页。
```

在 RAG 系统里，citation 的含义类似，但形态会更工程化：

```text
这个回答参考了哪几个 retrieved chunks。
```

一个简单 citation 可以包含：

```text
source: order-shipping-policy.md
title: 订单发货规则
section: 正常发货时效
chunk_id: order_shipping_policy_chunk_0001
score: 0.91
```

这些信息说明：

- 来源文件是什么。
- 文档标题是什么。
- 来自哪个章节。
- 对应哪个 chunk。
- 检索分数是多少。

你可以把 citation 理解成 RAG 回答背后的“证据索引”。

### 2. 为什么企业 RAG 必须带出处

普通聊天可以只返回一段回答。

企业知识库 RAG 不应该只返回一段回答。

原因有 5 个。

第一，用户需要判断答案是否可信。

如果系统回答：

```text
订单通常会在付款后 24 小时内发货。
```

用户可能会问：

```text
这是从哪里来的？
是最新规则吗？
是售后政策还是物流政策？
```

如果回答同时带出处：

```text
来源：order-shipping-policy.md / 正常发货时效
```

用户会更容易建立信任。

第二，业务人员需要复核。

客服、运营、法务、人事这些场景里，AI 的回答可能会影响真实业务动作。业务人员不能只看一个“听起来合理”的回答，还要能回到原始资料核对。

第三，开发者需要排查问题。

如果回答错了，开发者要判断：

```text
是检索错了？
是 chunk 切分错了？
是 metadata 错了？
是 prompt 没约束好？
是模型把资料理解错了？
```

没有 citation，就很难追踪。

第四，知识库需要持续维护。

如果很多错误回答都来自同一个旧文档，说明要更新文档。

如果很多回答都引用不到来源，说明检索或 metadata 设计有问题。

第五，企业系统需要审计。

在很多公司里，AI 回答不是“聊完就结束”。系统可能要记录：

```text
用户问了什么。
系统检索了哪些资料。
模型回答了什么。
回答引用了哪些来源。
```

这样后续才能复盘、追责、评测和优化。

所以 citation 不是 UI 装饰，它是企业 RAG 的可信工程能力。

### 3. citation 和 source 不是一回事

你可能会觉得：

```text
source 不就是 citation 吗？
```

不完全是。

`source` 通常只是 citation 里的一个字段。

比如：

```text
source = order-shipping-policy.md
```

它只能告诉你来源文件。

但一个完整 citation 往往还需要：

- `title`：文档标题。
- `section`：文档章节。
- `chunk_id`：具体 chunk。
- `score`：本次检索相似度分数。
- `source_index`：模型上下文里的第几份资料。

所以可以这样理解：

```text
source 是来源文件。
citation 是一条结构化来源记录。
```

在本项目里，`RagCitation` 比 `source` 更完整。

### 4. citation 和 metadata 的关系

第 14 节我们系统学过 metadata。

metadata 是 chunk 上携带的结构化描述，例如：

```json
{
  "source": "order-shipping-policy.md",
  "title": "订单发货规则",
  "section": "正常发货时效",
  "doc_type": "policy",
  "business_domain": "order",
  "permission_group": "customer_service"
}
```

第 19 节会从这些 metadata 里抽取一部分字段，形成 citation：

```text
metadata -> citation
```

不是所有 metadata 都适合给用户看。

比如：

- `permission_group` 是权限控制字段，不一定要展示给普通用户。
- `business_domain` 是业务分类字段，可能用于过滤和统计。
- `source/title/section/chunk_id` 更适合做出处。

所以 citation 不是直接把 metadata 原样暴露出去，而是：

```text
从 metadata 中选择适合追溯来源的字段，组成稳定的响应结构。
```

### 5. citation 和 chunk 的关系

当前 RAG 系统的最小检索单位是 chunk。

所以本节的 citation 也是 chunk 级别的。

也就是说：

```text
一个 citation 指向一个 retrieved chunk。
```

为什么不是直接引用整篇文档？

因为整篇文档可能很长。用户看到一个 30 页文档，仍然不知道答案具体来自哪里。

为什么不是直接引用句子？

因为逐句引用需要更复杂的能力：

- 判断回答里的每个关键结论。
- 找到每个结论对应的原文片段。
- 检查模型有没有把多个 chunk 的内容混合。
- 处理同一句回答对应多个来源的情况。

这些以后可以做，但不是第 19 节的最小目标。

本节先做到：

```text
回答引用了哪些检索 chunk。
```

这已经比“只有回答没有出处”强很多。

### 6. citation 和 answer 的关系

RAG 最终返回给用户的内容可以拆成两部分：

```text
answer：自然语言回答
citations：结构化来源列表
```

例如：

```json
{
  "answer": "订单通常会在付款后 24 小时内发货。",
  "citations": [
    {
      "source_index": 1,
      "source": "order-shipping-policy.md",
      "title": "订单发货规则",
      "section": "正常发货时效",
      "chunk_id": "order_shipping_policy_chunk_0001",
      "score": 0.91
    }
  ]
}
```

这里要注意：

```text
answer 是模型生成的。
citations 是后端根据检索结果生成的。
```

这条边界非常重要。

模型擅长组织语言，但不应该完全信任模型来决定真实出处。

后端掌握真实检索结果，所以后端更适合生成 citations。

### 7. 为什么不能完全让模型自己写出处

一个很常见的做法是直接在 prompt 里写：

```text
回答时请带上引用来源。
```

这可以作为辅助，但不能作为唯一可靠机制。

因为模型可能会：

1. 引用不存在的资料编号。
2. 把 `[资料 2]` 写成 `[资料 3]`。
3. 把没有用到的资料也列为来源。
4. 编造不存在的文件名。
5. 把 `source` 改写成一个看起来更正式但并不存在的标题。
6. 在资料不足时仍然给出看似完整的引用。

举个例子。

后端只给了模型：

```text
[资料 1]
source: order-shipping-policy.md
content: 订单付款后通常会在 24 小时内发货。
```

模型可能回答：

```text
订单通常会在付款后 24 小时内发货。[资料 2：物流规则手册]
```

这个引用看起来像真的，但其实是模型编的。

所以本节采用更稳的方式：

```text
模型生成 answer。
后端根据实际 chunks 生成 citations。
```

这不是说以后完全不让模型写行内引用，而是说：

```text
可信来源列表必须由后端掌握。
```

### 8. 后端生成 citations 的好处

后端生成 citations 有几个明显好处。

第一，来源真实。

因为 citations 来自 `RetrievedChunk`，不是模型临时编出来的。

第二，结构稳定。

无论模型怎么回答，后端返回的 citations 字段都是同一种结构。

第三，容易测试。

测试不需要判断模型有没有“聪明地引用”。只要给定 chunks，就能断言 citations 是否正确。

第四，容易做前端展示。

前端可以固定读取：

```text
citations[0].source
citations[0].title
citations[0].section
```

第五，方便审计和日志。

后续如果要记录“本次回答引用了哪些 chunk”，结构化 citations 比自然语言来源更适合存储。

### 9. 后端生成 citations 的局限

后端生成 citations 也不是万能的。

本节的 citations 表示：

```text
这些 chunks 被交给模型作为上下文。
```

它不严格等于：

```text
模型回答里的每一句话都一定准确来自这些 chunks。
```

这是一个很重要的边界。

当前本节能保证：

- citations 来自真实 retrieved chunks。
- 没有 chunks 时 citations 为空。
- citations 不由模型编造。

当前本节不能完全保证：

- 模型一定没有理解错资料。
- 模型回答里的每个结论都能逐句对齐某个 chunk。
- 模型没有混入少量常识。
- citation 和 answer 的每个语义点都一一对应。

这些需要更复杂的评测和校验。

所以你以后要能准确表达：

```text
第 19 节做的是 chunk-level citations，不是 statement-level factual attribution。
```

可以翻译成：

```text
本节做的是 chunk 级来源，不是逐句事实归因。
```

### 10. 为什么 citations 不能替代权限控制

有些人会误以为：

```text
只要回答带出处，就安全了。
```

不对。

citations 只说明答案参考了哪些资料，不负责判断用户有没有权限看这些资料。

权限控制应该在检索阶段做：

```text
payload filter 根据 permission_group 限定可检索资料。
```

如果权限过滤做错了，后端可能会把不该看的 chunk 交给模型。即使 citations 正确显示来源，也已经泄露了资料。

所以要记住：

```text
权限过滤在 citations 之前。
citations 不是权限系统。
```

### 11. score 不是证据强度

本节 citation 会带 `score`。

但你必须理解：

```text
score 是检索相似度，不是答案正确率。
```

score 高只能说明：

```text
这个 chunk 和 query 在当前 embedding/向量库规则下比较相似。
```

它不能说明：

- chunk 内容一定正确。
- chunk 一定是最新规则。
- 模型回答一定忠实。
- 用户问题一定被完全回答。

所以 `score` 适合调试和评测，不适合直接对用户说：

```text
这个答案可信度 91%。
```

本节把 score 放在 citation 里，是为了后续开发和排查，不是为了把它当成业务事实。

### 12. citation 质量依赖 metadata 质量

如果 metadata 写得差，citation 也会差。

比如 chunk metadata 是：

```json
{
  "source": "file1.md",
  "title": "",
  "section": ""
}
```

那 citation 就很难展示清楚。

如果 metadata 是：

```json
{
  "source": "order-shipping-policy.md",
  "title": "订单发货规则",
  "section": "正常发货时效"
}
```

citation 就会更可读。

所以第 14 节 metadata 设计不是孤立知识。

它会直接影响：

- payload filter。
- citation 展示。
- 排查检索结果。
- 评测数据分析。
- 文档更新和重建索引。

RAG 很多后续能力，本质都依赖前面 metadata 是否设计扎实。

### 13. citation 的两种常见展示方式

RAG 产品里常见两种展示方式。

第一种是独立来源列表。

回答下面列出：

```text
参考来源：
1. 订单发货规则 / 正常发货时效 / order-shipping-policy.md
2. 物流查询 FAQ / 异常物流说明 / logistics-tracking-faq.txt
```

本节做的就是这类结构化来源列表的后端基础。

第二种是行内引用。

回答里直接带：

```text
订单通常会在付款后 24 小时内发货。[1]
促销高峰期可能延迟。[2]
```

行内引用更精细，但难度也更高。

因为你要保证 `[1]` 真的对应这句话的证据，而不是模型随手放的编号。

本节先做第一种，后续可以在它之上继续增强。

### 14. citation 在 RAG 调试中的作用

当用户说：

```text
这个回答不对。
```

你不能只盯着 answer。

你要看 citations。

排查顺序可以是：

1. citations 里是否有相关文档？
2. source 是否正确？
3. section 是否正确？
4. chunk 内容是否真的支持回答？
5. score 是否太低？
6. 是否有更相关的 chunk 没被检索出来？
7. 模型是否把 chunk 内容理解错？

如果 citations 指向的资料本身就不相关，那问题在 retrieve。

如果 citations 指向的资料是对的，但 answer 错了，那问题更可能在 generate 或 prompt。

所以 citation 也是 RAG 调试的入口。

### 15. citation 与“可信 AI”的关系

企业使用 AI 时，经常关心一个问题：

```text
这个回答能不能信？
```

RAG 的 citation 不会让答案自动变成真理，但它能让答案变得可检查。

可信不是一句口号，而是工程能力：

- 能看到依据。
- 能回到原文。
- 能发现错误。
- 能修正文档。
- 能评测效果。
- 能审计链路。

所以本节虽然代码不多，但思想很重要。

它是从“模型会回答”走向“回答可追溯”的一步。

## 二、本节主题系统讲解

### 1. 第 19 节在 RAG 主线里的位置

目前主线已经走到：

```text
load
-> split
-> embed
-> store
-> retrieve
-> generate answer
```

第 19 节补上：

```text
generate answer with citations
```

更完整地看：

```text
用户问题
-> retriever 返回 RetrievedChunk 列表
-> generator 把 chunks 放进 prompt
-> 模型生成 answer
-> 后端把 chunks 转成 citations
-> 返回 RagAnswer(answer, citations)
```

这一步让 RAG 回答从：

```text
一段自然语言
```

升级为：

```text
自然语言回答 + 可追溯来源列表
```

### 2. 本节新增的数据模型

本节新增两个 Pydantic 模型：

```python
class RagCitation(BaseModel):
    source_index: int
    source: str
    title: str | None
    section: str | None
    chunk_id: str
    score: float
```

以及：

```python
class RagAnswer(BaseModel):
    answer: str
    citations: list[RagCitation]
```

为什么用 Pydantic？

因为 citations 以后很可能会作为 API 响应的一部分。

Pydantic 能带来：

- 字段类型清楚。
- 空值规则清楚。
- 最小长度等约束清楚。
- 后续接 FastAPI response model 更自然。
- 测试断言更稳定。

这里不是为了“多写类”，而是为了把输出结构固定下来。

### 3. `RagCitation` 每个字段的含义

`source_index`：

```text
从 1 开始的资料编号，对应 prompt 里的 [资料 1]、[资料 2]。
```

它的作用是把 citation 和模型上下文里的资料编号对齐。

`source`：

```text
来源文件或来源标识。
```

比如：

```text
order-shipping-policy.md
```

`title`：

```text
文档标题。
```

比如：

```text
订单发货规则
```

`section`：

```text
chunk 所在章节。
```

比如：

```text
正常发货时效
```

`chunk_id`：

```text
稳定 chunk 标识。
```

用于开发排查、重建索引、定位原始 chunk。

`score`：

```text
本次检索返回的相似度分数。
```

用于调试，不代表答案正确率。

### 4. 为什么 `title` 和 `section` 允许为空

真实文档不一定都有完整 metadata。

比如：

- 某个 txt 文件没有标题。
- 某段文本没有明显章节。
- 旧数据入库时 metadata 不完整。

如果 `title` 和 `section` 强制必填，系统会因为可展示信息缺失而直接失败。

本节选择：

```text
source 必须有兜底。
title/section 可以为 None。
```

原因是：

```text
source 是最基础的来源定位。
title/section 是增强可读性。
```

这是一种更稳的工程取舍。

### 5. 为什么 `source_index` 从 1 开始

代码里资料编号使用：

```text
[资料 1]
[资料 2]
```

而不是：

```text
[资料 0]
[资料 1]
```

因为给人看的编号通常从 1 开始。

这样后续用户看到：

```text
参考资料 1
```

更自然。

内部列表下标从 0 开始没问题，但对外展示编号用 1 更友好。

所以本节对 `source_index` 做了 `ge=1` 约束，也手动拒绝小于等于 0 的 index。

### 6. citation 构造为什么是函数

本节新增：

```python
build_rag_citation(index, chunk)
build_rag_citations(chunks)
```

为什么不在 `generate_answer_with_citations()` 里面直接写列表推导？

因为 citation 构造是一条独立规则。

它未来可能被多个地方复用：

- RAG API 响应。
- 日志审计。
- 调试工具。
- RAG 评测。
- 前端预览。

抽成函数后，测试也更清楚：

```text
给定一个 RetrievedChunk，应该生成什么 citation。
```

这比只在 service 测试里间接验证更容易理解。

### 7. 本节 prompt 为什么也要微调

第 18 节 prompt 里写的是：

```text
当前阶段先生成自然语言回答，引用来源会在后续小节单独学习。
```

第 19 节已经开始学引用来源，所以这句话过时了。

本节改成：

```text
可以按需要在回答中提到资料编号，但不要编造文件名、链接或不存在的出处。
最终引用来源由后端根据检索资料单独返回。
```

这两句话表达了两个边界。

第一，模型不要编造来源。

第二，真正结构化 citations 由后端返回。

这不是完全禁止模型写 `[资料 1]`，但不把模型的自然语言引用当成可信来源。

可信来源列表来自后端。

### 8. `generate_answer_with_citations()` 的流程

新增方法：

```python
generate_answer_with_citations(query, chunks=[...])
```

流程是：

```text
调用 generate_answer(query, chunks=chunks)
-> 得到 answer
-> build_rag_citations(chunks)
-> 返回 RagAnswer(answer=answer, citations=citations)
```

为什么复用 `generate_answer()`？

因为第 18 节已经把生成回答的逻辑做好了：

- 空问题校验。
- 无 chunks 兜底。
- API key 检查。
- messages 构造。
- 模型调用。
- 错误映射。
- 日志记录。

第 19 节不需要重写这些逻辑。

本节只是在回答外面加上 citations。

这体现了一个工程原则：

```text
新增能力尽量复用已有稳定边界，不要为了一个新字段重写整条链路。
```

### 9. 没有 chunks 时 citations 为什么为空

如果检索结果为空：

```text
chunks = []
```

第 18 节会返回：

```text
当前知识库没有找到足够相关的资料，无法根据知识库回答这个问题。
```

第 19 节在这种情况下应该返回：

```json
{
  "answer": "当前知识库没有找到足够相关的资料，无法根据知识库回答这个问题。",
  "citations": []
}
```

为什么 citations 为空？

因为没有任何检索资料可以引用。

不能为了格式好看返回一个假的来源。

这也是一个重要原则：

```text
没有证据，就不要伪造证据。
```

### 10. 本节为什么不做“只返回模型真正用到的 citations”

你可能会问：

```text
如果 top_k 返回了 3 个 chunk，但模型回答只用到第 1 个，那 citations 是否应该只返回第 1 个？
```

这是一个好问题，但本节暂时不做。

原因是：

```text
后端现在还不能可靠判断模型到底用到了哪些 chunk。
```

模型可能读了 3 个 chunk，其中一个主用，另两个辅助判断。

如果让模型自己说“我用了哪些来源”，又会回到模型可能编造引用的问题。

所以本节选择一个更稳的最小语义：

```text
citations 表示本次回答可参考的检索上下文来源。
```

以后如果要做到“模型实际使用来源”，需要更复杂的引用校验或结构化生成策略。

### 11. 本节为什么还不做 API

本节仍然只改内部 RAG 模块。

原因是当前要先把两个内部能力打稳：

```text
generate_answer()
generate_answer_with_citations()
```

如果现在直接做 API，会同时引入：

- 请求体模型。
- response_model。
- retriever 和 generator 依赖注入。
- Qdrant 是否启动。
- `.env` 模型配置。
- 空结果响应。
- 错误处理。

这些都会分散第 19 节的主题。

后面做 `/rag-chat` 时，API 层直接复用 `RagAnswer` 会更自然。

### 12. 第 19 节完成后，RAG 回答链路长什么样

从内部能力看，现在链路可以表达成：

```text
RetrievedChunk 列表
-> build_rag_messages()
-> 模型生成 answer
-> build_rag_citations()
-> RagAnswer(answer, citations)
```

从学习地图看：

```text
第 18 节：能回答
第 19 节：回答带出处
第 20 节：无检索结果时的完整处理策略
第 21 节：RAG 异常处理
第 22 节：RAG fake 测试体系
```

本节是 RAG 从“回答”走向“可信回答”的基础步骤。

## 三、本节代码改动说明

### 1. 新增 `RagCitation`

位置：

```text
projects/ai-service/app/rag/generator.py
```

`RagCitation` 表示一条结构化引用来源。

学习重点不是字段很多，而是职责清楚：

```text
RagCitation 不保存完整 chunk 正文。
RagCitation 保存足够追溯来源的信息。
```

为什么不把完整 `content` 放进 citation？

因为 citation 是来源索引，不是重新返回整段资料正文。

后续如果前端需要展示原文片段，可以单独设计 `snippet` 或原文预览字段，但这不是本节目标。

### 2. 新增 `RagAnswer`

`RagAnswer` 把回答和来源放在一起：

```python
answer: str
citations: list[RagCitation]
```

这为后续 API 响应打基础。

以前只有：

```text
str
```

现在可以表达：

```text
回答是什么。
来源有哪些。
```

### 3. 新增 metadata 文本清洗辅助函数

本节新增了两个小函数：

```python
_optional_metadata_text(value)
_required_metadata_text(value, fallback)
```

它们的作用是把 metadata 值转成适合 citation 的字符串。

例如：

- 空字符串转成 `None`。
- 缺失的 `source` 使用 `unknown-source` 兜底。
- 数字或布尔值也能安全转成字符串。

这里不需要过度展开代码语法，你只要理解目的：

```text
citation 面向结构化输出，不能把空字符串当成有效标题。
```

### 4. 新增 `build_rag_citation()`

这个函数做一件事：

```text
把一个 RetrievedChunk 转成一个 RagCitation。
```

它从 chunk 里取：

- `metadata["source"]`
- `metadata["title"]`
- `metadata["section"]`
- `chunk.chunk_id`
- `chunk.score`

再加上当前资料编号 `source_index`。

这个函数体现了本节最重要的边界：

```text
citation 来自后端真实 RetrievedChunk，不来自模型输出。
```

### 5. 新增 `build_rag_citations()`

这个函数把多个 chunks 转成 citations：

```text
[chunk1, chunk2]
-> [citation1, citation2]
```

并且自动从 1 开始编号。

它让 service 代码保持简单：

```text
只需要调用 build_rag_citations(chunks)
```

不用在业务流程里重复写编号逻辑。

### 6. 修改 `build_rag_user_prompt()`

本节把 prompt 里的引用规则改成：

```text
可以按需要在回答中提到资料编号，但不要编造文件名、链接或不存在的出处。
最终引用来源由后端根据检索资料单独返回。
```

这句话让模型知道：

- 不能编造来源。
- 后端会单独处理结构化来源。

但它不把 citation 可信性建立在模型文本上。

### 7. 新增 `generate_answer_with_citations()`

这个方法返回：

```python
RagAnswer
```

而不是普通字符串。

它适合后续 RAG API 使用。

保留 `generate_answer()` 的原因是：

- 第 18 节能力仍然有用。
- 有些内部场景可能只需要 answer 字符串。
- 避免一次改动影响太大。

## 四、本节测试说明

本节新增和调整了 `tests/test_rag_generator.py`。

重要测试包括：

1. `test_build_rag_citation_uses_backend_retrieved_metadata`

验证 citation 来自 chunk metadata，而不是模型输出。

2. `test_build_rag_citation_uses_fallback_for_missing_source`

验证 source 缺失时有稳定兜底，空 title/section 不会伪装成有效内容。

3. `test_build_rag_citations_numbers_retrieved_chunks`

验证多个 chunks 会生成从 1 开始的 `source_index`。

4. `test_rag_answer_service_returns_answer_with_backend_citations`

验证 service 会返回 answer 和 citations，并且只调用一次 fake model。

5. `test_rag_answer_service_returns_empty_citations_without_context`

验证没有检索结果时不调用模型，citations 为空。

这些测试不证明真实模型回答质量。

它们保护的是工程边界：

```text
来源由后端生成。
结构稳定。
空结果不伪造出处。
模型调用仍然可控。
```

## 五、常见误区

### 误区 1：回答带了出处就一定正确

不对。

出处说明答案参考了哪些资料，但不自动保证模型理解完全正确。

还需要检索质量、prompt、评测和安全校验。

### 误区 2：让模型在回答里写 `[1]` 就算完成 citations

不够。

模型可能写错编号、编造来源或引用没有用到的资料。

本节更重视后端结构化 citations。

### 误区 3：citation 就是 source 字段

不完整。

source 只是来源文件。citation 还包含 title、section、chunk_id、score、source_index 等信息。

### 误区 4：score 越高答案越正确

不一定。

score 是检索相似度，不是答案正确率。

### 误区 5：citations 可以替代权限过滤

不可以。

权限过滤必须在检索阶段完成。citation 只是说明引用了哪些资料，不能阻止越权资料进入模型上下文。

### 误区 6：后端生成 citations 就能知道模型真正用了哪些资料

当前还不能。

本节 citations 表示被提供给模型的检索上下文来源，不是逐句使用证明。

## 六、本节练习

### 练习 1：解释 citation 的作用

题目：

请用自己的话解释 RAG 里的 citation 是什么，为什么企业知识库问答需要它。

参考答案：

citation 是答案的结构化来源说明，用来告诉用户和开发者回答参考了哪些知识库资料。企业 RAG 需要 citation，因为用户要判断答案是否可信，业务人员要复核原文，开发者要排查错误，系统也需要审计和评测回答链路。

### 练习 2：判断字段职责

题目：

下面字段中，哪些更适合放进 citation？哪些更适合用于权限过滤？

```text
source
title
section
chunk_id
score
permission_group
business_domain
```

参考答案：

`source`、`title`、`section`、`chunk_id`、`score` 更适合放进 citation，其中 score 主要用于调试。`permission_group` 更适合用于权限过滤。`business_domain` 可以用于过滤、统计和内部分类，是否展示给用户要看产品设计。

### 练习 3：为什么 citations 不交给模型生成

题目：

为什么不能只靠 prompt 要求模型“回答时带出处”？

参考答案：

因为模型可能编造不存在的来源、引用错误编号、把没有用到的资料列为来源，或者把 source 改写成不存在的标题。后端掌握真实 retrieved chunks，所以可信的结构化 citations 应该由后端根据检索结果生成。

### 练习 4：空结果时 citations 应该是什么

题目：

如果 `chunks=[]`，返回的 citations 应该是什么？为什么？

参考答案：

应该是空列表 `[]`。因为没有任何检索资料可以作为来源，不能为了格式完整而伪造出处。

### 练习 5：chunk 级 citation 的边界

题目：

本节的 chunk 级 citation 能保证什么？不能保证什么？

参考答案：

能保证 citations 来自后端实际检索到并提供给模型的 chunks，不是模型编造的。不能保证模型回答里的每一句话都逐句准确对应某个 chunk，也不能保证模型没有理解错资料。这些需要后续更细的引用校验和评测。

## 七、自测问题

### 自测 1

问题：

`RagCitation` 是模型生成的吗？

答案：

不是。`RagCitation` 由后端根据 `RetrievedChunk` 的 metadata、chunk_id 和 score 生成。

### 自测 2

问题：

`RagAnswer` 为什么要包含 `answer` 和 `citations` 两部分？

答案：

因为自然语言回答和结构化来源是两类信息。answer 负责给用户解释问题，citations 负责追溯回答参考了哪些资料。

### 自测 3

问题：

`source_index` 为什么从 1 开始？

答案：

因为它对应 prompt 里的 `[资料 1]`、`[资料 2]`，给人看的编号从 1 开始更自然。

### 自测 4

问题：

`score` 能不能理解为“答案正确率”？

答案：

不能。score 是检索相似度，不是答案正确率。

### 自测 5

问题：

没有检索结果时，为什么不能返回一个默认 citation？

答案：

因为 citation 表示真实来源。没有检索结果就没有来源，返回默认 citation 会伪造证据。

### 自测 6

问题：

本节的 citations 能不能替代权限过滤？

答案：

不能。权限过滤必须在检索阶段通过 payload filter 等方式完成，citations 只是来源展示和追溯。

### 自测 7

问题：

本节是否实现了逐句引用？

答案：

没有。本节实现的是 chunk 级结构化来源列表，不是逐句引用校验。

### 自测 8

问题：

为什么 prompt 里仍然提醒模型不要编造文件名、链接或不存在的出处？

答案：

因为模型可能在自然语言回答里提到来源。虽然最终结构化 citations 由后端返回，但 prompt 仍然要减少模型在回答文本里编造来源的概率。

## 八、你应该能口述出的版本

你可以这样向别人解释本节：

```text
第 19 节解决的是 RAG 回答的出处问题。第 18 节我们已经能把检索到的 RetrievedChunk 交给模型生成回答，但只有 answer 不够，企业知识库问答还需要知道答案参考了哪些资料。

本节新增 RagCitation 和 RagAnswer。RagCitation 保存 source_index、source、title、section、chunk_id 和 score，表示一个 chunk 级来源。RagAnswer 包含 answer 和 citations 两部分。answer 由模型生成，citations 由后端根据真实 retrieved chunks 生成。

这样做的关键是避免模型自己编造来源。模型擅长组织语言，但它可能写错资料编号、编造文件名或引用不存在的来源。后端掌握真实检索结果，所以可信的 citations 应该由后端构造。

本节实现的是 chunk 级 citation，不是逐句引用校验。它能说明本次回答参考了哪些检索上下文，但不能保证回答里的每句话都逐句对应某个 chunk。后续还会继续学习无结果处理、RAG 异常、测试、安全和评测。
```

## 九、本节产出

新增：

- `notes/rag-stage4-19-citations.md`

修改：

- `projects/ai-service/app/rag/generator.py`
- `projects/ai-service/tests/test_rag_generator.py`
- `README.md`
- `docs/learning-progress.md`
- `docs/learning-resources.md`
- `projects/ai-service/README.md`
- `projects/ai-service/app/rag/README.md`

## 十、参考资料

- [阶段 4 第 14 节：metadata 设计](rag-stage4-14-metadata-design.md)
- [阶段 4 第 15 节：基础 top_k 检索](rag-stage4-15-basic-top-k-retrieval.md)
- [阶段 4 第 16 节：payload filter](rag-stage4-16-payload-filter.md)
- [阶段 4 第 17 节：score_threshold](rag-stage4-17-score-threshold.md)
- [阶段 4 第 18 节：把检索结果交给模型回答](rag-stage4-18-retrieved-context-to-model-answer.md)
- [阶段 2 第 16 节：Pydantic 约束结构化输出](llm-api-stage2-16-pydantic-structured-output.md)
