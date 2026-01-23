"""Apify SDK client for Instagram scraping.

Replaces Playwright-based local scraping with Apify cloud actors.
Uses apify-client for async execution of scraping tasks.
"""

from typing import Optional

import structlog
from apify_client import ApifyClientAsync

from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

# Apify actor IDs for Instagram scraping
INSTAGRAM_PROFILE_ACTOR = "apify/instagram-profile-scraper"
INSTAGRAM_POSTS_ACTOR = "apify/instagram-post-scraper"
INSTAGRAM_HASHTAG_ACTOR = "apify/instagram-hashtag-scraper"


def _get_client() -> ApifyClientAsync:
    """Get an authenticated Apify async client."""
    if not settings.apify_token:
        raise RuntimeError("APIFY_TOKEN is not configured")
    return ApifyClientAsync(token=settings.apify_token)


async def scrape_profile(username: str) -> dict:
    """Scrape an Instagram profile using Apify.

    Args:
        username: Instagram username (without @)

    Returns:
        Profile data dict with keys: username, full_name, biography,
        followers_count, follows_count, posts_count, is_verified,
        is_business_account, business_category, profile_pic_url, instagram_id
    """
    client = _get_client()

    run_input = {
        "usernames": [username],
        "resultsLimit": 1,
    }

    logger.info("apify_profile_scrape_start", username=username)

    run = await client.actor(INSTAGRAM_PROFILE_ACTOR).call(run_input=run_input)
    items = await client.dataset(run["defaultDatasetId"]).list_items()

    if not items.items:
        logger.warning("apify_profile_not_found", username=username)
        return {}

    raw = items.items[0]

    profile = {
        "username": raw.get("username", username),
        "full_name": raw.get("fullName", ""),
        "biography": raw.get("biography", ""),
        "followers_count": raw.get("followersCount", 0),
        "follows_count": raw.get("followsCount", 0),
        "posts_count": raw.get("postsCount", 0),
        "is_verified": raw.get("verified", False),
        "is_business_account": raw.get("isBusinessAccount", False),
        "business_category": raw.get("businessCategoryName", ""),
        "profile_pic_url": raw.get("profilePicUrlHD", raw.get("profilePicUrl", "")),
        "instagram_id": raw.get("id", ""),
        "external_url": raw.get("externalUrl", ""),
    }

    logger.info(
        "apify_profile_scrape_done",
        username=username,
        followers=profile["followers_count"],
    )

    return profile


async def scrape_posts(
    username: str,
    limit: int = 50,
    reels_only: bool = False,
) -> list[dict]:
    """Scrape Instagram posts/reels using Apify.

    Args:
        username: Instagram username
        limit: Maximum number of posts to retrieve
        reels_only: If True, only return reels (videos)

    Returns:
        List of post dicts with engagement metrics and metadata
    """
    client = _get_client()

    run_input = {
        "username": [username],
        "resultsLimit": limit,
    }

    logger.info(
        "apify_posts_scrape_start",
        username=username,
        limit=limit,
        reels_only=reels_only,
    )

    run = await client.actor(INSTAGRAM_POSTS_ACTOR).call(run_input=run_input)
    items = await client.dataset(run["defaultDatasetId"]).list_items()

    posts = []
    for raw in items.items:
        is_video = raw.get("type") == "Video" or raw.get("videoUrl") is not None
        is_reel = is_video and raw.get("productType") == "clips"

        if reels_only and not is_reel:
            continue

        post = {
            "instagram_id": raw.get("id", ""),
            "short_code": raw.get("shortCode", ""),
            "type": raw.get("type", "Image"),
            "url": raw.get("url", ""),
            "display_url": raw.get("displayUrl", ""),
            "caption": raw.get("caption", ""),
            "likes_count": raw.get("likesCount", 0),
            "comments_count": raw.get("commentsCount", 0),
            "video_view_count": raw.get("videoViewCount", 0),
            "video_play_count": raw.get("videoPlayCount", 0),
            "video_duration": raw.get("videoDuration", 0.0),
            "is_reel": is_reel,
            "is_pinned": raw.get("isPinned", False),
            "is_sponsored": raw.get("isSponsored", False),
            "is_comments_disabled": raw.get("commentsDisabled", False),
            "location_name": raw.get("locationName", ""),
            "location_id": raw.get("locationId", ""),
            "alt_text": raw.get("alt", ""),
            "posted_at": raw.get("timestamp"),
            "hashtags": raw.get("hashtags", []),
            "mentions": raw.get("mentions", []),
        }
        posts.append(post)

    logger.info(
        "apify_posts_scrape_done",
        username=username,
        total=len(posts),
        reels_only=reels_only,
    )

    return posts


async def scrape_google_ads(
    advertiser_name: Optional[str] = None,
    domain: Optional[str] = None,
    region: str = "BR",
    limit: int = 50,
) -> dict:
    """Scrape Google Ads Transparency Center using Apify.

    Args:
        advertiser_name: Name of the advertiser to search
        domain: Website domain to search
        region: ISO country code
        limit: Max results

    Returns:
        Dict with advertisers and ads lists
    """
    client = _get_client()

    # Use a Google Ads transparency scraper actor
    run_input = {
        "searchQuery": advertiser_name or domain or "",
        "country": region,
        "maxResults": limit,
    }

    if domain:
        run_input["domain"] = domain

    logger.info(
        "apify_google_ads_start",
        advertiser_name=advertiser_name,
        domain=domain,
    )

    run = await client.actor("apify/google-ads-transparency-scraper").call(
        run_input=run_input
    )
    items = await client.dataset(run["defaultDatasetId"]).list_items()

    advertisers = {}
    ads = []

    for raw in items.items:
        adv_id = raw.get("advertiserId", "")
        if adv_id and adv_id not in advertisers:
            advertisers[adv_id] = {
                "platform_id": adv_id,
                "name": raw.get("advertiserName", ""),
                "page_url": raw.get("advertiserUrl", ""),
                "country": region,
            }

        ads.append({
            "platform_ad_id": raw.get("adId", ""),
            "advertiser_platform_id": adv_id,
            "title": raw.get("title", ""),
            "body_text": raw.get("bodyText", ""),
            "link_url": raw.get("linkUrl", ""),
            "ad_type": raw.get("adType", "text"),
            "started_at": raw.get("firstShown"),
            "ended_at": raw.get("lastShown"),
        })

    logger.info(
        "apify_google_ads_done",
        advertisers=len(advertisers),
        ads=len(ads),
    )

    return {"advertisers": list(advertisers.values()), "ads": ads}
