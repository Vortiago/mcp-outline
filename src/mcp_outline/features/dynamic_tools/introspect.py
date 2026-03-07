"""Build tool metadata maps by introspecting registered tools.

After ``register_all(mcp)`` is called, the builder functions in
this module derive ``TOOL_ENDPOINT_MAP`` and ``WRITE_TOOL_NAMES``
from the ``meta`` and ``annotations`` already present on each
registered tool — no separate hand-maintained files needed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def build_tool_endpoint_map(
    mcp: "FastMCP",
) -> dict[str, str]:
    """Return ``{tool_name: endpoint}`` from tool metadata.

    Each tool is expected to carry
    ``meta={"endpoint": "namespace.method"}`` on its
    ``@mcp.tool()`` decorator.
    """
    result: dict[str, str] = {}
    for name, tool in mcp._tool_manager._tools.items():
        if tool.meta and "endpoint" in tool.meta:
            result[name] = tool.meta["endpoint"]
    return result


def build_write_tool_names(
    mcp: "FastMCP",
) -> frozenset[str]:
    """Return tool names where ``readOnlyHint`` is ``False``."""
    names: set[str] = set()
    for name, tool in mcp._tool_manager._tools.items():
        if (
            tool.annotations is not None
            and tool.annotations.readOnlyHint is False
        ):
            names.add(name)
    return frozenset(names)
