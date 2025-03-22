"""
Document reading tools for the MCP Outline server.

This module provides MCP tools for reading document content and comments.
"""
from typing import Optional, Dict, Any, List

from mcp_outline.features.documents.common import get_outline_client, OutlineClientError

def _format_document_content(document: Dict[str, Any]) -> str:
    """Format document content into readable text."""
    title = document.get("title", "Untitled Document")
    text = document.get("text", "")
    
    return f"""# {title}

{text}
"""

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

def _format_backlinks(documents: List[Dict[str, Any]]) -> str:
    """Format backlinks into readable text."""
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
            response = client.post("comments.list", {"documentId": document_id})
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
            return _format_backlinks(documents)
        except OutlineClientError as e:
            return f"Error retrieving backlinks: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    @mcp.tool()
    def get_document_id_from_title(query: str, collection_id: Optional[str] = None) -> str:
        """
        Find a document ID by searching for its title.
        
        Args:
            query: Title to search for
            collection_id: Optional collection to search within
            
        Returns:
            Document ID if found, or search results
        """
        try:
            client = get_outline_client()
            results = client.search_documents(query, collection_id)
            
            if not results:
                return f"No documents found matching '{query}'"
            
            # Check if we have an exact title match
            exact_matches = [r for r in results if r.get("document", {}).get("title", "").lower() == query.lower()]
            
            if exact_matches:
                doc = exact_matches[0].get("document", {})
                doc_id = doc.get("id", "unknown")
                title = doc.get("title", "Untitled")
                return f"Document ID: {doc_id} (Title: {title})"
            
            # Otherwise return the top match
            doc = results[0].get("document", {})
            doc_id = doc.get("id", "unknown")
            title = doc.get("title", "Untitled")
            return f"Best match - Document ID: {doc_id} (Title: {title})"
        except OutlineClientError as e:
            return f"Error searching for document: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
