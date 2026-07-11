# 学习上下文：Java + Python + AI

来源线程：`019f26a1-6a8b-7362-97c8-91060948d331`

整理时间：2026-07-04

## 一句话定位

当前学习方向是 **Java 后端转 AI 应用工程**。

不优先走纯算法、模型训练或只做提示词，而是把已有 Java 后端能力和 Python AI 生态结合起来，做能落地、可上线、可维护的 AI 应用。

## 学习协作主旨

后续学习必须始终按“从零基础教学”的方式推进。

核心要求：

- 不默认学习者已经懂某个概念。
- 每个新知识点先讲清楚“它是什么、为什么需要它、解决什么问题”。
- 再讲“它和已学知识的关系”，尽量用 Java 后端经验做类比，但不能因为会 Java 就跳过 Python/AI 基础。
- 然后给出最小可运行例子，通过代码验证理解。
- 最后补充常见错误、适用场景、边界和复习问题。
- 每节练习和自测问题都要在文档中提供参考答案，方便复盘。
- 对于重要知识点，需要提供可靠资料、官方文档、课程或视频方向，帮助系统学习。
- 学习目标不是只会照抄命令，而是能向别人解释清楚原理、用途、实践方式和常见坑。

教学节奏：

```text
概念解释 -> 为什么需要 -> 最小例子 -> 动手练习 -> 结果讲解 -> 常见问题 -> 自测问题 -> 笔记沉淀
```

判断是否学会：

```text
能自己写出来
能自己改出来
能说清楚为什么这么做
能解释出错时该怎么排查
能把它放进真实项目里使用
```

## 后续每节教学细则

在上面的主旨基础上，后续每节默认继续遵守这些细则：

1. 如果本节有新增、修改或删除业务代码，必须把这些代码讲得更细。测试代码不用逐行展开，但业务代码、配置、服务层、工具层、路由层、数据模型、错误处理和调用链路要讲清楚，让学习者真正知道每段代码为什么存在、解决什么问题、以后怎么改。
2. 尽量少重复以前已经讲过且几乎完全一样的内容。只有当旧知识在本节有新的使用方式、新的边界、新的风险或新的工程意义时，才重新提起并补充。
3. 每节内容要尽量丰富，不能只满足“代码能跑”。笔记要帮助学习者扩充知识储备，理解基础知识、工程背景、真实项目场景、常见误区、后续演进方向和可以向别人讲清楚的表达方式。
4. 测试部分不需要像业务代码一样讲得特别细。只讲重要测试：它验证了什么风险、为什么需要这个测试、失败时说明哪里可能有问题。重点仍然放在本节基础知识、扩充知识和增删改业务代码讲解上。
5. 笔记格式不必死板。最终目标是让学习者通过笔记完整学会对应知识点，未来开发、工作或向别人讲解时都能说得清楚、用得出来。
6. 如果需要检查项目里是否有中文乱码，看到 PowerShell 输出乱码时，应该优先怀疑是 PowerShell 输出编码把 UTF-8 中文显示错了。先用字节、编辑器、测试结果或其他方式确认文件真实内容，再决定是否修复，避免误判后做无意义的大范围改动。

## 背景判断

截至旧线程讨论时，结论是：

- Java 仍然适合企业后端、权限、数据库、业务流程、稳定接口。
- Python 是 AI 应用层、数据处理、模型 API、RAG、评测脚本的主力语言。
- AI 岗位机会真实存在，但初级竞争加剧，单纯“会调用模型 API”不够。
- 更现实的路线是 AI 应用工程：RAG、智能客服、Agent、知识库、工作流自动化、模型 API 接入、评测和工程化。

## 路线边界

优先路线：

```text
Java 后端
  负责登录、权限、业务 API、数据库、工单、订单、报表等稳定系统

Python AI 服务
  负责 LLM API、RAG、LangChain、LangGraph、工具编排、评测和 AI 流程

向量库/数据层
  使用 Qdrant、PostgreSQL + pgvector 等

工程化
  Docker、日志、追踪、权限、安全、成本统计、评测、部署文档
```

不作为当前主线：

- Spring AI：旧线程中明确因为本地/目标环境不流行，暂不作为主线。
- 纯算法岗：暂不优先学习模型训练、深度学习研究、GPU 训练。
- 全自动 Agent：先做可控流程，再逐步增加智能决策。

## 推荐技术栈

```text
Java 后端：
Spring Boot / MySQL / Redis / REST API / 权限 / 业务系统

Python AI 层：
Python 3.11+ / FastAPI / Pydantic / httpx / pytest / LangChain / LangGraph

AI 能力：
LLM API / Prompt / Streaming / Structured Output / Tool Calling / RAG / Agent / Eval

数据和检索：
PostgreSQL + pgvector 或 Qdrant / embedding / metadata / rerank / hybrid search

工程化：
Docker / Docker Compose / 日志 / 请求 ID / 限流 / 重试 / 缓存 / 调用追踪 / 成本统计
```

## 学习优先级

```text
RAG > Tool Calling > LangGraph > Eval/工程化 > Agent 花活
```

原因：

- RAG 是 AI 应用工程最常见、最能落地的能力。
- Tool Calling 能复用 Java 后端业务接口。
- LangGraph 适合有状态、有分支、可中断、可恢复、可审批的业务流程。
- Eval、日志、追踪、安全和部署决定项目能不能从 demo 变成真实服务。

## 12 周主计划

### 第 0 周：环境准备

准备：

- Python 3.11/3.12
- uv 或 poetry
- FastAPI
- LangChain
- LangGraph
- Qdrant 或 PostgreSQL + pgvector
- Docker / Docker Compose
- OpenAI-compatible 模型 API
- Java Spring Boot 测试服务

建议目录：

```text
projects/ai-service
projects/business-service
docs/
notes/
```

### 第 1 周：Python + FastAPI 工程基础

目标：能写一个标准 Python API 服务。

任务：

- Python 虚拟环境、依赖管理、项目结构
- FastAPI 路由、请求体、响应体、异常处理
- Pydantic 模型、配置管理、环境变量
- httpx 调外部接口、超时、重试
- logging、请求 ID、基础 pytest

验收：

- `POST /chat` 可以返回模型回答
- `GET /stream-chat` 支持流式输出
- 密钥从 `.env` 读取
- 有基础日志和异常处理

### 第 2 周：LLM API 基础

目标：理解大模型应用不是只发一句 prompt。

重点：

- system prompt / user prompt
- temperature / max_tokens / top_p
- streaming
- structured output
- tool calling 基础
- token 成本
- 模型超时和失败兜底

练习：

- 简历信息抽取：输入文本，输出 JSON
- 客服意图分类：售前、售后、投诉、退款、物流
- 长文本结构化总结

验收：

- 输出能被 Pydantic 校验
- 模型输出格式错误时能重试或清晰报错
- 接口能返回 token 消耗、耗时、模型名称

### 第 3 周：LangChain 核心组件

目标：会用 LangChain 组织模型、Prompt、工具和结构化输出。

重点：

- ChatModel、messages、prompt template
- Runnable / chain 基础
- structured output + Pydantic
- tools 定义和调用
- streaming 和 callbacks

练习项目：客服助手 v1。

验收：

- 至少 3 个 tool
- 每次 tool 调用有日志
- 工具入参有 Pydantic 校验
- 回答能流式返回

### 第 4 周：Java 业务服务接入

目标：把 Java 后端能力接进 AI 系统。

Java 服务接口：

```text
GET /api/orders/{orderId}
GET /api/refunds/{orderId}
GET /api/tickets/{ticketId}
POST /api/tickets
GET /api/users/{userId}/permissions
```

Python AI 层工具：

```text
query_order(order_id)
query_refund(order_id)
create_ticket(user_id, title, description, category)
query_user_permissions(user_id)
```

验收：

- AI 不直接查数据库
- AI 只通过 Java API 做业务动作
- 创建工单前生成结构化字段
- 高风险操作预留 confirmation 字段

### 第 5 周：RAG 入门，文档入库

目标：完成知识库的数据处理链路。

链路：

```text
load -> split -> embed -> store -> retrieve -> generate
```

重点：

- Markdown / txt / PDF / docx 解析
- chunk 切分策略
- embedding 接入
- 向量库存储
- metadata 设计

chunk metadata 至少包含：

```text
doc_id
chunk_id
content
source
page
title
user_group
created_at
embedding
```

验收：

- 上传 PDF 后能切成 chunks
- 每个 chunk 有 metadata
- 能按 doc_id 删除和重建索引

### 第 6 周：RAG 查询链路

目标：完成企业知识库问答 v1。

流程：

```text
用户提问
  -> 问题向量化
  -> 向量库 top_k 检索
  -> 拼接 context
  -> LLM 基于 context 回答
  -> 返回 answer + citations
```

必须实现：

- top_k 参数
- score_threshold
- 引用来源
- 无资料时拒答
- 检索日志

验收：

- 回答必须带引用
- 引用能定位到文档和 chunk
- 没有检索结果时不能胡编
- 至少准备 20 个测试问题

### 第 7 周：RAG 进阶

目标：让 RAG 从 demo 变成可用系统。

补充：

- 权限过滤：user_group / user_id / department
- 问题改写
- 多路召回：向量检索 + 关键词检索
- rerank
- 上下文压缩
- 答案约束

验收：

- 不同用户看到不同文档结果
- 同一个问题能看到检索到哪些 chunk
- 有命中率统计：hit / miss / low_score

### 第 8 周：LangGraph 基础

目标：掌握状态机式 Agent 编排。

重点：

- StateGraph
- state schema
- node
- edge
- conditional edge
- checkpoint
- thread_id
- interrupt

练习流程：

```text
接收用户问题
  -> 分类：知识问答 / 工单 / 闲聊 / 业务查询
  -> 不同分类走不同节点
  -> 最终统一返回
```

验收：

- 每个节点职责单一
- 状态里能看到中间结果
- 条件分支可测试
- 同一个 thread_id 能继续对话

### 第 9 周：智能工单 Agent

目标：做一个可展示的 LangGraph 项目。

流程：

```text
用户描述问题
  -> 问题分类
  -> 检索知识库
  -> 判断能否直接解决
  -> 不能解决则提取工单字段
  -> 让用户确认
  -> 调用 Java API 创建工单
  -> 返回工单号
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

验收：

- 字段提取使用 structured output
- 创建工单前必须 human confirmation
- 用户补充信息后能继续上次流程
- 创建成功后能查 Java 后端工单记录

### 第 10 周：生产化能力

目标：项目像真实公司能上线的服务。

补充：

- 请求日志
- 模型调用日志
- tool 调用日志
- token 成本统计
- 超时控制
- 失败重试
- 限流
- 缓存
- Docker Compose
- 健康检查
- 错误码规范

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

验收：

- 每次回答都能追踪完整链路
- 出错时能定位是检索、模型、工具还是 Java API 问题
- 服务可以 `docker compose up` 一键启动

### 第 11 周：评测与优化

目标：别只靠感觉判断 AI 效果。

测试集：

```text
知识库问答 30 条
工单场景 20 条
订单/退款查询 20 条
异常输入 10 条
越权问题 10 条
```

评测维度：

- 检索是否命中
- 答案是否基于引用
- 是否胡编
- 工具是否调用正确
- 字段提取是否正确
- 是否越权
- 响应耗时

验收：

- 有 `eval.py` 可一键跑测试
- 输出 pass/fail 报告
- 每次改 prompt 或 chunk 策略后能对比效果

### 第 12 周：作品整理和面试准备

最终交付：

1. 企业知识库 RAG
2. 智能工单 Agent

每个项目整理：

- README
- 架构图
- 启动方式
- 接口文档
- 核心流程截图
- 测试问题样例
- 技术难点说明
- 可优化点

简历表达：

```text
基于 FastAPI + LangChain + LangGraph 构建企业知识库问答与智能工单 Agent。
实现文档解析、chunk 切分、embedding、向量检索、权限过滤、RAG 引用回答、
LangGraph 多节点流程编排、人工确认、Java 业务工具调用、流式响应、
调用链日志、token 成本统计和 Docker 部署。
```

## 是否足够

旧线程结论：

- 这套计划足够入门并转向 AI 应用工程。
- 如果认真做完，并完成两个完整项目，基本可以开始投 AI 应用开发 / 后端 AI 工程岗位。
- 如果要长期有竞争力，还必须补 Eval、Observability、安全、业务理解、部署维护。

判断是否“够了”的 6 个标准：

```text
1. 能独立做一个知识库 RAG 系统
2. 能解释 chunk、embedding、rerank、引用来源
3. 能用 LangGraph 做多步骤业务流程
4. 能让 AI 安全调用 Java 后端接口
5. 能做日志、评测、权限、成本统计
6. 能把项目 Docker 化并写清楚部署文档
```

## 后续协作约定

以后在这个项目继续学习时，默认按以下方式推进：

1. 每次学习前先查看 `docs/learning-progress.md`。
2. 学一个知识点，就在 `notes/` 记录简短笔记。
3. 做一个练习或项目，就放到 `projects/`。
4. 每完成一个阶段，更新进度、产出、问题和下一步。
5. 不只看教程，必须用代码和可运行项目验证。
