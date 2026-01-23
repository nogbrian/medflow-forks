"""AI services for multi-provider chat and image generation."""

from app.services.ai.base import BaseAIProvider, ChatMessage, ImageGenerationRequest
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.openai_provider import OpenAIProvider
from app.services.ai.xai_provider import XAIProvider
from app.services.ai.anthropic_provider import AnthropicProvider
from app.services.ai.provider_factory import get_provider, get_available_providers
from app.services.ai.agno_service import (
    AgnoMultiModelService,
    get_multi_model_service,
    FRONTIER_MODELS,
    MultiModelResponse,
)
from app.services.ai.memory_service import (
    MemoryService,
    get_memory_service,
    MemoryEntry,
    ContextWindow,
)

__all__ = [
    # Base
    "BaseAIProvider",
    "ChatMessage",
    "ImageGenerationRequest",
    # Providers
    "GeminiProvider",
    "OpenAIProvider",
    "XAIProvider",
    "AnthropicProvider",
    "get_provider",
    "get_available_providers",
    # Multi-model
    "AgnoMultiModelService",
    "get_multi_model_service",
    "FRONTIER_MODELS",
    "MultiModelResponse",
    # Memory
    "MemoryService",
    "get_memory_service",
    "MemoryEntry",
    "ContextWindow",
]
