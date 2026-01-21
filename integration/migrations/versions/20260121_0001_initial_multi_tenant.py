"""Initial multi-tenant schema.

Revision ID: 0001
Revises:
Create Date: 2026-01-21 02:30:00

Creates the core multi-tenant tables:
- agencies (marketing agencies / superusers)
- clinics (medical clinics / tenants)
- users (authenticated users)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE agencyplan AS ENUM ('starter', 'pro', 'enterprise')")
    op.execute("CREATE TYPE clinicstatus AS ENUM ('trial', 'active', 'paused', 'cancelled')")
    op.execute("CREATE TYPE userrole AS ENUM ('superuser', 'agency_staff', 'clinic_owner', 'clinic_staff')")

    # Create agencies table
    op.create_table(
        "agencies",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column(
            "plan",
            postgresql.ENUM("starter", "pro", "enterprise", name="agencyplan", create_type=False),
            nullable=False,
            server_default="starter",
        ),
        sa.Column("max_clinics", sa.Integer, nullable=False, server_default="5"),
        sa.Column("twenty_workspace_id", sa.String(100), nullable=True),
        sa.Column("chatwoot_account_id", sa.String(100), nullable=True),
        sa.Column("settings", postgresql.JSONB, nullable=True),
        sa.Column("branding", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create clinics table
    op.create_table(
        "clinics",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "agency_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("agencies.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, index=True),
        sa.Column("specialty", sa.String(100), nullable=True),
        sa.Column("crm_number", sa.String(20), nullable=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("whatsapp", sa.String(20), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(50), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM("trial", "active", "paused", "cancelled", name="clinicstatus", create_type=False),
            nullable=False,
            server_default="trial",
        ),
        sa.Column("twenty_workspace_id", sa.String(100), nullable=True),
        sa.Column("calcom_team_id", sa.String(100), nullable=True),
        sa.Column("chatwoot_inbox_id", sa.String(100), nullable=True),
        sa.Column("evolution_instance", sa.String(100), nullable=True),
        sa.Column("settings", postgresql.JSONB, nullable=True),
        sa.Column("ai_persona", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create unique constraint for clinic slug within agency
    op.create_unique_constraint("uq_clinic_agency_slug", "clinics", ["agency_id", "slug"])

    # Create users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "agency_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("agencies.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "clinic_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("clinics.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "role",
            postgresql.ENUM("superuser", "agency_staff", "clinic_owner", "clinic_staff", name="userrole", create_type=False),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("email_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("force_password_change", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("twenty_user_id", sa.String(100), nullable=True),
        sa.Column("calcom_user_id", sa.String(100), nullable=True),
        sa.Column("chatwoot_user_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create indexes for common queries
    op.create_index("ix_users_agency_role", "users", ["agency_id", "role"])
    op.create_index("ix_clinics_status", "clinics", ["status"])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index("ix_clinics_status")
    op.drop_index("ix_users_agency_role")
    op.drop_table("users")
    op.drop_constraint("uq_clinic_agency_slug", "clinics")
    op.drop_table("clinics")
    op.drop_table("agencies")

    # Drop enum types
    op.execute("DROP TYPE userrole")
    op.execute("DROP TYPE clinicstatus")
    op.execute("DROP TYPE agencyplan")
