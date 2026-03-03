# Mapping of MCP tool names to the Outline API endpoint used
# for scope-based access checks.  The scope matcher evaluates
# each endpoint against the API key's stored scopes using
# Outline's ``canAccess`` algorithm.
#
# To update: add new tools here when they are registered.
# A cross-check unit test verifies this map stays in sync with
# the tools registered by ``register_all``.
TOOL_ENDPOINT_MAP: dict[str, str] = {
    # --- Read tools (17) ---
    "read_document": "documents.info",
    "export_document": "documents.export",
    "search_documents": "documents.search",
    "get_document_id_from_title": "documents.search",
    "list_collections": "collections.list",
    "get_collection_structure": "collections.documents",
    "export_collection": "collections.export",
    "export_all_collections": "collections.export_all",
    "list_document_comments": "comments.list",
    "get_comment": "comments.info",
    "get_document_backlinks": "documents.list",
    "get_attachment_url": "attachments.redirect",
    "fetch_attachment": "attachments.redirect",
    "list_document_attachments": "documents.info",
    "list_archived_documents": "documents.archived",
    "list_trash": "documents.deleted",
    "ask_ai_about_documents": "documents.answerQuestion",
    # --- Write tools (16) ---
    "create_document": "documents.create",
    "update_document": "documents.update",
    "add_comment": "comments.create",
    "archive_document": "documents.archive",
    "unarchive_document": "documents.restore",
    "delete_document": "documents.delete",
    "restore_document": "documents.restore",
    "move_document": "documents.move",
    "create_collection": "collections.create",
    "update_collection": "collections.update",
    "delete_collection": "collections.delete",
    "batch_create_documents": "documents.create",
    "batch_update_documents": "documents.update",
    "batch_move_documents": "documents.move",
    "batch_archive_documents": "documents.archive",
    "batch_delete_documents": "documents.delete",
}
