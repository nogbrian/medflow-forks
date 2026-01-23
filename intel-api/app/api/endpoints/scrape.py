from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models import get_db
from app.schemas.scrape import TriggerScrapeRequest, TriggerScrapeResponse
from app.services.database import DatabaseService
from app.services.orchestrator import orchestrator

logger = structlog.get_logger()

router = APIRouter()


@router.post("/instagram-orchestrator", response_model=TriggerScrapeResponse)
async def trigger_scrape(
    request: TriggerScrapeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger Instagram scraping workflow.

    This endpoint replaces the n8n webhook and handles:
    - Profile scraping (new or existing profiles)
    - Posts scraping
    - Reels scraping

    The scraping runs as a background task and returns immediately with a scrape_run_id.
    """
    logger.info(
        "scrape_triggered",
        action=request.action,
        username=request.username,
        profile_id=request.profile_id,
    )

    db_service = DatabaseService(db)

    try:
        # Determine the profile_id
        profile_id = request.profile_id

        if request.username and not request.profile_id:
            # New profile - need to scrape and create it first
            logger.info("creating_new_profile", username=request.username)
            profile_id = await orchestrator.ensure_profile(
                username=request.username,
                workspace_id=request.workspace_id,
                session_cookie=request.session_cookie,
            )

        if not profile_id:
            raise HTTPException(
                status_code=400,
                detail="Could not determine profile_id"
            )

        # Verify profile exists
        profile = await db_service.get_profile(profile_id)
        if not profile:
            raise HTTPException(
                status_code=404,
                detail=f"Profile {profile_id} not found"
            )

        # Create scrape run record
        scrape_run_id = await db_service.create_scrape_run(profile_id, request.action)

        # Start background scraping task
        background_tasks.add_task(
            orchestrator.run_scrape,
            scrape_run_id=scrape_run_id,
            profile_id=profile_id,
            action=request.action,
            session_cookie=request.session_cookie,
        )

        logger.info(
            "scrape_started",
            scrape_run_id=scrape_run_id,
            profile_id=profile_id,
            action=request.action,
        )

        return TriggerScrapeResponse(
            success=True,
            scrape_run_id=scrape_run_id,
            profile_id=profile_id,
            action=request.action,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("scrape_trigger_failed", error=str(e))
        return TriggerScrapeResponse(
            success=False,
            error=str(e),
        )
