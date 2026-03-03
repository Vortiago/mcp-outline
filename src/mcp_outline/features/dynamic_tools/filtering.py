"""Filtering logic for dynamic tool list via API key scopes."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, List, Optional, Set

from mcp.types import Tool as MCPTool

from mcp_outline.features.documents.common import (
    _get_header_api_key,
)
from mcp_outline.features.dynamic_tools.scope_matching import (
    blocked_tools_for_scopes,
)
from mcp_outline.features.dynamic_tools.tool_endpoint_map import (
    TOOL_ENDPOINT_MAP,
)
from mcp_outline.utils.outline_client import OutlineClient, OutlineError

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _is_enabled() -> bool:
    """Return ``True`` when the dynamic tool list feature is on."""
    return os.getenv("OUTLINE_DYNAMIC_TOOL_LIST", "").lower() in (
        "true",
        "1",
        "yes",
    )


async def get_blocked_tools(
    api_key: Optional[str],
    api_url: Optional[str],
) -> Set[str]:
    """Return tool names *api_key* cannot access.

    Calls ``apiKeys.list``, matches by ``last4``, then applies
    scope matching locally.  Fail-open on errors (except 401
    which blocks all tools).
    """
    if not api_key:
        return set()

    try:
        client = OutlineClient(api_key=api_key, api_url=api_url)
        last4 = api_key[-4:]

        # Fetch API keys, paginating if the key isn't in
        # the first page.
        scopes: Optional[List[str]] = None
        found = False
        offset = 0
        limit = 100
        while True:
            try:
                keys = await client.list_api_keys(limit=limit, offset=offset)
            except OutlineError as e:
                if e.status_code == 401:
                    # Key is completely invalid → block all.
                    return set(TOOL_ENDPOINT_MAP.keys())
                # 403 / other → fail-open.
                logger.debug(
                    "apiKeys.list failed (%s), returning full tool list",
                    e,
                )
                return set()

            for key_data in keys:
                if key_data.get("last4") == last4:
                    key_scope = key_data.get("scope")
                    if not found:
                        scopes = key_scope
                        found = True
                    elif key_scope is None:
                        # Full-access key wins.
                        scopes = None
                    elif scopes is not None:
                        # last4 collision → union.
                        scopes = list(set(scopes) | set(key_scope))

            if len(keys) < limit:
                break
            offset += limit

        if not found:
            logger.debug(
                "API key last4=%s not found in "
                "apiKeys.list, returning full tool list",
                last4,
            )
            return set()

        return blocked_tools_for_scopes(scopes)

    except Exception as exc:
        logger.debug(
            "Dynamic tool list: scope check failed (%s),"
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
    tools blocked by the API key's scopes are hidden.
    Disabled by default; set ``OUTLINE_DYNAMIC_TOOL_LIST=true``
    to enable.

    Call this **after** ``register_all(mcp)``.
    """
    if not _is_enabled():
        return

    original_list_tools = mcp.list_tools

    async def filtered_list_tools() -> List[MCPTool]:
        tools: List[MCPTool] = await original_list_tools()

        try:
            api_key = _get_header_api_key() or os.getenv("OUTLINE_API_KEY")
            api_url = os.getenv("OUTLINE_API_URL")

            blocked = await get_blocked_tools(api_key, api_url)

            if blocked:
                return [t for t in tools if t.name not in blocked]
        except Exception as exc:
            logger.debug(
                "Dynamic tool filtering failed (%s), returning full tool list",
                exc,
            )

        return tools

    # Re-register with the lowlevel server so the protocol
    # handler calls our filtered function instead of the
    # original captured reference.
    mcp._mcp_server.list_tools()(filtered_list_tools)
