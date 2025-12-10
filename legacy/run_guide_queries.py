import asyncio
from agent import create_graph
from langchain_core.messages import HumanMessage

async def run_queries():
    print("Initializing agent...")
    try:
        graph = create_graph()
    except Exception as e:
        print(f"Failed to create graph: {e}")
        return

    # Query 1: Level 1 - The "Big Picture" View
    print("\n--- Running Level 1 Query (Natural Language) ---")
    question = "Generate a full roster of all employees that shows their names, their job titles, and which department and location they are assigned to."
    print(f"Question: {question}")
    
    inputs = {"messages": [HumanMessage(content=question)]}
    async for event in graph.astream(inputs, stream_mode="values"):
        message = event["messages"][-1]
        if message.type == "ai" and message.content:
            print(f"\nAgent Answer:\n{message.content}")

    # Query 2: Direct SQL Execution (Level 3 - Headcount)
    print("\n--- Running Level 3 Query (Direct SQL Request) ---")
    sql_query = """
    SELECT 
        r.title AS job_title, 
        COUNT(e.id) AS headcount
    FROM role r
    JOIN employee e ON r.id = e.role_id
    GROUP BY r.title
    ORDER BY headcount DESC;
    """
    request = f"Execute this SQL query:\n{sql_query}"
    print(f"Request: {request}")
    
    inputs = {"messages": [HumanMessage(content=request)]}
    async for event in graph.astream(inputs, stream_mode="values"):
        message = event["messages"][-1]
        if message.type == "ai" and message.content:
            print(f"\nAgent Answer:\n{message.content}")

if __name__ == "__main__":
    asyncio.run(run_queries())
