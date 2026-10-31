"""
Tests for common utilities (get_outline_client, _get_header_api_key).
"""

import os
from types import SimpleNamespace
from typing import Optional
from unittest.mock import AsyncMock, patch

import pytest
from starlette.datastructures import Headers

from mcp_outline.features.documents.common import (
    OutlineClientError,
    _get_header_api_key,
    get_outline_client,
)
from mcp_outline.request_context import capture_request_headers


async def _header_key_during_request(
    headers: Optional[dict],
) -> Optional[str]:
    """Run the header middleware and read the key inside the message.

    ``headers=None`` stands for a message with no HTTP request (stdio).
    """
    request = (
        None if headers is None else SimpleNamespace(headers=Headers(headers))
    )
    ctx = SimpleNamespace(request=request)

    async def call_next(_ctx):
        return _get_header_api_key()

    return await capture_request_headers(ctx, call_next)  # type: ignore[arg-type]


class TestGetHeaderApiKey:
    """Tests for the _get_header_api_key helper."""

    def test_returns_none_outside_request_context(self):
        """No message in progress -> returns None."""
        assert _get_header_api_key() is None

    @pytest.mark.asyncio
    async def test_returns_key_from_header(self):
        """Header present -> returns key value."""
        result = await _header_key_during_request(
            {"x-outline-api-key": "sk-test-key"}
        )
        assert result == "sk-test-key"

    @pytest.mark.asyncio
    async def test_returns_none_when_header_absent(self):
        """Request exists but header missing -> None."""
        assert await _header_key_during_request({}) is None

    @pytest.mark.asyncio
    async def test_sanitizes_header_value(self):
        """Quoted/whitespace values are cleaned."""
        result = await _header_key_during_request(
            {"x-outline-api-key": '  "sk-quoted"  '}
        )
        assert result == "sk-quoted"

    @pytest.mark.asyncio
    async def test_returns_none_when_request_is_none(self):
        """Message with no HTTP request (stdio) -> None."""
        assert await _header_key_during_request(None) is None

    @pytest.mark.asyncio
    async def test_header_cleared_after_message(self):
        """The header does not outlive its message."""
        await _header_key_during_request({"x-outline-api-key": "sk-gone"})
        assert _get_header_api_key() is None


# ---------------------------------------------------------------------------
# Tests for get_outline_client
# ---------------------------------------------------------------------------


class TestGetOutlineClient:
    """Tests for get_outline_client with per-request key."""

    @pytest.mark.anyio
    async def test_uses_header_key_over_env_var(self):
        """Header key takes priority over env var."""
        with (
            patch(
                "mcp_outline.features.documents.common._get_header_api_key",
                return_value="header-key",
            ),
            patch.dict(
                os.environ,
                {"OUTLINE_API_KEY": "env-key"},
            ),
            patch(
                "mcp_outline.features.documents.common.OutlineClient"
            ) as mock_cls,
        ):
            mock_cls.return_value = AsyncMock()

            await get_outline_client()
            mock_cls.assert_called_once_with(
                api_key="header-key", api_url=None
            )

    @pytest.mark.anyio
    async def test_falls_back_to_env_var(self):
        """No header -> uses env var."""
        with (
            patch(
                "mcp_outline.features.documents.common._get_header_api_key",
                return_value=None,
            ),
            patch.dict(
                os.environ,
                {"OUTLINE_API_KEY": "env-key"},
            ),
            patch(
                "mcp_outline.features.documents.common.OutlineClient"
            ) as mock_cls,
        ):
            mock_cls.return_value = AsyncMock()

            await get_outline_client()
            mock_cls.assert_called_once_with(api_key="env-key", api_url=None)

    @pytest.mark.anyio
    async def test_no_key_anywhere_raises(self):
        """Neither header nor env var -> OutlineClientError."""
        with (
            patch(
                "mcp_outline.features.documents.common._get_header_api_key",
                return_value=None,
            ),
            patch.dict(os.environ, {}, clear=False),
            patch(
                "mcp_outline.features.documents.common.OutlineClient"
            ) as mock_cls,
        ):
            os.environ.pop("OUTLINE_API_KEY", None)
            from mcp_outline.utils.outline_client import (
                OutlineError,
            )

            mock_cls.side_effect = OutlineError("Missing API key")

            with pytest.raises(OutlineClientError):
                await get_outline_client()
