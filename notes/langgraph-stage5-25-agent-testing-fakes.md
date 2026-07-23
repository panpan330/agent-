# 阶段 5 第 25 节：LangGraph 测试：fake LLM / fake RAG / fake Java client

## 本节定位

上一节我们把智能工单 Agent 的日志、`trace_id`、`node_history` 和错误兜底补上了。

到这里，Agent 已经不是一个简单函数了。

它现在包含：

```text
用户输入
-> 意图识别
-> RAG 知识库回答
-> 判断是否需要创建工单
-> 提取工单字段
-> 缺字段追问
-> 用户确认
-> interrupt / resume
-> checkpoint / thread_id
-> Java mock 创建工单
-> 节点错误处理
-> 图级 fallback
-> logging / trace_id
```

功能多了以后，测试就不再只是“调用一下函数，看看结果对不对”。

本节要解决的问题是：

```text
怎样测试一个会调用模型、RAG、外部 Java 服务、checkpoint 和 interrupt 的 LangGraph Agent，
同时又不让测试真的依赖模型、向量库、Docker、Java 服务、网络和人工确认？
```

这节的核心不是 pytest 语法本身。

这节真正要学的是：

```text
如何把 Agent 拆成可测试的层次，
如何用 fake 替换不稳定外部依赖，
如何只测当前要验证的行为，
如何保证复杂流程可重复、可定位、可回归。
```

## 本节学习目标

学完本节，你应该能讲清楚：

1. 为什么 Agent 测试比普通接口测试更难。

   答案：因为 Agent 不是单次输入输出，它有多节点、多分支、外部依赖、状态保存、中断恢复和副作用。

2. 什么是 fake LLM、fake RAG、fake Java client。

   答案：它们都是测试替身，用固定、可控、可记录调用的对象替代真实模型、真实检索服务和真实 Java HTTP 服务。

3. fake、stub、mock、spy 的区别。

   答案：stub 主要提供固定返回；spy 主要记录调用；mock 通常还校验调用预期；fake 是可工作的简化实现，可能同时具备 stub 和 spy 能力。

4. 为什么测试里不能默认真实调用大模型。

   答案：真实模型慢、贵、不稳定、有配额限制，输出还可能变化，不适合作为单元测试依赖。

5. 为什么测试里不能默认真实连接 Qdrant、Milvus 或 Java 服务。

   答案：外部服务会引入环境依赖、网络波动、启动顺序、数据状态和清理问题，会让普通测试变慢、变脆。

6. 什么是依赖注入。

   答案：不是在函数内部固定创建依赖，而是允许外部把依赖对象传进来，这样生产环境用真实依赖，测试环境用 fake 依赖。

7. LangGraph 测试可以分哪些层。

   答案：纯函数层、单节点层、路由层、整图路径层、checkpoint 层、interrupt/resume 层、fallback 层、日志层、接口层。

8. 为什么 compiled graph 的 `graph.nodes[...]` 可以用于节点级测试。

   答案：它允许我们只调用某个节点，不必为了验证一个节点而跑完整个图。

9. 为什么 `graph.update_state(..., as_node=...)` 能做局部执行测试。

   答案：它可以把测试状态“放到某个节点刚执行完”的位置，再从那里继续跑后续流程。

10. 为什么每个测试最好使用新的 checkpointer。

    答案：checkpoint 会保存 thread state，如果多个测试共享同一个 checkpointer，状态可能互相污染。

11. 为什么测试要验证错误路径和 fallback。

    答案：Agent 调用外部系统时失败是常态，只测成功路径不能证明系统可控。

12. 为什么日志测试不应该验证完整用户原文。

    答案：日志要可排查，但不能泄露敏感内容，测试应该验证关键字段存在、敏感内容不存在。

## 本节先不学什么

本节先不做：

1. 不接真实大模型测试。
2. 不接真实 embedding 测试。
3. 不启动 Qdrant。
4. 不启动 Milvus。
5. 不启动 Java mock service。
6. 不接 LangSmith 自动评测。
7. 不做 Agent 质量评测数据集。
8. 不做端到端浏览器测试。
9. 不做压测。
10. 不做 CI/CD 测试流水线。

原因很简单：

```text
第 25 节先把“Agent 如何可测试”这件事学透。
真实模型、真实向量库、真实服务属于更高层的集成测试和验收测试，不应该混进基础单元测试。
```

## 一、基础知识铺垫

### 1. 为什么 Agent 测试更难

普通函数通常像这样：

```text
输入 A -> 函数 -> 输出 B
```

例如：

```python
def add(a: int, b: int) -> int:
    return a + b
```

测试它很简单：

```python
assert add(1, 2) == 3
```

但 Agent 流程通常像这样：

```text
输入
-> 节点 1 写入 State
-> 条件边判断去哪个节点
-> 节点 2 调用 RAG
-> 节点 3 判断要不要创建工单
-> 节点 4 可能请求用户确认
-> 图暂停
-> 用户稍后确认
-> 图从 checkpoint 恢复
-> 节点 5 调用 Java 服务
-> 节点 6 写最终结果
```

这里至少有 6 类不确定性：

```text
模型输出不确定
RAG 检索结果不确定
外部 Java 服务状态不确定
checkpoint 状态可能残留
interrupt 需要人工输入
日志和错误路径可能被忽略
```

所以 Agent 测试不能只问：

```text
最终答案是不是某句话？
```

还要问：

```text
它走了哪些节点？
它走的是哪条条件边？
State 里关键字段有没有写对？
外部依赖有没有被调用？
调用参数是不是正确？
失败时有没有进入 fallback？
中断时 State 有没有保存？
恢复时有没有继续到正确节点？
日志里有没有 trace_id？
日志里有没有泄露用户原文？
```

这就是本节测试设计的起点。

### 2. 测试的核心目标不是“覆盖率数字”

覆盖率很重要，但覆盖率不是目标本身。

对 Agent 来说，测试真正要保证的是：

```text
确定性
可重复
可定位
可隔离
可回归
```

确定性：

```text
同一份测试输入，每次都得到同样结果。
```

可重复：

```text
今天、本周、下个月、换一台机器，都能跑。
```

可定位：

```text
测试失败时，能知道是哪个节点、哪条边、哪个依赖出问题。
```

可隔离：

```text
测试一个节点时，不被真实模型、真实数据库、真实网络影响。
```

可回归：

```text
以后改代码时，旧功能如果被破坏，测试能立刻提醒。
```

所以这节不是为了“多写几个测试”。

这节是为了建立一个判断标准：

```text
你的 Agent 到底是不是可控的工程系统。
```

### 3. 单元测试、集成测试、端到端测试

这三个概念一定要分清。

单元测试：

```text
只测试一个小单元。
外部依赖用 fake 替代。
速度快。
失败原因明确。
```

例子：

```text
只测试 classify_intent_node。
只测试 decide_ticket_need。
只测试 FakePolicyRagService 是否记录 queries。
```

集成测试：

```text
测试多个模块组合后能不能工作。
可以用一部分真实依赖，也可以用 fake 依赖。
速度中等。
失败原因需要进一步定位。
```

例子：

```text
用 fake RAG + fake Java client 跑完整 LangGraph 工单流程。
用 httpx.MockTransport 测 Java client 的 HTTP 映射。
```

端到端测试：

```text
尽量模拟真实用户完整链路。
可能需要真实服务、真实数据库、真实配置。
速度慢。
维护成本高。
```

例子：

```text
启动 FastAPI。
启动 Java mock service。
启动 Qdrant。
配置真实或测试 API key。
从接口发请求，最终创建工单。
```

本节重点是前两种：

```text
单元测试 + 轻量集成测试。
```

因为它们适合日常开发中频繁运行。

### 4. fake、stub、mock、spy 到底是什么

这些词经常混着用，但你要知道大概区别。

stub：

```text
提供固定返回值。
重点是“给被测代码喂一个可控结果”。
```

例子：

```python
class StubRagService:
    def answer_policy_question(self, query: str):
        return fixed_answer
```

spy：

```text
记录自己被怎么调用。
重点是“事后检查调用参数”。
```

例子：

```python
class SpyRagService:
    def __init__(self):
        self.queries = []

    def answer_policy_question(self, query: str):
        self.queries.append(query)
        return fixed_answer
```

mock：

```text
通常预先声明期待的调用方式，然后测试过程中校验有没有按期待调用。
Python 里常见的是 unittest.mock.Mock。
```

fake：

```text
一个简化但能工作的替代实现。
它不是真实外部服务，但行为足够像真实依赖。
```

本项目里的 `FakePolicyRagService` 同时具备两种能力：

```text
stub：返回固定 RagAnswer
spy：记录 queries
```

本项目里的 `FakeTicketCreator` 也同时具备：

```text
stub：返回固定 CreatedTicket
spy：记录 CreateTicketArgs 和 idempotency_key
error fake：可以配置抛出异常
```

你可以这样理解：

```text
fake 是可控的假服务。
stub 是固定返回。
spy 是记录调用。
mock 是带预期校验的替身。
```

### 5. 为什么不能在单元测试里真实调用大模型

真实模型调用的问题很多：

```text
慢
贵
有网络依赖
有 API key 依赖
可能限流
输出可能变化
供应商可能升级模型
同一句 prompt 不一定每次完全相同
失败时很难判断是代码坏了还是模型服务波动
```

所以单元测试里应该使用 fake LLM。

fake LLM 的目标不是“模拟模型所有能力”。

它的目标是：

```text
在测试中稳定返回我们指定的模型结果。
```

比如：

```text
输入：我要投诉订单 A1001
fake LLM 固定返回：intent=complaint, order_id=A1001, urgency=high
```

这样我们测试的就不是“模型今天聪不聪明”，而是：

```text
后端拿到结构化结果后，是否正确进入工单确认和创建流程。
```

本项目之前在阶段 2、阶段 3、阶段 4 已经多次使用了 fake LLM 思想。
本节把这个思想放进 LangGraph Agent 测试体系里。

### 6. 为什么不能在单元测试里真实连接 RAG

RAG 依赖很多层：

```text
文档
chunk
embedding
向量库
top_k
score_threshold
filter
rerank
生成回答
引用来源
无资料兜底
```

真实 RAG 测试容易受这些因素影响：

```text
向量库是否启动
collection 是否存在
数据是否已经入库
embedding 维度是否匹配
检索分数是否变化
top_k 是否改过
文档内容是否更新
```

如果我们只是想测试 Agent 路由：

```text
RAG answered -> 不创建工单
RAG no_context -> 进入工单流程
```

那就不应该真的连向量库。

我们只需要 fake RAG 返回两种稳定结果：

```text
answered
no_context
```

这样测试关注点就非常清楚：

```text
Agent 如何处理 RAG 结果。
```

而不是：

```text
向量检索质量好不好。
```

检索质量属于阶段 4 的评测问题。
Agent 流程测试不应该和它绑死。

### 7. 为什么不能在单元测试里真实调用 Java 服务

Java 服务属于外部业务系统。

它可能有：

```text
HTTP 网络
端口占用
启动顺序
数据库
鉴权
超时
幂等
数据状态
```

如果每次测试都真实调用 Java 服务，测试会变得很慢，也很容易失败。

在 Agent 单元测试里，我们应该用 fake Java client：

```text
FakeTicketCreator
```

它能做三件事：

```text
返回固定 CreatedTicket
记录传入的 CreateTicketArgs
记录传入的 idempotency_key
模拟创建失败
```

这样我们可以验证：

```text
只有用户确认后才调用 create_ticket
传给 Java 的字段映射正确
幂等键被传入
Java 失败时 Agent 进入安全 fallback
```

这些才是 Agent 需要负责的边界。

### 8. 什么是依赖注入

依赖注入就是：

```text
不要在被测函数内部把外部依赖写死。
把依赖作为参数传进来。
```

不容易测试的写法：

```python
def retrieve_policy_node(state):
    service = RealPolicyRagService()
    return service.answer_policy_question(state["query"])
```

这种写法的问题是：

```text
测试时很难替换 RealPolicyRagService。
```

更适合测试的写法：

```python
def retrieve_policy_node(state, service=None):
    rag_service = service or create_policy_rag_service()
    return rag_service.answer_policy_question(state["query"])
```

这表示：

```text
生产环境不传 service，用默认真实或学习版服务。
测试环境传 fake service。
```

本节在 `build_ticket_agent_graph()` 里补了同样的能力：

```python
def build_ticket_agent_graph(
    ticket_creator: TicketCreator | None = None,
    *,
    policy_rag_service: PolicyRagService | None = None,
    checkpointer: Any | None = None,
    interrupt_confirmation: bool = False,
):
```

这样整张图也能注入 fake RAG。

### 9. 为什么 graph 也要能注入依赖

单独测节点时，我们可以这样传 fake：

```python
retrieve_policy_node(state, service=fake_rag)
```

但整图测试时，节点是由 LangGraph 调用的。

我们不会直接调用 `retrieve_policy_node()`。

我们调用的是：

```python
graph.invoke(initial_state)
```

所以 fake 不能只传给单个节点。

我们要在构建图时就把 fake 绑定进去：

```python
graph = build_ticket_agent_graph(policy_rag_service=fake_rag)
```

然后图里的 `retrieve_policy` 节点执行时，会使用这个 fake：

```python
builder.add_node(
    "retrieve_policy",
    lambda state: retrieve_policy_node(state, service=policy_rag_service),
)
```

这就是图级依赖注入。

它解决的是：

```text
整图执行时，怎么替换图内部某个节点依赖。
```

### 10. LangGraph 节点级测试

LangGraph 官方文档给了一个很实用的测试思路：

```text
编译后的 graph 可以通过 graph.nodes 访问单个节点。
```

也就是说，我们可以这样测：

```python
graph = build_ticket_agent_graph()
update = graph.nodes["classify_intent"].invoke({"normalized_message": "你好"})
```

这很有价值。

因为如果你只是为了测试 `classify_intent`，没必要跑完整流程：

```text
normalize_user_input
classify_intent
build_direct_answer
END
```

你可以只测一个节点的局部更新：

```text
输入局部 State -> 节点 -> 输出局部 State update
```

节点级测试适合验证：

```text
某个节点写了哪些 State 字段
某个节点是否追加了 node_history
某个节点是否调用了 fake 依赖
某个节点遇到异常时是否返回 fallback
```

### 11. LangGraph 路由测试

条件边本质上依赖 routing function。

比如：

```python
def route_by_intent(state):
    return state.get("intent", "unclear")
```

路由测试要回答：

```text
某个 State 下，下一步应该去哪个分支？
```

它不一定要跑完整图。

例如：

```python
assert route_by_intent({"intent": "ticket_request"}) == "ticket_request"
assert route_by_ticket_need({"needs_ticket": True}) == "create_ticket"
```

这种测试简单，但非常重要。

因为 LangGraph 的图结构里，很多问题不是节点内部算错，而是：

```text
路由函数返回的 key 和 path_map 对不上。
```

或者：

```text
某个字段缺失时走错默认分支。
```

### 12. LangGraph 整图路径测试

整图路径测试要验证：

```text
某个用户输入经过整张图后，是否走到预期业务路径。
```

我们项目里常用 `node_history` 判断路径：

```python
assert result["node_history"] == [
    "normalize_user_input",
    "classify_intent",
    "retrieve_policy",
    "decide_ticket_need",
]
```

这比只看最终回答更可靠。

因为最终回答可能相似，但路径可能错了。

例如：

```text
RAG answered -> 直接回答
ticket_request -> 创建工单确认
```

如果最终都返回一段中文，你只看 `final_answer` 可能发现不了分支错误。

`node_history` 能告诉你：

```text
Agent 实际经过了哪些节点。
```

### 13. LangGraph 局部执行测试

局部执行测试是本节很重要的一点。

真实场景中，我们有时不想从 `START` 开始跑完整流程。

例如我们只想测试：

```text
classify_intent 已经完成后，
后面的 decide_ticket_need -> extract_ticket_fields 能不能正常跑。
```

这时候可以用：

```python
graph.update_state(
    config,
    partial_state,
    as_node="classify_intent",
)
```

含义是：

```text
把这份 State 写进 checkpoint，
并告诉 LangGraph：这相当于 classify_intent 节点刚刚完成。
```

然后：

```python
result = graph.invoke(None, config=config, interrupt_after=["extract_ticket_fields"])
```

这里的 `None` 表示：

```text
不要传新的输入，从 checkpoint 当前状态继续执行。
```

`interrupt_after=["extract_ticket_fields"]` 表示：

```text
执行到 extract_ticket_fields 后暂停，方便测试中间状态。
```

这样我们就能精准测试流程中间段。

这对复杂 Agent 很有用。

### 14. checkpoint 测试为什么要用新的 MemorySaver

checkpoint 会保存 thread state。

如果多个测试共享同一个 graph 和同一个 checkpointer，就可能发生：

```text
上一个测试写入了 thread_id=A 的状态
下一个测试刚好用了相同 thread_id
结果下一个测试读到旧状态
```

这会导致测试随机失败。

所以测试里通常要：

```text
每个测试创建自己的 checkpointed graph
每个测试使用唯一 thread_id
```

本项目里：

```python
graph = build_checkpointed_ticket_agent_graph(ticket_creator=FakeTicketCreator())
```

函数内部会创建新的：

```python
MemorySaver()
```

这样测试之间不会共享 checkpoint。

### 15. interrupt / resume 测试要关注什么

`interrupt` 测试不是只看“有没有暂停”。

至少要看：

```text
返回结果里有没有 __interrupt__
interrupt payload 是否结构化
payload kind 是否正确
pending_ticket_confirmation 是否存在
snapshot.next 是否停在正确节点
resume approved=True 后是否创建工单
resume approved=False 后是否不创建工单
错误 thread_id 是否进入安全 fallback
```

本项目之前已经覆盖了：

```text
暂停等待确认
确认后继续创建工单
拒绝后不创建工单
无法找到 interrupt payload 的业务错误
resume 异常兜底
```

本节不会重复堆同样测试，而是把它们放进测试体系里解释清楚。

### 16. fallback 测试要关注什么

fallback 测试要验证：

```text
用户看到安全消息
内部异常不泄露
State 有错误码
State 标记 fallback_used=True
node_history 记录出错位置
日志记录错误类型
日志不记录敏感原文
```

一个常见错误是：

```text
只测试 raise 了异常。
```

但 Agent 对外不能随便把异常抛给用户。

对用户来说，更重要的是：

```text
系统是否给出安全可理解的失败回答。
```

对开发者来说，更重要的是：

```text
日志和 State 是否足够排查。
```

### 17. 日志测试要关注什么

日志测试不是“把整行日志逐字匹配一遍”。

逐字匹配太脆弱。

更合理的是验证：

```text
关键事件出现了
关键字段出现了
敏感内容没有出现
trace_id 被带上了
```

例如：

```python
assert "ticket_agent_finished operation=invoke_safe" in caplog.text
assert "last_node=build_direct_answer" in caplog.text
assert "你好" not in caplog.text
```

这说明：

```text
日志记录了运行结束事件
日志记录了最后节点
日志没有泄露用户原始输入
```

这比只测输出更接近生产问题排查。

## 二、本节主题系统讲解

### 1. 当前智能工单 Agent 的测试地图

现在我们的 Agent 测试已经覆盖多个层次。

可以这样理解：

```text
纯函数测试
  classify_ticket_intent
  decide_ticket_need
  extract_ticket_fields
  find_missing_ticket_fields
  build_ticket_confirmation_message

节点测试
  normalize_user_input_node
  classify_intent_node
  retrieve_policy_node
  create_ticket_node

路由测试
  route_by_intent
  route_by_ticket_need
  route_by_ticket_fields_complete
  route_by_ticket_confirmation

整图测试
  policy question -> RAG -> finish
  no_context -> ticket flow
  ticket_request -> confirmation
  approved -> create_ticket

checkpoint 测试
  保存 pending confirmation
  按 thread_id 隔离状态
  从 checkpoint 恢复创建工单

interrupt 测试
  暂停
  resume approved
  resume rejected
  invalid thread_id fallback

错误和日志测试
  Java 创建失败
  unknown exception fallback
  run_ticket_agent_safely
  caplog 验证日志

测试替身
  FakeTicketCreator
  FakePolicyRagService
  FakeNoContextPolicyRagService
  FakeOrderLookupClient
  FakeTicketExtractor
```

这个地图比单个测试更重要。

因为以后你维护 Agent 时，要先判断：

```text
这次改动影响哪一层？
应该补哪一层测试？
```

### 2. 本节新增的关键能力：图级 fake RAG 注入

之前 `retrieve_policy_node()` 已经支持传入 `service`。

但整图构建时还不能传入 fake RAG。

本节把 `build_ticket_agent_graph()` 改成：

```python
def build_ticket_agent_graph(
    ticket_creator: TicketCreator | None = None,
    *,
    policy_rag_service: PolicyRagService | None = None,
    checkpointer: Any | None = None,
    interrupt_confirmation: bool = False,
):
```

这里多出来的是：

```text
policy_rag_service
```

它的作用是：

```text
让整张 LangGraph 图在测试时使用 fake RAG。
```

图里绑定节点时：

```python
builder.add_node(
    "retrieve_policy",
    lambda state: retrieve_policy_node(state, service=policy_rag_service),
)
```

这个 `lambda` 的作用是：

```text
LangGraph 执行 retrieve_policy 节点时，仍然只会传 state。
lambda 帮我们把外部传入的 policy_rag_service 带进去。
```

你可以把它理解成：

```text
给节点提前装配好测试依赖。
```

### 3. 为什么参数用了 `*`

函数签名里有一个 `*`：

```python
def build_ticket_agent_graph(
    ticket_creator: TicketCreator | None = None,
    *,
    policy_rag_service: PolicyRagService | None = None,
    checkpointer: Any | None = None,
    interrupt_confirmation: bool = False,
):
```

`*` 后面的参数必须用关键字传参。

也就是说可以这样：

```python
build_ticket_agent_graph(policy_rag_service=fake_rag)
```

不建议也不允许这样：

```python
build_ticket_agent_graph(fake_creator, fake_rag)
```

这样设计的好处是：

```text
参数含义清楚。
以后再加 checkpointer、interrupt_confirmation 等参数时，不容易把位置传错。
```

对于图构建函数这种参数较多的函数，关键字参数更安全。

### 4. `build_checkpointed_ticket_agent_graph()` 也要支持 fake RAG

如果只改普通图构建函数，还不够。

因为 checkpoint 图是这样创建的：

```python
graph = build_checkpointed_ticket_agent_graph(...)
```

所以本节也让它支持：

```python
build_checkpointed_ticket_agent_graph(
    ticket_creator=fake_creator,
    policy_rag_service=fake_rag,
)
```

这保证了：

```text
普通整图测试可以 fake RAG
checkpoint 测试也可以 fake RAG
interrupt 图测试也可以 fake RAG
```

测试能力要在所有构建入口保持一致。

否则以后某一种图能测，另一种图不能测，就会留下盲区。

### 5. `FakePolicyRagService` 的设计

本节新增测试 fake：

```python
class FakePolicyRagService:
    def __init__(
        self,
        answer: RagAnswer | None = None,
        *,
        error: Exception | None = None,
    ) -> None:
        self.answer = answer or make_policy_rag_answer()
        self.error = error
        self.queries: list[str] = []

    def answer_policy_question(self, query: str) -> RagAnswer:
        self.queries.append(query)
        if self.error is not None:
            raise self.error
        return self.answer
```

逐行理解：

```text
answer
```

表示测试希望 RAG 返回什么答案。

```text
error
```

表示测试希望 RAG 调用时抛出什么异常。

```text
queries
```

记录 Agent 实际传给 RAG 的查询文本。

```text
self.queries.append(query)
```

这是 spy 能力。

它让测试可以断言：

```python
assert service.queries == ["退款规则是什么？"]
```

```text
if self.error is not None: raise self.error
```

这是失败模拟能力。

它让以后可以测试：

```text
RAG 失败时 Agent 是否进入安全 fallback。
```

```text
return self.answer
```

这是 stub 能力。

它保证 RAG 返回固定结果。

### 6. 为什么要有 `FakeNoContextPolicyRagService`

普通 fake RAG 默认返回 `answered`。

但 Agent 里有一条很重要的分支：

```text
RAG 没找到资料 -> 进入工单流程 -> 让人工补充或处理知识库缺口
```

所以我们需要一个专门返回 `no_context` 的 fake：

```python
class FakeNoContextPolicyRagService(FakePolicyRagService):
    def __init__(self) -> None:
        super().__init__(build_no_context_rag_answer())
```

它的作用是让测试可读：

```python
service = FakeNoContextPolicyRagService()
```

比下面这种写法更直观：

```python
service = FakePolicyRagService(build_no_context_rag_answer())
```

测试代码也是文档。

好的 fake 名称可以直接表达测试场景。

### 7. `make_policy_rag_answer()` 的意义

`make_policy_rag_answer()` 负责构造一个带 citation 的 RAG 回答：

```python
def make_policy_rag_answer(
    *,
    answer: str = "根据测试知识库，退款通常需要核对订单状态和售后条件。",
) -> RagAnswer:
    return build_grounded_rag_answer(
        answer,
        [
            make_retrieved_chunk(
                chunk_id="fake_policy_chunk_0001",
                content="退款通常需要核对订单状态和售后条件。",
                metadata={
                    "source": "fake-policy.md",
                    "title": "测试政策",
                    "section": "退款",
                    "chunk_id": "fake_policy_chunk_0001",
                },
            )
        ],
    )
```

这里重点不是内容本身。

重点是结构完整：

```text
answer 有文本
status 是 answered
citations 有 source
citations 有 chunk_id
metadata 像真实 RAG chunk
```

为什么 citation 也要有？

因为 Agent 不只关心“有没有回答”，还可能关心：

```text
引用来源是否被写进 State
RAG answered 是否进入 finish 分支
no_context 是否进入 ticket 分支
```

所以 fake 返回的数据结构要尽量贴近真实结构。

### 8. 节点级测试：只测 `classify_intent`

本节新增：

```python
def test_compiled_graph_node_can_be_invoked_for_node_level_test() -> None:
    graph = build_ticket_agent_graph()

    update = graph.nodes["classify_intent"].invoke({"normalized_message": "你好"})

    assert update["intent"] == "smalltalk"
    assert update["intent_reason"]
    assert update["node_history"] == ["classify_intent"]
```

这个测试说明：

```text
编译后的 LangGraph 可以直接调用某个节点。
```

它验证三件事：

```text
intent 写成 smalltalk
intent_reason 不为空
node_history 只记录 classify_intent
```

注意，这里没有验证最终回答。

因为这个测试不是整图测试。

它只关心：

```text
classify_intent 节点自己的输出。
```

### 9. 整图 fake RAG answered 测试

本节新增：

```python
def test_build_ticket_agent_graph_uses_injected_fake_rag_service() -> None:
    service = FakePolicyRagService()
    graph = build_ticket_agent_graph(policy_rag_service=service)

    result = graph.invoke(
        {
            "user_message": "退款规则是什么？",
            "node_history": [],
        }
    )

    assert service.queries == ["退款规则是什么？"]
    assert result["intent"] == "policy_question"
    assert result["rag_answer_status"] == "answered"
    assert result["rag_citations"][0]["source"] == "fake-policy.md"
    assert result["needs_ticket"] is False
    assert result["ticket_need_source"] == "rag_answered"
```

这个测试验证的是：

```text
整张图真的使用了注入的 fake RAG。
```

最关键的断言是：

```python
assert service.queries == ["退款规则是什么？"]
```

如果这条断言失败，说明：

```text
图里的 retrieve_policy 节点没有调用我们传入的 fake RAG。
```

后面的断言说明：

```text
fake RAG 返回 answered
Agent 识别为 policy_question
Agent 不创建工单
Agent 记录 rag_answered
```

这就是一个完整但很轻量的整图路径测试。

### 10. 整图 fake RAG no_context 测试

本节新增：

```python
def test_build_ticket_agent_graph_uses_fake_rag_no_context_ticket_flow() -> None:
    service = FakeNoContextPolicyRagService()
    graph = build_ticket_agent_graph(policy_rag_service=service)

    result = graph.invoke(
        {
            "user_message": "会员等级政策是什么？",
            "node_history": [],
        }
    )

    assert service.queries == ["会员等级政策是什么？"]
    assert result["intent"] == "policy_question"
    assert result["rag_answer_status"] == "no_context"
    assert result["needs_ticket"] is True
    assert result["ticket_need_source"] == "rag_no_context"
    assert result["ticket_fields"]["issue_type"] == "policy_gap"
    assert result["ticket_fields_complete"] is True
    assert result["ticket_confirmation_required"] is True
```

这个测试非常关键。

它验证的是：

```text
RAG 没资料不是流程结束。
RAG 没资料会进入工单流程。
```

为什么这是合理的？

因为对企业客服来说，知识库没有资料时，不能只说“我不知道”。

更好的流程是：

```text
把问题识别为知识缺口
生成 policy_gap 工单
交给人工或运营补知识库
```

这个测试把“知识库无资料”变成了一个可验证业务分支。

### 11. 局部执行测试：从 classify 后继续跑

本节新增：

```python
def test_checkpointed_graph_can_resume_partial_execution_after_classify() -> None:
    graph = build_checkpointed_ticket_agent_graph(ticket_creator=FakeTicketCreator())
    config = build_ticket_agent_thread_config("ticket-partial-001")

    graph.update_state(
        config,
        {
            "user_message": "我要投诉订单 1001，物流一直不动",
            "normalized_message": "我要投诉订单 1001，物流一直不动",
            "intent": "ticket_request",
            "node_history": ["normalize_user_input", "classify_intent"],
        },
        as_node="classify_intent",
    )
    result = graph.invoke(None, config=config, interrupt_after=["extract_ticket_fields"])
    snapshot = graph.get_state(config)
```

这段代码要慢慢理解。

第一步：

```python
graph = build_checkpointed_ticket_agent_graph(ticket_creator=FakeTicketCreator())
```

我们构建一个有 checkpoint 的图。

因为只有有 checkpoint，才能保存中间状态，再从中间继续。

第二步：

```python
config = build_ticket_agent_thread_config("ticket-partial-001")
```

我们给这次测试一个 thread_id。

第三步：

```python
graph.update_state(..., as_node="classify_intent")
```

我们手动写入一份状态，并告诉 LangGraph：

```text
这份状态相当于 classify_intent 节点执行后的结果。
```

第四步：

```python
graph.invoke(None, config=config, interrupt_after=["extract_ticket_fields"])
```

这里的 `None` 很重要。

它表示：

```text
不要从 START 重新输入用户消息。
从 checkpoint 里的当前状态继续执行。
```

第五步：

```python
interrupt_after=["extract_ticket_fields"]
```

它表示：

```text
执行完 extract_ticket_fields 后暂停。
```

这样我们可以断言：

```python
assert result["ticket_fields"]["order_id"] == "1001"
assert snapshot.next == ("request_ticket_confirmation",)
```

也就是说：

```text
从 classify_intent 后继续跑，确实进入了工单字段提取。
字段提取结束后，下一步应该去 request_ticket_confirmation。
```

这类测试很适合验证复杂图的中间段。

### 12. fake Java client 测试在本节中的位置

本项目的 `FakeTicketCreator` 已经在之前课程中加入。

本节把它纳入 LangGraph 测试体系。

它的核心能力是：

```python
class FakeTicketCreator:
    def __init__(
        self,
        *,
        ticket: CreatedTicket | None = None,
        error: Exception | None = None,
    ) -> None:
        self.ticket = ticket
        self.error = error
        self.calls: list[CreateTicketArgs] = []
        self.idempotency_keys: list[str] = []
```

重点字段：

```text
calls
```

记录创建工单时传入的参数。

```text
idempotency_keys
```

记录创建工单时传入的幂等键。

```text
error
```

用于模拟 Java 服务失败。

这让我们能测试：

```text
未确认时不调用 Java
确认后调用 Java
调用参数映射正确
幂等键传递正确
Java 失败时写入失败状态
Java 异常时进入 fallback
```

### 13. 为什么 fake Java client 比真实 Java 服务更适合单元测试

真实 Java 服务适合验证：

```text
HTTP 路径是否可达
请求体是否匹配 Java DTO
Java 服务是否能创建工单
跨服务 trace_id 是否能传递
```

fake Java client 适合验证：

```text
Agent 是否在正确时机请求创建工单
Agent 传出的参数是否正确
Agent 是否携带幂等键
Agent 如何处理 Java 失败
```

两者不是谁替代谁。

它们是不同层级：

```text
单元测试：fake Java client
集成测试：httpx.MockTransport 或 Java mock API
验收测试：真实启动服务后端到端调用
```

### 14. fake LLM 在当前项目里的位置

当前 `ticket_agent.py` 里的意图识别和字段提取主要还是规则版。

所以本节没有强行把真实 LLM 接进 Agent。

但 fake LLM 的思想已经在项目前面出现过：

```text
阶段 2：测试模型调用：mock/fake LLM client
阶段 3：工具调用链路中用 fake client 固定模型 tool_calls
阶段 4：RAG 生成回答时用 fake LLM 固定回答
```

如果以后把：

```text
classify_intent
extract_ticket_fields
build_final_answer
```

换成真实模型节点，那测试方式会延续本节思路：

```text
定义 LLM 协议
生产环境传真实 LLM client
测试环境传 fake LLM client
fake LLM 固定返回 intent、字段、summary
测试只验证 Agent 如何使用模型结果
```

所以本节标题里的 fake LLM 不是说今天必须新增一个真实 LLM Agent 节点。

它的意思是：

```text
LangGraph Agent 的外部智能依赖也要可替换、可控制、可测试。
```

### 15. 测试文件如何组织更合理

当前项目有：

```text
tests/tool_fakes.py
tests/rag_fakes.py
tests/fakes.py
tests/test_tool_fakes.py
tests/test_ticket_agent_intent.py
```

可以这样理解：

```text
tool_fakes.py
  放可复用测试替身。

test_tool_fakes.py
  测试这些 fake 自己是否可靠。

test_ticket_agent_intent.py
  测试智能工单 Agent 的节点、路由、图、checkpoint、interrupt、fallback、日志。
```

为什么 fake 自己也要测试？

因为 fake 如果写错，其他测试可能给出假信心。

例如：

```text
FakePolicyRagService 如果没有记录 queries，
那图是否真的调用 fake RAG 就无法验证。
```

所以 fake 也是测试基础设施。

测试基础设施也要可靠。

## 三、本节代码改动讲解

### 1. `ticket_agent.py` 的改动

本节主要改了图构建函数。

现在 `build_ticket_agent_graph()` 支持：

```python
policy_rag_service: PolicyRagService | None = None
```

这不是业务功能变化。

这是测试能力变化。

它让我们能写：

```python
service = FakePolicyRagService()
graph = build_ticket_agent_graph(policy_rag_service=service)
```

然后整图执行时，RAG 节点会使用这个 fake。

这个设计遵循一个原则：

```text
生产代码负责业务能力。
图构建函数负责装配依赖。
测试代码负责传入 fake。
```

### 2. `tests/tool_fakes.py` 的改动

本节新增：

```text
make_policy_rag_answer
FakePolicyRagService
FakeNoContextPolicyRagService
```

它们让测试可以稳定模拟两种 RAG 结果：

```text
answered
no_context
```

同时还能记录：

```text
Agent 实际传入的 query
```

这就是 fake RAG 的价值。

### 3. `tests/test_tool_fakes.py` 的改动

本节新增 fake 自身测试：

```text
make_policy_rag_answer 返回 grounded answer 和 citation
FakePolicyRagService 返回固定答案并记录 query
FakePolicyRagService 可以抛出配置好的异常
FakeNoContextPolicyRagService 返回 no_context
```

这些测试看起来小，但意义很大。

它们保证：

```text
后续所有使用 fake RAG 的测试，基础工具本身是可信的。
```

### 4. `tests/test_ticket_agent_intent.py` 的改动

本节新增了四类测试：

```text
compiled graph 节点级测试
整图注入 fake RAG answered 测试
整图注入 fake RAG no_context 测试
checkpoint 局部执行测试
```

这些测试分别覆盖：

```text
节点可单测
外部依赖可替换
RAG answered 分支正确
RAG no_context 分支正确
流程中间段可恢复执行
```

这比单纯多测几个最终回答更有价值。

## 四、测试讲解

### 1. 本节运行的重点测试

本节运行：

```powershell
uv run pytest tests/test_ticket_agent_intent.py tests/test_tool_fakes.py
```

通过结果：

```text
103 passed
```

这说明：

```text
新增 fake RAG 没破坏旧的 Agent 测试。
节点级测试、整图 fake RAG 测试、局部执行测试都通过。
```

### 2. 为什么还要跑全量测试

本节改了共享文件：

```text
app/agents/ticket_agent.py
tests/tool_fakes.py
```

这些文件可能被其他测试引用。

所以本节最后还要跑：

```powershell
uv run pytest
```

这是为了确认：

```text
不只本节测试通过，整个 ai-service 项目仍然通过。
```

## 五、常见误区

### 误区 1：测试 Agent 就必须真实调用模型

不对。

大多数 Agent 自动化测试都应该先用 fake 模型。

真实模型更适合：

```text
少量 smoke test
人工验收
评测集跑分
上线前回归
```

### 误区 2：fake 越像真实服务越好

不一定。

fake 要足够像真实依赖的关键契约，但不能复杂到和真实服务一样难维护。

好的 fake 应该：

```text
简单
稳定
可配置
可记录调用
返回结构贴近真实对象
```

### 误区 3：整图测试越多越好

不一定。

整图测试有价值，但太多整图测试会变慢、重复、难定位。

更好的方式是：

```text
纯函数测试覆盖细节
节点测试覆盖节点输出
路由测试覆盖分支 key
少量整图测试覆盖关键业务路径
checkpoint/interrupt/fallback 测试覆盖复杂机制
```

### 误区 4：只测成功路径

不够。

Agent 一旦调用外部服务，就必须测试失败路径。

至少要测：

```text
RAG 无资料
Java 创建失败
未知异常
无 pending confirmation
invalid thread_id
用户拒绝确认
```

### 误区 5：日志测试只看有没有日志

不够。

日志测试还应该验证：

```text
关键字段有
敏感原文没有
trace_id 能关联
错误类型能定位
```

## 六、以后真实项目里怎么用这套思想

如果你以后做企业级 Agent，测试可以按这个顺序设计：

```text
1. 给所有外部依赖定义协议或接口
2. 让图构建函数支持依赖注入
3. 为模型、RAG、数据库、业务服务写 fake
4. fake 支持固定返回、记录调用、模拟异常
5. 纯函数先单测
6. 节点再单测
7. 路由函数单测
8. 整图只覆盖关键路径
9. checkpoint 和 interrupt 单独测
10. fallback 和日志单独测
11. 少量真实依赖 smoke test 放到集成测试或手动验收
```

这就是从“会写代码”走向“会做工程”的测试思路。

## 七、本节练习

### 练习 1：解释 fake RAG 的作用

问题：

```text
为什么本节要新增 FakePolicyRagService，而不是直接使用真实 RAG？
```

参考答案：

```text
因为本节要测试的是 Agent 如何处理 RAG 返回结果，而不是测试向量库检索质量。
真实 RAG 会依赖 embedding、向量库、知识库数据、top_k、score_threshold 和网络环境。
这些因素会让测试变慢、不稳定、难定位。
FakePolicyRagService 可以稳定返回 answered 或 no_context，并记录 Agent 传入的 query。
这样测试可以专注验证 Agent 分支是否正确。
```

### 练习 2：解释 fake、stub、spy 的区别

问题：

```text
FakePolicyRagService 里哪些部分像 stub，哪些部分像 spy？
```

参考答案：

```text
self.answer 和 return self.answer 像 stub，因为它们提供固定返回结果。
self.queries.append(query) 像 spy，因为它记录被调用时传入的参数，方便测试后断言 Agent 是否真的调用了这个 fake，以及调用参数是否正确。
```

### 练习 3：解释图级依赖注入

问题：

```text
为什么只让 retrieve_policy_node 支持 service 参数还不够，还要让 build_ticket_agent_graph 支持 policy_rag_service 参数？
```

参考答案：

```text
单独调用 retrieve_policy_node 时可以直接传 service。
但整图测试调用的是 graph.invoke，LangGraph 会自动调用节点，测试代码不会直接调用 retrieve_policy_node。
所以必须在构建图时把 fake RAG 注入进去，让图内部的 retrieve_policy 节点执行时使用这个 fake。
```

### 练习 4：解释节点级测试

问题：

```text
graph.nodes["classify_intent"].invoke(...) 这种测试有什么好处？
```

参考答案：

```text
它可以只测试某个节点的局部行为，不需要跑完整张图。
这样测试更快，失败时更容易定位。
例如测试 classify_intent 节点时，只需要验证 intent、intent_reason 和 node_history，不需要关心后续 build_direct_answer 或其他节点。
```

### 练习 5：解释局部执行测试

问题：

```text
graph.update_state(..., as_node="classify_intent") 和 graph.invoke(None, config=config) 合起来解决什么问题？
```

参考答案：

```text
它们允许测试从图的中间状态继续执行。
update_state 把测试准备好的 State 写入 checkpoint，并告诉 LangGraph 这相当于 classify_intent 节点刚执行完。
invoke(None) 表示不传新的输入，而是从 checkpoint 当前状态继续跑。
这样可以精准测试图的中间段，而不用每次从 START 跑完整流程。
```

### 练习 6：解释为什么每个 checkpoint 测试要独立 graph

问题：

```text
为什么 checkpoint 测试里最好每个测试创建新的 build_checkpointed_ticket_agent_graph()？
```

参考答案：

```text
因为 checkpoint 会保存 thread_id 对应的 State。
如果多个测试共享同一个 checkpointer，旧测试的状态可能影响新测试，导致测试互相污染。
每个测试创建新的 checkpointed graph，可以确保 MemorySaver 是新的，状态不会串。
```

### 练习 7：解释 fake Java client 的价值

问题：

```text
FakeTicketCreator 为什么要记录 calls 和 idempotency_keys？
```

参考答案：

```text
calls 用来验证 Agent 传给创建工单服务的参数是否正确。
idempotency_keys 用来验证写操作是否携带幂等键。
这两个字段让测试不需要真实调用 Java 服务，也能确认 Agent 是否在正确时机、用正确参数请求创建工单。
```

### 练习 8：解释为什么日志测试不应记录用户原文

问题：

```text
为什么测试里要断言用户原始输入不在 caplog.text 里？
```

参考答案：

```text
因为用户原始输入可能包含隐私、订单信息、身份信息或敏感内容。
日志应该记录可排查的工程字段，例如 operation、thread_id、last_node、error_type、trace_id，而不是完整用户原文。
断言用户原文不在日志里，可以防止后续改代码时不小心把敏感内容写进日志。
```

## 八、自测题

### 自测 1：一句话解释本节真正学了什么

问题：

```text
本节真正学的是 pytest 语法吗？
```

参考答案：

```text
不是。本节真正学的是如何让复杂 LangGraph Agent 可测试：通过依赖注入和 fake 替代外部模型、RAG、Java 服务，通过节点级、路由级、整图、checkpoint、interrupt、fallback、日志测试来验证 Agent 的关键行为。
```

### 自测 2：为什么 fake LLM 很重要

问题：

```text
如果 Agent 某个节点未来改成真实大模型调用，单元测试应该怎么做？
```

参考答案：

```text
应该定义模型调用协议或服务接口，生产环境使用真实 LLM client，测试环境注入 fake LLM client。
fake LLM 固定返回结构化结果，比如 intent 或 ticket fields。
测试验证 Agent 如何使用模型结果，而不是依赖真实模型每次生成。
```

### 自测 3：RAG answered 和 no_context 分支分别代表什么

问题：

```text
RAG 返回 answered 和 no_context 时，智能工单 Agent 应该分别怎么处理？
```

参考答案：

```text
answered 表示知识库已经有可引用回答，当前通常不需要创建工单。
no_context 表示知识库没有足够资料，Agent 可以把它当作知识缺口或人工处理需求，进入工单流程。
```

### 自测 4：为什么 `node_history` 是重要测试字段

问题：

```text
为什么不能只看 final_answer，还要看 node_history？
```

参考答案：

```text
因为 final_answer 只能说明最终给用户的文字是什么，不能证明 Agent 走了正确流程。
node_history 能显示实际经过了哪些节点，可以验证条件边和业务路径是否正确。
```

### 自测 5：什么时候应该写整图测试

问题：

```text
是不是每个细节都应该写整图测试？
```

参考答案：

```text
不是。细节更适合纯函数测试、节点测试和路由测试。
整图测试应该覆盖关键业务路径，例如政策问答、无资料进入工单、确认后创建工单、interrupt/resume 等。
整图测试太多会变慢、重复且失败难定位。
```

### 自测 6：什么是 `interrupt_after`

问题：

```text
`interrupt_after=["extract_ticket_fields"]` 在测试里有什么作用？
```

参考答案：

```text
它让图在执行完 extract_ticket_fields 节点后暂停。
这样测试可以检查中间 State，例如 ticket_fields、ticket_fields_complete，以及下一步 snapshot.next 是否指向 request_ticket_confirmation。
```

### 自测 7：什么是 `as_node`

问题：

```text
graph.update_state(..., as_node="classify_intent") 里的 as_node 是什么意思？
```

参考答案：

```text
它告诉 LangGraph，这次手动写入的状态应该被视为 classify_intent 节点执行后的状态。
这样 LangGraph 能根据图结构从 classify_intent 后面的边继续执行。
```

### 自测 8：为什么 fake 自己也要测试

问题：

```text
FakePolicyRagService 这种测试工具为什么也要写测试？
```

参考答案：

```text
因为 fake 是其他测试的基础设施。
如果 fake 不记录 query、不返回正确结构或错误模拟失效，其他测试可能误判。
测试 fake 自己，可以保证后续基于 fake 的 Agent 测试更可信。
```

### 自测 9：如何判断一个 Agent 测试写得好不好

问题：

```text
一个好的 Agent 测试通常应该具备哪些特点？
```

参考答案：

```text
它应该目标明确、依赖可控、结果确定、失败易定位、覆盖关键路径和失败路径。
它不应该默认依赖真实模型、真实向量库或真实外部服务。
它应该能说明测试的是节点行为、路由行为、整图路径、checkpoint、interrupt、fallback 还是日志安全。
```

### 自测 10：本节以后如何影响你写代码

问题：

```text
以后新增 Agent 节点时，应该先想哪些测试问题？
```

参考答案：

```text
先想这个节点依赖哪些外部服务，是否能注入 fake。
再想节点输入 State 是什么，输出哪些字段，走哪些路由，失败时怎么处理，是否有副作用，是否需要 checkpoint 或 interrupt。
最后补纯函数测试、节点测试、必要的整图路径测试和失败路径测试。
```

## 九、本节小结

本节把智能工单 Agent 的测试体系补完整了一层。

你现在要记住的不是某个测试函数名字，而是这套思路：

```text
复杂 Agent 要先拆层。
外部依赖要可注入。
模型、RAG、Java 服务要能 fake。
节点可以单测。
路由可以单测。
整图只测关键路径。
checkpoint 可以从中间恢复测。
interrupt/resume 要单独测。
fallback 和日志安全不能漏。
```

如果以后你能对别人说清楚：

```text
我的 Agent 单元测试不会真实调用模型、向量库和 Java 服务。
我用 fake LLM / fake RAG / fake Java client 保证测试确定性。
我同时覆盖节点、路由、整图、checkpoint、interrupt、fallback 和日志安全。
真实服务调用放到更高层的集成测试或验收测试。
```

那你讲的就不是“我会写几个 pytest”。

你讲的是：

```text
我知道怎么把 AI Agent 做成可维护、可回归、可排查的工程系统。
```

## 十、参考资料

- [LangGraph Test 官方文档](https://docs.langchain.com/oss/python/langgraph/test)
- [LangGraph Interrupts 官方文档](https://docs.langchain.com/oss/python/langgraph/interrupts)
- [pytest fixtures 官方文档](https://docs.pytest.org/en/stable/explanation/fixtures.html)
- [pytest monkeypatch 官方文档](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)
- 本仓库：`notes/llm-api-stage2-17-testing-model-calls.md`
- 本仓库：`notes/tool-calling-stage3-17-tool-testing-fakes.md`
- 本仓库：`notes/rag-stage4-22-rag-testing-fakes.md`
- 本仓库：`notes/langgraph-stage5-21-checkpoint-thread-id.md`
- 本仓库：`notes/langgraph-stage5-22-interrupt-human-in-the-loop.md`
- 本仓库：`notes/langgraph-stage5-23-node-error-fallback.md`
- 本仓库：`notes/langgraph-stage5-24-observability-trace-logging.md`
