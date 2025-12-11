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
# Note: Prompts are now defined inline in main.py as templates

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
# DATABASE CONNECTION TOOLS (Real-time Database Access)
# =============================================================================

@mcp.tool()
def db_status() -> str:
    """Check database connection status and configuration."""
    import os
    db_url = os.environ.get("DATABASE_URL", "")
    static_mode = os.environ.get("STATIC_SCHEMA_MODE", "true").lower() == "true"
    
    status = {
        "static_mode": static_mode,
        "database_configured": bool(db_url),
        "database_host": db_url.split("@")[1].split("/")[0] if "@" in db_url else "Not configured"
    }
    
    if not static_mode and db_url:
        try:
            from tools.database import get_connection
            conn = get_connection()
            conn.close()
            status["connection_test"] = "✅ Connected successfully"
        except Exception as e:
            status["connection_test"] = f"❌ Connection failed: {e}"
    else:
        status["connection_test"] = "⚠️ Running in static mode"
    
    return str(status)


@mcp.tool()
def run_query(sql_query: str) -> str:
    """
    Execute a real-time SQL query against the connected database.
    Only SELECT queries are allowed for safety.
    Returns live results from the database.
    """
    if not sql_query.strip().upper().startswith("SELECT"):
        return "❌ Error: Only SELECT queries are allowed for safety."
    
    try:
        results = query_database(sql_query)
        if isinstance(results, str) and "static schema mode" in results:
            return results
        
        # Format results nicely
        if isinstance(results, list) and len(results) > 0:
            # Create markdown table
            headers = list(results[0].keys()) if isinstance(results[0], dict) else []
            if headers:
                table = "| " + " | ".join(headers) + " |\n"
                table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
                for row in results[:50]:  # Limit to 50 rows
                    table += "| " + " | ".join(str(row.get(h, "")) for h in headers) + " |\n"
                if len(results) > 50:
                    table += f"\n*...and {len(results) - 50} more rows*"
                return f"**Query Results ({len(results)} rows):**\n\n{table}"
        return str(results)
    except Exception as e:
        return f"❌ Query error: {e}"


@mcp.tool()
def get_table_info(table_name: str) -> str:
    """
    Get detailed information about a specific table including columns, types, and row count.
    """
    try:
        # Get column info
        schema_query = f"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = '{table_name}'
            ORDER BY ordinal_position;
        """
        columns = query_database(schema_query)
        
        if isinstance(columns, str) and "static schema mode" in columns:
            return columns
        
        # Get row count
        count_result = query_database(f"SELECT COUNT(*) as count FROM {table_name}")
        row_count = count_result[0]['count'] if count_result else 0
        
        # Format output
        output = f"# Table: {table_name}\n\n"
        output += f"**Total rows:** {row_count}\n\n"
        output += "## Columns\n\n"
        output += "| Column | Type | Nullable | Default |\n"
        output += "|--------|------|----------|--------|\n"
        for col in columns:
            output += f"| {col['column_name']} | {col['data_type']} | {col['is_nullable']} | {col.get('column_default', '-')} |\n"
        
        # Get sample data
        sample = query_database(f"SELECT * FROM {table_name} LIMIT 5")
        if sample and isinstance(sample, list):
            output += f"\n## Sample Data (5 rows)\n\n"
            headers = list(sample[0].keys())
            output += "| " + " | ".join(headers) + " |\n"
            output += "| " + " | ".join(["---"] * len(headers)) + " |\n"
            for row in sample:
                output += "| " + " | ".join(str(row.get(h, "")) for h in headers) + " |\n"
        
        return output
    except Exception as e:
        return f"❌ Error getting table info: {e}"


@mcp.tool()
def list_tables() -> str:
    """List all tables in the database with row counts."""
    try:
        tables_query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """
        tables = query_database(tables_query)
        
        if isinstance(tables, str) and "static schema mode" in tables:
            return tables
        
        output = "# Database Tables\n\n"
        output += "| Table | Row Count |\n"
        output += "|-------|----------|\n"
        
        for table in tables:
            table_name = table['table_name']
            try:
                count_result = query_database(f"SELECT COUNT(*) as count FROM {table_name}")
                count = count_result[0]['count'] if count_result else 0
            except:
                count = "?"
            output += f"| {table_name} | {count} |\n"
        
        return output
    except Exception as e:
        return f"❌ Error listing tables: {e}"


# =============================================================================
# TEMPLATE TOOLS (Report Generators)
# =============================================================================

@mcp.tool()
def employee_report() -> str:
    """Generate a comprehensive employee summary report with department and role breakdown."""
    try:
        employees = get_employees()
        departments = get_departments()
        schema = get_database_schema()
        
        return f"""# Employee Summary Report

## Overview
Generated employee report based on organization database.

## Database Schema
{schema}

## All Employees
{employees}

## All Departments
{departments}

## Insights
- Use ask_database for specific queries like "How many employees per department?"
- Use generate_sql_query to create custom reports
"""
    except Exception as e:
        return f"Error generating report: {e}"


@mcp.tool()
def department_report() -> str:
    """Generate a department analysis report showing all departments and their details."""
    try:
        departments = get_departments()
        
        return f"""# Department Analysis Report

## All Departments
{departments}

## Available Queries
You can use ask_database with questions like:
- "How many employees in Engineering?"
- "Which department has the most projects?"
- "List employees in Sales department"
"""
    except Exception as e:
        return f"Error generating report: {e}"


@mcp.tool()
def schema_report() -> str:
    """Generate a complete database schema documentation report."""
    try:
        schema = get_database_schema()
        
        return f"""# Database Schema Report

{schema}

## Table Relationships
- employee.department_id → department.id
- employee.role_id → role.id
- project.department_id → department.id

## Common Query Patterns

### Join employees with departments:
```sql
SELECT e.name, d.name as department
FROM employee e
JOIN department d ON e.department_id = d.id;
```

### Count by department:
```sql
SELECT d.name, COUNT(*) as count
FROM department d
JOIN employee e ON d.id = e.department_id
GROUP BY d.name;
```

### Filter by status:
```sql
SELECT * FROM project WHERE status = 'Active';
```
"""
    except Exception as e:
        return f"Error generating report: {e}"


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
# MCP PROMPTS (Templates for ChatGPT)
# =============================================================================

@mcp.prompt(
    name="Employee Report",
    description="Generate a comprehensive employee summary report with department breakdown"
)
def prompt_employee_report() -> str:
    """Generate employee summary report."""
    logger.info("📋 Template used: Employee Report")
    return """Generate an Employee Summary Report:

WORKFLOW:
1. Call get_schema to understand the database structure
2. Use ask_database to get total employee count
3. Use ask_database to get employee count by department
4. Use ask_database to get employee count by role
5. Format results as a professional report with tables

OUTPUT: Present a formatted report with:
- Executive summary
- Department breakdown table
- Role distribution table
- Key insights and recommendations"""


@mcp.prompt(
    name="SQL Query Builder", 
    description="Generate optimized SQL query from natural language requirement"
)
def prompt_sql_builder(requirement: str) -> str:
    """Build SQL from natural language."""
    logger.info(f"📋 Template used: SQL Query Builder - {requirement}")
    return f"""Build an SQL Query:

REQUIREMENT: {requirement}

WORKFLOW:
1. Call get_schema to see available tables
2. Use generate_sql_query with the requirement
3. Use validate_sql to check the generated query
4. Use get_optimization_tips for performance suggestions

OUTPUT: 
- The SQL query in a code block
- Explanation of what it does
- Any optimization suggestions"""


@mcp.prompt(
    name="Department Analysis",
    description="Analyze departments including employee counts, projects, and resources"
)
def prompt_department_analysis() -> str:
    """Analyze departments."""
    logger.info("📋 Template used: Department Analysis")
    return """Analyze All Departments:

WORKFLOW:
1. Use list_departments to get all departments
2. Use ask_database: "How many employees in each department?"
3. Use ask_database: "How many projects per department?"
4. Use ask_database: "Which department has most active projects?"

OUTPUT:
- Department overview table
- Employee distribution chart
- Project allocation insights
- Resource recommendations"""


@mcp.prompt(
    name="Database Schema Explorer",
    description="Explore and document the complete database structure"
)
def prompt_schema_explorer() -> str:
    """Explore database schema."""
    logger.info("📋 Template used: Database Schema Explorer")
    return """Explore Database Schema:

WORKFLOW:
1. Call get_schema to retrieve complete schema
2. Identify all tables and their columns
3. Map foreign key relationships
4. Document table purposes

OUTPUT:
- Schema diagram description
- Table summaries with column types
- Relationship map
- Common query patterns for this schema"""


@mcp.prompt(
    name="Project Status Report",
    description="Generate status report for all projects with department allocation"
)
def prompt_project_status() -> str:
    """Generate project status report."""
    logger.info("📋 Template used: Project Status Report")
    return """Generate Project Status Report:

WORKFLOW:
1. Use ask_database: "List all projects with their status"
2. Use ask_database: "Count projects by status"
3. Use ask_database: "Projects per department"
4. Identify departments with highest project load

OUTPUT:
- Project status summary
- Status distribution (Active/Completed/etc.)
- Department workload analysis
- Recommendations for resource allocation"""


@mcp.prompt(
    name="Custom Query",
    description="Execute a custom natural language query against the database"
)
def prompt_custom_query(question: str) -> str:
    """Execute custom query."""
    logger.info(f"📋 Template used: Custom Query - {question}")
    return f"""Answer Database Question:

QUESTION: {question}

WORKFLOW:
1. Call get_schema if needed to understand structure
2. Use ask_database with the question
3. Format the results clearly

OUTPUT:
- Direct answer to the question
- Supporting data in table format
- Any relevant insights"""


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
