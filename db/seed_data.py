"""
Script to populate Neon database with random sample data.
- 500 departments
- 200 roles  
- 10000 employees
- 400 projects
"""
import os
import random
import string
import psycopg
from psycopg.rows import dict_row

# Neon connection string - MUST be set via environment variable
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("❌ Error: DATABASE_URL environment variable not set!")
    print("   Set it with: export DATABASE_URL='postgresql://...'")
    exit(1)

# Sample data generators
FIRST_NAMES = ["Alice", "Bob", "Charlie", "Diana", "Evan", "Fiona", "George", "Hannah", 
               "Ivan", "Julia", "Kevin", "Luna", "Mike", "Nina", "Oscar", "Priya",
               "Quinn", "Rachel", "Sam", "Tina", "Uma", "Victor", "Wendy", "Xavier", "Yuki", "Zara"]

LAST_NAMES = ["Smith", "Jones", "Brown", "Wilson", "Taylor", "Davis", "Miller", "Anderson",
              "Thomas", "Jackson", "White", "Harris", "Martin", "Garcia", "Martinez", "Robinson",
              "Clark", "Rodriguez", "Lewis", "Lee", "Walker", "Hall", "Allen", "Young", "King", "Wright"]

LOCATIONS = ["Building A", "Building B", "Building C", "Building D", "Building E",
             "Remote", "New York", "San Francisco", "London", "Tokyo", "Berlin", "Sydney"]

DEPT_PREFIXES = ["Engineering", "Sales", "Marketing", "HR", "Finance", "Operations", 
                 "Research", "Design", "Support", "Legal", "Product", "Data"]

ROLE_PREFIXES = ["Junior", "Senior", "Lead", "Principal", "Director", "VP", "Manager", "Associate"]
ROLE_TYPES = ["Engineer", "Analyst", "Designer", "Developer", "Specialist", "Coordinator", 
              "Consultant", "Administrator", "Strategist", "Architect"]

PROJECT_PREFIXES = ["Project", "Initiative", "Campaign", "Program", "Sprint", "Phase"]
PROJECT_STATUS = ["Active", "Completed", "On Hold", "Planning", "In Review"]


def random_email(name: str, domain_num: int) -> str:
    return f"{name.lower().replace(' ', '.')}{random.randint(1, 9999)}@company{domain_num}.com"


def random_salary_range() -> str:
    base = random.randint(4, 20) * 10
    return f"{base}k-{base + random.randint(10, 40)}k"


def main():
    print("Connecting to Neon database...")
    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    cur = conn.cursor()
    
    # Clear existing data
    print("Clearing existing data...")
    cur.execute("TRUNCATE employee, project, department, role RESTART IDENTITY CASCADE")
    conn.commit()
    
    # Insert 500 departments
    print("Inserting 500 departments...")
    departments = []
    for i in range(500):
        prefix = random.choice(DEPT_PREFIXES)
        name = f"{prefix} {random.choice(['Team', 'Division', 'Unit', 'Group'])} {i+1}"
        location = random.choice(LOCATIONS)
        departments.append((name, location))
    
    cur.executemany(
        "INSERT INTO department (name, location) VALUES (%s, %s)",
        departments
    )
    conn.commit()
    print(f"  ✓ Inserted {len(departments)} departments")
    
    # Insert 200 roles
    print("Inserting 200 roles...")
    roles = []
    for i in range(200):
        prefix = random.choice(ROLE_PREFIXES)
        role_type = random.choice(ROLE_TYPES)
        title = f"{prefix} {role_type}"
        salary = random_salary_range()
        roles.append((title, salary))
    
    cur.executemany(
        "INSERT INTO role (title, salary_range) VALUES (%s, %s)",
        roles
    )
    conn.commit()
    print(f"  ✓ Inserted {len(roles)} roles")
    
    # Insert 10000 employees
    print("Inserting 10000 employees (this may take a moment)...")
    employees = []
    for i in range(10000):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        name = f"{first} {last}"
        email = random_email(name, i % 100)
        dept_id = random.randint(1, 500)
        role_id = random.randint(1, 200)
        employees.append((name, email, dept_id, role_id))
        
        # Batch insert every 1000 rows
        if len(employees) >= 1000:
            cur.executemany(
                "INSERT INTO employee (name, email, department_id, role_id) VALUES (%s, %s, %s, %s)",
                employees
            )
            conn.commit()
            print(f"    ... {i+1} employees inserted")
            employees = []
    
    # Insert remaining
    if employees:
        cur.executemany(
            "INSERT INTO employee (name, email, department_id, role_id) VALUES (%s, %s, %s, %s)",
            employees
        )
        conn.commit()
    print(f"  ✓ Inserted 10000 employees")
    
    # Insert 400 projects
    print("Inserting 400 projects...")
    projects = []
    for i in range(400):
        prefix = random.choice(PROJECT_PREFIXES)
        name = f"{prefix} {''.join(random.choices(string.ascii_uppercase, k=3))}-{i+1}"
        description = f"Description for {name}"
        dept_id = random.randint(1, 500)
        status = random.choice(PROJECT_STATUS)
        projects.append((name, description, dept_id, status))
    
    cur.executemany(
        "INSERT INTO project (name, description, department_id, status) VALUES (%s, %s, %s, %s)",
        projects
    )
    conn.commit()
    print(f"  ✓ Inserted {len(projects)} projects")
    
    # Verify counts
    print("\n--- Verification ---")
    cur.execute("SELECT COUNT(*) as count FROM department")
    print(f"Departments: {cur.fetchone()['count']}")
    
    cur.execute("SELECT COUNT(*) as count FROM role")
    print(f"Roles: {cur.fetchone()['count']}")
    
    cur.execute("SELECT COUNT(*) as count FROM employee")
    print(f"Employees: {cur.fetchone()['count']}")
    
    cur.execute("SELECT COUNT(*) as count FROM project")
    print(f"Projects: {cur.fetchone()['count']}")
    
    cur.close()
    conn.close()
    print("\n✅ Database populated successfully!")


if __name__ == "__main__":
    main()
