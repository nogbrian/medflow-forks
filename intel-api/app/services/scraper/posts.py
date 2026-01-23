"""Instagram posts/reels scraper using Apify."""

from typing import Optional

import structlog

from app.services.scraper.apify_client import scrape_posts
from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class PostsScraper:
    """Scrape Instagram posts and reels via Apify actors."""

    def __init__(self, session_cookie: Optional[str] = None):
        self.session_cookie = session_cookie

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def scrape(
        self,
        username: str,
        limit: int = 50,
        reels_only: bool = False,
        max_retries: int = 2,
    ) -> list[dict]:
        """Scrape posts/reels for a given username.

        Args:
            username: Instagram username
            limit: Maximum posts to retrieve
            reels_only: Only return reels (video clips)
            max_retries: Number of retry attempts

        Returns:
            List of post data dicts
        """
        for attempt in range(max_retries + 1):
            try:
                return await scrape_posts(
                    username=username,
                    limit=limit,
                    reels_only=reels_only,
                )
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(
                        "posts_scrape_retry",
                        username=username,
                        attempt=attempt + 1,
                        error=str(e),
                    )
                    continue
                logger.error(
                    "posts_scrape_failed",
                    username=username,
                    error=str(e),
                )
                raise
