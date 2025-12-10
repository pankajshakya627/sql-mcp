"""
MCP Prompts for the DB Agent server.
Provides pre-built prompts for common database operations.
"""


def query_helper(question: str) -> str:
    """
    Generate a properly formatted prompt for asking database questions.
    Ensures the model uses the correct tool with proper context.
    """
    return f"""You are a SQL database assistant using the db-agent-mcp connector.

TASK: Answer this database question: "{question}"

INSTRUCTIONS:
1. Use ONLY the ask_database tool from the db-agent-mcp connector
2. Do NOT use web search or any other data sources
3. Present the results in a clear, formatted way
4. If the query fails, explain the error and suggest alternatives

Execute the query now."""


def schema_explorer() -> str:
    """
    Prompt for exploring and understanding the database schema.
    """
    return """You are exploring the organization database schema using the db-agent-mcp connector.

TASK: Analyze the database structure

INSTRUCTIONS:
1. First, call get_schema to retrieve the complete schema
2. Summarize the tables and their relationships
3. Identify primary and foreign key relationships
4. List the main entities and how they connect

Do NOT use any tools other than get_schema from db-agent-mcp.
Begin schema exploration now."""


def sql_generator_prompt(requirement: str) -> str:
    """
    Prompt for generating SQL without execution.
    Useful when you need to review the query before running.
    """
    return f"""You are a SQL query generator using the db-agent-mcp connector.

REQUIREMENT: {requirement}

INSTRUCTIONS:
1. Use ONLY the generate_sql_query tool from db-agent-mcp
2. The tool returns SQL only - it does NOT execute
3. After receiving the SQL, present it in a code block
4. Explain what the query does
5. Suggest any optimizations if applicable

IMPORTANT:
- Do NOT execute the query
- Do NOT use ask_database (that executes)
- Only use generate_sql_query

Generate the SQL now."""


def multi_step_analysis(analysis_goal: str) -> str:
    """
    Prompt for complex multi-step database analysis.
    Guides the model through a structured analysis workflow.
    """
    return f"""You are performing a multi-step database analysis using the db-agent-mcp connector.

ANALYSIS GOAL: {analysis_goal}

WORKFLOW (execute in order):
1. STEP 1 - Schema Discovery
   - Call get_schema to understand available tables
   - Note relevant tables for this analysis

2. STEP 2 - Query Planning
   - Based on schema, plan the SQL queries needed
   - Consider JOINs and aggregations required

3. STEP 3 - Data Retrieval
   - Use ask_database for each query
   - Collect and organize results

4. STEP 4 - Synthesis
   - Combine findings from all queries
   - Present insights and conclusions

RULES:
- Use ONLY db-agent-mcp connector tools
- Do NOT use web search or external tools
- Execute each step before moving to the next
- If a step fails, explain and attempt recovery

Begin Step 1 now."""


def comparison_query(entity1: str, entity2: str, metric: str) -> str:
    """
    Prompt for comparing two entities in the database.
    """
    return f"""You are comparing database entities using the db-agent-mcp connector.

COMPARISON:
- Entity 1: {entity1}
- Entity 2: {entity2}
- Metric: {metric}

INSTRUCTIONS:
1. Use ask_database to query data for {entity1}
2. Use ask_database to query data for {entity2}
3. Compare the {metric} between them
4. Present results in a comparison table
5. Provide analysis of the differences

RULES:
- Use ONLY ask_database from db-agent-mcp connector
- Do NOT invent data - only use query results
- If entities don't exist, report that clearly

Begin comparison now."""


def report_generator(report_type: str) -> str:
    """
    Prompt for generating database reports.
    Supports: employee_summary, department_overview, project_status
    """
    report_templates = {
        "employee_summary": """
REPORT: Employee Summary Report

QUERIES TO EXECUTE (use ask_database for each):
1. Total employee count
2. Employee count by department
3. Employee count by role
4. Recent hires (if hire_date available)

OUTPUT FORMAT:
- Executive summary paragraph
- Breakdown tables
- Key insights""",
        
        "department_overview": """
REPORT: Department Overview Report

QUERIES TO EXECUTE (use ask_database for each):
1. List all departments with locations
2. Employee count per department
3. Project count per department
4. Largest and smallest departments

OUTPUT FORMAT:
- Department summary table
- Resource allocation insights
- Recommendations""",
        
        "project_status": """
REPORT: Project Status Report

QUERIES TO EXECUTE (use ask_database for each):
1. Projects by status (Active, Completed, etc.)
2. Projects per department
3. Department with most active projects

OUTPUT FORMAT:
- Status distribution chart description
- Department workload analysis
- Recommendations"""
    }
    
    template = report_templates.get(report_type, f"""
REPORT: Custom Report - {report_type}

Analyze the database to generate a report on: {report_type}

Use ask_database to gather relevant data and present findings clearly.""")
    
    return f"""You are generating a database report using the db-agent-mcp connector.

{template}

RULES:
- Use ONLY ask_database from db-agent-mcp connector
- Present all data in formatted tables where appropriate
- Include insights and actionable recommendations
- Do NOT use external tools or web search

Begin report generation now."""
