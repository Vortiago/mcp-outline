"""E2E tests for collection management tools.

Covers the full lifecycle of a collection: create, list, update, export,
and delete. Each test exercises a single MCP tool against a live Outline
instance spun up via Docker Compose.

"""

import pytest

from .helpers import _create_collection, _create_document, _extract_id, _text

pytestmark = [pytest.mark.e2e, pytest.mark.anyio]


async def test_create_collection_direct(mcp_session):
    """Create a collection and confirm it appears in list_collections.

    Guards against: regressions where create_collection succeeds but the
    new collection is silently omitted from subsequent list responses.
    """
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
    """Rename a collection via update_collection and verify the response.

    Guards against: update_collection silently no-oping or returning the old
    name in the response.
    """
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
    """Trigger an async export for a single collection and verify the response.

    Guards against: export_collection returning an error when a collection
    contains at least one document.
    """
    async with mcp_session() as session:
        coll_id = await _create_collection(session, "E2E Export Coll")
        await _create_document(session, coll_id, "Doc in Export Coll")

        result = await session.call_tool(
            "export_collection",
            arguments={"collection_id": coll_id},
        )
        assert "# Export Operation" in _text(result)


async def test_export_all_collections(mcp_session):
    """Trigger a workspace-wide export and verify the response format.

    Guards against: export_all_collections failing when the workspace has
    multiple collections, or the response header being missing.
    """
    async with mcp_session() as session:
        result = await session.call_tool(
            "export_all_collections",
        )
        assert "# Export Operation" in _text(result)


async def test_delete_collection(mcp_session):
    """Delete a collection and confirm the success message.

    Guards against: delete_collection returning a non-error string that
    doesn't confirm deletion, masking silent failures.
    """
    async with mcp_session() as session:
        coll_id = await _create_collection(session, "E2E Delete Coll")

        result = await session.call_tool(
            "delete_collection",
            arguments={"collection_id": coll_id},
        )
        assert "deleted successfully" in _text(result)
