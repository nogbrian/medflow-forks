#!/usr/bin/env python3
"""
Seed script for initial data.

Creates:
- Tráfego para Consultórios agency
- Superusers

Usage:
    python scripts/seed.py (from repo root)
    python seed.py (from integration folder)
"""

import asyncio
import sys
from pathlib import Path

# Add integration to path for imports when run from scripts folder
current_dir = Path(__file__).parent
if current_dir.name == "scripts":
    sys.path.insert(0, str(current_dir.parent / "integration"))
# Also support running from integration folder directly
sys.path.insert(0, str(current_dir))

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from core.auth import get_password_hash
from core.config import get_settings
from core.models import Agency, AgencyPlan, User, UserRole


async def seed_database():
    """Seed the database with initial data."""
    settings = get_settings()
    print(f"Connecting to database: {settings.database_url[:50]}...")

    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Check if already seeded
        result = await db.execute(select(Agency).limit(1))
        if result.scalar_one_or_none():
            print("Database already seeded. Skipping.")
            return

        print("Seeding database...")

        # Create Tráfego para Consultórios agency
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
        print(f"Created agency: {agency.name} ({agency.id})")

        # Create superusers
        superusers = [
            ("cto@trafegoparaconsultorios.com.br", "CTO"),
            ("heloisa@trafegoparaconsultorios.com.br", "Heloísa"),
            ("briansouzanogueira@gmail.com", "Brian Souza Nogueira"),
        ]

        for email, name in superusers:
            user = User(
                id=str(uuid4()),
                agency_id=agency.id,
                email=email,
                password_hash=get_password_hash("tpc2026#"),
                role=UserRole.SUPERUSER,
                name=name,
                is_active=True,
                email_verified=True,
            )
            db.add(user)
            print(f"Created superuser: {email}")

        await db.commit()
        print("\nDatabase seeded successfully!")
        print("\n" + "=" * 50)
        print("Superuser credentials:")
        print("=" * 50)
        print("Password for all: tpc2026#")
        for email, name in superusers:
            print(f"  - {email} ({name})")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(seed_database())
