from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
import structlog

from app.api.router import api_router
from app.config import get_settings
from app.models.base import engine, Base
from app.models import *  # noqa: F401,F403 — import all models for create_all

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()
settings = get_settings()


async def verify_database_connection() -> bool:
    """Test database connection on startup."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("database_connection_verified")
        return True
    except Exception as e:
        logger.error("database_connection_failed", error=str(e))
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("application_starting", debug=settings.debug)

    db_ok = await verify_database_connection()
    if not db_ok:
        logger.error("startup_failed", reason="database_connection_failed")
        raise RuntimeError("Failed to connect to database")

    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database_tables_ensured")

    logger.info("application_started")

    yield

    logger.info("application_shutdown")


app = FastAPI(
    title="Intel - Viral Finder API",
    description="Instagram intelligence and ads transparency backend",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS is handled by Traefik in production; this allows local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://intel.trafegoparaconsultorios.com.br",
        "https://medflow.trafegoparaconsultorios.com.br",
        "http://localhost:3002",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "intel-api"}
