"""API route for dashboard metrics - aggregates data from CRM, Chatwoot, Cal.com."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends

from api.deps import require_auth
from core.logging import get_logger
from tools.crm import listar_leads
from tools.calendar import get_calcom_service
from tools.chatwoot import get_chatwoot_service

logger = get_logger(__name__)
router = APIRouter(prefix="/dashboard", tags=["Dashboard"], dependencies=[Depends(require_auth)])


@router.get("/metrics")
async def get_metrics() -> dict:
    """
    Get aggregated dashboard metrics.

    Returns leads count, upcoming bookings, active conversations, and conversion rate.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    month_start = datetime.now().replace(day=1).strftime("%Y-%m-%d")

    # Fetch data from all sources in parallel-safe manner
    leads_total = 0
    bookings_count = 0
    conversations_active = 0

    try:
        leads = await listar_leads(limite=200)
        leads_total = len(leads)
    except Exception as e:
        logger.error("Failed to fetch leads for dashboard", error=str(e))

    try:
        calendar = get_calcom_service()
        bookings = await calendar.listar_agendamentos(
            date_from=today,
            date_to=(datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        )
        bookings_count = len(bookings)
    except Exception as e:
        logger.error("Failed to fetch bookings for dashboard", error=str(e))

    try:
        chatwoot = get_chatwoot_service()
        result = await chatwoot._request(
            method="GET",
            endpoint="/conversations",
            params={"status": "open", "page": 1},
        )
        meta = result.get("data", {}).get("meta", result.get("meta", {}))
        conversations_active = meta.get("all_count", 0)
    except Exception as e:
        logger.error("Failed to fetch conversations for dashboard", error=str(e))

    # Conversion rate: bookings / leads (simplified)
    conversion_rate = 0.0
    if leads_total > 0:
        conversion_rate = round((bookings_count / leads_total) * 100, 1)

    return {
        "leads_total": leads_total,
        "bookings_upcoming": bookings_count,
        "conversations_active": conversations_active,
        "conversion_rate": conversion_rate,
        "period": {
            "start": month_start,
            "end": today,
        },
    }


@router.get("/recent-leads")
async def get_recent_leads() -> dict:
    """Get the 10 most recent leads for the dashboard table."""
    try:
        leads = await listar_leads(limite=10)
        return {"data": leads}
    except Exception as e:
        logger.error("Failed to fetch recent leads", error=str(e))
        return {"data": []}


@router.get("/upcoming-bookings")
async def get_upcoming_bookings() -> dict:
    """Get today's upcoming bookings for the dashboard sidebar."""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        calendar = get_calcom_service()
        bookings = await calendar.listar_agendamentos(
            date_from=today,
            date_to=tomorrow,
        )
        return {"data": bookings}
    except Exception as e:
        logger.error("Failed to fetch upcoming bookings", error=str(e))
        return {"data": []}
