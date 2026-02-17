"""
Tests for document attachment tools.
"""

from unittest.mock import AsyncMock, patch

import pytest

from mcp_outline.features.documents.common import OutlineClientError
from mcp_outline.features.documents.document_attachments import (
    _format_attachment_list,
    _parse_attachment_ids,
)


# Mock FastMCP for registering tools
class MockMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, **kwargs):
        def decorator(func):
            self.tools[func.__name__] = func
            return func

        return decorator


SAMPLE_ATTACHMENT_ID = "6fe06f93-e331-408d-b954-6bb4ed50e67d"
SAMPLE_REDIRECT_URL = "https://storage.example.com/signed/attachment.pdf"
SAMPLE_DOCUMENT_WITH_ATTACHMENTS = {
    "id": "doc123",
    "title": "Document with Attachments",
    "text": (
        "Here is a [PDF](/api/attachments.redirect?id="
        "6fe06f93-e331-408d-b954-6bb4ed50e67d) and another "
        "[image](/api/attachments.redirect?id="
        "a1b2c3d4-e5f6-7890-abcd-ef1234567890)."
    ),
}
SAMPLE_DOCUMENT_NO_ATTACHMENTS = {
    "id": "doc456",
    "title": "Plain Document",
    "text": "No attachments here, just text.",
}


@pytest.fixture
def mcp():
    """Fixture to provide mock MCP instance."""
    return MockMCP()


@pytest.fixture
def register_attachment_tools(mcp):
    """Fixture to register document attachment tools."""
    from mcp_outline.features.documents.document_attachments import (
        register_tools,
    )

    register_tools(mcp)
    return mcp


class TestAttachmentParsing:
    """Tests for attachment ID parsing helpers."""

    def test_parse_attachment_ids_finds_multiple(self):
        """Parse document with multiple attachment refs."""
        text = SAMPLE_DOCUMENT_WITH_ATTACHMENTS["text"]
        result = _parse_attachment_ids(text)
        assert len(result) == 2
        ids = [r[0] for r in result]
        assert "6fe06f93-e331-408d-b954-6bb4ed50e67d" in ids
        assert "a1b2c3d4-e5f6-7890-abcd-ef1234567890" in ids

    def test_parse_attachment_ids_empty_text(self):
        """Parse empty text returns empty list."""
        assert _parse_attachment_ids("") == []
        assert _parse_attachment_ids("  \n  ") == []

    def test_parse_attachment_ids_no_matches(self):
        """Parse text with no attachment refs."""
        result = _parse_attachment_ids("Just plain text, no refs.")
        assert result == []

    def test_parse_attachment_ids_deduplicates(self):
        """Same attachment ID repeated is returned once."""
        text = (
            "Same [a](/api/attachments.redirect?id="
            "6fe06f93-e331-408d-b954-6bb4ed50e67d) and "
            "[b](/api/attachments.redirect?id="
            "6fe06f93-e331-408d-b954-6bb4ed50e67d)"
        )
        result = _parse_attachment_ids(text)
        assert len(result) == 1
        assert result[0][0] == "6fe06f93-e331-408d-b954-6bb4ed50e67d"

    def test_format_attachment_list_empty(self):
        """Format empty attachment list."""
        result = _format_attachment_list("My Doc", [])
        assert "No attachments found" in result
        assert "My Doc" in result

    def test_format_attachment_list_with_items(self):
        """Format list with attachments."""
        attachments = [
            ("id1", "context 1"),
            ("id2", "context 2"),
        ]
        result = _format_attachment_list("My Doc", attachments)
        assert "2 attachment(s)" in result
        assert "id1" in result
        assert "id2" in result
        assert "context 1" in result
        assert "context 2" in result


class TestDocumentAttachmentTools:
    """Tests for document attachment MCP tools."""

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_attachments.get_outline_client"
    )
    async def test_get_attachment_url_success(
        self, mock_get_client, register_attachment_tools
    ):
        """Test get_attachment_url tool success case."""
        mock_client = AsyncMock()
        mock_client.get_attachment_redirect_url.return_value = (
            SAMPLE_REDIRECT_URL
        )
        mock_get_client.return_value = mock_client

        result = await register_attachment_tools.tools["get_attachment_url"](
            SAMPLE_ATTACHMENT_ID
        )

        mock_client.get_attachment_redirect_url.assert_called_once_with(
            SAMPLE_ATTACHMENT_ID
        )
        assert result == SAMPLE_REDIRECT_URL

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_attachments.get_outline_client"
    )
    async def test_get_attachment_url_client_error(
        self, mock_get_client, register_attachment_tools
    ):
        """Test get_attachment_url with OutlineClientError."""
        mock_client = AsyncMock()
        mock_client.get_attachment_redirect_url.side_effect = (
            OutlineClientError("API error")
        )
        mock_get_client.return_value = mock_client

        result = await register_attachment_tools.tools["get_attachment_url"](
            SAMPLE_ATTACHMENT_ID
        )

        assert "Error" in result
        assert "API error" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_attachments.get_outline_client"
    )
    async def test_fetch_attachment_success(
        self, mock_get_client, register_attachment_tools
    ):
        """Test fetch_attachment tool success case."""
        mock_client = AsyncMock()
        mock_client.fetch_attachment_content.return_value = (
            b"binary content",
            "application/pdf",
        )
        mock_get_client.return_value = mock_client

        result = await register_attachment_tools.tools["fetch_attachment"](
            SAMPLE_ATTACHMENT_ID
        )

        mock_client.fetch_attachment_content.assert_called_once_with(
            SAMPLE_ATTACHMENT_ID
        )
        assert "Content-Type: application/pdf" in result
        assert "Content-Length: 14" in result
        assert "Content-Base64:" in result
        assert "YmluYXJ5IGNvbnRlbnQ=" in result  # base64 of "binary content"

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_attachments.get_outline_client"
    )
    async def test_fetch_attachment_client_error(
        self, mock_get_client, register_attachment_tools
    ):
        """Test fetch_attachment with OutlineClientError."""
        mock_client = AsyncMock()
        mock_client.fetch_attachment_content.side_effect = OutlineClientError(
            "Not found"
        )
        mock_get_client.return_value = mock_client

        result = await register_attachment_tools.tools["fetch_attachment"](
            SAMPLE_ATTACHMENT_ID
        )

        assert "Error" in result
        assert "Not found" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_attachments.get_outline_client"
    )
    async def test_list_document_attachments_success(
        self, mock_get_client, register_attachment_tools
    ):
        """Test list_document_attachments with document containing refs."""
        mock_client = AsyncMock()
        mock_client.get_document.return_value = (
            SAMPLE_DOCUMENT_WITH_ATTACHMENTS
        )
        mock_get_client.return_value = mock_client

        result = await register_attachment_tools.tools[
            "list_document_attachments"
        ]("doc123")

        mock_client.get_document.assert_called_once_with("doc123")
        assert "2 attachment(s)" in result
        assert "6fe06f93-e331-408d-b954-6bb4ed50e67d" in result
        assert "a1b2c3d4-e5f6-7890-abcd-ef1234567890" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_attachments.get_outline_client"
    )
    async def test_list_document_attachments_no_attachments(
        self, mock_get_client, register_attachment_tools
    ):
        """Test list_document_attachments with document having no refs."""
        mock_client = AsyncMock()
        mock_client.get_document.return_value = SAMPLE_DOCUMENT_NO_ATTACHMENTS
        mock_get_client.return_value = mock_client

        result = await register_attachment_tools.tools[
            "list_document_attachments"
        ]("doc456")

        assert "No attachments found" in result
        assert "Plain Document" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_attachments.get_outline_client"
    )
    async def test_list_document_attachments_client_error(
        self, mock_get_client, register_attachment_tools
    ):
        """Test list_document_attachments with invalid document ID."""
        mock_client = AsyncMock()
        mock_client.get_document.side_effect = OutlineClientError("Not found")
        mock_get_client.return_value = mock_client

        result = await register_attachment_tools.tools[
            "list_document_attachments"
        ]("bad-id")

        assert "Error" in result
        assert "Not found" in result
