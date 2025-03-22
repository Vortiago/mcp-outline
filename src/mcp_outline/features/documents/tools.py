"""
Document outline tools for the MCP Outline server.

This module provides MCP tools for working with document outlines.
"""
from typing import Optional, Dict, Any, List
from mcp_outline.features.documents.common import get_outline_client, OutlineClientError


def _format_document_outline(document_id: str) -> str:
    """
    Format a document outline for display.
    
    Args:
        document_id: The document ID
        
    Returns:
        String with formatted document outline
    """
    try:
        client = get_outline_client()
        document = client.get_document(document_id)
        
        # Simple placeholder formatting - to be expanded
        title = document.get("title", "Untitled Document")
        text = document.get("text", "")
        return f"""# Document Outline: {title}

{text}
"""
    except OutlineClientError as e:
        return f"Error retrieving document outline: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

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
    Register document outline tools with the MCP server.
    
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
