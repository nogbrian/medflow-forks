#!/usr/bin/env python3
"""
Seed script for initial data.

Creates:
- Default agency
- Demo clinic
- Admin user

Usage:
    python scripts/seed.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "integration"))

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from core.auth import get_password_hash
from core.config import get_settings
from core.models import Agency, AgencyPlan, Clinic, ClinicStatus, User, UserRole


async def seed_database():
    """Seed the database with initial data."""
    settings = get_settings()

    engine = create_async_engine(settings.database_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Check if already seeded
        result = await db.execute(select(Agency).limit(1))
        if result.scalar_one_or_none():
            print("Database already seeded. Skipping.")
            return

        print("Seeding database...")

        # Create default agency
        agency = Agency(
            id=str(uuid4()),
            name="MedFlow Agency",
            slug="medflow",
            email="admin@medflow.com",
            phone="+55 11 99999-0000",
            plan=AgencyPlan.ENTERPRISE,
            max_clinics=100,
            branding={
                "logo_url": None,
                "primary_color": "#4F46E5",
                "secondary_color": "#10B981",
                "company_name": "MedFlow",
            },
            settings={
                "default_language": "pt-BR",
                "timezone": "America/Sao_Paulo",
            },
        )
        db.add(agency)
        await db.flush()
        print(f"Created agency: {agency.name} ({agency.id})")

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
        await db.flush()
        print(f"Created clinic: {clinic.name} ({clinic.id})")

        # Create admin user
        admin = User(
            id=str(uuid4()),
            agency_id=agency.id,
            email="admin@medflow.com",
            password_hash=get_password_hash("admin123"),  # Change in production!
            role=UserRole.SUPERUSER,
            name="Admin",
            is_active=True,
            email_verified=True,
        )
        db.add(admin)
        print(f"Created admin user: {admin.email}")

        # Create clinic owner
        owner = User(
            id=str(uuid4()),
            agency_id=agency.id,
            clinic_id=clinic.id,
            email="dono@clinicademo.com",
            password_hash=get_password_hash("clinic123"),  # Change in production!
            role=UserRole.CLINIC_OWNER,
            name="Dr. Demo",
            is_active=True,
            email_verified=True,
        )
        db.add(owner)
        print(f"Created clinic owner: {owner.email}")

        # Create clinic staff
        staff = User(
            id=str(uuid4()),
            clinic_id=clinic.id,
            email="recepcionista@clinicademo.com",
            password_hash=get_password_hash("staff123"),  # Change in production!
            role=UserRole.CLINIC_STAFF,
            name="Recepcionista Demo",
            is_active=True,
            email_verified=True,
        )
        db.add(staff)
        print(f"Created clinic staff: {staff.email}")

        await db.commit()
        print("\nDatabase seeded successfully!")
        print("\n" + "=" * 50)
        print("Default credentials (CHANGE IN PRODUCTION!):")
        print("=" * 50)
        print(f"Admin:         admin@medflow.com / admin123")
        print(f"Clinic Owner:  dono@clinicademo.com / clinic123")
        print(f"Clinic Staff:  recepcionista@clinicademo.com / staff123")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(seed_database())
