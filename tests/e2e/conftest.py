"""
E2E test fixtures for the MCP Outline server.

Manages Docker Compose stack lifecycle and API key creation
via OIDC/Dex authentication.

The E2E stack runs in an isolated Docker Compose project
(mcp-outline-e2e) on separate ports (3031/5557) so it
never conflicts with a developer's running instance.
"""

import html
import os
import re
import subprocess
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


def _wait_for_outline(timeout_s=300):
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
    """Authenticate via OIDC/Dex and create an API key.

    Uses manual cookie management to prevent httpx's cookie
    jar from leaking Outline cookies to Dex (both run on
    localhost but on different ports).
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
    """Ensure E2E Outline stack is running; manage lifecycle."""
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
    """Create an Outline API key via OIDC login."""
    return _login_and_create_api_key()


@pytest.fixture(scope="session")
def mcp_server_params(outline_api_key):
    """MCP server parameters with real credentials."""
    env = os.environ.copy()
    env["MCP_TRANSPORT"] = "stdio"
    env["OUTLINE_API_KEY"] = outline_api_key
    env["OUTLINE_API_URL"] = f"{OUTLINE_URL}/api"
    return StdioServerParameters(
        command="python",
        args=["-m", "mcp_outline"],
        env=env,
    )


@pytest.fixture(scope="session")
def mcp_session(mcp_server_params):
    """Factory returning async context manager sessions."""

    @asynccontextmanager
    async def _create():
        async with stdio_client(
            mcp_server_params,
        ) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session

    return _create
