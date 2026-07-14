# 阶段 4 第 4 节：embedding 是什么：文本怎么变成向量

> 本节结论：embedding 是把文本转换成数字向量的技术。RAG 不是直接拿文字去向量数据库里搜，而是先把 chunk 和用户问题都变成向量，再用向量相似度找语义接近的内容。embedding 让系统能理解“订单三天没发货”和“超过 72 小时未发货”语义相近，但它不是万能理解，也不能替代权限、引用、评测和业务校验。

## 生成笔记前的教学复核

这一节仍然以理解为主，不真实调用 embedding API。

这一节必须讲清：

```text
1. embedding 是什么。
2. 文本为什么可以变成一组数字。
3. embedding 和关键词匹配有什么区别。
4. 为什么语义相近的文本向量更接近。
5. chunk embedding 和 query embedding 分别是什么。
6. 为什么文档和问题最好使用同一个 embedding 模型。
7. embedding 维度是什么意思。
8. embedding 在 RAG 流程里负责哪一步。
9. embedding 不能解决什么问题。
```

## 本节一句话定位

前 3 节我们知道：

```text
RAG 要把 document 切成 chunk。
chunk 要写入向量数据库。
用户问题要去检索相关 chunk。
```

第 4 节要回答：

```text
为什么文本能被“相似度搜索”？
```

答案就是：

```text
embedding 把文本变成向量。
```

## 先给结论

embedding 是：

```text
把文本、图片、音频等内容转换成一组数字向量的表示方法。
```

在当前 RAG 阶段，我们只关心文本 embedding。

例如：

```text
文本：
订单超过 72 小时未发货可以升级投诉。

embedding 向量：
[0.012, -0.231, 0.887, 0.104, ...]
```

真实 embedding 向量通常有很多维，不是只有 4 个数字。

我们不需要手动理解每个数字的含义。

只要理解一句话：

```text
语义相近的文本，embedding 向量在空间里通常更接近。
```

例如：

```text
订单三天没发货怎么办？
```

和：

```text
订单超过 72 小时未发货可以升级投诉。
```

字面不完全一样，但语义接近。

embedding 的目标就是让这种语义接近在数字向量空间里体现出来。

## 为什么 RAG 需要 embedding

RAG 的关键动作是：

```text
根据用户问题找到相关文档 chunk。
```

如果只靠关键词匹配，系统可能只找包含相同词的文本。

但用户提问和文档写法经常不一样。

例如用户说：

```text
包裹一直没动静，能投诉吗？
```

文档里可能写：

```text
物流状态超过 72 小时未更新时，可创建物流异常工单。
```

两句话关键词差异很大：

```text
包裹 vs 物流状态
没动静 vs 未更新
投诉 vs 异常工单
```

但语义很接近。

embedding 就是为了解决：

```text
文字表面不同，但意思相近
```

这个问题。

## embedding 和关键词匹配的区别

### 关键词匹配

关键词匹配看的是：

```text
有没有出现某些词
```

例如搜索：

```text
未发货
```

它容易找到包含“未发货”的文档。

但如果文档写的是：

```text
商品尚未出库
```

关键词匹配可能找不到。

### embedding 检索

embedding 检索看的是：

```text
语义是否接近
```

它可能知道：

```text
未发货
尚未出库
没有发出
物流无更新
```

在某些上下文里可能语义相关。

### 简单对比

| 维度 | 关键词匹配 | embedding 检索 |
| --- | --- | --- |
| 核心依据 | 字面词是否匹配 | 语义是否相近 |
| 擅长 | 精确词、编号、专有名词 | 同义表达、自然语言问题 |
| 不擅长 | 同义改写 | 精确过滤和强规则 |
| 例子 | 搜 `A1001` | 搜“订单三天没发货怎么办” |

注意：

```text
embedding 不一定替代关键词匹配。
```

后面会学混合检索：

```text
关键词检索 + 向量检索
```

因为两者各有优势。

## 文本怎么变成数字

这个过程由 embedding 模型完成。

你可以把 embedding 模型想成一个函数：

```text
embedding_model(text) -> vector
```

例如：

```text
embedding_model("订单超过 72 小时未发货")
-> [0.012, -0.231, 0.887, ...]
```

这个函数不是我们手写规则。

它是一个训练好的模型。

它在训练过程中学到了大量文本之间的语义关系，所以能把文本映射到一个向量空间。

### 向量空间是什么

为了先理解，可以想象一个二维平面。

```text
横轴：和订单物流相关程度
纵轴：和退款规则相关程度
```

那么：

```text
订单三天没发货
物流超过 72 小时未更新
包裹一直没有发出
```

可能会落在比较接近的位置。

而：

```text
如何修改登录密码
员工请假流程
数据库连接池配置
```

会落在较远的位置。

真实 embedding 不是二维，而是高维。

但直觉一样：

```text
语义相近 -> 向量距离近
语义不同 -> 向量距离远
```

## embedding 维度是什么意思

embedding 向量是一组数字。

这组数字有多少个，就叫多少维。

例如：

```text
[0.1, 0.2, -0.3]
```

这是 3 维向量。

真实 embedding 模型可能输出：

```text
几百维
一千多维
几千维
```

维度越高，不代表一定越好。

它会影响：

```text
向量库 collection 配置
存储空间
检索速度
索引成本
模型成本
```

非常重要的一点：

```text
同一个向量库 collection 里的向量维度必须一致。
```

如果 collection 创建时要求 1536 维，你不能写入 1024 维向量。

所以后面选择 embedding 模型时，要记录：

```text
模型名
输出维度
适合语言
成本
是否支持批量
```

## chunk embedding 是什么

chunk embedding 是：

```text
把文档 chunk 转成向量。
```

它发生在文档入库阶段。

流程是：

```text
document
-> split 成 chunk
-> 对每个 chunk 调 embedding
-> 得到 chunk vector
-> 写入向量数据库
```

例如：

```text
chunk:
订单超过 72 小时仍未发货，客服应先查询订单状态...

chunk embedding:
[0.012, -0.231, 0.887, ...]
```

向量库里存的就是：

```text
chunk_id
chunk vector
chunk content
metadata
```

## query embedding 是什么

query embedding 是：

```text
把用户问题转成向量。
```

它发生在用户问答阶段。

流程是：

```text
用户问题
-> 调 embedding
-> 得到 query vector
-> 去向量库找相似 chunk vector
```

例如：

```text
query:
订单三天没发货怎么办？

query embedding:
[0.018, -0.220, 0.841, ...]
```

如果 query vector 和某个 chunk vector 很接近，就说明：

```text
这个 chunk 可能和用户问题相关。
```

## 文档和问题为什么最好用同一个 embedding 模型

RAG 里通常有两类文本要 embedding：

```text
文档 chunk
用户问题 query
```

这两者最好使用同一个 embedding 模型。

原因是：

```text
同一个模型输出的向量在同一个语义空间里。
```

如果文档用模型 A，问题用模型 B，就可能出现：

```text
向量维度不同
相似度不可比
语义空间不一致
检索结果不稳定
```

类比一下：

```text
文档向量用“米”做单位
问题向量用“斤”做单位
```

它们就很难直接比较。

所以真实项目里要统一配置：

```text
EMBEDDING_MODEL
EMBEDDING_DIMENSION
```

并保证：

```text
入库时和检索时使用同一套配置。
```

## embedding 在 RAG 流程里的位置

回到第 2 节的两条流水线。

### 文档入库阶段

```text
load -> clean -> split -> embed -> store
```

这里的 embed 是：

```text
chunk embedding
```

作用：

```text
把每个 chunk 变成向量，方便后续检索。
```

### 用户问答阶段

```text
question -> embed query -> retrieve -> build prompt -> generate -> cite sources
```

这里的 embed query 是：

```text
query embedding
```

作用：

```text
把用户问题变成向量，拿去和 chunk vector 做相似度搜索。
```

所以 embedding 在 RAG 里出现两次：

```text
入库时：chunk -> vector
查询时：question -> vector
```

## embedding 和 vector store 的关系

embedding 模型负责：

```text
把文本变成向量
```

vector store 负责：

```text
存向量
按相似度搜索向量
返回对应的 content 和 metadata
```

它们不是一个东西。

| 组件 | 职责 |
| --- | --- |
| embedding model | 文本 -> 向量 |
| vector store | 存向量并搜索相似向量 |
| LLM | 基于检索资料生成答案 |

例如：

```text
OpenAI / DashScope / 本地模型
-> 可以做 embedding

Qdrant / Milvus
-> 可以做 vector store
```

RAG 至少需要：

```text
embedding model + vector store + LLM
```

## embedding 检索的直观例子

假设知识库有 4 个 chunk：

```text
A：订单超过 72 小时仍未发货，可创建投诉工单。
B：用户收到商品 7 天内可以申请退款。
C：登录密码可以在个人中心修改。
D：接口调用失败时请检查 trace_id 和错误码。
```

用户问：

```text
包裹三天还没发出，怎么处理？
```

关键词匹配可能找不到 A，因为问题里没有“72 小时”“未发货”“投诉工单”这些词。

embedding 检索可能返回：

```text
A：订单超过 72 小时仍未发货，可创建投诉工单。
```

因为：

```text
包裹三天还没发出
```

和：

```text
订单超过 72 小时仍未发货
```

语义接近。

这就是 embedding 的价值。

## embedding 的局限性

embedding 很重要，但它不是万能的。

### 1. 不擅长精确编号

例如：

```text
A1001
A1007
B1001
```

这些编号语义上可能没什么意义。

embedding 不一定比关键词匹配更可靠。

所以订单号、用户 ID、SKU、接口名这类信息，往往需要：

```text
关键词检索
metadata filter
Tool Calling
结构化查询
```

### 2. 不保证结果一定正确

embedding 找的是相似内容，不代表内容一定能回答问题。

可能出现：

```text
相似但不适用
相似但版本过旧
相似但用户无权限
相似但缺少关键上下文
```

所以还需要：

```text
score_threshold
metadata filter
rerank
引用来源
评测
```

### 3. 不理解业务权限

embedding 只负责语义相似度。

它不知道：

```text
当前用户能不能看这份文档
这个规则是否适用于这个地区
这个文档是否已经过期
```

这些要靠 metadata 和后端规则。

### 4. 可能受文档质量影响

如果 chunk 内容很乱：

```text
页眉页脚多
乱码多
标题丢失
上下文被切断
```

embedding 出来的向量质量也会受影响。

所以 embedding 之前的：

```text
clean
split
metadata 设计
```

同样重要。

## embedding 和 LLM 的区别

这两个也容易混。

LLM 负责生成文本。

embedding model 负责生成向量。

对比：

| 组件 | 输入 | 输出 | 用途 |
| --- | --- | --- | --- |
| LLM | prompt/messages | 自然语言回答或结构化输出 | 回答、总结、推理、抽取 |
| embedding model | 文本 | 数字向量 | 语义检索、相似度比较 |

例如：

```text
LLM:
"请根据资料回答用户问题"
-> "根据售后政策，超过 72 小时未发货..."

embedding model:
"订单超过 72 小时未发货"
-> [0.012, -0.231, 0.887, ...]
```

RAG 里两者配合：

```text
embedding model 找资料
LLM 基于资料回答
```

## embedding 和 token 的关系

embedding 模型处理文本时，也会受到输入长度限制。

文本太长会带来问题：

```text
超过 embedding 模型输入限制
成本更高
语义被稀释
检索粒度太粗
```

这也是为什么要先切 chunk。

如果把整本手册拿去 embedding，效果通常不好。

更合理的是：

```text
先 split 成 chunk
再对每个 chunk 生成 embedding
```

## 什么时候生成 embedding

### 文档入库时生成

文档 chunk 的 embedding 通常在入库时生成。

这意味着：

```text
一个 chunk 生成一次 embedding
然后存入向量库
```

除非文档更新或换 embedding 模型，否则不需要每次用户提问都重新生成文档 embedding。

### 用户提问时生成

用户问题的 embedding 在查询时生成。

因为每次用户问题不同。

流程是：

```text
用户问题
-> query embedding
-> 向量搜索
```

## 如果更换 embedding 模型会怎样

这是后面会遇到的工程问题。

如果你原来用模型 A 给所有文档生成 embedding。

后来换成模型 B。

可能会出现：

```text
向量维度不同
向量空间不同
旧向量和新 query 不可比
检索结果变差
```

通常需要：

```text
重新给文档生成 embedding
重建向量索引
记录 embedding_model 和 embedding_dimension
```

所以真实项目里，embedding 配置要慎重。

## 本节暂时不学什么

本节不学：

```text
具体调用 embedding API
如何批量生成 embedding
embedding 价格和成本计算
Qdrant collection 维度怎么建
向量相似度公式
混合检索
rerank
embedding 模型选型细节
```

这些后面会学。

本节只解决：

```text
embedding 是什么，以及它为什么能让 RAG 做语义检索。
```

## 常见误区

### 误区 1：embedding 是把文本翻译成某种编码

不准确。

普通编码更像：

```text
字符 -> 数字表示
```

embedding 更像：

```text
文本语义 -> 向量表示
```

它不是简单编码字符，而是表示语义。

### 误区 2：embedding 向量里的每个数字都能解释

通常不能。

我们不会说：

```text
第 17 维代表物流
第 83 维代表退款
```

真实向量的每个维度通常不是这样直观解释的。

我们关注整体向量之间的距离和相似度。

### 误区 3：embedding 能完全理解用户问题

不能。

embedding 主要做相似度匹配。

它不能替代：

```text
业务规则判断
权限控制
精确数据库查询
用户确认
模型最终回答
```

### 误区 4：embedding 越大越好

不一定。

更高维度可能带来：

```text
更多存储
更慢检索
更高成本
更复杂索引
```

要结合效果、成本和系统规模选择。

### 误区 5：文档和问题可以随便用不同 embedding 模型

不应该。

文档 chunk 和用户 query 最好使用同一个 embedding 模型。

否则向量空间不一致，检索结果可能不可靠。

## 本节练习

### 练习 1：用一句话解释 embedding

题目：

```text
不用“高维向量空间”这种术语，用自己的话解释 embedding 是什么。
```

参考答案：

```text
embedding 就是把一段文本变成一组数字，让计算机可以比较两段文本在意思上是不是接近。
```

### 练习 2：判断更适合关键词还是 embedding

题目：

```text
下面场景更适合关键词匹配，还是 embedding 检索？

1. 查订单号 A1001
2. 查“订单三天没发货怎么办”
3. 查接口名 create_ticket
4. 查“包裹一直没动静能不能投诉”
5. 查 SKU-7788
```

参考答案：

```text
更适合关键词/精确匹配：
1. 订单号 A1001
3. 接口名 create_ticket
5. SKU-7788

更适合 embedding 检索：
2. 订单三天没发货怎么办
4. 包裹一直没动静能不能投诉

真实系统里也可以混合使用。
```

### 练习 3：区分 chunk embedding 和 query embedding

题目：

```text
chunk embedding 和 query embedding 分别在什么时候生成？
```

参考答案：

```text
chunk embedding 在文档入库阶段生成，把每个文档 chunk 转成向量并存入向量库。

query embedding 在用户问答阶段生成，把用户问题转成向量，再去向量库检索相似 chunk。
```

### 练习 4：解释为什么要用同一个 embedding 模型

题目：

```text
为什么文档 chunk 和用户 query 最好用同一个 embedding 模型？
```

参考答案：

```text
因为同一个 embedding 模型输出的向量在同一个语义空间里，才能比较相似度。如果文档和问题使用不同模型，可能维度不同、语义空间不同，检索结果就不可靠。
```

### 练习 5：指出 embedding 的局限

题目：

```text
embedding 能不能可靠处理订单号、用户权限和文档版本？为什么？
```

参考答案：

```text
不能完全可靠。订单号更适合精确匹配或业务 API 查询；用户权限和文档版本属于业务规则和 metadata 过滤，不是语义相似度问题。embedding 只负责帮助找到语义相近内容。
```

## 自测题

### 自测 1：embedding 在 RAG 的哪两个阶段出现？

参考答案：

```text
文档入库阶段：对 chunk 生成 embedding。
用户问答阶段：对用户问题生成 query embedding。
```

### 自测 2：embedding model 和 LLM 的区别是什么？

参考答案：

```text
embedding model 把文本转换成数字向量，用于相似度检索。LLM 根据 prompt/messages 生成自然语言或结构化输出，用于回答、总结、抽取和推理。
```

### 自测 3：embedding 维度是什么意思？

参考答案：

```text
embedding 维度就是向量里数字的个数。例如 3 个数字是 3 维向量。真实 embedding 可能有几百到几千维。同一个向量库 collection 里的向量维度必须一致。
```

### 自测 4：为什么 embedding 能找到“超过 72 小时未发货”和“三天没发货”的关系？

参考答案：

```text
因为 embedding 模型会把语义相近的文本映射到相近的向量位置。这两句话字面不同，但含义接近，所以向量相似度可能较高。
```

### 自测 5：embedding 能不能保证 RAG 答案一定正确？

参考答案：

```text
不能。embedding 只能帮助检索语义相近内容，不能保证检索结果适用、最新、有权限或足够完整。还需要 metadata filter、score_threshold、rerank、引用来源、prompt 约束和评测。
```

### 自测 6：更换 embedding 模型时为什么可能要重建索引？

参考答案：

```text
因为不同 embedding 模型可能输出不同维度和不同语义空间的向量。旧 chunk 向量和新 query 向量可能不可比，所以通常需要重新生成文档 embedding 并重建向量索引。
```

### 自测 7：embedding 为什么不能替代 Tool Calling？

参考答案：

```text
embedding 负责语义检索文档，不能查询实时订单状态、创建工单或执行业务操作。实时业务数据和写操作仍然需要 Tool Calling 调后端 API，并经过权限、确认和幂等控制。
```

## 本节总结

这一节你要记住：

```text
embedding = 文本 -> 向量
```

RAG 里有两类 embedding：

```text
chunk embedding：文档入库时生成
query embedding：用户提问时生成
```

embedding 的价值是：

```text
让系统能按语义相似度检索相关 chunk
```

embedding 的边界是：

```text
它只解决语义相似，不解决权限、版本、业务规则、精确编号和答案可靠性。
```

下一节学习：

```text
阶段 4 第 5 节：向量相似度：为什么能用向量找相似内容
```

下一节会继续解释检索背后的核心：向量之间到底怎么比较“近”和“远”，为什么 top_k 和 score_threshold 会影响 RAG 效果。

