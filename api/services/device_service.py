"""
Device registration business logic service.
"""
import random
import string
from datetime import datetime
from typing import Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from api.models import Device, Employee


def generate_registration_code() -> str:
    """Generate a human-readable registration code like 'ABC-123-XYZ'."""
    part1 = ''.join(random.choices(string.ascii_uppercase, k=3))
    part2 = ''.join(random.choices(string.digits, k=3))
    part3 = ''.join(random.choices(string.ascii_uppercase, k=3))
    return f"{part1}-{part2}-{part3}"


def find_device_by_fingerprint(db: Session, fingerprint: str) -> Optional[Device]:
    """Find a device by its fingerprint."""
    return db.query(Device).filter(Device.fingerprint == fingerprint).first()


from sqlalchemy import func

def find_device_by_code(db: Session, registration_code: str) -> Optional[Device]:
    """Find a device by its registration code (case-insensitive and stripped)."""
    return db.query(Device).filter(
        func.upper(Device.registration_code) == registration_code.strip().upper()
    ).first()


def create_pending_device(
    db: Session,
    fingerprint: str,
    hostname: Optional[str],
    machine_guid: Optional[str],
    system_username: Optional[str],
    system_details: Optional[dict],
) -> Device:
    """Create a new pending device registration."""
    # Generate unique registration code
    while True:
        code = generate_registration_code()
        existing = find_device_by_code(db, code)
        if not existing:
            break
    
    device = Device(
        fingerprint=fingerprint,
        registration_code=code,
        hostname=hostname,
        machine_guid=machine_guid,
        system_username=system_username,
        system_details=system_details,
        status="pending",
        last_seen=datetime.utcnow(),
    )
    db.add(device)
    db.flush()
    return device


def assign_device_to_employee(db: Session, device: Device, employee_id: int) -> Device:
    """Assign a pending device to an employee and activate it."""
    device.employee_id = employee_id
    device.status = "active"
    device.registered_at = datetime.utcnow()
    db.flush()
    return device


def replace_employee_device(db: Session, employee_id: int, new_device: Device) -> Device:
    """Replace an employee's current device with a new one."""
    # Deactivate all existing active devices for this employee
    old_devices = db.query(Device).filter(
        and_(
            Device.employee_id == employee_id,
            Device.status == "active",
        )
    ).all()
    
    for old_device in old_devices:
        old_device.status = "replaced"
    
    # Activate the new device
    new_device.employee_id = employee_id
    new_device.status = "active"
    new_device.registered_at = datetime.utcnow()
    db.flush()
    return new_device


def get_pending_devices(db: Session) -> list:
    """Get all devices awaiting registration."""
    return db.query(Device).filter(Device.status == "pending").order_by(Device.created_at.desc()).all()
