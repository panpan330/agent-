# 阶段 4 第 37 节：RAG 检索评测基础

> 本节目标：理解为什么 RAG 不能只靠“感觉搜得不错”，掌握检索评测集、Recall@K、Precision@K、Hit Rate、MRR、bad case 分析，以及如何为当前知识库设计最小但有效的检索评测。

## 0. 本节学习地图

前面我们已经完成了 RAG 的大部分主线能力：

```text
文档加载
-> chunk 切分
-> embedding
-> Qdrant 入库
-> top_k 检索
-> payload filter
-> score_threshold
-> 混合检索
-> rerank
-> 安全检查
-> 把检索结果交给模型回答
-> 引用来源
-> 无资料兜底
```

还补了 Milvus：

```text
Milvus 本地启动
-> schema / entity / index
-> 入库
-> 向量检索
-> metadata filter
-> scalar index
-> Qdrant vs Milvus 选型
```

到这里，你已经能“做一个 RAG”。

但还有一个非常关键的问题：

```text
怎么判断它做得好不好？
```

如果只靠手动问几句：

```text
退货运费谁承担？
物流怎么查？
账号被盗怎么办？
```

然后看返回结果“好像还行”，这不叫评测，只叫试用。

真正的 RAG 工程需要回答：

- 这个 query 期望命中哪个文档？
- 期望命中哪个 chunk？
- top_k=3 时命中了吗？
- top_k=5 比 top_k=3 好多少？
- 换 chunk_size 后检索效果变好还是变差？
- 加 score_threshold 后有没有误伤相关内容？
- 加 metadata filter 后有没有把正确资料过滤掉？
- rerank 之后第一个结果是不是更可靠？
- 错误样本集中在哪些业务类型？

本节先学评测基础，不写脚本。下一节第 38 节再把这些概念落到当前项目的最小评测脚本里。

学完本节，你应该能解释：

1. RAG 检索评测和生成评测有什么区别。
2. 什么是评测集。
3. 什么是 query、expected source、expected chunk、relevance judgment。
4. 什么是 Recall@K。
5. 什么是 Precision@K。
6. 什么是 Hit Rate。
7. 什么是 MRR。
8. 为什么一个指标不够，要组合看。
9. 为什么 bad case 分析比单个平均分更能指导改进。
10. 当前项目最小评测集应该怎么设计。

本节暂时不学：

- LLM-as-a-judge 自动打分细节；
- Ragas/LangSmith 的完整平台使用；
- nDCG、MAP 的复杂实现；
- 大规模人工标注流程；
- 线上 A/B test；
- 真实 embedding 模型评测脚本；
- Qdrant/Milvus 实机评测脚本。

这些后续再逐步补。

## 1. 基础知识铺垫

### 1.1 什么是评测

评测就是：

```text
用一组固定问题和固定判断标准，衡量系统输出是否达到预期。
```

它和“随便试一下”最大的区别是：

| 随便试一下 | 正式评测 |
| --- | --- |
| 问题临时想 | 问题固定保存 |
| 结果靠感觉 | 结果有标准 |
| 今天和明天不可比较 | 每次运行可比较 |
| 很难定位退步 | 能发现哪类问题变差 |
| 适合快速体验 | 适合工程迭代 |

RAG 评测的意义是：

```text
让系统质量从主观感觉变成可观察、可比较、可改进。
```

### 1.2 为什么 RAG 特别需要评测

普通接口功能比较容易测。

例如：

```text
GET /health 应该返回 200
```

这类测试只有明确结果：

```text
通过 / 不通过
```

RAG 不一样。

用户问：

```text
退货运费谁承担？
```

系统可能返回：

```text
退款退货规则 chunk 5
退款到账时间 chunk 4
七天无理由退货 chunk 2
```

哪一个最好？

如果 top 3 里有正确 chunk，但排在第 3，算好吗？

如果 top 5 里有正确文档，但没有正确 section，算好吗？

如果检索到了正确资料，但最终模型没引用，问题出在检索还是生成？

这些都需要评测方法拆开看。

### 1.3 RAG 评测要拆成两层

RAG 至少有两层评测：

```text
检索评测
生成评测
```

检索评测看：

```text
retriever 找到的资料对不对
```

生成评测看：

```text
generator 有没有基于资料回答好
```

两者不要混在一起。

因为最终答案不好，原因可能有很多：

| 现象 | 可能原因 |
| --- | --- |
| 答案胡说 | 检索没找到资料，或模型没按资料回答 |
| 答案缺关键条件 | 检索漏掉了必要 chunk |
| 答案有资料但不完整 | top_k 太小，或 chunk 切得太碎 |
| 答案引用错误 | citation 构造或上下文对应关系有问题 |
| 答案很啰嗦 | prompt 和生成控制问题 |

如果不拆开，你不知道该改：

- chunk_size；
- embedding 模型；
- top_k；
- filter；
- rerank；
- prompt；
- 模型；
- citation 逻辑。

本节只聚焦第一层：

```text
检索评测
```

### 1.4 retriever 和 generator 的边界

在我们的项目里，retriever 大概负责：

```text
用户问题
-> query embedding
-> vector store query
-> metadata filter
-> score_threshold
-> 返回 RetrievedChunk 列表
```

generator 负责：

```text
RetrievedChunk 列表
-> 拼成上下文
-> 调用模型
-> 输出回答
-> 返回 citations
```

所以检索评测先不问：

```text
模型回答得好不好？
```

而是先问：

```text
正确资料有没有被找回来？
正确资料排得够不够靠前？
错误资料有没有混太多？
```

这就是本节的核心。

### 1.5 什么是评测集

评测集是一组固定样本。

每个样本至少包含：

```text
query
expected
```

对 RAG 检索来说，一个样本可以是：

```yaml
query: "退货运费谁承担？"
expected_sources:
  - "refund-return-policy.md"
expected_sections:
  - "运费处理"
expected_chunk_ids:
  - "refund_return_policy_chunk_0005"
```

含义是：

```text
当用户这样问时，我希望检索结果里至少包含这个来源、这个章节或这个 chunk。
```

### 1.6 query 是什么

query 是用户问题，也就是检索入口。

但评测 query 不应该只写标准书面问法。

同一个意图可以有很多问法：

```text
退货运费谁承担？
我不想要了退货邮费谁出？
七天无理由退货要我自己付运费吗？
商品质量问题退货运费算谁的？
```

这些 query 可能都和退款退货相关，但对应答案可能略有区别。

评测集里应该覆盖：

- 标准问法；
- 口语问法；
- 模糊问法；
- 带条件问法；
- 容易混淆的问法；
- 无资料问题。

### 1.7 expected source 是什么

`expected source` 是期望命中的文档来源。

例如：

```text
refund-return-policy.md
```

这是最粗粒度的检索评测。

优点：

- 标注简单；
- 不容易受 chunk 切分变化影响；
- 适合评测早期。

缺点：

- 太粗；
- 命中文档不等于命中正确段落；
- 同一文档里可能有多个主题。

所以早期可以先用 source 级评测，后面再细到 section 或 chunk。

### 1.8 expected section 是什么

`expected section` 是期望命中的文档章节。

例如：

```text
运费处理
退款到账时间
发货异常工单
身份验证
```

它比 source 更细。

如果用户问：

```text
退货运费谁承担？
```

命中：

```text
refund-return-policy.md / 运费处理
```

比只命中：

```text
refund-return-policy.md / 七天无理由退货
```

更准确。

section 级评测适合我们的当前项目，因为我们已经在 metadata 里保存了 `section`。

### 1.9 expected chunk 是什么

`expected chunk` 是最细粒度。

例如：

```text
refund_return_policy_chunk_0005
```

它的优点是判断最明确：

```text
检索结果里有没有这个 chunk_id
```

缺点是：

- chunk_size 改了，chunk_id 可能变化；
- 文档内容改了，chunk 可能变化；
- 一个问题可能有多个正确 chunk；
- 过细标注成本更高。

所以 chunk 级评测适合稳定阶段，不一定适合一开始就全面使用。

### 1.10 relevant 是什么

`relevant` 表示“相关”。

检索评测中最基础的判断是：

```text
某个 retrieved chunk 对某个 query 是否相关？
```

可以简单二分类：

```text
1 = 相关
0 = 不相关
```

也可以做多级：

```text
2 = 非常相关，直接回答问题
1 = 有点相关，辅助回答
0 = 不相关
```

本阶段先用二分类更适合。

因为初学时要先把评测链路跑通：

```text
命中 / 未命中
```

不要一开始就引入复杂人工打分。

### 1.11 什么是 K

`K` 指检索返回前多少条。

例如：

```text
top_k=3
```

表示只看前 3 条检索结果。

`Recall@3`、`Precision@3`、`Hit Rate@3`、`MRR@3` 都是在前 3 条结果里计算。

为什么要固定 K？

因为用户和模型都不会无限看结果。

RAG 里通常只会把前几条 chunk 放进模型上下文：

```text
top_k=3
top_k=5
top_k=8
```

如果正确资料排在第 50 名，理论上“检索到了”，但实际没用。

### 1.12 为什么只看平均分不够

假设 10 个问题平均 Recall@3 是 0.8。

看起来不错。

但可能实际情况是：

```text
退款类 5 个问题全对
物流类 3 个问题全对
账号安全 2 个问题全错
```

平均分掩盖了账号安全类的失败。

所以评测结果不能只看总平均，还要看：

- 按业务域拆分；
- 按 query 类型拆分；
- 看失败样本；
- 看排名；
- 看返回了哪些干扰 chunk；
- 看 filter 是否误伤；
- 看错误是否集中在某个文档。

这就是 bad case 分析。

## 2. 本节主题系统讲解

### 2.1 检索评测的最小流程

最小检索评测流程是：

```text
准备评测集
-> 对每个 query 调用 retriever
-> 得到 top_k retrieved chunks
-> 和 expected 做匹配
-> 计算指标
-> 输出总分和失败样本
```

具体一点：

```text
query: "退货运费谁承担？"
expected_chunk_ids: ["refund_return_policy_chunk_0005"]

retrieved:
1. refund_return_policy_chunk_0002
2. refund_return_policy_chunk_0004
3. refund_return_policy_chunk_0005

top_k=3
hit: yes
rank: 3
```

这个样本：

- Hit Rate@3 算命中；
- Recall@3 算找回了 1/1；
- MRR 的 reciprocal rank 是 1/3；
- Precision@3 是 1/3。

### 2.2 Hit Rate@K

Hit Rate@K 问的是：

```text
前 K 条结果里有没有至少一个正确结果？
```

如果有，就是 1。

如果没有，就是 0。

对单个 query：

```text
Hit@K = 1 if top K contains any relevant result else 0
```

对多个 query：

```text
Hit Rate@K = 命中的 query 数量 / query 总数量
```

例子：

| query | top 3 是否命中 |
| --- | --- |
| Q1 | 是 |
| Q2 | 是 |
| Q3 | 否 |
| Q4 | 是 |

则：

```text
Hit Rate@3 = 3 / 4 = 0.75
```

Hit Rate 很适合 RAG 早期。

因为很多问题只要找回一个关键 chunk，生成阶段就有机会回答。

但它也有缺点：

```text
只关心有没有命中，不关心命中了几个，也不太关心排第几。
```

### 2.3 Recall@K

Recall@K 问的是：

```text
所有应该找回的相关结果里，前 K 条找回了多少？
```

公式：

```text
Recall@K = top K 中相关结果数量 / 该 query 的相关结果总数量
```

例子：

某 query 期望相关 chunk 有 2 个：

```text
expected = [A, B]
```

检索 top 3：

```text
[A, C, D]
```

命中了 A，没有命中 B。

所以：

```text
Recall@3 = 1 / 2 = 0.5
```

如果 top 5：

```text
[A, C, D, B, E]
```

则：

```text
Recall@5 = 2 / 2 = 1.0
```

Recall@K 适合回答：

```text
重要资料有没有被找回来？
```

RAG 中 Recall 很重要，因为：

```text
如果检索阶段没找回资料，生成阶段再强也没法基于正确资料回答。
```

### 2.4 Precision@K

Precision@K 问的是：

```text
前 K 条结果里，有多少比例是相关的？
```

公式：

```text
Precision@K = top K 中相关结果数量 / K
```

例子：

某 query 的 top 5：

```text
[A相关, B不相关, C相关, D不相关, E不相关]
```

相关结果数量是 2。

所以：

```text
Precision@5 = 2 / 5 = 0.4
```

Precision@K 适合回答：

```text
返回给模型的上下文里，噪声多不多？
```

RAG 里 precision 低会导致：

- 模型读到无关资料；
- 回答跑偏；
- 上下文窗口浪费；
- 引用来源不干净；
- rerank 压力变大。

但 Precision@K 也不能单独看。

如果 top_k 很小，Precision 可能高，但 Recall 很低。

例如只返回 1 条：

```text
top_k=1
```

这 1 条刚好相关：

```text
Precision@1 = 1.0
```

但如果这个问题需要 3 条资料才能完整回答，Recall 可能只有：

```text
Recall@1 = 1 / 3 = 0.33
```

### 2.5 Recall 和 Precision 的取舍

Recall 和 Precision 经常互相拉扯。

top_k 变大：

- 更容易找回相关资料；
- Recall 往往上升；
- 但无关资料也可能增加；
- Precision 可能下降；
- 模型上下文更长，成本更高。

top_k 变小：

- 上下文更干净；
- Precision 可能上升；
- 但可能漏掉必要资料；
- Recall 可能下降。

RAG 调参就是在问：

```text
我需要多找一点，还是少而准一点？
```

客服知识库通常更看重：

```text
先不要漏掉关键政策，再通过 rerank/score_threshold 控制噪声。
```

### 2.6 MRR

MRR 是 Mean Reciprocal Rank。

它关注：

```text
第一个相关结果排在第几名？
```

对单个 query：

```text
Reciprocal Rank = 1 / 第一个相关结果的排名
```

如果第一个相关结果在第 1 名：

```text
RR = 1 / 1 = 1.0
```

如果在第 2 名：

```text
RR = 1 / 2 = 0.5
```

如果在第 5 名：

```text
RR = 1 / 5 = 0.2
```

如果 top_k 里没有相关结果：

```text
RR = 0
```

多个 query 的平均值就是 MRR。

MRR 适合回答：

```text
正确资料是不是尽量排在前面？
```

RAG 里 MRR 很有用，因为模型通常更重视靠前的上下文，或者我们的上下文拼接顺序会让靠前 chunk 更显眼。

### 2.7 用一个例子同时算四个指标

假设某 query 有 2 个正确 chunk：

```text
expected = [B, D]
```

检索 top 5：

```text
rank 1: A 不相关
rank 2: B 相关
rank 3: C 不相关
rank 4: D 相关
rank 5: E 不相关
```

Hit Rate@5：

```text
前 5 有相关结果 -> 1
```

Recall@5：

```text
找回 B 和 D，共 2 个；expected 也是 2 个
Recall@5 = 2 / 2 = 1.0
```

Precision@5：

```text
前 5 有 2 个相关
Precision@5 = 2 / 5 = 0.4
```

MRR@5：

```text
第一个相关结果 B 在 rank 2
RR = 1 / 2 = 0.5
```

这个结果说明：

```text
资料找全了，但排序不够好，噪声也不少。
```

所以改进方向可能是：

- rerank；
- 优化 query embedding；
- 调整 chunk；
- 加更精确的 metadata filter；
- 降低 top_k 后观察 Recall 是否还能保住。

### 2.8 为什么 RAG 早期先看 Hit Rate 和 Recall@K

RAG 早期最常见问题是：

```text
正确资料根本没进上下文。
```

所以先看：

- Hit Rate@K；
- Recall@K；
- bad cases。

如果这两个指标很差，先不要急着优化 prompt。

因为模型没有资料，prompt 再好也可能只是更有礼貌地胡说或拒答。

早期指标优先级建议：

```text
Hit Rate@K / Recall@K
-> MRR
-> Precision@K
-> 更复杂的 nDCG/MAP/LLM 评测
```

### 2.9 检索评测和生成评测怎么配合

完整 RAG 评测可以分三层：

```text
1. Retriever 评测：找没找到正确资料
2. Generator 评测：基于资料回答得好不好
3. End-to-end 评测：用户最终体验好不好
```

例子：

| 检索结果 | 生成结果 | 判断 |
| --- | --- | --- |
| 正确资料没找回 | 答案错 | 先修 retriever |
| 正确资料找回 | 答案错 | 修 prompt/model/generator |
| 正确资料找回 | 答案对但没引用 | 修 citation |
| 正确资料找回但噪声很多 | 答案混乱 | 修 precision/rerank |

所以检索评测不是最终目标，但它是定位问题的第一层。

### 2.10 评测集怎么设计

一个好的小型评测集应该覆盖：

1. 常见问题。
2. 高频业务。
3. 容易混淆的问题。
4. 需要 metadata filter 的问题。
5. 无资料问题。
6. 需要多个 chunk 才能回答的问题。
7. 口语化问法。
8. 不同文档类型。

当前知识库有：

```text
refund-return-policy.md
order-shipping-policy.md
logistics-tracking-faq.txt
account-security-faq.md
```

最小评测集可以先做 12 条：

| 类型 | 数量 |
| --- | --- |
| 退款退货 | 3 |
| 订单发货 | 3 |
| 物流查询 | 2 |
| 账号安全 | 2 |
| 容易混淆 | 1 |
| 无资料问题 | 1 |

这样比只问 3 个问题可靠很多。

### 2.11 评测样本应该长什么样

下一节我们会落代码，这里先设计结构。

一个样本可以长这样：

```json
{
  "id": "refund_shipping_fee_001",
  "query": "退货运费谁承担？",
  "expected_sources": ["refund-return-policy.md"],
  "expected_sections": ["运费处理"],
  "expected_chunk_ids": ["refund_return_policy_chunk_0005"],
  "business_domain": "refund",
  "permission_group": "customer_service",
  "notes": "应命中退款退货规则里的运费处理段落"
}
```

字段解释：

| 字段 | 作用 |
| --- | --- |
| `id` | 样本唯一编号 |
| `query` | 用户问题 |
| `expected_sources` | 期望命中文档 |
| `expected_sections` | 期望命中章节 |
| `expected_chunk_ids` | 期望命中 chunk |
| `business_domain` | 检索过滤条件 |
| `permission_group` | 权限过滤条件 |
| `notes` | 人类解释，方便 bad case 分析 |

### 2.12 评测粒度怎么选

三种常见粒度：

| 粒度 | 优点 | 缺点 | 当前建议 |
| --- | --- | --- | --- |
| source 级 | 稳定、标注简单 | 太粗 | 必须有 |
| section 级 | 适合业务知识定位 | 依赖 section metadata | 推荐有 |
| chunk 级 | 最精确 | chunk 变化会影响标注 | 少量核心样本使用 |

当前项目建议：

```text
source 级 + section 级为主
chunk 级为辅
```

原因是我们还会继续调整 chunk 策略。如果所有评测都强绑定 chunk_id，后续改 chunk_size 会导致评测集维护成本很高。

### 2.13 评测集不是越大越好

初学阶段不要一开始写 200 条样本。

更合理：

```text
先写 10-20 条高质量样本
-> 每次改检索逻辑都跑
-> 从 bad case 里补新样本
-> 慢慢扩充到 50 条、100 条
```

评测集增长应该来自真实问题和失败案例，而不是为了数量好看。

### 2.14 bad case 是什么

bad case 就是评测失败样本。

例如：

```text
query: 商品质量问题退货运费谁出？
expected_section: 运费处理
retrieved_top3:
1. 七天无理由退货
2. 退款到账时间
3. 账号身份验证
```

这个失败需要分析：

- 是 query 语义表达问题吗？
- 是 chunk 切分导致“运费处理”内容太短吗？
- 是 fake embedding 表达能力太弱吗？
- 是 top_k 太小吗？
- 是 metadata filter 错了吗？
- 是文档本身写得不清楚吗？

bad case 不是为了证明系统差，而是为了指导下一步改进。

### 2.15 bad case 应该怎么记录

每个 bad case 至少记录：

```text
query
expected
retrieved results
miss reason
next action
```

例子：

```text
query: 商品质量问题退货运费谁出？
expected: refund-return-policy.md / 运费处理
retrieved: 七天无理由退货、退款到账时间、账号身份验证
miss reason: 相关 chunk 排名太低，fake embedding 对“运费”和“质量问题”的语义区分弱
next action: 尝试真实 embedding，或增加关键词混合检索权重
```

这比单纯说：

```text
Recall@3 = 0.67
```

更能指导工程修改。

### 2.16 常见失败原因分类

RAG 检索失败常见原因：

| 原因 | 表现 | 可能改进 |
| --- | --- | --- |
| query 太口语 | 标准文档没命中 | query rewrite、真实 embedding |
| chunk 太大 | 一个 chunk 混多个主题 | 减小 chunk_size、标题感知 |
| chunk 太小 | 关键上下文分散 | 增加 overlap、提高 top_k |
| metadata 错 | filter 后正确资料被排除 | 修 metadata |
| top_k 太小 | 正确资料排第 4/5 | 调大 top_k、rerank |
| score_threshold 太高 | 相关资料被过滤掉 | 调低阈值 |
| embedding 弱 | 语义相近但召回差 | 换真实 embedding |
| 同义词问题 | “邮费”和“运费”匹配差 | hybrid search、同义词扩展 |
| 文档写得差 | 没有明确答案 | 改知识文档 |

这张表很重要。以后你看到指标下降，不能只会调 `top_k`，要能定位原因。

### 2.17 为什么 fake embedding 下评测仍然有意义

我们当前很多 smoke 使用 deterministic fake embedding。

它不是语义模型，不能代表真实检索效果。

那为什么还要评测？

因为在 fake embedding 下仍然可以评测：

- 评测脚本逻辑是否正确；
- filter 是否生效；
- top_k 是否传对；
- score_threshold 是否影响结果；
- 返回字段是否完整；
- 指标计算是否正确；
- bad case 报告是否可读。

但要明确边界：

```text
fake embedding 评测不能证明真实语义检索质量。
```

真正判断语义检索效果，后面要接真实 embedding。

### 2.18 为什么评测不能只看最终答案

假设最终答案是错的。

如果只看答案，你不知道哪里错。

可能是：

```text
retriever 没找回资料
generator 没读懂资料
prompt 没限制住模型
引用来源构造错误
metadata filter 误过滤
```

再假设最终答案是对的。

也不代表检索一定好。

模型可能凭常识答对，或者训练数据里知道答案，但这不是企业 RAG 的可靠能力。

所以必须把检索单独评测。

### 2.19 当前项目第 38 节会怎么落地

下一节我们会新增一个最小评测脚本，大概结构是：

```text
data/rag_eval/retrieval_cases.json
scripts/rag_retrieval_eval.py
app/rag/evaluation.py
tests/test_rag_evaluation.py
```

它会做：

```text
读取评测样本
-> 调用 retriever
-> 比对 source/section/chunk_id
-> 计算 Hit Rate@K、Recall@K、Precision@K、MRR
-> 输出 bad cases
```

具体文件名下一节以项目实际结构为准。

本节先不写，是为了避免你还没理解指标，就先陷入代码细节。

## 3. 指标对照表

| 指标 | 问的问题 | 优点 | 缺点 |
| --- | --- | --- | --- |
| Hit Rate@K | 前 K 条里有没有至少一个正确结果 | 简单、适合 RAG 早期 | 不关心命中几个、不关心噪声 |
| Recall@K | 应该找回的结果里找回了多少 | 能衡量漏没漏关键资料 | 不关心无关结果多不多 |
| Precision@K | 前 K 条里相关结果比例多少 | 能衡量上下文噪声 | top_k 小时可能虚高 |
| MRR@K | 第一个正确结果排多靠前 | 能衡量排序质量 | 只关心第一个相关结果 |
| bad case 列表 | 哪些样本失败，为什么失败 | 最能指导改进 | 需要人工分析 |

当前项目最优先：

```text
Hit Rate@3
Recall@3
MRR@3
bad cases
```

再观察：

```text
Precision@3
Hit Rate@5
Recall@5
```

## 4. 练习

### 练习 1：计算 Hit Rate@3

有 5 个 query，top 3 是否命中如下：

```text
Q1 命中
Q2 未命中
Q3 命中
Q4 命中
Q5 未命中
```

请计算 Hit Rate@3。

### 练习 2：计算 Recall@5

某 query 有 3 个相关 chunk：

```text
expected = [A, B, C]
```

检索 top 5：

```text
[D, A, E, C, F]
```

请计算 Recall@5。

### 练习 3：计算 Precision@5

沿用练习 2 的结果：

```text
[D, A, E, C, F]
```

其中 A、C 相关，其余不相关。请计算 Precision@5。

### 练习 4：计算 MRR

三个 query 的第一个相关结果排名如下：

```text
Q1 rank 1
Q2 rank 4
Q3 top 5 未命中
```

请计算 MRR@5。

### 练习 5：判断问题应该先修哪里

某 RAG 系统出现：

```text
检索 top 5 里没有任何相关 chunk，但模型最终回答看起来还可以。
```

这个系统应该先优化 retriever 还是 generator？为什么？

## 5. 练习参考答案

### 答案 1

5 个 query 里命中 3 个。

所以：

```text
Hit Rate@3 = 3 / 5 = 0.6
```

### 答案 2

expected 有 3 个：

```text
A, B, C
```

top 5 找回了：

```text
A, C
```

找回 2 个。

所以：

```text
Recall@5 = 2 / 3 = 0.6667
```

### 答案 3

top 5 一共 5 条，其中相关 2 条。

所以：

```text
Precision@5 = 2 / 5 = 0.4
```

### 答案 4

Q1：

```text
RR = 1 / 1 = 1
```

Q2：

```text
RR = 1 / 4 = 0.25
```

Q3 未命中：

```text
RR = 0
```

所以：

```text
MRR@5 = (1 + 0.25 + 0) / 3 = 0.4167
```

### 答案 5

应该先优化 retriever。

原因是：

```text
top 5 里没有相关 chunk，说明正确资料没有进入模型上下文。
```

模型回答看起来还可以，可能是模型凭常识或训练数据答出来的，但这不是企业 RAG 可靠性。企业 RAG 的目标是基于知识库资料回答。如果检索没找回资料，就应该先修检索链路，例如 embedding、chunk、metadata filter、top_k、score_threshold、hybrid search 或 rerank。

## 6. 自测题

### 自测 1

RAG 检索评测和生成评测分别看什么？

### 自测 2

为什么 Recall@K 对 RAG 很重要？

### 自测 3

Precision@K 高是否一定代表 RAG 系统好？为什么？

### 自测 4

MRR 高说明什么？

### 自测 5

为什么 bad case 分析不能被平均分替代？

### 自测 6

当前项目最小评测集为什么建议先用 source/section 级，而不是全部强绑定 chunk_id？

## 7. 自测题参考答案

### 自测 1 答案

检索评测看 retriever 找到的资料对不对、全不全、排得靠不靠前、噪声多不多。

生成评测看 generator 是否基于资料回答、答案是否正确、是否幻觉、是否引用正确、是否表达清楚。

两者要分开看，因为最终答案不好不一定是同一个环节的问题。

### 自测 2 答案

Recall@K 重要是因为 RAG 的生成阶段依赖检索上下文。如果正确资料没有被检索进前 K 条，模型通常无法可靠地基于知识库回答。尤其是企业知识库，漏掉关键政策或流程会直接导致错误回答。

### 自测 3 答案

不一定。

Precision@K 高只说明前 K 条里相关比例高，但它不保证所有必要资料都被找回。如果 top_k 很小，Precision 可能很高，但 Recall 很低，系统仍然会漏掉重要信息。

所以 Precision 要和 Recall、Hit Rate、MRR、bad case 一起看。

### 自测 4 答案

MRR 高说明第一个相关结果通常排得比较靠前。

这对 RAG 很有用，因为模型通常优先看到靠前的上下文，或者靠前 chunk 更可能被用于回答和引用。

但 MRR 主要关注第一个相关结果，不代表所有必要资料都找全了。

### 自测 5 答案

平均分只能说明整体趋势，不能告诉你具体哪类问题失败。

例如平均 Recall@3 是 0.8，但可能账号安全类问题全错，退款类问题全对。只有看 bad case，才能知道下一步应该改 metadata、chunk、embedding、filter、rerank 还是知识文档。

### 自测 6 答案

因为当前项目后续还可能调整 chunk_size、overlap 和切分策略。chunk_id 可能随着切分变化而变化。如果全部强绑定 chunk_id，评测集维护成本会很高。

source/section 级更稳定，适合当前阶段。少量关键问题可以保留 chunk_id 级评测，用来检查最核心的命中能力。

## 8. 本节小结

本节的核心不是记公式，而是建立一个工程判断：

```text
RAG 不能只靠感觉判断好不好。
检索质量必须用固定评测集和固定指标持续观察。
```

你现在应该能说清：

- 检索评测看的是资料有没有找对；
- 生成评测看的是模型有没有基于资料答好；
- Hit Rate@K 看有没有命中；
- Recall@K 看重要资料找回多少；
- Precision@K 看上下文噪声多少；
- MRR 看第一个正确结果排得多靠前；
- bad case 分析决定下一步怎么改；
- 当前项目应该先设计小而高质量的评测集。

下一节建议进入：

```text
阶段 4 第 38 节：给当前 RAG 项目做一个最小检索评测脚本
```

第 38 节会真正新增评测样本、评测指标计算函数、脚本和测试，把本节方法落到当前项目里。

## 9. 本节参考资料

资料核对日期：2026-07-18。

- [Stanford IR Book: Evaluation in information retrieval](https://nlp.stanford.edu/IR-book/pdf/08eval.pdf)
- [Stanford CS276 Evaluation handout](https://web.stanford.edu/class/cs276/handouts/EvaluationNew-handout-1-per.pdf)
- [LangSmith: Evaluate a RAG application](https://docs.langchain.com/langsmith/evaluate-rag-tutorial)
- [Ragas Metrics: Component-wise evaluation](https://docs.ragas.io/en/v0.1.21/concepts/metrics/)
- [Ragas Context Precision](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/)
- [Ragas Context Recall](https://docs.ragas.io/en/latest/concepts/metrics/available_metrics/context_recall/)
