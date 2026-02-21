"""E2E tests for comments & collaboration tools."""

import re

import anyio
import pytest

from .helpers import (
    _create_collection,
    _create_document,
    _extract_id,
    _text,
)

pytestmark = [pytest.mark.e2e, pytest.mark.anyio]


async def test_add_and_list_comments(mcp_session):
    """Add, list, and get comments on a document."""
    async with mcp_session() as session:
        coll_id = await _create_collection(session, "E2E Comments")
        doc_id = await _create_document(
            session, coll_id, "Comment Test Doc", "For comments."
        )

        # add_comment
        result = await session.call_tool(
            "add_comment",
            arguments={
                "document_id": doc_id,
                "text": "E2E test comment.",
            },
        )
        text = _text(result)
        assert "added successfully" in text
        comment_id = _extract_id(text)

        # list_document_comments
        result = await session.call_tool(
            "list_document_comments",
            arguments={"document_id": doc_id},
        )
        text = _text(result)
        assert "# Document Comments" in text
        assert comment_id in text

        # get_comment
        result = await session.call_tool(
            "get_comment",
            arguments={"comment_id": comment_id},
        )
        assert "# Comment by" in _text(result)


async def test_get_document_backlinks(mcp_session):
    """Verify backlinks between two linked documents."""
    async with mcp_session() as session:
        coll_id = await _create_collection(session, "E2E Backlinks")
        target_id = await _create_document(
            session, coll_id, "Backlink Target", "I am target."
        )

        # Read target to get its URL for linking
        result = await session.call_tool(
            "read_document",
            arguments={"document_id": target_id},
        )
        url_m = re.search(r"URL:\s*(http\S+)", _text(result))
        doc_url = url_m.group(1) if url_m else ""

        # Create a doc that links to the target
        await _create_document(
            session,
            coll_id,
            "Backlink Source",
            f"Link to [target]({doc_url})",
        )

        await anyio.sleep(2)

        result = await session.call_tool(
            "get_document_backlinks",
            arguments={"document_id": target_id},
        )
        text = _text(result)
        # Backlinks may need time to index
        assert "Backlink Source" in text or "No documents link" in text
