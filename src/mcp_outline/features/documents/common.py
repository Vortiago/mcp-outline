"""
Common utilities for document outline features.

This module provides shared functionality used by both tools and resources.
"""

import os
from typing import Optional

from mcp_outline.utils.outline_client import (
    OutlineClient,
    OutlineError,
    _sanitize_value,
)


class OutlineClientError(Exception):
    """Exception raised for errors in document outline client operations."""

    pass


def _get_header_api_key() -> Optional[str]:
    """Get Outline API key from the current HTTP request header.

    Reads the ``x-outline-api-key`` header from the MCP SDK's
    request context. The SDK stores the Starlette ``Request``
    object in a ``ContextVar`` during every tool call for both
    SSE and streamable-http transports.

    Returns ``None`` when:
    - Not inside a request context (e.g. startup, tests)
    - Using stdio transport (no HTTP request available)
    - The header is not present in the request

    Returns:
        Sanitized API key string, or None.
    """
    try:
        from mcp.server.lowlevel.server import (
            request_ctx,
        )

        ctx = request_ctx.get()
        if ctx.request is not None:
            raw = ctx.request.headers.get("x-outline-api-key")
            return _sanitize_value(raw)
    except (LookupError, ImportError, AttributeError):
        pass
    return None


def get_resolved_api_key() -> str:
    """Return the API key for the current request.

    Priority: ``x-outline-api-key`` HTTP header > ``OUTLINE_API_KEY``
    environment variable. Returns empty string when neither is set.
    """
    return _get_header_api_key() or os.getenv("OUTLINE_API_KEY", "")


async def get_outline_client() -> OutlineClient:
    """Get the document outline client (async).

    Checks for a per-request API key from the
    ``x-outline-api-key`` HTTP header first, then falls back
    to the ``OUTLINE_API_KEY`` environment variable.

    Returns:
        OutlineClient instance

    Raises:
        OutlineClientError: If client creation fails
    """
    try:
        api_key = get_resolved_api_key() or None
        api_url = os.getenv("OUTLINE_API_URL")

        # Create an instance of the outline client
        return OutlineClient(api_key=api_key, api_url=api_url)
    except OutlineError as e:
        raise OutlineClientError(f"Outline client error: {str(e)}")
    except Exception as e:
        raise OutlineClientError(f"Unexpected error: {str(e)}")
