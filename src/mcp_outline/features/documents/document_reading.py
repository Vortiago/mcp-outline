"""
Document reading tools for the MCP Outline server.

This module provides MCP tools for reading document content.
"""

import re
from typing import Any, Dict, List, Optional

from mcp.types import CallToolResult, ToolAnnotations

from mcp_outline.features.documents.common import (
    OutlineClientError,
    get_outline_client,
)
from mcp_outline.utils.response_handler import create_tool_response


def _format_document_content(document: Dict[str, Any]) -> str:
    """Format document content into readable text."""
    title = document.get("title", "Untitled Document")
    text = document.get("text", "")

    return f"""# {title}

{text}
"""


def _parse_headings_safely(markdown: str) -> List[Dict[str, Any]]:
    """
    Extract headings from markdown, skipping # inside code blocks.

    Args:
        markdown: The markdown text to parse

    Returns:
        List of dicts with 'level', 'text', and 'line' keys
    """
    headings: List[Dict[str, Any]] = []

    # Split into lines for processing
    lines = markdown.split("\n")
    in_code_block = False
    line_num = 0

    for line in lines:
        line_num += 1

        # Track code block state
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue

        # Skip if inside code block
        if in_code_block:
            continue

        # Match headings (# to ####, limit to H1-H4 for clarity)
        match = re.match(r"^(#{1,4})\s+(.+)$", line)
        if match:
            level = len(match.group(1))
            text = match.group(2).strip()
            headings.append({"level": level, "text": text, "line": line_num})

    return headings


def _extract_section(markdown: str, heading: str) -> Optional[str]:
    """
    Extract content from a heading until the next same-level or higher heading.

    Args:
        markdown: The full markdown text
        heading: The heading text to find (case-insensitive)

    Returns:
        The section content, or None if heading not found
    """
    lines = markdown.split("\n")
    in_code_block = False
    found_heading = False
    found_level = 0
    section_lines: List[str] = []

    for line in lines:
        # Track code block state
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            if found_heading:
                section_lines.append(line)
            continue

        # If inside code block, just collect lines if we found heading
        if in_code_block:
            if found_heading:
                section_lines.append(line)
            continue

        # Check for heading
        match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if match:
            level = len(match.group(1))
            text = match.group(2).strip()

            if found_heading:
                # Check if this heading ends our section
                # (same level or higher = smaller number)
                if level <= found_level:
                    break
                else:
                    # Sub-heading, include it
                    section_lines.append(line)
            elif text.lower() == heading.lower():
                # Found our target heading
                found_heading = True
                found_level = level
                # Don't include the heading itself in the content
        elif found_heading:
            section_lines.append(line)

    if not found_heading:
        return None

    # Clean up: remove leading/trailing empty lines
    content = "\n".join(section_lines).strip()
    return content if content else "Section has no content."


def _format_outline(
    title: str, headings: List[Dict[str, Any]], word_count: int
) -> str:
    """
    Format headings as an indented table of contents.

    Args:
        title: Document title
        headings: List of heading dicts
        word_count: Approximate word count of document

    Returns:
        Formatted outline string
    """
    output = f"# {title}\n\n"
    output += f"Word count: ~{word_count:,}\n\n"
    output += "## Table of Contents\n\n"

    if not headings:
        output += "_No headings found in document._\n"
        return output

    for h in headings:
        indent = "  " * (h["level"] - 1)
        output += f"{indent}- {h['text']}\n"

    return output


def register_tools(mcp) -> None:
    """
    Register document reading tools with the MCP server.

    Args:
        mcp: The FastMCP server instance
    """

    @mcp.tool(
        annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True)
    )
    async def read_document(document_id: str) -> CallToolResult:
        """
        Retrieves and displays the full content of a document.

        Use this tool when you need to:
        - Access the complete content of a specific document
        - Review document information in detail
        - Quote or reference document content
        - Analyze document contents

        Args:
            document_id: The document ID to retrieve

        Returns:
            Formatted string containing the document title and content
        """
        try:
            client = await get_outline_client()
            document = await client.get_document(document_id)
            return create_tool_response(
                _format_document_content(document),
                {
                    "document_id": document_id,
                    "title": document.get("title", "Untitled"),
                    "text": document.get("text", ""),
                },
            )
        except OutlineClientError as e:
            return create_tool_response(
                f"Error reading document: {str(e)}",
                {"error": str(e), "document_id": document_id},
            )
        except Exception as e:
            return create_tool_response(
                f"Unexpected error: {str(e)}",
                {"error": str(e), "document_id": document_id},
            )

    @mcp.tool(
        annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True)
    )
    async def export_document(document_id: str) -> CallToolResult:
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
            Document content in markdown format without additional formatting
        """
        try:
            client = await get_outline_client()
            response = await client.post(
                "documents.export", {"id": document_id}
            )
            content = response.get("data", "No content available")
            return create_tool_response(
                content,
                {
                    "document_id": document_id,
                    "content": content,
                    "format": "markdown",
                },
            )
        except OutlineClientError as e:
            return create_tool_response(
                f"Error exporting document: {str(e)}",
                {"error": str(e), "document_id": document_id},
            )
        except Exception as e:
            return create_tool_response(
                f"Unexpected error: {str(e)}",
                {"error": str(e), "document_id": document_id},
            )

    @mcp.tool(
        annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True)
    )
    async def get_document_outline(document_id: str) -> CallToolResult:
        """
        Returns the hierarchical structure (table of contents) of a document.

        IMPORTANT: This tool is optimized for context efficiency. For large
        documents, it returns only the headings/TOC structure instead of the
        full content, saving significant context space. For small documents
        (<1000 characters), it automatically returns the full content since
        the overhead is not worth it.

        Use this tool when you need to:
        - Understand what sections a document contains
        - Find the heading for a specific section to read
        - Get a quick overview of document structure
        - Decide which section(s) to read with read_document_section
        - Preview document organization before reading full content

        Args:
            document_id: The document ID to get outline for

        Returns:
            Document title, table of contents, and word count
        """
        try:
            client = await get_outline_client()
            document = await client.get_document(document_id)
            title = document.get("title", "Untitled Document")
            markdown = document.get("text", "")

            # For small docs, return full content (overhead not worth it)
            if len(markdown) < 1000:
                return create_tool_response(
                    f"# {title}\n\n{markdown}",
                    {
                        "title": title,
                        "full_content": True,
                        "text": markdown,
                        "document_id": document_id,
                    },
                )

            # Parse headings and format outline
            headings = _parse_headings_safely(markdown)
            word_count = len(markdown.split())

            return create_tool_response(
                _format_outline(title, headings, word_count),
                {
                    "title": title,
                    "headings": headings,
                    "word_count": word_count,
                    "document_id": document_id,
                },
            )
        except OutlineClientError as e:
            return create_tool_response(
                f"Error getting document outline: {str(e)}",
                {"error": str(e)},
            )
        except Exception as e:
            return create_tool_response(
                f"Unexpected error: {str(e)}",
                {"error": str(e)},
            )

    @mcp.tool(
        annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True)
    )
    async def read_document_section(
        document_id: str, heading: str
    ) -> CallToolResult:
        """
        Reads a specific section of a document by its heading.

        IMPORTANT: This tool is optimized for context efficiency. Instead of
        loading the entire document, it extracts only the content under a
        specific heading (until the next same-level or higher heading). This
        can save significant context when you only need part of a large
        document.

        Use this tool when you need to:
        - Read only a relevant portion of a large document
        - Get content under a specific heading found via get_document_outline
        - Save context by not loading the full document
        - Extract information from a known section

        Args:
            document_id: The document ID to read from
            heading: The exact heading text to extract (case-insensitive)

        Returns:
            The content under the specified heading
        """
        try:
            client = await get_outline_client()
            document = await client.get_document(document_id)
            markdown = document.get("text", "")

            section = _extract_section(markdown, heading)
            if section is None:
                # Heading not found - provide helpful error with options
                headings = _parse_headings_safely(markdown)
                available = [h["text"] for h in headings]

                error_msg = f"Heading '{heading}' not found."
                if available:
                    error_msg += "\n\nAvailable headings:\n"
                    error_msg += "\n".join(f"- {h}" for h in available)
                else:
                    error_msg += "\n\nNo headings found in this document."

                return create_tool_response(
                    error_msg,
                    {
                        "error": "heading_not_found",
                        "available_headings": available,
                        "document_id": document_id,
                    },
                )

            return create_tool_response(
                f"## {heading}\n\n{section}",
                {
                    "heading": heading,
                    "content": section,
                    "document_id": document_id,
                },
            )
        except OutlineClientError as e:
            return create_tool_response(
                f"Error reading document section: {str(e)}",
                {"error": str(e)},
            )
        except Exception as e:
            return create_tool_response(
                f"Unexpected error: {str(e)}",
                {"error": str(e)},
            )
