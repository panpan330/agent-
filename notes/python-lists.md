# Python 列表 list

日期：2026-07-04

对应代码：

```text
projects/python-basics/03_lists.py
projects/python-basics/03_practice_task_list.py
```

## 1. 列表是什么

列表是 Python 里用来**按顺序保存多个值**的数据类型。

类型名是：

```python
list
```

示例：

```python
tasks = ["学习变量", "学习字符串", "学习列表"]
```

这里 `tasks` 不是一个值，而是一组值。

列表里的每个值叫元素。

## 2. 为什么需要列表

如果没有列表，多个任务只能这样写：

```python
task1 = "学习变量"
task2 = "学习字符串"
task3 = "学习列表"
```

这样很难统一处理。

有了列表，可以这样写：

```python
tasks = ["学习变量", "学习字符串", "学习列表"]
```

后面就可以统一：

- 遍历所有任务。
- 添加任务。
- 删除任务。
- 统计数量。
- 取前几个任务。

AI 应用里也会大量用列表：

```python
messages = [
    "system: 你是一个 Python 老师",
    "user: 请解释列表",
    "assistant: 列表是按顺序保存多个值的容器",
]
```

RAG 里也会有：

```python
chunks = [
    "第一段文档内容",
    "第二段文档内容",
    "第三段文档内容",
]
```

## 3. 创建列表

列表用中括号 `[]`。

```python
numbers = [1, 2, 3]
names = ["Tom", "Jerry", "Alice"]
empty = []
```

空列表表示现在还没有元素，后面可以继续添加。

## 4. 访问列表元素

列表有顺序，所以可以用索引取元素。

```python
tasks = ["学习变量", "学习字符串", "学习列表"]
```

取第一个：

```python
tasks[0]
```

结果：

```text
学习变量
```

取最后一个：

```python
tasks[-1]
```

结果：

```text
学习列表
```

注意：索引从 0 开始。

## 5. 修改列表元素

可以通过索引修改元素：

```python
tasks[0] = "复习变量和类型"
```

修改后：

```python
["复习变量和类型", "学习字符串", "学习列表"]
```

这点和字符串不同。字符串不可变，列表可变。

## 6. 添加元素 append()

`append()` 会把新元素加到列表末尾。

```python
tasks.append("学习字典")
```

注意：`append()` 会直接修改原列表。

## 7. 删除元素 remove()

`remove()` 按值删除。

```python
tasks.remove("学习字符串")
```

意思是：从列表里删除值为 `"学习字符串"` 的元素。

如果列表里没有这个值，会报错。

## 8. 删除并取出元素 pop()

`pop()` 会删除并返回元素。

```python
last_task = tasks.pop()
```

不传参数时，默认删除最后一个。

也可以指定索引：

```python
first_task = tasks.pop(0)
```

这会删除并返回第一个元素。

## 9. 列表长度 len()

`len()` 用来获取列表元素数量。

```python
len(tasks)
```

示例：

```python
tasks = ["学习变量", "学习列表"]
print(len(tasks))
```

输出：

```text
2
```

## 10. 遍历列表 for

遍历就是一个一个拿出来处理。

```python
for task in tasks:
    print(task)
```

含义：

```text
每次从 tasks 里取一个元素，临时命名为 task，然后执行缩进里的代码。
```

## 11. 带编号遍历 enumerate()

如果既要元素，又要编号，可以用 `enumerate()`。

```python
for index, task in enumerate(tasks, start=1):
    print(f"{index}. {task}")
```

`start=1` 表示编号从 1 开始，更适合展示给人看。

注意：列表真正的索引仍然从 0 开始。

## 12. 判断元素是否存在 in

```python
"学习列表" in tasks
```

结果是布尔值：

```text
True 或 False
```

常用于：

- 判断任务是否存在。
- 判断某个关键词是否在列表里。
- 判断某个检索结果是否包含目标内容。

## 13. 列表切片

切片用来取出列表的一部分。

```python
ai_steps = ["Python 基础", "FastAPI", "LangChain", "RAG", "LangGraph"]
```

取前两个：

```python
ai_steps[0:2]
```

结果：

```python
["Python 基础", "FastAPI"]
```

从第 3 个到最后：

```python
ai_steps[2:]
```

结果：

```python
["LangChain", "RAG", "LangGraph"]
```

最后两个：

```python
ai_steps[-2:]
```

结果：

```python
["RAG", "LangGraph"]
```

## 14. 列表可以放不同类型，但不建议乱放

Python 允许：

```python
mixed = ["Panpan", 25, True, None]
```

但是在真实项目里，如果一个列表里类型太乱，会很难维护。

更推荐一个列表里放同一类数据：

```python
tasks = ["学习变量", "学习字符串", "学习列表"]
scores = [90, 85, 100]
```

## 15. 常见错误

### 错误 1：索引越界

```python
tasks = ["学习变量", "学习列表"]
print(tasks[5])
```

列表没有第 6 个元素，会报错。

### 错误 2：remove 删除不存在的值

```python
tasks.remove("学习 FastAPI")
```

如果列表里没有 `"学习 FastAPI"`，会报错。

更稳的写法：

```python
if "学习 FastAPI" in tasks:
    tasks.remove("学习 FastAPI")
```

### 错误 3：搞混索引和值

```python
tasks.pop("学习变量")
```

这是错误的。

`pop()` 要的是索引，不是值。

按值删除用：

```python
tasks.remove("学习变量")
```

按索引删除并取出用：

```python
tasks.pop(0)
```

### 错误 4：遍历时变量名不清楚

不推荐：

```python
for x in tasks:
    print(x)
```

更推荐：

```python
for task in tasks:
    print(task)
```

变量名清楚，别人更容易看懂。

## 16. 本节练习

创建文件：

```text
projects/python-basics/03_practice_task_list.py
```

要求：

1. 创建学习任务列表：

   ```python
   tasks = ["学习变量", "学习字符串", "学习列表"]
   ```

2. 添加 `"学习字典"`。
3. 添加 `"学习函数"`。
4. 删除 `"学习字符串"`。
5. 用 `pop(0)` 取出第一个任务，表示已经完成。
6. 打印剩余任务。
7. 打印任务数量。
8. 判断是否包含 `"学习列表"`。
9. 判断是否包含 `"学习 FastAPI"`。
10. 打印前两个任务。
11. 用 `enumerate()` 带编号打印所有任务。

## 17. 练习参考答案

```python
def main() -> None:
    tasks = ["学习变量", "学习字符串", "学习列表"]

    print("初始任务:", tasks)

    tasks.append("学习字典")
    tasks.append("学习函数")
    print("添加任务后:", tasks)

    tasks.remove("学习字符串")
    print("删除学习字符串后:", tasks)

    finished_task = tasks.pop(0)
    print("完成的任务:", finished_task)
    print("剩余任务:", tasks)

    print("任务数量:", len(tasks))
    print("是否包含学习列表:", "学习列表" in tasks)
    print("是否包含学习 FastAPI:", "学习 FastAPI" in tasks)

    print("前两个任务:", tasks[0:2])

    print("带编号的任务列表:")
    for index, task in enumerate(tasks, start=1):
        print(f"{index}. {task}")


if __name__ == "__main__":
    main()
```

运行：

```powershell
uv run python 03_practice_task_list.py
```

## 18. 自测问题

1. 列表是什么？
2. 列表用什么符号创建？
3. `tasks[0]` 取的是第几个元素？
4. `tasks[-1]` 表示什么？
5. `append()` 做什么？
6. `remove()` 和 `pop()` 有什么区别？
7. `len(tasks)` 返回什么？
8. `for task in tasks` 是什么意思？
9. `enumerate(tasks, start=1)` 解决什么问题？
10. `tasks[0:2]` 为什么只取前两个？
11. 列表和字符串最大的一个区别是什么？

## 19. 自测参考答案

1. 列表是什么？

   列表是按顺序保存多个值的数据类型，类型名是 `list`。

2. 列表用什么符号创建？

   用中括号 `[]` 创建。

3. `tasks[0]` 取的是第几个元素？

   取第 1 个元素，因为列表索引从 0 开始。

4. `tasks[-1]` 表示什么？

   表示取最后一个元素。

5. `append()` 做什么？

   把一个新元素添加到列表末尾。

6. `remove()` 和 `pop()` 有什么区别？

   `remove()` 按值删除；`pop()` 按索引删除，并返回被删除的元素。

7. `len(tasks)` 返回什么？

   返回列表里的元素数量。

8. `for task in tasks` 是什么意思？

   逐个从 `tasks` 里取出元素，每次临时命名为 `task`，然后执行循环体里的代码。

9. `enumerate(tasks, start=1)` 解决什么问题？

   它可以在遍历时同时拿到编号和元素，`start=1` 让编号从 1 开始。

10. `tasks[0:2]` 为什么只取前两个？

    切片包含开始位置 0，不包含结束位置 2，所以取索引 0 和 1。

11. 列表和字符串最大的一个区别是什么？

    列表是可变的，可以修改、添加、删除元素；字符串不可变，字符串方法通常返回新字符串。

## 20. 推荐资料

- Python 官方教程：Lists  
  https://docs.python.org/3/tutorial/introduction.html#lists

- Python 官方教程：More on Lists  
  https://docs.python.org/3/tutorial/datastructures.html#more-on-lists

- Python 官方文档：Sequence Types  
  https://docs.python.org/3/library/stdtypes.html#sequence-types-list-tuple-range

- Datawhale：聪明办法学 Python 第二版  
  https://github.com/datawhalechina/learn-python-the-smart-way-v2
