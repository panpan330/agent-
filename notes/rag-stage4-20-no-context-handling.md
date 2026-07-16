# 阶段 4 第 20 节：无检索结果时怎么处理

## 本节状态

已完成。

第 17 节我们学了 `score_threshold`：

```text
低相关 chunk 不应该进入回答阶段。
```

第 18 节我们学了把检索结果交给模型回答：

```text
RetrievedChunk -> RAG context -> model -> answer
```

第 19 节我们学了回答必须带出处：

```text
answer + citations
```

第 20 节要专门处理一种非常常见、也非常重要的情况：

```text
检索阶段没有给生成阶段提供可用 chunk。
```

也就是：

```text
chunks = []
```

本节的核心不是“返回一句抱歉”，而是：

```text
把“无可用知识库资料”设计成一个清楚、可测试、可被前后端识别的业务状态。
```

## 本节学习目标

学完本节，你要能讲清楚：

1. 什么叫 RAG 的无检索结果。
2. 为什么无检索结果不是系统异常。
3. 为什么无检索结果时不能让模型硬答。
4. `top_k` 为空、`score_threshold` 过滤为空、权限过滤为空有什么区别。
5. 为什么 generator 只看到 `chunks=[]`，不能假装知道上游具体原因。
6. 为什么只返回一段字符串不够，最好要有结构化状态。
7. `answered` 和 `no_context` 两种状态的区别。
8. `no_context_reason` 为什么要机器可读。
9. `suggestions` 为什么是用户体验兜底，而不是事实答案。
10. 没有资料时为什么 citations 必须是空列表。
11. 本节新增代码如何保持第 18、19 节能力不被破坏。

## 本节暂时不学什么

本节只做生成阶段的无资料结构化兜底。

暂时不做：

- 不做 `/rag-chat` HTTP API。
- 不做真实 Qdrant 调用。
- 不做真实模型调用。
- 不自动扩大检索范围。
- 不做关键词检索兜底。
- 不做转人工接口。
- 不做知识缺口数据库。
- 不做权限过滤原因透出。
- 不做多轮追问策略。

这些都很重要，但不是本节最小目标。

本节先把一个基础原则立住：

```text
没有可用检索资料时，RAG 系统要明确返回 no_context，而不是假装 answered。
```

## 一、基础知识铺垫

### 1. 什么是“无检索结果”

在 RAG 里，用户问题进入系统后，一般会经历：

```text
用户问题
-> query embedding
-> vector search
-> payload filter
-> score_threshold
-> top_k chunks
-> generator
```

如果最后传给 generator 的 chunks 是空列表：

```python
chunks = []
```

就可以说：

```text
生成阶段没有可用检索资料。
```

注意，这里的“无检索结果”不一定只有一种原因。

可能是：

- 向量库里真的没有相似内容。
- 有相似内容，但分数低于 `score_threshold`。
- 有相似内容，但被权限过滤挡掉了。
- 用户问的问题不属于当前知识库范围。
- 用户问题太模糊，检索不到稳定资料。
- 文档还没入库。
- 入库时 metadata 设计错了。
- embedding 模型效果不好。
- chunk 切分让相关信息被拆散了。

所以你不能把 `chunks=[]` 简单理解成：

```text
向量库里没有任何东西。
```

更准确的理解是：

```text
在当前检索条件下，没有可用于回答的知识库上下文。
```

### 2. 无检索结果不是系统异常

这是本节最重要的基础概念之一。

系统异常是：

```text
Qdrant 挂了。
embedding API 超时。
模型调用失败。
代码抛异常。
网络连接失败。
```

无检索结果是：

```text
系统正常工作了，只是没有找到可用资料。
```

这两类情况不能混在一起。

如果 Qdrant 挂了，应该返回系统错误或服务不可用。

如果检索正常但没有资料，应该返回：

```text
当前知识库没有找到足够相关的资料。
```

为什么要分清？

因为用户和开发者需要采取的行动不同。

| 情况 | 含义 | 应对 |
| --- | --- | --- |
| 无检索结果 | 知识库没有可用资料 | 换问法、补文档、转人工 |
| 系统异常 | 服务链路坏了 | 排查日志、恢复服务、重试 |

如果你把无检索结果当成 500 错误，用户会以为系统坏了。

如果你把系统异常当成无资料，开发者会漏掉真正故障。

所以本节要建立一个清楚的工程边界：

```text
no_context 是业务状态，不是系统错误。
```

### 3. 为什么无结果时不能让模型硬答

假设用户问：

```text
公司的年会抽奖规则是什么？
```

当前知识库没有任何年会抽奖文档。

如果继续调用模型，模型可能回答：

```text
公司年会抽奖通常会按员工工号随机抽取，一等奖可能是电子产品。
```

这听起来像合理答案，但它不是知识库答案。

企业 RAG 最大的问题不是“模型不会说话”，而是：

```text
模型说得很像真的，但没有企业资料支撑。
```

所以没有 chunks 时继续调用模型，会把 RAG 变成普通聊天。

这会造成几个风险：

1. 用户误以为答案来自企业知识库。
2. 模型可能编造政策。
3. 客服或业务人员可能照着错误答案执行。
4. 后续无法提供真实 citation。
5. 系统审计时找不到证据链。

因此本项目坚持：

```text
无可用检索资料时，不调用模型硬答。
```

### 4. 无结果和“模型不知道”不是一回事

有些人会把这两句话混在一起：

```text
模型不知道。
知识库没有资料。
```

它们不是一回事。

`模型不知道` 说的是模型自身能力或训练知识。

`知识库没有资料` 说的是当前 RAG 检索上下文为空。

RAG 系统的回答依据应该是：

```text
当前检索到的知识库资料。
```

所以即使模型凭常识可能知道，也不应该在无资料时硬答。

比如：

```text
退货邮费谁承担？
```

模型可能凭电商常识回答：

```text
质量问题商家承担，个人原因用户承担。
```

但你的企业政策可能有特殊活动规则。

如果知识库没有查到相关资料，正确做法仍然是承认资料不足，而不是用常识补齐。

### 5. `top_k=[]` 和阈值过滤为空的区别

从 generator 角度看，二者都可能变成：

```python
chunks = []
```

但从检索阶段看，它们不一样。

第一种：

```text
向量库查询本身没有返回候选。
```

可能原因：

- 知识库太小。
- 文档没有入库。
- query embedding 异常。
- 检索条件太窄。

第二种：

```text
向量库返回了候选，但都低于 score_threshold。
```

可能原因：

- 资料有点相似，但不够可靠。
- 阈值设得太高。
- embedding 模型不适合当前语料。
- 用户问法和文档表达差距太大。

这两个情况对后续优化不同。

如果完全没候选，可能要检查入库、filter、embedding。

如果有候选但低于阈值，可能要调阈值、调 chunk、换 embedding、加 rerank。

但是本节 generator 只拿到最终 `chunks=[]`，所以它不应该乱猜：

```text
一定是 score_threshold 过滤掉了。
```

它只能表达：

```text
没有可用 retrieved chunks。
```

### 6. 权限过滤为空也不能直接说“没有资料”

还有一种情况很重要：

```text
知识库里有资料，但当前用户没有权限看。
```

例如：

```text
permission_group = internal_admin
```

当前用户是：

```text
customer_service
```

payload filter 会把这些内部资料过滤掉。

这时对当前用户来说，确实没有可用资料。

但系统内部不能简单理解成“知识库没有这类知识”。

因为真实情况是：

```text
有资料，但当前权限不可见。
```

本节不做权限原因透出，原因是权限信息本身可能敏感。

真实系统里通常不会直接告诉用户：

```text
你没有权限查看 internal_admin 文档。
```

而是更安全地说：

```text
当前知识库没有找到你可用范围内的相关资料。
```

这会在后面的 RAG 安全里继续深入。

### 7. 为什么只返回字符串不够

第 18 节已经有一个简单兜底：

```text
当前知识库没有找到足够相关的资料，无法根据知识库回答这个问题。
```

这句话对人类可读，但对系统不够清楚。

前端或调用方如果只拿到字符串，很难稳定判断：

```text
这是正常回答？
还是无资料兜底？
还是模型生成的一句话？
```

如果以后要做 UI，前端可能需要：

- 无资料时显示灰色提示。
- 隐藏引用来源区域。
- 展示“换个问法”建议。
- 提供“转人工”按钮。
- 提供“记录知识缺口”按钮。

这些都不能靠解析中文字符串来做。

所以本节把结构升级成：

```json
{
  "answer": "当前知识库没有找到足够相关的资料，无法根据知识库回答这个问题。",
  "status": "no_context",
  "citations": [],
  "no_context_reason": "no_retrieved_chunks",
  "suggestions": [
    "换一种更具体的问法，例如补充订单、退款、物流或账号安全等关键词。",
    "确认问题是否属于当前知识库覆盖范围。",
    "如果这是新政策或新问题，可以记录为待补充知识。"
  ]
}
```

这就是结构化状态的价值。

### 8. 状态和文案要分开

这一节你要学会一个非常重要的工程习惯：

```text
状态给程序判断，文案给人阅读。
```

比如：

```text
status = "no_context"
answer = "当前知识库没有找到足够相关的资料..."
```

`status` 是机器可读的，稳定，不应该频繁改。

`answer` 是用户可读的，可以根据产品语气调整。

如果前端通过 `answer` 文字判断无结果：

```text
只要包含“没有找到”就当无结果
```

这非常脆弱。

以后文案改成：

```text
暂时没有检索到可支持回答的资料。
```

前端判断就可能失效。

所以正确方式是：

```text
if status == "no_context":
    显示无资料状态
```

这就是为什么本节新增 `RagAnswerStatus`。

### 9. 为什么需要 `no_context_reason`

`status="no_context"` 表示没有上下文。

但系统还需要知道更具体的原因。

本节新增：

```text
no_context_reason = "no_retrieved_chunks"
```

这个 reason 的含义是：

```text
生成阶段没有收到可用于回答的 retrieved chunks。
```

为什么不叫：

```text
score_too_low
```

因为 generator 并不知道上游到底发生了什么。

也许是阈值过滤空。

也许是权限过滤空。

也许是向量库完全没有返回。

所以 reason 要符合当前模块真实知道的信息。

这体现一个很重要的工程原则：

```text
不要在下游模块编造上游原因。
```

如果以后 pipeline 能拿到更详细的检索诊断信息，可以再扩展更多 reason。

比如：

- `below_score_threshold`
- `filtered_by_permission`
- `out_of_scope`
- `knowledge_base_empty`

但本节 generator 只做 `no_retrieved_chunks`。

### 10. suggestions 是什么

`suggestions` 是给用户或前端的下一步建议。

它不是答案。

它也不是知识库事实。

它只是告诉用户：

```text
现在没找到资料，你可以怎么继续。
```

本节使用三个固定建议：

```text
换一种更具体的问法，例如补充订单、退款、物流或账号安全等关键词。
确认问题是否属于当前知识库覆盖范围。
如果这是新政策或新问题，可以记录为待补充知识。
```

为什么建议要固定？

因为本节不调用模型。

如果无资料时还让模型生成建议，模型仍可能夹带不存在的业务事实。

固定建议更稳定，也更容易测试。

### 11. 无资料时 citations 必须为空

第 19 节我们学了 citations。

本节要补一个关键边界：

```text
无资料时，citations 必须是 []。
```

不能为了前端显示整齐，返回：

```json
{
  "source": "unknown",
  "title": "无来源"
}
```

这会产生一个假的 citation。

citation 表示真实来源。

没有检索资料，就没有来源。

所以空列表是最诚实的表达。

### 12. 无资料时不要消耗模型 token

无资料时调用模型不仅有幻觉风险，还有成本问题。

如果系统每天有大量知识库外问题，而每个都继续调用模型，会造成：

- token 成本增加。
- 延迟增加。
- 模型输出不可控。
- 日志和监控更复杂。

本节仍然保持：

```text
chunks=[] 时不调用模型。
```

这既是安全边界，也是成本边界。

### 13. 无结果处理是产品体验的一部分

无结果处理不是纯后端问题。

真实产品里，用户看到无结果时可能会困惑：

```text
是我问错了吗？
是系统坏了吗？
是公司没有这条规则吗？
```

好的无结果处理应该让用户知道：

- 当前不能根据知识库回答。
- 可以怎么改问。
- 是否可以转人工。
- 是否可以反馈缺失知识。

所以本节虽然只在后端加了 `suggestions`，但背后是产品体验设计。

一个成熟 RAG 产品不能只考虑“有答案时怎么漂亮地回答”，也要考虑“没答案时怎么诚实地收场”。

### 14. 无结果处理和知识库运营

无结果不是没有价值。

大量无结果问题可以告诉你：

```text
用户真正关心什么，但知识库还没有覆盖。
```

比如很多用户问：

```text
预售商品什么时候发货？
```

但知识库只有普通订单发货规则。

这说明知识库需要补：

```text
预售商品发货规则
```

所以生产系统通常会把 no_context 事件记录下来，用于：

- 知识库补充。
- FAQ 优化。
- chunk 策略调整。
- 检索参数调优。
- 用户问题分类。

本节不做记录数据库，但你要知道它的价值。

### 15. 无结果和“拒答”的关系

无结果时的回答可以看作一种拒答。

但这个拒答不是冷冰冰地说：

```text
不能回答。
```

而是更准确地说：

```text
当前知识库没有找到足够相关的资料，所以我不能根据知识库回答。
```

这个表达包含两个意思：

1. 不是系统崩了。
2. 不是模型不会说话。
3. 是当前知识库资料不足。

这种拒答比模型硬编更可靠。

## 二、本节主题系统讲解

### 1. 第 20 节在 RAG 链路里的位置

目前链路是：

```text
retrieve_top_k()
-> chunks
-> generate_answer_with_citations()
-> RagAnswer
```

第 20 节关注的是：

```text
chunks = []
```

时应该怎么返回。

第 18 节只返回字符串：

```text
RAG_NO_CONTEXT_REPLY
```

第 19 节让有资料时可以返回：

```text
answer + citations
```

第 20 节把无资料时也纳入同一个结构：

```text
RagAnswer(
  answer=RAG_NO_CONTEXT_REPLY,
  status=NO_CONTEXT,
  citations=[],
  no_context_reason=NO_RETRIEVED_CHUNKS,
  suggestions=[...]
)
```

这样调用方不需要猜测字符串含义。

### 2. 本节新增 `RagAnswerStatus`

本节新增：

```python
class RagAnswerStatus(str, Enum):
    ANSWERED = "answered"
    NO_CONTEXT = "no_context"
```

它表达 RAG 回答状态。

`answered` 表示：

```text
系统拿到了 retrieved chunks，并调用模型生成了基于资料的回答。
```

`no_context` 表示：

```text
系统没有可用 retrieved chunks，所以没有调用模型硬答，而是返回无资料兜底。
```

为什么用枚举？

因为状态值应该是有限集合。

如果随便写字符串，很容易出现：

```text
no-context
no_context
NO_CONTEXT
noResult
```

枚举能让代码更稳定。

### 3. 本节新增 `RagNoContextReason`

本节新增：

```python
class RagNoContextReason(str, Enum):
    NO_RETRIEVED_CHUNKS = "no_retrieved_chunks"
```

它表达无上下文的机器可读原因。

当前只有一个 reason，是因为 generator 只能确定一件事：

```text
没有可用 chunks 传进来。
```

以后 pipeline 更完整后，可以扩展更多 reason。

但当前不提前编造复杂分类。

这是为了保持学习和代码边界清楚。

### 4. `RagAnswer` 为什么要新增字段

第 19 节的 `RagAnswer` 是：

```text
answer + citations
```

第 20 节扩展成：

```text
answer
status
citations
no_context_reason
suggestions
```

有资料时：

```json
{
  "answer": "订单通常会在付款后 24 小时内发货。",
  "status": "answered",
  "citations": [
    {
      "source": "order-shipping-policy.md"
    }
  ],
  "no_context_reason": null,
  "suggestions": []
}
```

无资料时：

```json
{
  "answer": "当前知识库没有找到足够相关的资料，无法根据知识库回答这个问题。",
  "status": "no_context",
  "citations": [],
  "no_context_reason": "no_retrieved_chunks",
  "suggestions": [
    "换一种更具体的问法，例如补充订单、退款、物流或账号安全等关键词。",
    "确认问题是否属于当前知识库覆盖范围。",
    "如果这是新政策或新问题，可以记录为待补充知识。"
  ]
}
```

这样一个模型同时能表达成功回答和无资料兜底。

### 5. 为什么保留旧的 `generate_answer()`

本节没有删除：

```python
generate_answer()
```

它仍然返回字符串。

原因是：

- 第 18 节学的是基础生成回答。
- 某些内部场景可能只需要 answer 文本。
- 保留旧方法能减少改动影响。
- 第 20 节重点是结构化回答，不是推翻前面实现。

新增的更完整方法是：

```python
generate_answer_with_citations()
```

现在它返回的 `RagAnswer` 会区分：

```text
answered
no_context
```

### 6. `build_no_context_rag_answer()` 做什么

本节新增：

```python
build_no_context_rag_answer()
```

它专门构造无资料结果。

返回内容包括：

- 固定兜底回答。
- `status=NO_CONTEXT`
- `citations=[]`
- `no_context_reason=NO_RETRIEVED_CHUNKS`
- 固定 suggestions。

为什么抽成函数？

因为无资料结果是一个固定结构。

如果每个地方都手写，容易出现：

- 有的地方忘了 status。
- 有的地方 citations 不是空。
- 有的地方 reason 拼错。
- 有的地方 suggestions 不一致。

抽成函数让结构稳定，也方便测试。

### 7. `build_grounded_rag_answer()` 做什么

本节新增：

```python
build_grounded_rag_answer(answer, chunks)
```

它用于有资料、有回答的情况。

返回：

- `answer`
- `status=ANSWERED`
- `citations=build_rag_citations(chunks)`
- `no_context_reason=None`
- `suggestions=[]`

这让有资料和无资料两种结果形成对照。

有资料：

```text
answered + citations
```

无资料：

```text
no_context + no citations + suggestions
```

### 8. `generate_answer_with_citations()` 的新流程

更新后的流程是：

```text
输入 query + chunks
-> query 去空白校验
-> chunks 为空：记录 no_context 日志，返回 build_no_context_rag_answer()
-> chunks 非空：调用 generate_answer()
-> 用 build_grounded_rag_answer() 包装 answer 和 citations
```

这个流程最关键的是：

```text
chunks 为空时直接返回结构化 no_context，不调用模型。
```

这保持了第 18 节的安全边界，又增强了第 19 节的结构化输出。

### 9. 为什么 generator 不区分“完全没搜到”和“阈值过滤空”

因为 generator 的输入只有：

```text
chunks
```

它没有看到：

- Qdrant 原始候选。
- 过滤前分数。
- payload filter 条件。
- 权限上下文。
- score_threshold 值。

所以 generator 不能返回：

```text
below_score_threshold
```

否则就是下游模块猜测上游原因。

本节用：

```text
no_retrieved_chunks
```

更准确。

后续如果做完整 pipeline，可以把 retriever 诊断信息传下来，再细分原因。

### 10. 本节日志边界

无资料时会记录：

```text
rag_answer_skipped reason=no_context provider=... model=...
```

它不记录完整用户问题。

为什么？

因为用户问题可能含敏感信息。

无资料事件本身值得记录，但不应该把完整问题、完整 prompt 或 API key 写进日志。

后续如果要做知识缺口分析，可以设计专门的数据采集策略，并考虑脱敏、权限和保留期限。

### 11. 本节和第 21 节的边界

第 20 节处理：

```text
系统正常运行，但没有可用检索资料。
```

第 21 节会处理：

```text
embedding、向量库、模型调用异常。
```

这两节不要混淆。

第 20 节是：

```text
no_context
```

第 21 节会是：

```text
error handling
```

一个是业务状态，一个是异常处理。

### 12. 第 20 节完成后当前 RAG 输出能力

现在 `RagAnswer` 可以表达三类核心信息：

```text
answer：给人看的回答或兜底文案
status：给程序看的状态
citations：给用户和开发者追溯的来源
```

再加上：

```text
no_context_reason：无资料原因
suggestions：用户下一步建议
```

这为后续 API 打基础。

以后 `/rag-chat` 返回时，前端可以根据 `status` 做不同展示。

例如：

```text
answered -> 显示回答和引用来源
no_context -> 显示兜底文案、建议、反馈入口
```

## 三、本节代码改动说明

### 1. 修改 `app/rag/generator.py`

本节继续在：

```text
projects/ai-service/app/rag/generator.py
```

里完成。

新增：

- `RAG_NO_CONTEXT_SUGGESTIONS`
- `RagAnswerStatus`
- `RagNoContextReason`
- `RagAnswer.status`
- `RagAnswer.no_context_reason`
- `RagAnswer.suggestions`
- `build_no_context_rag_answer()`
- `build_grounded_rag_answer()`

修改：

- `generate_answer_with_citations()` 在 `chunks=[]` 时返回结构化 no_context。

### 2. `RAG_NO_CONTEXT_SUGGESTIONS`

这是固定建议列表。

它不是模型生成的。

固定建议的好处是：

- 稳定。
- 可测试。
- 不产生模型费用。
- 不会编造业务事实。

### 3. `RagAnswerStatus`

它把回答状态限制在当前支持的范围：

```text
answered
no_context
```

这是给程序判断的，不是给用户直接阅读的主文案。

### 4. `RagNoContextReason`

当前只有：

```text
no_retrieved_chunks
```

它表示生成阶段没有收到可用 chunks。

这个命名保持了模块诚实性：不猜测向量库、权限、阈值的具体上游原因。

### 5. `RagAnswer` 新增字段

`RagAnswer` 现在不仅能表达“回答是什么”，还能表达“这是不是基于资料回答的”。

这很重要。

因为以后前端或别的服务不能只看 `answer` 字符串。

它应该看：

```text
status
```

### 6. `generate_answer_with_citations()` 的无资料分支

关键逻辑是：

```text
if not chunks:
    log no_context
    return build_no_context_rag_answer()
```

这说明：

- 不构造 prompt。
- 不调用模型。
- 不生成 citations。
- 返回结构化 no_context。

这就是本节的核心实现。

## 四、本节测试说明

本节更新：

```text
projects/ai-service/tests/test_rag_generator.py
```

重要测试包括：

1. `test_build_no_context_rag_answer_returns_structured_fallback`

验证无资料结果包含：

- `RAG_NO_CONTEXT_REPLY`
- `status=NO_CONTEXT`
- `no_context_reason=NO_RETRIEVED_CHUNKS`
- `citations=[]`
- 固定 suggestions

2. `test_build_grounded_rag_answer_returns_answered_status_and_citations`

验证有资料回答包含：

- `status=ANSWERED`
- citations
- 没有 no_context_reason
- suggestions 为空

3. `test_rag_answer_service_returns_empty_citations_without_context`

验证 service 在 `chunks=[]` 时：

- 不调用 fake model。
- 返回 no_context 状态。
- citations 为空。
- suggestions 存在。

这些测试保护的是：

```text
无资料状态不会被伪装成普通回答。
```

## 五、常见误区

### 误区 1：无结果就是系统坏了

不一定。

无结果可能是系统正常工作，只是没有找到可用资料。

系统坏了属于异常处理，第 21 节会讲。

### 误区 2：无结果时让模型自由回答能提升体验

短期看像是体验更好，长期看风险更高。

企业 RAG 的核心是基于知识库回答。没有资料时硬答，会制造看似可信的幻觉。

### 误区 3：返回一句中文兜底就够了

不够。

中文兜底适合用户阅读，但程序需要结构化状态，比如 `status=no_context`。

### 误区 4：无结果时也应该给一个 citation

不对。

citation 必须对应真实来源。没有检索资料时 citations 应该是空列表。

### 误区 5：generator 可以知道为什么没有结果

当前不能。

generator 只看到 `chunks=[]`，不知道上游是完全没搜到、阈值过滤、权限过滤还是知识库为空。

### 误区 6：suggestions 是答案的一部分

不是。

suggestions 是下一步建议，不是知识库事实，也不能当成业务规则。

## 六、本节练习

### 练习 1：区分业务状态和系统异常

题目：

下面哪些属于无检索结果业务状态？哪些属于系统异常？

```text
A. 当前用户的问题不在知识库范围内
B. Qdrant 服务连接失败
C. 检索结果都低于 score_threshold
D. 模型 API 超时
E. 权限过滤后没有可见资料
```

参考答案：

A、C、E 属于无检索结果或无可用上下文的业务状态。B、D 属于系统异常或外部服务异常。

### 练习 2：为什么无结果不调用模型

题目：

请解释为什么 `chunks=[]` 时不应该继续调用模型。

参考答案：

因为 RAG 的答案应该基于当前知识库检索资料。`chunks=[]` 表示没有可用资料，如果继续调用模型，模型可能凭常识或猜测回答，导致没有证据支撑的答案，还可能伪造业务规则和引用来源。

### 练习 3：设计 no_context 返回

题目：

请写出一个无资料时比较合理的结构化返回，至少包含 answer、status、citations。

参考答案：

```json
{
  "answer": "当前知识库没有找到足够相关的资料，无法根据知识库回答这个问题。",
  "status": "no_context",
  "citations": [],
  "no_context_reason": "no_retrieved_chunks",
  "suggestions": [
    "换一种更具体的问法。",
    "确认问题是否属于当前知识库覆盖范围。"
  ]
}
```

### 练习 4：为什么不能猜测上游原因

题目：

为什么 generator 不应该在 `chunks=[]` 时直接返回 `below_score_threshold`？

参考答案：

因为 generator 只接收最终 chunks，不知道上游检索过程中是否有候选、是否被 score_threshold 过滤、是否被权限过滤、是否向量库为空。下游模块不应该编造上游原因，所以当前只返回更准确的 `no_retrieved_chunks`。

### 练习 5：解释 suggestions 的边界

题目：

无资料返回里的 suggestions 能不能当成业务事实？为什么？

参考答案：

不能。suggestions 只是用户下一步操作建议，例如换问法、确认范围、记录知识缺口。它不来自知识库原文，也不是模型根据资料生成的事实答案。

## 七、自测问题

### 自测 1

问题：

`no_context` 是系统异常吗？

答案：

不是。它表示系统正常运行，但没有可用于回答的知识库上下文。

### 自测 2

问题：

无资料时 citations 应该是什么？

答案：

空列表 `[]`。

### 自测 3

问题：

为什么 `status` 比解析中文 `answer` 更适合程序判断？

答案：

因为 `status` 是稳定的机器可读字段，中文文案可能会调整。用字符串文案做程序判断很脆弱。

### 自测 4

问题：

`no_context_reason="no_retrieved_chunks"` 表示什么？

答案：

表示生成阶段没有收到可用的 retrieved chunks。它不具体说明上游为什么为空。

### 自测 5

问题：

无资料时为什么不调用模型生成 suggestions？

答案：

因为无资料时调用模型仍然可能产生幻觉或编造业务事实。固定 suggestions 更稳定、可测试，也不会产生模型费用。

### 自测 6

问题：

第 20 节和第 21 节的区别是什么？

答案：

第 20 节处理系统正常但没有检索上下文的业务状态。第 21 节会处理 embedding、向量库、模型调用等异常情况。

### 自测 7

问题：

有资料回答时 `suggestions` 应该是什么？

答案：

应该是空列表，因为 suggestions 是无资料兜底时给用户的下一步建议。

### 自测 8

问题：

为什么不能把无资料回答标记成 `answered`？

答案：

因为它不是基于检索资料生成的知识库回答，而是兜底状态。如果标记成 `answered`，前端、日志和评测都会误判。

## 八、你应该能口述出的版本

你可以这样向别人解释本节：

```text
第 20 节处理 RAG 中非常常见的情况：检索后没有可用 chunks。无结果不是系统异常，而是系统正常运行但没有找到可用于回答的知识库上下文。

这时不能继续调用模型硬答，因为那会让 RAG 退化成普通聊天，模型可能凭常识编造企业规则，也无法提供真实 citation。正确做法是返回结构化 no_context 状态。

本节把 RagAnswer 从 answer + citations 扩展为 answer、status、citations、no_context_reason 和 suggestions。有资料时 status 是 answered，并返回 citations；无资料时 status 是 no_context，citations 是空列表，reason 是 no_retrieved_chunks，并返回固定的用户建议。

需要注意，generator 只看到 chunks=[]，它不知道上游到底是完全没搜到、score_threshold 过滤空，还是权限过滤空，所以不能编造具体原因。第 20 节解决的是无资料业务状态，第 21 节才会讲 embedding、向量库、模型调用这些异常处理。
```

## 九、本节产出

新增：

- `notes/rag-stage4-20-no-context-handling.md`

修改：

- `projects/ai-service/app/rag/generator.py`
- `projects/ai-service/tests/test_rag_generator.py`
- `README.md`
- `docs/learning-progress.md`
- `docs/learning-resources.md`
- `projects/ai-service/README.md`
- `projects/ai-service/app/rag/README.md`

## 十、参考资料

- [阶段 4 第 17 节：score_threshold](rag-stage4-17-score-threshold.md)
- [阶段 4 第 18 节：把检索结果交给模型回答](rag-stage4-18-retrieved-context-to-model-answer.md)
- [阶段 4 第 19 节：引用来源：回答必须带出处](rag-stage4-19-citations.md)
- [阶段 2 第 11 节：模型调用错误处理](llm-api-stage2-11-model-error-handling.md)
- [阶段 1 第 14 节：统一异常处理](fastapi-stage1-14-exception-handling.md)
