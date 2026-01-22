"""Authentication routes."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select

from core.auth import (
    CurrentUser,
    DBSession,
    create_access_token,
    get_password_hash,
    verify_password,
)
from core.models import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    agency_id: str | None
    clinic_id: str | None
    is_active: bool


@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, db: DBSession):
    """Login and get access token."""
    try:
        logger.info(f"Login attempt for email: {data.email}")
        result = await db.execute(
            select(User).where(User.email == data.email)
        )
        user = result.scalar_one_or_none()
        logger.info(f"User found: {user is not None}")

        if not user:
            logger.info("User not found in database")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        logger.info(f"Verifying password for user {user.email}")
        password_valid = verify_password(data.password, user.password_hash)
        logger.info(f"Password valid: {password_valid}")

        if not password_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login error: {str(e)}",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)
    await db.flush()

    token = create_access_token(data={"sub": user.id})

    return LoginResponse(
        access_token=token,
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role.value,
            "agency_id": user.agency_id,
            "clinic_id": user.clinic_id,
            "force_password_change": user.force_password_change,
        },
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: CurrentUser):
    """Get current user info."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role.value,
        agency_id=current_user.agency_id,
        clinic_id=current_user.clinic_id,
        is_active=current_user.is_active,
    )


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    """Change password."""
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    if len(data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )

    current_user.password_hash = get_password_hash(data.new_password)
    current_user.force_password_change = False
    await db.flush()

    return {"message": "Password changed successfully"}
