# 阶段 6 第 7 节：RAG + Agent 组合评测

## 本节定位

前面三节我们已经完成了三类 eval：

```text
第 4 节：意图识别评测
第 5 节：工单字段提取评测
第 6 节：Agent 路由评测
```

这一节学习：

```text
RAG + Agent 组合评测
```

它关注的问题是：

```text
当 Agent 进入政策问答路线后，RAG 结果和 Agent 后续行为是否一起正确？
```

注意，这一节不是单独评测 RAG 检索。

也不是单独评测 Agent 路由。

而是把两者连起来看：

```text
用户问题
-> Agent 判断为 policy_question
-> 进入 retrieve_policy
-> RAG 返回 answered 或 no_context
-> Agent 根据 RAG 状态决定是否创建工单
```

这一节不需要打开虚拟机，不需要 Docker，不需要 Qdrant，不需要 Milvus。

当前仍然使用项目里的 fake RAG。

真实向量库、真实 embedding、真实 Milvus/Qdrant 的组合评测后面再学。

## 本节学习目标

学完本节，你应该能解释清楚：

1. 什么是 RAG + Agent 组合评测。
2. 为什么单独评测 RAG 召回还不够。
3. 为什么单独评测 Agent 路由也不够。
4. 什么是 `rag_answer_status`。
5. 什么是 `answered`。
6. 什么是 `no_context`。
7. 什么是 citation。
8. 什么是 expected sources。
9. 什么是 actual sources。
10. 什么是 source recall。
11. 为什么 answered 时不应该创建工单。
12. 为什么 no-context 时应该进入 policy_gap 工单。
13. 为什么 no-context 不能编造答案。
14. 为什么 `ticket_need_source` 要等于 `rag_no_context`。
15. 怎么输出 RAG + Agent bad cases。
16. 组合 eval 和前面三类 eval 的关系。

## 本节先不学什么

本节暂时不学习：

- 不接真实向量库。
- 不启动 Qdrant。
- 不启动 Milvus。
- 不调用真实 embedding 模型。
- 不真实调用大模型生成最终回答。
- 不评测语义答案好坏。
- 不用 LLM-as-judge。
- 不接 LangSmith 平台实验。
- 不把 eval 放入 CI。

这些都重要，但本节先把最核心的组合行为讲清楚：

```text
RAG 有答案 -> 引用正确 -> 不创建工单
RAG 没答案 -> 不编造 -> 转 policy_gap 工单
```

## 一、基础知识铺垫

### 1. 什么是 RAG

RAG 是 Retrieval-Augmented Generation 的缩写。

中文常说：

```text
检索增强生成
```

它的基本思路是：

```text
先从知识库检索相关资料
再基于资料生成回答
```

如果不用 RAG，大模型回答业务问题时可能只靠自己的参数记忆。

这会有两个问题：

- 模型可能不知道你公司自己的业务规则。
- 模型可能编造听起来合理但实际不存在的规则。

RAG 的作用是把回答约束在知识库资料上。

### 2. 什么是 Agent 里的 RAG 节点

在当前 Ticket Agent 里，RAG 不是独立系统。

它是 Agent 流程中的一个节点：

```text
retrieve_policy
```

当用户问题被识别为：

```text
policy_question
```

Agent 会进入：

```text
retrieve_policy
```

这个节点负责回答政策、规则、FAQ 类问题。

例如：

```text
退款多久到账？
账号有异常登录提醒，我应该怎么处理？
```

都应该进入 RAG 政策问答路线。

### 3. 什么是 RAG + Agent 组合

RAG + Agent 组合指的是：

```text
RAG 不只是返回资料，它的结果还会影响 Agent 后续决策。
```

当前项目里，RAG 返回两种核心状态：

```text
answered
no_context
```

如果是：

```text
answered
```

Agent 应该认为知识库已经能回答，通常不需要创建工单。

如果是：

```text
no_context
```

Agent 应该认为知识库没有足够资料，不能编造答案，可以进入 policy_gap 工单。

这就是组合行为。

### 4. 为什么单独评测 RAG 还不够

单独 RAG 评测通常会看：

```text
检索到了什么文档？
source 对不对？
chunk 对不对？
recall@k 多少？
```

这很重要。

但它还不能回答：

```text
RAG 结果出来后，Agent 有没有做对后续业务决策？
```

例如 RAG 正确返回了 no-context。

但 Agent 没有进入工单流程，而是直接回答：

```text
会员积分可以兑换礼品。
```

这就是错误。

单独 RAG 检索可能是对的，但 Agent 后续行为错了。

所以需要 RAG + Agent 组合评测。

### 5. 为什么单独 Agent 路由还不够

第 6 节我们评测了 Agent 路由路径。

路由 eval 能检查：

```text
有没有经过 retrieve_policy
有没有经过 decide_ticket_need
有没有进入 request_ticket_confirmation
```

但路由 eval 不会细看：

```text
RAG citation source 是否正确
RAG 状态是 answered 还是 no_context
expected_sources 是否匹配
```

例如路径是对的：

```text
retrieve_policy -> decide_ticket_need
```

但 citation source 错了。

路由 eval 不一定能发现。

所以需要组合 eval 检查 RAG 内容信号和 Agent 决策。

### 6. 什么是 rag_answer_status

`rag_answer_status` 表示 RAG 回答状态。

当前有两个关键状态：

```text
answered
no_context
```

它不是最终答案文本。

它是一个结构化状态。

Agent 根据这个状态决定后续动作。

如果：

```text
rag_answer_status = answered
```

说明知识库有资料支持回答。

如果：

```text
rag_answer_status = no_context
```

说明知识库没有找到足够资料。

### 7. 什么是 answered

`answered` 表示：

```text
RAG 找到了可用资料，并生成了有依据的回答。
```

例如：

```text
用户：退款多久到账？
```

fake RAG 返回：

```text
rag_answer_status: answered
rag_citations: refund-return-policy.md
```

这时 Agent 应该：

```text
needs_ticket: false
ticket_need_source: rag_answered
```

也就是：

```text
知识库已经回答了，不需要创建工单。
```

### 8. 什么是 no_context

`no_context` 表示：

```text
RAG 没找到足够资料支撑回答。
```

例如：

```text
用户：会员积分怎么兑换礼品？
```

当前知识库没有会员积分资料。

fake RAG 返回：

```text
rag_answer_status: no_context
rag_citations: []
```

这时 Agent 不应该编造会员积分规则。

它应该进入：

```text
policy_gap 工单
```

也就是：

```text
needs_ticket: true
ticket_need_source: rag_no_context
issue_type: policy_gap
```

### 9. 什么是 citation

citation 是引用来源。

在 RAG 里，它表示：

```text
这段回答基于哪份资料。
```

当前 citation 里有：

```text
source
title
section
chunk_id
score
```

例如：

```text
source: refund-return-policy.md
title: 退款退货规则
section: 退款申请
chunk_id: refund_return_policy_chunk_0001
```

citation 的价值是让回答可追溯。

用户和开发者可以知道答案来自哪里。

### 10. 什么是 expected sources

`expected sources` 是测试样本里提前写好的期望引用来源。

例如：

```json
"expected_sources": ["refund-return-policy.md"]
```

这表示：

```text
这条样本如果 answered，至少应该引用 refund-return-policy.md。
```

如果实际引用了：

```text
account-security-faq.md
```

那就是错的。

### 11. 什么是 actual sources

`actual sources` 是 Agent 实际运行后，从 `rag_citations` 里提取出来的来源。

例如实际 citation 是：

```python
[
    {
        "source": "refund-return-policy.md",
        "title": "退款退货规则",
        "section": "退款申请",
    }
]
```

那么 actual sources 是：

```text
refund-return-policy.md
```

组合 eval 会比较：

```text
expected_sources
actual_sources
```

### 12. 什么是 source recall

source recall 表示：

```text
期望来源里，有多少被实际命中了。
```

公式：

```text
source_recall = matched_sources / expected_sources
```

当前第 7 节有两个 expected source：

```text
refund-return-policy.md
account-security-faq.md
```

两个都命中：

```text
source_recall = 2 / 2 = 1.0
```

### 13. 为什么 answered 时不应该创建工单

如果知识库已经能回答用户的问题，通常不需要创建工单。

例如：

```text
退款多久到账？
```

如果知识库给出了退款规则引用，Agent 应该回答政策。

它不应该把用户引导到：

```text
创建工单确认
```

否则会造成不必要的人工处理。

所以 answered 样本 expected 是：

```text
should_create_ticket: false
ticket_need_source: rag_answered
```

### 14. 为什么 no-context 时应该进入 policy_gap 工单

如果知识库没有资料，Agent 不能编造答案。

例如：

```text
会员积分怎么兑换礼品？
```

当前知识库没有会员积分资料。

正确行为是：

```text
说明没有足够资料
进入 policy_gap 工单或人工处理
```

这背后的业务含义是：

```text
知识库存在缺口，需要人工补充或解释。
```

所以 expected 是：

```text
ticket_need_source: rag_no_context
expected_issue_type: policy_gap
confirmation_required: true
```

### 15. 什么是 policy_gap

`policy_gap` 表示政策知识库缺口。

它不是退款问题，不是物流问题，也不是普通投诉。

它表示：

```text
用户问的是政策类问题，但知识库没有足够资料。
```

这类问题适合生成一张内部工单，提醒人工补充知识库或处理用户疑问。

### 16. 什么是 must_not_fabricate

`must_not_fabricate` 表示不能编造。

在 RAG no-context 场景里尤其重要。

如果没有资料，Agent 不应该说：

```text
会员积分可以兑换礼品，100 积分兑换 10 元优惠券。
```

因为知识库没有这个依据。

当前本节不做复杂语义判断。

我们通过结构信号评测：

```text
rag_answer_status == no_context
rag_citations == []
ticket_need_source == rag_no_context
issue_type == policy_gap
```

这些信号共同说明 Agent 没有按“有资料回答”路线处理。

### 17. RAG + Agent 组合 eval 的核心问题

这一节只问三件事：

```text
RAG 状态对不对？
引用来源对不对？
Agent 根据 RAG 状态做的后续业务决策对不对？
```

这三件事缺一不可。

如果 RAG 状态对，引用错了，说明依据错。

如果引用对，Agent 决策错了，说明后续流程错。

如果 Agent 决策对，但 RAG no-context 时还带 citation，说明 no-context 信号不干净。

### 18. 本节和真实向量库评测的关系

当前本节用 fake RAG。

fake RAG 的好处是：

- 稳定。
- 不依赖 Docker。
- 不依赖向量库。
- 不依赖 embedding。
- 不受网络影响。
- 适合先学组合 eval 的结构。

后面接真实向量库时，组合 eval 的思想不变。

变化的是 RAG 节点底层从 fake 变成真实检索。

届时我们会关注更多指标：

```text
top_k
hit_rate
recall
precision
rerank
latency
```

但本节先把组合行为学清楚。

## 二、本节主题系统讲解

### 1. 本节新增了什么

本节新增：

```text
projects/ai-service/app/agents/rag_agent_evaluation.py
projects/ai-service/scripts/agent_rag_eval.py
projects/ai-service/tests/test_agent_rag_evaluation.py
notes/stage6-07-rag-agent-combination-evaluation.md
```

没有修改 `agent_cases.json`。

没有接入真实向量库。

没有新增 API。

### 2. 本节评测哪些样本

本节只选择：

```text
expected.rag 存在的样本
```

当前有 3 条：

```text
agent_policy_refund_arrival_001
agent_policy_account_security_001
agent_no_context_membership_points_001
```

这三条正好覆盖：

```text
退款政策 answered
账号安全 answered
会员积分 no_context
```

### 3. 退款政策 answered 样本

输入：

```text
退款多久到账？
```

期望：

```text
rag_answer_status: answered
expected_sources: refund-return-policy.md
must_cite: true
should_create_ticket: false
```

实际：

```text
rag_answer_status: answered
actual_sources: refund-return-policy.md
needs_ticket: false
ticket_need_source: rag_answered
```

这条通过。

### 4. 账号安全 answered 样本

输入：

```text
账号有异常登录提醒，我应该怎么处理？
```

期望：

```text
rag_answer_status: answered
expected_sources: account-security-faq.md
must_cite: true
should_create_ticket: false
```

实际：

```text
rag_answer_status: answered
actual_sources: account-security-faq.md
needs_ticket: false
ticket_need_source: rag_answered
```

这条通过。

这条样本也延续了第 6 节的修正：

```text
异常登录
```

现在能正确命中账号安全 fake RAG。

### 5. 会员积分 no-context 样本

输入：

```text
会员积分怎么兑换礼品？
```

期望：

```text
rag_answer_status: no_context
expected_sources: []
should_create_ticket: true
ticket_need_source: rag_no_context
expected_issue_type: policy_gap
confirmation_required: true
```

实际：

```text
rag_answer_status: no_context
actual_sources: []
needs_ticket: true
ticket_need_source: rag_no_context
issue_type: policy_gap
ticket_confirmation_required: true
```

这条通过。

### 6. 本节完整评测链路

完整链路是：

```text
读取 agent_cases.json
-> 选择 expected.rag 存在的样本
-> 运行 run_ticket_agent(message)
-> 读取 rag_answer_status
-> 读取 rag_citations 里的 source
-> 比较 expected_sources 和 actual_sources
-> 检查 must_cite
-> 检查 should_create_ticket
-> 检查 ticket_need_source
-> 检查 no-context 是否转 policy_gap 工单
-> 汇总 case_pass_rate / source_recall
-> 输出 bad cases
```

### 7. 本节为什么不只看 source

只看 source 不够。

例如：

```text
actual_sources = refund-return-policy.md
```

这只能说明引用来源对。

但还要看：

```text
rag_answer_status 是否 answered
needs_ticket 是否 false
ticket_need_source 是否 rag_answered
```

否则可能出现：

```text
引用对了，但仍然创建工单
```

这就是组合错误。

### 8. 本节为什么不只看 should_create_ticket

只看是否创建工单也不够。

例如：

```text
should_create_ticket = false
actual_should_create_ticket = false
```

这看起来对。

但如果 source 错了，回答依据仍然错。

所以要同时看 RAG 信号和 Agent 决策。

### 9. 本节为什么不做 LLM-as-judge

LLM-as-judge 可以判断回答语义质量。

但本节还不需要。

因为我们当前重点是结构化组合行为：

```text
status
source
ticket decision
ticket_need_source
issue_type
confirmation_required
```

这些都可以用规则 evaluator 判断。

先把能确定判断的部分做稳，再引入 LLM judge。

### 10. 本节输出指标

本节脚本输出：

```text
case_pass_rate
answered_cases
answered_passed_cases
no_context_cases
no_context_passed_cases
expected_sources
matched_sources
source_recall
citation_passed_count
ticket_decision_passed_count
p0_case_pass_rate
```

这些指标分别看不同层面。

不是只看一个 accuracy。

### 11. source_recall 的意义

当前 source recall 是：

```text
2 / 2 = 1.0
```

说明两个 expected source 都命中。

如果某次改动后账号安全引用变成退款文档：

```text
expected_sources: account-security-faq.md
actual_sources: refund-return-policy.md
```

source recall 会下降。

bad case 会显示 missing source。

### 12. ticket_decision_passed_count 的意义

这个指标看：

```text
RAG 结果出来后，Agent 是否做了正确工单决策。
```

answered 样本应该：

```text
not create ticket
```

no-context 样本应该：

```text
create policy_gap ticket
```

这就是 RAG + Agent 的连接点。

### 13. no_context_passed_cases 的意义

no-context 是 RAG 系统非常重要的安全边界。

当没有资料时，系统不能假装有资料。

`no_context_passed_cases` 表示这些无上下文样本是否正确处理。

当前是：

```text
1 / 1
```

也就是唯一 no-context 样本通过。

## 三、新增代码讲解

### 1. `rag_agent_evaluation.py` 的定位

新增文件：

```text
projects/ai-service/app/agents/rag_agent_evaluation.py
```

它负责 RAG + Agent 组合 eval。

它不是 RAG 检索模块。

也不是业务 Agent 节点。

它只负责评测：

```text
RAG 结构信号 + Agent 后续决策
```

### 2. `select_rag_agent_eval_cases()`

这个函数负责筛选样本。

逻辑是：

```text
expected.rag 是 dict
```

也就是只选择有 RAG 期望的样本。

当前选出 3 条。

这和第 5 节字段 eval 类似：

```text
不同 evaluator 只消费自己负责的样本子集。
```

### 3. `RagAgentEvalCaseResult`

这个模型表示单条组合评测结果。

它包含：

```text
expected_rag_answer_status
actual_rag_answer_status
expected_sources
actual_sources
matched_sources
missing_sources
unexpected_sources
expected_must_cite
citations_present
expected_should_create_ticket
actual_should_create_ticket
expected_ticket_need_source
actual_ticket_need_source
expected_issue_type
actual_issue_type
expected_confirmation_required
actual_confirmation_required
node_history
passed
failed_reasons
```

它把 RAG 和 Agent 两边的关键结果放在一起。

### 4. `RagAgentEvalSummary`

这个模型表示整体报告。

它包含：

```text
case_count
passed_case_count
failed_case_count
case_pass_rate
answered_case_count
answered_passed_case_count
no_context_case_count
no_context_passed_case_count
expected_source_count
matched_source_count
source_recall
citation_passed_count
ticket_decision_passed_count
p0_case_pass_rate
```

这能同时看：

- answered 场景。
- no-context 场景。
- source 命中。
- citation 是否存在。
- 工单决策是否正确。

### 5. `evaluate_rag_agent_case()`

这是单条组合 eval 的核心函数。

它做这些事：

```text
读取 expected.rag
读取 expected.ticket
运行 Agent
读取 actual rag_answer_status
读取 actual rag_citations
比较 expected_sources
比较 citation 是否存在
比较 should_create_ticket
比较 ticket_need_source
比较 policy_gap issue_type
比较 confirmation_required
收集 failed_reasons
```

这就是组合 eval 的核心。

### 6. 为什么 expected status 从 expect_context 推导

样本里目前写的是：

```json
"expect_context": true
```

或：

```json
"expect_context": false
```

本节把它推导成：

```text
true -> answered
false -> no_context
```

这符合当前 fake RAG 的状态模型。

后面如果 RAG 状态更多，可以把 expected status 显式写入样本。

### 7. `_citation_sources()`

这个函数从 `rag_citations` 里提取 source。

例如：

```python
[
    {"source": "refund-return-policy.md"},
    {"source": "refund-return-policy.md"},
]
```

会得到：

```text
["refund-return-policy.md"]
```

它会去重。

因为本节 source recall 看的是来源是否命中，不看同一来源出现几次。

### 8. `_actual_should_create_ticket()`

这个函数判断实际是否进入工单流程。

逻辑和前面字段 eval 保持一致：

```text
needs_ticket == True
或者 ticket_fields 存在
```

这样可以兼容不同节点状态。

### 9. no_context_behavior_passed

这个布尔值专门判断 no-context 行为。

对于 no-context 样本，它要求：

```text
actual_rag_answer_status == no_context
actual_sources == []
actual_should_create_ticket == true
actual_ticket_need_source == rag_no_context
```

这些同时满足，才说明 no-context 行为通过。

### 10. `format_rag_agent_bad_cases()`

这个函数输出坏样本。

如果没有失败：

```text
No bad cases.
```

如果失败，会显示：

```text
case_id
expected_status
actual_status
expected_sources
actual_sources
failed_reasons
```

这能直接定位是：

- RAG 状态错。
- source 错。
- citation 缺失。
- 工单决策错。
- no-context 没转工单。

### 11. `agent_rag_eval.py`

新增脚本：

```text
projects/ai-service/scripts/agent_rag_eval.py
```

运行方式：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run python scripts/agent_rag_eval.py
```

它会输出 RAG + Agent 组合评测报告。

### 12. `test_agent_rag_evaluation.py`

新增测试：

```text
projects/ai-service/tests/test_agent_rag_evaluation.py
```

测试覆盖：

- 只选出 3 条 RAG 样本。
- 退款 answered 样本通过。
- 账号安全 answered 样本通过。
- 会员积分 no-context 转 policy_gap 工单通过。
- 错误 source 能变成 bad case。
- no-context 没转工单能变成 bad case。
- summary 和 bad cases 输出可读。

## 四、本节运行结果

手动运行：

```powershell
uv run python scripts/agent_rag_eval.py
```

输出：

```text
RAG + Agent evaluation summary
cases: 3
passed_cases: 3
failed_cases: 0
case_pass_rate: 1.0000
answered_cases: 2
answered_passed_cases: 2
no_context_cases: 1
no_context_passed_cases: 1
expected_sources: 2
matched_sources: 2
source_recall: 1.0000
citation_passed_count: 3
ticket_decision_passed_count: 3
p0_cases: 3
p0_passed_cases: 3
p0_failed_cases: 0
p0_case_pass_rate: 1.0000
No bad cases.
```

相关测试：

```powershell
uv run pytest tests/test_agent_rag_evaluation.py tests/test_agent_route_evaluation.py tests/test_agent_field_evaluation.py tests/test_agent_intent_evaluation.py tests/test_ticket_agent_intent.py -q
```

结果：

```text
130 passed
```

## 五、怎么阅读本节输出

### `cases: 3`

表示本节只评测 3 条 RAG 样本。

不是全部 12 条。

因为只有 3 条样本定义了 `expected.rag`。

### `answered_cases: 2`

表示有 2 条样本期望 RAG 能回答。

它们是：

```text
退款多久到账？
账号有异常登录提醒，我应该怎么处理？
```

### `no_context_cases: 1`

表示有 1 条样本期望 RAG 无资料。

它是：

```text
会员积分怎么兑换礼品？
```

### `expected_sources: 2`

表示 answered 样本一共期望 2 个来源：

```text
refund-return-policy.md
account-security-faq.md
```

### `matched_sources: 2`

表示这 2 个来源都命中。

### `source_recall: 1.0000`

表示来源召回率是 100%。

### `ticket_decision_passed_count: 3`

表示 3 条样本的工单决策都正确。

answered 的 2 条没有创建工单。

no-context 的 1 条进入了 `rag_no_context` 工单。

### `No bad cases.`

表示没有失败样本。

如果有失败，就要看：

```text
expected_status
actual_status
expected_sources
actual_sources
failed_reasons
```

## 六、常见误区

### 误区 1：RAG 找到文档就算成功

不一定。

找到了文档，还要看：

```text
文档是不是 expected source
Agent 是否根据 RAG 状态做了正确决策
```

### 误区 2：answered 就一定不能创建工单

通常政策已回答时不需要创建工单。

但未来可能有例外。

例如用户同时问政策并明确要求投诉。

本节样本没有这种混合场景。

当前规则是：

```text
纯政策 answered -> 不创建工单
```

### 误区 3：no-context 就直接回答“没有资料”结束

不一定。

在我们的智能工单 Agent 中，no-context 表示知识库缺口。

它应该进入：

```text
policy_gap 工单
```

这样后续可以人工处理或补充知识库。

### 误区 4：citation 只是展示用

不是。

citation 是 RAG 可信度的重要组成。

没有 citation，就很难追溯回答依据。

本节的 `must_cite` 就是为了约束 answered 样本必须有引用。

### 误区 5：fake RAG 没有学习价值

fake RAG 不代表真实检索能力。

但它非常适合学习组合 eval。

因为它稳定可控，能让你先理解：

```text
RAG 状态如何影响 Agent 后续行为
```

真实向量库只是把底层检索替换掉，组合 eval 的结构仍然可复用。

## 七、本节练习

### 练习 1：解释 RAG + Agent 组合评测

请回答：

```text
什么是 RAG + Agent 组合评测？
```

参考答案：

```text
RAG + Agent 组合评测不是只看 RAG 有没有返回文档，也不是只看 Agent 路由是否正确。
它会同时检查 RAG 的状态、引用来源，以及 Agent 根据 RAG 结果做出的后续业务决策。
例如 answered 时不创建工单，no_context 时转 policy_gap 工单。
```

### 练习 2：判断 answered 场景

用户输入：

```text
退款多久到账？
```

期望有哪些关键结果？

参考答案：

```text
rag_answer_status: answered
expected source: refund-return-policy.md
citations_present: true
should_create_ticket: false
ticket_need_source: rag_answered
```

### 练习 3：判断 no-context 场景

用户输入：

```text
会员积分怎么兑换礼品？
```

期望有哪些关键结果？

参考答案：

```text
rag_answer_status: no_context
expected_sources: []
actual_sources: []
should_create_ticket: true
ticket_need_source: rag_no_context
issue_type: policy_gap
confirmation_required: true
```

### 练习 4：解释为什么 no-context 不能编造

参考答案：

```text
no-context 表示知识库没有足够资料。
如果 Agent 在没有资料时直接编造会员积分规则，就会给用户错误信息。
正确做法是承认资料不足，并进入 policy_gap 工单或人工处理。
```

### 练习 5：计算 source_recall

一共有 4 个 expected sources，实际命中 3 个。

source_recall 是多少？

参考答案：

```text
source_recall = 3 / 4 = 0.75
```

### 练习 6：分析 bad case

假设：

```text
expected_sources: ["refund-return-policy.md"]
actual_sources: ["account-security-faq.md"]
```

这是什么问题？

参考答案：

```text
这是引用来源错误。
用户可能问的是退款政策，但系统引用了账号安全文档。
RAG + Agent eval 应该把 refund-return-policy.md 标记为 missing source，并输出 bad case。
```

### 练习 7：手动运行本节 eval

运行：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run python scripts/agent_rag_eval.py
```

重点看哪些指标？

参考答案：

```text
重点看：

cases
answered_cases
no_context_cases
expected_sources
matched_sources
source_recall
citation_passed_count
ticket_decision_passed_count
p0_case_pass_rate
bad cases

如果 failed_cases 大于 0，要继续看 expected_status、actual_status、expected_sources、actual_sources 和 failed_reasons。
```

## 八、自测题

### 自测 1：什么是 rag_answer_status？

答案：

```text
rag_answer_status 是 RAG 回答状态，当前重点是 answered 和 no_context。
它会影响 Agent 后续是否创建工单。
```

### 自测 2：answered 表示什么？

答案：

```text
answered 表示 RAG 找到了可用资料，并能给出有依据的回答。
```

### 自测 3：no_context 表示什么？

答案：

```text
no_context 表示 RAG 没找到足够资料支撑回答。
```

### 自测 4：为什么 answered 时通常不创建工单？

答案：

```text
因为知识库已经能回答用户政策问题，不需要额外创建人工工单。
```

### 自测 5：为什么 no-context 时要进入 policy_gap？

答案：

```text
因为用户问的是政策问题，但知识库没有资料。
这说明知识库存在缺口，适合生成 policy_gap 工单交给人工处理或补充知识库。
```

### 自测 6：citation 的作用是什么？

答案：

```text
citation 用来说明回答依据来自哪里，让回答可追溯。
```

### 自测 7：source_recall 怎么算？

答案：

```text
source_recall = matched_sources / expected_sources
```

### 自测 8：为什么本节不接真实向量库？

答案：

```text
因为本节目标是学习 RAG 状态和 Agent 后续决策的组合 eval。
fake RAG 稳定、可控、不依赖 Docker 和向量库，更适合先把组合评测结构学清楚。
```

### 自测 9：RAG + Agent eval 和路由 eval 有什么区别？

答案：

```text
路由 eval 看实际节点路径是否正确。
RAG + Agent eval 看 RAG 状态、引用来源和 Agent 后续工单决策是否一起正确。
```

### 自测 10：本节最重要的工程思想是什么？

答案：

```text
RAG 不能只看检索结果，Agent 也不能只看路径。
真正的业务质量要看 RAG 返回的状态和引用，是否驱动 Agent 做出正确后续决策。
```

## 九、本节你应该形成的表达能力

你可以这样向别人解释本节：

```text
我们给智能工单 Agent 增加了 RAG + Agent 组合评测。
它会从固定 agent_cases.json 里选择 expected.rag 存在的样本，运行完整 Agent 后检查 rag_answer_status、rag_citations 的 source、是否满足 must_cite，以及 Agent 根据 RAG 状态做出的工单决策。
对于 answered 样本，要求引用 expected source，并且不创建工单。
对于 no_context 样本，要求没有引用来源，不编造答案，并转入 rag_no_context 的 policy_gap 工单。
这样可以发现单独 RAG 检索评测和单独路由评测都不一定能发现的组合问题。
```

能讲清楚这段，说明你理解了本节的核心。

## 十、本节小结

本节完成了阶段 6 第四类真实 eval：

```text
RAG + Agent 组合评测
```

当前结果：

```text
3 条 RAG 样本全部通过
2 条 answered 样本全部通过
1 条 no-context 样本通过
source_recall = 1.0000
ticket_decision_passed_count = 3
没有 bad cases
```

本节最重要的知识是：

```text
RAG answered -> 应该有 citation -> 不创建工单
RAG no_context -> 不应该编造 -> 转 policy_gap 工单
组合 eval 同时检查 RAG 结构信号和 Agent 后续业务决策
```

下一节会学习：

```text
评测脚本设计
```

## 十一、参考资料

- [阶段 6 第 3 节：设计 Agent 测试集](stage6-03-agent-eval-dataset-design.md)
- [阶段 6 第 4 节：意图识别评测](stage6-04-agent-intent-evaluation.md)
- [阶段 6 第 5 节：工单字段提取评测](stage6-05-agent-ticket-field-evaluation.md)
- [阶段 6 第 6 节：Agent 路由评测](stage6-06-agent-route-evaluation.md)
- [LangSmith Evaluation Concepts](https://docs.langchain.com/langsmith/evaluation-concepts)
- [LangSmith Example data format](https://docs.langchain.com/langsmith/example-data-format)
- [LangChain Retrieval](https://docs.langchain.com/oss/python/langchain/retrieval)
- [Pydantic Validators](https://docs.pydantic.dev/latest/concepts/validators/)
- [pytest 官方文档](https://docs.pytest.org/)
