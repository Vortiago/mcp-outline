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
        comment_id = comment.get("id", "")
        
        output += f"## {i}. Comment by {user}\n"
        output += f"ID: {comment_id}\n"
        if created_at:
            output += f"Date: {created_at}\n"
        output += f"\n{text}\n\n"
    
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
        Retrieves all comments on a specific document.
        
        Use this tool when you need to:
        - Review feedback and discussions on a document
        - See all comments from different users
        - Find specific comments or questions
        - Track collaboration and input on documents
        
        Args:
            document_id: The document ID to get comments from
            
        Returns:
            Formatted string containing all comments with author and date info
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
        Retrieves a specific comment by its ID.
        
        Use this tool when you need to:
        - View details of a specific comment
        - Reference or quote a particular comment
        - Check comment content and metadata
        - Find a comment mentioned elsewhere
        
        Args:
            comment_id: The comment ID to retrieve
            
        Returns:
            Formatted string with the comment content and metadata
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
        Finds all documents that link to a specific document.
        
        Use this tool when you need to:
        - Discover references to a document across the workspace
        - Identify dependencies between documents
        - Find documents related to a specific document
        - Understand document relationships and connections
        
        Args:
            document_id: The document ID to find backlinks for
            
        Returns:
            Formatted string listing all documents that link to the specified 
document
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
