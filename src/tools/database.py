"""
Database connection and query tools for the MCP server.

This module provides database connectivity and query execution for the SQL MCP server.
It supports both live PostgreSQL connections and a static schema mode for development.

Exports:
    DB_AVAILABLE (bool): Whether a live database connection is available
    query_database(query, page, page_size): Execute SQL and return formatted table
    query_database_raw(query): Execute SQL and return raw list of dicts
    get_employees(department_id): Get employee list with optional filtering
    get_departments(): Get all departments
    get_database_schema(): Get database schema description

Environment Variables:
    DATABASE_URL: PostgreSQL connection string
    STATIC_SCHEMA_MODE: Set to 'true' to use static schema without database
"""
import os
import logging
from typing import Optional, List, Dict, Any

# Configure logging
logger = logging.getLogger("db-agent-mcp.database")

# Check if we're in static schema mode (no live database)
STATIC_SCHEMA_MODE = os.environ.get("STATIC_SCHEMA_MODE", "true").lower() == "true"

# Get database URL from environment
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Try to import psycopg only if not in static mode and we have a DB URL
if not STATIC_SCHEMA_MODE and DATABASE_URL:
    try:
        import psycopg
        from psycopg.rows import dict_row
        DB_AVAILABLE = True
        logger.info(f"✅ Database configured: {DATABASE_URL[:30]}...")
    except ImportError:
        DB_AVAILABLE = False
        logger.error("❌ psycopg not installed")
else:
    DB_AVAILABLE = False
    if STATIC_SCHEMA_MODE:
        logger.info("ℹ️ Running in static schema mode")
    elif not DATABASE_URL:
        logger.warning("⚠️ DATABASE_URL not set")


def get_connection():
    """Get a database connection."""
    if not DB_AVAILABLE:
        logger.warning("Connection requested but database not available")
        raise ConnectionError("Database not configured. Running in static schema mode.")
    
    try:
        logger.debug("Establishing database connection...")
        conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
        logger.debug("Database connection established")
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise ConnectionError(f"Database connection failed: {e}")


def format_as_table(results: list, max_rows: int = 100) -> str:
    """Format query results as a markdown table with pagination info."""
    if not results:
        return "*No results found*"
    
    if not isinstance(results, list):
        return str(results)
    
    if not isinstance(results[0], dict):
        return str(results)
    
    headers = list(results[0].keys())
    total_rows = len(results)
    
    # Build table
    table = "| " + " | ".join(str(h) for h in headers) + " |\n"
    table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
    
    # Limit rows
    display_rows = results[:max_rows]
    for row in display_rows:
        values = [str(row.get(h, ""))[:50] for h in headers]  # Truncate long values
        table += "| " + " | ".join(values) + " |\n"
    
    # Add pagination info
    if total_rows > max_rows:
        table += f"\n*Showing {max_rows} of {total_rows} rows. Use LIMIT and OFFSET for pagination.*"
    else:
        table += f"\n*Total: {total_rows} rows*"
    
    return table


def query_database(query: str, page: int = 1, page_size: int = 50):
    """
    Execute a read-only SQL query against the organization database.
    
    Args:
        query: SQL SELECT query to execute
        page: Page number for pagination (1-indexed)
        page_size: Number of rows per page (max 50 for smooth ChatGPT performance)
    
    Returns:
        - Formatted table string when database is available
        - Error message when not configured or on error
    """
    MAX_ROWS = 50  # Hard limit for smooth ChatGPT Web performance
    
    if not DB_AVAILABLE:
        return ("⚠️ Database not configured - running in static schema mode.\n\n"
                "Use 'generate_sql_query' to create SQL, or 'get_schema' "
                "to view the database structure.\n\n"
                f"Generated query that would run:\n```sql\n{query}\n```")
    
    if not query.strip().upper().startswith("SELECT"):
        return "Error: Only SELECT queries are allowed."
    
    # Enforce max 50 rows limit
    page_size = min(page_size, MAX_ROWS)
    offset = (page - 1) * page_size

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # First get total count (if query doesn't already have LIMIT)
                total = None
                if "LIMIT" not in query.upper():
                    count_query = f"SELECT COUNT(*) as total FROM ({query}) subq"
                    cur.execute(count_query)
                    total = cur.fetchone()['total']
                    
                    # Add LIMIT to query for performance
                    paginated_query = f"{query} LIMIT {MAX_ROWS} OFFSET {offset}"
                    cur.execute(paginated_query)
                else:
                    cur.execute(query)
                
                results = cur.fetchall()
                
                # Format as table
                output = format_as_table(results, max_rows=MAX_ROWS)
                
                # Add pagination message if more data exists
                if total and total > MAX_ROWS:
                    output += f"\n\n📊 **Showing {min(MAX_ROWS, len(results))} of {total} total rows.**"
                    output += "\n� *For more results, use `paginated_query` tool which supports page navigation.*"
                
                return output
    except Exception as e:
        logger.error(f"Query error: {e}")
        return f"Error executing query: {e}"


def query_database_raw(query: str):
    """
    Execute query and return raw list of dicts (for internal use by other tools).
    """
    if not DB_AVAILABLE:
        return None
    
    if not query.strip().upper().startswith("SELECT"):
        return None

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                return cur.fetchall()
    except Exception:
        return None


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
    
    # Build query safely - department_id is validated as int by type hint
    if department_id is not None:
        # Validate that department_id is actually an integer
        if not isinstance(department_id, int) or department_id < 0:
            return "Error: Invalid department_id. Must be a positive integer."
        query = f"""
            SELECT e.id, e.name, e.email, d.name as department, r.title as role
            FROM employee e
            JOIN department d ON e.department_id = d.id
            JOIN role r ON e.role_id = r.id
            WHERE e.department_id = {int(department_id)}
            LIMIT 50
        """
    else:
        query = """
            SELECT e.id, e.name, e.email, d.name as department, r.title as role
            FROM employee e
            JOIN department d ON e.department_id = d.id
            JOIN role r ON e.role_id = r.id
            LIMIT 50
        """
    
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
