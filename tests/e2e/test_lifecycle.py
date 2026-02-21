"""E2E tests for document lifecycle & organization tools."""

import pytest

from .helpers import _create_collection, _create_document, _text

pytestmark = [pytest.mark.e2e, pytest.mark.anyio]


async def test_archive_and_unarchive_document(mcp_session):
    """Archive, verify in list, then unarchive a document."""
    async with mcp_session() as session:
        coll_id = await _create_collection(session, "E2E Archive Coll")
        doc_id = await _create_document(
            session, coll_id, "Archive Test Doc", "Archived."
        )

        # archive_document
        result = await session.call_tool(
            "archive_document",
            arguments={"document_id": doc_id},
        )
        assert "archived successfully" in _text(result)

        # list_archived_documents
        result = await session.call_tool(
            "list_archived_documents",
        )
        text = _text(result)
        assert "# Archived Documents" in text
        assert doc_id in text

        # unarchive_document
        result = await session.call_tool(
            "unarchive_document",
            arguments={"document_id": doc_id},
        )
        assert "unarchived successfully" in _text(result)

        # verify readable
        result = await session.call_tool(
            "read_document",
            arguments={"document_id": doc_id},
        )
        assert "Archive Test Doc" in _text(result)


async def test_delete_and_restore_document(mcp_session):
    """Trash a doc, verify in trash, then restore."""
    async with mcp_session() as session:
        coll_id = await _create_collection(session, "E2E Trash Coll")
        doc_id = await _create_document(
            session, coll_id, "Trash Test Doc", "Trashed."
        )

        # delete_document (to trash)
        result = await session.call_tool(
            "delete_document",
            arguments={"document_id": doc_id},
        )
        assert "moved to trash" in _text(result)

        # list_trash
        result = await session.call_tool("list_trash")
        text = _text(result)
        assert "# Documents in Trash" in text
        assert doc_id in text

        # restore_document
        result = await session.call_tool(
            "restore_document",
            arguments={"document_id": doc_id},
        )
        assert "restored successfully" in _text(result)

        # verify readable
        result = await session.call_tool(
            "read_document",
            arguments={"document_id": doc_id},
        )
        assert "Trash Test Doc" in _text(result)


async def test_move_document(mcp_session):
    """Move a document between collections."""
    async with mcp_session() as session:
        src_id = await _create_collection(session, "E2E Move Source")
        tgt_id = await _create_collection(session, "E2E Move Target")
        doc_id = await _create_document(
            session, src_id, "Move Test Doc", "Will be moved."
        )

        result = await session.call_tool(
            "move_document",
            arguments={
                "document_id": doc_id,
                "collection_id": tgt_id,
            },
        )
        assert "moved successfully" in _text(result)

        result = await session.call_tool(
            "get_collection_structure",
            arguments={"collection_id": tgt_id},
        )
        assert "Move Test Doc" in _text(result)
