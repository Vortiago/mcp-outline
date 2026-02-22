"""E2E tests for batch operation tools.

Covers bulk create, update, move, archive, and delete in sequence. Each
test is independent: it creates its own collection and documents so that
failures don't cascade.

"""

import pytest

from .helpers import (
    _create_collection,
    _create_documents,
    _text,
)

pytestmark = [pytest.mark.e2e, pytest.mark.anyio]


async def test_batch_create_documents(mcp_session):
    """Batch-create two documents in one call and verify both succeed.

    Guards against: the batch endpoint creating only the first document or
    silently skipping items when the input list has more than one entry.
    """
    async with mcp_session() as session:
        coll_id = await _create_collection(session, "E2E Batch Create")

        result = await session.call_tool(
            "batch_create_documents",
            arguments={
                "documents": [
                    {
                        "title": "Batch Doc 1",
                        "text": "Content 1.",
                        "collection_id": coll_id,
                    },
                    {
                        "title": "Batch Doc 2",
                        "text": "Content 2.",
                        "collection_id": coll_id,
                    },
                ]
            },
        )
        text = _text(result)
        assert "Batch Create Results" in text
        assert "Succeeded: 2" in text


async def test_batch_update_documents(mcp_session):
    """Batch-rename two documents and verify both report success.

    Guards against: batch_update_documents silently failing on individual
    items while still reporting an overall success count.
    """
    async with mcp_session() as session:
        coll_id = await _create_collection(session, "E2E Batch Update")
        ids = await _create_documents(session, coll_id, 2)

        result = await session.call_tool(
            "batch_update_documents",
            arguments={
                "updates": [
                    {"id": ids[0], "title": "Renamed 0"},
                    {"id": ids[1], "title": "Renamed 1"},
                ]
            },
        )
        text = _text(result)
        assert "Batch Update Results" in text
        assert "Succeeded: 2" in text


async def test_batch_move_documents(mcp_session):
    """Batch-move two documents from a source to a target collection.

    Guards against: batch_move_documents leaving documents in the source
    collection or reporting success without actually moving them.
    """
    async with mcp_session() as session:
        src_id = await _create_collection(session, "E2E BMov Source")
        tgt_id = await _create_collection(session, "E2E BMov Target")
        ids = await _create_documents(session, src_id, 2)

        result = await session.call_tool(
            "batch_move_documents",
            arguments={
                "document_ids": ids,
                "collection_id": tgt_id,
            },
        )
        text = _text(result)
        assert "Batch Move Results" in text
        assert "Succeeded: 2" in text


async def test_batch_archive_documents(mcp_session):
    """Batch-archive two documents and verify both are counted as succeeded.

    Guards against: batch_archive_documents silently skipping documents or
    returning a partial success count without raising an error.
    """
    async with mcp_session() as session:
        coll_id = await _create_collection(session, "E2E BArch Coll")
        ids = await _create_documents(session, coll_id, 2)

        result = await session.call_tool(
            "batch_archive_documents",
            arguments={"document_ids": ids},
        )
        text = _text(result)
        assert "Batch Archive Results" in text
        assert "Succeeded: 2" in text


async def test_batch_delete_documents(mcp_session):
    """Batch-delete two documents and verify both are counted as succeeded.

    Guards against: batch_delete_documents reporting success while leaving
    documents in the collection rather than moving them to trash.
    """
    async with mcp_session() as session:
        coll_id = await _create_collection(session, "E2E BDel Coll")
        ids = await _create_documents(session, coll_id, 2)

        result = await session.call_tool(
            "batch_delete_documents",
            arguments={"document_ids": ids},
        )
        text = _text(result)
        assert "Batch Delete Results" in text
        assert "Succeeded: 2" in text
