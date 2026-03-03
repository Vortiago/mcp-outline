"""Dynamic tool list filtering based on Outline API key scopes.

When enabled, the MCP ``tools/list`` response is filtered per-request
by calling the Outline ``apiKeys.list`` endpoint to retrieve the
authenticated key's scopes, then applying Outline's scope matching
algorithm locally to determine which tools to show.

The API key must include the ``apiKeys.list`` scope for
introspection to work.  Without it the feature degrades
gracefully (shows all tools).

The feature is **off by default**.  Enable it by setting
``OUTLINE_DYNAMIC_TOOL_LIST`` to ``true``, ``1``, or ``yes``
(case-insensitive).

This module is intentionally fail-open: if scope introspection
fails for any reason the full tool list is returned.  Outline's
own API will still enforce permissions on individual tool calls.

Outline references
------------------
- User roles (admin / member / viewer / guest):
  https://docs.getoutline.com/s/guide/doc/users-roles-cwCxXP8R3V
- ``UserRole`` enum in source (``shared/types.ts``):
  https://github.com/outline/outline/blob/main/shared/types.ts
- API key scopes (added in v0.82):
  https://github.com/outline/outline/issues/8186
  https://github.com/outline/outline/pull/8297
- Full API endpoint list (OpenAPI spec):
  https://github.com/outline/openapi/blob/main/spec3.yml
- Interactive API reference:
  https://www.getoutline.com/developers
"""

from mcp_outline.features.dynamic_tools.filtering import (
    get_blocked_tools,
    install_dynamic_tool_list,
)
from mcp_outline.features.dynamic_tools.tool_endpoint_map import (
    TOOL_ENDPOINT_MAP,
)
from mcp_outline.features.dynamic_tools.write_tool_names import (
    WRITE_TOOL_NAMES,
)

__all__ = [
    "TOOL_ENDPOINT_MAP",
    "WRITE_TOOL_NAMES",
    "get_blocked_tools",
    "install_dynamic_tool_list",
]
