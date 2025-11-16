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
    "documents": {"count": 5},
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

    def test_format_collection_metadata_structure(self):
        """Test collection metadata format is key-value pairs."""
        result = _format_collection_metadata(SAMPLE_COLLECTION)
        lines = result.strip().split("\n")

        # Verify key-value format
        assert lines[0] == "Name: Test Collection"
        assert lines[1] == "Documents: 5"
        assert "Description: A test collection for unit tests" in result
        assert "Color: #FF0000" in result

    def test_format_collection_metadata_minimal(self):
        """Test collection with only required fields."""
        minimal_collection = {"name": "Minimal", "documents": {"count": 0}}

        result = _format_collection_metadata(minimal_collection)
        lines = result.strip().split("\n")

        # Should have exactly 2 lines (name and documents)
        assert len(lines) == 2
        assert lines[0] == "Name: Minimal"
        assert lines[1] == "Documents: 0"
        # Should not include optional fields
        assert "Description" not in result
        assert "Color" not in result

    def test_format_collection_tree_structure(self):
        """Test tree maintains proper hierarchical structure."""
        result = _format_collection_tree(SAMPLE_DOCUMENT_TREE)
        lines = result.strip().split("\n")

        # Verify parent has no indentation
        assert lines[0].startswith("- Parent Document")
        assert lines[3].startswith("- Another Parent")

        # Verify children have exactly 2 spaces indentation
        assert lines[1].startswith("  - Child Document 1")
        assert lines[2].startswith("  - Child Document 2")

        # Verify parent-child count
        parents = [line for line in lines if not line.startswith("  ")]
        children = [line for line in lines if line.startswith("  - ")]
        assert len(parents) == 2  # 2 parents
        assert len(children) == 2  # 2 children

    def test_format_collection_tree_deep_nesting(self):
        """Test tree with multiple nesting levels."""
        deep_tree = [
            {
                "id": "doc1",
                "title": "Level 1",
                "children": [
                    {
                        "id": "doc2",
                        "title": "Level 2",
                        "children": [
                            {"id": "doc3", "title": "Level 3", "children": []}
                        ],
                    }
                ],
            }
        ]

        result = _format_collection_tree(deep_tree)
        lines = result.strip().split("\n")

        # Verify indentation increases by 2 spaces per level
        assert lines[0].startswith("- Level 1")
        assert lines[1].startswith("  - Level 2")
        assert lines[2].startswith("    - Level 3")

    def test_format_collection_tree_empty(self):
        """Test formatting empty tree."""
        result = _format_collection_tree([])
        assert result == ""

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
            mock_client.get_collection.return_value = SAMPLE_COLLECTION
            mock_get_client.return_value = mock_client

            resource_func = register_collection_resources.resources[
                "outline://collection/{collection_id}"
            ]
            result = await resource_func("coll123")

            assert "Name: Test Collection" in result
            assert "Documents: 5" in result
            assert "Description: A test collection for unit tests" in result
            mock_client.get_collection.assert_called_once_with("coll123")

    @pytest.mark.asyncio
    async def test_get_collection_metadata_not_found(
        self, register_collection_resources
    ):
        """Test collection not found."""
        from mcp_outline.utils.outline_client import OutlineError

        with patch(
            "mcp_outline.features.resources.collection_resources."
            "get_outline_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_collection.side_effect = OutlineError(
                "Collection not found"
            )
            mock_get_client.return_value = mock_client

            resource_func = register_collection_resources.resources[
                "outline://collection/{collection_id}"
            ]
            result = await resource_func("nonexistent")

            assert "Outline API error: Collection not found" in result

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
            mock_client.list_documents.return_value = SAMPLE_DOCUMENT_LIST
            mock_get_client.return_value = mock_client

            resource_func = register_collection_resources.resources[
                "outline://collection/{collection_id}/documents"
            ]
            result = await resource_func("coll123")

            assert "# Documents" in result
            assert "Document 1" in result
            assert "Document 2" in result
            mock_client.list_documents.assert_called_once_with(
                collection_id="coll123"
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
            mock_client.list_documents.return_value = []
            mock_get_client.return_value = mock_client

            resource_func = register_collection_resources.resources[
                "outline://collection/{collection_id}/documents"
            ]
            result = await resource_func("coll123")

            assert "No documents in this collection" in result
