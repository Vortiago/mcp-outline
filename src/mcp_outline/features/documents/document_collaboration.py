"""
Document collaboration tools for the MCP Outline server.

This module provides MCP tools for document comments, sharing, and 
collaboration.
"""
from typing import Any, Dict, List

from mcp_outline.features.documents.common import (
    OutlineClientError,
    get_outline_client,
)


def _format_comments(comments: List[Dict[str, Any]]) -> str:
    """Format document comments into readable text."""
    if not comments:
        return "No comments found for this document."
    
    output = "# Document Comments\n\n"
    
    for i, comment in enumerate(comments, 1):
        user = comment.get("createdBy", {}).get("name", "Unknown User")
        created_at = comment.get("createdAt", "")
        text = comment.get("text", "")
        
        output += f"## {i}. Comment by {user}\n"
        if created_at:
            output += f"Date: {created_at}\n\n"
        output += f"{text}\n\n"
    
    return output

def register_tools(mcp) -> None:
    """
    Register document collaboration tools with the MCP server.
    
    Args:
        mcp: The FastMCP server instance
    """
    @mcp.tool()
    def list_document_comments(document_id: str) -> str:
        """
        Get all comments for a document.
        
        Args:
            document_id: The document ID
            
        Returns:
            Formatted string containing comments
        """
        try:
            client = get_outline_client()
            response = client.post(
                "comments.list", {"documentId": document_id}
            )
            comments = response.get("data", [])
            return _format_comments(comments)
        except OutlineClientError as e:
            return f"Error listing comments: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    @mcp.tool()
    def get_comment(comment_id: str) -> str:
        """
        Get a specific comment by ID.
        
        Args:
            comment_id: The comment ID
            
        Returns:
            Formatted string containing the comment details
        """
        try:
            client = get_outline_client()
            response = client.post("comments.info", {"id": comment_id})
            comment = response.get("data", {})
            
            if not comment:
                return "Comment not found."
            
            user = comment.get("createdBy", {}).get("name", "Unknown User")
            created_at = comment.get("createdAt", "")
            text = comment.get("text", "")
            
            output = f"# Comment by {user}\n"
            if created_at:
                output += f"Date: {created_at}\n\n"
            output += f"{text}\n"
            
            return output
        except OutlineClientError as e:
            return f"Error getting comment: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
            
    @mcp.tool()
    def get_document_backlinks(document_id: str) -> str:
        """
        Get a list of documents that link to this document.
        
        Args:
            document_id: The document ID
            
        Returns:
            Formatted string containing backlink information
        """
        try:
            client = get_outline_client()
            response = client.post("documents.list", {
                "backlinkDocumentId": document_id
            })
            documents = response.get("data", [])
            
            if not documents:
                return "No documents link to this document."
            
            output = "# Documents Linking to This Document\n\n"
            
            for i, document in enumerate(documents, 1):
                title = document.get("title", "Untitled Document")
                doc_id = document.get("id", "")
                updated_at = document.get("updatedAt", "")
                
                output += f"## {i}. {title}\n"
                output += f"ID: {doc_id}\n"
                if updated_at:
                    output += f"Last Updated: {updated_at}\n"
                output += "\n"
            
            return output
        except OutlineClientError as e:
            return f"Error retrieving backlinks: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
