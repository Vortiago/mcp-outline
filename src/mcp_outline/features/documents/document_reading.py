"""
Document reading tools for the MCP Outline server.

This module provides MCP tools for reading document content
with optional pagination, and shared helpers used by
navigation and editing modules.
"""

import re
from typing import List, Tuple

from mcp.types import ToolAnnotations

from mcp_outline.features.documents.common import (
    OutlineClientError,
    get_outline_client,
    get_resolved_api_key,
)
from mcp_outline.utils.document_cache import (
    CachedDocument,
    get_document_cache,
)


def format_lines_with_numbers(lines: List[str], start: int) -> str:
    """Format lines with line numbers (cat -n style)."""
    width = len(str(start + len(lines)))
    parts = []
    for i, line in enumerate(lines):
        num = start + i
        parts.append(f"{num:>{width}}\t{line}")
    return "\n".join(parts)


def parse_headings(
    lines: List[str],
) -> List[Tuple[int, int, str]]:
    """Parse markdown headings from lines.

    Returns list of (line_number, level, heading_text)
    tuples. Line numbers are 0-based.
    """
    headings: List[Tuple[int, int, str]] = []
    in_code_block = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if match:
            level = len(match.group(1))
            text = match.group(2).strip()
            headings.append((i, level, text))
    return headings


async def get_cached_or_fetch(
    document_id: str,
) -> CachedDocument:
    """Get document from cache or fetch from API.

    Returns:
        CachedDocument instance.

    Raises:
        OutlineClientError: If API call fails.
    """
    api_key = get_resolved_api_key()
    cache = get_document_cache()
    doc = await cache.get(api_key, document_id)
    if doc is not None:
        return doc
    client = await get_outline_client()
    data = await client.get_document(document_id)
    return await cache.put(api_key, document_id, data)


def register_tools(mcp) -> None:
    """
    Register document reading tools with the MCP server.

    Args:
        mcp: The FastMCP server instance
    """

    @mcp.tool(
        annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
        meta={
            "endpoint": "documents.info",
            "min_role": "viewer",
        },
    )
    async def read_document(
        document_id: str,
        offset: int = 0,
        limit: int = 0,
    ) -> str:
        """
        Retrieves and displays document content, optionally
        paginated by line range.

        Use this tool when you need to:
        - Access the complete content of a specific document
        - Read a specific range of lines from a large
          document
        - Review document information in detail
        - Quote or reference document content

        When offset or limit are set, output includes line
        numbers and a metadata header showing the range.
        When both are 0 (default), the full document is
        returned in the original format for backward
        compatibility.

        Args:
            document_id: The document ID to retrieve
            offset: 0-based line number to start from
                (default: 0)
            limit: Number of lines to return; 0 means all
                lines (default: 0)

        Returns:
            Formatted string containing the document title
            and content
        """
        try:
            doc = await get_cached_or_fetch(document_id)
            paginating = offset != 0 or limit != 0

            if not paginating:
                output = f"# {doc.title}\n\n{doc.text}"
            else:
                lines = doc.text.split("\n")
                total = len(lines)
                start = min(offset, total)
                end = min(start + limit, total) if limit > 0 else total
                selected = lines[start:end]
                numbered = format_lines_with_numbers(selected, start)
                output = (
                    f"# {doc.title}\n"
                    f"Lines {start}-{end - 1}"
                    f" of {total} total\n\n"
                    f"{numbered}"
                )

            if doc.url:
                output += f"\n\nURL: {doc.url}"
            return output
        except OutlineClientError as e:
            return f"Error reading document: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool(
        annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
        meta={
            "endpoint": "documents.export",
            "min_role": "viewer",
        },
    )
    async def export_document(document_id: str) -> str:
        """
        Exports a document as plain markdown text.

        Use this tool when you need to:
        - Get clean markdown content without formatting
        - Extract document content for external use
        - Process document content in another application
        - Share document content outside Outline

        Args:
            document_id: The document ID to export

        Returns:
            Document content in markdown format without
            additional formatting
        """
        try:
            client = await get_outline_client()
            response = await client.post(
                "documents.export", {"id": document_id}
            )
            return response.get("data", "No content available")
        except OutlineClientError as e:
            return f"Error exporting document: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
