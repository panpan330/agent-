# 阶段 4 第 16 节：payload filter：按文档类型、权限、来源过滤

## 本节状态

已完成。

本节接在第 15 节“基础 top_k 检索”之后。第 15 节解决的是：

```text
用户问题 -> query embedding -> Qdrant 向量检索 -> 返回 top_k 个最相似 chunk
```

第 16 节解决的是：

```text
用户问题 -> query embedding -> 带业务条件的 Qdrant 向量检索 -> 只在允许范围内返回 top_k 个最相似 chunk
```

也就是说，从这一节开始，我们不再只问“哪个 chunk 语义最像”，还要问：

- 这个 chunk 属不属于当前业务领域？
- 这个 chunk 属不属于当前用户能看的权限组？
- 这个 chunk 是不是我们想要的文档类型？
- 这个 chunk 是否来自指定文件？

这就是 RAG 从“能搜”走向“可控、可解释、可落地”的关键一步。

## 本节学习目标

学完本节，你要能讲清楚：

1. 为什么 RAG 不能只靠向量相似度。
2. 什么是 payload，什么是 payload filter。
3. 为什么权限过滤、业务领域过滤、文档类型过滤必须放在后端检索链路里。
4. `top_k` 加上 filter 以后，含义发生了什么变化。
5. Qdrant filter 里 `must` 和 `match.value` 分别表达什么。
6. 为什么第 14 节设计 metadata，到这一节才真正体现价值。
7. 为什么本节依然使用 fake embedding，而不是提前接真实 embedding 模型。
8. 如何在代码里把“业务过滤条件”变成 Qdrant 能理解的 JSON filter。

## 本节暂时不学什么

为了把边界讲清楚，本节不做这些事：

- 不做 `score_threshold`，下一节再讲低相关内容不回答。
- 不把检索结果交给大模型生成最终回答，后续第 18 节再讲。
- 不接真实 embedding API，后续会单独讲真实 embedding 模型选择、成本、维度和批量处理。
- 不做多租户完整权限系统，本节只做 RAG 检索侧的权限过滤雏形。
- 不做复杂布尔表达式，比如 `should`、`must_not`、范围过滤、时间过滤。
- 不做 Milvus 的 scalar filter，对比会放在阶段 4 后半段。

## 一、基础知识铺垫

### 1. 只靠向量相似度有什么问题

向量相似度解决的是“语义像不像”。

比如用户问：

```text
订单超过 72 小时没有发货怎么办？
```

向量检索会尝试找到语义接近的 chunk。它可能找到：

- 订单发货规则。
- 退款退货规则。
- 物流查询 FAQ。
- 账号安全 FAQ。

如果 embedding 模型足够好，通常“订单发货规则”会排在前面。但在真实项目里，你不能完全依赖这件事。

原因有几个：

1. 用户问题可能很短，语义信息不够。
2. 文档之间可能有相似表达，比如“处理时效”“客服介入”“审核”等。
3. embedding 模型不是业务规则引擎，它不知道谁有权限看什么。
4. top_k 只表示“最相似的几个”，不表示“一定属于正确业务范围”。
5. 企业知识库里可能有内部文档、客服文档、财务文档、管理员文档混在一起。

所以真实 RAG 系统里通常不是：

```text
只用向量相似度决定一切
```

而是：

```text
先限定允许检索的范围，再在这个范围内做语义相似度排序
```

本节的 payload filter 就是用来限定检索范围的。

### 2. 什么是 payload

在 Qdrant 里，一个 point 大致可以理解为：

```text
point = id + vector + payload
```

对应到我们的 RAG 项目里：

```text
point id  -> chunk_id 生成出来的稳定 UUID
vector    -> chunk 文本生成出来的 embedding 向量
payload   -> chunk 的正文和 metadata
```

payload 里面保存的不是向量，而是和这个向量对应的业务信息。

例如一个订单发货规则 chunk 的 payload 可以像这样：

```json
{
  "chunk_id": "order_shipping_policy_chunk_0001",
  "content": "订单付款后通常会在 24 小时内发货...",
  "source": "order-shipping-policy.md",
  "title": "订单发货规则",
  "section": "正常发货时效",
  "doc_type": "policy",
  "business_domain": "order",
  "permission_group": "customer_service"
}
```

其中：

- `content` 是将来要交给模型回答问题的正文。
- `source` 用来说明内容来自哪个文件。
- `title` 用来说明文档标题。
- `section` 用来说明 chunk 位于哪个章节。
- `doc_type` 用来说明文档类型，比如 `policy`、`faq`。
- `business_domain` 用来说明业务领域，比如 `order`、`refund`、`logistics`。
- `permission_group` 用来说明哪些角色或系统范围可以看。

这就是第 14 节 metadata 设计的价值。metadata 不是为了“看起来完整”，而是为了后面能过滤、引用、排查和权限控制。

### 3. 什么是 payload filter

payload filter 就是按照 payload 字段筛选 point。

比如我们只想查客服能看的订单领域文档，就可以表达为：

```json
{
  "must": [
    {
      "key": "permission_group",
      "match": {
        "value": "customer_service"
      }
    },
    {
      "key": "business_domain",
      "match": {
        "value": "order"
      }
    }
  ]
}
```

这段 filter 的意思是：

```text
必须满足 permission_group == customer_service
并且必须满足 business_domain == order
```

这里的关键点有两个：

1. `must` 表示“这些条件都必须满足”，可以先理解成 SQL 里的 `AND`。
2. `match.value` 表示字段值要精确匹配某个值。

所以它不是“让模型判断要不要过滤”，而是后端用明确字段条件限制向量数据库的检索范围。

### 4. filter 和 top_k 的关系

没有 filter 时：

```text
在整个 collection 里找最相似的 top_k 个 chunk
```

有 filter 时：

```text
先限定可检索范围，再在这个范围里找最相似的 top_k 个 chunk
```

这句话很重要。

如果用户问订单问题，`top_k=3`，但没有 filter，那么结果可能是：

```text
1. 退款文档 chunk
2. 账号安全文档 chunk
3. 订单文档 chunk
```

如果加上：

```text
business_domain = order
```

那么结果应该变成：

```text
只在订单领域文档里找最相似的 3 个 chunk
```

这时 `top_k=3` 不再是“全库最相似 3 个”，而是“过滤后的候选集合里最相似 3 个”。

这也是很多初学者容易混淆的点：

```text
filter 不是排序规则。
filter 是候选范围规则。
score 才是相似度排序结果。
```

### 5. 为什么权限不能只靠 prompt

错误做法：

```text
把所有检索结果都交给模型，然后在 prompt 里写：
“如果用户没有权限，请不要回答内部文档内容。”
```

这种方式不可靠。

因为模型已经看到了不该看的内容。即使你要求它不要说，它也可能受上下文影响，或者在复杂对话里泄露信息。

更正确的边界是：

```text
用户没有权限看到的 chunk，一开始就不要被检索出来。
```

也就是：

```text
权限控制要尽量前置到检索阶段。
```

本节的 `permission_group` 只是一个教学版雏形。真实系统中，权限会更复杂，可能包括：

- 用户角色。
- 部门。
- 租户。
- 数据级权限。
- 文档密级。
- 文档生效状态。
- 组织层级。

但核心思想不变：

```text
不要把用户不该看的内容交给模型。
```

### 6. filter 和关键词搜索不是一回事

payload filter 不是全文搜索。

例如：

```json
{
  "key": "business_domain",
  "match": {
    "value": "order"
  }
}
```

它不是在正文里搜索“order”这个词，而是要求 payload 里的 `business_domain` 字段等于 `order`。

所以 payload filter 更像数据库里的结构化条件：

```sql
WHERE business_domain = 'order'
```

向量检索更像语义排序：

```text
ORDER BY semantic_similarity DESC
```

合在一起就是：

```sql
WHERE business_domain = 'order'
ORDER BY semantic_similarity DESC
LIMIT 3
```

这不是 Qdrant 真正执行的 SQL，只是帮助理解。

### 7. filter 字段必须来自稳定 metadata

能不能按某个字段过滤，取决于这个字段是否稳定存在于 payload 里。

比如我们想按 `business_domain` 过滤，那么入库时每个 chunk 的 payload 里就必须有：

```json
{
  "business_domain": "order"
}
```

如果有些 chunk 没有这个字段，或者有时写成 `order`，有时写成 `orders`，有时写成 `订单`，过滤结果就会不稳定。

所以第 14 节我们做了 metadata 标准化和必备字段校验，本节才可以放心构造 filter。

顺序应该是：

```text
先设计 metadata -> 入库时写入 payload -> 查询时使用 payload filter
```

如果没有前面的 metadata 设计，本节就只能临时拼字段，后面会很难维护。

### 8. 为什么本节先支持 4 个过滤字段

本节支持：

```text
permission_group
business_domain
doc_type
source
```

原因是它们对应企业 RAG 里最常见的 4 类控制需求：

| 字段 | 解决的问题 | 示例 |
| --- | --- | --- |
| `permission_group` | 谁能看 | `customer_service` |
| `business_domain` | 查哪个业务领域 | `order`、`refund` |
| `doc_type` | 查哪种文档 | `policy`、`faq` |
| `source` | 限定某个来源文件 | `order-shipping-policy.md` |

这 4 个字段足够支撑你理解 payload filter 的主线。

后面如果要扩展，可以加：

- `tenant_id`：租户隔离。
- `department_id`：部门隔离。
- `visibility`：公开、内部、私密。
- `effective_from`、`effective_to`：文档生效时间。
- `version`：文档版本。
- `language`：语言。

但现在不急着加，先把最核心的过滤链路讲清楚。

## 二、本节主题系统讲解

### 1. 第 15 节和第 16 节的链路对比

第 15 节：

```text
retrieve_top_k(query)
-> embedding_model.embed_texts([query])
-> vector_store.query_similar(query_vector, top_k=3)
-> Qdrant /points/query
-> 返回 RetrievedChunk
```

第 16 节：

```text
retrieve_top_k(query, permission_group="customer_service", business_domain="order")
-> build_payload_filter(...)
-> embedding_model.embed_texts([query])
-> vector_store.query_similar(query_vector, top_k=3, payload_filter=...)
-> Qdrant /points/query，body 里带 filter
-> 返回过滤后的 RetrievedChunk
```

新增的核心不是“多写几个参数”，而是把业务约束放进检索请求。

### 2. 本节新增的 `filters.py` 负责什么

新增文件：

```text
projects/ai-service/app/rag/filters.py
```

它的职责是：

```text
把项目内部容易理解的过滤参数
转换成 Qdrant 能理解的 payload filter JSON
```

为什么要单独建这个文件？

因为 filter 是一个独立知识点。

它不属于 embedding。
它不属于 document loader。
它也不应该散落在 router、service 或 vector store 的每个调用点里。

如果以后你要换向量库、扩展字段、增加 `must_not`、增加时间范围过滤，都应该优先在这个边界附近改。

### 3. `build_match_condition()` 做了什么

它接收：

```python
key = "business_domain"
value = "order"
```

返回：

```python
{
    "key": "business_domain",
    "match": {
        "value": "order",
    },
}
```

这就是 Qdrant 的单个字段精确匹配条件。

这里有几个设计点：

1. `value is None` 时返回 `None`。
   这表示“用户没有要求这个过滤条件”，不是错误。

2. `value.strip()` 后为空字符串时抛出错误。
   因为 `"   "` 不是有效过滤条件。它通常说明调用方传错了参数。

3. `key.strip()` 后为空字符串时也抛出错误。
   因为空字段名无法构造有意义的过滤条件。

4. 这里不让模型或用户随意传任意复杂 filter。
   本节只从后端明确支持的参数构造 filter，边界更清楚。

### 4. `build_payload_filter()` 做了什么

它接收这些可选参数：

```python
permission_group: str | None = None
business_domain: str | None = None
doc_type: str | None = None
source: str | None = None
```

然后把非空条件组成：

```python
{
    "must": [
        {"key": "permission_group", "match": {"value": "customer_service"}},
        {"key": "business_domain", "match": {"value": "order"}},
    ]
}
```

如果所有参数都是 `None`，它返回：

```python
None
```

为什么不返回空字典 `{}`？

因为空 filter 的含义不清楚：

- 它是“不需要过滤”？
- 还是“过滤条件构造错了”？
- Qdrant 会不会接受？

在我们的项目里，统一约定：

```text
None 表示不使用 filter。
非 None 的 dict 表示要发送给 Qdrant 的 filter。
```

这样调用链更清楚。

### 5. `normalize_payload_filter()` 做了什么

这个函数在 vector store 层使用。

它的作用是：

```text
进入 Qdrant 请求前，对 payload_filter 做最后一次轻量归一化
```

规则是：

- `None` 继续表示不使用 filter。
- 空字典 `{}` 抛出错误。
- 其他 mapping 转成普通 `dict`。

为什么 vector store 层还要检查？

因为 `QdrantVectorStore.query_similar()` 是更底层的适配器。将来不一定只有 `retrieve_top_k()` 会调用它。

所以底层也要保护自己，不能默认所有调用方都传得正确。

### 6. `QdrantVectorStore.query_similar()` 有什么变化

第 15 节时，它发送的请求体大致是：

```json
{
  "query": [0.1, 0.2, 0.3, 0.4],
  "limit": 3,
  "with_payload": true,
  "with_vector": false
}
```

第 16 节增加 filter 后，请求体可以变成：

```json
{
  "query": [0.1, 0.2, 0.3, 0.4],
  "limit": 3,
  "with_payload": true,
  "with_vector": false,
  "filter": {
    "must": [
      {
        "key": "permission_group",
        "match": {
          "value": "customer_service"
        }
      },
      {
        "key": "business_domain",
        "match": {
          "value": "order"
        }
      }
    ]
  }
}
```

注意这里的几个字段：

- `query` 是查询向量。
- `limit` 是最多返回多少条。
- `with_payload` 表示结果里要不要带 payload。
- `with_vector` 表示结果里要不要带原始向量。
- `filter` 表示检索前的结构化过滤条件。

我们默认 `with_vector=False`，因为问答阶段通常不需要把向量返回给上层。我们需要的是正文、来源、章节、分数等信息。

### 7. `retrieve_top_k()` 有什么变化

现在它可以这样调用：

```python
retrieve_top_k(
    "订单超过 72 小时没有发货怎么办？",
    embedding_model=embedding_model,
    vector_store=vector_store,
    top_k=3,
    permission_group="customer_service",
    business_domain="order",
)
```

这句话表达的业务语义是：

```text
把用户问题转成向量，
但只在客服可见的订单领域文档里找最相似的 3 个 chunk。
```

这比单纯的：

```python
retrieve_top_k(query, top_k=3)
```

更接近真实企业 RAG。

因为真实系统里，检索范围通常来自：

- 当前登录用户。
- 当前租户。
- 当前业务线。
- 当前入口场景。
- 当前问题分类结果。

现在我们只是先用显式参数把这条链路跑通。

### 8. 为什么 filter 在 retriever 层构造，而不是在脚本里手写 Qdrant JSON

脚本里可以直接写：

```python
payload_filter = {
    "must": [
        {"key": "business_domain", "match": {"value": "order"}}
    ]
}
```

但这不是好的学习路径。

因为脚本只是临时入口，真正的项目代码应该提供稳定的内部 API。

更合理的是：

```python
retrieve_top_k(
    query,
    business_domain="order",
)
```

由 `retrieve_top_k()` 内部调用 `build_payload_filter()`。

这样上层调用方不需要知道 Qdrant filter JSON 的细节。它只需要知道自己的业务意图：

```text
我要查 order 领域。
我要查 customer_service 权限组。
我要查 policy 文档。
我要查某个 source 文件。
```

底层再把这些意图转换成 Qdrant 的请求格式。

### 9. 本节烟测脚本为什么加上过滤条件

脚本：

```text
projects/ai-service/scripts/rag_retrieve_smoke.py
```

现在调用检索时加了：

```python
permission_group="customer_service"
business_domain="order"
```

这表示：

```text
用 fake query embedding 做一次真实 Qdrant 查询，
但只在客服可见的订单领域文档里检索。
```

这里还要记住第 15 节讲过的限制：

```text
fake embedding 只能验证链路能不能跑通，不能代表真实语义检索质量。
```

所以如果 fake embedding 返回结果看起来不够聪明，不要急着调业务逻辑。真正语义质量要等后面接入真实 embedding 模型再评估。

本节烟测更关注：

- Windows 能访问 VMware Ubuntu 里的 Qdrant。
- collection 能查询。
- Qdrant 请求体里带 filter。
- 返回结果能解析成 `RetrievedChunk`。
- 检索范围能被 `business_domain`、`permission_group` 限定。

## 三、从业务角度理解本节的 4 个过滤字段

### 1. `permission_group`

示例：

```python
permission_group="customer_service"
```

含义：

```text
只检索客服可见的知识 chunk。
```

这不是完整权限系统，但它体现了权限过滤的第一步：

```text
不是所有知识都应该进入模型上下文。
```

以后如果有管理员文档、财务文档、内部处理 SOP，就不能让普通客服入口直接检索到。

### 2. `business_domain`

示例：

```python
business_domain="order"
```

含义：

```text
只检索订单业务领域的知识 chunk。
```

如果用户问发货问题，我们通常不希望退款、账号安全、物流查询全部混进候选范围。

业务领域过滤能降低“语义相似但业务不对”的概率。

### 3. `doc_type`

示例：

```python
doc_type="policy"
```

含义：

```text
只检索政策类文档。
```

这在真实系统里很有用。

比如同样是订单领域，可能有：

- `policy`：正式规则。
- `faq`：常见问答。
- `sop`：客服操作流程。
- `notice`：临时公告。

不同入口可能优先使用不同文档类型。

### 4. `source`

示例：

```python
source="order-shipping-policy.md"
```

含义：

```text
只检索某一个来源文件里的 chunk。
```

这在调试和指定文档问答里很有用。

比如你想验证“订单发货规则”这份文档切分和入库是否正常，就可以限定 source，避免其他文档干扰。

## 四、常见误区

### 误区 1：filter 会让模型更聪明

filter 不会提高 embedding 模型的语义理解能力。

它做的是缩小候选范围。

可以理解为：

```text
filter 决定在哪些资料里找。
embedding score 决定这些资料里谁更相似。
```

### 误区 2：top_k=3 就一定返回 3 条

不一定。

如果过滤后的候选范围只有 1 条满足条件，那最多只能返回 1 条。

所以有 filter 以后：

```text
top_k 是最多返回数量，不是保证返回数量。
```

### 误区 3：没有返回结果一定是向量库坏了

不一定。

可能原因包括：

- collection 里没有数据。
- 当前 filter 太严格。
- metadata 写入时字段值和查询时不一致。
- 查询的 `business_domain` 拼错。
- 查询的 `permission_group` 和入库 payload 不匹配。
- Qdrant 服务没启动。

排查时要先看：

```text
Qdrant 里 points_count 是否大于 0
scroll 看 payload 字段是否存在
filter 的 key 和 value 是否和 payload 完全一致
```

### 误区 4：权限过滤可以等模型回答时再处理

不建议。

权限过滤越靠后，泄露风险越高。

更合理的顺序是：

```text
检索前或检索时限制候选范围
-> 只把允许看到的 chunk 交给模型
-> 模型基于允许范围生成回答
```

### 误区 5：payload filter 就是全文搜索

不是。

payload filter 匹配的是结构化字段。

它不会在 `content` 正文里做关键词全文搜索。

如果未来要做“关键词检索 + 向量检索”，那是后面混合检索的内容。

## 五、本节代码改动说明

### 1. 新增 `app/rag/filters.py`

新增内容包括：

- `PayloadFilter`：表示本项目当前使用的 Qdrant filter 类型。
- `FILTERABLE_METADATA_KEYS`：列出当前允许作为过滤条件的 metadata 字段。
- `build_match_condition()`：构造单个 Qdrant match 条件。
- `build_payload_filter()`：把多个业务过滤参数合成 `must` filter。
- `normalize_payload_filter()`：在 vector store 层做轻量防御。

这部分代码的学习重点不是 Python 语法，而是职责边界：

```text
业务参数 -> 项目内部 filter builder -> Qdrant filter JSON
```

### 2. 修改 `app/rag/vector_store.py`

核心变化：

```python
def query_similar(
    self,
    query_vector: list[float],
    *,
    top_k: int,
    payload_filter: Mapping[str, Any] | None = None,
    with_payload: bool = True,
    with_vector: bool = False,
) -> list[RetrievedChunk]:
```

新增了 `payload_filter` 参数。

然后请求体从固定结构变成：

```python
request_body = {
    "query": query_vector,
    "limit": top_k,
    "with_payload": with_payload,
    "with_vector": with_vector,
}
if normalized_filter is not None:
    request_body["filter"] = normalized_filter
```

这个写法有一个好处：

```text
没有 filter 时，请求体保持简单。
有 filter 时，才把 filter 字段发送给 Qdrant。
```

这比无论如何都发送空 filter 更清晰。

### 3. 修改 `app/rag/retriever.py`

核心变化：

```python
payload_filter = build_payload_filter(
    permission_group=permission_group,
    business_domain=business_domain,
    doc_type=doc_type,
    source=source,
)
```

然后：

```python
return vector_store.query_similar(
    query_vector,
    top_k=top_k,
    payload_filter=payload_filter,
    with_payload=True,
    with_vector=False,
)
```

这说明 `retriever` 开始承担两件事：

1. 把用户问题变成 query vector。
2. 把业务检索范围变成 payload filter。

但它仍然不负责：

- 生成最终回答。
- 调用大模型。
- 做权限系统完整鉴权。
- 做 score_threshold 判断。

这些边界暂时不混在一起。

### 4. 修改 `scripts/rag_retrieve_smoke.py`

现在烟测脚本用：

```python
retrieve_top_k(
    query,
    embedding_model=embedding_model,
    vector_store=vector_store,
    top_k=3,
    permission_group="customer_service",
    business_domain="order",
)
```

这让手动烟测更接近真实场景：

```text
不是全库乱搜，而是在指定权限组和业务领域里搜。
```

## 六、手动验证思路

如果你的 VMware Ubuntu 里的 Qdrant 正在运行，可以在 Windows 的 `ai-service` 目录执行：

```powershell
uv run python scripts/rag_retrieve_smoke.py
```

如果 Qdrant 没启动，需要先打开虚拟机，并确保容器运行：

```bash
docker ps --filter name=qdrant
```

Windows 侧也可以用：

```powershell
curl.exe http://192.168.88.10:6333/collections/learning_rag_chunks
```

如果要查看 payload，可以在 PowerShell 里优先使用 `Invoke-RestMethod`，避免 `curl` 别名和引号问题：

```powershell
$body = @{
    limit = 3
    with_payload = $true
    with_vector = $false
} | ConvertTo-Json

$response = Invoke-RestMethod `
    -Method Post `
    -Uri "http://192.168.88.10:6333/collections/learning_rag_chunks/points/scroll" `
    -ContentType "application/json" `
    -Body $body

$response.result.points | Format-List
```

如果 PowerShell 显示中文乱码，先不要急着改文件。优先怀疑是终端输出编码显示问题。可以用代码或编辑器确认源文件是不是 UTF-8。

## 七、测试说明

本节测试覆盖了三层：

1. `test_rag_filters.py`
   验证 filter builder 能生成正确 Qdrant JSON，并拒绝空条件。

2. `test_rag_retriever.py`
   验证 `retrieve_top_k()` 会把业务过滤参数转换成 payload filter，再传给 vector store。

3. `test_rag_vector_store.py`
   验证 `QdrantVectorStore.query_similar()` 会把 filter 放进 Qdrant `/points/query` 请求体。

这里测试不真实调用 Qdrant。

原因是：

```text
单元测试要稳定、快速、可重复。
真实 Qdrant 联调交给 smoke script。
```

## 八、本节和前面几节的关系

### 和第 13 节的关系

第 13 节完成：

```text
chunk -> fake embedding -> Qdrant point -> upsert
```

也就是把数据写进 Qdrant。

第 16 节是在查询时利用这些 point 的 payload。

### 和第 14 节的关系

第 14 节设计 metadata：

```text
source/title/section/doc_type/business_domain/permission_group
```

第 16 节开始真正用 metadata 做过滤。

如果没有第 14 节，本节无法稳定过滤。

### 和第 15 节的关系

第 15 节只做：

```text
相似度 top_k
```

第 16 节变成：

```text
过滤后的相似度 top_k
```

这是企业 RAG 的一个关键升级。

### 和第 17 节的关系

第 17 节会继续补：

```text
score_threshold：低相关内容不回答
```

到那时检索控制会进一步变成：

```text
先用 filter 限定范围
-> 再用 top_k 找候选
-> 再用 score_threshold 拒绝低相关内容
```

## 九、本节练习

### 练习 1：解释 filter 和 top_k 的关系

题目：

请用自己的话解释：

```text
top_k=3
```

在有 filter 和没有 filter 时分别是什么意思。

参考答案：

没有 filter 时，`top_k=3` 表示在整个 collection 里返回最相似的最多 3 个 chunk。

有 filter 时，`top_k=3` 表示先用 filter 限定候选范围，然后只在这个范围里返回最相似的最多 3 个 chunk。

所以 filter 决定“在哪些资料里找”，top_k 决定“最多拿回几个”。

### 练习 2：写出订单领域过滤条件

题目：

请写出一个 Qdrant payload filter，要求：

```text
permission_group = customer_service
business_domain = order
```

参考答案：

```json
{
  "must": [
    {
      "key": "permission_group",
      "match": {
        "value": "customer_service"
      }
    },
    {
      "key": "business_domain",
      "match": {
        "value": "order"
      }
    }
  ]
}
```

### 练习 3：判断哪个字段适合做 filter

题目：

下面哪些字段适合做 payload filter？

```text
A. business_domain
B. permission_group
C. content
D. doc_type
E. source
```

参考答案：

适合的是 A、B、D、E。

`content` 是正文，通常用于交给模型生成回答，不适合在本节用 `match.value` 做结构化过滤。后面如果要按正文关键词搜索，会进入全文搜索或混合检索话题，不属于本节 payload filter 的重点。

### 练习 4：解释为什么权限过滤不能只靠 prompt

题目：

为什么不能把所有 chunk 都交给模型，然后在 prompt 里要求模型“不要泄露无权限内容”？

参考答案：

因为模型已经看到了不该看的内容。只靠 prompt 约束模型不要说，风险太高。更合理的方式是在检索阶段就过滤掉用户无权看到的 chunk，只把允许范围内的内容交给模型。

### 练习 5：设计一个调试场景

题目：

如果你想只验证 `order-shipping-policy.md` 这份文档的检索结果，应该用哪个过滤字段？

参考答案：

应该用 `source`：

```python
retrieve_top_k(
    query,
    embedding_model=embedding_model,
    vector_store=vector_store,
    source="order-shipping-policy.md",
)
```

这样可以只在这一个来源文件的 chunk 里检索，方便调试文档切分、入库和查询结果。

## 十、自测问题

### 自测 1

问题：

payload filter 解决的是语义相似度问题，还是候选范围问题？

答案：

候选范围问题。语义相似度由 embedding 和向量距离负责，payload filter 负责限定在哪些 point 里检索。

### 自测 2

问题：

`must` 条件可以怎么理解？

答案：

可以先理解成多个条件之间的 `AND`。所有 `must` 里的条件都满足，这个 point 才会进入候选范围。

### 自测 3

问题：

为什么 `build_payload_filter()` 在没有任何过滤条件时返回 `None`，而不是 `{}`？

答案：

`None` 明确表示“不使用 filter”。空字典含义不清楚，容易让调用方和底层适配器混淆，所以本项目把空 filter 当成错误处理。

### 自测 4

问题：

如果 `business_domain="order"` 查不到结果，可能有哪些原因？

答案：

可能 collection 没有数据；payload 里没有 `business_domain` 字段；入库时字段值不是 `order`；查询时拼写不一致；filter 太严格；Qdrant 服务或 collection 配置有问题。

### 自测 5

问题：

本节为什么仍然使用 fake embedding？

答案：

因为本节目标是学习 payload filter 和检索范围控制，不是评估真实语义检索质量。fake embedding 足够验证查询链路、请求体结构、filter 传递和结果解析。真实 embedding 会在后续单独学习。

### 自测 6

问题：

`permission_group` 是不是完整权限系统？

答案：

不是。它只是 RAG 检索侧权限过滤的教学版字段。真实权限系统还会结合用户身份、角色、租户、部门、数据权限、文档密级等信息。

### 自测 7

问题：

payload filter 和 score_threshold 分别解决什么？

答案：

payload filter 解决“在哪些资料里找”。score_threshold 解决“找到的内容够不够相关”。前者是范围控制，后者是相关性质量控制。

### 自测 8

问题：

为什么第 14 节 metadata 设计对第 16 节很重要？

答案：

因为 filter 依赖稳定的 payload 字段。第 14 节把 `source`、`doc_type`、`business_domain`、`permission_group` 等字段标准化并写入 payload，第 16 节才能按这些字段过滤。

## 十一、你应该能口述出的版本

你可以这样向别人解释本节：

```text
第 15 节我们已经能把用户问题转成 query embedding，然后去 Qdrant 里取回 top_k 个最相似 chunk。

但真实企业知识库不能只靠语义相似度，因为向量检索不知道业务权限、文档类型、业务领域和来源文件。比如客服入口只能看客服可见文档，订单问题最好只在订单领域里检索，不能把无权限或不相关领域的 chunk 交给模型。

所以第 16 节加入了 payload filter。payload 是 Qdrant point 里除 vector 之外的结构化业务信息，比如 source、doc_type、business_domain、permission_group。filter 就是按这些字段限制候选范围。

代码上，我们新增 filters.py，把 permission_group、business_domain、doc_type、source 这些项目内部参数转换成 Qdrant 的 filter JSON，比如 must + match.value。然后让 retriever 在调用 vector_store.query_similar() 时传入 payload_filter，vector_store 再把 filter 放进 Qdrant /points/query 请求体。

这样 top_k 的含义就变成：先在允许范围内过滤，再返回这个范围里最相似的最多 k 个 chunk。filter 控制范围，score 控制相似度排序。这个能力是后面做引用来源、权限控制、低相关拒答和完整 RAG 问答的基础。
```

## 十二、本节产出

新增：

- `projects/ai-service/app/rag/filters.py`
- `projects/ai-service/tests/test_rag_filters.py`

修改：

- `projects/ai-service/app/rag/vector_store.py`
- `projects/ai-service/app/rag/retriever.py`
- `projects/ai-service/scripts/rag_retrieve_smoke.py`
- `projects/ai-service/tests/test_rag_vector_store.py`
- `projects/ai-service/tests/test_rag_retriever.py`
- `README.md`
- `docs/learning-progress.md`
- `docs/learning-resources.md`
- `projects/ai-service/README.md`
- `projects/ai-service/app/rag/README.md`

## 十三、参考资料

- [Qdrant Filtering](https://qdrant.tech/documentation/search/filtering/)
- [Qdrant Query Points API](https://api.qdrant.tech/api-reference/search/query-points)
- [阶段 4 第 14 节：metadata 设计](rag-stage4-14-metadata-design.md)
- [阶段 4 第 15 节：基础 top_k 检索](rag-stage4-15-basic-top-k-retrieval.md)
