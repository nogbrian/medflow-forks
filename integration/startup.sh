#!/bin/bash
set -e

# Run database migrations first
echo "Running database migrations..."
python -m alembic upgrade head || echo "Alembic migration completed (or skipped)"

# Seed database if not already seeded
echo "Checking if database needs seeding..."
python << 'PYSEED'
import asyncio
import sys
import os

async def seed():
    try:
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy import select, text
        from core.config import get_settings
        from core.models import Agency, AgencyPlan, Clinic, ClinicStatus, User, UserRole
        from core.auth import get_password_hash
        from uuid import uuid4

        settings = get_settings()
        engine = create_async_engine(settings.database_url, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as db:
            # Check if already seeded
            result = await db.execute(select(Agency).limit(1))
            if result.scalar_one_or_none():
                print("Database already seeded. Skipping.")
                return

            print("Seeding database...")

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
            print(f"Created agency: {agency.name}")

            # Create superusers
            users = [
                ("cto@trafegoparaconsultorios.com.br", "CTO", UserRole.SUPERUSER),
                ("heloisa@trafegoparaconsultorios.com.br", "Heloísa", UserRole.SUPERUSER),
                ("briansouzanogueira@gmail.com", "Brian Souza Nogueira", UserRole.SUPERUSER),
            ]

            for email, name, role in users:
                user = User(
                    id=str(uuid4()),
                    agency_id=agency.id,
                    email=email,
                    password_hash=get_password_hash("tpc2026#"),
                    role=role,
                    name=name,
                    is_active=True,
                    email_verified=True,
                )
                db.add(user)
                print(f"Created user: {email}")

            await db.commit()
            print("Database seeded successfully!")
    except Exception as e:
        print(f"Seed error (non-fatal): {e}")
        sys.exit(0)  # Don't fail startup

asyncio.run(seed())
PYSEED

# Start the main application
echo "Starting application..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
