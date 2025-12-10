"""
Document organization for the MCP Outline server.

This module provides MCP tools for organizing documents.
"""

from typing import Any, Dict, Optional

from mcp.types import CallToolResult, ToolAnnotations

from mcp_outline.features.documents.common import (
    OutlineClientError,
    get_outline_client,
)
from mcp_outline.utils.response_handler import create_tool_response


def register_tools(mcp) -> None:
    """
    Register document organization tools with the MCP server.

    Args:
        mcp: The FastMCP server instance
    """

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=False,
        )
    )
    async def move_document(
        document_id: str,
        collection_id: Optional[str] = None,
        parent_document_id: Optional[str] = None,
    ) -> CallToolResult:
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
                return create_tool_response(
                    "Error: You must specify either a collection_id or "
                    "parent_document_id.",
                    {"error": "missing_target", "document_id": document_id},
                )

            data: Dict[str, Any] = {"id": document_id}

            if collection_id:
                data["collectionId"] = collection_id

            if parent_document_id:
                data["parentDocumentId"] = parent_document_id

            response = await client.post("documents.move", data)

            # Check for successful response
            if response.get("data"):
                doc_data = response.get("data", {})
                doc_title = doc_data.get("title", "Untitled")

                structured_data: Dict[str, Any] = {
                    "document_id": document_id,
                    "title": doc_title,
                }
                if collection_id:
                    structured_data["new_collection_id"] = collection_id
                if parent_document_id:
                    structured_data["new_parent_id"] = parent_document_id

                return create_tool_response(
                    "Document moved successfully.",
                    structured_data,
                )
            else:
                return create_tool_response(
                    "Failed to move document.",
                    {"error": "move_failed", "document_id": document_id},
                )
        except OutlineClientError as e:
            return create_tool_response(
                f"Error moving document: {str(e)}",
                {"error": str(e), "document_id": document_id},
            )
        except Exception as e:
            return create_tool_response(
                f"Unexpected error: {str(e)}",
                {"error": str(e), "document_id": document_id},
            )
