"""
Document lifecycle management for the MCP Outline server.

This module provides MCP tools for archiving, trashing, and restoring
documents.
"""

from mcp_outline.features.documents.common import (
    OutlineClientError,
    get_outline_client,
)


def register_tools(mcp) -> None:
    """
    Register document lifecycle tools with the MCP server.

    Args:
        mcp: The FastMCP server instance
    """

    @mcp.tool()
    async def archive_document(document_id: str) -> str:
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
                return "Failed to archive document."

            doc_title = document.get("title", "Untitled")

            return f"Document archived successfully: {doc_title}"
        except OutlineClientError as e:
            return f"Error archiving document: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool()
    async def unarchive_document(document_id: str) -> str:
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
                return "Failed to unarchive document."

            doc_title = document.get("title", "Untitled")

            return f"Document unarchived successfully: {doc_title}"
        except OutlineClientError as e:
            return f"Error unarchiving document: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool()
    async def delete_document(
        document_id: str, permanent: bool = False
    ) -> str:
        """
        Moves a document to trash or permanently deletes it.

        IMPORTANT: When permanent=False (the default), documents are moved to
        trash and retained for 30 days before being permanently deleted.
        During
        this period, they can be restored using the restore_document tool.
        Setting permanent=True bypasses the trash and immediately deletes the
        document without any recovery option.

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
                success = await client.permanently_delete_document(document_id)
                if success:
                    return "Document permanently deleted."
                else:
                    return "Failed to permanently delete document."
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
                    return f"Document moved to trash: {doc_title}"
                else:
                    return "Failed to move document to trash."

        except OutlineClientError as e:
            return f"Error deleting document: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool()
    async def restore_document(document_id: str) -> str:
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
                return "Failed to restore document from trash."

            doc_title = document.get("title", "Untitled")

            return f"Document restored successfully: {doc_title}"
        except OutlineClientError as e:
            return f"Error restoring document: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool()
    async def list_archived_documents() -> str:
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
            return _format_documents_list(documents, "Archived Documents")
        except OutlineClientError as e:
            return f"Error listing archived documents: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool()
    async def list_trash() -> str:
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

            return _format_documents_list(documents, "Documents in Trash")
        except OutlineClientError as e:
            return f"Error listing trash: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
