"""Local implementation of Outline's scope matching algorithm.

Mirrors ``AuthenticationHelper.canAccess`` from the Outline
TypeScript codebase.  Given a list of scope strings (as stored
on an API key) and an endpoint path, determines whether the
key grants access.

References
----------
- AuthenticationHelper.canAccess:
  https://github.com/outline/outline/blob/main/shared/
  helpers/AuthenticationHelper.ts
- Scope enum (Read / Write / Create):
  https://github.com/outline/outline/blob/main/shared/types.ts
"""

from __future__ import annotations

from typing import Optional

from mcp_outline.features.dynamic_tools.tool_endpoint_map import (
    TOOL_ENDPOINT_MAP,
)

# ------------------------------------------------------------------
# Outline method-to-scope mapping
# ------------------------------------------------------------------

_METHOD_TO_SCOPE: dict[str, str] = {
    "create": "create",
    "config": "read",
    "list": "read",
    "info": "read",
    "search": "read",
    "documents": "read",
    "drafts": "read",
    "viewed": "read",
    "export": "read",
}


def _get_method_scope(method: str) -> str:
    """Return the scope level for a given API method.

    Methods not in the mapping default to ``"write"``.
    """
    return _METHOD_TO_SCOPE.get(method, "write")


# ------------------------------------------------------------------
# Core scope check
# ------------------------------------------------------------------


def is_endpoint_accessible(
    endpoint: str,
    scopes: list[str],
) -> bool:
    """Check whether *scopes* grant access to *endpoint*.

    Implements the same logic as Outline's
    ``AuthenticationHelper.canAccess(path, scopes)``.

    Args:
        endpoint: Outline API endpoint, e.g.
            ``"documents.info"`` or ``"collections.list"``.
        scopes: Scope strings as stored on the API key.

    Returns:
        ``True`` if at least one scope grants access.
    """
    parts = endpoint.split(".", 1)
    if len(parts) != 2:
        return True  # unparseable → fail-open

    namespace, method = parts
    method_scope = _get_method_scope(method)

    for scope in scopes:
        if scope.startswith("/api/"):
            # Route scope: /api/namespace.method
            scope_path = scope[5:]  # strip "/api/"
            scope_parts = scope_path.split(".", 1)
            if len(scope_parts) != 2:
                continue
            scope_ns, scope_method = scope_parts
            if (namespace == scope_ns or scope_ns == "*") and (
                method == scope_method or scope_method == "*"
            ):
                return True

        elif ":" in scope:
            # Namespaced scope: namespace:level
            scope_ns, scope_level = scope.split(":", 1)
            if (namespace == scope_ns or scope_ns == "*") and (
                scope_level == "write" or method_scope == scope_level
            ):
                return True

        # Global scopes (no ":" or "/api/") are broken in
        # Outline v1.5.0 due to normalisation prepending
        # "/api/" — they match nothing.  Skip silently.

    return False


# ------------------------------------------------------------------
# Bulk helpers
# ------------------------------------------------------------------


def blocked_tools_for_scopes(
    scopes: Optional[list[str]],
) -> set[str]:
    """Return tool names the key *cannot* access.

    Args:
        scopes: The API key's scope array, or ``None``
            for full access (no restrictions).

    Returns:
        Set of blocked tool names.
        Empty set when *scopes* is ``None``.
    """
    if scopes is None or len(scopes) == 0:
        return set()

    blocked: set[str] = set()
    for tool_name, endpoint in TOOL_ENDPOINT_MAP.items():
        if not is_endpoint_accessible(endpoint, scopes):
            blocked.add(tool_name)
    return blocked
