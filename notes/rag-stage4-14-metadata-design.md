# 阶段 4 第 14 节：metadata 设计：source、title、section、权限字段

## 本节状态说明

本节已完成。

本节对应代码：

- `projects/ai-service/app/rag/metadata.py`
- `projects/ai-service/app/rag/loaders.py`
- `projects/ai-service/app/rag/splitters.py`
- `projects/ai-service/app/rag/vector_store.py`
- `projects/ai-service/tests/test_rag_metadata.py`
- `projects/ai-service/tests/test_rag_vector_store.py`

本节接在第 13 节后面：

```text
第 13 节：chunk + vector + payload 写进 Qdrant
第 14 节：认真设计 payload 里的 metadata
```

## 本节一句话定位

本节解决的问题是：**RAG 检索出来的不应该只是一段文本，还应该知道这段文本来自哪里、属于什么业务、用户有没有权限看、以后能不能展示出处。**

第 13 节我们已经把 chunk 写进 Qdrant。那时 payload 里保存了 content 和 metadata。本节要做的是：把 metadata 从“随便放几个字段”升级成“有字段规则、有必备字段、有类型约束、有 payload 白名单”的工程化设计。

## 本节学习目标

学完本节，你应该能说清楚：

1. metadata 是什么，为什么 RAG 不能只存 content。
2. metadata、payload、vector、content 的关系。
3. document-level metadata 和 chunk-level metadata 的区别。
4. `source`、`title`、`section` 分别负责什么。
5. `doc_type`、`business_domain`、`permission_group` 分别解决什么问题。
6. 为什么权限字段必须在入库阶段就保留下来。
7. 为什么 metadata 字段要命名稳定、类型稳定。
8. 什么是必备字段，什么是可选字段。
9. 为什么 Qdrant payload 需要白名单。
10. 本节新增的 `metadata.py` 如何保护后续检索和权限过滤。

## 本节暂时不学什么

本节暂时不做这些事：

- 不做 top_k 检索。
- 不做 payload filter 查询。
- 不做真实用户权限系统。
- 不做引用来源展示接口。
- 不做文档删除和重新入库。
- 不重新跑 Qdrant 实机入库作为必需步骤。

原因很简单：metadata 是后续这些能力的基础。先把字段设计清楚，再学检索和过滤，后面会顺很多。

## 基础知识铺垫：metadata 是什么

metadata 可以翻译成“元数据”。

元数据不是正文内容，而是描述正文内容的数据。

比如一段正文是：

```text
订单付款成功后，仓库会在 24 小时内处理发货。
```

它的 metadata 可能是：

```json
{
  "source": "order-shipping-policy.md",
  "title": "订单发货规则",
  "section": "正常发货时效",
  "doc_type": "policy",
  "business_domain": "order",
  "permission_group": "customer_service"
}
```

正文回答“内容是什么”。

metadata 回答：

- 这段内容来自哪个文件？
- 属于哪篇文档？
- 属于哪个章节？
- 是政策文档还是 FAQ？
- 是订单业务还是退款业务？
- 哪类用户有权限看到？

所以 metadata 不是可有可无的备注，它是 RAG 工程里非常关键的数据结构。

## content、vector、metadata、payload 的关系

第 13 节我们已经见过 Qdrant point：

```text
point = id + vector + payload
```

再细一点：

```text
payload = content + metadata
```

所以完整关系是：

```text
content：原文片段，给大模型读
vector：原文片段的向量，用来检索相似内容
metadata：描述原文片段的结构化信息
payload：Qdrant 里保存 content 和 metadata 的地方
```

可以用一个简单类比：

```text
content 像书里的正文段落
vector 像图书馆系统用来找相似内容的内部编码
metadata 像图书卡片上的书名、作者、分类、位置、访问权限
payload 像把正文和卡片信息一起装进数据库记录
```

没有 vector，向量库没法按语义找相似内容。

没有 content，大模型最后没有上下文可读。

没有 metadata，系统不知道结果来自哪里，也不知道该不该给用户看。

## 为什么 RAG 不能只存 content

很多初学者会想：只要把原文存进去，检索出来交给模型不就行了吗？

这只能做最简单的玩具 Demo。

真实一点的 RAG 系统至少会遇到这些问题：

1. 用户问完之后，你要告诉他答案依据来自哪里。
2. 客服只能看客服文档，不能看财务或管理员文档。
3. 订单问题最好优先检索订单业务文档。
4. FAQ、政策、操作手册的使用方式不同。
5. 文档更新时，要知道哪些 chunk 来自旧文件。
6. 检索结果不准时，要排查命中了哪个文件、哪个章节。

这些都不是 content 单独能解决的。

metadata 的意义就是：让一段文本从“孤立字符串”变成“可追踪、可过滤、可解释、可维护的知识片段”。

## document-level metadata 和 chunk-level metadata

metadata 有两个层级：

```text
document-level metadata：整篇文档级别
chunk-level metadata：每个 chunk 级别
```

### document-level metadata

document-level metadata 描述整篇文档。

例如：

```json
{
  "source": "refund-return-policy.md",
  "title": "退款退货规则",
  "file_name": "refund-return-policy.md",
  "file_extension": ".md",
  "doc_type": "policy",
  "business_domain": "refund",
  "permission_group": "customer_service"
}
```

这些字段通常从文件路径、文件内容开头、文档头部信息里提取。

### chunk-level metadata

chunk-level metadata 描述某一个 chunk。

例如：

```json
{
  "chunk_id": "refund_return_policy_chunk_0003",
  "chunk_index": 3,
  "chunk_count": 5,
  "chunk_size_chars": 105,
  "section": "质量问题"
}
```

这些字段通常在切分时产生。

最后写入 Qdrant payload 时，会把两层合并：

```text
document metadata + chunk metadata + content
```

## metadata 完整数据流

metadata 不是在某一个地方突然出现的，它会随着 RAG 入库流程一步一步流动。

完整数据流是：

```text
知识文档头部
-> loader 提取 document metadata
-> RagDocument.metadata
-> splitter 继承 document metadata，并补充 chunk metadata
-> RagChunk.metadata
-> embedding 阶段保持 metadata 不变
-> EmbeddedChunk.metadata
-> build_qdrant_payload() 校验和白名单过滤
-> Qdrant point.payload
-> 后续检索、过滤、引用来源、调试、删除重建
```

用图表示：

```mermaid
flowchart LR
    A["文档头部: 文档类型/业务领域/权限组"] --> B["load_document()"]
    B --> C["RagDocument.metadata"]
    C --> D["split_document_into_chunks()"]
    D --> E["RagChunk.metadata"]
    E --> F["embed_chunks()"]
    F --> G["EmbeddedChunk.metadata"]
    G --> H["build_qdrant_payload()"]
    H --> I["Qdrant payload"]
    I --> J["后续 filter / 引用来源 / 调试 / 重建"]
```

这张图很重要。你要记住：

- loader 负责拿到文档级 metadata。
- splitter 负责补充 chunk 级 metadata。
- embedding 不应该修改 metadata。
- vector_store 写入前负责最后校验。
- Qdrant payload 是后续所有检索增强能力的基础。

如果某个字段在前面丢了，后面就很难补回来。

## 本节字段总览

本项目当前设计的 metadata 字段分成三组。

### 文档来源字段

| 字段 | 含义 | 示例 |
| --- | --- | --- |
| `source` | 知识来源的稳定路径 | `order-shipping-policy.md` |
| `title` | 文档标题 | `订单发货规则` |
| `file_name` | 文件名 | `order-shipping-policy.md` |
| `file_extension` | 文件后缀 | `.md` |

### 业务分类字段

| 字段 | 含义 | 示例 |
| --- | --- | --- |
| `doc_type` | 文档类型 | `policy`、`faq` |
| `business_domain` | 业务领域 | `order`、`refund`、`logistics` |
| `permission_group` | 权限组 | `customer_service` |

### chunk 字段

| 字段 | 含义 | 示例 |
| --- | --- | --- |
| `chunk_id` | 项目内部稳定 chunk 标识 | `order_shipping_policy_chunk_0001` |
| `chunk_index` | 当前 chunk 是第几个 | `1` |
| `chunk_count` | 这篇文档总共切出几个 chunk | `4` |
| `chunk_size_chars` | 当前 chunk 字符数 | `180` |
| `section` | 当前 chunk 所属章节 | `正常发货时效` |

## metadata 字段设计决策表

下面这张表专门回答“为什么要有这个字段”。以后你复习或讲给别人听时，可以先看这张表。

| 字段 | 为什么需要 | 以后主要用于 | 如果没有会怎样 |
| --- | --- | --- | --- |
| `source` | 稳定追踪知识来自哪个文件 | 引用来源、删除重建、排查问题 | 不知道命中内容来自哪里 |
| `title` | 给人看的文档名称 | 答案出处展示、调试阅读 | 出处只能显示文件名，不友好 |
| `file_name` | 保留原始文件名 | 文件级重建、调试 | source 改成路径后不方便拿文件名 |
| `file_extension` | 知道文档格式 | 解析策略、后续扩展 PDF/docx | 很难判断文档最初是什么格式 |
| `doc_type` | 区分文档形态 | policy/faq/manual 过滤和调优 | FAQ 和政策混在一起，难以控制权威性 |
| `business_domain` | 区分业务领域 | 订单/退款/物流/账号过滤 | 用户问订单却可能命中账号文档 |
| `permission_group` | 控制谁能看 | 权限过滤、安全边界 | 可能把无权限内容检索进 prompt |
| `chunk_id` | 稳定追踪 chunk | point id 转换、更新、删除、调试 | 无法稳定定位某个 chunk |
| `chunk_index` | 知道 chunk 顺序 | 引用、调试、重建对比 | 不知道 chunk 在原文中的位置 |
| `chunk_count` | 知道文档被切成多少块 | 切分质量检查、调试 | 很难判断文档是否被异常切分 |
| `chunk_size_chars` | 知道 chunk 大小 | chunk 策略调优 | 不方便发现过大或过小 chunk |
| `section` | 知道所属章节 | 引用来源、局部主题理解 | 只能引用整篇文档，定位不够细 |
| `tags` | 补充多标签分类 | 更灵活的过滤和运营标记 | 对复杂分类支持不足 |

注意：字段不是越多越好。每个字段都应该能回答“以后谁会用它、用来做什么、不存会有什么后果”。

## source 字段：知道内容来自哪里

`source` 是 RAG 里最重要的 metadata 字段之一。

它回答：

```text
这个 chunk 来自哪个知识来源？
```

在本项目中，`source` 使用相对于知识库目录的路径：

```text
order-shipping-policy.md
refund-return-policy.md
```

为什么不用绝对路径？

比如：

```text
D:\wendang\java+python+ai\projects\ai-service\data\knowledge_base\order-shipping-policy.md
```

绝对路径有几个问题：

- 换电脑就变了。
- 上传到服务器后路径不同。
- 可能暴露本机目录结构。
- 不利于跨环境复现。

所以 `source` 应该尽量稳定、短、可移植。

## title 字段：给人看的文档名

`title` 是给人看的。

`source` 更像机器追踪用的来源路径，`title` 更适合展示给用户或开发者。

例如：

```text
source = refund-return-policy.md
title = 退款退货规则
```

后续回答带出处时，可以显示：

```text
参考来源：退款退货规则 / 七天无理由退货
```

这比直接显示文件名更友好。

## section 字段：知道命中了哪个章节

`section` 是 chunk 所属的章节。

例如文档结构是：

```markdown
# 退款退货规则

## 七天无理由退货

...

## 退款到账时间

...
```

切出来的 chunk 可以带：

```json
{
  "section": "退款到账时间"
}
```

section 的价值很大：

- 方便展示引用来源。
- 方便排查检索结果为什么命中。
- 方便后续做章节级过滤或权重调整。
- 让大模型知道上下文属于哪个小主题。

注意：`section` 是可选字段。因为不是所有 txt 文档都有清晰标题结构。

## doc_type 字段：文档类型

`doc_type` 描述文档类型。

本项目当前示例：

```text
policy
faq
```

它的作用是让系统区分不同知识形态。

比如：

- `policy` 更像规则、制度、处理标准。
- `faq` 更像常见问题和答案。
- 后续还可能有 `manual`、`api_doc`、`notice`。

为什么要区分？

因为不同文档类型适合不同处理方式。

例如：

- 用户问“能不能退货”，政策文档可能更权威。
- 用户问“物流三天没更新怎么办”，FAQ 可能更直接。
- 用户问“接口字段怎么传”，API 文档才有意义。

后续检索时可以做：

```text
只检索 doc_type = policy 的内容
```

或者：

```text
优先 policy，补充 faq
```

## business_domain 字段：业务领域

`business_domain` 描述这个 chunk 属于哪个业务域。

本项目当前示例：

```text
order
refund
logistics
account
```

它解决的问题是：企业知识库通常不是一个主题。

如果用户问：

```text
订单超过 72 小时没发货怎么办？
```

更应该优先命中 `order` 领域，而不是账号安全或退款文档。

后续可以用 `business_domain` 做过滤或调试：

```text
只搜 business_domain = order
```

或者查看检索结果是否跑偏：

```text
用户问订单，结果却命中 account 文档，说明检索效果有问题。
```

## permission_group 字段：权限边界

`permission_group` 是非常重要的字段。

它回答：

```text
谁可以看这个 chunk？
```

本项目当前示例：

```text
customer_service
```

它表示这类内容可以给客服助手使用。

为什么权限字段要在入库阶段就保存？

因为检索发生在生成回答之前。如果不在检索阶段过滤权限，就可能出现这种危险流程：

```text
用户无权限
-> 检索到了敏感文档
-> 敏感内容进入 prompt
-> 模型可能泄露
```

正确方向应该是：

```text
用户权限
-> payload filter 过滤 permission_group
-> 只检索用户有权看的 chunk
-> 再交给模型
```

所以权限不是“回答时提醒模型不要说”，而是应该在检索前就尽量过滤掉。

## chunk_id 字段：追踪和重建

`chunk_id` 是项目内部 chunk 的稳定标识。

例如：

```text
order_shipping_policy_chunk_0001
```

它和 Qdrant point id 不是一回事。

第 13 节我们已经做了：

```text
chunk_id -> 稳定 UUID -> Qdrant point id
```

但原始 `chunk_id` 仍然要放进 payload。

原因是：

- 方便调试。
- 方便展示。
- 方便删除或重建。
- 方便和本地切分结果对应。

如果只保留 Qdrant UUID，你很难看出这个 point 对应哪篇文档第几个 chunk。

## chunk_index、chunk_count、chunk_size_chars

这三个字段主要用于调试和重建。

### chunk_index

表示当前 chunk 是第几个。

```text
chunk_index = 3
```

### chunk_count

表示这篇文档总共切出了几个 chunk。

```text
chunk_count = 5
```

### chunk_size_chars

表示当前 chunk 的字符数。

```text
chunk_size_chars = 180
```

这些字段后续有什么用？

- 检查切分是否异常。
- 判断文档是不是被切得太碎。
- 展示引用时可以定位 chunk 顺序。
- 重新入库时可以对比变化。

## metadata 设计的三种常见失败

### 失败 1：字段太少

只存：

```json
{
  "source": "order.md"
}
```

问题是：

- 没法按业务过滤。
- 没法按权限过滤。
- 没法展示友好标题。
- 很难排查检索结果。

### 失败 2：字段太多

把所有信息都塞进 payload：

```json
{
  "local_path": "D:\\...",
  "created_by": "...",
  "internal_note": "...",
  "raw_headers": "...",
  "debug_text": "..."
}
```

问题是：

- 可能暴露敏感信息。
- payload 变得混乱。
- 字段没人维护。
- 后续过滤逻辑不稳定。

### 失败 3：字段不稳定

有时写：

```json
{
  "permission_group": "customer_service"
}
```

有时写：

```json
{
  "permission": ["客服"]
}
```

有时写：

```json
{
  "role": "cs"
}
```

这会导致后续 filter 很难写。

metadata 的字段名和类型必须稳定。

## 字段命名原则

本项目使用英文 snake_case 字段名：

```text
business_domain
permission_group
chunk_size_chars
```

为什么不用中文字段名？

中文字段当然也能用，但工程里通常更推荐英文 snake_case：

- 和 Python 命名风格一致。
- 和 JSON API 风格更常见。
- 和 Qdrant filter、日志、测试更容易配合。
- 避免不同系统对中文 key 的兼容问题。

字段值可以是中文，但字段名最好稳定。

## 字段类型原则

metadata 字段类型不能随意变化。

本项目当前支持：

```python
str | int | float | bool | list[str]
```

常用规则：

| 字段 | 类型 |
| --- | --- |
| `source` | `str` |
| `title` | `str` |
| `doc_type` | `str` |
| `business_domain` | `str` |
| `permission_group` | `str` |
| `chunk_index` | `int` |
| `chunk_count` | `int` |
| `chunk_size_chars` | `int` |
| `tags` | `list[str]` |

为什么 `chunk_index` 不用字符串？

因为后续可能要排序、比较、统计。如果存成 `"3"`，就会产生额外转换。

为什么 `permission_group` 当前用字符串，不用列表？

因为本项目当前每个文档只有一个权限组，先保持简单。以后如果出现多个权限组，再升级为 `permission_groups: list[str]` 会更合理。

## 必备字段和可选字段

metadata 不是所有字段都必须有。

本项目当前必备 document 字段：

```text
source
title
file_name
file_extension
doc_type
business_domain
permission_group
```

本项目当前必备 chunk 字段：

```text
source
title
file_name
file_extension
doc_type
business_domain
permission_group
chunk_id
chunk_index
chunk_count
chunk_size_chars
```

当前可选字段：

```text
section
tags
```

为什么 `section` 可选？

因为 Markdown 文档通常有标题，但 txt 文档可能没有明确章节。强制要求所有 chunk 都有 section，会让 txt 或其他格式变得难处理。

## 为什么需要 payload 白名单

第 13 节我们把 metadata 放进 Qdrant payload。

如果直接把所有 metadata 原样写进去，短期很方便，长期会有风险：

- 不该进库的字段也进库。
- 调试字段混入正式数据。
- 本机路径、内部备注、敏感标记可能被保存。
- 后续 filter 字段越来越乱。

所以本节新增了 payload 白名单。

只有这些字段允许进入 Qdrant payload：

```text
source
title
file_name
file_extension
doc_type
business_domain
permission_group
chunk_id
chunk_index
chunk_count
chunk_size_chars
section
tags
content
```

注意：`content` 不是普通 metadata 字段，但它会被放进 payload，因为后续大模型需要读原文。

## 本节主题系统讲解：新增 metadata.py

本节新增 `app/rag/metadata.py`。

它集中负责：

1. 定义 metadata 字段。
2. 标准化 metadata 值。
3. 校验 document metadata。
4. 校验 chunk metadata。
5. 构造 Qdrant payload。

为什么要单独建一个文件？

因为 metadata 规则会被很多模块用到：

- loader 负责提取 document metadata。
- splitter 负责补充 chunk metadata。
- vector_store 负责写入 payload。
- retriever 以后会根据 metadata filter 检索。
- generator 以后会根据 metadata 展示引用来源。

如果这些规则散落在各个文件里，后面很容易不一致。

## normalize_metadata()

`normalize_metadata()` 做标准化。

例如：

```python
{
    " source ": " order-shipping-policy.md ",
    "tags": [" order ", " ", " shipping "],
}
```

会变成：

```python
{
    "source": "order-shipping-policy.md",
    "tags": ["order", "shipping"],
}
```

它解决的是脏数据问题：

- 字段名前后有空格。
- 字符串值前后有空格。
- 列表里有空字符串。

标准化不是为了好看，而是为了后续 filter 稳定。

如果 `permission_group` 有时候是 `"customer_service"`，有时候是 `" customer_service "`，filter 时就会很麻烦。

## validate_document_metadata()

`validate_document_metadata()` 检查一篇文档必须有的字段。

它要求：

```text
source
title
file_name
file_extension
doc_type
business_domain
permission_group
```

这些字段必须是非空字符串。

它还检查：

```text
file_extension 必须是 .md 或 .txt
```

这是因为当前阶段我们只支持 Markdown/txt 文档。如果以后支持 PDF、docx，再扩展这个规则。

## validate_chunk_metadata()

`validate_chunk_metadata()` 在 document metadata 基础上继续检查 chunk 字段。

它要求：

```text
chunk_id
chunk_index
chunk_count
chunk_size_chars
```

其中：

- `chunk_id` 必须是非空字符串。
- `chunk_index` 必须是正整数。
- `chunk_count` 必须是正整数。
- `chunk_size_chars` 必须是正整数。
- `section` 如果存在，也必须是非空字符串。

为什么要检查正整数？

因为 `chunk_index = 0`、`chunk_count = -1` 这种数据没有业务意义，应该尽早报错。

## build_qdrant_payload()

`build_qdrant_payload()` 是本节最关键的落地点。

它做的事情是：

```text
chunk_id + content + metadata
-> 标准化
-> chunk_id 一致性检查
-> 必备字段检查
-> payload 白名单过滤
-> 返回可写入 Qdrant 的 payload
```

为什么要检查 chunk_id 一致？

因为 `EmbeddedChunk.chunk_id` 和 `metadata["chunk_id"]` 如果不一致，就说明数据已经错乱。

例如：

```text
EmbeddedChunk.chunk_id = order_chunk_0001
metadata.chunk_id = refund_chunk_0003
```

这时不能继续写入 Qdrant，必须报错。

## loaders.py 的变化

loader 原本会提取：

```text
source
title
file_name
file_extension
doc_type
business_domain
permission_group
```

本节增加了：

```text
normalize_metadata(metadata)
```

也就是说，loader 输出的 metadata 会先做基础清洗。

它没有在 loader 阶段强制调用 `validate_document_metadata()`，原因是：loader 的职责是“加载和提取”。真正写入 Qdrant 前会做严格校验。这样可以让 loader 仍然保持相对通用，方便以后处理临时文档或调试文档。

## splitters.py 的变化

splitter 原本会补充：

```text
chunk_id
chunk_index
chunk_count
chunk_size_chars
section
```

本节让 splitter 创建 chunk metadata 时也走 `normalize_metadata()`。

这样可以保证从 document metadata 继承来的字段，以及 splitter 新增的字段，格式都比较稳定。

## vector_store.py 的变化

第 13 节里，`build_qdrant_point()` 直接把 metadata 复制进 payload。

本节改成：

```text
build_qdrant_point()
-> build_qdrant_payload()
-> Qdrant point
```

这意味着：写入 Qdrant 前，会做最后一道闸门。

如果 metadata 缺字段、类型不对、chunk_id 不一致，系统会在写入前报错，而不是把脏数据塞进向量库。

这个位置很关键，因为 Qdrant 是后续检索的基础。一旦脏数据写进去，后面 filter、引用、调试都会变麻烦。

## 为什么不是用 Pydantic 模型定义 metadata

你可能会问：既然我们已经学过 Pydantic，为什么不直接写一个 `RagMetadata` 模型？

这是一个合理问题。

当前我选择先用函数和常量，是因为：

1. metadata 字段还在教学阶段，会逐步扩展。
2. 当前项目里 `RagDocument.metadata` 和 `RagChunk.metadata` 仍然是灵活 dict。
3. Qdrant payload 本身也是 dict。
4. 先用函数能更清楚地看到标准化、校验、白名单每一步。

后续如果 metadata 稳定下来，可以再升级成 Pydantic 模型，例如：

```text
DocumentMetadata
ChunkMetadata
QdrantPayload
```

这会更严谨，但现在不是必须。

## metadata 和权限安全

权限字段不是摆设。

错误做法是：

```text
先检索所有文档
-> 把结果交给模型
-> 告诉模型“不要回答没权限的内容”
```

这很危险，因为敏感内容已经进入 prompt 了。

更好的做法是：

```text
根据当前用户身份得到 permission_group
-> 在 Qdrant payload filter 里限制 permission_group
-> 只返回用户能看的 chunk
-> 再交给模型回答
```

虽然本节还没有写 payload filter，但 `permission_group` 字段就是为后续这个能力准备的。

## 真实业务场景：客服问订单问题时 metadata 怎么发挥作用

假设用户问：

```text
我的订单已经付款三天了还没发货，客服应该怎么处理？
```

如果没有 metadata，系统只能做纯向量相似度检索，可能命中这些内容：

```text
订单发货规则
退款退货规则
物流查询 FAQ
账号安全 FAQ
```

其中有些内容相似，但不一定最合适。

如果有 metadata，后续就可以这样控制：

```text
用户身份：customer_service
问题业务域：order
优先文档类型：policy

检索约束：
permission_group = customer_service
business_domain = order
doc_type = policy
```

这样系统更可能命中：

```text
source = order-shipping-policy.md
title = 订单发货规则
section = 超过 72 小时未发货
```

最终模型回答时也可以带出处：

```text
根据《订单发货规则 / 超过 72 小时未发货》，如果订单超过 72 小时仍未发货，客服可以先核查仓库状态，并在符合条件时创建工单继续跟进。
```

这个例子说明：metadata 不是“存着好看”，而是直接影响 RAG 的可控性和可解释性。

## metadata 和引用来源

RAG 的回答最好能带出处。

例如：

```text
根据《订单发货规则 / 正常发货时效》，订单付款成功后通常会在 24 小时内处理发货。
```

这个出处来自哪里？

不是模型凭空知道的，而是来自 metadata：

```text
title = 订单发货规则
section = 正常发货时效
source = order-shipping-policy.md
```

所以 metadata 质量越好，后续引用来源越自然。

## metadata 和检索调试

假设用户问：

```text
账号密码忘了怎么办？
```

检索结果却命中了：

```text
source = refund-return-policy.md
business_domain = refund
```

这时你能快速判断：检索跑偏了。

如果没有 metadata，你只看到一段文本，很难系统化排查。

metadata 可以帮助你回答：

- 命中了哪个文件？
- 命中了哪个章节？
- 命中的是 FAQ 还是 policy？
- 命中的是哪个业务域？
- chunk 是第几个？
- 这个 chunk 大小是否异常？

## metadata 和文档更新/删除

以后知识库会更新。

例如 `order-shipping-policy.md` 内容改了，你需要重新入库。

如果有 `source` 和 `chunk_id`，你可以定位：

```text
哪些 point 来自 order-shipping-policy.md？
哪些 point 对应旧 chunk？
是否要删除后重建？
```

如果没有这些字段，文档更新会变得很混乱。

## payload filter 预告：第 16 节会怎样用这些字段

本节还没有实现 payload filter，但你现在应该先知道后面会怎么用。

Qdrant payload filter 的核心思想是：

```text
不仅按 vector 相似度找，还要按 payload 字段过滤。
```

例如只检索客服可看的文档：

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

再比如只检索订单业务：

```json
{
  "must": [
    {
      "key": "business_domain",
      "match": {
        "value": "order"
      }
    }
  ]
}
```

再严格一点，组合多个条件：

```text
permission_group = customer_service
business_domain = order
doc_type = policy
```

这就是为什么本节要先把字段设计好。

如果字段名不稳定，后面 filter 写不出来。

如果字段值不稳定，filter 查不准。

如果权限字段缺失，filter 防不住。

如果 payload 没有白名单，filter 可能依赖了不该长期存在的临时字段。

所以第 14 节不是孤立的一节，它是在给第 16 节 payload filter、第 19 节引用来源、第 23 节文档更新删除打基础。

## 本节新增测试重点

本节新增 `test_rag_metadata.py`。

重点测试：

1. metadata 字段和值会被 trim。
2. 空 key 会被拒绝。
3. document metadata 必备字段缺失会报错。
4. 不支持的文件后缀会报错。
5. chunk metadata 必须有正整数 chunk 字段。
6. Qdrant payload 只保留白名单字段。
7. `chunk_id` 不一致会报错。
8. 空 content 不能进入 payload。

`test_rag_vector_store.py` 也补了写入前 payload 校验，确保 metadata 不合格时不会真的调用 Qdrant。

## 常见错误

### 错误 1：认为 metadata 只是注释

metadata 不是注释，它会影响检索、过滤、引用、权限、调试和重建。

### 错误 2：只保存 source，不保存业务字段

只知道来源文件还不够。后续需要 `doc_type`、`business_domain`、`permission_group` 才能做更精细的检索控制。

### 错误 3：权限字段靠 prompt 控制

不要把权限完全交给模型判断。权限应该尽量在检索前通过 payload filter 控制。

### 错误 4：字段名反复变化

今天叫 `permission_group`，明天叫 `role`，后天叫 `auth`，会让 filter 和测试全部变乱。

### 错误 5：把内部调试字段都写入 Qdrant

payload 应该有边界。不是所有 metadata 都适合进入向量数据库。

### 错误 6：把绝对路径写入 source

绝对路径不稳定，也可能暴露本机结构。优先使用相对知识库目录的路径。

### 错误 7：忽略字段类型

`chunk_index` 应该是整数，`tags` 应该是字符串列表。字段类型不稳定会影响排序、过滤和统计。

### 错误 8：把 metadata 设计和检索阶段割裂开

metadata 字段不是为了本节代码好看，而是为了后续检索、过滤、引用、调试和重建。设计字段时必须提前想它以后在哪里被使用。

## 本节练习

### 练习 1：解释 metadata 的作用

请用自己的话解释：metadata 在 RAG 中为什么重要？

参考答案：

metadata 让 chunk 不只是一个孤立文本片段，而是带有来源、标题、章节、业务领域、文档类型和权限信息的知识单元。它支撑引用来源、权限过滤、检索调试、文档更新和后续 payload filter。

### 练习 2：判断字段属于哪个层级

请判断下面字段属于 document-level 还是 chunk-level：

```text
source
title
chunk_index
section
permission_group
chunk_size_chars
```

参考答案：

`source`、`title`、`permission_group` 属于 document-level。`chunk_index`、`chunk_size_chars` 属于 chunk-level。`section` 更接近 chunk-level，因为同一篇文档的不同 chunk 可能属于不同章节。

### 练习 3：为什么 permission_group 重要

请解释为什么权限字段不能等到模型回答时再处理。

参考答案：

如果先检索所有内容再让模型判断权限，敏感内容已经进入 prompt，存在泄露风险。更好的做法是在检索前根据用户权限用 payload filter 限制 `permission_group`，只把用户有权看的 chunk 交给模型。

### 练习 4：判断 payload 是否合理

下面 payload 是否合理？

```json
{
  "source": "D:\\my\\private\\path\\order.md",
  "title": "订单规则",
  "content": "订单超过 72 小时未发货...",
  "debug_note": "这是我本地测试用的内部备注"
}
```

参考答案：

不太合理。`source` 使用了本机绝对路径，不稳定且可能暴露本机目录结构。`debug_note` 是内部调试字段，不应该随便进入 Qdrant payload。更合理的做法是使用相对路径，并通过 payload 白名单限制字段。

### 练习 5：设计一个账号安全 FAQ 的 metadata

请给账号安全 FAQ 设计 metadata。

参考答案：

```json
{
  "source": "account-security-faq.md",
  "title": "账号安全常见问题",
  "file_name": "account-security-faq.md",
  "file_extension": ".md",
  "doc_type": "faq",
  "business_domain": "account",
  "permission_group": "customer_service"
}
```

### 练习 6：为什么要 payload 白名单

参考答案：

payload 白名单可以防止无关字段、调试字段、敏感字段被写入 Qdrant。它让向量库中的数据结构更稳定，后续 filter、引用来源、调试和权限控制都更可控。

### 练习 7：解释 chunk_id 一致性检查

为什么 `EmbeddedChunk.chunk_id` 和 `metadata["chunk_id"]` 不一致时应该报错？

参考答案：

因为这说明数据状态已经错乱。一个对象的主 chunk_id 和 metadata 里的 chunk_id 指向不同 chunk，继续写入会导致 point id、payload、来源追踪不一致，后续删除、重建、调试都会出问题。

### 练习 8：为订单客服场景选择 metadata 过滤字段

用户问：“订单超过 72 小时没有发货怎么办？”

如果后续要做 payload filter，你会优先使用哪些 metadata 字段？

参考答案：

可以优先使用：

```text
permission_group = customer_service
business_domain = order
doc_type = policy
```

`permission_group` 保证用户有权访问，`business_domain` 限制在订单业务，`doc_type=policy` 优先命中规则类文档。后续也可以根据检索效果决定是否放宽 `doc_type`，让 FAQ 也参与召回。

### 练习 9：解释字段设计决策

请从 `source`、`title`、`business_domain`、`permission_group` 中任选两个，说出“为什么需要它、以后用在哪里、如果没有会怎样”。

参考答案示例：

`source` 用来稳定追踪内容来自哪个文件，后续用于引用来源、删除重建和排查问题。如果没有 source，就很难知道命中的 chunk 来自哪里。

`permission_group` 用来控制谁能看这段内容，后续用于 payload filter。如果没有 permission_group，就可能把无权限内容检索进 prompt，造成安全风险。

## 自测题

### 自测 1：metadata 和 content 的区别是什么？

答案：

content 是原文片段，供大模型阅读。metadata 是描述原文片段的信息，例如来源、标题、章节、业务域和权限组。

### 自测 2：metadata 和 Qdrant payload 的关系是什么？

答案：

Qdrant payload 用来保存 content 和 metadata。metadata 是 payload 里的结构化描述信息，content 是 payload 里的原文文本。

### 自测 3：为什么 `source` 不建议使用绝对路径？

答案：

绝对路径换环境后不稳定，可能暴露本机目录结构，也不利于部署和复现。更推荐使用相对知识库目录的路径。

### 自测 4：`title` 和 `source` 有什么区别？

答案：

`source` 更适合机器追踪来源路径，`title` 更适合展示给用户或开发者阅读。

### 自测 5：`section` 为什么可选？

答案：

不是所有文档都有明确章节结构。例如 txt FAQ 可能没有 Markdown 标题。强制要求 section 会降低兼容性。

### 自测 6：`doc_type` 和 `business_domain` 有什么区别？

答案：

`doc_type` 描述文档形态，例如 policy 或 faq。`business_domain` 描述业务领域，例如 order、refund、logistics、account。

### 自测 7：为什么 `chunk_index` 应该是 int？

答案：

因为它后续可能用于排序、比较和统计。用 int 比字符串更稳定、更符合语义。

### 自测 8：payload 白名单解决什么问题？

答案：

它防止任意 metadata 字段进入 Qdrant，减少敏感信息泄露、调试字段污染和字段混乱的风险。

### 自测 9：本节为什么还不做 payload filter？

答案：

payload filter 是检索阶段的内容。本节先设计和校验字段，后续检索时才能基于这些字段过滤。

### 自测 10：metadata 字段设计得好，对后续哪些能力有帮助？

答案：

有助于引用来源、权限过滤、业务域过滤、文档类型过滤、检索调试、文档更新、删除重建和结果展示。

### 自测 11：metadata 从文档到 Qdrant payload 会经过哪些步骤？

答案：

文档头部信息先被 loader 提取成 `RagDocument.metadata`，splitter 继承它并补充 chunk 字段形成 `RagChunk.metadata`，embedding 阶段保持 metadata 不变，vector_store 在写入前用 `build_qdrant_payload()` 做校验和白名单过滤，最后进入 Qdrant point.payload。

### 自测 12：为什么本节说 metadata 是后续 payload filter 的基础？

答案：

因为 payload filter 依赖 payload 里的结构化字段。如果 `permission_group`、`business_domain`、`doc_type` 等字段没有在入库时稳定写入，后续检索时就没法按权限、业务域或文档类型过滤。

## 讲给别人听的口述版

如果别人问你“RAG 里的 metadata 是干什么的”，你可以这样回答：

```text
RAG 不能只把文本和向量存进向量库，还要保存 metadata。
content 是给模型读的原文，vector 是给向量库检索用的，metadata 则负责描述这段文本来自哪里、属于哪个文档、哪个章节、哪个业务域、哪类用户有权限看。
我们的项目把 metadata 分成文档级和 chunk 级：source、title、doc_type、business_domain、permission_group 属于文档级；chunk_id、chunk_index、chunk_count、chunk_size_chars、section 属于 chunk 级。
写入 Qdrant 前，我们会做字段标准化、必备字段校验和 payload 白名单过滤，确保后续引用来源、权限过滤、检索调试和文档重建都有可靠字段可用。
这一节还不做真正的 payload filter，但 permission_group、doc_type、business_domain 这些字段就是为后续过滤检索结果准备的。
```

这段能讲清楚，说明你已经理解 metadata 的工程价值，而不是只会说“metadata 是附加信息”。

## 本节复盘

本节完成了 RAG metadata 的工程化设计：

- 明确 metadata 不是注释，而是 RAG 的结构化控制信息。
- 区分了 document-level metadata 和 chunk-level metadata。
- 设计了来源字段、业务分类字段、权限字段和 chunk 字段。
- 解释了 `source`、`title`、`section`、`doc_type`、`business_domain`、`permission_group` 的职责。
- 增加了 metadata 标准化。
- 增加了 document/chunk metadata 校验。
- 增加了 Qdrant payload 白名单。
- 让 Qdrant 写入前会先校验 payload，不合格就不写入。
- 补清楚了 metadata 从文档头部到 Qdrant payload 的完整流动过程。
- 通过客服订单场景说明了 metadata 如何服务后续检索控制。
- 提前理解了 payload filter 会怎样依赖这些字段。

第 15 节可以在这个基础上开始学习：**基础 top_k 检索**。

到那时，metadata 会开始真正参与检索结果解释和后续 filter 设计。
