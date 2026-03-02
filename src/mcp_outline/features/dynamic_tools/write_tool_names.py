# ------------------------------------------------------------------
# Write-tool registry
# ------------------------------------------------------------------
# Every tool whose ``readOnlyHint`` annotation is ``False``.
# A cross-check unit test verifies this set stays in sync.
WRITE_TOOL_NAMES: frozenset = frozenset(
    {
        # document_content
        "create_document",
        "update_document",
        "add_comment",
        # document_lifecycle
        "archive_document",
        "unarchive_document",
        "delete_document",
        "restore_document",
        # document_organization
        "move_document",
        # collection_tools
        "create_collection",
        "update_collection",
        "delete_collection",
        # batch_operations
        "batch_archive_documents",
        "batch_move_documents",
        "batch_delete_documents",
        "batch_update_documents",
        "batch_create_documents",
    }
)
