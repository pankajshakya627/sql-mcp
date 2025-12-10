"""
Static database schema definition for Text-to-SQL generation.
No actual database connection required.
"""

DATABASE_SCHEMA = """
# Database Schema

## Table: department
  - id: integer (NOT NULL, PRIMARY KEY)
  - name: varchar(100) (NOT NULL)
  - location: varchar(100) (NULL)

## Table: role
  - id: integer (NOT NULL, PRIMARY KEY)
  - title: varchar(100) (NOT NULL)
  - salary_range: varchar(50) (NULL)

## Table: employee
  - id: integer (NOT NULL, PRIMARY KEY)
  - name: varchar(100) (NOT NULL)
  - email: varchar(100) (NULL, UNIQUE)
  - department_id: integer (NULL, FOREIGN KEY → department.id)
  - role_id: integer (NULL, FOREIGN KEY → role.id)
  - hire_date: date (NULL)

## Table: project
  - id: integer (NOT NULL, PRIMARY KEY)
  - name: varchar(100) (NOT NULL)
  - description: text (NULL)
  - department_id: integer (NULL, FOREIGN KEY → department.id)
  - status: varchar(20) (NULL, DEFAULT 'Active')

## Foreign Key Relationships
  - employee.department_id → department.id
  - employee.role_id → role.id
  - project.department_id → department.id

## Sample Data Context (for reference, not actual data)
- Departments: Engineering, HR, Sales, Marketing
- Roles: Software Engineer, Senior Engineer, HR Manager, Sales Representative, Marketing Specialist
- Typical queries: employee lists, department employee counts, project assignments
"""

def get_schema():
    """Return the static database schema."""
    return DATABASE_SCHEMA
