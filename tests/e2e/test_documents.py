"""E2E tests for document CRUD tools."""

import pytest

from .helpers import (
    _create_collection,
    _create_document,
    _extract_id,
    _text,
)

pytestmark = [pytest.mark.e2e, pytest.mark.anyio]


async def test_create_and_read_document(mcp_session):
    """Create a document, then read it back."""
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
    """Read a document and verify URL is present."""
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
    """Create a template document."""
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


async def test_update_document(mcp_session):
    """Update a document's title and text."""
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
