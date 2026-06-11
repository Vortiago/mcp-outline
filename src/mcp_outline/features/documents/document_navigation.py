"""
Document navigation tools for the MCP Outline server.

This module provides tools for navigating large documents
by heading structure: table of contents and section reading.
"""

from typing import List, Tuple

from mcp.types import ToolAnnotations

from mcp_outline.features.documents.common import (
    OutlineClientError,
)
from mcp_outline.features.documents.document_reading import (
    format_lines_with_numbers,
    get_cached_or_fetch,
    parse_headings,
    staged_changes_notice,
)

# Cap grep-style output so broad queries stay token-safe
_MAX_CONTENT_MATCHES = 50


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
            return "\n".join(parts) + staged_changes_notice(doc)
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

            # Accept headings as the TOC displays them
            # (e.g. "## Background"): strip the markdown
            # prefix before matching against heading text.
            needle = heading.strip().lstrip("#").strip().lower()
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
            return output + staged_changes_notice(doc)
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
    async def search_document_content(
        document_id: str,
        query: str,
        context_lines: int = 2,
    ) -> str:
        """
        Searches within a document for lines containing a
        text snippet (grep-style), returning matches with
        line numbers and surrounding context.

        Use this tool when you need to:
        - Locate specific text in a large document without
          reading it in full
        - Find the exact text and line number to build
          edit_document old_string values or
          read_document offsets

        Matching is case-insensitive per line. Line numbers
        are 0-based and valid as read_document offsets.

        Args:
            document_id: The document ID to search
            query: Text snippet to find (case-insensitive)
            context_lines: Lines of context around each
                match (default: 2, must be non-negative)

        Returns:
            Matching lines with line numbers and context
        """
        if context_lines < 0:
            return "Error: context_lines must be non-negative."
        if not query:
            return "Error: query must not be empty."
        try:
            doc = await get_cached_or_fetch(document_id)
            lines = doc.text.split("\n")
            needle = query.lower()
            matches = [
                i for i, line in enumerate(lines) if needle in line.lower()
            ]

            if not matches:
                return (
                    f"No lines matching '{query}' in"
                    f" '{doc.title}'. Try a shorter or"
                    " different snippet, or"
                    " get_document_toc to browse structure."
                )

            shown = matches[:_MAX_CONTENT_MATCHES]
            last = len(lines) - 1
            blocks: List[Tuple[int, int]] = []
            block_start = max(0, shown[0] - context_lines)
            block_end = min(last, shown[0] + context_lines)
            for m in shown[1:]:
                start = max(0, m - context_lines)
                end = min(last, m + context_lines)
                if start <= block_end + 1:
                    block_end = max(block_end, end)
                else:
                    blocks.append((block_start, block_end))
                    block_start, block_end = start, end
            blocks.append((block_start, block_end))

            rendered = "\n--\n".join(
                format_lines_with_numbers(lines[s : e + 1], s)
                for s, e in blocks
            )
            header = f"# {doc.title}\n{len(matches)} match(es) for '{query}'"
            if len(matches) > len(shown):
                header += f" (showing first {len(shown)})"
            output = f"{header}\n\n{rendered}"
            return output + staged_changes_notice(doc)
        except OutlineClientError as e:
            return f"Error reading document: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
