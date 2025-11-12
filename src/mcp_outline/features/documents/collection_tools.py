"""
Collection management tools for the MCP Outline server.

This module provides MCP tools for managing collections.
"""

from typing import Any, Dict, Optional

from mcp_outline.features.documents.common import (
    OutlineClientError,
    get_outline_client,
)


def _format_file_operation(file_operation: Optional[Dict[str, Any]]) -> str:
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
    async def create_collection(
        name: str, description: str = "", color: Optional[str] = None
    ) -> str:
        """
            Creates a new collection for organizing documents.

            Use this tool when you need to:
            - Create a new section or category for documents
            - Set up a workspace for a new project or team
            - Organize content by department or topic
            - Establish a separate space for related documents

            Args:
                name: Name for the collection
                description: Optional description of the collection's purpose
                color: Optional hex color code for visual identification
        (e.g. #FF0000)

            Returns:
                Result message with the new collection ID
        """
        try:
            client = await get_outline_client()
            collection = await client.create_collection(
                name, description, color
            )

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
    async def update_collection(
        collection_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[str] = None,
    ) -> str:
        """
        Modifies an existing collection's properties.

        Use this tool when you need to:
        - Rename a collection
        - Update a collection's description
        - Change a collection's color coding
        - Refresh collection metadata

        Args:
            collection_id: The collection ID to update
            name: Optional new name for the collection
            description: Optional new description
            color: Optional new hex color code (e.g. #FF0000)

        Returns:
            Result message confirming update
        """
        try:
            client = await get_outline_client()

            # Make sure at least one field is being updated
            if name is None and description is None and color is None:
                return "Error: You must specify at least one field to update."

            collection = await client.update_collection(
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
    async def delete_collection(collection_id: str) -> str:
        """
        Permanently removes a collection and all its documents.

        Use this tool when you need to:
        - Remove an entire section of content
        - Delete obsolete project collections
        - Remove collections that are no longer needed
        - Clean up workspace organization

        WARNING: This action cannot be undone and will delete all
        documents within the collection.

        Args:
            collection_id: The collection ID to delete

        Returns:
            Result message confirming deletion
        """
        try:
            client = await get_outline_client()
            success = await client.delete_collection(collection_id)

            if success:
                return "Collection and all its documents deleted successfully."
            else:
                return "Failed to delete collection."
        except OutlineClientError as e:
            return f"Error deleting collection: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool()
    async def export_collection(
        collection_id: str, format: str = "outline-markdown"
    ) -> str:
        """
        Exports all documents in a collection to a downloadable file.

        IMPORTANT: This tool starts an asynchronous export operation which may
        take time to complete. The function returns information about the
        operation, including its status. When the operation is complete, the
        file can be downloaded or accessed via Outline's UI. The export
        preserves the document hierarchy and includes all document content and
        structure in the
        specified format.

        Use this tool when you need to:
        - Create a backup of collection content
        - Share collection content outside of Outline
        - Convert collection content to other formats
        - Archive collection content for offline use

        Args:
            collection_id: The collection ID to export
            format: Export format ("outline-markdown", "json", or "html")

        Returns:
            Information about the export operation and how to access the file
        """
        try:
            client = await get_outline_client()
            file_operation = await client.export_collection(
                collection_id, format
            )

            if not file_operation:
                return "Failed to start export operation."

            return _format_file_operation(file_operation)
        except OutlineClientError as e:
            return f"Error exporting collection: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool()
    async def export_all_collections(format: str = "outline-markdown") -> str:
        """
        Exports the entire workspace content to a downloadable file.

        IMPORTANT: This tool starts an asynchronous export operation which may
        take time to complete, especially for large workspaces. The function
        returns information about the operation, including its status. When
        the operation is complete, the file can be downloaded or accessed via
        Outline's UI. The export includes all collections, documents, and
        their
        hierarchies in the specified format.

        Use this tool when you need to:
        - Create a complete backup of all workspace content
        - Migrate content to another system
        - Archive all workspace documents
        - Get a comprehensive export of knowledge base

        Args:
            format: Export format ("outline-markdown", "json", or "html")

        Returns:
            Information about the export operation and how to access the file
        """
        try:
            client = await get_outline_client()
            file_operation = await client.export_all_collections(format)

            if not file_operation:
                return "Failed to start export operation."

            return _format_file_operation(file_operation)
        except OutlineClientError as e:
            return f"Error exporting collections: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
