# 阶段 6 第 12 节：evaluator 类型

## 本节定位

前面第 1-11 节我们已经做了这些事情：

```text
第 1-2 节：知道 AI 应用为什么需要 eval，以及 test 和 eval 有什么区别
第 3 节：设计 Agent 测试集
第 4 节：评测意图识别
第 5 节：评测工单字段提取
第 6 节：评测 Agent 路由
第 7 节：评测 RAG + Agent 组合行为
第 8 节：把多个评测脚本组织成统一入口
第 9 节：生成评测报告
第 10 节：做坏例分析
第 11 节：把核心样本沉淀成回归评测
```

到这里，你已经不是只会写几个测试函数了。

你已经有了一个本地可运行的 Agent eval 雏形。

但是还有一个很重要的问题：

```text
我们现在写的这些评测，到底属于哪一种 evaluator？

以后真实接入 LLM 后，还应该继续用代码规则评测吗？

什么场景该用人评？

什么场景该用 LLM-as-judge？

什么场景该用 pairwise 对比？
```

这就是本节要解决的问题。

本节不急着加新功能。

本节要把 evaluator 的类型讲清楚，并把这些类型映射回当前项目。

本节的核心目标是：

```text
你以后看到一个 AI 应用输出，能判断应该用什么 evaluator 去评它。
```

---

## 本节学习目标

学完本节，你应该能解释清楚：

1. 什么是 evaluator。
2. evaluator 和 eval dataset 的区别。
3. evaluator 和 eval runner 的区别。
4. evaluator 和 eval report 的区别。
5. 规则 evaluator 是什么。
6. 代码 evaluator 是什么。
7. human evaluator 是什么。
8. LLM-as-judge 是什么。
9. pairwise evaluator 是什么。
10. composite evaluator 是什么。
11. summary evaluator 是什么。
12. 什么是 reference-based evaluation。
13. 什么是 reference-free evaluation。
14. 什么是 deterministic evaluator。
15. 什么是 non-deterministic evaluator。
16. 当前项目的意图识别评测属于哪类 evaluator。
17. 当前项目的字段提取评测属于哪类 evaluator。
18. 当前项目的路由评测属于哪类 evaluator。
19. 当前项目的 RAG + Agent 组合评测属于哪类 evaluator。
20. 为什么当前阶段优先使用代码/规则 evaluator。
21. 为什么不应该一上来就用 LLM-as-judge 评所有东西。
22. 以后真实模型节点接入后，哪些地方仍然适合用代码 evaluator。
23. 哪些地方未来更适合补 LLM-as-judge。
24. 怎么给一个新需求选择合适的 evaluator。

---

## 本节先不学什么

本节暂时不做这些：

```text
1. 不接入 LangSmith evaluator UI
2. 不真实调用 LLM-as-judge
3. 不把 OpenAI grader API 接进项目
4. 不做多人标注系统
5. 不做 pairwise A/B 实验平台
6. 不做线上实时 evaluator
7. 不新增业务代码
8. 不修改 java-mock-service
9. 不打开 Docker / Qdrant / Milvus
```

原因很简单：

```text
先知道 evaluator 有哪些类型、分别解决什么问题，
再去接工具或平台，才不容易乱用。
```

如果还没分清楚：

```text
规则评测
代码评测
人类评审
LLM 裁判
两两对比
```

就直接上平台，很容易变成：

```text
能跑，但不知道自己到底在评什么。
```

本节先补的是“判断力”。

---

## 一、基础知识铺垫

### 1. evaluator 是什么

evaluator 可以先理解成：

```text
判断一次 AI 应用输出好不好、对不对、能不能接受的评判器。
```

它输入一些信息，输出一个评判结果。

最常见的输入是：

```text
用户输入
实际输出
期望输出
中间过程
业务规则
参考资料
```

最常见的输出是：

```text
passed: true / false
score: 0.0 - 1.0
reason: 为什么通过或失败
metric: accuracy、recall、precision、pass_rate 等
bad case evidence: 失败证据
```

举一个非常基础的例子：

```text
用户输入：
我要查 ORD-1001 的订单

期望结果：
intent = order_query

实际结果：
intent = ticket_request

evaluator 判断：
不通过
原因：expected intent=order_query, actual intent=ticket_request
```

这里 evaluator 的工作不是生成回答。

它的工作是评价回答。

换句话说：

```text
业务代码负责做事。
evaluator 负责判断做得怎么样。
```

---

### 2. evaluator 不是 eval dataset

eval dataset 是评测数据集。

它回答的问题是：

```text
拿哪些样本来评？
```

比如当前项目的：

```text
projects/ai-service/data/agent_eval/agent_cases.json
```

里面有很多固定样本：

```text
用户说什么
期望 intent 是什么
期望 route 是什么
期望是否创建工单
期望 RAG 是否命中
期望引用哪些 source
样本优先级是什么
样本标签是什么
```

evaluator 回答的是：

```text
怎么判断一个样本通过还是失败？
```

两者关系是：

```text
eval dataset = 试卷
evaluator = 判卷规则
eval runner = 发卷、收卷、调用判卷规则的人
eval report = 成绩单
bad case analysis = 错题分析
```

这几个概念必须分开。

如果混在一起，项目会越来越乱。

---

### 3. evaluator 不是 eval runner

eval runner 是运行评测的东西。

它负责：

```text
1. 读取评测数据集
2. 选择要跑哪些 suite
3. 调用业务系统或 Agent
4. 调用 evaluator 判断结果
5. 汇总多个 evaluator 的结果
6. 决定 exit code
```

当前项目里的：

```text
projects/ai-service/app/agents/eval_suite.py
```

更接近 eval runner / suite orchestrator。

它里面有：

```text
AgentEvalSuite
build_agent_eval_suite_registry()
run_agent_eval_suites()
run_agent_eval_suites_for_cases()
filter_agent_eval_cases()
```

这些东西本身不直接定义“某个业务输出怎么才算对”。

它们主要负责组织：

```text
intent evaluator
field evaluator
route evaluator
rag evaluator
```

所以要记住：

```text
evaluator 负责判分。
runner 负责把评测跑起来。
```

---

### 4. evaluator 不是 eval report

eval report 是评测报告。

它负责把结果展示出来。

当前项目里的：

```text
projects/ai-service/app/agents/eval_report.py
```

主要负责：

```text
1. 把 AgentEvalRunReport 转成 Markdown
2. 展示 Overall
3. 展示 Suite Summary
4. 展示各 suite 的 Summary
5. 展示各 suite 的 Bad Cases
6. 写入 UTF-8 Markdown 文件
```

它不负责判断：

```text
intent 到底对不对
字段到底对不对
路由到底对不对
RAG 引用到底对不对
```

这些判断已经在 evaluator 里做完。

所以：

```text
evaluator = 评分规则
report = 把评分结果展示给人看
```

---

### 5. evaluator 不是 bad case analysis

bad case analysis 是坏例分析。

它发生在 evaluator 之后。

当前项目里的：

```text
projects/ai-service/app/agents/bad_case_analysis.py
```

做的事情是：

```text
1. 从评测报告里找失败样本
2. 按证据文本判断失败大类
3. 给出 likely layer
4. 给出 diagnosis
5. 给出 recommended action
6. 给出 regression action
```

它回答的问题是：

```text
失败了以后，应该怎么分析、怎么修、怎么进入回归保护？
```

evaluator 回答的问题是：

```text
这个样本到底有没有失败？
```

所以它们不是同一个东西。

---

### 6. 什么是 score

score 是分数。

最常见的形式是：

```text
0 / 1
0.0 - 1.0
0 - 100
```

例如：

```text
intent accuracy = 1.0
field accuracy = 0.875
source recall = 0.6667
route pass rate = 0.9167
```

score 的重点不是数字好看。

重点是：

```text
这个数字能不能稳定地反映你关心的质量。
```

如果一个 score 不能指导你判断质量，就只是噪音。

举例：

```text
一个客服回答很礼貌，但引用错了退款政策。
```

如果只打“语气友好度”，可能分很高。

但对企业客服系统来说，这个回答可能是严重失败。

所以 evaluator 的 score 必须贴合业务目标。

---

### 7. 什么是 pass / fail

pass / fail 是最简单的评判结果：

```text
通过 / 失败
```

它适合很明确的业务要求：

```text
intent 必须等于 policy_question
必须包含 required node
不能访问 forbidden node
RAG 有答案时必须带 citation
用户未确认前不能创建工单
```

pass / fail 的优点：

```text
清晰
稳定
适合 CI
容易定位问题
适合回归保护
```

pass / fail 的缺点：

```text
表达不了“部分正确”
表达不了“质量有点差但还没完全错”
对开放式文本评价不够细
```

所以在工程里经常会同时使用：

```text
passed: true / false
score: 0.0 - 1.0
failed_reason: 失败原因
```

当前项目里很多 evaluator 都是这种组合。

---

### 8. 什么是 reference output

reference output 可以理解为：

```text
参考答案。
```

在 eval 数据集里，它通常放在：

```text
expected
ground_truth
label
reference_answer
```

当前项目用的是：

```text
expected
```

比如：

```text
expected.intent
expected.intent_route
expected.ticket.expected_fields
expected.rag.expected_sources
```

有 reference output 的评测，通常更容易做得稳定。

因为 evaluator 可以明确比较：

```text
actual 是否等于 expected
actual 是否包含 expected
actual 是否满足 expected 的业务规则
```

---

### 9. 什么是 reference-based evaluation

reference-based evaluation 是：

```text
基于参考答案的评测。
```

它需要数据集中提前写好正确答案。

例如：

```text
输入：我想查一下 ORD-1001 的物流
期望：intent = order_query
实际：intent = order_query
结果：通过
```

这种方式适合：

```text
分类任务
字段提取任务
结构化输出任务
工具调用参数任务
路由路径任务
RAG 召回 source 任务
业务规则判断任务
```

当前项目的大部分 evaluator 都是 reference-based。

因为我们在 `agent_cases.json` 里提前写了 expected。

---

### 10. 什么是 reference-free evaluation

reference-free evaluation 是：

```text
没有固定参考答案，也要评价输出质量。
```

比如线上真实用户问：

```text
我这个订单退款到底怎么处理？
```

系统回答了一段自然语言。

你不一定提前准备了这条问题的标准答案。

但你仍然想判断：

```text
回答是否有帮助
是否礼貌
是否安全
是否拒绝了不该回答的问题
是否胡编了不存在的政策
是否泄露敏感信息
```

这时就可能需要：

```text
LLM-as-judge
human review
规则安全扫描
线上监控指标
```

reference-free evaluation 更接近生产监控。

它更灵活，但也更难稳定。

---

### 11. 什么是 deterministic evaluator

deterministic evaluator 是：

```text
同样输入，每次评测结果都一样。
```

例如：

```text
actual_intent == expected_intent
required_nodes 是否都出现
forbidden_nodes 是否没出现
expected_sources 是否都被引用
JSON 是否能解析
字段是否满足 Pydantic schema
```

确定性 evaluator 的优点：

```text
稳定
便宜
快
适合自动化测试
适合 CI
适合回归评测
失败原因容易解释
```

它的缺点：

```text
对语义相似、表达质量、语气、完整性这些开放问题不够灵活。
```

当前项目第 4-11 节主要使用 deterministic evaluator。

这是有意为之。

因为我们当前要先把结构化行为保护住。

---

### 12. 什么是 non-deterministic evaluator

non-deterministic evaluator 是：

```text
同样输入，评测结果可能不是 100% 一样。
```

典型例子就是：

```text
LLM-as-judge
```

原因是：

```text
LLM 本身可能受模型版本、采样参数、上下文、服务端实现影响。
```

即使你把温度设低，也不能把它当成普通 if 判断。

它的优点是：

```text
能评开放式自然语言
能评语义是否等价
能评回答是否完整
能评是否有帮助
能评语气是否合适
```

它的缺点是：

```text
成本更高
速度更慢
结果可能波动
需要设计 judge prompt
需要校验 judge 本身是否可靠
高风险场景仍然需要人类审核
```

所以不要把 LLM-as-judge 当成万能答案。

---

### 13. 什么是 objective evaluation

objective evaluation 是偏客观的评测。

比如：

```text
intent 是否相等
订单号是否提取正确
是否走了 create_ticket 节点
是否带了 citation
source 是否命中
JSON schema 是否合法
```

这类问题一般适合：

```text
代码 evaluator
规则 evaluator
Pydantic 校验
字符串匹配
集合包含判断
数值指标
```

客观评测的核心是：

```text
正确答案相对明确。
```

当前项目已经覆盖了大量客观评测。

---

### 14. 什么是 subjective evaluation

subjective evaluation 是偏主观的评测。

比如：

```text
回答是否有帮助
解释是否清楚
语气是否合适
总结是否简洁
是否真正解决用户问题
两个回答哪个更好
```

这类问题不容易用简单 if 判断。

可能需要：

```text
人工评审
LLM-as-judge
pairwise evaluator
用户反馈
线上满意度数据
```

主观评测不代表不重要。

恰恰相反，很多 AI 产品最后拼的就是主观体验。

但在工程学习顺序上，我们先把客观行为评稳，再补主观质量评测。

---

### 15. 什么是规则 evaluator

规则 evaluator 是：

```text
用明确规则判断输出。
```

例如：

```text
如果 intent 等于 expected.intent，则通过
如果 node_history 包含 create_ticket 但用户未确认，则失败
如果 actual_sources 少于 expected_sources，则失败
如果输出包含手机号，则失败
如果 JSON 解析失败，则失败
```

规则 evaluator 不一定要复杂。

它的价值在于：

```text
把你明确知道的质量要求固定下来。
```

一个非常重要的原则是：

```text
凡是能用明确规则评的，优先用规则。
```

不要为了“显得 AI 化”就让大模型去评简单等值判断。

例如：

```text
actual_intent == expected_intent
```

这种事没有必要交给 LLM。

---

### 16. 什么是代码 evaluator

代码 evaluator 是规则 evaluator 的一种常见实现形式。

它用代码写评判逻辑。

比如 Python 函数：

```text
evaluate_intent_case()
evaluate_ticket_field_case()
evaluate_agent_route_case()
evaluate_rag_agent_case()
```

代码 evaluator 可以做：

```text
等值判断
集合判断
字段比较
路径比较
schema 校验
正则检查
敏感词扫描
数值指标计算
复杂业务规则判断
```

它的最大价值是：

```text
可测试、可复用、可进入 CI。
```

当前项目的核心 evaluator 全部是代码 evaluator。

---

### 17. 什么是 human evaluator

human evaluator 是人类评审。

它适合：

```text
高风险输出
主观体验判断
样本标签创建
LLM-as-judge 校准
复杂业务争议
新产品早期探索
线上坏例复盘
```

例如客服 AI 回答：

```text
“你的退款不符合规则。”
```

这句话可能需要业务人员判断：

```text
政策理解是否正确
表达是否容易激怒用户
是否应该给出下一步操作建议
是否符合公司客服规范
```

人评的优点：

```text
可靠性高
能理解复杂语境
能处理业务灰区
能发现 evaluator 规则没覆盖的问题
```

人评的缺点：

```text
慢
贵
难以大规模自动化
不同人标准可能不一致
需要标注规范
```

真实团队通常会用人评做两件事：

```text
1. 建立高质量 golden dataset
2. 校准自动 evaluator 是否靠谱
```

---

### 18. 什么是 LLM-as-judge

LLM-as-judge 是：

```text
用一个大模型去评价另一个模型或 AI 应用的输出。
```

它也叫：

```text
model grader
LLM evaluator
AI judge
```

基本流程是：

```text
用户输入
实际输出
参考答案或评价标准
-> 交给 judge model
-> judge model 输出分数和理由
```

例如：

```text
请判断这个客服回答是否准确引用了退款政策。
分数范围 0-1。
如果回答没有依据，给 0。
如果回答部分正确，给 0.5。
如果回答完整且有依据，给 1。
```

LLM-as-judge 适合：

```text
自然语言回答质量
语义等价判断
总结质量
解释是否清楚
回答是否完整
语气是否合适
RAG 回答是否基于上下文
```

不适合：

```text
简单等值判断
安全红线判断的唯一依据
高风险业务审批
成本敏感的大规模回归入口
没有校准过的生产阻断规则
```

本节必须记住一句话：

```text
LLM-as-judge 很有用，但不是替代所有 evaluator 的万能锤子。
```

---

### 19. 什么是 pairwise evaluator

pairwise evaluator 是两两对比 evaluator。

它不一定直接给一个输出打绝对分。

它更关心：

```text
A 和 B 哪个更好？
```

例如：

```text
prompt v1 的回答
prompt v2 的回答

问题：
哪个回答更准确、更清楚、更适合客服场景？
```

pairwise 很适合：

```text
比较两个 prompt 版本
比较两个模型
比较两个 RAG 策略
比较两个 rerank 策略
比较两个答案生成策略
```

为什么有时 pairwise 比绝对打分容易？

因为人或模型可能很难判断：

```text
这个回答到底是 0.7 还是 0.8？
```

但更容易判断：

```text
A 明显比 B 更准确。
```

未来你做 prompt 版本管理时，pairwise 会很有用。

---

### 20. 什么是 composite evaluator

composite evaluator 是组合 evaluator。

它把多个维度合成一个总分或总判断。

例如客服回答质量可以拆成：

```text
事实正确性：50%
引用来源：20%
语气合适：15%
回答完整性：15%
```

最后得到：

```text
overall_quality_score
```

当前项目的 RAG + Agent 组合评测已经有一点 composite evaluator 的味道。

因为它同时看：

```text
rag_status_passed
sources_passed
citation_passed
ticket_decision_passed
no_context_behavior_passed
```

然后汇总成：

```text
passed = not failed_reasons
```

虽然我们还没有做加权分数，但思想已经出现了：

```text
一个样本是否通过，取决于多个维度是否都满足。
```

---

### 21. 什么是 summary evaluator

summary evaluator 是汇总型 evaluator。

它关心的不是单个样本，而是整个评测运行的总体指标。

例如：

```text
accuracy
p0_accuracy
field_accuracy
route_pass_rate
source_recall
case_pass_rate
```

单个样本 evaluator 会回答：

```text
case-001 是否通过？
```

summary evaluator 或 summary metric 会回答：

```text
这一批样本整体通过率是多少？
P0 样本有没有失败？
source recall 是多少？
```

当前项目里：

```text
IntentEvalSummary
TicketFieldEvalSummary
AgentRouteEvalSummary
RagAgentEvalSummary
AgentEvalRunReport
```

都在做 summary 层的工作。

严格说，它们不全是 evaluator 本身。

更准确地说：

```text
它们是 evaluator 结果的聚合与报告模型。
```

---

### 22. 为什么 evaluator 类型很重要

你学 evaluator 类型，不是为了背名词。

而是为了做工程判断。

如果选错 evaluator，会出现很多问题。

比如：

```text
用 LLM-as-judge 判断 intent 是否等值
```

这会导致：

```text
成本变高
速度变慢
结果可能波动
还不如 if actual == expected 稳定
```

再比如：

```text
只用字符串等值判断评自然语言回答
```

这会导致：

```text
明明语义正确，但因为措辞不同被判失败
明明措辞相似，但事实错误却被判通过
```

所以 evaluator 的第一原则是：

```text
评什么，就选能稳定衡量这个目标的 evaluator。
```

---

## 二、本节主题系统讲解

### 1. 当前项目到底有哪些 evaluator

当前项目中，真正承担 evaluator 角色的主要是：

```text
projects/ai-service/app/agents/intent_evaluation.py
projects/ai-service/app/agents/field_evaluation.py
projects/ai-service/app/agents/route_evaluation.py
projects/ai-service/app/agents/rag_agent_evaluation.py
```

它们分别评：

```text
intent_evaluation.py
-> 用户意图识别是否正确

field_evaluation.py
-> 工单字段提取是否正确

route_evaluation.py
-> Agent 节点路径是否正确

rag_agent_evaluation.py
-> RAG 回答状态、引用来源和后续工单决策是否正确
```

这四个 evaluator 有一个共同点：

```text
都不是让大模型来判分。
```

它们都用 Python 代码做判断。

所以它们属于：

```text
code evaluator
rule-based evaluator
deterministic evaluator
mostly reference-based evaluator
```

---

### 2. intent_evaluation.py 属于什么 evaluator

`intent_evaluation.py` 评的是：

```text
用户输入应该被分到哪种 intent。
```

它关心：

```text
expected_intent
actual_intent
expected_route
actual_route
classifier_reason
passed
failed_reason
accuracy
p0_accuracy
```

它的核心判断是：

```text
actual_intent == expected_intent
and actual_route == expected_route
```

所以它是：

```text
代码 evaluator
规则 evaluator
确定性 evaluator
reference-based evaluator
分类任务 evaluator
```

为什么适合用代码 evaluator？

因为意图识别输出是结构化分类结果。

它不是一段开放式自然语言。

只要 expected intent 写得清楚，判断就很直接。

例如：

```text
expected_intent = order_query
actual_intent = order_query
-> pass

expected_intent = order_query
actual_intent = ticket_request
-> fail
```

这不需要 LLM-as-judge。

如果让 LLM 来判断：

```text
“order_query 和 ticket_request 是否一样？”
```

反而把简单问题复杂化了。

---

### 3. field_evaluation.py 属于什么 evaluator

`field_evaluation.py` 评的是：

```text
工单字段有没有提取对。
```

它关心：

```text
should_create_ticket 是否一致
ticket_need_source 是否一致
missing_ticket_fields 是否一致
confirmation_required 是否一致
expected_fields 和 actual_fields 是否一致
field_accuracy
case_pass_rate
missing_field_case_count
```

它的判断不是只看一个字段。

它会逐个比较：

```text
order_id
issue_type
description
urgency
```

或者更多未来字段。

所以它属于：

```text
代码 evaluator
规则 evaluator
确定性 evaluator
reference-based evaluator
结构化字段 evaluator
部分 composite evaluator
```

为什么说它有一点 composite 味道？

因为一个工单样本是否通过，可能同时取决于：

```text
是否应该创建工单
缺失字段是否正确
确认状态是否正确
每个字段值是否正确
```

任何一个关键维度错了，都可能导致 case fail。

---

### 4. route_evaluation.py 属于什么 evaluator

`route_evaluation.py` 评的是：

```text
Agent 是否走了正确的节点路径。
```

它关心：

```text
expected_node_path
actual_node_path
required_nodes
missing_required_nodes
forbidden_nodes
visited_forbidden_nodes
expected_terminal_node
actual_terminal_node
path_exact_match
route_pass_rate
exact_match_rate
```

这个 evaluator 很有 Agent 特色。

普通聊天机器人可能只看最终回答。

但 Agent 不只要回答对，还要过程可控。

比如：

```text
用户只是问退款规则
-> 不应该进入 create_ticket

用户明确投诉并提供完整信息
-> 应该进入 request_ticket_confirmation

用户未确认前
-> 不能进入 create_ticket
```

所以 route evaluator 属于：

```text
代码 evaluator
规则 evaluator
确定性 evaluator
reference-based evaluator
Agent process evaluator
路径 evaluator
```

它特别适合 LangGraph 项目。

因为 LangGraph 把流程拆成了 node 和 edge。

只要 state 里有 `node_history`，我们就能评：

```text
走过哪些节点
有没有少走关键节点
有没有误走危险节点
终点是否正确
```

这是 Agent 工程化里非常重要的一类 evaluator。

---

### 5. rag_agent_evaluation.py 属于什么 evaluator

`rag_agent_evaluation.py` 评的是：

```text
RAG 和 Agent 组合起来后，行为是否符合业务预期。
```

它不是单纯评 RAG 检索。

也不是单纯评 Agent 路由。

它关注组合结果：

```text
RAG 是否应该有上下文
actual_rag_answer_status 是否正确
expected_sources 是否被引用
must_cite 时是否真的有 citation
RAG 有答案时是否不创建工单
RAG 无上下文时是否进入 policy_gap 工单
工单类型是否正确
确认状态是否正确
```

所以它属于：

```text
代码 evaluator
规则 evaluator
确定性 evaluator
reference-based evaluator
RAG behavior evaluator
Agent decision evaluator
组合 evaluator
```

为什么它重要？

因为真实 AI 应用的错误经常不是单点错误。

可能是：

```text
RAG 没检到
-> Agent 误以为没有政策
-> 进入工单流程
-> 创建了不该创建的工单
```

也可能是：

```text
RAG 检到了
-> 引用 source 不对
-> 回答看起来有依据，但依据是错的
```

这类问题必须用组合 evaluator 看。

只评单个节点是不够的。

---

### 6. eval_suite.py 为什么不是 evaluator 本身

`eval_suite.py` 有很多和 evaluation 相关的名字。

但要分清楚：

```text
AgentEvalSuite
build_agent_eval_suite_registry()
run_agent_eval_suites()
filter_agent_eval_cases()
format_agent_eval_run_report()
```

这些主要是组织层。

它们做的是：

```text
把多个 evaluator 注册到一起
按命令行参数选择 suite
读取或接收 cases
筛选 regression/P0 样本
运行每个 suite
汇总每个 suite 的结果
输出统一格式
```

它更像：

```text
eval runner
suite registry
orchestrator
```

不是单个 evaluator。

当然，它里面的 `AgentEvalSuite.evaluate` 会指向 evaluator 函数。

但 `eval_suite.py` 自己的主要职责是：

```text
组织评测，而不是定义业务判分细节。
```

---

### 7. eval_report.py 为什么不是 evaluator

`eval_report.py` 的职责是：

```text
把评测结果写成 Markdown 报告。
```

它关心：

```text
表格怎么展示
Overall 放什么
Suite Summary 放什么
Bad Cases 怎么展示
报告文件怎么写入
```

它不关心：

```text
intent 为什么算错
字段为什么算错
路径为什么算错
RAG source 为什么算错
```

所以它是：

```text
report generator
```

不是 evaluator。

这个边界很重要。

否则后续你很容易把“判断逻辑”和“展示逻辑”写在一起。

一旦写在一起，就会变成：

```text
报告格式一改，评测逻辑也容易被改坏。
评测逻辑一改，报告格式也跟着受影响。
```

当前项目把 evaluator 和 report 分开，是正确方向。

---

### 8. bad_case_analysis.py 为什么不是 evaluator

`bad_case_analysis.py` 读取的是已经失败的证据。

它做的是失败后的分类和建议。

例如：

```text
rag_retrieval_or_citation
agent_decision_after_rag
agent_route
ticket_field_extraction
intent_classification
```

它更像：

```text
错题分析助手
```

而不是：

```text
判卷器
```

它依赖 evaluator 先告诉它：

```text
哪些 case 是 bad case。
```

然后它再判断：

```text
这个 bad case 可能属于哪个问题层。
```

所以执行顺序是：

```text
业务系统运行
-> evaluator 判定 pass/fail
-> report 记录结果
-> bad_case_analysis 分析失败原因
-> regression action 进入回归保护
```

---

### 9. 为什么当前阶段优先代码/规则 evaluator

当前阶段的核心目标不是先追求“评价一切自然语言质量”。

当前阶段的核心目标是：

```text
把智能工单 Agent 的关键业务行为评稳。
```

智能工单 Agent 有很多明确边界：

```text
意图不能乱分
字段不能乱提
未确认不能创建工单
政策问题命中知识库时不该乱建工单
无上下文时要走 policy_gap
必须带引用来源时不能缺 citation
```

这些都适合代码/规则 evaluator。

优先代码 evaluator 的原因是：

```text
1. 成本低，不用每次评测都花模型调用费
2. 速度快，适合本地频繁跑
3. 稳定，同样输入同样输出
4. 可解释，失败原因能直接定位字段或路径
5. 适合 pytest 和 CI
6. 适合回归评测
7. 能保护业务红线
```

这不是“LLM-as-judge 不重要”。

而是学习顺序上应该先做：

```text
明确规则能评的，先用代码评稳。
```

再做：

```text
开放式文本质量，再用 LLM-as-judge 或人评补充。
```

---

### 10. 为什么不要一上来就用 LLM-as-judge

很多人做 AI eval 时会犯一个错误：

```text
只要是 AI 输出，就全部丢给另一个 AI 评。
```

这个做法看起来先进，但有几个问题。

第一，浪费。

比如：

```text
actual_intent == expected_intent
```

代码一行能判断。

没必要让大模型读一堆上下文后再说：

```text
“它们是一样的。”
```

第二，不稳定。

LLM-as-judge 可能受模型版本、prompt、采样参数影响。

如果它今天判通过、明天判失败，你很难把它放进严格 CI。

第三，解释成本高。

代码 evaluator 失败时可以给出：

```text
expected intent=order_query; got intent=ticket_request
```

LLM judge 失败时可能给出一段自然语言理由。

这段理由也可能需要再判断是否可靠。

第四，安全边界不能只靠 judge model。

例如：

```text
用户未确认前不能创建工单。
```

这是业务红线。

应该用确定性代码规则拦住。

不能只问模型：

```text
“你觉得这个操作安全吗？”
```

---

### 11. 什么时候应该用 LLM-as-judge

LLM-as-judge 最适合评：

```text
开放式自然语言质量
语义是否等价
回答是否完整
回答是否有帮助
回答是否符合语气要求
总结是否忠实
RAG 生成回答是否真正基于上下文
复杂解释是否遗漏关键点
```

比如未来真实模型回答：

```text
根据退款政策，7 天内未使用且包装完整的商品可以申请退款。你可以先在订单页提交申请。
```

我们可以用代码检查：

```text
是否有 citation
是否引用了 expected_sources
是否没有泄露敏感信息
```

但代码很难判断：

```text
回答是否解释清楚
是否漏掉了“特殊活动订单以活动规则为准”
语气是否适合客服
是否真正回答了用户的问题
```

这些地方可以考虑 LLM-as-judge。

但要注意：

```text
LLM-as-judge 不是单独存在的。
它应该和代码规则、人评、坏例分析一起组成评测体系。
```

---

### 12. 什么时候应该用 human evaluator

human evaluator 适合三类场景。

第一类：建立参考答案。

```text
评测集里的 expected 不是从天上掉下来的。
它需要人根据业务规则写出来。
```

第二类：评主观质量。

```text
客服回答是否专业
解释是否清楚
语气是否合适
用户是否容易理解
```

第三类：高风险问题。

```text
退款争议
投诉升级
隐私数据
财务金额
法律相关表达
```

这类场景不能完全依赖自动 evaluator。

人评的目标不是替代自动评测。

人评的目标是：

```text
给自动评测提供校准标准。
```

---

### 13. 什么时候应该用 pairwise evaluator

pairwise evaluator 适合做版本对比。

例如：

```text
prompt v1 vs prompt v2
qwen3.7-plus vs 另一个模型
top_k=3 vs top_k=5
rerank on vs rerank off
RAG answer prompt A vs prompt B
```

它回答：

```text
哪个版本更好？
```

而不是：

```text
某个版本到底是 83 分还是 87 分？
```

pairwise 很适合阶段 6 后面的：

```text
prompt 版本管理
真实 LLM 节点评测
模型版本对比
RAG 参数调优对比
```

但当前第 12 节还不需要实现。

先知道它的适用场景。

---

### 14. 当前项目未来 evaluator 分层

未来接入真实 LLM 后，建议 evaluator 分层是：

```text
第一层：确定性安全与结构检查
第二层：业务结果检查
第三层：过程路径检查
第四层：自然语言质量检查
第五层：人工抽检和高风险审核
```

对应 evaluator：

```text
第一层
-> Pydantic schema 校验、敏感信息扫描、工具权限规则

第二层
-> intent、field、tool args、RAG source、ticket decision 代码 evaluator

第三层
-> route evaluator、node_history evaluator、interrupt/checkpoint evaluator

第四层
-> LLM-as-judge、pairwise evaluator、helpfulness/groundedness evaluator

第五层
-> human evaluator、业务专家复核、客服质检
```

这是一套更接近真实工程团队的评测体系。

不是只靠一种 evaluator。

---

### 15. evaluator 选择流程

以后你遇到一个新评测需求，可以按这个流程判断。

第一问：

```text
有没有明确参考答案？
```

有：

```text
优先 reference-based evaluation。
```

没有：

```text
考虑 reference-free evaluation、人评、LLM-as-judge 或线上监控。
```

第二问：

```text
输出是不是结构化的？
```

是：

```text
优先代码 evaluator、Pydantic、规则判断。
```

不是：

```text
再考虑文本相似度、LLM-as-judge、人评。
```

第三问：

```text
判断标准是不是客观明确？
```

是：

```text
用 deterministic evaluator。
```

不是：

```text
考虑 LLM-as-judge / human evaluator。
```

第四问：

```text
是不是要比较两个版本？
```

是：

```text
考虑 pairwise evaluator。
```

第五问：

```text
是不是高风险业务？
```

是：

```text
自动 evaluator 只能做第一层筛选，最终要有人类审核或明确业务规则兜底。
```

---

## 三、本节代码对照讲解

本节没有新增业务代码。

这不是偷懒。

这是因为本节主题是：

```text
理解 evaluator 类型，并把当前项目已有代码归类。
```

如果为了“有代码改动”硬加一个新 evaluator，很容易让学习重点偏掉。

当前项目已经有足够多的 evaluator 例子：

```text
intent_evaluation.py
field_evaluation.py
route_evaluation.py
rag_agent_evaluation.py
```

本节应该把它们讲透，而不是堆新文件。

---

### 1. `evaluate_intent_case()` 的学习价值

`evaluate_intent_case()` 是最典型的分类 evaluator。

它的学习价值是：

```text
一个 AI 分类结果可以像普通业务结果一样被评测。
```

它不是看自然语言回答漂不漂亮。

它看的是：

```text
分类标签是否正确
分类后路由是否正确
```

你要记住它代表的 evaluator 类型：

```text
classification evaluator
reference-based evaluator
deterministic code evaluator
```

---

### 2. `evaluate_ticket_field_case()` 的学习价值

`evaluate_ticket_field_case()` 展示的是字段级 evaluator。

它不只判断整个 case 是否通过。

它还会拆到每个字段：

```text
field_name
expected_value
actual_value
passed
failed_reason
```

这很重要。

因为字段提取任务里，只有一句：

```text
这个 case 失败了。
```

是不够的。

你还要知道：

```text
是订单号错了？
是问题类型错了？
是紧急程度错了？
是缺失字段判断错了？
```

它代表的 evaluator 类型：

```text
structured extraction evaluator
field-level evaluator
reference-based evaluator
deterministic code evaluator
```

---

### 3. `evaluate_agent_route_case()` 的学习价值

`evaluate_agent_route_case()` 展示的是 Agent 过程 evaluator。

它评的不是最终一句话。

它评的是：

```text
Agent 流程有没有走对。
```

对 LangGraph 项目来说，这非常关键。

因为 Agent 的危险不只是“回答错”。

还可能是：

```text
跳过确认
误调用工具
误创建工单
应该追问却没有追问
应该结束却继续执行
```

它代表的 evaluator 类型：

```text
process evaluator
route evaluator
path evaluator
deterministic code evaluator
```

---

### 4. `evaluate_rag_agent_case()` 的学习价值

`evaluate_rag_agent_case()` 展示的是组合行为 evaluator。

它把 RAG 和 Agent 放在一起看。

它的学习价值是：

```text
真实 AI 系统的质量，经常来自多个模块组合后的行为。
```

例如：

```text
RAG 没检到
-> Agent 要知道这是 no_context
-> 后续可以走 policy_gap 工单
```

或者：

```text
RAG 检到了
-> 回答必须带 source
-> 不应该直接进入工单创建
```

它代表的 evaluator 类型：

```text
RAG behavior evaluator
Agent decision evaluator
composite evaluator
reference-based deterministic code evaluator
```

---

### 5. `AgentEvalSuite` 的学习价值

`AgentEvalSuite` 本身不是单个 evaluator。

它像一个登记表：

```text
suite name
suite title
evaluate function
format summary function
format bad cases function
```

它的学习价值是：

```text
当 evaluator 变多后，必须有统一组织方式。
```

如果没有 suite registry，后续会变成：

```text
一个脚本跑 intent
一个脚本跑 field
一个脚本跑 route
一个脚本跑 rag
每个脚本参数不同
每个脚本输出不同
每个脚本 exit code 不同
```

这会让评测无法工程化。

所以：

```text
evaluator 负责判断。
suite 负责组织。
```

---

## 四、本节没有新增代码的原因

这节不新增代码，原因有三个。

第一，当前项目已经有足够多 evaluator 类型样本。

如果再新增一个演示 evaluator，只会重复前面第 4-7 节。

第二，本节真正欠缺的是概念体系。

你现在需要知道：

```text
同样叫 evaluator，背后可能是代码规则、人评、LLM 裁判、pairwise 对比或组合指标。
```

第三，下一节会进入真实 LLM 意图识别节点。

到那时会开始出现新的问题：

```text
真实模型输出不稳定怎么办？
结构化输出错了怎么办？
同一个 evaluator 是否还能继续用？
fake 和 real 怎么同时存在？
```

所以第 12 节先把 evaluator 类型补齐，下一节再接真实模型节点，学习顺序更稳。

---

## 五、本节产出

本节产出是：

```text
notes/stage6-12-evaluator-types.md
README.md 阶段 6 第 12 节索引更新
docs/learning-progress.md 学习进度更新
docs/learning-resources.md 资料索引更新
```

本节没有新增：

```text
Python 业务代码
测试代码
评测数据
报告样例
Docker 配置
```

因为这节是：

```text
概念系统化 + 当前项目 evaluator 映射
```

---

## 六、常见误区

### 误区 1：evaluator 就是测试

不准确。

测试更偏代码契约。

evaluator 更偏 AI 行为质量。

有些 evaluator 可以用 pytest 跑，但 evaluator 不等于 pytest。

---

### 误区 2：evaluator 就是报告

不对。

evaluator 负责判断。

报告负责展示。

不要把评判逻辑写进报告生成器。

---

### 误区 3：所有 AI 输出都应该用 LLM-as-judge

不对。

结构化输出、分类结果、路由路径、权限边界，优先用代码规则。

LLM-as-judge 更适合开放式文本质量。

---

### 误区 4：代码 evaluator 太简单，所以不高级

不对。

工程里很多最重要的保护就是简单规则。

例如：

```text
用户未确认前不能创建工单。
```

这条规则越简单，越应该用确定性代码保护。

---

### 误区 5：有了 pass/fail 就不需要分数

不一定。

pass/fail 适合红线。

分数适合观察趋势。

例如：

```text
P0 必须 100% pass
整体 field_accuracy 从 0.92 降到 0.83，要警惕
source_recall 连续下降，要分析 RAG 检索质量
```

---

### 误区 6：人评太慢，所以没用

不对。

人评不适合每次 CI 都跑。

但人评适合：

```text
创建高质量 expected
审核高风险样本
校准 LLM-as-judge
发现自动 evaluator 盲区
```

---

### 误区 7：pairwise 只是 A/B 测试

不完全。

pairwise 可以用于 A/B，但它更本质的问题是：

```text
两个输出哪个更好？
```

它可以用于：

```text
prompt 对比
模型对比
RAG 策略对比
回答生成策略对比
```

---

## 七、本节练习

### 练习 1：区分 dataset、evaluator、runner、report

请判断下面内容分别属于哪一类：

```text
1. agent_cases.json
2. evaluate_intent_case()
3. run_agent_eval_suites()
4. build_agent_eval_markdown_report()
5. analyze_agent_eval_bad_cases()
```

答案：

```text
1. agent_cases.json
   -> eval dataset
   -> 因为它保存评测样本和 expected。

2. evaluate_intent_case()
   -> evaluator
   -> 因为它判断单个意图识别样本是否通过。

3. run_agent_eval_suites()
   -> eval runner / suite orchestrator
   -> 因为它组织多个 suite 运行。

4. build_agent_eval_markdown_report()
   -> report generator
   -> 因为它把评测结果变成 Markdown 报告。

5. analyze_agent_eval_bad_cases()
   -> bad case analyzer
   -> 因为它分析失败样本的原因和后续动作。
```

---

### 练习 2：判断 evaluator 类型

下面这些评测需求应该优先用哪类 evaluator？

```text
1. 判断 actual_intent 是否等于 expected_intent
2. 判断回答是否礼貌、清楚、适合客服语气
3. 判断用户未确认前是否调用了 create_ticket
4. 比较 prompt v1 和 prompt v2 哪个回答更好
5. 审核一个高金额退款争议回答是否合规
```

答案：

```text
1. 代码/规则 evaluator。
   因为这是明确等值判断。

2. LLM-as-judge 或 human evaluator。
   因为这是开放式自然语言质量和主观体验判断。

3. 代码/规则 evaluator。
   因为这是明确业务安全边界。

4. pairwise evaluator。
   因为问题是比较两个版本哪个更好。

5. human evaluator 为主，代码规则和 LLM-as-judge 可辅助。
   因为这是高风险业务场景，不能完全交给自动评测。
```

---

### 练习 3：给当前项目 evaluator 归类

请给下面文件归类：

```text
1. intent_evaluation.py
2. field_evaluation.py
3. route_evaluation.py
4. rag_agent_evaluation.py
```

答案：

```text
1. intent_evaluation.py
   -> classification evaluator
   -> code evaluator
   -> rule-based evaluator
   -> deterministic evaluator
   -> reference-based evaluator

2. field_evaluation.py
   -> structured extraction evaluator
   -> field-level evaluator
   -> code evaluator
   -> deterministic evaluator
   -> reference-based evaluator

3. route_evaluation.py
   -> process/path evaluator
   -> Agent route evaluator
   -> code evaluator
   -> deterministic evaluator
   -> reference-based evaluator

4. rag_agent_evaluation.py
   -> RAG behavior evaluator
   -> Agent decision evaluator
   -> composite evaluator
   -> code evaluator
   -> deterministic evaluator
   -> reference-based evaluator
```

---

### 练习 4：判断是否该用 LLM-as-judge

下面哪些场景适合 LLM-as-judge？

```text
A. 判断 JSON 是否能解析
B. 判断回答是否完整解释了退款规则
C. 判断 actual_route 是否等于 expected_route
D. 判断两个总结哪个更清晰
E. 判断回答是否严格引用了给定上下文
```

答案：

```text
B、D、E 更适合 LLM-as-judge。

A 不适合，代码解析 JSON 更稳定。
C 不适合，字符串等值判断更稳定。

E 可以用 LLM-as-judge，但最好搭配代码 evaluator。
代码 evaluator 先检查有没有 citation、source 是否来自检索结果；
LLM-as-judge 再判断回答内容是否真的被上下文支持。
```

---

### 练习 5：设计一个 evaluator 选择方案

假设下一节接入真实 LLM 意图识别节点后，模型输出：

```text
{
  "intent": "ticket_request",
  "reason": "用户明确希望客服处理订单投诉"
}
```

你会怎么评测这个输出？

答案：

```text
第一层：Pydantic 校验。
检查输出是否是合法 JSON，intent 是否在允许枚举里，reason 是否是字符串。

第二层：代码 evaluator。
用 expected.intent 对比 actual.intent。
用 expected.intent_route 对比 actual_route。
计算 accuracy 和 p0_accuracy。

第三层：坏例分析。
如果 intent 错了，记录 message、expected、actual、reason。

第四层：必要时补 LLM-as-judge。
如果 reason 的质量也要评，例如解释是否合理、是否符合业务逻辑，可以用 LLM-as-judge 或人评辅助。

但 intent 本身是否正确，仍然优先用代码 evaluator。
```

---

## 八、自测题

### 自测 1：一句话解释 evaluator

问题：

```text
什么是 evaluator？
```

答案：

```text
evaluator 是用来判断 AI 应用某次输出是否符合预期的评判器，它可以输出 pass/fail、score、失败原因和指标。
```

---

### 自测 2：evaluator 和 eval dataset 有什么区别？

答案：

```text
eval dataset 是评测样本和参考答案，回答“拿什么来评”；evaluator 是评判规则或评判程序，回答“怎么判断对不对”。
```

---

### 自测 3：为什么当前项目优先使用代码 evaluator？

答案：

```text
因为当前项目很多评测目标是结构化、明确、可客观判断的，比如 intent、字段、路由、source、citation、是否创建工单。代码 evaluator 更便宜、更快、更稳定、更适合回归评测和 CI。
```

---

### 自测 4：LLM-as-judge 适合什么，不适合什么？

答案：

```text
LLM-as-judge 适合评开放式自然语言质量、语义等价、回答完整性、语气、RAG 回答是否基于上下文。不适合替代简单等值判断、业务安全红线判断和未校准的高风险审批。
```

---

### 自测 5：pairwise evaluator 解决什么问题？

答案：

```text
pairwise evaluator 用来比较两个输出或两个版本哪个更好，适合 prompt 对比、模型对比、RAG 策略对比和答案生成策略对比。
```

---

### 自测 6：route evaluator 为什么对 Agent 很重要？

答案：

```text
Agent 的质量不只看最终回答，还要看过程是否可控。route evaluator 可以检查是否走了 required nodes、是否误走 forbidden nodes、终点是否正确，能防止跳过确认、误调用工具、误创建工单等流程风险。
```

---

### 自测 7：human evaluator 什么时候不能省？

答案：

```text
在高风险业务、主观质量判断、复杂业务争议、创建 golden dataset、校准 LLM-as-judge 时，人类评审不能省。自动 evaluator 可以辅助，但不能完全替代人类判断。
```

---

### 自测 8：为什么 report generator 不应该承担 evaluator 职责？

答案：

```text
因为 report generator 的职责是展示结果，evaluator 的职责是判断结果。如果把评判逻辑写进报告生成器，报告格式变化会影响评测逻辑，评测逻辑变化也会影响展示，模块边界会混乱。
```

---

### 自测 9：reference-based 和 reference-free 的区别是什么？

答案：

```text
reference-based evaluation 有明确参考答案，可以比较 actual 和 expected；reference-free evaluation 没有固定参考答案，需要根据评价标准、规则、人评或 LLM-as-judge 判断输出质量。
```

---

### 自测 10：真实 LLM 接入后，当前 intent evaluator 是否还要保留？

答案：

```text
要保留。真实 LLM 只是替换或增强 intent 生成方式，intent 是否正确仍然可以用 expected.intent 和 actual.intent 做代码评测。模型变真实后，更需要稳定 evaluator 防止行为退化。
```

---

## 九、本节你应该形成的表达能力

学完本节后，你应该能这样介绍当前项目的 evaluator 体系：

```text
当前项目的 Agent eval 先从确定性的代码/规则 evaluator 做起。

我们有 intent evaluator 评意图分类，有 field evaluator 评工单字段提取，
有 route evaluator 评 LangGraph 节点路径，有 RAG + Agent evaluator 评检索回答、
引用来源和后续工单决策。

这些 evaluator 大多是 reference-based、deterministic、code evaluator，
适合本地自动化、pytest、CI 和回归保护。

eval_suite.py 负责组织多个 evaluator 运行，eval_report.py 负责生成 Markdown 报告，
bad_case_analysis.py 负责失败后的错题分析。

后续真实接入 LLM 后，结构化结果仍然优先用代码 evaluator 评；
开放式回答质量、语气、完整性、语义等价和版本对比，再逐步引入
LLM-as-judge、human evaluator 和 pairwise evaluator。
```

如果你能把上面这段话讲清楚，就说明本节核心已经掌握。

---

## 十、本节小结

本节我们没有新增业务功能。

但这节非常重要。

因为你学会了把 evaluator 分层：

```text
规则 evaluator
代码 evaluator
human evaluator
LLM-as-judge
pairwise evaluator
composite evaluator
summary evaluator
```

你也学会了从不同维度判断 evaluator：

```text
reference-based / reference-free
deterministic / non-deterministic
objective / subjective
single-case / summary-level
absolute scoring / pairwise comparison
```

当前项目已经具备一套本地评测基础：

```text
intent_evaluation.py
field_evaluation.py
route_evaluation.py
rag_agent_evaluation.py
eval_suite.py
eval_report.py
bad_case_analysis.py
```

下一节开始，我们会进入：

```text
阶段 6 第 13 节：真实 LLM 意图识别节点
```

那时要重点学习：

```text
真实模型怎么输出 intent
为什么输出还要 Pydantic 校验
真实 LLM 和 fake LLM 怎么共存
模型输出不稳定时 evaluator 怎么继续发挥作用
```

---

## 十一、参考资料

- [LangSmith Evaluation](https://docs.langchain.com/langsmith/evaluation)
  - 用途：理解 offline evaluation、online evaluation、dataset、evaluator、experiment、production monitoring 的基本流程。

- [LangSmith Evaluation Types](https://docs.langchain.com/langsmith/evaluation-types)
  - 用途：理解 benchmarking、unit tests、regression tests、backtesting、pairwise evaluation，以及 LLM-as-judge、code evaluator、composite evaluator、summary evaluator、pairwise evaluator 等实现方式。

- [LangSmith Code Evaluator SDK](https://docs.langchain.com/langsmith/code-evaluator-sdk)
  - 用途：理解用代码函数实现 evaluator 的方向，和当前项目 Python 代码 evaluator 的思路一致。

- [LangSmith LLM-as-Judge SDK](https://docs.langchain.com/langsmith/llm-as-judge-sdk)
  - 用途：理解如何用大模型作为 judge，对开放式文本质量进行评分。

- [OpenAI Evals Guide](https://developers.openai.com/api/docs/guides/evals)
  - 用途：理解 eval 数据、testing criteria、grader、reference label、模型输出评测等概念。

- [OpenAI Evaluation Best Practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices)
  - 用途：补充理解评测集设计、评测迭代和模型行为质量改进的最佳实践。

- [OpenAI Graders](https://developers.openai.com/api/docs/guides/graders)
  - 用途：理解 string check、text similarity、score model grader、Python code execution 等 grader 类型。
