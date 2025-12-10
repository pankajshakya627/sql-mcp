"""
SQL Generator for Text-to-SQL MCP Server.
Note: No LLM calls here - ChatGPT will use its own reasoning with the schema.
"""

from database_schema import get_schema


def get_database_schema():
    """Return the static database schema for SQL generation."""
    return get_schema()

