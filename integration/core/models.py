"""
Multi-tenant database models.

Architecture:
- Agency: The marketing agency (superuser)
- Clinic: Medical clinic (tenant/client)
- User: Can belong to agency or clinic
"""

import enum
from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


# =============================================================================
# ENUMS
# =============================================================================


class UserRole(str, enum.Enum):
    """User roles."""
    SUPERUSER = "superuser"        # Agency owner/admin
    AGENCY_STAFF = "agency_staff"  # Agency employee
    CLINIC_OWNER = "clinic_owner"  # Clinic admin
    CLINIC_STAFF = "clinic_staff"  # Clinic employee


class ClinicStatus(str, enum.Enum):
    """Clinic subscription status."""
    TRIAL = "trial"
    ACTIVE = "active"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class AgencyPlan(str, enum.Enum):
    """Agency subscription plan."""
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


# =============================================================================
# MODELS
# =============================================================================


class Agency(Base):
    """
    Marketing agency (superuser).

    This is the top-level entity that owns clinics.
    In a white-label scenario, each agency is a separate customer.
    """
    __tablename__ = "agencies"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Subscription
    plan: Mapped[AgencyPlan] = mapped_column(
        Enum(AgencyPlan),
        default=AgencyPlan.STARTER,
    )
    max_clinics: Mapped[int] = mapped_column(default=5)

    # External service IDs (for syncing)
    twenty_workspace_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    chatwoot_account_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Settings
    settings: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    branding: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)  # logo, colors, etc.

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    clinics: Mapped[list["Clinic"]] = relationship(back_populates="agency")
    users: Mapped[list["User"]] = relationship(back_populates="agency")


class Clinic(Base):
    """
    Medical clinic (tenant).

    Each clinic is a client of the agency with isolated data.
    """
    __tablename__ = "clinics"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    agency_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("agencies.id", ondelete="CASCADE"),
        index=True,
    )

    # Basic info
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(100), index=True)
    specialty: Mapped[str | None] = mapped_column(String(100), nullable=True)
    crm_number: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Contact
    email: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    whatsapp: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Location
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status
    status: Mapped[ClinicStatus] = mapped_column(
        Enum(ClinicStatus),
        default=ClinicStatus.TRIAL,
    )

    # External service IDs (isolated per clinic)
    twenty_workspace_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    calcom_team_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    chatwoot_inbox_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    evolution_instance: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Settings
    settings: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    ai_persona: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)  # Brand voice, etc.

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    agency: Mapped["Agency"] = relationship(back_populates="clinics")
    users: Mapped[list["User"]] = relationship(back_populates="clinic")

    # Unique constraint: slug must be unique within agency
    __table_args__ = (
        {"schema": None},  # Will add UniqueConstraint separately if needed
    )


class User(Base):
    """
    User account.

    Can belong to:
    - Agency only (superuser, agency_staff)
    - Clinic only (clinic_owner, clinic_staff)
    - Both agency and clinic (for agency staff managing specific clinic)
    """
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Relations (at least one must be set)
    agency_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("agencies.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    clinic_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("clinics.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Auth
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole))

    # Profile
    name: Mapped[str] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    force_password_change: Mapped[bool] = mapped_column(Boolean, default=False)

    # External service IDs
    twenty_user_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    calcom_user_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    chatwoot_user_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    agency: Mapped["Agency | None"] = relationship(back_populates="users")
    clinic: Mapped["Clinic | None"] = relationship(back_populates="users")

    @property
    def is_superuser(self) -> bool:
        """Check if user has superuser privileges."""
        return self.role == UserRole.SUPERUSER

    @property
    def is_agency_user(self) -> bool:
        """Check if user belongs to agency."""
        return self.role in [UserRole.SUPERUSER, UserRole.AGENCY_STAFF]

    @property
    def is_clinic_user(self) -> bool:
        """Check if user belongs to clinic."""
        return self.role in [UserRole.CLINIC_OWNER, UserRole.CLINIC_STAFF]

    def can_access_clinic(self, clinic_id: str) -> bool:
        """Check if user can access a specific clinic."""
        # Superuser can access all clinics in their agency
        if self.is_superuser:
            return True
        # Agency staff can access all clinics
        if self.role == UserRole.AGENCY_STAFF:
            return True
        # Clinic users can only access their own clinic
        return self.clinic_id == clinic_id
