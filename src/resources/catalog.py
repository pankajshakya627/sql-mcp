"""
MCP Resources for the DB Agent server.
Provides schema, tool catalog, sample queries, usage guides, and connection info.
"""
# Handle both direct execution and package imports
try:
    from src.schema import DATABASE_SCHEMA
except ImportError:
    try:
        from schema import DATABASE_SCHEMA
    except ImportError:
        DATABASE_SCHEMA = """
# Database Schema (fallback)
Tables: department, role, employee, project
"""


def get_database_schema_resource() -> str:
    """
    The complete database schema including tables, columns, and relationships.
    Use this resource to understand the database structure before generating queries.
    """
    return DATABASE_SCHEMA


def get_tool_catalog() -> str:
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

### 3. execute_sql
**Purpose**: Execute raw SQL against the database
**Input**: Valid SELECT SQL statement
**Output**: Query results as list of dictionaries
**Use When**: You have a pre-built SQL query to execute

### 4. get_schema
**Purpose**: Retrieve current database schema
**Input**: None
**Output**: Formatted schema string with tables and columns
**Use When**: You need to understand table structure before writing queries

### 5. validate_sql
**Purpose**: Validate SQL syntax without executing
**Input**: SQL query string
**Output**: Validation feedback and suggestions

### 6. get_optimization_tips
**Purpose**: Get query optimization suggestions
**Input**: SQL query string
**Output**: Performance improvement tips

## Tool Selection Matrix

| Task                          | Recommended Tool      |
|-------------------------------|----------------------|
| Quick answers                 | ask_database         |
| SQL generation only           | generate_sql_query   |
| Custom SQL execution          | execute_sql          |
| Schema discovery              | get_schema           |
| Check SQL syntax              | validate_sql         |
| Query performance             | get_optimization_tips|
"""


def get_sample_queries() -> str:
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


def get_usage_guide() -> str:
    """
    Usage guide for ChatGPT Developer Mode MCP integration.
    Contains prompting strategies and best practices.
    """
    return """
# ChatGPT Developer Mode Usage Guide

## Quick Start

1. Enable the db-agent-mcp connector in your chat
2. Reference tools explicitly by name
3. Use the provided prompts for common tasks

## Prompting Best Practices

### Be Explicit
Always name the specific tool you want:
- "Use the db-agent-mcp connector's ask_database tool to find all Engineering employees"
- "Use generate_sql_query to create a query for department counts"

### Specify the Action
Focus on what you want accomplished:
- "Query the database for active projects"
- "Generate SQL to list employees hired in 2024"

### Disallow Alternatives
Prevent ambiguity by restricting to this connector:
- "Do not use web search. Only use the db-agent-mcp connector."
- "Use only the ask_database tool, not any built-in data tools."

### Multi-Step Operations
For complex flows, specify the sequence:
- "First call get_schema to see the tables. Then use generate_sql_query to create a query based on what you learned."

## Resource Access

Access these resources for context:
- schema://database - Full database schema
- config://tools - Tool catalog and selection guide
- samples://queries - Example SQL patterns
- guide://usage - This usage guide
- context://connection - Database connection info

## Common Workflows

### Workflow 1: Quick Answer
"Use ask_database to tell me how many employees work in Sales"

### Workflow 2: SQL Review Before Execution
1. "Use generate_sql_query to create SQL for listing all managers"
2. Review the SQL
3. "Now execute this SQL: [paste query]"

### Workflow 3: Schema Discovery
"First get the schema using get_schema, then generate SQL to join employees with their projects"
"""


def get_connection_info() -> str:
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
