"""
models/employee.py
~~~~~~~~~~~~~~~~~~
Pydantic models for the Employee resource.
FastAPI uses these for request validation, response serialization,
and automatic Swagger schema generation.
"""

from pydantic import BaseModel, EmailStr, Field


class EmployeeBase(BaseModel):
    """Fields shared by create and update requests."""
    name:       str   = Field(..., min_length=1, max_length=100, examples=["Alice Johnson"])
    email:      str   = Field(..., examples=["alice@example.com"])
    department: str   = Field(..., examples=["Engineering"])
    position:   str   = Field(..., examples=["Senior Engineer"])
    salary:     float = Field(..., gt=0, examples=[95000.0])


class EmployeeCreate(EmployeeBase):
    """Request body for POST /employees — all fields required."""
    pass


class EmployeeUpdate(BaseModel):
    """
    Request body for PUT /employees/{id} — all fields required (full replacement).
    Use PATCH for partial updates.
    """
    name:       str   = Field(..., min_length=1, max_length=100, examples=["Alice Johnson"])
    email:      str   = Field(..., examples=["alice@example.com"])
    department: str   = Field(..., examples=["Engineering"])
    position:   str   = Field(..., examples=["Lead Engineer"])
    salary:     float = Field(..., gt=0, examples=[100000.0])


class EmployeePatch(BaseModel):
    """Request body for PATCH /employees/{id} — all fields optional (partial update)."""
    name:       str   | None = Field(None, min_length=1, max_length=100)
    email:      str   | None = Field(None)
    department: str   | None = Field(None)
    position:   str   | None = Field(None)
    salary:     float | None = Field(None, gt=0)


class Employee(EmployeeBase):
    """Full employee resource returned in responses (includes server-assigned id)."""
    id: int = Field(..., examples=[1])
