"""
Document content management for the MCP Outline server.

This module provides MCP tools for creating and updating
document content, and adding comments.
"""

from typing import Any, Dict, Optional

from mcp.types import ToolAnnotations

from mcp_outline.features.documents.common import (
    OutlineClientError,
    get_outline_client,
)
from mcp_outline.utils.document_cache import get_document_cache


def register_tools(mcp) -> None:
    """
    Register document content tools with the MCP server.

    Args:
        mcp: The FastMCP server instance
    """

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
        ),
        meta={
            "endpoint": "documents.create",
            "min_role": "member",
        },
    )
    async def create_document(
        title: str,
        collection_id: str,
        text: str = "",
        parent_document_id: Optional[str] = None,
        publish: bool = True,
        template: Optional[bool] = None,
        icon: Optional[str] = None,
    ) -> str:
        """
        Creates a new document in a specified collection.

        Use this tool when you need to:
        - Add new content to a knowledge base
        - Create documentation, guides, or notes
        - Add a child document to an existing parent
        - Start a new document thread or topic
        - Create a reusable template document

        Note: For Mermaid diagrams, use ```mermaidjs
        (not ```mermaid) as the code fence language
        identifier for proper rendering.

        Args:
            title: The document title
            collection_id: The collection ID to create in
            text: Optional markdown content for the document
            parent_document_id: Optional parent document ID
                for nesting
            publish: Whether to publish immediately (True)
                or save as draft (False)
            template: If True, creates the document as a
                template
            icon: Optional emoji character to use as the
                document icon (e.g. "📋", "🚀"). If None,
                no icon is set.

        Returns:
            Result message with the new document ID
        """
        try:
            client = await get_outline_client()

            data = {
                "title": title,
                "text": text,
                "collectionId": collection_id,
                "publish": publish,
            }

            if parent_document_id:
                data["parentDocumentId"] = parent_document_id

            if template is not None:
                data["template"] = template

            if icon is not None:
                data["icon"] = icon

            response = await client.post("documents.create", data)
            document = response.get("data", {})

            if not document:
                return "Failed to create document."

            doc_id = document.get("id", "unknown")
            doc_title = document.get("title", "Untitled")

            return f"Document created successfully: {doc_title} (ID: {doc_id})"
        except OutlineClientError as e:
            return f"Error creating document: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=False,
        ),
        meta={
            "endpoint": "documents.update",
            "min_role": "member",
        },
    )
    async def update_document(
        document_id: str,
        title: Optional[str] = None,
        text: Optional[str] = None,
        append: bool = False,
        template: Optional[bool] = None,
        icon: Optional[str] = None,
    ) -> str:
        """
        Modifies an existing document's title or content.

        IMPORTANT: This tool replaces the document content
        rather than just adding to it. For partial edits
        (changing specific text), prefer the edit_document
        tool instead.

        Use this tool when you need to:
        - Replace the entire document content
        - Change a document's title
        - Append new content to an existing document
        - Convert a document to or from a template

        Note: For Mermaid diagrams, use ```mermaidjs
        (not ```mermaid) as the code fence language
        identifier for proper rendering.

        Args:
            document_id: The document ID to update
            title: New title (if None, keeps existing title)
            text: New content (if None, keeps existing)
            append: If True, adds text to end of document
                instead of replacing
            template: If True, converts to a template.
                If False, converts a template back to a
                regular document.
            icon: Optional emoji character to use as the
                document icon (e.g. "📋", "🚀"). If None,
                keeps existing icon. Pass an empty string
                to remove the icon.

        Returns:
            Result message confirming update
        """
        try:
            client = await get_outline_client()

            data: Dict[str, Any] = {"id": document_id}

            if title is not None:
                data["title"] = title

            if text is not None:
                data["text"] = text
                data["append"] = append

            if template is not None:
                data["template"] = template

            if icon is not None:
                # Empty string removes the icon;
                # Outline API expects null to clear it.
                data["icon"] = None if icon == "" else icon

            response = await client.post("documents.update", data)
            document = response.get("data", {})

            if not document:
                return "Failed to update document."

            # Evict all cached copies of this document
            # (across all API keys) to prevent stale reads
            cache = get_document_cache()
            await cache.evict_document(document_id)

            doc_title = document.get("title", "Untitled")
            return f"Document updated successfully: {doc_title}"
        except OutlineClientError as e:
            return f"Error updating document: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
        ),
        meta={
            "endpoint": "comments.create",
            "min_role": "viewer",
        },
    )
    async def add_comment(
        document_id: str,
        text: str,
        parent_comment_id: Optional[str] = None,
    ) -> str:
        """
        Adds a comment to a document or replies to an
        existing comment.

        Use this tool when you need to:
        - Provide feedback on document content
        - Ask questions about specific information
        - Reply to another user's comment
        - Collaborate with others on document development

        Args:
            document_id: The document to comment on
            text: The comment text (supports markdown)
            parent_comment_id: Optional parent comment ID
                (for replies)

        Returns:
            Result message with the new comment ID
        """
        try:
            client = await get_outline_client()

            data = {
                "documentId": document_id,
                "text": text,
            }

            if parent_comment_id:
                data["parentCommentId"] = parent_comment_id

            response = await client.post("comments.create", data)
            comment = response.get("data", {})

            if not comment:
                return "Failed to create comment."

            comment_id = comment.get("id", "unknown")

            if parent_comment_id:
                return f"Reply added successfully (ID: {comment_id})"
            else:
                return f"Comment added successfully (ID: {comment_id})"
        except OutlineClientError as e:
            return f"Error adding comment: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
