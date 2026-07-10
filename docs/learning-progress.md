# Java + Python + AI 学习进度

## 当前状态

```text
路线已确定：Java 后端 + Python AI 服务 + LangChain/LangGraph + RAG/Agent 工程化
当前阶段：阶段 3 LangChain + Java 工具调用基础已开始，第 2 节 为什么 AI 不能直接操作业务系统已完成，下一步进入第 3 节
主要仓库：D:\wendang\java+python+ai
执行路线：docs/ai-application-learning-roadmap.md
```

## 阶段进度

| 阶段 | 时间 | 主题 | 状态 | 产出 |
| --- | --- | --- | --- | --- |
| M0 | 第 0 周 | 环境与仓库 | 进行中 | README、上下文、路线图、进度表 |
| M1 | 第 1-2 周 | Python AI 服务基础 | 进行中 | `projects/ai-service`、聊天接口、流式输出、结构化输出 |
| M2 | 第 3-4 周 | LangChain + Java 工具调用 | 进行中 | 客服助手 v1、Java mock 业务服务 |
| M3 | 第 5-7 周 | 企业知识库 RAG | 未开始 | 文档入库、检索问答、引用来源、权限过滤、初版评测 |
| M4 | 第 8-9 周 | LangGraph 智能工单 | 未开始 | 工单 Agent v1 |
| M5 | 第 10-11 周 | 生产化与评测 | 未开始 | trace、日志、限流、重试、eval、Docker Compose |
| M6 | 第 12 周 | 作品整理 | 未开始 | README、架构图、截图、面试讲稿、简历描述 |

## 近期任务

- [ ] 确认 Python、Java、Docker 环境
- [x] 安装并配置 uv 到 D 盘
- [x] 确认 Python 3.12.3 可用
- [x] 确认 JDK 17 可用
- [ ] 安装或配置 Docker
- [x] 完成第 1 层：Python 项目环境和 uv 基础练习
- [x] 完成 Python 基础语法第 1 节：变量和基本类型
- [x] 完成 Python 基础语法第 2 节：字符串
- [x] 完成 Python 基础语法第 3 节：列表
- [x] 完成 Python 基础语法第 4 节：字典
- [x] 完成 Python 基础语法第 5 节：条件判断
- [x] 完成 Python 基础语法第 6 节：循环
- [x] 完成 Python 基础语法第 7 节：函数
- [x] 完成 Python 基础语法第 8 节：模块导入
- [x] 完成 Python 基础语法第 9 节：异常处理
- [x] 完成 Python 基础语法第 10 节：文件读写和 JSON
- [x] 完成 Python 基础语法第 11 节：类型提示
- [x] 完成 Python 基础语法第 12 节：类和对象
- [x] 完成 Python 基础语法第 13 节：元组和集合
- [x] 完成 Python 基础语法第 14 节：常用数据处理写法
- [x] 完成 Python 基础语法第 15 节：函数进阶
- [x] 完成 Python 基础语法第 16 节：标准库基础
- [x] 完成 Python 基础语法第 17 节：正则表达式 re
- [x] 完成 Python 基础语法第 18 节：pytest 测试基础
- [x] 完成 Python 基础语法第 19 节：调试和报错阅读
- [x] 完成 Python 基础语法第 20 节：HTTP/API 基础
- [x] 完成 Python 基础语法第 21 节：async/await 异步基础
- [x] 完成 Python 基础综合项目：Learning Task Assistant
- [x] 创建 `projects/ai-service`
- [x] 搭建 FastAPI 基础项目
- [x] 实现 `/health`
- [x] 实现模拟 `/chat` 接口
- [x] 实现 `/stream-chat`
- [x] 加入 `.env` 配置读取
- [x] 加入 trace_id 请求追踪
- [x] 加入统一异常处理
- [x] 加入 CORS 基础配置
- [x] 加入基础日志
- [x] 增加结构化输出练习接口
- [x] 完成阶段 1 第 1 节：Web 服务、HTTP 和 API 是什么
- [x] 完成阶段 1 第 2 节：FastAPI 是什么
- [x] 完成阶段 1 第 3 节：创建 `ai-service` 项目骨架
- [x] 完成阶段 1 第 4 节：FastAPI 最小服务 `/health`
- [x] 完成阶段 1 第 5 节：router 路由拆分
- [x] 完成阶段 1 第 6 节：POST、请求体和 JSON
- [x] 完成阶段 1 第 7 节：Pydantic 请求模型
- [x] 完成阶段 1 第 8 节：Pydantic 响应模型
- [x] 完成阶段 1 第 9 节：模拟 `/chat` 接口
- [x] 完成阶段 1 第 10 节：测试 FastAPI 接口
- [x] 完成阶段 1 第 11 节：`.env` 配置读取
- [x] 完成阶段 1 第 12 节：`logging` 日志
- [x] 完成阶段 1 第 13 节：`trace_id` 请求追踪
- [x] 完成阶段 1 第 14 节：统一异常处理
- [x] 完成阶段 1 第 15 节：CORS 基础
- [x] 完成阶段 1 第 16 节：阶段 1 项目整理
- [x] 完成阶段 2 第 1 节：什么是 LLM API
- [x] 完成阶段 2 第 2 节：API key 和 `.env` 安全配置
- [x] 完成阶段 2 第 3 节：token、上下文窗口、费用基础
- [x] 完成阶段 2 第 4 节：OpenAI-compatible SDK 基础调用方式
- [x] 完成阶段 2 第 5 节：messages 是什么：system / user / assistant
- [x] 完成阶段 2 第 6 节：prompt 基础：怎么写清楚任务
- [x] 完成阶段 2 第 7 节：第一次真实 `/chat` 调用
- [x] 完成阶段 2 第 8 节：多轮对话基础：历史消息怎么传
- [x] 完成阶段 2 第 9 节：timeout 超时
- [x] 完成阶段 2 第 10 节：retry 重试和 rate limit 限流基础
- [x] 完成阶段 2 第 11 节：模型调用错误处理
- [x] 完成阶段 2 第 12 节：模型调用日志：模型名、耗时、trace_id、token
- [x] 完成阶段 2 第 13 节：streaming 流式输出是什么
- [x] 完成阶段 2 第 14 节：FastAPI `StreamingResponse` 实现 `/stream-chat`
- [x] 完成阶段 2 第 15 节：结构化输出是什么
- [x] 完成阶段 2 第 16 节：Pydantic 约束结构化输出
- [x] 完成阶段 2 第 17 节：测试模型调用：mock/fake LLM client
- [x] 完成阶段 2 第 18 节：阶段 2 项目整理
- [x] 完成阶段 3 第 1 节：Tool Calling 是什么
- [x] 完成阶段 3 第 2 节：为什么 AI 不能直接操作业务系统
- [x] 写 FastAPI 项目结构学习笔记

## 阶段 1 细化学习清单

学习状态和代码状态分开看。即使代码已经提前搭好，学习上也按下面顺序重新讲透。

| 节 | 主题 | 学习状态 | 对应产出 |
| --- | --- | --- | --- |
| 1 | Web 服务、HTTP 和 API 是什么 | 已完成 | `notes/fastapi-stage1-01-web-http-api.md` |
| 2 | FastAPI 是什么 | 已完成 | `notes/fastapi-stage1-02-what-is-fastapi.md` |
| 3 | 创建 `projects/ai-service` 项目骨架 | 已完成 | `notes/fastapi-stage1-03-ai-service-project-skeleton.md` |
| 4 | FastAPI 最小服务 `/health` | 已完成 | `notes/fastapi-stage1-04-health-endpoint.md` |
| 5 | router 路由拆分 | 已完成 | `notes/fastapi-stage1-05-router-splitting.md` |
| 6 | POST、请求体和 JSON | 已完成 | `notes/fastapi-stage1-06-post-body-json.md` |
| 7 | Pydantic 请求模型 | 已完成 | `notes/fastapi-stage1-07-pydantic-request-model.md`、`app/schemas/chat.py`、`tests/test_chat_schema.py` |
| 8 | Pydantic 响应模型 | 已完成 | `notes/fastapi-stage1-08-pydantic-response-model.md`、`app/schemas/chat.py`、`tests/test_chat_schema.py` |
| 9 | 模拟 `/chat` 接口 | 已完成 | `notes/fastapi-stage1-09-mock-chat-endpoint.md`、`app/routers/chat.py`、`tests/test_chat_api.py` |
| 10 | 测试 FastAPI 接口 | 已完成 | `notes/fastapi-stage1-10-testing-fastapi-apis.md`、`tests/conftest.py`、`tests/test_health.py`、`tests/test_chat_api.py` |
| 11 | `.env` 配置读取 | 已完成 | `notes/fastapi-stage1-11-env-config.md`、`.env.example`、`app/core/config.py`、`tests/test_config.py` |
| 12 | `logging` 日志 | 已完成 | `notes/fastapi-stage1-12-logging.md`、`app/core/logging.py`、`tests/test_logging.py` |
| 13 | `trace_id` 请求追踪 | 已完成 | `notes/fastapi-stage1-13-trace-id.md`、`app/core/trace.py`、`app/middleware/tracing.py`、`tests/test_trace.py` |
| 14 | 统一异常处理 | 已完成 | `notes/fastapi-stage1-14-exception-handling.md`、`app/core/exception_handlers.py`、`app/core/exceptions.py`、`app/schemas/error.py`、`tests/test_exception_handlers.py` |
| 15 | CORS 基础 | 已完成 | `notes/fastapi-stage1-15-cors.md`、`app/core/cors.py`、`tests/test_cors.py`、`.env.example` |
| 16 | 阶段 1 项目整理 | 已完成 | `notes/fastapi-stage1-16-project-summary.md`、`projects/ai-service/README.md`、测试检查 |

## 阶段 2 细化学习清单

阶段 2 目标：把当前 mock `/chat` 逐步变成真实大模型调用，并补齐 API key、安全、token、prompt、超时、重试、日志、流式输出、结构化输出和测试基础。

| 节 | 主题 | 学习状态 | 对应产出 |
| --- | --- | --- | --- |
| 1 | 什么是 LLM API | 已完成 | `notes/llm-api-stage2-01-what-is-llm-api.md` |
| 2 | API key 和 `.env` 安全配置 | 已完成 | `notes/llm-api-stage2-02-api-key-env-security.md`、`app/core/config.py`、`tests/test_config.py` |
| 3 | token、上下文窗口、费用基础 | 已完成 | `notes/llm-api-stage2-03-token-context-cost.md`、`app/core/token_usage.py`、`tests/test_token_usage.py`、`.env.example` |
| 4 | OpenAI-compatible SDK 基础调用方式 | 已完成 | `notes/llm-api-stage2-04-openai-compatible-sdk.md`、`app/services/llm_client.py`、`tests/test_llm_client.py`、`scripts/llm_compatible_smoke_test.py` |
| 5 | messages 是什么：system / user / assistant | 已完成 | `notes/llm-api-stage2-05-messages-roles.md`、`app/schemas/chat.py`、`app/services/message_builder.py`、`tests/test_message_builder.py` |
| 6 | prompt 基础：怎么写清楚任务 | 已完成 | `notes/llm-api-stage2-06-prompt-basics.md`、`app/services/prompt_builder.py`、`tests/test_prompt_builder.py` |
| 7 | 第一次真实 `/chat` 调用 | 已完成 | `notes/llm-api-stage2-07-real-chat-call.md`、`app/services/llm_service.py`、`app/routers/chat.py`、`tests/test_llm_service.py`、`tests/test_chat_api.py` |
| 8 | 多轮对话基础：历史消息怎么传 | 已完成 | `notes/llm-api-stage2-08-multi-turn-history.md`、`ChatRequest.history`、`LLMChatService.generate_reply(..., history=...)`、多轮对话测试 |
| 9 | 超时 timeout | 已完成 | `notes/llm-api-stage2-09-timeout.md`、`APITimeoutError` -> `LLM_TIMEOUT`、504 接口测试 |
| 10 | 重试 retry 和限流 rate limit 基础 | 已完成 | `notes/llm-api-stage2-10-retry-rate-limit.md`、`LLM_MAX_RETRIES`、`RateLimitError` -> `LLM_RATE_LIMITED` |
| 11 | 模型调用错误处理 | 已完成 | `notes/llm-api-stage2-11-model-error-handling.md`、`map_openai_error_to_app_exception`、常见 SDK 错误映射测试 |
| 12 | 模型调用日志：模型名、耗时、trace_id、token | 已完成 | `notes/llm-api-stage2-12-llm-call-logging.md`、`LLMTokenUsage`、`extract_token_usage`、成功/失败调用日志测试 |
| 13 | streaming 流式输出是什么 | 已完成 | `notes/llm-api-stage2-13-streaming-concept.md`、普通响应/流式响应、chunk、SSE、`StreamingResponse` 概念 |
| 14 | FastAPI `StreamingResponse` 实现 `/stream-chat` | 已完成 | `notes/llm-api-stage2-14-stream-chat-endpoint.md`、`/stream-chat`、SSE `message/done/error`、流式 service/router 测试 |
| 15 | 结构化输出是什么 | 已完成 | `notes/llm-api-stage2-15-structured-output-concept.md`、JSON Mode、Structured Outputs、JSON Schema、Pydantic 校验概念 |
| 16 | Pydantic 约束结构化输出 | 已完成 | `notes/llm-api-stage2-16-pydantic-structured-output.md`、`/extract-ticket`、`TicketExtraction`、JSON Mode、Pydantic 输出校验 |
| 17 | 测试模型调用：mock/fake LLM client | 已完成 | `notes/llm-api-stage2-17-testing-model-calls.md`、`tests/fakes.py`、`tests/test_fake_llm_client.py`、fake client 复用 |
| 18 | 阶段 2 项目整理 | 已完成 | `notes/llm-api-stage2-18-project-summary.md`、模型参数基础、OpenAI-compatible 差异、调用链路复盘、阶段验收 |

## 阶段 3 细化学习清单

阶段 3 目标：让 Python AI 服务具备工具调用能力，并逐步接入 Java 业务服务。先讲清楚 Tool Calling 的底层流程，再引入 LangChain 的封装。

| 节 | 主题 | 学习状态 | 对应产出 |
| --- | --- | --- | --- |
| 1 | Tool Calling 是什么 | 已完成 | `notes/tool-calling-stage3-01-what-is-tool-calling.md` |
| 2 | 为什么 AI 不能直接操作业务系统 | 已完成 | `notes/tool-calling-stage3-02-why-ai-cannot-operate-business-system-directly.md` |
| 3 | 工具参数和 JSON Schema | 未开始 | 待新增 |
| 4 | 结构化输出 vs Tool Calling | 未开始 | 待新增 |
| 5 | 用 fake tool 模拟查订单 | 未开始 | 待新增 |
| 6 | 工具调用结果也要 Pydantic 校验 | 未开始 | 待新增 |
| 7 | 工具调用错误处理：超时、404、500 | 未开始 | 待新增 |
| 8 | 工具调用权限边界 | 未开始 | 待新增 |
| 9 | 工具调用幂等性 | 未开始 | 待新增 |
| 10 | 用 FastAPI 写一个最小 Java mock 业务服务 | 未开始 | 待新增 |
| 11 | Python AI 服务调用 Java mock API | 未开始 | 待新增 |
| 12 | 让模型决定是否调用工具 | 未开始 | 待新增 |
| 13 | 工具调用结果再交给模型总结 | 未开始 | 待新增 |
| 14 | 用户确认机制：敏感操作不能直接执行 | 未开始 | 待新增 |
| 15 | 创建工单流程：提取字段、确认、调用 Java API | 未开始 | 待新增 |
| 16 | 工具调用日志和 trace_id 串联 | 未开始 | 待新增 |
| 17 | 工具调用测试：fake Java API / fake tool | 未开始 | 待新增 |
| 18 | LangChain 是什么，为什么现在才引入 | 未开始 | 待新增 |
| 19 | LangChain ChatModel 基础 | 未开始 | 待新增 |
| 20 | LangChain Tool 基础 | 未开始 | 待新增 |
| 21 | LangChain 结构化输出 | 未开始 | 待新增 |
| 22 | 阶段 3 项目整理 | 未开始 | 待新增 |

## 当前 Sprint 验收标准

M0/M1 第一阶段完成时，必须满足：

- [ ] 本地能运行 Python、Java、Docker。
- [x] 本地能运行 Python。
- [x] 本地能运行 Java。
- [ ] 本地能运行 Docker。
- [x] uv 安装在 D 盘，缓存、Python 管理目录和工具目录都指向 D 盘。
- [x] `projects/ai-service` 有清晰目录结构。
- [x] FastAPI 服务能启动。
- [x] `/health` 返回正常。
- [x] `/chat` 能完成一次普通模型调用。
- [x] `/stream-chat` 能流式返回。
- [x] 请求日志包含 trace_id、模型名、耗时、错误信息。
- [x] 密钥只从 `.env` 或环境变量读取，并提供 `.env.example`。
- [x] 至少有 5 个 pytest 用例。

## 项目目标

### 项目 1：企业知识库 RAG

必须能力：

- 文档上传
- 文档解析
- chunk 切分
- embedding
- 向量库入库
- top_k 检索
- score_threshold
- 引用来源
- 权限过滤
- 无资料拒答
- 评测集

### 项目 2：智能工单 Agent

必须能力：

- 用户问题分类
- 检索知识库
- 判断是否能直接回答
- 结构化提取工单字段
- 用户确认
- 调用 Java API 创建工单
- 支持继续对话
- 记录完整调用链

## 知识点清单

### Python AI 工程

- [ ] Python 虚拟环境
- [ ] 依赖管理
- [ ] FastAPI
- [ ] Pydantic
- [ ] httpx
- [x] logging
- [x] pytest
- [ ] Dockerfile

### LLM API

- [x] OpenAI-compatible SDK 基础调用
- [x] system prompt / user prompt
- [x] streaming
- [x] structured output
- [ ] tool calling
- [x] token 成本
- [x] 超时和重试
- [x] 模型错误兜底

### LangChain

- [ ] ChatModel
- [ ] PromptTemplate
- [ ] Runnable
- [ ] tools
- [ ] structured output
- [ ] callbacks
- [ ] retriever

### RAG

- [ ] 文档解析
- [ ] chunk 切分
- [ ] embedding
- [ ] vector store
- [ ] metadata
- [ ] similarity search
- [ ] hybrid search
- [ ] rerank
- [ ] citations
- [ ] 权限过滤
- [ ] 检索评测

### LangGraph

- [ ] StateGraph
- [ ] state schema
- [ ] node
- [ ] edge
- [ ] conditional edge
- [ ] checkpoint
- [ ] interrupt
- [ ] human-in-the-loop
- [ ] thread_id

### Java 集成

- [ ] Spring Boot 业务服务
- [ ] 用户权限接口
- [ ] 订单查询接口
- [ ] 退款查询接口
- [ ] 工单创建接口
- [ ] AI tools 调 Java API
- [ ] 敏感操作确认

### 工程化

- [x] 请求日志
- [x] 模型调用日志
- [ ] tool 调用日志
- [x] trace_id
- [ ] token 成本统计
- [ ] 限流
- [x] 重试
- [ ] 缓存
- [ ] Docker Compose
- [ ] eval.py

## 复盘记录

### 2026-07-04

- 从旧线程 `019f26a1-6a8b-7362-97c8-91060948d331` 整理学习上下文。
- 明确主线：不走 Spring AI 主线，优先 LangChain + LangGraph。
- 明确产出：企业知识库 RAG、智能工单 Agent。
- 当前项目目录作为后续学习主仓库。
- 完善学习路径：将 12 周计划拆成 M0-M6，收敛为两个主项目，并把日志、评测、安全前置。
- 安装 uv 0.11.26 到 `D:\tools\uv\bin`，并配置 `UV_CACHE_DIR`、`UV_PYTHON_INSTALL_DIR`、`UV_TOOL_DIR` 到 D 盘。
- 检查环境：Python 3.12.3 可用，JDK 17 可用，Docker 暂不可用。
- 创建 `projects/python-basics`，完成 uv 项目初始化、虚拟环境创建、`requests` 依赖安装和 HTTP 请求练习。
- 新增笔记 `notes/python-project-environment.md`。
- 明确后续教学主旨：所有知识从基础讲起，不默认已经会；目标是会用、理解原理、能解释给别人听，并通过代码和自测验证。
- 新增 `docs/learning-resources.md`，开始维护官方文档、GitHub 学习笔记、视频课程和阶段资料组合。
- 完成变量和基本类型练习，新增 `projects/python-basics/01_variables_types.py` 和 `notes/python-variables-and-types.md`。
- 明确笔记规则：以后每节练习和自测问题都要附参考答案；已补充到变量和基本类型笔记。
- 完成字符串练习，新增 `projects/python-basics/02_strings.py`、`projects/python-basics/02_practice_clean_question.py` 和 `notes/python-strings.md`。
- 完成列表练习，新增 `projects/python-basics/03_lists.py`、`projects/python-basics/03_practice_task_list.py` 和 `notes/python-lists.md`。
- 完成字典练习，新增 `projects/python-basics/04_dicts.py`、`projects/python-basics/04_practice_user_profile.py` 和 `notes/python-dicts.md`。
- 完成条件判断练习，新增 `projects/python-basics/05_conditions.py`、`projects/python-basics/05_practice_question_check.py` 和 `notes/python-conditions.md`。
- 完成循环练习，新增 `projects/python-basics/06_loops.py`、`projects/python-basics/06_practice_batch_tasks.py` 和 `notes/python-loops.md`。
- 完成函数练习，新增 `projects/python-basics/07_functions.py`、`projects/python-basics/07_practice_question_functions.py` 和 `notes/python-functions.md`。
- 完成模块导入练习，新增 `projects/python-basics/question_utils.py`、`projects/python-basics/08_imports.py`、`projects/python-basics/08_practice_import_question_utils.py` 和 `notes/python-imports.md`。
- 完成异常处理练习，新增 `projects/python-basics/09_exceptions.py`、`projects/python-basics/09_practice_safe_request.py` 和 `notes/python-exceptions.md`。
- 完成文件读写和 JSON 练习，新增 `projects/python-basics/10_files_json.py`、`projects/python-basics/10_practice_task_json.py`、示例 JSON 数据和 `notes/python-files-json.md`。
- 完成类型提示练习，新增 `projects/python-basics/11_type_hints.py`、`projects/python-basics/11_practice_typed_question.py` 和 `notes/python-type-hints.md`。
- 完成类和对象练习，新增 `projects/python-basics/12_classes.py`、`projects/python-basics/12_practice_learning_task.py` 和 `notes/python-classes.md`。
- 完成元组和集合练习，新增 `projects/python-basics/13_tuple_set.py`、`projects/python-basics/13_practice_tuple_set.py` 和 `notes/python-tuples-sets.md`。
- 完成常用数据处理写法练习，新增 `projects/python-basics/14_data_processing.py`、`projects/python-basics/14_practice_data_processing.py` 和 `notes/python-data-processing.md`。

### 2026-07-05

- 完成函数进阶练习，新增 `projects/python-basics/15_function_advanced.py`、`projects/python-basics/15_practice_function_advanced.py` 和 `notes/python-function-advanced.md`。
- 完成标准库基础练习，新增 `projects/python-basics/16_standard_library.py`、`projects/python-basics/16_practice_standard_library.py` 和 `notes/python-standard-library.md`。
- 完成正则表达式练习，新增 `projects/python-basics/17_regex.py`、`projects/python-basics/17_practice_regex.py` 和 `notes/python-regex.md`。
- 完成 pytest 测试基础练习，新增 `projects/python-basics/lesson18_pytest_basics.py`、`projects/python-basics/lesson18_practice_pytest.py`、测试文件和 `notes/python-pytest.md`。
- 完成调试和报错阅读练习，新增 `projects/python-basics/lesson19_debugging_traceback.py`、`projects/python-basics/lesson19_practice_debugging.py`、测试文件和 `notes/python-debugging-traceback.md`。
- 完成 HTTP/API 基础练习，新增 `projects/python-basics/lesson20_http_api.py`、`projects/python-basics/lesson20_practice_http_api.py`、测试文件和 `notes/python-http-api.md`。
- 完成 async/await 异步基础练习，新增 `projects/python-basics/lesson21_async_await.py`、`projects/python-basics/lesson21_practice_async_await.py`、测试文件和 `notes/python-async-await.md`。
- 完成 Python 基础综合项目 Learning Task Assistant，新增 `projects/python-basics/learning_task_assistant/`、`projects/python-basics/lesson22_mini_project_demo.py`、测试文件和 `notes/python-mini-project.md`。
- 开始阶段 1：FastAPI 服务基础，创建 `projects/ai-service`，完成 FastAPI 项目骨架、`/health` 接口、健康检查测试和 `notes/fastapi-stage1-project-structure.md`。
