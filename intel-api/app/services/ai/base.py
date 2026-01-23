"""Base interface for AI providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Optional
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class ChatMessage:
    """A single message in a conversation."""
    role: MessageRole
    content: str
    images: list[str] = field(default_factory=list)  # Base64 or URLs


@dataclass
class ImageGenerationRequest:
    """Request for image generation."""
    style_prompt: str
    content_prompt: str
    aspect_ratio: str = "1:1"  # "1:1", "9:16", "16:9", "3:4"


@dataclass
class ProviderInfo:
    """Information about an AI provider."""
    name: str
    display_name: str
    supports_chat: bool = True
    supports_image_generation: bool = False
    supports_vision: bool = False
    text_models: list[str] = field(default_factory=list)
    image_models: list[str] = field(default_factory=list)


class BaseAIProvider(ABC):
    """Abstract base class for AI providers."""

    @property
    @abstractmethod
    def info(self) -> ProviderInfo:
        """Get provider information."""
        pass

    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """
        Send messages and get a response.

        Args:
            messages: List of conversation messages
            system_prompt: Optional system instruction
            model: Model to use (provider-specific)
            temperature: Creativity (0.0-1.0)
            max_tokens: Maximum response tokens

        Returns:
            Assistant's response text
        """
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[ChatMessage],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """
        Send messages and stream the response.

        Yields:
            Chunks of the assistant's response
        """
        pass

    @abstractmethod
    async def generate_image(
        self,
        request: ImageGenerationRequest,
        model: Optional[str] = None,
    ) -> str:
        """
        Generate an image.

        Args:
            request: Image generation parameters
            model: Model to use

        Returns:
            Base64-encoded image data URL
        """
        pass

    @property
    def supports_image_generation(self) -> bool:
        """Check if provider supports image generation."""
        return self.info.supports_image_generation

    @property
    def supports_vision(self) -> bool:
        """Check if provider supports image understanding."""
        return self.info.supports_vision
