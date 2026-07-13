# 阶段 3 第 17 节：工具调用测试：fake Java API / fake tool

> 本节结论：AI 工具调用链路不能靠真实模型、真实 Java 服务和手动点接口来验证。测试要分层：模型用 fake client，工具依赖用 fake object，HTTP 边界用 `httpx.MockTransport`，FastAPI 路由用 dependency override。这样测试稳定、便宜、可重复，也能明确定位失败到底发生在哪一层。

## 生成笔记前的教学复核

本节必须满足这些教学要求：

```text
1. 先讲清楚为什么 AI 工具调用测试不能依赖真实模型和真实外部服务。
2. 系统讲解 fake、mock、stub、dependency override、MockTransport 的区别。
3. 讲清 service 测试、client 测试、router 测试分别验证什么。
4. 讲清哪些东西应该 fake，哪些东西不应该 fake。
5. 代码只讲测试辅助模块和关键测试边界，不逐行讲所有测试。
6. 让学习者能不看代码说清：一个工具调用链路应该怎么分层测试。
7. 不提前学习 pytest 高级插件、测试覆盖率平台、契约测试平台、真实 CI/CD。
```

## 本节一句话定位

第 17 节是在第 13-16 节的工具调用链路基础上，学习如何把“模型、工具、Java API、FastAPI 路由”拆开测试，避免自动化测试依赖真实模型和真实外部服务。

## 本节解决的真实问题

前面我们已经实现了：

```text
模型决定是否调用工具
-> 后端执行只读工具
-> 工具结果交给模型总结
-> 写操作需要确认
-> 确认后调用 Java mock 创建工单
-> 日志和 trace_id 串联
```

如果测试方式不对，会出现几个问题：

```text
每次测试都真实调用模型 -> 花钱、慢、不稳定
每次测试都启动 Java 服务 -> 麻烦、容易端口冲突
测试结果依赖网络 -> 今天过，明天可能失败
一个端到端测试失败 -> 不知道是模型错、工具错、HTTP client 错还是路由错
为了测试方便绕过校验 -> 线上风险反而被测试掩盖
```

本节要解决的是：

```text
如何用 fake 和 mock 把外部不稳定因素替换掉，同时仍然验证关键业务规则。
```

## 本节新增能力

学完后你应该能做到：

- 知道什么时候用 fake 模型，什么时候用 fake tool；
- 知道什么时候用 `httpx.MockTransport` 测 HTTP client；
- 知道 FastAPI 的 dependency override 解决什么问题；
- 能把一个工具调用链路拆成 service 测试、client 测试、router 测试；
- 能判断测试是否过度依赖外部服务；
- 能解释为什么自动化测试不应该真实调用 LLM。

## 和上一节的区别

第 16 节学的是：

```text
工具链路运行时怎么记录日志，出错后怎么排查。
```

第 17 节学的是：

```text
工具链路上线前怎么用自动化测试验证，尽量不让错误跑到运行时。
```

简单说：

```text
第 16 节：出问题后怎么查
第 17 节：提交前怎么测
```

## 基础知识铺垫

### 1. 什么是自动化测试

人话解释：自动化测试就是让程序自己验证程序，而不是每次都靠人手动点接口。

例如你写了一个订单查询工具，自动化测试可以帮你反复验证：

```text
订单存在时返回正确字段
订单不存在时返回 ORDER_NOT_FOUND
Java 返回 500 时映射成 TOOL_UPSTREAM_ERROR
模型参数错误时不会执行工具
```

工程术语：automated tests。它们应该可重复、可快速运行、结果稳定。

当前项目使用：

```text
pytest
FastAPI TestClient
httpx.MockTransport
fake OpenAI-compatible client
dependency_overrides
```

### 2. 为什么 AI 测试不能真实调用模型

真实调用模型有几个问题：

1. 成本：每次测试都会花 token；
2. 速度：模型调用比本地函数慢很多；
3. 不稳定：模型输出可能轻微变化；
4. 外部依赖：服务商网络、限流、余额都会影响测试；
5. 难定位：失败时不知道是你代码错，还是模型这次输出变了；
6. 安全：测试环境不应该依赖真实 API key。

自动化测试要验证的是：

```text
我们的代码如何处理模型输出。
```

不是验证：

```text
某个真实模型今天会不会按我们希望回答。
```

真实模型调用可以放到手动 smoke test 或评测系统里，不应该放进普通单元测试。

### 3. 什么是 fake

fake 是一个“能工作但很简化的替身”。

例如真实模型 client 会通过网络调用大模型。fake 模型 client 不走网络，只返回你预设的内容：

```text
真实 LLM client：发 HTTP 请求给模型服务商
FakeOpenAICompatibleClient：直接返回 make_chat_completion(...)
```

fake 的特点：

- 行为可控；
- 速度快；
- 不依赖外部服务；
- 可以记录调用参数；
- 适合替换模型、工具、业务 client。

当前项目里：

```text
tests/fakes.py        模型 fake
tests/tool_fakes.py   工具和业务服务 fake
```

### 4. 什么是 mock

mock 也是测试替身，但更强调“验证交互”。

例如你想验证：

```text
JavaTicketClient 是否真的 POST /tickets？
是否带了 Idempotency-Key？
是否带了 X-Trace-Id？
```

这时你不只是要一个返回值，还要检查请求细节。

当前项目用 `httpx.MockTransport` 来模拟 HTTP 服务。它能接住 HTTP 请求，让测试检查：

```text
request.method
request.url.path
request.headers
request.content
```

### 5. 什么是 stub

stub 是更简单的替身，通常只返回固定结果。

例如：

```python
lambda arguments: make_query_order_result()
```

它不关心记录了什么，也不模拟复杂错误，只是让被测代码继续往下走。

区别可以这样理解：

| 名称 | 重点 | 当前项目例子 |
| --- | --- | --- |
| stub | 给固定返回值 | `lambda arguments: make_query_order_result()` |
| fake | 简化但可用的替身 | `FakeTicketCreator` |
| mock | 验证交互细节 | `httpx.MockTransport` 检查 header/path |

实际工作里这些词有时会混用，但你要理解背后的测试目的。

### 6. 什么是 dependency override

FastAPI 的 dependency override 是测试时替换依赖的机制。

真实接口运行时：

```text
/tickets/plans
-> get_ticket_workflow_service()
-> create_ticket_workflow_service(settings)
-> 真实模型服务 + 真实 JavaTicketClient
```

测试时我们不想真实调模型和 Java，于是替换成：

```text
app.dependency_overrides[get_ticket_workflow_service] = lambda: fake_workflow
```

这样 router 仍然走真实 HTTP 请求、真实 Pydantic 校验、真实响应模型，但内部 service 是假的。

这适合测试：

```text
路由路径是否正确
请求体校验是否正确
响应状态码是否正确
依赖注入是否接上
错误响应是否统一
```

### 7. 什么是 `httpx.MockTransport`

`httpx.MockTransport` 是 httpx 提供的测试工具。它可以拦截 HTTP client 发出的请求，不真正访问网络。

例如：

```text
JavaOrderClient.get_order("A1001")
-> client.get("/orders/A1001")
-> MockTransport handler 收到 request
-> handler 返回 httpx.Response(200, json=...)
```

它适合测试 HTTP adapter，也就是：

```text
JavaOrderClient
JavaTicketClient
```

因为这些类真正关心 HTTP 方法、路径、header、状态码和 JSON。

### 8. 什么是测试边界

测试边界就是“这个测试到底测到哪一层为止”。

如果边界不清，测试会变得很乱。

比如：

```text
测试 /tickets/plans 时同时真实调用模型和 Java 服务
```

这就是边界过大。失败时很难定位。

更好的拆法：

```text
测试 structured_output_service：fake 模型输出 JSON
测试 ticket_workflow_service：fake extractor + fake ticket creator
测试 JavaTicketClient：MockTransport 模拟 Java HTTP 响应
测试 /tickets API：dependency override 替换 workflow service
```

每一层只测自己该负责的东西。

### 9. 什么是单元测试、集成测试、端到端测试

简单理解：

| 类型 | 测什么 | 速度 | 当前项目例子 |
| --- | --- | --- | --- |
| 单元测试 | 一个函数/一个 service 的规则 | 快 | `build_create_ticket_args()` |
| 集成测试 | 几个模块一起工作 | 中 | `TicketWorkflowService + fake dependencies` |
| 端到端测试 | 尽量接近真实环境 | 慢 | 真实模型 + 真实 Java 服务 |

本阶段主要写单元测试和轻量集成测试。

真实端到端测试以后会学，但不会放进每次都跑的普通测试里。

### 10. 为什么测试也要防止敏感信息

测试里也不能写真实 API key。

错误示例：

```python
Settings(llm_api_key="sk-real-key")
```

正确做法：

```python
Settings(llm_api_key="test-key")
```

测试数据也应该是假的：

```text
demo_user_001
A1001
T1001
```

不要把真实用户、真实订单、真实投诉内容写进测试。

## 本节主题系统讲解

### 1. AI 工具调用链路为什么必须分层测试

AI 工具调用链路包含很多不稳定因素：

```text
模型输出不稳定
网络不稳定
Java 服务可能不可用
时间和 TTL 可能变化
幂等状态可能残留
日志和 trace_id 依赖请求上下文
```

如果写一个大测试把所有东西串起来：

```text
真实 HTTP 请求
-> 真实模型
-> 真实工具
-> 真实 Java 服务
-> 真实返回
```

看起来完整，但维护成本很高。失败时很难判断问题在哪。

所以我们要分层：

```text
模型层：fake LLM
工具业务层：fake tool / fake client
HTTP client 层：MockTransport
FastAPI 层：dependency override
```

每层都只验证自己的责任。

### 2. 模型 fake 应该测什么

模型 fake 不测试“模型聪不聪明”，它测试我们的代码如何处理模型响应。

应该测：

- 模型返回普通文本时怎么处理；
- 模型返回 tool_calls 时怎么处理；
- 模型返回非法 JSON 时怎么处理；
- 模型返回多个工具调用时是否拒绝；
- 模型调用报错时是否映射成项目错误；
- token usage 是否能提取；
- streaming chunk 是否能处理。

当前项目的 `tests/fakes.py` 做了这些事情：

```text
FakeChatCompletions
FakeOpenAICompatibleClient
make_chat_completion
make_tool_call
make_stream_chunk
make_status_error
```

### 3. 工具 fake 应该测什么

工具 fake 不测试 HTTP 协议，它测试工具业务逻辑。

以订单查询为例，`FakeOrderLookupClient` 替代真实 Java order client：

```text
query_order()
-> fake_client.get_order(order_id)
-> 返回固定 Java 订单 payload
-> 映射成 QueryOrderResult
```

它适合测试：

- 字段映射；
- 不暴露 `customer_id`；
- Java 返回缺字段时 Pydantic 校验失败；
- Java client 抛 `ORDER_NOT_FOUND` 时保留错误；
- Java client 抛未知错误时映射成 `TOOL_CALL_FAILED`。

### 4. HTTP MockTransport 应该测什么

`MockTransport` 测的是 HTTP adapter 这一层。

比如 `JavaTicketClient` 应该验证：

- 请求方法是 `POST`；
- 路径是 `/tickets`；
- body 是 `CreateTicketArgs` 转出的 JSON；
- header 里有 `Idempotency-Key`；
- header 里有 `X-Trace-Id`；
- 201 时解析成 `CreatedTicket`；
- 500 时映射成 `TOOL_UPSTREAM_ERROR`；
- 非 JSON 时映射成 `TOOL_RESULT_VALIDATION_FAILED`。

它不应该测试模型，也不应该测试 FastAPI router。

### 5. Router 测试应该测什么

Router 测试关注 HTTP 边界：

- URL 是否正确；
- 方法是否正确；
- 请求体验证是否生效；
- response_model 是否生效；
- 状态码是否正确；
- 错误响应是否统一；
- `X-Trace-Id` 是否返回；
- dependency override 是否接上。

Router 测试不应该真实调用模型和 Java。

比如 `/tickets/plans` 测试时，我们用 fake workflow，保证测试重点是：

```text
FastAPI 路由和请求/响应协议
```

不是：

```text
模型服务商今天是否可用
```

### 6. Service 测试应该测什么

Service 测试关注业务编排：

以 `TicketWorkflowService` 为例：

```text
plan_ticket()
-> fake extractor 返回 TicketExtraction
-> build_create_ticket_args()
-> confirmation_service 创建计划

execute_confirmed_ticket()
-> 检查 confirmed
-> 校验 CreateTicketArgs
-> fake ticket creator 创建工单
-> 幂等复用结果
```

它适合测试：

- unknown intent 不乱猜；
- 未确认不能执行；
- actor 不一致不能执行；
- 参数坏了不能执行；
- 同一确认重复执行不会重复创建；
- fake ticket creator 是否只被调用一次。

### 7. 什么东西不要 fake

不是所有东西都要 fake。

一般不要 fake：

- Pydantic 模型校验；
- 关键业务转换函数；
- 错误映射函数；
- 幂等逻辑本身；
- 权限守卫；
- 确认状态机。

如果这些都 fake 掉，测试就只是在测试 fake，不是在测试你的业务逻辑。

应该 fake 的是外部不稳定依赖：

```text
LLM provider
Java HTTP service
网络
时间较难控制的外部系统
```

### 8. 好测试应该长什么样

好的工具调用测试应该具备：

```text
稳定：不依赖真实网络和真实模型
快速：本地毫秒级完成
明确：失败能看出是哪一层问题
真实：保留关键业务校验，不绕过核心规则
安全：不使用真实 key，不写真实敏感数据
可维护：fake 集中复用，不到处复制
```

坏测试常见表现：

```text
必须联网才能跑
偶尔失败
失败原因不清楚
测试里写真实 API key
所有逻辑都 mock 掉
fake 散落在很多文件里，行为不一致
```

### 9. 本节为什么新增 `tests/tool_fakes.py`

之前工具相关 fake 分散在测试文件里：

```text
test_fake_order_tool.py 里有 FakeOrderLookupClient
test_ticket_workflow_service.py 里有 FakeExtractor / FakeTicketCreator
test_tickets_api.py 又有一份类似 fake
```

这会带来问题：

- 重复；
- 行为不一致；
- 后续改字段时要改很多地方；
- 学习时看不出 fake 的统一边界。

所以本节新增：

```text
tests/tool_fakes.py
```

集中放：

```text
FakeOrderLookupClient
FakeTicketExtractor
FakeTicketCreator
make_java_order_payload()
make_ticket_extraction()
make_created_ticket()
```

这让测试策略更清楚：

```text
tests/fakes.py       模型 fake
tests/tool_fakes.py  工具/业务 fake
MockTransport        HTTP adapter fake server
dependency_overrides Router 层替换 service
```

## 最小心智模型

记住这 6 行：

```text
不要在普通自动化测试里真实调用模型
不要让测试依赖真实 Java 服务
模型输出用 fake LLM
工具依赖用 fake object
HTTP client 用 MockTransport
FastAPI router 用 dependency override
```

## 当前项目如何落地

本节新增和整理：

```text
tests/tool_fakes.py
  工具和业务服务测试替身

tests/test_tool_fakes.py
  验证这些 fake 自身行为稳定

tests/test_fake_order_tool.py
  使用共享 FakeOrderLookupClient

tests/test_ticket_workflow_service.py
  使用共享 FakeTicketExtractor / FakeTicketCreator

tests/test_tickets_api.py
  使用共享 fake 组装 router 测试
```

已有测试继续保留：

```text
tests/fakes.py
  模型 fake

tests/test_java_order_client.py
tests/test_java_ticket_client.py
  使用 httpx.MockTransport 测 HTTP adapter
```

## 关键代码讲解

### 1. `tests/tool_fakes.py`

这个文件不是生产代码，只服务测试。

它做三类事：

```text
构造测试数据：make_java_order_payload / make_ticket_extraction / make_created_ticket
模拟依赖对象：FakeOrderLookupClient / FakeTicketExtractor / FakeTicketCreator
记录调用信息：calls / messages / idempotency_keys
```

为什么 fake 要记录调用？

因为很多测试不只是关心返回结果，还要确认：

```text
工具是否被调用
调用了几次
传入的 order_id 是什么
幂等键是否传对
```

### 2. `FakeOrderLookupClient`

它替代真实 `JavaOrderClient`，只实现工具需要的接口：

```python
get_order(order_id)
```

它可以：

- 返回固定订单 payload；
- 记录调用过的 order_id；
- 抛出预设错误。

这让 `query_order()` 测试不需要 HTTP。

### 3. `FakeTicketExtractor`

它替代真实模型字段提取。

真实 extractor 会调用模型。fake extractor 直接返回预设 `TicketExtraction`。

这让 `TicketWorkflowService.plan_ticket()` 能专心测试：

```text
模型提取结果 -> CreateTicketArgs -> confirmation plan
```

而不是测试模型服务。

### 4. `FakeTicketCreator`

它替代真实 `JavaTicketClient`。

它可以：

- 返回固定 `CreatedTicket`；
- 记录 `CreateTicketArgs`；
- 记录 `idempotency_key`；
- 抛出预设错误。

这让 `execute_confirmed_ticket()` 能测试确认计划消费和幂等，而不需要 Java 服务。

### 5. 为什么还保留 `MockTransport`

fake object 适合 service 测试，但不能验证 HTTP 请求细节。

例如你想知道 `JavaTicketClient` 是否真的发送：

```text
POST /tickets
Idempotency-Key: ...
X-Trace-Id: ...
```

这必须用 `MockTransport`。所以 fake 和 MockTransport 不是互相替代，而是服务不同测试层。

## 常见误区和排查

| 误区 | 问题 | 正确做法 |
| --- | --- | --- |
| 自动化测试真实调模型 | 慢、贵、不稳定 | 用 fake LLM |
| 所有测试都启动 Java 服务 | 外部依赖重、端口冲突 | client 层用 MockTransport，service 层用 fake |
| 所有逻辑都 mock 掉 | 测不到真实业务规则 | 只替换外部依赖，保留校验和编排 |
| fake 到处复制 | 行为不一致、维护困难 | 集中到 `tests/tool_fakes.py` |
| router 测试直接测真实 service | 容易跨太多层 | 用 dependency override 控制边界 |
| 只测成功路径 | 错误处理不可靠 | 同时测超时、404、500、参数错误 |
| 测试写真实 key | 安全风险 | 使用 `test-key` 或 fake settings |

## 手动验证方式

本节主要靠自动化测试验证。你可以运行：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run pytest tests/test_tool_fakes.py tests/test_fake_order_tool.py tests/test_ticket_workflow_service.py tests/test_tickets_api.py tests/test_java_order_client.py tests/test_java_ticket_client.py -q
```

如果你想观察 fake 的意义，可以对比：

```text
test_fake_order_tool.py
  不发 HTTP，直接 fake Java order client

test_java_order_client.py
  发 httpx 请求，但由 MockTransport 接住，不访问真实网络

test_tickets_api.py
  走 FastAPI TestClient，但 workflow service 被 dependency override 替换
```

## 重要测试说明

本节新增：

```text
tests/test_tool_fakes.py
```

它验证：

- fake order client 能返回数据并记录调用；
- fake order client 能抛出预设错误；
- fake ticket extractor 能返回预设模型提取结果；
- fake ticket creator 能记录幂等键；
- fake ticket creator 能抛出预设 AppException。

这些测试看似简单，但价值是保证后续其他测试依赖的 fake 本身是可信的。

## 练习

### 练习 1：判断该用哪种测试替身

你要测试 `JavaTicketClient` 是否把 `Idempotency-Key` 放进 header，应该用 fake object 还是 `MockTransport`？

#### 参考答案

用 `MockTransport`。因为这里要验证 HTTP 请求细节，包括 header、method、path、body。fake object 更适合 service 层，不适合验证 HTTP adapter。

### 练习 2：为什么测试模型工具调用不用真实模型

#### 参考答案

真实模型输出不稳定、调用慢、会花钱、依赖 API key 和网络。自动化测试应该验证“代码如何处理模型输出”，所以应该用 fake LLM 返回固定 `tool_calls` 或固定文本。

### 练习 3：Router 测试为什么要 dependency override

#### 参考答案

Router 测试主要验证 HTTP 边界：路径、请求体、响应模型、状态码和统一错误格式。用 dependency override 可以替换真实 service，避免测试路由时顺便真实调用模型或 Java 服务。

### 练习 4：哪些逻辑不应该 fake

下面哪些应该尽量保留真实逻辑？

```text
Pydantic 请求校验
确认状态机
真实 LLM provider
幂等逻辑
Java 外部网络服务
权限守卫
```

#### 参考答案

应该保留真实逻辑：Pydantic 请求校验、确认状态机、幂等逻辑、权限守卫。

应该替换掉：真实 LLM provider、Java 外部网络服务。

### 练习 5：一个测试失败时怎么定位边界

如果 `TicketWorkflowService` 的测试失败，优先怀疑哪些层？

#### 参考答案

优先怀疑 service 编排、确认计划、参数转换、幂等或 fake 设置。因为该测试已经用 fake extractor 和 fake ticket creator 替换了模型和 Java 服务，所以不应该先怀疑真实模型或真实 Java 网络。

## 自测题

1. fake、mock、stub 的区别是什么？

   参考答案：stub 主要返回固定值；fake 是简化但可工作的替身；mock 更强调验证交互，比如请求路径、header、调用次数。

2. 为什么 `tests/fakes.py` 和 `tests/tool_fakes.py` 分开？

   参考答案：前者面向模型 API fake，后者面向工具和业务服务 fake。分开能让测试替身的职责更清楚。

3. `httpx.MockTransport` 适合测试哪一层？

   参考答案：适合测试 HTTP client/adapter 层，例如 `JavaOrderClient` 和 `JavaTicketClient`。

4. dependency override 适合测试哪一层？

   参考答案：适合 FastAPI router 层，用来替换依赖 service，让测试专注 HTTP 请求/响应边界。

5. 为什么不能把所有东西都 fake 掉？

   参考答案：如果把 Pydantic 校验、权限、幂等、确认状态机都 fake 掉，测试就不能验证真实业务规则，只是在验证 fake。

6. 好的工具调用测试应该具备哪些特征？

   参考答案：稳定、快速、边界清楚、不依赖真实模型和网络、保留关键业务校验、不使用真实敏感信息。

7. 本节对后续 LangChain/LangGraph 学习有什么帮助？

   参考答案：后续链路更复杂，如果现在不掌握 fake、MockTransport 和分层测试，进入 LangChain/LangGraph 后很容易写出慢、脆弱、难定位的测试。

## 本节你真正学会了什么

以前你已经会让工具调用链路跑起来，也会加日志排查。

本节你真正学的是：

```text
怎么在不调用真实模型、不依赖真实 Java 服务的情况下，把工具调用链路稳定测住。
```

你应该能不看代码讲出：

```text
模型层用 fake LLM；
工具业务层用 fake object；
HTTP adapter 层用 MockTransport；
FastAPI router 层用 dependency override；
核心业务校验、确认、权限和幂等不要 fake 掉。
```

如果你以后自己做一个新工具，比如 `query_refund`，应该先设计：

```text
工具参数模型怎么测
工具结果模型怎么测
service 层用什么 fake
Java client 层用什么 MockTransport
router 层怎么 override
错误路径测哪些
```

## 下一节衔接

第 18 节建议进入“LangChain 是什么，为什么现在才引入”。

我们已经手写过 Tool Calling 的底层流程、确认机制、Java 调用、日志和测试。现在再学 LangChain，才不会把它当魔法，而是能看懂它到底封装了哪些我们已经手写过的能力。
