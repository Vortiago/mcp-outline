"""
Test to simulate GitHub Copilot CLI behavior with different tool schemas.

This test simulates what happens when an LLM sees tool schemas with
different parameter configurations and what arguments it might generate.
"""

import json

import pytest


def test_pydantic_validator_coerces_empty_string():
    """
    Test that the patch's field validator works correctly.

    This directly tests the core fix: the Pydantic validator that
    coerces empty string to empty dict.
    """
    from mcp_outline.patches.copilot_cli import patch_for_copilot_cli

    # Apply the patch
    patch_for_copilot_cli()

    try:
        import mcp.types
    except ImportError:
        pytest.skip("MCP SDK not installed")

    # Test 1: Empty string should be coerced to empty dict
    params = mcp.types.CallToolRequestParams(
        name="test_tool",
        arguments="",  # This is what Copilot CLI sends
    )
    assert params.arguments == {}, (
        "Empty string should be coerced to empty dict"
    )

    # Test 2: Empty dict should pass through unchanged
    params2 = mcp.types.CallToolRequestParams(name="test_tool", arguments={})
    assert params2.arguments == {}, "Empty dict should pass through"

    # Test 3: Normal values should pass through unchanged
    params3 = mcp.types.CallToolRequestParams(
        name="test_tool", arguments={"key": "value"}
    )
    assert params3.arguments == {"key": "value"}, (
        "Normal values should pass through"
    )

    # Test 4: None should pass through unchanged
    params4 = mcp.types.CallToolRequestParams(name="test_tool", arguments=None)
    assert params4.arguments is None, "None should pass through"

    # Test 5: Patch is idempotent
    patch_for_copilot_cli()  # Apply again
    params5 = mcp.types.CallToolRequestParams(name="test_tool", arguments="")
    assert params5.arguments == {}, (
        "Patch should still work after reapplication"
    )


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
