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
_PATCH_READ_CLIENT = (
    "mcp_outline.features.documents.document_reading.get_outline_client"
)
_PATCH_READ_API_KEY = (
    "mcp_outline.features.documents.document_reading.get_resolved_api_key"
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
    @patch(_PATCH_API_KEY, return_value="key-a")
    @patch(_PATCH_CLIENT)
    @patch(_PATCH_FETCH)
    async def test_edit_save_preserves_other_users_staged_edits(
        self,
        mock_fetch,
        mock_get_client,
        mock_api_key,
        register_editing_tools,
    ):
        from mcp_outline.utils.document_cache import (
            get_document_cache,
        )

        cache = get_document_cache()
        await cache.put(
            "key-b",
            "doc-edit",
            {"title": "Editable Doc", "text": "Line one.", "url": ""},
        )
        await cache.update_text(
            "key-b", "doc-edit", "B staged text", dirty=True
        )

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
        assert "Saved to Outline" in result

        b_doc = await cache.get("key-b", "doc-edit")
        assert b_doc is not None
        assert b_doc.dirty is True
        assert b_doc.text == "B staged text"

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
    @patch(_PATCH_CLIENT)
    @patch(_PATCH_FETCH)
    async def test_edit_empty_edits_no_staged_changes(
        self,
        mock_fetch,
        mock_get_client,
        mock_api_key,
        register_editing_tools,
    ):
        mock_fetch.return_value = _make_cached_doc()
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

        result = await register_editing_tools.tools["edit_document"](
            document_id="doc-edit",
            edits=[],
        )
        assert "No edits provided" in result
        mock_client.post.assert_not_called()

    @pytest.mark.asyncio
    @patch(_PATCH_API_KEY, return_value="test-key")
    @patch(_PATCH_CLIENT)
    @patch(_PATCH_FETCH)
    async def test_edit_empty_edits_staged_without_save(
        self,
        mock_fetch,
        mock_get_client,
        mock_api_key,
        register_editing_tools,
    ):
        staged = _make_cached_doc("staged text")
        staged.dirty = True
        mock_fetch.return_value = staged
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

        result = await register_editing_tools.tools["edit_document"](
            document_id="doc-edit",
            edits=[],
            save=False,
        )
        assert "no staged changes" not in result
        assert "staged unsaved changes" in result
        assert "save=True" in result
        mock_client.post.assert_not_called()

    @pytest.mark.asyncio
    @patch(_PATCH_API_KEY, return_value="test-key")
    @patch(_PATCH_CLIENT)
    @patch(_PATCH_FETCH)
    async def test_edit_empty_edits_saves_staged_changes(
        self,
        mock_fetch,
        mock_get_client,
        mock_api_key,
        register_editing_tools,
    ):
        staged = _make_cached_doc("staged text")
        staged.dirty = True
        mock_fetch.return_value = staged
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "data": {
                "title": "Editable Doc",
                "text": "staged text",
            }
        }
        mock_get_client.return_value = mock_client

        result = await register_editing_tools.tools["edit_document"](
            document_id="doc-edit",
            edits=[],
            save=True,
        )
        assert "Saved to Outline" in result
        mock_client.post.assert_called_once_with(
            "documents.update",
            {"id": "doc-edit", "text": "staged text"},
        )

    @pytest.mark.asyncio
    @patch(_PATCH_READ_API_KEY, return_value="test-key")
    @patch(_PATCH_READ_CLIENT)
    @patch(_PATCH_API_KEY, return_value="test-key")
    @patch(_PATCH_CLIENT)
    async def test_edit_stage_then_flush_clears_dirty_state(
        self,
        mock_get_client,
        mock_api_key,
        mock_read_client,
        mock_read_api_key,
        register_editing_tools,
    ):
        from mcp_outline.utils.document_cache import (
            get_document_cache,
            reset_document_cache,
        )

        # Asserts post-flush re-caching, so enable caching
        with patch.dict("os.environ", {"OUTLINE_CACHE_TTL": "300"}):
            reset_document_cache()
            await self._run_stage_then_flush(
                mock_get_client,
                mock_read_client,
                register_editing_tools,
                get_document_cache,
            )

    async def _run_stage_then_flush(
        self,
        mock_get_client,
        mock_read_client,
        register_editing_tools,
        get_document_cache,
    ):
        read_client = AsyncMock()
        read_client.get_document.return_value = {
            "title": "Editable Doc",
            "text": "Line one.\nLine two.",
            "url": "/doc/editable",
        }
        mock_read_client.return_value = read_client
        save_client = AsyncMock()
        save_client.post.return_value = {
            "data": {
                "title": "Editable Doc",
                "text": "Line ONE.\nLine two.",
            }
        }
        mock_get_client.return_value = save_client

        tool = register_editing_tools.tools["edit_document"]
        staged = await tool(
            document_id="doc-edit",
            edits=[_edit("Line one.", "Line ONE.")],
            save=False,
        )
        assert "unsaved changes" in staged
        flushed = await tool(document_id="doc-edit", edits=[], save=True)
        assert "Saved to Outline" in flushed

        doc = await get_document_cache().get("test-key", "doc-edit")
        assert doc is not None
        assert doc.dirty is False
        assert doc.text == "Line ONE.\nLine two."

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
