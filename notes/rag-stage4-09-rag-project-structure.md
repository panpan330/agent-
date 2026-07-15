# 阶段 4 第 9 节：RAG 项目结构设计

> 本节结论：RAG 不是一个函数，也不是把“读文档、切 chunk、调 embedding、写 Qdrant、查 Qdrant、拼 prompt、调模型”全塞进一个接口里。一个可维护的 RAG 项目应该先拆清楚模块边界。本节在 `projects/ai-service` 中新增 `app/rag` 内部包，用来承载 RAG 领域能力；当前只放 `RagDocument` 和 `RagChunk` 两个内部数据模型，后续再逐步接入 loader、splitter、embedding、vector_store、retriever、generator 和 pipeline。

## 本节状态说明

这一节不需要打开 VMware Ubuntu 虚拟机。

原因是：

```text
本节不访问 Qdrant。
本节不启动 Docker。
本节不写入向量。
本节只在 Windows 主项目里设计 RAG 代码结构。
```

当前新增内容：

```text
projects/ai-service/app/rag/__init__.py
projects/ai-service/app/rag/documents.py
projects/ai-service/app/rag/README.md
projects/ai-service/tests/test_rag_documents.py
```

同步更新：

```text
projects/ai-service/README.md
README.md
docs/learning-progress.md
docs/learning-resources.md
```

## 生成笔记前的教学复核

这一节必须讲清：

```text
1. 为什么 RAG 项目需要先设计结构。
2. RAG 不是一个单独函数，而是一条流水线。
3. 文档入库流程和用户问答流程为什么要分开。
4. loader、splitter、embedding、vector_store、retriever、generator、pipeline 分别负责什么。
5. 为什么新增 app/rag，而不是把所有代码塞进 app/services。
6. app/rag、app/services、app/routers、app/schemas 的职责边界。
7. 为什么当前只新增 RagDocument 和 RagChunk。
8. RagDocument、RagChunk 和后续 Qdrant point 的关系。
9. 新增代码逐行在学什么。
10. 后续第 10-18 节如何沿着这个结构扩展。
```

## 本节一句话定位

第 8 节我们已经让 Qdrant 跑起来了。

但 Qdrant 跑起来不等于 RAG 项目已经有结构。

第 9 节要解决的是：

```text
RAG 代码以后放在哪里，每个模块负责什么，怎么避免项目越写越乱。
```

如果不先设计结构，后面很容易变成：

```text
一个 rag.py 文件里同时做：
读文件
切 chunk
调 embedding
写 Qdrant
查 Qdrant
拼 prompt
调模型
返回接口响应
处理异常
写日志
```

这种代码一开始能跑，但很难学清楚，也很难维护。

## 基础知识铺垫：什么是项目结构

项目结构不是简单地创建几个文件夹。

项目结构真正解决的是：

```text
代码应该按什么职责摆放。
```

比如你现在的 `ai-service` 已经有这些层：

```text
app/core       通用基础能力：配置、日志、异常、trace_id
app/middleware FastAPI 中间件
app/routers    HTTP API 路由
app/schemas    API 请求/响应模型
app/services   应用服务和外部调用编排
app/tools      Tool Calling 相关工具定义和执行辅助
```

这些不是随便分的。

它们背后的思想是：

```text
不同职责的代码不要混在一起。
```

RAG 也需要自己的领域边界。

所以本节新增：

```text
app/rag
```

它不是为了显得项目复杂，而是为了让 RAG 相关能力有清晰归属。

## 基础知识铺垫：什么是领域代码

“领域代码”可以先理解成：

```text
围绕某个业务或技术主题本身的核心规则和数据结构。
```

在 Tool Calling 阶段，我们有：

```text
app/tools
```

它关心：

```text
工具定义
工具参数
工具权限
工具幂等
工具注册表
```

在 RAG 阶段，我们新增：

```text
app/rag
```

它关心：

```text
文档
chunk
embedding
向量库
检索
生成
RAG 流水线
```

这些概念不是 HTTP 层概念，也不是单纯模型调用概念。

它们属于 RAG 领域本身。

## 基础知识铺垫：RAG 有两条主流程

RAG 项目一定要分清两条流程。

### 第一条：文档入库流程

也叫 ingestion pipeline。

它负责：

```text
原始文档
-> 加载
-> 清洗
-> 切 chunk
-> 生成 embedding
-> 写入向量数据库
```

这条流程通常不是用户每问一次就跑一次。

它一般在：

```text
新增文档
更新文档
删除文档
重新构建知识库
```

时运行。

### 第二条：用户问答流程

也叫 query pipeline 或 retrieval-generation pipeline。

它负责：

```text
用户问题
-> 生成 query embedding
-> 检索相关 chunk
-> 组装 prompt
-> 调用 LLM
-> 返回答案和引用来源
```

这条流程是用户提问时运行。

这两条流程使用了一些共同概念：

```text
chunk
metadata
embedding
vector store
```

但它们不是同一个流程。

如果混在一起，后面会非常乱。

## 为什么不能把 RAG 都写进一个接口

假设我们未来写一个接口：

```text
POST /rag/ask
```

如果这个接口里直接写：

```text
读取所有文档
切分所有 chunk
调用 embedding
写入 Qdrant
查询 Qdrant
拼 prompt
调用模型
返回回答
```

会有什么问题？

### 问题 1：每次提问都重复入库

文档入库应该提前完成。

用户提问时应该直接检索已有向量。

如果每次问答都重新读文档、切 chunk、生成 embedding，会非常慢，也很贵。

### 问题 2：测试困难

你很难单独测试：

```text
文档加载对不对
chunk 切分对不对
embedding 调用对不对
Qdrant 写入对不对
检索排序对不对
prompt 拼接对不对
```

所有逻辑塞在一起，就只能做大而慢的端到端测试。

### 问题 3：排查困难

如果最终答案错了，你不知道问题出在哪里：

```text
是文档没加载？
是 chunk 切坏了？
是 embedding 失败？
是 Qdrant 没写入？
是检索 top_k 太小？
是 prompt 写得不好？
是模型回答偏了？
```

模块分清后，才能逐层定位。

### 问题 4：后续扩展困难

后面我们会加：

```text
payload filter
score_threshold
引用来源
无结果拒答
文档更新删除
fake embedding 测试
fake vector store 测试
混合检索
rerank
安全过滤
```

如果一开始没有结构，越往后越难加。

## 本节主题系统讲解：RAG 模块应该怎么拆

一个清晰的 RAG 项目，至少要能说清这些模块：

```text
documents
loaders
splitters
embeddings
vector_store
retriever
generator
pipeline
```

下面逐个讲。

## documents：内部数据结构

`documents` 负责定义 RAG 内部通用数据模型。

当前新增：

```text
RagDocument
RagChunk
```

它们不是 HTTP 请求模型。

它们是 RAG 内部流转的数据结构。

比如：

```text
加载器读出 RagDocument
切分器把 RagDocument 切成 RagChunk
embedding 模块把 RagChunk.content 转成向量
vector_store 模块把 RagChunk.metadata 写成 Qdrant payload
retriever 模块返回命中的 RagChunk 或检索结果
generator 模块把 RagChunk.content 拼进 prompt
```

所以 `RagDocument` 和 `RagChunk` 是后续模块之间的共同语言。

## loaders：文档加载

`loaders` 后续负责把原始文件读进来。

例如：

```text
Markdown 文件
txt 文件
PDF 文件
Word 文件
网页内容
```

阶段 4 前半段我们先从简单的 Markdown/txt 开始。

loader 的输出应该是：

```text
RagDocument
```

也就是：

```text
原文内容 + 文档级 metadata
```

比如：

```text
content = "订单超过 72 小时未发货，可以创建投诉工单。"
metadata.source = "order_policy.md"
metadata.title = "订单发货规则"
metadata.doc_type = "policy"
```

## splitters：chunk 切分

`splitters` 后续负责把 `RagDocument` 切成多个 `RagChunk`。

它关心：

```text
chunk_size
overlap
按段落切
按标题切
保留标题上下文
chunk_id 怎么生成
metadata 怎么继承
```

splitter 的输入：

```text
RagDocument
```

splitter 的输出：

```text
list[RagChunk]
```

后面第 12 节会专门讲：

```text
chunk 切分策略：大小、重叠、标题、段落。
```

## embeddings：向量生成

`embeddings` 后续负责调用 embedding 模型。

它做两类事情：

```text
1. 文档入库时，把 chunk content 变成 chunk vector。
2. 用户提问时，把 user question 变成 query vector。
```

它不应该负责：

```text
读文件
切 chunk
写 Qdrant
拼最终回答
```

它只关心：

```text
文本 -> 向量
```

这样后续我们做 fake embedding 测试会很容易。

## vector_store：向量库适配

`vector_store` 后续负责和 Qdrant 交互。

它会隐藏这些细节：

```text
Qdrant base_url
collection 名
创建 collection
upsert point
query/search
payload filter
score_threshold
删除 point
```

为什么要做适配层？

因为业务代码不应该到处直接写 Qdrant API。

如果到处散落：

```text
qdrant_client.upsert(...)
qdrant_client.query_points(...)
```

以后你想换 Milvus、pgvector，或者做 fake vector store 测试，会很痛苦。

所以后续会通过一个项目自己的 adapter 包起来。

先记住：

```text
vector_store 是项目代码和 Qdrant 之间的边界。
```

## retriever：检索器

`retriever` 后续负责：

```text
根据用户问题向量，从向量库里取回相关 chunk。
```

它关心：

```text
top_k
score_threshold
payload filter
返回结果排序
无结果处理
```

它不应该负责：

```text
生成最终回答。
```

retriever 的输出应该接近：

```text
检索到的 chunk
score
source
metadata
```

后面第 15-17 节会逐步实现：

```text
基础 top_k 检索
payload filter
score_threshold
```

## generator：生成器

`generator` 后续负责：

```text
把检索结果整理成 prompt，调用模型生成答案。
```

它关心：

```text
prompt 模板
引用来源
无结果拒答
回答格式
模型调用
```

它不应该负责：

```text
读取文档
写 Qdrant
直接修改向量库
```

generator 的输入可能是：

```text
用户问题
检索到的 chunks
```

输出是：

```text
答案
引用来源
```

后面第 18-20 节会逐步讲。

## pipeline：流程编排

`pipeline` 负责把各模块串起来。

通常会有两类 pipeline：

```text
IngestionPipeline
QuestionAnsweringPipeline
```

入库 pipeline：

```text
loader
-> splitter
-> embedding
-> vector_store
```

问答 pipeline：

```text
embedding
-> retriever
-> generator
```

pipeline 的价值是：

```text
让模块各司其职，同时又能组合成完整流程。
```

## app/rag、app/services、app/routers、app/schemas 怎么分

这是本节最重要的工程边界。

### app/rag

放 RAG 领域内部组件。

例如：

```text
RagDocument
RagChunk
MarkdownLoader
TextSplitter
EmbeddingProvider
QdrantVectorStore
RagRetriever
RagGenerator
RagIngestionPipeline
RagQuestionAnsweringPipeline
```

它关心 RAG 怎么工作。

### app/services

放应用服务和业务编排。

例如未来可能有：

```text
KnowledgeBaseService
RagChatService
```

它们会调用 `app/rag` 里的组件。

它们更接近：

```text
这个 FastAPI 应用要提供什么能力。
```

### app/routers

放 HTTP 路由。

例如未来可能有：

```text
POST /rag/ingest
POST /rag/query
```

router 负责：

```text
接收请求
调用 service
返回响应
```

router 不应该写大量 RAG 细节。

### app/schemas

放 HTTP 请求/响应模型。

例如未来可能有：

```text
RagQueryRequest
RagQueryResponse
RetrievedSource
```

它们是接口层的输入输出。

不要和 `RagDocument`、`RagChunk` 混淆。

## 内部模型和 API 模型有什么区别

这点很重要。

`RagDocument`、`RagChunk` 是内部模型。

它们在 RAG 流水线内部流转。

API 模型是给 HTTP 接口用的。

比如：

```text
RagQueryRequest:
  question: str
  top_k: int
```

这是用户请求。

而：

```text
RagChunk:
  chunk_id: str
  content: str
  metadata: dict
```

这是系统内部的 chunk。

它们不要混在一起，是因为：

```text
1. 内部模型可能包含不适合暴露给用户的字段。
2. API 响应要考虑前端展示和安全过滤。
3. 内部模型要服务流水线计算。
4. API 模型要服务接口契约。
```

这就是为什么 `app/rag/documents.py` 不放在 `app/schemas` 里。

## 本节代码变更总览

本节新增：

```text
projects/ai-service/app/rag/__init__.py
projects/ai-service/app/rag/documents.py
projects/ai-service/app/rag/README.md
projects/ai-service/tests/test_rag_documents.py
```

并更新：

```text
projects/ai-service/README.md
```

### app/rag/__init__.py

代码：

```python
"""Internal RAG components for document ingestion, retrieval, and answer generation."""
```

这行代码有两个作用：

```text
1. 让 app/rag 成为一个 Python package。
2. 用一句话说明这个包的职责。
```

现在它没有导出具体对象。

这是有意的。

因为当前阶段还很早，不急着设计公共导出 API。

### app/rag/documents.py

这个文件定义 RAG 内部最基础的两个数据模型：

```text
RagDocument
RagChunk
```

它们使用 Pydantic。

原因是：

```text
1. 项目已经大量使用 Pydantic。
2. RAG 数据在模块间流动时也需要基本校验。
3. 例如 content 不能为空，chunk_id 不能为空。
```

### MetadataValue

代码：

```python
MetadataValue: TypeAlias = str | int | float | bool | list[str]
Metadata: TypeAlias = dict[str, MetadataValue]
```

这表示 metadata 的值暂时允许这些类型：

```text
字符串
整数
小数
布尔值
字符串列表
```

为什么不直接写：

```python
dict[str, object]
```

因为 `object` 太宽了。

它会让任何东西都能放进去：

```text
函数
复杂对象
嵌套类
不可序列化对象
```

而后续 metadata 要写入 Qdrant payload，最好保持接近 JSON 的简单结构。

当前没有支持任意嵌套对象，是为了先保持清晰。

### RagDocument

代码结构：

```python
class RagDocument(BaseModel):
    content: str = Field(min_length=1, ...)
    metadata: Metadata = Field(default_factory=dict, ...)
```

`RagDocument` 表示：

```text
一份加载并清洗后的文档。
```

它通常来自：

```text
Markdown 文件
txt 文件
以后可能还有 PDF/Word/HTML
```

字段解释：

```text
content：文档正文
metadata：文档级元数据，例如 source、title、doc_type、permission_group
```

为什么 `content` 要 `min_length=1`？

因为空文档不能进入 RAG 流程。

空内容后面会导致：

```text
无法切分
embedding 没意义
检索结果没内容
模型回答无材料
```

### RagChunk

代码结构：

```python
class RagChunk(BaseModel):
    chunk_id: str = Field(min_length=1, ...)
    content: str = Field(min_length=1, ...)
    metadata: Metadata = Field(default_factory=dict, ...)
```

`RagChunk` 表示：

```text
文档切分后的一个片段。
```

字段解释：

```text
chunk_id：稳定 chunk 标识，后续可以作为 Qdrant point id
content：chunk 原文，后续会生成 embedding
metadata：chunk 级 metadata，后续会成为 Qdrant payload
```

这里把 `chunk_id` 提前放进模型，是因为第 7 节已经讲过：

```text
point id 要稳定。
```

后续写 Qdrant 时可以形成映射：

```text
RagChunk.chunk_id -> Qdrant point.id
RagChunk.content -> embedding 输入
RagChunk.metadata -> Qdrant payload
```

## 为什么现在不写 loader / splitter / vector_store

这是很重要的节奏控制。

第 9 节只做结构设计。

如果现在直接写 loader、splitter、Qdrant client，会把第 10、11、12、13 节内容提前混在一起。

当前只新增：

```text
RagDocument
RagChunk
```

原因是：

```text
1. 它们是后续所有模块的共同输入输出。
2. 它们足够小，适合作为结构设计的第一个落点。
3. 它们能把前面学过的 document、chunk、metadata、Qdrant point 概念串起来。
4. 它们不会依赖 Qdrant、embedding 模型或外部服务。
```

也就是说：

```text
先定义内部数据契约，再逐步实现流程组件。
```

## 本节测试讲什么

新增测试：

```text
tests/test_rag_documents.py
```

测试重点不是复杂算法，而是确认内部模型边界：

```text
1. RagDocument 能保存 content 和 metadata。
2. RagChunk 不允许空 content。
3. RagChunk.chunk_id 是后续 Qdrant point id 的稳定来源。
```

为什么要测这么基础的东西？

因为这两个模型会成为后续 RAG 流水线的底层数据结构。

一旦底层数据结构失控，后面的 loader、splitter、embedding、vector store 都会被影响。

测试不需要讲得很重，但你要知道：

```text
这些测试是在保护 RAG 内部数据契约。
```

## 当前项目结构变化

新增后，`ai-service` 关键结构变成：

```text
app/
  core/
  middleware/
  routers/
  rag/
    README.md
    __init__.py
    documents.py
  schemas/
  services/
  tools/
  main.py
tests/
  test_rag_documents.py
```

未来会逐步变成：

```text
app/
  rag/
    documents.py
    loaders.py
    splitters.py
    embeddings.py
    vector_store.py
    retriever.py
    generator.py
    pipeline.py
```

但这些文件不会一次性空建一堆。

我们会按照学习进度逐个添加。

## 后续章节如何接到这个结构

第 10 节：

```text
准备第一批 Markdown/txt 知识文档。
```

它会给 loader 提供真实输入。

第 11 节：

```text
文档加载和文本清洗。
```

可能新增：

```text
app/rag/loaders.py
```

它会输出：

```text
RagDocument
```

第 12 节：

```text
chunk 切分策略。
```

可能新增：

```text
app/rag/splitters.py
```

它会把：

```text
RagDocument -> list[RagChunk]
```

第 13 节：

```text
生成 embedding 并写入 Qdrant。
```

可能新增：

```text
app/rag/embeddings.py
app/rag/vector_store.py
```

第 15-17 节：

```text
基础 top_k 检索
payload filter
score_threshold
```

可能新增：

```text
app/rag/retriever.py
```

第 18-20 节：

```text
把检索结果交给模型回答
引用来源
无检索结果处理
```

可能新增：

```text
app/rag/generator.py
app/rag/pipeline.py
```

这样每节都有自然落点。

## 常见错误理解

### 错误 1：项目结构就是文件夹越多越好

不对。

文件夹多不代表结构好。

结构好的标准是：

```text
职责清楚
依赖清楚
后续扩展顺
测试容易写
问题容易定位
```

所以本节没有一次性创建一堆空文件。

### 错误 2：RAG 只有一个“问答接口”

不对。

RAG 至少有：

```text
文档入库流程
用户问答流程
```

问答接口只是最终对外暴露的一部分。

### 错误 3：app/services 什么都能放

不建议。

`app/services` 适合应用编排。

RAG 内部组件应该放在 `app/rag`。

否则 `services` 会越来越臃肿。

### 错误 4：内部模型和 API 模型可以随便混用

不建议。

内部模型服务的是流水线。

API 模型服务的是接口契约。

两者边界不同。

### 错误 5：现在不写 Qdrant client 就没学到东西

不对。

现在学的是工程结构。

如果没有结构，后面写 Qdrant client 只会变成“把代码堆进去”。

## 本节练习

### 练习 1：判断模块职责

请判断下面功能应该放在哪个模块：

```text
1. 读取 Markdown 文件。
2. 把文档切成 chunk。
3. 调用 embedding 模型生成向量。
4. 把 point 写入 Qdrant。
5. 根据 top_k 检索相关 chunk。
6. 把检索结果拼成 prompt 并调用模型回答。
7. 接收 HTTP 请求 POST /rag/query。
```

参考答案：

```text
1. loaders
2. splitters
3. embeddings
4. vector_store
5. retriever
6. generator 或 pipeline
7. routers
```

解释：

```text
RAG 内部能力放 app/rag。
HTTP 接口放 app/routers。
复杂应用编排可以通过 app/services 调用 app/rag。
```

### 练习 2：解释为什么需要 RagChunk

问题：

```text
既然已经有 RagDocument，为什么还需要 RagChunk？
```

参考答案：

```text
因为 RAG 检索通常不是按整篇文档检索，而是按文档切分后的 chunk 检索。
RagDocument 表示加载后的文档，RagChunk 表示切分后的片段。
后续 embedding、Qdrant point、检索结果主要围绕 chunk 工作。
```

### 练习 3：解释 RagChunk 和 Qdrant point 的关系

问题：

```text
RagChunk 的字段后续如何映射到 Qdrant point？
```

参考答案：

```text
RagChunk.chunk_id 可以映射为 Qdrant point.id。
RagChunk.content 会作为 embedding 输入，生成 point.vector。
RagChunk.metadata 会写入 point.payload。
```

### 练习 4：判断是否应该现在创建所有未来文件

问题：

```text
为什么本节没有一次性创建 loaders.py、splitters.py、embeddings.py、vector_store.py、retriever.py、generator.py、pipeline.py？
```

参考答案：

```text
因为这些模块各自对应后续章节的学习内容。
如果现在一次性创建大量空文件，会显得结构很多，但没有真实职责和测试。
当前先创建 app/rag 包和 documents.py，建立边界与内部数据契约；后续学到哪个能力，再新增哪个模块。
```

### 练习 5：区分内部模型和 API 模型

问题：

```text
RagChunk 为什么不放到 app/schemas 里？
```

参考答案：

```text
因为 RagChunk 是 RAG 流水线内部数据模型，不是直接对外的 HTTP 请求或响应模型。
app/schemas 更适合放接口层的请求/响应契约。
把内部模型和 API 模型分开，有利于隐藏内部字段、保持接口稳定，并让 RAG 流程可以独立测试。
```

## 自测问题

### 自测 1：本节为什么不需要打开虚拟机？

参考答案：

```text
因为本节只做 Windows 项目里的 RAG 代码结构设计，不访问 Qdrant，不启动 Docker，不写入向量。
```

### 自测 2：app/rag 的职责是什么？

参考答案：

```text
app/rag 用来放 RAG 领域内部组件，例如文档、chunk、加载、切分、embedding、向量库适配、检索、生成和 pipeline。
```

### 自测 3：文档入库流程和问答流程有什么区别？

参考答案：

```text
文档入库流程负责加载文档、清洗、切 chunk、生成 embedding 并写入向量库。
问答流程负责把用户问题变成 query embedding，检索相关 chunk，再交给模型生成回答。
入库通常在文档更新时运行，问答在用户提问时运行。
```

### 自测 4：RagDocument 表示什么？

参考答案：

```text
RagDocument 表示加载并清洗后的文档，包含 content 和文档级 metadata。
```

### 自测 5：RagChunk 表示什么？

参考答案：

```text
RagChunk 表示文档切分后的一个片段，包含稳定的 chunk_id、chunk 内容和 chunk 级 metadata。
```

### 自测 6：为什么 chunk_id 要稳定？

参考答案：

```text
因为 chunk_id 后续可以作为 Qdrant point id，用于更新、删除、去重和排查。如果每次入库都随机变化，旧数据清理和文档更新会变复杂。
```

### 自测 7：为什么不把所有 RAG 代码放进 router？

参考答案：

```text
router 应该只负责 HTTP 请求接收、调用 service、返回响应。RAG 细节如果放进 router，会导致接口层臃肿、测试困难、复用困难。
```

## 本节复盘

这一节你要真正掌握的是：

```text
1. RAG 是一条流水线，不是一个函数。
2. 文档入库流程和用户问答流程要分开。
3. app/rag 是 RAG 领域内部包。
4. app/services 负责应用服务编排，不应该吞掉所有 RAG 内部细节。
5. app/routers 只做 HTTP 接口层。
6. app/schemas 放 API 请求/响应模型。
7. RagDocument 是加载后的文档。
8. RagChunk 是切分后的片段，后续会映射到 Qdrant point。
9. 当前只建立最小骨架，后续每节再逐步增加真实能力。
```

如果你能讲清楚这些，后面第 10-18 节就不会只是“跟着写代码”，而是知道每段代码为什么应该放在那里。
