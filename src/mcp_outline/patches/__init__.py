"""Compatibility fixes for MCP clients that break the protocol."""

from mcp_outline.patches.copilot_cli import coerce_empty_tool_arguments

__all__ = ["coerce_empty_tool_arguments"]
