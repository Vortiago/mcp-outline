"""
Tests for collection management tools.
"""

from unittest.mock import AsyncMock, patch

import pytest

from mcp_outline.features.documents.collection_tools import (
    _format_file_operation,
)
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


# Sample data
SAMPLE_COLLECTION = {
    "id": "col123",
    "name": "Test Collection",
    "description": "A test collection",
}

SAMPLE_FILE_OPERATION_COMPLETE = {
    "id": "fileop123",
    "state": "complete",
    "type": "export",
    "name": "Test Export",
}

SAMPLE_FILE_OPERATION_PROCESSING = {
    "id": "fileop456",
    "state": "processing",
    "type": "export",
    "name": "Test Export",
}


@pytest.fixture
def mcp():
    """Fixture to provide mock MCP instance."""
    return MockMCP()


@pytest.fixture
def register_collection_tools(mcp):
    """Fixture to register collection management tools."""
    from mcp_outline.features.documents.collection_tools import register_tools

    register_tools(mcp)
    return mcp


class TestFileOperationFormatter:
    """Tests for _format_file_operation formatter."""

    def test_format_file_operation_complete(self):
        """Test formatting complete file operation."""
        result = _format_file_operation(SAMPLE_FILE_OPERATION_COMPLETE)

        assert "Export Operation: Test Export" in result
        assert "State: complete" in result
        assert "Type: export" in result
        assert "fileop123" in result
        assert "export is complete" in result

    def test_format_file_operation_processing(self):
        """Test formatting processing file operation."""
        result = _format_file_operation(SAMPLE_FILE_OPERATION_PROCESSING)

        assert "Export Operation: Test Export" in result
        assert "State: processing" in result
        assert "still in progress" in result
        assert "fileop456" in result

    def test_format_file_operation_empty(self):
        """Test formatting empty file operation."""
        result = _format_file_operation({})

        # Empty dict is falsy so should return no data message
        assert "No file operation data available" in result

    def test_format_file_operation_none(self):
        """Test formatting None file operation."""
        result = _format_file_operation(None)

        assert "No file operation data available" in result


class TestCreateCollection:
    """Tests for create_collection tool."""

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.collection_tools.get_outline_client"
    )
    async def test_create_collection_success(
        self, mock_get_client, register_collection_tools
    ):
        """Test create_collection tool success case."""
        mock_client = AsyncMock()
        mock_client.create_collection.return_value = SAMPLE_COLLECTION
        mock_get_client.return_value = mock_client

        result = await register_collection_tools.tools["create_collection"](
            name="Test Collection", description="A test collection"
        )

        mock_client.create_collection.assert_called_once_with(
            "Test Collection", "A test collection", None
        )
        assert "Collection created successfully" in result
        assert "Test Collection" in result
        assert "col123" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.collection_tools.get_outline_client"
    )
    async def test_create_collection_with_color(
        self, mock_get_client, register_collection_tools
    ):
        """Test create_collection with color specified."""
        mock_client = AsyncMock()
        mock_client.create_collection.return_value = SAMPLE_COLLECTION
        mock_get_client.return_value = mock_client

        result = await register_collection_tools.tools["create_collection"](
            name="Test Collection",
            description="A test collection",
            color="#FF0000",
        )

        mock_client.create_collection.assert_called_once_with(
            "Test Collection", "A test collection", "#FF0000"
        )
        assert "Collection created successfully" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.collection_tools.get_outline_client"
    )
    async def test_create_collection_failure(
        self, mock_get_client, register_collection_tools
    ):
        """Test create_collection when no collection is returned."""
        mock_client = AsyncMock()
        mock_client.create_collection.return_value = None
        mock_get_client.return_value = mock_client

        result = await register_collection_tools.tools["create_collection"](
            name="Test Collection"
        )

        assert "Failed to create collection" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.collection_tools.get_outline_client"
    )
    async def test_create_collection_client_error(
        self, mock_get_client, register_collection_tools
    ):
        """Test create_collection with client error."""
        mock_client = AsyncMock()
        mock_client.create_collection.side_effect = OutlineClientError(
            "API error"
        )
        mock_get_client.return_value = mock_client

        result = await register_collection_tools.tools["create_collection"](
            name="Test Collection"
        )

        assert "Error creating collection" in result
        assert "API error" in result


class TestUpdateCollection:
    """Tests for update_collection tool."""

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.collection_tools.get_outline_client"
    )
    async def test_update_collection_success(
        self, mock_get_client, register_collection_tools
    ):
        """Test update_collection tool success case."""
        mock_client = AsyncMock()
        mock_client.update_collection.return_value = SAMPLE_COLLECTION
        mock_get_client.return_value = mock_client

        result = await register_collection_tools.tools["update_collection"](
            collection_id="col123", name="Updated Collection"
        )

        mock_client.update_collection.assert_called_once_with(
            "col123", "Updated Collection", None, None
        )
        assert "Collection updated successfully" in result
        assert "Test Collection" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.collection_tools.get_outline_client"
    )
    async def test_update_collection_all_fields(
        self, mock_get_client, register_collection_tools
    ):
        """Test update_collection with all fields."""
        mock_client = AsyncMock()
        mock_client.update_collection.return_value = SAMPLE_COLLECTION
        mock_get_client.return_value = mock_client

        result = await register_collection_tools.tools["update_collection"](
            collection_id="col123",
            name="New Name",
            description="New Description",
            color="#00FF00",
        )

        mock_client.update_collection.assert_called_once_with(
            "col123", "New Name", "New Description", "#00FF00"
        )
        assert "Collection updated successfully" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.collection_tools.get_outline_client"
    )
    async def test_update_collection_no_fields(
        self, mock_get_client, register_collection_tools
    ):
        """Test update_collection with no fields to update."""
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

        result = await register_collection_tools.tools["update_collection"](
            collection_id="col123"
        )

        # Should not call the client
        mock_client.update_collection.assert_not_called()
        assert "Error" in result
        assert "at least one field to update" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.collection_tools.get_outline_client"
    )
    async def test_update_collection_failure(
        self, mock_get_client, register_collection_tools
    ):
        """Test update_collection when no collection is returned."""
        mock_client = AsyncMock()
        mock_client.update_collection.return_value = None
        mock_get_client.return_value = mock_client

        result = await register_collection_tools.tools["update_collection"](
            collection_id="col123", name="Updated Name"
        )

        assert "Failed to update collection" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.collection_tools.get_outline_client"
    )
    async def test_update_collection_client_error(
        self, mock_get_client, register_collection_tools
    ):
        """Test update_collection with client error."""
        mock_client = AsyncMock()
        mock_client.update_collection.side_effect = OutlineClientError(
            "API error"
        )
        mock_get_client.return_value = mock_client

        result = await register_collection_tools.tools["update_collection"](
            collection_id="col123", name="Updated Name"
        )

        assert "Error updating collection" in result
        assert "API error" in result


class TestDeleteCollection:
    """Tests for delete_collection tool."""

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.collection_tools.get_outline_client"
    )
    async def test_delete_collection_success(
        self, mock_get_client, register_collection_tools
    ):
        """Test delete_collection tool success case."""
        mock_client = AsyncMock()
        mock_client.delete_collection.return_value = True
        mock_get_client.return_value = mock_client

        result = await register_collection_tools.tools["delete_collection"](
            "col123"
        )

        mock_client.delete_collection.assert_called_once_with("col123")
        assert (
            "Collection and all its documents deleted successfully" in result
        )

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.collection_tools.get_outline_client"
    )
    async def test_delete_collection_failure(
        self, mock_get_client, register_collection_tools
    ):
        """Test delete_collection when deletion fails."""
        mock_client = AsyncMock()
        mock_client.delete_collection.return_value = False
        mock_get_client.return_value = mock_client

        result = await register_collection_tools.tools["delete_collection"](
            "col123"
        )

        assert "Failed to delete collection" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.collection_tools.get_outline_client"
    )
    async def test_delete_collection_client_error(
        self, mock_get_client, register_collection_tools
    ):
        """Test delete_collection with client error."""
        mock_client = AsyncMock()
        mock_client.delete_collection.side_effect = OutlineClientError(
            "API error"
        )
        mock_get_client.return_value = mock_client

        result = await register_collection_tools.tools["delete_collection"](
            "col123"
        )

        assert "Error deleting collection" in result
        assert "API error" in result


class TestExportCollection:
    """Tests for export_collection tool."""

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.collection_tools.get_outline_client"
    )
    async def test_export_collection_success(
        self, mock_get_client, register_collection_tools
    ):
        """Test export_collection tool success case."""
        mock_client = AsyncMock()
        mock_client.export_collection.return_value = (
            SAMPLE_FILE_OPERATION_COMPLETE
        )
        mock_get_client.return_value = mock_client

        result = await register_collection_tools.tools["export_collection"](
            "col123"
        )

        mock_client.export_collection.assert_called_once_with(
            "col123", "outline-markdown"
        )
        assert "Export Operation" in result
        assert "complete" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.collection_tools.get_outline_client"
    )
    async def test_export_collection_custom_format(
        self, mock_get_client, register_collection_tools
    ):
        """Test export_collection with custom format."""
        mock_client = AsyncMock()
        mock_client.export_collection.return_value = (
            SAMPLE_FILE_OPERATION_PROCESSING
        )
        mock_get_client.return_value = mock_client

        result = await register_collection_tools.tools["export_collection"](
            "col123", format="json"
        )

        mock_client.export_collection.assert_called_once_with("col123", "json")
        assert "Export Operation" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.collection_tools.get_outline_client"
    )
    async def test_export_collection_failure(
        self, mock_get_client, register_collection_tools
    ):
        """Test export_collection when no file operation is returned."""
        mock_client = AsyncMock()
        mock_client.export_collection.return_value = None
        mock_get_client.return_value = mock_client

        result = await register_collection_tools.tools["export_collection"](
            "col123"
        )

        assert "Failed to start export operation" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.collection_tools.get_outline_client"
    )
    async def test_export_collection_client_error(
        self, mock_get_client, register_collection_tools
    ):
        """Test export_collection with client error."""
        mock_client = AsyncMock()
        mock_client.export_collection.side_effect = OutlineClientError(
            "API error"
        )
        mock_get_client.return_value = mock_client

        result = await register_collection_tools.tools["export_collection"](
            "col123"
        )

        assert "Error exporting collection" in result
        assert "API error" in result


class TestExportAllCollections:
    """Tests for export_all_collections tool."""

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.collection_tools.get_outline_client"
    )
    async def test_export_all_collections_success(
        self, mock_get_client, register_collection_tools
    ):
        """Test export_all_collections tool success case."""
        mock_client = AsyncMock()
        mock_client.export_all_collections.return_value = (
            SAMPLE_FILE_OPERATION_COMPLETE
        )
        mock_get_client.return_value = mock_client

        result = await register_collection_tools.tools[
            "export_all_collections"
        ]()

        mock_client.export_all_collections.assert_called_once_with(
            "outline-markdown"
        )
        assert "Export Operation" in result
        assert "complete" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.collection_tools.get_outline_client"
    )
    async def test_export_all_collections_custom_format(
        self, mock_get_client, register_collection_tools
    ):
        """Test export_all_collections with custom format."""
        mock_client = AsyncMock()
        mock_client.export_all_collections.return_value = (
            SAMPLE_FILE_OPERATION_PROCESSING
        )
        mock_get_client.return_value = mock_client

        result = await register_collection_tools.tools[
            "export_all_collections"
        ](format="html")

        mock_client.export_all_collections.assert_called_once_with("html")
        assert "Export Operation" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.collection_tools.get_outline_client"
    )
    async def test_export_all_collections_failure(
        self, mock_get_client, register_collection_tools
    ):
        """Test export_all_collections when no file operation is returned."""
        mock_client = AsyncMock()
        mock_client.export_all_collections.return_value = None
        mock_get_client.return_value = mock_client

        result = await register_collection_tools.tools[
            "export_all_collections"
        ]()

        assert "Failed to start export operation" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.collection_tools.get_outline_client"
    )
    async def test_export_all_collections_client_error(
        self, mock_get_client, register_collection_tools
    ):
        """Test export_all_collections with client error."""
        mock_client = AsyncMock()
        mock_client.export_all_collections.side_effect = OutlineClientError(
            "API error"
        )
        mock_get_client.return_value = mock_client

        result = await register_collection_tools.tools[
            "export_all_collections"
        ]()

        assert "Error exporting collections" in result
        assert "API error" in result
