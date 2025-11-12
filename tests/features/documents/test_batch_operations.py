"""
Tests for batch operations tools.
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
}

SAMPLE_DOCUMENTS = [
    {"id": "doc1", "title": "Document 1"},
    {"id": "doc2", "title": "Document 2"},
    {"id": "doc3", "title": "Document 3"},
]


@pytest.fixture
def mcp():
    """Fixture to provide mock MCP instance."""
    return MockMCP()


@pytest.fixture
def register_batch_tools(mcp):
    """Fixture to register batch operation tools."""
    from mcp_outline.features.documents.batch_operations import (
        register_tools,
    )

    register_tools(mcp)
    return mcp


class TestBatchArchiveDocuments:
    """Tests for batch_archive_documents tool."""

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.batch_operations.get_outline_client"
    )
    async def test_batch_archive_all_success(
        self, mock_get_client, register_batch_tools
    ):
        """Test batch_archive_documents with all successes."""
        mock_client = AsyncMock()
        mock_client.archive_document.side_effect = [
            {"id": "doc1", "title": "Document 1"},
            {"id": "doc2", "title": "Document 2"},
            {"id": "doc3", "title": "Document 3"},
        ]
        mock_get_client.return_value = mock_client

        result = await register_batch_tools.tools["batch_archive_documents"](
            ["doc1", "doc2", "doc3"]
        )

        assert "Total: 3" in result
        assert "Succeeded: 3" in result
        assert "Failed: 0" in result
        assert "✓" in result
        assert mock_client.archive_document.call_count == 3

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.batch_operations.get_outline_client"
    )
    async def test_batch_archive_all_failures(
        self, mock_get_client, register_batch_tools
    ):
        """Test batch_archive_documents with all failures."""
        mock_client = AsyncMock()
        mock_client.archive_document.side_effect = OutlineClientError(
            "API error"
        )
        mock_get_client.return_value = mock_client

        result = await register_batch_tools.tools["batch_archive_documents"](
            ["doc1", "doc2", "doc3"]
        )

        assert "Total: 3" in result
        assert "Succeeded: 0" in result
        assert "Failed: 3" in result
        assert "✗" in result
        assert "API error" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.batch_operations.get_outline_client"
    )
    async def test_batch_archive_partial_success(
        self, mock_get_client, register_batch_tools
    ):
        """Test batch_archive_documents with mixed results."""
        mock_client = AsyncMock()
        mock_client.archive_document.side_effect = [
            {"id": "doc1", "title": "Document 1"},
            OutlineClientError("Not found"),
            {"id": "doc3", "title": "Document 3"},
        ]
        mock_get_client.return_value = mock_client

        result = await register_batch_tools.tools["batch_archive_documents"](
            ["doc1", "doc2", "doc3"]
        )

        assert "Total: 3" in result
        assert "Succeeded: 2" in result
        assert "Failed: 1" in result
        assert "Document 1" in result
        assert "Document 3" in result
        assert "Not found" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.batch_operations.get_outline_client"
    )
    async def test_batch_archive_empty_list(
        self, mock_get_client, register_batch_tools
    ):
        """Test batch_archive_documents with empty list."""
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

        result = await register_batch_tools.tools["batch_archive_documents"](
            []
        )

        assert "Error: No document IDs provided" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.batch_operations.get_outline_client"
    )
    async def test_batch_archive_single_document(
        self, mock_get_client, register_batch_tools
    ):
        """Test batch_archive_documents with single document."""
        mock_client = AsyncMock()
        mock_client.archive_document.return_value = {
            "id": "doc1",
            "title": "Single Document",
        }
        mock_get_client.return_value = mock_client

        result = await register_batch_tools.tools["batch_archive_documents"](
            ["doc1"]
        )

        assert "Total: 1" in result
        assert "Succeeded: 1" in result
        assert "Failed: 0" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.batch_operations.get_outline_client"
    )
    async def test_batch_archive_no_document_returned(
        self, mock_get_client, register_batch_tools
    ):
        """Test batch_archive_documents when API returns None."""
        mock_client = AsyncMock()
        mock_client.archive_document.return_value = None
        mock_get_client.return_value = mock_client

        result = await register_batch_tools.tools["batch_archive_documents"](
            ["doc1"]
        )

        assert "Failed: 1" in result
        assert "No document returned from API" in result


class TestBatchMoveDocuments:
    """Tests for batch_move_documents tool."""

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.batch_operations.get_outline_client"
    )
    async def test_batch_move_all_success(
        self, mock_get_client, register_batch_tools
    ):
        """Test batch_move_documents with all successes."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "data": {"id": "doc1", "title": "Moved Doc"}
        }
        mock_get_client.return_value = mock_client

        result = await register_batch_tools.tools["batch_move_documents"](
            ["doc1", "doc2"], collection_id="col123"
        )

        assert "Total: 2" in result
        assert "Succeeded: 2" in result
        assert "Failed: 0" in result
        assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.batch_operations.get_outline_client"
    )
    async def test_batch_move_no_destination(
        self, mock_get_client, register_batch_tools
    ):
        """Test batch_move_documents without collection or parent."""
        result = await register_batch_tools.tools["batch_move_documents"](
            ["doc1", "doc2"]
        )

        assert "Error" in result
        assert "collection_id or parent_document_id" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.batch_operations.get_outline_client"
    )
    async def test_batch_move_with_parent(
        self, mock_get_client, register_batch_tools
    ):
        """Test batch_move_documents with parent document."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "data": {"id": "doc1", "title": "Moved Doc"}
        }
        mock_get_client.return_value = mock_client

        result = await register_batch_tools.tools["batch_move_documents"](
            ["doc1"], parent_document_id="parent123"
        )

        assert "Succeeded: 1" in result
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args[0]
        assert call_args[0] == "documents.move"
        assert call_args[1]["parentDocumentId"] == "parent123"

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.batch_operations.get_outline_client"
    )
    async def test_batch_move_partial_success(
        self, mock_get_client, register_batch_tools
    ):
        """Test batch_move_documents with mixed results."""
        mock_client = AsyncMock()
        mock_client.post.side_effect = [
            {"data": {"id": "doc1", "title": "Doc 1"}},
            OutlineClientError("Permission denied"),
            {"data": {"id": "doc3", "title": "Doc 3"}},
        ]
        mock_get_client.return_value = mock_client

        result = await register_batch_tools.tools["batch_move_documents"](
            ["doc1", "doc2", "doc3"], collection_id="col123"
        )

        assert "Total: 3" in result
        assert "Succeeded: 2" in result
        assert "Failed: 1" in result
        assert "Permission denied" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.batch_operations.get_outline_client"
    )
    async def test_batch_move_empty_list(
        self, mock_get_client, register_batch_tools
    ):
        """Test batch_move_documents with empty list."""
        result = await register_batch_tools.tools["batch_move_documents"](
            [], collection_id="col123"
        )

        assert "Error: No document IDs provided" in result


class TestBatchDeleteDocuments:
    """Tests for batch_delete_documents tool."""

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.batch_operations.get_outline_client"
    )
    async def test_batch_delete_to_trash_success(
        self, mock_get_client, register_batch_tools
    ):
        """Test batch_delete_documents moving to trash."""
        mock_client = AsyncMock()
        mock_client.get_document.side_effect = [
            {"id": "doc1", "title": "Document 1"},
            {"id": "doc2", "title": "Document 2"},
        ]
        mock_client.post.return_value = {"success": True}
        mock_get_client.return_value = mock_client

        result = await register_batch_tools.tools["batch_delete_documents"](
            ["doc1", "doc2"], permanent=False
        )

        assert "Total: 2" in result
        assert "Succeeded: 2" in result
        assert "Failed: 0" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.batch_operations.get_outline_client"
    )
    async def test_batch_delete_permanent_success(
        self, mock_get_client, register_batch_tools
    ):
        """Test batch_delete_documents with permanent deletion."""
        mock_client = AsyncMock()
        mock_client.permanently_delete_document.return_value = True
        mock_get_client.return_value = mock_client

        result = await register_batch_tools.tools["batch_delete_documents"](
            ["doc1", "doc2"], permanent=True
        )

        assert "Total: 2" in result
        assert "Succeeded: 2" in result
        assert mock_client.permanently_delete_document.call_count == 2

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.batch_operations.get_outline_client"
    )
    async def test_batch_delete_partial_success(
        self, mock_get_client, register_batch_tools
    ):
        """Test batch_delete_documents with mixed results."""
        mock_client = AsyncMock()
        mock_client.get_document.side_effect = [
            {"id": "doc1", "title": "Document 1"},
            OutlineClientError("Not found"),
        ]
        mock_client.post.return_value = {"success": True}
        mock_get_client.return_value = mock_client

        result = await register_batch_tools.tools["batch_delete_documents"](
            ["doc1", "doc2"], permanent=False
        )

        assert "Total: 2" in result
        assert "Succeeded: 1" in result
        assert "Failed: 1" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.batch_operations.get_outline_client"
    )
    async def test_batch_delete_empty_list(
        self, mock_get_client, register_batch_tools
    ):
        """Test batch_delete_documents with empty list."""
        result = await register_batch_tools.tools["batch_delete_documents"]([])

        assert "Error: No document IDs provided" in result


class TestBatchUpdateDocuments:
    """Tests for batch_update_documents tool."""

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.batch_operations.get_outline_client"
    )
    async def test_batch_update_all_success(
        self, mock_get_client, register_batch_tools
    ):
        """Test batch_update_documents with all successes."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "data": {"id": "doc1", "title": "Updated Title"}
        }
        mock_get_client.return_value = mock_client

        updates = [
            {"id": "doc1", "title": "New Title 1"},
            {"id": "doc2", "text": "New content"},
            {"id": "doc3", "title": "Title 3", "text": "Content 3"},
        ]

        result = await register_batch_tools.tools["batch_update_documents"](
            updates
        )

        assert "Total: 3" in result
        assert "Succeeded: 3" in result
        assert "Failed: 0" in result
        assert mock_client.post.call_count == 3

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.batch_operations.get_outline_client"
    )
    async def test_batch_update_with_append(
        self, mock_get_client, register_batch_tools
    ):
        """Test batch_update_documents with append flag."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "data": {"id": "doc1", "title": "Document"}
        }
        mock_get_client.return_value = mock_client

        updates = [{"id": "doc1", "text": "Appended content", "append": True}]

        result = await register_batch_tools.tools["batch_update_documents"](
            updates
        )

        assert "Succeeded: 1" in result
        call_args = mock_client.post.call_args[0]
        assert call_args[1]["append"] is True

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.batch_operations.get_outline_client"
    )
    async def test_batch_update_missing_id(
        self, mock_get_client, register_batch_tools
    ):
        """Test batch_update_documents with missing document ID."""
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

        updates = [{"title": "No ID"}]

        result = await register_batch_tools.tools["batch_update_documents"](
            updates
        )

        assert "Failed: 1" in result
        assert "Missing document ID" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.batch_operations.get_outline_client"
    )
    async def test_batch_update_partial_success(
        self, mock_get_client, register_batch_tools
    ):
        """Test batch_update_documents with mixed results."""
        mock_client = AsyncMock()
        mock_client.post.side_effect = [
            {"data": {"id": "doc1", "title": "Updated"}},
            OutlineClientError("Permission denied"),
        ]
        mock_get_client.return_value = mock_client

        updates = [
            {"id": "doc1", "title": "Title 1"},
            {"id": "doc2", "title": "Title 2"},
        ]

        result = await register_batch_tools.tools["batch_update_documents"](
            updates
        )

        assert "Total: 2" in result
        assert "Succeeded: 1" in result
        assert "Failed: 1" in result
        assert "Permission denied" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.batch_operations.get_outline_client"
    )
    async def test_batch_update_empty_list(
        self, mock_get_client, register_batch_tools
    ):
        """Test batch_update_documents with empty list."""
        result = await register_batch_tools.tools["batch_update_documents"]([])

        assert "Error: No updates provided" in result


class TestBatchCreateDocuments:
    """Tests for batch_create_documents tool."""

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.batch_operations.get_outline_client"
    )
    async def test_batch_create_all_success(
        self, mock_get_client, register_batch_tools
    ):
        """Test batch_create_documents with all successes."""
        mock_client = AsyncMock()
        mock_client.post.side_effect = [
            {"data": {"id": "new1", "title": "Document 1"}},
            {"data": {"id": "new2", "title": "Document 2"}},
            {"data": {"id": "new3", "title": "Document 3"}},
        ]
        mock_get_client.return_value = mock_client

        documents = [
            {"title": "Doc 1", "collection_id": "col1"},
            {"title": "Doc 2", "collection_id": "col1", "text": "Content"},
            {
                "title": "Doc 3",
                "collection_id": "col1",
                "publish": False,
            },
        ]

        result = await register_batch_tools.tools["batch_create_documents"](
            documents
        )

        assert "Total: 3" in result
        assert "Succeeded: 3" in result
        assert "Failed: 0" in result
        assert "new1" in result
        assert "new2" in result
        assert "new3" in result
        assert mock_client.post.call_count == 3

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.batch_operations.get_outline_client"
    )
    async def test_batch_create_missing_title(
        self, mock_get_client, register_batch_tools
    ):
        """Test batch_create_documents with missing title."""
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

        documents = [{"collection_id": "col1"}]

        result = await register_batch_tools.tools["batch_create_documents"](
            documents
        )

        assert "Failed: 1" in result
        assert "Missing required field: title" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.batch_operations.get_outline_client"
    )
    async def test_batch_create_missing_collection_id(
        self, mock_get_client, register_batch_tools
    ):
        """Test batch_create_documents with missing collection_id."""
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

        documents = [{"title": "Document"}]

        result = await register_batch_tools.tools["batch_create_documents"](
            documents
        )

        assert "Failed: 1" in result
        assert "Missing required field: collection_id" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.batch_operations.get_outline_client"
    )
    async def test_batch_create_with_parent(
        self, mock_get_client, register_batch_tools
    ):
        """Test batch_create_documents with parent document."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "data": {"id": "new1", "title": "Child Doc"}
        }
        mock_get_client.return_value = mock_client

        documents = [
            {
                "title": "Child",
                "collection_id": "col1",
                "parent_document_id": "parent123",
            }
        ]

        result = await register_batch_tools.tools["batch_create_documents"](
            documents
        )

        assert "Succeeded: 1" in result
        call_args = mock_client.post.call_args[0]
        assert call_args[1]["parentDocumentId"] == "parent123"

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.batch_operations.get_outline_client"
    )
    async def test_batch_create_partial_success(
        self, mock_get_client, register_batch_tools
    ):
        """Test batch_create_documents with mixed results."""
        mock_client = AsyncMock()
        mock_client.post.side_effect = [
            {"data": {"id": "new1", "title": "Doc 1"}},
            OutlineClientError("Quota exceeded"),
            {"data": {"id": "new3", "title": "Doc 3"}},
        ]
        mock_get_client.return_value = mock_client

        documents = [
            {"title": "Doc 1", "collection_id": "col1"},
            {"title": "Doc 2", "collection_id": "col1"},
            {"title": "Doc 3", "collection_id": "col1"},
        ]

        result = await register_batch_tools.tools["batch_create_documents"](
            documents
        )

        assert "Total: 3" in result
        assert "Succeeded: 2" in result
        assert "Failed: 1" in result
        assert "Quota exceeded" in result
        assert "new1" in result
        assert "new3" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.batch_operations.get_outline_client"
    )
    async def test_batch_create_empty_list(
        self, mock_get_client, register_batch_tools
    ):
        """Test batch_create_documents with empty list."""
        result = await register_batch_tools.tools["batch_create_documents"]([])

        assert "Error: No documents provided" in result


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_create_result_entry_success(self):
        """Test _create_result_entry for successful operation."""
        from mcp_outline.features.documents.batch_operations import (
            _create_result_entry,
        )

        result = _create_result_entry(
            "doc123", "success", title="Test Document"
        )

        assert result["id"] == "doc123"
        assert result["status"] == "success"
        assert result["title"] == "Test Document"
        assert "error" not in result

    def test_create_result_entry_failure(self):
        """Test _create_result_entry for failed operation."""
        from mcp_outline.features.documents.batch_operations import (
            _create_result_entry,
        )

        result = _create_result_entry("doc123", "failed", error="Not found")

        assert result["id"] == "doc123"
        assert result["status"] == "failed"
        assert result["error"] == "Not found"
        assert "title" not in result

    def test_format_batch_results_all_success(self):
        """Test _format_batch_results with all successes."""
        from mcp_outline.features.documents.batch_operations import (
            _format_batch_results,
        )

        results = [
            {"id": "doc1", "status": "success", "title": "Doc 1"},
            {"id": "doc2", "status": "success", "title": "Doc 2"},
        ]

        output = _format_batch_results("archive", 2, 2, 0, results)

        assert "Total: 2" in output
        assert "Succeeded: 2" in output
        assert "Failed: 0" in output
        assert "✓ All 2 documents archived successfully" in output

    def test_format_batch_results_all_failure(self):
        """Test _format_batch_results with all failures."""
        from mcp_outline.features.documents.batch_operations import (
            _format_batch_results,
        )

        results = [
            {"id": "doc1", "status": "failed", "error": "Error 1"},
            {"id": "doc2", "status": "failed", "error": "Error 2"},
        ]

        output = _format_batch_results("delete", 2, 0, 2, results)

        assert "Total: 2" in output
        assert "Succeeded: 0" in output
        assert "Failed: 2" in output
        assert "✗ All 2 operations failed" in output

    def test_format_batch_results_mixed(self):
        """Test _format_batch_results with mixed results."""
        from mcp_outline.features.documents.batch_operations import (
            _format_batch_results,
        )

        results = [
            {"id": "doc1", "status": "success", "title": "Doc 1"},
            {"id": "doc2", "status": "failed", "error": "Not found"},
            {"id": "doc3", "status": "success", "title": "Doc 3"},
        ]

        output = _format_batch_results("move", 3, 2, 1, results)

        assert "Total: 3" in output
        assert "Succeeded: 2" in output
        assert "Failed: 1" in output
        assert "✓ doc1 - Doc 1" in output
        assert "✓ doc3 - Doc 3" in output
        assert "✗ doc2 - Error: Not found" in output
