"""
Document organization for the MCP Outline server.

This module provides MCP tools for organizing documents.
"""

from typing import Optional

from mcp_outline.features.documents.common import (
    OutlineClientError,
    get_outline_client,
)


def register_tools(mcp) -> None:
    """
    Register document organization tools with the MCP server.

    Args:
        mcp: The FastMCP server instance
    """

    @mcp.tool()
    async def move_document(
        document_id: str,
        collection_id: Optional[str] = None,
        parent_document_id: Optional[str] = None,
    ) -> str:
        """
        Relocates a document to a different collection or parent document.

        IMPORTANT: When moving a document that has child documents (nested
        documents), all child documents will move along with it, maintaining
        their hierarchical structure. You must specify either collection_id or
        parent_document_id (or both).

        Use this tool when you need to:
        - Reorganize your document hierarchy
        - Move a document to a more relevant collection
        - Change a document's parent document
        - Restructure content organization

        Args:
            document_id: The document ID to move
            collection_id: Target collection ID (if moving between collections)
            parent_document_id: Optional parent document ID (for nesting)

        Returns:
            Result message confirming the move operation
        """
        try:
            client = await get_outline_client()

            # Require at least one destination parameter
            if collection_id is None and parent_document_id is None:
                return (
                    "Error: You must specify either a collection_id or "
                    "parent_document_id."
                )

            data = {"id": document_id}

            if collection_id:
                data["collectionId"] = collection_id

            if parent_document_id:
                data["parentDocumentId"] = parent_document_id

            response = await client.post("documents.move", data)

            # Check for successful response
            if response.get("data"):
                return "Document moved successfully."
            else:
                return "Failed to move document."
        except OutlineClientError as e:
            return f"Error moving document: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
