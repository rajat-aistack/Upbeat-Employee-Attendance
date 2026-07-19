"""
Pydantic schemas for request/response validation.
"""
from datetime import datetime, date
from typing import Optional, List, Any
from pydantic import BaseModel, Field


# ─────────────────────────── Employee Schemas ───────────────────────────

class EmployeeCreate(BaseModel):
    employee_id: str = Field(..., min_length=1, max_length=20, description="Unique employee ID (e.g., UPB-001)")
    name: str = Field(..., min_length=1, max_length=100)
    department: str = Field(..., min_length=1, max_length=50)
    designation: str = Field(..., min_length=1, max_length=50)
    mobile: Optional[str] = Field(None, max_length=20)
    joining_date: Optional[date] = None


class EmployeeUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=50)
    designation: Optional[str] = Field(None, max_length=50)
    mobile: Optional[str] = Field(None, max_length=20)
    joining_date: Optional[date] = None


class EmployeeStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(active|inactive)$")


class EmployeeResponse(BaseModel):
    id: int
    employee_id: str
    name: str
    department: str
    designation: str
    mobile: Optional[str] = None
    joining_date: Optional[date] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EmployeeListResponse(BaseModel):
    employees: List[EmployeeResponse]
    total: int


# ─────────────────────────── Device Schemas ───────────────────────────

class DeviceRegistrationRequest(BaseModel):
    """Sent by Employee App when device is not registered."""
    fingerprint: str = Field(..., min_length=64, max_length=64)
    hostname: Optional[str] = None
    machine_guid: Optional[str] = None
    system_username: Optional[str] = None
    system_details: Optional[dict] = None


class DeviceRegistrationResponse(BaseModel):
    registration_code: str
    message: str


class DeviceAssignRequest(BaseModel):
    """Sent by Admin App to assign a device to an employee."""
    registration_code: str
    employee_id: int


class DeviceReplaceRequest(BaseModel):
    """Sent by Admin App to replace an employee's device."""
    new_registration_code: str
    employee_id: int


class DeviceStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(active|inactive|removed)$")


class DeviceResponse(BaseModel):
    id: int
    employee_id: Optional[int] = None
    employee_name: Optional[str] = None
    fingerprint: str
    registration_code: str
    hostname: Optional[str] = None
    machine_guid: Optional[str] = None
    system_username: Optional[str] = None
    system_details: Optional[dict] = None
    status: str
    registered_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DeviceLookupResponse(BaseModel):
    """Response when employee app looks up its device."""
    registered: bool
    status: Optional[str] = None
    employee_name: Optional[str] = None
    employee_id: Optional[str] = None
    employee_db_id: Optional[int] = None
    employee_status: Optional[str] = None


class DeviceListResponse(BaseModel):
    devices: List[DeviceResponse]
    total: int


# ─────────────────────────── Attendance Schemas ───────────────────────────

class PunchInRequest(BaseModel):
    device_fingerprint: str
    hostname: Optional[str] = None
    system_username: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    wifi_ssid: Optional[str] = None
    wifi_bssid: Optional[str] = None
    gateway_mac: Optional[str] = None
    gateway_ip: Optional[str] = None
    timestamp: Optional[datetime] = None
    sync_id: Optional[str] = None


class PunchOutRequest(BaseModel):
    device_fingerprint: str
    hostname: Optional[str] = None
    system_username: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    wifi_ssid: Optional[str] = None
    wifi_bssid: Optional[str] = None
    gateway_mac: Optional[str] = None
    gateway_ip: Optional[str] = None
    timestamp: Optional[datetime] = None
    sync_id: Optional[str] = None


class SyncRecord(BaseModel):
    """A single offline attendance record to sync."""
    action: str = Field(..., pattern="^(punch_in|punch_out)$")
    device_fingerprint: str
    hostname: Optional[str] = None
    system_username: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    wifi_ssid: Optional[str] = None
    wifi_bssid: Optional[str] = None
    gateway_mac: Optional[str] = None
    gateway_ip: Optional[str] = None
    timestamp: datetime
    sync_id: str


class SyncRequest(BaseModel):
    """Bulk sync request from Employee App."""
    records: List[SyncRecord]


class SyncResponse(BaseModel):
    synced: int
    skipped: int
    errors: List[str]


class AttendanceStatusResponse(BaseModel):
    """Today's attendance status for a device."""
    has_checked_in: bool = False
    has_checked_out: bool = False
    check_in_time: Optional[str] = None
    check_out_time: Optional[str] = None
    employee_name: Optional[str] = None


class AttendanceResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: str
    date: date
    check_in_at: Optional[datetime] = None
    check_out_at: Optional[datetime] = None
    status: str
    is_late: bool
    missing_checkout: bool
    remarks: Optional[str] = None
    working_hours: Optional[str] = None

    model_config = {"from_attributes": True}


class AttendanceListResponse(BaseModel):
    records: List[AttendanceResponse]
    total: int


# ─────────────────────────── Office Settings Schemas ───────────────────────────

class OfficeSettingsUpdate(BaseModel):
    wifi_ssid: Optional[str] = None
    wifi_bssid: Optional[str] = None
    gateway_mac: Optional[str] = None
    gateway_ip: Optional[str] = None
    office_start_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    office_end_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    grace_period_minutes: Optional[int] = Field(None, ge=0, le=120)
    late_threshold_minutes: Optional[int] = Field(None, ge=0, le=240)
    sync_interval_seconds: Optional[int] = Field(None, ge=30, le=3600)


class OfficeSettingsResponse(BaseModel):
    id: int
    wifi_ssid: Optional[str] = None
    wifi_bssid: Optional[str] = None
    gateway_mac: Optional[str] = None
    gateway_ip: Optional[str] = None
    office_start_time: str
    office_end_time: str
    grace_period_minutes: int
    late_threshold_minutes: int
    sync_interval_seconds: int

    model_config = {"from_attributes": True}


class WiFiSettingsResponse(BaseModel):
    """Minimal WiFi settings for employee app validation."""
    wifi_ssid: Optional[str] = None
    wifi_bssid: Optional[str] = None
    gateway_mac: Optional[str] = None
    gateway_ip: Optional[str] = None
    office_start_time: str
    grace_period_minutes: int
    late_threshold_minutes: int


# ─────────────────────────── Dashboard Schemas ───────────────────────────

class DashboardStats(BaseModel):
    total_employees: int = 0
    present_today: int = 0
    absent_today: int = 0
    checked_in: int = 0
    checked_out: int = 0
    pending_registrations: int = 0
    missing_checkout: int = 0
    late_arrivals: int = 0


# ─────────────────────────── Auth Schemas ───────────────────────────

class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


# ─────────────────────────── Report Schemas ───────────────────────────

class ReportFilter(BaseModel):
    start_date: date
    end_date: date
    employee_id: Optional[int] = None
    department: Optional[str] = None
    status: Optional[str] = None


class ReportSummary(BaseModel):
    total_records: int
    total_present: int
    total_absent: int
    total_late: int
    total_missing_checkout: int
    avg_check_in_time: Optional[str] = None
    avg_working_hours: Optional[str] = None


# ─────────────────────────── Generic Schemas ───────────────────────────

class MessageResponse(BaseModel):
    message: str
    success: bool = True
