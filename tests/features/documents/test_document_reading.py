"""
Tests for document reading tools.
"""

from unittest.mock import AsyncMock, patch

import pytest

from mcp_outline.features.documents.common import (
    OutlineClientError,
)
from mcp_outline.features.documents.document_reading import (
    format_lines_with_numbers,
    parse_headings,
)
from mcp_outline.utils.document_cache import (
    reset_document_cache,
)


class MockMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, **kwargs):
        def decorator(func):
            self.tools[func.__name__] = func
            return func

        return decorator


SAMPLE_DOCUMENT = {
    "id": "doc123",
    "title": "Test Document",
    "text": "This is a test document with some content.",
    "updatedAt": "2023-01-01T12:00:00Z",
}

SAMPLE_MULTILINE_DOCUMENT = {
    "id": "doc456",
    "title": "Multiline Doc",
    "text": (
        "Line 0\n"
        "Line 1\n"
        "Line 2\n"
        "Line 3\n"
        "Line 4\n"
        "Line 5\n"
        "Line 6\n"
        "Line 7\n"
        "Line 8\n"
        "Line 9"
    ),
    "url": "/doc/multi",
}

SAMPLE_EXPORT_RESPONSE = {
    "data": ("# Test Document\n\nThis is a test document with some content.")
}


@pytest.fixture
def mcp():
    return MockMCP()


@pytest.fixture
def register_reading_tools(mcp):
    from mcp_outline.features.documents.document_reading import (
        register_tools,
    )

    register_tools(mcp)
    return mcp


@pytest.fixture(autouse=True)
def _clean_cache():
    reset_document_cache()
    yield
    reset_document_cache()


_PATCH_CLIENT = (
    "mcp_outline.features.documents.document_reading.get_outline_client"
)
_PATCH_API_KEY = (
    "mcp_outline.features.documents.document_reading.get_resolved_api_key"
)


def _mock_api(mock_get_client, mock_api_key, document):
    mock_api_key.return_value = "test-key"
    mock_client = AsyncMock()
    mock_client.get_document.return_value = document
    mock_get_client.return_value = mock_client
    return mock_client


class TestDocumentReadingFormatters:
    """Tests for document reading formatting functions."""

    def testformat_lines_with_numbers(self):
        lines = ["hello", "world"]
        result = format_lines_with_numbers(lines, 5)
        assert "5\thello" in result
        assert "6\tworld" in result

    def testparse_headings(self):
        lines = [
            "# Heading 1",
            "Some text",
            "## Heading 2",
            "More text",
            "### Heading 3",
        ]
        headings = parse_headings(lines)
        assert len(headings) == 3
        assert headings[0] == (0, 1, "Heading 1")
        assert headings[1] == (2, 2, "Heading 2")
        assert headings[2] == (4, 3, "Heading 3")

    def testparse_headings_skips_code_blocks(self):
        lines = [
            "# Real Heading",
            "```python",
            "# Not a heading",
            "```",
            "## Another Real",
        ]
        headings = parse_headings(lines)
        assert len(headings) == 2
        assert headings[0] == (0, 1, "Real Heading")
        assert headings[1] == (4, 2, "Another Real")

    def testparse_headings_empty(self):
        headings = parse_headings(["no headings here"])
        assert headings == []


class TestReadDocument:
    """Tests for read_document tool."""

    @pytest.mark.asyncio
    @patch(_PATCH_API_KEY)
    @patch(_PATCH_CLIENT)
    async def test_read_document_full(
        self,
        mock_get_client,
        mock_api_key,
        register_reading_tools,
    ):
        _mock_api(mock_get_client, mock_api_key, SAMPLE_DOCUMENT)
        result = await register_reading_tools.tools["read_document"]("doc123")
        assert "# Test Document" in result
        assert "This is a test document with some content." in result
        assert "Lines" not in result

    @pytest.mark.asyncio
    @patch(_PATCH_API_KEY)
    @patch(_PATCH_CLIENT)
    async def test_read_document_with_offset_limit(
        self,
        mock_get_client,
        mock_api_key,
        register_reading_tools,
    ):
        _mock_api(
            mock_get_client,
            mock_api_key,
            SAMPLE_MULTILINE_DOCUMENT,
        )
        result = await register_reading_tools.tools["read_document"](
            "doc456", offset=2, limit=3
        )
        assert "Lines 2-4 of 10 total" in result
        assert "2\tLine 2" in result
        assert "3\tLine 3" in result
        assert "4\tLine 4" in result
        assert "Line 0" not in result
        assert "Line 5" not in result

    @pytest.mark.asyncio
    @patch(_PATCH_API_KEY)
    @patch(_PATCH_CLIENT)
    async def test_read_document_offset_only(
        self,
        mock_get_client,
        mock_api_key,
        register_reading_tools,
    ):
        _mock_api(
            mock_get_client,
            mock_api_key,
            SAMPLE_MULTILINE_DOCUMENT,
        )
        result = await register_reading_tools.tools["read_document"](
            "doc456", offset=8
        )
        assert "Lines 8-9 of 10 total" in result
        assert "8\tLine 8" in result
        assert "9\tLine 9" in result

    @pytest.mark.asyncio
    @patch(_PATCH_API_KEY)
    @patch(_PATCH_CLIENT)
    async def test_read_document_offset_beyond_end(
        self,
        mock_get_client,
        mock_api_key,
        register_reading_tools,
    ):
        _mock_api(
            mock_get_client,
            mock_api_key,
            SAMPLE_MULTILINE_DOCUMENT,
        )
        result = await register_reading_tools.tools["read_document"](
            "doc456", offset=100, limit=5
        )
        assert "Lines 10-9 of 10 total" in result

    @pytest.mark.asyncio
    @patch(_PATCH_API_KEY)
    @patch(_PATCH_CLIENT)
    async def test_read_document_uses_cache(
        self,
        mock_get_client,
        mock_api_key,
        register_reading_tools,
    ):
        mock_client = _mock_api(mock_get_client, mock_api_key, SAMPLE_DOCUMENT)
        tool = register_reading_tools.tools["read_document"]
        await tool("doc123")
        await tool("doc123")
        mock_client.get_document.assert_called_once()

    @pytest.mark.asyncio
    @patch(_PATCH_CLIENT)
    async def test_read_document_client_error(
        self, mock_get_client, register_reading_tools
    ):
        mock_client = AsyncMock()
        mock_client.get_document.side_effect = OutlineClientError("API error")
        mock_get_client.return_value = mock_client
        result = await register_reading_tools.tools["read_document"]("doc123")
        assert "Error reading document" in result


class TestExportDocument:
    """Tests for export_document tool."""

    @pytest.mark.asyncio
    @patch(_PATCH_CLIENT)
    async def test_export_document_success(
        self, mock_get_client, register_reading_tools
    ):
        mock_client = AsyncMock()
        mock_client.post.return_value = SAMPLE_EXPORT_RESPONSE
        mock_get_client.return_value = mock_client
        result = await register_reading_tools.tools["export_document"](
            "doc123"
        )
        mock_client.post.assert_called_once_with(
            "documents.export", {"id": "doc123"}
        )
        assert "# Test Document" in result

    @pytest.mark.asyncio
    @patch(_PATCH_CLIENT)
    async def test_export_document_empty_response(
        self, mock_get_client, register_reading_tools
    ):
        mock_client = AsyncMock()
        mock_client.post.return_value = {}
        mock_get_client.return_value = mock_client
        result = await register_reading_tools.tools["export_document"](
            "doc123"
        )
        assert "No content available" in result

    @pytest.mark.asyncio
    @patch(_PATCH_CLIENT)
    async def test_export_document_client_error(
        self, mock_get_client, register_reading_tools
    ):
        mock_client = AsyncMock()
        mock_client.post.side_effect = OutlineClientError("API error")
        mock_get_client.return_value = mock_client
        result = await register_reading_tools.tools["export_document"](
            "doc123"
        )
        assert "Error exporting document" in result
