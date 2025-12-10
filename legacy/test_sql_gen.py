import asyncio
import sys
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_sql_generation():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["agent.py"],
        env=os.environ.copy()
    )

    print(f"🔌 Connecting to MCP Server...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            tools = await session.list_tools()
            tool_names = [t.name for t in tools.tools]
            print(f"🛠️  Available Tools: {tool_names}")
            
            if "generate_sql_query" not in tool_names:
                print("❌ Error: 'generate_sql_query' tool not found!")
                return

            question = "Show me the top 3 departments with the most employees"
            print(f"\n❓ Question: {question}")
            
            result = await session.call_tool("generate_sql_query", arguments={"question": question})
            
            if result.content:
                print("\n--- 📝 Generated SQL ---")
                for content in result.content:
                    print(content.text)
            else:
                print("No response content.")

if __name__ == "__main__":
    asyncio.run(test_sql_generation())
