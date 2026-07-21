# 阶段 5 第 14 节：意图识别节点

## 本节定位

上一节我们完成了智能工单 Agent v1 的总流程设计。

从这一节开始，我们正式把设计落到代码里。

第 14 节实现第一个真正的智能工单 Agent 业务节点：

```text
classify_intent
```

也就是：

```text
意图识别节点
```

用户发来一句话后，Agent 不能马上查知识库，也不能马上查订单，更不能马上创建工单。

它必须先回答一个问题：

```text
用户到底想做什么？
```

用户可能在问：

```text
退款规则是什么？
我的订单 1001 到哪了？
我要投诉订单 1001
你好，你能做什么？
帮我直接退款到账
这个怎么办？
```

这些句子看起来都是“用户输入”，但后续路线完全不同。

所以本节要做的是：

```text
把用户自然语言输入分类成固定的业务意图。
```

本节不会真实调用大模型。

本节先实现一个确定性的规则分类器。

原因是：

```text
学习阶段先把 State、node、route、edge、测试结构打稳。
```

等结构稳定后，后面再把规则分类替换成：

```text
LLM structured output
```

这样你能清楚知道：

```text
什么是 Agent 流程本身。
什么是模型能力。
```

## 本节学习目标

学完本节，你应该能解释清楚：

1. 什么是意图识别。
2. 为什么智能工单 Agent 要先做意图识别。
3. 本项目 v1 先定义哪些 intent。
4. `policy_question`、`order_query`、`ticket_request` 分别是什么意思。
5. `smalltalk`、`unsupported`、`unclear` 为什么也要设计。
6. 规则分类和 LLM 分类的区别。
7. 为什么本节先用规则分类器。
8. `TicketAgentState` 里为什么要保存 `intent` 和 `intent_reason`。
9. `classify_intent_node` 应该返回什么。
10. `route_by_intent` 为什么是 routing function，不是业务节点。
11. `TICKET_AGENT_INTENT_ROUTES` 怎么把意图映射到后续节点。
12. 为什么本节的 RAG、订单、工单节点只是占位。
13. 如何用测试覆盖意图识别和路由。

## 本节先不学什么

本节暂时不学：

1. 不接真实大模型。
2. 不使用 OpenAI / Qwen structured output。
3. 不真实查询 Qdrant / Milvus。
4. 不真实调用 Java mock 服务。
5. 不真正创建工单。
6. 不实现 checkpoint。
7. 不实现 interrupt。
8. 不做多轮确认恢复。

这些不是跳过。

而是后面按顺序来。

本节只聚焦一件事：

```text
用户输入进来后，Agent 怎么判断下一步应该走哪条路线。
```

## 一、基础知识铺垫

### 1. 什么是意图

意图可以理解成：

```text
用户这句话背后的目的。
```

比如：

```text
退款规则是什么？
```

表面上是一句话。

背后的目的：

```text
询问政策/规则。
```

再比如：

```text
我的订单 1001 到哪了？
```

背后的目的：

```text
查询订单状态。
```

再比如：

```text
我要投诉订单 1001，物流一直不动。
```

背后的目的：

```text
发起售后/投诉/工单处理。
```

这些目的就是 intent。

### 2. 为什么要先识别意图

智能工单 Agent 后面有多条路线：

```text
RAG 知识库回答
订单查询工具
工单字段抽取
直接回答
不支持兜底
追问用户
```

如果不先识别意图，Agent 就不知道该走哪条路线。

错误做法：

```text
所有问题都先查 RAG。
所有问题都先查订单。
所有问题都交给模型自由发挥。
```

这都会出问题。

订单状态不能靠 RAG 猜。

退款规则不需要查订单。

创建工单不能让模型直接执行。

所以意图识别是整个智能工单 Agent 的第一个关键分支点。

### 3. 意图识别不是最终回答

意图识别只回答：

```text
用户想做什么？
```

它不负责：

```text
生成最终答案
查询订单
检索知识库
创建工单
追问缺失字段
```

比如：

```text
用户：我的订单 1001 到哪了？
```

意图识别节点只应该输出：

```python
intent = "order_query"
```

它不应该直接输出：

```text
你的订单正在运输中。
```

因为真实订单状态要通过工具查询。

这就是节点单一职责。

### 4. 规则分类是什么

规则分类就是用明确规则判断意图。

比如：

```text
句子里有“退款规则” -> policy_question
句子里有“订单” -> order_query
句子里有“投诉” -> ticket_request
句子是“你好” -> smalltalk
```

优点：

```text
简单
稳定
可测试
不花 token
不依赖网络
容易解释
```

缺点：

```text
不够灵活
难覆盖复杂表达
容易被关键词误导
需要不断维护规则
```

本节用规则分类，不是因为规则分类最好。

而是因为学习阶段最适合先把流程打稳。

### 5. LLM 分类是什么

LLM 分类就是让大模型判断意图。

比如给模型提示：

```text
请把用户输入分类成：
policy_question / order_query / ticket_request / smalltalk / unsupported / unclear
```

模型返回结构化结果：

```python
{
    "intent": "order_query",
    "reason": "用户询问订单物流状态",
}
```

优点：

```text
能理解更复杂表达
能结合上下文
能输出原因和结构化信息
```

缺点：

```text
有调用成本
有延迟
可能不稳定
需要后端校验
测试不能真实依赖模型
```

后面我们可以把规则分类器替换成 LLM structured output。

但后端仍然要校验：

```text
intent 是否在允许列表里。
```

### 6. 为什么本节先用规则分类器

原因有三个。

第一，自动化测试稳定。

```text
规则分类每次返回一致。
真实模型可能每次略有不同。
```

第二，先学 Agent 结构。

本节重点是：

```text
State -> node -> intent -> route -> next node
```

不是模型 prompt 调优。

第三，后续更容易替换。

只要接口稳定：

```python
classify_ticket_intent(message) -> {"intent": ..., "reason": ...}
```

以后内部换成 LLM，也不影响 LangGraph 主结构。

### 7. 为什么 intent 要是固定集合

本节定义：

```python
TicketIntent = Literal[
    "policy_question",
    "order_query",
    "ticket_request",
    "smalltalk",
    "unsupported",
    "unclear",
]
```

这表示 intent 只能是这六类。

为什么要固定？

因为后续 routing function 需要根据 intent 分支。

如果模型或规则随便返回：

```text
refund_question
logistics_problem
complain_order
random_unknown
```

后端就不知道怎么路由。

所以 Agent 流程必须有固定枚举。

模型可以判断。

但判断结果必须落到后端允许的固定集合里。

### 8. 六类 intent 的含义

`policy_question`：

```text
政策、规则、FAQ、知识库问题。
```

例如：

```text
退款规则是什么？
多久可以退货？
账号安全怎么验证？
```

`order_query`：

```text
订单、物流、支付、发货状态查询。
```

例如：

```text
我的订单 1001 到哪了？
订单支付成功了吗？
```

`ticket_request`：

```text
投诉、售后处理、创建工单、人工处理诉求。
```

例如：

```text
我要投诉订单 1001。
商品坏了，帮我处理。
```

`smalltalk`：

```text
问候或询问助手能力。
```

例如：

```text
你好。
你能做什么？
```

`unsupported`：

```text
超出 v1 范围或不允许自动执行的请求。
```

例如：

```text
帮我直接退款到账。
给我黑客攻击脚本。
```

`unclear`：

```text
表达太模糊，需要追问。
```

例如：

```text
有问题。
这个怎么办？
```

### 9. 为什么需要 intent_reason

本节不仅保存：

```python
intent
```

还保存：

```python
intent_reason
```

原因是：

```text
Agent 不能只知道结果，还要方便调试为什么这么判断。
```

比如：

```python
intent = "order_query"
intent_reason = "用户在询问订单、物流、支付或发货状态。"
```

以后如果分类错了，你可以看：

```text
它为什么这么分类？
是关键词命中了？
是模型判断错了？
是规则顺序不合理？
```

这对学习和调试都很重要。

### 10. 意图识别和路由的关系

意图识别节点写入：

```python
intent = "order_query"
```

路由函数读取：

```python
state["intent"]
```

然后决定下一步：

```text
order_query -> query_order
```

所以流程是：

```text
classify_intent_node 负责判断意图。
route_by_intent 负责根据意图选路。
```

不要把这两件事混在一起。

## 二、本节主题系统讲解

### 1. 本节新增了什么文件

本节新增：

```text
projects/ai-service/app/agents/ticket_agent.py
projects/ai-service/tests/test_ticket_agent_intent.py
```

`ticket_agent.py` 是智能工单 Agent 的起点。

它和前面的 `minimal_graph.py` 不一样。

`minimal_graph.py` 是 LangGraph 基础教学图。

`ticket_agent.py` 是后面要逐步发展成智能工单 Agent v1 的业务图。

### 2. 为什么不继续改 minimal_graph.py

`minimal_graph.py` 的职责是：

```text
教学 LangGraph 基础概念。
```

它已经承担了：

```text
StateGraph
node
edge
conditional edge
START / END
invoke / stream
```

如果继续把智能工单业务塞进去，它会变乱。

所以从第 14 节开始，新建：

```text
ticket_agent.py
```

这样边界清楚：

```text
minimal_graph.py：基础教学图
ticket_agent.py：业务 Agent 图
```

### 3. 本节的图结构

当前图是：

```text
START
  -> normalize_user_input
  -> classify_intent
      -> policy_question -> retrieve_policy -> END
      -> order_query -> query_order -> END
      -> ticket_request -> extract_ticket_fields -> END
      -> smalltalk -> build_direct_answer -> END
      -> unsupported -> build_unsupported_answer -> END
      -> unclear -> ask_clarifying_question -> END
```

注意：

```text
retrieve_policy / query_order / extract_ticket_fields 现在还是占位节点。
```

它们不是最终实现。

它们只是为了让第 14 节的路由图能跑通。

第 15 节开始会逐个替换：

```text
retrieve_policy -> 接入 RAG
query_order -> 接入订单工具
extract_ticket_fields -> 抽取工单字段
```

### 4. TICKET_AGENT_FIXED_EDGES

代码：

```python
TICKET_AGENT_FIXED_EDGES: tuple[tuple[str, str], ...] = (
    (START, "normalize_user_input"),
    ("normalize_user_input", "classify_intent"),
    ("retrieve_policy", END),
    ("query_order", END),
    ("extract_ticket_fields", END),
    ("build_direct_answer", END),
    ("build_unsupported_answer", END),
    ("ask_clarifying_question", END),
)
```

这些是固定边。

意思是：

```text
图从 normalize_user_input 开始。
清洗后固定进入 classify_intent。
每条当前占位路线执行完后，本轮结束。
```

为什么这些路线都先连到 `END`？

因为本节还没有实现后续真实业务节点。

占位节点返回一段说明后，本轮就结束。

### 5. TICKET_AGENT_INTENT_ROUTES

代码：

```python
TICKET_AGENT_INTENT_ROUTES: dict[TicketAgentRoute, str] = {
    "policy_question": "retrieve_policy",
    "order_query": "query_order",
    "ticket_request": "extract_ticket_fields",
    "smalltalk": "build_direct_answer",
    "unsupported": "build_unsupported_answer",
    "unclear": "ask_clarifying_question",
}
```

这张表是本节核心。

它表达：

```text
每种 intent 走哪一个后续节点。
```

这就是第 13 节总流程设计落到代码里的第一步。

### 6. TicketAgentState

代码：

```python
class TicketAgentState(TypedDict, total=False):
    user_message: str
    normalized_message: str
    intent: TicketIntent
    intent_reason: str
    final_answer: str
    node_history: Annotated[list[str], add]
```

当前 State 只有最小字段：

```text
user_message：用户原始输入
normalized_message：清洗后的输入
intent：意图
intent_reason：意图判断原因
final_answer：本轮给用户的回答
node_history：执行过的节点
```

后面会继续加：

```text
order_id
order_result
rag_answer
ticket_fields
missing_fields
confirmation_status
ticket_id
```

现在不提前加，是为了控制复杂度。

### 7. normalize_user_input_node

代码：

```python
def normalize_user_input_node(state: TicketAgentState) -> TicketAgentState:
    user_message = state.get("user_message", "")

    return {
        "normalized_message": user_message.strip(),
        "node_history": ["normalize_user_input"],
    }
```

职责：

```text
清洗用户输入。
```

它只做 `strip()`。

这很简单，但很重要。

比如：

```text
"  退款规则是什么？  "
```

会变成：

```text
"退款规则是什么？"
```

后面的分类节点读取的是清洗后的输入。

### 8. classify_ticket_intent

代码里这个函数是规则分类器：

```python
def classify_ticket_intent(message: str) -> TicketAgentIntentClassification:
    ...
```

它输入一段字符串。

输出：

```python
{
    "intent": "...",
    "reason": "...",
}
```

它不是 LangGraph node。

它是纯业务函数。

为什么要单独拆出来？

因为这样可以直接单测规则分类，不必每次跑完整图。

### 9. classify_intent_node

代码：

```python
def classify_intent_node(state: TicketAgentState) -> TicketAgentState:
    classification = classify_ticket_intent(state.get("normalized_message", ""))

    return {
        "intent": classification["intent"],
        "intent_reason": classification["reason"],
        "node_history": ["classify_intent"],
    }
```

它是 LangGraph node。

职责：

```text
从 State 读取 normalized_message。
调用规则分类器。
把 intent 和 intent_reason 写回 State。
```

它不决定下一步节点。

下一步由：

```text
route_by_intent
```

负责。

### 10. route_by_intent

代码：

```python
def route_by_intent(state: TicketAgentState) -> TicketAgentRoute:
    intent = state.get("intent")
    if intent in TICKET_AGENT_INTENT_ROUTES:
        return intent
    return "unclear"
```

它是 routing function。

职责：

```text
根据 State.intent 返回路线。
```

如果 State 里没有 intent，或者 intent 不合法，就走：

```text
unclear
```

这是保守兜底。

因为意图不明确时，不应该乱查订单或创建工单。

### 11. 占位节点为什么存在

比如：

```python
def query_order_node(state: TicketAgentState) -> TicketAgentState:
    return {
        "final_answer": "已识别为订单查询问题，后续课程会接入 query_order 工具。",
        "node_history": ["query_order"],
    }
```

它现在没有真的查订单。

原因是：

```text
本节只学意图识别和路由。
```

如果本节同时接 RAG、订单工具、工单字段抽取，知识点会太混。

所以占位节点的作用是：

```text
让图能完整运行。
让测试能验证路线。
为后续课程留下稳定节点名。
```

### 12. build_ticket_agent_graph

代码：

```python
def build_ticket_agent_graph():
    builder = StateGraph(TicketAgentState)
    ...
    builder.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        TICKET_AGENT_INTENT_ROUTES,
    )
    return builder.compile()
```

这里把第 13 节设计变成了可运行图。

核心结构：

```text
START -> normalize_user_input -> classify_intent -> conditional route
```

这是智能工单 Agent v1 的第一段主干。

## 三、当前代码逐段讲解

### 1. TicketIntent

```python
TicketIntent = Literal[
    "policy_question",
    "order_query",
    "ticket_request",
    "smalltalk",
    "unsupported",
    "unclear",
]
```

这是意图枚举。

它让你一眼看到：

```text
当前 Agent v1 能识别哪些类别。
```

这个类型以后可以继续扩展。

但每扩展一个 intent，都要同步考虑：

```text
路由表
节点
测试
文档
```

### 2. 关键词常量

本节有：

```python
POLICY_KEYWORDS
ORDER_KEYWORDS
TICKET_KEYWORDS
SMALLTALK_KEYWORDS
UNSUPPORTED_KEYWORDS
UNCLEAR_MESSAGES
```

这些不是最终产品级分类器。

它们是：

```text
v1 学习阶段的确定性规则。
```

它们让测试变得稳定。

也让你能清楚看到：

```text
每个 intent 大概由哪些业务语义触发。
```

### 3. 规则判断顺序

当前顺序是：

```text
空输入
unsupported
smalltalk
ticket_request
order_query
policy_question
unclear
```

顺序很重要。

比如：

```text
我要投诉订单 1001，物流一直不动
```

里面有：

```text
订单
物流
投诉
一直不动
```

如果先判断订单，它可能被分成 `order_query`。

但用户明确说了投诉和处理诉求。

所以本节让 `ticket_request` 优先于 `order_query`。

这体现了业务优先级。

### 4. unsupported 为什么放在前面

比如：

```text
帮我直接退款到账
```

它和客服业务有关。

但它是敏感写操作。

v1 不允许自动执行。

所以先判断 `unsupported`，避免它被误判成普通政策问题或工单请求。

这里体现的是：

```text
安全优先。
```

### 5. route_by_intent 的兜底

如果没有 intent：

```python
route_by_intent({})
```

返回：

```text
unclear
```

这符合安全设计。

未知状态不应该走：

```text
query_order
extract_ticket_fields
create_ticket
```

未知就追问。

### 6. stream_ticket_agent_updates

本节保留了 stream 辅助函数：

```python
def stream_ticket_agent_updates(user_message: str) -> list[TicketAgentStreamPart]:
    return list(
        ticket_agent_graph.stream(
            build_ticket_agent_input(user_message),
            stream_mode="updates",
            version="v2",
        )
    )
```

这是继承第 12 节的学习成果。

它可以观察：

```text
normalize_user_input 更新了什么
classify_intent 更新了什么
最后走到哪个占位节点
```

这对测试路由很有用。

## 四、六类意图详解

### 1. policy_question

适合：

```text
退款规则
退货规则
售后政策
账号安全
FAQ
```

后续路线：

```text
retrieve_policy
```

第 15 节会把它接入 RAG。

关键原则：

```text
规则和政策类问题应该基于知识库回答。
```

不要让模型凭空编造规则。

### 2. order_query

适合：

```text
订单状态
物流状态
支付状态
发货状态
签收状态
```

后续路线：

```text
query_order
```

后面会接：

```text
query_order -> JavaOrderClient -> java-mock-service
```

关键原则：

```text
订单状态是业务数据，不能靠 RAG 或模型猜。
```

### 3. ticket_request

适合：

```text
投诉
创建工单
售后处理
人工处理
商品破损
物流一直不动并要求处理
```

后续路线：

```text
extract_ticket_fields
```

后面会继续：

```text
抽取字段
检查缺失字段
请求用户确认
确认后创建工单
```

关键原则：

```text
创建工单是写操作，必须确认。
```

### 4. smalltalk

适合：

```text
你好
你是谁
你能做什么
```

后续路线：

```text
build_direct_answer
```

这类问题不需要查知识库，也不需要查订单。

### 5. unsupported

适合：

```text
直接退款到账
取消订单
黑客攻击脚本
写小说
股票
天气
```

后续路线：

```text
build_unsupported_answer
```

这里分两种。

第一种是安全问题：

```text
攻击脚本
```

第二种是业务边界问题：

```text
直接退款到账
```

退款规则可以回答。

直接执行退款不在 v1 自动执行范围内。

### 6. unclear

适合：

```text
有问题
这个怎么办
帮我看看
空输入
```

后续路线：

```text
ask_clarifying_question
```

这不是失败。

这是正常追问流程。

## 五、测试设计

### 1. 测固定边

测试：

```python
test_ticket_agent_fixed_edges_define_entry_and_finish_points
```

它确认：

```text
START -> normalize_user_input
normalize_user_input -> classify_intent
各个占位路线 -> END
```

这不是测试 LangGraph。

这是测试我们自己的图结构。

### 2. 测路由表

测试：

```python
test_ticket_agent_intent_routes_map_intent_to_next_node
```

它确认：

```text
policy_question -> retrieve_policy
order_query -> query_order
ticket_request -> extract_ticket_fields
...
```

如果以后有人把 `order_query` 错接到 RAG，测试会失败。

### 3. 测规则分类器

测试：

```python
test_classify_ticket_intent_returns_expected_intent
```

它覆盖：

```text
policy_question
order_query
ticket_request
smalltalk
unsupported
unclear
空输入
```

这是本节最重要的测试之一。

### 4. 测节点输出

测试：

```python
test_classify_intent_node_writes_intent_to_state
```

它确认：

```text
classify_intent_node 会把 intent 和 intent_reason 写入 State。
```

这比只测纯函数更接近 LangGraph 节点行为。

### 5. 测 route_by_intent

测试：

```python
test_route_by_intent_returns_matching_route
test_route_by_intent_defaults_to_unclear
```

它确认：

```text
合法 intent 正常路由。
缺失 intent 走 unclear。
```

### 6. 测完整图路线

测试：

```python
test_run_ticket_agent_routes_to_expected_placeholder_node
```

它确认完整图会走：

```text
normalize_user_input -> classify_intent -> 对应占位节点
```

这是整图主流程测试。

### 7. 测 stream

测试：

```python
test_stream_ticket_agent_updates_exposes_intent_route
```

它确认 stream 里能看到：

```text
normalize_user_input
classify_intent
query_order
```

这继承了第 12 节的调试能力。

以后智能工单 Agent 越复杂，stream 测试越重要。

## 六、常见错误

### 1. 把意图识别当成最终回答

错误：

```text
classify_intent 直接回答用户订单状态。
```

正确：

```text
classify_intent 只写 intent。
订单状态要由 query_order 节点查询。
```

### 2. intent 没有固定集合

错误：

```text
模型想返回什么就返回什么。
```

正确：

```text
intent 必须落在后端允许的固定集合中。
```

### 3. 缺失 intent 时乱走默认路线

错误：

```text
缺失 intent 默认查订单。
```

正确：

```text
缺失 intent 默认 unclear，追问用户。
```

### 4. 把 RAG 和订单查询混在一起

错误：

```text
订单状态走 RAG。
```

正确：

```text
订单状态走 query_order。
政策规则走 RAG。
```

### 5. 把敏感写操作当成普通工单请求

错误：

```text
帮我直接退款到账 -> ticket_request
```

正确：

```text
直接退款到账是 v1 不支持的敏感操作，应该 unsupported。
```

### 6. 过早接真实大模型

错误：

```text
还没设计好 State 和 route，就先接真实模型分类。
```

正确：

```text
先规则版跑通结构，再替换成 fake LLM / structured output。
```

### 7. 没有写意图测试

意图识别是后续所有路线的入口。

如果它没有测试，后面 RAG、工具、工单路线都会不稳定。

所以本节测试覆盖了六类意图。

## 七、本节练习与参考答案

### 练习 1：什么是意图识别？

参考答案：

意图识别是判断用户输入背后目的的过程。比如用户问“退款规则是什么”，意图是 `policy_question`；用户问“订单 1001 到哪了”，意图是 `order_query`。

### 练习 2：为什么智能工单 Agent 要先识别意图？

参考答案：

因为不同意图要走不同业务路线。政策问题走 RAG，订单问题走订单工具，工单请求走字段抽取和确认流程，不明确问题要追问。

### 练习 3：本节定义了哪六类 intent？

参考答案：

```text
policy_question
order_query
ticket_request
smalltalk
unsupported
unclear
```

### 练习 4：`退款规则是什么？` 应该是什么 intent？

参考答案：

`policy_question`，因为它是政策/规则类知识库问题。

### 练习 5：`我的订单 1001 到哪了？` 应该是什么 intent？

参考答案：

`order_query`，因为它在询问真实订单和物流状态。

### 练习 6：`我要投诉订单 1001` 应该是什么 intent？

参考答案：

`ticket_request`，因为用户表达了投诉或工单处理诉求。

### 练习 7：`帮我直接退款到账` 为什么不是 policy_question？

参考答案：

因为它不是询问退款规则，而是在要求执行敏感写操作。v1 不允许自动退款，所以应该是 `unsupported`。

### 练习 8：`route_by_intent` 是 node 吗？

参考答案：

不是。它是 routing function，用于 conditional edge。它读取 State 里的 `intent`，返回下一条路线。

### 练习 9：为什么本节的 `query_order` 只是占位节点？

参考答案：

因为本节只学习意图识别和路由。真实订单查询会在后续课程接入 `query_order` 工具和 Java mock 服务。

### 练习 10：为什么要测试 stream？

参考答案：

因为 stream 能显示图实际经过哪些节点。意图识别和路由是流程问题，只看最终回答不够，stream 可以验证是否真的走到了预期节点。

## 八、自测题与答案

### 自测 1：意图识别节点写入 State 的核心字段是什么？

答案：

`intent` 和 `intent_reason`。

### 自测 2：`policy_question` 后续路由到哪里？

答案：

`retrieve_policy`。

### 自测 3：`order_query` 后续路由到哪里？

答案：

`query_order`。

### 自测 4：`ticket_request` 后续路由到哪里？

答案：

`extract_ticket_fields`。

### 自测 5：不明确输入后续路由到哪里？

答案：

`ask_clarifying_question`。

### 自测 6：为什么未知 intent 默认走 unclear？

答案：

因为未知状态下不能冒险查订单或创建工单。追问用户是更安全的默认路线。

### 自测 7：本节是否真实调用大模型？

答案：

没有。本节使用规则分类器，保证结构和测试稳定。

### 自测 8：本节是否真实查询订单？

答案：

没有。`query_order` 现在只是占位节点，后续课程才会接入真实工具链。

### 自测 9：为什么 `ticket_agent.py` 和 `minimal_graph.py` 分开？

答案：

`minimal_graph.py` 是 LangGraph 基础教学图，`ticket_agent.py` 是智能工单业务 Agent 图。分开可以保持职责清楚。

### 自测 10：本节最核心的一句话是什么？

答案：

意图识别节点负责把用户输入分类成固定 intent，后续 conditional edge 根据 intent 把 Agent 路由到正确业务路线。

## 九、本节小结

本节完成了智能工单 Agent v1 的第一个业务节点：

```text
classify_intent
```

当前业务图已经可以做到：

```text
用户输入
  -> normalize_user_input
  -> classify_intent
  -> 根据 intent 路由到对应占位节点
  -> END
```

六条路线分别是：

```text
policy_question -> retrieve_policy
order_query -> query_order
ticket_request -> extract_ticket_fields
smalltalk -> build_direct_answer
unsupported -> build_unsupported_answer
unclear -> ask_clarifying_question
```

本节最重要的能力不是关键词规则本身。

而是：

```text
你已经把智能工单 Agent 的第一层分流做成了可运行、可测试、可观察的 LangGraph 图。
```

下一节进入：

```text
阶段 5 第 15 节：RAG 知识库回答节点
```

也就是把：

```text
policy_question -> retrieve_policy
```

这条占位路线替换成真正的知识库回答路线。

## 参考资料

- [LangGraph Thinking in LangGraph](https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph)
  - 用途：参考官方建议的 Agent 构建顺序：先拆离散步骤，再设计 State，再实现 node，并让分类节点决定后续路线。
- [LangGraph Graph API overview](https://docs.langchain.com/oss/python/langgraph/graph-api)
  - 用途：确认 `StateGraph`、node、edge、conditional edge、`START`、`END` 和 routing function 的基本写法。
- [LangGraph Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents)
  - 用途：理解 workflow 与 agent 的边界，明确本项目先采用可控 workflow + 局部 agent 能力。
