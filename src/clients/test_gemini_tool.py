import src.configs.config
from loguru import logger
import asyncio
from fastmcp import Client

async def test_gemini_analysis():
   
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

   #try:
   #    # Sample data to send for analysis
   #    sample_data = [15.2, 18.5, 16.8, 20.1, 17.9, 19.3]
   #    print(f"Calling 'analyze_data_with_gemini' with data: {sample_data}")

   #    # Use the client to call the tool
   #    # The tool name matches the function name in src/mry-server2.py
   #    # The arguments match the parameter name in the function definition
   #    result = await client.call_tool("analyze_data_with_gemini", arguments={"data_points": sample_data})

   #    print("\n--- Gemini Analysis Result ---")
   #    print(result)
   #    print("-----------------------------\n")

   #except Exception as e:
   #    print(f"\nError during test: {e}")
   #    print("Please ensure the MCP server (src/my-server2.py) is running.")
   #    print("Also, verify that your Gemini API key is correctly configured in src/configs/config_dev.yaml.")

   #finally:
   #    # Close the client connection if necessary (depends on client implementation details)
   #    # For httpx-based clients like this one, explicit closing might not be strictly needed
   #    # but it's good practice if a close method exists.
   #    # await client.close() # Uncomment if the client has an async close method
   #    pass

if __name__ == "__main__":
    asyncio.run(test_gemini_analysis())
