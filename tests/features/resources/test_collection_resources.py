"""
Tests for collection-related MCP resources.
"""

from unittest.mock import AsyncMock, patch

import pytest

from mcp_outline.features.documents.common import OutlineClientError
from mcp_outline.features.resources.collection_resources import (
    _format_collection_metadata,
    _format_collection_tree,
    _format_document_list,
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
SAMPLE_COLLECTION = {
    "id": "coll123",
    "name": "Test Collection",
    "description": "A test collection for unit tests",
    "color": "#FF0000",
    "documents": 5,
}

SAMPLE_DOCUMENT_TREE = [
    {
        "id": "doc1",
        "title": "Parent Document",
        "children": [
            {
                "id": "doc2",
                "title": "Child Document 1",
                "children": [],
            },
            {
                "id": "doc3",
                "title": "Child Document 2",
                "children": [],
            },
        ],
    },
    {
        "id": "doc4",
        "title": "Another Parent",
        "children": [],
    },
]

SAMPLE_DOCUMENT_LIST = [
    {
        "id": "doc1",
        "title": "Document 1",
        "updatedAt": "2023-01-01T12:00:00Z",
    },
    {
        "id": "doc2",
        "title": "Document 2",
        "updatedAt": "2023-01-02T12:00:00Z",
    },
]


@pytest.fixture
def mcp():
    """Fixture to provide mock MCP instance."""
    return MockMCP()


@pytest.fixture
def register_collection_resources(mcp):
    """Fixture to register collection resources."""
    from mcp_outline.features.resources.collection_resources import (
        register_resources,
    )

    register_resources(mcp)
    return mcp


class TestCollectionResourceFormatters:
    """Tests for collection resource formatting functions."""

    def test_format_collection_metadata(self):
        """Test formatting collection metadata."""
        result = _format_collection_metadata(SAMPLE_COLLECTION)

        assert "# Test Collection" in result
        assert "A test collection for unit tests" in result
        assert "**Documents**: 5" in result
        assert "**Color**: #FF0000" in result

    def test_format_collection_metadata_no_description(self):
        """Test formatting collection without description."""
        collection = SAMPLE_COLLECTION.copy()
        collection["description"] = ""

        result = _format_collection_metadata(collection)

        assert "# Test Collection" in result
        assert "**Documents**: 5" in result

    def test_format_collection_tree(self):
        """Test formatting collection document tree."""
        result = _format_collection_tree(SAMPLE_DOCUMENT_TREE)

        assert "- Parent Document (doc1)" in result
        assert "  - Child Document 1 (doc2)" in result
        assert "  - Child Document 2 (doc3)" in result
        assert "- Another Parent (doc4)" in result

    def test_format_collection_tree_empty(self):
        """Test formatting empty tree."""
        result = _format_collection_tree([])
        assert result == ""

    def test_format_document_list(self):
        """Test formatting document list."""
        result = _format_document_list(SAMPLE_DOCUMENT_LIST)

        assert "# Documents" in result
        assert "**Document 1**" in result
        assert "`doc1`" in result
        assert "Last updated: 2023-01-01T12:00:00Z" in result

    def test_format_document_list_empty(self):
        """Test formatting empty document list."""
        result = _format_document_list([])
        assert "No documents in this collection" in result


class TestCollectionResources:
    """Tests for collection resource handlers."""

    @pytest.mark.asyncio
    async def test_get_collection_metadata_success(
        self, register_collection_resources
    ):
        """Test successful collection metadata retrieval."""
        with patch(
            "mcp_outline.features.resources.collection_resources."
            "get_outline_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.list_collections.return_value = [SAMPLE_COLLECTION]
            mock_get_client.return_value = mock_client

            resource_func = register_collection_resources.resources[
                "outline://collection/{collection_id}"
            ]
            result = await resource_func("coll123")

            assert "# Test Collection" in result
            assert "A test collection for unit tests" in result
            mock_client.list_collections.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_collection_metadata_not_found(
        self, register_collection_resources
    ):
        """Test collection not found."""
        with patch(
            "mcp_outline.features.resources.collection_resources."
            "get_outline_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.list_collections.return_value = []
            mock_get_client.return_value = mock_client

            resource_func = register_collection_resources.resources[
                "outline://collection/{collection_id}"
            ]
            result = await resource_func("nonexistent")

            assert "Error: Collection nonexistent not found" in result

    @pytest.mark.asyncio
    async def test_get_collection_metadata_error(
        self, register_collection_resources
    ):
        """Test collection metadata retrieval error."""
        with patch(
            "mcp_outline.features.resources.collection_resources."
            "get_outline_client"
        ) as mock_get_client:
            mock_get_client.side_effect = OutlineClientError("API error")

            resource_func = register_collection_resources.resources[
                "outline://collection/{collection_id}"
            ]
            result = await resource_func("coll123")

            assert "Outline client error: API error" in result

    @pytest.mark.asyncio
    async def test_get_collection_tree_success(
        self, register_collection_resources
    ):
        """Test successful collection tree retrieval."""
        with patch(
            "mcp_outline.features.resources.collection_resources."
            "get_outline_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_collection_documents.return_value = (
                SAMPLE_DOCUMENT_TREE
            )
            mock_get_client.return_value = mock_client

            resource_func = register_collection_resources.resources[
                "outline://collection/{collection_id}/tree"
            ]
            result = await resource_func("coll123")

            assert "# Document Tree" in result
            assert "Parent Document" in result
            assert "Child Document 1" in result
            mock_client.get_collection_documents.assert_called_once_with(
                "coll123"
            )

    @pytest.mark.asyncio
    async def test_get_collection_tree_empty(
        self, register_collection_resources
    ):
        """Test collection tree with no documents."""
        with patch(
            "mcp_outline.features.resources.collection_resources."
            "get_outline_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_collection_documents.return_value = []
            mock_get_client.return_value = mock_client

            resource_func = register_collection_resources.resources[
                "outline://collection/{collection_id}/tree"
            ]
            result = await resource_func("coll123")

            assert "No documents in this collection" in result

    @pytest.mark.asyncio
    async def test_get_collection_documents_success(
        self, register_collection_resources
    ):
        """Test successful collection documents list retrieval."""
        with patch(
            "mcp_outline.features.resources.collection_resources."
            "get_outline_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.search_documents.return_value = {
                "data": SAMPLE_DOCUMENT_LIST
            }
            mock_get_client.return_value = mock_client

            resource_func = register_collection_resources.resources[
                "outline://collection/{collection_id}/documents"
            ]
            result = await resource_func("coll123")

            assert "# Documents" in result
            assert "Document 1" in result
            assert "Document 2" in result
            mock_client.search_documents.assert_called_once_with(
                query="", collection_id="coll123"
            )

    @pytest.mark.asyncio
    async def test_get_collection_documents_empty(
        self, register_collection_resources
    ):
        """Test collection documents with no results."""
        with patch(
            "mcp_outline.features.resources.collection_resources."
            "get_outline_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.search_documents.return_value = {"data": []}
            mock_get_client.return_value = mock_client

            resource_func = register_collection_resources.resources[
                "outline://collection/{collection_id}/documents"
            ]
            result = await resource_func("coll123")

            assert "No documents in this collection" in result
