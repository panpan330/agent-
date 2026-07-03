# AI 应用工程学习进度

> 维护目标：防止学习路线、已完成内容、待补能力和项目沉淀丢失。以后每完成一个小任务，就更新本文件的状态、日期、产出链接和复盘。

## 1. 总目标

从已有 Java 后端能力出发，转向 AI 应用工程方向，形成可以面试、可以落地、可以长期扩展的能力体系。

目标岗位方向：

- AI 应用开发工程师
- 后端 AI 工程师
- Java 后端 + LLM 应用工程师
- RAG / Agent 应用开发工程师

核心技术路线：

```text
Java 后端
  ↓
业务 API / 权限 / 数据库 / 工单 / 订单 / 报表
  ↓ REST / SSE / MQ
Python AI 服务
  ↓
FastAPI + LangChain + LangGraph
  ↓
LLM / Embedding / Vector DB / Rerank / Tool Calling / Eval
```

## 2. 当前状态

| 模块 | 状态 | 说明 |
| --- | --- | --- |
| Java 后端基础 | 进行中 | 已有一定掌握，后续重点是把 Java 业务 API 暴露给 AI 工具调用 |
| Python 工程基础 | 未开始 | 需要补 FastAPI、Pydantic、pytest、Docker、日志 |
| LLM API 基础 | 未开始 | 需要掌握 prompt、流式输出、结构化输出、tool calling、token 成本 |
| LangChain | 未开始 | 重点学习 model、prompt、chain、tools、retriever、structured output |
| RAG | 未开始 | 重点学习文档解析、chunk、embedding、向量库、rerank、引用来源、权限过滤 |
| LangGraph | 未开始 | 重点学习 StateGraph、node、edge、checkpoint、interrupt、human-in-the-loop |
| 生产化能力 | 未开始 | 重点学习日志、追踪、评测、限流、重试、成本统计、安全 |
| 项目作品 | 未开始 | 计划完成企业知识库 RAG、智能工单 Agent、业务数据助手 |

状态约定：

- 未开始：还没有系统学习或产出。
- 进行中：已经开始学习或编码，但还没有达到验收标准。
- 已完成：完成学习任务、代码产出和复盘。
- 需复习：已学过但不熟，或者项目中暴露出薄弱点。

## 3. 12 周学习计划

### 第 0 周：环境与仓库准备

目标：搭好长期学习环境和仓库结构。

任务清单：

- [x] 创建学习仓库结构。
- [x] 创建总进度文档。
- [ ] 安装 Python 3.11/3.12。
- [ ] 安装 uv 或 poetry。
- [ ] 安装 Docker / Docker Compose。
- [ ] 准备一个 OpenAI-compatible 模型 API。
- [ ] 准备 Java Spring Boot 测试服务。
- [ ] 确定向量库：Qdrant 或 PostgreSQL + pgvector。

验收标准：

- 能本地启动 Python 环境。
- 能本地启动 Java 测试服务。
- 能用 Docker 启动向量库。
- 仓库中有清晰的学习入口文档。

### 第 1 周：Python + FastAPI 工程基础

目标：能写一个标准 Python API 服务。

学习任务：

- [ ] Python 虚拟环境和依赖管理。
- [ ] FastAPI 路由、请求体、响应体。
- [ ] Pydantic 模型校验。
- [ ] 环境变量和配置管理。
- [ ] httpx / requests 调外部接口。
- [ ] logging 日志。
- [ ] pytest 基础测试。
- [ ] Dockerfile 基础。

练习产出：

- [ ] `/health` 健康检查接口。
- [ ] `/chat` 普通聊天接口。
- [ ] `/stream-chat` 流式聊天接口。
- [ ] 基础日志和异常处理。

验收标准：

- 服务能启动。
- 密钥不写死，统一从 `.env` 读取。
- 普通接口和流式接口都能调用模型。
- 有基础测试用例。

### 第 2 周：LLM API 基础

目标：理解大模型应用的基本运行机制。

学习任务：

- [ ] system prompt / user prompt / assistant message。
- [ ] temperature、top_p、max_tokens。
- [ ] streaming。
- [ ] structured output。
- [ ] function calling / tool calling。
- [ ] token 成本统计。
- [ ] 模型调用超时、重试和兜底。
- [ ] prompt injection 基础风险。

练习产出：

- [ ] 简历信息抽取接口。
- [ ] 客服意图分类接口。
- [ ] 长文本结构化摘要接口。

验收标准：

- 输出能被 Pydantic 校验。
- 模型格式错误时能重试或返回清晰错误。
- 接口返回耗时、模型名称和 token 消耗。

### 第 3 周：LangChain 核心组件

目标：会用 LangChain 组织模型、Prompt、工具和结构化输出。

学习任务：

- [ ] ChatModel。
- [ ] messages。
- [ ] prompt template。
- [ ] Runnable / chain。
- [ ] structured output + Pydantic。
- [ ] tools 定义和调用。
- [ ] streaming。
- [ ] callbacks / tracing 基础。

练习产出：

- [ ] 客服助手 v1。
- [ ] 至少 3 个 mock tool：查询订单、查询退款、查询物流。
- [ ] 每次 tool 调用都有日志。

验收标准：

- 用户自然语言提问后，AI 能判断是否调用工具。
- 工具入参有校验。
- 工具结果能被模型整合成自然语言回答。
- 支持流式输出。

### 第 4 周：Java 业务服务接入

目标：把 Java 后端优势接进 AI 系统。

Java API 任务：

- [ ] `GET /api/orders/{orderId}` 查询订单。
- [ ] `GET /api/refunds/{orderId}` 查询退款。
- [ ] `GET /api/tickets/{ticketId}` 查询工单。
- [ ] `POST /api/tickets` 创建工单。
- [ ] `GET /api/users/{userId}/permissions` 查询用户权限。

Python AI tool 任务：

- [ ] `query_order(order_id)`。
- [ ] `query_refund(order_id)`。
- [ ] `create_ticket(user_id, title, description, category)`。
- [ ] `query_user_permissions(user_id)`。

验收标准：

- AI 不直接查业务数据库。
- AI 只能通过 Java API 做业务动作。
- 高风险动作预留人工确认字段。
- Java API 有清晰错误码和日志。

### 第 5 周：RAG 入门，文档入库

目标：完成知识库的数据处理链路。

学习任务：

- [ ] RAG 基础流程：load -> split -> embed -> store -> retrieve -> generate。
- [ ] Markdown / txt 解析。
- [ ] PDF / docx 解析。
- [ ] chunk 切分策略。
- [ ] embedding 接入。
- [ ] 向量库写入和删除。
- [ ] metadata 设计。

推荐 metadata：

```text
doc_id
chunk_id
content
source
page
title
user_group
department
created_at
embedding
```

练习产出：

- [ ] 文档上传接口。
- [ ] 文档解析脚本。
- [ ] 文档切分并写入向量库。
- [ ] 按 `doc_id` 删除和重建索引。

验收标准：

- 上传一个 PDF 后能切成 chunks。
- 每个 chunk 有 metadata。
- 能查询向量库中的文档片段。

### 第 6 周：RAG 查询链路

目标：完成企业知识库问答 v1。

功能链路：

```text
用户提问
  ↓
问题向量化
  ↓
向量库 top_k 检索
  ↓
拼接 context
  ↓
LLM 基于 context 回答
  ↓
返回 answer + citations
```

学习任务：

- [ ] top_k。
- [ ] score_threshold。
- [ ] citations 引用来源。
- [ ] 无资料时拒答。
- [ ] 检索日志。
- [ ] Prompt 中约束“只能基于资料回答”。

练习产出：

- [ ] 企业知识库问答 v1。
- [ ] 至少 20 个测试问题。
- [ ] 每个回答带引用来源。

验收标准：

- 回答必须带引用。
- 引用能定位到文档和 chunk。
- 没有检索结果时不能胡编。
- 能看到检索到的 chunks。

### 第 7 周：RAG 进阶

目标：让 RAG 从 demo 变成可用系统。

学习任务：

- [ ] 权限过滤：user_group / user_id / department。
- [ ] 问题改写。
- [ ] 多路召回：向量检索 + 关键词检索。
- [ ] rerank。
- [ ] 上下文压缩。
- [ ] 召回失败兜底。
- [ ] 答案引用校验。

练习产出：

- [ ] 权限过滤版知识库。
- [ ] hybrid search 初版。
- [ ] rerank 初版。
- [ ] 检索命中率统计。

验收标准：

- 不同用户看到不同文档结果。
- 同一个问题能看到召回和 rerank 的差异。
- 有 hit / miss / low_score 统计。

### 第 8 周：LangGraph 基础

目标：掌握状态机式 Agent 编排。

学习任务：

- [ ] StateGraph。
- [ ] state schema。
- [ ] node。
- [ ] edge。
- [ ] conditional edge。
- [ ] checkpoint。
- [ ] thread_id。
- [ ] interrupt。

练习流程：

```text
接收用户问题
  ↓
分类：知识问答 / 工单 / 闲聊 / 业务查询
  ↓
不同分类走不同节点
  ↓
最终统一返回
```

验收标准：

- 每个节点职责单一。
- 状态里能看到中间结果。
- 条件分支可测试。
- 同一个 `thread_id` 能继续对话。

### 第 9 周：智能工单 Agent

目标：做一个真正能展示的 LangGraph 项目。

流程：

```text
用户描述问题
  ↓
问题分类
  ↓
检索知识库
  ↓
判断能否直接解决
  ↓
不能解决则提取工单字段
  ↓
让用户确认
  ↓
调用 Java API 创建工单
  ↓
返回工单号
```

工单字段：

```text
title
description
category
priority
user_id
related_order_id
evidence
```

练习产出：

- [ ] 智能工单 Agent v1。
- [ ] 问题分类节点。
- [ ] 知识库检索节点。
- [ ] 字段提取节点。
- [ ] 用户确认节点。
- [ ] 创建工单 tool 节点。

验收标准：

- 字段提取使用 structured output。
- 创建工单前必须 human confirmation。
- 用户补充信息后能继续上次流程。
- 创建成功后能查 Java 后端工单记录。

### 第 10 周：生产化能力

目标：项目像真实公司能上线的服务。

学习任务：

- [ ] 请求日志。
- [ ] 模型调用日志。
- [ ] tool 调用日志。
- [ ] token 成本统计。
- [ ] 超时控制。
- [ ] 失败重试。
- [ ] 限流。
- [ ] 缓存。
- [ ] Docker Compose。
- [ ] 健康检查。
- [ ] 错误码规范。

建议记录 `ai_trace`：

```text
trace_id
user_id
question
route
retrieved_chunks
tool_calls
final_answer
latency_ms
token_usage
cost
created_at
```

验收标准：

- 每次回答都能追踪完整链路。
- 出错时能定位是检索、模型、工具还是 Java API 问题。
- 服务可以 `docker compose up` 一键启动。

### 第 11 周：评测与优化

目标：不用感觉判断 AI 效果，而是用测试集评估。

测试集计划：

- [ ] 知识库问答 30 条。
- [ ] 工单场景 20 条。
- [ ] 订单/退款查询 20 条。
- [ ] 异常输入 10 条。
- [ ] 越权问题 10 条。

评测维度：

- [ ] 检索是否命中。
- [ ] 答案是否基于引用。
- [ ] 是否胡编。
- [ ] 工具是否调用正确。
- [ ] 字段提取是否正确。
- [ ] 是否越权。
- [ ] 响应耗时。

练习产出：

- [ ] `eval.py` 一键评测脚本。
- [ ] pass/fail 报告。
- [ ] prompt 或 chunk 策略调整前后的对比记录。

验收标准：

- 能一键跑评测。
- 能定位失败样例。
- 能用数据说明优化是否有效。

### 第 12 周：作品整理和面试准备

目标：形成能展示、能讲清楚的作品。

最终项目：

- [ ] 企业知识库 RAG。
- [ ] 智能工单 Agent。
- [ ] 业务数据助手，可作为加分项目。

每个项目需要整理：

- [ ] README。
- [ ] 架构图。
- [ ] 启动方式。
- [ ] 接口文档。
- [ ] 核心流程截图。
- [ ] 测试问题样例。
- [ ] 技术难点说明。
- [ ] 可优化点。

面试题准备：

- [ ] RAG 为什么会答错？
- [ ] chunk 大小怎么选？
- [ ] 向量检索和关键词检索区别？
- [ ] rerank 解决什么问题？
- [ ] Agent 为什么需要 LangGraph？
- [ ] tool calling 怎么保证安全？
- [ ] AI 为什么不能直接操作数据库？
- [ ] 如何评测一个知识库问答系统？

## 4. 长期必补能力

这些不是 12 周内全部吃透，但需要长期补齐。

| 能力 | 优先级 | 状态 | 说明 |
| --- | --- | --- | --- |
| Eval 评测体系 | 高 | 未开始 | AI 应用上线前必须能评估准确率、幻觉率、越权率 |
| Observability 可观测性 | 高 | 未开始 | 需要追踪 prompt、检索、tool、token、耗时、错误 |
| Prompt 版本管理 | 中 | 未开始 | 每次改 prompt 要能回滚和对比 |
| LLM 安全 | 高 | 未开始 | prompt injection、越权、工具误调用、数据泄露 |
| LLMOps | 中 | 未开始 | 部署、监控、灰度、成本控制、模型切换 |
| 数据工程基础 | 中 | 未开始 | 文档清洗、数据质量、批处理、增量更新 |
| 业务抽象能力 | 高 | 进行中 | 把真实业务流程拆成 AI 可编排的节点和工具 |
| PyTorch / 模型微调 | 低 | 未开始 | 暂不作为主线，后续需要转算法/模型方向再补 |

## 5. 项目规划

### 项目 1：企业知识库 RAG

目标：完成一个可以作为简历项目展示的知识库问答系统。

核心功能：

- [ ] 文档上传。
- [ ] PDF / Word / Markdown 解析。
- [ ] chunk 切分。
- [ ] embedding。
- [ ] 向量库检索。
- [ ] rerank。
- [ ] 引用来源。
- [ ] 权限过滤。
- [ ] 流式回答。
- [ ] 检索日志。
- [ ] eval 测试集。

技术栈：

```text
FastAPI
LangChain
Qdrant 或 pgvector
LLM API
Embedding API
Docker Compose
```

### 项目 2：智能工单 Agent

目标：用 LangGraph 做一个可控、可恢复、带人工确认的业务 Agent。

核心功能：

- [ ] 问题分类。
- [ ] 知识库检索。
- [ ] 工单字段提取。
- [ ] 用户补充信息。
- [ ] 人工确认。
- [ ] 调 Java API 创建工单。
- [ ] 返回工单号。
- [ ] 支持 thread_id 继续流程。

技术栈：

```text
FastAPI
LangGraph
LangChain tools
Java Spring Boot business-service
MySQL 或 PostgreSQL
Docker Compose
```

### 项目 3：业务数据助手

目标：自然语言查询业务数据，但不让 AI 直接执行任意 SQL。

核心功能：

- [ ] 预定义查询工具。
- [ ] 用户问题分类。
- [ ] 参数提取。
- [ ] 权限校验。
- [ ] 调 Java API 查询数据。
- [ ] 返回摘要和表格。
- [ ] 可选：生成图表。

安全原则：

- AI 不直接连生产数据库。
- AI 不生成裸 SQL 直接执行。
- 所有查询必须经过白名单工具。
- 查询结果必须受用户权限控制。

## 6. 学习记录模板

以后每次学习后，可以按这个格式追加。

```text
日期：
学习模块：
学习内容：
完成产出：
遇到的问题：
解决方式：
需要复习：
下一步：
```

## 7. 每周复盘模板

```text
周次：
本周目标：
完成情况：
代码产出：
文档产出：
卡点：
下周优先级：
是否需要调整路线：
```

## 8. 简历表达草稿

后续项目完成后，可以逐步打磨成简历描述。

```text
基于 FastAPI + LangChain + LangGraph 构建企业知识库问答与智能工单 Agent，
实现文档解析、chunk 切分、embedding、向量检索、权限过滤、RAG 引用回答、
LangGraph 多节点流程编排、人工确认、Java 业务工具调用、流式响应、
调用链日志、token 成本统计和 Docker 部署。
```

## 9. 下一步

短期先做这三件事：

- [ ] 确认 Python、Docker、模型 API、向量库环境。
- [ ] 创建 `projects/ai-service`，完成 FastAPI 基础服务。
- [ ] 创建第一篇学习记录：Python + FastAPI 工程基础。
