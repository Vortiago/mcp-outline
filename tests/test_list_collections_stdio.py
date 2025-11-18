"""
Integration test for list_collections tool in stdio mode.

Tests that the tool works correctly when called with empty arguments,
as GitHub Copilot CLI does.
"""

import os

import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.types import CallToolResult, TextContent


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_collections_tool_schema():
    """
    Test that list_collections has a proper input schema.

    This verifies that the tool schema allows empty arguments.
    """
    env = os.environ.copy()
    env["MCP_TRANSPORT"] = "stdio"

    server_params = StdioServerParameters(
        command="python", args=["-m", "mcp_outline"], env=env
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()

            # List available tools
            tools_result = await session.list_tools()

            # Find list_collections tool
            list_collections_tool = None
            for tool in tools_result.tools:
                if tool.name == "list_collections":
                    list_collections_tool = tool
                    break

            assert list_collections_tool is not None, (
                "list_collections tool not found"
            )

            # The schema should be a valid JSON Schema
            assert isinstance(list_collections_tool.inputSchema, dict)

            # For a tool with no parameters, the schema should be:
            # - Either {"type": "object", "properties": {}}
            # - Or {"type": "object"} with no properties
            schema = list_collections_tool.inputSchema
            assert schema.get("type") == "object", (
                "Input schema must be of type 'object'"
            )


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_collections_with_empty_arguments():
    """
    Test calling list_collections with empty arguments.

    This simulates how GitHub Copilot CLI calls tools with no parameters.
    """
    env = os.environ.copy()
    env["MCP_TRANSPORT"] = "stdio"
    # Use a fake API key for testing the tool call structure
    # (it will fail on the API call, but we want to see if it gets that far)
    env["OUTLINE_API_KEY"] = "test-key-for-integration-test"

    server_params = StdioServerParameters(
        command="python", args=["-m", "mcp_outline"], env=env
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()

            # Call list_collections with empty arguments (as Copilot does)
            # This should not raise a JSON parsing error
            try:
                result = await session.call_tool("list_collections", {})

                # Verify the result structure
                assert isinstance(result, CallToolResult)
                assert len(result.content) > 0

                # The content should be text
                first_content = result.content[0]
                assert isinstance(first_content, TextContent)

                # Should contain either collections or an error message
                # (error is expected since we're using a fake API key)
                text = first_content.text
                assert isinstance(text, str)
                assert len(text) > 0

                # The result should either show collections or an API error
                # but NOT a JSON parsing error
                assert "Unexpected end of JSON input" not in text, (
                    "Tool should not produce JSON parsing errors"
                )
                assert "json" not in text.lower() or "API" in text, (
                    "Any JSON-related error suggests argument parsing issue"
                )

            except Exception as e:
                # If we get an exception, it should NOT be about JSON parsing
                error_msg = str(e)
                assert "Unexpected end of JSON input" not in error_msg, (
                    f"Tool call failed with JSON parsing error: {error_msg}"
                )
                assert (
                    "json" not in error_msg.lower()
                    or "api" in error_msg.lower()
                ), f"Unexpected error (possibly JSON parsing): {error_msg}"
                # Re-raise if it's an unexpected error type
                raise


@pytest.mark.integration
@pytest.mark.anyio
async def test_compare_search_and_list_schemas():
    """
    Compare the schemas of search_documents and list_collections.

    This helps identify any differences that might cause issues.
    """
    env = os.environ.copy()
    env["MCP_TRANSPORT"] = "stdio"

    server_params = StdioServerParameters(
        command="python", args=["-m", "mcp_outline"], env=env
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()

            # List available tools
            tools_result = await session.list_tools()

            # Find both tools
            search_tool = None
            list_tool = None

            for tool in tools_result.tools:
                if tool.name == "search_documents":
                    search_tool = tool
                elif tool.name == "list_collections":
                    list_tool = tool

            assert search_tool is not None, "search_documents not found"
            assert list_tool is not None, "list_collections not found"

            # Both should have type: object
            assert search_tool.inputSchema.get("type") == "object"
            assert list_tool.inputSchema.get("type") == "object"

            # search_documents should have required parameters
            search_props = search_tool.inputSchema.get("properties", {})
            assert "query" in search_props, (
                "search_documents should have query parameter"
            )

            # list_collections should have no required parameters
            list_required = list_tool.inputSchema.get("required", [])

            # Verify that list_collections accepts empty arguments
            assert len(list_required) == 0, (
                "list_collections should have no required parameters"
            )
