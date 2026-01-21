"""
Service synchronization routes.

Handles syncing data between Twenty CRM, Cal.com, and Chatwoot.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from core.auth import CurrentUser, DBSession, require_superuser
from core.config import get_settings

router = APIRouter(prefix="/sync")
settings = get_settings()


class SyncClinicRequest(BaseModel):
    clinic_id: str
    services: list[str] = ["twenty", "calcom", "chatwoot"]


class WebhookPayload(BaseModel):
    event: str
    source: str
    data: dict


@router.post("/clinic")
async def sync_clinic(
    data: SyncClinicRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = None,
    db: DBSession = None,
):
    """
    Sync a clinic across all services.

    This will:
    - Create/update workspace in Twenty CRM
    - Create/update team in Cal.com
    - Create/update inbox in Chatwoot
    """
    require_superuser(current_user)

    # TODO: Implement actual sync
    background_tasks.add_task(
        _sync_clinic_to_services,
        data.clinic_id,
        data.services,
    )

    return {
        "success": True,
        "message": f"Sync started for clinic {data.clinic_id}",
        "services": data.services,
    }


@router.post("/webhooks/twenty")
async def handle_twenty_webhook(
    payload: WebhookPayload,
    db: DBSession = None,
):
    """
    Handle webhooks from Twenty CRM.

    Events:
    - contact.created
    - contact.updated
    - opportunity.created
    - opportunity.stage_changed
    """
    event = payload.event
    data = payload.data

    # TODO: Process webhook
    if event == "contact.created":
        # Sync to Chatwoot as contact
        pass
    elif event == "opportunity.stage_changed":
        # Trigger agent actions
        pass

    return {"received": True, "event": event}


@router.post("/webhooks/calcom")
async def handle_calcom_webhook(
    payload: WebhookPayload,
    db: DBSession = None,
):
    """
    Handle webhooks from Cal.com.

    Events:
    - BOOKING_CREATED
    - BOOKING_RESCHEDULED
    - BOOKING_CANCELLED
    """
    event = payload.event
    data = payload.data

    # TODO: Process webhook
    if event == "BOOKING_CREATED":
        # Create/update in Twenty CRM
        # Send confirmation via Chatwoot
        pass

    return {"received": True, "event": event}


@router.post("/webhooks/chatwoot")
async def handle_chatwoot_webhook(
    payload: WebhookPayload,
    db: DBSession = None,
):
    """
    Handle webhooks from Chatwoot.

    Events:
    - message_created
    - conversation_created
    - conversation_status_changed
    """
    event = payload.event
    data = payload.data

    # TODO: Process webhook
    if event == "message_created":
        # Route to appropriate agent
        # Update contact in Twenty CRM
        pass

    return {"received": True, "event": event}


@router.get("/status")
async def get_sync_status(
    current_user: CurrentUser = None,
):
    """Get status of all service connections."""
    return {
        "twenty": {
            "connected": bool(settings.twenty_api_key),
            "url": settings.twenty_api_url,
        },
        "calcom": {
            "connected": bool(settings.calcom_api_key),
            "url": settings.calcom_api_url,
        },
        "chatwoot": {
            "connected": bool(settings.chatwoot_api_key),
            "url": settings.chatwoot_api_url,
        },
    }


async def _sync_clinic_to_services(clinic_id: str, services: list[str]):
    """Background task to sync clinic to services."""
    # TODO: Implement actual sync logic
    pass
