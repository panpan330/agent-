# 阶段 4 第 36 节：Qdrant vs Milvus：什么时候选谁

> 本节目标：把我们已经实际跑过的 Qdrant 和 Milvus 放到同一个框架里比较，真正理解“什么时候选 Qdrant，什么时候选 Milvus”，而不是只记一个简单结论。

## 0. 本节学习地图

前面我们已经分别学过：

- Qdrant 的 collection、point、vector、payload；
- Qdrant 入库、检索、payload filter、score_threshold、删除和重新入库；
- Milvus 的 collection、schema、field、entity、index；
- Milvus Standalone 本地启动；
- 同一批知识文档写入 Milvus；
- Milvus metadata filter 和 scalar index。

所以这一节不再单独学习某一个 API，而是进入“选型能力”。

你以后做项目或面试时，别人可能会问：

```text
你为什么用 Qdrant？
为什么不用 Milvus？
什么时候 Milvus 更合适？
两个向量数据库有什么区别？
RAG 项目里 vector store 应该怎么选？
```

这类问题不能只回答：

```text
Qdrant 简单，Milvus 强。
```

这句话方向大体没错，但太粗。真正能体现理解的回答应该能说明：

- 项目规模；
- 部署环境；
- 团队运维能力；
- 数据模型复杂度；
- filter 和 index 需求；
- 是否需要集群和高可用；
- 是否要多语言 SDK；
- 是否已经在 Kubernetes 体系里；
- 是否需要从学习版平滑走到生产级。

本节学完，你应该能做到：

1. 说清 Qdrant 和 Milvus 都在 RAG 链路里的位置。
2. 说清两者数据模型如何对应。
3. 说清 Qdrant 为什么适合先学、先做 Demo、先做中小型 RAG。
4. 说清 Milvus 为什么适合更强结构、更大规模、更复杂运维场景。
5. 能根据具体项目条件做出合理选择。
6. 能解释我们当前项目为什么主线先用 Qdrant，再补 Milvus。
7. 能说清“向量数据库选型不是越强越好，而是越匹配越好”。

本节不新增业务代码。原因是：

```text
本节主题是选型判断，代码不是主要学习载体。
```

硬写一个脚本并不能帮助你真正理解 Qdrant 和 Milvus 的差异。我们已经在前面分别跑通两边入库和检索，这一节应该把知识抽象出来。

## 1. 基础知识铺垫

### 1.1 什么是技术选型

技术选型不是“哪个工具最厉害就选哪个”。

技术选型是：

```text
在当前业务目标、数据规模、团队能力、成本限制、上线时间和未来扩展之间做权衡。
```

例如：

```text
我要学 RAG，数据只有几百个文档，目标是快速做出能跑的系统。
```

这时你应该优先考虑：

- 容易安装；
- API 容易理解；
- 错误容易排查；
- 文档适合初学；
- 本地能快速验证；
- 对硬件要求不高。

又例如：

```text
公司有数亿到数十亿向量，需要多租户、高吞吐、复杂索引、Kubernetes 集群和专业运维。
```

这时你应该优先考虑：

- 分布式架构；
- 高可用；
- 组件可扩展；
- 存储和计算扩展能力；
- 大规模索引管理；
- 监控和运维能力；
- 团队是否能维护复杂系统。

同一个工具在不同阶段的答案可能不同。

### 1.2 “能用”和“适合”不是一回事

Qdrant 能做 RAG，Milvus 也能做 RAG。

但“能做”不等于“最适合当前场景”。

你可以用 Milvus 做一个 100 条数据的学习 Demo，也可以用 Qdrant 做生产项目。但选型时要问：

```text
我当前最重要的问题是什么？
```

如果最重要的问题是：

```text
先理解 RAG 的完整流程
```

那么简单清晰更重要。

如果最重要的问题是：

```text
承载超大规模向量数据和复杂部署
```

那么架构能力更重要。

技术选型最怕两种极端：

```text
只选最简单的，不考虑未来。
只选最重的，不考虑当前。
```

### 1.3 向量数据库在 RAG 里到底负责什么

RAG 的主流程是：

```text
load -> split -> embed -> store -> retrieve -> generate
```

向量数据库主要负责：

```text
store + retrieve
```

也就是：

- 存储 chunk 的向量；
- 存储 chunk 的 metadata；
- 根据 query vector 查相似 chunk；
- 根据 metadata filter 缩小检索范围；
- 返回 score、payload/entity；
- 支持删除、更新、重新入库；
- 支持索引、性能优化、扩容和备份。

它不负责：

- 替你切分文档；
- 替你决定 chunk size；
- 替你调用大模型；
- 替你保证回答一定正确；
- 替你做完整权限系统；
- 替你做业务审核。

所以选向量数据库时，重点不是“它能不能生成答案”，而是：

```text
它能不能稳定、高效、可维护地存储和检索你的知识向量。
```

### 1.4 RAG 选型要看哪些维度

选 Qdrant 或 Milvus 时，至少看这些维度：

| 维度 | 要问的问题 |
| --- | --- |
| 学习成本 | 初学能不能很快理解核心概念 |
| 本地启动 | 本地 Docker 能不能顺利跑起来 |
| 数据模型 | 是否需要强 schema |
| metadata filter | 过滤能力是否符合业务 |
| 索引机制 | 是否容易创建和维护索引 |
| 数据规模 | 当前和未来向量数量有多大 |
| 部署复杂度 | 单机够不够，是否需要集群 |
| 运维能力 | 团队能不能维护组件、备份、监控、升级 |
| API 习惯 | REST、gRPC、SDK 是否符合团队习惯 |
| 生态整合 | LangChain、框架、云服务支持是否方便 |
| 成本 | 机器、内存、存储、运维、人力成本 |
| 上线时间 | 是快速验证还是长期生产系统 |

注意：这些维度没有一个永远第一。它们要根据项目阶段排序。

### 1.5 什么叫“学习阶段选型”

学习阶段的目标不是追求最终生产级最优架构。

学习阶段要优先做到：

```text
能理解
能跑通
能排错
能解释
能逐步扩展
```

所以学习阶段选型应该偏：

- 概念少；
- 链路短；
- 安装简单；
- API 直观；
- 日志和错误容易看懂；
- 本地验证成本低。

这就是我们阶段 4 一开始先用 Qdrant 的原因。

### 1.6 什么叫“生产阶段选型”

生产阶段的目标不只是“能跑”。

生产阶段要关心：

- 高可用；
- 备份恢复；
- 监控告警；
- 权限和网络安全；
- 数据迁移；
- 版本升级；
- 多节点扩展；
- 查询吞吐；
- 延迟；
- 成本；
- 团队维护能力。

生产选型往往不由一个技术点决定，而由一组现实条件决定。

例如：

```text
Milvus 分布式能力强，但如果团队没有 Kubernetes 运维经验，直接上 Milvus Distributed 可能不是收益，而是风险。
```

### 1.7 为什么我们先 Qdrant 后 Milvus

我们的学习路线是：

```text
先用 Qdrant 跑通 RAG 主线
再用 Milvus 做向量库对比和工程扩展
```

原因是：

1. Qdrant 的 point/payload 模型更直观。
2. Qdrant REST API 对初学者更友好。
3. 本地启动和排查更轻。
4. 先理解 RAG 主线比先理解复杂部署更重要。
5. Milvus 的 schema/index/deployment 更适合在你已有 RAG 主线后再学。

这不是说 Milvus 不好。

恰恰相反，Milvus 很值得学。只是学习顺序应该服务理解：

```text
先建立 RAG 主线，再比较更复杂的向量数据库系统。
```

## 2. 本节主题系统讲解

### 2.1 一句话定位 Qdrant 和 Milvus

可以先记一个简化定位：

```text
Qdrant：更容易上手、模型直观、适合快速构建 RAG 和中小规模工程落地。
Milvus：更强调强 schema、索引体系和大规模向量检索，适合更重的企业级和大规模场景。
```

但这只是入口，不是完整答案。

更准确地说：

- Qdrant 更像“面向应用工程师友好的向量搜索引擎”；
- Milvus 更像“面向大规模向量检索系统的数据库平台”。

### 2.2 数据模型对比

Qdrant 的核心概念：

```text
collection
point
vector
payload
```

Milvus 的核心概念：

```text
collection
schema
field
entity
index
```

对应关系：

| RAG 概念 | Qdrant | Milvus |
| --- | --- | --- |
| 一组知识向量 | collection | collection |
| 一个 chunk 记录 | point | entity |
| chunk 唯一 ID | point id | primary field |
| embedding 向量 | vector | vector field |
| metadata | payload | scalar fields |
| 文本正文 | payload 里的 content | scalar field `content` |
| 过滤字段 | payload key | scalar field |
| 字段索引 | payload index | scalar index |

最关键的差异是：

```text
Qdrant 的 payload 更灵活。
Milvus 的 schema 更明确。
```

### 2.3 Qdrant 的 point/payload 为什么适合先学

Qdrant point 很像一个 JSON 对象：

```json
{
  "id": "chunk_001",
  "vector": [0.1, 0.2, 0.3],
  "payload": {
    "content": "退货运费规则...",
    "source": "refund-return-policy.md",
    "business_domain": "refund",
    "permission_group": "customer_service"
  }
}
```

这种模型对初学者很友好：

- 一个 point 就是一条 chunk；
- vector 是向量；
- payload 是附加信息；
- filter 就是按 payload 筛选；
- REST API 请求体很好读。

所以你在阶段 4 前半段能比较顺利地理解：

```text
文档 -> chunk -> vector + payload -> point
```

### 2.4 Milvus 的 schema/entity 为什么更“数据库化”

Milvus 更强调 schema。

一个 collection 创建前，你要定义：

- primary key 字段；
- vector field；
- scalar fields；
- 字段类型；
- 字符串最大长度；
- 向量维度；
- index params。

例如本项目里 Milvus entity 大概长这样：

```text
chunk_id: VARCHAR primary key
embedding: FLOAT_VECTOR
content: VARCHAR
source: VARCHAR
doc_type: VARCHAR
business_domain: VARCHAR
permission_group: VARCHAR
chunk_index: INT64
```

这种方式更严谨。

好处：

- 字段结构明确；
- 数据质量更容易约束；
- 类型错误更早暴露；
- 更接近传统数据库建模；
- 适合复杂系统长期维护。

代价：

- 初学成本更高；
- 新增字段要考虑 schema；
- 调试门槛更高；
- 本地部署组件更多。

### 2.5 metadata filter 对比

Qdrant filter：

```json
{
  "must": [
    {
      "key": "permission_group",
      "match": {
        "value": "customer_service"
      }
    }
  ]
}
```

Milvus filter：

```text
permission_group == "customer_service"
```

这两种设计各有特点。

Qdrant 的 filter 是结构化 JSON：

- 更像 API 请求体；
- 对程序构造比较友好；
- 不容易出现字符串拼接错误；
- 和 payload 模型配套。

Milvus 的 filter 是表达式字符串：

- 表达能力直观；
- 类似数据库查询条件；
- 写复杂条件时简洁；
- 但后端必须负责字段白名单和字符串转义。

所以在我们的项目里：

```text
业务层继续使用结构化 payload_filter dict。
Qdrant adapter 原样转给 Qdrant。
Milvus adapter 把 dict 翻译成 Milvus expression。
```

这就是 adapter 的价值。

### 2.6 过滤索引对比

Qdrant 叫 payload index。

Milvus 叫 scalar index。

两者解决的问题类似：

```text
让 metadata filter 更快、更稳定地缩小候选范围。
```

区别是：

| 维度 | Qdrant payload index | Milvus scalar index |
| --- | --- | --- |
| 依附对象 | payload 字段 | scalar field |
| 建模风格 | JSON payload 上的索引 | schema field 上的索引 |
| 学习体验 | 更接近给 JSON key 建索引 | 更接近数据库字段索引 |
| 常见字段 | permission、domain、source | permission、domain、source |
| 设计重点 | 过滤和 HNSW 结合 | scalar 表达式和向量检索候选缩小 |

本质上你要记住：

```text
Qdrant 的 payload index 和 Milvus 的 scalar index，都不是为了生成答案，而是为了让过滤检索更高效。
```

### 2.7 向量索引对比

向量索引是用来加速相似度搜索的。

Qdrant 默认围绕 HNSW 这类图索引做向量搜索。前面我们学习 Qdrant 时，没有深入调 HNSW 参数，因为当时目标是先跑通 RAG。

Milvus 支持更丰富的索引体系，并且更强调 index params 和 metric type。第 34 节我们为了学习简单，使用：

```text
AUTOINDEX
```

这表示让 Milvus 自动选择合适索引。

当前阶段不要急着深入所有向量索引类型。你只要先把这层关系讲清楚：

```text
向量索引负责相似度搜索。
scalar/payload 索引负责 metadata filter。
```

等以后进入性能优化、召回率评测、十万/百万级数据时，再学习 HNSW、IVF、DiskANN 等索引细节。

### 2.8 部署复杂度对比

我们本地实际体验已经很明显。

Qdrant：

```text
docker run qdrant/qdrant
6333 HTTP
6334 gRPC
```

它启动简单，访问也直观。

Milvus Standalone：

```text
Milvus standalone
etcd
MinIO
19530 SDK/gRPC
9091 WebUI/管理
```

你已经亲自遇到过：

- Docker Compose；
- 容器状态；
- `milvus-standalone` 退出；
- volume 权限；
- VMware 内存；
- 端口连通；
- Windows 访问虚拟机 IP。

这正好说明一个重要选型事实：

```text
Milvus 能力更完整，但部署和排查成本也更高。
```

这不是缺点，而是取舍。

### 2.9 本地学习体验对比

| 维度 | Qdrant | Milvus |
| --- | --- | --- |
| 第一次启动 | 更简单 | 更重 |
| 本地资源要求 | 较低 | 更高 |
| HTTP 调试 | 很直接 | 主要 SDK/gRPC，WebUI 另走端口 |
| 概念数量 | collection/point/vector/payload | collection/schema/field/entity/index |
| 初学排错 | 相对容易 | 要懂容器、依赖组件、端口、schema |
| 适合阶段 | RAG 入门和主线打通 | RAG 后半段对比和工程扩展 |

所以我们的学习顺序是合理的：

```text
Qdrant 用来建立 RAG 主线。
Milvus 用来建立大型向量数据库视角。
```

### 2.10 生产部署对比

生产部署时不能只看本地启动体验。

Qdrant 官方也有 Cloud、Kubernetes、Helm、自托管、监控、备份、安全等生产能力。

Milvus 也有 Lite、Standalone、Distributed 等部署模式，Distributed 面向更大规模和更高负载。

所以更准确的判断不是：

```text
Qdrant 只能小项目，Milvus 才能生产。
```

而是：

```text
Qdrant 的生产落地路径通常更轻，适合很多中小型到较大 RAG 应用。
Milvus 的分布式架构和强 schema 更适合团队愿意承担更重部署与运维复杂度的大规模场景。
```

### 2.11 数据规模怎么影响选择

数据规模可以粗略分层：

| 规模 | 大概情况 | 倾向 |
| --- | --- | --- |
| 几百到几万 chunks | 学习、Demo、小知识库 | Qdrant 更省心 |
| 几万到几百万 chunks | 企业部门知识库、中小生产项目 | Qdrant 或 Milvus Standalone 都可，看团队能力 |
| 千万到亿级 vectors | 大型知识库、搜索平台 | 认真评估 Milvus、Qdrant 集群和云服务 |
| 亿级到数十亿 vectors | 超大规模向量检索 | Milvus Distributed 或专业托管服务更值得评估 |

这只是学习级判断，不是硬规则。

真实选型还要看：

- 查询 QPS；
- 向量维度；
- top_k；
- filter 复杂度；
- 更新频率；
- 是否冷热分层；
- 是否多租户；
- 可用机器规格；
- 团队经验。

### 2.12 团队能力怎么影响选择

一个工具技术上适合，不代表团队能维护。

如果团队只有一两个后端开发，还没有专门运维：

```text
优先简单可靠，减少组件数量。
```

这时 Qdrant 或托管服务更现实。

如果团队已经有：

- Kubernetes；
- Prometheus/Grafana；
- 存储运维经验；
- 数据平台团队；
- 高可用方案；
- 值班和故障处理流程；

那么 Milvus Distributed 的复杂度就更容易被消化。

技术选型要问：

```text
我们能不能把它长期维护好？
```

而不是只问：

```text
它理论上能不能支撑很大规模？
```

### 2.13 数据模型复杂度怎么影响选择

如果你的 RAG chunk 比较简单：

```text
id
vector
content
source
permission_group
business_domain
```

Qdrant 的 payload 模型非常自然。

如果你的业务需要很明确的字段约束：

- 多种字段类型；
- 固定 schema；
- 字段缺失要尽早失败；
- 需要严格控制 entity 结构；
- 更接近传统数据库建模；

Milvus 的 schema 模型更有优势。

一句话：

```text
数据结构越自由，Qdrant 越顺手。
数据结构越强调 schema 和类型约束，Milvus 越自然。
```

### 2.14 更新和删除怎么影响选择

RAG 系统不是一次入库后永远不变。

企业知识库会遇到：

- 文档更新；
- 文档删除；
- 重新入库；
- 权限变更；
- metadata 修正；
- embedding 模型切换；
- 旧 chunk 清理。

我们已经在 Qdrant 里做过：

```text
按 source 删除旧 points，再重新 upsert
```

Milvus 也可以做插入、更新、删除和重新建索引，但因为 schema 和索引体系更明确，你要更小心数据结构和字段类型。

当前学习项目里，Qdrant 这块更容易先形成完整闭环。

### 2.15 多语言和 Java 后端怎么考虑

你本身有 Java 基础，后面会走：

```text
Java 后端 + Python AI 服务
```

这时向量数据库有两种接入方式：

方案 A：

```text
Java 后端不直接碰向量库
Python AI 服务负责 RAG 检索
Java 只提供业务 API
```

方案 B：

```text
Java 后端也直接调用向量库
Python AI 服务和 Java 都可能访问 vector store
```

我们当前更推荐方案 A。

原因：

- RAG 逻辑集中在 Python AI 服务；
- Java 后端继续负责业务系统；
- 权限、订单、工单等由 Java 提供 API；
- 向量库细节不会扩散到多个服务；
- 便于学习和排查。

在方案 A 里，Qdrant 或 Milvus 的 Java SDK 都不是首要问题，因为主要由 Python 调用。

如果未来公司要求 Java 直接接入向量库，再比较两边 Java SDK、团队习惯和服务边界。

### 2.16 LangChain 集成怎么考虑

LangChain 支持很多 vector store。

但你现在已经学过一个很重要的原则：

```text
不要一开始就把框架封装当成真实理解。
```

我们先自己实现 Qdrant adapter 和 Milvus adapter，是为了理解：

- collection 怎么创建；
- vector 怎么写；
- metadata 怎么存；
- filter 怎么传；
- search result 怎么解析；
- score 怎么理解；
- 错误怎么处理。

等这些懂了，再用 LangChain 的 vector store 封装，才不会变成“只会调库，不知道底层发生什么”。

选型时，LangChain 集成是加分项，但不是唯一依据。

### 2.17 成本怎么比较

成本不只是云服务价格。

成本包括：

```text
机器成本
内存成本
存储成本
网络成本
运维人力
学习成本
排错成本
迁移成本
上线时间成本
```

例如：

```text
Milvus 可以支撑很大规模，但为了一个小知识库部署多个组件，可能成本过高。
```

又例如：

```text
Qdrant 学起来快，但如果未来数据规模和查询模式明显超过当前单机方案，也要提前规划扩展和备份。
```

成本要和收益一起看。

### 2.18 安全怎么比较

向量数据库安全至少包括：

- API key 或认证；
- 内网访问；
- TLS；
- 备份加密；
- 权限控制；
- 不把数据库端口暴露到公网；
- 不把用户原始敏感问题随便记录；
- metadata filter 不能由模型绕过。

Qdrant 和 Milvus 都需要你做部署安全。

对我们项目来说，更关键的是：

```text
权限边界不应该交给模型决定。
```

无论选 Qdrant 还是 Milvus，`permission_group` 都必须由后端可信地传入 filter。

### 2.19 一个简单决策树

你可以先用这个决策树：

```text
问题 1：我现在是不是学习、Demo、小型项目？
是 -> 优先 Qdrant
否 -> 看问题 2

问题 2：团队是否需要强 schema、大规模索引体系、分布式部署？
是 -> 评估 Milvus
否 -> 看问题 3

问题 3：团队是否希望更低部署复杂度、更快上线？
是 -> 优先 Qdrant 或托管 Qdrant
否 -> 看问题 4

问题 4：数据是否达到千万、亿级甚至更大，且团队有 Kubernetes/运维能力？
是 -> 认真评估 Milvus Distributed 或托管 Milvus/Zilliz
否 -> Qdrant 或 Milvus Standalone 都可以做压测后决定
```

这个决策树不是绝对答案，但能帮你避免“凭感觉选型”。

### 2.20 当前项目应该怎么选

我们当前项目目标是：

```text
Java 后端 + Python AI 服务 + 企业知识库 RAG + 智能工单 Agent
```

当前阶段重点是：

- 学会 RAG 主线；
- 学会检索、引用、权限、无资料兜底；
- 学会工具调用和 Java 业务系统配合；
- 学会工程化测试和错误处理；
- 形成能展示、能讲解的项目。

所以当前主线建议：

```text
继续以 Qdrant 作为主线 vector store。
Milvus 作为对比学习、扩展能力和面试加分项。
```

原因：

1. Qdrant 已经承载了阶段 4 主线大部分代码。
2. Qdrant 更适合当前学习闭环。
3. 当前数据规模很小，不需要 Milvus Distributed。
4. Milvus 已经完成本地启动、入库、检索、filter/index，对比目标已经达成。
5. 后续 Agent 主线不应该被向量库部署复杂度拖慢。

这不等于放弃 Milvus。

更准确的项目策略是：

```text
主线用 Qdrant 保持推进。
Milvus 作为可切换 adapter 和选型对照保留。
```

这在工程上是一个稳妥策略。

## 3. 对比总表

### 3.1 核心定位

| 维度 | Qdrant | Milvus |
| --- | --- | --- |
| 产品定位 | 向量搜索和语义搜索引擎 | 大规模向量数据库平台 |
| 学习体感 | 更轻、更直观 | 更系统、更数据库化 |
| 数据模型 | point + vector + payload | entity + fields + schema |
| 适合入门 | 很适合 | 可以，但概念更多 |
| 适合大规模 | 可以扩展，需按部署形态评估 | 分布式路线更突出 |

### 3.2 本地开发

| 维度 | Qdrant | Milvus |
| --- | --- | --- |
| 本地启动 | 简单 Docker 容器 | Standalone 也方便，但组件和资源更多 |
| 常用端口 | `6333` HTTP、`6334` gRPC | `19530` SDK/gRPC、`9091` WebUI/管理 |
| 调试方式 | REST、WebUI、SDK | SDK、WebUI、日志、组件状态 |
| 对初学者 | 更友好 | 更考验 Docker、端口、schema、索引理解 |

### 3.3 RAG 开发体验

| 维度 | Qdrant | Milvus |
| --- | --- | --- |
| chunk 映射 | chunk -> point | chunk -> entity |
| metadata | payload | scalar field |
| filter | JSON 结构 | boolean expression 字符串 |
| filter 索引 | payload index | scalar index |
| 返回结果 | point + payload + score | hit + entity + distance/score |
| 适配层复杂度 | 较低 | 较高 |

### 3.4 工程化

| 维度 | Qdrant | Milvus |
| --- | --- | --- |
| schema 管理 | 较灵活 | 更严格 |
| 数据校验 | 主要靠应用层和 payload 约定 | collection schema 更强 |
| 索引管理 | payload index、vector index | vector index、scalar index、更强索引体系 |
| 生产运维 | 可轻可重 | 通常更重，尤其 Distributed |
| 团队要求 | 后端团队较容易上手 | 更需要数据库/平台/运维意识 |

### 3.5 项目选择建议

| 场景 | 建议 |
| --- | --- |
| 学习 RAG | Qdrant |
| 个人作品集项目 | Qdrant |
| 小型企业知识库 | Qdrant 优先 |
| 需要强 schema 的中大型系统 | Milvus 可优先评估 |
| 明确千万到亿级向量规模 | Qdrant 集群和 Milvus 都要压测评估 |
| 亿级以上和重型企业部署 | Milvus Distributed 或托管 Milvus 值得重点评估 |
| 团队没有运维能力 | 优先轻量方案或托管服务 |
| 团队已有 Kubernetes 和数据平台 | 可以认真评估 Milvus Distributed |

## 4. 面试和项目讲解怎么说

### 4.1 如果别人问：为什么你项目先用 Qdrant

可以这样回答：

```text
我这个项目的阶段目标是先把企业知识库 RAG 主线跑通，包括文档加载、chunk 切分、embedding、入库、metadata filter、score_threshold、引用来源、无资料兜底和测试。

Qdrant 的 collection/point/vector/payload 模型更直观，本地部署和 REST 调试成本更低，适合快速形成完整闭环。当前项目数据规模也不大，不需要一开始引入更重的分布式向量数据库部署。
```

### 4.2 如果别人问：那 Milvus 你会吗

可以这样回答：

```text
会。我在项目后半段补了 Milvus 对比实现。用同一批 RAG chunk 设计了 Milvus schema，把 chunk 映射成 entity，创建 vector index 和 metadata scalar index，通过 PyMilvus 完成 upsert 和 search，并实现了 metadata filter expression 转换。

我也在本地 Docker Milvus Standalone 上验证过入库、检索和 scalar index。
```

### 4.3 如果别人问：Qdrant 和 Milvus 最大区别是什么

可以这样回答：

```text
从 RAG 应用开发视角看，Qdrant 的 point + payload 模型更轻、更直接，适合快速开发和中小型 RAG 应用。Milvus 更强调 schema、field、entity、index 和分布式能力，适合更强结构、更大规模和更重运维的场景。

两者都能做 vector search 和 metadata filter，但建模方式不同。Qdrant 是 payload filter 和 payload index，Milvus 是 scalar field、boolean expression 和 scalar index。
```

### 4.4 如果别人问：生产环境你会怎么选

可以这样回答：

```text
我不会只按工具名选择。我会先看数据规模、QPS、filter 复杂度、更新频率、部署环境、团队运维能力和上线时间。

如果是中小规模企业知识库，团队希望快速上线、低运维成本，我会优先考虑 Qdrant 或托管 Qdrant。

如果明确是大规模向量检索，团队已有 Kubernetes 和数据平台运维能力，并且需要强 schema、复杂索引和分布式扩展，我会认真评估 Milvus Distributed 或托管 Milvus。
```

### 4.5 如果别人问：为什么不直接用 LangChain vector store

可以这样回答：

```text
LangChain vector store 封装可以提高开发效率，但我先自己实现 Qdrant 和 Milvus adapter，是为了理解底层数据模型、filter、index、search result、错误处理和测试边界。

理解底层后再用 LangChain 封装，才能知道封装替我做了什么，也能在出问题时排查。
```

## 5. 本项目当前结论

当前项目继续保持：

```text
主线 vector store：Qdrant
对比和扩展 vector store：Milvus
```

这样安排更适合你的学习目标。

原因：

- Qdrant 已经承载完整 RAG 主线；
- Milvus 已经完成核心概念、部署、入库、检索、filter/index；
- 后续要进入智能工单 Agent，不应该继续停留在向量数据库横向扩展上太久；
- 你现在需要的是把 RAG 能力和 Tool Calling、Java 业务服务串起来；
- Milvus 保留为面试和生产选型对比能力。

后续如果我们要做更真实的企业级版本，可以再补：

- 用真实 embedding 重新入库；
- Qdrant payload index 创建；
- Milvus 更细的向量索引参数；
- 两边相同数据集压测；
- 检索评测集；
- 多租户和权限系统；
- Docker Compose 统一启动 AI 服务、Java 服务、向量库。

但现在先进入下一块更合理。

## 6. 练习

### 练习 1：判断项目选型

场景：

```text
你要做一个公司内部客服知识库，第一版只有 200 个 Markdown 文档，目标是 2 周内做出可演示版本。团队只有你一个人，主要会 Python 和 Java，没有 Kubernetes 经验。
```

你优先选 Qdrant 还是 Milvus？为什么？

### 练习 2：判断 Milvus 更合适的场景

场景：

```text
公司已经有数据平台团队和 Kubernetes 集群，要做亿级图片向量检索，要求多节点扩展、监控、备份、高吞吐和长期运维。
```

这时为什么 Milvus 值得重点评估？

### 练习 3：概念映射

把下面 Qdrant 概念映射成 Milvus 概念：

```text
point
payload
payload index
vector
point id
```

### 练习 4：解释 filter 差异

用自己的话解释：

```text
Qdrant filter 和 Milvus filter 最大的表达形式差异是什么？
```

### 练习 5：说出本项目当前策略

请用 3-5 句话说明：

```text
为什么本项目主线继续用 Qdrant，同时保留 Milvus 对比实现？
```

## 7. 练习参考答案

### 答案 1

优先选 Qdrant。

原因：

- 数据量小，200 个 Markdown 文档不需要复杂分布式向量数据库；
- 目标是 2 周内做演示，开发速度和排错成本更重要；
- 团队只有一个人，没有 Kubernetes 经验，应该降低运维复杂度；
- Qdrant 的 point/payload 模型更直观，本地 Docker 和 REST 调试更方便；
- 第一版先跑通 RAG 主线，后面再根据数据规模和性能瓶颈评估是否迁移。

### 答案 2

Milvus 值得重点评估，因为这个场景已经不是小型 RAG Demo，而是大规模向量检索平台。

关键原因：

- 数据规模达到亿级；
- 团队有 Kubernetes 和数据平台运维能力；
- 需要多节点扩展；
- 需要高吞吐和长期运维；
- Milvus Distributed 的架构定位适合更大规模和高负载场景；
- 强 schema、索引体系和组件化架构更适合平台级系统。

但仍然要压测，不应该只凭名称决定。

### 答案 3

映射关系：

| Qdrant | Milvus |
| --- | --- |
| point | entity |
| payload | scalar fields |
| payload index | scalar index |
| vector | vector field |
| point id | primary field |

### 答案 4

Qdrant filter 是结构化 JSON 风格，通常通过 `must`、`should`、`match`、`range` 等字段表达过滤条件。

Milvus filter 是 boolean expression 字符串风格，例如：

```text
permission_group == "customer_service" and business_domain == "refund"
```

所以 Qdrant 更像构造 API 请求体，Milvus 更像写数据库查询表达式。Milvus 表达式更紧凑，但后端要负责字段白名单、值类型校验和字符串转义。

### 答案 5

本项目当前目标是学习和完成企业知识库 RAG + 智能工单 Agent，主线应该保持推进速度和可理解性。Qdrant 已经承载了完整 RAG 主线，部署简单、模型直观，适合作为当前主线 vector store。Milvus 已经完成本地启动、schema、入库、检索、metadata filter 和 scalar index 学习，保留它可以体现我们理解了另一种更强结构、更偏大规模的向量数据库方案。当前不应该为了继续横向比较向量库而拖慢后续 Agent 主线。

## 8. 自测题

### 自测 1

Qdrant 的 `payload` 和 Milvus 的 `scalar field` 分别承担什么作用？

### 自测 2

为什么“Qdrant 简单，Milvus 强”不是一个合格的完整选型回答？

### 自测 3

如果一个项目只有几千个 chunk，团队没有运维能力，但要求一个月内上线，选型时应该优先考虑什么？

### 自测 4

为什么 Milvus 的 schema 对大型系统可能是优势？

### 自测 5

为什么我们说向量数据库选型要看“当前阶段”？

## 9. 自测题参考答案

### 自测 1 答案

Qdrant 的 `payload` 用来保存 point 的附加业务信息，例如 `content`、`source`、`permission_group`、`business_domain`，它可以用于返回展示和 filter。

Milvus 的 `scalar field` 用来保存 entity 的普通字段，例如字符串、整数、JSON 等，同样可以用于返回展示和 metadata filter。

两者都承担 RAG 里的 metadata 角色，只是数据模型表达方式不同。

### 自测 2 答案

因为这句话太粗，不能说明真实项目里的权衡。

合格选型要说明：

- 数据规模；
- 查询 QPS；
- filter 复杂度；
- 部署环境；
- 团队运维能力；
- 上线时间；
- 成本；
- 未来扩展；
- 为什么当前阶段这个选择更合适。

### 自测 3 答案

应该优先考虑：

- 部署简单；
- 开发快；
- 排错容易；
- 本地和生产路径清楚；
- 团队能长期维护；
- 成本可控。

这种场景通常优先考虑 Qdrant 或托管向量数据库，而不是一开始就上复杂分布式部署。

### 自测 4 答案

Milvus schema 能明确规定字段名、字段类型、primary key、vector field、字符串长度、向量维度等。大型系统里，数据结构清晰和约束明确有助于数据质量、接口契约、长期维护和错误提前暴露。

代价是 schema 设计和变更成本更高。

### 自测 5 答案

因为同一个项目在不同阶段关注点不同。

学习阶段重在理解、跑通和排错；生产阶段重在稳定、高可用、备份、监控和扩展；大规模阶段重在吞吐、延迟、索引和运维体系。

所以不是一开始就选最重的，也不是永远停留在最简单的，而是根据当前阶段和未来风险做匹配。

## 10. 本节小结

本节你应该形成一个清晰判断：

```text
Qdrant 和 Milvus 不是谁绝对取代谁。
它们都能做 RAG vector store，但更适合的项目阶段和工程条件不同。
```

当前学习项目建议：

```text
Qdrant 继续做主线。
Milvus 保留为对比实现和大规模向量数据库知识储备。
```

你现在已经不是只会说“我用过向量数据库”，而是应该能说：

- 我知道向量数据库在 RAG 里的职责；
- 我知道 Qdrant point/payload 和 Milvus entity/schema 的映射；
- 我知道 payload index 和 scalar index 的作用；
- 我知道 filter 不能后置到 Python；
- 我知道选型要看规模、部署、运维、schema、filter 和成本；
- 我知道当前项目为什么这样选。

下一节建议进入：

```text
阶段 4 第 37 节：RAG 检索评测是什么，为什么不能只靠感觉判断好不好
```

因为我们已经完成了 Qdrant 主线、Milvus 对比和选型判断。接下来要补的是“如何评价检索效果”，也就是让 RAG 从能跑进入可衡量。

## 11. 本节参考资料

资料核对日期：2026-07-18。

- [Qdrant Documentation Overview](https://qdrant.tech/documentation/overview/)
- [Qdrant Points](https://qdrant.tech/documentation/manage-data/points/)
- [Qdrant Search](https://qdrant.tech/documentation/search/search/)
- [Qdrant Payload Indexing](https://qdrant.tech/documentation/manage-data/indexing/)
- [Qdrant Installation](https://qdrant.tech/documentation/installation/)
- [Qdrant API & SDKs](https://qdrant.tech/documentation/interfaces/)
- [Qdrant Web UI](https://qdrant.tech/documentation/web-ui/)
- [Milvus Overview](https://milvus.io/docs/overview.md)
- [Milvus Deployment Options](https://milvus.io/docs/install-overview.md)
- [Milvus Collection Explained](https://milvus.io/docs/manage-collections.md)
- [Milvus Create Collection](https://milvus.io/docs/create-collection.md)
- [Milvus Data Model Design](https://milvus.io/docs/schema-hands-on.md)
- [Milvus Index Explained](https://milvus.io/docs/index-explained.md)
- [Milvus Main Components](https://milvus.io/docs/main_components.md)
