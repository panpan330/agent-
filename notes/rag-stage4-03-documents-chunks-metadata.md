# 阶段 4 第 3 节：文档、知识库、chunk、metadata 是什么

> 本节结论：RAG 不是把“文件”直接丢进向量数据库，而是把文档拆成多个可检索的 chunk，并给每个 chunk 绑定 metadata。向量数据库真正检索的基本单位通常是 chunk，不是整篇文档。metadata 决定了引用来源、权限过滤、版本排查、文档更新和后续评测能力。

## 生成笔记前的教学复核

这一节继续打基础，不急着接 Qdrant。

这一节必须讲清：

```text
1. document 是什么。
2. knowledge base 是什么。
3. chunk 是什么，为什么不能总是整篇文档入库。
4. metadata 是什么，为什么它不是可有可无的附属品。
5. document、chunk、embedding、vector、metadata、vector store 的关系。
6. 一个企业知识库里的文档应该怎么组织。
7. 后续引用来源、权限过滤、更新删除为什么都依赖 metadata。
```

## 本节一句话定位

第 1 节讲了：

```text
为什么需要 RAG。
```

第 2 节讲了：

```text
RAG 的两条流水线。
```

第 3 节要讲：

```text
RAG 流水线里流动的数据到底是什么。
```

如果你不知道 document、chunk、metadata 的区别，后面写向量库入库代码时就会只是在“存字符串”，不知道自己为什么这样存。

## 先给一张关系图

先看整体关系：

```text
Knowledge Base 知识库
  |
  +-- Document 文档 1：售后政策.md
  |     |
  |     +-- Chunk 1：退款规则
  |     +-- Chunk 2：物流异常
  |     +-- Chunk 3：投诉升级
  |
  +-- Document 文档 2：产品手册.md
  |     |
  |     +-- Chunk 1：安装步骤
  |     +-- Chunk 2：常见故障
  |
  +-- Document 文档 3：接口说明.md
        |
        +-- Chunk 1：创建工单接口
        +-- Chunk 2：查询订单接口
```

每个 chunk 入库时，通常会变成：

```text
chunk content
-> embedding vector
-> metadata
-> vector store point/entity
```

所以你要记住：

```text
知识库由文档组成。
文档会被切成 chunk。
chunk 会被 embedding 成向量。
向量和 metadata 一起写入向量数据库。
检索时返回的是相关 chunk。
回答时引用的是 chunk 的 metadata。
```

## 什么是 document

document 就是知识库里的原始知识来源。

它可以是一个文件，也可以不是文件。

常见 document 来源包括：

```text
Markdown 文档
txt 文档
PDF 文件
Word 文档
网页
数据库记录
FAQ 条目
工单历史
接口文档
产品手册
公司制度
```

在最开始学习时，我们会优先用：

```text
Markdown / txt
```

因为它们简单、可读、方便调试。

### document 不等于文件路径

很多初学者会把 document 理解成：

```text
一个文件路径
```

这只对了一部分。

文件路径只是 document 的来源之一。

一个 document 至少应该包含：

```text
文档 ID
标题
正文内容
来源
文档类型
所属空间
更新时间
权限信息
```

例如：

```json
{
  "doc_id": "after_sales_policy",
  "title": "售后政策",
  "source": "docs/after-sales-policy.md",
  "doc_type": "policy",
  "department": "customer_service",
  "access_level": "internal",
  "updated_at": "2026-07-14",
  "content": "订单超过 72 小时仍未发货..."
}
```

这比单纯一个文件路径有用得多。

因为后面你要做：

```text
引用来源
权限过滤
文档更新
删除旧版本
按部门检索
按文档类型检索
```

这些都需要 document 的结构化信息。

### document 是入库前的较大单位

可以这样理解：

```text
document 是人类写作和管理知识的单位。
chunk 是机器检索知识的单位。
```

人类通常按文档管理：

```text
售后政策.md
产品安装手册.pdf
退款规则.docx
```

机器检索时通常按 chunk 搜索：

```text
售后政策 / 物流异常处理这一段
产品安装手册 / 第 3 步安装说明这一段
退款规则 / 退款时效这一段
```

## 什么是 knowledge base

knowledge base 就是知识库。

但在 RAG 里，它不是一个抽象口号。

它通常表示：

```text
一组文档
一套入库规则
一个或多个向量库 collection
一套权限和 metadata 设计
一个检索问答入口
```

例如你可以有多个知识库：

```text
客服知识库
研发文档知识库
人事制度知识库
产品手册知识库
```

每个知识库可能有不同：

```text
文档来源
用户权限
chunk 策略
embedding 模型
向量库 collection
更新频率
引用展示方式
```

### 知识库不是文件夹那么简单

你可以用文件夹组织知识库。

例如：

```text
knowledge_base/
  customer_service/
    after_sales_policy.md
    refund_policy.md
  product/
    install_manual.md
    troubleshooting.md
```

但真正的知识库还包括：

```text
这些文件怎么读取
怎么切分
怎么生成向量
怎么写入向量库
怎么过滤权限
怎么返回引用
怎么更新删除
```

所以知识库是：

```text
文档集合 + 处理规则 + 检索能力
```

## 什么是 chunk

chunk 是从 document 里切出来的小文本片段。

例如原文档：

```text
售后政策

1. 退款规则
用户收到商品 7 天内可以申请退款...

2. 物流异常处理
订单超过 72 小时仍未发货，客服应先查询订单状态...

3. 投诉升级
用户连续两次催促未解决时，可以升级投诉...
```

切分后可能得到：

```text
chunk 1：退款规则这一段
chunk 2：物流异常处理这一段
chunk 3：投诉升级这一段
```

### 为什么需要 chunk

因为整篇文档通常不适合直接作为检索单位。

原因有几个。

#### 1. 整篇文档太大

一篇文档可能有几千字、几万字。

如果整篇做 embedding：

```text
一个向量代表太多主题
语义会被稀释
检索不够精准
```

例如一篇售后政策同时讲：

```text
退款
换货
物流
投诉
保修
```

用户问物流问题。

整篇文档的向量可能不如“物流异常处理”这一段精准。

#### 2. prompt 不能无限长

检索到整篇文档后，如果把整篇都放进 prompt：

```text
token 成本高
上下文太长
模型不容易抓重点
引用来源太粗
```

chunk 能让系统只给模型最相关的少量资料。

#### 3. 引用来源要精确

如果引用整篇文档，用户仍然不知道答案来自哪里。

更好的引用是：

```text
售后政策.md / 物流异常处理 / chunk 3
```

chunk 让引用更精确。

#### 4. 权限和版本可能细到章节

有时同一份文档里不同章节权限不同。

比如：

```text
公开 FAQ
内部处理规则
主管审批规则
```

如果都放在一个大 chunk 里，就不容易做细粒度权限控制。

## chunk 太大和太小的问题

chunk 不是越大越好，也不是越小越好。

### chunk 太大

问题：

```text
主题混杂
检索不精准
prompt 变长
模型抓不到重点
引用来源粗糙
```

例子：

```text
一个 chunk 同时包含退款、物流、投诉、保修四个主题。
```

用户问物流，检索结果里却带来很多退款和保修内容。

### chunk 太小

问题：

```text
上下文不足
语义被切断
模型无法理解完整规则
引用片段不完整
```

例子：

```text
chunk A：订单超过 72 小时仍未发货
chunk B：客服应先查询订单状态
chunk C：如确认未出库可创建投诉工单
```

如果只检索到 chunk A，模型不知道后续处理动作。

### 好 chunk 的基本标准

好的 chunk 通常应该：

```text
语义相对完整
主题尽量单一
长度适中
保留标题或章节信息
能独立支持一个小问题的回答
能追溯到原始文档
```

后面第 12 节会专门讲 chunk 切分策略。

本节先记住：

```text
chunk 是 RAG 检索质量的核心单位。
```

## 什么是 metadata

metadata 是描述数据的数据。

在 RAG 里，metadata 是 chunk 的附加信息。

它不是模型直接回答的主体，但它决定系统能不能管理、过滤、引用和排查。

一个 chunk 可以这样表示：

```json
{
  "chunk_id": "after_sales_policy_0003",
  "content": "订单超过 72 小时仍未发货，客服应先查询订单状态...",
  "metadata": {
    "doc_id": "after_sales_policy",
    "source": "docs/after-sales-policy.md",
    "title": "售后政策",
    "section": "物流异常处理",
    "doc_type": "policy",
    "department": "customer_service",
    "access_level": "internal",
    "version": "2026-07",
    "updated_at": "2026-07-14",
    "chunk_index": 3
  }
}
```

其中：

```text
content 是模型真正会参考的文本。
metadata 是后端用于管理和过滤的信息。
```

## metadata 为什么重要

metadata 至少有 7 个作用。

### 1. 引用来源

用户看到答案时，需要知道：

```text
答案来自哪份文档
哪一节
哪个片段
```

这需要：

```text
source
title
section
chunk_index
```

如果没有 metadata，系统只能说：

```text
根据资料显示...
```

但说不出资料是哪份。

### 2. 权限过滤

不同用户能看的文档不同。

例如：

```text
access_level: public
access_level: internal
access_level: manager_only
```

检索时可以加 filter：

```text
只检索当前用户有权访问的 chunk
```

这依赖 metadata。

如果没有 metadata，向量库可能把用户无权看的内容检索出来。

这是严重安全问题。

### 3. 文档类型过滤

用户可能只想查：

```text
policy 政策
manual 手册
faq 常见问题
api_doc 接口文档
ticket_case 历史工单
```

这需要：

```text
doc_type
```

例如：

```json
{"doc_type": "policy"}
```

### 4. 部门或项目空间过滤

企业里可能有多个部门：

```text
customer_service
product
engineering
finance
hr
```

用户属于哪个部门，就优先或只能检索哪个部门的文档。

这需要：

```text
department
workspace_id
project_id
```

### 5. 版本管理

文档会更新。

如果同一份文档有多个版本，需要知道：

```text
当前 chunk 来自哪个版本
是不是最新版本
更新时间是什么
```

这需要：

```text
version
updated_at
```

否则模型可能引用旧政策。

### 6. 删除和重新入库

后面学文档更新时会遇到：

```text
文档改了，要删除旧 chunk，写入新 chunk。
```

如果每个 chunk 都有：

```text
doc_id
```

就可以删除：

```text
doc_id = after_sales_policy 的所有旧 chunk
```

如果没有 doc_id，删除旧数据会很麻烦。

### 7. 调试和评测

RAG 效果不好时，你要排查：

```text
检索到了哪几个 chunk
它们来自哪份文档
相似度分数是多少
为什么没检索到正确文档
是不是权限 filter 过滤掉了
是不是旧版本文档还在
```

这些都依赖 metadata。

所以 metadata 不是附属品。

它是 RAG 工程能力的一部分。

## 向量数据库里到底存什么

很多人以为向量数据库只存 vector。

这不够。

一个 RAG chunk 入库通常至少包括：

```text
id
vector
payload / metadata
content
```

以 Qdrant 的概念来说，后面会看到：

```text
point = id + vector + payload
```

payload 里通常要放：

```text
content
source
title
section
doc_id
chunk_index
access_level
updated_at
```

检索时，向量数据库根据 vector 找相似 chunk。

返回时，系统拿 payload 里的 content 和 metadata 组装回答。

也就是说：

```text
vector 负责找相似内容。
content 负责给模型参考。
metadata 负责过滤、引用、管理和排查。
```

## document、chunk、embedding、vector 的关系

这几个词容易混。

用一张表区分：

| 概念 | 是什么 | 主要用途 |
| --- | --- | --- |
| document | 原始文档或知识来源 | 人类管理知识 |
| chunk | 从 document 切出的文本片段 | 机器检索的基本单位 |
| content | chunk 的正文文本 | 给模型阅读和回答 |
| metadata | chunk 的附加信息 | 引用、过滤、权限、更新、排查 |
| embedding | 把文本转向量的过程或结果 | 语义相似度检索 |
| vector | 一组数字 | 向量数据库搜索 |
| vector store | 存 vector 和 payload 的系统 | 按相似度检索 chunk |

一句话：

```text
document 被切成 chunk，chunk content 被 embedding 成 vector，vector 和 metadata 一起存进 vector store。
```

## 一个完整例子

原始文档：

```text
文件：售后政策.md
标题：售后政策

## 物流异常处理

订单超过 72 小时仍未发货，客服应先查询订单状态和仓库处理记录。
如确认未出库，可创建投诉工单并标记为 high urgency。
```

入库前的 document：

```json
{
  "doc_id": "after_sales_policy",
  "title": "售后政策",
  "source": "docs/after-sales-policy.md",
  "doc_type": "policy",
  "department": "customer_service",
  "access_level": "internal",
  "content": "## 物流异常处理\n订单超过 72 小时仍未发货..."
}
```

切出来的 chunk：

```json
{
  "chunk_id": "after_sales_policy_0001",
  "content": "订单超过 72 小时仍未发货，客服应先查询订单状态和仓库处理记录。如确认未出库，可创建投诉工单并标记为 high urgency。",
  "metadata": {
    "doc_id": "after_sales_policy",
    "source": "docs/after-sales-policy.md",
    "title": "售后政策",
    "section": "物流异常处理",
    "doc_type": "policy",
    "department": "customer_service",
    "access_level": "internal",
    "chunk_index": 1
  }
}
```

写入向量库的 point：

```json
{
  "id": "after_sales_policy_0001",
  "vector": [0.012, -0.231, 0.887],
  "payload": {
    "content": "订单超过 72 小时仍未发货...",
    "doc_id": "after_sales_policy",
    "source": "docs/after-sales-policy.md",
    "title": "售后政策",
    "section": "物流异常处理",
    "access_level": "internal"
  }
}
```

用户问：

```text
订单三天没发货，客服应该怎么处理？
```

检索返回：

```text
chunk_id: after_sales_policy_0001
content: 订单超过 72 小时仍未发货...
source: docs/after-sales-policy.md
section: 物流异常处理
score: 0.86
```

最终回答引用：

```text
来源：售后政策 / 物流异常处理
```

这就是 document、chunk、metadata 在一条链路里的关系。

## 企业知识库应该怎么组织

最开始可以用简单目录：

```text
knowledge-base/
  customer-service/
    after-sales-policy.md
    refund-policy.md
    logistics-faq.md
  product/
    install-manual.md
    troubleshooting.md
  engineering/
    api-orders.md
    api-tickets.md
```

但目录只是第一层组织。

还要给每份文档设计 metadata。

例如：

```text
customer-service/after-sales-policy.md
doc_type: policy
department: customer_service
access_level: internal
```

```text
product/install-manual.md
doc_type: manual
department: product
access_level: public
```

```text
engineering/api-orders.md
doc_type: api_doc
department: engineering
access_level: internal
```

这样后续就可以做：

```text
只查客服文档
只查公开文档
只查 policy
只查 engineering 下的接口文档
```

## metadata 字段设计建议

阶段 4 初期可以先设计这些字段。

| 字段 | 含义 | 用途 |
| --- | --- | --- |
| `doc_id` | 文档唯一 ID | 更新、删除、分组 |
| `chunk_id` | chunk 唯一 ID | 精确引用和排查 |
| `source` | 来源路径或 URL | 引用来源 |
| `title` | 文档标题 | 展示和引用 |
| `section` | 章节标题 | 精确定位 |
| `chunk_index` | chunk 顺序 | 排序和排查 |
| `doc_type` | 文档类型 | 类型过滤 |
| `department` | 所属部门 | 部门过滤 |
| `access_level` | 权限等级 | 权限过滤 |
| `version` | 文档版本 | 版本管理 |
| `updated_at` | 更新时间 | 排查旧文档 |

注意：

```text
metadata 字段不要无限膨胀。
```

先放真正会用于：

```text
引用
过滤
权限
更新
排查
```

的字段。

## chunk_id 怎么设计

chunk_id 最好稳定、可追溯。

简单设计：

```text
{doc_id}_{chunk_index}
```

例如：

```text
after_sales_policy_0001
after_sales_policy_0002
after_sales_policy_0003
```

更严谨的设计可以加入版本或内容 hash：

```text
{doc_id}_{version}_{chunk_index}
{doc_id}_{content_hash}
```

为什么要稳定 ID？

因为后续要做：

```text
重复入库去重
删除旧 chunk
更新文档
排查某个引用
评测命中结果
```

如果每次随机生成 ID，管理会变困难。

## 本节暂时不学什么

本节不学：

```text
具体 chunk size 选多少
overlap 怎么设置
Markdown 解析代码怎么写
Qdrant point 怎么创建
Milvus schema 怎么定义
embedding API 怎么调用
权限过滤代码怎么写
```

这些后面会讲。

本节只要先把数据单位搞清楚：

```text
document
knowledge base
chunk
content
metadata
embedding
vector
vector store
```

## 常见误区

### 误区 1：向量数据库里直接存文档

不准确。

通常不是整篇文档直接入库，而是把文档切成 chunk，再把 chunk 的向量和 metadata 入库。

### 误区 2：metadata 可有可无

不对。

没有 metadata，就很难做引用来源、权限过滤、文档更新、删除旧版本和检索排查。

### 误区 3：chunk 越小越精准

不一定。

chunk 太小会丢上下文。

精准不是越小越好，而是：

```text
语义完整 + 主题单一 + 长度适中
```

### 误区 4：source 只需要文件名

不一定。

文件名只是最基础来源。

更好的来源还包括：

```text
title
section
chunk_index
version
updated_at
```

这样引用更准确。

### 误区 5：权限可以等回答时再处理

不应该。

权限最好在检索阶段就过滤。

否则模型可能已经看到了用户无权访问的 chunk。

正确思路是：

```text
先按权限过滤可检索范围
再把检索结果交给模型
```

## 本节练习

### 练习 1：区分概念

题目：

```text
请分别用一句话解释 document、chunk、metadata。
```

参考答案：

```text
document：知识库里的原始知识来源，例如一份售后政策文档。
chunk：从 document 中切出来的、用于检索的小文本片段。
metadata：描述 chunk 来源、标题、章节、权限、版本等信息的数据。
```

### 练习 2：判断哪些适合作为 metadata

题目：

```text
下面哪些字段适合作为 metadata？

1. 文档标题 title
2. 文档正文 content
3. 文档来源 source
4. 用户问题 question
5. 权限等级 access_level
6. 章节 section
7. chunk 顺序 chunk_index
```

参考答案：

```text
适合作为 metadata：
1. title
3. source
5. access_level
6. section
7. chunk_index

不适合作为 metadata：
2. content 是 chunk 正文，通常放在 payload 中给模型阅读，不只是 metadata。
4. question 是用户查询，不属于文档 chunk 的 metadata。
```

### 练习 3：为什么不能只存 vector

题目：

```text
如果向量数据库里只存 vector，不存 content 和 metadata，会有什么问题？
```

参考答案：

```text
只能找到相似向量，但不知道对应的原文是什么，也不知道来源、标题、章节、权限和版本。这样无法把资料交给模型回答，也无法返回引用来源，更无法做权限过滤和文档更新。
```

### 练习 4：设计一个 chunk

题目：

```text
给下面文本设计一个 chunk 结构：

文件：refund-policy.md
标题：退款政策
章节：退款时效
内容：用户收到商品 7 天内可以申请退款，超过 7 天需人工审核。
```

参考答案：

```json
{
  "chunk_id": "refund_policy_0001",
  "content": "用户收到商品 7 天内可以申请退款，超过 7 天需人工审核。",
  "metadata": {
    "doc_id": "refund_policy",
    "source": "refund-policy.md",
    "title": "退款政策",
    "section": "退款时效",
    "doc_type": "policy",
    "department": "customer_service",
    "access_level": "internal",
    "chunk_index": 1
  }
}
```

### 练习 5：判断检索单位

题目：

```text
用户问“超过 72 小时未发货怎么办？”，RAG 最好检索整篇售后政策，还是检索相关 chunk？为什么？
```

参考答案：

```text
最好检索相关 chunk。整篇售后政策可能包含退款、换货、保修、投诉等多个主题，粒度太粗。相关 chunk 能提供更精准的上下文，降低 token 成本，也能给出更准确的引用来源。
```

## 自测题

### 自测 1：知识库和文档是什么关系？

参考答案：

```text
知识库是一组文档和处理规则的集合。文档是知识库里的原始知识来源，知识库还包括文档如何入库、切分、向量化、检索、过滤和引用。
```

### 自测 2：RAG 检索的基本单位通常是什么？

参考答案：

```text
通常是 chunk，而不是整篇 document。chunk 是从文档里切出来的可检索片段。
```

### 自测 3：metadata 最重要的作用有哪些？

参考答案：

```text
引用来源、权限过滤、文档类型过滤、部门或项目空间过滤、版本管理、删除和重新入库、调试和评测。
```

### 自测 4：vector、content、metadata 各自负责什么？

参考答案：

```text
vector 负责相似度检索。
content 负责给模型阅读并生成回答。
metadata 负责引用、过滤、权限、更新、排查和评测。
```

### 自测 5：为什么 chunk_id 最好稳定？

参考答案：

```text
稳定的 chunk_id 方便重复入库去重、删除旧 chunk、更新文档、排查引用来源和做评测。如果每次随机生成 ID，后续管理会很困难。
```

### 自测 6：权限过滤应该在检索前还是回答后做？

参考答案：

```text
应该尽量在检索阶段做。这样可以避免模型看到用户无权访问的内容。回答后再过滤已经太晚，因为敏感资料可能已经进入模型上下文。
```

### 自测 7：为什么本节还不直接讲 Qdrant？

参考答案：

```text
因为在学习 Qdrant point、payload、collection 之前，必须先理解 RAG 要存的基本数据单位。否则后面只会照着 API 存数据，却不知道 vector、content 和 metadata 分别承担什么职责。
```

## 本节总结

这一节你要记住：

```text
document 是原始知识来源。
knowledge base 是文档集合加处理和检索规则。
chunk 是 RAG 检索的基本文本单位。
metadata 是引用、过滤、权限、更新和排查的关键。
vector 负责相似度检索。
content 负责给模型回答。
```

最重要的一句话：

```text
RAG 入库不是存“文件”，而是存“可检索的 chunk + vector + metadata”。
```

下一节学习：

```text
阶段 4 第 4 节：embedding 是什么：文本怎么变成向量
```

下一节会专门讲为什么文本可以变成数字向量，为什么向量能表示语义相似度，以及 embedding 在 RAG 里到底承担什么角色。

