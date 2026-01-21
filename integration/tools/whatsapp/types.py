"""WhatsApp message types and data structures."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """Types of WhatsApp messages."""

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    LOCATION = "location"
    CONTACT = "contact"
    INTERACTIVE = "interactive"
    TEMPLATE = "template"
    REACTION = "reaction"


class Message(BaseModel):
    """Incoming WhatsApp message structure."""

    id: str = Field(description="Message ID from WhatsApp")
    phone: str = Field(description="Sender phone number")
    instance: str = Field(description="WhatsApp instance name")
    type: MessageType
    content: dict[str, Any]
    timestamp: datetime
    is_from_me: bool = False
    quoted_message_id: str | None = None


class Button(BaseModel):
    """Interactive button structure."""

    id: str = Field(max_length=256)
    title: str = Field(max_length=20)


class ListRow(BaseModel):
    """List row item structure."""

    id: str = Field(max_length=200)
    title: str = Field(max_length=24)
    description: str | None = Field(default=None, max_length=72)


class ListSection(BaseModel):
    """List section structure."""

    title: str = Field(max_length=24)
    rows: list[ListRow]


class SendMessageResult(BaseModel):
    """Result of sending a message."""

    success: bool
    message_id: str | None = None
    error: str | None = None


class MediaUploadResult(BaseModel):
    """Result of uploading media."""

    success: bool
    media_id: str | None = None
    url: str | None = None
    error: str | None = None
