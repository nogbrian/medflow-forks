import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    instagram_id = Column(String(255), nullable=True)
    username = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    biography = Column(String, nullable=True)
    external_url = Column(String, nullable=True)
    followers_count = Column(Integer, default=0)
    follows_count = Column(Integer, default=0)
    posts_count = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)
    is_business_account = Column(Boolean, default=False)
    business_category = Column(String(255), nullable=True)
    profile_pic_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    last_scraped_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="profiles")
    posts = relationship("Post", back_populates="profile", cascade="all, delete-orphan")
    scrape_runs = relationship("ScrapeRun", back_populates="profile", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_profiles_workspace_id", "workspace_id"),
        Index("ix_profiles_username", "username"),
        Index("ix_profiles_instagram_id", "instagram_id"),
        Index("ix_profiles_is_active", "is_active"),
    )
