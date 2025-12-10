# Usage Guide

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Setup database
python -m db.setup_db

# Configure API key in .env
echo "OPENROUTER_API_KEY=your_key" > .env

# Run server
python -m src.main
```

## ChatGPT Developer Mode

### Enable

1. Settings → Apps & Connectors → Advanced → Developer Mode ON
2. Add connector with MCP server URL

### Effective Prompts

```
# Be explicit
Use db-agent-mcp's ask_database tool to find Engineering employees.

# Disallow alternatives
Do not use web search. Only use db-agent-mcp.

# Multi-step
First call get_schema, then generate_sql_query for department counts.
```

## Tools

| Tool                 | Purpose                        |
| -------------------- | ------------------------------ |
| `ask_database`       | Question → Answer (full agent) |
| `generate_sql_query` | Question → SQL (no execution)  |
| `execute_sql`        | Execute raw SQL                |
| `get_schema`         | Get DB structure               |
| `validate_sql`       | Check SQL syntax               |

## Resources

| URI                 | Content      |
| ------------------- | ------------ |
| `schema://database` | Full schema  |
| `config://tools`    | Tool catalog |
| `samples://queries` | Example SQL  |
| `guide://usage`     | This guide   |
