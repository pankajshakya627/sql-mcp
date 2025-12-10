#!/usr/bin/env python3
"""
Test script for Text-to-SQL FastMCP Server
"""
import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_server():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["text_to_sql_server.py"],
    )

    print("=" * 80)
    print("Testing Text-to-SQL FastMCP Server")
    print("=" * 80)
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("\n✅ Server initialized")
            
            # List tools
            tools = await session.list_tools()
            print(f"\n📋 Available tools ({len(tools.tools)}):")
            for tool in tools.tools:
                print(f"  - {tool.name}")
            
            # Test 1: Get schema
            print("\n" + "=" * 80)
            print("Test 1: Get Full Schema")
            print("=" * 80)
            result = await session.call_tool("get_database_schema_info", arguments={})
            print(result.content[0].text[:300] + "...")
            
            # Test 2: List tables
            print("\n" + "=" * 80)
            print("Test 2: List All Tables")
            print("=" * 80)
            result = await session.call_tool("list_all_tables", arguments={})
            print(result.content[0].text)
            
            # Test 3: Get table details
            print("\n" + "=" * 80)
            print("Test 3: Get Employee Table Details")
            print("=" * 80)
            result = await session.call_tool("get_table_details", arguments={"table_name": "employee"})
            print(result.content[0].text)
            
            # Test 4: Sample queries
            print("\n" + "=" * 80)
            print("Test 4: Get Sample Queries")
            print("=" * 80)
            result = await session.call_tool("get_sample_queries", arguments={})
            print(result.content[0].text[:400] + "...")
            
            # Test 5: Validate SQL
            print("\n" + "=" * 80)
            print("Test 5: Validate SQL Query")
            print("=" * 80)
            test_sql = "SELECT e.name, d.name FROM employee e JOIN department d ON e.department_id = d.id"
            result = await session.call_tool("validate_sql_syntax", arguments={"sql_query": test_sql})
            print(result.content[0].text)
            
            # Test 6: Optimization tips
            print("\n" + "=" * 80)
            print("Test 6: Get Optimization Tips")
            print("=" * 80)
            test_sql2 = "SELECT * FROM employee WHERE department_id = 1"
            result = await session.call_tool("get_query_optimization_tips", arguments={"sql_query": test_sql2})
            print(result.content[0].text)
            
            print("\n" + "=" * 80)
            print("✅ All tests completed successfully!")
            print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_server())
