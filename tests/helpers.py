"""Shared test helpers for unit and integration tests.

Utilities used across multiple test modules.  E2E-specific
helpers live in ``tests/e2e/helpers.py``.
"""

from mcp import Client


async def list_tools_via_handler(mcp_server):
    """Call ``tools/list`` through an in-process MCP client.

    This is the code path real MCP clients use, so the server
    middleware (dynamic tool filtering) runs.
    """
    async with Client(mcp_server) as client:
        result = await client.list_tools()
    return result.tools
