"""
Tests for document search tools.
"""

from unittest.mock import AsyncMock, patch

import pytest

from mcp_outline.features.documents.common import OutlineClientError
from mcp_outline.features.documents.document_search import (
    _format_collection_documents,
    _format_collections,
    _format_documents_list,
    _format_search_results,
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


# Sample test data
SAMPLE_SEARCH_RESULTS = [
    {
        "document": {"id": "doc1", "title": "Test Document 1"},
        "context": "This is a test document.",
    },
    {
        "document": {"id": "doc2", "title": "Test Document 2"},
        "context": "Another test document.",
    },
]

SAMPLE_DOCUMENTS = [
    {
        "id": "doc1",
        "title": "Test Document 1",
        "updatedAt": "2023-01-01T12:00:00Z",
    },
    {
        "id": "doc2",
        "title": "Test Document 2",
        "updatedAt": "2023-01-02T12:00:00Z",
    },
]

SAMPLE_COLLECTIONS = [
    {
        "id": "coll1",
        "name": "Test Collection 1",
        "description": "Collection description",
    },
    {"id": "coll2", "name": "Test Collection 2", "description": ""},
]

SAMPLE_COLLECTION_DOCUMENTS = [
    {
        "id": "doc1",
        "title": "Root Document",
        "children": [
            {"id": "doc2", "title": "Child Document", "children": []}
        ],
    }
]


class TestDocumentSearchFormatters:
    """Tests for document search formatting functions."""

    def test_format_search_results_with_data(self):
        """Test formatting search results with valid data."""
        result = _format_search_results(SAMPLE_SEARCH_RESULTS)

        # Verify the result contains the expected information
        assert "# Search Results" in result
        assert "Test Document 1" in result
        assert "doc1" in result
        assert "This is a test document." in result
        assert "Test Document 2" in result

    def test_format_search_results_empty(self):
        """Test formatting empty search results."""
        result = _format_search_results([])

        assert "No documents found" in result

    def test_format_documents_list_with_data(self):
        """Test formatting document list with valid data."""
        result = _format_documents_list(SAMPLE_DOCUMENTS, "Document List")

        # Verify the result contains the expected information
        assert "# Document List" in result
        assert "Test Document 1" in result
        assert "doc1" in result
        assert "2023-01-01" in result
        assert "Test Document 2" in result

    def test_format_collections_with_data(self):
        """Test formatting collections with valid data."""
        result = _format_collections(SAMPLE_COLLECTIONS)

        # Verify the result contains the expected information
        assert "# Collections" in result
        assert "Test Collection 1" in result
        assert "coll1" in result
        assert "Collection description" in result
        assert "Test Collection 2" in result

    def test_format_collections_empty(self):
        """Test formatting empty collections list."""
        result = _format_collections([])

        assert "No collections found" in result

    def test_format_collection_documents_with_data(self):
        """Test formatting collection document structure with valid data."""
        result = _format_collection_documents(SAMPLE_COLLECTION_DOCUMENTS)

        # Verify the result contains the expected information
        assert "# Collection Structure" in result
        assert "Root Document" in result
        assert "doc1" in result
        assert "Child Document" in result
        assert "doc2" in result

    def test_format_collection_documents_empty(self):
        """Test formatting empty collection document structure."""
        result = _format_collection_documents([])

        assert "No documents found in this collection" in result


@pytest.fixture
def mcp():
    """Fixture to provide mock MCP instance."""
    return MockMCP()


@pytest.fixture
def register_search_tools(mcp):
    """Fixture to register document search tools."""
    from mcp_outline.features.documents.document_search import register_tools

    register_tools(mcp)
    return mcp


class TestDocumentSearchTools:
    """Tests for document search tools."""

    @pytest.mark.asyncio
    @patch("mcp_outline.features.documents.document_search.get_outline_client")
    async def test_search_documents_success(
        self, mock_get_client, register_search_tools
    ):
        """Test search_documents tool success case."""
        # Set up mock client
        mock_client = AsyncMock()
        mock_client.search_documents.return_value = {
            "data": SAMPLE_SEARCH_RESULTS,
            "pagination": {"limit": 25, "offset": 0},
        }
        mock_get_client.return_value = mock_client

        # Call the tool
        result = await register_search_tools.tools["search_documents"](
            "test query"
        )

        # Verify client was called correctly
        mock_client.search_documents.assert_called_once_with(
            "test query", None, 25, 0
        )

        # Verify result contains expected information
        assert "Test Document 1" in result
        assert "doc1" in result

    @pytest.mark.asyncio
    @patch("mcp_outline.features.documents.document_search.get_outline_client")
    async def test_search_documents_with_collection(
        self, mock_get_client, register_search_tools
    ):
        """Test search_documents tool with collection filter."""
        # Set up mock client
        mock_client = AsyncMock()
        mock_client.search_documents.return_value = {
            "data": SAMPLE_SEARCH_RESULTS,
            "pagination": {"limit": 25, "offset": 0},
        }
        mock_get_client.return_value = mock_client

        # Call the tool
        _ = await register_search_tools.tools["search_documents"](
            "test query", "coll1"
        )

        # Verify client was called correctly
        mock_client.search_documents.assert_called_once_with(
            "test query", "coll1", 25, 0
        )

    @pytest.mark.asyncio
    @patch("mcp_outline.features.documents.document_search.get_outline_client")
    async def test_search_documents_client_error(
        self, mock_get_client, register_search_tools
    ):
        """Test search_documents tool with client error."""
        # Set up mock client to raise an error
        mock_client = AsyncMock()
        mock_client.search_documents.side_effect = OutlineClientError(
            "API error"
        )
        mock_get_client.return_value = mock_client

        # Call the tool
        result = await register_search_tools.tools["search_documents"](
            "test query"
        )

        # Verify error is handled and returned
        assert "Error searching documents" in result
        assert "API error" in result

    @pytest.mark.asyncio
    @patch("mcp_outline.features.documents.document_search.get_outline_client")
    async def test_list_collections_success(
        self, mock_get_client, register_search_tools
    ):
        """Test list_collections tool success case."""
        # Set up mock client
        mock_client = AsyncMock()
        mock_client.list_collections.return_value = SAMPLE_COLLECTIONS
        mock_get_client.return_value = mock_client

        # Call the tool
        result = await register_search_tools.tools["list_collections"]()

        # Verify client was called correctly
        mock_client.list_collections.assert_called_once()

        # Verify result contains expected information
        assert "Test Collection 1" in result
        assert "coll1" in result

    @pytest.mark.asyncio
    @patch("mcp_outline.features.documents.document_search.get_outline_client")
    async def test_get_collection_structure_success(
        self, mock_get_client, register_search_tools
    ):
        """Test get_collection_structure tool success case."""
        # Set up mock client
        mock_client = AsyncMock()
        mock_client.get_collection_documents.return_value = (
            SAMPLE_COLLECTION_DOCUMENTS
        )
        mock_get_client.return_value = mock_client

        # Call the tool
        result = await register_search_tools.tools["get_collection_structure"](
            "coll1"
        )

        # Verify client was called correctly
        mock_client.get_collection_documents.assert_called_once_with("coll1")

        # Verify result contains expected information
        assert "Root Document" in result
        assert "Child Document" in result

    @pytest.mark.asyncio
    @patch("mcp_outline.features.documents.document_search.get_outline_client")
    async def test_get_document_id_from_title_exact_match(
        self, mock_get_client, register_search_tools
    ):
        """Test get_document_id_from_title tool with exact match."""
        # Search results with exact title match
        exact_match_results = {
            "data": [{"document": {"id": "doc1", "title": "Exact Match"}}],
            "pagination": {"limit": 25, "offset": 0},
        }

        # Set up mock client
        mock_client = AsyncMock()
        mock_client.search_documents.return_value = exact_match_results
        mock_get_client.return_value = mock_client

        # Call the tool
        result = await register_search_tools.tools[
            "get_document_id_from_title"
        ]("Exact Match")

        # Verify client was called correctly
        mock_client.search_documents.assert_called_once_with(
            "Exact Match", None
        )

        # Verify result contains expected information
        assert "Document ID: doc1" in result
        assert "Exact Match" in result

    @pytest.mark.asyncio
    @patch("mcp_outline.features.documents.document_search.get_outline_client")
    async def test_get_document_id_from_title_best_match(
        self, mock_get_client, register_search_tools
    ):
        """Test get_document_id_from_title tool with best match (non-exact)."""
        # Set up mock client
        mock_client = AsyncMock()
        mock_client.search_documents.return_value = {
            "data": SAMPLE_SEARCH_RESULTS,
            "pagination": {"limit": 25, "offset": 0},
        }
        mock_get_client.return_value = mock_client

        # Call the tool with title that doesn't exactly match
        result = await register_search_tools.tools[
            "get_document_id_from_title"
        ]("Test Doc")

        # Verify result contains expected information
        assert "Best match" in result
        assert "doc1" in result

    @pytest.mark.asyncio
    @patch("mcp_outline.features.documents.document_search.get_outline_client")
    async def test_get_document_id_from_title_no_results(
        self, mock_get_client, register_search_tools
    ):
        """Test get_document_id_from_title tool with no results."""
        # Set up mock client
        mock_client = AsyncMock()
        mock_client.search_documents.return_value = {
            "data": [],
            "pagination": {"limit": 25, "offset": 0},
        }
        mock_get_client.return_value = mock_client

        # Call the tool
        result = await register_search_tools.tools[
            "get_document_id_from_title"
        ]("Nonexistent")

        # Verify result contains expected information
        assert "No documents found" in result
        assert "Nonexistent" in result

    @pytest.mark.asyncio
    @patch("mcp_outline.features.documents.document_search.get_outline_client")
    async def test_search_documents_with_pagination_params(
        self, mock_get_client, register_search_tools
    ):
        """Test search_documents tool with custom pagination parameters."""
        # Set up mock client
        mock_client = AsyncMock()
        mock_client.search_documents.return_value = {
            "data": SAMPLE_SEARCH_RESULTS,
            "pagination": {"limit": 10, "offset": 20},
        }
        mock_get_client.return_value = mock_client

        # Call the tool with custom pagination
        result = await register_search_tools.tools["search_documents"](
            "test query", None, 10, 20
        )

        # Verify client was called with pagination params
        mock_client.search_documents.assert_called_once_with(
            "test query", None, 10, 20
        )

        # Verify pagination info in output
        assert "Showing results 21-22" in result

    @pytest.mark.asyncio
    @patch("mcp_outline.features.documents.document_search.get_outline_client")
    async def test_search_documents_full_page_shows_more_available(
        self, mock_get_client, register_search_tools
    ):
        """Test that full page of results shows 'more available' hint."""
        # Create a full page of results (limit == result count)
        full_page_results = [
            {
                "document": {"id": f"doc{i}", "title": f"Document {i}"},
                "context": f"Context {i}",
            }
            for i in range(1, 26)  # 25 results
        ]

        mock_client = AsyncMock()
        mock_client.search_documents.return_value = {
            "data": full_page_results,
            "pagination": {"limit": 25, "offset": 0},
        }
        mock_get_client.return_value = mock_client

        # Call the tool
        result = await register_search_tools.tools["search_documents"](
            "test query"
        )

        # Verify it suggests more results may be available
        assert "More results may be available" in result
        assert "offset=25" in result

    @pytest.mark.asyncio
    @patch("mcp_outline.features.documents.document_search.get_outline_client")
    async def test_search_documents_partial_page_no_hint(
        self, mock_get_client, register_search_tools
    ):
        """Test that partial page doesn't show 'more available' hint."""
        # Only 2 results when limit is 25
        mock_client = AsyncMock()
        mock_client.search_documents.return_value = {
            "data": SAMPLE_SEARCH_RESULTS,  # Only 2 results
            "pagination": {"limit": 25, "offset": 0},
        }
        mock_get_client.return_value = mock_client

        # Call the tool
        result = await register_search_tools.tools["search_documents"](
            "test query"
        )

        # Verify it doesn't suggest more results
        assert "More results may be available" not in result


class TestDocumentSearchPaginationFormatters:
    """Tests for pagination in search result formatters."""

    def test_format_search_results_with_pagination(self):
        """Test formatting search results with pagination metadata."""
        pagination = {"limit": 25, "offset": 0}
        result = _format_search_results(SAMPLE_SEARCH_RESULTS, pagination)

        assert "Showing results 1-2" in result
        assert "# Search Results" in result

    def test_format_search_results_with_offset_pagination(self):
        """Test formatting search results with non-zero offset."""
        pagination = {"limit": 10, "offset": 20}
        result = _format_search_results(SAMPLE_SEARCH_RESULTS, pagination)

        assert "Showing results 21-22" in result

    def test_format_search_results_no_pagination(self):
        """Test formatting search results without pagination metadata."""
        result = _format_search_results(SAMPLE_SEARCH_RESULTS, None)

        # Should not show pagination info
        assert "Showing results" not in result
        # But should still show results
        assert "Test Document 1" in result


class TestDocumentSearchEdgeCases:
    """Tests for edge cases and error handling in search functionality."""

    def test_format_search_results_with_empty_pagination_dict(self):
        """Test formatter handles empty pagination dict gracefully."""
        # Empty pagination dict (no limit or offset keys)
        # Empty dict is falsy in Python, so treated like None
        pagination = {}
        result = _format_search_results(SAMPLE_SEARCH_RESULTS, pagination)

        # Empty dict should be treated like None (no pagination info shown)
        assert "Showing results" not in result
        # But should still show results
        assert "Test Document 1" in result

    def test_format_search_results_with_partial_pagination_keys(self):
        """Test formatter handles missing pagination keys."""
        # Only limit, no offset
        pagination = {"limit": 10}
        result = _format_search_results(SAMPLE_SEARCH_RESULTS, pagination)

        # Should use default offset=0
        assert "Showing results 1-2" in result

        # Only offset, no limit
        pagination = {"offset": 20}
        result = _format_search_results(SAMPLE_SEARCH_RESULTS, pagination)

        # Should use default limit=25
        assert "Showing results 21-22" in result

    def test_format_search_results_empty_results_with_pagination(self):
        """Test formatter handles empty results with pagination metadata."""
        pagination = {"limit": 25, "offset": 100}
        result = _format_search_results([], pagination)

        # Should show "no results" message, not crash
        assert "No documents found" in result
        # Should not show pagination info for empty results
        assert "Showing results" not in result

    def test_format_search_results_single_result_with_pagination(self):
        """Test formatter handles single result correctly."""
        single_result = [
            {
                "document": {"id": "doc1", "title": "Single Document"},
                "context": "Only one result",
            }
        ]
        pagination = {"limit": 25, "offset": 0}
        result = _format_search_results(single_result, pagination)

        # Should show range 1-1
        assert "Showing results 1-1" in result
        assert "Single Document" in result
        # Should not suggest more results (1 != 25)
        assert "More results may be available" not in result

    def test_format_search_results_with_zero_ranking(self):
        """Test formatter handles zero relevance ranking."""
        results_with_zero_ranking = [
            {
                "document": {"id": "doc1", "title": "Zero Rank Doc"},
                "ranking": 0.0,
                "context": "Zero relevance",
            }
        ]
        result = _format_search_results(results_with_zero_ranking)

        # Should format 0.0 correctly
        assert "Relevance: 0.00" in result
        assert "Zero Rank Doc" in result

    def test_format_search_results_with_negative_ranking(self):
        """Test formatter handles negative relevance ranking."""
        results_with_negative_ranking = [
            {
                "document": {"id": "doc1", "title": "Negative Rank Doc"},
                "ranking": -1.5,
                "context": "Negative relevance",
            }
        ]
        result = _format_search_results(results_with_negative_ranking)

        # Should format negative value correctly
        assert "Relevance: -1.50" in result
        assert "Negative Rank Doc" in result

    def test_format_search_results_with_high_precision_ranking(self):
        """Test formatter rounds ranking to 2 decimal places."""
        results_with_precise_ranking = [
            {
                "document": {"id": "doc1", "title": "Precise Rank Doc"},
                "ranking": 1.23456789,
                "context": "High precision",
            }
        ]
        result = _format_search_results(results_with_precise_ranking)

        # Should round to 2 decimals
        assert "Relevance: 1.23" in result
        assert "1.23456789" not in result

    def test_format_search_results_missing_document_fields(self):
        """Test formatter handles missing document fields gracefully."""
        results_with_missing_fields = [
            {
                "document": {},  # Empty document
                "context": "Some context",
            }
        ]
        result = _format_search_results(results_with_missing_fields)

        # Should use default values
        assert "Untitled" in result
        assert "Some context" in result

    def test_format_search_results_missing_context_and_ranking(self):
        """Test formatter handles missing optional fields."""
        results_without_optional_fields = [
            {"document": {"id": "doc1", "title": "Basic Doc"}}
            # No context or ranking
        ]
        result = _format_search_results(results_without_optional_fields)

        # Should still display document
        assert "Basic Doc" in result
        assert "doc1" in result
        # Should not have Relevance or Context lines
        assert "Relevance:" not in result
        assert "Context:" not in result

    @pytest.mark.asyncio
    @patch("mcp_outline.features.documents.document_search.get_outline_client")
    async def test_search_documents_missing_pagination_in_response(
        self, mock_get_client, register_search_tools
    ):
        """Test tool handles API response without pagination key."""
        # API returns data but no pagination key
        mock_client = AsyncMock()
        mock_client.search_documents.return_value = {
            "data": SAMPLE_SEARCH_RESULTS
            # No "pagination" key
        }
        mock_get_client.return_value = mock_client

        # Should not crash
        result = await register_search_tools.tools["search_documents"](
            "test query"
        )

        # Should still show results
        assert "Test Document 1" in result
        # Should not show pagination info (since pagination key is missing)
        assert "Showing results" not in result

    @pytest.mark.asyncio
    @patch("mcp_outline.features.documents.document_search.get_outline_client")
    async def test_search_documents_empty_response_data(
        self, mock_get_client, register_search_tools
    ):
        """Test tool handles empty data array in response."""
        mock_client = AsyncMock()
        mock_client.search_documents.return_value = {
            "data": [],
            "pagination": {"limit": 25, "offset": 0},
        }
        mock_get_client.return_value = mock_client

        result = await register_search_tools.tools["search_documents"](
            "test query"
        )

        # Should show no results message
        assert "No documents found" in result

    @pytest.mark.asyncio
    @patch("mcp_outline.features.documents.document_search.get_outline_client")
    async def test_search_documents_malformed_response(
        self, mock_get_client, register_search_tools
    ):
        """Test tool handles completely malformed API response."""
        mock_client = AsyncMock()
        # Response missing "data" key entirely
        mock_client.search_documents.return_value = {}
        mock_get_client.return_value = mock_client

        result = await register_search_tools.tools["search_documents"](
            "test query"
        )

        # Should handle gracefully with empty results
        assert "No documents found" in result

    @pytest.mark.asyncio
    @patch("mcp_outline.features.documents.document_search.get_outline_client")
    async def test_search_documents_with_very_high_offset(
        self, mock_get_client, register_search_tools
    ):
        """Test tool handles offset beyond available results."""
        # High offset but no results (offset past end of data)
        mock_client = AsyncMock()
        mock_client.search_documents.return_value = {
            "data": [],
            "pagination": {"limit": 25, "offset": 1000},
        }
        mock_get_client.return_value = mock_client

        result = await register_search_tools.tools["search_documents"](
            "test query", None, 25, 1000
        )

        # Should handle gracefully
        assert "No documents found" in result

    @pytest.mark.asyncio
    @patch("mcp_outline.features.documents.document_search.get_outline_client")
    async def test_get_document_id_from_title_malformed_response(
        self, mock_get_client, register_search_tools
    ):
        """Test get_document_id_from_title handles malformed response."""
        mock_client = AsyncMock()
        # Response missing "data" key
        mock_client.search_documents.return_value = {}
        mock_get_client.return_value = mock_client

        result = await register_search_tools.tools[
            "get_document_id_from_title"
        ]("Some Title")

        # Should handle gracefully
        assert "No documents found" in result
        assert "Some Title" in result

    @pytest.mark.asyncio
    @patch("mcp_outline.features.documents.document_search.get_outline_client")
    async def test_get_document_id_from_title_missing_document_fields(
        self, mock_get_client, register_search_tools
    ):
        """Test get_document_id_from_title handles missing document fields."""
        mock_client = AsyncMock()
        # Result with empty document object
        mock_client.search_documents.return_value = {
            "data": [{"document": {}}],  # Empty document, no id or title
            "pagination": {"limit": 25, "offset": 0},
        }
        mock_get_client.return_value = mock_client

        result = await register_search_tools.tools[
            "get_document_id_from_title"
        ]("Some Title")

        # Should handle gracefully with defaults
        assert "Best match" in result
        assert "unknown" in result  # Default id
        assert "Untitled" in result  # Default title
