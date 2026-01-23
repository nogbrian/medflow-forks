"""Google Gemini AI provider - Frontier Models January 2026."""

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

# Lazy import to avoid issues if package not installed
try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None


class GeminiProvider(BaseAIProvider):
    """Google Gemini AI provider with frontier models (Gemini 3)."""

    # Frontier text models (January 2026)
    TEXT_MODELS = {
        "gemini-3-pro": "gemini-3-pro-preview",  # State-of-the-art reasoning
        "gemini-3-flash": "gemini-3-flash-preview",  # Fast frontier
        "gemini-2.5-pro": "gemini-2.5-pro",  # Production tier
        "gemini-2.5-flash": "gemini-2.5-flash",  # Production fast
        "gemini-2.0-flash": "gemini-2.0-flash",  # Legacy
    }

    # Image models (Imagen 4)
    IMAGE_MODELS = {
        "imagen-4": "imagen-4",  # Latest image generation
        "imagen-3": "imagen-3",  # Previous gen
    }

    # Defaults
    TEXT_MODEL = "gemini-3-flash-preview"
    IMAGE_MODEL = "imagen-4"

    def __init__(self, api_key: Optional[str] = None):
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai package not installed")

        settings = get_settings()
        self.api_key = api_key or settings.gemini_api_key

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required")

        genai.configure(api_key=self.api_key)

    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="gemini",
            display_name="Google Gemini",
            supports_chat=True,
            supports_image_generation=False,  # Native Gemini doesn't generate images
            supports_vision=True,
            text_models=list(self.TEXT_MODELS.keys()),
            image_models=list(self.IMAGE_MODELS.keys()),
        )

    def _convert_messages(self, messages: list[ChatMessage]) -> list[dict]:
        """Convert ChatMessage to Gemini format."""
        history = []

        for msg in messages:
            parts = []

            # Add text content
            if msg.content:
                parts.append(msg.content)

            # Add images
            for img in msg.images:
                if img.startswith("data:"):
                    # Parse data URL
                    header, data = img.split(",", 1)
                    mime_type = header.split(";")[0].split(":")[1]
                    parts.append({
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": data,
                        }
                    })
                else:
                    # Assume it's a URL or base64 without header
                    parts.append({
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": img,
                        }
                    })

            role = "user" if msg.role == MessageRole.USER else "model"
            history.append({"role": role, "parts": parts})

        return history

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

        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        model_instance = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config,
            safety_settings=safety_settings,
            system_instruction=system_prompt,
        )

        # Convert messages to Gemini format
        history = self._convert_messages(messages[:-1]) if len(messages) > 1 else []

        # Start chat with history
        chat = model_instance.start_chat(history=history)

        # Get last message
        last_msg = messages[-1]
        parts = [last_msg.content] if last_msg.content else []

        # Add images from last message
        for img in last_msg.images:
            if img.startswith("data:"):
                header, data = img.split(",", 1)
                mime_type = header.split(";")[0].split(":")[1]
                parts.append({
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": data,
                    }
                })

        logger.info("Sending message to Gemini", model=model_name)

        response = await chat.send_message_async(parts)

        return response.text

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

        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        model_instance = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config,
            safety_settings=safety_settings,
            system_instruction=system_prompt,
        )

        history = self._convert_messages(messages[:-1]) if len(messages) > 1 else []
        chat = model_instance.start_chat(history=history)

        last_msg = messages[-1]
        parts = [last_msg.content] if last_msg.content else []

        for img in last_msg.images:
            if img.startswith("data:"):
                header, data = img.split(",", 1)
                mime_type = header.split(";")[0].split(":")[1]
                parts.append({
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": data,
                    }
                })

        logger.info("Streaming from Gemini", model=model_name)

        response = await chat.send_message_async(parts, stream=True)

        async for chunk in response:
            if chunk.text:
                yield chunk.text

    async def generate_image(
        self,
        request: ImageGenerationRequest,
        model: Optional[str] = None,
    ) -> str:
        """
        Generate image.

        Note: Gemini doesn't have built-in image generation.
        This would need to use Google's Imagen API separately.
        For now, raise NotImplementedError.
        """
        raise NotImplementedError(
            "Gemini doesn't support native image generation. "
            "Use OpenAI (DALL-E) for image generation."
        )
