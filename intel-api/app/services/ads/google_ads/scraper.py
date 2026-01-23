"""Google Ads Transparency Center scraper using Apify.

Uses Apify cloud actors to scrape the Google Ads Transparency Center.
"""

import structlog
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.config import get_settings
from app.models import async_session_maker, Advertiser, Ad, AdCreative
from app.services.scraper.apify_client import scrape_google_ads

logger = structlog.get_logger(__name__)


class GoogleAdsScraperError(Exception):
    """Base exception for Google Ads scraper errors."""
    pass


class GoogleAdsRateLimitError(GoogleAdsScraperError):
    """Rate limit detected."""
    pass


class GoogleAdsScraper:
    """Scraper for Google Ads Transparency Center via Apify."""

    def __init__(self):
        settings = get_settings()
        self.max_results = settings.google_ads_max_results

    async def search_ads(
        self,
        advertiser_name: Optional[str] = None,
        advertiser_id: Optional[str] = None,
        domain: Optional[str] = None,
        region: str = "BR",
        date_range: str = "LAST_30_DAYS",
        ad_format: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict]:
        """Search Google Ads Transparency Center via Apify.

        Args:
            advertiser_name: Advertiser name to search
            advertiser_id: Google advertiser ID (direct lookup)
            domain: Website domain to search
            region: ISO country code
            date_range: LAST_7_DAYS, LAST_30_DAYS, LAST_90_DAYS, ALL_TIME
            ad_format: TEXT, IMAGE, or VIDEO
            limit: Max ads to return

        Returns:
            List of ad data dictionaries
        """
        logger.info(
            "google_ads_search_start",
            advertiser_name=advertiser_name,
            domain=domain,
            region=region,
        )

        try:
            result = await scrape_google_ads(
                advertiser_name=advertiser_name or advertiser_id,
                domain=domain,
                region=region,
                limit=limit,
            )

            ads = result.get("ads", [])
            logger.info("google_ads_search_done", ads_found=len(ads))
            return ads

        except RuntimeError as e:
            if "APIFY_TOKEN" in str(e):
                raise GoogleAdsScraperError("APIFY_TOKEN not configured")
            raise GoogleAdsScraperError(str(e))
        except Exception as e:
            logger.error("google_ads_search_error", error=str(e))
            raise GoogleAdsScraperError(str(e))

    async def save_ads_to_db(self, ads: list[dict], workspace_id: UUID) -> tuple[int, int]:
        """Save scraped ads to database.

        Returns:
            Tuple of (ads_saved, advertisers_found)
        """
        ads_saved = 0
        advertisers_cache: dict[str, UUID] = {}

        async with async_session_maker() as session:
            for ad_data in ads:
                try:
                    google_advertiser_id = ad_data.get("advertiser_platform_id")
                    if not google_advertiser_id:
                        continue

                    # Get or create advertiser
                    if google_advertiser_id not in advertisers_cache:
                        advertiser = await self._get_or_create_advertiser(
                            session,
                            google_advertiser_id,
                            ad_data.get("advertiser_name", "Unknown"),
                        )
                        advertisers_cache[google_advertiser_id] = advertiser.id

                    advertiser_id = advertisers_cache[google_advertiser_id]

                    ad = Ad(
                        advertiser_id=advertiser_id,
                        platform="google",
                        platform_ad_id=ad_data.get("platform_ad_id"),
                        title=ad_data.get("title"),
                        body_text=ad_data.get("body_text"),
                        link_url=ad_data.get("link_url"),
                        ad_type=ad_data.get("ad_type", "text"),
                        status="active",
                        started_at=ad_data.get("started_at"),
                        ended_at=ad_data.get("ended_at"),
                    )
                    session.add(ad)
                    ads_saved += 1

                except Exception as e:
                    logger.error("google_ad_save_error", error=str(e))
                    continue

            await session.commit()

        return ads_saved, len(advertisers_cache)

    async def _get_or_create_advertiser(
        self,
        session,
        google_advertiser_id: str,
        name: str,
    ) -> Advertiser:
        """Get existing advertiser or create new one."""
        from sqlalchemy import select

        result = await session.execute(
            select(Advertiser).where(
                Advertiser.platform == "google",
                Advertiser.platform_id == google_advertiser_id,
            )
        )
        advertiser = result.scalar_one_or_none()

        if advertiser:
            if advertiser.name != name and name != "Unknown":
                advertiser.name = name
                advertiser.updated_at = datetime.utcnow()
            return advertiser

        advertiser = Advertiser(
            platform="google",
            platform_id=google_advertiser_id,
            name=name,
            page_url=f"https://adstransparency.google.com/advertiser/{google_advertiser_id}",
        )
        session.add(advertiser)
        await session.flush()

        return advertiser
