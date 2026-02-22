"""Integration tests for health check endpoints.

Tests the ``/health`` (liveness) and ``/ready`` (readiness) HTTP endpoints
by starting the MCP server as a subprocess in ``streamable-http`` mode and
polling until it binds to its port.

"""

import os
import subprocess
import sys
import time

import httpx
import pytest

HEALTH_PORT = 3997
HEALTH_BASE = f"http://127.0.0.1:{HEALTH_PORT}"
STARTUP_TIMEOUT = 8  # seconds


def _wait_for_server(base_url: str, timeout: float) -> bool:
    """Poll /health until 200 or timeout. Returns True if server is up."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            resp = httpx.get(f"{base_url}/health", timeout=1.0)
            if resp.status_code == 200:
                return True
        except (httpx.ConnectError, httpx.TimeoutException):
            pass
        time.sleep(0.25)
    return False


def _start_server() -> subprocess.Popen:
    """Start the MCP server in streamable-http mode."""
    env = os.environ.copy()
    env["MCP_TRANSPORT"] = "streamable-http"
    env["MCP_HOST"] = "127.0.0.1"
    env["MCP_PORT"] = str(HEALTH_PORT)
    # Use a dummy key so the server starts; /ready will fail to connect
    env["OUTLINE_API_KEY"] = "integration-test-invalid-key"

    return subprocess.Popen(
        [sys.executable, "-m", "mcp_outline"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )


@pytest.mark.integration
def test_health_liveness():
    """Start the server and verify GET /health returns 200 with status=healthy.

    Guards against: the liveness endpoint being broken during refactors of the
    server startup sequence, or the JSON response shape changing.
    """
    process = _start_server()
    try:
        ready = _wait_for_server(HEALTH_BASE, STARTUP_TIMEOUT)
        assert ready, (
            f"Server did not bind on port {HEALTH_PORT} "
            f"within {STARTUP_TIMEOUT}s"
        )

        resp = httpx.get(f"{HEALTH_BASE}/health", timeout=5.0)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
    finally:
        process.terminate()
        try:
            process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()


@pytest.mark.integration
def test_health_readiness_not_ready():
    """Verify GET /ready returns 503 when the Outline API key is invalid.

    Guards against: the readiness probe returning 200 even when the server
    cannot reach the Outline API, which would cause false-positive health
    checks in container orchestration.
    """
    process = _start_server()
    try:
        ready = _wait_for_server(HEALTH_BASE, STARTUP_TIMEOUT)
        assert ready, (
            f"Server did not bind on port {HEALTH_PORT} "
            f"within {STARTUP_TIMEOUT}s"
        )

        resp = httpx.get(f"{HEALTH_BASE}/ready", timeout=15.0)
        assert resp.status_code == 503
        data = resp.json()
        assert data["status"] == "not_ready"
        assert data["api_accessible"] is False
        assert "error" in data
        assert isinstance(data["error"], str)
    finally:
        process.terminate()
        try:
            process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
