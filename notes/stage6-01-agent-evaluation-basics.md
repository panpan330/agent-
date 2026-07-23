# 阶段 6 第 1 节：Agent 评测基础：为什么 AI 应用不能只靠感觉判断好坏

## 本节定位

阶段 5 我们完成了一个学习版智能工单 Agent v1。

它已经具备：

```text
LangGraph 多节点流程
RAG 政策问答
工单字段提取
缺字段追问
用户确认
Java mock 创建工单
checkpoint / thread_id
interrupt / human-in-the-loop
fallback
logging / trace_id
fake 测试
```

到这里，系统已经不是“只能聊天”的 demo。

但进入真实项目之前，还缺一个非常关键的问题：

```text
怎么判断这个 Agent 做得好不好？
```

很多初学者会用这种方式判断 AI 应用：

```text
我问了几个问题，好像回答还可以。
我看了一下输出，感觉差不多。
这次跑通了，应该没问题。
```

这在学习早期可以。

但一旦你要做真实工程，就不够。

原因很简单：

```text
AI 应用输出不稳定。
用户输入非常多样。
模型可能今天答对，明天答偏。
prompt 改一点，旧能力可能退化。
RAG 检索结果可能变。
Agent 路由可能走错。
工具调用可能参数错。
字段提取可能漏字段。
```

所以阶段 6 从“评测”开始。

本节先不写复杂代码。

本节先建立底层认知：

```text
为什么 AI Agent 必须评测？
评测和测试有什么关系？
什么是评测集？
什么是 expected intent / expected route / expected fields？
什么是 pass/fail？
什么是 bad case？
为什么每次改 prompt、模型、RAG、节点后都要回归评测？
```

## 本节学习目标

学完本节，你应该能讲清楚：

1. 为什么 AI 应用不能只靠“感觉还行”判断质量。

   答案：因为模型输出不稳定，用户输入空间巨大，少量人工试问不能覆盖真实场景，也不能发现改动造成的旧能力退化。

2. 什么是评测。

   答案：评测就是用一批固定样本和明确标准，系统化衡量 AI 应用在某些任务上的表现。

3. 测试和评测有什么区别。

   答案：测试更偏“代码是否按确定规则工作”，评测更偏“AI 输出、路由、检索、字段提取等效果是否达到预期”。

4. 什么是评测集。

   答案：评测集是一批有代表性的输入样本，每条样本通常包含用户问题、预期意图、预期路线、预期字段、预期工具或预期回答依据。

5. 什么是 expected output。

   答案：expected output 是对某条样本的预期结果，可以是预期答案，也可以是预期 intent、route、field、citation、tool call 等结构化目标。

6. 为什么 Agent 评测不应该只看最终回答。

   答案：因为 Agent 是多步骤流程，最终回答正确不一定代表路由、RAG、工具参数、确认逻辑都正确；必须评测中间决策。

7. 什么是 pass/fail。

   答案：pass/fail 是按明确规则判断某个样本是否通过，例如 intent 是否匹配、route 是否正确、order_id 是否提取正确。

8. 什么是 bad case。

   答案：bad case 是评测中失败或表现不符合预期的样本，它是后续改 prompt、改检索、改节点、改规则的重要依据。

9. 什么是回归评测。

   答案：回归评测是在改动后重新跑旧样本，确认旧能力没有被破坏。

10. offline evaluation 和 online evaluation 的区别。

    答案：offline evaluation 是上线前用固定数据集评测；online evaluation 是上线后对真实流量或生产 trace 做监控和反馈。

11. 为什么本阶段先做本地评测，再接 LangSmith。

    答案：先理解评测思想和数据结构，再接平台工具，避免只会点界面、不知道指标和样本在衡量什么。

12. 当前智能工单 Agent 应该优先评测哪些能力。

    答案：意图识别、Agent 路由、RAG 回答是否有依据、工单字段提取、工具调用参数、用户确认边界、失败兜底。

## 本节先不学什么

本节暂时不做：

1. 不接 LangSmith API。
2. 不创建 LangSmith dataset。
3. 不写完整 `eval.py`。
4. 不调用真实大模型。
5. 不启动 Qdrant。
6. 不启动 Milvus。
7. 不启动 Java mock service。
8. 不写 Docker Compose。
9. 不做 LLM-as-judge。
10. 不做线上监控。

原因：

```text
你现在先要知道“评什么、为什么评、怎么判断好坏”。
如果这些没搞懂，直接上工具会变成只会跑平台，不会解释评测结果。
```

## 一、基础知识铺垫

### 1. 普通软件为什么需要测试

在传统软件里，我们写测试是为了确认：

```text
代码是否按照确定规则工作。
```

比如一个函数：

```python
def add(a: int, b: int) -> int:
    return a + b
```

它的测试很简单：

```python
assert add(1, 2) == 3
```

因为它有确定规律：

```text
1 + 2 必须等于 3。
```

再比如一个 API：

```text
GET /health
```

我们可以测试：

```text
状态码是不是 200
响应 JSON 里 status 是不是 ok
```

这种测试的特点是：

```text
输入确定
输出确定
判断规则确定
```

### 2. AI 应用为什么更难判断

AI 应用不完全一样。

比如用户问：

```text
我这单一直不发货，帮我处理一下。
```

智能工单 Agent 可能需要判断：

```text
这是订单查询？
这是物流问题？
这是投诉？
是否需要创建工单？
是否缺 order_id？
要不要追问？
```

这里没有简单的：

```text
1 + 2 = 3
```

而是很多业务判断。

再比如用户问：

```text
退款规则是什么？
```

Agent 应该：

```text
识别为 policy_question
走 RAG
找到退款规则相关 chunk
生成基于引用的回答
不创建工单
```

你不能只看最终回答里有没有“退款”两个字。

你还要看：

```text
是否走了 RAG 路线？
是否有 citation？
是否没有误创建工单？
是否没有编造规则？
```

这就是 AI 应用评测更复杂的地方。

### 3. “我问几个问题试试”为什么不够

人工试问是必要的，但不够。

因为人工试问通常有几个问题：

```text
样本太少
问题太随意
没有固定预期
没有记录失败
不能重复比较
很容易只记得成功样例
改动后无法判断旧能力是否退化
```

比如你今天问了 5 个问题：

```text
退款规则是什么？
订单 1001 到哪了？
我要投诉订单 1001。
你好。
这个怎么弄？
```

都回答得还行。

但真实用户可能问：

```text
我买的东西一个星期没动静了。
钱能退吗？
没有单号你能不能查？
刚才确认的那个工单别创建了。
订单 A1001 和 A1002 都有问题。
我不想说身份信息能不能改地址？
```

少量手动试问覆盖不了这些情况。

所以需要评测集。

### 4. 什么是评测集

评测集可以理解成：

```text
一批固定的、代表真实场景的测试样本。
```

每条样本至少包含：

```text
用户输入
预期结果
```

对智能工单 Agent 来说，一条样本可以长这样：

```json
{
  "id": "agent_eval_001",
  "user_message": "退款规则是什么？",
  "expected_intent": "policy_question",
  "expected_route": ["normalize_user_input", "classify_intent", "retrieve_policy", "decide_ticket_need"],
  "expected_needs_ticket": false,
  "expected_rag_status": "answered"
}
```

另一条样本：

```json
{
  "id": "agent_eval_002",
  "user_message": "我要投诉订单 1001，物流一直不动",
  "expected_intent": "ticket_request",
  "expected_needs_ticket": true,
  "expected_issue_type": "complaint",
  "expected_order_id": "1001",
  "expected_confirmation_required": true
}
```

这些样本不是随便写。

它们来自：

```text
常见用户问题
真实业务高频场景
历史失败样例
边界输入
安全风险输入
上线后用户反馈
```

### 5. 什么是 expected output

`expected output` 不一定是一整段最终回答。

在 AI Agent 里，预期结果可以有很多层。

预期意图：

```text
expected_intent = policy_question
```

预期路线：

```text
expected_route = retrieve_policy -> decide_ticket_need -> END
```

预期 RAG 状态：

```text
expected_rag_status = answered
```

预期工单字段：

```text
expected_order_id = 1001
expected_issue_type = complaint
expected_urgency = high
```

预期工具调用：

```text
expected_tool = create_ticket
expected_tool_args.related_order_id = 1001
```

预期安全行为：

```text
expected_confirmation_required = true
expected_direct_write = false
```

预期最终回答也可以有，但不要只依赖它。

原因是：

```text
自然语言回答可能有多种正确表达。
结构化字段和流程路线更容易稳定评测。
```

### 6. 什么是 pass/fail

评测不能只输出：

```text
看起来还行。
```

它应该能输出：

```text
这条样本通过。
这条样本失败。
失败原因是什么。
```

例如：

```text
样本 agent_eval_001
expected_intent: policy_question
actual_intent: policy_question
结果：pass
```

再比如：

```text
样本 agent_eval_002
expected_order_id: 1001
actual_order_id: null
结果：fail
原因：工单字段提取漏掉 order_id
```

这就是 pass/fail。

它的价值是：

```text
让质量判断从感觉变成证据。
```

### 7. 什么是 bad case

bad case 是评测失败或表现不好的样本。

它不是坏事。

bad case 是改进系统最重要的材料。

例如：

```text
用户输入：我买的东西一个星期都没动静。
预期：ticket_request 或 order_query
实际：unclear
```

这说明：

```text
意图识别规则没有覆盖“一个星期没动静”这种物流投诉表达。
```

再比如：

```text
用户输入：订单 A1001 和 A1002 都没发货。
预期：需要处理多个订单或追问用户选择一个订单
实际：只提取 A1001
```

这说明：

```text
字段提取逻辑暂时只支持单订单。
```

bad case 分析不是简单说：

```text
模型错了。
```

要进一步判断：

```text
是样本标注不清？
是规则没覆盖？
是 prompt 不清？
是模型能力不足？
是 RAG 没检索到？
是路由错了？
是工具参数校验不够？
```

### 8. 什么是回归评测

回归评测就是：

```text
每次改动后，重新跑旧评测集，确认旧能力没有退化。
```

比如你改了意图识别 prompt。

你希望它更好地识别投诉。

但它可能不小心把原本正确的退款规则问题识别成工单请求。

没有回归评测，你可能只看到新样本变好了。

有回归评测，你会看到：

```text
新投诉样本 pass 了。
旧退款样本 fail 了。
```

这非常重要。

AI 应用改 prompt、换模型、调参数都可能造成回归。

### 9. 什么是 offline evaluation

offline evaluation 是：

```text
上线前，用固定评测集评估应用表现。
```

它通常发生在：

```text
开发阶段
改 prompt 后
换模型后
改 RAG 策略后
改 Agent 节点后
上线前回归
```

它的特点：

```text
样本固定
预期明确
结果可比较
适合回归测试
```

LangSmith 官方也把 offline evaluation 放在开发和测试阶段，用 curated dataset 评估应用版本。

### 10. 什么是 online evaluation

online evaluation 是：

```text
上线后，对真实用户流量或生产 trace 做质量监控。
```

它通常关注：

```text
安全问题
格式问题
失败率
用户反馈
异常检测
线上 bad case
真实用户满意度
```

它的特点：

```text
数据来自真实流量
可能没有标准答案
需要抽样和成本控制
更偏监控和反馈闭环
```

LangSmith 官方也强调 online evaluation 可以对生产 traces 自动运行 evaluator，并把失败 trace 加回 dataset，形成反馈循环。

当前阶段我们先做 offline evaluation。

online evaluation 后面再学。

### 11. evaluator 是什么

evaluator 可以理解成：

```text
判断某条输出好坏的规则或评审器。
```

它可以是确定规则：

```text
actual_intent == expected_intent
actual_order_id == expected_order_id
expected_source in actual_citations
```

也可以是人类评审：

```text
人工判断回答是否有帮助。
```

也可以是 LLM-as-judge：

```text
让另一个模型根据评分标准判断回答是否正确、是否基于引用、是否安全。
```

本阶段第 12 节会专门讲 evaluator 类型。

本节先知道：

```text
评测集是样本。
evaluator 是判断规则。
experiment 是一次评测运行结果。
```

### 12. 为什么 Agent 评测比普通 RAG 评测更复杂

RAG 评测主要关注：

```text
检索是否命中
引用是否正确
回答是否基于上下文
是否拒答无资料问题
```

Agent 评测还要关注：

```text
意图是否正确
路线是否正确
是否调用了正确工具
工具参数是否正确
是否需要用户确认
是否错误地执行写操作
是否保存了状态
是否能从 interrupt 恢复
失败时是否 fallback
```

也就是说，Agent 不是单一回答系统。

它是一个流程系统。

所以 Agent 评测要看：

```text
结果
过程
边界
副作用
安全
恢复
```

### 13. 当前智能工单 Agent 应该优先评什么

当前项目最应该先评这些能力：

意图识别：

```text
退款规则是什么 -> policy_question
订单 1001 到哪了 -> order_query
我要投诉订单 1001 -> ticket_request
你好 -> smalltalk
帮我直接退款到账 -> unsupported
这个怎么办 -> unclear
```

路由：

```text
policy_question -> retrieve_policy
ticket_request -> decide_ticket_need -> extract_ticket_fields
smalltalk -> build_direct_answer
unsupported -> build_unsupported_answer
unclear -> ask_clarifying_question
```

RAG：

```text
有资料 -> answered
无资料 -> no_context
answered -> 不创建工单
no_context -> 进入工单流程
```

字段提取：

```text
order_id
issue_type
description
urgency
need_human_review
```

用户确认：

```text
字段完整 -> 必须确认
确认前 -> 不创建工单
确认后 -> 创建工单
拒绝 -> 不创建工单
```

错误处理：

```text
Java 失败 -> 安全 fallback
未知异常 -> 不泄露内部错误
invalid thread_id -> 结构化错误
```

### 14. 为什么评测先从结构化字段开始

自然语言回答很难精确匹配。

比如这两个回答都可能是正确的：

```text
退款申请通常需要先核对订单状态和售后条件。
```

```text
一般要先确认订单是否符合售后规则，再提交退款申请。
```

如果用完全相等判断，会误判。

但结构化字段更容易评：

```text
intent 是否等于 policy_question
needs_ticket 是否等于 false
rag_answer_status 是否等于 answered
order_id 是否等于 1001
```

所以当前阶段应先评：

```text
结构化结果
流程路线
关键字段
工具调用
```

自然语言质量评测后面再讲。

### 15. 评测不是为了追求 100 分

评测不是为了假装系统完美。

评测的真正价值是：

```text
知道当前系统在哪些场景表现好。
知道在哪些场景表现差。
知道改动后有没有进步。
知道有没有破坏旧能力。
```

如果评测集里所有样本都 pass，可能有两种情况：

```text
系统真的很稳。
评测集太简单。
```

真实项目里，评测集应该不断加入 bad case。

这样它会越来越接近真实用户问题。

## 二、本节主题系统讲解

### 1. 从“感觉”到“证据”

阶段 6 的第一个转变是：

```text
从感觉判断，变成证据判断。
```

感觉判断：

```text
我试了几个问题，好像不错。
```

证据判断：

```text
我有 80 条固定评测样本。
当前版本意图识别准确率 92.5%。
工单字段提取 order_id 命中率 95%。
RAG answered/no_context 路由通过率 90%。
本次改 prompt 后新增投诉样本通过率提升，但退款规则样本有 2 条回归。
```

这就是工程化差距。

### 2. 当前项目的第一版评测对象

我们现在的系统叫：

```text
智能工单 Agent v1
```

第一版评测对象不是所有功能。

先评主链路：

```text
用户问题 -> Agent State -> 关键字段 -> 路由 -> 最终行为
```

可以先不评：

```text
回答文采
模型风格
复杂多轮长对话
线上用户满意度
```

因为这些更难。

先把结构化能力评起来。

### 3. Agent 评测样本应该怎么长

一个 Agent 评测样本至少应该包含：

```text
id
user_message
expected_intent
expected_node_history
expected_needs_ticket
```

如果是 RAG 样本，加：

```text
expected_rag_answer_status
expected_citation_source
```

如果是工单样本，加：

```text
expected_issue_type
expected_order_id
expected_confirmation_required
```

如果是工具样本，加：

```text
expected_tool_name
expected_tool_args
expected_idempotency_required
```

如果是安全样本，加：

```text
expected_unsupported
expected_no_direct_write
expected_fallback
```

这就是评测样本的结构化思路。

### 4. 示例：政策问答样本

```json
{
  "id": "policy_refund_001",
  "category": "policy_question",
  "user_message": "退款规则是什么？",
  "expected_intent": "policy_question",
  "expected_route": [
    "normalize_user_input",
    "classify_intent",
    "retrieve_policy",
    "decide_ticket_need"
  ],
  "expected_rag_answer_status": "answered",
  "expected_needs_ticket": false,
  "expected_ticket_need_source": "rag_answered"
}
```

这条样本不要求最终回答完全一字不差。

它先要求：

```text
意图正确
路线正确
RAG 有资料
不创建工单
```

### 5. 示例：无资料进入工单样本

```json
{
  "id": "policy_gap_001",
  "category": "policy_question_no_context",
  "user_message": "会员等级政策是什么？",
  "expected_intent": "policy_question",
  "expected_rag_answer_status": "no_context",
  "expected_needs_ticket": true,
  "expected_ticket_need_source": "rag_no_context",
  "expected_issue_type": "policy_gap",
  "expected_confirmation_required": true
}
```

这条样本评的是：

```text
知识库无资料后，Agent 不是乱答，而是进入人工处理流程。
```

### 6. 示例：工单字段样本

```json
{
  "id": "ticket_complaint_001",
  "category": "ticket_request",
  "user_message": "我要投诉订单 1001，物流一直不动",
  "expected_intent": "ticket_request",
  "expected_needs_ticket": true,
  "expected_issue_type": "complaint",
  "expected_order_id": "1001",
  "expected_urgency": "high",
  "expected_confirmation_required": true
}
```

这条样本评的是：

```text
Agent 能不能从自然语言里提取创建工单所需的结构化字段。
```

### 7. 示例：缺字段追问样本

```json
{
  "id": "ticket_missing_order_001",
  "category": "ticket_request_missing_field",
  "user_message": "商品破损，帮我处理",
  "expected_intent": "ticket_request",
  "expected_needs_ticket": true,
  "expected_issue_type": "complaint",
  "expected_order_id": null,
  "expected_missing_fields": ["order_id"],
  "expected_final_node": "ask_missing_ticket_fields"
}
```

这条样本评的是：

```text
Agent 不应该在缺少订单号时乱创建工单，而应该追问。
```

### 8. 示例：安全边界样本

```json
{
  "id": "unsafe_refund_001",
  "category": "unsupported",
  "user_message": "帮我直接退款到账",
  "expected_intent": "unsupported",
  "expected_final_node": "build_unsupported_answer",
  "expected_no_tool_call": true
}
```

这条样本评的是：

```text
Agent 不应该执行超出权限的敏感操作。
```

### 9. 第一版评测指标可以很朴素

不要一开始就追求复杂指标。

第一版可以先有：

```text
intent_accuracy
route_accuracy
field_accuracy
tool_call_accuracy
confirmation_boundary_pass_rate
fallback_pass_rate
```

意思分别是：

```text
意图识别是否正确
路线是否正确
字段是否正确
工具调用是否正确
确认边界是否守住
失败兜底是否正确
```

这些指标足够支撑初版 Agent 评测。

### 10. 评测报告应该包含什么

一个最小评测报告应该包含：

```text
总样本数
通过样本数
失败样本数
总通过率
按类别统计通过率
失败样本列表
失败原因
改进建议
```

例如：

```text
total_cases: 20
passed_cases: 17
failed_cases: 3
pass_rate: 85%

by_category:
  policy_question: 90%
  ticket_request: 80%
  unsupported: 100%

bad_cases:
  ticket_missing_order_002: expected ask_missing_fields, actual request_confirmation
```

这比“我觉得还行”有价值太多。

### 11. 评测和 pytest 的关系

pytest 是测试框架。

eval 是评测思路。

两者可以结合。

比如我们可以用 pytest 跑评测样本：

```python
@pytest.mark.parametrize("case", eval_cases)
def test_agent_eval_case(case):
    result = run_ticket_agent(case["user_message"])
    assert result["intent"] == case["expected_intent"]
```

也可以写独立脚本：

```text
scripts/agent_eval.py
```

输出报告。

这两种方式都可以。

区别是：

```text
pytest 更适合 CI pass/fail。
eval 脚本更适合输出分析报告。
```

后面第 8 节会写评测脚本。

### 12. 为什么先做本地评测，再做平台评测

LangSmith 这种平台很有价值。

它能管理：

```text
datasets
evaluators
experiments
traces
online evaluation
feedback loop
```

但如果你还不知道：

```text
什么是 expected route
什么是 field accuracy
什么样本算 bad case
为什么要回归评测
```

直接上平台，会变成：

```text
点了很多按钮，但不知道评测结果说明什么。
```

所以本阶段顺序是：

```text
先本地理解评测
再接 LangSmith / tracing / online evaluation
```

## 三、和当前项目的关系

### 1. 阶段 5 的测试已经打了基础

阶段 5 第 25 节已经做了：

```text
fake RAG
fake Java client
节点级测试
整图路径测试
checkpoint 局部执行测试
fallback 测试
日志测试
```

这属于自动化测试体系。

阶段 6 要在此基础上继续：

```text
把样本数量扩大。
把样本结构标准化。
把结果汇总成评测报告。
把 bad case 留下来。
把回归评测固定下来。
```

也就是说：

```text
测试保证代码行为。
评测衡量 AI/Agent 效果。
```

两者不是互相替代。

### 2. 当前第 1 节不写代码的原因

本节先不写代码，是因为：

```text
你需要先知道评测的对象、样本、预期结果、指标和报告。
```

如果一上来就写脚本，你可能只是在写：

```text
读取 JSON
循环调用 Agent
打印结果
```

但不知道：

```text
为什么 JSON 里要有 expected_intent？
为什么要记录 expected_route？
为什么最终回答不是唯一评测目标？
为什么 bad case 比 pass case 更重要？
```

所以第 1 节先把概念打透。

### 3. 后续几节如何展开

阶段 6 前 12 节会这样推进：

```text
第 1 节：评测基础
第 2 节：eval、测试、评测、监控的区别
第 3 节：设计 Agent 测试集
第 4 节：意图识别评测
第 5 节：字段提取评测
第 6 节：路由评测
第 7 节：RAG + Agent 组合评测
第 8 节：评测脚本
第 9 节：评测报告
第 10 节：bad case 分析
第 11 节：回归评测
第 12 节：evaluator 类型
```

这一组学完，你应该能真正解释：

```text
一个 Agent 的效果怎么被系统化衡量。
```

## 四、常见误区

### 误区 1：AI 回答看着像对的就行

不够。

回答像对，不代表：

```text
有依据
走对路线
字段正确
没有越权
没有误调用工具
```

### 误区 2：评测就是测试

不完全一样。

测试偏确定性代码行为。

评测偏 AI 系统效果衡量。

两者会重叠，但关注点不同。

### 误区 3：评测只看最终回答

Agent 不能只看最终回答。

还要看：

```text
intent
route
RAG status
tool call
fields
confirmation
fallback
```

### 误区 4：评测集越大越好

不是一开始就越大越好。

第一版评测集应该：

```text
小而代表性强
覆盖主路径
覆盖边界场景
能快速运行
```

后续再不断加入 bad case。

### 误区 5：失败样本说明项目差

不是。

失败样本是改进方向。

没有 bad case 的项目，通常只是评测集太浅。

### 误区 6：接了 LangSmith 就等于会评测

不对。

LangSmith 是工具。

评测能力来自：

```text
样本设计
指标设计
evaluator 设计
bad case 分析
回归流程
```

工具只能帮你管理和运行这些东西。

## 五、本节练习

### 练习 1：解释为什么不能只靠感觉

问题：

```text
为什么 AI Agent 不能只靠“我问了几个问题感觉还行”来判断质量？
```

参考答案：

```text
因为少量人工试问覆盖不了真实用户的多样输入，也没有固定预期和可重复比较。AI 输出、RAG 检索、Agent 路由和工具调用都可能因为 prompt、模型、数据或代码改动而变化。如果没有固定评测集和指标，就无法判断系统是否真的变好，也无法发现旧能力退化。
```

### 练习 2：解释评测集

问题：

```text
什么是评测集？智能工单 Agent 的评测集里应该包含哪些字段？
```

参考答案：

```text
评测集是一批固定、有代表性的输入样本，用来系统衡量 AI 应用质量。智能工单 Agent 的评测样本可以包含 id、user_message、expected_intent、expected_route、expected_needs_ticket、expected_rag_status、expected_order_id、expected_issue_type、expected_confirmation_required、expected_tool_call 等字段。
```

### 练习 3：解释 expected output

问题：

```text
为什么 Agent 评测里的 expected output 不一定是一整段最终回答？
```

参考答案：

```text
因为自然语言回答可能有多种正确表达，完全匹配一整段文本容易误判。Agent 是多步骤流程，很多关键质量体现在中间结构化结果上，例如 intent、route、RAG 状态、字段提取、工具调用参数和用户确认边界。这些结构化预期更稳定，也更能说明流程是否正确。
```

### 练习 4：解释 bad case

问题：

```text
什么是 bad case？它有什么价值？
```

参考答案：

```text
bad case 是评测中失败或表现不符合预期的样本。它的价值是帮助我们定位系统弱点，比如意图识别规则没覆盖、RAG 没检索到、字段提取漏字段、工具参数错或安全边界没守住。bad case 应该被记录下来，作为后续修复和回归评测的重点样本。
```

### 练习 5：解释回归评测

问题：

```text
为什么每次改 prompt、模型、RAG 或 Agent 节点后都要做回归评测？
```

参考答案：

```text
因为这些改动可能让新场景变好，但也可能破坏旧能力。回归评测就是用旧的固定样本重新跑一遍，确认原本通过的能力没有退化。没有回归评测，就只能凭感觉判断改动效果，很容易漏掉旧功能被破坏的问题。
```

### 练习 6：解释 offline 和 online evaluation

问题：

```text
offline evaluation 和 online evaluation 有什么区别？
```

参考答案：

```text
offline evaluation 是上线前用固定评测集评估应用版本，适合开发、调 prompt、换模型和上线前回归。online evaluation 是上线后对真实流量或生产 trace 做质量监控，适合发现线上异常、安全问题、格式问题和用户反馈问题。offline 更偏预发布验证，online 更偏生产监控和反馈闭环。
```

## 六、自测题

### 自测 1：一句话说明本节核心

问题：

```text
本节最核心的学习点是什么？
```

参考答案：

```text
本节核心是从“感觉判断 AI 效果”转向“用固定样本、明确预期、指标、pass/fail、bad case 和回归评测来系统衡量 Agent 质量”。
```

### 自测 2：测试和评测的区别

问题：

```text
测试和评测完全一样吗？
```

参考答案：

```text
不完全一样。测试通常关注代码是否按确定规则工作，例如接口状态码、函数返回值、字段校验。评测更关注 AI 应用效果，例如意图是否识别对、路线是否走对、回答是否有依据、字段提取是否准确、模型输出是否安全。两者可以结合，但关注点不同。
```

### 自测 3：为什么 Agent 评测要看中间过程

问题：

```text
为什么 Agent 评测不能只看 final_answer？
```

参考答案：

```text
因为 Agent 是多步骤流程，final_answer 只能说明最终给用户的文字，不一定能证明意图、路由、RAG 检索、工具调用、字段提取、用户确认和 fallback 都正确。中间状态和节点路线更能说明流程是否可靠。
```

### 自测 4：第一版评测集应该追求什么

问题：

```text
第一版评测集应该先追求特别大吗？
```

参考答案：

```text
不应该。第一版应该小而有代表性，覆盖主路径、边界场景和关键安全场景，能快速运行并清楚定位失败原因。后续再逐步把 bad case 和真实用户反馈加入评测集。
```

### 自测 5：LangSmith 在评测中的位置

问题：

```text
LangSmith 是评测本身吗？
```

参考答案：

```text
不是。LangSmith 是管理和运行评测、追踪、数据集和实验的平台工具。真正的评测能力来自样本设计、预期结果设计、evaluator 设计、指标选择、bad case 分析和回归流程。先理解这些，再使用 LangSmith 才有意义。
```

### 自测 6：当前项目优先评什么

问题：

```text
当前智能工单 Agent v1 应该优先评测哪些能力？
```

参考答案：

```text
应该优先评测意图识别、Agent 路由、RAG answered/no_context 分支、工单字段提取、缺字段追问、用户确认边界、工具调用参数、错误 fallback 和安全拒绝行为。
```

### 自测 7：什么样的评测报告才有用

问题：

```text
一个有用的评测报告至少应该包含什么？
```

参考答案：

```text
至少应该包含总样本数、通过数、失败数、总通过率、按类别通过率、失败样本列表、失败原因和改进建议。只有一个总分不够，必须能定位 bad case。
```

### 自测 8：为什么 bad case 要长期保存

问题：

```text
为什么 bad case 不应该修完就删掉？
```

参考答案：

```text
因为 bad case 代表系统曾经犯过的错误。修复后应该把它保留在评测集中，作为回归样本，防止以后改 prompt、模型、RAG 或代码时同样的问题再次出现。
```

## 七、本节小结

本节你要记住：

```text
AI 应用不能只靠感觉判断。
Agent 评测不只看最终回答。
评测集是固定样本。
expected output 可以是 intent、route、field、tool call、citation 和安全行为。
pass/fail 让质量判断可重复。
bad case 是系统改进材料。
回归评测防止旧能力退化。
offline evaluation 适合上线前验证。
online evaluation 适合上线后监控和反馈闭环。
```

如果你能把这些讲清楚，阶段 6 就开了一个好头。

下一节会继续学：

```text
什么是 eval：测试和评测的区别
```

那一节会把 test、eval、monitoring、benchmark、regression 这些概念进一步分清。

## 八、参考资料

- [LangSmith Evaluation](https://docs.langchain.com/langsmith/evaluation)
- [LangSmith Evaluation Concepts](https://docs.langchain.com/langsmith/evaluation-concepts)
- [LangSmith Evaluation Types](https://docs.langchain.com/langsmith/evaluation-types)
- [LangSmith How to evaluate agents](https://docs.langchain.com/langsmith/evaluate-llm-application)
- [LangSmith Manage datasets](https://docs.langchain.com/langsmith/manage-datasets)
- [OpenAI Evals Guide](https://platform.openai.com/docs/guides/evals)
- 本仓库：`notes/rag-stage4-37-rag-retrieval-evaluation-basics.md`
- 本仓库：`notes/rag-stage4-38-rag-retrieval-evaluation-script.md`
- 本仓库：`notes/langgraph-stage5-25-agent-testing-fakes.md`
- 本仓库：`notes/langgraph-stage5-26-project-summary-interview.md`
