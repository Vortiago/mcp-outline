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
from mcp_outline.features.dynamic_tools.write_tool_names import (
    WRITE_TOOL_NAMES,
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


async def _get_role_blocked_tools(
    client: OutlineClient,
) -> Set[str]:
    """Block write tools when the user's role is ``viewer``."""
    try:
        data = await client.get_auth_info()
        role = data.get("user", {}).get("role")
        if role == "viewer":
            return set(WRITE_TOOL_NAMES)
    except OutlineError as exc:
        if exc.status_code == 403:
            logger.warning(
                "Dynamic tool list: auth.info returned "
                "403 (authorization_error). The API key "
                "likely lacks the 'auth.info' scope "
                "required for role-based filtering. "
                "Add 'auth.info' to the key's scope "
                "array in Outline Settings → API Keys. "
                "Role-based filtering has been skipped "
                "for this request.",
            )
        else:
            logger.debug(
                "auth.info check failed (%s), skipping role check",
                exc,
            )
    except Exception as exc:
        logger.debug(
            "auth.info check failed (%s), skipping role check",
            exc,
        )
    return set()


async def get_blocked_tools(
    api_key: Optional[str],
    api_url: Optional[str],
) -> Set[str]:
    """Return tool names *api_key* cannot access.

    Performs two independent checks (results unioned):

    1. ``auth.info`` — blocks write tools for viewer role
    2. ``apiKeys.list`` — blocks tools excluded by key scopes

    Each check fails open independently (except 401 on
    ``apiKeys.list`` which blocks all tools).
    """
    if not api_key:
        return set()

    try:
        client = OutlineClient(api_key=api_key, api_url=api_url)
    except Exception as exc:
        logger.debug(
            "Dynamic tool list: client init failed (%s),"
            " returning full tool list",
            exc,
        )
        return set()

    # Check 1: role-based blocking (auth.info)
    blocked = await _get_role_blocked_tools(client)

    # Check 2: scope-based blocking (apiKeys.list)
    try:
        last4 = api_key[-4:]
        scopes: Optional[List[str]] = None
        found = False
        offset = 0
        limit = 100
        while True:
            try:
                keys = await client.list_api_keys(limit=limit, offset=offset)
            except OutlineError as e:
                if e.status_code == 401:
                    logger.warning(
                        "Dynamic tool list: API key ending "
                        "in '…%s' returned 401 "
                        "(authentication_required). The key "
                        "may be invalid, expired, or "
                        "revoked. All tools have been "
                        "hidden. Verify the key in Outline "
                        "Settings → API Keys.",
                        api_key[-4:],
                    )
                    return set(TOOL_ENDPOINT_MAP.keys())
                if e.status_code == 403:
                    logger.warning(
                        "Dynamic tool list: API key ending "
                        "in '…%s' returned 403 "
                        "(authorization_error). The key "
                        "likely lacks the 'apiKeys.list' "
                        "scope required for tool "
                        "filtering. Add 'apiKeys.list' "
                        "to the key's scope array in "
                        "Outline Settings → API Keys. "
                        "Scope-based filtering has been "
                        "skipped for this request.",
                        api_key[-4:],
                    )
                else:
                    logger.debug(
                        "apiKeys.list failed (%s), skipping scope check",
                        e,
                    )
                return blocked

            for key_data in keys:
                if key_data.get("last4") == last4:
                    key_scope = key_data.get("scope")
                    if not found:
                        scopes = key_scope
                        found = True
                    elif key_scope is None:
                        scopes = None
                    elif scopes is not None:
                        scopes = list(set(scopes) | set(key_scope))

            if len(keys) < limit:
                break
            offset += limit

        if not found:
            logger.debug(
                "API key last4=%s not found in "
                "apiKeys.list, skipping scope check",
                last4,
            )
            return blocked

        blocked |= blocked_tools_for_scopes(scopes)

    except Exception as exc:
        logger.debug(
            "Dynamic tool list: scope check failed (%s), skipping scope check",
            exc,
        )

    return blocked


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
