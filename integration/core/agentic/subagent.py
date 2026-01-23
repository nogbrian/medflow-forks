"""Subagent spawning with isolated context.

Allows a parent agent to delegate subtasks to child agents that run
in their own context without polluting the parent's message history.
"""

from __future__ import annotations

import uuid
from typing import Any

from core.agentic.config import AgenticConfig
from core.agentic.context import AgenticContext, AgenticResult
from core.agentic.loop import AgenticLoop
from core.llm_router import CostTracker, LLMRouter
from core.logging import get_logger

logger = get_logger(__name__)


class SubagentSpawner:
    """Spawns isolated subagent instances for task delegation.

    Subagents have their own context and message history but share
    the parent's cost tracker for unified billing.
    """

    def __init__(
        self,
        parent_loop: AgenticLoop,
        available_tools: dict[str, Any] | None = None,
    ):
        """Initialize the spawner.

        Args:
            parent_loop: The parent agentic loop that owns this spawner
            available_tools: Tools available to subagents (defaults to parent's tools)
        """
        self.parent_loop = parent_loop
        self.available_tools = available_tools or parent_loop.tools
        self._cost_tracker = parent_loop.llm.cost_tracker

    async def spawn(
        self,
        task: str,
        system_prompt: str,
        tools: list[str] | None = None,
        config: AgenticConfig | None = None,
        timeout: int = 120,
    ) -> AgenticResult:
        """Spawn a subagent with isolated context.

        Args:
            task: The task description / user message for the subagent
            system_prompt: System prompt defining the subagent's behavior
            tools: Subset of tool names to make available (None = all)
            config: Custom config for the subagent (defaults to reasonable limits)
            timeout: Timeout in seconds for the subagent execution

        Returns:
            AgenticResult from the subagent's execution
        """
        # Build tool subset
        subagent_tools = self._filter_tools(tools)

        # Create config with safety limits
        if config is None:
            config = AgenticConfig(
                max_turns=10,
                timeout_seconds=timeout,
                max_cost_usd=0.5,
                tier="smart",
                enable_compaction=False,  # Short-lived, shouldn't need compaction
            )
        else:
            config.timeout_seconds = min(config.timeout_seconds, timeout)

        # Create isolated context
        context = AgenticContext(
            session_id=str(uuid.uuid4()),
            agent_name=f"subagent-{self.parent_loop.context.agent_name}",
            parent_session_id=self.parent_loop.context.session_id,
            cost_tracker=self._cost_tracker,  # Shared cost tracking
        )

        # Create isolated LLM router sharing cost tracker
        llm = LLMRouter(cost_tracker=self._cost_tracker)

        # Create and run the subagent loop
        subagent = AgenticLoop(
            system_prompt=system_prompt,
            tools=subagent_tools,
            config=config,
            llm=llm,
            context=context,
        )

        logger.info(
            "subagent_spawned",
            parent_session=self.parent_loop.context.session_id,
            subagent_session=context.session_id,
            task=task[:100],
            tools=list(subagent_tools.keys()),
        )

        result = await subagent.run(task)

        logger.info(
            "subagent_completed",
            subagent_session=context.session_id,
            success=result.success,
            turns=result.turns_used,
            cost_usd=round(result.total_cost_usd, 6),
        )

        return result

    def _filter_tools(self, names: list[str] | None) -> dict[str, Any]:
        """Filter available tools by name list."""
        if names is None:
            return dict(self.available_tools)

        filtered = {}
        for name in names:
            if name in self.available_tools:
                filtered[name] = self.available_tools[name]
            else:
                logger.warning("subagent_tool_not_found", tool=name)
        return filtered


def create_delegate_tool(spawner: SubagentSpawner) -> dict[str, Any]:
    """Create a 'delegate_task' tool that agents can use to spawn subagents.

    This allows agents to delegate work to specialized subagents via
    the standard tool-calling interface.

    Returns:
        Tool definition dict compatible with AgenticLoop.tools format
    """

    async def delegate_task(
        task: str,
        agent_type: str = "general",
        tools: str = "",
    ) -> str:
        """Delegate a subtask to a specialized subagent.

        Args:
            task: Description of the task to delegate
            agent_type: Type of agent ("research", "content", "crm", "calendar")
            tools: Comma-separated list of tool names to allow (empty = all)

        Returns:
            The subagent's final response
        """
        # Map agent_type to system prompt
        system_prompts = {
            "general": "You are a helpful assistant. Complete the given task thoroughly.",
            "research": (
                "You are a research specialist. Gather information, analyze data, "
                "and provide comprehensive findings. Be factual and cite sources."
            ),
            "content": (
                "You are a content creation specialist for medical marketing in Brazil. "
                "Create engaging, CFM-compliant content. Write in Brazilian Portuguese."
            ),
            "crm": (
                "You are a CRM specialist. Manage leads, update records, and ensure "
                "data consistency across the pipeline."
            ),
            "calendar": (
                "You are a scheduling specialist. Check availability, create bookings, "
                "and handle rescheduling with proper confirmation."
            ),
        }

        system_prompt = system_prompts.get(agent_type, system_prompts["general"])
        tool_list = [t.strip() for t in tools.split(",") if t.strip()] or None

        result = await spawner.spawn(
            task=task,
            system_prompt=system_prompt,
            tools=tool_list,
        )

        if result.success:
            return result.final_response
        else:
            return f"Subagent failed ({result.stop_reason}): {result.final_response}"

    return {
        "definition": {
            "name": "delegate_task",
            "description": (
                "Delegate a subtask to a specialized subagent. Use this when a task "
                "requires focused work that shouldn't clutter the main conversation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "Description of the task to delegate",
                    },
                    "agent_type": {
                        "type": "string",
                        "enum": ["general", "research", "content", "crm", "calendar"],
                        "description": "Type of specialist agent to use",
                    },
                    "tools": {
                        "type": "string",
                        "description": "Comma-separated tool names to allow (empty = all)",
                    },
                },
                "required": ["task"],
            },
        },
        "handler": delegate_task,
        "category": "orchestration",
        "idempotent": False,
    }
