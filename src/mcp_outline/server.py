"""
Outline MCP Server

A simple MCP server that provides document outline capabilities.
"""

import logging
import os
from typing import Literal

from mcp.server.fastmcp import FastMCP

from mcp_outline.features import register_all

# Create a FastMCP server instance with a name and port configuration
mcp = FastMCP("Document Outline", port=3001)

# Register all features
register_all(mcp)


def main() -> None:
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

    logging.info(
        f"Starting MCP Outline server with transport mode: {transport_mode}"
    )

    # Start the server with the specified transport
    mcp.run(transport=transport_mode)


if __name__ == "__main__":
    main()
