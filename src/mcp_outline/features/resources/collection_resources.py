"""
Collection-related MCP resources.

Provides direct access to collection metadata and document lists via URIs.
"""

from mcp_outline.features.documents.common import (
    OutlineClientError,
    get_outline_client,
)
from mcp_outline.utils.outline_client import OutlineError


def _format_collection_metadata(collection: dict) -> str:
    """
    Format collection metadata for display.

    Args:
        collection: Collection data from API

    Returns:
        Formatted collection metadata
    """
    name = collection.get("name", "Untitled")
    description = collection.get("description", "")
    color = collection.get("color", "")
    doc_count = collection.get("documents", 0)

    result = f"# {name}\n\n"

    if description:
        result += f"{description}\n\n"

    result += f"**Documents**: {doc_count}\n"

    if color:
        result += f"**Color**: {color}\n"

    return result


def _format_collection_tree(tree: list, indent: int = 0) -> str:
    """
    Format collection document tree hierarchically.

    Args:
        tree: List of document nodes with children
        indent: Current indentation level

    Returns:
        Formatted tree structure
    """
    result = ""
    for node in tree:
        title = node.get("title", "Untitled")
        doc_id = node.get("id", "")
        prefix = "  " * indent + "- "
        result += f"{prefix}{title} ({doc_id})\n"

        children = node.get("children", [])
        if children:
            result += _format_collection_tree(children, indent + 1)

    return result


def _format_document_list(documents: list) -> str:
    """
    Format list of documents in a collection.

    Args:
        documents: List of document summaries

    Returns:
        Formatted document list
    """
    if not documents:
        return "No documents in this collection.\n"

    result = "# Documents\n\n"
    for doc in documents:
        title = doc.get("title", "Untitled")
        doc_id = doc.get("id", "")
        updated = doc.get("updatedAt", "")
        result += f"- **{title}** (`{doc_id}`)\n"
        if updated:
            result += f"  - Last updated: {updated}\n"

    return result


def register_resources(mcp):
    """Register collection-related resources."""

    @mcp.resource("outline://collection/{collection_id}")
    async def get_collection_metadata(collection_id: str) -> str:
        """
        Get collection metadata and properties.

        Args:
            collection_id: The collection ID

        Returns:
            Formatted collection metadata
        """
        try:
            client = await get_outline_client()
            # Get all collections and find the matching one
            collections = await client.list_collections()
            collection = next(
                (c for c in collections if c.get("id") == collection_id),
                None,
            )

            if not collection:
                return f"Error: Collection {collection_id} not found"

            return _format_collection_metadata(collection)
        except OutlineClientError as e:
            return f"Outline client error: {str(e)}"
        except OutlineError as e:
            return f"Outline API error: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"

    @mcp.resource("outline://collection/{collection_id}/tree")
    async def get_collection_tree(collection_id: str) -> str:
        """
        Get hierarchical document tree for a collection.

        Args:
            collection_id: The collection ID

        Returns:
            Formatted document tree
        """
        try:
            client = await get_outline_client()
            documents = await client.get_collection_documents(collection_id)

            if not documents:
                return "No documents in this collection.\n"

            result = "# Document Tree\n\n"
            result += _format_collection_tree(documents)
            return result
        except OutlineClientError as e:
            return f"Outline client error: {str(e)}"
        except OutlineError as e:
            return f"Outline API error: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"

    @mcp.resource("outline://collection/{collection_id}/documents")
    async def get_collection_documents(collection_id: str) -> str:
        """
        Get list of documents in a collection.

        Args:
            collection_id: The collection ID

        Returns:
            Formatted document list
        """
        try:
            client = await get_outline_client()
            # Search for all documents in the collection
            result = await client.search_documents(
                query="", collection_id=collection_id
            )

            documents = result.get("data", [])
            return _format_document_list(documents)
        except OutlineClientError as e:
            return f"Outline client error: {str(e)}"
        except OutlineError as e:
            return f"Outline API error: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"
