import src.configs.config
from src.configs.config import yaml_configs
from loguru import logger
import asyncio
from fastmcp import Client
from mcp.types import Tool
from google import genai

# Only run this block for Gemini Developer API
ai_client = genai.Client(api_key=yaml_configs["gemini"]["api_key"])
model = 'gemini-2.0-flash-001'
server_url = "http://127.0.0.1:13333/sse" # Make sure this matches your server's host and port

# Check if the model is available by attempting to generate content
try:
    logger.info("Generating content...")
    response = ai_client.models.generate_content(
        model=model, contents='Why is the sky blue?'
    )
    logger.info(response.text)
except Exception as e:
    logger.error(f"Model is not available. Please check your configuration. Error: {e}")

async def connect_my_server2():

    logger.info(f"Connecting to MCP server at {server_url}...")
    async with Client(server_url) as client:
        logger.info(f"Transport: {client.transport}")

            # Get tool descriptions from the server
        tools = await client.list_tools()

        # list the tools defined in the mcp server
        for tool in tools:
            logger.info(f"Tool: {tool.name}, Description: {tool.description}")
        
         # Example interaction:  Ask Gemini to use a tool
        user_query = "What is 3.5 times 2?"
        await process_query(client, user_query, tools)


async def process_query(client: Client, query: str, tools: list[Tool]):
    logger.info(f"Processing query: {query}")
    """Processes a user query using Gemini to select and call a tool."""
    logger.info(f"Connecting to MCP server at {server_url}...")
    try:
        prompt = f"""You are a helpful assistant that can use tools.
                    Available tools:
                    {tools}
                    User query: {query}
                    Decide which tool to use (if any) and provide the tool name and arguments as a JSON object.  If no tool is needed, respond directly to the user.

                    Example:
                    User query: What is the product of 5 and 7?
                    Your response: {{"tool_name": "multiply", "arguments": {{"a": 5, "b": 7}}}}

                    User query: What's the weather like today?
                    Your response: I cannot get the weather for you.

                    Now, respond to the user query: {query}
                    """
        logger.info(f"Generating content...")
        response = ai_client.models.generate_content(
            model=model, contents=prompt
        )
        logger.info(f"Gemini response: {response.text}")
        try:
            tool_call = eval(response.text)  # Safely evaluate Gemini's JSON response
            if "tool_name" in tool_call and "arguments" in tool_call:
                tool_name = tool_call["tool_name"]
                arguments = tool_call["arguments"]
                result = await client.call_tool(tool_name, arguments=arguments)
                logger.info(f"Result of {tool_name}({arguments}): {result}")
                print(f"The answer is: {result}")
            else:
                print(response.text)  # Gemini's direct response
        except (SyntaxError, NameError):
            print(response.text)  # Gemini's direct response if not a tool call
    except Exception as e:
        logger.error(f"Error processing query: {e}")

async def call_tool_multiply(client: Client, a: float, b: float):
    try:
        result = await client.call_tool("multiply", arguments={"a": a, "b": b})
        logger.info(f"Result of multiply({a}, {b}): {result}")
    except Exception as e:
        logger.error(f"Error calling tool: {e}")

if __name__ == "__main__":
    asyncio.run(connect_my_server2())
