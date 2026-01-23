"""Shared test fixtures and configuration."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from types import ModuleType

import pytest

# Add integration directory to path so imports work
integration_path = str(Path(__file__).parent.parent / "integration")
if integration_path not in sys.path:
    sys.path.insert(0, integration_path)

# Prevent core/__init__.py from importing heavy modules (database, auth, models)
# by intercepting the import. The unit tests only need core.config, core.logging,
# core.tools.*, and core.agentic.* — none of which need SQLAlchemy.
import importlib

# First, create a minimal core module that doesn't import database/auth/models
_core_module = ModuleType("core")
_core_module.__path__ = [str(Path(__file__).parent.parent / "integration" / "core")]
_core_module.__package__ = "core"
sys.modules["core"] = _core_module

# Now import the sub-modules we actually need
# core.config needs pydantic_settings which we have
core_config = importlib.import_module("core.config")
sys.modules["core.config"] = core_config
_core_module.get_settings = core_config.get_settings
_core_module.Settings = core_config.Settings

# core.logging needs structlog which we have
core_logging = importlib.import_module("core.logging")
sys.modules["core.logging"] = core_logging

# Create a minimal tools module that doesn't import apify/database_tools/image_gen etc.
# This lets tests import tools.crm, tools.calendar, tools.chatwoot directly.
_tools_module = ModuleType("tools")
_tools_module.__path__ = [str(Path(__file__).parent.parent / "integration" / "tools")]
_tools_module.__package__ = "tools"
sys.modules["tools"] = _tools_module

# Import only the tool modules we need for API route tests
_tools_crm = importlib.import_module("tools.crm")
sys.modules["tools.crm"] = _tools_crm

_tools_calendar = importlib.import_module("tools.calendar")
sys.modules["tools.calendar"] = _tools_calendar

_tools_chatwoot = importlib.import_module("tools.chatwoot")
sys.modules["tools.chatwoot"] = _tools_chatwoot

# Create minimal api and api.routes packages (without triggering auth/sqlalchemy imports)
if "api" not in sys.modules:
    _api_module = ModuleType("api")
    _api_module.__path__ = [str(Path(__file__).parent.parent / "integration" / "api")]
    _api_module.__package__ = "api"
    sys.modules["api"] = _api_module

if "api.routes" not in sys.modules:
    _routes_module = ModuleType("api.routes")
    _routes_module.__path__ = [str(Path(__file__).parent.parent / "integration" / "api" / "routes")]
    _routes_module.__package__ = "api.routes"
    sys.modules["api.routes"] = _routes_module


@pytest.fixture
def mock_settings():
    """Mock application settings with test values."""
    with patch("core.config.get_settings") as mock:
        settings = MagicMock()
        settings.app_env = "development"
        settings.llm_provider = "anthropic"
        settings.anthropic_api_key = "test-key-anthropic"
        settings.openai_api_key = "test-key-openai"
        settings.google_api_key = None
        settings.xai_api_key = None
        settings.model_smart = "claude-sonnet-4-5-20250514"
        settings.model_fast = "claude-haiku-4-20250514"
        settings.webhook_secret = "test-webhook-secret"
        settings.evolution_api_url = "http://localhost:8080"
        settings.evolution_api_key = "test-evolution-key"
        settings.chatwoot_api_url = "http://localhost:3000"
        settings.chatwoot_api_key = "test-chatwoot-key"
        settings.chatwoot_account_id = "1"
        settings.chatwoot_inbox_id = "1"
        settings.chatwoot_human_team_id = "1"
        settings.twenty_api_url = "http://localhost:3001"
        settings.twenty_api_key = "test-twenty-key"
        settings.calcom_api_url = "http://localhost:3002"
        settings.calcom_api_key = "test-calcom-key"
        settings.meta_access_token = None
        settings.database_url = "sqlite+aiosqlite:///test.db"
        settings.redis_url = "redis://localhost:6379"
        mock.return_value = settings
        yield settings


@pytest.fixture
def mock_llm_response():
    """Factory for creating mock LLM responses."""
    from core.llm_router import LLMResponse, TokenUsage

    def _make(
        content: str = "Test response",
        tool_calls: list = None,
        input_tokens: int = 100,
        output_tokens: int = 50,
    ) -> LLMResponse:
        return LLMResponse(
            content=content,
            tool_calls=tool_calls or [],
            usage=TokenUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model="claude-sonnet-4-5-20250514",
            ),
            stop_reason="end_turn",
        )

    return _make


@pytest.fixture
def sample_tools():
    """Sample tool definitions for testing the agentic loop."""

    async def echo_tool(message: str) -> str:
        return f"Echo: {message}"

    async def add_tool(a: int, b: int) -> str:
        return str(a + b)

    async def failing_tool(input: str) -> str:
        raise RuntimeError("Tool execution failed")

    return {
        "echo": {
            "definition": {
                "name": "echo",
                "description": "Echo a message back",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "Message to echo"},
                    },
                    "required": ["message"],
                },
            },
            "handler": echo_tool,
        },
        "add": {
            "definition": {
                "name": "add",
                "description": "Add two numbers",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "integer", "description": "First number"},
                        "b": {"type": "integer", "description": "Second number"},
                    },
                    "required": ["a", "b"],
                },
            },
            "handler": add_tool,
        },
        "failing": {
            "definition": {
                "name": "failing",
                "description": "A tool that always fails",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input": {"type": "string"},
                    },
                    "required": ["input"],
                },
            },
            "handler": failing_tool,
        },
    }
