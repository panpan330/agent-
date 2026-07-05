# Python async/await 异步基础

日期：2026-07-05

对应代码：

```text
projects/python-basics/lesson21_async_await.py
projects/python-basics/lesson21_practice_async_await.py
projects/python-basics/test_lesson21_practice_async_await.py
```

## 1. 为什么要学 async/await

后面进入 FastAPI、AI API、数据库、向量库、Java API 调用时，经常会看到：

```python
async def chat():
    ...
```

以及：

```python
await model.ainvoke(...)
```

如果不理解异步，看到这些代码会很容易混。

可以先记住：

```text
async/await 主要用来处理等待时间，比如网络请求、数据库查询、文件或模型调用。
```

## 2. 同步代码是什么

同步代码就是一行一行执行。

上一行没执行完，下一行不能开始。

```python
user = fetch_user()
orders = fetch_orders()
```

如果 `fetch_user()` 要等 1 秒，`fetch_orders()` 也要等 1 秒，总耗时大约 2 秒。

## 3. 异步代码是什么

异步代码允许程序在等待时先去做别的等待任务。

比如：

```python
user_task = fetch_user()
orders_task = fetch_orders()
```

两个任务都在等网络时，可以一起等待。

如果两个任务各等 1 秒，并发等待总耗时可能接近 1 秒，而不是 2 秒。

注意：

```text
异步不是让 CPU 算得更快，而是让等待更有效率。
```

## 4. async def 是什么

普通函数：

```python
def hello() -> str:
    return "hello"
```

异步函数：

```python
async def hello() -> str:
    return "hello"
```

`async def` 定义的是协程函数。

调用它时，不会立刻得到结果，而是得到一个 coroutine 对象。

## 5. await 是什么

`await` 用来等待异步函数的结果。

```python
async def fetch_user() -> dict:
    await asyncio.sleep(1)
    return {"name": "Panpan"}
```

调用：

```python
user = await fetch_user()
```

含义：

```text
等待 fetch_user() 完成，然后把结果赋值给 user。
```

## 6. asyncio.sleep()

同步等待：

```python
time.sleep(1)
```

异步等待：

```python
await asyncio.sleep(1)
```

`asyncio.sleep()` 常用来模拟网络请求等待。

真实项目里，等待的可能是：

- HTTP 请求。
- 数据库查询。
- Redis 查询。
- 向量库检索。
- AI 模型返回结果。

## 7. asyncio.run()

普通 Python 脚本不能在最外层直接写：

```python
await fetch_user()
```

需要用：

```python
asyncio.run(main_async())
```

示例：

```python
async def main_async() -> None:
    user = await fetch_user()
    print(user)


def main() -> None:
    asyncio.run(main_async())
```

## 8. 顺序 await

```python
user = await fetch_user()
permissions = await fetch_permissions()
orders = await fetch_orders()
```

这是顺序等待。

第一个等完，才开始第二个。

如果每个都要 0.3 秒，总耗时大约 0.9 秒。

## 9. asyncio.gather()

`asyncio.gather()` 可以同时等待多个协程。

```python
user, permissions, orders = await asyncio.gather(
    fetch_user(),
    fetch_permissions(),
    fetch_orders(),
)
```

如果每个都要 0.3 秒，总耗时可能接近 0.3 秒。

这很适合并发查询多个互不依赖的数据。

## 10. 什么时候可以并发

可以并发的前提是任务之间没有依赖关系。

例如：

- 查用户信息。
- 查用户权限。
- 查最近订单。

这三件事如果互不依赖，就可以并发。

如果第二步必须依赖第一步结果，就不能直接并发。

## 11. batch 批量处理

多个用户问题可以并发分类：

```python
tasks = [classify_question_async(question) for question in questions]
results = await asyncio.gather(*tasks)
```

这里的 `*tasks` 是第 15 节学过的解包调用。

## 12. create_task()

`asyncio.create_task()` 可以先创建任务，让它交给事件循环调度。

```python
task = asyncio.create_task(fetch_user())

# 这里可以做别的事情

user = await task
```

初学阶段先重点掌握 `await` 和 `gather()`。

`create_task()` 后面遇到后台任务、并发调度时再深入。

## 13. wait_for() 超时控制

异步任务也要考虑超时。

```python
try:
    result = await asyncio.wait_for(fetch_user(), timeout=1)
except TimeoutError:
    result = {"ok": False, "reason": "timeout"}
```

后面调用模型、Java API、向量库时，都要考虑超时。

## 14. 异步和 HTTP

上一节我们用的是 `requests`。

`requests` 是同步 HTTP 客户端。

后面 FastAPI 项目更常见的是：

- `httpx`：支持同步和异步 HTTP 请求。
- AI SDK 的异步调用。
- 数据库异步客户端。

现在先学 `asyncio`，后面再把它和 `httpx`、FastAPI 接起来。

## 15. FastAPI 里的 async def

FastAPI 可以写：

```python
@app.get("/health")
def health():
    return {"status": "ok"}
```

也可以写：

```python
@app.get("/chat")
async def chat():
    result = await call_model()
    return result
```

如果接口内部要等待网络、数据库、模型调用，常见写法是 `async def`。

## 16. 异步不是多线程

先不要把异步和多线程混在一起。

本节先记住：

```text
异步适合大量等待型任务。
多线程/多进程更偏向并行执行阻塞代码或 CPU 任务。
```

后面如果需要，我们再单独讲线程和进程。

## 17. 常见错误

### 错误 1：忘记 await

错误：

```python
user = fetch_user()
```

这时 `user` 不是结果，而是 coroutine 对象。

正确：

```python
user = await fetch_user()
```

### 错误 2：在普通函数里直接 await

错误：

```python
def main():
    user = await fetch_user()
```

`await` 只能在 `async def` 里面使用。

### 错误 3：能并发却写成顺序 await

```python
user = await fetch_user()
permissions = await fetch_permissions()
orders = await fetch_orders()
```

如果三者互不依赖，可以改成：

```python
user, permissions, orders = await asyncio.gather(...)
```

### 错误 4：用 time.sleep() 阻塞异步函数

异步函数里不要写：

```python
time.sleep(1)
```

应该写：

```python
await asyncio.sleep(1)
```

## 18. 本节练习

创建文件：

```text
projects/python-basics/lesson21_practice_async_await.py
projects/python-basics/test_lesson21_practice_async_await.py
```

要求：

1. 写 `fake_get_json(name, delay)`
   - 用 `await asyncio.sleep(delay)` 模拟网络等待。
   - 返回一个字典。
2. 写 `fetch_user_profile(user_id)`
   - 调用 `fake_get_json()`。
   - 返回用户资料。
3. 写 `fetch_user_permissions(user_id)`
   - 返回权限集合。
4. 写 `fetch_user_orders(user_id)`
   - 返回订单列表。
5. 写 `build_user_context(user_id)`
   - 用 `asyncio.gather()` 并发获取资料、权限、订单。
6. 写 `batch_classify_questions(questions)`
   - 并发分类多个问题。
7. 写 `run_with_timeout(awaitable, timeout)`
   - 成功返回 `ok=True`。
   - 超时返回 `ok=False` 和原因。
8. 写 pytest 测试，用 `asyncio.run()` 运行异步函数。

## 19. 练习参考答案

```python
async def fake_get_json(name: str, delay: float = 0.1) -> dict[str, object]:
    await asyncio.sleep(delay)
    return {
        "name": name,
        "ok": True,
    }
```

```python
async def build_user_context(user_id: int) -> dict[str, object]:
    profile, permissions, orders = await asyncio.gather(
        fetch_user_profile(user_id),
        fetch_user_permissions(user_id),
        fetch_user_orders(user_id),
    )

    return {
        "profile": profile,
        "permissions": sorted(permissions),
        "orders": orders,
    }
```

```python
async def run_with_timeout(awaitable: Awaitable[Any], timeout: float) -> dict[str, object]:
    try:
        result = await asyncio.wait_for(awaitable, timeout=timeout)
    except TimeoutError:
        return {
            "ok": False,
            "reason": "timeout",
        }

    return {
        "ok": True,
        "result": result,
    }
```

测试示例：

```python
def test_fake_get_json() -> None:
    result = asyncio.run(fake_get_json("test", delay=0))

    assert result == {
        "name": "test",
        "ok": True,
    }
```

运行：

```powershell
uv run pytest test_lesson21_practice_async_await.py -q
```

## 20. 自测问题

1. `async def` 定义的是什么？
2. `await` 是干什么的？
3. 为什么普通脚本里常用 `asyncio.run()`？
4. `asyncio.sleep()` 和 `time.sleep()` 有什么区别？
5. 顺序 `await` 和 `asyncio.gather()` 有什么区别？
6. 什么样的任务适合并发等待？
7. `asyncio.wait_for()` 用来做什么？
8. 忘记 `await` 会发生什么？
9. 为什么异步不等于 CPU 算得更快？
10. FastAPI 里为什么会看到 `async def`？

## 21. 自测参考答案

1. `async def` 定义的是什么？

   `async def` 定义的是异步函数，也叫协程函数。

2. `await` 是干什么的？

   `await` 用来等待一个异步任务完成，并拿到它的结果。

3. 为什么普通脚本里常用 `asyncio.run()`？

   因为普通脚本最外层不能直接写 `await`，需要用 `asyncio.run()` 启动事件循环并运行主协程。

4. `asyncio.sleep()` 和 `time.sleep()` 有什么区别？

   `asyncio.sleep()` 是异步等待，不会阻塞事件循环；`time.sleep()` 是同步阻塞等待。

5. 顺序 `await` 和 `asyncio.gather()` 有什么区别？

   顺序 `await` 是一个等完再等下一个；`gather()` 可以同时等待多个互不依赖的协程。

6. 什么样的任务适合并发等待？

   互不依赖、主要时间花在等待上的任务，比如多个 HTTP 请求、数据库查询、模型调用。

7. `asyncio.wait_for()` 用来做什么？

   它用来给异步任务设置超时时间。

8. 忘记 `await` 会发生什么？

   你拿到的不是最终结果，而是 coroutine 对象，函数体也不会按你预期执行。

9. 为什么异步不等于 CPU 算得更快？

   因为异步主要优化等待时间，不是让 CPU 同时执行更多计算。

10. FastAPI 里为什么会看到 `async def`？

    因为接口内部常常要等待模型、数据库、HTTP 请求等 IO 操作，用 `async def` 可以更高效地处理等待。

## 22. 推荐资料

- Python 官方文档：asyncio
  https://docs.python.org/3/library/asyncio.html

- Python 官方文档：Coroutines and Tasks
  https://docs.python.org/3/library/asyncio-task.html

- FastAPI 官方文档：Async
  https://fastapi.tiangolo.com/async/
