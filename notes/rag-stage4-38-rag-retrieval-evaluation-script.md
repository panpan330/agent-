# 阶段 4 第 38 节：给当前 RAG 项目做一个最小检索评测脚本

## 本节学习目标

这一节要把上一节的“RAG 检索评测基础”真正落到当前项目里。

学完这一节，你应该能做到：

1. 知道为什么 RAG 项目不能只靠“我试了几个问题，感觉还行”判断检索质量。
2. 知道什么是固定评测样本，为什么它必须能重复运行。
3. 知道一次检索评测最少需要哪些数据：query、expected target、retrieved chunks、top_k、metric。
4. 能解释 Hit Rate@K、Recall@K、Precision@K、MRR@K 在代码里是怎么计算出来的。
5. 能解释为什么本节先评测 retrieval，不急着评测最终 answer。
6. 能解释为什么本节评测脚本先使用本地关键词检索，不依赖 Qdrant、Milvus、真实 embedding 或真实大模型。
7. 能看懂 bad case 报告，并知道 bad case 对后续调参、改 chunk、改检索策略有什么意义。

本节对应产出：

- `projects/ai-service/app/rag/evaluation.py`
- `projects/ai-service/data/rag_eval/retrieval_cases.json`
- `projects/ai-service/data/rag_eval/README.md`
- `projects/ai-service/scripts/rag_retrieval_eval.py`
- `projects/ai-service/tests/test_rag_evaluation.py`

## 本节先不学什么

为了把基础打扎实，本节有意不引入下面这些内容：

1. 不真实调用大模型 embedding。
2. 不连接 Qdrant 或 Milvus。
3. 不做 LLM-as-a-judge。
4. 不评测最终答案是否正确。
5. 不引入 Ragas、LangSmith 之类的评测框架。
6. 不做复杂统计显著性分析。
7. 不做线上 A/B test。

原因很简单：初学阶段最重要的是先把“检索评测的最小闭环”理解透。只要这个闭环会了，后面把检索器从关键词换成 Qdrant、Milvus、混合检索、rerank，都只是替换输入来源，评测思想不变。

## 一、基础知识铺垫

### 1. 什么是检索评测

RAG 的核心链路可以简化成：

```text
用户问题 -> 检索器找资料 -> 把资料交给模型 -> 模型生成回答
```

其中“检索器找资料”这一步如果错了，后面的模型很难答对。

例如用户问：

```text
退货运费谁承担？
```

如果检索器找回的是“账号安全 FAQ”，模型即使再强，也会遇到两个问题：

1. 模型可能根据错误资料胡乱回答。
2. 模型可能发现资料不相关，然后只能拒答或兜底。

所以 RAG 评测不能只看最终回答，还要单独看检索器到底有没有把正确资料找回来。

检索评测就是在回答这个问题：

```text
对一批固定问题，检索器有没有把我们期望的资料排在 top_k 结果里？
```

### 2. 为什么要固定评测样本

如果每次都临时问几个问题，结果就很难比较。

今天你问：

```text
退款多久到账？
```

明天你问：

```text
商品退货怎么处理？
```

如果今天效果好、明天效果差，你无法判断是检索器退步了，还是问题本身变难了。

固定评测样本的作用是：

```text
每次都用同一批问题，观察不同版本代码的检索质量变化。
```

这和考试很像。一次考试如果每个人题目都不一样，分数就很难公平比较。检索评测也是一样，样本固定以后，才有“版本 A 比版本 B 好还是差”的判断基础。

本节新增的样本文件是：

```text
projects/ai-service/data/rag_eval/retrieval_cases.json
```

它保存了 12 个检索评测样本。每个样本大致包含：

```json
{
  "id": "refund_shipping_fee_001",
  "query": "退货运费谁承担？",
  "expected_sources": ["refund-return-policy.md"],
  "expected_sections": ["运费处理"],
  "expected_chunk_ids": ["refund_return_policy_chunk_0005"],
  "permission_group": "customer_service",
  "business_domain": "refund",
  "notes": "..."
}
```

这些字段不是随便写的，每个字段都有评测意义。

### 3. query 是什么

`query` 就是用户可能真的会问的问题。

评测样本里的 query 不应该只写成文档标题，也不应该只写成关键词堆砌。因为真实用户不会总是输入标准标题。

例如知识库里可能有章节：

```text
## 运费处理
```

但用户可能会问：

```text
退货运费谁承担？
质量问题退货邮费谁出？
```

这两个问题表达不同，但都可能应该命中同一个规则。

所以评测 query 的设计要尽量接近真实用户问题，而不是只复制文档里的原文标题。

### 4. expected target 是什么

`expected target` 可以理解成“这个问题应该命中的标准答案位置”。

在本节里，我们支持三种粒度：

1. `expected_chunk_ids`
2. `expected_sections`
3. `expected_sources`

它们从精确到宽松分别是：

```text
chunk_id 最精确
section 次精确
source 最宽松
```

举例：

```text
expected_chunk_ids = ["refund_return_policy_chunk_0005"]
```

表示这个问题最好命中特定 chunk。

```text
expected_sections = ["运费处理"]
```

表示只要命中“运费处理”这个章节，就认为找对方向。

```text
expected_sources = ["refund-return-policy.md"]
```

表示只要命中“退款退货规则”这份文档，就算粗粒度命中。

实际项目中，标注越精确，评测越严格；标注越宽松，评测越容易通过，但发现问题的能力也会变弱。

### 5. 为什么 chunk_id 是最强匹配

RAG 最终交给模型的不是整份文档，而是 chunk。

如果一个文档有 20 个 chunk，只有其中一个 chunk 讲“退货运费”，检索器返回同一文档里讲“退款到账时间”的 chunk，严格来说也不能算完全正确。

所以当样本里写了 `expected_chunk_ids`，评测器会优先按 chunk_id 判断。

这意味着：

```text
只要 expected_chunk_ids 存在，就不再用 source 粗略放水。
```

这样设计是为了避免一个常见误判：

```text
检索器找到了正确文档，但找错了文档里的具体位置。
```

对 RAG 来说，这种情况仍然可能导致回答错误。

### 6. 为什么 section 匹配还要配合 source

有些文档可能有相同章节名。

例如：

```text
refund-return-policy.md 里有 “处理流程”
order-shipping-policy.md 里也可能有 “处理流程”
```

如果只按 section 判断，检索器命中错误文档里的同名章节，也会被误判为正确。

所以本节的逻辑是：

```text
如果 expected_sections 和 expected_sources 同时存在：
必须 section 对得上，source 也要在 expected_sources 里。
```

这叫“额外门槛”。它让 section 匹配更稳。

### 7. no-result case 是什么

不是所有问题都应该返回资料。

例如当前知识库主要覆盖：

- 退款退货
- 订单发货
- 物流查询
- 账号安全

如果用户问：

```text
会员积分怎么兑换？
```

当前知识库没有对应资料。一个负责任的 RAG 系统应该识别“没有资料”，而不是强行返回不相关 chunk。

这类样本叫：

```text
no-result case
```

本节样本里有：

```json
{
  "id": "no_context_membership_points_001",
  "query": "会员积分怎么兑换？",
  "expect_no_results": true
}
```

它的评测目标不是“找回某个 chunk”，而是“不要乱返回”。

### 8. top_k 是什么

`top_k` 表示检索器最多返回前 K 条结果。

如果 `top_k=3`，检索结果可以理解成：

```text
第 1 名 chunk
第 2 名 chunk
第 3 名 chunk
```

检索评测多数时候都带 `@K`，例如：

```text
Hit Rate@3
Recall@3
Precision@3
MRR@3
```

意思是：

```text
只看前 3 条结果来算指标。
```

K 的选择会直接影响结果。K 越大，越容易把正确资料包含进来；但 K 太大也会把很多噪声交给模型，让答案变乱、成本变高。

### 9. Hit Rate@K 是什么

Hit Rate@K 关心的是：

```text
前 K 条里有没有至少一个相关结果。
```

例子：

```text
top_k = 3
检索结果：
1. 错
2. 对
3. 错
```

这个样本的 hit 就是 `true`。

Hit Rate@K 适合回答：

```text
检索器有没有摸到正确资料？
```

它不太关心正确资料排第几，也不太关心错误资料多不多。

### 10. Recall@K 是什么

Recall@K 关心的是：

```text
应该找回的资料里，前 K 条找回了多少。
```

如果一个问题有 2 个期望 chunk：

```text
expected = A, B
top_3 检索结果 = A, C, D
```

那么：

```text
recall@3 = 找回的期望数量 / 全部期望数量 = 1 / 2 = 0.5
```

Recall 更适合回答：

```text
该找的资料有没有找全？
```

在 RAG 里，Recall 很重要。因为模型生成答案需要资料，如果关键 chunk 没有被召回，后面再怎么 prompt、rerank，也很难补救。

### 11. Precision@K 是什么

Precision@K 关心的是：

```text
前 K 条结果里，有多少是相关的。
```

如果：

```text
top_k = 3
检索结果 = 对, 错, 错
```

那么：

```text
precision@3 = 1 / 3 = 0.3333
```

Precision 更适合回答：

```text
返回给模型的上下文干不干净？
```

注意本节代码故意使用固定分母 `top_k`，而不是 `实际返回数量`。

也就是说，如果 `top_k=3`，检索器只返回 1 条正确结果：

```text
precision@3 = 1 / 3
```

不是：

```text
precision = 1 / 1
```

为什么这样设计？

因为我们想衡量的是：

```text
在允许返回 K 条上下文的窗口里，检索器填进去的有效信息比例。
```

如果检索器只返回 1 条，另外 2 个位置没有利用起来，也是一种信息利用不足。这个规则更适合当前学习场景。

### 12. MRR@K 是什么

MRR 是 Mean Reciprocal Rank，中文可以理解成：

```text
平均倒数排名
```

对单个样本来说，它先找到第一个相关结果的排名。

如果第一个相关结果排第 1：

```text
reciprocal rank = 1 / 1 = 1.0
```

如果第一个相关结果排第 2：

```text
reciprocal rank = 1 / 2 = 0.5
```

如果第一个相关结果排第 3：

```text
reciprocal rank = 1 / 3 = 0.3333
```

如果前 K 条没有相关结果：

```text
reciprocal rank = 0
```

MRR@K 就是把多个样本的 reciprocal rank 求平均。

MRR 适合回答：

```text
正确资料是不是排得足够靠前？
```

在 RAG 里，排名靠前很重要。因为模型通常会更注意靠前的上下文，开发者也可能只把前几条传给模型。

### 13. bad case 是什么

bad case 是没有通过评测的样本。

它不是“代码报错”，而是“检索效果不符合预期”。

例如本节脚本运行后会看到：

```text
Bad cases:
- refund_arrival_001
- order_late_shipping_001
```

这说明当前本地关键词检索器在这两个问题上没有把期望 chunk 找进 top_3。

bad case 的价值很大。它告诉我们下一步应该观察什么：

1. 是 query 写得太口语化了吗？
2. 是 chunk 切分把关键句拆散了吗？
3. 是关键词检索能力不够，需要向量检索吗？
4. 是 metadata filter 太严格了吗？
5. 是 top_k 太小了吗？
6. 是 expected target 标注错了吗？

评测的意义不是追求第一次满分，而是把“哪里差”暴露出来。

### 14. 为什么本节先不用真实向量库

你可能会问：既然这是 RAG，为什么不直接连 Qdrant 或 Milvus？

因为本节目标是学习“评测脚本怎么设计”，不是学习“某个向量库怎么查询”。

如果一开始就连接真实向量库，问题会变多：

1. 虚拟机是否开启。
2. Docker 容器是否运行。
3. collection 是否存在。
4. embedding 维度是否匹配。
5. 数据是否已经入库。
6. 网络是否能连通。
7. 模型 key 是否配置。

这些问题都会干扰本节主题。

所以本节先用本地 `SimpleKeywordRetriever` 做 baseline。它只依赖本地 `data/knowledge_base`，不需要虚拟机、不需要 Qdrant、不需要 Milvus、不需要真实模型。

这就是一个好学习顺序：

```text
先学评测方法 -> 再把被评测对象换成真实检索器
```

## 二、本节主题系统讲解

### 1. 本节搭建的最小检索评测闭环

本节完整链路如下：

```text
data/knowledge_base
        |
        v
加载文档 load_documents_from_directory()
        |
        v
切分 chunk split_documents()
        |
        v
本地关键词检索 SimpleKeywordRetriever
        |
        v
得到 RetrievedChunk 列表
        |
        v
读取 data/rag_eval/retrieval_cases.json
        |
        v
evaluate_retrieval_results()
        |
        v
输出 summary + bad cases
```

这条链路看起来简单，但它已经具备评测系统最核心的能力：

1. 有固定问题。
2. 有期望答案位置。
3. 有真实检索结果。
4. 有指标计算。
5. 有失败样本报告。
6. 可以重复运行。

以后真实项目中的评测系统，本质也是这个结构，只是会更复杂。

### 2. 评测模块为什么放在 `app/rag/evaluation.py`

本节新增：

```text
projects/ai-service/app/rag/evaluation.py
```

它不放在 `scripts/` 里，是因为评测逻辑本身是可复用的业务能力。

`scripts/` 适合放一次性手动入口，例如：

```text
uv run python scripts/rag_retrieval_eval.py
```

但指标计算、样本模型、结果汇总不应该只属于某一个脚本。

以后我们可以用同一个 `evaluation.py` 评测不同检索器：

```text
关键词检索
Qdrant 向量检索
Milvus 向量检索
混合检索
rerank 后结果
线上日志回放结果
```

所以本节的设计是：

```text
evaluation.py 只关心“检索结果是否命中预期”
rag_retrieval_eval.py 负责“把当前项目的数据跑起来”
```

这样拆分以后，评测模块不会和某个向量数据库绑死。

### 3. 为什么评测输入使用 `RetrievedChunk`

项目里已经有统一的检索结果模型：

```text
RetrievedChunk
```

它表示“已经从某种检索器里找回来的 chunk”。

无论底层来自 Qdrant、Milvus、关键词检索还是混合检索，最后都可以转成：

```text
content
metadata
score
```

本节评测模块直接接收 `list[RetrievedChunk]`，好处是：

1. 不关心底层检索器是什么。
2. 不关心向量库接口返回格式是什么。
3. 只关心 RAG 系统内部统一结果。
4. 后续替换检索器时不用重写指标计算。

这也是工程里很重要的思想：

```text
先建立内部统一模型，再让不同外部系统适配到这个模型。
```

### 4. 评测样本文件的字段设计

`retrieval_cases.json` 是一个 JSON 数组，每个元素是一条评测样本。

核心字段：

```text
id
query
expected_sources
expected_sections
expected_chunk_ids
expect_no_results
permission_group
business_domain
doc_type
source
notes
```

字段解释：

`id`：样本唯一标识。它不能重复，因为后面 bad case 报告和历史趋势都要靠 id 追踪。

`query`：用户问题。它应该尽量像真实用户会问的问题。

`expected_sources`：期望命中的文档来源，例如 `refund-return-policy.md`。

`expected_sections`：期望命中的章节，例如 `运费处理`。

`expected_chunk_ids`：期望命中的具体 chunk，例如 `refund_return_policy_chunk_0005`。

`expect_no_results`：是否期望没有检索结果。用于测试系统是否会乱召回。

`permission_group`：本样本检索时使用的权限过滤条件。

`business_domain`：本样本检索时使用的业务域过滤条件。

`doc_type`：本样本检索时使用的文档类型过滤条件。

`source`：本样本检索时使用的来源过滤条件。

`notes`：人能读懂的样本说明。这个字段不参与指标计算，但能帮助以后复盘。

### 5. 为什么样本里既有 expected，也有 filter

很多初学者会混淆：

```text
expected target 和 filter 是一回事吗？
```

不是。

`expected_*` 表示：

```text
我希望检索结果命中哪里。
```

`permission_group`、`business_domain`、`doc_type`、`source` 表示：

```text
这次检索应该带什么过滤条件。
```

举例：

```text
query = "退货运费谁承担？"
business_domain = "refund"
expected_chunk_ids = ["refund_return_policy_chunk_0005"]
```

这里的 `business_domain=refund` 是检索时用来缩小范围的过滤条件。

`expected_chunk_ids` 是评测时用来判断结果是否正确的标准。

一个是“检索约束”，一个是“评测答案”。

### 6. 为什么样本必须校验

评测样本如果写错，指标就会骗人。

例如：

```json
{
  "id": "case_001",
  "query": "退货运费谁承担？"
}
```

这个样本没有 expected target，也没有声明 `expect_no_results=true`。

那评测器不知道它应该命中什么。

再例如：

```json
{
  "id": "case_002",
  "query": "会员积分怎么兑换？",
  "expect_no_results": true,
  "expected_sources": ["refund-return-policy.md"]
}
```

这就自相矛盾了：一边说期望没有结果，一边又给了期望文档。

所以本节用 Pydantic 做样本校验：

1. `id` 和 `query` 必须非空。
2. `expected_sources`、`expected_sections`、`expected_chunk_ids` 必须是字符串列表。
3. expected 列表会去掉空白并去重。
4. 普通样本必须有至少一个 expected target。
5. no-result 样本不能再写 expected target。
6. 可选 filter 的空字符串会当成 `None`。
7. 样本 id 不能重复。

这一步非常重要。因为评测系统最怕“测试数据本身不可信”。

### 7. match_level 的优先级

本节评测器会自动选择最强的匹配级别：

```text
expected_chunk_ids 有值 -> match_level = chunk_id
否则 expected_sections 有值 -> match_level = section
否则 expected_sources 有值 -> match_level = source
否则 no-result -> match_level = none
```

为什么这样设计？

因为越精确的标注越能说明问题。

如果一个样本已经告诉你：

```text
正确 chunk_id 是 refund_return_policy_chunk_0005
```

那评测时就不应该退回到 source 粗粒度判断。

否则会出现：

```text
检索器找到了 refund-return-policy.md，但找到的是退款到账 chunk，不是运费 chunk。
```

如果按 source 算通过，这个样本就失去了意义。

### 8. 指标计算的整体逻辑

对每条普通样本，评测器会做这些事：

```text
1. 取前 top_k 条 retrieved chunks
2. 按 match_level 判断每条 chunk 是否 relevant
3. 统计前 top_k 里命中了多少 expected target
4. 判断是否 hit
5. 计算 first_relevant_rank
6. 计算 precision_at_k
7. 计算 recall_at_k
8. 计算 reciprocal_rank
9. 判断 passed
```

其中 `passed` 的标准是：

```text
matched_expected_count == expected_count
```

也就是所有期望目标都被找到了。

如果一个样本只期望 1 个 chunk，只要 top_k 内命中这个 chunk 就通过。

如果一个样本期望 2 个 chunk，top_k 内只命中 1 个，那 hit 可能是 true，但 passed 仍然是 false。

这个差异很关键：

```text
hit 说明至少摸到了正确资料。
passed 说明本样本的期望资料找全了。
```

### 9. no-result case 的指标为什么单独算

no-result case 不适合和普通样本混在一起平均。

普通样本关注：

```text
应该找回的资料有没有被找回。
```

no-result 样本关注：

```text
不该返回资料时有没有乱返回。
```

它们衡量的不是同一种能力。

所以本节汇总时：

1. Hit Rate、Recall、Precision、MRR 只平均普通样本。
2. no-result 样本单独计算 `no_result_success_rate`。

这样看报告更清楚：

```text
普通问题召回能力怎么样？
无资料问题克制能力怎么样？
```

### 10. 为什么 bad case 要输出 retrieved items

只知道某个样本失败还不够。

例如：

```text
- refund_arrival_001: missing expected retrieval targets
```

这告诉你失败了，但没有告诉你“错到哪里”。

所以 bad case 报告还会输出检索器实际返回的结果：

```text
rank=1 relevant=False score=...
source=...
section=...
chunk_id=...
```

你可以据此判断：

1. 是文档方向错了。
2. 是文档对了但章节错了。
3. 是章节对了但 chunk_id 错了。
4. 是相关结果排在 top_k 之外。
5. 是完全没有返回结果。

bad case 是后续优化的入口，不是终点。

## 三、本节新增代码讲解

### 1. `data/rag_eval/retrieval_cases.json`

这个文件是本节的评测集。

当前一共有 12 条样本，覆盖：

1. 退款退货规则。
2. 订单发货规则。
3. 物流查询 FAQ。
4. 账号安全 FAQ。
5. 一个当前知识库无法回答的问题。

为什么不是一开始写 100 条？

因为学习阶段更重要的是：

```text
样本少，但每条都能解释清楚。
```

如果一开始写太多样本，你可能只看到一个总分，却不知道每个样本为什么这样标注。

本节的 12 条样本是一个最小可维护版本：

```text
覆盖多个业务域 + 覆盖精确 chunk + 覆盖 no-result + 能暴露 bad case
```

### 2. `RetrievalEvalCase`

`RetrievalEvalCase` 是评测样本模型。

它的职责不是检索，也不是计算指标，而是保证输入样本可靠。

核心字段：

```python
class RetrievalEvalCase(BaseModel):
    id: str = Field(min_length=1)
    query: str = Field(min_length=1)
    expected_sources: list[str] = Field(default_factory=list)
    expected_sections: list[str] = Field(default_factory=list)
    expected_chunk_ids: list[str] = Field(default_factory=list)
    expect_no_results: bool = False
    permission_group: str | None = None
    business_domain: str | None = None
    doc_type: str | None = None
    source: str | None = None
    notes: str = ""
```

你要重点理解这几个点：

`Field(min_length=1)`：要求字符串不能为空。

`default_factory=list`：给列表字段一个新的空列表，避免多个对象共享同一个默认列表。

`str | None`：表示这个字段可以是字符串，也可以是空值。

`expect_no_results`：把“期望无结果”明确建模，不靠空 expected 列表猜测。

### 3. 字段校验器

本节用 `field_validator` 做输入清洗。

`id` 和 `query` 会去掉前后空格。

expected 列表会做三件事：

1. 如果没传，变成空列表。
2. 如果不是字符串列表，报错。
3. 去掉每个字符串前后空格，并去重。

可选 filter 字段会做：

```text
"  refund  " -> "refund"
"   " -> None
```

为什么空字符串要变成 `None`？

因为空字符串不是一个有效过滤值。假如把空字符串传给 retriever，它可能会尝试匹配：

```text
metadata["business_domain"] == ""
```

这通常不是我们想要的。

`notes` 则不同。`notes` 是说明文字，空字符串可以存在，所以它不会按 filter 逻辑处理。

### 4. `validate_expectations`

这个模型级校验负责检查样本逻辑是否自洽。

普通样本必须有 expected target：

```text
expected_sources
expected_sections
expected_chunk_ids
```

至少一个非空。

no-result 样本则相反：

```text
expect_no_results = true
```

时不能再写 expected target。

这背后的思想是：

```text
评测样本必须表达清楚“什么结果算对”。
```

没有标准答案的评测，最后一定会变成主观感觉。

### 5. `load_retrieval_eval_cases`

这个函数负责从 JSON 文件加载评测样本。

它做了两层检查：

1. 文件内容必须是 JSON list。
2. 样本 id 不能重复。

为什么 id 重复很严重？

因为后面我们用：

```text
retrievals_by_case_id
```

把样本 id 映射到对应检索结果。

如果两个样本 id 一样，后一个可能覆盖前一个，bad case 报告也会混乱。

### 6. `_ExpectedMatcher`

`_ExpectedMatcher` 是内部辅助对象，用来封装“怎么判断一个 chunk 是否相关”。

它会根据样本内容决定 match level。

举例：

```text
expected_chunk_ids = ["a"]
```

那么只看：

```text
chunk.metadata["chunk_id"]
```

是否等于 `a`。

如果没有 expected_chunk_ids，但有 expected_sections，就看：

```text
chunk.metadata["section"]
```

是否命中期望章节。

如果样本同时写了 expected_sources，那么 source 也要匹配。

如果只写 expected_sources，就只看：

```text
chunk.metadata["source"]
```

这个类让主评测函数更清晰，不必把所有判断条件堆在一个大函数里。

### 7. `evaluate_retrieval_case`

这是单条样本的评测函数。

输入：

```text
eval_case
retrieved_chunks
top_k
```

输出：

```text
RetrievalEvalCaseResult
```

它会记录：

```text
case_id
query
top_k
match_level
metric_applicable
expected_count
retrieved_count
relevant_retrieved_count
matched_expected_count
hit
first_relevant_rank
precision_at_k
recall_at_k
reciprocal_rank
passed
failed_reason
retrieved_items
```

这里最值得理解的是：

```text
retrieved_count 是实际返回数量
precision_at_k 的分母是 top_k
```

这两个不是一回事。

假设：

```text
top_k = 3
实际返回 1 条
这 1 条是相关的
```

那么：

```text
retrieved_count = 1
precision_at_k = 1 / 3
```

这样能体现出检索器只填满了一个有效上下文位置。

### 8. `evaluate_retrieval_results`

这个函数负责汇总多条样本。

输入是：

```text
cases
retrievals_by_case_id
top_k
```

其中 `retrievals_by_case_id` 的结构类似：

```python
{
    "refund_shipping_fee_001": [RetrievedChunk(...), RetrievedChunk(...)],
    "order_shipping_time_001": [RetrievedChunk(...)]
}
```

它会逐条调用 `evaluate_retrieval_case`，然后计算整体平均指标。

注意：

```text
普通样本和 no-result 样本分开统计。
```

普通样本进入：

```text
hit_rate_at_k
recall_at_k
precision_at_k
mrr_at_k
```

no-result 样本进入：

```text
no_result_success_rate
```

### 9. `format_retrieval_eval_summary`

这个函数把结果整理成适合人看的文本。

脚本输出不是为了机器读，而是为了你快速判断：

```text
本轮评测整体怎么样？
多少样本通过？
哪些指标低？
no-result 是否成功？
```

输出示例：

```text
RAG retrieval evaluation summary
top_k: 3
cases: 12
evaluated_cases: 11
no_result_cases: 1
passed_cases: 10
failed_cases: 2
hit_rate@3: 0.8182
recall@3: 0.8182
precision@3: 0.2727
mrr@3: 0.7727
no_result_success_rate: 1.0000
```

这些数字要一起看，不要只看一个指标。

### 10. `format_retrieval_bad_cases`

这个函数只输出失败样本。

它的价值是：

```text
把总分拆成可以处理的问题清单。
```

如果没有 bad case，只看 summary 就够了。

如果有 bad case，应该继续看：

1. 失败样本的 query。
2. 失败原因。
3. 实际返回了哪些 chunk。
4. 返回 chunk 的 source、section、chunk_id、score。

这一步就是后续优化的起点。

### 11. `scripts/rag_retrieval_eval.py`

这个脚本是本节手动入口。

它做的事情是：

```text
1. 读取 data/rag_eval/retrieval_cases.json
2. 加载 data/knowledge_base 文档
3. 按项目默认 chunk 策略切分文档
4. 用 SimpleKeywordRetriever 做本地检索
5. 把 KeywordSearchResult 转成 RetrievedChunk
6. 调用 evaluation.py 计算指标
7. 打印 summary 和 bad cases
```

为什么要把 `KeywordSearchResult` 转成 `RetrievedChunk`？

因为评测模块只认项目统一检索结果模型。

这再次体现了统一内部模型的好处：

```text
脚本负责适配输入，评测模块只负责评测。
```

### 12. 为什么设置 `keyword_min_score=0.2`

关键词检索如果没有最低分，很容易什么都返回一点。

例如用户问：

```text
会员积分怎么兑换？
```

当前知识库没有会员积分，但如果阈值太低，检索器可能因为某个普通词命中而返回无关资料。

所以脚本默认：

```text
--keyword-min-score 0.2
```

这个值不是生产最佳值，只是学习阶段的一个可解释默认值。

它的作用是让 no-result case 有机会通过，同时保留一些关键词召回能力。

你可以手动调它：

```powershell
uv run python scripts/rag_retrieval_eval.py --keyword-min-score 0.1
uv run python scripts/rag_retrieval_eval.py --keyword-min-score 0.3
```

然后观察指标变化。

### 13. 单元测试重点

本节测试文件：

```text
projects/ai-service/tests/test_rag_evaluation.py
```

测试重点不是“测试脚本能不能打印文字”，而是测试评测核心逻辑：

1. 样本加载和重复 id 检查。
2. chunk_id 命中时 Hit Rate、Recall、Precision、MRR 的计算。
3. section 匹配时 source 门槛是否生效。
4. no-result case 是否单独处理。
5. summary 是否正确排除 no-result case。
6. bad case 报告是否能输出失败样本。

测试不连接真实 Qdrant、Milvus、embedding 或模型。

这是因为指标计算必须稳定。评测代码本身如果依赖外部服务，就很难判断失败到底是指标逻辑错了，还是外部服务状态不稳定。

## 四、如何运行本节脚本

进入 ai-service 项目：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
```

如果担心 PowerShell 中文显示问题，可以先设置：

```powershell
$env:PYTHONIOENCODING='utf-8'
```

运行检索评测脚本：

```powershell
uv run python scripts/rag_retrieval_eval.py
```

运行本节单元测试：

```powershell
uv run pytest tests/test_rag_evaluation.py -q
```

本节不需要打开 VMware，不需要启动 Qdrant，也不需要启动 Milvus。

## 五、本节当前评测结果怎么读

当前脚本输出的核心结果是：

```text
top_k: 3
cases: 12
evaluated_cases: 11
no_result_cases: 1
passed_cases: 10
failed_cases: 2
hit_rate@3: 0.8182
recall@3: 0.8182
precision@3: 0.2727
mrr@3: 0.7727
no_result_success_rate: 1.0000
```

逐项解释：

`cases: 12` 表示总共有 12 条评测样本。

`evaluated_cases: 11` 表示有 11 条普通检索样本参与 Hit Rate、Recall、Precision、MRR 平均。

`no_result_cases: 1` 表示有 1 条期望无结果样本。

`passed_cases: 10` 表示 10 条样本通过。

`failed_cases: 2` 表示 2 条样本失败，需要看 bad case。

`hit_rate@3: 0.8182` 表示 11 条普通样本里，大约 81.82% 的样本能在前 3 条里找到至少一个相关结果。

`recall@3: 0.8182` 表示期望目标的平均召回比例约为 81.82%。当前大多数样本只有一个 expected chunk，所以它和 hit_rate 比较接近。

`precision@3: 0.2727` 表示 top_3 结果里，平均有效比例不高。这并不奇怪，因为每个样本通常只期待一个 chunk，而 top_3 有三个位置。

`mrr@3: 0.7727` 表示相关结果整体排得比较靠前，但仍有失败样本和排名不完美的情况。

`no_result_success_rate: 1.0000` 表示当前那条无资料问题没有乱召回，表现符合预期。

### 为什么有 2 个 bad case 反而是好事

学习阶段出现 bad case 是正常的，而且有价值。

如果第一次就 100% 通过，你反而学不到怎么分析问题。

当前两个 bad case 说明：

```text
本地关键词检索 baseline 不是万能的。
```

它可能受限于：

1. 用户 query 和文档措辞不一致。
2. 文档 chunk 中关键词分散。
3. 关键词权重太简单。
4. 缺少语义相似能力。
5. top_k 较小。

这正好为后续学习铺路：

```text
为什么要向量检索？
为什么要混合检索？
为什么要调 chunk？
为什么要 rerank？
为什么要持续评测？
```

## 六、从本节开始，你应该怎样思考 RAG 优化

以前你可能会这样想：

```text
我改了一下 chunk_size，感觉效果好像好了。
```

学完本节后，应该换成：

```text
我改了 chunk_size，然后跑同一批 retrieval_cases.json。
Hit Rate@3 从多少变成多少？
Recall@3 从多少变成多少？
MRR@3 有没有提高？
bad case 有没有减少？
有没有新的 no-result 误召回？
```

这就是从“凭感觉调”变成“用数据调”。

RAG 工程里，很多优化都不是绝对正确的。

比如：

```text
top_k 调大
```

可能提高 Recall，但降低 Precision。

```text
score_threshold 调高
```

可能减少噪声，但也可能漏掉正确资料。

```text
chunk_size 调大
```

可能保留更多上下文，但也可能让 chunk 变得太宽、检索不精准。

所以评测脚本的作用就是帮你观察这些取舍。

## 七、常见误区

### 误区 1：最终回答对了，就说明检索没问题

不一定。

模型可能靠自己的参数知识答对，也可能猜对。

企业 RAG 更关心：

```text
回答是不是基于企业资料。
```

所以检索评测和答案评测要分开看。

### 误区 2：Hit Rate 高就足够了

Hit Rate 高只说明“至少找到了一个相关结果”。

但如果 top_3 里另外两个都是噪声，模型仍然可能被干扰。

所以还要看 Precision、MRR 和 bad case。

### 误区 3：Precision 低一定代表系统差

不一定。

如果每个 query 只有一个 expected chunk，而 `top_k=3`，那么即使第一条永远正确：

```text
precision@3 = 1 / 3 = 0.3333
```

所以 Precision 要结合样本设计和 top_k 解释。

### 误区 4：bad case 是坏事

bad case 不是坏事，它是改进线索。

没有 bad case，你不知道系统错在哪里。

### 误区 5：评测集越大越好

评测集当然需要逐步变大，但一开始更重要的是质量。

一个好的小评测集应该满足：

1. 每条样本都能解释为什么这样标注。
2. 覆盖主要业务域。
3. 覆盖常见问法。
4. 覆盖无资料问题。
5. 能暴露当前系统缺点。

## 八、本节练习与参考答案

### 练习 1：解释 `retrieval_cases.json` 的作用

题目：用自己的话说明 `retrieval_cases.json` 为什么不是普通测试数据，而是 RAG 检索评测集。

参考答案：

`retrieval_cases.json` 保存固定的用户问题和期望命中的资料位置。它的作用是让我们每次修改检索策略后，都能用同一批问题重复运行评测，比较 Hit Rate、Recall、Precision、MRR 和 bad case 变化。它不是随便给脚本用的样例数据，而是判断检索质量的标准样本集。

### 练习 2：区分 expected 和 filter

题目：`expected_chunk_ids` 和 `business_domain` 有什么区别？

参考答案：

`expected_chunk_ids` 是评测标准，表示这个问题应该命中哪些 chunk。`business_domain` 是检索过滤条件，表示检索时只在某个业务域内查。前者回答“什么结果算对”，后者回答“这次检索应该限制在哪个范围”。

### 练习 3：计算 Precision@3

题目：某个问题 top_3 返回结果是：第 1 条相关，第 2 条不相关，第 3 条不相关。Precision@3 是多少？

参考答案：

Precision@3 = 相关结果数量 / 3 = 1 / 3 = 0.3333。

### 练习 4：计算 Recall@3

题目：某个问题期望命中 2 个 chunk，top_3 只找回了其中 1 个。Recall@3 是多少？

参考答案：

Recall@3 = 找回的期望目标数量 / 全部期望目标数量 = 1 / 2 = 0.5。

### 练习 5：计算 Reciprocal Rank

题目：某个问题第一个相关结果排在第 2 名，reciprocal rank 是多少？

参考答案：

reciprocal rank = 1 / 2 = 0.5。

### 练习 6：解释 no-result case

题目：为什么“会员积分怎么兑换？”适合作为 no-result case？

参考答案：

因为当前知识库主要覆盖退款退货、订单发货、物流查询和账号安全，没有会员积分兑换资料。这个问题可以测试检索器是否会在没有相关资料时乱返回不相关 chunk。

### 练习 7：判断通过与否

题目：某样本 `expected_chunk_ids=["A", "B"]`，top_3 找回了 `A`，但没找回 `B`。这个样本 hit 是什么？passed 是什么？

参考答案：

hit 是 `true`，因为至少找到了一个相关结果。passed 是 `false`，因为期望的两个 chunk 没有全部找回。

### 练习 8：解释为什么本节不用真实向量库

题目：为什么本节先用本地关键词检索做 baseline，而不是直接连 Qdrant 或 Milvus？

参考答案：

因为本节学习重点是评测脚本和指标计算。如果直接连真实向量库，会引入 Docker、网络、collection、embedding 维度、数据入库状态等干扰。先用本地关键词检索可以让评测流程稳定可运行，等评测思想清楚后，再替换成真实向量检索。

### 练习 9：分析 bad case

题目：如果某个 bad case 的实际返回结果 source 是正确的，但 section 不正确，这说明什么？

参考答案：

说明检索器大方向找到了正确文档，但没有定位到正确章节或正确 chunk。后续可能需要检查 chunk 切分、关键词权重、向量召回、rerank 或 expected 标注是否合理。

### 练习 10：改参数观察

题目：运行下面命令后，你应该重点观察什么？

```powershell
uv run python scripts/rag_retrieval_eval.py --top-k 5
```

参考答案：

应该观察 Hit Rate@5、Recall@5、Precision@5、MRR@5 和 bad case 是否变化。top_k 变大可能让更多正确资料进入结果，提高 Hit Rate 或 Recall，但也可能让 Precision 降低，因为返回了更多不相关内容。

## 九、自测题与答案

### 自测 1

问题：检索评测主要评测 RAG 链路中的哪一步？

答案：主要评测 retrieval，也就是“从知识库找回资料”的步骤。

### 自测 2

问题：为什么固定评测样本比临时随便问几个问题更可靠？

答案：固定样本能让每次运行面对同一批问题，方便比较不同代码版本、不同检索策略或不同参数设置带来的变化。

### 自测 3

问题：`expected_chunk_ids`、`expected_sections`、`expected_sources` 哪个最精确？

答案：`expected_chunk_ids` 最精确，其次是 `expected_sections`，最后是 `expected_sources`。

### 自测 4

问题：如果样本写了 `expected_chunk_ids`，评测器为什么不退回到 source 判断？

答案：因为 chunk_id 是更精确的标准。退回到 source 会把“找到正确文档但找错具体 chunk”的情况误判为正确。

### 自测 5

问题：no-result case 的目标是什么？

答案：目标是验证系统在知识库没有相关资料时，不要乱返回不相关 chunk。

### 自测 6

问题：Hit Rate@K 和 Recall@K 的区别是什么？

答案：Hit Rate@K 看前 K 条里有没有至少一个相关结果；Recall@K 看期望目标中有多少比例被前 K 条找回。

### 自测 7

问题：Precision@K 更关注什么？

答案：更关注前 K 条结果里相关内容的比例，也就是返回给模型的上下文是否干净。

### 自测 8

问题：MRR@K 为什么和排名有关？

答案：MRR 使用第一个相关结果的倒数排名。相关结果越靠前，分数越高；如果前 K 条没有相关结果，分数为 0。

### 自测 9

问题：为什么本节 summary 里的 no-result success rate 单独统计？

答案：因为 no-result 样本衡量的是“不该返回时是否克制”，普通样本衡量的是“该返回时是否找回”。两者不是同一种能力，混在一起平均会误导判断。

### 自测 10

问题：`evaluation.py` 为什么不直接调用 Qdrant 或 Milvus？

答案：因为它应该是通用评测模块，只负责根据 `RetrievedChunk` 计算指标。Qdrant、Milvus、关键词检索都可以先适配成 `RetrievedChunk`，再交给它评测。

### 自测 11

问题：bad case 报告最重要的价值是什么？

答案：它把整体指标拆成具体失败样本，让我们知道应该分析哪条 query、哪个 expected target、实际返回了哪些错误 chunk，从而指导后续优化。

### 自测 12

问题：本节脚本不需要启动虚拟机的原因是什么？

答案：因为它只读取本地知识库文件，使用本地关键词检索 baseline，不连接 Qdrant、Milvus、真实 embedding 或真实模型。

## 十、本节小结

本节真正学到的不是“又写了一个脚本”，而是建立了 RAG 检索质量的最小闭环：

```text
固定问题 -> 固定期望 -> 运行检索器 -> 计算指标 -> 输出 bad case -> 指导下一轮优化
```

这一步很关键。

没有评测脚本时，RAG 优化很容易变成感觉工程：

```text
好像更准了
好像更慢了
好像没问题
```

有了评测脚本以后，你就可以开始用数据说话：

```text
Hit Rate@3 变了多少
Recall@3 变了多少
MRR@3 变了多少
bad case 还剩哪些
no-result 有没有乱召回
```

后续无论我们把检索器换成 Qdrant、Milvus、混合检索，还是加 rerank，这套评测思路都可以继续复用。
