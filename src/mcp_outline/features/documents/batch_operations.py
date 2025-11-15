"""
Batch document operations for the MCP Outline server.

This module provides MCP tools for performing operations on multiple
documents efficiently.
"""

from typing import Any, Dict, List, Optional

from mcp_outline.features.documents.common import (
    OutlineClientError,
    get_outline_client,
)


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


def register_tools(mcp) -> None:
    """
    Register batch operation tools with the MCP server.

    Args:
        mcp: The FastMCP server instance
    """

    @mcp.tool()
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

        results: List[Dict[str, Any]] = []
        succeeded = 0
        failed = 0

        try:
            client = await get_outline_client()

            for doc_id in document_ids:
                try:
                    document = await client.archive_document(doc_id)

                    if document:
                        results.append(
                            _create_result_entry(
                                doc_id,
                                "success",
                                title=document.get("title", "Untitled"),
                            )
                        )
                        succeeded += 1
                    else:
                        results.append(
                            _create_result_entry(
                                doc_id,
                                "failed",
                                error="No document returned from API",
                            )
                        )
                        failed += 1

                except OutlineClientError as e:
                    results.append(
                        _create_result_entry(doc_id, "failed", error=str(e))
                    )
                    failed += 1
                except Exception as e:
                    results.append(
                        _create_result_entry(
                            doc_id,
                            "failed",
                            error=f"Unexpected error: {str(e)}",
                        )
                    )
                    failed += 1

            return _format_batch_results(
                "archive", len(document_ids), succeeded, failed, results
            )

        except OutlineClientError as e:
            return f"Error initializing client: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool()
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

        results: List[Dict[str, Any]] = []
        succeeded = 0
        failed = 0

        try:
            client = await get_outline_client()

            for doc_id in document_ids:
                try:
                    # Build request data
                    data = {"id": doc_id}

                    if collection_id:
                        data["collectionId"] = collection_id

                    if parent_document_id:
                        data["parentDocumentId"] = parent_document_id

                    response = await client.post("documents.move", data)

                    if response.get("data"):
                        # Get document title for success message
                        doc_data = response.get("data", {})
                        results.append(
                            _create_result_entry(
                                doc_id,
                                "success",
                                title=doc_data.get("title", "Untitled"),
                            )
                        )
                        succeeded += 1
                    else:
                        results.append(
                            _create_result_entry(
                                doc_id,
                                "failed",
                                error="Failed to move document",
                            )
                        )
                        failed += 1

                except OutlineClientError as e:
                    results.append(
                        _create_result_entry(doc_id, "failed", error=str(e))
                    )
                    failed += 1
                except Exception as e:
                    results.append(
                        _create_result_entry(
                            doc_id,
                            "failed",
                            error=f"Unexpected error: {str(e)}",
                        )
                    )
                    failed += 1

            return _format_batch_results(
                "move", len(document_ids), succeeded, failed, results
            )

        except OutlineClientError as e:
            return f"Error initializing client: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool()
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

        results: List[Dict[str, Any]] = []
        succeeded = 0
        failed = 0

        try:
            client = await get_outline_client()

            for doc_id in document_ids:
                try:
                    if permanent:
                        success = await client.permanently_delete_document(
                            doc_id
                        )
                        if success:
                            results.append(
                                _create_result_entry(
                                    doc_id,
                                    "success",
                                    title="Permanently deleted",
                                )
                            )
                            succeeded += 1
                        else:
                            results.append(
                                _create_result_entry(
                                    doc_id,
                                    "failed",
                                    error="Permanent deletion failed",
                                )
                            )
                            failed += 1
                    else:
                        # Get document details before deleting
                        document = await client.get_document(doc_id)
                        doc_title = document.get("title", "Untitled")

                        # Move to trash
                        response = await client.post(
                            "documents.delete", {"id": doc_id}
                        )

                        if response.get("success", False):
                            results.append(
                                _create_result_entry(
                                    doc_id, "success", title=doc_title
                                )
                            )
                            succeeded += 1
                        else:
                            results.append(
                                _create_result_entry(
                                    doc_id,
                                    "failed",
                                    error="Failed to move to trash",
                                )
                            )
                            failed += 1

                except OutlineClientError as e:
                    results.append(
                        _create_result_entry(doc_id, "failed", error=str(e))
                    )
                    failed += 1
                except Exception as e:
                    results.append(
                        _create_result_entry(
                            doc_id,
                            "failed",
                            error=f"Unexpected error: {str(e)}",
                        )
                    )
                    failed += 1

            operation = "permanently delete" if permanent else "delete"
            return _format_batch_results(
                operation, len(document_ids), succeeded, failed, results
            )

        except OutlineClientError as e:
            return f"Error initializing client: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool()
    async def batch_update_documents(updates: List[Dict[str, Any]]) -> str:
        """
        Updates multiple documents with different changes.

        This tool processes each update sequentially, continuing even if
        individual operations fail. Rate limiting is handled automatically.

        Each update dictionary should contain:
        - id (required): Document ID to update
        - title (optional): New title
        - text (optional): New content
        - append (optional): If True, appends text instead of replacing

        Use this tool when you need to:
        - Update multiple documents with different changes
        - Batch edit document titles or content
        - Append content to multiple documents

        Note: For Mermaid diagrams, use ```mermaidjs (not ```mermaid)
        as the code fence language identifier for proper rendering.

        Recommended batch size: 10-50 documents per operation

        Args:
            updates: List of update specifications, each containing id and
                optional title, text, and append fields

        Returns:
            Summary of batch operation with success/failure details
        """
        if not updates:
            return "Error: No updates provided."

        results: List[Dict[str, Any]] = []
        succeeded = 0
        failed = 0

        try:
            client = await get_outline_client()

            for update_spec in updates:
                doc_id = update_spec.get("id")

                if not doc_id:
                    results.append(
                        _create_result_entry(
                            "unknown",
                            "failed",
                            error="Missing document ID in update spec",
                        )
                    )
                    failed += 1
                    continue

                try:
                    # Build update data
                    data: Dict[str, Any] = {"id": doc_id}

                    if "title" in update_spec:
                        data["title"] = update_spec["title"]

                    if "text" in update_spec:
                        data["text"] = update_spec["text"]
                        data["append"] = update_spec.get("append", False)

                    response = await client.post("documents.update", data)
                    document = response.get("data", {})

                    if document:
                        results.append(
                            _create_result_entry(
                                doc_id,
                                "success",
                                title=document.get("title", "Untitled"),
                            )
                        )
                        succeeded += 1
                    else:
                        results.append(
                            _create_result_entry(
                                doc_id,
                                "failed",
                                error="Failed to update document",
                            )
                        )
                        failed += 1

                except OutlineClientError as e:
                    results.append(
                        _create_result_entry(doc_id, "failed", error=str(e))
                    )
                    failed += 1
                except Exception as e:
                    results.append(
                        _create_result_entry(
                            doc_id,
                            "failed",
                            error=f"Unexpected error: {str(e)}",
                        )
                    )
                    failed += 1

            return _format_batch_results(
                "update", len(updates), succeeded, failed, results
            )

        except OutlineClientError as e:
            return f"Error initializing client: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool()
    async def batch_create_documents(documents: List[Dict[str, Any]]) -> str:
        """
        Creates multiple documents in a single batch operation.

        This tool processes each creation sequentially, continuing even if
        individual operations fail. Rate limiting is handled automatically.

        Each document dictionary should contain:
        - title (required): Document title
        - collection_id (required): Collection ID to create in
        - text (optional): Markdown content
        - parent_document_id (optional): Parent document for nesting
        - publish (optional): Whether to publish immediately (default: True)

        Use this tool when you need to:
        - Create multiple documents at once
        - Bulk import content into collections
        - Set up document structures efficiently

        Note: For Mermaid diagrams, use ```mermaidjs (not ```mermaid)
        as the code fence language identifier for proper rendering.

        Recommended batch size: 10-50 documents per operation

        Args:
            documents: List of document specifications, each containing
                title, collection_id, and optional text, parent_document_id,
                and publish fields

        Returns:
            Summary of batch operation with created document IDs and
            success/failure details
        """
        if not documents:
            return "Error: No documents provided."

        results: List[Dict[str, Any]] = []
        succeeded = 0
        failed = 0
        created_ids: List[str] = []

        try:
            client = await get_outline_client()

            for doc_spec in documents:
                # Validate required fields
                if "title" not in doc_spec:
                    results.append(
                        _create_result_entry(
                            "unknown",
                            "failed",
                            error="Missing required field: title",
                        )
                    )
                    failed += 1
                    continue

                if "collection_id" not in doc_spec:
                    results.append(
                        _create_result_entry(
                            "unknown",
                            "failed",
                            error="Missing required field: collection_id",
                        )
                    )
                    failed += 1
                    continue

                try:
                    # Build create data
                    data = {
                        "title": doc_spec["title"],
                        "collectionId": doc_spec["collection_id"],
                        "text": doc_spec.get("text", ""),
                        "publish": doc_spec.get("publish", True),
                    }

                    if "parent_document_id" in doc_spec:
                        data["parentDocumentId"] = doc_spec[
                            "parent_document_id"
                        ]

                    response = await client.post("documents.create", data)
                    document = response.get("data", {})

                    if document:
                        doc_id = document.get("id", "unknown")
                        doc_title = document.get("title", "Untitled")
                        created_ids.append(doc_id)
                        results.append(
                            _create_result_entry(
                                doc_id, "success", title=doc_title
                            )
                        )
                        succeeded += 1
                    else:
                        results.append(
                            _create_result_entry(
                                "unknown",
                                "failed",
                                error="Failed to create document",
                            )
                        )
                        failed += 1

                except OutlineClientError as e:
                    results.append(
                        _create_result_entry("unknown", "failed", error=str(e))
                    )
                    failed += 1
                except Exception as e:
                    results.append(
                        _create_result_entry(
                            "unknown",
                            "failed",
                            error=f"Unexpected error: {str(e)}",
                        )
                    )
                    failed += 1

            # Format results with created IDs
            result_text = _format_batch_results(
                "create", len(documents), succeeded, failed, results
            )

            # Add created IDs section if any succeeded
            if created_ids:
                result_text += "\n\nCreated Document IDs:\n"
                for doc_id in created_ids:
                    result_text += f"  - {doc_id}\n"

            return result_text

        except OutlineClientError as e:
            return f"Error initializing client: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
