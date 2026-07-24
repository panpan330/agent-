# 阶段 6 第 10 节：坏例分析

## 本节定位

前面我们已经有了：

```text
第 4 节：意图识别评测
第 5 节：工单字段提取评测
第 6 节：Agent 路由评测
第 7 节：RAG + Agent 组合评测
第 8 节：统一评测脚本
第 9 节：Markdown 评测报告
```

现在我们能运行：

```powershell
uv run python scripts/agent_eval.py
```

也能生成报告：

```powershell
uv run python scripts/agent_eval.py --cases-path data/agent_eval/agent_cases.json --report-path data/agent_eval/reports/agent_eval_report.md
```

但是，报告里如果出现：

```text
Bad cases:
```

我们不能只停在：

```text
失败了。
```

真正重要的是继续追问：

```text
为什么失败？
失败发生在哪一层？
是代码错、数据错、expected 错、还是业务边界没定义清楚？
应该怎么修？
修完怎么防止以后退化？
```

这就是第 10 节：

```text
坏例分析
```

本节新增：

```text
app/agents/bad_case_analysis.py
tests/test_bad_case_analysis.py
data/agent_eval/reports/agent_bad_case_analysis.md
data/agent_eval/reports/bad_case_analysis_sample.md
```

并增强：

```text
scripts/agent_eval.py
```

新增参数：

```text
--bad-case-analysis-path
```

当前真实评测仍然全部通过，所以真实坏例分析报告是：

```text
No bad cases to analyze.
```

为了教学，本节另外生成了一份明确标注为 synthetic 的示例报告：

```text
data/agent_eval/reports/bad_case_analysis_sample.md
```

它不代表当前 Agent 真实失败。

它只是用来学习：

```text
如果失败了，应该怎么读、怎么分类、怎么分析。
```

本节不需要打开 VMware。

不需要 Docker。

不需要 Qdrant。

不需要 Milvus。

也不会真实调用大模型。

---

## 本节学习目标

学完本节，你应该能解释清楚：

1. 什么是 bad case。
2. bad case 和 bug 有什么区别。
3. 为什么坏例分析是 AI 应用评测的核心。
4. 为什么失败不等于一定要立刻改代码。
5. 坏例可能来自哪些层。
6. 什么是 expected issue。
7. 什么是 dataset issue。
8. 什么是 rule issue。
9. 什么是 prompt/model issue。
10. 什么是 RAG retrieval/citation issue。
11. 什么是 Agent routing issue。
12. 什么是 ticket field extraction issue。
13. 什么是 regression action。
14. 如何把坏例变成回归保护。
15. 当前项目如何把 bad case 文本转换成分析报告。
16. 为什么真实评测通过时也可以生成“无坏例分析报告”。
17. 为什么 synthetic 示例必须明确标注。

---

## 本节先不学什么

本节暂时不学：

```text
1. 自动修复 bad case
2. LLM 自动判断根因
3. LangSmith annotation queue
4. 多人评审工作流
5. 线上用户反馈入库
6. 历史 bad case 趋势图
7. 自动创建 GitHub issue
8. 自动生成 prompt 修改建议
```

原因是：

```text
你现在最需要先学会人工分析坏例。
```

如果人工都不知道怎么判断，直接让 LLM 或平台自动分析，很容易变成：

```text
工具看起来高级，但你自己解释不清楚。
```

本节的目标不是“自动化程度最高”。

而是：

```text
把坏例分析的基本思维练扎实。
```

---

## 一、基础知识铺垫

### 1. 什么是 bad case

bad case 可以理解为：

```text
评测中没有达到预期的样本。
```

在我们的项目里，一个 bad case 通常意味着：

```text
某条 agent_cases.json 里的样本，实际运行结果和 expected 不一致。
```

例如：

```text
expected intent = policy_question
actual intent = ticket_request
```

这就是意图识别 bad case。

再例如：

```text
expected_path = normalize_user_input -> classify_intent -> retrieve_policy -> decide_ticket_need
actual_path = normalize_user_input -> classify_intent -> retrieve_policy -> decide_ticket_need -> extract_ticket_fields
```

这就是路由 bad case。

bad case 的重点不是“看起来不好”。

而是：

```text
它违反了我们事先写好的 expected。
```

### 2. bad case 和 bug 的区别

bad case 不一定等于 bug。

bug 通常表示：

```text
程序实现和明确需求不一致。
```

bad case 表示：

```text
评测结果和 expected 不一致。
```

这里有一个关键问题：

```text
expected 本身可能也错。
```

所以出现 bad case 时，不能立刻说：

```text
代码错了。
```

正确顺序应该是：

```text
1. 先确认 expected 是否合理
2. 再确认输入数据是否合理
3. 再确认实际输出从哪一步开始偏离
4. 最后决定是否改代码、改数据、改 expected、补样本或补说明
```

### 3. 为什么 AI 应用更依赖 bad case 分析

传统后端系统很多行为是确定的。

例如：

```text
订单不存在 -> 返回 404
参数缺失 -> 返回 422
```

但 AI 应用更容易遇到边界模糊：

```text
用户这句话到底是问政策，还是想投诉？
缺少订单号时应该追问，还是创建人工工单？
RAG 找到相似文档但不是最准确文档，算不算通过？
模型字段提取漏了一个隐含信息，要不要算错？
```

所以 AI 应用的质量提升不是只靠：

```text
跑一遍测试。
```

更重要的是：

```text
不断看 bad cases，分析原因，把分析结果变成更好的规则、prompt、数据集和回归评测。
```

### 4. 什么是根因

根因是 root cause。

可以理解为：

```text
导致 bad case 出现的最关键原因。
```

一个 bad case 表面上可能表现为：

```text
RAG 没有引用正确来源。
```

但根因可能有很多：

```text
知识库里没有这份文档
chunk 切分太碎
query 改写丢了关键词
向量检索 top_k 太小
score_threshold 太高
citation 映射字段错了
expected_sources 写错了
```

这些修法完全不一样。

所以坏例分析的目标不是只记录现象。

而是要尽量定位：

```text
第一处真正出错的位置。
```

### 5. 什么是第一分叉点

第一分叉点可以理解为：

```text
实际链路第一次偏离预期链路的位置。
```

例如 expected path：

```text
normalize_user_input
-> classify_intent
-> retrieve_policy
-> decide_ticket_need
```

actual path：

```text
normalize_user_input
-> classify_intent
-> retrieve_policy
-> decide_ticket_need
-> extract_ticket_fields
```

前四步都一样。

分叉点是：

```text
decide_ticket_need 之后多走了 extract_ticket_fields
```

这说明你不应该先怀疑：

```text
classify_intent
retrieve_policy
```

更应该检查：

```text
decide_ticket_need
```

这就是坏例分析里的关键能力。

### 6. 什么是 expected issue

expected issue 表示：

```text
评测预期本身不合理。
```

例如用户说：

```text
帮我查一下 ORDER1001 物流。
```

如果 expected intent 写成：

```text
policy_question
```

那大概率 expected 是错的。

这时如果实际系统识别成：

```text
order_query
```

虽然评测会失败，但你不应该改代码。

应该改：

```text
agent_cases.json 里的 expected
```

所以坏例分析必须先问：

```text
expected 合理吗？
```

### 7. 什么是 dataset issue

dataset issue 表示：

```text
评测数据本身有问题。
```

可能包括：

```text
输入句子太假
样本和业务不符
样本缺少必要上下文
同一个 case_id 重复
metadata 标错
priority 标错
```

dataset issue 不一定是业务代码问题。

它可能是：

```text
评测集设计需要修正。
```

### 8. 什么是 rule issue

rule issue 表示：

```text
规则判断没有覆盖某种表达。
```

当前学习项目里，很多 Agent 行为是 fake/rule-based。

例如：

```text
classify_ticket_intent
FakePolicyRagService
decide_ticket_need
extract_ticket_fields
```

如果用户换一种表达，规则没识别出来，就可能出现 bad case。

这种问题通常要考虑：

```text
加规则
改规则顺序
扩大关键词覆盖
避免规则误伤
补相邻样本
```

### 9. 什么是 prompt/model issue

后续第 13 节以后会接入真实 LLM 节点。

那时候 bad case 可能来自：

```text
prompt 不清楚
输出格式不稳定
模型理解错意图
模型漏提字段
模型过度推断
模型不遵守系统边界
```

这类问题不一定能靠普通 if else 修掉。

可能需要：

```text
改 prompt
加 few-shot 示例
加强 Pydantic 校验
加入 retry
拆任务
改模型
```

本节先不真实调用模型，但你要先知道这个分类。

### 10. 什么是 RAG retrieval/citation issue

RAG 相关坏例常见有两类：

```text
检索问题
引用问题
```

检索问题是：

```text
该找回的资料没有找回。
```

引用问题是：

```text
资料可能找到了，但最终 citation/source 不对。
```

例如：

```text
expected_sources: ['refund-return-policy.md']
actual_sources: ['account-security-faq.md']
missing_sources=['refund-return-policy.md']
```

这就是典型的：

```text
rag_retrieval_or_citation
```

分析时不要直接改 Agent 路由。

要先检查：

```text
知识库是否有资料
chunk 是否合理
query 是否保留关键词
top_k 是否太小
score_threshold 是否过高
source metadata 是否正确
citation 映射是否丢字段
```

### 11. 什么是 Agent routing issue

Agent routing issue 表示：

```text
Agent 走错了节点路径。
```

例如：

```text
本来 RAG 已经回答了政策问题，不应该创建工单。
```

但实际路径多走了：

```text
extract_ticket_fields
```

这说明可能是：

```text
decide_ticket_need 的条件判断错了。
```

路由问题一定要看：

```text
expected_path
actual_path
terminal node
missing_required_nodes
visited_forbidden_nodes
```

### 12. 什么是 ticket field extraction issue

字段提取坏例表示：

```text
应该提取出来的工单字段没有提取正确。
```

例如：

```text
field order_id expected='ORDER1001' actual=None
```

这说明：

```text
订单号没有提取出来。
```

但分析时仍然要问：

```text
用户输入里真的有 ORDER1001 吗？
是否大小写、空格、符号影响了提取？
如果没有订单号，expected 是否应该要求追问？
```

### 13. 什么是 intent classification issue

意图识别坏例表示：

```text
用户意图被分错。
```

例如：

```text
expected=policy_question actual=ticket_request
```

这类问题很关键。

因为意图识别通常是 Agent 后续路线的入口。

如果入口错了，后面都可能错。

分析意图坏例时要问：

```text
用户表达是否模糊？
expected 是否合理？
关键词规则是否太宽？
规则顺序是否有问题？
是否需要增加澄清分支？
```

### 14. 什么是 regression action

regression action 可以理解为：

```text
修完后防止以后再坏的动作。
```

例如：

```text
Keep this case in the route eval suite and rerun route plus full suite after the graph change.
```

这句话表达的是：

```text
这个坏例不能只修一次就忘了。
它应该继续留在评测集里，作为回归保护。
```

坏例分析最终必须落到：

```text
以后怎么防止它再发生。
```

### 15. 为什么不是所有坏例都立刻改代码

bad case 出现后，可能有几种处理方式：

```text
1. 改代码
2. 改 expected
3. 改评测数据
4. 增加新样本
5. 调整优先级
6. 标记为暂不处理
7. 交给产品确认业务规则
```

如果 expected 错了，改代码反而会把正确系统改坏。

如果业务规则没定义清楚，开发者不应该凭感觉决定。

如果样本太极端但不重要，可能先标为 p2。

所以坏例分析需要判断：

```text
该采取哪种动作。
```

### 16. 什么是 synthetic 示例

synthetic 表示：

```text
人为构造的。
```

本节的：

```text
bad_case_analysis_sample.md
```

是 synthetic 示例。

它不是当前 Agent 的真实失败。

为什么要做 synthetic 示例？

因为当前真实评测是通过的：

```text
failed_suites: 0
bad_cases: 0
```

如果没有示例，你就看不到坏例分析报告长什么样。

但 synthetic 示例必须明确标注。

否则别人会误以为：

```text
当前项目真的有这些失败。
```

### 17. 为什么坏例分析可以先用规则分类

本节没有用 LLM 自动分析 bad case。

而是用规则分类。

原因是：

```text
当前 bad case 文本已经有明显结构。
```

例如：

```text
expected_path
actual_path
visited_forbidden_nodes
missing_sources
field_accuracy
```

这些关键词已经能粗略判断类别。

规则分类的优点：

```text
确定
便宜
可测试
不需要 API Key
不会引入模型不稳定
```

后续如果要做更复杂的根因分析，可以再引入 LLM 辅助。

---

## 二、本节主题系统讲解

### 1. 本节解决的真实问题

第 9 节报告能告诉你：

```text
有没有 bad cases。
```

第 10 节要进一步告诉你：

```text
bad cases 大概属于哪一类问题。
```

如果只是看到：

```text
Bad cases:
- agent_policy_refund_arrival_001 ...
```

你还需要人工判断：

```text
它是 RAG 问题？
是路由问题？
是字段提取问题？
是 expected 写错？
```

本节新增的分析模块先做第一层归类：

```text
intent_classification
ticket_field_extraction
agent_routing
rag_retrieval_or_citation
agent_decision_after_rag
unknown
```

这不是最终裁决。

它是：

```text
帮助你更快进入正确分析方向。
```

### 2. 本节新增后的整体链路

现在完整链路是：

```text
agent_cases.json
        |
        v
scripts/agent_eval.py
        |
        v
run_agent_eval_suites(...)
        |
        v
AgentEvalRunReport
        |
        +--> eval_report.py
        |       |
        |       v
        |    agent_eval_report.md
        |
        +--> bad_case_analysis.py
                |
                v
             agent_bad_case_analysis.md
             bad_case_analysis_sample.md
```

注意：

```text
bad_case_analysis.py 不重新运行 evaluator。
```

它读取的是：

```text
AgentEvalRunReport
```

也就是第 8 节已经生成的结构化运行结果。

### 3. 真实坏例分析报告

真实命令：

```powershell
uv run python scripts/agent_eval.py --cases-path data/agent_eval/agent_cases.json --bad-case-analysis-path data/agent_eval/reports/agent_bad_case_analysis.md
```

当前真实报告内容是：

```text
Failed suites: 0
Bad cases: 0
No bad cases to analyze.
```

这说明：

```text
当前评测集上没有真实坏例。
```

这不是坏事。

它说明当前阶段代码在这 12 条样本上仍然稳定。

### 4. synthetic 示例报告

示例文件：

```text
data/agent_eval/reports/bad_case_analysis_sample.md
```

它开头明确写了：

```text
This sample uses synthetic bad cases for Stage 6 lesson 10.
It is not a real failure report from the current Agent.
```

这句话很重要。

因为示例报告里有 3 个坏例：

```text
rag_retrieval_or_citation
agent_routing
ticket_field_extraction
```

它们只是教学样例。

不是当前项目真实失败。

### 5. BadCaseAnalysisItem 表达什么

新增模型：

```python
class BadCaseAnalysisItem(BaseModel):
```

它表示：

```text
一个坏例分析项。
```

主要字段：

```text
suite_name
suite_title
case_id
priority
category
likely_layer
diagnosis
recommended_action
regression_action
review_questions
evidence_lines
```

它不是原始 bad case。

它是在原始 bad case 基础上加了：

```text
分类
诊断
建议动作
回归动作
复盘问题
```

这就是从“失败输出”到“分析记录”的升级。

### 6. BadCaseAnalysisReport 表达什么

新增模型：

```python
class BadCaseAnalysisReport(BaseModel):
```

它表示：

```text
一次完整 Agent eval run 的坏例分析总报告。
```

主要字段：

```text
source_cases_path
failed_suite_count
bad_case_count
category_counts
items
```

其中：

```text
category_counts
```

能告诉你：

```text
坏例主要集中在哪类问题。
```

例如 synthetic 示例：

```text
agent_routing: 1
rag_retrieval_or_citation: 1
ticket_field_extraction: 1
```

### 7. analyze_agent_eval_bad_cases 的作用

函数：

```python
def analyze_agent_eval_bad_cases(run_report: AgentEvalRunReport) -> BadCaseAnalysisReport:
```

它的输入是：

```text
AgentEvalRunReport
```

输出是：

```text
BadCaseAnalysisReport
```

流程：

```text
1. 遍历每个 suite_report
2. 跳过已经 passed 的 suite
3. 跳过 No bad cases.
4. 拆分 bad case block
5. 对每个 block 做分类
6. 生成 BadCaseAnalysisItem
7. 汇总 category_counts
```

### 8. _split_bad_case_blocks 的作用

已有 bad case 文本结构大概是：

```text
Bad cases:
- case_001: ...
  expected_path: ...
  actual_path: ...
  - reason...
- case_002: ...
  - reason...
```

`_split_bad_case_blocks` 会把它拆成：

```text
block 1 = case_001 的所有行
block 2 = case_002 的所有行
```

注意：

```text
只有以 "- " 开头的行才算新 case。
```

以两个空格加 `-` 开头的是 reason：

```text
  - reason...
```

不能误判成新 case。

### 9. _classify_bad_case_category 的作用

这个函数根据 suite name 和 evidence 关键词做第一层分类。

例如：

```text
missing_sources
expected_sources
```

会分类为：

```text
rag_retrieval_or_citation
```

例如：

```text
expected_path
actual_path
visited_forbidden_nodes
```

会分类为：

```text
agent_routing
```

例如：

```text
field_accuracy
field order_id expected...
```

会分类为：

```text
ticket_field_extraction
```

这不是百分百根因。

它只是：

```text
根据证据进入最可能的分析方向。
```

### 10. _category_guidance 的作用

分类之后，还需要知道：

```text
这个类别应该怎么分析。
```

所以 `_category_guidance` 为每个类别提供：

```text
likely_layer
diagnosis
recommended_action
regression_action
review_questions
```

例如 `agent_routing`：

```text
likely_layer = Agent route graph
recommended_action = Compare expected_path and actual_path...
```

这能帮助你在报告里直接看到：

```text
下一步该查哪里。
```

### 11. build_bad_case_analysis_markdown_report 的作用

函数：

```python
build_bad_case_analysis_markdown_report(...)
```

负责把结构化分析结果生成 Markdown。

报告结构：

```text
# Agent Bad Case Analysis
## Overall
## Category Summary
## Analysis Items
```

如果没有坏例：

```text
No bad cases to analyze.
```

如果有坏例，每个 item 包含：

```text
Evidence
Diagnosis
Review Questions
Recommended Action
Regression Action
```

### 12. write_bad_case_analysis_markdown_report 的作用

函数：

```python
write_bad_case_analysis_markdown_report(...)
```

负责写文件。

它会：

```text
1. 创建父目录
2. 生成 Markdown
3. 用 UTF-8 写入
4. 返回路径
```

和第 9 节的报告写入设计保持一致。

### 13. scripts/agent_eval.py 新增了什么

第 10 节给脚本新增：

```text
--bad-case-analysis-path
```

示例：

```powershell
uv run python scripts/agent_eval.py --cases-path data/agent_eval/agent_cases.json --bad-case-analysis-path data/agent_eval/reports/agent_bad_case_analysis.md
```

脚本会：

```text
1. 运行 Agent eval suite
2. 得到 AgentEvalRunReport
3. 调用 analyze_agent_eval_bad_cases
4. 写入坏例分析 Markdown
5. 打印 bad_case_analysis 路径
```

### 14. 为什么不把 bad case 分析写进 eval_report.py

第 9 节的 `eval_report.py` 负责：

```text
评测结果报告。
```

第 10 节的 `bad_case_analysis.py` 负责：

```text
坏例分析报告。
```

这两个报告相关，但职责不同。

评测报告回答：

```text
评测结果是什么？
```

坏例分析回答：

```text
失败原因可能是什么，下一步怎么处理？
```

所以拆开更清楚。

### 15. 本节测试覆盖了什么

新增测试：

```text
tests/test_bad_case_analysis.py
```

覆盖：

```text
1. 当前真实全通过报告可以生成无坏例分析
2. RAG source failure 能归类为 rag_retrieval_or_citation
3. route failure 能归类为 agent_routing
4. field failure 能归类为 ticket_field_extraction
5. Markdown 包含 evidence、review questions、action
6. 写报告时能自动创建父目录
```

这些测试的重点是：

```text
分析逻辑可重复，可验证。
```

---

## 三、新增代码讲解

### 1. 新增 app/agents/bad_case_analysis.py

这个文件是本节核心。

它不运行 Agent。

不调用模型。

不重新做 eval。

它只做：

```text
读取 AgentEvalRunReport 里的 bad_case_lines，生成坏例分析。
```

这符合工程分层：

```text
eval_suite.py 负责跑评测
eval_report.py 负责评测报告
bad_case_analysis.py 负责坏例分析
```

### 2. BadCaseAnalysisItem

代码：

```python
class BadCaseAnalysisItem(BaseModel):
```

用 Pydantic 是因为它是结构化数据。

字段里最重要的是：

```text
category
likely_layer
diagnosis
recommended_action
regression_action
evidence_lines
```

其中：

```text
evidence_lines
```

保留原始坏例证据。

这很重要。

因为分析报告不能只给结论。

必须能回到原始证据。

### 3. BadCaseAnalysisReport

这个模型是总报告。

它包含：

```text
bad_case_count
category_counts
items
```

`category_counts` 可以帮助你从整体上看：

```text
坏例集中在哪里。
```

如果 10 个坏例里 8 个都是：

```text
rag_retrieval_or_citation
```

那你就不应该优先改工单字段提取。

应该先看 RAG。

### 4. 正则解析 case_id 和 priority

代码里有：

```python
_CASE_HEADER_RE = re.compile(r"^- (?P<case_id>[^:]+):")
_PRIORITY_RE = re.compile(r"\bpriority=(?P<priority>p[0-2])\b")
```

这是用正则从文本里提取：

```text
case_id
priority
```

例如：

```text
- agent_policy_refund_arrival_001: expected_status=answered actual_status=answered priority=p0
```

提取结果：

```text
case_id = agent_policy_refund_arrival_001
priority = p0
```

### 5. analyze_agent_eval_bad_cases

核心流程：

```python
for suite_report in run_report.suite_reports:
    if suite_report.passed or _has_no_bad_cases(...):
        continue
    for evidence_lines in _split_bad_case_blocks(...):
        items.append(_analyze_bad_case_block(...))
```

这段表达的是：

```text
只分析失败 suite 里的真实 bad cases。
```

如果 suite 已通过，就不用分析。

如果 bad_case_lines 是：

```text
No bad cases.
```

也不用分析。

### 6. _split_bad_case_blocks

这个函数处理文本块拆分。

它的核心判断是：

```python
if line.startswith("- "):
```

这代表新的 bad case 开始。

缩进行：

```text
  - reason
```

不会被当成新 case。

这就是根据已有格式做的轻量解析。

### 7. _classify_bad_case_category

这个函数根据关键词归类。

例如：

```python
if "missing_sources" in normalized:
    return "rag_retrieval_or_citation"
```

它不是 AI 判断。

是规则判断。

规则判断的好处是：

```text
可预测
可测试
不耗 token
不需要 API Key
```

当前阶段这比 LLM 自动分析更合适。

### 8. _category_guidance

这个函数是本节教学价值很高的地方。

它把类别映射到：

```text
可能层
诊断说明
建议动作
回归动作
复盘问题
```

例如 `rag_retrieval_or_citation` 会提示你：

```text
先检查知识库、chunk、source metadata、retrieval threshold 和 citation mapping。
```

这能避免你看到 RAG 坏例后马上乱改 Agent 路由。

### 9. build_bad_case_analysis_markdown_report

这个函数生成 Markdown。

无坏例时：

```text
No bad cases to analyze.
```

有坏例时：

```text
Category Summary
Analysis Items
Evidence
Diagnosis
Review Questions
Recommended Action
Regression Action
```

这就是一个坏例分析记录应该有的基本结构。

### 10. write_bad_case_analysis_markdown_report

这个函数负责写文件。

它和第 9 节的写报告函数保持一致：

```python
report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(..., encoding="utf-8")
```

还是同一个原则：

```text
写文本明确 UTF-8。
```

### 11. scripts/agent_eval.py 的改动

新增导入：

```python
from app.agents.bad_case_analysis import (
    analyze_agent_eval_bad_cases,
    write_bad_case_analysis_markdown_report,
)
```

新增参数：

```python
--bad-case-analysis-path
```

新增流程：

```python
if args.bad_case_analysis_path is not None:
    analysis = analyze_agent_eval_bad_cases(report)
    analysis_path = write_bad_case_analysis_markdown_report(...)
```

这样你可以一次运行评测，同时生成：

```text
评测报告
坏例分析报告
```

例如：

```powershell
uv run python scripts/agent_eval.py --cases-path data/agent_eval/agent_cases.json --report-path data/agent_eval/reports/agent_eval_report.md --bad-case-analysis-path data/agent_eval/reports/agent_bad_case_analysis.md
```

### 12. tests/test_bad_case_analysis.py

测试里构造了 fake 失败报告。

原因是：

```text
当前真实评测全部通过。
```

如果只测真实评测，就测不到：

```text
RAG 坏例
路由坏例
字段坏例
FAIL 分析报告
```

所以用 fake report 是合理的。

注意：

```text
fake report 只在测试和 synthetic 示例里使用。
```

它不污染真实评测结果。

---

## 四、本节运行结果

运行真实坏例分析：

```powershell
uv run python scripts/agent_eval.py --cases-path data/agent_eval/agent_cases.json --bad-case-analysis-path data/agent_eval/reports/agent_bad_case_analysis.md
```

核心输出：

```text
failed_suites: 0
passed: true
bad_case_analysis: data\agent_eval\reports\agent_bad_case_analysis.md
```

真实坏例分析报告：

```text
Source cases path: data\agent_eval\agent_cases.json
Failed suites: 0
Bad cases: 0
No bad cases to analyze.
```

示例坏例分析报告：

```text
data/agent_eval/reports/bad_case_analysis_sample.md
```

它包含 3 个 synthetic 示例分类：

```text
rag_retrieval_or_citation
agent_routing
ticket_field_extraction
```

运行新增测试：

```powershell
uv run pytest tests/test_bad_case_analysis.py -q
```

结果：

```text
5 passed
```

---

## 五、怎么阅读坏例分析报告

### 1. 先看 Overall

如果看到：

```text
Bad cases: 0
```

说明当前没有坏例需要分析。

如果看到：

```text
Bad cases: 3
```

说明下面会有具体分析项。

### 2. 再看 Category Summary

Category Summary 告诉你：

```text
坏例集中在哪些类别。
```

例如：

```text
rag_retrieval_or_citation: 1
agent_routing: 1
ticket_field_extraction: 1
```

这比直接看一堆 bad case 更清楚。

### 3. 再看每个 Analysis Item

每个 item 都有：

```text
suite / case_id
priority
category
likely layer
```

你应该先确定：

```text
这是哪条样本，属于哪层问题。
```

### 4. 看 Evidence

Evidence 是原始证据。

不要跳过。

分析必须从证据出发。

如果 evidence 是：

```text
expected_path: ...
actual_path: ...
visited_forbidden_nodes=...
```

那你应该优先看路由分叉点。

### 5. 看 Review Questions

Review Questions 是复盘问题。

它们不是最终答案。

它们的作用是帮你避免直接拍脑袋。

例如：

```text
Should the expected route change, or is the graph decision wrong?
```

这提醒你：

```text
先判断 expected 是否正确。
```

### 6. 看 Recommended Action

Recommended Action 是建议下一步。

它告诉你：

```text
应该优先查哪里。
```

不是说一定照做。

但它能让分析有方向。

### 7. 看 Regression Action

Regression Action 告诉你：

```text
修完后怎么防止再坏。
```

如果一个坏例被修复后没有进入回归保护，那么以后很可能再次出现。

---

## 六、常见误区

### 误区 1：bad case 一定是代码 bug

不是。

bad case 只表示：

```text
actual 和 expected 不一致。
```

可能是代码错。

也可能是 expected 错。

### 误区 2：看到坏例就马上改代码

不应该。

先分析：

```text
expected 是否正确
数据是否合理
第一分叉点在哪里
影响范围有多大
```

然后再决定改什么。

### 误区 3：只看指标不看 bad case

指标告诉你：

```text
坏了多少。
```

bad case 告诉你：

```text
为什么坏。
```

AI 应用调优不能只看指标。

### 误区 4：只修当前样本

只修当前样本可能导致过拟合。

你还要想：

```text
有没有相邻表达？
有没有反例？
会不会影响其他 intent？
```

### 误区 5：synthetic 示例可以不标注

不行。

synthetic 示例必须明确标注。

否则别人会误以为它是真实失败报告。

### 误区 6：自动分类就是最终根因

不是。

本节规则分类只是第一层分析辅助。

最终根因仍然需要结合代码、数据、业务预期判断。

### 误区 7：当前没有坏例就不用学坏例分析

不对。

当前样本集通过，不代表以后不会失败。

坏例分析是你后续接真实模型、真实 RAG、真实工具时必须掌握的能力。

---

## 七、本节练习

### 练习 1：生成真实坏例分析报告

题目：

在 `projects/ai-service` 目录下，生成当前真实 Agent eval 的坏例分析报告，命令是什么？

参考答案：

```powershell
uv run python scripts/agent_eval.py --cases-path data/agent_eval/agent_cases.json --bad-case-analysis-path data/agent_eval/reports/agent_bad_case_analysis.md
```

当前真实结果应该是：

```text
Bad cases: 0
No bad cases to analyze.
```

### 练习 2：解释 synthetic 示例的作用

题目：

为什么本节要保留 `bad_case_analysis_sample.md`？

参考答案：

因为当前真实评测全部通过，没有真实 bad case。

为了学习坏例分析报告长什么样，需要构造一个明确标注为 synthetic 的示例。

它用于教学，不代表当前 Agent 真实失败。

### 练习 3：区分 bad case 和 bug

题目：

bad case 是否一定是 bug？

参考答案：

不一定。

bad case 表示 actual 和 expected 不一致。

如果 expected 写错了，那应该改 expected 或数据集，而不是改代码。

### 练习 4：分析 RAG source 坏例

题目：

看到下面证据时，你应该优先怀疑哪一层？

```text
expected_sources: ['refund-return-policy.md']
actual_sources: ['account-security-faq.md']
missing_sources=['refund-return-policy.md']
```

参考答案：

优先怀疑：

```text
RAG retrieval or citation
```

应该检查知识库文档、chunk、query、top_k、score_threshold、source metadata 和 citation mapping。

### 练习 5：分析路由坏例

题目：

看到 expected_path 和 actual_path 前面都一样，但 actual_path 后面多走了 `extract_ticket_fields`，应该优先检查哪里？

参考答案：

应该优先检查路径第一次分叉的位置。

如果多走发生在 `decide_ticket_need` 之后，就优先检查：

```text
decide_ticket_need
```

不要先去怀疑 classify_intent 或 retrieve_policy。

### 练习 6：解释 regression action

题目：

什么是 regression action？

参考答案：

regression action 是修复坏例后防止再次退化的动作。

例如保留该 case 在 eval suite 里，修复后 rerun 对应 suite 和完整 suite。

### 练习 7：为什么测试里要构造 fake 失败报告

题目：

当前真实评测全部通过，为什么测试里还要构造 fake 失败报告？

参考答案：

因为坏例分析逻辑必须在失败场景下也可验证。

如果只测真实通过场景，就无法测试分类、FAIL 报告、review questions 和 recommended action。

### 练习 8：什么时候不应该改代码

题目：

出现 bad case 后，哪些情况下不应该立刻改代码？

参考答案：

包括：

```text
expected 本身错了
样本输入不合理
业务规则没定义清楚
优先级不高且影响范围不明确
失败是评测口径变化导致的
```

这时应先修 expected、修数据集、找业务确认，或补充样本和说明。

---

## 八、自测题

### 自测 1：坏例分析的第一步是什么？

参考答案：

第一步是确认 expected 是否合理，并阅读原始 evidence。

不能直接假设代码错了。

### 自测 2：什么是第一分叉点？

参考答案：

第一分叉点是 actual 链路第一次偏离 expected 链路的位置。

它通常指向最值得优先检查的节点或决策。

### 自测 3：为什么 `missing_sources` 通常指向 RAG retrieval/citation 问题？

参考答案：

因为它说明预期来源没有出现在实际引用来源里。

可能是检索没找回，也可能是 citation 映射丢失或错映射。

### 自测 4：为什么字段提取坏例不一定要直接补规则？

参考答案：

因为要先判断用户输入里是否真的包含该字段。

如果字段没有明确出现，Agent 可能应该追问，而不是猜测。

### 自测 5：为什么坏例要变成回归样本？

参考答案：

因为修复一次不代表以后不会再坏。

把坏例保留在评测集里，可以防止后续改动把旧问题重新引入。

### 自测 6：本节为什么不用 LLM 自动分析坏例？

参考答案：

因为当前 bad case 文本结构明确，用规则分类更确定、便宜、可测试，也不需要 API Key。

等人工分析方法扎实后，再考虑 LLM 辅助。

### 自测 7：真实坏例分析报告显示 0 个坏例说明什么？

参考答案：

说明当前 12 条评测样本在 intent、field、route、rag 四个 suite 上全部通过。

它不说明系统永远没有问题，只说明当前评测集没有发现问题。

### 自测 8：synthetic 示例报告为什么必须明确标注？

参考答案：

因为 synthetic 示例是人为构造的教学样例。

如果不标注，别人可能误以为它是当前 Agent 的真实失败报告。

---

## 九、本节你应该形成的表达能力

学完本节后，你应该能这样说明：

```text
第 10 节学习的是坏例分析。bad case 不等于 bug，它只表示 actual 和 expected 不一致。
分析坏例时要先看 expected 是否合理，再看 evidence，找到第一分叉点，然后判断失败来自意图识别、字段提取、Agent 路由、RAG 检索/引用、RAG 后决策，还是数据集或 expected 本身。
本节新增 bad_case_analysis.py，把 AgentEvalRunReport 里的 bad_case_lines 拆成分析项，并生成 Markdown 坏例分析报告。
当前真实评测没有坏例，所以 agent_bad_case_analysis.md 显示 No bad cases to analyze。
为了教学，bad_case_analysis_sample.md 使用 synthetic bad cases 展示失败时如何分类、诊断、提出 review questions、recommended action 和 regression action。
```

如果别人问你：

```text
坏例出现后第一件事是不是改代码？
```

你应该回答：

```text
不是。第一件事是确认 expected 和样本是否合理，并定位第一分叉点。只有确认是实现问题后才改代码。
```

如果别人问你：

```text
为什么坏例分析对 AI 应用重要？
```

你应该回答：

```text
因为 AI 应用的失败来源很多，可能来自意图、字段、RAG、工具、路由、prompt、模型、数据集或业务预期。只看 pass rate 不够，必须分析 bad cases 才能知道怎么改。
```

---

## 十、本节小结

本节完成了从：

```text
发现 bad cases
```

到：

```text
分析 bad cases
```

的第一步。

新增：

```text
app/agents/bad_case_analysis.py
tests/test_bad_case_analysis.py
data/agent_eval/reports/agent_bad_case_analysis.md
data/agent_eval/reports/bad_case_analysis_sample.md
```

增强：

```text
scripts/agent_eval.py --bad-case-analysis-path
```

本节你真正要掌握的是：

```text
bad case 是 AI 应用持续改进的入口，不只是失败列表。
```

下一节是：

```text
阶段 6 第 11 节：回归评测
```

我们会学习：

```text
修完坏例后，如何系统防止旧能力退化。
```

---

## 十一、参考资料

- [LangSmith Evaluation concepts](https://docs.langchain.com/langsmith/evaluation-concepts)
  - 用途：理解 AI 应用评测为什么要把“好”拆成可衡量标准，以及 offline evaluation、online evaluation、dataset、example、evaluator、experiment 的关系。

- [OpenAI Evals guide](https://developers.openai.com/api/docs/guides/evals)
  - 用途：辅助理解 eval 的目标是系统化衡量模型或应用行为，而不是临时试问几次。

- [GitHub Actions artifacts](https://docs.github.com/en/actions/tutorials/store-and-share-data)
  - 用途：理解后续 CI 中评测报告和坏例分析报告可以作为 workflow artifact 保存，方便下载和复盘。
