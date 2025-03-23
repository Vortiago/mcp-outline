"""
Document content management for the MCP Outline server.

This module provides MCP tools for creating and updating document content.
"""
from typing import Any, Dict, Optional

from mcp_outline.features.documents.common import (
    OutlineClientError,
    get_outline_client,
)


def register_tools(mcp) -> None:
    """
    Register document content tools with the MCP server.
    
    Args:
        mcp: The FastMCP server instance
    """
    @mcp.tool()
    def create_document(
        title: str,
        collection_id: str,
        text: str = "",
        parent_document_id: Optional[str] = None,
        publish: bool = True
    ) -> str:
        """
        Create a new document.
        
        Args:
            title: The document title
            collection_id: The collection ID to create the document in
            text: Optional markdown content for the document
            parent_document_id: Optional parent document ID for nesting
            publish: Whether to publish the document immediately
            
        Returns:
            Result message with the new document ID
        """
        try:
            client = get_outline_client()
            
            data = {
                "title": title,
                "text": text,
                "collectionId": collection_id,
                "publish": publish
            }
            
            if parent_document_id:
                data["parentDocumentId"] = parent_document_id
                
            response = client.post("documents.create", data)
            document = response.get("data", {})
            
            if not document:
                return "Failed to create document."
                
            doc_id = document.get("id", "unknown")
            doc_title = document.get("title", "Untitled")
            
            return f"Document created successfully: {doc_title} (ID: {doc_id})"
        except OutlineClientError as e:
            return f"Error creating document: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    @mcp.tool()
    def update_document(
        document_id: str,
        title: Optional[str] = None,
        text: Optional[str] = None,
        append: bool = False
    ) -> str:
        """
        Update an existing document.
        
        Args:
            document_id: The document ID to update
            title: New title (if None, keeps existing title)
            text: New content (if None, keeps existing content)
            append: If True, appends text instead of replacing
            
        Returns:
            Result message
        """
        try:
            client = get_outline_client()
            
            # Only include fields that are being updated
            data: Dict[str, Any] = {"id": document_id}
            
            if title is not None:
                data["title"] = title
                
            if text is not None:
                data["text"] = text
                data["append"] = append
            
            response = client.post("documents.update", data)
            document = response.get("data", {})
            
            if not document:
                return "Failed to update document."
                
            doc_title = document.get("title", "Untitled")
            
            return f"Document updated successfully: {doc_title}"
        except OutlineClientError as e:
            return f"Error updating document: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
            
    @mcp.tool()
    def add_comment(
        document_id: str,
        text: str
    ) -> str:
        """
        Add a comment to a document.
        
        Args:
            document_id: The document to comment on
            text: The comment text (supports markdown)
            
        Returns:
            Result message with the new comment ID
        """
        try:
            client = get_outline_client()
            
            data = {
                "documentId": document_id,
                "text": text
            }
            
            response = client.post("comments.create", data)
            comment = response.get("data", {})
            
            if not comment:
                return "Failed to create comment."
                
            comment_id = comment.get("id", "unknown")
            
            return f"Comment added successfully (ID: {comment_id})"
        except OutlineClientError as e:
            return f"Error adding comment: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
