"""
Tests for document collaboration tools.
"""

from unittest.mock import AsyncMock, patch

import pytest

from mcp_outline.features.documents.common import OutlineClientError
from mcp_outline.features.documents.document_collaboration import (
    _format_comments,
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


# Sample comment data
SAMPLE_COMMENTS = [
    {
        "id": "comment1",
        "data": {"content": "This is a test comment"},
        "createdAt": "2023-01-01T12:00:00Z",
        "createdBy": {"id": "user1", "name": "Test User"},
    },
    {
        "id": "comment2",
        "data": {"content": "Another comment"},
        "createdAt": "2023-01-02T12:00:00Z",
        "createdBy": {"id": "user2", "name": "Another User"},
    },
]

# Sample documents for backlinks
SAMPLE_BACKLINK_DOCUMENTS = [
    {
        "id": "doc1",
        "title": "Referencing Document 1",
        "updatedAt": "2023-01-01T12:00:00Z",
    },
    {
        "id": "doc2",
        "title": "Referencing Document 2",
        "updatedAt": "2023-01-02T12:00:00Z",
    },
]


@pytest.fixture
def mcp():
    """Fixture to provide mock MCP instance."""
    return MockMCP()


@pytest.fixture
def register_collaboration_tools(mcp):
    """Fixture to register document collaboration tools."""
    from mcp_outline.features.documents.document_collaboration import (
        register_tools,
    )

    register_tools(mcp)
    return mcp


class TestDocumentCollaborationFormatters:
    """Tests for document collaboration formatting functions."""

    def test_format_comments_with_data(self):
        """Test formatting comments with valid data."""
        result = _format_comments(SAMPLE_COMMENTS)

        # Verify the result contains the expected information
        assert "# Document Comments" in result
        assert "Comment by Test User" in result
        assert "This is a test comment" in result
        assert "2023-01-01" in result
        assert "Comment by Another User" in result
        assert "Another comment" in result

    def test_format_comments_empty(self):
        """Test formatting empty comments list."""
        result = _format_comments([])

        assert "No comments found for this document" in result

    def test_format_comments_missing_fields(self):
        """Test formatting comments with missing fields."""
        # Comments with missing fields
        incomplete_comments = [
            # Missing user name
            {
                "id": "comment1",
                "data": {"content": "Comment with missing user"},
                "createdAt": "2023-01-01T12:00:00Z",
                "createdBy": {},
            },
            # Missing created date
            {
                "id": "comment2",
                "data": {"content": "Comment with missing date"},
                "createdBy": {"name": "Test User"},
            },
            # Missing text
            {
                "id": "comment3",
                "createdAt": "2023-01-03T12:00:00Z",
                "createdBy": {"name": "Another User"},
            },
        ]

        result = _format_comments(incomplete_comments)

        # Verify the result handles missing fields gracefully
        assert "Unknown User" in result
        assert "Comment with missing user" in result
        assert "Test User" in result
        assert "Comment with missing date" in result
        assert "Another User" in result


class TestDocumentCollaborationTools:
    """Tests for document collaboration tools."""

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_collaboration.get_outline_client"
    )
    async def test_list_document_comments_success(
        self, mock_get_client, register_collaboration_tools
    ):
        """Test list_document_comments tool success case."""
        # Set up mock client
        mock_client = AsyncMock()
        mock_client.post.return_value = {"data": SAMPLE_COMMENTS}
        mock_get_client.return_value = mock_client

        # Call the tool
        result = await register_collaboration_tools.tools[
            "list_document_comments"
        ]("doc123")

        # Verify client was called correctly
        mock_client.post.assert_called_once_with(
            "comments.list",
            {
                "documentId": "doc123",
                "includeAnchorText": False,
                "limit": 25,
                "offset": 0,
            },
        )

        # Verify result contains expected information
        assert "# Document Comments" in result
        assert "Comment by Test User" in result
        assert "This is a test comment" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_collaboration.get_outline_client"
    )
    async def test_list_document_comments_empty(
        self, mock_get_client, register_collaboration_tools
    ):
        """Test list_document_comments tool with no comments."""
        # Set up mock client with empty response
        mock_client = AsyncMock()
        mock_client.post.return_value = {"data": []}
        mock_get_client.return_value = mock_client

        # Call the tool
        result = await register_collaboration_tools.tools[
            "list_document_comments"
        ]("doc123")

        # Verify result contains expected message
        assert "No comments found" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_collaboration.get_outline_client"
    )
    async def test_get_comment_success(
        self, mock_get_client, register_collaboration_tools
    ):
        """Test get_comment tool success case."""
        # Set up mock client
        mock_client = AsyncMock()
        mock_client.post.return_value = {"data": SAMPLE_COMMENTS[0]}
        mock_get_client.return_value = mock_client

        # Call the tool
        result = await register_collaboration_tools.tools["get_comment"](
            "comment1"
        )

        # Verify client was called correctly
        mock_client.post.assert_called_once_with(
            "comments.info", {"id": "comment1", "includeAnchorText": False}
        )

        # Verify result contains expected information
        assert "# Comment by Test User" in result
        assert "This is a test comment" in result
        assert "2023-01-01" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_collaboration.get_outline_client"
    )
    async def test_get_comment_not_found(
        self, mock_get_client, register_collaboration_tools
    ):
        """Test get_comment tool with comment not found."""
        # Set up mock client with empty response
        mock_client = AsyncMock()
        mock_client.post.return_value = {"data": {}}
        mock_get_client.return_value = mock_client

        # Call the tool
        result = await register_collaboration_tools.tools["get_comment"](
            "comment999"
        )

        # Verify result contains expected message
        assert "Comment not found" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_collaboration.get_outline_client"
    )
    async def test_get_document_backlinks_success(
        self, mock_get_client, register_collaboration_tools
    ):
        """Test get_document_backlinks tool success case."""
        # Set up mock client
        mock_client = AsyncMock()
        mock_client.post.return_value = {"data": SAMPLE_BACKLINK_DOCUMENTS}
        mock_get_client.return_value = mock_client

        # Call the tool
        result = await register_collaboration_tools.tools[
            "get_document_backlinks"
        ]("doc123")

        # Verify client was called correctly
        mock_client.post.assert_called_once_with(
            "documents.list", {"backlinkDocumentId": "doc123"}
        )

        # Verify result contains expected information
        assert "# Documents Linking to This Document" in result
        assert "Referencing Document 1" in result
        assert "doc1" in result
        assert "Referencing Document 2" in result
        assert "doc2" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_collaboration.get_outline_client"
    )
    async def test_get_document_backlinks_none(
        self, mock_get_client, register_collaboration_tools
    ):
        """Test get_document_backlinks tool with no backlinks."""
        # Set up mock client with empty response
        mock_client = AsyncMock()
        mock_client.post.return_value = {"data": []}
        mock_get_client.return_value = mock_client

        # Call the tool
        result = await register_collaboration_tools.tools[
            "get_document_backlinks"
        ]("doc123")

        # Verify result contains expected message
        assert "No documents link to this document" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_collaboration.get_outline_client"
    )
    async def test_get_document_backlinks_client_error(
        self, mock_get_client, register_collaboration_tools
    ):
        """Test get_document_backlinks tool with client error."""
        # Set up mock client to raise an error
        mock_client = AsyncMock()
        mock_client.post.side_effect = OutlineClientError("API error")
        mock_get_client.return_value = mock_client

        # Call the tool
        result = await register_collaboration_tools.tools[
            "get_document_backlinks"
        ]("doc123")

        # Verify error is handled and returned
        assert "Error retrieving backlinks" in result
        assert "API error" in result
