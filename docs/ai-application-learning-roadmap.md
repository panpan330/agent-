# AI 应用工程学习路线图

版本：2026-07-04

适用目标：已有 Java 后端基础，转向 AI 应用开发 / 后端 AI 工程 / RAG 与 Agent 应用工程。

## 1. 路线定位

主线不是纯算法、模型训练或只做提示词，而是：

```text
Java 后端能力
  + Python AI 服务
  + LangChain / LangGraph
  + RAG / Tool Calling
  + 评测 / 追踪 / 安全 / 部署
  = 能落地的 AI 应用工程能力
```

学习后的目标不是“知道很多名词”，而是能独立做出两个可运行、可讲清楚、可继续迭代的项目：

1. 企业知识库 RAG 系统
2. 智能工单 Agent

第三个项目“业务数据助手”只作为加分项，等前两个项目稳定后再做。

## 2. 技术栈选择

### 主技术栈

| 层级 | 技术 | 用途 |
| --- | --- | --- |
| Java 业务层 | Spring Boot | 用户、权限、订单、退款、工单、业务 API |
| Python AI 层 | FastAPI | 对外提供 AI 服务接口 |
| 数据校验 | Pydantic | 请求、响应、结构化输出、tool 入参校验 |
| LLM 编排 | LangChain | 模型调用、prompt、tool calling、structured output、retriever |
| 流程编排 | LangGraph | 多步骤、有状态、可恢复、可人工确认的 Agent 流程 |
| 向量库 | Qdrant 优先 | RAG 初期上手快，后续再补 pgvector |
| 部署 | Docker Compose | 本地和演示环境一键启动 |
| 测试评估 | pytest + eval 脚本 | 单元测试、接口测试、RAG/Agent 效果评测 |

### 暂不作为主线

- Spring AI：当前目标环境不流行，先不作为主线。
- PyTorch / 模型训练 / 微调：以后要转算法或模型方向再补。
- Milvus / Elasticsearch / 多向量库横向对比：先用一个向量库做透。
- 全自动 Agent：先做可控流程，再逐步增加智能决策。
- Kubernetes：项目能 Docker Compose 跑通后再考虑。

## 3. 学习原则

1. **项目牵引，不刷 API**
   每个知识点都要落到接口、脚本、测试或项目功能里。

2. **从基础讲起，不跳知识**
   不默认已经懂某个概念。每个知识点都要先讲“是什么、为什么、解决什么问题”，再写最小例子，最后进入项目。

3. **理解优先，不只会用**
   目标不是复制命令，而是能向别人解释原理、用途、边界、常见错误和排查方式。

4. **资料辅助，建立体系**
   重要知识点要补充官方文档、课程或视频方向，避免只靠零散问答学习。

5. **练习必须有答案**
   每节笔记都要包含练习参考答案和自测参考答案，方便复盘和纠错。

6. **先可控，再智能**
   AI 只能调用明确授权的工具。创建工单、查询敏感数据等动作必须有权限校验和人工确认。

7. **日志和评测前置**
   从第一个 `/chat` 接口开始就记录模型、耗时、token、错误和 trace_id。

8. **Java 优势不能丢**
   Java 继续负责业务系统和稳定接口，Python 负责 AI 编排和模型生态。

9. **每周必须有可验收产出**
   没有通过验收标准，就不要急着进入下一阶段。

默认教学流程：

```text
概念解释 -> 为什么需要 -> 最小例子 -> 动手练习 -> 结果讲解 -> 常见问题 -> 自测问题 -> 笔记沉淀
```

## 4. 总体阶段

| 阶段 | 时间 | 主题 | 核心产出 |
| --- | --- | --- | --- |
| M0 | 第 0 周 | 环境与仓库 | 学习仓库、环境检查、模型 API、Docker |
| M1 | 第 1-2 周 | Python AI 服务基础 | FastAPI AI 服务、聊天接口、流式输出、结构化输出 |
| M2 | 第 3-4 周 | LangChain + Java 工具调用 | 客服助手 v1、Java mock 业务服务、tool 调用 |
| M3 | 第 5-7 周 | 企业知识库 RAG | 文档入库、检索问答、引用来源、权限过滤、初版评测 |
| M4 | 第 8-9 周 | LangGraph 智能工单 | 分类、检索、字段提取、用户确认、创建工单 |
| M5 | 第 10-11 周 | 生产化与评测 | trace、日志、限流、重试、eval、Docker Compose |
| M6 | 第 12 周 | 作品整理 | README、架构图、截图、面试讲稿、简历描述 |

如果每天只有 1-2 小时，可以把 M3 和 M5 各延长 1 周。不要为了赶进度牺牲项目质量。

## 5. M0：环境与仓库

目标：把后续学习的基础环境和目录定下来。

任务：

- 安装 Python 3.11/3.12。
- 安装 uv 或 poetry，二选一即可。
- 安装 JDK 17+。
- 安装 Docker / Docker Compose。
- 准备一个 OpenAI-compatible 模型 API。
- 选择向量库，初期建议 Qdrant。
- 明确仓库目录：

```text
docs/       路线、进度、架构、复盘
notes/      学习笔记、踩坑记录
projects/   项目代码
```

验收标准：

- 能运行 `python --version`。
- 能运行 `java -version`。
- 能运行 `docker version`。
- 仓库有清晰的 README、路线图和进度表。

## 6. M1：Python AI 服务基础

时间：第 1-2 周

目标：做出一个标准的 Python AI 服务，而不是零散脚本。

建议目录：

```text
projects/ai-service/
  app/
    main.py
    core/config.py
    core/logging.py
    api/routes/
    schemas/
    services/
    tests/
  .env.example
  pyproject.toml
  Dockerfile
  README.md
```

学习内容：

- Python 虚拟环境和依赖管理。
- FastAPI 路由、请求体、响应体、异常处理。
- Pydantic 模型校验。
- 环境变量管理。
- httpx 调外部接口。
- logging、trace_id、请求耗时。
- pytest 基础测试。
- Dockerfile 基础。

必须实现：

- `GET /health`
- `POST /chat`
- `GET /stream-chat` 或 `POST /stream-chat`
- `POST /extract/resume`
- `POST /classify/intent`

验收标准：

- 服务能启动。
- 密钥不写死，统一从 `.env` 读取。
- 普通聊天和流式聊天都能调用模型。
- 结构化输出能被 Pydantic 校验。
- 每次请求至少记录 trace_id、模型名、耗时、错误信息。
- 至少有 5 个 pytest 用例。

## 7. M2：LangChain + Java 工具调用

时间：第 3-4 周

目标：掌握 tool calling，并把 Java 后端能力接入 AI。

### Python AI 层

学习内容：

- ChatModel / messages。
- Prompt template。
- structured output。
- tools 定义和调用。
- Runnable / chain 基础。
- streaming。
- callbacks / tracing 基础。

必须实现的 mock tools：

```text
query_order(order_id)
query_refund(order_id)
query_logistics(order_id)
create_ticket(user_id, title, description, category)
```

### Java 业务层

建议目录：

```text
projects/business-service/
```

必须实现接口：

```text
GET /api/orders/{orderId}
GET /api/refunds/{orderId}
GET /api/logistics/{orderId}
GET /api/tickets/{ticketId}
POST /api/tickets
GET /api/users/{userId}/permissions
```

安全原则：

- AI 不直接查业务数据库。
- AI 不直接执行高风险动作。
- AI 只能通过白名单 tool 调 Java API。
- 创建工单、退款、审批等动作必须预留 confirmation。

验收标准：

- 用户自然语言提问后，AI 能判断是否调用工具。
- tool 入参有 Pydantic 校验。
- tool 结果能被模型整合为自然语言回答。
- 每次 tool 调用都有日志。
- Python tool 可以调用 Java API。
- Java API 有清晰错误码和日志。

## 8. M3：企业知识库 RAG

时间：第 5-7 周

目标：完成第一个主项目：企业知识库 RAG 系统。

### 第 5 周：文档入库

学习内容：

- RAG 基础流程：load -> split -> embed -> store -> retrieve -> generate。
- Markdown / txt / PDF / docx 解析。
- 文本清洗。
- chunk 切分策略。
- embedding 接入。
- Qdrant 写入、删除、重建索引。
- metadata 设计。

推荐 metadata：

```text
doc_id
chunk_id
content
source
page
title
department
user_group
created_at
```

验收标准：

- 可以上传或导入一个文档。
- 文档能切分成 chunks。
- 每个 chunk 有 metadata。
- 能按 doc_id 删除和重建索引。

### 第 6 周：查询链路

必须实现：

- 用户提问向量化。
- top_k 检索。
- score_threshold。
- context 拼接。
- 基于 context 回答。
- citations 引用来源。
- 无资料时拒答。
- 检索日志。

验收标准：

- 回答必须带引用。
- 引用能定位到文档和 chunk。
- 没有检索结果时不能胡编。
- 至少准备 20 个测试问题。

### 第 7 周：RAG 进阶

必须补充：

- 权限过滤：department / user_group / user_id。
- 问题改写。
- 混合检索初版：向量检索 + 关键词检索。
- rerank 初版。
- 上下文压缩。
- 命中率统计：hit / miss / low_score。

验收标准：

- 不同用户能看到不同文档范围。
- 同一个问题能看到召回和 rerank 的差异。
- 能输出检索到的 chunks。
- 有初版 RAG eval 报告。

## 9. M4：LangGraph 智能工单 Agent

时间：第 8-9 周

目标：完成第二个主项目：智能工单 Agent。

学习内容：

- StateGraph。
- state schema。
- node。
- edge。
- conditional edge。
- checkpoint。
- thread_id。
- interrupt。
- human-in-the-loop。

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

验收标准：

- 每个节点职责单一。
- 状态里能看到中间结果。
- 条件分支可测试。
- 同一个 thread_id 能继续对话。
- 字段提取使用 structured output。
- 创建工单前必须 human confirmation。
- 创建成功后能查 Java 后端工单记录。

## 10. M5：生产化与评测

时间：第 10-11 周

目标：把项目从 demo 提升到可上线雏形。

必须补充：

- 请求日志。
- 模型调用日志。
- tool 调用日志。
- token 成本统计。
- 超时控制。
- 失败重试。
- 限流。
- 缓存。
- 错误码规范。
- Docker Compose。
- 健康检查。

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
error
created_at
```

评测集：

```text
知识库问答 30 条
工单场景 20 条
订单/退款查询 20 条
异常输入 10 条
越权问题 10 条
```

评测维度：

- 检索是否命中。
- 答案是否基于引用。
- 是否胡编。
- tool 是否调用正确。
- 字段提取是否正确。
- 是否越权。
- 响应耗时。

验收标准：

- 有 `eval.py` 或等价评测脚本。
- 能一键输出 pass/fail 报告。
- 能定位失败样例。
- 每次改 prompt、chunk、rerank 策略后能对比效果。
- 服务能 `docker compose up` 一键启动。

## 11. M6：作品整理和面试准备

时间：第 12 周

目标：把项目整理成能展示、能讲清楚、能写进简历的作品。

每个主项目必须整理：

- README。
- 架构图。
- 启动方式。
- 接口文档。
- 核心流程截图。
- 测试问题样例。
- 技术难点说明。
- 可优化点。
- 失败案例和改进记录。

面试必须能讲清楚：

- RAG 为什么会答错？
- chunk 大小怎么选？
- 向量检索和关键词检索区别？
- rerank 解决什么问题？
- 为什么 AI 不能直接操作数据库？
- tool calling 怎么保证安全？
- LangGraph 解决了什么问题？
- human-in-the-loop 为什么必要？
- 如何评测一个知识库问答系统？
- 如何定位一次 AI 回答失败？

简历表达草稿：

```text
基于 FastAPI + LangChain + LangGraph 构建企业知识库问答与智能工单 Agent，
实现文档解析、chunk 切分、embedding、向量检索、权限过滤、RAG 引用回答、
LangGraph 多节点流程编排、人工确认、Java 业务工具调用、流式响应、
调用链日志、token 成本统计、评测脚本和 Docker Compose 部署。
```

## 12. 每周执行节奏

建议每周固定节奏：

```text
周一：明确本周验收标准，拆任务
周二到周四：编码实现核心功能
周五：补测试、日志、异常处理
周六：整理 README、笔记、截图
周日：复盘，更新 learning-progress.md
```

每天 2 小时版本：

```text
20 分钟：看文档或复习概念
70 分钟：写代码
20 分钟：测试和调试
10 分钟：更新笔记
```

## 13. 不要提前分散精力

前 8 周不要重点投入：

- 大模型微调。
- PyTorch 深度学习。
- 多模型横向测评。
- 复杂前端 UI。
- Kubernetes。
- 多 Agent 花活。
- 自研向量数据库。

这些东西不是没用，而是当前阶段投入产出比不高。先把 RAG 和工单 Agent 做成可运行项目。

## 14. 通关标准

达到下面 6 条，才算具备 AI 应用工程实战基础：

```text
1. 能独立做一个知识库 RAG 系统。
2. 能解释 chunk、embedding、rerank、引用来源。
3. 能用 LangGraph 做多步骤业务流程。
4. 能让 AI 安全调用 Java 后端接口。
5. 能做日志、评测、权限、成本统计。
6. 能把项目 Docker 化并写清楚部署文档。
```

## 15. 下一步

立即开始 M0/M1：

1. 检查 Python、Java、Docker 环境。
2. 创建 `projects/ai-service`。
3. 搭建 FastAPI 基础项目。
4. 实现 `/health`、`/chat`、`/stream-chat`。
5. 从第一天开始记录日志、trace_id 和学习笔记。
