"""
MedFlow Integration Layer - Main Application.

Unified API that integrates:
- Twenty CRM
- Cal.com Scheduling
- Chatwoot Messaging
- AI Agents (content creation, lead qualification, etc.)
- Creative Studio
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print(f"Starting {settings.app_name} ({settings.app_env})")
    yield
    # Shutdown
    print("Shutting down")


app = FastAPI(
    title="MedFlow Integration API",
    description="Unified API for medical growth platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "integration"}


@app.get("/")
async def root():
    """Root endpoint - redirect to docs or dashboard."""
    return {
        "name": "MedFlow Integration API",
        "version": "1.0.0",
        "docs": "/docs",
        "services": {
            "crm": "/crm/",
            "agenda": "/agenda/",
            "inbox": "/inbox/",
            "api": "/api/",
        },
    }


# =============================================================================
# IMPORT ROUTES (lazy to avoid circular imports)
# =============================================================================

from api.routes import auth, clinics, agents, creative_lab, sync

# Auth & Users
app.include_router(auth.router, prefix="/api", tags=["Auth"])

# Clinics (multi-tenant)
app.include_router(clinics.router, prefix="/api", tags=["Clinics"])

# Agents (AI)
app.include_router(agents.router, prefix="/api", tags=["Agents"])

# Creative Studio
app.include_router(creative_lab.router, prefix="/api", tags=["Creative Lab"])

# Service Sync
app.include_router(sync.router, prefix="/api", tags=["Sync"])
