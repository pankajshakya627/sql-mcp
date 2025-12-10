from mcp.server.fastmcp import FastMCP
from sql_generator import get_database_schema
from database_schema import DATABASE_SCHEMA

# Initialize FastMCP server
mcp = FastMCP("text-to-sql")

# ============================================================================
# RESOURCES (Read-only data - more efficient than tools for static info)
# ============================================================================

@mcp.resource("schema://database")
def get_full_schema() -> str:
    """
    Complete database schema with all tables, columns, and relationships.
    URI: schema://database
    """
    return get_database_schema()


@mcp.resource("schema://tables")
def list_tables_resource() -> str:
    """
    List of all available tables.
    URI: schema://tables
    """
    return "Available tables: department, role, employee, project"


@mcp.resource("schema://table/{table_name}")
def get_table_schema(table_name: str) -> str:
    """
    Detailed schema for a specific table.
    URI: schema://table/{table_name}
    Example: schema://table/employee
    """
    table_schemas = {
        "department": """## Table: department
  - id: integer (NOT NULL, PRIMARY KEY)
  - name: varchar(100) (NOT NULL)
  - location: varchar(100) (NULL)

Referenced by:
  - employee.department_id
  - project.department_id""",
        
        "role": """## Table: role
  - id: integer (NOT NULL, PRIMARY KEY)
  - title: varchar(100) (NOT NULL)
  - salary_range: varchar(50) (NULL)

Referenced by:
  - employee.role_id""",
        
        "employee": """## Table: employee
  - id: integer (NOT NULL, PRIMARY KEY)
  - name: varchar(100) (NOT NULL)
  - email: varchar(100) (NULL, UNIQUE)
  - department_id: integer (NULL, FOREIGN KEY → department.id)
  - role_id: integer (NULL, FOREIGN KEY → role.id)
  - hire_date: date (NULL)

Foreign Keys:
  - department_id → department.id
  - role_id → role.id""",
        
        "project": """## Table: project
  - id: integer (NOT NULL, PRIMARY KEY)
  - name: varchar(100) (NOT NULL)
  - description: text (NULL)
  - department_id: integer (NULL, FOREIGN KEY → department.id)
  - status: varchar(20) (NULL, DEFAULT 'Active')

Foreign Keys:
  - department_id → department.id"""
    }
    
    if table_name.lower() in table_schemas:
        return table_schemas[table_name.lower()]
    else:
        return f"Table '{table_name}' not found. Available tables: department, role, employee, project"


@mcp.resource("examples://sql-queries")
def get_example_queries() -> str:
    """
    Example SQL queries for common patterns.
    URI: examples://sql-queries
    """
    return """# Sample SQL Queries

## Simple SELECT
-- List all employees
SELECT * FROM employee;

-- List all departments
SELECT id, name, location FROM department;

## JOINs
-- Get employees with their department names
SELECT e.name, e.email, d.name as department
FROM employee e
JOIN department d ON e.department_id = d.id;

-- Get employees with their roles and departments
SELECT e.name, r.title, d.name as department
FROM employee e
LEFT JOIN role r ON e.role_id = r.id
LEFT JOIN department d ON e.department_id = d.id;

## Aggregations
-- Count employees per department
SELECT d.name, COUNT(e.id) as employee_count
FROM department d
LEFT JOIN employee e ON d.id = e.department_id
GROUP BY d.id, d.name;

-- Count projects by status
SELECT status, COUNT(*) as count
FROM project
GROUP BY status;

## Filtering
-- Find employees in specific department
SELECT e.name, e.email
FROM employee e
JOIN department d ON e.department_id = d.id
WHERE d.name = 'Engineering';

-- Find projects for a department
SELECT p.name, p.description, p.status
FROM project p
JOIN department d ON p.department_id = d.id
WHERE d.name = 'Engineering';
"""


# ============================================================================
# TOOLS (For active operations like validation and optimization)
# ============================================================================

@mcp.tool()
def validate_sql_syntax(sql_query: str) -> str:
    """
    Validate SQL query syntax and get feedback.
    
    Args:
        sql_query: SQL query to validate
        
    Returns:
        Validation feedback and suggestions
    """
    issues = []
    suggestions = []
    
    sql_upper = sql_query.upper().strip()
    
    # Check if it's a SELECT query
    if not sql_upper.startswith("SELECT"):
        issues.append("⚠️  Query should start with SELECT for read-only operations")
    
    # Check for common issues
    if "FROM" not in sql_upper:
        issues.append("❌ Missing FROM clause")
    
    if sql_upper.count("(") != sql_upper.count(")"):
        issues.append("❌ Unmatched parentheses")
    
    # Check for table names
    valid_tables = ["department", "role", "employee", "project"]
    for table in valid_tables:
        if table.upper() in sql_upper:
            suggestions.append(f"✅ References table: {table}")
    
    # Check for JOINs
    if "JOIN" in sql_upper:
        if "ON" not in sql_upper:
            issues.append("⚠️  JOIN clause should have ON condition")
        suggestions.append("✅ Uses JOIN operation")
    
    # Check for semicolon
    if not sql_query.strip().endswith(";"):
        suggestions.append("💡 Consider ending query with semicolon (;)")
    
    result = "# SQL Validation Results\n\n"
    
    if not issues:
        result += "✅ No critical issues found!\n\n"
    else:
        result += "## Issues Found:\n"
        for issue in issues:
            result += f"  {issue}\n"
        result += "\n"
    
    if suggestions:
        result += "## Notes:\n"
        for suggestion in suggestions:
            result += f"  {suggestion}\n"
    
    return result


@mcp.tool()
def get_query_optimization_tips(sql_query: str) -> str:
    """
    Get optimization suggestions for a SQL query.
    
    Args:
        sql_query: SQL query to analyze
        
    Returns:
        Optimization suggestions
    """
    tips = ["# Query Optimization Tips\n"]
    
    sql_upper = sql_query.upper()
    
    # Check for SELECT *
    if "SELECT *" in sql_upper:
        tips.append("💡 Avoid SELECT * - Specify only needed columns for better performance")
    
    # Check for indexes on foreign keys
    if "JOIN" in sql_upper:
        tips.append("✅ Using JOINs - Ensure foreign key columns are indexed")
        tips.append("💡 Consider using table aliases (e.g., 'e' for employee) for readability")
    
    # Check for WHERE clause
    if "WHERE" in sql_upper:
        tips.append("✅ Using WHERE clause - Good for filtering")
        tips.append("💡 Ensure WHERE conditions use indexed columns when possible")
    
    # Check for aggregations
    if any(agg in sql_upper for agg in ["COUNT", "SUM", "AVG", "MAX", "MIN"]):
        tips.append("✅ Using aggregation functions")
        if "GROUP BY" not in sql_upper:
            tips.append("⚠️  Aggregation without GROUP BY - Verify this is intentional")
    
    # Check for LIMIT
    if "LIMIT" not in sql_upper and "SELECT" in sql_upper:
        tips.append("💡 Consider adding LIMIT for large result sets")
    
    # Check for DISTINCT
    if "DISTINCT" in sql_upper:
        tips.append("⚠️  DISTINCT can be expensive - Use only if necessary")
    
    if len(tips) == 1:
        tips.append("\n✅ Query looks well-optimized!")
    
    return "\n".join(tips)


if __name__ == "__main__":
    mcp.run()

