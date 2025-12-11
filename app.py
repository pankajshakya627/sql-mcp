"""
🗄️ SQL MCP Server - Streamlit UI
Interactive web interface for database queries and exploration.
Exposes ALL functionality from main.py MCP server.

Run with: streamlit run app.py
"""
import os
import sys
import streamlit as st
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

# Load environment variables
load_dotenv()

# Import ALL tools from database module
from tools.database import (
    query_database,
    query_database_raw,
    get_employees,
    get_departments,
    get_database_schema,
    DB_AVAILABLE
)
from tools.sql_generator import (
    generate_sql_query,
    validate_sql_syntax,
    get_query_optimization_tips
)
from tools.session_store import session_store

# Page configuration
st.set_page_config(
    page_title="SQL MCP Server",
    page_icon="🗄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        background: linear-gradient(90deg, #00d2ff, #3a7bd5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .tool-card {
        background: rgba(255,255,255,0.05);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


def get_db_connection():
    """Get database connection with dynamic configuration."""
    db_type = st.session_state.get("database_type", "static")
    
    if db_type == "sqlite":
        try:
            from tools.sqlite_local import get_sqlite_connection
            conn = get_sqlite_connection()
            return conn, "SQLite Connected"
        except Exception as e:
            return None, str(e)
    
    elif db_type == "postgresql":
        try:
            import psycopg
            from psycopg.rows import dict_row
            db_url = st.session_state.get("database_url") or os.environ.get("DATABASE_URL", "")
            if not db_url:
                return None, "No connection string provided"
            conn = psycopg.connect(db_url, row_factory=dict_row)
            return conn, "PostgreSQL Connected"
        except Exception as e:
            return None, str(e)
    
    return None, "Static mode - no live connection"


def execute_query_dynamic(query: str):
    """Execute query using the selected database type."""
    db_type = st.session_state.get("database_type", "static")
    
    # Static mode - use original functions
    if db_type == "static":
        return query_database(query)
    
    # SQLite mode
    if db_type == "sqlite":
        try:
            from tools.sqlite_local import query_sqlite
            results = query_sqlite(query)
            
            if isinstance(results, str):  # Error message
                return results
            
            if not results:
                return "*No results found*"
            
            # Format as table
            headers = list(results[0].keys())
            table = "| " + " | ".join(str(h) for h in headers) + " |\n"
            table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
            
            for row in results[:50]:
                values = [str(row.get(h, ""))[:40] for h in headers]
                table += "| " + " | ".join(values) + " |\n"
            
            if len(results) > 50:
                table += f"\n*Showing 50 of {len(results)} rows*"
            else:
                table += f"\n*Total: {len(results)} rows*"
            
            return table
        except Exception as e:
            return f"❌ SQLite Error: {e}"
    
    # PostgreSQL mode
    if db_type == "postgresql":
        db_url = st.session_state.get("database_url") or os.environ.get("DATABASE_URL", "")
        
        if not db_url:
            return "❌ No DATABASE_URL configured"
        
        try:
            import psycopg
            from psycopg.rows import dict_row
            
            with psycopg.connect(db_url, row_factory=dict_row) as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    results = cur.fetchall()
                    
                    if not results:
                        return "*No results found*"
                    
                    # Format as table
                    headers = list(results[0].keys())
                    table = "| " + " | ".join(str(h) for h in headers) + " |\n"
                    table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
                    
                    for row in results[:50]:
                        values = [str(row.get(h, ""))[:40] for h in headers]
                        table += "| " + " | ".join(values) + " |\n"
                    
                    if len(results) > 50:
                        table += f"\n*Showing 50 of {len(results)} rows*"
                    else:
                        table += f"\n*Total: {len(results)} rows*"
                    
                    return table
        except Exception as e:
            return f"❌ PostgreSQL Error: {e}"
    
    return "❌ Unknown database type"


def main():
    # Header
    st.markdown('<p class="main-header">🗄️ SQL MCP Server</p>', unsafe_allow_html=True)
    
    # Initialize session state
    if "database_url" not in st.session_state:
        st.session_state.database_url = os.environ.get("DATABASE_URL", "")
    if "database_type" not in st.session_state:
        # Check environment for database type
        if os.environ.get("DATABASE_TYPE", "").lower() == "sqlite":
            st.session_state.database_type = "sqlite"
        elif os.environ.get("DATABASE_URL"):
            st.session_state.database_type = "postgresql"
        else:
            st.session_state.database_type = "static"
    
    # Sidebar
    with st.sidebar:
        st.header("🔌 Database Connection")
        
        # Connection mode
        connection_mode = st.radio(
            "Connection Mode",
            [
                "🌐 PostgreSQL (Neon/Cloud)",
                "💾 SQLite (Local File)",
                "📄 Static Mode (Demo)"
            ],
            index={"postgresql": 0, "sqlite": 1, "static": 2}.get(st.session_state.database_type, 2)
        )
        
        # Update database type based on selection
        if "PostgreSQL" in connection_mode:
            st.session_state.database_type = "postgresql"
        elif "SQLite" in connection_mode:
            st.session_state.database_type = "sqlite"
        else:
            st.session_state.database_type = "static"
        
        # PostgreSQL configuration
        if st.session_state.database_type == "postgresql":
            st.markdown("### 🌐 PostgreSQL Connection")
            
            # Check if .env has a URL
            env_url = os.environ.get("DATABASE_URL", "")
            
            if env_url:
                st.success("✅ Found in .env")
                use_env = st.checkbox("Use .env connection", value=True)
                if use_env:
                    st.session_state.database_url = env_url
                    if "@" in env_url:
                        host = env_url.split("@")[1].split("/")[0]
                        st.caption(f"Host: {host}")
            
            # Manual input
            with st.expander("🔧 Enter Connection String"):
                manual_url = st.text_input(
                    "PostgreSQL URL",
                    placeholder="postgresql://user:pass@host/dbname?sslmode=require",
                    type="password"
                )
                if manual_url:
                    st.session_state.database_url = manual_url
                
                st.caption("Example: `postgresql://user:password@ep-xxx.neon.tech/dbname?sslmode=require`")
            
            # Test connection
            if st.button("🔌 Test Connection"):
                conn, status = get_db_connection()
                if conn:
                    st.success(f"✅ {status}")
                    conn.close()
                else:
                    st.error(f"❌ {status}")
        
        # SQLite configuration
        elif st.session_state.database_type == "sqlite":
            st.markdown("### 💾 SQLite Local Database")
            
            try:
                from tools.sqlite_local import get_sqlite_connection, sqlite_db_exists, get_sqlite_path
                
                db_path = get_sqlite_path()
                
                if sqlite_db_exists():
                    st.success("✅ Database exists")
                    st.caption(f"Path: `{db_path}`")
                else:
                    st.info("📦 Database will be created on first use")
                    st.caption(f"Path: `{db_path}`")
                
                if st.button("🔌 Initialize/Test SQLite"):
                    try:
                        conn = get_sqlite_connection()
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM employee")
                        count = cursor.fetchone()[0]
                        conn.close()
                        st.success(f"✅ Connected! {count} employees found")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                        
            except ImportError:
                st.error("❌ SQLite module not found")
        
        # Static mode
        else:
            st.info("📄 Using static demo data")
            st.caption("No database connection required")
        
        st.divider()
        
        # Navigation
        st.header("🧭 Navigation")
        page = st.selectbox(
            "Select Page",
            options=[
                "🏠 Dashboard",
                "🔍 Query Database",
                "🤖 AI SQL Generator",
                "📊 Schema Explorer",
                "📄 Paginated Results",
                "📈 Data Reports",
                "🛠️ Tools & Utilities",
                "⚙️ Database Status"
            ],
            index=0
        )
    
    # Route to page
    if "Dashboard" in page:
        dashboard_page()
    elif "Query Database" in page:
        query_page()
    elif "AI SQL Generator" in page:
        ai_generator_page()
    elif "Schema Explorer" in page:
        schema_page()
    elif "Paginated Results" in page:
        pagination_page()
    elif "Data Reports" in page:
        reports_page()
    elif "Tools & Utilities" in page:
        tools_page()
    elif "Database Status" in page:
        status_page()


def dashboard_page():
    """Dashboard with quick access to all features."""
    st.header("🏠 Dashboard")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🔌 Database", "Connected" if DB_AVAILABLE else "Static Mode")
    
    with col2:
        if DB_AVAILABLE:
            tables = query_database_raw("SELECT COUNT(*) as c FROM information_schema.tables WHERE table_schema='public'")
            count = tables[0]['c'] if tables else 4
        else:
            count = 4
        st.metric("📋 Tables", count)
    
    with col3:
        if DB_AVAILABLE:
            emp = query_database_raw("SELECT COUNT(*) as c FROM employee")
            emp_count = emp[0]['c'] if emp else "N/A"
        else:
            emp_count = "Sample"
        st.metric("👥 Employees", emp_count)
    
    with col4:
        st.metric("🔧 Tools", "20+")
    
    st.divider()
    
    # Quick actions
    st.subheader("⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🔍 Run Query")
        quick_query = st.text_input("Quick SQL", "SELECT * FROM employee LIMIT 5", key="dash_query")
        if st.button("▶️ Execute", key="dash_exec"):
            result = execute_query_dynamic(quick_query)
            st.markdown(result)
    
    with col2:
        st.markdown("### 🤖 Ask AI")
        question = st.text_input("Ask in English", "How many employees?", key="dash_ai")
        if st.button("🪄 Generate SQL", key="dash_gen"):
            sql = generate_sql_query(question)
            st.code(sql, language="sql")
    
    with col3:
        st.markdown("### 📊 Quick View")
        table = st.selectbox("Select Table", ["employee", "department", "role", "project"], key="dash_table")
        if st.button("👁️ Preview", key="dash_preview"):
            result = execute_query_dynamic(f"SELECT * FROM {table} LIMIT 5")
            st.markdown(result)


def query_page():
    """SQL Query execution page."""
    st.header("🔍 Execute SQL Query")
    
    # Sample queries
    with st.expander("📚 Sample Queries"):
        samples = {
            "All Employees": "SELECT * FROM employee LIMIT 50",
            "Employee Count by Dept": "SELECT d.name, COUNT(*) as count FROM employee e JOIN department d ON e.department_id = d.id GROUP BY d.name",
            "Active Projects": "SELECT * FROM project WHERE status = 'Active'",
            "Employees with Roles": "SELECT e.name, r.title FROM employee e JOIN role r ON e.role_id = r.id"
        }
        for name, sql in samples.items():
            if st.button(f"📝 {name}", key=f"sample_{name}"):
                st.session_state.query = sql
    
    # Query input
    query = st.text_area(
        "Enter SQL Query",
        value=st.session_state.get("query", "SELECT * FROM employee LIMIT 10"),
        height=150
    )
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        execute = st.button("▶️ Execute", type="primary", use_container_width=True)
    with col2:
        validate = st.button("✅ Validate", use_container_width=True)
    with col3:
        if st.button("💡 Get Tips", use_container_width=True):
            tips = get_query_optimization_tips(query)
            st.info(tips)
    
    if validate:
        result = validate_sql_syntax(query)
        if "valid" in result.lower() or "✅" in result:
            st.success(result)
        else:
            st.error(result)
    
    if execute:
        with st.spinner("Executing query..."):
            result = execute_query_dynamic(query)
            st.markdown("### Results")
            st.markdown(result)


def ai_generator_page():
    """AI-powered SQL generation page."""
    st.header("🤖 AI SQL Generator")
    
    st.info("💡 Describe what you want in natural language, and AI will generate the SQL query.")
    
    # Question input
    question = st.text_area(
        "What do you want to know?",
        placeholder="e.g., Show me all employees in the Engineering department who were hired this year",
        height=100
    )
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("🪄 Generate SQL", type="primary", use_container_width=True):
            if question:
                with st.spinner("Generating SQL..."):
                    result = generate_sql_query(question)
                    st.session_state.generated_sql = result
            else:
                st.warning("Please enter a question first")
    
    with col2:
        if st.button("▶️ Generate & Execute", use_container_width=True):
            if question:
                with st.spinner("Generating and executing..."):
                    sql = generate_sql_query(question)
                    st.code(sql, language="sql")
                    result = execute_query_dynamic(sql)
                    st.markdown("### Results")
                    st.markdown(result)
    
    # Show generated SQL
    if "generated_sql" in st.session_state:
        st.subheader("Generated SQL")
        st.code(st.session_state.generated_sql, language="sql")
        
        if st.button("▶️ Execute This Query"):
            result = execute_query_dynamic(st.session_state.generated_sql)
            st.markdown(result)
    
    st.divider()
    
    # Example questions
    st.subheader("💡 Example Questions")
    examples = [
        "How many employees are in each department?",
        "List all active projects with their departments",
        "Show employees with their roles and salaries",
        "Find departments with more than 5 employees",
        "Get the latest hired employees"
    ]
    
    cols = st.columns(2)
    for i, example in enumerate(examples):
        with cols[i % 2]:
            if st.button(f"📝 {example}", key=f"ex_{i}"):
                st.session_state.example_question = example
                st.rerun()


def schema_page():
    """Database schema exploration page."""
    st.header("📊 Schema Explorer")
    
    tab1, tab2, tab3 = st.tabs(["📋 Schema Overview", "🔎 Table Details", "👀 Data Preview"])
    
    with tab1:
        st.subheader("Database Schema")
        schema = get_database_schema()
        st.code(schema, language="markdown")
    
    with tab2:
        st.subheader("Table Information")
        
        # Table selection
        ALLOWED_TABLES = ["department", "role", "employee", "project"]
        table = st.selectbox("Select Table", ALLOWED_TABLES)
        
        if st.button("🔍 Get Table Info"):
            with st.spinner("Fetching table info..."):
                query = f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = '{table}'
                    ORDER BY ordinal_position;
                """
                columns = query_database_raw(query)
                
                if columns:
                    st.dataframe(columns, use_container_width=True)
                    
                    # Row count
                    count_result = query_database_raw(f"SELECT COUNT(*) as count FROM {table}")
                    if count_result:
                        st.metric("Total Rows", count_result[0]['count'])
                else:
                    st.info("Using static schema (database not connected)")
                    static_schema = {
                        "department": ["id (int)", "name (varchar)", "location (varchar)"],
                        "role": ["id (int)", "title (varchar)", "salary_range (varchar)"],
                        "employee": ["id (int)", "name (varchar)", "email (varchar)", "department_id (int)", "role_id (int)"],
                        "project": ["id (int)", "name (varchar)", "description (text)", "department_id (int)"]
                    }
                    for col in static_schema.get(table, []):
                        st.write(f"• {col}")
    
    with tab3:
        st.subheader("Data Preview")
        
        preview_table = st.selectbox("Select table to preview", ALLOWED_TABLES, key="preview_sel")
        preview_limit = st.slider("Number of rows", 5, 50, 10)
        
        if st.button("📊 Show Preview"):
            result = execute_query_dynamic(f"SELECT * FROM {preview_table} LIMIT {preview_limit}")
            st.markdown(result)


def pagination_page():
    """Paginated results page."""
    st.header("📄 Paginated Query Results")
    
    st.info("Execute large queries and navigate through results page by page.")
    
    # Query input
    query = st.text_area(
        "SQL Query",
        value="SELECT * FROM employee",
        height=100
    )
    
    page_size = st.slider("Rows per page", 10, 50, 20)
    
    if st.button("🚀 Execute with Pagination", type="primary"):
        with st.spinner("Executing query..."):
            results = query_database_raw(query)
            
            if results:
                session = session_store.create_session(query, results, page_size)
                st.session_state.pagination_session = session.session_id
                st.success(f"✅ Session created: {session.session_id} ({len(results)} total rows)")
            else:
                st.warning("No results or database not available")
    
    # Display paginated results
    if "pagination_session" in st.session_state:
        session_id = st.session_state.pagination_session
        session = session_store.get_session(session_id)
        
        if session:
            st.divider()
            
            # Navigation
            col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 2, 1])
            
            with col1:
                if st.button("⏮️ First", disabled=session.current_page <= 1):
                    session.get_page(1)
                    st.rerun()
            
            with col2:
                if st.button("⬅️ Prev", disabled=session.current_page <= 1):
                    session.prev_page()
                    st.rerun()
            
            with col3:
                if st.button("➡️ Next", disabled=session.current_page >= session.total_pages):
                    session.next_page()
                    st.rerun()
            
            with col4:
                st.write(f"Page {session.current_page} of {session.total_pages} ({session.total_rows} rows)")
            
            with col5:
                if st.button("🗑️ Clear"):
                    session_store.delete_session(session_id)
                    del st.session_state.pagination_session
                    st.rerun()
            
            # Jump to page
            go_page = st.number_input("Go to page", 1, session.total_pages, session.current_page)
            if go_page != session.current_page:
                session.get_page(go_page)
                st.rerun()
            
            # Display data
            page_data = session.get_page()
            if page_data["data"]:
                st.dataframe(page_data["data"], use_container_width=True)
        else:
            st.warning("Session expired. Please run the query again.")
            del st.session_state.pagination_session


def reports_page():
    """Pre-built data reports."""
    st.header("📈 Data Reports")
    
    report = st.selectbox(
        "Select Report",
        [
            "👥 Employee Summary",
            "🏢 Department Overview",
            "📊 Role Distribution",
            "🗂️ Project Status",
            "📋 Full Database Summary"
        ]
    )
    
    if st.button("📊 Generate Report", type="primary"):
        with st.spinner("Generating report..."):
            if "Employee Summary" in report:
                st.subheader("👥 Employee Summary")
                
                # Total employees
                st.markdown(get_employees())
                
                # By department
                dept_query = """
                    SELECT d.name as Department, COUNT(*) as Employees
                    FROM employee e JOIN department d ON e.department_id = d.id
                    GROUP BY d.name ORDER BY Employees DESC
                """
                st.markdown("### By Department")
                st.markdown(execute_query_dynamic(dept_query))
            
            elif "Department Overview" in report:
                st.subheader("🏢 Department Overview")
                st.markdown(get_departments())
                
                # Projects per department
                proj_query = """
                    SELECT d.name as Department, COUNT(p.id) as Projects
                    FROM department d LEFT JOIN project p ON d.id = p.department_id
                    GROUP BY d.name
                """
                st.markdown("### Projects per Department")
                st.markdown(execute_query_dynamic(proj_query))
            
            elif "Role Distribution" in report:
                st.subheader("📊 Role Distribution")
                role_query = """
                    SELECT r.title as Role, r.salary_range, COUNT(e.id) as Employees
                    FROM role r LEFT JOIN employee e ON r.id = e.role_id
                    GROUP BY r.title, r.salary_range
                """
                st.markdown(execute_query_dynamic(role_query))
            
            elif "Project Status" in report:
                st.subheader("🗂️ Project Status")
                proj_query = "SELECT name, description, status FROM project ORDER BY status"
                st.markdown(execute_query_dynamic(proj_query))
            
            elif "Full Database" in report:
                st.subheader("📋 Full Database Summary")
                
                st.markdown("### Tables")
                tables_query = """
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                """
                st.markdown(execute_query_dynamic(tables_query))
                
                st.markdown("### Schema")
                st.code(get_database_schema(), language="markdown")


def tools_page():
    """Utility tools page."""
    st.header("🛠️ Tools & Utilities")
    
    tab1, tab2, tab3 = st.tabs(["✅ SQL Validator", "💡 Optimization Tips", "📋 List Tables"])
    
    with tab1:
        st.subheader("SQL Syntax Validator")
        sql_to_validate = st.text_area("Enter SQL to validate", height=100, key="val_sql")
        
        if st.button("✅ Validate SQL"):
            if sql_to_validate:
                result = validate_sql_syntax(sql_to_validate)
                if "valid" in result.lower() or "✅" in result:
                    st.success(result)
                else:
                    st.error(result)
    
    with tab2:
        st.subheader("Query Optimization Tips")
        sql_to_optimize = st.text_area("Enter SQL for optimization tips", height=100, key="opt_sql")
        
        if st.button("💡 Get Tips"):
            if sql_to_optimize:
                tips = get_query_optimization_tips(sql_to_optimize)
                st.info(tips)
    
    with tab3:
        st.subheader("Database Tables")
        
        if st.button("📋 List All Tables"):
            tables_query = """
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """
            tables = query_database_raw(tables_query)
            
            if tables:
                for t in tables:
                    table_name = t['table_name']
                    count_result = query_database_raw(f"SELECT COUNT(*) as c FROM {table_name}")
                    count = count_result[0]['c'] if count_result else "?"
                    st.write(f"📋 **{table_name}** - {count} rows")
            else:
                st.write("📋 department, employee, role, project (static mode)")


def status_page():
    """Database connection status page."""
    st.header("⚙️ Database Status")
    
    # Connection info
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Connection Status")
        
        if DB_AVAILABLE:
            st.success("✅ Database Connected")
        else:
            st.warning("⚠️ Running in Static Mode")
        
        # Environment info
        st.markdown("### Environment")
        st.write(f"**STATIC_SCHEMA_MODE:** {os.environ.get('STATIC_SCHEMA_MODE', 'true')}")
        
        db_url = os.environ.get("DATABASE_URL", "")
        if db_url:
            # Mask password
            masked = db_url.split("@")[0].split(":")[0] + ":****@" + db_url.split("@")[1] if "@" in db_url else "Configured"
            st.write(f"**DATABASE_URL:** {masked}")
        else:
            st.write("**DATABASE_URL:** Not set")
    
    with col2:
        st.subheader("Test Connection")
        
        if st.button("🔌 Test Database Connection"):
            if DB_AVAILABLE:
                try:
                    result = query_database_raw("SELECT 1 as test")
                    if result:
                        st.success("✅ Connection successful!")
                        st.json({"status": "connected", "test": result[0]})
                except Exception as e:
                    st.error(f"❌ Connection failed: {e}")
            else:
                st.info("Database not configured. Running in static mode.")
        
        if st.button("📊 Get Database Stats"):
            if DB_AVAILABLE:
                stats = {}
                for table in ["employee", "department", "role", "project"]:
                    try:
                        result = query_database_raw(f"SELECT COUNT(*) as c FROM {table}")
                        stats[table] = result[0]['c'] if result else 0
                    except:
                        stats[table] = "error"
                st.json(stats)
            else:
                st.json({"mode": "static", "tables": ["department", "role", "employee", "project"]})


if __name__ == "__main__":
    main()
