"""
Database connection and query tools for the MCP server.
"""
import psycopg
from psycopg.rows import dict_row
from typing import Optional, List, Dict, Any


# Database connection string - uses environment or defaults
DB_CONN_STRING = "dbname=org_db user=pankajshakya host=localhost port=5432"


def get_connection():
    """Get a database connection."""
    try:
        return psycopg.connect(DB_CONN_STRING, row_factory=dict_row)
    except psycopg.OperationalError:
        # Fallback for different user if needed
        return psycopg.connect(
            "dbname=org_db user=postgres host=localhost port=5432",
            row_factory=dict_row
        )


def query_database(query: str) -> List[Dict[str, Any]]:
    """
    Execute a read-only SQL query against the organization database.
    
    Args:
        query: The SQL query to execute. Must be a SELECT statement.
        
    Returns:
        List of dictionaries containing query results.
    """
    # Basic safety check - strictly read-only
    if not query.strip().upper().startswith("SELECT"):
        raise ValueError("Only SELECT queries are allowed.")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()


def get_employees(department_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Get a list of employees, optionally filtered by department.
    
    Args:
        department_id: Optional ID of the department to filter by.
        
    Returns:
        List of employee records with department and role info.
    """
    query = """
        SELECT e.id, e.name, e.email, d.name as department, r.title as role
        FROM employee e
        JOIN department d ON e.department_id = d.id
        JOIN role r ON e.role_id = r.id
    """
    params = []
    
    if department_id is not None:
        query += " WHERE e.department_id = %s"
        params.append(department_id)
        
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


def get_departments() -> List[Dict[str, Any]]:
    """List all departments."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM department")
            return cur.fetchall()


def get_database_schema() -> str:
    """
    Get the schema of the database from PostgreSQL information_schema.
    Useful for understanding the database structure before querying.
    
    Returns:
        Formatted string with table and column information.
    """
    schema_query = """
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(schema_query)
            rows = cur.fetchall()
            
    # Format as a readable string
    schema_str = ""
    current_table = ""
    for row in rows:
        if row['table_name'] != current_table:
            current_table = row['table_name']
            schema_str += f"\nTable: {current_table}\n"
        schema_str += f"  - {row['column_name']} ({row['data_type']})\n"
    
    return schema_str
