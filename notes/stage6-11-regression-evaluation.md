# 阶段 6 第 11 节：回归评测

## 本节定位

第 10 节我们学了坏例分析：

```text
bad case 出现后
-> 先看 evidence
-> 判断 expected 是否合理
-> 找第一分叉点
-> 判断问题层
-> 决定 recommended action
-> 给出 regression action
```

第 11 节继续往下走：

```text
坏例修完以后，怎么防止以后又坏回去？
```

这就是：

```text
回归评测
```

本节新增能力：

```text
1. 在 agent_cases.json 中标记第一版 regression 样本
2. 让统一评测入口支持按 tag 和 priority 筛选样本
3. 支持 --regression 只跑回归样本
4. 支持 --priority p0 只跑 P0 样本
5. 在终端输出和 Markdown 报告里显示 case_filter 与 selected_cases
6. 生成稳定的回归评测报告和回归坏例分析报告
```

新增或更新的关键文件：

```text
app/agents/eval_suite.py
scripts/agent_eval.py
data/agent_eval/agent_cases.json
data/agent_eval/reports/agent_regression_report.md
data/agent_eval/reports/agent_regression_bad_case_analysis.md
tests/test_agent_eval_suite.py
```

本节不需要打开 VMware。

不需要 Docker。

不需要 Qdrant。

不需要 Milvus。

也不会真实调用大模型。

---

## 本节学习目标

学完本节，你应该能解释清楚：

1. 什么是 regression。
2. 什么是 regression evaluation。
3. 回归评测和普通评测的区别。
4. 为什么 AI 项目容易出现“修 A 坏 B”。
5. 什么是回归样本。
6. 什么是 P0 回归集。
7. 什么是 full suite regression。
8. 什么是 targeted regression。
9. 为什么坏例修复后应该进入回归集。
10. 为什么本节用 tag 标记回归样本。
11. 为什么 `--regression` 和 `--priority p0` 可以组合使用。
12. 为什么报告里必须显示 `case_filter` 和 `selected_cases`。
13. 如何运行当前项目的第一版回归评测。
14. 如何判断回归评测是否通过。
15. 如何把未来坏例变成新的回归保护。

---

## 本节先不学什么

本节暂时不学：

```text
1. GitHub Actions 自动跑回归评测
2. 每次 PR 自动比较历史报告
3. 按 commit 保存历史 regression report
4. 基于 LangSmith dataset split 的正式回归集管理
5. 线上 bad case 自动进入离线评测集
6. flaky eval 自动隔离
7. 多模型版本回归对比
```

原因是：

```text
先要在本地掌握什么是回归评测，以及如何稳定地跑一组回归样本。
```

如果没有本地回归入口，就直接上 CI，会导致：

```text
CI 只是把混乱自动化。
```

本节先把本地基础做好。

---

## 一、基础知识铺垫

### 1. 什么是 regression

regression 在软件工程里通常翻译为：

```text
回归
```

它不是数学里的回归分析。

在测试和评测语境下，regression 指的是：

```text
以前能正常工作的能力，在后续改动后坏掉了。
```

例如，之前系统能正确识别：

```text
“帮我查一下订单 A1001”
```

为：

```text
order_query
```

后来你为了优化投诉识别，改了意图分类规则。

结果这个订单查询被误判为：

```text
ticket_request
```

这就是 regression：

```text
旧能力退化了。
```

### 2. 什么是回归评测

回归评测就是：

```text
用固定样本反复检查旧能力是否还正常。
```

它的核心问题不是：

```text
新功能有没有做出来？
```

而是：

```text
原来已经正确的能力有没有被新改动破坏？
```

在当前项目里，回归评测就是反复运行一组固定 Agent cases：

```text
intent
field
route
rag
```

看它们是否继续通过。

### 3. 回归评测和普通评测有什么区别

普通评测关注：

```text
当前系统在某批样本上表现怎么样。
```

回归评测更关注：

```text
当前系统有没有把已经通过的关键能力弄坏。
```

普通评测可以更宽。

回归评测通常更稳定、更关键、更经常跑。

你可以这样理解：

```text
普通评测：看整体能力画像
回归评测：守住不能退化的底线
```

### 4. 为什么 AI 项目特别容易修 A 坏 B

AI 项目尤其容易发生 regression。

原因包括：

```text
1. 用户表达很丰富
2. 意图边界容易重叠
3. prompt 改动影响面大
4. RAG 检索参数影响多个问题
5. 工具调用策略改变后会影响路由
6. 模型版本变化可能改变输出风格
7. 一条规则可能误伤相邻场景
```

例如你为了让：

```text
“我要投诉商家不发货”
```

更容易进入工单流程，增加了“投诉”关键词。

但可能误伤：

```text
“投诉处理规则是什么？”
```

后者可能其实是政策问答。

这就是 AI 应用里常见的：

```text
修 A 坏 B。
```

### 5. 什么是回归样本

回归样本就是：

```text
被选入回归评测集，需要长期反复检查的样本。
```

它通常来自：

```text
1. 核心业务流程
2. 曾经出现过的坏例
3. 高风险安全边界
4. 用户高频问题
5. 容易被规则误伤的边界
6. 线上真实问题沉淀
```

回归样本不是越多越好。

第一版应该小而关键。

如果一开始就把所有样本都塞进回归集，也不是不能跑，但你会失去：

```text
哪些样本最关键
哪些样本是必须守住的底线
```

这个层次。

### 6. 什么是 P0 回归集

P0 表示最高优先级。

P0 回归集就是：

```text
最不能退化的一组关键样本。
```

当前项目里 P0 样本包括：

```text
RAG 政策回答
RAG no_context 转政策缺口工单
订单查询
订单号缺失追问
物流/投诉/退款工单
安全边界
提示词注入防护
```

这些能力如果退化，说明 Agent 主链路有明显问题。

所以本节把 10 条 P0 样本标记为：

```text
regression
p0_regression
```

### 7. 什么是 full suite regression

full suite regression 指：

```text
在回归样本上运行所有评测套件。
```

当前命令：

```powershell
uv run python scripts/agent_eval.py --regression --priority p0
```

会在 10 条 P0 回归样本上运行：

```text
intent
field
route
rag
```

这就是当前项目的第一版 full suite regression。

### 8. 什么是 targeted regression

targeted regression 指：

```text
针对某个刚改过的能力，只跑相关回归样本或相关 suite。
```

例如你只改了 RAG citation 逻辑。

可以先跑：

```powershell
uv run python scripts/agent_eval.py --regression --suite rag
```

这比每次都跑完整 suite 更快。

但注意：

```text
targeted regression 不能完全替代 full suite regression。
```

因为有些改动影响面可能比你以为的大。

### 9. 什么是 smoke、targeted、full 的分层

回归评测可以分层：

```text
smoke regression：最少样本，快速确认系统没明显坏
targeted regression：针对改动范围跑相关样本
full regression：完整回归集全部跑
```

当前项目还没有单独 smoke 集。

本节做的是：

```text
P0 regression
```

它比 smoke 更完整，但还没有发展成大型生产回归体系。

### 10. 为什么用 tag 标记回归样本

本节没有改 schema。

而是复用已有字段：

```text
metadata.tags
```

给关键样本加：

```text
regression
p0_regression
```

原因是：

```text
1. 当前 schema 已经支持 tags
2. tags 很适合表达样本分组
3. 不需要新增字段和迁移逻辑
4. 后续可以继续加 safety_regression、rag_regression 等标签
```

这是一种保守、低风险的演进方式。

### 11. 为什么还要支持 priority 筛选

只有 tag 还不够。

因为你可能想跑：

```text
所有 regression 样本
```

也可能想跑：

```text
只跑 P0 regression 样本
```

所以本节支持：

```text
--regression
--priority p0
```

组合起来就是：

```text
包含 regression 标签，且 priority 是 p0。
```

### 12. 什么是 case_filter

case_filter 是：

```text
本次评测对样本做了什么筛选。
```

例如全量评测：

```text
case_filter: all
selected_cases: 12
```

P0 回归评测：

```text
case_filter: tags=regression;priority=p0
selected_cases: 10
```

报告里必须显示这个信息。

否则别人看到：

```text
cases: 10
```

会不知道：

```text
为什么不是 12？
是数据丢了，还是筛选了？
```

### 13. 为什么筛选结果为 0 要报错

如果用户输入：

```powershell
uv run python scripts/agent_eval.py --tag not_a_real_tag
```

筛选结果是 0。

这时不能默默通过。

否则报告可能显示：

```text
0 cases
passed: true
```

这会误导人。

所以本节实现：

```text
筛选后 0 条样本 -> 抛出 ValueError
```

这是为了避免“空跑成功”。

### 14. 为什么回归报告也要有坏例分析

回归评测失败时，你不只想知道：

```text
回归失败了。
```

还想知道：

```text
失败集中在哪个类别？
是 RAG、route、field 还是 intent？
```

所以本节生成两份回归产物：

```text
agent_regression_report.md
agent_regression_bad_case_analysis.md
```

当前都显示通过。

以后如果回归失败，坏例分析报告会帮助你更快定位。

### 15. 什么是回归基线

回归基线可以理解为：

```text
当前确认通过的一组样本和结果。
```

本节生成的：

```text
agent_regression_report.md
```

可以作为学习项目里的第一版回归基线。

它记录：

```text
P0 regression 样本 10 条
intent 10/10
field 4/4
route 10/10
rag 3/3
failed_suites 0
```

以后如果改代码后这份报告变红，就说明：

```text
关键能力退化了。
```

### 16. 回归评测和坏例分析怎么衔接

第 10 节的坏例分析里有：

```text
Regression Action
```

它的含义是：

```text
这个坏例修完后，应该留在哪个 suite 里继续防退化。
```

第 11 节就是把这个动作落地：

```text
用 regression 标签把关键样本纳入回归评测。
```

所以关系是：

```text
坏例分析告诉你为什么失败
回归评测防止它以后再失败
```

---

## 二、本节主题系统讲解

### 1. 本节前后的能力变化

第 10 节之后，我们可以生成坏例分析报告。

但还不能方便地说：

```text
只跑关键回归样本。
```

第 11 节之后，可以运行：

```powershell
uv run python scripts/agent_eval.py --regression --priority p0
```

得到：

```text
case_filter: tags=regression;priority=p0
selected_cases: 10
```

这说明：

```text
当前运行的是 P0 回归集。
```

### 2. agent_cases.json 的变化

本节没有新增样本。

只是给 10 条 P0 样本加了 tags：

```text
regression
p0_regression
```

例如：

```json
"tags": ["policy_question", "rag", "refund", "regression", "p0_regression"]
```

这表示：

```text
这条样本属于回归集，并且是 P0 回归样本。
```

当前没有给 P1 样本加 regression。

因为第一版先守住 P0。

### 3. app/agents/eval_suite.py 的变化

本节新增：

```python
class AgentEvalCaseFilter(BaseModel):
    include_tags: list[str] = Field(default_factory=list)
    priority: AgentEvalPriority | None = None
```

它表达：

```text
本次评测要筛选哪些样本。
```

当前支持：

```text
include_tags
priority
```

以后可以扩展：

```text
business_domain
case_type
difficulty
case_id
```

但本节先不扩展太多。

### 4. filter_agent_eval_cases 的作用

新增函数：

```python
def filter_agent_eval_cases(cases, case_filter=None) -> list[AgentEvalCase]:
```

它负责从所有 cases 里筛选出目标样本。

逻辑是：

```text
如果没有 filter -> 返回全部
如果指定 priority -> 只保留对应 priority
如果指定 include_tags -> 只保留包含所有 tag 的样本
```

注意：

```text
include_tags 是全部满足，不是满足任意一个。
```

例如：

```text
include_tags=["regression", "rag"]
```

表示：

```text
必须同时包含 regression 和 rag。
```

### 5. describe_agent_eval_case_filter 的作用

新增函数：

```python
describe_agent_eval_case_filter(...)
```

它把 filter 变成可读字符串：

```text
all
tags=regression;priority=p0
```

这个字符串会进入：

```text
终端输出
Markdown 报告
坏例分析报告
```

这样以后回看报告时，你能知道：

```text
这次到底跑的是哪批样本。
```

### 6. AgentEvalRunReport 新增字段

第 11 节给 `AgentEvalRunReport` 增加：

```text
selected_case_count
case_filter
```

它们的作用是：

```text
记录本次评测筛选了多少样本，以及筛选条件是什么。
```

全量评测：

```text
case_filter = all
selected_case_count = 12
```

P0 回归评测：

```text
case_filter = tags=regression;priority=p0
selected_case_count = 10
```

### 7. scripts/agent_eval.py 新增参数

新增参数：

```text
--regression
--tag
--priority
```

它们的用途：

```text
--regression：等价于要求样本包含 regression 标签
--tag：要求样本包含指定标签，可重复
--priority：要求样本是 p0/p1/p2
```

常用命令：

```powershell
uv run python scripts/agent_eval.py --regression --priority p0
```

只跑 RAG 回归：

```powershell
uv run python scripts/agent_eval.py --regression --tag rag --suite rag
```

### 8. _build_case_filter 的作用

脚本中新增：

```python
def _build_case_filter(...)
```

它把 CLI 参数转换成：

```text
AgentEvalCaseFilter
```

如果用户没有传任何筛选参数，返回：

```text
None
```

这代表全量样本。

如果用户传：

```text
--regression --priority p0
```

就构造：

```text
include_tags=["regression"]
priority="p0"
```

### 9. eval_report.py 的变化

第 11 节让 Markdown 报告的 Overall 增加：

```text
Case filter
Selected cases
```

所以报告现在能显示：

```text
Case filter | tags=regression;priority=p0
Selected cases | 10
```

这对回归报告非常重要。

### 10. bad_case_analysis.py 的变化

坏例分析总览也增加：

```text
Case filter
Selected cases
```

原因是：

```text
坏例分析报告必须知道自己分析的是哪批样本。
```

如果回归坏例分析报告显示：

```text
Bad cases: 0
```

你还要知道它是在：

```text
P0 回归样本 10 条
```

这个范围内没有坏例。

### 11. 回归报告产物

本节生成：

```text
data/agent_eval/reports/agent_regression_report.md
```

内容核心：

```text
Status: PASS
Case filter: tags=regression;priority=p0
Selected cases: 10
Failed suites: 0
```

这就是当前 P0 回归基线。

### 12. 回归坏例分析产物

本节生成：

```text
data/agent_eval/reports/agent_regression_bad_case_analysis.md
```

当前内容核心：

```text
Case filter: tags=regression;priority=p0
Selected cases: 10
Bad cases: 0
No bad cases to analyze.
```

如果以后回归失败，这份报告会显示坏例分类。

### 13. 当前 P0 回归集包含哪些样本

当前 P0 回归集共 10 条：

```text
agent_policy_refund_arrival_001
agent_policy_account_security_001
agent_no_context_membership_points_001
agent_order_query_with_order_id_001
agent_order_query_missing_order_id_001
agent_ticket_logistics_full_001
agent_ticket_complaint_missing_order_001
agent_ticket_refund_full_001
agent_unsupported_price_prediction_001
agent_prompt_injection_ignore_rules_001
```

不包含两个 P1 样本：

```text
agent_smalltalk_hello_001
agent_unclear_empty_001
```

这不是说 P1 不重要。

只是第一版 P0 回归集先守住关键能力。

### 14. 为什么 field suite 在 10 个样本里只显示 4 cases

你会看到回归报告里：

```text
Selected cases: 10
field cases: 4
```

这不是矛盾。

原因是：

```text
统一入口先筛出 10 条回归样本；
field evaluator 再从这 10 条里挑出 should_create_ticket=true 的工单字段样本。
```

所以：

```text
selected_cases 是输入给 suite 的总样本数
field cases 是字段评测真正适用的样本数
```

RAG suite 同理：

```text
selected_cases: 10
rag cases: 3
```

### 15. 回归评测失败后怎么处理

如果未来看到：

```text
failed_suites: 1
passed: false
```

不要只说失败。

处理顺序：

```text
1. 打开 agent_regression_report.md
2. 看哪个 suite FAIL
3. 打开对应 Bad Cases
4. 打开 agent_regression_bad_case_analysis.md
5. 看 category 和 evidence
6. 找第一分叉点
7. 判断 expected 是否合理
8. 决定改代码、改 expected、改数据集还是补规则
9. 修复后重新跑 --regression --priority p0
10. 再跑必要的 full suite
```

### 16. 本节和第 12 节的关系

第 11 节解决：

```text
回归样本怎么筛，回归评测怎么跑。
```

第 12 节会学习：

```text
evaluator 类型。
```

也就是：

```text
规则 evaluator
代码 evaluator
人工 evaluator
LLM-as-judge
pairwise evaluator
```

这些 evaluator 以后都可能进入回归体系。

---

## 三、新增代码讲解

### 1. agent_cases.json 增加 regression 标签

本节修改了：

```text
data/agent_eval/agent_cases.json
```

给 10 条 P0 样本增加：

```text
regression
p0_regression
```

例如：

```json
"tags": ["order_query", "tool_call", "query_order", "regression", "p0_regression"]
```

这说明：

```text
这个订单查询样本属于 P0 回归集。
```

### 2. AgentEvalCaseFilter

新增：

```python
class AgentEvalCaseFilter(BaseModel):
    include_tags: list[str] = Field(default_factory=list)
    priority: AgentEvalPriority | None = None
```

它是结构化筛选条件。

不用在多个函数里传散乱参数：

```text
tags
priority
regression
```

而是统一成：

```text
AgentEvalCaseFilter
```

### 3. filter_agent_eval_cases

这个函数执行筛选。

关键逻辑：

```python
if case_filter.priority is not None and eval_case.metadata.priority != case_filter.priority:
    continue
if include_tags and not include_tags.issubset(set(eval_case.metadata.tags)):
    continue
```

第一段处理 priority。

第二段处理 tags。

`issubset` 表示：

```text
样本 tags 必须包含所有 include_tags。
```

### 4. 空筛选保护

新增逻辑：

```python
if not selected_cases:
    raise ValueError(...)
```

这是为了防止：

```text
筛选条件写错，但脚本空跑成功。
```

空跑成功非常危险。

因为它会让你误以为：

```text
回归通过了。
```

实际只是：

```text
一个样本都没跑。
```

### 5. format_agent_eval_run_report 新增筛选信息

终端输出新增：

```text
case_filter: tags=regression;priority=p0
selected_cases: 10
```

这两行是第 11 节的关键。

它们告诉你：

```text
这次不是全量 12 条，而是 P0 回归 10 条。
```

### 6. scripts/agent_eval.py 新增 --regression

`--regression` 是便捷参数。

它的实际效果是：

```text
include_tags 增加 regression
```

所以：

```powershell
uv run python scripts/agent_eval.py --regression
```

等价于：

```text
只选包含 regression 标签的样本。
```

### 7. scripts/agent_eval.py 新增 --tag

`--tag` 是通用标签筛选。

例如：

```powershell
uv run python scripts/agent_eval.py --tag rag
```

表示：

```text
只选包含 rag 标签的样本。
```

可以重复：

```powershell
uv run python scripts/agent_eval.py --tag regression --tag rag
```

表示：

```text
同时包含 regression 和 rag。
```

### 8. scripts/agent_eval.py 新增 --priority

`--priority` 限制：

```text
p0
p1
p2
```

例如：

```powershell
uv run python scripts/agent_eval.py --priority p0
```

表示只跑 P0 样本。

与 `--regression` 组合：

```powershell
uv run python scripts/agent_eval.py --regression --priority p0
```

就是当前 P0 回归评测。

### 9. tests/test_agent_eval_suite.py 的新增测试

本节新增测试覆盖：

```text
1. regression + p0 能选出 10 条样本
2. 选出的样本都包含 regression 标签
3. 选出的样本都是 p0
4. p1 smalltalk 和 unclear 不在 P0 回归集
5. regression filter 跑 intent 和 rag 能通过
6. 空筛选会报错
7. 终端格式化输出包含 case_filter 和 selected_cases
```

这些测试保护回归入口的核心行为。

---

## 四、本节运行结果

运行 P0 回归评测：

```powershell
uv run python scripts/agent_eval.py --regression --priority p0
```

核心输出：

```text
case_filter: tags=regression;priority=p0
selected_cases: 10
failed_suites: 0
passed: true
```

生成回归报告：

```powershell
uv run python scripts/agent_eval.py --cases-path data/agent_eval/agent_cases.json --regression --priority p0 --report-path data/agent_eval/reports/agent_regression_report.md --bad-case-analysis-path data/agent_eval/reports/agent_regression_bad_case_analysis.md
```

报告文件：

```text
data/agent_eval/reports/agent_regression_report.md
data/agent_eval/reports/agent_regression_bad_case_analysis.md
```

当前 P0 回归结果：

```text
Selected cases: 10
intent: 10/10
field: 4/4
route: 10/10
rag: 3/3
failed_suites: 0
passed: true
```

新增测试局部运行：

```powershell
uv run pytest tests/test_agent_eval_suite.py tests/test_agent_eval_report.py tests/test_bad_case_analysis.py -q
```

结果：

```text
19 passed
```

---

## 五、怎么阅读回归报告

### 1. 先确认是不是回归报告

看 Overall：

```text
Case filter | tags=regression;priority=p0
Selected cases | 10
```

如果是：

```text
Case filter | all
Selected cases | 12
```

那是全量报告，不是 P0 回归报告。

### 2. 再看 Status

当前：

```text
Status | PASS
```

说明 P0 回归通过。

### 3. 再看 Suite Summary

重点看：

```text
Failed cases
Status
```

当前所有 suite 都是：

```text
FAIL cases = 0
PASS
```

### 4. 注意 selected_cases 和 suite cases 的区别

`Selected cases` 是筛选后的输入样本总数。

每个 suite 的 `Cases` 是该 suite 实际适用的样本数。

所以看到：

```text
Selected cases: 10
rag cases: 3
```

不是错误。

是因为 10 条回归样本里只有 3 条有 RAG expected。

### 5. 回归失败时看坏例分析报告

如果回归报告失败，打开：

```text
agent_regression_bad_case_analysis.md
```

看：

```text
Category Summary
Evidence
Recommended Action
Regression Action
```

---

## 六、常见误区

### 误区 1：回归评测就是重新跑一遍所有测试

不准确。

回归评测关注的是：

```text
旧能力是否退化。
```

可以跑全量，也可以跑关键回归集。

### 误区 2：所有样本都应该立刻进 P0 回归集

不一定。

P0 回归集应该守住最关键能力。

所有样本都塞进去会让优先级失去意义。

### 误区 3：targeted regression 可以替代 full regression

不能完全替代。

targeted regression 适合快速检查局部改动。

但发布前或大改后仍应跑 full suite regression。

### 误区 4：回归评测通过就说明系统没问题

不是。

它只说明：

```text
当前回归集覆盖的能力没有退化。
```

没覆盖的场景仍然可能有问题。

### 误区 5：筛选 0 条样本也算通过

不应该。

空筛选应该报错。

否则会产生假的通过结果。

### 误区 6：报告里不需要写筛选条件

必须写。

否则别人不知道报告是全量、P0 回归、RAG 回归，还是某个 tag 的局部评测。

### 误区 7：坏例修完后就可以删掉

通常不应该。

坏例修完后更应该保留或转成回归样本。

这样以后才能防止同类问题再次出现。

---

## 七、本节练习

### 练习 1：运行 P0 回归评测

题目：

在 `projects/ai-service` 目录下运行 P0 回归评测，命令是什么？

参考答案：

```powershell
uv run python scripts/agent_eval.py --regression --priority p0
```

当前应该看到：

```text
case_filter: tags=regression;priority=p0
selected_cases: 10
passed: true
```

### 练习 2：生成 P0 回归报告

题目：

生成 P0 回归评测报告和坏例分析报告，命令是什么？

参考答案：

```powershell
uv run python scripts/agent_eval.py --cases-path data/agent_eval/agent_cases.json --regression --priority p0 --report-path data/agent_eval/reports/agent_regression_report.md --bad-case-analysis-path data/agent_eval/reports/agent_regression_bad_case_analysis.md
```

生成：

```text
data/agent_eval/reports/agent_regression_report.md
data/agent_eval/reports/agent_regression_bad_case_analysis.md
```

### 练习 3：只跑 RAG 回归样本

题目：

只运行 RAG 相关的回归评测，命令怎么写？

参考答案：

```powershell
uv run python scripts/agent_eval.py --regression --tag rag --suite rag
```

这里：

```text
--regression 要求 regression 标签
--tag rag 要求 rag 标签
--suite rag 只运行 RAG suite
```

### 练习 4：解释 selected_cases 和 suite cases

题目：

为什么报告里 `Selected cases` 是 10，但 RAG suite 的 `cases` 是 3？

参考答案：

因为 `Selected cases` 是回归筛选后进入统一评测入口的样本总数。

RAG suite 只会从这 10 条里挑出带 `expected.rag` 的样本，所以是 3 条。

### 练习 5：解释为什么空筛选要报错

题目：

为什么 `--tag not_a_real_tag` 选出 0 条样本时不应该算通过？

参考答案：

因为没有运行任何样本。

如果空跑也返回通过，会制造假的安全感。

所以筛选 0 条样本应该直接报错。

### 练习 6：解释 regression tag 的价值

题目：

为什么本节用 `metadata.tags` 增加 `regression`，而不是新增 schema 字段？

参考答案：

因为已有 schema 已经支持 tags，tags 很适合表达样本分组。

这样改动小、风险低，也方便以后继续加 `rag_regression`、`safety_regression` 等标签。

### 练习 7：坏例修复后应该做什么

题目：

一个坏例修复后，除了确认当前通过，还应该做什么？

参考答案：

应该把它保留在评测集里，必要时加 `regression` 标签，让它进入回归评测，防止以后再次退化。

### 练习 8：什么时候跑 full suite regression

题目：

什么时候应该跑完整回归，而不是只跑 targeted regression？

参考答案：

包括：

```text
发布前
改了共享逻辑
改了 prompt 或模型输出格式
改了 Agent 路由
改了 RAG 检索参数
修复影响面不确定的坏例
```

---

## 八、自测题

### 自测 1：什么是 regression？

参考答案：

regression 是以前正常工作的能力，在后续改动后坏掉了。

### 自测 2：什么是回归评测？

参考答案：

回归评测是用固定样本反复检查旧能力是否仍然正常，防止新改动破坏已有能力。

### 自测 3：为什么 AI 项目容易修 A 坏 B？

参考答案：

因为用户表达复杂、意图边界重叠、prompt 和规则影响面大、RAG 参数和模型版本变化会影响多个场景。

### 自测 4：P0 回归集应该包含什么样的样本？

参考答案：

应该包含最关键、最不能退化的业务和安全样本，例如核心 RAG 问答、订单查询、工单创建、缺字段追问、安全边界和提示词注入防护。

### 自测 5：`--regression --priority p0` 表示什么？

参考答案：

表示只运行同时满足以下条件的样本：

```text
包含 regression 标签
priority 是 p0
```

### 自测 6：为什么报告要显示 `case_filter`？

参考答案：

因为读者需要知道本次评测跑的是全量样本、回归样本、P0 样本，还是某个 tag 的局部样本。

### 自测 7：为什么 targeted regression 不能完全替代 full regression？

参考答案：

因为局部改动可能影响到你没预料到的能力。targeted regression 适合快速检查相关区域，但完整回归更适合发布前和大改后。

### 自测 8：当前 P0 回归评测结果是什么？

参考答案：

当前 P0 回归评测选中 10 条样本，运行 intent、field、route、rag 四个 suite，结果是：

```text
failed_suites: 0
passed: true
```

---

## 九、本节你应该形成的表达能力

学完本节后，你应该能这样说明：

```text
第 11 节学习的是回归评测。回归指的是原来正常的能力在后续改动后退化。
本节用 metadata.tags 标记第一版 P0 回归集，给 10 条 P0 样本增加 regression 和 p0_regression 标签。
统一脚本新增 --regression、--tag、--priority 参数，可以只跑回归样本或某类局部样本。
AgentEvalRunReport、终端输出、Markdown 报告和坏例分析报告都增加了 case_filter 与 selected_cases，这样回看报告时能知道本次到底跑了哪批样本。
当前 P0 回归评测 selected_cases=10，intent/field/route/rag 全部通过。
```

如果别人问你：

```text
为什么坏例修完后要进入回归集？
```

你可以回答：

```text
因为修复一次不代表以后不会再坏。进入回归集后，每次相关改动都能重新检查这条样本，防止旧问题回到系统里。
```

如果别人问你：

```text
为什么不只跑全量评测？
```

你可以回答：

```text
全量评测重要，但回归集强调关键旧能力防退化。回归集可以更小、更稳定、更适合频繁运行；全量评测适合更完整的阶段性检查。
```

---

## 十、本节小结

本节完成了当前项目第一版回归评测能力：

```text
1. P0 样本加 regression 标签
2. 统一脚本支持 --regression
3. 支持 --tag 和 --priority
4. 筛选结果为 0 时直接报错
5. 终端输出显示 case_filter 和 selected_cases
6. Markdown 报告显示 case_filter 和 selected_cases
7. 坏例分析报告显示 case_filter 和 selected_cases
8. 生成 P0 回归报告和回归坏例分析报告
```

本节真正要掌握的是：

```text
回归评测不是为了证明新功能多强，而是为了守住旧能力不退化。
```

下一节是：

```text
阶段 6 第 12 节：evaluator 类型
```

我们会系统学习：

```text
规则 evaluator、代码 evaluator、人工 evaluator、LLM-as-judge、pairwise evaluator 分别适合什么场景。
```

---

## 十一、参考资料

- [LangSmith Evaluation concepts](https://docs.langchain.com/langsmith/evaluation-concepts)
  - 用途：理解 offline evaluation、dataset、examples、reference outputs、regression testing 和 continuous improvement 的关系。

- [OpenAI Evals guide](https://developers.openai.com/api/docs/guides/evals)
  - 用途：辅助理解 eval 如何系统化衡量应用行为，而不是靠临时试问。

- [pytest: How to invoke pytest](https://docs.pytest.org/en/stable/how-to/usage.html)
  - 用途：理解如何运行指定测试、局部测试和全量测试；回归评测在工程习惯上和 pytest 的局部/全量运行思想相通。
