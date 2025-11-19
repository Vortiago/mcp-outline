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
