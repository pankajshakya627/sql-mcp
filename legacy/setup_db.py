import psycopg
from psycopg import sql
import sys

# Database connection parameters - adjust as needed for local setup
# Assuming default 'postgres' user and 'postgres' database exists to connect initially
DB_PARAMS = {
    "dbname": "postgres",
    "user": "pankajshakya", # Trying current user first, often default on Mac
    "host": "localhost",
    "port": "5432"
}

TARGET_DB = "org_db"

def create_database():
    try:
        # Connect to default database to create the new one
        conn = psycopg.connect(**DB_PARAMS, autocommit=True)
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (TARGET_DB,))
        if not cur.fetchone():
            print(f"Creating database {TARGET_DB}...")
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(TARGET_DB)))
        else:
            print(f"Database {TARGET_DB} already exists.")
        
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error creating database: {e}")
        # Fallback: try 'postgres' user if current user fails
        if DB_PARAMS["user"] != "postgres":
            print("Retrying with user 'postgres'...")
            DB_PARAMS["user"] = "postgres"
            return create_database()
        return False

def create_tables_and_seed():
    try:
        # Connect to the new database
        conn_params = DB_PARAMS.copy()
        conn_params["dbname"] = TARGET_DB
        conn = psycopg.connect(**conn_params)
        cur = conn.cursor()

        # Create tables
        print("Creating tables...")
        
        # Department Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS department (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                location VARCHAR(100)
            );
        """)

        # Role Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS role (
                id SERIAL PRIMARY KEY,
                title VARCHAR(100) NOT NULL,
                salary_range VARCHAR(50)
            );
        """)

        # Employee Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS employee (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE,
                department_id INTEGER REFERENCES department(id),
                role_id INTEGER REFERENCES role(id),
                hire_date DATE DEFAULT CURRENT_DATE
            );
        """)

        # Project Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS project (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                department_id INTEGER REFERENCES department(id),
                status VARCHAR(20) DEFAULT 'Active'
            );
        """)

        # Seed Data
        print("Seeding data...")
        
        # Check if data exists to avoid duplicates on re-run
        cur.execute("SELECT COUNT(*) FROM department")
        if cur.fetchone()[0] == 0:
            # Departments
            cur.execute("""
                INSERT INTO department (name, location) VALUES
                ('Engineering', 'Building A'),
                ('HR', 'Building B'),
                ('Sales', 'Building C'),
                ('Marketing', 'Building B');
            """)
            
            # Roles
            cur.execute("""
                INSERT INTO role (title, salary_range) VALUES
                ('Software Engineer', '80k-120k'),
                ('Senior Engineer', '120k-160k'),
                ('HR Manager', '70k-100k'),
                ('Sales Representative', '50k-80k + Commission'),
                ('Marketing Specialist', '60k-90k');
            """)
            
            # Employees
            cur.execute("""
                INSERT INTO employee (name, email, department_id, role_id) VALUES
                ('Alice Smith', 'alice@org.com', 1, 2),
                ('Bob Jones', 'bob@org.com', 1, 1),
                ('Charlie Brown', 'charlie@org.com', 2, 3),
                ('Diana Prince', 'diana@org.com', 3, 4),
                ('Evan Wright', 'evan@org.com', 4, 5);
            """)
            
            # Projects
            cur.execute("""
                INSERT INTO project (name, description, department_id) VALUES
                ('Project Alpha', 'Next gen platform', 1),
                ('Project Beta', 'Mobile app overhaul', 1),
                ('Recruitment Drive', 'Q4 Hiring', 2),
                ('Q4 Sales Push', 'End of year targets', 3);
            """)
            
            print("Data seeded successfully.")
        else:
            print("Data already exists, skipping seed.")

        conn.commit()
        cur.close()
        conn.close()
        print("Database setup complete.")
        
    except Exception as e:
        print(f"Error setting up tables/data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if create_database():
        create_tables_and_seed()
    else:
        print("Failed to ensure database exists.")
        sys.exit(1)
