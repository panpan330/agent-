# Python 模块导入 import

日期：2026-07-04

对应代码：

```text
projects/python-basics/question_utils.py
projects/python-basics/08_imports.py
projects/python-basics/08_practice_import_question_utils.py
```

## 1. 模块是什么

一个 Python 文件就是一个模块。

例如：

```text
question_utils.py
```

这个文件里定义了函数：

```python
def clean_question(question: str) -> str:
    return question.strip()
```

那么 `question_utils.py` 就是一个模块。

可以先理解成：

```text
模块 = 一个可以被别的 Python 文件复用的 .py 文件
```

## 2. import 是什么

`import` 用来导入别的模块。

导入后，就可以使用模块里的函数、变量、类。

示例：

```python
import question_utils

question_utils.clean_question("  hello  ")
```

## 3. 为什么要拆文件

如果所有代码都写在一个文件里，会越来越乱。

更好的方式是按职责拆开：

```text
question_utils.py   放问题处理函数
08_imports.py       导入并调用这些函数
```

后面 FastAPI 项目会这样拆：

```text
app/
  main.py
  core/config.py
  schemas/chat.py
  services/llm_client.py
```

## 4. import 整个模块

```python
import question_utils
```

调用时要带模块名：

```python
question_utils.clean_question(raw_question)
```

优点：

- 来源清楚。
- 不容易和当前文件里的函数重名。

缺点：

- 每次调用都要写模块名。

## 5. from ... import ...

也可以只导入某个函数：

```python
from question_utils import clean_question
```

调用时可以直接写：

```python
clean_question(raw_question)
```

优点：

- 写起来短。

缺点：

- 如果导入太多，可能看不清函数来自哪里。

## 6. as 起别名

可以给导入的函数或模块起别名。

```python
from question_utils import contains_keyword as has_keyword
```

调用：

```python
has_keyword(question, "Python")
```

别名适合：

- 原名字太长。
- 避免重名。
- 让业务含义更清楚。

## 7. 导入标准库

标准库是 Python 自带的库，不需要额外安装。

示例：

```python
import datetime
import json
```

使用当前时间：

```python
now = datetime.datetime.now()
```

字典转 JSON 字符串：

```python
json_text = json.dumps(data, ensure_ascii=False)
```

## 8. 导入第三方库

第三方库不是 Python 自带的，需要先安装。

例如 `requests`：

```powershell
uv add requests
```

导入：

```python
import requests
```

使用：

```python
response = requests.get("https://httpbin.org/get", timeout=5)
```

网络请求可能失败，所以真实项目里要处理异常。

## 9. 导入自己写的文件

同一个目录下有：

```text
question_utils.py
08_imports.py
```

在 `08_imports.py` 里可以写：

```python
import question_utils
```

或者：

```python
from question_utils import clean_question
```

这就是导入自己写的模块。

## 10. `__name__ == "__main__"`

你经常看到：

```python
if __name__ == "__main__":
    main()
```

意思是：

```text
只有当前文件被直接运行时，才执行 main()
如果这个文件被别人 import，就不自动执行 main()
```

例如 `question_utils.py` 可以直接运行：

```powershell
uv run python question_utils.py
```

也可以被别的文件导入：

```python
from question_utils import clean_question
```

有了 `if __name__ == "__main__"`，被导入时不会乱执行演示代码。

## 11. `__pycache__` 是什么

导入模块后，Python 可能生成：

```text
__pycache__/
```

这是 Python 的缓存文件夹，用来加快下次导入。

它不是我们手写的代码，通常不需要提交到 Git。

本仓库 `.gitignore` 已经忽略它。

## 12. 常见错误

### 错误 1：模块名写错

```python
import question_util
```

如果文件叫 `question_utils.py`，就会导入失败。

### 错误 2：文件不在 Python 能找到的位置

如果模块不在当前目录或包路径里，Python 找不到。

初学阶段先把练习文件放在同一个目录，避免路径问题。

### 错误 3：循环导入

比如：

```text
a.py 导入 b.py
b.py 又导入 a.py
```

这叫循环导入，容易导致错误。

初学阶段避免两个文件互相导入。

### 错误 4：导入时执行了不该执行的代码

如果模块里直接写：

```python
print("演示代码")
```

别人 import 这个模块时也会打印。

更好的写法：

```python
if __name__ == "__main__":
    print("演示代码")
```

## 13. 本节练习

创建文件：

```text
projects/python-basics/question_utils.py
projects/python-basics/08_practice_import_question_utils.py
```

要求：

1. 在 `question_utils.py` 里定义：
   - `clean_question`
   - `is_valid_question`
   - `contains_keyword`
   - `build_prompt`
2. 在 `08_practice_import_question_utils.py` 里导入这些函数。
3. 清洗问题。
4. 校验问题。
5. 判断是否包含 `Python`。
6. 判断是否包含 `import`。
7. 构建 prompt。
8. 打印结果字典。

## 14. 练习参考答案

`question_utils.py`：

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


if __name__ == "__main__":
    demo_question = "  我想学习 Python import  "
    cleaned = clean_question(demo_question)
    print("清洗后:", cleaned)
    print("是否有效:", is_valid_question(cleaned))
    print("是否包含 Python:", contains_keyword(cleaned, "Python"))
    print(build_prompt(cleaned))
```

`08_practice_import_question_utils.py`：

```python
from question_utils import build_prompt, clean_question, contains_keyword, is_valid_question


def main() -> None:
    raw_question = "   我想学习 Python import   "
    question = clean_question(raw_question)

    if not is_valid_question(question):
        print("问题无效")
        return

    result = {
        "question": question,
        "contains_python": contains_keyword(question, "Python"),
        "contains_import": contains_keyword(question, "import"),
        "prompt": build_prompt(question, role="Python 模块导入老师"),
    }

    print(result)


if __name__ == "__main__":
    main()
```

运行：

```powershell
uv run python question_utils.py
uv run python 08_practice_import_question_utils.py
```

## 15. 自测问题

1. 模块是什么？
2. `import` 是干什么的？
3. 为什么项目要拆成多个文件？
4. `import question_utils` 和 `from question_utils import clean_question` 有什么区别？
5. `as` 起别名有什么用？
6. 标准库和第三方库有什么区别？
7. 自己写的 `.py` 文件能不能被导入？
8. `if __name__ == "__main__"` 解决什么问题？
9. `__pycache__` 是什么？
10. 什么是循环导入？

## 16. 自测参考答案

1. 模块是什么？

   一个 Python 文件就是一个模块，可以被其他 Python 文件导入复用。

2. `import` 是干什么的？

   `import` 用来导入模块，让当前文件可以使用模块里的函数、变量或类。

3. 为什么项目要拆成多个文件？

   因为所有代码写在一个文件里会变乱。拆文件可以按职责组织代码，方便维护和复用。

4. `import question_utils` 和 `from question_utils import clean_question` 有什么区别？

   前者导入整个模块，调用时写 `question_utils.clean_question()`；后者只导入函数，调用时可以直接写 `clean_question()`。

5. `as` 起别名有什么用？

   可以缩短名字、避免重名，或者让调用时的名字更符合当前业务语义。

6. 标准库和第三方库有什么区别？

   标准库是 Python 自带的，不需要安装；第三方库需要通过 `uv add` 等方式安装。

7. 自己写的 `.py` 文件能不能被导入？

   可以。一个 `.py` 文件就是一个模块，只要 Python 能找到它，就可以导入。

8. `if __name__ == "__main__"` 解决什么问题？

   它让某些代码只在当前文件被直接运行时执行，被 import 时不执行。

9. `__pycache__` 是什么？

   Python 的模块缓存目录，用来加快导入速度，通常不需要提交到 Git。

10. 什么是循环导入？

    A 模块导入 B 模块，B 模块又导入 A 模块。这样容易导致导入过程出错。

## 17. 推荐资料

- Python 官方教程：Modules
  https://docs.python.org/3/tutorial/modules.html

- Python 官方教程：Executing modules as scripts
  https://docs.python.org/3/tutorial/modules.html#executing-modules-as-scripts

- Python 官方文档：import system
  https://docs.python.org/3/reference/import.html

- Datawhale：聪明办法学 Python 第二版
  https://github.com/datawhalechina/learn-python-the-smart-way-v2
