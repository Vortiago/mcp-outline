"""Integration tests for dynamic tool list feature.

Starts the MCP server as a subprocess with
``OUTLINE_DYNAMIC_TOOL_LIST=true`` and verifies that:
- The server starts and completes the MCP handshake.
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
    env = {k: v for k, v in os.environ.items() if not k.startswith("OUTLINE_")}
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

            # Verify tools are still returned
            tools_result = await session.list_tools()
            assert len(tools_result.tools) > 2
