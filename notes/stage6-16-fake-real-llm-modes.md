# 阶段 6 第 16 节：fake LLM 和真实 LLM 双模式

本节目标：把智能工单 Agent 里的“规则模式、fake LLM 模式、真实 LLM 模式”明确拆开，并用配置统一选择。

这节不是为了追求新功能看起来更多，而是为了补一个生产化 AI 项目里非常关键的能力：

```text
同一套业务流程，可以在不同环境下选择不同模型执行方式。

本地开发：默认规则模式，稳定、便宜、不会误调真实模型。
自动测试：fake LLM 模式，走 JSON/Pydantic 边界，但不发网络请求。
手动验收：真实 LLM 模式，接入 OpenAI-compatible 大模型。
```

前面第 13、14、15 节已经完成：

```text
第 13 节：真实 LLM 意图识别节点
第 14 节：真实 LLM 工单字段提取节点
第 15 节：Pydantic 校验模型输出
```

现在还差一个问题：

```text
这些能力怎么在项目里“安全地启用”和“稳定地测试”？
```

这就是第 16 节要解决的。

---

## 一、本节在主线里的位置

阶段 6 当前主线是把已经能跑的 Agent 推向真实工程系统。

前面几节先解决“能不能评估”和“能不能接真实模型”：

```text
第 1-11 节：Agent eval 基础、数据集、报告、坏例分析、回归评测
第 12 节：evaluator 类型
第 13 节：真实 LLM 意图识别
第 14 节：真实 LLM 字段提取
第 15 节：Pydantic 校验模型输出
```

从第 13 节开始，项目里已经有真实模型能力了。

但是有真实模型能力，不等于应该默认使用真实模型。

真实模型有这些特点：

- 需要 API key。
- 需要网络。
- 可能产生费用。
- 响应可能变慢。
- 输出可能随模型版本变化。
- 自动测试里如果真实调用，就会不稳定。
- API key 一旦误提交，会变成安全事故。

所以本节要把“运行模式”变成一个清楚的配置边界。

本节完成后，当前 Agent 可以这样理解：

```text
rule_based
-> 不调用模型
-> 规则判断 intent 和 ticket fields
-> 适合默认开发、快速测试、稳定回归

fake_llm
-> 不调用模型
-> 但模拟模型返回 JSON
-> 再走同一套 Pydantic 校验
-> 适合测试模型输出边界和 graph 注入链路

real_llm
-> 调用真实 OpenAI-compatible 模型
-> 需要 LLM_API_KEY
-> 适合手动 smoke、真实效果验证、后续 eval
```

---

## 二、本节学习目标

学完本节，你要能解释清楚：

1. 为什么 AI 项目需要区分规则模式、fake LLM 模式和真实 LLM 模式。
2. 为什么真实 LLM 不应该成为自动化测试的默认依赖。
3. fake LLM、mock、stub、fake client 分别是什么意思。
4. 为什么 `fake_llm` 不能代表真实模型效果。
5. 为什么 `fake_llm` 仍然有学习和工程价值。
6. 什么是“运行模式配置”。
7. 什么是“依赖注入”。
8. 什么是“工厂函数”。
9. 为什么默认值应该是 `rule_based`，不是 `real_llm`。
10. 为什么 `real_llm` 模式在构建依赖前要先检查 API key。
11. 为什么构建真实 LLM 依赖时不能立刻发起模型请求。
12. 为什么自动测试可以用 fake client 测真实 LLM 封装。
13. `TICKET_AGENT_MODEL_MODE` 应该怎么配置。
14. `build_ticket_agent_graph_for_model_mode()` 在项目里负责什么。
15. 本节新增测试分别保护了哪些边界。

---

## 三、本节暂时不学什么

本节只解决“模式选择”和“测试边界”。

暂时不展开：

- 不做 prompt 版本管理。
- 不做真实模型效果打分。
- 不把真实 LLM 加进全量回归 eval。
- 不做多模型 A/B 对比。
- 不做模型输出失败后的自动 retry。
- 不做模型降级策略。
- 不改 Java mock service。
- 不改 RAG 检索流程。
- 不改用户确认和创建工单流程。
- 不在自动测试里真实调用你的模型 API key。

这些后面会按节学习。

现在先把一个边界打牢：

```text
什么时候不调模型
什么时候模拟模型
什么时候真实调模型
```

---

## 四、基础知识铺垫

### 1. 为什么需要“模式”

模式可以理解成：

```text
同一套代码，在不同环境下采用不同运行策略。
```

例如一个后端项目经常会有：

```text
local: 本地开发模式
test: 自动测试模式
staging: 预发布模式
production: 生产模式
```

这些环境可能连接不同的数据库、日志级别、第三方服务和缓存。

AI 项目也一样。

一个 Agent 在不同阶段可能需要不同的模型使用方式：

```text
开发功能时：希望稳定、快、不花钱
写测试时：希望可重复、不依赖外部服务
调 prompt 时：希望真实调用模型
上线前验收：希望用真实模型跑关键样本
线上运行时：希望真实模型可观测、可超时、可降级
```

如果没有模式切换，项目很容易变成两种坏情况。

第一种坏情况：所有地方都真实调用模型。

问题是：

- 测试慢。
- 测试结果不稳定。
- 没网就失败。
- API key 没配就失败。
- 可能产生费用。
- 很难判断失败是代码问题还是模型服务问题。

第二种坏情况：所有地方都只用规则或 fake。

问题是：

- 项目永远不验证真实模型效果。
- prompt 写得好不好不知道。
- 真实模型返回格式是否兼容不知道。
- 线上才发现模型输出不稳定。

所以生产化 AI 项目通常需要同时保留几条路径：

```text
稳定路径：开发和测试用。
模拟路径：验证工程边界用。
真实路径：验证模型效果用。
```

本节的三种模式就是这个思想的入门版。

### 2. 为什么默认模式必须保守

本节把默认值设成：

```text
TICKET_AGENT_MODEL_MODE=rule_based
```

原因很明确：

```text
默认运行项目时，不应该自动触发真实模型调用。
```

默认值应该满足：

- 新人拉下项目就能跑。
- 没有 API key 也能跑。
- 跑测试不会发网络请求。
- 不会意外消耗 token。
- 不会因为供应商网络问题导致本地开发失败。

这就是为什么默认是 `rule_based`。

如果你想真实调用模型，需要显式配置：

```env
TICKET_AGENT_MODEL_MODE="real_llm"
LLM_API_KEY="你的本机 key"
LLM_BASE_URL="你的 OpenAI-compatible base_url"
LLM_MODEL="qwen3.7-plus"
```

显式配置的意义是：

```text
你清楚知道自己正在进入真实模型调用路径。
```

### 3. 什么是 rule_based

`rule_based` 是规则模式。

它的特点是：

- 不调用大模型。
- 不需要 API key。
- 不需要网络。
- 行为确定。
- 测试稳定。
- 适合做默认回归基线。

规则模式不是“低级模式”。

在真实工程里，规则经常负责这些稳定边界：

- 明确的黑名单。
- 明确的安全策略。
- 明确的字段格式校验。
- 明确的兜底流程。
- 可解释的基础路由。

AI 项目不是把所有逻辑都交给大模型。

更合理的分工是：

```text
规则负责稳定边界。
模型负责理解复杂自然语言。
后端负责校验、流程和业务安全。
```

所以本项目保留 `rule_based` 很重要。

### 4. 什么是 real_llm

`real_llm` 是真实模型模式。

它的特点是：

- 会调用配置好的 OpenAI-compatible chat model。
- 需要 API key。
- 需要 base_url 和 model 配置正确。
- 可以处理更自然、更复杂的用户表达。
- 输出需要 Pydantic 校验。
- 适合手动 smoke 和后续真实 eval。

真实模型模式不是简单把规则替换掉。

在当前项目里，它只替换两个位置：

```text
classify_intent 节点
extract_ticket_fields 节点
```

它不负责：

- 是否允许创建工单。
- 是否需要用户确认。
- 是否调用 Java API。
- 是否写入业务系统。
- 是否绕过 Pydantic 校验。

这点非常重要。

模型参与理解，但不能接管业务边界。

### 5. 什么是 fake_llm

`fake_llm` 是模拟 LLM 模式。

它不调用真实模型。

它做的事情是：

```text
规则得到一个结果
-> 把结果 dump 成 JSON 字符串
-> 再交给 Pydantic 解析和校验
-> 返回和真实 LLM 节点一致的业务结构
```

也就是说，`fake_llm` 的重点不是模拟模型聪明程度。

它的重点是模拟工程路径：

```text
JSON 输出
-> Pydantic 校验
-> Agent state 写入
-> LangGraph 继续执行
```

所以它能验证这些东西：

- graph 能不能注入“像 LLM 一样”的组件。
- Pydantic 解析链路是否能正常工作。
- field extractor 的 `extraction_source` 是否正确写入。
- 自动测试是否不会误调真实模型。
- `real_llm` 和 `fake_llm` 是否共用同样的数据边界。

但是它不能验证这些东西：

- 真实模型能不能理解复杂表达。
- prompt 写得是否足够好。
- 真实模型会不会乱输出字段。
- 真实模型在不同版本下是否稳定。
- 真实模型成本和延迟如何。

一句话记：

```text
fake_llm 测工程边界，不测模型智能。
```

### 6. fake、mock、stub 的区别

这几个词很容易混。

先用最简单的方式理解。

#### stub

stub 是“固定返回值”。

例如：

```text
不管你问什么，它都返回 intent=smalltalk。
```

它像一个占位回答器。

主要用途：

- 让测试能继续跑。
- 不关心内部逻辑。
- 只关心调用方怎么处理返回值。

#### mock

mock 更强调“验证有没有被调用、被怎么调用”。

例如：

```text
记录调用次数
记录传入参数
断言 model 是否等于 qwen-test
断言 response_format 是否等于 {"type": "json_object"}
```

本项目的 `FakeChatCompletions` 同时带一点 stub 和 mock 的特点：

- 它可以返回固定内容。
- 它也会记录 `calls`。

所以测试可以断言：

```python
assert len(completions.calls) == 1
assert completions.last_call["model"] == "qwen-test"
```

#### fake

fake 是“可以工作的简化实现”。

它不像 stub 那样完全固定，也不像 mock 那样主要记录调用。

例如本节的 `FakeLLMTicketIntentClassifier`：

```text
它会真的根据当前规则分类
然后真的转 JSON
再真的用 Pydantic 校验
```

它不是生产真实模型，但它是一条可运行的简化路径。

可以这样区分：

```text
stub：给固定结果。
mock：记录和断言调用。
fake：用简化逻辑模拟一个可工作的组件。
```

### 7. 为什么自动化测试不应该真实调用模型

自动化测试的核心目标是：

```text
快速、稳定、可重复地判断代码有没有坏。
```

真实模型调用不适合放进默认自动化测试，原因包括：

- 模型输出不完全确定。
- 网络可能失败。
- 供应商服务可能限流。
- API key 在 CI 或本机可能不存在。
- 调用会花钱。
- 响应慢会拖慢测试套件。
- 测试失败后难判断是代码坏了还是模型飘了。

所以本项目保持原则：

```text
pytest 默认不真实调用模型。
真实模型用 smoke script 或后续 eval 单独跑。
```

这不是逃避真实模型，而是分清测试类型。

可以把它们分成：

```text
unit test
-> 不依赖外部服务
-> 快速验证代码逻辑

integration smoke
-> 允许依赖真实服务
-> 手动运行
-> 用来验证配置和真实链路

eval
-> 批量样本
-> 观察质量指标
-> 用来比较模型、prompt 和版本
```

本节主要补的是第一类：稳定自动化测试。

### 8. 什么是依赖注入

依赖注入就是：

```text
函数或对象不自己硬编码依赖，而是允许外部把依赖传进来。
```

例如不好的写法：

```python
def classify_intent_node(state):
    classifier = LLMTicketIntentClassifier(get_settings())
    return classifier.classify_intent(state["normalized_message"])
```

问题是：

- 每次都会绑定真实 LLM 类。
- 测试很难替换。
- 默认可能误调模型。
- 节点和具体模型实现耦合太紧。

更好的写法：

```python
def classify_intent_node(state, *, classifier=None):
    if classifier is None:
        return classify_ticket_intent(...)
    return classifier.classify_intent(...)
```

这样外部可以传：

```text
None -> 规则模式
FakeLLMTicketIntentClassifier -> fake LLM 模式
LLMTicketIntentClassifier -> 真实 LLM 模式
```

这就是依赖注入的价值。

它让业务节点不用关心“这个分类器到底来自哪里”。

节点只关心：

```text
我有一个 classifier，它能 classify_intent。
```

### 9. 什么是工厂函数

工厂函数就是：

```text
集中创建对象的函数。
```

本节新增的工厂函数是：

```python
create_ticket_agent_model_dependencies(...)
```

它负责根据模式返回对应依赖：

```text
rule_based
-> intent_classifier=None
-> field_extractor=None

fake_llm
-> FakeLLMTicketIntentClassifier
-> FakeLLMTicketFieldExtractor

real_llm
-> LLMTicketIntentClassifier
-> LLMTicketFieldExtractor
```

为什么要用工厂函数？

因为如果到处都写：

```python
if mode == "fake_llm":
    ...
elif mode == "real_llm":
    ...
```

项目会很快失控。

集中放到一个工厂函数里，有几个好处：

- 模式选择逻辑只写一份。
- 测试更集中。
- 新增模式更容易。
- graph 构建代码更干净。
- API key 检查可以放在统一入口。

### 10. 为什么 real_llm 要先检查 API key

真实模型模式必须需要 key。

如果没有 key，还继续构建真实模型依赖，错误会在更深的位置爆出来。

那样排查困难。

所以本节加了：

```python
ensure_real_ticket_agent_llm_is_configured(settings)
```

它的职责很单一：

```text
如果选择 real_llm，但没有可用 LLM_API_KEY，就立即抛出清晰的 AppException。
```

这个错误比底层 SDK 的错误更适合当前项目。

因为它能告诉你：

```text
不是代码逻辑坏了，而是本机 .env 没配 LLM_API_KEY。
```

### 11. 为什么构建依赖时不能立刻调用模型

本节测试里有一个重要断言：

```python
assert completions.calls == []
```

它验证的是：

```text
创建 real_llm 依赖时，不应该立刻发起模型调用。
```

为什么？

因为“创建对象”和“执行业务”是两件事。

创建对象应该只做准备：

- 保存 settings。
- 保存 client。
- 建立后续调用需要的对象关系。

真正调用模型应该发生在：

```text
classify_intent_node 执行时
或
extract_ticket_fields_node 执行时
```

这样做的好处：

- graph 可以先构建。
- 测试可以检查依赖类型。
- 配置错误可以早发现。
- 业务调用发生在明确节点里。
- 日志和异常边界更清楚。

---

## 五、本节主题系统讲解

### 1. 本节之前项目的问题

第 13、14 节之后，项目已经有真实模型组件：

```text
LLMTicketIntentClassifier
LLMTicketFieldExtractor
```

同时也保留了规则函数：

```text
classify_ticket_intent()
extract_ticket_fields()
```

graph 也支持外部传入：

```text
intent_classifier
field_extractor
```

这说明底层能力已经有了。

但第 16 节之前还缺一个统一入口：

```text
用户或开发者到底从哪里选择“用规则、fake，还是真实 LLM”？
```

如果没有统一入口，就会出现：

- 每次手动构建 graph。
- 每个测试自己拼依赖。
- 哪个地方会真实调模型不够明显。
- `.env` 里没有一个直观配置告诉你当前 Agent 模式。
- 以后做 smoke/eval 时容易混乱。

所以本节补的是工程组织能力。

### 2. 本节之后的模式选择流程

现在流程变成：

```text
.env / Settings
-> ticket_agent_model_mode
-> create_ticket_agent_model_dependencies()
-> build_ticket_agent_graph_for_model_mode()
-> LangGraph 节点执行
```

用图表示：

```text
TICKET_AGENT_MODEL_MODE
        |
        v
create_ticket_agent_model_dependencies()
        |
        +-- rule_based -> None, None
        |
        +-- fake_llm  -> FakeLLMTicketIntentClassifier, FakeLLMTicketFieldExtractor
        |
        +-- real_llm  -> LLMTicketIntentClassifier, LLMTicketFieldExtractor
        |
        v
build_ticket_agent_graph(...)
        |
        v
classify_intent_node / extract_ticket_fields_node
```

注意：

```text
graph 节点本身没有写一堆 if mode == ...
```

节点还是只通过接口工作。

这说明我们把“模式选择”和“节点执行”拆开了。

### 3. 三种模式的职责边界

| 模式 | 是否调用模型 | 是否需要 key | 是否走 Pydantic 输出校验 | 适合场景 |
| --- | --- | --- | --- | --- |
| `rule_based` | 否 | 否 | 不走 LLM JSON 校验链路 | 默认开发、快速回归、稳定基线 |
| `fake_llm` | 否 | 否 | 走 | 测试 JSON/Pydantic/graph 注入链路 |
| `real_llm` | 是 | 是 | 走 | 手动 smoke、真实效果验证、后续 eval |

这个表必须记住。

尤其要记住：

```text
fake_llm 不等于 real_llm。
```

它们共用工程边界，但不共用模型能力。

### 4. 为什么 fake_llm 要走 JSON 再 Pydantic

如果 fake 只是直接返回字典：

```python
return classify_ticket_intent(message)
```

它只能验证规则逻辑。

但它不能验证：

- JSON dump 是否正确。
- Pydantic JSON 解析是否正常。
- 多余字段是否会被拒绝。
- 字段类型是否会被检查。
- graph 接入“模型风格输出”是否正常。

所以本节的 fake LLM 故意这样写：

```python
classification = classify_ticket_intent(message)
raw_json = json.dumps(classification, ensure_ascii=False)
return parse_ticket_intent_classification_json(raw_json)
```

字段提取也一样：

```python
fields = extract_ticket_fields(state)
raw_json = json.dumps(fields, ensure_ascii=False)
return parse_ticket_field_extraction_json(raw_json)
```

这段代码的重点是：

```text
不真实调用模型，但走真实解析校验边界。
```

这就是 fake LLM 的工程价值。

### 5. 为什么 graph 入口要新加一层

原来已经有：

```python
build_ticket_agent_graph(...)
```

它负责接收具体依赖：

```text
intent_classifier
field_extractor
policy_rag_service
ticket_creator
```

本节新增：

```python
build_ticket_agent_graph_for_model_mode(...)
```

它负责接收模式：

```text
mode
settings
client
```

两者分工不同：

```text
build_ticket_agent_graph
-> 底层图构建器
-> 直接接收依赖对象

build_ticket_agent_graph_for_model_mode
-> 模式入口
-> 根据配置先创建依赖，再调用底层图构建器
```

这种分层很常见。

底层函数保留灵活性。

上层函数提供易用入口。

### 6. 为什么 global graph 仍然保持 rule_based

文件里仍然保留：

```python
ticket_agent_graph = build_ticket_agent_graph()
```

这意味着默认全局 graph 还是规则模式。

这不是遗漏。

这是安全设计。

原因是：

- 现有 API 或脚本如果直接使用 `ticket_agent_graph`，不会突然开始调真实模型。
- 老测试不需要因为新模式而改。
- 本地没配 API key 也能继续跑。
- 真实模型必须通过显式入口启用。

这是生产化代码里很重要的兼容思路：

```text
新增能力时，不要让老路径默认变危险。
```

---

## 六、本节代码讲解

本节生产代码主要改了两个文件：

```text
projects/ai-service/app/core/config.py
projects/ai-service/app/agents/ticket_agent.py
```

还更新了：

```text
projects/ai-service/.env.example
```

### 1. 配置类型：TicketAgentModelMode

新增：

```python
TicketAgentModelMode = Literal["rule_based", "fake_llm", "real_llm"]
```

这行的意义是：

```text
当前 Agent 模型模式只能是这三个字符串之一。
```

为什么不用普通 `str`？

如果写成：

```python
ticket_agent_model_mode: str = "rule_based"
```

那么这些错值也会被接受：

```text
production
real
llm
fake
openai
```

这样错误会拖到运行时才暴露。

用 `Literal` 后，Pydantic Settings 读取配置时就能校验。

如果 `.env` 写错：

```env
TICKET_AGENT_MODEL_MODE="production"
```

测试会验证它报：

```text
literal_error
```

这就是配置即边界。

### 2. Settings 里的新字段

新增：

```python
ticket_agent_model_mode: TicketAgentModelMode = Field(default="rule_based")
```

这表示：

```text
如果 .env 没写，默认 rule_based。
如果 .env 写了，必须是 rule_based / fake_llm / real_llm 之一。
```

为什么这个字段放在 `Settings`？

因为它是运行时配置，不是业务数据。

业务数据是：

```text
用户消息
订单号
工单字段
Agent state
```

运行时配置是：

```text
用哪个模型
是否真实调用
base_url 是什么
API key 从哪里读
timeout 多久
```

所以放在 `app/core/config.py` 合理。

### 3. `.env.example` 里的说明

新增：

```env
# rule_based: stable local rules, no model call.
# fake_llm: simulate LLM output through the same JSON/Pydantic path, no model call.
# real_llm: call the configured OpenAI-compatible chat model.
TICKET_AGENT_MODEL_MODE="rule_based"
```

这里没有写真实 key。

它只是告诉你：

```text
本机 .env 可以复制这个字段，然后按需要改模式。
```

真实 key 只能放本机 `.env`，不能提交 GitHub。

### 4. TicketAgentModelDependencies

新增：

```python
class TicketAgentModelDependencies(TypedDict):
    mode: TicketAgentModelMode
    intent_classifier: "TicketIntentClassifier | None"
    field_extractor: "TicketFieldExtractor | None"
```

这个类型用于表达：

```text
根据某个模式，最终选出来的一组 Agent 模型依赖。
```

它包含三部分：

- `mode`：最终使用的模式。
- `intent_classifier`：意图识别依赖。
- `field_extractor`：字段提取依赖。

为什么 `intent_classifier` 和 `field_extractor` 可以是 `None`？

因为在 `rule_based` 模式下，graph 节点会走默认规则函数。

也就是：

```text
None 不代表缺失。
None 在这里代表使用默认规则实现。
```

### 5. FakeLLMTicketIntentClassifier

新增：

```python
class FakeLLMTicketIntentClassifier:
    def classify_intent(self, message: str) -> TicketAgentIntentClassification:
        classification = classify_ticket_intent(message)
        raw_json = json.dumps(classification, ensure_ascii=False)
        return parse_ticket_intent_classification_json(raw_json)
```

这段代码的学习重点不是规则分类。

规则分类以前已经学过。

这里真正要理解的是后两步：

```python
raw_json = json.dumps(classification, ensure_ascii=False)
return parse_ticket_intent_classification_json(raw_json)
```

它们让 fake 结果走过：

```text
Python dict
-> JSON string
-> Pydantic model_validate_json
-> 业务 TypedDict
```

这和真实模型的返回路径更接近。

真实模型是：

```text
LLM text
-> JSON string
-> Pydantic model_validate_json
-> 业务 TypedDict
```

fake 模式只是把最前面的 LLM text 换成了规则生成的 JSON text。

### 6. FakeLLMTicketFieldExtractor

新增：

```python
class FakeLLMTicketFieldExtractor:
    extraction_source: TicketFieldExtractionSource = "fake_llm"

    def extract_fields(self, state: TicketAgentState) -> TicketFields:
        fields = extract_ticket_fields(state)
        raw_json = json.dumps(fields, ensure_ascii=False)
        return parse_ticket_field_extraction_json(raw_json)
```

这里多了一个字段：

```python
extraction_source = "fake_llm"
```

它的作用是写入 Agent state：

```text
ticket_field_extraction_source = "fake_llm"
```

这个字段有助于调试和评估。

以后看一次 Agent 输出时，可以知道字段来自：

```text
rule_based
fake_llm
llm
```

在生产化系统里，这类“来源字段”非常重要。

因为当效果不好时，你要先知道：

```text
到底是规则提取错了？
fake 路径错了？
还是真实模型输出错了？
```

### 7. ensure_real_ticket_agent_llm_is_configured

新增：

```python
def ensure_real_ticket_agent_llm_is_configured(settings: Settings) -> None:
    if not settings.has_llm_api_key:
        raise AppException(
            code="LLM_API_KEY_MISSING",
            message="LLM API key 未配置，请先在本机 .env 中配置 LLM_API_KEY。",
            status_code=500,
        )
```

这段代码只做一件事：

```text
选择 real_llm 时，必须先有 API key。
```

为什么错误码仍然是 `LLM_API_KEY_MISSING`？

因为前面真实 LLM 节点已经使用这个错误码。

本节继续复用，避免项目里出现多个表达同一问题的错误码。

这是统一异常设计。

### 8. create_ticket_agent_model_dependencies

这是本节最重要的工厂函数：

```python
def create_ticket_agent_model_dependencies(
    mode: TicketAgentModelMode | None = None,
    *,
    settings: Settings | None = None,
    client: Any | None = None,
) -> TicketAgentModelDependencies:
```

它有三个输入：

```text
mode
-> 显式指定模式；不传则读 settings.ticket_agent_model_mode。

settings
-> 配置对象；不传则 get_settings()。

client
-> 真实 LLM 使用的 OpenAI-compatible client；测试时可以传 fake client。
```

这行很关键：

```python
selected_mode = mode or selected_settings.ticket_agent_model_mode
```

它表示：

```text
调用方显式传 mode 时，优先使用传入 mode。
否则使用配置文件里的 ticket_agent_model_mode。
```

三条分支：

```python
if selected_mode == "rule_based":
    return {
        "mode": "rule_based",
        "intent_classifier": None,
        "field_extractor": None,
    }
```

规则模式返回 `None`，让 graph 使用默认规则。

```python
if selected_mode == "fake_llm":
    return {
        "mode": "fake_llm",
        "intent_classifier": FakeLLMTicketIntentClassifier(),
        "field_extractor": FakeLLMTicketFieldExtractor(),
    }
```

fake 模式返回两个 fake 实现。

```python
if selected_mode == "real_llm":
    ensure_real_ticket_agent_llm_is_configured(selected_settings)
    return {
        "mode": "real_llm",
        "intent_classifier": create_llm_ticket_intent_classifier(...),
        "field_extractor": create_llm_ticket_field_extractor(...),
    }
```

真实模式先检查 key，再创建真实组件。

最后还有：

```python
raise ValueError(f"Unsupported ticket agent model mode: {selected_mode}")
```

理论上 `Literal` 和 Pydantic 已经会拦住非法模式。

但是保留这行有意义。

因为函数也可能被 Python 代码直接用错。

这是防御式编程。

### 9. build_ticket_agent_graph_for_model_mode

新增：

```python
def build_ticket_agent_graph_for_model_mode(...):
    dependencies = create_ticket_agent_model_dependencies(
        mode,
        settings=settings,
        client=client,
    )

    return build_ticket_agent_graph(
        ticket_creator=ticket_creator,
        policy_rag_service=policy_rag_service,
        intent_classifier=dependencies["intent_classifier"],
        field_extractor=dependencies["field_extractor"],
        checkpointer=checkpointer,
        interrupt_confirmation=interrupt_confirmation,
    )
```

它的作用是：

```text
把“模式选择”变成“graph 依赖注入”。
```

你可以这样理解：

```text
create_ticket_agent_model_dependencies()
-> 负责选零件

build_ticket_agent_graph_for_model_mode()
-> 负责把零件装进 graph

build_ticket_agent_graph()
-> 负责真正编译 LangGraph
```

分工清楚以后，后面继续扩展就容易了。

例如后面可能会做：

```text
real_llm_with_retry
real_llm_with_fallback
eval_llm
prompt_v2
```

到时候不需要把每个节点都改乱。

---

## 七、本节测试重点

本节新增：

```text
projects/ai-service/tests/test_ticket_agent_llm_modes.py
```

并扩展：

```text
projects/ai-service/tests/test_config.py
```

测试部分不用死记每一行。

你重点理解这些测试保护的边界。

### 1. 默认模式必须是 rule_based

测试验证：

```python
assert settings.ticket_agent_model_mode == "rule_based"
```

意义：

```text
项目默认不调真实模型。
```

### 2. 环境变量可以切到 fake_llm

测试验证：

```python
monkeypatch.setenv("TICKET_AGENT_MODEL_MODE", "fake_llm")
assert settings.ticket_agent_model_mode == "fake_llm"
```

意义：

```text
模式确实可以通过 .env / 环境变量控制。
```

### 3. env 文件可以切到 real_llm

测试验证临时 `.env` 里的：

```env
TICKET_AGENT_MODEL_MODE="real_llm"
```

能被读取。

意义：

```text
手动真实模型 smoke 时，可以通过本机 .env 显式开启。
```

### 4. 错误模式会被拒绝

测试验证：

```python
Settings(ticket_agent_model_mode="production", _env_file=None)
```

会触发：

```text
literal_error
```

意义：

```text
配置拼错不要拖到运行中才发现。
```

### 5. 工厂函数默认返回规则模式依赖

测试验证：

```python
dependencies == {
    "mode": "rule_based",
    "intent_classifier": None,
    "field_extractor": None,
}
```

意义：

```text
默认 graph 不需要任何模型对象。
```

### 6. fake_llm 模式返回 fake 组件

测试验证：

```python
isinstance(dependencies["intent_classifier"], FakeLLMTicketIntentClassifier)
isinstance(dependencies["field_extractor"], FakeLLMTicketFieldExtractor)
```

意义：

```text
fake 模式确实不是 None，也不是 real LLM。
```

### 7. real_llm 没有 key 会失败

测试验证：

```python
create_ticket_agent_model_dependencies("real_llm", settings=Settings(...无 key...))
```

会抛：

```text
LLM_API_KEY_MISSING
```

意义：

```text
真实模型模式不能在缺 key 时悄悄继续。
```

### 8. 构建 real_llm 依赖不应该立即调用 client

测试验证：

```python
assert completions.calls == []
```

意义：

```text
创建依赖不是执行模型调用。
```

### 9. 默认 graph 即使传了 client 也不会调模型

测试传入 fake client，但使用默认规则模式。

然后断言：

```python
assert completions.calls == []
```

意义：

```text
默认 rule_based 不会因为传了 client 就误调模型。
```

### 10. real_llm graph 可以用 fake client 测试

测试构建真实模式 graph，但 client 是 fake 的。

这不是偷懒。

这是标准测试方法。

它验证：

- graph 确实把 `LLMTicketIntentClassifier` 注入了节点。
- 节点确实调用了 OpenAI-compatible client。
- 调用参数里 model 正确。
- `response_format={"type": "json_object"}` 没丢。
- 返回 JSON 会被 Pydantic 解析。
- 后续 graph 能继续走到直接回答节点。

---

## 八、如何手动使用三种模式

### 1. 默认规则模式

本机 `.env` 不写也行。

或者显式写：

```env
TICKET_AGENT_MODEL_MODE="rule_based"
```

适合：

- 平时写代码。
- 跑全量测试。
- 不想启动任何外部服务。
- 不想消耗模型额度。

### 2. fake LLM 模式

本机 `.env` 写：

```env
TICKET_AGENT_MODEL_MODE="fake_llm"
```

适合：

- 验证 graph 能不能注入模型形态组件。
- 验证 JSON/Pydantic 边界。
- 验证字段来源标记。
- 学习模型模式的工程结构。

注意：

```text
fake_llm 不需要 LLM_API_KEY。
```

### 3. 真实 LLM 模式

本机 `.env` 写：

```env
TICKET_AGENT_MODEL_MODE="real_llm"
LLM_PROVIDER="aliyun-compatible"
LLM_MODEL="qwen3.7-plus"
LLM_BASE_URL="你的 OpenAI-compatible base_url"
LLM_API_KEY="你的本机 API key"
```

适合：

- 手动 smoke。
- prompt 调试。
- 真实模型效果检查。
- 后续接入 eval。

注意：

```text
真实 API key 只放本机 .env。
.env.example 只能放空值或占位说明。
不要把真实 key 提交到 GitHub。
```

---

## 九、常见误区

### 误区 1：fake_llm 能证明真实模型效果

不能。

fake LLM 只能证明工程链路能跑。

真实模型理解能力、稳定性、成本、延迟，都要用真实调用和 eval 判断。

### 误区 2：有了 real_llm 就不需要 rule_based

不是。

规则模式仍然适合：

- 默认开发。
- 快速测试。
- 明确安全边界。
- 稳定兜底。

真实模型不是替代所有规则。

### 误区 3：测试里调用真实模型更真实，所以更好

自动化测试追求稳定可重复。

真实模型测试适合单独放进 smoke 或 eval。

把真实模型放进默认 pytest，会让测试变慢、不稳定、难排查。

### 误区 4：只要 `.env` 配了 key，就应该自动真实调用

不应该。

有 key 不代表当前运行就想调模型。

所以本节还需要 `TICKET_AGENT_MODEL_MODE="real_llm"` 显式开启。

### 误区 5：模式切换就是到处写 if

不是。

好的模式切换应该集中在工厂函数或配置层。

节点本身仍然只依赖接口。

---

## 十、本节练习

### 练习 1：解释三种模式

题目：用自己的话解释 `rule_based`、`fake_llm`、`real_llm` 三种模式分别适合什么时候用。

参考答案：

`rule_based` 适合默认开发和稳定回归，它不调用模型、不需要 key、结果确定。

`fake_llm` 适合测试模型形态的工程边界，它不调用真实模型，但会走 JSON 到 Pydantic 的解析校验路径。

`real_llm` 适合手动 smoke、真实效果验证和后续 eval，它会调用配置好的 OpenAI-compatible 模型，所以必须有 API key。

### 练习 2：判断 fake_llm 的价值

题目：`fake_llm` 不调用真实模型，那它还有什么价值？

参考答案：

它的价值不是验证模型智能，而是验证工程链路。它能让代码走过“模拟 JSON 输出 -> Pydantic 校验 -> Agent state -> LangGraph 后续节点”的路径，同时保持测试稳定、不依赖网络、不消耗 token。

### 练习 3：为什么默认不能是 real_llm

题目：为什么 `TICKET_AGENT_MODEL_MODE` 默认值要是 `rule_based`，而不是 `real_llm`？

参考答案：

因为默认运行项目时不应该自动触发真实模型调用。真实模型需要 API key、网络、可能产生费用，并且输出不完全稳定。默认 `rule_based` 可以保证新人拉项目后没有 key 也能跑，自动测试也不会误调外部服务。

### 练习 4：解释依赖注入

题目：为什么 `classify_intent_node` 不应该在函数内部固定创建 `LLMTicketIntentClassifier`？

参考答案：

如果节点内部固定创建真实 LLM 分类器，测试就很难替换，默认运行也可能误调真实模型。通过依赖注入，外部可以传入不同 classifier：不传就是规则模式，传 fake 就是 fake 模式，传真实分类器就是真实模型模式。节点只关心 classifier 是否能 `classify_intent()`，不关心它来自哪里。

### 练习 5：写出真实模式配置

题目：如果你要手动开启真实 LLM 模式，本机 `.env` 至少要配置哪些关键字段？

参考答案：

至少要配置：

```env
TICKET_AGENT_MODEL_MODE="real_llm"
LLM_MODEL="qwen3.7-plus"
LLM_BASE_URL="你的 OpenAI-compatible base_url"
LLM_API_KEY="你的本机 API key"
```

如果供应商或项目需要，也可以配置：

```env
LLM_PROVIDER="aliyun-compatible"
REQUEST_TIMEOUT_SECONDS=30
LLM_MAX_RETRIES=2
```

### 练习 6：判断测试边界

题目：为什么本节 `real_llm` 的自动测试仍然用 `FakeOpenAICompatibleClient`？

参考答案：

因为自动测试要验证的是项目代码是否正确调用 client、是否传入正确参数、是否能解析返回 JSON、是否能继续执行 graph，而不是验证真实模型服务是否可用。真实模型可用性和效果应该放到手动 smoke 或后续 eval 中验证。

---

## 十一、自测题

### 自测 1

题目：`fake_llm` 会不会调用真实模型？

答案：不会。`fake_llm` 使用本地规则生成结果，再把结果转成 JSON 并交给 Pydantic 校验。

### 自测 2

题目：`fake_llm` 能不能证明 prompt 写得很好？

答案：不能。因为 `fake_llm` 根本没有调用真实模型，也没有使用真实模型理解 prompt。它只能验证工程链路。

### 自测 3

题目：`real_llm` 模式缺少 API key 时，应该在什么阶段报错？

答案：应该在创建真实模型依赖时尽早报错，错误码是 `LLM_API_KEY_MISSING`。这样比等到底层 SDK 调用时报错更清楚。

### 自测 4

题目：为什么 `create_ticket_agent_model_dependencies()` 返回的 `intent_classifier` 在 `rule_based` 模式下是 `None`？

答案：因为 `None` 在这里表示使用 graph 节点内部的默认规则函数。它不是缺少依赖，而是明确选择规则模式。

### 自测 5

题目：`build_ticket_agent_graph_for_model_mode()` 和 `build_ticket_agent_graph()` 有什么区别？

答案：`build_ticket_agent_graph_for_model_mode()` 根据模式先创建依赖，再调用 `build_ticket_agent_graph()`。`build_ticket_agent_graph()` 是底层图构建函数，直接接收已经选好的依赖对象。

### 自测 6

题目：为什么本节要在 `.env.example` 里写 `TICKET_AGENT_MODEL_MODE`，但不能写真实 API key？

答案：`.env.example` 是给配置结构看的，可以提交到 GitHub；真实 API key 是敏感信息，只能放本机 `.env`，不能提交。

### 自测 7

题目：如果以后真实模型输出经常不稳定，是不是应该删除 `fake_llm`？

答案：不应该。真实模型不稳定说明需要改 prompt、校验、降级或 eval；`fake_llm` 仍然负责稳定验证工程边界。

### 自测 8

题目：为什么构建真实 LLM 依赖时，不应该立刻调用模型？

答案：因为创建对象和执行业务是两件事。构建依赖只应该准备对象，真正调用模型应该发生在 graph 节点执行时，这样边界更清楚、测试更稳定、日志也更准确。

---

## 十二、面试表达版

如果面试官问：

```text
你们项目里真实 LLM 是怎么测试和启用的？
```

可以这样回答：

```text
我们没有让真实 LLM 成为默认测试依赖，而是把 Agent 模型执行方式拆成了 rule_based、fake_llm 和 real_llm 三种模式。

rule_based 是默认模式，用于本地开发和稳定回归，不需要 API key，也不会发网络请求。

fake_llm 不调用真实模型，但会把规则结果转成 JSON，再走同一套 Pydantic 校验路径，用来测试模型输出边界、依赖注入和 LangGraph 执行链路。

real_llm 会使用配置里的 OpenAI-compatible client，只有显式设置 TICKET_AGENT_MODEL_MODE=real_llm 并配置 LLM_API_KEY 后才启用。自动化测试里我们用 fake client 验证调用参数和解析流程，真实模型效果则放到 smoke 或后续 eval 中验证。
```

这个回答体现了几个能力：

- 知道真实 LLM 不能直接进入默认测试。
- 知道 fake 的价值是工程边界，不是模型智能。
- 知道配置、依赖注入、Pydantic 校验和 LangGraph graph 构建之间的关系。
- 知道 API key 安全边界。
- 知道真实效果要靠 smoke/eval，而不是靠单元测试硬跑供应商服务。

---

## 十三、本节小结

本节完成了一件生产化 AI 项目里很重要的事：

```text
把“是否真实调用模型”变成明确配置，而不是散落在代码里的临时选择。
```

你现在应该记住这条主线：

```text
Settings 读取 TICKET_AGENT_MODEL_MODE
-> 工厂函数选择依赖
-> graph 构建入口注入依赖
-> 节点通过接口调用分类器和字段提取器
-> Pydantic 负责接住模型形态输出
```

本节不是为了多写几个类。

它真正补的是工程判断：

```text
稳定开发、自动测试、真实模型验证，不能混成一条默认路径。
```

下一节进入：

```text
阶段 6 第 17 节：prompt 版本管理
```

有了模式切换之后，才适合继续管理 prompt。

因为后面我们会开始面对一个新问题：

```text
同一个真实模型节点，如果 prompt 改了，怎么记录版本、怎么比较效果、怎么避免改坏后不知道？
```
