# 阶段 4 第 7 节：Qdrant 基础：collection、point、vector、payload

> 本节结论：Qdrant 的核心数据模型可以先记成一句话：一个 `collection` 里保存很多 `point`，每个 `point` 至少有 `id` 和 `vector`，通常还会有 `payload`。在 RAG 里，一个文档会被切成多个 chunk，每个 chunk 通常会变成 Qdrant 里的一个 point；`vector` 用于语义相似度检索，`payload` 保存 chunk 原文、来源、标题、权限等业务信息。

## 生成笔记前的教学复核

这一节仍然不启动 Qdrant，不调用真实 Qdrant 服务，也不写项目代码。

这一节必须讲清：

```text
1. Qdrant 的 collection 是什么。
2. Qdrant 的 point 是什么。
3. point id 有什么作用。
4. vector 在 point 里负责什么。
5. payload 在 point 里负责什么。
6. 一个 chunk 怎么映射成一个 point。
7. collection 创建时为什么要关心向量维度和距离算法。
8. payload 和 metadata 的关系。
9. 命名规范、id 设计、payload 字段设计的初步原则。
10. 这些概念后面怎么进入代码和项目结构。
```

## 本节一句话定位

第 6 节讲：

```text
为什么 RAG 需要向量数据库，以及为什么我们先选 Qdrant。
```

第 7 节讲：

```text
Qdrant 里面到底怎么组织一条 chunk 向量数据。
```

如果第 6 节解决的是：

```text
为什么要有向量库？
```

那第 7 节解决的是：

```text
向量库里的数据长什么样？
```

## 先用普通数据库类比一下

你之前学 Java 后端时，应该更熟悉这种结构：

```text
database
  table
    row
      column
```

比如订单表：

```text
table: orders

row:
  order_id = A1001
  status = paid
  amount = 199.00
```

关系型数据库里，我们经常说：

```text
一张表里有很多行。
一行里有很多字段。
```

Qdrant 里可以先粗略类比成：

```text
collection
  point
    id
    vector
    payload
```

也就是：

```text
一个 collection 里有很多 point。
一个 point 里有 id、vector、payload。
```

注意，这只是帮助入门的类比。

Qdrant 不是关系型数据库，它的核心不是表关联、事务和 SQL，而是向量相似度搜索。

## Qdrant 数据模型总图

可以先看成下面这样：

```text
Qdrant
└── collection: company_knowledge_base
    ├── point: chunk-001
    │   ├── id: chunk-001
    │   ├── vector: [0.12, 0.78, 0.21, ...]
    │   └── payload:
    │       ├── content: 订单超过 72 小时未发货，可以创建投诉工单。
    │       ├── source: order_policy.md
    │       ├── title: 订单发货规则
    │       ├── doc_type: policy
    │       └── permission_group: customer_service
    │
    ├── point: chunk-002
    │   ├── id: chunk-002
    │   ├── vector: [0.33, 0.10, 0.65, ...]
    │   └── payload:
    │       ├── content: 用户收到商品 7 天内可以申请退货。
    │       ├── source: refund_policy.md
    │       └── ...
    │
    └── point: chunk-003
        ├── id: chunk-003
        ├── vector: [...]
        └── payload: {...}
```

这张图是本节最重要的图。

如果你能看懂它，第 7 节就抓住了主线。

## 基础知识铺垫：Qdrant 为什么要这样设计

RAG 检索需要同时解决两个问题：

```text
1. 语义上像不像。
2. 业务上能不能用。
```

`vector` 解决第一个问题：

```text
用户问题和哪个 chunk 语义最接近？
```

`payload` 解决第二个问题：

```text
这个 chunk 的原文是什么？
来自哪个文档？
标题是什么？
当前用户有没有权限看？
文档是否过期？
后面回答时引用哪个来源？
```

所以一个 RAG chunk 不能只存成：

```text
[0.12, 0.78, 0.21, ...]
```

因为这只是一串数字。

它必须和业务信息绑定在一起：

```text
id + vector + payload
```

这就是 Qdrant 的 point 模型非常适合 RAG 入门的原因。

## 本节主题系统讲解

下面正式逐个拆：

```text
collection
point
id
vector
payload
distance
```

## collection 是什么

`collection` 是 Qdrant 里存放 point 的容器。

可以先理解成：

```text
collection = 一组向量记录的集合。
```

在 RAG 里，collection 通常对应：

```text
一个知识库
一类文档
一个业务域
一个租户的数据空间
```

比如：

```text
company_knowledge_base
customer_service_docs
hr_policy_docs
it_support_docs
```

最简单的企业知识库项目，可以先只有一个 collection：

```text
company_knowledge_base
```

里面存所有知识库 chunk。

## collection 和 table 像不像

初学时可以类比：

```text
Qdrant collection ~= 数据库 table
```

但不能完全等同。

关系型数据库的 table 关心：

```text
字段类型
主键
外键
索引
约束
事务
SQL 查询
```

Qdrant 的 collection 更关心：

```text
向量维度
距离算法
向量索引
point 存储
payload filter
相似度搜索
```

所以 collection 是向量检索意义上的容器，不是传统 SQL 表。

## collection 创建时最重要的配置

创建 Qdrant collection 时，初学阶段最该关注两个东西：

```text
1. vector size
2. distance
```

### vector size

`vector size` 表示向量维度。

比如：

```text
3 维向量：[0.1, 0.2, 0.3]
4 维向量：[0.1, 0.2, 0.3, 0.4]
1536 维向量：[...1536 个数字...]
```

真实 embedding 模型会固定输出某个维度。

例如某个 embedding 模型输出 1024 维，那么同一个 collection 里就应该按 1024 维来配置。

不能一会儿写 1024 维，一会儿写 1536 维。

因为不同维度的向量没法直接做同一种相似度比较。

可以这样理解：

```text
二维坐标点：[x, y]
三维坐标点：[x, y, z]
```

二维点和三维点不是同一个空间里的点，不能直接比较距离。

### distance

`distance` 表示 Qdrant 用什么方式比较向量相似度。

常见的有：

```text
Cosine
Dot
Euclid
Manhattan
```

第 5 节我们已经讲过：

```text
cosine 更关注方向相似。
dot product 会受到方向和长度共同影响。
euclid 更像空间距离。
```

在 RAG 入门里，很多文本 embedding 场景会使用 cosine。

但最终用什么，要看：

```text
1. embedding 模型说明。
2. 向量是否归一化。
3. 向量库配置。
4. 检索评测结果。
```

这节先记住：

```text
collection 不是随便建的，它要和 embedding 模型输出匹配。
```

## 一个项目应该建几个 collection

这是初学者很容易纠结的问题。

不要一开始就追求复杂设计。

早期 RAG 项目可以先这样：

```text
一个 collection：company_knowledge_base
```

然后用 payload 区分：

```text
doc_type
source
department
permission_group
tenant_id
```

比如：

```json
{
  "doc_type": "policy",
  "department": "customer_service",
  "permission_group": "customer_service"
}
```

什么时候考虑拆多个 collection？

可以看这些条件：

```text
1. 不同数据使用不同 embedding 模型。
2. 不同数据向量维度不一样。
3. 不同业务域完全不需要一起检索。
4. 不同租户需要更强隔离。
5. 数据规模和性能策略明显不同。
```

比如：

```text
客服知识库：1024 维中文文本 embedding
图片知识库：768 维图片 embedding
```

这两类数据就不适合简单塞进同一个普通文本 collection 里。

## point 是什么

Qdrant 官方文档把 point 视为 Qdrant 操作的核心实体。

你可以先记住：

```text
point = Qdrant collection 里的一条记录。
```

在 RAG 里，point 通常对应：

```text
一个 chunk。
```

不是一整篇文档。

例如：

```text
order_policy.md
```

被切成 3 个 chunk：

```text
chunk 1：发货规则
chunk 2：超时处理
chunk 3：投诉流程
```

那么写入 Qdrant 时，通常是：

```text
point 1 -> chunk 1
point 2 -> chunk 2
point 3 -> chunk 3
```

这就是：

```text
一个 chunk 一个 point。
```

## 为什么不是一篇文档一个 point

因为 RAG 要找的是能回答用户问题的局部材料。

假设有一篇很长的客服政策文档：

```text
第一章：账号问题
第二章：订单问题
第三章：退款问题
第四章：发票问题
第五章：投诉问题
```

用户只问：

```text
订单三天没发货怎么办？
```

如果整篇文档是一个 point，那么检索结果太粗。

模型拿到的是一大段混合材料：

```text
账号、订单、退款、发票、投诉全都在里面。
```

这会导致：

```text
1. prompt 变长。
2. 噪声变多。
3. 引用来源不够精确。
4. 模型更容易答偏。
```

所以 RAG 通常把文档切成 chunk，再让 chunk 成为 point。

这就是第 3 节 chunk 概念和本节 point 概念的连接。

## point 的最小结构

一个最小 point 可以这样理解：

```json
{
  "id": "chunk-001",
  "vector": [0.12, 0.78, 0.21],
  "payload": {
    "content": "订单超过 72 小时未发货，可以创建投诉工单。"
  }
}
```

其中：

```text
id：这条记录是谁。
vector：怎么按语义找到它。
payload：找到以后知道它是什么。
```

如果没有 `id`：

```text
不好更新、删除、去重、排查。
```

如果没有 `vector`：

```text
无法做向量相似度检索。
```

如果没有 `payload`：

```text
即使搜到了，也不知道原文、来源、权限和引用信息。
```

## id 是什么

`id` 是 point 的唯一标识。

它的作用类似：

```text
这条记录的身份证。
```

Qdrant 支持数字 id，也支持 UUID 字符串。

在 RAG 项目里，id 用来做：

```text
1. 更新某个 chunk。
2. 删除某个 chunk。
3. 避免重复写入。
4. 追踪检索结果来自哪个 chunk。
5. 排查线上问题。
```

比如一次检索返回：

```text
point id = order_policy_001_chunk_003
```

你就能知道：

```text
这是 order_policy 文档里的第 3 个 chunk。
```

## RAG 里的 id 怎么设计

早期可以先用清晰可读的 id：

```text
order_policy_001_chunk_001
order_policy_001_chunk_002
refund_policy_002_chunk_001
```

更工程化一点，可以用：

```text
doc_id + chunk_index
```

比如：

```text
doc_20260714_0001_chunk_0003
```

也可以用 UUID：

```text
550e8400-e29b-41d4-a716-446655440000
```

可读 id 的优点：

```text
方便学习和调试。
```

UUID 的优点：

```text
更容易全局唯一，适合系统自动生成。
```

我们当前学习阶段可以先用：

```text
doc_id + chunk_index
```

这样你能看懂数据从哪里来。

## id 设计要避免什么

不要用随手变化的 id。

比如每次入库都生成完全不同的随机 id，而不保存映射关系。

这样会导致：

```text
1. 同一篇文档重新入库后旧 point 删不掉。
2. 同一个 chunk 重复出现多次。
3. 更新文档时无法定位原来的 chunk。
4. 检索排查时不知道结果对应哪个文档版本。
```

RAG 不是一次性 demo。

企业知识库一定会遇到：

```text
新增文档
修改文档
删除文档
重新入库
版本更新
```

所以 point id 设计会影响后续维护。

## vector 是什么

`vector` 是 embedding 的结果。

例如 chunk 原文：

```text
订单超过 72 小时未发货，可以创建投诉工单。
```

经过 embedding 模型后，得到：

```text
[0.12, 0.78, 0.21, ...]
```

这个数组就是 vector。

Qdrant 用它来做：

```text
向量相似度检索。
```

当用户问：

```text
订单三天没发货怎么办？
```

系统也生成 query vector：

```text
[0.11, 0.80, 0.19, ...]
```

Qdrant 比较：

```text
query vector 和每个 point.vector 的相似度。
```

然后返回最接近的 point。

## dense vector 是什么

Qdrant 支持多种向量形态。

当前阶段先重点理解 dense vector。

dense vector 可以理解成：

```text
固定长度的浮点数列表。
```

比如：

```text
[0.12, -0.08, 0.33, 0.91]
```

它的特点是：

```text
1. 长度固定。
2. 每个位置都有一个数字。
3. 大多数文本 embedding 模型输出的就是 dense vector。
```

阶段 4 前半段，我们默认用 dense vector 来理解 RAG。

后面讲混合检索时，再补 sparse vector。

## sparse vector 先有个印象

sparse vector 可以先理解成：

```text
大部分位置是 0，只记录少量非 0 项的向量。
```

它常用于：

```text
关键词匹配
稀疏检索
混合检索
```

你现在不用深入。

只要知道：

```text
dense vector 更偏语义相似。
sparse vector 更容易表达词项匹配。
```

后面第 26 节讲混合检索时会再回来。

## named vectors 先有个印象

Qdrant 一个 point 可以有一个或多个 vector。

多个 vector 时，可以用名字区分。

比如：

```text
text_vector
title_vector
summary_vector
```

这叫 named vectors。

当前阶段先不使用多向量。

我们先用最简单的单向量模型：

```text
point.vector = chunk 的 embedding
```

原因是：

```text
先把 RAG 主线跑通，比一开始做多向量复杂设计更重要。
```

## payload 是什么

`payload` 是 point 上附带的业务信息。

Qdrant 官方说法里，payload 是和 vector 一起保存的额外信息，可以用 JSON 表示。

在 RAG 里，你可以把 payload 理解成：

```text
chunk 的 metadata + chunk 原文。
```

比如：

```json
{
  "content": "订单超过 72 小时未发货，可以创建投诉工单。",
  "source": "order_policy.md",
  "title": "订单发货规则",
  "section": "发货异常处理",
  "doc_type": "policy",
  "permission_group": "customer_service",
  "chunk_index": 3
}
```

这里最重要的是：

```text
payload 不参与 embedding 生成。
payload 也不是 vector。
payload 是辅助检索、过滤、展示、引用和排查的业务字段。
```

## payload 和 metadata 是什么关系

前面第 3 节我们讲过 metadata。

在 RAG 语境里：

```text
metadata = 文档或 chunk 的描述信息。
```

在 Qdrant 语境里：

```text
payload = point 上保存的附加 JSON 信息。
```

所以在本项目里可以先这样理解：

```text
metadata 写进 Qdrant 后，就成为 payload 的一部分。
```

例如本地 RAG 数据结构里可能叫：

```text
metadata.source
metadata.title
metadata.doc_type
```

写入 Qdrant 时可能变成：

```text
payload.source
payload.title
payload.doc_type
```

名字不同，职责相通。

## payload 里应该放什么

一个企业知识库 RAG 的 payload，可以先从这些字段开始：

```text
content
source
title
section
doc_id
chunk_id
chunk_index
doc_type
permission_group
created_at
updated_at
```

每个字段的作用：

| 字段 | 含义 | 作用 |
| --- | --- | --- |
| content | chunk 原文 | 交给模型生成答案 |
| source | 来源路径或来源名 | 回答引用、排查来源 |
| title | 文档标题 | 展示和引用更友好 |
| section | 文档章节 | 精确定位内容 |
| doc_id | 文档唯一标识 | 文档级更新、删除、追踪 |
| chunk_id | chunk 唯一标识 | point id 映射、排查 |
| chunk_index | chunk 顺序 | 恢复上下文、排序 |
| doc_type | 文档类型 | 按政策、FAQ、手册过滤 |
| permission_group | 权限组 | 权限过滤 |
| created_at / updated_at | 时间 | 判断版本和过期情况 |

注意：

```text
payload 不是越多越好。
```

应该放：

```text
检索、过滤、展示、引用、排查真正需要的字段。
```

## payload 里不建议放什么

不建议放：

```text
1. 密码。
2. API key。
3. 用户隐私明文。
4. 不需要被检索结果返回的敏感数据。
5. 超大原始文件内容。
6. 和 chunk 无关的大量业务对象。
```

尤其是企业 RAG，要始终记住：

```text
payload 可能会随着检索结果进入 AI 服务，再进入 prompt。
```

所以 payload 字段设计要谨慎。

后面第 28 节会专门讲 RAG 安全：

```text
文档权限、Prompt Injection、敏感信息。
```

## point、chunk、document 的关系

这是本节最关键的映射。

可以看成：

```text
document
  -> split
      -> chunk
          -> embedding
              -> Qdrant point
```

例如：

```text
文档：order_policy.md
```

切分后：

```text
chunk 1：订单创建后多久发货
chunk 2：订单超过 72 小时未发货怎么办
chunk 3：投诉工单创建规则
```

写入 Qdrant：

```text
point 1:
  id = order_policy_chunk_001
  vector = chunk 1 embedding
  payload.content = chunk 1 原文

point 2:
  id = order_policy_chunk_002
  vector = chunk 2 embedding
  payload.content = chunk 2 原文

point 3:
  id = order_policy_chunk_003
  vector = chunk 3 embedding
  payload.content = chunk 3 原文
```

所以你要形成这个直觉：

```text
RAG 检索时，向量数据库返回的不是“整篇知识库”，而是若干个相关 chunk point。
```

## 一个完整的 chunk 到 point 映射例子

原始文档：

```text
文件名：order_policy.md
标题：订单发货规则
```

其中一个 chunk：

```text
订单超过 72 小时未发货，可以创建投诉工单。客服需要先确认仓库状态，再联系承运商。
```

这个 chunk 在我们自己的 RAG 程序里可以表示为：

```json
{
  "chunk_id": "order_policy_001_chunk_003",
  "content": "订单超过 72 小时未发货，可以创建投诉工单。客服需要先确认仓库状态，再联系承运商。",
  "metadata": {
    "doc_id": "order_policy_001",
    "source": "order_policy.md",
    "title": "订单发货规则",
    "section": "发货异常处理",
    "doc_type": "policy",
    "permission_group": "customer_service",
    "chunk_index": 3
  }
}
```

经过 embedding 后：

```json
{
  "chunk_id": "order_policy_001_chunk_003",
  "vector": [0.12, 0.78, 0.21]
}
```

写入 Qdrant 时，可以变成：

```json
{
  "id": "order_policy_001_chunk_003",
  "vector": [0.12, 0.78, 0.21],
  "payload": {
    "content": "订单超过 72 小时未发货，可以创建投诉工单。客服需要先确认仓库状态，再联系承运商。",
    "doc_id": "order_policy_001",
    "chunk_id": "order_policy_001_chunk_003",
    "source": "order_policy.md",
    "title": "订单发货规则",
    "section": "发货异常处理",
    "doc_type": "policy",
    "permission_group": "customer_service",
    "chunk_index": 3
  }
}
```

这就是：

```text
chunk -> point
metadata -> payload
embedding -> vector
chunk_id -> point id
```

## 检索时 Qdrant 返回什么

当用户问：

```text
订单三天没发货怎么办？
```

系统生成 query vector：

```text
[0.11, 0.80, 0.19]
```

然后查 Qdrant：

```text
在 company_knowledge_base collection 里，
找和 query vector 最相似的 point，
最多返回 5 个，
并且只返回当前用户有权限看的 point。
```

Qdrant 可能返回：

```json
[
  {
    "id": "order_policy_001_chunk_003",
    "score": 0.91,
    "payload": {
      "content": "订单超过 72 小时未发货，可以创建投诉工单。客服需要先确认仓库状态，再联系承运商。",
      "source": "order_policy.md",
      "title": "订单发货规则"
    }
  }
]
```

Python AI 服务拿到结果后，重点使用：

```text
payload.content -> 给模型作为参考材料
payload.source -> 用于回答引用来源
score -> 用于判断相关性强弱
id -> 用于日志和排查
```

## score 不属于 point 原始数据

这里要注意一个细节。

point 原始保存的是：

```text
id
vector
payload
```

`score` 是查询时计算出来的结果。

也就是说：

```text
point 存在库里时，不固定带某个 score。
```

同一个 point 面对不同 query vector，score 不一样。

比如：

```text
用户问题 A：订单三天没发货怎么办？
point score = 0.91

用户问题 B：怎么修改登录密码？
point score = 0.12
```

因为 score 表示：

```text
当前 query vector 和这个 point.vector 的相似程度。
```

不是 point 自己的固定属性。

## vector 负责召回，payload 负责解释

这句话很重要：

```text
vector 负责召回，payload 负责解释。
```

召回是什么意思？

```text
从大量候选内容里，把可能相关的内容找出来。
```

vector 做的是：

```text
这个 chunk 和用户问题语义像不像？
```

payload 做的是：

```text
这个 chunk 是什么？
来自哪里？
能不能给用户看？
怎么展示？
怎么引用？
```

如果只看 vector：

```text
你只能知道它“像”。
```

如果加上 payload：

```text
你才知道它“是什么”。
```

## filter 和 payload 的关系

第 16 节会详细讲 payload filter。

这节先建立直觉：

```text
filter 是基于 payload 字段做条件过滤。
```

例如：

```text
只查客服有权限看的文档：
permission_group = customer_service
```

只查政策文档：

```text
doc_type = policy
```

只查某个来源：

```text
source = order_policy.md
```

所以如果你后面希望这样过滤：

```text
按权限过滤
按文档类型过滤
按来源过滤
按租户过滤
```

那这些字段就应该在写入 point 时放进 payload。

字段设计是提前做的，不是查询时凭空出现的。

## payload 字段类型为什么重要

Qdrant payload 是 JSON 形式。

常见字段类型包括：

```text
string
number
boolean
array
object
```

字段类型会影响后续过滤。

比如：

```json
{
  "doc_type": "policy",
  "chunk_index": 3,
  "enabled": true,
  "permission_groups": ["customer_service", "manager"]
}
```

这里：

```text
doc_type 是字符串。
chunk_index 是数字。
enabled 是布尔值。
permission_groups 是字符串数组。
```

如果你把数字乱存成字符串：

```json
{
  "chunk_index": "3"
}
```

后面做范围过滤或排序时可能会不方便。

所以 payload 也要有设计意识。

## content 要不要放在 payload 里

学习阶段，我们会把 chunk 原文放进 payload：

```json
{
  "content": "订单超过 72 小时未发货，可以创建投诉工单。"
}
```

原因是：

```text
检索出来以后，马上就能拿到原文给模型。
```

但生产系统里也可能有别的设计：

```text
1. payload 里放完整 chunk content。
2. payload 里只放 chunk_id，原文去业务数据库或对象存储查。
3. payload 里放摘要和引用信息，完整内容按需加载。
```

当前阶段先采用第一种：

```text
payload 保存 content。
```

因为它最直观，最适合学习完整 RAG 流程。

后面做性能、安全和大文档优化时，再讨论更复杂设计。

## collection 命名建议

命名要能表达业务含义。

推荐：

```text
company_knowledge_base
customer_service_docs
hr_policy_docs
rag_demo_docs
```

不推荐：

```text
test
data
aaa
collection1
my_vectors
```

原因是：

```text
一旦项目里有多个 collection，模糊名字会让你不知道哪个存什么。
```

学习阶段我们可以计划使用：

```text
company_knowledge_base
```

作为阶段 4 主线 collection 名。

## point id 命名建议

推荐：

```text
{doc_id}_chunk_{chunk_index}
```

例如：

```text
order_policy_001_chunk_003
```

优点：

```text
1. 一眼能看出来自哪个文档。
2. 一眼能看出是第几个 chunk。
3. 排查日志时更方便。
4. 后续删除某个文档的所有 chunk 更容易设计。
```

如果以后做生产系统，可以改成：

```text
UUID
```

或者：

```text
稳定 hash
```

例如根据：

```text
doc_id + chunk_index + chunk_content_hash
```

生成稳定 id。

但这些先不展开。

## payload 字段命名建议

字段名要稳定、统一、可读。

推荐统一使用：

```text
snake_case
```

例如：

```text
doc_id
chunk_id
chunk_index
doc_type
permission_group
created_at
updated_at
```

不要混着写：

```text
docId
doc_id
DocID
documentId
```

因为后续 filter 写条件时，如果字段名不统一，会非常容易出错。

## 本节不写真实代码的原因

本节是 Qdrant 概念落地前的最后一节纯概念课。

如果现在直接写代码，你可能会照着运行：

```text
create_collection()
upsert()
query_points()
```

但不一定真正知道：

```text
collection 为什么要配置 vector size
point 为什么通常对应 chunk
payload 为什么不是随便放
id 为什么要稳定
score 为什么不是 point 固定字段
filter 为什么依赖 payload 设计
```

所以下一节再启动 Qdrant。

这一节先把数据模型学透。

## 和后续课程的关系

这节内容会直接影响后面很多节：

```text
第 8 节：本地启动 Qdrant
  会看到真实 Qdrant 服务。

第 13 节：生成 embedding 并写入 Qdrant
  会真正创建 collection 和 upsert point。

第 14 节：metadata 设计
  会进一步设计 payload 字段。

第 15 节：基础 top_k 检索
  会用 query vector 查 point。

第 16 节：payload filter
  会用 payload 字段做权限和类型过滤。

第 23 节：文档更新、删除、重新入库
  会依赖稳定 point id 和 doc_id。

第 31-36 节：Milvus 对比
  会把 Qdrant point/payload 和 Milvus entity/field/schema 对照理解。
```

所以这节不是孤立概念。

它是后面 RAG 入库和检索代码的地基。

## 常见错误理解

### 错误 1：collection 越多越专业

不对。

collection 太多会让查询、管理、权限和同步更复杂。

早期项目先用一个 collection，加 payload 字段区分业务属性，往往更容易学清楚。

只有当 embedding 模型、向量维度、业务隔离或检索需求明显不同时，再考虑拆 collection。

### 错误 2：point 就是一篇文档

在 RAG 里通常不是。

point 更常对应 chunk。

一篇文档会被切成多个 chunk，每个 chunk 一个 point。

### 错误 3：payload 只是备注，可有可无

不对。

payload 决定了：

```text
检索结果能不能展示
回答能不能引用来源
权限能不能过滤
文档能不能更新排查
```

没有 payload，RAG 很难做成企业知识库。

### 错误 4：id 随便生成就行

学习 demo 可以简单，但长期项目不能随便。

id 如果不稳定，后续更新、删除、去重会很麻烦。

### 错误 5：score 是 point 自带的字段

不是。

score 是每次 query 时根据 query vector 和 point.vector 计算出来的。

同一个 point 面对不同 query，会有不同 score。

### 错误 6：payload filter 能弥补所有权限问题

不对。

payload filter 是权限过滤的一部分，但用户身份、角色、租户、授权关系仍然要由业务系统负责。

向量库不能单独替代完整权限系统。

## 本节练习

### 练习 1：判断概念对应关系

请判断下面关系是否合理：

```text
1. 一篇文档 -> 一个 collection。
2. 一个 chunk -> 一个 point。
3. chunk embedding -> point.vector。
4. chunk metadata -> point.payload。
5. point.score -> 写入 point 时固定保存。
```

参考答案：

```text
1. 不一定合理。
   一篇文档通常不需要单独建一个 collection。
   一个 collection 更常对应一个知识库、一类文档或一个业务域。

2. 合理。
   RAG 里通常一个 chunk 对应一个 point。

3. 合理。
   chunk embedding 就是用于检索的 vector。

4. 合理。
   metadata 写进 Qdrant 后通常体现为 payload。

5. 不合理。
   score 是查询时计算出来的，不是 point 写入时固定保存的字段。
```

### 练习 2：给 chunk 设计 point

给定 chunk：

```text
员工请假需要提前一天提交申请，病假需要补充医院证明。
```

文档信息：

```text
doc_id = hr_leave_policy_001
source = hr_leave_policy.md
title = 请假制度
section = 请假申请规则
doc_type = policy
permission_group = employee
chunk_index = 2
```

请设计一个 Qdrant point。

参考答案：

```json
{
  "id": "hr_leave_policy_001_chunk_002",
  "vector": [0.10, 0.35, 0.87],
  "payload": {
    "content": "员工请假需要提前一天提交申请，病假需要补充医院证明。",
    "doc_id": "hr_leave_policy_001",
    "chunk_id": "hr_leave_policy_001_chunk_002",
    "source": "hr_leave_policy.md",
    "title": "请假制度",
    "section": "请假申请规则",
    "doc_type": "policy",
    "permission_group": "employee",
    "chunk_index": 2
  }
}
```

说明：

```text
vector 这里用 3 维假数据，只是为了理解结构。
真实 embedding 维度会由 embedding 模型决定。
```

### 练习 3：判断哪些字段适合放 payload

下面哪些适合放进 payload？

```text
1. chunk 原文 content。
2. 文档来源 source。
3. 用户密码 password。
4. 权限组 permission_group。
5. 文档类型 doc_type。
6. API key。
7. chunk 顺序 chunk_index。
```

参考答案：

```text
1. 适合。
   学习阶段把 chunk 原文放 payload，检索后可以直接给模型。

2. 适合。
   用于引用来源和排查。

3. 不适合。
   密码不能放进向量库 payload。

4. 适合。
   用于权限过滤。

5. 适合。
   用于按文档类型过滤。

6. 不适合。
   API key 是敏感信息，不能放进 payload。

7. 适合。
   用于恢复 chunk 顺序和排查。
```

### 练习 4：解释 collection 为什么要匹配 embedding 维度

问题：

```text
为什么一个 collection 不能随便混用不同维度的 embedding？
```

参考答案：

```text
因为向量相似度比较要求向量处在同一个向量空间里。
如果一个向量是 1024 维，另一个向量是 1536 维，它们不能直接按同一种距离算法比较。
collection 创建时要配置向量维度，这个维度应该和写入该 collection 的 embedding 模型输出一致。
```

### 练习 5：解释为什么 id 要稳定

问题：

```text
为什么 RAG 里的 point id 最好稳定，而不是每次重新入库都随便生成新 id？
```

参考答案：

```text
因为企业知识库会发生文档更新、删除和重新入库。
如果 id 不稳定，同一个 chunk 每次都会变成新 point，旧 point 可能删不掉，导致重复数据、过期数据和检索混乱。
稳定 id 有助于更新、删除、去重和问题排查。
```

## 自测问题

### 自测 1：Qdrant 的 collection 是什么？

参考答案：

```text
collection 是 Qdrant 中保存一组 point 的容器。在 RAG 里，它通常对应一个知识库、一类文档或一个业务域。
```

### 自测 2：Qdrant 的 point 是什么？

参考答案：

```text
point 是 collection 里的一条向量记录，通常包含 id、vector 和 payload。在 RAG 里，一个 point 通常对应一个 chunk。
```

### 自测 3：vector 在 point 里负责什么？

参考答案：

```text
vector 是 chunk 的 embedding，用于和用户问题的 query vector 做相似度比较，从而召回相关 chunk。
```

### 自测 4：payload 在 point 里负责什么？

参考答案：

```text
payload 保存和 vector 关联的业务信息，例如 chunk 原文、来源、标题、章节、权限组、文档类型等，用于展示、引用、过滤和排查。
```

### 自测 5：metadata 和 payload 有什么关系？

参考答案：

```text
metadata 是 RAG 语境里描述文档或 chunk 的信息；payload 是 Qdrant 语境里 point 上附带的 JSON 信息。metadata 写入 Qdrant 后，通常会成为 payload 的一部分。
```

### 自测 6：score 是 point 的固定字段吗？

参考答案：

```text
不是。score 是查询时根据 query vector 和 point.vector 计算出来的相似度结果。同一个 point 面对不同问题会有不同 score。
```

### 自测 7：为什么一个 chunk 通常对应一个 point？

参考答案：

```text
因为 RAG 需要检索能回答问题的局部材料。把整篇文档作为一个 point 太粗，会让 prompt 变长、噪声变多、引用不精确。chunk 作为 point 更利于精准召回。
```

### 自测 8：payload filter 为什么依赖字段设计？

参考答案：

```text
filter 是基于 payload 字段做条件过滤。如果写入 point 时没有保存 permission_group、doc_type、source 等字段，查询时就无法按这些条件过滤。
```

## 本节复盘

这一节你要真正掌握的不是 Qdrant API，而是这套映射关系：

```text
知识库 -> collection
文档切分后的 chunk -> point
chunk_id -> point id
chunk embedding -> vector
chunk 原文和 metadata -> payload
检索相关性 -> query 时返回的 score
```

你还要能解释：

```text
1. 为什么 collection 要关心向量维度和距离算法。
2. 为什么 point 通常对应 chunk，而不是整篇文档。
3. 为什么 payload 是企业 RAG 的核心字段集合。
4. 为什么 point id 要稳定。
5. 为什么 score 不是 point 固定字段。
```

如果这些能讲清楚，下一节本地启动 Qdrant 时，你就不会只是看到一个服务端口，而是知道这个服务以后要承载什么数据。

## 参考资料

- [Qdrant Collections](https://qdrant.tech/documentation/manage-data/collections/)
- [Qdrant Points](https://qdrant.tech/documentation/manage-data/points/)
- [Qdrant Vectors](https://qdrant.tech/documentation/manage-data/vectors/)
- [Qdrant Payload](https://qdrant.tech/documentation/manage-data/payload/)
- [Qdrant Filtering](https://qdrant.tech/documentation/search/filtering/)
- [Qdrant Similarity Search](https://qdrant.tech/documentation/search/search/)
