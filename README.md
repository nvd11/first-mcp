# First MCP Project - GitHub Tool Server

This is an advanced Model Context Protocol (MCP) server built with **FastMCP** and **FastAPI**.
It provides GitHub-related AI tools and implements an enterprise-grade **Token Passthrough Authentication Mechanism**, allowing Cline/Claude clients to securely use their own GitHub tokens when connecting remotely.

## 🏗 Architecture

This project adopts an **"Onion" Layered Architecture**:

```mermaid
graph TD
    Client[Cline Client] -->|HTTP Header: X-Github-Token| FastAPI[FastAPI Wrapper (server.py)]
    FastAPI -->|Middleware Intercept| Context[ContextVars]
    FastAPI -->|Mount /mcp| FastMCP[FastMCP Core (src/servers/mcp_github_tool_server.py)]
    FastMCP -->|Tool Execution| Tool[get_repo_list]
    Tool -->|Read Token| Context
    Tool -->|Call API| GitHub[GitHub API]
```

### Core Components

1.  **FastAPI Wrapper (`server.py`)**:
    *   **Role**: Gateway & Middleware Container.
    *   **Responsibility**: Intercepts HTTP requests, extracts the `X-Github-Token` header, and stores it in Python's `ContextVars`. It also mounts the FastMCP app to the `/mcp` path.

2.  **FastMCP Core (`src/servers/mcp_github_tool_server.py`)**:
    *   **Role**: MCP Business Logic Core.
    *   **Responsibility**: Defines `@mcp.tool` and `@mcp.resource`. It is oblivious to HTTP details and simply reads the token from ContextVars to invoke the Service.

3.  **GitHub Service (`src/services/github_service.py`)**:
    *   **Role**: Business Service Layer.
    *   **Responsibility**: Encapsulates GitHub API calls. Supports token injection via constructor to achieve multi-tenant isolation.

---

## 🚀 Quick Start

### 1. Start the Server

```bash
# Install dependencies
pip install -r requirements.txt

# Start Server (Listens on port 13333)
python server.py
```

### 2. Configure Cline (VS Code)

Add the following to your Cline `mcpServers` configuration:

```json
{
  "mcpServers": {
    "my-github-server": {
      "url": "http://127.0.0.1:13333/mcp/sse",
      "transport": "sse",
      "headers": {
        "X-Github-Token": "YOUR_GITHUB_PERSONAL_ACCESS_TOKEN"
      },
      "autoApprove": []
    }
  }
}
```

---

## 📚 Documentation

This project includes a series of in-depth technical documents recording best practices and pitfalls encountered during development:

*   **[FastMCP Development Guide](docs/fastmcp_guide.md)**: Core concepts, differences between Instructions and Prompts.
*   **[Token Passthrough Solution](docs/blog_cline_token_passthrough.md)**: Detailed design document for this project's core architecture.
*   **[FastAPI Mounting Pitfalls](docs/blog_fastapi_mount_pitfall.md)**: Why you shouldn't mount to the root path.
*   **[ContextVars Deep Dive](docs/blog_python_contextvars.md)**: The secret weapon for Python concurrency.
*   **[Curl Testing Guide](docs/blog_testing_sse_with_curl.md)**: How to test SSE endpoints via command line.

## ✨ Key Features

*   ✅ **Stateless Auth**: The server stores no user tokens; tokens arrive with requests and leave with responses.
*   ✅ **Concurrency Safe**: Uses `ContextVars` to ensure tokens from different users never interfere with each other during concurrent requests.
*   ✅ **Dual Mode**: If no Header Token is provided, the service automatically falls back to the server-side `.env` configuration, facilitating local debugging.
