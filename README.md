# ApiTestsPython — Employee REST API

A demo REST API built with **FastAPI** (Python) covering Employee CRUD operations.  
Swagger UI is built-in — no extra tools needed to call the API interactively.

---

## Prerequisites

- Python 3.9+

---

## Setup

```bash
cd ApiTestsPython

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux

# Install dependencies
pip install -r requirements.txt
```

---

## Start the server

```bash
uvicorn main:app --reload --port 8000
```

| URL | Purpose |
|-----|---------|
| http://localhost:8000/docs | **Swagger UI** — interactive API explorer |
| http://localhost:8000/redoc | ReDoc — clean documentation view |
| http://localhost:8000/openapi.json | Raw OpenAPI 3.0 JSON spec |

---

## Authentication

Every endpoint requires the `X-API-Key` header.

| Header | Value |
|--------|-------|
| `X-API-Key` | `secret123` |

In Swagger UI: click **Authorize** (top-right lock icon) → enter `secret123` → **Authorize**.

---

## Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/employees` | List all employees (with optional query params) |
| `GET` | `/api/employees/{employee_id}` | Get employee by ID (path variable) |
| `POST` | `/api/employees` | Create employee |
| `POST` | `/api/departments/{department}/employees` | Create employee in a department (POST with path variable) |
| `PUT` | `/api/employees/{employee_id}` | Full update (replace all fields) |
| `PATCH` | `/api/employees/{employee_id}` | Partial update (only provided fields change) |
| `DELETE` | `/api/employees/{employee_id}` | Delete employee |

### Query parameters — `GET /api/employees`

| Param | Type | Description |
|-------|------|-------------|
| `department` | string | Filter by department (exact, case-insensitive) |
| `position` | string | Filter by position (exact, case-insensitive) |
| `name` | string | Filter by name substring (case-insensitive) |

**Examples:**
```
GET /api/employees?department=Engineering
GET /api/employees?position=Senior+Engineer
GET /api/employees?name=alice
```

---

## Request / Response examples

### Create employee — `POST /api/employees`

**Headers:**
```
X-API-Key: secret123
Content-Type: application/json
```

**Body:**
```json
{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "department": "Engineering",
  "position": "Senior Engineer",
  "salary": 95000.0
}
```

**Response 201:**
```json
{
  "id": 6,
  "name": "Jane Doe",
  "email": "jane@example.com",
  "department": "Engineering",
  "position": "Senior Engineer",
  "salary": 95000.0
}
```

### Create in department — `POST /api/departments/Engineering/employees`

The `department` field is set from the URL path — any `department` in the body is overridden.

### Partial update — `PATCH /api/employees/1`

Send only the fields to change:
```json
{ "salary": 100000.0 }
```

---

## Project structure

```
ApiTestsPython/
├── main.py                       ← FastAPI app, Swagger config, CORS
├── requirements.txt
├── models/
│   └── employee.py               ← Pydantic request/response models
├── routers/
│   └── employee_router.py        ← All employee endpoints
├── dependencies/
│   └── headers.py                ← X-API-Key + Accept header validation
└── data/
    └── store.py                  ← In-memory employee store (seeded with 5 employees)
```

---

## Seeded data

5 employees are pre-loaded on startup (data resets when the server restarts):

| ID | Name | Department | Position | Salary |
|----|------|------------|----------|--------|
| 1 | Alice Johnson | Engineering | Senior Engineer | $95,000 |
| 2 | Bob Smith | Marketing | Marketing Manager | $75,000 |
| 3 | Carol White | Engineering | Junior Engineer | $65,000 |
| 4 | David Brown | HR | HR Specialist | $60,000 |
| 5 | Eva Martinez | Finance | Finance Analyst | $70,000 |

---

## Stack

| Package | Version | Purpose |
|---------|---------|---------|
| FastAPI | 0.115.5 | REST framework + auto Swagger generation |
| uvicorn | 0.32.1 | ASGI server |
| pydantic | 2.10.3 | Request/response validation and serialisation |
