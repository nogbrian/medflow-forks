"""Agentic Loop - the core execution engine for autonomous agents.

Implements the LLM → tool_calls → execute → repeat pattern with:
- Multi-provider streaming via LLMRouter
- Configurable limits (turns, cost, timeout)
- Tool execution with retry and error handling
- Context compaction for long conversations
- Hooks for observability
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from collections.abc import AsyncIterator
from typing import Any

from core.agentic.config import AgenticConfig
from core.agentic.context import AgenticContext, AgenticResult, ToolExecution
from core.llm_router import LLMResponse, LLMRouter, StreamChunk
from core.logging import get_logger

logger = get_logger(__name__)


class AgenticLoop:
    """Autonomous agent execution loop.

    Runs the pattern: LLM call → parse tool_calls → execute tools → repeat
    until the LLM produces a final response without tool calls, or a limit is hit.
    """

    def __init__(
        self,
        system_prompt: str,
        tools: dict[str, Any] | None = None,
        config: AgenticConfig | None = None,
        llm: LLMRouter | None = None,
        context: AgenticContext | None = None,
    ):
        """Initialize the agentic loop.

        Args:
            system_prompt: System message defining agent behavior
            tools: Dict mapping tool names to their definitions and handlers.
                   Format: {name: {"definition": {...}, "handler": async_callable}}
            config: Execution configuration (limits, model, etc.)
            llm: LLM router instance (created if not provided)
            context: Existing context to resume (created if not provided)
        """
        self.system_prompt = system_prompt
        self.tools = tools or {}
        self.config = config or AgenticConfig()
        self.llm = llm or LLMRouter()
        self.context = context or AgenticContext(
            session_id=str(uuid.uuid4()),
            cost_tracker=self.llm.cost_tracker,
        )
        self._compactor: Any | None = None

    def _get_tool_definitions(self) -> list[dict[str, Any]] | None:
        """Get OpenAI-format tool definitions for the LLM."""
        if not self.tools:
            return None

        definitions = []
        for name, tool_info in self.tools.items():
            # Filter by allowed_tools if configured
            if self.config.allowed_tools and name not in self.config.allowed_tools:
                continue
            defn = tool_info.get("definition", {})
            definitions.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": defn.get("description", ""),
                    "parameters": defn.get("parameters", {"type": "object", "properties": {}}),
                },
            })
        return definitions or None

    def _build_messages(self) -> list[dict[str, Any]]:
        """Build the full message list including system prompt."""
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt},
        ]
        messages.extend(self.context.messages)
        return messages

    async def _execute_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """Execute a tool and return the result as a string.

        Handles retries and error reporting.
        """
        tool_info = self.tools.get(name)
        if not tool_info:
            return json.dumps({"error": f"Tool '{name}' not found"})

        handler = tool_info.get("handler")
        if not handler:
            return json.dumps({"error": f"Tool '{name}' has no handler"})

        start = time.monotonic()
        retries = 0
        last_error = ""

        while retries <= self.config.max_retries_per_tool:
            try:
                if self.config.on_tool_start:
                    await self.config.on_tool_start(name, arguments)

                result = await handler(**arguments)

                duration_ms = (time.monotonic() - start) * 1000
                execution = ToolExecution(
                    name=name,
                    arguments=arguments,
                    result=str(result)[:5000],
                    duration_ms=duration_ms,
                    success=True,
                    turn=self.context.turn,
                )
                self.context.add_tool_execution(execution)

                if self.config.on_tool_end:
                    await self.config.on_tool_end(name, result)

                # Ensure result is a string
                if isinstance(result, dict | list):
                    return json.dumps(result, ensure_ascii=False)
                return str(result)

            except Exception as e:
                last_error = str(e)
                retries += 1
                if retries <= self.config.max_retries_per_tool and self.config.retry_on_error:
                    logger.warning(
                        "tool_retry",
                        tool=name,
                        attempt=retries,
                        error=last_error,
                    )
                    await asyncio.sleep(0.5 * retries)
                    continue
                break

        # All retries failed
        duration_ms = (time.monotonic() - start) * 1000
        execution = ToolExecution(
            name=name,
            arguments=arguments,
            result="",
            duration_ms=duration_ms,
            success=False,
            error=last_error,
            turn=self.context.turn,
        )
        self.context.add_tool_execution(execution)
        logger.error("tool_failed", tool=name, error=last_error)
        return json.dumps({"error": f"Tool '{name}' failed: {last_error}"})

    def _check_limits(self) -> str | None:
        """Check if any limits have been exceeded. Returns stop_reason or None."""
        if self.context.turn >= self.config.max_turns:
            return "max_turns"
        if self.context.elapsed_seconds >= self.config.timeout_seconds:
            return "timeout"
        if self.config.max_cost_usd > 0 and self.context.total_cost_usd >= self.config.max_cost_usd:
            return "cost_limit"
        return None

    async def _maybe_compact(self) -> None:
        """Run context compaction if needed."""
        if not self.config.enable_compaction:
            return

        # Lazy import to avoid circular deps
        if self._compactor is None:
            try:
                from core.agentic.compaction import ContextCompactor
                model = self.llm.get_model(self.config.tier)
                self._compactor = ContextCompactor(
                    threshold=self.config.compaction_threshold,
                    model_context_limit=self.llm.get_context_limit(model),
                )
            except ImportError:
                self.config.enable_compaction = False
                return

        if await self._compactor.should_compact(self.context.messages):
            self.context.messages = await self._compactor.compact(
                self.context.messages, self.llm
            )
            logger.info("context_compacted", turn=self.context.turn)

    async def run(self, user_message: str) -> AgenticResult:
        """Run the agentic loop to completion.

        Args:
            user_message: The user's input message

        Returns:
            AgenticResult with the final response and execution metadata
        """
        self.context.add_message("user", user_message)
        tool_definitions = self._get_tool_definitions()

        while True:
            # Check limits before each turn
            stop_reason = self._check_limits()
            if stop_reason:
                self.context.finish(stop_reason)
                return AgenticResult(
                    final_response=self._get_last_assistant_content(),
                    success=stop_reason == "max_turns",
                    context=self.context,
                )

            self.context.turn += 1

            # Compact context if needed
            await self._maybe_compact()

            # Call LLM
            messages = self._build_messages()
            try:
                response: LLMResponse = await self.llm.chat(
                    messages=messages,
                    tier=self.config.tier,
                    tools=tool_definitions,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                )
            except Exception as e:
                logger.error("llm_call_failed", error=str(e), turn=self.context.turn)
                self.context.finish("error")
                return AgenticResult(
                    final_response=f"Error calling LLM: {e}",
                    success=False,
                    context=self.context,
                )

            # Process response
            if response.tool_calls:
                # Add assistant message with tool calls
                self.context.messages.append({
                    "role": "assistant",
                    "content": response.content or "",
                    "tool_calls": response.tool_calls,
                })

                # Execute each tool call
                for tool_call in response.tool_calls:
                    fn = tool_call["function"]
                    tool_name = fn["name"]
                    try:
                        args = json.loads(fn["arguments"]) if isinstance(fn["arguments"], str) else fn["arguments"]
                    except json.JSONDecodeError:
                        args = {}

                    result = await self._execute_tool(tool_name, args)

                    # Add tool result message
                    self.context.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": result,
                    })

                # Notify hook
                if self.config.on_turn_end:
                    await self.config.on_turn_end(self.context.turn, response)

                # Continue loop
                continue

            else:
                # No tool calls - this is the final response
                if response.content:
                    self.context.add_message("assistant", response.content)

                if self.config.on_turn_end:
                    await self.config.on_turn_end(self.context.turn, response)

                self.context.finish("complete")
                return AgenticResult(
                    final_response=response.content,
                    success=True,
                    context=self.context,
                )

    async def run_streaming(self, user_message: str) -> AsyncIterator[dict[str, Any]]:
        """Run the agentic loop with streaming output.

        Yields SSE-compatible event dicts:
        - {"type": "text", "content": "..."}
        - {"type": "tool_start", "name": "...", "id": "..."}
        - {"type": "tool_result", "name": "...", "content": "..."}
        - {"type": "turn", "number": N}
        - {"type": "usage", "costs": {...}}
        - {"type": "done", "result": {...}}
        - {"type": "error", "message": "..."}
        """
        self.context.add_message("user", user_message)
        tool_definitions = self._get_tool_definitions()

        while True:
            # Check limits
            stop_reason = self._check_limits()
            if stop_reason:
                self.context.finish(stop_reason)
                yield {
                    "type": "done",
                    "result": AgenticResult(
                        final_response=self._get_last_assistant_content(),
                        success=stop_reason == "max_turns",
                        context=self.context,
                    ).to_dict(),
                }
                return

            self.context.turn += 1
            yield {"type": "turn", "number": self.context.turn}

            # Compact if needed
            await self._maybe_compact()

            # Stream LLM response
            messages = self._build_messages()
            full_content = ""
            tool_calls: list[dict[str, Any]] = []
            current_tool_args: dict[str, str] = {}  # tool_call_id → accumulated args

            try:
                async for chunk in self.llm.chat_stream(
                    messages=messages,
                    tier=self.config.tier,
                    tools=tool_definitions,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                ):
                    if chunk.type == "text":
                        full_content += chunk.content
                        yield {"type": "text", "content": chunk.content}

                    elif chunk.type == "tool_call_start":
                        yield {
                            "type": "tool_start",
                            "name": chunk.tool_name,
                            "id": chunk.tool_call_id,
                        }
                        current_tool_args[chunk.tool_call_id] = ""

                    elif chunk.type == "tool_call_delta":
                        if chunk.tool_call_id in current_tool_args:
                            current_tool_args[chunk.tool_call_id] += chunk.tool_arguments

                    elif chunk.type == "tool_call_end":
                        args_str = current_tool_args.get(chunk.tool_call_id, "{}")
                        tool_calls.append({
                            "id": chunk.tool_call_id,
                            "type": "function",
                            "function": {
                                "name": chunk.tool_name,
                                "arguments": args_str,
                            },
                        })

                    elif chunk.type == "usage" and chunk.usage:
                        yield {
                            "type": "usage",
                            "costs": self.context.cost_tracker.to_dict(),
                        }

                    elif chunk.type == "done":
                        pass  # Handled below

            except Exception as e:
                logger.error("llm_stream_failed", error=str(e))
                self.context.finish("error")
                yield {"type": "error", "message": str(e)}
                return

            # Process tool calls
            if tool_calls:
                self.context.messages.append({
                    "role": "assistant",
                    "content": full_content or "",
                    "tool_calls": tool_calls,
                })

                for tool_call in tool_calls:
                    fn = tool_call["function"]
                    tool_name = fn["name"]
                    try:
                        args = json.loads(fn["arguments"]) if isinstance(fn["arguments"], str) else fn["arguments"]
                    except json.JSONDecodeError:
                        args = {}

                    result = await self._execute_tool(tool_name, args)

                    self.context.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": result,
                    })

                    yield {
                        "type": "tool_result",
                        "name": tool_name,
                        "id": tool_call["id"],
                        "content": result[:2000],
                    }

                # Continue the loop
                continue

            else:
                # Final response
                if full_content:
                    self.context.add_message("assistant", full_content)

                self.context.finish("complete")
                yield {
                    "type": "done",
                    "result": AgenticResult(
                        final_response=full_content,
                        success=True,
                        context=self.context,
                    ).to_dict(),
                }
                return

    def _get_last_assistant_content(self) -> str:
        """Get the content of the last assistant message."""
        for msg in reversed(self.context.messages):
            if msg["role"] == "assistant" and msg.get("content"):
                return msg["content"]
        return ""
