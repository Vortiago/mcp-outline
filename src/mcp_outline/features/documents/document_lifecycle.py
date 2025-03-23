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
    def archive_document(document_id: str) -> str:
        """
        Archive a document.
        
        Args:
            document_id: The document ID to archive
            
        Returns:
            Result message
        """
        try:
            client = get_outline_client()
            document = client.archive_document(document_id)
            
            if not document:
                return "Failed to archive document."
                
            doc_title = document.get("title", "Untitled")
            
            return f"Document archived successfully: {doc_title}"
        except OutlineClientError as e:
            return f"Error archiving document: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    @mcp.tool()
    def unarchive_document(document_id: str) -> str:
        """
        Unarchive a previously archived document.
        
        Args:
            document_id: The document ID to unarchive
            
        Returns:
            Result message
        """
        try:
            client = get_outline_client()
            document = client.unarchive_document(document_id)
            
            if not document:
                return "Failed to unarchive document."
                
            doc_title = document.get("title", "Untitled")
            
            return f"Document unarchived successfully: {doc_title}"
        except OutlineClientError as e:
            return f"Error unarchiving document: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
            
    @mcp.tool()
    def delete_document(document_id: str, permanent: bool = False) -> str:
        """
        Delete a document (move to trash or permanently delete).
        
        Args:
            document_id: The document ID to delete
            permanent: If True, permanently deletes the document instead of 
                moving to trash
            
        Returns:
            Result message
        """
        try:
            client = get_outline_client()
            
            if permanent:
                success = client.permanently_delete_document(document_id)
                if success:
                    return "Document permanently deleted."
                else:
                    return "Failed to permanently delete document."
            else:
                # First get the document details for the success message
                document = client.get_document(document_id)
                doc_title = document.get("title", "Untitled")
                
                # Move to trash (using the regular delete endpoint)
                response = client.post("documents.delete", {"id": document_id})
                
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
    def restore_document(document_id: str) -> str:
        """
        Restore a document from trash.
        
        Args:
            document_id: The document ID to restore
            
        Returns:
            Result message
        """
        try:
            client = get_outline_client()
            document = client.restore_document(document_id)
            
            if not document:
                return "Failed to restore document from trash."
                
            doc_title = document.get("title", "Untitled")
            
            return f"Document restored successfully: {doc_title}"
        except OutlineClientError as e:
            return f"Error restoring document: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
            
    @mcp.tool()
    def list_archived_documents() -> str:
        """
        List all archived documents.
        
        Returns:
            Formatted string containing archived documents
        """
        try:
            client = get_outline_client()
            response = client.post("documents.archived")
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
    def list_trash() -> str:
        """
        List all documents in the trash.
        
        Returns:
            Formatted string containing trashed documents
        """
        try:
            client = get_outline_client()
            documents = client.list_trash()
            from mcp_outline.features.documents.document_search import (
                _format_documents_list,
            )
            return _format_documents_list(documents, "Documents in Trash")
        except OutlineClientError as e:
            return f"Error listing trash: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
