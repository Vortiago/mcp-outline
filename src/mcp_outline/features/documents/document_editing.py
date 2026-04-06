"""
Document editing tools for the MCP Outline server.

This module provides string-match editing with optional
staging, allowing surgical document changes without holding
the full document in context.
"""

from typing import List

from mcp.types import ToolAnnotations

from mcp_outline.features.documents.common import (
    OutlineClientError,
    get_outline_client,
    get_resolved_api_key,
)
from mcp_outline.features.documents.document_reading import (
    get_cached_or_fetch,
)
from mcp_outline.features.documents.models import (
    DocumentEdit,
)
from mcp_outline.utils.document_cache import get_document_cache


def _apply_edits(text: str, edits: List[DocumentEdit]) -> str:
    """Apply edits sequentially on a working copy.

    Raises ValueError if an edit fails (not found or
    multiple matches).
    """
    working = text
    for edit in edits:
        old = edit.old_string
        new = edit.new_string
        if not old:
            raise ValueError("Each edit must have a non-empty 'old_string'.")
        count = working.count(old)
        if count == 0:
            snippet = old[:80]
            raise ValueError(f"'{snippet}' not found in document.")
        if count > 1:
            snippet = old[:80]
            raise ValueError(
                f"'{snippet}' matches {count} locations."
                " Include more surrounding context."
            )
        working = working.replace(old, new, 1)
    return working


def register_tools(mcp) -> None:
    """
    Register document editing tools with the MCP server.

    Args:
        mcp: The FastMCP server instance
    """

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
    async def edit_document(
        document_id: str,
        edits: List[DocumentEdit],
        save: bool = True,
    ) -> str:
        """
        Edits a document using string-match replacement.

        Each edit finds a unique old_string in the document
        and replaces it with new_string. Edits are applied
        server-side — you never need to hold the full
        document in context.

        IMPORTANT: Batch all edits for a document into a
        single call when possible to minimize API calls.
        Each old_string must uniquely match one location in
        the document. Include surrounding context if needed
        to disambiguate.

        Edits are applied sequentially, so later edits can
        target text created by earlier edits in the same
        batch. If any edit fails, no changes are applied
        (all-or-nothing).

        By default (save=True), changes are pushed to
        Outline immediately. Set save=False to stage changes
        locally, then call save_document when done. This is
        useful for large rewrites spanning multiple calls.

        Args:
            document_id: The document ID to edit
            edits: List of edits to apply
            save: If True (default), push changes to Outline
                immediately. If False, stage locally.

        Returns:
            Summary of edits applied and save status
        """
        try:
            doc = await get_cached_or_fetch(document_id)

            new_text = _apply_edits(doc.text, edits)

            api_key = get_resolved_api_key()
            cache = get_document_cache()
            n = len(edits)

            if save:
                client = await get_outline_client()
                response = await client.post(
                    "documents.update",
                    {
                        "id": document_id,
                        "text": new_text,
                    },
                )
                result_doc = response.get("data", {})
                saved_text = result_doc.get("text", new_text)
                saved_title = result_doc.get("title", doc.title)
                # Evict all cached copies (other API keys)
                # then re-cache for the current user
                await cache.evict_document(document_id)
                await cache.put(
                    api_key,
                    document_id,
                    {
                        "title": saved_title,
                        "text": saved_text,
                        "url": doc.url,
                    },
                )
                return (
                    f"Applied {n} edit(s) to '{doc.title}'. Saved to Outline."
                )
            else:
                await cache.update_text(
                    api_key,
                    document_id,
                    new_text,
                    dirty=True,
                )
                return (
                    f"Applied {n} edit(s) to "
                    f"'{doc.title}'. "
                    f"Document has unsaved changes"
                    f" — call save_document to push"
                    f" to Outline."
                )
        except ValueError as e:
            return f"Edit failed: {str(e)} No edits were applied."
        except OutlineClientError as e:
            return f"Error editing document: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=True,
        ),
        meta={
            "endpoint": "documents.update",
            "min_role": "member",
        },
    )
    async def save_document(document_id: str) -> str:
        """
        Pushes staged (unsaved) edits to Outline.

        Use this after calling edit_document with save=False
        one or more times. If there are no unsaved changes,
        this tool does nothing.

        Args:
            document_id: The document ID to save

        Returns:
            Result message confirming save
        """
        try:
            api_key = get_resolved_api_key()
            cache = get_document_cache()
            doc = await cache.get(api_key, document_id)

            if doc is None or not doc.dirty:
                return "No unsaved changes for this document."

            client = await get_outline_client()
            response = await client.post(
                "documents.update",
                {"id": document_id, "text": doc.text},
            )
            result_doc = response.get("data", {})
            saved_text = result_doc.get("text", doc.text)
            saved_title = result_doc.get("title", doc.title)
            await cache.evict_document(document_id)
            await cache.put(
                api_key,
                document_id,
                {
                    "title": saved_title,
                    "text": saved_text,
                    "url": doc.url,
                },
            )
            return f"Document saved successfully: {saved_title}"
        except OutlineClientError as e:
            return f"Error saving document: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
