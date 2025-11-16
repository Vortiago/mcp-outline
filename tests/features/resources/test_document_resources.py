"""
Tests for document-related MCP resources.
"""

from unittest.mock import AsyncMock, patch

import pytest

from mcp_outline.features.documents.common import OutlineClientError
from mcp_outline.features.resources.document_resources import (
    _format_backlinks,
)


# Mock FastMCP for registering resources
class MockMCP:
    def __init__(self):
        self.resources = {}

    def resource(self, uri_template: str):
        def decorator(func):
            self.resources[uri_template] = func
            return func

        return decorator


# Sample test data
SAMPLE_DOCUMENT = {
    "id": "doc123",
    "title": "Test Document",
    "text": (
        "# Test Document\n\nThis is a test document with markdown content."
    ),
}

SAMPLE_BACKLINKS = [
    {
        "id": "doc456",
        "title": "Document 1 Linking Here",
    },
    {
        "id": "doc789",
        "title": "Document 2 Linking Here",
    },
]


@pytest.fixture
def mcp():
    """Fixture to provide mock MCP instance."""
    return MockMCP()


@pytest.fixture
def register_document_resources(mcp):
    """Fixture to register document resources."""
    from mcp_outline.features.resources.document_resources import (
        register_resources,
    )

    register_resources(mcp)
    return mcp


class TestDocumentResourceFormatters:
    """Tests for document resource formatting functions."""

    def test_format_backlinks_structure(self):
        """Test backlinks format is consistent."""
        result = _format_backlinks(SAMPLE_BACKLINKS)
        lines = result.strip().split("\n")

        # Each line should be a bullet point
        assert all(line.startswith("- ") for line in lines)

        # Each line should have title and ID in parentheses
        assert "Document 1 Linking Here (doc456)" in result
        assert "Document 2 Linking Here (doc789)" in result

        # Verify count
        assert len(lines) == 2

    def test_format_backlinks_empty(self):
        """Test formatting empty backlinks."""
        result = _format_backlinks([])
        assert result == "No backlinks found."

    def test_format_backlinks_special_characters(self):
        """Test backlinks with special characters in titles."""
        backlinks = [
            {"id": "doc1", "title": "Document with *asterisks*"},
            {"id": "doc2", "title": "Document [with] {braces}"},
        ]

        result = _format_backlinks(backlinks)

        # Should preserve special characters
        assert "*asterisks*" in result
        assert "[with]" in result
        assert "{braces}" in result


class TestDocumentResources:
    """Tests for document resource handlers."""

    @pytest.mark.asyncio
    async def test_get_document_content_success(
        self, register_document_resources
    ):
        """Test successful document content retrieval."""
        with patch(
            "mcp_outline.features.resources.document_resources."
            "get_outline_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_document.return_value = SAMPLE_DOCUMENT
            mock_get_client.return_value = mock_client

            resource_func = register_document_resources.resources[
                "outline://document/{document_id}"
            ]
            result = await resource_func("doc123")

            assert "# Test Document" in result
            assert "This is a test document with markdown content." in result
            mock_client.get_document.assert_called_once_with("doc123")

    @pytest.mark.asyncio
    async def test_get_document_content_empty(
        self, register_document_resources
    ):
        """Test document with empty content."""
        with patch(
            "mcp_outline.features.resources.document_resources."
            "get_outline_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_document.return_value = {
                "id": "doc123",
                "title": "Empty Doc",
            }
            mock_get_client.return_value = mock_client

            resource_func = register_document_resources.resources[
                "outline://document/{document_id}"
            ]
            result = await resource_func("doc123")

            assert result == ""

    @pytest.mark.asyncio
    async def test_get_document_content_error(
        self, register_document_resources
    ):
        """Test document content retrieval error."""
        with patch(
            "mcp_outline.features.resources.document_resources."
            "get_outline_client"
        ) as mock_get_client:
            mock_get_client.side_effect = OutlineClientError("API error")

            resource_func = register_document_resources.resources[
                "outline://document/{document_id}"
            ]
            result = await resource_func("doc123")

            assert "Outline client error: API error" in result

    @pytest.mark.asyncio
    async def test_get_document_backlinks_success(
        self, register_document_resources
    ):
        """Test successful document backlinks retrieval."""
        with patch(
            "mcp_outline.features.resources.document_resources."
            "get_outline_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post.return_value = {"data": SAMPLE_BACKLINKS}
            mock_get_client.return_value = mock_client

            resource_func = register_document_resources.resources[
                "outline://document/{document_id}/backlinks"
            ]
            result = await resource_func("doc123")

            # Verify simple bullet list format
            assert "Document 1 Linking Here (doc456)" in result
            assert "Document 2 Linking Here (doc789)" in result
            # Should not have markdown headers
            assert "# Backlinks" not in result
            mock_client.post.assert_called_once_with(
                "documents.list", {"backlinkDocumentId": "doc123"}
            )

    @pytest.mark.asyncio
    async def test_get_document_backlinks_empty(
        self, register_document_resources
    ):
        """Test document with no backlinks."""
        with patch(
            "mcp_outline.features.resources.document_resources."
            "get_outline_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post.return_value = {"data": []}
            mock_get_client.return_value = mock_client

            resource_func = register_document_resources.resources[
                "outline://document/{document_id}/backlinks"
            ]
            result = await resource_func("doc123")

            assert result == "No backlinks found."

    @pytest.mark.asyncio
    async def test_get_document_backlinks_error(
        self, register_document_resources
    ):
        """Test document backlinks retrieval error."""
        with patch(
            "mcp_outline.features.resources.document_resources."
            "get_outline_client"
        ) as mock_get_client:
            mock_get_client.side_effect = OutlineClientError("API error")

            resource_func = register_document_resources.resources[
                "outline://document/{document_id}/backlinks"
            ]
            result = await resource_func("doc123")

            assert "Outline client error: API error" in result
