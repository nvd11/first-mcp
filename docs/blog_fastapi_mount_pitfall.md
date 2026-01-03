# 踩坑记录：FastAPI 挂载 Starlette 子应用时的“根路径陷阱”

最近在重构一个 MCP Server 项目，想把 `FastMCP` (基于 Starlette) 挂载到 `FastAPI` 下面做鉴权中间件。本以为是常规操作，结果掉进了一个深坑，折腾了半天。记录一下，希望能帮到遇到同样报错的兄弟。

## 案发现场

架构很简单：
1.  外层：FastAPI (用于处理 Auth Middleware)。
2.  内层：FastMCP (本质是 Starlette App，处理 SSE)。
3.  目标：把 FastMCP 挂载到根路径 `/`，这样 URL 看起来干净。

代码大概长这样：

```python
app = FastAPI()

@app.middleware("http")
async def auth_middleware(request, call_next):
    # ... 鉴权逻辑 ...
    response = await call_next(request)
    return response

# 挂载到根路径
mcp_app = mcp.sse_app()
app.mount("/", mcp_app) 
```

一运行，中间件日志正常打印，但在 `await call_next(request)` 时直接崩了，抛出一个巨诡异的错误：

```
TypeError: 'Response' object is not iterable
```
或者在某些版本下表现为 request 挂起。

## 原因分析

这个问题涉及到 ASGI 规范和 Starlette 的 `Mount` 实现机制。

当我们把一个子应用挂载到根路径 `/` 时，Starlette 的路由匹配机制会把**所有**请求都匹配给这个子应用（因为它是一个 catch-all）。

但在 FastAPI 中，Middleware 的执行顺序和路由匹配顺序在处理根路径挂载时容易产生微妙的冲突。特别是当子应用（FastMCP）自己也有一套请求生命周期处理时，外层的 Middleware 在处理 `call_next` 返回的 Response 对象时，可能会拿到一个意料之外的对象（比如已经关闭的流，或者是协程对象而非 Response），导致在外层尝试迭代它时报错。

简单来说：**在 FastAPI 中把另一个完整的 App 挂载到根路径 `/`，同时还挂着自定义 Middleware，是一个高风险操作。** 路由的“贪婪匹配”可能会吞噬掉本该由外层处理的逻辑，或者打乱 ASGI 的调用栈。

## 解决方案

最稳妥的办法就是：**不要挂载到根路径**。

给子应用分配一个专属的 namespace（前缀），比如 `/mcp`。这样路由匹配清晰明了，外层 Middleware 也能准确区分哪些请求是给子应用的，哪些是给外层的。

**修复后的代码**：

```python
# 1. 挂载到 /mcp
app.mount("/mcp", mcp_app)

# 2. 修改中间件判断逻辑
@app.middleware("http")
async def auth_middleware(request, call_next):
    if request.url.path.startswith("/mcp/sse"):
        # ... 鉴权 ...
    return await call_next(request)
```

**副作用**：
客户端连接地址需要改一下，从 `http://host/sse` 变成 `http://host/mcp/sse`。这点小改动换来的是系统的稳定，值。

## 总结

在 FastAPI/Starlette 开发中，尽量避免使用 `app.mount("/", sub_app)` 这种“霸道”的挂载方式，除非你是故意要接管所有路由且不使用复杂的外层中间件。

**Namespace is your friend.** 给子应用一个家，别让它在大街上流浪。
