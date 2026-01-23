"""Unit tests for the tool registry."""

import pytest

from core.tools.registry import ToolRegistry, ToolDefinition, _generate_schema


class TestToolRegistration:
    """Test tool registration via decorator and explicit add."""

    def test_register_decorator(self):
        """Tools can be registered via decorator."""
        registry = ToolRegistry()

        @registry.register(description="Test tool", category="test")
        async def my_tool(name: str, count: int = 1) -> str:
            return f"{name} x {count}"

        assert "my_tool" in registry
        assert registry.count == 1

        tool = registry.get("my_tool")
        assert tool is not None
        assert tool.name == "my_tool"
        assert tool.description == "Test tool"
        assert tool.category == "test"

    def test_register_with_custom_name(self):
        """Custom tool names override function name."""
        registry = ToolRegistry()

        @registry.register(name="custom_name", description="Custom")
        async def internal_fn() -> str:
            return "ok"

        assert "custom_name" in registry
        assert "internal_fn" not in registry

    def test_register_explicit_add(self):
        """Tools can be added explicitly."""
        registry = ToolRegistry()
        tool_def = ToolDefinition(
            name="explicit_tool",
            description="Added explicitly",
            parameters={"type": "object", "properties": {}},
            handler=lambda: "ok",
            category="custom",
        )
        registry.add(tool_def)

        assert "explicit_tool" in registry
        assert registry.get("explicit_tool").category == "custom"

    def test_register_with_explicit_parameters(self):
        """Explicit parameter schemas override auto-generation."""
        registry = ToolRegistry()
        schema = {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
            },
            "required": ["query"],
        }

        @registry.register(description="Search", parameters=schema)
        async def search(query: str) -> str:
            return query

        tool = registry.get("search")
        assert tool.parameters == schema


class TestToolListing:
    """Test tool listing and filtering."""

    def setup_method(self):
        self.registry = ToolRegistry()

        @self.registry.register(category="crm", description="CRM tool 1")
        async def crm_tool_1() -> str:
            return ""

        @self.registry.register(category="crm", description="CRM tool 2")
        async def crm_tool_2() -> str:
            return ""

        @self.registry.register(category="calendar", description="Calendar tool")
        async def calendar_tool() -> str:
            return ""

    def test_list_all(self):
        assert len(self.registry.list_tools()) == 3

    def test_list_by_category(self):
        crm_tools = self.registry.list_tools(category="crm")
        assert len(crm_tools) == 2

        cal_tools = self.registry.list_tools(category="calendar")
        assert len(cal_tools) == 1

    def test_get_categories(self):
        categories = self.registry.get_categories()
        assert "crm" in categories
        assert "calendar" in categories

    def test_get_for_loop_format(self):
        tools = self.registry.get_for_loop()
        assert "crm_tool_1" in tools
        assert "definition" in tools["crm_tool_1"]
        assert "handler" in tools["crm_tool_1"]

    def test_get_for_loop_filtered(self):
        tools = self.registry.get_for_loop(categories=["calendar"])
        assert len(tools) == 1
        assert "calendar_tool" in tools

    def test_get_for_loop_by_names(self):
        tools = self.registry.get_for_loop(names=["crm_tool_1", "calendar_tool"])
        assert len(tools) == 2


class TestOpenAIFormat:
    """Test conversion to OpenAI function calling format."""

    def test_to_openai_format(self):
        registry = ToolRegistry()

        @registry.register(description="Echo a message")
        async def echo(message: str) -> str:
            return message

        definitions = registry.get_openai_definitions()
        assert len(definitions) == 1
        assert definitions[0]["type"] == "function"
        assert definitions[0]["function"]["name"] == "echo"
        assert definitions[0]["function"]["description"] == "Echo a message"

    def test_tool_definition_to_openai(self):
        tool_def = ToolDefinition(
            name="test",
            description="A test tool",
            parameters={
                "type": "object",
                "properties": {"x": {"type": "integer"}},
                "required": ["x"],
            },
            handler=lambda x: x,
        )
        result = tool_def.to_openai_format()
        assert result["type"] == "function"
        assert result["function"]["name"] == "test"
        assert result["function"]["parameters"]["required"] == ["x"]


class TestArgumentValidation:
    """Test JSON Schema argument validation."""

    def setup_method(self):
        self.registry = ToolRegistry()

        @self.registry.register(
            description="Test",
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"},
                    "active": {"type": "boolean"},
                },
                "required": ["name"],
            },
        )
        async def validated_tool(name: str, age: int = 0, active: bool = True) -> str:
            return name

    def test_valid_arguments(self):
        is_valid, error = self.registry.validate_arguments(
            "validated_tool", {"name": "John", "age": 30}
        )
        assert is_valid
        assert error == ""

    def test_missing_required_field(self):
        is_valid, error = self.registry.validate_arguments(
            "validated_tool", {"age": 30}
        )
        assert not is_valid
        assert "name" in error

    def test_wrong_type(self):
        is_valid, error = self.registry.validate_arguments(
            "validated_tool", {"name": "John", "age": "not-a-number"}
        )
        assert not is_valid
        assert "age" in error

    def test_unknown_tool(self):
        is_valid, error = self.registry.validate_arguments(
            "nonexistent", {"x": 1}
        )
        assert not is_valid
        assert "not found" in error


class TestSchemaGeneration:
    """Test automatic JSON Schema generation from function signatures."""

    def test_simple_function(self):
        async def fn(name: str, count: int) -> str:
            return ""

        schema = _generate_schema(fn)
        assert schema["type"] == "object"
        assert "name" in schema["properties"]
        assert "count" in schema["properties"]
        assert schema["properties"]["name"]["type"] == "string"
        assert schema["properties"]["count"]["type"] == "integer"
        assert "name" in schema["required"]
        assert "count" in schema["required"]

    def test_optional_parameters(self):
        async def fn(required: str, optional: str = "default") -> str:
            return ""

        schema = _generate_schema(fn)
        assert "required" in schema["required"]
        assert "optional" not in schema["required"]

    def test_bool_type(self):
        async def fn(flag: bool) -> str:
            return ""

        schema = _generate_schema(fn)
        assert schema["properties"]["flag"]["type"] == "boolean"

    def test_skips_self_parameter(self):
        async def fn(self, name: str) -> str:
            return ""

        schema = _generate_schema(fn)
        assert "self" not in schema["properties"]
