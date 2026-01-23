"""Ad Creative model for ad images/videos."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import relationship

from app.models.base import Base


class AdCreative(Base):
    __tablename__ = "ad_creatives"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ad_id = Column(UUID(as_uuid=True), ForeignKey("ads.id", ondelete="CASCADE"), nullable=False)

    # Creative content
    creative_type = Column(String(50), nullable=False)  # 'image', 'video', 'carousel_card'
    url = Column(String, nullable=True)  # Original URL from platform
    local_path = Column(String, nullable=True)  # If downloaded locally
    thumbnail_url = Column(String, nullable=True)

    # Dimensions
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)

    # Video specific
    duration_seconds = Column(Float, nullable=True)

    # Order (for carousels)
    position = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    ad = relationship("Ad", back_populates="creatives")

    __table_args__ = (
        Index("ix_ad_creatives_ad_id", "ad_id"),
        Index("ix_ad_creatives_type", "creative_type"),
    )
