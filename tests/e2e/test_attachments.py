"""E2E tests for attachment tools.

Uploads a real file via the Outline API, then tests the
read-only MCP attachment tools against it.
"""

import pytest

from .helpers import (
    _create_collection,
    _create_document,
    _text,
    _upload_attachment,
)

pytestmark = [pytest.mark.e2e, pytest.mark.anyio]


@pytest.fixture(scope="module")
def attachment_id(outline_api_key):
    """Upload a test attachment once for all tests in this module."""
    return _upload_attachment(outline_api_key)


async def test_list_document_attachments(attachment_id, mcp_session):
    """Create doc with attachment ref, list attachments."""
    att_id = attachment_id

    async with mcp_session() as session:
        coll_id = await _create_collection(session, "E2E Attach List")
        # Create doc whose text references the real attachment
        doc_id = await _create_document(
            session,
            coll_id,
            "Attachment List Doc",
            f"See [file](/api/attachments.redirect?id={att_id})",
        )

        result = await session.call_tool(
            "list_document_attachments",
            arguments={"document_id": doc_id},
        )
        text = _text(result)
        assert att_id in text
        assert "1." in text  # at least one attachment listed


async def test_get_attachment_url(attachment_id, mcp_session):
    """Resolve attachment ID to a download URL."""
    att_id = attachment_id

    async with mcp_session() as session:
        result = await session.call_tool(
            "get_attachment_url",
            arguments={"attachment_id": att_id},
        )
        text = _text(result)
        # Should return a URL, not an error
        assert "Error" not in text
        assert "http" in text or "/" in text


async def test_fetch_attachment(attachment_id, mcp_session):
    """Fetch attachment content as base64."""
    att_id = attachment_id

    async with mcp_session() as session:
        result = await session.call_tool(
            "fetch_attachment",
            arguments={"attachment_id": att_id},
        )
        text = _text(result)
        assert "Content-Type:" in text
        assert "Content-Base64:" in text
