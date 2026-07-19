"""
Device registration and management API endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Device, Employee
from api.schemas import (
    DeviceRegistrationRequest, DeviceRegistrationResponse,
    DeviceAssignRequest, DeviceReplaceRequest, DeviceStatusUpdate,
    DeviceResponse, DeviceLookupResponse, DeviceListResponse,
    MessageResponse,
)
from api.security import verify_api_key, verify_admin_token
from api.services.device_service import (
    find_device_by_fingerprint, find_device_by_code,
    create_pending_device, assign_device_to_employee,
    replace_employee_device, get_pending_devices,
)

router = APIRouter(prefix="/api/devices", tags=["Devices"])


def _build_device_response(device: Device, employee: Optional[Employee] = None) -> DeviceResponse:
    """Build a DeviceResponse with optional employee name."""
    return DeviceResponse(
        id=device.id,
        employee_id=device.employee_id,
        employee_name=employee.name if employee else None,
        fingerprint=device.fingerprint,
        registration_code=device.registration_code,
        hostname=device.hostname,
        machine_guid=device.machine_guid,
        system_username=device.system_username,
        system_details=device.system_details,
        status=device.status,
        registered_at=device.registered_at,
        last_seen=device.last_seen,
        created_at=device.created_at,
    )


@router.post("/request-registration", response_model=DeviceRegistrationResponse)
def request_device_registration(
    data: DeviceRegistrationRequest,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
):
    """Employee App sends device fingerprint to get a registration code."""
    existing = find_device_by_fingerprint(db, data.fingerprint)
    if existing:
        if existing.status == "pending":
            return DeviceRegistrationResponse(
                registration_code=existing.registration_code,
                message="Registration pending. Please provide this code to your admin.",
            )
        elif existing.status == "active":
            return DeviceRegistrationResponse(
                registration_code=existing.registration_code,
                message="This device is already registered.",
            )
        elif existing.status in ("inactive", "replaced"):
            return DeviceRegistrationResponse(
                registration_code=existing.registration_code,
                message="This device has been deactivated. Please contact your admin.",
            )

    device = create_pending_device(
        db,
        fingerprint=data.fingerprint,
        hostname=data.hostname,
        machine_guid=data.machine_guid,
        system_username=data.system_username,
        system_details=data.system_details,
    )

    return DeviceRegistrationResponse(
        registration_code=device.registration_code,
        message="Registration pending. Please provide this code to your admin.",
    )


@router.get("/lookup/{fingerprint}", response_model=DeviceLookupResponse)
def lookup_device(
    fingerprint: str,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
):
    """Employee App checks if the device is registered and gets employee info."""
    device = find_device_by_fingerprint(db, fingerprint)

    if not device:
        return DeviceLookupResponse(registered=False)

    if device.status != "active" or not device.employee_id:
        return DeviceLookupResponse(registered=False, status=device.status)

    employee = db.query(Employee).filter(Employee.id == device.employee_id).first()

    if not employee:
        return DeviceLookupResponse(registered=False, status="orphaned")

    return DeviceLookupResponse(
        registered=True,
        status=device.status,
        employee_name=employee.name,
        employee_id=employee.employee_id,
        employee_db_id=employee.id,
        employee_status=employee.status,
    )


@router.get("", response_model=DeviceListResponse)
def list_devices(
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
    _admin: str = Depends(verify_admin_token),
):
    """List all devices (admin only)."""
    query = db.query(Device)
    count_query = db.query(func.count(Device.id))

    if status_filter:
        query = query.filter(Device.status == status_filter)
        count_query = count_query.filter(Device.status == status_filter)

    total = count_query.scalar() or 0
    devices = query.order_by(Device.created_at.desc()).offset(skip).limit(limit).all()

    device_responses = []
    for device in devices:
        employee = None
        if device.employee_id:
            employee = db.query(Employee).filter(Employee.id == device.employee_id).first()
        device_responses.append(_build_device_response(device, employee))

    return DeviceListResponse(devices=device_responses, total=total)


@router.get("/pending", response_model=DeviceListResponse)
def list_pending_devices(
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
    _admin: str = Depends(verify_admin_token),
):
    """List devices awaiting registration (admin only)."""
    devices = get_pending_devices(db)
    return DeviceListResponse(
        devices=[_build_device_response(d) for d in devices],
        total=len(devices),
    )


@router.post("/register", response_model=MessageResponse)
def register_device(
    data: DeviceAssignRequest,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
    _admin: str = Depends(verify_admin_token),
):
    """Admin assigns a pending device to an employee."""
    device = find_device_by_code(db, data.registration_code)
    if not device:
        raise HTTPException(status_code=404, detail="Registration code not found")

    if device.status == "active":
        raise HTTPException(status_code=400, detail="This device is already registered")

    employee = db.query(Employee).filter(Employee.id == data.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    if employee.status != "active":
        raise HTTPException(status_code=400, detail="Employee is not active")

    assign_device_to_employee(db, device, data.employee_id)
    return MessageResponse(message=f"Device successfully registered to {employee.name}")


@router.put("/{device_id}/replace", response_model=MessageResponse)
def replace_device(
    device_id: int,
    data: DeviceReplaceRequest,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
    _admin: str = Depends(verify_admin_token),
):
    """Replace an employee's device with a new one (admin only)."""
    new_device = find_device_by_code(db, data.new_registration_code)
    if not new_device:
        raise HTTPException(status_code=404, detail="New registration code not found")

    if new_device.status != "pending":
        raise HTTPException(status_code=400, detail="New device is not in pending state")

    employee = db.query(Employee).filter(Employee.id == data.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    replace_employee_device(db, data.employee_id, new_device)
    return MessageResponse(message=f"Device replaced successfully for {employee.name}")


@router.patch("/{device_id}/status", response_model=MessageResponse)
def update_device_status(
    device_id: int,
    data: DeviceStatusUpdate,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
    _admin: str = Depends(verify_admin_token),
):
    """Change device status (admin only)."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    device.status = data.status
    db.flush()

    return MessageResponse(message=f"Device status updated to '{data.status}'")
