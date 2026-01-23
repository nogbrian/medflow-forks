"""Unit tests for context compaction."""

import pytest
from unittest.mock import AsyncMock

from core.agentic.compaction import ContextCompactor, estimate_tokens
from core.llm_router import LLMResponse, TokenUsage


class TestEstimateTokens:
    """Test token estimation."""

    def test_simple_messages(self):
        messages = [
            {"role": "user", "content": "Hello world"},  # 11 chars
            {"role": "assistant", "content": "Hi there!"},  # 9 chars
        ]
        tokens = estimate_tokens(messages)
        # ~20 chars / 3.5 = ~5-6 tokens
        assert 3 < tokens < 10

    def test_empty_messages(self):
        assert estimate_tokens([]) == 0

    def test_tool_calls_counted(self):
        messages = [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [{
                    "function": {
                        "name": "search",
                        "arguments": '{"query": "test query here"}',
                    },
                }],
            }
        ]
        tokens = estimate_tokens(messages)
        assert tokens > 0

    def test_large_message_estimate(self):
        # 100K characters ~ 28K tokens
        messages = [{"role": "user", "content": "x" * 100_000}]
        tokens = estimate_tokens(messages)
        assert 25_000 < tokens < 35_000


class TestShouldCompact:
    """Test compaction threshold detection."""

    @pytest.mark.asyncio
    async def test_under_threshold(self):
        compactor = ContextCompactor(
            threshold=0.8,
            model_context_limit=200_000,
        )
        # Small messages - well under threshold
        messages = [
            {"role": "system", "content": "Be helpful."},
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
        ]
        assert not await compactor.should_compact(messages)

    @pytest.mark.asyncio
    async def test_over_threshold(self):
        compactor = ContextCompactor(
            threshold=0.8,
            model_context_limit=1000,  # Very small limit for testing
        )
        # Large messages - over 80% of 1000 tokens
        messages = [
            {"role": "user", "content": "x" * 5000},  # ~1400 tokens > 800
        ]
        assert await compactor.should_compact(messages)


class TestCompaction:
    """Test the compaction process."""

    @pytest.fixture
    def mock_router(self):
        router = AsyncMock()
        router.chat.return_value = LLMResponse(
            content="Resumo: O usuário pediu informações sobre agendamento.",
            tool_calls=[],
            usage=TokenUsage(input_tokens=200, output_tokens=20),
        )
        return router

    @pytest.mark.asyncio
    async def test_too_few_messages_skipped(self, mock_router):
        compactor = ContextCompactor(model_context_limit=1000)
        messages = [
            {"role": "system", "content": "Prompt"},
            {"role": "user", "content": "Hi"},
        ]
        result = await compactor.compact(messages, mock_router)
        assert result == messages  # No compaction

    @pytest.mark.asyncio
    async def test_preserves_system_prompt(self, mock_router):
        compactor = ContextCompactor(model_context_limit=1000)
        messages = [
            {"role": "system", "content": "System prompt here"},
            {"role": "user", "content": "Message 1"},
            {"role": "assistant", "content": "Response 1"},
            {"role": "user", "content": "Message 2"},
            {"role": "assistant", "content": "Response 2"},
            {"role": "user", "content": "Latest message"},
            {"role": "assistant", "content": "Latest response"},
        ]
        result = await compactor.compact(messages, mock_router)

        # System prompt must be preserved
        assert result[0]["role"] == "system"
        assert result[0]["content"] == "System prompt here"

    @pytest.mark.asyncio
    async def test_preserves_last_user_message(self, mock_router):
        compactor = ContextCompactor(model_context_limit=1000)
        messages = [
            {"role": "system", "content": "Prompt"},
            {"role": "user", "content": "Old message"},
            {"role": "assistant", "content": "Old response"},
            {"role": "user", "content": "Another old"},
            {"role": "assistant", "content": "Another response"},
            {"role": "user", "content": "Latest question"},
            {"role": "assistant", "content": "Latest answer"},
        ]
        result = await compactor.compact(messages, mock_router)

        # Last user message and assistant response should be in result
        user_messages = [m for m in result if m["role"] == "user" and "Resumo" not in m.get("content", "")]
        assert any("Latest question" in m["content"] for m in user_messages)

    @pytest.mark.asyncio
    async def test_preserves_recent_tool_results(self, mock_router):
        compactor = ContextCompactor(
            model_context_limit=1000,
            preserve_recent_tools=2,
        )
        messages = [
            {"role": "system", "content": "Prompt"},
            {"role": "user", "content": "Old"},
            {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "old_tool", "arguments": "{}"}}]},
            {"role": "tool", "tool_call_id": "old", "content": "Old tool result"},
            {"role": "user", "content": "Do something"},
            {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "tool1", "arguments": "{}"}}]},
            {"role": "tool", "tool_call_id": "t1", "content": "Recent result 1"},
            {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "tool2", "arguments": "{}"}}]},
            {"role": "tool", "tool_call_id": "t2", "content": "Recent result 2"},
            {"role": "user", "content": "Latest"},
            {"role": "assistant", "content": "Final answer"},
        ]
        result = await compactor.compact(messages, mock_router)

        # Recent tool results should be preserved
        tool_results = [m for m in result if m["role"] == "tool"]
        assert len(tool_results) >= 2

    @pytest.mark.asyncio
    async def test_summary_inserted(self, mock_router):
        compactor = ContextCompactor(model_context_limit=1000)
        messages = [
            {"role": "system", "content": "Prompt"},
            {"role": "user", "content": "Old question 1"},
            {"role": "assistant", "content": "Old answer 1"},
            {"role": "user", "content": "Old question 2"},
            {"role": "assistant", "content": "Old answer 2"},
            {"role": "user", "content": "Old question 3"},
            {"role": "assistant", "content": "Old answer 3"},
            {"role": "user", "content": "Current question"},
            {"role": "assistant", "content": "Current answer"},
        ]
        result = await compactor.compact(messages, mock_router)

        # Should contain a summary message
        summary_msgs = [m for m in result if "Resumo" in m.get("content", "")]
        assert len(summary_msgs) == 1

    @pytest.mark.asyncio
    async def test_reduces_message_count(self, mock_router):
        compactor = ContextCompactor(
            model_context_limit=1000,
            preserve_recent_tools=0,
        )
        messages = [
            {"role": "system", "content": "Prompt"},
            {"role": "user", "content": "First question"},
            {"role": "assistant", "content": "First answer"},
            {"role": "user", "content": "Second question"},
            {"role": "assistant", "content": "Second answer"},
            {"role": "user", "content": "Third question"},
            {"role": "assistant", "content": "Third answer"},
            {"role": "user", "content": "Fourth question"},
            {"role": "assistant", "content": "Fourth answer"},
            {"role": "user", "content": "Latest question"},  # protected
            {"role": "assistant", "content": "Latest answer"},  # protected
        ]

        result = await compactor.compact(messages, mock_router)
        # Original: 11 messages. After compaction: system + summary + protected tail
        # Should be fewer than 11
        assert len(result) < len(messages)

    @pytest.mark.asyncio
    async def test_summary_failure_fallback(self):
        """Falls back to last few messages if summarization fails."""
        failing_router = AsyncMock()
        failing_router.chat.side_effect = RuntimeError("LLM unavailable")

        compactor = ContextCompactor(model_context_limit=1000)
        messages = [
            {"role": "system", "content": "Prompt"},
            {"role": "user", "content": "Q1"},
            {"role": "assistant", "content": "A1"},
            {"role": "user", "content": "Q2"},
            {"role": "assistant", "content": "A2"},
            {"role": "user", "content": "Q3"},
            {"role": "assistant", "content": "A3"},
        ]
        result = await compactor.compact(messages, failing_router)

        # Should still produce a result (fallback)
        assert len(result) > 0
        assert result[0]["role"] == "system"
