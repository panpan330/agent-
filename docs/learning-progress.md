# Java + Python + AI 学习进度

## 当前状态

```text
路线已确定：Java 后端 + Python AI 服务 + LangChain/LangGraph + RAG/Agent 工程化
当前阶段：第 0 周，项目和学习上下文初始化
主要仓库：D:\wendang\java+python+ai
执行路线：docs/ai-application-learning-roadmap.md
```

## 阶段进度

| 阶段 | 时间 | 主题 | 状态 | 产出 |
| --- | --- | --- | --- | --- |
| M0 | 第 0 周 | 环境与仓库 | 进行中 | README、上下文、路线图、进度表 |
| M1 | 第 1-2 周 | Python AI 服务基础 | 未开始 | `projects/ai-service`、聊天接口、流式输出、结构化输出 |
| M2 | 第 3-4 周 | LangChain + Java 工具调用 | 未开始 | 客服助手 v1、Java mock 业务服务 |
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
- [ ] 创建 `projects/ai-service`
- [ ] 搭建 FastAPI 基础项目
- [ ] 实现 `/health`
- [ ] 实现 `/chat`
- [ ] 实现 `/stream-chat`
- [ ] 加入 `.env` 配置读取
- [ ] 加入基础日志、trace_id 和异常处理
- [ ] 增加结构化输出练习接口
- [ ] 写第 1 篇学习笔记：Python AI 服务项目结构

## 当前 Sprint 验收标准

M0/M1 第一阶段完成时，必须满足：

- [ ] 本地能运行 Python、Java、Docker。
- [x] 本地能运行 Python。
- [x] 本地能运行 Java。
- [ ] 本地能运行 Docker。
- [x] uv 安装在 D 盘，缓存、Python 管理目录和工具目录都指向 D 盘。
- [ ] `projects/ai-service` 有清晰目录结构。
- [ ] FastAPI 服务能启动。
- [ ] `/health` 返回正常。
- [ ] `/chat` 能完成一次普通模型调用。
- [ ] `/stream-chat` 能流式返回。
- [ ] 请求日志包含 trace_id、模型名、耗时、错误信息。
- [ ] 密钥只从 `.env` 读取，并提供 `.env.example`。
- [ ] 至少有 5 个 pytest 用例。

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
- [ ] logging
- [ ] pytest
- [ ] Dockerfile

### LLM API

- [ ] system prompt / user prompt
- [ ] streaming
- [ ] structured output
- [ ] tool calling
- [ ] token 成本
- [ ] 超时和重试
- [ ] 模型错误兜底

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

- [ ] 请求日志
- [ ] 模型调用日志
- [ ] tool 调用日志
- [ ] trace_id
- [ ] token 成本统计
- [ ] 限流
- [ ] 重试
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
