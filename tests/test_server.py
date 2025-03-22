"""
Tests for the MCP Outline server.
"""
from mcp_outline.server import mcp
import pytest

@pytest.mark.anyio
async def test_server_initialization():
    """Test that the server initializes correctly."""
    assert mcp.name == "Document Outline"
    assert len(await mcp.list_tools()) > 0  # Ensure functions are registered
