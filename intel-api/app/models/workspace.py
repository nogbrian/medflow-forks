import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    color = Column(String, default="#6366f1")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    profiles = relationship("Profile", back_populates="workspace", cascade="all, delete-orphan")

    # AI relationships
    brand_profiles = relationship("BrandProfile", back_populates="workspace", cascade="all, delete-orphan")
    ai_conversations = relationship("AIConversation", back_populates="workspace", cascade="all, delete-orphan")
    generated_images = relationship("GeneratedImage", back_populates="workspace", cascade="all, delete-orphan")
