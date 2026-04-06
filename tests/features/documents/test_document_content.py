"""
Tests for document content tools (create, update, comment).
"""

from unittest.mock import AsyncMock, patch

import pytest

from mcp_outline.features.documents.common import (
    OutlineClientError,
)


class MockMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, **kwargs):
        def decorator(func):
            self.tools[func.__name__] = func
            return func

        return decorator


SAMPLE_CREATE_DOCUMENT_RESPONSE = {
    "data": {
        "id": "doc123",
        "title": "Test Document",
        "text": "This is a test document.",
        "updatedAt": "2023-01-01T12:00:00Z",
        "createdAt": "2023-01-01T12:00:00Z",
    }
}

SAMPLE_UPDATE_DOCUMENT_RESPONSE = {
    "data": {
        "id": "doc123",
        "title": "Updated Document",
        "text": "This document has been updated.",
        "updatedAt": "2023-01-02T12:00:00Z",
    }
}

SAMPLE_COMMENT_RESPONSE = {
    "data": {
        "id": "comment123",
        "documentId": "doc123",
        "createdById": "user123",
        "createdAt": "2023-01-01T12:00:00Z",
        "body": "This is a comment",
    }
}


@pytest.fixture
def mcp():
    return MockMCP()


@pytest.fixture
def register_content_tools(mcp):
    from mcp_outline.features.documents.document_content import (
        register_tools,
    )

    register_tools(mcp)
    return mcp


_PATCH_CLIENT = (
    "mcp_outline.features.documents.document_content.get_outline_client"
)


class TestDocumentContentTools:
    """Tests for document content tools."""

    @pytest.mark.asyncio
    @patch(_PATCH_CLIENT)
    async def test_create_document_success(
        self, mock_get_client, register_content_tools
    ):
        mock_client = AsyncMock()
        mock_client.post.return_value = SAMPLE_CREATE_DOCUMENT_RESPONSE
        mock_get_client.return_value = mock_client

        result = await register_content_tools.tools["create_document"](
            title="Test Document",
            collection_id="col123",
            text="This is a test document.",
        )

        mock_client.post.assert_called_once_with(
            "documents.create",
            {
                "title": "Test Document",
                "text": "This is a test document.",
                "collectionId": "col123",
                "publish": True,
            },
        )
        assert "Document created successfully" in result
        assert "Test Document" in result
        assert "doc123" in result

    @pytest.mark.asyncio
    @patch(_PATCH_CLIENT)
    async def test_create_document_with_parent(
        self, mock_get_client, register_content_tools
    ):
        mock_client = AsyncMock()
        mock_client.post.return_value = SAMPLE_CREATE_DOCUMENT_RESPONSE
        mock_get_client.return_value = mock_client

        _ = await register_content_tools.tools["create_document"](
            title="Test Document",
            collection_id="col123",
            text="This is a test document.",
            parent_document_id="parent123",
        )

        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args[0]
        assert call_args[0] == "documents.create"
        assert "parentDocumentId" in call_args[1]
        assert call_args[1]["parentDocumentId"] == "parent123"

    @pytest.mark.asyncio
    @patch(_PATCH_CLIENT)
    async def test_create_document_as_template(
        self, mock_get_client, register_content_tools
    ):
        mock_client = AsyncMock()
        mock_client.post.return_value = SAMPLE_CREATE_DOCUMENT_RESPONSE
        mock_get_client.return_value = mock_client

        _ = await register_content_tools.tools["create_document"](
            title="Test Template",
            collection_id="col123",
            text="Template content.",
            template=True,
        )

        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args[0]
        assert call_args[0] == "documents.create"
        assert call_args[1]["template"] is True

    @pytest.mark.asyncio
    @patch(_PATCH_CLIENT)
    async def test_create_document_template_not_sent_when_none(
        self, mock_get_client, register_content_tools
    ):
        mock_client = AsyncMock()
        mock_client.post.return_value = SAMPLE_CREATE_DOCUMENT_RESPONSE
        mock_get_client.return_value = mock_client

        _ = await register_content_tools.tools["create_document"](
            title="Test Document", collection_id="col123"
        )

        call_args = mock_client.post.call_args[0]
        assert "template" not in call_args[1]

    @pytest.mark.asyncio
    @patch(_PATCH_CLIENT)
    async def test_create_document_with_icon(
        self, mock_get_client, register_content_tools
    ):
        mock_client = AsyncMock()
        mock_client.post.return_value = SAMPLE_CREATE_DOCUMENT_RESPONSE
        mock_get_client.return_value = mock_client

        _ = await register_content_tools.tools["create_document"](
            title="Test Document",
            collection_id="col123",
            icon="📋",
        )

        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args[0]
        assert call_args[0] == "documents.create"
        assert call_args[1]["icon"] == "📋"

    @pytest.mark.asyncio
    @patch(_PATCH_CLIENT)
    async def test_create_document_icon_not_sent_when_none(
        self, mock_get_client, register_content_tools
    ):
        mock_client = AsyncMock()
        mock_client.post.return_value = SAMPLE_CREATE_DOCUMENT_RESPONSE
        mock_get_client.return_value = mock_client

        _ = await register_content_tools.tools["create_document"](
            title="Test Document",
            collection_id="col123",
        )

        call_args = mock_client.post.call_args[0]
        assert "icon" not in call_args[1]

    @pytest.mark.asyncio
    @patch(_PATCH_CLIENT)
    async def test_create_document_failure(
        self, mock_get_client, register_content_tools
    ):
        mock_client = AsyncMock()
        mock_client.post.return_value = {"data": None}
        mock_get_client.return_value = mock_client

        result = await register_content_tools.tools["create_document"](
            title="Test Document", collection_id="col123"
        )
        assert "Failed to create document" in result

    @pytest.mark.asyncio
    @patch(_PATCH_CLIENT)
    async def test_create_document_client_error(
        self, mock_get_client, register_content_tools
    ):
        mock_client = AsyncMock()
        mock_client.post.side_effect = OutlineClientError("API error")
        mock_get_client.return_value = mock_client

        result = await register_content_tools.tools["create_document"](
            title="Test Document", collection_id="col123"
        )
        assert "Error creating document" in result
        assert "API error" in result

    @pytest.mark.asyncio
    @patch(_PATCH_CLIENT)
    async def test_update_document_success(
        self, mock_get_client, register_content_tools
    ):
        mock_client = AsyncMock()
        mock_client.post.return_value = SAMPLE_UPDATE_DOCUMENT_RESPONSE
        mock_get_client.return_value = mock_client

        result = await register_content_tools.tools["update_document"](
            document_id="doc123",
            title="Updated Document",
            text="This document has been updated.",
        )

        mock_client.post.assert_called_once_with(
            "documents.update",
            {
                "id": "doc123",
                "title": "Updated Document",
                "text": "This document has been updated.",
                "append": False,
            },
        )
        assert "Document updated successfully" in result
        assert "Updated Document" in result

    @pytest.mark.asyncio
    @patch(_PATCH_CLIENT)
    async def test_update_document_append(
        self, mock_get_client, register_content_tools
    ):
        mock_client = AsyncMock()
        mock_client.post.return_value = SAMPLE_UPDATE_DOCUMENT_RESPONSE
        mock_get_client.return_value = mock_client

        _ = await register_content_tools.tools["update_document"](
            document_id="doc123",
            text="Additional text.",
            append=True,
        )

        call_args = mock_client.post.call_args[0]
        assert call_args[0] == "documents.update"
        assert call_args[1]["append"] is True

    @pytest.mark.asyncio
    @patch(_PATCH_CLIENT)
    async def test_update_document_set_template(
        self, mock_get_client, register_content_tools
    ):
        mock_client = AsyncMock()
        mock_client.post.return_value = SAMPLE_UPDATE_DOCUMENT_RESPONSE
        mock_get_client.return_value = mock_client

        _ = await register_content_tools.tools["update_document"](
            document_id="doc123", template=True
        )

        mock_client.post.assert_called_once_with(
            "documents.update",
            {"id": "doc123", "template": True},
        )

    @pytest.mark.asyncio
    @patch(_PATCH_CLIENT)
    async def test_update_document_unset_template(
        self, mock_get_client, register_content_tools
    ):
        mock_client = AsyncMock()
        mock_client.post.return_value = SAMPLE_UPDATE_DOCUMENT_RESPONSE
        mock_get_client.return_value = mock_client

        _ = await register_content_tools.tools["update_document"](
            document_id="doc123", template=False
        )

        mock_client.post.assert_called_once_with(
            "documents.update",
            {"id": "doc123", "template": False},
        )

    @pytest.mark.asyncio
    @patch(_PATCH_CLIENT)
    async def test_update_document_with_icon(
        self, mock_get_client, register_content_tools
    ):
        mock_client = AsyncMock()
        mock_client.post.return_value = SAMPLE_UPDATE_DOCUMENT_RESPONSE
        mock_get_client.return_value = mock_client

        _ = await register_content_tools.tools["update_document"](
            document_id="doc123",
            icon="🚀",
        )

        mock_client.post.assert_called_once_with(
            "documents.update",
            {
                "id": "doc123",
                "icon": "🚀",
            },
        )

    @pytest.mark.asyncio
    @patch(_PATCH_CLIENT)
    async def test_update_document_remove_icon(
        self, mock_get_client, register_content_tools
    ):
        mock_client = AsyncMock()
        mock_client.post.return_value = SAMPLE_UPDATE_DOCUMENT_RESPONSE
        mock_get_client.return_value = mock_client

        _ = await register_content_tools.tools["update_document"](
            document_id="doc123",
            icon="",
        )

        mock_client.post.assert_called_once_with(
            "documents.update",
            {
                "id": "doc123",
                "icon": None,
            },
        )

    @pytest.mark.asyncio
    @patch(_PATCH_CLIENT)
    async def test_update_document_icon_not_sent_when_none(
        self, mock_get_client, register_content_tools
    ):
        mock_client = AsyncMock()
        mock_client.post.return_value = SAMPLE_UPDATE_DOCUMENT_RESPONSE
        mock_get_client.return_value = mock_client

        _ = await register_content_tools.tools["update_document"](
            document_id="doc123",
            title="Updated Title",
        )

        mock_client.post.assert_called_once_with(
            "documents.update",
            {
                "id": "doc123",
                "title": "Updated Title",
            },
        )

    @pytest.mark.asyncio
    @patch(_PATCH_CLIENT)
    async def test_update_document_template_not_sent_when_none(
        self, mock_get_client, register_content_tools
    ):
        mock_client = AsyncMock()
        mock_client.post.return_value = SAMPLE_UPDATE_DOCUMENT_RESPONSE
        mock_get_client.return_value = mock_client

        _ = await register_content_tools.tools["update_document"](
            document_id="doc123", title="Updated Title"
        )

        mock_client.post.assert_called_once_with(
            "documents.update",
            {"id": "doc123", "title": "Updated Title"},
        )

    @pytest.mark.asyncio
    @patch(_PATCH_CLIENT)
    async def test_update_document_evicts_cache_all_keys(
        self,
        mock_get_client,
        register_content_tools,
    ):
        """Verify update_document evicts all cached copies
        of the document regardless of API key."""
        from mcp_outline.utils.document_cache import (
            get_document_cache,
            reset_document_cache,
        )

        reset_document_cache()
        cache = get_document_cache()
        doc_data = {
            "title": "Old",
            "text": "Old text.",
            "url": "",
        }
        await cache.put("key-A", "doc123", doc_data)
        await cache.put("key-B", "doc123", doc_data)

        mock_client = AsyncMock()
        mock_client.post.return_value = SAMPLE_UPDATE_DOCUMENT_RESPONSE
        mock_get_client.return_value = mock_client

        await register_content_tools.tools["update_document"](
            document_id="doc123",
            text="New text.",
        )

        assert await cache.get("key-A", "doc123") is None
        assert await cache.get("key-B", "doc123") is None
        reset_document_cache()

    @pytest.mark.asyncio
    @patch(_PATCH_CLIENT)
    async def test_add_comment_success(
        self, mock_get_client, register_content_tools
    ):
        mock_client = AsyncMock()
        mock_client.post.return_value = SAMPLE_COMMENT_RESPONSE
        mock_get_client.return_value = mock_client

        result = await register_content_tools.tools["add_comment"](
            document_id="doc123",
            text="This is a comment",
        )

        mock_client.post.assert_called_once_with(
            "comments.create",
            {
                "documentId": "doc123",
                "text": "This is a comment",
            },
        )
        assert "Comment added successfully" in result
        assert "comment123" in result

    @pytest.mark.asyncio
    @patch(_PATCH_CLIENT)
    async def test_add_comment_failure(
        self, mock_get_client, register_content_tools
    ):
        mock_client = AsyncMock()
        mock_client.post.return_value = {"data": None}
        mock_get_client.return_value = mock_client

        result = await register_content_tools.tools["add_comment"](
            document_id="doc123",
            text="This is a comment",
        )
        assert "Failed to create comment" in result

    @pytest.mark.asyncio
    @patch(_PATCH_CLIENT)
    async def test_add_comment_client_error(
        self, mock_get_client, register_content_tools
    ):
        mock_client = AsyncMock()
        mock_client.post.side_effect = OutlineClientError("API error")
        mock_get_client.return_value = mock_client

        result = await register_content_tools.tools["add_comment"](
            document_id="doc123",
            text="This is a comment",
        )
        assert "Error adding comment" in result
        assert "API error" in result
