# 阶段 4 第 5 节：向量相似度：为什么能用向量找相似内容

> 本节结论：embedding 把文本变成向量以后，RAG 还需要用“向量相似度”判断用户问题和哪些 chunk 更接近。向量相似度不是在判断答案一定正确，而是在给检索阶段提供一个相关性排序。`top_k` 负责取最相似的前几个结果，`score_threshold` 负责过滤太不相关的结果。

## 生成笔记前的教学复核

这一节仍然以理解为主，不接 Qdrant。

这一节必须讲清：

```text
1. 什么是向量相似度。
2. 为什么向量距离近，语义可能相近。
3. similarity 和 distance 的区别。
4. cosine similarity 是什么。
5. dot product 是什么。
6. top_k 是怎么来的。
7. score_threshold 为什么重要。
8. 为什么相似度高不等于答案一定正确。
9. 这些概念后面怎么对应到 Qdrant / Milvus 检索。
```

## 本节一句话定位

第 4 节讲了：

```text
文本可以通过 embedding 变成向量。
```

第 5 节讲：

```text
向量之间怎么比较“像不像”。
```

RAG 检索的核心就是：

```text
把用户问题向量和知识库 chunk 向量做相似度比较。
```

## 先给结论

RAG 检索可以简化成一句话：

```text
找出和用户问题向量最相似的 chunk 向量。
```

例如：

```text
用户问题：
订单三天没发货怎么办？

query vector:
[0.10, 0.80, 0.20]
```

知识库里有多个 chunk：

```text
chunk A：订单超过 72 小时未发货，可以创建投诉工单。
chunk B：用户收到商品 7 天内可以申请退款。
chunk C：登录密码可以在个人中心修改。
```

它们也都有向量：

```text
A vector: [0.12, 0.78, 0.21]
B vector: [0.45, 0.20, 0.70]
C vector: [0.90, 0.05, 0.10]
```

检索系统会比较：

```text
query vector 和 A vector 像不像
query vector 和 B vector 像不像
query vector 和 C vector 像不像
```

如果 A 最像，就返回 A。

这就是向量相似度在 RAG 里的作用。

## 什么是向量

向量可以先理解成：

```text
一组有顺序的数字
```

例如：

```text
[0.10, 0.80, 0.20]
```

这是一个 3 维向量。

真实 embedding 向量可能是几百维或几千维。

但理解时可以先用 2 维或 3 维。

你可以把向量想象成空间里的一个点。

例如二维向量：

```text
[1, 2]
```

表示平面上的一个点。

三维向量：

```text
[1, 2, 3]
```

表示三维空间里的一个点。

高维向量我们画不出来，但数学上可以比较距离和方向。

## 为什么向量能表示语义

这件事来自 embedding 模型。

embedding 模型会把文本映射到向量空间里。

它希望做到：

```text
语义相近的文本 -> 向量更接近
语义不同的文本 -> 向量更远
```

比如：

```text
订单三天没发货
订单超过 72 小时未发货
物流一直没更新
```

这些文本都和物流/发货异常相关，向量可能比较接近。

而：

```text
如何修改登录密码
员工请假流程
数据库连接池配置
```

它们和发货异常关系很远，向量通常更远。

注意这里说的是：

```text
可能更接近
通常更远
```

不是绝对保证。

embedding 是统计和模型学习结果，不是严格逻辑规则。

## similarity 和 distance 的区别

这两个词很重要。

### similarity：相似度

similarity 表示：

```text
两个向量有多像
```

通常：

```text
值越大，越相似
```

例如：

```text
similarity = 0.92
```

通常表示比较相似。

### distance：距离

distance 表示：

```text
两个向量有多远
```

通常：

```text
值越小，越接近
```

例如：

```text
distance = 0.08
```

通常表示很接近。

### 两者的直觉区别

| 概念 | 含义 | 越大越好吗 |
| --- | --- | --- |
| similarity | 相似度 | 通常越大越相似 |
| distance | 距离 | 通常越小越相似 |

不同向量数据库和不同度量方式，返回字段可能叫：

```text
score
distance
similarity
```

所以后面使用 Qdrant 或 Milvus 时要看清：

```text
这个分数到底是越大越好，还是越小越好。
```

## cosine similarity 是什么

cosine similarity 中文常叫：

```text
余弦相似度
```

它比较的是：

```text
两个向量方向是否接近。
```

不是主要看长度，而是看方向。

### 用方向理解

假设有两个向量：

```text
A: [1, 1]
B: [2, 2]
```

它们长度不同。

但方向一样。

cosine similarity 会认为它们非常相似。

再看：

```text
A: [1, 0]
B: [0, 1]
```

一个朝右，一个朝上。

方向相差很大。

cosine similarity 会认为它们不相似。

### 为什么文本向量常用 cosine

因为很多场景里，我们更关心：

```text
语义方向是否接近
```

而不是向量长度本身。

例如两段文本长短不同，但主题一致，方向可能接近。

这就是 cosine similarity 常用于文本 embedding 的原因之一。

### cosine 值的大致理解

常见理解：

```text
接近 1：方向非常接近，比较相似
接近 0：方向差异较大
接近 -1：方向相反
```

但在实际向量库里，不同模型、不同归一化方式、不同数据库返回格式，分数含义会有差异。

所以不要死记：

```text
0.8 一定好
0.5 一定差
```

要结合数据和评测调试。

## dot product 是什么

dot product 中文叫：

```text
点积
```

它也是一种向量相似度计算方式。

直觉上可以理解为：

```text
两个向量方向越一致，点积通常越大。
```

如果向量做过归一化，dot product 和 cosine similarity 的效果会很接近。

### 什么是归一化

归一化可以先粗略理解为：

```text
把向量长度调整到同一标准。
```

比如把所有向量都变成长度为 1。

这样比较时，长度影响减少，方向影响更明显。

### dot product 的注意点

dot product 可能受向量长度影响。

所以它适不适合，要看：

```text
embedding 模型输出是否已归一化
向量数据库使用什么 distance metric
业务检索效果如何
```

后面用具体向量库时，我们会按它的文档和实际效果配置。

## Euclidean distance 是什么

Euclidean distance 中文叫：

```text
欧氏距离
```

它比较的是：

```text
两个点在空间里的直线距离。
```

二维平面里很直观：

```text
A 点在 [0, 0]
B 点在 [3, 4]
距离是 5
```

在高维向量里也可以计算距离。

直觉是：

```text
距离越小，两个向量越接近。
```

但文本 embedding 场景中，cosine 和 dot product 更常见。

你现在不需要深入数学推导。

只要知道：

```text
向量相似度有多种计算方式。
不同方式的 score 含义不完全一样。
使用向量库时要知道自己选了哪一种。
```

## top_k 是怎么来的

top_k 是 RAG 检索里非常常见的参数。

它表示：

```text
返回相似度最高的前 k 个 chunk。
```

例如：

```text
top_k = 3
```

表示返回最相似的 3 个结果。

### 举个例子

用户问题：

```text
订单三天没发货怎么办？
```

向量库里有 5 个 chunk。

相似度分数：

```text
chunk A: 0.91 物流异常处理
chunk B: 0.76 投诉升级规则
chunk C: 0.42 退款时效
chunk D: 0.20 修改密码
chunk E: 0.12 数据库连接池
```

如果：

```text
top_k = 2
```

返回：

```text
A 和 B
```

如果：

```text
top_k = 4
```

返回：

```text
A、B、C、D
```

但 D 明显不相关。

所以 top_k 不是越大越好。

### top_k 太小的问题

如果 top_k 太小：

```text
可能漏掉有用资料
答案缺上下文
多角度问题回答不完整
```

### top_k 太大的问题

如果 top_k 太大：

```text
引入无关资料
prompt 变长
token 成本上升
模型注意力分散
可能把错误资料也喂给模型
```

所以 top_k 要调。

后面会通过测试和评测来决定。

## score_threshold 为什么重要

score_threshold 表示：

```text
相似度低于某个阈值的结果不要。
```

例如：

```text
score_threshold = 0.70
```

如果结果是：

```text
chunk A: 0.91
chunk B: 0.76
chunk C: 0.42
chunk D: 0.20
```

最终只保留：

```text
A 和 B
```

### 为什么需要 threshold

因为 top_k 总会返回前 k 个结果。

即使所有结果都很差，top_k 也可能硬返回几个最不差的。

例如用户问：

```text
公司附近哪家火锅好吃？
```

知识库里只有售后政策。

如果只用 top_k，向量库可能仍然返回：

```text
退款规则
物流异常处理
投诉升级
```

但这些都不该用于回答火锅问题。

score_threshold 可以帮助系统判断：

```text
没有足够相关的资料。
```

然后回答：

```text
当前知识库没有足够资料回答这个问题。
```

### threshold 也不能乱设

threshold 太高：

```text
容易拒答
明明有资料也被过滤掉
```

threshold 太低：

```text
容易引入无关资料
模型可能基于不相关资料乱答
```

所以 threshold 也要通过数据调试。

## 相似度高不等于答案正确

这是非常重要的一点。

向量相似度只表示：

```text
这个 chunk 和用户问题在语义上比较接近。
```

它不保证：

```text
这个 chunk 一定能回答问题
这个 chunk 一定是最新版本
这个 chunk 当前用户有权限看
这个 chunk 没有被错误切分
这个 chunk 没有和其他 chunk 冲突
模型一定会正确使用它
```

例如：

```text
用户问：超过 72 小时未发货可以自动赔付吗？
```

检索到：

```text
订单超过 72 小时未发货，可创建投诉工单。
```

相似度很高。

但这个 chunk 只能说明：

```text
可以创建投诉工单
```

不能说明：

```text
可以自动赔付
```

如果模型过度发挥，就会答错。

所以 RAG prompt 要要求：

```text
资料没有说的，不要补充。
```

## 相似度分数要和 metadata 一起看

一个检索结果不只看 score。

还要看：

```text
source
section
doc_type
access_level
version
updated_at
```

例如：

```text
chunk A: score 0.91, version 2024
chunk B: score 0.88, version 2026
```

如果政策已更新，B 可能更值得使用。

又比如：

```text
chunk A: score 0.93, access_level manager_only
chunk B: score 0.82, access_level internal
```

如果当前用户不是主管，A 不能给模型看。

这就是为什么第 3 节强调 metadata。

RAG 检索不是只看：

```text
相似度分数
```

还要看：

```text
权限、版本、类型、来源、业务适用性
```

## score 的实际含义要看向量库

不同系统返回的 score 可能不同。

例如：

```text
有的 score 越大越相似。
有的 distance 越小越相似。
有的返回 cosine similarity。
有的返回距离值。
```

所以接入向量库时，不要只看字段名。

要确认：

```text
当前 metric 是什么
返回值越大越好还是越小越好
阈值应该怎么设置
```

这在后面学 Qdrant 和 Milvus 时会继续讲。

## 向量相似度在 RAG 流程里的位置

回到 RAG 的两条流水线。

文档入库阶段：

```text
load -> clean -> split -> embed -> store
```

这里会把 chunk vector 存起来。

用户问答阶段：

```text
question -> embed query -> retrieve -> build prompt -> generate -> cite sources
```

向量相似度发生在：

```text
retrieve
```

具体是：

```text
query vector
vs
chunk vectors
```

然后得到：

```text
相似度排序结果
```

再经过：

```text
top_k
score_threshold
metadata filter
```

最终得到候选 chunk。

## 一个完整检索例子

知识库 chunk：

```text
A：订单超过 72 小时仍未发货，可创建投诉工单。
B：用户收到商品 7 天内可以申请退款。
C：登录密码可以在个人中心修改。
D：接口调用失败时请检查 trace_id。
```

用户问题：

```text
包裹三天还没发出，客服应该怎么处理？
```

向量检索结果：

```text
A score=0.92
B score=0.55
D score=0.31
C score=0.18
```

如果配置：

```text
top_k = 3
score_threshold = 0.60
```

先取 top 3：

```text
A、B、D
```

再按阈值过滤：

```text
A
```

最终只有 A 会进入 prompt。

模型基于 A 回答。

这就是：

```text
top_k + score_threshold
```

一起工作的方式。

## 向量相似度和业务判断的边界

向量相似度只回答：

```text
哪些文本语义上像这个问题？
```

它不回答：

```text
用户有没有权限？
当前政策是否生效？
订单是否真的三天没发货？
是否应该创建工单？
是否需要主管审批？
```

这些问题要交给：

```text
metadata filter
业务 API
Tool Calling
后端规则
用户确认
```

所以不要把向量相似度当成业务判断。

它只是检索排序工具。

## 本节暂时不学什么

本节不学：

```text
cosine similarity 的完整公式推导
Qdrant distance 配置
Milvus index 参数
HNSW 索引
向量归一化代码
真实 top_k 检索代码
评测集调参
```

这些后面会学。

本节只要先理解：

```text
向量之间可以比较相似度。
相似度用于排序和筛选候选 chunk。
相似不等于正确。
```

## 常见误区

### 误区 1：score 越高，答案就一定越对

不对。

score 高只说明文本相似。

答案是否正确还要看：

```text
资料是否足够
资料是否最新
用户是否有权限
模型是否正确使用资料
```

### 误区 2：top_k 越大越好

不对。

top_k 太大会带来无关内容和更高 token 成本。

它需要根据问题类型、chunk 质量和模型上下文调试。

### 误区 3：threshold 越高越安全

不一定。

threshold 太高会导致系统经常拒答。

threshold 太低会导致无关资料进入 prompt。

需要评测调参。

### 误区 4：向量检索可以替代权限过滤

不能。

向量检索只看语义。

权限必须由 metadata filter 和后端逻辑控制。

### 误区 5：所有向量库 score 含义都一样

不对。

不同向量库、不同 metric、不同配置下，score/distance 的含义可能不同。

接入时必须看文档和测试结果。

## 本节练习

### 练习 1：解释 similarity 和 distance

题目：

```text
用自己的话解释 similarity 和 distance 的区别。
```

参考答案：

```text
similarity 表示两个向量有多像，通常值越大越相似。
distance 表示两个向量有多远，通常值越小越接近。
使用向量库时要确认返回值是 similarity 还是 distance。
```

### 练习 2：判断 top_k 结果

题目：

```text
检索结果如下：

A score=0.91
B score=0.80
C score=0.62
D score=0.30

如果 top_k=2，返回哪些？
```

参考答案：

```text
返回 A 和 B。
```

### 练习 3：加入 score_threshold

题目：

```text
检索结果如下：

A score=0.91
B score=0.80
C score=0.62
D score=0.30

如果 top_k=3，score_threshold=0.70，最终保留哪些？
```

参考答案：

```text
top_k=3 先取 A、B、C。
score_threshold=0.70 再过滤掉 C。
最终保留 A 和 B。
```

### 练习 4：判断相似度高是否足够

题目：

```text
用户问“超过 72 小时未发货可以自动赔付吗？”

检索到 chunk：
“订单超过 72 小时未发货，可创建投诉工单。”

score=0.93。

模型能不能回答“可以自动赔付”？为什么？
```

参考答案：

```text
不能。这个 chunk 只说明可以创建投诉工单，没有说明可以自动赔付。相似度高只表示资料和问题相关，不表示资料支持用户问题里的每个结论。
```

### 练习 5：权限过滤

题目：

```text
检索结果：

A score=0.94, access_level=manager_only
B score=0.82, access_level=internal

当前用户只是普通客服。应该把哪个 chunk 给模型？为什么？
```

参考答案：

```text
应该只把 B 给模型。A 虽然相似度更高，但用户无权访问。权限过滤应该优先于把资料交给模型。
```

## 自测题

### 自测 1：向量相似度在 RAG 哪一步使用？

参考答案：

```text
在 retrieve 检索阶段使用。系统用 query vector 和 chunk vectors 做相似度比较，找到最相关的 chunk。
```

### 自测 2：cosine similarity 主要比较什么？

参考答案：

```text
主要比较两个向量的方向是否接近。方向越接近，余弦相似度通常越高。
```

### 自测 3：top_k 的作用是什么？

参考答案：

```text
top_k 用来控制返回相似度最高的前 k 个 chunk。它决定最多给模型多少条检索资料。
```

### 自测 4：score_threshold 的作用是什么？

参考答案：

```text
score_threshold 用来过滤低相似度结果，避免无关资料进入 prompt。它也能帮助系统在没有足够相关资料时拒答。
```

### 自测 5：为什么相似度高不等于答案正确？

参考答案：

```text
因为相似度只表示文本相关，不保证资料完整、最新、有权限或能支持问题里的全部结论。模型仍然可能误用资料或补充资料中没有的内容。
```

### 自测 6：score 是越大越好还是越小越好？

参考答案：

```text
不一定。要看向量库返回的是 similarity 还是 distance，以及当前使用的 metric。similarity 通常越大越相似，distance 通常越小越接近。
```

### 自测 7：向量相似度能不能替代业务 API 查询？

参考答案：

```text
不能。向量相似度只能找语义相关的文档 chunk，不能查询实时订单状态、判断真实库存、创建工单或执行退款。这些仍然要通过 Tool Calling 调业务 API。
```

## 本节总结

这一节你要记住：

```text
embedding 让文本变成向量。
向量相似度让系统能比较 query 和 chunk 谁更接近。
top_k 决定取前几个。
score_threshold 决定低相关结果要不要丢掉。
```

同时必须记住边界：

```text
相似度高不等于答案正确。
向量检索不等于业务判断。
权限、版本、引用、评测仍然要靠后端工程设计。
```

下一节学习：

```text
阶段 4 第 6 节：向量数据库是什么，为什么先选 Qdrant
```

下一节会从“向量怎么比较”进入“向量应该存在哪里、为什么普通数据库不够用、为什么我们先用 Qdrant”。

