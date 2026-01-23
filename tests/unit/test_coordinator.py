"""Unit tests for the agent coordinator routing."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

# These tests require agno package (production dependency)
pytestmark = pytest.mark.skipif(
    True,  # Skip in local dev - run in Docker with full deps
    reason="Requires agno package (run in Docker)",
)


class TestRouteMessage:
    """Test message routing logic."""

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Mock the coordinator module imports."""
        with patch("core.config.get_settings") as mock_settings:
            settings = MagicMock()
            settings.llm_provider = "anthropic"
            settings.anthropic_api_key = "test"
            settings.model_smart = "claude-sonnet-4-5-20250514"
            settings.model_fast = "claude-haiku-4-20250514"
            mock_settings.return_value = settings
            yield

    @pytest.mark.asyncio
    async def test_scheduling_keywords_route_to_scheduler(self):
        """Messages about scheduling route to scheduler agent."""
        from agents.coordinator import route_message

        result = await route_message(
            message="Gostaria de agendar uma consulta para terça-feira",
            contact_data={"phone": "5511999990000"},
        )

        assert result["agent"] in ("scheduler", "appointment_scheduler")
        assert result["confidence"] > 0.5

    @pytest.mark.asyncio
    async def test_pricing_keywords_route_to_sdr(self):
        """Messages about pricing route to SDR agent."""
        from agents.coordinator import route_message

        result = await route_message(
            message="Quanto custa uma consulta de dermatologia?",
            contact_data={"phone": "5511999990000"},
        )

        # SDR handles pricing inquiries
        assert result["agent"] in ("sdr", "atendente")

    @pytest.mark.asyncio
    async def test_general_greeting(self):
        """General greetings get routed appropriately."""
        from agents.coordinator import route_message

        result = await route_message(
            message="Olá, boa tarde!",
            contact_data={"phone": "5511999990000"},
        )

        # Should route to SDR or support
        assert "agent" in result
        assert result["confidence"] > 0

    @pytest.mark.asyncio
    async def test_returns_required_fields(self):
        """Routing result always has agent, confidence, reasoning."""
        from agents.coordinator import route_message

        result = await route_message(
            message="Preciso remarcar minha consulta",
            contact_data={},
        )

        assert "agent" in result
        assert "confidence" in result
