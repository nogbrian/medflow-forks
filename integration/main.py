"""
MedFlow Integration Layer - Simplified Main Application for debugging.
Build: 2026-01-22T07:00:00Z - forced rebuild
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Callable
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from starlette.middleware.base import BaseHTTPMiddleware

from core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        logger.info(f"{request.method} {request.url.path} - {response.status_code} ({duration:.3f}s)")
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting MedFlow Integration API (simplified)")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="MedFlow Integration API",
    version="3.1.0",
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "env": settings.app_env,
        "version": "3.1.0",
        "build": "20260122-debug"
    }


@app.get("/")
async def root():
    return {
        "name": "MedFlow Integration API",
        "version": "3.1.0",
        "status": "ok"
    }


class SeedRequest(BaseModel):
    password: str = "tpc2026#"


@app.post("/api/admin/seed")
async def seed_database(data: SeedRequest):
    """Seed the database with initial data."""
    try:
        engine = create_async_engine(settings.database_url, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as db:
            # Check if tables exist
            tables_result = await db.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            )
            tables = [row[0] for row in tables_result.fetchall()]

            if "agencies" not in tables:
                return {"status": "error", "message": "Tables not found. Run migrations first.", "tables": tables}

            # Check if already seeded
            check_result = await db.execute(text("SELECT COUNT(*) FROM agencies"))
            count = check_result.scalar()
            if count > 0:
                return {"status": "already_seeded", "message": "Database already has agencies"}

            # Create agency
            agency_id = str(uuid4())
            await db.execute(
                text("""
                    INSERT INTO agencies (id, name, slug, email, phone, plan, max_clinics, branding, settings, created_at, updated_at)
                    VALUES (:id, :name, :slug, :email, :phone, 'enterprise', 100, :branding, :settings, NOW(), NOW())
                """),
                {
                    "id": agency_id,
                    "name": "Tráfego para Consultórios",
                    "slug": "tpc",
                    "email": "contato@trafegoparaconsultorios.com.br",
                    "phone": "+55 11 99999-0000",
                    "branding": '{"logo_url": null, "primary_color": "#F24E1E", "secondary_color": "#111111", "company_name": "Tráfego para Consultórios"}',
                    "settings": '{"default_language": "pt-BR", "timezone": "America/Sao_Paulo"}',
                }
            )

            # Create superusers
            # Truncate password to 72 bytes (bcrypt limit)
            safe_password = data.password[:72] if data.password else "tpc2026#"
            password_hash = pwd_context.hash(safe_password)
            users = [
                ("cto@trafegoparaconsultorios.com.br", "CTO"),
                ("heloisa@trafegoparaconsultorios.com.br", "Heloísa"),
                ("briansouzanogueira@gmail.com", "Brian Souza Nogueira"),
            ]

            created_users = []
            for email, name in users:
                user_id = str(uuid4())
                await db.execute(
                    text("""
                        INSERT INTO users (id, agency_id, email, password_hash, role, name, is_active, email_verified, created_at, updated_at)
                        VALUES (:id, :agency_id, :email, :password_hash, 'superuser', :name, true, true, NOW(), NOW())
                    """),
                    {
                        "id": user_id,
                        "agency_id": agency_id,
                        "email": email,
                        "password_hash": password_hash,
                        "name": name,
                    }
                )
                created_users.append(email)

            await db.commit()

            return {
                "status": "success",
                "agency_id": agency_id,
                "users_created": created_users,
            }
    except Exception as e:
        logger.exception("Seed error")
        return {"status": "error", "message": str(e)}


@app.get("/api/admin/db-status")
async def db_status():
    """Check database status."""
    try:
        engine = create_async_engine(settings.database_url, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as db:
            await db.execute(text("SELECT 1"))

            tables_result = await db.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            )
            tables = [row[0] for row in tables_result.fetchall()]

            counts = {}
            for table in ["agencies", "clinics", "users"]:
                if table in tables:
                    count_result = await db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    counts[table] = count_result.scalar()
                else:
                    counts[table] = "table not found"

            alembic_version = None
            if "alembic_version" in tables:
                ver_result = await db.execute(text("SELECT version_num FROM alembic_version"))
                row = ver_result.fetchone()
                alembic_version = row[0] if row else None

            return {
                "status": "connected",
                "tables": tables,
                "alembic_version": alembic_version,
                "counts": counts,
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/admin/run-migrations")
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
        return {"status": "error", "message": str(e)}


@app.post("/api/admin/reset-db")
async def reset_db():
    """Reset database - drop all tables and reset alembic version."""
    try:
        engine = create_async_engine(settings.database_url, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as db:
            # Get all tables
            tables_result = await db.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            )
            tables = [row[0] for row in tables_result.fetchall()]

            dropped = []
            for table in tables:
                await db.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                dropped.append(table)

            await db.commit()

            return {
                "status": "success",
                "dropped_tables": dropped,
            }
    except Exception as e:
        logger.exception("Reset DB error")
        return {"status": "error", "message": str(e)}


# Import auth routes (we know these work)
try:
    from api.routes.auth import router as auth_router
    app.include_router(auth_router, prefix="/api", tags=["Auth"])
    logger.info("Auth routes loaded")
except Exception as e:
    logger.error(f"Failed to load auth routes: {e}")
