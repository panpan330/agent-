# Java + Python + AI 学习项目

这个仓库用于长期沉淀 Java 后端转 AI 应用工程的学习记录、项目代码、实验结论和复盘。

当前主线不是纯算法岗，也不是只做提示词，而是：

```text
Java 后端 + Python AI 服务 + LangChain/LangGraph + RAG + Tool Calling + 工程化上线
```

## 学习主线

- Java 后端继续负责业务系统、权限、数据库、稳定 API 和工程化能力。
- Python + FastAPI 负责 AI 服务层。
- LangChain 负责 LLM 调用、RAG、工具调用和结构化输出。
- LangGraph 负责多步骤、可恢复、可审计的 Agent/Workflow 编排。
- 项目重点先收敛到企业知识库 RAG 和智能工单 Agent。

## 仓库结构

```text
docs/      学习路线、进度、上下文和项目规划
notes/     学习笔记、踩坑记录、复盘
projects/ 练习项目、Demo 和完整作品
```

## 核心文档

- [学习上下文](docs/learning-context.md)
- [AI 应用工程学习路线图](docs/ai-application-learning-roadmap.md)
- [学习进度](docs/learning-progress.md)
- [学习资料清单](docs/learning-resources.md)
- [旧版长期进度文档](docs/ai-application-learning-progress.md)

## Python 基础学习笔记索引

| 顺序 | 主题 | 笔记路径 |
| --- | --- | --- |
| 0 | Python 项目环境和 uv | [notes/python-project-environment.md](notes/python-project-environment.md) |
| 1 | 变量和基本类型 | [notes/python-variables-and-types.md](notes/python-variables-and-types.md) |
| 2 | 字符串 | [notes/python-strings.md](notes/python-strings.md) |
| 3 | 列表 | [notes/python-lists.md](notes/python-lists.md) |
| 4 | 字典 | [notes/python-dicts.md](notes/python-dicts.md) |
| 5 | 条件判断 | [notes/python-conditions.md](notes/python-conditions.md) |
| 6 | 循环 | [notes/python-loops.md](notes/python-loops.md) |
| 7 | 函数 | [notes/python-functions.md](notes/python-functions.md) |
| 8 | 模块导入 | [notes/python-imports.md](notes/python-imports.md) |
| 9 | 异常处理 | [notes/python-exceptions.md](notes/python-exceptions.md) |
| 10 | 文件读写和 JSON | [notes/python-files-json.md](notes/python-files-json.md) |
| 11 | 类型提示 | [notes/python-type-hints.md](notes/python-type-hints.md) |
| 12 | 类和对象 | [notes/python-classes.md](notes/python-classes.md) |
| 13 | 元组和集合 | [notes/python-tuples-sets.md](notes/python-tuples-sets.md) |
| 14 | 常用数据处理写法 | [notes/python-data-processing.md](notes/python-data-processing.md) |
| 15 | 函数进阶 | [notes/python-function-advanced.md](notes/python-function-advanced.md) |
| 16 | 标准库基础 | [notes/python-standard-library.md](notes/python-standard-library.md) |
| 17 | 正则表达式 re | [notes/python-regex.md](notes/python-regex.md) |
| 18 | pytest 测试基础 | [notes/python-pytest.md](notes/python-pytest.md) |
| 19 | 调试和报错阅读 | [notes/python-debugging-traceback.md](notes/python-debugging-traceback.md) |
| 20 | HTTP/API 基础 | [notes/python-http-api.md](notes/python-http-api.md) |
| 21 | async/await 异步基础 | [notes/python-async-await.md](notes/python-async-await.md) |
| 22 | Python 基础综合项目 | [notes/python-mini-project.md](notes/python-mini-project.md) |

对应练习代码主要在 [projects/python-basics](projects/python-basics)。

## 阶段 1：Python AI 服务学习笔记索引

| 顺序 | 主题 | 笔记路径 | 代码路径 |
| --- | --- | --- | --- |
| 1 | Web 服务、HTTP 和 API 是什么 | [notes/fastapi-stage1-01-web-http-api.md](notes/fastapi-stage1-01-web-http-api.md) | [projects/ai-service](projects/ai-service) |
| 2 | FastAPI 是什么 | [notes/fastapi-stage1-02-what-is-fastapi.md](notes/fastapi-stage1-02-what-is-fastapi.md) | [projects/ai-service](projects/ai-service) |
| 3 | 创建 `ai-service` 项目骨架 | [notes/fastapi-stage1-03-ai-service-project-skeleton.md](notes/fastapi-stage1-03-ai-service-project-skeleton.md) | [projects/ai-service](projects/ai-service) |
| 4 | FastAPI 最小服务 `/health` | [notes/fastapi-stage1-04-health-endpoint.md](notes/fastapi-stage1-04-health-endpoint.md) | [projects/ai-service](projects/ai-service) |
| 5 | router 路由拆分 | [notes/fastapi-stage1-05-router-splitting.md](notes/fastapi-stage1-05-router-splitting.md) | [projects/ai-service](projects/ai-service) |
| 6 | POST、请求体和 JSON | [notes/fastapi-stage1-06-post-body-json.md](notes/fastapi-stage1-06-post-body-json.md) | [projects/ai-service](projects/ai-service) |
| 7 | Pydantic 请求模型 | [notes/fastapi-stage1-07-pydantic-request-model.md](notes/fastapi-stage1-07-pydantic-request-model.md) | [projects/ai-service](projects/ai-service) |
| 8 | Pydantic 响应模型 | [notes/fastapi-stage1-08-pydantic-response-model.md](notes/fastapi-stage1-08-pydantic-response-model.md) | [projects/ai-service](projects/ai-service) |
| 9 | 模拟 `/chat` 接口 | [notes/fastapi-stage1-09-mock-chat-endpoint.md](notes/fastapi-stage1-09-mock-chat-endpoint.md) | [projects/ai-service](projects/ai-service) |
| 10 | 测试 FastAPI 接口 | [notes/fastapi-stage1-10-testing-fastapi-apis.md](notes/fastapi-stage1-10-testing-fastapi-apis.md) | [projects/ai-service](projects/ai-service) |
| 11 | `.env` 配置读取 | [notes/fastapi-stage1-11-env-config.md](notes/fastapi-stage1-11-env-config.md) | [projects/ai-service](projects/ai-service) |
| 12 | `logging` 日志 | [notes/fastapi-stage1-12-logging.md](notes/fastapi-stage1-12-logging.md) | [projects/ai-service](projects/ai-service) |
| 13 | `trace_id` 请求追踪 | [notes/fastapi-stage1-13-trace-id.md](notes/fastapi-stage1-13-trace-id.md) | [projects/ai-service](projects/ai-service) |
| 14 | 统一异常处理 | [notes/fastapi-stage1-14-exception-handling.md](notes/fastapi-stage1-14-exception-handling.md) | [projects/ai-service](projects/ai-service) |
| 15 | CORS 基础 | [notes/fastapi-stage1-15-cors.md](notes/fastapi-stage1-15-cors.md) | [projects/ai-service](projects/ai-service) |
| 16 | 阶段 1 项目整理 | [notes/fastapi-stage1-16-project-summary.md](notes/fastapi-stage1-16-project-summary.md) | [projects/ai-service](projects/ai-service) |

## 阶段 2：LLM API 基础调用学习笔记索引

| 顺序 | 主题 | 笔记路径 | 代码路径 |
| --- | --- | --- | --- |
| 1 | 什么是 LLM API | [notes/llm-api-stage2-01-what-is-llm-api.md](notes/llm-api-stage2-01-what-is-llm-api.md) | [projects/ai-service](projects/ai-service) |
| 2 | API key 和 `.env` 安全配置 | [notes/llm-api-stage2-02-api-key-env-security.md](notes/llm-api-stage2-02-api-key-env-security.md) | [projects/ai-service](projects/ai-service) |
| 3 | token、上下文窗口、费用基础 | [notes/llm-api-stage2-03-token-context-cost.md](notes/llm-api-stage2-03-token-context-cost.md) | [projects/ai-service](projects/ai-service) |
| 4 | OpenAI-compatible SDK 基础调用方式 | [notes/llm-api-stage2-04-openai-compatible-sdk.md](notes/llm-api-stage2-04-openai-compatible-sdk.md) | [projects/ai-service](projects/ai-service) |
| 5 | messages 是什么：system / user / assistant | [notes/llm-api-stage2-05-messages-roles.md](notes/llm-api-stage2-05-messages-roles.md) | [projects/ai-service](projects/ai-service) |
| 6 | prompt 基础：怎么写清楚任务 | [notes/llm-api-stage2-06-prompt-basics.md](notes/llm-api-stage2-06-prompt-basics.md) | [projects/ai-service](projects/ai-service) |
| 7 | 第一次真实 `/chat` 调用 | [notes/llm-api-stage2-07-real-chat-call.md](notes/llm-api-stage2-07-real-chat-call.md) | [projects/ai-service](projects/ai-service) |
| 8 | 多轮对话基础：历史消息怎么传 | [notes/llm-api-stage2-08-multi-turn-history.md](notes/llm-api-stage2-08-multi-turn-history.md) | [projects/ai-service](projects/ai-service) |
| 9 | timeout 超时 | [notes/llm-api-stage2-09-timeout.md](notes/llm-api-stage2-09-timeout.md) | [projects/ai-service](projects/ai-service) |
| 10 | retry 重试和 rate limit 限流基础 | [notes/llm-api-stage2-10-retry-rate-limit.md](notes/llm-api-stage2-10-retry-rate-limit.md) | [projects/ai-service](projects/ai-service) |
| 11 | 模型调用错误处理 | [notes/llm-api-stage2-11-model-error-handling.md](notes/llm-api-stage2-11-model-error-handling.md) | [projects/ai-service](projects/ai-service) |
| 12 | 模型调用日志：模型名、耗时、trace_id、token | [notes/llm-api-stage2-12-llm-call-logging.md](notes/llm-api-stage2-12-llm-call-logging.md) | [projects/ai-service](projects/ai-service) |
| 13 | streaming 流式输出是什么 | [notes/llm-api-stage2-13-streaming-concept.md](notes/llm-api-stage2-13-streaming-concept.md) | [projects/ai-service](projects/ai-service) |
| 14 | FastAPI `StreamingResponse` 实现 `/stream-chat` | [notes/llm-api-stage2-14-stream-chat-endpoint.md](notes/llm-api-stage2-14-stream-chat-endpoint.md) | [projects/ai-service](projects/ai-service) |
| 15 | 结构化输出是什么 | [notes/llm-api-stage2-15-structured-output-concept.md](notes/llm-api-stage2-15-structured-output-concept.md) | [projects/ai-service](projects/ai-service) |
| 16 | Pydantic 约束结构化输出 | [notes/llm-api-stage2-16-pydantic-structured-output.md](notes/llm-api-stage2-16-pydantic-structured-output.md) | [projects/ai-service](projects/ai-service) |
| 17 | 测试模型调用：mock/fake LLM client | [notes/llm-api-stage2-17-testing-model-calls.md](notes/llm-api-stage2-17-testing-model-calls.md) | [projects/ai-service](projects/ai-service) |
| 18 | 阶段 2 项目整理 | [notes/llm-api-stage2-18-project-summary.md](notes/llm-api-stage2-18-project-summary.md) | [projects/ai-service](projects/ai-service) |

## 阶段 3：LangChain + Java 工具调用学习笔记索引

| 顺序 | 主题 | 笔记路径 | 代码路径 |
| --- | --- | --- | --- |
| 1 | Tool Calling 是什么 | [notes/tool-calling-stage3-01-what-is-tool-calling.md](notes/tool-calling-stage3-01-what-is-tool-calling.md) | [projects/ai-service](projects/ai-service) |
| 2 | 为什么 AI 不能直接操作业务系统 | [notes/tool-calling-stage3-02-why-ai-cannot-operate-business-system-directly.md](notes/tool-calling-stage3-02-why-ai-cannot-operate-business-system-directly.md) | [projects/ai-service](projects/ai-service) |
| 3 | 工具参数和 JSON Schema | [notes/tool-calling-stage3-03-tool-parameters-json-schema.md](notes/tool-calling-stage3-03-tool-parameters-json-schema.md) | [projects/ai-service](projects/ai-service) |
| 4 | 结构化输出 vs Tool Calling | [notes/tool-calling-stage3-04-structured-output-vs-tool-calling.md](notes/tool-calling-stage3-04-structured-output-vs-tool-calling.md) | [projects/ai-service](projects/ai-service) |
| 5 | 用 fake tool 模拟查订单 | [notes/tool-calling-stage3-05-fake-query-order-tool.md](notes/tool-calling-stage3-05-fake-query-order-tool.md) | [projects/ai-service](projects/ai-service) |
| 6 | 工具调用结果也要 Pydantic 校验 | [notes/tool-calling-stage3-06-tool-result-pydantic-validation.md](notes/tool-calling-stage3-06-tool-result-pydantic-validation.md) | [projects/ai-service](projects/ai-service) |
| 7 | 工具调用错误处理：超时、404、500 | [notes/tool-calling-stage3-07-tool-error-handling.md](notes/tool-calling-stage3-07-tool-error-handling.md) | [projects/ai-service](projects/ai-service) |
| 8 | 工具调用权限边界 | [notes/tool-calling-stage3-08-tool-permission-boundary.md](notes/tool-calling-stage3-08-tool-permission-boundary.md) | [projects/ai-service](projects/ai-service) |
| 9 | 工具调用幂等性 | [notes/tool-calling-stage3-09-tool-idempotency.md](notes/tool-calling-stage3-09-tool-idempotency.md) | [projects/ai-service](projects/ai-service) |
| 10 | 用 FastAPI 写一个最小 Java mock 业务服务 | [notes/tool-calling-stage3-10-java-mock-service.md](notes/tool-calling-stage3-10-java-mock-service.md) | [projects/java-mock-service](projects/java-mock-service) |
| 11 | Python AI 服务调用 Java mock API | [notes/tool-calling-stage3-11-python-calls-java-mock-api.md](notes/tool-calling-stage3-11-python-calls-java-mock-api.md) | [projects/ai-service](projects/ai-service)、[projects/java-mock-service](projects/java-mock-service) |
| 12 | 让模型决定是否调用工具 | [notes/tool-calling-stage3-12-model-decides-tool-call.md](notes/tool-calling-stage3-12-model-decides-tool-call.md) | [projects/ai-service](projects/ai-service) |
| 13 | 工具调用结果再交给模型总结 | [notes/tool-calling-stage3-13-tool-result-model-summary.md](notes/tool-calling-stage3-13-tool-result-model-summary.md) | [projects/ai-service](projects/ai-service)、[projects/java-mock-service](projects/java-mock-service) |
| 14 | 用户确认机制：敏感操作不能直接执行 | [notes/tool-calling-stage3-14-user-confirmation.md](notes/tool-calling-stage3-14-user-confirmation.md) | [projects/ai-service](projects/ai-service) |
| 15 | 创建工单流程：提取字段、确认、调用 Java API | [notes/tool-calling-stage3-15-ticket-creation-workflow.md](notes/tool-calling-stage3-15-ticket-creation-workflow.md) | [projects/ai-service](projects/ai-service)、[projects/java-mock-service](projects/java-mock-service) |
| 16 | 工具调用日志和 trace_id 串联 | [notes/tool-calling-stage3-16-tool-logging-trace-id.md](notes/tool-calling-stage3-16-tool-logging-trace-id.md) | [projects/ai-service](projects/ai-service) |
| 17 | 工具调用测试：fake Java API / fake tool | [notes/tool-calling-stage3-17-tool-testing-fakes.md](notes/tool-calling-stage3-17-tool-testing-fakes.md) | [projects/ai-service](projects/ai-service) |
| 18 | LangChain 是什么，为什么现在才引入 | [notes/tool-calling-stage3-18-what-is-langchain.md](notes/tool-calling-stage3-18-what-is-langchain.md) | [projects/ai-service](projects/ai-service) |
| 19 | LangChain ChatModel 基础 | [notes/tool-calling-stage3-19-langchain-chatmodel-basics.md](notes/tool-calling-stage3-19-langchain-chatmodel-basics.md) | [projects/ai-service](projects/ai-service) |
| 20 | LangChain Tool 基础 | [notes/tool-calling-stage3-20-langchain-tool-basics.md](notes/tool-calling-stage3-20-langchain-tool-basics.md) | [projects/ai-service](projects/ai-service) |
| 21 | LangChain 结构化输出 | [notes/tool-calling-stage3-21-langchain-structured-output.md](notes/tool-calling-stage3-21-langchain-structured-output.md) | [projects/ai-service](projects/ai-service) |
| 22 | 阶段 3 项目整理 | [notes/tool-calling-stage3-22-project-summary.md](notes/tool-calling-stage3-22-project-summary.md) | [projects/ai-service](projects/ai-service)、[projects/java-mock-service](projects/java-mock-service) |

## 阶段 4：企业知识库 RAG 学习笔记索引

| 顺序 | 主题 | 笔记路径 | 代码路径 |
| --- | --- | --- | --- |
| 1 | RAG 是什么，为什么大模型需要知识库 | [notes/rag-stage4-01-what-is-rag.md](notes/rag-stage4-01-what-is-rag.md) | 待新增 |
| 2 | RAG 完整流程：load -> split -> embed -> store -> retrieve -> generate | [notes/rag-stage4-02-rag-pipeline.md](notes/rag-stage4-02-rag-pipeline.md) | 待新增 |

## 当前目标

12 周内完成两个能展示的项目：

1. 企业知识库 RAG 系统
2. 智能工单 Agent

第三个项目“业务数据助手”作为加分项，等前两个主项目稳定后再做。

每次继续学习时，优先更新 `docs/learning-progress.md`，再把代码、笔记和复盘分别放入对应目录。
