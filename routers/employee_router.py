"""
routers/employee_router.py
~~~~~~~~~~~~~~~~~~~~~~~~~~
Employee CRUD router.

Endpoints:
  GET    /api/employees                          List employees (with optional query params)
  GET    /api/employees/{employee_id}            Get employee by ID (path variable)
  POST   /api/employees                          Create employee
  POST   /api/departments/{department}/employees Create employee in a department (POST with path variable)
  PUT    /api/employees/{employee_id}            Full update
  PATCH  /api/employees/{employee_id}            Partial update
  DELETE /api/employees/{employee_id}            Delete employee

All endpoints require the X-API-Key and Accept headers (enforced via Depends).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from models.employee import Employee, EmployeeCreate, EmployeeUpdate, EmployeePatch
from dependencies.headers import require_headers
import data.store as store

router = APIRouter(
    prefix="/api",
    tags=["Employees"],
    dependencies=[Depends(require_headers)],   # applied to every route in this router
)


# ── GET /api/employees ────────────────────────────────────────────────────────

@router.get(
    "/employees",
    response_model=list[Employee],
    summary="List employees",
    description=(
        "Return all employees. Optionally filter by **department**, **position**, "
        "or a **name** substring (case-insensitive)."
    ),
)
def list_employees(
    department: str | None = Query(None, description="Filter by department (exact match)"),
    position:   str | None = Query(None, description="Filter by position (exact match)"),
    name:       str | None = Query(None, description="Filter by name (case-insensitive substring)"),
) -> list[Employee]:
    results = list(store.employees.values())

    if department:
        results = [e for e in results if e.department.lower() == department.lower()]
    if position:
        results = [e for e in results if e.position.lower() == position.lower()]
    if name:
        results = [e for e in results if name.lower() in e.name.lower()]

    return results


# ── GET /api/employees/{employee_id} ─────────────────────────────────────────

@router.get(
    "/employees/{employee_id}",
    response_model=Employee,
    summary="Get employee by ID",
    description="Retrieve a single employee using their numeric **path variable** ID.",
)
def get_employee(
    employee_id: int = Path(..., description="Numeric employee ID", gt=0),
) -> Employee:
    employee = store.employees.get(employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {employee_id} not found",
        )
    return employee


# ── POST /api/employees ───────────────────────────────────────────────────────

@router.post(
    "/employees",
    response_model=Employee,
    status_code=status.HTTP_201_CREATED,
    summary="Create employee",
    description="Create a new employee. The server assigns a unique numeric ID.",
)
def create_employee(body: EmployeeCreate) -> Employee:
    new_id   = store.next_id()
    employee = Employee(id=new_id, **body.model_dump())
    store.employees[new_id] = employee
    return employee


# ── POST /api/departments/{department}/employees ──────────────────────────────

@router.post(
    "/departments/{department}/employees",
    response_model=Employee,
    status_code=status.HTTP_201_CREATED,
    summary="Create employee in a department (POST with path variable)",
    description=(
        "Create a new employee and assign them to the **department** specified in the URL path. "
        "The `department` field in the request body is **overridden** by the path variable."
    ),
)
def create_employee_in_department(
    department:  str           = Path(..., description="Department name from the URL path"),
    body:        EmployeeCreate = ...,
) -> Employee:
    new_id = store.next_id()
    data   = body.model_dump()
    data["department"] = department          # path variable takes precedence
    employee = Employee(id=new_id, **data)
    store.employees[new_id] = employee
    return employee


# ── PUT /api/employees/{employee_id} ─────────────────────────────────────────

@router.put(
    "/employees/{employee_id}",
    response_model=Employee,
    summary="Full update (replace) employee",
    description="Replace all fields of an existing employee. Every field is required.",
)
def update_employee(
    employee_id: int           = Path(..., description="Numeric employee ID", gt=0),
    body:        EmployeeUpdate = ...,
) -> Employee:
    if employee_id not in store.employees:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {employee_id} not found",
        )
    updated = Employee(id=employee_id, **body.model_dump())
    store.employees[employee_id] = updated
    return updated


# ── PATCH /api/employees/{employee_id} ───────────────────────────────────────

@router.patch(
    "/employees/{employee_id}",
    response_model=Employee,
    summary="Partial update employee",
    description="Update only the provided fields. Omitted fields retain their current values.",
)
def patch_employee(
    employee_id: int          = Path(..., description="Numeric employee ID", gt=0),
    body:        EmployeePatch = ...,
) -> Employee:
    employee = store.employees.get(employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {employee_id} not found",
        )
    # Apply only the fields that were explicitly provided in the request
    patch_data = body.model_dump(exclude_unset=True)
    updated    = employee.model_copy(update=patch_data)
    store.employees[employee_id] = updated
    return updated


# ── DELETE /api/employees/{employee_id} ──────────────────────────────────────

@router.delete(
    "/employees/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete employee",
    description="Permanently remove an employee by ID. Returns 204 No Content on success.",
)
def delete_employee(
    employee_id: int = Path(..., description="Numeric employee ID", gt=0),
) -> None:
    if employee_id not in store.employees:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {employee_id} not found",
        )
    del store.employees[employee_id]
