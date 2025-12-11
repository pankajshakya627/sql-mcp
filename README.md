# 🗄️ SQL MCP Server

A powerful **Model Context Protocol (MCP)** server that enables ChatGPT and other LLM clients to interact with PostgreSQL databases using natural language. Now includes a beautiful **Streamlit Web UI** for direct database interaction!

[![FastMCP](https://img.shields.io/badge/FastMCP-Server-blue)](https://fastmcp.cloud)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![PostgreSQL](https://img.shields.io/badge/database-PostgreSQL-blue)](https://www.postgresql.org/)
[![SQLite](https://img.shields.io/badge/database-SQLite-green)](https://www.sqlite.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)](https://streamlit.io/)

---

## ✨ Features

- 🔍 **Natural Language Queries** - Ask questions in plain English, get SQL results
- 🎛️ **Streamlit Web UI** - Beautiful 8-page web interface for database exploration
- 📊 **Smart Pagination** - Navigate large datasets with session-based pagination
- � **SQLite Support** - Local SQLite database auto-created for offline development
- �🛡️ **Security First** - SQL injection prevention, read-only queries, table whitelists
- ⚡ **Real-time Data** - Connect to live PostgreSQL (Neon.tech supported)
- 📄 **Static Mode** - Works without database for demos and testing
- 🔧 **20+ MCP Tools** - Comprehensive toolset for database operations
- 🤖 **AI SQL Generator** - LLM-powered SQL generation with optimization tips
- 🔄 **PR-Agent Integration** - Automated code review via GitHub Actions

---

## 📁 Project Structure

```
sql-db-mcp/
├── main.py                    # 🚀 Main FastMCP server entry point
├── app.py                     # 🎛️ Streamlit Web UI
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker deployment config
├── docker-compose.yml         # Docker Compose for local dev
├── .env                       # Environment variables (create from .env.example)
├── .env.example               # Example environment configuration
│
├── src/                       # Source modules
│   ├── __init__.py
│   ├── schema.py              # Database schema definition
│   │
│   ├── tools/                 # MCP Tools
│   │   ├── __init__.py
│   │   ├── database.py        # Database connection & queries
│   │   ├── sql_generator.py   # LLM-powered SQL generation
│   │   ├── session_store.py   # Pagination session management
│   │   └── sqlite_local.py    # SQLite local database support
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
│   ├── local.db               # SQLite local database (auto-created)
│   ├── setup_db.sql           # Table creation & seed data
│   └── seed_data.py           # Generate large sample datasets
│
├── .github/workflows/         # CI/CD
│   └── pr-agent.yml           # PR-Agent automated code review
│
├── docs/                      # Documentation
│   ├── neon_setup.md          # Neon.tech setup guide
│   ├── security_audit.md      # Security review report
│   └── architecture.md        # System architecture
│
└── tests/                     # Unit tests
    └── __init__.py
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

Create `.env` file (or copy from `.env.example`):

```env
# OPTION 1: PostgreSQL (Neon.tech cloud)
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
STATIC_SCHEMA_MODE=false

# OPTION 2: SQLite Local Database (auto-creates db/local.db)
DATABASE_TYPE=sqlite

# OPTION 3: Static Mode (no database needed)
STATIC_SCHEMA_MODE=true

# LLM API (for AI SQL generation)
OPENROUTER_API_KEY=sk-or-v1-your-key-here
# OR
OPENAI_API_KEY=sk-your-key-here
```

### 3. Run Options

**MCP Server (for ChatGPT/Claude):**

```bash
python main.py
```

**Streamlit Web UI:**

```bash
streamlit run app.py
# Or with custom port:
streamlit run app.py --server.port 8090
```

---

## 🎛️ Streamlit Web UI

A beautiful 8-page web interface for database exploration:

| Page                     | Features                                                |
| ------------------------ | ------------------------------------------------------- |
| 🏠 **Dashboard**         | Quick stats, one-click queries, AI search, data preview |
| 🔍 **Query Database**    | Execute SQL, validate syntax, optimization tips         |
| 🤖 **AI SQL Generator**  | Natural language to SQL, generate & execute             |
| 📊 **Schema Explorer**   | Schema overview, table details, data preview            |
| 📄 **Paginated Results** | Large queries with page navigation                      |
| 📈 **Data Reports**      | Pre-built Employee, Department, Role, Project reports   |
| 🛠️ **Tools & Utilities** | SQL validator, optimization tips, list tables           |
| ⚙️ **Database Status**   | Connection test, environment info, stats                |

### Connection Modes

Switch between databases directly in the UI:

- 🌐 **PostgreSQL** - Connect to Neon.tech or any PostgreSQL
- 💾 **SQLite** - Use local `db/local.db` (auto-created with sample data)
- 📄 **Static** - Demo mode with no database required

---

## 🛠️ Available MCP Tools

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

| Tool                    | Description                                    |
| ----------------------- | ---------------------------------------------- |
| `validate_sql`          | Validate SQL syntax                            |
| `get_optimization_tips` | Get LLM-powered query optimization suggestions |

---

## � SQLite Local Database

For offline development, a local SQLite database is available:

```bash
# Enable SQLite in .env
DATABASE_TYPE=sqlite
```

The database (`db/local.db`) is auto-created with sample data:

- 10 employees
- 5 departments
- 9 roles
- 6 projects

---

## �💬 Usage Examples

### In ChatGPT (with MCP connector)

```
Use ask_database: "How many employees are in Engineering?"
```

```
Use paginated_query with "SELECT * FROM employee" and page_size 20
```

```
Use get_optimization_tips for my query "SELECT * FROM employee WHERE name LIKE '%john%'"
```

### Via Streamlit Web UI

1. Run `streamlit run app.py`
2. Select connection mode in sidebar (PostgreSQL/SQLite/Static)
3. Navigate to Query Database page
4. Enter SQL and click Execute

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

## 🤖 PR-Agent Integration

Automated code review on every PR using GitHub Actions:

```yaml
# .github/workflows/pr-agent.yml triggers on:
- pull_request: [opened, synchronize, reopened]
- workflow_dispatch: Manual trigger with options
```

**Available Actions:**

- `review` - Code review with issues and suggestions
- `describe` - Generate PR title and description
- `improve` - Code improvement suggestions
- `ask` - Answer questions about the PR
- `changelog` - Generate changelog entry
- `all` - Run all actions

**Setup:**

1. Add `PR_AGENT_PAT` secret with access to PR-AGENT repo
2. Add API keys: `GROQ_API_KEY`, `OPENROUTER_API_KEY`, etc.

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
        ChatGPT[ChatGPT]
        Claude[Claude Desktop]
        Inspector[MCP Inspector]
        StreamlitUI[Streamlit Web UI]
    end

    subgraph "MCP Server"
        FastMCP[FastMCP Server]
        Tools[20+ MCP Tools]
        Resources[MCP Resources]
        Sessions[Session Store]
    end

    subgraph "Data Layer"
        Neon[(Neon PostgreSQL)]
        SQLite[(SQLite Local)]
        Static[Static Schema Mode]
    end

    ChatGPT --> FastMCP
    Claude --> FastMCP
    Inspector --> FastMCP
    StreamlitUI --> Tools
    FastMCP --> Tools
    FastMCP --> Resources
    Tools --> Sessions
    Tools --> Neon
    Tools --> SQLite
    Tools --> Static
```

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

PR-Agent will automatically review your code!

---

## 📝 License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [FastMCP](https://fastmcp.cloud) - MCP server framework
- [Neon](https://neon.tech) - Serverless PostgreSQL
- [Streamlit](https://streamlit.io) - Web UI framework
- [LangChain](https://langchain.com) - LLM orchestration
- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent framework
