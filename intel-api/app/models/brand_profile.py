"""Brand Profile model for storing client brand identity."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base


class BrandProfile(Base):
    __tablename__ = "brand_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)

    # Basic info
    name = Column(String(255), nullable=False)  # Client/brand name
    description = Column(Text, nullable=True)

    # Visual identity (AI-generated analysis)
    color_palette = Column(JSONB, nullable=True)  # {primary: "#...", secondary: "...", accent: "..."}
    typography = Column(JSONB, nullable=True)  # {heading: "...", body: "...", sizes: {...}}
    visual_style = Column(Text, nullable=True)  # Text description of visual style

    # Uploaded files
    logo_url = Column(String, nullable=True)
    brand_manual_url = Column(String, nullable=True)  # PDF or Markdown URL

    # AI-generated synthesis
    ai_synthesis = Column(Text, nullable=True)  # Markdown summary of brand

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workspace = relationship("Workspace", back_populates="brand_profiles")
    conversations = relationship("AIConversation", back_populates="brand_profile")

    __table_args__ = (
        Index("ix_brand_profiles_workspace_id", "workspace_id"),
        Index("ix_brand_profiles_name", "name"),
    )
