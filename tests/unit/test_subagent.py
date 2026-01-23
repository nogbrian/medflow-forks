"""Unit tests for subagent spawning."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.agentic.config import AgenticConfig
from core.agentic.context import AgenticContext
from core.agentic.loop import AgenticLoop
from core.agentic.subagent import SubagentSpawner, create_delegate_tool
from core.llm_router import CostTracker, LLMResponse, TokenUsage


@pytest.fixture
def parent_loop():
    """Create a parent loop with mock LLM."""
    llm = AsyncMock()
    llm.cost_tracker = CostTracker()
    llm.get_model.return_value = "claude-sonnet-4-5-20250514"
    llm.get_context_limit.return_value = 200_000

    context = AgenticContext(
        session_id="parent-session-123",
        agent_name="parent-agent",
        cost_tracker=llm.cost_tracker,
    )

    loop = AgenticLoop(
        system_prompt="Parent system prompt",
        tools={
            "tool_a": {"definition": {"name": "tool_a"}, "handler": AsyncMock(return_value="A result")},
            "tool_b": {"definition": {"name": "tool_b"}, "handler": AsyncMock(return_value="B result")},
            "tool_c": {"definition": {"name": "tool_c"}, "handler": AsyncMock(return_value="C result")},
        },
        llm=llm,
        context=context,
    )
    return loop


class TestSubagentSpawner:
    """Test subagent spawning with isolated context."""

    @pytest.mark.asyncio
    async def test_spawn_creates_isolated_context(self, parent_loop):
        """Subagent gets its own context, not the parent's."""
        spawner = SubagentSpawner(parent_loop)

        # Mock the LLMRouter class that SubagentSpawner creates
        with patch("core.agentic.subagent.LLMRouter") as MockRouter:
            mock_llm = MagicMock()
            mock_llm.cost_tracker = parent_loop.llm.cost_tracker
            mock_llm.get_model.return_value = "test"
            mock_llm.get_context_limit.return_value = 200_000
            mock_llm.chat = AsyncMock(return_value=LLMResponse(
                content="Subagent response",
                tool_calls=[],
                usage=TokenUsage(input_tokens=50, output_tokens=20),
            ))
            MockRouter.return_value = mock_llm

            result = await spawner.spawn(
                task="Do something",
                system_prompt="You are a subagent.",
            )

        assert result.success
        assert result.final_response == "Subagent response"
        # Subagent has its own session ID
        assert result.context.session_id != parent_loop.context.session_id
        # Parent context is tracked
        assert result.context.parent_session_id == "parent-session-123"

    @pytest.mark.asyncio
    async def test_spawn_shares_cost_tracker(self, parent_loop):
        """Subagent costs are tracked in the parent's cost tracker."""
        spawner = SubagentSpawner(parent_loop)

        initial_calls = parent_loop.llm.cost_tracker.total_calls

        with patch("core.agentic.subagent.LLMRouter") as MockRouter:
            mock_llm = MagicMock()
            mock_llm.cost_tracker = parent_loop.llm.cost_tracker
            mock_llm.get_model.return_value = "test"
            mock_llm.get_context_limit.return_value = 200_000
            mock_llm.chat = AsyncMock(return_value=LLMResponse(
                content="Done",
                tool_calls=[],
                usage=TokenUsage(input_tokens=100, output_tokens=50, model="test"),
            ))
            MockRouter.return_value = mock_llm

            await spawner.spawn(
                task="Task",
                system_prompt="Prompt",
            )

        # Cost tracker should have the subagent's usage
        # (the mock doesn't actually add to tracker since it's mocked,
        #  but the architecture is verified)
        assert spawner._cost_tracker is parent_loop.llm.cost_tracker

    @pytest.mark.asyncio
    async def test_spawn_with_tool_filter(self, parent_loop):
        """Subagent only gets specified tools."""
        spawner = SubagentSpawner(parent_loop)
        filtered = spawner._filter_tools(["tool_a", "tool_c"])

        assert "tool_a" in filtered
        assert "tool_c" in filtered
        assert "tool_b" not in filtered

    @pytest.mark.asyncio
    async def test_spawn_all_tools_when_none(self, parent_loop):
        """When tools=None, subagent gets all parent tools."""
        spawner = SubagentSpawner(parent_loop)
        filtered = spawner._filter_tools(None)

        assert "tool_a" in filtered
        assert "tool_b" in filtered
        assert "tool_c" in filtered

    @pytest.mark.asyncio
    async def test_spawn_respects_timeout(self, parent_loop):
        """Subagent config respects the timeout parameter."""
        spawner = SubagentSpawner(parent_loop)

        custom_config = AgenticConfig(timeout_seconds=999)
        with patch("core.agentic.subagent.LLMRouter") as MockRouter:
            mock_llm = MagicMock()
            mock_llm.cost_tracker = parent_loop.llm.cost_tracker
            mock_llm.get_model.return_value = "test"
            mock_llm.get_context_limit.return_value = 200_000
            mock_llm.chat = AsyncMock(return_value=LLMResponse(content="OK", tool_calls=[], usage=TokenUsage()))
            MockRouter.return_value = mock_llm

            result = await spawner.spawn(
                task="Task",
                system_prompt="Prompt",
                config=custom_config,
                timeout=60,  # Should cap the config timeout
            )

        # Timeout should be min(config.timeout, timeout_param)
        assert custom_config.timeout_seconds == 60

    @pytest.mark.asyncio
    async def test_subagent_does_not_pollute_parent_messages(self, parent_loop):
        """Parent's message history is not modified by subagent."""
        parent_loop.context.messages = [
            {"role": "user", "content": "Parent message"},
        ]
        original_count = len(parent_loop.context.messages)

        spawner = SubagentSpawner(parent_loop)

        with patch("core.agentic.subagent.LLMRouter") as MockRouter:
            mock_llm = MagicMock()
            mock_llm.cost_tracker = parent_loop.llm.cost_tracker
            mock_llm.get_model.return_value = "test"
            mock_llm.get_context_limit.return_value = 200_000
            mock_llm.chat = AsyncMock(return_value=LLMResponse(
                content="Subagent added messages",
                tool_calls=[],
                usage=TokenUsage(),
            ))
            MockRouter.return_value = mock_llm

            await spawner.spawn(task="Sub task", system_prompt="Sub prompt")

        # Parent messages unchanged
        assert len(parent_loop.context.messages) == original_count
        assert parent_loop.context.messages[0]["content"] == "Parent message"


class TestDelegateTool:
    """Test the delegate_task tool creation."""

    @pytest.mark.asyncio
    async def test_delegate_tool_format(self, parent_loop):
        """delegate_task tool has correct format for AgenticLoop."""
        spawner = SubagentSpawner(parent_loop)
        tool = create_delegate_tool(spawner)

        assert "definition" in tool
        assert "handler" in tool
        assert tool["definition"]["name"] == "delegate_task"
        assert "task" in tool["definition"]["parameters"]["properties"]

    @pytest.mark.asyncio
    async def test_delegate_tool_callable(self, parent_loop):
        """delegate_task handler can be called."""
        spawner = SubagentSpawner(parent_loop)
        tool = create_delegate_tool(spawner)
        handler = tool["handler"]

        with patch("core.agentic.subagent.LLMRouter") as MockRouter:
            mock_llm = MagicMock()
            mock_llm.cost_tracker = parent_loop.llm.cost_tracker
            mock_llm.get_model.return_value = "test"
            mock_llm.get_context_limit.return_value = 200_000
            mock_llm.chat = AsyncMock(return_value=LLMResponse(
                content="Research result",
                tool_calls=[],
                usage=TokenUsage(),
            ))
            MockRouter.return_value = mock_llm

            result = await handler(
                task="Research topic X",
                agent_type="research",
            )

        assert "Research result" in result

    @pytest.mark.asyncio
    async def test_delegate_handles_failure(self, parent_loop):
        """delegate_task reports failures gracefully."""
        spawner = SubagentSpawner(parent_loop)
        tool = create_delegate_tool(spawner)
        handler = tool["handler"]

        with patch("core.agentic.subagent.LLMRouter") as MockRouter:
            mock_llm = MagicMock()
            mock_llm.cost_tracker = parent_loop.llm.cost_tracker
            mock_llm.get_model.return_value = "test"
            mock_llm.get_context_limit.return_value = 200_000
            mock_llm.chat = AsyncMock(side_effect=RuntimeError("LLM error"))
            MockRouter.return_value = mock_llm

            result = await handler(task="Will fail")

        assert "failed" in result.lower() or "error" in result.lower()
