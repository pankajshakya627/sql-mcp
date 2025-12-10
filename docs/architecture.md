# DB Agent MCP Architecture

## Overview

The DB Agent MCP is a FastMCP server that provides natural language database query capabilities using a LangGraph agent.

## Architecture Diagram

```mermaid
graph TB
    subgraph Client["MCP Client"]
        UI[ChatGPT/Claude]
    end

    subgraph Server["DB Agent MCP Server"]
        MCP[FastMCP]
        Tools[Tools]
        Resources[Resources]
        Prompts[Prompts]
        Agent[LangGraph Agent]
    end

    subgraph Database["PostgreSQL"]
        % Explicit cylinder shape
        DB([org_db])
        style DB fill:#f9f,shape:cylinder
    end

    UI --> MCP
    MCP --> Tools
    MCP --> Resources
    MCP --> Prompts
    Tools --> Agent
    Agent --> DB
```

## Components

| Component       | Location                     | Purpose                                      |
| --------------- | ---------------------------- | -------------------------------------------- |
| FastMCP Server  | `src/main.py`                | Entry point, exposes tools/resources/prompts |
| LangGraph Agent | `src/main.py`                | Multi-step query orchestration               |
| Database Tools  | `src/tools/database.py`      | Direct DB operations                         |
| SQL Generator   | `src/tools/sql_generator.py` | LLM-based SQL generation                     |
| Resources       | `src/resources/catalog.py`   | Schema, samples, guides                      |
| Prompts         | `src/prompts/templates.py`   | Pre-built prompt templates                   |

## Technology Stack

- **MCP Framework**: FastMCP
- **Agent Framework**: LangGraph + LangChain
- **LLM Provider**: OpenRouter (configurable)
- **Database**: PostgreSQL
- **Python**: 3.10+
