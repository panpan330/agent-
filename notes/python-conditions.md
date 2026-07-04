# Python 条件判断 if

日期：2026-07-04

对应代码：

```text
projects/python-basics/05_conditions.py
projects/python-basics/05_practice_question_check.py
```

## 1. 条件判断是什么

条件判断让程序根据不同情况走不同分支。

最基本形式：

```python
if 条件:
    条件成立时执行的代码
```

例如：

```python
age = 18

if age >= 18:
    print("成年人")
```

如果 `age >= 18` 是 `True`，就执行缩进里的代码。

## 2. 为什么需要条件判断

真实程序不可能永远只走一条路。

后端和 AI 应用里会经常判断：

- 用户有没有登录。
- 用户有没有权限。
- 参数是不是空。
- 问题是不是太短。
- 检索分数是否足够高。
- 是否需要调用工具。
- 是否需要人工确认。

示例：

```python
if not question:
    print("问题不能为空")
```

## 3. if / else

`else` 表示条件不成立时执行。

```python
question = "怎么学习 Python？"

if question:
    print("用户问题:", question)
else:
    print("问题不能为空")
```

如果 `question` 不是空字符串，就走 `if`。

如果 `question` 是空字符串，就走 `else`。

## 4. if / elif / else

多个条件时用 `elif`。

```python
score = 82

if score >= 90:
    print("优秀")
elif score >= 60:
    print("及格")
else:
    print("不及格")
```

Python 会从上到下判断，命中一个分支后，后面的分支就不再判断。

## 5. 比较运算符

| 运算符 | 含义 |
| --- | --- |
| `==` | 等于 |
| `!=` | 不等于 |
| `>` | 大于 |
| `>=` | 大于等于 |
| `<` | 小于 |
| `<=` | 小于等于 |

注意：

```python
age = 18
```

这是赋值。

```python
age == 18
```

这是判断是否相等。

## 6. 布尔值 True / False

条件判断最终看的是布尔值。

```python
age >= 18
```

结果要么是：

```python
True
```

要么是：

```python
False
```

## 7. and / or / not

### and

两个条件都成立才是 `True`。

```python
if is_logged_in and has_permission:
    print("可以访问")
```

### or

至少一个条件成立就是 `True`。

```python
if is_logged_in or has_permission:
    print("至少满足一个条件")
```

### not

取反。

```python
if not has_permission:
    print("没有权限")
```

## 8. 空字符串、空列表、None 的判断

这些值在条件判断里会被当成 False：

```python
""
[]
None
```

所以可以写：

```python
if not question:
    print("问题不能为空")
```

```python
if not chunks:
    print("没有检索结果")
```

```python
if user is None:
    print("用户不存在")
```

判断 `None` 时，更推荐：

```python
user is None
user is not None
```

## 9. 字符串和列表里的判断

字符串包含判断：

```python
if "Python" in user_question:
    print("问题里提到了 Python")
```

列表包含判断：

```python
if "字典" in finished_topics:
    print("已经学过字典")
```

## 10. 字典字段判断

字典经常来自请求体或配置。

```python
request = {
    "question": "怎么学习 LangChain？",
    "has_permission": True,
}

if request.get("question") and request.get("has_permission"):
    print("问题有效，并且用户有权限")
```

这里用 `get()` 是为了避免 key 不存在时报错。

## 11. AI 应用里的拒答判断

RAG 场景里，经常根据检索分数决定是否回答。

```python
retrieval_score = 0.42

if retrieval_score < 0.5:
    print("没有找到足够可靠的资料，应该拒答或提示用户补充信息")
else:
    print("可以基于检索结果回答")
```

这是 AI 应用里非常重要的思路：

```text
不是所有问题都应该回答。
资料不可靠时，要拒答或提示用户补充信息。
```

## 12. 缩进非常重要

Python 用缩进表示代码块。

正确：

```python
if age >= 18:
    print("成年人")
```

错误：

```python
if age >= 18:
print("成年人")
```

缩进不对会直接报错。

## 13. 常见错误

### 错误 1：把 `=` 当成 `==`

错误：

```python
if age = 18:
    print("18岁")
```

正确：

```python
if age == 18:
    print("18岁")
```

### 错误 2：忘记冒号

错误：

```python
if age >= 18
    print("成年人")
```

正确：

```python
if age >= 18:
    print("成年人")
```

### 错误 3：大小写问题

Python 里布尔值是：

```python
True
False
```

不是：

```python
true
false
```

### 错误 4：条件顺序写错

错误：

```python
score = 95

if score >= 60:
    print("及格")
elif score >= 90:
    print("优秀")
```

`95` 会先命中 `score >= 60`，所以永远不会走到优秀。

正确：

```python
if score >= 90:
    print("优秀")
elif score >= 60:
    print("及格")
```

## 14. 本节练习

创建文件：

```text
projects/python-basics/05_practice_question_check.py
```

要求：

1. 创建请求字典：

   ```python
   request = {
       "user_id": "u001",
       "question": "  我想学习 Python 条件判断  ",
       "has_permission": True,
       "finished_topics": ["变量", "字符串", "列表", "字典"],
   }
   ```

2. 取出并清洗问题。
3. 判断问题是否为空。
4. 判断问题长度是否小于 5。
5. 判断用户是否有权限。
6. 如果检查通过，打印清洗后的问题。
7. 判断问题是否包含 `"Python"`。
8. 判断问题是否包含 `"条件判断"`。
9. 判断是否已经学过 `"字典"` 和 `"列表"`。
10. 根据 `retrieval_score` 判断：
    - 大于等于 0.8：检索结果很可靠。
    - 大于等于 0.5：检索结果一般。
    - 否则：检索结果不可靠。

## 15. 练习参考答案

```python
def main() -> None:
    request = {
        "user_id": "u001",
        "question": "  我想学习 Python 条件判断  ",
        "has_permission": True,
        "finished_topics": ["变量", "字符串", "列表", "字典"],
    }

    raw_question = request.get("question", "")
    question = raw_question.strip()
    has_permission = request.get("has_permission", False)
    finished_topics = request.get("finished_topics", [])

    if not question:
        print("问题不能为空")
    elif len(question) < 5:
        print("问题太短，请补充更多信息")
    elif not has_permission:
        print("用户没有权限提问")
    else:
        print("问题检查通过")
        print("清洗后的问题:", question)

        if "Python" in question:
            print("问题和 Python 有关")

        if "条件判断" in question:
            print("问题和条件判断有关")

        if "字典" in finished_topics and "列表" in finished_topics:
            print("已经具备学习条件判断的前置基础")
        else:
            print("建议先复习列表和字典")

    retrieval_score = 0.68
    if retrieval_score >= 0.8:
        print("检索结果很可靠，可以直接回答")
    elif retrieval_score >= 0.5:
        print("检索结果一般，回答时要谨慎并提示来源")
    else:
        print("检索结果不可靠，应该拒答或让用户补充信息")


if __name__ == "__main__":
    main()
```

运行：

```powershell
uv run python 05_practice_question_check.py
```

## 16. 自测问题

1. 条件判断解决什么问题？
2. `if / elif / else` 的执行顺序是什么？
3. `=` 和 `==` 有什么区别？
4. `and`、`or`、`not` 分别是什么意思？
5. `if not question` 可以判断什么？
6. 为什么判断 `None` 推荐用 `is None`？
7. `"Python" in question` 是什么意思？
8. 为什么条件顺序写错会导致逻辑错误？
9. 为什么 RAG 里要根据检索分数判断是否拒答？
10. Python 里为什么缩进很重要？

## 17. 自测参考答案

1. 条件判断解决什么问题？

   让程序根据不同情况执行不同代码分支。

2. `if / elif / else` 的执行顺序是什么？

   从上到下判断，命中第一个成立的分支后，后面的分支不再执行。如果都不成立，执行 `else`。

3. `=` 和 `==` 有什么区别？

   `=` 是赋值，把右边的值给左边变量；`==` 是比较，判断两边是否相等。

4. `and`、`or`、`not` 分别是什么意思？

   `and` 表示两个条件都成立；`or` 表示至少一个条件成立；`not` 表示取反。

5. `if not question` 可以判断什么？

   可以判断 `question` 是否为空字符串或其他假值。

6. 为什么判断 `None` 推荐用 `is None`？

   因为 `None` 是 Python 里的单例空值，用 `is None` 表达更准确。

7. `"Python" in question` 是什么意思？

   判断字符串 `question` 里是否包含 `"Python"`。

8. 为什么条件顺序写错会导致逻辑错误？

   因为 Python 会从上到下命中第一个成立条件。宽泛条件写前面，后面的更严格条件可能永远执行不到。

9. 为什么 RAG 里要根据检索分数判断是否拒答？

   因为检索结果不可靠时强行回答容易胡编。分数太低时应该拒答或让用户补充信息。

10. Python 里为什么缩进很重要？

    Python 用缩进表示代码块。缩进决定哪些代码属于 `if`、`for`、函数等结构。

## 18. 推荐资料

- Python 官方教程：if Statements  
  https://docs.python.org/3/tutorial/controlflow.html#if-statements

- Python 官方文档：Boolean Operations  
  https://docs.python.org/3/library/stdtypes.html#boolean-operations-and-or-not

- Python 官方文档：Comparisons  
  https://docs.python.org/3/library/stdtypes.html#comparisons

- Datawhale：聪明办法学 Python 第二版  
  https://github.com/datawhalechina/learn-python-the-smart-way-v2
