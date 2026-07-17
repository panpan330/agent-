# 阶段 4 第 24 节：embedding 模型选择、维度、成本和批量处理

## 本节状态

已完成。

本节开始从“确定性 fake embedding”过渡到“真实 embedding 工程认知”。

前面我们一直使用 `DeterministicHashEmbeddingModel`。

它的好处是：

- 不需要 API key
- 不花钱
- 测试稳定
- 维度可控
- 适合学习 RAG 数据链路

但它不是真正理解语义的 embedding 模型。

它不能真的知道：

```text
“退款多久到账”
和
“售后退款处理时效”
语义相近。
```

所以后续要做真实 RAG，必须接入真实 embedding 模型。

第 24 节不急着让你真实调用线上 embedding API。

本节先补齐两个层面的能力：

1. 知识层面

   你要明白 embedding 模型怎么选、维度是什么、为什么维度会影响 Qdrant collection、批量调用为什么重要、成本大概怎么算。

2. 代码层面

   项目新增 OpenAI-compatible embedding 适配器、embedding 配置、批量切分辅助函数和向量存储估算函数。

本节完成后，项目具备了接入真实 embedding 的基础结构，但默认主线仍然可以继续使用 fake embedding 做稳定学习和测试。

## 本节学习目标

学完本节，你应该能讲清楚：

1. embedding 模型和聊天模型是不是同一个东西。
2. 为什么 RAG 通常需要单独的 embedding 模型。
3. document embedding 和 query embedding 为什么要用同一个模型。
4. embedding 维度是什么。
5. 为什么 Qdrant collection 的 vector size 必须和 embedding 维度一致。
6. 为什么换 embedding 模型通常要重建 collection 或新建 collection。
7. 为什么真实 embedding 不能像 fake embedding 一样随便设成 8 维。
8. 模型选择时要考虑中文效果、成本、速度、维度、上下文长度和 provider 兼容性。
9. batch size 是什么，为什么不要一个 chunk 调一次 API。
10. 成本和存储占用大概怎么估算。
11. 本节新增代码如何把真实 embedding API 接入项目，但不破坏现有 fake 测试。

## 本节暂时不学什么

本节暂时不做：

- 不真实调用你的线上 embedding API。
- 不把当前 Qdrant collection 从 8 维直接迁移到真实维度。
- 不重建真实 Qdrant collection。
- 不做 embedding 质量评测。
- 不接本地开源 embedding 模型。
- 不做 GPU 部署。
- 不做向量量化、PQ、HNSW 参数调优。
- 不做混合检索。
- 不做 rerank。

这些会在后续小节逐步展开。

如果后面要真实写入 Qdrant，就需要打开 VMware Ubuntu 并确认 Qdrant 正在运行。

本节主线不需要打开 VMware。

## 一、基础知识铺垫

### 1. embedding 模型是什么

embedding 模型的作用是：

```text
把文本变成一组数字。
```

这组数字叫向量。

例如：

```text
输入文本：
退款多久到账？

输出向量：
[0.012, -0.351, 0.884, ...]
```

真实向量通常不是 3 个数、8 个数，而是几百到几千个数。

这些数字不是给人看的。

它们是给向量数据库和相似度算法用的。

如果两段文本语义相近，它们的向量通常也更接近。

这就是语义检索的基础。

### 2. embedding 模型和聊天模型不是一回事

聊天模型的典型输入输出是：

```text
输入：一段对话
输出：一段自然语言回答
```

embedding 模型的典型输入输出是：

```text
输入：一段文本
输出：一组浮点数向量
```

聊天模型擅长生成。

embedding 模型擅长表示。

你可以这样理解：

```text
聊天模型：负责说话。
embedding 模型：负责把文字变成可比较的语义坐标。
```

RAG 里两者经常同时出现：

```text
embedding 模型负责检索前的语义向量。
聊天模型负责拿到资料后的最终回答。
```

### 3. 为什么 RAG 通常需要单独的 embedding 模型

RAG 的检索阶段需要做两件事：

```text
把文档 chunk 变成向量。
把用户问题变成向量。
```

然后向量数据库比较：

```text
用户问题向量
vs
文档 chunk 向量
```

这个过程不需要模型生成长文本。

它需要的是稳定、便宜、快速、适合相似度计算的向量表示。

所以很多项目会使用：

```text
聊天模型：qwen3.7-plus / GPT / Claude 等
embedding 模型：text-embedding-v4 / text-embedding-3-small / bge / e5 等
```

它们可以来自同一个 provider，也可以来自不同 provider。

### 4. query embedding 和 document embedding 要用同一个模型

这是 RAG 里非常重要的基础规则。

文档入库时：

```text
chunk -> embedding model A -> document vector
```

用户提问时：

```text
query -> embedding model A -> query vector
```

这两个向量在同一个语义空间里，才能比较。

如果文档用模型 A，查询用模型 B：

```text
document vector 来自 A 的坐标系
query vector 来自 B 的坐标系
```

它们就像地图坐标系统不一样。

数字都像向量，但含义不在同一个空间。

检索结果可能会变得不稳定，甚至完全错误。

所以你要记住：

```text
同一批 collection 里的 document embedding 和 query embedding，应该使用同一个 embedding 模型、同一个维度、同一种向量配置。
```

### 5. embedding 维度是什么

embedding 维度就是向量里有多少个数字。

例如：

```text
[0.1, 0.2, 0.3]
```

这是 3 维向量。

我们前面 fake embedding 用过 8 维：

```text
[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
```

真实 embedding 常见维度可能是：

```text
768
1024
1536
2048
3072
```

根据官方文档，OpenAI `text-embedding-3-small` 默认是 1536 维，`text-embedding-3-large` 默认是 3072 维。

阿里云 Model Studio 的 `text-embedding-v4` 支持多个输出维度，默认值是 1024，并支持 2048、1536、1024、768、512、256、128、64 等维度。

这些具体数字会随 provider 更新，实际使用时必须看当前官方文档。

### 6. 维度不是越大越无脑好

维度更大，通常意味着模型可以表达更多语义细节。

但维度更大也带来成本：

- 每条 vector 占用更多存储
- 向量距离计算更重
- 网络传输更大
- Qdrant point 写入数据更大
- 内存和索引成本更高

你可以粗略理解：

```text
向量存储大小 ≈ chunk 数量 × 维度 × 每个数字字节数
```

如果用 float32，一个数字通常按 4 字节估算。

例如：

```text
100,000 个 chunks
1536 维
float32 4 字节

100000 × 1536 × 4 = 614,400,000 字节
约 586 MB
```

这还没算 payload、索引、元数据、数据库额外开销。

所以维度选择是质量、速度、存储和成本之间的取舍。

### 7. 为什么 Qdrant collection 维度必须一致

Qdrant collection 是一组可以互相搜索的 points。

同一个向量空间里的向量必须有相同维度。

如果 collection 创建时是：

```json
{
  "vectors": {
    "size": 8,
    "distance": "Cosine"
  }
}
```

那它期待写入的是 8 维向量。

如果你后来写入 1024 维真实 embedding，就不匹配。

所以你不能把 fake 8 维 collection 直接拿来存真实 1024 维 embedding。

你需要：

```text
新建 collection
或删除旧 collection 后按真实维度重建
```

这就是为什么本节没有直接把项目切到真实 embedding。

### 8. 为什么换 embedding 模型可能要重建 collection

换模型可能带来三类变化：

1. 维度变化

   例如从 8 维 fake 改成 1024 维真实模型。

2. 语义空间变化

   即使维度相同，模型 A 和模型 B 学到的向量空间也不同。

3. 距离度量选择变化

   有些 embedding 更适合 cosine，有些可能推荐 dot product。

所以换 embedding 模型不是改一个配置就完事。

通常要：

```text
重新生成所有 document embeddings
重新写入 collection
确保 query embedding 也使用同一个新模型
```

### 9. 为什么 fake embedding 还能继续保留

真实 embedding 很重要。

但 fake embedding 也不能删。

原因是：

- 单元测试不能依赖真实 API key
- 单元测试不能花钱
- 单元测试不能因为网络波动失败
- fake embedding 可以稳定复现
- fake embedding 适合测试流程编排

所以项目里会同时存在：

```text
DeterministicHashEmbeddingModel：学习和测试用
OpenAICompatibleEmbeddingModel：真实 API 接入用
FakeEmbeddingModel：单元测试 fake
```

它们都实现同一个 `EmbeddingModel` 协议：

```python
embed_texts(texts) -> list[Vector]
dimension -> int
```

这就是接口抽象的价值。

### 10. embedding 成本主要按输入 token 算

多数云 embedding API 的费用是按输入 token 计算。

这和聊天模型类似，但 embedding 通常只算输入文本。

例如你有：

```text
10,000 个 chunks
每个 chunk 平均 300 tokens
```

那么总输入大约：

```text
10,000 × 300 = 3,000,000 tokens
```

如果 provider 按每百万 tokens 收费，就可以估算入库成本。

注意：

- 文档入库会消耗 embedding token
- 用户每次查询也会生成 query embedding
- 重新入库会再次消耗 embedding token
- chunk 越碎，chunk 数越多，总请求管理成本越高

### 11. embedding 成本不只包括 API 费用

你还要考虑：

- 向量存储成本
- 向量索引成本
- 查询 CPU/内存成本
- 网络传输成本
- 重新入库成本
- 失败重试成本
- 开发调试成本

很多新手只看：

```text
API 每百万 token 多少钱
```

但真实 RAG 系统还要看：

```text
我有多少 chunks？
每个 chunk 多长？
维度多大？
多久重新入库？
每天多少 query？
```

### 12. batch size 是什么

batch size 表示一次 API 请求里放多少条文本。

比如：

```text
batch_size = 10
```

表示一次 embedding 请求最多传 10 段文本。

如果你有 25 个 chunks，就会拆成：

```text
第 1 批：10 条
第 2 批：10 条
第 3 批：5 条
```

这就是批量处理。

### 13. 为什么不要一个 chunk 调一次 API

如果 1000 个 chunks 每个都单独调一次 API：

```text
1000 chunks -> 1000 requests
```

问题是：

- 请求开销大
- 网络往返慢
- 更容易触发 rate limit
- 日志和错误处理更复杂
- 总体入库时间更长

如果 batch size 是 10：

```text
1000 chunks -> 100 requests
```

如果 batch size 是 64：

```text
1000 chunks -> 16 requests
```

所以批量 embedding 是工程里必须考虑的基础能力。

### 14. batch size 不是越大越好

batch size 太大也有风险：

- 超过 provider 单次文本数量限制
- 超过单条文本 token 限制
- 超过请求体大小限制
- 单次失败影响更多 chunks
- 响应时间更长
- 重试成本更高

阿里云 Model Studio 文档里，`text-embedding-v4` 的同步 embedding batch size 是 10。

这说明不同 provider、不同模型的限制并不一样。

所以 batch size 必须看官方文档，不能凭感觉。

### 15. 同步批量和离线批量不是一回事

本节代码里的 batch 是同步批量：

```text
一次 API 请求里传多条文本，马上拿返回结果。
```

有些 provider 还提供离线 batch inference：

```text
上传 JSONL 文件
创建批处理任务
过一段时间下载结果
```

离线 batch 适合大规模数据处理。

同步 batch 适合：

- 小规模入库
- 在线更新
- 调试
- 学习阶段

当前项目先做同步 batch。

### 16. 真实 embedding 的返回值必须校验

真实 API 返回后，不能直接相信。

至少要校验：

- 返回数量是否等于输入数量
- 每个 item 是否有 embedding
- 每个 embedding 是否是数字列表
- 每个向量维度是否等于配置维度

否则后面写入 Qdrant 时才报错，定位会更麻烦。

本节代码在 `OpenAICompatibleEmbeddingModel` 里做了这些检查。

这和前面我们一直强调的原则一致：

```text
外部服务返回的数据，进入项目核心流程前要校验。
```

### 17. `dimensions` 参数是什么

有些 embedding 模型支持在请求里指定输出维度。

OpenAI 的 embedding v3 模型支持 `dimensions` 参数，用于缩短输出向量。

阿里云 Model Studio 的 embedding 同步 API 也支持设置输出维度，但它的原生 HTTP 参数结构和 OpenAI-compatible SDK 参数并不完全等价。

所以本节配置了：

```text
EMBEDDING_REQUEST_DIMENSIONS
```

它的意思是：

```text
是否把 dimensions 参数传给 OpenAI-compatible embeddings.create()
```

默认代码支持这个开关。

但真实接入某个 provider 前，必须确认这个 provider 的 OpenAI-compatible embedding 接口是否支持这个参数。

### 18. 为什么本节没有直接真实调用你给的 qwen3.7-plus

你之前给的是：

```text
model = qwen3.7-plus
```

这是聊天/推理模型，不是 embedding 模型。

embedding 应该选 embedding 专用模型，例如：

```text
text-embedding-v4
text-embedding-3-small
text-embedding-3-large
```

具体要用哪个，要看你当前 provider 的模型列表、价格、地域和兼容接口。

所以不要把聊天模型名直接填到 embedding 模型配置里。

### 19. 中文 RAG 怎么选 embedding 模型

你的学习项目主要是中文客服知识库。

选择 embedding 模型时，至少要考虑：

- 中文语义检索效果
- 中英文混合能力
- 最大输入长度
- 输出维度
- 单次 batch 限制
- 成本
- 延迟
- 是否支持 OpenAI-compatible SDK
- 是否支持你所在地域
- 是否有免费额度或测试额度

不要只看“模型名很新”。

RAG 模型选择最终要靠评测。

后面我们会学习：

```text
检索质量调优
RAG eval
```

那时会更系统地比较模型效果。

### 20. 本节新增代码和学习目标的关系

本节不是为了马上上线真实 embedding。

本节新增代码是为了让项目具备正确接口：

```text
EmbeddingModel 协议
-> fake embedding 继续测试
-> OpenAICompatibleEmbeddingModel 接真实 API
-> batch helper 控制批量
-> storage estimator 理解维度成本
-> Settings 保存模型、维度、batch 配置
```

这让后续第 25 节、第 26 节继续做检索质量调优时，有更稳的基础。

## 二、本节主题系统讲解

### 1. 第 24 节在 RAG 主线里的位置

前面第 13 节我们做过：

```text
生成 embedding 并写入 Qdrant
```

但当时用的是 fake embedding。

第 24 节补的是：

```text
真实 embedding 模型接入前的工程结构和认知基础。
```

它不是重复第 13 节。

第 13 节解决：

```text
RAG 入库链路怎么跑通。
```

第 24 节解决：

```text
真实 embedding 模型怎么选，怎么配置，怎么批量，怎么校验，怎么估算成本。
```

### 2. 本节新增 `OpenAICompatibleEmbeddingModel`

新增位置：

```text
projects/ai-service/app/rag/embeddings.py
```

它的职责是：

```text
把一组文本传给 OpenAI-compatible embedding API，
拿回一组向量，
并校验数量和维度。
```

核心接口仍然是：

```python
embed_texts(texts: Sequence[str]) -> list[Vector]
```

这让它能和现有入库流程无缝衔接。

### 3. 为什么把真实 embedding 放在 `app/rag/embeddings.py`

因为 embedding 是 RAG 领域能力。

它不是普通聊天服务。

它服务的是：

```text
document chunks -> vectors
query -> vector
```

所以放在 `app/rag/embeddings.py` 更合理。

后续如果复杂起来，可以再拆：

```text
app/rag/embedding_clients.py
app/rag/embedding_models.py
```

当前没必要提前拆太细。

### 4. `EmbeddingModel` 协议继续保持简单

协议仍然只有：

```python
dimension
embed_texts(texts)
```

这是刻意保持简单。

因为入库和检索真正需要的就是：

```text
我给你文本，你给我向量。
我知道向量维度是多少。
```

无论背后是：

- fake hash
- fake test model
- OpenAI-compatible API
- 本地模型
- 后续 LangChain embedding wrapper

只要符合这个协议，就能接入当前 RAG 流程。

### 5. `OpenAICompatibleEmbeddingModel.from_settings()`

本节新增：

```python
OpenAICompatibleEmbeddingModel.from_settings(settings)
```

它从配置里读取：

```text
EMBEDDING_API_KEY
EMBEDDING_BASE_URL
EMBEDDING_MODEL
EMBEDDING_DIMENSION
EMBEDDING_BATCH_SIZE
EMBEDDING_REQUEST_DIMENSIONS
```

然后构造真实 client。

这样以后真实接入时，不需要把 API key 写进代码。

这也延续了前面 `.env` 安全配置的原则。

### 6. 为什么 embedding 配置和 LLM 配置分开

本节新增独立配置：

```text
EMBEDDING_PROVIDER
EMBEDDING_MODEL
EMBEDDING_BASE_URL
EMBEDDING_API_KEY
EMBEDDING_DIMENSION
EMBEDDING_BATCH_SIZE
EMBEDDING_REQUEST_DIMENSIONS
```

原因是：

```text
聊天模型和 embedding 模型可能不是同一个模型。
```

例如：

```text
LLM_MODEL=qwen3.7-plus
EMBEDDING_MODEL=text-embedding-v4
```

如果把它们混在一起，很容易误把聊天模型当 embedding 模型。

### 7. 为什么 embedding API key 可以回退到 LLM_API_KEY

`Settings.resolved_embedding_api_key` 的顺序是：

```text
EMBEDDING_API_KEY
LLM_API_KEY
OPENAI_API_KEY
```

这是一种学习项目里的便利设计。

如果同一个 provider 的聊天模型和 embedding 模型共用 key，就不用重复配置。

但更推荐你理解它们是两类配置。

生产系统里，有时会把不同服务的 key 分开，便于权限和账单管理。

### 8. 为什么 embedding base_url 可以回退到 LLM_BASE_URL

同理，如果你的 provider 在同一个 workspace 下同时提供聊天和 embedding 的 OpenAI-compatible endpoint，那么 embedding 可以复用 base_url。

所以本项目支持：

```text
优先 EMBEDDING_BASE_URL
否则 LLM_BASE_URL
```

但这只是方便。

真实使用时要确认：

```text
这个 base_url 是否真的支持 embeddings.create()
这个模型名是否真的是 embedding 模型
```

### 9. 新增 `split_texts_into_batches()`

这个函数做一件事：

```text
把 texts 按 batch_size 切成多批。
```

例如：

```python
split_texts_into_batches(
    ["a", "b", "c", "d", "e"],
    batch_size=2,
)
```

结果是：

```python
[
    ["a", "b"],
    ["c", "d"],
    ["e"],
]
```

这个函数很小，但它体现了批量处理思想。

### 10. 为什么批量函数要拒绝空白文本

空白文本没有语义。

如果传给真实 embedding API：

- 可能直接报错
- 可能浪费请求
- 可能返回无意义向量
- 可能污染入库数据

所以本节在 batch helper 中拒绝空白文本。

前面 `DeterministicHashEmbeddingModel` 也拒绝空白文本。

这让 fake 和真实适配器的行为更一致。

### 11. 新增 `estimate_dense_vector_storage_bytes()`

这个函数用于估算 dense vector 原始存储大小。

公式是：

```text
vector_count × dimension × bytes_per_value
```

默认 `bytes_per_value=4`，按 float32 粗略估算。

例如：

```python
estimate_dense_vector_storage_bytes(
    vector_count=1000,
    dimension=1536,
)
```

结果：

```text
6,144,000 bytes
```

这个数字不是 Qdrant 实际占用。

真实占用还包括：

- payload
- index
- segment
- WAL
- optimizer
- 元数据

但它能帮助你形成维度成本意识。

### 12. 为什么不在本节封装真实错误映射

本节 `OpenAICompatibleEmbeddingModel` 暂时只负责调用和校验。

真实 API 报错后，会在上层入库流程里被：

```python
rag_embedding_failed(exc)
```

映射成统一应用错误。

这个错误映射在第 21 节已经学过。

所以本节不重复写一套 provider 错误映射。

### 13. 为什么不让测试真实调用 embedding API

测试真实调用 embedding API 会带来：

- API key 泄漏风险
- 费用
- 网络不稳定
- provider 限流
- 返回变化
- 本地和 CI 环境不一致

所以本节测试使用 fake embedding endpoint。

测试重点是：

```text
请求参数对不对
批量拆分对不对
返回数量校验对不对
维度校验对不对
配置构造对不对
```

真实 API 调用以后会放到 smoke test。

### 14. `.env.example` 为什么新增 embedding 配置

本节在 `.env.example` 里新增：

```text
EMBEDDING_PROVIDER
EMBEDDING_MODEL
EMBEDDING_BASE_URL
EMBEDDING_API_KEY
EMBEDDING_DIMENSION
EMBEDDING_BATCH_SIZE
EMBEDDING_REQUEST_DIMENSIONS
```

这是为了让后续真实接入时有清晰位置。

注意：

```text
当前 QDRANT_VECTOR_SIZE=8 主要服务前面 fake smoke。
真实 embedding 入库时，真实 collection 维度必须和 EMBEDDING_DIMENSION 一致。
```

不要把 8 维 fake collection 直接拿来写 1024 维真实 embedding。

### 15. 本节完成后后续怎么走

本节完成后，项目具备：

- fake embedding
- 测试 fake embedding
- OpenAI-compatible real embedding adapter
- embedding 独立配置
- batch helper
- storage estimator

下一节第 25 节会进入：

```text
检索质量调优：chunk size、overlap、top_k、score_threshold
```

也就是不只问“能不能检索”，而是开始问：

```text
检索得好不好？
为什么有些问题搜不到？
参数怎么影响召回？
```

## 三、本节代码改动说明

### 1. `Settings` 新增 embedding 配置

文件：

```text
projects/ai-service/app/core/config.py
```

新增字段：

```python
embedding_provider
embedding_model
embedding_base_url
embedding_api_key
embedding_dimension
embedding_batch_size
embedding_request_dimensions
```

新增属性：

```python
resolved_embedding_api_key
has_embedding_api_key
resolved_embedding_base_url
```

它们的作用是让真实 embedding 接入不依赖硬编码。

### 2. `OpenAICompatibleEmbeddingModel`

文件：

```text
projects/ai-service/app/rag/embeddings.py
```

核心能力：

- 读取模型名
- 读取维度
- 按 batch size 分批
- 调用 `client.embeddings.create(...)`
- 可选传 `dimensions`
- 校验返回数量
- 校验向量维度
- 校验向量元素是数字

它服务真实 embedding API。

但测试里不会真实调用。

### 3. `split_texts_into_batches()`

文件：

```text
projects/ai-service/app/rag/embeddings.py
```

作用：

```text
把文本列表按 batch size 切分。
```

它看起来简单，但这是批量 embedding 的基础。

### 4. `estimate_dense_vector_storage_bytes()`

文件：

```text
projects/ai-service/app/rag/embeddings.py
```

作用：

```text
用 vector_count × dimension × bytes_per_value 粗略估算 dense vectors 原始存储大小。
```

这个函数不是生产级容量规划工具。

它是学习工具，帮助你理解：

```text
维度越大，存储越大。
chunks 越多，存储越大。
```

### 5. 测试补充

本节测试主要覆盖：

- 默认配置是否包含 embedding 设置
- 环境变量是否能读取 embedding 设置
- embedding key/base_url 回退逻辑
- batch size 和 dimension 的配置校验
- batch helper 是否正确分批
- storage estimator 是否按公式计算
- OpenAI-compatible embedding adapter 是否按批调用
- 是否可选传 `dimensions`
- provider 返回数量不匹配是否报错
- provider 返回维度不匹配是否报错
- provider 返回非数字向量是否报错

## 四、常见误区

### 误区 1：聊天模型也能直接当 embedding 模型

不应该这样理解。

聊天模型和 embedding 模型任务不同。

聊天模型输出自然语言。

embedding 模型输出向量。

RAG 检索阶段应该使用 embedding 专用模型。

### 误区 2：文档 embedding 和 query embedding 可以用不同模型

不建议。

它们必须在同一个向量空间里比较。

文档和查询使用不同 embedding 模型，会导致相似度不可靠。

### 误区 3：维度越大越好

维度更大可能带来更强表达能力，但也带来存储、计算、索引和传输成本。

模型选择要看实际检索效果和成本。

### 误区 4：换 embedding 模型只要改配置

不够。

换模型通常要重新生成文档向量，并重建或刷新 collection。

否则文档向量和查询向量可能不在同一语义空间。

### 误区 5：batch size 越大越好

不一定。

batch size 必须受 provider 限制、请求大小、失败重试成本和延迟影响。

例如阿里云 `text-embedding-v4` 同步接口的 batch size 是 10。

### 误区 6：真实 embedding 测试应该放在单元测试里

不应该。

真实 embedding 调用应该放在手动 smoke test 或专门集成测试里。

单元测试应该用 fake 保持稳定。

## 五、本节练习

### 练习 1：区分聊天模型和 embedding 模型

题目：

请说明聊天模型和 embedding 模型的输入输出区别。

参考答案：

聊天模型输入对话消息，输出自然语言回答。embedding 模型输入文本，输出数字向量。聊天模型负责生成，embedding 模型负责把文本表示成可比较的语义向量。

### 练习 2：解释为什么 query 和 document 要用同一 embedding 模型

题目：

为什么文档入库和用户查询应该使用同一个 embedding 模型？

参考答案：

因为向量相似度比较要求两个向量处在同一个语义空间。文档向量和查询向量如果来自不同模型，就像用不同坐标系比较位置，结果可能不可靠。

### 练习 3：判断 collection 是否能复用

题目：

一个 Qdrant collection 是 8 维 fake embedding 创建的。现在你想写入 1024 维真实 embedding，可以直接复用吗？

参考答案：

不能。collection 的 vector size 必须和写入向量维度一致。8 维 collection 不能直接写入 1024 维向量，需要新建 collection 或重建 collection。

### 练习 4：估算向量原始存储

题目：

如果有 50,000 个 chunks，每个向量 1024 维，按 float32 4 字节估算，原始向量大约占多少字节？

参考答案：

```text
50,000 × 1024 × 4 = 204,800,000 bytes
```

约 195 MB。真实数据库占用还会加上 payload、索引和其他开销。

### 练习 5：设计 batch 拆分

题目：

有 25 个 chunks，provider 的 batch size 是 10，需要拆成几批？

参考答案：

拆成 3 批：

```text
10 + 10 + 5
```

### 练习 6：解释为什么 batch size 不能随便设大

题目：

为什么不把 batch size 直接设成 1000？

参考答案：

因为 provider 可能限制单次文本数量、单条文本 token、请求体大小和超时时间。batch 太大时，一次失败会影响更多 chunks，重试成本也更高。

### 练习 7：配置真实 embedding 前要检查什么

题目：

真实接入 embedding API 前，至少要检查哪些配置？

参考答案：

要检查 API key、base_url、embedding 模型名、输出维度、batch size、是否支持 `dimensions` 参数、Qdrant collection 维度是否一致，以及 document/query 是否使用同一 embedding 模型。

### 练习 8：判断是否应该真实调用 API

题目：

单元测试里应该真实调用 embedding API 吗？为什么？

参考答案：

不应该。真实 API 会依赖 key、网络、费用和 provider 状态，容易导致测试不稳定。单元测试应使用 fake，真实 API 调用放到 smoke test 或集成测试。

### 练习 9：解释 `EMBEDDING_REQUEST_DIMENSIONS`

题目：

`EMBEDDING_REQUEST_DIMENSIONS` 是什么？

参考答案：

它表示是否把配置的 `EMBEDDING_DIMENSION` 作为 `dimensions` 参数传给 OpenAI-compatible embedding API。不是所有 provider 或模型都支持这个参数，真实使用前必须查官方文档。

## 六、自测问题

### 自测 1

问题：

embedding 模型的输出是什么？

答案：

一组数字向量，通常是几百到几千个浮点数。

### 自测 2

问题：

聊天模型和 embedding 模型在 RAG 中分别负责什么？

答案：

embedding 模型负责把文档 chunk 和用户问题变成向量，用于检索；聊天模型负责根据检索到的资料生成最终自然语言回答。

### 自测 3

问题：

为什么同一个 Qdrant collection 里的向量维度必须一致？

答案：

因为向量相似度计算要求同一向量空间内的向量有相同维度。Qdrant collection 的 vector size 定义了该 collection 接受的向量长度。

### 自测 4

问题：

如果换 embedding 模型，需要重新生成文档向量吗？

答案：

通常需要。因为新模型的语义空间可能不同，即使维度相同，也不能直接混用旧模型生成的向量。

### 自测 5

问题：

batch size 是什么？

答案：

batch size 是一次 embedding API 请求中包含多少条文本。

### 自测 6

问题：

为什么 batch embedding 比一个 chunk 调一次 API 更好？

答案：

它能减少请求次数、降低网络往返开销、减少日志和调度成本，并提高入库效率。

### 自测 7

问题：

向量存储大小的粗略估算公式是什么？

答案：

```text
vector_count × dimension × bytes_per_value
```

float32 可按 4 字节估算。

### 自测 8

问题：

`DeterministicHashEmbeddingModel` 以后还有用吗？

答案：

有。它适合学习、测试和本地稳定验证，不依赖真实 API。真实 embedding 接入后，单元测试仍应保留 fake。

### 自测 9

问题：

`OpenAICompatibleEmbeddingModel` 为什么要校验返回数量？

答案：

因为输入多少条文本，就应该返回多少个向量。如果数量不一致，后续 chunk 和 vector 会错位，导致错误入库。

### 自测 10

问题：

`OpenAICompatibleEmbeddingModel` 为什么要校验向量维度？

答案：

因为向量维度必须和配置维度、Qdrant collection 维度一致。维度不一致会导致写入失败或检索空间混乱。

### 自测 11

问题：

为什么不能把 `qwen3.7-plus` 直接当 embedding 模型？

答案：

`qwen3.7-plus` 是聊天/生成模型，不是 embedding 专用模型。embedding 应该使用 provider 提供的 embedding 模型，例如 `text-embedding-v4` 或 `text-embedding-3-small`。

### 自测 12

问题：

本节为什么没有真实调用 embedding API？

答案：

因为本节重点是理解模型选择、维度、成本和批量，并建立可测试的适配器。真实 API 调用需要 key、费用和真实 collection 维度配合，适合后续 smoke test。

## 七、你应该能口述出的版本

你可以这样向别人解释本节：

```text
第 24 节讲真实 embedding 接入前必须懂的基础。embedding 模型和聊天模型不是一回事，聊天模型负责生成回答，embedding 模型负责把文档和问题变成向量，让向量数据库可以计算语义相似度。RAG 里文档入库和用户查询必须用同一个 embedding 模型、同一个维度，否则向量不在同一个语义空间里，检索会不可靠。

embedding 维度就是向量里有多少个数字。维度会影响 Qdrant collection 的 vector size，也会影响存储、计算、索引和网络成本。比如 OpenAI text-embedding-3-small 默认 1536 维，text-embedding-3-large 默认 3072 维；阿里云 text-embedding-v4 支持多个维度，默认 1024。换 embedding 模型或换维度时，通常要重新生成文档向量并新建或刷新 collection。

本节代码新增了 OpenAICompatibleEmbeddingModel，用来调用 OpenAI-compatible embedding API，同时校验返回数量、向量维度和向量数字类型；新增了 split_texts_into_batches，用来把 chunks 按 batch size 分批；还新增了 estimate_dense_vector_storage_bytes，用来粗略估算向量存储。配置上新增了 EMBEDDING_MODEL、EMBEDDING_DIMENSION、EMBEDDING_BATCH_SIZE 等字段。

本节没有直接真实调用线上 embedding，因为当前 Qdrant 练习 collection 还是 8 维 fake 向量。真实 embedding 要先确认模型、维度、batch 限制、base_url、API key，并让 collection 维度和 embedding 输出维度一致。单元测试继续用 fake，真实 API 调用后续放到 smoke test。
```

## 八、本节产出

新增或修改：

- `projects/ai-service/app/core/config.py`
  - 新增 embedding 独立配置
  - 新增 embedding key/base_url 解析属性
- `projects/ai-service/app/rag/embeddings.py`
  - 新增 `OpenAICompatibleEmbeddingModel`
  - 新增 `split_texts_into_batches()`
  - 新增 `estimate_dense_vector_storage_bytes()`
- `projects/ai-service/.env.example`
  - 新增 embedding 配置示例
- `projects/ai-service/tests/test_config.py`
  - 新增 embedding 配置测试
- `projects/ai-service/tests/test_rag_embeddings.py`
  - 新增真实 embedding 适配器、批量、维度和存储估算测试
- `notes/rag-stage4-24-embedding-model-dimension-cost-batch.md`

## 九、参考资料

- [OpenAI Embeddings Guide](https://developers.openai.com/api/docs/guides/embeddings)
- [Alibaba Cloud Model Studio Embedding](https://www.alibabacloud.com/help/en/model-studio/embedding)
- [Alibaba Cloud Model Studio Text Embedding Synchronous API](https://www.alibabacloud.com/help/en/model-studio/text-embedding-synchronous-api)
- [Qdrant Collections](https://qdrant.tech/documentation/manage-data/collections/)
