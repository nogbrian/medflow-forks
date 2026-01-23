"""Advertiser model for ad accounts/pages."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class Advertiser(Base):
    __tablename__ = "advertisers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    platform = Column(String(50), nullable=False)  # 'meta', 'google'
    platform_id = Column(String(255), nullable=True)  # Page ID or advertiser ID
    name = Column(String(500), nullable=False)
    page_url = Column(String, nullable=True)
    profile_image_url = Column(String, nullable=True)
    disclaimer = Column(String, nullable=True)  # "Paid for by..."
    country = Column(String(10), nullable=True)  # ISO country code
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    ads = relationship("Ad", back_populates="advertiser", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_advertisers_platform", "platform"),
        Index("ix_advertisers_platform_id", "platform_id"),
        Index("ix_advertisers_name", "name"),
    )
