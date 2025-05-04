import src.configs.config
from loguru import logger
import asyncio
from fastmcp import Client

async def connect_my_server2():
   
    server_url = "http://127.0.0.1:13333/sse" # Make sure this matches your server's host and port

    logger.info(f"Connecting to MCP server at {server_url}...")
    async with Client(server_url) as client:
        logger.info(f"Transport: {client.transport}")

        print(f"Connected to MCP server at {server_url}...")
        await call_tool_multiply(client, 3.5, 2.0)


async def call_tool_multiply(client: Client, a: float, b: float):
    try:
        result = await client.call_tool("multiply", arguments={"a": a, "b": b})
        logger.info(f"Result of multiply({a}, {b}): {result}")
    except Exception as e:
        logger.error(f"Error calling tool: {e}")


if __name__ == "__main__":
    asyncio.run(connect_my_server2())
