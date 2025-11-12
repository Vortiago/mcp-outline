"""
Tests for document reading tools.
"""

from unittest.mock import AsyncMock, patch

import pytest

from mcp_outline.features.documents.common import OutlineClientError
from mcp_outline.features.documents.document_reading import (
    _format_document_content,
)


# Mock FastMCP for registering tools
class MockMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func

        return decorator


# Sample document data
SAMPLE_DOCUMENT = {
    "id": "doc123",
    "title": "Test Document",
    "text": "This is a test document with some content.",
    "updatedAt": "2023-01-01T12:00:00Z",
}

# Sample export response
SAMPLE_EXPORT_RESPONSE = {
    "data": "# Test Document\n\nThis is a test document with some content."
}


@pytest.fixture
def mcp():
    """Fixture to provide mock MCP instance."""
    return MockMCP()


@pytest.fixture
def register_reading_tools(mcp):
    """Fixture to register document reading tools."""
    from mcp_outline.features.documents.document_reading import register_tools

    register_tools(mcp)
    return mcp


class TestDocumentReadingFormatters:
    """Tests for document reading formatting functions."""

    def test_format_document_content(self):
        """Test formatting document content."""
        result = _format_document_content(SAMPLE_DOCUMENT)

        # Verify the result contains the expected information
        assert "# Test Document" in result
        assert "This is a test document with some content." in result

    def test_format_document_content_missing_fields(self):
        """Test formatting document content with missing fields."""
        # Test with missing title
        doc_no_title = {"text": "Content only"}
        result_no_title = _format_document_content(doc_no_title)
        assert "# Untitled Document" in result_no_title
        assert "Content only" in result_no_title

        # Test with missing text
        doc_no_text = {"title": "Title only"}
        result_no_text = _format_document_content(doc_no_text)
        assert "# Title only" in result_no_text
        assert result_no_text.strip().endswith("# Title only")

        # Test with empty document
        empty_doc = {}
        result_empty = _format_document_content(empty_doc)
        assert "# Untitled Document" in result_empty


class TestDocumentReadingTools:
    """Tests for document reading tools."""

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_reading.get_outline_client"
    )
    async def test_read_document_success(
        self, mock_get_client, register_reading_tools
    ):
        """Test read_document tool success case."""
        # Set up mock client
        mock_client = AsyncMock()
        mock_client.get_document.return_value = SAMPLE_DOCUMENT
        mock_get_client.return_value = mock_client

        # Call the tool
        result = await register_reading_tools.tools["read_document"]("doc123")

        # Verify client was called correctly
        mock_client.get_document.assert_called_once_with("doc123")

        # Verify result contains expected information
        assert "# Test Document" in result
        assert "This is a test document with some content." in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_reading.get_outline_client"
    )
    async def test_read_document_client_error(
        self, mock_get_client, register_reading_tools
    ):
        """Test read_document tool with client error."""
        # Set up mock client to raise an error
        mock_client = AsyncMock()
        mock_client.get_document.side_effect = OutlineClientError("API error")
        mock_get_client.return_value = mock_client

        # Call the tool
        result = await register_reading_tools.tools["read_document"]("doc123")

        # Verify error is handled and returned
        assert "Error reading document" in result
        assert "API error" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_reading.get_outline_client"
    )
    async def test_export_document_success(
        self, mock_get_client, register_reading_tools
    ):
        """Test export_document tool success case."""
        # Set up mock client
        mock_client = AsyncMock()
        mock_client.post.return_value = SAMPLE_EXPORT_RESPONSE
        mock_get_client.return_value = mock_client

        # Call the tool
        result = await register_reading_tools.tools["export_document"](
            "doc123"
        )

        # Verify client was called correctly
        mock_client.post.assert_called_once_with(
            "documents.export", {"id": "doc123"}
        )

        # Verify result contains expected information
        assert "# Test Document" in result
        assert "This is a test document with some content." in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_reading.get_outline_client"
    )
    async def test_export_document_empty_response(
        self, mock_get_client, register_reading_tools
    ):
        """Test export_document tool with empty response."""
        # Set up mock client with empty response
        mock_client = AsyncMock()
        mock_client.post.return_value = {}
        mock_get_client.return_value = mock_client

        # Call the tool
        result = await register_reading_tools.tools["export_document"](
            "doc123"
        )

        # Verify result contains default message
        assert "No content available" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_reading.get_outline_client"
    )
    async def test_export_document_client_error(
        self, mock_get_client, register_reading_tools
    ):
        """Test export_document tool with client error."""
        # Set up mock client to raise an error
        mock_client = AsyncMock()
        mock_client.post.side_effect = OutlineClientError("API error")
        mock_get_client.return_value = mock_client

        # Call the tool
        result = await register_reading_tools.tools["export_document"](
            "doc123"
        )

        # Verify error is handled and returned
        assert "Error exporting document" in result
        assert "API error" in result
