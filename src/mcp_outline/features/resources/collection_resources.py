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
    Format collection metadata as key-value pairs.

    Args:
        collection: Collection data from API

    Returns:
        Formatted collection metadata
    """
    name = collection.get("name", "Untitled")
    description = collection.get("description", "")
    color = collection.get("color", "")
    doc_count = collection.get("documents", {}).get("count", 0)

    result = [
        f"Name: {name}",
        f"Documents: {doc_count}",
    ]

    if description:
        result.append(f"Description: {description}")

    if color:
        result.append(f"Color: {color}")

    return "\n".join(result)


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
            # Get collection directly by ID
            collection = await client.get_collection(collection_id)
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
            # Get all documents in the collection
            documents = await client.list_documents(
                collection_id=collection_id
            )
            return _format_document_list(documents)
        except OutlineClientError as e:
            return f"Outline client error: {str(e)}"
        except OutlineError as e:
            return f"Outline API error: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"
