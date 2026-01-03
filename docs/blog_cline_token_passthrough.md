# 搞定 Cline 远程 MCP 鉴权：我的踩坑与最佳实践

大家好。最近在折腾 MCP Server，遇到个特别抓狂的问题。

本地开发一切顺利，GitHub Token 塞进 `.env` 环境变量里就完事了，Cline (VS Code 插件) 跑得飞起。但当我把 Server 部署到服务器上，想让团队里每个人用 **自己的 GitHub Token** 去跑任务时，傻眼了...

Cline 的配置里好像没地方填“动态参数”？难道要每个人都去改 Server 的环境变量？这也太不安全了。

折腾了一晚上，终于摸索出了一套 **基于 HTTP Header 和 ContextVars 的透传方案**。亲测有效，这就把方案分享给大家，少走弯路。

---

## 痛点：如何把 Token 传过去？

我们面临的死局是：
1.  **MCP 协议**：主要是 JSON-RPC，标准里好像没规定怎么传鉴权 Token。
2.  **Cline 客户端**：配置项少得可怜，只有 `command` (本地) 和 `url` (远程)。

但我转念一想，MCP 的 SSE 模式本质上就是 HTTP 长连接。既然是 HTTP，**Header 总能用吧？**

### 验证时刻：Cline 真的发 Header 吗？

虽然 Cline 文档里没明说支持自定义 Header，但我决定赌一把。我写了个简单的“抓包脚本”来验证。

**Header Sniffer 脚本 (`src/header_sniffer.py`)**：

```python
from aiohttp import web

async def handle_all(request):
    print("\n[Request Received]")
    print("--- Headers ---")
    for name, value in request.headers.items():
        print(f"{name}: {value}")
    print("---------------")
    # 返回一个假的 SSE 响应防止客户端报错
    return web.Response(text="OK")

if __name__ == "__main__":
    app = web.Application()
    app.router.add_route('*', '/{tail:.*}', handle_all)
    print("Sniffer running on port 13334...")
    web.run_app(app, port=13334)
```

**验证过程**：
1.  启动这个脚本：`python src/header_sniffer.py`
2.  在 Cline 的配置里填入：
    ```json
    "url": "http://127.0.0.1:13334/sse",
    "headers": {
      "X-Github-Token": "test-token-123"
    }
    ```
3.  点击连接。

**结果**：终端里清晰地跳出了：
`X-Github-Token: test-token-123`

**当时我就激动了！** Cline 的底层实现是完整的，它默默支持着 Header 发送。这就好办了，路通了。

---

## Server 端接招：从 FastMCP 到 FastAPI

路通了，但 Server 端怎么收呢？

我用的是 `fastmcp` 库，它封装得太好了，以至于我找不到地方插 Middleware 去拦截 Header。翻了半天源码，发现 `FastMCP` 类其实是一个独立的 Server，不开放底层接口。

**破局思路**：既然改不了它，就**包装**它。

`FastMCP` 虽然高冷，但它提供了一个 `sse_app()` 方法，返回的是一个标准的 ASGI 应用。这就意味着，我可以用 **FastAPI** 做外壳，负责处理 HTTP Header 和鉴权，然后把“脏活累活”甩给 FastMCP 去干。

### 核心代码实现

直接上干货。我们需要用到 Python 的 `contextvars`，这玩意儿是处理并发请求的神器，比 ThreadLocal 更好用。

```python
from contextvars import ContextVar
from fastapi import FastAPI, Request
from fastmcp import FastMCP
import uvicorn

# 1. 定义一个“隐形口袋” (ContextVar)
# 用来在请求处理过程中临时存放 Token，请求结束自动销毁，并发安全。
user_token_ctx = ContextVar("user_token", default=None)

# 2. 定义 FastAPI 外壳
app = FastAPI()

# 3. 编写中间件：拦截 Token 并装进口袋
@app.middleware("http")
async def token_passthrough_middleware(request: Request, call_next):
    # 只拦截 MCP 相关的 SSE 请求
    if request.url.path.startswith("/sse") or request.url.path.startswith("/messages"):
        # 拿到用户传来的 Token
        token = request.headers.get("X-Github-Token")
        if token:
            user_token_ctx.set(token)
            print(f"收到来自 {request.client.host} 的 Token，已暂存。")
            
    response = await call_next(request)
    return response

# 4. FastMCP 核心逻辑
mcp = FastMCP("MyServer")

@mcp.tool()
async def list_repos():
    # 5. 在工具里从口袋掏出 Token
    token = user_token_ctx.get()
    
    if token:
        print("Using Client-Provided Token!")
        # 这里就可以用用户的 Token 去调 GitHub API 了
        client = GitHubClient(token=token)
    else:
        print("Fallback to Server Token...")
        client = GitHubClient(token=os.getenv("GITHUB_TOKEN"))
        
    return client.get_repos()

# 6. 关键一步：把 FastMCP 挂载上去
mcp_app = mcp.sse_app()
app.mount("/", mcp_app)

if __name__ == "__main__":
    # 启动的是 FastAPI，而不是 mcp.run()
    uvicorn.run(app, host="0.0.0.0", port=13333)
```

---

## 客户端配置 (Cline)

Server 端改好后，Cline 这边的配置就非常简单直观了：

```json
{
  "mcpServers": {
    "my-remote-server": {
      "url": "http://192.168.1.100:13333/sse",
      "transport": "sse",
      "headers": {
        "X-Github-Token": "ghp_这就是每个用户自己的Token"
      },
      "autoApprove": []
    }
  }
}
```

---

## 总结一下

这个方案最爽的地方在于**无感**和**隔离**。

1.  **隔离性**：利用 `ContextVar`，即使用户 A 和用户 B 同时发请求，他们的 Token 也绝不会串台。
2.  **兼容性**：代码里我做了回退处理，本地开发没 Header 时依然可以用 `.env` 里的 Token，不影响调试。
3.  **安全性**：Server 变成了无状态的管道，不存用户数据，大大降低了运维风险。

希望这个踩坑记录能帮到正在折腾 MCP 的你。如果有更好的方案，欢迎交流！
