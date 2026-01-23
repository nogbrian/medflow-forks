import re
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models import Profile, Post, Hashtag, Mention, ScrapeRun, Setting

logger = structlog.get_logger()


class DatabaseService:
    """Database operations for scraping data."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_profile(self, profile_id: str) -> Optional[Profile]:
        """Get a profile by ID."""
        result = await self.session.execute(
            select(Profile).where(Profile.id == uuid.UUID(profile_id))
        )
        return result.scalar_one_or_none()

    async def get_profile_by_username(self, workspace_id: str, username: str) -> Optional[Profile]:
        """Get a profile by workspace and username."""
        result = await self.session.execute(
            select(Profile).where(
                Profile.workspace_id == uuid.UUID(workspace_id),
                Profile.username == username
            )
        )
        return result.scalar_one_or_none()

    async def upsert_profile(self, workspace_id: str, profile_data: dict) -> str:
        """Upsert a profile and return its ID."""
        now = datetime.utcnow()

        # Check if profile exists
        existing = await self.get_profile_by_username(workspace_id, profile_data.get("username", ""))

        if existing:
            # Update existing profile
            await self.session.execute(
                update(Profile)
                .where(Profile.id == existing.id)
                .values(
                    instagram_id=profile_data.get("instagram_id") or existing.instagram_id,
                    full_name=profile_data.get("full_name") or existing.full_name,
                    biography=profile_data.get("biography") or existing.biography,
                    external_url=profile_data.get("external_url") or existing.external_url,
                    followers_count=profile_data.get("followers_count", existing.followers_count),
                    follows_count=profile_data.get("follows_count", existing.follows_count),
                    posts_count=profile_data.get("posts_count", existing.posts_count),
                    is_verified=profile_data.get("is_verified", existing.is_verified),
                    is_business_account=profile_data.get("is_business_account", existing.is_business_account),
                    business_category=profile_data.get("business_category") or existing.business_category,
                    profile_pic_url=profile_data.get("profile_pic_url") or existing.profile_pic_url,
                    last_scraped_at=now,
                    updated_at=now,
                )
            )
            await self.session.commit()
            logger.info("profile_updated", profile_id=str(existing.id), username=profile_data.get("username"))
            return str(existing.id)

        # Create new profile
        profile_id = uuid.uuid4()
        profile = Profile(
            id=profile_id,
            workspace_id=uuid.UUID(workspace_id),
            instagram_id=profile_data.get("instagram_id"),
            username=profile_data.get("username"),
            full_name=profile_data.get("full_name"),
            biography=profile_data.get("biography"),
            external_url=profile_data.get("external_url"),
            followers_count=profile_data.get("followers_count", 0),
            follows_count=profile_data.get("follows_count", 0),
            posts_count=profile_data.get("posts_count", 0),
            is_verified=profile_data.get("is_verified", False),
            is_business_account=profile_data.get("is_business_account", False),
            business_category=profile_data.get("business_category"),
            profile_pic_url=profile_data.get("profile_pic_url"),
            last_scraped_at=now,
            created_at=now,
            updated_at=now,
        )
        self.session.add(profile)
        await self.session.commit()
        logger.info("profile_created", profile_id=str(profile_id), username=profile_data.get("username"))
        return str(profile_id)

    async def upsert_post(self, profile_id: str, post_data: dict) -> str:
        """Upsert a post and return its ID."""
        now = datetime.utcnow()
        instagram_id = post_data.get("instagram_id")

        if not instagram_id:
            logger.warning("post_missing_instagram_id", data=post_data)
            return ""

        # Check if post exists
        result = await self.session.execute(
            select(Post).where(Post.instagram_id == instagram_id)
        )
        existing = result.scalar_one_or_none()

        # Parse posted_at if string
        posted_at = post_data.get("posted_at")
        if isinstance(posted_at, str):
            try:
                posted_at = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
            except ValueError:
                posted_at = None

        if existing:
            # Update existing post
            await self.session.execute(
                update(Post)
                .where(Post.id == existing.id)
                .values(
                    likes_count=post_data.get("likes_count", existing.likes_count),
                    comments_count=post_data.get("comments_count", existing.comments_count),
                    video_view_count=post_data.get("video_view_count") or existing.video_view_count,
                    video_play_count=post_data.get("video_play_count") or existing.video_play_count,
                    scraped_at=now,
                    updated_at=now,
                )
            )
            await self.session.commit()
            return str(existing.id)

        # Create new post
        post_id = uuid.uuid4()
        post = Post(
            id=post_id,
            profile_id=uuid.UUID(profile_id),
            instagram_id=instagram_id,
            short_code=post_data.get("short_code"),
            type=post_data.get("type", "Image"),
            url=post_data.get("url"),
            display_url=post_data.get("display_url"),
            caption=post_data.get("caption"),
            likes_count=post_data.get("likes_count", 0),
            comments_count=post_data.get("comments_count", 0),
            video_view_count=post_data.get("video_view_count"),
            video_play_count=post_data.get("video_play_count"),
            video_duration=post_data.get("video_duration"),
            is_reel=post_data.get("is_reel", False),
            is_pinned=post_data.get("is_pinned", False),
            is_sponsored=post_data.get("is_sponsored", False),
            is_comments_disabled=post_data.get("is_comments_disabled", False),
            location_name=post_data.get("location_name"),
            location_id=post_data.get("location_id"),
            alt_text=post_data.get("alt_text"),
            posted_at=posted_at,
            scraped_at=now,
            created_at=now,
            updated_at=now,
        )
        self.session.add(post)
        await self.session.commit()

        # Extract and save hashtags and mentions from caption
        caption = post_data.get("caption", "") or ""
        await self._save_hashtags(post_id, caption)
        await self._save_mentions(post_id, caption)

        return str(post_id)

    async def _save_hashtags(self, post_id: uuid.UUID, caption: str) -> None:
        """Extract and save hashtags from caption."""
        hashtags = set(re.findall(r"#(\w+)", caption))
        for tag in hashtags:
            try:
                hashtag = Hashtag(
                    id=uuid.uuid4(),
                    post_id=post_id,
                    tag=tag.lower(),
                    created_at=datetime.utcnow(),
                )
                self.session.add(hashtag)
            except Exception:
                pass  # Ignore duplicates
        await self.session.commit()

    async def _save_mentions(self, post_id: uuid.UUID, caption: str) -> None:
        """Extract and save mentions from caption."""
        mentions = set(re.findall(r"@(\w+)", caption))
        for username in mentions:
            try:
                mention = Mention(
                    id=uuid.uuid4(),
                    post_id=post_id,
                    username=username.lower(),
                    created_at=datetime.utcnow(),
                )
                self.session.add(mention)
            except Exception:
                pass  # Ignore duplicates
        await self.session.commit()

    async def create_scrape_run(self, profile_id: str, scrape_type: str) -> str:
        """Create a new scrape run record."""
        scrape_run_id = uuid.uuid4()
        scrape_run = ScrapeRun(
            id=scrape_run_id,
            profile_id=uuid.UUID(profile_id),
            status="running",
            scrape_type=scrape_type,
            started_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )
        self.session.add(scrape_run)
        await self.session.commit()
        logger.info("scrape_run_created", scrape_run_id=str(scrape_run_id), profile_id=profile_id)
        return str(scrape_run_id)

    async def complete_scrape_run(self, scrape_run_id: str, posts_count: int, reels_count: int) -> None:
        """Mark a scrape run as completed."""
        await self.session.execute(
            update(ScrapeRun)
            .where(ScrapeRun.id == uuid.UUID(scrape_run_id))
            .values(
                status="completed",
                posts_scraped=posts_count,
                reels_scraped=reels_count,
                completed_at=datetime.utcnow(),
            )
        )
        await self.session.commit()
        logger.info("scrape_run_completed", scrape_run_id=scrape_run_id, posts=posts_count, reels=reels_count)

    async def fail_scrape_run(self, scrape_run_id: str, error_message: str) -> None:
        """Mark a scrape run as failed."""
        await self.fail_scrape_run_with_status(scrape_run_id, "failed", error_message)

    async def fail_scrape_run_with_status(self, scrape_run_id: str, status: str, error_message: str) -> None:
        """Mark a scrape run with a specific failure status."""
        await self.session.execute(
            update(ScrapeRun)
            .where(ScrapeRun.id == uuid.UUID(scrape_run_id))
            .values(
                status=status,
                error_message=error_message,
                completed_at=datetime.utcnow(),
            )
        )
        await self.session.commit()
        logger.warning("scrape_run_status_changed", scrape_run_id=scrape_run_id, status=status, error=error_message)

    async def get_setting(self, key: str) -> Optional[str]:
        """Get a setting value by key."""
        result = await self.session.execute(
            select(Setting).where(Setting.key == key)
        )
        setting = result.scalar_one_or_none()
        return setting.value if setting else None
