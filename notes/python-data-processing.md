# Python 常用数据处理写法

日期：2026-07-04

对应代码：

```text
projects/python-basics/14_data_processing.py
projects/python-basics/14_practice_data_processing.py
```

## 1. 本节学什么

前面我们已经学了列表、字典、集合、循环和函数。

这一节不是学一个全新的大概念，而是学习写项目时非常常见的数据处理写法：

- 切片：从列表、字符串里取一段。
- `enumerate()`：循环时同时拿到序号和值。
- `zip()`：把两组数据一一配对。
- `sorted()` 和 `key`：按指定规则排序。
- 推导式：快速生成列表、字典、集合。
- `any()` 和 `all()`：判断一组条件是否满足。
- 可变对象和不可变对象：理解为什么有些数据会被“连带修改”。
- 浅拷贝和深拷贝：理解复制复杂数据时的区别。

这些写法以后会大量出现在：

- 清洗用户问题。
- 排序 RAG 检索结果。
- 过滤低分文档。
- 去重文档来源。
- 生成接口响应 JSON。
- 处理配置和任务列表。

## 2. 切片是什么

切片就是从一个序列里取一段。

列表、字符串、元组都可以切片。

```python
topics = ["变量", "字符串", "列表", "字典", "函数"]
```

取前三个：

```python
topics[:3]
```

取第 2 到第 4 个：

```python
topics[1:4]
```

取最后两个：

```python
topics[-2:]
```

注意：索引还是从 `0` 开始。

## 3. 切片的左闭右开

```python
topics[1:4]
```

含义是：

```text
从索引 1 开始，取到索引 4 之前
```

也就是包含索引 `1`、`2`、`3`，不包含索引 `4`。

可以记成：

```text
[开始位置:结束位置]
包括开始，不包括结束
```

## 4. 切片复制列表

```python
copied_topics = topics[:]
```

这会得到一个新的列表。

但要注意：如果列表里还有字典、列表这种嵌套对象，`[:]` 只是一层复制，不是深拷贝。

深拷贝后面会讲。

## 5. enumerate 是什么

普通循环只能直接拿到元素：

```python
for topic in topics:
    print(topic)
```

如果你想同时拿到序号和值，可以用 `enumerate()`：

```python
for index, topic in enumerate(topics, start=1):
    print(index, topic)
```

这里：

- `index` 是序号。
- `topic` 是当前元素。
- `start=1` 表示序号从 `1` 开始。

## 6. enumerate 常见用途

学习笔记编号：

```python
for index, topic in enumerate(topics, start=1):
    print(f"第 {index} 节：{topic}")
```

RAG 结果编号：

```python
for index, document in enumerate(documents, start=1):
    print(f"引用 {index}: {document['title']}")
```

比自己手动写 `count = count + 1` 更清楚。

## 7. zip 是什么

`zip()` 用来把多组数据按位置配对。

```python
questions = ["什么是 list？", "什么是 dict？"]
answers = ["列表", "字典"]
```

配对：

```python
for question, answer in zip(questions, answers):
    print(question, answer)
```

结果类似：

```text
什么是 list？ 列表
什么是 dict？ 字典
```

## 8. zip 的注意点

如果两个列表长度不一样，`zip()` 会以短的那个为准。

```python
questions = ["Q1", "Q2", "Q3"]
answers = ["A1", "A2"]
```

`zip(questions, answers)` 只会配出两组。

所以在真实项目里，如果长度必须一致，要先检查：

```python
if len(questions) != len(answers):
    raise ValueError("问题和答案数量不一致")
```

## 9. sorted 是什么

`sorted()` 用来排序。

简单排序：

```python
scores = [0.8, 0.95, 0.6]
print(sorted(scores))
```

从大到小排序：

```python
print(sorted(scores, reverse=True))
```

## 10. sorted + key

如果列表里放的是字典，Python 不知道应该按哪个字段排序。

例如：

```python
documents = [
    {"title": "Python 变量", "score": 0.68},
    {"title": "Python 函数", "score": 0.92},
]
```

我们要告诉 Python：按 `score` 排。

```python
def get_score(document: dict[str, object]) -> float:
    return float(document["score"])


sorted_documents = sorted(documents, key=get_score, reverse=True)
```

这里 `key=get_score` 的意思是：

```text
排序时，每个 document 先交给 get_score，拿到分数，再按分数排序
```

RAG 检索结果排序会经常用到这个思路。

## 11. 列表推导式

列表推导式是用一行代码生成新列表。

普通写法：

```python
cleaned_topics = []

for topic in raw_topics:
    if topic.strip():
        cleaned_topics.append(topic.strip().lower())
```

推导式写法：

```python
cleaned_topics = [topic.strip().lower() for topic in raw_topics if topic.strip()]
```

可以先读成：

```text
对 raw_topics 里的每个 topic：
如果 topic.strip() 不为空，
就把 topic.strip().lower() 放进新列表
```

## 12. 字典推导式

```python
topics = ["python", "java", "ai"]
topic_lengths = {topic: len(topic) for topic in topics}
```

结果：

```python
{"python": 6, "java": 4, "ai": 2}
```

这适合把一组数据加工成 key-value。

## 13. 集合推导式

```python
raw_topics = ["Python", "python", "Java"]
unique_topics = {topic.lower() for topic in raw_topics}
```

结果会去重：

```python
{"python", "java"}
```

因为集合天然不允许重复。

## 14. 推导式什么时候不要用

推导式适合简单逻辑。

如果逻辑很复杂，不要硬写成一行。

这种时候普通 `for` 循环更清楚：

```python
result = []

for item in items:
    if 条件1:
        ...
    if 条件2:
        ...
    result.append(...)
```

代码不是越短越好，初学阶段优先保证能读懂。

## 15. any 和 all

`any()`：只要有一个满足条件，就返回 `True`。

```python
scores = [0.91, 0.82, 0.65]
any(score >= 0.9 for score in scores)
```

`all()`：必须全部满足条件，才返回 `True`。

```python
all(score >= 0.6 for score in scores)
```

AI 应用里的例子：

```python
has_high_score = any(score >= 0.8 for score in scores)
all_passed = all(score >= 0.5 for score in scores)
```

## 16. 可变对象和不可变对象

Python 里的数据大致可以分成两类：

- 不可变对象：创建后不能原地修改。
- 可变对象：创建后可以原地修改。

常见不可变对象：

- `int`
- `float`
- `str`
- `bool`
- `tuple`

常见可变对象：

- `list`
- `dict`
- `set`

## 17. 不可变对象示例

```python
a = 10
b = a
a = a + 1
```

这时：

```text
a 是 11
b 还是 10
```

因为数字不可变，`a = a + 1` 不是修改原来的 `10`，而是让 `a` 指向新的 `11`。

## 18. 可变对象示例

```python
skills_a = ["Python", "Java"]
skills_b = skills_a
skills_a.append("AI")
```

这时：

```text
skills_a 是 ["Python", "Java", "AI"]
skills_b 也是 ["Python", "Java", "AI"]
```

因为 `skills_a` 和 `skills_b` 指向的是同一个列表。

## 19. 为什么可变对象容易出 bug

如果你把一个列表传给函数，函数内部修改了它，外面的列表也会变。

```python
def add_skill(skills: list[str]) -> None:
    skills.append("AI")
```

调用：

```python
my_skills = ["Python"]
add_skill(my_skills)
```

`my_skills` 会变成：

```python
["Python", "AI"]
```

这不一定是错，但你必须知道它会发生。

## 20. 浅拷贝

浅拷贝只复制最外层容器。

```python
new_list = old_list.copy()
```

或：

```python
new_list = old_list[:]
```

如果列表里只是字符串、数字，浅拷贝通常够用。

如果列表里还有字典、列表这种嵌套对象，浅拷贝不够。

## 21. 浅拷贝的问题

```python
plan = {
    "tasks": [
        {"name": "学习列表", "done": False}
    ]
}

new_plan = plan.copy()
new_plan["tasks"][0]["done"] = True
```

这会影响原来的 `plan`。

原因是：

```text
plan 和 new_plan 的最外层字典不同，
但里面的 tasks 列表还是同一个对象。
```

## 22. 深拷贝

深拷贝会连嵌套对象一起复制。

```python
from copy import deepcopy

new_plan = deepcopy(plan)
```

修改 `new_plan` 里的嵌套内容，不会影响原来的 `plan`。

真实项目里，如果你要“基于旧数据生成新数据，但不能改坏旧数据”，就要考虑深拷贝。

## 23. 本节练习

创建文件：

```text
projects/python-basics/14_practice_data_processing.py
```

要求：

1. 写函数 `clean_topics(raw_topics: list[str]) -> list[str]`
   - 去掉空字符串。
   - 去掉左右空格。
   - 转成小写。
2. 写函数 `number_topics(topics: list[str]) -> list[str]`
   - 用 `enumerate()` 给主题编号。
3. 写函数 `pair_questions_and_answers(questions, answers)`
   - 用 `zip()` 把问题和答案配成字典列表。
4. 写函数 `filter_and_sort_documents(documents, min_score, top_k)`
   - 过滤低分文档。
   - 按 `score` 从高到低排序。
   - 只返回前 `top_k` 个。
5. 写函数 `collect_sources(documents)`
   - 从文档列表里收集来源。
   - 用 set 去重。
6. 写函数 `update_task_safely(plan, task_index, done)`
   - 用深拷贝生成新计划。
   - 修改新计划里的任务状态。
   - 不影响原计划。

## 24. 练习参考答案

```python
from copy import deepcopy


def clean_topics(raw_topics: list[str]) -> list[str]:
    return [topic.strip().lower() for topic in raw_topics if topic.strip()]


def number_topics(topics: list[str]) -> list[str]:
    result = []

    for index, topic in enumerate(topics, start=1):
        result.append(f"{index}. {topic}")

    return result


def pair_questions_and_answers(
    questions: list[str],
    answers: list[str],
) -> list[dict[str, str]]:
    pairs = []

    for question, answer in zip(questions, answers):
        pairs.append(
            {
                "question": question,
                "answer": answer,
            }
        )

    return pairs


def get_score(document: dict[str, object]) -> float:
    score = document.get("score", 0.0)

    if isinstance(score, int | float):
        return float(score)

    return 0.0


def filter_and_sort_documents(
    documents: list[dict[str, object]],
    min_score: float,
    top_k: int,
) -> list[dict[str, object]]:
    valid_documents = [
        document
        for document in documents
        if get_score(document) >= min_score
    ]

    sorted_documents = sorted(valid_documents, key=get_score, reverse=True)
    return sorted_documents[:top_k]


def collect_sources(documents: list[dict[str, object]]) -> set[str]:
    sources = set()

    for document in documents:
        source = document.get("source")
        if isinstance(source, str) and source:
            sources.add(source)

    return sources


def update_task_safely(plan: dict[str, object], task_index: int, done: bool) -> dict[str, object]:
    new_plan = deepcopy(plan)
    tasks = new_plan.get("tasks", [])

    if isinstance(tasks, list) and 0 <= task_index < len(tasks):
        task = tasks[task_index]
        if isinstance(task, dict):
            task["done"] = done

    return new_plan
```

运行：

```powershell
uv run python 14_practice_data_processing.py
```

## 25. 自测问题

1. 什么是切片？
2. `topics[1:4]` 包含索引 4 吗？
3. `enumerate()` 解决什么问题？
4. `zip()` 解决什么问题？
5. `zip()` 遇到两个列表长度不一样时会怎样？
6. `sorted(documents, key=get_score, reverse=True)` 是什么意思？
7. 列表推导式适合什么场景？
8. `any()` 和 `all()` 有什么区别？
9. list、dict、set 是可变对象还是不可变对象？
10. 浅拷贝和深拷贝有什么区别？

## 26. 自测参考答案

1. 什么是切片？

   切片是从列表、字符串、元组等序列里取出一段数据。

2. `topics[1:4]` 包含索引 4 吗？

   不包含。切片是左闭右开，包含开始位置，不包含结束位置。

3. `enumerate()` 解决什么问题？

   它能在循环时同时拿到序号和值，避免自己手动维护计数器。

4. `zip()` 解决什么问题？

   它能把多组数据按位置一一配对。

5. `zip()` 遇到两个列表长度不一样时会怎样？

   它会以最短的那组数据为准，多出来的元素不会参与配对。

6. `sorted(documents, key=get_score, reverse=True)` 是什么意思？

   表示排序时先用 `get_score()` 取出每个文档的分数，再按分数从高到低排序。

7. 列表推导式适合什么场景？

   适合用简单逻辑从旧列表生成新列表，比如清洗、过滤、转换数据。

8. `any()` 和 `all()` 有什么区别？

   `any()` 是只要有一个条件满足就返回 `True`；`all()` 是所有条件都满足才返回 `True`。

9. list、dict、set 是可变对象还是不可变对象？

   它们都是可变对象，可以原地修改。

10. 浅拷贝和深拷贝有什么区别？

    浅拷贝只复制最外层容器，嵌套对象仍然共享；深拷贝会把嵌套对象也复制出来，修改新对象不会影响原对象。

## 27. 推荐资料

- Python 官方教程：More on Lists
  https://docs.python.org/3/tutorial/datastructures.html#more-on-lists

- Python 官方教程：Looping Techniques
  https://docs.python.org/3/tutorial/datastructures.html#looping-techniques

- Python 官方文档：sorted
  https://docs.python.org/3/library/functions.html#sorted

- Python 官方文档：copy
  https://docs.python.org/3/library/copy.html
