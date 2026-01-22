"""Instagram publishing tools via Meta Graph API."""

from datetime import datetime
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import get_settings
from core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class InstagramPublisher:
    """Client for Instagram Graph API publishing."""

    def __init__(self):
        self.access_token = settings.meta_access_token
        self.base_url = "https://graph.facebook.com/v19.0"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict | None = None,
        json_data: dict | None = None,
    ) -> dict:
        """Make an HTTP request to Instagram Graph API."""
        url = f"{self.base_url}/{endpoint}"

        if params is None:
            params = {}
        params["access_token"] = self.access_token

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
            )
            response.raise_for_status()
            return response.json()

    async def _get_instagram_account_id(self, page_id: str) -> str | None:
        """Get Instagram Business Account ID linked to a Facebook Page."""
        try:
            result = await self._request(
                "GET",
                f"{page_id}",
                params={"fields": "instagram_business_account"},
            )
            return result.get("instagram_business_account", {}).get("id")
        except Exception as e:
            logger.error("Failed to get Instagram account ID", error=str(e))
            return None


_publisher = InstagramPublisher()


async def publicar_post(
    instagram_account_id: str,
    imagem_url: str,
    caption: str,
) -> dict[str, Any] | None:
    """
    Publish a post to Instagram.

    Args:
        instagram_account_id: Instagram Business Account ID
        imagem_url: Public URL of the image
        caption: Post caption with hashtags

    Returns:
        Published post data if successful, None otherwise
    """
    try:
        # Step 1: Create media container
        container = await _publisher._request(
            "POST",
            f"{instagram_account_id}/media",
            params={
                "image_url": imagem_url,
                "caption": caption,
            },
        )

        container_id = container.get("id")
        if not container_id:
            logger.error("Failed to create media container")
            return None

        # Step 2: Publish the container
        result = await _publisher._request(
            "POST",
            f"{instagram_account_id}/media_publish",
            params={"creation_id": container_id},
        )

        media_id = result.get("id")
        if media_id:
            logger.info("Post published", media_id=media_id)
            return {
                "id": media_id,
                "url": f"https://www.instagram.com/p/{media_id}/",
                "published_at": datetime.utcnow().isoformat(),
            }

        return None

    except Exception as e:
        logger.error("Failed to publish post", error=str(e))
        return None


async def agendar_post(
    instagram_account_id: str,
    imagem_url: str,
    caption: str,
    scheduled_time: datetime,
) -> dict[str, Any] | None:
    """
    Schedule a post for future publication.

    Note: Instagram API doesn't support native scheduling for regular posts.
    This stores the post data for later publication via Celery Beat.

    Args:
        instagram_account_id: Instagram Business Account ID
        imagem_url: Public URL of the image
        caption: Post caption with hashtags
        scheduled_time: When to publish

    Returns:
        Scheduled post data if successful, None otherwise
    """
    try:
        # For now, return the scheduled data
        # The actual scheduling is handled by the approval system
        logger.info(
            "Post scheduled",
            account_id=instagram_account_id,
            scheduled_time=scheduled_time.isoformat(),
        )

        return {
            "instagram_account_id": instagram_account_id,
            "imagem_url": imagem_url,
            "caption": caption,
            "scheduled_time": scheduled_time.isoformat(),
            "status": "scheduled",
        }

    except Exception as e:
        logger.error("Failed to schedule post", error=str(e))
        return None


async def publicar_story(
    instagram_account_id: str,
    imagem_url: str,
) -> dict[str, Any] | None:
    """
    Publish a story to Instagram.

    Args:
        instagram_account_id: Instagram Business Account ID
        imagem_url: Public URL of the image

    Returns:
        Published story data if successful, None otherwise
    """
    try:
        # Step 1: Create story container
        container = await _publisher._request(
            "POST",
            f"{instagram_account_id}/media",
            params={
                "image_url": imagem_url,
                "media_type": "STORIES",
            },
        )

        container_id = container.get("id")
        if not container_id:
            logger.error("Failed to create story container")
            return None

        # Step 2: Publish the story
        result = await _publisher._request(
            "POST",
            f"{instagram_account_id}/media_publish",
            params={"creation_id": container_id},
        )

        media_id = result.get("id")
        if media_id:
            logger.info("Story published", media_id=media_id)
            return {
                "id": media_id,
                "type": "story",
                "published_at": datetime.utcnow().isoformat(),
            }

        return None

    except Exception as e:
        logger.error("Failed to publish story", error=str(e))
        return None


async def publicar_carrossel(
    instagram_account_id: str,
    imagens_urls: list[str],
    caption: str,
) -> dict[str, Any] | None:
    """
    Publish a carousel post to Instagram.

    Args:
        instagram_account_id: Instagram Business Account ID
        imagens_urls: List of public image URLs (2-10 images)
        caption: Post caption with hashtags

    Returns:
        Published carousel data if successful, None otherwise
    """
    try:
        if len(imagens_urls) < 2 or len(imagens_urls) > 10:
            logger.error("Carousel must have 2-10 images")
            return None

        # Step 1: Create containers for each image
        children_ids = []
        for img_url in imagens_urls:
            container = await _publisher._request(
                "POST",
                f"{instagram_account_id}/media",
                params={
                    "image_url": img_url,
                    "is_carousel_item": "true",
                },
            )
            if container.get("id"):
                children_ids.append(container["id"])

        if len(children_ids) < 2:
            logger.error("Failed to create enough carousel items")
            return None

        # Step 2: Create carousel container
        carousel = await _publisher._request(
            "POST",
            f"{instagram_account_id}/media",
            params={
                "media_type": "CAROUSEL",
                "caption": caption,
                "children": ",".join(children_ids),
            },
        )

        carousel_id = carousel.get("id")
        if not carousel_id:
            logger.error("Failed to create carousel container")
            return None

        # Step 3: Publish the carousel
        result = await _publisher._request(
            "POST",
            f"{instagram_account_id}/media_publish",
            params={"creation_id": carousel_id},
        )

        media_id = result.get("id")
        if media_id:
            logger.info("Carousel published", media_id=media_id)
            return {
                "id": media_id,
                "type": "carousel",
                "images_count": len(children_ids),
                "url": f"https://www.instagram.com/p/{media_id}/",
                "published_at": datetime.utcnow().isoformat(),
            }

        return None

    except Exception as e:
        logger.error("Failed to publish carousel", error=str(e))
        return None
