"""
SQLite Local Database Module
Auto-creates and manages a local SQLite database for offline/development use.
"""
import os
import sqlite3
from pathlib import Path


# Database file path
DB_DIR = Path(__file__).parent.parent.parent / "db"
SQLITE_DB_PATH = DB_DIR / "local.db"


def get_sqlite_connection():
    """Get SQLite database connection, creating database if it doesn't exist."""
    # Ensure db directory exists
    DB_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check if database exists
    db_exists = SQLITE_DB_PATH.exists()
    
    # Connect (creates file if not exists)
    conn = sqlite3.connect(str(SQLITE_DB_PATH))
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    
    # If new database, initialize with schema and sample data
    if not db_exists:
        initialize_database(conn)
    
    return conn


def initialize_database(conn):
    """Create tables and insert sample data."""
    cursor = conn.cursor()
    
    # Create tables
    cursor.executescript("""
        -- Department table
        CREATE TABLE IF NOT EXISTS department (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            location TEXT
        );
        
        -- Role table
        CREATE TABLE IF NOT EXISTS role (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL UNIQUE,
            salary_range TEXT
        );
        
        -- Employee table
        CREATE TABLE IF NOT EXISTS employee (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            department_id INTEGER,
            role_id INTEGER,
            hire_date DATE,
            FOREIGN KEY (department_id) REFERENCES department(id),
            FOREIGN KEY (role_id) REFERENCES role(id)
        );
        
        -- Project table
        CREATE TABLE IF NOT EXISTS project (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            department_id INTEGER,
            status TEXT DEFAULT 'Active',
            FOREIGN KEY (department_id) REFERENCES department(id)
        );
    """)
    
    # Insert sample data
    cursor.executescript("""
        -- Departments
        INSERT OR IGNORE INTO department (name, location) VALUES 
            ('Engineering', 'Building A'),
            ('Human Resources', 'Building B'),
            ('Sales', 'Building C'),
            ('Marketing', 'Building D'),
            ('Finance', 'Building E');
        
        -- Roles
        INSERT OR IGNORE INTO role (title, salary_range) VALUES 
            ('Software Engineer', '$80,000 - $150,000'),
            ('Senior Engineer', '$120,000 - $200,000'),
            ('Engineering Manager', '$150,000 - $250,000'),
            ('HR Specialist', '$50,000 - $80,000'),
            ('HR Manager', '$80,000 - $120,000'),
            ('Sales Representative', '$45,000 - $100,000'),
            ('Sales Manager', '$90,000 - $150,000'),
            ('Marketing Specialist', '$55,000 - $90,000'),
            ('Financial Analyst', '$70,000 - $110,000');
        
        -- Employees
        INSERT OR IGNORE INTO employee (name, email, department_id, role_id, hire_date) VALUES 
            ('Alice Johnson', 'alice@company.com', 1, 1, '2022-01-15'),
            ('Bob Smith', 'bob@company.com', 1, 2, '2021-06-01'),
            ('Carol Williams', 'carol@company.com', 1, 3, '2020-03-20'),
            ('David Brown', 'david@company.com', 2, 4, '2022-08-10'),
            ('Emma Davis', 'emma@company.com', 2, 5, '2019-11-05'),
            ('Frank Miller', 'frank@company.com', 3, 6, '2023-02-14'),
            ('Grace Wilson', 'grace@company.com', 3, 7, '2021-09-30'),
            ('Henry Taylor', 'henry@company.com', 4, 8, '2022-05-22'),
            ('Ivy Thomas', 'ivy@company.com', 5, 9, '2021-12-01'),
            ('Jack Anderson', 'jack@company.com', 1, 1, '2023-07-01');
        
        -- Projects
        INSERT OR IGNORE INTO project (name, description, department_id, status) VALUES 
            ('Cloud Migration', 'Migrate infrastructure to cloud', 1, 'Active'),
            ('Mobile App v2', 'Next generation mobile application', 1, 'Active'),
            ('HR Portal', 'Employee self-service portal', 2, 'Completed'),
            ('Sales Dashboard', 'Real-time sales analytics', 3, 'Active'),
            ('Brand Refresh', 'Company rebranding initiative', 4, 'Planning'),
            ('Budget System', 'New budgeting software', 5, 'Active');
    """)
    
    conn.commit()
    print(f"✅ SQLite database initialized at: {SQLITE_DB_PATH}")


def query_sqlite(query: str):
    """Execute a query against the SQLite database."""
    try:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        
        # Fetch results
        results = cursor.fetchall()
        
        if not results:
            return []
        
        # Convert to list of dicts
        columns = [description[0] for description in cursor.description]
        data = [dict(zip(columns, row)) for row in results]
        
        conn.close()
        return data
    
    except Exception as e:
        return f"Error: {e}"


def get_sqlite_path():
    """Get the path to the SQLite database file."""
    return str(SQLITE_DB_PATH)


def sqlite_db_exists():
    """Check if the SQLite database exists."""
    return SQLITE_DB_PATH.exists()


# Auto-initialize on import if needed
if __name__ == "__main__":
    conn = get_sqlite_connection()
    print(f"Database ready at: {SQLITE_DB_PATH}")
    
    # Test query
    result = query_sqlite("SELECT * FROM employee LIMIT 3")
    print("\nSample employees:")
    for row in result:
        print(f"  - {row['name']} ({row['email']})")
    
    conn.close()
