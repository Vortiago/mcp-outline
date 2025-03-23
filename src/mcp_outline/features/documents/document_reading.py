"""
Document reading tools for the MCP Outline server.

This module provides MCP tools for reading document content.
"""
from typing import Any, Dict

from mcp_outline.features.documents.common import (
    OutlineClientError,
    get_outline_client,
)


def _format_document_content(document: Dict[str, Any]) -> str:
    """Format document content into readable text."""
    title = document.get("title", "Untitled Document")
    text = document.get("text", "")
    
    return f"""# {title}

{text}
"""

def register_tools(mcp) -> None:
    """
    Register document reading tools with the MCP server.
    
    Args:
        mcp: The FastMCP server instance
    """
    @mcp.tool()
    def read_document(document_id: str) -> str:
        """
        Get the full content of a document.
        
        Args:
            document_id: The document ID
            
        Returns:
            Formatted string containing the document content
        """
        try:
            client = get_outline_client()
            document = client.get_document(document_id)
            return _format_document_content(document)
        except OutlineClientError as e:
            return f"Error reading document: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    @mcp.tool()
    def export_document(document_id: str) -> str:
        """
        Export a document as markdown.
        
        Args:
            document_id: The document ID
            
        Returns:
            Document content in markdown format
        """
        try:
            client = get_outline_client()
            response = client.post("documents.export", {"id": document_id})
            return response.get("data", "No content available")
        except OutlineClientError as e:
            return f"Error exporting document: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
