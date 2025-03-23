"""
Collection management tools for the MCP Outline server.

This module provides MCP tools for managing collections.
"""
from typing import Any, Dict, Optional

from mcp_outline.features.documents.common import (
    OutlineClientError,
    get_outline_client,
)


def _format_file_operation(file_operation: Dict[str, Any]) -> str:
    """Format file operation data into readable text."""
    if not file_operation:
        return "No file operation data available."
    
    # Get the file operation details
    state = file_operation.get("state", "unknown")
    type_info = file_operation.get("type", "unknown")
    name = file_operation.get("name", "unknown")
    file_operation_id = file_operation.get("id", "")
    
    # Format output
    output = f"# Export Operation: {name}\n\n"
    output += f"State: {state}\n"
    output += f"Type: {type_info}\n"
    output += f"ID: {file_operation_id}\n\n"
    
    # Provide instructions based on the state
    if state == "complete":
        output += "The export is complete and ready to download. "
        output += (
            "Use the ID with the appropriate download tool to retrieve "
            "the file.\n"
        )
    else:
        output += "The export is still in progress. "
        output += (
            f"Check the operation state again later using the ID: "
            f"{file_operation_id}\n"
        )
    
    return output

def register_tools(mcp) -> None:
    """
    Register collection management tools with the MCP server.
    
    Args:
        mcp: The FastMCP server instance
    """
    @mcp.tool()
    def create_collection(
        name: str,
        description: str = "",
        color: Optional[str] = None
    ) -> str:
        """
        Create a new collection.
        
        Args:
            name: Name for the collection
            description: Optional description
            color: Optional hex color code (e.g. #FF0000)
            
        Returns:
            Result message with the new collection ID
        """
        try:
            client = get_outline_client()
            collection = client.create_collection(name, description, color)
            
            if not collection:
                return "Failed to create collection."
                
            collection_id = collection.get("id", "unknown")
            collection_name = collection.get("name", "Untitled")
            
            return (
                f"Collection created successfully: {collection_name} "
                f"(ID: {collection_id})"
            )
        except OutlineClientError as e:
            return f"Error creating collection: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    @mcp.tool()
    def update_collection(
        collection_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[str] = None
    ) -> str:
        """
        Update an existing collection.
        
        Args:
            collection_id: The collection ID to update
            name: Optional new name
            description: Optional new description
            color: Optional new hex color code (e.g. #FF0000)
            
        Returns:
            Result message
        """
        try:
            client = get_outline_client()
            
            # Make sure at least one field is being updated
            if name is None and description is None and color is None:
                return "Error: You must specify at least one field to update."
            
            collection = client.update_collection(
                collection_id, name, description, color
            )
            
            if not collection:
                return "Failed to update collection."
                
            collection_name = collection.get("name", "Untitled")
            
            return f"Collection updated successfully: {collection_name}"
        except OutlineClientError as e:
            return f"Error updating collection: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    @mcp.tool()
    def delete_collection(collection_id: str) -> str:
        """
        Delete a collection and all its documents.
        
        This action cannot be undone! All documents within the collection 
        will be deleted.
        
        Args:
            collection_id: The collection ID to delete
            
        Returns:
            Result message
        """
        try:
            client = get_outline_client()
            success = client.delete_collection(collection_id)
            
            if success:
                return "Collection and all its documents deleted successfully."
            else:
                return "Failed to delete collection."
        except OutlineClientError as e:
            return f"Error deleting collection: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    @mcp.tool()
    def export_collection(
        collection_id: str,
        format: str = "outline-markdown"
    ) -> str:
        """
        Export a collection to a file.
        
        Args:
            collection_id: The collection ID to export
            format: Export format ("outline-markdown", "json", or "html")
            
        Returns:
            Information about the export operation
        """
        try:
            client = get_outline_client()
            file_operation = client.export_collection(collection_id, format)
            
            if not file_operation:
                return "Failed to start export operation."
                
            return _format_file_operation(file_operation)
        except OutlineClientError as e:
            return f"Error exporting collection: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    @mcp.tool()
    def export_all_collections(format: str = "outline-markdown") -> str:
        """
        Export all collections to a file.
        
        Args:
            format: Export format ("outline-markdown", "json", or "html")
            
        Returns:
            Information about the export operation
        """
        try:
            client = get_outline_client()
            file_operation = client.export_all_collections(format)
            
            if not file_operation:
                return "Failed to start export operation."
                
            return _format_file_operation(file_operation)
        except OutlineClientError as e:
            return f"Error exporting collections: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
