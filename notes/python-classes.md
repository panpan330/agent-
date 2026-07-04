# Python 类和对象 class

日期：2026-07-04

对应代码：

```text
projects/python-basics/12_classes.py
projects/python-basics/12_practice_learning_task.py
```

## 1. 类是什么

类是用来描述一类对象的模板。

例如“学习任务”都有：

- 名称。
- 是否完成。
- 标记完成的方法。
- 转成字典的方法。

就可以定义一个类：

```python
class LearningTask:
    ...
```

可以先理解成：

```text
类 = 创建对象的模板
```

## 2. 对象是什么

对象是根据类创建出来的具体数据。

```python
task = LearningTask("学习 class")
```

这里：

- `LearningTask` 是类。
- `task` 是对象。
- `"学习 class"` 是这个对象的具体数据。

## 3. 为什么需要类

字典也能表示任务：

```python
task = {
    "name": "学习 class",
    "done": False,
}
```

但字典只有数据，没有固定行为。

类可以把数据和行为放在一起：

```python
task.mark_done()
task.to_dict()
```

后面 Pydantic、FastAPI、LangChain 里会看到很多类。

## 4. class 基本写法

```python
class LearningTask:
    def __init__(self, name: str, done: bool = False) -> None:
        self.name = name
        self.done = done
```

注意：

- 类名通常用大驼峰：`LearningTask`。
- 类里面的函数叫方法。
- 方法第一个参数通常是 `self`。

## 5. `__init__` 是什么

`__init__` 是初始化方法。

创建对象时会自动调用。

```python
task = LearningTask("学习 class")
```

会执行：

```python
def __init__(self, name: str, done: bool = False) -> None:
    self.name = name
    self.done = done
```

它负责给对象设置初始属性。

## 6. self 是什么

`self` 表示当前对象自己。

```python
self.name = name
self.done = done
```

意思是：

```text
把传进来的 name 保存到当前对象的 name 属性上
把传进来的 done 保存到当前对象的 done 属性上
```

调用方法时不需要手动传 `self`：

```python
task.mark_done()
```

Python 会自动把 `task` 作为 `self` 传进去。

## 7. 属性

属性是对象身上的数据。

```python
task.name
task.done
```

示例：

```python
task = LearningTask("学习 class")
print(task.name)
print(task.done)
```

## 8. 方法

方法是对象身上的函数。

```python
def mark_done(self) -> None:
    self.done = True
```

调用：

```python
task.mark_done()
```

这个方法会修改对象的 `done` 属性。

## 9. 对象转字典

真实项目里，经常需要把对象转成字典，再转 JSON。

```python
def to_dict(self) -> dict[str, object]:
    return {
        "name": self.name,
        "done": self.done,
    }
```

调用：

```python
task.to_dict()
```

## 10. `__repr__` 是什么

直接打印对象时，如果没有 `__repr__`，可能看到：

```text
<__main__.LearningTask object at 0x...>
```

这不容易读。

可以定义：

```python
def __repr__(self) -> str:
    return f"LearningTask(name={self.name!r}, done={self.done!r})"
```

这样打印对象更清楚。

## 11. 类和字典的区别

字典：

```python
task_dict = {"name": "学习字典形式任务", "done": False}
print(task_dict["name"])
```

对象：

```python
task_object = LearningTask("学习对象形式任务")
print(task_object.name)
```

对比：

| 对比 | 字典 | 类对象 |
| --- | --- | --- |
| 数据访问 | `task["name"]` | `task.name` |
| 行为方法 | 没有固定方法 | 可以定义方法 |
| 结构约束 | 较弱 | 更清晰 |
| 适合场景 | 简单数据、JSON | 有数据也有行为 |

## 12. 类和 Pydantic BaseModel 的关系

后面 Pydantic 会这样写：

```python
class ChatRequest(BaseModel):
    question: str
    stream: bool = False
```

这也是类。

区别是：

- 普通类需要自己写 `__init__`、校验、转字典。
- Pydantic 的 `BaseModel` 会帮你做初始化、类型校验、转字典、生成 JSON schema。

所以现在学 class，是为了后面看懂 Pydantic。

## 13. 常见错误

### 错误 1：忘记 self

错误：

```python
class Task:
    def mark_done():
        ...
```

正确：

```python
class Task:
    def mark_done(self) -> None:
        ...
```

### 错误 2：把类和对象搞混

类：

```python
LearningTask
```

对象：

```python
task = LearningTask("学习 class")
```

类是模板，对象是具体实例。

### 错误 3：访问属性写错

对象访问属性：

```python
task.name
```

字典访问字段：

```python
task_dict["name"]
```

不要混用。

### 错误 4：类里逻辑太复杂

初学阶段不要把所有逻辑都塞进类。

先保持类简单：

- 保存数据。
- 提供少量方法。
- 能转成字典。

## 14. 本节练习

创建文件：

```text
projects/python-basics/12_practice_learning_task.py
```

要求：

1. 定义 `LearningTask` 类。
2. `__init__` 接收：
   - `name`
   - `topic`
   - `done`
3. 添加 `mark_done()` 方法。
4. 添加 `to_dict()` 方法。
5. 添加 `__repr__()` 方法。
6. 创建任务对象列表。
7. 把最后一个任务标记完成。
8. 写函数统计完成数量。
9. 写函数把任务对象列表转成字典列表。

## 15. 练习参考答案

```python
class LearningTask:
    def __init__(self, name: str, topic: str, done: bool = False) -> None:
        self.name = name
        self.topic = topic
        self.done = done

    def mark_done(self) -> None:
        self.done = True

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "topic": self.topic,
            "done": self.done,
        }

    def __repr__(self) -> str:
        return f"LearningTask(name={self.name!r}, topic={self.topic!r}, done={self.done!r})"


def count_done_tasks(tasks: list[LearningTask]) -> int:
    count = 0
    for task in tasks:
        if task.done:
            count += 1
    return count


def tasks_to_dicts(tasks: list[LearningTask]) -> list[dict[str, object]]:
    result = []
    for task in tasks:
        result.append(task.to_dict())
    return result


def main() -> None:
    tasks = [
        LearningTask("学习变量", "Python 基础", done=True),
        LearningTask("学习函数", "Python 基础", done=True),
        LearningTask("学习 class", "Python 基础"),
    ]

    print("原始任务:")
    print(tasks)

    tasks[2].mark_done()

    print("完成数量:", count_done_tasks(tasks))
    print("字典列表:")
    print(tasks_to_dicts(tasks))


if __name__ == "__main__":
    main()
```

运行：

```powershell
uv run python 12_practice_learning_task.py
```

## 16. 自测问题

1. 类是什么？
2. 对象是什么？
3. `__init__` 什么时候执行？
4. `self` 表示什么？
5. 属性是什么？
6. 方法是什么？
7. 类和字典有什么区别？
8. `to_dict()` 常用于什么？
9. `__repr__()` 解决什么问题？
10. 为什么学 Pydantic 前要先理解 class？

## 17. 自测参考答案

1. 类是什么？

   类是创建对象的模板，用来描述一类对象有哪些数据和行为。

2. 对象是什么？

   对象是根据类创建出来的具体实例。

3. `__init__` 什么时候执行？

   创建对象时自动执行，用来初始化对象属性。

4. `self` 表示什么？

   `self` 表示当前对象自己。

5. 属性是什么？

   属性是对象身上的数据，比如 `task.name`、`task.done`。

6. 方法是什么？

   方法是定义在类里的函数，用来操作对象的数据或提供对象行为。

7. 类和字典有什么区别？

   字典主要保存 key-value 数据；类对象既能保存数据，也能定义方法。

8. `to_dict()` 常用于什么？

   常用于把对象转换成字典，方便后续转 JSON、返回接口响应或保存文件。

9. `__repr__()` 解决什么问题？

   它让对象被打印时显示更清楚的文本，而不是内存地址。

10. 为什么学 Pydantic 前要先理解 class？

    因为 Pydantic 的 `BaseModel` 本质上也是通过类定义数据模型和字段。

## 18. 推荐资料

- Python 官方教程：Classes
  https://docs.python.org/3/tutorial/classes.html

- Python 官方文档：Data model
  https://docs.python.org/3/reference/datamodel.html

- Datawhale：聪明办法学 Python 第二版
  https://github.com/datawhalechina/learn-python-the-smart-way-v2
