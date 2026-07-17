# 阶段 4 第 26 节：混合检索：关键词检索 + 向量检索

## 本节状态

已完成。

第 25 节我们学了检索质量调优：

- `chunk_size`
- `chunk_overlap`
- `top_k`
- `score_threshold`

这些参数主要围绕“向量检索”展开。

第 26 节开始补另一条检索路线：

```text
关键词检索
```

然后把它和向量检索合在一起：

```text
混合检索 = 向量检索 + 关键词检索 + 合并去重排序
```

为什么要学这个？

因为真实 RAG 不一定只靠向量检索。

向量检索擅长语义相似。

关键词检索擅长精确词命中。

两者各有短板，也能互补。

本节新增：

- `projects/ai-service/app/rag/hybrid.py`
- `projects/ai-service/tests/test_rag_hybrid.py`
- `projects/ai-service/scripts/rag_keyword_search_preview.py`

本节不需要打开 VMware。

因为本节的关键词检索和混合融合逻辑可以完全在本地用 fake / 本地 chunks 测试。

## 本节学习目标

学完本节，你应该能讲清楚：

1. 为什么只靠向量检索不够。
2. 为什么只靠关键词检索也不够。
3. 关键词检索的基本思想是什么。
4. BM25 大概是什么，为什么本节先不直接实现复杂 BM25。
5. 混合检索的基本流程是什么。
6. vector recall 和 keyword recall 分别解决什么问题。
7. 为什么混合检索要合并、去重、排序。
8. 为什么不能直接把向量分数和关键词分数当成同一尺度。
9. 本节的简单分数融合是怎么做的。
10. `SimpleKeywordRetriever`、`KeywordSearchResult`、`HybridSearchResult`、`hybrid_retrieve()` 分别负责什么。

## 本节暂时不学什么

本节暂时不做：

- 不实现完整 BM25。
- 不接 Elasticsearch / OpenSearch。
- 不接 Qdrant sparse vector。
- 不做 SPLADE、ColBERT 这类高级检索。
- 不做 rerank。
- 不真实调用大模型。
- 不真实调用 embedding API。
- 不要求打开 Qdrant。
- 不做检索评测集。

本节目标是先把混合检索的底层思路讲明白，并在代码里跑通最小可理解版本。

## 一、基础知识铺垫

### 1. 什么是向量检索

向量检索就是：

```text
把文本变成向量
用向量相似度找语义接近的内容
```

例如：

```text
用户问：退款多久到账？
文档写：售后退款处理时效为 1 到 3 个工作日。
```

这两句话关键词不完全一样。

但语义接近。

向量检索有机会把它们匹配起来。

### 2. 向量检索擅长什么

向量检索擅长：

- 同义表达
- 近义表达
- 问法和文档说法不完全一致的场景
- 长句语义相似
- 用户用自然语言描述需求

比如：

```text
用户说：钱什么时候退回来？
文档写：退款到账时间通常为 1 到 3 个工作日。
```

关键词不完全重合，但语义相近。

这就是向量检索的优势。

### 3. 向量检索不擅长什么

向量检索也有短板。

它可能不擅长：

- 订单号
- SKU 编号
- 产品型号
- 政策编号
- 错误码
- 人名、地名、专有名词
- 必须精确命中的关键词

例如：

```text
ERR_1024
ORD-20260717-0001
SKU-X9-Pro
退款规则第 3.2 条
```

这些内容不是“语义相近”就够了。

它们往往需要精确匹配。

### 4. 什么是关键词检索

关键词检索就是：

```text
从用户问题里提取词
看文档 chunk 里是否出现这些词
出现越多，分数越高
```

最简单的关键词检索可以理解为：

```text
query terms
vs
chunk text
```

例如：

```text
query terms: 退款, 到账
chunk text: 退款到账时间通常为 1 到 3 个工作日。
```

这个 chunk 命中了“退款”和“到账”，所以关键词相关性较高。

### 5. 关键词检索擅长什么

关键词检索擅长：

- 精确词命中
- 编号命中
- 错误码命中
- 固定术语命中
- 人名、产品名、专有名词
- 文档中明确出现的业务词

例如：

```text
用户问：订单 ORD-10086 怎么查？
文档里出现：ORD-10086
```

关键词检索很适合这种场景。

### 6. 关键词检索不擅长什么

关键词检索不擅长同义表达。

例如：

```text
用户说：钱什么时候退回来？
文档写：退款到账时间。
```

如果没有共同关键词，普通关键词检索可能搜不到。

所以关键词检索也不是万能的。

### 7. 为什么要混合检索

因为向量检索和关键词检索互补。

你可以这样理解：

```text
向量检索：负责语义召回。
关键词检索：负责精确召回。
混合检索：两边都搜，再合并结果。
```

这样可以提高召回覆盖面。

尤其是企业知识库里，经常同时存在：

- 自然语言问题
- 固定业务术语
- 编号
- 政策条款
- 产品名

混合检索更贴近真实项目。

### 8. 混合检索的基本流程

最简单的混合检索流程是：

```text
用户问题
-> 向量检索得到一批 chunks
-> 关键词检索得到一批 chunks
-> 按 chunk_id 合并去重
-> 融合分数
-> 排序
-> 取 final_top_k
```

本节代码就是这个结构。

### 9. 为什么要去重

同一个 chunk 可能同时被向量检索和关键词检索命中。

例如：

```text
chunk_id = refund_chunk_0001
```

它既语义接近，也命中了关键词。

如果不去重，模型上下文里可能出现重复内容。

重复内容会：

- 浪费 token
- 干扰模型
- 让引用来源重复
- 降低上下文质量

所以混合检索必须去重。

### 10. 为什么按 chunk_id 去重

当前项目里，`chunk_id` 是 chunk 级稳定标识。

同一个知识片段，无论来自向量检索还是关键词检索，都应该有同一个 `chunk_id`。

所以用它去重合理。

以后如果项目引入更正式的 `document_id + chunk_index`，也可以用更稳定的组合键。

### 11. 为什么不能直接比较向量分数和关键词分数

向量检索分数和关键词检索分数不是同一个体系。

向量分数可能来自：

- cosine similarity
- dot product
- distance 转换

关键词分数可能来自：

- 命中词数量
- 词频
- BM25
- 自定义权重

所以：

```text
vector_score = 0.88
keyword_score = 0.88
```

并不代表它们含义一样。

本节代码会先在各自结果集内部做简单归一化，再做加权融合。

这是教学版做法，不是最终生产级排序。

### 12. 什么是分数归一化

分数归一化就是把不同来源的分数变到可比较范围。

本节采用非常简单的方式：

```text
normalized_score = score / 当前结果集最高 score
```

例如向量结果分数：

```text
0.90, 0.60
```

归一化后：

```text
1.0, 0.666...
```

关键词结果分数：

```text
1.0, 0.8
```

归一化后：

```text
1.0, 0.8
```

然后再按权重合并。

### 13. 什么是加权融合

加权融合就是：

```text
hybrid_score = vector_norm * vector_weight + keyword_norm * keyword_weight
```

本节默认：

```text
vector_weight = 0.7
keyword_weight = 0.3
```

意思是：

```text
仍然更相信向量语义召回，但给关键词精确命中一定加分。
```

这不是唯一方案。

后续还会学习更常见的 RRF、rerank 等方法。

### 14. 什么是 BM25

BM25 是一种经典关键词检索排序算法。

你现在可以先粗略理解：

```text
BM25 会考虑词是否出现、出现次数、词在多少文档中出现、文档长度等因素。
```

它比简单“命中几个词”更成熟。

很多搜索系统都使用 BM25 或类似思想。

但本节不直接实现完整 BM25。

原因是：

- 当前重点是混合检索流程
- 项目还没有引入搜索引擎
- 中文分词本身也需要额外处理
- 直接上 BM25 容易把学习焦点带偏

所以本节先做最小关键词检索。

### 15. 中文关键词检索为什么麻烦

英文可以按空格分词：

```text
refund arrival time
```

中文没有天然空格：

```text
退款多久到账
```

你要判断它里面有哪些词：

```text
退款
到账
多久
```

本节没有引入专业中文分词库。

而是用非常简单的中文 ngram：

```text
连续中文字符串 -> 二元/三元片段
```

例如：

```text
退款多久到账
-> 退款, 款多, 多久, 久到, 到账
-> 退款多, 款多久, 多久到, 久到账
```

这很粗糙，但足够教学。

### 16. 简单关键词检索的局限

本节关键词检索很简单。

它会有局限：

- 不能真正理解词性
- 不能处理复杂中文分词
- 容易匹配到宽泛词
- 对同义词无能为力
- 对停用词处理不足
- 没有 BM25 的文档频率权重

比如脚本输出里，“退款多久到账”会命中所有包含“退款”的 chunks。

这说明关键词检索能补精确召回，但也会带来噪声。

后续需要 rerank 或更成熟的关键词检索来改善。

### 17. 混合检索和 rerank 的关系

混合检索是召回阶段。

它的目标是：

```text
尽量把可能相关的候选 chunks 找出来。
```

rerank 是重排序阶段。

它的目标是：

```text
在候选 chunks 里重新判断谁最相关。
```

所以常见链路是：

```text
vector + keyword 混合召回
-> 去重
-> rerank
-> final top_k
-> 交给模型回答
```

本节先学混合召回。

下一节会学 rerank。

### 18. 混合检索和 metadata filter 的关系

metadata filter 仍然重要。

无论向量检索还是关键词检索，都应该遵守权限和业务过滤。

例如：

```text
permission_group = customer_service
business_domain = refund
```

如果向量检索过滤了权限，但关键词检索没过滤，就可能把用户不该看到的内容召回。

所以本节的关键词检索也支持：

- `permission_group`
- `business_domain`
- `doc_type`
- `source`

混合检索时，两路都传同样的过滤条件。

### 19. 为什么本节不接真实 Qdrant hybrid search

Qdrant 支持更高级的检索能力，例如稀疏向量和多路查询。

但本节不直接接。

原因是：

- 我们还在学习混合检索的底层流程
- 先用本地关键词检索更容易理解
- 不需要打开 VMware
- 不引入更多外部依赖

等理解了基础逻辑，再学 Qdrant sparse vector 或外部搜索引擎会更稳。

### 20. 本节代码的学习价值

本节代码重点不是“做一个完美搜索引擎”。

重点是让你看懂：

```text
关键词召回怎么来
向量召回怎么来
两路结果怎么合并
为什么要去重
为什么要分数归一化
为什么要保留 retrieval_sources
```

这些是后续学 BM25、RRF、rerank、LangChain retriever 都要用的底层知识。

## 二、本节主题系统讲解

### 1. 第 26 节在阶段 4 里的位置

第 25 节学的是：

```text
怎么调已有向量检索参数。
```

第 26 节学的是：

```text
向量检索之外，再加一路关键词检索。
```

它是 RAG 从“单路检索”走向“多路召回”的第一步。

### 2. 本节新增 `app/rag/hybrid.py`

这个模块包含两部分：

```text
关键词检索
混合融合
```

主要对象：

- `KeywordSearchResult`
- `SimpleKeywordRetriever`
- `HybridSearchResult`
- `HybridSearchWeights`

主要函数：

- `extract_keyword_terms()`
- `fuse_hybrid_results()`
- `hybrid_retrieve()`

### 3. `extract_keyword_terms()` 做什么

它把用户问题或 chunk 文本转成关键词列表。

它处理两类文本：

1. 英文、数字、下划线

   ```text
   ABC123
   order_id
   refund
   ```

2. 中文连续文本

   用二元/三元 ngram 做粗略切分。

例如：

```python
extract_keyword_terms("订单 ABC123 退款多久到账？")
```

会包含：

```text
订单
abc123
退款
多久
到账
```

### 4. `SimpleKeywordRetriever` 做什么

它接收一批 `RagChunk`：

```python
SimpleKeywordRetriever(chunks)
```

然后可以执行：

```python
search("退款多久到账？", top_k=5)
```

它会：

```text
提取 query terms
过滤 metadata
给每个 chunk 做关键词匹配
按 score 排序
返回 KeywordSearchResult
```

### 5. `KeywordSearchResult` 里有什么

它包含：

```text
chunk_id
content
metadata
score
matched_terms
```

其中 `matched_terms` 很重要。

它能告诉你：

```text
这个 chunk 为什么被关键词检索命中？
到底命中了哪些词？
```

这对调试很有帮助。

### 6. 本节关键词 score 怎么算

本节是教学版简单打分。

思路是：

```text
query terms 里命中的词越多，分数越高。
词越长，权重越高。
同一个词多次出现最多加到 3 次。
最终分数限制在 0 到 1。
```

这不是 BM25。

它只是帮助我们跑通关键词召回和混合融合。

### 7. `HybridSearchResult` 里有什么

它包含：

```text
chunk_id
content
metadata
hybrid_score
vector_score
keyword_score
retrieval_sources
matched_terms
```

其中 `retrieval_sources` 可能是：

```text
["vector"]
["keyword"]
["vector", "keyword"]
```

如果一个 chunk 同时被两路命中，说明它更值得关注。

### 8. `fuse_hybrid_results()` 做什么

它接收：

```text
vector_chunks
keyword_results
```

然后：

```text
按 chunk_id 合并
分别归一化 vector_score 和 keyword_score
按权重计算 hybrid_score
按 hybrid_score 排序
返回 final top_k
```

这是本节的融合核心。

### 9. `HybridSearchWeights` 做什么

它控制向量和关键词的权重：

```python
HybridSearchWeights(
    vector_weight=0.7,
    keyword_weight=0.3,
)
```

它会拒绝：

```text
vector_weight = 0
keyword_weight = 0
```

因为两边权重都为 0，融合分数就没有意义。

### 10. `hybrid_retrieve()` 做什么

它是完整混合检索编排函数。

流程是：

```text
query
-> retrieve_top_k() 做向量检索
-> keyword_retriever.search() 做关键词检索
-> fuse_hybrid_results() 合并融合
```

它也会把同样的 metadata filter 传给两路检索。

### 11. 为什么关键词检索用本地 chunks

本节关键词检索直接基于 `RagChunk` 列表。

这有几个好处：

- 不需要外部搜索引擎
- 不需要 Qdrant
- 不需要网络
- 便于测试
- 便于理解

缺点是：

- 只适合小数据量学习
- 真实生产不应该把所有文档都放内存里粗暴扫描

后续如果数据变多，就应该接搜索引擎或数据库索引。

### 12. 为什么新增 `rag_keyword_search_preview.py`

这个脚本不做向量检索。

它只让你观察关键词检索的效果。

运行：

```powershell
uv run python scripts/rag_keyword_search_preview.py
```

它会输出：

```text
score
source
section
chunk_id
matched terms
```

这个脚本帮助你直观看到：

```text
关键词检索命中了什么，为什么命中。
```

### 13. 当前脚本输出说明

本节运行脚本得到类似结果：

```text
query: 退款多久到账？
1. score=0.1818 source=refund-return-policy.md section=退款到账时间 matched=退款, 到账
2. score=0.0909 source=logistics-tracking-faq.txt matched=退款
3. score=0.0909 source=refund-return-policy.md section=退款退货规则 matched=退款
```

这说明：

- 最相关结果命中了“退款”和“到账”
- 一些只命中“退款”的 chunk 也被召回
- 简单关键词检索会带来噪声

这正是后续 rerank 要解决的问题。

### 14. 为什么本节测试不真实调用 Qdrant

本节测试的是：

```text
关键词检索逻辑
融合逻辑
参数传递
metadata filter
去重和排序
```

这些不需要真实 Qdrant。

向量检索部分继续用 `FakeVectorStoreReader`。

这样测试稳定、快、不依赖 VMware。

### 15. 本节完成后下一步是什么

下一节是：

```text
rerank 重排序是什么
```

混合检索会召回更多候选结果。

候选结果多了，就更需要一个更强的重排序步骤判断谁最相关。

所以顺序是合理的：

```text
先学混合召回
再学 rerank
```

## 三、本节代码改动说明

### 1. 新增 `app/rag/hybrid.py`

它承载关键词检索和混合融合。

当前没有拆成多个文件，是为了学习阶段保持集中。

后续如果复杂，可以拆成：

```text
keyword_retriever.py
hybrid_retriever.py
fusion.py
```

### 2. 新增 `SimpleKeywordRetriever`

它用本地 `RagChunk` 列表做关键词检索。

它支持：

- `top_k`
- `min_score`
- `permission_group`
- `business_domain`
- `doc_type`
- `source`

这保证关键词检索也遵守基本 metadata 边界。

### 3. 新增 `fuse_hybrid_results()`

它负责：

- 合并向量结果和关键词结果
- 按 `chunk_id` 去重
- 保留 `vector_score`
- 保留 `keyword_score`
- 保留 `retrieval_sources`
- 保留 `matched_terms`
- 计算 `hybrid_score`

### 4. 新增 `hybrid_retrieve()`

它是完整编排入口。

它调用现有：

```python
retrieve_top_k()
```

再调用：

```python
keyword_retriever.search()
```

最后调用：

```python
fuse_hybrid_results()
```

### 5. 新增 `test_rag_hybrid.py`

测试覆盖：

- 中文/英文关键词提取
- 关键词检索排序
- metadata filter
- top_k 和 min_score
- hybrid fusion 合并去重
- 权重校验
- 完整 `hybrid_retrieve()`

### 6. 新增 `rag_keyword_search_preview.py`

这是本地学习脚本。

它不连接 Qdrant。

它让你直接观察关键词召回的结果和命中词。

## 四、常见误区

### 误区 1：有向量检索就不需要关键词检索

不对。

向量检索对语义相似很强，但对编号、专有名词、错误码、固定术语可能不够稳。

### 误区 2：关键词检索一定比向量检索更准

不对。

关键词检索不理解语义。

用户换一种说法，它可能搜不到。

### 误区 3：混合检索就是把两个列表拼起来

不够。

还要去重、融合分数、排序、保留来源信息。

### 误区 4：vector_score 和 keyword_score 可以直接相加

不严谨。

它们来自不同分数体系。

本节先做简单归一化再加权融合。

### 误区 5：本节简单关键词检索就是生产级搜索

不是。

它只是教学版。

生产系统通常需要 BM25、搜索引擎、中文分词、同义词、停用词、rerank 等能力。

### 误区 6：关键词检索不需要权限过滤

错误。

两路检索都必须遵守权限边界。

否则混合检索可能把用户不该看到的内容召回。

## 五、本节练习

### 练习 1：解释为什么只靠向量检索不够

题目：

为什么企业 RAG 里只靠向量检索可能不够？

参考答案：

因为向量检索擅长语义相似，但对订单号、错误码、政策编号、产品型号、固定术语等需要精确匹配的内容可能不够稳。这些场景更适合关键词检索补充。

### 练习 2：解释为什么只靠关键词检索不够

题目：

为什么只靠关键词检索也不够？

参考答案：

因为关键词检索不理解同义表达。如果用户说法和文档说法不一致，例如“钱什么时候退回来”和“退款到账时间”，普通关键词检索可能搜不到。

### 练习 3：说出混合检索流程

题目：

请说出本节混合检索的基本流程。

参考答案：

用户问题先分别走向量检索和关键词检索，两路各返回一批 chunks，然后按 `chunk_id` 合并去重，归一化分数并加权融合，最后按 `hybrid_score` 排序取最终结果。

### 练习 4：解释为什么要去重

题目：

为什么混合检索必须去重？

参考答案：

因为同一个 chunk 可能同时被向量检索和关键词检索命中。如果不去重，模型上下文里会出现重复内容，浪费 token 并干扰回答。

### 练习 5：解释为什么不能直接相加分数

题目：

为什么不能直接把 `vector_score` 和 `keyword_score` 相加？

参考答案：

因为它们来自不同分数体系，含义和尺度不同。向量分数可能是相似度，关键词分数可能是词匹配分。直接相加不严谨，需要先归一化或使用更成熟的融合方法。

### 练习 6：解释 `retrieval_sources`

题目：

`HybridSearchResult.retrieval_sources` 有什么用？

参考答案：

它记录一个结果来自哪些检索通道，例如 `vector`、`keyword`，或者两者都有。这样可以调试某个 chunk 是语义召回来的，还是关键词召回来的。

### 练习 7：判断 metadata filter

题目：

混合检索时，为什么关键词检索也要应用 `permission_group`？

参考答案：

因为权限边界必须对所有召回通道一致。如果向量检索过滤权限，但关键词检索不过滤，就可能召回用户无权看到的内容。

### 练习 8：解释本节为什么不实现 BM25

题目：

为什么本节不直接实现完整 BM25？

参考答案：

因为本节重点是理解混合检索流程：两路召回、合并、去重、融合排序。完整 BM25 会引入文档频率、长度归一化、中文分词等额外复杂度，容易转移学习重点。

### 练习 9：解释为什么下一节适合学 rerank

题目：

为什么混合检索之后适合学习 rerank？

参考答案：

混合检索会召回更多候选 chunks，其中会有噪声。rerank 可以在候选结果中重新判断相关性，把真正最适合回答的问题排到前面。

## 六、自测问题

### 自测 1

问题：

向量检索擅长什么？

答案：

擅长语义相似、同义表达、自然语言问法和文档说法不完全一致的场景。

### 自测 2

问题：

关键词检索擅长什么？

答案：

擅长精确词、编号、错误码、政策条款、产品名、固定术语等明确出现的内容。

### 自测 3

问题：

混合检索的核心思想是什么？

答案：

同时使用向量检索和关键词检索，两路召回后合并去重，再融合分数排序。

### 自测 4

问题：

本节用什么字段去重？

答案：

使用 `chunk_id` 去重。

### 自测 5

问题：

`matched_terms` 有什么用？

答案：

它记录关键词检索命中了哪些词，方便调试关键词结果为什么被召回。

### 自测 6

问题：

本节默认向量和关键词权重是多少？

答案：

默认 `vector_weight=0.7`，`keyword_weight=0.3`。

### 自测 7

问题：

为什么两边权重不能都为 0？

答案：

因为都为 0 时融合分数没有任何意义，无法排序。

### 自测 8

问题：

本节的关键词检索是生产级的吗？

答案：

不是。它是教学版简单关键词检索，用来理解混合检索流程。

### 自测 9

问题：

中文关键词检索为什么比英文麻烦？

答案：

中文没有天然空格分词，需要额外分词或 ngram。简单切分容易产生噪声。

### 自测 10

问题：

`hybrid_retrieve()` 内部调用了哪几个主要步骤？

答案：

调用 `retrieve_top_k()` 做向量检索，调用 `keyword_retriever.search()` 做关键词检索，再调用 `fuse_hybrid_results()` 做融合。

### 自测 11

问题：

为什么本节不需要打开 VMware？

答案：

因为关键词检索和融合逻辑可以在本地 chunks 和 fake vector store 上测试，不依赖真实 Qdrant。

### 自测 12

问题：

混合检索之后为什么还需要 rerank？

答案：

因为混合检索召回更多候选，也会带来更多噪声。rerank 可以进一步判断候选 chunks 与问题的相关性。

## 七、你应该能口述出的版本

你可以这样向别人解释本节：

```text
第 26 节讲混合检索。向量检索擅长语义相似，比如用户说法和文档说法不完全一样时仍然可能召回正确内容；关键词检索擅长精确命中，比如订单号、错误码、政策编号、产品型号和固定业务术语。两者各有短板，所以真实 RAG 常常会把两路检索结合起来。

混合检索的基本流程是：用户问题先走向量检索得到一批 chunks，再走关键词检索得到另一批 chunks，然后按 chunk_id 合并去重，分别归一化向量分数和关键词分数，用权重计算 hybrid_score，最后排序取 final_top_k。这样既保留语义召回能力，也能补充精确词召回能力。

本节代码新增 SimpleKeywordRetriever，它用本地 RagChunk 列表做教学版关键词检索，支持 top_k、min_score 和 metadata filter；新增 fuse_hybrid_results，把 vector results 和 keyword results 合并成 HybridSearchResult；新增 hybrid_retrieve，完成向量检索、关键词检索和融合的完整编排。

本节实现不是生产级搜索。简单中文 ngram 关键词检索会有噪声，分数融合也只是教学版。它的目的不是替代 BM25、搜索引擎或 rerank，而是让我们真正理解混合检索的底层流程。下一节学习 rerank，就是为了解决混合召回后候选结果多、噪声也多的问题。
```

## 八、本节产出

新增或修改：

- `projects/ai-service/app/rag/hybrid.py`
  - `KeywordSearchResult`
  - `SimpleKeywordRetriever`
  - `HybridSearchResult`
  - `HybridSearchWeights`
  - `extract_keyword_terms()`
  - `fuse_hybrid_results()`
  - `hybrid_retrieve()`
- `projects/ai-service/tests/test_rag_hybrid.py`
- `projects/ai-service/scripts/rag_keyword_search_preview.py`
- `notes/rag-stage4-26-hybrid-search.md`

## 九、参考资料

- [阶段 4 第 15 节：基础 top_k 检索](rag-stage4-15-basic-top-k-retrieval.md)
- [阶段 4 第 16 节：payload filter](rag-stage4-16-payload-filter.md)
- [阶段 4 第 25 节：检索质量调优](rag-stage4-25-retrieval-quality-tuning.md)
