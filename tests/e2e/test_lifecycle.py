"""E2E tests for document lifecycle and organization tools.

Covers the three main state transitions a document can undergo: archive/
unarchive, delete/restore (via trash), and cross-collection move.

"""

import anyio
import pytest

from .helpers import _create_collection, _create_document, _text

pytestmark = [pytest.mark.e2e, pytest.mark.anyio]


async def test_archive_and_unarchive_document(mcp_session):
    """Archive a document, confirm it's in the archived list, then unarchive.

    Guards against: archive_document succeeding but the document not appearing
    in list_archived_documents, or unarchive_document failing to restore
    normal readability.
    """
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

        # list_archived_documents (retry — archival may be async)
        text = ""
        for _ in range(10):
            result = await session.call_tool(
                "list_archived_documents",
            )
            text = _text(result)
            if doc_id in text:
                break
            await anyio.sleep(2)
        assert doc_id in text, f"Archived doc {doc_id} not found: {text}"
        assert "# Archived Documents" in text

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
    """Move a document to trash, confirm it's in list_trash, then restore.

    Guards against: delete_document permanently deleting rather than moving to
    trash, or restore_document failing to make the document readable again.
    """
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
    """Move a document to a target collection and verify via structure.

    Guards against: move_document reporting success while the document
    remains in the original collection or disappears from both.
    """
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
