# 阶段 4 第 31 节：Milvus 是什么，和 Qdrant 有什么区别

## 0. 本节定位

前面我们已经用 Qdrant 跑通了一条企业知识库 RAG 主线：

```text
文档
-> 加载和清洗
-> chunk 切分
-> embedding
-> 写入 Qdrant
-> top_k 检索
-> payload filter 权限过滤
-> score_threshold 拦截低相关资料
-> rerank
-> 安全检查
-> 模型回答
-> 引用来源
```

到这里，你已经不是只听过 RAG，而是做过一个学习版 RAG 的核心链路。

现在补 Milvus，不是为了马上把项目换成 Milvus，也不是为了追新工具。真正目的有三个：

1. 你要知道向量数据库不是只有 Qdrant。
2. 你要能解释 Qdrant 和 Milvus 在概念、数据模型、部署、索引、过滤、工程复杂度上的差异。
3. 你以后做项目选型、面试讲架构、和别人讨论 RAG 时，不能只说“我会用某个库”，而要能说清楚“为什么选它”。

本节是概念对比课，重点是理解，不做安装。

## 1. 本节学习目标

学完本节，你要能做到：

1. 用自己的话解释 Milvus 是什么。
2. 用自己的话解释 Qdrant 是什么。
3. 说清楚“向量数据库”和“普通数据库”的区别。
4. 把 Qdrant 的 `collection / point / vector / payload` 和 Milvus 的 `collection / schema / field / entity / vector field / scalar field` 对应起来。
5. 明白 Qdrant 更像“point + payload”的模型，Milvus 更强调“schema + field + entity”的模型。
6. 明白为什么我们先用 Qdrant 学 RAG 主线。
7. 明白什么情况下企业项目可能会考虑 Milvus。
8. 能解释索引不是“数据本身”，而是为了加速搜索额外建立的数据结构。
9. 能解释 metadata、payload、scalar field、filter 在 RAG 里的共同作用。
10. 能给出一个初步的向量数据库选型判断框架。

## 2. 本节不学什么

这一节先不做这些事：

1. 不安装 Milvus。
2. 不启动 Milvus Docker。
3. 不修改 `projects/ai-service` 的向量库实现。
4. 不把现有 Qdrant 代码迁移到 Milvus。
5. 不做性能压测。
6. 不比较所有向量数据库。
7. 不追求背诵每个配置项。

第 32 节才会进入“本地 Docker 启动 Milvus Standalone”。

第 33-35 节会逐步讲 Milvus 的核心概念、入库检索、metadata/scalar filter 和索引。

第 36 节会在你真的操作过 Milvus 之后，再做一次更完整的 Qdrant vs Milvus 选型复盘。

所以第 31 节更像“先建立地图”。

## 3. 先给结论

如果只用一句话说：

```text
Qdrant 和 Milvus 都是向量数据库，都能支撑 RAG 检索。
Qdrant 对初学者和中小型 RAG 项目更直观，point + payload 模型上手快。
Milvus 更强调 schema、field、entity、index 和大规模/分布式能力，概念更多，工程感更重。
```

再换成更接近工程选型的话：

```text
学习 RAG 主线、快速搭建、单机或中小规模服务，Qdrant 很适合。
如果团队已经有更强的基础设施能力，数据规模大，字段模型复杂，需要更完整的 schema 管理和大规模部署能力，可以进一步评估 Milvus。
```

注意：这不是说 Qdrant 不能做生产，也不是说 Milvus 一定更高级。选型永远要看业务、团队、数据规模、运维能力、生态、成本和风险。

## 4. 官方资料核对

本节参考了官方文档，查阅日期：2026-07-17。

### 4.1 Milvus 官方资料

- Milvus Overview: https://milvus.io/docs/overview.md
- Milvus Collection Explained: https://milvus.io/docs/manage-collections.md
- Milvus Schema Explained: https://milvus.io/docs/schema.md
- Milvus Index Explained: https://milvus.io/docs/index-explained.md
- Milvus Docker Compose 安装: https://milvus.io/docs/install_standalone-docker-compose.md

### 4.2 Qdrant 官方资料

- Qdrant Overview: https://qdrant.tech/documentation/overview/
- Qdrant Collections: https://qdrant.tech/documentation/manage-data/collections/
- Qdrant Points: https://qdrant.tech/documentation/manage-data/points/
- Qdrant Filtering: https://qdrant.tech/documentation/search/filtering/
- Qdrant Local Quickstart: https://qdrant.tech/documentation/quickstart/

这些链接不是让你一次性全看完，而是作为以后深入查证的“源头资料”。你现在先吃透本节笔记。

## 5. 基础知识铺垫

### 5.1 普通数据库主要擅长什么

你已经有 Java 基础，所以可以先用普通后端系统来理解。

在一个传统业务系统里，我们经常用 MySQL、PostgreSQL 这类关系型数据库保存结构化数据。

比如订单表：

| id | user_id | status | amount | created_at |
| --- | --- | --- | --- | --- |
| 1001 | U001 | paid | 199.00 | 2026-07-01 |
| 1002 | U002 | refunded | 88.00 | 2026-07-03 |

这种数据库最擅长的问题是：

```sql
select * from orders where status = 'paid';
```

也就是：

1. 字段明确。
2. 条件明确。
3. 精确匹配、范围查询、排序、聚合。
4. 数据有稳定 schema。

普通数据库问的是：

```text
哪一行的 status 等于 paid？
哪一行的 amount 大于 100？
哪一行的 user_id 等于 U001？
```

它擅长“精确条件查询”。

### 5.2 RAG 里的检索问题不一样

企业知识库里常见的是文档：

```text
用户申请退货后，如果是商品质量问题导致的退货，运费通常由商家承担。
如果是用户个人原因退货，运费通常由用户承担。
```

用户可能这样问：

```text
退货运费谁出？
```

也可能这样问：

```text
客户说东西坏了要退，邮费怎么算？
```

普通数据库如果只按关键词查，可能遇到问题：

1. 用户说“邮费”，文档写“运费”。
2. 用户说“东西坏了”，文档写“商品质量问题”。
3. 用户说“怎么算”，文档写“由谁承担”。
4. 用户的问题不一定包含文档原词。

这就是语义检索要解决的问题：

```text
不只看字面是否一样，还要看意思是否接近。
```

向量数据库保存的是 embedding 向量，让系统可以根据“语义距离”找相似内容。

### 5.3 embedding 是什么

embedding 是模型把文本变成一组数字。

例如：

```text
"退货运费谁出？"
-> [0.12, -0.08, 0.44, ...]
```

这一组数字不是人类手写规则，而是 embedding 模型学出来的语义表示。

在 RAG 里通常有两类 embedding：

| 类型 | 输入 | 用途 |
| --- | --- | --- |
| 文档 chunk embedding | 知识库里的每个 chunk | 入库时生成，长期保存 |
| query embedding | 用户问题 | 检索时生成，用来搜索相似 chunk |

向量数据库负责保存 chunk embedding，并在用户提问时找出最接近 query embedding 的 chunk。

### 5.4 向量数据库到底保存什么

一个 RAG chunk 入库后，通常不只保存向量。

我们项目里一个 chunk 大概有这些东西：

```text
chunk_id: refund_return_policy_chunk_0003
content: 商品质量问题导致退货时，运费通常由商家承担...
embedding: [0.13, 0.72, -0.31, ...]
metadata:
  source: refund-return-policy.md
  title: 退款退货规则
  section: 运费处理
  doc_type: policy
  business_domain: refund
  permission_group: customer_service
```

其中：

| 内容 | 作用 |
| --- | --- |
| `content` | 最后给模型看的原文 |
| `embedding` | 给向量数据库做相似度搜索 |
| `metadata` | 做权限过滤、引用来源、业务范围过滤、调试 |
| `chunk_id` | 唯一定位一个 chunk，支持更新和删除 |

所以向量数据库保存的不是“只有一串数字”，而是：

```text
向量 + 原文或原文引用 + 业务字段 + 唯一 ID
```

不同向量数据库只是给这些东西取了不同名字，并且约束方式不同。

### 5.5 为什么不能只用普通数据库存向量

理论上，你可以把向量数组存进普通数据库字段里。

比如：

```text
chunk_id = 1
vector = [0.1, 0.2, 0.3, ...]
content = "..."
```

但问题是：

1. 向量维度可能是 768、1024、1536、3072。
2. 文档 chunk 可能有几万、几十万、几百万。
3. 每次检索都要计算 query vector 和大量 chunk vector 的距离。
4. 精确全量计算成本很高。
5. 还要同时支持过滤、排序、删除、更新、批量写入。

向量数据库专门优化这些事：

1. 高维向量存储。
2. 向量索引。
3. 近似最近邻搜索。
4. metadata/filter 过滤。
5. 批量写入。
6. 数据更新、删除。
7. 分片、复制、持久化、备份。

### 5.6 什么是最近邻搜索

最近邻搜索的意思是：

```text
给我一个 query vector，帮我找出最接近它的几个 vector。
```

在 RAG 中：

```text
query vector = 用户问题的 embedding
数据库里的 vector = 知识库 chunk 的 embedding
最近的几个 vector = 最可能相关的知识片段
```

我们前面反复讲过 `top_k`。

`top_k=5` 的意思就是：

```text
返回最相似的前 5 个 chunk。
```

但这里有一个关键点：

```text
top_k 只表示返回数量，不保证返回内容一定正确。
```

所以后面才需要：

1. `score_threshold`
2. payload filter
3. hybrid search
4. rerank
5. 安全检查
6. 引用来源
7. 无资料拒答

### 5.7 什么是 ANN

ANN 是 Approximate Nearest Neighbor，近似最近邻。

直白理解：

```text
不一定逐个比较所有向量，而是用索引结构快速找到“很可能最接近”的向量。
```

为什么要“近似”？

因为当数据量很大时，精确比较所有向量太慢。

ANN 的核心取舍是：

| 目标 | 含义 |
| --- | --- |
| 更快 | 查询速度更高 |
| 更省 | CPU、内存、磁盘成本更可控 |
| 召回更好 | 尽量别漏掉真正相关内容 |
| 结果更稳定 | 同样输入尽量返回合理结果 |

索引策略就是围绕这些目标做权衡。

### 5.8 什么是索引

索引不是数据本身。

索引是为了更快查数据而建立的辅助结构。

普通数据库里，给 `user_id` 建索引，是为了更快查：

```sql
where user_id = 'U001'
```

向量数据库里，给 vector 建索引，是为了更快查：

```text
哪些 vector 和 query vector 最相似？
```

官方 Milvus 文档也强调：索引是建立在数据之上的额外结构，可以加速搜索，但会带来预处理时间、空间、内存和召回率取舍。

你需要记住：

```text
索引不是免费午餐。
```

索引会带来：

1. 写入后构建索引的成本。
2. 更多磁盘或内存占用。
3. 查询参数调优成本。
4. 召回率和速度之间的取舍。

### 5.9 metadata、payload、scalar field 是一类问题

我们前面在 Qdrant 里一直说 payload。

比如：

```json
{
  "source": "refund-return-policy.md",
  "business_domain": "refund",
  "permission_group": "customer_service"
}
```

在 Milvus 里，类似信息通常会被建成 scalar field，或者在动态字段里保存。

例如：

```text
source: VarChar
business_domain: VarChar
permission_group: VarChar
```

不同叫法背后的业务目的相同：

```text
让检索不只看语义相似，还要满足业务条件。
```

比如：

```text
只检索 customer_service 有权限看的文档。
只检索 refund 业务域的文档。
只检索 policy 类型的文档。
```

RAG 如果没有 metadata/filter，通常很难进入企业级使用。

### 5.10 向量数据库不是 RAG 的全部

很多初学者会把 RAG 简化成：

```text
RAG = embedding + vector database
```

这不准确。

更准确的是：

```text
RAG = 文档工程 + embedding + 向量库 + 检索策略 + prompt 约束 + 生成 + 引用 + 安全 + 评测 + 运维
```

向量数据库只是其中一层。

它很重要，但不能替代：

1. 文档清洗。
2. chunk 策略。
3. metadata 设计。
4. 权限过滤。
5. rerank。
6. 答案引用。
7. 无资料拒答。
8. prompt injection 防护。
9. 评测集。

所以不要把“换一个向量数据库”误解成“RAG 质量自动变好”。

## 6. 本节主题系统讲解

### 6.1 Milvus 是什么

Milvus 是一个开源向量数据库。

它的核心作用是：

```text
存储大量向量，并支持高效的相似度搜索。
```

在 RAG 里，Milvus 可以承担 vector store 的角色：

```text
chunk -> embedding -> Milvus
用户问题 -> query embedding -> Milvus search -> 返回相关 chunk
```

Milvus 官方文档强调它是高性能、可扩展的向量数据库，可以从本机环境扩展到大规模分布式系统。

你可以先把 Milvus 理解成：

```text
更强调 schema、field、entity、index、分布式扩展能力的向量数据库。
```

### 6.2 Qdrant 是什么

Qdrant 也是一个向量数据库。

在我们的项目中，Qdrant 已经承担了 vector store 的角色：

```text
RagChunk
-> EmbeddedChunk
-> Qdrant point
-> query_similar()
-> RetrievedChunk
```

Qdrant 的核心数据模型非常直观：

```text
collection 里面有很多 point
point 里面有 vector 和 payload
```

官方文档里，point 是 Qdrant 操作的中心实体，一个 point 由 vector 和可选 payload 组成。

你可以先把 Qdrant 理解成：

```text
更容易从 RAG chunk 映射到 point + payload 的向量数据库。
```

### 6.3 两者解决的是同一个大问题

Qdrant 和 Milvus 都不是大模型。

它们不负责：

1. 生成回答。
2. 理解用户意图。
3. 写 prompt。
4. 判断答案是否可信。
5. 自动修复文档质量。

它们主要负责：

1. 保存向量。
2. 保存向量旁边的业务字段。
3. 根据 query vector 找相似 vector。
4. 支持过滤条件。
5. 支持更新、删除、批量写入。
6. 支持索引和性能优化。

在 RAG 架构中，它们的位置是：

```text
用户问题
-> embedding 模型
-> 向量数据库检索
-> 返回候选 chunk
-> 后端做过滤、重排、安全检查
-> 大模型基于资料回答
```

### 6.4 最核心的概念对应表

先看最重要的映射。

| RAG 概念 | Qdrant 叫法 | Milvus 叫法 | 解释 |
| --- | --- | --- | --- |
| 知识库的一组 chunk | collection | collection | 一批可一起检索的数据 |
| 一个 chunk 的记录 | point | entity | 一条可被检索的数据记录 |
| chunk 的 embedding | vector | vector field | 用于相似度搜索的数字向量 |
| chunk_id | point id | primary key | 唯一标识一条记录 |
| metadata | payload | scalar field 或 dynamic field | 业务字段，用于过滤和展示 |
| 文本内容 | payload 里的 content | scalar field 里的 content | 最终给模型看的原文 |
| 向量索引 | vector index/HNSW 等 | index | 加速相似度搜索 |
| 过滤条件 | payload filter | scalar filter | 按权限、业务域、文档类型过滤 |

这张表很重要。

以后你看到不同向量数据库的文档，不要被名字吓住。先问：

```text
它的 collection 是什么？
一条记录叫什么？
向量字段放哪里？
metadata 放哪里？
怎么 filter？
怎么建 index？
怎么 upsert/delete？
```

这就是学习任何向量数据库的主线。

### 6.5 Qdrant 的数据模型：collection、point、vector、payload

Qdrant 的模型更贴近我们前面做的 RAG 代码。

一个 collection 可以理解成一组 point。

一个 point 大概长这样：

```json
{
  "id": "refund_return_policy_chunk_0003",
  "vector": [0.12, 0.23, -0.18],
  "payload": {
    "content": "商品质量问题导致退货时，运费通常由商家承担。",
    "source": "refund-return-policy.md",
    "title": "退款退货规则",
    "section": "运费处理",
    "doc_type": "policy",
    "business_domain": "refund",
    "permission_group": "customer_service"
  }
}
```

你看到这个结构，基本就能懂：

1. `id` 用来唯一定位。
2. `vector` 用来做相似度检索。
3. `payload.content` 用来给模型回答。
4. `payload.source/title/section` 用来做引用来源。
5. `payload.permission_group` 用来做权限过滤。
6. `payload.business_domain/doc_type` 用来做业务过滤。

这也是我们为什么先选 Qdrant 学 RAG。

它和 RAG chunk 的映射关系非常直接。

### 6.6 Milvus 的数据模型：collection、schema、field、entity

Milvus 的模型更像数据库表。

官方文档把 collection 描述成由固定列和变化行组成的二维表：

```text
每个字段是一列。
每条 entity 是一行。
```

如果用 Milvus 表达我们项目里的 chunk，可能会设计成：

| 字段名 | 字段类型 | 作用 |
| --- | --- | --- |
| `chunk_id` | primary key | 唯一标识 chunk |
| `content` | VarChar | chunk 原文 |
| `embedding` | FloatVector | chunk 向量 |
| `source` | VarChar | 来源文件 |
| `title` | VarChar | 文档标题 |
| `section` | VarChar | 所属章节 |
| `doc_type` | VarChar | 文档类型 |
| `business_domain` | VarChar | 业务域 |
| `permission_group` | VarChar | 权限组 |
| `chunk_index` | Int64 | chunk 顺序 |

这就是 Milvus 的 schema 思维：

```text
先定义 collection 里有哪些字段，每个字段是什么类型，然后再插入 entity。
```

这种方式更像你熟悉的 Java 后端数据库建模。

### 6.7 schema 是什么

schema 可以理解为“数据结构约定”。

在关系型数据库里：

```sql
create table orders (
  id bigint primary key,
  status varchar(32),
  amount decimal(10, 2)
);
```

这就是 schema。

在 Milvus 里：

```text
collection schema:
  chunk_id: primary key
  content: VarChar
  embedding: FloatVector(dim=1536)
  source: VarChar
  permission_group: VarChar
```

也是 schema。

schema 的好处：

1. 字段清晰。
2. 类型清晰。
3. 便于长期维护。
4. 便于团队协作。
5. 便于优化索引和查询。

schema 的代价：

1. 前期设计更重。
2. 字段变化要更谨慎。
3. 初学时概念更多。
4. 快速试验不如“随手塞 payload”直观。

### 6.8 Qdrant 有没有 schema

Qdrant 的 collection 创建时，必须定义 vector size 和 distance。

比如：

```text
vector size = 1536
distance = Cosine
```

这部分是明确约束。

但 payload 本身更灵活，你可以往 payload 里放 JSON 风格的数据。

这让 Qdrant 对初学者更友好：

```text
先把 RAG 跑通，再逐步规范 payload 字段。
```

但灵活也有代价：

1. 字段名写错可能不容易第一时间发现。
2. 同一个字段可能出现不同类型。
3. 团队协作时需要自己维护 metadata 规范。
4. 高频过滤字段需要考虑 payload index。

所以我们前面第 14 节专门做了 metadata 标准化，就是为了弥补“字段自由”带来的工程风险。

### 6.9 Milvus 的 entity 和 Qdrant 的 point 怎么理解

你可以这样对应：

```text
Qdrant point ~= Milvus entity ~= 我们项目里的一个 RagChunk 入库记录
```

但是它们的表达方式不同。

Qdrant point 更像：

```json
{
  "id": "...",
  "vector": [...],
  "payload": {...}
}
```

Milvus entity 更像一行表数据：

```text
chunk_id = "..."
content = "..."
embedding = [...]
source = "..."
permission_group = "customer_service"
```

你熟悉 Java 和数据库后，可以这样记：

```text
Qdrant point 更像一个文档对象。
Milvus entity 更像一行结构化记录。
```

### 6.10 payload 和 scalar field 的区别

Qdrant payload：

```json
{
  "source": "refund-return-policy.md",
  "permission_group": "customer_service"
}
```

Milvus scalar field：

```text
source: VarChar
permission_group: VarChar
```

共同点：

1. 都不是向量。
2. 都描述业务属性。
3. 都可以辅助过滤。
4. 都可以用于返回结果展示。
5. 都可以用于引用来源。

差异：

| 对比项 | Qdrant payload | Milvus scalar field |
| --- | --- | --- |
| 风格 | JSON payload | schema field |
| 初学直观性 | 更直观 | 更接近数据库建模 |
| 字段约束 | 更灵活 | 更明确 |
| 字段变更 | 相对轻 | 需要考虑 schema |
| 团队规范 | 需要自己管好 metadata 约定 | schema 本身就是约束 |

### 6.11 filter 为什么非常关键

只做向量相似度会有风险。

比如用户是普通客服，只能看客服知识库。

如果不做权限过滤，向量数据库可能检索出内部管理员文档。

所以检索条件不能只有：

```text
找最相似的 chunk
```

还要加上：

```text
只能找当前用户有权限看的 chunk
```

在 Qdrant 里，我们用 payload filter。

在 Milvus 里，会用 scalar filter 或表达式过滤。

业务上它们解决的是同一个问题：

```text
语义相关 + 权限允许 + 业务范围匹配
```

### 6.12 为什么“先过滤再向量检索”和“向量检索后过滤”有差异

你需要理解一个工程细节。

假设有 100 万个 chunk。

其中：

1. 只有 2 万个属于 `customer_service` 权限组。
2. 用户只能看这 2 万个。
3. 用户问“退款多久到账？”

如果系统先从 100 万个里找 top_k，再过滤权限，可能出现：

```text
top_k 里大部分是用户没权限看的内容。
过滤后剩下 0 条或很少。
```

如果系统能把 filter 和向量检索结合起来，就更容易在允许范围里找相关内容。

所以企业 RAG 里，filter 不是可有可无。

你在选向量数据库时，要关注：

1. filter 能不能和 vector search 一起用。
2. filter 字段有没有索引。
3. 高频过滤字段的性能怎么样。
4. 多租户或权限隔离怎么设计。

### 6.13 Qdrant 的 payload index

Qdrant 官方文档提到 payload index 可以帮助某个 payload 属性更高效过滤。

这类似关系型数据库里给常用查询列建索引。

比如我们经常按这些字段过滤：

```text
permission_group
business_domain
doc_type
source
```

如果数据量变大，就需要考虑给这些字段建立 payload index。

否则每次过滤都可能更吃资源。

你现在不用马上写代码，但要知道：

```text
metadata 字段不是只为了展示，也是性能设计的一部分。
```

### 6.14 Milvus 的 scalar field 和索引

Milvus 里，非向量字段通常是 scalar field。

例如：

```text
permission_group
business_domain
doc_type
source
```

这些字段可以配合向量搜索做过滤。

如果某个字段频繁参与过滤，也需要考虑索引和查询设计。

这和普通数据库很像：

```text
字段设计不好，查询就难写。
索引设计不好，查询就慢。
```

向量数据库没有让数据库设计消失，只是让数据库设计多了“向量字段”和“相似度搜索”这一层。

### 6.15 向量维度在两个数据库里都很重要

无论 Qdrant 还是 Milvus，同一个向量字段都要知道维度。

例如 embedding 模型输出 1536 维：

```text
vector dimension = 1536
```

如果 collection 建成 1536 维，你就不能塞 1024 维向量。

这就是我们第 24 节讲过的：

```text
embedding 模型选择会影响向量库 collection/schema 设计。
```

换 embedding 模型可能不是改一个配置那么简单。

可能要：

1. 新建 collection。
2. 全量重新 embedding。
3. 重新入库。
4. 重新调 score_threshold。
5. 重新做评测。

### 6.16 distance metric 也不能乱选

常见相似度或距离：

1. Cosine
2. Dot product
3. Euclidean

Qdrant collection 创建时要指定 distance。

Milvus vector field/index/search 也要关注 metric type。

这里不用背细节，但要记住：

```text
distance metric 要和 embedding 模型、向量归一化方式、业务评测结果一起看。
```

不能因为某篇文章说 Cosine 常用，就永远无脑选 Cosine。

学习阶段用 Cosine 很合理。

生产阶段要基于 embedding 模型说明和评测集验证。

### 6.17 为什么我们先用 Qdrant

我们前面选择 Qdrant，不是因为 Milvus 不重要。

主要原因是：

1. Qdrant 本地启动简单。
2. HTTP API 直观。
3. collection/point/vector/payload 概念少。
4. 和 RAG chunk 映射非常直接。
5. 更适合初学者把 RAG 主线跑通。
6. 你可以更快看到“文档如何变成可检索知识”。
7. 我们重点是先学会 RAG，而不是先陷入复杂部署。

这符合你的学习目标：

```text
先真正理解一条链路，再扩展到更多工具。
```

### 6.18 为什么现在补 Milvus

现在补 Milvus，是因为你已经有了 Qdrant 实战经验。

如果一开始就讲 Milvus，你可能会被这些概念压住：

1. collection
2. schema
3. field
4. entity
5. primary key
6. vector field
7. scalar field
8. index
9. standalone
10. cluster
11. object storage
12. metadata store

但现在不一样。

你已经知道：

1. chunk 是什么。
2. embedding 是什么。
3. vector store 是什么。
4. payload filter 是什么。
5. score_threshold 是什么。
6. 文档更新为什么要删除旧 chunk。
7. RAG 安全为什么要做权限检查。

所以现在看 Milvus，就不是死记概念，而是做映射：

```text
原来 Qdrant 的 point，在 Milvus 里更像 entity。
原来 Qdrant 的 payload，在 Milvus 里可以拆成 scalar fields。
原来 Qdrant collection 的 vector size，在 Milvus 里会体现在 vector field dim。
```

这种学习顺序更扎实。

### 6.19 Milvus 的部署模式为什么会让人感觉更重

Milvus 支持从轻量使用到更大规模部署。

常见形态包括：

1. Milvus Lite。
2. Milvus Standalone。
3. Milvus Cluster。
4. Zilliz Cloud。

你现在先知道这几个名字就够。

第 32 节我们会学 Milvus Standalone，因为它适合本地学习。

Milvus Cluster 涉及更多组件和运维知识，不适合作为你第一次接触 Milvus 的入口。

你需要建立一个判断：

```text
向量数据库能力越强，不代表学习入口越简单。
```

工具的复杂度如果超出当前学习阶段，会干扰你理解主线。

### 6.20 Qdrant 的部署为什么适合作为学习入口

我们之前在 VMware Ubuntu Docker 里启动 Qdrant。

你已经验证过：

```text
Docker 容器运行 Qdrant
Windows 浏览器访问 http://192.168.88.10:6333
ai-service 通过 QDRANT_URL 访问它
```

这个链路很清楚：

```text
Windows 项目
-> VMware Ubuntu IP
-> Docker 容器端口映射
-> Qdrant HTTP API
```

对学习来说，这已经足够建立“向量数据库是独立服务”的概念。

所以 Milvus 后面也会沿用这个学习方式：

```text
先本地 Standalone 跑起来，再学习核心概念。
```

## 7. 从我们项目角度看两者差异

### 7.1 目前项目怎么依赖 Qdrant

我们项目里和 Qdrant 直接相关的主要模块是：

```text
projects/ai-service/app/rag/vector_store.py
```

它承担的职责是：

1. 创建或确认 collection。
2. 把 `EmbeddedChunk` 写成 Qdrant point。
3. 根据 query vector 做相似度查询。
4. 传入 payload filter。
5. 传入 score_threshold。
6. 删除旧 points。
7. 把 Qdrant 返回结果转成项目内部的 `RetrievedChunk`。

这说明一个重要工程原则：

```text
业务代码不应该到处直接写 Qdrant API。
```

我们把 Qdrant 封装在 vector store 层，是为了以后替换或对比 Milvus 时，不让全项目到处改。

### 7.2 如果以后接 Milvus，最理想改哪里

理想情况不是把全项目推倒重来，而是新增一个 Milvus 版本的 vector store。

概念上可能是：

```text
QdrantVectorStore
MilvusVectorStore
```

它们都对上层暴露类似能力：

```text
upsert_chunks(...)
query_similar(...)
delete_by_source(...)
```

上层 RAG 服务不需要关心底层到底是 Qdrant 还是 Milvus。

这就是接口隔离思想。

虽然我们现在还没做抽象接口，但你要先建立这个意识：

```text
向量数据库是基础设施，不应该污染业务主流程。
```

### 7.3 我们的 `RagChunk` 映射到 Qdrant

现在的思路是：

```text
RagChunk.chunk_id -> Qdrant point id
RagChunk.content -> Qdrant payload.content
RagChunk.metadata -> Qdrant payload
embedding vector -> Qdrant vector
```

这很自然。

所以你看 Qdrant point，会觉得它像：

```text
一个 chunk 对象序列化后的结果。
```

### 7.4 同一个 `RagChunk` 映射到 Milvus

如果换成 Milvus，思路会更像：

```text
RagChunk.chunk_id -> primary key field
RagChunk.content -> VarChar field
embedding vector -> FloatVector field
metadata.source -> VarChar field
metadata.title -> VarChar field
metadata.section -> VarChar field
metadata.doc_type -> VarChar field
metadata.business_domain -> VarChar field
metadata.permission_group -> VarChar field
metadata.chunk_index -> Int64 field
```

也就是把 metadata 里常用字段拆成更明确的字段。

这样做的好处是：

1. 字段类型清楚。
2. 过滤字段清楚。
3. 团队协作更明确。
4. 后续评估索引更有基础。

代价是：

1. schema 设计要先想清楚。
2. 字段变化成本更高。
3. 初始代码会多一些。

### 7.5 Qdrant 更像“先跑通，再规范”

学习阶段：

```text
point.payload 里先保存必要 metadata。
```

然后随着课程推进，我们逐步规范：

1. 第 14 节 metadata 设计。
2. 第 16 节 payload filter。
3. 第 23 节按 source 删除和重新入库。
4. 第 28 节权限和敏感信息安全检查。

这种路线适合学习，因为你每一节都能看到一个具体问题。

### 7.6 Milvus 更像“先建模，再使用”

Milvus 更强调：

```text
先设计 collection schema，再插入 entity，再建 index，再 search。
```

这和 Java 后端做数据库表设计很像。

如果你已经理解了关系型数据库建模，Milvus 的 schema 并不难。

真正容易混乱的是：

```text
它既像数据库表，又有向量字段，又有向量索引，又有相似度搜索。
```

所以我们后面会拆开讲：

1. 第 32 节只启动。
2. 第 33 节只讲核心概念。
3. 第 34 节只做同一批文档写入和检索。
4. 第 35 节只讲 scalar filter 和索引基础。

## 8. 选型对比

### 8.1 学习难度

| 对比项 | Qdrant | Milvus |
| --- | --- | --- |
| 初学入口 | 更简单 | 概念更多 |
| 本地启动 | 较轻 | Standalone 可学，但整体概念更重 |
| 数据模型 | point + payload 直观 | schema + field + entity 更像数据库 |
| 和 RAG chunk 映射 | 非常直接 | 需要先设计字段 |

结论：

```text
如果目标是先学懂 RAG 主线，Qdrant 更适合作为第一站。
```

### 8.2 数据建模方式

| 对比项 | Qdrant | Milvus |
| --- | --- | --- |
| 记录单位 | point | entity |
| 向量字段 | point vector，可有 named vectors | vector field |
| metadata | payload | scalar field 或 dynamic field |
| 字段约束 | payload 更灵活 | schema 更明确 |
| 适合心智模型 | 文档对象 | 数据表 |

结论：

```text
Qdrant 更像文档对象存储加向量搜索。
Milvus 更像带向量字段的结构化搜索数据库。
```

### 8.3 过滤能力

两者都支持过滤。

Qdrant：

```text
payload filter
```

Milvus：

```text
scalar filter / 表达式过滤
```

业务上都可以做：

1. 权限过滤。
2. 文档类型过滤。
3. 业务域过滤。
4. 来源过滤。
5. 时间范围过滤。

选型时不能只问“能不能 filter”，还要问：

1. 高频 filter 字段怎么建索引？
2. filter 和向量检索结合时性能如何？
3. 多条件过滤是否稳定？
4. 多租户隔离怎么做？
5. 权限字段如何避免漏过滤？

### 8.4 索引和性能

两者都支持向量索引。

你现在不用比较每种索引算法的细节。

先掌握这个原则：

```text
索引用来加速搜索，但会带来构建成本、存储成本、内存成本和召回率取舍。
```

如果数据很小：

```text
索引差异可能不是最重要的问题。
```

如果数据很大：

```text
索引策略、过滤字段、分片、缓存、磁盘/内存配置、写入方式都会影响系统表现。
```

### 8.5 生态和集成

两者都有 Python SDK，也都可以接 LangChain。

对我们的学习来说：

```text
SDK 是否能用不是最大问题。
最大问题是你能否理解 RAG 数据流和工程边界。
```

换句话说：

```text
会调用 SDK 不等于会做 RAG。
```

你要能解释：

1. 为什么这样设计 chunk。
2. 为什么保存这些 metadata。
3. 为什么需要 filter。
4. 为什么需要 score_threshold。
5. 为什么要 rerank。
6. 为什么要做安全检查。
7. 为什么要评测检索质量。

这些能力比背某个 SDK 方法名重要。

### 8.6 部署和运维

Qdrant 的学习部署较轻。

Milvus 的完整生态和扩展能力更强，但也意味着你要面对更多部署模式和组件概念。

对于个人学习：

```text
越简单越容易专注在 RAG 本质。
```

对于企业生产：

```text
越大规模越需要关注可扩展、高可用、备份、监控、成本、团队运维能力。
```

所以选型不能脱离团队实际。

### 8.7 什么时候更倾向 Qdrant

以下场景可以优先考虑 Qdrant：

1. 想快速跑通 RAG。
2. 团队刚开始做向量检索。
3. 数据规模中小。
4. 希望本地开发体验简单。
5. metadata 以 JSON payload 形式表达更自然。
6. 项目需要快速试错。
7. 运维资源有限。
8. 学习阶段想少一点基础设施复杂度。

对你当前阶段来说，Qdrant 是合理选择。

### 8.8 什么时候更应该评估 Milvus

以下场景可以进一步评估 Milvus：

1. 数据规模很大。
2. 团队有更强的基础设施和运维能力。
3. 需要更明确的 schema 建模。
4. 需要更系统地管理字段、向量字段、索引和搜索。
5. 需要从本机原型逐步考虑更大规模部署。
6. 团队已有 Milvus 或 Zilliz Cloud 经验。
7. 公司技术栈或平台要求使用 Milvus。
8. 需要严肃评估性能、扩展性和长期维护。

注意“评估”不等于“必选”。

任何选型都应该做小规模验证。

## 9. 选型时真正要问的问题

### 9.1 不要只问“哪个更好”

“Qdrant 和 Milvus 哪个更好”这个问题太粗。

更专业的问法是：

```text
在我们的数据规模、查询量、权限模型、团队能力和部署环境下，哪个更合适？
```

技术选型没有脱离场景的绝对答案。

### 9.2 数据规模问题

你要问：

1. 现在有多少文档？
2. 切成多少 chunk？
3. 未来半年会增长到多少？
4. 每个 chunk 的向量维度是多少？
5. 每天新增多少文档？
6. 是否需要频繁更新和删除？

如果只是几千到几十万 chunk，很多方案都能跑。

如果是上亿甚至更大规模，就必须严肃评估分布式、索引、存储、成本和运维。

### 9.3 查询压力问题

你要问：

1. 每秒多少次检索？
2. 高峰期多少 QPS？
3. 每次 top_k 多大？
4. 是否要混合检索？
5. 是否要 rerank？
6. 是否要多路召回？
7. 响应时间要求是多少？

RAG 慢不一定是向量数据库慢。

可能慢在：

1. embedding API。
2. rerank。
3. 大模型生成。
4. 网络。
5. filter 字段没有优化。
6. 返回 payload 太大。

所以性能分析要看整条链路。

### 9.4 权限模型问题

企业 RAG 必须问：

1. 文档是否分部门？
2. 用户是否分角色？
3. 是否有租户隔离？
4. 是否有内部文档和外部文档？
5. 是否要按地区、业务线、数据等级过滤？
6. 权限变化后，旧向量如何处理？

如果权限模型复杂，metadata/scalar field 设计就非常重要。

向量数据库选型也必须考虑 filter 能力和性能。

### 9.5 更新和删除问题

知识库不是只新增。

你要问：

1. 文档更新后旧 chunk 怎么删除？
2. chunk_id 是否稳定？
3. 删除是按 id 还是按 source？
4. 是否支持批量删除？
5. 删除后索引怎么维护？
6. 是否需要软删除？
7. 是否需要版本号？

我们前面第 23 节已经做过这个主题。

换 Milvus 时，也必须重新考虑对应实现。

### 9.6 运维能力问题

你要问：

1. 谁来部署？
2. 谁来监控？
3. 谁来备份？
4. 谁来升级？
5. 出问题谁排查？
6. 是否能接受云服务？
7. 是否必须私有化？
8. 是否有 Kubernetes 能力？

很多技术选型失败，不是工具本身不行，而是团队无法承担它的运维复杂度。

### 9.7 成本问题

向量数据库成本不只是机器钱。

还包括：

1. embedding 成本。
2. 存储成本。
3. 内存成本。
4. CPU/GPU 成本。
5. 网络成本。
6. 运维人力成本。
7. 迁移成本。
8. 学习成本。

如果一个工具能力很强，但团队不会运维，成本可能反而更高。

## 10. 常见误区

### 10.1 误区一：Milvus 比 Qdrant 高级，所以一定要换

不对。

工具不能只按“看起来更强”来选。

如果当前项目用 Qdrant 已经能满足：

1. 数据量。
2. 查询速度。
3. 权限过滤。
4. 更新删除。
5. 稳定性。
6. 运维成本。

那就没有必要为了“更高级”而迁移。

迁移本身有风险。

### 10.2 误区二：Qdrant 简单，所以不适合生产

也不对。

简单上手不等于不能生产。

关键看：

1. 你的数据规模。
2. 你的 SLA。
3. 你的部署方式。
4. 你的监控备份。
5. 你的团队经验。
6. 你的评测结果。

“简单”在很多业务里反而是优点。

### 10.3 误区三：向量数据库选好了，RAG 就好了

不对。

RAG 质量通常更受这些因素影响：

1. 文档质量。
2. chunk 切分。
3. metadata 设计。
4. embedding 模型。
5. 检索参数。
6. hybrid search。
7. rerank。
8. prompt 约束。
9. 引用来源。
10. 评测集。

向量数据库很重要，但不是全部。

### 10.4 误区四：只看 benchmark 就能选型

benchmark 有参考价值，但不能替代业务验证。

原因是：

1. benchmark 数据集可能和你的业务不同。
2. 查询模式可能不同。
3. filter 条件可能不同。
4. payload 大小可能不同。
5. top_k 和并发可能不同。
6. 部署硬件可能不同。

你最终要用自己的数据做小规模验证。

### 10.5 误区五：metadata 随便存就行

不对。

metadata 决定：

1. 能不能做权限过滤。
2. 能不能显示引用来源。
3. 能不能按业务域检索。
4. 能不能删除和重新入库。
5. 能不能做审计。
6. 能不能排查坏答案来源。

metadata 是 RAG 工程核心，不是附属品。

## 11. 面试和表达方式

### 11.1 如果别人问：Milvus 是什么

你可以这样回答：

```text
Milvus 是一个开源向量数据库，主要用于存储 embedding 向量并做高效相似度搜索。在 RAG 系统里，它通常作为 vector store，保存文档 chunk 的向量和相关字段。Milvus 更强调 collection schema、vector field、scalar field、entity 和 index，适合进一步评估大规模向量检索和更结构化的数据建模场景。
```

### 11.2 如果别人问：Qdrant 是什么

你可以这样回答：

```text
Qdrant 是一个向量数据库，核心数据模型是 collection 里面保存 point，每个 point 包含 vector 和 payload。RAG 里可以把每个文档 chunk 存成一个 point，vector 用于相似度搜索，payload 保存 content、source、permission_group 等 metadata，用于回答、引用和过滤。
```

### 11.3 如果别人问：你为什么先用 Qdrant

你可以这样回答：

```text
因为当前阶段重点是先跑通 RAG 主线。Qdrant 的 collection、point、vector、payload 模型和文档 chunk 的映射非常直接，本地 Docker 启动也比较简单，适合先把加载、切分、embedding、入库、检索、filter、score_threshold、rerank、引用和安全检查这些 RAG 核心环节学扎实。等主线稳定后，再补 Milvus 做选型对比。
```

### 11.4 如果别人问：什么时候考虑 Milvus

你可以这样回答：

```text
如果数据规模变大，团队需要更明确的 schema 建模、更系统的字段管理、更复杂的索引和部署能力，或者团队已有 Milvus/Zilliz 生态经验，就应该评估 Milvus。但我不会只因为它看起来更强就迁移，会基于业务数据量、查询模式、权限过滤、运维能力、成本和评测结果做验证。
```

### 11.5 如果别人问：payload 和 scalar field 有什么区别

你可以这样回答：

```text
在 RAG 里它们承担的业务角色类似，都是保存非向量的 metadata，比如 source、doc_type、business_domain、permission_group。Qdrant 里通常叫 payload，形式更像 JSON；Milvus 里通常会建成 scalar field，更强调 schema 和字段类型。它们都可以用于过滤、引用来源和结果展示。
```

### 11.6 如果别人问：向量数据库索引是什么

你可以这样回答：

```text
索引是建立在向量数据之上的辅助结构，用来加速相似度搜索。它不是数据本身。索引能提升查询速度，但会增加构建时间、存储或内存成本，并且不同索引和参数会影响召回率，所以需要结合数据规模、查询模式和评测结果调优。
```

## 12. 本节和后续课程的关系

第 31 节是概念地图。

后面几节安排是：

| 后续节 | 主题 | 重点 |
| --- | --- | --- |
| 第 32 节 | 本地 Docker 启动 Milvus Standalone | 先让 Milvus 跑起来 |
| 第 33 节 | Milvus 核心概念 | collection、schema、field、entity、index |
| 第 34 节 | 同一批文档写入 Milvus 并检索 | 用项目文档走一遍 Milvus 入库和搜索 |
| 第 35 节 | Milvus metadata/scalar filter 和索引基础 | 对应 Qdrant payload filter 和索引 |
| 第 36 节 | Qdrant vs Milvus 选型复盘 | 基于两边实操再做更完整判断 |

你可以把第 31 节看成：

```text
先学会看地图，再开始走 Milvus 这条路。
```

## 13. 本节最小完整理解图

```text
RAG chunk
  |
  | content
  | embedding
  | metadata
  v

Qdrant:
  collection
    point
      id
      vector
      payload

Milvus:
  collection
    schema
      primary key field
      vector field
      scalar fields
    entity
      field values

共同目标:
  根据 query vector 找相似 chunk
  同时支持 metadata/filter
  最终把可信资料交给模型回答
```

## 14. 学习时你应该怎么记

不要死记所有术语。

你按这五个问题记：

### 14.1 一条数据叫什么

Qdrant：

```text
point
```

Milvus：

```text
entity
```

### 14.2 向量放哪里

Qdrant：

```text
point.vector
```

Milvus：

```text
vector field
```

### 14.3 metadata 放哪里

Qdrant：

```text
payload
```

Milvus：

```text
scalar fields 或 dynamic field
```

### 14.4 唯一 ID 放哪里

Qdrant：

```text
point id
```

Milvus：

```text
primary key field
```

### 14.5 怎么控制检索范围

Qdrant：

```text
payload filter
```

Milvus：

```text
scalar filter / 表达式过滤
```

这五个问题能回答出来，你就不会被术语绕晕。

## 15. 本节没有改代码的原因

本节没有新增或修改运行代码。

原因：

1. 第 31 节目标是建立 Milvus 和 Qdrant 的概念映射。
2. 现在直接写 Milvus 代码会把“选型理解”和“安装接入细节”混在一起。
3. 后续第 32 节会先启动 Milvus。
4. 第 34 节才适合写入同一批文档并做检索。

这不是偷懒，而是学习顺序的控制：

```text
先理解为什么，再学习怎么做。
```

## 16. 本节练习

### 练习 1：概念配对

请把下面概念配对：

| RAG 概念 | Qdrant | Milvus |
| --- | --- | --- |
| 一批可检索数据 | ? | ? |
| 一条 chunk 记录 | ? | ? |
| 非向量业务字段 | ? | ? |
| 唯一 ID | ? | ? |
| 向量字段 | ? | ? |

### 练习 2：判断题

判断下面说法对不对，并说明原因。

1. Qdrant 简单，所以不能用于生产。
2. Milvus 概念更多，所以任何 RAG 项目都应该优先选 Milvus。
3. payload/scalar field 主要用于保存业务字段，可以支持权限过滤和引用来源。
4. 向量数据库选好了，RAG 的回答质量就一定好了。
5. embedding 模型维度变化，可能需要重建 collection 或 schema 并重新入库。

### 练习 3：用自己的话解释

请用 3-5 句话解释：

```text
为什么我们先用 Qdrant 学 RAG，再补 Milvus？
```

### 练习 4：项目映射

假设我们的 `RagChunk` 有：

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
```

请分别说明这些字段在 Qdrant 和 Milvus 里可能怎么保存。

### 练习 5：选型思考

下面两个场景分别更适合先评估哪个？

场景 A：

```text
个人学习项目，几百到几千个 chunk，主要目标是理解 RAG 主线，本地 Docker 跑起来即可。
```

场景 B：

```text
企业知识库，未来可能有上亿向量，团队有基础设施能力，需要更明确的 schema、索引和大规模部署评估。
```

## 17. 练习参考答案

### 练习 1 参考答案

| RAG 概念 | Qdrant | Milvus |
| --- | --- | --- |
| 一批可检索数据 | collection | collection |
| 一条 chunk 记录 | point | entity |
| 非向量业务字段 | payload | scalar field 或 dynamic field |
| 唯一 ID | point id | primary key field |
| 向量字段 | vector | vector field |

### 练习 2 参考答案

1. 不对。简单上手不等于不能生产，是否适合生产要看数据规模、稳定性要求、部署方式、监控备份、团队经验和评测结果。
2. 不对。Milvus 概念更多、扩展能力强，但不代表任何项目都要优先选它。选型要看业务场景和团队能力。
3. 对。payload/scalar field 保存 source、doc_type、business_domain、permission_group 等 metadata，可以支持过滤、引用、展示和调试。
4. 不对。RAG 质量还受文档质量、chunk 策略、embedding 模型、metadata、hybrid search、rerank、prompt、安全和评测影响。
5. 对。向量维度和 collection/schema 强相关，换 embedding 模型后可能需要重新生成向量、重新入库并重新调参。

### 练习 3 参考答案

我们先用 Qdrant，是因为它的 collection、point、vector、payload 模型和 RAG chunk 映射非常直接，适合先跑通加载、切分、embedding、入库、检索、过滤、回答和引用这条主线。Milvus 更强调 schema、field、entity、index 和部署模式，概念更多，如果一开始就讲，容易让学习重点偏到基础设施细节。等 Qdrant 主线做完后再补 Milvus，就可以用已有经验做概念映射，理解会更扎实。

### 练习 4 参考答案

Qdrant 里可以这样保存：

| 字段 | Qdrant 位置 |
| --- | --- |
| `chunk_id` | point id，也可在 payload 里保留 |
| `content` | payload.content |
| `embedding` | point.vector |
| `source` | payload.source |
| `title` | payload.title |
| `section` | payload.section |
| `doc_type` | payload.doc_type |
| `business_domain` | payload.business_domain |
| `permission_group` | payload.permission_group |

Milvus 里可以这样保存：

| 字段 | Milvus 位置 |
| --- | --- |
| `chunk_id` | primary key field |
| `content` | VarChar scalar field |
| `embedding` | FloatVector vector field |
| `source` | VarChar scalar field |
| `title` | VarChar scalar field |
| `section` | VarChar scalar field |
| `doc_type` | VarChar scalar field |
| `business_domain` | VarChar scalar field |
| `permission_group` | VarChar scalar field |

### 练习 5 参考答案

场景 A 更适合先用 Qdrant。

理由：目标是学习和快速跑通主线，数据量小，本地 Docker 即可，Qdrant 的 point + payload 模型更直观。

场景 B 应该认真评估 Milvus，也可以同时做 Qdrant 对照压测。

理由：数据规模大、schema 和索引要求更强、团队有基础设施能力，需要更严肃地评估扩展性、运维成本、过滤性能和长期维护。

## 18. 自测题

### 自测 1

Milvus 和 Qdrant 是大模型吗？

### 自测 2

Qdrant 的 point 通常由哪几部分组成？

### 自测 3

Milvus 的 collection schema 至少通常要考虑哪几类字段？

### 自测 4

payload filter 或 scalar filter 在企业 RAG 中为什么重要？

### 自测 5

为什么说索引不是免费午餐？

### 自测 6

如果 embedding 模型从 1536 维换成 1024 维，为什么不能简单把新向量塞进旧 collection？

### 自测 7

为什么说“向量数据库选好了，RAG 就好了”是误解？

### 自测 8

你怎么向别人解释“Qdrant point”和“Milvus entity”的关系？

### 自测 9

什么情况下你会建议先用 Qdrant？

### 自测 10

什么情况下你会建议评估 Milvus？

## 19. 自测题参考答案

### 自测 1 参考答案

不是。Milvus 和 Qdrant 是向量数据库，负责保存向量、做相似度搜索和过滤，不负责生成回答。生成回答通常由大模型完成。

### 自测 2 参考答案

Qdrant 的 point 通常包含：

1. point id
2. vector
3. payload

在 RAG 里，vector 用于相似度搜索，payload 保存 content、source、title、permission_group 等信息。

### 自测 3 参考答案

Milvus collection schema 至少要考虑：

1. primary key field
2. vector field
3. content 字段
4. source/title/section 等来源字段
5. doc_type/business_domain/permission_group 等过滤字段

### 自测 4 参考答案

因为企业 RAG 不能只按语义相似检索，还要满足权限、业务域、文档类型、来源等条件。没有 filter，系统可能把用户无权访问的文档交给模型，造成安全问题。

### 自测 5 参考答案

索引能加速搜索，但会带来构建时间、存储空间、内存使用、参数调优和召回率取舍。索引不是数据本身，而是额外的辅助结构。

### 自测 6 参考答案

因为 collection 或 vector field 对向量维度有约束。旧 collection 如果按 1536 维建立，就不能直接写入 1024 维向量。通常需要新建 collection/schema，重新生成 embedding，重新入库，并重新调参评测。

### 自测 7 参考答案

因为 RAG 质量还取决于文档质量、chunk 切分、metadata、embedding 模型、检索参数、hybrid search、rerank、prompt、安全检查、引用来源和评测。向量数据库只是其中一层。

### 自测 8 参考答案

它们都可以理解为“向量数据库里的一条记录”，在我们的 RAG 项目里通常对应一个文档 chunk。Qdrant 叫 point，结构更像 id + vector + payload；Milvus 叫 entity，结构更像 schema 表里的一行。

### 自测 9 参考答案

当项目目标是学习 RAG、快速原型、中小规模、本地部署、metadata 更适合 JSON payload、团队希望降低基础设施复杂度时，可以先用 Qdrant。

### 自测 10 参考答案

当数据规模大、团队需要更明确的 schema 建模、要评估更复杂的索引和部署能力、已有 Milvus/Zilliz 生态经验，或企业平台要求使用 Milvus 时，应认真评估 Milvus。

## 20. 本节总结

本节最重要的不是记住某个产品宣传点，而是建立向量数据库选型的底层框架。

你现在应该能理解：

1. Qdrant 和 Milvus 都是向量数据库。
2. 它们在 RAG 中都可以作为 vector store。
3. Qdrant 的学习入口更直观，核心是 collection、point、vector、payload。
4. Milvus 的建模更像数据库，核心是 collection、schema、field、entity、index。
5. payload 和 scalar field 本质上都在解决 metadata 和 filter 问题。
6. 索引是加速搜索的辅助结构，不是免费能力。
7. 选型要看业务场景、数据规模、权限模型、查询压力、运维能力和成本。
8. 我们先用 Qdrant 是为了学懂 RAG 主线，现在补 Milvus 是为了建立更完整的向量数据库视野。

一句话收尾：

```text
会用一个向量数据库是工具能力，能解释为什么选它、怎么建模、怎么过滤、怎么扩展，才是工程能力。
```
