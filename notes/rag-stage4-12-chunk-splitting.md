# 阶段 4 第 12 节：chunk 切分策略：大小、重叠、标题、段落

> 本节结论：chunk 切分是 RAG 检索质量的核心环节之一。文档不能整篇直接 embedding，也不能随便按固定字符硬切。本节新增 `app/rag/splitters.py`，实现一个“段落优先、标题感知”的基础 splitter：把 `RagDocument` 切成 `RagChunk`，保留来源 metadata，生成稳定 `chunk_id`，记录 `section`、`chunk_index`、`chunk_count` 和 `chunk_size_chars`。本节仍不连接 Qdrant，不生成 embedding。

## 本节状态说明

这一节不需要打开 VMware Ubuntu 虚拟机。

原因是：

```text
本节不访问 Qdrant。
本节不启动 Docker。
本节不生成 embedding。
本节只把已加载的 RagDocument 切成 RagChunk。
```

本节新增：

```text
projects/ai-service/app/rag/splitters.py
projects/ai-service/tests/test_rag_splitters.py
```

本节更新：

```text
projects/ai-service/app/rag/README.md
projects/ai-service/README.md
```

## 生成笔记前的教学复核

这一节必须讲清：

```text
1. chunk 是什么。
2. 为什么不能整篇文档直接 embedding。
3. chunk 太大有什么问题。
4. chunk 太小有什么问题。
5. chunk_size 是什么。
6. chunk_overlap 是什么。
7. 为什么标题和章节上下文重要。
8. 为什么按段落优先，而不是纯字符硬切。
9. RagDocument 如何变成 list[RagChunk]。
10. chunk_id 为什么要稳定。
11. splitter 为什么不负责 embedding 和 Qdrant。
12. 本节代码每个核心函数负责什么。
13. chunk 切分为什么影响召回率和精确率。
14. chunk 切分和 embedding 语义表达有什么关系。
15. chunk 切分和 token 成本、上下文窗口有什么关系。
16. 常见切分策略有哪些，各自适合什么场景。
17. 不同文档类型应该怎么考虑切分。
18. 怎么判断 chunk 切得好不好。
```

## 本节一句话定位

第 11 节已经做到：

```text
文件
-> loader
-> RagDocument
```

第 12 节继续往下：

```text
RagDocument
-> splitter
-> list[RagChunk]
```

也就是：

```text
把一篇加载好的文档，切成多个适合 embedding 和检索的小片段。
```

## 本节补强说明

这一节第一次写的时候，已经讲了 chunk、`chunk_size`、`chunk_overlap`、标题、段落和本项目代码。

但它还不够完整。

问题在于：

```text
代码讲解比较多；
chunk 切分作为 RAG 核心主题的系统讲解不够厚。
```

所以这里补强两部分：

```text
1. 基础知识铺垫加强版：为什么 chunk 切分会影响 RAG 整体质量。
2. 本节主题系统讲解加强版：常见切分策略、不同文档类型、调参和评估方法。
```

补强后的目标不是让你背代码，而是让你能跟别人讲清楚：

```text
为什么 RAG 不是随便切文本；
为什么 chunk 粒度会影响检索；
为什么标题、段落、overlap、metadata 都很关键；
如何判断切分策略是否合理。
```

## 基础知识铺垫加强版：chunk 切分为什么重要

RAG 的检索不是直接在“整篇文档”上做判断。

大多数时候，向量数据库里真正被检索的是：

```text
chunk 的 embedding。
```

也就是说，用户问题来了以后，系统比较的是：

```text
query vector
vs
chunk vector
```

不是：

```text
query vector
vs
整篇文档
```

所以 chunk 切分决定了：

```text
1. 向量库里到底有哪些可检索单位。
2. 每个向量代表什么语义。
3. 检索能不能召回正确内容。
4. 模型最终看到的是完整依据还是碎片噪声。
```

如果 chunk 切错了，后面即使：

```text
embedding 模型很好
Qdrant 配置正确
top_k 设置合理
prompt 写得不错
```

最终效果仍然可能很差。

原因是：

```text
检索库里的基本材料已经坏了。
```

## chunk 切分影响 RAG 的四个环节

chunk 切分至少影响 RAG 的四个环节。

### 1. 影响 embedding 表达

embedding 模型会把一段文本压缩成一个向量。

如果 chunk 内容主题清楚：

```text
订单超过 72 小时未发货时，客服可以创建发货异常工单。
```

这个向量大概率会表达：

```text
订单发货异常
超时未发货
客服工单
```

如果 chunk 内容混杂：

```text
订单发货规则、退款规则、账号安全、物流异常、客服话术……
```

这个向量就会变成多种语义的混合。

用户问一个具体问题时，混合向量不一定能精准匹配。

### 2. 影响检索召回

召回可以先理解成：

```text
用户问问题时，系统能不能把真正相关的 chunk 找回来。
```

如果一个重要规则被切碎了，可能每个碎片都不够像用户问题。

结果是：

```text
正确内容明明在知识库里，但检索没有拿回来。
```

这就是召回失败。

### 3. 影响检索精确

精确可以先理解成：

```text
系统拿回来的 chunk 里，有多少是真正相关的。
```

如果 chunk 太大，里面混入很多无关内容。

向量库可能把它拿回来，但模型看到的是：

```text
相关内容 + 一堆噪声。
```

这会降低回答质量。

### 4. 影响生成回答

模型最终不是直接看向量。

模型看到的是：

```text
被检索出来的 chunk 原文。
```

如果 chunk 内容完整、上下文清楚，模型更容易回答正确。

如果 chunk 断裂、缺标题、缺上下文，模型更容易：

```text
答不完整
答偏
把多个规则混在一起
无法引用准确来源
```

## 召回率和精确率的基础理解

这两个词后面做 RAG 评测会经常出现。

### 召回率 recall

召回率关注：

```text
应该找到的内容，有没有被找回来。
```

例子：

用户问：

```text
订单三天没发货怎么办？
```

知识库里有正确 chunk：

```text
如果订单付款后超过 72 小时仍未发货，客服可以创建发货异常工单。
```

如果检索结果里包含它，就说明召回成功。

如果没有包含它，就是召回失败。

### 精确率 precision

精确率关注：

```text
找回来的内容里，有多少是真的相关。
```

如果 top_k=5 返回：

```text
1. 超过 72 小时未发货规则
2. 发货异常工单
3. 物流三天未更新
4. 退款到账时间
5. 忘记登录密码
```

前 3 个可能相关，后 2 个明显不相关。

这说明精确率不够好。

### chunk 切分和 recall / precision 的关系

chunk 太小：

```text
容易丢上下文，导致正确内容不够像用户问题。
召回可能下降。
```

chunk 太大：

```text
容易混入噪声。
精确率可能下降。
```

所以 chunk 切分本质上是在平衡：

```text
上下文完整性
语义单一性
检索召回
检索精确
token 成本
```

## chunk 切分和 embedding 的关系

embedding 模型不是魔法。

它只能根据输入文本生成向量。

输入文本如果主题清晰，向量通常更有用。

输入文本如果主题混乱，向量也会混乱。

可以这样理解：

```text
embedding 向量是 chunk 内容的压缩表示。
chunk 内容质量决定了压缩出来的向量质量上限。
```

例如：

```text
chunk A:
退款通常会在 1 到 3 个工作日内原路退回。
```

它适合匹配：

```text
退款多久到账？
```

如果 chunk B 是：

```text
退款通常会在 1 到 3 个工作日内原路退回。用户忘记密码时可以通过手机号验证码重置。物流显示签收但用户没收到时需要核对签收人。
```

它包含三个主题：

```text
退款
账号
物流
```

embedding 会压缩成一个混合向量。

用户问退款时，它可能还能被召回，但模型会看到很多无关内容。

## chunk 切分和 token 成本的关系

RAG 检索出来的 chunk 最后会进入 prompt。

如果 chunk 太长，`top_k` 又比较大，prompt 会变得很长。

例如：

```text
top_k = 5
每个 chunk = 1000 字
```

模型可能一次要读：

```text
5000 字上下文 + 用户问题 + system prompt + 引用要求
```

这会带来：

```text
1. token 成本增加。
2. 响应速度变慢。
3. 上下文窗口更容易被占满。
4. 模型被无关内容干扰。
```

所以 chunk 切分不是只影响检索。

它也影响：

```text
费用
性能
回答稳定性
```

## chunk 切分和引用来源的关系

企业 RAG 通常要求：

```text
回答必须带出处。
```

如果 chunk 切得好，引用可以很具体：

```text
来源：order-shipping-policy.md / 超过 72 小时未发货
```

如果 chunk 太大，引用只能很粗：

```text
来源：order-shipping-policy.md
```

如果 chunk 太小，引用可能不完整：

```text
来源：某个只有半句话的 chunk
```

所以 chunk metadata 里的：

```text
source
title
section
chunk_index
```

都很重要。

它们不是装饰字段，而是后续引用和排查的基础。

## 基础知识铺垫：chunk 是什么

chunk 可以先理解成：

```text
从文档中切出来的一小段文本。
```

在 RAG 里，通常不是整篇文档直接进入向量数据库，而是：

```text
一篇文档
-> 切成多个 chunk
-> 每个 chunk 生成 embedding
-> 每个 chunk 写成 Qdrant point
```

所以 chunk 是连接这些概念的核心：

```text
document
RagDocument
RagChunk
embedding
Qdrant point
retrieval result
source citation
```

第 7 节讲过：

```text
RAG 里一个 Qdrant point 通常对应一个 chunk。
```

本节就是生成这些 chunk。

## 为什么不能整篇文档直接 embedding

假设有一篇文档：

```text
订单发货规则
退款退货规则
物流异常处理
账号安全问题
```

用户问：

```text
退款一般多久到账？
```

如果整篇文档只有一个 embedding，那么这个向量代表的是整篇文档的混合语义。

它里面有：

```text
订单
退款
物流
账号
```

用户问题只和退款有关，但向量里混了很多其他主题。

这样会导致：

```text
1. 检索不精准。
2. 模型拿到太多无关内容。
3. prompt 变长。
4. 引用来源不够具体。
5. 后续权限和来源排查变粗。
```

所以 RAG 更常见的做法是：

```text
按章节、段落、语义片段切成 chunk。
```

这样用户问退款问题时，更容易检索到退款相关 chunk。

## 为什么 chunk 不能太大

chunk 太大会有这些问题。

### 1. 语义混杂

一个 chunk 里如果包含太多主题：

```text
发货
退款
物流
账号
```

embedding 会变成混合语义。

用户问某个具体问题时，检索结果可能不够精准。

### 2. prompt 变长

RAG 检索到 chunk 后，会把 chunk 内容放进 prompt。

如果每个 chunk 很长：

```text
top_k = 5
每个 chunk 2000 字
```

那一次回答可能塞进很多文本。

结果是：

```text
token 成本高
响应慢
模型更容易被无关内容干扰
```

### 3. 引用来源不具体

如果一个 chunk 太大，引用时只能说：

```text
来源：订单发货规则
```

但用户想知道的是：

```text
具体哪一段说明超过 72 小时未发货怎么处理。
```

chunk 适中，引用更精确。

## 为什么 chunk 不能太小

chunk 太小也有问题。

### 1. 上下文丢失

比如一个规则本来是：

```text
如果订单付款后超过 72 小时仍未发货，客服需要先检查商品缺货、地址异常、仓库延迟等情况。如果没有特殊原因，可以创建发货异常工单。
```

如果切得太小，可能变成：

```text
如果订单付款后超过 72 小时仍未发货
```

另一个 chunk：

```text
客服需要先检查商品缺货、地址异常
```

再另一个 chunk：

```text
如果没有特殊原因，可以创建发货异常工单
```

每个 chunk 都不完整。

模型看到其中一个，可能答不完整。

### 2. 检索结果碎片化

用户问一个完整问题，可能需要多个碎片才能回答。

如果 chunk 太小，top_k 里会出现很多碎片。

这会增加后续组合难度。

### 3. embedding 表达能力下降

embedding 需要一定上下文才能表示语义。

太短的文本可能语义不明确。

比如：

```text
可以创建工单。
```

这句话单独看，完全不知道是什么工单。

如果保留上下文：

```text
如果订单付款后超过 72 小时仍未发货，客服可以创建发货异常工单。
```

就清楚很多。

## chunk_size 是什么

`chunk_size` 表示：

```text
希望每个 chunk 大概不要超过多长。
```

当前代码里用字符数做近似：

```text
chunk_size = 500
```

表示：

```text
尽量让每个 chunk 不超过 500 个字符。
```

注意：

```text
字符数不是 token 数。
```

但学习阶段先用字符数更直观。

后面做更精细的优化时，可以考虑按 token 切分。

## chunk_overlap 是什么

`chunk_overlap` 表示：

```text
相邻 chunk 之间保留一点重复上下文。
```

为什么需要 overlap？

因为切分边界可能刚好切在一个语义连接处。

比如：

```text
chunk 1:
如果订单付款后超过 72 小时仍未发货，客服需要先检查订单状态。

chunk 2:
如果没有特殊原因，客服可以创建发货异常工单。
```

第二个 chunk 单独看，可能不知道“没有特殊原因”指什么。

如果有 overlap，第二个 chunk 可以带一点前文：

```text
客服需要先检查订单状态。

如果没有特殊原因，客服可以创建发货异常工单。
```

这样语义更完整。

## overlap 不是越大越好

overlap 太大会导致：

```text
1. 重复内容太多。
2. 向量库里存很多近似重复 chunk。
3. 检索结果可能被重复内容占满。
4. token 成本增加。
```

所以 overlap 是一个需要调的参数。

当前默认：

```text
chunk_size = 500
chunk_overlap = 80
```

只是学习阶段的保守起点。

后面第 25 节会专门讲检索质量调优。

## 为什么标题和章节很重要

标题是文档的上下文。

比如 chunk 内容是：

```text
用户收到商品后 7 天内，可以申请七天无理由退货。
```

如果知道它属于：

```text
退款退货规则 / 七天无理由退货
```

模型会更容易理解。

如果 chunk 内容是：

```text
不能直接退款。
```

这句话单独看很模糊。

如果知道它属于：

```text
物流查询常见问题 / 物流异常可以直接退款吗？
```

语义就清楚很多。

所以本节 splitter 会记录：

```text
section
```

到 chunk metadata 里。

后续它可以进入 Qdrant payload。

## 为什么按段落优先

文档天然有结构。

比如 Markdown：

```text
## 超过 72 小时未发货

如果订单付款后超过 72 小时仍未发货，客服需要先检查订单是否存在以下情况：

- 商品缺货
- 地址信息异常
```

段落和列表通常是相对完整的语义单元。

如果按固定字符硬切，可能把一个句子切成两半。

所以本节采用：

```text
先按空行切 block。
再把 block 组合成 chunk。
如果单个 block 太大，再按字符窗口切。
```

这叫：

```text
段落优先。
```

它不是最复杂的切分算法，但非常适合入门。

## 本节主题系统讲解加强版：常见切分策略

chunk 切分有很多策略。

不要以为只有一种：

```text
每 500 字切一刀。
```

真实 RAG 项目里，切分策略通常要根据文档类型、问题类型、检索目标和模型上下文来选择。

下面先建立全局地图。

## 策略 1：固定长度切分

固定长度切分就是：

```text
每 N 个字符或 token 切一个 chunk。
```

比如：

```text
每 500 个字符切一段。
```

优点：

```text
1. 实现简单。
2. 每个 chunk 大小比较均匀。
3. 容易控制 token 成本。
```

缺点：

```text
1. 可能从句子中间切断。
2. 可能把标题和正文分开。
3. 可能把列表切碎。
4. 不理解文档结构。
```

适合：

```text
没有明显结构的长文本。
作为兜底策略。
```

不适合：

```text
结构清楚的 Markdown、FAQ、政策文档。
```

本节代码里的 `_split_oversized_block()` 就是固定长度切分的兜底版本。

它不是主策略。

主策略仍然是段落优先。

## 策略 2：按段落切分

按段落切分就是：

```text
根据空行、换行、自然段边界来切。
```

优点：

```text
1. 更符合人类写作结构。
2. 不容易切断句子。
3. chunk 可读性更好。
4. 适合 Markdown/txt 入门文档。
```

缺点：

```text
1. 如果段落很长，仍然需要兜底切分。
2. 如果文档空行混乱，效果会变差。
3. 有些列表项可能需要和前文一起保留。
```

本项目当前使用：

```text
段落优先 + 超长段落兜底切分。
```

原因是：

```text
我们的样本文档标题、段落、列表都比较清楚。
```

## 策略 3：按标题/章节切分

Markdown 文档通常有：

```text
# 一级标题
## 二级标题
### 三级标题
```

按标题切分就是：

```text
每个章节尽量形成一个或多个 chunk。
```

优点：

```text
1. 保留章节语义。
2. 引用来源更清楚。
3. 用户问某类问题时更容易命中对应章节。
```

缺点：

```text
1. 如果章节太长，仍然要继续切。
2. 如果标题太短，单独作为 chunk 没意义。
3. 标题层级处理会比普通段落切分复杂。
```

本节代码做的是标题感知：

```text
遇到标题时记录 section；
chunk metadata 里保存 section；
但不是完整的复杂 Markdown 解析器。
```

这是学习阶段的合理折中。

## 策略 4：递归切分

递归切分的思路是：

```text
先按大边界切；
切不开或太长，再按小边界切。
```

常见顺序可能是：

```text
章节
-> 段落
-> 句子
-> 字符
```

比如：

```text
先按 ## 标题切；
如果某一节太长，再按段落切；
如果某段还太长，再按句子或字符切。
```

优点：

```text
1. 比固定长度更尊重文档结构。
2. 又能保证 chunk 不会无限大。
3. 是很多成熟 splitter 的基本思路。
```

缺点：

```text
1. 实现复杂度更高。
2. 需要处理各种边界情况。
3. 不同语言和文档格式需要不同规则。
```

后面如果引入 LangChain TextSplitter，你会发现它的一些 splitter 也有类似思想。

## 策略 5：语义切分

语义切分更进一步。

它不是只看字符、段落、标题，而是尝试判断：

```text
哪些句子在语义上应该放在一起。
```

可能会用：

```text
embedding 相似度
句子边界
主题变化检测
LLM 辅助判断
```

优点：

```text
1. 更接近人的理解。
2. 适合复杂文档。
3. 理论上能切出更自然的 chunk。
```

缺点：

```text
1. 实现成本高。
2. 可能需要额外模型调用。
3. 速度和成本更高。
4. 结果不一定稳定。
```

当前阶段不做语义切分。

原因是：

```text
先把基础 RAG 主线跑通。
```

## 常见切分策略对比表

| 策略 | 优点 | 缺点 | 适合阶段 |
| --- | --- | --- | --- |
| 固定长度切分 | 简单、大小可控 | 容易切断语义 | 兜底、入门理解 |
| 段落切分 | 保留自然语义 | 依赖文档格式 | 当前项目主策略 |
| 标题/章节切分 | 上下文清楚、引用友好 | 长章节还要二次切 | Markdown/政策文档 |
| 递归切分 | 结构和大小兼顾 | 实现更复杂 | 进阶实践 |
| 语义切分 | 更贴近主题变化 | 成本高、不稳定 | 高级优化 |

## 不同文档类型怎么切

不同文档不应该一律用同一种策略。

### 政策文档

例如：

```text
订单发货规则
退款退货规则
```

特点：

```text
标题清楚
章节清楚
规则段落清楚
```

适合：

```text
按标题 + 段落切分。
```

要保留：

```text
title
section
doc_type
business_domain
permission_group
```

### FAQ 文档

例如：

```text
问题：物流三天没有更新怎么办？
回答：客服需要先查询承运商轨迹……
```

特点：

```text
问题和回答天然是一组。
```

理想切法：

```text
一个 Q/A 对尽量作为一个 chunk。
```

不要把问题和回答切开。

如果把问题切在一个 chunk，回答切在另一个 chunk，检索效果会变差。

当前本节还没有专门写 FAQ splitter。

但后面可以优化。

### 操作手册

例如：

```text
第一步：打开系统
第二步：选择订单
第三步：创建工单
```

特点：

```text
步骤顺序很重要。
```

切分时要注意：

```text
不能把前后依赖很强的步骤切得太碎。
```

可以按小节切，但要保留步骤上下文。

### API 文档

API 文档通常有：

```text
接口地址
请求参数
响应字段
错误码
示例
```

切分时要避免：

```text
接口地址在一个 chunk；
参数说明在另一个 chunk；
错误码又在另一个 chunk。
```

理想情况：

```text
一个接口的完整说明尽量在一个或少数几个 chunk 里。
```

### 表格文档

表格比较麻烦。

如果直接转成纯文本，可能变成：

```text
字段 名称 类型 是否必填 说明
```

结构容易乱。

表格切分要考虑：

```text
表头是否保留
每行是否完整
字段含义是否丢失
```

当前阶段不处理复杂表格。

## 中文文档切分有什么特殊点

中文和英文不完全一样。

英文有空格：

```text
The order has not been shipped for 72 hours.
```

中文没有天然词间空格：

```text
订单超过72小时未发货
```

所以按词切分在中文里更复杂。

当前阶段按：

```text
标题
段落
字符长度
```

比按词更简单。

后面如果做更精细中文切分，可能会考虑：

```text
中文句号。
问号？
分号；
列表项
领域词汇
```

但现在不需要一开始就上复杂中文分词。

## chunk_size 怎么选

没有一个永远正确的 chunk_size。

它取决于：

```text
文档类型
模型上下文窗口
embedding 模型最大输入长度
用户问题粒度
top_k 设置
是否有 rerank
是否要求引用精确
```

初学可以用经验起点：

```text
短 FAQ：100-300 中文字符
政策段落：300-800 中文字符
长手册：500-1000 中文字符
```

但最终要靠评测。

本项目当前默认：

```text
500 字符
```

是为了学习阶段可控。

不是生产推荐值。

## chunk_overlap 怎么选

overlap 也没有固定答案。

可以按经验起点：

```text
chunk_size 的 10% 到 20%
```

比如：

```text
chunk_size = 500
chunk_overlap = 50 到 100
```

但要注意：

```text
overlap 不是为了制造重复；
overlap 是为了缓解边界断裂。
```

如果文档本身段落很完整，overlap 可以小一点。

如果切分经常切断上下文，overlap 可以适当增加。

## 如何判断 chunk 切得好不好

不要只看代码能不能运行。

chunk 切分质量要人工和测试一起看。

### 1. 抽样阅读 chunk

随机看一些 chunk，问自己：

```text
这个 chunk 单独看能不能理解？
它有没有缺少标题？
它有没有混入多个无关主题？
它是不是太短？
它是不是太长？
```

### 2. 用典型问题检查召回

准备问题：

```text
订单三天没发货怎么办？
退款多久到账？
物流显示签收但没收到怎么办？
忘记密码怎么办？
```

看检索是否能召回正确 chunk。

### 3. 看 top_k 结果是否重复

如果 top_k 返回很多高度重复 chunk，可能 overlap 太大。

### 4. 看回答引用是否准确

如果模型回答能引用到具体 section，说明 metadata 和 chunk 粒度比较健康。

如果只能引用整篇文档，可能 chunk/metadata 太粗。

### 5. 看无关内容比例

如果一个 chunk 里有太多无关内容，说明 chunk 太大或切分边界不合理。

## 本项目当前策略的取舍

本节当前实现不是最强 splitter。

它是一个学习阶段的清晰实现：

```text
段落优先
标题感知
超长段落兜底
段落级 overlap
稳定 chunk_id
metadata 继承
```

它适合当前样本文档：

```text
Markdown 政策文档
txt FAQ 文档
短小、结构清楚、可控
```

它暂时不处理：

```text
复杂 PDF
Word 表格
嵌套 Markdown 表格
代码文档复杂块
精细中文句子切分
语义切分
rerank 优化
```

这不是缺陷，而是学习阶段边界。

后续当我们做检索质量调优时，可以再迭代 splitter。

## 本节主题系统讲解：新增 splitters.py

新增文件：

```text
projects/ai-service/app/rag/splitters.py
```

核心函数：

```text
split_text_into_blocks()
split_document_into_chunks()
split_documents_into_chunks()
```

辅助函数：

```text
_is_inline_metadata_block()
_extract_markdown_heading()
_split_oversized_block()
_select_overlap_blocks()
_build_chunk_id()
_validate_chunk_options()
```

## split_text_into_blocks()

代码职责：

```text
按空行把文本切成 block。
```

例如：

```text
第一段

第二段


第三段
```

会变成：

```text
["第一段", "第二段", "第三段"]
```

为什么按空行？

因为第 11 节 cleaning 已经把多余空行压缩成稳定格式。

空行通常表示段落边界。

## _is_inline_metadata_block()

第 10 节样本文档开头有：

```text
> 文档类型：policy
> 业务领域：order
> 权限组：customer_service
```

这些是 metadata 线索，不是业务正文。

loader 已经把它们提取到：

```text
RagDocument.metadata
```

所以 splitter 不应该再把这些行切成 chunk。

否则后面检索可能搜到：

```text
文档类型：policy
业务领域：order
权限组：customer_service
```

这对回答用户问题没有价值。

所以 `_is_inline_metadata_block()` 会识别并跳过这类 block。

## _extract_markdown_heading()

这个函数识别 Markdown 标题：

```text
# 订单发货规则
## 超过 72 小时未发货
```

提取出：

```text
订单发货规则
超过 72 小时未发货
```

并记录到：

```text
metadata["section"]
```

注意：

```text
section 是当前 chunk 所属章节。
```

后续检索结果可以用它做展示或引用。

## _split_oversized_block()

大多数情况下，一个段落不会超过 `chunk_size`。

但如果出现很长的一段，比如长 FAQ、长代码块、长表格文本，就需要切。

`_split_oversized_block()` 负责：

```text
如果单个 block 超过 chunk_size，就按字符窗口拆成多个 segment。
```

它也使用：

```text
chunk_overlap
```

让被硬切的大段落保留一点重叠。

这是兜底逻辑。

正常情况下，我们仍然优先保留完整段落。

## _select_overlap_blocks()

这个函数负责段落级 overlap。

它从前一个 chunk 的末尾选择若干完整 block，作为下一个 chunk 的开头。

比如：

```text
chunk 1:
alpha-001

beta-0002

chunk 2:
beta-0002

gamma-003
```

这里 `beta-0002` 就是 overlap。

为什么保留完整 block？

因为比硬截字符更容易读。

当然，如果 overlap block 加上新内容会超过 `chunk_size`，代码会丢掉 overlap，避免生成超长 chunk。

## _build_chunk_id()

chunk_id 要稳定。

本节根据文档 source 生成：

```text
order-shipping-policy.md
-> order_shipping_policy_chunk_0001
-> order_shipping_policy_chunk_0002
```

为什么不用随机 UUID？

学习阶段需要可读、可排查。

看到：

```text
order_shipping_policy_chunk_0003
```

你能知道：

```text
这是订单发货规则文档的第 3 个 chunk。
```

后续写 Qdrant 时：

```text
RagChunk.chunk_id -> Qdrant point.id
```

稳定 id 非常重要。

## _validate_chunk_options()

它负责检查参数：

```text
chunk_size > 0
chunk_overlap >= 0
chunk_overlap < chunk_size
```

为什么 overlap 必须小于 chunk_size？

如果：

```text
chunk_overlap >= chunk_size
```

切分时窗口可能无法向前推进，或者产生大量重复内容。

所以必须拒绝。

## split_document_into_chunks()

这是本节最核心函数。

输入：

```text
RagDocument
```

输出：

```text
list[RagChunk]
```

它做的事情：

```text
1. 校验 chunk 参数。
2. 把 document.content 切成 blocks。
3. 跳过 metadata-only block。
4. 遇到 Markdown 标题时更新 section。
5. 按 chunk_size 组合 blocks。
6. 必要时保留 overlap。
7. 生成稳定 chunk_id。
8. 合并原 document metadata。
9. 给每个 chunk 增加 chunk_index、chunk_count、chunk_size_chars、section。
10. 返回 RagChunk 列表。
```

## split_documents_into_chunks()

这个函数批量处理多个文档。

输入：

```text
list[RagDocument]
```

输出：

```text
list[RagChunk]
```

它只是循环调用：

```text
split_document_into_chunks()
```

为什么需要它？

因为第 11 节的目录 loader 输出就是：

```text
list[RagDocument]
```

第 12 节需要把它们统一切成：

```text
list[RagChunk]
```

## RagChunk metadata 里新增什么

本节生成的每个 chunk 会继承 document metadata。

比如：

```text
source
title
file_name
file_extension
doc_type
business_domain
permission_group
```

还会新增：

```text
chunk_id
chunk_index
chunk_count
chunk_size_chars
section
```

这些字段后续会进入 Qdrant payload。

例如：

```json
{
  "source": "order-shipping-policy.md",
  "title": "订单发货规则",
  "doc_type": "policy",
  "business_domain": "order",
  "permission_group": "customer_service",
  "chunk_id": "order_shipping_policy_chunk_0001",
  "chunk_index": 1,
  "chunk_count": 5,
  "chunk_size_chars": 120,
  "section": "超过 72 小时未发货"
}
```

## splitter 不负责什么

本节 splitter 不负责：

```text
1. 读取文件。
2. 清洗原始文件。
3. 调用 embedding 模型。
4. 连接 Qdrant。
5. 写入 point。
6. 检索 top_k。
7. 生成最终答案。
```

它只负责：

```text
RagDocument -> list[RagChunk]
```

这就是分层。

## 本节测试讲什么

新增：

```text
projects/ai-service/tests/test_rag_splitters.py
```

测试覆盖：

```text
1. 按空行切 block。
2. Markdown 文档能切成多个 chunk。
3. chunk_id 稳定。
4. document metadata 会继承到 chunk。
5. inline metadata block 不进入 chunk content。
6. Markdown section 能进入 chunk metadata。
7. 段落级 overlap 能工作。
8. 无效 chunk_overlap 会报错。
9. 多文档批量切分能工作。
```

这些测试保护的是：

```text
切分策略的基本契约。
```

不是最终检索质量。

检索质量后面还要通过 RAG 评测来判断。

## 为什么不用 LangChain TextSplitter

LangChain 有成熟的 text splitter。

但当前阶段我们先自己实现一个最小 splitter。

原因是：

```text
1. 你需要理解 chunk 切分本身。
2. 现在文档很简单，用自定义实现更透明。
3. 后面学 LangChain 封装时，才能知道它帮你做了什么。
4. 当前项目先建立自己的数据模型 RagDocument/RagChunk。
```

这不是说 LangChain splitter 不好。

而是学习顺序上：

```text
先理解基本原理，再使用成熟封装。
```

## 常见错误理解

### 错误 1：chunk_size 越大越好

不对。

太大会混入多个主题，检索不精准，prompt 成本高。

### 错误 2：chunk_size 越小越好

也不对。

太小会丢上下文，模型拿到碎片后很难回答完整。

### 错误 3：overlap 越大越安全

不对。

overlap 太大会制造大量重复内容，影响检索和成本。

### 错误 4：按字符硬切就够了

不建议。

按字符硬切可能把句子、列表、规则从中间切开。

段落优先更符合文本结构。

### 错误 5：chunk_id 可以随机生成

学习 demo 可以，但长期项目不建议。

稳定 chunk_id 对更新、删除、排查和 Qdrant point id 都很重要。

### 错误 6：splitter 可以顺便写 Qdrant

不应该。

splitter 只负责切分。

写 Qdrant 是 vector_store 的职责。

### 错误 7：只要 chunk 不超过长度限制就算切好了

不对。

长度只是一个基本约束。

真正要看的是：

```text
语义是否完整
主题是否单一
是否带标题上下文
metadata 是否够用
检索能不能命中
模型回答是否能引用准确来源
```

一个 chunk 就算长度刚好，如果里面混入多个不相关主题，也不是好 chunk。

### 错误 8：chunk 切分只影响检索，不影响生成

不对。

chunk 会进入 prompt。

所以它也影响：

```text
模型看到什么上下文
模型是否被噪声干扰
回答是否完整
引用是否准确
token 成本是否可控
```

### 错误 9：所有文档都用同一种切分策略

不建议。

政策文档、FAQ、操作手册、API 文档、表格文档的结构不同。

切分策略应该根据文档类型调整。

## 本节练习

### 练习 1：判断 chunk 大小问题

下面说法哪些正确？

```text
1. chunk 越大越好，因为上下文更多。
2. chunk 越小越好，因为检索更精准。
3. chunk 太大会语义混杂。
4. chunk 太小会丢上下文。
5. chunk_size 需要结合文档结构和检索效果调优。
```

参考答案：

```text
3、4、5 正确。
1 和 2 都太绝对。
```

### 练习 2：解释 overlap

问题：

```text
chunk_overlap 的作用是什么？
```

参考答案：

```text
chunk_overlap 用来让相邻 chunk 保留一部分重复上下文，减少切分边界导致的语义断裂。
但 overlap 不能太大，否则会制造太多重复内容。
```

### 练习 3：解释为什么保留 section

问题：

```text
为什么要把 Markdown 标题记录到 chunk.metadata["section"]？
```

参考答案：

```text
因为 section 能告诉后续检索结果属于哪个章节。
它有助于模型理解上下文，也有助于引用来源和问题排查。
```

### 练习 4：说明 RagDocument 到 RagChunk 的映射

问题：

```text
RagDocument 的哪些信息会进入 RagChunk？
```

参考答案：

```text
RagDocument.content 会被切成多个 RagChunk.content。
RagDocument.metadata 会继承到每个 RagChunk.metadata。
splitter 还会额外补充 chunk_id、chunk_index、chunk_count、chunk_size_chars、section 等字段。
```

### 练习 5：判断职责归属

下面功能属于 splitter 吗？

```text
1. 把 Markdown 文档切成多个 chunk。
2. 给 chunk 生成稳定 chunk_id。
3. 调用 embedding 模型。
4. 写入 Qdrant。
5. 记录 chunk_index。
```

参考答案：

```text
1、2、5 属于 splitter。
3 属于 embeddings。
4 属于 vector_store。
```

### 练习 6：分析 chunk 是否合理

下面这个 chunk 是否合理？

```text
退款通常会在 1 到 3 个工作日内原路退回。用户忘记登录密码时，可以通过手机号验证码重置。物流显示已签收但用户说没有收到时，客服需要核对签收人。
```

参考答案：

```text
不太合理。
```

原因：

```text
它混合了退款、账号安全、物流三个主题。
embedding 会得到混合语义。
用户问退款时，账号和物流内容是噪声；
用户问账号时，退款和物流内容又是噪声。
```

更好的做法：

```text
按业务主题或文档章节拆成不同 chunk。
```

### 练习 7：为 FAQ 选择切分策略

问题：

```text
FAQ 文档里有很多“问题/回答”对，为什么不应该把问题和回答切开？
```

参考答案：

```text
因为问题和回答是一组完整语义。
如果问题在一个 chunk，回答在另一个 chunk，用户查询时可能只召回问题或只召回答案，导致上下文不完整。
FAQ 更适合尽量让一个 Q/A 对保持在同一个 chunk 中。
```

### 练习 8：判断 chunk_size 和 overlap 的取舍

问题：

```text
如果检索结果里经常出现很多重复 chunk，可能是什么原因？
```

参考答案：

```text
可能是 chunk_overlap 太大，导致相邻 chunk 重复内容过多。
也可能是 chunk_size 太小，导致同一个主题被切成太多相似片段。
需要检查 top_k 结果和 chunk 内容，再调整 chunk_size / overlap。
```

### 练习 9：设计人工检查清单

问题：

```text
你拿到一批切好的 chunk 后，应该人工检查哪些点？
```

参考答案：

```text
1. 单个 chunk 是否能独立理解。
2. 是否带有标题或 section 上下文。
3. 是否混入多个无关主题。
4. 是否过短或过长。
5. metadata 里是否有 source、title、section、chunk_id。
6. 相邻 chunk 是否重复过多。
7. 典型问题能否召回正确 chunk。
```

## 自测问题

### 自测 1：本节为什么不需要打开虚拟机？

参考答案：

```text
因为本节只做本地文本切分，不访问 Qdrant，不启动 Docker，也不生成 embedding。
```

### 自测 2：splitter 的输入输出是什么？

参考答案：

```text
输入是 RagDocument，输出是 list[RagChunk]。
```

### 自测 3：为什么不整篇文档直接 embedding？

参考答案：

```text
整篇文档可能包含多个主题，embedding 会语义混杂，检索不精准，prompt 成本高，引用来源也不够具体。
```

### 自测 4：本节 splitter 为什么按段落优先？

参考答案：

```text
因为段落通常是相对完整的语义单元。按段落优先能减少把句子和规则从中间切开的情况。
```

### 自测 5：chunk_id 后续会用在哪里？

参考答案：

```text
chunk_id 后续可以作为 Qdrant point id，用于写入、更新、删除、去重和排查。
```

### 自测 6：inline metadata block 为什么不进入 chunk？

参考答案：

```text
因为这些内容已经被 loader 提取到 metadata 中，不是业务正文。如果进入 chunk，会污染检索结果。
```

### 自测 7：chunk_count 有什么用？

参考答案：

```text
chunk_count 表示这篇文档一共被切成多少个 chunk，有助于调试、展示和判断切分是否异常。
```

### 自测 8：chunk 切分如何影响召回率？

参考答案：

```text
如果正确答案被切得太碎，每个碎片都缺少足够上下文，可能和用户问题不够相似，导致检索不到正确内容，召回率下降。
```

### 自测 9：chunk 切分如何影响精确率？

参考答案：

```text
如果 chunk 太大或主题混杂，检索可能返回包含少量相关内容但大量无关内容的 chunk，导致返回结果噪声变多，精确率下降。
```

### 自测 10：为什么不同文档类型可能需要不同切分策略？

参考答案：

```text
因为政策文档、FAQ、操作手册、API 文档和表格文档的结构不同。FAQ 要尽量保持问题和回答在一起，政策文档适合按标题和段落切，操作手册要保留步骤顺序，API 文档要避免把接口、参数和错误码切散。
```

## 本节复盘

这一节你要真正掌握的是：

```text
1. chunk 是 RAG 的核心检索单位。
2. 文档不能太粗地整篇 embedding，也不能切得太碎。
3. chunk_size 控制大小，chunk_overlap 缓解边界断裂。
4. 标题和章节上下文会影响检索和回答质量。
5. 本节 splitter 采用段落优先、标题感知的基础策略。
6. RagDocument 被切成 RagChunk。
7. RagChunk metadata 会继承 document metadata，并补充 chunk_id、section 等字段。
8. splitter 不负责 embedding 和 Qdrant。
9. chunk 切分会影响召回率、精确率、token 成本和最终回答质量。
10. 固定长度、段落、标题、递归、语义切分各有适用场景。
11. FAQ、政策、操作手册、API 文档、表格文档不能完全用同一种切法。
12. 判断 chunk 好不好，要看语义完整、主题单一、上下文清楚、metadata 完整和检索效果。
```

下一节可以进入：

```text
阶段 4 第 13 节：生成 embedding 并写入 Qdrant。
```
