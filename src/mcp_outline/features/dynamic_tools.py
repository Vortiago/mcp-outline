"""Dynamic tool list filtering based on Outline user permissions.

When enabled, the MCP ``tools/list`` response is filtered per-request
based on the authenticated user's Outline role **and** API-key scopes.
Viewer-role users (or keys scoped to read-only endpoints) only see
read-only tools; members and admins see the full set.

The feature is **on by default**.  Disable it by setting
``OUTLINE_DYNAMIC_TOOL_LIST`` to ``false``, ``0``, or ``no``
(case-insensitive).

This module is intentionally fail-open: if the ``auth.info`` call
fails for any reason the full tool list is returned.  Outline's own
API will still enforce permissions on individual tool calls.

Outline references
------------------
- User roles (admin / member / viewer / guest):
  https://docs.getoutline.com/s/guide/doc/users-roles-cwCxXP8R3V
- ``UserRole`` enum in source (``shared/types.ts``):
  https://github.com/outline/outline/blob/main/shared/types.ts
- API key scopes (space-separated endpoint prefixes, added in v0.82):
  https://github.com/outline/outline/issues/8186
  https://github.com/outline/outline/pull/8297
- Full API endpoint list (OpenAPI spec — use to update
  ``_WRITE_ENDPOINT_PREFIXES`` when Outline adds new write
  endpoints):
  https://github.com/outline/openapi/blob/main/spec3.yml
- Interactive API reference:
  https://www.getoutline.com/developers
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from mcp.types import Tool as MCPTool

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

from mcp_outline.features.documents.common import (
    _get_header_api_key,
)
from mcp_outline.utils.outline_client import (
    OutlineClient,
    OutlineError,
)

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Write-tool registry
# ------------------------------------------------------------------
# Every tool whose ``readOnlyHint`` annotation is ``False``.
# A cross-check unit test verifies this set stays in sync.
WRITE_TOOL_NAMES: frozenset = frozenset(
    {
        # document_content
        "create_document",
        "update_document",
        "add_comment",
        # document_lifecycle
        "archive_document",
        "unarchive_document",
        "delete_document",
        "restore_document",
        # document_organization
        "move_document",
        # collection_tools
        "create_collection",
        "update_collection",
        "delete_collection",
        # batch_operations
        "batch_archive_documents",
        "batch_move_documents",
        "batch_delete_documents",
        "batch_update_documents",
        "batch_create_documents",
    }
)

# Outline API endpoints that require write access.  Used to detect
# whether an API key's scopes allow write operations.
# To update: check the OpenAPI spec for new write endpoints:
#   https://github.com/outline/openapi/blob/main/spec3.yml
_WRITE_ENDPOINT_PREFIXES = (
    "documents.create",
    "documents.update",
    "documents.move",
    "documents.archive",
    "documents.unarchive",
    "documents.delete",
    "documents.restore",
    "collections.create",
    "collections.update",
    "collections.delete",
    "comments.create",
)


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


def _has_write_scope(policies: List[Dict[str, Any]]) -> bool:
    """Inspect *policies* from ``auth.info`` for write abilities.

    Outline returns a ``policies`` list alongside the ``data``
    object.  Each entry has an ``abilities`` dict describing what
    the authenticated token can do.  We look for any document or
    collection write ability.

    The ability keys checked below come from Outline's policy
    layer.  See the ``server/policies/`` directory in the Outline
    repo for the authoritative list of abilities per resource:
    https://github.com/outline/outline/tree/main/server/policies

    Returns ``True`` when write access is detected **or** when the
    policies structure is missing / unrecognised (fail-open).
    """
    if not policies:
        return True  # no info → assume full access

    for policy in policies:
        abilities = policy.get("abilities", {})
        # Look for any write-related ability
        for key in (
            "createDocument",
            "create",
            "update",
            "archive",
            "delete",
        ):
            if abilities.get(key) is True:
                return True

    # If we got policies but none had write abilities,
    # the token is read-only.
    return False


def _has_write_endpoint_scope(
    scopes: Optional[str],
) -> bool:
    """Check if API-key *scopes* include any write endpoint.

    Outline API-key scopes are a space-separated list of endpoint
    prefixes (e.g. ``"documents.list documents.info"``).  An empty
    or ``None`` scope means the key has full access.

    Scope matching uses dot-boundary prefixes, mirroring Outline's
    own middleware.  See the implementation PR for details:
    https://github.com/outline/outline/pull/8297

    Returns ``True`` if the key can reach at least one write
    endpoint, or if scopes are absent (unscoped = full access).
    """
    if not scopes:
        return True  # unscoped key → full access

    scope_list = scopes.strip().split()
    for scope in scope_list:
        # Global write scope
        if scope in ("write", "*"):
            return True
        for prefix in _WRITE_ENDPOINT_PREFIXES:
            # Exact match or dot-boundary prefix in either direction.
            # e.g. scope "documents" matches prefix "documents.create"
            #      scope "documents.create" matches prefix "documents.create"
            # but  scope "doc" does NOT match "documents.create"
            if scope == prefix:
                return True
            if prefix.startswith(scope + "."):
                return True
            if scope.startswith(prefix + "."):
                return True
    return False


async def _get_user_permissions(
    api_key: Optional[str],
    api_url: Optional[str],
) -> Dict[str, Any]:
    """Determine the effective permissions for *api_key*.

    Calls ``auth.info`` and inspects both the user role and the
    response policies to account for API-key scopes.

    Roles are defined in ``shared/types.ts`` (``UserRole`` enum):
    https://github.com/outline/outline/blob/main/shared/types.ts
    Currently: admin, member, viewer, guest.

    Returns a dict with:
    - ``role``: the Outline user role (``str`` or ``None``)
    - ``can_write``: whether the token allows write operations
    """
    if not api_key:
        return {"role": None, "can_write": True}

    try:
        client = OutlineClient(api_key=api_key, api_url=api_url)
        response = await client.auth_info_full()

        data = response.get("data", {})
        user = data.get("user", {})
        role = user.get("role")

        # Check policies for write abilities
        policies = response.get("policies", [])
        can_write_policy = _has_write_scope(policies)

        # Check API key scopes if available
        api_key_data = data.get("apiKey", {})
        scopes = api_key_data.get("scope") if api_key_data else None
        can_write_scope = _has_write_endpoint_scope(scopes)

        # Role-based inference as fallback
        if role == "viewer":
            can_write_role = False
        else:
            can_write_role = True

        # The most restrictive wins
        can_write = can_write_role and can_write_policy and can_write_scope

        return {"role": role, "can_write": can_write}

    except (OutlineError, Exception) as exc:
        logger.debug(
            "Dynamic tool list: auth.info failed (%s), "
            "returning full tool list",
            exc,
        )
        return {"role": None, "can_write": True}


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------


def install_dynamic_tool_list(mcp: FastMCP) -> None:
    """Install per-request tool filtering on *mcp*.

    Replaces ``mcp.list_tools`` with a wrapper that filters write
    tools for viewer-role users or read-only-scoped API keys.
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

        perms = await _get_user_permissions(api_key, api_url)

        if not perms["can_write"]:
            return [t for t in tools if t.name not in WRITE_TOOL_NAMES]

        return tools

    mcp.list_tools = filtered_list_tools  # type: ignore[method-assign]
