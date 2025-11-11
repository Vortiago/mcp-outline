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


def _format_comments(
    comments: List[Dict[str, Any]],
    total_count: int = 0,
    limit: int = 25,
    offset: int = 0,
) -> str:
    """Format document comments into readable text."""
    if not comments:
        return "No comments found for this document."

    output = "# Document Comments\n\n"

    # Add pagination info if provided
    if total_count:
        shown_range = (
            f"{offset + 1}-{min(offset + len(comments), total_count)}"
        )
        output += f"Showing comments {shown_range} of {total_count} total\n\n"

        # Add warning if there might be more comments than shown
        if len(comments) == limit:
            output += "Note: Only showing the first batch of comments. "
            output += f"Use offset={offset + limit} to see more comments.\n\n"

    for i, comment in enumerate(comments, offset + 1):
        user = comment.get("createdBy", {}).get("name", "Unknown User")
        created_at = comment.get("createdAt", "")
        comment_id = comment.get("id", "")
        anchor_text = comment.get("anchorText", "")

        # Extract data object containing the comment content
        data = comment.get("data", {})

        # Convert data to JSON string for display
        try:
            import json

            text = json.dumps(data, indent=2)
        except Exception:
            text = str(data)

        output += f"## {i}. Comment by {user}\n"
        output += f"ID: {comment_id}\n"
        if created_at:
            output += f"Date: {created_at}\n"
        if anchor_text:
            output += f'\nReferencing text: "{anchor_text}"\n'
        if data:
            output += f"\nComment content:\n```json\n{text}\n```\n\n"
        else:
            output += "\n(No comment content found)\n\n"

    return output


def register_tools(mcp) -> None:
    """
    Register document collaboration tools with the MCP server.

    Args:
        mcp: The FastMCP server instance
    """

    @mcp.tool()
    async def list_document_comments(
        document_id: str,
        include_anchor_text: bool = False,
        limit: int = 25,
        offset: int = 0,
    ) -> str:
        """
        Retrieves comments on a specific document with pagination support.

        IMPORTANT: By default, this returns up to 25 comments at a time. If
        there are more than 25 comments on the document, you'll need to make
        multiple calls with different offset values to get all comments. The
        response will indicate if there
        are more comments available.

        Use this tool when you need to:
        - Review feedback and discussions on a document
        - See all comments from different users
        - Find specific comments or questions
        - Track collaboration and input on documents

        Args:
            document_id: The document ID to get comments from
            include_anchor_text: Whether to include the document text that
                comments refer to
            limit: Maximum number of comments to return (default: 25)
            offset: Number of comments to skip for pagination (default: 0)

        Returns:
            Formatted string containing comments with author, date, and
            optional anchor text
        """
        try:
            client = await get_outline_client()
            data = {
                "documentId": document_id,
                "includeAnchorText": include_anchor_text,
                "limit": limit,
                "offset": offset,
            }

            response = await client.post("comments.list", data)
            comments = response.get("data", [])
            pagination = response.get("pagination", {})

            total_count = pagination.get("total", len(comments))
            return _format_comments(comments, total_count, limit, offset)
        except OutlineClientError as e:
            return f"Error listing comments: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool()
    async def get_comment(
        comment_id: str, include_anchor_text: bool = False
    ) -> str:
        """
        Retrieves a specific comment by its ID.

        Use this tool when you need to:
        - View details of a specific comment
        - Reference or quote a particular comment
        - Check comment content and metadata
        - Find a comment mentioned elsewhere

        Args:
            comment_id: The comment ID to retrieve
            include_anchor_text: Whether to include the document text that
                the comment refers to

        Returns:
            Formatted string with the comment content and metadata
        """
        try:
            client = await get_outline_client()
            response = await client.post(
                "comments.info",
                {"id": comment_id, "includeAnchorText": include_anchor_text},
            )
            comment = response.get("data", {})

            if not comment:
                return "Comment not found."

            user = comment.get("createdBy", {}).get("name", "Unknown User")
            created_at = comment.get("createdAt", "")
            anchor_text = comment.get("anchorText", "")

            # Extract data object containing the comment content
            data = comment.get("data", {})

            # Convert data to JSON string for display
            try:
                import json

                text = json.dumps(data, indent=2)
            except Exception:
                text = str(data)

            output = f"# Comment by {user}\n"
            if created_at:
                output += f"Date: {created_at}\n"
            if anchor_text:
                output += f'\nReferencing text: "{anchor_text}"\n'
            if data:
                output += f"\nComment content:\n```json\n{text}\n```\n"
            else:
                output += "\n(No comment content found)\n"

            return output
        except OutlineClientError as e:
            return f"Error getting comment: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool()
    async def get_document_backlinks(document_id: str) -> str:
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
            Formatted string listing all documents that link to
            the specified document
        """
        try:
            client = await get_outline_client()
            response = await client.post(
                "documents.list", {"backlinkDocumentId": document_id}
            )
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
