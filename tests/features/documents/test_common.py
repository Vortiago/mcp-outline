"""
Tests for common utilities (get_outline_client, _get_header_api_key).
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from unittest.mock import AsyncMock, patch

import pytest

from mcp_outline.features.documents.common import (
    OutlineClientError,
    _get_header_api_key,
    get_outline_client,
)

# ---------------------------------------------------------------------------
# Helpers: lightweight stand-ins for Starlette Request / MCP RequestContext
# ---------------------------------------------------------------------------


class _FakeHeaders:
    """Minimal mapping that mimics Starlette Headers."""

    def __init__(self, mapping: dict):
        self._data = {k.lower(): v for k, v in mapping.items()}

    def get(self, key: str, default=None):
        return self._data.get(key.lower(), default)


class _FakeRequest:
    """Minimal stand-in for a Starlette Request."""

    def __init__(self, headers: Optional[dict] = None):
        self.headers = _FakeHeaders(headers or {})


@dataclass
class _FakeRequestContext:
    """Minimal stand-in for mcp RequestContext."""

    request: object = field(default=None)


# ---------------------------------------------------------------------------
# Tests for _get_header_api_key
# ---------------------------------------------------------------------------


class TestGetHeaderApiKey:
    """Tests for the _get_header_api_key helper."""

    def test_returns_none_outside_request_context(self):
        """No request context set -> returns None."""
        result = _get_header_api_key()
        assert result is None

    def test_returns_key_from_header(self):
        """Header present -> returns key value."""
        fake_ctx = _FakeRequestContext(
            request=_FakeRequest(headers={"x-outline-api-key": "sk-test-key"})
        )
        with patch(
            "mcp_outline.features.documents.common.request_ctx",
            create=True,
        ) as mock_var:
            mock_var.get.return_value = fake_ctx
            # Patch the import inside _get_header_api_key
            with patch.dict(
                "sys.modules",
                {
                    "mcp.server.lowlevel.server": type(
                        "mod",
                        (),
                        {"request_ctx": mock_var},
                    )
                },
            ):
                result = _get_header_api_key()
        assert result == "sk-test-key"

    def test_returns_none_when_header_absent(self):
        """Request exists but header missing -> None."""
        fake_ctx = _FakeRequestContext(request=_FakeRequest(headers={}))
        with patch.dict(
            "sys.modules",
            {
                "mcp.server.lowlevel.server": type(
                    "mod",
                    (),
                    {
                        "request_ctx": type(
                            "cv",
                            (),
                            {"get": lambda self: fake_ctx},
                        )()
                    },
                )
            },
        ):
            result = _get_header_api_key()
        assert result is None

    def test_sanitizes_header_value(self):
        """Quoted/whitespace values are cleaned."""
        fake_ctx = _FakeRequestContext(
            request=_FakeRequest(
                headers={"x-outline-api-key": '  "sk-quoted"  '}
            )
        )
        with patch.dict(
            "sys.modules",
            {
                "mcp.server.lowlevel.server": type(
                    "mod",
                    (),
                    {
                        "request_ctx": type(
                            "cv",
                            (),
                            {"get": lambda self: fake_ctx},
                        )()
                    },
                )
            },
        ):
            result = _get_header_api_key()
        assert result == "sk-quoted"

    def test_returns_none_when_request_is_none(self):
        """RequestContext with request=None -> None."""
        fake_ctx = _FakeRequestContext(request=None)
        with patch.dict(
            "sys.modules",
            {
                "mcp.server.lowlevel.server": type(
                    "mod",
                    (),
                    {
                        "request_ctx": type(
                            "cv",
                            (),
                            {"get": lambda self: fake_ctx},
                        )()
                    },
                )
            },
        ):
            result = _get_header_api_key()
        assert result is None


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
            mock_client = AsyncMock()
            mock_client.auth_info.return_value = {}
            mock_cls.return_value = mock_client

            client = await get_outline_client()
            mock_cls.assert_called_once_with(
                api_key="header-key", api_url=None
            )
            assert client is mock_client

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
            mock_client = AsyncMock()
            mock_client.auth_info.return_value = {}
            mock_cls.return_value = mock_client

            client = await get_outline_client()
            mock_cls.assert_called_once_with(api_key="env-key", api_url=None)
            assert client is mock_client

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
            # Remove env var if present
            os.environ.pop("OUTLINE_API_KEY", None)
            mock_client = AsyncMock()
            mock_client.auth_info.side_effect = Exception("No API key")
            mock_cls.return_value = mock_client

            with pytest.raises(OutlineClientError):
                await get_outline_client()
