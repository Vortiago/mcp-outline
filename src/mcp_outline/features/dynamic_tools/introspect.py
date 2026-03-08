"""Build tool metadata maps by introspecting registered tools.

After ``register_all(mcp)`` is called, the builder functions in
this module derive ``TOOL_ENDPOINT_MAP`` and role-blocked maps
from the ``meta`` already present on each registered tool — no
separate hand-maintained files needed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

# Outline workspace roles ordered by privilege level.
_ROLE_LEVELS: dict[str, int] = {
    "viewer": 0,
    "member": 1,
    "admin": 2,
}


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


def build_role_blocked_map(
    mcp: "FastMCP",
) -> dict[str, frozenset[str]]:
    """Return ``{role: blocked_tool_names}`` from ``min_role``.

    Each tool carries ``meta={"min_role": "viewer"|"member"|"admin"}``
    declaring the minimum Outline role required.  For each role in
    the hierarchy, tools whose ``min_role`` exceeds that role are
    added to its blocked set.

    Verified against Outline route handlers
    (``collections.ts``, ``documents.ts``) and
    ``AuthenticationHelper.ts``.
    """
    blocked: dict[str, set[str]] = {r: set() for r in _ROLE_LEVELS}
    for name, tool in mcp._tool_manager._tools.items():
        min_role = (tool.meta or {}).get("min_role")
        if min_role is None:
            continue
        if min_role not in _ROLE_LEVELS:
            raise ValueError(
                f"Tool '{name}' has invalid min_role "
                f"'{min_role}'; expected one of "
                f"{set(_ROLE_LEVELS)}"
            )
        min_level = _ROLE_LEVELS[min_role]
        for role, level in _ROLE_LEVELS.items():
            if level < min_level:
                blocked[role].add(name)
    return {r: frozenset(s) for r, s in blocked.items()}
