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
    async def read_document(document_id: str) -> str:
        """
        Retrieves and displays the full content of a document.

        Use this tool when you need to:
        - Access the complete content of a specific document
        - Review document information in detail
        - Quote or reference document content
        - Analyze document contents

        Args:
            document_id: The document ID to retrieve

        Returns:
            Formatted string containing the document title and content
        """
        try:
            client = await get_outline_client()
            document = await client.get_document(document_id)
            return _format_document_content(document)
        except OutlineClientError as e:
            return f"Error reading document: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool()
    async def export_document(document_id: str) -> str:
        """
        Exports a document as plain markdown text.

        Use this tool when you need to:
        - Get clean markdown content without formatting
        - Extract document content for external use
        - Process document content in another application
        - Share document content outside Outline

        Args:
            document_id: The document ID to export

        Returns:
            Document content in markdown format without additional formatting
        """
        try:
            client = await get_outline_client()
            response = await client.post(
                "documents.export", {"id": document_id}
            )
            return response.get("data", "No content available")
        except OutlineClientError as e:
            return f"Error exporting document: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
