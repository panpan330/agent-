# Python 调试和报错阅读

日期：2026-07-05

对应代码：

```text
projects/python-basics/lesson19_debugging_traceback.py
projects/python-basics/lesson19_practice_debugging.py
projects/python-basics/test_lesson19_practice_debugging.py
```

## 1. 本节学什么

这一节学习怎么面对代码报错。

目标不是让你“背错误”，而是让你知道：

- 报错信息应该从哪里看。
- traceback 里的文件、行号、函数调用关系怎么看。
- 常见错误类型分别说明什么。
- 怎么用 `print()`、`logging`、断点思路定位问题。
- 怎么把调试过程变成测试，防止问题再次出现。

可以先记住：

```text
报错不是敌人，报错是 Python 告诉你问题在哪里。
```

## 2. traceback 是什么

traceback 是 Python 报错时打印出来的调用链。

它通常长这样：

```text
Traceback (most recent call last):
  File "lesson19_debugging_traceback.py", line 81, in main
    divide_total(10, 0)
  File "lesson19_debugging_traceback.py", line 14, in divide_total
    return total / count
ZeroDivisionError: division by zero
```

重点看三类信息：

- 文件名：哪个文件出问题。
- 行号：哪一行出问题。
- 错误类型和错误信息：问题是什么。

## 3. traceback 先看最后一行

最后一行通常最关键：

```text
ZeroDivisionError: division by zero
```

含义：

- 错误类型：`ZeroDivisionError`
- 错误信息：`division by zero`

先看最后一行，你能快速知道“大概是什么错”。

## 4. 再从下往上找自己的代码

traceback 里可能会出现很多库文件。

你的重点是找自己写的文件，比如：

```text
File "lesson19_debugging_traceback.py", line 14, in divide_total
```

这表示：

- 文件：`lesson19_debugging_traceback.py`
- 行号：`14`
- 函数：`divide_total`

然后你回到这一行看变量值和逻辑。

## 5. 常见错误：ZeroDivisionError

```python
def divide_total(total: int, count: int) -> float:
    return total / count
```

如果调用：

```python
divide_total(10, 0)
```

会报：

```text
ZeroDivisionError
```

原因是除数不能为 `0`。

修复思路：

```python
if count == 0:
    raise ValueError("count must not be 0")
```

## 6. 常见错误：KeyError

```python
user = {"age": 25}
print(user["name"])
```

会报：

```text
KeyError: 'name'
```

含义是字典里没有这个 key。

修复思路：

```python
if "name" not in user:
    raise KeyError("missing required field: name")
```

或者如果允许默认值：

```python
user.get("name", "")
```

## 7. 常见错误：ValueError

```python
float("abc")
```

会报：

```text
ValueError
```

含义是类型大方向对，但值不合法。

`"abc"` 是字符串，可以尝试转 float，但它不是数字格式。

## 8. 常见错误：TypeError

```python
len(123)
```

会报：

```text
TypeError
```

含义是操作不适合这个类型。

`len()` 适合字符串、列表、字典这类对象，不适合整数。

## 9. 常见错误：FileNotFoundError

```python
Path("missing.json").open("r", encoding="utf-8")
```

如果文件不存在，会报：

```text
FileNotFoundError
```

修复思路：

```python
if not path.exists():
    return []
```

或者明确抛出更容易理解的错误。

## 10. print 调试

最简单的调试方法是打印中间变量。

```python
print("raw_question:", raw_question)
print("cleaned:", cleaned)
print("type:", type(cleaned))
```

适合初学阶段快速确认：

- 函数有没有执行到。
- 变量值是什么。
- 数据类型是什么。
- 条件判断有没有进入。

## 11. logging 调试

真实项目更推荐 `logging`。

```python
logging.debug("原始问题: %r", question)
logging.info("处理完成")
logging.warning("配置缺失，使用默认值")
```

日志级别：

- `DEBUG`：调试细节。
- `INFO`：普通运行信息。
- `WARNING`：警告。
- `ERROR`：错误。

调试时可以打开 `DEBUG` 级别，线上可以只看 `INFO` 或更高。

## 12. 用 traceback 模块安全演示报错

练习脚本里用了：

```python
import traceback

try:
    divide_total(10, 0)
except Exception as error:
    print(type(error).__name__)
    print(error)
    print(traceback.format_exc())
```

这样程序不会直接崩掉，但你仍然能看到完整 traceback。

这适合学习阶段观察错误。

## 13. 调试的基本顺序

建议每次报错都按这个顺序：

1. 看最后一行，确定错误类型和错误信息。
2. 从下往上找自己写的文件和行号。
3. 回到那一行，检查变量值和类型。
4. 用 `print()`、`logging` 或断点继续缩小范围。
5. 修复后重新运行脚本。
6. 如果这个问题容易复发，补一个 pytest 测试。

## 14. VS Code 断点是什么

断点就是让程序运行到某一行时停下来。

停下来以后你可以看：

- 当前变量值。
- 当前执行到哪一行。
- 函数调用栈。
- 一步一步往下执行。

初学阶段先知道这个概念。

后面进入 FastAPI 项目时，我们会专门练习 VS Code debugger。

## 15. 不要吞掉异常

不推荐：

```python
try:
    result = parse_score(value)
except Exception:
    pass
```

这样错误被静默隐藏，你不知道问题发生了。

更好的写法：

```python
try:
    result = parse_score(value)
except ValueError as error:
    logging.warning("分数解析失败: %s", error)
    raise
```

## 16. 自定义错误信息

错误信息要让人看得懂。

不清楚：

```python
raise ValueError("bad")
```

更清楚：

```python
raise ValueError("score must be between 0 and 1")
```

报错信息越具体，调试越快。

## 17. 用测试固定问题

如果你修复了一个 bug，最好补测试。

例如：

```python
def calculate_average(numbers: list[float]) -> float:
    if not numbers:
        raise ValueError("numbers must not be empty")
    return sum(numbers) / len(numbers)
```

测试：

```python
def test_calculate_average_error() -> None:
    with pytest.raises(ValueError):
        calculate_average([])
```

这样以后别人改代码，如果又忘了处理空列表，测试会失败。

## 18. 常见调试误区

### 误区 1：只看第一行 traceback

traceback 最后一行通常更关键。

### 误区 2：看到红字就慌

报错是信息，不是失败判决。

### 误区 3：只修表面现象

例如 `KeyError` 不只是“加个默认值”就完事。

你要判断这个 key 是必须字段，还是可以没有。

### 误区 4：所有异常都 except Exception

初学阶段可以用它演示报错。

真实业务里要尽量捕获明确异常，比如 `ValueError`、`KeyError`、`FileNotFoundError`。

## 19. 本节练习

创建文件：

```text
projects/python-basics/lesson19_practice_debugging.py
projects/python-basics/test_lesson19_practice_debugging.py
```

要求：

1. 写函数 `parse_positive_int(value)`
   - 转成整数。
   - 不是整数时抛 `ValueError`。
   - 小于等于 0 时抛 `ValueError`。
2. 写函数 `get_required_field(data, key)`
   - key 不存在时抛 `KeyError`。
3. 写函数 `calculate_average(numbers)`
   - 空列表时抛 `ValueError`。
4. 写函数 `normalize_user(user)`
   - 必须有 `name` 和 `age`。
   - `name` 必须是非空字符串。
   - `age` 必须是正整数。
5. 写函数 `safe_run(case_name, func)`
   - 成功时返回 `ok=True` 和结果。
   - 失败时返回错误类型和错误信息。
6. 给这些函数写 pytest 测试。

## 20. 练习参考答案

```python
def parse_positive_int(value: object) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError("value must be an integer") from error

    if number <= 0:
        raise ValueError("value must be positive")

    return number
```

```python
def get_required_field(data: dict[str, object], key: str) -> object:
    if key not in data:
        raise KeyError(f"missing required field: {key}")

    return data[key]
```

```python
def calculate_average(numbers: list[float]) -> float:
    if not numbers:
        raise ValueError("numbers must not be empty")

    return sum(numbers) / len(numbers)
```

```python
def safe_run(case_name: str, func: Callable[[], object]) -> dict[str, object]:
    try:
        result = func()
    except Exception as error:
        return {
            "case_name": case_name,
            "ok": False,
            "error_type": type(error).__name__,
            "error_message": str(error),
        }

    return {
        "case_name": case_name,
        "ok": True,
        "result": result,
    }
```

测试示例：

```python
def test_calculate_average_error() -> None:
    with pytest.raises(ValueError):
        calculate_average([])
```

运行：

```powershell
uv run pytest test_lesson19_practice_debugging.py -q
```

## 21. 自测问题

1. traceback 是什么？
2. 看 traceback 时为什么先看最后一行？
3. `KeyError` 通常说明什么？
4. `ValueError` 通常说明什么？
5. `TypeError` 通常说明什么？
6. `FileNotFoundError` 通常说明什么？
7. `print()` 调试适合看什么？
8. `logging.debug()` 和 `logging.info()` 有什么区别？
9. 为什么不要随便 `except Exception: pass`？
10. 修复 bug 后为什么建议补测试？

## 22. 自测参考答案

1. traceback 是什么？

   traceback 是 Python 报错时打印出来的调用链，告诉你错误从哪里一路发生到哪里。

2. 看 traceback 时为什么先看最后一行？

   因为最后一行通常包含错误类型和错误信息，可以快速判断问题大类。

3. `KeyError` 通常说明什么？

   通常说明访问字典时，指定的 key 不存在。

4. `ValueError` 通常说明什么？

   通常说明类型大方向可以处理，但具体值不合法，比如 `"abc"` 不能转成数字。

5. `TypeError` 通常说明什么？

   通常说明对某种类型做了不支持的操作，比如对整数调用 `len()`。

6. `FileNotFoundError` 通常说明什么？

   通常说明程序要读取或打开的文件路径不存在。

7. `print()` 调试适合看什么？

   适合快速查看代码有没有执行到、变量值是什么、变量类型是什么、条件分支有没有进入。

8. `logging.debug()` 和 `logging.info()` 有什么区别？

   `debug` 是更细的调试信息，通常开发时看；`info` 是普通运行信息，真实项目中更常保留。

9. 为什么不要随便 `except Exception: pass`？

   因为它会把错误静默吞掉，让你不知道问题发生了，后面更难定位。

10. 修复 bug 后为什么建议补测试？

    因为测试能固定这个 bug 的场景，防止以后改代码时同样的问题再次出现。

## 23. 推荐资料

- Python 官方文档：Errors and Exceptions
  https://docs.python.org/3/tutorial/errors.html

- Python 官方文档：traceback
  https://docs.python.org/3/library/traceback.html

- Python 官方文档：logging
  https://docs.python.org/3/library/logging.html

- VS Code 官方文档：Debugging Python
  https://code.visualstudio.com/docs/python/debugging
