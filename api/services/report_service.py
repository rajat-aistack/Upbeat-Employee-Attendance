"""
Report generation business logic service.
"""
from datetime import date
from typing import Optional, List, Tuple

from sqlalchemy import and_
from sqlalchemy.orm import Session

from api.models import Attendance, Employee
from api.services.attendance_service import calculate_working_hours


def get_attendance_report(
    db: Session,
    start_date: date,
    end_date: date,
    employee_id: Optional[int] = None,
    department: Optional[str] = None,
    status: Optional[str] = None,
) -> Tuple[List[dict], int]:
    """Generate attendance report with filters."""
    query = db.query(Attendance).join(
        Employee, Attendance.employee_id == Employee.id
    ).filter(
        and_(
            Attendance.date >= start_date,
            Attendance.date <= end_date,
        )
    ).order_by(Attendance.date.desc(), Attendance.employee_name)
    
    if employee_id is not None:
        query = query.filter(Attendance.employee_id == employee_id)
    
    if department:
        query = query.filter(Employee.department == department)
    
    if status:
        query = query.filter(Attendance.status == status)
    
    records = query.all()
    
    report_data = []
    for record in records:
        working_hrs = calculate_working_hours(record.check_in_at, record.check_out_at)
        report_data.append({
            "id": record.id,
            "employee_id": record.employee_id,
            "employee_name": record.employee_name,
            "date": record.date.isoformat(),
            "check_in_at": record.check_in_at.isoformat() if record.check_in_at else None,
            "check_out_at": record.check_out_at.isoformat() if record.check_out_at else None,
            "working_hours": working_hrs,
            "status": record.status,
            "is_late": record.is_late,
            "missing_checkout": record.missing_checkout,
            "remarks": record.remarks,
        })
    
    return report_data, len(report_data)


def get_report_summary(
    db: Session,
    start_date: date,
    end_date: date,
    employee_id: Optional[int] = None,
    department: Optional[str] = None,
) -> dict:
    """Generate summary statistics for a report period."""
    query = db.query(Attendance).join(
        Employee, Attendance.employee_id == Employee.id
    ).filter(
        and_(
            Attendance.date >= start_date,
            Attendance.date <= end_date,
        )
    )
    
    if employee_id is not None:
        query = query.filter(Attendance.employee_id == employee_id)
    
    if department:
        query = query.filter(Employee.department == department)
    
    records = query.all()
    
    total = len(records)
    present = sum(1 for r in records if r.status == "present")
    late = sum(1 for r in records if r.is_late)
    missing = sum(1 for r in records if r.missing_checkout)
    
    # Calculate average check-in time
    check_in_times = [r.check_in_at for r in records if r.check_in_at]
    avg_check_in = None
    if check_in_times:
        total_minutes = sum(t.hour * 60 + t.minute for t in check_in_times)
        avg_minutes = total_minutes // len(check_in_times)
        avg_h, avg_m = divmod(avg_minutes, 60)
        avg_check_in = f"{avg_h:02d}:{avg_m:02d}"
    
    # Calculate average working hours
    working_deltas = []
    for r in records:
        if r.check_in_at and r.check_out_at:
            delta = r.check_out_at - r.check_in_at
            working_deltas.append(delta.total_seconds())
    
    avg_working = None
    if working_deltas:
        avg_seconds = sum(working_deltas) / len(working_deltas)
        avg_wh = int(avg_seconds) // 3600
        avg_wm = (int(avg_seconds) % 3600) // 60
        avg_working = f"{avg_wh}h {avg_wm}m"
    
    return {
        "total_records": total,
        "total_present": present,
        "total_absent": total - present,
        "total_late": late,
        "total_missing_checkout": missing,
        "avg_check_in_time": avg_check_in,
        "avg_working_hours": avg_working,
    }
