"""E2E test fixtures for the MCP Outline server.

Manages the Docker Compose stack lifecycle and Outline API
key creation via OIDC/Dex authentication. All fixtures are
session-scoped: the stack starts once, one API key is
created, and one set of server parameters is shared across
every test in the session.

The E2E stack runs in an isolated Docker Compose project
(``mcp-outline-e2e``) on separate ports (3031/5557) so it
never conflicts with a developer's running Outline instance.

Cookie isolation: ``_login_and_create_api_key`` uses manual
cookie management via ``_parse_set_cookies`` instead of
httpx's built-in cookie jar. Both Outline and Dex run on
``localhost`` but on different ports; httpx would otherwise
send Outline session cookies to Dex, causing authentication
failures.
"""

import html
import os
import re
import subprocess
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urljoin

import httpx
import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import (
    StdioServerParameters,
    stdio_client,
)

from .helpers import OUTLINE_URL

PROJECT_ROOT = Path(__file__).resolve().parents[2]
E2E_PROJECT = "mcp-outline-e2e"

# Base compose command for the E2E stack
_COMPOSE_CMD = [
    "docker",
    "compose",
    "-p",
    E2E_PROJECT,
    "-f",
    "docker-compose.yml",
    "-f",
    "docker-compose.e2e.yml",
]


def _outline_is_ready():
    """Check if E2E Outline is responding."""
    try:
        resp = httpx.get(OUTLINE_URL, timeout=3.0)
        return resp.status_code < 500
    except httpx.RequestError:
        return False


def _wait_for_outline(timeout_s=120):
    """Poll until Outline responds or timeout."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if _outline_is_ready():
            return
        time.sleep(3)
    raise TimeoutError(f"Outline not ready within {timeout_s}s")


def _parse_set_cookies(response):
    """Extract cookies from Set-Cookie headers."""
    cookies = {}
    for name, value in response.headers.multi_items():
        if name.lower() == "set-cookie":
            k, v = value.split(";")[0].split("=", 1)
            cookies[k.strip()] = v.strip()
    return cookies


def _login_and_create_api_key():
    """Authenticate via OIDC/Dex and return a new API key value.

    Four-step flow:
    1. GET ``/auth/oidc`` on Outline to start the OIDC redirect
       and capture the initial session cookies.
    2. Follow the redirect to Dex, handle optional connector
       selection, parse the login form, and POST credentials.
    3. Follow the callback URL back to Outline using the saved
       cookies (manual management — see module docstring).
    4. POST to ``apiKeys.create`` using the ``accessToken``
       cookie as a Bearer token and return the key value.
    """
    # Step 1: Start OIDC flow on Outline
    resp = httpx.get(
        f"{OUTLINE_URL}/auth/oidc",
        follow_redirects=False,
        timeout=30.0,
    )
    outline_cookies = _parse_set_cookies(resp)
    dex_url = resp.headers["location"]

    # Step 2: Complete Dex login with separate client
    with httpx.Client(follow_redirects=True, timeout=30.0) as dex_client:
        resp = dex_client.get(dex_url)
        resp.raise_for_status()

        # Handle connector selection if present
        if 'name="login"' not in resp.text:
            link = re.search(
                r'href="([^"]*local[^"]*)"',
                resp.text,
            )
            if not link:
                raise RuntimeError("No local connector on Dex page")
            resp = dex_client.get(
                urljoin(
                    str(resp.url),
                    html.unescape(link.group(1)),
                )
            )
            resp.raise_for_status()

        # Parse login form
        action_m = re.search(r'<form[^>]*action="([^"]*)"', resp.text)
        if not action_m:
            raise RuntimeError("No login form found on Dex page")
        login_url = urljoin(
            str(resp.url),
            html.unescape(action_m.group(1)),
        )

        # Collect hidden fields
        form_data = {}
        for inp in re.findall(r"<input[^>]+>", resp.text):
            t = re.search(r'type="([^"]*)"', inp)
            n = re.search(r'name="([^"]*)"', inp)
            v = re.search(r'value="([^"]*)"', inp)
            if t and n and v and t.group(1) == "hidden":
                form_data[n.group(1)] = html.unescape(v.group(1))
        form_data["login"] = "admin@example.com"
        form_data["password"] = "admin"

        # Submit login, capture redirect URL
        resp = dex_client.post(
            login_url,
            data=form_data,
            follow_redirects=False,
        )
        callback_url = resp.headers["location"]

    # Step 3: Follow callback with original Outline cookies
    cookie_hdr = "; ".join(f"{k}={v}" for k, v in outline_cookies.items())
    resp = httpx.get(
        callback_url,
        headers={"Cookie": cookie_hdr},
        follow_redirects=False,
        timeout=30.0,
    )
    # Merge new cookies from callback response
    outline_cookies.update(_parse_set_cookies(resp))

    access_token = outline_cookies.get("accessToken")
    if not access_token:
        raise RuntimeError(
            "No accessToken cookie after OIDC login "
            f"(redirected to {resp.headers.get('location')})"
        )

    # Step 4: Create API key using Bearer token
    resp = httpx.post(
        f"{OUTLINE_URL}/api/apiKeys.create",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={"name": "e2e-test"},
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()["data"]["value"]


@pytest.fixture(scope="session")
def outline_stack():
    """Ensure the E2E Outline stack is running and manage its lifecycle.

    If Outline is already responding on port 3031 (e.g. a developer's
    manually started stack), this fixture reuses it and does **not**
    tear it down on exit. If it is not running, the fixture starts it
    via ``docker compose up -d`` and tears it down with ``down -v``
    after the session completes.

    Yields the Outline base URL (``http://localhost:3031``).
    """
    managed = False

    if not _outline_is_ready():
        compose_env = {
            **os.environ,
            "DEX_HOST_PORT": "5557",
            "OUTLINE_HOST_PORT": "3031",
        }
        subprocess.run(
            [*_COMPOSE_CMD, "up", "-d", "outline"],
            cwd=str(PROJECT_ROOT),
            env=compose_env,
            check=True,
        )
        managed = True

    _wait_for_outline()
    yield OUTLINE_URL

    if managed:
        subprocess.run(
            [*_COMPOSE_CMD, "down", "-v"],
            cwd=str(PROJECT_ROOT),
            check=True,
        )


@pytest.fixture(scope="session")
def outline_api_key(outline_stack):
    """Create one Outline API key for the entire test session.

    Session-scoped so the OIDC login flow runs exactly once regardless
    of how many tests are collected. Depends on ``outline_stack`` to
    guarantee Outline is reachable before the login attempt.

    Returns the raw API key string (``sk-...``).
    """
    return _login_and_create_api_key()


@pytest.fixture(scope="session")
def mcp_server_params(outline_api_key):
    """Build ``StdioServerParameters`` pointing at the local E2E stack.

    Sets ``OUTLINE_API_URL`` to the localhost Outline instance so the
    MCP server under test talks to the E2E stack, not the default cloud
    API. The API key from ``outline_api_key`` is injected via the
    ``OUTLINE_API_KEY`` environment variable.
    """
    env = os.environ.copy()
    env["MCP_TRANSPORT"] = "stdio"
    env["OUTLINE_API_KEY"] = outline_api_key
    env["OUTLINE_API_URL"] = f"{OUTLINE_URL}/api"
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_outline"],
        env=env,
    )


@pytest.fixture(scope="session")
def mcp_session(mcp_server_params):
    """Return a factory that creates one ``ClientSession`` per test.

    Each call to the returned factory starts a fresh stdio subprocess
    and MCP handshake, then yields the initialised session. Using a
    factory (rather than a single shared session) keeps tests isolated:
    one test's tool calls cannot affect another's server state.

    Usage::

        async with mcp_session() as session:
            result = await session.call_tool("some_tool", arguments={})
    """

    @asynccontextmanager
    async def _create():
        async with stdio_client(
            mcp_server_params,
        ) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session

    return _create
