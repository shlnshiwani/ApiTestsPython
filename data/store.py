"""
data/store.py
~~~~~~~~~~~~~
In-memory employee data store.
Acts as a simple database for the demo API.
"""

from models.employee import Employee

# Auto-increment counter for new employee IDs
_next_id = 6

# Seed data — keyed by employee ID
employees: dict[int, Employee] = {
    1: Employee(id=1, name="Alice Johnson",  email="alice@example.com",  department="Engineering", position="Senior Engineer",  salary=95000.0),
    2: Employee(id=2, name="Bob Smith",      email="bob@example.com",    department="Marketing",   position="Marketing Manager", salary=75000.0),
    3: Employee(id=3, name="Carol White",    email="carol@example.com",  department="Engineering", position="Junior Engineer",   salary=65000.0),
    4: Employee(id=4, name="David Brown",    email="david@example.com",  department="HR",          position="HR Specialist",     salary=60000.0),
    5: Employee(id=5, name="Eva Martinez",   email="eva@example.com",    department="Finance",     position="Finance Analyst",   salary=70000.0),
}


def next_id() -> int:
    """Return and increment the global ID counter."""
    global _next_id
    current = _next_id
    _next_id += 1
    return current
