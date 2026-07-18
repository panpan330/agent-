# 阶段 4 第 39 节：企业知识库 RAG 最终收尾复盘

## 本节定位

这一节是阶段 4 的最终收尾课。

它不是新增一个复杂功能，也不是再引入一个新框架，而是把阶段 4 的全部内容重新整理成一个完整体系。

阶段 4 一共分成三大部分：

1. Qdrant 主线 RAG：从文档到检索问答。
2. RAG 工程增强：更新删除、调优、混合检索、rerank、安全、性能。
3. Milvus 对比和检索评测：理解向量库选型，并学会用评测脚本判断检索质量。

你现在要从“跟着写了一堆功能”提升到“能完整解释一个 RAG 系统为什么这样设计”。

本节最终目标：

```text
以后别人问你 RAG 是什么、怎么做、有哪些坑、怎么评测、Qdrant 和 Milvus 怎么选，你能讲出一条完整、可信、工程化的答案。
```

## 本节学习目标

学完这一节，你应该能做到：

1. 从整体上解释 RAG 为什么存在。
2. 画出文档入库链路和用户问答链路。
3. 解释 document、chunk、metadata、embedding、vector store、retriever、generator 的关系。
4. 解释 Qdrant 的 collection、point、vector、payload。
5. 解释 Milvus 的 collection、schema、field、entity、index。
6. 说明 Qdrant 和 Milvus 的核心差异与选型思路。
7. 解释 top_k、score_threshold、hybrid search、rerank 分别解决什么问题。
8. 解释 citations、no_context、安全检查为什么是企业 RAG 必备能力。
9. 解释 RAG 性能优化为什么包括缓存、批处理、超时和降级。
10. 解释检索评测为什么要有固定评测集、Hit Rate@K、Recall@K、Precision@K、MRR 和 bad case。
11. 说清楚当前项目已经完成了什么，还缺什么生产级能力。
12. 知道阶段 5 LangGraph 为什么接在 RAG 后面学。

## 一、基础知识铺垫

### 1. 为什么要阶段复盘

学习一个大阶段时，很容易出现这种情况：

```text
每一节当时好像都懂了，但过一段时间以后，只记得写过很多文件。
```

这是正常的。

因为技术知识不是按“文件数量”组织在脑子里的，而是按“问题链路”组织的。

比如 RAG 阶段真正要记住的不是：

```text
我写过 documents.py、loaders.py、splitters.py、vector_store.py...
```

而是：

```text
用户的问题为什么需要知识库？
知识库里的文档怎么变成可检索的数据？
用户问题怎么变成检索请求？
检索结果怎么变成模型上下文？
模型回答怎么保证有出处、可拒答、可评测？
```

阶段复盘的意义就是把零散文件重新组织成知识体系。

### 2. RAG 到底解决什么问题

RAG 的全称是 Retrieval-Augmented Generation，可以理解成：

```text
检索增强生成
```

它解决的是大模型本身的几个限制：

1. 大模型不知道你的私有业务资料。
2. 大模型训练数据可能过时。
3. 大模型可能凭空编造答案。
4. 大模型无法天然引用企业内部文档来源。
5. 大模型不能自动知道用户权限边界。

所以 RAG 的思路是：

```text
先从你的知识库里找资料，再让模型基于这些资料回答。
```

RAG 的关键不是“让模型更聪明”，而是：

```text
让模型回答时有可控、可追溯、可更新的外部资料。
```

### 3. RAG 和普通聊天的区别

普通聊天大致是：

```text
用户问题 -> 大模型 -> 回答
```

RAG 是：

```text
用户问题 -> 检索知识库 -> 找到相关资料 -> 大模型基于资料回答 -> 带出处返回
```

普通聊天主要依赖模型参数里的知识。

RAG 主要依赖外部知识库里的资料。

这就带来一个重要变化：

```text
RAG 系统质量 = 检索质量 + 上下文组织质量 + 模型生成质量 + 安全与评测质量
```

如果只会调用模型，不会检索、不会切文档、不会设计 metadata、不会评测，就不能算真正会做 RAG。

### 4. RAG 和 Tool Calling 的区别

阶段 3 学的是 Tool Calling，阶段 4 学的是 RAG。

它们都可以给模型补能力，但补的是不同能力。

Tool Calling 解决：

```text
模型需要调用外部系统做动作或查实时结构化数据。
```

例如：

```text
查询订单
创建工单
查物流状态
```

RAG 解决：

```text
模型需要查大量非结构化或半结构化知识资料。
```

例如：

```text
退款政策
发货规则
账号安全 FAQ
产品手册
内部制度
```

一个成熟 AI 应用通常会同时用它们：

```text
RAG 查知识
Tool Calling 查业务系统或执行动作
LangGraph 编排多步骤流程
```

阶段 5 学 LangGraph，就是要把这些能力组织成一个有状态的 Agent 流程。

### 5. RAG 和微调的区别

很多人刚学 RAG 时会问：

```text
为什么不直接微调模型，让模型记住知识？
```

RAG 和微调解决的问题不同。

RAG 更适合：

1. 知识经常变化。
2. 文档很多。
3. 需要引用来源。
4. 需要权限控制。
5. 需要可删除、可更新。
6. 不希望每次改资料都重新训练模型。

微调更适合：

1. 改变模型表达风格。
2. 学习固定输出格式。
3. 学习某类任务模式。
4. 少量稳定行为修正。

企业知识库问答通常优先 RAG，而不是微调。

### 6. RAG 的两条主链路

RAG 项目永远要分清两条链路：

```text
文档入库链路
用户问答链路
```

文档入库链路负责把文档变成可检索的数据：

```text
load -> clean -> split -> metadata -> embed -> store
```

用户问答链路负责根据问题找到资料并生成回答：

```text
query -> embed query -> retrieve -> filter -> rerank -> generate -> cite
```

很多 RAG 混乱都来自把这两条链路混在一起。

例如：

```text
chunk 切分是入库阶段的事。
top_k 检索是问答阶段的事。
metadata 既影响入库，也影响问答过滤。
embedding 既用于文档，也用于 query。
```

复盘时一定要能说清楚每个模块属于哪条链路。

### 7. 什么是 document

document 是进入 RAG 系统的原始知识单位。

在当前项目里，document 可以来自：

```text
Markdown 文件
txt 文件
```

以后也可以扩展成：

```text
PDF
Word
网页
数据库记录
企业知识库页面
```

document 通常包含：

```text
content: 文档正文
metadata: 文档来源、标题、类型、权限等信息
```

当前项目里的内部模型是：

```text
RagDocument
```

它的意义是把外部文件统一成项目内部可处理的数据结构。

### 8. 什么是 chunk

chunk 是从 document 切出来的小文本块。

为什么不直接把整篇文档丢进向量库？

因为：

1. 文档太长，embedding 效果会变差。
2. 用户问题通常只对应文档里的某一小段。
3. 模型上下文窗口有限。
4. 检索结果需要尽量精准。
5. 引用来源最好能定位到具体段落。

所以 RAG 入库时会把文档切成 chunk。

当前项目里的内部模型是：

```text
RagChunk
```

每个 chunk 都应该带：

```text
chunk_id
content
source
title
section
chunk_index
chunk_count
permission_group
business_domain
```

chunk 是 RAG 里最核心的数据单位。

### 9. 什么是 metadata

metadata 是描述 chunk 的结构化信息。

正文内容回答：

```text
这段资料说了什么？
```

metadata 回答：

```text
这段资料来自哪里？
属于哪个业务域？
是什么文档类型？
用户有没有权限看？
后续怎么引用它？
更新时怎么删除它？
```

当前项目用 metadata 支撑：

1. 引用来源。
2. 权限过滤。
3. 文档类型过滤。
4. 业务域过滤。
5. 按 source 删除旧 chunks。
6. bad case 分析。
7. Milvus scalar filter。
8. Qdrant payload filter。

所以 metadata 不是附属品，而是企业 RAG 的工程骨架。

### 10. 什么是 embedding

embedding 是把文本变成向量。

简单说：

```text
文本 -> 一组数字
```

例如：

```text
"退款多久到账" -> [0.13, -0.42, 0.88, ...]
```

这些数字不是随机的。好的 embedding 模型会让语义相近的文本在向量空间里更接近。

RAG 里有两类 embedding：

```text
chunk embedding
query embedding
```

chunk embedding 在入库时生成：

```text
chunk content -> vector -> 写入向量库
```

query embedding 在用户提问时生成：

```text
user query -> vector -> 去向量库搜索相似 chunk
```

你要记住一个关键点：

```text
同一个 collection 里的 chunk vector 和 query vector 必须来自兼容的 embedding 模型，并且维度一致。
```

否则相似度搜索没有意义，向量库也可能直接报错。

### 11. 什么是 vector store

vector store 是专门保存和搜索向量数据的存储系统。

它通常保存：

```text
id
vector
payload / scalar fields
```

RAG 里 vector store 的职责是：

```text
根据 query vector 找到最相似的 chunk vectors，并返回对应文本和 metadata。
```

当前阶段学了两个向量库：

1. Qdrant。
2. Milvus。

我们不是为了“多学几个库”而学它们，而是为了理解：

```text
不同向量库都在解决同一类问题，但数据模型、部署复杂度、过滤能力、规模适配不同。
```

### 12. 什么是 retriever

retriever 是检索器。

它不一定等于向量库。

向量库只负责底层搜索。

retriever 负责把业务检索逻辑组织起来，例如：

```text
query embedding
top_k
score_threshold
metadata filter
向量库查询
结果转换
错误映射
```

当前项目里的核心模块是：

```text
app/rag/retriever.py
```

后面又扩展了：

```text
hybrid.py
rerank.py
security.py
evaluation.py
```

它们都围绕“检索结果质量”展开。

### 13. 什么是 generator

generator 是生成器。

它负责把检索结果变成模型可以理解的上下文，然后调用大模型生成回答。

它要处理：

1. 如何组织 retrieved chunks。
2. 如何告诉模型只能基于资料回答。
3. 无资料时是否拒答。
4. 回答里如何返回 citations。
5. 模型调用失败时如何处理。

当前项目里的核心模块是：

```text
app/rag/generator.py
```

RAG 不是“检索完直接把资料塞给模型”那么简单。上下文组织方式会直接影响回答质量。

### 14. 为什么 citations 很重要

citations 是引用来源。

企业 RAG 里，回答必须尽量可追溯。

如果系统回答：

```text
质量问题退货时，用户需要提供照片或视频证明。
```

最好同时返回：

```text
source = refund-return-policy.md
section = 商品质量问题
chunk_id = refund_return_policy_chunk_0003
```

这样用户或客服可以知道答案从哪里来。

没有 citations 的 RAG，很容易变成“看起来像知识库问答，实际上仍然不可验证”。

### 15. 为什么 no_context 很重要

no_context 表示没有找到可用资料。

企业 RAG 必须能拒答。

如果知识库没有资料，系统应该明确说：

```text
当前知识库没有找到足够相关的资料。
```

而不是硬编一个答案。

这就是：

```text
无资料不硬答
```

它是 RAG 可信度的底线。

### 16. 为什么 RAG 需要评测

RAG 效果不能只靠感觉。

如果你改了 chunk_size、top_k、score_threshold、embedding 模型、rerank 策略，必须回答：

```text
效果到底变好了还是变差了？
哪些 query 好了？
哪些 query 坏了？
有没有无资料问题被乱召回？
```

所以 RAG 需要评测集和指标。

阶段 4 后面学到的评测指标包括：

```text
Hit Rate@K
Recall@K
Precision@K
MRR@K
bad case
no-result success rate
```

评测让 RAG 优化从“凭感觉调”变成“用数据调”。

## 二、本节主题系统讲解

### 1. 阶段 4 的完整学习地图

阶段 4 从第 1 节到第 39 节，可以分成 8 组。

第一组：RAG 基础概念。

```text
第 1-8 节
RAG 是什么、完整流程、document/chunk/metadata、embedding、相似度、向量数据库、Qdrant 基础、本地启动 Qdrant
```

第二组：RAG 项目骨架和入库。

```text
第 9-14 节
项目结构、知识文档、加载清洗、chunk 切分、embedding、Qdrant 写入、metadata 设计
```

第三组：基础检索问答。

```text
第 15-21 节
top_k 检索、payload filter、score_threshold、把检索结果交给模型、citations、no_context、错误处理
```

第四组：测试和维护。

```text
第 22-24 节
fake embedding、fake vector store、文档更新删除重新入库、真实 embedding 适配器准备
```

第五组：检索质量增强。

```text
第 25-27 节
chunk/top_k/threshold 调优、混合检索、rerank
```

第六组：企业工程能力。

```text
第 28-30 节
安全、性能、Qdrant 主线项目验收
```

第七组：Milvus 扩展和选型。

```text
第 31-36 节
Milvus vs Qdrant、本地启动 Milvus、核心概念、Milvus 入库检索、metadata filter、选型框架
```

第八组：检索评测和最终复盘。

```text
第 37-39 节
检索评测基础、最小评测脚本、阶段最终收尾
```

这一套学下来，你已经不是只会“调用一个 RAG 框架”，而是知道 RAG 系统内部每一步在做什么。

### 2. 当前项目的 RAG 入库链路

当前项目的入库链路可以这样讲：

```text
data/knowledge_base
        |
        v
loaders.py
读取 Markdown/txt，清洗文本，生成 RagDocument
        |
        v
splitters.py
按标题、段落、chunk_size、overlap 切成 RagChunk
        |
        v
metadata.py
校验 source/title/section/doc_type/business_domain/permission_group 等字段
        |
        v
embeddings.py
生成 fake embedding 或 OpenAI-compatible real embedding
        |
        v
vector_store.py / milvus_store.py
写入 Qdrant point 或 Milvus entity
        |
        v
ingestion.py
编排整个 load -> split -> embed -> store 流程
```

这条链路的关键点是：

1. loader 不负责切 chunk。
2. splitter 不负责生成 embedding。
3. metadata 模块不负责存储，只负责标准化和校验。
4. embedding 模块不关心向量库存哪里。
5. vector store adapter 不负责读文件。
6. ingestion 只做编排，把多个步骤串起来。

这就是模块边界。

模块边界清晰，后续才容易替换：

```text
Markdown loader -> PDF loader
fake embedding -> real embedding
Qdrant adapter -> Milvus adapter
```

### 3. 当前项目的 RAG 问答链路

问答链路可以这样讲：

```text
用户问题
  |
  v
retriever.py
生成 query embedding，带 top_k、score_threshold、payload filter 去向量库检索
  |
  v
RetrievedChunk 列表
  |
  v
security.py
检查权限、Prompt Injection、敏感信息，只保留 safe chunks
  |
  v
rerank.py / hybrid.py
根据策略融合或重排候选结果
  |
  v
generator.py
把 retrieved chunks 整理成上下文，调用模型生成 grounded answer
  |
  v
RagAnswer
answer + citations + status + suggestions
```

这个链路说明 RAG 问答不是一个动作，而是一串动作。

任何一步出问题都会影响最终答案。

例如：

1. query embedding 错，检索就偏。
2. metadata filter 错，可能查不到资料或越权查到资料。
3. top_k 太小，可能漏召回。
4. score_threshold 太高，可能无资料。
5. score_threshold 太低，可能噪声太多。
6. rerank 错，正确资料可能被排后面。
7. generator prompt 不清楚，模型可能脱离资料回答。
8. citations 不做结构化，回答难追溯。

所以真正的 RAG 工程是系统工程，不是单点技巧。

### 4. 当前项目里每个 RAG 文件的职责

下面这张表是以后复习时最有用的文件地图。

| 文件 | 职责 | 你应该能解释什么 |
| --- | --- | --- |
| `documents.py` | 定义 RAG 内部数据模型 | `RagDocument`、`RagChunk`、`RetrievedChunk` 的区别 |
| `loaders.py` | 加载 Markdown/txt 文档 | 文件如何变成 `RagDocument` |
| `splitters.py` | 文档切分 | 为什么要 chunk、chunk_size/overlap/section/chunk_id 怎么来 |
| `metadata.py` | metadata 标准化和校验 | source/title/section/permission_group 等字段为什么重要 |
| `embeddings.py` | fake 和真实 embedding 适配 | 文本如何变向量、维度和批量处理为什么重要 |
| `filters.py` | Qdrant payload filter 构造 | 权限、业务域、来源过滤如何转成查询条件 |
| `vector_store.py` | Qdrant 适配器 | point、vector、payload、upsert、query、delete |
| `milvus_store.py` | Milvus 适配器 | schema、field、entity、index、filter expression |
| `ingestion.py` | 入库编排 | load -> split -> embed -> store 如何串起来 |
| `retriever.py` | 基础检索编排 | query embedding、top_k、score_threshold、filter、错误映射 |
| `generator.py` | RAG 回答生成 | retrieved chunks 如何变上下文，citations/no_context 怎么返回 |
| `tuning.py` | 参数观察工具 | chunk 参数、retrieval 参数怎么对质量产生影响 |
| `hybrid.py` | 混合检索 | 关键词检索和向量检索如何融合 |
| `rerank.py` | 重排序 | 召回候选如何二次排序，为什么要保留原始排名 |
| `security.py` | 检索结果安全检查 | 权限复查、Prompt Injection、敏感信息扫描 |
| `performance.py` | 性能学习工具 | cache key、TTL cache、batch、near_timeout、降级 |
| `evaluation.py` | 检索评测 | 固定样本、指标计算、bad case 报告 |
| `errors.py` | RAG 错误映射 | embedding/vector store 错误如何变成稳定错误码 |

你以后看项目，不要从文件名死记，而要按链路理解：

```text
入库链路用哪些文件？
问答链路用哪些文件？
质量优化用哪些文件？
安全性能评测用哪些文件？
```

### 5. Qdrant 主线到底学到了什么

Qdrant 是阶段 4 的主线向量库。

你需要掌握的核心概念是：

```text
collection
point
vector
payload
query/search
filter
score_threshold
```

可以这样解释：

```text
Qdrant 的 collection 类似一个向量集合。
每个 point 是一条向量记录。
point 里包含 id、vector 和 payload。
vector 用于相似度搜索。
payload 保存 metadata，用于过滤、展示和引用来源。
```

当前项目里：

```text
一个 RagChunk -> 一个 Qdrant point
chunk embedding -> point vector
chunk metadata -> point payload
chunk_id -> point id 或 payload 中的稳定标识
```

Qdrant 主线让你跑通了：

```text
文档切 chunk -> 生成 embedding -> 写入 Qdrant -> 用户 query 检索 -> 返回 RetrievedChunk -> 模型回答
```

这是企业知识库 RAG 的最小主线。

### 6. Milvus 扩展到底学到了什么

Milvus 是阶段 4 后半段补充的向量库。

你需要掌握的核心概念是：

```text
collection
schema
field
entity
primary key
vector field
scalar field
index
filter expression
```

可以这样解释：

```text
Milvus 的 collection 需要 schema。
schema 定义每条 entity 有哪些 field。
其中一个 field 通常是主键，一个 field 是 vector，其他 field 是 metadata scalar fields。
向量 field 用于相似度检索，scalar fields 用于 metadata 过滤。
index 用于加速向量检索或标量过滤。
```

当前项目里：

```text
一个 RagChunk -> 一个 Milvus entity
chunk embedding -> vector field
metadata -> scalar fields
chunk_id -> primary key
```

Milvus 学习的价值不是替代 Qdrant 主线，而是让你看懂向量数据库不是只有一种数据模型。

### 7. Qdrant 和 Milvus 怎么选

阶段 4 的选型结论是：

```text
当前学习项目继续用 Qdrant 做主线，Milvus 作为可切换 adapter 和大规模场景对比能力保留。
```

你可以这样讲：

Qdrant 更适合：

1. 学习上手。
2. 中小规模 RAG。
3. 快速本地验证。
4. 简单部署。
5. payload filter 使用直观。

Milvus 更适合：

1. 更大规模向量检索。
2. 更明确的 schema 管理。
3. 更复杂的索引和存储扩展。
4. 团队有一定运维能力。
5. 未来可能走分布式部署。

不要说：

```text
Qdrant 一定比 Milvus 好
Milvus 一定比 Qdrant 好
```

更专业的说法是：

```text
选择向量库要看数据规模、部署复杂度、metadata filter 需求、团队运维能力、成本和项目阶段。
```

### 8. 检索质量为什么不是只看向量库

很多初学者会把 RAG 效果归因于向量库：

```text
换个向量库是不是就准了？
```

其实检索质量由很多因素共同决定：

1. 原始文档质量。
2. 文档清洗质量。
3. chunk 切分策略。
4. metadata 设计。
5. embedding 模型。
6. 向量相似度和索引。
7. top_k。
8. score_threshold。
9. filter。
10. hybrid search。
11. rerank。
12. query 改写。
13. 评测集覆盖度。

向量库只是其中一环。

如果文档本身写得乱、chunk 切得不合理、metadata 缺失，即使用很强的向量库，也很难得到好结果。

### 9. top_k、score_threshold、hybrid、rerank 的关系

这几个概念都和检索质量有关，但职责不同。

`top_k` 解决：

```text
最多返回多少条候选资料。
```

`score_threshold` 解决：

```text
低相关结果要不要拦截。
```

`hybrid search` 解决：

```text
只靠向量检索可能漏掉关键词、编号、专有名词；只靠关键词又不懂语义，所以把两者融合。
```

`rerank` 解决：

```text
第一阶段召回结果不一定排序最好，需要二次重排，把更可能有用的资料放前面。
```

它们不是互相替代，而是层层配合：

```text
召回候选 -> 过滤低相关 -> 融合多路候选 -> 重排序 -> 交给模型
```

### 10. 安全为什么必须在资料进入模型前做

RAG 安全不是可有可无。

检索结果进入模型前，至少要考虑：

1. 用户有没有权限看这段资料。
2. 资料里是否有 Prompt Injection 指令。
3. 资料里是否包含敏感信息。
4. 模型是否可能被不可信资料误导。

如果安全检查放在模型回答之后，问题已经发生了：

```text
模型可能已经读到了不该读的资料。
```

所以当前项目把安全检查设计在：

```text
retrieved chunks -> model context
```

之间。

这条边界很重要。

### 11. 性能为什么不只是“跑得快”

RAG 性能包括很多方面：

1. 文档入库速度。
2. embedding 调用耗时。
3. 向量库查询耗时。
4. rerank 耗时。
5. 模型生成耗时。
6. 网络调用超时。
7. 高并发下资源消耗。
8. 缓存命中率。
9. 降级策略。

阶段 4 学了：

```text
cache key
TTL cache
batch plan
near_timeout
degradation decision
```

这些不是生产级完整实现，但已经让你理解：

```text
RAG 系统不是只要答案准，还要在可接受时间内稳定返回。
```

### 12. 评测让 RAG 优化有方向

第 37-38 节最重要的思想是：

```text
没有评测，就没有可靠优化。
```

现在项目里有：

```text
data/rag_eval/retrieval_cases.json
scripts/rag_retrieval_eval.py
app/rag/evaluation.py
```

你可以用固定样本观察：

1. Hit Rate@K。
2. Recall@K。
3. Precision@K。
4. MRR@K。
5. no-result success rate。
6. bad case。

这意味着以后你改任何检索策略，都可以先问：

```text
指标变了吗？
bad case 变了吗？
有没有为了提高召回而引入更多噪声？
有没有为了减少噪声而漏掉正确资料？
```

这就是工程化学习和随便试试的区别。

## 三、当前项目已经具备的能力

### 1. 入库能力

当前项目已经能做到：

1. 准备 Markdown/txt 示例知识库。
2. 加载文档并清洗文本。
3. 按标题和段落切分 chunk。
4. 为 chunk 生成稳定 chunk_id。
5. 标准化 metadata。
6. 校验必备 metadata 字段。
7. 生成 deterministic fake embedding。
8. 接入 OpenAI-compatible 真实 embedding 适配器。
9. 写入 Qdrant。
10. 写入 Milvus。
11. 按 source 删除旧 chunks。
12. 重新刷新目录入库。

这说明你已经学会了 RAG 的入库主线。

### 2. 检索能力

当前项目已经能做到：

1. 把用户问题变成 query embedding。
2. 使用 top_k 检索。
3. 使用 score_threshold 过滤低相关结果。
4. 使用 permission_group、business_domain、doc_type、source 过滤。
5. 从 Qdrant 返回统一 `RetrievedChunk`。
6. 从 Milvus 返回统一 `RetrievedChunk`。
7. 使用关键词检索做本地 baseline。
8. 融合关键词检索和向量检索结果。
9. 对候选结果做规则 rerank。
10. 输出原始排名、重排排名和分数拆解。

这说明你已经知道“检索”不是一句 search，而是一套策略组合。

### 3. 生成回答能力

当前项目已经能做到：

1. 把 `RetrievedChunk` 整理成模型上下文。
2. 要求模型基于资料回答。
3. 返回结构化 `RagAnswer`。
4. 返回 citations。
5. 无资料时返回 `no_context`。
6. 无资料时不调用模型硬答。
7. 使用 fake LLM 测试生成链路。

这说明你已经掌握了基础 RAG 回答生成。

### 4. 安全、性能和错误处理能力

当前项目已经能做到：

1. RAG embedding 错误映射。
2. vector store 错误映射。
3. collection 配置错误映射。
4. 权限复查。
5. Prompt Injection 检测。
6. 敏感信息识别。
7. safe chunks 过滤。
8. 检索缓存 key。
9. 内存 TTL cache 演示。
10. embedding batch plan。
11. near_timeout 判断。
12. 降级决策建模。

这些能力让 RAG 从“能跑”逐步走向“更像工程项目”。

### 5. 测试和评测能力

当前项目已经能做到：

1. 用 fake embedding 测试，不依赖真实模型。
2. 用 fake vector store 测试，不依赖真实 Qdrant。
3. 用 mock/fake LLM 测试，不真实调用模型。
4. 测试入库、检索、生成、错误、安全、性能。
5. 用固定 retrieval cases 做检索评测。
6. 输出 summary 和 bad case。

这说明你已经开始具备 AI 工程里非常重要的能力：

```text
不是只会写 demo，而是知道怎么验证 demo。
```

## 四、当前项目还不是生产级的地方

这一部分很重要。

学完阶段 4，不代表你已经做出了完整生产级 RAG 系统。更准确地说：

```text
你已经掌握了企业 RAG 的核心基础，并做出了学习版主线项目。
```

还缺的生产级能力包括：

### 1. 文档解析还不完整

当前主要支持 Markdown/txt。

生产中常见：

1. PDF。
2. Word。
3. Excel。
4. HTML。
5. 飞书/语雀/Confluence 页面。
6. 扫描件 OCR。

这些文档解析会遇到：

1. 表格。
2. 标题层级。
3. 页眉页脚。
4. 图片。
5. 扫描噪声。
6. 多栏排版。

这些后面可以作为扩展学习。

### 2. embedding 还没有作为默认真实链路

项目里已经有真实 embedding 适配器，但很多测试和 smoke 仍然使用 fake embedding。

这是刻意设计的：

```text
自动化测试不能依赖真实模型和费用。
```

但生产环境必须配置真实 embedding 模型，并保证：

1. 文档 embedding 和 query embedding 模型一致。
2. 向量维度和 collection 配置一致。
3. batch size 合理。
4. 错误和重试策略稳定。
5. 成本可控。

### 3. 权限系统还只是学习版

当前的 `permission_group` 是学习版权限字段。

生产中权限可能来自：

1. 用户角色。
2. 部门。
3. 数据范围。
4. 文档密级。
5. 租户隔离。
6. 临时授权。

真正的权限过滤应该和 Java 业务系统或统一权限系统结合。

### 4. 评测集还很小

当前只有最小 retrieval cases。

生产级评测还需要：

1. 更多 query。
2. 多种问法。
3. 多业务域覆盖。
4. 难例和边界问题。
5. 无答案问题。
6. 权限越界问题。
7. 最终答案评测。
8. groundedness 评测。
9. 历史版本趋势对比。

第 38 节只是把方法立起来。

### 5. 还没有完整 API 化的 RAG 产品接口

当前 RAG 能力更多是内部模块、脚本和测试。

生产项目通常还需要：

1. 文档上传接口。
2. 文档列表接口。
3. 文档删除接口。
4. 知识库重建任务。
5. RAG 问答接口。
6. 引用来源展示。
7. 管理后台。
8. 异步任务状态查询。

这些可以在后续项目化阶段继续补。

### 6. 还没有 Docker Compose 一键编排

现在 Qdrant 和 Milvus 是在 VMware Ubuntu Docker 里手动启动过。

生产化阶段还要学：

1. Python AI service Dockerfile。
2. Java service Dockerfile。
3. Qdrant/Milvus compose。
4. 环境变量注入。
5. 数据卷。
6. 健康检查。
7. 服务依赖。

这会在后续工程化阶段再做。

## 五、你现在应该能讲出的面试版答案

### 1. 一分钟讲 RAG

可以这样说：

```text
RAG 是检索增强生成。它不是只把问题丢给大模型，而是先把企业文档切成 chunk，生成 embedding，写入向量数据库。用户提问时，系统把 query 也转成 embedding，在向量库里检索相关 chunk，再把这些 chunk 作为上下文交给模型回答。这样模型可以基于企业私有资料回答，并且能返回引用来源。工程上还要处理 metadata 权限过滤、无资料拒答、检索质量评测、安全检查、缓存和错误处理。
```

### 2. 两分钟讲当前项目

可以这样说：

```text
我的项目里有一个 Python FastAPI AI 服务，内部有独立的 app/rag 包。入库链路会读取 data/knowledge_base 里的 Markdown/txt 文档，清洗后转成 RagDocument，再按标题和段落切成 RagChunk。每个 chunk 会带 source、title、section、doc_type、business_domain、permission_group 等 metadata，然后生成 embedding，写入 Qdrant。后面我又做了 Milvus adapter，可以把同一批 chunk 映射成 Milvus entity，支持 schema、index、upsert、search 和 metadata scalar filter。

问答链路里，用户 query 会生成 query embedding，带 top_k、score_threshold 和 metadata filter 去检索，返回统一 RetrievedChunk。检索结果可以做安全检查、混合检索融合、rerank，再由 generator 组织成模型上下文生成回答。回答会返回结构化 citations；如果没有资料，会返回 no_context，不让模型硬答。测试里用 fake embedding、fake vector store 和 fake LLM 隔离外部依赖。最后我还加了 retrieval evaluation，用固定样本计算 Hit Rate@K、Recall@K、Precision@K、MRR 和 bad case。
```

### 3. 讲 Qdrant 和 Milvus 选型

可以这样说：

```text
Qdrant 和 Milvus 都能作为 RAG 的 vector store。Qdrant 的 point/payload 模型比较直观，本地部署和学习成本低，适合中小规模 RAG 和快速验证。Milvus 更偏向大规模向量检索，有明确 schema、field、entity 和 index 概念，适合更复杂的索引和分布式扩展场景，但部署和运维成本更高。所以我当前项目用 Qdrant 做主线，Milvus 做 adapter 和对比学习。真实选型要看数据规模、filter 复杂度、运维能力、成本和项目阶段。
```

### 4. 讲检索质量怎么优化

可以这样说：

```text
RAG 检索质量不是只靠向量库决定的。首先文档本身要清晰，chunk 切分要合理，metadata 要完整。检索时 top_k 决定候选数量，score_threshold 控制低相关结果，payload filter 控制权限和业务范围。向量检索适合语义相似，关键词检索适合编号、专有名词和精确词，所以可以做 hybrid search。召回之后还可以 rerank，把更相关的 chunk 排到前面。最后必须用固定评测集看 Hit Rate@K、Recall@K、Precision@K、MRR 和 bad case，而不是凭感觉判断。
```

### 5. 讲 RAG 的安全边界

可以这样说：

```text
企业 RAG 不能把检索到的所有资料直接交给模型。检索结果进入模型上下文前要做权限复查，确认用户能看这些资料；还要检查文档里是否有 Prompt Injection 风险和敏感信息。无资料时不能硬答，必须返回 no_context。回答要带 citations，方便追溯。AI 也不能绕过 Java 业务系统直接访问数据库或执行操作，需要走白名单工具和权限校验。
```

## 六、以后复习阶段 4 的顺序

如果你以后忘了 RAG，建议不要从第 1 节重新全文刷起。

可以按这个顺序复习：

1. 先看本节最终复盘。
2. 再看第 30 节 Qdrant 主线项目验收。
3. 再看第 38 节检索评测脚本。
4. 如果忘了基础概念，看第 1-8 节。
5. 如果忘了入库，看第 9-14 节。
6. 如果忘了检索问答，看第 15-21 节。
7. 如果忘了优化，看第 25-29 节。
8. 如果忘了 Milvus，看第 31-36 节。

也可以按问题复习：

```text
我不懂 chunk -> 看第 3、12 节
我不懂 embedding -> 看第 4、13、24 节
我不懂 Qdrant -> 看第 6、7、8、13、15、16、17 节
我不懂 Milvus -> 看第 31-35 节
我不懂评测 -> 看第 37、38 节
我不懂安全 -> 看第 28 节
我不懂性能 -> 看第 29 节
```

## 七、阶段 4 验收清单

下面这些问题，如果你能回答清楚，阶段 4 就算真正学扎实了。

### 基础概念

- [x] 能解释 RAG 是什么。
- [x] 能解释 RAG 和普通聊天的区别。
- [x] 能解释 RAG 和 Tool Calling 的区别。
- [x] 能解释 RAG 和微调的区别。
- [x] 能解释文档入库链路。
- [x] 能解释用户问答链路。

### 数据模型

- [x] 能解释 document。
- [x] 能解释 chunk。
- [x] 能解释 metadata。
- [x] 能解释 embedding。
- [x] 能解释 vector store。
- [x] 能解释 retrieved chunk。
- [x] 能解释 citation。

### 向量库

- [x] 能解释 Qdrant collection、point、vector、payload。
- [x] 能解释 Milvus collection、schema、field、entity、index。
- [x] 能解释 Qdrant 和 Milvus 的差异。
- [x] 能说明当前项目为什么 Qdrant 做主线、Milvus 做扩展。

### 检索质量

- [x] 能解释 top_k。
- [x] 能解释 score_threshold。
- [x] 能解释 payload filter。
- [x] 能解释 hybrid search。
- [x] 能解释 rerank。
- [x] 能解释 bad case。

### 企业工程

- [x] 能解释 no_context。
- [x] 能解释 citations。
- [x] 能解释权限过滤。
- [x] 能解释 Prompt Injection 风险。
- [x] 能解释敏感信息扫描。
- [x] 能解释缓存、批处理、超时、降级。
- [x] 能解释 RAG 错误映射。

### 评测

- [x] 能解释为什么要固定评测集。
- [x] 能解释 Hit Rate@K。
- [x] 能解释 Recall@K。
- [x] 能解释 Precision@K。
- [x] 能解释 MRR@K。
- [x] 能解释 no-result case。
- [x] 能运行最小检索评测脚本。

## 八、阶段 4 常用命令

进入项目：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
```

运行全部测试：

```powershell
uv run pytest -q
```

运行本地检索评测脚本：

```powershell
uv run python scripts/rag_retrieval_eval.py
```

运行 Qdrant 入库 smoke：

```powershell
uv run python scripts/rag_ingest_smoke.py
```

运行 Qdrant 检索 smoke：

```powershell
uv run python scripts/rag_retrieve_smoke.py
```

运行 Milvus 入库检索 smoke：

```powershell
uv run python scripts/rag_milvus_smoke.py
```

运行 Milvus filter/index smoke：

```powershell
uv run python scripts/rag_milvus_filter_smoke.py
```

注意：

```text
rag_retrieval_eval.py 不需要虚拟机。
rag_ingest_smoke.py 和 rag_retrieve_smoke.py 需要 Qdrant 正在运行。
rag_milvus_smoke.py 和 rag_milvus_filter_smoke.py 需要 Milvus 正在运行。
```

如果以后你问“下一节学什么”，阶段 5 初期不一定需要虚拟机。但如果某节要跑 Qdrant 或 Milvus，我会提前告诉你打开 VMware。

## 九、阶段 4 和阶段 5 的衔接

阶段 4 解决的是：

```text
怎么让 AI 根据企业知识库回答问题。
```

阶段 5 要解决的是：

```text
怎么把 RAG、Tool Calling、用户确认、多步骤流程组织成一个可恢复、可控制的 Agent。
```

你已经有了：

1. FastAPI AI 服务。
2. Java mock 业务服务。
3. Tool Calling 基础。
4. 用户确认机制。
5. 创建工单流程。
6. RAG 知识库能力。
7. 检索评测脚本。

接下来 LangGraph 会把这些能力串起来。

阶段 5 可能会学：

1. LangGraph 是什么。
2. StateGraph 是什么。
3. state schema 怎么设计。
4. node 是什么。
5. edge 是什么。
6. conditional edge 是什么。
7. checkpoint 是什么。
8. thread_id 是什么。
9. interrupt 和 human-in-the-loop。
10. 用 RAG 判断能否直接回答。
11. 不够回答时创建工单。
12. 用户确认后调用 Java API。

所以阶段 5 不是突然换方向，而是承接前面所有能力。

## 十、本节练习与参考答案

### 练习 1：画出 RAG 的两条链路

题目：写出文档入库链路和用户问答链路。

参考答案：

文档入库链路：

```text
load -> clean -> split -> metadata -> embed -> store
```

用户问答链路：

```text
query -> query embedding -> retrieve -> filter/rerank/security -> generate -> cite
```

### 练习 2：解释 chunk 和 metadata

题目：chunk 和 metadata 分别解决什么问题？

参考答案：

chunk 是被检索和传给模型的文本片段，解决“把长文档拆成可检索小块”的问题。metadata 是描述 chunk 的结构化信息，解决来源追踪、权限过滤、业务域过滤、文档更新删除、引用来源和调试评测的问题。

### 练习 3：解释 Qdrant point

题目：Qdrant 的 point 对应当前项目里的什么？

参考答案：

一个 Qdrant point 对应一个 RAG chunk。point 里的 vector 对应 chunk embedding，payload 对应 chunk metadata，id 或 payload 中的 chunk_id 用于稳定定位这段资料。

### 练习 4：解释 Milvus entity

题目：Milvus 的 entity 对应当前项目里的什么？

参考答案：

一个 Milvus entity 对应一个 RAG chunk。entity 必须符合 collection schema，其中 primary key 可以对应 chunk_id，vector field 保存 chunk embedding，scalar fields 保存 source、section、permission_group、business_domain 等 metadata。

### 练习 5：区分 top_k 和 score_threshold

题目：top_k 和 score_threshold 分别控制什么？

参考答案：

top_k 控制最多返回多少条候选结果。score_threshold 控制低于相关性门槛的结果是否被过滤。top_k 解决数量问题，score_threshold 解决最低相关性问题。

### 练习 6：解释 hybrid search

题目：为什么企业 RAG 里可能需要 hybrid search？

参考答案：

因为向量检索适合语义相似，但可能漏掉订单号、专有名词、精确术语；关键词检索适合精确匹配，但不懂语义。hybrid search 把关键词检索和向量检索融合，可以提高召回的稳定性。

### 练习 7：解释 rerank

题目：rerank 在 RAG 链路中的位置和作用是什么？

参考答案：

rerank 位于召回之后、生成之前。第一阶段检索返回候选 chunk 后，rerank 对候选结果重新排序，把更可能回答问题的资料排到前面，减少模型看到噪声资料的概率。

### 练习 8：解释 no_context

题目：为什么无资料时不能让模型硬答？

参考答案：

因为企业 RAG 要求回答基于企业资料。没有检索到可用资料时，如果让模型硬答，模型可能凭自己的知识或猜测编造答案。正确做法是返回 no_context，并提示当前知识库没有足够资料。

### 练习 9：解释检索评测

题目：为什么 RAG 检索优化必须有固定评测集？

参考答案：

固定评测集能让每次修改检索策略后面对同一批 query 和 expected target，方便比较 Hit Rate@K、Recall@K、Precision@K、MRR 和 bad case 变化。如果每次问题都不一样，就无法判断效果变化来自代码改动还是样本变化。

### 练习 10：讲出阶段 4 当前项目

题目：用 3-5 句话描述阶段 4 当前项目已经做到什么。

参考答案：

当前项目已经实现了学习版企业知识库 RAG。它能读取 Markdown/txt 文档，切分 chunk，生成 embedding，并写入 Qdrant，也支持 Milvus adapter。用户提问时可以按 top_k、score_threshold 和 metadata filter 检索，返回 `RetrievedChunk`，再由模型基于资料回答并返回 citations；无资料时返回 no_context。项目还补充了混合检索、rerank、安全检查、性能工具和检索评测脚本。

## 十一、自测题与答案

### 自测 1

问题：RAG 的核心价值是什么？

答案：让模型基于外部知识库回答问题，使回答可以使用私有资料、更新资料、引用来源，并减少凭空编造。

### 自测 2

问题：文档入库链路和用户问答链路最大的区别是什么？

答案：入库链路把文档变成可检索数据；问答链路根据用户问题检索这些数据并生成回答。

### 自测 3

问题：metadata 为什么不是可选的小细节？

答案：因为 metadata 支撑引用来源、权限过滤、业务域过滤、文档删除更新、调试和评测，是企业 RAG 的工程基础。

### 自测 4

问题：embedding 维度为什么必须和 collection 配置一致？

答案：因为向量库要求同一个向量字段里的向量维度一致，否则无法计算相似度，也可能直接写入或查询失败。

### 自测 5

问题：Qdrant 的 payload 和 Milvus 的 scalar fields 在 RAG 中都可以承担什么职责？

答案：都可以保存 metadata，并用于过滤、引用来源、调试和数据管理。

### 自测 6

问题：为什么检索结果要先做安全检查再交给模型？

答案：因为模型一旦读取了不该看的资料或恶意指令，风险已经发生。安全检查应该在资料进入模型上下文之前完成。

### 自测 7

问题：Hit Rate@K 高但 Precision@K 低，可能说明什么？

答案：说明系统经常能找回至少一个相关资料，但同时也返回了较多不相关资料，模型上下文可能有噪声。

### 自测 8

问题：MRR@K 主要关注什么？

答案：关注第一个相关结果排得是否靠前。相关结果越靠前，MRR 越高。

### 自测 9

问题：为什么阶段 5 要学 LangGraph？

答案：因为当前已经具备 RAG、Tool Calling、用户确认和 Java API 调用能力，接下来需要用 LangGraph 把这些能力编排成有状态、多步骤、可恢复、可人工介入的 Agent 流程。

### 自测 10

问题：学完阶段 4 后，是否等于已经做出了生产级 RAG？

答案：不是。更准确地说，是已经掌握企业 RAG 的核心基础，并做出了学习版主线项目。生产级还需要更完善的文档解析、权限系统、评测集、API 化、异步任务、部署、监控和运维。

## 十二、本节结论

阶段 4 到这里可以正式收尾。

你现在已经建立了 RAG 的完整基础体系：

```text
概念 -> 文档 -> chunk -> metadata -> embedding -> 向量库 -> 检索 -> 生成 -> 引用 -> 拒答 -> 安全 -> 性能 -> 评测 -> 选型
```

这条链路就是企业知识库 RAG 的核心。

后面继续学习时，不要把阶段 4 当成结束后就丢掉的内容。阶段 5 LangGraph 会继续使用它：

```text
用户问题能用知识库回答 -> 走 RAG
知识库不够或需要操作业务系统 -> 走 Tool Calling
需要多步骤状态管理和人工确认 -> 走 LangGraph
```

阶段 4 给你准备的是“知识库能力”，阶段 5 要学习的是“把知识库能力和业务动作组织成可控 Agent”。
