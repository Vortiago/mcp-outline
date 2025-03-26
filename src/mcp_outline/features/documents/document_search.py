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
        Searches for documents using keywords or phrases across your knowledge 
        base.
        
        IMPORTANT: The search performs full-text search across all document 
        content and titles. Results are ranked by relevance, with exact 
        matches 
        and title matches typically ranked higher. The search will return 
        snippets of content (context) where the search terms appear in the 
        document. You can limit the search to a specific collection by 
        providing 
        the collection_id.
        
        Use this tool when you need to:
        - Find documents containing specific terms or topics
        - Locate information across multiple documents
        - Search within a specific collection using collection_id
        - Discover content based on keywords
        
        Args:
            query: Search terms (e.g., "vacation policy" or "project plan")
            collection_id: Optional collection to limit the search to
            
        Returns:
            Formatted string containing search results with document titles 
            and 
            contexts
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
        Retrieves and displays all available collections in the workspace.
        
        Use this tool when you need to:
        - See what collections exist in the workspace
        - Get collection IDs for other operations
        - Explore the organization of the knowledge base
        - Find a specific collection by name
        
        Returns:
            Formatted string containing collection names, IDs, and descriptions
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
        Retrieves the hierarchical document structure of a collection.
        
        Use this tool when you need to:
        - Understand how documents are organized in a collection
        - Find document IDs within a specific collection
        - See the parent-child relationships between documents
        - Get an overview of a collection's content structure
        
        Args:
            collection_id: The collection ID to examine
            
        Returns:
            Formatted string showing the hierarchical structure of documents
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
        Locates a document ID by searching for its title.
        
        IMPORTANT: This tool first checks for exact title matches 
        (case-insensitive). If none are found, it returns the best partial 
        match instead. This is useful when you're not sure of the exact title 
        but need 
        to reference a document in other operations. Results are more accurate 
        when you provide more of the actual title in your query.
        
        Use this tool when you need to:
        - Find a document's ID when you only know its title
        - Get the document ID for use in other operations
        - Verify if a document with a specific title exists
        - Find the best matching document if exact title is unknown
        
        Args:
            query: Title to search for (can be exact or partial)
            collection_id: Optional collection to limit the search to
            
        Returns:
            Document ID if found, or best match information
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
