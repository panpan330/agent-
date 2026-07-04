# Python 异常处理 try / except

日期：2026-07-04

对应代码：

```text
projects/python-basics/09_exceptions.py
projects/python-basics/09_practice_safe_request.py
```

## 1. 异常是什么

异常是程序运行时出现的错误。

例如：

```python
int("abc")
```

这里 `"abc"` 不能转成整数，会抛出 `ValueError`。

如果不处理异常，程序会直接中断。

## 2. 为什么需要异常处理

真实程序一定会遇到错误：

- 用户输入格式不对。
- 字典 key 不存在。
- 列表索引越界。
- 文件不存在。
- 网络请求超时。
- 模型 API 调用失败。
- JSON 解析失败。

异常处理的目标不是把错误藏起来，而是：

```text
出错时给出可控结果
不中断整个流程
保留清楚的错误信息
```

## 3. try / except

基本写法：

```python
try:
    可能出错的代码
except 某种异常:
    出错时执行的代码
```

示例：

```python
try:
    age = int("abc")
except ValueError:
    age = 0
```

## 4. 捕获具体异常

不同错误有不同异常类型。

### ValueError

值格式不合法。

```python
int("abc")
```

会抛出 `ValueError`。

### KeyError

字典 key 不存在。

```python
user = {"age": 25}
user["name"]
```

会抛出 `KeyError`。

### IndexError

列表索引越界。

```python
items = []
items[0]
```

会抛出 `IndexError`。

### RequestException

`requests` 请求失败时，通常捕获：

```python
requests.RequestException
```

## 5. 捕获错误对象

```python
try:
    age = int("abc")
except ValueError as error:
    print(error)
```

`error` 里保存了错误信息。

后面写日志时会经常用。

## 6. Exception 通用异常

`Exception` 可以捕获很多普通异常。

```python
try:
    do_something()
except Exception as error:
    print(error)
```

但不要一上来就用它包所有代码。

更推荐优先捕获具体异常：

```python
except ValueError:
except KeyError:
except requests.RequestException:
```

这样错误处理更清楚。

## 7. else

`else` 在没有异常时执行。

```python
try:
    number = int("100")
except ValueError:
    print("转换失败")
else:
    print("转换成功:", number)
```

## 8. finally

`finally` 无论有没有异常都会执行。

```python
try:
    number = int("100")
except ValueError:
    print("转换失败")
finally:
    print("一定会执行")
```

常用于：

- 关闭文件。
- 释放资源。
- 清理临时状态。

## 9. raise 主动抛异常

有时不是 Python 自己报错，而是我们主动判断业务规则不满足。

```python
def validate_question(question: str) -> None:
    if not question.strip():
        raise ValueError("问题不能为空")
```

调用方可以捕获这个异常：

```python
try:
    validate_question("")
except ValueError as error:
    print(error)
```

## 10. 什么时候捕获，什么时候 raise

简单理解：

```text
发现下游错误 -> 捕获异常
发现自己的业务规则不满足 -> raise 主动抛异常
```

比如：

- 字符串转数字失败：捕获 `ValueError`。
- 网络请求失败：捕获 `requests.RequestException`。
- 用户问题为空：主动 `raise ValueError("问题不能为空")`。

## 11. 不要裸 except

不推荐：

```python
try:
    do_something()
except:
    print("出错了")
```

问题：

- 不知道捕获了什么错误。
- 可能把严重错误也吞掉。
- 排查问题困难。

更推荐：

```python
except ValueError as error:
    print(error)
```

或者：

```python
except Exception as error:
    print(error)
```

至少保留错误对象。

## 12. AI 应用里的异常处理

后面会经常处理：

```python
try:
    response = requests.post(url, json=payload, timeout=30)
except requests.RequestException as error:
    return {
        "ok": False,
        "error": str(error),
    }
```

常见场景：

- LLM API 超时。
- 模型返回格式错误。
- JSON 解析失败。
- 向量库请求失败。
- 工具调用失败。
- 文件解析失败。

## 13. 常见错误

### 错误 1：try 包太多代码

不推荐：

```python
try:
    很多很多代码
except Exception:
    ...
```

范围太大时，不知道到底哪一步出错。

### 错误 2：吞掉错误不记录

不推荐：

```python
except ValueError:
    pass
```

这样错误完全消失，后面很难排查。

### 错误 3：捕获异常后返回假成功

不推荐：

```python
except requests.RequestException:
    return {"ok": True}
```

请求失败却返回成功，会误导上游逻辑。

### 错误 4：把业务判断全写成异常

普通分支可以用 `if`，不需要都用异常。

```python
if score < 0.5:
    return "拒答"
```

异常更适合处理“不应该正常发生”的错误情况。

## 14. 本节练习

创建文件：

```text
projects/python-basics/09_practice_safe_request.py
```

要求：

1. 写 `safe_int(value: str, default: int = 0) -> int`。
2. 写 `safe_get(data: dict, key: str, default: str = "") -> str`。
3. 写 `validate_question(question: str) -> None`，问题为空或太短时主动 `raise ValueError`。
4. 写 `safe_fetch(url: str) -> dict`，捕获 `requests.RequestException`。
5. 写 `process_request(request: dict) -> dict`，组合前面的函数。
6. 测试：
   - 正常请求。
   - 问题太短。
   - 缺少 question。

## 15. 练习参考答案

```python
import requests


def safe_int(value: str, default: int = 0) -> int:
    try:
        return int(value)
    except ValueError:
        return default


def safe_get(data: dict, key: str, default: str = "") -> str:
    try:
        return data[key]
    except KeyError:
        return default


def validate_question(question: str) -> None:
    question = question.strip()
    if not question:
        raise ValueError("问题不能为空")
    if len(question) < 5:
        raise ValueError("问题太短")


def safe_fetch(url: str) -> dict:
    try:
        response = requests.get(url, timeout=5)
        return {
            "ok": True,
            "status_code": response.status_code,
            "error": None,
        }
    except requests.RequestException as error:
        return {
            "ok": False,
            "status_code": None,
            "error": str(error),
        }


def process_request(request: dict) -> dict:
    question = safe_get(request, "question", "").strip()
    age = safe_int(str(request.get("age", "0")))

    try:
        validate_question(question)
    except ValueError as error:
        return {
            "valid": False,
            "reason": str(error),
            "question": question,
            "age": age,
        }

    return {
        "valid": True,
        "reason": None,
        "question": question,
        "age": age,
    }


def main() -> None:
    requests_to_check = [
        {"question": " 我想学习 Python 异常处理 ", "age": "25"},
        {"question": "hi", "age": "abc"},
        {"age": "30"},
    ]

    for request in requests_to_check:
        print(process_request(request))

    print(safe_fetch("https://httpbin.org/get"))


if __name__ == "__main__":
    main()
```

运行：

```powershell
uv run python 09_practice_safe_request.py
```

## 16. 自测问题

1. 异常是什么？
2. 为什么需要异常处理？
3. `try / except` 的执行逻辑是什么？
4. `ValueError` 通常什么时候出现？
5. `KeyError` 通常什么时候出现？
6. `else` 和 `finally` 分别什么时候执行？
7. `raise` 是干什么的？
8. 为什么不推荐裸 `except`？
9. 为什么捕获异常后不能返回假成功？
10. AI 应用里哪些地方需要异常处理？

## 17. 自测参考答案

1. 异常是什么？

   异常是程序运行时出现的错误，如果不处理，程序会中断。

2. 为什么需要异常处理？

   为了在出错时返回可控结果，保留错误信息，并避免整个程序直接崩掉。

3. `try / except` 的执行逻辑是什么？

   先执行 `try` 里的代码。如果没有异常，跳过 `except`。如果出现匹配的异常，执行对应的 `except`。

4. `ValueError` 通常什么时候出现？

   值的格式不符合要求时，比如 `int("abc")`。

5. `KeyError` 通常什么时候出现？

   读取字典里不存在的 key 时。

6. `else` 和 `finally` 分别什么时候执行？

   `else` 在没有异常时执行；`finally` 无论有没有异常都会执行。

7. `raise` 是干什么的？

   `raise` 用来主动抛出异常，表示当前数据或状态不符合要求。

8. 为什么不推荐裸 `except`？

   因为不知道捕获了什么错误，可能吞掉严重问题，导致排查困难。

9. 为什么捕获异常后不能返回假成功？

   因为上游代码会以为操作成功，后续逻辑会基于错误前提继续执行，导致更隐蔽的问题。

10. AI 应用里哪些地方需要异常处理？

    LLM API 调用、JSON 解析、文件解析、向量库请求、工具调用、网络超时、模型输出格式错误等。

## 18. 推荐资料

- Python 官方教程：Errors and Exceptions
  https://docs.python.org/3/tutorial/errors.html

- Python 官方教程：Handling Exceptions
  https://docs.python.org/3/tutorial/errors.html#handling-exceptions

- Python 官方教程：Raising Exceptions
  https://docs.python.org/3/tutorial/errors.html#raising-exceptions

- Datawhale：聪明办法学 Python 第二版
  https://github.com/datawhalechina/learn-python-the-smart-way-v2
