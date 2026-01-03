# 实战指南：如何使用 curl 命令行测试 FastMCP (SSE 模式)

在开发 FastMCP Server 时，我们经常需要快速验证某个 Tool 或 Resource 是否工作正常。虽然编写 Python 客户端代码是最正规的方式，但有时手边只有命令行。

本文将手把手教你如何使用 `curl` 征服 MCP over SSE 协议。

## 1. 原理解析：为什么需要两个窗口？

MCP (Model Context Protocol) 在使用 SSE (Server-Sent Events) 传输时，采用了 **"读写分离"** 的模式：

*   **读 (Read)**: 一个持久的 HTTP 长连接，服务器通过它源源不断地推送数据（Events）。
*   **写 (Write)**: 短暂的 HTTP POST 请求，客户端通过它发送指令。

因此，我们需要打开两个终端窗口：一个负责“听”，一个负责“说”。

---

## 2. 准备工作

假设您的 FastMCP Server 运行在本地：
*   **Host**: `127.0.0.1`
*   **Port**: `13333`

---

## 3. 实战步骤

### 第一步：建立监听 (Terminal A)

打开第一个终端窗口，输入以下命令连接到 SSE 端点：

```bash
curl -N http://127.0.0.1:13333/sse
```
*注意：`-N` 参数至关重要，它告诉 curl 禁用缓冲，立即显示服务器推过来的数据。*

**Sample Output (成功连接):**
```
event: endpoint
data: /messages/?session_id=6e0d5044d8fd45b595fbba50a15d65c4

: ping - 2026-01-03 10:00:10.371033+00:00
```

👉 **关键动作**：请复制 `data:` 后面的完整路径 `/messages/?session_id=...`。这是您的专属通信频道。

---

### 第二步：发送指令 (Terminal B)

保持 Terminal A 开启，打开第二个终端窗口。我们将构造一个 JSON-RPC 请求来调用工具。

**假设我们要调用的工具是 `multiply`，参数是 `a=3, b=4`。**

构造 POST 请求：
1.  **URL**: 拼接 host 和刚才复制的路径。
    *   ⚠️ **注意**：URL 末尾的斜杠 `/` 不能少！FastMCP 默认路由是 `/messages/`。如果少了斜杠，会收到 `307 Redirect` 错误。
2.  **Body**: 标准的 JSON-RPC 2.0 格式。

**命令示例**：
```bash
curl -X POST "http://127.0.0.1:13333/messages/?session_id=YOUR_SESSION_ID_HERE" \
     -H "Content-Type: application/json" \
     -d '{
           "jsonrpc": "2.0", 
           "method": "tools/call", 
           "params": {
             "name": "multiply", 
             "arguments": {"a": 3, "b": 4}
           }, 
           "id": 1
         }'
```

**Terminal B 的 Sample Output**:
```
Accepted
```
*(是的，这里通常只返回 Accepted，表示服务器已收到请求。真正的结果会在 Terminal A 显示。)*

---

### 第三步：查看结果 (Terminal A)

回到第一个窗口，您会看到新的事件被推出来了：

**Sample Output (工具执行结果):**
```
event: message
data: {"jsonrpc":"2.0","id":1,"result":{"content":[{"type":"text","text":"12.0"}]}}
```
可以看到，`result` 字段里包含了计算结果 `12.0`。

---

## 4. 常见坑点排查 (Troubleshooting)

### Q: 发送 POST 后没反应？
*   **检查 Terminal A**：结果是异步返回的，一定要看监听窗口。
*   **检查斜杠**：确认 POST URL 是 `/messages/?...` 而不是 `/messages?...`。可以加 `-v` 参数查看是否返回了 `307 Temporary Redirect`。

### Q: Session ID 过期？
*   SSE 连接如果断开，Session ID 就会失效。每次重新运行 `curl -N .../sse` 都会生成一个新的 ID，发 POST 时记得更新。

### Q: 乱码或无输出？
*   确保 `curl` 加上了 `-N` (no buffer)。
*   确保 `curl` 加上了 `-H "Content-Type: application/json"`，否则服务器可能不解析 Body。
