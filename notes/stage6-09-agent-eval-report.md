# 阶段 6 第 9 节：评测报告

## 本节定位

第 8 节我们完成了统一评测入口：

```powershell
uv run python scripts/agent_eval.py
```

它可以一次运行：

```text
intent
field
route
rag
```

并输出：

```text
Overall
suites: 4
passed_suites: 4
failed_suites: 0
passed: true
```

这已经能回答：

```text
当前 Agent 整体评测是否通过？
```

但第 8 节还有一个问题：

```text
终端输出看完就过去了，不方便保存、回看、复盘和分享。
```

所以第 9 节学习：

```text
评测报告
```

本节新增的能力是：

```text
把 AgentEvalRunReport 生成 Markdown 报告文件。
```

新增文件：

```text
app/agents/eval_report.py
tests/test_agent_eval_report.py
data/agent_eval/reports/agent_eval_report.md
```

同时增强：

```text
scripts/agent_eval.py
```

新增参数：

```text
--report-path
```

现在可以这样运行：

```powershell
uv run python scripts/agent_eval.py --cases-path data/agent_eval/agent_cases.json --report-path data/agent_eval/reports/agent_eval_report.md
```

运行后会生成：

```text
data/agent_eval/reports/agent_eval_report.md
```

本节不需要打开 VMware。

不需要 Docker。

不需要 Qdrant。

不需要 Milvus。

也不会真实调用大模型。

---

## 本节学习目标

学完本节，你应该能解释清楚：

1. 什么是评测报告。
2. 评测报告和终端输出有什么区别。
3. 为什么报告不是简单把终端输出复制到文件。
4. 为什么本节先做 Markdown 报告。
5. Markdown 报告和 JSON 报告分别适合什么场景。
6. 一个 Agent 评测报告应该包含哪些基本信息。
7. 什么是 Overall、Suite Summary、Summary、Bad Cases。
8. 为什么报告里要有 PASS/FAIL。
9. 为什么报告路径要稳定。
10. 为什么报告生成逻辑要从 `agent_eval.py` 里拆出来。
11. `build_agent_eval_markdown_report()` 做什么。
12. `write_agent_eval_markdown_report()` 做什么。
13. 为什么写文件要指定 UTF-8。
14. 以后 CI 为什么会需要 report artifact。

---

## 本节先不学什么

本节暂时不学：

```text
1. JSON 评测报告落盘
2. HTML 报告
3. 图表
4. 历史趋势对比
5. 多次运行的 diff
6. LangSmith experiment report
7. GitHub Actions 上传 artifact 的完整配置
8. 线上评测报告
```

原因是：

```text
先把本地 Markdown 报告做清楚。
```

如果本地报告结构都还没想清楚，直接做 JSON、HTML、图表和 CI，反而容易变成：

```text
格式很多，重点不清。
```

本节先解决：

```text
一次评测结果应该怎样变成一份能读、能保存、能复盘的报告。
```

---

## 一、基础知识铺垫

### 1. 什么是评测报告

评测报告可以理解为：

```text
一次评测运行结果的结构化记录。
```

它不是模型回答。

不是测试代码。

也不是业务接口返回。

它记录的是：

```text
这次评测跑了什么？
用的哪份数据？
哪些 suite 参与？
整体是否通过？
每个 suite 是否通过？
关键指标是多少？
有哪些 bad cases？
```

第 8 节的终端输出回答的是：

```text
现在屏幕上看到什么？
```

第 9 节的报告回答的是：

```text
以后回看这次评测时，应该看到什么？
```

这是两个不同层次。

### 2. 评测报告和终端输出的区别

终端输出适合：

```text
开发者当前立刻看结果。
```

报告文件适合：

```text
保存
回看
提交到仓库
发给别人
放进 CI artifact
做阶段复盘
```

终端输出强调：

```text
快速
直接
短平快
```

报告强调：

```text
结构
可读
可保存
可复盘
```

所以报告不能只是：

```text
把 print 的内容原封不动写入文件。
```

本节报告会重新组织成：

```text
1. 标题
2. Overall 总览
3. Suite Summary 总表
4. 每个 suite 的详细摘要
5. 每个 suite 的 Bad Cases
```

### 3. 为什么 AI 应用更需要评测报告

普通后端接口通常可以靠单元测试和集成测试说明：

```text
这个输入应该得到这个输出。
```

AI 应用更复杂。

因为它可能涉及：

```text
意图识别
字段提取
工具调用
RAG 检索
Agent 路由
模型输出稳定性
安全边界
```

这些质量问题不一定能靠一条测试断言讲明白。

评测报告能把多个维度放到一起：

```text
intent accuracy
field accuracy
route pass rate
source recall
bad cases
overall status
```

这样你才能真正看出：

```text
Agent 到底强在哪里，弱在哪里。
```

### 4. 什么是 Markdown

Markdown 是一种轻量文本格式。

你写：

```markdown
# 标题

## 小标题

| 字段 | 值 |
| --- | --- |
| Status | PASS |
```

在 GitHub 或很多编辑器里会渲染成清楚的标题和表格。

Markdown 的优点是：

```text
1. 本质还是普通文本
2. Git diff 友好
3. GitHub 可以直接预览
4. 写起来简单
5. 学习成本低
```

这很适合作为本阶段第一版评测报告。

### 5. 什么是 Markdown 表格

Markdown 表格通常长这样：

```markdown
| Item | Value |
| --- | --- |
| Status | PASS |
| Suite count | 4 |
```

第一行是表头。

第二行是分隔。

后面是数据行。

表格适合展示：

```text
key-value 总览
多个 suite 的对比
状态和数量
```

本节报告用了两个表格：

```text
Overall 表
Suite Summary 表
```

### 6. 什么是代码块

Markdown 代码块通常这样写：

````markdown
```text
Agent intent evaluation summary
cases: 12
passed_cases: 12
```
````

代码块的好处是：

```text
保留原始文本格式。
```

本节把每个 suite 原来的 summary 和 bad cases 放进代码块。

这样做是因为：

```text
这些内容原本就是稳定的行文本。
```

放进代码块后不会被 Markdown 表格或列表错误解析。

### 7. Markdown 报告和 JSON 报告的区别

Markdown 报告适合人看。

JSON 报告适合程序读。

Markdown 报告更像：

```text
给开发者、学习者、面试复盘看的报告。
```

JSON 报告更像：

```text
给 CI、监控系统、趋势分析脚本读取的数据。
```

简单对比：

```text
Markdown：可读性强，适合 GitHub 展示
JSON：结构严格，适合机器解析
```

本节先做 Markdown。

以后可以在同一个 `AgentEvalRunReport` 基础上继续生成 JSON。

这就是为什么第 8 节先有结构化 report 对象。

### 8. 什么是 Overall

Overall 是整体总览。

它回答：

```text
这次完整评测整体是否通过？
```

本节报告里的 Overall 包含：

```text
Status
Cases path
Suites
Suite count
Passed suites
Failed suites
```

其中最重要的是：

```text
Status
Failed suites
```

如果：

```text
Status = PASS
Failed suites = 0
```

表示这次评测整体通过。

如果：

```text
Status = FAIL
Failed suites > 0
```

表示至少一个评测套件失败。

### 9. 什么是 Suite Summary

Suite Summary 是评测套件总表。

它把每个 suite 放在同一张表里：

```text
intent
field
route
rag
```

展示：

```text
suite 名称
标题
case 数
失败 case 数
状态
```

这样你不用翻每个详细段落，就能先知道：

```text
哪个 suite 坏了。
```

### 10. 什么是 Summary

Summary 是某个 suite 自己的摘要。

例如 intent suite：

```text
Agent intent evaluation summary
cases: 12
passed_cases: 12
failed_cases: 0
accuracy: 1.0000
```

它回答：

```text
这个 suite 内部的关键指标是多少？
```

不同 suite 的 Summary 字段不完全一样。

例如：

```text
intent 有 accuracy
field 有 field_accuracy
route 有 route_pass_rate
rag 有 source_recall
```

所以本节没有强行把所有指标塞进一张大表。

而是：

```text
总表只放共性字段；
详细 Summary 保留 suite 自己的指标。
```

这是一个重要设计。

### 11. 什么是 Bad Cases

Bad Cases 是坏例列表。

它回答：

```text
哪些样本没有通过，为什么没有通过？
```

如果所有样本都通过，当前输出是：

```text
No bad cases.
```

以后如果某个 suite 失败，报告里会保留该 suite 的坏例详情。

坏例是 AI 评测里非常重要的内容。

因为指标只能告诉你：

```text
有问题。
```

坏例才能帮助你分析：

```text
问题具体在哪里。
```

### 12. 为什么报告里要有 PASS/FAIL

数字很多时，人很容易看漏。

例如：

```text
failed_suites: 0
```

当然能说明通过。

但报告里直接显示：

```text
Status | PASS
```

会更直观。

失败时显示：

```text
Status | FAIL
```

也能立刻提醒读者。

这不是装饰。

这是报告可读性设计。

### 13. 什么是报告路径

报告路径就是报告文件保存在哪里。

本节选择：

```text
projects/ai-service/data/agent_eval/reports/agent_eval_report.md
```

相对于 `projects/ai-service`，命令里写：

```text
data/agent_eval/reports/agent_eval_report.md
```

为什么放在 `data/agent_eval/reports/`？

因为这份报告属于：

```text
Agent eval 数据和运行结果。
```

它和：

```text
data/agent_eval/agent_cases.json
```

关系很近。

所以放在同一个主题目录下更清楚。

### 14. 为什么报告路径要稳定

如果每次报告路径都不一样：

```text
report1.md
report-final.md
new-report.md
tmp.md
```

以后就很难找。

稳定路径的好处是：

```text
1. 文档可以固定链接
2. README 可以固定引用
3. CI 可以固定上传
4. 学习复盘可以固定查看
```

本节用：

```text
data/agent_eval/reports/agent_eval_report.md
```

作为当前学习版固定报告路径。

### 15. 什么是 report artifact

artifact 可以理解为：

```text
一次自动化运行产生的文件产物。
```

以后如果接 GitHub Actions，CI 可能会运行：

```powershell
uv run python scripts/agent_eval.py --report-path data/agent_eval/reports/agent_eval_report.md
```

然后把生成的 Markdown 报告作为 artifact 上传。

这样即使 CI 运行在远程机器上，你也能下载报告看：

```text
到底哪个 suite 失败？
失败样本是什么？
指标是多少？
```

本节不配置 CI。

但报告文件能力就是 artifact 的前置基础。

### 16. 为什么写文件要指定 UTF-8

本节代码：

```python
report_path.write_text(
    build_agent_eval_markdown_report(report),
    encoding="utf-8",
)
```

这里显式写：

```text
encoding="utf-8"
```

原因是：

```text
项目里有中文笔记和中文业务样本。
```

如果不指定编码，不同系统默认编码可能不一样。

Windows 上尤其容易出现中文显示问题。

所以学习项目里写文本文件时，应该尽量明确：

```text
用 UTF-8 写入。
```

如果你在 PowerShell 里看到中文乱码，第一反应仍然应该是：

```text
很可能是 PowerShell 输出编码显示问题。
```

不要直接大规模改文件。

### 17. 为什么报告生成逻辑不能放进脚本里

第 8 节已经讲过：

```text
脚本入口要薄。
```

第 9 节继续保持这个原则。

`scripts/agent_eval.py` 只增加：

```python
--report-path
write_agent_eval_markdown_report(...)
```

真正的 Markdown 生成在：

```text
app/agents/eval_report.py
```

这样做有好处：

```text
1. 报告生成逻辑可以单独测试
2. 脚本仍然清楚
3. 以后生成 JSON/HTML 报告时可以继续扩展模块
4. 不会让 agent_eval.py 变成大杂烩
```

### 18. 什么是从结构化对象生成报告

本节不是从终端文本反向解析报告。

而是从：

```text
AgentEvalRunReport
```

直接生成 Markdown。

这是关键。

不要做：

```text
先 print
再抓取 print 内容
再写文件
```

这样会很脆弱。

本节做的是：

```text
run_agent_eval_suites
-> AgentEvalRunReport
-> format_agent_eval_run_report 生成终端输出
-> build_agent_eval_markdown_report 生成 Markdown 报告
```

同一个结构化对象，可以生成不同展示形式。

这就是更好的设计。

---

## 二、本节主题系统讲解

### 1. 本节前后的能力变化

第 8 节后：

```powershell
uv run python scripts/agent_eval.py
```

你能在终端看到完整评测。

第 9 节后：

```powershell
uv run python scripts/agent_eval.py --cases-path data/agent_eval/agent_cases.json --report-path data/agent_eval/reports/agent_eval_report.md
```

你不仅能看到终端输出，还能得到：

```text
data/agent_eval/reports/agent_eval_report.md
```

这就是能力变化：

```text
从“一次性查看”变成“可保存报告”。
```

### 2. 本节新增后的运行链路

完整链路现在是：

```text
scripts/agent_eval.py
        |
        v
run_agent_eval_suites(...)
        |
        v
AgentEvalRunReport
        |
        +--> format_agent_eval_run_report(...)
        |       |
        |       v
        |    终端输出
        |
        +--> build_agent_eval_markdown_report(...)
                |
                v
             Markdown 文本
                |
                v
             write_text(..., encoding="utf-8")
                |
                v
             data/agent_eval/reports/agent_eval_report.md
```

你要特别注意：

```text
终端输出和 Markdown 报告是同源的。
```

它们都来自：

```text
AgentEvalRunReport
```

不是互相解析。

### 3. eval_report.py 的职责

新增文件：

```text
app/agents/eval_report.py
```

它负责：

```text
把 AgentEvalRunReport 变成 Markdown 报告。
```

它不负责：

```text
加载数据集
运行 evaluator
解析命令行参数
决定 exit code
```

这些职责已经分别属于：

```text
intent_evaluation.py / field_evaluation.py / route_evaluation.py / rag_agent_evaluation.py
eval_suite.py
scripts/agent_eval.py
```

`eval_report.py` 的定位很清楚：

```text
报告生成层。
```

### 4. build_agent_eval_markdown_report 的设计

函数：

```python
def build_agent_eval_markdown_report(report: AgentEvalRunReport) -> str:
```

输入：

```text
AgentEvalRunReport
```

输出：

```text
Markdown 字符串
```

它不写文件。

只构造内容。

这样测试时可以直接：

```python
markdown = build_agent_eval_markdown_report(report)
assert "## Overall" in markdown
```

不用真的操作文件系统。

这让测试更简单。

### 5. write_agent_eval_markdown_report 的设计

函数：

```python
def write_agent_eval_markdown_report(report, path) -> Path:
```

输入：

```text
AgentEvalRunReport
报告路径
```

做的事：

```text
1. 创建父目录
2. 生成 Markdown
3. 用 UTF-8 写入文件
4. 返回写入路径
```

代码里有：

```python
report_path.parent.mkdir(parents=True, exist_ok=True)
```

这表示：

```text
如果 reports 目录不存在，就自动创建。
```

这对命令行脚本很友好。

用户不需要手动先建目录。

### 6. _markdown_table 的设计

本节新增：

```python
def _markdown_table(headers: list[str], rows: list[list[str]]) -> list[str]:
```

它负责生成 Markdown 表格。

为什么要单独写函数？

因为报告里不止一个表：

```text
Overall 表
Suite Summary 表
```

如果每个表都手写字符串拼接，重复会变多。

这个函数把表格生成规则集中起来。

### 7. _table_cell 的设计

函数：

```python
def _table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")
```

它处理 Markdown 表格里的特殊字符。

表格列之间用：

```text
|
```

分隔。

如果单元格内容本身包含 `|`，表格就可能被破坏。

所以这里把 `|` 转义成：

```text
\|
```

如果单元格里有换行，就改成：

```text
<br>
```

当前报告数据很简单，但这个函数是一个小防护。

### 8. _status_label 的设计

函数：

```python
def _status_label(passed: bool) -> str:
    return "PASS" if passed else "FAIL"
```

它把布尔值转成报告里的人类可读状态。

代码里不用到处写：

```python
"PASS" if passed else "FAIL"
```

而是集中到一个函数里。

这样以后如果想改成：

```text
PASSED / FAILED
```

只改一个地方。

### 9. agent_eval.py 新增了什么

第 9 节修改了：

```text
scripts/agent_eval.py
```

新增参数：

```python
parser.add_argument(
    "--report-path",
    type=Path,
    help="Write a Markdown evaluation report to this path.",
)
```

意思是：

```text
用户可以选择把评测报告写到指定路径。
```

如果不传：

```text
只打印终端输出。
```

如果传：

```text
打印终端输出，并额外写 Markdown 文件。
```

这样保留了兼容性。

### 10. 为什么 --report-path 是可选的

如果默认每次都写报告，可能会带来问题：

```text
1. 临时运行也会改文件
2. 工作区经常出现不必要的 diff
3. 初学者可能不清楚文件为什么变了
```

所以本节设计为：

```text
只有显式传 --report-path 时才写报告。
```

这符合一个原则：

```text
会修改文件的行为，最好显式触发。
```

### 11. 为什么这次生成一份样例报告

虽然 `--report-path` 是可选的，但本节仍然生成了一份样例：

```text
data/agent_eval/reports/agent_eval_report.md
```

原因是：

```text
你是在学习，不只是写工具。
```

保留样例报告能帮助你：

```text
1. 直接打开看报告长什么样
2. 对照笔记理解报告结构
3. 以后回看第 9 节时不需要重新运行
4. GitHub 首页可以链接到具体产物
```

在真实生产项目里，是否提交生成报告要看团队规则。

在当前学习项目里，保留一份稳定样例是合理的。

### 12. 报告为什么不包含时间戳

你可能会想：

```text
报告是不是应该有 generated_at？
```

生产报告可以有。

但本节暂时没有加入时间戳。

原因是：

```text
时间戳会导致每次运行都产生 diff。
```

当前学习项目更需要稳定、可重复的报告。

所以先不加时间戳。

以后如果要保留历史报告，可以使用：

```text
reports/2026-07-24-agent-eval.md
reports/latest.md
```

这种策略。

但那是后续内容。

### 13. 报告为什么不直接写中文标题

当前生成报告标题是：

```text
Agent Evaluation Report
```

suite 标题也是英文：

```text
Intent evaluation
Ticket field evaluation
Agent route evaluation
RAG + Agent evaluation
```

原因是：

```text
这些标题来自代码里的 suite title。
```

代码层保持英文，有利于：

```text
1. 变量和函数命名一致
2. 日志、CI、脚本输出更通用
3. 避免中英文混杂导致编码误判
```

学习笔记用中文讲解。

工程脚本输出可以保持英文。

这是当前项目一贯风格。

### 14. 报告为什么保留原始 summary_lines

每个 evaluator 已经有自己的格式化函数：

```text
format_intent_eval_summary
format_ticket_field_eval_summary
format_agent_route_eval_summary
format_rag_agent_eval_summary
```

本节没有重新发明这些 summary。

而是复用：

```text
summary_lines
bad_case_lines
```

这样做的好处是：

```text
1. 不重复实现指标展示
2. 保持终端输出和报告细节一致
3. 新增 evaluator 时，只要提供格式化函数即可接入
```

报告层只负责组织结构，不负责重新定义每个指标。

### 15. 本节测试覆盖了什么

新增测试：

```text
tests/test_agent_eval_report.py
```

主要覆盖：

```text
1. Markdown 是否包含标题
2. 是否包含 Overall
3. 是否包含 PASS
4. 是否包含 Suite Summary
5. 是否包含每个 suite 的详情段
6. 是否包含 summary 代码块
7. 是否包含 bad cases 代码块
8. 失败报告是否显示 FAIL
9. 写报告时是否能创建父目录
10. 写出的文件是否能用 UTF-8 读取
```

这些测试保护的是报告结构。

不是测试 Markdown 渲染器。

### 16. 本节和第 10 节的关系

第 9 节做的是：

```text
评测报告怎么生成。
```

第 10 节会学：

```text
坏例分析。
```

也就是：

```text
当报告里真的出现 bad cases 时，应该如何判断原因。
```

所以第 9 节偏输出结构。

第 10 节偏问题分析方法。

---

## 三、新增代码讲解

### 1. 新增 app/agents/eval_report.py

这个文件是报告生成模块。

它导入：

```python
from pathlib import Path

from app.agents.eval_suite import AgentEvalRunReport, AgentEvalSuiteReport
```

说明它基于第 8 节的结构化报告对象工作。

它不导入具体 evaluator。

这点很重要。

因为报告模块不应该关心：

```text
intent 怎么评
field 怎么评
route 怎么评
rag 怎么评
```

它只关心：

```text
给我 AgentEvalRunReport，我生成 Markdown。
```

### 2. build_agent_eval_markdown_report

核心函数：

```python
def build_agent_eval_markdown_report(report: AgentEvalRunReport) -> str:
```

它先创建标题：

```python
lines = [
    "# Agent Evaluation Report",
    "",
    "## Overall",
    "",
]
```

这里用 `lines` 列表，而不是直接不断拼接字符串。

原因是：

```text
多行文本用 list 收集，最后 join，更清晰。
```

最后：

```python
return "\n".join(lines).rstrip() + "\n"
```

这保证报告末尾有一个换行。

文本文件末尾保留换行是常见习惯。

### 3. Overall 表如何生成

代码使用：

```python
_markdown_table(
    ["Item", "Value"],
    [
        ["Status", _status_label(report.passed)],
        ["Cases path", report.cases_path],
        ["Suites", ", ".join(suite.name for suite in report.suite_reports)],
        ["Suite count", str(report.suite_count)],
        ["Passed suites", str(report.passed_suite_count)],
        ["Failed suites", str(report.failed_suite_count)],
    ],
)
```

这说明 Overall 表的数据来自：

```text
AgentEvalRunReport
```

不是从终端输出解析来的。

这就是结构化数据的价值。

### 4. Suite Summary 表如何生成

代码使用列表推导：

```python
[
    [
        suite.name,
        suite.title,
        str(suite.case_count),
        str(suite.failed_case_count),
        _status_label(suite.passed),
    ]
    for suite in report.suite_reports
]
```

它遍历每个 suite report。

生成每一行：

```text
suite 名称
suite 标题
case 数
失败 case 数
PASS/FAIL
```

这就是报告里的横向对比表。

### 5. _suite_markdown_lines

函数：

```python
def _suite_markdown_lines(report: AgentEvalSuiteReport) -> list[str]:
```

负责生成每个 suite 的详细段落。

结构是：

```markdown
## rag: RAG + Agent evaluation

### Summary

```text
...
```

### Bad Cases

```text
...
```
```

这种结构很适合阅读。

先看总表。

如果某个 suite 有问题，再跳到对应详情。

### 6. write_agent_eval_markdown_report

这个函数做文件写入：

```python
report_path = Path(path)
report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(
    build_agent_eval_markdown_report(report),
    encoding="utf-8",
)
return report_path
```

重点有三个：

```text
1. Path(path)：兼容字符串路径和 Path 对象
2. mkdir(parents=True, exist_ok=True)：自动创建目录
3. encoding="utf-8"：明确中文和文本编码
```

### 7. agent_eval.py 的修改

新增导入：

```python
from app.agents.eval_report import write_agent_eval_markdown_report
```

新增参数：

```python
parser.add_argument(
    "--report-path",
    type=Path,
    help="Write a Markdown evaluation report to this path.",
)
```

主流程新增：

```python
if args.report_path is not None:
    report_path = write_agent_eval_markdown_report(report, args.report_path)
    print("")
    print(f"markdown_report: {report_path}")
```

这段的意思是：

```text
如果用户传了 report-path，就写报告并打印报告路径。
```

打印：

```text
markdown_report: data\agent_eval\reports\agent_eval_report.md
```

方便用户知道文件在哪里。

### 8. 新增 tests/test_agent_eval_report.py

这个测试文件不需要启动真实命令行进程。

它直接测试：

```text
build_agent_eval_markdown_report
write_agent_eval_markdown_report
```

这符合第 8 节原则：

```text
核心逻辑放模块里，测试模块函数。
```

### 9. 测试 PASS 报告

测试：

```python
def test_build_agent_eval_markdown_report_contains_overall_and_suite_tables()
```

它运行：

```python
report = run_agent_eval_suites(CASES_PATH, suite_names=["intent", "rag"])
```

然后检查 Markdown 包含：

```text
# Agent Evaluation Report
## Overall
| Status | PASS |
## Suite Summary
## intent: Intent evaluation
## rag: RAG + Agent evaluation
No bad cases.
```

这个测试保护正常报告结构。

### 10. 测试 FAIL 报告

测试：

```python
def test_build_agent_eval_markdown_report_marks_failed_run_and_suite()
```

它手动构造一个失败的：

```text
AgentEvalRunReport
```

检查 Markdown 里是否有：

```text
FAIL
Bad cases
```

这很重要。

因为当前真实 Agent eval 全部通过。

如果只用真实数据测试，就测不到失败报告长什么样。

### 11. 测试写文件

测试：

```python
def test_write_agent_eval_markdown_report_creates_parent_directory(tmp_path)
```

它用 pytest 的 `tmp_path` 创建临时目录。

然后写：

```text
nested/agent_eval_report.md
```

验证：

```text
父目录会自动创建
文件存在
内容能用 UTF-8 读取
```

这比在真实项目目录里测试更干净。

---

## 四、本节运行结果

运行报告生成命令：

```powershell
uv run python scripts/agent_eval.py --cases-path data/agent_eval/agent_cases.json --report-path data/agent_eval/reports/agent_eval_report.md
```

终端关键输出：

```text
Agent evaluation suite
suites: intent, field, route, rag

Overall
suites: 4
passed_suites: 4
failed_suites: 0
passed: true

markdown_report: data\agent_eval\reports\agent_eval_report.md
```

生成的报告路径：

```text
projects/ai-service/data/agent_eval/reports/agent_eval_report.md
```

报告总览：

```markdown
# Agent Evaluation Report

## Overall

| Item | Value |
| --- | --- |
| Status | PASS |
| Cases path | data\agent_eval\agent_cases.json |
| Suites | intent, field, route, rag |
| Suite count | 4 |
| Passed suites | 4 |
| Failed suites | 0 |
```

运行新增测试：

```powershell
uv run pytest tests/test_agent_eval_report.py tests/test_agent_eval_suite.py -q
```

结果：

```text
11 passed
```

---

## 五、怎么阅读本节报告

### 1. 先看标题

标题：

```markdown
# Agent Evaluation Report
```

说明这是 Agent 评测报告。

### 2. 再看 Overall

重点看：

```text
Status
Failed suites
```

当前：

```text
Status = PASS
Failed suites = 0
```

说明整体通过。

### 3. 再看 Suite Summary

Suite Summary 表能让你快速知道：

```text
intent 是否通过
field 是否通过
route 是否通过
rag 是否通过
```

如果某一行是：

```text
FAIL
```

就跳到对应 suite 的详细段落。

### 4. 再看具体 suite 的 Summary

例如 RAG suite：

```text
source_recall: 1.0000
no_context_passed_cases: 1
ticket_decision_passed_count: 3
```

这些指标能帮助你理解：

```text
RAG 和 Agent 组合行为是否符合预期。
```

### 5. 最后看 Bad Cases

如果是：

```text
No bad cases.
```

说明该 suite 当前没有坏例。

如果出现坏例，就要进入第 10 节要学的内容：

```text
坏例分析。
```

---

## 六、常见误区

### 误区 1：报告就是终端输出复制一份

不是。

报告应该重新组织结构。

终端输出偏即时查看。

报告偏保存和复盘。

### 误区 2：只有失败时才需要报告

不是。

通过时的报告也有价值。

它能证明：

```text
当前版本在这份评测集上是通过的。
```

这对学习记录、项目展示和回归基线都重要。

### 误区 3：报告越长越好

不是。

报告要有层次。

不要把所有细节堆成流水账。

本节结构是：

```text
Overall
Suite Summary
Suite Details
Bad Cases
```

先总后分。

### 误区 4：Markdown 报告适合所有自动化场景

不是。

Markdown 适合人看。

机器处理更适合 JSON。

本节先做 Markdown，是因为当前目标是学习、回看和 GitHub 展示。

### 误区 5：写文件不用管编码

不对。

项目里有中文内容。

写报告时明确：

```text
encoding="utf-8"
```

可以减少跨系统编码问题。

### 误区 6：报告路径随便放

不建议。

报告路径应该和评测数据、评测主题有关系。

本节放在：

```text
data/agent_eval/reports/
```

因为它属于 Agent eval。

### 误区 7：报告里一定要放时间戳

不一定。

学习版报告为了稳定 diff，暂时不放时间戳。

以后做历史趋势时再引入时间、版本、commit hash 等信息。

---

## 七、本节练习

### 练习 1：生成当前 Agent 评测报告

题目：

在 `projects/ai-service` 目录下生成 Markdown 评测报告，命令是什么？

参考答案：

```powershell
uv run python scripts/agent_eval.py --cases-path data/agent_eval/agent_cases.json --report-path data/agent_eval/reports/agent_eval_report.md
```

生成文件：

```text
data/agent_eval/reports/agent_eval_report.md
```

### 练习 2：只生成 RAG suite 的报告

题目：

如果只想跑 RAG suite 并写入一个临时报告，命令怎么写？

参考答案：

```powershell
uv run python scripts/agent_eval.py --suite rag --report-path data/agent_eval/reports/rag_eval_report.md
```

这会只运行：

```text
rag
```

并写入：

```text
data/agent_eval/reports/rag_eval_report.md
```

### 练习 3：解释 Markdown 报告和终端输出区别

题目：

Markdown 报告和终端输出有什么区别？

参考答案：

终端输出适合当前立刻查看。

Markdown 报告适合保存、回看、提交到仓库、在 GitHub 预览、以后作为 CI artifact 下载。

报告不是简单复制终端输出，而是重新组织成标题、总览、总表、详情和坏例区。

### 练习 4：解释为什么先做 Markdown

题目：

为什么本节先做 Markdown 报告，而不是 JSON 报告？

参考答案：

因为当前学习阶段更需要人能直接阅读和复盘。

Markdown 是普通文本，Git diff 友好，GitHub 可以直接预览。

JSON 更适合机器读取，可以后续再做。

### 练习 5：解释 `build_agent_eval_markdown_report`

题目：

`build_agent_eval_markdown_report()` 的输入和输出分别是什么？

参考答案：

输入是：

```text
AgentEvalRunReport
```

输出是：

```text
Markdown 字符串
```

它只生成内容，不写文件。

### 练习 6：解释 `write_agent_eval_markdown_report`

题目：

`write_agent_eval_markdown_report()` 做了哪几件事？

参考答案：

它会：

```text
1. 把路径转成 Path
2. 创建父目录
3. 调用 build_agent_eval_markdown_report 生成 Markdown
4. 用 UTF-8 写入文件
5. 返回报告路径
```

### 练习 7：解释为什么报告里需要 Suite Summary

题目：

已经有每个 suite 的详细 Summary，为什么还需要 Suite Summary 总表？

参考答案：

因为总表能快速定位哪个 suite 失败。

如果没有总表，读者需要逐段翻完整报告，效率低。

Suite Summary 是先总后分里的“总”。

### 练习 8：解释为什么失败报告也要测试

题目：

当前真实评测全都通过，为什么还要写测试构造 FAIL 报告？

参考答案：

因为报告生成逻辑必须在失败时也正确。

如果只测试 PASS，无法保证坏例、FAIL 状态和失败 suite 表格能正常生成。

所以测试里手动构造失败的 `AgentEvalRunReport`。

---

## 八、自测题

### 自测 1：什么是评测报告？

参考答案：

评测报告是一次评测运行结果的结构化记录。

它记录使用的数据集、运行的 suite、整体状态、各 suite 指标和 bad cases。

### 自测 2：为什么报告不能只是把终端输出复制到文件？

参考答案：

因为终端输出偏即时查看，报告偏保存和复盘。

报告应该有更清楚的层次，例如 Overall、Suite Summary、Suite Details 和 Bad Cases。

### 自测 3：Markdown 报告适合谁看？

参考答案：

Markdown 报告主要适合人看。

例如开发者、学习者、面试复盘的人，或者在 GitHub 上浏览项目的人。

### 自测 4：JSON 报告适合什么场景？

参考答案：

JSON 报告适合程序读取。

例如 CI 统计、趋势分析、自动化仪表盘、数据库入库等。

### 自测 5：为什么本节报告路径放在 `data/agent_eval/reports/`？

参考答案：

因为这份报告属于 Agent eval 数据和运行结果。

它和 `data/agent_eval/agent_cases.json` 是同一主题，放在一起更清楚。

### 自测 6：为什么写报告时要 `encoding="utf-8"`？

参考答案：

因为项目包含中文内容。

显式指定 UTF-8 能减少不同系统默认编码不同导致的中文读写问题。

### 自测 7：`--report-path` 为什么是可选参数？

参考答案：

因为写报告会修改文件。

只有用户明确传入 `--report-path` 时才写文件，可以避免临时运行时产生不必要的工作区 diff。

### 自测 8：为什么本节报告暂时不加时间戳？

参考答案：

因为时间戳会导致每次运行都产生 diff。

当前学习版报告更需要稳定、可重复。

历史报告和时间戳可以后续再设计。

---

## 九、本节你应该形成的表达能力

学完本节后，你应该能这样说明：

```text
第 9 节在统一 Agent eval suite 的基础上增加了 Markdown 报告生成能力。
脚本仍然先运行评测得到 AgentEvalRunReport，然后同一个结构化对象既可以生成终端输出，也可以生成 Markdown 报告。
报告生成逻辑放在 app/agents/eval_report.py，不塞进 scripts/agent_eval.py。
用户只有传 --report-path 时才会写报告文件。
当前学习版报告保存在 data/agent_eval/reports/agent_eval_report.md，包含 Overall、Suite Summary、每个 suite 的 Summary 和 Bad Cases。
```

如果别人问你：

```text
为什么 Markdown 报告有价值？
```

你可以回答：

```text
因为它能把一次评测结果保存下来，方便 GitHub 预览、学习复盘、团队沟通和后续 CI artifact。
终端输出适合当下看，Markdown 报告适合以后看。
```

如果别人问你：

```text
这是不是生产级评测报告？
```

你可以回答：

```text
这是学习版的第一版报告。它已经有稳定结构和可保存文件，但还没有 JSON、历史趋势、图表、commit 信息和 CI artifact，这些会在后续生产化内容里继续补。
```

---

## 十、本节小结

本节把第 8 节的统一评测入口继续推进了一步：

```text
从终端输出
到 Markdown 报告文件
```

本节新增：

```text
app/agents/eval_report.py
tests/test_agent_eval_report.py
data/agent_eval/reports/agent_eval_report.md
```

并增强：

```text
scripts/agent_eval.py --report-path
```

当前报告包含：

```text
Overall
Suite Summary
每个 suite 的 Summary
每个 suite 的 Bad Cases
PASS/FAIL 状态
```

本节真正要掌握的是：

```text
评测报告是 AI 应用质量体系里的可保存证据，不是临时输出。
```

下一节进入：

```text
阶段 6 第 10 节：坏例分析
```

到时候我们会学习：

```text
当报告里真的出现 bad cases 时，如何判断问题来自数据、规则、模型、RAG、Agent 路由还是业务预期。
```

---

## 十一、参考资料

- [CommonMark Spec](https://spec.commonmark.org/0.31.2/)
  - 用途：理解 Markdown 是一种可读的结构化文本格式，标题、代码块、列表等语法为什么适合写轻量报告。

- [Python pathlib 官方文档](https://docs.python.org/3/library/pathlib.html)
  - 用途：理解 `Path`、路径拼接、创建目录、读写文件等基础能力，本节报告写入用到了 `Path.write_text()` 和 `Path.mkdir()`。

- [GitHub Actions：Store and share data with workflow artifacts](https://docs.github.com/en/actions/tutorials/store-and-share-data)
  - 用途：理解后续 CI 为什么会把评测报告这类文件作为 artifact 保存和分享。
