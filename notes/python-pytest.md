# Python pytest 测试基础

日期：2026-07-05

对应代码：

```text
projects/python-basics/lesson18_pytest_basics.py
projects/python-basics/lesson18_practice_pytest.py
projects/python-basics/test_lesson18_pytest_basics.py
projects/python-basics/test_lesson18_practice_pytest.py
```

## 1. 测试是什么

测试就是用代码验证代码是否符合预期。

例如你写了一个加法函数：

```python
def add(a: int, b: int) -> int:
    return a + b
```

你可以写一个测试：

```python
def test_add() -> None:
    assert add(2, 3) == 5
```

可以先理解成：

```text
测试 = 自动检查你的函数有没有按预期工作
```

## 2. 为什么要学测试

只靠手动运行脚本，很容易漏问题。

测试能帮你：

- 确认函数结果对不对。
- 防止以后改代码时把旧功能改坏。
- 快速验证边界情况。
- 让别人相信你的代码不是“刚好能跑”。
- 后面写 FastAPI、RAG、Agent 时做质量保障。

工程里非常重要的一点是：

```text
会写代码只是第一步，会验证代码才是能做项目。
```

## 3. pytest 是什么

`pytest` 是 Python 里非常常用的测试框架。

它不是标准库，需要安装。

本项目使用 uv 安装开发依赖：

```powershell
uv add --dev pytest
```

安装后运行测试：

```powershell
uv run pytest
```

## 4. 为什么是开发依赖

pytest 是开发时用来验证代码的工具，线上运行程序时通常不需要它。

所以它适合放在开发依赖里。

`pyproject.toml` 里会出现类似配置：

```toml
[dependency-groups]
dev = [
    "pytest>=...",
]
```

## 5. pytest 怎么找到测试

pytest 会自动查找符合命名规则的文件和函数。

常见规则：

- 测试文件名：`test_*.py` 或 `*_test.py`
- 测试函数名：`test_` 开头

例如：

```text
test_lesson18_pytest_basics.py
```

里面的函数：

```python
def test_add() -> None:
    ...
```

pytest 会自动找到并运行它。

## 6. 为什么本节文件叫 lesson18

前面很多脚本叫：

```text
15_function_advanced.py
```

这种文件可以直接运行：

```powershell
uv run python 15_function_advanced.py
```

但它不能被普通方式导入：

```python
import 15_function_advanced
```

因为 Python 模块名不能以数字开头。

测试文件需要导入被测试函数，所以本节使用：

```text
lesson18_pytest_basics.py
```

这是更接近真实项目的命名方式。

## 7. assert 是什么

`assert` 用来断言一个条件必须成立。

```python
assert add(2, 3) == 5
```

如果条件成立，测试通过。

如果条件不成立，测试失败。

例如：

```python
assert add(2, 3) == 6
```

会失败。

## 8. 第一个测试

被测试函数：

```python
def add(a: int, b: int) -> int:
    return a + b
```

测试函数：

```python
def test_add() -> None:
    assert add(2, 3) == 5
```

运行：

```powershell
uv run pytest
```

## 9. 测试字符串清洗

被测试函数：

```python
def clean_question(question: str) -> str:
    return " ".join(question.strip().split())
```

测试：

```python
def test_clean_question() -> None:
    assert clean_question("  Python    pytest   怎么学？  ") == "Python pytest 怎么学？"
```

这里验证了：

- 去掉开头和结尾空格。
- 把中间多个空格压成一个空格。

## 10. 参数化测试

如果同一个函数要测多组输入，可以用 `pytest.mark.parametrize`。

```python
@pytest.mark.parametrize(
    ("order_id", "expected"),
    [
        ("ORD-20260705-001", True),
        ("ORD-20260705-01", False),
        ("订单 ORD-20260705-001", False),
    ],
)
def test_is_valid_order_id(order_id: str, expected: bool) -> None:
    assert is_valid_order_id(order_id) is expected
```

这相当于自动运行 3 次测试。

## 11. 为什么参数化很重要

很多规则不能只测一个例子。

例如订单号校验：

- 正确格式应该通过。
- 少一位应该失败。
- 前面多了中文也应该失败。

参数化可以让测试更完整、更清楚。

## 12. 测试异常

有些函数遇到错误输入时，应该主动报错。

被测试函数：

```python
def parse_score(value: object) -> float:
    score = float(value)
    if score < 0 or score > 1:
        raise ValueError("score must be between 0 and 1")
    return score
```

测试：

```python
def test_parse_score_error() -> None:
    with pytest.raises(ValueError):
        parse_score("abc")
```

含义：

```text
这段代码应该抛出 ValueError。
如果没有抛出，测试失败。
```

## 13. tmp_path 是什么

`tmp_path` 是 pytest 提供的临时目录。

测试文件读写时，不要直接写真实项目文件。

使用：

```python
def test_load_tasks_from_json(tmp_path: Path) -> None:
    tasks_file = tmp_path / "tasks.json"
```

pytest 会给每个测试准备一个临时目录。

测试结束后，不会污染你的项目目录。

## 14. 测试 JSON 读写

写测试数据：

```python
tasks_file.write_text(
    json.dumps([{"name": "学习 pytest", "done": True}], ensure_ascii=False),
    encoding="utf-8",
)
```

读取并断言：

```python
tasks = load_tasks_from_json(tasks_file)
assert len(tasks) == 1
assert tasks[0]["name"] == "学习 pytest"
```

这种写法以后测试配置文件、报告文件、RAG 文档解析都会用到。

## 15. 测试正则规则

正则非常适合写测试。

例如订单号：

```python
@pytest.mark.parametrize(
    ("order_id", "expected"),
    [
        ("ORD-20260705-001", True),
        ("ORD-20260705-01", False),
    ],
)
def test_is_valid_order_id(order_id: str, expected: bool) -> None:
    assert is_valid_order_id(order_id) is expected
```

正则一旦改错，测试会立刻发现。

## 16. 测试分类规则

```python
@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("我的订单怎么退款？", "refund"),
        ("快递什么时候发货？", "shipping"),
        ("帮我开发票", "invoice"),
        ("Python 怎么学？", "other"),
    ],
)
def test_classify_question(question: str, expected: str) -> None:
    assert classify_question(question) == expected
```

这能验证规则分类是否符合预期。

## 17. 测试文件怎么组织

小项目可以先放在同一层目录：

```text
lesson18_pytest_basics.py
test_lesson18_pytest_basics.py
```

稍微正式一点的项目会这样：

```text
src/
  app/
    service.py
tests/
  test_service.py
```

我们后面做 FastAPI 项目时会使用更正式的结构。

## 18. 运行指定测试文件

运行全部测试：

```powershell
uv run pytest
```

运行指定测试文件：

```powershell
uv run pytest test_lesson18_pytest_basics.py
```

更安静地运行：

```powershell
uv run pytest -q
```

`-q` 是 quiet，输出更简短。

## 19. 看测试失败

测试失败不是坏事。

失败信息会告诉你：

- 哪个测试失败。
- 实际结果是什么。
- 期望结果是什么。
- 失败发生在哪一行。

这就是测试的价值。

它不是只告诉你“错了”，还告诉你“哪里不符合预期”。

## 20. 常见错误

### 错误 1：测试文件名不对

pytest 默认不会自动运行：

```text
demo.py
```

推荐：

```text
test_demo.py
```

### 错误 2：测试函数名不以 test_ 开头

不会被自动识别：

```python
def check_add():
    ...
```

推荐：

```python
def test_add():
    ...
```

### 错误 3：只测试正常情况

不要只测正确输入。

还要测：

- 空字符串。
- 错误格式。
- 边界值。
- 异常情况。

### 错误 4：测试依赖真实文件

不要在测试里直接修改真实数据文件。

用 `tmp_path` 创建临时文件更安全。

## 21. 本节练习

创建文件：

```text
projects/python-basics/lesson18_practice_pytest.py
projects/python-basics/test_lesson18_practice_pytest.py
```

要求：

1. 写函数 `normalize_tags(raw_tags)`
   - 清洗标签。
   - 转小写。
   - 去重。
2. 写函数 `require_order_id(text)`
   - 从文本里提取订单号。
   - 没有订单号时抛出 `ValueError`。
3. 写函数 `build_report(user_name, tags, order_id)`
   - 用户名不能为空。
   - 返回报告字典。
4. 写函数 `save_report(path, report)`
   - 保存 JSON 文件。
5. 写函数 `load_report(path)`
   - 读取 JSON 文件。
6. 给上面函数写 pytest 测试。

## 22. 练习参考答案

业务函数：

```python
def normalize_tags(raw_tags: list[str]) -> list[str]:
    result = []

    for raw_tag in raw_tags:
        tag = raw_tag.strip().lower()
        if tag and tag not in result:
            result.append(tag)

    return result
```

```python
def require_order_id(text: str) -> str:
    match = re.search(r"ORD-\d{8}-\d{3}", text)

    if match is None:
        raise ValueError("order id is required")

    return match.group()
```

测试函数：

```python
def test_normalize_tags() -> None:
    assert normalize_tags([" Python ", "AI", "python", "", " FastAPI "]) == [
        "python",
        "ai",
        "fastapi",
    ]
```

```python
def test_require_order_id_error() -> None:
    with pytest.raises(ValueError):
        require_order_id("用户没有提供订单号")
```

文件读写测试：

```python
def test_save_and_load_report(tmp_path: Path) -> None:
    report_file = tmp_path / "reports" / "report.json"
    report = {
        "user_name": "Panpan",
        "tags": ["python", "pytest"],
        "order_id": "ORD-20260705-001",
    }

    save_report(report_file, report)
    loaded_report = load_report(report_file)

    assert report_file.exists()
    assert loaded_report == report
```

运行：

```powershell
uv run pytest -q
```

## 23. 自测问题

1. 测试是什么？
2. pytest 是什么？
3. pytest 默认怎么发现测试文件和测试函数？
4. `assert` 的作用是什么？
5. 参数化测试解决什么问题？
6. `pytest.raises(ValueError)` 是干什么的？
7. `tmp_path` 是什么？
8. 为什么测试里不要直接修改真实项目文件？
9. 为什么正则规则适合写测试？
10. 测试失败意味着什么？

## 24. 自测参考答案

1. 测试是什么？

   测试是用代码验证代码是否符合预期。

2. pytest 是什么？

   pytest 是 Python 常用测试框架，用来自动发现和运行测试。

3. pytest 默认怎么发现测试文件和测试函数？

   常见规则是测试文件名以 `test_` 开头，测试函数名也以 `test_` 开头。

4. `assert` 的作用是什么？

   `assert` 用来断言条件必须成立，不成立时测试失败。

5. 参数化测试解决什么问题？

   它可以用同一个测试函数测试多组输入和预期结果，减少重复代码。

6. `pytest.raises(ValueError)` 是干什么的？

   它用来断言某段代码应该抛出 `ValueError`，如果没有抛出，测试失败。

7. `tmp_path` 是什么？

   `tmp_path` 是 pytest 提供的临时目录，适合测试文件读写。

8. 为什么测试里不要直接修改真实项目文件？

   因为可能污染项目数据，导致测试之间相互影响，也可能误删或改坏真实文件。

9. 为什么正则规则适合写测试？

   因为正则规则输入和输出很明确，改错后测试能很快发现。

10. 测试失败意味着什么？

    测试失败表示实际结果和预期不一致，需要检查代码或测试预期。失败本身是帮助定位问题的工具。

## 25. 推荐资料

- pytest 官方文档
  https://docs.pytest.org/

- pytest 官方文档：How to write and report assertions
  https://docs.pytest.org/en/stable/how-to/assert.html

- pytest 官方文档：Parametrize
  https://docs.pytest.org/en/stable/how-to/parametrize.html

- pytest 官方文档：tmp_path
  https://docs.pytest.org/en/stable/how-to/tmp_path.html
