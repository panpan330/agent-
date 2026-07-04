# Python 文件读写和 JSON

日期：2026-07-04

对应代码：

```text
projects/python-basics/10_files_json.py
projects/python-basics/10_practice_task_json.py
projects/python-basics/data/tasks.json
```

## 1. 文件是什么

文件是硬盘上的数据。

前面学的变量、列表、字典都在程序运行时存在。程序结束后，内存里的数据就没了。

如果想长期保存数据，就要写入文件。

常见文件：

- `.txt` 文本文件。
- `.json` JSON 数据文件。
- `.md` Markdown 文档。
- `.csv` 表格数据。
- `.log` 日志文件。

## 2. 为什么需要文件读写

AI 应用里会经常用文件：

- 读取测试集。
- 保存评测报告。
- 读取 prompt 模板。
- 保存学习记录。
- 读取待入库文档。
- 写入日志。

例如：

```text
data/tasks.json
eval_report.json
documents/python_notes.md
```

## 3. 路径是什么

路径就是文件或目录的位置。

Windows 路径：

```text
D:\wendang\java+python+ai\projects\python-basics\data\tasks.json
```

在 Python 里推荐用 `pathlib.Path` 处理路径：

```python
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
JSON_FILE = DATA_DIR / "tasks.json"
```

`/` 在 `Path` 里表示拼接路径，不是除法。

## 4. 绝对路径和相对路径

绝对路径从盘符或根目录开始：

```text
D:\wendang\java+python+ai\projects\python-basics\data\tasks.json
```

相对路径相对于当前工作目录：

```text
data/tasks.json
```

初学时容易因为当前工作目录不同导致找不到文件。

所以示例里用：

```python
BASE_DIR = Path(__file__).parent
```

表示以当前 Python 文件所在目录为基准。

## 5. 写文本文件

```python
TEXT_FILE.write_text("今天学习 Python 文件读写。\n", encoding="utf-8")
```

`encoding="utf-8"` 表示用 UTF-8 编码保存中文。

## 6. 读文本文件

```python
content = TEXT_FILE.read_text(encoding="utf-8")
```

读出来的是字符串。

## 7. 追加写入

用 `open("a")` 表示追加。

```python
with TEXT_FILE.open("a", encoding="utf-8") as file:
    file.write("追加一行。\n")
```

模式含义：

| 模式 | 含义 |
| --- | --- |
| `"r"` | 读取 |
| `"w"` | 写入，会覆盖原内容 |
| `"a"` | 追加，写到文件末尾 |

## 8. with 是什么

`with` 可以自动管理资源。

```python
with path.open("r", encoding="utf-8") as file:
    content = file.read()
```

文件用完后会自动关闭。

不推荐手动写：

```python
file = open(...)
...
file.close()
```

因为中间出错时可能忘记关闭文件。

## 9. 文件不存在异常

如果读取不存在的文件：

```python
path.read_text(encoding="utf-8")
```

可能会抛出：

```text
FileNotFoundError
```

可以先判断：

```python
if not path.exists():
    ...
```

## 10. JSON 是什么

JSON 是一种文本数据格式，常用于接口请求、接口响应、配置文件和测试集。

JSON 示例：

```json
[
  {
    "name": "学习变量",
    "done": true
  }
]
```

它和 Python 的列表、字典很像。

## 11. Python 数据和 JSON 的关系

Python：

```python
tasks = [
    {"name": "学习变量", "done": True},
    {"name": "学习文件读写", "done": False},
]
```

JSON：

```json
[
  {"name": "学习变量", "done": true},
  {"name": "学习文件读写", "done": false}
]
```

区别：

- Python 里布尔值是 `True` / `False`。
- JSON 里布尔值是 `true` / `false`。
- Python 数据在内存里。
- JSON 是文本格式，保存在文件或网络请求里。

## 12. json.load()

从文件读取 JSON，并转成 Python 数据。

```python
with JSON_FILE.open("r", encoding="utf-8") as file:
    tasks = json.load(file)
```

如果 JSON 文件里是数组，读出来是 Python 列表。

如果 JSON 文件里是对象，读出来是 Python 字典。

## 13. json.dump()

把 Python 数据写成 JSON 文件。

```python
with JSON_FILE.open("w", encoding="utf-8") as file:
    json.dump(tasks, file, ensure_ascii=False, indent=2)
```

参数：

- `ensure_ascii=False`：中文正常显示，不转成 `\uXXXX`。
- `indent=2`：格式化缩进，方便阅读。

## 14. 常见错误

### 错误 1：忘记 encoding

不推荐：

```python
path.read_text()
```

更推荐：

```python
path.read_text(encoding="utf-8")
```

### 错误 2：写入模式覆盖文件

```python
open("notes.txt", "w")
```

会覆盖原内容。

如果想追加，用：

```python
open("notes.txt", "a")
```

### 错误 3：JSON 格式错误

JSON 字符串必须符合格式。

错误示例：

```json
{"name": "Panpan",}
```

最后多了一个逗号，可能解析失败。

### 错误 4：混淆 json.load 和 json.loads

```python
json.load(file)
```

从文件对象读取。

```python
json.loads(text)
```

从字符串读取。

同理：

```python
json.dump(data, file)
```

写入文件对象。

```python
json.dumps(data)
```

转成字符串。

## 15. AI 应用里的文件和 JSON

评测集可能长这样：

```json
[
  {
    "question": "RAG 是什么？",
    "expected_keyword": "检索增强生成"
  }
]
```

评测报告可能长这样：

```json
{
  "total_count": 30,
  "passed_count": 24,
  "failed_count": 6
}
```

后面写 `eval.py` 时会大量用：

```python
json.load()
json.dump()
for case in test_cases:
    ...
```

## 16. 本节练习

创建文件：

```text
projects/python-basics/10_practice_task_json.py
```

要求：

1. 使用 `Path` 定义数据文件路径。
2. 如果任务文件不存在，创建默认任务。
3. 读取任务 JSON。
4. 新增任务 `"学习 JSON 文件"`，如果已经存在就不重复添加。
5. 写回任务 JSON。
6. 统计：
   - 总任务数。
   - 已完成数量。
   - 未完成数量。
   - 未完成任务列表。
7. 写入报告 JSON。

## 17. 练习参考答案

```python
import json
from pathlib import Path


BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
TASK_FILE = DATA_DIR / "practice_tasks.json"
REPORT_FILE = DATA_DIR / "practice_report.json"


def create_default_tasks() -> list[dict]:
    return [
        {"name": "学习变量", "done": True},
        {"name": "学习字符串", "done": True},
        {"name": "学习列表", "done": True},
        {"name": "学习文件读写", "done": False},
    ]


def save_json(path: Path, data: list[dict] | dict) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def load_json(path: Path) -> list[dict]:
    if not path.exists():
        default_tasks = create_default_tasks()
        save_json(path, default_tasks)
        return default_tasks

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def add_task(tasks: list[dict], name: str) -> None:
    for task in tasks:
        if task["name"] == name:
            return

    tasks.append({"name": name, "done": False})


def build_report(tasks: list[dict]) -> dict:
    done_count = 0
    undone_tasks = []

    for task in tasks:
        if task["done"]:
            done_count += 1
        else:
            undone_tasks.append(task["name"])

    return {
        "total_count": len(tasks),
        "done_count": done_count,
        "undone_count": len(undone_tasks),
        "undone_tasks": undone_tasks,
    }


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)

    tasks = load_json(TASK_FILE)
    add_task(tasks, "学习 JSON 文件")
    save_json(TASK_FILE, tasks)

    report = build_report(tasks)
    save_json(REPORT_FILE, report)

    print("任务:", tasks)
    print("报告:", report)


if __name__ == "__main__":
    main()
```

运行：

```powershell
uv run python 10_practice_task_json.py
```

## 18. 自测问题

1. 文件读写解决什么问题？
2. 为什么推荐用 `Path(__file__).parent`？
3. `"r"`、`"w"`、`"a"` 分别是什么意思？
4. `with` 有什么作用？
5. JSON 是什么？
6. Python 字典和 JSON 是同一个东西吗？
7. `json.load()` 和 `json.loads()` 有什么区别？
8. `json.dump()` 和 `json.dumps()` 有什么区别？
9. `ensure_ascii=False` 有什么用？
10. AI 评测为什么会用 JSON 文件？

## 19. 自测参考答案

1. 文件读写解决什么问题？

   文件读写让程序可以从硬盘读取数据，也可以把结果长期保存下来。

2. 为什么推荐用 `Path(__file__).parent`？

   因为它以当前 Python 文件所在目录为基准，避免运行目录变化导致相对路径失效。

3. `"r"`、`"w"`、`"a"` 分别是什么意思？

   `"r"` 是读取，`"w"` 是写入并覆盖原内容，`"a"` 是追加到文件末尾。

4. `with` 有什么作用？

   `with` 可以自动管理文件资源，代码块结束后自动关闭文件。

5. JSON 是什么？

   JSON 是一种文本数据格式，常用于接口、配置、测试集和报告。

6. Python 字典和 JSON 是同一个东西吗？

   不是。字典是 Python 内存里的数据结构，JSON 是文本格式。

7. `json.load()` 和 `json.loads()` 有什么区别？

   `json.load()` 从文件对象读取 JSON；`json.loads()` 从字符串读取 JSON。

8. `json.dump()` 和 `json.dumps()` 有什么区别？

   `json.dump()` 把数据写入文件对象；`json.dumps()` 把数据转成 JSON 字符串。

9. `ensure_ascii=False` 有什么用？

   让 JSON 文件里的中文正常显示，而不是转成 `\uXXXX`。

10. AI 评测为什么会用 JSON 文件？

    因为测试问题、期望答案、评测结果都适合用结构化数据保存，方便程序批量读取和统计。

## 20. 推荐资料

- Python 官方教程：Reading and Writing Files
  https://docs.python.org/3/tutorial/inputoutput.html#reading-and-writing-files

- Python 官方文档：json
  https://docs.python.org/3/library/json.html

- Python 官方文档：pathlib
  https://docs.python.org/3/library/pathlib.html

- Datawhale：聪明办法学 Python 第二版
  https://github.com/datawhalechina/learn-python-the-smart-way-v2
