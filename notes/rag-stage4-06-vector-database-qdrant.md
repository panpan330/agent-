# 阶段 4 第 6 节：向量数据库是什么，为什么先选 Qdrant

> 本节结论：向量数据库不是“大模型”，也不是“知识库答案生成器”，它主要负责保存向量、保存 metadata/payload、按向量相似度检索、按业务字段过滤、返回最相关的候选内容。RAG 需要向量数据库，是因为企业知识库里的 chunk 数量会越来越多，不能每次都靠普通文件或普通数据库全量遍历。我们先选 Qdrant，是为了用较低的部署和概念成本跑通 RAG 主线；Milvus 也很重要，但更适合在理解完整 RAG 流程后作为进阶对比学习。

## 生成笔记前的教学复核

这一节仍然是概念课，不启动 Qdrant，不写入真实向量，也不接入代码。

这一节必须讲清：

```text
1. 为什么 RAG 需要向量数据库。
2. 向量数据库和普通数据库有什么区别。
3. 向量数据库到底保存什么。
4. collection、point、vector、payload、id 分别是什么。
5. search、top_k、score、filter 在检索里分别负责什么。
6. 向量数据库不能替代哪些东西。
7. 为什么阶段 4 先用 Qdrant。
8. 为什么 Milvus 不是不学，而是后面学。
9. 本项目后续会怎样从 Qdrant 过渡到 Milvus 对比。
```

## 本节一句话定位

第 4 节讲了：

```text
文本可以变成向量。
```

第 5 节讲了：

```text
向量之间可以比较相似度。
```

第 6 节要解决的问题是：

```text
如果企业知识库里有大量 chunk 和向量，这些向量放在哪里、怎么高效查、怎么按权限过滤？
```

答案就是：

```text
向量数据库。
```

## 先从最朴素的问题开始

假设我们现在有一个企业知识库，里面只有 5 个 chunk。

我们可以把它们写在一个 Python list 里：

```text
chunk 1：订单超过 72 小时未发货，可以创建投诉工单。
chunk 2：用户收到商品 7 天内可以申请退货。
chunk 3：员工请假需要提前一天提交申请。
chunk 4：会员积分可以在个人中心查看。
chunk 5：登录密码可以通过短信验证码重置。
```

每个 chunk 再生成一个 embedding：

```text
chunk 1 vector: [...]
chunk 2 vector: [...]
chunk 3 vector: [...]
chunk 4 vector: [...]
chunk 5 vector: [...]
```

用户问：

```text
订单三天没发货怎么办？
```

系统也给用户问题生成一个 query embedding：

```text
query vector: [...]
```

然后逐个比较：

```text
query vector vs chunk 1 vector
query vector vs chunk 2 vector
query vector vs chunk 3 vector
query vector vs chunk 4 vector
query vector vs chunk 5 vector
```

因为只有 5 个 chunk，逐个比较完全可以。

但是企业知识库不会只有 5 个 chunk。

真实情况可能是：

```text
5 个 chunk
500 个 chunk
5 万个 chunk
500 万个 chunk
```

这时候你每次提问都全量遍历，就会出现几个问题：

```text
1. 慢：每次都要比较大量向量。
2. 难维护：向量、原文、来源、权限字段混在一起不好管理。
3. 难过滤：只查“当前用户有权限看的文档”会变麻烦。
4. 难更新：文档改了、删除了、重新入库了，需要可靠地更新对应 chunk。
5. 难扩展：后面要混合检索、索引、批量写入、召回调优，会越来越复杂。
```

向量数据库就是为了解决这些问题出现的。

## 向量数据库是什么

你可以先这样理解：

```text
向量数据库 = 专门保存向量，并且能高效按向量相似度搜索的数据库。
```

更完整一点：

```text
向量数据库 =
保存向量
+ 保存向量关联的业务信息
+ 支持相似度搜索
+ 支持 metadata/payload 过滤
+ 支持更新、删除、批量写入
+ 支持索引和性能优化
```

在 RAG 里，向量数据库通常负责：

```text
文档 chunk 入库：
chunk 文本 -> embedding vector -> 写入向量数据库

用户问题检索：
用户问题 -> query embedding -> 向量数据库搜索相似 chunk
```

它不是“会思考的 AI”。

它更像一个很专业的仓库管理员：

```text
你给我一个 query vector，
我帮你从一堆 chunk vector 里找最像的几个，
并且把它们的原文、标题、来源、权限字段一起返回。
```

## 普通文件能不能存向量

能。

比如你可以把 chunk 和 vector 存成 JSON：

```text
[
  {
    "id": "chunk-001",
    "content": "订单超过 72 小时未发货，可以创建投诉工单。",
    "vector": [0.12, 0.78, 0.21],
    "metadata": {
      "source": "order_policy.md",
      "department": "customer_service"
    }
  }
]
```

这对学习早期是可以的。

但是它不适合真实 RAG 主线。

原因是：

```text
1. 每次查询都要读文件。
2. 文件变大以后读取和解析成本高。
3. 多人并发查询会麻烦。
4. 更新某个 chunk 不方便。
5. 按 metadata 过滤要自己写很多逻辑。
6. 没有专业向量索引。
```

文件适合做最小演示，不适合做长期服务。

## MySQL / PostgreSQL 能不能存向量

也能。

普通关系型数据库当然可以存这些字段：

```text
id
content
vector
source
department
permission_group
created_at
updated_at
```

但是关键不只是“能存”，而是：

```text
能不能高效地按向量相似度搜索。
```

关系型数据库最擅长的是：

```text
1. 结构化数据。
2. 事务。
3. 精确查询。
4. JOIN。
5. 唯一约束。
6. 业务数据一致性。
```

比如：

```sql
SELECT * FROM orders WHERE order_id = 'A1001';
```

这类查询是关系型数据库的强项。

但 RAG 检索问的是：

```text
请找出和“订单三天没发货怎么办”语义最像的 5 个 chunk。
```

这不是传统的精确匹配。

它需要比较高维向量的相似度，并且通常需要索引来加速。

PostgreSQL 也有 pgvector 这种扩展，可以做向量检索。后续如果走工程扩展路线，也可以学。

但阶段 4 先选专门的向量数据库，是因为它能让你更直接地理解 RAG 里的：

```text
vector
collection
point
payload
filter
top_k search
```

这些核心概念。

## 向量数据库和普通数据库的主要区别

可以先看这张表：

| 对比点 | 普通关系型数据库 | 向量数据库 |
| --- | --- | --- |
| 核心数据 | 表、行、列 | collection、point/vector、payload |
| 典型查询 | 精确匹配、范围查询、JOIN | 相似度搜索、近邻搜索、payload filter |
| 典型问题 | 订单 A1001 的状态是什么 | 哪些 chunk 和这个问题语义最接近 |
| 排序依据 | 时间、金额、字段值 | similarity score / distance |
| 强项 | 事务、一致性、结构化业务数据 | 高维向量检索、语义召回 |
| 在 RAG 里的位置 | 存业务数据、用户、权限、任务记录 | 存 chunk 向量和检索索引 |

注意：

```text
向量数据库不是用来完全替代 MySQL/PostgreSQL 的。
```

企业项目里常见组合是：

```text
MySQL/PostgreSQL：用户、订单、权限、文档记录、业务状态
向量数据库：chunk 向量、payload、相似度检索
对象存储/文件系统：原始 PDF、Word、图片、Markdown 文件
LLM：根据检索结果生成回答
```

每个组件有自己的职责。

## 向量数据库在 RAG 里的位置

RAG 主线可以分成两条流水线。

第一条是入库流水线：

```text
原始文档
-> 文本解析
-> 清洗
-> chunk 切分
-> embedding
-> 写入向量数据库
```

第二条是问答流水线：

```text
用户问题
-> query embedding
-> 向量数据库检索
-> 返回相关 chunk
-> 拼 prompt
-> 模型回答
-> 返回答案和引用来源
```

向量数据库主要参与两步：

```text
1. 入库时保存 chunk embedding。
2. 问答时根据 query embedding 找相似 chunk。
```

它不负责：

```text
1. 把 PDF 解析成文本。
2. 判断 chunk 应该怎么切。
3. 调用 embedding 模型。
4. 生成最终自然语言答案。
5. 判断用户是否真的有权限。
6. 评价答案质量。
```

这些事情要由 RAG 系统里的其他模块完成。

## 向量数据库到底保存什么

在 RAG 场景里，一条最小但完整的数据通常包含：

```text
id
content
vector
metadata / payload
```

用更接近 Qdrant 的说法，是：

```text
point = id + vector + payload
```

其中：

| 字段 | 含义 | 在 RAG 里的作用 |
| --- | --- | --- |
| id | 这一条向量记录的唯一标识 | 更新、删除、去重、追踪来源 |
| vector | chunk 文本生成的 embedding | 用来做相似度检索 |
| payload | 这条向量关联的业务信息 | 返回原文、来源、标题、权限、过滤条件 |
| content | chunk 原文，通常放在 payload 里 | 最终交给模型生成答案 |

举一个概念例子：

```json
{
  "id": "order-policy-001",
  "vector": [0.12, 0.78, 0.21],
  "payload": {
    "content": "订单超过 72 小时未发货，可以创建投诉工单。",
    "source": "order_policy.md",
    "title": "订单发货规则",
    "section": "发货异常处理",
    "doc_type": "policy",
    "permission_group": "customer_service"
  }
}
```

你现在不需要记住具体 API 写法，只需要明白：

```text
vector 负责“能不能被语义搜到”
payload 负责“搜到以后知道这是什么、来自哪里、能不能给用户看”
```

这是 RAG 里非常重要的分工。

## collection 是什么

Qdrant 里有一个重要概念叫 collection。

可以先理解成：

```text
collection = 一组同类向量数据的集合
```

如果类比关系型数据库：

```text
关系型数据库：table
Qdrant：collection
```

但这个类比不是完全等价，只是帮助入门。

在一个 RAG 项目里，你可能这样设计：

```text
collection: company_knowledge_base
里面存放所有企业知识库 chunk 的向量。
```

或者更细一点：

```text
collection: customer_service_docs
collection: internal_it_docs
collection: hr_policy_docs
```

具体怎么分 collection，不是越多越好。

设计时要考虑：

```text
1. 这些数据是否使用同一个 embedding 模型。
2. 这些向量维度是否一致。
3. 这些数据是否使用同一种相似度算法。
4. 查询时是否经常需要跨这些数据一起检索。
5. 权限和业务隔离是否要求强隔离。
```

Qdrant 文档里明确强调：同一个 collection 里的向量通常要保持相同维度，并且使用同一种距离/相似度配置。

所以 collection 不是随便建的。

它是 RAG 数据组织的第一层边界。

## point 是什么

Qdrant 里另一个重要概念叫 point。

可以先理解成：

```text
point = collection 里的一条向量记录。
```

在 RAG 里，一个 point 通常对应一个 chunk。

例如：

```text
一个 Markdown 文档
-> 切成 20 个 chunk
-> 每个 chunk 生成一个 vector
-> 写入 Qdrant 变成 20 个 point
```

每个 point 至少要有：

```text
id
vector
```

通常还会带：

```text
payload
```

payload 里会放：

```text
chunk 原文
文档标题
来源路径
章节标题
权限字段
文档类型
更新时间
```

所以你可以记住这句话：

```text
RAG 不是把“整篇文档”直接作为一个 point，而是通常把“切分后的 chunk”作为 point。
```

为什么？

因为整篇文档太长，召回不精准，也不适合直接塞进模型上下文。

## vector 是什么

vector 就是 embedding 的结果。

比如：

```text
"订单超过 72 小时未发货，可以创建投诉工单。"
```

经过 embedding 模型后，得到：

```text
[0.12, 0.78, 0.21, ...]
```

真实 vector 不是 3 维，而可能是几百维、上千维甚至更多。

向量数据库保存 vector，是为了后续比较：

```text
query vector 和 chunk vector 的相似度。
```

这里有一个很重要的要求：

```text
同一个 collection 里的向量维度必须一致。
```

如果你用一个 embedding 模型生成 1536 维向量，又用另一个模型生成 1024 维向量，不能直接混在同一个普通 collection 配置里当作同一种向量搜索。

这也是为什么 embedding 模型选择不是小事。

后面第 24 节会专门讲：

```text
embedding 模型选择、维度、成本和批量处理。
```

## payload / metadata 是什么

在前面第 3 节我们讲过 metadata。

Qdrant 里常用的说法是 payload。

你可以先把它们放在一起理解：

```text
metadata / payload = 向量旁边保存的业务信息。
```

它不是用来做向量相似度计算的主角，但它对 RAG 非常关键。

比如一个 point：

```json
{
  "id": "refund-policy-003",
  "vector": [0.22, 0.31, 0.88],
  "payload": {
    "content": "用户收到商品 7 天内可以申请退货。",
    "source": "refund_policy.md",
    "doc_type": "policy",
    "permission_group": "customer_service"
  }
}
```

这里：

```text
vector 让它能被搜到。
payload 让系统知道它是什么。
```

如果没有 payload，即使向量库找到了最相似的向量，也会出现问题：

```text
1. 不知道原文是什么。
2. 不知道来自哪个文档。
3. 不知道能不能给当前用户看。
4. 不知道答案引用该写什么来源。
5. 不知道文档是否已经过期。
```

所以 RAG 不是只存 vector。

RAG 必须同时存：

```text
vector + payload
```

## search 是什么

search 就是向量检索。

在 RAG 问答中，search 大概做这件事：

```text
输入：
query vector

条件：
top_k = 5
permission_group = 当前用户有权限的组
doc_type = policy

输出：
最相似的 5 个 point
```

更完整一点：

```text
用户问题：
订单三天没发货怎么办？

query vector:
[...]

向量数据库检索：
在 company_knowledge_base collection 中，
找出和 query vector 最相似的 point，
只允许返回 permission_group 符合当前用户权限的文档，
最多返回 5 条。
```

返回结果可能长这样：

```json
[
  {
    "id": "order-policy-001",
    "score": 0.91,
    "payload": {
      "content": "订单超过 72 小时未发货，可以创建投诉工单。",
      "source": "order_policy.md"
    }
  },
  {
    "id": "logistics-policy-004",
    "score": 0.84,
    "payload": {
      "content": "物流连续 3 天无更新时，客服应先查询承运商状态。",
      "source": "logistics_policy.md"
    }
  }
]
```

然后 Python AI 服务会把这些 chunk 整理进 prompt，让模型回答。

## top_k 是什么

`top_k` 表示：

```text
返回最相似的前 k 条结果。
```

比如：

```text
top_k = 3
```

意思是：

```text
只返回最相似的 3 个 chunk。
```

`top_k` 不是越大越好。

太小会导致：

```text
召回不够，漏掉重要材料。
```

太大会导致：

```text
1. prompt 变长。
2. token 成本增加。
3. 模型看到太多噪声。
4. 回答更容易混入不相关内容。
```

所以后面做 RAG 调优时，`top_k` 是一个重要参数。

## score 是什么

score 表示向量数据库认为：

```text
这个结果和 query vector 有多接近。
```

但你必须注意：

```text
score 不是答案正确率。
```

score 高只说明：

```text
这个 chunk 和用户问题在向量空间里比较接近。
```

它不能保证：

```text
1. 这个 chunk 一定能回答问题。
2. 这个 chunk 没有过期。
3. 这个 chunk 权限一定正确。
4. 这个 chunk 的内容一定真实。
5. 模型最终回答一定正确。
```

所以 RAG 不能只看 score。

还要配合：

```text
metadata/payload filter
score_threshold
引用来源
无结果兜底
答案评测
人工复核
```

## filter 是什么

filter 是用 payload 里的字段做过滤。

比如企业知识库里有这些文档：

```text
客服政策文档
财务制度文档
内部研发文档
人事制度文档
```

不是每个用户都能看所有文档。

如果当前用户是客服，他可能只能查：

```text
permission_group = customer_service
```

如果当前用户是 HR，他可能能查：

```text
permission_group = hr
```

如果当前问题只想查政策类文档，可以加：

```text
doc_type = policy
```

这就是 filter 的价值。

没有 filter，RAG 会出现很危险的问题：

```text
1. 普通员工问问题，系统返回了管理层文档。
2. 客服问售后政策，系统混入了财务内部制度。
3. 用户问当前规则，系统返回了过期文档。
4. 多租户系统里 A 公司用户搜到了 B 公司文档。
```

所以在企业 RAG 中，payload filter 不是锦上添花，而是基本安全边界之一。

## 检索时 filter 和 vector search 谁先谁后

这个问题初学时不用钻到底层实现，但要理解工程含义。

从逻辑上看，目标是：

```text
在满足过滤条件的候选数据里，找向量最相似的结果。
```

也就是：

```text
只在“用户有权看的文档”里找相似内容。
```

不要理解成：

```text
先随便找最相似的，再把不该看的删掉就完了。
```

因为如果先搜全库，再过滤，可能出现：

```text
1. 前几名全是用户无权看的内容。
2. 过滤后没有结果。
3. 实际上用户有权看的第 20 名内容被漏掉。
```

成熟的向量数据库会提供向量搜索和 payload filter 结合的能力。

后面第 16 节会专门讲：

```text
payload filter：按文档类型、权限、来源过滤。
```

## 向量数据库不替代什么

这是本节非常重要的一段。

初学 RAG 时很容易误以为：

```text
有了向量数据库，知识库问答就完成了。
```

不是。

向量数据库只负责检索的一部分。

它不替代 LLM。

```text
向量数据库负责找材料。
LLM 负责根据材料组织自然语言回答。
```

它不替代 embedding 模型。

```text
embedding 模型负责把文本变成向量。
向量数据库负责保存和搜索这些向量。
```

它不替代业务数据库。

```text
MySQL/PostgreSQL 仍然负责用户、订单、权限、业务记录。
向量数据库负责 chunk 向量检索。
```

它不替代权限系统。

```text
权限判断不能只交给向量库。
向量库可以配合 filter，但用户身份、角色、租户、授权关系仍然要由业务系统管理。
```

它不替代文档解析。

```text
PDF、Word、Markdown、HTML 怎么解析，仍然是文档处理模块负责。
```

它不替代 chunk 策略。

```text
chunk 大小、overlap、标题保留、段落边界，仍然要由 RAG 入库流程设计。
```

它不替代答案评测。

```text
检索结果好不好、回答是否引用来源、是否拒答，仍然需要评测和测试。
```

记住这句话：

```text
向量数据库是 RAG 的检索基础设施，不是整个 RAG 系统本身。
```

## 为什么先选 Qdrant

阶段 4 先选 Qdrant，不是因为 Qdrant 永远比其他向量数据库好。

而是因为它适合作为 RAG 入门主线。

原因主要有 5 个。

### 1. 概念比较直观

Qdrant 的几个核心概念很适合教学：

```text
collection
point
vector
payload
filter
search
```

这些词和 RAG 的数据模型对应得很自然：

```text
collection -> 一个知识库或一类知识库数据
point -> 一个 chunk 的向量记录
vector -> chunk embedding
payload -> chunk 原文、来源、权限、metadata
search -> 用 query embedding 找相似 chunk
```

你先把这些概念学明白，后面再学 Milvus、pgvector、Elasticsearch vector search，理解成本都会下降。

### 2. 本地学习成本较低

学习阶段最怕一上来被环境复杂度拖住。

我们现在的目标是：

```text
先跑通 RAG 主线。
```

不是一开始就做：

```text
高可用集群
分布式部署
复杂索引调优
大规模生产压测
```

Qdrant 对本地学习比较友好，后面第 8 节会用它在本地启动服务。

这样你能把注意力放在：

```text
文档怎么入库
向量怎么保存
检索怎么返回 chunk
回答怎么引用来源
权限 filter 怎么加
```

这些 RAG 主线能力上。

### 3. payload/filter 模型适合企业知识库

企业 RAG 不是只做语义相似度。

企业 RAG 必须考虑：

```text
来源
标题
章节
文档类型
租户
部门
角色
权限组
更新时间
是否过期
```

Qdrant 的 payload 和 filter 能直接承载这些学习点。

后面我们做：

```text
按文档类型过滤
按权限过滤
按来源过滤
```

会比较自然。

### 4. 和 LangChain 集成清晰

我们阶段 3 已经学过 LangChain 基础。

LangChain 官方也有 Qdrant vector store 集成。

这意味着后面你可以同时理解两层：

```text
底层：Qdrant 自己的 collection/point/vector/payload/search
上层：LangChain VectorStore/Retriever 怎么封装 Qdrant
```

我们会先理解底层，再看封装。

这样你不会只会调一个框架方法，却不知道背后发生什么。

### 5. 适合作为 Milvus 对比前的基准

如果你直接从 Milvus 开始，也不是不行。

但初学时容易被更多部署和索引概念打断。

先用 Qdrant 跑通一套 RAG 后，再学 Milvus，你会更容易问出正确问题：

```text
Milvus 的 collection 和 Qdrant 的 collection 有什么相同和不同？
Milvus 为什么更强调 schema、field、index？
Milvus 的 scalar filter 和 Qdrant payload filter 有什么区别？
什么时候该选 Milvus？
什么时候 Qdrant 就够了？
```

这比一开始同时学两个向量库更稳。

## Milvus 不讲吗

讲。

而且阶段 4 已经把 Milvus 放进了后半段。

当前阶段安排是：

```text
第 6-30 节：先用 Qdrant 跑通 RAG 主线
第 31-36 节：再学习 Milvus，并和 Qdrant 做对比
```

这样安排的原因是：

```text
先学“RAG 该怎么工作”
再学“不同向量数据库怎么选型”
```

Milvus 的特点更偏向：

```text
1. 大规模向量检索。
2. 更明确的 schema / field / index 概念。
3. 更适合拿来讲索引、召回、性能、扩展。
4. 更适合在你已经知道 RAG 主线后做选型对比。
```

所以不是跳过 Milvus。

而是：

```text
Qdrant 先帮你学会 RAG 主流程；
Milvus 后面帮你补齐向量数据库选型和规模化理解。
```

## Qdrant 和 Milvus 先粗略对比

这一节先只做粗略对比，不进入具体 API。

| 维度 | Qdrant | Milvus |
| --- | --- | --- |
| 当前学习定位 | RAG 主线入门首选 | 后半段进阶对比 |
| 初学重点 | collection、point、vector、payload、filter | collection、schema、field、entity、index |
| 本地学习成本 | 相对更轻，适合先跑通流程 | 概念和部署理解更重，适合后学 |
| 企业 RAG 重点 | payload filter、语义检索、LangChain 接入 | 大规模检索、索引、schema、性能选型 |
| 我们什么时候学 | 第 6-30 节主线使用 | 第 31-36 节专项对比 |

不要把这张表理解成绝对优劣。

它只是说明：

```text
在你的当前学习阶段，先用 Qdrant 更适合建立 RAG 主线理解。
```

## 一个完整 RAG 检索例子

现在把前面概念串起来。

### 入库阶段

原始文档：

```text
order_policy.md
```

内容：

```text
订单超过 72 小时未发货，可以创建投诉工单。
```

切成 chunk：

```text
chunk_id = order_policy_001
content = 订单超过 72 小时未发货，可以创建投诉工单。
```

生成 embedding：

```text
vector = [0.12, 0.78, 0.21, ...]
```

写入 Qdrant：

```text
collection = company_knowledge_base
point = {
  id: order_policy_001,
  vector: [...],
  payload: {
    content: "...",
    source: "order_policy.md",
    title: "订单发货规则",
    section: "发货异常处理",
    doc_type: "policy",
    permission_group: "customer_service"
  }
}
```

### 查询阶段

用户问题：

```text
订单三天没发货怎么办？
```

生成 query embedding：

```text
query_vector = [...]
```

带过滤条件检索：

```text
collection = company_knowledge_base
query_vector = [...]
top_k = 5
filter = permission_group in 当前用户权限组
```

向量数据库返回：

```text
point 1:
  score = 0.91
  payload.content = 订单超过 72 小时未发货，可以创建投诉工单。
  payload.source = order_policy.md

point 2:
  score = 0.84
  payload.content = 物流连续 3 天无更新时，客服应先查询承运商状态。
  payload.source = logistics_policy.md
```

Python AI 服务再做：

```text
把检索到的 chunk 拼进 prompt
让模型基于这些材料回答
要求回答附带 source
```

最终回答可能是：

```text
如果订单超过 72 小时未发货，可以先查询物流状态；
若确认仍未发货，可以创建投诉工单。

来源：
1. order_policy.md
2. logistics_policy.md
```

这就是向量数据库在 RAG 里的实际作用。

## 为什么不能只靠 prompt

有些人会问：

```text
我能不能直接把企业文档塞进 prompt？
```

少量内容可以。

大量内容不行。

原因有：

```text
1. 模型上下文窗口有限。
2. 文档太多，token 成本高。
3. 每次都传全量文档很慢。
4. 用户只问一个问题，不需要所有文档。
5. 权限过滤和引用来源会变得混乱。
```

RAG 的思想不是：

```text
把所有知识一次性塞给模型。
```

而是：

```text
先检索出最相关的一小部分，再交给模型回答。
```

向量数据库就是帮我们完成“先检索出最相关的一小部分”的基础设施。

## 为什么不能只靠关键词搜索

关键词搜索也有价值，后面还会讲混合检索。

但只靠关键词搜索有局限。

比如用户问：

```text
订单三天没发货怎么办？
```

文档写的是：

```text
订单超过 72 小时未发货，可以创建投诉工单。
```

关键词上：

```text
三天
72 小时
```

不是同一个词。

但语义上很接近。

向量检索可以更容易找到这种语义相近内容。

不过，向量检索也不是万能的。

所以成熟 RAG 经常会结合：

```text
关键词检索
向量检索
metadata filter
rerank
```

这就是后面第 26 节混合检索、第 27 节 rerank 要讲的内容。

## 向量索引先有个印象就行

你现在只需要知道：

```text
向量库为了更快地找相似向量，通常会使用向量索引。
```

如果没有索引，最直观的方法是：

```text
query vector 和所有 chunk vector 一个一个比。
```

这叫暴力遍历，数据少时可以，数据大时慢。

索引的目标是：

```text
尽量更快找到足够相似的结果。
```

但索引不是免费午餐。

它通常会带来取舍：

```text
1. 查询速度。
2. 召回质量。
3. 内存占用。
4. 写入速度。
5. 构建索引成本。
```

这一节不展开索引算法。

你先记住：

```text
向量数据库不只是“存数组”，它还会围绕向量搜索做索引和性能优化。
```

Milvus 后半段会更系统地讲 index。

## 本项目后续怎么落地

本节只是第 6 节，先建立概念。

后面会按这个顺序推进：

```text
第 7 节：Qdrant 基础：collection、point、vector、payload
第 8 节：本地启动 Qdrant
第 9 节：RAG 项目结构设计
第 10-12 节：准备文档、加载文档、chunk 切分
第 13 节：生成 embedding 并写入 Qdrant
第 14-17 节：metadata、top_k、filter、score_threshold
第 18-20 节：把检索结果交给模型回答、引用来源、无结果处理
第 21-30 节：错误处理、测试、更新删除、调优、安全、性能、复盘
第 31-36 节：Milvus 学习和 Qdrant 对比
```

这条路线的核心是：

```text
先理解，再运行，再写入，再检索，再生成，再优化，再对比。
```

## 常见错误理解

### 错误 1：向量数据库就是知识库

不准确。

向量数据库只是知识库系统的一部分。

完整知识库还包括：

```text
文档管理
解析
切分
embedding
权限
检索
生成
引用
评测
运维
```

### 错误 2：只要相似度高，答案就一定对

不对。

相似度高只代表检索候选更相关。

答案是否正确还取决于：

```text
chunk 是否完整
chunk 是否过期
模型是否严格基于材料回答
是否有引用来源
是否设置了无结果拒答
```

### 错误 3：payload 不重要

非常错误。

企业 RAG 里 payload 直接关系到：

```text
来源引用
权限过滤
文档类型过滤
版本管理
问题排查
```

只存 vector，不存 payload，基本做不出可靠知识库。

### 错误 4：向量数据库可以替代业务数据库

不对。

向量数据库适合语义检索。

业务数据库仍然负责结构化业务数据和事务。

### 错误 5：一开始就必须选最强向量数据库

不对。

学习阶段最重要的是把主线跑通。

你要先能解释：

```text
为什么要存向量
怎么检索
怎么过滤
怎么把结果交给模型
怎么引用来源
怎么评估质量
```

再讨论更深入的选型。

## 本节不写代码的原因

这节故意不写代码。

原因是：

```text
向量数据库这节的关键不是 API，而是职责边界。
```

如果现在立刻启动 Qdrant、创建 collection、写 point，你可能能照着运行，但不一定理解：

```text
为什么要 collection
为什么 point 通常对应 chunk
为什么 payload 很重要
为什么 filter 是企业 RAG 的安全边界
为什么 Qdrant 和 Milvus 要分阶段学
```

所以这一节先把“为什么”和“是什么”打牢。

下一节再进入 Qdrant 的核心概念。

## 本节练习

### 练习 1：判断哪些数据适合放进向量数据库

下面哪些适合放进向量数据库？哪些更适合放进业务数据库？

```text
1. 用户账号和密码哈希。
2. 订单付款状态。
3. 知识库 chunk 的 embedding。
4. chunk 原文、来源、标题、权限组。
5. 某个订单的物流单号。
6. 用来检索“退款规则”的 query vector。
```

参考答案：

```text
1. 用户账号和密码哈希：业务数据库。
   这是典型结构化用户数据，而且涉及安全和权限。

2. 订单付款状态：业务数据库。
   这是订单业务状态，需要事务和强一致性。

3. 知识库 chunk 的 embedding：向量数据库。
   它是向量检索的核心数据。

4. chunk 原文、来源、标题、权限组：通常可以作为 payload 放进向量数据库，同时原始文档记录也可以在业务数据库保存。
   在 RAG 检索时，payload 用于返回内容、引用来源和过滤。

5. 某个订单的物流单号：业务数据库。
   这是结构化业务字段，应该由订单/物流系统管理。

6. 用来检索“退款规则”的 query vector：通常不长期保存，作为一次查询输入传给向量数据库。
   如果为了日志、评测或调试，也可以另行记录，但它不是知识库主数据。
```

### 练习 2：设计一个最小 payload

假设有一个 chunk：

```text
员工请假需要提前一天提交申请，病假需要补充医院证明。
```

请设计一个最小但有用的 payload。

参考答案：

```json
{
  "content": "员工请假需要提前一天提交申请，病假需要补充医院证明。",
  "source": "hr_leave_policy.md",
  "title": "请假制度",
  "section": "请假申请规则",
  "doc_type": "policy",
  "permission_group": "employee"
}
```

解释：

```text
content：模型回答需要原文。
source：回答引用来源需要它。
title：方便展示和排查。
section：方便定位文档章节。
doc_type：后续可以按文档类型过滤。
permission_group：后续可以做权限过滤。
```

### 练习 3：解释 top_k 太大和太小的问题

问题：

```text
RAG 检索时 top_k 设置成 1 和设置成 50，各有什么风险？
```

参考答案：

```text
top_k = 1 的风险：
只返回最相似的 1 条，可能漏掉必要上下文。
如果第 1 条虽然相似但不完整，模型回答会缺信息。

top_k = 50 的风险：
返回内容太多，prompt 变长，token 成本增加。
大量不相关 chunk 会干扰模型，答案可能变散或混入错误信息。

所以 top_k 需要根据知识库质量、chunk 大小、问题类型和评测结果调优。
```

### 练习 4：说明为什么企业 RAG 必须有 filter

问题：

```text
为什么企业知识库 RAG 不能只做向量相似度搜索，还必须做 payload filter？
```

参考答案：

```text
因为企业文档通常有权限、部门、租户、文档类型、版本和有效期。
如果只按相似度搜索，系统可能返回当前用户无权查看的文档，也可能把不相关业务线或过期文档交给模型。
payload filter 可以把检索范围限制在符合业务条件的数据里，例如只查当前用户权限组、只查 policy 文档、只查未过期文档。
所以 filter 是企业 RAG 的安全和质量基础之一。
```

## 自测问题

### 自测 1：向量数据库最核心的作用是什么？

参考答案：

```text
保存向量，并根据 query vector 高效检索相似向量，同时结合 payload 返回原文、来源、权限等业务信息。
```

### 自测 2：Qdrant 里的 point 可以怎么理解？

参考答案：

```text
point 是 collection 里的一条向量记录。在 RAG 里通常对应一个 chunk，包含 id、vector 和 payload。
```

### 自测 3：payload 为什么不能省？

参考答案：

```text
因为 vector 只能用于相似度检索，不能告诉系统原文、来源、标题、权限、文档类型和是否过期。
没有 payload，就无法可靠地展示引用、做权限过滤和排查检索结果。
```

### 自测 4：向量数据库能不能替代 LLM？

参考答案：

```text
不能。向量数据库负责找相关材料，LLM 负责基于材料生成自然语言回答。
```

### 自测 5：为什么现在先学 Qdrant，不直接进入 Milvus？

参考答案：

```text
因为当前阶段的重点是跑通 RAG 主线。Qdrant 的 collection、point、vector、payload、filter 概念直观，本地学习成本较低，适合先建立完整流程。
Milvus 也会学，但放在后半段作为规模化、schema、index 和选型对比学习。
```

### 自测 6：score 高代表答案一定正确吗？

参考答案：

```text
不代表。score 高只说明检索结果和 query vector 在向量空间中更接近。
答案是否正确还取决于 chunk 是否完整、是否过期、权限是否正确、模型是否严格基于材料回答，以及是否有引用和评测。
```

### 自测 7：collection 设计时要考虑什么？

参考答案：

```text
要考虑数据是否使用同一个 embedding 模型、向量维度是否一致、相似度算法是否一致、查询时是否需要一起检索，以及业务隔离和权限边界。
```

## 本节复盘

你现在应该能用自己的话讲清楚：

```text
1. RAG 为什么不能只靠 prompt 或普通文件。
2. 向量数据库保存的是 vector + payload，不是只保存文本。
3. Qdrant 的 collection 可以理解成一组同类向量数据。
4. Qdrant 的 point 通常对应一个 chunk。
5. top_k 控制返回数量，score 表示相似度，不等于答案正确率。
6. payload filter 是企业 RAG 的关键安全边界。
7. Qdrant 适合先学主线，Milvus 适合后面做进阶对比。
```

如果这些能讲清楚，下一节学习 Qdrant 的 collection、point、vector、payload 时，就不会只是背 API，而是知道每个概念为什么存在。

## 参考资料

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Qdrant Collections](https://qdrant.tech/documentation/manage-data/collections/)
- [Qdrant Points](https://qdrant.tech/documentation/manage-data/points/)
- [Qdrant Local Quickstart](https://qdrant.tech/documentation/quickstart/)
- [LangChain Qdrant integration](https://docs.langchain.com/oss/python/integrations/vectorstores/qdrant)
- [Milvus Documentation](https://milvus.io/docs)
