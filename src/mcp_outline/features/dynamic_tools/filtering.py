"""Filtering logic for dynamic tool list via API key scopes."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Dict, List, Optional, Set

from mcp.types import Tool as MCPTool

from mcp_outline.features.documents.common import (
    _get_header_api_key,
)
from mcp_outline.features.dynamic_tools.scope_matching import (
    get_blocked_tools as get_blocked_tools_from_scopes,
)
from mcp_outline.features.dynamic_tools.tool_endpoint_map import (
    TOOL_ENDPOINT_MAP,
)
from mcp_outline.utils.outline_client import OutlineClient, OutlineError

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Per-key cache: API key scopes are immutable (revoke + recreate
# to change), so results are cached for the process lifetime.
_blocked_cache: Dict[str, Set[str]] = {}


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
    """Determine which tools *api_key* cannot access.

    Calls ``apiKeys.list`` to retrieve the key's stored scopes,
    then applies Outline's scope matching algorithm locally to
    determine which tool endpoints are accessible.

    The current key is matched by comparing its last 4 characters
    against the ``last4`` field in the response.  If multiple keys
    share the same ``last4`` (collision), all their scopes are
    combined (union).  If any matching key has ``null`` scope
    (full access), the result is full access.

    Results are cached per API key for the process lifetime
    since Outline key scopes are immutable.

    Error handling:
    - 401 from ``apiKeys.list`` → invalid key → block ALL tools.
    - 403 or other HTTP errors → fail-open (empty blocked set).
    - Key not found in list → fail-open.

    The API key must include ``apiKeys.list`` in its scope for
    introspection to work.  Without it the feature degrades
    gracefully (shows all tools).
    """
    if not api_key:
        return set()

    if api_key in _blocked_cache:
        return _blocked_cache[api_key]

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
                err_str = str(e)
                if err_str.startswith("HTTP 401"):
                    # Key is completely invalid → block all.
                    blocked = set(TOOL_ENDPOINT_MAP.keys())
                    _blocked_cache[api_key] = blocked
                    return blocked
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

        blocked = get_blocked_tools_from_scopes(scopes)
        _blocked_cache[api_key] = blocked
        return blocked

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
