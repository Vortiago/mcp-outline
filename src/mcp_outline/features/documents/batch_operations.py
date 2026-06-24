"""
Batch document operations for the MCP Outline server.

This module provides MCP tools for performing operations on multiple
documents efficiently.
"""

from typing import Any, Awaitable, Callable, Dict, List, Optional, TypeVar

from mcp.types import ToolAnnotations

from mcp_outline.features.documents.common import (
    OutlineClientError,
    get_outline_client,
    get_resolved_api_key,
)
from mcp_outline.features.documents.models import (
    BatchCreateItem,
    BatchUpdateItem,
)
from mcp_outline.utils.document_cache import get_document_cache
from mcp_outline.utils.outline_client import OutlineClient


def _create_result_entry(
    doc_id: str,
    status: str,
    title: Optional[str] = None,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a standardized result entry for batch operations.

    Args:
        doc_id: The document ID
        status: Status of the operation ('success' or 'failed')
        title: Optional document title (for successful operations)
        error: Optional error message (for failed operations)

    Returns:
        Dictionary containing result information
    """
    result: Dict[str, Any] = {"id": doc_id, "status": status}

    if title:
        result["title"] = title

    if error:
        result["error"] = error

    return result


def _format_batch_results(
    operation: str,
    total: int,
    succeeded: int,
    failed: int,
    results: List[Dict[str, Any]],
) -> str:
    """
    Format batch operation results into a user-friendly string.

    Args:
        operation: The operation name (e.g., 'archive', 'move', 'delete')
        total: Total number of operations attempted
        succeeded: Number of successful operations
        failed: Number of failed operations
        results: List of individual operation results

    Returns:
        Formatted string containing batch operation summary
    """
    # Header with summary
    lines = [
        f"Batch {operation.title()} Results:",
        f"- Total: {total}",
        f"- Succeeded: {succeeded}",
        f"- Failed: {failed}",
        "",
    ]

    # Short summary if all succeeded
    if failed == 0 and succeeded > 0:
        lines.append(f"✓ All {succeeded} documents {operation}d successfully.")
        return "\n".join(lines)

    # Short summary if all failed
    if succeeded == 0 and failed > 0:
        lines.append(f"✗ All {failed} operations failed.")
        lines.append("")

    # Add details section
    if results:
        lines.append("Details:")

        # Group by status for cleaner output
        successes = [r for r in results if r["status"] == "success"]
        failures = [r for r in results if r["status"] == "failed"]

        # Show successful operations
        if successes:
            for result in successes:
                title = result.get("title", "Untitled")
                doc_id = result["id"]
                lines.append(f"  ✓ {doc_id} - {title}")

        # Show failed operations with error details
        if failures:
            if successes:
                lines.append("")  # Blank line between sections
            for result in failures:
                doc_id = result["id"]
                error = result.get("error", "Unknown error")
                lines.append(f"  ✗ {doc_id} - Error: {error}")

    return "\n".join(lines)


T = TypeVar("T")


async def _run_batch(
    items: List[T],
    operation_label: str,
    op: Callable[[OutlineClient, T], Awaitable[Dict[str, Any]]],
    *,
    id_of: Callable[[T], str] = str,
) -> str:
    """
    Run ``op`` over ``items`` with per-item error isolation.

    Owns client acquisition, iteration, per-item error isolation,
    success/failure tallying, and result formatting. Each ``op``
    returns a result entry (success or expected failure); a raised
    exception is converted into a failure entry keyed by ``id_of``.

    Args:
        items: Items to process (document IDs or spec objects).
        operation_label: Verb shown in the summary (e.g. ``archive``).
        op: Async per-item operation returning a result entry from
            ``_create_result_entry``.
        id_of: Maps an item to the id used when ``op`` raises before a
            result entry exists. Defaults to ``str`` (the item is its
            own id); batch create passes a constant because the id is
            only known after a successful call.

    Returns:
        Formatted batch operation summary.
    """
    results: List[Dict[str, Any]] = []

    try:
        client = await get_outline_client()

        for item in items:
            try:
                results.append(await op(client, item))
            except OutlineClientError as e:
                results.append(
                    _create_result_entry(id_of(item), "failed", error=str(e))
                )
            except Exception as e:
                results.append(
                    _create_result_entry(
                        id_of(item),
                        "failed",
                        error=f"Unexpected error: {str(e)}",
                    )
                )

        succeeded = sum(1 for r in results if r["status"] == "success")
        failed = len(results) - succeeded
        return _format_batch_results(
            operation_label, len(items), succeeded, failed, results
        )

    except OutlineClientError as e:
        return f"Error initializing client: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


def register_tools(mcp) -> None:
    """
    Register batch operation tools with the MCP server.

    Args:
        mcp: The FastMCP server instance
    """

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=True,
        ),
        meta={
            "endpoint": "documents.archive",
            "min_role": "member",
        },
    )
    async def batch_archive_documents(document_ids: List[str]) -> str:
        """
        Archives multiple documents in a single batch operation.

        This tool processes each document sequentially, continuing even if
        individual operations fail. Rate limiting is handled automatically
        by the Outline client.

        IMPORTANT: Archived documents are removed from collections but remain
        searchable. They won't appear in normal collection views but can
        still be found through search or the archive list.

        Use this tool when you need to:
        - Archive multiple outdated documents at once
        - Clean up collections in bulk
        - Batch hide documents without deleting them

        Recommended batch size: 10-50 documents per operation

        Args:
            document_ids: List of document IDs to archive

        Returns:
            Summary of batch operation with success/failure details
        """
        if not document_ids:
            return "Error: No document IDs provided."

        async def op(client: OutlineClient, doc_id: str) -> Dict[str, Any]:
            document = await client.archive_document(doc_id)
            if document:
                return _create_result_entry(
                    doc_id,
                    "success",
                    title=document.get("title", "Untitled"),
                )
            return _create_result_entry(
                doc_id, "failed", error="No document returned from API"
            )

        return await _run_batch(document_ids, "archive", op)

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=True,
        ),
        meta={
            "endpoint": "documents.move",
            "min_role": "member",
        },
    )
    async def batch_move_documents(
        document_ids: List[str],
        collection_id: Optional[str] = None,
        parent_document_id: Optional[str] = None,
    ) -> str:
        """
        Moves multiple documents to a different collection or parent.

        This tool processes each document sequentially, continuing even if
        individual operations fail. Rate limiting is handled automatically.

        IMPORTANT: When moving documents that have child documents, all
        children will move along with them, maintaining hierarchical
        structure. You must specify either collection_id or
        parent_document_id (or both).

        Use this tool when you need to:
        - Reorganize multiple documents at once
        - Move documents between collections in bulk
        - Restructure document hierarchies efficiently

        Recommended batch size: 10-50 documents per operation

        Args:
            document_ids: List of document IDs to move
            collection_id: Target collection ID (optional)
            parent_document_id: Target parent document ID (optional)

        Returns:
            Summary of batch operation with success/failure details
        """
        if not document_ids:
            return "Error: No document IDs provided."

        if collection_id is None and parent_document_id is None:
            return (
                "Error: You must specify either a collection_id or "
                "parent_document_id."
            )

        async def op(client: OutlineClient, doc_id: str) -> Dict[str, Any]:
            data = {"id": doc_id}
            if collection_id:
                data["collectionId"] = collection_id
            if parent_document_id:
                data["parentDocumentId"] = parent_document_id

            response = await client.post("documents.move", data)
            if response.get("data"):
                doc_data = response.get("data", {})
                return _create_result_entry(
                    doc_id,
                    "success",
                    title=doc_data.get("title", "Untitled"),
                )
            return _create_result_entry(
                doc_id, "failed", error="Failed to move document"
            )

        return await _run_batch(document_ids, "move", op)

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=True,
        ),
        meta={
            "endpoint": "documents.delete",
            "min_role": "member",
        },
    )
    async def batch_delete_documents(
        document_ids: List[str], permanent: bool = False
    ) -> str:
        """
        Deletes multiple documents, moving them to trash or permanently.

        This tool processes each document sequentially, continuing even if
        individual operations fail. Rate limiting is handled automatically.

        IMPORTANT: When permanent=False (the default), documents are moved
        to trash and retained for 30 days. Setting permanent=True bypasses
        trash and immediately deletes documents without recovery option.

        Use this tool when you need to:
        - Remove multiple unwanted documents at once
        - Clean up workspace in bulk
        - Permanently delete sensitive information (with permanent=True)

        Recommended batch size: 10-50 documents per operation

        Args:
            document_ids: List of document IDs to delete
            permanent: If True, permanently deletes without recovery option

        Returns:
            Summary of batch operation with success/failure details
        """
        if not document_ids:
            return "Error: No document IDs provided."

        async def op(client: OutlineClient, doc_id: str) -> Dict[str, Any]:
            if permanent:
                success = await client.permanently_delete_document(doc_id)
                if success:
                    return _create_result_entry(
                        doc_id, "success", title="Permanently deleted"
                    )
                return _create_result_entry(
                    doc_id, "failed", error="Permanent deletion failed"
                )

            # Get document details before deleting
            document = await client.get_document(doc_id)
            doc_title = document.get("title", "Untitled")

            # Move to trash
            response = await client.post("documents.delete", {"id": doc_id})
            if response.get("success", False):
                return _create_result_entry(doc_id, "success", title=doc_title)
            return _create_result_entry(
                doc_id, "failed", error="Failed to move to trash"
            )

        operation = "permanently delete" if permanent else "delete"
        return await _run_batch(document_ids, operation, op)

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=True,
        ),
        meta={
            "endpoint": "documents.update",
            "min_role": "member",
        },
    )
    async def batch_update_documents(
        updates: List[BatchUpdateItem],
    ) -> str:
        """
        Updates multiple documents with different changes.

        This tool processes each update sequentially,
        continuing even if individual operations fail.
        Rate limiting is handled automatically.

        Use this tool when you need to:
        - Update multiple documents with different changes
        - Batch edit document titles or content
        - Append content to multiple documents

        Note: For Mermaid diagrams, use ```mermaidjs
        (not ```mermaid) as the code fence language
        identifier for proper rendering.

        Recommended batch size: 10-50 documents per
        operation

        Args:
            updates: List of update specifications

        Returns:
            Summary of batch operation with
            success/failure details
        """
        if not updates:
            return "Error: No updates provided."

        async def op(
            client: OutlineClient, update_spec: BatchUpdateItem
        ) -> Dict[str, Any]:
            doc_id = update_spec.id
            data: Dict[str, Any] = {"id": doc_id}

            if update_spec.title is not None:
                data["title"] = update_spec.title

            if update_spec.text is not None:
                data["text"] = update_spec.text
                data["append"] = (
                    update_spec.append
                    if update_spec.append is not None
                    else False
                )

            response = await client.post("documents.update", data)
            document = response.get("data", {})

            if document:
                cache = get_document_cache()
                await cache.invalidate_for_write(
                    get_resolved_api_key(), doc_id
                )
                return _create_result_entry(
                    doc_id,
                    "success",
                    title=document.get("title", "Untitled"),
                )
            return _create_result_entry(
                doc_id, "failed", error="Failed to update document"
            )

        return await _run_batch(updates, "update", op, id_of=lambda u: u.id)

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=True,
        ),
        meta={
            "endpoint": "documents.create",
            "min_role": "member",
        },
    )
    async def batch_create_documents(
        documents: List[BatchCreateItem],
    ) -> str:
        """
        Creates multiple documents in a single batch
        operation.

        This tool processes each creation sequentially,
        continuing even if individual operations fail.
        Rate limiting is handled automatically.

        Use this tool when you need to:
        - Create multiple documents at once
        - Bulk import content into collections
        - Set up document structures efficiently

        Note: For Mermaid diagrams, use ```mermaidjs
        (not ```mermaid) as the code fence language
        identifier for proper rendering.

        Recommended batch size: 10-50 documents per
        operation

        Args:
            documents: List of document specifications

        Returns:
            Summary of batch operation with created
            document IDs and success/failure details
        """
        if not documents:
            return "Error: No documents provided."

        created_ids: List[str] = []

        async def op(
            client: OutlineClient, doc_spec: BatchCreateItem
        ) -> Dict[str, Any]:
            data: Dict[str, Any] = {
                "title": doc_spec.title,
                "collectionId": doc_spec.collection_id,
                "text": doc_spec.text or "",
                "publish": (
                    doc_spec.publish if doc_spec.publish is not None else True
                ),
            }
            if doc_spec.parent_document_id:
                data["parentDocumentId"] = doc_spec.parent_document_id

            response = await client.post("documents.create", data)
            document = response.get("data", {})

            if document:
                doc_id = document.get("id", "unknown")
                created_ids.append(doc_id)
                return _create_result_entry(
                    doc_id,
                    "success",
                    title=document.get("title", "Untitled"),
                )
            return _create_result_entry(
                "unknown", "failed", error="Failed to create document"
            )

        result_text = await _run_batch(
            documents, "create", op, id_of=lambda _: "unknown"
        )

        # Add created IDs section if any succeeded
        if created_ids:
            result_text += "\n\nCreated Document IDs:\n"
            for doc_id in created_ids:
                result_text += f"  - {doc_id}\n"

        return result_text
