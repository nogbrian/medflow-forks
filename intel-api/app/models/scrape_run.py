import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="pending")
    scrape_type = Column(String, nullable=True)
    posts_scraped = Column(Integer, default=0)
    reels_scraped = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    profile = relationship("Profile", back_populates="scrape_runs")

    __table_args__ = (
        Index("ix_scrape_runs_profile_id", "profile_id"),
        Index("ix_scrape_runs_status", "status"),
        Index("ix_scrape_runs_created_at", "created_at"),
    )
