"""Base utilities for Agno agents."""

from functools import lru_cache
from typing import Literal

from config import get_settings


@lru_cache
def get_db():
    """Get cached Postgres database connection for Agno agents.

    Returns None for now - database integration will be added later.
    """
    # TODO: Fix agno.db.postgres import - the module structure has changed
    # For now, return None to allow the app to start
    return None


def get_model(model_type: Literal["smart", "fast"] = "smart"):
    """
    Get the appropriate LLM model based on settings.

    Args:
        model_type: "smart" for complex tasks, "fast" for routing/simple tasks

    Returns:
        Configured LLM model instance
    """
    settings = get_settings()
    model_id = settings.model_smart if model_type == "smart" else settings.model_fast

    if settings.llm_provider == "anthropic":
        from agno.models.anthropic import Claude

        return Claude(id=model_id)

    elif settings.llm_provider == "openai":
        from agno.models.openai import OpenAIChat

        return OpenAIChat(id=model_id)

    elif settings.llm_provider == "google":
        from agno.models.google import Gemini

        return Gemini(id=model_id)

    else:
        raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")


# Default model IDs per provider (frontier models as of Jan 2026)
DEFAULT_MODELS = {
    "anthropic": {
        "smart": "claude-sonnet-4-5-20250514",
        "fast": "claude-haiku-4-20250514",
    },
    "openai": {
        "smart": "gpt-5.2",
        "fast": "gpt-5.2-mini",
    },
    "google": {
        "smart": "gemini-2.5-pro",
        "fast": "gemini-2.5-flash",
    },
    "xai": {
        "smart": "grok-4.1",
        "fast": "grok-4",
    },
}
