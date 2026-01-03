import uvicorn
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse
from loguru import logger

# Import MCP server and context variable
from src.servers.mcp_github_tool_server import mcp, user_token_ctx

# ==============================================================================
# Security & Server Setup
# ==============================================================================

# 创建 FastAPI 主应用
app = FastAPI()

# 添加中间件来处理 Header (Token透传)
@app.middleware("http")
async def context_middleware(request: Request, call_next):
    # 仅对 MCP 的 SSE 和 Messages 接口进行处理
    # 注意：由于我们挂载到了 /mcp，所以路径前缀变了
    if request.url.path.startswith("/mcp/sse") or request.url.path.startswith("/mcp/messages"):
        # 提取 GitHub Token (使用 X-Github-Token Header)
        # 这是一个自定义 Header，专门用于透传 GitHub Token 给 Tool 使用
        github_token = request.headers.get("X-Github-Token")
        
        if github_token:
            # 如果客户端传了 GitHub Token，存入 ContextVar
            # 注意：这里我们不做任何鉴权，直接信任并透传
            user_token_ctx.set(github_token)
            logger.info(f"Received X-Github-Token from {request.client.host}")
        else:
            # 如果没传，Tool 会回退到环境变量
            pass
            
    response = await call_next(request)
    return response

# 将 FastMCP 的 SSE 应用挂载到 /mcp 路径
# 避免挂载到根路径导致与 FastAPI 中间件冲突
mcp_app = mcp.sse_app()
app.mount("/mcp", mcp_app)

if __name__ == "__main__":
    # 使用 uvicorn 运行 FastAPI 应用，而不是直接运行 mcp
    logger.info(f"Starting MCP server on port 13333. Token passthrough enabled.")
    # Bind to 0.0.0.0 to allow external access (e.g. from Docker or other machines)
    uvicorn.run(app, host="0.0.0.0", port=13333)
