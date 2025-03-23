# Document management features for MCP Outline
from typing import Optional
from mcp_outline.features.documents import document_search
from mcp_outline.features.documents import document_reading
from mcp_outline.features.documents import document_content
from mcp_outline.features.documents import document_organization
from mcp_outline.features.documents import document_lifecycle
from mcp_outline.features.documents import document_collaboration
from mcp_outline.features.documents import collection_tools
from mcp_outline.features.documents import ai_tools

def register(mcp, api_key: Optional[str] = None, api_url: Optional[str] = None):
    """
    Register document management features with the MCP server.
    
    Args:
        mcp: The FastMCP server instance
        api_key: Optional API key for Outline
        api_url: Optional API URL for Outline
    """
    # Register all the tools from each module
    document_search.register_tools(mcp)
    document_reading.register_tools(mcp)
    document_content.register_tools(mcp)
    document_organization.register_tools(mcp)
    document_lifecycle.register_tools(mcp)
    document_collaboration.register_tools(mcp)
    collection_tools.register_tools(mcp)
    ai_tools.register_tools(mcp)
