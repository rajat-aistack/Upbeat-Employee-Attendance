"""
Attendance business logic service.
"""
from datetime import datetime, date, timedelta
from typing import Optional, Tuple

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from api.models import Attendance, Device, Employee, OfficeSettings


def get_today_attendance(
    db: Session, employee_id: int, today: date
) -> Optional[Attendance]:
    """Get today's attendance record for an employee."""
    return db.query(Attendance).filter(
        and_(
            Attendance.employee_id == employee_id,
            Attendance.date == today,
        )
    ).first()


def check_late_status(db: Session, check_in_time: datetime) -> Tuple[bool, str]:
    """Determine if a check-in is late based on office settings."""
    settings = db.query(OfficeSettings).first()
    
    if not settings:
        return False, ""
    
    # Parse office start time
    try:
        start_parts = settings.office_start_time.split(":")
        office_start = check_in_time.replace(
            hour=int(start_parts[0]),
            minute=int(start_parts[1]),
            second=0, microsecond=0
        )
    except (ValueError, IndexError):
        return False, ""
    
    grace_deadline = office_start + timedelta(minutes=settings.grace_period_minutes)
    late_deadline = office_start + timedelta(minutes=settings.late_threshold_minutes)
    
    if check_in_time <= grace_deadline:
        return False, ""
    elif check_in_time <= late_deadline:
        return True, "Arrived after grace period"
    else:
        return True, "Late arrival"


def resolve_device_employee(
    db: Session, fingerprint: str
) -> Optional[Tuple[Device, Employee]]:
    """Look up the device and its assigned employee from a fingerprint."""
    device = db.query(Device).filter(
        and_(
            Device.fingerprint == fingerprint,
            Device.status == "active",
        )
    ).first()
    
    if not device or not device.employee_id:
        return None
    
    employee = db.query(Employee).filter(Employee.id == device.employee_id).first()
    
    if not employee or employee.status != "active":
        return None
    
    # Update last seen
    device.last_seen = datetime.utcnow()
    
    return device, employee


def calculate_working_hours(check_in: Optional[datetime], check_out: Optional[datetime]) -> Optional[str]:
    """Calculate working hours between check-in and check-out."""
    if not check_in or not check_out:
        return None
    
    delta = check_out - check_in
    total_seconds = int(delta.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    
    return f"{hours}h {minutes}m"
