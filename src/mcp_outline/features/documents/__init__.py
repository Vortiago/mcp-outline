# Document management features for MCP Outline
from mcp_outline.features.documents import tools


def register(mcp):
    """
    Register document management features with the MCP server.
    
    Args:
        mcp: The FastMCP server instance
    """
    tools.register_tools(mcp)
