"""AI Message model for individual chat messages."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Index, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.models.base import Base


class AIMessage(Base):
    __tablename__ = "ai_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False)

    # Message content
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)

    # Attached images (base64 or URLs)
    images = Column(ARRAY(String), default=[])

    # Token usage (for tracking/billing)
    token_count = Column(Integer, nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    conversation = relationship("AIConversation", back_populates="messages")

    __table_args__ = (
        Index("ix_ai_messages_conversation_id", "conversation_id"),
        Index("ix_ai_messages_created_at", "created_at"),
    )
