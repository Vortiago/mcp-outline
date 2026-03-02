"""E2E tests for per-request API key via the x-outline-api-key header.

Verifies that the MCP server accepts an Outline API key through the
``x-outline-api-key`` HTTP header when running in ``streamable-http``
mode, and that the header takes priority over the ``OUTLINE_API_KEY``
environment variable.

These tests start the MCP server as a subprocess (like the health-check
integration tests) and connect via the MCP SDK's
``streamable_http_client`` transport.
"""

import os
import subprocess
import sys
import time

import httpx
import pytest
from mcp.client.session import ClientSession
from mcp.client.streamable_http import (
    streamable_http_client,
)
from mcp.types import TextContent

from .helpers import OUTLINE_URL

E2E_PORT = 3998
E2E_BASE = f"http://127.0.0.1:{E2E_PORT}"
STARTUP_TIMEOUT = 8  # seconds

pytestmark = [pytest.mark.e2e, pytest.mark.anyio]


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------


def _wait_for_server(base_url: str, timeout: float) -> bool:
    """Poll ``/health`` until 200 or *timeout*."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            resp = httpx.get(f"{base_url}/health", timeout=1.0)
            if resp.status_code == 200:
                return True
        except (
            httpx.ConnectError,
            httpx.TimeoutException,
        ):
            pass
        time.sleep(0.25)
    return False


def _start_http_server(api_key: str, api_url: str) -> subprocess.Popen:
    """Start the MCP server in streamable-http mode."""
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith("OUTLINE_") and not k.startswith("MCP_")
    }
    env["MCP_TRANSPORT"] = "streamable-http"
    env["MCP_HOST"] = "127.0.0.1"
    env["MCP_PORT"] = str(E2E_PORT)
    env["OUTLINE_API_KEY"] = api_key
    env["OUTLINE_API_URL"] = api_url
    return subprocess.Popen(
        [sys.executable, "-m", "mcp_outline"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )


def _stop(process: subprocess.Popen) -> None:
    """Terminate a server subprocess cleanly."""
    process.terminate()
    try:
        process.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.communicate()


# -------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------


async def test_header_api_key_overrides_env_var(
    outline_stack, outline_api_key
):
    """Verify ``x-outline-api-key`` header overrides env var.

    Starts the server with a dummy ``OUTLINE_API_KEY`` that will
    fail authentication, then sends the real key via the header.
    If the tool call succeeds, the per-request header was used.

    Guards against: the header being ignored and the server always
    using the environment variable.
    """
    api_url = f"{OUTLINE_URL}/api"
    process = _start_http_server(
        api_key="dummy-invalid-key",
        api_url=api_url,
    )
    try:
        ready = _wait_for_server(E2E_BASE, STARTUP_TIMEOUT)
        assert ready, (
            f"Server did not bind on port {E2E_PORT} within {STARTUP_TIMEOUT}s"
        )

        http_client = httpx.AsyncClient(
            headers={
                "x-outline-api-key": outline_api_key,
            },
            timeout=httpx.Timeout(30.0, read=300.0),
        )
        async with streamable_http_client(
            url=f"{E2E_BASE}/mcp",
            http_client=http_client,
        ) as (read, write, _):
            async with ClientSession(read, write) as s:
                await s.initialize()
                result = await s.call_tool("list_collections")
                item = result.content[0]
                assert isinstance(item, TextContent)
                assert "Error" not in item.text
                assert (
                    "# Collections" in item.text
                    or "No collections found" in item.text
                )
    finally:
        _stop(process)


async def test_env_var_used_when_no_header(outline_stack, outline_api_key):
    """Verify env var fallback when no header is sent.

    Starts the server with the real ``OUTLINE_API_KEY`` and
    connects without the ``x-outline-api-key`` header. The
    tool call should succeed using the environment variable.

    Guards against: the per-request header feature breaking
    backward compatibility with the env-var-only approach.
    """
    api_url = f"{OUTLINE_URL}/api"
    process = _start_http_server(
        api_key=outline_api_key,
        api_url=api_url,
    )
    try:
        ready = _wait_for_server(E2E_BASE, STARTUP_TIMEOUT)
        assert ready, (
            f"Server did not bind on port {E2E_PORT} within {STARTUP_TIMEOUT}s"
        )

        # No x-outline-api-key header — should fall back
        # to the env var.
        async with streamable_http_client(
            url=f"{E2E_BASE}/mcp",
        ) as (read, write, _):
            async with ClientSession(read, write) as s:
                await s.initialize()
                result = await s.call_tool("list_collections")
                item = result.content[0]
                assert isinstance(item, TextContent)
                assert "Error" not in item.text
                assert (
                    "# Collections" in item.text
                    or "No collections found" in item.text
                )
    finally:
        _stop(process)
