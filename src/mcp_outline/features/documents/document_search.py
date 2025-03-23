"""
Document search tools for the MCP Outline server.

This module provides MCP tools for searching and listing documents.
"""
from typing import Any, Dict, List, Optional

from mcp_outline.features.documents.common import (
    OutlineClientError,
    get_outline_client,
)


def _format_search_results(results: List[Dict[str, Any]]) -> str:
    """Format search results into readable text."""
    if not results:
        return "No documents found matching your search."
    
    output = "# Search Results\n\n"
    
    for i, result in enumerate(results, 1):
        document = result.get("document", {})
        title = document.get("title", "Untitled")
        doc_id = document.get("id", "")
        context = result.get("context", "")
        
        output += f"## {i}. {title}\n"
        output += f"ID: {doc_id}\n"
        if context:
            output += f"Context: {context}\n"
        output += "\n"
    
    return output

def _format_documents_list(documents: List[Dict[str, Any]], title: str) -> str:
    """Format a list of documents into readable text."""
    if not documents:
        return f"No {title.lower()} found."
    
    output = f"# {title}\n\n"
    
    for i, document in enumerate(documents, 1):
        doc_title = document.get("title", "Untitled")
        doc_id = document.get("id", "")
        updated_at = document.get("updatedAt", "")
        
        output += f"## {i}. {doc_title}\n"
        output += f"ID: {doc_id}\n"
        if updated_at:
            output += f"Last Updated: {updated_at}\n"
        output += "\n"
    
    return output

def _format_collections(collections: List[Dict[str, Any]]) -> str:
    """Format collections into readable text."""
    if not collections:
        return "No collections found."
    
    output = "# Collections\n\n"
    
    for i, collection in enumerate(collections, 1):
        name = collection.get("name", "Untitled Collection")
        coll_id = collection.get("id", "")
        description = collection.get("description", "")
        
        output += f"## {i}. {name}\n"
        output += f"ID: {coll_id}\n"
        if description:
            output += f"Description: {description}\n"
        output += "\n"
    
    return output

def _format_collection_documents(doc_nodes: List[Dict[str, Any]]) -> str:
    """Format collection document structure into readable text."""
    if not doc_nodes:
        return "No documents found in this collection."
    
    def format_node(node, depth=0):
        # Extract node details
        title = node.get("title", "Untitled")
        node_id = node.get("id", "")
        children = node.get("children", [])
        
        # Format this node
        indent = "  " * depth
        text = f"{indent}- {title} (ID: {node_id})\n"
        
        # Recursively format children
        for child in children:
            text += format_node(child, depth + 1)
        
        return text
    
    output = "# Collection Structure\n\n"
    for node in doc_nodes:
        output += format_node(node)
    
    return output

def register_tools(mcp) -> None:
    """
    Register document search tools with the MCP server.
    
    Args:
        mcp: The FastMCP server instance
    """
    @mcp.tool()
    def search_documents(
        query: str, 
        collection_id: Optional[str] = None
    ) -> str:
        """
        Search for documents with keywords.
        
        Args:
            query: Search terms
            collection_id: Optional collection to search within
            
        Returns:
            Formatted string containing search results
        """
        try:
            client = get_outline_client()
            results = client.search_documents(query, collection_id)
            return _format_search_results(results)
        except OutlineClientError as e:
            return f"Error searching documents: {str(e)}"
        except Exception as e:
            return f"Unexpected error during search: {str(e)}"
    
    @mcp.tool()
    def list_collections() -> str:
        """
        List all available collections.
        
        Returns:
            Formatted string containing collection information
        """
        try:
            client = get_outline_client()
            collections = client.list_collections()
            return _format_collections(collections)
        except OutlineClientError as e:
            return f"Error listing collections: {str(e)}"
        except Exception as e:
            return f"Unexpected error listing collections: {str(e)}"
    
    @mcp.tool()
    def get_collection_structure(collection_id: str) -> str:
        """
        Get the document structure for a collection.
        
        Args:
            collection_id: The collection ID
            
        Returns:
            Formatted string containing the collection structure
        """
        try:
            client = get_outline_client()
            docs = client.get_collection_documents(collection_id)
            return _format_collection_documents(docs)
        except OutlineClientError as e:
            return f"Error getting collection structure: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
            
    @mcp.tool()
    def get_document_id_from_title(
        query: str, collection_id: Optional[str] = None
    ) -> str:
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
            exact_matches = [
                r for r in results 
                if (r.get("document", {}).get("title", "").lower() 
                    == query.lower())
            ]
            
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
