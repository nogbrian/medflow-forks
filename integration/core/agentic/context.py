"""Context tracking for agentic loop sessions."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from core.llm_router import CostTracker, TokenUsage


@dataclass
class ToolExecution:
    """Record of a single tool execution."""

    name: str
    arguments: dict[str, Any]
    result: str
    duration_ms: float = 0.0
    success: bool = True
    error: str = ""
    turn: int = 0


@dataclass
class AgenticContext:
    """Tracks state across an agentic loop session.

    Holds messages, tool history, costs, and execution metadata.
    """

    # Session identity
    session_id: str = ""
    agent_name: str = ""
    parent_session_id: str = ""  # For subagent tracking

    # Message history (OpenAI format)
    messages: list[dict[str, Any]] = field(default_factory=list)

    # Execution state
    turn: int = 0
    started_at: float = field(default_factory=time.time)
    finished_at: float = 0.0

    # Tool tracking
    tool_executions: list[ToolExecution] = field(default_factory=list)

    # Cost tracking
    cost_tracker: CostTracker = field(default_factory=CostTracker)

    # Status
    stop_reason: str = ""  # "complete", "max_turns", "timeout", "cost_limit", "error"

    @property
    def elapsed_seconds(self) -> float:
        """Seconds since session started."""
        end = self.finished_at or time.time()
        return end - self.started_at

    @property
    def total_cost_usd(self) -> float:
        return self.cost_tracker.total_cost_usd

    @property
    def total_tokens(self) -> int:
        return self.cost_tracker.total_input_tokens + self.cost_tracker.total_output_tokens

    def add_message(self, role: str, content: str, **kwargs: Any) -> None:
        """Add a message to the context."""
        msg: dict[str, Any] = {"role": role, "content": content}
        msg.update(kwargs)
        self.messages.append(msg)

    def add_tool_execution(self, execution: ToolExecution) -> None:
        """Record a tool execution."""
        self.tool_executions.append(execution)

    def finish(self, reason: str) -> None:
        """Mark the session as finished."""
        self.stop_reason = reason
        self.finished_at = time.time()

    def to_dict(self) -> dict[str, Any]:
        """Serialize context to dict for logging/storage."""
        return {
            "session_id": self.session_id,
            "agent_name": self.agent_name,
            "turn": self.turn,
            "elapsed_seconds": round(self.elapsed_seconds, 2),
            "stop_reason": self.stop_reason,
            "tool_executions": len(self.tool_executions),
            "costs": self.cost_tracker.to_dict(),
        }


@dataclass
class AgenticResult:
    """Final result from an agentic loop execution."""

    # The final text response from the agent
    final_response: str = ""

    # Whether the execution completed successfully
    success: bool = True

    # Full context for inspection
    context: AgenticContext = field(default_factory=AgenticContext)

    # Extracted structured output (if any)
    structured_output: dict[str, Any] | None = None

    @property
    def stop_reason(self) -> str:
        return self.context.stop_reason

    @property
    def total_cost_usd(self) -> float:
        return self.context.total_cost_usd

    @property
    def turns_used(self) -> int:
        return self.context.turn

    @property
    def tools_called(self) -> list[str]:
        return [t.name for t in self.context.tool_executions]

    def to_dict(self) -> dict[str, Any]:
        return {
            "final_response": self.final_response[:500],
            "success": self.success,
            "stop_reason": self.stop_reason,
            "turns_used": self.turns_used,
            "tools_called": self.tools_called,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "elapsed_seconds": round(self.context.elapsed_seconds, 2),
        }
