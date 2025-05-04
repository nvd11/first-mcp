import asyncio
import src.configs.config

from fastmcp import FastMCP, Client

mcp = FastMCP("My MCP Server")

@mcp.tool()
def greet(name: str) -> str:
    """
    Greet a user by name.
    """
    return f"Hello, {name}!"


# we could run it with below command to assign host and port
# fastmcp run src/servers/mcp-server1.py:mcp --transport sse --host 127.0.0.1 --port 13333

# please note, if we use fastmcp run command, we don't need below __name__ == "__main__" block

if __name__ == "__main__":
    # only for testing purpose, to trigger it , we could just run this file in IDE 
    # or run it by python src/servers/mcp-server1.py
    mcp.run()
