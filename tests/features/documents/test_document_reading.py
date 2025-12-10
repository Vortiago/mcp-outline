"""
Tests for document reading tools.
"""

from unittest.mock import AsyncMock, patch

import pytest
from mcp.types import CallToolResult

from mcp_outline.features.documents.common import OutlineClientError
from mcp_outline.features.documents.document_reading import (
    _extract_section,
    _format_document_content,
    _format_outline,
    _parse_headings_safely,
)


def extract_text(result) -> str:
    """Extract text content from a tool result (string or CallToolResult)."""
    if isinstance(result, CallToolResult):
        return result.content[0].text
    return result


# Mock FastMCP for registering tools
class MockMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, **kwargs):
        def decorator(func):
            self.tools[func.__name__] = func
            return func

        return decorator


# Sample document data
SAMPLE_DOCUMENT = {
    "id": "doc123",
    "title": "Test Document",
    "text": "This is a test document with some content.",
    "updatedAt": "2023-01-01T12:00:00Z",
}

# Sample document with headings for outline tests (must be > 1000 chars)
# Adding enough content to exceed the 1000 char threshold for TOC mode
SAMPLE_DOCUMENT_WITH_HEADINGS = {
    "id": "doc456",
    "title": "Documentation Guide",
    "text": """# Introduction

This is the introduction section with enough content to make the document
larger than 1000 characters. We need to ensure that the document is long
enough to trigger the table of contents mode instead of returning full content.

## Getting Started

Here is how to get started with this comprehensive guide. This section
contains detailed instructions for new users who want to understand the
basics of working with our system.

### Installation

Run pip install to install the package and all its dependencies. Make sure
you have Python 3.8 or later installed on your system before proceeding.

### Configuration

Set up your config file by creating a new .env file in your project root.
You'll need to add your API keys and other settings here. See the examples
directory for sample configurations.

## Advanced Usage

This section covers advanced topics for experienced users who want to take
full advantage of all features. We'll cover batch operations, custom hooks,
and performance optimization techniques.

## Conclusion

That's all folks! Thank you for reading this comprehensive guide.
""",
}

# Sample small document (under 1000 chars)
SAMPLE_SMALL_DOCUMENT = {
    "id": "doc789",
    "title": "Quick Note",
    "text": "This is a short note.",
}

# Sample document with code blocks
SAMPLE_DOCUMENT_WITH_CODE = {
    "id": "doc101",
    "title": "Code Examples",
    "text": """# Code Examples

Here is some code:

```python
# This is not a heading
def hello():
    print("Hello")
```

## Real Heading

This is a real section.
""",
}

# Sample export response
SAMPLE_EXPORT_RESPONSE = {
    "data": "# Test Document\n\nThis is a test document with some content."
}


@pytest.fixture
def mcp():
    """Fixture to provide mock MCP instance."""
    return MockMCP()


@pytest.fixture
def register_reading_tools(mcp):
    """Fixture to register document reading tools."""
    from mcp_outline.features.documents.document_reading import register_tools

    register_tools(mcp)
    return mcp


class TestDocumentReadingFormatters:
    """Tests for document reading formatting functions."""

    def test_format_document_content(self):
        """Test formatting document content."""
        result = _format_document_content(SAMPLE_DOCUMENT)

        # Verify the result contains the expected information
        assert "# Test Document" in result
        assert "This is a test document with some content." in result

    def test_format_document_content_missing_fields(self):
        """Test formatting document content with missing fields."""
        # Test with missing title
        doc_no_title = {"text": "Content only"}
        result_no_title = _format_document_content(doc_no_title)
        assert "# Untitled Document" in result_no_title
        assert "Content only" in result_no_title

        # Test with missing text
        doc_no_text = {"title": "Title only"}
        result_no_text = _format_document_content(doc_no_text)
        assert "# Title only" in result_no_text
        assert result_no_text.strip().endswith("# Title only")

        # Test with empty document
        empty_doc = {}
        result_empty = _format_document_content(empty_doc)
        assert "# Untitled Document" in result_empty


class TestDocumentReadingTools:
    """Tests for document reading tools."""

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_reading.get_outline_client"
    )
    async def test_read_document_success(
        self, mock_get_client, register_reading_tools
    ):
        """Test read_document tool success case."""
        # Set up mock client
        mock_client = AsyncMock()
        mock_client.get_document.return_value = SAMPLE_DOCUMENT
        mock_get_client.return_value = mock_client

        # Call the tool
        result = await register_reading_tools.tools["read_document"]("doc123")

        # Verify client was called correctly
        mock_client.get_document.assert_called_once_with("doc123")

        # Verify result contains expected information
        assert "# Test Document" in extract_text(result)
        assert "This is a test document with some content." in extract_text(
            result
        )

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_reading.get_outline_client"
    )
    async def test_read_document_client_error(
        self, mock_get_client, register_reading_tools
    ):
        """Test read_document tool with client error."""
        # Set up mock client to raise an error
        mock_client = AsyncMock()
        mock_client.get_document.side_effect = OutlineClientError("API error")
        mock_get_client.return_value = mock_client

        # Call the tool
        result = await register_reading_tools.tools["read_document"]("doc123")

        # Verify error is handled and returned
        assert "Error reading document" in extract_text(result)
        assert "API error" in extract_text(result)

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_reading.get_outline_client"
    )
    async def test_export_document_success(
        self, mock_get_client, register_reading_tools
    ):
        """Test export_document tool success case."""
        # Set up mock client
        mock_client = AsyncMock()
        mock_client.post.return_value = SAMPLE_EXPORT_RESPONSE
        mock_get_client.return_value = mock_client

        # Call the tool
        result = await register_reading_tools.tools["export_document"](
            "doc123"
        )

        # Verify client was called correctly
        mock_client.post.assert_called_once_with(
            "documents.export", {"id": "doc123"}
        )

        # Verify result contains expected information
        assert "# Test Document" in extract_text(result)
        assert "This is a test document with some content." in extract_text(
            result
        )

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_reading.get_outline_client"
    )
    async def test_export_document_empty_response(
        self, mock_get_client, register_reading_tools
    ):
        """Test export_document tool with empty response."""
        # Set up mock client with empty response
        mock_client = AsyncMock()
        mock_client.post.return_value = {}
        mock_get_client.return_value = mock_client

        # Call the tool
        result = await register_reading_tools.tools["export_document"](
            "doc123"
        )

        # Verify result contains default message
        assert "No content available" in extract_text(result)

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_reading.get_outline_client"
    )
    async def test_export_document_client_error(
        self, mock_get_client, register_reading_tools
    ):
        """Test export_document tool with client error."""
        # Set up mock client to raise an error
        mock_client = AsyncMock()
        mock_client.post.side_effect = OutlineClientError("API error")
        mock_get_client.return_value = mock_client

        # Call the tool
        result = await register_reading_tools.tools["export_document"](
            "doc123"
        )

        # Verify error is handled and returned
        assert "Error exporting document" in extract_text(result)
        assert "API error" in extract_text(result)


class TestHeadingParsing:
    """Tests for heading parsing helper functions."""

    def test_parse_headings_basic(self):
        """Test parsing basic markdown headings."""
        markdown = """# Heading 1
Some text.
## Heading 2
More text.
### Heading 3
Even more text."""
        headings = _parse_headings_safely(markdown)

        assert len(headings) == 3
        assert headings[0] == {"level": 1, "text": "Heading 1", "line": 1}
        assert headings[1] == {"level": 2, "text": "Heading 2", "line": 3}
        assert headings[2] == {"level": 3, "text": "Heading 3", "line": 5}

    def test_parse_headings_skips_code_blocks(self):
        """Test that headings inside code blocks are ignored."""
        markdown = """# Real Heading

```python
# This is a comment, not a heading
def func():
    pass
```

## Another Real Heading"""
        headings = _parse_headings_safely(markdown)

        assert len(headings) == 2
        assert headings[0]["text"] == "Real Heading"
        assert headings[1]["text"] == "Another Real Heading"

    def test_parse_headings_limits_depth(self):
        """Test that only H1-H4 are captured."""
        markdown = """# H1
## H2
### H3
#### H4
##### H5
###### H6"""
        headings = _parse_headings_safely(markdown)

        # Should only capture H1-H4
        assert len(headings) == 4
        assert headings[0]["level"] == 1
        assert headings[1]["level"] == 2
        assert headings[2]["level"] == 3
        assert headings[3]["level"] == 4

    def test_parse_headings_empty_document(self):
        """Test parsing empty document."""
        headings = _parse_headings_safely("")
        assert headings == []

    def test_parse_headings_no_headings(self):
        """Test parsing document with no headings."""
        markdown = "Just some text without any headings."
        headings = _parse_headings_safely(markdown)
        assert headings == []


class TestSectionExtraction:
    """Tests for section extraction helper functions."""

    def test_extract_section_basic(self):
        """Test basic section extraction."""
        markdown = """# Introduction
This is intro content.

## Getting Started
This is the getting started content.

## Next Steps
More content here."""
        section = _extract_section(markdown, "Getting Started")

        assert section is not None
        assert "This is the getting started content." in section
        assert "More content here" not in section

    def test_extract_section_last_section(self):
        """Test extracting the last section (no terminating heading)."""
        markdown = """# Introduction
Intro text.

## Final Section
This is the final section content.
It has multiple lines.
And no heading after it."""
        section = _extract_section(markdown, "Final Section")

        assert section is not None
        assert "This is the final section content." in section
        assert "multiple lines" in section
        assert "no heading after it" in section

    def test_extract_section_case_insensitive(self):
        """Test that section extraction is case-insensitive."""
        markdown = """# Introduction
Intro content.

## GETTING STARTED
Started content."""
        section = _extract_section(markdown, "getting started")

        assert section is not None
        assert "Started content" in section

    def test_extract_section_not_found(self):
        """Test extraction when heading not found."""
        markdown = """# Introduction
Some content."""
        section = _extract_section(markdown, "NonExistent")

        assert section is None

    def test_extract_section_with_subheadings(self):
        """Test that subheadings are included in extracted section."""
        markdown = """# Intro

## Main Section

Content here.

### Subsection

Sub content.

## Next Section

Other content."""
        section = _extract_section(markdown, "Main Section")

        assert section is not None
        assert "Content here." in section
        assert "### Subsection" in section
        assert "Sub content." in section
        assert "Other content" not in section

    def test_extract_section_empty_content(self):
        """Test extraction of section with no content."""
        markdown = """# First

## Empty Section

## Next Section

Content."""
        section = _extract_section(markdown, "Empty Section")

        assert section == "Section has no content."

    def test_extract_section_preserves_code_blocks(self):
        """Test that code blocks are preserved in extracted section."""
        markdown = """# Code Section

Here is code:

```python
# Comment
def hello():
    pass
```

# Next Section"""
        section = _extract_section(markdown, "Code Section")

        assert section is not None
        assert "```python" in section
        assert "# Comment" in section


class TestFormatOutline:
    """Tests for outline formatting."""

    def test_format_outline_basic(self):
        """Test basic outline formatting."""
        headings = [
            {"level": 1, "text": "Introduction", "line": 1},
            {"level": 2, "text": "Getting Started", "line": 5},
            {"level": 2, "text": "Conclusion", "line": 10},
        ]
        result = _format_outline("My Doc", headings, 500)

        assert "# My Doc" in result
        assert "Word count: ~500" in result
        assert "Table of Contents" in result
        assert "- Introduction" in result
        assert "  - Getting Started" in result
        assert "  - Conclusion" in result

    def test_format_outline_empty(self):
        """Test outline formatting with no headings."""
        result = _format_outline("Empty Doc", [], 100)

        assert "# Empty Doc" in result
        assert "No headings found" in result


class TestDocumentOutlineTool:
    """Tests for get_document_outline tool."""

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_reading.get_outline_client"
    )
    async def test_get_document_outline_large_doc(
        self, mock_get_client, register_reading_tools
    ):
        """Test get_document_outline returns TOC for large documents."""
        import mcp_outline.utils.response_handler as rh

        orig_structured = rh.STRUCTURED_OUTPUT_ENABLED
        try:
            rh.STRUCTURED_OUTPUT_ENABLED = True

            mock_client = AsyncMock()
            mock_client.get_document.return_value = (
                SAMPLE_DOCUMENT_WITH_HEADINGS
            )
            mock_get_client.return_value = mock_client

            result = await register_reading_tools.tools[
                "get_document_outline"
            ]("doc456")

            # Should return CallToolResult
            assert isinstance(result, CallToolResult)

            text = extract_text(result)
            assert "Documentation Guide" in text
            assert "Table of Contents" in text
            assert "Introduction" in text
            assert "Getting Started" in text
            assert "Installation" in text
            assert "Advanced Usage" in text

            # Should have structured content
            assert result.structuredContent is not None
            assert result.structuredContent["title"] == "Documentation Guide"
            assert len(result.structuredContent["headings"]) > 0
        finally:
            rh.STRUCTURED_OUTPUT_ENABLED = orig_structured

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_reading.get_outline_client"
    )
    async def test_get_document_outline_small_doc_returns_full_content(
        self, mock_get_client, register_reading_tools
    ):
        """Test that small documents return full content instead of TOC."""
        import mcp_outline.utils.response_handler as rh

        orig_structured = rh.STRUCTURED_OUTPUT_ENABLED
        try:
            rh.STRUCTURED_OUTPUT_ENABLED = True

            mock_client = AsyncMock()
            mock_client.get_document.return_value = SAMPLE_SMALL_DOCUMENT
            mock_get_client.return_value = mock_client

            result = await register_reading_tools.tools[
                "get_document_outline"
            ]("doc789")

            text = extract_text(result)
            # Should return full content for small docs
            assert "Quick Note" in text
            assert "This is a short note." in text
            # Should NOT have table of contents
            assert "Table of Contents" not in text

            # Structured content should indicate full content
            assert result.structuredContent is not None
            assert result.structuredContent.get("full_content") is True
        finally:
            rh.STRUCTURED_OUTPUT_ENABLED = orig_structured

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_reading.get_outline_client"
    )
    async def test_get_document_outline_skips_code_block_headings(
        self, mock_get_client, register_reading_tools
    ):
        """Test that headings inside code blocks are not included in TOC."""
        # Create a large enough document with code blocks
        # Use proper text padding to ensure headings start at line beginnings
        padding = "This is padding text. " * 60  # ~1200 chars
        large_doc_with_code = {
            "id": "doc102",
            "title": "Code Doc",
            "text": f"""# Preamble

{padding}

{SAMPLE_DOCUMENT_WITH_CODE["text"]}""",
        }
        mock_client = AsyncMock()
        mock_client.get_document.return_value = large_doc_with_code
        mock_get_client.return_value = mock_client

        result = await register_reading_tools.tools["get_document_outline"](
            "doc102"
        )

        text = extract_text(result)
        # Should NOT include the comment inside code block as a heading
        assert "This is not a heading" not in text
        # Should include real headings
        assert "Preamble" in text
        assert "Code Examples" in text
        assert "Real Heading" in text

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_reading.get_outline_client"
    )
    async def test_get_document_outline_error(
        self, mock_get_client, register_reading_tools
    ):
        """Test get_document_outline handles errors gracefully."""
        mock_client = AsyncMock()
        mock_client.get_document.side_effect = OutlineClientError("Not found")
        mock_get_client.return_value = mock_client

        result = await register_reading_tools.tools["get_document_outline"](
            "invalid"
        )

        text = extract_text(result)
        assert "Error" in text
        assert "Not found" in text

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_reading.get_outline_client"
    )
    async def test_get_document_outline_generic_exception(
        self, mock_get_client, register_reading_tools
    ):
        """Test get_document_outline handles generic exceptions."""
        mock_client = AsyncMock()
        mock_client.get_document.side_effect = RuntimeError("Unexpected error")
        mock_get_client.return_value = mock_client

        result = await register_reading_tools.tools["get_document_outline"](
            "doc123"
        )

        text = extract_text(result)
        assert "Unexpected error" in text

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_reading.get_outline_client"
    )
    async def test_get_document_outline_boundary_1000_chars(
        self, mock_get_client, register_reading_tools
    ):
        """Test behavior at exactly 1000 character boundary."""
        import mcp_outline.utils.response_handler as rh

        orig_structured = rh.STRUCTURED_OUTPUT_ENABLED
        try:
            rh.STRUCTURED_OUTPUT_ENABLED = True

            # Exactly 1000 chars should return full content
            doc_at_boundary = {
                "id": "boundary",
                "title": "Boundary Test",
                "text": "x" * 1000,
            }
            mock_client = AsyncMock()
            mock_client.get_document.return_value = doc_at_boundary
            mock_get_client.return_value = mock_client

            result = await register_reading_tools.tools[
                "get_document_outline"
            ]("boundary")

            # At exactly 1000, should return full content (< 1000 is the check)
            assert result.structuredContent.get("full_content") is not True
        finally:
            rh.STRUCTURED_OUTPUT_ENABLED = orig_structured

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_reading.get_outline_client"
    )
    async def test_get_document_outline_large_doc_no_headings(
        self, mock_get_client, register_reading_tools
    ):
        """Test outline of large document with no headings."""
        doc_no_headings = {
            "id": "noheadings",
            "title": "No Headings Doc",
            "text": "Just plain text. " * 100,  # ~1700 chars, no headings
        }
        mock_client = AsyncMock()
        mock_client.get_document.return_value = doc_no_headings
        mock_get_client.return_value = mock_client

        result = await register_reading_tools.tools["get_document_outline"](
            "noheadings"
        )

        text = extract_text(result)
        assert "No Headings Doc" in text
        assert "No headings found" in text

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_reading.get_outline_client"
    )
    async def test_get_document_outline_empty_text(
        self, mock_get_client, register_reading_tools
    ):
        """Test outline with empty text field."""
        import mcp_outline.utils.response_handler as rh

        orig_structured = rh.STRUCTURED_OUTPUT_ENABLED
        try:
            rh.STRUCTURED_OUTPUT_ENABLED = True

            doc_empty_text = {
                "id": "empty",
                "title": "Empty Doc",
                "text": "",
            }
            mock_client = AsyncMock()
            mock_client.get_document.return_value = doc_empty_text
            mock_get_client.return_value = mock_client

            result = await register_reading_tools.tools[
                "get_document_outline"
            ]("empty")

            # Empty doc is small, should return full content
            text = extract_text(result)
            assert "Empty Doc" in text
            assert result.structuredContent.get("full_content") is True
        finally:
            rh.STRUCTURED_OUTPUT_ENABLED = orig_structured


class TestReadDocumentSectionTool:
    """Tests for read_document_section tool."""

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_reading.get_outline_client"
    )
    async def test_read_document_section_success(
        self, mock_get_client, register_reading_tools
    ):
        """Test read_document_section extracts correct section."""
        import mcp_outline.utils.response_handler as rh

        orig_structured = rh.STRUCTURED_OUTPUT_ENABLED
        try:
            rh.STRUCTURED_OUTPUT_ENABLED = True

            mock_client = AsyncMock()
            mock_client.get_document.return_value = (
                SAMPLE_DOCUMENT_WITH_HEADINGS
            )
            mock_get_client.return_value = mock_client

            result = await register_reading_tools.tools[
                "read_document_section"
            ]("doc456", "Getting Started")

            assert isinstance(result, CallToolResult)

            text = extract_text(result)
            assert "Getting Started" in text
            assert "Here is how to get started" in text

            # Structured content should have the section
            assert result.structuredContent is not None
            assert result.structuredContent["heading"] == "Getting Started"
        finally:
            rh.STRUCTURED_OUTPUT_ENABLED = orig_structured

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_reading.get_outline_client"
    )
    async def test_read_document_section_case_insensitive(
        self, mock_get_client, register_reading_tools
    ):
        """Test read_document_section is case-insensitive."""
        mock_client = AsyncMock()
        mock_client.get_document.return_value = SAMPLE_DOCUMENT_WITH_HEADINGS
        mock_get_client.return_value = mock_client

        result = await register_reading_tools.tools["read_document_section"](
            "doc456", "getting started"
        )

        text = extract_text(result)
        assert "Here is how to get started" in text

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_reading.get_outline_client"
    )
    async def test_read_document_section_not_found(
        self, mock_get_client, register_reading_tools
    ):
        """Test read_document_section when heading not found."""
        import mcp_outline.utils.response_handler as rh

        orig_structured = rh.STRUCTURED_OUTPUT_ENABLED
        try:
            rh.STRUCTURED_OUTPUT_ENABLED = True

            mock_client = AsyncMock()
            mock_client.get_document.return_value = (
                SAMPLE_DOCUMENT_WITH_HEADINGS
            )
            mock_get_client.return_value = mock_client

            result = await register_reading_tools.tools[
                "read_document_section"
            ]("doc456", "NonExistent Section")

            text = extract_text(result)
            assert "not found" in text
            # Should list available headings
            assert "Available headings" in text
            assert "Introduction" in text
            assert "Getting Started" in text

            # Structured content should have available headings
            assert result.structuredContent is not None
            assert result.structuredContent["error"] == "heading_not_found"
            assert len(result.structuredContent["available_headings"]) > 0
        finally:
            rh.STRUCTURED_OUTPUT_ENABLED = orig_structured

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_reading.get_outline_client"
    )
    async def test_read_document_section_includes_subheadings(
        self, mock_get_client, register_reading_tools
    ):
        """Test read_document_section includes subheadings."""
        mock_client = AsyncMock()
        mock_client.get_document.return_value = SAMPLE_DOCUMENT_WITH_HEADINGS
        mock_get_client.return_value = mock_client

        result = await register_reading_tools.tools["read_document_section"](
            "doc456", "Getting Started"
        )

        text = extract_text(result)
        # Should include subheadings
        assert "Installation" in text or "### Installation" in text
        assert "Configuration" in text or "### Configuration" in text

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_reading.get_outline_client"
    )
    async def test_read_document_section_error(
        self, mock_get_client, register_reading_tools
    ):
        """Test read_document_section handles errors gracefully."""
        mock_client = AsyncMock()
        mock_client.get_document.side_effect = OutlineClientError(
            "Document not found"
        )
        mock_get_client.return_value = mock_client

        result = await register_reading_tools.tools["read_document_section"](
            "invalid", "Some Section"
        )

        text = extract_text(result)
        assert "Error" in text
        assert "Document not found" in text

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_reading.get_outline_client"
    )
    async def test_read_document_section_generic_exception(
        self, mock_get_client, register_reading_tools
    ):
        """Test read_document_section handles generic exceptions."""
        mock_client = AsyncMock()
        mock_client.get_document.side_effect = RuntimeError("Unexpected error")
        mock_get_client.return_value = mock_client

        result = await register_reading_tools.tools["read_document_section"](
            "doc123", "Section"
        )

        text = extract_text(result)
        assert "Unexpected error" in text

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_reading.get_outline_client"
    )
    async def test_read_document_section_doc_with_no_headings(
        self, mock_get_client, register_reading_tools
    ):
        """Test read_document_section on doc with no headings."""
        import mcp_outline.utils.response_handler as rh

        orig_structured = rh.STRUCTURED_OUTPUT_ENABLED
        try:
            rh.STRUCTURED_OUTPUT_ENABLED = True

            doc_no_headings = {
                "id": "noheadings",
                "title": "No Headings",
                "text": "Just plain text without any headings.",
            }
            mock_client = AsyncMock()
            mock_client.get_document.return_value = doc_no_headings
            mock_get_client.return_value = mock_client

            result = await register_reading_tools.tools[
                "read_document_section"
            ]("noheadings", "Any Section")

            text = extract_text(result)
            assert "not found" in text
            assert "No headings found" in text
            assert result.structuredContent["available_headings"] == []
        finally:
            rh.STRUCTURED_OUTPUT_ENABLED = orig_structured
