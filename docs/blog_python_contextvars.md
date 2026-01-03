# Python ContextVars 详解：并发编程的隐形传参神器

在 Python 的异步编程中，我们经常遇到一个棘手的问题：**如何在调用链深处获取请求上下文（比如 User ID、Request ID），而不用层层传参？**

全局变量？不行，并发环境下会数据打架。
`threading.local`？不行，`asyncio` 是单线程并发，线程级隔离没用。

这时候，Python 3.7 引入的 `contextvars` 模块就是那个救世主。

---

## 1. 什么是 ContextVar？

想象一下，你有一个全局字典，但是**每个协程 (Coroutine) 看到的都是自己独立的版本**。你在协程 A 里改了数据，协程 B 完全无感。

这就是 `ContextVar`。它提供了 **Task-Local Storage**（任务级局部存储），专门为 `asyncio` 设计。

---

## 2. 基础用法：像全局变量一样声明，像局部变量一样使用

```python
import asyncio
from contextvars import ContextVar

# 1. 声明：通常放在模块顶层，作为"全局"对象
request_id: ContextVar[str] = ContextVar("request_id", default="unknown")

async def process_data():
    # 3. 读取：在任何地方都能读到当前上下文的值
    # 根本不需要通过函数参数传进来！
    rid = request_id.get()
    print(f"Processing data for Request ID: {rid}")

async def handle_request(req_id: str):
    # 2. 设置：为当前协程上下文设置值
    token = request_id.set(req_id)
    try:
        await process_data()
    finally:
        # (可选) 恢复旧值，虽然在 Task 结束时会自动清理
        request_id.reset(token)

async def main():
    # 同时并发处理两个请求，看看会不会乱？
    await asyncio.gather(
        handle_request("REQ-001"),
        handle_request("REQ-002")
    )

if __name__ == "__main__":
    asyncio.run(main())
```

**输出结果：**
```text
Processing data for Request ID: REQ-001
Processing data for Request ID: REQ-002
```
看到没？虽然 `process_data` 没有参数，但它神奇地知道自己属于哪个请求。如果是普通全局变量，这里早就乱成一锅粥了。

---

## 3. 进阶场景：Middleware 与 依赖注入

在 Web 框架（如 FastAPI/Starlette）中，`ContextVar` 是实现 Middleware 传参给业务逻辑的核心技术。

### 场景：记录每个请求的 User Agent

```python
from fastapi import FastAPI, Request
from contextvars import ContextVar

# 定义上下文变量
user_agent_ctx = ContextVar("user_agent", default="unknown")

app = FastAPI()

# Middleware：拦截请求，提取信息
@app.middleware("http")
async def extract_ua_middleware(request: Request, call_next):
    ua = request.headers.get("User-Agent", "unknown")
    # 设置到 ContextVar
    token = user_agent_ctx.set(ua)
    
    response = await call_next(request)
    
    # 清理（虽然 Starlette 会为每个 Request 创建新 Context，但显式 reset 是好习惯）
    user_agent_ctx.reset(token)
    return response

# Service 层：深层逻辑，完全不依赖 Request 对象
def get_user_device_info():
    # 直接获取！不需要把 Request 对象传进来
    ua = user_agent_ctx.get()
    return f"User is using: {ua}"

@app.get("/")
async def root():
    return {"device": get_user_device_info()}
```

**这种模式的巨大优势**：
你的 Service 层代码不需要引入 `fastapi.Request`，也不需要层层透传 `request` 对象。代码变得极其干净、解耦。

---

## 4. 常见坑点 (必读)

### 坑 1：在线程池中使用 (`run_in_executor`)
如果你在异步函数里调用了同步阻塞代码（比如用 `loop.run_in_executor`），`ContextVar` **默认不会自动传递过去**。

```python
import asyncio
from contextvars import ContextVar, copy_context

my_var = ContextVar("my_var")

def sync_worker():
    # 这里会报错 LookupError，因为在新线程里上下文是空的
    return my_var.get() 

async def main():
    my_var.set("hello")
    loop = asyncio.get_running_loop()
    
    # ❌ 错误写法：直接调用
    # await loop.run_in_executor(None, sync_worker)
    
    # ✅ 正确写法：手动拷贝上下文
    ctx = copy_context()
    await loop.run_in_executor(None, ctx.run, sync_worker)
```

### 坑 2：以为它是全局修改
记住，`set()` 只影响**当前 Task 及其子 Task**。如果你在父 Task 设置了值，子 Task 能读到。但如果子 Task 修改了值，父 Task 是看不到变化的（类似于函数作用域）。

```python
var = ContextVar("var")

async def sub_task():
    var.set("child")
    print(f"Child: {var.get()}")  # Child: child

async def main():
    var.set("parent")
    await asyncio.create_task(sub_task())
    print(f"Parent: {var.get()}") # Parent: parent (未被子任务修改！)
```

---

## 5. 总结

`ContextVar` 是 Python 并发编程中被严重低估的神器。

*   **何时用**：当你需要在调用链中隐式传递 Request ID、Auth Token、Session 等“环境信息”时。
*   **好处**：代码解耦，无需层层传参，并发安全。
*   **记住**：它是基于 Task 隔离的，不是基于 Thread 的。

下次别再傻傻地把 `request` 对象传遍整个项目了，试试 `ContextVar` 吧。

---

## 6. 他山之石：Java 中的对应概念

如果你是从 Java 转过来的开发者，可能会觉得 `ContextVar` 很眼熟。

### 1. ThreadLocal (传统霸主)
在传统的 Java 多线程模型中，`ThreadLocal` 是实现隐式传参的标准方式。
*   **原理**：基于线程 ID 隔离。
*   **痛点**：在 Python `asyncio` 或 Java 虚拟线程这种“单线程/少线程并发”的模型下失效。而且如果不手动 `remove()`，极易造成内存泄漏（Memory Leak）。

### 2. ScopedValue (Java 21+ 新星)
随着 Java 21 引入虚拟线程 (Virtual Threads)，Java 也推出了 `ScopedValue`。它几乎就是 `ContextVar` 的亲兄弟。

```java
// Java 21+ 示例
public final static ScopedValue<String> REQUEST_ID = ScopedValue.newInstance();

// 类似 Python 的 contextvars.run()
ScopedValue.where(REQUEST_ID, "req-123").run(() -> {
    // 在这个作用域内，REQUEST_ID 可见
    // 类似于 Python 的 .get()
    System.out.println(REQUEST_ID.get());
});
```

**对比总结**：
*   **ThreadLocal**：适用于传统的“一请求一线程”模型（如老版 Spring Boot）。
*   **ContextVar / ScopedValue**：适用于现代的“异步/协程/虚拟线程”模型，更轻量，更安全。
