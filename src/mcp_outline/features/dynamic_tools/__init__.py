"""Dynamic tool list filtering based on Outline API key scopes.

Filters MCP ``tools/list`` per-request using ``apiKeys.list`` scope
introspection and ``auth.info`` role checking.  Off by default;
enable with ``OUTLINE_DYNAMIC_TOOL_LIST=true``.  Fail-open: if
introspection fails, the full tool list is returned.
"""

from mcp_outline.features.dynamic_tools.filtering import (
    get_blocked_tools,
    install_dynamic_tool_list,
)
from mcp_outline.features.dynamic_tools.introspect import (
    ROLE_LEVELS,
    build_role_blocked_map,
    build_tool_endpoint_map,
)

__all__ = [
    "ROLE_LEVELS",
    "build_role_blocked_map",
    "build_tool_endpoint_map",
    "get_blocked_tools",
    "install_dynamic_tool_list",
]
