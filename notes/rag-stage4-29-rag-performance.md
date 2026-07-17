# 阶段 4 第 29 节：RAG 性能：缓存、批处理、超时、降级

## 本节状态

已完成。

本节接在第 28 节 `RAG 安全：文档权限、Prompt Injection、敏感信息` 之后。

到目前为止，RAG 主链路已经具备：

```text
文档加载
-> chunk 切分
-> metadata
-> embedding
-> Qdrant 入库
-> top_k 检索
-> payload filter
-> score_threshold
-> 混合检索
-> rerank
-> 安全检查
-> 生成回答
-> 引用来源
-> 无资料兜底
```

这说明系统功能上已经比较完整。

但真实项目里，只能跑通还不够。

还要考虑：

```text
慢不慢
贵不贵
稳不稳
失败时怎么办
缓存会不会串权限
超时会不会拖垮整个服务
```

这些就是本节的主题：RAG 性能和工程可用性。

## 本节学习目标

学完本节，你应该能解释清楚：

1. RAG 性能瓶颈通常在哪里。
2. RAG 里的延迟、吞吐、成本、稳定性分别是什么意思。
3. 为什么 embedding 适合批处理。
4. query embedding 能不能缓存。
5. 检索结果缓存适合什么场景。
6. 模型回答缓存为什么更危险。
7. 为什么缓存 key 不能只用 query 文本。
8. 为什么缓存 key 必须包含权限、过滤条件、top_k、score_threshold、collection、embedding 模型等信息。
9. TTL 缓存是什么。
10. timeout 为什么必须存在。
11. near_timeout 和 timed_out 有什么区别。
12. 什么是降级。
13. 降级和失败有什么区别。
14. 为什么本节只做学习版性能工具，不接 Redis、不改 Qdrant、不真实调用模型。

## 本节暂时不学什么

本节暂时不学：

1. 不接 Redis。
2. 不接真实分布式缓存。
3. 不改 Qdrant 配置。
4. 不真实调用 embedding API。
5. 不真实调用大模型。
6. 不做异步任务队列。
7. 不做 Celery、Kafka、RabbitMQ。
8. 不做 Prometheus/Grafana 监控。
9. 不做压测。
10. 不做复杂熔断器。
11. 不需要打开 VMware Ubuntu 或 Qdrant。

原因是：

你现在更需要先理解性能工程的基本概念。

如果一上来就接 Redis、监控、队列和压测工具，很容易变成背工具命令，而不是理解 RAG 为什么慢、哪里能缓存、缓存有什么风险、超时和降级应该怎么设计。

## 一、基础知识铺垫

### 1. 性能不是只看“快不快”

很多初学者一听性能，就会想：

```text
怎么让接口更快？
```

但工程里的性能至少包括：

1. 延迟。
2. 吞吐。
3. 成本。
4. 稳定性。
5. 可恢复性。

延迟是：

```text
一次请求从开始到结束要多久。
```

吞吐是：

```text
单位时间内能处理多少请求。
```

成本是：

```text
每次请求消耗多少模型调用、向量库调用、CPU、内存和网络资源。
```

稳定性是：

```text
高峰、慢服务、外部依赖抖动时系统还能不能正常工作。
```

可恢复性是：

```text
失败后能不能兜底、重试、降级，而不是整个链路卡死。
```

### 2. RAG 为什么容易慢

RAG 比普通聊天多了很多步骤。

普通聊天大概是：

```text
用户问题 -> 模型 -> 回答
```

RAG 是：

```text
用户问题
-> query embedding
-> 向量库检索
-> 可能还要关键词检索
-> 可能还要混合融合
-> 可能还要 rerank
-> 可能还要安全检查
-> 构造 prompt
-> 调用模型
-> 返回回答和引用
```

每多一步，就多一份延迟和失败可能。

### 3. RAG 常见性能瓶颈

常见瓶颈包括：

1. 文档入库时 embedding 慢。
2. 文档入库时批量太小，API 调用太多。
3. query embedding 每次都重新算。
4. 向量库检索慢。
5. top_k 设置过大。
6. rerank 候选太多。
7. prompt 上下文太长。
8. 大模型生成慢。
9. 外部 API 超时。
10. 缓存 key 设计不合理导致缓存命中率低。
11. 缓存 key 设计错误导致越权复用。

### 4. RAG 的性能优化不应该破坏正确性

性能优化不能只追求快。

如果为了快，把权限过滤忽略了，就会越权。

如果为了快，把旧缓存一直用下去，就会回答过期政策。

如果为了快，把 top_k 调得太小，就会召回不到关键资料。

如果为了省钱，把安全检查去掉，就可能泄露敏感信息。

所以 RAG 性能优化必须同时看：

```text
速度
准确性
权限
安全
成本
稳定性
```

### 5. 什么是缓存

缓存就是：

把某次计算或查询结果临时保存起来。

下次遇到相同条件时，不重新计算，直接复用。

例如：

```text
第一次问：退款多久到账？
系统检索 Qdrant 得到 chunk A、chunk B
把这个结果放进缓存

短时间内再次问同样问题
直接从缓存取 chunk A、chunk B
```

这样可以减少：

1. embedding 调用。
2. 向量库调用。
3. 网络延迟。
4. API 成本。

### 6. 缓存不是越多越好

缓存有风险。

常见风险：

1. 缓存过期后还被使用。
2. 权限不同的用户共用缓存。
3. filter 不同但命中同一缓存。
4. 知识库更新后还用旧结果。
5. query 看起来一样，但业务语境不同。
6. 缓存占用内存过大。

所以缓存必须有边界。

### 7. 为什么缓存 key 很重要

缓存 key 决定：

```text
什么情况下算“同一个请求”
```

如果缓存 key 设计错，系统会复用错误结果。

错误示例：

```text
cache_key = query
```

看似合理，但有严重问题。

同样是：

```text
退款多久到账？
```

不同用户权限可能不同。

不同业务域可能不同。

不同 top_k 可能不同。

不同 score_threshold 可能不同。

不同 collection 可能不同。

不同 embedding 模型可能不同。

这些条件不同，就不能简单共用缓存。

### 8. RAG 检索缓存 key 应该包含什么

一个更合理的检索缓存 key 至少应该考虑：

```text
query
top_k
score_threshold
permission_group
business_domain
doc_type
source
embedding_model
embedding_dimension
collection_name
```

这不是说永远只能这些字段。

而是表达原则：

```text
凡是会影响检索结果的条件，都应该进入 cache key。
```

### 9. 为什么缓存 key 不直接暴露 query

用户问题可能包含敏感内容。

比如：

```text
我的手机号 13800138000 退款多久到账？
```

如果你把完整 query 写进缓存 key、日志或监控系统，就可能泄露隐私。

所以本节代码用 query hash。

也就是：

```text
query -> sha256 hash -> 放进 cache key components
```

最终 key 看起来像：

```text
rag_retrieval:5418ef74...
```

不会直接暴露原始问题。

### 10. 什么是 TTL

TTL 是 Time To Live。

意思是：

```text
缓存最多能活多久。
```

比如：

```text
ttl_seconds = 60
```

表示缓存 60 秒后过期。

TTL 的意义是：

1. 避免长期使用旧结果。
2. 限制内存占用。
3. 让知识库更新后逐步生效。
4. 降低缓存污染风险。

### 11. 为什么知识库更新会影响缓存

如果文档更新了，旧检索结果可能不再准确。

例如：

旧政策：

```text
退款 1 到 3 个工作日到账
```

新政策：

```text
退款 3 到 5 个工作日到账
```

如果缓存还返回旧 chunk，系统就可能给出过期答案。

所以真实项目里通常要结合：

1. TTL。
2. collection version。
3. document version。
4. refresh timestamp。
5. 主动清理缓存。

本节先只学 TTL 和 cache key。

### 12. query embedding 能不能缓存

可以，但要谨慎。

query embedding 缓存的 key 通常要包含：

```text
query hash
embedding model
embedding dimension
provider
```

因为同一个 query，用不同 embedding 模型会得到不同向量。

如果模型或维度变了，还复用旧向量，就会检索错误。

### 13. 检索结果能不能缓存

可以。

检索结果缓存比较常见。

适合场景：

1. 热门问题。
2. FAQ 类问题。
3. 知识库短时间内不频繁变化。
4. 同一权限范围内的重复查询。

不适合场景：

1. 高度个性化问题。
2. 强实时数据。
3. 权限变化频繁。
4. 文档刚更新后必须立刻生效。

### 14. 模型回答能不能缓存

可以，但更危险。

模型回答缓存不仅受检索结果影响，还受：

1. prompt 模板。
2. 模型版本。
3. temperature。
4. 用户角色。
5. 输出格式。
6. 当前日期。
7. 安全策略。
8. 引用来源。

如果缓存模型回答，要非常小心。

本节不做模型回答缓存。

原因是：

对初学阶段来说，先缓存检索结果更容易理解，也更容易控制风险。

### 15. 什么是批处理

批处理就是：

把多个任务合成一批处理。

例如 embedding：

```text
一次传 1 条文本
```

改成：

```text
一次传 64 条文本
```

这样可以减少 API 调用次数和网络开销。

### 16. 为什么 embedding 适合批处理

文档入库时通常有很多 chunk。

比如 1000 个 chunk。

如果每个 chunk 调一次 embedding API，就是 1000 次请求。

如果 batch_size=64，大概只需要：

```text
ceil(1000 / 64) = 16 次请求
```

这会明显降低：

1. 网络开销。
2. 请求排队。
3. provider 限流风险。
4. 调用成本管理复杂度。

### 17. 批处理不是越大越好

batch_size 太大也有问题：

1. 请求体过大。
2. 超过 provider 限制。
3. 单次失败影响更多文本。
4. 响应时间更长。
5. 内存占用更高。

所以 batch_size 要结合：

1. provider 文档限制。
2. 文本长度。
3. 超时设置。
4. 重试策略。
5. 业务吞吐目标。

### 18. 什么是 timeout

timeout 是超时。

意思是：

```text
某一步最多等多久。
```

例如：

```text
embedding_timeout = 5s
vector_store_timeout = 5s
llm_timeout = 30s
```

如果没有 timeout，一个外部服务卡住，整个请求可能一直挂着。

这会占用线程、连接、内存，最终拖垮服务。

### 19. timeout 不是失败处理的全部

timeout 只是发现问题。

发现之后还要决定：

1. 是否重试。
2. 是否用缓存。
3. 是否返回无资料。
4. 是否返回兜底说明。
5. 是否记录日志。
6. 是否触发告警。

所以 timeout 和降级经常一起设计。

### 20. 什么是 near_timeout

near_timeout 是接近超时。

比如 timeout 是 1 秒。

如果某次调用用了 850ms，虽然没超时，但已经很接近。

这说明系统有性能风险。

本节用：

```text
near_timeout_ratio = 0.8
```

也就是超过 timeout 的 80% 就标记为 near_timeout。

near_timeout 可以帮助你提前发现：

```text
现在还没崩，但已经越来越慢。
```

### 21. 什么是降级

降级是：

当完整链路不可用时，系统退到一个能力更弱但仍可控的方案。

例如：

```text
向量库慢 -> 使用短期缓存检索结果
模型生成慢 -> 返回“已找到资料但模型暂时不可用”
安全检查后无 safe chunks -> 返回不能根据知识库回答
```

降级不是假装成功。

降级是明确告诉系统和用户：

```text
当前完整能力不可用，使用更保守的处理方式。
```

### 22. 降级和失败的区别

失败是：

```text
系统直接报错或无响应。
```

降级是：

```text
系统知道某一步失败了，但还能给出安全、可解释、可恢复的结果。
```

例如：

失败：

```text
500 Internal Server Error
```

降级：

```text
当前知识库服务暂时不可用，无法根据知识库回答这个问题。
```

或者：

```text
正在使用最近一次可用的知识库检索结果生成回答。
```

### 23. RAG 里常见降级方式

常见降级方式：

1. 使用短期缓存的检索结果。
2. 不调用模型，返回无资料兜底。
3. 只返回安全来源，不生成自然语言答案。
4. 降低 top_k。
5. 跳过非必要 rerank。
6. 暂停复杂多路召回。
7. 提示稍后重试。

注意：

降级不能越过安全边界。

不能因为系统慢，就跳过权限过滤或安全检查。

### 24. 本节代码的学习价值

本节代码不是生产级性能系统。

它的学习价值是：

1. 学会构造安全的缓存 key。
2. 理解 TTL 缓存。
3. 理解缓存命中、未命中、过期和驱逐。
4. 理解 embedding batch plan。
5. 理解 timeout 状态分类。
6. 理解降级决策。
7. 为后续 Redis、监控、压测、熔断打基础。

## 二、本节主题系统讲解

### 1. 本节新增 `app/rag/performance.py`

本节新增文件：

```text
projects/ai-service/app/rag/performance.py
```

它是 RAG 内部性能学习工具。

它不负责真实 Redis。

它不调用 Qdrant。

它不调用模型。

它负责把性能概念用代码表达出来：

```text
cache key
TTL cache
batch plan
operation timing
degradation decision
```

### 2. `RagCacheKey` 表示什么

`RagCacheKey` 表示一个缓存 key。

它包含：

```text
namespace
digest
components
```

`namespace` 用来区分缓存类型。

例如：

```text
rag_retrieval
```

`digest` 是对 components 做 hash 后得到的字符串。

`components` 是参与构造 key 的条件。

注意：

最终用于缓存的是：

```text
namespace:digest
```

而不是原始 query。

### 3. `build_retrieval_cache_key()` 做什么

这个函数构造检索缓存 key。

它会接收：

```text
query
top_k
score_threshold
permission_group
business_domain
doc_type
source
embedding_model
embedding_dimension
collection_name
```

然后生成稳定 key。

同样条件会生成同样 key。

条件变化会生成不同 key。

### 4. 为什么 `permission_group` 要进入 cache key

这是本节最重要的点之一。

同样的问题：

```text
退款多久到账？
```

客服权限和内部员工权限看到的资料可能不同。

如果缓存 key 不包含权限，可能发生：

```text
内部员工先问，缓存了内部资料
客服用户后问，同样 query 命中缓存
客服用户拿到内部资料
```

这就是缓存越权。

所以权限条件必须进入 cache key。

### 5. 为什么 `top_k` 要进入 cache key

`top_k=3` 和 `top_k=10` 返回的候选数量不同。

如果 key 不包含 top_k，就可能出现：

```text
想要 10 条结果
却命中了之前 top_k=3 的缓存
```

这会影响召回质量。

### 6. 为什么 `score_threshold` 要进入 cache key

`score_threshold=0.8` 和 `score_threshold=0.5` 返回结果不同。

阈值越高，过滤越严格。

如果 key 不包含阈值，就可能复用错误范围的检索结果。

### 7. 为什么 embedding 模型和维度要进入 cache key

同一个文本，用不同 embedding 模型可能得到完全不同的向量空间。

同一个模型，不同维度也可能影响检索结果。

所以缓存检索结果时要考虑：

```text
embedding_model
embedding_dimension
```

否则模型升级后还复用旧缓存，会造成结果不一致。

### 8. 为什么 collection name 要进入 cache key

不同 collection 可能对应不同知识库。

例如：

```text
learning_rag_chunks
product_docs
internal_policy_docs
```

同样 query 在不同 collection 里的结果不同。

所以 collection name 也要进入 key。

### 9. `InMemoryTtlCache` 表示什么

`InMemoryTtlCache` 是学习版内存 TTL 缓存。

它支持：

```text
set
get
clear
stats
```

它会记录：

```text
hit_count
miss_count
set_count
evicted_count
current_entries
```

这能帮助你理解缓存运行状态。

### 10. 什么是 cache hit

cache hit 是缓存命中。

意思是：

```text
根据 key 找到了未过期缓存
```

命中后可以直接复用结果。

本节测试里：

```text
cache.set("key-1", value)
cache.get("key-1")
```

会让 `hit_count` 加 1。

### 11. 什么是 cache miss

cache miss 是缓存未命中。

常见原因：

1. key 不存在。
2. key 存在但已过期。
3. 条件变化导致 key 不同。
4. 缓存被驱逐。

miss 后通常要重新计算或重新查询。

### 12. 什么是 cache eviction

eviction 是缓存驱逐。

意思是：

```text
缓存因为过期或空间不足被删除。
```

本节内存缓存有两个驱逐场景：

1. TTL 到期。
2. 超过 max_entries 后驱逐最旧项。

### 13. 为什么本节用内存缓存

因为本节目标是学习概念。

内存缓存优点：

1. 简单。
2. 无外部依赖。
3. 容易测试。
4. 能讲清楚 TTL、hit、miss、eviction。

缺点：

1. 进程重启会丢。
2. 多实例之间不共享。
3. 容量有限。
4. 不适合生产分布式部署。

真实项目里可以换成 Redis。

但 Redis 不改变核心概念。

### 14. `RagBatchPlan` 表示什么

`RagBatchPlan` 表示批处理计划。

字段包括：

```text
item_count
batch_size
batch_count
batches
```

例如 5 条文本，batch_size=2：

```text
batch 1: 2 条
batch 2: 2 条
batch 3: 1 条
```

这样你能直观看到批处理怎么切。

### 15. `build_batch_plan()` 做什么

这个函数把字符串列表拆成批次。

它会拒绝：

1. batch_size <= 0。
2. 空字符串。
3. 只有空格的字符串。

为什么拒绝空文本？

因为 embedding 不应该处理空文本。

空文本进入 embedding 会浪费调用，也可能触发 provider 错误。

### 16. `RagOperationStage` 表示什么

这个枚举表示 RAG 链路阶段：

```text
embedding
vector_store
rerank
generation
security
```

性能观察要知道慢在哪里。

如果只知道“RAG 慢”，没法优化。

要知道：

```text
是 embedding 慢？
是向量库慢？
是 rerank 慢？
是模型生成慢？
是安全检查慢？
```

### 17. `assess_operation_timing()` 做什么

这个函数根据耗时和 timeout 判断状态。

状态有：

```text
ok
near_timeout
timed_out
```

例如：

```text
timeout = 1s
elapsed = 300ms -> ok
elapsed = 850ms -> near_timeout
elapsed = 1000ms -> timed_out
```

这能帮助你理解性能监控里的“慢但未失败”。

### 18. 为什么 near_timeout 很有价值

如果只看 timed_out，你只能在失败后才知道问题。

near_timeout 可以提前暴露风险。

比如最近 10 分钟里：

```text
vector_store near_timeout 次数越来越多
```

说明向量库可能越来越慢。

你可以提前处理，而不是等大量请求超时。

### 19. `choose_degradation_decision()` 做什么

这个函数根据当前失败阶段和可用资源，选择降级策略。

它考虑两个条件：

```text
has_cached_retrieval
has_safe_chunks
```

如果有缓存，优先使用缓存。

如果没有缓存，但有 safe chunks，可以返回安全兜底。

如果都没有，返回 no_context 类兜底。

### 20. 为什么优先用缓存

如果向量库暂时失败，但有短期缓存的检索结果，这时可以使用缓存。

原因是：

1. 缓存结果来自之前成功的检索。
2. 短 TTL 内通常可接受。
3. 比直接报错体验更好。

但必须注意：

缓存也要满足权限、过滤条件和安全条件。

不能随便拿旧缓存。

### 21. 为什么有 safe chunks 时可以安全兜底

如果模型生成失败，但检索和安全检查已经成功，系统至少知道：

```text
有一些安全资料
```

这时可以返回：

```text
当前模型回答暂时不可用，但已检索到相关资料，请稍后重试或查看来源资料。
```

这比 500 错误更友好。

但不能伪装成模型已经回答。

### 22. 为什么没有缓存也没有 safe chunks 时返回 no_context

如果没有缓存，也没有安全资料，系统就没有可靠依据。

这时最稳妥的是：

```text
当前知识库服务暂时不可用，无法根据知识库回答这个问题。
```

不要编造，不要硬答。

### 23. 本节脚本做什么

本节新增：

```text
scripts/rag_performance_preview.py
```

它演示：

1. 构造检索缓存 key。
2. 写入内存 TTL 缓存。
3. 命中缓存。
4. 构造 batch plan。
5. 判断 near_timeout。
6. 选择使用缓存的降级策略。

它不连接 Qdrant。

不需要 VMware。

不调用真实模型。

## 三、本节代码改动说明

### 1. 新增 `app/rag/performance.py`

这个文件是本节核心。

它包含：

```text
RagCacheKey
InMemoryTtlCache
RagCacheStats
RagBatchPlan
RagOperationTiming
RagDegradationDecision
build_retrieval_cache_key()
build_batch_plan()
assess_operation_timing()
choose_degradation_decision()
```

### 2. 新增 `build_retrieval_cache_key()`

这个函数最重要。

它体现了缓存正确性的底层原则：

```text
影响检索结果的条件必须进入 cache key。
```

本节不会把原始 query 放进 key。

而是放 query hash。

### 3. 新增 `InMemoryTtlCache`

这是学习版 TTL 缓存。

它能演示：

1. set 写入。
2. get 命中。
3. TTL 过期。
4. max_entries 驱逐。
5. stats 统计。

真实项目里可以换成 Redis。

但 Redis 也会有类似概念：

```text
key
value
TTL
hit
miss
eviction
```

### 4. 新增 `build_batch_plan()`

这个函数演示批处理拆分。

虽然项目里 embedding 已经有 `split_texts_into_batches()`，但本节单独做 `RagBatchPlan` 是为了让你看到：

```text
多少条输入
每批多少条
一共几批
每批内容是什么
```

它更适合学习和调试。

### 5. 新增 `assess_operation_timing()`

这个函数把耗时变成状态：

```text
ok
near_timeout
timed_out
```

它不负责真正中断请求。

真实请求中断通常由 HTTP client、SDK timeout 或异步任务框架负责。

本节先学习“如何描述和判断耗时状态”。

### 6. 新增 `choose_degradation_decision()`

这个函数把失败后的选择结构化。

它返回：

```text
mode
reason
should_call_model
should_use_cache
user_message
```

这样降级不是散落在代码里的 if/else 文案，而是一个明确的决策对象。

### 7. 新增 `test_rag_performance.py`

测试覆盖：

1. cache key 稳定。
2. cache key 不暴露原始 query。
3. 权限、top_k 变化会改变 key。
4. TTL 缓存命中。
5. TTL 过期。
6. 缓存容量满时驱逐最旧项。
7. batch plan 拆分。
8. 非法 batch 参数被拒绝。
9. 耗时状态分类。
10. 降级优先使用缓存。
11. 无缓存但有 safe chunks 时安全兜底。
12. 都没有时返回 no_context。

### 8. 新增 `rag_performance_preview.py`

这个脚本用于手动观察。

运行：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run python scripts/rag_performance_preview.py
```

会看到：

```text
cache_key
cache_hit
cache_stats
batch_count
timing
degradation
```

## 四、运行结果解释

预览脚本输出里有：

```text
cache_key: rag_retrieval:5418ef74...
```

说明最终缓存 key 是 hash，不直接暴露用户问题。

输出里有：

```text
cache_hit: ['refund_return_policy_chunk_0004']
```

说明缓存命中，返回了之前保存的检索结果。

输出里有：

```text
batch_count: 3
```

说明 5 条文本按 batch_size=2 被拆成 3 批。

输出里有：

```text
status=near_timeout
```

说明 850ms / 1s 已经接近超时。

输出里有：

```text
mode=use_cached_retrieval
```

说明如果向量库失败且有缓存，系统可以优先用缓存降级。

## 五、常见误区

### 误区 1：缓存 key 只用 query 就够了

不够。

RAG 检索结果受权限、过滤条件、top_k、score_threshold、collection 和 embedding 模型影响。

只用 query 会导致错误复用，甚至越权。

### 误区 2：缓存能解决所有性能问题

不能。

缓存只能优化重复请求。

第一次请求、个性化请求、强实时请求仍然要走真实链路。

### 误区 3：TTL 越长越好

不一定。

TTL 越长，命中率可能越高，但旧数据风险越大。

### 误区 4：批处理越大越好

不一定。

batch 太大可能超过 provider 限制，也可能增加单次失败影响范围。

### 误区 5：timeout 设置得越长越稳

不对。

timeout 太长会让请求长时间占用资源，可能拖垮服务。

### 误区 6：降级就是随便返回一个答案

不是。

降级必须安全、诚实、可解释。

不能把不确定内容包装成确定答案。

### 误区 7：性能优化可以先跳过安全检查

不可以。

性能优化不能突破权限和安全边界。

缓存、降级、批处理都必须尊重安全策略。

## 六、本节练习

### 练习 1：解释 RAG 的常见性能瓶颈

问题：

RAG 哪些步骤容易成为性能瓶颈？

参考答案：

embedding、向量库检索、混合检索、rerank、上下文构造、大模型生成、外部 API 网络延迟和安全检查都可能成为瓶颈。

### 练习 2：解释缓存 key 为什么不能只用 query

问题：

为什么 `cache_key = query` 是危险设计？

参考答案：

因为同一个 query 在不同权限、filter、top_k、score_threshold、collection、embedding 模型下结果可能不同，只用 query 会导致错误复用和越权风险。

### 练习 3：解释 TTL

问题：

TTL 是什么？

参考答案：

TTL 是缓存存活时间，表示缓存最多保存多久，过期后需要重新计算或重新查询。

### 练习 4：解释 batch size

问题：

batch_size=64 表示什么？

参考答案：

表示一次批处理最多处理 64 条输入，例如一次 embedding API 请求最多发送 64 条文本。

### 练习 5：解释 near_timeout

问题：

near_timeout 有什么价值？

参考答案：

它表示操作还没真正超时，但已经接近超时，可以提前暴露性能风险，帮助监控和优化。

### 练习 6：解释降级

问题：

什么是降级？

参考答案：

降级是在完整链路不可用时，退到一个能力更弱但安全可控的方案，例如使用缓存、返回无资料兜底或提示稍后重试。

### 练习 7：判断缓存字段

问题：

检索缓存 key 是否应该包含 permission_group？

参考答案：

应该。否则不同权限用户可能复用同一缓存，产生越权。

### 练习 8：判断缓存字段

问题：

embedding 模型升级后，旧检索缓存还能无条件使用吗？

参考答案：

不能。embedding 模型变化会影响向量空间和检索结果，缓存 key 应该包含 embedding 模型和维度。

### 练习 9：判断降级策略

问题：

向量库失败，但有短 TTL 检索缓存，可以怎么处理？

参考答案：

可以使用缓存检索结果降级，但前提是缓存 key 包含权限和检索条件，并且缓存没有过期。

### 练习 10：判断降级策略

问题：

模型生成超时，但已有 safe chunks，能不能编造一个完整答案？

参考答案：

不能。可以返回安全兜底，说明模型回答暂时不可用，不能伪装成模型已经根据资料生成了答案。

## 七、自测问题

### 自测 1

问题：

RAG 性能只看响应时间吗？

答案：

不是。还要看吞吐、成本、稳定性和失败后的可恢复性。

### 自测 2

问题：

缓存命中是什么意思？

答案：

根据 key 找到了未过期缓存，可以直接复用。

### 自测 3

问题：

缓存未命中可能有哪些原因？

答案：

key 不存在、缓存过期、条件变化导致 key 不同、缓存被驱逐。

### 自测 4

问题：

检索缓存 key 为什么要包含 score_threshold？

答案：

因为不同 score_threshold 会返回不同结果范围。

### 自测 5

问题：

检索缓存 key 为什么要包含 collection_name？

答案：

因为不同 collection 对应不同知识库，同样 query 的结果不同。

### 自测 6

问题：

embedding 为什么适合批处理？

答案：

文档入库通常有大量 chunk，批处理能减少 API 请求次数、网络开销和限流风险。

### 自测 7

问题：

timeout 的作用是什么？

答案：

限制某一步最多等待多久，避免外部服务卡住导致整个请求长时间占用资源。

### 自测 8

问题：

near_timeout 是失败吗？

答案：

不是。它表示还没失败，但已经接近超时，是性能风险信号。

### 自测 9

问题：

降级可以跳过权限过滤吗？

答案：

不可以。降级也必须遵守权限和安全边界。

### 自测 10

问题：

模型回答缓存为什么比检索结果缓存更危险？

答案：

因为模型回答受 prompt、模型版本、角色、当前日期、安全策略和引用来源等更多因素影响，更容易错误复用。

### 自测 11

问题：

内存缓存适合生产分布式多实例共享吗？

答案：

不适合。生产多实例通常需要 Redis 这类共享缓存。

### 自测 12

问题：

如果没有缓存，也没有 safe chunks，系统应该怎么降级？

答案：

应该返回不能根据知识库回答的兜底，而不是硬答或编造。

## 八、你应该能口述出的版本

你可以这样讲：

RAG 性能不是单纯追求接口更快，而是要同时考虑延迟、吞吐、成本、稳定性和失败后的降级。RAG 链路比普通聊天长很多，embedding、向量库、rerank、模型生成都可能变慢。性能优化常见手段包括缓存、批处理、timeout 和降级，但这些手段不能破坏权限、安全和答案正确性。

检索缓存 key 不能只用用户问题，因为同一个问题在不同权限、filter、top_k、score_threshold、collection 和 embedding 模型下结果不同。本节用 query hash 和这些检索参数构造稳定 key，避免原始问题直接出现在 key 中。批处理用于减少 embedding 等批量任务的 API 调用次数。timeout 用来限制外部依赖最多等待多久。降级是在完整链路失败时，退到使用缓存、返回安全兜底或无资料兜底，而不是直接崩溃或编造答案。

## 九、本节产出

本节新增：

```text
projects/ai-service/app/rag/performance.py
projects/ai-service/tests/test_rag_performance.py
projects/ai-service/scripts/rag_performance_preview.py
notes/rag-stage4-29-rag-performance.md
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
uv run pytest tests/test_rag_performance.py -q
uv run python scripts/rag_performance_preview.py
```

## 十、下一节衔接

下一节进入：

```text
阶段 4 第 30 节：阶段 4 主线项目验收和复盘
```

原因是：

阶段 4 主线已经学完 RAG 基础、检索增强、安全和性能基础。

第 30 节会整理：

1. 阶段 4 已完成什么。
2. RAG 主链路现在长什么样。
3. 每个模块负责什么。
4. 哪些能力是学习版。
5. 哪些能力后续需要生产化。
6. Milvus 对比为什么放在阶段 4 后半段继续学。
