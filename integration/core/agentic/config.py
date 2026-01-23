"""Configuration for the agentic loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class AgenticConfig:
    """Configuration for an agentic loop execution.

    Controls behavior limits, model selection, and tool access.
    """

    # Execution limits
    max_turns: int = 25
    timeout_seconds: int = 300
    max_cost_usd: float = 1.0

    # Model configuration
    tier: Literal["fast", "smart", "creative"] = "smart"
    temperature: float = 0.7
    max_tokens: int = 4096

    # Tool configuration
    allowed_tools: list[str] | None = None  # None = all tools
    parallel_tool_calls: bool = True

    # Context management
    enable_compaction: bool = True
    compaction_threshold: float = 0.8  # Compact when context > 80% full

    # Streaming
    stream: bool = False

    # Retry configuration
    max_retries_per_tool: int = 2
    retry_on_error: bool = True

    # Hooks
    on_tool_start: Any | None = None  # async callable(tool_name, args)
    on_tool_end: Any | None = None  # async callable(tool_name, result)
    on_turn_end: Any | None = None  # async callable(turn_number, response)

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)
