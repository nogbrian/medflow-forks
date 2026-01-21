"""Apify scraping tools."""

from typing import Any

from apify_client import ApifyClient

from config import get_settings
from config.apify_actors import (
    GOOGLE_TRENDS_SCRAPER,
    INSTAGRAM_HASHTAG_SCRAPER,
    INSTAGRAM_PROFILE_SCRAPER,
    META_ADS_LIBRARY_SCRAPER,
    YOUTUBE_CHANNEL_SCRAPER,
    YOUTUBE_SCRAPER,
)
from core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Initialize Apify client
client = ApifyClient(settings.apify_token)


async def buscar_reels_virais(
    hashtags: list[str],
    min_likes: int = 10000,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Search for viral Instagram Reels by hashtags.

    Args:
        hashtags: List of hashtags to search
        min_likes: Minimum number of likes
        limit: Maximum number of results

    Returns:
        List of viral reels data
    """
    try:
        run_input = {
            "hashtags": hashtags,
            "resultsLimit": limit * 2,  # Fetch more to filter
        }

        run = client.actor(INSTAGRAM_HASHTAG_SCRAPER).call(run_input=run_input)

        items = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            if item.get("likesCount", 0) >= min_likes:
                items.append({
                    "id": item.get("id"),
                    "url": item.get("url"),
                    "caption": item.get("caption"),
                    "likes": item.get("likesCount"),
                    "comments": item.get("commentsCount"),
                    "views": item.get("videoViewCount"),
                    "owner": item.get("ownerUsername"),
                    "timestamp": item.get("timestamp"),
                })
                if len(items) >= limit:
                    break

        logger.info("Viral reels found", hashtags=hashtags, count=len(items))
        return items

    except Exception as e:
        logger.error("Failed to fetch viral reels", error=str(e))
        return []


async def analisar_perfil_instagram(username: str) -> dict[str, Any] | None:
    """
    Analyze an Instagram profile.

    Args:
        username: Instagram username

    Returns:
        Profile data if found, None otherwise
    """
    try:
        run_input = {
            "usernames": [username],
        }

        run = client.actor(INSTAGRAM_PROFILE_SCRAPER).call(run_input=run_input)

        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            logger.info("Profile analyzed", username=username)
            return {
                "username": item.get("username"),
                "full_name": item.get("fullName"),
                "biography": item.get("biography"),
                "followers": item.get("followersCount"),
                "following": item.get("followsCount"),
                "posts": item.get("postsCount"),
                "is_verified": item.get("verified"),
                "profile_pic": item.get("profilePicUrl"),
                "external_url": item.get("externalUrl"),
                "recent_posts": item.get("latestPosts", [])[:10],
            }

        return None

    except Exception as e:
        logger.error("Failed to analyze profile", username=username, error=str(e))
        return None


async def buscar_ads_meta_library(
    search_terms: list[str],
    country: str = "BR",
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    Search Meta Ads Library for competitor ads.

    Args:
        search_terms: Keywords to search
        country: Country code
        limit: Maximum number of results

    Returns:
        List of ads data
    """
    try:
        run_input = {
            "searchTerms": search_terms,
            "countryCode": country,
            "adType": "all",
            "maxItems": limit,
        }

        run = client.actor(META_ADS_LIBRARY_SCRAPER).call(run_input=run_input)

        items = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            items.append({
                "id": item.get("id"),
                "page_name": item.get("pageName"),
                "page_id": item.get("pageId"),
                "ad_text": item.get("adCreativeBodyText"),
                "ad_link": item.get("adCreativeLinkUrl"),
                "start_date": item.get("adDeliveryStartTime"),
                "media_url": item.get("adCreativeImageUrl"),
                "platforms": item.get("publisherPlatforms"),
            })

        logger.info("Ads found", search_terms=search_terms, count=len(items))
        return items

    except Exception as e:
        logger.error("Failed to search ads library", error=str(e))
        return []


async def buscar_videos_youtube(
    keywords: list[str],
    min_views: int = 10000,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Search for YouTube videos by keywords.

    Args:
        keywords: Keywords to search
        min_views: Minimum number of views
        limit: Maximum number of results

    Returns:
        List of videos data
    """
    try:
        run_input = {
            "searchKeywords": keywords,
            "maxResults": limit * 2,
        }

        run = client.actor(YOUTUBE_SCRAPER).call(run_input=run_input)

        items = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            if item.get("viewCount", 0) >= min_views:
                items.append({
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "description": item.get("description"),
                    "views": item.get("viewCount"),
                    "likes": item.get("likes"),
                    "channel": item.get("channelName"),
                    "channel_url": item.get("channelUrl"),
                    "duration": item.get("duration"),
                    "published_at": item.get("date"),
                    "thumbnail": item.get("thumbnailUrl"),
                })
                if len(items) >= limit:
                    break

        logger.info("YouTube videos found", keywords=keywords, count=len(items))
        return items

    except Exception as e:
        logger.error("Failed to search YouTube videos", error=str(e))
        return []


async def monitorar_canal_youtube(channel_url: str) -> dict[str, Any] | None:
    """
    Monitor a YouTube channel.

    Args:
        channel_url: YouTube channel URL

    Returns:
        Channel data if found, None otherwise
    """
    try:
        run_input = {
            "channelUrls": [channel_url],
            "maxVideos": 10,
        }

        run = client.actor(YOUTUBE_CHANNEL_SCRAPER).call(run_input=run_input)

        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            logger.info("Channel monitored", channel_url=channel_url)
            return {
                "name": item.get("channelName"),
                "url": item.get("channelUrl"),
                "subscribers": item.get("numberOfSubscribers"),
                "videos_count": item.get("numberOfVideos"),
                "description": item.get("channelDescription"),
                "recent_videos": item.get("videos", [])[:10],
            }

        return None

    except Exception as e:
        logger.error("Failed to monitor channel", channel_url=channel_url, error=str(e))
        return None


async def buscar_google_trends(
    keywords: list[str],
    geo: str = "BR",
) -> list[dict[str, Any]]:
    """
    Search Google Trends for keyword popularity.

    Args:
        keywords: Keywords to analyze
        geo: Geographic location code

    Returns:
        Trends data for each keyword
    """
    try:
        run_input = {
            "searchTerms": keywords,
            "geo": geo,
            "timeRange": "today 3-m",  # Last 3 months
        }

        run = client.actor(GOOGLE_TRENDS_SCRAPER).call(run_input=run_input)

        items = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            items.append({
                "keyword": item.get("keyword"),
                "interest_over_time": item.get("interestOverTime"),
                "related_queries": item.get("relatedQueries"),
                "related_topics": item.get("relatedTopics"),
            })

        logger.info("Trends analyzed", keywords=keywords, count=len(items))
        return items

    except Exception as e:
        logger.error("Failed to fetch Google Trends", error=str(e))
        return []
