"""E2E tests for search & navigation tools."""

import anyio
import pytest

from .helpers import (
    _create_collection,
    _create_document,
    _text,
)

pytestmark = [pytest.mark.e2e, pytest.mark.anyio]


async def test_list_collections(mcp_session):
    """list_collections returns valid formatted output."""
    async with mcp_session() as session:
        result = await session.call_tool("list_collections")
        text = _text(result)
        assert "# Collections" in text or "No collections found" in text


async def test_list_collections_pagination(mcp_session):
    """Verify limit/offset parameters work."""
    async with mcp_session() as session:
        for name in ("E2E Page A", "E2E Page B"):
            await _create_collection(session, name)

        r1 = await session.call_tool(
            "list_collections",
            arguments={"limit": 1},
        )
        r2 = await session.call_tool(
            "list_collections",
            arguments={"limit": 1, "offset": 1},
        )
        t1, t2 = _text(r1), _text(r2)
        assert "# Collections" in t1
        assert "# Collections" in t2
        assert t1 != t2


async def test_get_collection_structure(mcp_session):
    """Get document hierarchy within a collection."""
    async with mcp_session() as session:
        coll_id = await _create_collection(session, "E2E Structure Coll")
        await _create_document(
            session, coll_id, "Structure Doc", "In the tree."
        )

        result = await session.call_tool(
            "get_collection_structure",
            arguments={"collection_id": coll_id},
        )
        text = _text(result)
        assert "# Collection Structure" in text
        assert "Structure Doc" in text


async def test_get_document_id_from_title(mcp_session):
    """Look up a document ID by its title."""
    async with mcp_session() as session:
        coll_id = await _create_collection(session, "E2E Title Lookup")
        doc_id = await _create_document(
            session, coll_id, "UniqueTitle42Lookup"
        )

        for _ in range(5):
            result = await session.call_tool(
                "get_document_id_from_title",
                arguments={"query": "UniqueTitle42Lookup"},
            )
            text = _text(result)
            if "Document ID:" in text:
                break
            await anyio.sleep(1)
        else:
            pytest.fail("Title lookup failed")

        assert doc_id in text


async def test_export_document(mcp_session):
    """Export a document as markdown."""
    async with mcp_session() as session:
        coll_id = await _create_collection(session, "E2E Export Doc")
        doc_id = await _create_document(
            session,
            coll_id,
            "Export Test Doc",
            "Exported content here.",
        )

        result = await session.call_tool(
            "export_document",
            arguments={"document_id": doc_id},
        )
        assert "Exported content here." in _text(result)


async def test_search_documents(mcp_session):
    """Create a document and find it via search."""
    async with mcp_session() as session:
        coll_id = await _create_collection(session, "E2E Search Collection")

        unique = "xyzzy42unique"
        await _create_document(
            session,
            coll_id,
            f"Searchable {unique}",
            f"Content with {unique}.",
        )

        for _ in range(5):
            result = await session.call_tool(
                "search_documents",
                arguments={"query": unique},
            )
            text = _text(result)
            if unique in text:
                break
            await anyio.sleep(1)
        else:
            pytest.fail("Document not found in search")

        assert "# Search Results" in text
