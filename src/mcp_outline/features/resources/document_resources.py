"""
Document-related MCP resources.

Provides direct access to document content and backlinks via URIs.
"""

from mcp_outline.features.documents.common import (
    OutlineClientError,
    get_outline_client,
)
from mcp_outline.utils.outline_client import OutlineError


def _format_backlinks(backlinks: list) -> str:
    """
    Format document backlinks as simple list.

    Args:
        backlinks: List of documents linking to the target document

    Returns:
        Formatted backlinks list
    """
    if not backlinks:
        return "No backlinks found."

    # Simple bullet list without heavy formatting
    result = []
    for doc in backlinks:
        title = doc.get("title", "Untitled")
        doc_id = doc.get("id", "")
        result.append(f"- {title} ({doc_id})")

    return "\n".join(result)


def register_resources(mcp):
    """Register document-related resources."""

    @mcp.resource("outline://document/{document_id}")
    async def get_document_content(document_id: str) -> str:
        """
        Get full document content in markdown format.

        Args:
            document_id: The document ID

        Returns:
            Document content as markdown
        """
        try:
            client = await get_outline_client()
            document = await client.get_document(document_id)

            # Return the markdown text content
            return document.get("text", "")
        except OutlineClientError as e:
            return f"Outline client error: {str(e)}"
        except OutlineError as e:
            return f"Outline API error: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"

    @mcp.resource("outline://document/{document_id}/backlinks")
    async def get_document_backlinks(document_id: str) -> str:
        """
        Get documents that link to this document.

        Args:
            document_id: The document ID

        Returns:
            Formatted list of backlinks
        """
        try:
            client = await get_outline_client()
            # Use direct API call to get backlinks
            response = await client.post(
                "documents.list", {"backlinkDocumentId": document_id}
            )
            backlinks = response.get("data", [])

            return _format_backlinks(backlinks)
        except OutlineClientError as e:
            return f"Outline client error: {str(e)}"
        except OutlineError as e:
            return f"Outline API error: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"
