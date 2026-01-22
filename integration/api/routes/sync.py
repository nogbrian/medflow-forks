"""
Service synchronization routes.

Handles syncing data between Twenty CRM, Cal.com, and Chatwoot.
Includes webhook endpoints with signature verification.
"""

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request
from pydantic import BaseModel

from core.auth import CurrentUser, DBSession, require_superuser
from core.config import get_settings
from services.sync_service import SyncService, verify_webhook_signature

router = APIRouter(prefix="/sync")
settings = get_settings()
logger = logging.getLogger(__name__)


class SyncClinicRequest(BaseModel):
    clinic_id: str
    services: list[str] = ["twenty", "calcom", "chatwoot"]


class WebhookSetupRequest(BaseModel):
    base_url: str


# =============================================================================
# SYNC OPERATIONS
# =============================================================================


@router.post("/clinic")
async def sync_clinic(
    data: SyncClinicRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Sync a clinic across all services.

    This will:
    - Create/update workspace in Twenty CRM
    - Create/update team in Cal.com
    - Create/update inbox in Chatwoot
    - Sync existing contacts bidirectionally
    """
    require_superuser(current_user)

    background_tasks.add_task(
        _run_clinic_sync,
        db,
        data.clinic_id,
        data.services,
    )

    return {
        "success": True,
        "message": f"Sync started for clinic {data.clinic_id}",
        "services": data.services,
    }


@router.post("/webhooks/setup")
async def setup_webhooks(
    data: WebhookSetupRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Register webhooks for all services.

    Call this once during initial setup to enable bidirectional sync.
    """
    require_superuser(current_user)

    sync = SyncService(db)
    try:
        results = await sync.setup_webhooks(data.base_url)
        return {
            "success": True,
            "results": results,
        }
    finally:
        await sync.close()


# =============================================================================
# TWENTY CRM WEBHOOKS
# =============================================================================


@router.post("/webhooks/twenty")
async def handle_twenty_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: DBSession,
    x_twenty_signature: str | None = Header(None, alias="X-Twenty-Signature"),
    x_twenty_webhook_signature: str | None = Header(None, alias="X-Twenty-Webhook-Signature"),
):
    """
    Handle webhooks from Twenty CRM.

    Events:
    - person.created / person.updated
    - company.created / company.updated
    - opportunity.created / opportunity.updated
    """
    body = await request.body()

    # Log all headers for debugging
    logger.info(f"Twenty webhook headers: {dict(request.headers)}")

    # Accept either header format that Twenty might use
    signature = x_twenty_webhook_signature or x_twenty_signature

    # Verify signature
    if settings.webhook_secret and settings.webhook_secret != "change-me-webhook-secret":
        if not signature:
            logger.warning("Twenty webhook missing signature (checked X-Twenty-Signature and X-Twenty-Webhook-Signature)")
            raise HTTPException(status_code=401, detail="Missing signature")

        if not verify_webhook_signature(body, signature, settings.webhook_secret):
            logger.warning("Twenty webhook signature verification failed")
            raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()
    event = payload.get("event", payload.get("type", ""))
    data = payload.get("data", payload)

    logger.info(f"Twenty webhook received: {event}")

    if event in ("person.created", "person.updated"):
        background_tasks.add_task(
            _sync_twenty_contact_to_chatwoot,
            db,
            data,
        )
    elif event == "opportunity.updated":
        background_tasks.add_task(
            _handle_opportunity_update,
            db,
            data,
        )

    return {"received": True, "event": event}


# =============================================================================
# CAL.COM WEBHOOKS
# =============================================================================


@router.post("/webhooks/calcom")
async def handle_calcom_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: DBSession,
    x_cal_signature_256: str | None = Header(None, alias="X-Cal-Signature-256"),
):
    """
    Handle webhooks from Cal.com.

    Events:
    - BOOKING_CREATED
    - BOOKING_RESCHEDULED
    - BOOKING_CANCELLED
    - MEETING_ENDED
    """
    body = await request.body()

    # Verify signature
    if settings.webhook_secret and settings.webhook_secret != "change-me-webhook-secret":
        if not x_cal_signature_256:
            logger.warning("Cal.com webhook missing signature")
            raise HTTPException(status_code=401, detail="Missing signature")

        if not verify_webhook_signature(body, x_cal_signature_256, settings.webhook_secret):
            logger.warning("Cal.com webhook signature verification failed")
            raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()
    event = payload.get("triggerEvent", "")
    booking = payload.get("payload", {})

    logger.info(f"Cal.com webhook received: {event}")

    if event == "BOOKING_CREATED":
        background_tasks.add_task(_sync_booking_to_twenty, db, booking)
        background_tasks.add_task(_notify_booking_chatwoot, db, booking, "created")
    elif event == "BOOKING_RESCHEDULED":
        background_tasks.add_task(_sync_booking_to_twenty, db, booking)
        background_tasks.add_task(_notify_booking_chatwoot, db, booking, "rescheduled")
    elif event == "BOOKING_CANCELLED":
        background_tasks.add_task(_sync_booking_to_twenty, db, booking)
        background_tasks.add_task(_notify_booking_chatwoot, db, booking, "cancelled")

    return {"received": True, "event": event}


# =============================================================================
# CHATWOOT WEBHOOKS
# =============================================================================


@router.post("/webhooks/chatwoot")
async def handle_chatwoot_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: DBSession,
    x_chatwoot_signature: str | None = Header(None, alias="X-Chatwoot-Signature"),
):
    """
    Handle webhooks from Chatwoot.

    Events:
    - message_created
    - conversation_created
    - conversation_status_changed
    - contact_created
    """
    body = await request.body()

    # Verify signature
    if settings.webhook_secret and settings.webhook_secret != "change-me-webhook-secret":
        if not x_chatwoot_signature:
            logger.warning("Chatwoot webhook missing signature")
            raise HTTPException(status_code=401, detail="Missing signature")

        if not verify_webhook_signature(body, x_chatwoot_signature, settings.webhook_secret):
            logger.warning("Chatwoot webhook signature verification failed")
            raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()
    event = payload.get("event", "")
    data = payload

    logger.info(f"Chatwoot webhook received: {event}")

    if event == "contact_created":
        background_tasks.add_task(
            _sync_chatwoot_contact_to_twenty,
            db,
            data.get("contact", data),
        )
    elif event == "message_created":
        # Route to AI agent if applicable
        background_tasks.add_task(
            _route_message_to_agent,
            db,
            data,
        )

    return {"received": True, "event": event}


# =============================================================================
# STATUS
# =============================================================================


@router.get("/status")
async def get_sync_status(current_user: CurrentUser):
    """Get status of all service connections."""
    return {
        "twenty": {
            "configured": bool(settings.twenty_api_key),
            "url": settings.twenty_api_url,
        },
        "calcom": {
            "configured": bool(settings.calcom_api_key),
            "url": settings.calcom_api_url,
        },
        "chatwoot": {
            "configured": bool(settings.chatwoot_api_key),
            "url": settings.chatwoot_api_url,
        },
        "webhook_secret_set": settings.webhook_secret != "change-me-webhook-secret",
    }


# =============================================================================
# BACKGROUND TASKS
# =============================================================================


async def _run_clinic_sync(
    db: DBSession,
    clinic_id: str,
    services: list[str],
) -> None:
    """Background task to sync clinic to services."""
    sync = SyncService(db)
    try:
        result = await sync.sync_clinic(clinic_id)
        logger.info(f"Clinic sync completed: {result}")
    except Exception as e:
        logger.error(f"Clinic sync failed: {e}")
    finally:
        await sync.close()


async def _sync_twenty_contact_to_chatwoot(
    db: DBSession,
    contact_data: dict[str, Any],
) -> None:
    """Sync a Twenty contact to Chatwoot."""
    sync = SyncService(db)
    try:
        await sync.sync_twenty_contact_to_chatwoot(contact_data)
    except Exception as e:
        logger.error(f"Contact sync to Chatwoot failed: {e}")
    finally:
        await sync.close()


async def _sync_chatwoot_contact_to_twenty(
    db: DBSession,
    contact_data: dict[str, Any],
) -> None:
    """Sync a Chatwoot contact to Twenty."""
    sync = SyncService(db)
    try:
        await sync.sync_chatwoot_contact_to_twenty(contact_data)
    except Exception as e:
        logger.error(f"Contact sync to Twenty failed: {e}")
    finally:
        await sync.close()


async def _sync_booking_to_twenty(
    db: DBSession,
    booking: dict[str, Any],
) -> None:
    """Sync a Cal.com booking to Twenty."""
    sync = SyncService(db)
    try:
        await sync.sync_calcom_booking_to_twenty(booking)
    except Exception as e:
        logger.error(f"Booking sync to Twenty failed: {e}")
    finally:
        await sync.close()


async def _notify_booking_chatwoot(
    db: DBSession,
    booking: dict[str, Any],
    event_type: str,
) -> None:
    """Send booking notification to Chatwoot."""
    sync = SyncService(db)
    try:
        await sync.send_booking_notification_to_chatwoot(booking, event_type)
    except Exception as e:
        logger.error(f"Booking notification failed: {e}")
    finally:
        await sync.close()


async def _handle_opportunity_update(
    db: DBSession,
    opportunity: dict[str, Any],
) -> None:
    """Handle opportunity stage changes for automation."""
    stage = opportunity.get("stage", "")

    # Trigger actions based on stage
    if stage == "QUALIFIED":
        # Lead qualified - could trigger SDR agent or calendar invite
        logger.info(f"Opportunity {opportunity.get('id')} qualified - triggering automation")
        # TODO: Integrate with agent orchestration

    elif stage == "PROPOSAL":
        # Send proposal via Chatwoot
        logger.info(f"Opportunity {opportunity.get('id')} in proposal stage")


async def _route_message_to_agent(
    db: DBSession,
    message_data: dict[str, Any],
) -> None:
    """Route incoming Chatwoot message to appropriate AI agent."""
    # Skip outgoing messages and private notes
    message = message_data.get("message", message_data)
    if message.get("message_type") != "incoming":
        return

    content = message.get("content", "")
    conversation = message_data.get("conversation", {})
    inbox = conversation.get("inbox", {})

    # Check if this inbox has AI enabled
    inbox_settings = inbox.get("additional_attributes", {})
    if not inbox_settings.get("ai_enabled", True):
        return

    logger.info(f"Routing message to agent: {content[:50]}...")

    # TODO: Integrate with agent coordinator
    # from agents.coordinator import AgentCoordinator
    # coordinator = AgentCoordinator(db, clinic_id)
    # response = await coordinator.process_message(content, conversation_id)
    # if response:
    #     sync = SyncService(db)
    #     await chatwoot.send_message(conversation['id'], response.content)
