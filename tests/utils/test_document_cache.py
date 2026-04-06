"""Tests for document cache."""

import time
from unittest.mock import patch

import pytest

from mcp_outline.utils.document_cache import (
    DocumentCache,
    get_document_cache,
    reset_document_cache,
)

SAMPLE_DOC_DATA = {
    "id": "doc1",
    "title": "Test Doc",
    "text": "Line 1\nLine 2\nLine 3",
    "url": "/doc/test-doc1",
}

SAMPLE_DOC_DATA_2 = {
    "id": "doc2",
    "title": "Another Doc",
    "text": "Hello world",
    "url": "/doc/test-doc2",
}


class TestDocumentCache:
    """Tests for DocumentCache."""

    @pytest.mark.asyncio
    async def test_put_and_get(self):
        cache = DocumentCache(ttl=300, max_size=10)
        await cache.put("key1", "doc1", SAMPLE_DOC_DATA)
        doc = await cache.get("key1", "doc1")
        assert doc is not None
        assert doc.title == "Test Doc"
        assert doc.text == "Line 1\nLine 2\nLine 3"
        assert doc.url == "/doc/test-doc1"
        assert doc.dirty is False

    @pytest.mark.asyncio
    async def test_get_miss(self):
        cache = DocumentCache(ttl=300, max_size=10)
        doc = await cache.get("key1", "nonexistent")
        assert doc is None

    @pytest.mark.asyncio
    async def test_cache_key_includes_api_key(self):
        cache = DocumentCache(ttl=300, max_size=10)
        await cache.put("key1", "doc1", SAMPLE_DOC_DATA)
        await cache.put("key2", "doc1", SAMPLE_DOC_DATA_2)
        doc1 = await cache.get("key1", "doc1")
        doc2 = await cache.get("key2", "doc1")
        assert doc1 is not None
        assert doc2 is not None
        assert doc1.title == "Test Doc"
        assert doc2.title == "Another Doc"

    @pytest.mark.asyncio
    async def test_ttl_expiry(self):
        cache = DocumentCache(ttl=1, max_size=10)
        await cache.put("key1", "doc1", SAMPLE_DOC_DATA)
        doc = await cache.get("key1", "doc1")
        assert doc is not None

        with patch(
            "mcp_outline.utils.document_cache.time.monotonic",
            return_value=time.monotonic() + 2,
        ):
            doc = await cache.get("key1", "doc1")
            assert doc is None

    @pytest.mark.asyncio
    async def test_dirty_entries_survive_ttl(self):
        cache = DocumentCache(ttl=1, max_size=10)
        await cache.put("key1", "doc1", SAMPLE_DOC_DATA)
        await cache.update_text("key1", "doc1", "modified", dirty=True)

        with patch(
            "mcp_outline.utils.document_cache.time.monotonic",
            return_value=time.monotonic() + 2,
        ):
            doc = await cache.get("key1", "doc1")
            assert doc is not None
            assert doc.text == "modified"
            assert doc.dirty is True

    @pytest.mark.asyncio
    async def test_lru_eviction(self):
        cache = DocumentCache(ttl=300, max_size=2)
        await cache.put("k", "doc1", SAMPLE_DOC_DATA)
        await cache.put("k", "doc2", SAMPLE_DOC_DATA_2)
        await cache.put(
            "k",
            "doc3",
            {"title": "Third", "text": "t", "url": ""},
        )
        # doc1 should be evicted (LRU)
        assert await cache.get("k", "doc1") is None
        assert await cache.get("k", "doc2") is not None
        assert await cache.get("k", "doc3") is not None

    @pytest.mark.asyncio
    async def test_lru_eviction_skips_dirty(self):
        cache = DocumentCache(ttl=300, max_size=2)
        await cache.put("k", "doc1", SAMPLE_DOC_DATA)
        await cache.update_text("k", "doc1", "dirty text", dirty=True)
        await cache.put("k", "doc2", SAMPLE_DOC_DATA_2)
        # Adding a third should skip dirty doc1, evict doc2
        await cache.put(
            "k",
            "doc3",
            {"title": "Third", "text": "t", "url": ""},
        )
        assert await cache.get("k", "doc1") is not None
        assert await cache.get("k", "doc2") is None
        assert await cache.get("k", "doc3") is not None

    @pytest.mark.asyncio
    async def test_update_text(self):
        cache = DocumentCache(ttl=300, max_size=10)
        await cache.put("k", "doc1", SAMPLE_DOC_DATA)
        await cache.update_text("k", "doc1", "new content", dirty=True)
        doc = await cache.get("k", "doc1")
        assert doc is not None
        assert doc.text == "new content"
        assert doc.dirty is True

    @pytest.mark.asyncio
    async def test_update_text_nonexistent(self):
        cache = DocumentCache(ttl=300, max_size=10)
        # Should not raise
        await cache.update_text("k", "nope", "text", dirty=True)

    @pytest.mark.asyncio
    async def test_mark_clean(self):
        cache = DocumentCache(ttl=300, max_size=10)
        await cache.put("k", "doc1", SAMPLE_DOC_DATA)
        await cache.update_text("k", "doc1", "staged", dirty=True)
        await cache.mark_clean("k", "doc1", "saved text", "New Title")
        doc = await cache.get("k", "doc1")
        assert doc is not None
        assert doc.text == "saved text"
        assert doc.title == "New Title"
        assert doc.dirty is False

    @pytest.mark.asyncio
    async def test_evict(self):
        cache = DocumentCache(ttl=300, max_size=10)
        await cache.put("k", "doc1", SAMPLE_DOC_DATA)
        await cache.evict("k", "doc1")
        assert await cache.get("k", "doc1") is None

    @pytest.mark.asyncio
    async def test_evict_nonexistent(self):
        cache = DocumentCache(ttl=300, max_size=10)
        # Should not raise
        await cache.evict("k", "nope")

    @pytest.mark.asyncio
    async def test_evict_document_all_keys(self):
        cache = DocumentCache(ttl=300, max_size=10)
        await cache.put("key-A", "doc1", SAMPLE_DOC_DATA)
        await cache.put("key-B", "doc1", SAMPLE_DOC_DATA)
        await cache.put("key-A", "doc2", SAMPLE_DOC_DATA_2)
        await cache.evict_document("doc1")
        assert await cache.get("key-A", "doc1") is None
        assert await cache.get("key-B", "doc1") is None
        # doc2 should be untouched
        assert await cache.get("key-A", "doc2") is not None

    @pytest.mark.asyncio
    async def test_clear(self):
        cache = DocumentCache(ttl=300, max_size=10)
        await cache.put("k", "doc1", SAMPLE_DOC_DATA)
        await cache.put("k", "doc2", SAMPLE_DOC_DATA_2)
        await cache.clear()
        assert await cache.get("k", "doc1") is None
        assert await cache.get("k", "doc2") is None

    @pytest.mark.asyncio
    async def test_put_overwrites_existing(self):
        cache = DocumentCache(ttl=300, max_size=10)
        await cache.put("k", "doc1", SAMPLE_DOC_DATA)
        await cache.put(
            "k",
            "doc1",
            {
                "title": "Updated",
                "text": "new",
                "url": "",
            },
        )
        doc = await cache.get("k", "doc1")
        assert doc is not None
        assert doc.title == "Updated"
        assert doc.text == "new"

    @pytest.mark.asyncio
    async def test_get_refreshes_lru_order(self):
        cache = DocumentCache(ttl=300, max_size=2)
        await cache.put("k", "doc1", SAMPLE_DOC_DATA)
        await cache.put("k", "doc2", SAMPLE_DOC_DATA_2)
        # Access doc1 to make it most recently used
        await cache.get("k", "doc1")
        # Add doc3 — should evict doc2 (now LRU)
        await cache.put(
            "k",
            "doc3",
            {"title": "Third", "text": "t", "url": ""},
        )
        assert await cache.get("k", "doc1") is not None
        assert await cache.get("k", "doc2") is None

    @pytest.mark.asyncio
    async def test_missing_fields_use_defaults(self):
        cache = DocumentCache(ttl=300, max_size=10)
        await cache.put("k", "doc1", {})
        doc = await cache.get("k", "doc1")
        assert doc is not None
        assert doc.title == "Untitled"
        assert doc.text == ""
        assert doc.url == ""


class TestGetDocumentCache:
    """Tests for the singleton accessor."""

    def setup_method(self):
        reset_document_cache()

    def teardown_method(self):
        reset_document_cache()

    def test_returns_singleton(self):
        c1 = get_document_cache()
        c2 = get_document_cache()
        assert c1 is c2

    def test_reads_env_vars(self):
        with patch.dict(
            "os.environ",
            {
                "OUTLINE_CACHE_TTL": "60",
                "OUTLINE_CACHE_MAX_SIZE": "50",
            },
        ):
            reset_document_cache()
            cache = get_document_cache()
            assert cache._ttl == 60.0
            assert cache._max_size == 50

    def test_defaults(self):
        cache = get_document_cache()
        assert cache._ttl == 300.0
        assert cache._max_size == 100
