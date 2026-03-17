"""Dynamic tool list filtering based on Outline API key scopes.

Filters MCP ``tools/list`` per-request using ``apiKeys.list`` scope
introspection.  Off by default; enable with
``OUTLINE_DYNAMIC_TOOL_LIST=true``.  Fail-open: if introspection
fails, the full tool list is returned.
"""

from mcp_outline.features.dynamic_tools.filtering import (
    get_blocked_tools,
    install_dynamic_tool_list,
)
from mcp_outline.features.dynamic_tools.introspect import (
    build_tool_endpoint_map,
)

__all__ = [
    "build_tool_endpoint_map",
    "get_blocked_tools",
    "install_dynamic_tool_list",
]
