# DB Agent MCP - ChatGPT Prompt Guide

## Quick Reference Prompts

### Getting Started

```
First, read the "schema://database" resource from the db-agent-mcp connector to understand the database structure.
```

### Query Examples

**Simple Query:**

```
Use the db-agent-mcp connector's "ask_database" tool to find all employees in the Engineering department.
Do not use web search. Only use db-agent-mcp.
```

**Generate SQL Only (no execution):**

```
Use the db-agent-mcp connector's "generate_sql_query" tool to create a SQL query that counts employees by department. Do not execute it, just show me the SQL.
```

**With Schema Context:**

```
Read the "schema://database" resource from db-agent-mcp first.
Then use the "generate_sql_query" tool to create a query joining employees with their roles.
```

**Validate SQL:**

```
Use the db-agent-mcp connector's "validate_sql" tool to check this query:
SELECT * FROM employee WHERE department_id = 1
```

---

## Advanced Prompts

### Multi-Step Analysis

```
Using ONLY the db-agent-mcp connector, perform this analysis:
1. First, call get_schema to see available tables
2. Then use generate_sql_query to create a query showing department employee counts
3. Present the results in a formatted table

Do NOT use web search or any external tools.
```

### Report Generation

```
Generate an Employee Summary Report using the db-agent-mcp connector:
1. Read "schema://database" resource for context
2. Use ask_database to get total employee count
3. Use ask_database to get employees by department
4. Format as a professional report with insights

Only use db-agent-mcp tools.
```

### Entity Comparison

```
Using db-agent-mcp, compare the Engineering and Sales departments:
1. Get employee count for each
2. Get project count for each
3. Present in a comparison table
4. Provide analysis

Do not use external tools.
```

---

## Resource-First Approach (Recommended)

Always start by reading resources for context:

```
Before answering my questions about the organization database, please:
1. Read "schema://database" from db-agent-mcp to understand tables
2. Read "samples://queries" for SQL patterns
3. Read "config://tools" to know which tools to use

Then help me find employees working on active projects.
```

---

## Best Practices

### ✅ DO:

- Name the connector explicitly: `db-agent-mcp`
- Name tools explicitly: `ask_database`, `generate_sql_query`
- Request resources first for context
- Specify "Do not use web search"

### ❌ DON'T:

- Use vague requests like "query the database"
- Expect ChatGPT to infer which tool to use
- Mix with other data sources

---

## Available Tools

| Tool                 | Purpose              | Example                        |
| -------------------- | -------------------- | ------------------------------ |
| `ask_database`       | Full Q&A pipeline    | "How many employees in Sales?" |
| `generate_sql_query` | Create SQL only      | "SQL for active projects"      |
| `execute_sql`        | Run raw SQL          | `SELECT * FROM department`     |
| `get_schema`         | View table structure | -                              |
| `validate_sql`       | Check SQL syntax     | -                              |
| `list_employees`     | Employee list        | With department filter         |
| `list_departments`   | Department list      | -                              |

## Available Resources

| URI                    | Content                            |
| ---------------------- | ---------------------------------- |
| `schema://database`    | Complete schema with relationships |
| `config://tools`       | Tool catalog and usage guide       |
| `samples://queries`    | Example SQL patterns               |
| `guide://usage`        | This usage guide                   |
| `context://connection` | Database connection info           |
