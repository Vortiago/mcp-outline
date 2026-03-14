"""Filtering logic for dynamic tool list via API key scopes."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Optional

import anyio
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


def _log_api_error(
    endpoint: str,
    exc: OutlineError,
    check_name: str,
) -> None:
    """Log a structured warning/debug for API errors."""
    if exc.status_code == 401:
        logger.warning(
            "Dynamic tool list: %s returned 401 "
            "(authentication_required). The API key "
            "may be invalid, expired, or revoked. "
            "%s has been skipped for this request.",
            endpoint,
            check_name,
        )
    elif exc.status_code == 403:
        logger.warning(
            "Dynamic tool list: %s returned 403 "
            "(authorization_error). The API key "
            "likely lacks the '%s' scope. "
            "Add '%s' to the key's scope array "
            "in Outline Settings → API Keys. "
            "%s has been skipped for this request.",
            endpoint,
            endpoint,
            endpoint,
            check_name,
        )
    else:
        logger.debug(
            "%s check failed (%s), skipping %s",
            endpoint,
            type(exc).__name__,
            check_name.lower(),
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
        _log_api_error("auth.info", exc, "Role-based filtering")
    except Exception as exc:
        logger.debug(
            "auth.info check failed (%s), skipping role check",
            type(exc).__name__,
        )
    return set()


async def _get_scope_blocked_tools(
    client: OutlineClient,
    api_key: str,
    tool_endpoint_map: dict[str, str],
) -> set[str]:
    """Block tools the API key's scopes don't grant access to.

    Calls ``apiKeys.list``, finds the key by its last 4 characters,
    and checks each tool's endpoint against the scopes.

    On a 401 (invalid/expired key), returns all tool names so
    that every tool is hidden.
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
                        "(authentication_required). "
                        "All tools have been hidden. "
                        "Verify the key in Outline "
                        "Settings → API Keys.",
                    )
                    return set(tool_endpoint_map.keys())
                _log_api_error(
                    "apiKeys.list",
                    e,
                    "Scope-based filtering",
                )
                return set()

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
            logger.warning(
                "Dynamic tool list: API key not found in "
                "apiKeys.list. All tools have been hidden. "
                "Verify the key in Outline "
                "Settings → API Keys.",
            )
            return set(tool_endpoint_map.keys())

        return blocked_tools_for_scopes(scopes, tool_endpoint_map)

    except Exception as exc:
        logger.debug(
            "Dynamic tool list: scope check failed (%s), skipping scope check",
            type(exc).__name__,
        )
        return set()


async def get_blocked_tools(
    api_key: Optional[str],
    api_url: Optional[str],
    tool_endpoint_map: dict[str, str],
    role_blocked_map: dict[str, frozenset[str]],
) -> set[str]:
    """Return tool names *api_key* cannot access.

    Runs two independent checks concurrently (results unioned):

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
            type(exc).__name__,
        )
        return set()

    role_blocked: set[str] = set()
    scope_blocked: set[str] = set()

    async def _role_check() -> None:
        nonlocal role_blocked
        role_blocked = await _get_role_blocked_tools(client, role_blocked_map)

    async def _scope_check() -> None:
        nonlocal scope_blocked
        scope_blocked = await _get_scope_blocked_tools(
            client, api_key, tool_endpoint_map
        )

    async with anyio.create_task_group() as tg:
        tg.start_soon(_role_check)
        tg.start_soon(_scope_check)

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
                type(exc).__name__,
            )

        return tools

    # Re-register with the lowlevel server so the protocol
    # handler calls our filtered function instead of the
    # original captured reference.
    mcp._mcp_server.list_tools()(filtered_list_tools)
