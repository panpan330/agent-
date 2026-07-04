# Python 函数 def

日期：2026-07-04

对应代码：

```text
projects/python-basics/07_functions.py
projects/python-basics/07_practice_question_functions.py
```

## 1. 函数是什么

函数是把一段代码封装起来，并给它起一个名字。

以后需要这段逻辑时，直接调用函数名。

最简单的函数：

```python
def say_hello() -> None:
    print("Hello, Python")
```

调用函数：

```python
say_hello()
```

可以先理解成：

```text
函数 = 有名字的一段可复用逻辑
```

## 2. 为什么需要函数

如果没有函数，代码会越来越长，逻辑会全部堆在一起。

例如清洗问题、判断问题、构建 prompt，如果都写在一起，会很乱。

拆成函数后：

```python
question = clean_question(raw_question)
valid = is_valid_question(question)
prompt = build_prompt(question)
```

好处：

- 代码更清楚。
- 可以重复使用。
- 更容易测试。
- 出错时更容易定位。
- 后面可以直接变成 FastAPI 接口或 LangChain tool。

## 3. def 基本写法

```python
def 函数名():
    函数体
```

示例：

```python
def say_hello() -> None:
    print("Hello, Python")
```

注意：

- `def` 表示定义函数。
- 函数名后面要有 `()`。
- 结尾要有冒号 `:`。
- 函数体需要缩进。

## 4. 参数

参数是调用函数时传进去的数据。

```python
def greet(name: str) -> None:
    print(f"你好，{name}")
```

调用：

```python
greet("Panpan")
```

这里：

- `name` 是参数名。
- `"Panpan"` 是传进去的值。

## 5. 返回值 return

`return` 用来把结果返回给调用者。

```python
def add(a: int, b: int) -> int:
    return a + b
```

调用：

```python
result = add(3, 5)
```

`result` 的值是：

```text
8
```

## 6. print 和 return 的区别

`print()` 是打印给人看。

`return` 是把结果交给程序继续使用。

示例：

```python
def add(a: int, b: int) -> int:
    return a + b
```

这个函数的结果可以继续参与计算。

如果只 `print(a + b)`，外面的程序拿不到结果。

## 7. 没有 return 会怎样

如果函数没有写 `return`，默认返回 `None`。

```python
def say_hello() -> None:
    print("Hello")
```

调用：

```python
result = say_hello()
print(result)
```

结果是：

```text
None
```

## 8. 默认参数

默认参数是在调用时可以不传的参数。

```python
def build_prompt(question: str, topic: str = "Python") -> str:
    return f"请解释 {topic}：{question}"
```

调用时不传 `topic`：

```python
build_prompt("什么是函数？")
```

`topic` 会使用默认值 `"Python"`。

调用时传 `topic`：

```python
build_prompt("什么是函数？", topic="Python 函数")
```

会使用传入的值。

## 9. 关键字参数

关键字参数就是调用时明确写参数名。

```python
build_prompt(question="什么是函数？", topic="Python 函数")
```

好处：

- 可读性强。
- 参数多时不容易传错顺序。

## 10. 类型提示

类型提示告诉读代码的人：参数和返回值应该是什么类型。

```python
def clean_question(question: str) -> str:
    return question.strip().lower()
```

含义：

- `question: str` 表示 `question` 应该是字符串。
- `-> str` 表示返回值应该是字符串。

类型提示不会自动阻止错误，但它能帮助编辑器提示，也能让代码更清楚。

## 11. 函数里调用函数

函数可以组合使用。

```python
def clean_question(question: str) -> str:
    return question.strip().lower()


def is_valid_question(question: str) -> bool:
    return len(question) >= 5


def process_question(raw_question: str) -> dict:
    question = clean_question(raw_question)
    valid = is_valid_question(question)
    return {
        "question": question,
        "valid": valid,
    }
```

这就是把复杂逻辑拆成小步骤。

## 12. 作用域：局部变量

函数里面定义的变量，通常只在函数里面能用。

```python
def clean_question(question: str) -> str:
    cleaned = question.strip()
    return cleaned
```

`cleaned` 是局部变量。

函数外面不能直接使用它。

## 13. AI 应用里的函数

后面会大量写这种函数：

```python
def clean_question(question: str) -> str:
    return question.strip()
```

```python
def build_prompt(question: str) -> str:
    return f"用户问题：{question}"
```

```python
def query_order(order_id: str) -> dict:
    return {"order_id": order_id, "status": "paid"}
```

FastAPI 接口也是函数：

```python
def health() -> dict:
    return {"status": "ok"}
```

LangChain tool 也经常是函数。

## 14. 常见错误

### 错误 1：忘记调用括号

```python
say_hello
```

这样只是拿到函数本身，没有执行。

正确：

```python
say_hello()
```

### 错误 2：忘记 return

```python
def add(a: int, b: int) -> int:
    a + b
```

这个函数返回 `None`。

正确：

```python
def add(a: int, b: int) -> int:
    return a + b
```

### 错误 3：参数数量不匹配

```python
def add(a: int, b: int) -> int:
    return a + b

add(1)
```

少传了一个参数，会报错。

### 错误 4：把 print 当 return

```python
def add(a: int, b: int) -> None:
    print(a + b)

result = add(1, 2)
print(result)
```

`result` 是 `None`，因为函数没有返回值。

## 15. 本节练习

创建文件：

```text
projects/python-basics/07_practice_question_functions.py
```

要求实现这些函数：

1. `clean_question(question: str) -> str`
   - 去掉左右空格。
2. `is_valid_question(question: str) -> bool`
   - 判断问题长度是否大于等于 5。
3. `contains_keyword(question: str, keyword: str) -> bool`
   - 判断问题里是否包含关键词，忽略大小写。
4. `build_prompt(question: str, role: str = "Python 学习助手") -> str`
   - 构建多行 prompt。
5. `check_score(score: float, threshold: float = 0.5) -> dict`
   - 根据检索分数判断是否可以回答。
6. `process_user_question(raw_question: str, score: float) -> dict`
   - 组合前面的函数，返回处理结果。

测试三种情况：

- 正常问题。
- 问题太短。
- 检索分数太低。

## 16. 练习参考答案

```python
def clean_question(question: str) -> str:
    return question.strip()


def is_valid_question(question: str) -> bool:
    return len(question) >= 5


def contains_keyword(question: str, keyword: str) -> bool:
    return keyword.lower() in question.lower()


def build_prompt(question: str, role: str = "Python 学习助手") -> str:
    return f"""你是一个{role}。
用户问题：{question}
请按“概念、例子、练习”的结构回答。"""


def check_score(score: float, threshold: float = 0.5) -> dict:
    if score < threshold:
        return {
            "can_answer": False,
            "reason": "检索分数太低",
        }

    return {
        "can_answer": True,
        "reason": "检索分数可用",
    }


def process_user_question(raw_question: str, score: float) -> dict:
    question = clean_question(raw_question)

    if not is_valid_question(question):
        return {
            "valid": False,
            "reason": "问题不能为空或太短",
            "question": question,
        }

    score_result = check_score(score)
    if not score_result["can_answer"]:
        return {
            "valid": False,
            "reason": score_result["reason"],
            "question": question,
        }

    return {
        "valid": True,
        "reason": None,
        "question": question,
        "contains_python": contains_keyword(question, "Python"),
        "prompt": build_prompt(question),
    }


def main() -> None:
    result = process_user_question("   我想学习 Python 函数   ", 0.82)
    print(result)

    short_result = process_user_question(" hi ", 0.82)
    print(short_result)

    low_score_result = process_user_question("我想学习 Python 函数", 0.32)
    print(low_score_result)


if __name__ == "__main__":
    main()
```

运行：

```powershell
uv run python 07_practice_question_functions.py
```

## 17. 自测问题

1. 函数是什么？
2. 为什么需要函数？
3. `def greet(name: str) -> None` 里 `name` 是什么？
4. `return` 是干什么的？
5. `print()` 和 `return` 有什么区别？
6. 函数没有 `return` 时默认返回什么？
7. 默认参数有什么用？
8. 关键字参数有什么好处？
9. 类型提示有什么用？
10. 为什么复杂逻辑要拆成多个小函数？

## 18. 自测参考答案

1. 函数是什么？

   函数是一段有名字的、可重复调用的代码逻辑。

2. 为什么需要函数？

   函数能减少重复代码，让逻辑更清楚，更容易测试和复用。

3. `def greet(name: str) -> None` 里 `name` 是什么？

   `name` 是参数，调用函数时需要传入具体值。

4. `return` 是干什么的？

   `return` 把函数的结果返回给调用者。

5. `print()` 和 `return` 有什么区别？

   `print()` 只是打印给人看；`return` 是把结果交给程序继续使用。

6. 函数没有 `return` 时默认返回什么？

   默认返回 `None`。

7. 默认参数有什么用？

   默认参数让调用者可以不传某些参数，函数会使用默认值。

8. 关键字参数有什么好处？

   可读性更好，参数多时不容易传错顺序。

9. 类型提示有什么用？

   类型提示让代码更清楚，也能帮助编辑器提示和后续静态检查。

10. 为什么复杂逻辑要拆成多个小函数？

    因为小函数职责更单一，容易理解、复用、测试和排查问题。

## 19. 推荐资料

- Python 官方教程：Defining Functions
  https://docs.python.org/3/tutorial/controlflow.html#defining-functions

- Python 官方教程：Default Argument Values
  https://docs.python.org/3/tutorial/controlflow.html#default-argument-values

- Python 官方教程：Keyword Arguments
  https://docs.python.org/3/tutorial/controlflow.html#keyword-arguments

- Datawhale：聪明办法学 Python 第二版
  https://github.com/datawhalechina/learn-python-the-smart-way-v2
