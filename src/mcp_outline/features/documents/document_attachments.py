"""
Document attachment tools for the MCP Outline server.

This module provides MCP tools for fetching and discovering attachments
(PDFs, images, etc.) in Outline documents.
"""

import base64
import re
from typing import List, Tuple

from mcp.types import ToolAnnotations

from mcp_outline.features.documents.common import (
    OutlineClientError,
    get_outline_client,
)

# Pattern for /api/attachments.redirect?id=<uuid>
ATTACHMENT_PATTERN = re.compile(
    r"/api/attachments\.redirect\?id="
    r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"
)


def _parse_attachment_ids(text: str) -> List[Tuple[str, str]]:
    """Extract attachment IDs and context from document text.

    Args:
        text: The document text (markdown/content) to parse.

    Returns:
        List of (attachment_id, context_snippet) tuples.
    """
    results: List[Tuple[str, str]] = []
    seen: set[str] = set()

    for match in ATTACHMENT_PATTERN.finditer(text):
        attachment_id = match.group(1)
        if attachment_id in seen:
            continue
        seen.add(attachment_id)

        start = max(0, match.start() - 40)
        end = min(len(text), match.end() + 40)
        snippet = text[start:end].replace("\n", " ").strip()
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
        results.append((attachment_id, snippet))

    return results


def _format_attachment_list(
    document_title: str, attachments: List[Tuple[str, str]]
) -> str:
    """Format attachment list for display."""
    if not attachments:
        return f"Document '{document_title}': No attachments found."

    lines = [
        f"Document '{document_title}': {len(attachments)} attachment(s)\n"
    ]
    for i, (aid, snippet) in enumerate(attachments, 1):
        lines.append(f"{i}. ID: {aid}")
        lines.append(f"   Context: {snippet}\n")
    return "\n".join(lines).rstrip()


def register_tools(mcp) -> None:
    """
    Register document attachment tools with the MCP server.

    Args:
        mcp: The FastMCP server instance
    """

    @mcp.tool(
        annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True)
    )
    async def get_attachment_url(attachment_id: str) -> str:
        """
        Resolve an attachment ID to a downloadable URL.

        Calls attachments.redirect and returns the final URL after the
        redirect. Allows clients/agents to fetch the file themselves.

        Use this tool when you need to:
        - Get a direct URL to download an attachment
        - Share or reference an attachment URL
        - Let another system fetch the file

        Args:
            attachment_id: The attachment UUID

        Returns:
            The redirect URL (signed download URL)
        """
        try:
            client = await get_outline_client()
            url = await client.get_attachment_redirect_url(attachment_id)
            return url
        except OutlineClientError as e:
            return f"Error: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool(
        annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True)
    )
    async def fetch_attachment(attachment_id: str) -> str:
        """
        Fetch attachment content and return it as base64.

        Calls attachments.redirect, follows the redirect, and returns the
        raw file content encoded as base64. Useful for images and files
        that agents can process.

        Use this tool when you need to:
        - Read PDF content from Outline documents
        - Process embedded images
        - Analyze files referenced in documents
        - Enable AI tools to work with all document content

        Args:
            attachment_id: The attachment UUID

        Returns:
            Multi-line string with Content-Type, Content-Length, and
            Content-Base64
        """
        try:
            client = await get_outline_client()
            content, content_type = await client.fetch_attachment_content(
                attachment_id
            )
            b64 = base64.b64encode(content).decode("ascii")
            return (
                f"Content-Type: {content_type}\n"
                f"Content-Length: {len(content)}\n"
                f"Content-Base64: {b64}"
            )
        except OutlineClientError as e:
            return f"Error: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool(
        annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True)
    )
    async def list_document_attachments(document_id: str) -> str:
        """
        List attachment IDs referenced in a document.

        Parses document content for attachment references (e.g.
        /api/attachments.redirect?id=<uuid>) and returns a list of
        attachment IDs with context snippets.

        Use this tool when you need to:
        - Discover attachments within a document
        - Find attachment IDs for use with get_attachment_url or
          fetch_attachment
        - Audit what files a document references

        Args:
            document_id: The document ID to scan

        Returns:
            Formatted list of attachment IDs and context
        """
        try:
            client = await get_outline_client()
            document = await client.get_document(document_id)
            title = document.get("title", "Untitled Document")
            text = document.get("text", "")
            attachments = _parse_attachment_ids(text)
            return _format_attachment_list(title, attachments)
        except OutlineClientError as e:
            return f"Error: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
