"""
Test to simulate GitHub Copilot CLI behavior with different tool schemas.

This test simulates what happens when an LLM sees tool schemas with
different parameter configurations and what arguments it might generate.
"""

import json

import pytest


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

    print("\n=== Schema Analysis ===")
    print(f"\nNo properties:")
    print(json.dumps(schema_no_properties, indent=2))
    print("^ LLM interpretation: 'No parameters' -> might send ''")

    print(f"\nWith optional parameter:")
    print(json.dumps(schema_with_optional, indent=2))
    print("^ LLM interpretation: 'Optional parameter' -> should send {}")

    print(f"\nWith required parameter:")
    print(json.dumps(schema_with_required, indent=2))
    print(
        "^ LLM interpretation: 'Required parameter' -> must send {\"query\": ...}"
    )


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

    # Test parsing
    print("\n=== GitHub Copilot CLI Log Analysis ===")

    print(
        f"\nActual arguments sent: {repr(copilot_tool_call['function']['arguments'])}"
    )
    try:
        json.loads(copilot_tool_call["function"]["arguments"])
        print("✓ Valid JSON")
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON: {e}")

    print(
        f"\nCorrect arguments: {repr(correct_tool_call['function']['arguments'])}"
    )
    try:
        result = json.loads(correct_tool_call["function"]["arguments"])
        print(f"✓ Valid JSON: {result}")
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON: {e}")


def test_hypothesis_about_schema_change():
    """
    Test our hypothesis: Adding an optional parameter makes LLMs
    send valid JSON objects instead of empty strings.

    This is based on the observation that tools with parameters
    (like search_documents) work fine, while parameterless tools
    (like list_collections) fail.
    """
    # Evidence from user's log:
    # 1. search_documents works: arguments = "{\"query\": \"*\", \"limit\": 100}"
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

    print("\n=== Hypothesis Testing ===")
    print("\nWorking schema (search_documents):")
    print(json.dumps(working_schema, indent=2))
    print("Result: LLM sends valid JSON with required parameters")

    print("\nFailing schema (old list_collections):")
    print(json.dumps(failing_schema, indent=2))
    print("Result: LLM sends empty string ''")

    print("\nFixed schema (new list_collections):")
    print(json.dumps(fixed_schema, indent=2))
    print('Hypothesis: LLM will now send {} or {"unused": null}')

    # The key insight: Tools with ANY parameter structure (even optional)
    # signal to the LLM that it should construct a JSON object.
    # Tools with EMPTY properties might be interpreted as "no data needed"
    # leading to empty string instead of empty object.
