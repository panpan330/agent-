# 阶段 4 第 22 节：RAG 测试：fake embedding、fake vector store

## 本节状态

已完成。

前面几节我们已经有了 RAG 的几个关键能力：

```text
retrieve_top_k()
-> generate_answer_with_citations()
-> no_context
-> RAG 错误映射
```

第 22 节专门学习：

```text
这些能力应该怎么测试，为什么不能依赖真实 embedding、真实 Qdrant、真实模型。
```

本节不是单纯“多写几个测试文件”，而是要建立一个 RAG 工程里非常重要的习惯：

```text
核心逻辑用 fake 稳定测试，真实外部服务用少量 smoke test 手动或集成验证。
```

## 本节学习目标

学完本节，你要能讲清楚：

1. 为什么 RAG 自动化测试不能默认依赖真实 embedding、Qdrant 和大模型。
2. fake、mock、stub、spy 大概有什么区别。
3. 什么是 fake embedding。
4. 什么是 fake vector store。
5. 为什么 fake 不只要“返回数据”，还要记录调用参数。
6. RAG 测试应该分成单元测试、集成测试、手动 smoke test。
7. `retrieve_top_k()` 应该测试哪些边界。
8. `ingest_directory_to_vector_store()` 应该测试哪些边界。
9. `generate_answer_with_citations()` 为什么继续用 fake LLM。
10. no_context 和 error mapping 应该怎么测试。
11. 当前新增的 `tests/rag_fakes.py` 负责什么。
12. 什么时候该用真实 Qdrant，什么时候不该用。

## 本节暂时不学什么

本节只整理 RAG 自动化测试的 fake 基础。

暂时不做：

- 不启动 VMware。
- 不连接真实 Qdrant。
- 不调用真实 embedding API。
- 不调用真实大模型。
- 不做 `/rag-chat` API 测试。
- 不做大型评测集。
- 不做端到端性能测试。
- 不做 CI 里的 Docker Qdrant 集成测试。

这些后续会继续补。

## 一、基础知识铺垫

### 1. RAG 为什么特别需要测试隔离

普通纯函数测试很简单。

比如：

```text
输入字符串 -> 输出清洗后的字符串
```

只要给定输入，输出就稳定。

RAG 不一样。

RAG 链路里有很多外部依赖：

```text
embedding API
vector database
LLM API
文件系统
网络
环境变量
权限过滤配置
```

这些东西都有不确定性：

- 网络可能断。
- Qdrant 可能没启动。
- API key 可能没配置。
- 模型输出不完全稳定。
- embedding 模型可能升级。
- 第三方服务可能限流。
- 请求会产生费用。
- 本地和 CI 环境可能不同。

如果自动化测试依赖这些真实服务，测试会变得：

```text
慢、不稳定、贵、难排查。
```

所以 RAG 测试必须学会隔离外部依赖。

隔离不是为了“偷懒”，而是为了让测试稳定地验证我们自己的代码逻辑。

### 2. 自动化测试的目标是什么

自动化测试不是为了证明：

```text
真实大模型一定回答正确。
```

自动化测试更适合证明：

```text
我们的代码在给定输入下，会做出预期动作。
```

比如：

- query 会被 strip 后再传给 embedding。
- embedding 返回向量后，会传给 vector store。
- payload filter 会正确传给 vector store。
- score_threshold 会正确传给 vector store。
- chunks 为空时不会调用模型。
- chunks 不为空时会调用模型。
- citations 来自后端 retrieved chunks。
- embedding 失败会映射成 RAG 错误码。
- Qdrant 失败不会伪装成 no_context。

这些都可以用 fake 稳定测试。

真实模型回答质量，要靠后续评测集和人工验收。

### 3. fake、mock、stub、spy 是什么

这些词经常混用，先建立一个实用理解。

`stub`：

```text
返回固定结果的替身。
```

比如：

```text
不管输入什么，都返回 [[0.1, 0.2, 0.3, 0.4]]
```

`fake`：

```text
一个可运行的简化实现。
```

比如：

```text
FakeEmbeddingModel 根据输入条数返回同样数量的固定维度向量。
FakeVectorStoreReader 不连 Qdrant，但能记录 query_similar 参数并返回固定 chunks。
```

`mock`：

```text
更关注调用行为的替身，通常会断言某方法是否被调用、调用几次、参数是什么。
```

`spy`：

```text
真实或 fake 对象旁边的记录器，记录调用历史。
```

本节的 `FakeEmbeddingModel` 和 `FakeVectorStoreReader` 既是 fake，也带一点 spy 能力。

因为它们不仅返回数据，还记录：

- 调用了几次。
- 输入文本是什么。
- query_vector 是什么。
- top_k 是什么。
- payload_filter 是什么。
- score_threshold 是什么。

### 4. 为什么 fake 要记录调用参数

RAG 里很多 bug 不是“函数没返回”，而是“传错参数”。

比如：

- 用户问题没有 strip。
- `top_k` 没传进去。
- `payload_filter` 丢了。
- `score_threshold` 没传给 Qdrant。
- `with_payload` 错设成 False。
- `with_vector` 错设成 True，浪费传输。

如果 fake 只返回固定数据，不记录调用参数，就很难发现这些 bug。

所以一个好的 fake 应该同时支持：

```text
返回可控结果
记录调用参数
模拟异常
```

本节新增的 fake 就围绕这三点设计。

### 5. 为什么不能用真实 embedding 做单元测试

真实 embedding 有几个问题。

第一，依赖 API key。

第二，依赖网络。

第三，可能产生费用。

第四，返回向量维度和数值可能随模型变化。

第五，测试难以断言具体向量值。

第六，测试速度会变慢。

所以单元测试不要真实调用 embedding API。

单元测试应该关心：

```text
我们有没有正确调用 embedding_model.embed_texts()
我们有没有检查返回数量和维度
我们有没有把向量传给 vector store
```

这些用 fake embedding 就够了。

### 6. fake embedding 应该具备什么能力

本节新增：

```text
FakeEmbeddingModel
```

它应该具备 4 个能力：

1. 有 `dimension`。
2. 能按输入文本数量返回相同数量的向量。
3. 能记录调用时传入的 texts。
4. 能配置异常或坏响应，用来测试错误处理。

比如：

```python
FakeEmbeddingModel(dimension=4)
```

可以模拟正常 embedding。

```python
FakeEmbeddingModel(vectors=[])
```

可以模拟返回数量不对。

```python
FakeEmbeddingModel(vectors=[[0.1, 0.2]])
```

可以模拟维度不对。

```python
FakeEmbeddingModel(error=RuntimeError("embedding provider failed"))
```

可以模拟 embedding 服务失败。

### 7. 为什么不能用真实 Qdrant 做单元测试

真实 Qdrant 也不适合单元测试。

因为它需要：

- Docker 或外部服务。
- 端口可用。
- collection 已创建。
- 数据已写入。
- 网络连接正常。
- 测试后清理数据。

如果单元测试依赖真实 Qdrant，测试会变慢，也更容易因为环境问题失败。

真实 Qdrant 更适合：

```text
手动 smoke test
少量集成测试
上线前环境验证
```

不是每次单元测试都连。

### 8. fake vector store 应该具备什么能力

RAG 里 vector store 有两种角色。

查询侧：

```text
query_similar()
```

入库侧：

```text
ensure_collection()
upsert_embedded_chunks()
```

所以本节新增两个 fake：

```text
FakeVectorStoreReader
FakeVectorStoreWriter
```

`FakeVectorStoreReader` 负责：

- 记录 query_vector。
- 记录 top_k。
- 记录 payload_filter。
- 记录 score_threshold。
- 返回固定 RetrievedChunk。
- 模拟 vector store 错误。

`FakeVectorStoreWriter` 负责：

- 记录 ensure_collection 参数。
- 记录 upsert_embedded_chunks 参数。
- 保存写入的 embedded_chunks。
- 模拟 ensure_collection 错误。
- 模拟 upsert 错误。

这样我们不需要真实 Qdrant，也能测试检索和入库编排逻辑。

### 9. fake LLM 的位置

本项目之前已经有：

```text
tests/fakes.py
FakeOpenAICompatibleClient
FakeChatCompletions
```

它用于测试：

- 模型是否被调用。
- 传入的 messages 是否正确。
- 无 chunks 时是否不调用模型。
- 模型错误是否映射。
- usage token 是否能提取。

第 22 节不重复造 fake LLM。

因为已有 fake LLM 已经够用。

本节补的是 RAG 特有 fake：

```text
fake embedding
fake vector store
```

### 10. 单元测试、集成测试、smoke test 的区别

RAG 测试至少要分三层。

第一层：单元测试。

```text
不依赖真实外部服务。
使用 fake embedding、fake vector store、fake LLM。
运行快，适合每次改代码都跑。
```

第二层：集成测试。

```text
可能连接真实 Qdrant 或测试容器。
验证多个模块组合是否能工作。
数量少，运行频率低于单元测试。
```

第三层：smoke test。

```text
手动或脚本验证真实环境是否能跑通。
比如 scripts/rag_ingest_smoke.py 和 scripts/rag_retrieve_smoke.py。
```

不要把这三层混在一起。

如果所有测试都连真实 Qdrant，开发会很痛苦。

如果所有测试都只用 fake，不做 smoke test，又无法确认真实环境能跑。

正确做法是：

```text
大量 fake 单元测试 + 少量真实服务 smoke/integration 验证。
```

### 11. RAG 测试应该测什么，不测什么

单元测试应该测：

- 参数是否正确传递。
- 状态是否正确返回。
- 错误是否正确映射。
- 无资料时是否不调用模型。
- citations 是否来自 chunks。
- filter / threshold 是否进入 vector store。
- 入库时是否先 ensure collection 再 upsert。

单元测试不应该测：

- 真实 embedding 语义质量。
- 真实 Qdrant ANN 召回率。
- 真实模型回答是否优雅。
- 真实网络稳定性。
- 真实用户体验。

这些属于集成测试、评测集、人工验收和线上监控。

### 12. 为什么测试也要服务学习

你是为了真正学会，而不是只让测试变绿。

所以测试本身也要能读懂系统边界。

好的测试名字应该像一句说明：

```text
test_retrieve_top_k_passes_payload_filter_to_vector_store
```

它告诉你：

```text
这一测验证 retrieve_top_k 会把 payload_filter 传给 vector store。
```

坏的测试名字可能是：

```text
test_case_1
```

看不出意义。

本节的测试文件和 fake 命名，都是为了让你之后复盘时能读懂：

```text
RAG 的哪个边界被保护了。
```

### 13. 一条 RAG 查询应该怎么分层测试

一条完整 RAG 查询看起来像这样：

```text
用户问题
-> query embedding
-> vector store 检索
-> chunks
-> generator
-> answer / citations / no_context
```

它不应该只靠一个大测试覆盖。

更好的方式是分层测试。

第一层：测试 `retrieve_top_k()`。

重点验证：

- query 是否去空白。
- embedding 是否收到正确文本。
- top_k 是否传给 vector store。
- payload_filter 是否传给 vector store。
- score_threshold 是否传给 vector store。
- embedding 错误是否映射。
- vector store 错误是否映射。

这里用：

```text
FakeEmbeddingModel
FakeVectorStoreReader
```

第二层：测试 `RagAnswerService`。

重点验证：

- chunks 为空时不调用模型。
- chunks 不为空时调用模型。
- messages 是否包含检索资料。
- citations 是否来自 retrieved chunks。
- no_context 状态是否正确。

这里用：

```text
FakeChatCompletions
FakeOpenAICompatibleClient
```

第三层：以后测试 `/rag-chat` API。

重点验证：

- API 请求能进入 RAG pipeline。
- 正常回答能返回 answer + citations。
- no_context 能返回结构化状态。
- RAG 错误能被统一异常处理。

这里会组合使用：

```text
FakeEmbeddingModel
FakeVectorStoreReader
FakeChatCompletions
FastAPI dependency_overrides
```

第四层：真实 smoke test。

重点验证：

- 本地 Qdrant 是否能访问。
- collection 是否存在或能创建。
- 文档能真实写入。
- 查询能真实返回 points。

这里才使用：

```text
scripts/rag_ingest_smoke.py
scripts/rag_retrieve_smoke.py
真实 Qdrant
```

分层测试的好处是：

```text
哪一层坏了，就能更快定位问题。
```

如果只写一个端到端大测试，它失败时你很难马上知道是 embedding、Qdrant、prompt、模型还是 API 层的问题。

### 14. 一条 RAG 入库链路应该怎么分层测试

入库链路是：

```text
load documents
-> split chunks
-> embed chunks
-> ensure collection
-> upsert points
```

也要分层。

loader 测试：

```text
文件能不能读取？
编码是否按 UTF-8？
title/metadata 是否提取？
```

splitter 测试：

```text
chunk_size 是否生效？
chunk_overlap 是否生效？
chunk_id 是否稳定？
section metadata 是否正确？
```

metadata 测试：

```text
必备字段是否校验？
payload 白名单是否生效？
权限字段是否保留？
```

embedding 测试：

```text
输入 chunks 是否变成同数量 vectors？
维度是否正确？
坏响应是否被拒绝？
```

ingestion 编排测试：

```text
是否先 embed？
是否 ensure collection？
是否 upsert？
vector_size 是否来自 embedding_model.dimension？
distance 是否传入？
wait 是否传入？
```

真实 smoke test：

```text
文档是否真的写入 Qdrant？
Qdrant 里 points_count 是否增加？
payload 是否能 scroll 出来？
```

这就是入库测试策略。

不要指望一个 `ingest_directory_to_vector_store()` 测试验证所有细节。

它主要验证编排，细节由各模块自己的单元测试保护。

### 15. fake 测试能抓住哪些 bug

fake 测试很有用，但你要知道它能抓什么。

fake 能抓住：

- 参数没传。
- 参数传错。
- 调用顺序错。
- 状态返回错。
- 错误映射错。
- 无资料时不该调用模型却调用了。
- 有资料时 citations 没生成。
- embedding 返回数量不对时没有报错。
- vector store 错误被吞掉。
- upsert 没有被调用。

比如：

```text
score_threshold 没传给 vector store
```

`FakeVectorStoreReader.last_call` 可以直接抓到。

再比如：

```text
chunks=[] 时仍然调用模型
```

`FakeChatCompletions.calls` 可以抓到。

所以 fake 测试特别适合保护代码边界和参数传递。

### 16. fake 测试抓不住哪些 bug

fake 不是万能的。

fake 抓不住：

- 真实 embedding 语义效果差。
- Qdrant ANN 召回率不够。
- collection 索引配置不合理。
- 网络延迟太高。
- 大模型回答不忠实资料。
- 中文文档真实分布导致 chunk 效果差。
- score_threshold 在真实数据上太高或太低。
- rerank 效果不佳。
- 前端引用展示体验不好。

这些需要：

- 真实 smoke test。
- 集成测试。
- RAG eval 评测集。
- 人工抽查。
- 线上日志和监控。

所以不要说：

```text
fake 测试全过，所以 RAG 质量一定好。
```

更准确的说法是：

```text
fake 测试保证代码边界和调用逻辑正确；RAG 质量还要靠真实数据和评测验证。
```

### 17. fake vector store 和 `httpx.MockTransport` 的区别

本项目里有两种常见测试方式：

```text
FakeVectorStoreReader
httpx.MockTransport
```

它们解决的问题不一样。

`FakeVectorStoreReader` 用在业务编排测试里。

它假装自己就是一个 vector store reader，不关心 HTTP 细节。

适合测试：

```text
retrieve_top_k 有没有把 query_vector、filter、top_k、threshold 传进去。
```

`httpx.MockTransport` 用在 Qdrant 适配层测试里。

它模拟 HTTP 响应，检查请求体和响应解析。

适合测试：

```text
QdrantVectorStore 有没有发对 HTTP path、method、json body。
Qdrant 返回的 result/points 能不能被解析成 RetrievedChunk。
```

可以这样记：

```text
业务编排测试用 fake vector store。
HTTP 适配测试用 MockTransport。
真实环境验证用 smoke test。
```

如果用 fake vector store 测 Qdrant 请求体，那测不到。

如果用 MockTransport 测所有业务编排，测试会变得又长又分散。

### 18. fake 测试和 eval 的区别

RAG 后面会学评测，也就是 eval。

fake 测试和 eval 不是一回事。

fake 测试问的是：

```text
代码有没有按设计调用？
边界有没有处理？
错误有没有映射？
```

eval 问的是：

```text
系统回答质量好不好？
检索结果相关吗？
答案有没有忠实资料？
引用来源准不准？
```

举例。

fake 测试可以验证：

```text
top_k=5 被传给 vector store。
```

但它不能验证：

```text
top_k=5 在真实业务数据上是不是最优。
```

fake 测试可以验证：

```text
模型收到了检索上下文。
```

但它不能验证：

```text
模型是否正确理解了上下文。
```

所以后续 RAG eval 会补另一块能力。

当前第 22 节先解决：

```text
代码逻辑和边界是否可控。
```

### 19. 测试金字塔在 RAG 里的样子

可以用一个简单金字塔理解：

```text
          少量端到端 / smoke
       少量真实服务集成测试
    一些适配层测试(MockTransport)
大量单元测试(fake embedding/vector/LLM)
```

越底层，数量越多，运行越快，越稳定。

越上层，越接近真实环境，但数量要少。

如果金字塔倒过来：

```text
大量真实模型 + 真实 Qdrant 端到端测试
少量单元测试
```

开发会很痛苦。

因为每次改一点代码，都可能被环境、网络、费用、模型波动拖住。

### 20. 什么时候应该新增一个 fake

不是遇到外部依赖就马上写很复杂的 fake。

可以按这个标准判断：

应该新增 fake 的情况：

- 这个依赖会被多个测试复用。
- 真实依赖慢、不稳定或有费用。
- 测试需要记录调用参数。
- 测试需要模拟多种结果和错误。
- 后续 API 测试会继续用到。

不一定要新增 fake 的情况：

- 只在一个测试里用一次。
- 简单 monkeypatch 就够。
- 已有 fake 已经能表达。
- 你只是为了“看起来统一”。

本节新增 `tests/rag_fakes.py` 是因为 RAG 后面会持续用到 embedding、vector store、retrieved chunk 这些测试替身。

## 二、本节主题系统讲解

### 1. 第 22 节在 RAG 主线里的位置

前面我们已经实现了：

```text
load -> split -> embed -> store
query -> embed -> retrieve -> generate -> citations/no_context
```

第 22 节不新增业务能力，而是补工程能力：

```text
让这些 RAG 能力可以被稳定测试。
```

如果没有稳定测试，后面做 `/rag-chat` API 时会很危险。

因为一旦出了问题，很难判断是：

- embedding 调错了。
- filter 没传。
- vector store 出错。
- no_context 逻辑错。
- citations 逻辑错。
- 模型被错误调用。

所以本节是后续 API 编排前的测试地基。

### 2. 新增 `tests/rag_fakes.py`

本节新增：

```text
projects/ai-service/tests/rag_fakes.py
```

它集中放 RAG 测试 fake。

当前包含：

- `make_retrieved_chunk()`
- `FakeEmbeddingModel`
- `FakeVectorStoreReader`
- `FakeVectorStoreWriter`

为什么不放到 `app/rag`？

因为这些是测试工具，不是业务代码。

生产代码不应该依赖测试 fake。

### 3. `make_retrieved_chunk()` 做什么

它用于快速构造一个 `RetrievedChunk`。

默认内容是订单发货资料。

测试可以通过 overrides 改字段：

```python
make_retrieved_chunk(chunk_id="chunk-1", score=0.82)
```

这样避免每个测试都重复写一大段 `RetrievedChunk(...)`。

但它不是业务工厂，只是测试数据构造辅助。

### 4. `FakeEmbeddingModel` 做什么

它模拟 `EmbeddingModel`。

它能：

- 返回指定维度的向量。
- 记录 `embed_texts()` 收到的 texts。
- 返回手动配置的 vectors。
- 抛出手动配置的 error。

这让我们可以测试：

- query 是否去空白。
- embedding 是否被调用。
- embedding 返回数量错误时是否映射错误码。
- embedding provider 失败时是否映射错误码。

### 5. `FakeVectorStoreReader` 做什么

它模拟查询侧 vector store。

它能记录：

- `query_vector`
- `top_k`
- `payload_filter`
- `score_threshold`
- `with_payload`
- `with_vector`

它能返回固定 chunks，也能抛出错误。

这让我们可以测试：

```text
retrieve_top_k 有没有把正确参数传给 vector store。
```

这比真实连 Qdrant 更适合单元测试。

### 6. `FakeVectorStoreWriter` 做什么

它模拟入库侧 vector store。

它能记录：

- `ensure_collection(vector_size, distance)`
- `upsert_embedded_chunks(embedded_chunks, wait)`

它能保存写入的 `embedded_chunks`。

它也能模拟：

- ensure collection 失败。
- upsert 失败。

这让入库测试可以验证：

```text
load -> split -> embed -> ensure collection -> upsert
```

的编排顺序和参数。

### 7. 为什么没有把所有测试都重构

本节没有把所有 RAG 测试都大改。

原因是：

```text
重构测试也要控制范围。
```

当前重点是把最需要复用的 fake 提出来：

- retriever 测试。
- ingestion 测试。
- 后续 API 测试会用到的 chunk 构造。

`test_rag_generator.py` 里已经有更贴近本文件断言的本地构造函数，暂时不强行改。

这是一个工程取舍：

```text
先提炼真正会复用的部分，不为了统一而大范围扰动已有测试。
```

### 8. 当前项目 RAG 测试怎么分类

当前 RAG 测试可以这样看：

| 测试文件 | 类型 | 主要验证 |
| --- | --- | --- |
| `test_rag_documents.py` | 单元测试 | document/chunk 模型 |
| `test_rag_loaders.py` | 单元测试 | 文件加载和清洗 |
| `test_rag_splitters.py` | 单元测试 | chunk 切分 |
| `test_rag_metadata.py` | 单元测试 | metadata 标准化 |
| `test_rag_embeddings.py` | 单元测试 | fake embedding 生成和校验 |
| `test_rag_vector_store.py` | 适配层测试 | Qdrant 请求/响应适配，使用 `httpx.MockTransport` |
| `test_rag_retriever.py` | 单元测试 | query embedding + vector store reader 编排 |
| `test_rag_ingestion.py` | 单元测试 | load/split/embed/store 入库编排 |
| `test_rag_generator.py` | 单元测试 | context、answer、citations、no_context |
| `test_rag_errors.py` | 单元测试 | RAG 错误映射 |
| `test_rag_fakes.py` | 测试工具测试 | fake 工具自身行为 |

真实 Qdrant 验证目前主要在脚本里：

```text
scripts/rag_ingest_smoke.py
scripts/rag_retrieve_smoke.py
```

### 9. 为什么 fake 自己也要测试

你可能会问：

```text
fake 只是测试工具，为什么还要 test_rag_fakes.py？
```

因为 fake 会被很多测试复用。

如果 fake 自己有 bug，可能导致很多测试误判。

比如：

- fake 没记录调用参数。
- fake 返回向量数量不对。
- fake 没按配置抛错误。
- fake writer 没保存 upsert 的 chunks。

所以共享 fake 值得有少量测试。

这不是过度测试，而是保护测试工具本身。

### 10. 第 22 节完成后，对后续有什么帮助

后面做 `/rag-chat` API 时，可以直接组合：

```text
FakeEmbeddingModel
FakeVectorStoreReader
FakeChatCompletions
FakeOpenAICompatibleClient
```

来测试：

- 请求进来后是否检索。
- 检索结果是否交给 generator。
- no_context 是否返回正确结构。
- 模型是否只在有 chunks 时调用。
- citations 是否返回。
- 错误码是否被统一异常处理返回。

这就是本节的真正价值：

```text
先把 fake 工具准备好，后面 API 编排测试会更简单。
```

### 11. RAG 查询测试策略地图

以后测试一次完整 RAG 查询时，不要直接上来就写一个大而全的测试。

可以拆成：

```text
retriever 单元测试
generator 单元测试
pipeline/API 编排测试
smoke test
eval
```

每层回答的问题不同。

| 层级 | 主要问题 | 工具 |
| --- | --- | --- |
| retriever 单元测试 | query 是否变成 vector，filter/threshold 是否传给 store | FakeEmbeddingModel、FakeVectorStoreReader |
| generator 单元测试 | chunks 是否变成 prompt，模型是否按条件调用，citations/no_context 是否正确 | FakeChatCompletions |
| pipeline/API 编排测试 | retriever 和 generator 是否正确串起来 | fake embedding、fake vector store、fake LLM、dependency overrides |
| smoke test | 真实 Qdrant 和脚本是否能跑通 | 本地 Qdrant、smoke scripts |
| eval | 检索和回答质量是否达标 | 评测集、人工标注、指标 |

这张表要记住。

它能帮你判断：

```text
一个问题应该在哪一层测试。
```

### 12. RAG 入库测试策略地图

入库也可以拆成：

| 层级 | 主要问题 | 工具 |
| --- | --- | --- |
| loader 测试 | 文档读取和清洗是否正确 | 临时文件/样例文件 |
| splitter 测试 | chunk 切分是否稳定 | RagDocument 样例 |
| metadata 测试 | 必备字段和 payload 是否正确 | dict 样例 |
| embedding 测试 | embedding 结果数量和维度是否校验 | fake/deterministic embedding |
| ingestion 编排测试 | 是否按顺序 embed、ensure、upsert | FakeEmbeddingModel、FakeVectorStoreWriter |
| vector store 适配测试 | Qdrant HTTP 请求体和响应解析是否正确 | httpx.MockTransport |
| smoke test | 真实 Qdrant 是否写入成功 | 本地 Qdrant |

这说明：

```text
ingestion 测试不是替代 loader/splitter/metadata/vector_store 测试。
```

它只验证编排。

### 13. 为什么第 22 节没有引入 pytest monkeypatch

`monkeypatch` 很有用，后面也会见到。

但本节优先使用 fake 对象。

原因是：

```text
当前 RAG 函数本身已经通过参数接收 embedding_model 和 vector_store。
```

这叫依赖注入。

既然可以直接传 fake，就不需要 monkeypatch 去临时替换全局对象。

一般来说：

```text
能通过参数传 fake，就优先传 fake。
必须替换模块级对象或环境变量时，再用 monkeypatch。
```

这样测试更直观。

### 14. 为什么测试工具放在 `tests/` 而不是 `app/`

`tests/rag_fakes.py` 放在测试目录。

原因是它只服务测试。

如果放进 `app/rag`，生产代码就可能误用它。

测试 fake 不应该成为业务 API。

可以这样理解：

```text
app/ 是生产代码。
tests/ 是验证生产代码的工具和用例。
```

测试工具可以依赖生产模型。

生产代码不应该依赖测试工具。

### 15. 后续 `/rag-chat` API 测试会怎么用

未来 `/rag-chat` 大概会做：

```text
POST /rag-chat
-> retrieve_top_k()
-> generate_answer_with_citations()
-> 返回 RagAnswer
```

测试时可以这样安排：

正常回答：

```text
FakeEmbeddingModel 返回 query vector
FakeVectorStoreReader 返回 chunks
FakeChatCompletions 返回模型回答
断言 response.status == answered
断言 citations 不为空
```

无资料：

```text
FakeVectorStoreReader 返回 []
断言 response.status == no_context
断言 FakeChatCompletions.calls == []
```

向量库失败：

```text
FakeVectorStoreReader(error=QdrantVectorStoreError(...))
断言 API 返回 RAG_VECTOR_STORE_FAILED
```

这就是为什么第 22 节先准备 fake。

它会直接降低后续 API 测试难度。

## 三、本节代码改动说明

### 1. 新增 `tests/rag_fakes.py`

这个文件是本节核心产出。

它不是生产代码。

它服务于测试。

新增内容：

- `make_retrieved_chunk()`
- `FakeEmbeddingModel`
- `FakeVectorStoreReader`
- `FakeVectorStoreWriter`

### 2. 新增 `tests/test_rag_fakes.py`

这个文件测试 fake 自身行为。

覆盖：

- `make_retrieved_chunk()` 可以覆盖字段。
- `FakeEmbeddingModel` 能记录 texts。
- `FakeEmbeddingModel` 能返回配置好的 vectors。
- `FakeEmbeddingModel` 能抛出配置好的 error。
- `FakeVectorStoreReader` 能记录 query 参数。
- `FakeVectorStoreReader` 能抛出配置好的 error。
- `FakeVectorStoreWriter` 能记录 ensure/upsert 参数。
- `FakeVectorStoreWriter` 能抛出配置好的 error。

### 3. 修改 `test_rag_retriever.py`

之前文件里有本地 `FakeVectorStoreReader`。

本节改为复用：

```text
tests.rag_fakes.FakeEmbeddingModel
tests.rag_fakes.FakeVectorStoreReader
```

这样 retriever 测试更聚焦：

```text
retrieve_top_k 自己做了什么。
```

而不是每个测试文件都维护一份 fake。

### 4. 修改 `test_rag_ingestion.py`

之前文件里有本地 `FakeVectorStore`。

本节改为复用：

```text
FakeEmbeddingModel
FakeVectorStoreWriter
```

这样入库测试能稳定检查：

- embedding 是否被调用。
- ensure collection 参数。
- upsert 参数。
- 写入 chunks 数量。

## 四、常见误区

### 误区 1：测试必须连真实服务才有意义

不对。

大多数单元测试应该隔离真实服务。

真实服务留给少量集成测试和 smoke test。

### 误区 2：fake 越像真实服务越好

不一定。

fake 应该足够支持当前测试目标。

如果 fake 复杂到几乎重写一个 Qdrant，那就跑偏了。

### 误区 3：只测返回值，不测调用参数

RAG 很多 bug 是参数传错。

所以 fake 要记录调用参数。

### 误区 4：所有测试都应该 mock

不对。

能用简单 fake 就不要过度 mock。

fake 通常更容易读，也更适合教学和长期维护。

### 误区 5：有 fake 测试就不需要 smoke test

也不对。

fake 测试验证代码逻辑。

smoke test 验证真实环境能否跑通。

两者互补。

## 五、本节练习

### 练习 1：解释为什么 RAG 单元测试不用真实 Qdrant

题目：

为什么 `retrieve_top_k()` 的单元测试不应该默认连接真实 Qdrant？

参考答案：

因为单元测试要稳定、快速、低成本。真实 Qdrant 需要 Docker、端口、collection、数据和网络环境，容易因为环境问题失败。`retrieve_top_k()` 单元测试重点是验证 query embedding、filter、top_k、score_threshold 是否正确传给 vector store，用 fake vector store 更合适。

### 练习 2：区分 fake 和 smoke test

题目：

fake 测试和 smoke test 分别验证什么？

参考答案：

fake 测试验证代码逻辑和参数传递，不依赖真实外部服务。smoke test 验证真实环境和真实外部服务能否跑通，比如真实 Qdrant 是否能写入和检索。

### 练习 3：设计 fake embedding

题目：

一个合格的 fake embedding 至少应该具备哪些能力？

参考答案：

至少要有 `dimension`，能根据输入文本数量返回相同数量的向量，能记录收到的 texts，能配置返回坏向量或抛出异常，用于测试错误映射。

### 练习 4：解释为什么 fake 要记录参数

题目：

为什么 `FakeVectorStoreReader` 不只返回 chunks，还要记录 `top_k`、`payload_filter`、`score_threshold`？

参考答案：

因为 RAG 的很多 bug 是参数没有正确传递。记录参数后，测试可以断言 `retrieve_top_k()` 是否把 filter、top_k、score_threshold 正确传给 vector store。

### 练习 5：判断测试类型

题目：

下面测试分别属于单元测试、适配层测试还是 smoke test？

```text
A. 用 FakeVectorStoreReader 测 retrieve_top_k
B. 用 httpx.MockTransport 测 Qdrant 请求体
C. 运行 scripts/rag_ingest_smoke.py 写入本地 Qdrant
```

参考答案：

A 是单元测试。B 是适配层测试。C 是 smoke test。

### 练习 6：判断 fake 能不能抓住问题

题目：

下面问题中，哪些 fake 测试能抓住？哪些抓不住？

```text
A. score_threshold 没有传给 vector store
B. 真实 embedding 模型语义效果不好
C. chunks=[] 时仍然调用模型
D. 真实 Qdrant collection 索引配置不合理
E. payload_filter 没传给 vector store
```

参考答案：

A、C、E fake 测试能抓住，因为它们属于参数传递和调用边界问题。B、D fake 测试抓不住，因为它们属于真实模型效果和真实向量库配置问题，需要 eval、集成测试或 smoke test。

### 练习 7：选择测试工具

题目：

如果你要验证 `QdrantVectorStore.query_similar()` 发给 Qdrant 的 HTTP JSON 请求体是否包含 `score_threshold`，应该用 `FakeVectorStoreReader` 还是 `httpx.MockTransport`？

参考答案：

应该用 `httpx.MockTransport`。因为这是 Qdrant HTTP 适配层测试，需要检查真实适配器构造的 HTTP path、method 和 JSON body。`FakeVectorStoreReader` 更适合测试上层业务代码有没有把参数传给 vector store 接口。

### 练习 8：设计 `/rag-chat` API 测试

题目：

未来测试 `/rag-chat` 的 no_context 场景时，应该怎么配置 fake？

参考答案：

可以让 `FakeVectorStoreReader` 返回空列表，让 fake LLM client 可用但断言它没有被调用。请求结束后断言响应里 `status=no_context`、`citations=[]`，并且 `FakeChatCompletions.calls == []`。

### 练习 9：区分 fake 测试和 eval

题目：

fake 测试能证明 `top_k=5` 是业务上最好的参数吗？为什么？

参考答案：

不能。fake 测试只能证明 `top_k=5` 被正确传递。它不能证明这个参数在真实数据上的召回率和回答质量。参数效果需要 RAG eval、真实数据和人工评测来验证。

## 六、自测问题

### 自测 1

问题：

为什么 RAG 自动化测试不能大量依赖真实模型？

答案：

因为真实模型依赖 API key、网络和费用，输出也可能不稳定，不适合做快速稳定的单元测试。

### 自测 2

问题：

`FakeEmbeddingModel.last_texts` 有什么用？

答案：

用于断言业务代码传给 embedding 的文本是否正确，比如 query 是否已去掉前后空白。

### 自测 3

问题：

`FakeVectorStoreReader.last_call` 有什么用？

答案：

用于断言 vector store 查询参数是否正确，例如 `top_k`、`payload_filter`、`score_threshold`、`with_payload` 和 `with_vector`。

### 自测 4

问题：

为什么 fake 自己也要测试？

答案：

因为 fake 会被多个测试复用，如果 fake 自己行为错误，会导致很多测试误判。少量测试能保护共享测试工具。

### 自测 5

问题：

fake 测试能证明真实 Qdrant 一定可用吗？

答案：

不能。fake 测试只能证明代码逻辑和参数传递。真实 Qdrant 可用性需要 smoke test 或集成测试验证。

### 自测 6

问题：

第 22 节为什么不重写 fake LLM？

答案：

因为项目已有 `tests/fakes.py`，里面的 `FakeChatCompletions` 和 `FakeOpenAICompatibleClient` 已经能测试模型调用边界。本节补的是 RAG 特有 fake。

### 自测 7

问题：

`FakeVectorStoreWriter` 主要服务哪个流程？

答案：

主要服务 RAG 入库流程，用于测试 ensure collection 和 upsert embedded chunks 的编排和参数。

### 自测 8

问题：

后续 `/rag-chat` API 测试可以复用哪些 fake？

答案：

可以复用 `FakeEmbeddingModel`、`FakeVectorStoreReader`、`FakeChatCompletions` 和 `FakeOpenAICompatibleClient`。

### 自测 9

问题：

业务编排测试、HTTP 适配层测试、真实 smoke test 分别适合用什么工具？

答案：

业务编排测试适合用 fake vector store。HTTP 适配层测试适合用 `httpx.MockTransport`。真实 smoke test 适合连接本地或测试环境里的真实 Qdrant。

### 自测 10

问题：

fake 测试和 RAG eval 的区别是什么？

答案：

fake 测试验证代码逻辑、参数传递、状态和错误边界。RAG eval 验证真实检索和回答质量，例如相关性、忠实度、引用准确性。

### 自测 11

问题：

为什么本节优先传入 fake 对象，而不是使用 monkeypatch？

答案：

因为当前 RAG 函数通过参数接收 `embedding_model` 和 `vector_store`，可以直接注入 fake。能通过参数注入时，测试更直观，不需要 monkeypatch 替换全局对象。

### 自测 12

问题：

为什么 `tests/rag_fakes.py` 不应该放进 `app/rag`？

答案：

因为它是测试工具，不是生产代码。生产代码不应该依赖测试 fake，避免测试辅助对象变成业务 API。

## 七、你应该能口述出的版本

你可以这样向别人解释本节：

```text
第 22 节讲 RAG 测试。RAG 链路依赖 embedding、向量库和大模型，如果单元测试都连真实服务，测试会慢、不稳定、贵，也容易因为环境问题失败。

所以我们把测试分层：核心逻辑用 fake 做单元测试，Qdrant 请求适配可以用 httpx.MockTransport，真实 Qdrant 留给 smoke test。

本节新增 tests/rag_fakes.py，里面有 FakeEmbeddingModel、FakeVectorStoreReader、FakeVectorStoreWriter 和 make_retrieved_chunk。FakeEmbeddingModel 能记录输入 texts、返回固定维度向量、模拟错误；FakeVectorStoreReader 能记录 top_k、payload_filter、score_threshold 并返回 fake chunks；FakeVectorStoreWriter 能记录 ensure_collection 和 upsert 参数。

这样 retrieve、ingestion、no_context、error mapping、后续 /rag-chat API 都能在不启动 Qdrant、不调用模型的情况下稳定测试。

但 fake 测试不是万能的。它能抓参数传递、状态返回、错误映射、是否调用模型这些代码边界问题；它抓不住真实 embedding 语义质量、Qdrant 召回率、模型回答忠实度。那些要靠 MockTransport 适配层测试、真实 smoke test 和后续 RAG eval 来补。
```

## 八、本节产出

新增：

- `projects/ai-service/tests/rag_fakes.py`
- `projects/ai-service/tests/test_rag_fakes.py`
- `notes/rag-stage4-22-rag-testing-fakes.md`

修改：

- `projects/ai-service/tests/test_rag_retriever.py`
- `projects/ai-service/tests/test_rag_ingestion.py`
- `README.md`
- `docs/learning-progress.md`
- `docs/learning-resources.md`
- `projects/ai-service/README.md`

## 九、参考资料

- [阶段 4 第 15 节：基础 top_k 检索](rag-stage4-15-basic-top-k-retrieval.md)
- [阶段 4 第 20 节：无检索结果时怎么处理](rag-stage4-20-no-context-handling.md)
- [阶段 4 第 21 节：RAG 错误处理](rag-stage4-21-error-handling.md)
- [阶段 2 第 17 节：测试模型调用：mock/fake LLM client](llm-api-stage2-17-testing-model-calls.md)
- [Python pytest 基础](python-pytest.md)
