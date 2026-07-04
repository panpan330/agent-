# Python 变量和基本类型

日期：2026-07-04

对应代码：

```text
projects/python-basics/01_variables_types.py
```

## 1. 变量是什么

变量可以先理解成：**给一个值起名字**。

例如：

```python
name = "Panpan"
age = 25
```

含义是：

- `"Panpan"` 是一个字符串值。
- `25` 是一个整数值。
- `name` 是指向 `"Panpan"` 的变量名。
- `age` 是指向 `25` 的变量名。

以后写 `name`，Python 就能找到它对应的值。

## 2. Python 变量和 Java 变量的区别

Java 通常这样写：

```java
String name = "Panpan";
int age = 25;
```

Java 的变量声明时就写了类型：

```text
name 是 String
age 是 int
```

Python 通常这样写：

```python
name = "Panpan"
age = 25
```

Python 不需要显式写类型。解释器会根据右边的值判断类型：

```text
"Panpan" -> str
25 -> int
```

这叫动态类型。

## 3. 基本类型

本节先掌握 5 个最常见类型：

| 类型 | Python 名字 | 示例 | 含义 |
| --- | --- | --- | --- |
| 整数 | `int` | `25` | 没有小数点的数字 |
| 小数 | `float` | `1.75` | 带小数点的数字 |
| 字符串 | `str` | `"Panpan"` | 文本 |
| 布尔值 | `bool` | `True` / `False` | 真或假 |
| 空值 | `NoneType` | `None` | 暂时没有值 |

注意：

```python
25
```

是数字。

```python
"25"
```

是字符串。

它们看起来像，但类型不同。

## 4. type() 是什么

`type()` 用来查看一个值或变量的类型。

```python
age = 25
print(type(age))
```

输出：

```text
<class 'int'>
```

说明 `age` 当前指向的是 `int` 类型的值。

## 5. Python 变量可以重新指向不同类型

示例：

```python
score = 100
score = "A+"
```

第一次：

```text
score -> int
```

第二次：

```text
score -> str
```

这在 Python 里可以运行。

但真实项目里不要随便这么写，因为会降低可读性，让别人不知道 `score` 到底应该是什么类型。

## 6. 类型转换

用户输入、HTTP 请求、环境变量里拿到的数据，经常是字符串。

比如：

```python
user_input_age = "30"
```

如果要做数学计算，需要先转成整数：

```python
next_year_age = int(user_input_age) + 1
```

常见转换：

```python
int("30")       # 字符串转整数
float("19.99") # 字符串转小数
str(25)        # 数字转字符串
bool(1)        # 转布尔值
```

## 7. 字符串拼接和 f-string

不推荐这样写复杂字符串：

```python
message = "name=" + name + ", age=" + str(age)
```

更推荐 f-string：

```python
message = f"name={name}, age={age}"
```

原因：

- 更清楚。
- 不用手动把数字 `str(age)`。
- 后面写日志、接口返回、调试信息会经常用。

## 8. None 是什么

`None` 表示“没有值”。

例如：

```python
phone = None
```

意思不是空字符串，也不是 0，而是这个变量现在没有手机号。

判断是否有值：

```python
has_phone = phone is not None
```

## 9. 常见错误

### 错误 1：字符串和数字直接相加

```python
age = 25
message = "age=" + age
```

这样会报错，因为 Python 不知道你是想做字符串拼接还是数字计算。

正确写法：

```python
message = "age=" + str(age)
```

或：

```python
message = f"age={age}"
```

### 错误 2：把字符串当数字算

```python
age = "30"
next_year_age = age + 1
```

错误原因：

```text
age 是 str
1 是 int
```

正确写法：

```python
next_year_age = int(age) + 1
```

### 错误 3：大小写写错

Python 的布尔值必须是：

```python
True
False
```

不是：

```python
true
false
```

`None` 也必须首字母大写。

## 10. 本节练习

在 `projects/python-basics` 里新建一个文件：

```text
01_practice_profile.py
```

要求：

1. 定义姓名 `name`。
2. 定义年龄 `age`。
3. 定义身高 `height`。
4. 定义是否正在学习 AI `is_learning_ai`。
5. 定义当前工作方向 `target_role`。
6. 用 `type()` 打印每个变量的类型。
7. 用 f-string 输出一句完整介绍。

示例输出：

```text
我叫 Panpan，今年 25 岁，身高 1.75，目标方向是 AI 应用工程师。
```

### 练习参考答案

`projects/python-basics/01_practice_profile.py`：

```python
def main() -> None:
    name = "Panpan"
    age = 25
    height = 1.75
    is_learning_ai = True
    target_role = "AI 应用工程师"

    print("type(name):", type(name))
    print("type(age):", type(age))
    print("type(height):", type(height))
    print("type(is_learning_ai):", type(is_learning_ai))
    print("type(target_role):", type(target_role))

    introduction = (
        f"我叫 {name}，今年 {age} 岁，身高 {height}，"
        f"正在学习 AI：{is_learning_ai}，目标方向是 {target_role}。"
    )
    print(introduction)


if __name__ == "__main__":
    main()
```

运行：

```powershell
uv run python 01_practice_profile.py
```

### 故意制造错误并修复

错误示例：

```python
age = "25"
next_year_age = age + 1
```

错误原因：

```text
age 是 str
1 是 int
Python 不能把字符串和整数直接相加
```

修复：

```python
age = "25"
next_year_age = int(age) + 1
print(next_year_age)
```

## 11. 自测问题

学完这一节，要能回答：

1. 变量是什么？
2. Python 为什么不用写 `int age = 25`？
3. `25` 和 `"25"` 有什么区别？
4. `type()` 是干什么的？
5. `None` 和空字符串 `""` 一样吗？
6. 为什么 `"age=" + age` 会报错？
7. f-string 解决了什么问题？
8. 为什么真实项目里不建议同一个变量一会儿是 `int`，一会儿是 `str`？

### 自测参考答案

1. 变量是什么？

   变量是给一个值起的名字。代码后面可以通过这个名字找到对应的值。

2. Python 为什么不用写 `int age = 25`？

   因为 Python 是动态类型语言。解释器会根据右边的值判断类型，`25` 会被识别为 `int`。

3. `25` 和 `"25"` 有什么区别？

   `25` 是整数，可以做数学计算；`"25"` 是字符串，本质是文本，不能直接和整数相加。

4. `type()` 是干什么的？

   `type()` 用来查看一个值或变量当前的类型，例如 `type(25)` 是 `<class 'int'>`。

5. `None` 和空字符串 `""` 一样吗？

   不一样。`None` 表示没有值；`""` 是一个存在的字符串，只是内容为空。

6. 为什么 `"age=" + age` 会报错？

   如果 `age` 是整数，左边是字符串，右边是整数。Python 不会自动把整数转成字符串，所以会报类型错误。

7. f-string 解决了什么问题？

   f-string 让字符串里插入变量更简单、更清楚，也能自动把数字等值转换成字符串形式。

8. 为什么真实项目里不建议同一个变量一会儿是 `int`，一会儿是 `str`？

   因为会降低可读性，也容易造成类型错误。别人看到变量名时无法判断它到底应该是什么类型，维护成本会变高。

## 12. 后续笔记规则

从下一节开始，每篇学习笔记都固定包含：

```text
概念解释
最小代码
常见错误
本节练习
练习参考答案
自测问题
自测参考答案
推荐资料
```

## 13. 推荐资料

- Python 官方教程：数字和字符串  
  https://docs.python.org/3/tutorial/introduction.html

- Datawhale：聪明办法学 Python 第二版  
  https://github.com/datawhalechina/learn-python-the-smart-way-v2

- 小甲鱼 Python 视频：变量、字符串、数字类型  
  https://www.bilibili.com/video/BV1xs411Q799/
