"""
Admin authentication API endpoint.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import AdminUser
from api.schemas import AdminLoginRequest, AdminLoginResponse
from api.security import verify_password, create_access_token, verify_api_key

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=AdminLoginResponse)
def admin_login(
    data: AdminLoginRequest,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
):
    """Authenticate admin user and return JWT token."""
    admin = db.query(AdminUser).filter(
        AdminUser.username == data.username
    ).first()

    if not admin or not verify_password(data.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    access_token = create_access_token(admin.username)
    return AdminLoginResponse(
        access_token=access_token,
        username=admin.username,
    )
