"""
Tests for the MCP Outline server.
"""

import os
from unittest.mock import patch

import pytest
from mcp.server.fastmcp import FastMCP

from mcp_outline.features import register_all


@pytest.fixture
def fresh_mcp_server():
    """Create a fresh MCP server instance for testing."""
    return FastMCP("Test Server")


@pytest.mark.anyio
async def test_server_initialization():
    """Test that the server initializes correctly."""
    from mcp_outline.server import mcp

    assert mcp.name == "Document Outline"
    assert len(await mcp.list_tools()) > 0  # Ensure functions are registered


@pytest.mark.anyio
async def test_ai_tools_disabled_via_env_var(fresh_mcp_server):
    """Test that AI tools are not registered when disabled via env var."""
    with patch.dict(os.environ, {"OUTLINE_DISABLE_AI_TOOLS": "true"}):
        register_all(fresh_mcp_server)
        tools = await fresh_mcp_server.list_tools()
        tool_names = [tool.name for tool in tools]

        assert "ask_ai_about_documents" not in tool_names
        # Verify other tools are still registered
        assert "search_documents" in tool_names


@pytest.mark.anyio
async def test_ai_tools_enabled_by_default(fresh_mcp_server):
    """Test that AI tools are registered when env var is not set."""
    with patch.dict(os.environ, {}, clear=False):
        # Ensure the env var is not set
        os.environ.pop("OUTLINE_DISABLE_AI_TOOLS", None)
        register_all(fresh_mcp_server)
        tools = await fresh_mcp_server.list_tools()
        tool_names = [tool.name for tool in tools]

        assert "ask_ai_about_documents" in tool_names


@pytest.mark.anyio
async def test_read_only_mode_disables_write_tools(fresh_mcp_server):
    """Test OUTLINE_READ_ONLY=true blocks write tools, allows read tools."""
    with patch.dict(os.environ, {"OUTLINE_READ_ONLY": "true"}):
        register_all(fresh_mcp_server)
        tools = await fresh_mcp_server.list_tools()
        tool_names = [tool.name for tool in tools]

        # Verify write tools are NOT registered
        assert "create_document" not in tool_names
        assert "update_document" not in tool_names
        assert "archive_document" not in tool_names
        assert "delete_document" not in tool_names
        assert "move_document" not in tool_names
        assert "batch_archive_documents" not in tool_names

        # Verify read tools ARE registered
        assert "search_documents" in tool_names
        assert "read_document" in tool_names
        assert "list_document_comments" in tool_names
        assert "export_collection" in tool_names
        assert "ask_ai_about_documents" in tool_names


@pytest.mark.anyio
async def test_read_only_mode_blocks_destructive_tools(fresh_mcp_server):
    """Test create/update collection tools blocked in read-only mode."""
    with patch.dict(os.environ, {"OUTLINE_READ_ONLY": "true"}):
        register_all(fresh_mcp_server)
        tools = await fresh_mcp_server.list_tools()
        tool_names = [tool.name for tool in tools]

        # Verify write/destructive collection tools are NOT registered
        assert "create_collection" not in tool_names
        assert "update_collection" not in tool_names
        assert "delete_collection" not in tool_names

        # Verify export collection tools ARE registered
        assert "export_collection" in tool_names
        assert "export_all_collections" in tool_names


@pytest.mark.anyio
async def test_disable_delete_blocks_deletes_only(fresh_mcp_server):
    """Test OUTLINE_DISABLE_DELETE=true blocks only delete ops."""
    with patch.dict(os.environ, {"OUTLINE_DISABLE_DELETE": "true"}):
        register_all(fresh_mcp_server)
        tools = await fresh_mcp_server.list_tools()
        tool_names = [tool.name for tool in tools]

        # Verify delete tools are NOT registered
        assert "delete_document" not in tool_names
        assert "delete_collection" not in tool_names

        # Verify other write tools ARE registered
        assert "create_document" in tool_names
        assert "update_document" in tool_names
        assert "archive_document" in tool_names
        assert "create_collection" in tool_names
        assert "update_collection" in tool_names


@pytest.mark.anyio
async def test_both_flags_together(fresh_mcp_server):
    """Test that OUTLINE_READ_ONLY takes precedence when both are set."""
    with patch.dict(
        os.environ,
        {"OUTLINE_READ_ONLY": "true", "OUTLINE_DISABLE_DELETE": "true"},
    ):
        register_all(fresh_mcp_server)
        tools = await fresh_mcp_server.list_tools()
        tool_names = [tool.name for tool in tools]

        # Should behave like read-only mode (same as test 1)
        # Verify write tools are NOT registered
        assert "create_document" not in tool_names
        assert "update_document" not in tool_names
        assert "archive_document" not in tool_names
        assert "delete_document" not in tool_names
        assert "move_document" not in tool_names
        assert "batch_archive_documents" not in tool_names

        # Verify read tools ARE registered
        assert "search_documents" in tool_names
        assert "read_document" in tool_names
        assert "list_document_comments" in tool_names
        assert "export_collection" in tool_names
        assert "ask_ai_about_documents" in tool_names


@pytest.mark.anyio
async def test_ai_tools_work_with_read_only(fresh_mcp_server):
    """Test that AI tools work in read-only mode unless separately disabled."""
    # Test 1: AI tools work with read-only mode
    with patch.dict(os.environ, {"OUTLINE_READ_ONLY": "true"}):
        register_all(fresh_mcp_server)
        tools = await fresh_mcp_server.list_tools()
        tool_names = [tool.name for tool in tools]

        assert "ask_ai_about_documents" in tool_names

    # Test 2: AI tools disabled when both flags are set
    fresh_mcp_server2 = FastMCP("Test Server 2")
    with patch.dict(
        os.environ,
        {"OUTLINE_READ_ONLY": "true", "OUTLINE_DISABLE_AI_TOOLS": "true"},
    ):
        register_all(fresh_mcp_server2)
        tools2 = await fresh_mcp_server2.list_tools()
        tool_names2 = [tool.name for tool in tools2]

        assert "ask_ai_about_documents" not in tool_names2
