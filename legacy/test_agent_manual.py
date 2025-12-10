import asyncio
from agent import create_graph
from langchain_core.messages import HumanMessage

async def test():
    print("Initializing graph...")
    try:
        graph = create_graph()
    except Exception as e:
        print(f"Failed to create graph: {e}")
        return

    print("Graph initialized. Running query...")
    inputs = {"messages": [HumanMessage(content="What tables are in the database?")]}
    
    async for event in graph.astream(inputs, stream_mode="values"):
        message = event["messages"][-1]
        print(f"[{message.type}]: {message.content}")

if __name__ == "__main__":
    asyncio.run(test())
