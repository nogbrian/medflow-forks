"""Admin routes for database management."""

from uuid import uuid4

from fastapi import APIRouter, HTTPException

from core.auth import DBSession, get_password_hash
from core.models import Agency, AgencyPlan, User, UserRole
from sqlalchemy import select, text

router = APIRouter(prefix="/admin")


@router.get("/db-status")
async def db_status(db: DBSession):
    """Check database status and tables."""
    try:
        # Check if we can connect
        await db.execute(text("SELECT 1"))

        # Check if tables exist
        tables_result = await db.execute(
            text(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
            )
        )
        tables = [row[0] for row in tables_result.fetchall()]

        # Check alembic version
        alembic_version = None
        if "alembic_version" in tables:
            ver_result = await db.execute(
                text("SELECT version_num FROM alembic_version")
            )
            row = ver_result.fetchone()
            alembic_version = row[0] if row else None

        # Count records
        counts = {}
        for table in ["agencies", "clinics", "users"]:
            if table in tables:
                count_result = await db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                counts[table] = count_result.scalar()
            else:
                counts[table] = "table not found"

        return {
            "status": "connected",
            "tables": tables,
            "alembic_version": alembic_version,
            "counts": counts,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/seed")
async def seed_database(db: DBSession):
    """Seed the database with initial data."""
    try:
        # Check if already seeded
        result = await db.execute(select(Agency).limit(1))
        if result.scalar_one_or_none():
            return {"status": "already_seeded", "message": "Database already has data"}

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
        superusers = [
            ("cto@trafegoparaconsultorios.com.br", "CTO"),
            ("heloisa@trafegoparaconsultorios.com.br", "Heloísa"),
            ("briansouzanogueira@gmail.com", "Brian Souza Nogueira"),
        ]

        created_users = []
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
            created_users.append(email)

        await db.commit()

        return {
            "status": "success",
            "agency": agency.name,
            "users_created": created_users,
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-migrations")
async def run_migrations():
    """Run alembic migrations."""
    import subprocess

    try:
        result = subprocess.run(
            ["python", "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return {
            "status": "success" if result.returncode == 0 else "error",
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
