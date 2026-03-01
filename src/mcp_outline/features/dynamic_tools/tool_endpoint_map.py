# Mapping of MCP tool names to the Outline API endpoint used
# for probing access.  The probe POSTs a body with a fake UUID
# to each endpoint and checks for 401.
#
# NOTE: this is a *probing* map, not a documentation map.
# Some endpoints cannot be reliably probed, so tools are mapped
# to a proxy endpoint instead:
#
# - ``attachments.redirect`` validates + looks up the resource
#   *before* checking auth, so it never returns 401 for an
#   invalid key.  Attachment tools are mapped to
#   ``documents.info`` instead — if the key can read documents
#   it can access attachments.
#
# - ``collections.export`` and ``collections.export_all`` have
#   aggressive rate limits that fire *before* auth.  Once
#   exhausted, probes get 429 regardless of key validity.
#   Mapped to ``collections.list`` instead — if the key can
#   list collections it can export them.
#
# Limitation: a key scoped to only one of the proxy endpoints
# (e.g. ``attachments.redirect`` but not ``documents.info``)
# would have its tools hidden.  Since the MCP client (an LLM)
# can only call tools visible in the tool list, those tools
# become inaccessible even though the key technically permits
# them.  These are unlikely scope combinations in practice.
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
    # export endpoints use collections.list as probe — see NOTE above.
    "export_collection": "collections.list",
    "export_all_collections": "collections.list",
    "list_document_comments": "comments.list",
    "get_comment": "comments.info",
    "get_document_backlinks": "documents.list",
    # Attachment tools use documents.info as probe — see NOTE above.
    "get_attachment_url": "documents.info",
    "fetch_attachment": "documents.info",
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
