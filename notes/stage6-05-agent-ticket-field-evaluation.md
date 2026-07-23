# 阶段 6 第 5 节：工单字段提取评测

## 本节定位

上一节我们完成了：

```text
意图识别评测
```

它回答的问题是：

```text
用户这句话应该进入哪条业务路线？
```

这一节往后走一步，学习：

```text
工单字段提取评测
```

它回答的问题是：

```text
当用户确实需要创建工单时，Agent 有没有把工单字段抽对？
```

例如：

```text
用户：订单 A1002 三天没有物流更新了，我很着急，请帮我创建工单催一下
```

我们期望 Agent 抽出：

```text
issue_type: logistics
order_id: A1002
user_request: 创建工单
urgency: high
need_human_review: true
missing_ticket_fields: []
confirmation_required: true
```

如果这些字段错了，后果比普通回答措辞错更严重。

因为这些字段后面可能会变成 Java 后端的工单创建参数。

本节不需要虚拟机，不需要 Docker，不需要 Qdrant，不需要 Milvus，也不需要真实调用大模型。

本节仍然使用本地固定样本：

```text
projects/ai-service/data/agent_eval/agent_cases.json
```

## 本节学习目标

学完本节，你应该能解释清楚：

1. 什么是字段提取。
2. 工单字段提取和意图识别有什么区别。
3. 为什么字段提取评测要比意图识别评测更细。
4. 什么是 expected fields。
5. 什么是 actual fields。
6. 哪些字段适合精确匹配。
7. 哪些字段暂时不适合精确匹配。
8. 什么是 case 级通过率。
9. 什么是 field 级准确率。
10. 为什么要评测 `missing_ticket_fields`。
11. 为什么要评测 `confirmation_required`。
12. 为什么要评测 `ticket_need_source`。
13. 为什么字段 eval 要跑完整 Agent 流程，而不是只测一个函数。
14. bad case 怎么定位到具体字段。
15. eval 如何反过来推动代码规则修正。

## 本节先不学什么

本节只学习工单字段提取 eval，不提前学习：

- 不真实创建 Java 工单。
- 不真实调用 LLM 做字段抽取。
- 不评测最终回复是否自然。
- 不评测 RAG 召回质量。
- 不评测工具调用参数。
- 不评测多轮对话补全字段。
- 不接入 LangSmith 实验平台。
- 不把 eval 放进 CI。

这些后面会逐步学。

本节只把“字段提取是否符合 expected”这件事讲扎实。

## 一、基础知识铺垫

### 1. 什么是字段

字段就是结构化数据里的一个属性。

例如一张工单里可能有：

```text
问题类型
订单号
问题描述
用户诉求
紧急程度
是否需要人工复核
```

在代码里，它们对应：

```text
issue_type
order_id
description
user_request
urgency
need_human_review
```

字段的作用是把自然语言变成系统能处理的数据。

用户说：

```text
订单 A1002 三天没有物流更新了，我很着急，请帮我创建工单催一下
```

系统不能直接把这一整句话随便扔给后端。

它需要拆成：

```text
issue_type = logistics
order_id = A1002
user_request = 创建工单
urgency = high
need_human_review = true
```

这就是字段提取。

### 2. 什么是字段提取

字段提取就是从用户自然语言里提取结构化信息。

输入是：

```text
一段用户说的话
```

输出是：

```text
一组字段和值
```

例如：

```text
输入：订单 A1003 退货后还没退款，请帮我创建退款工单处理
```

输出：

```text
issue_type: refund
order_id: A1003
user_request: 创建工单
urgency: normal
need_human_review: true
```

字段提取是很多 AI 应用里非常常见的任务。

典型场景包括：

- 从用户描述里提取工单字段。
- 从聊天里提取订单号。
- 从简历里提取姓名、学历、工作年限。
- 从发票里提取金额、税号、日期。
- 从客服对话里提取投诉原因。
- 从合同里提取甲方、乙方、付款条款。

只要你看到“自然语言 -> 结构化数据”，就要想到字段提取。

### 3. 字段提取和意图识别的区别

意图识别回答：

```text
用户想做哪一类事？
```

字段提取回答：

```text
这类事里需要哪些具体参数？
```

例如：

```text
用户：订单 A1002 三天没有物流更新了，我很着急，请帮我创建工单催一下
```

意图识别结果：

```text
ticket_request
```

字段提取结果：

```text
issue_type: logistics
order_id: A1002
urgency: high
```

你可以把它们理解成两层：

```text
第一层：判断走哪条路
第二层：准备这条路需要的参数
```

意图识别错了，流程会走错。

字段提取错了，流程可能走对了，但参数会错。

### 4. 为什么字段提取比意图识别更复杂

意图识别通常是从几个类别里选一个：

```text
policy_question
order_query
ticket_request
smalltalk
unsupported
unclear
```

字段提取则要同时判断多个字段：

```text
issue_type
order_id
user_request
urgency
need_human_review
missing_ticket_fields
confirmation_required
```

每个字段都可能对，也可能错。

例如：

```text
issue_type 对了
order_id 对了
user_request 对了
urgency 错了
need_human_review 对了
```

这时整条 case 是否通过？

字段级准确率是多少？

坏样本应该怎么展示？

这就是字段评测更复杂的原因。

字段提取不是单个标签判断，而是多字段结构判断。

### 5. 什么是 expected fields

`expected fields` 是样本里提前写好的期望字段。

例如：

```json
{
  "expected_fields": {
    "issue_type": "logistics",
    "order_id": "A1002",
    "user_request": "创建工单",
    "urgency": "high",
    "need_human_review": true
  }
}
```

这表示：

```text
这条样本中，我们要求这些字段必须抽对。
```

注意，expected fields 不一定要包含所有字段。

本节有意没有把 `description` 放进 expected fields。

原因后面会讲。

### 6. 什么是 actual fields

`actual fields` 是当前 Agent 实际抽出来的字段。

例如 Agent 运行后得到：

```python
{
    "issue_type": "logistics",
    "order_id": "A1002",
    "description": "订单 A1002 三天没有物流更新了，我很着急，请帮我创建工单催一下",
    "user_request": "创建工单",
    "urgency": "high",
    "need_human_review": True,
}
```

eval 会拿 actual fields 和 expected fields 对比。

对比结果可能是：

```text
issue_type: pass
order_id: pass
user_request: pass
urgency: pass
need_human_review: pass
```

如果 urgency 实际是 `normal`，就会变成：

```text
urgency: fail
```

### 7. 什么字段适合精确匹配

精确匹配就是：

```text
actual_value == expected_value
```

本节适合精确匹配的字段包括：

```text
issue_type
order_id
user_request
urgency
need_human_review
```

原因是这些字段值比较稳定。

例如：

```text
order_id: A1002
```

错一个字符就是错。

再比如：

```text
urgency: high
```

如果 expected 是 `high`，actual 是 `normal`，业务含义就不同。

所以要精确匹配。

### 8. 什么字段暂时不适合精确匹配

本节没有精确匹配：

```text
description
```

原因是 description 是自然语言摘要或描述。

它可能有多种合理表达。

例如下面两种都可能合理：

```text
订单 A1002 三天没有物流更新了，我很着急，请帮我创建工单催一下
```

和：

```text
用户反馈订单 A1002 三天无物流更新，希望创建工单催促处理。
```

它们文字不一样，但语义接近。

如果现在强行做精确匹配，可能会让 eval 变得过于脆弱。

所以本节先只评测稳定字段。

后面如果要评测 description，可以有几种方式：

- 检查是否包含订单号。
- 检查是否包含核心问题。
- 检查长度是否合理。
- 用 LLM-as-judge 判断语义是否覆盖。
- 用人工抽检。

这是字段 eval 的重要思想：

**不是所有字段都适合用同一种比较方式。**

### 9. 什么是 missing_ticket_fields

`missing_ticket_fields` 表示创建工单前还缺哪些字段。

例如：

```text
用户：我要投诉商家一直不发货，麻烦人工处理
```

这句话说明了：

```text
issue_type: complaint
user_request: 投诉处理
```

但没有订单号。

而投诉、退款、物流类问题通常需要订单号。

所以 expected 是：

```text
missing_ticket_fields: ["order_id"]
```

这很重要。

Agent 不能在缺订单号时假装字段完整。

正确行为应该是追问：

```text
请补充相关订单号。
```

### 10. 为什么要评测缺字段

缺字段评测是工单 Agent 的安全边界之一。

如果缺字段识别错了，会有两种问题。

第一种，漏报缺字段：

```text
用户没给订单号
Agent 却认为字段完整
```

后果是后端可能收到不完整工单。

第二种，误报缺字段：

```text
用户已经给了订单号
Agent 却继续追问订单号
```

后果是用户体验很差。

所以缺字段评测必须单独看。

### 11. 什么是 confirmation_required

`confirmation_required` 表示是否需要用户确认后才能继续创建工单。

完整字段样本应该是：

```text
confirmation_required: true
```

因为创建工单是一个会影响业务系统的动作。

在真正创建前，应该让用户确认：

```text
请确认是否按以下信息创建工单。
```

缺字段样本应该是：

```text
confirmation_required: false
```

因为字段还不完整，不能进入确认创建。

这就是确认边界。

### 12. 为什么要评测 confirmation_required

如果确认边界错了，会有两个风险。

第一种风险：

```text
字段完整，但 Agent 没有请求确认
```

后面就可能直接创建工单，缺少用户确认。

第二种风险：

```text
字段不完整，但 Agent 进入确认
```

用户会确认一张信息不完整的工单。

所以本节把 `confirmation_required` 纳入字段 eval。

它不是字段本身，但它和字段完整性紧密相关。

### 13. 什么是 ticket_need_source

`ticket_need_source` 表示为什么需要创建工单。

当前有两类重点来源：

```text
explicit_user_request
rag_no_context
```

`explicit_user_request` 表示用户明确说要投诉、人工处理或创建工单。

例如：

```text
订单 A1002 三天没有物流更新了，我很着急，请帮我创建工单催一下
```

`rag_no_context` 表示用户问的是政策问题，但知识库没有资料，所以转为工单或人工处理。

例如：

```text
会员积分怎么兑换礼品？
```

如果这个问题知识库没有资料，Agent 可以进入政策缺口工单：

```text
issue_type: policy_gap
ticket_need_source: rag_no_context
```

### 14. 为什么要评测 ticket_need_source

同样是创建工单，原因可能不同。

用户明确要投诉，和知识库没查到资料，业务含义不一样。

如果来源错了，后面工单分类、优先级、处理人和统计报表都可能受影响。

所以本节不仅看字段，还看：

```text
ticket_need_source
```

### 15. 什么是 case 级通过率

case 级通过率看的是：

```text
一整条样本是否完全通过。
```

只要这个 case 有一个关键字段错了，case 就失败。

例如一条样本有 5 个 expected 字段：

```text
issue_type: pass
order_id: pass
user_request: pass
urgency: fail
need_human_review: pass
```

字段级看是：

```text
4 / 5 = 80%
```

但 case 级看是：

```text
fail
```

case 级更严格。

### 16. 什么是 field 级准确率

field 级准确率看的是：

```text
所有 expected 字段里，有多少字段匹配成功。
```

公式是：

```text
field_accuracy = matched_field_count / expected_field_count
```

例如 4 条样本一共检查 16 个字段。

如果 16 个都对：

```text
field_accuracy = 16 / 16 = 1.0
```

如果错 2 个：

```text
field_accuracy = 14 / 16 = 0.875
```

field 级指标能告诉你系统距离正确差多少。

case 级指标能告诉你完整业务样本是否可用。

两个都要看。

### 17. 为什么字段 eval 要跑完整 Agent

本节没有只调用：

```python
extract_ticket_fields()
```

而是默认运行：

```python
run_ticket_agent(message)
```

原因是字段提取受前面节点影响。

例如：

```text
会员积分怎么兑换礼品？
```

这句话不是用户明确说要创建工单。

它要先走：

```text
policy_question
-> retrieve_policy
-> no_context
-> decide_ticket_need
-> extract_ticket_fields
```

只有跑完整流程，才能得到：

```text
ticket_need_source: rag_no_context
issue_type: policy_gap
```

如果只测字段函数，就测不到这个链路。

这就是 Agent eval 和普通函数测试的区别。

### 18. 字段 eval 的核心链路

本节完整评测链路是：

```text
读取 agent_cases.json
-> 选出 should_create_ticket 为 true 的样本
-> 运行 run_ticket_agent(message)
-> 取 actual ticket_fields
-> 取 expected_fields / expected_issue_type
-> 逐字段比较
-> 比较 missing_ticket_fields
-> 比较 confirmation_required
-> 比较 ticket_need_source
-> 汇总 case_pass_rate / field_accuracy
-> 输出 bad cases
```

这条链路你要真正理解。

后续评测工具参数、RAG 组合、端到端 Agent 行为时，思路都是类似的。

## 二、本节主题系统讲解

### 1. 本节新增了什么

本节新增：

```text
projects/ai-service/app/agents/field_evaluation.py
projects/ai-service/scripts/agent_ticket_field_eval.py
projects/ai-service/tests/test_agent_field_evaluation.py
notes/stage6-05-agent-ticket-field-evaluation.md
```

本节修改：

```text
projects/ai-service/app/agents/ticket_agent.py
```

`ticket_agent.py` 只做了一个很小但有学习价值的修正：

- `着急`、`催一下` 现在会让 urgency 更容易识别为 `high`。
- 单独出现 `投诉` 不再直接等于 `high`。

这来自 eval 预检发现的字段坏样本。

### 2. 为什么字段 eval 只选 4 条样本

上一节数据集有 12 条样本。

但不是每条都需要评测工单字段。

例如：

```text
普通问候
超出客服范围
订单查询
政策问答已回答
```

这些都不应该创建工单。

字段提取 eval 只选择：

```text
expected.ticket.should_create_ticket == true
```

当前共有 4 条：

```text
agent_no_context_membership_points_001
agent_ticket_logistics_full_001
agent_ticket_complaint_missing_order_001
agent_ticket_refund_full_001
```

这叫评测样本筛选。

不是所有 eval 都要消费所有样本。

不同 evaluator 只消费自己负责的那一部分。

### 3. 四条样本分别覆盖什么

第一条：

```text
agent_no_context_membership_points_001
```

覆盖：

```text
政策问题
知识库无上下文
转为 policy_gap 工单
```

第二条：

```text
agent_ticket_logistics_full_001
```

覆盖：

```text
物流问题
订单号完整
高紧急度
需要确认
```

第三条：

```text
agent_ticket_complaint_missing_order_001
```

覆盖：

```text
投诉问题
缺少订单号
不能进入确认
需要追问缺字段
```

第四条：

```text
agent_ticket_refund_full_001
```

覆盖：

```text
退款问题
订单号完整
普通紧急度
需要确认
```

这 4 条样本虽然不多，但覆盖了字段提取的核心分支。

### 4. 本节为什么既看字段，又看流程状态

字段提取不只是：

```text
issue_type/order_id/urgency 对不对
```

还要看流程状态：

```text
should_create_ticket
ticket_need_source
missing_ticket_fields
confirmation_required
```

原因是这些状态决定后续业务能不能继续。

例如：

```text
字段抽对了，但 missing_ticket_fields 错了
```

系统仍然可能走错。

再比如：

```text
字段抽对了，但 confirmation_required 错了
```

系统可能跳过用户确认。

所以本节叫“工单字段提取评测”，但实际覆盖的是：

```text
字段提取 + 字段完整性 + 工单确认边界
```

### 5. 本节为什么产生两个指标

本节输出两个核心指标：

```text
case_pass_rate
field_accuracy
```

`case_pass_rate` 表示：

```text
多少条工单样本完整通过。
```

`field_accuracy` 表示：

```text
所有被检查字段里，多少字段匹配成功。
```

这两个指标用途不同。

如果 `case_pass_rate` 低，说明完整业务样本不可靠。

如果 `field_accuracy` 低，说明字段提取整体质量差。

如果 `field_accuracy` 高但 `case_pass_rate` 低，说明大多数字段对了，但每条 case 都有少量关键错误。

这在 AI 评测中很常见。

### 6. 本节运行结果

本节手动运行：

```powershell
uv run python scripts/agent_ticket_field_eval.py
```

输出：

```text
Agent ticket field evaluation summary
cases: 4
passed_cases: 4
failed_cases: 0
case_pass_rate: 1.0000
expected_fields: 16
matched_fields: 16
field_accuracy: 1.0000
p0_cases: 4
p0_passed_cases: 4
p0_failed_cases: 0
p0_case_pass_rate: 1.0000
missing_field_cases: 1
missing_field_passed_cases: 1
No bad cases.
```

这表示：

- 4 条需要创建工单的样本全部通过。
- 16 个 expected 字段全部匹配。
- 4 条 P0 工单样本全部通过。
- 1 条缺字段样本正确识别缺少订单号。
- 没有 bad cases。

### 7. eval 预检发现了什么问题

在写正式字段 evaluator 之前，我先用当前代码跑了一次 4 条工单样本。

当时发现两个字段问题。

第一个问题：

```text
订单 A1002 三天没有物流更新了，我很着急，请帮我创建工单催一下
```

expected：

```text
urgency: high
```

actual：

```text
urgency: normal
```

原因是规则里没有覆盖：

```text
着急
催一下
```

第二个问题：

```text
我要投诉商家一直不发货，麻烦人工处理
```

expected：

```text
urgency: normal
```

actual：

```text
urgency: high
```

原因是旧规则把所有：

```text
投诉
```

都当成高紧急度。

这太粗了。

用户投诉确实需要人工关注，但不一定全部是 high。

所以本节修正为：

```text
着急、催一下、一直不动、破损、坏了、加急、立刻、马上
```

这些更像高紧急度信号。

单独的“投诉”不再直接等于 high。

这就是 eval 的实际价值：

```text
它能把字段规则的问题定位到具体样本、具体字段、具体原因。
```

## 三、新增代码讲解

### 1. `field_evaluation.py` 的定位

新增文件：

```text
projects/ai-service/app/agents/field_evaluation.py
```

它是第 5 节的核心。

它不是业务逻辑。

它是评测逻辑。

业务逻辑负责：

```text
从用户消息里抽取字段
```

评测逻辑负责：

```text
判断抽取结果和 expected 是否一致
```

这两个要分开。

### 2. `select_ticket_field_eval_cases()`

这个函数负责筛选样本。

逻辑是：

```python
expected.ticket.should_create_ticket == True
```

只有需要创建工单的样本，才进入字段提取 eval。

这能避免把问候、订单查询、普通政策问答也拿来评测工单字段。

这一步对应一个重要评测思想：

```text
先明确 evaluator 负责什么，再选择对应样本。
```

### 3. `TicketFieldComparison`

这个模型表示单个字段的比较结果。

它包含：

```text
field_name
expected_value
actual_value
passed
failed_reason
```

例如如果 urgency 错了，会产生类似结果：

```text
field_name: urgency
expected_value: high
actual_value: normal
passed: false
failed_reason: field 'urgency' expected='high' actual='normal'
```

这比只告诉你“case 失败”更有用。

因为你能直接知道哪个字段错。

### 4. `TicketFieldEvalCaseResult`

这个模型表示一整条 case 的字段评测结果。

它包含：

```text
case_id
message
expected_should_create_ticket
actual_should_create_ticket
expected_ticket_need_source
actual_ticket_need_source
expected_missing_ticket_fields
actual_missing_ticket_fields
expected_confirmation_required
actual_confirmation_required
expected_fields
actual_fields
field_comparisons
field_accuracy
passed
failed_reasons
```

这让一条 case 的结果很完整。

你既能看整体是否通过，也能看每个字段。

### 5. `TicketFieldEvalSummary`

这个模型表示整体汇总。

它包含：

```text
case_count
passed_case_count
failed_case_count
case_pass_rate
expected_field_count
matched_field_count
field_accuracy
p0_case_count
p0_passed_case_count
p0_failed_case_count
p0_case_pass_rate
missing_field_case_count
missing_field_passed_case_count
```

这比只输出一个准确率更完整。

字段 eval 需要同时看多个角度。

### 6. `evaluate_ticket_field_case()`

这是单条字段 eval 的核心函数。

它做这些事：

```text
读取 expected.ticket
运行 Agent
取 actual_state
整理 expected_fields
取 actual_fields
逐字段比较
比较 missing_ticket_fields
比较 confirmation_required
比较 ticket_need_source
汇总 failed_reasons
返回 TicketFieldEvalCaseResult
```

它默认运行：

```python
run_ticket_agent(message)
```

但也支持传入假的 `agent_runner`。

测试里就用 fake runner 模拟字段错误。

### 7. 为什么 `agent_runner` 可替换

本节 evaluator 默认跑真实本地 Agent。

但测试 bad case 时，我们不希望真的改坏业务代码。

所以函数支持：

```python
agent_runner=lambda _: {...}
```

这样可以人为返回错误字段，验证 evaluator 能不能识别坏样本。

这是一种很实用的测试技巧。

它让评测器本身也能被测试。

### 8. `_expected_fields()`

这个辅助函数负责从 expected ticket 里整理要比较的字段。

它支持两种写法。

第一种：

```json
"expected_fields": {
  "issue_type": "logistics",
  "order_id": "A1002"
}
```

第二种：

```json
"expected_issue_type": "policy_gap"
```

为什么有第二种？

因为 no-context policy gap 这一条样本目前只要求评测：

```text
issue_type: policy_gap
```

不要求精确比较所有字段。

所以 evaluator 会把 `expected_issue_type` 转成：

```text
expected_fields["issue_type"] = "policy_gap"
```

### 9. `_actual_should_create_ticket()`

这个函数判断实际结果是否进入工单流程。

它看：

```text
needs_ticket == True
或者
ticket_fields 存在
```

为什么不只看 `needs_ticket`？

因为不同流程节点可能返回的状态不完全一样。

如果已经有 `ticket_fields`，说明至少进入了字段提取阶段。

这可以让 evaluator 更稳一点。

### 10. `_collect_failed_reasons()`

这个函数负责收集失败原因。

它会检查：

```text
should_create_ticket
ticket_need_source
missing_ticket_fields
confirmation_required
每个 expected field
```

所有失败原因都会进入：

```text
failed_reasons
```

这样一个 case 如果错了两个字段，会同时显示两个原因。

这对排查非常有帮助。

### 11. `format_ticket_field_bad_cases()`

这个函数负责输出坏样本。

如果没有失败：

```text
No bad cases.
```

如果有失败：

```text
Bad cases:
- agent_ticket_logistics_full_001: priority=p0 task_type=ticket_field_extraction field_accuracy=0.6000
  - field 'issue_type' expected='logistics' actual='refund'
  - field 'urgency' expected='high' actual='normal'
```

这种输出是字段 eval 的关键。

你能直接定位：

```text
哪条样本
哪个字段
期望是什么
实际是什么
```

## 四、修改代码讲解

### 1. 为什么修改 `ticket_agent.py`

本节改了紧急度关键词。

原来：

```text
投诉
```

会直接触发：

```text
urgency = high
```

这太粗。

因为不是所有投诉都一定是高紧急度。

更强的高紧急度信号应该是：

```text
着急
催一下
一直不动
破损
坏了
加急
立刻
马上
```

所以本节改成：

```text
单独“投诉”不再自动 high。
“着急/催一下”等更明确的紧急表达会触发 high。
```

### 2. 这段修改有什么学习价值

这不是为了让规则分类器完美。

它的学习价值是：

```text
eval 发现字段错误
我们分析错误原因
修正规则
再次运行 eval
确认通过
```

这就是 AI 工程里的常见闭环。

如果未来换成真实大模型，闭环也类似：

```text
eval 发现 bad case
分析是 prompt 问题、模型问题、schema 问题还是数据问题
修改对应部分
再次 eval
```

### 3. 为什么不是盲目加关键词

如果只是为了让样本过，可以疯狂加关键词。

但那不是好做法。

本节修改遵循一个原则：

```text
关键词要表达稳定业务含义。
```

`着急` 和 `催一下` 明确表达紧急。

单独 `投诉` 只表达问题类型，不一定表达紧急程度。

这个区别很重要。

字段规则不能只看词出现，还要看词代表的业务含义。

## 五、本节运行结果

本节运行：

```powershell
uv run python scripts/agent_ticket_field_eval.py
```

结果：

```text
Agent ticket field evaluation summary
cases: 4
passed_cases: 4
failed_cases: 0
case_pass_rate: 1.0000
expected_fields: 16
matched_fields: 16
field_accuracy: 1.0000
p0_cases: 4
p0_passed_cases: 4
p0_failed_cases: 0
p0_case_pass_rate: 1.0000
missing_field_cases: 1
missing_field_passed_cases: 1
No bad cases.
```

本节也运行：

```powershell
uv run pytest tests/test_agent_field_evaluation.py tests/test_agent_intent_evaluation.py tests/test_ticket_agent_intent.py -q
```

结果：

```text
110 passed
```

## 六、怎么阅读字段 eval 输出

### `cases: 4`

表示这次字段 eval 只评测 4 条工单样本。

不是 12 条。

因为只有 4 条样本期望创建工单。

### `passed_cases: 4`

表示 4 条工单样本全部通过。

### `expected_fields: 16`

表示这 4 条样本里，一共检查了 16 个 expected 字段。

不是每条都检查同样多字段。

no-context policy gap 样本只检查了：

```text
issue_type
```

另外 3 条工单样本各检查 5 个字段。

所以：

```text
1 + 5 + 5 + 5 = 16
```

### `matched_fields: 16`

表示 16 个 expected 字段全部匹配。

### `field_accuracy: 1.0000`

表示字段级准确率是 100%。

### `missing_field_cases: 1`

表示有 1 条样本专门覆盖缺字段场景。

就是：

```text
agent_ticket_complaint_missing_order_001
```

### `missing_field_passed_cases: 1`

表示这条缺字段样本通过。

也就是 Agent 正确识别出缺少：

```text
order_id
```

并且没有进入确认创建。

## 七、常见误区

### 误区 1：字段提取只看 order_id

订单号很重要，但字段提取不只看订单号。

工单还需要：

```text
issue_type
user_request
urgency
need_human_review
missing_ticket_fields
confirmation_required
```

只看订单号会漏掉很多业务错误。

### 误区 2：字段全都应该精确匹配

不是。

稳定枚举字段适合精确匹配。

自然语言描述字段不一定适合精确匹配。

本节没有精确匹配 `description`，就是为了避免 eval 过于脆弱。

### 误区 3：字段级准确率 100% 就一定可以上线

不是。

当前样本只有 4 条。

它说明第一版基础样本通过，不代表所有真实场景都覆盖了。

后面还要继续增加样本、扩大场景、接入真实模型评测。

### 误区 4：缺字段只是用户体验问题

缺字段不只是体验问题。

它还影响业务安全。

如果订单号缺失却创建工单，后端处理会困难。

如果字段完整却继续追问，用户体验会变差。

### 误区 5：所有投诉都应该 high

不一定。

投诉是问题类型，不等于紧急程度。

紧急程度应该看更明确的表达：

```text
着急
加急
马上
立刻
一直不动
破损
```

## 八、本节练习

### 练习 1：解释字段提取和意图识别的区别

请回答：

```text
字段提取和意图识别分别解决什么问题？
```

参考答案：

```text
意图识别解决“用户想做哪一类事”，例如 ticket_request、order_query、policy_question。

字段提取解决“这类事里需要哪些具体参数”，例如 issue_type、order_id、urgency、user_request。

意图识别决定走哪条业务路线，字段提取为这条路线准备结构化参数。
```

### 练习 2：判断字段

用户输入：

```text
订单 A1002 三天没有物流更新了，我很着急，请帮我创建工单催一下
```

应该抽出哪些关键字段？

参考答案：

```text
issue_type: logistics
order_id: A1002
user_request: 创建工单
urgency: high
need_human_review: true
missing_ticket_fields: []
confirmation_required: true
```

### 练习 3：判断缺字段

用户输入：

```text
我要投诉商家一直不发货，麻烦人工处理
```

为什么应该缺少 `order_id`？

参考答案：

```text
因为用户表达了投诉和人工处理诉求，但没有提供具体订单号。
投诉、物流、退款这类工单通常需要订单号才能继续处理。
所以 missing_ticket_fields 应该包含 order_id。
```

### 练习 4：解释 confirmation_required

请回答：

```text
什么时候 confirmation_required 应该是 true？
什么时候应该是 false？
```

参考答案：

```text
当工单字段已经完整，系统准备进入创建工单前，confirmation_required 应该是 true，因为需要用户确认后再创建。

当字段还不完整，例如缺少订单号时，confirmation_required 应该是 false，因为系统应该先追问缺失字段，而不是让用户确认一张不完整的工单。
```

### 练习 5：计算 field_accuracy

一共有 16 个 expected 字段，其中 14 个匹配成功。

field_accuracy 是多少？

参考答案：

```text
field_accuracy = 14 / 16 = 0.875
```

### 练习 6：解释为什么 description 暂时不做精确匹配

参考答案：

```text
description 是自然语言描述，合理表达可能有很多种。
如果强行精确匹配，容易把语义正确但文字不同的结果判成失败。
所以本节先评测稳定字段，例如 issue_type、order_id、urgency、need_human_review。
```

### 练习 7：手动运行字段 eval

请运行：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run python scripts/agent_ticket_field_eval.py
```

你应该重点看哪些输出？

参考答案：

```text
重点看：

cases
passed_cases
failed_cases
case_pass_rate
expected_fields
matched_fields
field_accuracy
p0_case_pass_rate
missing_field_cases
missing_field_passed_cases
bad cases

如果 failed_cases 大于 0，就要继续看 Bad cases 里的具体字段失败原因。
```

## 九、自测题

### 自测 1：什么是 expected fields？

答案：

```text
expected fields 是测试集中提前定义好的期望字段和值。
字段 eval 会拿 actual fields 和 expected fields 对比。
```

### 自测 2：什么是 actual fields？

答案：

```text
actual fields 是 Agent 实际运行后抽取出来的工单字段。
```

### 自测 3：为什么字段 eval 要看 missing_ticket_fields？

答案：

```text
因为缺字段决定流程是否可以继续。
如果缺订单号却认为字段完整，会创建不完整工单。
如果字段完整却误判缺失，会重复追问用户。
```

### 自测 4：case_pass_rate 和 field_accuracy 有什么区别？

答案：

```text
case_pass_rate 看一整条样本是否完整通过。
field_accuracy 看所有 expected 字段中有多少字段匹配成功。

case_pass_rate 更严格，field_accuracy 更细。
```

### 自测 5：为什么 no-context policy gap 样本也进入字段 eval？

答案：

```text
因为知识库无资料时，Agent 会把问题转为工单或人工处理。
这时也需要评测 issue_type 是否是 policy_gap、ticket_need_source 是否是 rag_no_context、是否进入确认。
```

### 自测 6：为什么要评测 ticket_need_source？

答案：

```text
因为同样是创建工单，来源可能不同。
用户明确要求创建工单是 explicit_user_request。
知识库无资料转工单是 rag_no_context。
来源不同会影响后续分类、处理和统计。
```

### 自测 7：本节为什么不直接真实创建工单？

答案：

```text
本节目标是评测字段提取和确认边界，不是测试 Java 后端创建工单。
真实创建工单属于写操作，需要确认、安全边界和后端链路评测，后续再学。
```

### 自测 8：如果 urgency expected 是 high，actual 是 normal，这是什么级别的问题？

答案：

```text
这是字段级失败。
这条字段 comparison 会失败，并导致整条 case 失败。
bad cases 会显示 urgency 的 expected 和 actual。
```

### 自测 9：为什么单独“投诉”不一定代表 high？

答案：

```text
投诉表达的是问题类型，不一定表达紧急程度。
紧急程度应该由更明确的词触发，例如 着急、加急、马上、立刻、一直不动、破损。
```

### 自测 10：本节最重要的工程思想是什么？

答案：

```text
用固定样本把字段期望写清楚，用 evaluator 逐字段比较 actual 和 expected，用 case 级和 field 级指标观察质量，再用 bad cases 反向修正字段提取逻辑。
```

## 十、本节你应该形成的表达能力

你可以这样向别人解释本节成果：

```text
我们在 Agent eval 数据集里筛选出 should_create_ticket 为 true 的样本，专门做工单字段提取评测。
评测器会运行完整 Ticket Agent，拿到实际 ticket_fields、missing_ticket_fields、ticket_need_source 和 confirmation_required。
然后它把这些实际结果和 expected_fields、expected_issue_type、missing_ticket_fields、confirmation_required 做比较。
本节同时输出 case_pass_rate 和 field_accuracy，既能看整条工单样本是否通过，也能看所有字段的整体匹配率。
这让我们能把字段错误定位到具体 case 和具体字段，而不是只靠感觉判断 Agent 是否表现正常。
```

能讲清楚这段，说明你真正理解了工单字段评测的意义。

## 十一、本节小结

本节完成了阶段 6 第二类真实 eval：

```text
工单字段提取评测
```

当前结果：

```text
4 条工单样本全部通过
16 个 expected 字段全部匹配
1 条缺字段样本正确识别
没有 bad cases
```

本节最重要的知识不是某一行代码，而是这套评测思路：

```text
意图识别决定路线
字段提取准备参数
缺字段判断决定是否追问
确认边界决定是否能进入创建动作
字段 eval 用 case 级和 field 级指标共同衡量质量
```

下一节会继续往 Agent 流程走，学习：

```text
Agent 路由评测
```

## 十二、参考资料

- [阶段 6 第 3 节：设计 Agent 测试集](stage6-03-agent-eval-dataset-design.md)
- [阶段 6 第 4 节：意图识别评测](stage6-04-agent-intent-evaluation.md)
- [LangSmith Evaluation Concepts](https://docs.langchain.com/langsmith/evaluation-concepts)
- [LangSmith Example data format](https://docs.langchain.com/langsmith/example-data-format)
- [Pydantic Validators](https://docs.pydantic.dev/latest/concepts/validators/)
- [pytest 官方文档](https://docs.pytest.org/)
