"""Generated Image model for AI-created images."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base


class GeneratedImage(Base):
    __tablename__ = "generated_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("ai_conversations.id", ondelete="SET NULL"), nullable=True)

    # Generation details
    provider = Column(String(50), nullable=False)  # 'openai', 'xai'
    model = Column(String(100), nullable=True)  # 'dall-e-3', etc.

    # Prompts used
    style_prompt = Column(Text, nullable=True)
    content_prompt = Column(Text, nullable=False)
    aspect_ratio = Column(String(10), nullable=False)  # '1:1', '9:16', '16:9'

    # Result
    image_url = Column(String, nullable=False)  # URL or base64 data URL
    thumbnail_url = Column(String, nullable=True)

    # Metadata
    image_metadata = Column("metadata", JSONB, nullable=True)  # Extra params, quality, etc.

    # Timestamp
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    workspace = relationship("Workspace", back_populates="generated_images")

    __table_args__ = (
        Index("ix_generated_images_workspace_id", "workspace_id"),
        Index("ix_generated_images_conversation_id", "conversation_id"),
        Index("ix_generated_images_created_at", "created_at"),
    )
