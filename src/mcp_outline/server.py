"""
Outline MCP Server

A simple MCP server that provides document outline capabilities.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from mcp_outline.features import register_all
from mcp_outline.features.dynamic_tools import (
    build_role_blocked_map,
    build_tool_endpoint_map,
    install_dynamic_tool_list,
)
from mcp_outline.patches import patch_for_copilot_cli

# Apply compatibility patches for MCP clients
# This must happen before creating the FastMCP instance
patch_for_copilot_cli()

# Strip empty env vars so that dotenv can fill them from the
# config file.  MCP clients (e.g. Claude Code) may pass
# empty strings for unset variables via their env block.
for _key in list(os.environ):
    if _key.startswith("OUTLINE_") and os.environ[_key] == "":
        del os.environ[_key]

# Load configuration from dotenv files.
# Existing environment variables always take priority (override=False).
# Project-level file is loaded first so it wins over user-level.
_project_env = Path.cwd() / ".mcp-outline.env"
load_dotenv(_project_env)
_config_path = Path.home() / ".config" / "mcp-outline" / ".env"
load_dotenv(_config_path)

# Get host from environment variable, default to 127.0.0.1
# Use 0.0.0.0 for Docker containers to allow external connections
host = os.getenv("MCP_HOST", "127.0.0.1")

# Get port from environment variable, default to 3000
port = int(os.getenv("MCP_PORT", "3000"))

# Server instructions — injected into the LLM's system prompt
# by MCP clients. Keep under 2KB (Claude Code truncates at 2KB).
_INSTRUCTIONS = (
    "Manages documents in Outline, a wiki and knowledge "
    "base. Use for searching, reading, navigating, editing,"
    " and organizing documents and collections.\n\n"
    "Finding content: search_documents or "
    "get_document_id_from_title to get document IDs, "
    "list_collections to discover collections.\n\n"
    "Large documents: start with get_document_toc to see "
    "heading structure, then read_document_section to read "
    "by heading, or read_document with offset/limit for "
    "line ranges.\n\n"
    "Editing: use edit_document for targeted changes. "
    "Batch all changes into one call when possible. "
    "Use update_document only for full content replacement,"
    " title changes, or appending.\n\n"
    "Large rewrites: call edit_document with save=False "
    "to stage changes across multiple calls, then "
    "save_document once at the end.\n\n"
    "Markdown: Outline uses standard markdown. For Mermaid "
    "diagrams use mermaidjs (not mermaid) as the code "
    "fence language."
)

# Create a FastMCP server instance with a name and port configuration
mcp = FastMCP(
    "Document Outline",
    host=host,
    port=port,
    instructions=_INSTRUCTIONS,
)

# Register all features
register_all(mcp)

# Build tool metadata maps by introspecting registered tools
tool_endpoint_map = build_tool_endpoint_map(mcp)
role_blocked_map = build_role_blocked_map(mcp)

# Install per-request dynamic tool filtering (off by default)
install_dynamic_tool_list(mcp, tool_endpoint_map, role_blocked_map)


def main() -> None:
    # Suppress KeyboardInterrupt traceback for clean exit
    sys.excepthook = lambda exc_type, exc_value, exc_tb: (
        sys.exit(0)
        if exc_type is KeyboardInterrupt
        else sys.__excepthook__(exc_type, exc_value, exc_tb)
    )

    # Get transport mode from environment variable,
    # default to stdio for backward compatibility
    transport_str = os.getenv("MCP_TRANSPORT", "stdio").lower()

    # Validate transport mode and ensure type safety
    transport_mode: Literal["stdio", "sse", "streamable-http"]
    if transport_str in ("stdio", "sse", "streamable-http"):
        transport_mode = transport_str  # type: ignore
    else:
        logging.error(
            f"Invalid transport mode: {transport_str}. "
            f"Must be one of: stdio, sse, streamable-http"
        )
        transport_mode = "stdio"

    # Configure logging based on transport mode
    if transport_mode == "stdio":
        # In stdio mode, suppress all logging to prevent interference
        # with MCP protocol. MCP uses stdio for JSON-RPC communication,
        # so any logs to stdout/stderr break the protocol.
        logging.basicConfig(
            level=logging.CRITICAL,  # Only show critical errors
            format="%(message)s",
            force=True,  # Override any existing logging configuration
        )
        # Also suppress httpx logging (HTTP request logs)
        logging.getLogger("httpx").setLevel(logging.CRITICAL)
        # Suppress MCP SDK's internal logging
        logging.getLogger("mcp").setLevel(logging.CRITICAL)
    else:
        # In SSE/HTTP modes, enable info logging for debugging
        logging.basicConfig(
            level=logging.INFO,
            format="[%(asctime)s] %(levelname)-8s %(message)s",
            datefmt="%m/%d/%y %H:%M:%S",
            force=True,  # Override any existing logging configuration
        )
        logging.getLogger("httpx").setLevel(logging.INFO)
        logging.info(
            f"Starting MCP Outline server with "
            f"transport mode: {transport_mode}"
        )
        if not os.getenv("OUTLINE_API_KEY"):
            logging.info(
                "No OUTLINE_API_KEY set. "
                "Per-request authentication only "
                "(x-outline-api-key header)."
            )

    # Start the server with the specified transport
    mcp.run(transport=transport_mode)


if __name__ == "__main__":
    main()
