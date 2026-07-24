# 阶段 6 第 8 节：评测脚本设计

## 本节定位

前面几节我们已经分别完成了四类 Agent 评测：

```text
第 4 节：意图识别评测
第 5 节：工单字段提取评测
第 6 节：Agent 路由评测
第 7 节：RAG + Agent 组合评测
```

每一类评测都有自己的脚本：

```text
scripts/agent_intent_eval.py
scripts/agent_ticket_field_eval.py
scripts/agent_route_eval.py
scripts/agent_rag_eval.py
```

这些脚本现在都能运行。

但是它们有一个共同问题：

```text
如果以后要一键评测整个 Agent，就需要一个统一入口。
```

所以第 8 节学习：

```text
评测脚本设计
```

更准确地说，本节学习的是：

```text
怎样把分散的 evaluator 组织成一个可重复运行、可选择子项、可输出整体结果、适合以后接 CI 的命令行评测入口。
```

本节新增了：

```text
app/agents/eval_suite.py
scripts/agent_eval.py
tests/test_agent_eval_suite.py
```

以后你可以这样运行完整 Agent 评测：

```powershell
uv run python scripts/agent_eval.py
```

也可以只运行某一个评测套件：

```powershell
uv run python scripts/agent_eval.py --suite rag
uv run python scripts/agent_eval.py --suite route
```

还可以查看当前支持哪些评测套件：

```powershell
uv run python scripts/agent_eval.py --list-suites
```

本节不需要打开 VMware。

不需要 Docker。

不需要 Qdrant。

不需要 Milvus。

也不会真实调用大模型。

---

## 本节学习目标

学完本节，你应该能解释清楚：

1. 什么是评测脚本。
2. 评测脚本和 evaluator 的区别。
3. 为什么不能只写几个能跑的散脚本。
4. 为什么评测脚本要有清晰的命令行参数。
5. 为什么评测脚本要有稳定输出。
6. 为什么评测失败时脚本应该返回非 0 exit code。
7. 什么是 eval suite。
8. 什么是 registry。
9. 为什么脚本入口应该尽量薄。
10. 为什么真正的评测编排逻辑应该放进可测试的 Python 模块。
11. 为什么本节保留了原来的单项脚本，又新增了统一入口。
12. 以后 CI 自动评测会怎样使用这个统一入口。

---

## 本节先不学什么

本节暂时不学：

```text
1. CI 配置文件
2. GitHub Actions 自动运行 eval
3. JSON/HTML 评测报告落盘
4. LangSmith experiment
5. LLM-as-judge
6. 多数据集版本对比
7. 线上流量采样评测
```

原因是：

```text
评测脚本入口是这些能力的前置基础。
```

如果还没有一个稳定的本地脚本入口，就直接上 CI、报告和平台化评测，会变成：

```text
表面看起来更高级，实际每次运行都不可控。
```

所以本节先把基础打牢。

---

## 一、基础知识铺垫

### 1. 什么是脚本

脚本可以先理解成：

```text
为了完成某个固定任务而写的可执行程序。
```

在我们项目里，脚本通常放在：

```text
projects/ai-service/scripts/
```

例如：

```text
scripts/agent_intent_eval.py
```

它的任务不是对外提供 API。

也不是定义业务核心模型。

它的任务是：

```text
从命令行启动一次评测。
```

你在 PowerShell 里运行：

```powershell
uv run python scripts/agent_intent_eval.py
```

这时 Python 会执行这个文件。

脚本读取数据集，调用 evaluator，然后把结果打印出来。

### 2. 什么是评测脚本

评测脚本是脚本的一种。

它专门负责：

```text
运行评测任务。
```

一个最小的评测脚本通常有这几个步骤：

```text
1. 找到评测数据集
2. 加载评测样本
3. 调用某个 evaluator
4. 得到 summary
5. 打印 summary
6. 打印 bad cases
7. 根据是否失败返回 exit code
```

对应到之前的单项脚本，大概就是：

```text
load_agent_eval_cases
-> evaluate_xxx_cases
-> format_xxx_eval_summary
-> format_xxx_bad_cases
-> return 0 or 1
```

### 3. evaluator 和评测脚本不是一回事

这是本节最重要的基础区别之一。

evaluator 是：

```text
判断某类行为是否符合预期的评测逻辑。
```

例如：

```text
evaluate_intent_cases
evaluate_ticket_field_cases
evaluate_agent_route_cases
evaluate_rag_agent_cases
```

评测脚本是：

```text
把 evaluator 跑起来的命令行入口。
```

二者关系可以这样看：

```text
评测脚本
  -> 读取数据集
  -> 选择 evaluator
  -> 运行 evaluator
  -> 打印报告
  -> 返回 exit code
```

evaluator 更像发动机。

评测脚本更像启动器和仪表盘。

如果 evaluator 写得好，但是脚本混乱，那么别人很难稳定运行。

如果脚本写得好，但是 evaluator 判断标准不清楚，那么输出结果也没有意义。

两者都重要，但职责不同。

### 4. 为什么不能只靠散脚本

前面四个脚本都能跑：

```text
agent_intent_eval.py
agent_ticket_field_eval.py
agent_route_eval.py
agent_rag_eval.py
```

散脚本的优点是：

```text
简单
直观
学习单个评测时很好理解
```

但散脚本的缺点是：

```text
1. 每次要手动运行多个命令
2. 输出格式不容易汇总
3. 以后接 CI 时不知道该跑哪个
4. 多个脚本里容易复制同样逻辑
5. 新增 evaluator 时容易忘记补统一入口
```

所以进入工程化阶段后，需要一个统一入口：

```text
scripts/agent_eval.py
```

它的目标不是替代所有单项脚本。

它的目标是：

```text
给完整评测提供一个稳定入口。
```

### 5. 什么是命令行接口 CLI

CLI 是 Command Line Interface。

中文可以理解为：

```text
命令行接口。
```

你在 PowerShell 输入命令：

```powershell
uv run python scripts/agent_eval.py --suite rag
```

这就是在使用命令行接口。

这里有三层：

```text
uv run
python
scripts/agent_eval.py --suite rag
```

`uv run` 负责在当前项目环境里运行命令。

`python` 负责启动 Python 解释器。

`scripts/agent_eval.py --suite rag` 是传给 Python 程序的脚本路径和参数。

### 6. 什么是命令行参数

命令行参数就是：

```text
你在运行脚本时传进去的额外信息。
```

例如：

```powershell
uv run python scripts/agent_eval.py --suite rag
```

这里的：

```text
--suite rag
```

就是参数。

它表达的是：

```text
只运行 rag 这个评测套件。
```

再例如：

```powershell
uv run python scripts/agent_eval.py --cases-path data/agent_eval/agent_cases.json
```

这里表达的是：

```text
使用指定路径的数据集。
```

脚本一旦支持参数，就比固定写死更灵活。

但参数不能乱加。

一个好的命令行参数应该：

```text
1. 名字清楚
2. 默认值合理
3. 可选范围明确
4. 错误输入能被拦住
5. 帮助信息能看懂
```

### 7. 什么是 argparse

`argparse` 是 Python 标准库里的命令行参数解析工具。

它的作用是：

```text
把命令行里的字符串参数解析成 Python 对象。
```

例如命令：

```powershell
uv run python scripts/agent_eval.py --suite rag
```

对于脚本来说，命令行参数本质上最开始都是字符串。

`argparse` 会帮我们把这些字符串整理成：

```python
args.suite == ["rag"]
```

本节新增脚本里用了：

```python
ArgumentParser
parser.add_argument(...)
parser.parse_args(argv)
```

这些都是 `argparse` 的基础用法。

### 8. 什么是 argv

`argv` 可以先理解成：

```text
命令行参数列表。
```

例如：

```powershell
python scripts/agent_eval.py --suite rag
```

程序看到的参数大概是：

```text
["scripts/agent_eval.py", "--suite", "rag"]
```

在 Python 里，默认可以通过 `sys.argv` 拿到。

但本节代码没有在 `main()` 里直接写死使用 `sys.argv`。

而是这样设计：

```python
def main(argv: Sequence[str] | None = None) -> int:
```

这样做有一个好处：

```text
测试时可以直接传入模拟参数。
```

例如：

```python
main(["--suite", "rag"])
```

这比测试时真的启动一个新进程更轻。

本节测试主要测 `eval_suite.py` 模块，没有大量测试 argparse。

但这个 `argv` 设计是一个好习惯。

### 9. 什么是 exit code

exit code 是程序退出时返回给操作系统的数字。

最常见约定是：

```text
0 表示成功
非 0 表示失败
```

例如：

```python
return 0 if report.passed else 1
```

为什么这对评测脚本很重要？

因为人看输出可以知道失败。

但 CI 不会像人一样阅读每一行中文或英文解释。

CI 更依赖：

```text
这个命令最终退出码是不是 0。
```

如果 eval 失败了，脚本仍然返回 0，那么 CI 会误以为一切正常。

这会导致：

```text
评测已经发现坏例，但自动化流程没有拦住问题。
```

所以本节统一入口继续保持规则：

```text
所有 suite 都通过 -> exit code 0
任意 suite 失败 -> exit code 1
```

### 10. 什么是 stdout

stdout 是 standard output。

中文可以理解为：

```text
标准输出。
```

也就是你在终端看到的普通打印内容。

本节脚本使用：

```python
print(line)
```

这些内容会进入 stdout。

为什么要关心 stdout？

因为评测脚本输出不是随便打印。

它需要同时服务两类读者：

```text
1. 人
2. 自动化系统
```

人希望输出可读。

自动化系统希望输出稳定。

所以本节输出里有稳定的标题：

```text
Agent evaluation suite
== intent: Intent evaluation ==
Overall
failed_suites: 0
passed: true
```

这些行未来可以被日志系统、CI 页面或简单脚本读取。

### 11. 什么是 eval suite

suite 可以理解为：

```text
一组相关任务的集合。
```

eval suite 就是：

```text
一组评测任务。
```

在本节项目里，我们把这四类评测看成四个 suite：

```text
intent
field
route
rag
```

完整评测就是：

```text
intent + field + route + rag
```

单项评测就是：

```text
只跑其中一个 suite
```

这样以后新增：

```text
tool
prompt
llm_output
checkpoint
```

也可以继续放进同一个 suite 体系。

### 12. 什么是 registry

registry 可以理解为：

```text
注册表。
```

它把名字和具体对象对应起来。

本节里：

```python
{
    "intent": AgentEvalSuite(...),
    "field": AgentEvalSuite(...),
    "route": AgentEvalSuite(...),
    "rag": AgentEvalSuite(...),
}
```

就是一个评测套件注册表。

有了 registry，脚本就不用写一堆 if else：

```python
if suite == "intent":
    ...
elif suite == "field":
    ...
elif suite == "route":
    ...
```

而是可以通过名字找到套件：

```python
suite_registry[name]
```

这让扩展更清楚。

新增一个 suite 时，主要改：

```text
build_agent_eval_suite_registry()
```

### 13. 什么是 orchestration

orchestration 可以理解为：

```text
编排。
```

编排层自己不做某个具体业务判断。

它负责把多个步骤组织起来。

本节的 `eval_suite.py` 就是一个评测编排层。

它不关心：

```text
intent 到底怎么判断
field 到底怎么比较
route 到底怎么匹配
rag citation 到底怎么检查
```

这些是各自 evaluator 的职责。

它关心的是：

```text
1. 有哪些 suite
2. 选择哪些 suite
3. 按什么顺序运行
4. 怎么收集结果
5. 怎么形成整体报告
6. 怎么计算整体是否通过
```

这就是编排层。

### 14. 脚本入口为什么要薄

脚本入口最好不要写太多核心逻辑。

原因是：

```text
脚本入口通常更难直接单元测试。
```

如果把所有逻辑都塞进：

```text
scripts/agent_eval.py
```

测试时要么启动子进程，要么很难控制输入输出。

本节选择：

```text
scripts/agent_eval.py 只负责解析命令行参数和打印
app/agents/eval_suite.py 负责真正的评测编排
```

这样设计后，测试可以直接测：

```python
run_agent_eval_suites(...)
format_agent_eval_run_report(...)
exit_code_for_agent_eval_report(...)
```

不用每个测试都启动命令行进程。

### 15. 为什么要保留单项脚本

本节没有删除：

```text
agent_intent_eval.py
agent_ticket_field_eval.py
agent_route_eval.py
agent_rag_eval.py
```

原因是：

```text
单项脚本对学习和调试仍然有价值。
```

当你只想调试 RAG + Agent 组合评测时，运行：

```powershell
uv run python scripts/agent_rag_eval.py
```

比完整跑 suite 更直接。

当你想上线前做完整回归时，运行：

```powershell
uv run python scripts/agent_eval.py
```

更合适。

所以现在形成了两层：

```text
单项脚本：适合局部学习和局部调试
统一脚本：适合整体回归和以后 CI
```

### 16. 为什么默认跑全部 suite

如果用户运行：

```powershell
uv run python scripts/agent_eval.py
```

没有传任何参数。

本节设计为：

```text
默认运行全部 suite。
```

原因是：

```text
默认行为应该符合最常见、最安全的使用场景。
```

评测脚本最常见的使用场景是：

```text
我想知道当前 Agent 整体有没有退化。
```

所以默认跑全部。

如果只想跑某一项，再显式写：

```powershell
--suite rag
```

### 17. 为什么要支持 --list-suites

`--list-suites` 的作用是：

```text
告诉使用者当前脚本支持哪些评测套件。
```

运行结果：

```text
intent
field
route
rag
```

这个功能看似小，但很实用。

因为过几节后，suite 会越来越多。

如果每次都要打开源码查有哪些 suite，就不方便。

### 18. 为什么要限制 --suite 的 choices

本节脚本里：

```python
choices=["all", *list_agent_eval_suite_names()]
```

意思是：

```text
--suite 只能选择 all、intent、field、route、rag。
```

如果用户输入：

```powershell
uv run python scripts/agent_eval.py --suite abc
```

argparse 会直接提示参数错误。

这样可以避免：

```text
错误输入悄悄被忽略。
```

脚本设计里，一个很重要的原则是：

```text
错误要早暴露，不要默默吞掉。
```

### 19. 为什么输出要有人类可读的分段

完整评测会输出很多内容。

如果没有分段，用户会很难看出哪一部分属于哪个 suite。

所以本节输出类似：

```text
== intent: Intent evaluation ==
...

== field: Ticket field evaluation ==
...

== route: Agent route evaluation ==
...

== rag: RAG + Agent evaluation ==
...

Overall
...
```

这种分段能让你快速定位：

```text
到底是 intent 坏了，还是 route 坏了，还是 rag 坏了。
```

### 20. 为什么整体报告要有 Overall

每个 suite 有自己的 summary。

但完整评测还需要一个整体判断：

```text
这次完整评测到底算不算通过？
```

所以本节加入：

```text
Overall
suites: 4
passed_suites: 4
failed_suites: 0
passed: true
```

它回答的是：

```text
从完整 Agent eval suite 的角度看，当前是否通过。
```

以后 CI 最关心的就是这个整体结果和 exit code。

### 21. 为什么本节不输出 JSON 报告

你可能会问：

```text
既然要给 CI 用，为什么不直接输出 JSON？
```

这是一个好问题。

原因是：

```text
JSON 报告是后续评测报告章节更适合学的内容。
```

本节先解决：

```text
统一入口
套件选择
统一格式化
整体通过失败
exit code
```

等第 9 节“评测报告”时，再进一步讨论：

```text
报告落盘
JSON 报告
Markdown 报告
坏例列表
改进建议
```

这就是学习顺序。

### 22. 什么是可测试的脚本设计

可测试的脚本设计不是指每一行 `print` 都要测。

而是指：

```text
脚本背后的核心逻辑可以被自动化测试覆盖。
```

本节把核心逻辑放在：

```text
app/agents/eval_suite.py
```

测试文件：

```text
tests/test_agent_eval_suite.py
```

覆盖了：

```text
1. suite 名称顺序稳定
2. 默认运行所有 suite
3. 可以只运行一个 suite
4. 可以按指定顺序运行多个 suite
5. 未知 suite 会报错
6. 整体报告可读
7. 有 suite 失败时整体失败
8. exit code 成功失败规则正确
```

这些比只测命令能不能打印更重要。

---

## 二、本节主题系统讲解

### 1. 本节解决的真实问题

第 4 到第 7 节完成后，项目已经有了四个 evaluator：

```text
intent evaluator
field evaluator
route evaluator
rag evaluator
```

如果手动跑全部评测，需要：

```powershell
uv run python scripts/agent_intent_eval.py
uv run python scripts/agent_ticket_field_eval.py
uv run python scripts/agent_route_eval.py
uv run python scripts/agent_rag_eval.py
```

这对学习没问题。

但对工程化不够好。

真实项目里你希望有一个入口：

```powershell
uv run python scripts/agent_eval.py
```

它自动完成：

```text
1. 加载同一份数据集
2. 运行多个 evaluator
3. 输出每个 evaluator 的报告
4. 输出整体通过失败
5. 返回正确 exit code
```

这就是本节的核心。

### 2. 本节新增后的整体结构

新增后结构变成：

```text
data/agent_eval/agent_cases.json
        |
        v
scripts/agent_eval.py
        |
        v
app/agents/eval_suite.py
        |
        +--> intent_evaluation.py
        +--> field_evaluation.py
        +--> route_evaluation.py
        +--> rag_agent_evaluation.py
        |
        v
terminal output + exit code
```

你要注意：

```text
agent_eval.py 不是新的 evaluator。
```

它只是统一入口。

真正判断对错的仍然是：

```text
intent_evaluation.py
field_evaluation.py
route_evaluation.py
rag_agent_evaluation.py
```

### 3. 为什么 eval_suite.py 放在 app/agents

`eval_suite.py` 放在：

```text
app/agents/eval_suite.py
```

原因是它属于 Agent 评测领域逻辑。

它不是普通工具函数。

它知道：

```text
AgentEvalCase
intent evaluator
field evaluator
route evaluator
rag evaluator
```

这些都属于 Agent 评测。

所以放在 `app/agents` 下是合理的。

脚本 `scripts/agent_eval.py` 只调用它，不承载太多逻辑。

### 4. AgentEvalSuite 表达了什么

本节新增：

```python
@dataclass(frozen=True)
class AgentEvalSuite:
    name: str
    title: str
    evaluate: EvaluateSuite
    format_summary: FormatSuiteReport
    format_bad_cases: FormatSuiteReport
```

你可以把它理解为：

```text
一个评测套件的说明书。
```

它说明：

```text
这个 suite 叫什么
显示标题是什么
怎么运行评测
怎么格式化 summary
怎么格式化 bad cases
```

例如 RAG suite：

```python
AgentEvalSuite(
    name="rag",
    title="RAG + Agent evaluation",
    evaluate=evaluate_rag_agent_cases,
    format_summary=format_rag_agent_eval_summary,
    format_bad_cases=format_rag_agent_bad_cases,
)
```

这段的意思是：

```text
当用户选择 rag 时：
用 evaluate_rag_agent_cases 跑评测；
用 format_rag_agent_eval_summary 打印摘要；
用 format_rag_agent_bad_cases 打印坏例。
```

### 5. 为什么 AgentEvalSuite 用 dataclass

`AgentEvalSuite` 用的是：

```python
@dataclass(frozen=True)
```

不是 Pydantic。

原因是：

```text
它主要保存函数引用。
```

比如：

```python
evaluate=evaluate_intent_cases
```

这不是普通 JSON 数据。

它更像运行时配置。

`dataclass` 很适合这种简单的 Python 对象。

`frozen=True` 表示创建后不希望被随便修改。

这能减少误改：

```text
注册好的 suite 不应该在运行中被改名或换 evaluator。
```

### 6. AgentEvalSuiteReport 表达了什么

本节新增：

```python
class AgentEvalSuiteReport(BaseModel):
    name: str
    title: str
    case_count: int
    failed_case_count: int
    passed: bool
    summary_lines: list[str]
    bad_case_lines: list[str]
```

这是单个 suite 的运行结果。

它不是 evaluator 原始 summary。

它是统一包装后的结果。

不管底层是 intent、field、route 还是 rag，统一入口只需要知道：

```text
这个 suite 叫什么
跑了多少 case
失败多少 case
是否通过
summary 要打印哪些行
bad cases 要打印哪些行
```

这就把不同 evaluator 的差异收敛到统一结构里。

### 7. AgentEvalRunReport 表达了什么

本节新增：

```python
class AgentEvalRunReport(BaseModel):
    cases_path: str
    suite_count: int
    passed_suite_count: int
    failed_suite_count: int
    passed: bool
    suite_reports: list[AgentEvalSuiteReport]
```

这是完整评测运行的总报告。

它回答：

```text
这次使用哪个数据集？
一共跑了几个 suite？
几个 suite 通过？
几个 suite 失败？
整体是否通过？
每个 suite 的报告是什么？
```

这就是 `Overall` 输出的数据来源。

### 8. build_agent_eval_suite_registry 的作用

代码：

```python
def build_agent_eval_suite_registry() -> dict[str, AgentEvalSuite]:
```

它负责构建注册表。

现在有四项：

```text
intent
field
route
rag
```

顺序也有意义。

本节固定顺序是：

```text
intent -> field -> route -> rag
```

原因是它符合学习顺序：

```text
先看意图
再看字段
再看路由
最后看 RAG + Agent 组合行为
```

顺序稳定很重要。

因为输出顺序不稳定，会影响阅读，也会影响将来做报告对比。

### 9. resolve_agent_eval_suites 的作用

代码：

```python
def resolve_agent_eval_suites(...)
```

它负责把用户输入的名字转换成真正的 suite 对象。

情况一：

```text
用户没有传 suite
```

返回全部 suite。

情况二：

```text
用户传了 all
```

返回全部 suite。

情况三：

```text
用户传了 ["rag"]
```

返回 RAG suite。

情况四：

```text
用户传了未知名字
```

抛出错误。

这个函数是统一入口里的参数选择层。

### 10. run_agent_eval_suites 的作用

代码：

```python
def run_agent_eval_suites(cases_path, suite_names=None, registry=None)
```

它负责从文件路径开始运行。

流程是：

```text
读取 agent_cases.json
-> 得到 cases
-> 调用 run_agent_eval_suites_for_cases
```

为什么要拆成两个函数？

因为：

```text
一个适合真实文件运行
一个适合测试时直接传 cases
```

这种拆分能让测试更容易。

### 11. run_agent_eval_suites_for_cases 的作用

代码：

```python
def run_agent_eval_suites_for_cases(cases, cases_path, suite_names=None, registry=None)
```

它已经不关心文件怎么读取了。

它只关心：

```text
给我 cases，我来跑 suite。
```

这让它更纯粹。

测试里可以传：

```python
cases = load_agent_eval_cases(CASES_PATH)[:1]
```

然后用 fake suite 模拟失败。

这就是可测试设计。

### 12. _run_single_suite 的作用

代码：

```python
def _run_single_suite(suite, cases)
```

它负责运行一个 suite。

流程：

```text
summary = suite.evaluate(cases)
failed_case_count = summary.failed_case_count
case_count = summary.case_count
summary_lines = suite.format_summary(summary)
bad_case_lines = suite.format_bad_cases(summary)
```

然后包装成：

```text
AgentEvalSuiteReport
```

它要求每个 evaluator summary 至少暴露：

```text
case_count
failed_case_count
```

这也是一种隐含接口。

虽然不同 summary 类型不同，但只要都有这两个字段，就能被统一入口编排。

### 13. format_agent_eval_run_report 的作用

这个函数负责把结构化报告变成终端文本。

它不重新计算评测结果。

它只格式化。

这点很重要：

```text
计算和展示分开。
```

如果以后要做 JSON 报告，可以复用：

```text
AgentEvalRunReport
```

而不需要重新跑评测。

如果以后要做 Markdown 报告，也可以从同一个 report 生成。

### 14. exit_code_for_agent_eval_report 的作用

代码：

```python
def exit_code_for_agent_eval_report(report):
    return 0 if report.passed else 1
```

它很短。

但它表达了一个工程规则：

```text
完整评测通过，命令成功。
完整评测失败，命令失败。
```

不要小看这类函数。

它把规则命名了。

以后别人看到这个函数名，不用猜：

```text
脚本退出码到底怎么来的？
```

### 15. scripts/agent_eval.py 的职责

脚本主要做三件事：

```text
1. 解析命令行参数
2. 调用 eval_suite 模块
3. 打印结果并返回 exit code
```

它不直接写具体 evaluator 逻辑。

这样脚本就保持很薄。

这也是以后写脚本时可以借鉴的模式：

```text
脚本文件负责 CLI
app 模块负责核心逻辑
tests 测核心逻辑
```

### 16. 本节新增命令怎么用

查看支持的 suite：

```powershell
uv run python scripts/agent_eval.py --list-suites
```

输出：

```text
intent
field
route
rag
```

运行全部 suite：

```powershell
uv run python scripts/agent_eval.py
```

只运行 RAG suite：

```powershell
uv run python scripts/agent_eval.py --suite rag
```

运行 route 和 intent：

```powershell
uv run python scripts/agent_eval.py --suite route --suite intent
```

指定数据集路径：

```powershell
uv run python scripts/agent_eval.py --cases-path data/agent_eval/agent_cases.json
```

查看帮助：

```powershell
uv run python scripts/agent_eval.py --help
```

### 17. 本节为什么不直接合并删除旧脚本

这属于工程取舍。

如果现在删除旧脚本，会有两个问题：

```text
1. 前面第 4-7 节笔记里提到的单项脚本会失效
2. 学习时调试某个 evaluator 不如原来直接
```

所以本节策略是：

```text
新增统一入口，保留单项入口。
```

这是一种兼容性更好的做法。

工程里经常会这样演进：

```text
先保留旧入口
再增加新入口
等新入口稳定后再考虑是否收敛
```

### 18. 本节和下一节的关系

第 8 节解决：

```text
如何统一运行评测。
```

第 9 节会解决：

```text
如何输出更完整的评测报告。
```

所以第 8 节更偏：

```text
脚本入口设计
运行编排
exit code
suite 选择
```

第 9 节会更偏：

```text
报告内容设计
坏例展示
指标展示
报告落盘
给人看和给机器看
```

---

## 三、本节新增代码讲解

### 1. 新增 app/agents/eval_suite.py

这个文件是本节核心。

它承担：

```text
Agent 评测套件编排
```

不是具体 evaluator。

你可以把它看成：

```text
把第 4-7 节的 evaluator 串起来的控制层。
```

它导入了四类评测：

```python
from app.agents.field_evaluation import ...
from app.agents.intent_evaluation import ...
from app.agents.rag_agent_evaluation import ...
from app.agents.route_evaluation import ...
```

这说明它依赖已有 evaluator。

但它不改这些 evaluator 的内部逻辑。

### 2. EvaluationSummary 为什么用 Any

代码里有：

```python
EvaluationSummary = Any
```

这是因为四个 evaluator 的 summary 类型不同：

```text
IntentEvalSummary
TicketFieldEvalSummary
AgentRouteEvalSummary
RagAgentEvalSummary
```

它们不是同一个类。

但统一入口只要求它们共同拥有：

```text
case_count
failed_case_count
```

还有对应的格式化函数。

所以这里用 `Any` 是一种务实写法。

后面如果要更严格，可以学习 `Protocol`。

但当前阶段先不引入太多类型系统知识。

### 3. AgentEvalSuite 的 evaluate 字段

代码：

```python
evaluate: EvaluateSuite
```

它保存的是函数。

例如：

```python
evaluate=evaluate_intent_cases
```

这意味着：

```text
函数也可以作为数据保存到对象里。
```

Python 里函数是一等对象。

也就是说，函数可以：

```text
1. 赋值给变量
2. 作为参数传递
3. 放进 dataclass
4. 从函数返回
```

本节 registry 就用了这个能力。

### 4. build_agent_eval_suite_registry

这个函数里显式列出当前支持的 suite。

这样做有两个好处：

```text
1. 所有 suite 都集中注册，容易查
2. 输出顺序稳定
```

如果以后新增工具调用评测，可能会加：

```python
AgentEvalSuite(
    name="tool",
    title="Tool calling evaluation",
    evaluate=evaluate_tool_cases,
    format_summary=format_tool_eval_summary,
    format_bad_cases=format_tool_bad_cases,
)
```

这样就接入统一入口了。

### 5. resolve_agent_eval_suites

这个函数负责处理用户选择。

它把：

```python
["rag"]
```

变成：

```text
RAG suite 对象
```

它把：

```python
None
```

变成：

```text
全部 suite
```

它遇到未知名字会抛错。

这就是命令行参数和内部对象之间的转换层。

### 6. run_agent_eval_suites

这个函数从文件路径开始。

它适合真实脚本调用。

因为脚本拿到的是：

```text
cases_path
```

不是已经加载好的 cases。

所以它先调用：

```python
load_agent_eval_cases(cases_path)
```

再进入下一层。

### 7. run_agent_eval_suites_for_cases

这个函数从 cases 开始。

它适合测试。

测试里可以传：

```python
cases = load_agent_eval_cases(CASES_PATH)[:1]
```

也可以注入 fake registry。

这就是为什么本节测试能模拟失败 suite：

```python
registry = {
    "fake": AgentEvalSuite(...)
}
```

不用真的把项目搞坏。

### 8. _summary_int

这个私有函数：

```python
def _summary_int(summary, field_name):
```

负责从 summary 上读取整数字段。

如果字段不存在或不是整数，它会抛出：

```text
TypeError
```

这是一种防御。

因为统一入口要求每个 summary 至少有：

```text
case_count
failed_case_count
```

如果以后有人新增 evaluator，却没按这个约定返回 summary，错误会尽早暴露。

### 9. 新增 scripts/agent_eval.py

这个文件是命令行入口。

核心结构是：

```python
def build_parser() -> ArgumentParser:
    ...

def main(argv: Sequence[str] | None = None) -> int:
    ...

if __name__ == "__main__":
    raise SystemExit(main())
```

这是一个常见脚本结构。

`build_parser()` 负责构建参数解析器。

`main()` 负责运行主流程。

`SystemExit(main())` 负责把返回值变成进程退出码。

### 10. --suite 为什么用 action="append"

代码：

```python
parser.add_argument(
    "--suite",
    action="append",
    ...
)
```

`append` 的意思是：

```text
这个参数可以重复出现，每出现一次就追加一个值。
```

例如：

```powershell
uv run python scripts/agent_eval.py --suite route --suite intent
```

解析后大概是：

```python
args.suite == ["route", "intent"]
```

这样比用逗号字符串更清楚。

不需要自己手动拆：

```text
"route,intent"
```

### 11. --cases-path 为什么用 Path 类型

代码：

```python
type=Path
```

这样 argparse 会把输入转换成 `Path` 对象。

后续代码处理路径更自然。

默认值是：

```python
DEFAULT_CASES_PATH = PROJECT_ROOT / "data" / "agent_eval" / "agent_cases.json"
```

这表示：

```text
默认读取当前项目里的 Agent 评测数据集。
```

### 12. 新增 tests/test_agent_eval_suite.py

测试覆盖的是设计边界。

不是为了追求数量。

重点有：

```text
suite 名称顺序
默认跑全部
筛选单项
筛选多项并保持顺序
未知 suite 报错
格式化输出可读
任意 suite 失败时整体失败
exit code 成功失败规则
```

这些测试会保护统一入口的核心行为。

---

## 四、本节运行结果

查看 suite：

```powershell
uv run python scripts/agent_eval.py --list-suites
```

输出：

```text
intent
field
route
rag
```

只运行 RAG suite：

```powershell
uv run python scripts/agent_eval.py --suite rag
```

核心输出：

```text
Agent evaluation suite
suites: rag

== rag: RAG + Agent evaluation ==
RAG + Agent evaluation summary
cases: 3
passed_cases: 3
failed_cases: 0
source_recall: 1.0000
No bad cases.

Overall
suites: 1
passed_suites: 1
failed_suites: 0
passed: true
```

运行新测试：

```powershell
uv run pytest tests/test_agent_eval_suite.py -q
```

结果：

```text
8 passed
```

---

## 五、怎么阅读本节输出

### 1. 先看 Agent evaluation suite

这说明你运行的是统一入口。

不是单项脚本。

### 2. 看 cases_path

它告诉你：

```text
这次评测使用的是哪份数据集。
```

如果以后有多份数据集，这一行很关键。

### 3. 看 suites

它告诉你：

```text
这次实际跑了哪些评测套件。
```

比如：

```text
suites: rag
```

就表示只跑了 RAG + Agent 评测。

### 4. 看每个 == suite ==

例如：

```text
== rag: RAG + Agent evaluation ==
```

这一段下面就是 RAG suite 的详细摘要和 bad cases。

### 5. 最后看 Overall

`Overall` 是整体结果。

你最需要关注：

```text
failed_suites
passed
```

如果：

```text
failed_suites: 0
passed: true
```

说明本次整体评测通过。

如果：

```text
failed_suites: 1
passed: false
```

说明至少一个 suite 有失败。

这时脚本退出码也应该是 1。

---

## 六、常见误区

### 误区 1：统一脚本就是把四个脚本复制到一起

不是。

如果只是复制，就会形成更大的重复代码。

本节统一脚本的关键是：

```text
用 suite registry 把 evaluator 组织起来。
```

### 误区 2：脚本能打印结果就够了

不够。

评测脚本必须考虑：

```text
参数
输出格式
失败状态
exit code
可测试性
以后接 CI
```

### 误区 3：exit code 不重要

非常重要。

CI 判断命令是否成功，主要看 exit code。

如果评测失败但 exit code 还是 0，自动化流程就会放过问题。

### 误区 4：所有逻辑都写在 scripts 目录最方便

短期看方便。

长期看会难测试、难复用、难维护。

更好的方式是：

```text
scripts 负责入口
app 模块负责核心逻辑
tests 负责核心逻辑测试
```

### 误区 5：统一入口会取代单项入口

现在不会。

单项入口适合局部调试。

统一入口适合整体回归。

两者用途不同。

### 误区 6：默认只跑一个 suite 更快

更快不一定更安全。

默认运行完整评测更符合回归检查的目的。

想快的时候，可以显式指定：

```powershell
--suite rag
```

### 误区 7：输出越花哨越好

不是。

评测脚本输出应该稳定、清楚、容易复制。

花哨颜色、复杂表格、过度装饰都不是当前阶段重点。

---

## 七、本节练习

### 练习 1：运行完整 Agent 评测

题目：

在 `projects/ai-service` 目录下运行统一评测入口。

命令是什么？

参考答案：

```powershell
uv run python scripts/agent_eval.py
```

你应该重点看输出里的：

```text
Overall
failed_suites
passed
```

如果当前代码正常，应该看到：

```text
failed_suites: 0
passed: true
```

### 练习 2：只运行 RAG + Agent 评测

题目：

只运行 `rag` suite，命令是什么？

参考答案：

```powershell
uv run python scripts/agent_eval.py --suite rag
```

这条命令只会跑：

```text
RAG + Agent evaluation
```

不会跑 intent、field、route。

### 练习 3：查看可用 suite

题目：

如果你忘了有哪些 suite，应该运行什么命令？

参考答案：

```powershell
uv run python scripts/agent_eval.py --list-suites
```

当前输出应该包含：

```text
intent
field
route
rag
```

### 练习 4：同时运行 route 和 intent

题目：

只运行 route 和 intent 两个 suite，命令是什么？

参考答案：

```powershell
uv run python scripts/agent_eval.py --suite route --suite intent
```

因为 `--suite` 使用了 `action="append"`，所以可以重复写。

输出顺序会按照你传入的顺序：

```text
route
intent
```

### 练习 5：解释 exit code

题目：

为什么 eval 失败时脚本应该返回非 0 exit code？

参考答案：

因为 CI 或自动化脚本主要通过 exit code 判断命令是否成功。

约定是：

```text
0 表示成功
非 0 表示失败
```

如果评测失败但脚本返回 0，CI 会误以为没有问题。

### 练习 6：解释脚本入口为什么要薄

题目：

为什么不把所有评测编排逻辑都写进 `scripts/agent_eval.py`？

参考答案：

因为脚本入口主要负责命令行参数和打印输出。

如果核心逻辑都写在脚本里，会更难测试和复用。

本节把核心逻辑放到：

```text
app/agents/eval_suite.py
```

这样测试可以直接调用 Python 函数，而不是每次都启动命令行进程。

### 练习 7：说明 registry 的价值

题目：

`build_agent_eval_suite_registry()` 解决了什么问题？

参考答案：

它把 suite 名称和 suite 配置集中注册起来。

这样统一入口可以通过名字找到对应 evaluator 和格式化函数。

这比到处写 if else 更清楚，也更容易扩展。

### 练习 8：新增 suite 时应该改哪里

题目：

如果以后新增一个 `tool` 评测套件，大概率要先改哪个地方？

参考答案：

先在：

```text
app/agents/eval_suite.py
```

里的：

```python
build_agent_eval_suite_registry()
```

新增一个：

```python
AgentEvalSuite(...)
```

然后补对应测试和脚本运行验证。

---

## 八、自测题

### 自测 1：评测脚本和 evaluator 的区别是什么？

参考答案：

evaluator 负责判断某类行为是否符合预期。

评测脚本负责从命令行启动评测，包括加载数据、调用 evaluator、打印报告和返回 exit code。

### 自测 2：为什么本节新增的是 scripts/agent_eval.py，而不是继续新增第五个单项脚本？

参考答案：

因为前面已经有多个单项脚本。

本节的目标是把多个 evaluator 组织成统一入口，支持完整回归评测和后续 CI，而不是继续增加分散入口。

### 自测 3：默认运行全部 suite 有什么好处？

参考答案：

默认运行全部 suite 更适合整体回归检查。

用户不传参数时，脚本就能回答：

```text
当前 Agent 整体评测是否通过？
```

### 自测 4：为什么 `--suite` 可以重复写？

参考答案：

因为 argparse 里使用了：

```python
action="append"
```

每出现一次 `--suite`，就把对应值追加到列表里。

所以可以写：

```powershell
--suite route --suite intent
```

### 自测 5：什么是 `AgentEvalRunReport`？

参考答案：

它是一次完整评测运行的总报告。

它记录使用的数据集、suite 数量、通过的 suite 数量、失败的 suite 数量、整体是否通过，以及每个 suite 的报告。

### 自测 6：为什么 `format_agent_eval_run_report` 不直接重新跑评测？

参考答案：

因为它的职责是格式化，不是计算。

评测已经在 `run_agent_eval_suites` 中完成。

计算和展示分开，可以让代码更清楚，也方便以后扩展 JSON 或 Markdown 报告。

### 自测 7：为什么测试里要用 fake suite 模拟失败？

参考答案：

因为我们不应该为了测试统一入口失败逻辑而故意破坏真实 Agent。

fake suite 可以稳定构造失败 summary，专门验证：

```text
任意 suite 失败时整体报告失败，exit code 为 1。
```

### 自测 8：如果将来 CI 运行 `uv run python scripts/agent_eval.py`，它最关心什么？

参考答案：

最关心两件事：

```text
1. 命令输出里的整体结果
2. 命令最终 exit code
```

如果 exit code 是 0，CI 认为通过。

如果 exit code 是非 0，CI 认为失败。

---

## 九、本节你应该形成的表达能力

学完本节后，你应该能这样解释：

```text
我们前面已经分别实现了意图、字段、路由和 RAG + Agent 组合评测。
第 8 节把这些 evaluator 统一组织成 Agent eval suite。
新增的 scripts/agent_eval.py 是命令行入口，默认运行全部 suite，也支持 --suite 选择单项。
真正的编排逻辑放在 app/agents/eval_suite.py 里，脚本只负责解析参数、调用编排函数、打印结果并返回 exit code。
这样设计后，本地可以一键回归，后面也能接 CI。
```

如果别人问你：

```text
为什么不直接在脚本里写一堆 if else？
```

你可以回答：

```text
因为 suite registry 更清楚、更容易扩展，也更利于测试。
脚本入口应该薄，核心逻辑应该放在可测试模块里。
```

如果别人问你：

```text
为什么 exit code 重要？
```

你可以回答：

```text
因为 CI 和自动化系统主要靠 exit code 判断命令成功或失败。
AI 评测发现坏例时，脚本必须返回非 0，否则自动化流程会误判为通过。
```

---

## 十、本节小结

本节完成了从：

```text
多个分散评测脚本
```

到：

```text
统一 Agent eval suite 入口
```

的第一步。

新增的统一入口具备：

```text
1. 默认运行全部 suite
2. 支持 --suite 筛选
3. 支持 --list-suites
4. 统一格式化输出
5. 输出 Overall
6. 根据整体结果返回 exit code
7. 有测试覆盖核心设计边界
```

本节真正要掌握的不是某几行代码。

而是这个思想：

```text
评测脚本不是临时命令，而是 AI 应用质量体系的一部分。
```

后续第 9 节会继续在这个基础上学习：

```text
评测报告
```

也就是如何把当前终端输出进一步整理成更适合回看、复盘和持续改进的报告。

---

## 十一、参考资料

- [Python argparse 官方文档](https://docs.python.org/3/library/argparse.html)
  - 用途：学习 Python 标准库如何解析命令行参数、定义 option、flag、choices 和 help 信息。

- [Python sys.argv 官方文档](https://docs.python.org/3/library/sys.html#sys.argv)
  - 用途：理解命令行参数最底层如何进入 Python 程序。

- [pytest 官方文档：How to invoke pytest](https://docs.pytest.org/en/stable/how-to/usage.html)
  - 用途：理解为什么测试命令本身也依赖 exit code，以及如何在本地运行指定测试文件。
