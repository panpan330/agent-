# 阶段 4 第 17 节：score_threshold：低相关内容不回答

## 本节状态

已完成。

本节接在第 16 节 payload filter 后面。

第 16 节解决的是：

```text
在哪些资料里找？
```

第 17 节解决的是：

```text
找到的资料够不够相关？
```

这两个问题都很重要。

只有限定范围还不够。即使我们已经限定：

```text
permission_group = customer_service
business_domain = order
```

向量数据库仍然可能返回一些“勉强相似”的 chunk。

真实 RAG 系统不能只要向量库返回了东西，就硬让模型回答。否则模型可能拿低相关资料凑答案，最后用户看到的是看似专业、实际不可靠的回答。

所以本节加入 `score_threshold`，让低相关检索结果不要进入后续回答链路。

## 本节学习目标

学完本节，你要能讲清楚：

1. 什么是检索结果的 `score`。
2. 什么是 `score_threshold`。
3. 为什么 `top_k` 不等于“这些结果都能用”。
4. 为什么低相关内容应该被过滤掉，而不是交给模型自由发挥。
5. `filter`、`top_k`、`score_threshold` 三者分别控制什么。
6. 为什么阈值不是随便拍脑袋定的，而是需要结合 embedding 模型、距离函数和业务数据调出来。
7. 为什么当前 fake embedding 只能验证阈值链路，不能用来决定真实阈值。
8. 本项目如何把 `score_threshold` 传给 Qdrant Query API。

## 本节暂时不学什么

本节不做这些事：

- 不做最终 RAG 回答生成，后面第 18 节再把检索结果交给模型。
- 不做完整“无资料拒答”接口，后面会在问答链路里系统讲。
- 不接真实 embedding 模型，真实阈值调优要等真实 embedding 接入后才有意义。
- 不做自动评测集和阈值调参实验，第 25 节会系统讲检索质量调优。
- 不做 rerank，后面会单独讲重排序。
- 不做混合检索，后面会讲关键词检索 + 向量检索。

## 一、基础知识铺垫

### 1. top_k 的结果为什么不一定都能用

第 15 节我们学过 `top_k`。

比如：

```text
top_k = 3
```

表示最多返回 3 个最相似的 chunk。

但这里有一个很容易误解的点：

```text
最相似，不等于足够相关。
```

如果一个知识库里完全没有用户问题相关资料，向量数据库仍然可以返回“相对最像”的几个。

比如用户问：

```text
公司年会抽奖规则是什么？
```

但我们的知识库只有：

- 订单发货规则
- 退款退货规则
- 物流查询 FAQ
- 账号安全 FAQ

向量数据库还是可能返回 top 3，因为它的任务是排序：

```text
从已有资料里找最像的几个
```

但这不代表这些资料真的能回答“年会抽奖规则”。

所以 RAG 里必须有第二层判断：

```text
这些 top_k 结果的相关性是否达到最低可用标准？
```

这就是 `score_threshold` 的作用。

### 2. 什么是 score

`score` 是向量数据库返回的检索分数。

它表示：

```text
query vector 和 chunk vector 的相似或距离程度
```

在本项目当前 Qdrant collection 里，我们使用的是：

```text
distance = Cosine
```

你可以先把它理解成：

```text
score 越高，向量越相似。
```

例如：

| chunk | score | 初步理解 |
| --- | --- | --- |
| 订单发货时效 chunk | 0.91 | 很相关 |
| 物流查询 chunk | 0.72 | 有点相关 |
| 账号安全 chunk | 0.31 | 可能不相关 |

但这里要注意：不同向量库、不同距离函数、不同 embedding 模型下，score 的含义和范围可能不一样。

Qdrant 官方也说明，`score_threshold` 返回的是分数优于阈值的点；具体是高于还是低于阈值，会受距离函数影响。对于 cosine similarity，可以先理解成只返回更高分的结果。

所以不要死记：

```text
score 一定在 0 到 1 之间。
score 一定越高越好。
0.8 一定是好阈值。
```

在我们当前学习项目里，为了降低理解难度，可以先按 cosine 的常见直觉理解：

```text
分数越高，越相似。
```

但以后做真实项目时，要回到你使用的向量库、距离函数和 embedding 模型文档确认。

### 3. 什么是 score_threshold

`score_threshold` 是最低相关性门槛。

它表达的是：

```text
分数达不到这个门槛的结果，不要返回。
```

例如：

```text
score_threshold = 0.75
```

可以理解成：

```text
只要相似度足够高的结果。
低于 0.75 的 chunk 不进入后续流程。
```

如果 Qdrant 原本找到：

| 排名 | chunk | score |
| --- | --- | --- |
| 1 | 订单发货时效 | 0.91 |
| 2 | 物流查询说明 | 0.72 |
| 3 | 账号安全 FAQ | 0.31 |

加上：

```text
score_threshold = 0.75
```

最终可能只返回：

| 排名 | chunk | score |
| --- | --- | --- |
| 1 | 订单发货时效 | 0.91 |

这说明：

```text
top_k 是最多返回多少个。
score_threshold 是低于什么质量不要。
```

### 4. 为什么低相关内容不能交给模型

如果把低相关 chunk 交给模型，模型通常不会主动说：

```text
这些资料不相关，我不能回答。
```

它可能会尝试从已有上下文里“拼出”一个答案。

这会导致几个问题：

1. 回答看起来很自然，但来源不支持。
2. 用户以为答案来自知识库，实际是模型补出来的。
3. 客服或业务人员可能基于错误答案做操作。
4. 后续引用来源时，引用的 chunk 也解释不了答案。
5. 系统评测时会出现“有检索、有回答，但回答不可信”的问题。

所以 RAG 不是：

```text
只要搜到东西，就让模型回答。
```

而应该是：

```text
搜到足够相关的资料，才让模型回答。
搜不到足够相关的资料，就拒答、提示无资料、转人工或换检索策略。
```

本节先实现第一步：

```text
低于阈值的 chunk 不返回。
```

后面完整问答链路会继续处理：

```text
没有可用 chunk 时，怎么给用户一个安全、诚实的回答。
```

### 5. filter、top_k、score_threshold 的分工

这三个参数经常一起出现，但含义完全不同。

| 参数 | 解决的问题 | 可以怎么理解 |
| --- | --- | --- |
| `filter` | 在哪些资料里找 | WHERE |
| `top_k` | 最多拿回几个 | LIMIT |
| `score_threshold` | 分数低到什么程度不要 | 最低质量线 |

用伪 SQL 帮助理解：

```sql
WHERE business_domain = 'order'
ORDER BY semantic_score DESC
LIMIT 3
只保留 semantic_score >= 0.75 的结果
```

这不是 Qdrant 真正执行的 SQL，只是为了理解。

对应到 RAG 检索控制：

```text
filter：先排除不该查的范围。
top_k：从剩下的范围里拿最多 k 个候选。
score_threshold：把候选里分数太低的排除。
```

### 6. 阈值为什么不能拍脑袋定

很多初学者会问：

```text
那我是不是直接设 0.8 就行？
```

不能这么简单。

阈值至少受这些因素影响：

1. embedding 模型
   不同模型生成的向量分布不同，同样的问题和文档，score 可能差很多。

2. 距离函数
   Cosine、Dot、Euclid 的分数含义不同。

3. chunk 切分方式
   chunk 太短、太长、上下文不完整，都会影响分数。

4. 数据领域
   客服 FAQ、法律条款、代码文档、商品描述的语义分布不同。

5. 问题表达方式
   用户问得越短、越口语化，分数可能越不稳定。

6. 是否使用 rerank
   如果后面有重排序模型，第一阶段向量检索阈值可以更宽一点。

所以真实系统里阈值通常要通过实验调出来。

基本做法是：

```text
准备一批用户问题
标注每个问题应该命中的文档或 chunk
跑检索
观察好结果和坏结果的 score 分布
选择一个能平衡召回率和准确率的阈值
```

### 7. 阈值太高和太低分别有什么问题

阈值太低：

```text
低相关内容也会进入模型上下文。
回答更容易跑偏或硬编。
```

阈值太高：

```text
很多本来能回答的问题被过滤掉。
系统经常说“没有资料”。
```

这就是典型取舍：

| 阈值策略 | 优点 | 风险 |
| --- | --- | --- |
| 较低阈值 | 更容易召回资料 | 噪声更多 |
| 较高阈值 | 回答更谨慎 | 漏掉可用资料 |
| 分业务调阈值 | 更贴近真实场景 | 配置更复杂 |

早期学习阶段先不要追求完美阈值。

本节重点是理解：

```text
RAG 需要有最低相关性门槛。
```

### 8. fake embedding 下为什么不能认真调阈值

当前项目还在用：

```text
DeterministicHashEmbeddingModel
```

它是确定性的 fake embedding。

它的作用是：

```text
让我们不用花钱调用真实模型，也能把 RAG 链路跑通。
```

但它不理解中文语义。

所以它返回的 score 不能代表真实相关性。

这意味着：

```text
当前 score_threshold 只能验证参数链路。
不能用当前分数决定真实业务阈值。
```

等后面接入真实 embedding 模型后，才有必要认真观察：

- 订单问题命中订单文档的分数分布。
- 不相关问题的分数分布。
- 不同 top_k 下分数变化。
- 不同 chunk_size 下分数变化。

## 二、本节主题系统讲解

### 1. 第 16 节到第 17 节的链路变化

第 16 节：

```text
retrieve_top_k(
    query,
    permission_group="customer_service",
    business_domain="order",
)
-> Qdrant filter
-> 返回过滤范围内的 top_k
```

第 17 节：

```text
retrieve_top_k(
    query,
    permission_group="customer_service",
    business_domain="order",
    score_threshold=0.75,
)
-> Qdrant filter
-> Qdrant score_threshold
-> 只返回范围正确且分数足够的 top_k
```

检索控制从两层变成三层：

```text
范围控制 -> 数量控制 -> 质量控制
```

### 2. `retrieve_top_k()` 新增了什么

现在可以传：

```python
score_threshold: float | None = None
```

调用示例：

```python
retrieve_top_k(
    "订单超过 72 小时没有发货怎么办？",
    embedding_model=embedding_model,
    vector_store=vector_store,
    top_k=3,
    permission_group="customer_service",
    business_domain="order",
    score_threshold=0.75,
)
```

这句话表达的是：

```text
只在客服可见的订单领域文档里检索，
最多返回 3 个 chunk，
并且低于 0.75 分的结果不要。
```

这比单纯 `top_k=3` 更接近真实 RAG。

### 3. 为什么入口层要校验 score_threshold

本节新增了最小校验：

```text
score_threshold 必须是数字，不能是 True、False 或字符串。
```

为什么 `True` 不行？

因为 Python 里 `bool` 是 `int` 的子类。

如果不特别排除，`True` 可能被当成数字 `1`。

这会让调用方传错参数却不报错。

所以我们明确拒绝：

```python
score_threshold=True
```

也拒绝：

```python
score_threshold="0.8"
```

因为字符串不是数值。

### 4. 为什么不把 score_threshold 限死在 0 到 1

你可能会想：

```text
score_threshold 不就应该是 0 到 1 吗？
```

在当前项目的 cosine 直觉下，这么理解方便入门。

但代码层面没有硬写：

```text
必须 0 <= score_threshold <= 1
```

原因是：

1. Qdrant 支持不同距离函数。
2. 不同距离函数下 score 的含义不同。
3. Dot product 的分数不一定被限制在 0 到 1。
4. 更底层的 vector store 适配器不应该过早把所有距离函数都按 cosine 限制。

所以当前代码只校验：

```text
它必须是一个数字。
```

具体设置多少，交给使用方根据模型、距离函数和数据来决定。

### 5. `QdrantVectorStore.query_similar()` 新增了什么

新增参数：

```python
score_threshold: float | None = None
```

如果调用方传了阈值，Qdrant 请求体会增加：

```json
{
  "score_threshold": 0.75
}
```

完整请求体可以像这样：

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
  },
  "score_threshold": 0.75
}
```

这里的含义是：

```text
用 query 向量查询。
最多返回 3 条。
返回 payload，不返回 vector。
只查客服可见的订单领域文档。
只返回分数优于 0.75 的点。
```

### 6. 为什么让 Qdrant 做阈值过滤

我们也可以在 Python 里先拿回 top_k，再自己过滤：

```python
chunks = vector_store.query_similar(...)
chunks = [chunk for chunk in chunks if chunk.score >= 0.75]
```

但本节选择把 `score_threshold` 传给 Qdrant。

原因是：

1. Qdrant 原生支持这个参数。
2. 让向量库少返回无用结果，减少网络传输。
3. 分数含义和距离函数由向量库更清楚。
4. 上层代码更直接表达“我只要超过阈值的结果”。

不过你也要知道：

```text
后端仍然可以在更上层做二次防御。
```

比如将来 RAG pipeline 里可以检查：

```text
如果 chunks 为空，就不要调用模型生成答案。
```

### 7. 本节 smoke 脚本为什么用低阈值

脚本：

```text
projects/ai-service/scripts/rag_retrieve_smoke.py
```

现在带了：

```python
score_threshold=0.2
```

这个阈值不是推荐业务阈值。

原因是当前还是 fake embedding。

这里设置一个较低阈值，只是为了验证：

```text
score_threshold 参数能顺着 retrieve_top_k -> vector_store -> Qdrant 请求体传下去。
```

它不代表真实 RAG 系统应该用 `0.2`。

等真实 embedding 模型接入后，才会重新讨论：

```text
真实订单知识库里，0.6、0.7、0.8 分别意味着什么。
```

## 三、用例子理解低相关拒答

### 例子 1：有高分结果

用户问：

```text
订单超过 72 小时没有发货怎么办？
```

检索结果：

| chunk | score |
| --- | --- |
| 订单超时未发货处理规则 | 0.91 |
| 正常发货时效 | 0.84 |
| 物流查询说明 | 0.62 |

如果：

```text
score_threshold = 0.75
```

保留：

```text
0.91
0.84
```

过滤：

```text
0.62
```

这时后续模型可以基于前两个 chunk 回答。

### 例子 2：全是低分结果

用户问：

```text
公司年会抽奖规则是什么？
```

检索结果：

| chunk | score |
| --- | --- |
| 账号安全 FAQ | 0.35 |
| 订单发货规则 | 0.31 |
| 退款退货说明 | 0.29 |

如果：

```text
score_threshold = 0.75
```

最终返回：

```text
空结果
```

这不是坏事。

它说明系统没有找到足够可靠的资料。

后续问答层应该更诚实地说：

```text
当前知识库没有找到足够相关的资料，无法根据知识库回答这个问题。
```

而不是强行编一个答案。

### 例子 3：阈值太高导致漏答

用户问：

```text
订单多久发货？
```

检索结果：

| chunk | score |
| --- | --- |
| 正常发货时效 | 0.73 |
| 超时未发货处理 | 0.69 |

如果：

```text
score_threshold = 0.8
```

结果为空。

但这两个 chunk 实际上可能已经可用。

这说明阈值太高会漏掉本来能回答的问题。

所以阈值不是越高越好，而是要调。

## 四、常见误区

### 误区 1：top_k=3 就说明有 3 条可用资料

不对。

`top_k=3` 只是最多返回 3 条最相似结果。

这 3 条可能都很相关，也可能只是“没有更好的，所以它们排前面”。

### 误区 2：score_threshold 越高系统越好

不对。

阈值越高，系统越谨慎，但也越容易漏答。

好的阈值不是看起来严格，而是在你的数据集上表现稳定。

### 误区 3：一个阈值可以适用于所有业务

不一定。

订单规则、退款政策、账号安全 FAQ、法律条款、代码文档，它们的问题表达和文档结构不同，分数分布也可能不同。

真实系统里可能会分场景设置不同阈值。

### 误区 4：当前 fake embedding 的分数可以用来确定真实阈值

不可以。

fake embedding 不理解语义。

它只能帮我们验证工程链路：

```text
参数能传下去。
请求体是对的。
结果能解析。
测试能覆盖。
```

### 误区 5：score_threshold 可以替代 filter

不可以。

`filter` 和 `score_threshold` 解决的是不同问题。

```text
filter：不该查的资料不要查。
score_threshold：查出来但不够相关的资料不要用。
```

权限问题不能靠分数解决。

低相关问题也不能靠权限过滤解决。

## 五、本节代码改动说明

### 1. `app/rag/retriever.py`

`retrieve_top_k()` 新增：

```python
score_threshold: float | None = None
```

然后把它传给：

```python
vector_store.query_similar(...)
```

这表示上层调用方可以用一个业务参数控制最低相关性门槛。

同时新增最小校验：

```text
score_threshold 必须是数字。
```

### 2. `app/rag/vector_store.py`

`QdrantVectorStore.query_similar()` 新增：

```python
score_threshold: float | None = None
```

请求体新增逻辑：

```python
if score_threshold is not None:
    request_body["score_threshold"] = score_threshold
```

这意味着：

```text
不传阈值时，请求体保持和以前一样。
传阈值时，才把 score_threshold 发给 Qdrant。
```

这种写法保持了向后兼容。

### 3. `scripts/rag_retrieve_smoke.py`

烟测脚本现在传：

```python
score_threshold=0.2
```

注意：这只是 fake embedding 阶段的链路验证阈值，不是业务推荐值。

### 4. 测试文件

本节补充：

- `test_rag_retriever.py`
  验证 `retrieve_top_k()` 会把 `score_threshold` 传给 vector store，并拒绝非法阈值。

- `test_rag_vector_store.py`
  验证 `QdrantVectorStore.query_similar()` 会把 `score_threshold` 放进 Qdrant 请求体。

测试仍然不调用真实 Qdrant。

真实 Qdrant 联调用 smoke script 手动验证。

## 六、手动验证思路

如果 VMware Ubuntu 里的 Qdrant 正在运行，可以在 Windows 的 `ai-service` 目录执行：

```powershell
uv run python scripts/rag_retrieve_smoke.py
```

当前脚本会做：

```text
query -> fake embedding -> Qdrant Query API
filter: permission_group=customer_service, business_domain=order
score_threshold: 0.2
```

如果虚拟机没开，本节自动化测试仍然可以跑，不需要 Qdrant。

如果手动 smoke 返回空结果，不要立刻判断代码错了。排查顺序应该是：

1. Qdrant 是否启动。
2. collection 是否存在。
3. collection 里是否有 points。
4. filter 是否和 payload 字段匹配。
5. score_threshold 是否过高。
6. 当前 fake embedding 分数是否本来就不稳定。

## 七、本节练习

### 练习 1：解释 top_k 和 score_threshold 的区别

题目：

请解释下面两个参数分别控制什么：

```text
top_k = 3
score_threshold = 0.75
```

参考答案：

`top_k=3` 表示最多返回 3 个最相似的 chunk。

`score_threshold=0.75` 表示低于最低相关性门槛的结果不要返回。

也就是说，`top_k` 控制数量上限，`score_threshold` 控制质量底线。

### 练习 2：判断过滤后的结果

题目：

检索结果如下：

| chunk | score |
| --- | --- |
| A | 0.92 |
| B | 0.76 |
| C | 0.58 |

如果 `score_threshold=0.75`，哪些 chunk 会保留？

参考答案：

保留 A 和 B。C 的分数低于 0.75，会被过滤掉。

### 练习 3：分析空结果

题目：

`top_k=5`，但是加了 `score_threshold=0.8` 后返回空列表，这一定说明向量库坏了吗？

参考答案：

不一定。

可能是没有足够相关的资料，也可能是阈值太高，或者当前 filter 太严格，或者 fake embedding 分数不稳定。应该先检查 Qdrant 是否有数据、payload filter 是否匹配、阈值是否合理。

### 练习 4：解释为什么低相关内容不应该交给模型

题目：

为什么低相关 chunk 不应该继续交给大模型生成回答？

参考答案：

因为模型可能会基于低相关资料硬凑答案，导致回答看起来流畅但没有可靠来源支撑。RAG 的目标是根据知识库回答，不是让模型在资料不足时自由发挥。

### 练习 5：说明当前 fake embedding 的限制

题目：

为什么现在不能根据 fake embedding 的 score 来决定真实业务阈值？

参考答案：

因为 fake embedding 不理解语义，只是为了让链路可运行。它生成的分数不能代表真实问题和真实文档之间的语义相关性。真实阈值要等真实 embedding 模型接入后，用实际数据评估。

## 八、自测问题

### 自测 1

问题：

`score_threshold` 解决的是候选范围问题，还是相关性质量问题？

答案：

相关性质量问题。候选范围主要由 `filter` 控制。

### 自测 2

问题：

如果没有任何 chunk 达到 `score_threshold`，后续问答层应该怎么做？

答案：

不应该强行调用模型编答案。更合理的是返回“没有找到足够相关资料”，或者进入转人工、扩大检索范围、换检索策略等兜底流程。

### 自测 3

问题：

为什么本项目代码没有把 `score_threshold` 限制成 0 到 1？

答案：

因为不同距离函数和向量库的 score 含义不同。当前项目使用 cosine 时可以先按分数越高越相关理解，但底层适配器不应该过早把所有情况都限制成 0 到 1。

### 自测 4

问题：

`filter` 和 `score_threshold` 能不能互相替代？

答案：

不能。`filter` 控制查哪些资料，`score_threshold` 控制查出来的资料是否足够相关。权限过滤不能靠分数替代，低相关拒绝也不能靠权限过滤替代。

### 自测 5

问题：

阈值太高会带来什么风险？

答案：

会漏掉本来可用的资料，导致系统经常返回“没有找到足够相关资料”。

### 自测 6

问题：

阈值太低会带来什么风险？

答案：

低相关资料也会进入模型上下文，模型更容易生成没有来源支撑的回答。

### 自测 7

问题：

为什么 `score_threshold=True` 应该被拒绝？

答案：

因为 Python 里 `bool` 是 `int` 的子类，如果不排除，`True` 可能被当成数字 `1`。这会掩盖调用方传错参数的问题。

### 自测 8

问题：

真实阈值应该怎么确定？

答案：

准备一批真实或接近真实的用户问题，标注正确文档或 chunk，跑检索，观察相关和不相关结果的 score 分布，再选择能平衡召回率和准确率的阈值。

## 九、你应该能口述出的版本

你可以这样向别人解释本节：

```text
前面我们已经能用 top_k 从 Qdrant 取回最相似的 chunk，也能用 payload filter 限定权限和业务范围。但 top_k 只表示“最多拿回几个最相似结果”，不表示这些结果都足够相关。如果知识库里没有真正相关的资料，向量库仍然会返回相对最像的结果。

所以本节加入 score_threshold。它是最低相关性门槛，低于阈值的检索结果不要返回。这样后续模型不会拿低相关资料硬凑答案。

filter、top_k、score_threshold 分工不同：filter 控制在哪些资料里找，top_k 控制最多返回几个，score_threshold 控制分数低到什么程度不要。当前项目把 score_threshold 从 retrieve_top_k 传到 QdrantVectorStore.query_similar，再放进 Qdrant /points/query 请求体。

但是阈值不是随便定的。它和 embedding 模型、距离函数、chunk 切分、业务数据有关。当前我们还在用 fake embedding，所以只能验证工程链路，不能用当前分数决定真实阈值。真实阈值要等真实 embedding 接入后通过评测调出来。
```

## 十、本节产出

修改：

- `projects/ai-service/app/rag/retriever.py`
- `projects/ai-service/app/rag/vector_store.py`
- `projects/ai-service/scripts/rag_retrieve_smoke.py`
- `projects/ai-service/tests/test_rag_retriever.py`
- `projects/ai-service/tests/test_rag_vector_store.py`
- `README.md`
- `docs/learning-progress.md`
- `docs/learning-resources.md`
- `projects/ai-service/README.md`
- `projects/ai-service/app/rag/README.md`

新增：

- `notes/rag-stage4-17-score-threshold.md`

## 十一、参考资料

- [Qdrant Query Points API](https://api.qdrant.tech/api-reference/search/query-points)
- [Qdrant Similarity Search](https://qdrant.tech/documentation/search/search/)
- [Qdrant Search Points API：score_threshold](https://api.qdrant.tech/api-reference/search/points)
- [阶段 4 第 15 节：基础 top_k 检索](rag-stage4-15-basic-top-k-retrieval.md)
- [阶段 4 第 16 节：payload filter](rag-stage4-16-payload-filter.md)
