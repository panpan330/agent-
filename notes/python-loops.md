# Python 循环 for / while

日期：2026-07-04

对应代码：

```text
projects/python-basics/06_loops.py
projects/python-basics/06_practice_batch_tasks.py
```

## 1. 循环是什么

循环就是让程序重复执行一段代码。

如果没有循环，处理多个任务只能这样写：

```python
print(tasks[0])
print(tasks[1])
print(tasks[2])
```

有了循环，可以这样写：

```python
for task in tasks:
    print(task)
```

## 2. 为什么需要循环

真实开发经常要处理一批数据：

- 多个用户。
- 多个订单。
- 多个学习任务。
- 多条聊天消息。
- 多个文档 chunk。
- 多个检索结果。
- 多条评测样例。

AI 应用里也会经常用循环：

```python
for chunk in chunks:
    print(chunk)
```

```python
for test_case in test_cases:
    run_eval(test_case)
```

## 3. for 遍历列表

```python
tasks = ["学习变量", "学习字符串", "学习列表"]

for task in tasks:
    print("任务:", task)
```

含义：

```text
每次从 tasks 里取出一个元素
临时命名为 task
执行缩进里的代码
```

## 4. enumerate 带编号遍历

如果要同时拿到编号和元素：

```python
for index, task in enumerate(tasks, start=1):
    print(f"{index}. {task}")
```

`start=1` 表示编号从 1 开始，适合展示给人看。

## 5. for 遍历字符串

字符串也可以被遍历。

```python
word = "Python"

for char in word:
    print(char)
```

会依次输出：

```text
P
y
t
h
o
n
```

## 6. for 遍历字典

遍历字典时，常用 `items()` 同时拿 key 和 value。

```python
user = {
    "name": "Panpan",
    "age": 25,
}

for key, value in user.items():
    print(f"{key}: {value}")
```

## 7. range()

`range()` 用来生成数字序列。

```python
for number in range(5):
    print(number)
```

输出：

```text
0
1
2
3
4
```

注意：`range(5)` 不包含 5。

## 8. range(start, stop, step)

```python
for number in range(1, 10, 2):
    print(number)
```

含义：

```text
从 1 开始
到 10 之前停止
每次加 2
```

输出：

```text
1
3
5
7
9
```

## 9. continue

`continue` 表示跳过本次循环，直接进入下一次。

```python
for topic in topics:
    if topic in finished_topics:
        continue
    print("还没学:", topic)
```

如果这个 topic 已经学过，就跳过，不打印。

## 10. break

`break` 表示提前结束整个循环。

```python
for score in scores:
    if score < 0.5:
        print("发现低分结果，停止处理:", score)
        break
    print("处理检索结果:", score)
```

适合：

- 找到目标后停止。
- 遇到严重错误后停止。
- 检测到不可靠结果后停止。

## 11. while 循环

`while` 会在条件成立时一直循环。

```python
retry_count = 0
max_retries = 3

while retry_count < max_retries:
    print("尝试")
    retry_count += 1
```

适合：

- 重试。
- 等待某个条件发生。
- 处理不确定次数的任务。

## 12. 避免死循环

错误示例：

```python
retry_count = 0

while retry_count < 3:
    print("尝试")
```

`retry_count` 一直是 0，条件永远成立，程序会一直跑。

正确写法：

```python
retry_count = 0

while retry_count < 3:
    print("尝试")
    retry_count += 1
```

写 `while` 时一定要确认循环条件最终会变成 False。

## 13. 嵌套循环

循环里还可以写循环。

```python
users = ["u001", "u002"]
permissions = ["read", "write"]

for user_id in users:
    for permission in permissions:
        print(f"user={user_id}, permission={permission}")
```

输出每个用户和每个权限的组合。

嵌套循环不要乱用。层数太多时代码会难读。

## 14. AI 应用里的批量评测

评测集通常是一个列表，里面每个元素是一个字典。

```python
test_cases = [
    {"question": "Python 列表是什么？", "expected_keyword": "多个值"},
    {"question": "字典是什么？", "expected_keyword": "键值对"},
]
```

遍历评测：

```python
for case in test_cases:
    print(case["question"])
    print(case["expected_keyword"])
```

后面做 RAG eval、tool calling eval 时会大量用这种结构。

## 15. 常见错误

### 错误 1：遍历时修改列表导致结果混乱

不推荐：

```python
for task in tasks:
    tasks.remove(task)
```

边遍历边删除容易导致跳过元素。

### 错误 2：忘记更新 while 条件

```python
while retry_count < 3:
    print("尝试")
```

没有 `retry_count += 1`，会死循环。

### 错误 3：把 break 和 continue 搞混

`continue`：跳过本次，继续下一次。

`break`：直接结束整个循环。

### 错误 4：变量名不清楚

不推荐：

```python
for x in xs:
    print(x)
```

更推荐：

```python
for task in tasks:
    print(task)
```

## 16. 本节练习

创建文件：

```text
projects/python-basics/06_practice_batch_tasks.py
```

要求：

1. 创建任务列表，每个任务是一个字典，包含：
   - `name`
   - `done`
   - `important`
2. 打印全部任务，并带编号。
3. 遍历未完成任务。
4. 已完成任务用 `continue` 跳过。
5. 遇到重要任务时，用 `break` 停止。
6. 统计已经看到的未完成任务数量。
7. 创建一个测试集 `test_cases`。
8. 遍历测试集，判断答案里是否包含期望关键词。
9. 统计通过数量。

## 17. 练习参考答案

```python
def main() -> None:
    tasks = [
        {"name": "学习变量", "done": True, "important": False},
        {"name": "学习字符串", "done": True, "important": False},
        {"name": "学习列表", "done": True, "important": False},
        {"name": "学习字典", "done": True, "important": False},
        {"name": "学习条件判断", "done": True, "important": False},
        {"name": "学习循环", "done": False, "important": False},
        {"name": "学习函数", "done": False, "important": True},
        {"name": "学习异常处理", "done": False, "important": False},
    ]

    unfinished_count = 0

    print("全部任务:")
    for index, task in enumerate(tasks, start=1):
        print(f"{index}. {task['name']} done={task['done']} important={task['important']}")

    print("\n未完成任务:")
    for task in tasks:
        if task["done"]:
            continue

        unfinished_count += 1
        print("-", task["name"])

        if task["important"]:
            print("遇到重要任务，先停下来重点学习:", task["name"])
            break

    print("\n已统计到的未完成任务数量:", unfinished_count)

    print("\n模拟批量评测:")
    test_cases = [
        {"question": "列表是什么？", "answer": "列表是保存多个值的容器", "keyword": "多个值"},
        {"question": "字典是什么？", "answer": "字典保存键值对", "keyword": "键值对"},
        {"question": "循环是什么？", "answer": "循环可以重复处理数据", "keyword": "重复"},
    ]

    passed_count = 0
    for case in test_cases:
        if case["keyword"] in case["answer"]:
            passed_count += 1
            print("通过:", case["question"])
        else:
            print("失败:", case["question"])

    print("通过数量:", passed_count)
    print("总数量:", len(test_cases))


if __name__ == "__main__":
    main()
```

运行：

```powershell
uv run python 06_practice_batch_tasks.py
```

## 18. 自测问题

1. 循环解决什么问题？
2. `for task in tasks` 是什么意思？
3. `enumerate(tasks, start=1)` 的作用是什么？
4. `range(5)` 会生成哪些数字？
5. `range(1, 10, 2)` 会生成哪些数字？
6. `continue` 和 `break` 有什么区别？
7. `while` 适合什么场景？
8. 什么是死循环？
9. 为什么不推荐边遍历列表边删除元素？
10. AI 评测为什么会用到循环？

## 19. 自测参考答案

1. 循环解决什么问题？

   循环用来重复执行代码，适合批量处理多个数据。

2. `for task in tasks` 是什么意思？

   每次从 `tasks` 里取一个元素，临时命名为 `task`，然后执行循环体。

3. `enumerate(tasks, start=1)` 的作用是什么？

   遍历时同时得到编号和元素，编号从 1 开始。

4. `range(5)` 会生成哪些数字？

   生成 `0, 1, 2, 3, 4`，不包含 5。

5. `range(1, 10, 2)` 会生成哪些数字？

   生成 `1, 3, 5, 7, 9`。

6. `continue` 和 `break` 有什么区别？

   `continue` 跳过本次循环，继续下一次；`break` 直接结束整个循环。

7. `while` 适合什么场景？

   适合循环次数不固定，但有明确结束条件的场景，比如重试。

8. 什么是死循环？

   循环条件永远为 True，程序一直执行，无法正常结束。

9. 为什么不推荐边遍历列表边删除元素？

   因为删除会改变列表结构，容易导致元素被跳过或逻辑混乱。

10. AI 评测为什么会用到循环？

    因为评测通常要批量处理很多测试样例，每个样例都要调用模型、判断结果、统计通过率。

## 20. 推荐资料

- Python 官方教程：for Statements
  https://docs.python.org/3/tutorial/controlflow.html#for-statements

- Python 官方教程：range()
  https://docs.python.org/3/tutorial/controlflow.html#the-range-function

- Python 官方教程：break and continue
  https://docs.python.org/3/tutorial/controlflow.html#break-and-continue-statements

- Datawhale：聪明办法学 Python 第二版
  https://github.com/datawhalechina/learn-python-the-smart-way-v2
