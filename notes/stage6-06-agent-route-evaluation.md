# 阶段 6 第 6 节：Agent 路由评测

## 本节定位

前面两节我们已经完成了两类 eval：

```text
第 4 节：意图识别评测
第 5 节：工单字段提取评测
```

第 4 节关注：

```text
用户这句话应该被识别成什么 intent？
```

第 5 节关注：

```text
如果需要创建工单，字段有没有抽对？
```

这一节学习第三类 eval：

```text
Agent 路由评测
```

它关注：

```text
Agent 实际有没有走对流程节点？
```

例如：

```text
用户：退款多久到账？
```

期望路径：

```text
normalize_user_input
-> classify_intent
-> retrieve_policy
-> decide_ticket_need
```

再例如：

```text
用户：我要投诉商家一直不发货，麻烦人工处理
```

期望路径：

```text
normalize_user_input
-> classify_intent
-> decide_ticket_need
-> extract_ticket_fields
-> ask_missing_ticket_fields
```

这一节不需要打开虚拟机，不需要 Docker，不需要 Qdrant，不需要 Milvus，也不需要真实调用大模型。

本节仍然使用本地固定样本：

```text
projects/ai-service/data/agent_eval/agent_cases.json
```

## 本节学习目标

学完本节，你应该能解释清楚：

1. 什么是 Agent 路由。
2. 什么是节点。
3. 什么是边。
4. 什么是条件边。
5. 什么是 `node_history`。
6. 为什么 intent 对了，还要看路径对不对。
7. 为什么字段对了，也还要看流程对不对。
8. 什么是 expected node path。
9. 什么是 actual node path。
10. 什么是 path exact match。
11. 什么是 required nodes。
12. 什么是 forbidden nodes。
13. 什么是 terminal node。
14. 路由 eval 如何从样本 expected 推导路径。
15. 路由 eval 如何输出 bad cases。
16. 路由 eval 和意图 eval、字段 eval 的区别。

## 本节先不学什么

本节只学习 Agent 路由评测，不提前学习：

- 不评测 RAG 召回是否正确。
- 不评测字段值是否正确。
- 不评测工具参数是否正确。
- 不真实创建 Java 工单。
- 不评测最终中文回答质量。
- 不评测多轮对话恢复。
- 不接入 LangSmith 实验平台。
- 不接入 CI。

这一节只回答一个问题：

```text
这条输入有没有走过正确的一组节点？
```

## 一、基础知识铺垫

### 1. 什么是 Agent

在本项目里，Agent 不是单纯的聊天机器人。

它更像一个会做流程决策的程序。

它收到用户消息后，不是直接生成一句话就结束。

它可能要做这些事：

```text
清洗输入
识别意图
查询知识库
判断是否需要工单
抽取工单字段
追问缺失字段
请求用户确认
拒绝不支持请求
直接回答问候
```

这些动作组合起来，就是一个 Agent 流程。

### 2. 什么是节点

节点就是 Agent 流程里的一个处理步骤。

在我们的 Ticket Agent 里，常见节点有：

```text
normalize_user_input
classify_intent
retrieve_policy
decide_ticket_need
query_order
extract_ticket_fields
ask_missing_ticket_fields
request_ticket_confirmation
build_direct_answer
build_unsupported_answer
ask_clarifying_question
```

你可以把节点理解成流水线上的一站。

每个节点负责一件相对清楚的事情。

例如：

```text
normalize_user_input
```

负责清理用户输入。

```text
classify_intent
```

负责判断意图。

```text
retrieve_policy
```

负责查政策知识库。

```text
extract_ticket_fields
```

负责抽取工单字段。

### 3. 什么是边

边表示一个节点执行完以后，下一步走到哪里。

例如：

```text
normalize_user_input -> classify_intent
```

这是一条固定边。

意思是：

```text
清洗输入之后，一定进入意图识别。
```

再比如：

```text
retrieve_policy -> decide_ticket_need
```

意思是：

```text
查完政策后，要判断是否需要创建工单。
```

节点是步骤。

边是步骤之间的连接。

### 4. 什么是固定边

固定边就是一定会走的边。

在当前 Agent 里：

```text
START -> normalize_user_input
normalize_user_input -> classify_intent
retrieve_policy -> decide_ticket_need
query_order -> END
build_direct_answer -> END
build_unsupported_answer -> END
ask_clarifying_question -> END
```

这些边基本不需要做复杂判断。

只要到了这个节点，下一步就是固定方向。

### 5. 什么是条件边

条件边就是根据状态判断下一步走哪里。

例如 `classify_intent` 之后：

```text
policy_question -> retrieve_policy
order_query -> query_order
ticket_request -> decide_ticket_need
smalltalk -> build_direct_answer
unsupported -> build_unsupported_answer
unclear -> ask_clarifying_question
```

这就是条件边。

同一个节点执行完，可能去不同的下游节点。

条件边是 Agent 路由的核心。

### 6. 什么是路由

路由就是：

```text
根据当前状态选择下一步节点。
```

例如：

```text
intent = order_query
```

路由结果应该是：

```text
query_order
```

再比如：

```text
ticket_fields_complete = False
```

路由结果应该是：

```text
ask_missing_ticket_fields
```

路由不是回答用户的话。

路由是程序控制流。

### 7. 什么是 node_history

`node_history` 是当前 Agent 记录的节点执行历史。

例如：

```text
["normalize_user_input", "classify_intent", "query_order"]
```

表示这次请求依次走过：

```text
normalize_user_input
-> classify_intent
-> query_order
```

这个字段对教学和调试非常重要。

没有 `node_history`，你只能看到最后回答。

有了 `node_history`，你能看到 Agent 背后实际走了哪些步骤。

### 8. 为什么只看最终回答不够

假设用户问：

```text
退款多久到账？
```

Agent 最终回答：

```text
退款一般需要按售后规则处理。
```

看起来好像还可以。

但它背后的路径可能是：

```text
normalize_user_input
-> classify_intent
-> retrieve_policy
-> decide_ticket_need
-> extract_ticket_fields
-> request_ticket_confirmation
```

这就有问题。

用户只是问政策，不一定要创建工单。

如果 Agent 多走到了工单确认，就说明路由有问题。

所以不能只看最终回答。

### 9. 为什么 intent 对了还不够

第 4 节评测的是：

```text
actual_intent == expected_intent
```

但 intent 对了，后面仍然可能走错。

本节预检就发现过一个典型问题：

```text
用户：账号有异常登录提醒，我应该怎么处理？
```

意图识别结果是：

```text
policy_question
```

这一步是对的。

但 fake RAG 原来没有覆盖“异常登录”，导致它返回 no-context。

于是实际路径变成：

```text
normalize_user_input
-> classify_intent
-> retrieve_policy
-> decide_ticket_need
-> extract_ticket_fields
-> request_ticket_confirmation
```

期望路径其实应该是：

```text
normalize_user_input
-> classify_intent
-> retrieve_policy
-> decide_ticket_need
```

这说明：

```text
intent 对了，但后续路由错了。
```

所以需要路由 eval。

### 10. 为什么字段对了也还要看路径

第 5 节评测字段。

字段评测看：

```text
issue_type
order_id
urgency
missing_ticket_fields
confirmation_required
```

但字段对了，不代表流程一定完整。

例如一个错误实现可能直接调用：

```text
extract_ticket_fields
```

跳过：

```text
decide_ticket_need
```

字段可能仍然看起来对，但流程缺少必要判断。

再比如：

```text
extract_ticket_fields
-> request_ticket_confirmation
```

如果中间本该先判断缺字段却跳过，也是不安全的。

所以字段 eval 和路由 eval 是互补的。

### 11. 什么是 expected node path

`expected node path` 是我们期望 Agent 走过的节点列表。

例如订单查询：

```text
normalize_user_input
-> classify_intent
-> query_order
```

例如普通问候：

```text
normalize_user_input
-> classify_intent
-> build_direct_answer
```

例如完整工单：

```text
normalize_user_input
-> classify_intent
-> decide_ticket_need
-> extract_ticket_fields
-> request_ticket_confirmation
```

expected node path 是路由 eval 的正确答案。

### 12. 什么是 actual node path

`actual node path` 是 Agent 实际运行出来的 `node_history`。

例如：

```text
actual_node_path:
normalize_user_input
-> classify_intent
-> retrieve_policy
-> decide_ticket_need
```

路由 eval 会把：

```text
expected_node_path
```

和：

```text
actual_node_path
```

做比较。

### 13. 什么是 path exact match

`path exact match` 表示路径完全匹配。

要求：

```text
节点数量一样
节点顺序一样
每个节点名字一样
```

例如：

```text
expected:
normalize_user_input -> classify_intent -> query_order

actual:
normalize_user_input -> classify_intent -> query_order
```

这是 exact match。

如果 actual 多了一个节点：

```text
normalize_user_input -> classify_intent -> query_order -> request_ticket_confirmation
```

就不是 exact match。

如果 actual 少了一个节点：

```text
normalize_user_input -> query_order
```

也不是 exact match。

如果顺序错了：

```text
classify_intent -> normalize_user_input -> query_order
```

也不是 exact match。

### 14. 什么是 required nodes

`required nodes` 是这条样本必须经过的节点。

在本节里，required nodes 默认就是 expected path 里的所有节点。

例如完整工单：

```text
normalize_user_input
classify_intent
decide_ticket_need
extract_ticket_fields
request_ticket_confirmation
```

如果 actual path 少了：

```text
extract_ticket_fields
```

那就是缺少 required node。

### 15. 什么是 forbidden nodes

`forbidden nodes` 是这条样本不应该经过的节点。

例如普通问候：

```text
用户：你好，你能做什么？
```

期望路径：

```text
normalize_user_input
-> classify_intent
-> build_direct_answer
```

它不应该经过：

```text
retrieve_policy
query_order
extract_ticket_fields
request_ticket_confirmation
create_ticket
```

这些就是 forbidden nodes。

如果问候消息进入了 `query_order`，说明路由明显错了。

### 16. 什么是 terminal node

`terminal node` 是这条路径的最后一个节点。

例如：

```text
normalize_user_input
-> classify_intent
-> build_unsupported_answer
```

terminal node 是：

```text
build_unsupported_answer
```

终止节点很重要。

因为它代表这条请求最终停在哪里。

例如不支持请求应该停在：

```text
build_unsupported_answer
```

如果它停在：

```text
retrieve_policy
```

就说明安全边界有问题。

### 17. 路由 eval 和传统单元测试的区别

传统单元测试可能会测试：

```text
route_by_intent({"intent": "order_query"}) == "order_query"
```

这有价值。

但它只测试一个函数。

路由 eval 测的是：

```text
真实用户输入
-> 完整 Agent 执行
-> 实际 node_history
-> 和 expected path 比较
```

它更接近用户请求真实经过的流程。

### 18. 路由 eval 和意图 eval 的区别

意图 eval 看：

```text
expected_intent vs actual_intent
```

路由 eval 看：

```text
expected_node_path vs actual_node_path
```

意图 eval 只判断分类标签。

路由 eval 判断流程控制。

### 19. 路由 eval 和字段 eval 的区别

字段 eval 看：

```text
字段值是否正确
```

路由 eval 看：

```text
节点流程是否正确
```

例如同一条工单请求：

```text
订单 A1002 三天没有物流更新了，我很着急，请帮我创建工单催一下
```

字段 eval 关心：

```text
issue_type 是否是 logistics
order_id 是否是 A1002
urgency 是否是 high
```

路由 eval 关心：

```text
是否走了 decide_ticket_need
是否走了 extract_ticket_fields
是否走了 request_ticket_confirmation
有没有误走 query_order
```

### 20. 为什么路由 eval 对 Agent 特别重要

普通 LLM 问答主要看回答质量。

Agent 不一样。

Agent 会调用工具、查库、创建业务对象、触发确认流程。

它更像一个控制系统。

控制系统最怕走错流程。

比如：

```text
用户问候 -> 误调用订单工具
用户问政策 -> 误进入工单创建
用户投诉缺订单号 -> 跳过追问直接确认
提示词注入 -> 误进入普通政策问答
```

这些问题不是回答文案的小问题。

它们是流程安全问题。

## 二、本节主题系统讲解

### 1. 本节新增了什么

本节新增：

```text
projects/ai-service/app/agents/route_evaluation.py
projects/ai-service/scripts/agent_route_eval.py
projects/ai-service/tests/test_agent_route_evaluation.py
notes/stage6-06-agent-route-evaluation.md
```

本节修改：

```text
projects/ai-service/app/agents/ticket_agent.py
```

修改内容很小：

```text
FakePolicyRagService 增加“异常登录/身份验证”的账号安全命中。
```

这是路由预检发现的问题。

### 2. 为什么要补 FakePolicyRagService

上一节样本里有：

```text
账号有异常登录提醒，我应该怎么处理？
```

expected 是：

```text
intent: policy_question
ticket.should_create_ticket: false
```

这表示：

```text
它应该作为账号安全政策问题回答，不应该创建工单。
```

但修正前 fake RAG 只识别：

```text
账号安全
```

不识别：

```text
异常登录
```

所以它返回 no-context，导致 Agent 多走到了：

```text
extract_ticket_fields
request_ticket_confirmation
```

这就是路由错误。

修正后，“异常登录/身份验证”也能命中账号安全假数据，流程回到正确路径：

```text
normalize_user_input
-> classify_intent
-> retrieve_policy
-> decide_ticket_need
```

### 3. 本节路由 eval 的完整链路

本节完整链路是：

```text
读取 agent_cases.json
-> 对每条 case 推导 expected_node_path
-> 运行 run_ticket_agent(message)
-> 读取 actual node_history
-> 比较 exact path
-> 检查 required nodes
-> 检查 forbidden nodes
-> 检查 terminal node
-> 汇总 route_pass_rate / exact_match_rate
-> 输出 bad cases
```

这就是路由 eval 的骨架。

### 4. expected_node_path 从哪里来

本节没有修改 `agent_cases.json`。

而是根据已有 expected 推导路径。

例如：

```text
expected.intent = order_query
```

得到：

```text
normalize_user_input
-> classify_intent
-> query_order
```

如果：

```text
expected.intent = ticket_request
expected.ticket.missing_ticket_fields = []
expected.ticket.confirmation_required = true
```

得到：

```text
normalize_user_input
-> classify_intent
-> decide_ticket_need
-> extract_ticket_fields
-> request_ticket_confirmation
```

如果：

```text
expected.intent = ticket_request
expected.ticket.missing_ticket_fields = ["order_id"]
```

得到：

```text
normalize_user_input
-> classify_intent
-> decide_ticket_need
-> extract_ticket_fields
-> ask_missing_ticket_fields
```

### 5. 为什么暂时不把 node_path 写进 JSON

把 `expected_node_path` 直接写进 JSON 也可以。

但这一节暂时不这么做。

原因是当前样本已经有足够信息推导路径：

```text
intent
ticket.should_create_ticket
ticket.missing_ticket_fields
ticket.confirmation_required
```

如果现在每条样本再手写 node path，会增加重复信息。

重复信息有维护成本。

例如你以后改了路由节点名，就要同时改代码和 JSON。

所以本节先用推导方式。

后面如果路由变复杂，推导规则不够表达，再考虑把 expected node path 显式写进样本。

### 6. 当前 12 条样本的路径覆盖

当前路由 eval 覆盖 12 条样本：

政策已回答：

```text
normalize_user_input
-> classify_intent
-> retrieve_policy
-> decide_ticket_need
```

政策无上下文转工单：

```text
normalize_user_input
-> classify_intent
-> retrieve_policy
-> decide_ticket_need
-> extract_ticket_fields
-> request_ticket_confirmation
```

订单查询：

```text
normalize_user_input
-> classify_intent
-> query_order
```

完整工单：

```text
normalize_user_input
-> classify_intent
-> decide_ticket_need
-> extract_ticket_fields
-> request_ticket_confirmation
```

缺字段工单：

```text
normalize_user_input
-> classify_intent
-> decide_ticket_need
-> extract_ticket_fields
-> ask_missing_ticket_fields
```

闲聊：

```text
normalize_user_input
-> classify_intent
-> build_direct_answer
```

不清楚：

```text
normalize_user_input
-> classify_intent
-> ask_clarifying_question
```

不支持/安全边界：

```text
normalize_user_input
-> classify_intent
-> build_unsupported_answer
```

### 7. 本节为什么用 exact match

本节要求：

```text
actual_node_path == expected_node_path
```

原因是当前 Agent 还是教学阶段，流程比较清楚。

严格匹配能帮助你看清楚每个分支。

如果以后 Agent 增加观测节点、缓存节点、审计节点，exact match 可能会太严格。

到那时可以改成：

```text
必须包含 required nodes
不能包含 forbidden nodes
terminal node 必须正确
中间允许一些 harmless nodes
```

但现在先用 exact match，学习最清楚。

### 8. 本节为什么还看 required nodes

exact match 已经很严格了，为什么还要看 required nodes？

因为 bad case 输出要帮助定位。

如果路径失败，只说：

```text
path not equal
```

不够清楚。

如果再输出：

```text
missing_required_nodes=["extract_ticket_fields"]
```

你就知道缺了哪个关键节点。

### 9. 本节为什么还看 forbidden nodes

有些错误不是少走节点，而是多走了不该走的节点。

例如政策问答不该进入：

```text
request_ticket_confirmation
```

如果进入了，这属于危险信号。

所以本节计算：

```text
visited_forbidden_nodes
```

它能告诉你多走了哪些不该走的节点。

### 10. 本节为什么还看 terminal node

terminal node 是最后停在哪。

有时中间节点都差不多，但最后节点错了，业务结果就错了。

例如提示词注入应该停在：

```text
build_unsupported_answer
```

如果停在：

```text
retrieve_policy
```

就说明安全边界失守。

所以 terminal node 要单独看。

## 三、新增代码讲解

### 1. `route_evaluation.py` 的定位

新增文件：

```text
projects/ai-service/app/agents/route_evaluation.py
```

它是路由 eval 的核心模块。

它不是业务节点，也不是 API。

它负责：

```text
根据样本 expected 推导路径
运行 Agent
比较 expected path 和 actual path
汇总指标
格式化报告
```

### 2. `COMMON_ENTRY_NODES`

代码里有：

```python
COMMON_ENTRY_NODES = ["normalize_user_input", "classify_intent"]
```

这表示当前所有用户请求都会先经过：

```text
normalize_user_input
classify_intent
```

这是所有路径的共同开头。

把它抽出来，可以减少重复。

### 3. `ALL_AGENT_ROUTE_NODES`

这个集合列出了当前 Agent 可能出现的路由节点。

例如：

```text
retrieve_policy
query_order
extract_ticket_fields
request_ticket_confirmation
build_unsupported_answer
```

它的作用是帮助计算 forbidden nodes。

如果某条 expected path 不包含某个节点，那么这个节点对这条 case 来说就是 forbidden node。

### 4. `AgentRouteEvalCaseResult`

这个模型表示单条路由评测结果。

它保存：

```text
case_id
message
expected_intent
actual_intent
expected_node_path
actual_node_path
expected_terminal_node
actual_terminal_node
required_nodes
missing_required_nodes
forbidden_nodes
visited_forbidden_nodes
unexpected_nodes
path_exact_match
required_nodes_passed
forbidden_nodes_passed
terminal_node_passed
passed
failed_reasons
```

这比只返回 true/false 有用得多。

它能说明路由到底错在哪里。

### 5. `AgentRouteEvalSummary`

这个模型表示整体报告。

它保存：

```text
case_count
passed_case_count
failed_case_count
route_pass_rate
exact_match_count
exact_match_rate
required_nodes_passed_count
forbidden_nodes_passed_count
terminal_node_passed_count
p0_route_pass_rate
```

这让你能从整体上看路由质量。

### 6. `build_expected_node_path()`

这是本节最重要的函数之一。

它根据样本 expected 推导路径。

例如：

```python
if intent == "order_query":
    return COMMON_ENTRY_NODES + ["query_order"]
```

这表示订单查询的路径固定是：

```text
normalize_user_input
-> classify_intent
-> query_order
```

再比如：

```python
if intent == "ticket_request":
    path = COMMON_ENTRY_NODES + ["decide_ticket_need"]
    path += _expected_ticket_tail(expected_ticket)
    return path
```

这里工单请求还要看：

```text
missing_ticket_fields
confirmation_required
```

来决定后续是追问还是确认。

### 7. `_expected_ticket_tail()`

这个函数负责推导工单后半段路径。

如果缺字段：

```text
extract_ticket_fields
-> ask_missing_ticket_fields
```

如果字段完整并需要确认：

```text
extract_ticket_fields
-> request_ticket_confirmation
```

如果没有缺字段也没有确认要求：

```text
extract_ticket_fields
```

当前样本主要用前两种。

### 8. `evaluate_agent_route_case()`

这是单条 route eval 的核心。

流程是：

```text
运行 Agent
读取 node_history
构造 expected_node_path
计算 forbidden_nodes
计算 missing_required_nodes
计算 visited_forbidden_nodes
计算 terminal node
判断是否通过
```

核心比较是：

```python
path_exact_match = actual_node_path == expected_node_path
```

同时还计算：

```text
required_nodes_passed
forbidden_nodes_passed
terminal_node_passed
```

这些指标帮助诊断失败。

### 9. `evaluate_agent_route_cases()`

这个函数对所有样本批量评测。

当前会评测 12 条样本。

它汇总：

```text
route_pass_rate
exact_match_rate
p0_route_pass_rate
```

本节结果都是：

```text
1.0000
```

### 10. `format_agent_route_bad_cases()`

这个函数负责输出坏样本。

如果没有坏样本：

```text
No bad cases.
```

如果有坏样本，会输出：

```text
Bad cases:
- case_id ...
  expected_path: ...
  actual_path: ...
  - missing_required_nodes=...
  - visited_forbidden_nodes=...
```

它的目标是让你一眼看出：

```text
少走了什么
多走了什么
最后停在哪里
```

### 11. `agent_route_eval.py`

新增脚本：

```text
projects/ai-service/scripts/agent_route_eval.py
```

运行方式：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run python scripts/agent_route_eval.py
```

它会读取：

```text
data/agent_eval/agent_cases.json
```

然后输出路由 eval 报告。

### 12. `test_agent_route_evaluation.py`

新增测试：

```text
projects/ai-service/tests/test_agent_route_evaluation.py
```

测试覆盖：

- policy answered case 的 expected path。
- no-context 转工单 case 的 expected path。
- 缺字段工单 case 的 expected path。
- 闲聊和安全边界的 expected path。
- 账号安全政策问题实际路径。
- 12 条样本全部路由通过。
- 多走 forbidden node 时能失败。
- 少走 required node 时能失败。
- summary 和 bad cases 输出可读。

这不是简单断言，而是在验证路由 eval 机制本身。

## 四、本节修改代码讲解

### 1. 修改位置

本节修改了：

```text
projects/ai-service/app/agents/ticket_agent.py
```

具体是 `FakePolicyRagService` 的账号安全匹配。

修正前只覆盖：

```text
账号安全
```

修正后覆盖：

```text
账号安全
异常登录
身份验证
```

### 2. 为什么这段代码值得讲

这段代码不是为了大改 RAG。

它的学习价值是：

```text
路由 eval 能发现 intent eval 发现不了的问题。
```

账号异常登录 case 的 intent 是对的。

但 fake RAG 没命中，导致后续路由错了。

这说明：

```text
只评测 intent 不足以保证流程正确。
```

### 3. 为什么不是在路由 eval 里放宽

我们没有说：

```text
账号安全问题多走到工单也算通过。
```

因为 expected 明确写了：

```text
ticket.should_create_ticket: false
```

如果知识库应该能回答，就不应该创建工单。

所以正确修复是补 fake RAG 覆盖，而不是放宽 eval。

这是很重要的判断：

```text
如果 eval 暴露的是代码问题，就修代码。
如果 eval 暴露的是 expected 写错，才修数据集。
```

## 五、本节运行结果

手动运行：

```powershell
uv run python scripts/agent_route_eval.py
```

输出：

```text
Agent route evaluation summary
cases: 12
passed_cases: 12
failed_cases: 0
route_pass_rate: 1.0000
exact_match_count: 12
exact_match_rate: 1.0000
required_nodes_passed_count: 12
forbidden_nodes_passed_count: 12
terminal_node_passed_count: 12
p0_cases: 10
p0_passed_cases: 10
p0_failed_cases: 0
p0_route_pass_rate: 1.0000
No bad cases.
```

相关测试：

```powershell
uv run pytest tests/test_agent_route_evaluation.py tests/test_agent_field_evaluation.py tests/test_agent_intent_evaluation.py tests/test_ticket_agent_intent.py -q
```

结果：

```text
120 passed
```

## 六、怎么阅读路由 eval 输出

### `cases: 12`

表示本节路由 eval 使用全部 12 条样本。

因为每条样本都应该有一条 Agent 路径。

### `passed_cases: 12`

表示 12 条样本的路由全部通过。

### `route_pass_rate: 1.0000`

表示路由通过率是 100%。

### `exact_match_count: 12`

表示 12 条样本 actual path 都和 expected path 完全一致。

### `required_nodes_passed_count: 12`

表示每条样本的必要节点都经过了。

### `forbidden_nodes_passed_count: 12`

表示每条样本都没有经过不该经过的节点。

### `terminal_node_passed_count: 12`

表示每条样本最终停留的节点都正确。

### `p0_route_pass_rate: 1.0000`

表示 P0 样本路由全部通过。

路由 eval 里 P0 尤其重要。

因为 P0 往往涉及：

```text
安全边界
工具调用
工单确认
核心业务流程
```

## 七、常见误区

### 误区 1：intent 对了，路由一定对

不一定。

意图只是入口判断。

后续 RAG、ticket_need、field_complete 都可能继续影响路径。

### 误区 2：最终回答看起来对，路径就一定对

不一定。

路径可能多走了不该走的节点。

例如用户只是问政策，却进入了工单确认。

### 误区 3：路由 eval 只适合 LangGraph

不是。

任何 Agent 只要有流程节点，都可以做路由 eval。

即使你不用 LangGraph，也可以记录步骤列表，然后比较 expected path。

### 误区 4：exact match 永远是最佳方式

不是。

当前阶段流程简单，所以 exact match 很清楚。

未来如果有日志节点、缓存节点、审计节点，可能要改成 required/forbidden 更灵活。

### 误区 5：多走一个节点无所谓

不一定。

如果多走的是只读日志节点，可能影响不大。

但如果多走的是：

```text
request_ticket_confirmation
create_ticket
query_order
```

就可能有业务风险。

### 误区 6：bad case 只看最后节点就行

不够。

有时最后节点正确，但中间绕了不该走的节点。

所以本节同时看：

```text
exact path
required nodes
forbidden nodes
terminal node
```

## 八、本节练习

### 练习 1：解释节点和路由

请回答：

```text
节点是什么？路由是什么？
```

参考答案：

```text
节点是 Agent 流程里的一个处理步骤，例如 classify_intent、retrieve_policy、extract_ticket_fields。

路由是根据当前状态选择下一步节点，例如 intent=order_query 时走 query_order，ticket_fields_complete=false 时走 ask_missing_ticket_fields。
```

### 练习 2：判断订单查询路径

用户输入：

```text
帮我查一下订单 A1001 现在是什么状态
```

期望路径是什么？

参考答案：

```text
normalize_user_input
-> classify_intent
-> query_order
```

### 练习 3：判断完整工单路径

用户输入：

```text
订单 A1002 三天没有物流更新了，我很着急，请帮我创建工单催一下
```

期望路径是什么？

参考答案：

```text
normalize_user_input
-> classify_intent
-> decide_ticket_need
-> extract_ticket_fields
-> request_ticket_confirmation
```

### 练习 4：判断缺字段工单路径

用户输入：

```text
我要投诉商家一直不发货，麻烦人工处理
```

期望路径是什么？

参考答案：

```text
normalize_user_input
-> classify_intent
-> decide_ticket_need
-> extract_ticket_fields
-> ask_missing_ticket_fields
```

原因是这条样本缺少订单号，不能进入确认创建。

### 练习 5：解释 forbidden nodes

请回答：

```text
为什么普通问候不应该经过 retrieve_policy 或 query_order？
```

参考答案：

```text
普通问候只需要直接回答助手能力，不需要查知识库，也不需要查询订单。
如果问候经过 retrieve_policy 或 query_order，说明 Agent 误走了业务流程。
这些节点对普通问候来说就是 forbidden nodes。
```

### 练习 6：分析 bad case

假设：

```text
expected_path:
normalize_user_input -> classify_intent -> retrieve_policy -> decide_ticket_need

actual_path:
normalize_user_input -> classify_intent -> retrieve_policy -> decide_ticket_need -> extract_ticket_fields -> request_ticket_confirmation
```

这是什么问题？

参考答案：

```text
actual path 多走了 extract_ticket_fields 和 request_ticket_confirmation。
如果这条样本只是政策问答且 expected 里 should_create_ticket=false，那么这两个节点是 forbidden nodes。
这说明 Agent 把本该直接回答的政策问题误转成了工单确认流程。
```

### 练习 7：手动运行路由 eval

请运行：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run python scripts/agent_route_eval.py
```

重点看哪些指标？

参考答案：

```text
重点看：

cases
passed_cases
failed_cases
route_pass_rate
exact_match_rate
required_nodes_passed_count
forbidden_nodes_passed_count
terminal_node_passed_count
p0_route_pass_rate
bad cases

如果 failed_cases 大于 0，要继续看 expected_path、actual_path 和 failed_reasons。
```

## 九、自测题

### 自测 1：什么是 node_history？

答案：

```text
node_history 是 Agent 实际执行过的节点列表，用来观察一次请求背后走过哪些流程节点。
```

### 自测 2：什么是 expected node path？

答案：

```text
expected node path 是我们根据样本 expected 推导出的期望节点路径。
```

### 自测 3：什么是 actual node path？

答案：

```text
actual node path 是 Agent 实际运行后从 node_history 里得到的节点路径。
```

### 自测 4：path exact match 要求什么？

答案：

```text
要求 expected node path 和 actual node path 的节点数量、顺序、名字都完全一致。
```

### 自测 5：为什么要看 required nodes？

答案：

```text
required nodes 能告诉我们路径中是否缺少必须经过的关键节点。
```

### 自测 6：为什么要看 forbidden nodes？

答案：

```text
forbidden nodes 能告诉我们 Agent 是否多走了不该走的节点，例如问候误走订单查询、政策问答误走工单确认。
```

### 自测 7：terminal node 为什么重要？

答案：

```text
terminal node 表示流程最终停在哪里。最终节点错误通常意味着业务结果错误，例如安全请求没有停在 build_unsupported_answer。
```

### 自测 8：为什么账号异常登录 case 能说明路由 eval 的价值？

答案：

```text
因为它的 intent 可以是正确的 policy_question，但如果 RAG 没命中账号安全资料，就会继续走到 no-context 工单确认。
这说明 intent 对不代表完整路径对，路由 eval 能抓到这种问题。
```

### 自测 9：路由 eval 和字段 eval 有什么区别？

答案：

```text
路由 eval 看节点流程是否正确。
字段 eval 看工单字段值是否正确。
它们分别检查流程控制和结构化数据质量。
```

### 自测 10：本节最重要的工程思想是什么？

答案：

```text
复杂 Agent 不能只评测最终回答或意图标签，还要评测实际执行路径。
通过 expected path 和 actual node_history 对比，可以发现多走、少走、终止节点错误等流程问题。
```

## 十、本节你应该形成的表达能力

你可以这样向别人解释本节：

```text
我们为智能工单 Agent 增加了路由评测。
它会读取固定 agent_cases.json，根据每条样本的 expected intent、ticket.should_create_ticket、missing_ticket_fields 和 confirmation_required 推导 expected node path。
然后运行完整 Agent，拿到实际 node_history，比较 actual node path 是否和 expected node path 完全一致。
同时还检查 required nodes、forbidden nodes 和 terminal node。
这样可以发现 intent 正确但后续流程走错的问题，比如政策问题误进入工单确认。
```

如果能把这段话讲清楚，说明你已经理解了路由 eval 的核心意义。

## 十一、本节小结

本节完成了阶段 6 第三类真实 eval：

```text
Agent 路由评测
```

当前结果：

```text
12 条样本全部通过
exact_match_rate = 1.0000
P0 路由通过率 = 1.0000
没有 bad cases
```

本节最重要的知识是：

```text
intent 是入口判断
字段是结构化参数
路由是流程控制
node_history 是观察实际路径的依据
route eval 能发现多走、少走、终止节点错误
```

下一节会继续组合前面能力，学习：

```text
RAG + Agent 组合评测
```

## 十二、参考资料

- [阶段 6 第 3 节：设计 Agent 测试集](stage6-03-agent-eval-dataset-design.md)
- [阶段 6 第 4 节：意图识别评测](stage6-04-agent-intent-evaluation.md)
- [阶段 6 第 5 节：工单字段提取评测](stage6-05-agent-ticket-field-evaluation.md)
- [LangSmith Evaluation Concepts](https://docs.langchain.com/langsmith/evaluation-concepts)
- [LangGraph Persistence / Memory](https://docs.langchain.com/oss/python/langgraph/persistence)
- [pytest 官方文档](https://docs.pytest.org/)
