# Python 标准库基础

日期：2026-07-05

对应代码：

```text
projects/python-basics/16_standard_library.py
projects/python-basics/16_practice_standard_library.py
```

## 1. 标准库是什么

标准库就是 Python 自带的一批工具。

它们不需要你用 `uv add` 或 `pip install` 安装，只要安装了 Python，就可以直接使用。

示例：

```python
from pathlib import Path
from datetime import datetime
import logging
```

可以先理解成：

```text
标准库 = Python 官方自带的工具箱
```

## 2. 为什么要学标准库

真实项目里，不可能只写变量、循环、函数。

你一定会遇到这些事情：

- 找文件。
- 读配置。
- 记录时间。
- 计算接口耗时。
- 统计数据。
- 分组数据。
- 打日志。
- 读取环境变量。
- 查看 Python 运行信息。

这些事情很多都不用第三方库，标准库就能完成。

## 3. 本节学哪些模块

这一节先学最常用的一批：

- `pathlib`：处理文件路径。
- `datetime`：处理日期和时间。
- `time`：计算耗时。
- `collections`：更方便的数据结构。
- `logging`：记录日志。
- `os`：读取环境变量。
- `sys`：查看 Python 运行信息。

`re` 正则表达式会单独开一节，因为它本身容易绕。

## 4. import 和 from import

导入模块有两种常见写法。

第一种：

```python
import os
```

使用时写：

```python
os.getenv("APP_ENV")
```

第二种：

```python
from pathlib import Path
```

使用时直接写：

```python
Path.cwd()
```

这两种都可以。

原则：

```text
模块名短，常用 import 模块名。
只用模块里的少数几个类或函数，可以 from 模块 import 名字。
```

## 5. pathlib 是什么

`pathlib` 用来处理文件路径。

以前也能用字符串拼路径：

```python
path = "data/tasks.json"
```

但更推荐用 `Path`：

```python
from pathlib import Path

path = Path("data") / "tasks.json"
```

这里的 `/` 不是除法，而是 `Path` 对象重载后的路径拼接。

## 6. pathlib 常用写法

当前工作目录：

```python
Path.cwd()
```

拼接路径：

```python
data_dir = Path.cwd() / "data"
tasks_file = data_dir / "tasks.json"
```

判断是否存在：

```python
tasks_file.exists()
```

获取文件名：

```python
tasks_file.name
```

获取后缀：

```python
tasks_file.suffix
```

获取父目录：

```python
tasks_file.parent
```

## 7. pathlib 读文件

```python
from pathlib import Path

path = Path("data") / "tasks.json"

with path.open("r", encoding="utf-8") as file:
    content = file.read()
```

注意：

- `"r"` 表示读取。
- `encoding="utf-8"` 表示按 UTF-8 编码读取。
- `with` 会自动关闭文件。

## 8. json 和 pathlib 配合

```python
import json
from pathlib import Path

path = Path("data") / "tasks.json"

with path.open("r", encoding="utf-8") as file:
    data = json.load(file)
```

`json.load(file)` 会把 JSON 文件内容转成 Python 数据。

例如 JSON 数组会变成 Python 列表，JSON 对象会变成 Python 字典。

## 9. datetime 是什么

`datetime` 用来处理日期和时间。

```python
from datetime import datetime

now = datetime.now()
```

格式化成字符串：

```python
now.strftime("%Y-%m-%d %H:%M:%S")
```

常用格式：

- `%Y`：四位年份。
- `%m`：月份。
- `%d`：日期。
- `%H`：小时。
- `%M`：分钟。
- `%S`：秒。

## 10. timezone 是什么

真实项目经常要处理时区。

UTC 时间：

```python
from datetime import datetime, timezone

utc_now = datetime.now(timezone.utc)
```

转成 ISO 格式：

```python
utc_now.isoformat()
```

接口响应、日志、数据库里经常用这种格式。

## 11. timedelta 是什么

`timedelta` 表示一段时间。

```python
from datetime import datetime, timedelta

now = datetime.now()
tomorrow = now + timedelta(days=1)
```

也可以表示小时、分钟、秒：

```python
later = now + timedelta(minutes=30)
```

## 12. time 用来计算耗时

如果你想知道一段代码运行了多久，可以用：

```python
import time

start = time.perf_counter()

# 执行一些代码

elapsed = time.perf_counter() - start
```

`perf_counter()` 适合计算耗时。

后面做 AI 接口时，我们会记录：

- 请求开始时间。
- 模型调用耗时。
- 检索耗时。
- 总耗时。

## 13. collections.Counter

`Counter` 用来统计数量。

```python
from collections import Counter

words = ["python", "ai", "python"]
counter = Counter(words)
```

结果类似：

```python
Counter({"python": 2, "ai": 1})
```

查看出现最多的内容：

```python
counter.most_common(2)
```

## 14. Counter 的项目用途

以后可以用它做：

- 统计关键词出现次数。
- 统计任务状态。
- 统计错误类型。
- 统计文档来源数量。

例如：

```python
status_counter = Counter(["done", "todo", "done"])
```

## 15. collections.defaultdict

普通字典分组时，经常要先判断 key 是否存在：

```python
groups = {}

for task in tasks:
    topic = task["topic"]
    if topic not in groups:
        groups[topic] = []
    groups[topic].append(task)
```

`defaultdict(list)` 可以少写这个判断：

```python
from collections import defaultdict

groups = defaultdict(list)

for task in tasks:
    groups[task["topic"]].append(task)
```

当 key 不存在时，它会自动创建一个空列表。

## 16. logging 是什么

`logging` 是 Python 标准库里的日志工具。

初学时我们经常用：

```python
print("任务数量:", len(tasks))
```

真实项目更常用：

```python
logging.info("任务数量: %s", len(tasks))
```

日志比 `print()` 更适合工程项目，因为它有级别、有格式，可以输出到文件，也可以被日志平台收集。

## 17. logging 基本配置

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
```

含义：

- `level=logging.INFO`：显示 INFO 及以上级别的日志。
- `asctime`：日志时间。
- `levelname`：日志级别。
- `message`：日志内容。

## 18. 日志级别

常见日志级别：

- `DEBUG`：调试信息，开发时看。
- `INFO`：普通运行信息。
- `WARNING`：警告，可能需要关注。
- `ERROR`：错误，某个操作失败。
- `CRITICAL`：严重错误。

示例：

```python
logging.info("服务启动")
logging.warning("配置项缺失，使用默认值")
logging.error("请求失败")
```

## 19. 为什么 logging 不直接用 f-string

推荐写法：

```python
logging.info("任务数量: %s", len(tasks))
```

也能写：

```python
logging.info(f"任务数量: {len(tasks)}")
```

初学阶段两种都能看懂。

工程里更推荐第一种，因为日志系统可以延迟格式化，在高频日志场景下更合适。

## 20. os.getenv 读取环境变量

环境变量是操作系统提供给程序的配置。

读取：

```python
import os

app_env = os.getenv("APP_ENV", "local")
```

含义：

- 读取名为 `APP_ENV` 的环境变量。
- 如果不存在，就使用默认值 `"local"`。

后面 `.env` 文件、本地密钥、模型名称、数据库地址都会和环境变量有关。

## 21. sys 查看运行信息

```python
import sys

print(sys.version)
print(sys.argv)
```

常用：

- `sys.version`：Python 版本信息。
- `sys.argv`：命令行参数。

例如运行：

```powershell
python app.py hello
```

`sys.argv` 可能是：

```python
["app.py", "hello"]
```

## 22. 常见错误

### 错误 1：手动拼路径

不推荐：

```python
path = "data" + "/" + "tasks.json"
```

推荐：

```python
path = Path("data") / "tasks.json"
```

### 错误 2：忘记 encoding

中文文件建议明确写：

```python
path.open("r", encoding="utf-8")
```

### 错误 3：用 time.time() 做耗时统计

`time.time()` 是当前时间戳，可能受系统时间调整影响。

计算耗时更推荐：

```python
time.perf_counter()
```

### 错误 4：真实项目里全部用 print

练习时可以用 `print()`。

但服务项目里要逐步改成 `logging`。

### 错误 5：环境变量不存在就直接用

错误：

```python
api_key = os.getenv("OPENAI_API_KEY")
print(api_key.upper())
```

如果环境变量不存在，`api_key` 是 `None`，会报错。

应该先判断，或者提供默认值。

## 23. 本节练习

创建文件：

```text
projects/python-basics/16_practice_standard_library.py
```

要求：

1. 写函数 `get_project_paths(root: Path) -> dict[str, Path]`
   - 返回项目根目录、data 目录、tasks 文件路径。
2. 写函数 `load_json_list(path: Path) -> list[dict[str, object]]`
   - 如果文件不存在，返回空列表。
   - 如果 JSON 不是列表，也返回空列表。
3. 写函数 `count_task_status(tasks)`
   - 用 `Counter` 统计 `done` 和 `todo` 数量。
4. 写函数 `group_tasks_by_topic(tasks)`
   - 用 `defaultdict(list)` 按主题分组。
5. 写函数 `build_run_info()`
   - 返回环境变量 `APP_ENV`。
   - 返回 Python 版本。
   - 返回 UTC 运行时间。
6. 写函数 `log_summary(tasks, elapsed_seconds)`
   - 用 `logging.info()` 输出任务数量和耗时。

## 24. 练习参考答案

```python
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import json
import logging
import os
import sys
import time


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def get_project_paths(root: Path) -> dict[str, Path]:
    data_dir = root / "data"

    return {
        "root": root,
        "data_dir": data_dir,
        "tasks_file": data_dir / "tasks.json",
    }


def load_json_list(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        return []

    result = []
    for item in data:
        if isinstance(item, dict):
            result.append(item)

    return result


def count_task_status(tasks: list[dict[str, object]]) -> Counter[str]:
    counter: Counter[str] = Counter()

    for task in tasks:
        done = task.get("done", False)
        status = "done" if done else "todo"
        counter[status] += 1

    return counter


def group_tasks_by_topic(tasks: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    groups: defaultdict[str, list[dict[str, object]]] = defaultdict(list)

    for task in tasks:
        topic = task.get("topic", "未分类")
        if not isinstance(topic, str) or not topic:
            topic = "未分类"
        groups[topic].append(task)

    return dict(groups)


def build_run_info() -> dict[str, object]:
    return {
        "app_env": os.getenv("APP_ENV", "local"),
        "python_version": sys.version.split()[0],
        "run_at": datetime.now(timezone.utc).isoformat(),
    }


def log_summary(tasks: list[dict[str, object]], elapsed_seconds: float) -> None:
    logging.info("任务数量: %s", len(tasks))
    logging.info("处理耗时: %.6f 秒", elapsed_seconds)
```

运行：

```powershell
uv run python 16_practice_standard_library.py
```

## 25. 自测问题

1. 标准库是什么？
2. `pathlib` 主要解决什么问题？
3. `Path("data") / "tasks.json"` 里的 `/` 是什么意思？
4. `datetime.now()` 和 `datetime.now(timezone.utc)` 有什么区别？
5. `timedelta` 表示什么？
6. 为什么计算耗时推荐 `time.perf_counter()`？
7. `Counter` 适合做什么？
8. `defaultdict(list)` 解决什么问题？
9. `logging` 相比 `print()` 有什么优势？
10. `os.getenv("APP_ENV", "local")` 的第二个参数是什么意思？

## 26. 自测参考答案

1. 标准库是什么？

   标准库是 Python 官方自带的工具箱，不需要额外安装就能使用。

2. `pathlib` 主要解决什么问题？

   它主要用来处理文件和目录路径，比如拼接路径、判断文件是否存在、获取文件名和后缀。

3. `Path("data") / "tasks.json"` 里的 `/` 是什么意思？

   在 `Path` 对象里，`/` 表示路径拼接，不是数学除法。

4. `datetime.now()` 和 `datetime.now(timezone.utc)` 有什么区别？

   `datetime.now()` 返回本地当前时间；`datetime.now(timezone.utc)` 返回带 UTC 时区信息的当前时间。

5. `timedelta` 表示什么？

   `timedelta` 表示一段时间，比如一天、30 分钟、5 秒。

6. 为什么计算耗时推荐 `time.perf_counter()`？

   因为它适合做高精度耗时统计，不容易受系统时间调整影响。

7. `Counter` 适合做什么？

   适合统计数量，比如词频、状态数量、错误类型数量。

8. `defaultdict(list)` 解决什么问题？

   它在按 key 分组时，如果 key 不存在，会自动创建空列表，少写手动初始化代码。

9. `logging` 相比 `print()` 有什么优势？

   `logging` 有日志级别、时间格式、输出控制，适合真实服务和长期运行的项目。

10. `os.getenv("APP_ENV", "local")` 的第二个参数是什么意思？

    第二个参数是默认值。如果环境变量 `APP_ENV` 不存在，就返回 `"local"`。

## 27. 推荐资料

- Python 官方文档：pathlib
  https://docs.python.org/3/library/pathlib.html

- Python 官方文档：datetime
  https://docs.python.org/3/library/datetime.html

- Python 官方文档：collections
  https://docs.python.org/3/library/collections.html

- Python 官方文档：logging
  https://docs.python.org/3/library/logging.html

- Python 官方文档：os
  https://docs.python.org/3/library/os.html

- Python 官方文档：sys
  https://docs.python.org/3/library/sys.html
