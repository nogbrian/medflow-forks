"""Webhook router that aggregates all webhook endpoints."""

from fastapi import APIRouter

from webhooks.evolution import router as evolution_router

router = APIRouter(tags=["Webhooks"])

# Include Evolution API webhooks
router.include_router(evolution_router)
