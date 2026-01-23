import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    instagram_id = Column(String, unique=True, nullable=False)
    short_code = Column(String, nullable=True)
    type = Column(String, default="Image")
    url = Column(String, nullable=True)
    display_url = Column(String, nullable=True)
    caption = Column(String, nullable=True)
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    video_view_count = Column(Integer, nullable=True)
    video_play_count = Column(Integer, nullable=True)
    video_duration = Column(Float, nullable=True)
    is_reel = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)
    is_sponsored = Column(Boolean, default=False)
    is_comments_disabled = Column(Boolean, default=False)
    location_name = Column(String, nullable=True)
    location_id = Column(String, nullable=True)
    alt_text = Column(String, nullable=True)
    posted_at = Column(DateTime(timezone=True), nullable=True)
    scraped_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    profile = relationship("Profile", back_populates="posts")
    hashtags = relationship("Hashtag", back_populates="post", cascade="all, delete-orphan")
    mentions = relationship("Mention", back_populates="post", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_posts_profile_id", "profile_id"),
        Index("ix_posts_posted_at", "posted_at"),
        Index("ix_posts_is_reel", "is_reel"),
    )
