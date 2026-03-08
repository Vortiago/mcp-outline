"""Filtering logic for dynamic tool list via API key scopes."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Optional

from mcp.types import Tool as MCPTool

from mcp_outline.features.documents.common import (
    _get_header_api_key,
)
from mcp_outline.features.dynamic_tools.scope_matching import (
    blocked_tools_for_scopes,
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
    role_blocked_map: dict[str, frozenset[str]],
) -> set[str]:
    """Block tools the user's Outline role cannot access.

    Calls ``auth.info`` and looks up the role in
    *role_blocked_map* (built from ``min_role`` metadata).
    """
    try:
        data = await client.get_auth_info()
        role = data.get("user", {}).get("role")
        if role in role_blocked_map:
            return set(role_blocked_map[role])
        if role is not None:
            logger.warning(
                "Dynamic tool list: auth.info returned "
                "unknown role '%s'. Role-based filtering "
                "has been skipped for this request.",
                role,
            )
    except OutlineError as exc:
        if exc.status_code == 401:
            logger.warning(
                "Dynamic tool list: auth.info returned "
                "401 (authentication_required). The API "
                "key may be invalid, expired, or revoked. "
                "Role-based filtering has been skipped "
                "for this request.",
            )
        elif exc.status_code == 403:
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


async def _get_scope_blocked_tools(
    client: OutlineClient,
    api_key: str,
    tool_endpoint_map: dict[str, str],
) -> tuple[set[str], bool]:
    """Block tools the API key's scopes don't grant access to.

    Calls ``apiKeys.list``, finds the key by its last 4 characters,
    and checks each tool's endpoint against the scopes.

    Returns a tuple of ``(blocked_tools, block_all)``.
    *block_all* is ``True`` when a 401 indicates the key is
    invalid — the caller should hide every tool.
    """
    try:
        # Extract last-4 suffix for key matching (Outline
        # returns ``last4`` on each API key object).
        last4 = api_key[-4:]

        scopes: Optional[list[str]] = None
        found = False
        offset = 0
        limit = 100
        while True:
            try:
                keys = await client.list_api_keys(limit=limit, offset=offset)
            except OutlineError as e:
                if e.status_code == 401:
                    logger.warning(
                        "Dynamic tool list: apiKeys.list "
                        "returned 401 "
                        "(authentication_required). The key "
                        "may be invalid, expired, or "
                        "revoked. All tools have been "
                        "hidden. Verify the key in Outline "
                        "Settings → API Keys.",
                    )
                    return set(tool_endpoint_map.keys()), True
                if e.status_code == 403:
                    logger.warning(
                        "Dynamic tool list: apiKeys.list "
                        "returned 403 "
                        "(authorization_error). The key "
                        "likely lacks the 'apiKeys.list' "
                        "scope required for tool "
                        "filtering. Add 'apiKeys.list' "
                        "to the key's scope array in "
                        "Outline Settings → API Keys. "
                        "Scope-based filtering has been "
                        "skipped for this request.",
                    )
                else:
                    logger.debug(
                        "apiKeys.list failed (%s), skipping scope check",
                        e,
                    )
                return set(), False

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
                "API key not found in apiKeys.list, skipping scope check",
            )
            return set(), False

        return (
            blocked_tools_for_scopes(scopes, tool_endpoint_map),
            False,
        )

    except Exception as exc:
        logger.debug(
            "Dynamic tool list: scope check failed (%s), skipping scope check",
            exc,
        )
        return set(), False


async def get_blocked_tools(
    api_key: Optional[str],
    api_url: Optional[str],
    tool_endpoint_map: dict[str, str],
    role_blocked_map: dict[str, frozenset[str]],
) -> set[str]:
    """Return tool names *api_key* cannot access.

    Performs two independent checks **concurrently** (results
    unioned):

    1. ``auth.info`` — blocks tools by user role via ``min_role``
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
    role_blocked = await _get_role_blocked_tools(client, role_blocked_map)

    # Check 2: scope-based blocking (apiKeys.list)
    scope_blocked, block_all = await _get_scope_blocked_tools(
        client, api_key, tool_endpoint_map
    )

    if block_all:
        # 401 from apiKeys.list — key is invalid, hide everything.
        return scope_blocked | role_blocked

    return role_blocked | scope_blocked


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------


def install_dynamic_tool_list(
    mcp: "FastMCP",
    tool_endpoint_map: dict[str, str],
    role_blocked_map: dict[str, frozenset[str]],
) -> None:
    """Install per-request tool filtering on *mcp*.

    Re-registers the lowlevel ``tools/list`` handler so that
    tools blocked by the API key's scopes or user role are
    hidden.  Disabled by default; set
    ``OUTLINE_DYNAMIC_TOOL_LIST=true`` to enable.

    Call this **after** ``register_all(mcp)``.
    """
    if not _is_enabled():
        return

    original_list_tools = mcp.list_tools

    async def filtered_list_tools() -> list[MCPTool]:
        tools: list[MCPTool] = await original_list_tools()

        try:
            api_key = _get_header_api_key() or os.getenv("OUTLINE_API_KEY")
            api_url = os.getenv("OUTLINE_API_URL")

            blocked = await get_blocked_tools(
                api_key,
                api_url,
                tool_endpoint_map,
                role_blocked_map,
            )

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
