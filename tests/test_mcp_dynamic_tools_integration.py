"""Integration tests for dynamic tool list feature.

Starts the MCP server as a subprocess with
``OUTLINE_DYNAMIC_TOOL_LIST=true`` and verifies that:
- The server starts and completes the MCP handshake.
- The ``tools`` capability advertises ``listChanged: true``.
- Tools are still returned (no crash due to the feature).
"""

import os
import sys

import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


@pytest.mark.integration
@pytest.mark.anyio
async def test_dynamic_tool_list_server_starts():
    """Server starts cleanly with OUTLINE_DYNAMIC_TOOL_LIST=true.

    Guards against: the dynamic tool list feature crashing the
    server at startup or breaking the MCP protocol handshake.
    """
    env = os.environ.copy()
    env["MCP_TRANSPORT"] = "stdio"
    env["OUTLINE_DYNAMIC_TOOL_LIST"] = "true"

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_outline"],
        env=env,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            result = await session.initialize()
            assert result.serverInfo.name == "Document Outline"

            # Verify listChanged capability is advertised
            assert result.capabilities is not None
            assert result.capabilities.tools is not None
            assert result.capabilities.tools.listChanged is True

            # Verify tools are still returned
            tools_result = await session.list_tools()
            assert len(tools_result.tools) > 2


@pytest.mark.integration
@pytest.mark.anyio
async def test_dynamic_tool_list_disabled_no_list_changed():
    """Without the feature, listChanged should not be true.

    Guards against: the feature leaking into default mode.
    """
    env = os.environ.copy()
    env["MCP_TRANSPORT"] = "stdio"
    env.pop("OUTLINE_DYNAMIC_TOOL_LIST", None)

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_outline"],
        env=env,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            result = await session.initialize()

            # listChanged should be absent or False
            if (
                result.capabilities is not None
                and result.capabilities.tools is not None
            ):
                assert result.capabilities.tools.listChanged is not True
