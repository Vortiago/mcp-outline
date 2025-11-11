"""
Tests for document lifecycle tools.
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


# Sample document data
SAMPLE_DOCUMENT = {
    "id": "doc123",
    "title": "Test Document",
    "text": "Sample content",
    "updatedAt": "2023-01-01T12:00:00Z",
}

SAMPLE_DOCUMENTS_LIST = [
    {
        "id": "doc1",
        "title": "Archived Doc 1",
        "updatedAt": "2023-01-01T12:00:00Z",
    },
    {
        "id": "doc2",
        "title": "Archived Doc 2",
        "updatedAt": "2023-01-02T12:00:00Z",
    },
]


@pytest.fixture
def mcp():
    """Fixture to provide mock MCP instance."""
    return MockMCP()


@pytest.fixture
def register_lifecycle_tools(mcp):
    """Fixture to register document lifecycle tools."""
    from mcp_outline.features.documents.document_lifecycle import (
        register_tools,
    )

    register_tools(mcp)
    return mcp


class TestArchiveDocument:
    """Tests for archive_document tool."""

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_lifecycle.get_outline_client"
    )
    async def test_archive_document_success(
        self, mock_get_client, register_lifecycle_tools
    ):
        """Test archive_document tool success case."""
        mock_client = AsyncMock()
        mock_client.archive_document.return_value = SAMPLE_DOCUMENT
        mock_get_client.return_value = mock_client

        result = await register_lifecycle_tools.tools["archive_document"](
            "doc123"
        )

        mock_client.archive_document.assert_called_once_with("doc123")
        assert "Document archived successfully" in result
        assert "Test Document" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_lifecycle.get_outline_client"
    )
    async def test_archive_document_no_document_returned(
        self, mock_get_client, register_lifecycle_tools
    ):
        """Test archive_document when no document is returned."""
        mock_client = AsyncMock()
        mock_client.archive_document.return_value = None
        mock_get_client.return_value = mock_client

        result = await register_lifecycle_tools.tools["archive_document"](
            "doc123"
        )

        assert "Failed to archive document" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_lifecycle.get_outline_client"
    )
    async def test_archive_document_client_error(
        self, mock_get_client, register_lifecycle_tools
    ):
        """Test archive_document with client error."""
        mock_client = AsyncMock()
        mock_client.archive_document.side_effect = OutlineClientError(
            "API error"
        )
        mock_get_client.return_value = mock_client

        result = await register_lifecycle_tools.tools["archive_document"](
            "doc123"
        )

        assert "Error archiving document" in result
        assert "API error" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_lifecycle.get_outline_client"
    )
    async def test_archive_document_unexpected_error(
        self, mock_get_client, register_lifecycle_tools
    ):
        """Test archive_document with unexpected error."""
        mock_client = AsyncMock()
        mock_client.archive_document.side_effect = ValueError(
            "Unexpected error"
        )
        mock_get_client.return_value = mock_client

        result = await register_lifecycle_tools.tools["archive_document"](
            "doc123"
        )

        assert "Unexpected error" in result


class TestUnarchiveDocument:
    """Tests for unarchive_document tool."""

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_lifecycle.get_outline_client"
    )
    async def test_unarchive_document_success(
        self, mock_get_client, register_lifecycle_tools
    ):
        """Test unarchive_document tool success case."""
        mock_client = AsyncMock()
        mock_client.unarchive_document.return_value = SAMPLE_DOCUMENT
        mock_get_client.return_value = mock_client

        result = await register_lifecycle_tools.tools["unarchive_document"](
            "doc123"
        )

        mock_client.unarchive_document.assert_called_once_with("doc123")
        assert "Document unarchived successfully" in result
        assert "Test Document" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_lifecycle.get_outline_client"
    )
    async def test_unarchive_document_no_document_returned(
        self, mock_get_client, register_lifecycle_tools
    ):
        """Test unarchive_document when no document is returned."""
        mock_client = AsyncMock()
        mock_client.unarchive_document.return_value = None
        mock_get_client.return_value = mock_client

        result = await register_lifecycle_tools.tools["unarchive_document"](
            "doc123"
        )

        assert "Failed to unarchive document" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_lifecycle.get_outline_client"
    )
    async def test_unarchive_document_client_error(
        self, mock_get_client, register_lifecycle_tools
    ):
        """Test unarchive_document with client error."""
        mock_client = AsyncMock()
        mock_client.unarchive_document.side_effect = OutlineClientError(
            "API error"
        )
        mock_get_client.return_value = mock_client

        result = await register_lifecycle_tools.tools["unarchive_document"](
            "doc123"
        )

        assert "Error unarchiving document" in result
        assert "API error" in result


class TestDeleteDocument:
    """Tests for delete_document tool."""

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_lifecycle.get_outline_client"
    )
    async def test_delete_document_to_trash_success(
        self, mock_get_client, register_lifecycle_tools
    ):
        """Test delete_document tool moving to trash (default)."""
        mock_client = AsyncMock()
        mock_client.get_document.return_value = SAMPLE_DOCUMENT
        mock_client.post.return_value = {"success": True}
        mock_get_client.return_value = mock_client

        result = await register_lifecycle_tools.tools["delete_document"](
            "doc123"
        )

        mock_client.get_document.assert_called_once_with("doc123")
        mock_client.post.assert_called_once_with(
            "documents.delete", {"id": "doc123"}
        )
        assert "Document moved to trash" in result
        assert "Test Document" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_lifecycle.get_outline_client"
    )
    async def test_delete_document_to_trash_failure(
        self, mock_get_client, register_lifecycle_tools
    ):
        """Test delete_document when move to trash fails."""
        mock_client = AsyncMock()
        mock_client.get_document.return_value = SAMPLE_DOCUMENT
        mock_client.post.return_value = {"success": False}
        mock_get_client.return_value = mock_client

        result = await register_lifecycle_tools.tools["delete_document"](
            "doc123"
        )

        assert "Failed to move document to trash" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_lifecycle.get_outline_client"
    )
    async def test_delete_document_permanently_success(
        self, mock_get_client, register_lifecycle_tools
    ):
        """Test delete_document tool with permanent deletion."""
        mock_client = AsyncMock()
        mock_client.permanently_delete_document.return_value = True
        mock_get_client.return_value = mock_client

        result = await register_lifecycle_tools.tools["delete_document"](
            "doc123", permanent=True
        )

        mock_client.permanently_delete_document.assert_called_once_with(
            "doc123"
        )
        assert "Document permanently deleted" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_lifecycle.get_outline_client"
    )
    async def test_delete_document_permanently_failure(
        self, mock_get_client, register_lifecycle_tools
    ):
        """Test delete_document permanent deletion failure."""
        mock_client = AsyncMock()
        mock_client.permanently_delete_document.return_value = False
        mock_get_client.return_value = mock_client

        result = await register_lifecycle_tools.tools["delete_document"](
            "doc123", permanent=True
        )

        assert "Failed to permanently delete document" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_lifecycle.get_outline_client"
    )
    async def test_delete_document_client_error(
        self, mock_get_client, register_lifecycle_tools
    ):
        """Test delete_document with client error."""
        mock_client = AsyncMock()
        mock_client.get_document.side_effect = OutlineClientError("API error")
        mock_get_client.return_value = mock_client

        result = await register_lifecycle_tools.tools["delete_document"](
            "doc123"
        )

        assert "Error deleting document" in result
        assert "API error" in result


class TestRestoreDocument:
    """Tests for restore_document tool."""

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_lifecycle.get_outline_client"
    )
    async def test_restore_document_success(
        self, mock_get_client, register_lifecycle_tools
    ):
        """Test restore_document tool success case."""
        mock_client = AsyncMock()
        mock_client.restore_document.return_value = SAMPLE_DOCUMENT
        mock_get_client.return_value = mock_client

        result = await register_lifecycle_tools.tools["restore_document"](
            "doc123"
        )

        mock_client.restore_document.assert_called_once_with("doc123")
        assert "Document restored successfully" in result
        assert "Test Document" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_lifecycle.get_outline_client"
    )
    async def test_restore_document_no_document_returned(
        self, mock_get_client, register_lifecycle_tools
    ):
        """Test restore_document when no document is returned."""
        mock_client = AsyncMock()
        mock_client.restore_document.return_value = None
        mock_get_client.return_value = mock_client

        result = await register_lifecycle_tools.tools["restore_document"](
            "doc123"
        )

        assert "Failed to restore document from trash" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_lifecycle.get_outline_client"
    )
    async def test_restore_document_client_error(
        self, mock_get_client, register_lifecycle_tools
    ):
        """Test restore_document with client error."""
        mock_client = AsyncMock()
        mock_client.restore_document.side_effect = OutlineClientError(
            "API error"
        )
        mock_get_client.return_value = mock_client

        result = await register_lifecycle_tools.tools["restore_document"](
            "doc123"
        )

        assert "Error restoring document" in result
        assert "API error" in result


class TestListArchivedDocuments:
    """Tests for list_archived_documents tool."""

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_lifecycle.get_outline_client"
    )
    async def test_list_archived_documents_success(
        self, mock_get_client, register_lifecycle_tools
    ):
        """Test list_archived_documents tool success case."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {"data": SAMPLE_DOCUMENTS_LIST}
        mock_get_client.return_value = mock_client

        result = await register_lifecycle_tools.tools[
            "list_archived_documents"
        ]()

        mock_client.post.assert_called_once_with("documents.archived")
        assert "Archived Documents" in result
        assert "Archived Doc 1" in result
        assert "Archived Doc 2" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_lifecycle.get_outline_client"
    )
    async def test_list_archived_documents_empty(
        self, mock_get_client, register_lifecycle_tools
    ):
        """Test list_archived_documents with no archived documents."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {"data": []}
        mock_get_client.return_value = mock_client

        result = await register_lifecycle_tools.tools[
            "list_archived_documents"
        ]()

        assert "archived documents" in result.lower()

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_lifecycle.get_outline_client"
    )
    async def test_list_archived_documents_client_error(
        self, mock_get_client, register_lifecycle_tools
    ):
        """Test list_archived_documents with client error."""
        mock_client = AsyncMock()
        mock_client.post.side_effect = OutlineClientError("API error")
        mock_get_client.return_value = mock_client

        result = await register_lifecycle_tools.tools[
            "list_archived_documents"
        ]()

        assert "Error listing archived documents" in result
        assert "API error" in result


class TestListTrash:
    """Tests for list_trash tool."""

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_lifecycle.get_outline_client"
    )
    async def test_list_trash_success(
        self, mock_get_client, register_lifecycle_tools
    ):
        """Test list_trash tool success case."""
        mock_client = AsyncMock()
        mock_client.list_trash.return_value = SAMPLE_DOCUMENTS_LIST
        mock_get_client.return_value = mock_client

        result = await register_lifecycle_tools.tools["list_trash"]()

        mock_client.list_trash.assert_called_once()
        assert "Documents in Trash" in result
        assert "Archived Doc 1" in result
        assert "Archived Doc 2" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_lifecycle.get_outline_client"
    )
    async def test_list_trash_empty(
        self, mock_get_client, register_lifecycle_tools
    ):
        """Test list_trash with no documents in trash."""
        mock_client = AsyncMock()
        mock_client.list_trash.return_value = []
        mock_get_client.return_value = mock_client

        result = await register_lifecycle_tools.tools["list_trash"]()

        assert "documents in trash" in result.lower()

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_lifecycle.get_outline_client"
    )
    async def test_list_trash_client_error(
        self, mock_get_client, register_lifecycle_tools
    ):
        """Test list_trash with client error."""
        mock_client = AsyncMock()
        mock_client.list_trash.side_effect = OutlineClientError("API error")
        mock_get_client.return_value = mock_client

        result = await register_lifecycle_tools.tools["list_trash"]()

        assert "Error listing trash" in result
        assert "API error" in result
