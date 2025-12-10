"""
Document lifecycle management for the MCP Outline server.

This module provides MCP tools for archiving, trashing, and restoring
documents.
"""

import os
from typing import Any, Dict, List

from mcp.types import CallToolResult, ToolAnnotations

from mcp_outline.features.documents.common import (
    OutlineClientError,
    get_outline_client,
)
from mcp_outline.utils.response_handler import create_tool_response


def register_tools(mcp) -> None:
    """
    Register document lifecycle tools with the MCP server.

    Args:
        mcp: The FastMCP server instance
    """
    disable_delete = os.getenv("OUTLINE_DISABLE_DELETE", "").lower() in (
        "true",
        "1",
        "yes",
    )

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False, destructiveHint=True, idempotentHint=True
        )
    )
    async def archive_document(document_id: str) -> CallToolResult:
        """
        Archives a document to remove it from active use while preserving it.

        IMPORTANT: Archived documents are removed from collections but remain
        searchable in the system. They won't appear in normal collection views
        but can still be found through search or the archive list.

        Use this tool when you need to:
        - Remove outdated or inactive documents from view
        - Clean up collections while preserving document history
        - Preserve documents that are no longer relevant
        - Temporarily hide documents without deleting them

        Args:
            document_id: The document ID to archive

        Returns:
            Result message confirming archival
        """
        try:
            client = await get_outline_client()
            document = await client.archive_document(document_id)

            if not document:
                return create_tool_response(
                    "Failed to archive document.",
                    {"error": "archive_failed", "document_id": document_id},
                )

            doc_title = document.get("title", "Untitled")

            return create_tool_response(
                f"Document archived successfully: {doc_title}",
                {
                    "document_id": document_id,
                    "title": doc_title,
                    "status": "archived",
                },
            )
        except OutlineClientError as e:
            return create_tool_response(
                f"Error archiving document: {str(e)}",
                {"error": str(e), "document_id": document_id},
            )
        except Exception as e:
            return create_tool_response(
                f"Unexpected error: {str(e)}",
                {"error": str(e), "document_id": document_id},
            )

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False, destructiveHint=False, idempotentHint=True
        )
    )
    async def unarchive_document(document_id: str) -> CallToolResult:
        """
        Restores a previously archived document to active status.

        Use this tool when you need to:
        - Restore archived documents to active use
        - Access or reference previously archived content
        - Make archived content visible in collections again
        - Update and reuse archived documents

        Args:
            document_id: The document ID to unarchive

        Returns:
            Result message confirming restoration
        """
        try:
            client = await get_outline_client()
            document = await client.unarchive_document(document_id)

            if not document:
                return create_tool_response(
                    "Failed to unarchive document.",
                    {"error": "unarchive_failed", "document_id": document_id},
                )

            doc_title = document.get("title", "Untitled")

            return create_tool_response(
                f"Document unarchived successfully: {doc_title}",
                {
                    "document_id": document_id,
                    "title": doc_title,
                    "status": "active",
                },
            )
        except OutlineClientError as e:
            return create_tool_response(
                f"Error unarchiving document: {str(e)}",
                {"error": str(e), "document_id": document_id},
            )
        except Exception as e:
            return create_tool_response(
                f"Unexpected error: {str(e)}",
                {"error": str(e), "document_id": document_id},
            )

    if not disable_delete:

        @mcp.tool(
            annotations=ToolAnnotations(
                readOnlyHint=False, destructiveHint=True, idempotentHint=True
            )
        )
        async def delete_document(
            document_id: str, permanent: bool = False
        ) -> CallToolResult:
            """
            Moves a document to trash or permanently deletes it.

            IMPORTANT: When permanent=False (the default), documents are
            moved to trash and retained for 30 days before being
            permanently deleted. During this period, they can be restored
            using the restore_document tool. Setting permanent=True
            bypasses the trash and immediately deletes the document
            without any recovery option.

            Use this tool when you need to:
            - Remove unwanted or unnecessary documents
            - Delete obsolete content
            - Clean up workspace by removing documents
            - Permanently remove sensitive information (with permanent=True)

            Args:
                document_id: The document ID to delete
                permanent: If True, permanently deletes the document without
                    recovery option

            Returns:
                Result message confirming deletion
            """
            try:
                client = await get_outline_client()

                if permanent:
                    success = await client.permanently_delete_document(
                        document_id
                    )
                    if success:
                        return create_tool_response(
                            "Document permanently deleted.",
                            {
                                "document_id": document_id,
                                "status": "deleted",
                                "permanent": True,
                            },
                        )
                    else:
                        return create_tool_response(
                            "Failed to permanently delete document.",
                            {
                                "error": "delete_failed",
                                "document_id": document_id,
                            },
                        )
                else:
                    # First get the document details for the success message
                    document = await client.get_document(document_id)
                    doc_title = document.get("title", "Untitled")

                    # Move to trash (using the regular delete endpoint)
                    response = await client.post(
                        "documents.delete", {"id": document_id}
                    )

                    # Check for successful response
                    if response.get("success", False):
                        return create_tool_response(
                            f"Document moved to trash: {doc_title}",
                            {
                                "document_id": document_id,
                                "title": doc_title,
                                "status": "deleted",
                                "permanent": False,
                            },
                        )
                    else:
                        return create_tool_response(
                            "Failed to move document to trash.",
                            {
                                "error": "delete_failed",
                                "document_id": document_id,
                            },
                        )

            except OutlineClientError as e:
                return create_tool_response(
                    f"Error deleting document: {str(e)}",
                    {"error": str(e), "document_id": document_id},
                )
            except Exception as e:
                return create_tool_response(
                    f"Unexpected error: {str(e)}",
                    {"error": str(e), "document_id": document_id},
                )

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False, destructiveHint=False, idempotentHint=True
        )
    )
    async def restore_document(document_id: str) -> CallToolResult:
        """
        Recovers a document from the trash back to active status.

        Use this tool when you need to:
        - Retrieve accidentally deleted documents
        - Restore documents from trash to active use
        - Recover documents deleted within the last 30 days
        - Access content that was previously trashed

        Args:
            document_id: The document ID to restore

        Returns:
            Result message confirming restoration
        """
        try:
            client = await get_outline_client()
            document = await client.restore_document(document_id)

            if not document:
                return create_tool_response(
                    "Failed to restore document from trash.",
                    {"error": "restore_failed", "document_id": document_id},
                )

            doc_title = document.get("title", "Untitled")

            return create_tool_response(
                f"Document restored successfully: {doc_title}",
                {
                    "document_id": document_id,
                    "title": doc_title,
                    "status": "restored",
                },
            )
        except OutlineClientError as e:
            return create_tool_response(
                f"Error restoring document: {str(e)}",
                {"error": str(e), "document_id": document_id},
            )
        except Exception as e:
            return create_tool_response(
                f"Unexpected error: {str(e)}",
                {"error": str(e), "document_id": document_id},
            )

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=True, destructiveHint=False, idempotentHint=True
        )
    )
    async def list_archived_documents() -> CallToolResult:
        """
        Displays all documents that have been archived.

        Use this tool when you need to:
        - Find specific archived documents
        - Review what documents have been archived
        - Identify documents for possible unarchiving
        - Check archive status of workspace content

        Returns:
            Formatted string containing list of archived documents
        """
        try:
            client = await get_outline_client()
            response = await client.post("documents.archived")
            from mcp_outline.features.documents.document_search import (
                _format_documents_list,
            )

            documents = response.get("data", [])

            # Build structured document list
            doc_list: List[Dict[str, Any]] = []
            for doc in documents:
                doc_list.append(
                    {
                        "document_id": doc.get("id", ""),
                        "title": doc.get("title", "Untitled"),
                        "updated_at": doc.get("updatedAt", ""),
                    }
                )

            return create_tool_response(
                _format_documents_list(documents, "Archived Documents"),
                {
                    "documents": doc_list,
                    "count": len(doc_list),
                },
            )
        except OutlineClientError as e:
            return create_tool_response(
                f"Error listing archived documents: {str(e)}",
                {"error": str(e)},
            )
        except Exception as e:
            return create_tool_response(
                f"Unexpected error: {str(e)}",
                {"error": str(e)},
            )

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=True, destructiveHint=False, idempotentHint=True
        )
    )
    async def list_trash() -> CallToolResult:
        """
        Displays all documents currently in the trash.

        Use this tool when you need to:
        - Find deleted documents that can be restored
        - Review what documents are pending permanent deletion
        - Identify documents to restore from trash
        - Verify if specific documents were deleted

        Returns:
            Formatted string containing list of documents in trash
        """
        try:
            client = await get_outline_client()
            documents = await client.list_trash()
            from mcp_outline.features.documents.document_search import (
                _format_documents_list,
            )

            # Build structured document list
            doc_list: List[Dict[str, Any]] = []
            for doc in documents:
                doc_list.append(
                    {
                        "document_id": doc.get("id", ""),
                        "title": doc.get("title", "Untitled"),
                        "deleted_at": doc.get("deletedAt", ""),
                    }
                )

            return create_tool_response(
                _format_documents_list(documents, "Documents in Trash"),
                {
                    "documents": doc_list,
                    "count": len(doc_list),
                },
            )
        except OutlineClientError as e:
            return create_tool_response(
                f"Error listing trash: {str(e)}",
                {"error": str(e)},
            )
        except Exception as e:
            return create_tool_response(
                f"Unexpected error: {str(e)}",
                {"error": str(e)},
            )
