"""
Tests for AI-powered document tools.
"""

from unittest.mock import AsyncMock, patch

import pytest

from mcp_outline.features.documents.ai_tools import _format_ai_answer
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


# Sample AI response data
SAMPLE_AI_RESPONSE_WITH_ANSWER = {
    "search": {"answer": "The vacation policy allows 15 days per year."},
    "documents": [
        {"id": "doc1", "title": "Employee Handbook"},
        {"id": "doc2", "title": "HR Policies"},
    ],
}

SAMPLE_AI_RESPONSE_NO_ANSWER = {"search": {"answer": ""}, "documents": []}

SAMPLE_AI_RESPONSE_NO_SEARCH = {"documents": []}


@pytest.fixture
def mcp():
    """Fixture to provide mock MCP instance."""
    return MockMCP()


@pytest.fixture
def register_ai_tools(mcp):
    """Fixture to register AI tools."""
    from mcp_outline.features.documents.ai_tools import register_tools

    register_tools(mcp)
    return mcp


class TestAIAnswerFormatter:
    """Tests for _format_ai_answer formatter."""

    def test_format_ai_answer_with_sources(self):
        """Test formatting AI answer with source documents."""
        result = _format_ai_answer(SAMPLE_AI_RESPONSE_WITH_ANSWER)

        assert "# AI Answer" in result
        assert "vacation policy allows 15 days" in result
        assert "## Sources" in result
        assert "Employee Handbook" in result
        assert "doc1" in result
        assert "HR Policies" in result
        assert "doc2" in result

    def test_format_ai_answer_no_sources(self):
        """Test formatting AI answer without source documents."""
        response_no_sources = {
            "search": {"answer": "Test answer without sources."},
            "documents": [],
        }
        result = _format_ai_answer(response_no_sources)

        assert "# AI Answer" in result
        assert "Test answer without sources" in result
        assert "## Sources" not in result

    def test_format_ai_answer_no_answer(self):
        """Test formatting when no answer is found."""
        result = _format_ai_answer(SAMPLE_AI_RESPONSE_NO_ANSWER)

        assert "No answer was found" in result

    def test_format_ai_answer_no_search_field(self):
        """Test formatting when AI answering is not available."""
        result = _format_ai_answer(SAMPLE_AI_RESPONSE_NO_SEARCH)

        assert (
            "AI answering is not enabled" in result
            or "no relevant information" in result
        )

    def test_format_ai_answer_empty_response(self):
        """Test formatting empty response."""
        result = _format_ai_answer({})

        assert (
            "AI answering is not enabled" in result
            or "no relevant information" in result
        )


class TestAskAIAboutDocuments:
    """Tests for ask_ai_about_documents tool."""

    @pytest.mark.asyncio
    @patch("mcp_outline.features.documents.ai_tools.get_outline_client")
    async def test_ask_ai_about_documents_success(
        self, mock_get_client, register_ai_tools
    ):
        """Test ask_ai_about_documents tool success case."""
        mock_client = AsyncMock()
        mock_client.answer_question.return_value = (
            SAMPLE_AI_RESPONSE_WITH_ANSWER
        )
        mock_get_client.return_value = mock_client

        result = await register_ai_tools.tools["ask_ai_about_documents"](
            question="What is the vacation policy?"
        )

        mock_client.answer_question.assert_called_once_with(
            "What is the vacation policy?", None, None
        )
        assert "vacation policy allows 15 days" in result
        assert "Employee Handbook" in result

    @pytest.mark.asyncio
    @patch("mcp_outline.features.documents.ai_tools.get_outline_client")
    async def test_ask_ai_with_collection_id(
        self, mock_get_client, register_ai_tools
    ):
        """Test ask_ai_about_documents with collection_id specified."""
        mock_client = AsyncMock()
        mock_client.answer_question.return_value = (
            SAMPLE_AI_RESPONSE_WITH_ANSWER
        )
        mock_get_client.return_value = mock_client

        result = await register_ai_tools.tools["ask_ai_about_documents"](
            question="What is the vacation policy?", collection_id="col123"
        )

        mock_client.answer_question.assert_called_once_with(
            "What is the vacation policy?", "col123", None
        )
        assert "vacation policy" in result

    @pytest.mark.asyncio
    @patch("mcp_outline.features.documents.ai_tools.get_outline_client")
    async def test_ask_ai_with_document_id(
        self, mock_get_client, register_ai_tools
    ):
        """Test ask_ai_about_documents with document_id specified."""
        mock_client = AsyncMock()
        mock_client.answer_question.return_value = (
            SAMPLE_AI_RESPONSE_WITH_ANSWER
        )
        mock_get_client.return_value = mock_client

        result = await register_ai_tools.tools["ask_ai_about_documents"](
            question="What is the vacation policy?", document_id="doc123"
        )

        mock_client.answer_question.assert_called_once_with(
            "What is the vacation policy?", None, "doc123"
        )
        assert "vacation policy" in result

    @pytest.mark.asyncio
    @patch("mcp_outline.features.documents.ai_tools.get_outline_client")
    async def test_ask_ai_with_both_ids(
        self, mock_get_client, register_ai_tools
    ):
        """Test ask_ai_about_documents with both IDs specified."""
        mock_client = AsyncMock()
        mock_client.answer_question.return_value = (
            SAMPLE_AI_RESPONSE_WITH_ANSWER
        )
        mock_get_client.return_value = mock_client

        result = await register_ai_tools.tools["ask_ai_about_documents"](
            question="What is the vacation policy?",
            collection_id="col123",
            document_id="doc456",
        )

        mock_client.answer_question.assert_called_once_with(
            "What is the vacation policy?", "col123", "doc456"
        )
        assert "vacation policy" in result

    @pytest.mark.asyncio
    @patch("mcp_outline.features.documents.ai_tools.get_outline_client")
    async def test_ask_ai_no_answer_found(
        self, mock_get_client, register_ai_tools
    ):
        """Test ask_ai_about_documents when no answer is found."""
        mock_client = AsyncMock()
        mock_client.answer_question.return_value = SAMPLE_AI_RESPONSE_NO_ANSWER
        mock_get_client.return_value = mock_client

        result = await register_ai_tools.tools["ask_ai_about_documents"](
            question="What is the vacation policy?"
        )

        assert "No answer was found" in result

    @pytest.mark.asyncio
    @patch("mcp_outline.features.documents.ai_tools.get_outline_client")
    async def test_ask_ai_not_enabled(
        self, mock_get_client, register_ai_tools
    ):
        """Test ask_ai_about_documents when AI is not enabled."""
        mock_client = AsyncMock()
        mock_client.answer_question.return_value = SAMPLE_AI_RESPONSE_NO_SEARCH
        mock_get_client.return_value = mock_client

        result = await register_ai_tools.tools["ask_ai_about_documents"](
            question="What is the vacation policy?"
        )

        assert (
            "AI answering is not enabled" in result
            or "no relevant information" in result
        )

    @pytest.mark.asyncio
    @patch("mcp_outline.features.documents.ai_tools.get_outline_client")
    async def test_ask_ai_client_error(
        self, mock_get_client, register_ai_tools
    ):
        """Test ask_ai_about_documents with client error."""
        mock_client = AsyncMock()
        mock_client.answer_question.side_effect = OutlineClientError(
            "API error"
        )
        mock_get_client.return_value = mock_client

        result = await register_ai_tools.tools["ask_ai_about_documents"](
            question="What is the vacation policy?"
        )

        assert "Error getting answer" in result
        assert "API error" in result

    @pytest.mark.asyncio
    @patch("mcp_outline.features.documents.ai_tools.get_outline_client")
    async def test_ask_ai_unexpected_error(
        self, mock_get_client, register_ai_tools
    ):
        """Test ask_ai_about_documents with unexpected error."""
        mock_client = AsyncMock()
        mock_client.answer_question.side_effect = ValueError(
            "Unexpected error"
        )
        mock_get_client.return_value = mock_client

        result = await register_ai_tools.tools["ask_ai_about_documents"](
            question="What is the vacation policy?"
        )

        assert "Unexpected error" in result
