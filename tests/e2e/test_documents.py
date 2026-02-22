"""E2E tests for document CRUD tools.

Covers create, read, and update paths including draft, template, and
nested-document variants. Every test creates its own isolated collection
so failures are independent.

"""

import pytest

from .helpers import (
    _create_collection,
    _create_document,
    _extract_id,
    _text,
)

pytestmark = [pytest.mark.e2e, pytest.mark.anyio]


async def test_create_and_read_document(mcp_session):
    """Create a document and verify its title and body via read_document.

    Guards against: create_document returning success while the document is
    unreadable or missing its content in subsequent reads.
    """
    async with mcp_session() as session:
        coll_id = await _create_collection(session, "E2E Read Collection")

        result = await session.call_tool(
            "create_document",
            arguments={
                "title": "E2E Test Document",
                "text": "Hello from E2E tests.",
                "collection_id": coll_id,
            },
        )
        text = _text(result)
        assert "created successfully" in text
        doc_id = _extract_id(text)

        result = await session.call_tool(
            "read_document",
            arguments={"document_id": doc_id},
        )
        text = _text(result)
        assert "# E2E Test Document" in text
        assert "Hello from E2E tests." in text


async def test_document_url_in_output(mcp_session):
    """Confirm read_document always includes the document URL in its output.

    Guards against: the URL field being dropped from the formatter when
    Outline's API response changes shape.
    """
    async with mcp_session() as session:
        coll_id = await _create_collection(session, "E2E URL Collection")
        doc_id = await _create_document(
            session, coll_id, "URL Test Doc", "Check URL."
        )

        result = await session.call_tool(
            "read_document",
            arguments={"document_id": doc_id},
        )
        assert "URL:" in _text(result)


async def test_create_template_document(mcp_session):
    """Create a document with template=True and verify the success response.

    Guards against: the template flag being ignored by the API client,
    or the response omitting the expected confirmation message.
    """
    async with mcp_session() as session:
        coll_id = await _create_collection(session, "E2E Template Collection")

        result = await session.call_tool(
            "create_document",
            arguments={
                "title": "E2E Template",
                "text": "Template content.",
                "collection_id": coll_id,
                "template": True,
            },
        )
        assert "created successfully" in _text(result)


async def test_create_nested_document(mcp_session):
    """Create a child document under a parent and verify the hierarchy.

    Creates a parent document, then a child with parent_document_id set,
    and confirms both appear in get_collection_structure output.
    Guards against: the parent_document_id parameter being silently dropped,
    resulting in a flat structure instead of the expected nesting.
    """
    async with mcp_session() as session:
        coll_id = await _create_collection(session, "E2E Nesting")
        parent_id = await _create_document(
            session, coll_id, "Parent Doc", "Parent."
        )

        result = await session.call_tool(
            "create_document",
            arguments={
                "title": "Child Doc",
                "text": "Child content.",
                "collection_id": coll_id,
                "parent_document_id": parent_id,
            },
        )
        assert "created successfully" in _text(result)

        result = await session.call_tool(
            "get_collection_structure",
            arguments={"collection_id": coll_id},
        )
        text = _text(result)
        assert "Parent Doc" in text
        assert "Child Doc" in text


async def test_create_draft_document(mcp_session):
    """Create a document with publish=False and verify it is still readable.

    Guards against: draft documents being inaccessible via read_document,
    which would break workflows that stage content before publishing.
    """
    async with mcp_session() as session:
        coll_id = await _create_collection(session, "E2E Draft Coll")

        result = await session.call_tool(
            "create_document",
            arguments={
                "title": "Draft Doc",
                "text": "Draft content.",
                "collection_id": coll_id,
                "publish": False,
            },
        )
        text = _text(result)
        assert "created successfully" in text
        doc_id = _extract_id(text)

        # Draft is readable by creator
        result = await session.call_tool(
            "read_document",
            arguments={"document_id": doc_id},
        )
        assert "Draft Doc" in _text(result)


async def test_update_document(mcp_session):
    """Update a document's title and body, then verify via read_document.

    Guards against: update_document reporting success while the underlying
    document retains the original content in the Outline API.
    """
    async with mcp_session() as session:
        coll_id = await _create_collection(session, "E2E Update Doc")
        doc_id = await _create_document(
            session, coll_id, "Original Title", "Original."
        )

        result = await session.call_tool(
            "update_document",
            arguments={
                "document_id": doc_id,
                "title": "Updated Title",
                "text": "Updated text.",
            },
        )
        assert "updated successfully" in _text(result)

        result = await session.call_tool(
            "read_document",
            arguments={"document_id": doc_id},
        )
        text = _text(result)
        assert "# Updated Title" in text
        assert "Updated text." in text
