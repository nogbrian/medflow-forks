"""OpenAI AI provider (GPT-5.2 + GPT Image 1.5) - Frontier Models January 2026."""

import base64
import structlog
from typing import AsyncIterator, Optional

from app.config import get_settings
from app.services.ai.base import (
    BaseAIProvider,
    ChatMessage,
    ImageGenerationRequest,
    MessageRole,
    ProviderInfo,
)

logger = structlog.get_logger(__name__)

# Lazy import
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None


class OpenAIProvider(BaseAIProvider):
    """OpenAI provider with frontier models (GPT-5.2 + GPT Image 1.5)."""

    # Frontier text models (January 2026)
    TEXT_MODELS = {
        "gpt-5.2": "gpt-5.2",  # Latest frontier with reasoning
        "gpt-5.1": "gpt-5.1",  # Previous frontier
        "gpt-5": "gpt-5",  # Base GPT-5
        "gpt-4o": "gpt-4o",  # Legacy (retiring Feb 2026)
    }

    # Frontier image models
    IMAGE_MODELS = {
        "gpt-image-1.5": "gpt-image-1.5",  # Latest image generation
        "dall-e-3": "dall-e-3",  # Legacy
    }

    # Defaults
    TEXT_MODEL = "gpt-5.2"
    IMAGE_MODEL = "gpt-image-1.5"

    def __init__(self, api_key: Optional[str] = None):
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package not installed")

        settings = get_settings()
        self.api_key = api_key or settings.openai_api_key

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required")

        self.client = AsyncOpenAI(api_key=self.api_key)

    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="openai",
            display_name="OpenAI",
            supports_chat=True,
            supports_image_generation=True,
            supports_vision=True,
            text_models=list(self.TEXT_MODELS.keys()),
            image_models=list(self.IMAGE_MODELS.keys()),
        )

    def _convert_messages(
        self,
        messages: list[ChatMessage],
        system_prompt: Optional[str] = None,
    ) -> list[dict]:
        """Convert ChatMessage to OpenAI format."""
        openai_messages = []

        # Add system prompt
        if system_prompt:
            openai_messages.append({
                "role": "system",
                "content": system_prompt,
            })

        for msg in messages:
            content = []

            # Add text
            if msg.content:
                content.append({
                    "type": "text",
                    "text": msg.content,
                })

            # Add images
            for img in msg.images:
                if img.startswith("data:"):
                    # Already a data URL
                    image_url = img
                elif img.startswith("http"):
                    # External URL
                    image_url = img
                else:
                    # Assume base64 without header
                    image_url = f"data:image/png;base64,{img}"

                content.append({
                    "type": "image_url",
                    "image_url": {"url": image_url},
                })

            # Determine role
            if msg.role == MessageRole.USER:
                role = "user"
            elif msg.role == MessageRole.ASSISTANT:
                role = "assistant"
            else:
                role = "system"

            # For simple text messages, use string content
            if len(content) == 1 and content[0]["type"] == "text":
                openai_messages.append({
                    "role": role,
                    "content": content[0]["text"],
                })
            else:
                openai_messages.append({
                    "role": role,
                    "content": content,
                })

        return openai_messages

    async def chat(
        self,
        messages: list[ChatMessage],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """Send messages and get response."""
        model_name = model or self.TEXT_MODEL

        openai_messages = self._convert_messages(messages, system_prompt)

        logger.info("Sending message to OpenAI", model=model_name)

        response = await self.client.chat.completions.create(
            model=model_name,
            messages=openai_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content or ""

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """Stream chat response."""
        model_name = model or self.TEXT_MODEL

        openai_messages = self._convert_messages(messages, system_prompt)

        logger.info("Streaming from OpenAI", model=model_name)

        stream = await self.client.chat.completions.create(
            model=model_name,
            messages=openai_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def generate_image(
        self,
        request: ImageGenerationRequest,
        model: Optional[str] = None,
    ) -> str:
        """Generate image using DALL-E 3."""
        model_name = model or self.IMAGE_MODEL

        # Combine prompts
        full_prompt = f"Style: {request.style_prompt}\n\nContent: {request.content_prompt}"

        # Map aspect ratio to DALL-E size
        size_map = {
            "1:1": "1024x1024",
            "16:9": "1792x1024",
            "9:16": "1024x1792",
            "3:4": "1024x1024",  # DALL-E doesn't support 3:4, use square
            "4:3": "1792x1024",
        }
        size = size_map.get(request.aspect_ratio, "1024x1024")

        logger.info(
            "Generating image with DALL-E",
            model=model_name,
            size=size,
        )

        response = await self.client.images.generate(
            model=model_name,
            prompt=full_prompt,
            size=size,
            quality="hd",
            n=1,
            response_format="b64_json",
        )

        # Return as data URL
        b64_data = response.data[0].b64_json
        return f"data:image/png;base64,{b64_data}"
