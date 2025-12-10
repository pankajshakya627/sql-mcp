import asyncio
import sys
from agent import create_graph
from langchain_core.messages import HumanMessage

async def main():
    if len(sys.argv) < 2:
        print("Usage: python query.py \"Your natural language query here\"")
        sys.exit(1)

    query = sys.argv[1]
    print(f"Processing query: \"{query}\"...\n")

    try:
        graph = create_graph()
        if not graph:
            print("Error: Could not initialize agent graph.")
            return

        inputs = {"messages": [HumanMessage(content=query)]}
        
        # Stream the output to show progress/results
        async for event in graph.astream(inputs, stream_mode="values"):
            message = event["messages"][-1]
            if message.type == "ai" and message.content:
                print(f"\n--- Answer ---\n{message.content}\n")
                
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
