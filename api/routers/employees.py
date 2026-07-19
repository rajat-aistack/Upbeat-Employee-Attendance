"""
Employee CRUD API endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Employee
from api.schemas import (
    EmployeeCreate, EmployeeUpdate, EmployeeStatusUpdate,
    EmployeeResponse, EmployeeListResponse, MessageResponse,
)
from api.security import verify_api_key, verify_admin_token

router = APIRouter(prefix="/api/employees", tags=["Employees"])


@router.get("", response_model=EmployeeListResponse)
def list_employees(
    search: Optional[str] = Query(None, description="Search by name"),
    department: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
):
    """List all employees with optional filters."""
    query = db.query(Employee)
    count_query = db.query(func.count(Employee.id))

    if search:
        search_filter = or_(
            Employee.name.ilike(f"%{search}%"),
            Employee.employee_id.ilike(f"%{search}%"),
        )
        query = query.filter(search_filter)
        count_query = count_query.filter(search_filter)

    if department:
        query = query.filter(Employee.department == department)
        count_query = count_query.filter(Employee.department == department)

    if status_filter:
        query = query.filter(Employee.status == status_filter)
        count_query = count_query.filter(Employee.status == status_filter)

    total = count_query.scalar() or 0
    employees = query.order_by(Employee.name).offset(skip).limit(limit).all()

    return EmployeeListResponse(
        employees=[EmployeeResponse.model_validate(e) for e in employees],
        total=total,
    )


@router.get("/departments", response_model=list)
def list_departments(
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
):
    """Get list of unique departments."""
    result = db.query(Employee.department).distinct().order_by(Employee.department).all()
    return [row[0] for row in result]


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
):
    """Get a single employee by database ID."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return EmployeeResponse.model_validate(employee)


@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    data: EmployeeCreate,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
    _admin: str = Depends(verify_admin_token),
):
    """Create a new employee (admin only)."""
    existing = db.query(Employee).filter(Employee.employee_id == data.employee_id).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Employee ID '{data.employee_id}' already exists"
        )

    employee = Employee(
        employee_id=data.employee_id,
        name=data.name,
        department=data.department,
        designation=data.designation,
        mobile=data.mobile,
        joining_date=data.joining_date,
    )
    db.add(employee)
    db.flush()
    db.refresh(employee)
    return EmployeeResponse.model_validate(employee)


@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int,
    data: EmployeeUpdate,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
    _admin: str = Depends(verify_admin_token),
):
    """Update an employee's details (admin only)."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(employee, key, value)

    db.flush()
    db.refresh(employee)
    return EmployeeResponse.model_validate(employee)


@router.patch("/{employee_id}/status", response_model=MessageResponse)
def update_employee_status(
    employee_id: int,
    data: EmployeeStatusUpdate,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
    _admin: str = Depends(verify_admin_token),
):
    """Activate or deactivate an employee (admin only)."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    employee.status = data.status
    db.flush()

    action = "activated" if data.status == "active" else "deactivated"
    return MessageResponse(message=f"Employee '{employee.name}' has been {action}")


@router.delete("/{employee_id}", response_model=MessageResponse)
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
    _admin: str = Depends(verify_admin_token),
):
    """Delete an employee permanently (admin only)."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    name = employee.name
    db.delete(employee)
    db.flush()
    return MessageResponse(message=f"Employee '{name}' has been deleted")
