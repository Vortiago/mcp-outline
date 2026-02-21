"""E2E tests for batch operation tools."""

import pytest

from .helpers import (
    _create_collection,
    _create_documents,
    _text,
)

pytestmark = [pytest.mark.e2e, pytest.mark.anyio]


async def test_batch_create_documents(mcp_session):
    """Batch-create two documents."""
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
    """Batch-update two documents."""
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
    """Batch-move documents to another collection."""
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
    """Batch-archive documents."""
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
    """Batch-delete documents."""
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
