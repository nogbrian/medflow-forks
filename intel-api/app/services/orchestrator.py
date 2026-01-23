"""Scraping orchestrator with proper error handling."""

from typing import Optional
import structlog

from app.models import async_session_maker
from app.services.database import DatabaseService
from app.services.scraper import (
    ProfileScraper,
    PostsScraper,
    AuthenticationExpiredError,
    RateLimitError,
    ProfileNotFoundError,
    AgeRestrictionError,
)
from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class ScrapeOrchestrator:
    """Orchestrates the scraping workflow."""

    async def ensure_profile(
        self,
        username: str,
        workspace_id: str,
        session_cookie: Optional[str] = None,
    ) -> str:
        """Ensure a profile exists in the database, creating it if necessary."""
        async with async_session_maker() as session:
            db_service = DatabaseService(session)

            # Check if profile already exists
            existing = await db_service.get_profile_by_username(workspace_id, username)
            if existing:
                logger.info("profile_exists", username=username, profile_id=str(existing.id))
                return str(existing.id)

            # Scrape profile data
            logger.info("scraping_new_profile", username=username)
            async with ProfileScraper(session_cookie) as scraper:
                profile_data = await scraper.scrape(username)

            # Save profile
            profile_id = await db_service.upsert_profile(workspace_id, profile_data)
            return profile_id

    async def run_scrape(
        self,
        scrape_run_id: str,
        profile_id: str,
        action: str,
        session_cookie: Optional[str] = None,
    ) -> None:
        """Run the complete scraping workflow as a background task."""
        async with async_session_maker() as session:
            db_service = DatabaseService(session)

            try:
                # Get profile
                profile = await db_service.get_profile(profile_id)
                if not profile:
                    raise ValueError(f"Profile {profile_id} not found")

                username = profile.username
                posts_count = 0
                reels_count = 0

                # Scrape profile if needed
                if action in ("full", "profile_only"):
                    logger.info("scraping_profile_data", username=username, action=action)
                    async with ProfileScraper(session_cookie) as scraper:
                        profile_data = await scraper.scrape(username)
                        await db_service.upsert_profile(str(profile.workspace_id), profile_data)

                # Scrape posts if needed
                if action in ("full", "posts_only"):
                    logger.info("scraping_posts", username=username, action=action)
                    async with PostsScraper(session_cookie) as scraper:
                        posts = await scraper.scrape(
                            username,
                            limit=settings.max_posts_per_scrape,
                            reels_only=False
                        )

                        for post in posts:
                            if not post.get("is_reel"):
                                await db_service.upsert_post(profile_id, post)
                                posts_count += 1

                        logger.info("posts_saved", username=username, count=posts_count)

                # Scrape reels if needed
                if action in ("full", "reels_only"):
                    logger.info("scraping_reels", username=username, action=action)
                    async with PostsScraper(session_cookie) as scraper:
                        reels = await scraper.scrape(
                            username,
                            limit=settings.max_reels_per_scrape,
                            reels_only=True
                        )

                        for reel in reels:
                            reel["is_reel"] = True
                            await db_service.upsert_post(profile_id, reel)
                            reels_count += 1

                        logger.info("reels_saved", username=username, count=reels_count)

                # Complete the scrape run
                await db_service.complete_scrape_run(scrape_run_id, posts_count, reels_count)
                logger.info("scrape_completed", scrape_run_id=scrape_run_id, posts=posts_count, reels=reels_count)

            except AuthenticationExpiredError as e:
                # Special status for expired cookies - frontend can notify user
                logger.warning("scrape_auth_expired", scrape_run_id=scrape_run_id, error=str(e))
                await db_service.fail_scrape_run_with_status(
                    scrape_run_id,
                    status="auth_expired",
                    error_message="Session cookie has expired. Please update your Instagram cookie."
                )

            except RateLimitError as e:
                logger.warning("scrape_rate_limited", scrape_run_id=scrape_run_id, error=str(e))
                await db_service.fail_scrape_run_with_status(
                    scrape_run_id,
                    status="rate_limited",
                    error_message=f"Rate limited by Instagram. Retry after {e.retry_after} seconds."
                )

            except ProfileNotFoundError as e:
                logger.warning("scrape_profile_not_found", scrape_run_id=scrape_run_id, error=str(e))
                await db_service.fail_scrape_run(scrape_run_id, f"Profile not found: {e.username}")

            except AgeRestrictionError as e:
                logger.warning("scrape_age_restricted", scrape_run_id=scrape_run_id, error=str(e))
                await db_service.fail_scrape_run_with_status(
                    scrape_run_id,
                    status="age_restricted",
                    error_message=f"Profile requires {e.min_age}+ age verification. Please provide a valid session cookie."
                )

            except Exception as e:
                logger.error("scrape_failed", scrape_run_id=scrape_run_id, error=str(e))
                await db_service.fail_scrape_run(scrape_run_id, str(e))
                raise


# Singleton instance
orchestrator = ScrapeOrchestrator()
