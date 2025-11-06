"""
Integration tests for MCP server functionality.

Tests that start the actual MCP server and verify it works through the
MCP protocol.
"""

import os

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
