"""
MedFlow Integration Layer - Main Application.

Unified API that integrates:
- Twenty CRM
- Cal.com Scheduling
- Chatwoot Messaging
- AI Agents (content creation, lead qualification, etc.)
- Creative Studio
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.is_production else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


# =============================================================================
# SECURITY MIDDLEWARE
# =============================================================================


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Remove server header
        if "server" in response.headers:
            del response.headers["server"]

        # Content Security Policy for API
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests with timing."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Generate request ID
        request_id = request.headers.get("X-Request-ID", f"req-{int(start_time * 1000)}")

        # Log request
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"client={request.client.host if request.client else 'unknown'}"
        )

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Log response
            logger.info(
                f"[{request_id}] {request.method} {request.url.path} "
                f"status={response.status_code} duration={duration:.3f}s"
            )

            # Add timing header
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration:.3f}s"

            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"[{request_id}] {request.method} {request.url.path} "
                f"error={str(e)} duration={duration:.3f}s"
            )
            raise


# =============================================================================
# APPLICATION SETUP
# =============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info(f"Starting {settings.app_name} ({settings.app_env})")

    # Validate critical settings
    if settings.jwt_secret == "change-me-jwt-secret":
        logger.warning("WARNING: Using default JWT secret. Set JWT_SECRET in production!")

    if settings.webhook_secret == "change-me-webhook-secret":
        logger.warning("WARNING: Using default webhook secret. Set WEBHOOK_SECRET in production!")

    yield

    # Shutdown
    logger.info("Shutting down")


app = FastAPI(
    title="MedFlow Integration API",
    description="Unified API for medical growth platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    # Disable automatic OpenAPI in production for security
    openapi_url="/openapi.json" if settings.is_development else None,
)


# Add middleware (order matters - first added = last executed)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# CORS - configured per environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID", "X-Response-Time"],
)


# =============================================================================
# ERROR HANDLERS
# =============================================================================


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler - don't leak internal errors."""
    logger.exception(f"Unhandled error: {exc}")

    if settings.is_development:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "type": type(exc).__name__},
        )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# =============================================================================
# HEALTH & STATUS
# =============================================================================


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "env": settings.app_env, "version": "2.0.0"}


@app.get("/")
async def root():
    """Root endpoint - service info."""
    return {
        "name": "MedFlow Integration API",
        "version": "1.0.0",
        "environment": settings.app_env,
        "docs": "/docs" if settings.is_development else None,
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

logger.info("Starting route imports...")

# Import routes directly to avoid __init__.py issues
try:
    from api.routes.auth import router as auth_router
    logger.info("auth_router imported successfully")
except Exception as e:
    logger.error(f"Failed to import auth_router: {e}")
    raise

try:
    from api.routes.admin import router as admin_router
    logger.info("admin_router imported successfully")
except Exception as e:
    logger.error(f"Failed to import admin_router: {e}")
    raise

try:
    from api.routes.clinics import router as clinics_router
    logger.info("clinics_router imported successfully")
except Exception as e:
    logger.error(f"Failed to import clinics_router: {e}")
    raise

# Auth & Users
app.include_router(auth_router, prefix="/api", tags=["Auth"])

# Admin (database management)
app.include_router(admin_router, prefix="/api", tags=["Admin"])

# Clinics (multi-tenant)
app.include_router(clinics_router, prefix="/api", tags=["Clinics"])

# Other routes - import on demand to avoid issues
try:
    from api.routes.agents import router as agents_router
    app.include_router(agents_router, prefix="/api", tags=["Agents"])
except Exception as e:
    logger.error(f"Failed to import agents router: {e}")

try:
    from api.routes.creative_lab import router as creative_lab_router
    app.include_router(creative_lab_router, prefix="/api", tags=["Creative Lab"])
except Exception as e:
    logger.error(f"Failed to import creative_lab router: {e}")

try:
    from api.routes.sync import router as sync_router
    app.include_router(sync_router, prefix="/api", tags=["Sync"])
except Exception as e:
    logger.error(f"Failed to import sync router: {e}")

try:
    from api.routes.navigation import router as navigation_router
    app.include_router(navigation_router, prefix="/api", tags=["Navigation"])
except Exception as e:
    logger.error(f"Failed to import navigation router: {e}")

try:
    from api.routes.branding import router as branding_router
    app.include_router(branding_router, prefix="/api", tags=["Branding"])
except Exception as e:
    logger.error(f"Failed to import branding router: {e}")
