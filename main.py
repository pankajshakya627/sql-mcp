"""
DB Agent MCP Server - Unified FastMCP server for database operations.

Run with: python main.py
"""
import os
import sys
from typing import Annotated, TypedDict, List, Dict, Any

from fastmcp import FastMCP
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from tools.database import (
    query_database, 
    get_employees, 
    get_departments, 
    get_database_schema
)
from tools.sql_generator import (
    generate_sql_query as gen_sql,
    validate_sql_syntax,
    get_query_optimization_tips
)
from resources.catalog import (
    get_database_schema_resource,
    get_tool_catalog,
    get_sample_queries,
    get_usage_guide,
    get_connection_info
)
from prompts.templates import (
    query_helper,
    schema_explorer,
    sql_generator_prompt,
    multi_step_analysis,
    comparison_query,
    report_generator
)

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("db-agent-mcp")


# =============================================================================
# LANGGRAPH AGENT SETUP
# =============================================================================

class AgentState(TypedDict):
    """State definition for the LangGraph agent."""
    messages: Annotated[list[BaseMessage], add_messages]


@tool
def run_sql_tool(query: str) -> str:
    """Execute a read-only SQL query against the organization database."""
    try:
        results = query_database(query)
        return str(results)
    except Exception as e:
        return f"Error executing SQL: {e}"


@tool
def get_schema_tool() -> str:
    """Get the database schema, including table names and columns."""
    try:
        return get_database_schema()
    except Exception as e:
        return f"Error getting schema: {e}"


agent_tools = [run_sql_tool, get_schema_tool]


def create_agent_graph():
    """Create and compile the LangGraph agent for database queries."""
    api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY or OPENAI_API_KEY environment variable not set.")

    llm = ChatOpenAI(
        model="amazon/nova-2-lite-v1:free",
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0
    )
    
    llm_with_tools = llm.bind_tools(agent_tools)

    def chatbot(state: AgentState):
        messages = state["messages"]
        return {"messages": [llm_with_tools.invoke(messages)]}

    graph_builder = StateGraph(AgentState)
    graph_builder.add_node("chatbot", chatbot)
    
    tool_node = ToolNode(agent_tools)
    graph_builder.add_node("tools", tool_node)

    graph_builder.add_conditional_edges(
        "chatbot",
        lambda state: "tools" if state["messages"][-1].tool_calls else END,
    )
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.set_entry_point("chatbot")
    
    return graph_builder.compile()


# Initialize agent
try:
    agent_graph = create_agent_graph()
except Exception as e:
    print(f"Warning: Failed to initialize agent: {e}")
    agent_graph = None


# =============================================================================
# MCP TOOLS
# =============================================================================

@mcp.tool()
def ask_database(question: str) -> str:
    """Ask a natural language question about the database."""
    if not agent_graph:
        return "Error: Agent not initialized. Check API key."

    system_message = SystemMessage(
        content="You are a helpful SQL assistant. Use the available tools to answer the user's question."
    )
    
    inputs = {"messages": [system_message, HumanMessage(content=question)]}
    
    final_response = ""
    for event in agent_graph.stream(inputs, stream_mode="values"):
        message = event["messages"][-1]
        if isinstance(message, BaseMessage) and message.content:
            final_response = message.content
             
    return str(final_response)


@mcp.tool()
def generate_sql_query(question: str) -> str:
    """Generate a SQL query without executing it."""
    return gen_sql(question)


@mcp.tool()
def execute_sql(query: str) -> str:
    """Execute a raw SQL SELECT query."""
    try:
        results = query_database(query)
        return str(results)
    except Exception as e:
        return f"Error executing SQL: {e}"


@mcp.tool()
def get_schema() -> str:
    """Get the database schema."""
    return get_database_schema()


@mcp.tool()
def validate_sql(query: str) -> str:
    """Validate SQL query syntax."""
    return validate_sql_syntax(query)


@mcp.tool()
def get_optimization_tips(query: str) -> str:
    """Get query optimization tips."""
    return get_query_optimization_tips(query)


@mcp.tool()
def list_employees(department_id: int = None) -> str:
    """List employees, optionally filtered by department."""
    try:
        results = get_employees(department_id)
        return str(results)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def list_departments() -> str:
    """List all departments."""
    try:
        results = get_departments()
        return str(results)
    except Exception as e:
        return f"Error: {e}"


# =============================================================================
# MCP RESOURCES
# =============================================================================

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db-agent-mcp")

@mcp.resource("schema://database")
def resource_database_schema() -> str:
    """Complete database schema."""
    logger.info("📖 Resource accessed: schema://database")
    return get_database_schema_resource()


@mcp.resource("config://tools")
def resource_tool_catalog() -> str:
    """Tool catalog with usage patterns."""
    logger.info("📖 Resource accessed: config://tools")
    return get_tool_catalog()


@mcp.resource("samples://queries")
def resource_sample_queries() -> str:
    """Sample SQL queries."""
    logger.info("📖 Resource accessed: samples://queries")
    return get_sample_queries()


@mcp.resource("guide://usage")
def resource_usage_guide() -> str:
    """Usage guide for ChatGPT Developer Mode."""
    logger.info("📖 Resource accessed: guide://usage")
    return get_usage_guide()


@mcp.resource("context://connection")
def resource_connection_info() -> str:
    """Database connection info."""
    logger.info("📖 Resource accessed: context://connection")
    return get_connection_info()


# =============================================================================
# MCP PROMPTS
# =============================================================================

@mcp.prompt()
def prompt_query_helper(question: str) -> str:
    """Prompt for database questions."""
    return query_helper(question)


@mcp.prompt()
def prompt_schema_explorer() -> str:
    """Prompt for schema exploration."""
    return schema_explorer()


@mcp.prompt()
def prompt_sql_generator(requirement: str) -> str:
    """Prompt for SQL generation."""
    return sql_generator_prompt(requirement)


@mcp.prompt()
def prompt_multi_step_analysis(analysis_goal: str) -> str:
    """Prompt for multi-step analysis."""
    return multi_step_analysis(analysis_goal)


@mcp.prompt()
def prompt_comparison(entity1: str, entity2: str, metric: str) -> str:
    """Prompt for entity comparison."""
    return comparison_query(entity1, entity2, metric)


@mcp.prompt()
def prompt_report(report_type: str) -> str:
    """Prompt for report generation."""
    return report_generator(report_type)


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # mcp.run()
    mcp.run(
        host="0.0.0.0",
        port=8000,
        transport='http'
    )
