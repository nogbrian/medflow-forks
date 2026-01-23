"""Multi-provider LLM router with fallback, cost tracking, and streaming.

Supports Anthropic, OpenAI, Google, and xAI with three tiers:
- fast: Low-latency tasks (routing, classification, summarization)
- smart: Complex reasoning (agent responses, planning)
- creative: Content generation (copy, social media, ads)
"""

from __future__ import annotations

import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Literal

from core.config import get_settings
from core.logging import get_logger

logger = get_logger(__name__)

ModelTier = Literal["fast", "smart", "creative"]

# Cost per 1M tokens (input/output) in USD - approximate
MODEL_COSTS: dict[str, tuple[float, float]] = {
    # Anthropic
    "claude-opus-4-5-20250514": (15.0, 75.0),
    "claude-sonnet-4-5-20250514": (3.0, 15.0),
    "claude-haiku-4-20250514": (0.25, 1.25),
    # OpenAI
    "gpt-5.2": (5.0, 15.0),
    "gpt-5.2-mini": (0.15, 0.6),
    "gpt-4o": (2.5, 10.0),
    "gpt-4o-mini": (0.15, 0.6),
    # Google
    "gemini-2.5-pro": (1.25, 5.0),
    "gemini-2.5-flash": (0.075, 0.3),
    # xAI
    "grok-4.1": (3.0, 15.0),
    "grok-4": (2.0, 10.0),
}

# Context window sizes per model
MODEL_CONTEXT_LIMITS: dict[str, int] = {
    "claude-opus-4-5-20250514": 200_000,
    "claude-sonnet-4-5-20250514": 200_000,
    "claude-haiku-4-20250514": 200_000,
    "gpt-5.2": 128_000,
    "gpt-5.2-mini": 128_000,
    "gpt-4o": 128_000,
    "gpt-4o-mini": 128_000,
    "gemini-2.5-pro": 1_000_000,
    "gemini-2.5-flash": 1_000_000,
    "grok-4.1": 131_072,
    "grok-4": 131_072,
}

# Provider → tier → model mapping
PROVIDER_MODELS: dict[str, dict[ModelTier, str]] = {
    "anthropic": {
        "fast": "claude-haiku-4-20250514",
        "smart": "claude-sonnet-4-5-20250514",
        "creative": "claude-sonnet-4-5-20250514",
    },
    "openai": {
        "fast": "gpt-4o-mini",
        "smart": "gpt-4o",
        "creative": "gpt-4o",
    },
    "google": {
        "fast": "gemini-2.5-flash",
        "smart": "gemini-2.5-pro",
        "creative": "gemini-2.5-pro",
    },
    "xai": {
        "fast": "grok-4",
        "smart": "grok-4.1",
        "creative": "grok-4.1",
    },
}

# Fallback order when primary provider fails
FALLBACK_ORDER: list[str] = ["anthropic", "openai", "google", "xai"]


@dataclass
class TokenUsage:
    """Token usage for a single LLM call."""

    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""
    provider: str = ""
    duration_ms: float = 0.0

    @property
    def cost_usd(self) -> float:
        """Estimated cost in USD."""
        costs = MODEL_COSTS.get(self.model, (1.0, 3.0))
        input_cost = (self.input_tokens / 1_000_000) * costs[0]
        output_cost = (self.output_tokens / 1_000_000) * costs[1]
        return input_cost + output_cost


@dataclass
class CostTracker:
    """Accumulated cost tracking across multiple calls."""

    calls: list[TokenUsage] = field(default_factory=list)

    @property
    def total_input_tokens(self) -> int:
        return sum(c.input_tokens for c in self.calls)

    @property
    def total_output_tokens(self) -> int:
        return sum(c.output_tokens for c in self.calls)

    @property
    def total_cost_usd(self) -> float:
        return sum(c.cost_usd for c in self.calls)

    @property
    def total_calls(self) -> int:
        return len(self.calls)

    def add(self, usage: TokenUsage) -> None:
        self.calls.append(usage)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "total_calls": self.total_calls,
        }


@dataclass
class StreamChunk:
    """A chunk from streaming LLM response."""

    type: Literal["text", "tool_call_start", "tool_call_delta", "tool_call_end", "usage", "done"]
    content: str = ""
    tool_name: str = ""
    tool_call_id: str = ""
    tool_arguments: str = ""
    usage: TokenUsage | None = None


@dataclass
class LLMResponse:
    """Response from an LLM call."""

    content: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    usage: TokenUsage = field(default_factory=TokenUsage)
    stop_reason: str = ""


class LLMRouter:
    """Multi-provider LLM router with fallback and cost tracking."""

    def __init__(
        self,
        provider: str | None = None,
        cost_tracker: CostTracker | None = None,
    ):
        settings = get_settings()
        self.primary_provider = provider or settings.llm_provider
        self.cost_tracker = cost_tracker or CostTracker()
        self._settings = settings
        self._clients: dict[str, Any] = {}

    def get_model(self, tier: ModelTier = "smart") -> str:
        """Get the model ID for a given tier."""
        models = PROVIDER_MODELS.get(self.primary_provider, PROVIDER_MODELS["anthropic"])
        return models[tier]

    def get_context_limit(self, model: str | None = None) -> int:
        """Get context window size for a model."""
        model = model or self.get_model("smart")
        return MODEL_CONTEXT_LIMITS.get(model, 128_000)

    def _get_available_providers(self) -> list[str]:
        """Get providers with configured API keys, in fallback order."""
        key_map = {
            "anthropic": self._settings.anthropic_api_key,
            "openai": self._settings.openai_api_key,
            "google": self._settings.google_api_key,
            "xai": self._settings.xai_api_key,
        }
        # Primary first, then fallback order
        available = []
        if key_map.get(self.primary_provider):
            available.append(self.primary_provider)
        for p in FALLBACK_ORDER:
            if p != self.primary_provider and key_map.get(p):
                available.append(p)
        return available

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tier: ModelTier = "smart",
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Send a chat request with automatic fallback across providers.

        Args:
            messages: Chat messages in OpenAI format [{role, content}]
            tier: Model tier to use
            tools: Tool definitions in OpenAI function format
            temperature: Sampling temperature
            max_tokens: Maximum output tokens

        Returns:
            LLMResponse with content and/or tool calls
        """
        providers = self._get_available_providers()
        if not providers:
            raise RuntimeError("No LLM providers configured. Set at least one API key.")

        last_error: Exception | None = None
        for provider in providers:
            try:
                model = PROVIDER_MODELS[provider][tier]
                start = time.monotonic()
                response = await self._call_provider(
                    provider=provider,
                    model=model,
                    messages=messages,
                    tools=tools,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                response.usage.duration_ms = (time.monotonic() - start) * 1000
                response.usage.provider = provider
                response.usage.model = model
                self.cost_tracker.add(response.usage)
                return response
            except Exception as e:
                last_error = e
                logger.warning(
                    "llm_provider_failed",
                    provider=provider,
                    tier=tier,
                    error=str(e),
                )
                continue

        raise RuntimeError(f"All LLM providers failed. Last error: {last_error}")

    async def chat_stream(
        self,
        messages: list[dict[str, Any]],
        tier: ModelTier = "smart",
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[StreamChunk]:
        """Stream a chat response with automatic fallback.

        Yields StreamChunk objects for text and tool call events.
        """
        providers = self._get_available_providers()
        if not providers:
            raise RuntimeError("No LLM providers configured.")

        last_error: Exception | None = None
        for provider in providers:
            try:
                model = PROVIDER_MODELS[provider][tier]
                start = time.monotonic()
                async for chunk in self._stream_provider(
                    provider=provider,
                    model=model,
                    messages=messages,
                    tools=tools,
                    temperature=temperature,
                    max_tokens=max_tokens,
                ):
                    if chunk.type == "usage" and chunk.usage:
                        chunk.usage.duration_ms = (time.monotonic() - start) * 1000
                        chunk.usage.provider = provider
                        chunk.usage.model = model
                        self.cost_tracker.add(chunk.usage)
                    yield chunk
                return  # Success, don't try fallbacks
            except Exception as e:
                last_error = e
                logger.warning(
                    "llm_stream_provider_failed",
                    provider=provider,
                    error=str(e),
                )
                continue

        raise RuntimeError(f"All LLM providers failed for streaming. Last error: {last_error}")

    async def _call_provider(
        self,
        provider: str,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        """Call a specific provider's API."""
        if provider == "anthropic":
            return await self._call_anthropic(model, messages, tools, temperature, max_tokens)
        elif provider == "openai":
            return await self._call_openai(model, messages, tools, temperature, max_tokens)
        elif provider == "google":
            return await self._call_google(model, messages, tools, temperature, max_tokens)
        elif provider == "xai":
            return await self._call_xai(model, messages, tools, temperature, max_tokens)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def _stream_provider(
        self,
        provider: str,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        temperature: float,
        max_tokens: int,
    ) -> AsyncIterator[StreamChunk]:
        """Stream from a specific provider."""
        if provider == "anthropic":
            async for chunk in self._stream_anthropic(model, messages, tools, temperature, max_tokens):
                yield chunk
        elif provider == "openai":
            async for chunk in self._stream_openai(model, messages, tools, temperature, max_tokens):
                yield chunk
        elif provider == "google":
            async for chunk in self._stream_google(model, messages, tools, temperature, max_tokens):
                yield chunk
        elif provider == "xai":
            # xAI uses OpenAI-compatible API
            async for chunk in self._stream_openai(model, messages, tools, temperature, max_tokens, provider="xai"):
                yield chunk
        else:
            raise ValueError(f"Unknown provider: {provider}")

    # =========================================================================
    # ANTHROPIC
    # =========================================================================

    def _get_anthropic_client(self):
        if "anthropic" not in self._clients:
            import anthropic
            self._clients["anthropic"] = anthropic.AsyncAnthropic(
                api_key=self._settings.anthropic_api_key,
            )
        return self._clients["anthropic"]

    def _messages_to_anthropic(
        self, messages: list[dict[str, Any]]
    ) -> tuple[str, list[dict[str, Any]]]:
        """Convert OpenAI-format messages to Anthropic format.

        Returns (system_prompt, messages).
        """
        system = ""
        converted = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"] if isinstance(msg["content"], str) else str(msg["content"])
            elif msg["role"] == "tool":
                # Convert tool result to Anthropic format
                converted.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.get("tool_call_id", ""),
                        "content": msg["content"] if isinstance(msg["content"], str) else str(msg["content"]),
                    }],
                })
            elif msg["role"] == "assistant" and msg.get("tool_calls"):
                # Convert assistant tool_calls to Anthropic tool_use blocks
                content: list[dict[str, Any]] = []
                if msg.get("content"):
                    content.append({"type": "text", "text": msg["content"]})
                for tc in msg["tool_calls"]:
                    import json
                    args = tc["function"]["arguments"]
                    if isinstance(args, str):
                        args = json.loads(args)
                    content.append({
                        "type": "tool_use",
                        "id": tc["id"],
                        "name": tc["function"]["name"],
                        "input": args,
                    })
                converted.append({"role": "assistant", "content": content})
            else:
                converted.append({
                    "role": msg["role"],
                    "content": msg["content"] if isinstance(msg["content"], str) else str(msg.get("content", "")),
                })
        return system, converted

    def _tools_to_anthropic(self, tools: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
        """Convert OpenAI tool format to Anthropic format."""
        if not tools:
            return None
        anthropic_tools = []
        for tool in tools:
            fn = tool.get("function", tool)
            anthropic_tools.append({
                "name": fn["name"],
                "description": fn.get("description", ""),
                "input_schema": fn.get("parameters", {"type": "object", "properties": {}}),
            })
        return anthropic_tools

    async def _call_anthropic(
        self, model: str, messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None, temperature: float, max_tokens: int,
    ) -> LLMResponse:
        client = self._get_anthropic_client()
        system, converted_msgs = self._messages_to_anthropic(messages)
        anthropic_tools = self._tools_to_anthropic(tools)

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": converted_msgs,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system:
            kwargs["system"] = system
        if anthropic_tools:
            kwargs["tools"] = anthropic_tools

        response = await client.messages.create(**kwargs)

        content = ""
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "type": "function",
                    "function": {
                        "name": block.name,
                        "arguments": _json_dumps(block.input),
                    },
                })

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            usage=TokenUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                model=model,
            ),
            stop_reason=response.stop_reason or "",
        )

    async def _stream_anthropic(
        self, model: str, messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None, temperature: float, max_tokens: int,
    ) -> AsyncIterator[StreamChunk]:
        client = self._get_anthropic_client()
        system, converted_msgs = self._messages_to_anthropic(messages)
        anthropic_tools = self._tools_to_anthropic(tools)

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": converted_msgs,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system:
            kwargs["system"] = system
        if anthropic_tools:
            kwargs["tools"] = anthropic_tools

        input_tokens = 0
        output_tokens = 0
        current_tool_id = ""
        current_tool_name = ""

        async with client.messages.stream(**kwargs) as stream:
            async for event in stream:
                if event.type == "message_start":
                    if hasattr(event, "message") and hasattr(event.message, "usage"):
                        input_tokens = event.message.usage.input_tokens
                elif event.type == "content_block_start":
                    block = event.content_block
                    if block.type == "tool_use":
                        current_tool_id = block.id
                        current_tool_name = block.name
                        yield StreamChunk(
                            type="tool_call_start",
                            tool_call_id=block.id,
                            tool_name=block.name,
                        )
                elif event.type == "content_block_delta":
                    delta = event.delta
                    if delta.type == "text_delta":
                        yield StreamChunk(type="text", content=delta.text)
                    elif delta.type == "input_json_delta":
                        yield StreamChunk(
                            type="tool_call_delta",
                            tool_call_id=current_tool_id,
                            tool_name=current_tool_name,
                            tool_arguments=delta.partial_json,
                        )
                elif event.type == "content_block_stop":
                    if current_tool_id:
                        yield StreamChunk(
                            type="tool_call_end",
                            tool_call_id=current_tool_id,
                            tool_name=current_tool_name,
                        )
                        current_tool_id = ""
                        current_tool_name = ""
                elif event.type == "message_delta":
                    if hasattr(event, "usage"):
                        output_tokens = event.usage.output_tokens

        yield StreamChunk(
            type="usage",
            usage=TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens, model=model),
        )
        yield StreamChunk(type="done")

    # =========================================================================
    # OPENAI (also used for xAI via compatible API)
    # =========================================================================

    def _get_openai_client(self, provider: str = "openai"):
        if provider not in self._clients:
            import openai
            if provider == "xai":
                self._clients[provider] = openai.AsyncOpenAI(
                    api_key=self._settings.xai_api_key,
                    base_url="https://api.x.ai/v1",
                )
            else:
                self._clients[provider] = openai.AsyncOpenAI(
                    api_key=self._settings.openai_api_key,
                )
        return self._clients[provider]

    async def _call_openai(
        self, model: str, messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None, temperature: float, max_tokens: int,
    ) -> LLMResponse:
        return await self._call_openai_compat("openai", model, messages, tools, temperature, max_tokens)

    async def _call_xai(
        self, model: str, messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None, temperature: float, max_tokens: int,
    ) -> LLMResponse:
        return await self._call_openai_compat("xai", model, messages, tools, temperature, max_tokens)

    async def _call_openai_compat(
        self, provider: str, model: str, messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None, temperature: float, max_tokens: int,
    ) -> LLMResponse:
        client = self._get_openai_client(provider)

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools

        response = await client.chat.completions.create(**kwargs)
        choice = response.choices[0]

        tool_calls = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                tool_calls.append({
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                })

        return LLMResponse(
            content=choice.message.content or "",
            tool_calls=tool_calls,
            usage=TokenUsage(
                input_tokens=response.usage.prompt_tokens if response.usage else 0,
                output_tokens=response.usage.completion_tokens if response.usage else 0,
                model=model,
            ),
            stop_reason=choice.finish_reason or "",
        )

    async def _stream_openai(
        self, model: str, messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None, temperature: float, max_tokens: int,
        provider: str = "openai",
    ) -> AsyncIterator[StreamChunk]:
        client = self._get_openai_client(provider)

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        if tools:
            kwargs["tools"] = tools

        current_tool_calls: dict[int, dict[str, str]] = {}
        input_tokens = 0
        output_tokens = 0

        async for chunk in await client.chat.completions.create(**kwargs):
            if not chunk.choices and chunk.usage:
                input_tokens = chunk.usage.prompt_tokens
                output_tokens = chunk.usage.completion_tokens
                continue

            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            if delta.content:
                yield StreamChunk(type="text", content=delta.content)

            if delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    idx = tc_delta.index
                    if idx not in current_tool_calls:
                        current_tool_calls[idx] = {"id": "", "name": "", "arguments": ""}

                    if tc_delta.id:
                        current_tool_calls[idx]["id"] = tc_delta.id
                    if tc_delta.function and tc_delta.function.name:
                        current_tool_calls[idx]["name"] = tc_delta.function.name
                        yield StreamChunk(
                            type="tool_call_start",
                            tool_call_id=current_tool_calls[idx]["id"],
                            tool_name=tc_delta.function.name,
                        )
                    if tc_delta.function and tc_delta.function.arguments:
                        current_tool_calls[idx]["arguments"] += tc_delta.function.arguments
                        yield StreamChunk(
                            type="tool_call_delta",
                            tool_call_id=current_tool_calls[idx]["id"],
                            tool_name=current_tool_calls[idx]["name"],
                            tool_arguments=tc_delta.function.arguments,
                        )

            if chunk.choices[0].finish_reason:
                for tc_data in current_tool_calls.values():
                    if tc_data["id"]:
                        yield StreamChunk(
                            type="tool_call_end",
                            tool_call_id=tc_data["id"],
                            tool_name=tc_data["name"],
                        )

        yield StreamChunk(
            type="usage",
            usage=TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens, model=model),
        )
        yield StreamChunk(type="done")

    # =========================================================================
    # GOOGLE
    # =========================================================================

    def _get_google_client(self):
        if "google" not in self._clients:
            from google import genai
            self._clients["google"] = genai.Client(api_key=self._settings.google_api_key)
        return self._clients["google"]

    async def _call_google(
        self, model: str, messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None, temperature: float, max_tokens: int,
    ) -> LLMResponse:
        client = self._get_google_client()
        from google.genai import types

        # Convert messages to Google format
        system_instruction = None
        contents = []
        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            elif msg["role"] == "user":
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=msg["content"])],
                ))
            elif msg["role"] == "assistant":
                contents.append(types.Content(
                    role="model",
                    parts=[types.Part.from_text(text=msg.get("content", ""))],
                ))

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        if system_instruction:
            config.system_instruction = system_instruction

        # Google tools conversion
        if tools:
            google_tools = []
            for tool in tools:
                fn = tool.get("function", tool)
                google_tools.append(types.Tool(
                    function_declarations=[types.FunctionDeclaration(
                        name=fn["name"],
                        description=fn.get("description", ""),
                        parameters=fn.get("parameters"),
                    )],
                ))
            config.tools = google_tools

        response = await client.aio.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )

        content = ""
        tool_calls = []
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if part.text:
                    content += part.text
                elif part.function_call:
                    tool_calls.append({
                        "id": f"call_{part.function_call.name}",
                        "type": "function",
                        "function": {
                            "name": part.function_call.name,
                            "arguments": _json_dumps(dict(part.function_call.args) if part.function_call.args else {}),
                        },
                    })

        usage_meta = response.usage_metadata
        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            usage=TokenUsage(
                input_tokens=usage_meta.prompt_token_count if usage_meta else 0,
                output_tokens=usage_meta.candidates_token_count if usage_meta else 0,
                model=model,
            ),
            stop_reason="stop",
        )

    async def _stream_google(
        self, model: str, messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None, temperature: float, max_tokens: int,
    ) -> AsyncIterator[StreamChunk]:
        client = self._get_google_client()
        from google.genai import types

        system_instruction = None
        contents = []
        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            elif msg["role"] == "user":
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=msg["content"])],
                ))
            elif msg["role"] == "assistant":
                contents.append(types.Content(
                    role="model",
                    parts=[types.Part.from_text(text=msg.get("content", ""))],
                ))

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        if system_instruction:
            config.system_instruction = system_instruction

        input_tokens = 0
        output_tokens = 0

        async for chunk in client.aio.models.generate_content_stream(
            model=model,
            contents=contents,
            config=config,
        ):
            if chunk.candidates:
                for part in chunk.candidates[0].content.parts:
                    if part.text:
                        yield StreamChunk(type="text", content=part.text)
            if chunk.usage_metadata:
                input_tokens = chunk.usage_metadata.prompt_token_count or 0
                output_tokens = chunk.usage_metadata.candidates_token_count or 0

        yield StreamChunk(
            type="usage",
            usage=TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens, model=model),
        )
        yield StreamChunk(type="done")


def _json_dumps(obj: Any) -> str:
    """Safe JSON serialization."""
    import json
    return json.dumps(obj, ensure_ascii=False)
