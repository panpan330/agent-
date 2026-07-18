# 阶段 4 第 35 节：Milvus metadata/scalar filter 和索引基础

> 本节目标：理解 Milvus 里 metadata filter、scalar field、scalar index 的关系，并在项目里把第 34 节的“能写入、能向量检索”推进到“能按业务 metadata 缩小检索范围，并给常用过滤字段建立 scalar index”。

## 0. 本节学习地图

第 34 节我们已经做到：

```text
Markdown/txt 文档
-> RagDocument
-> RagChunk
-> fake embedding
-> EmbeddedChunk
-> Milvus entity
-> Milvus collection
-> PyMilvus search
-> RetrievedChunk
```

但是第 34 节还有一个明显缺口：它虽然能把 metadata 写进 Milvus，也能把简单 filter 转成 Milvus 表达式，但还没有系统讲清楚：

- metadata filter 到底是什么；
- scalar field 和 vector field 有什么区别；
- 为什么 RAG 不能只靠向量相似度；
- 为什么不能先向量检索 top_k，再在 Python 里过滤 metadata；
- Milvus 的 scalar index 是什么；
- 哪些 metadata 字段应该建 scalar index；
- 过滤表达式里 `and`、`or`、`not`、`in`、范围过滤分别适合什么场景；
- 新集合和已有集合应该怎样补索引。

本节就补这块。

学完本节，你应该能解释：

1. RAG 里 metadata filter 的业务价值。
2. Milvus 里 vector field、scalar field、primary key 各自负责什么。
3. scalar filter 是如何和向量检索配合工作的。
4. scalar index 为什么能提升过滤速度。
5. `INVERTED`、`STL_SORT`、`AUTOINDEX` 的基本区别。
6. 项目里为什么给 `permission_group`、`business_domain`、`doc_type`、`source` 建 scalar index。
7. 项目里 filter dict 是如何被翻译成 Milvus boolean expression 的。
8. 如何用 smoke 脚本验证 Milvus 索引和 metadata filter。

本节暂时不学：

- Milvus 分区 partition。
- Milvus 多向量字段。
- 稀疏向量和 dense + sparse hybrid search。
- IVF/HNSW/DiskANN 等复杂向量索引调参。
- Milvus 集群部署。
- 权限系统和数据库用户权限的完整设计。
- 真实 embedding 模型调用。

这些放到后续阶段，不在本节混在一起。

## 1. 基础知识铺垫

### 1.1 为什么 RAG 不能只做“向量相似度”

RAG 检索的核心动作是：

```text
用户问题 -> query embedding -> 向量数据库里找相似 chunk
```

这个动作解决的是“语义相似”的问题。

例如用户问：

```text
退货运费谁承担？
```

向量检索可能找到：

- 退款退货规则里的“运费处理”；
- 订单发货规则里的“发货异常”；
- 物流查询 FAQ 里的“物流轨迹”；
- 账号安全 FAQ 里的“身份验证”。

如果只看语义，相似度不一定等于“业务上应该给这个用户看的资料”。企业 RAG 至少还要看这些限制：

| 问题 | 只靠向量相似度能解决吗 | 需要什么 |
| --- | --- | --- |
| 客服只能看客服资料，不能看内部风控资料 | 不能 | `permission_group` |
| 用户问退款，只想看退款域，不想混入物流域 | 不稳定 | `business_domain` |
| 只想检索政策文档，不要 FAQ | 不能 | `doc_type` |
| 更新某个文档时，只删除这个文档旧 chunk | 不能 | `source` |
| 只查某个文档的第 2-5 个 chunk | 不能 | `chunk_index` 范围过滤 |

所以企业 RAG 一般不是：

```text
只做向量检索
```

而是：

```text
向量相似度 + metadata 过滤 + 排序/阈值/重排 + 安全检查
```

metadata filter 是 RAG 从“玩具 Demo”进入“业务系统”的关键能力之一。

### 1.2 metadata 是什么

metadata 可以理解为“文档 chunk 的业务标签”。

一个 chunk 的正文可能是：

```text
如果退货原因属于用户个人原因，退货运费通常由用户承担。
```

它的 metadata 可能是：

```json
{
  "source": "refund-return-policy.md",
  "title": "退款退货规则",
  "doc_type": "policy",
  "business_domain": "refund",
  "permission_group": "customer_service",
  "chunk_index": 5,
  "chunk_count": 5,
  "section": "运费处理"
}
```

正文回答“这段知识讲什么”。

metadata 回答“这段知识属于哪里、谁能看、用在什么业务范围、如何管理”。

你以后做企业知识库时，metadata 经常比正文更影响系统质量。因为正文决定相似度，metadata 决定边界。

### 1.3 Milvus 里的 vector field 和 scalar field

Milvus 的 collection 有 schema。schema 里有 field。

对 RAG 来说，最重要的 field 分三类：

| 类型 | 本项目字段 | 作用 |
| --- | --- | --- |
| primary key | `chunk_id` | 唯一标识一个 chunk entity |
| vector field | `embedding` | 存向量，用于相似度检索 |
| scalar field | `content`、`source`、`doc_type`、`business_domain`、`permission_group`、`chunk_index` 等 | 存普通字段，用于返回内容、metadata filter、管理和展示 |

vector field 是“语义查找”用的。

scalar field 是“业务条件过滤”用的。

你可以把 Milvus entity 理解成一行数据：

```text
chunk_id | embedding | content | source | doc_type | business_domain | permission_group | chunk_index
```

其中：

- `embedding` 是一串浮点数；
- 其他字段大多是字符串或整数；
- 检索时先用向量找相似，再结合 scalar filter 限制范围。

### 1.4 filter 和 search 是什么关系

Milvus search 大概可以理解为：

```text
从 collection 里找与 query_vector 最相似的 top_k 条 entity
```

如果加上 filter，就变成：

```text
先把不符合条件的 entity 排除掉，
再在剩下的 entity 里做向量相似度搜索。
```

例如：

```text
permission_group == "customer_service" and business_domain == "refund"
```

意思是：

```text
只在 customer_service 能看的、refund 业务域的 chunk 里找相似内容。
```

这个顺序很重要。

正确的业务语义是：

```text
在允许范围内找最相似
```

而不是：

```text
先从全库找最相似，再把不允许的丢掉
```

### 1.5 为什么不能“先 top_k，再 Python 过滤”

这是初学 RAG 很容易犯的错误。

错误做法：

```text
1. 从全库向量检索 top_k=5
2. 拿到 5 条结果
3. 在 Python 里过滤 permission_group/business_domain
```

这个做法的问题是：你拿到的 top 5 是“全库 top 5”，不是“允许范围内 top 5”。

举个例子：

```text
全库最相似结果：
1. 内部风控文档，score=0.96
2. 内部运营文档，score=0.95
3. 内部售后文档，score=0.94
4. 客服退款文档，score=0.91
5. 客服物流文档，score=0.88
```

如果用户只能看 `customer_service`，Python 后置过滤后可能剩：

```text
4. 客服退款文档
5. 客服物流文档
```

看起来还行。

但如果全库 top 5 全是内部文档，Python 后置过滤后会变成空结果：

```text
[]
```

这并不代表“客服范围里没有相关资料”，只代表“全库 top 5 里没有客服资料”。

正确做法是把 filter 交给向量数据库：

```text
search(query_vector, filter='permission_group == "customer_service"', limit=5)
```

这样得到的是：

```text
customer_service 范围内的 top 5
```

这也是本节要把 Milvus filter 做扎实的原因。

### 1.6 Milvus boolean expression 是什么

Milvus 的 filter 参数是一个字符串表达式，常见形式类似：

```text
permission_group == "customer_service"
business_domain == "refund"
source in ["refund-return-policy.md", "order-shipping-policy.md"]
chunk_index >= 2 and chunk_index <= 5
not (permission_group == "internal_only")
```

这些表达式本质上是“谓词条件”。每个 entity 代入进去后，结果要么是 `true`，要么是 `false`。

例如 entity 的字段是：

```json
{
  "permission_group": "customer_service",
  "business_domain": "refund",
  "chunk_index": 4
}
```

表达式：

```text
permission_group == "customer_service" and chunk_index >= 2
```

结果是：

```text
true and true -> true
```

所以这个 entity 可以进入向量检索候选范围。

如果 entity 是：

```json
{
  "permission_group": "internal_only",
  "business_domain": "refund",
  "chunk_index": 4
}
```

表达式结果是：

```text
false and true -> false
```

所以它会被排除。

### 1.7 `and`、`or`、`not` 怎么理解

Milvus filter 里常见的逻辑关系：

| 逻辑 | 含义 | 例子 |
| --- | --- | --- |
| `and` | 条件都满足 | 客服可见，并且退款业务 |
| `or` | 条件满足任意一个 | 文档类型是 policy 或 faq |
| `not` | 条件取反 | 不允许 internal_only |

例子：

```text
permission_group == "customer_service" and business_domain == "refund"
```

表示：

```text
既要 customer_service，又要 refund。
```

例子：

```text
doc_type == "policy" or doc_type == "faq"
```

表示：

```text
policy 可以，faq 也可以。
```

例子：

```text
not (permission_group == "internal_only")
```

表示：

```text
排除 internal_only。
```

实际业务里最常用的是 `and`，因为权限、业务域、来源通常都要同时满足。

### 1.8 `==`、`in`、范围过滤分别适合什么

常见 metadata 过滤有三类。

第一类：精确匹配。

```text
business_domain == "refund"
```

适合：

- 某个权限组；
- 某个业务域；
- 某个文档类型；
- 某个来源文档。

第二类：多个候选值。

```text
source in ["refund-return-policy.md", "order-shipping-policy.md"]
```

适合：

- 只在几个文档里查；
- 允许多个业务域；
- 允许多个文档类型；
- 批量筛选来源。

第三类：范围过滤。

```text
chunk_index >= 2 and chunk_index <= 5
```

适合：

- 时间范围；
- 数值区间；
- chunk 序号区间；
- 价格、库存、评分等数值条件。

本项目暂时只有 chunk 的整数 metadata，所以本节支持整数范围过滤。

### 1.9 scalar index 是什么

先记住一句话：

```text
vector index 加速“相似度搜索”，scalar index 加速“字段过滤”。
```

如果没有 scalar index，Milvus 仍然可以做过滤，但在数据量大时可能需要扫描更多数据，速度会变慢。

如果给常用过滤字段建 scalar index，Milvus 可以更快定位符合条件的 entity。

类比关系：

| 场景 | 没索引 | 有索引 |
| --- | --- | --- |
| 查书里某个词 | 从头到尾翻每页 | 先看目录/索引页 |
| 查数据库某个用户 ID | 全表扫描 | 走 B-tree/hash 索引 |
| 查 Milvus 某个 metadata 字段 | 扫更多 scalar 数据 | 走 scalar index 缩小候选范围 |

RAG 里最常建 scalar index 的字段是：

- 权限字段；
- 业务域字段；
- 文档类型字段；
- 来源文档字段；
- 租户字段；
- 时间字段；
- 状态字段。

因为这些字段经常出现在 filter 里。

### 1.10 filter 如何影响向量检索范围

Milvus 处理 filter + vector search 时，可以把符合 scalar 条件的 entity 形成候选集合，再在这个集合里做向量搜索。

可以抽象成：

```text
所有 entity:
  [1, 2, 3, 4, 5, 6, 7, 8]

filter: business_domain == "refund"

过滤后的候选:
  [2, 4, 5, 8]

再做向量相似度:
  query_vector vs [2, 4, 5, 8]

返回 top_k:
  [5, 2, 8]
```

这个候选集合在底层常可以用 bitset 这类结构表达。你暂时不需要深究底层实现，只要理解：

```text
filter 不是简单装饰条件，它会影响向量搜索的候选空间。
```

### 1.11 INVERTED index 是什么

本节代码给几个字符串 metadata 字段创建 `INVERTED` index。

倒排索引可以理解为：

```text
字段值 -> 拥有这个值的 entity
```

例如 `business_domain`：

```text
refund -> chunk_0001, chunk_0002, chunk_0005
shipping -> chunk_0003, chunk_0004
account -> chunk_0006
```

当你查询：

```text
business_domain == "refund"
```

Milvus 可以通过索引更快找到 refund 对应的 entity 集合。

所以 `INVERTED` 很适合：

- 分类字段；
- 状态字段；
- 权限组字段；
- 文档类型字段；
- 来源字段；
- exact match；
- `in` 查询。

### 1.12 STL_SORT 是什么

Milvus 还支持 `STL_SORT` 这类 scalar index。

它更适合：

- 数值比较；
- 范围查询；
- 有序字段；
- 类似 `price >= 100 and price <= 200`；
- 类似 `created_at >= xxx`。

本项目当前主要学习 RAG metadata exact filter，所以默认用 `INVERTED`。如果后续引入时间范围、价格范围、订单金额范围，再讨论给数值字段用更合适的索引类型。

### 1.13 AUTOINDEX 是什么

`AUTOINDEX` 可以让 Milvus 根据字段类型自动选择合适索引。

优点：

- 初学和快速开发省心；
- 不需要一开始理解所有索引细节；
- 后续 Milvus 版本可能会优化选择策略。

缺点：

- 对学习来说不够显式；
- 你不容易看出“这个字段为什么建这个索引”；
- 面试或项目讲解时，容易说不清楚选型理由。

本项目向量字段使用 `AUTOINDEX`，因为我们当前不做向量索引调参。

本项目 metadata 字段使用 `INVERTED`，因为这些字段主要用于 exact match 和 `in` 过滤，学习意图更清楚。

### 1.14 哪些字段适合建 scalar index

不是所有 scalar field 都应该建 index。

建 index 有收益，也有成本：

| 影响 | 说明 |
| --- | --- |
| 查询更快 | 高频过滤字段可以更快缩小候选范围 |
| 写入更重 | 新增/更新数据时需要维护索引 |
| 占用存储 | 索引本身也需要空间 |
| 管理复杂 | 字段越多，索引策略越需要维护 |

所以一般只给“经常出现在 filter 里的字段”建索引。

本项目选择：

```text
permission_group
business_domain
doc_type
source
```

原因：

| 字段 | 为什么建索引 |
| --- | --- |
| `permission_group` | 权限过滤非常高频，必须稳定 |
| `business_domain` | 企业问答常按业务域缩小范围 |
| `doc_type` | 区分 policy/faq/runbook 等文档类型 |
| `source` | 文档级检索、调试、更新删除都常用 |

暂时不默认给 `content` 建 scalar index，因为正文很长，当前不是做全文检索。

暂时不默认给 `section` 建 scalar index，因为示例数据少，而且 section 值更偏展示和定位。

暂时不默认给 `chunk_index` 建 scalar index，因为目前范围过滤只是教学演示，真实业务里范围字段是否建索引要看查询频率。

### 1.15 filter 字符串为什么要由后端生成

Milvus 的 filter 是字符串。

这很方便，也有风险。

错误做法：

```python
filter_expression = user_input
```

如果用户传入乱七八糟的表达式，后端就等于把数据库查询条件交给用户控制。

更合理的做法：

```text
用户/业务代码传入结构化 filter dict
-> 后端白名单校验字段
-> 后端校验值类型
-> 后端转义字符串
-> 后端生成 Milvus filter expression
```

这就是本节代码继续沿用的边界：

```text
外部不直接传 Milvus 表达式字符串。
```

项目只允许受控字段：

```text
permission_group
business_domain
doc_type
source
file_name
file_extension
section
chunk_index
chunk_count
chunk_size_chars
```

其他字段会被拒绝。

## 2. 本节主题系统讲解

### 2.1 本节从第 34 节接到哪里

第 34 节已经有 `MilvusVectorStore`，它做了：

```text
创建 collection schema
创建 vector index
把 EmbeddedChunk 转为 Milvus entity
upsert entity
search query_vector
把 Milvus hit 转为 RetrievedChunk
```

第 35 节在它上面补两块：

```text
1. 更完整的 metadata filter 表达式生成
2. 给高频 metadata 字段创建 scalar index
```

也就是从：

```text
能查
```

推进到：

```text
能按业务边界查，并且给过滤字段建立索引基础
```

### 2.2 新增代码的总体结构

本节主要改动：

```text
projects/ai-service/app/rag/milvus_store.py
projects/ai-service/scripts/rag_milvus_filter_smoke.py
projects/ai-service/tests/test_rag_milvus_store.py
```

职责分别是：

| 文件 | 本节新增重点 |
| --- | --- |
| `milvus_store.py` | scalar index 字段清单、索引创建、filter 表达式增强 |
| `rag_milvus_filter_smoke.py` | 真实 Milvus 上验证索引列表和 metadata filter |
| `test_rag_milvus_store.py` | 用 fake client 验证索引策略和表达式翻译 |

### 2.3 本节新增的 scalar index 字段

项目里新增：

```python
MILVUS_SCALAR_INDEX_TYPE = "INVERTED"
MILVUS_SCALAR_INDEX_FIELDS = (
    "permission_group",
    "business_domain",
    "doc_type",
    "source",
)
```

这不是随便选的。

这四个字段都属于“高频过滤字段”：

- `permission_group`：权限边界；
- `business_domain`：业务域边界；
- `doc_type`：文档类型边界；
- `source`：文档来源边界。

你可以把这四个字段理解成 RAG 检索前最常用的“筛选器”。

### 2.4 新 collection 创建时如何带上 scalar index

当 collection 不存在时，`ensure_collection()` 会调用 `_create_collection()`。

现在 `_create_collection()` 不只创建 vector index：

```python
index_params.add_index(
    field_name=MILVUS_VECTOR_FIELD,
    index_type="AUTOINDEX",
    metric_type=self.metric_type,
)
```

还会调用：

```python
_add_milvus_scalar_indexes(index_params)
```

这一步会把默认的四个 scalar index 加到同一个 `index_params` 里。

最终新集合创建出来时就已经具备：

```text
embedding              vector index
idx_permission_group   scalar index
idx_business_domain    scalar index
idx_doc_type           scalar index
idx_source             scalar index
```

### 2.5 已有 collection 为什么也要补索引

你本地的 Milvus collection 是第 34 节创建的。

第 34 节当时只建了向量索引，没有建这四个 scalar index。

如果第 35 节只修改“创建新集合”的逻辑，那么你已有的 collection 不会自动拥有这些 index。

所以本节在已有 collection 分支里增加：

```python
self.ensure_scalar_indexes()
```

流程变成：

```text
collection exists
-> 校验 embedding 字段维度
-> list_indexes()
-> 找出缺失的 scalar index
-> create_index() 创建缺失索引
-> load_collection()
```

这点很重要：学习项目不是每一节都删库重建。真实项目更是如此，经常要对已有 collection 做演进。

### 2.6 为什么要先 list_indexes

如果每次启动都无脑 create_index，可能出现：

- 索引已存在导致报错；
- 重复创建无意义；
- 启动变慢；
- 日志噪声变多；
- 难以判断真实缺失了什么。

所以代码先：

```python
existing_indexes = set(self.list_indexes())
```

再判断：

```python
missing_fields = [
    field_name
    for field_name in scalar_fields
    if not _field_has_milvus_index(field_name, existing_indexes)
]
```

只有缺失才创建。

这是工程上常见的“幂等初始化”思路：

```text
多次运行，结果一样，不重复做没必要的事情。
```

### 2.7 index name 为什么叫 `idx_xxx`

本节使用：

```python
def build_milvus_scalar_index_name(field_name: str) -> str:
    normalized_field = _normalize_scalar_index_field(field_name)
    return f"idx_{normalized_field}"
```

例如：

```text
permission_group -> idx_permission_group
source -> idx_source
```

这样做有几个好处：

1. 一眼看出这是 index，不是 field。
2. 名字稳定，测试容易断言。
3. 后续 list/describe/drop index 时能明确定位。
4. 避免不同地方临时拼名字，导致命名不一致。

### 2.8 为什么 filterable fields 和 indexed fields 不是一回事

项目里有两个概念：

```python
MILVUS_FILTERABLE_FIELDS
MILVUS_SCALAR_INDEX_FIELDS
```

它们不是同一个东西。

`MILVUS_FILTERABLE_FIELDS` 表示：

```text
允许出现在 Milvus filter 里的字段。
```

本节包括：

```text
permission_group
business_domain
doc_type
source
file_name
file_extension
section
chunk_index
chunk_count
chunk_size_chars
```

`MILVUS_SCALAR_INDEX_FIELDS` 表示：

```text
默认要建 scalar index 的字段。
```

本节只有：

```text
permission_group
business_domain
doc_type
source
```

也就是说：

```text
能过滤 != 必须建索引
```

字段能被过滤，说明业务允许用它做条件。

字段默认建索引，说明它足够常用，值得承担索引成本。

### 2.9 本节增强的 filter 表达式

第 34 节只支持：

```python
{
    "must": [
        {"key": "permission_group", "match": {"value": "customer_service"}},
        {"key": "business_domain", "match": {"value": "refund"}}
    ]
}
```

转成：

```text
permission_group == "customer_service" and business_domain == "refund"
```

第 35 节继续支持这个最常用场景，同时新增：

| filter dict | Milvus expression |
| --- | --- |
| `match.value` | `field == "value"` |
| `match.any` | `field in ["a", "b"]` |
| `range.gte/lte/gt/lt` | `field >= 2 and field <= 5` |
| `should` | `expr1 or expr2` |
| `must_not` | `not (expr)` |

### 2.10 为什么继续使用 Qdrant 风格的 filter dict

项目之前已经有 `build_payload_filter()`，它生成的是一种结构化 filter dict：

```python
{
    "must": [
        {"key": "permission_group", "match": {"value": "customer_service"}}
    ]
}
```

虽然这个形状最早是为 Qdrant 准备的，但它很适合作为项目内部的“通用过滤意图”。

项目内部表达：

```text
我要按 permission_group 精确过滤
```

Milvus 适配器负责翻译成：

```text
permission_group == "customer_service"
```

Qdrant 适配器负责翻译成：

```json
{
  "must": [
    {
      "key": "permission_group",
      "match": {
        "value": "customer_service"
      }
    }
  ]
}
```

这样做的好处是：

```text
业务层不需要知道底层向量库的 filter 语法。
```

以后换向量库，尽量只改 adapter。

### 2.11 filter 表达式翻译链路

本节的链路是：

```text
payload_filter
-> normalize_payload_filter()
-> build_milvus_filter_expression()
-> _build_milvus_condition_group()
-> _build_milvus_condition_expression()
-> _build_milvus_match_expression() / _build_milvus_range_expression()
-> PyMilvus search(filter=...)
```

例子：

```python
payload_filter = {
    "must": [
        {
            "key": "source",
            "match": {
                "any": [
                    "refund-return-policy.md",
                    "order-shipping-policy.md",
                ]
            },
        },
        {"key": "chunk_index", "range": {"gte": 2, "lte": 5}},
    ],
    "must_not": [
        {"key": "permission_group", "match": {"value": "internal_only"}},
    ],
}
```

会被翻译成：

```text
source in ["refund-return-policy.md", "order-shipping-policy.md"]
and chunk_index >= 2 and chunk_index <= 5
and not (permission_group == "internal_only")
```

传给：

```python
self.client.search(
    collection_name=self.collection_name,
    data=[query_vector],
    anns_field=MILVUS_VECTOR_FIELD,
    filter=filter_expression,
    limit=top_k,
    output_fields=output_fields,
    search_params={"metric_type": self.metric_type, "params": {}},
    timeout=self.timeout_seconds,
)
```

### 2.12 字符串为什么要转义

filter expression 是字符串。

如果值里有双引号或反斜杠，直接拼接会破坏表达式。

所以 `_format_milvus_filter_value()` 会做：

```python
escaped = normalized.replace("\\", "\\\\").replace('"', '\\"')
return f'"{escaped}"'
```

例如用户值是：

```text
a"b
```

会变成：

```text
"a\"b"
```

这属于基础安全卫生，不是完整 SQL injection 体系，但思想相同：

```text
外部输入不能直接拼进查询表达式。
```

### 2.13 为什么 range 暂时只支持整数 metadata

项目当前有三个整数 metadata：

```text
chunk_index
chunk_count
chunk_size_chars
```

所以本节 range filter 限定在这些字段上。

如果你允许字符串字段做 range：

```text
source >= 2
```

就没有业务意义。

如果后面加入时间字段，比如：

```text
created_at
updated_at
effective_at
```

那可以再扩展成时间范围过滤。

当前先保持简单和明确：

```text
范围过滤只支持数值字段。
```

### 2.14 `should` 为什么要加括号

表达式里 `and` 和 `or` 同时出现时，括号能避免歧义。

例如：

```text
permission_group == "customer_service" and doc_type == "policy" or doc_type == "faq"
```

人读起来可能理解成：

```text
(permission_group == "customer_service" and doc_type == "policy") or doc_type == "faq"
```

这会导致所有 FAQ 都能进来，即使不是 customer_service。

更清楚的是：

```text
permission_group == "customer_service" and (doc_type == "policy" or doc_type == "faq")
```

所以本节代码对 `or` 组做了包装：

```python
if " or " not in expression:
    return expression
return f"({expression})"
```

这是表达式生成里很重要的细节。

### 2.15 本节 smoke 脚本验证什么

新增脚本：

```text
projects/ai-service/scripts/rag_milvus_filter_smoke.py
```

它验证：

1. 能连接 Milvus；
2. 能入库同一批示例知识文档；
3. collection 里能看到 scalar index；
4. exact metadata filter 能查；
5. `source in [...]` + `chunk_index` 范围过滤能查；
6. 结果仍然能转成项目统一的 `RetrievedChunk`。

本节实际 smoke 结果里看到：

```text
indexes:
- idx_permission_group
- idx_business_domain
- idx_doc_type
- idx_source
- embedding
```

说明本节新增索引已经在真实 Milvus 上生效。

### 2.16 本节的学习版边界

当前代码是学习版，不是生产级最终形态。

它有这些明确边界：

- 不支持任意用户手写 Milvus filter 字符串。
- 不支持所有 Milvus 表达式语法。
- 不支持动态字段。
- 不支持 collection migration 管理工具。
- 不支持生产级索引策略评估。
- 不支持 scalar index 的性能基准测试。
- 不支持真实 embedding 模型。
- 不处理 Milvus 分区和多租户部署。

但是它已经足够让你掌握：

```text
RAG metadata filter + Milvus scalar index 的主干知识。
```

## 3. 本节代码讲解

### 3.1 `MILVUS_SCALAR_INDEX_FIELDS`

位置：

```text
projects/ai-service/app/rag/milvus_store.py
```

核心：

```python
MILVUS_SCALAR_INDEX_TYPE = "INVERTED"
MILVUS_SCALAR_INDEX_FIELDS = (
    "permission_group",
    "business_domain",
    "doc_type",
    "source",
)
```

这段代码是本节的索引策略。

它没有把所有字段都建索引，而是只选了当前企业 RAG 最常用的过滤字段。

这是一种很重要的工程思路：

```text
先为明确高频查询建索引，不为了“看起来完整”给所有字段都建索引。
```

### 3.2 `build_milvus_scalar_index_name`

核心：

```python
def build_milvus_scalar_index_name(field_name: str) -> str:
    normalized_field = _normalize_scalar_index_field(field_name)
    return f"idx_{normalized_field}"
```

它做两件事：

1. 校验字段能不能建索引；
2. 生成稳定 index name。

这类小函数的价值不是“代码复杂”，而是让项目里所有 index 命名都由一个地方决定。

后续如果命名要改，只改这里。

### 3.3 `build_milvus_scalar_index_specs`

核心：

```python
return [
    {
        "field_name": field_name,
        "index_type": normalized_index_type,
        "index_name": build_milvus_scalar_index_name(field_name),
    }
    for field_name in normalized_fields
]
```

它把：

```text
["permission_group", "source"]
```

变成：

```python
[
    {
        "field_name": "permission_group",
        "index_type": "INVERTED",
        "index_name": "idx_permission_group",
    },
    {
        "field_name": "source",
        "index_type": "INVERTED",
        "index_name": "idx_source",
    },
]
```

这个函数本身不调用 Milvus，只负责生成“索引描述”。

真正执行由 `_add_milvus_scalar_indexes()` 和 `create_index()` 做。

### 3.4 `_add_milvus_scalar_indexes`

核心：

```python
for index_spec in build_milvus_scalar_index_specs(
    fields,
    index_type=index_type,
):
    index_params.add_index(**index_spec)
```

它把项目里的索引描述添加到 PyMilvus 的 `IndexParams`。

在 Milvus SDK 里，创建索引不是直接传一个普通 dict，而是通过：

```python
index_params = client.prepare_index_params()
index_params.add_index(...)
client.create_index(..., index_params=index_params)
```

本节保留了这个官方 SDK 的使用方式。

### 3.5 `ensure_scalar_indexes`

这是本节最关键的方法之一。

流程：

```text
1. 标准化要建索引的字段
2. list_indexes() 查看已有索引
3. 算出 missing_fields
4. 如果没有缺失，直接返回 []
5. 如果有缺失，prepare_index_params()
6. add_index(...)
7. create_index(...)
8. 返回实际补建的字段
```

它体现了两个工程思想。

第一个：幂等。

```text
重复运行不会重复创建已有索引。
```

第二个：兼容已有数据。

```text
不用删掉第 34 节已有 collection，也能给它补上第 35 节需要的索引。
```

### 3.6 `build_milvus_filter_expression`

这个函数把项目内部 filter dict 转成 Milvus 字符串表达式。

支持：

```text
must
should
must_not
match.value
match.any
range.gt/gte/lt/lte
```

输入：

```python
{
    "must": [
        {"key": "permission_group", "match": {"value": "customer_service"}},
        {"key": "business_domain", "match": {"value": "refund"}},
    ]
}
```

输出：

```text
permission_group == "customer_service" and business_domain == "refund"
```

输入：

```python
{
    "must": [
        {"key": "source", "match": {"any": ["refund-return-policy.md", "order.md"]}},
        {"key": "chunk_index", "range": {"gte": 2, "lte": 5}},
    ],
    "must_not": [
        {"key": "permission_group", "match": {"value": "internal_only"}}
    ]
}
```

输出：

```text
source in ["refund-return-policy.md", "order.md"] and chunk_index >= 2 and chunk_index <= 5 and not (permission_group == "internal_only")
```

这个函数真正值得学的是“适配层翻译”：

```text
业务层不要直接操心 Milvus 语法。
业务层描述过滤意图。
Milvus adapter 负责翻译成 Milvus 认识的表达式。
```

### 3.7 `query_similar` 里的 filter

`query_similar()` 里这段很关键：

```python
filter_expression = build_milvus_filter_expression(payload_filter)
```

然后：

```python
self.client.search(
    ...
    filter=filter_expression,
    ...
)
```

这说明：

```text
metadata filter 是跟着向量检索一起交给 Milvus 执行的。
```

不是 search 完之后在 Python 里过滤。

这是正确的 RAG 检索边界。

### 3.8 `rag_milvus_filter_smoke.py`

这个脚本不是单元测试，而是手动 smoke。

它会真实连接 Milvus：

```python
vector_store = MilvusVectorStore.from_settings(settings)
```

然后入库：

```python
ingest_directory_to_vector_store(...)
```

再打印索引：

```python
for index_name in vector_store.list_indexes():
    print(f"- {index_name}")
```

最后分别跑：

```text
exact metadata filter
advanced metadata filter
```

这让你能亲眼看到：

```text
索引存在
过滤生效
返回结果仍然是 RetrievedChunk
```

## 4. 手动运行方式

### 4.1 先确认虚拟机 Milvus 开着

因为 Milvus 现在跑在 VMware Ubuntu Docker 里，所以运行本节 smoke 前要确保虚拟机开着，Milvus container 也在运行。

Windows PowerShell 里可以测：

```powershell
Test-NetConnection 192.168.88.10 -Port 19530
```

看到：

```text
TcpTestSucceeded : True
```

说明 Windows 能连到 Milvus gRPC 端口。

### 4.2 运行单元测试

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run pytest tests/test_rag_milvus_store.py
```

本节验证结果：

```text
18 passed
```

### 4.3 运行真实 Milvus smoke

如果你的本机 `.env` 里没有设置 `MILVUS_URI`，默认可能会连：

```text
127.0.0.1:19530
```

但你的 Milvus 实际在 VMware Ubuntu：

```text
192.168.88.10:19530
```

所以可以临时这样运行：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
$env:PYTHONIOENCODING='utf-8'
$env:MILVUS_URI='http://192.168.88.10:19530'
uv run python scripts/rag_milvus_filter_smoke.py
```

本节实际验证结果：

```text
Milvus filter/index smoke test finished
collection: learning_rag_chunks_milvus
chunks: 16
indexes:
- idx_permission_group
- idx_business_domain
- idx_doc_type
- idx_source
- embedding
```

这说明：

```text
第 34 节已有 collection 被补齐了第 35 节需要的 scalar index。
```

### 4.4 为什么第一次 smoke 会连到 127.0.0.1

因为配置默认值或 `.env` 没有把 `MILVUS_URI` 改成虚拟机地址。

错误信息类似：

```text
Fail connecting to server on 127.0.0.1:19530
```

这不是 Milvus 一定坏了，而是“项目配置指向的位置不对”。

解决方法：

```powershell
$env:MILVUS_URI='http://192.168.88.10:19530'
```

或者把本机 `.env` 里的：

```text
MILVUS_URI=http://192.168.88.10:19530
```

配置好。

## 5. 常见问题

### 5.1 Milvus WebUI 能打开，为什么 PyMilvus 连不上

要区分端口：

| 端口 | 用途 |
| --- | --- |
| `19530` | Milvus SDK/gRPC 连接 |
| `9091` | Milvus HTTP/WebUI/管理信息 |

PyMilvus 主要连 `19530`。

如果你测的是 WebUI，可能是：

```text
http://192.168.88.10:9091
```

如果代码连 Milvus，要看：

```text
192.168.88.10:19530
```

### 5.2 为什么索引列表里 `embedding` 排在最后

`list_indexes()` 返回顺序不应该作为业务逻辑依赖。

你只需要确认这些名字存在：

```text
idx_permission_group
idx_business_domain
idx_doc_type
idx_source
embedding
```

顺序不重要。

### 5.3 为什么 `indexed_vectors_count` 可能是 0

之前你在 Qdrant/Milvus 查询里见过类似计数。不同向量库和不同索引构建策略下，“points 已写入”和“索引已构建计数”不是同一个概念。

本节重点不是通过某一个单独计数判断全部状态，而是看：

- collection 是否 healthy；
- points/entities 是否存在；
- index list 是否包含预期索引；
- filter search 是否能返回符合条件的结果。

### 5.4 中文显示乱码怎么办

如果 PowerShell 输出中文乱码，先怀疑显示编码，不要马上改文件。

可以先用：

```powershell
$env:PYTHONIOENCODING='utf-8'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

或者读取文件时指定：

```powershell
Get-Content -Encoding UTF8 path\to\file.md
```

本节 smoke 输出中文正常，说明文件内容和 Python 输出本身没有问题。

### 5.5 filter 字段越多越好吗

不是。

filter 字段越多，业务能力越强，但复杂度也会上升：

- 字段要有清晰语义；
- 数据入库时要保证字段完整；
- 查询时要校验字段；
- 高频字段可能要建索引；
- 权限字段必须可信，不能让模型或用户随便伪造。

学习阶段先保持少而清楚，比一开始设计几十个字段更好。

## 6. 本节练习

### 练习 1：判断哪些字段应该建 scalar index

给出下面字段：

```text
content
permission_group
business_domain
chunk_index
source
title
```

如果当前系统最常见查询是：

```text
按权限、业务域、来源文档过滤，再做向量检索
```

你会优先给哪些字段建 scalar index？为什么？

### 练习 2：把 filter dict 翻译成 Milvus 表达式

把下面 filter dict 翻译成 Milvus expression：

```python
{
    "must": [
        {"key": "permission_group", "match": {"value": "customer_service"}},
        {"key": "source", "match": {"any": ["a.md", "b.md"]}},
        {"key": "chunk_index", "range": {"gte": 2, "lte": 4}},
    ]
}
```

### 练习 3：解释为什么不能后置过滤

用自己的话解释：

```text
为什么不能先从全库搜 top_k=5，再在 Python 里过滤 permission_group？
```

### 练习 4：运行 smoke

在虚拟机 Milvus 开启时运行：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
$env:PYTHONIOENCODING='utf-8'
$env:MILVUS_URI='http://192.168.88.10:19530'
uv run python scripts/rag_milvus_filter_smoke.py
```

观察输出里是否有：

```text
idx_permission_group
idx_business_domain
idx_doc_type
idx_source
embedding
```

并记录 exact filter 和 advanced filter 分别返回了哪些 `source`。

## 7. 练习参考答案

### 答案 1

优先建：

```text
permission_group
business_domain
source
```

如果 `doc_type` 也经常用于过滤，也应该建。本题给出的字段里没有 `doc_type`，所以不选。

原因：

- `permission_group` 是权限边界，几乎每次检索都可能用；
- `business_domain` 能缩小业务范围，避免退款问题混入物流、账号资料；
- `source` 适合限定某个文档，也适合文档更新、调试；
- `content` 太长，当前不是全文检索；
- `title` 更多用于展示和引用，不一定高频过滤；
- `chunk_index` 可以过滤，但当前不是高频业务条件。

### 答案 2

表达式是：

```text
permission_group == "customer_service" and source in ["a.md", "b.md"] and chunk_index >= 2 and chunk_index <= 4
```

注意：

- `match.value` 变成 `==`；
- `match.any` 变成 `in [...]`；
- `range.gte` 变成 `>=`；
- `range.lte` 变成 `<=`；
- `must` 里的多个条件用 `and` 连接。

### 答案 3

不能后置过滤的核心原因是：

```text
全库 top_k 不等于过滤范围内 top_k。
```

如果先从全库取 5 条，可能这 5 条大部分都属于用户无权查看的资料。后置过滤后可能只剩 0-1 条，但这并不代表用户有权范围内没有相关资料，只是全库 top 5 把有权资料挤掉了。

正确做法是：

```text
把 permission_group filter 交给向量数据库，让数据库在允许范围内做 top_k。
```

### 答案 4

本节实测输出中应该看到类似：

```text
indexes:
- idx_permission_group
- idx_business_domain
- idx_doc_type
- idx_source
- embedding
```

exact filter 查询：

```text
permission_group=customer_service
business_domain=refund
```

返回的 `source` 应该主要是：

```text
refund-return-policy.md
```

advanced filter 查询限定：

```text
source in ["refund-return-policy.md", "order-shipping-policy.md"]
chunk_index between 2 and 5
not internal_only
```

返回的 `source` 应该只来自：

```text
refund-return-policy.md
order-shipping-policy.md
```

## 8. 自测题

### 自测 1

Milvus 里 vector index 和 scalar index 分别解决什么问题？

### 自测 2

为什么 `permission_group` 这类字段通常比 `title` 更适合默认建 scalar index？

### 自测 3

下面两个方案哪个更合理？为什么？

方案 A：

```text
search 全库 top_k=5 -> Python 过滤 permission_group
```

方案 B：

```text
search 时直接传 filter='permission_group == "customer_service"'
```

### 自测 4

`match.any` 和多个 `should` 条件有什么相似点？

### 自测 5

为什么后端不应该直接接收用户传入的 Milvus filter 字符串？

## 9. 自测题参考答案

### 自测 1 答案

vector index 加速向量相似度搜索，例如根据 query embedding 找语义相近的 chunk。

scalar index 加速普通字段过滤，例如根据 `permission_group`、`business_domain`、`doc_type`、`source` 缩小候选范围。

一句话：

```text
vector index 管“像不像”，scalar index 管“符不符合条件”。
```

### 自测 2 答案

`permission_group` 是高频过滤字段，通常每次企业知识库查询都要用它控制权限边界；`title` 更多用于展示、引用或辅助定位，不一定每次查询都按 title 过滤。

所以：

```text
高频过滤字段更值得建索引。
展示字段不一定要默认建索引。
```

### 自测 3 答案

方案 B 更合理。

原因是：

```text
方案 B 得到的是权限范围内的 top_k。
方案 A 得到的是全库 top_k 后的残留结果。
```

方案 A 可能漏掉权限范围内真正相关的资料，尤其当全库最相似结果大部分是用户无权查看的资料时。

### 自测 4 答案

它们都表达“多个候选值满足一个即可”。

例如：

```text
source in ["a.md", "b.md"]
```

和：

```text
source == "a.md" or source == "b.md"
```

语义很接近。

但 `in` 更适合表达同一个字段的多个候选值；`should/or` 更适合表达多个条件分支。

### 自测 5 答案

因为 filter 字符串会直接影响数据库查询范围。如果用户可以随便传，可能导致：

- 查询不该查询的字段；
- 绕过后端权限约束；
- 构造异常表达式导致错误；
- 给后续安全审计造成困难。

更合理的是：

```text
用户/业务层传结构化过滤意图
-> 后端字段白名单校验
-> 后端值类型校验
-> 后端生成 Milvus filter expression
```

## 10. 本节小结

本节你完成了 Milvus RAG 检索里非常关键的一块：

```text
向量检索 + metadata filter + scalar index
```

现在你应该能说清：

- metadata filter 决定业务边界；
- scalar field 存普通字段，vector field 存语义向量；
- Milvus filter expression 应该由后端生成；
- `and/or/not/in/range` 分别适合不同过滤场景；
- scalar index 用来加速字段过滤；
- 高频过滤字段才值得默认建索引；
- 不能先全库 top_k 再在 Python 后置过滤；
- 本项目现在能给已有 Milvus collection 补齐 scalar index。

下一节建议进入：

```text
阶段 4 第 36 节：Qdrant vs Milvus：什么时候选谁
```

这一节会把我们已经实际跑过的 Qdrant 和 Milvus 放到一起，从学习成本、部署复杂度、数据模型、过滤能力、运维要求、生态封装、适用场景等角度做系统对比。

## 11. 本节参考资料

- [Milvus Scalar Index 官方文档](https://milvus.io/docs/scalar_index.md)
- [Milvus Boolean Expression Rules](https://milvus.io/docs/boolean.md)
- [Milvus Inverted Index](https://milvus.io/docs/inverted.md)
- [Milvus STL_SORT Index](https://milvus.io/docs/stl-sort.md)
- [PyMilvus create_index API](https://milvus.io/api-reference/pymilvus/v3.0.x/MilvusClient/Management/create_index.md)
- [PyMilvus list_indexes API](https://milvus.io/api-reference/pymilvus/v3.0.x/MilvusClient/Management/list_indexes.md)
- [PyMilvus describe_index API](https://milvus.io/api-reference/pymilvus/v3.0.x/MilvusClient/Management/describe_index.md)
