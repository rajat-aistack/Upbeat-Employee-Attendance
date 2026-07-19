"""
Office settings API endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import OfficeSettings
from api.schemas import (
    OfficeSettingsUpdate, OfficeSettingsResponse,
    WiFiSettingsResponse, MessageResponse,
)
from api.security import verify_api_key, verify_admin_token

router = APIRouter(prefix="/api/settings", tags=["Settings"])


def _get_or_create_settings(db: Session) -> OfficeSettings:
    """Get settings or create default row."""
    settings = db.query(OfficeSettings).first()
    if not settings:
        settings = OfficeSettings()
        db.add(settings)
        db.flush()
        db.refresh(settings)
    return settings


@router.get("", response_model=OfficeSettingsResponse)
def get_settings(
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
    _admin: str = Depends(verify_admin_token),
):
    """Get current office settings (admin only)."""
    settings = _get_or_create_settings(db)
    return OfficeSettingsResponse.model_validate(settings)


@router.put("", response_model=MessageResponse)
def update_settings(
    data: OfficeSettingsUpdate,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
    _admin: str = Depends(verify_admin_token),
):
    """Update office settings (admin only)."""
    settings = _get_or_create_settings(db)

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(settings, key, value)

    db.flush()
    return MessageResponse(message="Settings updated successfully")


@router.get("/wifi", response_model=WiFiSettingsResponse)
def get_wifi_settings(
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
):
    """Get WiFi validation settings (for employee app — no admin token required)."""
    settings = _get_or_create_settings(db)
    return WiFiSettingsResponse(
        wifi_ssid=settings.wifi_ssid,
        wifi_bssid=settings.wifi_bssid,
        gateway_mac=settings.gateway_mac,
        gateway_ip=settings.gateway_ip,
        office_start_time=settings.office_start_time,
        grace_period_minutes=settings.grace_period_minutes,
        late_threshold_minutes=settings.late_threshold_minutes,
    )
