-- Database initialization script for Docker
-- This runs automatically when the PostgreSQL container starts

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
    ('Marketing', 'Building B')
ON CONFLICT DO NOTHING;

INSERT INTO role (title, salary_range) VALUES
    ('Software Engineer', '80k-120k'),
    ('Senior Engineer', '120k-160k'),
    ('HR Manager', '70k-100k'),
    ('Sales Representative', '50k-80k + Commission'),
    ('Marketing Specialist', '60k-90k')
ON CONFLICT DO NOTHING;

INSERT INTO employee (name, email, department_id, role_id) VALUES
    ('Alice Smith', 'alice@org.com', 1, 2),
    ('Bob Jones', 'bob@org.com', 1, 1),
    ('Charlie Brown', 'charlie@org.com', 2, 3),
    ('Diana Prince', 'diana@org.com', 3, 4),
    ('Evan Wright', 'evan@org.com', 4, 5)
ON CONFLICT DO NOTHING;

INSERT INTO project (name, description, department_id) VALUES
    ('Project Alpha', 'Next gen platform', 1),
    ('Project Beta', 'Mobile app overhaul', 1),
    ('Recruitment Drive', 'Q4 Hiring', 2),
    ('Q4 Sales Push', 'End of year targets', 3)
ON CONFLICT DO NOTHING;
