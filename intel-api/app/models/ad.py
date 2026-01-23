"""Ad model for advertisements from Meta and Google."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index, Boolean, Date, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base


class Ad(Base):
    __tablename__ = "ads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    advertiser_id = Column(UUID(as_uuid=True), ForeignKey("advertisers.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(50), nullable=False)  # 'meta', 'google'
    platform_ad_id = Column(String(255), nullable=True)  # Ad ID from platform

    # Ad content
    title = Column(String, nullable=True)
    body_text = Column(Text, nullable=True)
    link_url = Column(String, nullable=True)
    link_title = Column(String, nullable=True)
    link_description = Column(String, nullable=True)
    call_to_action = Column(String(100), nullable=True)  # "Learn More", "Shop Now", etc.

    # Ad metadata
    ad_type = Column(String(50), nullable=True)  # 'image', 'video', 'carousel', 'text'
    status = Column(String(50), nullable=True)  # 'active', 'inactive', 'removed'

    # Reach and targeting
    impressions_lower = Column(Integer, nullable=True)
    impressions_upper = Column(Integer, nullable=True)
    spend_lower = Column(Integer, nullable=True)  # In cents
    spend_upper = Column(Integer, nullable=True)  # In cents
    currency = Column(String(10), nullable=True)
    reached_countries = Column(JSONB, nullable=True)  # ["BR", "US", "PT"]

    # Demographics (Meta specific)
    demographic_distribution = Column(JSONB, nullable=True)  # Age/gender breakdown
    region_distribution = Column(JSONB, nullable=True)  # Geographic distribution

    # Dates
    started_at = Column(Date, nullable=True)
    ended_at = Column(Date, nullable=True)

    # Platform-specific data
    platform_data = Column(JSONB, nullable=True)  # Raw platform-specific fields

    # Timestamps
    scraped_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    advertiser = relationship("Advertiser", back_populates="ads")
    creatives = relationship("AdCreative", back_populates="ad", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_ads_platform", "platform"),
        Index("ix_ads_platform_ad_id", "platform_ad_id"),
        Index("ix_ads_advertiser_id", "advertiser_id"),
        Index("ix_ads_status", "status"),
        Index("ix_ads_started_at", "started_at"),
    )
