"""Context compaction to manage long conversations within model limits.

When the message history exceeds a configurable threshold of the model's
context window, older messages are summarized using a fast model while
preserving critical context (system prompt, recent user messages, recent tool results).
"""

from __future__ import annotations

from typing import Any

from core.logging import get_logger

logger = get_logger(__name__)

# Approximate tokens per character (conservative estimate)
CHARS_PER_TOKEN = 3.5


def estimate_tokens(messages: list[dict[str, Any]]) -> int:
    """Estimate token count for a list of messages.

    Uses a character-based heuristic. For production accuracy,
    consider using tiktoken or provider-specific tokenizers.
    """
    total_chars = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total_chars += len(content)
        elif isinstance(content, list):
            # Handle structured content blocks
            for block in content:
                if isinstance(block, dict):
                    total_chars += len(str(block.get("text", block.get("content", ""))))
                else:
                    total_chars += len(str(block))

        # Account for tool calls in assistant messages
        tool_calls = msg.get("tool_calls", [])
        for tc in tool_calls:
            fn = tc.get("function", {})
            total_chars += len(fn.get("name", ""))
            total_chars += len(fn.get("arguments", ""))

    return int(total_chars / CHARS_PER_TOKEN)


class ContextCompactor:
    """Manages context window usage by compacting old messages.

    Strategy:
    1. Never remove: system prompt, last user message, last 3 tool results
    2. When threshold exceeded: summarize old messages with fast model
    3. Preserve: key decisions, tool outcomes, and user preferences
    """

    def __init__(
        self,
        threshold: float = 0.8,
        model_context_limit: int = 200_000,
        preserve_recent_tools: int = 3,
        target_after_compaction: float = 0.4,
    ):
        """Initialize the compactor.

        Args:
            threshold: Fraction of context limit that triggers compaction
            model_context_limit: Max tokens for the model
            preserve_recent_tools: Number of recent tool results to preserve
            target_after_compaction: Target context usage after compaction
        """
        self.threshold = threshold
        self.model_context_limit = model_context_limit
        self.preserve_recent_tools = preserve_recent_tools
        self.target_after_compaction = target_after_compaction

    async def should_compact(self, messages: list[dict[str, Any]]) -> bool:
        """Check if compaction is needed based on estimated token count."""
        token_count = estimate_tokens(messages)
        max_tokens = int(self.model_context_limit * self.threshold)
        should = token_count > max_tokens
        if should:
            logger.info(
                "compaction_needed",
                estimated_tokens=token_count,
                threshold_tokens=max_tokens,
            )
        return should

    async def compact(
        self,
        messages: list[dict[str, Any]],
        llm_router: Any,
    ) -> list[dict[str, Any]]:
        """Compact messages by summarizing older ones.

        Separates messages into protected (must keep) and compactable (can summarize).
        Uses the fast model tier to generate a summary.

        Args:
            messages: Full message history
            llm_router: LLMRouter instance for generating summary

        Returns:
            Compacted message list
        """
        if len(messages) < 5:
            return messages  # Too few to compact

        # Separate protected messages
        protected_head, compactable, protected_tail = self._split_messages(messages)

        if not compactable:
            return messages  # Nothing to compact

        # Generate summary of compactable messages
        summary = await self._summarize(compactable, llm_router)

        # Build compacted message list
        result: list[dict[str, Any]] = list(protected_head)
        result.append({
            "role": "user",
            "content": f"[Resumo do contexto anterior]\n{summary}",
        })
        result.extend(protected_tail)

        logger.info(
            "context_compacted",
            original_messages=len(messages),
            compacted_messages=len(result),
            original_tokens=estimate_tokens(messages),
            compacted_tokens=estimate_tokens(result),
        )

        return result

    def _split_messages(
        self, messages: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        """Split messages into protected head, compactable middle, and protected tail.

        Protected head: system messages
        Protected tail: last user message + last N tool results + their tool_calls
        Compactable: everything in between
        """
        # Protected head: all system messages at the start
        protected_head: list[dict[str, Any]] = []
        start_idx = 0
        for i, msg in enumerate(messages):
            if msg["role"] == "system":
                protected_head.append(msg)
                start_idx = i + 1
            else:
                break

        # Protected tail: work backwards from end
        protected_tail_indices: set[int] = set()
        tool_results_found = 0
        found_last_user = False

        for i in range(len(messages) - 1, start_idx - 1, -1):
            msg = messages[i]

            # Always keep the last user message
            if msg["role"] == "user" and not found_last_user:
                protected_tail_indices.add(i)
                found_last_user = True
                continue

            # Keep recent tool results
            if msg["role"] == "tool" and tool_results_found < self.preserve_recent_tools:
                protected_tail_indices.add(i)
                tool_results_found += 1
                # Also keep the assistant message that triggered this tool call
                if i > 0 and messages[i - 1]["role"] == "assistant":
                    protected_tail_indices.add(i - 1)
                continue

            # Keep assistant messages after the last user message
            if found_last_user and msg["role"] == "assistant" and not msg.get("tool_calls"):
                protected_tail_indices.add(i)
                continue

            # Stop once we have enough protected messages
            if found_last_user and tool_results_found >= self.preserve_recent_tools:
                break

        # Split
        tail_start = min(protected_tail_indices) if protected_tail_indices else len(messages)
        compactable = messages[start_idx:tail_start]
        protected_tail = messages[tail_start:]

        return protected_head, compactable, protected_tail

    async def _summarize(
        self,
        messages: list[dict[str, Any]],
        llm_router: Any,
    ) -> str:
        """Generate a concise summary of messages using the fast model."""
        # Build a text representation of messages to summarize
        conversation_text = []
        for msg in messages:
            role = msg["role"]
            content = msg.get("content", "")

            if role == "tool":
                # Truncate long tool results
                if len(content) > 500:
                    content = content[:500] + "...(truncated)"
                conversation_text.append(f"[Tool Result]: {content}")
            elif role == "assistant":
                if msg.get("tool_calls"):
                    tools_used = [tc["function"]["name"] for tc in msg["tool_calls"]]
                    conversation_text.append(f"[Assistant called tools: {', '.join(tools_used)}]")
                if content:
                    conversation_text.append(f"[Assistant]: {content[:300]}")
            elif role == "user":
                conversation_text.append(f"[User]: {content[:200]}")

        full_text = "\n".join(conversation_text)

        # Use fast tier to summarize
        summary_prompt = [
            {"role": "system", "content": (
                "You are a context summarizer. Summarize the following conversation "
                "preserving: key facts, decisions made, tool results that matter, "
                "and user preferences. Be concise but complete. Output in the same "
                "language as the conversation (Portuguese if applicable)."
            )},
            {"role": "user", "content": f"Summarize this conversation:\n\n{full_text}"},
        ]

        try:
            response = await llm_router.chat(
                messages=summary_prompt,
                tier="fast",
                temperature=0.3,
                max_tokens=1000,
            )
            return response.content
        except Exception as e:
            logger.error("compaction_summary_failed", error=str(e))
            # Fallback: just take the last few messages' content
            return "\n".join(conversation_text[-5:])
