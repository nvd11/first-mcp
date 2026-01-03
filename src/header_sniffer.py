import asyncio
from aiohttp import web

async def handle_all(request):
    print(f"\n[Request Received] {request.method} {request.path}")
    print("--- Headers ---")
    for name, value in request.headers.items():
        print(f"{name}: {value}")
    print("---------------")
    
    # 返回一个虚假的 SSE 响应，防止客户端报错断开
    if request.path.endswith('/sse'):
        resp = web.StreamResponse(headers={
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
        })
        await resp.prepare(request)
        await resp.write(b"event: endpoint\ndata: /messages?session_id=fake_session\n\n")
        # 保持连接一会儿
        await asyncio.sleep(5)
        return resp
        
    return web.Response(text="OK")

if __name__ == "__main__":
    app = web.Application()
    # 捕获所有路径
    app.router.add_route('*', '/{tail:.*}', handle_all)
    
    # 使用 13334 端口，避免冲突
    PORT = 13334
    print(f"Starting Header Sniffer on port {PORT}...")
    print(f"Please configure Cline to connect to: http://127.0.0.1:{PORT}/sse")
    web.run_app(app, port=PORT)
