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
        """Cache a document from an API response dict.

        If a dirty (staged) entry already exists it is
        returned unchanged — a racing API fetch must not
        destroy staged edits. Use ``evict`` first when the
        overwrite is intentional (e.g. after a save).
        """
        async with self._lock:
            key = (api_key, document_id)
            existing = self._store.get(key)
            if existing is not None and existing.dirty:
                self._store.move_to_end(key)
                return existing
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

    async def stage_text(
        self,
        api_key: str,
        document_id: str,
        base: CachedDocument,
        text: str,
    ) -> None:
        """Stage edited text as a dirty entry (upsert).

        Never silently no-ops: if the entry vanished (e.g.
        evicted by a concurrent save), it is recreated from
        ``base``.
        """
        async with self._lock:
            key = (api_key, document_id)
            self._store[key] = CachedDocument(
                title=base.title,
                text=text,
                url=base.url,
                cached_at=time.monotonic(),
                dirty=True,
            )
            self._store.move_to_end(key)
            self._evict_if_needed()

    async def evict(self, api_key: str, document_id: str) -> None:
        """Remove a specific cache entry."""
        async with self._lock:
            key = (api_key, document_id)
            self._store.pop(key, None)

    async def evict_document(self, document_id: str) -> None:
        """Remove clean cache entries for a document ID,
        regardless of API key.

        Dirty (staged) entries are preserved so one user's
        save never silently destroys another user's staged
        edits. Use ``evict`` to drop a specific entry
        unconditionally.
        """
        async with self._lock:
            self._evict_clean_locked(document_id)

    async def invalidate_for_write(
        self, api_key: str, document_id: str
    ) -> None:
        """Invalidate after a successful write: drop the
        writer's own entry (staged or not — it is superseded
        by the write) and all clean copies of the document.
        Other users' staged edits are preserved."""
        async with self._lock:
            self._store.pop((api_key, document_id), None)
            self._evict_clean_locked(document_id)

    def _evict_clean_locked(self, document_id: str) -> None:
        keys_to_remove = [
            k
            for k in self._store
            if k[1] == document_id and not self._store[k].dirty
        ]
        for key in keys_to_remove:
            del self._store[key]

    async def clear(self) -> None:
        """Remove all entries."""
        async with self._lock:
            self._store.clear()

    def _is_expired(self, doc: CachedDocument) -> bool:
        if self._ttl <= 0:
            # Caching disabled: clean entries are never
            # served. Dirty (staged) entries are exempt at
            # the call sites.
            return True
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
    from the environment on first call. The default TTL of
    30 seconds absorbs same-task read bursts (TOC, search,
    sections of one document) without hammering the Outline
    API, while keeping staleness short. Set
    ``OUTLINE_CACHE_TTL=0`` to disable caching entirely or
    a higher value for more API savings. Staged edits
    (dirty entries) work regardless.
    """
    global _cache
    if _cache is None:
        ttl = float(os.getenv("OUTLINE_CACHE_TTL", "30"))
        max_size = int(os.getenv("OUTLINE_CACHE_MAX_SIZE", "100"))
        _cache = DocumentCache(ttl=ttl, max_size=max_size)
    return _cache


def reset_document_cache() -> None:
    """Reset the singleton (for tests)."""
    global _cache
    _cache = None
