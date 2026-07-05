# Python 正则表达式 re

日期：2026-07-05

对应代码：

```text
projects/python-basics/17_regex.py
projects/python-basics/17_practice_regex.py
```

## 1. 正则表达式是什么

正则表达式是一种“文本匹配规则”。

它不是 Python 独有的东西，很多语言和工具都有正则。

可以先理解成：

```text
正则表达式 = 用一套符号描述你想找什么样的文本
```

例如：

```python
r"\d+"
```

表示：

```text
匹配一个或多个数字
```

## 2. 为什么要学正则

真实项目里，经常要从一段普通文本里提取结构化信息。

例如：

- 从用户问题里提取订单号。
- 从日志里提取 trace_id。
- 从文本里提取手机号、邮箱。
- 清理多个空格。
- 判断用户问题属于退款、物流还是发票。

AI 应用也一样。

大模型可以理解复杂语言，但很多明确格式的信息，用正则提取更稳定、更便宜、更可控。

## 3. re 模块

Python 用标准库 `re` 处理正则。

```python
import re
```

常用函数：

- `re.search()`：找有没有匹配。
- `re.findall()`：找出所有匹配。
- `re.sub()`：替换匹配内容。
- `re.fullmatch()`：判断整个字符串是否完全匹配。

## 4. 原始字符串 r"..."

正则里经常写反斜杠：

```python
\d
\s
\w
```

Python 字符串本身也会使用反斜杠转义。

为了避免混乱，写正则时通常使用原始字符串：

```python
r"\d+"
```

你可以先记住：

```text
写正则，默认用 r"..."
```

## 5. re.search()

`re.search()` 用来判断文本里是否有匹配内容。

```python
import re

text = "订单号是 ORD-20260705-001"
match = re.search(r"ORD-\d{8}-\d{3}", text)
```

如果找到，`match` 不是 `None`。

```python
if match is not None:
    print(match.group())
```

`match.group()` 表示取出匹配到的文本。

## 6. 订单号正则

示例订单号：

```text
ORD-20260705-001
```

规则：

- 固定以 `ORD-` 开头。
- 中间 8 位数字表示日期。
- 再一个 `-`。
- 最后 3 位数字表示序号。

正则：

```python
r"ORD-\d{8}-\d{3}"
```

解释：

- `ORD-`：匹配固定文本。
- `\d`：匹配数字。
- `{8}`：前面的规则重复 8 次。
- `{3}`：前面的规则重复 3 次。

## 7. re.findall()

`re.findall()` 用来找出所有匹配结果。

```python
text = "订单 ORD-20260705-001 和 ORD-20260705-002 都需要退款"
orders = re.findall(r"ORD-\d{8}-\d{3}", text)
```

结果：

```python
["ORD-20260705-001", "ORD-20260705-002"]
```

## 8. 常用符号

| 符号 | 含义 | 示例 |
| --- | --- | --- |
| `\d` | 数字 | `\d{3}` 匹配 3 个数字 |
| `\w` | 字母、数字、下划线 | `\w+` |
| `\s` | 空白字符 | 空格、换行、Tab |
| `.` | 任意字符，默认不匹配换行 | `a.b` |
| `+` | 一个或多个 | `\d+` |
| `*` | 零个或多个 | `\d*` |
| `?` | 零个或一个 | `https?` |
| `{n}` | 固定 n 次 | `\d{8}` |
| `{m,n}` | m 到 n 次 | `\d{2,4}` |
| `[]` | 字符范围 | `[3-9]` |
| `()` | 分组 | `(\d{8})` |
| `^` | 开头 | `^ORD` |
| `$` | 结尾 | `001$` |

## 9. 手机号正则

简单手机号规则：

```text
1 开头
第二位是 3 到 9
后面还有 9 位数字
```

正则：

```python
r"1[3-9]\d{9}"
```

解释：

- `1`：固定数字 1。
- `[3-9]`：匹配 3 到 9 之间任意一个数字。
- `\d{9}`：再匹配 9 个数字。

这个规则不是完整运营商校验，但足够做入门练习。

## 10. 邮箱正则

一个简化邮箱规则：

```python
r"[\w.-]+@[\w.-]+\.\w+"
```

解释：

- `[\w.-]+`：匹配用户名部分，允许字母数字下划线、点、横线。
- `@`：匹配固定符号。
- `[\w.-]+`：匹配域名主体。
- `\.`：匹配真正的点。
- `\w+`：匹配后缀，比如 `com`、`cn`。

注意：

邮箱完整规则非常复杂，真实生产系统通常会结合更成熟的校验方式。

## 11. re.sub()

`re.sub()` 用来替换匹配内容。

清理多个空格：

```python
text = "  Python    AI   学习   "
cleaned = re.sub(r"\s+", " ", text).strip()
```

解释：

- `\s+`：匹配一个或多个空白字符。
- `" "`：替换成一个普通空格。
- `.strip()`：去掉开头和结尾空格。

## 12. 手机号脱敏

需求：

```text
13812345678 -> 138****5678
```

代码：

```python
re.sub(r"(1[3-9]\d)\d{4}(\d{4})", r"\1****\2", text)
```

解释：

- `(1[3-9]\d)`：第一组，前三位。
- `\d{4}`：中间四位。
- `(\d{4})`：第二组，最后四位。
- `\1`：引用第一组。
- `\2`：引用第二组。

## 13. 分组 group

分组用 `()`。

```python
match = re.fullmatch(r"ORD-(\d{8})-(\d{3})", "ORD-20260705-001")
```

如果匹配成功：

```python
match.group(1)
match.group(2)
```

分别得到：

```text
20260705
001
```

## 14. fullmatch()

`re.search()` 是只要文本中有一部分匹配就算成功。

`re.fullmatch()` 要求整个字符串都匹配。

示例：

```python
re.fullmatch(r"\d{6}", "123456")
```

成功。

```python
re.fullmatch(r"\d{6}", "编号123456")
```

失败。

做格式校验时，通常用 `fullmatch()`。

## 15. flags

`flags` 是匹配选项。

忽略大小写：

```python
re.search(r"python", "I am learning Python", flags=re.IGNORECASE)
```

常见 `flags`：

- `re.IGNORECASE`：忽略大小写。
- `re.MULTILINE`：多行模式。
- `re.DOTALL`：让 `.` 也能匹配换行。

初学阶段先重点掌握 `re.IGNORECASE`。

## 16. 从日志里提取 trace_id

日志：

```text
2026-07-05 INFO trace_id=req-20260705-001 user_id=330 status=200
```

提取 trace_id：

```python
match = re.search(r"trace_id=([a-zA-Z0-9-]+)", log_line)
```

解释：

- `trace_id=`：固定文本。
- `(...)`：分组。
- `[a-zA-Z0-9-]+`：匹配字母、数字、横线，一个或多个。

## 17. 简单规则分类

用户问题：

```text
我的订单能退款吗？
```

可以用规则判断：

```python
if re.search(r"退款|退钱|退货", question):
    return "refund"
```

这里 `|` 表示“或者”。

```python
r"退款|退钱|退货"
```

含义是：

```text
匹配 退款 或 退钱 或 退货
```

## 18. 正则和 AI 的关系

不是所有事情都要交给大模型。

如果格式明确，比如订单号、手机号、邮箱、trace_id，用正则更合适：

- 快。
- 便宜。
- 稳定。
- 可测试。

如果用户语言复杂、意图模糊，再考虑让大模型理解。

后面做 Agent 时，经常会组合使用：

```text
正则提取明确字段
LLM 理解复杂语义
```

## 19. 常见错误

### 错误 1：忘记使用 r"..."

推荐：

```python
r"\d+"
```

不要一开始就写普通字符串：

```python
"\d+"
```

虽然有时也能跑，但容易因为转义变复杂。

### 错误 2：把 search 当 fullmatch

```python
re.search(r"\d{6}", "编号123456")
```

这会匹配成功。

但如果你要判断整个字符串是不是 6 位数字，应该用：

```python
re.fullmatch(r"\d{6}", "编号123456")
```

### 错误 3：正则写得过度复杂

正则越复杂，越难维护。

初学阶段先写简单、能读懂、能测试的规则。

### 错误 4：以为正则能理解语义

正则只能匹配文本模式，不能真正理解语义。

例如“我不想退款”里也包含“退款”两个字。

这种复杂意图不能只靠正则。

## 20. 本节练习

创建文件：

```text
projects/python-basics/17_practice_regex.py
```

要求：

1. 写函数 `extract_order_ids(text: str) -> list[str]`
   - 提取所有形如 `ORD-20260705-001` 的订单号。
2. 写函数 `is_valid_order_id(order_id: str) -> bool`
   - 用 `fullmatch()` 判断订单号是否合法。
3. 写函数 `extract_phone_numbers(text: str) -> list[str]`
   - 提取手机号。
4. 写函数 `extract_emails(text: str) -> list[str]`
   - 提取邮箱。
5. 写函数 `normalize_spaces(text: str) -> str`
   - 把多个空白字符变成一个空格。
6. 写函数 `mask_phone_numbers(text: str) -> str`
   - 手机号脱敏。
7. 写函数 `extract_log_fields(log_line: str) -> dict[str, str]`
   - 提取 `trace_id` 和 `user_id`。
8. 写函数 `classify_question(question: str) -> str`
   - 简单分类为 `refund`、`shipping`、`invoice`、`other`。

## 21. 练习参考答案

```python
import re


def extract_order_ids(text: str) -> list[str]:
    return re.findall(r"ORD-\d{8}-\d{3}", text)


def is_valid_order_id(order_id: str) -> bool:
    return re.fullmatch(r"ORD-\d{8}-\d{3}", order_id) is not None


def extract_phone_numbers(text: str) -> list[str]:
    return re.findall(r"1[3-9]\d{9}", text)


def extract_emails(text: str) -> list[str]:
    return re.findall(r"[\w.-]+@[\w.-]+\.\w+", text)


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def mask_phone_numbers(text: str) -> str:
    return re.sub(r"(1[3-9]\d)\d{4}(\d{4})", r"\1****\2", text)


def extract_log_fields(log_line: str) -> dict[str, str]:
    trace_match = re.search(r"trace_id=([a-zA-Z0-9-]+)", log_line)
    user_match = re.search(r"user_id=(\d+)", log_line)

    return {
        "trace_id": trace_match.group(1) if trace_match else "",
        "user_id": user_match.group(1) if user_match else "",
    }


def classify_question(question: str) -> str:
    rules = {
        "refund": r"退款|退钱|退货",
        "shipping": r"物流|快递|发货|配送",
        "invoice": r"发票|开票",
    }

    for category, pattern in rules.items():
        if re.search(pattern, question):
            return category

    return "other"
```

运行：

```powershell
uv run python 17_practice_regex.py
```

## 22. 自测问题

1. 正则表达式是什么？
2. 为什么写正则时常用 `r"..."`？
3. `re.search()` 和 `re.findall()` 有什么区别？
4. `re.search()` 和 `re.fullmatch()` 有什么区别？
5. `\d` 表示什么？
6. `+`、`*`、`?` 分别是什么意思？
7. `()` 在正则里有什么作用？
8. `|` 表示什么？
9. `re.sub()` 用来做什么？
10. 为什么订单号、手机号这类明确格式适合用正则？

## 23. 自测参考答案

1. 正则表达式是什么？

   正则表达式是一种文本匹配规则，用符号描述你想查找或替换什么样的文本。

2. 为什么写正则时常用 `r"..."`？

   因为正则里经常有反斜杠，原始字符串可以减少 Python 字符串转义带来的混乱。

3. `re.search()` 和 `re.findall()` 有什么区别？

   `search()` 找是否存在第一个匹配，返回 match 或 `None`；`findall()` 找出所有匹配，返回列表。

4. `re.search()` 和 `re.fullmatch()` 有什么区别？

   `search()` 只要字符串中某一部分匹配就成功；`fullmatch()` 要求整个字符串完全匹配。

5. `\d` 表示什么？

   `\d` 表示一个数字。

6. `+`、`*`、`?` 分别是什么意思？

   `+` 表示一个或多个；`*` 表示零个或多个；`?` 表示零个或一个。

7. `()` 在正则里有什么作用？

   `()` 用来分组，可以后续通过 `group(1)`、`group(2)` 取出对应部分。

8. `|` 表示什么？

   `|` 表示“或者”，比如 `退款|退钱|退货` 表示匹配其中任意一个。

9. `re.sub()` 用来做什么？

   `re.sub()` 用来把匹配到的内容替换成指定内容，常用于清洗文本和脱敏。

10. 为什么订单号、手机号这类明确格式适合用正则？

    因为它们格式固定，用正则提取更快、更稳定、更便宜，也更容易写测试验证。

## 24. 推荐资料

- Python 官方文档：re
  https://docs.python.org/3/library/re.html

- Python 官方 HOWTO：Regular Expression
  https://docs.python.org/3/howto/regex.html

- 菜鸟教程：Python 正则表达式
  https://www.runoob.com/python/python-reg-expressions.html
