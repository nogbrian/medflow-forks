"""Unit tests for the agentic loop."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.agentic.config import AgenticConfig
from core.agentic.context import AgenticContext
from core.agentic.loop import AgenticLoop
from core.llm_router import LLMResponse, TokenUsage


@pytest.fixture
def mock_llm():
    """Create a mock LLM router."""
    llm = MagicMock()
    llm.cost_tracker = MagicMock()
    llm.cost_tracker.total_cost_usd = 0.0
    llm.cost_tracker.total_input_tokens = 0
    llm.cost_tracker.total_output_tokens = 0
    llm.cost_tracker.total_calls = 0
    llm.cost_tracker.to_dict.return_value = {"total_cost_usd": 0.0, "total_calls": 0, "total_input_tokens": 0, "total_output_tokens": 0}
    llm.cost_tracker.add = MagicMock()
    llm.get_model.return_value = "claude-sonnet-4-5-20250514"
    llm.get_context_limit.return_value = 200_000
    # chat() is async
    llm.chat = AsyncMock()
    llm.chat_stream = AsyncMock()
    return llm


class TestAgenticLoopBasic:
    """Test basic loop execution without tool calls."""

    @pytest.mark.asyncio
    async def test_simple_response(self, mock_llm, sample_tools):
        """Loop returns immediately when LLM produces no tool calls."""
        mock_llm.chat.return_value = LLMResponse(
            content="Hello! How can I help?",
            tool_calls=[],
            usage=TokenUsage(input_tokens=50, output_tokens=20),
            stop_reason="end_turn",
        )

        loop = AgenticLoop(
            system_prompt="You are helpful.",
            tools=sample_tools,
            llm=mock_llm,
        )

        result = await loop.run("Hi there")

        assert result.success
        assert result.final_response == "Hello! How can I help?"
        assert result.turns_used == 1
        assert result.stop_reason == "complete"

    @pytest.mark.asyncio
    async def test_empty_response(self, mock_llm):
        """Loop handles empty LLM response gracefully."""
        mock_llm.chat.return_value = LLMResponse(
            content="",
            tool_calls=[],
            usage=TokenUsage(input_tokens=50, output_tokens=0),
            stop_reason="end_turn",
        )

        loop = AgenticLoop(system_prompt="Test", llm=mock_llm)
        result = await loop.run("Hi")

        assert result.success
        assert result.final_response == ""
        assert result.stop_reason == "complete"

    @pytest.mark.asyncio
    async def test_messages_include_system_prompt(self, mock_llm):
        """System prompt is included in messages sent to LLM."""
        mock_llm.chat.return_value = LLMResponse(
            content="Done",
            tool_calls=[],
            usage=TokenUsage(),
        )

        loop = AgenticLoop(system_prompt="Be helpful.", llm=mock_llm)
        await loop.run("Hello")

        call_args = mock_llm.chat.call_args
        messages = call_args.kwargs["messages"]
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "Be helpful."
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Hello"


class TestAgenticLoopWithTools:
    """Test loop execution with tool calls."""

    @pytest.mark.asyncio
    async def test_single_tool_call(self, mock_llm, sample_tools):
        """Loop executes a tool call and returns the final response."""
        # First call: LLM requests tool
        tool_response = LLMResponse(
            content="",
            tool_calls=[{
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "echo",
                    "arguments": json.dumps({"message": "hello"}),
                },
            }],
            usage=TokenUsage(input_tokens=100, output_tokens=30),
        )
        # Second call: LLM produces final response
        final_response = LLMResponse(
            content="The echo said: hello",
            tool_calls=[],
            usage=TokenUsage(input_tokens=150, output_tokens=20),
        )
        mock_llm.chat.side_effect = [tool_response, final_response]

        loop = AgenticLoop(
            system_prompt="Use tools.",
            tools=sample_tools,
            llm=mock_llm,
        )

        result = await loop.run("Echo hello")

        assert result.success
        assert result.final_response == "The echo said: hello"
        assert result.turns_used == 2
        assert "echo" in result.tools_called

    @pytest.mark.asyncio
    async def test_multiple_tool_calls_in_one_turn(self, mock_llm, sample_tools):
        """Loop handles multiple tool calls in a single LLM response."""
        tool_response = LLMResponse(
            content="",
            tool_calls=[
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "echo", "arguments": json.dumps({"message": "a"})},
                },
                {
                    "id": "call_2",
                    "type": "function",
                    "function": {"name": "add", "arguments": json.dumps({"a": 2, "b": 3})},
                },
            ],
            usage=TokenUsage(input_tokens=100, output_tokens=50),
        )
        final_response = LLMResponse(
            content="Echo a, and 2+3=5",
            tool_calls=[],
            usage=TokenUsage(input_tokens=200, output_tokens=20),
        )
        mock_llm.chat.side_effect = [tool_response, final_response]

        loop = AgenticLoop(
            system_prompt="Use tools.",
            tools=sample_tools,
            llm=mock_llm,
        )

        result = await loop.run("Do both")

        assert result.success
        assert result.turns_used == 2
        assert len(result.context.tool_executions) == 2

    @pytest.mark.asyncio
    async def test_tool_failure_handling(self, mock_llm, sample_tools):
        """Loop handles tool execution failures gracefully."""
        tool_response = LLMResponse(
            content="",
            tool_calls=[{
                "id": "call_1",
                "type": "function",
                "function": {"name": "failing", "arguments": json.dumps({"input": "test"})},
            }],
            usage=TokenUsage(),
        )
        final_response = LLMResponse(
            content="Sorry, the tool failed.",
            tool_calls=[],
            usage=TokenUsage(),
        )
        mock_llm.chat.side_effect = [tool_response, final_response]

        config = AgenticConfig(max_retries_per_tool=0)
        loop = AgenticLoop(
            system_prompt="Use tools.",
            tools=sample_tools,
            config=config,
            llm=mock_llm,
        )

        result = await loop.run("Run the failing tool")

        assert result.success  # Loop itself succeeds
        assert len(result.context.tool_executions) == 1
        assert not result.context.tool_executions[0].success

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self, mock_llm, sample_tools):
        """Loop handles calls to unknown tools."""
        tool_response = LLMResponse(
            content="",
            tool_calls=[{
                "id": "call_1",
                "type": "function",
                "function": {"name": "nonexistent", "arguments": "{}"},
            }],
            usage=TokenUsage(),
        )
        final_response = LLMResponse(
            content="That tool doesn't exist.",
            tool_calls=[],
            usage=TokenUsage(),
        )
        mock_llm.chat.side_effect = [tool_response, final_response]

        loop = AgenticLoop(
            system_prompt="Test",
            tools=sample_tools,
            llm=mock_llm,
        )

        result = await loop.run("Call nonexistent")
        assert result.success


class TestAgenticLoopLimits:
    """Test execution limits (turns, timeout, cost)."""

    @pytest.mark.asyncio
    async def test_max_turns_limit(self, mock_llm, sample_tools):
        """Loop stops when max turns is reached."""
        # Always return tool calls, never a final response
        tool_response = LLMResponse(
            content="thinking...",
            tool_calls=[{
                "id": "call_1",
                "type": "function",
                "function": {"name": "echo", "arguments": json.dumps({"message": "loop"})},
            }],
            usage=TokenUsage(),
        )
        mock_llm.chat.return_value = tool_response

        config = AgenticConfig(max_turns=3)
        loop = AgenticLoop(
            system_prompt="Test",
            tools=sample_tools,
            config=config,
            llm=mock_llm,
        )

        result = await loop.run("Keep looping")

        assert result.stop_reason == "max_turns"
        assert result.turns_used == 3

    @pytest.mark.asyncio
    async def test_llm_error_stops_loop(self, mock_llm):
        """Loop stops gracefully on LLM errors."""
        mock_llm.chat.side_effect = RuntimeError("API Error")

        loop = AgenticLoop(system_prompt="Test", llm=mock_llm)
        result = await loop.run("Hello")

        assert not result.success
        assert result.stop_reason == "error"
        assert "API Error" in result.final_response


class TestAgenticLoopStreaming:
    """Test streaming execution."""

    @pytest.mark.asyncio
    async def test_streaming_simple_response(self, mock_llm, sample_tools):
        """Streaming yields text chunks and done event."""
        from core.llm_router import StreamChunk

        async def mock_stream(*args, **kwargs):
            yield StreamChunk(type="text", content="Hello ")
            yield StreamChunk(type="text", content="world!")
            yield StreamChunk(type="usage", usage=TokenUsage(input_tokens=50, output_tokens=10, model="test"))
            yield StreamChunk(type="done")

        mock_llm.chat_stream = mock_stream

        loop = AgenticLoop(
            system_prompt="Test",
            tools=sample_tools,
            llm=mock_llm,
        )

        events = []
        async for event in loop.run_streaming("Hi"):
            events.append(event)

        text_events = [e for e in events if e["type"] == "text"]
        assert len(text_events) == 2
        assert text_events[0]["content"] == "Hello "
        assert text_events[1]["content"] == "world!"

        done_events = [e for e in events if e["type"] == "done"]
        assert len(done_events) == 1
        assert done_events[0]["result"]["success"]

    @pytest.mark.asyncio
    async def test_streaming_with_tool_calls(self, mock_llm, sample_tools):
        """Streaming yields tool events when tools are called."""
        from core.llm_router import StreamChunk

        call_count = 0

        async def mock_stream(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                # First call: tool call
                yield StreamChunk(type="tool_call_start", tool_call_id="c1", tool_name="echo")
                yield StreamChunk(type="tool_call_delta", tool_call_id="c1", tool_name="echo", tool_arguments='{"message":')
                yield StreamChunk(type="tool_call_delta", tool_call_id="c1", tool_name="echo", tool_arguments='"hi"}')
                yield StreamChunk(type="tool_call_end", tool_call_id="c1", tool_name="echo")
                yield StreamChunk(type="usage", usage=TokenUsage(input_tokens=50, output_tokens=20, model="test"))
                yield StreamChunk(type="done")
            else:
                # Second call: final text
                yield StreamChunk(type="text", content="Done!")
                yield StreamChunk(type="usage", usage=TokenUsage(input_tokens=80, output_tokens=5, model="test"))
                yield StreamChunk(type="done")

        mock_llm.chat_stream = mock_stream

        loop = AgenticLoop(
            system_prompt="Test",
            tools=sample_tools,
            llm=mock_llm,
        )

        events = []
        async for event in loop.run_streaming("Echo hi"):
            events.append(event)

        tool_start_events = [e for e in events if e["type"] == "tool_start"]
        assert len(tool_start_events) == 1
        assert tool_start_events[0]["name"] == "echo"

        tool_result_events = [e for e in events if e["type"] == "tool_result"]
        assert len(tool_result_events) == 1
        assert "Echo: hi" in tool_result_events[0]["content"]


class TestAgenticLoopHooks:
    """Test hook callbacks."""

    @pytest.mark.asyncio
    async def test_on_tool_start_hook(self, mock_llm, sample_tools):
        """on_tool_start hook is called before tool execution."""
        hook_calls = []

        async def on_start(name, args):
            hook_calls.append(("start", name, args))

        tool_response = LLMResponse(
            content="",
            tool_calls=[{
                "id": "c1",
                "type": "function",
                "function": {"name": "echo", "arguments": json.dumps({"message": "test"})},
            }],
            usage=TokenUsage(),
        )
        final_response = LLMResponse(content="Done", tool_calls=[], usage=TokenUsage())
        mock_llm.chat.side_effect = [tool_response, final_response]

        config = AgenticConfig(on_tool_start=on_start)
        loop = AgenticLoop(
            system_prompt="Test",
            tools=sample_tools,
            config=config,
            llm=mock_llm,
        )

        await loop.run("Echo test")

        assert len(hook_calls) == 1
        assert hook_calls[0][1] == "echo"

    @pytest.mark.asyncio
    async def test_on_turn_end_hook(self, mock_llm):
        """on_turn_end hook is called after each turn."""
        hook_calls = []

        async def on_turn(turn_num, response):
            hook_calls.append(turn_num)

        mock_llm.chat.return_value = LLMResponse(
            content="Done",
            tool_calls=[],
            usage=TokenUsage(),
        )

        config = AgenticConfig(on_turn_end=on_turn)
        loop = AgenticLoop(system_prompt="Test", config=config, llm=mock_llm)

        await loop.run("Hi")

        assert hook_calls == [1]
