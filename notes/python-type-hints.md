# Python 类型提示 type hints

日期：2026-07-04

对应代码：

```text
projects/python-basics/11_type_hints.py
projects/python-basics/11_practice_typed_question.py
```

## 1. 类型提示是什么

类型提示是在 Python 代码里标注变量、参数、返回值应该是什么类型。

示例：

```python
def greet(name: str) -> str:
    return f"你好，{name}"
```

这里：

- `name: str` 表示参数 `name` 应该是字符串。
- `-> str` 表示函数返回值应该是字符串。

## 2. 为什么 Python 也需要类型提示

Python 是动态类型语言，不像 Java 那样必须声明类型。

但是项目变大后，如果没有类型提示，别人很难知道：

- 这个函数需要什么参数？
- 参数应该是什么类型？
- 返回值是什么？
- 这个字典里大概有什么结构？

类型提示能让代码更清楚，也能帮助编辑器提示错误。

## 3. 变量类型提示

```python
name: str = "Panpan"
age: int = 25
height: float = 1.75
is_learning_ai: bool = True
```

常见类型：

| 类型提示 | 含义 |
| --- | --- |
| `str` | 字符串 |
| `int` | 整数 |
| `float` | 小数 |
| `bool` | 布尔值 |
| `None` | 空值 |

## 4. 函数参数和返回值类型提示

```python
def add(a: int, b: int) -> int:
    return a + b
```

含义：

- `a` 应该是 `int`。
- `b` 应该是 `int`。
- 返回值应该是 `int`。

## 5. 没有返回值时写 None

如果函数只是打印，不返回结果：

```python
def print_message(message: str) -> None:
    print(message)
```

`-> None` 表示这个函数没有有意义的返回值。

## 6. list[str]

表示字符串列表。

```python
topics: list[str] = ["变量", "字符串", "列表"]
```

函数参数：

```python
def get_first_topic(topics: list[str]) -> str | None:
    if not topics:
        return None
    return topics[0]
```

## 7. dict[str, object]

表示 key 是字符串，value 可以是多种对象。

```python
def build_user(name: str, age: int, skills: list[str]) -> dict[str, object]:
    return {
        "name": name,
        "age": age,
        "skills": skills,
    }
```

这里 value 有：

- 字符串。
- 整数。
- 列表。

所以用 `object` 表示比较宽泛。

## 8. dict[str, str]

如果字典里 key 和 value 都是字符串：

```python
metadata: dict[str, str] = {
    "source": "python-basics",
    "topic": "type hints",
}
```

这种结构很适合 metadata。

## 9. str | None

表示返回值可能是字符串，也可能是 `None`。

```python
def get_first_topic(topics: list[str]) -> str | None:
    if not topics:
        return None
    return topics[0]
```

如果列表为空，返回 `None`。

如果列表不为空，返回字符串。

## 10. dict[str, str] | None

表示参数可以是字典，也可以是 `None`。

```python
def build_ai_request(question: str, metadata: dict[str, str] | None = None) -> dict[str, object]:
    if metadata is None:
        metadata = {}
    return {
        "question": question,
        "metadata": metadata,
    }
```

这种写法很常见，因为默认参数不要直接写 `{}`。

## 11. Any

`Any` 表示任意类型。

```python
from typing import Any


def print_anything(value: Any) -> None:
    print(value)
```

`Any` 很灵活，但不要滥用。

如果到处都是 `Any`，类型提示就失去意义了。

## 12. 类型提示不会自动校验

看这个函数：

```python
def add(a: int, b: int) -> int:
    return a + b
```

如果调用：

```python
add("3", "5")
```

Python 运行时不会自动拦截。

结果是：

```text
35
```

因为字符串加字符串是拼接。

这说明：

```text
类型提示主要是给人和工具看的，不是运行时强制校验。
```

## 13. 类型提示和 Pydantic 的关系

类型提示本身不自动校验。

Pydantic 会利用类型提示做运行时校验。

后面 FastAPI 里会写：

```python
class ChatRequest(BaseModel):
    question: str
    stream: bool = False
```

这里的 `question: str`、`stream: bool` 会被 Pydantic 用来校验请求体。

所以现在学类型提示，是为后面的 Pydantic 和 FastAPI 打基础。

## 14. 常见错误

### 错误 1：以为类型提示会自动拦截错误

```python
def add(a: int, b: int) -> int:
    return a + b

add("3", "5")
```

运行时不会自动报错。

### 错误 2：返回值类型写错

```python
def get_age() -> str:
    return 25
```

标注返回 `str`，实际返回 `int`。这会误导别人。

### 错误 3：过度使用 Any

```python
def process(data: Any) -> Any:
    ...
```

这样看不出输入输出结构。

### 错误 4：复杂字典类型写得太随意

```python
dict
```

不如：

```python
dict[str, object]
dict[str, str]
```

更清楚。

## 15. 本节练习

创建文件：

```text
projects/python-basics/11_practice_typed_question.py
```

要求：

1. 给 `clean_question` 添加类型提示。
2. 给 `is_valid_question` 添加类型提示。
3. 给 `build_metadata` 添加类型提示。
4. 给 `build_prompt` 添加类型提示和默认参数。
5. 给 `process_question` 添加类型提示。
6. 处理 `metadata` 可能为 `None` 的情况。
7. 返回结果字典。

## 16. 练习参考答案

```python
def clean_question(question: str) -> str:
    return question.strip()


def is_valid_question(question: str) -> bool:
    return len(question) >= 5


def build_metadata(source: str, topic: str) -> dict[str, str]:
    return {
        "source": source,
        "topic": topic,
    }


def build_prompt(question: str, role: str = "Python 学习助手") -> str:
    return f"""你是一个{role}。
用户问题：{question}
请用零基础能理解的方式回答。"""


def process_question(raw_question: str, metadata: dict[str, str] | None = None) -> dict[str, object]:
    question = clean_question(raw_question)

    if metadata is None:
        metadata = {}

    if not is_valid_question(question):
        return {
            "valid": False,
            "question": question,
            "reason": "问题不能为空或太短",
            "metadata": metadata,
            "prompt": None,
        }

    return {
        "valid": True,
        "question": question,
        "reason": None,
        "metadata": metadata,
        "prompt": build_prompt(question),
    }


def main() -> None:
    metadata = build_metadata(source="python-basics", topic="type hints")

    result = process_question("  我想学习 Python 类型提示  ", metadata)
    print(result)

    invalid_result = process_question(" hi ")
    print(invalid_result)


if __name__ == "__main__":
    main()
```

运行：

```powershell
uv run python 11_practice_typed_question.py
```

## 17. 自测问题

1. 类型提示是什么？
2. Python 为什么还需要类型提示？
3. `question: str` 表示什么？
4. `-> dict[str, object]` 表示什么？
5. `list[str]` 表示什么？
6. `str | None` 表示什么？
7. `Any` 是什么，为什么不能滥用？
8. 类型提示会不会在运行时自动校验？
9. 类型提示和 Pydantic 有什么关系？
10. 为什么 `metadata: dict[str, str] | None = None` 比默认 `{}` 更稳？

## 18. 自测参考答案

1. 类型提示是什么？

   类型提示是在代码里标注变量、参数、返回值应该是什么类型。

2. Python 为什么还需要类型提示？

   因为项目变大后，类型提示能提高可读性，帮助编辑器提示错误，也为 FastAPI/Pydantic 等框架提供结构信息。

3. `question: str` 表示什么？

   表示参数 `question` 应该是字符串。

4. `-> dict[str, object]` 表示什么？

   表示函数返回一个字典，key 是字符串，value 可以是不同类型的对象。

5. `list[str]` 表示什么？

   表示一个列表，里面的元素应该都是字符串。

6. `str | None` 表示什么？

   表示值可能是字符串，也可能是 `None`。

7. `Any` 是什么，为什么不能滥用？

   `Any` 表示任意类型。滥用会让类型提示失去约束和说明作用。

8. 类型提示会不会在运行时自动校验？

   不会。Python 默认不会因为类型提示自动拦截错误类型。

9. 类型提示和 Pydantic 有什么关系？

   Pydantic 会读取类型提示，并在运行时根据这些类型提示校验数据。

10. 为什么 `metadata: dict[str, str] | None = None` 比默认 `{}` 更稳？

    因为可变默认值 `{}` 可能在多次调用之间共享状态，容易产生隐藏 bug。用 `None` 再在函数里创建新字典更安全。

## 19. 推荐资料

- Python 官方文档：typing
  https://docs.python.org/3/library/typing.html

- Python 官方文档：Type Hinting
  https://docs.python.org/3/howto/typing.html

- mypy 类型检查速查
  https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html

- Datawhale：聪明办法学 Python 第二版
  https://github.com/datawhalechina/learn-python-the-smart-way-v2
