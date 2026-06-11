"""
Shared fixtures for document feature tests.
"""

import pytest

from mcp_outline.utils.document_cache import reset_document_cache


@pytest.fixture
def enable_doc_cache(monkeypatch):
    """Enable document caching (off by default) for a test."""
    monkeypatch.setenv("OUTLINE_CACHE_TTL", "300")
    reset_document_cache()
    yield
    reset_document_cache()
