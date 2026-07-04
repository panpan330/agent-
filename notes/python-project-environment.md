# Python 项目环境基础

日期：2026-07-04

## 1. 这一层要解决什么问题

Python 项目开发前，先要搞清楚：

- Python 解释器负责运行代码。
- 每个项目应该有自己的虚拟环境 `.venv`。
- 依赖包是别人写好的库，比如 `requests`、`fastapi`、`langchain`。
- `uv` 负责创建环境、安装依赖、运行命令。
- `pyproject.toml` 记录项目配置和直接依赖。
- `uv.lock` 锁定完整依赖版本，保证环境可复现。

## 2. 和 Java 的类比

```text
Python 解释器 ≈ JDK/JRE
pyproject.toml ≈ pom.xml / build.gradle
uv.lock ≈ Maven/Gradle 解析后的依赖锁定结果
.venv ≈ 当前项目自己的依赖运行环境
uv ≈ Maven/Gradle + 虚拟环境管理工具
```

## 3. 本次练习项目

位置：

```text
projects/python-basics
```

创建命令：

```powershell
uv init projects\python-basics --name python-basics --no-package
```

运行命令：

```powershell
uv run python main.py
```

第一次运行时，uv 自动创建：

```text
.venv
uv.lock
```

## 4. 关键文件

### `.python-version`

指定项目期望使用的 Python 大版本：

```text
3.12
```

### `pyproject.toml`

项目配置和直接依赖。

安装 `requests` 后：

```toml
dependencies = [
    "requests>=2.34.2",
]
```

### `uv.lock`

锁定完整依赖树。

比如安装 `requests` 后，实际还会安装：

```text
certifi
charset-normalizer
idna
urllib3
```

这些是 `requests` 自己依赖的包。

### `.venv`

当前项目自己的虚拟环境。

以后这个项目安装的依赖都会进入 `.venv`，不会污染全局 Python。

## 5. 常用 uv 命令

```powershell
uv init 项目名
uv run python main.py
uv add requests
uv pip list
uv sync
```

含义：

- `uv init`：创建项目。
- `uv run`：在项目环境里运行命令。
- `uv add`：安装依赖，并写入 `pyproject.toml` 和 `uv.lock`。
- `uv pip list`：查看当前项目虚拟环境里的包。
- `uv sync`：根据 `pyproject.toml` 和 `uv.lock` 同步环境。

## 6. 本次代码

`projects/python-basics/request_demo.py`：

```python
import requests


def main() -> None:
    response = requests.get("https://httpbin.org/get", timeout=10)
    print("status:", response.status_code)
    print("content-type:", response.headers.get("content-type"))

    data = response.json()
    print("url:", data["url"])
    print("origin:", data["origin"])


if __name__ == "__main__":
    main()
```

运行：

```powershell
uv run python request_demo.py
```

输出中看到 `status: 200`，说明请求成功。

## 7. 现在应该掌握

完成这一层后，至少要能回答：

- 为什么 Python 项目需要虚拟环境？
- `uv run` 和直接 `python` 有什么区别？
- `uv add requests` 做了哪些事情？
- `pyproject.toml` 和 `uv.lock` 分别记录什么？
- 为什么依赖包不应该随便装到全局 Python？

## 8. 下一步

下一层学习 Python 基础语法：

- 变量
- 字符串
- 列表
- 字典
- 条件判断
- 循环
- 函数
- 异常处理
- 文件读写
- 类型提示
