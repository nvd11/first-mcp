import asyncio
import src.configs.config as app_config  # Import the config module
import google.generativeai as genai

from fastmcp import FastMCP

# Create a basic server instance
mcp = FastMCP(name="MyAssistantServer")

# You can also add instructions for how to interact with the server
mcp_with_instructions = FastMCP(
    name="HelpfulAssistant",
    instructions="This server provides data analysis tools. Call get_average() to analyze numerical data."
)

@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiplies two numbers together."""
    return a * b

@mcp.resource("data://config")
def get_config() -> dict:
    """Provides the application configuration."""
    return {"theme": "dark", "version": "1.0"}

@mcp.resource("users://{user_id}/profile")
def get_user_profile(user_id: int) -> dict:
    """Retrieves a user's profile by ID."""
    # The {user_id} in the URI is extracted and passed to this function
    return {"id": user_id, "name": f"User {user_id}", "status": "active"}

# we could run it with below command to assign host and port
# fastmcp run src/servers/my-server2.py:mcp --transport sse --host 127.0.0.1 --port 13333

# please note, if we use fastmcp run command, we don't need below __name__ == "__main__" block

if __name__ == "__main__":
    # This code only runs when the file is executed directly
    import asyncio
    asyncio.run(
    mcp.run_sse_async(
        host="127.0.0.1", 
        port=13333, 
        log_level="debug"
    )
)

