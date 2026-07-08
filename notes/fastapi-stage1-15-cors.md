# 阶段 1 第 15 节：CORS 基础

## 1. 这一节学什么

这一节学习 CORS。

先记住一句话：

```text
CORS 是浏览器用来判断“一个网页能不能访问另一个来源接口”的规则。
```

你以后做前后端分离项目时，经常会遇到这种情况：

```text
前端页面运行在 http://localhost:5173
后端接口运行在 http://127.0.0.1:8000
```

前端代码请求后端：

```text
fetch("http://127.0.0.1:8000/chat")
```

结果浏览器报错：

```text
CORS policy blocked ...
```

但你用 Postman、curl、Python requests 访问同一个接口，又能访问。

这不是后端接口一定坏了。

这通常是浏览器的同源策略和 CORS 配置问题。

本节目标：

```text
理解 origin 是什么
理解什么叫跨域
理解为什么浏览器会拦
理解 CORS 是什么
用 FastAPI 配置 CORSMiddleware
用 .env 配置允许的前端地址
用测试验证 CORS 响应头
```

## 2. 什么是 origin

`origin` 可以理解成：

```text
网页或请求来自哪里。
```

一个 origin 由三部分组成：

```text
协议 scheme
域名 host
端口 port
```

例如：

```text
http://localhost:5173
```

拆开看：

```text
协议：http
域名：localhost
端口：5173
```

再比如：

```text
http://127.0.0.1:8000
```

拆开看：

```text
协议：http
域名：127.0.0.1
端口：8000
```

## 3. 什么是同源

两个地址的：

```text
协议相同
域名相同
端口相同
```

才叫同源。

例如：

```text
http://localhost:5173/page
http://localhost:5173/api
```

这两个同源。

因为：

```text
协议都是 http
域名都是 localhost
端口都是 5173
```

## 4. 什么是不同源

只要协议、域名、端口有一个不同，就不是同源。

例如：

```text
http://localhost:5173
http://localhost:8000
```

不同源。

因为端口不同：

```text
5173 != 8000
```

再比如：

```text
http://localhost:5173
https://localhost:5173
```

不同源。

因为协议不同：

```text
http != https
```

再比如：

```text
http://localhost:5173
http://127.0.0.1:5173
```

不同源。

虽然它们在本机可能指向同一个地方，但浏览器看的是字符串里的 host：

```text
localhost != 127.0.0.1
```

## 5. 什么是跨域

跨域就是：

```text
一个 origin 的网页，去请求另一个 origin 的资源。
```

前端开发常见场景：

```text
前端：http://localhost:5173
后端：http://127.0.0.1:8000
```

前端访问后端，就是跨域。

因为端口和 host 都不一样。

## 6. 什么是浏览器同源策略

浏览器同源策略是浏览器的安全规则。

它大致意思是：

```text
默认情况下，一个网页不能随便读取另一个来源的响应内容。
```

它保护用户安全。

如果没有这个规则，恶意网站可能偷偷请求你已经登录的网站，并读取你的数据。

例如你登录了银行网站，又打开一个恶意网页。

恶意网页如果能随便读银行接口响应，就很危险。

所以浏览器必须限制跨源访问。

## 7. 为什么 Postman 可以，浏览器不行

这是初学者非常容易疑惑的点。

你可能会遇到：

```text
Postman 请求成功
curl 请求成功
Python requests 请求成功
浏览器 fetch 请求失败
```

原因是：

```text
CORS 是浏览器执行的安全策略。
```

Postman、curl、Python requests 不是浏览器页面。

它们不会按浏览器同源策略拦截响应。

所以：

```text
接口能访问
不代表浏览器页面一定能访问
```

浏览器页面能不能跨源读取响应，要看服务端有没有返回正确的 CORS 响应头。

## 8. 什么是 CORS

CORS 全称：

```text
Cross-Origin Resource Sharing
```

中文常说：

```text
跨源资源共享
```

简单理解：

```text
CORS 是服务端告诉浏览器：哪些来源可以访问我。
```

后端通过响应头告诉浏览器。

最常见响应头：

```text
Access-Control-Allow-Origin
```

例如：

```text
Access-Control-Allow-Origin: http://localhost:5173
```

意思是：

```text
允许 http://localhost:5173 这个前端页面读取我的响应。
```

## 9. Origin 请求头

浏览器跨源请求时，会带一个请求头：

```text
Origin: http://localhost:5173
```

它告诉后端：

```text
这次请求来自 http://localhost:5173。
```

后端看这个 Origin 是否在允许列表里。

如果允许，就返回：

```text
Access-Control-Allow-Origin: http://localhost:5173
```

浏览器看到允许，才把响应交给前端 JavaScript。

## 10. 为什么后端不能随便允许所有来源

你可能会看到一种配置：

```python
allow_origins=["*"]
```

意思是：

```text
允许所有来源。
```

学习 Demo 可以临时用。

但真实项目不能随便这样配。

原因是：

```text
你的接口可能有用户数据
你的接口以后可能带登录态
你的接口可能被任意网站调用
安全边界会变弱
```

所以本项目从一开始就用明确白名单：

```text
http://localhost:5173
http://127.0.0.1:5173
```

## 11. 什么是预检请求

有些跨域请求，浏览器不会直接发真正请求。

它会先发一个：

```text
OPTIONS
```

请求。

这个请求叫：

```text
preflight request
预检请求
```

意思是：

```text
浏览器先问后端：我能不能这样请求你？
```

例如前端想发：

```text
POST /chat
Content-Type: application/json
```

浏览器可能先发：

```text
OPTIONS /chat
Origin: http://localhost:5173
Access-Control-Request-Method: POST
Access-Control-Request-Headers: Content-Type
```

后端如果允许，就返回 CORS 相关响应头。

然后浏览器才发真正的 POST 请求。

## 12. 本节新增和修改的文件

新增：

```text
app/core/cors.py
tests/test_cors.py
notes/fastapi-stage1-15-cors.md
```

修改：

```text
app/core/config.py
app/main.py
.env.example
tests/test_config.py
README.md
docs/learning-progress.md
docs/learning-resources.md
projects/ai-service/README.md
```

## 13. .env.example 新增配置

文件：

```text
projects/ai-service/.env.example
```

新增：

```env
CORS_ALLOWED_ORIGINS="http://localhost:5173,http://127.0.0.1:5173"
```

这表示当前允许两个前端来源：

```text
http://localhost:5173
http://127.0.0.1:5173
```

为什么默认是 5173？

因为很多前端开发工具，比如 Vite，默认开发端口是 5173。

后面如果你前端运行在 3000，就可以改成：

```env
CORS_ALLOWED_ORIGINS="http://localhost:3000"
```

如果多个地址，用逗号分隔：

```env
CORS_ALLOWED_ORIGINS="http://localhost:5173,http://localhost:3000"
```

## 14. Settings 新增 CORS 配置

文件：

```text
projects/ai-service/app/core/config.py
```

新增字段：

```python
cors_allowed_origins: str = Field(
    default="http://localhost:5173,http://127.0.0.1:5173"
)
```

这里先用字符串。

因为 `.env` 文件里写字符串最直观。

## 15. 为什么要解析成列表

FastAPI 的 `CORSMiddleware` 需要的是列表：

```python
allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"]
```

但 `.env` 里我们写的是字符串：

```env
CORS_ALLOWED_ORIGINS="http://localhost:5173,http://127.0.0.1:5173"
```

所以需要把字符串拆成列表。

## 16. cors_allowed_origin_list

代码：

```python
@property
def cors_allowed_origin_list(self) -> list[str]:
    return [
        origin.strip()
        for origin in self.cors_allowed_origins.split(",")
        if origin.strip()
    ]
```

这段代码做三件事：

```text
用逗号 split
去掉每个地址两边的空格
过滤空字符串
```

例如：

```text
" http://localhost:5173, , http://127.0.0.1:5173 "
```

会变成：

```python
[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
```

## 17. 新增 app/core/cors.py

文件：

```text
projects/ai-service/app/core/cors.py
```

代码：

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def register_cors_middleware(app: FastAPI, allowed_origins: list[str]) -> None:
    if not allowed_origins:
        return

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
```

这个函数负责给 FastAPI 应用注册 CORS middleware。

## 18. CORSMiddleware 是什么

`CORSMiddleware` 是 FastAPI/Starlette 提供的中间件。

它会帮你处理：

```text
Origin 请求头
Access-Control-Allow-Origin 响应头
OPTIONS 预检请求
允许的方法
允许的请求头
```

你不用自己手写这些响应头。

## 19. allow_origins

```python
allow_origins=allowed_origins
```

这里传入允许访问后端的前端来源列表。

例如：

```python
[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
```

如果请求头是：

```text
Origin: http://localhost:5173
```

后端会返回：

```text
Access-Control-Allow-Origin: http://localhost:5173
```

如果请求头是：

```text
Origin: https://evil.example
```

后端不会返回允许它的 CORS 头。

浏览器就会拦住前端读取响应。

## 20. allow_credentials

```python
allow_credentials=False
```

这里表示：

```text
当前不允许跨域请求携带 cookie、认证凭证等 credentials。
```

我们当前还没有登录态、cookie、鉴权。

所以先设置为 `False`。

后面如果要做登录、JWT、cookie，需要重新讲安全配置。

## 21. allow_methods

```python
allow_methods=["GET", "POST", "OPTIONS"]
```

表示允许跨域请求使用这些 HTTP 方法。

当前项目主要有：

```text
GET /health
POST /chat
OPTIONS 预检请求
```

所以先允许这三个。

## 22. allow_headers

```python
allow_headers=["*"]
```

表示允许浏览器请求携带常见自定义请求头。

例如：

```text
Content-Type
X-Trace-Id
Authorization
```

当前前端发 JSON 时常见请求头是：

```text
Content-Type: application/json
```

## 23. 为什么 allowed_origins 为空时直接 return

代码：

```python
if not allowed_origins:
    return
```

意思是：

```text
如果配置里没有允许任何来源，就不注册 CORS middleware。
```

这比默认允许所有来源更安全。

空配置应该表示：

```text
不开放浏览器跨源访问。
```

## 24. main.py 如何接入

文件：

```text
projects/ai-service/app/main.py
```

新增：

```python
from app.core.cors import register_cors_middleware
```

注册：

```python
register_cors_middleware(app, settings.cors_allowed_origin_list)
```

当前 `create_app()` 做的事情是：

```text
读取 .env 配置
配置 logging
创建 FastAPI app
注册异常处理
注册 trace middleware
注册 CORS middleware
注册 router
```

## 25. CORS 和 trace_id 的关系

CORS 和 trace_id 是两件不同的事。

`trace_id` 解决：

```text
怎么追踪一次请求的日志。
```

CORS 解决：

```text
浏览器页面能不能跨源读取接口响应。
```

但它们都会通过 middleware 参与请求处理。

这也是为什么后端项目里经常会有多个 middleware。

## 26. 本节新增测试

新增文件：

```text
projects/ai-service/tests/test_cors.py
```

测试覆盖：

```text
允许的 Origin 能拿到 CORS 响应头
不允许的 Origin 拿不到 CORS 响应头
允许的预检请求能通过
不允许的预检请求会被拒绝
```

## 27. 测试允许的 Origin

```python
def test_allowed_origin_gets_cors_header(client: TestClient) -> None:
    origin = "http://localhost:5173"

    response = client.get("/health", headers={"Origin": origin})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
```

这里模拟浏览器请求：

```text
Origin: http://localhost:5173
```

因为它在允许列表里，所以响应头应该有：

```text
access-control-allow-origin: http://localhost:5173
```

## 28. 测试不允许的 Origin

```python
def test_disallowed_origin_does_not_get_cors_header(client: TestClient) -> None:
    response = client.get(
        "/health",
        headers={"Origin": "https://evil.example"},
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
```

注意：

```text
后端响应状态码仍然可能是 200。
```

但没有：

```text
access-control-allow-origin
```

浏览器看到没有允许头，就会阻止前端 JS 读取响应。

这就是为什么你在服务端测试里看到 200，但浏览器仍然报 CORS 错误。

## 29. 测试预检请求

```python
response = client.options(
    "/chat",
    headers={
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type",
    },
)
```

这模拟浏览器的预检请求。

它在问后端：

```text
来自 http://localhost:5173 的页面，能不能用 POST 请求 /chat，并携带 Content-Type？
```

如果允许，响应应该包含：

```text
access-control-allow-origin
access-control-allow-methods
access-control-allow-headers
```

## 30. 测试不允许的预检请求

```python
response = client.options(
    "/chat",
    headers={
        "Origin": "https://evil.example",
        "Access-Control-Request-Method": "POST",
    },
)

assert response.status_code == 400
assert "access-control-allow-origin" not in response.headers
```

这个测试说明：

```text
不在白名单里的 Origin，预检请求不能通过。
```

## 31. CORS 不是后端权限系统

这一点非常重要。

CORS 是浏览器安全机制。

它不是后端权限系统。

不能认为：

```text
配置了 CORS，就等于接口安全了。
```

因为：

```text
curl 可以绕过浏览器 CORS
Postman 可以绕过浏览器 CORS
服务端程序也可以绕过浏览器 CORS
```

真正的接口权限要靠：

```text
登录认证
Token
权限校验
服务端鉴权
限流
审计日志
```

CORS 只是告诉浏览器：

```text
哪些网页来源可以读取响应。
```

## 32. 本节练习

### 练习 1

题目：

解释下面两个地址是不是同源：

```text
http://localhost:5173
http://localhost:8000
```

参考答案：

不是同源。

虽然协议和域名相同，但端口不同：

```text
5173 != 8000
```

所以它们是不同 origin。

### 练习 2

题目：

为什么 Postman 能访问接口，但浏览器前端可能访问失败？

参考答案：

因为 CORS 是浏览器执行的安全策略。

Postman 不是浏览器页面，不会按浏览器同源策略拦截响应。

浏览器前端能不能读取响应，要看后端是否返回正确的 CORS 响应头。

### 练习 3

题目：

下面响应头是什么意思？

```text
Access-Control-Allow-Origin: http://localhost:5173
```

参考答案：

它表示后端允许来源为 `http://localhost:5173` 的网页读取这次跨源响应。

### 练习 4

题目：

为什么本项目不直接配置：

```python
allow_origins=["*"]
```

参考答案：

因为 `*` 表示允许所有来源。

真实项目接口可能涉及用户数据、登录态、内部信息，不能随便允许任意网站跨源读取响应。

所以本项目使用明确的允许列表。

### 练习 5

题目：

什么是预检请求？

参考答案：

预检请求是浏览器在某些跨域请求前自动发送的 `OPTIONS` 请求。

它用来询问后端是否允许真正的请求方法和请求头。

### 练习 6

题目：

`CORS_ALLOWED_ORIGINS` 现在为什么写成逗号分隔字符串？

参考答案：

因为 `.env` 文件里写字符串最直观，适合当前学习阶段。

代码会把它按逗号拆分成列表，再传给 `CORSMiddleware` 的 `allow_origins`。

## 33. 本节自测

### 自测 1

题目：

origin 由哪三部分组成？

参考答案：

origin 由三部分组成：

```text
协议
域名
端口
```

### 自测 2

题目：

只要协议、域名、端口有一个不同，是否同源？

参考答案：

不是同源。

协议、域名、端口必须全部相同才是同源。

### 自测 3

题目：

CORS 的全称是什么？

参考答案：

CORS 的全称是：

```text
Cross-Origin Resource Sharing
```

中文常说跨源资源共享。

### 自测 4

题目：

浏览器跨源请求时常见会带哪个请求头表示来源？

参考答案：

会带：

```text
Origin
```

例如：

```text
Origin: http://localhost:5173
```

### 自测 5

题目：

后端用哪个响应头告诉浏览器允许某个来源？

参考答案：

使用：

```text
Access-Control-Allow-Origin
```

### 自测 6

题目：

本项目 CORS 配置入口文件是哪个？

参考答案：

入口文件是：

```text
app/core/cors.py
```

### 自测 7

题目：

本项目允许的前端来源从哪里读取？

参考答案：

从 `.env` 或环境变量里的：

```text
CORS_ALLOWED_ORIGINS
```

读取。

### 自测 8

题目：

预检请求使用什么 HTTP 方法？

参考答案：

预检请求使用：

```text
OPTIONS
```

### 自测 9

题目：

CORS 是不是后端权限系统？

参考答案：

不是。

CORS 是浏览器安全机制，只限制浏览器页面跨源读取响应。

后端真正的权限仍然要靠认证、鉴权、Token、权限校验等。

### 自测 10

题目：

为什么不允许的 Origin 请求 `/health` 可能仍然返回 200，但浏览器还是会拦？

参考答案：

因为服务端可以正常处理请求并返回 200。

但如果响应里没有 `Access-Control-Allow-Origin`，浏览器不会把响应内容交给前端 JavaScript。

所以浏览器会表现为 CORS 拦截。

## 34. 本节小结

这一节完成了 CORS 基础：

```text
理解 origin
理解同源和跨域
理解浏览器同源策略
理解为什么 Postman 可以但浏览器不行
理解 CORS 响应头
理解预检请求
新增 CORS_ALLOWED_ORIGINS 配置
新增 app/core/cors.py
接入 CORSMiddleware
测试允许和拒绝的 Origin
测试 OPTIONS 预检请求
```

当前项目已经具备前后端分离开发时的基础 CORS 配置。

下一节学习：

```text
阶段 1 项目整理
```

会把阶段 1 的 FastAPI 基础能力整体复盘，并检查项目结构、README、测试、运行方式和下一阶段衔接。

## 35. 参考资料

- [FastAPI 官方文档：CORS Middleware](https://fastapi.tiangolo.com/tutorial/cors/)
- [MDN：Cross-Origin Resource Sharing](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS)
- [MDN：Same-origin policy](https://developer.mozilla.org/en-US/docs/Web/Security/Same-origin_policy)
