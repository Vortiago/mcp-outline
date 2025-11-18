"""
Patches for MCP SDK compatibility.

This module contains runtime patches for third-party libraries to handle
edge cases and compatibility issues with different MCP clients.
"""

from mcp_outline.patches.copilot_cli import patch_for_copilot_cli

__all__ = ["patch_for_copilot_cli"]
