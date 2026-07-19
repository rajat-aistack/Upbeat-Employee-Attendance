"""
SQLAlchemy ORM models for the Upbeat Attendance System.
"""
from datetime import datetime, date, time
from sqlalchemy import (
    Column, Integer, String, Date, Time, DateTime, Boolean, 
    ForeignKey, Text, JSON, Index
)
from sqlalchemy.orm import relationship
from api.database import Base


class Employee(Base):
    """Employee information."""
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    department = Column(String(50), nullable=False)
    designation = Column(String(50), nullable=False)
    mobile = Column(String(20), nullable=True)
    joining_date = Column(Date, nullable=True)
    status = Column(String(20), default="active", nullable=False)  # active, inactive
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    devices = relationship("Device", back_populates="employee", cascade="all, delete-orphan")
    attendance_records = relationship("Attendance", back_populates="employee", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Employee(id={self.id}, employee_id='{self.employee_id}', name='{self.name}')>"


class Device(Base):
    """Registered devices linked to employees."""
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    fingerprint = Column(String(64), unique=True, nullable=False, index=True)
    registration_code = Column(String(20), unique=True, nullable=False, index=True)
    hostname = Column(String(100), nullable=True)
    machine_guid = Column(String(100), nullable=True)
    system_username = Column(String(100), nullable=True)
    system_details = Column(JSON, nullable=True)
    status = Column(String(20), default="pending", nullable=False)  # pending, active, inactive, replaced
    registered_at = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    employee = relationship("Employee", back_populates="devices")

    def __repr__(self):
        return f"<Device(id={self.id}, fingerprint='{self.fingerprint[:16]}...', status='{self.status}')>"


class Attendance(Base):
    """Daily attendance records."""
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    employee_name = Column(String(100), nullable=False)  # Denormalized for reports
    device_fingerprint = Column(String(64), nullable=False)
    hostname = Column(String(100), nullable=True)
    system_username = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    mac_address = Column(String(17), nullable=True)
    wifi_ssid = Column(String(100), nullable=True)
    wifi_bssid = Column(String(17), nullable=True)
    gateway_mac = Column(String(17), nullable=True)
    gateway_ip = Column(String(45), nullable=True)
    check_in_at = Column(DateTime, nullable=True)
    check_out_at = Column(DateTime, nullable=True)
    date = Column(Date, nullable=False, index=True)
    status = Column(String(20), default="present", nullable=False)  # present, absent, half-day
    is_late = Column(Boolean, default=False, nullable=False)
    missing_checkout = Column(Boolean, default=False, nullable=False)
    remarks = Column(Text, nullable=True)
    sync_id = Column(String(36), unique=True, nullable=True)  # UUID for offline sync dedup
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    employee = relationship("Employee", back_populates="attendance_records")

    # Composite index for fast daily lookups
    __table_args__ = (
        Index("ix_attendance_employee_date", "employee_id", "date"),
    )

    def __repr__(self):
        return f"<Attendance(id={self.id}, employee='{self.employee_name}', date='{self.date}')>"


class OfficeSettings(Base):
    """Office configuration (single-row table)."""
    __tablename__ = "office_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    wifi_ssid = Column(String(100), nullable=True)
    wifi_bssid = Column(String(17), nullable=True)
    gateway_mac = Column(String(17), nullable=True)
    gateway_ip = Column(String(45), nullable=True)
    office_start_time = Column(String(5), default="09:00", nullable=False)  # HH:MM
    office_end_time = Column(String(5), default="18:00", nullable=False)  # HH:MM
    grace_period_minutes = Column(Integer, default=15, nullable=False)
    late_threshold_minutes = Column(Integer, default=30, nullable=False)
    sync_interval_seconds = Column(Integer, default=300, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<OfficeSettings(wifi_ssid='{self.wifi_ssid}')>"


class AdminUser(Base):
    """Admin user credentials."""
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<AdminUser(username='{self.username}')>"
