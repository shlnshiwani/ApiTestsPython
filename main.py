"""
main.py
~~~~~~~
FastAPI application entry point.

Start the server:
    uvicorn main:app --reload --port 8000

Swagger UI:  http://localhost:8000/docs
ReDoc:       http://localhost:8000/redoc
OpenAPI JSON: http://localhost:8000/openapi.json
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.employee_router import router as employee_router

app = FastAPI(
    title="Employee API",
    description="""
## Employee Management REST API

A demo REST API built with **FastAPI** showcasing:

- `GET` with **query parameters** (filter by department, position, name)
- `GET` with **path variable** (fetch by ID)
- `POST` with **request body** (create employee)
- `POST` with **path variable** (create in a specific department)
- `PUT` — full replacement
- `PATCH` — partial update
- `DELETE` — remove by ID

### Authentication
Every endpoint requires the **`X-API-Key`** header.
Use value: `secret123`

### Try it out
Click **Authorize** (top-right), enter `secret123` as the API key, then use **Try it out** on any endpoint.
""",
    version="1.0.0",
    contact={"name": "Dev Team"},
    openapi_tags=[
        {
            "name": "Employees",
            "description": "CRUD operations for the Employee resource.",
        }
    ],
)

# Allow all origins for demo purposes — restrict in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the employee router (all routes prefixed with /api)
app.include_router(employee_router)


# ── Security scheme — makes the "Authorize" button appear in Swagger UI ──────

from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Add X-API-Key as a global security scheme
    schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "Use value: secret123",
        }
    }
    # Apply security globally to all operations
    for path in schema["paths"].values():
        for operation in path.values():
            operation["security"] = [{"ApiKeyAuth": []}]

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi
