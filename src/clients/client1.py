import src.configs.config
from loguru import logger
import asyncio
from fastmcp import Client

async def test_gemini_analysis():
    server_url = "http://127.0.0.1:13333/sse" # Make sure this matches your server's host and port

    await asyncio.sleep(1)  # Add a small delay
    logger.info(f"Connecting to MCP server at {server_url}...")
    async with Client(server_url) as client:
        logger.info(f"Transport: {client.transport}")

        print(f"Connected to MCP server at {server_url}...")
        await call_tool(client,"Ford")

    # if not client.is_connected():
        # print("Client is not connected. Please check the server status.")
        # return


async def call_tool(client: Client, name: str):
    try:
        result = await client.call_tool("greet", {"name": name})
        print(result)
    except Exception as e:
        print(f"Error calling tool: {e}")


if __name__ == "__main__":
    asyncio.run(test_gemini_analysis())
