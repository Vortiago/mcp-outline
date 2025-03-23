"""
Collection management tools for the MCP Outline server.

This module provides MCP tools for managing collections.
"""
from typing import Optional, Dict, Any, List

from mcp_outline.features.documents.common import get_outline_client, OutlineClientError
from mcp_outline.features.documents.document_search import _format_collections

def register_tools(mcp) -> None:
    """
    Register collection management tools with the MCP server.
    
    Args:
        mcp: The FastMCP server instance
    """
    # Collection tools can be added here as needed, e.g.:
    # - create_collection
    # - update_collection
    # - delete_collection
    # - export_collection
    pass
