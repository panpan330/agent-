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

## 当前目标

12 周内完成两个能展示的项目：

1. 企业知识库 RAG 系统
2. 智能工单 Agent

第三个项目“业务数据助手”作为加分项，等前两个主项目稳定后再做。

每次继续学习时，优先更新 `docs/learning-progress.md`，再把代码、笔记和复盘分别放入对应目录。
