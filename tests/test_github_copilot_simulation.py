"""
Test to simulate GitHub Copilot CLI behavior with different tool schemas.

This test simulates what happens when an LLM sees tool schemas with
different parameter configurations and what arguments it might generate.
"""

import json
from typing import Any

import pytest
from mcp.server.context import ServerRequestContext

from mcp_outline.patches import coerce_empty_tool_arguments


def _context(method: str, params: Any) -> ServerRequestContext:
    """Build a request context with only the fields the middleware reads."""
    return ServerRequestContext(
        session=None,  # type: ignore[arg-type]
        lifespan_context=None,
        protocol_version="2025-11-25",
        method=method,
        params=params,
    )


async def _arguments_seen_by_handler(method: str, params: Any) -> Any:
    """Run the middleware and return the arguments the handler gets."""

    async def call_next(ctx):
        return ctx.params.get("arguments")

    return await coerce_empty_tool_arguments(
        _context(method, params), call_next
    )


@pytest.mark.anyio
async def test_empty_string_arguments_become_empty_dict():
    """Copilot CLI's "" arguments reach the handler as {}."""
    params = {"name": "list_collections", "arguments": ""}
    assert await _arguments_seen_by_handler("tools/call", params) == {}


@pytest.mark.anyio
@pytest.mark.parametrize("arguments", [{}, {"key": "value"}, None])
async def test_valid_arguments_pass_through(arguments):
    """A dict or a missing value reaches the handler unchanged."""
    params = {"name": "list_collections", "arguments": arguments}
    result = await _arguments_seen_by_handler("tools/call", params)
    assert result == arguments


@pytest.mark.anyio
async def test_other_methods_pass_through():
    """Only tools/call is rewritten."""
    params = {"name": "x", "arguments": ""}
    assert await _arguments_seen_by_handler("prompts/get", params) == ""


def test_empty_string_is_not_valid_json():
    """Confirm that empty string is NOT valid JSON."""
    with pytest.raises(json.JSONDecodeError, match="Expecting value"):
        json.loads("")


def test_empty_object_is_valid_json():
    """Confirm that empty object IS valid JSON."""
    result = json.loads("{}")
    assert result == {}


def test_schema_signals_for_parameterless_tools():
    """
    Test what different schemas signal to an LLM.

    When an LLM sees a tool schema, it uses the schema to generate arguments.
    """

    # Schema with NO properties (what we had before)
    schema_no_properties = {
        "type": "object",
        "properties": {},
        "title": "list_collectionsArguments",
    }

    # Schema with optional dummy parameter (what we have now)
    schema_with_optional = {
        "type": "object",
        "properties": {
            "unused": {
                "anyOf": [{"type": "string"}, {"type": "null"}],
                "default": None,
                "title": "Unused",
            }
        },
        "title": "list_collectionsArguments",
    }

    # Schema with required parameter
    schema_with_required = {
        "type": "object",
        "properties": {"query": {"type": "string", "title": "Query"}},
        "required": ["query"],
        "title": "search_documentsArguments",
    }

    # Analysis:
    # 1. schema_no_properties: LLM might think "no parameters needed"
    #    and send empty string "" or {}
    # 2. schema_with_optional: LLM sees there's a parameter structure,
    #    even if optional, so should send {} or {"unused": null}
    # 3. schema_with_required: LLM must send {"query": "..."}

    # Verify schemas are valid
    assert schema_no_properties["type"] == "object"
    assert schema_with_optional["type"] == "object"
    assert schema_with_required["type"] == "object"
    assert "query" in schema_with_required["properties"]


def test_copilot_log_analysis():
    """
    Analyze the actual GitHub Copilot CLI log to understand the issue.
    """
    # From the user's log:
    copilot_tool_call = {
        "id": "toolu_vrtx_01SMaVo92cmVr11B6oCRFxVY",
        "type": "function",
        "function": {
            "name": "outline-list_collections",
            "arguments": "",  # <- THE PROBLEM
        },
    }

    # This is what it should be:
    correct_tool_call = {
        "id": "toolu_vrtx_01SMaVo92cmVr11B6oCRFxVY",
        "type": "function",
        "function": {
            "name": "outline-list_collections",
            "arguments": "{}",  # <- Valid JSON
        },
    }

    # Test that Copilot's empty string is invalid JSON
    with pytest.raises(json.JSONDecodeError):
        json.loads(copilot_tool_call["function"]["arguments"])

    # Test that the correct format is valid JSON
    result = json.loads(correct_tool_call["function"]["arguments"])
    assert result == {}


def test_hypothesis_about_schema_change():
    """
    Test our hypothesis: Adding an optional parameter makes LLMs
    send valid JSON objects instead of empty strings.

    This is based on the observation that tools with parameters
    (like search_documents) work fine, while parameterless tools
    (like list_collections) fail.
    """
    # Evidence from user's log:
    # 1. search_documents works: has query & limit args
    # 2. list_collections fails: arguments = ""

    # Working tool schema (has parameters):
    working_schema = {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    }

    # Failing tool schema (no parameters):
    failing_schema = {"type": "object", "properties": {}}

    # Our fix (optional dummy parameter):
    fixed_schema = {
        "type": "object",
        "properties": {
            "unused": {
                "anyOf": [{"type": "string"}, {"type": "null"}],
                "default": None,
            }
        },
    }

    # The key insight: Tools with ANY parameter structure (even optional)
    # signal to the LLM that it should construct a JSON object.
    # Tools with EMPTY properties might be interpreted as "no data needed"
    # leading to empty string instead of empty object.

    # Verify all schemas are valid
    assert working_schema["type"] == "object"
    assert failing_schema["type"] == "object"
    assert fixed_schema["type"] == "object"
    assert "query" in working_schema["properties"]
    assert "unused" in fixed_schema["properties"]
