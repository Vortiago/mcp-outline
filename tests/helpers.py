"""Shared test helpers for unit and integration tests.

Utilities used across multiple test modules.  E2E-specific
helpers live in ``tests/e2e/helpers.py``.
"""

from mcp.types import ListToolsRequest


async def list_tools_via_handler(mcp_server):
    """Call list_tools through the lowlevel MCP handler.

    This is the code path real MCP clients use
    (``tools/list`` JSON-RPC request).  The handler is
    registered during ``FastMCP.__init__`` and may differ
    from the instance-level ``mcp.list_tools`` attribute
    that ``install_dynamic_tool_list`` patches.
    """
    handler = mcp_server._mcp_server.request_handlers[ListToolsRequest]
    server_result = await handler(ListToolsRequest())
    return server_result.root.tools
