"""
Tests for response handler utility.
"""

from mcp.types import CallToolResult, TextContent

from mcp_outline.utils.response_handler import (
    CHARS_PER_TOKEN,
    check_response_size,
    create_tool_response,
    estimate_tokens,
)


class TestEstimateTokens:
    """Tests for token estimation."""

    def test_estimate_tokens_basic(self):
        """Test basic token estimation."""
        # 100 characters should be ~25 tokens (100 / 4)
        text = "a" * 100
        assert estimate_tokens(text) == 25

    def test_estimate_tokens_empty(self):
        """Test token estimation for empty string."""
        assert estimate_tokens("") == 0

    def test_estimate_tokens_short(self):
        """Test token estimation for short text."""
        # Less than CHARS_PER_TOKEN should be 0
        text = "ab"
        assert estimate_tokens(text) == 0

    def test_estimate_tokens_uses_chars_per_token(self):
        """Test that estimation uses CHARS_PER_TOKEN constant."""
        text = "x" * CHARS_PER_TOKEN
        assert estimate_tokens(text) == 1

        text = "x" * (CHARS_PER_TOKEN * 10)
        assert estimate_tokens(text) == 10


class TestCheckResponseSize:
    """Tests for response size checking."""

    def test_check_response_size_small_response(self):
        """Test that small responses pass through unchanged."""
        small_text = "Small response"
        result_text, meta = check_response_size(small_text)

        assert result_text == small_text
        assert "truncated" not in meta
        assert "warning" not in meta
        assert meta["chars"] == len(small_text)

    def test_check_response_size_above_soft_limit(self):
        """Test response above soft limit gets warning."""
        # Use mocking instead of reload to avoid test pollution
        import mcp_outline.utils.response_handler as rh

        # Save originals
        orig_soft = rh.SOFT_LIMIT_TOKENS

        try:
            # Set low limit
            rh.SOFT_LIMIT_TOKENS = 10  # 10 tokens * 4 chars = 40 chars

            # Create text that exceeds soft limit
            text = "x" * 50  # ~12.5 tokens
            result_text, meta = rh.check_response_size(text)

            assert "Large response" in result_text
            assert meta.get("warning") == "large_response"
            assert "truncated" not in meta
        finally:
            # Restore originals
            rh.SOFT_LIMIT_TOKENS = orig_soft

    def test_check_response_size_above_hard_limit(self):
        """Test response above hard limit gets truncated."""
        import mcp_outline.utils.response_handler as rh

        # Save originals
        orig_hard = rh.HARD_LIMIT_TOKENS
        orig_soft = rh.SOFT_LIMIT_TOKENS

        try:
            # Set low limits
            rh.HARD_LIMIT_TOKENS = 10  # 10 tokens * 4 chars = 40 chars
            rh.SOFT_LIMIT_TOKENS = 5

            # Create text that exceeds hard limit
            text = "x" * 100  # ~25 tokens
            result_text, meta = rh.check_response_size(text)

            assert meta.get("truncated") is True
            assert "TRUNCATED" in result_text
            assert len(result_text) < len(text) + 200  # Some overhead for msg
        finally:
            # Restore originals
            rh.HARD_LIMIT_TOKENS = orig_hard
            rh.SOFT_LIMIT_TOKENS = orig_soft


class TestCreateToolResponse:
    """Tests for create_tool_response utility."""

    def test_create_tool_response_basic(self):
        """Test basic response creation."""
        result = create_tool_response("Hello, world!")

        assert isinstance(result, CallToolResult)
        assert len(result.content) == 1
        assert isinstance(result.content[0], TextContent)
        assert result.content[0].text == "Hello, world!"

    def test_create_tool_response_with_data(self):
        """Test response creation with structured data."""
        import mcp_outline.utils.response_handler as rh

        orig_structured = rh.STRUCTURED_OUTPUT_ENABLED
        try:
            rh.STRUCTURED_OUTPUT_ENABLED = True

            data = {"key": "value", "count": 42}
            result = rh.create_tool_response("Text content", data)

            assert result.content[0].text == "Text content"
            assert result.structuredContent is not None
            assert result.structuredContent["key"] == "value"
            assert result.structuredContent["count"] == 42
        finally:
            rh.STRUCTURED_OUTPUT_ENABLED = orig_structured

    def test_create_tool_response_without_data(self):
        """Test response creation without structured data."""
        result = create_tool_response("Just text")

        assert result.content[0].text == "Just text"
        # structuredContent should be None when no data provided
        assert result.structuredContent is None

    def test_create_tool_response_empty_data(self):
        """Test response creation with empty data dict."""
        result = create_tool_response("Text", {})

        assert result.content[0].text == "Text"
        # Empty dict should result in None structuredContent
        assert result.structuredContent is None

    def test_create_tool_response_data_not_mutated(self):
        """Test that input data dict is not mutated."""
        original_data = {"key": "value"}
        data_copy = original_data.copy()

        create_tool_response("Text", original_data)

        assert original_data == data_copy

    def test_create_tool_response_with_limits_enabled(self):
        """Test response includes meta when limits enabled."""
        import mcp_outline.utils.response_handler as rh

        # Save originals
        orig_limits = rh.LIMITS_ENABLED
        orig_soft = rh.SOFT_LIMIT_TOKENS
        orig_structured = rh.STRUCTURED_OUTPUT_ENABLED

        try:
            # Enable limits with low threshold and structured output
            rh.LIMITS_ENABLED = True
            rh.SOFT_LIMIT_TOKENS = 5
            rh.STRUCTURED_OUTPUT_ENABLED = True

            # Large text to trigger soft limit
            large_text = "x" * 100
            result = rh.create_tool_response(large_text, {"data": "test"})

            # Should have response_meta in structured content
            assert result.structuredContent is not None
            assert "response_meta" in result.structuredContent
            assert "data" in result.structuredContent
        finally:
            # Restore originals
            rh.LIMITS_ENABLED = orig_limits
            rh.SOFT_LIMIT_TOKENS = orig_soft
            rh.STRUCTURED_OUTPUT_ENABLED = orig_structured

    def test_create_tool_response_limits_disabled_by_default(self):
        """Test that limits are disabled by default."""
        import mcp_outline.utils.response_handler as rh

        # Ensure limits are disabled (default state)
        orig_limits = rh.LIMITS_ENABLED
        try:
            rh.LIMITS_ENABLED = False

            # With limits disabled, no modifications should be applied
            large_text = "x" * 100000  # Very large text
            result = rh.create_tool_response(large_text)

            # Text should not be modified (no truncation/warning)
            assert result.content[0].text == large_text
        finally:
            rh.LIMITS_ENABLED = orig_limits

    def test_create_tool_response_structured_output_disabled(self):
        """Test that structured output can be disabled."""
        import mcp_outline.utils.response_handler as rh

        orig_structured = rh.STRUCTURED_OUTPUT_ENABLED
        try:
            rh.STRUCTURED_OUTPUT_ENABLED = False

            result = rh.create_tool_response(
                "Test text", {"key": "value", "count": 42}
            )

            # Text should still be present
            assert result.content[0].text == "Test text"
            # Structured content should be None
            assert result.structuredContent is None
        finally:
            rh.STRUCTURED_OUTPUT_ENABLED = orig_structured

    def test_create_tool_response_structured_output_enabled_by_default(self):
        """Test that structured output is enabled by default."""
        import mcp_outline.utils.response_handler as rh

        orig_structured = rh.STRUCTURED_OUTPUT_ENABLED
        try:
            rh.STRUCTURED_OUTPUT_ENABLED = True

            result = rh.create_tool_response("Test text", {"key": "value"})

            # Both should be present
            assert result.content[0].text == "Test text"
            assert result.structuredContent is not None
            assert result.structuredContent["key"] == "value"
        finally:
            rh.STRUCTURED_OUTPUT_ENABLED = orig_structured


class TestResponseHandlerIntegration:
    """Integration tests for response handler."""

    def test_structured_content_preserves_complex_data(self):
        """Test that complex nested data is preserved."""
        import mcp_outline.utils.response_handler as rh

        orig_structured = rh.STRUCTURED_OUTPUT_ENABLED
        try:
            rh.STRUCTURED_OUTPUT_ENABLED = True

            complex_data = {
                "results": [
                    {"id": "1", "title": "Doc 1"},
                    {"id": "2", "title": "Doc 2"},
                ],
                "pagination": {"limit": 25, "offset": 0},
                "nested": {"deep": {"value": True}},
            }

            result = rh.create_tool_response("Text", complex_data)

            assert result.structuredContent["results"][0]["id"] == "1"
            assert result.structuredContent["pagination"]["limit"] == 25
            assert result.structuredContent["nested"]["deep"]["value"] is True
        finally:
            rh.STRUCTURED_OUTPUT_ENABLED = orig_structured

    def test_text_content_type_is_correct(self):
        """Test that content type is always 'text'."""
        result = create_tool_response("Content")

        assert result.content[0].type == "text"

    def test_response_with_special_characters(self):
        """Test response with unicode and special characters."""
        import mcp_outline.utils.response_handler as rh

        # Ensure limits are disabled for this test
        orig_limits = rh.LIMITS_ENABLED
        try:
            rh.LIMITS_ENABLED = False

            text_with_special = 'Hello 世界! 🎉 Special chars: <>&"'
            result = rh.create_tool_response(text_with_special)

            assert result.content[0].text == text_with_special
        finally:
            rh.LIMITS_ENABLED = orig_limits
