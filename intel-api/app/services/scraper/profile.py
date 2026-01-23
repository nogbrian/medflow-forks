"""Instagram profile scraper using Apify."""

from typing import Optional

import structlog

from app.services.scraper.apify_client import scrape_profile
from app.services.scraper.exceptions import ProfileNotFoundError

logger = structlog.get_logger()


class ProfileScraper:
    """Scrape Instagram profile data via Apify actors."""

    def __init__(self, session_cookie: Optional[str] = None):
        self.session_cookie = session_cookie

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def scrape(self, username: str, max_retries: int = 2) -> dict:
        """Scrape profile data for a given username.

        Args:
            username: Instagram username (without @)
            max_retries: Number of retry attempts

        Returns:
            Profile data dict

        Raises:
            ProfileNotFoundError: If profile doesn't exist
        """
        for attempt in range(max_retries + 1):
            try:
                data = await scrape_profile(username)
                if not data:
                    raise ProfileNotFoundError(username)
                return data
            except ProfileNotFoundError:
                raise
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(
                        "profile_scrape_retry",
                        username=username,
                        attempt=attempt + 1,
                        error=str(e),
                    )
                    continue
                logger.error(
                    "profile_scrape_failed",
                    username=username,
                    error=str(e),
                )
                raise
