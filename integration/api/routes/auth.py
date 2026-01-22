"""Authentication routes."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Header, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select

from core.auth import (
    CurrentUser,
    DBSession,
    create_access_token,
    get_password_hash,
    verify_password,
)
from core.config import get_settings
from core.models import Agency, AgencyPlan, Clinic, ClinicStatus, User, UserRole

router = APIRouter(prefix="/auth")
settings = get_settings()


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
    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
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


@router.post("/seed")
async def seed_database(
    db: DBSession,
    x_seed_token: str = Header(None, alias="X-Seed-Token"),
):
    """
    Seed the database with initial data (protected by seed token).

    This endpoint creates:
    - Tráfego para Consultórios agency
    - Superusers (CTO, Heloisa, Brian)
    - Demo clinic
    """
    # Verify seed token matches webhook secret
    if x_seed_token != settings.webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid seed token",
        )

    # Check if already seeded
    result = await db.execute(select(Agency).limit(1))
    if result.scalar_one_or_none():
        return {"message": "Database already seeded", "status": "skipped"}

    # Create agency
    agency = Agency(
        id=str(uuid4()),
        name="Tráfego para Consultórios",
        slug="tpc",
        email="contato@trafegoparaconsultorios.com.br",
        phone="+55 11 99999-0000",
        plan=AgencyPlan.ENTERPRISE,
        max_clinics=100,
        branding={
            "logo_url": None,
            "primary_color": "#F24E1E",
            "secondary_color": "#111111",
            "company_name": "Tráfego para Consultórios",
        },
        settings={
            "default_language": "pt-BR",
            "timezone": "America/Sao_Paulo",
        },
    )
    db.add(agency)
    await db.flush()

    # Create superusers
    users_created = []

    # CTO
    cto = User(
        id=str(uuid4()),
        agency_id=agency.id,
        email="cto@trafegoparaconsultorios.com.br",
        password_hash=get_password_hash("tpc2026#"),
        role=UserRole.SUPERUSER,
        name="CTO",
        is_active=True,
        email_verified=True,
    )
    db.add(cto)
    users_created.append(cto.email)

    # Heloisa
    heloisa = User(
        id=str(uuid4()),
        agency_id=agency.id,
        email="heloisa@trafegoparaconsultorios.com.br",
        password_hash=get_password_hash("tpc2026#"),
        role=UserRole.SUPERUSER,
        name="Heloísa",
        is_active=True,
        email_verified=True,
    )
    db.add(heloisa)
    users_created.append(heloisa.email)

    # Brian
    brian = User(
        id=str(uuid4()),
        agency_id=agency.id,
        email="briansouzanogueira@gmail.com",
        password_hash=get_password_hash("tpc2026#"),
        role=UserRole.SUPERUSER,
        name="Brian Souza Nogueira",
        is_active=True,
        email_verified=True,
    )
    db.add(brian)
    users_created.append(brian.email)

    # Create demo clinic
    clinic = Clinic(
        id=str(uuid4()),
        agency_id=agency.id,
        name="Clínica Demo",
        slug="demo",
        specialty="Dermatologia",
        email="contato@clinicademo.com",
        phone="+55 11 98888-0000",
        whatsapp="+55 11 98888-0001",
        city="São Paulo",
        state="SP",
        status=ClinicStatus.ACTIVE,
        ai_persona={
            "name": "Assistente Demo",
            "tone": "professional_friendly",
            "specialties": ["dermatologia", "estética"],
        },
        settings={
            "working_hours": {
                "monday": {"start": "08:00", "end": "18:00"},
                "tuesday": {"start": "08:00", "end": "18:00"},
                "wednesday": {"start": "08:00", "end": "18:00"},
                "thursday": {"start": "08:00", "end": "18:00"},
                "friday": {"start": "08:00", "end": "18:00"},
            },
            "appointment_duration": 30,
        },
    )
    db.add(clinic)

    await db.commit()

    return {
        "message": "Database seeded successfully",
        "status": "completed",
        "agency": agency.name,
        "users": users_created,
        "clinic": clinic.name,
    }
