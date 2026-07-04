# Python 元组 tuple 和集合 set

日期：2026-07-04

对应代码：

```text
projects/python-basics/13_tuple_set.py
projects/python-basics/13_practice_tuple_set.py
```

## 1. 为什么要补元组和集合

前面已经学了：

- `list`：列表，适合保存一组有顺序、会变化的数据。
- `dict`：字典，适合保存 key-value 结构的数据。

Python 里还有两个很常用的容器：

- `tuple`：元组，适合保存固定结构的数据。
- `set`：集合，适合去重、判断是否存在、做集合运算。

后面做 AI 应用时，`set` 会很常见：

- 文档 ID 去重。
- 用户权限集合。
- 知识库标签集合。
- 检索结果交集、差集。

`tuple` 也会常见：

- 函数一次返回多个值。
- 表示固定结构，比如 `(lesson_number, lesson_title)`。
- 表示不希望被随便修改的数据。

## 2. tuple 是什么

`tuple` 中文一般叫“元组”。

可以先理解成：

```text
tuple = 不可修改的、有顺序的数据组合
```

示例：

```python
lesson = (13, "元组和集合")
```

这个元组里有两个元素：

- `13`
- `"元组和集合"`

## 3. tuple 的基本写法

```python
lesson = (13, "元组和集合")
```

访问元素：

```python
print(lesson[0])
print(lesson[1])
```

索引和列表一样，从 `0` 开始。

## 4. 只有一个元素的 tuple

这是初学者很容易错的地方。

错误理解：

```python
value = ("Python")
```

这不是 tuple，而是字符串。

正确写法：

```python
value = ("Python",)
```

关键点是后面的逗号 `,`。

## 5. tuple 不可修改

tuple 创建后，不能修改里面的元素。

```python
lesson = (13, "元组和集合")
lesson[0] = 14
```

这会报错：

```text
TypeError
```

所以 tuple 适合表示“结构固定、不应该随便改”的数据。

## 6. tuple 解包

解包就是把元组里的元素一次性拆出来。

```python
lesson = (13, "元组和集合")
lesson_number, lesson_title = lesson
```

等价于：

```python
lesson_number = lesson[0]
lesson_title = lesson[1]
```

解包的好处是代码更清楚。

## 7. 函数返回多个值

Python 函数可以看起来像返回多个值：

```python
def parse_lesson() -> tuple[int, str]:
    return 13, "元组和集合"
```

调用：

```python
number, title = parse_lesson()
```

注意，本质上返回的是一个 tuple。

## 8. set 是什么

`set` 中文一般叫“集合”。

可以先理解成：

```text
set = 不重复、无顺序的一组数据
```

示例：

```python
skills = {"Python", "Java", "Python"}
print(skills)
```

结果里只会保留一个 `"Python"`。

## 9. set 的基本写法

创建有内容的 set：

```python
skills = {"Python", "Java", "AI"}
```

判断元素是否存在：

```python
print("Python" in skills)
```

添加元素：

```python
skills.add("FastAPI")
```

删除元素：

```python
skills.discard("Java")
```

`discard()` 删除不存在的元素时不会报错。

## 10. 空 set 怎么写

空 dict：

```python
value = {}
```

空 set：

```python
value = set()
```

注意：`{}` 是空字典，不是空集合。

## 11. set 去重

列表里可能有重复数据：

```python
document_ids = ["doc-1", "doc-2", "doc-1"]
```

转换成 set：

```python
unique_ids = set(document_ids)
```

结果会去掉重复值。

AI 应用里，检索结果可能来自多个来源，同一个文档可能出现多次，这时候就可以用 set 去重。

## 12. set 没有固定顺序

set 不保证顺序。

所以这段代码每次打印顺序可能不完全一样：

```python
skills = {"Python", "Java", "AI"}
print(skills)
```

如果只是为了显示得稳定，可以用：

```python
print(sorted(skills))
```

`sorted()` 会返回一个排好序的列表。

## 13. set 集合运算

两个集合：

```python
known_topics = {"变量", "函数", "类"}
required_topics = {"函数", "类", "FastAPI"}
```

合并，也叫并集：

```python
known_topics | required_topics
```

共有，也叫交集：

```python
known_topics & required_topics
```

差异，也叫差集：

```python
required_topics - known_topics
```

在学习路线里，差集可以表示“还没学的内容”。

## 14. 权限判断里的 set

假设接口需要这些权限：

```python
required_permissions = {"read:docs", "call:ai"}
```

用户拥有这些权限：

```python
user_permissions = {"read:docs", "upload:docs"}
```

缺少权限：

```python
missing_permissions = required_permissions - user_permissions
```

如果 `missing_permissions` 不是空集合，就说明权限不足。

## 15. list、tuple、set、dict 对比

| 类型 | 中文 | 是否有顺序 | 是否可修改 | 是否允许重复 | 适合做什么 |
| --- | --- | --- | --- | --- | --- |
| `list` | 列表 | 是 | 是 | 是 | 保存一组会变化的数据 |
| `tuple` | 元组 | 是 | 否 | 是 | 保存固定结构的数据 |
| `set` | 集合 | 否 | 是 | 否 | 去重、成员判断、集合运算 |
| `dict` | 字典 | 按插入顺序保存 | 是 | key 不重复 | 保存 key-value 数据 |

## 16. 常见错误

### 错误 1：把 `("Python")` 当成 tuple

```python
value = ("Python")
```

这是字符串。

正确：

```python
value = ("Python",)
```

### 错误 2：想修改 tuple

```python
lesson = (13, "元组和集合")
lesson[0] = 14
```

tuple 不可修改，这会报错。

### 错误 3：用 `{}` 创建空 set

```python
value = {}
```

这是空字典。

正确：

```python
value = set()
```

### 错误 4：依赖 set 的顺序

set 不保证顺序，不要用 `set` 保存“必须按顺序处理”的数据。

如果需要顺序，用 `list`。

## 17. 本节练习

创建文件：

```text
projects/python-basics/13_practice_tuple_set.py
```

要求：

1. 写函数 `normalize_keyword(keyword: str) -> str`
   - 去掉左右空格。
   - 转成小写。
2. 写函数 `extract_keywords(raw_keywords: list[str]) -> set[str]`
   - 清洗关键词。
   - 去掉空字符串。
   - 自动去重。
3. 写函数 `build_learning_record(student_name, lesson, keywords)`
   - `lesson` 使用 tuple，比如 `(13, "元组和集合")`。
   - 返回一个字典。
4. 写函数 `compare_document_ids(old_ids, new_ids)`
   - 返回全部文档 ID。
   - 返回重复文档 ID。
   - 返回新增文档 ID。
5. 写函数 `check_permissions(required_permissions, user_permissions)`
   - 返回是否有权限。
   - 返回缺少的权限集合。

## 18. 练习参考答案

```python
def normalize_keyword(keyword: str) -> str:
    return keyword.strip().lower()


def extract_keywords(raw_keywords: list[str]) -> set[str]:
    keywords = set()

    for raw_keyword in raw_keywords:
        keyword = normalize_keyword(raw_keyword)
        if keyword:
            keywords.add(keyword)

    return keywords


def build_learning_record(
    student_name: str,
    lesson: tuple[int, str],
    keywords: set[str],
) -> dict[str, object]:
    lesson_number, lesson_title = lesson

    return {
        "student_name": student_name,
        "lesson_number": lesson_number,
        "lesson_title": lesson_title,
        "keywords": sorted(keywords),
    }


def compare_document_ids(old_ids: set[str], new_ids: set[str]) -> dict[str, set[str]]:
    return {
        "all_ids": old_ids | new_ids,
        "same_ids": old_ids & new_ids,
        "only_new_ids": new_ids - old_ids,
    }


def check_permissions(
    required_permissions: set[str],
    user_permissions: set[str],
) -> tuple[bool, set[str]]:
    missing_permissions = required_permissions - user_permissions
    can_access = len(missing_permissions) == 0

    return can_access, missing_permissions
```

运行：

```powershell
uv run python 13_practice_tuple_set.py
```

## 19. 自测问题

1. tuple 是什么？
2. set 是什么？
3. `("Python")` 和 `("Python",)` 有什么区别？
4. tuple 能不能修改？
5. 什么是 tuple 解包？
6. 函数返回多个值，本质上返回的是什么？
7. 空 set 应该怎么创建？
8. set 为什么适合去重？
9. `a | b`、`a & b`、`a - b` 分别表示什么？
10. list、tuple、set、dict 分别适合什么场景？

## 20. 自测参考答案

1. tuple 是什么？

   tuple 是有顺序、不可修改的数据组合，适合保存固定结构的数据。

2. set 是什么？

   set 是不重复、无固定顺序的数据集合，适合去重、成员判断和集合运算。

3. `("Python")` 和 `("Python",)` 有什么区别？

   `("Python")` 是字符串；`("Python",)` 才是只有一个元素的 tuple。

4. tuple 能不能修改？

   不能。tuple 创建后不能修改里面的元素。

5. 什么是 tuple 解包？

   解包就是把 tuple 里的多个元素一次性赋值给多个变量。

6. 函数返回多个值，本质上返回的是什么？

   本质上返回的是 tuple。

7. 空 set 应该怎么创建？

   使用 `set()`。`{}` 是空字典。

8. set 为什么适合去重？

   因为 set 天然不允许重复元素。

9. `a | b`、`a & b`、`a - b` 分别表示什么？

   `a | b` 是并集，表示合并两个集合；`a & b` 是交集，表示两个集合共有的内容；`a - b` 是差集，表示在 `a` 里但不在 `b` 里的内容。

10. list、tuple、set、dict 分别适合什么场景？

    `list` 适合保存有顺序、会变化、可重复的数据；`tuple` 适合保存有顺序、固定结构、不希望修改的数据；`set` 适合去重和集合运算；`dict` 适合保存 key-value 结构的数据。

## 21. 推荐资料

- Python 官方教程：Tuples and Sequences
  https://docs.python.org/3/tutorial/datastructures.html#tuples-and-sequences

- Python 官方教程：Sets
  https://docs.python.org/3/tutorial/datastructures.html#sets

- Python 官方文档：内置类型 set
  https://docs.python.org/3/library/stdtypes.html#set-types-set-frozenset

- Datawhale：聪明办法学 Python 第二版
  https://github.com/datawhalechina/learn-python-the-smart-way-v2
