# 阶段 4 第 27 节：rerank 重排序是什么

## 本节状态

已完成。

本节接在第 26 节“混合检索：关键词检索 + 向量检索”之后。

第 26 节解决的是：

```text
用户问题
-> 向量检索召回一批候选 chunk
-> 关键词检索召回一批候选 chunk
-> 两批结果去重、归一化、加权融合
-> 得到候选结果列表
```

第 27 节解决的是：

```text
已经召回的候选 chunk
-> 再判断哪几个更适合回答当前问题
-> 重新排序
-> 把更值得交给模型的 chunk 放到前面
```

这一步就叫 `rerank`，中文一般叫“重排序”。

## 本节学习目标

学完本节，你应该能解释清楚：

1. `rerank` 是什么。
2. `rerank` 和普通检索排序有什么区别。
3. 为什么 `top_k` 检索结果不一定就是最终最适合回答的结果。
4. `recall` 和 `precision` 在 RAG 里分别是什么意思。
5. rerank 在 RAG 链路里的位置。
6. 规则 reranker、cross-encoder reranker、LLM reranker 的区别。
7. 为什么 rerank 不应该绕过权限过滤。
8. 为什么本节先实现学习版规则 reranker。
9. 本节新增的 `RerankCandidate`、`RerankedChunk`、`RerankScoreBreakdown` 分别表示什么。
10. 为什么重排序结果里要保留 `original_rank` 和 `rerank_rank`。

## 本节暂时不学什么

本节暂时不学：

1. 不接真实 rerank 模型。
2. 不调用大模型做 LLM rerank。
3. 不接 Cohere、Jina、BGE reranker 等真实服务。
4. 不改 Qdrant 配置。
5. 不要求打开 VMware Ubuntu 或 Qdrant。
6. 不做多阶段复杂 rerank pipeline。
7. 不做 query rewrite。
8. 不做 RAG 自动评测。
9. 不让 rerank 负责权限判断。

原因是：

你现在更需要先理解 rerank 的职责边界。

真实 rerank 模型只是实现方式之一。只有先明白 rerank 解决什么问题、输入是什么、输出是什么、为什么放在检索之后，后面接真实模型才不会变成“照着代码填 API key”。

## 一、基础知识铺垫

### 1. 先回顾 RAG 的核心链路

RAG 的典型问答链路是：

```text
用户问题
-> query embedding
-> 向量库检索
-> 取回相关 chunk
-> 把 chunk 放进 prompt
-> 大模型根据资料回答
```

到目前为止，我们已经学过：

1. 文档怎么加载。
2. 文档怎么切 chunk。
3. chunk 怎么生成 embedding。
4. chunk 怎么写入 Qdrant。
5. query 怎么生成 embedding。
6. top_k 怎么取回相似 chunk。
7. score_threshold 怎么过滤低相关结果。
8. metadata filter 怎么限制权限、来源、文档类型和业务领域。
9. 检索结果怎么交给模型生成回答。
10. 引用来源和无资料兜底怎么做。
11. 关键词检索和向量检索怎么混合。

现在的问题是：

检索拿回来的结果，顺序一定是最适合回答的吗？

答案是不一定。

### 2. 什么是 recall

`recall` 一般翻译成“召回率”。

在 RAG 里，你可以先把它理解成：

```text
应该被找回的资料，有多少被找回来了。
```

比如用户问：

```text
退款多久到账？
```

知识库里真正有用的 chunk 是：

```text
退款到账时间 chunk
```

如果检索结果里包含了这个 chunk，那么说明至少“召回到了关键资料”。

如果检索结果完全没有这个 chunk，而只找回了物流、订单、账号安全，那么后面的模型再聪明也很难根据资料答对。

所以 recall 关注的是：

```text
有没有把可能有用的资料找回来。
```

### 3. 什么是 precision

`precision` 一般翻译成“精确率”。

在 RAG 里，你可以先把它理解成：

```text
找回来的资料里，有多少是真的有用。
```

比如 top_k=5 找回了 5 个 chunk：

```text
1. 退款到账时间
2. 物流异常能不能退款
3. 七天无理由退货
4. 商品质量问题
5. 账号安全验证
```

这里第 1 个最有用。

第 2 个有“退款”，但主题是物流异常，不是到账时间。

第 3、4 个属于退款退货规则，但不能直接回答到账时间。

第 5 个基本无关。

这时 recall 可能还可以，因为关键 chunk 被找回来了。

但 precision 不够高，因为候选结果里混进了不少弱相关内容。

### 4. RAG 为什么经常先重 recall 再重 precision

RAG 的工程经验通常是：

```text
第一阶段先尽量召回可能相关的资料。
第二阶段再筛选和排序。
```

原因很简单：

如果第一阶段没有找回关键资料，后面就没东西可排。

所以检索阶段通常会设置稍微大一点的候选数，例如：

```text
retrieve_top_k = 20
rerank_top_k = 5
```

意思是：

先召回 20 个候选 chunk，再从中重排并选出最适合的 5 个交给模型。

### 5. 什么是 rerank

`rerank` 就是重排序。

它的输入不是整个知识库。

它的输入是已经召回的一批候选结果。

它的输出是重新排序后的候选结果。

可以写成：

```text
query + candidates -> reranker -> reranked candidates
```

其中：

```text
query       用户问题
candidates 检索阶段找回来的候选 chunk
reranker   负责重新判断每个 chunk 和问题的匹配程度
```

### 6. rerank 不等于 retrieve

`retrieve` 是检索。

它的目标是：

```text
从大量资料里找出一批可能相关的候选结果。
```

`rerank` 是重排序。

它的目标是：

```text
在已经找回的候选结果里，把更相关的排到前面。
```

区别很重要。

检索面对的是整个知识库。

重排序面对的是候选列表。

检索解决“找谁出来”。

重排序解决“谁排前面”。

### 7. 为什么检索分数不一定够用

向量检索的分数来自向量相似度。

它能表达语义相似。

但它不一定能准确判断：

1. 这个 chunk 是否能直接回答问题。
2. 这个 chunk 是否只是主题相近。
3. 这个 chunk 是否包含关键限制条件。
4. 这个 chunk 是否只是出现了几个相关词。
5. 这个 chunk 是否比另一个 chunk 更适合作为最终上下文。

比如：

```text
用户问：退款多久到账？
```

候选 A：

```text
物流异常不能直接退款，需要先确认订单状态和异常原因。
```

候选 B：

```text
退货商品入库并审核通过后，退款通常会在 1 到 3 个工作日内原路退回。
```

候选 A 有“退款”，也可能被召回。

但候选 B 才能直接回答“多久到账”。

rerank 的价值就在这里。

### 8. rerank 的常见位置

常见 RAG 链路可以写成：

```text
query
-> retrieve top 20
-> rerank top 20
-> keep top 5
-> build context
-> generate answer
```

如果加上第 26 节混合检索：

```text
query
-> vector retrieve top 20
-> keyword retrieve top 20
-> hybrid fusion
-> rerank top candidates
-> keep top 5
-> generate answer
```

也就是说，rerank 通常在“召回之后，生成之前”。

### 9. rerank 为什么能提升回答质量

模型最终看到的上下文通常有限。

如果你把弱相关 chunk 放到前面，模型容易：

1. 关注错误信息。
2. 回答跑偏。
3. 把多个主题混在一起。
4. 产生看似有依据但实际不精确的回答。

如果 rerank 把最相关 chunk 放到前面，模型更容易：

1. 直接找到答案。
2. 少读无关资料。
3. 回答更聚焦。
4. 引用来源更准确。

### 10. rerank 不能解决所有问题

rerank 只能重排已经召回的候选结果。

如果关键 chunk 没有被召回，rerank 没法凭空找出来。

比如：

```text
retrieve 阶段没有找回“退款到账时间” chunk
```

rerank 再怎么排，也只能在错误候选里排序。

所以 rerank 不是替代检索。

它是检索之后的增强。

### 11. 规则 reranker 是什么

规则 reranker 是用人工规则打分。

例如：

1. chunk 内容里命中多少 query 关键词。
2. title/section 是否命中 query 关键词。
3. 原始检索分数是否高。
4. 是否同时来自向量检索和关键词检索。
5. 是否属于指定业务领域。

规则 reranker 的优点：

1. 容易理解。
2. 容易测试。
3. 不需要额外模型。
4. 速度快。
5. 适合教学和早期调试。

规则 reranker 的缺点：

1. 语义理解弱。
2. 对表达变化不够鲁棒。
3. 需要人工设计规则。
4. 很难达到专业 rerank 模型的效果。

### 12. cross-encoder reranker 是什么

cross-encoder reranker 是一种常见的重排序模型方式。

它不是分别给 query 和 chunk 生成向量再比较。

它通常把 query 和 candidate 放在一起输入模型：

```text
[query, candidate chunk] -> relevance score
```

它直接判断：

```text
这个 chunk 对这个 query 有多相关。
```

这通常比单纯向量相似度更准确。

但代价是：

1. 需要额外模型。
2. 每个候选都要算一次分。
3. 候选越多，耗时越高。
4. 部署和成本更复杂。

### 13. LLM reranker 是什么

LLM reranker 是让大模型参与重排序。

形式可能是：

```text
给模型用户问题和候选资料
让模型判断哪些资料更适合回答
```

优点：

1. 理解能力强。
2. 可以处理复杂业务语境。
3. 可以解释为什么某个 chunk 更相关。

缺点：

1. 成本高。
2. 延迟高。
3. 输出需要结构化约束和校验。
4. 可能不稳定。
5. 不能让它绕过权限和安全规则。

### 14. rerank 和 hybrid search 的关系

第 26 节的 hybrid search 解决的是：

```text
向量召回和关键词召回怎么合并。
```

第 27 节的 rerank 解决的是：

```text
合并后的候选结果怎么再精排。
```

可以理解为：

```text
hybrid search 更偏召回增强。
rerank 更偏排序增强。
```

两者不是互斥关系。

实际项目里经常一起使用。

### 15. rerank 和 score_threshold 的关系

`score_threshold` 是粗过滤。

它做的是：

```text
低于某个检索分数的结果不要。
```

rerank 是精排序。

它做的是：

```text
候选结果都在这里了，重新判断谁更适合排前面。
```

常见组合是：

```text
先用 score_threshold 去掉明显不相关结果
再用 rerank 对剩下的候选精排
```

### 16. rerank 和 metadata filter 的关系

metadata filter 必须在 rerank 前面做。

原因是权限和业务边界不能交给 rerank 决定。

比如用户只能看 `customer_service` 权限组资料。

那么检索阶段就应该过滤：

```text
permission_group = customer_service
```

rerank 只能在过滤后的候选里排序。

不能让 rerank 把内部资料重新排回来。

### 17. rerank 为什么要保留原始排序

本节代码里有两个字段：

```text
original_rank
rerank_rank
```

`original_rank` 表示：

```text
候选结果在进入 rerank 之前排第几。
```

`rerank_rank` 表示：

```text
经过 rerank 之后排第几。
```

保留这两个字段很重要。

它可以帮助你调试：

1. 哪些 chunk 被提前了。
2. 哪些 chunk 被压后了。
3. rerank 是否真的改善了排序。
4. 规则是否过度偏向某类信号。
5. 原始检索分和 rerank 分是否冲突。

### 18. 为什么要有 score_breakdown

只给一个总分不够。

如果你只看到：

```text
rerank_score = 0.2864
```

你不知道这个分数从哪里来。

所以本节代码用 `RerankScoreBreakdown` 拆成：

```text
content_match_score
title_section_match_score
normalized_retrieval_score
source_agreement_score
```

这样你能解释：

这个 chunk 排前面，是因为内容命中了问题，还是因为标题命中，还是因为原始检索分高，还是因为同时被向量和关键词召回。

### 19. 为什么本节不接真实 rerank 模型

如果一上来就接真实 rerank 模型，你可能会只记住：

```text
调用某个 API
传入 query 和 documents
拿到 scores
排序
```

但这不等于真的理解 rerank。

本节先做规则版，是为了让你看清楚：

1. rerank 的输入输出是什么。
2. rerank 在 RAG 里的位置。
3. rerank 分数为什么需要解释。
4. rerank 不能替代召回。
5. rerank 不能替代权限过滤。
6. rerank 结果如何交给后续生成链路。

### 20. 本节代码的学习价值

本节代码不是为了实现生产级 reranker。

它的学习价值是：

1. 把 rerank 抽象成独立模块。
2. 明确候选输入模型。
3. 明确重排序输出模型。
4. 让排序分数可解释。
5. 保留原始排序和重排排序。
6. 提供后续接真实 rerank 模型的接口位置。

你以后接真实 reranker 时，只需要把“打分逻辑”换掉，而不是推翻整个链路。

## 二、本节主题系统讲解

### 1. 第 27 节在阶段 4 里的位置

阶段 4 的主线是企业知识库 RAG。

前面我们已经完成了从入库到检索再到生成的最小闭环。

第 25 节学的是检索质量调优。

第 26 节学的是混合检索。

第 27 节学的是重排序。

它们的关系可以写成：

```text
第 25 节：调 chunk_size、overlap、top_k、score_threshold
第 26 节：向量检索 + 关键词检索，扩大和补强召回
第 27 节：对召回结果重新排序，提升最终上下文质量
```

### 2. 本节新增 `app/rag/rerank.py`

本节新增文件：

```text
projects/ai-service/app/rag/rerank.py
```

它是 RAG 内部包的一部分。

它不属于 router。

它不负责 HTTP 接口。

它不负责调用 Qdrant。

它只负责：

```text
query + candidates -> reranked candidates
```

也就是重排序核心逻辑。

### 3. `RerankCandidate` 表示什么

`RerankCandidate` 表示“准备进入 rerank 的候选 chunk”。

它包含：

```text
chunk_id
content
metadata
retrieval_score
retrieval_sources
matched_terms
```

其中：

`chunk_id` 是 chunk 的稳定标识。

`content` 是 chunk 内容。

`metadata` 是来源、标题、section、权限等信息。

`retrieval_score` 是前一阶段的检索分数。

如果来自向量检索，它可以是向量相似度。

如果来自关键词检索，它可以是关键词分数。

如果来自混合检索，它可以是 hybrid_score。

`retrieval_sources` 表示候选来自哪里：

```text
["vector"]
["keyword"]
["vector", "keyword"]
```

`matched_terms` 是前一阶段已经命中的关键词。

### 4. 为什么候选模型不直接复用 `RetrievedChunk`

`RetrievedChunk` 是向量检索结果。

它的 score 更偏向 vector store 的返回分数。

但 rerank 的候选可能来自：

1. 向量检索。
2. 关键词检索。
3. 混合检索。
4. 未来真实 rerank 前的其他召回方式。

所以本节定义 `RerankCandidate`，让 rerank 输入更通用。

### 5. `RerankScoreBreakdown` 表示什么

`RerankScoreBreakdown` 表示重排序分数拆解。

本节有 4 个分数：

```text
content_match_score
title_section_match_score
normalized_retrieval_score
source_agreement_score
```

它们分别代表：

1. 内容和问题的词项匹配程度。
2. 标题/小节和问题的词项匹配程度。
3. 原始检索分数归一化后的强弱。
4. 是否同时被多个召回源命中。

这些不是生产级评分公式。

它们是学习版规则，用来让你看懂 rerank 怎么把多个信号合成一个排序分。

### 6. `RerankedChunk` 表示什么

`RerankedChunk` 表示“重排序后的 chunk”。

它包含：

```text
chunk_id
content
metadata
retrieval_score
rerank_score
original_rank
rerank_rank
score_breakdown
retrieval_sources
matched_terms
```

重点是：

`retrieval_score` 是进入 rerank 前的分数。

`rerank_score` 是 rerank 后的新分数。

`original_rank` 是原始排名。

`rerank_rank` 是重排后排名。

`score_breakdown` 是分数解释。

### 7. 本节规则 rerank 的评分公式

本节评分公式是：

```text
rerank_score =
  content_match_score * 0.55
+ title_section_match_score * 0.20
+ normalized_retrieval_score * 0.15
+ source_agreement_score * 0.10
```

这个公式表达的思想是：

1. 内容命中最重要。
2. 标题和小节命中也很重要。
3. 原始检索分数有参考价值，但不是全部。
4. 同时被关键词和向量召回，可以给一点奖励。

为什么内容权重最高？

因为最终模型回答时读的是 chunk 内容。

如果内容不能回答问题，只靠标题或原始分数高并不可靠。

### 8. 为什么要归一化 retrieval_score

候选可能来自不同召回方式。

不同召回方式的分数不能直接比较。

例如：

```text
向量分数：0.83
关键词分数：0.18
混合分数：0.52
```

这些分数来源不同，含义也不同。

本节做了简单归一化：

```text
normalized_retrieval_score = 当前分数 / 候选中的最高分
```

这样能把原始检索分压到 0 到 1 的范围里。

注意：

这只是教学版简化。

生产项目里要根据具体检索器、距离函数、业务数据分布进一步校准。

### 9. 为什么 title 和 section 单独算分

RAG chunk 经常来自长文档。

一个 chunk 的标题和小节信息很有价值。

比如用户问：

```text
退款多久到账？
```

如果某个 chunk 的 section 是：

```text
退款到账时间
```

这就是很强的相关性信号。

即使内容里没有完全重复问题原词，标题和 section 也能帮助 rerank 判断它更可能有用。

### 10. 为什么 source_agreement 只给小权重

如果一个 chunk 同时被向量检索和关键词检索命中，说明它被两个不同召回方式都认为相关。

这是一个有用信号。

但它不能压过内容本身。

如果内容完全不能回答问题，只因为它被两个检索器命中就排第一，会有风险。

所以本节只给 0.10 的小权重。

### 11. `RuleBasedReranker` 的作用

本节定义了：

```python
class RuleBasedReranker:
    def rerank(...)
```

它只是包装 `rerank_candidates()`。

为什么还要写这个类？

因为后续接真实 rerank 模型时，可以有类似结构：

```python
class ModelBasedReranker:
    def rerank(...)
```

这样服务层只需要依赖统一接口，不必关心具体是规则版、模型版还是 LLM 版。

### 12. 三个转换函数的作用

本节新增三个转换函数：

```text
make_rerank_candidates_from_retrieved_chunks()
make_rerank_candidates_from_keyword_results()
make_rerank_candidates_from_hybrid_results()
```

它们的作用是：

把不同检索阶段的结果统一转换成 `RerankCandidate`。

这很符合工程分层思路：

```text
不同召回器可以有不同结果模型
rerank 层只吃统一候选模型
```

### 13. `reranked_chunks_to_retrieved_chunks()` 的作用

后续生成链路现在主要吃 `RetrievedChunk`。

所以本节提供：

```text
reranked_chunks_to_retrieved_chunks()
```

它可以把 `RerankedChunk` 转回 `RetrievedChunk`。

这样后面接：

```text
build_rag_context()
generate_answer_with_citations()
```

会更顺。

注意：

转换后的 `score` 用的是 `rerank_score`。

这表示后续上下文里的 score 已经是重排序分数，而不是原始向量分数。

### 14. `format_reranked_chunks_for_debug()` 的作用

这个函数用于调试输出。

它会输出：

```text
rerank_score
original_rank
retrieval_score
content_match
title_section_match
sources
source
section
chunk_id
matched
```

这对学习很重要。

因为 rerank 不应该是黑盒。

至少在学习阶段，你要能看懂：

```text
为什么这个 chunk 被排到了前面？
为什么另一个 chunk 被压到了后面？
```

### 15. 本节预览脚本做什么

本节新增：

```text
scripts/rag_rerank_preview.py
```

它不连接 Qdrant。

它做的是：

1. 加载本地知识库文档。
2. 切分成 chunks。
3. 用学习版关键词检索拿到候选结果。
4. 把关键词结果转换成 rerank candidates。
5. 执行规则 rerank。
6. 打印 rerank 前后的顺序。

这样你不用开虚拟机、不用真实向量库，也能看懂 rerank 的效果。

## 三、本节代码改动说明

### 1. 新增 `app/rag/rerank.py`

这个文件是本节主文件。

它把 rerank 相关内容都放在一起：

```text
候选模型
重排结果模型
分数拆解模型
规则 reranker
转换函数
debug 格式化函数
```

这种拆分方式的好处是：

RAG 其他模块不需要知道 rerank 内部怎么计算分数。

它们只需要知道：

```text
给 rerank 一批候选
拿回重排后的结果
```

### 2. 新增 `RerankCandidate`

这不是数据库模型。

也不是 API 请求模型。

它是 RAG 内部模型。

它表示：

```text
某个 chunk 已经被召回，现在准备进入重排序。
```

它把多种检索来源统一到一个结构里。

### 3. 新增 `RerankedChunk`

`RerankedChunk` 是重排后的结果。

它比 `RerankCandidate` 多了：

```text
rerank_score
original_rank
rerank_rank
score_breakdown
```

这些字段主要服务于：

1. 调试。
2. 解释。
3. 学习。
4. 后续评测。

### 4. 新增 `rerank_candidates()`

这是核心函数。

它的流程是：

```text
校验 query
校验 top_k
提取 query terms
计算候选中的最高 retrieval_score
逐个候选计算 score_breakdown
合成 rerank_score
排序
截取 top_k
补上 rerank_rank
```

你可以把它看成一个独立的“精排函数”。

### 5. 新增 `RuleBasedReranker`

这个类目前只是轻量包装。

但它代表一个重要设计：

后续我们可以把规则版换成模型版。

接口仍然是：

```text
rerank(query, candidates, top_k)
```

### 6. 新增 `test_rag_rerank.py`

测试重点不是测每个字符串怎么输出。

测试重点是：

1. 更相关 chunk 能被排到前面。
2. 分数拆解字段存在。
3. top_k 能限制结果数。
4. 空 query、非法 top_k、非法 score 会被拒绝。
5. RetrievedChunk、KeywordSearchResult、HybridSearchResult 能转换成 RerankCandidate。
6. reranked result 能转回 RetrievedChunk。

### 7. 新增 `rag_rerank_preview.py`

这个脚本用于你手动观察。

运行：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run python scripts/rag_rerank_preview.py
```

你会看到：

```text
before rerank:
...
after rerank:
...
```

对比前后顺序，就能理解 rerank 在干什么。

## 四、运行结果解释

本节预览脚本输出里有这样的结果：

```text
before rerank:
1. 退款到账时间
2. 物流异常可以直接退款吗
3. 退款退货规则
...

after rerank:
1. 退款到账时间
2. 退款退货规则
3. 物流异常可以直接退款吗
...
```

这说明：

关键词检索阶段，物流 FAQ 因为出现了“退款”，被排到比较靠前。

但 rerank 发现它的 section 和内容并不直接回答“多久到账”。

于是退款退货规则相关 chunk 被提前。

这就是 rerank 的价值：

```text
候选可以宽一点
最终上下文要准一点
```

## 五、常见误区

### 误区 1：rerank 可以替代向量检索

不可以。

rerank 只能重排候选。

如果检索阶段没有召回关键资料，rerank 没法凭空生成资料。

### 误区 2：rerank 一定要用大模型

不一定。

rerank 可以是：

1. 规则版。
2. 传统机器学习模型。
3. cross-encoder 模型。
4. LLM 判断。
5. 多种方式组合。

本节先学规则版，是为了理解流程。

### 误区 3：原始 score 高就一定更适合回答

不一定。

原始 score 只代表某个检索器认为它相关。

它不一定代表它能直接回答问题。

rerank 会再看内容、标题、小节等信号。

### 误区 4：rerank 可以绕过权限过滤

绝对不可以。

权限过滤必须在 rerank 之前完成。

rerank 只能在用户有权看的候选资料里排序。

### 误区 5：rerank_score 是业务事实

不是。

`rerank_score` 只是排序分。

它不能写进最终业务回答里当事实。

模型回答时不能说：

```text
因为资料分数是 0.2864，所以退款 1 到 3 天到账。
```

分数只是系统内部排序信号。

### 误区 6：rerank 越复杂越好

不一定。

rerank 越复杂，可能带来：

1. 更高延迟。
2. 更高成本。
3. 更难测试。
4. 更难解释。
5. 更难排查问题。

真实项目要根据业务场景决定。

### 误区 7：top_k 越大，rerank 效果越好

不一定。

候选太少，可能漏掉好资料。

候选太多，rerank 成本会上升，也可能混入更多噪声。

常见做法是通过评测来调：

```text
retrieve_top_k
rerank_top_k
score_threshold
```

## 六、本节练习

### 练习 1：解释 rerank 的输入和输出

问题：

请用一句话解释 rerank 的输入和输出。

参考答案：

rerank 的输入是用户问题和已经召回的候选 chunk，输出是重新排序后的候选 chunk 列表。

### 练习 2：解释 rerank 和 retrieve 的区别

问题：

retrieve 和 rerank 分别解决什么问题？

参考答案：

retrieve 从知识库里找出候选资料，解决“找哪些资料出来”；rerank 在候选资料里重新排序，解决“哪些资料更应该排前面”。

### 练习 3：解释 recall 和 precision

问题：

在 RAG 里，recall 和 precision 分别是什么意思？

参考答案：

recall 关注应该找回的资料有没有被找回；precision 关注找回来的资料里有多少是真的有用。

### 练习 4：解释为什么 rerank 不能替代权限过滤

问题：

为什么不能把权限过滤放到 rerank 里做？

参考答案：

权限过滤是安全边界，必须在候选进入 rerank 前完成。rerank 只能排序用户已经有权访问的候选资料，不能决定用户能不能看到某份资料。

### 练习 5：解释 `original_rank` 和 `rerank_rank`

问题：

这两个字段分别有什么用？

参考答案：

`original_rank` 表示候选进入 rerank 前的排名；`rerank_rank` 表示重排后的排名。它们用于观察哪些 chunk 被提前或压后，方便调试排序效果。

### 练习 6：解释 `score_breakdown`

问题：

为什么不要只保留一个 `rerank_score`？

参考答案：

只有总分很难解释排序原因。`score_breakdown` 可以拆出内容匹配、标题小节匹配、原始检索分和召回源一致性等信号，帮助理解和调试。

### 练习 7：解释本节为什么不调用真实 rerank 模型

问题：

本节为什么先做规则版 reranker？

参考答案：

因为当前学习重点是理解 rerank 的职责、位置、输入输出和排序逻辑。规则版可解释、可测试、无外部依赖，更适合打基础。

### 练习 8：判断排序结果

问题：

用户问“退款多久到账？”，候选 A 是“物流异常不能直接退款”，候选 B 是“退款通常 1 到 3 个工作日到账”。哪个更应该排前面？

参考答案：

候选 B 更应该排前面，因为它直接回答到账时间。候选 A 虽然有“退款”，但主题是物流异常能否退款，不是到账时间。

### 练习 9：解释 rerank 在完整 RAG 中的位置

问题：

请写出包含 hybrid search 和 rerank 的 RAG 链路。

参考答案：

```text
用户问题
-> 向量检索
-> 关键词检索
-> 混合融合
-> rerank 重排序
-> 选取 top chunks
-> 构造上下文
-> 模型生成回答
```

### 练习 10：解释为什么 rerank 后还要截取 top_k

问题：

为什么 rerank 后通常只保留前几个 chunk？

参考答案：

因为模型上下文有限，放太多 chunk 会增加噪声、成本和延迟。rerank 后保留最相关的少量 chunk，可以提高最终回答的聚焦度。

## 七、自测问题

### 自测 1

问题：

rerank 是在检索之前还是检索之后？

答案：

检索之后。

### 自测 2

问题：

rerank 面对的是整个知识库还是候选列表？

答案：

候选列表。

### 自测 3

问题：

如果关键 chunk 没有被召回，rerank 能解决吗？

答案：

不能。rerank 不能凭空找回没有进入候选列表的资料。

### 自测 4

问题：

`retrieval_score` 和 `rerank_score` 是同一个东西吗？

答案：

不是。`retrieval_score` 是召回阶段给出的分数，`rerank_score` 是重排序阶段重新计算的分数。

### 自测 5

问题：

为什么本节要给 `retrieval_score` 做归一化？

答案：

因为不同检索方式的分数范围和含义不同，直接相加不可靠，归一化后更适合作为组合信号。

### 自测 6

问题：

`source_agreement_score` 表示什么？

答案：

表示候选是否同时来自多个召回源，例如同时被向量检索和关键词检索命中。

### 自测 7

问题：

为什么内容匹配权重最高？

答案：

因为最终模型回答时主要依赖 chunk 内容。如果内容不能回答问题，只靠标题或原始分高并不可靠。

### 自测 8

问题：

规则 reranker 的优点是什么？

答案：

容易理解、容易测试、不需要外部模型、速度快，适合教学和早期调试。

### 自测 9

问题：

cross-encoder reranker 和向量检索有什么核心区别？

答案：

向量检索通常分别编码 query 和 chunk 后比较向量相似度；cross-encoder 通常把 query 和 chunk 一起输入模型，直接判断二者相关性。

### 自测 10

问题：

LLM reranker 的主要风险是什么？

答案：

成本高、延迟高、输出可能不稳定，需要结构化约束、校验和安全边界。

### 自测 11

问题：

rerank 能不能决定用户是否有权限访问某个 chunk？

答案：

不能。权限过滤必须在 rerank 前完成。

### 自测 12

问题：

为什么要把 reranked chunks 转回 RetrievedChunk？

答案：

因为后续已有的 RAG 生成链路主要接收 RetrievedChunk，转换后可以复用已有上下文构造、引用来源和回答生成逻辑。

## 八、你应该能口述出的版本

你可以这样讲：

RAG 不是把向量库返回的 top_k 结果直接丢给模型就完事。检索阶段更像是先从知识库里找出一批可能相关的候选资料，这一步更关注不要漏掉关键 chunk。但候选结果里可能混入弱相关内容，所以需要 rerank。rerank 的输入是用户问题和候选 chunk，输出是重新排序后的 chunk。它不负责从知识库里找新资料，只负责在已有候选里判断谁更适合回答当前问题。

本节实现的是学习版规则 reranker。它会看 chunk 内容是否命中问题词、标题和 section 是否命中问题词、原始检索分数强不强，以及这个候选是否同时来自多个召回源。最后合成一个 `rerank_score`，并保留 `original_rank`、`rerank_rank` 和 `score_breakdown`，方便观察排序变化和解释原因。真实项目里可以把规则打分换成 cross-encoder reranker 或 LLM reranker，但权限过滤、候选输入、结果输出和调试字段这些工程边界仍然要保留。

## 九、本节产出

本节新增：

```text
projects/ai-service/app/rag/rerank.py
projects/ai-service/tests/test_rag_rerank.py
projects/ai-service/scripts/rag_rerank_preview.py
notes/rag-stage4-27-rerank.md
```

本节更新：

```text
README.md
docs/learning-progress.md
docs/learning-resources.md
projects/ai-service/README.md
projects/ai-service/app/rag/README.md
```

本节验证：

```text
uv run pytest tests/test_rag_rerank.py tests/test_rag_hybrid.py -q
uv run python scripts/rag_rerank_preview.py
```

## 十、下一节衔接

下一节进入：

```text
阶段 4 第 28 节：RAG 安全：文档权限、Prompt Injection、敏感信息
```

原因是：

我们已经有了基础检索、过滤、生成、引用、无资料兜底、错误处理、测试、文档维护、调优、混合检索和重排序。

接下来必须系统学习 RAG 安全。

否则 RAG 看起来能回答问题，但可能存在：

1. 越权读取文档。
2. 被知识库里的恶意内容注入 prompt。
3. 把敏感信息交给模型。
4. 引用来源暴露内部字段。
5. 错误回答被包装成“有资料依据”。

安全是企业 RAG 不能跳过的一层。
