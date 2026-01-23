"""API endpoints for Meta Ad Library and Google Ads Transparency."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import structlog

from app.models import get_db
from app.schemas.ads import (
    MetaAdSearchRequest,
    MetaAdSearchResponse,
    MetaAdByPageRequest,
    GoogleAdsSearchRequest,
    GoogleAdsSearchResponse,
)
from app.services.ads.meta_ads.client import (
    MetaAdLibraryClient,
    MetaAdLibraryError,
    MetaApiAuthError,
    MetaApiRateLimitError,
)
from app.services.ads.google_ads.scraper import (
    GoogleAdsScraper,
    GoogleAdsScraperError,
    GoogleAdsRateLimitError,
)

logger = structlog.get_logger()

router = APIRouter()


# =============================================================================
# Meta Ad Library Endpoints
# =============================================================================

@router.post("/meta-ads/search", response_model=MetaAdSearchResponse)
async def search_meta_ads(
    request: MetaAdSearchRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Search Meta Ad Library for ads.

    Searches the official Meta Ad Library API and saves results to database.
    """
    logger.info(
        "meta_ads_search_triggered",
        search_terms=request.search_terms,
        countries=request.ad_reached_countries,
        workspace_id=request.workspace_id,
    )

    try:
        client = MetaAdLibraryClient()

        # Search for ads
        ads = await client.search_ads(
            search_terms=request.search_terms,
            ad_reached_countries=request.ad_reached_countries,
            ad_active_status=request.ad_active_status,
            ad_type=request.ad_type,
            publisher_platforms=request.publisher_platforms,
            search_page_ids=request.search_page_ids,
            limit=request.limit,
        )

        if not ads:
            logger.info("meta_ads_no_results", search_terms=request.search_terms)
            return MetaAdSearchResponse(
                success=True,
                ads_found=0,
                ads_saved=0,
                advertisers_found=0,
            )

        # Save to database
        ads_saved, advertisers_found = await client.save_ads_to_db(
            ads, UUID(request.workspace_id)
        )

        logger.info(
            "meta_ads_search_complete",
            ads_found=len(ads),
            ads_saved=ads_saved,
            advertisers_found=advertisers_found,
        )

        return MetaAdSearchResponse(
            success=True,
            ads_found=len(ads),
            ads_saved=ads_saved,
            advertisers_found=advertisers_found,
        )

    except MetaApiAuthError as e:
        logger.error("meta_ads_auth_error", error=str(e))
        raise HTTPException(status_code=401, detail=str(e))

    except MetaApiRateLimitError as e:
        logger.warning("meta_ads_rate_limited", retry_after=e.retry_after)
        raise HTTPException(
            status_code=429,
            detail=f"Rate limited. Retry after {e.retry_after} seconds",
            headers={"Retry-After": str(e.retry_after)},
        )

    except MetaAdLibraryError as e:
        logger.error("meta_ads_error", error=str(e))
        return MetaAdSearchResponse(success=False, error=str(e))

    except Exception as e:
        logger.error("meta_ads_unexpected_error", error=str(e))
        return MetaAdSearchResponse(success=False, error=str(e))


@router.post("/meta-ads/by-page", response_model=MetaAdSearchResponse)
async def get_meta_ads_by_page(
    request: MetaAdByPageRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all ads from a specific Facebook page.

    Fetches all ads from a Facebook page ID and saves to database.
    """
    logger.info(
        "meta_ads_by_page_triggered",
        page_id=request.page_id,
        workspace_id=request.workspace_id,
    )

    try:
        client = MetaAdLibraryClient()

        # Get ads by page
        ads = await client.get_ads_by_page(
            page_id=request.page_id,
            ad_active_status=request.ad_active_status,
            limit=request.limit,
        )

        if not ads:
            logger.info("meta_ads_by_page_no_results", page_id=request.page_id)
            return MetaAdSearchResponse(
                success=True,
                ads_found=0,
                ads_saved=0,
                advertisers_found=0,
            )

        # Save to database
        ads_saved, advertisers_found = await client.save_ads_to_db(
            ads, UUID(request.workspace_id)
        )

        logger.info(
            "meta_ads_by_page_complete",
            page_id=request.page_id,
            ads_found=len(ads),
            ads_saved=ads_saved,
        )

        return MetaAdSearchResponse(
            success=True,
            ads_found=len(ads),
            ads_saved=ads_saved,
            advertisers_found=advertisers_found,
        )

    except MetaApiAuthError as e:
        logger.error("meta_ads_auth_error", error=str(e))
        raise HTTPException(status_code=401, detail=str(e))

    except MetaApiRateLimitError as e:
        logger.warning("meta_ads_rate_limited", retry_after=e.retry_after)
        raise HTTPException(
            status_code=429,
            detail=f"Rate limited. Retry after {e.retry_after} seconds",
            headers={"Retry-After": str(e.retry_after)},
        )

    except MetaAdLibraryError as e:
        logger.error("meta_ads_error", error=str(e))
        return MetaAdSearchResponse(success=False, error=str(e))

    except Exception as e:
        logger.error("meta_ads_unexpected_error", error=str(e))
        return MetaAdSearchResponse(success=False, error=str(e))


# =============================================================================
# Google Ads Transparency Endpoints
# =============================================================================

@router.post("/google-ads/search", response_model=GoogleAdsSearchResponse)
async def search_google_ads(
    request: GoogleAdsSearchRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Search Google Ads Transparency Center.

    Scrapes the Google Ads Transparency Center and saves results to database.
    Note: This uses web scraping as Google doesn't provide an official API.
    """
    logger.info(
        "google_ads_search_triggered",
        advertiser_name=request.advertiser_name,
        domain=request.domain,
        region=request.region,
        workspace_id=request.workspace_id,
    )

    try:
        scraper = GoogleAdsScraper()

        # Search for ads
        ads = await scraper.search_ads(
            advertiser_name=request.advertiser_name,
            advertiser_id=request.advertiser_id,
            domain=request.domain,
            region=request.region,
            date_range=request.date_range,
            ad_format=request.ad_format,
            limit=request.limit,
        )

        if not ads:
            logger.info(
                "google_ads_no_results",
                advertiser_name=request.advertiser_name,
                domain=request.domain,
            )
            return GoogleAdsSearchResponse(
                success=True,
                ads_found=0,
                ads_saved=0,
                advertisers_found=0,
            )

        # Save to database
        ads_saved, advertisers_found = await scraper.save_ads_to_db(
            ads, UUID(request.workspace_id)
        )

        logger.info(
            "google_ads_search_complete",
            ads_found=len(ads),
            ads_saved=ads_saved,
            advertisers_found=advertisers_found,
        )

        return GoogleAdsSearchResponse(
            success=True,
            ads_found=len(ads),
            ads_saved=ads_saved,
            advertisers_found=advertisers_found,
        )

    except GoogleAdsRateLimitError as e:
        logger.warning("google_ads_rate_limited", error=str(e))
        raise HTTPException(
            status_code=429,
            detail="Google rate limit detected. Please try again later.",
            headers={"Retry-After": "60"},
        )

    except GoogleAdsScraperError as e:
        logger.error("google_ads_error", error=str(e))
        return GoogleAdsSearchResponse(success=False, error=str(e))

    except Exception as e:
        logger.error("google_ads_unexpected_error", error=str(e))
        return GoogleAdsSearchResponse(success=False, error=str(e))
