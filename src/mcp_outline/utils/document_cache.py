"""In-memory LRU document cache with TTL.

Caches Outline document content to reduce API calls and support
staged edits. Thread-safe via asyncio.Lock.
"""

import asyncio
import os
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple


@dataclass
class CachedDocument:
    """A cached Outline document with metadata."""

    title: str
    text: str
    url: str
    cached_at: float = field(default_factory=time.monotonic)
    dirty: bool = False


class DocumentCache:
    """LRU document cache with TTL and dirty-tracking.

    Uses ``OrderedDict`` for O(1) LRU operations and
    ``asyncio.Lock`` for safe concurrent access.
    """

    def __init__(
        self,
        ttl: float = 300.0,
        max_size: int = 100,
    ) -> None:
        self._ttl = ttl
        self._max_size = max_size
        self._store: OrderedDict[Tuple[str, str], CachedDocument] = (
            OrderedDict()
        )
        self._lock = asyncio.Lock()

    async def get(
        self, api_key: str, document_id: str
    ) -> Optional[CachedDocument]:
        """Return cached doc if present and not expired."""
        async with self._lock:
            key = (api_key, document_id)
            doc = self._store.get(key)
            if doc is None:
                return None
            if self._is_expired(doc) and not doc.dirty:
                del self._store[key]
                return None
            self._store.move_to_end(key)
            return doc

    async def put(
        self,
        api_key: str,
        document_id: str,
        data: Dict[str, Any],
    ) -> CachedDocument:
        """Cache a document from an API response dict."""
        async with self._lock:
            key = (api_key, document_id)
            doc = CachedDocument(
                title=data.get("title", "Untitled"),
                text=data.get("text", ""),
                url=data.get("url", ""),
                cached_at=time.monotonic(),
                dirty=False,
            )
            self._store[key] = doc
            self._store.move_to_end(key)
            self._evict_if_needed()
            return doc

    async def update_text(
        self,
        api_key: str,
        document_id: str,
        text: str,
        dirty: bool,
    ) -> None:
        """Update cached text and dirty flag."""
        async with self._lock:
            key = (api_key, document_id)
            doc = self._store.get(key)
            if doc is None:
                return
            doc.text = text
            doc.dirty = dirty
            doc.cached_at = time.monotonic()
            self._store.move_to_end(key)

    async def mark_clean(
        self,
        api_key: str,
        document_id: str,
        text: str,
        title: str,
    ) -> None:
        """Clear dirty flag after a successful save."""
        async with self._lock:
            key = (api_key, document_id)
            doc = self._store.get(key)
            if doc is None:
                return
            doc.text = text
            doc.title = title
            doc.dirty = False
            doc.cached_at = time.monotonic()

    async def evict(self, api_key: str, document_id: str) -> None:
        """Remove a specific cache entry."""
        async with self._lock:
            key = (api_key, document_id)
            self._store.pop(key, None)

    async def evict_document(self, document_id: str) -> None:
        """Remove all cache entries for a document ID,
        regardless of API key."""
        async with self._lock:
            keys_to_remove = [k for k in self._store if k[1] == document_id]
            for key in keys_to_remove:
                del self._store[key]

    async def clear(self) -> None:
        """Remove all entries."""
        async with self._lock:
            self._store.clear()

    def _is_expired(self, doc: CachedDocument) -> bool:
        return (time.monotonic() - doc.cached_at) > self._ttl

    def _evict_if_needed(self) -> None:
        """Evict LRU entries until under max_size.

        Skips dirty entries to avoid losing staged edits.
        """
        while len(self._store) > self._max_size:
            evicted = False
            for key in list(self._store):
                if not self._store[key].dirty:
                    del self._store[key]
                    evicted = True
                    break
            if not evicted:
                break


_cache: Optional[DocumentCache] = None


def get_document_cache() -> DocumentCache:
    """Return the module-level cache singleton.

    Reads ``OUTLINE_CACHE_TTL`` and ``OUTLINE_CACHE_MAX_SIZE``
    from the environment on first call.
    """
    global _cache
    if _cache is None:
        ttl = float(os.getenv("OUTLINE_CACHE_TTL", "300"))
        max_size = int(os.getenv("OUTLINE_CACHE_MAX_SIZE", "100"))
        _cache = DocumentCache(ttl=ttl, max_size=max_size)
    return _cache


def reset_document_cache() -> None:
    """Reset the singleton (for tests)."""
    global _cache
    _cache = None
