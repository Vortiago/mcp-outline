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
        base = await cache.put("key1", "doc1", SAMPLE_DOC_DATA)
        await cache.stage_text("key1", "doc1", base, "modified")

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
        base = await cache.put("k", "doc1", SAMPLE_DOC_DATA)
        await cache.stage_text("k", "doc1", base, "dirty text")
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
    async def test_stage_text_marks_dirty(self):
        cache = DocumentCache(ttl=300, max_size=10)
        await cache.put("k", "doc1", SAMPLE_DOC_DATA)
        base = await cache.get("k", "doc1")
        assert base is not None
        await cache.stage_text("k", "doc1", base, "staged text")
        doc = await cache.get("k", "doc1")
        assert doc is not None
        assert doc.dirty is True
        assert doc.text == "staged text"

    @pytest.mark.asyncio
    async def test_stage_text_upserts_missing_entry(self):
        cache = DocumentCache(ttl=300, max_size=10)
        await cache.put("k", "doc1", SAMPLE_DOC_DATA)
        base = await cache.get("k", "doc1")
        assert base is not None
        # Entry evicted between fetch and staging (e.g. a
        # concurrent save) — staging must still persist
        await cache.evict("k", "doc1")
        await cache.stage_text("k", "doc1", base, "staged text")
        doc = await cache.get("k", "doc1")
        assert doc is not None
        assert doc.dirty is True
        assert doc.text == "staged text"
        assert doc.title == base.title

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
    async def test_evict_document_preserves_dirty_entries(self):
        cache = DocumentCache(ttl=300, max_size=10)
        await cache.put("key-A", "doc1", SAMPLE_DOC_DATA)
        base = await cache.put("key-B", "doc1", SAMPLE_DOC_DATA)
        await cache.stage_text("key-B", "doc1", base, "staged")
        await cache.evict_document("doc1")
        # Clean copy evicted, staged copy preserved
        assert await cache.get("key-A", "doc1") is None
        staged = await cache.get("key-B", "doc1")
        assert staged is not None
        assert staged.dirty is True
        assert staged.text == "staged"

    @pytest.mark.asyncio
    async def test_put_preserves_existing_dirty_entry(self):
        cache = DocumentCache(ttl=300, max_size=10)
        base = await cache.put("k", "doc1", SAMPLE_DOC_DATA)
        await cache.stage_text("k", "doc1", base, "staged")
        # A racing API fetch must not destroy staged edits
        await cache.put("k", "doc1", SAMPLE_DOC_DATA)
        doc = await cache.get("k", "doc1")
        assert doc is not None
        assert doc.dirty is True
        assert doc.text == "staged"

    @pytest.mark.asyncio
    async def test_invalidate_for_write(self):
        cache = DocumentCache(ttl=300, max_size=10)
        base_a = await cache.put("key-A", "doc1", SAMPLE_DOC_DATA)
        await cache.stage_text("key-A", "doc1", base_a, "A staged")
        await cache.put("key-B", "doc1", SAMPLE_DOC_DATA)
        base_c = await cache.put("key-C", "doc1", SAMPLE_DOC_DATA)
        await cache.stage_text("key-C", "doc1", base_c, "C staged")

        await cache.invalidate_for_write("key-A", "doc1")

        # Writer's own staged entry dropped; B's clean copy
        # dropped; C's staged edits preserved
        assert await cache.get("key-A", "doc1") is None
        assert await cache.get("key-B", "doc1") is None
        c_doc = await cache.get("key-C", "doc1")
        assert c_doc is not None
        assert c_doc.dirty is True

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
        assert cache._ttl == 30.0
        assert cache._max_size == 100

    @pytest.mark.asyncio
    async def test_default_short_cache_absorbs_bursts(self):
        """Without OUTLINE_CACHE_TTL, a short default cache
        serves repeated reads within the same task burst."""
        with patch.dict("os.environ", {}, clear=False):
            import os

            os.environ.pop("OUTLINE_CACHE_TTL", None)
            reset_document_cache()
            cache = get_document_cache()
            await cache.put(
                "k", "doc1", {"title": "T", "text": "x", "url": ""}
            )
            doc = await cache.get("k", "doc1")
            assert doc is not None
            assert doc.text == "x"

    @pytest.mark.asyncio
    async def test_ttl_zero_disables_caching(self):
        """OUTLINE_CACHE_TTL=0 disables clean-read caching;
        staging still works (dirty entries are exempt)."""
        with patch.dict("os.environ", {"OUTLINE_CACHE_TTL": "0"}):
            reset_document_cache()
            cache = get_document_cache()
            doc = await cache.put(
                "k", "doc1", {"title": "T", "text": "x", "url": ""}
            )
            assert await cache.get("k", "doc1") is None
            # Staging still works: dirty entries are exempt
            await cache.stage_text("k", "doc1", doc, "staged")
            staged = await cache.get("k", "doc1")
            assert staged is not None
            assert staged.dirty is True
            assert staged.text == "staged"
