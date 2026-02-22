"""
Integration tests for MCP server functionality.

Tests that start the actual MCP server and verify it works through the
MCP protocol.
"""

import os
import sys

import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


@pytest.mark.integration
@pytest.mark.anyio
async def test_mcp_server_integration():
    """
    Integration test: Start MCP server and verify basic functionality.

    This test validates:
    - Server starts without errors
    - MCP protocol handshake succeeds
    - Stdio transport works
    - Multiple tools are registered and discoverable
    """
    # Set environment for stdio mode
    env = os.environ.copy()
    env["MCP_TRANSPORT"] = "stdio"

    server_params = StdioServerParameters(
        command="python", args=["-m", "mcp_outline"], env=env
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            result = await session.initialize()
            assert result.serverInfo.name == "Document Outline"
            assert result.protocolVersion is not None

            # List available tools
            tools_result = await session.list_tools()

            # Smoke test: Verify we get a reasonable number of tools
            # Using > 2 to be flexible as tools are added/removed
            assert len(tools_result.tools) > 2, (
                "Server should register multiple tools"
            )

            # Verify tools have expected structure
            for tool in tools_result.tools:
                assert tool.name is not None
                assert tool.description is not None


@pytest.mark.integration
@pytest.mark.anyio
async def test_read_only_mode_tool_list():
    """
    Verify that OUTLINE_READ_ONLY=true omits write tools from MCP protocol.

    This tests the actual MCP protocol response, not just Python-level
    registration.
    """
    env = os.environ.copy()
    env["MCP_TRANSPORT"] = "stdio"
    env["OUTLINE_READ_ONLY"] = "true"

    server_params = StdioServerParameters(
        command=sys.executable, args=["-m", "mcp_outline"], env=env
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = {t.name for t in (await session.list_tools()).tools}

            # Write tools must be absent
            assert "create_document" not in tools
            assert "update_document" not in tools
            assert "delete_document" not in tools
            assert "create_collection" not in tools

            # Read tools must still be present
            assert "search_documents" in tools
            assert "read_document" in tools
            assert "list_collections" in tools
            assert "export_collection" in tools
