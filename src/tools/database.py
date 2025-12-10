"""
Database connection and query tools for the MCP server.
Supports both live database and static schema mode.
"""
import os
from typing import Optional, List, Dict, Any

# Check if we're in static schema mode (no live database)
STATIC_SCHEMA_MODE = os.environ.get("STATIC_SCHEMA_MODE", "true").lower() == "true"

# Try to import psycopg only if not in static mode
if not STATIC_SCHEMA_MODE:
    try:
        import psycopg
        from psycopg.rows import dict_row
        DB_AVAILABLE = True
    except ImportError:
        DB_AVAILABLE = False
else:
    DB_AVAILABLE = False

# Database connection string
DB_CONN_STRING = os.environ.get(
    "DATABASE_URL",
    "dbname=org_db user=pankajshakya host=localhost port=5432"
)


def get_connection():
    """Get a database connection."""
    if not DB_AVAILABLE:
        raise ConnectionError("Database not configured. Running in static schema mode.")
    
    try:
        return psycopg.connect(DB_CONN_STRING, row_factory=dict_row)
    except Exception as e:
        raise ConnectionError(f"Database connection failed: {e}")


def query_database(query: str) -> str:
    """
    Execute a read-only SQL query against the organization database.
    
    Returns error message if database is not configured.
    """
    if not DB_AVAILABLE:
        return ("⚠️ Database not configured - running in static schema mode.\n\n"
                "Use 'generate_sql_query' to create SQL, or 'get_schema' "
                "to view the database structure.\n\n"
                f"Generated query that would run:\n```sql\n{query}\n```")
    
    if not query.strip().upper().startswith("SELECT"):
        return "Error: Only SELECT queries are allowed."

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                results = cur.fetchall()
                return str(results)
    except Exception as e:
        return f"Error executing query: {e}"


def get_employees(department_id: Optional[int] = None) -> str:
    """Get a list of employees, optionally filtered by department."""
    if not DB_AVAILABLE:
        # Return sample data for demonstration
        return """⚠️ Database not configured - showing sample data:

| ID | Name | Email | Department | Role |
|----|------|-------|------------|------|
| 1 | Alice Smith | alice@org.com | Engineering | Senior Engineer |
| 2 | Bob Jones | bob@org.com | Engineering | Software Engineer |
| 3 | Charlie Brown | charlie@org.com | HR | HR Manager |
| 4 | Diana Prince | diana@org.com | Sales | Sales Representative |
| 5 | Evan Wright | evan@org.com | Marketing | Marketing Specialist |

*This is sample data. Connect a live database for real results.*"""
    
    query = """
        SELECT e.id, e.name, e.email, d.name as department, r.title as role
        FROM employee e
        JOIN department d ON e.department_id = d.id
        JOIN role r ON e.role_id = r.id
    """
    if department_id is not None:
        query += f" WHERE e.department_id = {department_id}"
    
    return query_database(query)


def get_departments() -> str:
    """List all departments."""
    if not DB_AVAILABLE:
        return """⚠️ Database not configured - showing sample data:

| ID | Name | Location |
|----|------|----------|
| 1 | Engineering | Building A |
| 2 | HR | Building B |
| 3 | Sales | Building C |
| 4 | Marketing | Building B |

*This is sample data. Connect a live database for real results.*"""
    
    return query_database("SELECT * FROM department")


def get_database_schema() -> str:
    """
    Get the database schema.
    Uses static schema when database is not available.
    """
    # Always use static schema for consistency
    try:
        from schema import DATABASE_SCHEMA
        return DATABASE_SCHEMA
    except ImportError:
        pass
    
    try:
        from src.schema import DATABASE_SCHEMA
        return DATABASE_SCHEMA
    except ImportError:
        pass
    
    # Fallback inline schema
    return """
# Database Schema

## Table: department
  - id: integer (PRIMARY KEY)
  - name: varchar(100)
  - location: varchar(100)

## Table: role
  - id: integer (PRIMARY KEY)
  - title: varchar(100)
  - salary_range: varchar(50)

## Table: employee
  - id: integer (PRIMARY KEY)
  - name: varchar(100)
  - email: varchar(100)
  - department_id: integer (FK → department.id)
  - role_id: integer (FK → role.id)
  - hire_date: date

## Table: project
  - id: integer (PRIMARY KEY)
  - name: varchar(100)
  - description: text
  - department_id: integer (FK → department.id)
  - status: varchar(20) DEFAULT 'Active'
"""
