"""Base utilities for Agno agents with proper database and model integration."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from core.config import get_settings

# Storage path for agent data
AGENT_STORAGE_DIR = Path(os.getenv("AGENT_STORAGE_DIR", "/tmp/agno"))
AGENT_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_agent_storage(agent_name: str):
    """Get SQLite storage for agent conversation history.

    Args:
        agent_name: Name of the agent (used as table name)

    Returns:
        SqliteAgentStorage instance for the agent
    """
    try:
        from agno.storage.agent.sqlite import SqliteAgentStorage

        db_file = AGENT_STORAGE_DIR / "agents.db"
        return SqliteAgentStorage(
            table_name=agent_name.replace("-", "_").lower(),
            db_file=str(db_file),
        )
    except ImportError:
        # Fallback if agno.storage is not available
        return None


@lru_cache
def get_db():
    """Get SQLite database connection for Agno agents.

    This is used for agent memory and session tracking.
    For production, consider using PostgreSQL via agno.db.postgres.

    Returns:
        SqliteDb instance or None if unavailable
    """
    try:
        from agno.db.sqlite import SqliteDb

        db_file = AGENT_STORAGE_DIR / "agno.db"
        return SqliteDb(db_file=str(db_file))
    except ImportError:
        # Try alternative import path
        try:
            from agno.storage.sqlite import SqliteDb

            db_file = AGENT_STORAGE_DIR / "agno.db"
            return SqliteDb(db_file=str(db_file))
        except ImportError:
            return None


def get_model(model_type: Literal["smart", "fast"] = "smart"):
    """Get the appropriate LLM model based on settings.

    Args:
        model_type: "smart" for complex tasks, "fast" for routing/simple tasks

    Returns:
        Configured LLM model instance

    Raises:
        ValueError: If provider is unknown or API key is missing
    """
    settings = get_settings()
    model_id = settings.model_smart if model_type == "smart" else settings.model_fast

    # Map providers to their model classes and API key env vars
    provider_config = {
        "anthropic": {
            "module": "agno.models.anthropic",
            "class": "Claude",
            "api_key": settings.anthropic_api_key,
            "env_var": "ANTHROPIC_API_KEY",
        },
        "openai": {
            "module": "agno.models.openai",
            "class": "OpenAIChat",
            "api_key": settings.openai_api_key,
            "env_var": "OPENAI_API_KEY",
        },
        "google": {
            "module": "agno.models.google",
            "class": "Gemini",
            "api_key": settings.google_api_key,
            "env_var": "GOOGLE_API_KEY",
        },
        "xai": {
            "module": "agno.models.xai",
            "class": "xAI",
            "api_key": settings.xai_api_key,
            "env_var": "XAI_API_KEY",
        },
    }

    if settings.llm_provider not in provider_config:
        raise ValueError(
            f"Unknown LLM provider: {settings.llm_provider}. "
            f"Supported: {list(provider_config.keys())}"
        )

    config = provider_config[settings.llm_provider]

    # Set API key in environment if provided (Agno reads from env)
    if config["api_key"]:
        os.environ[config["env_var"]] = config["api_key"]
    elif not os.getenv(config["env_var"]):
        raise ValueError(
            f"No API key for {settings.llm_provider}. "
            f"Set {config['env_var']} in environment or config."
        )

    # Dynamic import of the model class
    import importlib

    module = importlib.import_module(config["module"])
    model_class = getattr(module, config["class"])

    return model_class(id=model_id)


def create_agent(
    name: str,
    instructions: str | list[str],
    tools: list | None = None,
    model_type: Literal["smart", "fast"] = "smart",
    user_id: str | None = None,
    session_id: str | None = None,
    add_history: bool = True,
    markdown: bool = True,
):
    """Create a configured Agno agent with proper storage and model.

    Args:
        name: Agent name (used for storage table)
        instructions: Agent instructions/system prompt
        tools: List of tools available to the agent
        model_type: "smart" or "fast" model
        user_id: User identifier for memory
        session_id: Session identifier for conversation
        add_history: Whether to add conversation history to context
        markdown: Whether to format output as markdown

    Returns:
        Configured Agent instance
    """
    from agno.agent import Agent

    return Agent(
        name=name,
        model=get_model(model_type),
        storage=get_agent_storage(name),
        db=get_db(),
        instructions=instructions,
        tools=tools or [],
        user_id=user_id,
        session_id=session_id,
        add_history_to_context=add_history,
        markdown=markdown,
    )


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
