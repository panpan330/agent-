# 阶段 4 第 10 节：准备第一批 Markdown/txt 知识文档

> 本节结论：RAG 的第一步不是写向量检索代码，而是准备一批结构清楚、内容可控、适合切分和检索的知识文档。本节在 `projects/ai-service/data/knowledge_base` 下新增 4 份模拟客服知识文档，覆盖订单发货、退款退货、物流查询和账号安全。它们会作为后续文档加载、文本清洗、chunk 切分、embedding 生成、Qdrant 入库和检索问答的固定练习材料。

## 本节状态说明

这一节不需要打开 VMware Ubuntu 虚拟机。

原因是：

```text
本节不访问 Qdrant。
本节不启动 Docker。
本节不生成 embedding。
本节只在 Windows 项目里准备 RAG 知识文档。
```

本节新增：

```text
projects/ai-service/data/knowledge_base/README.md
projects/ai-service/data/knowledge_base/order-shipping-policy.md
projects/ai-service/data/knowledge_base/refund-return-policy.md
projects/ai-service/data/knowledge_base/logistics-tracking-faq.txt
projects/ai-service/data/knowledge_base/account-security-faq.md
projects/ai-service/tests/test_knowledge_base_samples.py
```

并更新：

```text
projects/ai-service/README.md
```

## 生成笔记前的教学复核

这一节必须讲清：

```text
1. 为什么 RAG 需要先准备知识文档。
2. 为什么初学阶段先用 Markdown/txt。
3. 为什么不一开始就拿 PDF/Word 做主线。
4. 什么样的文档适合做 RAG 入门材料。
5. 文档标题、段落、列表、FAQ 对后续 chunk 切分有什么影响。
6. 为什么样本文档要小而清楚。
7. 为什么文档要有 source、title、doc_type、business_domain、permission_group 这些 metadata 线索。
8. 新增的 4 份知识文档各自负责什么。
9. 这些文档后面如何进入 loader、splitter、embedding、Qdrant。
10. 为什么本节只做轻量测试。
```

## 本节一句话定位

第 9 节我们设计了 RAG 项目结构：

```text
app/rag
RagDocument
RagChunk
```

第 10 节要准备真实输入：

```text
data/knowledge_base 里的 Markdown/txt 知识文档。
```

如果没有文档，后面这些都没有材料：

```text
文档加载
文本清洗
chunk 切分
embedding
写入 Qdrant
检索
引用来源
```

所以本节不是“随便写几篇文章”。

它是在为后续 RAG 主线准备固定训练材料。

## 基础知识铺垫：RAG 里的“知识文档”是什么

RAG 里的知识文档可以先理解成：

```text
系统允许模型参考的外部知识来源。
```

例如企业里可能有：

```text
客服 FAQ
订单规则
退款政策
物流异常处理手册
账号安全操作规范
内部流程文档
产品说明书
接口文档
```

用户问问题时，RAG 系统不会让模型凭空回答。

它会先从这些知识文档中检索相关片段，然后把片段交给模型。

所以文档质量会直接影响：

```text
检索能不能找到正确材料
模型回答有没有依据
引用来源是否清楚
权限过滤能不能做
后续评测是否稳定
```

RAG 的效果不是只靠模型。

文档本身是 RAG 的地基。

## 基础知识铺垫：为什么先准备文档，而不是先写检索代码

因为 RAG 是数据驱动的。

如果没有文档，检索代码没有检索对象。

如果文档质量很差，就算代码写对了，结果也可能很差。

比如文档内容是：

```text
规则很多，自己看。
```

用户问：

```text
订单三天没发货怎么办？
```

系统很难从这种文档里找到有用信息。

如果文档写成：

```text
如果订单付款后超过 72 小时仍未发货，客服需要先检查商品缺货、地址异常、仓库延迟等原因。如果没有特殊原因，可以创建发货异常工单。
```

检索和回答都会更稳定。

所以先准备文档，是为了让后面的技术练习有可靠输入。

## 基础知识铺垫：为什么先用 Markdown

Markdown 是一种纯文本格式。

它用简单符号表示结构：

```text
# 一级标题
## 二级标题
- 列表项
> 引用
```text
代码块或固定格式文本
```
```

Markdown 适合 RAG 入门，因为：

```text
1. 文件是纯文本，容易读取。
2. 标题结构清楚，方便后面按标题切 chunk。
3. 段落边界明显，方便清洗。
4. 不需要复杂解析器。
5. 适合手写小型知识库。
```

比如：

```markdown
# 订单发货规则

## 超过 72 小时未发货

如果订单付款后超过 72 小时仍未发货，客服需要先检查订单状态。
```

后续切 chunk 时，可以利用：

```text
# 订单发货规则
## 超过 72 小时未发货
```

这些标题作为上下文。

## 基础知识铺垫：为什么也准备 txt

txt 是最普通的纯文本。

它没有 Markdown 的标题语法，但很接近很多真实系统里的原始文本：

```text
FAQ 导出
客服话术
简单知识条目
复制出来的纯文本资料
```

本节准备一份：

```text
logistics-tracking-faq.txt
```

目的是让你后面看到：

```text
不同格式的文档，加载和清洗方式可能不同。
```

Markdown 有比较明确的结构。

txt 更依赖内容里的文字标记，比如：

```text
问题：
回答：
```

后面做 loader 和 splitter 时，这种差异很重要。

## 为什么不一开始处理 PDF/Word

PDF、Word 是真实企业里常见格式，但不适合一开始做主线。

原因是：

```text
1. PDF 解析可能有换行错乱。
2. PDF 可能有页眉、页脚、表格、图片。
3. Word 可能有复杂样式、批注、表格。
4. 解析结果质量会影响 chunk 切分。
5. 初学时容易把精力浪费在格式解析问题上。
```

我们当前要先学清：

```text
文档 -> chunk -> embedding -> Qdrant -> retrieve -> generate
```

这条主线。

等主线跑通，再学 PDF/Word 解析更合理。

所以第 10 节先用：

```text
Markdown + txt
```

这是为了降低噪声，不是因为 PDF/Word 不重要。

## 本节主题系统讲解：什么样的文档适合 RAG 入门

适合入门的 RAG 文档应该有这些特点。

### 1. 主题明确

每篇文档最好只围绕一个业务主题。

比如：

```text
订单发货规则
退款退货规则
物流查询常见问题
账号安全常见问题
```

不要一篇文档里同时混入：

```text
订单、退款、人事、数据库、服务器、销售报价
```

主题太杂会让检索和 chunk 切分都变困难。

### 2. 段落清楚

每个段落尽量表达一个完整意思。

比如：

```text
如果订单付款后超过 72 小时仍未发货，客服需要先检查订单是否存在商品缺货、地址异常、仓库延迟等情况。
```

这是一个完整规则。

不要写成：

```text
超过时间就看下，能处理就处理，不行再说。
```

这种文本太模糊，不利于检索和回答。

### 3. 有标题层级

标题能帮助后面生成更好的 chunk。

比如：

```text
# 退款退货规则
## 七天无理由退货
## 商品质量问题
## 退款到账时间
```

当某个 chunk 被检索出来时，如果保留标题信息，模型更容易理解上下文。

### 4. 有可检索的具体规则

RAG 文档要能回答具体问题。

比如：

```text
退款通常会在 1 到 3 个工作日内原路退回。
```

这能回答：

```text
退款多久到账？
```

如果文档只是空泛描述：

```text
我们会尽快处理退款。
```

检索到也没法给出明确回答。

### 5. 带 metadata 线索

后续写入 Qdrant 时，每个 chunk 都要有 payload。

所以文档里要能提取或推导：

```text
source
title
doc_type
business_domain
permission_group
```

本节文档开头有类似：

```text
> 文档类型：policy
> 业务领域：order
> 权限组：customer_service
```

这不是 Markdown 必须这么写，而是为了教学阶段清晰。

后续 loader 可以根据文件名和文档内容提取 metadata。

## 本节新增文档总览

新增目录：

```text
projects/ai-service/data/knowledge_base
```

新增文件：

```text
README.md
order-shipping-policy.md
refund-return-policy.md
logistics-tracking-faq.txt
account-security-faq.md
```

这批文档覆盖：

| 文件 | 类型 | 业务领域 | 用途 |
| --- | --- | --- | --- |
| `order-shipping-policy.md` | policy | order | 练习订单发货和超时发货检索 |
| `refund-return-policy.md` | policy | refund | 练习退款、退货、运费规则检索 |
| `logistics-tracking-faq.txt` | faq | logistics | 练习纯文本 FAQ 加载和问答 |
| `account-security-faq.md` | faq | account | 练习账号安全和敏感操作规则检索 |

这些文档都是模拟数据。

它们不是现实公司的真实制度。

## 为什么选客服知识库作为第一批材料

因为客服知识库非常适合 RAG 入门。

它有几个优点：

```text
1. 问题自然，容易模拟用户提问。
2. 答案通常来自明确规则。
3. 很适合做引用来源。
4. 很容易设计 metadata，例如 doc_type、business_domain、permission_group。
5. 和阶段 3 的订单查询、工单创建场景能衔接。
```

比如用户可以问：

```text
订单三天没发货怎么办？
退款多久到账？
物流显示签收但没收到怎么办？
忘记登录密码怎么办？
```

这些问题都能从本节文档中找到相关材料。

## 文档 1：订单发货规则

文件：

```text
order-shipping-policy.md
```

它包含：

```text
正常发货时效
超过 72 小时未发货
发货异常工单
不能直接承诺的内容
```

它适合回答：

```text
订单超过 72 小时没发货怎么办？
客服能不能承诺具体发货时间？
发货异常工单需要记录什么？
```

后续可能生成的 metadata：

```text
source = order-shipping-policy.md
title = 订单发货规则
doc_type = policy
business_domain = order
permission_group = customer_service
```

## 文档 2：退款退货规则

文件：

```text
refund-return-policy.md
```

它包含：

```text
七天无理由退货
商品质量问题
退款到账时间
运费处理
```

它适合回答：

```text
七天无理由退货有什么限制？
商品质量问题需要用户提供什么？
退款一般多久到账？
什么情况下商家承担运费？
```

后续可能生成的 metadata：

```text
source = refund-return-policy.md
title = 退款退货规则
doc_type = policy
business_domain = refund
permission_group = customer_service
```

## 文档 3：物流查询常见问题

文件：

```text
logistics-tracking-faq.txt
```

它是 txt 格式。

它包含：

```text
物流三天没有更新
显示签收但用户没收到
快递被退回
修改收货地址
物流异常是否可以直接退款
```

它适合回答：

```text
物流三天没有更新怎么办？
快递显示签收但我没收到怎么办？
快递被退回怎么处理？
已经发货还能改地址吗？
```

后续可能生成的 metadata：

```text
source = logistics-tracking-faq.txt
title = 物流查询常见问题
doc_type = faq
business_domain = logistics
permission_group = customer_service
```

## 文档 4：账号安全常见问题

文件：

```text
account-security-faq.md
```

它包含：

```text
忘记登录密码
手机号无法使用
账号存在异常登录
敏感操作限制
```

它适合回答：

```text
忘记密码怎么办？
原手机号不用了怎么改绑？
账号异常登录怎么办？
客服能不能要用户短信验证码？
```

后续可能生成的 metadata：

```text
source = account-security-faq.md
title = 账号安全常见问题
doc_type = faq
business_domain = account
permission_group = customer_service
```

## 为什么文档中要有“不能直接做什么”

你会发现文档里不只写了：

```text
应该怎么做。
```

还写了：

```text
不能直接承诺具体发货时间。
不能直接退款。
不能索要用户完整密码、支付密码或短信验证码。
```

这是因为企业 RAG 不只是回答知识。

它还要避免错误引导。

比如用户问：

```text
物流异常可以直接退款吗？
```

如果文档里有明确规则：

```text
不能直接退款，需要先确认订单状态、物流状态和异常原因。
```

模型更容易给出安全回答。

所以好的知识库文档要包含：

```text
可以做什么
不能做什么
需要满足什么条件
需要收集什么信息
```

## 这批文档后面如何进入 RAG 流程

后面第 11 节：

```text
文档加载和文本清洗
```

会把这些文件读成：

```text
RagDocument
```

第 12 节：

```text
chunk 切分策略
```

会把 `RagDocument` 切成：

```text
list[RagChunk]
```

第 13 节：

```text
生成 embedding 并写入 Qdrant
```

会把：

```text
RagChunk.content -> embedding vector
RagChunk.chunk_id -> Qdrant point id
RagChunk.metadata -> Qdrant payload
```

第 15 节以后：

```text
用户问题 -> query embedding -> Qdrant 检索 -> 返回相关 chunks
```

这批文档会成为检索目标。

## 本节测试讲什么

新增测试：

```text
tests/test_knowledge_base_samples.py
```

测试很轻，只做两件事：

```text
1. 确认 4 个样本文档存在。
2. 确认样本文档不是空文件。
```

为什么这么简单？

因为本节的重点不是算法。

本节的产出是：

```text
稳定的 RAG 练习输入材料。
```

如果文件名改错、文件没提交、内容为空，后面 loader 学习会直接受影响。

所以这类轻量测试是有价值的。

## 为什么不测试文档内容是否“正确”

因为这些是模拟文档。

测试不应该过度绑定自然语言细节。

比如如果以后我们把一句话改得更清楚，不应该导致大量测试失败。

所以当前只测试：

```text
文件存在
文件非空
```

内容质量靠学习笔记和人工复核保证。

后面做 RAG 评测时，再测试：

```text
某个问题能不能检索到正确 chunk
回答是否引用正确来源
无结果时是否拒答
```

## 当前项目结构变化

新增后，结构变成：

```text
projects/ai-service/
  data/
    knowledge_base/
      README.md
      account-security-faq.md
      logistics-tracking-faq.txt
      order-shipping-policy.md
      refund-return-policy.md
  app/
    rag/
      documents.py
  tests/
    test_knowledge_base_samples.py
    test_rag_documents.py
```

这里的 `data/knowledge_base` 是学习阶段的数据目录。

它和 `app/rag` 的关系是：

```text
data/knowledge_base：保存原始知识文档
app/rag：保存处理这些文档的代码
```

## 为什么修改 .gitignore

仓库根目录原本有规则：

```text
data/
```

这类规则通常用于避免把本地临时数据、数据库文件、缓存文件提交到 Git。

但本节新增的：

```text
projects/ai-service/data/knowledge_base
```

不是临时数据，而是后续 RAG 学习主线要长期使用的样本知识库。

所以本节只增加精确例外：

```text
!projects/ai-service/data/
!projects/ai-service/data/knowledge_base/
!projects/ai-service/data/knowledge_base/*.md
!projects/ai-service/data/knowledge_base/*.txt
```

这样做的意思是：

```text
继续忽略普通 data 目录里的本地数据；
只允许这批学习用 Markdown/txt 样本文档进入 Git。
```

这比直接删除 `data/` 忽略规则更安全。

## 常见错误理解

### 错误 1：随便找一堆文档越多越好

不对。

初学阶段文档越多，问题越难定位。

如果检索结果不好，你不知道是：

```text
文档质量问题
chunk 切分问题
embedding 问题
Qdrant 查询问题
prompt 问题
```

所以一开始要用少量可控文档。

### 错误 2：RAG 文档只要给模型看就行，不需要结构

不对。

结构会影响：

```text
chunk 切分
metadata 提取
引用来源
检索质量
回答可解释性
```

标题、段落、列表都很重要。

### 错误 3：真实项目一定要从 PDF 开始

不对。

真实项目可能最终要支持 PDF，但学习主线应该先用 Markdown/txt 跑通。

PDF 解析是另一个复杂问题。

不要把“文档解析难题”和“RAG 主线学习”一开始就混在一起。

### 错误 4：metadata 可以以后再随便补

不完全对。

metadata 设计越晚，返工越多。

至少要提前考虑：

```text
source
title
doc_type
business_domain
permission_group
```

否则后面做 payload filter 和引用来源会很难。

### 错误 5：样本文档不需要测试

不对。

至少要保证：

```text
文件存在
文件非空
路径稳定
```

否则后面 loader 可能因为路径问题直接失败。

## 本节练习

### 练习 1：判断文档是否适合 RAG 入门

下面哪些文档适合作为 RAG 入门材料？

```text
1. 一篇 10 页 PDF 扫描件，里面很多图片和表格。
2. 一份 Markdown 格式的订单发货规则，标题和段落清楚。
3. 一个 500MB 的杂乱客服聊天记录导出。
4. 一份 txt 格式的物流 FAQ，每条都有“问题/回答”。
5. 一份没有标题、没有段落、内容混乱的长文本。
```

参考答案：

```text
2 和 4 更适合入门。

1 涉及 PDF 扫描件解析，初学阶段复杂度太高。
3 数据量大且杂乱，适合后期数据清洗专题，不适合作为第一批材料。
5 结构差，会影响 chunk 和检索，不适合入门。
```

### 练习 2：给文档设计 metadata

给定文档：

```text
文件名：shipping-delay-faq.md
标题：发货延迟常见问题
类型：FAQ
业务领域：订单
使用对象：客服
```

请设计 metadata。

参考答案：

```json
{
  "source": "shipping-delay-faq.md",
  "title": "发货延迟常见问题",
  "doc_type": "faq",
  "business_domain": "order",
  "permission_group": "customer_service"
}
```

解释：

```text
source 用于引用和排查。
title 用于展示和上下文。
doc_type 用于按文档类型过滤。
business_domain 用于按业务领域过滤。
permission_group 用于权限过滤。
```

### 练习 3：解释为什么文档要小而清楚

问题：

```text
为什么第一批 RAG 文档不应该一上来就很多、很复杂？
```

参考答案：

```text
因为初学阶段要先验证完整 RAG 主线。
少量清楚文档能降低排查难度。
如果检索失败，我们更容易判断是加载、切分、embedding、向量库还是 prompt 的问题。
大量复杂文档会把数据质量问题和代码问题混在一起。
```

### 练习 4：解释 Markdown 标题的价值

问题：

```text
Markdown 里的 # 和 ## 对 RAG 有什么帮助？
```

参考答案：

```text
# 和 ## 表示标题层级。
后续切 chunk 时可以把标题作为上下文保留，让 chunk 不只是孤立段落。
检索结果也可以用标题帮助模型理解来源和主题。
```

### 练习 5：判断文档属于哪类业务领域

请给下面问题匹配最可能的文档：

```text
1. 订单超过 72 小时没发货怎么办？
2. 退款一般多久到账？
3. 物流显示签收但用户没收到怎么办？
4. 忘记密码怎么办？
```

参考答案：

```text
1. order-shipping-policy.md
2. refund-return-policy.md
3. logistics-tracking-faq.txt
4. account-security-faq.md
```

## 自测问题

### 自测 1：本节为什么不需要打开虚拟机？

参考答案：

```text
因为本节只是准备本地知识文档，不访问 Qdrant，不启动 Docker，也不生成 embedding。
```

### 自测 2：为什么第一批文档选择 Markdown/txt？

参考答案：

```text
因为 Markdown/txt 都是纯文本，容易读取和清洗。Markdown 有标题结构，txt 简单直观，适合先跑通 RAG 主线。
```

### 自测 3：为什么不一开始用 PDF/Word？

参考答案：

```text
因为 PDF/Word 解析涉及复杂格式、表格、换行、图片、页眉页脚等问题，容易干扰 RAG 主线学习。先用 Markdown/txt 更容易定位问题。
```

### 自测 4：本节新增的知识文档放在哪里？

参考答案：

```text
projects/ai-service/data/knowledge_base
```

### 自测 5：为什么文档要有 metadata 线索？

参考答案：

```text
metadata 后续会成为 Qdrant payload，用于来源引用、文档类型过滤、业务领域过滤、权限过滤和问题排查。
```

### 自测 6：这批文档后面会怎么用？

参考答案：

```text
第 11 节加载成 RagDocument，第 12 节切成 RagChunk，第 13 节生成 embedding 并写入 Qdrant，后面用于检索、回答和引用来源。
```

### 自测 7：样本文档为什么也要测试？

参考答案：

```text
为了保证后续学习依赖的输入材料存在且非空。这样后面写 loader 时，不会因为文件漏提交或路径错误导致基础流程失败。
```

## 本节复盘

这一节你要真正掌握的是：

```text
1. RAG 需要先有高质量、可控的知识文档。
2. 初学阶段优先用 Markdown/txt，降低解析复杂度。
3. 文档标题、段落、列表和 FAQ 格式会影响后续 chunk 切分。
4. metadata 线索会影响后续 Qdrant payload、filter 和引用来源。
5. 第一批文档应该少而清楚，便于排查 RAG 主线问题。
6. data/knowledge_base 保存原始知识文档，app/rag 保存处理文档的代码。
7. 本节文档会在后续第 11-18 节持续使用。
```

下一节可以进入：

```text
阶段 4 第 11 节：文档加载和文本清洗。
```
