# Python 函数进阶

日期：2026-07-05

对应代码：

```text
projects/python-basics/15_function_advanced.py
projects/python-basics/15_practice_function_advanced.py
```

## 1. 本节学什么

第 7 节我们已经学过普通函数：

```python
def clean_question(question: str) -> str:
    return question.strip()
```

这一节继续往前走，学习函数在真实项目里更常见的写法：

- 关键字专用参数：强制调用时写参数名。
- `*args`：接收任意数量的位置参数。
- `**kwargs`：接收任意数量的关键字参数。
- 解包调用：把列表、字典拆开传给函数。
- 默认参数的坑：为什么默认参数不要随便写 `[]`。
- `lambda`：临时小函数。
- 函数作为参数：把函数传给另一个函数。
- 函数返回函数：先理解基本用法。
- 装饰器：FastAPI 里 `@app.get()` 的基础。

## 2. 关键字专用参数

普通函数可以这样写：

```python
def build_prompt(question: str, role: str = "Python 学习助手") -> str:
    return f"角色：{role}\n问题：{question}"
```

调用时既可以按位置传：

```python
build_prompt("什么是函数？", "AI 助手")
```

也可以写参数名：

```python
build_prompt("什么是函数？", role="AI 助手")
```

但是参数多了以后，按位置传容易看错顺序。

可以用 `*` 让后面的参数必须写名字：

```python
def build_prompt(question: str, *, role: str = "Python 学习助手", max_lines: int = 3) -> str:
    return f"角色：{role}\n问题：{question}\n最多回答 {max_lines} 行"
```

正确调用：

```python
build_prompt("什么是函数进阶？", role="AI 学习助手", max_lines=2)
```

错误调用：

```python
build_prompt("什么是函数进阶？", "AI 学习助手", 2)
```

因为 `role` 和 `max_lines` 必须写参数名。

## 3. 为什么需要关键字专用参数

它能让调用更清楚。

例如：

```python
build_prompt("解释 RAG", role="AI 教练", max_lines=5)
```

比下面这种更容易读：

```python
build_prompt("解释 RAG", "AI 教练", 5)
```

FastAPI、Pydantic、很多第三方库都会大量使用这种设计。

## 4. `*args` 是什么

`*args` 用来接收任意数量的位置参数。

示例：

```python
def merge_keywords(*keywords: str) -> list[str]:
    result = []

    for keyword in keywords:
        cleaned_keyword = keyword.strip().lower()
        if cleaned_keyword:
            result.append(cleaned_keyword)

    return result
```

调用：

```python
merge_keywords("Python", "AI", "FastAPI")
```

函数里面的 `keywords` 是一个 tuple：

```python
("Python", "AI", "FastAPI")
```

## 5. `args` 这个名字固定吗

不固定。

真正起作用的是前面的 `*`。

但是 Python 社区约定俗成写成：

```python
*args
```

所以初学阶段也按这个习惯写。

## 6. `**kwargs` 是什么

`**kwargs` 用来接收任意数量的关键字参数。

示例：

```python
def build_ai_request(question: str, **metadata: object) -> dict[str, object]:
    return {
        "question": question,
        "metadata": metadata,
    }
```

调用：

```python
build_ai_request(
    "怎么学习 Python？",
    source="lesson-15",
    stream=False,
    user_id=330,
)
```

函数里面的 `metadata` 是一个字典：

```python
{
    "source": "lesson-15",
    "stream": False,
    "user_id": 330,
}
```

## 7. `kwargs` 这个名字固定吗

也不固定。

真正起作用的是前面的 `**`。

但是社区习惯写成：

```python
**kwargs
```

所以我们也这样写。

## 8. 什么时候用 `*args` 和 `**kwargs`

先记住一个原则：

```text
普通函数优先写清楚的参数名。
只有确实需要接收不固定数量的参数时，才用 *args 或 **kwargs。
```

适合 `*args` 的场景：

- 合并多个标签。
- 计算多个分数。
- 接收多个文件路径。

适合 `**kwargs` 的场景：

- 透传可选配置。
- 收集额外 metadata。
- 包装第三方库函数。

## 9. 解包调用

解包调用是把容器拆开传给函数。

列表或元组用 `*` 解包：

```python
raw_keywords = ["Python", "LangChain", "RAG"]
merge_keywords(*raw_keywords)
```

等价于：

```python
merge_keywords("Python", "LangChain", "RAG")
```

字典用 `**` 解包：

```python
metadata = {"source": "local-note", "topic": "function-advanced"}
build_ai_request("什么是 kwargs？", **metadata)
```

等价于：

```python
build_ai_request("什么是 kwargs？", source="local-note", topic="function-advanced")
```

## 10. 默认参数的坑

这是 Python 初学者常见坑。

错误写法：

```python
def add_tag_wrong(tag: str, tags: list[str] = []) -> list[str]:
    tags.append(tag)
    return tags
```

你可能以为每次调用都会得到一个新列表。

但实际不是。

```python
print(add_tag_wrong("python"))
print(add_tag_wrong("ai"))
```

结果可能是：

```text
['python']
['python', 'ai']
```

第二次调用时，第一次的数据还在。

## 11. 为什么默认参数会这样

函数定义时，默认参数对象只创建一次。

所以这个 `[]` 不是每次调用都新建，而是被重复使用。

可以先记住：

```text
默认参数不要直接写可变对象，比如 []、{}、set()。
```

## 12. 默认参数的安全写法

用 `None` 表示“调用者没有传”：

```python
def add_tag_safe(tag: str, tags: list[str] | None = None) -> list[str]:
    if tags is None:
        tags = []

    tags.append(tag)
    return tags
```

这样每次不传 `tags` 时，函数内部都会创建一个新列表。

## 13. lambda 是什么

`lambda` 是临时小函数。

普通函数：

```python
def get_score(document: dict[str, object]) -> object:
    return document["score"]
```

lambda 写法：

```python
lambda document: document["score"]
```

常见用途是配合 `sorted()`：

```python
sorted_documents = sorted(documents, key=lambda document: document["score"], reverse=True)
```

## 14. lambda 什么时候用

适合简单逻辑：

```python
lambda item: item["score"]
```

不适合复杂逻辑。

如果逻辑超过一行，或者需要多个判断，优先写成普通函数。

普通函数更容易读，也更容易调试。

## 15. 函数也是对象

在 Python 里，函数可以像变量一样被传递。

```python
def clean_question(question: str) -> str:
    return question.strip()


processor = clean_question
```

这里 `processor` 指向了函数本身。

调用：

```python
processor("  Python  ")
```

等价于：

```python
clean_question("  Python  ")
```

## 16. 函数作为参数

可以把函数传给另一个函数。

```python
from collections.abc import Callable


def apply_to_questions(
    questions: list[str],
    processor: Callable[[str], str],
) -> list[str]:
    result = []

    for question in questions:
        result.append(processor(question))

    return result
```

调用：

```python
apply_to_questions(["  Python  "], clean_question)
```

这里 `processor` 是一个函数。

`Callable[[str], str]` 表示：

```text
这是一个可调用对象，接收一个 str，返回一个 str。
```

## 17. 函数返回函数

函数也可以返回另一个函数。

```python
def make_keyword_checker(keyword: str):
    def checker(text: str) -> bool:
        return keyword.lower() in text.lower()

    return checker
```

调用：

```python
contains_python = make_keyword_checker("Python")
print(contains_python("我正在学习 Python"))
```

`contains_python` 现在就是一个函数。

这个写法后面理解回调、闭包、装饰器时会有用。

## 18. 装饰器是什么

装饰器是在不修改原函数代码的情况下，给函数增加额外逻辑。

比如：

```python
def print_before_and_after(func):
    def wrapper(question: str) -> str:
        print("调用前")
        result = func(question)
        print("调用后")
        return result

    return wrapper
```

使用：

```python
@print_before_and_after
def clean_question_with_log(question: str) -> str:
    return question.strip()
```

这等价于：

```python
clean_question_with_log = print_before_and_after(clean_question_with_log)
```

## 19. 为什么现在要知道装饰器

因为 FastAPI 会这样写：

```python
@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
```

这里的 `@app.get("/health")` 就是装饰器。

你现在不需要立刻手写复杂装饰器，但必须知道：

```text
@xxx 是在给下面的函数增加额外能力。
```

## 20. 常见错误

### 错误 1：滥用 `*args` 和 `**kwargs`

如果参数本来很明确，不要写成：

```python
def create_user(*args, **kwargs):
    ...
```

初学阶段优先写清楚：

```python
def create_user(name: str, age: int) -> dict[str, object]:
    ...
```

### 错误 2：默认参数写 `[]`

错误：

```python
def add_item(item: str, items: list[str] = []) -> list[str]:
    ...
```

安全写法：

```python
def add_item(item: str, items: list[str] | None = None) -> list[str]:
    if items is None:
        items = []
    ...
```

### 错误 3：lambda 写太复杂

简单逻辑可以用：

```python
lambda item: item["score"]
```

复杂逻辑用普通函数。

### 错误 4：把函数调用结果传进去

如果一个函数需要接收函数本身：

```python
apply_to_questions(questions, clean_question)
```

不要写成：

```python
apply_to_questions(questions, clean_question())
```

`clean_question()` 是调用函数，`clean_question` 才是函数本身。

## 21. 本节练习

创建文件：

```text
projects/python-basics/15_practice_function_advanced.py
```

要求：

1. 写函数 `merge_tags(*tags: str) -> list[str]`
   - 接收任意数量标签。
   - 去掉左右空格。
   - 转小写。
   - 去重。
2. 写函数 `build_chat_request(question, *, stream=False, **metadata)`
   - `stream` 必须使用关键字传参。
   - `metadata` 收集额外信息。
3. 写函数 `append_history_safe(message, history=None)`
   - 使用安全默认参数写法。
4. 写函数 `apply_processor(items, processor)`
   - 把函数作为参数传入。
5. 写函数 `make_min_score_filter(min_score)`
   - 返回一个检查文档分数的函数。
6. 写一个简单装饰器 `log_call(func)`
   - 调用函数前打印原始输入。
   - 调用函数后打印处理结果。

## 22. 练习参考答案

```python
from collections.abc import Callable


def merge_tags(*tags: str) -> list[str]:
    result = []

    for tag in tags:
        cleaned_tag = tag.strip().lower()
        if cleaned_tag and cleaned_tag not in result:
            result.append(cleaned_tag)

    return result


def build_chat_request(
    question: str,
    *,
    stream: bool = False,
    **metadata: object,
) -> dict[str, object]:
    return {
        "question": question,
        "stream": stream,
        "metadata": metadata,
    }


def append_history_safe(message: str, history: list[str] | None = None) -> list[str]:
    if history is None:
        history = []

    history.append(message)
    return history


def apply_processor(items: list[str], processor: Callable[[str], str]) -> list[str]:
    result = []

    for item in items:
        result.append(processor(item))

    return result


def make_min_score_filter(min_score: float) -> Callable[[dict[str, object]], bool]:
    def checker(document: dict[str, object]) -> bool:
        score = document.get("score", 0.0)
        if not isinstance(score, int | float):
            return False
        return float(score) >= min_score

    return checker


def log_call(func: Callable[[str], str]) -> Callable[[str], str]:
    def wrapper(text: str) -> str:
        print("调用前:", text)
        result = func(text)
        print("调用后:", result)
        return result

    return wrapper
```

运行：

```powershell
uv run python 15_practice_function_advanced.py
```

## 23. 自测问题

1. `*args` 是什么？
2. `**kwargs` 是什么？
3. `args` 和 `kwargs` 这两个名字是固定的吗？
4. `merge_keywords(*raw_keywords)` 里的 `*` 是什么意思？
5. `build_ai_request("问题", **metadata)` 里的 `**` 是什么意思？
6. 为什么默认参数不要直接写 `[]`？
7. 安全的可变默认参数写法是什么？
8. `lambda` 适合什么场景？
9. 函数作为参数传递时，应该传 `clean_question` 还是 `clean_question()`？
10. 装饰器 `@xxx` 大概是什么意思？

## 24. 自测参考答案

1. `*args` 是什么？

   `*args` 用来接收任意数量的位置参数，函数内部通常把它当作 tuple 使用。

2. `**kwargs` 是什么？

   `**kwargs` 用来接收任意数量的关键字参数，函数内部通常把它当作 dict 使用。

3. `args` 和 `kwargs` 这两个名字是固定的吗？

   不是。真正起作用的是 `*` 和 `**`，但社区习惯写成 `args` 和 `kwargs`。

4. `merge_keywords(*raw_keywords)` 里的 `*` 是什么意思？

   这里的 `*` 表示把列表或元组拆开，作为多个位置参数传给函数。

5. `build_ai_request("问题", **metadata)` 里的 `**` 是什么意思？

   这里的 `**` 表示把字典拆开，作为多个关键字参数传给函数。

6. 为什么默认参数不要直接写 `[]`？

   因为默认参数对象在函数定义时只创建一次，多次调用会共用同一个列表，容易出现旧数据残留。

7. 安全的可变默认参数写法是什么？

   默认写 `None`，函数内部判断如果是 `None`，再创建新的列表、字典或集合。

8. `lambda` 适合什么场景？

   适合很短、很简单的临时函数，比如 `sorted()` 里的 `key`。

9. 函数作为参数传递时，应该传 `clean_question` 还是 `clean_question()`？

   应该传 `clean_question`，表示函数本身；`clean_question()` 是立刻调用函数。

10. 装饰器 `@xxx` 大概是什么意思？

    装饰器是在不修改原函数代码的情况下，给函数增加额外能力。FastAPI 的 `@app.get()` 就是这种写法。

## 25. 推荐资料

- Python 官方教程：More on Defining Functions
  https://docs.python.org/3/tutorial/controlflow.html#more-on-defining-functions

- Python 官方教程：Lambda Expressions
  https://docs.python.org/3/tutorial/controlflow.html#lambda-expressions

- Python 官方教程：Keyword Arguments
  https://docs.python.org/3/tutorial/controlflow.html#keyword-arguments

- Python 官方文档：Callable
  https://docs.python.org/3/library/typing.html#typing.Callable
