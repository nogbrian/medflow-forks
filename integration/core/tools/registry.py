"""Declarative tool registry with JSON Schema validation.

Provides a decorator-based API for registering tools that can be used
by the agentic loop. Each tool has a JSON Schema definition, category,
and async handler function.
"""

from __future__ import annotations

import inspect
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, get_type_hints

from core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ToolDefinition:
    """A registered tool with its metadata and handler."""

    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema
    handler: Callable[..., Any]
    category: str = "general"
    idempotent: bool = False
    requires_confirmation: bool = False

    def to_openai_format(self) -> dict[str, Any]:
        """Convert to OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def to_loop_format(self) -> dict[str, Any]:
        """Convert to the format expected by AgenticLoop.tools."""
        return {
            "definition": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
            "handler": self.handler,
            "category": self.category,
            "idempotent": self.idempotent,
        }


class ToolRegistry:
    """Central registry for all available tools.

    Supports registration via decorator or explicit add(), filtering by category,
    and JSON Schema validation of arguments.
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str | None = None,
        description: str = "",
        category: str = "general",
        idempotent: bool = False,
        requires_confirmation: bool = False,
        parameters: dict[str, Any] | None = None,
    ) -> Callable:
        """Decorator to register a function as a tool.

        If parameters schema is not provided, it's auto-generated from
        the function signature using type hints.

        Usage:
            @registry.register(category="crm", description="Search leads")
            async def buscar_lead(name: str, phone: str = "") -> dict:
                ...
        """
        def decorator(fn: Callable) -> Callable:
            tool_name = name or fn.__name__
            tool_desc = description or fn.__doc__ or f"Execute {tool_name}"

            # Clean up docstring description
            if "\n" in tool_desc:
                tool_desc = tool_desc.split("\n")[0].strip()

            schema = parameters or _generate_schema(fn)

            tool_def = ToolDefinition(
                name=tool_name,
                description=tool_desc,
                parameters=schema,
                handler=fn,
                category=category,
                idempotent=idempotent,
                requires_confirmation=requires_confirmation,
            )

            self._tools[tool_name] = tool_def
            logger.debug("tool_registered", name=tool_name, category=category)
            return fn

        return decorator

    def add(self, tool_def: ToolDefinition) -> None:
        """Explicitly add a tool definition."""
        self._tools[tool_def.name] = tool_def

    def get(self, name: str) -> ToolDefinition | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self, category: str | None = None) -> list[ToolDefinition]:
        """List all registered tools, optionally filtered by category."""
        tools = list(self._tools.values())
        if category:
            tools = [t for t in tools if t.category == category]
        return tools

    def get_categories(self) -> list[str]:
        """Get all unique categories."""
        return sorted(set(t.category for t in self._tools.values()))

    def get_for_loop(
        self,
        categories: list[str] | None = None,
        names: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get tools in AgenticLoop format, optionally filtered.

        Returns dict mapping name → {"definition": ..., "handler": ...}
        """
        result = {}
        for tool_def in self._tools.values():
            if categories and tool_def.category not in categories:
                continue
            if names and tool_def.name not in names:
                continue
            result[tool_def.name] = tool_def.to_loop_format()
        return result

    def get_openai_definitions(
        self,
        categories: list[str] | None = None,
        names: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get all tool definitions in OpenAI format."""
        definitions = []
        for tool_def in self._tools.values():
            if categories and tool_def.category not in categories:
                continue
            if names and tool_def.name not in names:
                continue
            definitions.append(tool_def.to_openai_format())
        return definitions

    def validate_arguments(self, name: str, arguments: dict[str, Any]) -> tuple[bool, str]:
        """Validate arguments against the tool's JSON Schema.

        Returns (is_valid, error_message).
        """
        tool_def = self._tools.get(name)
        if not tool_def:
            return False, f"Tool '{name}' not found"

        schema = tool_def.parameters
        required = schema.get("required", [])
        properties = schema.get("properties", {})

        # Check required fields
        for field_name in required:
            if field_name not in arguments:
                return False, f"Missing required field: {field_name}"

        # Check types (basic validation)
        for field_name, value in arguments.items():
            if field_name not in properties:
                continue  # Allow extra fields

            prop_schema = properties[field_name]
            expected_type = prop_schema.get("type")

            if expected_type and not _check_type(value, expected_type):
                return False, f"Field '{field_name}' expected type '{expected_type}', got {type(value).__name__}"

        return True, ""

    @property
    def count(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools


# Module-level registry instance
_global_registry = ToolRegistry()


def tool(
    name: str | None = None,
    description: str = "",
    category: str = "general",
    idempotent: bool = False,
    requires_confirmation: bool = False,
    parameters: dict[str, Any] | None = None,
) -> Callable:
    """Module-level decorator using the global registry.

    Usage:
        @tool(category="crm", description="Search for leads in CRM")
        async def buscar_lead(name: str, phone: str = "") -> dict:
            ...
    """
    return _global_registry.register(
        name=name,
        description=description,
        category=category,
        idempotent=idempotent,
        requires_confirmation=requires_confirmation,
        parameters=parameters,
    )


def get_global_registry() -> ToolRegistry:
    """Get the global tool registry."""
    return _global_registry


# =============================================================================
# SCHEMA GENERATION HELPERS
# =============================================================================


_PYTHON_TO_JSON_TYPE: dict[str, str] = {
    "str": "string",
    "int": "integer",
    "float": "number",
    "bool": "boolean",
    "list": "array",
    "dict": "object",
    "NoneType": "null",
}


def _generate_schema(fn: Callable) -> dict[str, Any]:
    """Auto-generate JSON Schema from function signature."""
    sig = inspect.signature(fn)
    hints = get_type_hints(fn) if hasattr(fn, "__annotations__") else {}

    properties: dict[str, Any] = {}
    required: list[str] = []

    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue

        prop: dict[str, Any] = {}

        # Get type from hints
        hint = hints.get(param_name)
        if hint:
            json_type = _python_type_to_json(hint)
            if json_type:
                prop["type"] = json_type

        # Check if required (no default value)
        if param.default is inspect.Parameter.empty:
            required.append(param_name)
        elif param.default is not None:
            prop["default"] = param.default

        # Extract description from docstring if available
        if not prop.get("type"):
            prop["type"] = "string"

        properties[param_name] = prop

    schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
    }
    if required:
        schema["required"] = required

    return schema


def _python_type_to_json(hint: Any) -> str | None:
    """Convert a Python type hint to JSON Schema type."""
    type_name = getattr(hint, "__name__", str(hint))

    # Handle Optional[X] -> type of X
    origin = getattr(hint, "__origin__", None)
    if origin is not None:
        # Handle list[X], dict[X, Y], etc.
        origin_name = getattr(origin, "__name__", str(origin))
        return _PYTHON_TO_JSON_TYPE.get(origin_name)

    return _PYTHON_TO_JSON_TYPE.get(type_name)


def _check_type(value: Any, expected: str) -> bool:
    """Basic type checking for JSON Schema validation."""
    type_map = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
        "null": type(None),
    }
    expected_types = type_map.get(expected)
    if not expected_types:
        return True  # Unknown type, skip validation
    return isinstance(value, expected_types)
