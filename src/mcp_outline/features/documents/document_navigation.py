"""
Document navigation tools for the MCP Outline server.

This module provides tools for navigating large documents
by heading structure: table of contents and section reading.
"""

from mcp.types import ToolAnnotations

from mcp_outline.features.documents.common import (
    OutlineClientError,
)
from mcp_outline.features.documents.document_reading import (
    format_lines_with_numbers,
    get_cached_or_fetch,
    parse_headings,
)


def register_tools(mcp) -> None:
    """
    Register document navigation tools with the MCP server.

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
    async def get_document_toc(document_id: str) -> str:
        """
        Returns the heading structure of a document as a
        table of contents with line numbers.

        Use this tool when you need to:
        - Understand the structure of a large document
        - Find specific sections before reading them
        - Navigate a document by its headings

        Line numbers in the output can be used with
        read_document(offset=...) or
        read_document_section(heading=...) to read specific
        parts.

        Args:
            document_id: The document ID

        Returns:
            Formatted table of contents with line numbers
        """
        try:
            doc = await get_cached_or_fetch(document_id)
            lines = doc.text.split("\n")
            headings = parse_headings(lines)

            if not headings:
                return (
                    f"# {doc.title} — Table of Contents"
                    "\n\nNo headings found in document."
                )

            total = len(lines)
            width = len(str(total))
            parts = [f"# {doc.title} — Table of Contents\n"]
            for line_num, level, text in headings:
                prefix = "#" * level
                parts.append(f"{line_num:>{width}}  {prefix} {text}")
            return "\n".join(parts)
        except OutlineClientError as e:
            return f"Error reading document: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool(
        annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
        meta={
            "endpoint": "documents.info",
            "min_role": "viewer",
        },
    )
    async def read_document_section(
        document_id: str,
        heading: str,
    ) -> str:
        """
        Reads a specific section of a document identified by
        heading match.

        Uses case-insensitive substring matching against
        headings. Returns the section content from the matched
        heading up to the next heading of the same or higher
        level, including all nested subsections.

        Use this tool when you need to:
        - Read a specific part of a large document
        - Focus on one section without loading everything
        - Navigate by heading name instead of line numbers

        Args:
            document_id: The document ID
            heading: Case-insensitive substring to match
                against headings (e.g. "arch" matches
                "## Architecture")

        Returns:
            Section content with line numbers
        """
        try:
            doc = await get_cached_or_fetch(document_id)
            lines = doc.text.split("\n")
            headings = parse_headings(lines)

            if not headings:
                return (
                    "No headings found in document. "
                    "Use read_document to read the "
                    "full content."
                )

            needle = heading.lower()
            matches = [
                (ln, lvl, txt)
                for ln, lvl, txt in headings
                if needle in txt.lower()
            ]

            if not matches:
                available = "\n".join(
                    f"  {'#' * lvl} {txt}" for _, lvl, txt in headings
                )
                return (
                    f"No heading matching '{heading}' "
                    f"found.\n\n"
                    f"Available headings:\n{available}"
                )

            if len(matches) > 1:
                ambiguous = "\n".join(
                    f"  Line {ln}: {'#' * lvl} {txt}"
                    for ln, lvl, txt in matches
                )
                return (
                    f"Multiple headings match "
                    f"'{heading}':\n{ambiguous}\n\n"
                    "Use a more specific heading "
                    "string."
                )

            start_line, start_level, matched_text = matches[0]
            end_line = len(lines)
            for ln, lvl, _ in headings:
                if ln > start_line and lvl <= start_level:
                    end_line = ln
                    break

            selected = lines[start_line:end_line]
            numbered = format_lines_with_numbers(selected, start_line)
            prefix = "#" * start_level
            total = len(lines)
            output = (
                f"# {doc.title}\n"
                f"Section: {prefix} {matched_text} "
                f"(lines {start_line}-{end_line - 1}"
                f" of {total} total)\n\n"
                f"{numbered}"
            )
            return output
        except OutlineClientError as e:
            return f"Error reading document: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
