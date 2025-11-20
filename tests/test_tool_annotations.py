"""
Tests for tool annotations.

This module verifies that MCP tools have correct annotations for read-only,
destructive, idempotent, and open-world operations.
"""

import pytest
from mcp.server.fastmcp import FastMCP

from mcp_outline.features import register_all


@pytest.fixture
def fresh_mcp_server():
    """Create a fresh MCP server instance for testing."""
    return FastMCP("Test Server")


@pytest.mark.anyio
async def test_read_only_tools_have_correct_annotations(fresh_mcp_server):
    """Test that read-only tools have readOnlyHint=True."""
    register_all(fresh_mcp_server)
    tools = await fresh_mcp_server.list_tools()

    # Define expected read-only tools
    read_only_tools = [
        "search_documents",
        "read_document",
        "list_document_comments",
        "export_collection",
        "get_comment",
        "list_collections",
        "get_collection_structure",
        "export_document",
        "get_document_backlinks",
        "list_archived_documents",
        "list_trash",
        "export_all_collections",
    ]

    for tool_name in read_only_tools:
        tool = next((t for t in tools if t.name == tool_name), None)
        assert tool is not None, f"Tool {tool_name} not found"
        assert tool.annotations is not None, (
            f"Tool {tool_name} has no annotations"
        )
        assert tool.annotations.readOnlyHint is True, (
            f"Tool {tool_name} should have readOnlyHint=True"
        )


@pytest.mark.anyio
async def test_destructive_tools_have_correct_annotations(fresh_mcp_server):
    """Test that destructive tools have destructiveHint=True."""
    register_all(fresh_mcp_server)
    tools = await fresh_mcp_server.list_tools()

    # Define expected destructive tools
    destructive_tools = [
        "delete_document",
        "delete_collection",
        "update_document",
        "move_document",
        "batch_delete_documents",
        "update_collection",
        "archive_document",
        "batch_archive_documents",
        "batch_move_documents",
        "batch_update_documents",
        "batch_create_documents",
    ]

    for tool_name in destructive_tools:
        tool = next((t for t in tools if t.name == tool_name), None)
        # Skip if tool not found (may be conditionally registered)
        if tool is None:
            continue
        assert tool.annotations is not None, (
            f"Tool {tool_name} has no annotations"
        )
        assert tool.annotations.destructiveHint is True, (
            f"Tool {tool_name} should have destructiveHint=True"
        )


@pytest.mark.anyio
async def test_non_destructive_write_tools(fresh_mcp_server):
    """Test non-destructive write tools have correct annotations."""
    register_all(fresh_mcp_server)
    tools = await fresh_mcp_server.list_tools()

    # Define non-destructive write tools
    non_destructive_write_tools = [
        "create_document",
        "add_comment",
        "create_collection",
        "unarchive_document",
        "restore_document",
    ]

    for tool_name in non_destructive_write_tools:
        tool = next((t for t in tools if t.name == tool_name), None)
        # Skip if tool not found (may be conditionally registered)
        if tool is None:
            continue
        assert tool.annotations is not None, (
            f"Tool {tool_name} has no annotations"
        )
        assert tool.annotations.readOnlyHint is False, (
            f"Tool {tool_name} should have readOnlyHint=False"
        )
        assert tool.annotations.destructiveHint is False, (
            f"Tool {tool_name} should have destructiveHint=False"
        )


@pytest.mark.anyio
async def test_idempotent_tools(fresh_mcp_server):
    """Test that idempotent tools have idempotentHint=True."""
    register_all(fresh_mcp_server)
    tools = await fresh_mcp_server.list_tools()

    # Define expected idempotent tools
    idempotent_tools = [
        "delete_document",
        "archive_document",
        "search_documents",
        "batch_delete_documents",
        "read_document",
        "list_collections",
        "get_collection_structure",
        "export_document",
        "list_document_comments",
        "get_comment",
        "get_document_backlinks",
        "unarchive_document",
        "restore_document",
        "list_archived_documents",
        "list_trash",
        "export_collection",
        "export_all_collections",
        "delete_collection",
        "batch_archive_documents",
        "batch_move_documents",
        "batch_update_documents",
        "batch_create_documents",
    ]

    for tool_name in idempotent_tools:
        tool = next((t for t in tools if t.name == tool_name), None)
        # Skip if tool not found (may be conditionally registered)
        if tool is None:
            continue
        assert tool.annotations is not None, (
            f"Tool {tool_name} has no annotations"
        )
        assert tool.annotations.idempotentHint is True, (
            f"Tool {tool_name} should have idempotentHint=True"
        )


@pytest.mark.anyio
async def test_ai_tools_have_open_world_hint(fresh_mcp_server):
    """Test that AI tools have openWorldHint=True."""
    register_all(fresh_mcp_server)
    tools = await fresh_mcp_server.list_tools()

    # Only AI tools should have openWorldHint (can discover new insights)
    # Regular search works with known entities, so no openWorldHint
    ai_tools = ["ask_ai_about_documents"]

    for tool_name in ai_tools:
        tool = next((t for t in tools if t.name == tool_name), None)
        # Skip if tool not found (may be conditionally registered)
        if tool is None:
            continue
        assert tool.annotations is not None, (
            f"Tool {tool_name} has no annotations"
        )
        assert tool.annotations.openWorldHint is True, (
            f"Tool {tool_name} should have openWorldHint=True"
        )
