"""AI Memory model for semantic search and long-term storage."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Index, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.models.base import Base

# Note: For pgvector support, you need to:
# 1. Install pgvector extension: CREATE EXTENSION IF NOT EXISTS vector;
# 2. The embedding column uses ARRAY for compatibility
#    For true pgvector, use: from pgvector.sqlalchemy import Vector


class AIMemory(Base):
    """
    AI Memory for semantic search and context engineering.

    Stores embeddings for semantic similarity search using pgvector.
    """
    __tablename__ = "ai_memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("ai_conversations.id", ondelete="SET NULL"), nullable=True)

    # Content
    content = Column(Text, nullable=False)
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system', 'memory', 'knowledge'

    # Embedding (3072 dimensions for text-embedding-3-large)
    # For pgvector: embedding = Column(Vector(3072))
    embedding = Column(ARRAY(float), nullable=True)

    # Metadata
    extra_metadata = Column("metadata", JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("ix_ai_memories_workspace_id", "workspace_id"),
        Index("ix_ai_memories_conversation_id", "conversation_id"),
        Index("ix_ai_memories_role", "role"),
        Index("ix_ai_memories_created_at", "created_at"),
        # For pgvector, add: Index("ix_ai_memories_embedding", embedding, postgresql_using="ivfflat")
    )


class AIKnowledge(Base):
    """
    Knowledge base entries for RAG.

    Stores documents, facts, and other information that can be
    retrieved during conversations.
    """
    __tablename__ = "ai_knowledge"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    brand_profile_id = Column(UUID(as_uuid=True), ForeignKey("brand_profiles.id", ondelete="SET NULL"), nullable=True)

    # Content
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(255), nullable=True)  # URL, file path, etc.
    content_type = Column(String(50), default="text")  # 'text', 'pdf', 'image', 'url'

    # Embedding
    embedding = Column(ARRAY(float), nullable=True)

    # Chunking metadata
    chunk_index = Column(String, nullable=True)
    parent_id = Column(UUID(as_uuid=True), nullable=True)  # For chunked documents

    # Metadata
    extra_metadata = Column("metadata", JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_ai_knowledge_workspace_id", "workspace_id"),
        Index("ix_ai_knowledge_brand_profile_id", "brand_profile_id"),
        Index("ix_ai_knowledge_content_type", "content_type"),
    )
