"""
Attendance (punch in/out, sync) API endpoints.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Attendance
from api.schemas import (
    PunchInRequest, PunchOutRequest, SyncRequest, SyncResponse,
    AttendanceStatusResponse, MessageResponse,
)
from api.security import verify_api_key
from api.services.attendance_service import (
    get_today_attendance, check_late_status, resolve_device_employee,
)

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])


@router.post("/punch-in", response_model=MessageResponse)
def punch_in(
    data: PunchInRequest,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
):
    """Record employee check-in."""
    result = resolve_device_employee(db, data.device_fingerprint)
    if not result:
        raise HTTPException(status_code=403, detail="Device not registered or employee not active")

    device, employee = result
    today = datetime.utcnow().date()
    now = data.timestamp or datetime.utcnow()

    existing = get_today_attendance(db, employee.id, today)
    if existing:
        if existing.check_in_at:
            raise HTTPException(status_code=400, detail="Already checked in today")

    is_late, late_remark = check_late_status(db, now)

    attendance = Attendance(
        employee_id=employee.id,
        employee_name=employee.name,
        device_fingerprint=data.device_fingerprint,
        hostname=data.hostname,
        system_username=data.system_username,
        ip_address=data.ip_address,
        mac_address=data.mac_address,
        wifi_ssid=data.wifi_ssid,
        wifi_bssid=data.wifi_bssid,
        gateway_mac=data.gateway_mac,
        gateway_ip=data.gateway_ip,
        check_in_at=now,
        date=today,
        status="present",
        is_late=is_late,
        remarks=late_remark if late_remark else None,
        sync_id=data.sync_id,
    )
    db.add(attendance)
    db.flush()

    time_str = now.strftime("%I:%M %p")
    msg = f"Punch In successful at {time_str}"
    if is_late:
        msg += " (Late arrival)"
    return MessageResponse(message=msg)


@router.post("/punch-out", response_model=MessageResponse)
def punch_out(
    data: PunchOutRequest,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
):
    """Record employee check-out."""
    result = resolve_device_employee(db, data.device_fingerprint)
    if not result:
        raise HTTPException(status_code=403, detail="Device not registered or employee not active")

    device, employee = result
    today = datetime.utcnow().date()
    now = data.timestamp or datetime.utcnow()

    existing = get_today_attendance(db, employee.id, today)
    if not existing or not existing.check_in_at:
        raise HTTPException(status_code=400, detail="You must check in before checking out")

    if existing.check_out_at:
        raise HTTPException(status_code=400, detail="Already checked out today")

    existing.check_out_at = now
    existing.hostname = data.hostname or existing.hostname
    existing.system_username = data.system_username or existing.system_username
    existing.ip_address = data.ip_address or existing.ip_address
    existing.mac_address = data.mac_address or existing.mac_address
    existing.wifi_ssid = data.wifi_ssid or existing.wifi_ssid
    existing.wifi_bssid = data.wifi_bssid or existing.wifi_bssid
    existing.gateway_mac = data.gateway_mac or existing.gateway_mac
    existing.gateway_ip = data.gateway_ip or existing.gateway_ip

    db.flush()

    time_str = now.strftime("%I:%M %p")
    return MessageResponse(message=f"Punch Out successful at {time_str}")


@router.get("/status/{fingerprint}", response_model=AttendanceStatusResponse)
def get_attendance_status(
    fingerprint: str,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
):
    """Get today's attendance status for a device."""
    result = resolve_device_employee(db, fingerprint)
    if not result:
        return AttendanceStatusResponse()

    device, employee = result
    today = datetime.utcnow().date()

    existing = get_today_attendance(db, employee.id, today)
    if not existing:
        return AttendanceStatusResponse(employee_name=employee.name)

    return AttendanceStatusResponse(
        has_checked_in=existing.check_in_at is not None,
        has_checked_out=existing.check_out_at is not None,
        check_in_time=existing.check_in_at.strftime("%I:%M %p") if existing.check_in_at else None,
        check_out_time=existing.check_out_at.strftime("%I:%M %p") if existing.check_out_at else None,
        employee_name=employee.name,
    )


@router.post("/sync", response_model=SyncResponse)
def sync_offline_records(
    data: SyncRequest,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
):
    """Bulk sync offline attendance records. Uses sync_id for idempotency."""
    synced = 0
    skipped = 0
    errors = []

    for record in data.records:
        try:
            # Check for duplicate sync_id
            if record.sync_id:
                existing = db.query(Attendance).filter(
                    Attendance.sync_id == record.sync_id
                ).first()
                if existing:
                    skipped += 1
                    continue

            result = resolve_device_employee(db, record.device_fingerprint)
            if not result:
                errors.append(f"Device {record.device_fingerprint[:8]}... not registered")
                continue

            device, employee = result
            record_date = record.timestamp.date()

            if record.action == "punch_in":
                existing_att = get_today_attendance(db, employee.id, record_date)
                if existing_att and existing_att.check_in_at:
                    skipped += 1
                    continue

                is_late, late_remark = check_late_status(db, record.timestamp)

                attendance = Attendance(
                    employee_id=employee.id,
                    employee_name=employee.name,
                    device_fingerprint=record.device_fingerprint,
                    hostname=record.hostname,
                    system_username=record.system_username,
                    ip_address=record.ip_address,
                    mac_address=record.mac_address,
                    wifi_ssid=record.wifi_ssid,
                    wifi_bssid=record.wifi_bssid,
                    gateway_mac=record.gateway_mac,
                    gateway_ip=record.gateway_ip,
                    check_in_at=record.timestamp,
                    date=record_date,
                    status="present",
                    is_late=is_late,
                    remarks=late_remark if late_remark else None,
                    sync_id=record.sync_id,
                )
                db.add(attendance)
                synced += 1

            elif record.action == "punch_out":
                existing_att = get_today_attendance(db, employee.id, record_date)
                if not existing_att or not existing_att.check_in_at:
                    errors.append(f"No check-in found for {employee.name} on {record_date}")
                    continue
                if existing_att.check_out_at:
                    skipped += 1
                    continue

                existing_att.check_out_at = record.timestamp
                synced += 1

        except Exception as e:
            errors.append(str(e))

    db.flush()
    return SyncResponse(synced=synced, skipped=skipped, errors=errors)
