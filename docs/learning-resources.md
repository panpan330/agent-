# 学习资料清单

维护原则：

- 官方文档优先，用来确认概念、API 和最佳实践。
- GitHub 学习笔记和教程作为辅助，用来补中文解释和练习。
- 视频只作为理解辅助，不用视频替代动手编码。
- 每个资料都要服务当前学习阶段，不为了收藏资料而收藏。
- 学完一个资料，要沉淀到 `notes/`，并用代码验证。

## 1. Python 基础

### 主资料

- [Python 官方教程](https://docs.python.org/3/tutorial/index.html)
  - 用途：确认 Python 语法和语言特性。
  - 使用方式：遇到变量、列表、字典、函数、异常、模块等概念时查官方解释。

- [Datawhale：聪明办法学 Python 第二版](https://github.com/datawhalechina/learn-python-the-smart-way-v2)
  - 用途：中文系统入门资料，偏计算机科学和 AI 学习方向。
  - 使用方式：作为 Python 基础阶段的主要中文参考。

### 辅助资料

- [jackfrued/Python-100-Days](https://github.com/jackfrued/python-100-days)
  - 用途：中文内容完整，覆盖 Python 基础、Web、数据、项目实践。
  - 使用方式：不按 100 天完整照学，只按当前知识点查对应章节。

- [shibing624/python-tutorial](https://github.com/shibing624/python-tutorial)
  - 用途：偏实用教程，包含 Python 基础、高级特性、Web、爬虫等。
  - 使用方式：作为补充例子和复习材料。

### 视频辅助

- [小甲鱼：零基础入门学习 Python](https://www.bilibili.com/video/BV1xs411Q799/)
  - 用途：适合零基础听概念。
  - 使用方式：只看当前知识点对应视频，不刷全集。

## 2. Python 项目环境与 uv

### 主资料

- [uv 官方文档](https://docs.astral.sh/uv/)
  - 用途：确认 uv 的项目管理、依赖管理、虚拟环境、lock 文件用法。

- [uv 项目指南](https://docs.astral.sh/uv/guides/projects/)
  - 用途：学习 `uv init`、`uv add`、`uv run`、`uv sync`。

### 已完成练习

- `projects/python-basics`
- `notes/python-project-environment.md`

## 3. HTTP / JSON / requests

### 主资料

- [Requests 官方 Quickstart](https://requests.readthedocs.io/en/latest/user/quickstart/)
  - 用途：学习 GET、POST、headers、JSON、timeout 等基础用法。

- [Requests 中文快速上手](https://docs.python-requests.org/projects/cn/zh-cn/latest/user/quickstart.html)
  - 用途：中文辅助理解。

### 辅助练习

- [4GeeksAcademy: Python API Requests Tutorial and Exercises](https://github.com/4GeeksAcademy/python-http-requests-api-tutorial-exercises)
  - 用途：练习 HTTP 请求和 API 调用。

## 4. FastAPI

### 主资料

- [FastAPI 官方 Tutorial](https://fastapi.tiangolo.com/tutorial/)
  - 用途：学习路由、请求参数、响应模型、依赖注入、自动文档。

- [FastAPI GitHub 仓库](https://github.com/fastapi/fastapi)
  - 用途：确认框架定位和官方示例。

### 中文辅助

- [FastAPI-Learning-Example](https://github.com/oinsd/FastAPI-Learning-Example)
  - 用途：中文视频配套示例。

- [fastapi-best-practices-zh-cn](https://github.com/hellowac/fastapi-best-practices-zh-cn)
  - 用途：进阶阶段看项目结构、异步、最佳实践。
  - 注意：不要一开始就看，等基础接口会写后再看。

## 5. Pydantic

### 主资料

- [Pydantic 官方 Get Started](https://pydantic.dev/docs/validation/latest/get-started/)
  - 用途：理解数据校验的作用。

- [Pydantic Models 文档](https://pydantic.dev/docs/validation/latest/concepts/models/)
  - 用途：学习 `BaseModel`、字段类型、嵌套模型、校验错误。

## 6. LangChain

### 主资料

- [LangChain 官方 Overview](https://docs.langchain.com/oss/python/langchain/overview)
  - 用途：理解 LangChain 在模型、prompt、tool、agent harness 中的位置。

- [LangChain Python Reference](https://reference.langchain.com/python/langchain)
  - 用途：查 API 细节。

## 7. LangGraph

### 主资料

- [LangGraph 官方 Overview](https://docs.langchain.com/oss/python/langgraph/overview)
  - 用途：理解有状态、长流程、可恢复 agent 编排。

- [LangGraph Quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart)
  - 用途：做第一个最小图流程。

- [LangChain Academy: Introduction to LangGraph](https://academy.langchain.com/courses/intro-to-langgraph)
  - 用途：系统课程辅助理解。

## 8. RAG / 向量库

### 主资料

- [Qdrant 官方文档](https://qdrant.tech/documentation/)
  - 用途：理解向量库、collection、point、filter、search。

- [Qdrant Local Quickstart](https://qdrant.tech/documentation/quickstart/)
  - 用途：后续本地跑 Qdrant 时使用。

### 辅助理解

- [RAGFlow GitHub](https://github.com/infiniflow/ragflow)
  - 用途：观察成熟 RAG 系统的功能边界。
  - 注意：不作为初学主线，先自己实现基础 RAG。

- [RAGFlow 文档](https://ragflow.io/docs/)
  - 用途：参考 RAG 产品化能力，如数据集、解析、引用、问答流程。

## 当前阶段推荐资料组合

现在处于 Python 基础阶段，优先看：

1. Datawhale：聪明办法学 Python 第二版
2. Python 官方教程
3. 小甲鱼 Python 视频，只看对应知识点
4. 本仓库 `notes/` 中我们自己整理的笔记

暂时不要深入：

- FastAPI 最佳实践
- LangChain
- LangGraph
- RAGFlow
- Qdrant

这些后面到对应阶段再看。
