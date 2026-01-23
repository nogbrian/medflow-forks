"""Anthropic Claude AI provider implementation."""

import base64
from typing import AsyncIterator
import anthropic
import structlog

from app.config import settings
from app.services.ai.base import (
    BaseAIProvider,
    ChatMessage,
    ImageGenerationRequest,
    MessageRole,
    ProviderInfo,
)

logger = structlog.get_logger()


class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude provider with Opus 4.5 and Sonnet 4.5 support."""

    # Frontier models (January 2026)
    TEXT_MODELS = {
        "claude-opus-4-5": "claude-opus-4-5-20251101",  # Most intelligent
        "claude-sonnet-4-5": "claude-sonnet-4-5-20251101",  # Fast, 1M context
        "claude-opus-4-1": "claude-opus-4-1-20250805",  # Agentic tasks
        "claude-sonnet-4": "claude-sonnet-4-20250514",  # Balanced
    }

    DEFAULT_TEXT_MODEL = "claude-opus-4-5-20251101"

    def __init__(self):
        self._client = None

    @property
    def client(self) -> anthropic.AsyncAnthropic:
        if self._client is None:
            api_key = settings.anthropic_api_key
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not configured")
            self._client = anthropic.AsyncAnthropic(api_key=api_key)
        return self._client

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def supports_image_generation(self) -> bool:
        return False  # Claude doesn't generate images

    @property
    def supports_vision(self) -> bool:
        return True  # Claude has excellent vision capabilities

    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="anthropic",
            display_name="Anthropic Claude",
            supports_chat=True,
            supports_image_generation=False,
            supports_vision=True,
            text_models=list(self.TEXT_MODELS.keys()),
            image_models=[],
        )

    def get_info(self) -> ProviderInfo:
        """Alias for info property for compatibility."""
        return self.info

    def _convert_messages(self, messages: list[ChatMessage]) -> list[dict]:
        """Convert ChatMessage to Anthropic message format."""
        converted = []

        for msg in messages:
            content = []

            # Add images first (for vision)
            if msg.images:
                for img in msg.images:
                    if img.startswith("data:"):
                        # Extract base64 data and media type
                        parts = img.split(",", 1)
                        if len(parts) == 2:
                            media_type = parts[0].split(";")[0].split(":")[1]
                            data = parts[1]
                            content.append({
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": data,
                                }
                            })
                    else:
                        # URL-based image
                        content.append({
                            "type": "image",
                            "source": {
                                "type": "url",
                                "url": img,
                            }
                        })

            # Add text content
            if msg.content:
                content.append({"type": "text", "text": msg.content})

            converted.append({
                "role": "user" if msg.role == MessageRole.USER else "assistant",
                "content": content if len(content) > 1 else msg.content,
            })

        return converted

    async def chat(
        self,
        messages: list[ChatMessage],
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> str:
        """Send a chat message and get a response."""
        model_id = self.TEXT_MODELS.get(model, self.DEFAULT_TEXT_MODEL) if model else self.DEFAULT_TEXT_MODEL

        logger.info("Anthropic chat request", model=model_id, message_count=len(messages))

        try:
            converted_messages = self._convert_messages(messages)

            response = await self.client.messages.create(
                model=model_id,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt or "",
                messages=converted_messages,
            )

            # Extract text from response
            text_content = ""
            for block in response.content:
                if block.type == "text":
                    text_content += block.text

            return text_content

        except anthropic.APIError as e:
            logger.error("Anthropic API error", error=str(e))
            raise

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> AsyncIterator[str]:
        """Stream a chat response."""
        model_id = self.TEXT_MODELS.get(model, self.DEFAULT_TEXT_MODEL) if model else self.DEFAULT_TEXT_MODEL

        logger.info("Anthropic streaming chat", model=model_id)

        try:
            converted_messages = self._convert_messages(messages)

            async with self.client.messages.stream(
                model=model_id,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt or "",
                messages=converted_messages,
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        except anthropic.APIError as e:
            logger.error("Anthropic streaming error", error=str(e))
            raise

    async def generate_image(
        self,
        request: ImageGenerationRequest,
        model: str | None = None,
    ) -> str:
        """Claude doesn't support image generation."""
        raise NotImplementedError("Anthropic Claude does not support image generation. Use OpenAI or Gemini instead.")
