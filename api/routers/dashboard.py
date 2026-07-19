"""
Dashboard statistics API endpoint.
"""
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Employee, Device, Attendance
from api.schemas import DashboardStats
from api.security import verify_api_key, verify_admin_token

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
    _admin: str = Depends(verify_admin_token),
):
    """Get today's dashboard statistics (admin only)."""
    today = datetime.utcnow().date()

    # Total active employees
    total_employees = db.query(func.count(Employee.id)).filter(
        Employee.status == "active"
    ).scalar() or 0

    # Today's attendance records
    records = db.query(Attendance).filter(Attendance.date == today).all()

    present_today = len(records)
    absent_today = max(0, total_employees - present_today)
    checked_in = sum(1 for r in records if r.check_in_at and not r.check_out_at)
    checked_out = sum(1 for r in records if r.check_out_at)
    missing_checkout = sum(1 for r in records if r.missing_checkout)
    late_arrivals = sum(1 for r in records if r.is_late)

    # Pending device registrations
    pending_registrations = db.query(func.count(Device.id)).filter(
        Device.status == "pending"
    ).scalar() or 0

    return DashboardStats(
        total_employees=total_employees,
        present_today=present_today,
        absent_today=absent_today,
        checked_in=checked_in,
        checked_out=checked_out,
        pending_registrations=pending_registrations,
        missing_checkout=missing_checkout,
        late_arrivals=late_arrivals,
    )
