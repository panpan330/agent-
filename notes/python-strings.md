# Python 字符串 str

日期：2026-07-04

对应代码：

```text
projects/python-basics/02_strings.py
projects/python-basics/02_practice_clean_question.py
```

## 1. 字符串是什么

字符串就是文本数据。

在 Python 里，字符串类型叫：

```python
str
```

例如：

```python
message = "Hello, Python"
```

这里：

- `"Hello, Python"` 是字符串值。
- `message` 是变量名。
- `type(message)` 会得到 `<class 'str'>`。

AI 应用里大量数据都是字符串：

- 用户输入的问题。
- prompt。
- 模型回答。
- 日志。
- 错误信息。
- 文档内容。
- RAG 里的 chunk。

## 2. 单引号、双引号、三引号

Python 字符串可以用单引号：

```python
text = 'I am learning Python'
```

也可以用双引号：

```python
text = "I am learning AI"
```

单引号和双引号大多数时候没有区别。

三引号适合写多行字符串：

```python
prompt = """你是一个 AI 学习助手。
请解释 Python 字符串。
每次都给出例子。"""
```

后面写 prompt 时，三引号会经常用到。

## 3. 字符串拼接

可以用 `+` 拼接字符串：

```python
first_name = "Pan"
last_name = "Pan"
full_name = first_name + last_name
```

结果：

```text
PanPan
```

注意：`+` 两边都必须是字符串。

错误示例：

```python
age = 25
message = "age=" + age
```

因为 `"age="` 是 `str`，`age` 是 `int`，不能直接相加。

## 4. f-string

更推荐用 f-string 拼接变量：

```python
name = "Panpan"
age = 25
message = f"我叫 {name}，今年 {age} 岁。"
```

优点：

- 清楚。
- 不用手动 `str(age)`。
- 很适合写日志、提示语、prompt。

## 5. 常用字符串方法

### strip()

去掉字符串左右两边的空白。

```python
text = "   hello   "
cleaned = text.strip()
```

结果：

```text
hello
```

常用于清洗用户输入。

### lower()

转小写。

```python
"HELLO".lower()
```

结果：

```text
hello
```

常用于关键词判断，避免大小写影响。

### upper()

转大写。

```python
"hello".upper()
```

结果：

```text
HELLO
```

### replace()

替换字符串中的内容。

```python
"I like AI".replace("AI", "Python")
```

结果：

```text
I like Python
```

### split()

把字符串拆成列表。

```python
words = "I want to learn Python".split(" ")
```

结果：

```python
["I", "want", "to", "learn", "Python"]
```

### join()

把多个字符串合并成一个字符串。

```python
words = ["I", "want", "to", "learn", "Python"]
text = "-".join(words)
```

结果：

```text
I-want-to-learn-Python
```

## 6. 字符串方法不会修改原字符串

Python 字符串是不可变的。

例如：

```python
text = " HELLO "
text.strip()
print(text)
```

`text` 还是原来的 `" HELLO "`。

正确写法：

```python
text = " HELLO "
text = text.strip()
print(text)
```

或者：

```python
cleaned_text = text.strip()
```

## 7. 索引和切片

字符串可以按位置取字符。

```python
language = "Python"
```

索引从 0 开始：

```python
language[0]  # P
language[1]  # y
```

负数从右边开始：

```python
language[-1]  # n
```

切片：

```python
language[0:2]  # Py
language[2:]   # thon
```

注意：

```text
[0:2] 包含 0，不包含 2
```

## 8. 判断是否包含

用 `in` 判断一个字符串里是否包含另一个字符串。

```python
question = "How can I learn Python?"
print("Python" in question)
```

结果：

```text
True
```

常用于简单关键词判断。

## 9. repr() 是什么

`repr()` 会显示字符串更“原始”的样子。

例如：

```python
text = "   hello   "
print(text)
print(repr(text))
```

普通 `print(text)` 不容易看出左右空格。

`repr(text)` 会显示：

```text
'   hello   '
```

所以调试字符串时，`repr()` 很有用。

## 10. prompt 字符串

后面写 AI 应用时，会经常写这种多行 prompt：

```python
role = "Python 基础老师"
topic = "字符串"

prompt = f"""你是一个{role}。
请用零基础能听懂的方式讲解：{topic}。
要求：
1. 先解释概念
2. 再给代码例子
3. 最后给练习题"""
```

这里同时用到了：

- 三引号多行字符串。
- f-string 插入变量。
- 普通文本排版。

## 11. 常见错误

### 错误 1：字符串和数字直接拼接

```python
age = 25
message = "age=" + age
```

修复：

```python
message = "age=" + str(age)
```

更推荐：

```python
message = f"age={age}"
```

### 错误 2：忘记接收方法返回值

```python
text = " hello "
text.strip()
print(text)
```

`strip()` 不会修改原字符串。要写：

```python
text = text.strip()
```

### 错误 3：索引越界

```python
language = "Python"
print(language[10])
```

字符串长度不够，会报错。

### 错误 4：大小写影响判断

```python
question = "I want to learn python"
print("Python" in question)
```

结果是：

```text
False
```

因为 `"Python"` 和 `"python"` 大小写不同。

修复：

```python
print("python" in question.lower())
```

## 12. 本节练习

创建文件：

```text
projects/python-basics/02_practice_clean_question.py
```

要求：

1. 定义原始用户问题：

   ```python
   raw_question = "   HELLO, I want to learn AI!!!   "
   ```

2. 用 `strip()` 去掉左右空格。
3. 用 `lower()` 转成小写。
4. 用 `replace()` 把 `ai` 替换成 `python`。
5. 用 `split(" ")` 拆成单词列表。
6. 判断是否包含关键词 `python`。
7. 用三引号和 f-string 拼出一个 prompt。
8. 打印每一步结果。

## 13. 练习参考答案

```python
def main() -> None:
    raw_question = "   HELLO, I want to learn AI!!!   "

    cleaned_question = raw_question.strip().lower()
    python_question = cleaned_question.replace("ai", "python")

    words = python_question.split(" ")
    keyword = "python"
    has_keyword = keyword in python_question

    prompt = f"""你是一个 Python 学习助手。
用户问题：{python_question}
问题单词列表：{words}
是否包含关键词 {keyword}：{has_keyword}

请根据用户问题，给出适合初学者的解释。"""

    print("原始问题:", repr(raw_question))
    print("清洗后问题:", cleaned_question)
    print("替换后问题:", python_question)
    print("单词列表:", words)
    print("是否包含关键词:", has_keyword)
    print("prompt:")
    print(prompt)


if __name__ == "__main__":
    main()
```

运行：

```powershell
uv run python 02_practice_clean_question.py
```

## 14. 自测问题

1. 字符串是什么？
2. 单引号和双引号有什么区别？
3. 三引号适合什么场景？
4. 为什么推荐 f-string？
5. `strip()` 做什么？
6. `split()` 和 `join()` 分别做什么？
7. 字符串索引为什么从 0 开始？
8. `language[0:2]` 为什么结果是 `Py`，不是 `Pyt`？
9. 为什么 `text.strip()` 后，原来的 `text` 没变？
10. 为什么 `"Python" in "python"` 是 `False`？

## 15. 自测参考答案

1. 字符串是什么？

   字符串是文本数据，在 Python 里类型是 `str`。

2. 单引号和双引号有什么区别？

   大多数时候没有区别，都可以表示字符串。只是在字符串内部包含引号时，可以互相搭配减少转义。

3. 三引号适合什么场景？

   适合写多行字符串，比如长文本、prompt、说明文案。

4. 为什么推荐 f-string？

   因为它可以清楚地把变量插入字符串，不需要手动做很多字符串拼接和类型转换。

5. `strip()` 做什么？

   去掉字符串左右两边的空白字符，常用于清洗用户输入。

6. `split()` 和 `join()` 分别做什么？

   `split()` 把字符串拆成列表；`join()` 把多个字符串合并成一个字符串。

7. 字符串索引为什么从 0 开始？

   Python 和很多编程语言一样，序列下标从 0 开始。第一个字符的位置是 0。

8. `language[0:2]` 为什么结果是 `Py`，不是 `Pyt`？

   切片规则是包含开始位置，不包含结束位置。`[0:2]` 包含 0 和 1，不包含 2。

9. 为什么 `text.strip()` 后，原来的 `text` 没变？

   因为字符串不可变。`strip()` 返回一个新字符串，不会修改原来的字符串。

10. 为什么 `"Python" in "python"` 是 `False`？

    因为字符串比较区分大小写。`P` 和 `p` 不是同一个字符。

## 16. 推荐资料

- Python 官方教程：Text  
  https://docs.python.org/3/tutorial/introduction.html#text

- Python 官方文档：Text Sequence Type str  
  https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str

- Datawhale：聪明办法学 Python 第二版  
  https://github.com/datawhalechina/learn-python-the-smart-way-v2

- 小甲鱼 Python 视频：字符串相关章节  
  https://www.bilibili.com/video/BV1xs411Q799/
