# Document management features for MCP Outline
from typing import Optional
from mcp_outline.features.documents import tools
from mcp_outline.features.documents import document_reading
from mcp_outline.features.documents import document_editing

def register(mcp, api_key: Optional[str] = None, api_url: Optional[str] = None):
    """
    Register document management features with the MCP server.
    
    Args:
        mcp: The FastMCP server instance
        api_key: Optional API key for Outline
        api_url: Optional API URL for Outline
    """
    tools.register_tools(mcp)
    document_reading.register_tools(mcp)
    document_editing.register_tools(mcp)
