# 阶段 4 第 21 节：RAG 错误处理：embedding、向量库、模型调用异常

## 本节状态

已完成。

第 20 节我们学了：

```text
系统正常运行，但没有可用检索资料 -> no_context
```

第 21 节专门学习另一类情况：

```text
RAG 链路某一环真的出错了 -> error handling
```

这两类情况必须严格区分。

```text
no_context：没有资料可答。
error：系统链路失败。
```

本节的核心不是“try/except 怎么写”，而是：

```text
RAG 系统要把 embedding、向量库、模型调用这些外部依赖失败，映射成清楚、安全、可测试的应用错误。
```

## 本节学习目标

学完本节，你要能讲清楚：

1. RAG 链路里哪些环节可能失败。
2. `no_context` 和 `error` 的本质区别。
3. 为什么不能把系统异常伪装成“知识库没有资料”。
4. 为什么底层异常不能直接暴露给用户。
5. embedding 失败有哪些类型。
6. 向量库失败有哪些类型。
7. 模型调用失败当前项目已经怎么处理。
8. 为什么 RAG 层需要统一错误码。
9. 为什么输入参数错误仍然保留 `ValueError`。
10. 为什么 `retrieve_top_k()` 和 `ingest_directory_to_vector_store()` 是合适的错误映射入口。
11. 本节新增的 `RAG_EMBEDDING_FAILED`、`RAG_EMBEDDING_BAD_RESPONSE`、`RAG_VECTOR_STORE_FAILED`、`RAG_VECTOR_STORE_CONFIG_ERROR` 分别表示什么。

## 本节暂时不学什么

本节只做 RAG 内部错误分类和映射。

暂时不做：

- 不做 `/rag-chat` API。
- 不做真实 Qdrant 调用。
- 不做真实 embedding API 调用。
- 不做真实模型调用。
- 不做重试策略。
- 不做熔断、降级、缓存。
- 不做错误告警系统。
- 不做 trace 日志增强。
- 不做 UI 错误展示。

这些都会在后续工程化和性能章节继续补。

## 一、基础知识铺垫

### 1. RAG 链路为什么更容易出错

普通 LLM 聊天链路大概是：

```text
用户问题 -> 调模型 -> 返回回答
```

RAG 链路长很多：

```text
用户问题
-> query embedding
-> vector store 检索
-> payload filter / score_threshold
-> retrieved chunks
-> prompt/context 构造
-> LLM 生成回答
-> citations / no_context / answer
```

链路越长，可能出错的地方越多。

RAG 里常见失败点包括：

- 用户输入为空。
- embedding 模型超时。
- embedding 返回向量数量不对。
- embedding 向量维度不对。
- 向量库连接失败。
- 向量库返回 500。
- collection 配置和当前 embedding 维度不一致。
- Qdrant 返回 JSON 结构异常。
- 检索结果 payload 缺少 `content` 或 `chunk_id`。
- 模型 API key 没配置。
- 模型超时、限流、认证失败。
- 模型返回空内容。

这些错误不能都用一句：

```text
回答失败。
```

来糊弄过去。

你要知道是哪一环失败，才能排查和修复。

### 2. no_context 和 error 的区别

第 20 节已经学过 `no_context`。

再强调一次：

```text
no_context 是系统正常运行后的业务结果。
```

比如：

```text
用户问“公司年会抽奖规则是什么？”
知识库里没有年会文档。
检索正常返回空。
```

这不是系统坏了。

应该返回：

```text
status = no_context
```

而 error 是：

```text
系统链路某一环失败。
```

比如：

```text
Qdrant 服务连不上。
embedding API 超时。
模型 API 返回 500。
```

这不是知识库没资料。

应该返回对应错误码。

可以这样记：

| 类型 | 系统是否正常运行 | 是否有可用资料 | 结果 |
| --- | --- | --- | --- |
| answered | 正常 | 有 | 回答 |
| no_context | 正常 | 没有 | 兜底 |
| error | 不正常 | 不确定 | 错误 |

### 3. 为什么不能把系统异常伪装成 no_context

假设 Qdrant 挂了。

错误做法：

```text
返回 no_context：当前知识库没有找到相关资料。
```

这非常危险。

因为真实情况不是知识库没资料，而是向量库服务不可用。

这样会带来几个问题：

1. 用户误以为知识库没有这方面内容。
2. 业务人员可能重复补文档，但真正问题是服务挂了。
3. 开发者监控不到故障。
4. 线上问题被隐藏。
5. 评测数据被污染。

正确做法是：

```text
返回 RAG_VECTOR_STORE_FAILED。
```

这告诉系统：

```text
不是资料不足，而是向量库调用失败。
```

所以一定要记住：

```text
no_context 不能吞掉系统异常。
```

### 4. 为什么底层异常不能直接暴露给用户

Qdrant 可能抛出：

```text
ConnectError: [WinError 10061] 由于目标计算机积极拒绝，无法连接。
```

embedding 服务可能返回：

```text
Connection reset by peer
```

模型服务可能返回：

```text
401 invalid_api_key
```

这些底层信息不适合直接给用户看。

原因：

- 太技术化，用户看不懂。
- 可能暴露内部服务地址。
- 可能暴露第三方供应商细节。
- 可能暴露配置问题。
- 不利于前端稳定处理。

所以后端应该映射成安全的应用错误：

```json
{
  "code": "RAG_VECTOR_STORE_FAILED",
  "message": "RAG 向量库调用失败，请稍后重试。"
}
```

底层异常留在日志里，用户看到统一、安全、可理解的信息。

### 5. 什么是错误映射

错误映射就是：

```text
把底层异常转换成项目统一异常。
```

例如：

```text
QdrantVectorStoreError -> RAG_VECTOR_STORE_FAILED
QdrantCollectionConfigError -> RAG_VECTOR_STORE_CONFIG_ERROR
RuntimeError from embedding provider -> RAG_EMBEDDING_FAILED
ValueError from embedding shape validation -> RAG_EMBEDDING_BAD_RESPONSE
```

映射后，API 层或调用方就不用关心底层到底是 `httpx.ConnectError`、`QdrantVectorStoreError` 还是某个 SDK 的异常。

它只需要处理统一的 `AppException`。

这就是项目统一异常体系的价值。

### 6. embedding 失败分几类

embedding 阶段可能失败很多种。

第一类是 provider 调用失败。

例如：

- embedding API 超时。
- 网络连接失败。
- 第三方服务 500。
- rate limit。
- SDK 抛 RuntimeError。

这类可以映射为：

```text
RAG_EMBEDDING_FAILED
```

第二类是 embedding 返回结构异常。

例如：

- 输入 1 条文本，却返回 0 个向量。
- 返回 2 个向量。
- 向量维度不是模型声明的维度。
- 向量为空。

这类不是“没资料”，也不是“用户问题为空”。

它表示 embedding 结果不可信，映射为：

```text
RAG_EMBEDDING_BAD_RESPONSE
```

第三类是用户输入错误。

比如：

```text
query = "   "
```

这类仍然是 `ValueError`，因为它是调用方传错参数，不是外部依赖失败。

### 7. 向量库失败分几类

向量库阶段也有不同错误。

第一类是调用失败：

- Qdrant 连接失败。
- 请求超时。
- Qdrant 返回 500。
- Qdrant 返回非 `ok` 状态。
- Qdrant 返回非法 JSON。

这些映射为：

```text
RAG_VECTOR_STORE_FAILED
```

第二类是 collection 配置不匹配：

- 当前 embedding 维度是 8。
- Qdrant collection 已经存在，维度是 1536。
- 或距离函数不匹配。

这不是临时网络波动，而是部署或配置问题。

所以映射为：

```text
RAG_VECTOR_STORE_CONFIG_ERROR
```

状态码也更偏服务端配置错误。

### 8. 模型调用失败当前已经怎么处理

第 18 节的 `RagAnswerService.generate_answer()` 里已经复用了 LLM 层错误处理：

```text
map_openai_error_to_app_exception()
```

它会把模型相关错误映射成：

- `LLM_TIMEOUT`
- `LLM_RATE_LIMITED`
- `LLM_AUTH_FAILED`
- `LLM_BAD_REQUEST`
- `LLM_SERVER_ERROR`
- `LLM_CALL_FAILED`

所以第 21 节没有重复造一套模型错误码。

这里要理解一个边界：

```text
embedding 和 vector store 是 RAG 特有链路。
LLM 调用错误已经在 LLM service 层有统一映射。
```

所以本节主要补 RAG 检索和入库阶段的错误映射。

### 9. 为什么输入参数错误仍然保留 ValueError

不是所有错误都应该变成 `AppException`。

比如：

```text
query 为空
top_k <= 0
score_threshold 不是数字
```

这些更像是调用方代码传错参数，属于编程错误或请求校验错误。

在当前内部函数层，保留 `ValueError` 更直接。

等以后接 HTTP API 时，请求模型和 FastAPI/Pydantic 会负责把用户请求错误变成 422 或统一校验错误。

所以本节只映射：

```text
外部依赖失败
外部依赖返回结构异常
RAG 基础设施配置错误
```

### 10. 为什么在 retriever 和 ingestion 做映射

`retrieve_top_k()` 是查询链路入口。

它会调用：

```text
embedding_model.embed_texts()
vector_store.query_similar()
```

所以它适合把：

- embedding 失败。
- vector store 查询失败。

映射成 RAG 应用错误。

`ingest_directory_to_vector_store()` 是入库链路入口。

它会调用：

```text
embed_chunks()
vector_store.ensure_collection()
vector_store.upsert_embedded_chunks()
```

所以它适合把：

- 入库 embedding 失败。
- collection 配置错误。
- upsert 失败。

映射成 RAG 应用错误。

这比在最底层每个小函数里都转换异常更清楚。

### 11. 错误码为什么要稳定

错误码是给程序和排查流程看的。

比如：

```text
RAG_VECTOR_STORE_FAILED
```

未来前端、日志、监控、告警、评测都可能依赖它。

如果今天叫：

```text
VECTOR_DB_ERROR
```

明天改成：

```text
QDRANT_FAILED
```

后天又改成：

```text
RAG_DB_DOWN
```

调用方会很难处理。

所以错误码设计要尽量稳定、清楚、不过度具体。

本节选择 `RAG_VECTOR_STORE_FAILED`，而不是 `QDRANT_FAILED`，是因为未来可能换 Milvus。

RAG 层错误码不应该过早绑定某个具体向量库品牌。

### 12. 用户可见信息和日志信息要分开

错误响应里的 `message` 应该安全、简洁。

日志里可以记录更详细的底层异常、耗时、服务名、trace_id。

本节先做错误码和安全 message。

后续工程化会继续补日志和 trace。

你要记住：

```text
用户需要知道现在无法完成请求。
开发者需要知道哪一环坏了。
两者看到的信息不一定一样。
```

### 13. RAG 错误处理要分层

学习错误处理时，最容易犯的错误是：

```text
看到异常就 try/except。
```

但工程里真正重要的是分层。

RAG 错误大致可以分成 5 层：

| 层级 | 例子 | 当前处理方式 |
| --- | --- | --- |
| 输入参数错误 | query 为空、top_k <= 0 | `ValueError` |
| 业务状态 | 没有可用 chunks | `status=no_context` |
| 外部依赖调用失败 | embedding API 超时、Qdrant 连接失败 | `RAG_EMBEDDING_FAILED`、`RAG_VECTOR_STORE_FAILED` |
| 外部依赖返回结构异常 | 向量数量不对、payload 缺字段 | `RAG_EMBEDDING_BAD_RESPONSE`、`RAG_VECTOR_STORE_FAILED` |
| 系统配置错误 | collection 维度不匹配 | `RAG_VECTOR_STORE_CONFIG_ERROR` |

这 5 层不能混。

如果混了，后果很直接：

- 用户输入错误会被误判成服务故障。
- 无资料会被误判成系统异常。
- Qdrant 挂了会被误判成知识库没内容。
- collection 配错会被误判成临时上游波动。

所以错误处理不是“多写几个 except”，而是：

```text
先判断错误属于哪一层，再决定它应该如何表达。
```

### 14. RAG 错误的传播路径

一个错误从底层发生，到最终被用户或前端看到，中间会经过多层。

以向量库连接失败为例：

```text
httpx.ConnectError
-> QdrantVectorStoreError
-> rag_vector_store_failed()
-> AppException(code="RAG_VECTOR_STORE_FAILED")
-> FastAPI 统一异常处理
-> ErrorResponse
```

这条路径说明了每层职责：

| 层 | 职责 |
| --- | --- |
| `httpx` | 告诉你 HTTP 连接失败 |
| `QdrantVectorStore` | 把 HTTP 失败变成向量库适配层错误 |
| `app/rag/errors.py` | 把向量库错误变成 RAG 应用错误 |
| 统一异常处理 | 把 `AppException` 变成统一 HTTP 响应 |
| 前端/调用方 | 根据错误码决定展示和后续动作 |

这样做的好处是：

```text
底层可以变化，但上层看到的错误语义稳定。
```

比如以后从 Qdrant 换成 Milvus，底层异常可能完全不同，但 RAG 层仍然可以继续返回：

```text
RAG_VECTOR_STORE_FAILED
```

### 15. 为什么错误码不是给人看的文案

错误码和错误文案是两种东西。

错误码：

```text
RAG_VECTOR_STORE_FAILED
```

是给程序、日志、监控、测试、前端判断用的。

错误文案：

```text
RAG 向量库调用失败，请稍后重试。
```

是给人读的。

它们不要混用。

错误码应该稳定，不要频繁改。

错误文案可以根据产品语气优化。

如果前端根据中文文案判断：

```text
只要 message 包含“向量库”就显示某个 UI
```

这很脆弱。

正确方式应该是：

```text
if code == "RAG_VECTOR_STORE_FAILED":
    显示 RAG 检索服务暂不可用
```

这和第 20 节的 `status` 很像：

```text
机器判断靠稳定字段。
人类阅读靠文案。
```

### 16. 错误处理和安全的关系

错误处理也属于安全边界。

如果你把底层错误直接返回，可能泄露：

- 内网服务地址。
- 端口号。
- collection 名称。
- 第三方供应商。
- API key 配置状态。
- 数据库结构。
- 文件路径。

比如直接返回：

```text
ConnectError: connect to http://192.168.88.10:6333 failed
```

用户就知道你的向量库地址和端口。

这在学习环境里看起来无所谓，但生产环境要避免。

所以错误响应要安全：

```text
RAG_VECTOR_STORE_FAILED
RAG 向量库调用失败，请稍后重试。
```

详细排查信息应该去日志里看，而且日志也要注意脱敏。

### 17. 错误处理和测试的关系

错误处理如果没有测试，很容易退化。

比如你今天设计了：

```text
QdrantVectorStoreError -> RAG_VECTOR_STORE_FAILED
```

以后某次重构，有人直接让 `QdrantVectorStoreError` 冒到 API 层。

如果没有测试，可能上线后才发现错误响应不统一。

所以错误处理测试至少要覆盖：

- 底层异常是否被映射。
- 已经是 `AppException` 的错误是否被重复包装。
- 错误码是否符合预期。
- 关键链路是否真的抛出 `AppException`。
- 不该被映射的输入错误是否仍保留。

本节新增 `tests/test_rag_errors.py` 就是为了保护这些规则。

### 18. 错误处理和监控的关系

错误码以后会进入监控。

比如可以统计：

```text
RAG_EMBEDDING_FAILED 1 小时内出现 50 次
RAG_VECTOR_STORE_FAILED 1 小时内出现 200 次
RAG_VECTOR_STORE_CONFIG_ERROR 出现 1 次
```

这些数字代表的问题不同。

`RAG_EMBEDDING_FAILED` 激增，可能是 embedding 服务不稳定。

`RAG_VECTOR_STORE_FAILED` 激增，可能是 Qdrant/Milvus 服务不可用。

`RAG_VECTOR_STORE_CONFIG_ERROR` 出现 1 次就值得重视，因为它通常不是临时波动，而是配置错了。

所以错误码不是为了让代码“好看”，它是后续可观测性的基础。

### 19. 错误处理和用户体验的关系

不同错误要给用户不同体验。

`no_context`：

```text
可以提示用户换问法、补充关键词、反馈知识缺口。
```

`RAG_VECTOR_STORE_FAILED`：

```text
应该提示服务暂时不可用，稍后重试或转人工。
```

`RAG_VECTOR_STORE_CONFIG_ERROR`：

```text
普通用户不需要知道维度不匹配，应该显示通用服务异常。
开发者需要在日志和告警里看到配置错误。
```

`LLM_RATE_LIMITED`：

```text
可以提示请求过多，稍后再试。
```

所以错误分类会影响产品体验。

如果所有情况都返回：

```text
抱歉，暂时无法回答。
```

用户体验会很模糊，开发排查也困难。

### 20. 本节为什么不做 retry

你可能会问：

```text
既然 embedding 和向量库可能失败，为什么本节不加重试？
```

因为重试是另一个主题。

重试要考虑：

- 哪些错误值得重试。
- 重试几次。
- 每次间隔多久。
- 是否指数退避。
- 是否会放大流量。
- 是否会造成重复写入。
- 请求是否幂等。
- 用户等待时间是否过长。

比如查询向量库失败可以考虑短重试。

但入库 upsert 重试就要考虑是否幂等。

模型限流也不能简单快速重试，否则可能更严重。

所以本节先把错误分类和错误映射做好。

后面工程化阶段再学 retry、timeout、降级、缓存、熔断。

## 二、本节主题系统讲解

### 1. 第 21 节在 RAG 主线里的位置

前面几节已经形成：

```text
retrieve
-> generate
-> citations
-> no_context
```

第 21 节补的是：

```text
如果 retrieve / ingest / generate 的基础设施失败，应该如何表达错误。
```

当前重点是：

```text
embedding
vector store
model call
```

模型调用错误已有基础，所以本节主要实现：

```text
embedding error mapping
vector store error mapping
```

### 2. 新增 `app/rag/errors.py`

本节新增：

```text
projects/ai-service/app/rag/errors.py
```

它集中放 RAG 错误映射函数。

当前包含：

```python
rag_embedding_failed(exc)
rag_embedding_bad_response()
rag_vector_store_failed(exc)
```

为什么单独建文件？

因为 RAG 错误会越来越多。

以后可能还有：

- loader 错误。
- parser 错误。
- rerank 错误。
- document update 错误。
- permission 错误。

集中放在 `errors.py`，比散在各个模块里更容易维护。

### 3. `rag_embedding_failed()` 做什么

它把 embedding 阶段异常转成 `AppException`。

规则：

```text
如果已经是 AppException -> 原样返回
如果是 ValueError -> RAG_EMBEDDING_BAD_RESPONSE
其他异常 -> RAG_EMBEDDING_FAILED
```

为什么 `ValueError` 在这里表示 bad response？

因为 `embed_chunks()` 和 `retrieve_top_k()` 里会检查：

- embedding 返回数量是否对。
- vector 维度是否对。

这些检查失败说明 embedding 返回结果不符合约定。

所以映射成：

```text
RAG_EMBEDDING_BAD_RESPONSE
```

### 4. `rag_vector_store_failed()` 做什么

它把向量库阶段异常转成 `AppException`。

规则：

```text
如果已经是 AppException -> 原样返回
如果是 QdrantCollectionConfigError -> RAG_VECTOR_STORE_CONFIG_ERROR
如果是 QdrantVectorStoreError -> RAG_VECTOR_STORE_FAILED
其他异常 -> RAG_VECTOR_STORE_FAILED
```

这里保留了一个重要区分：

```text
collection 配置不匹配 != 临时调用失败
```

collection 配置不匹配通常需要开发者修配置或重建 collection。

普通调用失败可能是网络、Qdrant 服务、响应异常等。

### 5. 修改 `retrieve_top_k()`

第 21 节后，查询链路变成：

```text
校验 query/top_k/score_threshold
-> 调 embedding_model.embed_texts()
   - provider 异常 -> RAG_EMBEDDING_FAILED
   - 返回数量/维度异常 -> RAG_EMBEDDING_BAD_RESPONSE
-> 调 vector_store.query_similar()
   - 向量库异常 -> RAG_VECTOR_STORE_FAILED
-> 返回 RetrievedChunk 列表
```

这里仍然保留：

```text
空 query -> ValueError
top_k <= 0 -> ValueError
score_threshold 类型错误 -> ValueError
```

因为这些是调用参数问题，不是外部依赖失败。

### 6. 修改 `ingest_directory_to_vector_store()`

入库链路变成：

```text
load documents
-> split chunks
-> embed_chunks()
   - embedding 异常 -> RAG_EMBEDDING_FAILED / BAD_RESPONSE
-> ensure_collection()
   - collection 配置异常 -> RAG_VECTOR_STORE_CONFIG_ERROR
-> upsert_embedded_chunks()
   - upsert 异常 -> RAG_VECTOR_STORE_FAILED
-> RagIngestionResult
```

为什么入库也要处理？

因为 RAG 不只有用户问答，还有知识入库。

如果入库失败，知识库可能根本没有被正确写入。

这会影响后续检索。

### 7. 本节没有改 `generate_answer()` 的原因

`generate_answer()` 已经有模型调用错误处理：

```python
except Exception as exc:
    app_exception = map_openai_error_to_app_exception(exc)
```

并且会记录：

```text
rag_answer_failed code=...
```

所以第 21 节不重复改它。

你要能说清楚：

```text
RAG 生成阶段的模型调用错误复用 LLM 层统一错误映射。
本节补的是 RAG 特有的 embedding 和 vector store 错误。
```

### 8. 新增测试保护什么

本节新增：

```text
tests/test_rag_errors.py
```

测试错误映射函数。

还修改：

```text
tests/test_rag_retriever.py
tests/test_rag_ingestion.py
```

测试真实链路里会抛出对应 `AppException`。

重点保护：

- embedding provider 异常 -> `RAG_EMBEDDING_FAILED`
- embedding 结果数量/维度异常 -> `RAG_EMBEDDING_BAD_RESPONSE`
- Qdrant 调用异常 -> `RAG_VECTOR_STORE_FAILED`
- collection 配置不匹配 -> `RAG_VECTOR_STORE_CONFIG_ERROR`
- 已经是 `AppException` 的错误不被重复包装

### 9. 第 21 节后当前 RAG 状态分类

现在 RAG 回答链路可以这样分类：

```text
有 chunks，模型成功 -> answered
没有 chunks，系统正常 -> no_context
embedding 失败 -> RAG_EMBEDDING_FAILED / BAD_RESPONSE
向量库失败 -> RAG_VECTOR_STORE_FAILED / CONFIG_ERROR
模型失败 -> LLM_* 错误
```

这就是一个更完整的工程状态图。

### 10. 一次查询失败的完整决策树

当用户发起一次 RAG 查询，可以按下面的决策树理解：

```text
query 是否为空？
-> 是：输入参数错误
-> 否：生成 query embedding

embedding 是否成功？
-> 否：RAG_EMBEDDING_FAILED 或 RAG_EMBEDDING_BAD_RESPONSE
-> 是：调用 vector store

vector store 是否成功？
-> 否：RAG_VECTOR_STORE_FAILED 或 RAG_VECTOR_STORE_CONFIG_ERROR
-> 是：得到 chunks

chunks 是否为空？
-> 是：no_context
-> 否：调用模型生成 answer

模型是否成功？
-> 否：LLM_* 错误
-> 是：answered + citations
```

这张图非常重要。

它把前面几节串起来了：

- 第 17 节：score_threshold 可能让 chunks 为空。
- 第 18 节：有 chunks 时调用模型生成回答。
- 第 19 节：有回答时返回 citations。
- 第 20 节：chunks 为空时返回 no_context。
- 第 21 节：embedding、vector store、model 失败时返回 error。

你以后排查 RAG 问题时，可以按这个顺序问：

```text
是输入问题？
是 embedding 问题？
是向量库问题？
是无资料？
是模型问题？
```

### 11. 一次入库失败的完整决策树

入库链路也有自己的错误路径：

```text
读取文档
-> 切 chunk
-> 生成 chunk embeddings
-> ensure collection
-> upsert points
```

本节主要覆盖后面三步。

决策树可以这样理解：

```text
embedding 是否成功？
-> 否：RAG_EMBEDDING_FAILED 或 RAG_EMBEDDING_BAD_RESPONSE
-> 是：检查 collection

collection 是否匹配？
-> 否：RAG_VECTOR_STORE_CONFIG_ERROR
-> 是：写入 points

upsert 是否成功？
-> 否：RAG_VECTOR_STORE_FAILED
-> 是：返回 RagIngestionResult
```

为什么入库错误也重要？

因为如果入库失败，后面查询可能表现成：

```text
no_context
```

但根本原因其实是：

```text
文档没有成功写进向量库。
```

所以生产 RAG 不能只关注问答接口，也要关注入库链路是否稳定。

### 12. 本节错误码和 HTTP 状态码的关系

当前 `AppException` 包含：

```text
code
message
status_code
```

本节错误大致分成两类状态码。

`502`：

```text
RAG_EMBEDDING_FAILED
RAG_EMBEDDING_BAD_RESPONSE
RAG_VECTOR_STORE_FAILED
```

为什么多是 502？

因为这些错误通常表示当前服务依赖的外部组件失败或返回不符合预期。

可以理解成：

```text
AI 服务本身收到请求了，但它依赖的 embedding/vector store 没有可靠完成工作。
```

`500`：

```text
RAG_VECTOR_STORE_CONFIG_ERROR
```

为什么是 500？

因为 collection 配置不匹配更像服务端自身配置问题。

这不是用户请求能解决的，也不一定是临时上游波动。

### 13. 为什么 `RAG_EMBEDDING_BAD_RESPONSE` 不是 `RAG_EMBEDDING_FAILED`

这两个错误很像，但语义不同。

`RAG_EMBEDDING_FAILED` 表示：

```text
embedding 调用没有正常完成。
```

比如超时、网络失败、provider 抛异常。

`RAG_EMBEDDING_BAD_RESPONSE` 表示：

```text
embedding 调用完成了，但返回结果不符合契约。
```

比如输入 1 条文本却返回 0 个向量，或者维度不对。

为什么要区分？

因为排查方向不同。

调用失败可能看服务可用性、网络、限流。

返回结构异常要看 SDK 适配、模型配置、维度配置、批量请求解析。

### 14. 为什么 `RAG_VECTOR_STORE_CONFIG_ERROR` 要单独存在

假设当前 embedding 模型维度是 8。

但 Qdrant collection 已经存在，维度是 1536。

如果你把它归为：

```text
RAG_VECTOR_STORE_FAILED
```

就会像一个普通向量库调用失败。

但真实问题是：

```text
collection schema 和当前 embedding 配置不一致。
```

这种错误重试多少次都没用。

需要做的是：

- 确认当前 embedding 模型维度。
- 确认 collection 配置。
- 决定是否删除重建 collection。
- 或者新建另一个 collection。
- 或者迁移旧数据。

所以它要有单独错误码。

### 15. 本节代码和后续 API 的关系

虽然本节没有做 `/rag-chat` API，但现在已经为 API 打了基础。

未来 API 可以这样处理：

```text
try:
    chunks = retrieve_top_k(...)
    result = generate_answer_with_citations(...)
    return result
except AppException as exc:
    交给统一异常处理
```

因为 `retrieve_top_k()` 已经能抛出稳定 RAG 错误，`generate_answer_with_citations()` 已经能返回 `answered/no_context`，API 层就不需要知道太多底层细节。

这就是提前做错误映射的价值：

```text
后续接口层会更薄、更清楚。
```

## 三、本节代码改动说明

### 1. 新增 `app/rag/errors.py`

这个文件集中处理 RAG 错误映射。

学习重点：

```text
不要让 httpx、Qdrant、embedding SDK 的底层异常直接散落到业务层。
```

### 2. 修改 `app/rag/retriever.py`

新增错误映射：

- embedding 调用异常。
- embedding 返回数量不对。
- embedding 返回维度不对。
- vector store 查询异常。

查询参数错误仍然保留 `ValueError`。

### 3. 修改 `app/rag/ingestion.py`

新增错误映射：

- `embed_chunks()` 失败。
- `ensure_collection()` 失败。
- `upsert_embedded_chunks()` 失败。

入库链路现在也能返回统一 RAG 错误。

### 4. 新增和更新测试

新增：

- `projects/ai-service/tests/test_rag_errors.py`

修改：

- `projects/ai-service/tests/test_rag_retriever.py`
- `projects/ai-service/tests/test_rag_ingestion.py`

## 四、常见误区

### 误区 1：RAG 没回答出来都算 no_context

不对。

只有系统正常运行但没有可用资料时，才是 no_context。

embedding、向量库、模型调用失败都是 error。

### 误区 2：底层异常直接返回给用户更真实

不对。

底层异常可能泄露内部信息，也不利于前端稳定处理。应该映射成安全、稳定的应用错误码。

### 误区 3：所有异常都转成一个 RAG_FAILED

太粗。

至少要区分 embedding、vector store、model call。否则排查困难。

### 误区 4：错误码越具体越好

也不对。

过度具体会绑定底层实现。比如 `QDRANT_CONNECT_ERROR` 未来换 Milvus 就尴尬。RAG 层错误码要既能定位大类，又不过度绑定供应商。

### 误区 5：参数错误也应该映射成 RAG 错误

当前不需要。

空 query、非法 top_k 是调用方输入问题，保留 `ValueError` 更清楚。接 HTTP API 时再由请求校验处理。

## 五、本节练习

### 练习 1：区分 no_context 和 error

题目：

下面哪些是 no_context？哪些是 error？

```text
A. 用户问的问题不在知识库范围内，检索正常返回空
B. Qdrant 连接失败
C. embedding API 超时
D. 检索结果都低于 score_threshold
E. 模型 API 返回 500
```

参考答案：

A、D 是 no_context。B、C、E 是 error。

### 练习 2：解释为什么不能把 Qdrant 失败当无资料

题目：

为什么 Qdrant 连接失败时不能返回 `status=no_context`？

参考答案：

因为真实情况不是知识库没有资料，而是向量库服务不可用。如果返回 no_context，会误导用户、污染评测数据，并隐藏线上故障。应该返回 `RAG_VECTOR_STORE_FAILED`。

### 练习 3：设计错误码

题目：

如果 embedding 返回的向量维度不等于模型声明维度，应该用哪个错误码？

参考答案：

应该用 `RAG_EMBEDDING_BAD_RESPONSE`。因为这是 embedding 返回结果结构异常，不是普通无资料，也不是向量库问题。

### 练习 4：解释为什么 `RAG_VECTOR_STORE_CONFIG_ERROR` 是 500

题目：

为什么 collection 维度和当前 embedding 维度不一致更像 500，而不是 502？

参考答案：

因为这通常是服务端配置或部署问题，需要开发者修复 collection 或 embedding 配置，不是临时上游服务失败。它属于当前系统配置不一致。

### 练习 5：说明模型错误为什么本节没重复实现

题目：

为什么第 21 节没有重新写一套模型调用错误码？

参考答案：

因为项目在 LLM service 层已经有 `map_openai_error_to_app_exception()`，能把模型超时、限流、认证失败、服务端错误等映射成统一 `LLM_*` 错误。RAG 生成阶段复用这套能力即可。

### 练习 6：画出查询错误决策树

题目：

请用文字写出一次 RAG 查询从 query 到 answer 之间可能出现的状态分支。

参考答案：

可以这样写：

```text
query 为空 -> 输入错误
embedding 失败 -> RAG_EMBEDDING_FAILED / BAD_RESPONSE
vector store 失败 -> RAG_VECTOR_STORE_FAILED / CONFIG_ERROR
chunks 为空 -> no_context
模型调用失败 -> LLM_* 错误
模型成功 -> answered + citations
```

### 练习 7：区分调用失败和坏响应

题目：

embedding API 成功返回 HTTP 200，但返回了 0 个向量。它应该是 `RAG_EMBEDDING_FAILED` 还是 `RAG_EMBEDDING_BAD_RESPONSE`？为什么？

参考答案：

应该是 `RAG_EMBEDDING_BAD_RESPONSE`。因为调用已经完成，但返回结构不符合契约：输入文本数量和返回向量数量不一致。

### 练习 8：说明为什么配置错误不适合重试

题目：

为什么 collection 维度不匹配时，不应该靠 retry 解决？

参考答案：

因为维度不匹配是配置或 schema 问题，不是临时网络波动。重复请求不会改变 collection 的维度，必须由开发者修配置、重建 collection 或迁移数据。

## 六、自测问题

### 自测 1

问题：

`RAG_VECTOR_STORE_FAILED` 和 `no_context` 的区别是什么？

答案：

`RAG_VECTOR_STORE_FAILED` 表示向量库调用失败，系统链路异常。`no_context` 表示系统正常运行但没有可用检索资料。

### 自测 2

问题：

embedding 返回数量不等于输入数量，属于什么错误？

答案：

属于 `RAG_EMBEDDING_BAD_RESPONSE`。

### 自测 3

问题：

为什么 RAG 层错误码不直接叫 `QDRANT_FAILED`？

答案：

因为 RAG 层不应该过早绑定某个具体向量库。未来可能换 Milvus，所以用 `RAG_VECTOR_STORE_FAILED` 更稳定。

### 自测 4

问题：

空 query 应该映射成 `RAG_EMBEDDING_FAILED` 吗？

答案：

不应该。空 query 是输入参数问题，当前内部函数保留 `ValueError`。

### 自测 5

问题：

`QdrantCollectionConfigError` 映射成什么？

答案：

映射成 `RAG_VECTOR_STORE_CONFIG_ERROR`。

### 自测 6

问题：

模型调用失败当前由谁负责映射？

答案：

由 LLM service 的 `map_openai_error_to_app_exception()` 负责映射，RAG generator 复用它。

### 自测 7

问题：

为什么错误信息不能直接暴露底层异常？

答案：

因为底层异常可能太技术化、暴露内部服务信息或供应商细节，也不利于前端稳定处理。

### 自测 8

问题：

`retrieve_top_k()` 现在会映射哪两类外部失败？

答案：

embedding 失败和 vector store 查询失败。

### 自测 9

问题：

错误码和错误文案分别给谁用？

答案：

错误码主要给程序、前端判断、日志、监控和测试使用；错误文案主要给人阅读。

### 自测 10

问题：

为什么本节不做 retry？

答案：

因为 retry 涉及错误是否可重试、重试次数、间隔、幂等性、成本和延迟等问题。本节先做错误分类和映射，retry 属于后续工程化内容。

### 自测 11

问题：

向量库连接失败从底层到上层大概会经历哪些错误层？

答案：

大致是 `httpx.ConnectError -> QdrantVectorStoreError -> rag_vector_store_failed() -> AppException(code="RAG_VECTOR_STORE_FAILED") -> 统一异常响应`。

### 自测 12

问题：

为什么入库链路也要做错误处理？

答案：

因为如果入库失败，知识文档没有正确写入向量库，后续查询可能表现为 no_context。只有入库链路也有清楚错误，才能排查知识库为什么没有可检索内容。

## 七、你应该能口述出的版本

你可以这样向别人解释本节：

```text
第 21 节讲 RAG 错误处理。它和第 20 节的 no_context 不一样：no_context 是系统正常运行但没找到可用资料，error 是 RAG 链路某一环失败。

RAG 链路比普通聊天更长，embedding、向量库、模型调用都可能失败。不能把 Qdrant 挂了伪装成知识库没资料，也不能把底层异常直接暴露给用户。

本节新增 app/rag/errors.py，把 embedding 失败映射成 RAG_EMBEDDING_FAILED 或 RAG_EMBEDDING_BAD_RESPONSE，把向量库失败映射成 RAG_VECTOR_STORE_FAILED，把 collection 配置不一致映射成 RAG_VECTOR_STORE_CONFIG_ERROR。

retrieve_top_k 现在会捕获 embedding 和 vector store 失败并抛出统一 AppException。ingest_directory_to_vector_store 也会把入库过程里的 embedding、collection、upsert 失败映射成 RAG 错误。模型调用错误已经由 LLM service 统一处理，所以本节不重复造一套模型错误码。

这一节还要记住错误处理的分层：输入错误保留 ValueError，无资料是 no_context，外部依赖失败是 RAG_* 或 LLM_* 错误，配置不一致要单独报 RAG_VECTOR_STORE_CONFIG_ERROR。错误码给程序和监控使用，错误文案给人看；底层异常留给日志，不直接暴露给用户。
```

## 八、本节产出

新增：

- `projects/ai-service/app/rag/errors.py`
- `projects/ai-service/tests/test_rag_errors.py`
- `notes/rag-stage4-21-error-handling.md`

修改：

- `projects/ai-service/app/rag/retriever.py`
- `projects/ai-service/app/rag/ingestion.py`
- `projects/ai-service/tests/test_rag_retriever.py`
- `projects/ai-service/tests/test_rag_ingestion.py`
- `README.md`
- `docs/learning-progress.md`
- `docs/learning-resources.md`
- `projects/ai-service/README.md`
- `projects/ai-service/app/rag/README.md`

## 九、参考资料

- [阶段 4 第 20 节：无检索结果时怎么处理](rag-stage4-20-no-context-handling.md)
- [阶段 4 第 18 节：把检索结果交给模型回答](rag-stage4-18-retrieved-context-to-model-answer.md)
- [阶段 2 第 11 节：模型调用错误处理](llm-api-stage2-11-model-error-handling.md)
- [阶段 1 第 14 节：统一异常处理](fastapi-stage1-14-exception-handling.md)
