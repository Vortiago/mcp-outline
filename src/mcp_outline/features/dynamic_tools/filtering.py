"""Filtering logic for dynamic tool list via endpoint probing."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Dict, List, Optional, Set

import anyio
from mcp.types import Tool as MCPTool

from mcp_outline.features.documents.common import (
    _get_header_api_key,
)
from mcp_outline.features.dynamic_tools.tool_endpoint_map import (
    TOOL_ENDPOINT_MAP,
)
from mcp_outline.utils.outline_client import OutlineClient

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _is_enabled() -> bool:
    """Return ``True`` when the dynamic tool list feature is on."""
    return os.getenv("OUTLINE_DYNAMIC_TOOL_LIST", "").lower() not in (
        "false",
        "0",
        "no",
    )


async def get_blocked_tools(
    api_key: Optional[str],
    api_url: Optional[str],
) -> Set[str]:
    """Determine which tools *api_key* cannot access.

    Probes all unique endpoints in ``TOOL_ENDPOINT_MAP``
    concurrently. Endpoints returning 401 are mapped back
    to their tool names, which are returned as the blocked set.

    Fail-open: returns an empty set on any unexpected error.
    """
    if not api_key:
        return set()

    try:
        client = OutlineClient(api_key=api_key, api_url=api_url)

        # Collect unique endpoints and their tool mappings
        endpoint_to_tools: Dict[str, List[str]] = {}
        for tool_name, endpoint in TOOL_ENDPOINT_MAP.items():
            endpoint_to_tools.setdefault(endpoint, []).append(tool_name)

        unique_endpoints = list(endpoint_to_tools.keys())

        # Probe all endpoints concurrently
        probe_results: Dict[str, bool] = {}

        async def _probe_one(ep: str) -> None:
            probe_results[ep] = await client.probe_endpoint(ep)

        async with anyio.create_task_group() as tg:
            for ep in unique_endpoints:
                tg.start_soon(_probe_one, ep)

        # Map blocked endpoints back to tool names
        blocked: Set[str] = set()
        for endpoint in unique_endpoints:
            if not probe_results.get(endpoint, True):
                blocked.update(endpoint_to_tools[endpoint])

        return blocked

    except Exception as exc:
        logger.debug(
            "Dynamic tool list: endpoint probing failed (%s),"
            " returning full tool list",
            exc,
        )
        return set()


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------


def install_dynamic_tool_list(mcp: "FastMCP") -> None:
    """Install per-request tool filtering on *mcp*.

    Re-registers the lowlevel ``tools/list`` handler so that
    tools whose endpoints are blocked (401) are hidden.
    Enabled by default; set ``OUTLINE_DYNAMIC_TOOL_LIST=false``
    to disable.

    Call this **after** ``register_all(mcp)``.
    """
    if not _is_enabled():
        return

    original_list_tools = mcp.list_tools

    async def filtered_list_tools() -> List[MCPTool]:
        tools: List[MCPTool] = await original_list_tools()

        api_key = _get_header_api_key() or os.getenv("OUTLINE_API_KEY")
        api_url = os.getenv("OUTLINE_API_URL")

        blocked = await get_blocked_tools(api_key, api_url)

        if blocked:
            return [t for t in tools if t.name not in blocked]

        return tools

    # Re-register with the lowlevel server so the protocol
    # handler calls our filtered function instead of the
    # original captured reference.
    mcp._mcp_server.list_tools()(filtered_list_tools)
