# 疑难杂症：如何让 Cline 乖乖使用 MCP Tool？

在开发 MCP Server 时，我们经常遇到一个令人头秃的问题：
**明明我写好了 Tool，也连接上了 Server，但 Cline 就是不用！**
它非要自己去运行 `gh` 命令，或者打开浏览器去搜，甚至直接说“我不知道怎么做”。

本文总结了导致“Cline 无视 MCP”的三大原因及解决方案。

---

## 原因一：缓存作祟 (Cache is the Enemy)

**现象**：
*   你刚加了新 Tool，或者刚改了 Tool 的名字/参数。
*   Cline 报错 `Unknown tool` 或 `Invalid parameters`。
*   Tool 名字前面带有奇怪的乱码前缀（如 `cIve1W0...`）。

**真相**：
Cline 为了性能，会缓存 Server 的工具列表。当你修改了 Server 代码（特别是增加了 Tool 或修改了签名），Cline 并不知道。它还在试图调用旧的工具，或者用旧的参数去调用。

**💊 处方：双重重启**
1.  **重启 Server**：确保新代码生效（特别是 Python 进程，必须 Ctrl+C 杀掉重开）。
2.  **重启 Cline (Reload Window)**：在 VS Code 中 `Cmd+Shift+P` -> `Reload Window`。这会强制 Cline 重新握手，拉取最新的工具列表。

---

## 原因二：Tool 根本没暴露 (The Hidden Tool)

**现象**：
*   你在 `service.py` 里写了很棒的逻辑。
*   但在 `server.py` 里忘记加 `@mcp.tool` 包装器。
*   或者忘了在 Server 入口文件中导入那个 Tool。

**真相**：
Cline 只能看到被 `@mcp.tool()` 装饰过的函数。如果你的功能只是一个普通的 Python 函数，Cline 是看不见的。

**💊 处方：检查入口**
确保你的 Server 代码里有类似这样的“胶水代码”：

```python
# my_server.py

# 1. 必须导入!
from my_services import amazing_function

# 2. 必须装饰!
@mcp.tool()
def my_amazing_tool(arg: str):
    """
    这里必须写清楚 Tool 是干嘛的！
    """
    return amazing_function(arg)
```

---

## 原因三：LLM 的“惯性” (Habitual Behavior)

**现象**：
*   Tool 也有了，缓存也清了。
*   你问：“查一下 GitHub Repo”。
*   Cline 转头就去运行 `gh repo list` 命令了。

**真相**：
Cline 的底层模型（如 Claude 3.5 Sonnet）在训练时见过大量的 CLI 操作。它潜意识里觉得“查 Repo = 运行 gh 命令”。如果你的 Tool 描述不够吸引人，或者 Instructions 没禁止它用 CLI，它就会走老路。

**💊 处方：软硬兼施**

1.  **软：优化 Tool Docstring**
    把 Tool 吹得厉害一点。
    *   ❌ *"List repos."* (太干瘪)
    *   ✅ *"The official, most accurate way to retrieve GitHub repositories. Faster and more reliable than CLI."* (官方、准确、快速)

2.  **硬：强化 Server Instructions**
    在 Server 的 `instructions` 里下死命令。
    
    ```python
    mcp = FastMCP(
        name="MyServer",
        instructions="""
        ...
        IMPORTANT RULES:
        1. When the user asks for GitHub data, **YOU MUST USE THE MCP TOOLS**.
        2. **DO NOT** use terminal commands (like `gh`) or web browser.
        3. The MCP tools are your primary source of truth.
        ...
        """
    )
    ```

---

## 总结 Checklist

如果 Cline 不听话，请按此顺序排查：

1.  [ ] **Server 重启了吗？** (代码生效)
2.  [ ] **Window Reload 了吗？** (缓存刷新)
3.  [ ] **@mcp.tool 加了吗？** (暴露接口)
4.  [ ] **Docstring 写好了吗？** (诱导 LLM)
5.  [ ] **Instructions 强调了吗？** (强制 LLM)
