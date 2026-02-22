"""E2E tests for collection management tools."""

import pytest

from .helpers import _create_collection, _create_document, _extract_id, _text

pytestmark = [pytest.mark.e2e, pytest.mark.anyio]


async def test_create_collection_direct(mcp_session):
    """Create a collection directly and verify it appears in the list."""
    async with mcp_session() as session:
        result = await session.call_tool(
            "create_collection",
            arguments={
                "name": "E2E Direct Collection",
                "description": "Direct.",
            },
        )
        text = _text(result)
        assert "created successfully" in text
        coll_id = _extract_id(text)

        # Verify it's visible in the list
        result = await session.call_tool("list_collections")
        assert coll_id in _text(result)


async def test_update_collection(mcp_session):
    """Update a collection's name."""
    async with mcp_session() as session:
        coll_id = await _create_collection(session, "E2E Update Coll")

        result = await session.call_tool(
            "update_collection",
            arguments={
                "collection_id": coll_id,
                "name": "E2E Coll Renamed",
            },
        )
        assert "updated successfully" in _text(result)


async def test_export_collection(mcp_session):
    """Export a collection."""
    async with mcp_session() as session:
        coll_id = await _create_collection(session, "E2E Export Coll")
        await _create_document(session, coll_id, "Doc in Export Coll")

        result = await session.call_tool(
            "export_collection",
            arguments={"collection_id": coll_id},
        )
        assert "# Export Operation" in _text(result)


async def test_export_all_collections(mcp_session):
    """Export all collections."""
    async with mcp_session() as session:
        result = await session.call_tool(
            "export_all_collections",
        )
        assert "# Export Operation" in _text(result)


async def test_delete_collection(mcp_session):
    """Delete a collection."""
    async with mcp_session() as session:
        coll_id = await _create_collection(session, "E2E Delete Coll")

        result = await session.call_tool(
            "delete_collection",
            arguments={"collection_id": coll_id},
        )
        assert "deleted successfully" in _text(result)
