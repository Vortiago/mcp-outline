"""
Tests for document editing tools (edit_document).
"""

from unittest.mock import AsyncMock, patch

import pytest

from mcp_outline.features.documents.document_editing import (
    _apply_edits,
)
from mcp_outline.features.documents.models import (
    DocumentEdit,
)
from mcp_outline.utils.document_cache import (
    CachedDocument,
    reset_document_cache,
)


def _edit(old: str, new: str) -> DocumentEdit:
    return DocumentEdit(old_string=old, new_string=new)


class MockMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, **kwargs):
        def decorator(func):
            self.tools[func.__name__] = func
            return func

        return decorator


@pytest.fixture
def mcp():
    return MockMCP()


@pytest.fixture
def register_editing_tools(mcp):
    from mcp_outline.features.documents.document_editing import (
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
    "mcp_outline.features.documents.document_editing.get_outline_client"
)
_PATCH_API_KEY = (
    "mcp_outline.features.documents.document_editing.get_resolved_api_key"
)
_PATCH_FETCH = (
    "mcp_outline.features.documents.document_editing.get_cached_or_fetch"
)


def _make_cached_doc(
    text="Line one.\nLine two.\nLine three.",
):
    return CachedDocument(
        title="Editable Doc",
        text=text,
        url="/doc/editable",
    )


class TestApplyEdits:
    """Tests for _apply_edits helper."""

    def test_single_edit(self):
        result = _apply_edits("hello world", [_edit("hello", "hi")])
        assert result == "hi world"

    def test_multiple_edits(self):
        result = _apply_edits(
            "hello world",
            [_edit("hello", "hi"), _edit("world", "earth")],
        )
        assert result == "hi earth"

    def test_dependent_edits(self):
        result = _apply_edits(
            "foo bar",
            [_edit("foo", "baz"), _edit("baz bar", "done")],
        )
        assert result == "done"

    def test_not_found(self):
        with pytest.raises(ValueError, match="not found"):
            _apply_edits("hello", [_edit("missing", "x")])

    def test_multiple_matches(self):
        with pytest.raises(ValueError, match="matches 2"):
            _apply_edits("foo foo", [_edit("foo", "bar")])

    def test_empty_old_string(self):
        with pytest.raises(ValueError, match="non-empty"):
            _apply_edits("hello", [_edit("", "x")])


class TestEditDocument:
    """Tests for edit_document tool."""

    @pytest.mark.asyncio
    @patch(_PATCH_API_KEY, return_value="test-key")
    @patch(_PATCH_CLIENT)
    @patch(_PATCH_FETCH)
    async def test_edit_and_save(
        self,
        mock_fetch,
        mock_get_client,
        mock_api_key,
        register_editing_tools,
    ):
        mock_fetch.return_value = _make_cached_doc()
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "data": {
                "title": "Editable Doc",
                "text": "Line one.\nLine TWO.\nLine three.",
            }
        }
        mock_get_client.return_value = mock_client

        result = await register_editing_tools.tools["edit_document"](
            document_id="doc-edit",
            edits=[_edit("Line two.", "Line TWO.")],
            save=True,
        )
        assert "Applied 1 edit(s)" in result
        assert "Saved to Outline" in result
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    @patch(_PATCH_API_KEY, return_value="test-key")
    @patch(_PATCH_FETCH)
    async def test_edit_stage_only(
        self,
        mock_fetch,
        mock_api_key,
        register_editing_tools,
    ):
        mock_fetch.return_value = _make_cached_doc()

        result = await register_editing_tools.tools["edit_document"](
            document_id="doc-edit",
            edits=[_edit("Line two.", "Line TWO.")],
            save=False,
        )
        assert "Applied 1 edit(s)" in result
        assert "unsaved changes" in result

    @pytest.mark.asyncio
    @patch(_PATCH_API_KEY, return_value="test-key")
    @patch(_PATCH_FETCH)
    async def test_edit_not_found(
        self,
        mock_fetch,
        mock_api_key,
        register_editing_tools,
    ):
        mock_fetch.return_value = _make_cached_doc("Line one.")

        result = await register_editing_tools.tools["edit_document"](
            document_id="doc-edit",
            edits=[_edit("missing", "x")],
        )
        assert "Edit failed" in result
        assert "not found" in result
        assert "No edits were applied" in result

    @pytest.mark.asyncio
    @patch(_PATCH_API_KEY, return_value="test-key")
    @patch(_PATCH_FETCH)
    async def test_edit_multiple_matches(
        self,
        mock_fetch,
        mock_api_key,
        register_editing_tools,
    ):
        mock_fetch.return_value = _make_cached_doc("foo foo")

        result = await register_editing_tools.tools["edit_document"](
            document_id="doc-edit",
            edits=[_edit("foo", "bar")],
        )
        assert "Edit failed" in result
        assert "matches 2" in result
