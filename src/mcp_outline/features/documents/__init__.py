# Document management features for MCP Outline
import os
from typing import Optional

from mcp_outline.features.documents import (
    ai_tools,
    batch_operations,
    collection_tools,
    document_collaboration,
    document_content,
    document_lifecycle,
    document_organization,
    document_reading,
    document_search,
)


def register(
    mcp, api_key: Optional[str] = None, api_url: Optional[str] = None
):
    """
    Register document management features with the MCP server.

    Args:
        mcp: The FastMCP server instance
        api_key: Optional API key for Outline
        api_url: Optional API URL for Outline
    """
    # Always register read-only tools
    document_search.register_tools(mcp)
    document_reading.register_tools(mcp)
    document_collaboration.register_tools(mcp)
    collection_tools.register_tools(mcp)

    # Conditionally register AI tools (can be disabled for local instances)
    if os.getenv("OUTLINE_DISABLE_AI_TOOLS", "").lower() not in (
        "true",
        "1",
        "yes",
    ):
        ai_tools.register_tools(mcp)

    # Conditionally register write tools (disabled in read-only mode)
    if os.getenv("OUTLINE_READ_ONLY", "").lower() not in (
        "true",
        "1",
        "yes",
    ):
        document_content.register_tools(mcp)
        document_lifecycle.register_tools(mcp)
        document_organization.register_tools(mcp)
        batch_operations.register_tools(mcp)
