"""E2E tests for search and navigation tools.

Covers collection listing (including pagination), collection structure,
title-based document lookup, markdown export, and full-text search.
Search-based tests retry with back-off because Outline indexes documents
asynchronously.

"""

import anyio
import pytest

from .helpers import (
    _create_collection,
    _create_document,
    _text,
)

pytestmark = [pytest.mark.e2e, pytest.mark.anyio]


async def test_list_collections(mcp_session):
    """Confirm list_collections returns valid formatted output.

    Guards against: list_collections raising an error on an empty workspace or
    returning unformatted raw JSON instead of the expected markdown structure.
    """
    async with mcp_session() as session:
        result = await session.call_tool("list_collections")
        text = _text(result)
        assert "# Collections" in text or "No collections found" in text


async def test_list_collections_pagination(mcp_session):
    """Verify that limit and offset return different pages of results.

    Guards against: pagination parameters being ignored, causing both pages
    to return identical results.
    """
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
    """Fetch the document hierarchy for a collection and verify a doc appears.

    Guards against: get_collection_structure returning an empty tree or
    raising an error when a collection contains at least one document.
    """
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
    """Look up a document's ID by its exact title, retrying while indexing.

    Guards against: get_document_id_from_title failing to find a document
    that exists, or returning a different document's ID on a title match.
    """
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
    """Export a document and verify its body content is present in the output.

    Guards against: export_document returning a success message or header
    only, without including the actual document content.
    """
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
    """Create a doc with a unique token and find it via search_documents.

    Uses a retry loop because Outline's full-text index is updated
    asynchronously after document creation.
    Guards against: search_documents returning no results immediately after
    creation and not retrying, or returning the wrong document.
    """
    async with mcp_session() as session:
        coll_id = await _create_collection(session, "E2E Search Collection")

        unique = "xyzzy42unique"
        await _create_document(
            session,
            coll_id,
            f"Searchable {unique}",
            f"Content with {unique}.",
        )

        for _ in range(10):
            result = await session.call_tool(
                "search_documents",
                arguments={"query": unique},
            )
            text = _text(result)
            if unique in text:
                break
            await anyio.sleep(2)
        else:
            pytest.fail("Document not found in search")

        assert "# Search Results" in text
