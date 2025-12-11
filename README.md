# 🗄️ SQL MCP Server

A powerful **Model Context Protocol (MCP)** server that enables ChatGPT and other LLM clients to interact with PostgreSQL databases using natural language.

[![FastMCP](https://img.shields.io/badge/FastMCP-Server-blue)](https://fastmcp.cloud)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PostgreSQL](https://img.shields.io/badge/database-PostgreSQL-blue)](https://www.postgresql.org/)

---

## ✨ Features

- 🔍 **Natural Language Queries** - Ask questions in plain English, get SQL results
- 📊 **Smart Pagination** - Navigate large datasets with session-based pagination
- 🛡️ **Security First** - SQL injection prevention, read-only queries, table whitelists
- ⚡ **Real-time Data** - Connect to live PostgreSQL (Neon.tech supported)
- 📄 **Static Mode** - Works without database for demos and testing
- 🔧 **20+ MCP Tools** - Comprehensive toolset for database operations

---

## 📁 Project Structure

```
sql-db-mcp/
├── main.py                    # 🚀 Main FastMCP server entry point
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker deployment config
├── docker-compose.yml         # Docker Compose for local dev
├── .env                       # Environment variables (create from .env.example)
│
├── src/                       # Source modules
│   ├── __init__.py
│   ├── schema.py              # Database schema definition
│   │
│   ├── tools/                 # MCP Tools
│   │   ├── __init__.py
│   │   ├── database.py        # Database connection & queries
│   │   ├── sql_generator.py   # LLM-powered SQL generation
│   │   └── session_store.py   # Pagination session management
│   │
│   ├── resources/             # MCP Resources
│   │   ├── __init__.py
│   │   └── catalog.py         # Schema, samples, guides
│   │
│   └── prompts/               # MCP Prompts
│       ├── __init__.py
│       └── templates.py       # Query templates
│
├── db/                        # Database scripts
│   ├── setup_db.sql           # Table creation & seed data
│   └── seed_data.py           # Generate large sample datasets
│
├── docs/                      # Documentation
│   ├── neon_setup.md          # Neon.tech setup guide
│   ├── security_audit.md      # Security review report
│   └── architecture.md        # System architecture
│
├── tests/                     # Unit tests
│   └── __init__.py
│
└── legacy/                    # Archived original files
    └── README.md
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/pankajshakya627/sql-mcp.git
cd sql-mcp
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file:

```env
# Database (use Neon.tech for cloud PostgreSQL)
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
STATIC_SCHEMA_MODE=false

# LLM API (for natural language SQL generation)
OPENROUTER_API_KEY=sk-or-v1-your-key-here
# OR
OPENAI_API_KEY=sk-your-key-here
```

### 3. Run Server

```bash
python main.py
```

Server starts on `http://localhost:8000`

---

## 🛠️ Available Tools

### Database Query Tools

| Tool                 | Description                                                   |
| -------------------- | ------------------------------------------------------------- |
| `ask_database`       | Smart query router - analyzes question and uses best approach |
| `execute_sql`        | Execute raw SQL SELECT queries                                |
| `run_query`          | Execute SQL with formatted table output                       |
| `generate_sql_query` | Generate SQL from natural language (without executing)        |

### Pagination Tools

| Tool              | Description                                                   |
| ----------------- | ------------------------------------------------------------- |
| `paginated_query` | Execute query with session-based pagination (20-50 rows/page) |
| `next_page`       | Get next page of results                                      |
| `prev_page`       | Get previous page of results                                  |
| `goto_page`       | Jump to specific page number                                  |
| `clear_session`   | Clear pagination session                                      |

### Schema & Info Tools

| Tool             | Description                               |
| ---------------- | ----------------------------------------- |
| `get_schema`     | Get full database schema                  |
| `get_table_info` | Get columns, types, row count for a table |
| `list_tables`    | List all tables with row counts           |
| `db_status`      | Check database connection status          |

### Data Tools

| Tool               | Description                                      |
| ------------------ | ------------------------------------------------ |
| `list_employees`   | List employees (with optional department filter) |
| `list_departments` | List all departments                             |

### Utility Tools

| Tool                    | Description                        |
| ----------------------- | ---------------------------------- |
| `validate_sql`          | Validate SQL syntax                |
| `get_optimization_tips` | Get query optimization suggestions |

---

## 💬 Usage Examples

### In ChatGPT (with MCP connector)

```
Use ask_database: "How many employees are in Engineering?"
```

```
Use paginated_query with "SELECT * FROM employee" and page_size 20
```

```
Use next_page with session_id "abc12345"
```

```
Use get_table_info for the "employee" table
```

### Via MCP Inspector

1. Open MCP Inspector at `http://localhost:6274`
2. Connect to `http://localhost:8000/mcp`
3. Browse and test available tools

---

## 🗃️ Database Schema

```sql
-- department: Organization departments
CREATE TABLE department (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(100)
);

-- role: Job roles with salary ranges
CREATE TABLE role (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    salary_range VARCHAR(50)
);

-- employee: Employee records
CREATE TABLE employee (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    department_id INTEGER REFERENCES department(id),
    role_id INTEGER REFERENCES role(id),
    hire_date DATE DEFAULT CURRENT_DATE
);

-- project: Active projects
CREATE TABLE project (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    department_id INTEGER REFERENCES department(id),
    status VARCHAR(20) DEFAULT 'Active'
);
```

---

## ☁️ Cloud Deployment

### Deploy to fastmcp.cloud

1. Push to GitHub
2. Connect repo at [fastmcp.cloud](https://fastmcp.cloud)
3. Add environment variables:
   - `DATABASE_URL`
   - `STATIC_SCHEMA_MODE=false`
   - `OPENROUTER_API_KEY`
4. Deploy

### Using Neon.tech for Database

See [docs/neon_setup.md](docs/neon_setup.md) for step-by-step guide.

---

## 🔒 Security

- ✅ **Read-only queries** - Only SELECT statements allowed
- ✅ **SQL injection prevention** - Table whitelist, input validation
- ✅ **Row limits** - Max 50 rows per query for performance
- ✅ **Session timeout** - Pagination sessions expire after 5 minutes
- ✅ **No credentials in code** - All secrets via environment variables

See [docs/security_audit.md](docs/security_audit.md) for full security review.

---

## 🐳 Docker

### Build & Run

```bash
docker build -t sql-mcp .
docker run -p 8000:8000 \
  -e DATABASE_URL="your_connection_string" \
  -e STATIC_SCHEMA_MODE=false \
  sql-mcp
```

### With Docker Compose

```bash
docker-compose up
```

---

## 📊 Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        ChatGPT[💬 ChatGPT]
        Claude[🤖 Claude Desktop]
        Inspector[🔍 MCP Inspector]
    end

    subgraph "MCP Server"
        FastMCP[🔌 FastMCP Server]
        Tools[🛠️ 20+ MCP Tools]
        Resources[📚 MCP Resources]
        Sessions[💾 Session Store]
    end

    subgraph "Data Layer"
        Neon([☁️ Neon PostgreSQL])
        Static[📄 Static Schema Mode]
    end

    % --- Connections ---
    ChatGPT --> FastMCP
    Claude --> FastMCP
    Inspector --> FastMCP
    FastMCP --> Tools
    FastMCP --> Resources
    Tools --> Sessions
    Tools --> Neon
    Tools --> Static

    % --- Styling for Clarity ---
    style "Client Layer" fill:#aff,stroke:#333,stroke-width:2px
    style "MCP Server" fill:#f9f,stroke:#333,stroke-width:2px
    style "Data Layer" fill:#faa,stroke:#333,stroke-width:2px

    % Optional: Style the Neon node as a cylinder (database)
    style Neon fill:#cff,shape:cylinder
```

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [FastMCP](https://fastmcp.cloud) - MCP server framework
- [Neon](https://neon.tech) - Serverless PostgreSQL
- [LangChain](https://langchain.com) - LLM orchestration
- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent framework
