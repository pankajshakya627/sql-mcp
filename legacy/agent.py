import os
import sys
from typing import Annotated, TypedDict, List

from fastmcp import FastMCP
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv

# Import tools from the existing server implementation
# We will wrap them for LangChain
from server import query_database, get_database_schema

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("sql-agent")

# Define the state of the agent
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# --- Tool Definitions for LangChain ---

@tool
def run_sql_tool(query: str) -> str:
    """
    Execute a read-only SQL query against the organization database.
    Input should be a valid SQL SELECT statement.
    """
    try:
        results = query_database(query)
        return str(results)
    except Exception as e:
        return f"Error executing SQL: {e}"

@tool
def get_schema_tool() -> str:
    """
    Get the database schema, including table names and columns.
    Use this to understand the database structure before querying.
    """
    try:
        return get_database_schema()
    except Exception as e:
        return f"Error getting schema: {e}"

# List of tools for the LLM
tools = [run_sql_tool, get_schema_tool]

# --- LangGraph Setup ---

def create_graph():
    # Check for API Key
    api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY or OPENAI_API_KEY environment variable not set.")

    # Initialize LLM with OpenRouter
    llm = ChatOpenAI(
        model="amazon/nova-2-lite-v1:free",  # User preferred model
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0
    )
    
    llm_with_tools = llm.bind_tools(tools)

    def chatbot(state: AgentState):
        messages = state["messages"]
        # Debug: Print the last message if it's a tool output
        if len(messages) > 0 and messages[-1].type == "tool":
             print(f"[DEBUG] Chatbot received tool output: {messages[-1].content}")
             
        return {"messages": [llm_with_tools.invoke(messages)]}

    graph_builder = StateGraph(AgentState)
    graph_builder.add_node("chatbot", chatbot)
    
    tool_node = ToolNode(tools)
    graph_builder.add_node("tools", tool_node)

    graph_builder.add_conditional_edges(
        "chatbot",
        lambda state: "tools" if state["messages"][-1].tool_calls else END,
    )
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.set_entry_point("chatbot")
    
    return graph_builder.compile()

# Compile the graph once
try:
    agent_graph = create_graph()
except Exception as e:
    print(f"Warning: Failed to initialize graph (likely missing API key): {e}")
    agent_graph = None

# --- FastMCP Tool Exposure ---

@mcp.tool()
def ask_database(question: str) -> str:
    """
    Ask a natural language question about the database.
    The agent will reason, check the schema, generate SQL, and return the answer.
    """
    if not agent_graph:
        return "Error: Agent not initialized. Check server logs/environment variables."

    # Interactive loop or single query
    system_message = SystemMessage(content="You are a helpful SQL assistant. Use the available tools to answer the user's question. If a tool returns a SQL query, present that EXACT query to the user. Do NOT modify the SQL returned by the tool.")
    
    inputs = {
        "messages": [
            system_message,
            HumanMessage(content=question)
        ]
    }
    
    if len(sys.argv) > 1:
        print(f"--- Input Messages ---\n{inputs['messages']}\n----------------------")
    
    final_response = ""
    for event in agent_graph.stream(inputs, stream_mode="values"):
        message = event["messages"][-1]
        if isinstance(message, BaseMessage) and message.content:
             final_response = message.content
             
    return str(final_response)

@mcp.tool()
def generate_sql_query(question: str) -> str:
    """
    Generate a SQL query based on a natural language question.
    This tool DOES NOT execute the query, it only returns the SQL code.
    """
    # Check for API Key
    api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "Error: API key not set."

    # Initialize LLM
    llm = ChatOpenAI(
        model="x-ai/grok-4.1-fast:free",
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0
    )
    
    schema = get_database_schema()
    
    prompt_content = f"""You are an expert SQL generator.
    Database Schema:
    {schema}
    
    User Question: {question}
    
    CRITICAL RULES:
    1. Return ONLY the SQL query. No markdown, no explanations.
    2. YOU MUST USE 'ILIKE' for ALL string comparisons. DO NOT use '=' for strings.
    3. Check the 'Sample Data Context' in the schema.
    """
    
    messages = [
        HumanMessage(content=prompt_content)
    ]
    
    response = llm.invoke(messages)
    sql = response.content.strip()
    
    # Fallback: Manually force ILIKE if the model fails
    if "=" in sql and "ILIKE" not in sql.upper():
        sys.stderr.write(f"[DEBUG] Regex Fallback Triggered! Original: {sql}\n")
        import re
        # Replace = 'Value' with ILIKE '%Value%'
        sql = re.sub(r"=\s*'([^']*)'", r"ILIKE '%\1%'", sql)
        sys.stderr.write(f"[DEBUG] Fixed SQL: {sql}\n")
        
    return sql


# --- FastMCP Resources ---

@mcp.resource("schema://database")
def resource_database_schema() -> str:
    """
    The complete database schema including tables, columns, and relationships.
    Use this resource to understand the database structure before generating queries.
    """
    from database_schema import DATABASE_SCHEMA
    return DATABASE_SCHEMA


@mcp.resource("config://tools")
def resource_tool_catalog() -> str:
    """
    Catalog of all available tools with their descriptions and usage patterns.
    Reference this to understand which tool to use for specific tasks.
    """
    return """
# SQL Agent Tool Catalog

## Available Tools

### 1. ask_database
**Purpose**: Natural language to answer - complete pipeline
**Input**: A question in plain English
**Output**: The answer derived from the database
**Use When**: You want a complete answer without seeing intermediate SQL
**Example**: "How many employees are in the Engineering department?"

### 2. generate_sql_query  
**Purpose**: Generate SQL without execution
**Input**: A question in plain English
**Output**: The SQL query only (no execution)
**Use When**: You need to review/modify SQL before running, or need the query for documentation
**Example**: "Generate SQL to find all projects with status 'Active'"

### 3. run_sql_tool (internal)
**Purpose**: Execute raw SQL against the database
**Input**: Valid SELECT SQL statement
**Output**: Query results as list of dictionaries
**Use When**: You have a pre-built SQL query to execute

### 4. get_schema_tool (internal)
**Purpose**: Retrieve current database schema
**Input**: None
**Output**: Formatted schema string with tables and columns
**Use When**: You need to understand table structure before writing queries

## Tool Selection Matrix

| Task                          | Recommended Tool      |
|-------------------------------|----------------------|
| Quick answers                 | ask_database         |
| SQL generation only           | generate_sql_query   |
| Custom SQL execution          | run_sql_tool         |
| Schema discovery              | get_schema_tool      |
"""


@mcp.resource("samples://queries")
def resource_sample_queries() -> str:
    """
    Sample queries and common patterns for the organization database.
    Use as reference for constructing your own queries.
    """
    return """
# Sample SQL Queries

## Employee Queries

### List all employees with department and role
```sql
SELECT e.name, e.email, d.name as department, r.title as role
FROM employee e
JOIN department d ON e.department_id = d.id
JOIN role r ON e.role_id = r.id;
```

### Count employees by department
```sql
SELECT d.name as department, COUNT(e.id) as employee_count
FROM department d
LEFT JOIN employee e ON d.id = e.department_id
GROUP BY d.name
ORDER BY employee_count DESC;
```

### Find employees by name (case-insensitive)
```sql
SELECT * FROM employee WHERE name ILIKE '%john%';
```

## Department Queries

### List departments with location
```sql
SELECT name, location FROM department ORDER BY name;
```

### Department with most employees
```sql
SELECT d.name, COUNT(e.id) as count
FROM department d
JOIN employee e ON d.id = e.department_id
GROUP BY d.name
ORDER BY count DESC
LIMIT 1;
```

## Project Queries

### Active projects by department
```sql
SELECT p.name as project, d.name as department, p.status
FROM project p
JOIN department d ON p.department_id = d.id
WHERE p.status = 'Active';
```

### Projects count by status
```sql
SELECT status, COUNT(*) as count
FROM project
GROUP BY status;
```

## Role/Salary Queries

### Roles with salary ranges
```sql
SELECT title, salary_range FROM role ORDER BY title;
```

### Employees by role
```sql
SELECT r.title, COUNT(e.id) as count
FROM role r
LEFT JOIN employee e ON r.id = e.role_id
GROUP BY r.title;
```

## Important Notes
- Always use ILIKE for string comparisons (case-insensitive)
- Only SELECT queries are allowed (read-only database)
- Check schema first if unsure about column names
"""


@mcp.resource("guide://usage")
def resource_usage_guide() -> str:
    """
    Usage guide for ChatGPT Developer Mode MCP integration.
    Contains prompting strategies and best practices.
    """
    return """
# ChatGPT Developer Mode Usage Guide

## Quick Start

1. Enable the SQL Agent connector in your chat
2. Reference tools explicitly by name
3. Use the provided prompts for common tasks

## Prompting Best Practices

### Be Explicit
Always name the specific tool you want:
- "Use the sql-agent connector's ask_database tool to find all Engineering employees"
- "Use generate_sql_query to create a query for department counts"

### Specify the Action
Focus on what you want accomplished:
- "Query the database for active projects"
- "Generate SQL to list employees hired in 2024"

### Disallow Alternatives
Prevent ambiguity by restricting to this connector:
- "Do not use web search. Only use the sql-agent connector."
- "Use only the ask_database tool, not any built-in data tools."

### Multi-Step Operations
For complex flows, specify the sequence:
- "First call get_schema_tool to see the tables. Then use generate_sql_query to create a query based on what you learned."

## Resource Access

Access these resources for context:
- schema://database - Full database schema
- config://tools - Tool catalog and selection guide
- samples://queries - Example SQL patterns
- guide://usage - This usage guide

## Common Workflows

### Workflow 1: Quick Answer
"Use ask_database to tell me how many employees work in Sales"

### Workflow 2: SQL Review Before Execution
1. "Use generate_sql_query to create SQL for listing all managers"
2. Review the SQL
3. "Now execute this SQL: [paste query]"

### Workflow 3: Schema Discovery
"First get the schema using get_schema_tool, then generate SQL to join employees with their projects"
"""


@mcp.resource("context://connection")
def resource_connection_info() -> str:
    """
    Connection and environment information for the SQL agent.
    """
    return """
# Connection Information

## Database Details
- **Type**: PostgreSQL
- **Database**: org_db
- **Mode**: Read-Only (SELECT queries only)

## Supported Operations
- ✅ SELECT queries
- ✅ JOINs across tables
- ✅ Aggregations (COUNT, SUM, AVG, etc.)
- ✅ Filtering with WHERE
- ✅ Grouping with GROUP BY
- ✅ Sorting with ORDER BY

## Blocked Operations
- ❌ INSERT, UPDATE, DELETE
- ❌ CREATE, DROP, ALTER
- ❌ TRUNCATE
- ❌ Any data modification

## Performance Tips
- Use LIMIT for large result sets
- Include specific columns instead of SELECT *
- Use indexes (id columns) in WHERE clauses
"""


# --- FastMCP Prompts ---

@mcp.prompt()
def query_helper(question: str) -> str:
    """
    Generate a properly formatted prompt for asking database questions.
    Ensures the model uses the correct tool with proper context.
    """
    return f"""You are a SQL database assistant using the sql-agent connector.

TASK: Answer this database question: "{question}"

INSTRUCTIONS:
1. Use ONLY the ask_database tool from the sql-agent connector
2. Do NOT use web search or any other data sources
3. Present the results in a clear, formatted way
4. If the query fails, explain the error and suggest alternatives

Execute the query now."""


@mcp.prompt()
def schema_explorer() -> str:
    """
    Prompt for exploring and understanding the database schema.
    """
    return """You are exploring the organization database schema using the sql-agent connector.

TASK: Analyze the database structure

INSTRUCTIONS:
1. First, call get_schema_tool to retrieve the complete schema
2. Summarize the tables and their relationships
3. Identify primary and foreign key relationships
4. List the main entities and how they connect

Do NOT use any tools other than get_schema_tool from sql-agent.
Begin schema exploration now."""


@mcp.prompt()
def sql_generator_prompt(requirement: str) -> str:
    """
    Prompt for generating SQL without execution.
    Useful when you need to review the query before running.
    """
    return f"""You are a SQL query generator using the sql-agent connector.

REQUIREMENT: {requirement}

INSTRUCTIONS:
1. Use ONLY the generate_sql_query tool from sql-agent
2. The tool returns SQL only - it does NOT execute
3. After receiving the SQL, present it in a code block
4. Explain what the query does
5. Suggest any optimizations if applicable

IMPORTANT:
- Do NOT execute the query
- Do NOT use ask_database (that executes)
- Only use generate_sql_query

Generate the SQL now."""


@mcp.prompt()
def multi_step_analysis(analysis_goal: str) -> str:
    """
    Prompt for complex multi-step database analysis.
    Guides the model through a structured analysis workflow.
    """
    return f"""You are performing a multi-step database analysis using the sql-agent connector.

ANALYSIS GOAL: {analysis_goal}

WORKFLOW (execute in order):
1. STEP 1 - Schema Discovery
   - Call get_schema_tool to understand available tables
   - Note relevant tables for this analysis

2. STEP 2 - Query Planning
   - Based on schema, plan the SQL queries needed
   - Consider JOINs and aggregations required

3. STEP 3 - Data Retrieval
   - Use ask_database for each query
   - Collect and organize results

4. STEP 4 - Synthesis
   - Combine findings from all queries
   - Present insights and conclusions

RULES:
- Use ONLY sql-agent connector tools
- Do NOT use web search or external tools
- Execute each step before moving to the next
- If a step fails, explain and attempt recovery

Begin Step 1 now."""


@mcp.prompt()
def comparison_query(entity1: str, entity2: str, metric: str) -> str:
    """
    Prompt for comparing two entities in the database.
    """
    return f"""You are comparing database entities using the sql-agent connector.

COMPARISON:
- Entity 1: {entity1}
- Entity 2: {entity2}
- Metric: {metric}

INSTRUCTIONS:
1. Use ask_database to query data for {entity1}
2. Use ask_database to query data for {entity2}
3. Compare the {metric} between them
4. Present results in a comparison table
5. Provide analysis of the differences

RULES:
- Use ONLY ask_database from sql-agent connector
- Do NOT invent data - only use query results
- If entities don't exist, report that clearly

Begin comparison now."""


@mcp.prompt()
def report_generator(report_type: str) -> str:
    """
    Prompt for generating database reports.
    Supports: employee_summary, department_overview, project_status
    """
    report_templates = {
        "employee_summary": """
REPORT: Employee Summary Report

QUERIES TO EXECUTE (use ask_database for each):
1. Total employee count
2. Employee count by department
3. Employee count by role
4. Recent hires (if hire_date available)

OUTPUT FORMAT:
- Executive summary paragraph
- Breakdown tables
- Key insights""",
        
        "department_overview": """
REPORT: Department Overview Report

QUERIES TO EXECUTE (use ask_database for each):
1. List all departments with locations
2. Employee count per department
3. Project count per department
4. Largest and smallest departments

OUTPUT FORMAT:
- Department summary table
- Resource allocation insights
- Recommendations""",
        
        "project_status": """
REPORT: Project Status Report

QUERIES TO EXECUTE (use ask_database for each):
1. Projects by status (Active, Completed, etc.)
2. Projects per department
3. Department with most active projects

OUTPUT FORMAT:
- Status distribution chart description
- Department workload analysis
- Recommendations"""
    }
    
    template = report_templates.get(report_type, f"""
REPORT: Custom Report - {report_type}

Analyze the database to generate a report on: {report_type}

Use ask_database to gather relevant data and present findings clearly.""")
    
    return f"""You are generating a database report using the sql-agent connector.

{template}

RULES:
- Use ONLY ask_database from sql-agent connector
- Present all data in formatted tables where appropriate
- Include insights and actionable recommendations
- Do NOT use external tools or web search

Begin report generation now."""


if __name__ == "__main__":
    mcp.run()
