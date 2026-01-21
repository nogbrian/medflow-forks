"""Core module - Multi-tenant infrastructure."""

from .config import Settings, get_settings
from .database import Base, get_db, AsyncSessionLocal
from .models import Agency, Clinic, User, UserRole
from .auth import (
    create_access_token,
    verify_password,
    get_password_hash,
    get_current_user,
    require_superuser,
    require_clinic_access,
)

__all__ = [
    "Settings",
    "get_settings",
    "Base",
    "get_db",
    "AsyncSessionLocal",
    "Agency",
    "Clinic",
    "User",
    "UserRole",
    "create_access_token",
    "verify_password",
    "get_password_hash",
    "get_current_user",
    "require_superuser",
    "require_clinic_access",
]
