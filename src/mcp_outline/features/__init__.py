# Document Outline MCP features package
from mcp_outline.features import documents


def register_all(mcp):
    """
    Register all features with the MCP server.
    
    Args:
        mcp: The FastMCP server instance
    """
    documents.register(mcp)
