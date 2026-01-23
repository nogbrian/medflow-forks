"""Factory for creating AI providers."""

from typing import Optional
import structlog

from app.config import get_settings
from app.services.ai.base import BaseAIProvider, ProviderInfo

logger = structlog.get_logger(__name__)


def get_provider(provider_name: str, api_key: Optional[str] = None) -> BaseAIProvider:
    """
    Get an AI provider instance.

    Args:
        provider_name: Name of the provider ('gemini', 'openai', 'xai')
        api_key: Optional API key override

    Returns:
        Provider instance

    Raises:
        ValueError: If provider is not supported or not configured
    """
    provider_name = provider_name.lower()

    if provider_name == "gemini":
        from app.services.ai.gemini_provider import GeminiProvider
        return GeminiProvider(api_key=api_key)

    elif provider_name == "openai":
        from app.services.ai.openai_provider import OpenAIProvider
        return OpenAIProvider(api_key=api_key)

    elif provider_name == "xai" or provider_name == "grok":
        from app.services.ai.xai_provider import XAIProvider
        return XAIProvider(api_key=api_key)

    elif provider_name == "anthropic" or provider_name == "claude":
        from app.services.ai.anthropic_provider import AnthropicProvider
        return AnthropicProvider()

    else:
        raise ValueError(f"Unknown provider: {provider_name}")


def get_available_providers() -> list[ProviderInfo]:
    """
    Get list of available (configured) providers.

    Returns:
        List of provider info for configured providers
    """
    settings = get_settings()
    available = []

    # Check Gemini
    if settings.gemini_api_key:
        try:
            from app.services.ai.gemini_provider import GeminiProvider, GEMINI_AVAILABLE
            if GEMINI_AVAILABLE:
                available.append(GeminiProvider(settings.gemini_api_key).info)
        except Exception as e:
            logger.warning("Gemini provider not available", error=str(e))

    # Check OpenAI
    if settings.openai_api_key:
        try:
            from app.services.ai.openai_provider import OpenAIProvider, OPENAI_AVAILABLE
            if OPENAI_AVAILABLE:
                available.append(OpenAIProvider(settings.openai_api_key).info)
        except Exception as e:
            logger.warning("OpenAI provider not available", error=str(e))

    # Check XAI
    if settings.xai_api_key:
        try:
            from app.services.ai.xai_provider import XAIProvider, OPENAI_AVAILABLE
            if OPENAI_AVAILABLE:
                available.append(XAIProvider(settings.xai_api_key).info)
        except Exception as e:
            logger.warning("XAI provider not available", error=str(e))

    # Check Anthropic
    if settings.anthropic_api_key:
        try:
            from app.services.ai.anthropic_provider import AnthropicProvider
            available.append(AnthropicProvider().info)
        except Exception as e:
            logger.warning("Anthropic provider not available", error=str(e))

    return available


def get_default_provider() -> Optional[BaseAIProvider]:
    """
    Get the default configured provider.

    Returns:
        Default provider instance or None if none configured
    """
    settings = get_settings()

    # Try configured default
    default = settings.default_ai_provider

    if default:
        try:
            return get_provider(default)
        except (ValueError, ImportError):
            pass

    # Fallback: try each provider in order
    for provider_name in ["openai", "anthropic", "gemini", "xai"]:
        try:
            return get_provider(provider_name)
        except (ValueError, ImportError):
            continue

    return None
