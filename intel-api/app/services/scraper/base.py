"""Base scraper interface using Apify SDK.

Provides a unified interface for scraping operations.
All scraping is delegated to Apify cloud actors.
"""

from typing import Optional

import structlog

from app.services.scraper.apify_client import scrape_profile, scrape_posts
from app.services.scraper.exceptions import ProfileNotFoundError

logger = structlog.get_logger()


class InstagramScraper:
    """Instagram scraper using Apify cloud actors.

    No local browser needed — all scraping runs on Apify's infrastructure.
    """

    def __init__(self, session_cookie: Optional[str] = None):
        # session_cookie kept for interface compatibility but not used with Apify
        self.session_cookie = session_cookie

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
