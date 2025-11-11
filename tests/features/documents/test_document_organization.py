"""
Tests for document organization tools.
"""

from unittest.mock import AsyncMock, patch

import pytest

from mcp_outline.features.documents.common import OutlineClientError


# Mock FastMCP for registering tools
class MockMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func

        return decorator


# Sample response data
SAMPLE_MOVE_RESPONSE = {
    "data": {
        "id": "doc123",
        "title": "Moved Document",
        "collectionId": "col456",
    }
}


@pytest.fixture
def mcp():
    """Fixture to provide mock MCP instance."""
    return MockMCP()


@pytest.fixture
def register_organization_tools(mcp):
    """Fixture to register document organization tools."""
    from mcp_outline.features.documents.document_organization import (
        register_tools,
    )

    register_tools(mcp)
    return mcp


class TestMoveDocument:
    """Tests for move_document tool."""

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_organization.get_outline_client"
    )
    async def test_move_document_to_collection_success(
        self, mock_get_client, register_organization_tools
    ):
        """Test move_document to a different collection."""
        mock_client = AsyncMock()
        mock_client.post.return_value = SAMPLE_MOVE_RESPONSE
        mock_get_client.return_value = mock_client

        result = await register_organization_tools.tools["move_document"](
            document_id="doc123", collection_id="col456"
        )

        mock_client.post.assert_called_once_with(
            "documents.move", {"id": "doc123", "collectionId": "col456"}
        )
        assert "Document moved successfully" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_organization.get_outline_client"
    )
    async def test_move_document_to_parent_success(
        self, mock_get_client, register_organization_tools
    ):
        """Test move_document to a different parent."""
        mock_client = AsyncMock()
        mock_client.post.return_value = SAMPLE_MOVE_RESPONSE
        mock_get_client.return_value = mock_client

        result = await register_organization_tools.tools["move_document"](
            document_id="doc123", parent_document_id="parent456"
        )

        mock_client.post.assert_called_once_with(
            "documents.move", {"id": "doc123", "parentDocumentId": "parent456"}
        )
        assert "Document moved successfully" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_organization.get_outline_client"
    )
    async def test_move_document_collection_and_parent(
        self, mock_get_client, register_organization_tools
    ):
        """Test move_document with both collection and parent specified."""
        mock_client = AsyncMock()
        mock_client.post.return_value = SAMPLE_MOVE_RESPONSE
        mock_get_client.return_value = mock_client

        result = await register_organization_tools.tools["move_document"](
            document_id="doc123",
            collection_id="col456",
            parent_document_id="parent789",
        )

        mock_client.post.assert_called_once_with(
            "documents.move",
            {
                "id": "doc123",
                "collectionId": "col456",
                "parentDocumentId": "parent789",
            },
        )
        assert "Document moved successfully" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_organization.get_outline_client"
    )
    async def test_move_document_no_destination(
        self, mock_get_client, register_organization_tools
    ):
        """Test move_document without collection_id or parent_document_id."""
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

        result = await register_organization_tools.tools["move_document"](
            document_id="doc123"
        )

        # Should not call the client
        mock_client.post.assert_not_called()
        assert "Error" in result
        assert "collection_id or parent_document_id" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_organization.get_outline_client"
    )
    async def test_move_document_failure(
        self, mock_get_client, register_organization_tools
    ):
        """Test move_document when API returns no data."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {}
        mock_get_client.return_value = mock_client

        result = await register_organization_tools.tools["move_document"](
            document_id="doc123", collection_id="col456"
        )

        assert "Failed to move document" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_organization.get_outline_client"
    )
    async def test_move_document_client_error(
        self, mock_get_client, register_organization_tools
    ):
        """Test move_document with client error."""
        mock_client = AsyncMock()
        mock_client.post.side_effect = OutlineClientError("API error")
        mock_get_client.return_value = mock_client

        result = await register_organization_tools.tools["move_document"](
            document_id="doc123", collection_id="col456"
        )

        assert "Error moving document" in result
        assert "API error" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_organization.get_outline_client"
    )
    async def test_move_document_unexpected_error(
        self, mock_get_client, register_organization_tools
    ):
        """Test move_document with unexpected error."""
        mock_client = AsyncMock()
        mock_client.post.side_effect = ValueError("Unexpected error")
        mock_get_client.return_value = mock_client

        result = await register_organization_tools.tools["move_document"](
            document_id="doc123", collection_id="col456"
        )

        assert "Unexpected error" in result
