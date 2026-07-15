# 阶段 4 第 11 节：文档加载和文本清洗

> 本节结论：RAG 的文档加载不是简单 `read_text()` 就结束。loader 的职责是从文件系统读取知识文档，做最基础的文本清洗，提取标题和 metadata，并输出统一的 `RagDocument`。本节新增 `app/rag/loaders.py`，支持加载 `.md` 和 `.txt` 文件，默认跳过知识库目录里的 `README.md`，并把第 10 节准备的样本文档转换成后续可切分、可向量化的内部文档对象。

## 本节状态说明

这一节不需要打开 VMware Ubuntu 虚拟机。

原因是：

```text
本节不访问 Qdrant。
本节不启动 Docker。
本节不生成 embedding。
本节只读取 Windows 项目里的 Markdown/txt 文件。
```

本节新增：

```text
projects/ai-service/app/rag/loaders.py
projects/ai-service/tests/test_rag_loaders.py
```

本节更新：

```text
projects/ai-service/app/rag/README.md
projects/ai-service/README.md
```

## 生成笔记前的教学复核

这一节必须讲清：

```text
1. loader 是什么。
2. loader 在 RAG 流程里处于什么位置。
3. 为什么不能把“读取文件、切 chunk、embedding、写 Qdrant”都放在 loader 里。
4. 为什么读取文本要指定 UTF-8。
5. 文本清洗 cleaning 做什么，不做什么。
6. Markdown/txt 标题怎么提取。
7. 文档 metadata 怎么提取。
8. 为什么 README.md 默认不作为知识文档加载。
9. load_document 和 load_documents_from_directory 的区别。
10. loader 输出为什么是 RagDocument。
```

## 本节一句话定位

第 10 节我们准备了第一批知识文档：

```text
projects/ai-service/data/knowledge_base/*.md
projects/ai-service/data/knowledge_base/*.txt
```

第 11 节要做的是：

```text
把这些文件读进 Python，并转换成 RagDocument。
```

也就是：

```text
文件系统里的文档
-> loader
-> RagDocument(content=..., metadata=...)
```

注意，本节只做到 `RagDocument`。

不做：

```text
chunk 切分
embedding 生成
写入 Qdrant
检索问答
```

## 基础知识铺垫：什么是 loader

loader 可以翻译成：

```text
加载器。
```

在 RAG 里，loader 负责：

```text
从某个来源读取原始内容，并转换成系统内部统一文档对象。
```

来源可以是：

```text
本地 Markdown 文件
本地 txt 文件
PDF
Word
网页
数据库
对象存储
企业知识库系统
```

当前阶段我们只做：

```text
Markdown/txt 本地文件 loader。
```

因为它最适合入门。

## loader 在 RAG 流程里的位置

文档入库流程是：

```text
原始文档
-> loader 加载
-> cleaning 清洗
-> splitter 切 chunk
-> embedding 生成向量
-> vector_store 写入 Qdrant
```

本节只覆盖：

```text
原始文档
-> loader 加载
-> cleaning 清洗
-> RagDocument
```

也就是说，loader 是入库流程的第一步。

如果 loader 输出不稳定，后面所有步骤都会受影响。

## 为什么 loader 不能什么都做

初学时很容易写出这种代码：

```text
读取文件
切 chunk
调用 embedding
写 Qdrant
```

全部塞进一个函数。

这样短期看起来很快，但问题很大。

### 问题 1：职责不清

loader 应该只关心：

```text
怎么把文件变成 RagDocument。
```

它不应该关心：

```text
chunk 多大
embedding 用哪个模型
Qdrant collection 叫什么
检索 top_k 是多少
```

这些属于后续模块。

### 问题 2：测试困难

如果 loader 同时调用 embedding 和 Qdrant，那么测试 loader 时就要准备外部服务。

这会让测试变慢、变复杂、变不稳定。

本节 loader 不依赖外部服务。

所以可以很快测试：

```text
文件能不能读取
清洗是否正确
metadata 是否提取
目录加载是否跳过 README
```

### 问题 3：后续不好替换

未来可能会有：

```text
MarkdownLoader
TxtLoader
PdfLoader
WordLoader
WebPageLoader
```

如果 loader 职责清楚，每种来源只需要负责加载自己的文档。

后面的 splitter、embedding、vector_store 可以复用。

## 基础知识铺垫：什么是文本清洗

文本清洗 cleaning 是指：

```text
把原始文本里不利于后续处理的杂质处理掉。
```

本节只做最基础的清洗：

```text
1. 把 Windows 换行 \r\n 统一成 \n。
2. 把旧 Mac 换行 \r 统一成 \n。
3. 去掉每行末尾多余空白。
4. 去掉整篇文档首尾空白。
5. 把连续 3 个以上空行压缩成 2 个空行。
```

为什么要这样做？

因为后续 chunk 切分会依赖文本结构。

如果换行乱、空白乱，切出来的 chunk 也会乱。

## 清洗不等于改写内容

这个边界很重要。

本节 cleaning 不做：

```text
1. 改写句子。
2. 总结段落。
3. 删除业务规则。
4. 翻译文本。
5. 调用模型润色。
```

因为 loader 阶段应该尽量保留原始知识。

清洗的目标是：

```text
让文本格式更稳定。
```

不是：

```text
改变文本含义。
```

## 基础知识铺垫：为什么读取文本要指定 UTF-8

Python 读取文本时可以写：

```python
path.read_text()
```

也可以写：

```python
path.read_text(encoding="utf-8")
```

本项目选择后者。

原因是：

```text
知识库文档包含中文。
```

如果不指定编码，Python 会使用系统默认编码。

在不同机器上，默认编码可能不同。

这会导致：

```text
同一份中文文档，在一台机器上读正常，在另一台机器上可能乱码或报错。
```

所以读取知识文档时明确使用：

```text
UTF-8
```

这是工程习惯。

补充提醒：

```text
如果 PowerShell 显示中文异常，第一怀疑应该是终端显示编码问题，而不是立刻改文件内容。
```

这是我们之前约定过的判断原则。

## 基础知识铺垫：metadata 从哪里来

metadata 不是凭空来的。

它可以来自：

```text
1. 文件路径。
2. 文件名。
3. 文件扩展名。
4. 文档标题。
5. 文档开头写明的元信息。
6. 外部数据库记录。
7. 用户上传时填写的表单。
```

当前阶段我们从文件和文档内容中提取：

```text
source
title
file_name
file_extension
doc_type
business_domain
permission_group
```

这些字段后续会进入：

```text
RagDocument.metadata
-> RagChunk.metadata
-> Qdrant point.payload
```

所以 loader 阶段提取 metadata，是后面 payload/filter/source citation 的基础。

## 本节主题系统讲解：新增 loaders.py

本节新增文件：

```text
projects/ai-service/app/rag/loaders.py
```

它主要提供这些能力：

```text
clean_document_text()
extract_document_title()
extract_inline_metadata()
load_document()
load_documents_from_directory()
```

它的输入是：

```text
文件路径或目录路径。
```

它的输出是：

```text
RagDocument
list[RagDocument]
```

## SUPPORTED_DOCUMENT_SUFFIXES

代码：

```python
SUPPORTED_DOCUMENT_SUFFIXES = {".md", ".txt"}
```

它表示当前 loader 只支持：

```text
Markdown 文件
txt 文件
```

如果传入：

```text
.pdf
.docx
.xlsx
```

当前会拒绝。

这不是因为这些格式不重要，而是因为本阶段先把 Markdown/txt 主线跑通。

## DEFAULT_IGNORED_FILE_NAMES

代码：

```python
DEFAULT_IGNORED_FILE_NAMES = {"README.md"}
```

为什么默认跳过 `README.md`？

因为：

```text
data/knowledge_base/README.md
```

是目录说明，不是知识库业务内容。

如果把 README 当成知识文档，后面检索时可能出现：

```text
用户问订单问题，系统检索到了目录说明。
```

这没有意义。

所以目录批量加载时默认跳过 README。

但单独调用 `load_document("README.md")` 仍然可以加载。

这表示：

```text
批量加载有默认过滤规则；
单文件加载尊重调用者指定的文件。
```

## METADATA_KEY_MAP

代码：

```python
METADATA_KEY_MAP = {
    "文档类型": "doc_type",
    "业务领域": "business_domain",
    "权限组": "permission_group",
}
```

第 10 节的文档里有：

```text
> 文档类型：policy
> 业务领域：order
> 权限组：customer_service
```

或者 txt 里有：

```text
文档类型：faq
业务领域：logistics
权限组：customer_service
```

loader 会把这些中文标记转换成统一英文 metadata key：

```text
doc_type
business_domain
permission_group
```

为什么不直接保留中文 key？

因为后续写代码和 filter 时，英文 snake_case 更稳定。

比如：

```text
metadata["doc_type"] == "policy"
metadata["permission_group"] == "customer_service"
```

比混合中文字段名更适合工程代码。

## clean_document_text()

这个函数负责基础清洗。

核心逻辑：

```python
normalized = raw_text.replace("\r\n", "\n").replace("\r", "\n")
lines = [line.rstrip() for line in normalized.split("\n")]
text = "\n".join(lines).strip()
return re.sub(r"\n{3,}", "\n\n", text)
```

逐步解释：

### 第一步：统一换行

```python
raw_text.replace("\r\n", "\n").replace("\r", "\n")
```

常见换行：

```text
Windows: \r\n
Linux/macOS: \n
旧 Mac: \r
```

统一成：

```text
\n
```

后续处理更稳定。

### 第二步：去掉每行末尾空白

```python
lines = [line.rstrip() for line in normalized.split("\n")]
```

`rstrip()` 会去掉每行右侧空白。

例如：

```text
"第一行  "
```

变成：

```text
"第一行"
```

这能减少无意义差异。

### 第三步：去掉整篇首尾空白

```python
text = "\n".join(lines).strip()
```

如果文件开头或末尾有空行，会被去掉。

### 第四步：压缩过多空行

```python
re.sub(r"\n{3,}", "\n\n", text)
```

意思是：

```text
连续 3 个以上换行，压缩成 2 个换行。
```

保留 2 个换行，是为了保留段落分隔。

不是所有换行都删掉。

## extract_document_title()

这个函数负责提取标题。

Markdown 文档：

```text
# 订单发货规则
```

提取成：

```text
订单发货规则
```

txt 文档：

```text
物流查询常见问题
```

第一行非空文本就是标题。

这里有一个细节：

```text
如果 txt 里遇到以 > 开头的说明行，会跳过。
```

因为 `>` 更像 Markdown 里的引用或 metadata 说明，不适合作为正文标题。

## extract_inline_metadata()

这个函数负责从文档前 20 行提取 metadata。

为什么只看前 20 行？

因为文档元信息通常写在开头。

没有必要扫描整篇文档。

它能处理两种形式：

```text
> 文档类型：policy
文档类型：faq
```

也就是支持带 `>` 和不带 `>`。

它还能处理中文冒号：

```text
：
```

和英文冒号：

```text
:
```

这样样本文档稍微不同，也能被提取。

## load_document()

这个函数负责加载单个文件。

输入：

```text
Path 或字符串路径。
```

输出：

```text
RagDocument
```

它做这些事情：

```text
1. 检查文件后缀是否支持。
2. 检查路径是否是文件。
3. 用 UTF-8 读取文本。
4. 清洗文本。
5. 空文档报错。
6. 提取 source、title、file_name、file_extension。
7. 提取 doc_type、business_domain、permission_group。
8. 返回 RagDocument。
```

一个加载结果大概是：

```text
RagDocument(
  content="...",
  metadata={
    "source": "order-shipping-policy.md",
    "title": "订单发货规则",
    "file_name": "order-shipping-policy.md",
    "file_extension": ".md",
    "doc_type": "policy",
    "business_domain": "order",
    "permission_group": "customer_service"
  }
)
```

## base_dir 是什么

`load_document()` 支持：

```python
base_dir=KNOWLEDGE_BASE_DIR
```

它的作用是生成相对 source。

比如真实文件路径是：

```text
D:/wendang/java+python+ai/projects/ai-service/data/knowledge_base/order-shipping-policy.md
```

如果不处理，metadata 里可能出现很长的本机绝对路径。

这不适合作为引用来源。

我们希望 source 是：

```text
order-shipping-policy.md
```

所以使用：

```text
path.relative_to(base_dir).as_posix()
```

这样后续引用来源更干净。

## load_documents_from_directory()

这个函数负责批量加载目录。

输入：

```text
一个目录路径
```

输出：

```text
list[RagDocument]
```

它会：

```text
1. 检查路径是否是目录。
2. 遍历目录下文件。
3. 只加载 .md 和 .txt。
4. 默认跳过 README.md。
5. 按文件名排序，保证顺序稳定。
6. 调用 load_document() 加载每个文件。
```

为什么要排序？

因为测试和调试时，稳定顺序很重要。

如果每次加载顺序不一样，后面排查会更困难。

## 本节测试讲什么

新增测试文件：

```text
projects/ai-service/tests/test_rag_loaders.py
```

测试覆盖：

```text
1. clean_document_text 能统一换行和空白。
2. Markdown 文档能提取 title 和 metadata。
3. txt 文档能提取 title 和 metadata。
4. 批量加载目录时默认跳过 README.md。
5. 不支持的后缀会被拒绝。
```

这些测试不是为了追求覆盖率数字。

它们是在保护 loader 的核心行为。

## 为什么测试不直接连 Qdrant

因为 loader 和 Qdrant 没关系。

loader 输出的是：

```text
RagDocument
```

Qdrant 写入是后续 `vector_store` 的职责。

如果 loader 测试依赖 Qdrant，就说明模块边界混乱了。

本节测试只需要本地文件。

这就是分层测试的好处。

## 本节和第 12 节的关系

第 11 节输出：

```text
list[RagDocument]
```

第 12 节会把它们切成：

```text
list[RagChunk]
```

也就是：

```text
load_documents_from_directory()
-> RagDocument
-> splitter
-> RagChunk
```

所以本节是 chunk 切分的前置条件。

## 常见错误理解

### 错误 1：loader 就是 read_text

不准确。

`read_text()` 只是读取文件内容。

loader 还要负责：

```text
清洗文本
提取标题
提取 metadata
统一输出 RagDocument
处理不支持的文件类型
```

### 错误 2：清洗越狠越好

不对。

清洗不能破坏原文含义。

本节只做基础格式清洗，不改写业务内容。

### 错误 3：metadata 后面再说

不建议。

metadata 应该在 loader 阶段就开始收集。

否则后面 chunk、payload、filter、引用来源都会缺上下文。

### 错误 4：README.md 也应该进入知识库

通常不应该。

本项目里的 `data/knowledge_base/README.md` 是目录说明，不是业务知识。

如果它进入检索库，会污染检索结果。

### 错误 5：路径直接用绝对路径就行

不建议。

绝对路径包含本机信息，也不利于 GitHub、部署和引用展示。

metadata source 更适合使用相对路径或文件名。

## 本节练习

### 练习 1：判断职责

下面哪些是 loader 的职责？

```text
1. 读取 Markdown 文件。
2. 清洗换行和空白。
3. 提取文档标题。
4. 把文档切成 chunk。
5. 调用 embedding 模型。
6. 写入 Qdrant。
7. 输出 RagDocument。
```

参考答案：

```text
1、2、3、7 是 loader 的职责。
4 是 splitter 的职责。
5 是 embeddings 的职责。
6 是 vector_store 的职责。
```

### 练习 2：解释为什么要指定 UTF-8

问题：

```text
读取中文知识文档时，为什么要写 encoding="utf-8"？
```

参考答案：

```text
因为不同系统默认编码可能不同。
如果不指定编码，中文文档在不同机器上可能出现乱码或读取失败。
明确使用 UTF-8 可以让读取行为更稳定。
```

### 练习 3：解释为什么压缩过多空行

问题：

```text
为什么 clean_document_text 会把连续 3 个以上空行压缩成 2 个空行，而不是全部删除？
```

参考答案：

```text
连续过多空行通常是无意义格式噪声，会影响后续切分。
但保留 2 个换行可以保留段落边界。
如果全部删除，段落结构会丢失。
```

### 练习 4：解释为什么默认跳过 README.md

问题：

```text
为什么 load_documents_from_directory 默认不加载 README.md？
```

参考答案：

```text
因为 data/knowledge_base/README.md 是目录说明，不是业务知识文档。
如果把它写入知识库，后续检索可能返回目录说明，从而污染结果。
```

### 练习 5：说明加载结果

问题：

```text
order-shipping-policy.md 加载后，metadata 里应该至少有哪些字段？
```

参考答案：

```text
source
title
file_name
file_extension
doc_type
business_domain
permission_group
```

其中：

```text
source = order-shipping-policy.md
title = 订单发货规则
doc_type = policy
business_domain = order
permission_group = customer_service
```

## 自测问题

### 自测 1：本节为什么不需要打开虚拟机？

参考答案：

```text
因为本节只读取本地 Markdown/txt 文件，不访问 Qdrant，不启动 Docker，也不生成 embedding。
```

### 自测 2：loader 输出什么？

参考答案：

```text
loader 输出 RagDocument，里面包含清洗后的 content 和提取出来的 metadata。
```

### 自测 3：cleaning 会不会改写业务规则？

参考答案：

```text
不应该。当前 cleaning 只做换行、空白、空行这类格式清洗，不改写业务内容。
```

### 自测 4：source 为什么用相对路径或文件名？

参考答案：

```text
因为绝对路径包含本机信息，不利于引用展示和跨环境运行。相对路径或文件名更稳定。
```

### 自测 5：metadata 后续会去哪里？

参考答案：

```text
metadata 会从 RagDocument 传给 RagChunk，后续再写入 Qdrant point.payload，用于过滤、引用来源和排查。
```

### 自测 6：unsupported suffix 为什么要报错？

参考答案：

```text
因为当前 loader 只明确支持 .md 和 .txt。
如果静默接受 .pdf 或 .docx，可能让用户误以为这些格式已经被正确解析。
明确报错可以避免错误假设。
```

### 自测 7：load_document 和 load_documents_from_directory 有什么区别？

参考答案：

```text
load_document 加载单个文件。
load_documents_from_directory 批量加载一个目录下支持的文档，并默认跳过 README.md。
```

## 本节复盘

这一节你要真正掌握的是：

```text
1. loader 是 RAG 入库流程的第一步。
2. loader 负责从文件到 RagDocument。
3. loader 不负责 chunk、embedding、Qdrant。
4. 文本清洗要稳定格式，但不能改写业务含义。
5. UTF-8 对中文文档读取很重要。
6. metadata 在 loader 阶段就要开始建立。
7. README.md 默认不作为业务知识文档加载。
8. 本节输出 list[RagDocument]，下一节会进入 chunk 切分。
```

下一节可以进入：

```text
阶段 4 第 12 节：chunk 切分策略：大小、重叠、标题、段落。
```
