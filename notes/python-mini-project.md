# Python 基础综合项目：Learning Task Assistant

日期：2026-07-05

对应代码：

```text
projects/python-basics/learning_task_assistant/
projects/python-basics/lesson22_mini_project_demo.py
projects/python-basics/test_lesson22_mini_project.py
```

## 1. 为什么要做综合项目

前面我们已经学了很多单点知识。

如果只停留在单文件练习，容易出现一个问题：

```text
每个语法点都看过，但不知道怎么组合成一个项目。
```

这个综合项目的目标就是把基础知识串起来：

- 类和对象。
- 函数。
- 类型提示。
- 字典、列表、元组、集合。
- 正则表达式。
- JSON 文件读写。
- pathlib 路径处理。
- logging 日志。
- 异常处理。
- pytest 测试。
- async/await 异步模拟。
- 模块拆分和包结构。

## 2. 项目做什么

项目名：

```text
Learning Task Assistant
```

它做几件事：

1. 管理学习任务。
2. 把任务保存到 JSON 文件。
3. 从用户问题里提取订单号。
4. 按规则分类问题。
5. 提取学习关键词。
6. 统计任务完成情况。
7. 模拟异步查询用户上下文。
8. 用 pytest 测试核心逻辑。

这个项目不是为了做一个漂亮界面，而是为了练工程组织能力。

## 3. 目录结构

```text
projects/python-basics/
  learning_task_assistant/
    __init__.py
    models.py
    rules.py
    storage.py
    service.py
    async_service.py
  lesson22_mini_project_demo.py
  test_lesson22_mini_project.py
```

每个文件有明确职责。

这比把全部代码塞进一个文件更接近真实项目。

## 4. __init__.py 是什么

```text
learning_task_assistant/__init__.py
```

这个文件表示：

```text
learning_task_assistant 是一个 Python 包
```

有了它，就可以这样导入：

```python
from learning_task_assistant.service import LearningTaskAssistant
```

后面 FastAPI 项目也会使用包结构。

## 5. models.py：数据模型

`models.py` 放数据结构。

本项目有两个模型：

```python
LearningTask
QuestionAnalysis
```

`LearningTask` 表示一个学习任务。

字段包括：

- `task_id`
- `title`
- `topic`
- `done`
- `created_at`

## 6. dataclass 是什么

本项目用了：

```python
from dataclasses import dataclass
```

`@dataclass` 可以减少样板代码。

例如：

```python
@dataclass
class LearningTask:
    task_id: str
    title: str
    topic: str
```

Python 会帮你生成初始化方法。

你可以先理解成：

```text
dataclass = 适合保存数据的简化 class 写法
```

## 7. __post_init__ 是什么

`dataclass` 创建对象后，会自动调用 `__post_init__()`。

本项目用它做数据清洗和校验：

```python
def __post_init__(self) -> None:
    self.title = self.title.strip()
    self.topic = self.topic.strip()

    if not self.title:
        raise ValueError("title is required")
```

这样可以保证任务对象一创建就比较干净。

## 8. to_dict 和 from_dict

对象不能直接保存成 JSON。

所以要先转成字典：

```python
task.to_dict()
```

从 JSON 读出来的是字典。

所以要能从字典恢复对象：

```python
LearningTask.from_dict(data)
```

这就是对象和 JSON 之间的转换。

## 9. rules.py：规则函数

`rules.py` 放纯规则逻辑。

包括：

- `normalize_text()`
- `extract_order_ids()`
- `classify_question()`
- `extract_keywords()`

这些函数不读文件，不保存数据，只负责处理输入并返回结果。

这种函数很容易测试。

## 10. 正则提取订单号

```python
ORDER_ID_PATTERN = r"ORD-\d{8}-\d{3}"
```

提取：

```python
re.findall(ORDER_ID_PATTERN, text)
```

去重但保留顺序：

```python
tuple(dict.fromkeys(order_ids))
```

这里用到了：

- 正则。
- tuple。
- dict key 不重复。

## 11. storage.py：文件读写

`storage.py` 负责 JSON 文件读写。

读取：

```python
load_tasks(path)
```

保存：

```python
save_tasks(path, tasks)
```

它用到了：

- `pathlib.Path`
- `json.load`
- `json.dump`
- 异常校验

## 12. service.py：业务服务

`service.py` 放主要业务逻辑。

核心类：

```python
class LearningTaskAssistant:
    ...
```

它负责：

- 添加任务。
- 查找任务。
- 标记完成。
- 分析问题。
- 统计任务。
- 保存数据。

可以理解成：

```text
service = 把模型、规则、存储组合起来的业务层
```

## 13. async_service.py：异步模拟

这个文件模拟异步查询：

```python
async def fake_fetch_user(user_id: int, delay: float = 0.05):
    await asyncio.sleep(delay)
```

然后用：

```python
await asyncio.gather(...)
```

并发获取用户信息和权限。

后面真实项目里，这些可能变成：

- 查 Java 用户服务。
- 查权限接口。
- 查订单接口。
- 调模型接口。

## 14. demo 入口

运行：

```powershell
uv run python lesson22_mini_project_demo.py
```

它会：

1. 创建 assistant。
2. 添加任务。
3. 标记任务完成。
4. 分析一个用户问题。
5. 异步查询用户上下文。
6. 保存 JSON。
7. 打印结果。

## 15. pytest 测试

测试文件：

```text
test_lesson22_mini_project.py
```

覆盖：

- 数据模型校验。
- 对象和字典转换。
- 正则和分类规则。
- JSON 保存和读取。
- assistant 添加、完成、统计。
- 重复任务和缺失任务异常。
- 异步用户上下文。

运行：

```powershell
uv run pytest test_lesson22_mini_project.py -q
```

## 16. 这个项目对应真实项目里的什么

现在这个小项目很简单，但结构已经接近真实后端：

| 当前项目 | 真实 FastAPI 项目 |
| --- | --- |
| `models.py` | Pydantic 模型、数据库模型 |
| `rules.py` | 文本规则、分类规则 |
| `storage.py` | 数据库访问、文件存储 |
| `service.py` | 业务服务层 |
| `async_service.py` | 异步调用模型、Java API、数据库 |
| `test_*.py` | 自动化测试 |

所以这个项目是进入 FastAPI 前的过渡。

## 17. 你应该能解释什么

完成本项目后，你要能解释：

1. 为什么要拆模块。
2. `__init__.py` 的作用。
3. 数据模型为什么要校验。
4. 对象为什么要转字典才能保存 JSON。
5. 为什么规则函数容易测试。
6. service 层负责什么。
7. 异步函数适合处理什么。
8. pytest 怎么保证项目功能不被改坏。

## 18. 本节练习

你可以尝试自己扩展：

1. 给任务增加 `priority` 字段。
2. 增加按 topic 筛选任务的函数。
3. 增加删除任务的函数。
4. 增加导出报告 JSON 的函数。
5. 给新增功能补 pytest 测试。

## 19. 自测问题

1. 为什么综合项目要拆成多个模块？
2. `__init__.py` 有什么作用？
3. `dataclass` 适合什么场景？
4. 为什么要写 `to_dict()`？
5. 为什么要写 `from_dict()`？
6. `rules.py` 为什么适合放纯函数？
7. `service.py` 负责什么？
8. `storage.py` 负责什么？
9. `async_service.py` 里的 `asyncio.gather()` 有什么作用？
10. 为什么综合项目必须写 pytest？

## 20. 自测参考答案

1. 为什么综合项目要拆成多个模块？

   因为不同代码有不同职责，拆开后更清楚、更容易测试，也更接近真实项目结构。

2. `__init__.py` 有什么作用？

   它表示目录是 Python 包，让这个目录里的模块可以被正常导入。

3. `dataclass` 适合什么场景？

   适合定义主要用来保存数据的类，可以减少手写初始化方法等样板代码。

4. 为什么要写 `to_dict()`？

   因为对象不能直接保存成 JSON，通常要先转成字典。

5. 为什么要写 `from_dict()`？

   因为从 JSON 读出来的是字典，需要把字典恢复成对象，方便后续调用对象方法。

6. `rules.py` 为什么适合放纯函数？

   纯函数输入清楚、输出清楚，不依赖外部状态，容易测试和复用。

7. `service.py` 负责什么？

   它负责组合模型、规则和存储，完成主要业务流程。

8. `storage.py` 负责什么？

   它负责数据持久化，比如从 JSON 文件读取任务、把任务保存到 JSON 文件。

9. `async_service.py` 里的 `asyncio.gather()` 有什么作用？

   它可以并发等待多个互不依赖的异步任务完成。

10. 为什么综合项目必须写 pytest？

    因为综合项目包含多个模块和业务流程，测试能验证它们组合后是否仍然符合预期，也能防止后续修改破坏旧功能。

## 21. 推荐资料

- Python 官方文档：dataclasses
  https://docs.python.org/3/library/dataclasses.html

- Python 官方文档：Modules
  https://docs.python.org/3/tutorial/modules.html

- Python 官方文档：Packages
  https://docs.python.org/3/tutorial/modules.html#packages

- pytest 官方文档
  https://docs.pytest.org/
