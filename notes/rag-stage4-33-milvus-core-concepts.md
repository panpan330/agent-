# 阶段 4 第 33 节：Milvus 核心概念：collection、schema、field、entity、index

## 0. 本节定位

前两节我们已经完成：

```text
第 31 节：Milvus 是什么，和 Qdrant 有什么区别
第 32 节：本地 Docker 启动 Milvus Standalone
```

现在你的 VMware Ubuntu Docker 里已经能跑 Milvus：

```text
milvus-standalone：Up / healthy
19530：Windows 可连通
9091：Windows 浏览器可打开 WebUI
WebUI 显示：Your Cluster is running well
Deploy Mode：STANDALONE
Build Version：3.0-beta
```

第 33 节开始学习 Milvus 里面真正的数据模型。

本节不急着写入数据。原因是：

```text
Milvus 不是随便塞 JSON 的地方。
在写入数据之前，你必须先理解 collection、schema、field、entity、index。
```

如果把 Milvus 当成 Qdrant 的 point + payload 来直接套，很容易犯这些错误：

1. 不知道 primary key 怎么选。
2. 不知道哪些字段应该是 scalar field。
3. 不知道 vector field 的维度为什么不能随便改。
4. 不知道 schema 一旦创建后哪些地方不好变。
5. 不知道 index 是为了什么，什么时候需要建。
6. 不知道哪些字段会影响后续 filter、delete、upsert、search。

所以本节的任务是：

```text
先把 Milvus 的核心概念学扎实，为第 34 节写入同一批 RAG 文档做准备。
```

## 1. 本节学习目标

学完本节，你要能做到：

1. 解释 Milvus collection 是什么。
2. 解释 schema 是什么，以及为什么写入数据前必须设计 schema。
3. 解释 field 是什么。
4. 区分 primary key field、vector field、scalar field。
5. 解释 entity 是什么。
6. 解释 index 是什么。
7. 说清楚 vector index 和 scalar index 的不同作用。
8. 能把我们项目里的 `RagChunk` 映射成 Milvus schema。
9. 能说清楚 Qdrant 的 `point/payload/vector/id` 和 Milvus 的 `entity/scalar field/vector field/primary key` 怎么对应。
10. 能解释为什么第 34 节写入 Milvus 前必须先设计 collection schema。

## 2. 本节不学什么

这一节先不学：

1. 不写 Python SDK 连接 Milvus。
2. 不创建真实 collection。
3. 不插入真实 RAG chunk。
4. 不做向量搜索。
5. 不调 Milvus index 参数。
6. 不做 Milvus scalar filter 实战。
7. 不替换当前 Qdrant 实现。
8. 不做生产环境 schema 迁移。

这些会放到后面。

第 33 节专注一件事：

```text
理解 Milvus 的数据模型。
```

## 3. 官方资料核对

本节参考官方文档，查阅日期：2026-07-18。

### 3.1 Milvus 官方资料

- Collection Explained: https://milvus.io/docs/manage-collections.md
- Create Collection: https://milvus.io/docs/create-collection.md
- Schema Explained: https://milvus.io/docs/schema.md
- Data Model Design for Search: https://milvus.io/docs/schema-hands-on.md
- Primary Field & AutoID: https://milvus.io/docs/primary-field.md
- Insert Entities: https://milvus.io/docs/insert-update-delete.md
- Index Explained: https://milvus.io/docs/index-explained.md
- In-memory Index: https://milvus.io/docs/index.md

官方文档里的几个关键事实：

1. Collection 可以理解成有固定列和变化行的二维表。
2. 每一列是 field。
3. 每一行是 entity。
4. Schema 描述 collection 的字段结构和约束。
5. Entity 必须满足 schema 才能插入。
6. 每个 collection 必须有且只有一个 primary field。
7. Vector field 保存 embedding，scalar field 保存结构化 metadata。
8. Index 是建立在数据上的额外结构，用于加速搜索，但会带来构建时间、空间、内存和召回率取舍。

## 4. 先给结论

Milvus 的核心心智模型可以用一句话理解：

```text
Milvus collection 很像一张带向量字段的数据库表。
```

更完整一点：

```text
collection 是表。
schema 是表结构。
field 是列。
entity 是行。
primary key field 是唯一 ID 列。
vector field 是保存 embedding 的列。
scalar field 是保存 metadata 的普通字段列。
index 是为了加快向量搜索或字段过滤而建立的辅助结构。
```

如果映射到我们 RAG 项目：

```text
一个 collection = 一个知识库或一类可统一检索的 chunk 集合
一个 entity = 一个 chunk 的入库记录
一个 vector field = chunk embedding
多个 scalar field = source/title/section/doc_type/business_domain/permission_group/content 等字段
一个 primary key = chunk_id 或 Milvus 自动生成的 id
一个 index = 为 embedding search 或 metadata filter 加速的结构
```

这就是第 34 节能写数据的前提。

## 5. 基础知识铺垫

### 5.1 先用关系型数据库类比

你有 Java 基础，所以我们先用数据库表理解 Milvus。

比如一个普通订单表：

```sql
create table orders (
    id bigint primary key,
    user_id varchar(64),
    status varchar(32),
    amount decimal(10, 2)
);
```

这里：

| 概念 | 解释 |
| --- | --- |
| `orders` | 表 |
| `id/user_id/status/amount` | 字段，也就是列 |
| `id bigint primary key` | 主键字段 |
| 每一条订单记录 | 一行数据 |

Milvus 也有类似结构，只是它多了一类特殊字段：

```text
vector field
```

也就是向量字段。

### 5.2 普通数据库表和 Milvus collection 的共同点

共同点：

1. 都要定义数据结构。
2. 都要有字段。
3. 都可以有主键。
4. 都可以插入多条记录。
5. 都可以按某些字段查询。
6. 都可以通过索引提升查询效率。

如果你把 Milvus 完全看成一个陌生东西，会很难。

如果你把它先看成：

```text
带向量字段的数据库表
```

就容易很多。

### 5.3 普通数据库表和 Milvus collection 的不同点

不同点也很重要。

| 对比项 | 普通数据库表 | Milvus collection |
| --- | --- | --- |
| 核心查询 | 精确查询、范围查询、聚合 | 向量相似度搜索 + scalar filter |
| 特殊字段 | 没有向量字段 | 有 vector field |
| 查询目标 | 找满足条件的行 | 找与 query vector 最相似的 entity |
| 主要索引 | B-Tree、Hash 等 | 向量索引、scalar index |
| 常见用途 | 业务数据 CRUD | embedding 检索、RAG、相似图片/文本搜索 |

所以不要把 Milvus 当成 MySQL 替代品。

Milvus 的强项是：

```text
高维向量相似度检索。
```

### 5.4 为什么 RAG 需要 schema

我们项目里的一个 chunk 有很多字段：

```text
chunk_id
content
embedding
source
title
section
doc_type
business_domain
permission_group
chunk_index
chunk_count
```

如果没有 schema，系统就不知道：

1. 哪个字段是唯一 ID。
2. 哪个字段是向量。
3. 向量是多少维。
4. 哪些字段是字符串。
5. 哪些字段是整数。
6. 哪些字段可以用于 filter。
7. 哪些字段要返回给模型。
8. 哪些字段后续可以建索引。

Milvus 的 schema 就是把这些约定固定下来。

### 5.5 schema 是“写入前的合同”

你可以把 schema 理解成：

```text
写入数据前，数据库和应用程序之间签的一份合同。
```

例如：

```text
你必须给我一个 chunk_id。
你必须给我一个 content。
你必须给我一个 1536 维 embedding。
你可以给我 source、title、section。
permission_group 必须是字符串。
chunk_index 必须是整数。
```

如果你后面插入的数据不符合这份合同，Milvus 就应该拒绝。

这不是麻烦，而是保护。

它能避免知识库长期运行后出现：

1. 字段名混乱。
2. 类型混乱。
3. 向量维度混乱。
4. 权限字段缺失。
5. 无法稳定过滤。
6. 无法稳定删除旧文档。

### 5.6 field 是 schema 的基本单位

schema 由 field 组成。

每个 field 要说明：

1. 字段名。
2. 数据类型。
3. 是否主键。
4. 是否向量。
5. 向量维度。
6. 字符串最大长度。
7. 是否允许为空。
8. 是否有默认值。
9. 是否启用 auto_id。

不是每个字段都要配置所有东西。

不同字段关心的约束不同。

### 5.7 entity 是一行真实数据

如果 schema 是表结构，那么 entity 就是一行数据。

例如 schema 有这些字段：

```text
chunk_id
content
embedding
source
permission_group
```

那么一个 entity 可能是：

```text
chunk_id = "refund_return_policy_chunk_0003"
content = "商品质量问题导致退货时，运费通常由商家承担。"
embedding = [0.13, 0.72, -0.31, ...]
source = "refund-return-policy.md"
permission_group = "customer_service"
```

在 RAG 里，一个 entity 通常对应一个 chunk。

### 5.8 vector field 是 Milvus 的核心字段

vector field 保存 embedding。

比如：

```text
embedding: FLOAT_VECTOR(dim=1536)
```

这表示：

```text
embedding 字段保存 1536 维浮点向量。
```

如果你的 embedding 模型输出 1536 维，你的 vector field 就要按 1536 维设计。

如果后面换成 1024 维模型，原 collection 不能随便继续写。

这就是第 24 节讲过的：

```text
embedding 模型选择会影响向量数据库结构。
```

### 5.9 scalar field 是 metadata 的落点

scalar field 保存普通结构化字段。

例如：

```text
source: VARCHAR
title: VARCHAR
section: VARCHAR
doc_type: VARCHAR
business_domain: VARCHAR
permission_group: VARCHAR
chunk_index: INT64
chunk_count: INT64
```

这些字段不参与向量相似度计算，但很重要。

它们用于：

1. 权限过滤。
2. 文档类型过滤。
3. 业务域过滤。
4. 引用来源展示。
5. 删除旧文档。
6. 调试坏答案。
7. 评测检索质量。

企业 RAG 不能只保存 embedding。

### 5.10 primary key 是唯一定位

primary key 是主键。

Milvus 官方文档强调：每个 collection 必须有且只有一个 primary field，用来唯一标识每个 entity。

它用于：

1. insert。
2. upsert。
3. delete。
4. query。
5. 避免歧义。

在 RAG 里，primary key 可以有两种思路：

| 方案 | 说明 |
| --- | --- |
| AutoID | 让 Milvus 自动生成 INT64 id |
| Manual ID | 我们自己提供 chunk_id，例如字符串 |

### 5.11 AutoID 和 Manual ID 怎么选

AutoID 好处：

1. 简单。
2. 不用自己生成唯一 ID。
3. 插入时方便。

AutoID 代价：

1. Milvus 生成的 id 和你的业务 chunk_id 不一定天然对应。
2. 删除某个 source 的旧 chunks 时，你仍然需要额外字段支持。
3. 文档刷新时要更谨慎处理重复数据。

Manual ID 好处：

1. 可以和业务 chunk_id 对齐。
2. 方便定位具体 chunk。
3. 方便幂等写入和排查。
4. 更适合我们这种学习版 RAG 对比 Qdrant。

Manual ID 代价：

1. 你要保证唯一。
2. 字符串长度要设计。
3. 生成规则要稳定。

我们项目已经有稳定 `chunk_id`，所以后面更适合先用 Manual ID 思路。

### 5.12 index 是什么

index 是索引。

普通数据库索引用来加速：

```sql
where user_id = 'U001'
```

Milvus 里的索引有两类重点：

1. vector index：加速向量相似度搜索。
2. scalar index：加速 metadata/filter 查询。

官方文档里说 index 是建立在数据之上的额外结构，可以加速搜索，但会带来预处理时间、空间、搜索时 RAM 成本，并可能影响召回率。

你要记住：

```text
索引是为了快，但不是免费的。
```

### 5.13 为什么不先学 index 参数

Milvus 支持很多 index 类型。

比如：

1. FLAT。
2. IVF_FLAT。
3. HNSW。
4. DISKANN。
5. AUTOINDEX。
6. SPARSE_INVERTED_INDEX。
7. BITMAP。
8. INVERTED。

如果一开始就陷入这些名字，会丢掉主线。

第 33 节只要求你理解：

```text
index 是干什么的。
vector index 和 scalar index 有什么区别。
为什么 index 要结合数据规模、查询方式和评测结果选择。
```

具体 index 参数，后面再学。

### 5.14 load 和 release 是什么

Milvus 的 collection 创建、插入、建索引之后，搜索时还涉及 load。

官方文档提到，加载 collection 是执行相似度搜索和查询的前提，因为 Milvus 要把 index 文件和 raw data 加载到内存，以便快速响应。

你先这样理解：

```text
collection 存在，不等于它已经准备好被快速搜索。
load 是把它加载到内存以便搜索。
release 是释放不再使用的 collection，节省内存。
```

这对你当前虚拟机尤其重要。

你的 Ubuntu 内存只有 3.8Gi，低于 Milvus 官方 Standalone 最低 8Gi 建议，所以更要理解：

```text
搜索会吃内存。
加载 collection 会吃内存。
索引也会吃内存。
```

### 5.15 dynamic field 是什么

Milvus 支持 dynamic field。

它允许插入 schema 里没有提前定义的字段，这些额外字段会进入保留字段。

这听起来像 Qdrant payload 的灵活性。

但本阶段我不建议你优先依赖 dynamic field。

原因：

1. 你正在学习 schema 设计。
2. 企业 RAG 的权限字段、来源字段、业务字段应该明确。
3. 过度依赖动态字段会削弱约束。
4. 后续 filter 和索引设计更容易混乱。

学习阶段建议：

```text
核心字段先显式定义。
dynamic field 后面作为补充理解。
```

## 6. 本节主题系统讲解

### 6.1 Milvus collection 是什么

collection 是 Milvus 管理数据的基本容器。

官方文档把 collection 描述成类似二维表：

```text
固定列 + 可变化行
```

其中：

```text
列 = field
行 = entity
```

类比关系型数据库：

```text
collection ~= table
entity ~= row
field ~= column
```

在 RAG 里，一个 collection 可以表示：

1. 一个知识库。
2. 一个租户的知识库。
3. 一个业务域的知识库。
4. 一个环境的数据集合。
5. 一个 embedding 模型版本对应的向量集合。

### 6.2 一个 RAG 项目应该建几个 collection

这个问题没有绝对答案。

常见思路有三种。

#### 6.2.1 一个项目一个 collection

例如：

```text
learning_rag_chunks
```

优点：

1. 简单。
2. 适合学习。
3. 所有文档统一检索。
4. schema 统一。

缺点：

1. 多租户隔离弱。
2. 权限全靠 scalar filter。
3. 数据规模大后管理复杂。

#### 6.2.2 一个业务域一个 collection

例如：

```text
refund_rag_chunks
order_rag_chunks
account_rag_chunks
```

优点：

1. 业务边界清楚。
2. 检索范围自然缩小。
3. 不同业务可以有不同 schema。

缺点：

1. 多 collection 管理复杂。
2. 跨业务检索需要多路召回。
3. 代码复杂度上升。

#### 6.2.3 一个租户一个 collection

例如：

```text
tenant_a_rag_chunks
tenant_b_rag_chunks
```

优点：

1. 数据隔离强。
2. 权限风险降低。

缺点：

1. collection 数量可能很多。
2. 运维和索引管理更复杂。
3. 跨租户统计和运营更麻烦。

### 6.3 当前学习项目适合哪种

我们当前学习项目适合：

```text
一个 collection 保存当前示例知识库 chunks
```

原因：

1. 现在重点是学习 Milvus 概念。
2. 示例文档数量少。
3. schema 可以统一。
4. 权限和业务域先用 scalar field 表达。
5. 后续更容易和 Qdrant 对比。

可以命名为：

```text
learning_rag_chunks_milvus
```

注意：第 33 节不真正创建 collection。这里只是设计思路。

### 6.4 schema 是什么

schema 是 collection 的结构定义。

它规定：

1. 有哪些字段。
2. 每个字段叫什么。
3. 每个字段是什么类型。
4. 哪个字段是 primary key。
5. 哪个字段是 vector field。
6. vector field 的维度是多少。
7. VARCHAR 最大长度是多少。
8. 字段是否 nullable。
9. 是否开启 auto_id。

如果没有 schema，Milvus 不知道怎么组织 entity。

### 6.5 为什么 schema 设计比创建 collection 更重要

创建 collection 只是命令。

schema 设计才是工程判断。

坏 schema 会导致：

1. 后续无法按权限过滤。
2. 无法按 source 删除旧文档。
3. 引用来源缺字段。
4. chunk_id 不稳定。
5. content 太长超过字段限制。
6. embedding 维度不匹配。
7. 后续改字段很麻烦。

所以你以后不能只问：

```text
Milvus 怎么 create_collection？
```

更应该先问：

```text
这个 RAG 业务需要哪些字段？
哪些字段用于搜索？
哪些字段用于过滤？
哪些字段用于展示？
哪些字段用于删除和更新？
哪些字段用于审计？
```

### 6.6 field 是什么

field 是 collection 的字段，也就是表的列。

常见 field 类型：

1. primary key field
2. vector field
3. scalar field

在 RAG 里，字段设计通常来自 chunk 数据模型。

例如：

```text
chunk_id
content
embedding
source
title
section
doc_type
business_domain
permission_group
chunk_index
chunk_count
```

这些字段共同描述一个 chunk。

### 6.7 primary key field

primary key field 用来唯一标识 entity。

Milvus 要求：

1. 每个 collection 必须有一个 primary field。
2. primary field 值不能为 null。
3. primary field 类型创建后不能随便改。
4. primary field 可以是 `INT64` 或 `VARCHAR`。

在我们的 RAG 项目里，推荐思路：

```text
chunk_id: VARCHAR primary key
```

例如：

```text
refund_return_policy_chunk_0003
```

原因：

1. 和现有 `RagChunk.chunk_id` 对齐。
2. 和 Qdrant point id 对齐。
3. 排查问题时直观。
4. 文档刷新时更容易做幂等逻辑。

### 6.8 vector field

vector field 保存向量。

对于文本 RAG，通常是 dense vector：

```text
embedding: FLOAT_VECTOR
dim: 1536
metric_type: COSINE 或 IP
```

注意这里有两个关键点：

#### 6.8.1 维度必须和 embedding 模型一致

如果 embedding 模型输出 1536 维：

```text
dim = 1536
```

如果模型输出 1024 维：

```text
dim = 1024
```

不能混写。

#### 6.8.2 metric type 要和模型和评测匹配

常见 metric：

1. COSINE
2. IP
3. L2

学习阶段可以先选常见方案。

生产阶段需要结合 embedding 模型说明和评测结果。

### 6.9 scalar field

scalar field 保存结构化值。

Milvus 官方文档说，scalar fields 常用于保存 vector embeddings 的 metadata，并通过 metadata filtering 改善搜索结果正确性。

对 RAG 来说，scalar field 是企业能力的基础。

例如：

| 字段 | 类型 | 用途 |
| --- | --- | --- |
| `content` | VARCHAR | 给模型看的 chunk 原文 |
| `source` | VARCHAR | 来源文件，支持引用和删除 |
| `title` | VARCHAR | 文档标题，支持引用 |
| `section` | VARCHAR | 所属章节，支持引用和调试 |
| `doc_type` | VARCHAR | 文档类型过滤 |
| `business_domain` | VARCHAR | 业务域过滤 |
| `permission_group` | VARCHAR | 权限过滤 |
| `chunk_index` | INT64 | chunk 顺序 |
| `chunk_count` | INT64 | 文档总 chunk 数 |

不要小看 scalar field。

没有它们，RAG 就只剩：

```text
向量相似度
```

这不够企业使用。

### 6.10 content 应该放 scalar field 吗

这是一个重要问题。

在 RAG 中，检索返回的结果最后要给模型看。

模型需要原文：

```text
content
```

所以 content 可以作为 `VARCHAR` 字段保存。

但要注意：

1. Milvus VARCHAR 有最大长度。
2. chunk 不应该太大。
3. 如果 content 太长，schema 需要合理设置 `max_length`。
4. 也可以只保存引用 ID，原文放到对象存储或普通数据库。

学习阶段为了简单，可以把 content 存进 Milvus。

生产阶段要看：

1. 文本长度。
2. 返回 payload 大小。
3. 成本。
4. 隐私和权限。
5. 是否需要独立文档存储。

### 6.11 source 为什么必须保留

`source` 很重要。

用途：

1. 引用来源。
2. 删除旧文档。
3. 重新入库。
4. 排查坏答案。
5. 评测检索结果。

比如你要刷新：

```text
refund-return-policy.md
```

就需要先删除旧 chunks：

```text
source == "refund-return-policy.md"
```

如果没有 source，你就很难知道哪些 entity 属于这个文档。

### 6.12 permission_group 为什么必须保留

企业 RAG 里，权限字段必须前置设计。

比如：

```text
permission_group = "customer_service"
```

检索时要加 filter：

```text
permission_group == 当前用户权限组
```

否则模型可能看到不该看的文档。

你要记住：

```text
权限不是模型自己保证的。
权限要在后端检索层保证。
```

### 6.13 business_domain 和 doc_type 的作用

`business_domain` 用于业务范围：

```text
refund
shipping
account
order
```

`doc_type` 用于文档类型：

```text
policy
faq
guide
notice
```

这些字段可以帮助：

1. 缩小检索范围。
2. 提升召回质量。
3. 方便运营知识库。
4. 方便评测不同业务域效果。

### 6.14 entity 是什么

entity 是 collection 里的一条数据记录。

官方文档里说，entity 是共享同一 schema 的数据记录，一行里所有字段值共同组成一个 entity。

在 RAG 中：

```text
一个 entity = 一个 chunk 的入库记录
```

例如：

```text
chunk_id = "refund_return_policy_chunk_0003"
content = "商品质量问题导致退货时，运费通常由商家承担。"
embedding = [0.12, -0.03, ...]
source = "refund-return-policy.md"
business_domain = "refund"
permission_group = "customer_service"
```

这个整体就是一条 entity。

### 6.15 insert 和 upsert 的区别

虽然本节不写数据，但你需要先知道概念。

`insert` 是插入。

如果主键重复，普通 insert 可能造成重复或应用层问题，具体行为要参考官方文档和版本。

`upsert` 是更新或插入。

大概意思：

```text
如果不存在，就插入。
如果已经存在，就更新。
```

RAG 文档刷新时，upsert 思维很重要。

但我们的文档更新通常更稳妥的做法是：

```text
按 source 删除旧 chunks
-> 重新切分
-> 重新 embedding
-> 重新写入
```

这是第 23 节已经讲过的主线。

### 6.16 index 是什么

index 是加速结构。

在 Milvus 里，index 可以建在 field 上。

有两类重点：

1. vector field index
2. scalar field index

它们都叫 index，但目的不同。

### 6.17 vector index 的作用

vector index 加速向量相似度搜索。

没有向量索引时：

```text
可能要暴力比较很多向量。
```

有向量索引后：

```text
可以更快找到相似向量。
```

但代价是：

1. 建索引需要时间。
2. 索引占磁盘或内存。
3. 搜索时可能增加内存。
4. 近似搜索可能影响召回率。
5. 参数需要调优。

### 6.18 scalar index 的作用

scalar index 加速普通字段过滤。

例如：

```text
permission_group == "customer_service"
business_domain == "refund"
source == "refund-return-policy.md"
```

如果数据量小，没建 scalar index 也可能能跑。

如果数据量大，高频过滤字段就应该评估 scalar index。

这和普通数据库一样：

```text
经常用来 where 的字段，可能需要索引。
```

### 6.19 filter 和 index 的关系

filter 是查询条件。

index 是加速结构。

不要混淆：

```text
filter 决定查什么。
index 决定怎么更快地查。
```

比如：

```text
permission_group == "customer_service"
```

这是 filter。

如果给 `permission_group` 建索引，那是为了让这个 filter 更快。

### 6.20 load 和 index 的关系

在 Milvus 中，搜索通常需要 collection 被加载。

加载时会把相关数据和索引放到内存里，以便快速查询。

这意味着：

```text
索引不是建完就万事大吉。
搜索时还要考虑加载状态和内存占用。
```

对你当前虚拟机来说，内存只有 3.8Gi，所以后续写入和查询时我们会控制数据量。

## 7. 用我们项目设计一个 Milvus schema

### 7.1 当前 RAG chunk 数据

我们当前项目里的 RAG chunk 大概包含：

```text
chunk_id
content
source
title
section
file_name
file_extension
doc_type
business_domain
permission_group
chunk_index
chunk_count
chunk_size_chars
embedding
```

第 34 节会用同一批文档写入 Milvus。

所以第 33 节先设计 schema。

### 7.2 学习版 Milvus collection 名称

建议名称：

```text
learning_rag_chunks_milvus
```

原因：

1. 和 Qdrant 的 `learning_rag_chunks` 区分。
2. 一眼能看出是 Milvus 版本。
3. 适合学习阶段。
4. 避免误删 Qdrant 数据。

### 7.3 学习版 schema 设计

可以先设计成：

| 字段名 | Milvus 类型 | 角色 | 用途 |
| --- | --- | --- | --- |
| `chunk_id` | `VARCHAR` | primary key | 唯一标识 chunk |
| `embedding` | `FLOAT_VECTOR` | vector field | 语义检索 |
| `content` | `VARCHAR` | scalar field | 给模型回答使用 |
| `source` | `VARCHAR` | scalar field | 引用、删除、刷新 |
| `title` | `VARCHAR` | scalar field | 引用展示 |
| `section` | `VARCHAR` | scalar field | 章节定位 |
| `doc_type` | `VARCHAR` | scalar field | 文档类型过滤 |
| `business_domain` | `VARCHAR` | scalar field | 业务域过滤 |
| `permission_group` | `VARCHAR` | scalar field | 权限过滤 |
| `chunk_index` | `INT64` | scalar field | chunk 顺序 |
| `chunk_count` | `INT64` | scalar field | chunk 总数 |
| `chunk_size_chars` | `INT64` | scalar field | chunk 大小观察 |

### 7.4 为什么 `chunk_id` 选 VARCHAR primary key

因为我们项目已有稳定 chunk_id。

例如：

```text
refund_return_policy_chunk_0003
```

使用它做 primary key 的好处：

1. 和 Qdrant point id 映射一致。
2. 不需要额外维护 Milvus auto id 和业务 chunk id 的关系。
3. 日志和 WebUI 中更容易识别。
4. 文档刷新和测试更直观。

### 7.5 为什么 `embedding` 是 FLOAT_VECTOR

因为我们做的是文本语义检索。

文本 embedding 通常是浮点向量。

学习阶段我们可以继续用 fake embedding 或小维度向量做练习。

例如第 13 节曾经用 8 维 fake vector 观察流程。

但真实 embedding 可能是：

```text
1024 维
1536 维
3072 维
```

Milvus collection 的 vector field 维度必须和写入向量一致。

### 7.6 为什么 content 存 VARCHAR

因为 RAG 搜索返回后要把 chunk 原文交给模型。

如果 Milvus 里只保存向量，不保存 content，那么检索后还要去别的地方按 chunk_id 查原文。

学习阶段为了简单：

```text
Milvus entity 里直接保存 content。
```

生产阶段可以评估：

```text
Milvus 保存 chunk_id 和 metadata，原文存普通数据库或对象存储。
```

### 7.7 为什么 source/title/section 都要有

它们是 citation 的基础。

如果回答里要显示：

```text
来源：refund-return-policy.md / 运费处理
```

就需要：

```text
source
title
section
```

没有这些字段，答案即使正确，也不够可信。

### 7.8 为什么 permission_group 必须是显式字段

因为权限过滤不能依赖模型。

检索时要先控制：

```text
只能查当前用户有权限看的 entity。
```

所以 `permission_group` 必须明确存在。

如果你把它随便塞进动态字段，后续 filter 和索引更容易失控。

### 7.9 为什么 chunk_index/chunk_count 有用

这两个字段不是检索必须字段，但对工程有用。

用途：

1. 调试 chunk 切分。
2. 观察一个文档被切成多少段。
3. 判断是否需要扩大上下文。
4. 引用时显示更细的片段位置。
5. 后续做相邻 chunk 扩展时有用。

### 7.10 是否需要 file_name/file_extension

可以需要，也可以先不需要。

如果你要按文件扩展名过滤：

```text
.md
.txt
.pdf
```

就可以保留 `file_extension`。

如果当前学习阶段文档都很简单，可以先保留核心字段，避免 schema 太大。

我的建议：

```text
第 34 节先用必要字段。
后续再根据需要补字段。
```

但注意：Milvus 后续新增字段有约束，不像 Python dict 那么随意。

### 7.11 是否开启 dynamic field

学习阶段建议：

```text
先不开或不依赖 dynamic field。
```

原因：

1. 我们要练 schema 设计。
2. RAG 核心 metadata 应该显式。
3. 后续 filter 字段应该稳定。
4. 便于和 Qdrant payload 做清晰对比。

dynamic field 可以以后作为进阶补充。

## 8. Qdrant 和 Milvus 概念继续对应

### 8.1 总对应表

| RAG 概念 | Qdrant | Milvus |
| --- | --- | --- |
| 知识库向量集合 | collection | collection |
| 一个 chunk 记录 | point | entity |
| 唯一 ID | point id | primary key field |
| embedding | vector | vector field |
| metadata | payload | scalar fields |
| 原文 content | payload.content | scalar field `content` |
| 权限字段 | payload.permission_group | scalar field `permission_group` |
| 过滤 | payload filter | scalar filter |
| 向量索引 | vector index | vector index |
| metadata 索引 | payload index | scalar index |

### 8.2 为什么 Milvus 更强调 schema

Qdrant 的 payload 更灵活。

Milvus 的 field 更明确。

这带来的差异：

| 对比 | Qdrant | Milvus |
| --- | --- | --- |
| 初学写入 | 更像写 JSON | 更像数据库建表 |
| 字段约束 | 主要靠应用层规范 | schema 层面更明确 |
| filter 字段 | payload 字段 | scalar field |
| 变更成本 | 相对轻 | 要考虑 schema 约束 |
| 团队协作 | 需要额外约定 | schema 更像共同合同 |

### 8.3 为什么不能机械迁移

不能把 Qdrant payload 里的所有东西无脑变成 Milvus field。

要先问：

1. 这个字段是否真的需要 filter？
2. 这个字段是否需要返回给模型？
3. 这个字段是否用于 citation？
4. 这个字段是否用于删除/刷新？
5. 这个字段是否频繁变化？
6. 这个字段类型是否稳定？

字段越多，schema 越复杂。

字段太少，业务能力不够。

schema 设计就是权衡。

## 9. 常见误区

### 9.1 误区一：collection 就等于整个数据库

不准确。

Milvus 服务可以有多个 collection。

一个 collection 更像：

```text
一张表
```

不是整个数据库实例。

### 9.2 误区二：entity 只是一条向量

不准确。

entity 是一条记录。

它通常包含：

1. primary key。
2. vector field。
3. scalar fields。

向量只是其中一个字段。

### 9.3 误区三：schema 只是形式

不对。

schema 决定：

1. 能写入什么数据。
2. 能怎样过滤。
3. 能返回什么字段。
4. 后续能否删除和刷新。
5. 后续能否建索引。
6. 团队能否稳定协作。

schema 是工程边界。

### 9.4 误区四：只要建了 vector index，RAG 质量就高

不对。

vector index 主要影响搜索性能和召回方式。

RAG 质量还取决于：

1. 文档质量。
2. chunk 切分。
3. embedding 模型。
4. metadata 设计。
5. filter。
6. top_k。
7. score_threshold。
8. rerank。
9. prompt。
10. 引用和安全检查。

### 9.5 误区五：scalar field 不重要

不对。

企业 RAG 里 scalar field 非常重要。

没有 scalar field，就很难做：

1. 权限过滤。
2. 业务域过滤。
3. 引用来源。
4. 文档刷新。
5. 审计排查。
6. 评测分析。

### 9.6 误区六：AutoID 一定比手动 ID 好

不一定。

AutoID 简单，但不一定适合所有 RAG 场景。

如果你希望 ID 和 chunk_id 对齐，手动 ID 更直观。

关键看：

```text
ID 是否需要和业务系统对齐。
```

### 9.7 误区七：字段越多越好

不对。

字段太多会让 schema 复杂：

1. 写入数据更麻烦。
2. 字段变更更麻烦。
3. 索引选择更复杂。
4. 团队理解成本更高。

字段设计要服务业务。

## 10. 面试和表达方式

### 10.1 如果别人问：Milvus collection 是什么

可以这样说：

```text
Milvus collection 是一组结构相同的数据记录，可以类比关系型数据库里的表。它有 schema，schema 里定义 fields，每一条写入的数据是 entity。在 RAG 里，一个 collection 通常保存一批文档 chunk 的 embedding 和 metadata。
```

### 10.2 如果别人问：schema 是什么

可以这样说：

```text
schema 是 collection 的结构定义，规定有哪些字段、字段类型、哪个是 primary key、哪个是 vector field、向量维度是多少、哪些是 scalar fields。它相当于写入数据前的合同，保证插入的 entity 结构一致。
```

### 10.3 如果别人问：field 有哪些类型

可以这样说：

```text
在 RAG 场景里主要关注三类字段：primary key field 用来唯一标识 entity，vector field 用来保存 embedding 做相似度搜索，scalar field 用来保存 metadata，例如 source、title、permission_group、business_domain，用于过滤、引用和管理。
```

### 10.4 如果别人问：entity 是什么

可以这样说：

```text
entity 是 Milvus collection 里的一条数据记录，可以类比表里的一行。在 RAG 中，一个 entity 通常对应一个 chunk，包含 chunk_id、embedding、content 和各种 metadata 字段。
```

### 10.5 如果别人问：index 是什么

可以这样说：

```text
index 是建立在数据上的额外结构，用来加速搜索。Milvus 里有 vector index 和 scalar index：vector index 加速向量相似度搜索，scalar index 加速 metadata/filter 查询。索引能提升性能，但会带来构建时间、存储、内存和召回率取舍。
```

### 10.6 如果别人问：你会怎么给 RAG 设计 Milvus schema

可以这样说：

```text
我会先从 RAG chunk 数据模型出发。至少设计一个 primary key，比如 chunk_id；一个 vector field，比如 embedding；再设计 scalar fields 保存 content、source、title、section、doc_type、business_domain、permission_group、chunk_index 等。这样既能做语义检索，也能做权限过滤、引用来源、文档刷新和调试排查。
```

## 11. 本节和后续课程的关系

第 33 节是概念设计。

后面几节会这样走：

| 节 | 主题 | 关系 |
| --- | --- | --- |
| 第 34 节 | 用同一批文档写入 Milvus 并做向量检索 | 把本节 schema 设计变成真实 collection 和 entity |
| 第 35 节 | Milvus metadata/scalar filter 和索引基础 | 深入使用 scalar field 做过滤，并理解 index |
| 第 36 节 | Qdrant vs Milvus：什么时候选谁 | 基于 Qdrant 和 Milvus 两边实操做选型复盘 |

所以本节学不扎实，第 34 节写入代码会变成照抄。

本节学扎实，第 34 节你会知道每一行代码为什么存在。

## 12. 本节最小完整理解图

```text
Milvus Server
  |
  v
Collection: learning_rag_chunks_milvus
  |
  v
Schema
  |
  |-- chunk_id: VARCHAR, primary key
  |-- embedding: FLOAT_VECTOR(dim=...)
  |-- content: VARCHAR
  |-- source: VARCHAR
  |-- title: VARCHAR
  |-- section: VARCHAR
  |-- doc_type: VARCHAR
  |-- business_domain: VARCHAR
  |-- permission_group: VARCHAR
  |-- chunk_index: INT64
  |-- chunk_count: INT64
  |
  v
Entity
  |
  |-- 一条 chunk 入库记录
  |
  v
Index
  |
  |-- vector index: 加速 embedding 相似度搜索
  |-- scalar index: 加速 metadata/filter 查询
```

## 13. 本节没有改代码的原因

本节没有新增运行代码。

原因：

1. 第 33 节目标是理解 Milvus 数据模型。
2. 创建 collection 前必须先会设计 schema。
3. 如果现在直接写 Python SDK，容易变成照抄示例。
4. 第 34 节会正式把 schema 落到代码和 Milvus 实例。

这节不是停在理论上，而是在为下一节写代码打地基。

## 14. 本节练习

### 练习 1：概念配对

把下面概念配对：

| 普通数据库 | Milvus |
| --- | --- |
| 表 | ? |
| 列 | ? |
| 行 | ? |
| 主键 | ? |
| 索引 | ? |

### 练习 2：字段分类

把下面字段分成 primary key field、vector field、scalar field：

```text
chunk_id
embedding
content
source
permission_group
chunk_index
```

### 练习 3：解释 schema

请用自己的话解释：

```text
为什么 Milvus 写入 RAG chunk 前要先设计 schema？
```

### 练习 4：设计字段

如果你要保存一个客服知识库 chunk，至少应该有哪些字段？

要求至少包含：

1. 唯一 ID。
2. 向量。
3. 原文。
4. 来源。
5. 权限。

### 练习 5：判断题

判断下面说法是否正确：

1. Milvus entity 只保存向量，不保存普通字段。
2. scalar field 可以用于权限过滤。
3. vector index 是为了加速向量相似度搜索。
4. primary key 可以帮助唯一定位 entity。
5. schema 设计不好，后续 RAG 的引用、过滤、删除都会受影响。

### 练习 6：Qdrant 对比

请说明 Qdrant 的 `point.id`、`point.vector`、`point.payload` 分别对应 Milvus 里的什么概念。

## 15. 练习参考答案

### 练习 1 参考答案

| 普通数据库 | Milvus |
| --- | --- |
| 表 | collection |
| 列 | field |
| 行 | entity |
| 主键 | primary key field |
| 索引 | index |

### 练习 2 参考答案

| 字段 | 分类 |
| --- | --- |
| `chunk_id` | primary key field |
| `embedding` | vector field |
| `content` | scalar field |
| `source` | scalar field |
| `permission_group` | scalar field |
| `chunk_index` | scalar field |

### 练习 3 参考答案

因为 schema 规定了 collection 里有哪些字段、字段类型、哪个字段是主键、哪个字段是向量、向量维度是多少，以及哪些 metadata 可以保存和过滤。RAG chunk 写入前如果不设计 schema，后续可能出现字段缺失、类型不一致、向量维度不匹配、无法权限过滤、无法引用来源、无法按 source 删除旧文档等问题。

### 练习 4 参考答案

至少可以设计：

| 字段 | 类型思路 | 用途 |
| --- | --- | --- |
| `chunk_id` | `VARCHAR` primary key | 唯一 ID |
| `embedding` | `FLOAT_VECTOR` | 向量检索 |
| `content` | `VARCHAR` | 原文 |
| `source` | `VARCHAR` | 来源和删除 |
| `permission_group` | `VARCHAR` | 权限过滤 |

还可以补充：

```text
title
section
doc_type
business_domain
chunk_index
chunk_count
```

### 练习 5 参考答案

1. 不正确。entity 是一条记录，除了向量字段，也可以包含 scalar fields。
2. 正确。`permission_group` 这类 scalar field 可以用于权限过滤。
3. 正确。vector index 用于加速向量相似度搜索。
4. 正确。primary key 用于唯一定位 entity。
5. 正确。schema 决定后续能否稳定引用、过滤、删除和排查。

### 练习 6 参考答案

| Qdrant | Milvus |
| --- | --- |
| `point.id` | primary key field |
| `point.vector` | vector field |
| `point.payload` | scalar fields 或 dynamic field |

## 16. 自测题

### 自测 1

Milvus collection 和普通数据库表有什么相似之处？

### 自测 2

Milvus collection 和普通数据库表最重要的不同是什么？

### 自测 3

schema 主要规定哪些东西？

### 自测 4

primary key field 在 Milvus 中有什么作用？

### 自测 5

为什么 RAG 中的 `embedding` 应该是 vector field？

### 自测 6

为什么 `permission_group` 应该设计成 scalar field？

### 自测 7

为什么 `source` 对文档更新和删除很重要？

### 自测 8

vector index 和 scalar index 的区别是什么？

### 自测 9

为什么 index 不是免费的？

### 自测 10

为什么第 33 节不直接写 Python 代码？

## 17. 自测题参考答案

### 自测 1 参考答案

它们都可以看成结构化数据集合。collection 类似表，field 类似列，entity 类似行，primary key field 类似主键。

### 自测 2 参考答案

Milvus collection 有 vector field，可以保存 embedding 并做向量相似度搜索；普通数据库表主要做精确查询、范围查询、排序、聚合等传统查询。

### 自测 3 参考答案

schema 规定字段名、字段类型、主键、向量字段、向量维度、字符串最大长度、是否允许为空、是否 auto_id，以及字段约束。

### 自测 4 参考答案

primary key field 用来唯一标识每个 entity。Milvus 通过它管理 insert、upsert、delete、query 等操作，避免无法区分数据记录。

### 自测 5 参考答案

因为 embedding 是文本语义向量，Milvus 要根据它做相似度搜索。vector field 专门用于保存这类向量，并配合 vector index 和 metric type 做 ANN 检索。

### 自测 6 参考答案

因为 `permission_group` 是结构化 metadata，不参与向量相似度计算，但检索时必须用于权限过滤，防止用户看到无权访问的文档。

### 自测 7 参考答案

因为文档更新时需要找到旧文档对应的所有 chunks。`source` 能标记每个 chunk 来自哪个文件，方便按 source 删除旧 entity，再重新入库。

### 自测 8 参考答案

vector index 加速向量相似度搜索，例如根据 query embedding 找相似 chunk；scalar index 加速普通字段过滤，例如按 `permission_group`、`business_domain` 或 `source` 筛选。

### 自测 9 参考答案

因为 index 会带来构建时间、存储空间、内存占用和参数调优成本。近似向量索引还可能带来召回率取舍，所以必须结合数据规模和评测结果使用。

### 自测 10 参考答案

因为本节目标是理解 Milvus 的核心数据模型。直接写 SDK 代码容易变成照抄示例，而不知道 collection、schema、field、entity、index 的设计含义。第 34 节会在理解 schema 后再写入真实数据。

## 18. 本节总结

本节最重要的是建立 Milvus 的数据模型心智。

你现在应该知道：

1. collection 类似表。
2. schema 是 collection 的结构定义。
3. field 类似列。
4. entity 类似行。
5. primary key field 唯一定位 entity。
6. vector field 保存 embedding。
7. scalar field 保存 metadata。
8. index 是建立在数据上的加速结构。
9. vector index 加速相似度搜索。
10. scalar index 加速 metadata/filter 查询。
11. RAG schema 设计要从 chunk 数据模型、权限、引用、删除、过滤、评测出发。
12. 我们第 34 节会把本节 schema 设计落到 Milvus 实例中。

一句话收尾：

```text
Milvus 不是只存向量，它存的是带 schema 的向量数据记录；会设计 schema，才算真正开始会用 Milvus 做 RAG。
```

## 19. 下一节预告

第 34 节会学习：

```text
用同一批文档写入 Milvus 并做向量检索
```

下一节会开始写代码。

核心任务是：

1. 安装或确认 Milvus Python SDK。
2. 连接 `http://192.168.88.10:19530`。
3. 创建学习版 collection。
4. 按本节 schema 写入示例 chunks。
5. 做一次基础向量搜索。
6. 和 Qdrant 的查询结果做概念对比。

下一节需要打开 VMware Ubuntu，并保持 Milvus 容器运行。
