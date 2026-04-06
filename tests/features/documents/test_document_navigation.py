"""
Tests for document navigation tools (TOC and section reading).
"""

from unittest.mock import AsyncMock, patch

import pytest

from mcp_outline.utils.document_cache import (
    reset_document_cache,
)


class MockMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, **kwargs):
        def decorator(func):
            self.tools[func.__name__] = func
            return func

        return decorator


SAMPLE_HEADED_DOCUMENT = {
    "id": "doc789",
    "title": "Headed Doc",
    "text": (
        "# Introduction\n"
        "Intro text.\n"
        "\n"
        "## Background\n"
        "Background text.\n"
        "\n"
        "## Goals\n"
        "Goals text.\n"
        "\n"
        "# Architecture\n"
        "Arch intro.\n"
        "\n"
        "## Components\n"
        "Components text.\n"
        "\n"
        "### Frontend\n"
        "Frontend details."
    ),
    "url": "/doc/headed",
}

SAMPLE_NO_HEADINGS = {
    "id": "doc-plain",
    "title": "Plain Doc",
    "text": "Just some plain text with no headings.",
    "url": "",
}


@pytest.fixture
def mcp():
    return MockMCP()


@pytest.fixture
def register_nav_tools(mcp):
    from mcp_outline.features.documents.document_navigation import (
        register_tools,
    )

    register_tools(mcp)
    return mcp


@pytest.fixture(autouse=True)
def _clean_cache():
    reset_document_cache()
    yield
    reset_document_cache()


_PATCH_CLIENT = (
    "mcp_outline.features.documents.document_reading.get_outline_client"
)
_PATCH_API_KEY = (
    "mcp_outline.features.documents.document_reading.get_resolved_api_key"
)


def _mock_api(mock_get_client, mock_api_key, document):
    mock_api_key.return_value = "test-key"
    mock_client = AsyncMock()
    mock_client.get_document.return_value = document
    mock_get_client.return_value = mock_client
    return mock_client


class TestGetDocumentToc:
    """Tests for get_document_toc tool."""

    @pytest.mark.asyncio
    @patch(_PATCH_API_KEY)
    @patch(_PATCH_CLIENT)
    async def test_toc_with_headings(
        self,
        mock_get_client,
        mock_api_key,
        register_nav_tools,
    ):
        _mock_api(
            mock_get_client,
            mock_api_key,
            SAMPLE_HEADED_DOCUMENT,
        )
        result = await register_nav_tools.tools["get_document_toc"]("doc789")
        assert "Table of Contents" in result
        assert "# Introduction" in result
        assert "## Background" in result
        assert "## Goals" in result
        assert "# Architecture" in result
        assert "## Components" in result
        assert "### Frontend" in result

    @pytest.mark.asyncio
    @patch(_PATCH_API_KEY)
    @patch(_PATCH_CLIENT)
    async def test_toc_no_headings(
        self,
        mock_get_client,
        mock_api_key,
        register_nav_tools,
    ):
        _mock_api(
            mock_get_client,
            mock_api_key,
            SAMPLE_NO_HEADINGS,
        )
        result = await register_nav_tools.tools["get_document_toc"](
            "doc-plain"
        )
        assert "No headings found" in result


class TestReadDocumentSection:
    """Tests for read_document_section tool."""

    @pytest.mark.asyncio
    @patch(_PATCH_API_KEY)
    @patch(_PATCH_CLIENT)
    async def test_section_match(
        self,
        mock_get_client,
        mock_api_key,
        register_nav_tools,
    ):
        _mock_api(
            mock_get_client,
            mock_api_key,
            SAMPLE_HEADED_DOCUMENT,
        )
        result = await register_nav_tools.tools["read_document_section"](
            "doc789", heading="Background"
        )
        assert "Section: ## Background" in result
        assert "Background text." in result
        assert "Goals text." not in result

    @pytest.mark.asyncio
    @patch(_PATCH_API_KEY)
    @patch(_PATCH_CLIENT)
    async def test_section_case_insensitive(
        self,
        mock_get_client,
        mock_api_key,
        register_nav_tools,
    ):
        _mock_api(
            mock_get_client,
            mock_api_key,
            SAMPLE_HEADED_DOCUMENT,
        )
        result = await register_nav_tools.tools["read_document_section"](
            "doc789", heading="background"
        )
        assert "Section: ## Background" in result

    @pytest.mark.asyncio
    @patch(_PATCH_API_KEY)
    @patch(_PATCH_CLIENT)
    async def test_section_substring_match(
        self,
        mock_get_client,
        mock_api_key,
        register_nav_tools,
    ):
        _mock_api(
            mock_get_client,
            mock_api_key,
            SAMPLE_HEADED_DOCUMENT,
        )
        result = await register_nav_tools.tools["read_document_section"](
            "doc789", heading="back"
        )
        assert "Section: ## Background" in result

    @pytest.mark.asyncio
    @patch(_PATCH_API_KEY)
    @patch(_PATCH_CLIENT)
    async def test_section_includes_nested(
        self,
        mock_get_client,
        mock_api_key,
        register_nav_tools,
    ):
        _mock_api(
            mock_get_client,
            mock_api_key,
            SAMPLE_HEADED_DOCUMENT,
        )
        result = await register_nav_tools.tools["read_document_section"](
            "doc789", heading="Architecture"
        )
        assert "Arch intro." in result
        assert "Components text." in result
        assert "Frontend details." in result

    @pytest.mark.asyncio
    @patch(_PATCH_API_KEY)
    @patch(_PATCH_CLIENT)
    async def test_section_no_match(
        self,
        mock_get_client,
        mock_api_key,
        register_nav_tools,
    ):
        _mock_api(
            mock_get_client,
            mock_api_key,
            SAMPLE_HEADED_DOCUMENT,
        )
        result = await register_nav_tools.tools["read_document_section"](
            "doc789", heading="nonexistent"
        )
        assert "No heading matching" in result
        assert "Available headings:" in result

    @pytest.mark.asyncio
    @patch(_PATCH_API_KEY)
    @patch(_PATCH_CLIENT)
    async def test_section_ambiguous_match(
        self,
        mock_get_client,
        mock_api_key,
        register_nav_tools,
    ):
        _mock_api(
            mock_get_client,
            mock_api_key,
            SAMPLE_HEADED_DOCUMENT,
        )
        result = await register_nav_tools.tools["read_document_section"](
            "doc789", heading="o"
        )
        assert "Multiple headings match" in result

    @pytest.mark.asyncio
    @patch(_PATCH_API_KEY)
    @patch(_PATCH_CLIENT)
    async def test_section_no_headings_in_doc(
        self,
        mock_get_client,
        mock_api_key,
        register_nav_tools,
    ):
        _mock_api(
            mock_get_client,
            mock_api_key,
            SAMPLE_NO_HEADINGS,
        )
        result = await register_nav_tools.tools["read_document_section"](
            "doc-plain", heading="anything"
        )
        assert "No headings found" in result
