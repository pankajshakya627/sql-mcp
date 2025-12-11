"""
🗄️ SQL MCP Server - Streamlit UI
Interactive web interface for database queries and exploration.

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

# Import tools
from tools.database import (
    query_database,
    query_database_raw,
    get_employees,
    get_departments,
    get_database_schema,
    DB_AVAILABLE
)
from tools.sql_generator import generate_sql_query, validate_sql_syntax
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
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    .main-header {
        font-size: 2.5rem;
        background: linear-gradient(90deg, #00d2ff, #3a7bd5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .status-connected {
        background: #10b981;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
    }
    .status-disconnected {
        background: #ef4444;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
    }
    .sql-box {
        background: #1e1e1e;
        border-radius: 10px;
        padding: 1rem;
        font-family: 'Fira Code', monospace;
    }
</style>
""", unsafe_allow_html=True)


def main():
    # Header
    st.markdown('<p class="main-header">🗄️ SQL MCP Server</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Connection status
        if DB_AVAILABLE:
            st.success("✅ Database Connected")
            db_url = os.environ.get("DATABASE_URL", "")
            if db_url:
                host = db_url.split("@")[1].split("/")[0] if "@" in db_url else "Local"
                st.caption(f"Host: {host}")
        else:
            st.warning("⚠️ Static Mode (No Database)")
            st.caption("Set DATABASE_URL to connect")
        
        st.divider()
        
        # Navigation using selectbox for better visibility
        st.header("🧭 Navigation")
        page = st.selectbox(
            "Select Page",
            options=[
                "🔍 Query Database",
                "📊 Explore Schema", 
                "🤖 AI SQL Generator",
                "📄 Paginated Results"
            ],
            index=0
        )
        
        st.divider()
        
        # Quick links
        st.header("🔗 Quick Actions")
        if st.button("📋 View Schema", use_container_width=True):
            st.session_state.page = "📊 Explore Schema"
            st.rerun()
        if st.button("🚀 Run Query", use_container_width=True):
            st.session_state.page = "🔍 Query Database"
            st.rerun()
    
    # Main content based on page
    if "Query Database" in page:
        query_page()
    elif "Explore Schema" in page:
        schema_page()
    elif "AI SQL Generator" in page:
        ai_generator_page()
    elif "Paginated Results" in page:
        pagination_page()


def query_page():
    """SQL Query execution page."""
    st.header("🔍 Execute SQL Query")
    
    # Query input
    query = st.text_area(
        "Enter SQL Query",
        value="SELECT * FROM employee LIMIT 10",
        height=150,
        placeholder="Enter your SELECT query here..."
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        execute = st.button("▶️ Execute", type="primary", use_container_width=True)
    with col2:
        validate = st.button("✅ Validate Syntax", use_container_width=True)
    
    if validate:
        result = validate_sql_syntax(query)
        if "valid" in result.lower():
            st.success(result)
        else:
            st.error(result)
    
    if execute:
        with st.spinner("Executing query..."):
            result = query_database(query)
            st.markdown("### Results")
            st.markdown(result)


def schema_page():
    """Database schema exploration page."""
    st.header("📊 Database Schema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Schema Overview")
        schema = get_database_schema()
        st.code(schema, language="markdown")
    
    with col2:
        st.subheader("🔎 Table Details")
        
        table = st.selectbox(
            "Select Table",
            ["department", "role", "employee", "project"]
        )
        
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
                    st.info("Table info not available in static mode")
    
    st.divider()
    
    # Quick data preview
    st.subheader("👀 Quick Data Preview")
    
    preview_table = st.selectbox(
        "Select table to preview",
        ["employee", "department", "role", "project"],
        key="preview_table"
    )
    
    if st.button("📊 Show Preview"):
        if preview_table == "employee":
            st.markdown(get_employees())
        elif preview_table == "department":
            st.markdown(get_departments())
        else:
            result = query_database(f"SELECT * FROM {preview_table} LIMIT 10")
            st.markdown(result)


def ai_generator_page():
    """AI-powered SQL generation page."""
    st.header("🤖 AI SQL Generator")
    
    st.info("💡 Describe what you want in natural language, and AI will generate the SQL query.")
    
    question = st.text_input(
        "What do you want to know?",
        placeholder="e.g., Show me all employees in the Engineering department"
    )
    
    if st.button("🪄 Generate SQL", type="primary"):
        if question:
            with st.spinner("Generating SQL..."):
                result = generate_sql_query(question)
                
                st.subheader("Generated SQL")
                st.code(result, language="sql")
                
                # Option to execute
                if st.button("▶️ Execute Generated Query"):
                    with st.spinner("Executing..."):
                        exec_result = query_database(result)
                        st.markdown("### Results")
                        st.markdown(exec_result)
        else:
            st.warning("Please enter a question first")
    
    st.divider()
    
    # Example questions
    st.subheader("💡 Example Questions")
    examples = [
        "How many employees are in each department?",
        "List all active projects",
        "Show employees with their roles and departments",
        "What is the average salary range by role?",
        "Find all employees hired this year"
    ]
    
    for example in examples:
        if st.button(f"📝 {example}", key=example):
            st.session_state.question = example
            st.rerun()


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
                # Create session
                session = session_store.create_session(query, results, page_size)
                st.session_state.pagination_session = session.session_id
                st.success(f"Session created: {session.session_id} ({len(results)} total rows)")
    
    # Display paginated results
    if "pagination_session" in st.session_state:
        session_id = st.session_state.pagination_session
        session = session_store.get_session(session_id)
        
        if session:
            st.divider()
            
            # Navigation
            col1, col2, col3, col4 = st.columns([1, 1, 2, 1])
            
            with col1:
                if st.button("⬅️ Previous", disabled=session.current_page <= 1):
                    session.prev_page()
                    st.rerun()
            
            with col2:
                if st.button("➡️ Next", disabled=session.current_page >= session.total_pages):
                    session.next_page()
                    st.rerun()
            
            with col3:
                st.write(f"Page {session.current_page} of {session.total_pages} ({session.total_rows} total rows)")
            
            with col4:
                if st.button("🗑️ Clear Session"):
                    session_store.delete_session(session_id)
                    del st.session_state.pagination_session
                    st.rerun()
            
            # Display data
            page_data = session.get_page()
            if page_data["data"]:
                st.dataframe(page_data["data"], use_container_width=True)
        else:
            st.warning("Session expired. Please run the query again.")
            del st.session_state.pagination_session


if __name__ == "__main__":
    main()
