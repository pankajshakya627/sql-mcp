import asyncio
import sys
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_client_query(query: str):
    # Define the server connection parameters
    # We are connecting to our own agent.py script acting as the server
    server_params = StdioServerParameters(
        command=sys.executable,  # Use the current python interpreter
        args=["agent.py"],       # Run agent.py
        env=os.environ.copy()    # Pass current environment (API keys, etc.)
    )

    print(f"🔌 Connecting to MCP Server (agent.py)...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            
            # List available tools to confirm connection
            tools = await session.list_tools()
            print(f"🛠️  Available Tools on Server: {[t.name for t in tools.tools]}")
            
            # Call the 'ask_database' tool exposed by the server
            print(f"🚀 Sending Query to Agent: '{query}'")
            print("⏳ Waiting for Agent to reason and execute tools...\n")
            
            # The agent logic happens inside the server now
            result = await session.call_tool("ask_database", arguments={"question": query})
            
            # Display the result
            if result.content:
                print("--- 🤖 Agent Response (via MCP) ---")
                for content in result.content:
                    print(content.text)
            else:
                print("No response content.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python client.py \"Your question here\"")
        sys.exit(1)
        
    query = sys.argv[1]
    asyncio.run(run_client_query(query))
