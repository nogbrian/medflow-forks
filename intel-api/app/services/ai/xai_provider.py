"""XAI (Grok) AI provider - Frontier Models January 2026."""

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

# XAI uses OpenAI-compatible API
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None


class XAIProvider(BaseAIProvider):
    """XAI (Grok) provider with frontier models (Grok 4)."""

    # XAI API base URL
    BASE_URL = "https://api.x.ai/v1"

    # Frontier text models (January 2026)
    TEXT_MODELS = {
        "grok-4.1-fast": "grok-4.1-fast",  # Latest and fastest
        "grok-4": "grok-4",  # Most intelligent
        "grok-3": "grok-3",  # Reasoning model
        "grok-3-mini": "grok-3-mini",  # Fast reasoning
        "grok-2-vision": "grok-2-vision-1212",  # Legacy vision
    }

    # Image models
    IMAGE_MODELS = {
        "grok-image": "grok-2-image-1212",
    }

    # Defaults
    TEXT_MODEL = "grok-4"
    TEXT_MODEL_VISION = "grok-2-vision-1212"
    IMAGE_MODEL = "grok-2-image-1212"

    def __init__(self, api_key: Optional[str] = None):
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package not installed (required for XAI)")

        settings = get_settings()
        self.api_key = api_key or settings.xai_api_key

        if not self.api_key:
            raise ValueError("XAI_API_KEY is required")

        # Use OpenAI client with XAI base URL
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.BASE_URL,
        )

    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="xai",
            display_name="xAI (Grok)",
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
        """Convert ChatMessage to XAI format (OpenAI-compatible)."""
        xai_messages = []

        # Add system prompt
        if system_prompt:
            xai_messages.append({
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

            # Add images (for vision model)
            for img in msg.images:
                if img.startswith("data:"):
                    image_url = img
                elif img.startswith("http"):
                    image_url = img
                else:
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

            # Simple text or complex content
            if len(content) == 1 and content[0]["type"] == "text":
                xai_messages.append({
                    "role": role,
                    "content": content[0]["text"],
                })
            else:
                xai_messages.append({
                    "role": role,
                    "content": content,
                })

        return xai_messages

    async def chat(
        self,
        messages: list[ChatMessage],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """Send messages and get response from Grok."""
        # Use vision model if images are present
        has_images = any(msg.images for msg in messages)
        model_name = model or (self.TEXT_MODEL_VISION if has_images else self.TEXT_MODEL)

        xai_messages = self._convert_messages(messages, system_prompt)

        logger.info("Sending message to XAI/Grok", model=model_name)

        response = await self.client.chat.completions.create(
            model=model_name,
            messages=xai_messages,
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
        """Stream chat response from Grok."""
        has_images = any(msg.images for msg in messages)
        model_name = model or (self.TEXT_MODEL_VISION if has_images else self.TEXT_MODEL)

        xai_messages = self._convert_messages(messages, system_prompt)

        logger.info("Streaming from XAI/Grok", model=model_name)

        stream = await self.client.chat.completions.create(
            model=model_name,
            messages=xai_messages,
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
        """Generate image using Grok image model."""
        model_name = model or self.IMAGE_MODEL

        # Combine prompts
        full_prompt = f"Style: {request.style_prompt}\n\nContent: {request.content_prompt}"

        logger.info(
            "Generating image with Grok",
            model=model_name,
            aspect_ratio=request.aspect_ratio,
        )

        # XAI image generation endpoint (may vary)
        response = await self.client.images.generate(
            model=model_name,
            prompt=full_prompt,
            n=1,
            response_format="b64_json",
        )

        b64_data = response.data[0].b64_json
        return f"data:image/png;base64,{b64_data}"
