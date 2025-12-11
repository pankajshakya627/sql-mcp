# Setting Up Neon.tech PostgreSQL for sql-mcp

## Quick Setup Guide

### Step 1: Create Neon Account

1. Go to [https://neon.tech](https://neon.tech)
2. Click "Sign Up" (free tier available)
3. Sign in with GitHub, Google, or email

### Step 2: Create Project

1. Click "Create Project"
2. Name: `sql-mcp-db`
3. Region: Choose closest to you
4. PostgreSQL version: 16 (latest)
5. Click "Create"

### Step 3: Get Connection String

After creation, you'll see your connection string:

```
postgresql://username:password@ep-xxx-xxx-xxx.region.aws.neon.tech/neondb?sslmode=require
```

**Copy this string and keep it secret!**

### Step 4: Create Tables

1. In Neon dashboard, click "SQL Editor"
2. Paste and run this SQL:

```sql
-- Create tables
CREATE TABLE IF NOT EXISTS department (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS role (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    salary_range VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS employee (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    department_id INTEGER REFERENCES department(id),
    role_id INTEGER REFERENCES role(id),
    hire_date DATE DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS project (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    department_id INTEGER REFERENCES department(id),
    status VARCHAR(20) DEFAULT 'Active'
);

-- Seed data
INSERT INTO department (name, location) VALUES
    ('Engineering', 'Building A'),
    ('HR', 'Building B'),
    ('Sales', 'Building C'),
    ('Marketing', 'Building B');

INSERT INTO role (title, salary_range) VALUES
    ('Software Engineer', '80k-120k'),
    ('Senior Engineer', '120k-160k'),
    ('HR Manager', '70k-100k'),
    ('Sales Representative', '50k-80k + Commission'),
    ('Marketing Specialist', '60k-90k');

INSERT INTO employee (name, email, department_id, role_id) VALUES
    ('Alice Smith', 'alice@org.com', 1, 2),
    ('Bob Jones', 'bob@org.com', 1, 1),
    ('Charlie Brown', 'charlie@org.com', 2, 3),
    ('Diana Prince', 'diana@org.com', 3, 4),
    ('Evan Wright', 'evan@org.com', 4, 5);

INSERT INTO project (name, description, department_id) VALUES
    ('Project Alpha', 'Next gen platform', 1),
    ('Project Beta', 'Mobile app overhaul', 1),
    ('Recruitment Drive', 'Q4 Hiring', 2),
    ('Q4 Sales Push', 'End of year targets', 3);
```

### Step 5: Configure fastmcp.cloud

In your fastmcp.cloud project settings, add these environment variables:

| Variable             | Value                                                                    |
| -------------------- | ------------------------------------------------------------------------ |
| `DATABASE_URL`       | `postgresql://username:password@ep-xxx.neon.tech/neondb?sslmode=require` |
| `STATIC_SCHEMA_MODE` | `false`                                                                  |
| `OPENROUTER_API_KEY` | `your_openrouter_key`                                                    |

### Step 6: Redeploy

Push your code and redeploy:

```bash
git add . && git commit -m "Updated for Neon DB" && git push origin main
```

### Step 7: Test

In ChatGPT:

```
Use SQL_BASED_MCP's list_employees tool
```

You should now see real data from your Neon database!
