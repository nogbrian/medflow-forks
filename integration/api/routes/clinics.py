"""Clinics (tenants) management routes."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from ulid import ULID

from core.auth import CurrentUser, DBSession, require_superuser
from core.models import Clinic, ClinicStatus

router = APIRouter(prefix="/clinics")


class ClinicCreate(BaseModel):
    name: str
    slug: str
    email: EmailStr
    phone: str | None = None
    specialty: str | None = None
    crm_number: str | None = None
    city: str | None = None
    state: str | None = None


class ClinicUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    specialty: str | None = None
    crm_number: str | None = None
    city: str | None = None
    state: str | None = None
    status: str | None = None


class ClinicResponse(BaseModel):
    id: str
    agency_id: str
    name: str
    slug: str
    email: str
    phone: str | None
    specialty: str | None
    city: str | None
    state: str | None
    status: str
    created_at: str


@router.get("", response_model=list[ClinicResponse])
async def list_clinics(
    current_user: CurrentUser,
    db: DBSession,
    status: str | None = None,
    skip: int = 0,
    limit: int = 50,
):
    """List clinics (agency users see all, clinic users see only their own)."""
    query = select(Clinic).offset(skip).limit(limit)

    if current_user.is_agency_user:
        # Agency user sees all clinics in their agency
        query = query.where(Clinic.agency_id == current_user.agency_id)
    else:
        # Clinic user sees only their clinic
        query = query.where(Clinic.id == current_user.clinic_id)

    if status:
        try:
            clinic_status = ClinicStatus(status)
            query = query.where(Clinic.status == clinic_status)
        except ValueError:
            pass

    result = await db.execute(query)
    clinics = result.scalars().all()

    return [
        ClinicResponse(
            id=c.id,
            agency_id=c.agency_id,
            name=c.name,
            slug=c.slug,
            email=c.email,
            phone=c.phone,
            specialty=c.specialty,
            city=c.city,
            state=c.state,
            status=c.status.value,
            created_at=c.created_at.isoformat(),
        )
        for c in clinics
    ]


@router.post("", response_model=ClinicResponse, status_code=status.HTTP_201_CREATED)
async def create_clinic(
    data: ClinicCreate,
    current_user: CurrentUser,
    db: DBSession,
):
    """Create a new clinic (superuser only)."""
    require_superuser(current_user)

    # Check if slug already exists
    existing = await db.execute(
        select(Clinic).where(
            Clinic.agency_id == current_user.agency_id,
            Clinic.slug == data.slug,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A clinic with this slug already exists",
        )

    clinic = Clinic(
        id=str(ULID()),
        agency_id=current_user.agency_id,
        name=data.name,
        slug=data.slug,
        email=data.email,
        phone=data.phone,
        specialty=data.specialty,
        crm_number=data.crm_number,
        city=data.city,
        state=data.state,
        status=ClinicStatus.TRIAL,
    )

    db.add(clinic)
    await db.flush()
    await db.refresh(clinic)

    return ClinicResponse(
        id=clinic.id,
        agency_id=clinic.agency_id,
        name=clinic.name,
        slug=clinic.slug,
        email=clinic.email,
        phone=clinic.phone,
        specialty=clinic.specialty,
        city=clinic.city,
        state=clinic.state,
        status=clinic.status.value,
        created_at=clinic.created_at.isoformat(),
    )


@router.get("/{clinic_id}", response_model=ClinicResponse)
async def get_clinic(
    clinic_id: str,
    current_user: CurrentUser,
    db: DBSession,
):
    """Get clinic details."""
    if not current_user.can_access_clinic(clinic_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    clinic = await db.get(Clinic, clinic_id)
    if not clinic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinic not found",
        )

    return ClinicResponse(
        id=clinic.id,
        agency_id=clinic.agency_id,
        name=clinic.name,
        slug=clinic.slug,
        email=clinic.email,
        phone=clinic.phone,
        specialty=clinic.specialty,
        city=clinic.city,
        state=clinic.state,
        status=clinic.status.value,
        created_at=clinic.created_at.isoformat(),
    )


@router.put("/{clinic_id}", response_model=ClinicResponse)
async def update_clinic(
    clinic_id: str,
    data: ClinicUpdate,
    current_user: CurrentUser,
    db: DBSession,
):
    """Update clinic (superuser or clinic owner only)."""
    clinic = await db.get(Clinic, clinic_id)
    if not clinic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinic not found",
        )

    # Check permissions
    if not current_user.is_superuser and current_user.clinic_id != clinic_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    update_data = data.model_dump(exclude_unset=True)

    # Handle status conversion
    if "status" in update_data:
        try:
            update_data["status"] = ClinicStatus(update_data["status"])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status value",
            )

    for field, value in update_data.items():
        setattr(clinic, field, value)

    await db.flush()
    await db.refresh(clinic)

    return ClinicResponse(
        id=clinic.id,
        agency_id=clinic.agency_id,
        name=clinic.name,
        slug=clinic.slug,
        email=clinic.email,
        phone=clinic.phone,
        specialty=clinic.specialty,
        city=clinic.city,
        state=clinic.state,
        status=clinic.status.value,
        created_at=clinic.created_at.isoformat(),
    )
