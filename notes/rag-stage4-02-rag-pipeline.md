# 阶段 4 第 2 节：RAG 完整流程：load -> split -> embed -> store -> retrieve -> generate

> 本节结论：RAG 不是一个单独的 API 调用，而是两条工程流水线。第一条是“文档入库流水线”：把原始文档变成可检索的 chunk、embedding 和 metadata，存进向量库。第二条是“用户问答流水线”：把用户问题变成查询，检索相关 chunk，组装 prompt，让模型基于资料回答并返回引用来源。

## 生成笔记前的教学复核

本节继续以理解为主，不急着写代码。

这一节必须讲清：

```text
1. RAG 为什么要分成文档入库阶段和用户问答阶段。
2. load、clean、split、embed、store 分别做什么。
3. question、embed query、retrieve、build prompt、generate、cite sources 分别做什么。
4. 每一步的输入是什么，输出是什么。
5. 每一步出错会导致什么问题。
6. 为什么 RAG 不是“直接把文档给模型”。
7. 后续代码会落在哪些模块里。
```

## 本节一句话定位

第 1 节讲的是：

```text
为什么需要 RAG。
```

第 2 节讲的是：

```text
RAG 系统到底怎么跑起来。
```

你要把 RAG 想成一个小型数据工程系统，而不是一个单纯的模型调用。

## RAG 不是一步，而是两条流水线

很多初学者会把 RAG 想得太简单：

```text
用户问问题
-> 查一下文档
-> 让模型回答
```

这个说法方向没错，但太粗。

真实 RAG 至少分成两条流水线。

第一条：

```text
文档入库流水线
```

第二条：

```text
用户问答流水线
```

### 文档入库流水线

它发生在用户提问之前。

目标是：

```text
把企业文档处理成向量数据库能检索的数据。
```

流程是：

```text
load -> clean -> split -> embed -> store
```

更完整一点：

```text
原始文档
-> 读取文档
-> 清洗文本
-> 切成 chunk
-> 生成 embedding
-> 绑定 metadata
-> 写入向量数据库
```

### 用户问答流水线

它发生在用户提问时。

目标是：

```text
根据用户问题找到相关资料，再让模型基于资料回答。
```

流程是：

```text
question -> embed query -> retrieve -> build prompt -> generate -> cite sources
```

更完整一点：

```text
用户问题
-> 问题向量化
-> 向量库检索 top_k chunk
-> 过滤低相关结果
-> 组装 RAG prompt
-> 调用模型生成回答
-> 返回答案和引用来源
```

## 为什么要分成两条流水线

因为“处理文档”和“回答问题”不是同一类工作。

### 文档入库是后台工作

文档入库通常是：

```text
批量的
耗时的
可重复执行的
需要保存结果的
不一定由用户请求实时触发的
```

例如：

```text
每天晚上同步最新文档
管理员上传文档后触发入库
文档更新后重新切分和向量化
删除过期文档的旧 chunk
```

### 用户问答是在线工作

用户问答通常是：

```text
实时的
需要低延迟的
需要权限过滤的
需要返回可读答案的
```

例如用户问：

```text
订单超过 72 小时未发货，客服应该怎么处理？
```

系统不能这时才把全部公司文档重新读取、切分、embedding 一遍。

正确做法是：

```text
文档提前入库
用户提问时只做查询和回答
```

这就是为什么 RAG 要拆成两条流水线。

## 文档入库流水线详解

现在逐步拆开：

```text
load -> clean -> split -> embed -> store
```

### 1. load：读取文档

load 的意思是：

```text
从某个来源读取原始文档内容。
```

来源可以是：

```text
本地 Markdown 文件
txt 文件
PDF 文件
docx 文件
网页
数据库记录
对象存储里的文件
企业知识库系统 API
```

在最开始，我们会用最简单的：

```text
Markdown / txt
```

因为它们容易读取，适合先理解 RAG 主线。

load 的输入和输出：

| 项目 | 内容 |
| --- | --- |
| 输入 | 文件路径、数据库记录、网页 URL、API 返回数据 |
| 输出 | 原始文本 + 基础来源信息 |

例如输入：

```text
docs/售后政策.md
```

输出可能是：

```text
content: "订单超过 72 小时未发货..."
source: "售后政策.md"
```

### 2. clean：清洗文本

clean 的意思是：

```text
把原始文本里的无效内容、噪声和格式问题处理掉。
```

常见清洗内容：

```text
去掉多余空行
去掉页眉页脚
去掉重复导航
去掉乱码字符
统一换行
去掉无意义目录
修正明显格式残留
```

为什么要清洗？

因为脏数据会影响后续所有步骤。

例如 PDF 解析后可能变成：

```text
售 后 政 策
第 1 页 / 共 10 页
订单超过 72 小时...
第 2 页 / 共 10 页
```

如果页码、页眉、页脚全都进入 chunk 和 embedding，检索质量会下降。

clean 的输入和输出：

| 项目 | 内容 |
| --- | --- |
| 输入 | 原始文本 |
| 输出 | 清洗后的文本 |

注意：

```text
清洗不是随便删内容。
```

真实项目里要避免把有效信息删掉。

### 3. split：切成 chunk

split 的意思是：

```text
把一篇长文档切成多个小片段。
```

这些小片段就叫：

```text
chunk
```

为什么要 split？

因为长文档直接做 embedding 有几个问题：

```text
粒度太粗
检索不精准
上下文太长
成本高
引用来源不清晰
```

例如一份售后政策有 10 个章节：

```text
1. 退款规则
2. 物流异常
3. 投诉升级
4. 保修政策
...
```

用户只问物流异常。

如果整篇文档作为一个向量，系统只能返回整篇文档。

如果按章节或段落切成 chunk，系统可以直接返回：

```text
物流异常处理
```

split 的输入和输出：

| 项目 | 内容 |
| --- | --- |
| 输入 | 清洗后的长文本 |
| 输出 | 多个 chunk |

每个 chunk 通常包含：

```text
chunk_id
content
source
title
section
chunk_index
```

后面我们会专门讲 chunk size 和 overlap。

现在先记住：

```text
chunk 是 RAG 检索的基本单位。
```

### 4. embed：生成向量

embed 的意思是：

```text
用 embedding 模型把文本 chunk 转成数字向量。
```

例如：

```text
"订单超过 72 小时未发货可以升级投诉"
```

会变成：

```text
[0.012, -0.183, 0.764, ...]
```

为什么要生成向量？

因为向量可以用来比较语义相似度。

用户问：

```text
订单三天没发货怎么办？
```

它和下面这段文本语义相近：

```text
订单超过 72 小时未发货可以升级投诉
```

虽然字面上不完全一样。

embedding 的价值就在这里：

```text
不只按关键词匹配，而是按语义相似度匹配。
```

embed 的输入和输出：

| 项目 | 内容 |
| --- | --- |
| 输入 | chunk 文本 |
| 输出 | chunk 向量 |

需要注意：

```text
文档 chunk 用什么 embedding 模型生成，
用户问题最好也用同一个 embedding 模型生成。
```

否则向量空间可能不一致。

### 5. store：写入向量数据库

store 的意思是：

```text
把 chunk 的向量、文本和 metadata 存进向量数据库。
```

一个入库后的记录通常包含：

```text
id
vector
payload / metadata
```

payload 里可能有：

```json
{
  "content": "订单超过 72 小时未发货可以升级投诉",
  "source": "售后政策.md",
  "title": "售后政策",
  "section": "物流异常处理",
  "doc_type": "policy",
  "access_level": "internal",
  "chunk_index": 3
}
```

store 的输入和输出：

| 项目 | 内容 |
| --- | --- |
| 输入 | chunk、embedding、metadata |
| 输出 | 向量数据库里的 points/entities |

在 Qdrant 里，我们后面会叫它：

```text
point
```

在 Milvus 里，后面会看到：

```text
entity / row
```

不同向量库叫法不完全一样，但本质类似：

```text
一条可检索的向量记录
```

## 用户问答流水线详解

现在拆开第二条：

```text
question -> embed query -> retrieve -> build prompt -> generate -> cite sources
```

### 1. question：用户问题

question 就是用户输入。

例如：

```text
订单三天没发货，客服应该怎么处理？
```

这一步看起来简单，但真实项目里也要注意：

```text
问题不能为空
问题不能太长
可能包含 prompt injection
可能涉及用户权限
可能需要 trace_id
```

阶段 1 和阶段 2 学过的请求校验、日志、异常处理，在 RAG 里仍然需要。

### 2. embed query：问题向量化

用户问题也要变成向量。

原因是：

```text
向量库里存的是 chunk 向量。
要找相似 chunk，就要把问题也变成同一个向量空间里的向量。
```

输入输出：

| 项目 | 内容 |
| --- | --- |
| 输入 | 用户问题 |
| 输出 | query vector |

例如：

```text
"订单三天没发货怎么办？"
-> [0.031, -0.129, 0.552, ...]
```

### 3. retrieve：检索相关 chunk

retrieve 的意思是：

```text
用用户问题向量去向量数据库里找最相似的 chunk。
```

常见参数：

```text
top_k
score_threshold
filter
```

### top_k

top_k 表示：

```text
返回最相似的前 k 条结果。
```

例如：

```text
top_k = 5
```

就是返回最相关的 5 个 chunk。

### score_threshold

score_threshold 表示：

```text
低于某个相似度分数就不要返回。
```

它的目的：

```text
避免把不相关资料交给模型。
```

### filter

filter 表示：

```text
按 metadata 过滤。
```

例如：

```text
只检索 doc_type=policy 的文档
只检索 access_level 在当前用户权限范围内的文档
只检索 customer_service 部门文档
```

retrieve 的输入输出：

| 项目 | 内容 |
| --- | --- |
| 输入 | query vector、top_k、filter、score_threshold |
| 输出 | 相关 chunk 列表 |

### 4. build prompt：组装提示词

拿到检索结果后，不能直接把结果原封不动丢给模型。

要构造一个明确的 RAG prompt。

它通常包括：

```text
系统角色
回答规则
检索到的资料
用户问题
资料不足时的处理方式
引用来源要求
```

例如：

```text
你是企业知识库助手。
请只根据下面资料回答用户问题。
如果资料不足，请回答“当前资料不足，无法确定”。
回答必须列出引用来源。

资料：
[1] 售后政策.md / 物流异常处理
订单超过 72 小时未发货...

用户问题：
订单三天没发货，客服应该怎么处理？
```

build prompt 的输入输出：

| 项目 | 内容 |
| --- | --- |
| 输入 | 用户问题、检索 chunk、回答规则 |
| 输出 | 发给模型的 messages/prompt |

### 5. generate：模型生成回答

generate 就是调用大模型。

但 RAG 里的生成和普通聊天不同。

普通聊天可以让模型自由回答。

RAG 应该要求模型：

```text
只根据资料回答
不要编造资料里没有的内容
资料不足时拒答
回答带引用来源
```

generate 的输入输出：

| 项目 | 内容 |
| --- | --- |
| 输入 | RAG prompt / messages |
| 输出 | 模型回答 |

### 6. cite sources：返回引用来源

引用来源是 RAG 很重要的工程能力。

不要只返回：

```text
客服应该先查询订单状态，如果超过 72 小时未发货可以创建投诉工单。
```

还要返回：

```text
来源：
1. 售后政策.md / 物流异常处理
```

引用来源可以来自 chunk 的 metadata。

例如：

```json
{
  "source": "售后政策.md",
  "section": "物流异常处理",
  "chunk_index": 3
}
```

cite sources 的输入输出：

| 项目 | 内容 |
| --- | --- |
| 输入 | 检索 chunk 的 metadata、模型回答 |
| 输出 | 答案 + sources |

引用来源的价值：

```text
用户能验证答案
开发者能排查问题
管理员能发现文档过期
评测时能检查引用是否正确
```

## 两条流水线合在一起

完整 RAG 可以画成这样：

```text
文档入库阶段：

Markdown / txt / PDF / docx
  |
  v
load 读取文档
  |
  v
clean 清洗文本
  |
  v
split 切成 chunk
  |
  v
embed 生成 chunk 向量
  |
  v
store 写入向量数据库


用户问答阶段：

用户问题
  |
  v
embed query 生成问题向量
  |
  v
retrieve 检索相关 chunk
  |
  v
build prompt 组装资料和问题
  |
  v
generate 模型回答
  |
  v
cite sources 返回答案和来源
```

这张图后面会一直用。

阶段 4 后续每一节，基本都在细化这张图里的某个节点。

## 每一步失败会发生什么

RAG 的难点不是“能不能跑通一次 demo”。

难点是：

```text
每一步质量都会影响最终回答。
```

| 步骤 | 如果做不好 | 最终表现 |
| --- | --- | --- |
| load | 文档没读全，编码错误，格式丢失 | 知识库缺内容 |
| clean | 噪声太多，删错内容 | 检索命中奇怪内容或缺关键内容 |
| split | chunk 太大或太小，切断语义 | 检索不准，回答缺上下文 |
| embed | 模型选错，批量失败，维度不一致 | 无法入库或检索质量差 |
| store | metadata 缺失，id 不稳定，重复入库 | 引用混乱，更新困难 |
| embed query | 问题向量化失败 | 无法检索 |
| retrieve | top_k、filter、阈值不合理 | 找不到资料或找错资料 |
| build prompt | 规则不清，资料格式混乱 | 模型乱答或引用不清 |
| generate | 不限制依据资料回答 | 幻觉或编造出处 |
| cite sources | metadata 不完整 | 答案无法追溯 |

这就是为什么 RAG 是工程问题，不只是模型问题。

## RAG 和阶段 1-3 的关系

阶段 4 不是从零开始。

前面学过的很多东西会复用。

### 阶段 1 的基础

阶段 1 学的：

```text
FastAPI
router
Pydantic
配置读取
日志
trace_id
统一异常处理
CORS
测试
```

RAG 服务也需要这些。

例如：

```text
POST /rag/query
GET /rag/documents
POST /rag/ingest
```

都要请求模型、响应模型、异常处理和测试。

### 阶段 2 的基础

阶段 2 学的：

```text
模型调用
messages
prompt
timeout
retry
streaming
结构化输出
fake LLM 测试
```

RAG 的 generate 阶段会复用这些。

比如：

```text
检索到 chunk 后，仍然要调用 LLM 生成回答。
```

### 阶段 3 的基础

阶段 3 学的：

```text
Tool Calling
Java API
权限边界
幂等
trace_id 串联
LangChain
分层测试
```

RAG 会继续复用工程思想：

```text
外部系统结果不可信，要校验
日志不能记录敏感信息
用户权限必须参与过滤
测试不能真实依赖所有外部服务
```

后续智能工单 Agent 会把阶段 3 和阶段 4 合起来：

```text
Tool Calling 查业务数据
RAG 查企业文档
LangGraph 编排流程
```

## 后续代码会怎么落地

虽然本节不写代码，但你要提前知道后面会落在哪些模块。

可能会在 `projects/ai-service` 中新增：

```text
app/schemas/rag.py
app/services/document_loader.py
app/services/text_splitter.py
app/services/embedding_service.py
app/services/vector_store_service.py
app/services/rag_service.py
app/routers/rag.py
```

也可能先在独立练习脚本里验证：

```text
scripts/rag_ingest_demo.py
scripts/rag_query_demo.py
```

后面我们会根据学习节奏决定。

但是分层思想不会变：

| 层 | 职责 |
| --- | --- |
| router | 接收入库请求和问答请求 |
| schema | 定义文档、chunk、检索结果、问答响应 |
| service | 执行 load/split/embed/store/retrieve/generate |
| core | 配置、日志、异常、trace |
| tests | fake embedding、fake vector store、service/router 测试 |

## 一个端到端例子

假设有一份文档：

```text
文件：售后政策.md

内容：
订单超过 72 小时仍未发货，客服应先查询订单状态和仓库处理记录；
如确认未出库，可创建投诉工单并标记为 high urgency。
```

### 入库阶段

```text
load:
读取 售后政策.md

clean:
去掉多余空行，统一文本格式

split:
生成 chunk:
"订单超过 72 小时仍未发货，客服应先查询订单状态和仓库处理记录；如确认未出库，可创建投诉工单并标记为 high urgency。"

embed:
生成 chunk 向量

store:
写入 Qdrant:
id: after_sales_policy_0001
vector: [...]
payload:
  content: ...
  source: 售后政策.md
  section: 物流异常处理
  doc_type: policy
```

### 问答阶段

用户问：

```text
订单三天没发货，客服应该怎么办？
```

系统执行：

```text
embed query:
把问题变成向量

retrieve:
检索到 after_sales_policy_0001

build prompt:
把检索 chunk 和用户问题组装给模型

generate:
模型回答：
根据售后政策，订单超过 72 小时未发货时，客服应先查询订单状态和仓库处理记录；
如果确认未出库，可以创建投诉工单并标记为 high urgency。

cite sources:
来源：售后政策.md / 物流异常处理
```

这就是一个最小但完整的 RAG 闭环。

## 本节暂时不学什么

本节不学：

```text
怎么安装 Qdrant
怎么调用 embedding API
怎么写入向量数据库
怎么设计 chunk size
怎么处理 PDF/docx
怎么写 RAG 接口
怎么做 rerank
怎么做混合检索
怎么接 Milvus
```

这些后面会逐节学习。

本节只解决：

```text
RAG 的工程流程到底是什么。
```

## 常见误区

### 误区 1：用户每次提问时都重新处理全部文档

不对。

文档入库和用户问答是两条流水线。

通常应该提前入库，用户提问时只检索。

### 误区 2：chunk 只要随便切就行

不对。

chunk 切分会直接影响检索质量。

切太大：

```text
检索不精准，prompt 太长
```

切太小：

```text
上下文不足，语义被切断
```

### 误区 3：检索到资料后，模型一定会正确回答

不对。

模型仍可能忽略资料、误解资料或编造补充内容。

所以 prompt 要明确：

```text
只根据资料回答
资料不足就拒答
必须带引用来源
```

### 误区 4：向量库只需要存 vector

不对。

只存 vector 不够。

还要存：

```text
原文 content
来源 source
章节 section
权限 access_level
文档类型 doc_type
更新时间 updated_at
```

否则无法引用、过滤、排查和更新。

### 误区 5：RAG 只要检索 top_k 就结束了

不对。

top_k 只是最基础检索。

后续还要考虑：

```text
score_threshold
metadata filter
hybrid search
rerank
权限过滤
评测集
引用正确性
```

## 本节练习

### 练习 1：写出两条 RAG 流水线

题目：

```text
请写出 RAG 的文档入库流水线和用户问答流水线。
```

参考答案：

```text
文档入库流水线：
load -> clean -> split -> embed -> store

用户问答流水线：
question -> embed query -> retrieve -> build prompt -> generate -> cite sources
```

### 练习 2：判断步骤属于哪条流水线

题目：

```text
判断下面步骤属于“文档入库”还是“用户问答”：

1. 读取售后政策.md
2. 把用户问题转成向量
3. 把文档切成 chunk
4. 从 Qdrant 检索 top_k
5. 把检索资料放入 prompt
6. 把 chunk 写入向量库
```

参考答案：

```text
文档入库：
1. 读取售后政策.md
3. 把文档切成 chunk
6. 把 chunk 写入向量库

用户问答：
2. 把用户问题转成向量
4. 从 Qdrant 检索 top_k
5. 把检索资料放入 prompt
```

### 练习 3：说明为什么要提前入库

题目：

```text
为什么不在用户每次提问时重新 load、split、embed 全部文档？
```

参考答案：

```text
因为文档读取、清洗、切分和 embedding 通常比较耗时，也会产生成本。用户问答需要低延迟，应该提前把文档处理好并存入向量库。用户提问时只需要把问题向量化并检索相关 chunk。
```

### 练习 4：指出每一步的失败后果

题目：

```text
如果 split 做得很差，会对最终 RAG 回答造成什么影响？
```

参考答案：

```text
如果 chunk 太大，检索结果可能不精准，模型收到很多无关内容；如果 chunk 太小，关键上下文可能被切断，模型拿不到完整依据。最终表现为回答不完整、引用不准确或检索不到真正相关资料。
```

### 练习 5：设计最小 RAG 返回结果

题目：

```text
一个 RAG 问答接口至少应该返回哪些内容？
```

参考答案：

```text
至少应该返回：

answer：模型基于资料生成的回答
sources：引用来源列表
trace_id：请求追踪编号

sources 里至少包含：
source：文档名或来源
section：章节
content_snippet：引用片段摘要
score：检索相似度分数
```

## 自测题

### 自测 1：RAG 为什么分成入库阶段和问答阶段？

参考答案：

```text
因为文档处理和用户问答的性质不同。文档入库是批量、耗时、可提前完成的后台工作；用户问答是实时、低延迟、需要权限过滤和生成答案的在线工作。
```

### 自测 2：load 的输出是什么？

参考答案：

```text
load 的输出通常是原始文本和基础来源信息，例如 content、source、title、file_path 等。
```

### 自测 3：store 时为什么不能只存向量？

参考答案：

```text
因为只存向量无法返回原文内容、引用来源、章节、权限信息和更新时间。RAG 需要同时保存 vector、content 和 metadata/payload。
```

### 自测 4：retrieve 阶段常见的三个参数是什么？

参考答案：

```text
top_k：返回前几个最相似结果。
score_threshold：过滤低相似度结果。
filter：根据 metadata/payload 做文档类型、来源或权限过滤。
```

### 自测 5：build prompt 阶段为什么重要？

参考答案：

```text
因为检索结果只是资料，模型还需要明确规则：只能根据资料回答、资料不足要拒答、回答要带引用来源。prompt 设计不好，模型可能忽略资料或编造内容。
```

### 自测 6：cite sources 为什么不应该靠模型凭空生成？

参考答案：

```text
引用来源应该来自检索结果的 metadata，而不是让模型自己编。模型可能编造不存在的文件名或章节。后端应该保存并返回真实 source、section、chunk_id 等信息。
```

### 自测 7：阶段 2 的模型调用能力在 RAG 哪一步复用？

参考答案：

```text
主要在 generate 阶段复用。检索到 chunk 并组装 prompt 后，仍然需要调用 LLM 生成最终回答，也需要复用 timeout、错误映射、日志、fake client 测试等能力。
```

## 本节总结

这一节你要记住：

```text
RAG = 文档入库流水线 + 用户问答流水线
```

文档入库：

```text
load -> clean -> split -> embed -> store
```

用户问答：

```text
question -> embed query -> retrieve -> build prompt -> generate -> cite sources
```

RAG 的难点不是某一个 API。

真正难点是：

```text
每一步的输入输出要清楚
每一步的质量会影响最终回答
每一步都要能测试、能排查、能解释
```

下一节会继续补基础概念：

```text
阶段 4 第 3 节：文档、知识库、chunk、metadata 是什么
```

下一节会把 RAG 里最容易混淆的几个数据单位讲透，为后面真正写文档处理代码做准备。

