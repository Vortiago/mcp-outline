# MCP Resources for Outline
"""
Resources provide direct content access via URIs without requiring tool calls.

URI Scheme:
- outline://collection/{id} - Collection metadata and properties
- outline://document/{id} - Full document content (markdown)
- outline://collection/{id}/tree - Hierarchical document tree
- outline://collection/{id}/documents - List of documents in collection
- outline://document/{id}/backlinks - Documents linking to this document
"""

from mcp_outline.features.resources import (
    collection_resources,
    document_resources,
)


def register(mcp):
    """
    Register all resource handlers with the MCP server.

    Args:
        mcp: The FastMCP server instance
    """
    collection_resources.register_resources(mcp)
    document_resources.register_resources(mcp)
