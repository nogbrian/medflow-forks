"""Pydantic schemas for AI endpoints."""

from typing import Optional, Literal
from pydantic import BaseModel, field_validator
from datetime import datetime
import uuid


# ============================================================
# Chat Schemas
# ============================================================

class ChatMessageRequest(BaseModel):
    """Single message in a chat request."""
    role: Literal["user", "assistant", "system"]
    content: str
    images: list[str] = []  # Base64 or URLs


class ChatRequest(BaseModel):
    """Request to send a chat message."""
    workspace_id: str
    conversation_id: Optional[str] = None  # None = new conversation
    agent_type: Literal["creative", "copywriter"] = "creative"
    provider: Literal["gemini", "openai", "xai", "anthropic"] = "openai"
    messages: list[ChatMessageRequest]
    system_prompt: Optional[str] = None
    brand_profile_id: Optional[str] = None
    stream: bool = False

    @field_validator("workspace_id", "conversation_id", "brand_profile_id")
    @classmethod
    def validate_uuid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError:
                raise ValueError("Invalid UUID format")
        return v


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    success: bool
    conversation_id: str
    message: Optional[str] = None
    error: Optional[str] = None


# ============================================================
# Image Generation Schemas
# ============================================================

class ImageGenerationRequest(BaseModel):
    """Request to generate an image."""
    workspace_id: str
    conversation_id: Optional[str] = None
    provider: Literal["openai", "xai"] = "openai"
    style_prompt: str
    content_prompt: str
    aspect_ratio: Literal["1:1", "9:16", "16:9", "3:4"] = "1:1"

    @field_validator("workspace_id", "conversation_id")
    @classmethod
    def validate_uuid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError:
                raise ValueError("Invalid UUID format")
        return v


class ImageGenerationResponse(BaseModel):
    """Response from image generation."""
    success: bool
    image_id: Optional[str] = None
    image_url: Optional[str] = None  # Base64 data URL
    error: Optional[str] = None


# ============================================================
# Conversation Schemas
# ============================================================

class ConversationCreate(BaseModel):
    """Create a new conversation."""
    workspace_id: str
    agent_type: Literal["creative", "copywriter"] = "creative"
    provider: Literal["gemini", "openai", "xai", "anthropic"] = "openai"
    title: Optional[str] = None
    brand_profile_id: Optional[str] = None
    system_prompt: Optional[str] = None


class ConversationUpdate(BaseModel):
    """Update a conversation."""
    title: Optional[str] = None
    is_archived: Optional[bool] = None
    context: Optional[dict] = None


class MessageOut(BaseModel):
    """Message output schema."""
    id: str
    role: str
    content: str
    images: list[str] = []
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationOut(BaseModel):
    """Conversation output schema."""
    id: str
    workspace_id: str
    brand_profile_id: Optional[str] = None
    title: Optional[str] = None
    agent_type: str
    provider: str
    is_archived: bool = False
    context: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
    messages: list[MessageOut] = []

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """List of conversations."""
    success: bool
    conversations: list[ConversationOut] = []
    total: int = 0


# ============================================================
# Brand Profile Schemas
# ============================================================

class BrandProfileCreate(BaseModel):
    """Create a brand profile."""
    workspace_id: str
    name: str
    description: Optional[str] = None


class BrandProfileUpdate(BaseModel):
    """Update a brand profile."""
    name: Optional[str] = None
    description: Optional[str] = None
    color_palette: Optional[dict] = None
    typography: Optional[dict] = None
    visual_style: Optional[str] = None


class BrandProfileOut(BaseModel):
    """Brand profile output schema."""
    id: str
    workspace_id: str
    name: str
    description: Optional[str] = None
    color_palette: Optional[dict] = None
    typography: Optional[dict] = None
    visual_style: Optional[str] = None
    logo_url: Optional[str] = None
    brand_manual_url: Optional[str] = None
    ai_synthesis: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BrandProfileListResponse(BaseModel):
    """List of brand profiles."""
    success: bool
    profiles: list[BrandProfileOut] = []
    total: int = 0


# ============================================================
# Provider Schemas
# ============================================================

class ProviderInfoOut(BaseModel):
    """Provider information."""
    name: str
    display_name: str
    supports_chat: bool
    supports_image_generation: bool
    supports_vision: bool
    text_models: list[str]
    image_models: list[str]


class ProvidersResponse(BaseModel):
    """List of available providers."""
    success: bool
    providers: list[ProviderInfoOut] = []
