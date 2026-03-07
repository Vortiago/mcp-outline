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
    build_tool_endpoint_map,
    build_write_tool_names,
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

# Create a FastMCP server instance with a name and port configuration
mcp = FastMCP("Document Outline", host=host, port=port)

# Register all features
register_all(mcp)

# Build tool metadata maps by introspecting registered tools
tool_endpoint_map = build_tool_endpoint_map(mcp)
write_tool_names = build_write_tool_names(mcp)

# Install per-request dynamic tool filtering (off by default)
install_dynamic_tool_list(mcp, tool_endpoint_map, write_tool_names)


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
