"""
Tests for document search tools.
"""
from unittest.mock import MagicMock, patch

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
        "document": {
            "id": "doc1",
            "title": "Test Document 1"
        },
        "context": "This is a test document."
    },
    {
        "document": {
            "id": "doc2",
            "title": "Test Document 2"
        },
        "context": "Another test document."
    }
]

SAMPLE_DOCUMENTS = [
    {
        "id": "doc1",
        "title": "Test Document 1",
        "updatedAt": "2023-01-01T12:00:00Z"
    },
    {
        "id": "doc2",
        "title": "Test Document 2",
        "updatedAt": "2023-01-02T12:00:00Z"
    }
]

SAMPLE_COLLECTIONS = [
    {
        "id": "coll1",
        "name": "Test Collection 1",
        "description": "Collection description"
    },
    {
        "id": "coll2",
        "name": "Test Collection 2",
        "description": ""
    }
]

SAMPLE_COLLECTION_DOCUMENTS = [
    {
        "id": "doc1",
        "title": "Root Document",
        "children": [
            {
                "id": "doc2",
                "title": "Child Document",
                "children": []
            }
        ]
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
    
    @patch("mcp_outline.features.documents.document_search.get_outline_client")
    def test_search_documents_success(
        self, mock_get_client, register_search_tools
    ):
        """Test search_documents tool success case."""
        # Set up mock client
        mock_client = MagicMock()
        mock_client.search_documents.return_value = SAMPLE_SEARCH_RESULTS
        mock_get_client.return_value = mock_client
        
        # Call the tool
        result = register_search_tools.tools["search_documents"]("test query")
        
        # Verify client was called correctly
        mock_client.search_documents.assert_called_once_with(
            "test query", 
            None
        )
        
        # Verify result contains expected information
        assert "Test Document 1" in result
        assert "doc1" in result
    
    @patch("mcp_outline.features.documents.document_search.get_outline_client")
    def test_search_documents_with_collection(
        self, mock_get_client, register_search_tools
    ):
        """Test search_documents tool with collection filter."""
        # Set up mock client
        mock_client = MagicMock()
        mock_client.search_documents.return_value = SAMPLE_SEARCH_RESULTS
        mock_get_client.return_value = mock_client
        
        # Call the tool
        _ = register_search_tools.tools["search_documents"](
            "test query", 
            "coll1"
        )
        
        # Verify client was called correctly
        mock_client.search_documents.assert_called_once_with(
            "test query", "coll1")
    
    @patch("mcp_outline.features.documents.document_search.get_outline_client")
    def test_search_documents_client_error(
        self, mock_get_client, register_search_tools
    ):
        """Test search_documents tool with client error."""
        # Set up mock client to raise an error
        mock_client = MagicMock()
        mock_client.search_documents.side_effect = OutlineClientError(
            "API error")
        mock_get_client.return_value = mock_client
        
        # Call the tool
        result = register_search_tools.tools["search_documents"]("test query")
        
        # Verify error is handled and returned
        assert "Error searching documents" in result
        assert "API error" in result
    
    @patch("mcp_outline.features.documents.document_search.get_outline_client")
    def test_list_collections_success(
        self, mock_get_client, register_search_tools
    ):
        """Test list_collections tool success case."""
        # Set up mock client
        mock_client = MagicMock()
        mock_client.list_collections.return_value = SAMPLE_COLLECTIONS
        mock_get_client.return_value = mock_client
        
        # Call the tool
        result = register_search_tools.tools["list_collections"]()
        
        # Verify client was called correctly
        mock_client.list_collections.assert_called_once()
        
        # Verify result contains expected information
        assert "Test Collection 1" in result
        assert "coll1" in result
    
    @patch("mcp_outline.features.documents.document_search.get_outline_client")
    def test_get_collection_structure_success(
        self, mock_get_client, register_search_tools
    ):
        """Test get_collection_structure tool success case."""
        # Set up mock client
        mock_client = MagicMock()
        mock_client.get_collection_documents.return_value = (
            SAMPLE_COLLECTION_DOCUMENTS)
        mock_get_client.return_value = mock_client
        
        # Call the tool
        result = register_search_tools.tools[
            "get_collection_structure"]("coll1")
        
        # Verify client was called correctly
        mock_client.get_collection_documents.assert_called_once_with("coll1")
        
        # Verify result contains expected information
        assert "Root Document" in result
        assert "Child Document" in result
    
    @patch("mcp_outline.features.documents.document_search.get_outline_client")
    def test_get_document_id_from_title_exact_match(
        self, mock_get_client, register_search_tools
    ):
        """Test get_document_id_from_title tool with exact match."""
        # Search results with exact title match
        exact_match_results = [
            {
                "document": {
                    "id": "doc1",
                    "title": "Exact Match"
                }
            }
        ]
        
        # Set up mock client
        mock_client = MagicMock()
        mock_client.search_documents.return_value = exact_match_results
        mock_get_client.return_value = mock_client
        
        # Call the tool
        result = register_search_tools.tools["get_document_id_from_title"](
            "Exact Match"
        )
        
        # Verify client was called correctly
        mock_client.search_documents.assert_called_once_with(
            "Exact Match", None)
        
        # Verify result contains expected information
        assert "Document ID: doc1" in result
        assert "Exact Match" in result
    
    @patch("mcp_outline.features.documents.document_search.get_outline_client")
    def test_get_document_id_from_title_best_match(
        self, mock_get_client, register_search_tools
    ):
        """Test get_document_id_from_title tool with best match (non-exact)."""
        # Set up mock client
        mock_client = MagicMock()
        mock_client.search_documents.return_value = SAMPLE_SEARCH_RESULTS
        mock_get_client.return_value = mock_client
        
        # Call the tool with title that doesn't exactly match
        result = register_search_tools.tools[
            "get_document_id_from_title"]("Test Doc")
        
        # Verify result contains expected information
        assert "Best match" in result
        assert "doc1" in result
    
    @patch("mcp_outline.features.documents.document_search.get_outline_client")
    def test_get_document_id_from_title_no_results(
        self, mock_get_client, register_search_tools
    ):
        """Test get_document_id_from_title tool with no results."""
        # Set up mock client
        mock_client = MagicMock()
        mock_client.search_documents.return_value = []
        mock_get_client.return_value = mock_client
        
        # Call the tool
        result = register_search_tools.tools[
            "get_document_id_from_title"]("Nonexistent")
        
        # Verify result contains expected information
        assert "No documents found" in result
        assert "Nonexistent" in result
