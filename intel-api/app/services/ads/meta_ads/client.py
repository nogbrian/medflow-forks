"""Meta Ad Library API client.

Uses the official Facebook Graph API to fetch ads from Meta's Ad Library.
API docs: https://developers.facebook.com/docs/marketing-api/reference/ads_archive/
"""

import httpx
import structlog
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.config import get_settings
from app.models import async_session_maker, Advertiser, Ad, AdCreative

logger = structlog.get_logger(__name__)


class MetaAdLibraryError(Exception):
    """Base exception for Meta Ad Library errors."""
    pass


class MetaApiRateLimitError(MetaAdLibraryError):
    """Rate limit reached."""
    def __init__(self, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(f"Rate limit reached. Retry after {retry_after} seconds")


class MetaApiAuthError(MetaAdLibraryError):
    """Invalid or expired access token."""
    pass


class MetaAdLibraryClient:
    """Client for Meta Ad Library API."""

    BASE_URL = "https://graph.facebook.com"

    # Ad Library API fields
    AD_FIELDS = [
        "id",
        "ad_creation_time",
        "ad_creative_bodies",
        "ad_creative_link_captions",
        "ad_creative_link_descriptions",
        "ad_creative_link_titles",
        "ad_delivery_start_time",
        "ad_delivery_stop_time",
        "ad_snapshot_url",
        "bylines",
        "currency",
        "delivery_by_region",
        "demographic_distribution",
        "estimated_audience_size",
        "impressions",
        "languages",
        "page_id",
        "page_name",
        "publisher_platforms",
        "spend",
        "target_ages",
        "target_gender",
        "target_locations",
    ]

    def __init__(self, access_token: Optional[str] = None):
        settings = get_settings()
        self.access_token = access_token or settings.meta_access_token
        self.api_version = settings.meta_api_version
        self.ads_per_request = settings.meta_ads_per_request

        if not self.access_token:
            raise MetaApiAuthError("META_ACCESS_TOKEN is required")

    @property
    def _api_url(self) -> str:
        return f"{self.BASE_URL}/{self.api_version}"

    async def _make_request(
        self,
        endpoint: str,
        params: dict,
    ) -> dict:
        """Make authenticated request to Meta Graph API."""
        params["access_token"] = self.access_token

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self._api_url}/{endpoint}", params=params)

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                raise MetaApiRateLimitError(retry_after)

            if response.status_code == 401 or response.status_code == 403:
                data = response.json()
                error_msg = data.get("error", {}).get("message", "Authentication failed")
                raise MetaApiAuthError(error_msg)

            if response.status_code != 200:
                data = response.json()
                error_msg = data.get("error", {}).get("message", f"API error: {response.status_code}")
                raise MetaAdLibraryError(error_msg)

            return response.json()

    async def search_ads(
        self,
        search_terms: Optional[str] = None,
        ad_reached_countries: list[str] = None,
        ad_active_status: str = "ALL",
        ad_type: str = "ALL",
        publisher_platforms: list[str] = None,
        search_page_ids: list[str] = None,
        limit: int = 50,
    ) -> list[dict]:
        """
        Search Meta Ad Library.

        Args:
            search_terms: Keywords to search for
            ad_reached_countries: List of ISO country codes (default: ["BR"])
            ad_active_status: "ALL", "ACTIVE", or "INACTIVE"
            ad_type: "ALL", "POLITICAL_AND_ISSUE_ADS", etc.
            publisher_platforms: ["facebook", "instagram", "audience_network", "messenger"]
            search_page_ids: List of Facebook page IDs
            limit: Maximum number of ads to return

        Returns:
            List of ad data dictionaries
        """
        if ad_reached_countries is None:
            ad_reached_countries = ["BR"]

        params = {
            "ad_reached_countries": ad_reached_countries,
            "ad_active_status": ad_active_status,
            "ad_type": ad_type,
            "fields": ",".join(self.AD_FIELDS),
            "limit": min(limit, self.ads_per_request),
        }

        if search_terms:
            params["search_terms"] = search_terms

        if publisher_platforms:
            params["publisher_platforms"] = publisher_platforms

        if search_page_ids:
            params["search_page_ids"] = search_page_ids

        logger.info(
            "Searching Meta Ad Library",
            search_terms=search_terms,
            countries=ad_reached_countries,
            limit=limit,
        )

        all_ads = []
        next_url = None

        while len(all_ads) < limit:
            if next_url:
                # Use pagination URL directly
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(next_url)
                    data = response.json()
            else:
                data = await self._make_request("ads_archive", params)

            ads = data.get("data", [])
            all_ads.extend(ads)

            # Check for pagination
            paging = data.get("paging", {})
            next_url = paging.get("next")

            if not next_url or len(ads) == 0:
                break

        logger.info("Meta Ad Library search complete", ads_found=len(all_ads))
        return all_ads[:limit]

    async def get_ads_by_page(
        self,
        page_id: str,
        ad_active_status: str = "ALL",
        limit: int = 100,
    ) -> list[dict]:
        """Get all ads from a specific Facebook page."""
        return await self.search_ads(
            search_page_ids=[page_id],
            ad_active_status=ad_active_status,
            limit=limit,
        )

    async def save_ads_to_db(self, ads: list[dict], workspace_id: UUID) -> tuple[int, int]:
        """
        Save ads to database.

        Returns:
            Tuple of (ads_saved, advertisers_found)
        """
        ads_saved = 0
        advertisers_cache = {}  # page_id -> advertiser_id

        async with async_session_maker() as session:
            for ad_data in ads:
                try:
                    # Get or create advertiser
                    page_id = ad_data.get("page_id")
                    page_name = ad_data.get("page_name", "Unknown")

                    if page_id not in advertisers_cache:
                        advertiser = await self._get_or_create_advertiser(
                            session, page_id, page_name
                        )
                        advertisers_cache[page_id] = advertiser.id

                    advertiser_id = advertisers_cache[page_id]

                    # Create ad
                    ad = await self._create_ad(session, ad_data, advertiser_id)

                    # Create creatives from ad_snapshot_url
                    if ad_data.get("ad_snapshot_url"):
                        await self._create_creative(
                            session,
                            ad.id,
                            ad_data["ad_snapshot_url"],
                        )

                    ads_saved += 1

                except Exception as e:
                    logger.error("Failed to save ad", ad_id=ad_data.get("id"), error=str(e))
                    continue

            await session.commit()

        return ads_saved, len(advertisers_cache)

    async def _get_or_create_advertiser(
        self,
        session,
        page_id: str,
        page_name: str,
    ) -> Advertiser:
        """Get existing advertiser or create new one."""
        from sqlalchemy import select

        # Try to find existing advertiser
        result = await session.execute(
            select(Advertiser).where(
                Advertiser.platform == "meta",
                Advertiser.platform_id == page_id,
            )
        )
        advertiser = result.scalar_one_or_none()

        if advertiser:
            # Update name if changed
            if advertiser.name != page_name:
                advertiser.name = page_name
                advertiser.updated_at = datetime.utcnow()
            return advertiser

        # Create new advertiser
        advertiser = Advertiser(
            platform="meta",
            platform_id=page_id,
            name=page_name,
            page_url=f"https://www.facebook.com/{page_id}" if page_id else None,
        )
        session.add(advertiser)
        await session.flush()

        return advertiser

    async def _create_ad(self, session, ad_data: dict, advertiser_id: UUID) -> Ad:
        """Create ad record from API data."""
        # Parse impressions range
        impressions = ad_data.get("impressions", {})
        impressions_lower = None
        impressions_upper = None

        if isinstance(impressions, dict):
            impressions_lower = impressions.get("lower_bound")
            impressions_upper = impressions.get("upper_bound")

        # Parse spend range
        spend = ad_data.get("spend", {})
        spend_lower = None
        spend_upper = None

        if isinstance(spend, dict):
            # Convert to cents
            spend_lower = int(float(spend.get("lower_bound", 0)) * 100) if spend.get("lower_bound") else None
            spend_upper = int(float(spend.get("upper_bound", 0)) * 100) if spend.get("upper_bound") else None

        # Parse dates
        started_at = None
        ended_at = None

        if ad_data.get("ad_delivery_start_time"):
            try:
                started_at = datetime.fromisoformat(
                    ad_data["ad_delivery_start_time"].replace("Z", "+00:00")
                ).date()
            except (ValueError, AttributeError):
                pass

        if ad_data.get("ad_delivery_stop_time"):
            try:
                ended_at = datetime.fromisoformat(
                    ad_data["ad_delivery_stop_time"].replace("Z", "+00:00")
                ).date()
            except (ValueError, AttributeError):
                pass

        # Get creative content
        body_texts = ad_data.get("ad_creative_bodies", [])
        link_titles = ad_data.get("ad_creative_link_titles", [])
        link_descriptions = ad_data.get("ad_creative_link_descriptions", [])
        link_captions = ad_data.get("ad_creative_link_captions", [])

        # Determine ad status
        status = "active" if ended_at is None else "inactive"

        ad = Ad(
            advertiser_id=advertiser_id,
            platform="meta",
            platform_ad_id=ad_data.get("id"),
            body_text=body_texts[0] if body_texts else None,
            link_title=link_titles[0] if link_titles else None,
            link_description=link_descriptions[0] if link_descriptions else None,
            link_url=link_captions[0] if link_captions else None,
            status=status,
            impressions_lower=int(impressions_lower) if impressions_lower else None,
            impressions_upper=int(impressions_upper) if impressions_upper else None,
            spend_lower=spend_lower,
            spend_upper=spend_upper,
            currency=ad_data.get("currency"),
            reached_countries=ad_data.get("delivery_by_region", {}).keys() if ad_data.get("delivery_by_region") else None,
            demographic_distribution=ad_data.get("demographic_distribution"),
            region_distribution=ad_data.get("delivery_by_region"),
            started_at=started_at,
            ended_at=ended_at,
            platform_data={
                "publisher_platforms": ad_data.get("publisher_platforms"),
                "languages": ad_data.get("languages"),
                "target_ages": ad_data.get("target_ages"),
                "target_gender": ad_data.get("target_gender"),
                "target_locations": ad_data.get("target_locations"),
                "estimated_audience_size": ad_data.get("estimated_audience_size"),
                "bylines": ad_data.get("bylines"),
            },
        )

        session.add(ad)
        await session.flush()

        return ad

    async def _create_creative(
        self,
        session,
        ad_id: UUID,
        snapshot_url: str,
    ) -> AdCreative:
        """Create creative from ad snapshot URL."""
        creative = AdCreative(
            ad_id=ad_id,
            creative_type="snapshot",
            url=snapshot_url,
            position=0,
        )
        session.add(creative)

        return creative
