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

## 当前目标

12 周内完成两个能展示的项目：

1. 企业知识库 RAG 系统
2. 智能工单 Agent

第三个项目“业务数据助手”作为加分项，等前两个主项目稳定后再做。

每次继续学习时，优先更新 `docs/learning-progress.md`，再把代码、笔记和复盘分别放入对应目录。
