# 阶段 4 第 25 节：检索质量调优：chunk size、overlap、top_k、score_threshold

## 本节状态

已完成。

前面我们已经能跑通一条基础 RAG 链路：

```text
load
-> split
-> embed
-> store
-> retrieve
-> generate
-> citations
-> no_context
-> errors
-> tests
```

第 25 节开始解决一个更贴近真实项目的问题：

> 为什么 RAG 有时候搜不到、搜偏了、搜太多、搜太少？

这不是模型“聪明不聪明”一个因素决定的。

RAG 回答质量很大一部分取决于检索质量。

检索质量又受到多组参数影响：

- `chunk_size`
- `chunk_overlap`
- `top_k`
- `score_threshold`
- metadata filter
- embedding 模型
- query 写法
- 文档质量

本节先集中学习最基础、最常见的四个参数：

```text
chunk_size
chunk_overlap
top_k
score_threshold
```

其中：

```text
chunk_size / chunk_overlap 是入库前的切分参数。
top_k / score_threshold 是查询时的检索参数。
```

这两类参数不能混为一谈。

本节新增了 RAG 调优辅助模块：

- `projects/ai-service/app/rag/tuning.py`

它可以做两件事：

- 对比不同 chunk 切分参数产生的 chunk 数量和长度分布
- 对比不同检索参数产生的检索结果数量、分数范围和来源分布

本节还新增了一个不需要 Qdrant 的本地脚本：

- `projects/ai-service/scripts/rag_chunk_tuning_preview.py`

它只观察 chunk 切分效果，不连接真实向量库，不需要打开 VMware。

## 本节学习目标

学完本节，你应该能讲清楚：

1. 为什么 RAG 质量不能只看大模型回答。
2. `chunk_size` 太大或太小分别有什么问题。
3. `chunk_overlap` 解决什么问题，又会带来什么副作用。
4. `top_k` 太大或太小分别有什么影响。
5. `score_threshold` 太高或太低分别有什么影响。
6. 哪些参数属于入库阶段，哪些参数属于查询阶段。
7. 为什么调 chunk 参数通常需要重新入库。
8. 为什么调 `top_k` 和 `score_threshold` 不一定需要重新入库。
9. 为什么调优要看检索结果，而不是只看最终回答。
10. 如何用结构化 report 观察参数变化带来的影响。

## 本节暂时不学什么

本节暂时不做：

- 不做真实 embedding 模型质量对比。
- 不做 RAG 自动评测集。
- 不做人工标注 golden dataset。
- 不做混合检索。
- 不做 rerank。
- 不做 query rewriting。
- 不做复杂召回率/准确率指标。
- 不真实调用大模型。
- 不要求打开 VMware。

这些后面会继续学。

本节先掌握最基础的参数调优思路。

## 一、基础知识铺垫

### 1. RAG 回答质量先取决于检索质量

RAG 的回答大致分两步：

```text
先检索资料
再让模型基于资料回答
```

如果第一步检索错了，第二步再强也很难救。

比如用户问：

```text
退款多久能到账？
```

如果检索出来的是：

```text
账号安全验证规则
```

那模型就算表达能力很强，也没有正确依据。

所以 RAG 调优时不能只看最终答案。

要先看：

```text
检索出来的 chunk 对不对？
分数高不高？
来源是不是应该出现的文档？
有没有漏掉关键文档？
有没有混入噪声？
```

### 2. 检索质量不是一个参数决定的

很多新手会问：

```text
top_k 应该设成几？
chunk_size 应该设成多少？
score_threshold 应该设多少？
```

这些问题没有固定答案。

因为它们取决于：

- 文档类型
- 文档长度
- 用户问题类型
- embedding 模型
- 业务容错程度
- 是否需要引用来源
- 模型上下文窗口
- 成本预算

所以调优不是背一个标准值。

调优是观察、对比、记录、验证。

### 3. 入库参数和查询参数要分清

本节最重要的边界之一：

```text
chunk_size / chunk_overlap 是入库参数。
top_k / score_threshold 是查询参数。
```

入库参数决定：

```text
文档怎么被切成 chunks
每个 chunk 内容长什么样
每个 chunk 的 embedding 是什么
向量库里存了多少 points
```

查询参数决定：

```text
从向量库里取多少结果
低于什么分数的结果不要
```

所以：

```text
改 chunk_size / overlap 通常要重新切分、重新 embedding、重新入库。
改 top_k / score_threshold 通常只影响查询，不一定要重新入库。
```

### 4. chunk_size 是什么

`chunk_size` 表示单个 chunk 大概允许多长。

当前项目按字符数做基础切分。

例如：

```text
chunk_size = 220
```

表示切分器会尽量让每个 chunk 不超过 220 个字符。

真实项目里也可能按 token 切分。

当前阶段先用字符数，便于学习和测试。

### 5. chunk 太小的问题

chunk 太小，会导致上下文不完整。

例如原文是：

```text
用户申请退款后，客服需要先确认订单状态。
如果订单已经发货，需要走退货退款流程。
如果订单未发货，可以直接申请取消订单退款。
```

如果切得太碎，可能变成：

```text
chunk 1：用户申请退款后，客服需要先确认订单状态。
chunk 2：如果订单已经发货，需要走退货退款流程。
chunk 3：如果订单未发货，可以直接申请取消订单退款。
```

用户问：

```text
已发货订单怎么退款？
```

如果只召回 chunk 2，模型可能不知道前面的“客服需要先确认订单状态”。

所以 chunk 太小容易丢上下文。

### 6. chunk 太大的问题

chunk 太大，会把多个主题混在一起。

例如一个 chunk 里同时包含：

```text
发货规则
退款规则
账号安全
物流查询
```

用户问退款，向量可能因为 chunk 里包含退款词而召回。

但这个 chunk 同时带着很多无关内容。

模型拿到后可能：

- 注意力被噪声干扰
- 引用来源不够精确
- 回答变啰嗦
- 上下文 token 成本变高

所以 chunk 太大也不好。

### 7. chunk_size 的基本取舍

你可以先用这句话记住：

```text
chunk_size 太小容易信息不完整，太大容易语义混杂。
```

实际调优时要观察：

- 每个 chunk 是否能独立表达一个相对完整知识点
- chunk 是否包含过多无关主题
- 用户问题是否能召回关键 chunk
- 引用来源是否足够具体

### 8. chunk_overlap 是什么

`chunk_overlap` 表示相邻 chunk 之间保留一部分重复内容。

它的目的不是制造重复。

它是为了避免关键信息刚好被切断。

例如：

```text
chunk 1 结尾：如果订单已经发货
chunk 2 开头：需要走退货退款流程
```

如果没有 overlap，两个片段被拆开后，单独看都不完整。

overlap 可以让相邻 chunk 有一些上下文交叠。

### 9. overlap 的好处

overlap 的主要好处是：

- 保留跨边界上下文
- 降低关键信息被切断的概率
- 提高某些问题的召回机会
- 让 chunk 更容易独立被模型理解

尤其是长段落或长列表内容，overlap 有价值。

### 10. overlap 的副作用

overlap 也有副作用：

- chunk 数量变多
- embedding 成本增加
- 向量库存储增加
- 检索结果更容易重复
- 模型上下文里可能出现重复内容

所以 overlap 不是越大越好。

如果 overlap 接近 chunk_size，就会制造大量重复。

当前 splitter 也明确禁止：

```text
chunk_overlap >= chunk_size
```

### 11. top_k 是什么

`top_k` 表示从向量库里取最相似的前 K 个结果。

例如：

```text
top_k = 3
```

表示最多取 3 个 chunks。

top_k 控制的是召回数量。

### 12. top_k 太小的问题

top_k 太小，可能漏掉关键资料。

例如用户问：

```text
已发货订单退款，运费谁承担？
```

可能需要同时召回：

- 退款规则
- 退货规则
- 运费规则

如果 `top_k=1`，只取一个 chunk，答案可能不完整。

### 13. top_k 太大的问题

top_k 太大，会带来噪声。

如果 `top_k=10`，模型可能拿到很多相关性一般的 chunks。

这些 chunks 会：

- 占用上下文窗口
- 增加 token 成本
- 干扰模型判断
- 让引用来源变多但不精确

所以 top_k 不是越大越好。

### 14. score_threshold 是什么

`score_threshold` 是最低相关分数门槛。

例如：

```text
score_threshold = 0.75
```

表示低于这个分数的结果不要。

它服务于一个目标：

```text
低相关内容不要硬塞给模型。
```

如果没有阈值，向量库可能总会返回 top_k 个结果。

即使这些结果都不太相关。

### 15. threshold 太低的问题

threshold 太低，会让低相关内容进入上下文。

这会导致：

- 模型基于不相关资料回答
- no_context 触发太少
- 看似有资料，其实资料很牵强
- 答案更容易幻觉

比如用户问：

```text
会员积分怎么兑换？
```

知识库里没有会员积分文档。

如果 threshold 很低，可能仍然召回退款、发货、账号安全文档。

模型就可能硬答。

### 16. threshold 太高的问题

threshold 太高，会过滤掉本来可用的资料。

这会导致：

- no_context 过多
- 用户明明问的是知识库内容，却被拒答
- 系统显得“什么都不知道”

所以 threshold 要结合实际分数分布调。

### 17. score 分数不能跨模型盲目比较

不同 embedding 模型、不同距离度量、不同数据集，score 分布可能不同。

所以不要认为：

```text
0.8 永远是高相关
0.5 永远是低相关
```

你要看当前系统里的真实分布。

这也是为什么本节新增调优报告。

它能帮助观察：

```text
不同 threshold 下还剩多少结果
top_score 和 bottom_score 是多少
来源分布是什么
```

### 18. 为什么调优要看来源分布

如果用户问订单发货，但检索来源都是：

```text
account-security-faq.md
refund-return-policy.md
```

那就说明检索偏了。

来源分布能快速帮助你判断：

```text
检索结果是不是来自应该出现的文档？
是不是混入太多其他业务域？
```

这比只看分数更直观。

### 19. 为什么调优要看 chunk_id

`chunk_id` 能告诉你具体命中了哪个 chunk。

如果同一个问题每次都命中不同 chunk，说明检索可能不稳定。

如果 top_k 里出现很多同一文档相邻 chunk，说明 overlap 或 chunk 切分可能导致重复。

所以调优报告里保留了：

```text
chunk_ids
debug_lines
```

### 20. 为什么最终答案不是唯一判断标准

最终答案很重要，但不能作为唯一标准。

因为模型有时能“猜对”。

它可能在检索资料不完美的情况下，凭通用知识写出看似合理的答案。

如果只看答案，你可能误以为检索没问题。

所以 RAG 调优顺序应该是：

```text
先看检索结果
再看模型回答
最后看引用来源是否支撑回答
```

### 21. 本节为什么不真实调用大模型

本节学习的是检索参数。

如果同时真实调用大模型，会引入额外变量：

- prompt 写法
- 模型输出随机性
- 模型是否善于总结
- 模型是否遵守引用
- API 延迟和费用

为了把学习焦点放在检索，本节不真实调用大模型。

### 22. 本节为什么不要求真实 embedding

真实 embedding 会让检索效果更接近真实项目。

但本节先学习调优思路和工具结构。

即使用 fake/deterministic embedding，也能理解：

- chunk 参数是入库参数
- top_k 是结果数量控制
- threshold 是低相关过滤
- report 怎么观察参数影响

真实 embedding 后续可以替换进去。

调优方法仍然适用。

## 二、本节主题系统讲解

### 1. 第 25 节在阶段 4 里的位置

第 25 节接在第 24 节之后。

第 24 节讲：

```text
embedding 模型、维度、成本和批量
```

第 25 节讲：

```text
即使 embedding 能用了，检索参数怎么调？
```

它标志着我们从“能跑通 RAG”进入“开始观察 RAG 质量”。

### 2. 本节新增 `app/rag/tuning.py`

这个文件不是生产 API。

它是 RAG 学习和调试辅助模块。

它负责生成结构化 report，帮助我们观察参数影响。

新增的核心模型：

- `ChunkTuningCase`
- `ChunkTuningReport`
- `RetrievalTuningCase`
- `RetrievalTuningReport`

新增的核心函数：

- `build_chunk_tuning_report()`
- `compare_chunk_tuning_cases()`
- `build_retrieval_tuning_cases()`
- `build_retrieval_tuning_report()`
- `compare_retrieval_tuning_cases()`

### 3. `ChunkTuningCase` 表示什么

`ChunkTuningCase` 表示一组切分参数：

```python
ChunkTuningCase(
    chunk_size=220,
    chunk_overlap=40,
)
```

它有校验：

```text
chunk_size > 0
chunk_overlap >= 0
chunk_overlap < chunk_size
```

这是为了避免无意义切分。

### 4. `ChunkTuningReport` 表示什么

`ChunkTuningReport` 表示一组切分参数产生的结果统计：

```text
document_count
chunk_count
min_chunk_chars
max_chunk_chars
average_chunk_chars
source_count
```

它不判断“好坏”。

它只把现象结构化展示出来。

调优时先看现象，再结合业务判断。

### 5. `build_chunk_tuning_report()` 做什么

它做的事是：

```text
documents
-> split_documents_into_chunks(...)
-> 统计 chunk 数量和长度分布
-> 返回 ChunkTuningReport
```

它不生成 embedding，也不写入 Qdrant。

所以它不需要 VMware。

### 6. `compare_chunk_tuning_cases()` 做什么

它接收多组 `ChunkTuningCase`：

```python
[
    ChunkTuningCase(chunk_size=180, chunk_overlap=20),
    ChunkTuningCase(chunk_size=260, chunk_overlap=40),
    ChunkTuningCase(chunk_size=420, chunk_overlap=80),
]
```

然后返回多份 report。

你可以观察：

```text
chunk_size 变大后，chunk_count 是否减少？
overlap 变大后，平均 chunk 长度是否变化？
某些参数是否切出太短的 chunk？
```

### 7. `RetrievalTuningCase` 表示什么

`RetrievalTuningCase` 表示一组查询参数：

```python
RetrievalTuningCase(
    top_k=3,
    score_threshold=0.8,
)
```

它控制：

```text
最多取几个结果
低于什么分数的结果不要
```

### 8. `build_retrieval_tuning_cases()` 做什么

它用来生成参数网格。

例如：

```python
build_retrieval_tuning_cases(
    top_ks=[1, 3],
    score_thresholds=[None, 0.8],
)
```

得到：

```text
top_k=1 threshold=None
top_k=1 threshold=0.8
top_k=3 threshold=None
top_k=3 threshold=0.8
```

这就是最基础的参数组合对比。

### 9. `RetrievalTuningReport` 表示什么

它记录一组检索参数下的检索结果摘要：

```text
query
top_k
score_threshold
result_count
source_count
top_score
bottom_score
sources
chunk_ids
debug_lines
```

它不是评测指标。

它是调试报告。

它帮助你快速回答：

```text
这组参数返回了几个结果？
最高分和最低分是多少？
来源有几个？
命中了哪些 chunk？
```

### 10. `compare_retrieval_tuning_cases()` 做什么

它会对每组 `RetrievalTuningCase` 调用一次 `retrieve_top_k()`。

然后把结果转成 `RetrievalTuningReport`。

这意味着它复用了当前项目已有的检索链路：

```text
query
-> embedding
-> payload filter
-> vector store query
-> RetrievedChunk
-> tuning report
```

### 11. 为什么调优模块不直接写 API

本节先写内部模块，不急着暴露 HTTP API。

原因是：

- 调优是内部开发动作
- 当前还没有前端调试界面
- 先把核心逻辑和报告结构稳定下来
- 后续需要时可以再接 FastAPI route

这符合“先核心逻辑，后接口暴露”的顺序。

### 12. FakeVectorStoreReader 为什么要支持 top_k 和 threshold

上一节 fake reader 主要记录参数。

第 25 节为了让调优报告能在单元测试中观察参数影响，我们让它更接近真实向量库行为：

```text
按 score 从高到低排序
按 score_threshold 过滤
按 top_k 截断
```

这样不用真实 Qdrant，也能测试：

```text
top_k=1 返回 1 个
threshold=0.8 过滤低分结果
```

注意它只是 fake，不代表真实向量库所有细节。

### 13. `rag_chunk_tuning_preview.py` 做什么

脚本位置：

```text
projects/ai-service/scripts/rag_chunk_tuning_preview.py
```

它会加载本地知识库文档，然后比较几组 chunk 参数：

```text
chunk_size=180 overlap=20
chunk_size=260 overlap=40
chunk_size=420 overlap=80
```

它输出：

```text
chunks 数量
最短 chunk
最长 chunk
平均 chunk 长度
```

这个脚本不连接 Qdrant。

所以不需要 VMware。

### 14. 当前脚本输出说明

本节运行脚本得到：

```text
RAG chunk tuning preview
documents: 4
chunk_size=180 overlap=20 chunks=18 min=8 max=174 avg=95.83
chunk_size=260 overlap=40 chunks=17 min=8 max=259 avg=101.59
chunk_size=420 overlap=80 chunks=16 min=8 max=408 avg=108.06
```

可以看到：

- chunk_size 变大后，chunk 数量略有减少
- max chunk 长度随 chunk_size 增大
- 当前示例文档较短，所以变化不算剧烈
- min=8 说明可能存在非常短的 chunk，后续可继续观察是否需要优化标题/短块处理

这就是调优的第一步：

```text
先观察，不急着下结论。
```

### 15. 本节完成后对下一节有什么帮助

下一节会进入更高级的检索方式：

```text
混合检索：关键词检索 + 向量检索
```

在学混合检索前，你必须先理解：

```text
基础向量检索本身有哪些可调参数。
```

否则后面加入关键词检索后，问题会更复杂。

## 三、本节代码改动说明

### 1. 新增 `app/rag/tuning.py`

新增调优辅助模块。

它不负责真实业务回答。

它负责把调优观察结构化。

核心产出是：

- chunk report
- retrieval report

### 2. 新增 `ChunkTuningCase` 和 `ChunkTuningReport`

它们服务入库前的切分调优。

你可以用它们比较：

```text
不同 chunk_size / overlap 会切出多少 chunks
chunk 长度分布是否合理
```

### 3. 新增 `RetrievalTuningCase` 和 `RetrievalTuningReport`

它们服务查询时的检索调优。

你可以用它们比较：

```text
不同 top_k / score_threshold 会返回多少结果
分数范围是多少
来源分布是什么
```

### 4. 修改 `FakeVectorStoreReader`

它现在会：

```text
按 score 降序
应用 score_threshold
应用 top_k
```

这样测试更接近真实检索行为。

### 5. 新增 `rag_chunk_tuning_preview.py`

这是一个不需要 Qdrant 的调试脚本。

运行方式：

```powershell
uv run python scripts/rag_chunk_tuning_preview.py
```

用途是观察本地知识库在不同切分参数下的 chunk 分布。

## 四、常见误区

### 误区 1：top_k 越大越好

不是。

top_k 太大可能带来噪声、重复内容和更高 token 成本。

### 误区 2：score_threshold 越高越安全

不一定。

threshold 太高会导致有用资料被过滤，no_context 变多。

### 误区 3：chunk_size 有一个通用最佳值

没有。

chunk_size 要根据文档类型、问题类型、embedding 模型和业务需求调整。

### 误区 4：overlap 越大召回越好

不一定。

overlap 太大会增加重复 chunk、存储成本和检索噪声。

### 误区 5：调 top_k 可以解决所有问题

不能。

如果文档切分很差，或者 embedding 模型不适合，调 top_k 只能缓解，不能根治。

### 误区 6：只看最终答案就能判断检索质量

不够。

模型可能猜对，也可能把噪声资料包装成流畅答案。

必须看检索结果本身。

## 五、本节练习

### 练习 1：判断参数类型

题目：

`chunk_size`、`chunk_overlap`、`top_k`、`score_threshold` 中，哪些是入库参数，哪些是查询参数？

参考答案：

`chunk_size` 和 `chunk_overlap` 是入库参数，影响文档怎么切 chunk，通常改了要重新入库。`top_k` 和 `score_threshold` 是查询参数，影响每次检索返回多少结果以及过滤哪些低分结果。

### 练习 2：解释 chunk 太小的问题

题目：

chunk 太小会带来什么问题？

参考答案：

chunk 太小容易导致上下文不完整，一个 chunk 可能不能独立表达完整知识点。检索到它后，模型可能缺少前后条件，回答不完整或误解业务规则。

### 练习 3：解释 chunk 太大的问题

题目：

chunk 太大会带来什么问题？

参考答案：

chunk 太大会把多个主题混在一起，增加噪声，占用更多上下文 token，也会让引用来源不够精确。模型可能被无关内容干扰。

### 练习 4：解释 overlap 的作用

题目：

为什么需要 `chunk_overlap`？

参考答案：

overlap 用来保留相邻 chunk 之间的部分上下文，降低关键信息刚好被切断的概率。它能提升边界处内容的召回机会。

### 练习 5：解释 overlap 的副作用

题目：

overlap 太大会有什么副作用？

参考答案：

overlap 太大会增加 chunk 数量、embedding 成本、向量库存储，也容易让检索结果出现重复内容，增加模型上下文噪声。

### 练习 6：判断 top_k 问题

题目：

如果用户问题需要多个文档共同回答，但 `top_k=1`，可能出现什么问题？

参考答案：

可能只召回一个 chunk，漏掉其他必要资料，导致答案不完整。比如同时涉及退款规则和运费规则的问题，top_k 太小可能只拿到其中一部分。

### 练习 7：判断 threshold 问题

题目：

如果 `score_threshold` 设置太低，可能出现什么问题？

参考答案：

低相关 chunks 也会进入上下文，模型可能基于牵强资料硬答，no_context 触发不足，增加错误回答风险。

### 练习 8：解释为什么调 chunk 参数要重新入库

题目：

为什么改 `chunk_size` 或 `chunk_overlap` 后，通常需要重新入库？

参考答案：

因为这两个参数决定文档切成哪些 chunks。chunks 改了，对应的 content、chunk_id、embedding 和 Qdrant points 都可能变化，所以需要重新切分、重新 embedding、重新写入向量库。

### 练习 9：解释为什么先看检索结果

题目：

为什么调 RAG 时要先看检索结果，再看模型回答？

参考答案：

因为模型回答依赖检索资料。如果检索错了，模型可能基于错误资料回答，也可能凭通用知识猜对。只看最终答案无法判断检索链路是否可靠。

## 六、自测问题

### 自测 1

问题：

`chunk_size` 控制什么？

答案：

控制单个 chunk 大概允许多长，当前项目按字符数控制。

### 自测 2

问题：

`chunk_overlap` 控制什么？

答案：

控制相邻 chunks 之间保留多少重复上下文，用于减少边界信息丢失。

### 自测 3

问题：

`top_k` 控制什么？

答案：

控制向量检索最多返回多少个最相似的 chunks。

### 自测 4

问题：

`score_threshold` 控制什么？

答案：

控制最低相关分数门槛，低于阈值的结果不返回。

### 自测 5

问题：

为什么改 `top_k` 通常不需要重新入库？

答案：

因为 `top_k` 是查询参数，只影响每次从已有向量库里取多少结果，不改变已经存储的 chunks 和 vectors。

### 自测 6

问题：

为什么改 `chunk_size` 通常需要重新入库？

答案：

因为它改变文档切分结果，进而改变 chunks、embeddings 和向量库 points。

### 自测 7

问题：

调优报告里的 `source_count` 有什么用？

答案：

它帮助观察检索结果来自多少个不同来源。如果问题应该命中某类文档，却返回很多无关来源，说明检索可能偏了。

### 自测 8

问题：

为什么调优报告要保留 `chunk_ids`？

答案：

因为 chunk_id 能定位具体命中的知识片段，方便观察是否重复命中相邻 chunk、是否漏掉关键 chunk。

### 自测 9

问题：

本节为什么新增 `rag_chunk_tuning_preview.py`？

答案：

为了在不连接 Qdrant、不打开 VMware 的情况下观察不同 chunk 参数产生的切分分布。

### 自测 10

问题：

为什么 fake reader 要按 score 排序并支持 threshold？

答案：

这样单元测试里也能观察 `top_k` 和 `score_threshold` 对结果数量和顺序的影响，更接近真实检索行为。

### 自测 11

问题：

score_threshold 可以跨模型固定使用同一个值吗？

答案：

不建议。不同 embedding 模型、距离度量和数据集的分数分布可能不同，需要结合当前系统实际观察。

### 自测 12

问题：

本节和后续混合检索有什么关系？

答案：

本节先理解基础向量检索的参数影响。后续混合检索会在向量检索之外加入关键词检索，如果基础参数都不清楚，混合检索会更难调。

## 七、你应该能口述出的版本

你可以这样向别人解释本节：

```text
第 25 节讲 RAG 检索质量调优。RAG 回答质量不只取决于大模型，也取决于检索出来的资料是不是对。我们重点学了四个参数：chunk_size、chunk_overlap、top_k、score_threshold。

chunk_size 和 chunk_overlap 是入库参数，决定文档怎么切成 chunks。chunk 太小容易上下文不完整，太大容易语义混杂；overlap 能保护边界上下文，但太大会制造重复、增加成本。改这些参数通常要重新切分、重新 embedding、重新入库。

top_k 和 score_threshold 是查询参数。top_k 控制取几个结果，太小可能漏资料，太大可能引入噪声；score_threshold 控制最低相关分数，太低会硬答，太高会过度拒答。改这些参数通常不需要重新入库。

本节新增 app/rag/tuning.py，用 ChunkTuningReport 和 RetrievalTuningReport 结构化观察参数影响。还新增 rag_chunk_tuning_preview.py，可以不打开 Qdrant 直接查看不同 chunk 参数切出的 chunk 数量和长度分布。调 RAG 时应该先看检索结果，再看模型回答，最后看引用是否支撑答案。
```

## 八、本节产出

新增或修改：

- `projects/ai-service/app/rag/tuning.py`
  - `ChunkTuningCase`
  - `ChunkTuningReport`
  - `RetrievalTuningCase`
  - `RetrievalTuningReport`
  - `build_chunk_tuning_report()`
  - `compare_chunk_tuning_cases()`
  - `build_retrieval_tuning_cases()`
  - `build_retrieval_tuning_report()`
  - `compare_retrieval_tuning_cases()`
- `projects/ai-service/scripts/rag_chunk_tuning_preview.py`
- `projects/ai-service/tests/test_rag_tuning.py`
- `projects/ai-service/tests/rag_fakes.py`
  - `FakeVectorStoreReader` 支持按 score 排序、`score_threshold` 过滤和 `top_k` 截断
- `projects/ai-service/tests/test_rag_fakes.py`

## 九、参考资料

- [阶段 4 第 12 节：chunk 切分策略](rag-stage4-12-chunk-splitting.md)
- [阶段 4 第 15 节：基础 top_k 检索](rag-stage4-15-basic-top-k-retrieval.md)
- [阶段 4 第 17 节：score_threshold](rag-stage4-17-score-threshold.md)
- [阶段 4 第 24 节：embedding 模型选择、维度、成本和批量处理](rag-stage4-24-embedding-model-dimension-cost-batch.md)
