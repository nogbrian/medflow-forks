"""AI Conversation model for chat history."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base


class AIConversation(Base):
    __tablename__ = "ai_conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    brand_profile_id = Column(UUID(as_uuid=True), ForeignKey("brand_profiles.id", ondelete="SET NULL"), nullable=True)

    # Conversation metadata
    title = Column(String(255), nullable=True)
    agent_type = Column(String(50), nullable=False)  # 'creative', 'copywriter'
    provider = Column(String(50), nullable=False)  # 'gemini', 'openai', 'xai'

    # Custom system prompt (if different from default)
    system_prompt = Column(Text, nullable=True)

    # Persistent context (ICP, SPU, etc.)
    context = Column(JSONB, nullable=True)  # {icp: {...}, spu: {...}, ...}

    # Status
    is_archived = Column(String(10), default="false")

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workspace = relationship("Workspace", back_populates="ai_conversations")
    brand_profile = relationship("BrandProfile", back_populates="conversations")
    messages = relationship("AIMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="AIMessage.created_at")

    __table_args__ = (
        Index("ix_ai_conversations_workspace_id", "workspace_id"),
        Index("ix_ai_conversations_agent_type", "agent_type"),
        Index("ix_ai_conversations_created_at", "created_at"),
    )
