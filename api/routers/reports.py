"""
Report generation API endpoints.
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.database import get_db
from api.schemas import AttendanceListResponse, AttendanceResponse, ReportSummary
from api.security import verify_api_key, verify_admin_token
from api.services.report_service import get_attendance_report, get_report_summary

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/attendance", response_model=AttendanceListResponse)
def get_report(
    start_date: date = Query(...),
    end_date: date = Query(...),
    employee_id: Optional[int] = Query(None),
    department: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
    _admin: str = Depends(verify_admin_token),
):
    """Get attendance report with filters (admin only)."""
    report_data, total = get_attendance_report(
        db, start_date, end_date, employee_id, department, status
    )

    records = []
    for item in report_data:
        records.append(AttendanceResponse(
            id=item["id"],
            employee_id=item["employee_id"],
            employee_name=item["employee_name"],
            date=item["date"],
            check_in_at=item["check_in_at"],
            check_out_at=item["check_out_at"],
            status=item["status"],
            is_late=item["is_late"],
            missing_checkout=item["missing_checkout"],
            remarks=item["remarks"],
            working_hours=item["working_hours"],
        ))

    return AttendanceListResponse(records=records, total=total)


@router.get("/summary", response_model=ReportSummary)
def get_summary(
    start_date: date = Query(...),
    end_date: date = Query(...),
    employee_id: Optional[int] = Query(None),
    department: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
    _admin: str = Depends(verify_admin_token),
):
    """Get summary statistics for a date range (admin only)."""
    summary = get_report_summary(
        db, start_date, end_date, employee_id, department
    )
    return ReportSummary(**summary)
