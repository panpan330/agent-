# 阶段 4 第 34 节：用同一批文档写入 Milvus 并做向量检索

## 本节定位

前面第 31 到 33 节，我们已经完成了三件事：

1. 知道 Milvus 是什么，以及它和 Qdrant 的概念差异。
2. 在 VMware Ubuntu 的 Docker 里启动了 Milvus Standalone。
3. 理解了 Milvus 的 collection、schema、field、entity、index。

这一节开始把 Milvus 从“概念”推进到“项目代码”。

本节做的事情很明确：

```text
同一批知识库文档
-> load
-> split
-> fake embedding
-> 写入 Milvus
-> 用 query embedding 检索 Milvus
-> 返回项目统一的 RetrievedChunk
```

也就是说，我们不重新发明一套 RAG 流程，而是复用前面已经完成的 RAG 主线，把原来的 Qdrant vector store 换成 Milvus vector store。

这一节非常关键，因为它让你真正理解一个工程问题：

```text
RAG 的主流程可以稳定不变，vector store 只是其中一个可替换的存储适配层。
```

## 本节最小但完整的学习目标

学完本节，你应该能讲清楚：

1. 为什么 Milvus 写入前必须先有 schema。
2. 为什么向量字段必须有固定维度。
3. 为什么向量字段需要 index。
4. 为什么 RAG chunk 写进 Milvus 时叫 entity。
5. 为什么同一个 chunk 既要保存向量，也要保存原文和 metadata。
6. `upsert` 和 `insert` 的区别是什么。
7. 为什么写入后立刻检索时，有时需要 `flush`。
8. Milvus 的 `search` 请求里，`data`、`anns_field`、`filter`、`limit`、`output_fields`、`search_params` 分别是什么意思。
9. 为什么项目内部仍然返回 `RetrievedChunk`，而不是让上层代码直接依赖 Milvus 的搜索结果格式。
10. 为什么单元测试用 fake Milvus client，而 smoke 脚本才连接真实 Milvus。

本节完成后，你要能这样口述：

```text
我把项目里的 RagChunk 先变成 EmbeddedChunk，再把 EmbeddedChunk 映射成 Milvus entity。
Milvus collection 不是随便塞 JSON 的，它需要固定 schema。
schema 里有一个 VARCHAR 主键 chunk_id，一个 FLOAT_VECTOR 向量字段 embedding，还有 content/source/title/permission_group 等 scalar fields。
写入时使用 upsert，因为同一个 chunk_id 再写一次应该覆盖或更新旧记录。
检索时把用户问题也转成同维度向量，用 MilvusClient.search 指定向量字段、top_k、过滤表达式和返回字段。
最后把 Milvus hit 转回项目统一的 RetrievedChunk，这样上层 RAG 代码不用关心底层用的是 Qdrant 还是 Milvus。
```

## 本节暂时不学什么

为了让这一节边界清楚，下面这些先不深入：

1. 不切换到真实 embedding 模型。
2. 不做 Milvus scalar index 优化。
3. 不讲 Milvus 分区 partition。
4. 不讲 Milvus 多副本、集群部署、资源组。
5. 不讲混合检索和 rerank 的 Milvus 生产级组合。
6. 不改 Java mock service。
7. 不做 LangChain Milvus VectorStore 封装。
8. 不做多租户权限系统，只复用已有 `permission_group` metadata。

这些后面会继续学。当前先把“最小可运行 Milvus 入库和检索链路”扎实跑通。

## 基础知识铺垫

### 1. RAG 入库到底在存什么

一个 RAG chunk 入库时，通常不是只存一句文本。

我们真正要存的是一条“可检索知识记录”：

```text
chunk_id
content
embedding vector
metadata
```

这四类信息各自负责不同事情。

`chunk_id` 负责唯一定位。

比如：

```text
refund_return_policy_chunk_0005
```

它告诉系统：“这就是退款退货文档里的第 5 个 chunk”。

`content` 负责回答问题。

比如：

```text
如果退货原因是用户个人原因，退货运费通常由用户承担。
```

模型最终回答用户时，要读的不是向量，而是这段原文。

`embedding vector` 负责相似度搜索。

比如：

```text
[0.12, 0.31, 0.88, ...]
```

向量数据库用它来判断“用户问题”和“哪段文档”更接近。

`metadata` 负责过滤、引用和治理。

比如：

```text
source=refund-return-policy.md
title=退款退货规则
section=运费处理
business_domain=refund
permission_group=customer_service
```

metadata 能解决这些问题：

1. 只查客服能看的文档。
2. 只查退款领域的文档。
3. 回答时告诉用户来源。
4. 文档更新时按 source 删除旧 chunk。
5. 后续做权限、安全、审计和评测。

所以一个 chunk 入库不是“把文本塞进数据库”这么简单，而是把文档变成一条结构化、可检索、可追踪的知识记录。

### 2. Qdrant point 和 Milvus entity 的对应关系

前面 Qdrant 里我们学过 point。

Qdrant point 大概长这样：

```json
{
  "id": "stable-point-id",
  "vector": [0.1, 0.2, 0.3, 0.4],
  "payload": {
    "chunk_id": "refund_return_policy_chunk_0005",
    "content": "退货运费处理规则...",
    "source": "refund-return-policy.md",
    "business_domain": "refund"
  }
}
```

Milvus 里更像数据库表的一行，叫 entity：

```python
{
    "chunk_id": "refund_return_policy_chunk_0005",
    "embedding": [0.1, 0.2, 0.3, 0.4],
    "content": "退货运费处理规则...",
    "source": "refund-return-policy.md",
    "business_domain": "refund",
}
```

两者的核心目的相同：

```text
保存向量 + 原文 + 元数据
```

区别在于：

| 对比点 | Qdrant | Milvus |
| --- | --- | --- |
| 一条记录叫什么 | point | entity |
| 向量放哪里 | vector | schema 里的 FLOAT_VECTOR field |
| 业务字段放哪里 | payload | scalar fields |
| 字段结构是否强约束 | 更灵活 | 更像数据库表，需要 schema |
| 查询过滤写法 | JSON filter | 标量过滤表达式字符串 |

这也是本节代码的核心：把项目里通用的 `EmbeddedChunk` 同时支持映射到 Qdrant point 和 Milvus entity。

### 3. 为什么 Milvus 需要 schema

Qdrant 里 payload 比较灵活，你可以把很多字段直接放进去。

Milvus 更像一张表，创建 collection 时要先定义字段：

```text
chunk_id            VARCHAR      主键
embedding           FLOAT_VECTOR 向量字段
content             VARCHAR      chunk 原文
source              VARCHAR      文档来源
title               VARCHAR      标题
permission_group    VARCHAR      权限分组
chunk_index         INT64        chunk 编号
```

这就是 schema。

schema 的作用不是增加麻烦，而是让 Milvus 提前知道：

1. 哪个字段是主键。
2. 哪个字段是向量。
3. 向量维度是多少。
4. 哪些字段是字符串。
5. 哪些字段是整数。
6. 哪些字段以后可以做过滤。

如果没有 schema，Milvus 不知道如何给向量建索引，也不知道每条记录是否满足结构要求。

可以把 schema 理解成：

```text
Milvus collection 的表结构说明书。
```

### 4. 为什么向量字段必须有固定维度

embedding 向量的长度叫维度。

比如本节继续使用学习版 fake embedding：

```text
dimension = 8
```

那么每个向量都必须长这样：

```python
[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
```

不能有的 chunk 是 8 维，有的是 1024 维，有的是 1536 维。

原因很简单：

```text
向量相似度计算要求两个向量维度一致。
```

你不能拿 8 个数字和 1024 个数字直接算 cosine similarity。

所以 Milvus collection 创建时要在 vector field 上写：

```python
dim=8
```

后续换真实 embedding 时，如果模型输出是 1024 维，就不能继续写入这个 8 维 collection。

正确做法是：

```text
换 embedding 模型或维度
-> 新建或重建对应维度的 collection
-> 重新入库
```

这点以后做真实 embedding 时非常重要。

### 5. 为什么向量字段需要 index

Milvus 是向量数据库，不只是普通数据库。

普通数据库索引通常服务于：

```text
WHERE source = 'refund-return-policy.md'
```

向量索引服务于：

```text
找出和 query_vector 最接近的 top_k 个向量
```

如果没有向量索引，向量数据库可能只能暴力扫描所有向量：

```text
query_vector
-> 和第 1 条向量算相似度
-> 和第 2 条向量算相似度
-> 和第 3 条向量算相似度
-> ...
```

数据少时没问题，数据多时会慢。

Milvus 通过 index 加速近似最近邻搜索，也就是 ANN：

```text
Approximate Nearest Neighbor
```

本节为了简单使用：

```python
index_type="AUTOINDEX"
metric_type="COSINE"
```

`AUTOINDEX` 表示让 Milvus 选择合适的索引策略，适合学习和快速验证。

`COSINE` 表示用余弦相似度衡量向量接近程度。

### 6. insert 和 upsert 的区别

`insert` 是插入。

可以理解成：

```text
这条记录以前不存在，现在新增进去。
```

`upsert` 是 update + insert。

可以理解成：

```text
如果主键不存在，就新增。
如果主键已经存在，就更新。
```

RAG 文档入库通常更适合 `upsert`。

原因是同一个 chunk 可能会重复入库：

1. 你重跑了 smoke 脚本。
2. 你修改了文档后重新入库。
3. 你换了 chunk 参数后重新生成。
4. 你调试时多次写入同一个 chunk_id。

如果用 `insert`，重复主键可能报错。

如果用 `upsert`，相同 `chunk_id` 会更新，学习阶段更方便。

但注意：

```text
upsert 不是万能的文档更新方案。
```

生产里如果 chunk 切分策略变了，旧 chunk_id 可能已经不对应新文档结构，这时仍然需要按 `source` 删除旧 chunks 再重新入库。

我们前面第 23 节已经学过这个问题。

### 7. 为什么写入后可能需要 flush

本节 smoke 一开始出现过一个现象：

```text
写入显示 vectors: 16
但紧接着查询时 retrieved chunks 为空
```

后来排查发现：

```text
数据已经写进 Milvus，稍后查询可以查到，过滤也正常。
```

这说明问题不是字段错，也不是 filter 错，而是写入后立即查询时可见性不够稳定。

Milvus 有写入缓冲、segment、load、索引等机制。学习阶段我们不展开这些底层细节，只先记住：

```text
写入成功，不等于下一行代码马上一定能稳定搜到。
```

为了让本节 smoke 稳定，我们在 `wait=True` 时调用：

```python
client.flush(collection_name=...)
```

这样做的学习意义是：

```text
当你写入后马上要验证检索结果时，要考虑写入可见性。
```

在生产系统里，是否每次写入都 flush 要结合性能和一致性要求设计。频繁 flush 可能影响吞吐，本节是学习版和 smoke 版，优先保证观察结果清楚。

### 8. Milvus 的 search 在做什么

Milvus search 的核心输入包括：

```python
client.search(
    collection_name="learning_rag_chunks_milvus",
    data=[[...query vector...]],
    anns_field="embedding",
    filter='permission_group == "customer_service"',
    limit=3,
    output_fields=["chunk_id", "content", "source", "section"],
    search_params={"metric_type": "COSINE", "params": {}},
)
```

逐个拆开：

`collection_name`：查哪个 collection。

`data`：查询向量。注意它是二维列表，因为一次可以查多个 query vector。

`anns_field`：在哪个向量字段上做 ANN search。本节是 `embedding`。

`filter`：标量字段过滤表达式。比如只查客服可见的退款文档。

`limit`：返回前几个结果，也就是 top_k。

`output_fields`：除了主键和距离分数，还要返回哪些字段。RAG 必须返回 `content`，否则模型没有原文可读。

`search_params`：搜索参数。本节主要指定 `metric_type`。

返回结果通常长这样：

```python
[
    [
        {
            "id": "refund_return_policy_chunk_0005",
            "distance": 0.8861,
            "entity": {
                "chunk_id": "refund_return_policy_chunk_0005",
                "content": "如果退货原因是用户个人原因...",
                "source": "refund-return-policy.md",
                "section": "运费处理",
            },
        }
    ]
]
```

外层列表表示多个 query vector 的结果。

内层列表表示某一个 query vector 的 top_k hits。

每个 hit 里有：

1. `id`：命中的主键。
2. `distance`：Milvus 返回的相似度或距离值。
3. `entity`：你要求返回的字段。

我们的项目不会把这个原始结构直接交给上层，而是转换成统一的 `RetrievedChunk`。

## 本节主题系统讲解

### 1. 本节最终链路

本节完成后的链路如下：

```text
data/knowledge_base
-> load_documents_from_directory
-> split_documents_into_chunks
-> embed_chunks
-> MilvusVectorStore.ensure_collection
-> MilvusVectorStore.upsert_embedded_chunks
-> retrieve_top_k
-> MilvusVectorStore.query_similar
-> RetrievedChunk[]
```

和 Qdrant 链路对比：

```text
Qdrant:
EmbeddedChunk -> build_qdrant_point -> Qdrant REST upsert -> Qdrant Query API

Milvus:
EmbeddedChunk -> build_milvus_entity -> PyMilvus upsert -> PyMilvus search
```

你要抓住一个重点：

```text
RAG 上层编排没有变，变的是 vector store adapter。
```

`ingestion.py` 仍然只知道：

```python
vector_store.ensure_collection(...)
vector_store.upsert_embedded_chunks(...)
```

`retriever.py` 仍然只知道：

```python
vector_store.query_similar(...)
```

它们不需要知道底层是 Qdrant REST，还是 PyMilvus SDK。

这就是“接口抽象”的价值。

### 2. 为什么新增 `MilvusVectorStore`

新增文件：

```text
projects/ai-service/app/rag/milvus_store.py
```

它的定位是：

```text
Milvus 适配层。
```

它不负责：

1. 读取文档。
2. 切分 chunk。
3. 调模型生成 embedding。
4. 组织最终回答。
5. 调 LLM。

它只负责：

1. 把 `EmbeddedChunk` 转成 Milvus entity。
2. 创建或校验 Milvus collection。
3. 创建向量索引。
4. upsert entities。
5. 把查询向量交给 Milvus search。
6. 把 Milvus hit 转成 `RetrievedChunk`。

这个边界非常重要。

如果一个类同时负责读文档、切 chunk、调 embedding、写 Milvus、调 LLM，后面会非常难维护，也很难测试。

### 3. 本节 Milvus schema 设计

本节 schema 不是随便定的，而是从前面 RAG metadata 设计自然延伸出来的。

核心字段：

| 字段 | Milvus 类型 | 作用 |
| --- | --- | --- |
| `chunk_id` | VARCHAR | 主键，唯一定位 chunk |
| `embedding` | FLOAT_VECTOR | 用于向量检索 |
| `content` | VARCHAR | 检索命中后交给模型阅读 |
| `source` | VARCHAR | 文档来源 |
| `title` | VARCHAR | 文档标题 |
| `file_name` | VARCHAR | 文件名 |
| `file_extension` | VARCHAR | 文件类型 |
| `doc_type` | VARCHAR | 文档类型 |
| `business_domain` | VARCHAR | 业务领域 |
| `permission_group` | VARCHAR | 权限分组 |
| `chunk_index` | INT64 | 第几个 chunk |
| `chunk_count` | INT64 | 本文档总 chunk 数 |
| `chunk_size_chars` | INT64 | chunk 字符数 |
| `section` | VARCHAR | 所属章节 |

为什么 `content` 也放进 Milvus？

因为检索返回后，模型需要读原文。

如果 Milvus 只存向量，命中后还要再去另一个数据库查原文，链路会多一步。

生产系统里确实可能把原文放对象存储或关系库，Milvus 只放索引字段和引用 ID。但学习阶段直接把 content 存进去，链路更直观。

为什么 `chunk_id` 选择 VARCHAR 主键？

因为我们前面的 chunk_id 已经是稳定字符串：

```text
refund_return_policy_chunk_0005
```

它比自增数字更容易调试，也能直接看出来源。

### 4. 为什么不直接复用 Qdrant payload

Qdrant payload 是一个灵活 JSON 对象。

Milvus schema 是固定字段。

所以不能简单写：

```python
entity["payload"] = payload
```

而要把 payload 展平：

```python
entity["source"] = payload["source"]
entity["title"] = payload["title"]
entity["permission_group"] = payload["permission_group"]
```

这一步让 metadata 从“一个 JSON payload”变成了 Milvus 的 scalar fields。

好处是：

```text
以后可以对这些 scalar fields 做过滤和索引优化。
```

代价是：

```text
schema 变严格了，字段缺失或类型不对会更早报错。
```

严格不是坏事。对企业 RAG 来说，权限字段、来源字段、文档类型字段不应该随便缺失。

### 5. 为什么要把 Qdrant filter 转成 Milvus expression

项目上层已经有一个统一的过滤构造函数：

```python
build_payload_filter(
    permission_group="customer_service",
    business_domain="refund",
)
```

它返回的是 Qdrant 风格：

```python
{
    "must": [
        {"key": "permission_group", "match": {"value": "customer_service"}},
        {"key": "business_domain", "match": {"value": "refund"}},
    ]
}
```

Qdrant 可以直接吃这个 JSON filter。

Milvus 不吃这个形状，它需要表达式字符串：

```text
permission_group == "customer_service" and business_domain == "refund"
```

所以本节新增：

```python
build_milvus_filter_expression(...)
```

它的作用就是翻译：

```text
项目统一 filter
-> Milvus scalar filter expression
```

目前只支持最简单、最安全、最容易理解的 must exact match。

也就是：

```text
字段 == 值 and 字段 == 值
```

不支持复杂的 should、must_not、range、like、数组过滤。

为什么先限制这么窄？

因为学习阶段先把主线讲透，比一次性堆很多高级条件更重要。

第 35 节再专门讲 Milvus metadata/scalar filter 和索引基础。

### 6. 为什么返回 `RetrievedChunk`

Milvus search 返回的是 Milvus 自己的 hit 结构。

但我们项目里的 RAG 生成、引用来源、安全检查、rerank、调优工具，都已经围绕 `RetrievedChunk` 工作。

所以适配器应该负责转换：

```text
Milvus hit
-> RetrievedChunk
```

这样上层代码只认一种结构：

```python
RetrievedChunk(
    point_id="refund_return_policy_chunk_0005",
    chunk_id="refund_return_policy_chunk_0005",
    content="...",
    metadata={...},
    score=0.8861,
)
```

这就是适配器模式最朴素的价值：

```text
把外部系统的差异关在边界内。
```

上层不需要到处写：

```python
if vector_store == "qdrant":
    ...
elif vector_store == "milvus":
    ...
```

这会让系统越来越乱。

### 7. 为什么测试用 fake client

本节新增的单元测试不连接真实 Milvus。

原因有三个：

1. 单元测试应该快。
2. 单元测试应该稳定。
3. 单元测试不应该依赖你是否打开 VMware。

所以测试里写了 fake Milvus client：

```text
FakeMilvusClient
FakeSchema
FakeIndexParams
FakeDataType
```

它们不是真的 Milvus，只是记录代码调用了什么参数。

比如验证：

```text
是否创建了 chunk_id 主键字段
是否创建了 embedding 向量字段
是否给 embedding 建了 AUTOINDEX
是否调用 upsert
是否调用 flush
是否调用 search
filter 是否翻译成 Milvus 表达式
```

真实 Milvus 连通性和真实写入检索，则由 smoke 脚本验证。

这个分层很重要：

```text
单元测试检查代码逻辑。
smoke 测试检查外部服务链路。
```

## 本节代码改动总览

### 1. 新增依赖

在 `projects/ai-service/pyproject.toml` 中新增：

```text
pymilvus
```

安装命令是：

```powershell
uv add pymilvus
```

`pymilvus` 是 Milvus 官方 Python SDK。

本节不用 HTTP REST 手写请求，而是用官方 SDK 调用：

```python
MilvusClient(...)
client.create_collection(...)
client.upsert(...)
client.search(...)
```

### 2. 新增配置

文件：

```text
projects/ai-service/app/core/config.py
projects/ai-service/.env.example
```

新增配置：

```text
MILVUS_URI="http://192.168.88.10:19530"
MILVUS_COLLECTION_NAME="learning_rag_chunks_milvus"
MILVUS_TIMEOUT_SECONDS=5
MILVUS_VECTOR_SIZE=8
MILVUS_TOKEN=""
```

这些配置分别表示：

| 配置 | 作用 |
| --- | --- |
| `MILVUS_URI` | Milvus 服务地址 |
| `MILVUS_COLLECTION_NAME` | 要写入和检索的 collection 名 |
| `MILVUS_TIMEOUT_SECONDS` | SDK 调用超时时间 |
| `MILVUS_VECTOR_SIZE` | 本节 fake embedding 的向量维度 |
| `MILVUS_TOKEN` | 有鉴权时使用，当前本地学习可以为空 |

注意：

```text
MILVUS_VECTOR_SIZE=8 是为了配合 fake embedding smoke。
```

等后面换真实 embedding，例如 1024 维，就不能继续写 8 维 collection。

### 3. 新增 Milvus 适配器

文件：

```text
projects/ai-service/app/rag/milvus_store.py
```

核心类：

```python
class MilvusVectorStore:
    ...
```

它提供三个主方法：

```python
ensure_collection(...)
upsert_embedded_chunks(...)
query_similar(...)
```

这三个方法刚好对上已有 RAG 抽象。

### 4. 新增 smoke 脚本

文件：

```text
projects/ai-service/scripts/rag_milvus_smoke.py
```

它会：

1. 读取 `data/knowledge_base`。
2. 用 fake embedding 生成 8 维向量。
3. 写入 Milvus collection。
4. 查询“退货运费谁承担？”。
5. 打印检索结果。

### 5. 新增测试

文件：

```text
projects/ai-service/tests/test_rag_milvus_store.py
```

测试重点：

1. metric 名称映射。
2. entity 构造。
3. filter 表达式转换。
4. collection schema/index 创建。
5. existing collection 维度校验。
6. upsert 调用和 flush。
7. search 参数和结果解析。
8. L2 与 COSINE 的 score_threshold 方向差异。
9. 无效输入提前报错。
10. SDK 异常映射。

## 关键代码讲解

### 1. metric 名称映射

项目里原来 Qdrant 用的是：

```text
Cosine
Dot
Euclid
```

Milvus 用的是：

```text
COSINE
IP
L2
```

所以本节新增：

```python
MILVUS_DISTANCE_ALIASES = {
    "cosine": "COSINE",
    "dot": "IP",
    "ip": "IP",
    "euclid": "L2",
    "l2": "L2",
}
```

学习重点：

```text
同一个概念，不同数据库命名可能不同。
```

代码里不要让上层到处记住这些差异，而是在适配器里统一翻译。

### 2. `build_milvus_entity`

这个函数负责：

```text
EmbeddedChunk -> Milvus entity
```

输入是项目内部结构：

```python
EmbeddedChunk(
    chunk_id="refund_return_policy_chunk_0005",
    content="...",
    metadata={...},
    vector=[...],
)
```

输出是 Milvus 可写入结构：

```python
{
    "chunk_id": "refund_return_policy_chunk_0005",
    "embedding": [...],
    "content": "...",
    "source": "refund-return-policy.md",
    "business_domain": "refund",
    "permission_group": "customer_service",
    ...
}
```

这里复用了：

```python
build_qdrant_payload(...)
```

这不是因为它只能服务 Qdrant，而是因为这个函数已经承载了项目对 RAG payload 的校验和白名单逻辑。

更准确地说，它现在承担的是：

```text
构造项目标准 RAG payload。
```

Qdrant 和 Milvus 都可以从这个标准 payload 继续映射。

### 3. `ensure_collection`

这个方法负责创建或校验 collection：

```python
store.ensure_collection(vector_size=8, distance="Cosine")
```

它会做：

1. 校验 `vector_size`。
2. 把 `Cosine` 转成 Milvus 的 `COSINE`。
3. 判断 collection 是否已存在。
4. 如果不存在，创建 schema 和 index。
5. 如果存在，检查向量维度是否匹配。
6. load collection。

为什么 existing collection 要检查维度？

因为如果已经存在一个 1024 维 collection，你却用 8 维 fake embedding 写进去，后面一定会报错。

越早报错越好。

报错越靠近问题源头，你越容易定位。

### 4. `_create_collection`

这个方法创建 schema。

关键字段：

```python
schema.add_field(
    field_name="chunk_id",
    datatype=DataType.VARCHAR,
    is_primary=True,
    max_length=256,
)
```

这表示：

```text
chunk_id 是字符串主键。
```

向量字段：

```python
schema.add_field(
    field_name="embedding",
    datatype=DataType.FLOAT_VECTOR,
    dim=vector_size,
)
```

这表示：

```text
embedding 是固定维度的浮点向量。
```

向量索引：

```python
index_params.add_index(
    field_name="embedding",
    index_type="AUTOINDEX",
    metric_type="COSINE",
)
```

这表示：

```text
对 embedding 字段创建向量索引，并使用 cosine 相似度。
```

### 5. `upsert_embedded_chunks`

这个方法负责批量写入：

```python
count = store.upsert_embedded_chunks(embedded_chunks)
```

它先做：

```text
所有 vector 维度一致校验
```

然后做：

```text
EmbeddedChunk 列表 -> Milvus entity 列表
```

最后调用：

```python
client.upsert(
    collection_name=self.collection_name,
    data=entities,
    timeout=self.timeout_seconds,
)
```

如果 `wait=True`，再调用：

```python
client.flush(...)
```

这一点在本节很重要，因为 smoke 是写完马上查。

### 6. `query_similar`

这个方法负责向量检索：

```python
chunks = store.query_similar(
    query_vector,
    top_k=3,
    payload_filter=payload_filter,
)
```

它会：

1. 校验 query vector。
2. 校验 top_k。
3. 把项目 filter 转成 Milvus expression。
4. 调 Milvus search。
5. 把 hit 转成 `RetrievedChunk`。
6. 根据 score_threshold 做学习版过滤。

为什么 score_threshold 在客户端过滤？

因为本节先保持逻辑容易理解。Milvus range search 可以更细地表达阈值，但涉及 `radius` 和 `range_filter`，不同距离函数方向也不同。

本节先用普通 search 取回 top_k，再在客户端按当前 metric 判断：

```text
COSINE/IP：分数越高越相似，所以 score >= threshold
L2：距离越低越相似，所以 score <= threshold
```

### 7. `build_milvus_filter_expression`

项目 filter：

```python
{
    "must": [
        {"key": "permission_group", "match": {"value": "customer_service"}},
        {"key": "business_domain", "match": {"value": "refund"}},
    ]
}
```

转换成 Milvus：

```text
permission_group == "customer_service" and business_domain == "refund"
```

这里做了字段白名单：

```python
MILVUS_FILTERABLE_FIELDS = {
    "permission_group",
    "business_domain",
    "doc_type",
    "source",
    "file_name",
    "file_extension",
    "section",
}
```

为什么要白名单？

因为 filter 字段最终会拼成表达式字符串。

如果允许任意字段，会有两个问题：

1. 用户传错字段，Milvus 报错不清楚。
2. 未来如果 filter 来自外部输入，表达式拼接必须非常谨慎。

本节先只支持明确字段。

## 实机 smoke 验证

你的 Milvus 运行在 VMware Ubuntu Docker 里。

本节验证前，Windows 到虚拟机的端口检查结果是：

```text
Test-NetConnection 192.168.88.10 -Port 19530
TcpTestSucceeded : True
```

运行命令：

```powershell
$env:MILVUS_URI='http://192.168.88.10:19530'
$env:MILVUS_COLLECTION_NAME='learning_rag_chunks_milvus'
$env:MILVUS_VECTOR_SIZE='8'
uv run python scripts/rag_milvus_smoke.py
```

实际输出：

```text
Milvus RAG smoke test finished
documents: 4
chunks: 16
vectors: 16
dimension: 8
collection: learning_rag_chunks_milvus
query: 退货运费谁承担？
retrieved chunks:
1. score=0.9049 source=refund-return-policy.md section=七天无理由退货 chunk_id=refund_return_policy_chunk_0002
2. score=0.8998 source=refund-return-policy.md section=退款到账时间 chunk_id=refund_return_policy_chunk_0004
3. score=0.8861 source=refund-return-policy.md section=运费处理 chunk_id=refund_return_policy_chunk_0005
```

这个结果说明：

1. Python 能连接 VMware 里的 Milvus。
2. collection 能创建或复用。
3. 4 个知识文档能切成 16 个 chunk。
4. 16 个 chunk 能生成 16 条 fake embedding。
5. 16 条 entity 能写入 Milvus。
6. 用户问题能转成 query vector。
7. Milvus 能按 `business_domain=refund` 和 `permission_group=customer_service` 做过滤检索。
8. 检索结果能转回项目统一的 debug 输出。

但你也要注意：

```text
当前排序不代表真实语义质量。
```

原因是我们使用的是 deterministic fake embedding，不是真实 embedding 模型。

fake embedding 只保证：

```text
同一段文本每次生成同一个向量。
```

它不保证：

```text
“退货运费谁承担？”一定最接近“运费处理”。
```

所以本节 smoke 验证的是：

```text
Milvus 写入和检索链路正确。
```

不是验证：

```text
embedding 语义质量很好。
```

真实语义质量要等后面切换真实 embedding 模型后再评估。

## 和 Qdrant 链路的对比复盘

### 1. 入库对比

Qdrant 入库：

```text
EmbeddedChunk
-> build_qdrant_point
-> HTTP PUT /collections/{collection}/points
```

Milvus 入库：

```text
EmbeddedChunk
-> build_milvus_entity
-> MilvusClient.upsert
```

差异：

| 对比点 | Qdrant | Milvus |
| --- | --- | --- |
| SDK/协议 | 当前项目用 HTTP REST | 当前项目用 PyMilvus |
| 写入单位 | point | entity |
| 主键 | point id | primary field |
| metadata | payload | scalar fields |
| collection 创建 | vectors size + distance | schema + index params |
| 写入可见性 | Qdrant wait 参数 | Milvus 本节用 flush 稳定 smoke |

### 2. 检索对比

Qdrant 检索：

```text
POST /collections/{collection}/points/query
body: query + limit + filter + score_threshold
```

Milvus 检索：

```python
client.search(
    data=[query_vector],
    anns_field="embedding",
    filter='...',
    limit=top_k,
    output_fields=[...],
)
```

差异：

| 对比点 | Qdrant | Milvus |
| --- | --- | --- |
| 过滤格式 | JSON filter | expression string |
| 返回结构 | points | list of hit lists |
| 分数字段 | score | distance |
| 返回原文 | payload.content | entity.content |

### 3. 共同点

共同点更重要：

```text
query -> query vector -> vector search -> top_k chunks -> RetrievedChunk
```

你要理解：

```text
RAG 的核心思想不依赖某一个向量数据库。
```

Qdrant 和 Milvus 是不同实现，但它们都在 RAG 里承担 vector store 的角色。

## 常见错误和排查

### 1. ModuleNotFoundError: No module named 'app'

之前你运行脚本遇到过：

```text
ModuleNotFoundError: No module named 'app'
```

原因是 Python 找不到项目根目录。

本节 smoke 脚本保留了这段：

```python
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
```

它的作用是：

```text
把 projects/ai-service 放进 Python import 搜索路径。
```

这样脚本可以直接：

```python
from app.core.config import get_settings
```

### 2. Windows 连不上 Milvus

如果 smoke 连接失败，先检查：

```powershell
Test-NetConnection 192.168.88.10 -Port 19530
```

成功时应该看到：

```text
TcpTestSucceeded : True
```

如果失败，按顺序排查：

1. VMware Ubuntu 是否开机。
2. Docker 是否启动。
3. Milvus container 是否 healthy。
4. Ubuntu IP 是否还是 `192.168.88.10`。
5. Windows 是否能访问 `http://192.168.88.10:9091/webui/`。

### 3. 写入时报维度不匹配

如果你看到类似 vector dimension mismatch，先问：

```text
当前 collection 是几维？
当前 embedding 模型输出几维？
```

本节 fake embedding 是 8 维：

```text
MILVUS_VECTOR_SIZE=8
```

如果后面真实 embedding 是 1024 维，就要用新的 collection。

### 4. 检索为空

检索为空不一定是数据库坏了。

可能原因：

1. collection 里没有数据。
2. 写入后马上查，数据还没稳定可见。
3. filter 太严格。
4. filter 字段值和实际 metadata 不一致。
5. query vector 维度不匹配。
6. collection 没有 load。
7. fake embedding 排序不符合语义直觉。

本节已经通过 `flush-on-wait` 处理了 smoke 里“写完马上查”的稳定性问题。

### 5. 中文显示乱码

如果 PowerShell 输出中文变成：

```text
è´¦å·
```

不要第一时间认为文件坏了。

优先怀疑：

```text
PowerShell 输出编码显示 UTF-8 中文时出了问题。
```

可以用：

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Get-Content -Encoding UTF8 文件路径
```

本节排查文档时就遵守这个原则，避免误判后大范围改文件。

## 本节新增文件

```text
projects/ai-service/app/rag/milvus_store.py
projects/ai-service/scripts/rag_milvus_smoke.py
projects/ai-service/tests/test_rag_milvus_store.py
notes/rag-stage4-34-milvus-ingestion-search.md
```

## 本节修改文件

```text
projects/ai-service/app/core/config.py
projects/ai-service/.env.example
projects/ai-service/tests/test_config.py
projects/ai-service/app/rag/README.md
projects/ai-service/README.md
README.md
docs/learning-progress.md
docs/learning-resources.md
projects/ai-service/pyproject.toml
projects/ai-service/uv.lock
```

## 本节测试

已运行：

```powershell
uv run pytest tests/test_config.py tests/test_rag_milvus_store.py
```

结果：

```text
37 passed
```

已运行真实 smoke：

```powershell
uv run python scripts/rag_milvus_smoke.py
```

结果：

```text
documents: 4
chunks: 16
vectors: 16
dimension: 8
collection: learning_rag_chunks_milvus
retrieved chunks: 3
```

已运行 `ai-service` 全量测试：

```powershell
uv run pytest
```

结果：

```text
506 passed
```

这说明新增 Milvus 适配器没有破坏已有 Qdrant、RAG、Tool Calling、FastAPI 代码。

## 本节练习

### 练习 1：说出 Milvus entity 里为什么必须有 content

问题：

```text
既然向量数据库主要负责向量检索，为什么我们还要把 content 存进 Milvus entity？
```

参考答案：

```text
因为向量只能用于相似度搜索，不能直接给模型阅读。
检索命中后，RAG 需要把原文片段交给模型作为上下文。
如果 Milvus 里不存 content，命中后还要拿 chunk_id 去另一个数据库查原文。
学习阶段把 content 直接存到 Milvus，可以让入库和检索链路更直观。
```

### 练习 2：解释 `chunk_id` 为什么适合做主键

问题：

```text
为什么本节用 chunk_id 做 Milvus primary field，而不是让 Milvus 自动生成 ID？
```

参考答案：

```text
chunk_id 是项目自己生成的稳定 ID，能直接表示文档和 chunk 的关系。
用 chunk_id 做主键后，重复入库同一个 chunk 可以 upsert 更新。
调试时也能从 ID 看出它属于哪个文档、哪个 chunk。
自动 ID 虽然方便，但不利于文档更新、重复写入和问题排查。
```

### 练习 3：把 Qdrant filter 翻译成 Milvus expression

题目：

```python
{
    "must": [
        {"key": "permission_group", "match": {"value": "customer_service"}},
        {"key": "source", "match": {"value": "refund-return-policy.md"}},
    ]
}
```

请写出对应 Milvus 表达式。

参考答案：

```text
permission_group == "customer_service" and source == "refund-return-policy.md"
```

### 练习 4：判断下面 collection 是否能继续写入

已存在 collection 的 vector field 是 1024 维。

当前 fake embedding 输出 8 维。

问题：

```text
能不能直接写入？为什么？
```

参考答案：

```text
不能。
同一个 Milvus vector field 的维度是固定的。
1024 维 collection 只能写入 1024 维向量。
8 维 fake embedding 应该写入 8 维 collection，或者重建 collection。
```

### 练习 5：解释为什么 smoke 和单元测试分开

问题：

```text
为什么 test_rag_milvus_store.py 不直接连接 VMware 里的真实 Milvus？
```

参考答案：

```text
单元测试应该快速、稳定、可重复，不应该依赖虚拟机是否打开、Docker 是否启动、网络是否通。
所以单元测试用 fake Milvus client 检查代码调用形状和转换逻辑。
真实 Milvus 连通性、写入和检索通过 smoke 脚本手动验证。
这叫测试分层。
```

## 自测题

### 自测 1

Milvus 的 collection 和 schema 是什么关系？

参考答案：

```text
collection 是 Milvus 中保存一批 entity 的容器，类似一张表。
schema 是 collection 的结构定义，说明有哪些字段、字段类型是什么、哪个字段是主键、哪个字段是向量字段、向量维度是多少。
```

### 自测 2

Milvus 里的 entity 对应 Qdrant 里的什么概念？

参考答案：

```text
大致对应 Qdrant 的 point。
二者都是向量数据库里的一条记录，通常都包含向量、原文或引用字段、metadata 或 scalar fields。
```

### 自测 3

为什么 Milvus 的 filter 是字符串表达式，而本项目内部 filter 仍然保留 Qdrant 风格对象？

参考答案：

```text
因为项目上层已经使用统一的 payload_filter 结构来表达过滤条件。
Milvus 适配器负责把这个项目内部结构翻译成 Milvus expression。
这样上层 retriever 不需要关心底层向量数据库的过滤语法差异。
```

### 自测 4

`upsert` 比 `insert` 更适合本节 smoke 的原因是什么？

参考答案：

```text
smoke 脚本可能重复运行。
同一个 chunk_id 重复写入时，upsert 可以新增或更新，而 insert 更容易因为主键重复失败。
所以学习阶段用 upsert 更适合反复验证。
```

### 自测 5

为什么 fake embedding 能验证链路，但不能证明检索质量？

参考答案：

```text
fake embedding 只保证同样文本每次生成同样向量，方便测试和 smoke。
它不理解语义，所以不能证明“用户问题”和“文档片段”真的语义相关。
检索质量要等真实 embedding 模型接入后，通过样例问题和评测集判断。
```

### 自测 6

`output_fields` 如果不包含 `content` 会发生什么？

参考答案：

```text
Milvus 可能只返回主键和距离分数，上层 RAG 拿不到原文片段。
没有 content，模型就没有依据回答问题。
所以 RAG 检索通常必须返回 content 和必要 metadata。
```

### 自测 7

为什么本节在 `wait=True` 时调用 `flush`？

参考答案：

```text
因为 smoke 是写入后马上查询。
为了让刚写入的 entity 更稳定地被后续 search 查到，本节在 wait=True 时 flush collection。
这适合学习和验证，但生产中要考虑 flush 对写入吞吐的影响。
```

### 自测 8

如果以后要用真实 embedding，最重要的配置检查是什么？

参考答案：

```text
检查真实 embedding 模型输出维度是否和 Milvus collection 的 vector field 维度一致。
如果模型输出 1024 维，就不能写入 8 维 collection。
```

## 面试表达版本

如果别人问你：“你是怎么把 RAG 文档写入 Milvus 的？”

你可以这样回答：

```text
我先把 Markdown/txt 文档加载成 RagDocument，再按标题和段落切成 RagChunk。
每个 chunk 会生成 embedding，然后变成 EmbeddedChunk。
写入 Milvus 前，我设计了 collection schema：chunk_id 做 VARCHAR 主键，embedding 做 FLOAT_VECTOR 字段，content 和 source、title、permission_group、business_domain 等信息作为 scalar fields 保存。
创建 collection 时给 embedding 建 AUTOINDEX，并指定 COSINE 作为相似度指标。
写入时使用 upsert，因为同一个 chunk_id 可能重复入库或更新。
检索时把用户问题转成同维度 query vector，调用 MilvusClient.search，指定 anns_field、top_k、filter expression 和 output_fields。
最后我把 Milvus 返回的 hit 转成项目统一的 RetrievedChunk，这样上层 RAG 生成、引用、安全检查等逻辑不依赖具体向量数据库。
```

如果别人继续问：“为什么不直接让上层代码用 Milvus 返回结果？”

可以回答：

```text
因为底层向量数据库可能切换。
Qdrant 返回 point，Milvus 返回 hit/entity，如果上层直接依赖它们，后面所有模块都会被具体数据库绑定。
我用 adapter 把外部返回值转成项目内部统一的 RetrievedChunk，让差异停留在 vector store 边界内。
```

## 官方资料

- Milvus Create Collection: https://milvus.io/docs/create-collection.md
- PyMilvus create_collection API: https://milvus.io/api-reference/pymilvus/v3.0.x/MilvusClient/Collections/create_collection.md
- PyMilvus upsert API: https://milvus.io/api-reference/pymilvus/v3.0.x/MilvusClient/Vector/upsert.md
- PyMilvus search API: https://milvus.io/api-reference/pymilvus/v3.0.x/MilvusClient/Vector/search.md

## 下一节

下一节建议学习：

```text
阶段 4 第 35 节：Milvus metadata/scalar filter 和索引基础
```

原因：

本节已经能用 Milvus 写入和检索，但 filter 只是最小可用。

下一节要继续讲清楚：

1. scalar field 为什么能过滤。
2. filter expression 更完整的写法。
3. scalar index 是什么。
4. 哪些 metadata 字段值得建索引。
5. 过滤条件和向量检索的执行关系。
6. Qdrant payload index 和 Milvus scalar index 的思路差异。
