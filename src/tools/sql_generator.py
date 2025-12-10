"""
SQL generation tools using LLM for natural language to SQL conversion.
"""
import os
import sys
import re
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

# Handle both direct execution and package imports
try:
    from .database import get_database_schema
except ImportError:
    from database import get_database_schema

# Get schema - use static if live DB fails
try:
    from src.schema import DATABASE_SCHEMA
except ImportError:
    try:
        from schema import DATABASE_SCHEMA  
    except ImportError:
        DATABASE_SCHEMA = ""


def get_llm():
    """Get an LLM instance for SQL generation."""
    api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY or OPENAI_API_KEY environment variable not set.")
    
    return ChatOpenAI(
        model="x-ai/grok-4.1-fast:free",
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0
    )


def generate_sql_query(question: str) -> str:
    """
    Generate a SQL query based on a natural language question.
    This tool DOES NOT execute the query, it only returns the SQL code.
    
    Args:
        question: Natural language question about the database.
        
    Returns:
        Generated SQL query string.
    """
    # Check if LLM is available
    api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        # Provide helpful response without LLM
        schema = get_database_schema()
        return f"""⚠️ LLM API key not configured. Here's guidance for your query:

**Your Question:** {question}

**Available Tables:**
- employee (id, name, email, department_id, role_id, hire_date)
- department (id, name, location)
- role (id, title, salary_range)
- project (id, name, description, department_id, status)

**Common SQL Patterns:**

1. **List employees with departments:**
```sql
SELECT e.name, e.email, d.name as department
FROM employee e
JOIN department d ON e.department_id = d.id;
```

2. **Count by department:**
```sql
SELECT d.name, COUNT(e.id) as count
FROM department d
LEFT JOIN employee e ON d.id = e.department_id
GROUP BY d.name;
```

3. **Filter employees:**
```sql
SELECT * FROM employee WHERE name ILIKE '%search_term%';
```

4. **Active projects:**
```sql
SELECT p.name, d.name as department
FROM project p
JOIN department d ON p.department_id = d.id
WHERE p.status = 'Active';
```

Modify these patterns based on your needs!"""
    
    llm = get_llm()
    schema = get_database_schema()
    
    prompt_content = f"""You are an expert SQL generator.
    Database Schema:
    {schema}
    
    User Question: {question}
    
    CRITICAL RULES:
    1. Return ONLY the SQL query. No markdown, no explanations.
    2. YOU MUST USE 'ILIKE' for ALL string comparisons. DO NOT use '=' for strings.
    3. Check the 'Sample Data Context' in the schema.
    """
    
    messages = [HumanMessage(content=prompt_content)]
    response = llm.invoke(messages)
    sql = response.content.strip()
    
    # Fallback: Manually force ILIKE if the model fails
    if "=" in sql and "ILIKE" not in sql.upper():
        sys.stderr.write(f"[DEBUG] Regex Fallback Triggered! Original: {sql}\n")
        sql = re.sub(r"=\s*'([^']*)'", r"ILIKE '%\1%'", sql)
        sys.stderr.write(f"[DEBUG] Fixed SQL: {sql}\n")
        
    return sql


def validate_sql_syntax(sql_query: str) -> str:
    """
    Validate SQL query syntax and get feedback.
    
    Args:
        sql_query: SQL query to validate.
        
    Returns:
        Validation feedback and suggestions.
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


def get_query_optimization_tips(sql_query: str) -> str:
    """
    Get optimization suggestions for a SQL query.
    
    Args:
        sql_query: SQL query to analyze.
        
    Returns:
        Optimization suggestions.
    """
    tips = ["# Query Optimization Tips\n"]
    
    sql_upper = sql_query.upper()
    
    if "SELECT *" in sql_upper:
        tips.append("💡 Avoid SELECT * - Specify only needed columns for better performance")
    
    if "JOIN" in sql_upper:
        tips.append("✅ Using JOINs - Ensure foreign key columns are indexed")
        tips.append("💡 Consider using table aliases (e.g., 'e' for employee) for readability")
    
    if "WHERE" in sql_upper:
        tips.append("✅ Using WHERE clause - Good for filtering")
        tips.append("💡 Ensure WHERE conditions use indexed columns when possible")
    
    if any(agg in sql_upper for agg in ["COUNT", "SUM", "AVG", "MAX", "MIN"]):
        tips.append("✅ Using aggregation functions")
        if "GROUP BY" not in sql_upper:
            tips.append("⚠️  Aggregation without GROUP BY - Verify this is intentional")
    
    if "LIMIT" not in sql_upper and "SELECT" in sql_upper:
        tips.append("💡 Consider adding LIMIT for large result sets")
    
    if "DISTINCT" in sql_upper:
        tips.append("⚠️  DISTINCT can be expensive - Use only if necessary")
    
    if len(tips) == 1:
        tips.append("\n✅ Query looks well-optimized!")
    
    return "\n".join(tips)
