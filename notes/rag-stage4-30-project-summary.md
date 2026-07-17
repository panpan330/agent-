# 阶段 4 第 30 节：阶段 4 主线项目验收和复盘

## 本节状态

已完成。

本节是阶段 4 企业知识库 RAG 主线的项目验收和复盘。

这里说的“主线”是指第 1 节到第 30 节这条 RAG 基础主线：

```text
RAG 概念
-> 文档
-> chunk
-> metadata
-> embedding
-> Qdrant
-> 入库
-> 检索
-> 过滤
-> 阈值
-> 生成回答
-> 引用来源
-> 无资料兜底
-> 错误处理
-> 测试
-> 文档维护
-> 真实 embedding 准备
-> 检索调优
-> 混合检索
-> rerank
-> 安全
-> 性能
-> 项目复盘
```

第 31 节之后会进入 Milvus 对比和扩展学习。

所以第 30 节不是整个阶段 4 所有内容的终点，而是：

```text
企业知识库 RAG 主线项目的阶段性验收点。
```

## 本节学习目标

学完本节，你应该能回答：

1. 阶段 4 到底学了什么。
2. 当前 RAG 项目的完整链路是什么。
3. `app/rag` 每个模块负责什么。
4. 哪些能力已经有代码支撑。
5. 哪些能力只是学习版，不是生产级。
6. 入库链路和问答链路分别怎么讲。
7. metadata 在整个 RAG 里贯穿了哪些能力。
8. 为什么 RAG 不是“向量库 + 大模型”这么简单。
9. 如果别人问你“这个 RAG 项目怎么设计的”，你应该怎么口述。
10. 当前项目离生产级企业 RAG 还差什么。
11. 为什么后面还要学 Milvus。
12. 下一阶段继续学习时应该怎么接上。

## 本节暂时不学什么

本节暂时不新增大型业务功能。

本节不做：

1. 不新增真实 HTTP RAG 问答接口。
2. 不接 Redis。
3. 不接真实 rerank 模型。
4. 不接真实 DLP。
5. 不改 Qdrant collection。
6. 不启动 Qdrant。
7. 不打开 VMware。
8. 不做 Milvus 安装。
9. 不做前端页面。
10. 不做线上部署。

本节的目标是：

```text
把已经学过的东西整理成一张完整、可讲、可复盘、可继续扩展的项目地图。
```

## 一、基础知识铺垫

### 1. 为什么需要阶段验收

学习一个项目时，只一节一节往前学是不够的。

因为你可能会出现一种情况：

```text
每一节都能跟着做
但合起来不知道系统到底长什么样
```

阶段验收就是为了防止这种问题。

它要检查：

1. 学过的概念是否能串起来。
2. 写过的代码是否形成体系。
3. 每个模块的职责是否清楚。
4. 哪些能力已经完成。
5. 哪些能力只是学习版。
6. 后续要补什么。

### 2. 项目复盘不是简单总结

简单总结可能只是：

```text
我们学了 RAG、Qdrant、embedding、retrieval。
```

这不够。

项目复盘要能回答：

```text
为什么这样设计？
输入是什么？
输出是什么？
中间经过哪些模块？
失败怎么处理？
安全怎么处理？
测试怎么保证？
后续怎么扩展？
```

你真正掌握一个项目，不是因为你看过代码，而是因为你能把这些问题讲清楚。

### 3. 什么叫“RAG 主线”

RAG 主线不是某一个函数。

它是一条完整链路：

```text
文档如何进入知识库
知识如何变成可检索 chunk
用户问题如何找到相关 chunk
chunk 如何进入模型上下文
模型如何根据资料回答
回答如何带出处
没有资料时如何拒答
错误、安全、性能如何处理
```

这条链路就是本阶段要建立的主线。

### 4. 为什么 RAG 不是“向量库 + 大模型”

很多人会把 RAG 简化成：

```text
把文档放进向量库
用户提问时查向量库
再给大模型回答
```

这个说法只对了一小部分。

真实 RAG 至少还要考虑：

1. 文档格式。
2. 文本清洗。
3. chunk 策略。
4. metadata。
5. embedding 模型。
6. 向量库 schema。
7. payload filter。
8. score threshold。
9. 混合检索。
10. rerank。
11. 引用来源。
12. 无资料兜底。
13. 权限和安全。
14. 缓存和性能。
15. 测试和 fake。
16. 文档更新和重新入库。

所以企业 RAG 是一个系统工程。

### 5. RAG 的两个核心流水线

RAG 通常有两个核心流水线：

```text
入库流水线
问答流水线
```

入库流水线负责：

```text
source documents -> chunks -> embeddings -> vector store
```

问答流水线负责：

```text
query -> retrieve -> context -> generate -> answer
```

本阶段就是围绕这两条线逐步搭起来的。

### 6. 入库流水线解决什么问题

入库流水线解决的是：

```text
怎样把原始文档变成机器可检索的知识。
```

原始文档本身通常不能直接检索。

你需要：

1. 读取文件。
2. 清洗文本。
3. 提取标题和 metadata。
4. 切成 chunk。
5. 生成 embedding。
6. 写入向量库。
7. 保存 payload。

这就是入库。

### 7. 问答流水线解决什么问题

问答流水线解决的是：

```text
怎样根据用户问题找资料，并让模型只根据资料回答。
```

它包括：

1. query embedding。
2. top_k 检索。
3. payload filter。
4. score_threshold。
5. 可选混合检索。
6. 可选 rerank。
7. 安全检查。
8. 构造 RAG context。
9. 调用模型。
10. 构造 citations。
11. no_context 兜底。

### 8. metadata 为什么贯穿全局

metadata 是阶段 4 里最重要的基础之一。

它不只是附加信息。

它支撑：

1. 文档来源。
2. 引用来源。
3. 权限过滤。
4. 文档类型过滤。
5. 业务领域过滤。
6. 删除旧文档。
7. 重新入库。
8. 调试。
9. 安全检查。
10. 缓存 key。

如果 metadata 设计不好，RAG 后面很多能力都会变得困难。

### 9. chunk 是 RAG 的关键单位

模型最终不是读取整份文档。

向量库也不是直接存整份文档。

RAG 里真正频繁流动的是 chunk。

chunk 需要同时携带：

```text
chunk_id
content
metadata
embedding vector
```

其中：

`content` 给模型看。

`metadata` 给系统用。

`vector` 给检索用。

`chunk_id` 给追踪和更新用。

### 10. 为什么要有 stable chunk_id

stable chunk_id 是稳定 chunk 标识。

它的作用包括：

1. 调试检索结果。
2. 构造引用来源。
3. 重排结果去重。
4. 文档刷新时定位。
5. 测试断言。
6. 复盘时讲清楚某段资料来自哪里。

没有稳定 ID，RAG 系统很难维护。

### 11. 检索质量不是只靠 embedding

embedding 很重要。

但检索质量还受很多因素影响：

1. chunk size。
2. chunk overlap。
3. 标题是否保留。
4. metadata 是否完整。
5. top_k。
6. score_threshold。
7. filter。
8. hybrid search。
9. rerank。
10. 文档本身质量。

所以 RAG 检索调优不是只换模型。

### 12. 生成回答不是 RAG 的全部

很多人觉得 RAG 的重点是最后的大模型回答。

但如果前面的检索资料不对，模型回答也很难对。

生成只是最后一步。

真正决定质量的往往是：

```text
文档质量
chunk 策略
metadata
检索
过滤
rerank
安全检查
```

### 13. citations 为什么重要

引用来源让回答可追溯。

没有 citations，用户只能相信模型。

有 citations，用户可以知道：

1. 答案来自哪份文档。
2. 来自哪个 section。
3. 来自哪个 chunk。
4. 后续怎么排查错误。

企业 RAG 里，citations 不只是锦上添花，而是可信度基础。

### 14. no_context 为什么重要

RAG 不应该任何问题都回答。

如果没有检索到足够资料，应该明确拒答。

no_context 的价值是：

1. 避免编造。
2. 明确知识库覆盖不足。
3. 提醒用户换问法。
4. 提醒团队补充知识。

### 15. 错误处理为什么要结构化

RAG 链路里可能失败的地方很多：

1. embedding 调用失败。
2. embedding 返回格式异常。
3. 向量库不可用。
4. collection 配置不匹配。
5. 模型调用失败。
6. 检索参数非法。

如果只抛普通异常，接口和日志会混乱。

结构化错误码可以让系统更可测、更可排查。

### 16. 测试为什么必须用 fake

RAG 测试如果依赖真实外部服务，会有很多问题：

1. 慢。
2. 贵。
3. 不稳定。
4. 需要 API key。
5. 结果可能波动。
6. CI 不好跑。

所以本阶段用 fake embedding、fake vector store、fake LLM 等方式，把核心逻辑测稳定。

### 17. 学习版和生产版要分清

本项目里很多能力是学习版。

学习版的目标是：

```text
帮助你理解概念、流程、边界和测试方式。
```

生产版还需要：

1. 更强的可靠性。
2. 更复杂的权限系统。
3. 更成熟的缓存。
4. 更全面的评测。
5. 更严格的安全。
6. 更完善的监控。
7. 更真实的业务接口。

这两者不能混淆。

### 18. 阶段验收要看“能不能讲”

你学完一个阶段，不能只看测试是否通过。

还要看你能不能讲：

```text
这个项目是做什么的
为什么这样拆模块
每个模块输入输出是什么
真实项目还差什么
如果出现问题怎么排查
```

能讲清楚，说明你不是只会照着代码跑。

## 二、本节主题系统讲解

### 1. 阶段 4 主线完成了什么

阶段 4 主线完成的是：

```text
一个企业知识库 RAG 的学习版后端核心能力。
```

它不是一个完整商业产品。

但它已经覆盖 RAG 的关键知识：

1. 基础概念。
2. 文档处理。
3. 向量化。
4. 向量库。
5. 检索。
6. 生成。
7. 引用。
8. 兜底。
9. 错误处理。
10. 测试。
11. 文档维护。
12. 调优。
13. 混合检索。
14. 重排序。
15. 安全。
16. 性能。

### 2. 当前项目目录

当前 RAG 代码主要在：

```text
projects/ai-service/app/rag
```

知识库样例在：

```text
projects/ai-service/data/knowledge_base
```

测试在：

```text
projects/ai-service/tests
```

手动预览脚本在：

```text
projects/ai-service/scripts
```

学习笔记在：

```text
notes
```

### 3. `documents.py` 的职责

`documents.py` 定义 RAG 内部基础数据模型：

```text
RagDocument
RagChunk
RetrievedChunk
```

它们分别表示：

`RagDocument`：加载和清洗后的原始文档。

`RagChunk`：切分后的知识片段。

`RetrievedChunk`：从向量库检索出来、准备进入后续流程的 chunk。

### 4. `loaders.py` 的职责

`loaders.py` 负责把 Markdown/txt 文件加载为 `RagDocument`。

它处理：

1. 文件读取。
2. UTF-8。
3. 基础清洗。
4. 标题提取。
5. metadata 线索提取。
6. 目录批量加载。

它位于入库流水线最前面。

### 5. `splitters.py` 的职责

`splitters.py` 负责把 `RagDocument` 切成 `RagChunk`。

它关注：

1. chunk_size。
2. chunk_overlap。
3. 段落优先。
4. 标题上下文。
5. section metadata。
6. 稳定 chunk_id。

它决定知识被切成什么粒度。

### 6. `metadata.py` 的职责

`metadata.py` 负责 metadata 标准化、校验和 payload 白名单。

它让 metadata 不再是随便的 dict。

它明确哪些字段是必备的，哪些字段可以写入 Qdrant payload。

metadata 是权限、引用、过滤和文档维护的基础。

### 7. `embeddings.py` 的职责

`embeddings.py` 负责文本向量化。

它包含：

1. deterministic fake embedding。
2. OpenAI-compatible embedding adapter。
3. batch helper。
4. storage estimation。
5. EmbeddedChunk 模型。

fake embedding 用于学习和测试。

真实 adapter 用于后续接真实 embedding 模型。

### 8. `vector_store.py` 的职责

`vector_store.py` 负责对接 Qdrant。

它处理：

1. collection 校验。
2. point 组装。
3. upsert 写入。
4. 按 filter 删除 points。
5. query 检索。
6. response 解析。

它是 RAG 和向量数据库之间的适配层。

### 9. `ingestion.py` 的职责

`ingestion.py` 编排入库流程：

```text
load -> split -> embed -> store
```

它还支持：

1. 删除某个 source 的旧 chunks。
2. 刷新目录。
3. 重新入库前清理旧 points。

这让知识库不只是能新增，还能维护。

### 10. `filters.py` 的职责

`filters.py` 负责构造 Qdrant payload filter。

支持字段包括：

```text
permission_group
business_domain
doc_type
source
```

它是权限过滤和业务范围过滤的基础。

### 11. `retriever.py` 的职责

`retriever.py` 负责基础 top_k 检索编排：

```text
query
-> query embedding
-> payload filter
-> vector_store.query_similar
-> RetrievedChunk
```

它还支持：

```text
score_threshold
```

用于过滤低相关内容。

### 12. `generator.py` 的职责

`generator.py` 负责把 retrieved chunks 交给模型回答。

它包含：

1. RAG system prompt。
2. context 格式化。
3. user prompt 构造。
4. messages 构造。
5. 模型调用。
6. RagAnswer。
7. RagCitation。
8. no_context 兜底。

它是检索结果到自然语言回答的桥。

### 13. `errors.py` 的职责

`errors.py` 负责 RAG 错误映射。

它把底层异常转换成项目统一错误：

```text
RAG_EMBEDDING_FAILED
RAG_EMBEDDING_BAD_RESPONSE
RAG_VECTOR_STORE_FAILED
RAG_VECTOR_STORE_CONFIG_ERROR
```

这样接口层不会暴露混乱的底层异常。

### 14. `tuning.py` 的职责

`tuning.py` 是检索质量调优学习工具。

它帮助观察：

1. chunk_size 对 chunk 数量的影响。
2. chunk_overlap 对切分的影响。
3. top_k 对结果数量的影响。
4. score_threshold 对结果过滤的影响。

它不是自动调参系统。

它是帮助你建立调优观察能力。

### 15. `hybrid.py` 的职责

`hybrid.py` 负责混合检索学习版。

它包含：

1. 简单关键词检索。
2. 中文 ngram 关键词提取。
3. KeywordSearchResult。
4. HybridSearchResult。
5. 向量结果和关键词结果合并。
6. 分数归一化。
7. 加权融合。
8. 按 chunk_id 去重。

它让你理解为什么企业 RAG 不能只依赖向量检索。

### 16. `rerank.py` 的职责

`rerank.py` 负责召回结果重排序学习版。

它包含：

1. RerankCandidate。
2. RerankedChunk。
3. RerankScoreBreakdown。
4. RuleBasedReranker。
5. original_rank。
6. rerank_rank。
7. score_breakdown。

它让你理解 rerank 是“召回之后、生成之前”的精排步骤。

### 17. `security.py` 的职责

`security.py` 负责 RAG 安全检查学习版。

它检查：

1. permission_group 是否允许。
2. Prompt Injection 风险。
3. 敏感信息风险。

它输出：

```text
safe_chunks
blocked_chunk_ids
findings
```

它强调：

```text
不安全资料不要进入模型上下文。
```

### 18. `performance.py` 的职责

`performance.py` 负责 RAG 性能学习工具。

它包含：

1. 检索缓存 key。
2. query hash。
3. 内存 TTL cache。
4. cache stats。
5. batch plan。
6. operation timing。
7. near_timeout。
8. degradation decision。

它让你理解 RAG 不是只要能答，还要考虑成本、延迟、稳定性和降级。

### 19. `tests/rag_fakes.py` 的职责

`tests/rag_fakes.py` 提供可复用 fake：

1. FakeEmbeddingModel。
2. FakeVectorStoreReader。
3. FakeVectorStoreWriter。
4. make_retrieved_chunk。

这些 fake 让测试不依赖真实 Qdrant、真实 embedding 或真实模型。

### 20. scripts 的职责

当前 RAG 相关脚本包括：

```text
rag_ingest_smoke.py
rag_retrieve_smoke.py
rag_chunk_tuning_preview.py
rag_keyword_search_preview.py
rag_rerank_preview.py
rag_security_preview.py
rag_performance_preview.py
```

它们用于手动观察和学习。

不是生产定时任务。

### 21. 当前入库链路怎么讲

你可以这样讲入库链路：

```text
先从 data/knowledge_base 读取 Markdown/txt 文件。
loader 把文件清洗成 RagDocument，并提取 title、doc_type、business_domain、permission_group 等 metadata。
splitter 按段落、标题、chunk_size 和 overlap 切成 RagChunk。
metadata 模块校验并标准化 metadata，再构造 Qdrant payload。
embedding 模块把 chunk content 变成向量。
vector_store 模块把 chunk_id、content、metadata、vector 组装成 Qdrant point。
ingestion 模块负责把 load、split、embed、store 串起来。
```

### 22. 当前问答链路怎么讲

你可以这样讲问答链路：

```text
用户问题进入 retriever。
retriever 先生成 query embedding。
再根据 permission_group、business_domain、doc_type、source 构造 payload filter。
然后调用 Qdrant 查询 top_k 相似 chunk。
score_threshold 可以过滤低相关结果。
检索结果可以进入 hybrid、rerank、安全检查等增强步骤。
安全通过的 chunks 会被 generator 格式化成 RAG context。
模型只根据这些资料回答。
后端根据 chunks 构造 citations。
如果没有可用资料，则返回 no_context，不调用模型硬答。
```

### 23. 当前有哪些学习版能力

学习版能力包括：

1. DeterministicHashEmbeddingModel。
2. SimpleKeywordRetriever。
3. RuleBasedReranker。
4. RagSecurityPolicy 规则扫描。
5. InMemoryTtlCache。
6. 预览脚本。
7. fake vector store。

这些不是生产级最终方案。

但它们帮助你理解核心概念。

### 24. 当前有哪些接近真实工程的能力

比较接近真实工程思路的能力包括：

1. OpenAI-compatible embedding adapter。
2. Qdrant REST adapter。
3. payload filter。
4. score_threshold。
5. source 删除和重新入库。
6. Pydantic 模型校验。
7. 结构化 citations。
8. no_context 状态。
9. 统一错误码。
10. fake 分层测试。

这些都是生产项目也会有的设计方向。

### 25. 当前项目还不是生产级的原因

当前项目还不是生产级，原因包括：

1. 没有真实文件上传接口。
2. 没有完整 RAG HTTP 问答接口。
3. 没有真实权限系统。
4. 没有 Redis 缓存。
5. 没有真实 rerank 模型。
6. 没有完整 DLP。
7. 没有 RAG eval。
8. 没有监控告警。
9. 没有 Docker Compose 集成。
10. 没有前端管理页面。
11. 没有多租户隔离。
12. 没有生产级日志和审计。

这不是失败。

这是学习阶段的正常边界。

### 26. 阶段 4 的核心收获

阶段 4 的核心收获不是“我会用 Qdrant”。

真正的核心收获是：

```text
我知道企业知识库 RAG 由哪些环节组成，
知道每个环节解决什么问题，
知道每个环节的输入输出，
知道哪些地方容易出错，
知道如何用测试隔离外部依赖，
知道生产化还要补哪些能力。
```

### 27. 阶段 4 和阶段 3 的关系

阶段 3 学的是：

```text
模型如何调用工具，如何访问 Java 业务服务。
```

阶段 4 学的是：

```text
模型如何根据企业知识库回答问题。
```

未来智能工单 Agent 会把两者结合：

```text
先用 RAG 查政策和规则
再用 Tool Calling 查订单或创建工单
最后用 LangGraph 编排多步骤流程
```

### 28. 为什么后面还要学 Milvus

你前面问过 Milvus。

现在 Qdrant 已经跑通过，RAG 主线也基本完整。

接下来学 Milvus 是为了：

1. 了解另一类主流向量数据库。
2. 对比 Qdrant 和 Milvus 的概念。
3. 理解 collection/schema/field/index。
4. 理解不同向量库的取舍。
5. 面试时能解释“为什么选择某个向量库”。

Milvus 不是替代前面内容。

它是扩展你的向量数据库视野。

## 三、阶段 4 主线验收清单

### 1. 概念验收

你应该能解释：

1. RAG 是什么。
2. RAG 和 prompt stuffing 的区别。
3. RAG 和微调的区别。
4. RAG 和 Tool Calling 的区别。
5. embedding 是什么。
6. 向量相似度是什么。
7. chunk 为什么重要。
8. metadata 为什么重要。
9. vector store 负责什么。
10. retrieve 和 generate 的区别。

### 2. 入库验收

你应该能解释：

1. 文档如何加载。
2. 文本为什么要清洗。
3. chunk_size 和 overlap 如何影响检索。
4. metadata 如何从文档进入 chunk。
5. embedding 如何生成。
6. Qdrant point 里有什么。
7. payload 保存什么。
8. 文档更新为什么要先删旧 chunks。

### 3. 检索验收

你应该能解释：

1. query embedding 是什么。
2. top_k 是什么。
3. score 是什么。
4. score_threshold 为什么存在。
5. payload filter 怎么限制范围。
6. RetrievedChunk 里有什么。
7. 为什么低相关内容不应该交给模型。

### 4. 生成验收

你应该能解释：

1. retrieved chunks 如何变成 context。
2. system prompt 负责什么。
3. user prompt 里为什么要写回答规则。
4. 为什么无资料时不调用模型硬答。
5. citations 为什么由后端构造。
6. score 和 chunk_id 不能当成业务事实。

### 5. 增强检索验收

你应该能解释：

1. 为什么要做调优。
2. 为什么要混合检索。
3. 关键词检索和向量检索各自优缺点。
4. 为什么要去重。
5. 为什么要分数归一化。
6. rerank 在哪里。
7. rerank 和 retrieve 的区别。

### 6. 安全验收

你应该能解释：

1. 权限过滤为什么不能交给模型。
2. permission_group 为什么重要。
3. Prompt Injection 是什么。
4. RAG Prompt Injection 为什么危险。
5. 敏感信息为什么不能随便进模型上下文。
6. safe_chunks 是什么。
7. findings 为什么要结构化。
8. evidence 为什么要脱敏。

### 7. 性能验收

你应该能解释：

1. RAG 为什么可能慢。
2. 缓存 key 为什么不能只用 query。
3. TTL 是什么。
4. embedding 为什么适合 batch。
5. timeout 为什么必须有。
6. near_timeout 的意义。
7. 降级和失败的区别。
8. 缓存不能突破权限边界。

### 8. 测试验收

你应该能解释：

1. 为什么 RAG 测试要用 fake。
2. FakeEmbeddingModel 解决什么问题。
3. FakeVectorStoreReader 解决什么问题。
4. FakeVectorStoreWriter 解决什么问题。
5. 为什么单元测试不应该真实调用模型。
6. 为什么接口测试和服务测试要分层。

## 四、当前项目运行和验证方式

### 1. Python 全量测试

在：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run pytest -q
```

当前阶段已验证全量通过。

### 2. Java mock 服务测试

在：

```powershell
cd D:\wendang\java+python+ai\projects\java-mock-service
uv run pytest -q
```

Java mock 服务在阶段 3 为工具调用打基础，阶段 4 主要没有修改它。

### 3. 不需要 Qdrant 的预览脚本

以下脚本不需要打开 VMware/Qdrant：

```powershell
uv run python scripts/rag_chunk_tuning_preview.py
uv run python scripts/rag_keyword_search_preview.py
uv run python scripts/rag_rerank_preview.py
uv run python scripts/rag_security_preview.py
uv run python scripts/rag_performance_preview.py
```

它们适合学习观察。

### 4. 需要 Qdrant 的脚本

以下脚本涉及 Qdrant：

```powershell
uv run python scripts/rag_ingest_smoke.py
uv run python scripts/rag_retrieve_smoke.py
```

如果后续要运行它们，需要启动 VMware Ubuntu 里的 Qdrant。

## 五、阶段 4 学习版和生产级差距

### 1. 文档接入差距

当前是本地 Markdown/txt 示例文档。

生产级可能需要：

1. 文件上传。
2. PDF/Word/Excel 解析。
3. 网页抓取。
4. 数据库同步。
5. 权限继承。
6. 文档版本。
7. 文档审核。

### 2. 检索能力差距

当前有基础 top_k、filter、threshold、hybrid、rerank 学习版。

生产级可能需要：

1. 真实 BM25。
2. 真实 rerank 模型。
3. query rewrite。
4. multi-query。
5. parent-child retrieval。
6. section-level retrieval。
7. 多向量检索。

### 3. 生成能力差距

当前有基础 grounded answer。

生产级可能需要：

1. 更严格的输出格式。
2. 引用到句级。
3. 回答后校验。
4. hallucination 检测。
5. 多语言支持。
6. 用户反馈闭环。

### 4. 安全能力差距

当前是规则扫描学习版。

生产级可能需要：

1. 统一权限中心。
2. 多租户隔离。
3. DLP。
4. 文档入库安全审核。
5. 输出安全检查。
6. 审计日志。
7. 敏感字段分级。

### 5. 性能能力差距

当前是学习版内存 TTL cache 和降级模型。

生产级可能需要：

1. Redis。
2. 限流。
3. 熔断。
4. 队列。
5. 异步入库。
6. 监控告警。
7. 压测。
8. 分布式部署。

### 6. 评测能力差距

当前还没有完整 RAG eval。

后续需要：

1. 标准问题集。
2. 期望答案。
3. 期望来源。
4. 检索命中率。
5. 引用准确率。
6. 回答质量评分。
7. 回归测试。

## 六、如果别人问你这个项目怎么讲

### 1. 30 秒版本

可以这样讲：

我做了一个企业知识库 RAG 学习项目。它把 Markdown/txt 知识文档加载、清洗、切 chunk，生成 embedding 后写入 Qdrant。用户提问时，系统会生成 query embedding，通过 payload filter 和 score_threshold 检索相关 chunk，再把检索结果整理成模型上下文生成回答，并由后端返回结构化引用来源。项目还补了文档更新、fake 测试、混合检索、rerank、安全检查和性能基础。

### 2. 2 分钟版本

可以这样讲：

这个 RAG 项目分成入库和问答两条链路。入库链路里，loader 读取 Markdown/txt 文档，splitter 按段落和标题切 chunk，metadata 模块校验 source、title、section、doc_type、business_domain、permission_group 等字段，embedding 模块生成向量，vector_store 模块把 chunk 写入 Qdrant。问答链路里，retriever 把用户问题转成 query embedding，通过 Qdrant 取回 top_k chunk，并支持 payload filter 和 score_threshold。随后可以经过混合检索、rerank 和安全检查，最后 generator 把 safe chunks 组织成上下文调用模型，回答同时返回 citations。如果没有资料，系统返回 no_context，不硬答。

项目还做了错误映射、fake embedding/fake vector store 测试、文档删除和重新入库、检索参数调优、Prompt Injection 和敏感信息检查、缓存 key/TTL/batch/降级等学习版工程能力。

### 3. 面试版重点

面试时可以强调：

1. 我不是只调用向量库，而是拆了完整 RAG 流程。
2. 我理解入库和问答是两条不同链路。
3. 我用 metadata 支撑权限、引用、过滤和更新。
4. 我知道 top_k、score_threshold、chunk_size、overlap 怎么影响结果。
5. 我知道为什么需要 no_context。
6. 我知道引用来源应该由后端根据 retrieved chunks 生成。
7. 我用 fake 隔离真实模型和向量库做测试。
8. 我知道当前实现哪些是学习版，生产还要补什么。

## 七、常见误区

### 误区 1：跑通一次 Qdrant 就等于会 RAG

不对。

跑通只是开始。

RAG 还包括文档处理、metadata、过滤、调优、安全、性能和评测。

### 误区 2：embedding 模型越强，RAG 就越好

不一定。

chunk、metadata、文档质量、filter、rerank 都会影响效果。

### 误区 3：RAG 可以回答所有问题

不可以。

知识库没有资料时，RAG 应该拒答或提示补充资料。

### 误区 4：引用来源可以让模型自己编

不可以。

引用来源应该由后端根据 retrieved chunks 构造。

### 误区 5：安全可以最后再补

不应该。

权限、注入和敏感信息应该从 RAG 链路设计时就考虑。

### 误区 6：缓存只是性能问题

不只是。

缓存也会影响权限、安全和正确性。

### 误区 7：测试真实模型才是真测试

不是。

大部分逻辑应该用 fake 做稳定测试，真实模型调用适合少量 smoke test 或集成测试。

## 八、本节练习

### 练习 1：说出 RAG 入库链路

问题：

请按顺序说出本项目的 RAG 入库链路。

参考答案：

```text
load documents
-> clean text
-> split chunks
-> validate metadata
-> embed chunks
-> build Qdrant points
-> upsert into vector store
```

### 练习 2：说出 RAG 问答链路

问题：

请按顺序说出本项目的 RAG 问答链路。

参考答案：

```text
query
-> query embedding
-> payload filter
-> vector search top_k
-> score_threshold
-> optional hybrid/rerank/security
-> build context
-> model answer
-> backend citations
-> no_context fallback when needed
```

### 练习 3：解释 metadata 的作用

问题：

metadata 在本项目里支撑了哪些能力？

参考答案：

metadata 支撑来源追踪、引用来源、权限过滤、业务领域过滤、文档类型过滤、按 source 删除旧 chunks、重新入库、安全检查和缓存 key 设计。

### 练习 4：解释为什么 citations 由后端生成

问题：

为什么不让模型自己编 citations？

参考答案：

因为模型可能编造来源。后端根据实际 retrieved chunks 构造 citations，可以保证来源和上下文一致，更可追溯。

### 练习 5：解释 no_context

问题：

no_context 解决什么问题？

参考答案：

它在没有可用检索资料时阻止模型硬答，避免编造，同时给用户建议和知识库补充方向。

### 练习 6：解释 fake 测试

问题：

为什么 RAG 单元测试大量使用 fake？

参考答案：

因为真实模型和向量库慢、贵、不稳定，还依赖外部环境。fake 可以稳定测试业务逻辑、错误处理和编排边界。

### 练习 7：区分学习版和生产版

问题：

请举出本项目中三个学习版能力。

参考答案：

DeterministicHashEmbeddingModel、SimpleKeywordRetriever、RuleBasedReranker、规则版安全扫描、InMemoryTtlCache 都是学习版能力。

### 练习 8：解释后续为什么学 Milvus

问题：

既然已经用了 Qdrant，为什么还要学 Milvus？

参考答案：

为了理解另一种主流向量数据库的 collection、schema、field、index 和检索能力，并能对比 Qdrant 与 Milvus 的取舍。

## 九、自测问题

### 自测 1

问题：

RAG 主线有哪两条核心流水线？

答案：

入库流水线和问答流水线。

### 自测 2

问题：

`RagDocument` 和 `RagChunk` 的区别是什么？

答案：

`RagDocument` 表示加载清洗后的文档，`RagChunk` 表示切分后的知识片段。

### 自测 3

问题：

`RetrievedChunk` 表示什么？

答案：

表示从向量库检索出来、准备进入后续 RAG 流程的 chunk。

### 自测 4

问题：

payload filter 主要依赖什么？

答案：

依赖 metadata 字段，例如 permission_group、business_domain、doc_type、source。

### 自测 5

问题：

score_threshold 的作用是什么？

答案：

过滤低相关检索结果，避免弱相关资料进入模型上下文。

### 自测 6

问题：

hybrid search 解决什么问题？

答案：

结合关键词检索和向量检索，补足单一检索方式的不足。

### 自测 7

问题：

rerank 在 RAG 链路里处于什么位置？

答案：

召回之后、生成之前。

### 自测 8

问题：

安全检查应该在资料进入模型上下文之前还是之后？

答案：

之前。

### 自测 9

问题：

缓存 key 为什么要包含权限信息？

答案：

避免不同权限用户复用同一检索缓存导致越权。

### 自测 10

问题：

当前项目是不是生产级企业 RAG？

答案：

不是。它是学习版企业 RAG 主线项目，已经覆盖核心概念和模块，但生产还需要权限系统、DLP、评测、监控、Redis、部署等能力。

### 自测 11

问题：

为什么第 30 节不新增大功能？

答案：

因为本节目的是阶段验收和复盘，把已有主线整理成完整项目地图，确认能讲清楚、能验证、能继续扩展。

### 自测 12

问题：

阶段 4 主线后面接什么？

答案：

接 Milvus 学习和 Qdrant vs Milvus 对比。

## 十、你应该能口述出的版本

你可以这样完整口述：

阶段 4 我完成了一个企业知识库 RAG 的学习版后端主线。这个项目分成入库和问答两条流水线。入库时，系统从本地 Markdown/txt 知识库读取文档，清洗文本，提取 metadata，按段落和标题切 chunk，然后生成 embedding，把 chunk 内容、metadata 和向量写入 Qdrant。问答时，系统把用户问题转成 query embedding，通过 payload filter 和 score_threshold 检索相关 chunk，再经过可选的混合检索、rerank 和安全检查，把 safe chunks 组织成模型上下文生成回答，并由后端根据 retrieved chunks 返回 citations。如果没有可用资料，则返回 no_context，不让模型硬答。

这个阶段还补了工程能力：文档删除和重新入库、真实 embedding adapter 准备、fake embedding/fake vector store 测试、检索参数调优、关键词和向量混合检索、规则 rerank、Prompt Injection 和敏感信息安全检查、缓存 key、TTL cache、batch plan、timeout 和降级决策。当前项目不是生产级，但已经能清楚展示 RAG 系统的核心模块、边界和后续生产化方向。

## 十一、本节产出

本节新增：

```text
notes/rag-stage4-30-project-summary.md
```

本节更新：

```text
README.md
docs/learning-progress.md
docs/learning-resources.md
projects/ai-service/README.md
projects/ai-service/app/rag/README.md
```

本节没有新增业务代码。

本节验证重点是：

```text
阶段 4 主线笔记、索引、进度和全量测试保持一致。
```

## 十二、下一节衔接

下一节进入：

```text
阶段 4 第 31 节：Milvus 是什么，和 Qdrant 有什么区别
```

这一节会从概念开始，不会直接让你上来就安装 Milvus。

原因是：

你已经先用 Qdrant 跑通了一条完整 RAG 主线。

接下来再学 Milvus，就不是盲目安装工具，而是带着问题对比：

1. Milvus 的 collection 和 Qdrant collection 有什么区别。
2. Milvus schema/field/entity/index 是什么。
3. Milvus 更适合什么场景。
4. Qdrant 更适合什么场景。
5. 真实项目如何选择向量数据库。
