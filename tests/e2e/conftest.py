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


def _outline_api(
    token: str,
    endpoint: str,
    payload: dict | None = None,
) -> httpx.Response:
    """POST to an Outline API endpoint with Bearer auth."""
    return httpx.post(
        f"{OUTLINE_URL}/api/{endpoint}",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
        timeout=30.0,
    )


def _require_redirect(resp, step_description: str) -> str:
    """Extract the ``Location`` header from a redirect response.

    Raises ``RuntimeError`` with diagnostics when the response is
    not a redirect or the header is missing.
    """
    location = resp.headers.get("location")
    if location:
        return location
    body_preview = resp.text[:500] if hasattr(resp, "text") else ""
    raise RuntimeError(
        f"{step_description}: expected redirect, got HTTP "
        f"{resp.status_code}. Body: {body_preview}"
    )


def _login(
    email: str = "admin@example.com",
    password: str = "admin",
    retries: int = 3,
) -> str:
    """Authenticate via OIDC/Dex and return the session token.

    Three-step flow:
    1. GET ``/auth/oidc`` on Outline to start the OIDC redirect
       and capture the initial session cookies.
    2. Follow the redirect to Dex, handle optional connector
       selection, parse the login form, and POST credentials.
    3. Follow the callback URL back to Outline using the saved
       cookies (manual management — see module docstring).

    Retries the full OIDC flow up to *retries* times with a
    short back-off to handle transient failures (e.g. Outline
    returning a non-redirect when hit concurrently).

    Returns the ``accessToken`` cookie value (session token).
    """
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            return _login_once(email, password)
        except (RuntimeError, httpx.RequestError) as exc:
            last_exc = exc
            if attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
    raise last_exc  # type: ignore[misc]


def _login_once(
    email: str,
    password: str,
) -> str:
    """Single-attempt OIDC login (called by ``_login``)."""
    # Step 1: Start OIDC flow on Outline
    resp = httpx.get(
        f"{OUTLINE_URL}/auth/oidc",
        follow_redirects=False,
        timeout=30.0,
    )
    outline_cookies = _parse_set_cookies(resp)
    dex_url = _require_redirect(resp, "OIDC initiation")

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
        form_data["login"] = email
        form_data["password"] = password

        # Submit login, capture redirect URL
        resp = dex_client.post(
            login_url,
            data=form_data,
            follow_redirects=False,
        )
        callback_url = _require_redirect(resp, "Dex login POST")

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
            f"(redirected to "
            f"{resp.headers.get('location')})"
        )
    return access_token


def _create_api_key(
    access_token: str,
    name: str = "e2e-test",
    scope: list | None = None,
    *,
    skip_on_error: bool = False,
) -> str:
    """Create an Outline API key and return its value.

    Args:
        access_token: OIDC session token (Bearer).
        name: Key name shown in Outline Settings.
        scope: Scope array, or ``None`` for full access.
        skip_on_error: If ``True``, call ``pytest.skip``
            instead of raising on non-200 responses.
    """
    json_body: dict = {"name": name}
    if scope is not None:
        json_body["scope"] = scope
    resp = _outline_api(access_token, "apiKeys.create", json_body)
    if resp.status_code != 200:
        if skip_on_error:
            pytest.skip(f"apiKeys.create returned {resp.status_code}")
        resp.raise_for_status()
    return resp.json()["data"]["value"]


def _login_and_create_api_key():
    """Login as admin and create a full-access API key.

    Returns ``(api_key_value, access_token)`` so downstream
    fixtures can create additional API keys using the session
    token.
    """
    token = _login("admin@example.com", "admin")
    key = _create_api_key(token)
    return key, token


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
def _outline_credentials(outline_stack):
    """Run the OIDC login once and return ``(api_key, access_token)``.

    Private fixture consumed by ``outline_api_key`` and
    ``outline_access_token``.
    """
    return _login_and_create_api_key()


@pytest.fixture(scope="session")
def outline_api_key(_outline_credentials):
    """Create one Outline API key for the entire test session.

    Session-scoped so the OIDC login flow runs exactly once regardless
    of how many tests are collected. Depends on ``outline_stack`` to
    guarantee Outline is reachable before the login attempt.

    Returns the raw API key string (``sk-...``).
    """
    return _outline_credentials[0]


@pytest.fixture(scope="session")
def outline_access_token(_outline_credentials):
    """Return the OIDC session access token.

    Needed by tests that must call endpoints (like
    ``apiKeys.create``) that require a session token
    rather than an API key.
    """
    return _outline_credentials[1]


@pytest.fixture(scope="session")
def mcp_server_params(outline_api_key):
    """Build ``StdioServerParameters`` pointing at the local E2E stack.

    Sets ``OUTLINE_API_URL`` to the localhost Outline instance so the
    MCP server under test talks to the E2E stack, not the default cloud
    API. The API key from ``outline_api_key`` is injected via the
    ``OUTLINE_API_KEY`` environment variable.

    All ``OUTLINE_*`` and ``MCP_*`` variables are stripped from the
    parent environment before the three required ones are set. This
    prevents flags like ``OUTLINE_READ_ONLY`` or
    ``OUTLINE_DISABLE_AI_TOOLS`` from leaking out of a developer's
    shell and silently altering which tools are registered.
    """
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith("OUTLINE_") and not k.startswith("MCP_")
    }
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
