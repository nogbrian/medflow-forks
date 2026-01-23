"""
Agno-based multi-model orchestration service.

Uses Agno framework for:
- Multi-model comparison (run same prompt on multiple models)
- Memory management (PostgreSQL + pgvector)
- Context engineering
- Agent orchestration
"""

import asyncio
from typing import Optional
from dataclasses import dataclass
import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)

# Lazy imports for Agno
try:
    from agno.agent import Agent
    from agno.models.openai import OpenAI
    from agno.models.anthropic import Claude
    from agno.models.google import Gemini
    from agno.models.xai import Grok
    from agno.memory.db.postgres import PgMemory
    from agno.knowledge.vectordb.pgvector import PgVector
    from agno.embedder.openai import OpenAIEmbedder
    AGNO_AVAILABLE = True
except ImportError:
    AGNO_AVAILABLE = False
    logger.warning("Agno not installed. Multi-model features will be limited.")


@dataclass
class ModelConfig:
    """Configuration for a model."""
    provider: str
    model_id: str
    display_name: str
    supports_vision: bool = True
    supports_images: bool = False


# Frontier models configuration (January 2026)
FRONTIER_MODELS = {
    # OpenAI
    "gpt-5.2": ModelConfig("openai", "gpt-5.2", "GPT-5.2", True, True),
    "gpt-5.1": ModelConfig("openai", "gpt-5.1", "GPT-5.1", True, True),
    "gpt-5": ModelConfig("openai", "gpt-5", "GPT-5", True, True),

    # Anthropic
    "claude-opus-4.5": ModelConfig("anthropic", "claude-opus-4-5-20251101", "Claude Opus 4.5", True, False),
    "claude-sonnet-4.5": ModelConfig("anthropic", "claude-sonnet-4-5-20251101", "Claude Sonnet 4.5", True, False),
    "claude-opus-4.1": ModelConfig("anthropic", "claude-opus-4-1-20250805", "Claude Opus 4.1", True, False),

    # Google
    "gemini-3-pro": ModelConfig("google", "gemini-3-pro-preview", "Gemini 3 Pro", True, True),
    "gemini-3-flash": ModelConfig("google", "gemini-3-flash-preview", "Gemini 3 Flash", True, True),
    "gemini-2.5-pro": ModelConfig("google", "gemini-2.5-pro", "Gemini 2.5 Pro", True, True),

    # xAI
    "grok-4.1": ModelConfig("xai", "grok-4.1-fast", "Grok 4.1 Fast", True, True),
    "grok-4": ModelConfig("xai", "grok-4", "Grok 4", True, True),
    "grok-3": ModelConfig("xai", "grok-3", "Grok 3", True, True),
}


@dataclass
class MultiModelResponse:
    """Response from multiple models."""
    model_id: str
    provider: str
    display_name: str
    content: str
    images: list[str] | None = None
    error: str | None = None
    latency_ms: float = 0


class AgnoMultiModelService:
    """
    Service for running prompts across multiple models simultaneously.
    Uses Agno for orchestration when available.
    """

    def __init__(self):
        self.settings = get_settings()
        self._agents: dict[str, Agent] = {}
        self._memory = None
        self._knowledge = None

    def _get_agno_model(self, model_key: str):
        """Get Agno model instance for a given model key."""
        if not AGNO_AVAILABLE:
            return None

        config = FRONTIER_MODELS.get(model_key)
        if not config:
            return None

        settings = self.settings

        if config.provider == "openai":
            return OpenAI(
                id=config.model_id,
                api_key=settings.openai_api_key,
            )
        elif config.provider == "anthropic":
            return Claude(
                id=config.model_id,
                api_key=settings.anthropic_api_key,
            )
        elif config.provider == "google":
            return Gemini(
                id=config.model_id,
                api_key=settings.gemini_api_key,
            )
        elif config.provider == "xai":
            return Grok(
                id=config.model_id,
                api_key=settings.xai_api_key,
            )

        return None

    def _get_agent(self, model_key: str, system_prompt: str | None = None) -> Agent | None:
        """Get or create an Agno agent for a model."""
        if not AGNO_AVAILABLE:
            return None

        cache_key = f"{model_key}:{hash(system_prompt or '')}"

        if cache_key not in self._agents:
            model = self._get_agno_model(model_key)
            if not model:
                return None

            agent = Agent(
                model=model,
                instructions=system_prompt,
                markdown=True,
                show_tool_calls=False,
            )
            self._agents[cache_key] = agent

        return self._agents[cache_key]

    async def chat_single(
        self,
        model_key: str,
        message: str,
        images: list[str] | None = None,
        system_prompt: str | None = None,
    ) -> MultiModelResponse:
        """Send a message to a single model."""
        import time

        config = FRONTIER_MODELS.get(model_key)
        if not config:
            return MultiModelResponse(
                model_id=model_key,
                provider="unknown",
                display_name=model_key,
                content="",
                error=f"Unknown model: {model_key}",
            )

        start_time = time.time()

        try:
            # Try Agno first
            if AGNO_AVAILABLE:
                agent = self._get_agent(model_key, system_prompt)
                if agent:
                    # Build message with images if present
                    if images:
                        # Agno handles multimodal via message content
                        response = await agent.arun(message, images=images)
                    else:
                        response = await agent.arun(message)

                    latency = (time.time() - start_time) * 1000

                    return MultiModelResponse(
                        model_id=config.model_id,
                        provider=config.provider,
                        display_name=config.display_name,
                        content=response.content if hasattr(response, 'content') else str(response),
                        latency_ms=latency,
                    )

            # Fallback to direct provider
            from app.services.ai import get_provider
            from app.services.ai.base import ChatMessage, MessageRole

            provider = get_provider(config.provider)
            messages = [
                ChatMessage(
                    role=MessageRole.USER,
                    content=message,
                    images=images or [],
                )
            ]

            response = await provider.chat(
                messages=messages,
                system_prompt=system_prompt,
                model=config.model_id,
            )

            latency = (time.time() - start_time) * 1000

            return MultiModelResponse(
                model_id=config.model_id,
                provider=config.provider,
                display_name=config.display_name,
                content=response,
                latency_ms=latency,
            )

        except Exception as e:
            logger.error("Model chat failed", model=model_key, error=str(e))
            latency = (time.time() - start_time) * 1000

            return MultiModelResponse(
                model_id=config.model_id,
                provider=config.provider,
                display_name=config.display_name,
                content="",
                error=str(e),
                latency_ms=latency,
            )

    async def chat_multi(
        self,
        model_keys: list[str],
        message: str,
        images: list[str] | None = None,
        system_prompt: str | None = None,
    ) -> list[MultiModelResponse]:
        """
        Send the same message to multiple models in parallel.
        Returns responses from all models for comparison.
        """
        tasks = [
            self.chat_single(model_key, message, images, system_prompt)
            for model_key in model_keys
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        results = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                config = FRONTIER_MODELS.get(model_keys[i])
                results.append(MultiModelResponse(
                    model_id=model_keys[i],
                    provider=config.provider if config else "unknown",
                    display_name=config.display_name if config else model_keys[i],
                    content="",
                    error=str(response),
                ))
            else:
                results.append(response)

        return results

    def get_available_models(self) -> list[dict]:
        """Get list of available frontier models."""
        settings = self.settings
        available = []

        for key, config in FRONTIER_MODELS.items():
            # Check if provider API key is configured
            has_key = False
            if config.provider == "openai" and settings.openai_api_key:
                has_key = True
            elif config.provider == "anthropic" and settings.anthropic_api_key:
                has_key = True
            elif config.provider == "google" and settings.gemini_api_key:
                has_key = True
            elif config.provider == "xai" and settings.xai_api_key:
                has_key = True

            available.append({
                "key": key,
                "model_id": config.model_id,
                "provider": config.provider,
                "display_name": config.display_name,
                "supports_vision": config.supports_vision,
                "supports_images": config.supports_images,
                "available": has_key,
            })

        return available


# Singleton instance
_service: AgnoMultiModelService | None = None


def get_multi_model_service() -> AgnoMultiModelService:
    """Get singleton multi-model service instance."""
    global _service
    if _service is None:
        _service = AgnoMultiModelService()
    return _service
