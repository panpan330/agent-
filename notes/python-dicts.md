# Python 字典 dict

日期：2026-07-04

对应代码：

```text
projects/python-basics/04_dicts.py
projects/python-basics/04_practice_user_profile.py
```

## 1. 字典是什么

字典是 Python 里用来保存**键值对**的数据类型。

类型名是：

```python
dict
```

示例：

```python
user = {
    "name": "Panpan",
    "age": 25,
    "target_role": "AI 应用工程师",
}
```

这里：

- `"name"` 是 key，叫键。
- `"Panpan"` 是 value，叫值。
- `"age"` 是 key。
- `25` 是 value。

可以先理解成：

```text
字典 = 有字段名的数据
```

## 2. 为什么需要字典

列表适合保存一组同类数据：

```python
skills = ["Java", "Python", "FastAPI"]
```

但是如果要表示一个用户，只用列表就很不清楚：

```python
user = ["Panpan", 25, "AI 应用工程师"]
```

别人不知道：

```text
第一个值是什么意思？
第二个值是什么意思？
第三个值是什么意思？
```

字典更清楚：

```python
user = {
    "name": "Panpan",
    "age": 25,
    "target_role": "AI 应用工程师",
}
```

每个值都有字段名。

## 3. 字典和列表的区别

| 对比 | 列表 list | 字典 dict |
| --- | --- | --- |
| 数据形式 | 一组按顺序排列的值 | 一组 key-value |
| 访问方式 | 通过索引访问 | 通过 key 访问 |
| 示例 | `tasks[0]` | `user["name"]` |
| 适合场景 | 多个同类数据 | 一个对象的多个字段 |

简单记：

```text
列表：多个东西
字典：一个东西的多个属性
```

## 4. 创建字典

字典用大括号 `{}`。

```python
user = {
    "name": "Panpan",
    "age": 25,
}
```

空字典：

```python
data = {}
```

## 5. 读取字段

用 key 读取：

```python
user["name"]
```

示例：

```python
print(user["name"])
print(user["age"])
```

如果 key 不存在，会报错。

## 6. 修改字段

```python
user["age"] = 26
```

如果 `"age"` 已经存在，就是修改。

## 7. 添加字段

```python
user["city"] = "Shanghai"
```

如果 `"city"` 不存在，就是新增。

字典的修改和新增写法一样，区别取决于 key 是否已经存在。

## 8. 删除字段 pop()

```python
removed_city = user.pop("city")
```

含义：

- 删除 `"city"` 这个字段。
- 返回被删除的值。

如果 key 不存在，会报错。

## 9. get() 安全读取

直接读取：

```python
user["email"]
```

如果 `"email"` 不存在，会报错。

更安全的写法：

```python
user.get("email")
```

如果不存在，返回 `None`。

也可以给默认值：

```python
user.get("email", "未填写邮箱")
```

如果不存在，返回：

```text
未填写邮箱
```

## 10. keys / values / items

```python
user.keys()
```

返回所有 key。

```python
user.values()
```

返回所有 value。

```python
user.items()
```

返回所有 key-value。

真实开发里最常用的是 `items()`，因为经常需要同时拿 key 和 value。

## 11. 遍历字典

```python
for key, value in user.items():
    print(f"{key}: {value}")
```

含义：

```text
每次从 user 里取出一组 key-value
key 保存字段名
value 保存字段值
```

## 12. 字典里可以放列表

```python
user = {
    "name": "Panpan",
    "skills": ["Java", "Python", "FastAPI"],
}
```

读取第一个技能：

```python
user["skills"][0]
```

这里分两步：

```text
user["skills"] -> 取出技能列表
[0] -> 取出列表第一个元素
```

## 13. 嵌套字典

字典里也可以放字典。

```python
profile = {
    "user": {
        "name": "Panpan",
        "age": 25,
    },
    "learning": {
        "current_topic": "dict",
    },
}
```

读取用户名：

```python
profile["user"]["name"]
```

读取当前主题：

```python
profile["learning"]["current_topic"]
```

## 14. 字典和 JSON 的关系

Python 字典长得很像 JSON。

Python 字典：

```python
user = {
    "name": "Panpan",
    "age": 25,
}
```

JSON：

```json
{
  "name": "Panpan",
  "age": 25
}
```

区别：

- 字典是 Python 内存里的数据结构。
- JSON 是一种文本格式，常用于网络传输和接口请求响应。

后面 FastAPI 接口、LLM API 请求体、tool calling 参数都会经常在字典和 JSON 之间转换。

## 15. AI 应用里的字典例子

聊天请求体可以表示成字典：

```python
chat_request = {
    "model": "gpt-example",
    "messages": [
        {"role": "system", "content": "你是一个 Python 老师"},
        {"role": "user", "content": "请解释字典"},
    ],
    "temperature": 0.7,
    "stream": False,
}
```

这里包含：

- 字符串。
- 数字。
- 布尔值。
- 列表。
- 嵌套字典。

这就是后面 AI API 请求体的基本结构。

## 16. 常见错误

### 错误 1：读取不存在的 key

```python
user["email"]
```

如果 `email` 不存在，会报错。

更稳：

```python
user.get("email", "未填写邮箱")
```

### 错误 2：key 写错

```python
user["Name"]
```

如果真实 key 是 `"name"`，这里会报错。

字典 key 区分大小写。

### 错误 3：搞混列表索引和字典 key

列表：

```python
tasks[0]
```

字典：

```python
user["name"]
```

不能写：

```python
user[0]
```

除非字典真的有 key `0`。

### 错误 4：嵌套结构层级没看清

```python
chat_request["content"]
```

如果 `content` 在 `messages` 里面，这样取不到。

正确：

```python
chat_request["messages"][1]["content"]
```

## 17. 本节练习

创建文件：

```text
projects/python-basics/04_practice_user_profile.py
```

要求：

1. 创建用户字典：

   ```python
   user = {
       "name": "Panpan",
       "age": 25,
       "skills": ["Java", "Python"],
   }
   ```

2. 打印姓名、年龄、技能。
3. 把年龄修改为 26。
4. 添加目标岗位 `target_role`。
5. 给 `skills` 添加 `"FastAPI"`。
6. 用 `get()` 安全读取 `email`，默认值是 `"未填写邮箱"`。
7. 用 `items()` 遍历所有字段。
8. 构造一个模拟 AI 请求体字典，包含：
   - `user_id`
   - `question`
   - `metadata`
9. 读取并打印请求体里的 `question` 和 `metadata.topic`。

## 18. 练习参考答案

```python
def main() -> None:
    user = {
        "name": "Panpan",
        "age": 25,
        "skills": ["Java", "Python"],
    }

    print("原始用户:", user)

    print("姓名:", user["name"])
    print("年龄:", user["age"])
    print("技能:", user["skills"])

    user["age"] = 26
    user["target_role"] = "AI 应用工程师"
    user["skills"].append("FastAPI")

    print("更新后的用户:", user)

    email = user.get("email", "未填写邮箱")
    print("邮箱:", email)

    print("用户字段:")
    for key, value in user.items():
        print(f"{key}: {value}")

    ai_request = {
        "user_id": "u001",
        "question": "我应该怎么学习 Python 字典？",
        "metadata": {
            "source": "python-basics",
            "topic": "dict",
            "level": "beginner",
        },
    }

    print("AI 请求体:", ai_request)
    print("问题:", ai_request["question"])
    print("主题:", ai_request["metadata"]["topic"])


if __name__ == "__main__":
    main()
```

运行：

```powershell
uv run python 04_practice_user_profile.py
```

## 19. 自测问题

1. 字典是什么？
2. 字典用什么符号创建？
3. 字典里的 key 和 value 分别是什么？
4. 列表和字典最核心的区别是什么？
5. `user["name"]` 是什么意思？
6. `user.get("email")` 和 `user["email"]` 有什么区别？
7. `items()` 是干什么的？
8. 字典里能不能放列表？
9. 字典和 JSON 是同一个东西吗？
10. `chat_request["messages"][1]["content"]` 是怎么一步步取到值的？

## 20. 自测参考答案

1. 字典是什么？

   字典是保存键值对的数据结构，适合表示一个对象的多个字段。

2. 字典用什么符号创建？

   用大括号 `{}` 创建。

3. 字典里的 key 和 value 分别是什么？

   key 是字段名，value 是字段对应的值。

4. 列表和字典最核心的区别是什么？

   列表通过索引访问，适合保存多个同类值；字典通过 key 访问，适合保存一个对象的多个字段。

5. `user["name"]` 是什么意思？

   从 `user` 字典里读取 key 为 `"name"` 的值。

6. `user.get("email")` 和 `user["email"]` 有什么区别？

   `user["email"]` 在 key 不存在时会报错；`user.get("email")` 不存在时返回 `None`，也可以设置默认值。

7. `items()` 是干什么的？

   返回字典里的所有 key-value，常用于遍历字典。

8. 字典里能不能放列表？

   可以。比如 `{"skills": ["Java", "Python"]}`。

9. 字典和 JSON 是同一个东西吗？

   不是。字典是 Python 的数据结构，JSON 是文本格式。它们长得像，但用途和类型不同。

10. `chat_request["messages"][1]["content"]` 是怎么一步步取到值的？

    先从 `chat_request` 取出 `"messages"` 列表，再取列表索引 1 的第二条消息字典，最后从这个字典里取 `"content"` 字段。

## 21. 推荐资料

- Python 官方教程：Dictionaries  
  https://docs.python.org/3/tutorial/datastructures.html#dictionaries

- Python 官方文档：Mapping Types dict  
  https://docs.python.org/3/library/stdtypes.html#mapping-types-dict

- Datawhale：聪明办法学 Python 第二版  
  https://github.com/datawhalechina/learn-python-the-smart-way-v2
