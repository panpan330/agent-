# 阶段 4 第 23 节：文档更新、删除、重新入库

## 本节状态

已完成。

本节是 RAG 知识库从“只能新增内容”走向“能维护内容”的一节。

前面我们已经完成：

- 文档加载
- 文本清洗
- chunk 切分
- metadata 设计
- embedding 生成
- Qdrant upsert 写入
- top_k 检索
- payload filter
- score_threshold
- 检索结果交给模型生成回答
- 引用来源
- no_context 兜底
- RAG 错误处理
- RAG fake 测试工具

这些能力能让一批文档第一次进入知识库，也能让用户基于这些文档问答。

但真实项目不会停留在“第一次入库”。

真实企业知识库一定会遇到：

- 文档内容被修改
- 文档被删除
- 文档从一个目录移动到另一个目录
- 文档标题改了
- 文档权限改了
- 文档重复上传
- chunk 切分策略调整
- embedding 模型更换
- 向量库里的旧数据需要清理

所以第 23 节要解决的问题是：

> 当源文档变化时，向量库里的旧 chunks 怎么办？

本节代码补齐了三类能力：

- Qdrant 适配层支持按 payload filter 删除 points
- 入库层支持按 `source` 删除某个文档的旧 chunks
- 入库层支持“重新入库目录”：先删除同 `source` 的旧 chunks，再写入新 chunks

本节新增或修改的核心文件：

- `projects/ai-service/app/rag/vector_store.py`
- `projects/ai-service/app/rag/ingestion.py`
- `projects/ai-service/tests/rag_fakes.py`
- `projects/ai-service/tests/test_rag_vector_store.py`
- `projects/ai-service/tests/test_rag_ingestion.py`
- `projects/ai-service/tests/test_rag_fakes.py`

## 本节学习目标

学完本节，你应该能讲清楚：

1. 为什么 RAG 不能只做新增入库。
2. 为什么文档更新后，旧 chunk 不清理会污染答案。
3. `upsert` 能解决什么问题，不能解决什么问题。
4. 为什么要按 `source` 删除旧 chunks。
5. `source`、`chunk_id`、Qdrant point id 各自负责什么。
6. 为什么重新入库常见做法是“先删旧，再写新”。
7. “先删后插”有什么风险。
8. 为什么真实生产系统还会引入文档版本、状态字段、任务队列和审计日志。
9. 本节代码为什么把删除能力放在 vector store 适配层，把业务流程放在 ingestion 层。
10. 如何用 fake 测试“删除旧数据再重新入库”的编排逻辑。

## 本节暂时不学什么

本节先不做这些：

- 不做文档上传 HTTP API。
- 不做前端文件管理页面。
- 不做后台任务队列。
- 不做分布式锁。
- 不做文档版本回滚。
- 不做生产级双写、灰度 collection 或蓝绿切换。
- 不真实调用 embedding API。
- 不要求打开 VMware 或真实 Qdrant。

如果要做真实 Qdrant smoke 验证，就需要打开 VMware Ubuntu 并启动 Qdrant。

但本节主学习内容不依赖真实 Qdrant。

## 一、基础知识铺垫

### 1. 知识库不是一次性数据

很多初学 RAG 的人会把知识库理解成：

```text
准备文档 -> 切分 -> embedding -> 写入向量库 -> 完事
```

这个理解只适合 demo。

真实企业里的知识库更像一个长期维护的数据系统。

比如客服知识库：

- 退款规则可能每个月变一次。
- 发货规则可能因为节假日调整。
- 账号安全策略可能因为风控升级而变化。
- 某些过期活动说明必须下线。
- 某些内部文档只能给特定权限组看。

如果 RAG 系统只会新增，不会更新和删除，那么它会逐渐变成一个“过期知识堆”。

模型表面上还在回答，但回答依据可能已经不可信。

所以企业知识库 RAG 里，“入库”不是一次性动作，而是持续的数据维护过程。

### 2. 文档更新后，旧 chunk 为什么会污染答案

假设原文档 `refund-return-policy.md` 里写着：

```text
退款将在 7 个工作日内处理。
```

后来业务规则改成：

```text
退款将在 3 个工作日内处理。
```

如果我们只是把新文档重新切 chunk 并 upsert，但旧 chunk 没有被删除，就可能同时存在两批内容：

```text
旧 chunk：退款将在 7 个工作日内处理。
新 chunk：退款将在 3 个工作日内处理。
```

用户问：

```text
退款多久能到账？
```

向量检索可能召回旧 chunk，也可能召回新 chunk，甚至两个都召回。

这会造成几个问题：

- 模型可能回答旧规则。
- 模型可能把两个规则混在一起。
- 引用来源看起来正常，但内容已经过期。
- 用户无法判断哪个答案是最新的。

这就是旧 chunk 污染。

RAG 的难点不只是“把内容放进去”，还包括“把不该存在的内容清理掉”。

### 3. 删除不是数据库里的附属功能，而是知识库质量的一部分

在普通 CRUD 系统里，删除通常是基础功能。

但在 RAG 系统里，很多人会忽略删除，因为他们只关注：

- 怎么切 chunk
- 怎么 embedding
- 怎么检索
- 怎么生成回答

可是一旦文档会变化，删除就直接影响知识库质量。

你可以这样理解：

```text
新增入库决定知识库能知道什么。
删除旧数据决定知识库不会错误地记住什么。
```

RAG 系统里，错误记住旧内容有时比不知道更危险。

因为“不知道”可以返回 no_context。

但“错误知道”会生成看似确定的错误答案。

### 4. chunk 和源文档是什么关系

一个源文档会被切成多个 chunk。

例如：

```text
refund-return-policy.md
  -> refund_return_policy_chunk_0001
  -> refund_return_policy_chunk_0002
  -> refund_return_policy_chunk_0003
  -> refund_return_policy_chunk_0004
```

在向量库里，每个 chunk 通常会变成一个 point。

也就是说，Qdrant 里不是直接存“一篇文档”，而是存“多个 point”。

每个 point 大致包含：

```text
point id
vector
payload
```

payload 里会保存：

```text
source
title
section
chunk_id
content
permission_group
business_domain
doc_type
```

所以删除一篇文档时，不能只删一条记录。

你要删除的是：

```text
payload.source == "refund-return-policy.md" 的所有 points
```

这就是本节按 `source` 删除的原因。

### 5. `source` 在本项目里的定位

在当前项目里，`source` 表示知识文档相对于知识库目录的来源路径。

例如：

```text
order-shipping-policy.md
refund-return-policy.md
account-security-faq.md
logistics-tracking-faq.txt
```

它的作用不是给用户展示标题。

它的核心作用是：

- 标识 chunk 属于哪份源文档。
- 支持按文档来源过滤检索。
- 支持按文档来源删除旧 chunks。
- 支持回答引用来源。

你可以把 `source` 理解成“文档级别的业务主键”。

它不一定是数据库主键，但在我们的 RAG 流程里，它承担了“这批 chunks 来自同一份文档”的识别职责。

### 6. `chunk_id` 在本项目里的定位

`chunk_id` 表示某个 chunk 的稳定编号。

例如：

```text
refund_return_policy_chunk_0001
refund_return_policy_chunk_0002
```

它比 `source` 更细。

关系是：

```text
source = 一份文档
chunk_id = 这份文档里的某一个 chunk
```

在本项目里，`chunk_id` 还会被转换成稳定的 Qdrant point id。

也就是说，同一个 `chunk_id` 反复入库，会得到同一个 point id。

这让 upsert 具备幂等性基础。

### 7. Qdrant point id 在本项目里的定位

Qdrant 的 point id 是向量库内部用来定位 point 的 id。

我们当前没有直接把 `chunk_id` 原样作为 point id，而是用：

```text
uuid5(namespace, chunk_id)
```

生成稳定 UUID。

这样做的好处是：

- 同一个 `chunk_id` 永远得到同一个 point id。
- Qdrant 接收到相同 point id 的 upsert 时，会覆盖旧 point。
- point id 格式更规范。

它们三者的关系可以这样理解：

```text
source      文档级标识：这批 chunks 属于哪份文档
chunk_id    chunk 级标识：这份文档里的第几个知识片段
point_id    向量库级标识：Qdrant 里实际写入的 point 编号
```

### 8. upsert 是什么

`upsert` 是 update + insert 的组合词。

它的意思是：

```text
如果记录不存在，就插入。
如果记录已存在，就更新。
```

在 Qdrant 里，如果你用相同 point id upsert 一个 point，旧 point 会被新 point 覆盖。

这对 RAG 很重要。

因为重新入库时，部分 chunk_id 可能保持不变。

这时 upsert 可以避免同一个 point id 重复插入。

### 9. upsert 能解决什么

upsert 能解决：

- 同一个 chunk_id 重复入库。
- 同一个 point id 的 vector 更新。
- 同一个 point id 的 payload 更新。
- 脚本重复执行导致的部分重复写入。

比如：

```text
shipping_chunk_0001 第一次写入
shipping_chunk_0001 第二次写入
```

只要 point id 稳定，第二次会覆盖第一次。

这让入库脚本具备一定的幂等性。

### 10. upsert 不能解决什么

upsert 不是万能的。

它不能解决“旧 chunk 数量比新 chunk 多”的问题。

举例：

旧文档切出 5 个 chunk：

```text
policy_chunk_0001
policy_chunk_0002
policy_chunk_0003
policy_chunk_0004
policy_chunk_0005
```

新文档变短，只切出 3 个 chunk：

```text
policy_chunk_0001
policy_chunk_0002
policy_chunk_0003
```

如果只 upsert 新的 3 个 chunk，那么旧的：

```text
policy_chunk_0004
policy_chunk_0005
```

仍然留在向量库。

这两个旧 chunk 以后仍然可能被检索出来。

所以仅靠 upsert 不够。

文档重新入库时，通常需要先清理这份文档的旧 chunks。

### 11. 为什么本节选择“先按 source 删除，再 upsert”

本节采用的策略是：

```text
读取文档
-> 切分 chunks
-> 生成 embeddings
-> ensure collection
-> 按 source 删除旧 points
-> upsert 新 points
```

关键点是：

```text
按 source 删除，而不是按 chunk_id 一个个删除。
```

原因是：

- 文档更新后，新旧 chunk 数量可能不同。
- 文档切分后，有些旧 chunk_id 可能不再出现。
- 按 source 删除能一次清理这份文档的所有旧 chunks。
- 然后再写入新 chunks，向量库里就只剩这份文档的最新版本。

这是初版 RAG 系统里很常见、也相对容易理解的策略。

### 12. 为什么不是先删再 embed

注意本节实现里，顺序不是：

```text
先删旧数据 -> 再加载、切分、embedding
```

而是：

```text
先加载、切分、embedding 成功 -> 再删旧数据 -> 再 upsert
```

这样设计是为了降低风险。

如果 embedding 阶段失败，而你已经先删了旧数据，那知识库里这份文档就没了。

所以更稳妥的顺序是：

```text
先确认新数据准备好了，再动旧数据。
```

本节代码就是这样处理的。

### 13. “先删后插”的风险

“先删后插”仍然有风险。

风险发生在：

```text
删除旧 points 成功
upsert 新 points 失败
```

这时向量库里会短暂或长期缺失这份文档。

在当前学习项目里，这个风险可以接受，因为我们是在做基础 RAG 工程。

但在生产系统里，可能需要更复杂的策略。

### 14. 生产系统可能怎么做

生产系统里，常见增强方案包括：

1. 文档版本号

   每个 chunk 增加：

   ```text
   document_id
   document_version
   is_active
   ```

   新版本先写入，再把旧版本标记为 inactive。

2. 软删除

   不直接删除 point，而是设置：

   ```text
   deleted = true
   ```

   检索时 filter 排除 deleted。

3. 后台任务队列

   文档更新触发异步任务：

   ```text
   pending -> processing -> succeeded / failed
   ```

4. 审计日志

   记录：

   ```text
   谁更新了文档
   更新了哪份文档
   删除了哪些旧版本
   写入了多少新 chunk
   ```

5. 灰度 collection

   先写入新 collection，验证后再切换别名。

这些属于后续工程化内容。

本节先掌握最基础、最关键的一步：

```text
知道旧 chunks 必须清理，并能按 source 清理。
```

### 15. 删除文档和重新入库不是一回事

这两个动作要分清：

```text
删除文档：
源文档已经不应该存在，向量库里对应 chunks 也要删除。

重新入库：
源文档仍然存在，但内容可能变了，需要清理旧 chunks，再写入新 chunks。
```

删除文档只需要：

```text
source -> payload filter -> delete points
```

重新入库需要：

```text
load -> split -> embed -> delete old source chunks -> upsert new chunks
```

所以本节有两个高层函数：

- `delete_document_from_vector_store()`
- `refresh_directory_in_vector_store()`

它们服务的场景不同。

### 16. 为什么删除要走 payload filter

向量库里的 point 是一个个 chunk。

如果你知道每个 point id，可以按 point id 删除。

但文档更新后，旧 chunk_id 和旧 point id 未必都知道。

更通用的办法是按 payload filter 删除。

也就是：

```text
删除 payload.source == "refund-return-policy.md" 的所有 points
```

这正好依赖前面第 14 节 metadata 设计。

如果当初没有把 `source` 写进 payload，现在就很难按文档清理旧数据。

这说明 metadata 不是装饰信息。

metadata 会直接决定你的 RAG 系统后续能不能维护。

### 17. 为什么本节不按 title 删除

`title` 是给人看的。

`source` 更适合做机器识别。

标题可能变化：

```text
退款退货规则
退款与退货规则
售后退款退货规则
```

但文件来源通常更稳定：

```text
refund-return-policy.md
```

所以本节按 `source` 删除。

以后如果做真实文档管理系统，更推荐引入：

```text
document_id
```

它会比文件名更稳定。

### 18. 为什么本节暂时不引入 document_id

`document_id` 是更生产化的设计。

但当前项目还没有文档上传 API，也没有数据库存文档表。

如果现在硬引入 `document_id`，我们还要补：

- 文档表
- 上传接口
- 文档 id 生成
- 文档和文件路径映射
- 文档版本
- 删除状态

这些会把本节重点拉偏。

所以当前阶段用 `source` 作为文档级标识。

等后面做完整知识库 API 或后台管理时，再把 `source` 升级为更正式的 `document_id`。

### 19. 重新入库和幂等性的关系

幂等性的意思是：

```text
同一个操作执行一次和执行多次，最终结果应该一致。
```

文档重新入库希望接近幂等：

```text
同一批文档 refresh 一次
同一批文档 refresh 两次
最终向量库里都应该只有这一批文档的最新 chunks
```

本节靠两个设计接近这个目标：

- 按 `source` 删除旧 chunks。
- 用稳定 `chunk_id` 生成稳定 point id。

执行多次 refresh 时：

```text
先删旧的
再写新的
```

最终结果不会越写越多。

### 20. 为什么重新入库不是简单重复跑 ingest

`ingest_directory_to_vector_store()` 的语义是：

```text
把当前目录里的文档写入向量库。
```

它没有表达：

```text
这些文档是替换旧版本。
```

所以它不会主动删除旧 chunks。

第 23 节新增 `refresh_directory_in_vector_store()`，它的语义更明确：

```text
用当前目录里的文档刷新向量库里同 source 的旧内容。
```

这两个函数的区别不是代码形式，而是业务语义不同。

### 21. 本节和上一节 fake 测试的关系

上一节我们专门补了：

- `FakeEmbeddingModel`
- `FakeVectorStoreReader`
- `FakeVectorStoreWriter`

本节马上用到了它们。

如果没有 fake writer，我们要测试重新入库，就可能需要真实 Qdrant。

但有 fake 后，我们可以断言：

- 是否调用了 `ensure_collection`
- 是否调用了 `delete_points_by_filter`
- 删除时传的 filter 是否包含正确 `source`
- 是否在删除后调用了 `upsert_embedded_chunks`
- 失败是否映射成统一 RAG 错误

这就是测试工具的价值：

它让后续业务能力可以更快、更稳地扩展。

### 22. 本节的安全边界

删除操作天然比新增更危险。

所以本节保持几个边界：

- 只按明确的 `source` 删除。
- 不允许空 filter 删除。
- 单元测试不连真实 Qdrant。
- 不提供“一键删除 collection”。
- 不在自动化测试里真实删除 Qdrant 数据。

这符合我们前面一直坚持的原则：

```text
自动化测试稳定、可重复、不依赖真实外部服务。
真实服务验证留给 smoke test。
```

## 二、本节主题系统讲解

### 1. 第 23 节在 RAG 主线里的位置

阶段 4 目前已经能完成基础问答链路：

```text
知识文档
-> load
-> split
-> embed
-> store
-> retrieve
-> generate
-> answer + citations
```

第 23 节补的是“知识库维护链路”：

```text
文档变更
-> 找到旧 chunks
-> 删除旧 chunks
-> 写入新 chunks
```

没有这一步，RAG 系统只能演示，不能长期使用。

因为长期使用的系统必须处理数据变化。

### 2. 本节新增的三个关键词

本节你要重点记住三个关键词：

```text
delete
refresh
source
```

它们的关系是：

```text
delete：删除向量库里的旧 points
refresh：重新入库一份或一批文档
source：定位一份文档对应的所有 chunks
```

以后你看到知识库更新问题，第一反应应该是：

```text
我靠什么字段找到旧数据？
我什么时候删除旧数据？
我如何保证删除不会误删？
我如何保证新数据写入失败时能发现问题？
```

### 3. Qdrant 适配层新增 `delete_points_by_filter()`

本节在 `QdrantVectorStore` 里新增方法：

```python
def delete_points_by_filter(
    self,
    payload_filter: Mapping[str, Any],
    *,
    wait: bool = True,
) -> None:
```

它做的事是：

```text
payload_filter
-> normalize_payload_filter()
-> POST /collections/{collection_name}/points/delete
-> body = {"filter": normalized_filter}
-> 检查 HTTP 状态
-> 检查 Qdrant status == "ok"
```

这属于适配层能力。

适配层不关心你为什么删除。

它只负责把项目内部的 filter 结构转换成 Qdrant HTTP 请求。

### 4. 为什么删除方法接收 payload filter

删除方法没有写死 `source`。

它接收的是：

```python
payload_filter: Mapping[str, Any]
```

这样以后它不只可以按 source 删除。

未来还可以支持：

```text
按 doc_type 删除
按 business_domain 删除
按 permission_group 删除
按 document_version 删除
按 deleted 标记删除
```

适配层保持通用。

业务层决定具体 filter。

这是分层设计里很重要的一点。

### 5. 为什么空 filter 要拒绝

删除接口最怕空条件。

如果某个向量库把空 filter 理解成“匹配所有 points”，那后果就是清空数据。

本节做了防线：

```python
normalized_filter = normalize_payload_filter(payload_filter)
if normalized_filter is None:
    raise ValueError("payload_filter must not be empty")
```

虽然 `normalize_payload_filter({})` 本身也会拒绝空 dict，但这里的判断让删除方法的意图更清楚：

```text
删除必须带明确条件。
```

### 6. 入库层新增 `VectorStoreUpdater`

原来入库层只需要一个 writer：

```python
class VectorStoreWriter(Protocol):
    ensure_collection(...)
    upsert_embedded_chunks(...)
```

第 23 节新增：

```python
class VectorStoreUpdater(VectorStoreWriter, Protocol):
    delete_points_by_filter(...)
```

这表示：

```text
普通入库只需要写能力。
重新入库和删除文档需要更新能力。
```

这种拆分能让接口语义更清晰。

不是所有“能写入”的对象都一定应该支持删除。

但“更新型入库”必须支持删除。

### 7. 新增 `delete_document_from_vector_store()`

这个函数服务“文档被删除”的场景。

它的核心流程是：

```text
source
-> build_payload_filter(source=source)
-> vector_store.delete_points_by_filter(filter)
-> 返回 RagDeletionResult
```

它不加载文档。

因为文档都已经被删了，你可能已经没有文件可读。

这时你只需要知道旧文档的 `source`。

比如：

```python
delete_document_from_vector_store(
    "refund-return-policy.md",
    vector_store=vector_store,
)
```

含义就是：

```text
删除向量库里所有来自 refund-return-policy.md 的 chunks。
```

### 8. 新增 `refresh_directory_in_vector_store()`

这个函数服务“重新入库目录”的场景。

它的流程是：

```text
load documents
-> split chunks
-> embed chunks
-> extract sources
-> ensure collection
-> delete old chunks for every source
-> upsert new chunks
-> return RagIngestionResult
```

它和普通 `ingest_directory_to_vector_store()` 很像，但多了：

```text
delete old chunks for every source
```

这就是“新增入库”和“刷新入库”的本质区别。

### 9. 为什么先 embed 再 delete

本节刷新流程里，embedding 在 delete 前面。

原因是：

```text
新数据没准备好之前，不要动旧数据。
```

如果文档加载失败、切分失败、embedding 失败，那旧数据还留在向量库里。

至少系统还能继续基于旧知识回答。

如果一开始就删除旧数据，然后 embedding 失败，这份知识就直接没了。

所以当前顺序更稳。

### 10. 为什么 delete 在 upsert 前面

如果 upsert 在 delete 前面，会出现另一类问题。

假设旧文档 5 个 chunks，新文档 3 个 chunks。

你先 upsert 新的 3 个 chunks：

```text
0001 覆盖
0002 覆盖
0003 覆盖
0004 旧数据仍然存在
0005 旧数据仍然存在
```

然后如果再按 source 删除，就会把刚写入的新 3 个也删掉。

所以对于“按 source 删除旧 chunks”这种策略，顺序必须是：

```text
delete old source chunks
-> upsert new source chunks
```

如果想先写新再删旧，就需要引入版本字段，例如：

```text
document_version = v2
```

然后删除：

```text
source == xxx AND document_version != v2
```

这是后续生产化策略。

### 11. 本节为什么不返回删除数量

`delete_document_from_vector_store()` 没有返回真实删除了多少 points。

原因是：

```text
当前 Qdrant 删除接口更偏操作确认，不适合在本节假设它一定返回删除条数。
```

我们当前返回：

```python
RagDeletionResult(
    source=...,
    collection_name=...,
)
```

它表达的是：

```text
这个删除请求已经按指定 source 发给 vector store。
```

后续如果要做更完整的数据治理，可以再加入：

- 删除前 scroll 统计
- 删除后 count 验证
- 操作日志
- 后台任务状态

但这些不是本节重点。

### 12. `replaced_source_count` 表示什么

`RagIngestionResult` 新增：

```python
replaced_source_count: int = Field(default=0, ge=0)
```

它表示：

```text
本次 refresh 处理了多少个不同的 source。
```

注意它不是删除的 point 数量。

例如一个目录里有 4 份文档：

```text
account-security-faq.md
logistics-tracking-faq.txt
order-shipping-policy.md
refund-return-policy.md
```

刷新目录时，`replaced_source_count` 是 4。

它表示这 4 个 source 的旧 chunks 都被请求删除过。

### 13. 本节为什么继续用 fake 测试

重新入库测试要验证的是业务编排：

```text
加载文档了吗？
切 chunk 了吗？
生成 embedding 了吗？
按 source 删除旧 chunks 了吗？
写入新 chunks 了吗？
错误映射对吗？
```

这些不需要真实 Qdrant。

如果用真实 Qdrant，测试会受到：

- Docker 是否启动
- 端口是否可达
- collection 是否存在
- 上一次测试数据是否残留
- 网络是否稳定

这些因素影响。

所以单元测试继续用 fake。

真实 Qdrant 验证后面可以作为 smoke test。

### 14. FakeVectorStoreWriter 为什么也要支持 delete

上一节 fake writer 已经能记录：

```text
ensure_collection 调用
upsert_embedded_chunks 调用
```

本节补上：

```text
delete_points_by_filter 调用
```

这样测试就能断言：

```text
删除条件里是不是 source
wait 参数有没有传下去
删除失败会不会被映射成 RAG_VECTOR_STORE_FAILED
```

fake 的能力跟着业务边界增长。

这就是可维护测试工具的意义。

### 15. 本节代码和前面知识点的连接

第 23 节不是孤立的一节。

它用到了前面很多知识点：

```text
第 11 节：文档加载，拿到 source
第 12 节：chunk 切分，生成 chunk_id
第 13 节：embedding 和 Qdrant upsert
第 14 节：metadata 设计，让 source 进入 payload
第 16 节：payload filter
第 21 节：RAG 错误映射
第 22 节：fake vector store 测试工具
```

这就是工程学习里很重要的感觉：

后面的功能不是凭空出现，而是不断复用前面打下的基础。

## 三、本节代码改动说明

### 1. `QdrantVectorStore.delete_points_by_filter()`

新增位置：

```text
projects/ai-service/app/rag/vector_store.py
```

核心职责：

```text
把项目里的 payload filter 变成 Qdrant 删除 points 的 HTTP 请求。
```

它的调用形式类似：

```python
store.delete_points_by_filter(
    {"must": [{"key": "source", "match": {"value": "shipping.md"}}]},
    wait=True,
)
```

发送给 Qdrant 的 body 是：

```json
{
  "filter": {
    "must": [
      {
        "key": "source",
        "match": {
          "value": "shipping.md"
        }
      }
    ]
  }
}
```

这里的关键点是：

- 方法名强调“按 filter 删除”。
- 不允许空 filter。
- 保持 `wait` 参数。
- HTTP 错误统一映射成 `QdrantVectorStoreError`。
- Qdrant 返回非 ok 状态也视为失败。

### 2. `VectorStoreUpdater`

新增位置：

```text
projects/ai-service/app/rag/ingestion.py
```

它继承了 `VectorStoreWriter` 的能力，并增加删除能力。

语义是：

```text
能刷新知识库的 vector store，不仅要能写，还要能删。
```

普通新增入库还可以只依赖 `VectorStoreWriter`。

需要重新入库时才依赖 `VectorStoreUpdater`。

### 3. `delete_document_from_vector_store()`

新增位置：

```text
projects/ai-service/app/rag/ingestion.py
```

它负责单文档删除：

```text
source -> payload filter -> delete points
```

这个函数适合未来接：

```text
DELETE /knowledge-documents/{source}
```

或后台文档管理动作。

当前还没有做 HTTP API，但业务函数已经准备好了。

### 4. `refresh_directory_in_vector_store()`

新增位置：

```text
projects/ai-service/app/rag/ingestion.py
```

它负责目录级重新入库：

```text
加载目录内文档
切分 chunks
生成 embeddings
提取所有 source
ensure collection
逐个 source 删除旧 chunks
upsert 新 chunks
返回结果
```

这一版只处理当前目录里存在的文档。

如果某个文档已经从目录里删掉，`refresh_directory_in_vector_store()` 不一定知道它曾经存在过。

这种场景要调用：

```python
delete_document_from_vector_store(old_source, vector_store=...)
```

或者未来引入文档清单表。

### 5. `FakeVectorStoreWriter` 新增删除记录

新增能力：

```text
delete_calls
last_delete_call
delete_error
delete_points_by_filter()
```

它让测试可以检查：

```text
删除条件是否正确
wait 参数是否正确
删除失败是否正确抛出
```

这不是为了模拟 Qdrant 全部行为。

它只模拟当前业务编排需要的边界。

### 6. 测试新增了哪些关键覆盖

本节测试主要覆盖：

- Qdrant 删除适配层是否请求 `/points/delete`
- 删除请求 body 是否包含 `filter`
- 空 delete filter 是否拒绝
- fake writer 是否能记录 delete 调用
- refresh 是否按每个 source 删除旧 chunks
- refresh 是否再 upsert 新 chunks
- delete source 是否去掉前后空格
- 删除失败是否映射成统一 RAG 错误

测试不是本节的重点讲解对象。

你只需要理解：

```text
测试证明我们没有把“重新入库”写成“重复新增”。
```

## 四、关键流程图

### 1. 普通新增入库

```text
load documents
-> split chunks
-> embed chunks
-> ensure collection
-> upsert chunks
```

普通新增入库不删除旧数据。

适合第一次导入，或者你明确知道没有旧数据。

### 2. 重新入库

```text
load documents
-> split chunks
-> embed chunks
-> extract sources
-> ensure collection
-> delete old chunks by source
-> upsert new chunks
```

重新入库会替换同 source 的旧 chunks。

适合文档内容有变化的场景。

### 3. 删除某个文档

```text
source
-> build payload filter
-> delete points by filter
```

删除文档不需要加载文件。

只需要知道这个文档曾经对应的 `source`。

## 五、常见误区

### 误区 1：重新跑入库脚本就等于更新知识库

不一定。

如果只是重复 upsert，旧 chunk 可能仍然残留。

尤其是新文档变短、chunk 数减少时，旧尾部 chunks 不会自动消失。

### 误区 2：有稳定 chunk_id 就不需要删除

稳定 chunk_id 只能保证同一个 chunk id 覆盖。

它不能保证旧 chunk_id 全部被覆盖。

所以稳定 chunk_id 和按 source 删除要配合使用。

### 误区 3：按标题删除就够了

标题是给人看的，不适合做稳定删除条件。

标题可能改，可能重复，也可能有不同语言版本。

当前项目按 `source` 删除更稳。

### 误区 4：删除接口可以接受空 filter

删除操作必须保守。

空 filter 容易造成误删。

本节明确拒绝空 filter。

### 误区 5：重新入库只要代码跑通就行

重新入库涉及数据一致性。

你要思考：

- 删除失败怎么办
- upsert 失败怎么办
- 重复执行怎么办
- 文档已经不存在怎么办
- 旧数据怎么定位
- 用户查询时会不会看到半更新状态

本节先处理基础版本，后续再学更完整的工程策略。

## 六、本节练习

### 练习 1：解释为什么只 upsert 不够

题目：

旧文档切出 5 个 chunks，新文档切出 3 个 chunks。如果只 upsert 新 chunks，会发生什么问题？

参考答案：

新的 3 个 chunks 会覆盖或写入对应 point，但旧的第 4、第 5 个 chunks 仍然留在向量库里。以后检索时，这些旧 chunks 仍可能被召回，导致模型基于过期内容回答。所以文档更新时不能只 upsert，还需要清理旧 chunks。

### 练习 2：解释为什么按 source 删除

题目：

为什么本节选择按 `source` 删除旧 chunks，而不是按 `title` 删除？

参考答案：

`source` 表示文档来源，适合定位一份文档对应的所有 chunks。`title` 更偏展示，可能变化、重复或不稳定。按 `source` 删除能更准确地清理同一份源文档产生的旧 chunks。

### 练习 3：说明 source、chunk_id、point_id 的区别

题目：

请分别说明 `source`、`chunk_id`、Qdrant `point_id` 的作用。

参考答案：

`source` 是文档级标识，用来表示 chunk 来自哪份文档，也支持按文档过滤和删除。`chunk_id` 是 chunk 级标识，用来表示某份文档里的某个知识片段。Qdrant `point_id` 是向量库内部的 point 编号，本项目用稳定 `chunk_id` 生成稳定 UUID，方便 upsert 覆盖同一个 chunk。

### 练习 4：判断流程顺序

题目：

下面哪个重新入库顺序更合理？

```text
A. delete old -> load -> split -> embed -> upsert
B. load -> split -> embed -> delete old -> upsert
```

参考答案：

B 更合理。因为先 load/split/embed 可以确认新数据已经准备好，再删除旧数据。如果一开始就删除旧数据，然后 embedding 失败，知识库会丢失这份文档。

### 练习 5：解释先删后插的风险

题目：

`delete old -> upsert new` 有什么风险？

参考答案：

如果删除旧 points 成功，但 upsert 新 points 失败，向量库里会暂时缺失这份文档。当前学习项目接受这个风险，但生产系统可能需要文档版本、软删除、后台任务、重试、审计日志或灰度 collection 来降低风险。

### 练习 6：设计删除 filter

题目：

如果要删除 `refund-return-policy.md` 对应的所有 chunks，payload filter 应该是什么样？

参考答案：

```python
{
    "must": [
        {
            "key": "source",
            "match": {
                "value": "refund-return-policy.md",
            },
        }
    ]
}
```

### 练习 7：区分普通入库和刷新入库

题目：

`ingest_directory_to_vector_store()` 和 `refresh_directory_in_vector_store()` 的语义区别是什么？

参考答案：

`ingest_directory_to_vector_store()` 表示把目录里的文档写入向量库，不主动删除旧数据。`refresh_directory_in_vector_store()` 表示用当前目录里的文档刷新向量库，会先按每个文档的 `source` 删除旧 chunks，再写入新 chunks。

### 练习 8：判断是否需要打开 VMware

题目：

本节单元测试需要打开 VMware Ubuntu 里的 Qdrant 吗？

参考答案：

不需要。本节单元测试使用 fake vector store 和 `httpx.MockTransport`，不依赖真实 Qdrant。只有做真实 Qdrant smoke 验证时才需要打开 VMware 并启动 Qdrant。

### 练习 9：思考生产系统升级

题目：

如果以后要让文档更新更安全，你会增加哪些字段或机制？

参考答案：

可以增加 `document_id`、`document_version`、`is_active`、`deleted`、更新时间、操作者、任务状态、审计日志等。也可以使用后台任务队列、重试机制、软删除、版本切换或灰度 collection，避免删除成功但写入失败导致知识缺失。

## 七、自测问题

### 自测 1

问题：

为什么 RAG 知识库不能只支持新增入库？

答案：

因为真实文档会更新、删除和调整权限。如果只新增不清理旧数据，向量库会残留过期 chunks，检索可能召回旧知识，导致模型回答错误。

### 自测 2

问题：

`upsert` 的含义是什么？

答案：

`upsert` 是 update + insert，表示记录不存在就插入，记录存在就更新。在向量库里，相同 point id 的 upsert 会覆盖旧 point。

### 自测 3

问题：

为什么 upsert 不能完全替代删除？

答案：

因为文档更新后，新旧 chunk 数量可能不同。新 chunks 只能覆盖同 id 的旧 chunks，无法自动删除那些新版本里已经不存在的旧 chunks。

### 自测 4

问题：

本节为什么按 `source` 删除？

答案：

因为 `source` 是文档级标识，同一份文档切出的所有 chunks 都带有相同 `source`。按 `source` 删除可以一次清理这份文档的所有旧 chunks。

### 自测 5

问题：

`refresh_directory_in_vector_store()` 为什么先生成 embedding，再删除旧 chunks？

答案：

因为新数据没有准备好之前，不应该动旧数据。如果 embedding 失败，旧数据仍然保留，知识库不会因为刷新失败而立即丢失这份文档。

### 自测 6

问题：

为什么删除接口不应该接受空 filter？

答案：

空 filter 可能造成大范围误删，甚至清空 collection。删除操作必须有明确条件，所以本节拒绝空 filter。

### 自测 7

问题：

`delete_document_from_vector_store()` 适合什么场景？

答案：

适合源文档已经被删除，或者需要手动下线某份文档时，按 `source` 删除向量库里对应的所有 chunks。

### 自测 8

问题：

`replaced_source_count` 是删除的 point 数量吗？

答案：

不是。它表示本次 refresh 处理了多少个不同的文档 source，不表示真实删除了多少个 points。

### 自测 9

问题：

为什么本节新增 `VectorStoreUpdater`，而不是直接把删除方法写进所有地方？

答案：

因为普通入库只需要写入能力，刷新和删除才需要删除能力。用 `VectorStoreUpdater` 可以表达“这个对象既能写又能删”，让接口语义更清楚。

### 自测 10

问题：

如果某份文档从目录里被移走了，`refresh_directory_in_vector_store()` 一定能删除它的旧 chunks 吗？

答案：

不一定。因为 refresh 只知道当前目录里还存在的文档 source。已经被移走的旧文档需要调用 `delete_document_from_vector_store(old_source, ...)`，或者未来通过文档清单表发现它已被删除。

### 自测 11

问题：

本节为什么不直接做真实 Qdrant 删除测试？

答案：

真实 Qdrant 测试依赖 Docker、端口、collection 和数据状态，不适合作为稳定单元测试。本节用 fake 和 MockTransport 验证业务编排与 HTTP 适配，真实服务验证留给 smoke test。

### 自测 12

问题：

生产系统里，怎么降低“删除成功但 upsert 失败”的风险？

答案：

可以引入文档版本、软删除、`is_active` 字段、后台任务队列、重试、审计日志、先写新版本再切换活跃版本，或者使用灰度 collection 验证后再切换。

## 八、你应该能口述出的版本

你可以这样向别人解释本节：

```text
第 23 节讲的是 RAG 知识库的数据维护。前面我们已经能把文档切成 chunks，生成 embedding，写入 Qdrant，并用检索结果生成回答。但真实知识库里的文档会更新和删除，如果只会新增入库，旧 chunks 会残留在向量库，导致模型可能基于过期内容回答。

所以本节补了两个能力。第一，QdrantVectorStore 新增 delete_points_by_filter，可以通过 payload filter 删除 points。第二，ingestion 层新增 delete_document_from_vector_store 和 refresh_directory_in_vector_store。前者用于按 source 删除某份文档的所有 chunks，后者用于重新入库目录：先加载、切分、生成 embedding，确认新数据准备好，再按每个 source 删除旧 chunks，最后 upsert 新 chunks。

本节的关键是理解 source、chunk_id 和 point_id 的职责。source 是文档级标识，用来找到一份文档的所有 chunks；chunk_id 是 chunk 级标识；point_id 是 Qdrant 里的记录编号，由稳定 chunk_id 生成。upsert 可以覆盖同 point id 的旧数据，但如果新文档 chunk 数变少，旧尾部 chunks 不会自动消失，所以必须按 source 删除旧 chunks。

这个方案是基础版，会有删除成功但 upsert 失败的风险。生产系统可以用 document_id、document_version、is_active、软删除、任务队列、审计日志或灰度 collection 来增强。本节先让我们掌握最重要的底层逻辑：知识库不是只新增，还必须能安全清理和刷新。
```

## 九、本节产出

新增或修改：

- `projects/ai-service/app/rag/vector_store.py`
  - 新增 `delete_points_by_filter()`
- `projects/ai-service/app/rag/ingestion.py`
  - 新增 `VectorStoreUpdater`
  - 新增 `RagDeletionResult`
  - 新增 `delete_document_from_vector_store()`
  - 新增 `refresh_directory_in_vector_store()`
  - `RagIngestionResult` 新增 `replaced_source_count`
- `projects/ai-service/tests/rag_fakes.py`
  - `FakeVectorStoreWriter` 新增 delete 调用记录和错误模拟
- `projects/ai-service/tests/test_rag_vector_store.py`
  - 新增 Qdrant 删除适配层测试
- `projects/ai-service/tests/test_rag_ingestion.py`
  - 新增 refresh/delete 编排测试
- `projects/ai-service/tests/test_rag_fakes.py`
  - 新增 fake writer 删除能力测试
- `notes/rag-stage4-23-document-update-delete-reingest.md`

## 十、参考资料

- [阶段 4 第 14 节：metadata 设计](rag-stage4-14-metadata-design.md)
- [阶段 4 第 16 节：payload filter](rag-stage4-16-payload-filter.md)
- [阶段 4 第 22 节：RAG 测试 fake](rag-stage4-22-rag-testing-fakes.md)
- [Qdrant Points API](https://api.qdrant.tech/api-reference/points)
- [Qdrant Filtering](https://qdrant.tech/documentation/concepts/filtering/)
